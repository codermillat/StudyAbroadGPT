# v5 §4.5 Stratified Causal Test — Held-Out Source-Verified Results

**Run date:** 2026-09-03
**Pre-registration:** `docs/analysis-plans/2026-09-02-stratified-causal-test.md` (frozen 2026-09-02)
**Analysis script:** `scripts/eval/analyze_stratified.py`
**Input data:** `data/v5-audit-results.csv` (30 rows = 15 C + 14 W + 1 M)
**Output tables/figures:** `data/v5-analysis/per_stratum_results.csv`, `data/v5-analysis/per_prompt_results.csv`, `data/v5-analysis/excluded_prompts.csv`, `data/v5-analysis/summary.txt`
**Merge summary:** `docs/audit/v5-stratified-merge-summary.md`

---

## Headline

| Statistic | Value |
|---|---|
| Total stratifiable prompts (C/W/M) | 30 (15 C, 14 W, 1 M) |
| Excluded as `unclear` (1 per stratum) | 2 (prompt 7 in W, prompt 49 in C) |
| Analyzable pairs (McNemar denominator) | 28 (14 C, 13 W, 1 M) |
| Power verdict (§4.2) | **INSUFFICIENT** (n_C, n_W < 15) |
| Decision rule (§6.4) outcome | LoRA worse in BOTH strata → ``uniformly worse'' branch fires; we **do not** interpret this strongly (under-powered) |

---

## Stratum-level 2×2 and McNemar

| Stratum | n | a (both correct) | b (base W, LoRA C) | c (base C, LoRA W) | d (both W) | LoRA err | Base err | Diff (L−B) | McNemar p (CC) | OR (c/b) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **C (clean)**    | 14 | 12 | 0 | 2 | 0 | 14.3% | 0%   | +14.3pp | 0.4795 | ∞ |
| **W (wrong)**    | 13 |  6 | 1 | 2 | 4 | 46.2% | 38.5% | +7.7pp  | 1.0000 | 2.0 |
| **M (mixed)**    |  1 |  1 | 0 | 0 | 0 | 0%   | 0%   | 0pp     | n/a    | n/a |

Without continuity correction: C p = 0.250, W p = 0.564.

---

## Per-prompt labels (full table in `data/v5-audit-results.csv`)

- **Stratum C, LoRA wrong (2 of 14):**
  - **prompt 11** (Australian healthcare): LoRA falsely claims international students become Medicare-eligible after 6 months; OSHC remains compulsory per `privatehealth.gov.au`.
  - **prompt 19** (UK student finance): LoRA claims maintenance loans are non-means-tested; GOV.UK says only tuition-fee loans are non-means-tested.
