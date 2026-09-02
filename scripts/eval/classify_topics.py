#!/usr/bin/env python3
"""
Keyword-based topic classification for the first 200 train conversations in
millat/StudyAbroadGPT-Dataset.

The script extracts the first user/human turn from each conversation, assigns
one of 10 study-abroad advising labels using deterministic keyword matching,
saves outputs/topic_annotation_results.csv, and prints a frequency table.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


DATASET_NAME = "millat/StudyAbroadGPT-Dataset"
OUTPUT_PATH = Path("outputs/topic_annotation_results.csv")
SAMPLE_SIZE = 200


LABEL_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        "admissions/application requirements",
        [
            "admission",
            "apply",
            "application",
            "eligibility",
            "requirement",
            "requirements",
            "deadline",
            "intake",
            "acceptance",
            "offer letter",
            "entry criteria",
            "minimum gpa",
            "cgpa",
        ],
    ),
    (
        "scholarships/funding",
        [
            "scholarship",
            "scholarships",
            "funding",
            "financial aid",
            "grant",
            "tuition waiver",
            "stipend",
            "assistantship",
            "loan",
            "bursary",
            "fee waiver",
            "cost of study",
            "afford",
        ],
    ),
    (
        "visa/immigration preparation",
        [
            "visa",
            "immigration",
            "embassy",
            "consulate",
            "study permit",
            "student permit",
            "i-20",
            "cas",
            "sevis",
            "biometrics",
            "passport",
            "residence permit",
            "interview",
        ],
    ),
    (
        "accommodation/living costs",
        [
            "accommodation",
            "housing",
            "hostel",
            "dorm",
            "rent",
            "apartment",
            "living cost",
            "living costs",
            "cost of living",
            "budget",
            "expenses",
            "meal",
            "food cost",
        ],
    ),
    (
        "university/program selection",
        [
            "university",
            "universities",
            "college",
            "program",
            "course",
            "major",
            "ranking",
            "choose",
            "select",
            "best country",
            "destination",
            "which country",
            "which university",
        ],
    ),
    (
        "documents/SOP/CV/recommendations",
        [
            "document",
            "documents",
            "sop",
            "statement of purpose",
            "personal statement",
            "cv",
            "resume",
            "recommendation",
            "lor",
            "reference letter",
            "transcript",
            "portfolio",
            "motivation letter",
        ],
    ),
    (
        "language tests/exams",
        [
            "ielts",
            "toefl",
            "pte",
            "duolingo",
            "gre",
            "gmat",
            "sat",
            "act",
            "language test",
            "english test",
            "exam",
            "test score",
            "band score",
        ],
    ),
    (
        "student life/cultural adaptation",
        [
            "student life",
            "culture",
            "cultural",
            "adapt",
            "homesick",
            "community",
            "part-time",
            "part time",
            "job",
            "work while studying",
            "health insurance",
            "safety",
            "weather",
            "social life",
        ],
    ),
    (
        "travel/pre-arrival preparation",
        [
            "travel",
            "flight",
            "arrival",
            "pre-arrival",
            "pre arrival",
            "airport",
            "packing",
            "ticket",
            "luggage",
            "quarantine",
            "orientation",
            "before leaving",
            "departure",
        ],
    ),
]

OTHER_LABEL = "other/general advising"


def ensure_package(package: str, import_name: str | None = None) -> None:
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def keyword_found(text: str, keyword: str) -> bool:
    if re.search(r"\W", keyword):
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def classify_topic(first_user_turn: str) -> tuple[str, str]:
    text = normalize(first_user_turn)
    scores: list[tuple[int, str, list[str]]] = []
    for label, keywords in LABEL_KEYWORDS:
        matches = [kw for kw in keywords if keyword_found(text, kw)]
        if matches:
            scores.append((len(matches), label, matches))

    if not scores:
        return OTHER_LABEL, ""

    scores.sort(key=lambda item: item[0], reverse=True)
    _, label, matches = scores[0]
    return label, "; ".join(matches)


def first_human_turn(conversation: list[dict]) -> str:
    for turn in conversation:
        if turn.get("from") == "human":
            return str(turn.get("value", ""))
    return ""


def main() -> None:
    ensure_package("datasets")
    from datasets import load_dataset

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    dataset = load_dataset(DATASET_NAME, split=f"train[:{SAMPLE_SIZE}]")

    rows = []
    frequency: Counter[str] = Counter()
    for idx, item in enumerate(dataset):
        conversation = item.get("conversations", [])
        first_turn = first_human_turn(conversation)
        label, matched_keywords = classify_topic(first_turn)
        frequency[label] += 1
        rows.append(
            {
                "sample_id": idx + 1,
                "split": "train",
                "index": idx,
                "first_user_turn": first_turn,
                "predicted_topic": label,
                "matched_keywords": matched_keywords,
            }
        )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "sample_id",
                "split",
                "index",
                "first_user_turn",
                "predicted_topic",
                "matched_keywords",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("Topic frequency table for first 200 train conversations")
    print("=" * 60)
    print(f"{'Topic':45} Count  Percent")
    print("-" * 60)
    for label, _ in LABEL_KEYWORDS + [(OTHER_LABEL, [])]:
        count = frequency[label]
        percent = (count / SAMPLE_SIZE) * 100
        print(f"{label:45} {count:5d}  {percent:6.2f}%")
    print("-" * 60)
    print(f"{'TOTAL':45} {sum(frequency.values()):5d}  {100.00:6.2f}%")
    print(f"\nSaved results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()