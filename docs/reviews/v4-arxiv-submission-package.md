# arXiv v4 Submission Package — 2504.15610

This file contains everything needed to post the revised manuscript as **version 4
of the existing arXiv submission 2504.15610** (same identifier — preserves the 5
existing citations; do **not** create a new submission). Three artifacts:

1. The arXiv **"Comments"** field text (metadata, public on the abstract page).
2. The arXiv **title-change** instruction (the title field genuinely changes in v4).
3. A **"Changes from earlier versions"** block to paste into the manuscript itself.

---

## 1. arXiv "Comments" field (paste into the Comments box on submit)

> Major revision and repositioning. Earlier versions (v1–v3) were titled "A
> LoRA-Based Approach to Fine-Tuning LLMs for Educational Guidance in
> Resource-Constrained Settings." This version corrects two unsupported claims
> from the earlier versions (an apparent "quantization-boundary" effect and a
> claim that optimizer/scheduler state was transferred across GPUs) and
> reframes the paper around (a) a reproducible free-tier cross-GPU
> adapter-handoff training recipe and (b) an honest held-out reliability
> evaluation with a source-verified factuality audit, extended to a direct
> audit of the synthetic training data. 19 pages, 5 figures, 7 tables. Code,
> dataset, adapter, and full evaluation harness released.

*(Keep it under ~1–2 lines per arXiv convention if preferred; the long form above
is acceptable. arXiv shows a per-version comment, so this records the v3→v4 delta
publicly.)*

---

## 2. Title change (arXiv metadata)

- **Old title (v1–v3):** A LoRA-Based Approach to Fine-Tuning LLMs for Educational
  Guidance in Resource-Constrained Settings
- **New title (v4):** Fine-Tuning a 7B Advisor on Free-Tier GPUs: An
  Adapter-Handoff Recipe and a Synthetic-Data Reliability Caution

arXiv permits changing the title on a new version; the abstract page will show the
new title with prior versions still accessible. The paper ID, and therefore the 5
citations, are unchanged. A title change does **not** require moderator
re-review beyond the normal new-version check.

---

## 2b. arXiv "Abstract" field (plain text — paste into the Abstract box)

LaTeX stripped (`\emph`, `\textbf`, `~`, `$...$`, `\alpha`) so nothing renders as
literal markup. arXiv rewraps automatically; line breaks below are cosmetic.

```
Fine-tuning a 7B-parameter language model for a specialized advising task is
attractive for resource-constrained settings, but the multi-epoch training runs it
requires routinely exceed the wall-clock session limits of the free-tier GPUs (e.g.,
Kaggle, Colab) available to such users. We report two things. First, a practical
recipe: a three-epoch QLoRA fine-tune of Mistral-7B-Instruct-v0.3 (4-bit NF4, LoRA
rank 16, alpha=32, via Unsloth) completed across two different free-tier 16 GB GPUs
(Tesla P100 then Tesla T4) by checkpointing only the small LoRA adapter (41.9M
parameters) and resuming on the second machine. We document that adapter-only handoff
is sufficient -- full optimizer and scheduler state need not be transferred -- so the
binding constraint is per-step VRAM and per-session wall-clock, not the aggregate
compute of a single machine. The two-phase run kept peak memory within budget on both
GPUs (15.888 GB / 14.741 GB) and reduced training loss from 1.01 to 0.34. Second, and
more importantly, an honest evaluation of the resulting model that returns a
cautionary result. On a blind held-out comparison against the un-fine-tuned base
model, the fine-tuned model scored higher on reference-based similarity to the
(synthetic) training distribution (BERTScore F1 +0.063 against synthetic references --
a fidelity, not quality, signal) but lower on advising quality: a blind LLM-as-judge
preferred the base model on 46% of prompts versus 18% for the fine-tuned model, and a
source-verified factuality audit found four confident factual errors from the
fine-tuned model on policy-sensitive topics (healthcare, admissions, and scholarships)
against zero for the base model on the same prompts. Fine-tuning on unverified
synthetic advising data raised fidelity to the training distribution while degrading
factual reliability. Auditing the training data directly with the same source-verified
method, we find that this is not a fine-tuning artifact: each of the four audited model
errors is already present in the Gemini-generated training answers, and a random-sample
audit finds a verifiable factual error in a sizable fraction of training responses
(point estimates 28-40%; single-judge, n=40). The training data is therefore sufficient
to account for the observed errors, which we attribute to the synthetic-data pipeline
rather than to the adapter-handoff method. We release the dataset, the adapter, the
cross-GPU training notebooks, and the full evaluation harness (automatic metrics, the
LLM-as-judge scripts, and both the model and dataset factuality catalogs) so that every
result can be reproduced from a single 16 GB GPU.
```

