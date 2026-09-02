# StudyAbroadGPT — Reproduction Bundle for arXiv:2504.15610

This repository contains the v4 audit, evaluation, and v5 submission assets for
**"Fine-Tuning a 7B Advisor on Free-Tier GPUs: An Adapter-Handoff Recipe and a
Synthetic-Data Reliability Caution"** ([arXiv:2504.15610v4](https://arxiv.org/abs/2504.15610)).
The v4 paper retracts two earlier-version claims and reframes the contribution
around (a) a free-tier cross-GPU adapter-handoff recipe and (b) a cautionary
source-verified factuality finding that localizes the reliability drop to the
synthetic-data pipeline.

> **Status (Sep 2026):** v4 published on arXiv. HF dataset and model cards
> reconciled to v4 (commit `3f91dd0`, `687758d`). v5 manuscript draft
> anonymized and pre-staged for the **NAACL 2027 BEA Workshop** (deadline
> 2026-10-15). Pre-registered §3 stratified causal test in flight.

---

## Repository layout

```
StudyAbroadGPT-1/
├── paper/
│   ├── main.tex                    # v4 LaTeX source (preserved; the working source)
│   └── v5-draft.tex                # v5 manuscript draft, 9 pages, anonymized for double-blind
├── legacy/
│   ├── paper-v1.md                 # v1-era draft (the "92% accuracy" version)
│   └── paper-v2-v3.md              # v2/v3 drafts (the Discover Education submission)
├── data/
│   ├── v4-adapter-config.json      # ground-truth LoRA hyperparams, verified against the released config
│   └── v4-50-prompt-eval/          # the 50-prompt held-out eval set + base/LoRA outputs (256 + 512 token)
├── docs/
│   ├── audit/                      # v4 source-verified factuality catalogs (data + model)
│   ├── eval/                       # v4 evaluation outputs (NLP metrics, LLM-judge, summaries)
│   ├── reviews/                    # journal-review materials, integrity report, chapter plan
│   ├── analysis-plans/             # the pre-registered §3 stratified causal test plan (frozen 2026-09-02)
│   ├── hf-cards/                   # the corrected v4 README files for the two HF repos
│   └── superpowers/plans/          # the v5 revision plan
├── scripts/
│   └── eval/                       # analysis harness (v4 scripts + 4 new §3 scripts)
│       ├── stratify_prompts.py            # Step 1: assign held-out prompts to C/W/M strata
│       ├── audit_training_neighbors.py    # Step 2: generate the audit template CSV
│       ├── generate_stratified.py         # Step 3: run base + LoRA on the stratified sample
│       ├── analyze_stratified.py          # Step 4: McNemar's test, CIs, forest plot
│       ├── llm_judge_eval.py              # v4 LLM-as-judge runner
│       ├── compute_reference_metrics.py   # v4 SacreBLEU/ROUGE/BERTScore w/ bootstrap CIs
│       └── (8 v4 scripts total)
└── (LoRA Paper/  is the local working dir; .gitignored)
```

## Headline results (arXiv:2504.15610v4)

| Result | Value | File |
|--------|------:|------|
| Training trajectory | 1.01 → 0.48 → 0.34 over 3 epochs (1 P100 + 2 T4) | `Report_P100/`, `Report_T4/` |
| Peak VRAM | 15.888 / 14.741 GB (P100 / T4) | same |
| Adapter trainable params | 41,943,040 (0.60% of 7.24B) | `data/v4-adapter-config.json` |
| BERTScore F1 (rescaled) | base 0.0981 → LoRA 0.1611, Δ +0.063 [+0.047, +0.078] | `docs/eval/v4-nlp-metrics-512.md` |
| LLM-judge preference | base 46% (23/50) vs LoRA 18% (9/50) vs tie 36%; McNemar-Bowker χ²(2)=9.3, p=0.0095 | `docs/eval/v4-llm-judge.md` |
| Source-verified LoRA errors | 4 / 0 base (on the 18/50 divergent prompts) | `docs/audit/v4-model-factuality-catalog.md` |
| Caveat Phrase Usage | base 2.0% → **LoRA 0.0%** (a safety regression) | `docs/eval/v4-final-experimental-summary.md` |
| Data error rate (n=40) | 11/40 hard (27.5% [Wilson 16–43%]); 16/40 inclusive (40% [26–55%]) | `docs/audit/v4-dataset-factuality-catalog.md` |
| Method-vs-data attribution | "supported" (v4 §4.4) → **"established" pending §3 stratified test** | `docs/analysis-plans/2026-09-02-stratified-causal-test.md` |

## What's in v4 §4 (and what isn't yet in v5)

