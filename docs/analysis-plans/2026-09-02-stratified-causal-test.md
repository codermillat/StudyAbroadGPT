# Pre-Registered Analysis Plan — Stratified Causal Test of Data Attribution

> **Status:** PRE-REGISTERED. Frozen on 2026-09-02. Do not edit after this date unless an explicit amendment is added at the bottom. Any deviation from this plan in the v5 manuscript must be reported and justified.

**Owner:** Md Millat Hosen
**arXiv ID of source paper:** 2504.15610 (v4; this is the v5 plan)
**Target venue:** NAACL 2027 BEA Workshop (primary); EMNLP 2027 Findings (fallback)
**Companion paper sections:** v4 §4.3.1 (source-verified factuality audit), v4 §4.4 (training-data audit), v4 §5.3 item (ii')

---

## 1. Background and motivation

v4 documents a **reliability finding**: on the 50-prompt held-out set, the LoRA fine-tuned model produced 4 source-verified factual errors (vs 0 for the base) on policy-sensitive topics (HMS admissions, Australian Medicare, Stanford MBBS, Brazil→Bangladesh scholarships). v4 §4.4 then audits the training data and shows the *same error classes* are present in the Gemini-1.0-Pro-generated corpus. From this, v4 claims the data pipeline is "sufficient to account for" the model's failures, and explicitly leaves open the **decisive** test:

> "the method-vs-data test of Section 4.4.3 — comparing base and fine-tuned error rates on prompts whose training neighbors are verified correct versus verified wrong — which would upgrade the data attribution from *supported* to *established*." (v4 §5.3)

This pre-registered plan specifies that test.

## 2. Hypothesis

**H1 (primary).** The LoRA model's error rate on held-out prompts whose training-set nearest neighbors are source-verified *wrong* is significantly higher than the base model's error rate on the *same prompts*. The LoRA model's error rate on held-out prompts whose training-set nearest neighbors are source-verified *correct* is **not** significantly higher than the base model's (i.e., the LoRA model does not "spoil" correct training context).

**H0 (null).** LoRA error rate equals base error rate within each stratum.

If H1 holds, the data attribution is **established** (the model learned from the wrong training data and reproduced the error, as designed). If only the wrong-stratum delta holds, attribution is partially established. If neither holds, v4's data-attribution claim weakens and the v5 manuscript must report that.

## 3. Data

### 3.1 Inputs (already in hand)

- **Held-out test split:** `millat/StudyAbroadGPT-Dataset` test split (402 conversations). All v4 §4.3 evaluation used a fixed 50-prompt topic-stratified sub-sample (seed 42).
- **Training data:** 2,274 conversations, available locally at `LoRA Paper/linked_repos/study-abroad-dataset/dataset/study_abroad_dataset.jsonl` (the raw Gemini-1.0-Pro output).
- **v4 source-verified catalog (training data, n=40 audit):** `docs/audit/v4-dataset-factuality-catalog.md` plus `LoRA Paper/outputs/Dataset_llm_judge_audit.md`. Hard-error rate point estimate 27.5% (Wilson 95% CI 16–43%); inclusive-error rate point estimate 40% (26–55%).
- **v4 source-verified catalog (model errors, n=4 verified cases):** `docs/audit/v4-model-factuality-catalog.md` — the 4 known model errors (HMS, AU Medicare, Stanford MBBS, BR→BD scholarships).
- **Model checkpoints:**
  - Base: `mistralai/Mistral-7B-Instruct-v0.3`
  - LoRA: `millat/StudyAbroadGPT-7B-LoRa-Kaggle` (adapter) or `merged` subfolder
- **Base and LoRA outputs on the 50-prompt v4 set:**
  - `data/v4-50-prompt-eval/base_model_outputs.csv`
  - `data/v4-50-prompt-eval/lora_model_outputs.csv`

### 3.2 Stratification procedure

For each held-out prompt, perform nearest-neighbor retrieval over the training set using a sentence-transformer embedding model:

- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (matches the v4 §3.1.1 topic classifier).
- **Retrieval:** for each held-out prompt, retrieve top-k=5 nearest neighbors from the training set, ranked by cosine similarity over the prompt's first user turn.
- **Neighbor labeling:** each retrieved neighbor is labeled using the §4.4 source-verified factuality method:
  - If the training answer has been audited source-verified *correct* in `docs/audit/v4-dataset-factuality-catalog.md` (or in a new audit pass if not yet covered), label `verified_correct`.
  - If audited source-verified *wrong* (factually incorrect per authoritative source), label `verified_wrong`.
  - If not yet audited, label `unaudited` and exclude from the primary analysis; it can be re-audited in a follow-up pass.

### 3.3 Stratum assignment

For each held-out prompt, assign the stratum based on the **majority label** of its top-5 neighbors:

- **Stratum C** (clean): ≥ 3 of top-5 neighbors are `verified_correct`, 0 are `verified_wrong`.
- **Stratum W** (wrong): ≥ 3 of top-5 neighbors are `verified_wrong`, 0 are `verified_correct`.
- **Stratum M** (mixed): anything else. **Excluded from the primary analysis.** Reported separately for transparency.

Prompts with **fewer than 3 audited neighbors** are also excluded from the primary analysis (i.e., require the training neighbor to be in the audited catalog).

### 3.4 Audit extension

The v4 catalog covers ~40 training answers. For this test we need **at least 30 audited neighbors per stratum**. Since the v4 catalog is small and the W stratum is harder (errors are rarer), we extend the audit:

1. Re-audit the n=40 sample from v4 in a second pass to confirm labels (reliability check).
2. Audit an additional **n=80 random training answers** (stratified to over-sample for likely-erroneous cases) using the same source-verified method. This is a one-author pass; documented in `docs/audit/v5-training-data-audit-extension.md`.
3. Final per-stratum audit budget: target **n_audit ≥ 100 training answers** with **≥ 20 labeled `verified_wrong`**.

The §3 test cannot run until this audit extension is complete. **Pre-registering the protocol now does not require running the extension yet.**

## 4. Sampling and sample size

### 4.1 Stratified prompt sample

Target a fresh stratified sample of held-out prompts (separate from the v4 50):

- **Stratum C (clean):** n_C = 30 prompts. Requires the prompt to have ≥ 3 verified-correct training neighbors.
- **Stratum W (wrong):** n_W = 30 prompts. Requires ≥ 3 verified-wrong training neighbors.

If the audited catalog cannot supply 30 prompts per stratum, run the analysis at whatever n is achievable and report the limitation. Smaller-n results are still informative; they just have wider CIs.

### 4.2 Power analysis

For a McNemar's test on a paired 2×2 (base error vs LoRA error) within a single stratum, the test detects differences of the form P(disagreement = LoRA wrong, base right) vs P(disagreement = base wrong, LoRA right).

For the **primary** contrast (LoRA error rate minus base error rate within Stratum W):

- Observed v4 difference in Stratum W direction: LoRA error ~50% (estimated from v4 §4.3.1; model produced wrong on all 4 high-sensitivity audited prompts where base was right), base error ~5% (estimated from base abstention rate 2/50 + minor factuality slips). Expected delta: ~45pp.
- At n=30 per stratum and expected delta of 25pp with α=0.05 (two-sided): McNemar's has **~50% power**.
- At n=60 per stratum: McNemar's has **~80% power** to detect 25pp.

**Decision rule:** if n_C, n_W < 30, report the test as **under-powered and exploratory**. If n = 30–60, report as **indicative**. If n ≥ 60, report as **adequately powered**.

### 4.3 Optional follow-up: re-use the v4 50-prompt set

The v4 50-prompt set was not stratified. As a sensitivity check, we can classify each of those 50 prompts by stratum (using the procedure in §3.2–3.3) and re-test on the subset that falls into C and W. This is **secondary**, not primary. The primary analysis uses the fresh sample in §4.1.

## 5. Generation and evaluation protocol

### 5.1 Generation settings

Match v4 §3.5.1 exactly:

- 4-bit NF4 quantization
- `do_sample=False`, `temperature=0.0`, `top_p=1.0`
- `max_new_tokens=512` (the 512-token re-run regime, since 96% truncated at 256)
- Same Mistral-Instruct chat template
- Same hardware target (a single 16 GB GPU; Kaggle T4 or Colab T4)

### 5.2 Outputs

For each prompt in the stratified sample, produce:

- `base_response_strat_<prompt_id>.txt`: base model output
- `lora_response_strat_<prompt_id>.txt`: LoRA model output
- `base_meta_strat_<prompt_id>.json`: generation metadata (timestamp, peak VRAM, token count, truncation flag)
- `lora_meta_strat_<prompt_id>.json`: same for LoRA

### 5.3 Factuality audit (the §4.3.1 method, applied)

For each (prompt, model) pair, apply the v4 §4.3.1 source-verified factuality audit:

- A claim is **wrong** if it makes a specific factual assertion that contradicts an authoritative external source (government, university, or official program page) cited in the v4 catalog or in a new audit pass.
- A claim is **correct** if it makes the same specific assertion and the assertion is verified true.
- A claim is **abstention** if the response declines to make the assertion.
- A response is **wrong** if it contains ≥ 1 wrong claim on a policy-sensitive topic.
- Otherwise the response is **correct**.

A single primary rater (the author) does the source verification. A second rater is **not** required for this pre-registered test (consistent with v4's single-author approach). Document the audit protocol in `docs/audit/v5-stratified-test-audit.md`.

## 6. Statistical analysis

### 6.1 Primary test (within each stratum)

For each stratum C and W separately, build a paired 2×2:

| | Base correct | Base wrong |
|---|---|---|
| **LoRA correct** | a | b |
| **LoRA wrong** | c | d |

McNemar's test (with continuity correction) on b vs c:

- H0: P(b) = P(c)
- Test statistic: (|b − c| − 1)² / (b + c)
- Report p-value (two-sided), 95% CI on the difference (Newcombe's method for paired proportions), and the matched-pair odds ratio.

### 6.2 Secondary tests

- **Pooled McNemar across both strata** (Mantel-Haenszel): tests the *common* LoRA-worse-than-base effect across strata.
- **Stratum × model interaction** (Cochran's Q or a logistic mixed model with stratum as a fixed effect): tests whether the LoRA-worse effect is **stronger** in Stratum W than Stratum C.
- **Stratum C test alone:** the null of "no effect in Stratum C" should *not* be rejected (i.e., LoRA does not spoil correct context).

### 6.3 What to report

In the v5 manuscript, include:

1. A table with the per-stratum counts (a, b, c, d), the McNemar p-value, the 95% CI on the LoRA − base error rate difference, and the matched-pair odds ratio.
2. A figure (forest plot or grouped bar chart) of base vs LoRA error rate within each stratum with 95% CIs.
3. A short paragraph stating which of the three decision rules from §4.2 applies (under-powered, indicative, or adequately powered).
4. The pre-registration reference (this file, with the frozen date).

### 6.4 Decision rules for the v5 manuscript

- **If H1 holds in Stratum W (p < 0.05, LoRA > base):** the data attribution is **established**. Update v4 §4.4.3 to "established" and §5.1 to claim a method-vs-data test was run.
- **If H1 is directionally correct but not significant (n too small):** report as "indicative." Keep v4's "supported" language.
- **If H1 fails in Stratum W (LoRA not worse than base even on wrong-context prompts):** v4's data attribution weakens. v5 must report this honestly. The §4.4.1 causal match (4 specific error classes traced to specific training examples) remains valid; the question is whether the *aggregate* error rate is higher in W than in C.
- **If Stratum C also shows LoRA > base:** the model is uniformly worse, not data-pipeline-driven. v5 must report this honestly too.

## 7. Reproducibility and release

### 7.1 Code release

- Stratification script: `scripts/eval/stratify_prompts.py` — takes a held-out prompt file and a labeled training set, returns the stratum assignment per prompt.
- Audit script: `scripts/eval/audit_training_neighbors.py` — re-runs the §4.4 source-verified audit on a new training sample.
- Generation script: `scripts/eval/generate_stratified.py` — runs base and LoRA on the stratified prompt set with v4 settings.
- Analysis script: `scripts/eval/analyze_stratified.py` — produces the McNemar tables, the CIs, and the forest plot figure.

All scripts go to `scripts/eval/`. They must run end-to-end with a single command and produce the v5 §4.4.3 numbers from a stratified prompt file.

### 7.2 Data release

- The stratified prompt sample (`data/v5-stratified-prompts.csv`) with stratum labels.
- The audit extension (`data/v5-training-audit-extension.csv`) with labels.
- Base and LoRA outputs (`data/v5-stratified-outputs/`).
- All released under MIT (consistent with the dataset license).

### 7.3 Anonymization for double-blind

If submitting to a double-blind venue (NAACL 2027 BEA Workshop, EMNLP 2027 Findings), the repository must be reviewable without revealing authorship. Anonymize:

- Replace `millat/`, `codermillat/`, `huggingface.co/millat/`, `github.com/codermillat/` references with `[Anonymized Author / Repository]`.
- Remove the ORCID, email, and affiliation from the manuscript.
- Move the integrity report and the chapter plan to supplementary.

## 8. Timeline

| Date | Milestone |
|---|---|
| 2026-09-02 | **This plan frozen.** Pre-registration logged. |
| 2026-09-05 | §2 reconciliation (HF cards, license) completed manually. |
| 2026-09-08 | Anonymized v5 manuscript draft (9 pages) ready. |
| 2026-09-12 | Statistical tests (Fisher, McNemar-Bowker, Wilson) added to v5 §4.3 and §4.4. |
| 2026-09-15 | Training-data audit extension (n=80 additional training answers audited) complete. |
| 2026-09-25 | Stratified prompt sample (n=30+30, or as many as feasible) generated. |
| 2026-09-30 | Base and LoRA outputs on the stratified sample complete. |
| 2026-10-05 | Source-verified factuality audit on stratified outputs complete. |
| 2026-10-10 | McNemar analysis and forest plot complete. |
| 2026-10-12 | v5 manuscript finalized; pre-registration reference included. |
| 2026-10-15 | **Submit to NAACL 2027 BEA Workshop.** |

## 9. Amendments

Any change to the analysis after this pre-registration is logged here with date, reason, and impact on the conclusions.

*(no amendments yet)*

## 10. Approval

This pre-registration is the author's binding analysis plan. The pre-registration date is 2026-09-02.
