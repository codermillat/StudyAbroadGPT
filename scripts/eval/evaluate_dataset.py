#!/usr/bin/env python3
"""
Evaluate StudyAbroadGPT-Dataset for academic dataset-quality evidence.

Outputs:
  - outputs/dataset_quality_metrics.json
  - outputs/dataset_quality_report.md
  - outputs/topic_annotation_template.csv
  - outputs/quality_review_template.csv

Primary checks:
  - structural validity and split statistics
  - exact duplicates and train/test leakage
  - repeated assistant responses
  - near-duplicate train/test pairs using TF-IDF cosine similarity > 0.90
  - lexical diversity metrics

This script is intentionally lightweight and reproducible for paper revision use.
"""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


DATASET_NAME = "millat/StudyAbroadGPT-Dataset"
NEAR_DUP_THRESHOLD = 0.90
OUTPUT_DIR = Path("outputs")


def ensure_package(package: str, import_name: str | None = None) -> None:
    """Install a missing package into the current Python environment."""
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installing missing dependency: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s.,;:!?%$€£₹/\-]", "", text)
    return text.strip()


def conversation_to_text(conversation: list[dict[str, str]]) -> str:
    parts = []
    for turn in conversation:
        role = str(turn.get("from", "")).strip()
        value = str(turn.get("value", "")).strip()
        parts.append(f"{role}: {value}")
    return "\n".join(parts)


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def distinct_n(texts: Iterable[str], n: int) -> float:
    total = 0
    unique: set[tuple[str, ...]] = set()
    for text in texts:
        toks = tokenize(text)
        grams = list(zip(*(toks[i:] for i in range(n)))) if len(toks) >= n else []
        total += len(grams)
        unique.update(grams)
    return len(unique) / total if total else 0.0


@dataclass
class Record:
    split: str
    index: int
    conversations: list[dict[str, str]]
    text: str
    norm_text: str
    turn_count: int
    user_turns: int
    assistant_turns: int
    valid_schema: bool
    role_alternation_ok: bool
    empty_values: int


def load_dataset_records() -> list[Record]:
    ensure_package("datasets")
    from datasets import load_dataset

    ds = load_dataset(DATASET_NAME)
    records: list[Record] = []
    for split in ds.keys():
        for idx, row in enumerate(ds[split]):
            conv = row.get("conversations", [])
            if not isinstance(conv, list):
                conv = []
            valid_schema = bool(conv) and all(
                isinstance(t, dict) and "from" in t and "value" in t for t in conv
            )
            roles = [str(t.get("from", "")).strip() for t in conv if isinstance(t, dict)]
            values = [str(t.get("value", "")) for t in conv if isinstance(t, dict)]
            role_alternation_ok = all(
                roles[i] != roles[i - 1] for i in range(1, len(roles))
            ) if roles else False
            text = conversation_to_text(conv)
            records.append(
                Record(
                    split=split,
                    index=idx,
                    conversations=conv,
                    text=text,
                    norm_text=normalize_text(text),
                    turn_count=len(conv),
                    user_turns=sum(1 for r in roles if r == "human"),
                    assistant_turns=sum(1 for r in roles if r == "assistant"),
                    valid_schema=valid_schema,
                    role_alternation_ok=role_alternation_ok,
                    empty_values=sum(1 for v in values if not v.strip()),
                )
            )
    return records


