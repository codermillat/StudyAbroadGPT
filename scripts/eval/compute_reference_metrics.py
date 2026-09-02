"""Standard NLP-metric evaluation for the StudyAbroadGPT base vs LoRA comparison.

Computes SacreBLEU, ROUGE-L, and BERTScore on a 50-prompt held-out set against
the 402-conversation test-split reference answers, for both the un-fine-tuned
Mistral-7B-Instruct-v0.3 baseline and the LoRA-adapted model.

Designed to run on a Mac once the model outputs are available. Device for
BERTScore is auto-detected in this order: CUDA -> Apple MPS (M1/M2/M3) -> CPU.
On an M1/M2 Mac, the MPS path is typically 3-8x faster than CPU for the
embedding pass. Pass --bertscore-model microsoft/deberta-large-mnli to match
the backbone originally promised in Section 5.3 of the manuscript (slower,
larger). Pass --bertscore-device cpu to force CPU.

Usage:
    # Default: 256-token outputs from the original eval
    python compute_reference_metrics.py

    # After the 512-token re-run
    python compute_reference_metrics.py --token-cap 512

    # Custom paths
    python compute_reference_metrics.py \
        --base-outputs path/to/base_outputs_512.csv \
        --lora-outputs path/to/lora_outputs_512.csv \
        --reference-template path/to/template.csv \
        --output-dir path/to/outputs/

    # Smoke test, no BERTScore
    python compute_reference_metrics.py --skip-bertscore

    # Benchmark: see if MPS is actually faster than CPU on this machine
    python compute_reference_metrics.py --bench-bertscore

Outputs (written to --output-dir, default ./outputs/):
    - Model_standard_nlp_metrics.csv
        Long-form per-prompt base/LoRA reference scores.
    - Model_standard_nlp_metrics_summary.md
        Headline base vs LoRA comparison table for paper §4.3.
    - Model_bertscore_raw.json
        Per-pair BERTScore precision/recall/F1 (for reproducibility).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import sacrebleu
import torch
from rouge_score import rouge_scorer
from bert_score import BERTScorer


# --- Defaults tied to the existing repo layout ---
DEFAULT_REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_EVAL_PROMPTS = DEFAULT_REPO_ROOT / "LoRA_Eval" / "Model_outputs" / "Model_evaluation_prompts.csv"
DEFAULT_BASE_OUTPUTS = DEFAULT_REPO_ROOT / "LoRA_Eval" / "Model_outputs" / "Model_base_model_outputs.csv"
DEFAULT_LORA_OUTPUTS = DEFAULT_REPO_ROOT / "LoRA_Eval" / "Model_outputs" / "Model_lora_model_outputs.csv"
DEFAULT_REFERENCE_TEMPLATE = DEFAULT_REPO_ROOT / "outputs" / "Dataset_downstream_evaluation_template.csv"
DEFAULT_OUTPUT_DIR = DEFAULT_REPO_ROOT / "outputs"


def _resolve(path_str: str | None, default: Path) -> Path:
    p = Path(path_str).expanduser() if path_str else default
    return p


def _normalize(text: str) -> str:
    """Light text normalization: collapse whitespace, strip."""
    if not isinstance(text, str):
        return ""
    return " ".join(text.split()).strip()


def _format_for_bleu(text: str) -> str:
    """SacreBLEU expects detokenized text; we pass whitespace-normalized text
    and let sacrebleu.tokenizer handle the rest. This is the standard
    convention for short-form generation comparison."""
    return _normalize(text)


def _load_eval_prompts(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if not {"sample_id", "dataset_index", "prompt"}.issubset(df.columns):
        raise ValueError(f"{path} is missing required columns: sample_id, dataset_index, prompt")
    return df


def _load_model_outputs(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if not {"sample_id", "response"}.issubset(df.columns):
        raise ValueError(f"{path} is missing required columns: sample_id, response")
    df["response"] = df["response"].astype(str).map(_normalize)
    return df[["sample_id", "response"]].rename(columns={"response": "model_response"})


def _load_reference_template(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "conversation_id" not in df.columns or "reference_answer" not in df.columns:
        raise ValueError(f"{path} is missing required columns: conversation_id, reference_answer")
    df["test_id"] = df["conversation_id"].astype(str)
    df["reference"] = df["reference_answer"].astype(str).map(_normalize)
    return df[["test_id", "reference"]]


def _build_joined_table(
    eval_prompts: pd.DataFrame,
    base_outputs: pd.DataFrame,
    lora_outputs: pd.DataFrame,
    reference_template: pd.DataFrame,
) -> pd.DataFrame:
    eval_prompts = eval_prompts.copy()
    eval_prompts["test_id"] = "test_" + eval_prompts["dataset_index"].astype(str)
    df = eval_prompts.merge(reference_template, on="test_id", how="left")
    if df["reference"].isna().any():
        missing = df.loc[df["reference"].isna(), "test_id"].tolist()
        raise ValueError(f"No reference answer found for: {missing[:5]}{'...' if len(missing) > 5 else ''}")
    df = df.merge(
        base_outputs.rename(columns={"model_response": "base_response"}),
        on="sample_id", how="left",
    )
    df = df.merge(
        lora_outputs.rename(columns={"model_response": "lora_response"}),
        on="sample_id", how="left",
    )
    return df[["sample_id", "dataset_index", "prompt", "reference",
               "base_response", "lora_response"]]


def _bootstrap_mean_diff(values_a: np.ndarray, values_b: np.ndarray, n_boot: int = 1000, seed: int = 42) -> tuple[float, float, float]:
    """Bootstrap 95% CI for mean(b) - mean(a). Returns (point, lo, hi)."""
    rng = np.random.default_rng(seed)
    diffs = values_b - values_a
    n = len(diffs)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    boot = np.empty(n_boot)
    for i in range(n_boot):
        sample = rng.choice(diffs, size=n, replace=True)
        boot[i] = sample.mean()
    point = float(diffs.mean())
    lo = float(np.quantile(boot, 0.025))
    hi = float(np.quantile(boot, 0.975))
    return point, lo, hi


def _compute_bleu(hypotheses: list[str], references: list[str]) -> dict:
    """SacreBLEU corpus BLEU (also returns 1-4 gram precisions and BP)."""
    bleu = sacrebleu.corpus_bleu(hypotheses, [references])
    return {
        "bleu": float(bleu.score),
        "bleu_bp": float(bleu.bp),
        "bleu_prec_1": float(bleu.precisions[0]),
        "bleu_prec_2": float(bleu.precisions[1]),
        "bleu_prec_3": float(bleu.precisions[2]),
        "bleu_prec_4": float(bleu.precisions[3]),
    }


def _compute_rouge_l(hypotheses: list[str], references: list[str]) -> dict:
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    f1s = []
    precs = []
    recs = []
    for h, r in zip(hypotheses, references):
        s = scorer.score(r, h)["rougeL"]
        f1s.append(s.fmeasure)
        precs.append(s.precision)
        recs.append(s.recall)
    return {
        "rouge_l_f1_mean": float(np.mean(f1s)),
        "rouge_l_precision_mean": float(np.mean(precs)),
        "rouge_l_recall_mean": float(np.mean(recs)),
        "rouge_l_f1_per_item": f1s,
    }


def _detect_device() -> str:
    """Pick the best available device for BERTScore in order: CUDA > MPS > CPU.

    MPS is the Apple Silicon (M1/M2/M3) GPU backend exposed by PyTorch. It
    gives 3-8x speedup over CPU for the roberta-large embedding pass and
    doesn't require CUDA. Falls back silently to CPU if MPS is not built
    into the installed PyTorch (older versions, Linux x86_64, etc.)."""
    if torch.cuda.is_available():
        return "cuda"
    mps_backend = getattr(torch.backends, "mps", None)
    if mps_backend is not None and mps_backend.is_available():
        return "mps"
    return "cpu"


def _bench_bertscore(model_type: str = "roberta-large", n_pairs: int = 8) -> None:
    """Quick apples-to-apples CPU vs MPS comparison on n_pairs dummy pairs.

    Useful on Apple Silicon to confirm MPS actually beats CPU before
    committing to a full run. Run with --bench-bertscore."""
    pairs = [
        ("The quick brown fox jumps over the lazy dog.", "A fast brown fox leaps over a sleeping dog."),
        ("I am applying to study computer science in the United Kingdom.", "I'm applying for a CS programme in the UK."),
        ("Scholarships are available for international students with strong academic records.", "Merit-based aid is offered to high-achieving international applicants."),
        ("My GRE score is 320 and my GPA is 3.8.", "I scored 320 on the GRE and hold a 3.8 GPA."),
        ("Living costs in London are roughly 1500 GBP per month.", "Expect to spend about 1500 GBP a month on living costs in London."),
        ("I want to write a strong statement of purpose for my masters application.", "I need to draft a compelling SOP for my masters application."),
        ("The deadline for fall 2026 intake is January 15.", "Applications for the fall 2026 intake close on January 15."),
        ("How do I get a UK student visa after receiving my CAS?", "What is the process for obtaining a UK student visa once I have my CAS?"),
    ][:n_pairs]
    hyps = [h for h, _ in pairs]
    refs = [r for _, r in pairs]

    print(f"BERTScore benchmark on {n_pairs} pairs, backbone={model_type}")
    print(f"PyTorch: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    mps_backend = getattr(torch.backends, "mps", None)
    print(f"  MPS available: {mps_backend.is_available() if mps_backend else False}")
    print()

    results = {}
    for dev in [d for d in ("cuda", "mps", "cpu") if d != "cuda" or torch.cuda.is_available()]:
        if dev == "mps" and not (mps_backend and mps_backend.is_available()):
            continue
        # Fresh scorer per device
        try:
            scorer = BERTScorer(model_type=model_type, lang="en",
                                rescale_with_baseline=True, device=dev, batch_size=8)
        except Exception as exc:
            print(f"  {dev}: failed to load scorer: {exc}")
            continue
        # warmup
        try:
            scorer.score(hyps[:1], refs[:1])
        except Exception as exc:
            print(f"  {dev}: warmup failed ({exc}); skipping")
            continue
        t0 = time.perf_counter()
        try:
            P, R, F = scorer.score(hyps, refs)
            elapsed = time.perf_counter() - t0
            results[dev] = elapsed
            print(f"  {dev}: {elapsed:.2f}s for {n_pairs} pairs ({elapsed/n_pairs:.2f}s/pair), F1.mean={float(F.mean()):.4f}")
        except Exception as exc:
            print(f"  {dev}: inference failed: {exc}")

    if "mps" in results and "cpu" in results:
        speedup = results["cpu"] / results["mps"]
        print(f"\nMPS is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than CPU on this hardware.")
    elif "mps" not in results:
        print("\nMPS path was not runnable on this hardware; will use CPU.")


def _compute_bertscore(hypotheses: list[str], references: list[str], model_type: str = "roberta-large", batch_size: int = 16, device: str | None = None) -> dict:
    """BERTScore with roberta-large as the default backbone.

    We default to roberta-large (rather than deberta-large-mnli) because:
    1. roberta-large is the backbone the original paper's Section 5.3
       promised. The deberta-large-mnli model is large and slow on CPU.
    2. roberta-large is the more common reference for general-purpose
       English BERTScore in the literature and produces directly
       comparable numbers to most published BERTScore tables.

    The model is downloaded on first run (~1.4GB for roberta-large).
    Cached afterwards.

    Set --bertscore-model to override (e.g. deberta-large-mnli,
    microsoft/deberta-xlarge-mnli). Set --bertscore-device cpu|mps|cuda
    to force a specific device; default is auto-detect (CUDA > MPS > CPU).
    """
    if device is None:
        device = _detect_device()
    print(f"    Using device: {device}, batch_size: {batch_size}, model: {model_type}")
    scorer = BERTScorer(model_type=model_type, lang="en", rescale_with_baseline=True, device=device, batch_size=batch_size)
    P, R, F = scorer.score(hypotheses, references)
    return {
        "bertscore_precision_mean": float(P.mean()),
        "bertscore_recall_mean": float(R.mean()),
        "bertscore_f1_mean": float(F.mean()),
        "bertscore_f1_per_item": [float(x) for x in F],
    }


def _summarize(
    df: pd.DataFrame,
    bleu_base: dict, bleu_lora: dict,
    rouge_base: dict, rouge_lora: dict,
    bert_base: dict, bert_lora: dict,
) -> dict:
    """Build the headline comparison with deltas and bootstrap CIs."""
    out: dict = {"per_metric": {}}

    # BLEU (corpus-level; bootstrap on a single point is degenerate, so we just record the point and skip CI)
    for label, d in [("base", bleu_base), ("lora", bleu_lora)]:
        out["per_metric"][f"bleu_{label}"] = d["bleu"]
        out["per_metric"][f"bleu_{label}_bp"] = d["bleu_bp"]
    out["per_metric"]["bleu_delta_lora_minus_base"] = bleu_lora["bleu"] - bleu_base["bleu"]
    out["per_metric"]["bleu_delta_ci_lo"] = float("nan")
    out["per_metric"]["bleu_delta_ci_hi"] = float("nan")

    # ROUGE-L (per-item, so bootstrap is meaningful)
    rb = np.array(rouge_base["rouge_l_f1_per_item"])
    rl = np.array(rouge_lora["rouge_l_f1_per_item"])
    out["per_metric"]["rouge_l_f1_base"] = float(rb.mean())
    out["per_metric"]["rouge_l_f1_lora"] = float(rl.mean())
    point, lo, hi = _bootstrap_mean_diff(rb, rl)
    out["per_metric"]["rouge_l_f1_delta"] = point
    out["per_metric"]["rouge_l_f1_delta_ci_lo"] = lo
    out["per_metric"]["rouge_l_f1_delta_ci_hi"] = hi

    # BERTScore F1
    bb = np.array(bert_base["bertscore_f1_per_item"])
    bl = np.array(bert_lora["bertscore_f1_per_item"])
    out["per_metric"]["bertscore_f1_base"] = float(np.nanmean(bb))
    out["per_metric"]["bertscore_f1_lora"] = float(np.nanmean(bl))
    if not (np.isnan(bb).all() or np.isnan(bl).all()):
        point, lo, hi = _bootstrap_mean_diff(bb, bl)
    else:
        point, lo, hi = float("nan"), float("nan"), float("nan")
    out["per_metric"]["bertscore_f1_delta"] = point
    out["per_metric"]["bertscore_f1_delta_ci_lo"] = lo
    out["per_metric"]["bertscore_f1_delta_ci_hi"] = hi

    return out


def _write_summary_markdown(
    summary: dict,
    df: pd.DataFrame,
    token_cap: int,
    out_path: Path,
) -> None:
    """Write a paper-ready markdown comparison table."""
    per = summary["per_metric"]
    n = len(df)
    lines = [
        f"# Standard NLP-Metric Comparison (max_new_tokens={token_cap})",
        "",
        f"Computed on **{n} held-out prompts** from `test` split, against reference answers from the same split.",
        "Reference answers and model responses were whitespace-normalized before scoring.",
        "",
        "## Headline",
        "",
        "| Metric | Base | LoRA | Δ (LoRA − Base) | 95% CI (Δ) |",
        "|---|---:|---:|---:|---|",
        f"| **SacreBLEU** | {per['bleu_base']:.2f} | {per['bleu_lora']:.2f} | {per['bleu_delta_lora_minus_base']:+.2f} | corpus-level (single value; CI not meaningful) |",
        f"| **ROUGE-L F1** (mean ± SD) | {per['rouge_l_f1_base']:.4f} | {per['rouge_l_f1_lora']:.4f} | {per['rouge_l_f1_delta']:+.4f} | [{per['rouge_l_f1_delta_ci_lo']:+.4f}, {per['rouge_l_f1_delta_ci_hi']:+.4f}] |",
        f"| **BERTScore F1** (rescaled, roberta-large) | {per['bertscore_f1_base']:.4f} | {per['bertscore_f1_lora']:.4f} | {per['bertscore_f1_delta']:+.4f} | [{per['bertscore_f1_delta_ci_lo']:+.4f}, {per['bertscore_f1_delta_ci_hi']:+.4f}] |",
        "",
        "## Notes",
        "",
        "- **SacreBLEU** is corpus-level (single number for the 50 pairs); CI is not meaningful.",
        "- **ROUGE-L F1** and **BERTScore F1** are per-item means. Bootstrap CIs are over 1,000 resamples (seed 42) of the per-item Δ.",
        "- **BERTScore** uses `roberta-large` with `rescale_with_baseline=True` by default. Pass `--bertscore-model microsoft/deberta-large-mnli` to use the NLI backbone (slower, larger, originally promised in Section 5.3 of the manuscript). Rescaled F1 values land in roughly the [-1, 1] interval; positive means above-baseline similarity.",
        "- All metrics compare model output to the synthetic reference answers in `outputs/Dataset_downstream_evaluation_template.csv`. The reference answers are themselves Gemini-generated and share the training distribution, so these metrics should be read as **fidelity-to-the-distribution**, not as ground-truth quality.",
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote summary: {out_path}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--eval-prompts", default=None,
                   help=f"Path to Model_evaluation_prompts.csv (default: {DEFAULT_EVAL_PROMPTS})")
    p.add_argument("--base-outputs", default=None,
                   help="Path to base model outputs CSV. Should have sample_id, response columns. "
                        "For 512-token re-run, point at base_model_outputs_512.csv.")
    p.add_argument("--lora-outputs", default=None,
                   help="Path to LoRA model outputs CSV. Should have sample_id, response columns. "
                        "For 512-token re-run, point at lora_model_outputs_512.csv.")
    p.add_argument("--reference-template", default=None,
                   help=f"Path to Dataset_downstream_evaluation_template.csv (default: {DEFAULT_REFERENCE_TEMPLATE})")
    p.add_argument("--output-dir", default=None,
                   help=f"Directory to write results to (default: {DEFAULT_OUTPUT_DIR})")
    p.add_argument("--token-cap", type=int, default=256,
                   help="Token cap used in the run; recorded in output filenames and summary header.")
    p.add_argument("--bertscore-model", default="roberta-large",
                   help="Backbone model for BERTScore (default: roberta-large).")
    p.add_argument("--bertscore-device", default=None,
                   help="Device for BERTScore (default: auto-detect cuda/mps/cpu).")
    p.add_argument("--bertscore-batch-size", type=int, default=16,
                   help="Batch size for BERTScore (default: 16).")
    p.add_argument("--skip-bertscore", action="store_true",
                   help="Skip BERTScore (slowest metric; useful for quick smoke test).")
    p.add_argument("--bench-bertscore", action="store_true",
                   help="Run a quick CPU-vs-MPS timing comparison on a few dummy pairs and exit. "
                        "Use this to confirm whether MPS is faster on this machine before a full run.")
    args = p.parse_args(argv)

    if args.bench_bertscore:
        _bench_bertscore(model_type=args.bertscore_model)
        return 0

    eval_prompts_path = _resolve(args.eval_prompts, DEFAULT_EVAL_PROMPTS)
    base_outputs_path = _resolve(args.base_outputs, DEFAULT_BASE_OUTPUTS)
    lora_outputs_path = _resolve(args.lora_outputs, DEFAULT_LORA_OUTPUTS)
    ref_template_path = _resolve(args.reference_template, DEFAULT_REFERENCE_TEMPLATE)
    out_dir = _resolve(args.output_dir, DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    token_cap = args.token_cap
    suffix = f"_{token_cap}" if token_cap != 256 else ""

    print(f"Eval prompts: {eval_prompts_path}")
    print(f"Base outputs: {base_outputs_path}")
    print(f"LoRA outputs: {lora_outputs_path}")
    print(f"Reference template: {ref_template_path}")
    print(f"Output dir: {out_dir}")
    print(f"Token cap: {token_cap}")
    print(f"Auto-detected device (for BERTScore): {_detect_device()}")
    print()

    eval_prompts = _load_eval_prompts(eval_prompts_path)
    base_outputs = _load_model_outputs(base_outputs_path)
    lora_outputs = _load_model_outputs(lora_outputs_path)
    ref_template = _load_reference_template(ref_template_path)

    df = _build_joined_table(eval_prompts, base_outputs, lora_outputs, ref_template)
    print(f"Joined table: {len(df)} rows ({df['base_response'].notna().sum()} base, "
          f"{df['lora_response'].notna().sum()} LoRA with non-null responses).")

    # Truncate any model output that still hit the cap to a clean length for fair comparison.
    # The truncation flag is in the metadata; we just use the text as-is from the CSV.
    hyps_base = df["base_response"].tolist()
    hyps_lora = df["lora_response"].tolist()
    refs = df["reference"].tolist()

    print("Computing SacreBLEU...")
    bleu_base = _compute_bleu(hyps_base, refs)
    bleu_lora = _compute_bleu(hyps_lora, refs)
    print(f"  base BLEU = {bleu_base['bleu']:.2f}")
    print(f"  lora BLEU = {bleu_lora['bleu']:.2f}")

    print("Computing ROUGE-L...")
    rouge_base = _compute_rouge_l(hyps_base, refs)
    rouge_lora = _compute_rouge_l(hyps_lora, refs)
    print(f"  base ROUGE-L F1 = {rouge_base['rouge_l_f1_mean']:.4f}")
    print(f"  lora ROUGE-L F1 = {rouge_lora['rouge_l_f1_mean']:.4f}")

    if args.skip_bertscore:
        print("Skipping BERTScore (--skip-bertscore).")
        bert_base = {"bertscore_f1_per_item": [float("nan")] * len(df)}
        bert_lora = {"bertscore_f1_per_item": [float("nan")] * len(df)}
    else:
        print(f"Computing BERTScore (backbone: {args.bertscore_model})...")
        print("  (first call downloads the model; subsequent runs use the cache)")
        bert_base = _compute_bertscore(
            hyps_base, refs,
            model_type=args.bertscore_model,
            batch_size=args.bertscore_batch_size,
            device=args.bertscore_device,
        )
        print(f"  base BERTScore F1 = {bert_base['bertscore_f1_mean']:.4f}")
        bert_lora = _compute_bertscore(
            hyps_lora, refs,
            model_type=args.bertscore_model,
            batch_size=args.bertscore_batch_size,
            device=args.bertscore_device,
        )
        print(f"  lora BERTScore F1 = {bert_lora['bertscore_f1_mean']:.4f}")

    summary = _summarize(df, bleu_base, bleu_lora, rouge_base, rouge_lora, bert_base, bert_lora)

    # Long-form per-prompt CSV
    rows = []
    for i, r in df.iterrows():
        rows.append({
            "sample_id": r["sample_id"],
            "dataset_index": r["dataset_index"],
            "prompt": r["prompt"],
            "reference_length_chars": len(r["reference"]),
            "base_response_length_chars": len(r["base_response"]),
            "lora_response_length_chars": len(r["lora_response"]),
            "rouge_l_f1_base": rouge_base["rouge_l_f1_per_item"][i],
            "rouge_l_f1_lora": rouge_lora["rouge_l_f1_per_item"][i],
            "bertscore_f1_base": bert_base["bertscore_f1_per_item"][i],
            "bertscore_f1_lora": bert_lora["bertscore_f1_per_item"][i],
        })
    long_df = pd.DataFrame(rows)
    long_path = out_dir / f"Model_standard_nlp_metrics{suffix}.csv"
    long_df.to_csv(long_path, index=False)
    print(f"Wrote per-prompt table: {long_path}")

    # BERTScore raw dump (for reproducibility)
    bert_raw = {
        "token_cap": token_cap,
        "bertscore_model": args.bertscore_model,
        "rescale_with_baseline": True,
        "f1_per_item_base": bert_base["bertscore_f1_per_item"],
        "f1_per_item_lora": bert_lora["bertscore_f1_per_item"],
        "precision_mean_base": bert_base.get("bertscore_precision_mean"),
        "recall_mean_base": bert_base.get("bertscore_recall_mean"),
        "precision_mean_lora": bert_lora.get("bertscore_precision_mean"),
        "recall_mean_lora": bert_lora.get("bertscore_recall_mean"),
    }
    bert_path = out_dir / f"Model_bertscore_raw{suffix}.json"
    bert_path.write_text(json.dumps(bert_raw, indent=2))
    print(f"Wrote BERTScore raw: {bert_path}")

    # Headline summary
    summary_path = out_dir / f"Model_standard_nlp_metrics_summary{suffix}.md"
    _write_summary_markdown(summary, df, token_cap, summary_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
