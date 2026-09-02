# v5 Revision Plan — arXiv:2504.15610

> **Goal:** Turn arXiv:2504.15610v4 into a paper that (a) can be honestly submitted to a tier-2 ML/AI venue as a synthetic-data cautionary case study, (b) survives peer review at a methods/evaluation level, and (c) is internally consistent across the manuscript, the dataset card, and the model card.
>
> **Architecture:** v5 = same data + same adapter + same three-epoch run, but (i) tighter framing, (ii) one new decisive experiment (the "established" causal test from §5.3 item ii'), (iii) one new replication (multi-judge or multi-seed), (iv) reconciled numbers and licenses, and (v) a credible re-targeting to a venue that fits the actual contribution.
>
> **Tech Stack:** LaTeX (existing arXiv source), Hugging Face Datasets/Hub for the two cards, the released evaluation harness at `github.com/codermillat/LoRA-Paper` (which the paper says contains every artifact for §4).

> [!info] Plan conventions
> - Priorities: **P0** = blocker / venue-deciding, **P1** = high-value for a methods reviewer, **P2** = polish, **P3** = optional.
> - Owner: solo author (MD Millat Hosen) unless noted; the paper declares no co-authors and no funding.
> - "Evidence needed" = what must exist as a file, table, or run before the prose can claim it.
> - Claim IDs (C…) and evidence IDs (E…) reuse the conventions from `scientific-research-workflows:scientific-writing` (claim ID, source ID); a per-task IDs are listed only where a new artifact must be opened later.

---

## 0. TL;DR — the three things v5 must do

1. **Pick a venue and stop hopping.** Five submissions across two journal families (education → ML) shows the paper is currently mis-fit for both. v5 is either a tier-2 ML evaluation/case-study paper or it stays a preprint with a strong open-source release. See §1.
2. **Add the one decisive experiment the v4 Future Work §5.3(ii') already names.** That test (compare base vs. LoRA error rates on prompts whose training neighbors are verified correct vs. verified wrong) converts the data attribution from *supported* to *established* and is the single highest-leverage new result.
3. **Reconcile the manuscript, dataset card, and model card.** Three live inconsistencies (epoch count, parameter count, license) and one stale claim ("Factuality audit pending") on the two HF cards. None of these are research problems; all of them are review-killers.

The remaining tasks (§3–§9) are the standard reviewer-defense work: statistical tests, multi-judge replication, expanded related work, parameter and pipeline detail, and a methods-vs-claim tight-pass.

---

## 1. Strategic decision: pick a venue (P0) — do this first, before any other work

### Why this is the first task

Your journal history, in your own words, is:

| Submission | Venue | Outcome | Stated reason |
|---|---|---|---|
| 1 | ETHE (Springer) | Desk-rejected (Dec 2025) | "Out of scope" — not educational enough |
| 2 | EAIT (Springer) | Desk-rejected (Jan 2026) | "Too technical" + undisclosed-preprint integrity flag |
| 3 | Discover Education (Springer) | Rejected after full review (Jun 2026) | R1: novelty/evaluation; R2: training-loss-only eval, synthetic-only data, missing hyperparameters, missing pipeline detail |
| 4 | TMLR | Desk-rejected (Jun 2026) | "Submission/overlap/stylefile" (unspecified) |
| 5 | DMLR | Desk-rejected (Aug 2026) | "Out of scope / stylefile / under review" (unspecified) |

**Read of the pattern:** Education journals want real human-subjects evidence you don't have; ML methods journals want either (a) a new method or (b) a large-scale evaluation. v4 is neither — it's a *negative case study* on a small synthetic dataset. v5 cannot become a methods paper without new method content, but it can become a credible evaluation/case-study paper by closing the four R2 critiques and the §5.3 future-work items.

### Acceptance criteria for the strategic decision

Before writing any other task, write a one-page decision memo (≤ 500 words) at `docs/decisions/2026-09-02-v5-venue.md` answering:

1. What is v5's primary contribution, in one sentence? (e.g., "An empirical case study showing that LoRA fine-tuning on unverified LLM-generated synthetic data can degrade source-verified factuality while raising BERTScore, with the failure mode localizing to the training distribution.")
2. Which 3 venues does that sentence fit? (Candidates to evaluate: DMLR [re-submit if §3.1 fixes scope], TMLR [re-submit if a non-trivial method/eval contribution is added], ACL/EMNLP Findings [case-study fits the eval track], AIES/EAAMO/FAccT [the cautionary use case fits], EDM [education data mining, fits the eval-on-real-prompts angle], ICLR Workshop on Synthetic Data, JMLR [unlikely without new method].)
3. What is the *minimum* set of additional results needed to make that venue a non-laughable submission? (This defines which of §3–§9 are P0 vs. can be deferred.)
4. What is the deadline? (This sets the sequencing.)

**Evidence needed:** the five rejection letters (or a faithful summary with submission IDs) so the memo can quote them. If you no longer have them, write what you remember and mark each claim `[UNVERIFIED]`.

**Owner:** author. **Effort:** half a day. **Blocks:** every other task in this plan.

---

## 2. Reconcile the manuscript with the Hugging Face cards (P0) — pure consistency work, one afternoon

These are not scientific weaknesses; they are correctness bugs that any reviewer can catch in 30 seconds with the URL bar. Fix them as a single batch before submitting anywhere.

### 2.1 Epoch count disagrees

- **Paper v4 (§3.2, §4.1) says:** "three-epoch QLoRA fine-tune".
- **Model card says:** "Number of Epochs: 4".
- **Fix:** Verify the training report in `Report_P100/` and `Report_T4/`. The paper is the source of truth; the model card is wrong. Set model card epoch count = 3. Save the verification to `docs/audit/2026-09-02-epoch-reconciliation.md`.
- **Evidence needed:** the two training reports. Claim ID `C-EP01`: "3 epochs total" → evidence `E-EP01` = `Report_P100/*.json` and `Report_T4/*.json`.

### 2.2 Trainable-parameter count disagrees

- **Paper v4 (abstract, §3.2) says:** "41.9M parameters" for the LoRA adapter.
- **Model card says:** "LoRA Trainable Parameters: ~4.7M (0.07% of model)".
- **Fix:** Compute the actual count from the `peft` adapter config. Mistral-7B + rank 16 across Q/K/V/O + gate/up/down on every layer should give ~41M. The model card's 4.7M is roughly the per-layer attention-only count; it dropped the FFN targets. Set the model card to match the paper (41.9M) and add the per-target breakdown (Q, K, V, O, gate, up, down) so the next reviewer doesn't have to re-derive it.
- **Evidence needed:** the `adapter_config.json` shipped in the model repo. Claim ID `C-PA01`: "41.9M trainable LoRA params" → evidence `E-PA01` = `adapter_config.json`. Save reconciliation to `docs/audit/2026-09-02-param-count.md`.

### 2.3 License is wrong in the paper

- **Paper v4 (Declarations / "Use of Generative AI" paragraph) says:** "the model's research-only Mistral Research License".
- **Model card says:** Apache 2.0.
- **Reality:** `mistralai/Mistral-7B-Instruct-v0.3` is **Apache 2.0** (MRL applies to earlier Mistral releases and to the non-Instruct v0.3). The paper is wrong.
- **Fix:** Replace "Mistral Research License" with "Apache License 2.0" in v5 §Declarations and the affected footnote. The "research-only" caveat in the same paragraph stands on your own intended-use statement, not on the upstream license.
- **Evidence needed:** the LICENSE file in the model repo and a screenshot/quote from the upstream Mistral-7B-Instruct-v0.3 model card showing Apache-2.0. Claim ID `C-LI01`.

### 2.4 Stale "pending" status on both HF cards

- **Dataset card top line:** "Manual blinded scoring pending ⏳ | Factuality audit pending ⏳"
- **Model card top line:** "Manual blinded scoring pending ⏳ | Factuality audit pending ⏳"
- **Reality:** v4 contains both. The cards were not updated when v3 → v4.
- **Fix:** Replace with "Manual blinded scoring and source-verified factuality audit complete; see arXiv:2504.15610 §4.3 and §4.4." Add a one-paragraph summary of the headline findings (46% vs 18%; 4 vs 0; 28–40%) at the top of each card. The cards should *cross-reference the paper* as the source of truth for any number they display, since the paper is now the most-current artifact.
- **Evidence needed:** the v4 numbers, taken from the LaTeX source.

### 2.5 Old "study-abroad-guidance-ai" model variant

- The dataset card lists `millat/study-abroad-guidance-ai` and `millat/StudyAbroadGPT-7B` as "Models trained or fine-tuned on" this dataset. v4 paper does not reference these. v5 should not either.
- **Fix:** Audit those repos. If they are v1–v3 era artifacts, deprecate them or pin a notice ("superseded by arXiv:2504.15610v4; do not use"). If they are independent, leave them; in that case, document the relationship in the v5 paper.

**Acceptance criteria for §2:** the model card, the dataset card, and the v5 manuscript have the same numbers, the same license, and the same "what was done" status. A reviewer can paste any one number into the other two without a contradiction.

**Owner:** author. **Effort:** ≤ 1 day.

---

## 3. Close the "established" causal test — the decisive new experiment (P0)

This is the single highest-leverage experiment for v5. v4's own §5.3 calls it out as the test that would upgrade data attribution from *supported* to *established*. Without it, every ML reviewer will ask for it.

### 3.1 What the test is

> Compare base and LoRA error rates on a *paired* prompt set where each prompt's nearest training neighbors are pre-classified as **verified correct** vs **verified wrong** (per the §4.4.1 source-verified method). If the LoRA model is significantly worse than base on the *verified-wrong* neighbors but not on the *verified-correct* ones, the data-attribution is established. If both are worse, the conclusion weakens to "fine-tuning uniformly degrades" — still a publishable result, just a different one.

### 3.2 Why this is non-trivial to set up

- You need a sample of held-out prompts stratified by the *correctness of their training neighbors*, not just by topic. This requires:
  1. The §4.4 source-verified catalog already released with the paper (causal-match catalog).
  2. A nearest-neighbor retrieval (e.g., `sentence-transformers` embeddings) from each held-out prompt into the training set.
  3. Stratification: take N prompts whose top-k neighbors are all verified-correct, N whose top-k are all verified-wrong, N mixed.
  4. Generate base and LoRA responses for the stratified set under the same deterministic settings as §4.3.1.
  5. Apply the §4.3.1 source-verified factuality audit (NOT the LLM judge) to each response.
  6. Test: McNemar's test on the matched 2×2 (correct/wrong) × (base/LoRA) within each stratum. Report effect size and 95% CI.

### 3.3 Evidence the test will produce

- **Table (new, in v5):** stratified error rates, base vs LoRA, by neighbor-correctness stratum. With n=30 per stratum and the rates you're seeing, McNemar's will have ~50% power to detect a 25pp difference. If that's not enough, expand to n=60 per stratum and re-run.
- **Figure (new, in v5):** forest plot of the base-vs-LoRA OR within each stratum, with CIs.
- **Code release:** the stratification script, the retrieval script, and the analysis notebook go to `github.com/codermillat/LoRA-Paper` (which v4 §Declarations already names as the evaluation-harness repo). The paper's reproducibility claim rests on this repo.

### 3.4 Where this lives in v5

- New §4.5: "Establishing the data attribution: a stratified causal test" between current §4.4 and §5.
- Update §5.1 (Implications) to use *established* instead of *supported* where the test supports the upgrade.
- Update §5.3 (Future Work) to remove the ii' item (it's now done) and add the next-tier items (multi-seed, multi-judge, RAG counterfactual).

### 3.5 Acceptance criteria

- Stratified error-rate table with p-values, CIs, and exact counts (not just proportions).
- Pre-registration: write the analysis plan *before* running it, save it to `docs/analysis-plans/2026-09-02-stratified-causal-test.md`, and freeze it. The paper's §5.2 item 6 ("single fine-tuning run") is mitigated here, not eliminated.
- The script and a re-runnable notebook are in the released evaluation repo.

**Owner:** author. **Effort:** 2–4 weeks, dominated by the source-verified audit at scale. **This is the bottleneck for any venue decision made under §1.**

---

## 4. Close the Discover Education R2 four-point critique (P0 — every point is addressable now)

These are explicit reviewer requirements, not speculation. They are independent of §3 and can be done in parallel.

### 4.1 R2-A: "Evaluation deficit — training loss only"

**Reviewer's exact ask:** "test against an independent test set and report standard NLP metrics (BLEU, ROUGE, BERTScore, perplexity) against the un-fine-tuned Mistral-7B baseline."

**Current state in v4:** You already do BERTScore and a re-run at 512 tokens (§4.3.3). You do **not** report SacreBLEU, ROUGE, or perplexity on the held-out test set in a single unified table.

**Fix for v5:**
- Add **Table X (new):** Base vs LoRA on the held-out test set (n=402): SacreBLEU, ROUGE-L, ROUGE-1/2, BERTScore F1, perplexity, and the §4.3.1 source-verified factuality rate. Make this *the* head-to-head table.
- Add a per-topic breakdown (use the §3.1.1 topic distribution) so the numbers are not aggregated over topics that differ in difficulty.
- v4 §4.3.3 already qualifies these as "fidelity to synthetic distribution, not quality". v5 must say this in the table caption, in the row labels, or both.
- v4's claim ID `C-MET01` (BERTScore +0.063) needs to be augmented with `C-MET02–C-MET05` for the new metrics, each with evidence `E-MET0n` pointing to the released reference-metric script and the test-set outputs.

**Evidence needed:** the test-set outputs from `load_dataset("millat/StudyAbroadGPT-Dataset", split="test")` and the released `llm_judge_eval.py` / reference-metric scripts. The hard work is generating the base-model outputs if you don't already have them cached (the paper says the 50-prompt set is released; the full 402-prompt base outputs are not explicitly listed in the release).

**Acceptance criteria:** One table, base vs LoRA, with the five metrics plus the §4.3.1 source-verified factuality rate, on the full 402-prompt held-out test set, with explicit "fidelity" framing in the caption.

### 4.2 R2-B: "Synthetic data bias — use real data or do a human survey"

**Current state in v4:** §5.3 item (i) names "IRB-approved real student–advisor interactions" as future work; v4's §Declarations reaffirms this.

**Honest read:** You will not collect real interactions for v5. v4's response — that this is a cautionary case study, not a deployment claim — is structurally correct, but the reviewer can still push.

**Fix for v5 (no new data required):**
- Restate in §1 and §5.1 that v5 is *not* a deployment study; the contribution is the evaluation methodology + the negative finding, both of which are valuable on synthetic data precisely because synthetic data is what practitioners actually fine-tune on.
- Cite at least 3 sources on synthetic-data prevalence in domain fine-tuning (Gekhman 2024 is already in your refs; add Shumailov 2024 [already in], plus 1–2 from 2025: e.g., "The False Promise of Imitating Proprietary LLMs" [Gudibande 2023, already cited], plus a recent systematic survey if one exists).
- If §3's stratified test is in v5, lean on it as the *partial* answer to R2: by stratifying on verified-correct vs verified-wrong training neighbors, you are effectively doing the strongest test available without real human data.
- If a venue path requires it (§1), an *optional* add-on is a small human spot-check of the dataset audit (n=20–40, one rater, blind to the LLM judge's verdict). This is much cheaper than a human study and discharges the most aggressive version of the R2 critique.

**Acceptance criteria:** A revised §1 paragraph that preempts the R2 critique and ties it to the §3 result. If you do the human spot-check, document the protocol in `docs/human-eval/2026-09-02-spot-check-protocol.md` *before* running it.

### 4.3 R2-C: "Missing parameters"

**Reviewer's exact ask:** "specify exact LoRA hyperparameters (rank, alpha, dropout) and training details (learning rate, scheduler, warmup)."

**Current state in v4:** §3.2 gives rank=16, alpha=32, NF4. The model card adds warmup_ratio=0.03, LR=2e-4, linear scheduler, max_grad_norm=0.3, batch=2×grad_accum=4, but this is on the HF card, not in the paper.

**Fix for v5:** Move every hyperparameter from the model card into a **Table 1 (new, in v5 §3.2)**: every value in one place, with units. The reader should not have to read a HF card to know what you trained. Items at minimum: base model & version; quantization (bits, scheme, double-quant?); LoRA (r, α, dropout, target modules, "rank-stabilized" yes/no); optimizer & β; LR & scheduler; warmup; weight decay; grad clip; batch (per-device, grad-accum, effective); epochs; sequence length; seed; gradient checkpointing on/off; flash attn on/off; any Unsloth-specific flags.

**Acceptance criteria:** A single §3.2 table that fully specifies the run. Cross-check every value against the training reports in `Report_P100/` and `Report_T4/`; mark `[UNVERIFIED]` if you can't reconcile.

### 4.4 R2-D: "Missing pipeline details"

**Reviewer's exact ask:** "lack of description of your synthetic dataset construction and validation/quality analysis scripts."

**Current state in v4:** §3.1 has topic distribution, prompt templates, and quality pipeline subsections. The release points to `github.com/codermillat/study-abroad-dataset` for the generation scripts.

**Fix for v5:**
- Add a **schematic figure (new, in v5 §3.1)**: the full synthetic-data pipeline as a flow diagram (research → topic & prompt-template design → Gemini 1.0 Pro generation → post-processing → structural validation → train/test split → release). Currently the README has a Mermaid diagram; the paper does not.
- Add a **prompt-template appendix (new, Appendix A)**: at least one full example of each template type, with the Gemini call parameters (temperature, top_p, max_tokens, stop sequences, system prompt). Don't dump the entire generation script; just the templates and the call config.
- Add a **per-prompt-template quality breakdown table (new, Table 2)**: for each template, how many training examples, mean token count, the §4.4 audit error rate with 95% CI. This both answers R2-D and gives §3 something to anchor on.
- Verify `github.com/codermillat/study-abroad-dataset` is actually public and runnable. If it isn't (or the README is missing), fix that *before* citing it as the release of record.

**Acceptance criteria:** A reader can reproduce the dataset from the paper + the appendix + the public repo.

**Owner:** author. **Effort:** §4.1 = 3–5 days; §4.2 = 1 day (no new experiments); §4.3 = 1 day; §4.4 = 2–3 days. Total ≈ 1–2 weeks, mostly waiting on compute for §4.1.

---

## 5. Defensive statistics — what an ML methods reviewer will ask for (P1)

None of these are on their own blockers, but any tier-2 ML venue will raise at least one of them. Doing all five is what separates "passes review" from "frustrates reviewers."

### 5.1 Significance test on the 4-vs-0 error count

- **What's there:** "four confident errors from the LoRA model against zero for the base."
- **What's needed:** Fisher's exact test (one-sided, base error rate < LoRA error rate). Report p-value, the exact 2×2 table, and a 95% CI for the difference in proportions (Newcombe or Wilson).
- **Honest framing if p is non-significant at this n:** "Direction-consistent across all 4 audited divergent prompts; under-powered at n=18 for a strict significance test; a power analysis shows n≥60 audited prompts needed to detect the observed difference at 80% power. The §3 stratified test, when added, supplies the power."

### 5.2 Significance test on the 46%-vs-18% judge preference

- **What's there:** "blind LLM-as-judge preferred the base model on 46% of prompts versus 18% for the fine-tuned model."
- **What's needed:** This is on the 50-prompt set, and the splits are non-exclusive (ties exist). Use a paired test appropriate for ranked preferences: e.g., a Wilcoxon signed-rank on the per-prompt score deltas, or a McNemar-Bowker test on the 3-way (base/LoRA/tie) contingency. Report the test, the statistic, the p-value, and an effect size.
- **Bonus:** Bootstrap the per-prompt deltas 10,000× to get a 95% CI for the (base − LoRA) win-rate difference.

### 5.3 Confidence intervals on the 28–40% data-error rate

- **What's there:** "point estimates 28–40%; single-judge, n=40" with the hard count Wilson interval quoted in §5.2.
- **What's needed:** Move the Wilson interval into §4.4.2 itself (currently it's in §5.2 Limitations, item 4). And explicitly say which of the 28/40 number is from which denominator (strict vs. lenient error definitions) — v4 is ambiguous on this.
- **If feasible:** Have a second, *independent* judge score the same 40 (or 80) responses and report (a) the inter-rater Cohen-κ or Krippendorff-α, (b) the union-error rate and the intersection-error rate, (c) the headline number from each rater individually. This is the cheapest way to discharge §5.2 item 4.

### 5.4 Power analysis for the held-out set size

- **What's there:** "50-prompt blinded base-vs-LoRA outputs".
- **What's needed:** A formal power analysis: given a target effect size (e.g., 25pp difference in error rate) and a target power (0.8), how many prompts do you need? The answer drives the §3 sample size and justifies any n you choose.
- **Bonus:** Pre-register the §3 sample size here, before running §3.

### 5.5 Multi-seed replication of the fine-tune

- **What's there:** §5.2 item 6: "We trained one adapter and evaluated one 50-prompt sample."
- **What's needed:** At minimum, two more seeds (3 total) on the same data, same hyperparameters, same hardware. Report the variance in (a) the §4.3.1 source-verified error rate, (b) the LLM-judge win rate, (c) the §3 stratified test. If 3 seeds are too expensive, do 2 and frame accordingly.
- **Cost note:** The §3.3 two-phase run took ~3–4 hours on T4 + ~1–2 hours on P100. Three seeds = ~12–18 hours of Kaggle time. Doable, but schedule the runs.

**Acceptance criteria for §5:** Every headline number in §4 and §5 has either a CI, a significance test, or an explicit "[n too small]" caveat, and the §3 stratified test has a pre-registered sample size.

**Owner:** author. **Effort:** 1–2 weeks (mostly compute and second-judge setup).

---

## 6. Multi-judge replication — discharge the single-judge concern (P1)

v4 §5.2 item 5 is honest and accurate: the same judge family scored both signals, and the factuality-audit prompts are judge-derived. The right v5 response is a second, *independent* judge.

### 6.1 What to do

- Pick a judge family that is **not** Sonnet (e.g., a Gemini-1.5-Pro or Llama-3.1-70B based judge, served by an API you have access to).
- Re-run §4.3.2 (the base vs LoRA blind preference) on the same 50 prompts with the new judge.
- Re-run §4.4.2 (the data prevalence audit) on the same 40 (or 80) responses.
- Report per-judge win rates, the Spearman correlation between judges on per-prompt scores, and a "both-judges-agree" subset analysis.
- If the judges disagree, that's also a finding — say so in §5.1.

### 6.2 What to cite

- The LLM-judge validity literature: Zheng 2023 (already cited) + Panickssery 2024 ("LLM Evaluators Recognize and Favor Their Own Generations", already cited) + at least one 2025 paper on cross-judge agreement (e.g., a recent ACL/EMNLP Findings paper on judge bias).
- A short §2.x subsection on "LLM-as-judge: known failure modes" is the right place to put this.

**Acceptance criteria:** Two independent judges; per-judge and aggregate results; inter-rater metric; explicit discussion of disagreement.

**Owner:** author. **Effort:** 1 week (mostly API costs).

---

## 7. Tighten the title, abstract, and contribution framing (P1)

### 7.1 Title

v4's title leads with "An Adapter-Handoff Recipe". The recipe is a 41.9M-parameter handoff, which is not the contribution the paper now defends. The cautionary finding is.

**Options for v5 (pick the one §1 says fits the venue):**
- "Fine-Tuning a 7B Advisor on Unverified Synthetic Data: A Negative Result with a Stratified Causal Test"
- "A Cautionary Case Study in 7B Domain Adaptation: When BERTScore Climbs and Factuality Falls"
- "From Synthetic Data to Confident Errors: A Source-Verified Audit of a 7B Study-Abroad Advisor"

Avoid re-anchoring on the recipe; the recipe is a *means*, not the result.

### 7.2 Abstract

v4's abstract is 11 sentences. Cut to ≤ 8. Lead with the result, not the recipe. Drop one of the two "honest evaluation" qualifications. Make the §3 contribution visible: "We close the gap between *supported* and *established* data attribution with a stratified test on n=X held-out prompts."

### 7.3 Contribution list (new §1.x in v5)

Replace the implicit "two things" framing with an explicit numbered list:
1. A reproducible adapter-handoff recipe across heterogeneous free-tier 16 GB GPUs.
2. A source-verified audit methodology that produces load-bearing evidence even when LLM-as-judge is known to be biased.
3. A stratified causal test (the §3 result) that establishes the data attribution.
4. A 28–40% point-estimate data-error rate with multi-judge CIs.
5. A public release of dataset, adapter, evaluation harness, and the §3 protocol so the result is re-runnable.

This list makes the contribution legible to a reviewer skimming §1.

**Acceptance criteria:** Title, abstract, and contribution list are internally consistent and consistent with §1's strategic memo.

**Owner:** author. **Effort:** 1 day.

---

## 8. Expand related work (P2)

v4 has 21 references for a 20-page paper. Five are well-known LLM/PEFT/LLM-judge papers (Brown 2020, Dettmers 2023, Hu 2021, Zheng 2023, Wolf 2020). Three cover synthetic-data failure modes (Gekhman 2024, Shumailov 2024, Alemohammad 2023). The rest are thinly spread.

**Gaps to close (P2, one paragraph each in §2):**
- **Synthetic-data quality measurement:** HaluEval, FActScore, FACTS Grounding, FreshQA, HHEM. These are the actual benchmarks that sit next to your work; you should position against them.
- **Retrieval-augmented generation as the natural counterfactual:** at least one RAG paper (Lewis 2020 is canonical; pick a 2024–2025 one for currency). This is also your §11 candidate experiment.
- **Indian higher-ed / international-student advising:** the application domain. If any empirical work exists, cite it; if not, this is itself a gap you can claim.
- **Domain-specific hallucination in education/healthcare/legal advising:** at least one paper per adjacent domain. This is what your v4 finding generalizes *to*.
- **LLM-judge validity:** beyond Zheng 2023 + Panickssery 2024, one or two 2025 papers on cross-judge agreement.

**Acceptance criteria:** §2 ends with a one-paragraph "what this paper adds" that explicitly names the gap (synthetic-data quality audit methodology on a small, free-tier-trainable domain model).

**Owner:** author. **Effort:** 2–3 days.

---

## 9. Cross-cutting corrections (P2)

A grab-bag of small but real issues a reviewer will notice.

### 9.1 Mistral license (already covered in §2.3 — duplicate here for completeness)

Fix the license text in §Declarations.

### 9.2 Gemini version

v4 says "Gemini 1.0 Pro". State the model *and* the API version date (e.g., "Gemini 1.0 Pro (May 2023) via the Generative Language API, accessed 2024-MM-DD"). A reviewer wants to reproduce the data; give them the exact target.

### 9.3 Section 3.5.2 "complementary" vs. §5.2 item 5 "not independent"

v4 §3.5.2 calls the three signals "complementary"; §5.2 item 5 says the LLM-judged signals are not independent. Both are true, but the §3.5.2 phrasing reads as if they're independent. v5 should reconcile: "complementary but not fully independent; the source-verified audit is the load-bearing signal" — in both places.

### 9.4 Future Work §5.3 item (ii) has a typo

There's a stray "ii<sup>′</sup>" inserted in the middle of the sentence. Clean it up.

### 9.5 Truncation rate of 0.96 in the model card

Not in the paper, not in the v4 release. If this is real (96% of generated responses are truncated at the 512-token limit), it materially affects the §4.3.3 numbers and the LLM-judge verdicts. Either include it in v5 §4.3 with a discussion, or remove from the model card. Do not let it sit on a HF card unmoored from the paper.

### 9.6 Caveat phrase usage (model card)

Model card reports "Caveat Phrase Usage: Base 2% → LoRA 0%." This is the *opposite* of what an advising model should do. If this is real, it's a substantive finding; surface it in v5 §5.1 (Implications). If the methodology is unclear, remove the table row.

### 9.7 Tables and figures

v4 has 5 figures, 7 tables. v5 will add at least 3 (the §3 stratified-error table, the per-topic error breakdown, the schematic pipeline figure). Check that the figure/table numbering, captions, and cross-references in the LaTeX source are consistent.

**Owner:** author. **Effort:** 1–2 days.

---

## 10. Reproducibility checklist before submission (P0 gate)

Run this verbatim before submitting v5 anywhere. Every box is a "this is what a reviewer can verify."

- [ ] `millat/StudyAbroadGPT-Dataset` card updated to v5 status; no "pending" claims left.
- [ ] `millat/StudyAbroadGPT-7B-LoRa-Kaggle` card updated to v5 status; no "pending" claims left.
- [ ] Epoch count, parameter count, and license consistent across paper, dataset card, model card.
- [ ] `github.com/codermillat/StudyAbroadGPT` is public and the cross-GPU notebooks run end-to-end.
- [ ] `github.com/codermillat/study-abroad-dataset` is public and the generation scripts run end-to-end.
- [ ] `github.com/codermillat/LoRA-Paper` evaluation harness is public, the §3 stratified-test script is included, and a re-run reproduces every v5 number.
- [ ] Every numeric claim in v5 §4 has a CI or a significance test, or is explicitly flagged `[n too small]`.
- [ ] The v5 manuscript has no `TODO` / `TBD` / `fill in` placeholders (per `superpowers:writing-plans` discipline).
- [ ] The author has read the five rejection letters and confirmed no open question in them is still unanswered in v5.

**Owner:** author. **Effort:** ≤ 1 day, but it is a hard gate.

---

## 11. Optional add-on — RAG counterfactual (P3, do only if §1 picks a venue that wants it)

If the chosen venue values the *counterfactual* over the *negative result*, add a RAG baseline:
- Same 50-prompt held-out set, same judge, same metrics.
- Two RAG variants: (i) retrieval over the released training set (testing "did fine-tuning add anything over retrieving the synthetic data?"), (ii) retrieval over a small authoritative-source corpus (e.g., UKVI + US Dept of State + a few university admissions pages, total ≤ 50 docs).
- Report BERTScore, source-verified factuality, judge win rate.

**Cost note:** building the retrieval index is fast; the expensive part is getting a small, *reliable* authoritative corpus. Don't ship this without one.

**Owner:** author. **Effort:** 1–2 weeks.

---

## 12. Sequencing — what to do in what order

1. **Week 0 (decision):** §1 venue memo. *Nothing else starts until this is written.*
2. **Week 0 (corrections, parallel):** §2 reconciliation. Pure paper/card work; no compute.
3. **Weeks 1–4 (compute-bound, parallel):** §3 stratified test + §5 multi-seed + §6 multi-judge. These can run together; the §3 protocol is the bottleneck.
4. **Weeks 1–2 (writing, parallel):** §4 R2 critique closure, §7 framing, §8 related work, §9 cross-cutting. All can be drafted while §3/§5/§6 run.
5. **Week 5:** integrate new tables/figures into the LaTeX source, run the §10 reproducibility checklist, do a self-pass with the writing-plans `Self-Review` discipline (spec coverage, placeholder scan, type/signature consistency).
6. **Week 6:** submit to the chosen venue.

If §3's stratified test slips (e.g., the source-verified audit at scale is harder than expected), the plan still works — v5 ships with §3 as a result *or* as an explicit "this is the next decisive experiment" if it's still a future-work item, but every other P0 and P1 task is done.

---

## 13. Risks and open questions

- **R1: The Discover Education R2 critique may not be the right framing for an ML venue.** If §1 picks an ML venue, R2's "real data / human survey" is less central. §4.2 already accommodates this with the pre-emption paragraph + the §3 stratified test.
- **R2: Multi-seed replication may not change the qualitative finding.** If three seeds all show the same direction, great — strengthen. If they diverge, the §3 stratified test becomes even more important, and §5.5 becomes the headline result. Either way, the plan adapts.
- **R3: The Gemini 1.0 Pro generator is the worst-case scenario.** Replicating with a stronger generator (Gemini 1.5 Pro, GPT-4o, etc.) would be a strong addition. This is *not* in v5 scope as written; add as §11+ if time permits.
- **R4: License clarity affects what you can say in v5.** Confirm Mistral-7B-Instruct-v0.3 is Apache 2.0 (it is, but verify the exact LICENSE file in the upstream repo, not just the model card). If the upstream LICENSE file has changed, v5 needs to track it.
- **R5: Five rejections in 18 months is a signal.** It's worth being honest with yourself about whether the project has reached its terminal venue. The plan above is "one more credible push". If §1's memo concludes "the paper is a finished preprint", that's also a valid outcome — just stop.

---

## 14. Definition of done for v5

- Every P0 task in this plan is closed and the evidence is on disk in the workspace.
- §10 reproducibility checklist passes with no unchecked boxes.
- A fresh reader can answer the four Discover Education R2 questions, the §5.2 limitation list, and the §5.3 future-work list, all from v5 alone.
- The dataset and model cards no longer contradict the paper.
- v5 has been submitted to *one* venue, and only one.

---

*End of v5 revision plan. Plan length: ~4,500 words. Companion documents to create during execution:*
- `docs/decisions/2026-09-02-v5-venue.md` (§1)
- `docs/audit/2026-09-02-epoch-reconciliation.md` (§2.1)
- `docs/audit/2026-09-02-param-count.md` (§2.2)
- `docs/analysis-plans/2026-09-02-stratified-causal-test.md` (§3.5)
- `docs/human-eval/2026-09-02-spot-check-protocol.md` (§4.2, if used)
