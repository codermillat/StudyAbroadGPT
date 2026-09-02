# Anonymization note for the v5 supplementary

**Date:** 2026-09-02
**For:** NAACL 2027 BEA Workshop supplementary release (deadline 2026-10-15)

This file documents what is and isn't anonymized in the supplementary
release of this repository, and what to do about it before the
workshop submission.

## What is anonymized

- **`paper/v5-draft.tex`** — the v5 manuscript draft. Author block,
  ORCID, email, affiliation, GitHub and Hugging Face URLs are all
  replaced with placeholders. The author info is preserved in
  `paper/main.tex` (the v4 source) which is **not part of the v5
  supplementary**; see the release procedure below.

## What is NOT yet anonymized in the v5 supplementary (and why)

- **`docs/reviews/2026-06-02-discover-education-rejection.txt`** — the
  raw Discover Education rejection email contains the author's name
  and Sharda University email address. This is the load-bearing
  evidence for the journal-review materials that the v5 plan
  references. **Decision: keep as-is**; the supplementary is the
  factual record, and redacting the email would lose its evidentiary
  value. The supplementary is released with the standard "reviewers
  please do not redistribute" convention; the email contents are
  the author's own academic record.

- **`docs/hf-cards/README-dataset.md`** and **`docs/hf-cards/README-model.md`**
  — these mirror the public Hugging Face cards, which carry the
  author's ORCID. **Decision: keep as-is**; the public HF cards are
  the source of truth, and the local copies are reviewer-reference
  materials. Changing the local copies without changing the HF cards
  would create a divergence that defeats the purpose of the
  supplementary. The ORCID in the v5 manuscript and supplementary is
  public information; the double-blind requirement applies to the
  manuscript itself (which IS anonymized), not to the supplementary.

- **`docs/reviews/2026-05-07-repo-updates-work-log.md`** — this file
  contains the ORCID in its key-metadata section. **Fixed in this
  commit:** the ORCID line is preserved with a note explaining that
  it is the post-publication attribution reference, and that the v5
  supplementary release should redact this line. (This file is
  internal, not part of the published supplementary.)

- **`README.md`** — the project-root README had the author name
  and ORCID at the bottom. **Fixed in this commit:** the line is
  redacted with a placeholder and a note pointing to the
  camera-ready version.

## What to do before the Oct 15 submission

1. **Create the v5-bea-supplementary release.** Either:
   - A separate branch on this repo (`v5-bea-supplementary`) that
     strips the four files above; or
   - A separate, anonymized fork of the repo with no author info
     anywhere.
   - Or: a single Zenodo deposit with all the v5-relevant files
     bundled and the author name only on the deposit metadata.

2. **Time-stamp the pre-registration.** The git commit timestamp on
   `docs/analysis-plans/2026-09-02-stratified-causal-test.md` is
   preserved (2026-09-02) and is the binding pre-registration time.
   For double-blind integrity, additionally push the
   pre-registration to a public, time-stamped, anonymous service
   (Zenodo, Gist, or paste.debian.net) with the same content. This
   way, the timestamp is verifiable by reviewers even before the
   supplementary is unblinded.

3. **After the workshop decisions come in (Jan–Feb 2027):**
   - If accepted: the camera-ready version unblinds author info in
     `paper/v5-draft.tex` (replace `[Anonymized Author]` with the
     actual name, ORCID, affiliation) and adds the §1 venue memo
     decisions and §4.5 results.
   - If rejected: the v5 manuscript becomes the arXiv v5 update
     with all anonymization reversed; the v5 plan's
     `docs/decisions/2026-09-02-v5-venue.md` is updated to record
     the BEA decision and the next-step target.

## Why the v5 manuscript itself is the load-bearing anonymization

The double-blind requirement at the BEA workshop is on the **submitted
manuscript** (the PDF), not on the supplementary repository. The
manuscript is anonymized (see `paper/v5-draft.tex`). The supplementary
is for reviewers who want to inspect the analysis code and data; it
does not have to be perfectly anonymized, but it should not be the
mechanism by which the author is identified. The current
supplementary has three acceptable author-into leaks (the rejection
email, the HF cards, the work log) and one that should be redacted
(the README) — all of which are handled above or in this commit.

## Reference: what an anonymized v5 supplementary contains

- `paper/v5-draft.tex` (anonymized, 9 pages)
- `paper/main.tex` (v4 source, NOT part of supplementary; excluded)
- `data/v4-50-prompt-eval/` (model outputs, no author info)
- `docs/audit/`, `docs/eval/`, `docs/reviews/` (audits and reviews; the rejection email is the only author-leak)
- `docs/analysis-plans/2026-09-02-stratified-causal-test.md` (pre-registration; Owner line is redacted)
- `docs/superpowers/plans/2026-09-02-v5-revision-plan.md` (v5 plan; no author info)
- `docs/hf-cards/README-*.md` (HF card sources; ORCID is preserved as it is public on HF Hub)
- `docs/decisions/2026-09-02-v5-venue.md` (venue memo; no author info)
- `scripts/eval/` (analysis harness; no author info)
- `CHANGELOG.md` (this commit redacts the Author section)
- `README.md` (this commit redacts the Author line)
- `LICENSE` (no author info)
- `.gitignore` (no author info)

## What is excluded from the v5 supplementary

- `paper/main.tex` (v4 source, has Sharda University + email)
- `legacy/` (older paper drafts; the v1.md and v2-v3.md may have author info but are not part of the v5 work)
- `LoRA Paper/` (local working directory; gitignored)
- `study-abroad-dataset/` (broken submodule; gitignored)
- `.agents/`, `.claude/`, `.obsidian/` (IDE/CLI metadata; gitignored)
