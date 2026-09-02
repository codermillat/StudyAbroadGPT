#!/usr/bin/env python3
"""
generate_stratified.py
======================

Step 3 of the stratified causal test pre-registered at
``docs/analysis-plans/2026-09-02-stratified-causal-test.md``.

For each prompt in the stratified sample (output of
``stratify_prompts.py``), produces a base-model output and a LoRA-model
output using the v4 §3.5.1 generation settings exactly.

Output layout
-------------

    <output-dir>/
        base/
            <prompt_id>.txt            # the response text
            <prompt_id>.json           # generation metadata
        lora/
            <prompt_id>.txt
            <prompt_id>.json
        generation_summary.csv          # per-prompt timing and length summary

The JSON metadata captures: timestamp, peak VRAM (if a CUDA device is
available), input token count, output token count, truncation flag
(whether the response hit ``max_new_tokens``), and the exact chat template
used.

Usage
-----

    python3 generate_stratified.py \\
        --stratified-prompts data/v5-stratified-prompts.csv \\
        --strata C,W \\
        --output-dir data/v5-stratified-outputs/ \\
        --base-model unsloth/mistral-7b-instruct-v0.3-bnb-4bit \\
        --lora-adapter millat/StudyAbroadGPT-7B-LoRa-Kaggle \\
        --max-new-tokens 512

Hardware
--------

A single 16 GB GPU is sufficient. The script reports per-prompt peak VRAM
in the JSON metadata when a CUDA device is available; on CPU the field
is ``null``.

Pre-registration §5
-------------------

The generation settings here are the v4 §3.5.1 settings exactly. Any
deviation must be logged as an amendment in
``docs/analysis-plans/2026-09-02-stratified-causal-test.md``.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

logger = logging.getLogger("generate_stratified")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class GenConfig:
    """v4 §3.5.1 generation settings (frozen)."""

    do_sample: bool = False
    temperature: float = 0.0
    top_p: float = 1.0
    max_new_tokens: int = 512
    chat_template: str = (
        "<s>[INST] {prompt} [/INST]"
    )


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_stratified_prompts(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Stratified prompts CSV not found: {csv_path}")
    rows: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    logger.info("Loaded %d stratified prompts from %s", len(rows), csv_path)
    return rows


def filter_by_strata(rows: list[dict], allowed_strata: Iterable[str]) -> list[dict]:
    allowed = set(allowed_strata)
    filtered = [r for r in rows if r.get("stratum") in allowed]
    logger.info(
        "Filtered to %d prompts in strata %s (from %d total)",
        len(filtered), sorted(allowed), len(rows),
    )
    return filtered


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------


def _have_cuda() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except ImportError:
        return False


def _cuda_peak_mb() -> float | None:
    try:
        import torch
        if torch.cuda.is_available():
            return float(torch.cuda.max_memory_allocated() / 1024 / 1024)
    except Exception:
        return None
    return None


def _reset_cuda_peak() -> None:
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
    except Exception:
        pass


def load_base_model(model_id: str, dtype: str = "bfloat16"):
    """Load the base model in 4-bit NF4 (matches v4)."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as e:
        raise ImportError(
            "transformers is required. Install with: pip install transformers bitsandbytes accelerate"
        ) from e

    logger.info("Loading base model %s in 4-bit NF4 ...", model_id)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=dtype,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model.eval()
    return model, tokenizer


def load_lora_model(base_model, base_tokenizer, lora_adapter_id: str):
    """Attach the LoRA adapter on top of the already-loaded base model."""
    try:
        from peft import PeftModel
    except ImportError as e:
        raise ImportError("peft is required. Install with: pip install peft") from e

    logger.info("Attaching LoRA adapter %s ...", lora_adapter_id)
    model = PeftModel.from_pretrained(base_model, lora_adapter_id)
    model.eval()
    return model, base_tokenizer


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _build_chat_prompt(tokenizer, user_text: str, template: str) -> str:
    """Apply the v4 Mistral-Instruct chat template. The template uses
    ``{prompt}`` as a placeholder for the user text.
    """
    return template.format(prompt=user_text)