def mean_sd(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "sd": None, "min": None, "max": None}
    return {
        "mean": statistics.mean(values),
        "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def exact_duplicate_analysis(records: list[Record]) -> dict[str, Any]:
    by_text: dict[str, list[Record]] = defaultdict(list)
    for r in records:
        by_text[r.norm_text].append(r)

    duplicate_groups = {k: v for k, v in by_text.items() if len(v) > 1}
    train_norms = {r.norm_text for r in records if r.split == "train"}
    test_norms = {r.norm_text for r in records if r.split == "test"}
    overlap = train_norms & test_norms
    return {
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_record_count": sum(len(v) for v in duplicate_groups.values()),
        "train_test_exact_overlap_count": len(overlap),
        "examples": [
            {
                "normalized_prefix": k[:300],
                "locations": [f"{r.split}[{r.index}]" for r in v],
            }
            for k, v in list(duplicate_groups.items())[:10]
        ],
    }


def repeated_assistant_analysis(records: list[Record]) -> dict[str, Any]:
    responses: dict[str, list[str]] = defaultdict(list)
    for r in records:
        for turn_idx, turn in enumerate(r.conversations):
            if turn.get("from") == "assistant":
                norm = normalize_text(str(turn.get("value", "")))
                if norm:
                    responses[norm].append(f"{r.split}[{r.index}].turn{turn_idx}")
    repeated = {k: v for k, v in responses.items() if len(v) > 1}
    return {
        "unique_assistant_responses": len(responses),
        "repeated_response_group_count": len(repeated),
        "repeated_response_instance_count": sum(len(v) for v in repeated.values()),
        "examples": [
            {"response_prefix": k[:300], "locations": v[:10], "count": len(v)}
            for k, v in list(repeated.items())[:10]
        ],
    }


def near_duplicate_analysis(records: list[Record]) -> dict[str, Any]:
    ensure_package("scikit-learn", "sklearn")
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    train = [r for r in records if r.split == "train"]
    test = [r for r in records if r.split == "test"]
    if not train or not test:
        return {"error": "train or test split missing"}

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_features=50000,
        stop_words="english",
    )
    matrix = vectorizer.fit_transform([r.text for r in train + test])
    train_matrix = matrix[: len(train)]
    test_matrix = matrix[len(train) :]
    sim = cosine_similarity(test_matrix, train_matrix)

    pairs = []
    max_scores = []
    for test_idx in range(sim.shape[0]):
        row = sim[test_idx]
        max_train_idx = int(np.argmax(row))
        max_score = float(row[max_train_idx])
        max_scores.append(max_score)
        if max_score >= NEAR_DUP_THRESHOLD:
            pairs.append(
                {
                    "test": f"test[{test[test_idx].index}]",
                    "train": f"train[{train[max_train_idx].index}]",
                    "cosine_similarity": max_score,
                    "test_prefix": test[test_idx].text[:300],
                    "train_prefix": train[max_train_idx].text[:300],
                }
            )
    return {
        "method": "TF-IDF word unigrams+bigrams with English stop-word removal",
        "threshold": NEAR_DUP_THRESHOLD,
        "near_duplicate_pair_count": len(pairs),
        "near_duplicate_test_percentage": len(pairs) / len(test) * 100,
        "max_similarity_mean": statistics.mean(max_scores),
        "max_similarity_sd": statistics.stdev(max_scores) if len(max_scores) > 1 else 0.0,
        "max_similarity_min": min(max_scores),
        "max_similarity_max": max(max_scores),
        "examples": pairs[:20],
    }


def structural_analysis(records: list[Record]) -> dict[str, Any]:
    splits = sorted(set(r.split for r in records))
    split_stats = {}
    for split in splits:
        subset = [r for r in records if r.split == split]
        split_stats[split] = {
            "conversation_count": len(subset),
            "turn_count": mean_sd([r.turn_count for r in subset]),
            "user_turns": sum(r.user_turns for r in subset),
            "assistant_turns": sum(r.assistant_turns for r in subset),
            "valid_schema_count": sum(r.valid_schema for r in subset),
            "role_alternation_ok_count": sum(r.role_alternation_ok for r in subset),
            "empty_value_count": sum(r.empty_values for r in subset),
        }

    all_texts = [r.text for r in records]
    return {
        "dataset_name": DATASET_NAME,
        "total_conversations": len(records),
        "splits": split_stats,
        "total_user_turns": sum(r.user_turns for r in records),
        "total_assistant_turns": sum(r.assistant_turns for r in records),
        "schema_pass_rate_percent": sum(r.valid_schema for r in records) / len(records) * 100,
        "role_alternation_pass_rate_percent": sum(r.role_alternation_ok for r in records) / len(records) * 100,
        "empty_value_count": sum(r.empty_values for r in records),
        "distinct_1": distinct_n(all_texts, 1),
        "distinct_2": distinct_n(all_texts, 2),
    }


