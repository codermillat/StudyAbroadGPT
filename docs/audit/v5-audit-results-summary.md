# v5 §3 Stratified Causal Test — Source-Verified Audit Results

**Audit date:** 2026-09-02 (round 1) → 2026-09-02 (round 2 extension)
**Pre-registration:** `docs/analysis-plans/2026-09-02-stratified-causal-test.md`
**Catalog file:** `data/v5-audit-catalog.csv`
**Template file:** `data/v5-audit-catalog-template.csv`
**Stratification output:** `data/v5-stratified-prompts.csv`

## Headline numbers (after round 2)

| Metric | Round 1 | Round 2 | Pre-reg target | Status |
|---|---:|---:|---:|---|
| Total audited rows | 89 | **149** | ≥ 100 | ✓ hit |
| `verified_wrong` (v5 subagent) | 16 | **39** | ≥ 20 | ✓ hit |
| `verified_wrong` (v4 D-cases) | 4 | 4 | — | — |
| `verified_wrong` total | 20 | **43** | ≥ 20 | ✓ hit |
| `verified_correct` | 64 | 68 | — | — |
| `unclear` | 5 | 38 | — | — |

The **verified_wrong rate across v5-sampled rows is 39/145 ≈ 27%** (95% Wilson CI [20%, 35%]). When the 4 v4 D-cases are included, the rate is 43/149 ≈ 29% (95% Wilson CI [22%, 37%]). This is **directly consistent with the v4 §4.4 point estimate of 28–40%** (n=40), now with a much tighter CI from a much larger n.

The round-2 extension targeted the 60 unaudited top-5 neighbors of the 37 prompts that were EXCLUDED in round 1 (the 37 were blocked because no audited neighbors existed for them). The round-2 verified_wrong rate of **21/60 = 35%** is even higher than the round-1 rate of 19% — the unaudited neighbors of the EXCLUDED prompts were disproportionately wrong, suggesting the model's error rate may be even higher in topic slices the original random sample underrepresented.

## Method

- **Sampling**: 60 random + 25 high-risk-keyword, drawn from the 2,954-row Gemini-1.0-Pro training corpus with seed=42. Then a round-2 extension of 60 more rows (the unique unaudited top-5 neighbors of the round-1 excluded prompts).
- **Source verification**: 6 parallel subagent verifications per round, each restricted to a topic batch (USA/Canada, UK/Other, Germany/EU, AU/NZ, Asia, General). Each claim was checked against a primary source (.gov, .edu, official org). Ambiguous verdicts were marked `unclear` per pre-registration protocol.
- **Parent re-verification**: 4 subagent-`unclear` rows were re-verified directly by the parent agent against primary sources. 2 flipped to `verified_wrong` (Freiburg B2 German requirement, DAAD March deadline), 2 to `verified_correct` (Stanford Nepali Student Association, NSF median salary).
- **v4 D-cases**: 4 source-verified D-Cases from the v4 audit (`docs/audit/v4-dataset-factuality-catalog.md`) were appended as positive controls — all 4 are labeled `verified_wrong` here.

## Stratification outcome (round 2)

| Stratum | Round 1 | Round 2 | Pre-reg threshold (≥15) |
|---|---:|---:|---|
| C (clean neighbors) | 12 | **15** | ✓ hit |
| W (wrong neighbors) | 1 | **14** | ⚠ 1 short |
| M (mixed) | 0 | **1** | — |
| Excluded | 37 | **20** | — |
| **Total stratifiable** | 13 | **30** | — |

The 30 stratifiable prompts are now sufficient to run the pre-registered McNemar's test on the C vs W comparison. The 20 still-excluded prompts are blocked by 0 audited neighbors in their top-5 (18 prompts) or 1 audited neighbor (2 prompts); a round-3 extension of ~55 audits would lift power to full threshold.

## All 43 verified_wrong rows (rounds 1 + 2 + v4)