def generate_one(
    model,
    tokenizer,
    user_text: str,
    cfg: GenConfig,
) -> tuple[str, dict]:
    """Generate a single response; return (text, metadata)."""
    import torch

    prompt = _build_chat_prompt(tokenizer, user_text, cfg.chat_template)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_token_count = int(inputs["input_ids"].shape[1])

    _reset_cuda_peak()
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            **inputs,
            do_sample=cfg.do_sample,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            max_new_tokens=cfg.max_new_tokens,
            pad_token_id=tokenizer.pad_token_id,
        )
    elapsed = time.time() - t0
    peak_mb = _cuda_peak_mb()
    full_text = tokenizer.decode(out[0], skip_special_tokens=True)
    # Strip the prompt prefix to leave just the assistant response
    response_text = full_text[len(prompt):].strip() if full_text.startswith(prompt) else full_text
    output_token_count = int(out.shape[1]) - input_token_count
    truncated = output_token_count >= cfg.max_new_tokens

    meta = {
        "input_token_count": input_token_count,
        "output_token_count": output_token_count,
        "truncated": bool(truncated),
        "elapsed_seconds": round(elapsed, 3),
        "peak_vram_mb": peak_mb,
        "do_sample": cfg.do_sample,
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_new_tokens": cfg.max_new_tokens,
        "device": str(model.device),
    }
    return response_text, meta


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_outputs(
    output_dir: Path,
    prompt_id: str,
    base_text: str,
    base_meta: dict,
    lora_text: str,
    lora_meta: dict,
) -> None:
    base_dir = output_dir / "base"
    lora_dir = output_dir / "lora"
    base_dir.mkdir(parents=True, exist_ok=True)
    lora_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / f"{prompt_id}.txt").write_text(base_text, encoding="utf-8")
    (base_dir / f"{prompt_id}.json").write_text(json.dumps(base_meta, indent=2), encoding="utf-8")
    (lora_dir / f"{prompt_id}.txt").write_text(lora_text, encoding="utf-8")
    (lora_dir / f"{prompt_id}.json").write_text(json.dumps(lora_meta, indent=2), encoding="utf-8")


def write_summary_csv(output_dir: Path, rows: list[dict]) -> None:
    """Write a single per-prompt summary CSV across base and LoRA."""
    summary_path = output_dir / "generation_summary.csv"
    fieldnames = [
        "prompt_id", "stratum", "input_token_count",
        "base_output_token_count", "base_truncated", "base_elapsed_seconds",
        "lora_output_token_count", "lora_truncated", "lora_elapsed_seconds",
    ]
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    logger.info("Wrote generation summary to %s", summary_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate base and LoRA outputs on a stratified prompt set.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--stratified-prompts", type=Path, required=True, help="Output of stratify_prompts.py.")
    p.add_argument("--strata", type=str, default="C,W", help="Comma-separated list of strata to include (e.g. C,W).")
    p.add_argument("--output-dir", type=Path, required=True, help="Directory to write base/ and lora/ subdirs.")
    p.add_argument("--base-model", type=str, default="unsloth/mistral-7b-instruct-v0.3-bnb-4bit")
    p.add_argument("--lora-adapter", type=str, default="millat/StudyAbroadGPT-7B-LoRa-Kaggle")
    p.add_argument("--max-new-tokens", type=int, default=512, help="Match v4 §3.5.1 512-token re-run.")
    p.add_argument("--device", type=str, default="auto", help="auto, cuda, or cpu. Defaults to auto.")
    p.add_argument("--skip-lora", action="store_true", help="Skip LoRA generation (base only).")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not _have_cuda():
        logger.warning("No CUDA device detected. Generation will run on CPU and be very slow.")

    rows = load_stratified_prompts(args.stratified_prompts)
    allowed = [s.strip() for s in args.strata.split(",") if s.strip()]
    rows = filter_by_strata(rows, allowed)
    if not rows:
        print(f"No prompts in strata {allowed}; nothing to do.")
        return 0

    cfg = GenConfig(max_new_tokens=args.max_new_tokens)

    base_model, tokenizer = load_base_model(args.base_model)
    if not args.skip_lora:
        lora_model, _ = load_lora_model(base_model, tokenizer, args.lora_adapter)
    else:
        lora_model = None

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict] = []

    for i, row in enumerate(rows, start=1):
        prompt_id = row.get("prompt_id", f"prompt_{i}")
        user_text = row.get("prompt", "").strip()
        if not user_text:
            logger.warning("Skipping %s: empty prompt", prompt_id)
            continue

        logger.info("[%d/%d] %s  stratum=%s", i, len(rows), prompt_id, row.get("stratum"))
        base_text, base_meta = generate_one(base_model, tokenizer, user_text, cfg)
        if lora_model is not None:
            lora_text, lora_meta = generate_one(lora_model, tokenizer, user_text, cfg)
        else:
            lora_text, lora_meta = "", {"skipped": True}

        write_outputs(args.output_dir, prompt_id, base_text, base_meta, lora_text, lora_meta)
        summary_rows.append({
            "prompt_id": prompt_id,
            "stratum": row.get("stratum", ""),
            "input_token_count": base_meta.get("input_token_count"),
            "base_output_token_count": base_meta.get("output_token_count"),
            "base_truncated": base_meta.get("truncated"),
            "base_elapsed_seconds": base_meta.get("elapsed_seconds"),
            "lora_output_token_count": lora_meta.get("output_token_count"),
            "lora_truncated": lora_meta.get("truncated"),
            "lora_elapsed_seconds": lora_meta.get("elapsed_seconds"),
        })

    write_summary_csv(args.output_dir, summary_rows)
    print()
    print(f"Generated {len(summary_rows)} base+LoRA pairs in {args.output_dir}")
    print(f"Per-prompt summary: {args.output_dir / 'generation_summary.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
