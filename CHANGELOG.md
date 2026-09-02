# Changelog — StudyAbroadGPT-1

This is a project-level changelog for the v4 → v5 transition of the
arXiv:2504.15610 paper and its supporting artifacts. Reviewers and
collaborators can use this to understand what changed between versions
without reading every file.

The paper itself (v4) is on arXiv: https://arxiv.org/abs/2504.15610
The v5 manuscript draft is `paper/v5-draft.tex` in this repo (anonymized
for the NAACL 2027 BEA Workshop submission, deadline 2026-10-15).

---

## v5 (anonymized submission draft, 2026-09-02) — in progress

### Manuscript changes vs. v4

- **Anonymized for double-blind.** Author block, ORCID, email,
  affiliation, GitHub and HF URLs replaced with placeholders. Live
  v4 author info retained in `paper/main.tex` (the v4 source).
- **Compressed from 19 → ~8 pages of main text.** Sections §3.1
  (dataset), §3.2 (model config), §4.1 (training dynamics), and §4.2
  (feasibility) are condensed; §4.3 (reliability evaluation) and §4.4
  (data audit) keep full length because they are the contribution.
- **Added new statistical tests in §4.3:**
  - Fisher's exact on the 4-vs-0 source-verified errors: one-sided
    $p{=}0.060$ (under-powered at $n{=}18$ divergent prompts).
  - McNemar-Bowker on the 3-way preference contingency
    (base / LoRA / tie): $\chi^2(2){=}9.3$, $p{=}0.0095$.
- **Added new §4.5: Pre-Registered Stratified Test (Pending).** The
  §3 stratified causal test from `docs/analysis-plans/2026-09-02-stratified-causal-test.md`
  is integrated into the manuscript as a §4.5 paragraph with explicit
  citation of the pre-registration file. The test is "pre-registered;
  results forthcoming" so the manuscript is submittable before the
  test runs; deviations are logged in §9 Amendments of the
  pre-registration.
- **Added §2.4 "Factuality Evaluation Beyond Reference-Based Metrics"**
  with new references: HaluEval (Li et al. 2023), FActScore (Min et al.
  2023), FreshQA (Vu et al. 2023).
- **Added §2.5 "RAG and the Counterfactual"** with Lewis 2020 and
  Gao 2024 RAG survey; defers the RAG baseline to v5+ future work.
- **Renumbered the AI Applications section to §2.6.**
- **Added §Declarations "Data and Code Availability"** that cites the
  v4-reconciled HF card commit SHAs (`3f91dd0` dataset, `687758d`
  model).
- **Added §Declarations "Ethics and Use of Generative AI"** that
  corrects the v1/v2-era "Mistral Research License" wording to
  "Apache 2.0" (the actual upstream Mistral-7B-Instruct-v0.3 license).

### Repository changes vs. the pre-v5 layout

- **Project structure reorganized.** New layout:
  ```
  paper/           v4 source (main.tex) + v5 draft (v5-draft.tex)
  legacy/          v1 (paper-v1.md) and v2/v3 (paper-v2-v3.md) drafts
  data/            v4 ground truth: adapter config, 50-prompt eval set
  docs/audit/      v4 source-verified factuality catalogs
  docs/eval/       v4 NLP metrics, LLM-judge, summaries
  docs/reviews/    journal rejection, response, integrity, chapter plan
  docs/analysis-plans/  the §3 pre-registration (frozen 2026-09-02)
  docs/superpowers/plans/  the v5 revision plan
  docs/hf-cards/   the v4-reconciled HF card content (matches HF Hub)
  docs/decisions/  the v5 venue decision memo (anonymized)
  scripts/eval/    the v4 analysis harness + 4 new §3 scripts
  LoRA Paper/      local working directory (gitignored)
  ```
- **Old files moved to `legacy/`.** `paper.md` → `legacy/paper-v1.md`;
  `paper_v2.md` → `legacy/paper-v2-v3.md`. Both via `git mv` so the
  rename is detected.
- **.gitignore expanded.** Now covers `LoRA Paper/`, `.obsidian/`,
  `.agents/`, `.claude/`, `study-abroad-dataset/` (broken submodule),
  all LaTeX build artifacts, `paper/*.pdf`, and standard Python/secret
  hygiene. The previous `.gitignore` was a single line.
- **HF Hub cards reconciled to v4.** The dataset card and model card
  were both updated to match the v4 paper: 3 epochs (not 4), 41.9M
  trainable parameters (not 4.7M), Apache 2.0 (not Mistral Research
  License), source-verified factuality audit complete (not "pending"),
  with the v4 §4.3 results table on the model card and the v4 §4.4
  catalog references on the dataset card.
- **README.md rewritten.** The previous v1-era engineering report
  README (which led with retracted claims) is replaced with a v4-aligned
  README documenting the new project structure, the §3 pipeline, the
  headline results, the reproduction commands, and the citation.

### §3 stratified causal test (the v5 contribution)

