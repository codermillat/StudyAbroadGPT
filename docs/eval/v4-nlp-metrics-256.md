# Standard NLP-Metric Comparison (max_new_tokens=256)

Computed on **50 held-out prompts** from `test` split, against reference answers from the same split.
Reference answers and model responses were whitespace-normalized before scoring.

## Headline

| Metric | Base | LoRA | Δ (LoRA − Base) | 95% CI (Δ) |
|---|---:|---:|---:|---|
| **SacreBLEU** | 2.60 | 4.09 | +1.49 | corpus-level (single value; CI not meaningful) |
| **ROUGE-L F1** (mean ± SD) | 0.1774 | 0.1970 | +0.0196 | [+0.0112, +0.0282] |
| **BERTScore F1** (rescaled, roberta-large) | 0.0948 | 0.1581 | +0.0634 | [+0.0477, +0.0774] |

## Notes

- **SacreBLEU** is corpus-level (single number for the 50 pairs); CI is not meaningful.
- **ROUGE-L F1** and **BERTScore F1** are per-item means. Bootstrap CIs are over 1,000 resamples (seed 42) of the per-item Δ.
- **BERTScore** uses `roberta-large` with `rescale_with_baseline=True` by default. Pass `--bertscore-model microsoft/deberta-large-mnli` to use the NLI backbone (slower, larger, originally promised in Section 5.3 of the manuscript). Rescaled F1 values land in roughly the [-1, 1] interval; positive means above-baseline similarity.
- All metrics compare model output to the synthetic reference answers in `outputs/Dataset_downstream_evaluation_template.csv`. The reference answers are themselves Gemini-generated and share the training distribution, so these metrics should be read as **fidelity-to-the-distribution**, not as ground-truth quality.
