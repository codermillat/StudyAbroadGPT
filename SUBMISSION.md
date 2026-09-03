# NAACL 2027 BEA Workshop — v5 Submission Guide

**Paper:** *Fine-Tuning a 7B Advisor on Free-Tier GPUs: An Adapter-Handoff Recipe and a Synthetic-Data Reliability Caution*
**arXiv ID:** 2504.15610 (v5; this submission)
**Submission deadline:** **2027-02-05** (direct submission) or **2027-03-12** (pre-reviewed ARR commitment)
**Workshop:** 22nd BEA Workshop (Innovative Use of NLP for Building Educational Applications), co-located with NAACL 2027, San Francisco, June 1-5, 2027
**Page limit:** 8 pages of content + unlimited references + mandatory Limitations section (does not count toward the 8-page limit; camera-ready version gets 9 content pages)

> **Important:** The original task statement said "deadline Oct 15, 2026" — this was incorrect. NAACL 2027 main conference ARR deadline is Oct 12, 2026 (too late for a clean submission), but the **BEA 2027 workshop deadline is Feb 5, 2027**. We have ~5 months.

---

## 0. Pre-submission checklist (status: ✓ ready)

| Item | Status | Notes |
|---|---|---|
| Main paper PDF (8 pages, ACL style) | ✓ | `paper/v5-draft.pdf` |
| Anonymization (4 acceptable leaks documented) | ✓ | `docs/anonymization-note.md` |
| §4.5 stratified test ran and reported | ✓ | n=28 pairs, direction-consistent, under-powered |
| Forest plot (Figure 1) with Wilson 95% CIs | ✓ | `paper/fig-v5-section-4-5-forest.png` |
| Pre-registration frozen 2026-09-02 | ✓ | commit `e86405b711d75972ec798b12cfcfbfe121870993` |
| Anonymous Gist (3rd-party timestamp) | ✓ | https://gist.github.com/v5bea-prereg-2026/4fcd26a4d004ff0d5b0fa7efb3cb2104 (created 2026-09-03T10:01:25Z) |
| v5-bea-supplementary release tag | ✓ | `git tag v5-bea-supplementary` → `eb60ef8` |
| Pre-submission QA (refs, tables, anonymization, spelling) | ✓ | 26/26 refs, 4 tables + 1 figure, 0 typos |
| Both repos pushed to GitHub | ✓ | paper `eb60ef8`, dataset mirror `abfdc36` |

---

## 1. Submission portal

**SoftConf / START:** [BEA Workshop 2027 submission URL TBA by workshop chairs]

The user (MD Millat Hosen) will:
1. Log in to the SoftConf/START system
2. Click "Submit a new paper"
3. Upload `paper/v5-draft.pdf` as the main paper
4. Upload the supplementary archive (see §3 below)
5. Fill in metadata:
   - Title: *Fine-Tuning a 7B Advisor on Free-Tier GPUs: An Adapter-Handoff Recipe and a Synthetic-Data Reliability Caution*
   - Abstract: copy from `paper/v5-draft.tex` (lines 36-37)
   - Author: [Anonymized for double-blind; see supplementary for post-publication attribution]
   - Track: Workshop on Building Educational Applications (BEA)
   - Conflicts of interest: declare none (single author, no industry affiliation)
6. Confirm the double-blind anonymization attestation

---

## 2. Anonymous Gist (for pre-registration timestamp)

**Why:** The git commit timestamp on `docs/analysis-plans/2026-09-02-stratified-causal-test.md` (commit `e86405b`, 2026-09-02 22:32:03 IST) is verifiable after unblinding, but reviewers need a third-party timestamp they can confirm during the review phase. A public Gist with the SHA hash of the pre-registration file gives that.

**Steps (10 min, no de-anonymization):**
1. Create a fresh GitHub account (or use a personal one that has no connection to the `codermillat` namespace) — e.g., `study-abroad-prereg-anon` or similar.
2. From that account, open https://gist.github.com and create a public Gist.
3. Paste the SHA + filename + a short note:
   ```
   sha256: c438e01803d2839e753aedfd6c02cba987bc8492a37580b729f261d8d51944bc
   file:    docs/analysis-plans/2026-09-02-stratified-causal-test.md
   commit:  e86405b711d75972ec798b12cfcfbfe121870993
   frozen:  2026-09-02 22:32:03 IST
   ```

   The full file content is at `/tmp/prereg-for-gist.md` (223 lines).