def create_annotation_templates(records: list[Record]) -> None:
    # Deterministic samples: spread across train/test by taking first N after sorting.
    samples = sorted(records, key=lambda r: (r.split, r.index))

    topic_labels = "admissions_application;scholarships_funding;visa_immigration;accommodation_living_costs;university_program_selection;documents_sop_cv_recommendations;language_tests_exams;student_life_cultural_adaptation;travel_prearrival;other_general"
    with (OUTPUT_DIR / "topic_annotation_template.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sample_id", "split", "index", "conversation_text", "primary_topic", "secondary_topic", "topic_label_options", "notes"],
        )
        writer.writeheader()
        for sid, r in enumerate(samples[:200], 1):
            writer.writerow(
                {
                    "sample_id": sid,
                    "split": r.split,
                    "index": r.index,
                    "conversation_text": r.text,
                    "primary_topic": "",
                    "secondary_topic": "",
                    "topic_label_options": topic_labels,
                    "notes": "",
                }
            )

    with (OUTPUT_DIR / "quality_review_template.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id",
                "split",
                "index",
                "conversation_text",
                "relevance_1_5",
                "helpfulness_1_5",
                "clarity_1_5",
                "completeness_1_5",
                "safety_caveating_1_5",
                "major_issue_flag",
                "notes",
            ],
        )
        writer.writeheader()
        for sid, r in enumerate(samples[:100], 1):
            writer.writerow(
                {
                    "sample_id": sid,
                    "split": r.split,
                    "index": r.index,
                    "conversation_text": r.text,
                    "relevance_1_5": "",
                    "helpfulness_1_5": "",
                    "clarity_1_5": "",
                    "completeness_1_5": "",
                    "safety_caveating_1_5": "",
                    "major_issue_flag": "",
                    "notes": "",
                }
            )


