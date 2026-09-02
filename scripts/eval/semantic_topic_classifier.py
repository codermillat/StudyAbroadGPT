#!/usr/bin/env python3
"""
Semantic topic classification for StudyAbroadGPT-Dataset.

This script classifies the first 200 train conversations into the same 10
study-abroad advising labels used by `classify_topics.py`, but uses semantic
similarity against richer label descriptions rather than direct keyword rules.

Preferred backend:
  - sentence-transformers, if already installed.

Fallback backend:
  - scikit-learn TF-IDF cosine similarity over user questions and label
    descriptions. This fallback is still description-based and more flexible
    than exact keyword matching, while remaining lightweight and reproducible.

Output:
  - outputs/semantic_topic_annotation_results.csv
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from typing import Callable


DATASET_NAME = "millat/StudyAbroadGPT-Dataset"
OUTPUT_PATH = Path("outputs/semantic_topic_annotation_results.csv")
SAMPLE_SIZE = 200
LOW_CONFIDENCE_MARGIN = 0.05


TOPIC_DESCRIPTIONS: list[tuple[str, str]] = [
    (
        "admissions/application requirements",
        "Questions about university admission, application requirements, eligibility, deadlines, academic criteria, GPA, acceptance, intakes, and applying to programs.",
    ),
    (
        "scholarships/funding",
        "Questions about scholarships, financial aid, grants, funding, tuition waivers, stipends, assistantships, education loans, affordability, and paying for study abroad.",
    ),
    (
        "visa/immigration preparation",
        "Questions about student visas, immigration rules, embassy interviews, study permits, residence permits, passports, biometrics, CAS, I-20, SEVIS, and immigration documents.",
    ),
    (
        "accommodation/living costs",
        "Questions about housing, student accommodation, dormitories, hostels, rent, apartments, monthly budget, living expenses, food costs, transport costs, and cost of living.",
    ),
    (
        "university/program selection",
        "Questions about choosing universities, selecting countries, comparing programs, majors, courses, rankings, academic fit, destination choice, and matching profile to institutions.",
    ),
    (
        "documents/SOP/CV/recommendations",
        "Questions about required documents, statement of purpose, personal statement, CV, resume, recommendation letters, reference letters, transcripts, portfolios, and motivation letters.",
    ),
    (
        "language tests/exams",
        "Questions about IELTS, TOEFL, PTE, Duolingo English Test, GRE, GMAT, SAT, ACT, standardized exams, English proficiency, test scores, and band requirements.",
    ),
    (
        "student life/cultural adaptation",
        "Questions about student life, cultural adjustment, making friends, networking, homesickness, part-time jobs, work while studying, health insurance, safety, weather, campus life, and social life.",
    ),
    (
        "travel/pre-arrival preparation",
        "Questions about travel planning, flights, tickets, packing, luggage, airport arrival, pre-arrival tasks, orientation, quarantine, departure, and what to do before leaving home.",
    ),
    (
        "other/general advising",
        "General study-abroad advising questions that do not clearly fit admissions, funding, visa, housing, university selection, documents, exams, student life, or travel preparation.",
    ),
]


def ensure_package(package: str, import_name: str | None = None) -> None:
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def first_human_turn(conversation: list[dict]) -> str:
    for turn in conversation:
        if turn.get("from") == "human":
            return str(turn.get("value", "")).strip()
    return ""


def sentence_transformer_classifier() -> tuple[str, Callable[[list[str], list[str]], list[list[float]]]] | None:
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return None

    model = SentenceTransformer("all-MiniLM-L6-v2")

    def score(texts: list[str], descriptions: list[str]) -> list[list[float]]:
        text_embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        desc_embeddings = model.encode(descriptions, normalize_embeddings=True, show_progress_bar=False)
        return cosine_similarity(text_embeddings, desc_embeddings).tolist()

    return "sentence-transformers/all-MiniLM-L6-v2", score


def tfidf_classifier() -> tuple[str, Callable[[list[str], list[str]], list[list[float]]]]:
    ensure_package("scikit-learn", "sklearn")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    def score(texts: list[str], descriptions: list[str]) -> list[list[float]]:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            stop_words="english",
            min_df=1,
        )
        matrix = vectorizer.fit_transform(texts + descriptions)
        text_matrix = matrix[: len(texts)]
        desc_matrix = matrix[len(texts) :]
        return cosine_similarity(text_matrix, desc_matrix).tolist()

    return "TF-IDF description similarity fallback", score


def choose_classifier() -> tuple[str, Callable[[list[str], list[str]], list[list[float]]]]:
    semantic = sentence_transformer_classifier()
    if semantic is not None:
        return semantic
    return tfidf_classifier()


def main() -> None:
    ensure_package("datasets")
    from datasets import load_dataset

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    dataset = load_dataset(DATASET_NAME, split=f"train[:{SAMPLE_SIZE}]")
    labels = [label for label, _ in TOPIC_DESCRIPTIONS]
    descriptions = [description for _, description in TOPIC_DESCRIPTIONS]
    questions = [first_human_turn(item.get("conversations", [])) for item in dataset]

    backend_name, score_fn = choose_classifier()
    similarities = score_fn(questions, descriptions)

    rows = []
    counts = {label: 0 for label in labels}
    for idx, (question, sims) in enumerate(zip(questions, similarities)):
        ranked = sorted(enumerate(sims), key=lambda pair: pair[1], reverse=True)
        best_idx, best_score = ranked[0]
        second_idx, second_score = ranked[1]
        predicted = labels[best_idx]
        counts[predicted] += 1
        rows.append(
            {
                "conversation_id": f"train_{idx}",
                "split": "train",
                "train_index": idx,
                "first_user_question": question,
                "predicted_topic": predicted,
                "similarity_score": f"{best_score:.6f}",
                "second_best_topic": labels[second_idx],
                "second_best_score": f"{second_score:.6f}",
                "low_confidence_flag": "yes" if (best_score - second_score) < LOW_CONFIDENCE_MARGIN else "no",
                "classifier_backend": backend_name,
            }
        )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "conversation_id",
                "split",
                "train_index",
                "first_user_question",
                "predicted_topic",
                "similarity_score",
                "second_best_topic",
                "second_best_score",
                "low_confidence_flag",
                "classifier_backend",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Classifier backend: {backend_name}")
    print(f"Saved semantic topic results to {OUTPUT_PATH}")
    print("\nSemantic topic frequency table")
    print("=" * 70)
    print(f"{'Topic':45} Count  Percent")
    print("-" * 70)
    for label in labels:
        count = counts[label]
        print(f"{label:45} {count:5d}  {(count / SAMPLE_SIZE * 100):6.2f}%")
    print("-" * 70)
    print(f"{'TOTAL':45} {sum(counts.values()):5d}  {100.00:6.2f}%")
    low_confidence = sum(1 for row in rows if row["low_confidence_flag"] == "yes")
    print(f"\nLow-confidence assignments: {low_confidence}/{SAMPLE_SIZE} ({low_confidence / SAMPLE_SIZE * 100:.2f}%)")


if __name__ == "__main__":
    main()