**Closed in v4:**
- §4.1 Training dynamics on P100 (loss 1.0125 → 0.4787) and T4 (resume → 0.3405)
- §4.2 Feasibility: per-session wall-clock is the binding constraint
- §4.3.1 Source-verified factuality audit (4 LoRA errors vs 0 base on policy-sensitive prompts)
- §4.3.2 Blind LLM-as-judge (Sonnet-family, 50-prompt held-out)
- §4.3.3 Reference-based metrics (SacreBLEU/ROUGE-L/BERTScore) with bootstrap 1,000-resample CIs
- §4.4.1 Causal match (each of the 4 LoRA errors traced to a specific training-data example)
- §4.4.2 Data prevalence audit (n=40, single judge, Wilson CIs)
- §4.4.3 Implication: data is *sufficient* to account for the failure
- §5.2 Limitations: 9 items disclosed
- §5.3 Future work: 4 items (real-student data, multi-judge, §3 stratified test, RAG-vs-LoRA)

**Added in v5 (the §4.5 stratified test, pre-registered):**
- The v4 §5.3(ii') method-vs-data test, with a pre-registered protocol
- Per-stratum 2×2 contingency tables (a, b, c, d)
- McNemar's test (continuity-corrected) per stratum
- Bootstrap 95% CIs on the LoRA − base error rate difference
- A forest plot of base vs LoRA error rate per stratum
- Pre-registered decision rules: if LoRA > base in Stratum W but not in Stratum C, the data attribution is **established**

## Reproducing v4 from a single 16 GB GPU

The complete v4 evaluation can be re-run on a single 16 GB GPU
(Kaggle T4 or Colab T4) using only the released artifacts in this repo:

```bash
# 1. Install dependencies
pip install -U transformers bitsandbytes accelerate peft \
                sentence-transformers sacrebleu rouge-score \
                bert-score pandas numpy matplotlib

# 2. Re-run the LLM-as-judge on the 50-prompt held-out set
python scripts/eval/llm_judge_eval.py \
    --base-model unsloth/mistral-7b-instruct-v0.3-bnb-4bit \
    --lora-adapter millat/StudyAbroadGPT-7B-LoRa-Kaggle \
    --eval-prompts data/v4-50-prompt-eval/evaluation_prompts.csv \
    --max-new-tokens 512

# 3. Recompute reference-based metrics with bootstrap CIs
python scripts/eval/compute_reference_metrics.py \
    --predictions outputs/lora_model_outputs.csv \
    --references data/v4-50-prompt-eval/evaluation_prompts.csv
```

The source-verified factuality audit and the dataset audit are documented
in `docs/audit/v4-model-factuality-catalog.md` and
`docs/audit/v4-dataset-factuality-catalog.md` respectively. Every claim is
cited to an authoritative external source (UKVI, Study Australia, HMS
Admissions, British Council, etc.).

## Running the §3 stratified causal test (v5 contribution)

The test converts v4's "data is sufficient" claim into an "established" claim
by comparing base-vs-LoRA error rates on prompts whose training neighbors
are source-verified correct vs source-verified wrong.

```bash
# Step 1: assign held-out prompts to strata
python scripts/eval/stratify_prompts.py \
    --held-out data/v4-50-prompt-eval/evaluation_prompts.csv \
    --training-data "LoRA Paper/linked_repos/study-abroad-dataset/dataset/study_abroad_dataset.jsonl" \
    --audit-catalog data/v5-audit-catalog.csv \
    --output data/v5-stratified-prompts.csv

# Step 2: extend the audit catalog (n=80 new training answers source-verified)
python scripts/eval/audit_training_neighbors.py generate \
    --training-data "LoRA Paper/linked_repos/study-abroad-dataset/dataset/study_abroad_dataset.jsonl" \
    --output data/v5-audit-template.csv \
    --mode mixed --n-random 60 --n-keyword 25 --seed 42

# Step 3: run base + LoRA on the stratified sample
python scripts/eval/generate_stratified.py \
    --stratified-prompts data/v5-stratified-prompts.csv \
    --strata C,W \
    --output-dir data/v5-stratified-outputs/ \
    --max-new-tokens 512

# Step 4: McNemar's test + forest plot
python scripts/eval/analyze_stratified.py \
    --audit-results data/v5-audit-results.csv \
    --output-dir data/v5-analysis/
```

The full pre-registration is at
`docs/analysis-plans/2026-09-02-stratified-causal-test.md` (frozen 2026-09-02).

## Citation

If you use this work, please cite the v4 paper:

```bibtex
@article{hosen2026finetuning,
  author = {Hosen, Md Millat},
  title = {Fine-Tuning a 7B Advisor on Free-Tier GPUs: An Adapter-Handoff
           Recipe and a Synthetic-Data Reliability Caution},
  journal = {arXiv preprint arXiv:2504.15610v4},
  year = {2026},
  doi = {10.48550/arXiv.2504.15610}
}
```

## License

- The dataset (`millat/StudyAbroadGPT-Dataset`) is MIT-licensed.
- The LoRA adapter (`millat/StudyAbroadGPT-7B-LoRa-Kaggle`) is Apache 2.0
  (the upstream Mistral-7B-Instruct-v0.3 license).
- The released artifacts in this repository are research objects that
  **document a failure mode**; by the v4 source-verified audit, the
  fine-tuned model is **not** fit for deployment as a student-advising
  system without prior factuality-gating or retrieval grounding.

## Author

Md Millat Hosen · [ORCID 0009-0005-7198-9893](https://orcid.org/0009-0005-7198-9893)