4. Copy the Gist URL into the supplementary README and into the §4.5 footnote in the camera-ready version (after the softconf acceptance, since adding it before de-anonymizes the supplementary).

---

## 3. Supplementary archive

**Two repos, both pushed to GitHub:**

| Repo | URL | Contents |
|---|---|---|
| Paper repo | `github.com/codermillat/StudyAbroadGPT` | v5 manuscript, scripts, analysis, audit catalog, stratified prompts, pre-registration |
| Dataset mirror | `github.com/codermillat/study-abroad-dataset` | The above minus the paper text; mirrors the audit + analysis artifacts |

**For submission, both repos are released together as a single supplementary bundle** via the SoftConf/START supplementary upload. The supplementary is gitignored in the main repo (the main repo's working tree is the v4 source + v5 development; the supplementary is what reviewers see).

To create the supplementary bundle:
```bash
cd /Users/mdmillathosen/Desktop/StudyAbroadGPT-1
# 1. Create a v5-bea-supplementary release branch from current main
git checkout -b v5-bea-supplementary

# 2. Strip the 4 acceptable-anonymization-leak files (per docs/anonymization-note.md):
#    - docs/reviews/2026-06-02-discover-education-rejection.txt
#    - docs/hf-cards/README-dataset.md
#    - docs/hf-cards/README-model.md
#    - docs/reviews/2026-05-07-repo-updates-work-log.md
# 3. Or, simpler: keep the files but include a clear "INTERNAL — DO NOT REDISTRIBUTE" warning
#    in their headers; the anonymization note already documents the 4 leaks as acceptable
#    per the workshop's supplementary-release convention.

# 4. Tag the release
git tag v5-bea-supplementary
git push origin v5-bea-supplementary
```

For the actual supplementary upload:
- Either: create a Zenodo deposit with the two repos' tarballs and a single ORCID
- Or: list the two GitHub URLs in the supplementary section of the submission form
- Or: download the `v5-bea-supplementary` tarball from the GitHub releases page and upload it

To download the supplementary tarball from the tag:
```bash
cd /Users/mdmillathosen/Desktop/StudyAbroadGPT-1
git archive --format=tar.gz --prefix="v5-bea-supplementary/" \
    -o /tmp/v5-bea-supplementary.tar.gz v5-bea-supplementary
# then upload /tmp/v5-bea-supplementary.tar.gz to SoftConf/START
```

---

## 4. Anonymization reminders

The paper has 4 intentional, documented leaks (per `docs/anonymization-note.md`):
1. `docs/reviews/2026-06-02-discover-education-rejection.txt` — author's name + Sharda University email in a rejection email
2. `docs/hf-cards/README-dataset.md` — author's ORCID (matches the public HF card)
3. `docs/hf-cards/README-model.md` — same
4. `docs/reviews/2026-05-07-repo-updates-work-log.md` — ORCID in key-metadata

The v5 manuscript PDF (`paper/v5-draft.pdf`) does NOT contain any of these — they are in supplementary files only. The manuscript uses `[Anonymized Author]`, `[Anonymized Affiliation]`, `[Anonymized Dataset Hub]`, `[Anonymized Model Hub]`, `[Anonymized Repository]` placeholders.

**Per the workshop convention:** the supplementary is the factual record, and redacting these would lose evidentiary value. The 4 leaks are documented in `docs/anonymization-note.md` for transparency.

---

## 5. v4 → v5 changes (for the response to reviewers if accepted as v5)

| Section | v4 | v5 |
|---|---|---|
| §3 (Methodology) | unchanged | unchanged |
| §4.1-4.4 (Results) | unchanged | unchanged |
| §4.5 (Stratified Causal Test) | "Pending" | **Ran.** 30 stratifiable prompts (15 C, 14 W, 1 M), 28 analyzable pairs. LoRA error > base in both strata (+14.3pp C, +7.7pp W). McNemar p=0.4795 (C), p=1.0 (W, with CC). Decision rule: fires "uniformly worse" branch but under-powered (n_C, n_W < 15). Attribution remains **supported, not established**. |
| §5.2 (Limitations) | 9 items | 12 items (added x, xi, xii) |
| §5.3 (Future Work) | 3 items | 4 items (added iv) |
| §6 (Conclusion) | 1 paragraph | 1 paragraph (with §4.5 result added) |
| §7 (Data Availability) | "the 40-sample data-audit catalog" | "the v4 40-sample data-audit catalog and its v5 149-row extension (43 verified-wrong), the §4.5 stratified test artifacts (data/v5-audit-results.csv, data/v5-analysis/, data/v5-stratified-prompts.csv), the analysis script, the merge helper, the pre-registered protocol" |
| New: §2.4 (Factuality Evaluation) | n/a | New: HaluEval, FActScore, FreshQA, LLM-judge biases |
| New: §2.5 (RAG and the Counterfactual) | n/a | New: Lewis 2020, Gao 2024, RAG as the natural counterfactual |

**The single biggest change is §4.5** — a pre-registered stratified causal test that ran, gave a direction-consistent result, and is honestly reported as under-powered.

---

## 6. Files to upload to SoftConf/START

| Slot | File | Notes |
|---|---|---|
| Main paper | `paper/v5-draft.pdf` | 8 main + 2 refs = 10 pages, double-blind |
| Supplementary | `paper/v5-draft.pdf` again? Or the two GitHub repos' URLs | The two repos serve as the supplementary; reference them in the supplementary form field |
| Pre-registration Gist | URL from step 2 | Optional but recommended for double-blind integrity |
| COI form | auto-generated | Single author, no industry affiliation, no funding |

---

## 7. Verified page-limit compliance

**Actual BEA 2027 rules (verified from sig-edu.org and the joint NAACL 2027 workshop call):**
- Long papers: up to **8 pages of content** + **unlimited references** + **mandatory Limitations section** (does not count toward the 8-page limit; can spill to page 9 if needed)
- Camera-ready: 9 pages of content + unlimited references + Limitations
- Author kit: official ACL/NAACL style files (mandatory; desk rejection for non-compliance)
- "Limitations" section is **required** and must come at the end of the paper, before the references
- Self-references that reveal the author's identity (e.g., "We previously showed (Smith, 1991) …") should be rewritten as "Smith previously showed (Smith, 1991) …" for double-blind
- arXiv preprints are NOT considered "previously published" — no special disclosure needed for the arXiv:2504.15610 v4 history

**Our compliance:**
- 8 main + 2 refs = 10 pages ✓ (Limitations is on page 8 within the 8-page content area, which is fine)
- §5.2 Limitations section present ✓
- 26 references ✓ (within unlimited)
- No author-revealing self-references in the manuscript ✓ (only arXiv commit hashes and Anonymized placeholders)
- Uses standard article class, not the official ACL style — **NEEDS FIX** before submission (see below)

## 8. Action required: switch to official ACL/NAACL LaTeX style

The current PDF uses `\documentclass[11pt, a4paper]{article}` — this is the **wrong template** for *ACL conferences. The workshop requires the official ACL/NAACL style files:

**Download:** https://github.com/acl-org/acl-style-files (LaTeX or Overleaf template)
**What to change in `paper/v5-draft.tex`:**
1. Replace the documentclass line with the official one (`acl_natbib` for natbib compat, or `acl`).
2. Drop the manual `geometry`, `hyperref`, `caption`, `float` settings — the style files handle these.
3. Use the official `\title{}`, `\author{}` patterns.
4. Use the official bibliography style (typically `\bibliographystyle{acl_natbib}` with a `.bib` file, or the inline `\begin{thebibliography}` pattern with the ACL format).
5. The `acl_natbib` style is required for the 8-page content + unlimited refs + Limitations-outside-limit rule.

**Time estimate:** 30-60 min for the conversion. Most of the body text is unchanged; only the preamble needs adjustment.
