# Chapter Plan — Repositioned Manuscript (Option A: Honest Systems Paper)

**Decided in plan-mode session, 2026-06-14**

- **Direction:** Option A — honest systems/reproducibility paper. No new training compute.
- **Core claim framing:** Two-pillar — (1) free-tier feasibility recipe (adapter-only cross-GPU handoff), and (2) **honest reliability finding, with the cause localized**: fine-tuning faithfully raised distribution-fidelity (BERTScore) but factual reliability *dropped* — and a direct audit of the training data shows **the method did not introduce the errors; it reproduced errors already present in the `gemini-1.0-pro` synthetic corpus.** The method is sound; the synthetic-data pipeline is the evidenced cause. This is the evaluation headline.
- **Evaluation plan (DONE, no API key/GPU needed):** now FOUR converging signals — three on the model, plus a direct audit of the data that closes the causal loop —
  - **Model factuality audit** (source-verified ground truth, judgment-free): 4 hard LoRA errors on policy-sensitive topics, 0 for base; 16/18 divergent prompts favor base. → `outputs/Model_factuality_error_catalog.md`
  - **Model LLM-as-judge** (blind, non-Gemini): base preferred 46% vs LoRA 18%; domain Δ−0.40 [−0.62,−0.18], helpfulness Δ−0.32 [−0.52,−0.12], both CIs exclude 0. → `outputs/Model_llm_judge_summary.md`
  - **BERTScore/ROUGE** (existing): LoRA > base = fidelity-to-synthetic-distribution, not quality.
  - **Dataset audit (NEW — the causal closure):**
    - *Causal match*: all 4 of the model's hard errors are present, in the same form, in the gemini-1.0-pro training answers (smoking gun: AU-Medicare false-eligibility claim appears verbatim-in-kind in both data and model output). → `outputs/Dataset_factuality_error_catalog.md`
    - *Prevalence*: LLM-as-judge over a random sample (n=40, seeds 42+123) → **27.5% hard-error rate [Wilson 95% CI 16–43%]**, 40% inclusive [26–55%]. ~¼–½ of training answers carry a verifiable factual error; dominant mode is confident fabrication of citable-sounding specifics. → `outputs/Dataset_llm_judge_audit.md`
    - *Provenance*: generator is `gemini-1.0-pro` (Dec-2023 model), hardcoded at `conversation_generator.py:79`; dataset built 2024 via a `{program}×{university}` template cross-product (`config.py`) that mechanically produced incoherent prompts, with **no factual-verification stage** (`quality_validator` checks structure/length only).
  - Scripts: `llm_judge_eval.py`, `analyze_judge_scores.py` (releasable artifacts).

---

## 1. Corrected Thesis (one sentence)

> A multi-epoch fine-tune of a 7B model can be completed entirely on **recurring free-tier 16 GB GPUs** by checkpointing **only the LoRA adapter** and handing it off across heterogeneous machines (P100 → T4) at small, measurable cost. Evaluating the resulting adapter honestly, we find that fine-tuning on **unverified synthetic advising data increases fidelity to the training distribution (BERTScore) while degrading factual reliability** — the LoRA model produces more confident, source-contradicted errors on policy-sensitive topics than the un-fine-tuned base, shown by a blind LLM-as-judge and a source-verified factuality audit. **Auditing the training data directly, we show this is not a fine-tuning artifact: the model's errors are reproductions of errors already present in the `gemini-1.0-pro`–generated corpus (~28–40% of sampled answers carry a verifiable factual error), so distribution-faithful fine-tuning behaved exactly as intended on a flawed distribution.** The locus of failure is the synthetic-data pipeline, not the adapter-handoff method.

**What this paper is NOT (claims removed):**
- ❌ "Quantization-boundary finding" — unsupported; quantization held constant across the claimed boundary; 0.48 is still descending at end of epoch 1 (slope −0.00027/step).
- ❌ "Optimizer + scheduler state transferred" — false per released code; only adapter weights cross the boundary.
- ❌ "Two-phase schedule as a controlled variable" — not controlled (reset optimizer + 4× batch + extra epochs change together).

## 2. Three Contributions (honest version)