def fmt_num(x: Any, digits: int = 2) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def write_report(metrics: dict[str, Any]) -> None:
    structural = metrics["structural"]
    exact = metrics["exact_duplicates"]
    near = metrics["near_duplicates"]
    repeated = metrics["repeated_assistant_responses"]
    train = structural["splits"].get("train", {})
    test = structural["splits"].get("test", {})

    report = f"""# StudyAbroadGPT-Dataset Quality Assessment

Generated by `evaluate_dataset.py`.

## 1. Dataset Scope

The evaluated dataset is `{DATASET_NAME}`, a synthetic, manually reviewed conversational dataset for study-abroad academic advising.

## 2. Structural Quality

| Property | Value |
|---|---:|
| Total conversations | {structural['total_conversations']} |
| Train conversations | {train.get('conversation_count', 'NA')} |
| Test conversations | {test.get('conversation_count', 'NA')} |
| Total user turns | {structural['total_user_turns']} |
| Total assistant turns | {structural['total_assistant_turns']} |
| Schema pass rate | {fmt_num(structural['schema_pass_rate_percent'])}% |
| Role alternation pass rate | {fmt_num(structural['role_alternation_pass_rate_percent'])}% |
| Empty value count | {structural['empty_value_count']} |
| Train mean turns ± SD | {fmt_num(train.get('turn_count', {}).get('mean'))} ± {fmt_num(train.get('turn_count', {}).get('sd'))} |
| Test mean turns ± SD | {fmt_num(test.get('turn_count', {}).get('mean'))} ± {fmt_num(test.get('turn_count', {}).get('sd'))} |
| Train turn range | {fmt_num(train.get('turn_count', {}).get('min'), 0)}–{fmt_num(train.get('turn_count', {}).get('max'), 0)} |
| Test turn range | {fmt_num(test.get('turn_count', {}).get('min'), 0)}–{fmt_num(test.get('turn_count', {}).get('max'), 0)} |
| Distinct-1 | {fmt_num(structural['distinct_1'], 4)} |
| Distinct-2 | {fmt_num(structural['distinct_2'], 4)} |

## 3. Leakage and Duplication Analysis

| Check | Method | Result |
|---|---|---:|
| Exact duplicate groups | Normalized full-conversation string matching | {exact['duplicate_group_count']} |
| Records involved in exact duplicates | Normalized full-conversation string matching | {exact['duplicate_record_count']} |
| Train/test exact overlaps | Normalized full-conversation string matching | {exact['train_test_exact_overlap_count']} |
| Near-duplicate train/test pairs | {near.get('method', 'TF-IDF cosine similarity')} at threshold ≥ {near.get('threshold', NEAR_DUP_THRESHOLD)} | {near.get('near_duplicate_pair_count', 'NA')} |
| Near-duplicate test-set percentage | Same as above | {fmt_num(near.get('near_duplicate_test_percentage'))}% |
| Repeated assistant response groups | Normalized assistant-message matching | {repeated['repeated_response_group_count']} |

Interpretation: exact train/test overlap directly indicates leakage risk. Near-duplicate pairs should be manually inspected before claiming leakage, because semantically similar advising questions may be legitimate in a narrow domain.

## 4. Synthetic-Validity Paragraph for Paper

The StudyAbroadGPT-Dataset was developed as a synthetic domain-specific corpus because no open, labeled conversational dataset was available for study-abroad academic advising in low-resource contexts. Synthetic generation enabled coverage of recurring student questions across admissions, scholarships, visa preparation, accommodation, documentation, and academic planning, while manual review was used to improve clarity, remove irrelevant outputs, and reduce unsafe or unsupported advice. Approximately [INSERT NUMBER] conversations were manually inspected and corrected after synthetic generation. The dataset is therefore intended as an experimental fine-tuning resource rather than a replacement for official university or immigration sources. Its validity is supported through structural checks, train/test leakage analysis, topic coverage analysis, and downstream model performance rather than through claims of exhaustive factual completeness.

## 5. Recommended Topic Coverage Reporting

Use `outputs/topic_annotation_template.csv` to manually annotate 100–200 conversations. If time is limited, 100 carefully annotated samples are defensible.

Recommended labels:

1. admissions/application requirements
2. scholarships/funding
3. visa/immigration preparation
4. accommodation/living costs
5. university/program selection
6. documents/SOP/CV/recommendations
7. language tests/exams
8. student life/cultural adaptation
9. travel/pre-arrival preparation
10. other/general advising

## 6. Recommended Human Quality Review

Use `outputs/quality_review_template.csv` to score 100 conversations on a 1–5 scale for relevance, helpfulness, clarity, completeness, and safety/caveating.

Paper wording if one annotator is used:

> Because the quality review was conducted by a single annotator, inter-annotator agreement was not computed; future work should include multi-rater expert evaluation.

## 7. Limitations Paragraph for Paper

The dataset is synthetic and was not validated against a comprehensive database of official university or immigration policies. Therefore, although it is useful for studying parameter-efficient domain adaptation, it should not be interpreted as a verified advising knowledge base. Future work should incorporate retrieval-augmented generation from official sources, multi-rater expert annotation, and bias analysis across destination countries, socioeconomic backgrounds, and applicant profiles.

## 8. Downstream Utility Framing

The downstream improvement of the LoRA-adapted model over the base instruction model provides task-level evidence that the dataset contains useful domain-specific supervision, despite its synthetic origin. The paper should present this as evidence of domain adaptation utility, not as proof that the dataset is factually exhaustive.
"""
    (OUTPUT_DIR / "dataset_quality_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Loading {DATASET_NAME}...")
    records = load_dataset_records()
    print(f"Loaded {len(records)} conversations.")

    metrics = {
        "structural": structural_analysis(records),
        "exact_duplicates": exact_duplicate_analysis(records),
        "repeated_assistant_responses": repeated_assistant_analysis(records),
        "near_duplicates": near_duplicate_analysis(records),
    }

    (OUTPUT_DIR / "dataset_quality_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    create_annotation_templates(records)
    write_report(metrics)

    print("\nKey results:")
    print(json.dumps({
        "total_conversations": metrics["structural"]["total_conversations"],
        "schema_pass_rate_percent": metrics["structural"]["schema_pass_rate_percent"],
        "train_test_exact_overlap_count": metrics["exact_duplicates"]["train_test_exact_overlap_count"],
        "near_duplicate_pair_count": metrics["near_duplicates"].get("near_duplicate_pair_count"),
        "near_duplicate_test_percentage": metrics["near_duplicates"].get("near_duplicate_test_percentage"),
        "repeated_response_group_count": metrics["repeated_assistant_responses"]["repeated_response_group_count"],
    }, indent=2))
    print(f"\nWrote outputs to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()