- **Stratum W, LoRA worse than base (3 of 13):**
  - **prompt 5** (Pakistani-student Canada scholarships): base=correct; LoRA fabricates "Canada-Pakistan Education Scholarship Program (CPESP)" and misattributes Humphrey Fellowships to Canada.
  - **prompt 11** (not in W; this is the C-stratum case above).
  - **prompt 14** (MIT admissions): both wrong (subject tests claim; rec count); LoRA additionally understates MIT's letter requirements.
  - **prompt 17** (UK student visa): both wrong (calls it "Tier 4" — replaced in 2020; wrong processing-time claim).
  - **prompt 22** (Chinese-student UK scholarships): base wrong (Marshall is for Americans); LoRA correct. This is the only discordant pair where **base is wrong and LoRA is right** in W.
  - **prompt 34** (Brazil→Bangladesh scholarships): base correct; LoRA fabricates 4 country-specific scholarship programs.
  - **prompt 37** (Stanford MBBS): both wrong (Stanford doesn't offer undergraduate MBBS).
- **Stratum C, LoRA correct on the 12 remaining prompts:** all 12 are either generic advising advice or correctly named programs/scholarships.
- **Stratum W, LoRA correct on the 6 prompts where both are correct:** the model handles them correctly, consistent with the v4 §4.4 finding that the model's errors concentrate on policy-sensitive specifics, not generic content.

---

## Excluded prompts (2)

| prompt_id | stratum | reason |
|---|---|---|
| 7  | W | LoRA mentions a "DU Admission Test (DUAT)" acronym and faculty-specific GPA cutoffs that could not be confirmed or refuted from the official `du.ac.bd` (procedure page reports "Content is being updated"). |
| 49 | C | LoRA claims a "DuPont Tennis Stadium" with 12 outdoor courts and a pro shop at MIT — MIT has DuPont Tennis Courts but the "Stadium + pro shop" framing could not be confirmed within the 2-search budget. |

Both exclusions are recorded in `data/v5-analysis/excluded_prompts.csv` and reduce the analyzable sample from 30 to 28.

---

## Decision-rule outcome (§6.4)

The pre-registered rule says:
> if LoRA error rate exceeds base only in W → data attribution is **established**;
> if both strata show LoRA > base → attribution weakens to "uniformly worse."

Mechanically, both strata show LoRA > base (+14.3pp in C, +7.7pp in W), so the rule fires the **"uniformly worse"** branch.

We **do not interpret this strongly**:
- The C-stratum effect is 2 of 14 prompts (and both are policy errors the base handles correctly — they are not stochastic noise).
- The W-stratum discordant-pair count is 3, giving McNemar p = 0.56 (no CC) or 1.0 (with CC).
- The pre-registration's $n\!\ge\!30$ "indicative" and $n\!\ge\!60$ "adequately powered" thresholds are not met; with the current sample, even a 25pp effect cannot be detected at 50% power.

The test is therefore reported as **direction-consistent but under-powered**. The data-attribution claim remains **supported, not established**. The audit catalog (`data/v5-audit-catalog.csv`), stratified sample (`data/v5-stratified-prompts.csv`), source-verified outputs (`data/v5-audit-results.csv`), analysis script (`scripts/eval/analyze_stratified.py`), and merge helper (`scripts/eval/merge_stratified_audits.py`) are released so a follow-up round with a larger audit catalog can re-run the test and discharge §6.4.

---

## v4 D-case reproduction

All 4 v4 §4.4 D-cases are in the v5 stratified sample. Their v5 source-verification:

| prompt_id | topic (v4 D-case) | stratum (v5) | base v5 | lora v5 | v4 verdict | v5 verdict |
|---:|---|---|---|---|---|
| 2  | HMS standardized testing | W | wrong | wrong | LoRA wrong | reproduced (LoRA wrong on GRE; base also wrong on a fabricated COVID MCAT-suspension claim) |
| 11 | AU Medicare | C | correct | wrong | LoRA wrong | reproduced |
| 34 | BR→BD scholarships | W | correct | wrong | LoRA wrong | reproduced |
| 37 | Stanford MBBS | W | wrong | wrong | LoRA wrong | reproduced |

3 of 4 reproduce as LoRA wrong; prompt 2 also has a base-side error (the COVID MCAT-suspension claim was fabricated by the base in v4 — not a v5-introduced error). This is consistent with the v4 §4.4 finding that the LoRA inherits and amplifies the policy-specific failure modes present in the training data.

---

## File map

| File | Purpose |
|---|---|
| `data/v5-audit-results.csv` | Per-prompt base/LoRA labels and source URLs (input to analyze) |
| `data/v5-audit-results.csv.template` | Empty template for re-running with a different audit |
| `data/v5-analysis/per_stratum_results.csv` | The 2×2 + McNemar per stratum (Table 4 in the paper) |
| `data/v5-analysis/per_prompt_results.csv` | One row per stratified prompt with both labels |
| `data/v5-analysis/excluded_prompts.csv` | The 2 unclear exclusions |
| `data/v5-analysis/summary.txt` | Human-readable summary printed by the script |
| `data/v5-stratified-prompts.csv` | Step 1 output: 50 prompts → 30 C/W/M + 20 excluded |
| `data/v5-audit-catalog.csv` | Step 2 input: 149 audited training neighbors (43 verified-wrong) |
| `scripts/eval/stratify_prompts.py` | Step 1: C/W/M stratification |
| `scripts/eval/audit_training_neighbors.py` | Step 2: audit template generator |
| `scripts/eval/generate_stratified.py` | Step 3: base + LoRA generation (was v5 GPU step) |
| `scripts/eval/analyze_stratified.py` | Step 4: McNemar + bootstrap CIs |
| `scripts/eval/merge_stratified_audits.py` | Helper: merge 6 batch JSONs into `data/v5-audit-results.csv` |
| `/tmp/v5_held_out_bundles/` | Working dir for per-prompt bundles and 6 subagent result JSONs |