1. **Free-tier feasibility recipe.** A documented protocol to finish a 3-epoch 7B QLoRA run under the ~9–12 h session/time limits of free Kaggle/Colab GPUs by splitting epochs across sessions and GPU types. Real constraint, reproducible workaround.
2. **Adapter-only handoff is sufficient.** Empirically, continuing training across machines needs **only the ~160 MB adapter**, not full optimizer/scheduler state. The cold-optimizer cost is a one-time +0.02 loss bump (0.41→0.43) recovered within ~15 steps.
3. **A cautionary reliability finding, with the cause isolated to the data — plus the evaluation harness that produced it.** On a blind held-out comparison, fine-tuning on unverified synthetic data made the model *less* factually reliable (base preferred 46% vs 18%; 4 source-verified LoRA errors vs 0 for base on visa/health/admissions), even though it raised BERTScore. Critically, we **apply the same audit mechanism to the training data itself** and show (a) each of the model's hard errors is already present in the gemini-1.0-pro answers, and (b) ~28–40% of a random sample of training answers carry a verifiable factual error. This **isolates the failure to the synthetic-data pipeline and exonerates the method** — a stronger, more defensible claim than "fine-tuning hurt the model." We release the dataset, adapter, blinded harness, LLM-as-judge scripts, and both the model and dataset factuality catalogs. Transferable warning: fine-tuning on unverified LLM-generated data inherits the generator's errors, and fidelity metrics (BERTScore/ROUGE) will *reward* that inheritance.

## 3. Per-Chapter Plan

### Title / Abstract  (~200 words)
- New working title: *"Fine-Tuning a 7B Advisor on Free-Tier GPUs: An Adapter-Handoff Recipe and a Synthetic-Data Reliability Caution."*
- Abstract arc: feasibility problem → adapter-handoff recipe (corrected: adapter-only, cold-optimizer bump) → the reliability finding (LoRA more confidently wrong on policy-sensitive facts; base preferred 46% vs 18%; 4 sourced errors vs 0) → BERTScore-up-but-reliability-down framed as fidelity-vs-quality → **cause isolated: dataset audit shows the errors pre-exist in the gemini-1.0-pro corpus (~28–40% error rate), so the method is sound and the data pipeline is the cause.** Drop all "quantization-boundary / the protocol is the artifact" language.

### §1 Introduction  (~600 words)
- **Purpose:** establish the *real* pain — free-tier GPUs time out before a multi-epoch 7B run finishes; students in resource-constrained settings hit this constantly.
- **Cut:** §1 para 3 ("finding vs. application vs. engineering report") entirely.
- **Core argument:** the binding constraint is *per-session wall-clock + per-step VRAM*, not total compute; adapter-handoff converts a too-long single run into several in-budget sessions.
- **Contributions list:** replace with the three above.

### §2 Literature Review  (~700 words, mostly survives)
- Keep PEFT/QLoRA/Unsloth subsections (§2.2) — accurate and well-cited.
- **Reframe §2's closing positioning:** the contribution is a *systems/reproducibility recipe*, not a method or a finding. Add 1–2 sentences on checkpointing / multi-session training to situate the adapter-handoff claim.
- Soften advising-domain framing (§2.3) — it's the application, not the contribution.

### §3 Methodology  (~1200 words — now the heart of the paper)
- **Promote §3.3 (two-phase schedule) to centerpiece.** Add an explicit **handoff procedure**: what is saved (adapter only), what is reloaded (`load_adapter`), what is reset (optimizer, scheduler), and why that's sufficient.
- **FIX the false claim** in §3.3: "optimizer state and scheduler transferred" → "adapter weights only; optimizer and scheduler reset on the second GPU."
- Keep Table 2 (hyperparameters) — it directly answers Reviewer 2 #3.
- Keep §3.1 dataset detail + quality pipeline — answers Reviewer 2 #4. Verify every Table 1/Table 3 number against `outputs/Dataset_dataset_quality_metrics.json`.
- **Add generator provenance to §3.1:** dataset generated 2024 with `gemini-1.0-pro` (`conversation_generator.py:79`) via a `{program}×{university}` template cross-product (`config.py`); the `quality_validator` enforces structure/length, **not factual correctness**. State this plainly — it is the mechanism behind the §4 dataset audit, and framing it as a known design limitation (weak 2023 generator + no fact-gate) is what makes the reliability finding a *data-pipeline* result, not a method failure.
- Remove the "controlled variable" sentence.

