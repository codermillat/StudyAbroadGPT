#!/usr/bin/env python3
"""
analyze_stratified.py
=====================

Step 4 of the stratified causal test pre-registered at
``docs/analysis-plans/2026-09-02-stratified-causal-test.md``.

Consumes the user-audited factuality labels for the stratified prompt
sample (output of ``generate_stratified.py`` followed by manual
source-verification) and produces the per-stratum 2x2 contingency
tables, McNemar's test, 95% CIs on the LoRA - base error rate
difference, and a forest-plot figure for v5 §4.4.3.

Input format
------------

A CSV with one row per stratified prompt, where the user has filled in
``base_label`` and ``lora_label`` (each: ``correct``, ``wrong``, or
``unclear``) and ideally ``base_source_url`` / ``lora_source_url`` and
free-text notes. The expected column set is::

    prompt_id, stratum, base_label, lora_label,
    base_source_url, lora_source_url, base_notes, lora_notes

Prompts labeled ``unclear`` for either model are excluded from the
primary analysis; they are reported separately for transparency.

Outputs
-------

    <output-dir>/
        per_stratum_results.csv     # the primary 2x2 tables, McNemar p, CI, OR
        per_prompt_results.csv      # one row per stratified prompt with both labels
        excluded_prompts.csv        # prompts excluded due to 'unclear' label
        forest_plot.png             # base vs LoRA error rate per stratum (if matplotlib)
        summary.txt                 # human-readable summary including the §4.2 decision rule

Usage
-----

    python3 analyze_stratified.py \\
        --audit-results data/v5-audit-results.csv \\
        --output-dir data/v5-analysis/

Pre-registration §6
-------------------

This script implements the §6.1 (primary McNemar per stratum) and §6.2
(secondary pooled test + stratum x model interaction) analyses.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

logger = logging.getLogger("analyze_stratified")


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_audit_results(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Audit results CSV not found: {csv_path}")
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    logger.info("Loaded %d audit results from %s", len(rows), csv_path)
    return rows


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def _safe_div(a: float, b: float) -> float:
    return a / b if b else float("nan")


@dataclass
class StratumResult:
    stratum: str
    n_pairs: int
    a: int  # both correct
    b: int  # base wrong, LoRA correct
    c: int  # base correct, LoRA wrong
    d: int  # both wrong
    p_lora: float
    p_base: float
    diff: float  # LoRA - base error rate
    ci_low: float
    ci_high: float
    mcnemar_p: float
    matched_or: float  # c/b (LoRA-wrong : base-wrong) among discordant
    note: str = ""


def build_2x2(rows: list[dict]) -> tuple[int, int, int, int]:
    """Return (a, b, c, d) where:
        a = both correct
        b = base wrong, LoRA correct
        c = base correct, LoRA wrong
        d = both wrong
    """
    a = b = c = d = 0
    for r in rows:
        bl = (r.get("base_label") or "").strip().lower()
        ll = (r.get("lora_label") or "").strip().lower()
        if bl == "correct" and ll == "correct":
            a += 1
        elif bl == "wrong" and ll == "correct":
            b += 1
        elif bl == "correct" and ll == "wrong":
            c += 1
        elif bl == "wrong" and ll == "wrong":
            d += 1
    return a, b, c, d


def mcnemar_test_with_cc(b: int, c: int) -> float:
    """McNemar's test with continuity correction.

    Test statistic: (|b - c| - 1)^2 / (b + c)  ~  chi^2(1)
    Returns the p-value (two-sided).
    """
    if (b + c) == 0:
        return float("nan")
    from math import erf, sqrt
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    # 1 - CDF of chi^2(1) at chi2: P(X > chi2) = 1 - erf(sqrt(chi2/2))
    p = 1.0 - erf(math.sqrt(chi2 / 2.0))
    return max(0.0, min(1.0, p))


def bootstrap_diff_ci(
    rows: list[dict],
    n_boot: int = 1000,
    seed: int = 42,
) -> tuple[float, float, float, float]:
    """Bootstrap 95% CI on the LoRA - base error rate difference.

    Returns (p_lora, p_base, ci_low, ci_high).
    """
    import random
    if not rows:
        return 0.0, 0.0, 0.0, 0.0
    rng = random.Random(seed)
    diffs: list[float] = []
    n = len(rows)
    for _ in range(n_boot):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        n_lora_wrong = sum(1 for r in sample if (r.get("lora_label") or "").strip().lower() == "wrong")
        n_base_wrong = sum(1 for r in sample if (r.get("base_label") or "").strip().lower() == "wrong")
        diffs.append(n_lora_wrong / n - n_base_wrong / n)
    diffs.sort()
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot) - 1]
    n_lora_wrong = sum(1 for r in rows if (r.get("lora_label") or "").strip().lower() == "wrong")
    n_base_wrong = sum(1 for r in rows if (r.get("base_label") or "").strip().lower() == "wrong")
    return n_lora_wrong / n, n_base_wrong / n, lo, hi


def evaluate_stratum(stratum: str, rows: list[dict], n_boot: int = 1000) -> StratumResult:
    a, b, c, d = build_2x2(rows)
    n = a + b + c + d
    p_lora, p_base, ci_lo, ci_hi = bootstrap_diff_ci(rows, n_boot=n_boot)
    p = mcnemar_test_with_cc(b, c)
    oratio = _safe_div(c, b) if b > 0 else float("inf")
    note = ""
    if (b + c) == 0:
        note = "No discordant pairs; McNemar's test undefined. Direction reported from point estimates only."
    return StratumResult(
        stratum=stratum,
        n_pairs=n,
        a=a, b=b, c=c, d=d,
        p_lora=p_lora,
        p_base=p_base,
        diff=p_lora - p_base,
        ci_low=ci_lo,
        ci_high=ci_hi,
        mcnemar_p=p,
        matched_or=oratio,
        note=note,
    )


def power_verdict(stratum_results: dict[str, StratumResult]) -> str:
    """Pre-registration §4.2 decision rule."""
    n_c = next((r.n_pairs for r in stratum_results.values() if r.stratum == "C"), 0)
    n_w = next((r.n_pairs for r in stratum_results.values() if r.stratum == "W"), 0)
    if n_c >= 60 and n_w >= 60:
        return f"ADEQUATELY POWERED (n_C={n_c}, n_W={n_w}; >= 60 per stratum, ~80% power to detect 25pp delta)."
    if n_c >= 30 and n_w >= 30:
        return f"INDICATIVE (n_C={n_c}, n_W={n_w}; >= 30 per stratum, ~50% power to detect 25pp delta)."
    if n_c >= 15 and n_w >= 15:
        return f"UNDER-POWERED and EXPLORATORY (n_C={n_c}, n_W={n_W}; 15-30 per stratum)."
    return f"INSUFFICIENT (n_C={n_c}, n_W={n_w}; < 15 per stratum). Re-audit to grow the labeled set."


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_per_stratum_csv(results: list[StratumResult], path: Path) -> None:
    fieldnames = [
        "stratum", "n_pairs", "a_both_correct", "b_base_wrong_lora_correct",
        "c_base_correct_lora_wrong", "d_both_wrong",
        "p_lora_error", "p_base_error", "diff_lora_minus_base",
        "ci95_low", "ci95_high", "mcnemar_p", "matched_pair_or", "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "stratum": r.stratum,
                "n_pairs": r.n_pairs,
                "a_both_correct": r.a,
                "b_base_wrong_lora_correct": r.b,
                "c_base_correct_lora_wrong": r.c,
                "d_both_wrong": r.d,
                "p_lora_error": f"{r.p_lora:.3f}",
                "p_base_error": f"{r.p_base:.3f}",
                "diff_lora_minus_base": f"{r.diff:+.3f}",
                "ci95_low": f"{r.ci_low:+.3f}",
                "ci95_high": f"{r.ci_high:+.3f}",
                "mcnemar_p": f"{r.mcnemar_p:.4f}" if not math.isnan(r.mcnemar_p) else "n/a",
                "matched_pair_or": "inf" if r.matched_or == float("inf") else f"{r.matched_or:.2f}",
                "note": r.note,
            })


def write_per_prompt_csv(rows: list[dict], path: Path) -> None:
    fieldnames = ["prompt_id", "stratum", "base_label", "lora_label",
                  "base_source_url", "lora_source_url", "base_notes", "lora_notes"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})


def write_excluded_csv(rows: list[dict], path: Path) -> None:
    fieldnames = ["prompt_id", "stratum", "base_label", "lora_label", "exclusion_reason"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% CI on a binomial proportion. Returns (low, high)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def _base_labels(rows: list[dict]) -> tuple[int, int]:
    """Return (n_base_wrong, n_lora_wrong) for a stratum row set, after exclusions."""
    n_b = sum(1 for r in rows if (r.get("base_label") or "").strip().lower() == "wrong")
    n_l = sum(1 for r in rows if (r.get("lora_label") or "").strip().lower() == "wrong")
    return n_b, n_l


def write_forest_plot(results: list[StratumResult], path: Path) -> bool:
    """Write a forest plot if matplotlib is available. Returns True on success.

    The plotted CIs are Wilson 95% intervals on the per-stratum error rates
    (not the difference CI), so the x-axis is naturally bounded to [0, 1].
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available; skipping forest plot.")
        return False
    if not results:
        return False

    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    y_positions = list(range(len(results)))
    labels = [r.stratum for r in results]
    for y, r in zip(y_positions, results):
        # Re-derive the per-stratum wrong counts so we can compute Wilson CIs on rates.
        # We have n_pairs and the 2x2 cells; error rate = (b + d) / n for base, (c + d) / n for LoRA.
        n = r.n_pairs
        n_b_wrong = r.b + r.d
        n_l_wrong = r.c + r.d
        b_lo, b_hi = _wilson_ci(n_b_wrong, n)
        l_lo, l_hi = _wilson_ci(n_l_wrong, n)
        # base
        ax.errorbar(
            r.p_base, y - 0.15,
            xerr=[[r.p_base - b_lo], [b_hi - r.p_base]],
            fmt="o", color="C0", capsize=4, label="Base" if y == 0 else None,
            markersize=7,
        )
        # lora
        ax.errorbar(
            r.p_lora, y + 0.15,
            xerr=[[r.p_lora - l_lo], [l_hi - r.p_lora]],
            fmt="s", color="C3", capsize=4, label="LoRA" if y == 0 else None,
            markersize=7,
        )
        # stratum size annotation
        ax.text(0.98, y, f"n={n}", transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=8, color="gray")
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.set_xlim(-0.02, max(0.6, max(r.p_lora for r in results) + 0.15))
    ax.set_xlabel("Source-verified factual error rate (Wilson 95% CI)")
    ax.set_title("Stratified source-verified error rates: base vs LoRA")
    ax.legend(loc="upper left", frameon=True)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def write_summary(results: list[StratumResult], verdict: str, path: Path) -> None:
    lines: list[str] = []
    lines.append("=" * 64)
    lines.append("STRATIFIED CAUSAL TEST — RESULTS SUMMARY (v5 §4.4.3)")
    lines.append("=" * 64)
    for r in results:
        lines.append("")
        lines.append(f"Stratum {r.stratum}  (n = {r.n_pairs} pairs)")
        lines.append(f"  2x2: a={r.a}  b={r.b} (base wrong, LoRA correct)  c={r.c} (base correct, LoRA wrong)  d={r.d}")
        lines.append(f"  Base error rate: {r.p_base:.3f}")
        lines.append(f"  LoRA error rate: {r.p_lora:.3f}")
        lines.append(f"  Diff (LoRA - Base): {r.diff:+.3f}  95% CI [{r.ci_low:+.3f}, {r.ci_high:+.3f}]")
        if math.isnan(r.mcnemar_p):
            lines.append(f"  McNemar's p: n/a ({r.note})")
        else:
            lines.append(f"  McNemar's p (with continuity correction): {r.mcnemar_p:.4f}")
        if r.matched_or == float("inf"):
            lines.append("  Matched-pair OR (c/b): inf (no b cases)")
        else:
            lines.append(f"  Matched-pair OR (c/b): {r.matched_or:.2f}")
    lines.append("")
    lines.append(f"Power verdict (§4.2 of the pre-registration): {verdict}")
    lines.append("")
    # Decision-rule summary (pre-registration §6.4)
    if "C" in [r.stratum for r in results] and "W" in [r.stratum for r in results]:
        w = next((r for r in results if r.stratum == "W"), None)
        c = next((r for r in results if r.stratum == "C"), None)
        if w and c and not math.isnan(w.mcnemar_p):
            w_p = w.mcnemar_p
            w_dir = w.diff > 0
            c_dir = c.diff > 0
            lines.append("Pre-registration §6.4 decision rule:")
            if w_p < 0.05 and w_dir and not c_dir:
                lines.append("  H1 holds in W but not C. Data attribution: ESTABLISHED.")
            elif w_dir and not c_dir and w_p >= 0.05:
                lines.append("  Direction consistent in W (LoRA worse) but under-powered. Data attribution: INDICATIVE.")
            elif w_dir and c_dir:
                lines.append("  LoRA worse in BOTH strata. Data attribution weakens to 'uniformly worse.'")
            else:
                lines.append("  LoRA not worse in W. Data attribution weakens.")
    lines.append("=" * 64)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run McNemar's tests on the stratified source-verified factuality audit.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--audit-results", type=Path, required=True,
                   help="CSV with prompt_id, stratum, base_label, lora_label columns (user-audited).")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--n-bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--strata", type=str, default="C,W",
                   help="Comma-separated list of strata to evaluate.")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    rows = load_audit_results(args.audit_results)
    allowed = [s.strip() for s in args.strata.split(",") if s.strip()]

    by_stratum: dict[str, list[dict]] = {s: [] for s in allowed}
    excluded: list[dict] = []
    for r in rows:
        s = r.get("stratum", "").strip()
        bl = (r.get("base_label") or "").strip().lower()
        ll = (r.get("lora_label") or "").strip().lower()
        if bl == "unclear" or ll == "unclear":
            r["exclusion_reason"] = "unclear_label"
            excluded.append(r)
            continue
        if s in by_stratum:
            by_stratum[s].append(r)
        else:
            excluded.append(r)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_per_prompt_csv(rows, args.output_dir / "per_prompt_results.csv")
    write_excluded_csv(excluded, args.output_dir / "excluded_prompts.csv")

    results: list[StratumResult] = []
    for s in allowed:
        results.append(evaluate_stratum(s, by_stratum[s], n_boot=args.n_bootstrap))

    write_per_stratum_csv(results, args.output_dir / "per_stratum_results.csv")
    wrote_plot = write_forest_plot(results, args.output_dir / "forest_plot.png")
    verdict = power_verdict({r.stratum: r for r in results})
    write_summary(results, verdict, args.output_dir / "summary.txt")

    # Also print the summary to stdout
    print((args.output_dir / "summary.txt").read_text(encoding="utf-8"))
    if wrote_plot:
        print(f"Forest plot: {args.output_dir / 'forest_plot.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
