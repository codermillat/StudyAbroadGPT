# Factuality Error Catalog — Base vs. LoRA (curated)

**What this is.** A curated, ground-truth factuality comparison of the base
Mistral-7B-Instruct-v0.3 model and the LoRA fine-tuned model on the 50-prompt
held-out evaluation set. Unlike the LLM-as-judge scores, the verdicts here do
**not** depend on any model's judgment — each contested claim is checked against
an authoritative external source (cited). This directly addresses Reviewer 2's
request for output-quality assessment on policy-sensitive advising topics.

**Selection.** Curated from the 18/50 prompts where the blind judge's domain-
accuracy scores diverged between models (see `Model_llm_judge_scores.csv`).
Direction of divergence across all 18: **LoRA worse on 16, better on 2, tied on
the remaining 32.** This catalog documents the clearest, highest-sensitivity
cases with external verification.

---

## Verified errors (LoRA produced a false claim; base did not)

### Case 1 — Harvard Medical School standardized testing (sample 2) — SEVERITY: HIGH
- **Prompt:** "What are the GRE requirements for Harvard Medical School?"
- **LoRA (WRONG):** "Harvard Medical School (HMS) requires the following for the Graduate Record Examinations (GRE): ... HMS requires all applicants to submit GRE scores."
- **Base (CORRECT):** "Harvard Medical School does not specify a minimum GRE score ... they do require the MCAT exam for all applicants."
- **Ground truth:** The HMS MD program centers on the **MCAT**; the GRE is **optional/supplemental, not required**. ([HMS Admissions Eligibility](https://meded.hms.harvard.edu/admissions-eligibility-requirements))
- **Verdict:** LoRA factuality **0/2** (fabricated a hard requirement). Base **2/2**.

### Case 2 — Medicare eligibility for international students in Australia (sample 11) — SEVERITY: HIGH
- **Prompt:** "How does the healthcare system work for international students in Australia?"
- **LoRA (WRONG):** "International students are eligible for Medicare coverage after they arrive in Australia and have been enrolled in their course for at least six months."
- **Base (CORRECT):** "international students are not eligible for Medicare. Instead, they are required to have Overseas Student Health Cover (OSHC) as a condition of their student visa."
- **Ground truth:** International students are **not** eligible for Medicare (save limited Reciprocal Health Care Agreement countries); **OSHC is compulsory** under student-visa condition 8501. ([Study Australia (gov)](https://www.studyaustralia.gov.au/en/plan-your-move/overseas-student-health-cover-oshc); [privatehealth.gov.au](https://www.privatehealth.gov.au/health_insurance/overseas/overseas_student_health_cover.htm))
- **Verdict:** LoRA factuality **0/2** (false eligibility claim on a visa-critical topic). Base **2/2**.

### Case 3 — Nonexistent "Bachelor of Medicine at Stanford" (sample 37) — SEVERITY: MED
- **Prompt:** "Do I need to submit my IGCSE for admission to Bachelor of Medicine at Stanford?"
- **LoRA (WRONG):** "Stanford University does not require IGCSE ... for admission to its Bachelor of Medicine program." — accepts and elaborates a program that does not exist.
- **Base (CORRECT):** "Stanford does not offer a direct undergraduate degree in medicine. Instead, students typically complete an undergraduate degree in a related field ..."
- **Ground truth:** US medical education is post-baccalaureate; Stanford offers the **MD** (Stanford School of Medicine), **not** an undergraduate "Bachelor of Medicine"/MBBS. Base correctly rejects the false premise; LoRA confabulates around it.
- **Verdict:** LoRA factuality **0/2** (false-premise acceptance). Base **2/2**.

### Case 4 — Fabricated scholarships for Brazilian students in Bangladesh (sample 34) — SEVERITY: MED
- **Prompt:** "What scholarships are available for Brazilian students in Bangladesh?"
- **LoRA (WRONG):** "Brazilian students ... may qualify for various scholarships. Here are some notable scholarships ... 1. Government of Bangladesh Scholarship ..." — names specific programs not established to exist for this corridor.
- **Base (CORRECT/HONEST):** "Scholarships for Brazilian students in Bangladesh are not common, as these two countries are geographically far apart ... However, there are opportunities for international scholarships ..."
- **Ground truth:** No established Brazil→Bangladesh scholarship programs of the kind LoRA names; the honest answer is base's "not common." LoRA fabricates specifics.
- **Verdict:** LoRA factuality **0/2** (fabrication). Base **2/2**.

---

## Cases where LoRA was BETTER (honesty requires reporting these)

- **Sample 17** (UK student-visa processing time): LoRA added correct timing/biometrics detail; judge domain 3 vs base 2. No factual error in either; LoRA more complete.
- **Sample 49** (MIT sports/fitness facilities): LoRA more accurate on facility specifics; judge domain 2 vs base 1 (base had some likely-inaccurate facility names).

These are completeness/specificity wins, **not** corrections of base factual errors — qualitatively weaker than the four LoRA failures above, which are hard factual/safety errors on policy-sensitive topics.

---

## Tally (curated divergent set)

| Direction | Count | Nature |
|---|---:|---|
| LoRA worse | 16/18 divergent | incl. 4 hard verified factual/safety errors above |
| LoRA better | 2/18 divergent | completeness/specificity, no base error corrected |
| Tied | 32/50 overall | both adequate or both truncated |

**Reading.** On the prompts where the two models differ, the difference is
overwhelmingly LoRA being *less* reliable, and the most severe cases are
confident factual errors on visa, healthcare, and admissions topics — exactly
the policy-sensitive areas where wrong advice carries real cost. This is
consistent with, and mechanistically explains, the LLM-as-judge result
(base preferred 46% vs 18%) and coexists with LoRA's higher BERTScore
(fidelity to the synthetic training distribution, not to ground truth).

**Disclosure.** Ground-truth verification was performed by the author with web
search against the cited authoritative sources (June 2026). This is a curated
audit of divergent cases, not a full 50x2 systematic factuality scoring; a
systematic pass remains available as a next step.
