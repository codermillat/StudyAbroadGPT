#!/usr/bin/env python3
"""
merge_stratified_audits.py
==========================

Merge the per-batch subagent source-verification JSONs into the single
``data/v5-audit-results.csv`` consumed by ``analyze_stratified.py``.

Inputs
------

* ``/tmp/v5_held_out_bundles/result_batch_{1..6}.json`` — written by the
  6 parallel explore subagents. Each file has schema::

      {"prompts": [{"prompt_id": <int>, "stratum": "C|W|M",
                     "base": {"label": ..., "source_urls": [...], "notes": ...},
                     "lora": {"label": ..., "source_urls": [...], "notes": ...}}, ...]}

* ``/tmp/v5_held_out_bundles/prompt_<NN>_stratum_<S>.json`` — per-prompt bundles
  to look up stratum (the JSONs are the source of truth for prompt order).

* ``data/v5-stratified-prompts.csv`` — stratified prompt list (defines order).

Output
------

``data/v5-audit-results.csv`` with columns::

    prompt_id, stratum, base_label, lora_label,
    base_source_url, lora_source_url, base_notes, lora_notes

Only ``verified_correct`` / ``verified_wrong`` / ``unclear`` are written through.
Any prompt missing from the batch JSONs gets a row with empty labels and a
``MISSING_BATCH`` note in base_notes (so ``analyze_stratified.py`` will see it
and exclude it via the "unclear" path or stratum filtering).

Usage
-----

    python3 merge_stratified_audits.py
        --batches-dir /tmp/v5_held_out_bundles
        --stratified  data/v5-stratified-prompts.csv
        --output      data/v5-audit-results.csv
        --summary     docs/audit/v5-stratified-merge-summary.md
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger("merge_stratified_audits")


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_stratified(csv_path: Path) -> list[dict]:
    """Load stratifiable prompts in order."""
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("stratum") in ("C", "W", "M"):
                rows.append(r)
    return rows


def load_batches(batches_dir: Path) -> dict[int, dict]:
    """Load all result_batch_*.json files. Returns {prompt_id: result}."""
    out: dict[int, dict] = {}
    for fp in sorted(batches_dir.glob("result_batch_*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to read %s: %s", fp, e)
            continue
        for entry in data.get("prompts", []):
            pid = int(entry.get("prompt_id"))
            out[pid] = entry
    return out


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def _short_label(label: str) -> str:
    """Normalize 'verified_correct' / 'verified_wrong' / 'unclear' to the
    short form expected by analyze_stratified.py ('correct' / 'wrong' / 'unclear')."""
    if not label:
        return ""
    s = label.strip().lower()
    if s in ("verified_correct", "correct"):
        return "correct"
    if s in ("verified_wrong", "wrong"):
        return "wrong"
    if s == "unclear":
        return "unclear"
    return s  # pass through (e.g. 'missing')


def merge(stratified: list[dict], batches: dict[int, dict]) -> list[dict]:
    rows: list[dict] = []
    for r in stratified:
        pid = int(r["prompt_id"])
        entry = batches.get(pid, {})
        base = entry.get("base", {})
        lora = entry.get("lora", {})
        rows.append({
            "prompt_id": pid,
            "stratum": r["stratum"],
            "base_label": _short_label(base.get("label", "")),
            "lora_label": _short_label(lora.get("label", "")),
            "base_source_url": "; ".join(base.get("source_urls", []) or []),
            "lora_source_url": "; ".join(lora.get("source_urls", []) or []),
            "base_notes": base.get("notes", "") if base else "MISSING_BATCH",
            "lora_notes": lora.get("notes", "") if lora else "MISSING_BATCH",
        })
    return rows


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = ["prompt_id", "stratum", "base_label", "lora_label",
                  "base_source_url", "lora_source_url", "base_notes", "lora_notes"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_summary(rows: list[dict], path: Path) -> None:
    from collections import Counter
    coverage: Counter = Counter()
    pair_counts: Counter = Counter()
    for r in rows:
        bl = (r["base_label"] or "missing").lower()
        ll = (r["lora_label"] or "missing").lower()
        coverage[bl] += 1
        coverage[ll] += 1
        pair_counts[(bl, ll)] += 1
    lines = [
        "# v5 Stratified Held-Out Source-Verified Audit — Merge Summary",
        "",
        "## Coverage by label (across both models, 60 expected = 30 prompts x 2 models)",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label in ["verified_correct", "verified_wrong", "unclear", "missing"]:
        lines.append(f"| {label} | {coverage.get(label, 0)} |")
    lines += [
        "",
        "## Paired-label contingency (rows = (base, lora))",
        "",
        "| base | lora | n |",
        "|---|---|---:|",
    ]
    for (bl, ll), n in sorted(pair_counts.items()):
        lines.append(f"| {bl} | {ll} | {n} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--batches-dir", type=Path,
                   default=Path("/tmp/v5_held_out_bundles"),
                   help="Directory containing result_batch_*.json.")
    p.add_argument("--stratified", type=Path, required=True,
                   help="Stratified prompts CSV (defines order and strata).")
    p.add_argument("--output", type=Path,
                   default=Path("data/v5-audit-results.csv"),
                   help="Output audit results CSV.")
    p.add_argument("--summary", type=Path,
                   default=Path("docs/audit/v5-stratified-merge-summary.md"),
                   help="Output merge summary Markdown.")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    stratified = load_stratified(args.stratified)
    batches = load_batches(args.batches_dir)
    logger.info("Loaded %d stratified prompts, %d batch entries",
                len(stratified), len(batches))
    rows = merge(stratified, batches)
    write_csv(rows, args.output)
    write_summary(rows, args.summary)
    print(f"Wrote {len(rows)} rows to {args.output}")
    print(f"Wrote summary to {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
