#!/usr/bin/env python3
"""
Summarize StudyAbroadGPT dataset evaluation CSVs after manual review.

Inputs, if present:
  - outputs/topic_annotation_results.csv
  - outputs/quality_review_template.csv
  - outputs/downstream_evaluation_template.csv

Output:
  - outputs/manual_evaluation_summary.md

The script is safe to run before manual scoring is complete. Blank scoring
columns are ignored and reported as pending.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import subprocess
import sys


def ensure_package(package: str, import_name: str | None = None) -> None:
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


ensure_package("pandas")
import pandas as pd


OUTPUT_DIR = Path("outputs")
TOPIC_FILE = OUTPUT_DIR / "topic_annotation_results.csv"
QUALITY_FILE = OUTPUT_DIR / "quality_review_template.csv"
DOWNSTREAM_FILE = OUTPUT_DIR / "downstream_evaluation_template.csv"
SUMMARY_FILE = OUTPUT_DIR / "manual_evaluation_summary.md"


def numeric_summary(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    available = [col for col in columns if col in df.columns]
    if not available:
        return pd.DataFrame()
    numeric = df[available].apply(pd.to_numeric, errors="coerce")
    rows = []
    for col in available:
        series = numeric[col].dropna()
        if series.empty:
            rows.append({"Metric": col, "N": 0, "Mean": None, "SD": None})
        else:
            rows.append(
                {
                    "Metric": col,
                    "N": int(series.count()),
                    "Mean": float(series.mean()),
                    "SD": float(series.std(ddof=1)) if series.count() > 1 else 0.0,
                }
            )
    return pd.DataFrame(rows)


def markdown_numeric_table(summary: pd.DataFrame) -> str:
    if summary.empty:
        return "No matching scoring columns found."
    lines = ["| Metric | N | Mean ± SD |", "|---|---:|---:|"]
    for _, row in summary.iterrows():
        if row["N"] == 0 or pd.isna(row["Mean"]):
            value = "Pending manual scoring"
        else:
            value = f"{row['Mean']:.2f} ± {row['SD']:.2f}"
        lines.append(f"| {row['Metric']} | {int(row['N'])} | {value} |")
    return "\n".join(lines)


def topic_section() -> str:
    if not TOPIC_FILE.exists():
        return "## Topic Coverage\n\n`outputs/topic_annotation_results.csv` not found.\n"
    df = pd.read_csv(TOPIC_FILE)
    if "predicted_topic" not in df.columns:
        return "## Topic Coverage\n\n`predicted_topic` column not found.\n"
    counts = df["predicted_topic"].fillna("missing").value_counts()
    total = int(counts.sum())
    lines = [
        "## Topic Coverage",
        "",
        f"Total annotated samples: **{total}**",
        "",
        "| Topic | Count | Percent |",
        "|---|---:|---:|",
    ]
    for topic, count in counts.items():
        lines.append(f"| {topic} | {int(count)} | {(count / total * 100):.2f}% |")
    return "\n".join(lines) + "\n"


def quality_section() -> str:
    if not QUALITY_FILE.exists():
        return "## Human Quality Review\n\n`outputs/quality_review_template.csv` not found.\n"
    df = pd.read_csv(QUALITY_FILE)
    columns = [
        "relevance_1_5",
        "helpfulness_1_5",
        "clarity_1_5",
        "completeness_1_5",
        "safety_1_5",
        "safety_caveating_1_5",
    ]
    summary = numeric_summary(df, columns)
    completed = 0
    if not summary.empty:
        completed = int(summary["N"].max())
    return (
        "## Human Quality Review\n\n"
        f"Rows in template: **{len(df)}**\n\n"
        f"Maximum completed score count in any dimension: **{completed}**\n\n"
        f"{markdown_numeric_table(summary)}\n"
    )


def downstream_section() -> str:
    if not DOWNSTREAM_FILE.exists():
        return "## Downstream Utility Evaluation\n\n`outputs/downstream_evaluation_template.csv` not found.\n"
    df = pd.read_csv(DOWNSTREAM_FILE)
    columns = [
        "domain_accuracy_base",
        "domain_accuracy_lora",
        "helpfulness_base",
        "helpfulness_lora",
    ]
    summary = numeric_summary(df, columns)
    response_counts = []
    for col in ["base_model_response", "lora_model_response"]:
        if col in df.columns:
            nonblank = df[col].fillna("").astype(str).str.strip().ne("").sum()
            response_counts.append(f"- `{col}` populated rows: **{int(nonblank)} / {len(df)}**")
    return (
        "## Downstream Utility Evaluation\n\n"
        f"Rows in template: **{len(df)}**\n\n"
        + "\n".join(response_counts)
        + "\n\n"
        + markdown_numeric_table(summary)
        + "\n"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    report = "\n\n".join(
        [
            "# Manual Evaluation Summary",
            "This summary is generated from the topic, quality-review, and downstream-evaluation CSV files. Blank manual scoring cells are treated as pending.",
            topic_section(),
            quality_section(),
            downstream_section(),
            "## Paper Use\n\nUse completed tables from this file in the `Dataset Quality Assessment` section after manual review/scoring is finished. If a table says `Pending manual scoring`, do not report it as a completed result yet.",
        ]
    )
    SUMMARY_FILE.write_text(report, encoding="utf-8")
    print(f"Wrote {SUMMARY_FILE}")


if __name__ == "__main__":
    main()