### §4 Results  (~1500 words — restructured; the reliability finding is the spine)
- **DELETE §4.1 "The Quantization-Boundary Finding."** Replace with §4.1 "Training Dynamics Across the Handoff": report the two loss curves honestly as a standard 3-epoch trajectory (1.01 → 0.48 end-epoch-1 → 0.34 end-epoch-3), with the +0.02 resume bump called out as the cold-optimizer cost.
- **§4.2 "Feasibility & Resource Use":** lead with peak VRAM (15.888 / 14.741 GB) and per-session wall-clock vs. free-tier limits — this is the recipe's evidence.
- **§4.3 "Evaluation: a fidelity–reliability trade-off" (NEW HEADLINE).** Present three converging signals in order of strength:
  1. **§4.3.1 Factuality audit (judgment-free, sourced).** The 4 verified LoRA errors (HMS GRE, AU Medicare, Stanford MBBS, BD scholarships) vs 0 base; 16/18 divergent prompts favor base. Table + the error catalog. Cite gov/university sources. *This is the strongest result — lead with it.*
  2. **§4.3.2 Blind LLM-as-judge.** Base preferred 46% vs 18%; domain Δ−0.40 [−0.62,−0.18], helpfulness Δ−0.32 [−0.52,−0.12]. Disclose explicitly as LLM-as-judge (single Sonnet judge, pointwise, synthetic-split prompts) — NOT human eval. Note the per-item reasons match the audit.
  3. **§4.3.3 Reference metrics (BERTScore/ROUGE).** LoRA > base — but frame as fidelity-to-synthetic-distribution, the mechanism that explains why matching the data more closely *lowered* reliability.
- **§4.4 "Auditing the training data: isolating the cause" (NEW — the causal closure; arguably the most important new section).** Apply the *same* judgment-free, source-verified mechanism to the training data:
  1. **§4.4.1 Causal match.** All four model errors are present, in the same form, in the gemini-1.0-pro training answers. Lead with the smoking gun: the AU-Medicare false-eligibility claim appears in both the training data and the model output. Table mapping each model error → its training-data source (from `Dataset_factuality_error_catalog.md`).
  2. **§4.4.2 Prevalence.** LLM-as-judge over a random sample (n=40, seeds 42+123): **27.5% hard-error rate [Wilson 95% CI 16–43%]**; 40% inclusive [26–55%]. Report as "roughly a quarter to a half," single-judge, wide CI. Name the dominant failure mode (fabricated citable-sounding specifics) and tie it to the weak generator + template cross-product + no fact-gate. From `Dataset_llm_judge_audit.md`.
  3. **§4.4.3 Implication.** Distribution-faithful fine-tuning behaved as intended on a flawed distribution → **method exonerated, data pipeline is the cause.** Pre-empts the reviewer question "how do you know it's the data and not the fine-tuning?"
- **§4.5 Synthesis:** four signals converge → fine-tuning on unverified synthetic data trades factual reliability for distribution-fidelity, and the direct dataset audit localizes the cause to the gemini-1.0-pro pipeline rather than the adapter-handoff method.
- Drop all "quantization-boundary floor" interpretation paragraphs.

