#!/usr/bin/env python3
"""Analyze LLM-as-judge scores: base vs LoRA, with bootstrap CIs.

Reads the pointwise judge output from llm_judge_eval.py, rejoins the source
mapping (which blinded slot was base vs LoRA per sample), and reports:

  * Per-model mean +/- SD for domain accuracy (0-3) and helpfulness (0-3).
  * Paired delta (LoRA - base) with a bootstrap 95% CI over per-sample deltas.
  * Win / tie / loss rate from the judge's preference, de-blinded to model.

A delta whose 95% CI excludes 0 is the only one to describe as a signal.

Usage:
    python analyze_judge_scores.py \
        --scores  outputs/Model_llm_judge_scores.csv \
        --mapping LoRA_Output/outputs/Model_downstream_blinded_mapping_revealed.csv \
        --out     outputs/Model_llm_judge_summary.md
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import statistics

BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 42


def load_mapping(path: str) -> dict[str, dict[str, str]]:
    """sample_id -> {"a": source, "b": source}, source in {base, lora}."""
    mapping = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            mapping[row["sample_id"]] = {
                "a": row["response_a_source"].strip().lower(),
                "b": row["response_b_source"].strip().lower(),
            }
    return mapping


def deblind(scores_path: str, mapping: dict[str, dict[str, str]]) -> list[dict]:
    """Map each pair's blinded slot scores onto base/lora."""
    out = []
    with open(scores_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sid = row["sample_id"]
            src = mapping[sid]  # {"a": base/lora, "b": base/lora}
            rec = {"sample_id": sid}
            for slot in ("a", "b"):
                model = src[slot]
                rec[f"{model}_domain"] = int(row[f"domain_{slot}"])
                rec[f"{model}_help"] = int(row[f"help_{slot}"])
            pref = row["preferred_slot"]
            rec["pref_model"] = "tie" if pref == "tie" else src[pref]
            out.append(rec)
    return out


def mean_sd(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return statistics.mean(values), (statistics.pstdev(values) if len(values) > 1 else 0.0)


def bootstrap_ci(deltas: list[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(deltas)
    means = sorted(
        statistics.mean(deltas[rng.randrange(n)] for _ in range(n))
        for _ in range(BOOTSTRAP_RESAMPLES)
    )
    return means[int(0.025 * BOOTSTRAP_RESAMPLES)], means[int(0.975 * BOOTSTRAP_RESAMPLES)]


def summarize(records: list[dict]) -> str:
    n = len(records)
    lines = [
        "# LLM-as-Judge Evaluation Summary",
        "",
        "**Methodology disclosure:** scores below are produced by an LLM judge "
        "(pointwise absolute scoring against the project rubric), NOT by human "
        "raters. The judge is a different model family from the Gemini generator "
        "used for the dataset and reference answers. This is an LLM-as-judge "
        "protocol; it complements, but does not replace, human or real-user "
        "evaluation, and must be named as such in the manuscript.",
        "",
        f"Samples: **{n}** | Scale: domain accuracy and helpfulness each **0-3** "
        f"| Bootstrap: **{BOOTSTRAP_RESAMPLES} resamples, seed {BOOTSTRAP_SEED}**",
        "",
        "| Metric | Base (mean +/- SD) | LoRA (mean +/- SD) | Delta (LoRA - Base) | 95% CI on Delta |",
        "|---|---:|---:|---:|---|",
    ]
    for key, label in (("domain", "Domain Accuracy (0-3)"), ("help", "Helpfulness (0-3)")):
        base_vals = [r[f"base_{key}"] for r in records]
        lora_vals = [r[f"lora_{key}"] for r in records]
        deltas = [lo - b for lo, b in zip(lora_vals, base_vals)]
        bm, bs = mean_sd(base_vals)
        lm, ls = mean_sd(lora_vals)
        dlo, dhi = bootstrap_ci(deltas)
        signal = "" if (dlo <= 0 <= dhi) else " *(CI excludes 0)*"
        lines.append(
            f"| {label} | {bm:.3f} +/- {bs:.3f} | {lm:.3f} +/- {ls:.3f} "
            f"| {lm - bm:+.3f}{signal} | [{dlo:+.3f}, {dhi:+.3f}] |"
        )

    win = sum(r["pref_model"] == "lora" for r in records)
    loss = sum(r["pref_model"] == "base" for r in records)
    tie = sum(r["pref_model"] == "tie" for r in records)
    lines += [
        "",
        "## Preference vote (de-blinded)",
        "",
        f"- LoRA preferred: **{win}/{n}** ({win/n:.0%})",
        f"- Base preferred: **{loss}/{n}** ({loss/n:.0%})",
        f"- Tie: **{tie}/{n}** ({tie/n:.0%})",
        "",
        "## Reporting guidance",
        "",
        "- Label explicitly as LLM-as-judge; report the CI with every delta.",
        "- Only a delta whose 95% CI excludes 0 is a signal; others are "
        "'no measurable difference'.",
        "- Do NOT present this as the human evaluation Reviewer 2 requested; "
        "name it as a complementary automatic measure on synthetic-split prompts.",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--out", default="outputs/Model_llm_judge_summary.md")
    args = parser.parse_args()

    mapping = load_mapping(args.mapping)
    records = deblind(args.scores, mapping)
    report = summarize(records)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print(report)
    print(f"\nWrote summary -> {args.out}")


if __name__ == "__main__":
    main()
