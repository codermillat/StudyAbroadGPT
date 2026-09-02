#!/usr/bin/env python3
"""
audit_training_neighbors.py
==========================

Step 2 of the stratified causal test pre-registered at
``docs/analysis-plans/2026-09-02-stratified-causal-test.md``.

Generates a fillable audit template CSV from the Gemini-1.0-Pro training
corpus, plus a starter set of the v4 D-Cases (the 4 source-verified wrong
training answers documented in
``docs/audit/v4-dataset-factuality-catalog.md``).

Workflow
--------

1. Generate the template::

       python3 audit_training_neighbors.py generate \\
           --training-data "LoRA Paper/linked_repos/study-abroad-dataset/dataset/study_abroad_dataset.jsonl" \\
           --output data/v5-audit-template.csv \\
           --mode mixed --n-random 60 --n-keyword 25 --seed 42

   This writes a CSV with columns
   ``training_id, first_user_turn, first_assistant_turn, keyword_match, label, source_url, notes``.
   The user fills in ``label`` (one of ``verified_correct``, ``verified_wrong``,
   or ``unclear``), ``source_url``, and ``notes`` for each row by hand using
   web search against authoritative sources (UKVI, US Dept of State,
   university admissions pages, scholarship commission pages, etc.).

2. Concatenate with the v4 D-Cases (already source-verified) and any
   other hand-audited rows to form the final audit catalog
   ``data/v5-audit-catalog.csv`` (the input expected by
   ``stratify_prompts.py``). The simplest way to add the v4 D-Cases is to
   copy them from the table in
   ``docs/audit/v4-dataset-factuality-catalog.md`` into the catalog CSV
   directly; the v4 D-Cases are only 4 rows, so this is a 5-minute job.

3. Run ``stratify_prompts.py`` against the completed audit catalog.

Pre-registration target (Section 3.4 of the protocol)
----------------------------------------------------

After the v4 catalog (n=40) and the new sample (n=85 default), the
final audit budget is ~125 with a target of at least 20 ``verified_wrong``
labels. The script's power-verdict summary (printed at the end) tells
you when you have enough.

Notes
-----

- The v4 D-Cases are NOT auto-extracted from the markdown. The four
  training answers are quoted in
  ``docs/audit/v4-dataset-factuality-catalog.md``; copy them by hand into
  the audit catalog. The script's role is to generate the *new* sample
  (the 80 random + keyword-targeted rows).
- The over-sampling for high-risk keywords is a coarse heuristic: the
  ground-truth for the W stratum is rare, and concentrating the audit
  effort on prompts that mention admissions/visa/scholarship terms
  raises the yield of ``verified_wrong`` labels per audited row.
- ``--seed`` defaults to 42 (matches the v4 held-out sample seed).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("audit_training_neighbors")


# High-risk keywords that correlate with the v4 error classes (HMS, AU
# Medicare, Stanford MBBS, Brazil->Bangladesh scholarships, etc.). These
# are not a comprehensive list; the goal is just to up-weight the audit
# yield for the W stratum.
HIGH_RISK_KEYWORDS: tuple[str, ...] = (
    # admissions / programs
    "Bachelor of", "Master of", "MS in", "MBA", "MBBS", "PhD in",
    "GRE", "IELTS", "TOEFL", "MCAT",
    # money / funding
    "scholarship", "tuition", "fees", "cost of", "budget", "funding",
    "eligible", "eligibility", "required",
    # policy / legal
    "visa", "F-1", "F1 visa", "student visa", "OPT", "CPT",
    "Medicare", "OSHC", "NHS", "health insurance", "healthcare",
    # scholarship bodies
    "Fulbright", "Chevening", "Commonwealth", "Erasmus", "DAAD",
    # numeric / citation patterns that the v4 catalog flagged
    "according to", "study", "studies", "percent", "%", "report",
    "survey", "in 20", "in 2024", "in 2025", "in 2023", "in 2022",
)


@dataclass
class TrainingRow:
    """One training example, candidate for audit."""

    training_id: str
    first_user_turn: str
    first_assistant_turn: str
    keyword_match: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _first_user_turn(conversation: dict) -> str:
    for turn in conversation.get("conversations", []):
        if turn.get("from") in ("human", "user"):
            return (turn.get("value") or "").strip()
    return ""


def _first_assistant_turn(conversation: dict) -> str:
    for turn in conversation.get("conversations", []):
        if turn.get("from") in ("assistant", "gpt"):
            return (turn.get("value") or "").strip()
    return ""


def _training_id_from_text(text: str) -> str:
    import hashlib
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def load_training_data(jsonl_path: Path) -> list[TrainingRow]:
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Training JSONL not found: {jsonl_path}")
    rows: list[TrainingRow] = []
    with jsonl_path.open(encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.warning("Skipping line %d: invalid JSON (%s)", line_no, e)
                continue
            user_turn = _first_user_turn(obj)
            asst_turn = _first_assistant_turn(obj)
            if not user_turn or not asst_turn:
                continue
            rows.append(
                TrainingRow(
                    training_id=_training_id_from_text(user_turn),
                    first_user_turn=user_turn,
                    first_assistant_turn=asst_turn,
                )
            )
    logger.info("Loaded %d training examples from %s", len(rows), jsonl_path)
    return rows


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


def find_keyword_matches(text: str) -> list[str]:
    """Return the list of HIGH_RISK_KEYWORDS that appear in `text` (case-insensitive)."""
    lower = text.lower()
    return [kw for kw in HIGH_RISK_KEYWORDS if kw.lower() in lower]


def sample_mixed(
    rows: list[TrainingRow],
    n_random: int,
    n_keyword: int,
    seed: int,
) -> list[TrainingRow]:
    """Stratified sample: n_random uniformly at random, n_keyword from the
    set of rows that match >= 1 HIGH_RISK_KEYWORD.

    Keyword-targeted rows that have already been sampled into the random
    pool are excluded from the keyword pool to avoid double-counting.
    """
    rng = random.Random(seed)

    # Shuffle and split
    indices = list(range(len(rows)))
    rng.shuffle(indices)

    random_picks: list[TrainingRow] = []
    seen_ids: set[str] = set()
    for i in indices:
        if len(random_picks) >= n_random:
            break
        r = rows[i]
        if r.training_id in seen_ids:
            continue
        seen_ids.add(r.training_id)
        random_picks.append(r)

    # Compute keyword matches for the remainder
    remaining = [r for r in rows if r.training_id not in seen_ids]
    keyword_pool = [r for r in remaining if find_keyword_matches(r.first_user_turn) or find_keyword_matches(r.first_assistant_turn)]
    rng.shuffle(keyword_pool)

    keyword_picks: list[TrainingRow] = []
    for r in keyword_pool:
        if len(keyword_picks) >= n_keyword:
            break
        keyword_picks.append(r)
        # tag with the keywords for the user's reference
        r.keyword_match = find_keyword_matches(r.first_user_turn) + find_keyword_matches(r.first_assistant_turn)

    return random_picks + keyword_picks


def sample_random(rows: list[TrainingRow], n: int, seed: int) -> list[TrainingRow]:
    rng = random.Random(seed)
    return rng.sample(rows, min(n, len(rows)))


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_template(sample: list[TrainingRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "training_id",
        "first_user_turn",
        "first_assistant_turn",
        "keyword_match",
        "label",
        "source_url",
        "notes",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sample:
            writer.writerow({
                "training_id": r.training_id,
                "first_user_turn": r.first_user_turn,
                "first_assistant_turn": r.first_assistant_turn[:600] + ("..." if len(r.first_assistant_turn) > 600 else ""),
                "keyword_match": ", ".join(r.keyword_match) if r.keyword_match else "",
                "label": "",
                "source_url": "",
                "notes": "",
            })
    logger.info("Wrote %d rows to %s", len(sample), output_path)


def print_summary(sample: list[TrainingRow], n_total: int) -> None:
    n_kw = sum(1 for r in sample if r.keyword_match)
    print()
    print("=" * 64)
    print("AUDIT TEMPLATE SUMMARY")
    print("=" * 64)
    print(f"Total training corpus size:    {n_total}")
    print(f"Sampled for audit:              {len(sample)}")
    print(f"  Random sample:                {len(sample) - n_kw}")
    print(f"  Keyword-targeted sample:      {n_kw}")
    print()
    print("Next steps:")
    print("  1. Open the audit template CSV in your editor.")
    print("  2. For each row, web-search the assistant's specific")
    print("     claims against authoritative sources (UKVI, US Dept of")
    print("     State, university admissions, scholarship commissions).")
    print("  3. Fill in 'label' (verified_correct / verified_wrong / unclear),")
    print("     'source_url', and 'notes'.")
    print("  4. Append the 4 v4 D-Cases from docs/audit/v4-dataset-factuality-catalog.md.")
    print("  5. Save as data/v5-audit-catalog.csv.")
    print()
    print("Pre-registration target: >= 100 audited rows, with >= 20 'verified_wrong' labels.")
    print("=" * 64)


# ---------------------------------------------------------------------------
# Verify subcommand (sanity check on an existing audit catalog)
# ---------------------------------------------------------------------------


def verify_catalog(catalog_path: Path) -> None:
    """Print a summary of an already-completed audit catalog CSV."""
    if not catalog_path.exists():
        raise FileNotFoundError(f"Audit catalog not found: {catalog_path}")

    counts: dict[str, int] = {}
    with catalog_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("label") or "").strip() or "(empty)"
            counts[label] = counts.get(label, 0) + 1

    print()
    print("=" * 64)
    print(f"AUDIT CATALOG VERIFICATION: {catalog_path}")
    print("=" * 64)
    for k, v in sorted(counts.items()):
        print(f"  {k:20s}: {v}")
    n_w = counts.get("verified_wrong", 0)
    n_c = counts.get("verified_correct", 0)
    n_total = sum(v for k, v in counts.items() if k in ("verified_correct", "verified_wrong"))
    print()
    if n_total >= 100 and n_w >= 20:
        print("Verdict: AUDIT BUDGET ADEQUATE (n_audit >= 100, n_wrong >= 20).")
    elif n_w < 20:
        print(f"Verdict: INSUFFICIENT. Need >= 20 'verified_wrong' labels; have {n_w}.")
        print("         Sample more high-risk-keyword rows (e.g., --n-keyword 50) and audit more.")
    else:
        print(f"Verdict: OK ({n_total} audited, {n_w} wrong), but aim for >= 100 total for the primary analysis.")
    print("=" * 64)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate an audit template for the §3 stratified test.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Sample training examples and write a fillable audit template.")
    g.add_argument("--training-data", type=Path, required=True, help="Training JSONL.")
    g.add_argument("--output", type=Path, required=True, help="Output audit template CSV.")
    g.add_argument("--mode", choices=["random", "keyword", "mixed"], default="mixed")
    g.add_argument("--n-random", type=int, default=60, help="Number of random samples (mode=random or mixed).")
    g.add_argument("--n-keyword", type=int, default=25, help="Number of high-risk keyword samples (mode=keyword or mixed).")
    g.add_argument("--n", type=int, default=None, help="Convenience: total sample size (overrides --n-random and --n-keyword when mode=random).")
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--verbose", "-v", action="store_true")

    v = sub.add_parser("verify", help="Print a summary of an existing audit catalog.")
    v.add_argument("--catalog", type=Path, required=True, help="Audit catalog CSV to verify.")

    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.cmd == "generate":
        rows = load_training_data(args.training_data)
        if args.mode == "random":
            n = args.n if args.n is not None else args.n_random
            sample = sample_random(rows, n, args.seed)
        elif args.mode == "keyword":
            n = args.n if args.n is not None else args.n_keyword
            keyword_pool = [
                r for r in rows
                if find_keyword_matches(r.first_user_turn) or find_keyword_matches(r.first_assistant_turn)
            ]
            rng = random.Random(args.seed)
            sample = rng.sample(keyword_pool, min(n, len(keyword_pool)))
            for r in sample:
                r.keyword_match = find_keyword_matches(r.first_user_turn) + find_keyword_matches(r.first_assistant_turn)
        else:  # mixed
            sample = sample_mixed(rows, args.n_random, args.n_keyword, args.seed)
        write_template(sample, args.output)
        print_summary(sample, len(rows))
        return 0

    if args.cmd == "verify":
        verify_catalog(args.catalog)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