Pre-registered on 2026-09-02 at
`docs/analysis-plans/2026-09-02-stratified-causal-test.md`. Implements
the v4 §5.3(ii') "decisive method-vs-data test" — comparing base and
LoRA error rates on prompts whose training-set nearest neighbors are
source-verified correct vs. wrong. The test converts the v4 "data is
sufficient" claim into an "established" claim.

- **Pre-registration file** (`docs/analysis-plans/2026-09-02-stratified-causal-test.md`):
  14 KB, 10 sections. Frozen analysis plan with hypothesis,
  stratification procedure, sample-size targets, statistical methods
  (McNemar's with continuity correction, bootstrap 95% CIs, Cochran's Q
  for the interaction), and pre-registered decision rules for what
  the v5 manuscript reports.
- **4 analysis scripts** in `scripts/eval/`:
  - `stratify_prompts.py` — Step 1: assign held-out prompts to C/W/M
    strata based on training-neighbor audit labels.
  - `audit_training_neighbors.py` — Step 2: generate a fillable audit
    template CSV with random + keyword-targeted sampling of the
    training corpus.
  - `generate_stratified.py` — Step 3: run base and LoRA on the
    stratified prompt set with the v4 §3.5.1 generation settings.
  - `analyze_stratified.py` — Step 4: McNemar's test, bootstrap CIs,
    forest plot, and the pre-registered §4.2 power verdict.

---

## v4 (arXiv:2504.15610v4, 2026-06-14) — published

Major revision and repositioning. The v1–v3 paper was titled "A
LoRA-Based Approach to Fine-Tuning LLMs for Educational Guidance in
Resource-Constrained Settings" and contained two claims that v4
withdraws:

1. **Withdrawn: the "quantization-boundary" finding.** Earlier versions
   attributed a loss reduction to a quantization-related effect at a
   training boundary. The v4 re-examination showed the loss curve
   was still declining at end of epoch one, quantization was held
   constant across the claimed boundary, and the additional reduction
   was fully explained by further epochs and a larger effective batch.
2. **Corrected: cross-GPU state transfer.** Earlier versions implied
   that optimizer and scheduler state were carried across the GPU
   handoff. The released code transfers **only** the LoRA adapter;
   the optimizer is re-initialized on the second GPU.

v4 reframes the contribution around (a) a reproducible free-tier
cross-GPU adapter-handoff recipe and (b) an honest held-out
reliability evaluation. Adds:

- A 50-prompt blinded held-out comparison against the un-fine-tuned
  base, with **four source-verified LoRA factual errors** (HMS testing,
  Australian healthcare, "Bachelor of Medicine at Stanford," Brazil→BD
  scholarships) vs. zero for the base on the same prompts.
- A blind LLM-as-judge preference: 46% base vs 18% LoRA vs 36% tie.
- Reference-based metrics: SacreBLEU 5.71→9.05, ROUGE-L F1 +0.019
  [+0.010, +0.028], BERTScore F1 +0.063 [+0.047, +0.078].
- A direct audit of the training data: 27.5% hard-error rate
  (Wilson 95% CI [16%, 43%]), 40% inclusive-error rate (CI [26%, 55%]),
  on a random sample of 40 training answers scored by one LLM judge.
- A causal match: each of the 4 audited model errors is present in
  the Gemini-1.0-Pro training answers, isolating the failure to the
  synthetic-data pipeline rather than the fine-tuning method.
- A caveat-phrase-usage regression: base 2.0% → LoRA 0.0% — the
  fine-tuned model **dropped its safety hedges** compared to base,
  a substantive concern for an advising model.
- 9 limitations and 5 future-work items, including the §5.3(ii')
  decisive method-vs-data test (now the v5 §3 work).

---

## v1–v3 (April–December 2025) — superseded, retained in `legacy/`

The original "LoRA-Based Approach" preprint, which made the
"quantization-boundary" and "cross-GPU state transfer" claims later
withdrawn. v1–v3 are preserved at `legacy/paper-v1.md` and
`legacy/paper-v2-v3.md` for the historical record. **Do not cite v1–v3.**
The v4 paper's "Changes from Earlier Versions" block documents the
retraction explicitly.

---

## Other notable changes (cross-version)

- **Git author identity on commits.** The pre-registration file
  `docs/analysis-plans/2026-09-02-stratified-causal-test.md` is
  time-stamped by git commit. The author identity is visible in
  `git log` for reviewers who care. For double-blind integrity, a
  separate, anonymized, time-stamped copy of the pre-registration
  will be deposited to a public service (Zenodo or Gist) before
  the Oct 15 BEA submission deadline. See the v5 plan for the
  exact procedure.
- **Working directory.** `LoRA Paper/` is the local working
  directory for the v4 work and is gitignored. It contains the
  Hugging Face `linked_repos/` clones (StudyAbroadGPT,
  StudyAbroadGPT-Dataset, StudyAbroadGPT-7B-LoRa-Kaggle, and
  study-abroad-dataset) used during the v4 evaluation. The raw
  training data (`study_abroad_dataset.jsonl`, 18 MB) lives there
  because the HF dataset is released in Parquet form and the raw
  JSONL is needed for the v5 §3 stratified test.
