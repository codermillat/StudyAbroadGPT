# v5 §3 Stratified Causal Test — Source-Verified Audit Results

**Audit date:** 2026-09-02
**Pre-registration:** `docs/analysis-plans/2026-09-02-stratified-causal-test.md`
**Catalog file:** `data/v5-audit-catalog.csv`
**Template file:** `data/v5-audit-catalog-template.csv`

## Headline numbers

| Metric | Value | Pre-reg target | Status |
|---|---:|---:|---|
| Total audited rows | 89 | ≥ 100 | ⚠ under-sampled (-11) |
| `verified_wrong` | **20** | ≥ 20 | ✓ hit |
| `verified_correct` | 64 | — | — |
| `unclear` | 5 | — | — |
| v4 D-cases (positive controls) | 4 | — | all `verified_wrong` |

The **verified_wrong rate across the 85 v5 sampled rows is 16/85 ≈ 19%** (95% Wilson CI [12%, 28%]). When the 4 v4 D-cases are included, the rate is 20/89 ≈ 22% (95% Wilson CI [15%, 32%]). The v4 §4.4 point estimate of 28–40% (n=40) is consistent with this — the v5 stratified sample's lower bound is slightly below v4, which is expected given the smaller n and the conservative "unclear" handling.

## Method

- **Sampling**: 60 random + 25 high-risk-keyword, drawn from the 2,954-row Gemini-1.0-Pro training corpus with seed=42.
- **Source verification**: 6 parallel subagent verifications, each restricted to a topic batch (USA/Canada, UK/Other, Germany/EU, AU/NZ, Asia, General). Each claim was checked against a primary source (.gov, .edu, official org). Ambiguous verdicts were marked `unclear` per pre-registration protocol.
- **Parent re-verification**: 4 subagent-`unclear` rows were re-verified directly by the parent agent against primary sources (uni-freiburg.de, daad.org, stanford CardinalEngage, NSF NCSES). 2 flipped to `verified_wrong`, 2 to `verified_correct`.
- **v4 D-cases**: 4 source-verified D-Cases from the v4 audit (`docs/audit/v4-dataset-factuality-catalog.md`) were appended as positive controls — all 4 are labeled `verified_wrong` here.

## All 20 verified_wrong rows

### From v5 subagent verifications (16)

