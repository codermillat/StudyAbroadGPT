# LLM-as-Judge Evaluation Summary

**Methodology disclosure:** scores below are produced by an LLM judge (pointwise absolute scoring against the project rubric), NOT by human raters. The judge is a different model family from the Gemini generator used for the dataset and reference answers. This is an LLM-as-judge protocol; it complements, but does not replace, human or real-user evaluation, and must be named as such in the manuscript.

Samples: **50** | Scale: domain accuracy and helpfulness each **0-3** | Bootstrap: **1000 resamples, seed 42**

| Metric | Base (mean +/- SD) | LoRA (mean +/- SD) | Delta (LoRA - Base) | 95% CI on Delta |
|---|---:|---:|---:|---|
| Domain Accuracy (0-3) | 2.140 +/- 0.530 | 1.740 +/- 0.687 | -0.400 *(CI excludes 0)* | [-0.620, -0.180] |
| Helpfulness (0-3) | 2.140 +/- 0.490 | 1.820 +/- 0.590 | -0.320 *(CI excludes 0)* | [-0.520, -0.120] |

## Preference vote (de-blinded)

- LoRA preferred: **9/50** (18%)
- Base preferred: **23/50** (46%)
- Tie: **18/50** (36%)

## Reporting guidance

- Label explicitly as LLM-as-judge; report the CI with every delta.
- Only a delta whose 95% CI excludes 0 is a signal; others are 'no measurable difference'.
- Do NOT present this as the human evaluation Reviewer 2 requested; name it as a complementary automatic measure on synthetic-split prompts.
