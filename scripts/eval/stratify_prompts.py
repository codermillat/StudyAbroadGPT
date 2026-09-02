#!/usr/bin/env python3
"""
stratify_prompts.py
===================

Step 1 of the stratified causal test pre-registered at
``docs/analysis-plans/2026-09-02-stratified-causal-test.md``.

For each held-out prompt, this script:

1. Embeds the first user turn with ``sentence-transformers/all-MiniLM-L6-v2``
   (the same model v4 §3.1.1 uses for topic classification).
2. Retrieves the top-k=5 nearest training-set neighbors by cosine similarity.
3. Looks up each neighbor's source-verified label (if any) from the audit
   catalog.
4. Assigns the prompt to one of three strata (C, W, M, or ``excluded``)
   using the rule in §3.3 of the pre-registration.

The output is a CSV that downstream steps (generation, audit, McNemar's
analysis) consume directly.

Usage
-----

    python stratify_prompts.py \\
        --held-out data/v4-50-prompt-eval/evaluation_prompts.csv \\
        --training-data "LoRA Paper/linked_repos/study-abroad-dataset/dataset/study_abroad_dataset.jsonl" \\
        --audit-catalog data/v5-audit-catalog.csv \\
        --output data/v5-stratified-prompts.csv

Input schemas
-------------

Held-out CSV (at minimum):
    prompt_id, prompt

Training JSONL: one JSON object per line with the schema
    {"conversations": [{"from": "human", "value": "..."}, ...]}

Audit catalog CSV (at minimum):
    training_id, label
where label is one of {verified_correct, verified_wrong}.
The ``training_id`` is the SHA1 hash of the first user turn of the
training conversation (computed by this script; see ``_first_user_turn``).

The script prints a stratum summary at the end. Stratum counts feed
directly into the pre-registered sample-size decision rule (§4.2 of the
pre-registration).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

logger = logging.getLogger("stratify_prompts")


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class TrainingExample:
    """One training conversation, plus the embedding we computed for it."""

    training_id: str
    first_user_turn: str
    label: str | None = None  # populated from the audit catalog
    embedding: list[float] = field(default_factory=list)


@dataclass
class HeldOutPrompt:
    """One held-out prompt with its stratum assignment."""

    prompt_id: str
    prompt: str
    neighbor_ids: list[str] = field(default_factory=list)
    neighbor_similarities: list[float] = field(default_factory=list)
    neighbor_labels: list[str] = field(default_factory=list)
    verified_correct_count: int = 0
    verified_wrong_count: int = 0
    unaudited_count: int = 0
    stratum: str = "excluded"  # C, W, M, or excluded


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _first_user_turn(conversation: dict) -> str:
    """Return the first user turn of a ShareGPT-style conversation."""
    for turn in conversation.get("conversations", []):
        if turn.get("from") in ("human", "user"):
            return (turn.get("value") or "").strip()
    return ""


def _training_id_from_text(text: str) -> str:
    """Stable id for a training example: SHA1 of the first user turn."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def load_held_out(csv_path: Path) -> list[HeldOutPrompt]:
    """Load held-out prompts from a CSV. Required: prompt_id, prompt."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Held-out CSV not found: {csv_path}")

    prompts: list[HeldOutPrompt] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "prompt_id" not in reader.fieldnames or "prompt" not in reader.fieldnames:
            raise ValueError(
                f"Held-out CSV must have 'prompt_id' and 'prompt' columns. "
                f"Found: {reader.fieldnames}"
            )
        for row in reader:
            prompts.append(
                HeldOutPrompt(
                    prompt_id=str(row["prompt_id"]).strip(),
                    prompt=str(row["prompt"]).strip(),
                )
            )
    logger.info("Loaded %d held-out prompts from %s", len(prompts), csv_path)
    return prompts


def load_training_data(jsonl_path: Path) -> list[TrainingExample]:
    """Load training examples from a JSONL of ShareGPT-style conversations."""
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Training JSONL not found: {jsonl_path}")

    examples: list[TrainingExample] = []
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
            text = _first_user_turn(obj)
            if not text:
                logger.warning("Skipping line %d: no first user turn", line_no)
                continue
            examples.append(
                TrainingExample(
                    training_id=_training_id_from_text(text),
                    first_user_turn=text,
                )
            )
    logger.info("Loaded %d training examples from %s", len(examples), jsonl_path)
    return examples


def load_audit_catalog(csv_path: Path | None) -> dict[str, str]:
    """Load the audit labels keyed by training_id. Returns {} if path is None."""
    if csv_path is None:
        logger.info("No audit catalog provided; all training labels are 'unaudited'.")
        return {}
    if not csv_path.exists():
        raise FileNotFoundError(f"Audit catalog not found: {csv_path}")

    valid_labels = {"verified_correct", "verified_wrong"}
    labels: dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "training_id" not in reader.fieldnames or "label" not in reader.fieldnames:
            raise ValueError(
                f"Audit catalog must have 'training_id' and 'label' columns. "
                f"Found: {reader.fieldnames}"
            )
        for row in reader:
            tid = str(row["training_id"]).strip()
            label = str(row["label"]).strip()
            if label not in valid_labels:
                logger.warning("Skipping %s: unknown label %r", tid, label)
                continue
            if tid in labels:
                logger.warning("Duplicate training_id %s; keeping first label %r", tid, labels[tid])
                continue
            labels[tid] = label
    logger.info(
        "Loaded %d audit labels (%d verified_correct, %d verified_wrong) from %s",
        len(labels),
        sum(1 for v in labels.values() if v == "verified_correct"),
        sum(1 for v in labels.values() if v == "verified_wrong"),
        csv_path,
    )
    return labels


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


def embed_texts(texts: list[str], model_name: str, cache_path: Path | None) -> list[list[float]]:
    """Embed a list of texts. Uses sentence-transformers. Caches to .npy if cache_path given."""
    if cache_path is not None and cache_path.exists():
        try:
            import numpy as np
            arr = np.load(cache_path)
            if arr.shape[0] == len(texts):
                logger.info("Loaded %d cached embeddings from %s", len(texts), cache_path)
                return arr.tolist()
            logger.info("Cache size mismatch (have %d, need %d); recomputing", arr.shape[0], len(texts))
        except Exception as e:
            logger.warning("Failed to load cache %s: %s; recomputing", cache_path, e)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "sentence-transformers is required. Install with: pip install sentence-transformers"
        ) from e

    logger.info("Loading embedding model %s ...", model_name)
    model = SentenceTransformer(model_name)
    logger.info("Encoding %d texts ...", len(texts))
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=64)
    embeddings_list = embeddings.tolist()

    if cache_path is not None:
        try:
            import numpy as np
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(cache_path, embeddings)
            logger.info("Cached %d embeddings to %s", len(texts), cache_path)
        except Exception as e:
            logger.warning("Failed to write cache %s: %s", cache_path, e)

    return embeddings_list


# ---------------------------------------------------------------------------
# Stratification
# ---------------------------------------------------------------------------


def _cosine_similarity_matrix(query: list[float], corpus: list[list[float]]) -> list[float]:
    """Cosine similarity of one query vector against a corpus of vectors."""
    import numpy as np
    q = np.asarray(query, dtype=np.float32)
    c = np.asarray(corpus, dtype=np.float32)
    q_norm = q / (np.linalg.norm(q) + 1e-12)
    c_norm = c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-12)
    return (c_norm @ q_norm).tolist()


def assign_stratum(
    prompt: HeldOutPrompt,
    neighbors: list[TrainingExample],
    similarities: list[float],
    min_audited: int = 3,
) -> None:
    """Populate the neighbor lists and stratum on the HeldOutPrompt in place.

    The rule is exactly §3.3 of the pre-registration:
        C: >= min_audited verified_correct, 0 verified_wrong
        W: >= min_audited verified_wrong,   0 verified_correct
        M: anything else (including mixed, or fewer than min_audited audited)
    """
    prompt.neighbor_ids = [n.training_id for n in neighbors]
    prompt.neighbor_similarities = [float(s) for s in similarities]
    prompt.neighbor_labels = [n.label or "unaudited" for n in neighbors]
    prompt.verified_correct_count = sum(1 for l in prompt.neighbor_labels if l == "verified_correct")
    prompt.verified_wrong_count = sum(1 for l in prompt.neighbor_labels if l == "verified_wrong")
    prompt.unaudited_count = sum(1 for l in prompt.neighbor_labels if l == "unaudited")

    audited = prompt.verified_correct_count + prompt.verified_wrong_count
    if audited < min_audited:
        prompt.stratum = "excluded"
    elif prompt.verified_correct_count >= min_audited and prompt.verified_wrong_count == 0:
        prompt.stratum = "C"
    elif prompt.verified_wrong_count >= min_audited and prompt.verified_correct_count == 0:
        prompt.stratum = "W"
    else:
        prompt.stratum = "M"


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_output(prompts: list[HeldOutPrompt], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "prompt_id", "prompt", "stratum",
        "verified_correct_count", "verified_wrong_count", "unaudited_count",
    ]
    for k in range(1, 6):
        fieldnames += [f"top_{k}_id", f"top_{k}_label", f"top_{k}_sim"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in prompts:
            row = {
                "prompt_id": p.prompt_id,
                "prompt": p.prompt,
                "stratum": p.stratum,
                "verified_correct_count": p.verified_correct_count,
                "verified_wrong_count": p.verified_wrong_count,
                "unaudited_count": p.unaudited_count,
            }
            for k in range(5):
                idx = k
                row[f"top_{k+1}_id"] = p.neighbor_ids[idx] if idx < len(p.neighbor_ids) else ""
                row[f"top_{k+1}_label"] = p.neighbor_labels[idx] if idx < len(p.neighbor_labels) else ""
                row[f"top_{k+1}_sim"] = f"{p.neighbor_similarities[idx]:.4f}" if idx < len(p.neighbor_similarities) else ""
            writer.writerow(row)
    logger.info("Wrote %d rows to %s", len(prompts), output_path)


def print_summary(prompts: list[HeldOutPrompt]) -> None:
    counts: dict[str, int] = {"C": 0, "W": 0, "M": 0, "excluded": 0}
    audited_neighbors: dict[str, int] = {"verified_correct": 0, "verified_wrong": 0, "unaudited": 0}
    for p in prompts:
        counts[p.stratum] = counts.get(p.stratum, 0) + 1
        for l in p.neighbor_labels:
            audited_neighbors[l] = audited_neighbors.get(l, 0) + 1

    print()
    print("=" * 64)
    print("STRATIFICATION SUMMARY")
    print("=" * 64)
    print(f"Total held-out prompts:        {len(prompts)}")
    print(f"  Stratum C (clean neighbors): {counts.get('C', 0)}")
    print(f"  Stratum W (wrong neighbors): {counts.get('W', 0)}")
    print(f"  Stratum M (mixed):            {counts.get('M', 0)}")
    print(f"  Excluded (insufficient audit):{counts.get('excluded', 0)}")
    print()
    print("Neighbor label totals (across all top-5 retrievals):")
    print(f"  verified_correct: {audited_neighbors.get('verified_correct', 0)}")
    print(f"  verified_wrong:   {audited_neighbors.get('verified_wrong', 0)}")
    print(f"  unaudited:        {audited_neighbors.get('unaudited', 0)}")
    print()
    # Pre-registration §4.2 decision rule
    n_c = counts.get("C", 0)
    n_w = counts.get("W", 0)
    if n_c >= 60 and n_w >= 60:
        verdict = "ADEQUATELY POWERED (>=60 per stratum, ~80% power to detect 25pp delta)"
    elif n_c >= 30 and n_w >= 30:
        verdict = "INDICATIVE (>=30 per stratum, ~50% power to detect 25pp delta)"
    elif n_c >= 15 and n_w >= 15:
        verdict = "UNDER-POWERED and EXPLORATORY (15-30 per stratum)"
    else:
        verdict = "INSUFFICIENT (<15 per stratum). Run the audit extension to grow the labeled set."
    print(f"Power verdict (§4.2 of the pre-registration): {verdict}")
    print("=" * 64)


# ---------------------------------------------------------------------------
# Sanity / test mode
# ---------------------------------------------------------------------------


def run_sanity_test(embedding_model: str) -> int:
    """Smoke test: build a tiny synthetic held-out + training set and run end-to-end."""
    import numpy as np

    print("Running sanity test ...")
    train = [
        TrainingExample(training_id="t1", first_user_turn="how to apply for UK student visa"),
        TrainingExample(training_id="t2", first_user_turn="scholarships for international students in USA"),
        TrainingExample(training_id="t3", first_user_turn="cost of living in Toronto for students"),
    ]
    held_out = [
        HeldOutPrompt(prompt_id="h1", prompt="UK student visa requirements"),
        HeldOutPrompt(prompt_id="h2", prompt="Tuition fees in the United States"),
    ]
    # Embed only the first user turn of each (matches the pre-registration)
    train_texts = [t.first_user_turn for t in train]
    held_texts = [h.prompt for h in held_out]
    train_emb = embed_texts(train_texts, embedding_model, cache_path=None)
    held_emb = embed_texts(held_texts, embedding_model, cache_path=None)
    # Fake an audit catalog: t1 correct, t2 wrong, t3 unaudited
    audit = {"t1": "verified_correct", "t2": "verified_wrong"}
    for t, lbl in zip(train, [audit.get(t.training_id, "unaudited") for t in train]):
        t.label = lbl
    for h, q in zip(held_out, held_emb):
        sims = _cosine_similarity_matrix(q, train_emb)
        order = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:5]
        neighbors = [train[i] for i in order]
        sim_values = [sims[i] for i in order]
        assign_stratum(h, neighbors, sim_values, min_audited=1)
        print(f"  h={h.prompt_id}  stratum={h.stratum}  neighbors={[n.training_id for n in neighbors]}  labels={h.neighbor_labels}")
    print("Sanity test OK.")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stratify held-out prompts by training-neighbor audit labels.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--held-out", type=Path, required=False, help="Held-out prompts CSV.")
    p.add_argument("--training-data", type=Path, required=False, help="Training JSONL.")
    p.add_argument("--audit-catalog", type=Path, default=None, help="Audit labels CSV (optional).")
    p.add_argument("--output", type=Path, required=False, help="Output stratified CSV.")
    p.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Sentence-transformer model to use.",
    )
    p.add_argument("--top-k", type=int, default=5, help="Number of nearest neighbors.")
    p.add_argument(
        "--min-audited",
        type=int,
        default=3,
        help="Min audited neighbors required for stratum C or W (§3.3 of the pre-registration).",
    )
    p.add_argument("--embedding-cache", type=Path, default=None, help="Path to .npy cache for training embeddings.")
    p.add_argument("--sanity-test", action="store_true", help="Run a 30-second smoke test and exit.")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.sanity_test:
        return run_sanity_test(args.embedding_model)

    if not args.held_out or not args.training_data or not args.output:
        print("Error: --held-out, --training-data, and --output are required (or pass --sanity-test).", file=sys.stderr)
        return 2

    held_out = load_held_out(args.held_out)
    training = load_training_data(args.training_data)
    audit_labels = load_audit_catalog(args.audit_catalog)

    # Attach audit labels to training examples
    for t in training:
        t.label = audit_labels.get(t.training_id)

    # Embed training (cached) and held-out
    cache = args.embedding_cache
    train_texts = [t.first_user_turn for t in training]
    train_emb = embed_texts(train_texts, args.embedding_model, cache)
    for t, e in zip(training, train_emb):
        t.embedding = e

    held_texts = [h.prompt for h in held_out]
    held_emb = embed_texts(held_texts, args.embedding_model, cache_path=None)

    # For each held-out prompt, retrieve top-k and assign stratum
    train_emb_matrix = [t.embedding for t in training]
    for h, q in zip(held_out, held_emb):
        sims = _cosine_similarity_matrix(q, train_emb_matrix)
        order = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[: args.top_k]
        neighbors = [training[i] for i in order]
        sim_values = [sims[i] for i in order]
        assign_stratum(h, neighbors, sim_values, min_audited=args.min_audited)

    write_output(held_out, args.output)
    print_summary(held_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