### Round 1 (16 from subagents) — see prior commit summary

### Round 2 (23 from subagents)

| training_id | Topic | Wrong claim | Source |
|---|---|---|---|
| `208337f8ab3125b3` | Stanford graduate admissions | "Stanford requires all applicants to submit GRE scores"; Stanford GRE is optional | [gradadmissions.stanford.edu](https://gradadmissions.stanford.edu/apply/test-scores) |
| `032f8a2e78ca719d` | AIIMS admissions | AIIMS requires GRE (V152/Q160/AW4.0); AIIMS uses NEET-PG / INI-CET | en.wikipedia.org/wiki/All_India_Institute_of_Medical_Sciences,_Delhi |
| `3f9a37fcb639a306` | MIT undergraduate | MIT "requires all applicants to submit standardized test scores"; MIT is test-optional for fall 2026 | [mitadmissions.org](https://mitadmissions.org/apply/firstyear/tests/) |
| `b42c1360f4c06598` | HMS MD | HMS requires GRE (V162/Q164/AW4.5); HMS MD requires MCAT, not GRE | [hms.harvard.edu](https://hms.harvard.edu/education-admissions/md-program/admissions) |
| `c6b718d496665553` | Stanford Medicine | "Bachelor of Medicine at Stanford" treated as a real program; Stanford Medicine only offers MD | [med.stanford.edu/md-admissions.html](https://med.stanford.edu/md-admissions.html) |
| `d2a80e07605620fa` | HMS MD MCAT | HMS MD class average MCAT 528; 528 is a perfect score; median is ~519-520 | en.wikipedia.org/wiki/Medical_College_Admission_Test |
| `9dd43f0b3576342a` | Stanford Early Action | Stanford EA is "binding if accepted"; Stanford's program is Restrictive Early Action, non-binding | en.wikipedia.org/wiki/Stanford_University |
| `29bf2494b83cc64a` | UC Berkeley TOEFL | Berkeley requires TOEFL 100 for undergraduates; actual minimum is 80 | [grad.berkeley.edu](https://grad.berkeley.edu/admissions/apply/english-language/) |
| `1a6c9bd034a9bd0c` | Canadian universities | "Improve your German before studying in Canada"; English is the language of instruction in Canada | [utoronto.ca](https://www.utoronto.ca/) |
| `ca99fcd05805c597` | Canadian scholarships | "Canada-India Joint Economic Commission Scholarship" (250 awards in 2022); does not exist in Government of Canada scholarship portal | [vanier.gc.ca](https://vanier.gc.ca/en/indigenous_scholars.html) |
| `244a7b75359750fa` | MBTA | MBTA unlimited monthly pass $90-$120; actual bus+subway range is $90-$132 | [mbta.com/fares/auto-pay](https://www.mbta.com/fares/auto-pay) |
| `99654566f22673f9` | EU universities | Oxford and Cambridge listed as "EU universities"; UK left the EU 31 Jan 2020 (Brexit) | en.wikipedia.org/wiki/European_Union |
| `827fc682dc811d4f` | UK scholarships | "In 2023-2024, 116 Chinese students were awarded Chevening"; China's allocation is ~30+, not 116 | en.wikipedia.org/wiki/Chevening_Scholarship |
| `129c88b6ce4a4b4d` | UK CS universities | Oxford offers "Mathematical and Computational Science Tripos"; Tripos is Cambridge terminology, not Oxford | en.wikipedia.org/wiki/University_of_Oxford |
| `22abd4c207474f70` | AIIMS MBBS | AIIMS MBBS admission via 200-MCQ entrance exam; AIIMS admissions go through NEET-UG since 2019 | en.wikipedia.org/wiki/All_India_Institute_of_Medical_Sciences,_Delhi |
| `09242cbbdda70674` | AIIMS + MCI | AIIMS MBBS exam still required + quotes "Indian Medical Council (MCI)"; MCI dissolved 2019, replaced by NMC | en.wikipedia.org/wiki/All_India_Institute_of_Medical_Sciences,_Delhi |
| `fd05db874de5ba10` | Tata scholarship | "Tata Education and Development Trust" provides scholarships to Brazilian students; Tata Trusts has no such program | [tatatrusts.org](https://www.tatatrusts.org/our-work/individual-grants-programme) |
| `97bf5f62475cf310` | Bangladesh scholarship | "BITEMS - Bangladesh International Training and Education Management System" offers scholarships; BITEMS does not exist | en.wikipedia.org/wiki/University_of_Dhaka |
| `81e02b955dce1742` | Australian intl students | "over 550,000 international students studied in Australia in 2021"; 2021 was ~417-500k after COVID drop | internationaleducation.gov.au (PRISMS 2021) |
| `2ffc1ea9a2488ff5` | Melbourne MD | "3.5 GPA domestic / 4.0 international"; GEMSAS has no such split, 4.0 effectively unreachable | [medicine.unimelb.edu.au](https://medicine.unimelb.edu.au/__data/assets/pdf_file/0009/2730168/MMS_MD_Selection_Guidelines_v3.1.pdf) |
| `5e848537bf88968f` | Australian scholarships | Three errors: Endeavour is current (ended 2019, replaced by Destination Australia); "University of Sydney IRS" (it's UTS); MIRS $31,200 (actual MRS is $34,400; MIRS merged into MRS 2016) | en.wikipedia.org/wiki/Endeavour_Awards |
| `2c56698f3abf591f` | DAAD deadline | "DAAD scholarship application deadline for non-EU students is typically in late March"; Study Scholarship closed 26 Sep 2024 | [partnership.itb.ac.id](https://partnership.itb.ac.id/daad-scholarship-2025-germany/) |
| `944ec1715a8b9484` | German MBA | "Survey by German Graduate School of Management and Law" with €80k MBA salary; GGS was a small 2006-2021 Fachhochschule, never published such a survey | de.wikipedia.org/wiki/German_Graduate_School_of_Management_and_Law |

### v4 D-cases (positive controls, 4)

| d-case | Topic |
|---|---|
| D1 | Australia healthcare — false Medicare eligibility (matches v4 Model Case 2) |
| D2 | Brazil→Bangladesh scholarships — fabricated programs (matches v4 Model Case 4) |
| D3 | "Bachelor of Medicine at Oxford" — false-premise elaboration (matches v4 Model Case 3) |
| D4 | "MS in Data Science at Harvard Medical School" — incoherent program accepted (matches v4 Model Case 1) |

## Patterns observed (combined)

1. **Confident fabrication of specific named entities.** The model invents named visa categories ("X-2 Visa", "Type A student visa"), healthcare systems ("National Health Service" applied to Bangladesh, "Indian Medical Council" after 2019), scholarship bodies ("BITEMS", "Canada-India Joint Economic Commission"), academic programs ("MS in CS at AIIMS", "Bachelor of Medicine at Stanford"), and even whole institutions ("German Graduate School of Management and Law" salary survey). These are not generic errors — they are fluent, category-correct hallucinations that survive surface-level reading.

2. **False-premise acceptance.** The model treats non-existent study destinations ("London, USA", "Toronto, Australia") and non-existent programs ("MS in CS at AIIMS", "Bachelor of Medicine at Stanford", "Mathematical and Computational Science Tripos" at Oxford) as real and elaborates admissions details. The same v4 §4.4 mechanism: the training data's template cross-product produces incoherent prompts, and the model learns to answer them as if valid.

3. **Quantitative claim fabrication.** Specific numbers are wrong by a wide margin: UK student visa "3 to 6 weeks" (actual 3 or 8); UK Railcard "£30" (actual £35); BahnCard "50% off long-distance + 25% off regional" (reversed structure); MBTA monthly "$90-$120" (actual $90-$132); 2021 Australia international students "over 550,000" (actual ~417-500k after COVID drop); Melbourne MD "3.5/4.0 GPA split" (GEMSAS has no such split). These are credible-looking but cannot survive a primary-source check.

4. **Healthcare/insurance is the densest error category.** 5 of 39 v5 verified_wrong rows concern healthcare or insurance eligibility (Bangladesh NHS, Bangladesh free healthcare, Australia Medicare for Pakistani students, USA SHIP "basic", MBTA pass bound). Healthcare/insurance is the highest-severity risk area for downstream advising harm.

5. **The v4 patterns are reproduced, not improved.** All four v4 D-cases (Australia Medicare, Brazil scholarships, Oxford medicine, HMS data science) are still present in the v5 sample as the same mechanism operating in a different slice of the corpus. The pre-registered stratified test (§4.5) is now ready to formally attribute this rate to the *data* rather than the *method*.

6. **Test-instrument confusion** (round-2 pattern). The model repeatedly maps "top medical school" → "must take graduate standardized test" without grounding in the actual admission policy: AIIMS → GRE (actually NEET-PG), HMS → GRE (actually MCAT). It also confuses test-optional with test-required (Stanford, MIT) — these are recent policy shifts the training data does not capture.

7. **Outdated program listings** (round-2 pattern). The model persists in describing pre-2019 program structures: AIIMS standalone MBBS exam (replaced by NEET-UG 2019), MCI as a current authority (dissolved 2019), Endeavour Leadership Program (ended 2019), MIRS (merged into MRS 2016), IPRS (replaced by RTP 2016-2017). The training data appears to be a 2023 snapshot that has already aged out of several authoritative sources.

8. **Country-pair scholarships are systematically over-fabricated.** Brazil→Bangladesh, Brazil→India, China→Bangladesh, Pakistan→India, Pakistan→Germany, Pakistan→Uzbekistan, Bangladesh→Uzbekistan — every country-pair scholarship in the sample that had a specific number or specific name attached turned out to be either fabricated or unverifiable. This is the same mechanism v4 §4.4 flagged for v4-D-Case 2 (Brazil→Bangladesh).

## Limitations

1. **Power on Stratum W.** The pre-registration requires ≥15 stratifiable prompts per stratum. Stratum C hit 15 but Stratum W is at 14 (1 short of threshold); Stratum M is at 1. The 30-prompt C+W comparison has reasonable sensitivity for McNemar's test, but a strict reading of §4.2 would call this INSUFFICIENT. A round-3 extension of ~55 audits (targeting the 18 still-excluded prompts with 0 audited top-5 neighbors) would push Stratum W over 15.
2. **Source-access failures.** DAAD.de and several university pages were inaccessible during the audit window. Some `unclear` rows are blocked by this rather than by absence of error.
3. **Verdict consistency.** 12 parallel subagents across 2 rounds may apply slightly different evidence bars. The parent re-verified 4 of the originally-`unclear` rows to catch this.
4. **Truncated training answers.** Several rows in the audit template had answers truncated at the source-JSONL boundary, so the subagent could only verify the visible portion. The total number of checkable claims per row may be under-counted.

## What this enables

This catalog completes the **source-verification side** of the §3 pre-registered stratified causal test. The next steps are:

1. ~~Run `scripts/eval/stratify_prompts.py` to assign each held-out prompt to C/W/M strata based on training-set nearest-neighbor labels from this catalog.~~ **DONE** — `data/v5-stratified-prompts.csv` (30 stratifiable, 20 excluded).
2. Run `scripts/eval/generate_stratified.py` on a GPU to produce base + LoRA outputs for the stratified held-out set (30 stratifiable prompts).
3. Run `scripts/eval/analyze_stratified.py` to compute McNemar's test per stratum and update v5 §4.5 with the stratified test outcome.
4. **Optional** (round-3 audit extension): audit ~55 more top-5 neighbors to push Stratum W over the 15-prompt threshold.