---

## 3. "Changes from Earlier Versions" block — paste into the manuscript

Insert this as an unnumbered note immediately after the abstract (before Section 1),
or as a footnote on the title. LaTeX provided.

```latex
\section*{Changes from Earlier Versions (v4)}
\small
This is a substantially revised version of a paper previously circulated under the
title ``A LoRA-Based Approach to Fine-Tuning LLMs for Educational Guidance in
Resource-Constrained Settings'' (arXiv:2504.15610v1--v3). Re-examination of our own
training logs, code, and statistics led us to withdraw two claims made in the
earlier versions and to reframe the contribution honestly:

\begin{itemize}
  \item \textbf{Withdrawn: the ``quantization-boundary'' finding.} Earlier versions
  attributed a loss reduction to a quantization-related effect at a training
  boundary. Our own loss curve is still declining at the end of epoch one, 4-bit
  NF4 quantization is held constant across the claimed boundary, and the additional
  reduction is fully explained by further epochs and a larger effective batch. We
  retract this claim; Section~4.1 now reports the trajectory as ordinary
  three-epoch training behavior.
  \item \textbf{Corrected: cross-GPU state transfer.} Earlier versions implied that
  optimizer and scheduler state were carried across the GPU handoff. The released
  code transfers \emph{only} the LoRA adapter; the optimizer is re-initialized on
  the second GPU. Section~3.3 now states this correctly, and the adapter-only
  handoff is reframed as the operational contribution.
  \item \textbf{Added: an honest reliability evaluation and a training-data audit.}
  A blinded held-out comparison against the un-fine-tuned base model, a blind
  LLM-as-judge, and a source-verified factuality audit show that fine-tuning on
  unverified synthetic data raised fidelity to the synthetic distribution while
  degrading factual reliability. A direct audit of the training data
  (Section~4.4) isolates the cause to the synthetic-data pipeline rather than the
  fine-tuning method.
  \item \textbf{Scope and venue.} The paper is repositioned from an educational-
  guidance contribution to a reproducibility / efficient-ML systems contribution
  with a synthetic-data reliability caution.
\end{itemize}
\normalsize
```

---

## 4. Submission checklist (mechanical)

- [ ] Log in to arXiv as the submitting author of 2504.15610.
- [ ] Choose **"Submit a new version (v4)"** — NOT a new submission.
- [ ] Upload the current `main_revised.tex` + all 5 figures (`fig1_arch.png`,
      `fig2_loss_p100.png`, `fig3_grad_p100.png`, `fig4_loss_t4.png`,
      `fig5_grad_t4.png`) and let arXiv compile, OR upload the compiled PDF if
      using PDF-only (source is preferred by arXiv).
- [ ] Update the **Title** field to the new title (§2 above).
- [ ] Paste the **Comments** field (§1 above).
- [ ] Confirm the abstract field matches the manuscript abstract (it changed).
- [ ] Verify the author/affiliation and the Data/Code Availability URLs resolve.
- [ ] (Recommended) Add/keep the cs.CL primary category; cross-list cs.LG.
- [ ] Submit; verify v4 renders and prior versions remain listed.

## 5. One honesty note for you

Because v1–v3 are permanent on arXiv, the retraction is visible — this is the
correct and defensible outcome: the v4 note shows you found and corrected the
errors yourself, which is far stronger than a silent re-upload. The 5 citations
attach to the identifier, so they carry forward to v4 regardless of the title and
content change.
