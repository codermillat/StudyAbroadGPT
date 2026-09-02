#!/usr/bin/env python3
"""
Create a 50-sample factuality audit template for StudyAbroadGPT-Dataset.

The template supports source-grounded checking of knowledge quality, including
official-source verification for claims about visas, admissions, costs,
scholarships, healthcare, accommodation, and university policy.
"""

from __future__ import annotations

import csv
import random
import subprocess
import sys
from pathlib import Path


DATASET_NAME = "millat/StudyAbroadGPT-Dataset"
OUTPUT_PATH = Path("outputs/factuality_audit_template.csv")
SAMPLE_SIZE = 50
RANDOM_SEED = 123


def ensure_package(package: str, import_name: str | None = None) -> None:
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def first_user_and_assistant(conversation: list[dict]) -> tuple[str, str]:
    user_question = ""
    assistant_response = ""
    for turn in conversation:
        role = turn.get("from")
        value = str(turn.get("value", "")).replace("\r", " ").replace("\n", " ").strip()
        if role == "human" and not user_question:
            user_question = value
        elif role == "assistant" and not assistant_response:
            assistant_response = value
        if user_question and assistant_response:
            break
    return user_question, assistant_response


def main() -> None:
    ensure_package("datasets")
    from datasets import load_dataset

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    dataset = load_dataset(DATASET_NAME, split="test")
    indices = list(range(len(dataset)))
    random.Random(RANDOM_SEED).shuffle(indices)
    selected = indices[:SAMPLE_SIZE]

    fieldnames = [
        "conversation_id",
        "split",
        "test_index",
        "user_question",
        "assistant_response",
        "factual_claims",
        "official_source_url",
        "source_type",
        "factuality_score_0_2",
        "policy_sensitivity",
        "needs_caveat",
        "notes",
    ]

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for idx in selected:
            item = dataset[idx]
            user_question, assistant_response = first_user_and_assistant(item.get("conversations", []))
            writer.writerow(
                {
                    "conversation_id": f"test_{idx}",
                    "split": "test",
                    "test_index": idx,
                    "user_question": user_question,
                    "assistant_response": assistant_response,
                    "factual_claims": "",
                    "official_source_url": "",
                    "source_type": "",
                    "factuality_score_0_2": "",
                    "policy_sensitivity": "",
                    "needs_caveat": "",
                    "notes": "",
                }
            )

    print(f"Saved {SAMPLE_SIZE} sampled test responses to {OUTPUT_PATH}")
    print(f"Random seed: {RANDOM_SEED}")


if __name__ == "__main__":
    main()