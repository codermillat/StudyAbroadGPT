#!/usr/bin/env python3
"""LLM-as-judge evaluation of blinded base-vs-LoRA responses.

This is an *LLM-as-judge* protocol, NOT human evaluation. It must be disclosed
as such in any manuscript: an LLM scores each response against the project's
downstream rubric (domain accuracy 0-3, helpfulness 0-3). It complements, and
does not replace, human evaluation or a real-user study.

Design choices that make it defensible:
  * Pointwise absolute scoring. Each response is scored on its own merits
    against the fixed rubric anchors -- exactly how a human fills the rubric --
    rather than "which of the two is better". Pointwise scoring is naturally
    free of position bias on the scores themselves.
  * Different model family from the data generator. The dataset and reference
    answers are Gemini-generated; a Gemini judge would reward fidelity to its
    own distribution (self-preference bias). Use a non-Gemini judge.
  * The judge never sees which response is base vs LoRA.

Reproducibility note: the run reported in the manuscript was produced with the
Claude Code agent acting as judge (same Sonnet family). A third party can
reproduce with their own Anthropic console key:

    export JUDGE_API_KEY=sk-ant-...
    python llm_judge_eval.py \
        --input  LoRA_Output/outputs/Model_downstream_blinded_evaluation.csv \
        --output outputs/Model_llm_judge_scores.csv \
        --model  claude-sonnet-4-6

Output schema (one row per pair):
    sample_id, domain_a, help_a, domain_b, help_b, preferred_slot, note_a, note_b
preferred_slot is "a" / "b" / "tie" over the blinded slots (no model identity).
Run analyze_judge_scores.py to rejoin the source mapping and compare base vs LoRA.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional

# Rubric anchors verbatim from outputs/Dataset_manual_scoring_rubric.md, section 3.
RUBRIC = """You are scoring responses from a study-abroad advising assistant.
Judge domain usefulness, correctness, and safety -- NOT fluency or pleasant
wording. A longer or more confident answer is NOT automatically better; an
answer that is confidently wrong, or that omits caveats on policy-sensitive
topics (visa, immigration, deadlines, healthcare), must score LOW.

DOMAIN ACCURACY (0-3):
  0 = Incorrect, misleading, hallucinated, or unsafe.
  1 = Partially correct but incomplete or weakly domain-specific.
  2 = Mostly correct with minor omissions or caveating issues.
  3 = Correct, domain-specific, actionable, and appropriately caveated.

HELPFULNESS (0-3):
  0 = Not useful or likely to confuse the student.
  1 = Some useful information but vague or incomplete.
  2 = Useful and mostly actionable, with minor gaps.
  3 = Highly useful, clear, actionable, and tailored to the question."""

JUDGE_INSTRUCTION = """Below is a student question and TWO candidate responses,
RESPONSE_A and RESPONSE_B. Score EACH response independently on the two 0-3
scales above (absolute scoring -- do not grade on a curve). Then say which you
prefer overall as advising ("a", "b", or "tie"). Score blind; do not assume
either response is from a better or fine-tuned model.

Return ONLY this JSON, no prose:
{
  "response_a": {"domain_accuracy": <0-3>, "helpfulness": <0-3>, "note": "<=15 words"},
  "response_b": {"domain_accuracy": <0-3>, "helpfulness": <0-3>, "note": "<=15 words"},
  "preferred": "a" | "b" | "tie"
}"""

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 4
RETRY_BACKOFF_SEC = 3.0
SCORE_MIN, SCORE_MAX = 0, 3


@dataclass(frozen=True)
class PairScore:
    sample_id: str
    domain_a: int
    help_a: int
    domain_b: int
    help_b: int
    preferred_slot: str  # "a" / "b" / "tie"
    note_a: str
    note_b: str


def build_prompt(question: str, resp_a: str, resp_b: str) -> str:
    return (
        f"{RUBRIC}\n\n{JUDGE_INSTRUCTION}\n\n"
        f"STUDENT QUESTION:\n{question}\n\n"
        f"RESPONSE_A:\n{resp_a}\n\n"
        f"RESPONSE_B:\n{resp_b}\n"
    )


def parse_judge_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"No JSON object in judge reply: {text[:200]!r}")
    obj = json.loads(text[start : end + 1])
    for key in ("response_a", "response_b", "preferred"):
        if key not in obj:
            raise ValueError(f"Judge JSON missing key {key!r}")
    return obj


def call_judge(client, model: str, prompt: str) -> dict:
    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=512,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in msg.content if b.type == "text").strip()
            return parse_judge_json(text)
        except Exception as exc:  # noqa: BLE001 - surfaced after retries
            last_err = exc
            time.sleep(RETRY_BACKOFF_SEC * (attempt + 1))
    raise RuntimeError(f"Judge call failed after {MAX_RETRIES} retries: {last_err}")


def coerce_score(value: object) -> int:
    score = int(value)
    if not SCORE_MIN <= score <= SCORE_MAX:
        raise ValueError(f"Score out of range {SCORE_MIN}-{SCORE_MAX}: {value}")
    return score


def score_pair(client, model: str, row: dict) -> PairScore:
    prompt = build_prompt(row["prompt"], row["response_a"], row["response_b"])
    result = call_judge(client, model, prompt)
    pref = str(result["preferred"]).strip().lower()
    if pref not in ("a", "b", "tie"):
        pref = "tie"
    return PairScore(
        sample_id=row["sample_id"],
        domain_a=coerce_score(result["response_a"]["domain_accuracy"]),
        help_a=coerce_score(result["response_a"]["helpfulness"]),
        domain_b=coerce_score(result["response_b"]["domain_accuracy"]),
        help_b=coerce_score(result["response_b"]["helpfulness"]),
        preferred_slot=pref,
        note_a=str(result["response_a"].get("note", ""))[:120],
        note_b=str(result["response_b"].get("note", ""))[:120],
    )


def load_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    required = {"sample_id", "prompt", "response_a", "response_b"}
    missing = (required - set(rows[0].keys())) if rows else required
    if missing:
        sys.exit(f"ERROR: input CSV missing columns: {sorted(missing)}")
    return rows


def make_client():
    api_key = os.environ.get("JUDGE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: set JUDGE_API_KEY (or ANTHROPIC_API_KEY).")
    try:
        import anthropic  # noqa: PLC0415 - optional dependency
    except ImportError:
        sys.exit("ERROR: pip install anthropic")
    base_url = os.environ.get("JUDGE_BASE_URL") or os.environ.get("ANTHROPIC_BASE_URL")
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return anthropic.Anthropic(**kwargs)


def write_scores(path: str, scores: list[PairScore]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(asdict(scores[0]).keys()))
        writer.writeheader()
        for score in scores:
            writer.writerow(asdict(score))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    rows = load_rows(args.input)
    client = make_client()
    scores = []
    for idx, row in enumerate(rows, 1):
        scores.append(score_pair(client, args.model, row))
        print(f"  scored {idx}/{len(rows)} (sample_id={row['sample_id']})", file=sys.stderr)

    write_scores(args.output, scores)
    print(f"Wrote {len(scores)} judge rows -> {args.output}")


if __name__ == "__main__":
    main()