### §5 Discussion / Limitations  (~800 words)
- **Lead with the finding's implication:** synthetic-data fine-tuning of small advising models needs factuality gating; distribution-fidelity metrics (BERTScore) can move *opposite* to ground-truth reliability and must not be reported alone. **The mechanism is now demonstrated, not hypothesized** — a weak 2023 generator (`gemini-1.0-pro`) + template cross-product + no fact-verification stage produced a corpus ~¼–½ of which is factually wrong, and faithful fine-tuning inherited it.
- **State the method-vs-data verdict explicitly:** the adapter-handoff recipe is not implicated; an identical recipe over a fact-gated corpus would be expected to improve, not degrade, reliability. This protects the systems contribution from the reliability finding.
- Lead limitation: fully synthetic train + eval data (Reviewer 2 #2) — now the *subject* of a measurement, not just an apology.
- **Eval honesty caveats (must state):** model factuality audit is curated (not full 50×2); LLM-judge (model and dataset) is a single non-human judge; dataset prevalence is n=40 with a wide CI → report as indicative; human scoring was NOT completed (correct the old §3.4.3 promise of author+co-reviewer κ — do not claim κ).
- **Add training-honesty paragraph:** loss reduction is epochs+batch, not a quantization effect; no boundary claimed. Pre-empts Reviewer 1.
- Future work: real student data + IRB pilot + second judge model + full systematic factuality pass — all marked not-yet-done.

### §6 Conclusion  (~300 words)
- Restate the feasibility recipe + adapter-only sufficiency + honest eval. No "finding" language.

## 4. Evidence Map (claim → artifact)

| Claim | Backing artifact | Status |
|---|---|---|
| 3-epoch trajectory 1.01→0.48→0.34 | `Report_P100/train/train-loss.csv`, `Report_T4/train/loss__MAX.csv` | ✅ verified |
| Resume bump 0.41→0.43 (cold optimizer) | same loss CSVs | ✅ verified |
| Adapter-only handoff (no optimizer state) | `Study_Abroad_GPT_Kaggle-T4.ipynb` (`load_adapter`, fresh `trainer.train()`, no `resume_from_checkpoint`) | ✅ verified |
| Peak VRAM 15.888 / 14.741 GB | `Report_P100/report.txt`, `Report_T4/report.txt` | ✅ verified |
| Held-out reference metrics @512 (BERTScore/ROUGE) | `outputs/Model_standard_nlp_metrics_summary_512.md` | ✅ verified |
| LLM-as-judge: base preferred 46% vs 18%; Δ domain −0.40, help −0.32 (CIs exclude 0) | `outputs/Model_llm_judge_summary.md`, `Model_llm_judge_scores.csv` | ✅ computed |
| Factuality audit: 4 sourced LoRA errors vs 0 base; 16/18 divergent favor base | `outputs/Model_factuality_error_catalog.md` | ✅ verified |
| Causal match: all 4 model errors present in gemini-1.0-pro training data (AU-Medicare smoking gun) | `outputs/Dataset_factuality_error_catalog.md` | ✅ source-verified |
| Dataset prevalence: 27.5% hard-error [16–43%], 40% inclusive [26–55%], n=40 (seeds 42+123) | `outputs/Dataset_llm_judge_audit.md` | ✅ computed |
| Generator = `gemini-1.0-pro` (2024); template cross-product; no fact-gate | `conversation_generator.py:79`, `config.py`, `quality_validator.py` | ✅ verified in code |

## 5. Evaluation status (DONE — no remaining user task)

The evaluation that answers Reviewer 2 is complete and on disk (model factuality audit + LLM-as-judge + reference metrics + **dataset causal/prevalence audit**). **No hand-scoring is required.** Remaining *optional* hardening, all marked future-work in the draft:
- Full systematic 50×2 model-factuality scoring (currently curated to divergent cases).
- Larger systematic dataset audit (n≥200, multiple judges, inter-rater agreement) to tighten the prevalence CI beyond the current n=40.
- A second, independent judge model (needs a real `sk-ant-…`/OpenAI key or a local LLM — not currently available).
- Real human raters / real-user pilot (IRB) — the genuinely-human eval, still future work.

**Integrity must-fix:** delete the old §3.4.3 promise of author+co-reviewer Cohen's κ — human scoring was not done; replace with the LLM-as-judge disclosure.

## 6. Venue Recommendation
- **Not** a general education journal (the §-mismatch that drew Reviewer 1's "engineering report" verdict).
- Target a reproducibility / efficient-ML / systems-for-ML workshop or track (e.g., MLSys-adjacent workshops, "practical/efficient NLP" tracks, or a reproducibility venue). The honest framing fits there and reviewers value working recipes + released artifacts.

## 7. Argument Stress Test (Step 3)
- *Weakest point:* "is adapter-handoff non-obvious?" — defend via the explicit free-tier time-limit constraint + the measured cold-optimizer cost (others assume you need full optimizer state; you show you don't).
- *Reverse test:* if total compute is unconstrained, the recipe is pointless — so scope every claim to the recurring-free-tier setting, never to "efficiency" in absolute GPU-hours.
- *Reviewer attack "the reliability drop means your method/training is broken":* now directly rebutted by §4.4 — the errors pre-exist in the data (causal match) and the data is ~¼–½ wrong (prevalence). The method faithfully learned a flawed distribution; it is not the cause. This converts the paper's most dangerous result into its strongest, most defensible contribution.
- *Residual exposure:* prevalence rests on a single LLM judge at n=40 (wide CI). Mitigate by reporting it as indicative, anchoring every counted error to an external source, and listing the larger multi-judge pass as future work.