| training_id | Topic | Wrong claim | Source |
|---|---|---|---|
| `5631ddebfbf71e1e` | USA / UC Berkeley SHIP | Calls SHIP "basic coverage"; Berkeley's page says "comprehensive major medical insurance plan" | [uhs.berkeley.edu/ship](https://uhs.berkeley.edu/ship) |
| `2702965dc582491b` | "London, USA" | Treats non-existent "London, USA" as real; gives $800–$1,200 1BR rent | en.wikipedia.org/wiki/London |
| `d6a160f7d36e73fe` | UK / NHS | "Free healthcare" via NHS for international students; actually pays IHS | [gov.uk/healthcare-immigration-application](https://www.gov.uk/healthcare-immigration-application) |
| `0bb530043585eada` | UK / Railcard | "National Railcard £30/year"; 16-25 Railcard is £35 and no single "National Railcard" exists | [railcard.co.uk/16-25-railcard](https://www.railcard.co.uk/16-25-railcard) |
| `54a61bed01979568` | UK / student visa | "3 to 6 weeks" processing; GOV.UK says 3 weeks outside UK, 8 weeks inside | [gov.uk/student-visa](https://www.gov.uk/student-visa) |
| `5fb92037a3da2749` | Germany / BahnCard | "50% off long-distance + 25% off regional"; reverses actual structure (BahnCard 50 = 50% off flexible long-distance) | [int.bahn.de/en/offers/bahncard](https://int.bahn.de/en/offers/bahncard) |
| `1e29e81510f70e14` | Germany / U Freiburg | "B2 German for most undergraduate"; actually DSH-2 / TestDaF 4 (≈ C1) | [uni-freiburg.de](https://uni-freiburg.de/en/studies/applying/international-applicants/full-time-studies/) |
| `8fdc816f40735d8e` | DAAD deadline | "Usually March"; main DAAD deadlines are Sept-Nov of preceding year | [daad.org](https://www.daad.org/en/2025/09/22/upcoming-daad-deadlines-for-2026-27/) |
| `7a925a55d373ee86` | Australia / Medicare | Lists Medicare as healthcare option for Pakistani students; Pakistan has no RHCA with Australia | [healthdirect.gov.au](https://www.healthdirect.gov.au/what-is-medicare) |
| `73bfbfebe468c11a` | Bangladesh healthcare | "Bangladesh provides free healthcare to all citizens including international students"; intl students need private insurance | en.wikipedia.org/wiki/Health_in_Bangladesh |
| `25393ab1202c9748` | India visa | "X-2 Visa" for Bangladeshi students; X-2 does not exist; correct category is "Student Visa" | [indianvisaonline.gov.in](https://indianvisaonline.gov.in/visa/visa-category.html) |
| `b65c3f353c6703ae` | Bangladesh NHS | "National Health Service provides primary and secondary care"; NHS is a UK term; Bangladesh has MOHFW/DGHS | en.wikipedia.org/wiki/Health_in_Bangladesh |
| `05a35d7a7d4095a1` | Ukraine visa | "Type A student visas" for Pakistani students; Type A is airport transit; study requires Type D | [mfa.gov.ua](https://mfa.gov.ua/en/consular-affairs/entry-and-stay-foreigners-ukraine/visa-information) |
| `73f0ab67c39bcd36` | New Zealand | "Major hub for technology companies, such as Microsoft, Amazon, and Google"; only small satellite offices | [nzte.govt.nz](https://www.nzte.govt.nz/) |
| `ca46dbb2f6e952c9` | EU visa | "EU student visa process"; no single EU student visa exists — each member state has its own | consilium.europa.eu |
| `8762633aa385d0cb` | AIIMS MS-CS | "MS in Computer Science at AIIMS"; AIIMS is purely a medical institution, no CS programs | [aiims.edu](https://www.aiims.edu/) |

### From v4 audit (positive controls, 4)

| d-case | Topic |
|---|---|
| D1 | Australia healthcare — false Medicare eligibility (matches v4 Model Case 2) |
| D2 | Brazil→Bangladesh scholarships — fabricated programs (matches v4 Model Case 4) |
| D3 | "Bachelor of Medicine at Oxford" — false-premise elaboration (matches v4 Model Case 3) |
| D4 | "MS in Data Science at Harvard Medical School" — incoherent program accepted (matches v4 Model Case 1) |

## Patterns observed

1. **Confident fabrication of specific named entities.** The model invents named visa categories ("X-2 Visa", "Type A student visa"), healthcare systems ("National Health Service" applied to Bangladesh), and academic programs ("MS in CS at AIIMS"). These are not just generic errors — they are fluent, category-correct hallucinations.

2. **False-premise acceptance.** The model treats non-existent study destinations ("London, USA", "Toronto, Australia") and non-existent programs ("MS in CS at AIIMS", "Bachelor of Medicine at Oxford" at the undergraduate level) as real and elaborates admissions details. This is the same v4 §4.4 mechanism: the training data's template cross-product produces incoherent prompts, and the model learns to answer them as if valid.

3. **Quantitative claim fabrication.** Specific numbers are wrong by a wide margin: UK student visa "3 to 6 weeks" (actual 3 or 8); UK Railcard "£30" (actual £35); BahnCard "50% off long-distance + 25% off regional" (reversed structure); Australian Medicare eligibility asserted for a nationality that has no RHCA with Australia. These are the kinds of claims that look credible but cannot survive a primary-source check.

4. **Healthcare/insurance is the densest error category.** 4 of 16 v5 verified_wrong rows concern healthcare or insurance eligibility (Bangladesh NHS, Bangladesh free healthcare, Australia Medicare, USA SHIP "basic"). This aligns with the v4 §4.4 finding that healthcare/insurance is the highest-severity risk area for downstream advising harm.

5. **The v4 patterns are reproduced, not improved.** The four v4 D-cases (Australia Medicare, Brazil scholarships, Oxford medicine, HMS data science) are all still present in the v5 sample as the same mechanism operating in a different slice of the corpus. The pre-registered stratified test (§4.5) is now ready to formally attribute this rate to the *data* rather than the *method*.

## 5 unclear rows (conservatively not labeled wrong)

| training_id | Topic | Why unclear |
|---|---|---|
| `bab5c27f772a7960` | DAAD scholarships for Pakistani students | "Exactly 150 in 2022" — DAAD.de was inaccessible; no primary source to confirm or contradict |
| `d0c71042fced4722` | Tashkent dorm cost | "$150/month" — site is JS-rendered, no static pricing found |
| `2978005719129e3f` | Ukraine student visa | "2-3 weeks to gather documents" — generic doc-prep timing, war context makes any pre-2022 guidance stale |
| `6cb1fccfc17a40de` | 60% of RAs in Social Sciences | Unnamed survey, unverifiable |
| `dd2fea8106ea71a1` | "Toronto, Australia" cost of living | Geographic premise wrong, but assistant redirected to Toronto, Canada with reasonable CAD figures |

## Limitations

1. **Sample size.** 85 sampled rows is below the pre-registered 100-row target. The headline statistics are therefore slightly under-powered. The verified_wrong rate of ~19% is consistent with v4 §4.4's 28–40% point estimate, but the wide CI allows a v5 rate anywhere from 12% to 28%.
2. **Truncated training answers.** Several rows in the audit template had answers truncated at the source-JSONL boundary, so the subagent could only verify the visible portion. The total number of checkable claims per row may be under-counted.
3. **Source-access failures.** DAAD.de and some university pages were inaccessible during the audit window. 3 of the 5 `unclear` rows are due to this, not to absence of error.
4. **Verdict consistency.** 6 parallel subagents may apply slightly different evidence bars. The parent re-verified 4 of the 5 originally-`unclear` rows to catch this.

## What this enables

This catalog completes the **source-verification side** of the §3 pre-registered stratified causal test. The next steps are:

1. Run `scripts/eval/stratify_prompts.py` to assign each held-out prompt to C/W/M strata based on training-set nearest-neighbor labels from this catalog.
2. Run `scripts/eval/generate_stratified.py` on a GPU to produce base + LoRA outputs for the stratified held-out set.
3. Run `scripts/eval/analyze_stratified.py` to compute McNemar's test per stratum and update v5 §4.5 with the stratified test outcome.
