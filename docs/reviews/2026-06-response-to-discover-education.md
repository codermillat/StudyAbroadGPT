# Response to Reviewers

We thank the editor and both reviewers. The reviews prompted a substantial
reframing of the paper. We summarize the changes first, then respond point by
point. The revised manuscript is `main_revised.tex`.

## Summary of major changes

1. **Repositioned the contribution.** The original framing (a "quantization-
   boundary finding") was not supported by our own data: the Phase-1 loss is
   still declining at end of epoch one, quantization is held constant across the
   claimed boundary, and the loss reduction is explained by additional epochs and
   a larger batch. We removed this claim entirely and reframed the paper around
   (a) a reproducible free-tier cross-GPU adapter-handoff training recipe and
   (b) an honest held-out reliability evaluation.
2. **Added a real output-quality evaluation** (addresses R2.1): a blind LLM-as-
   judge and a source-verified factuality audit, in addition to the reference-
   based metrics. These reveal that fine-tuning on synthetic data improved
   distribution fidelity but degraded factual reliability — now the paper's
   central finding.
2b. **Added a direct audit of the training data (new Section 4.4) that isolates
   the cause.** Using the same source-verified method on the corpus itself, we
   show (a) each of the four model errors is already present in the
   Gemini-generated training answers (causal match, Table 7), and (b) a random
   sample (n=40) finds a verifiable factual error in ~a quarter to a half of
   training answers. This demonstrates the reliability drop is a property of the
   **data pipeline**, not the fine-tuning method — converting the paper's most
   exposed result into its most defensible one.
3. **Corrected a factual error about the training procedure**: the cross-GPU
   handoff transfers only the LoRA adapter, not optimizer/scheduler state. The
   original text claimed otherwise; the revision matches the released code.
4. **Removed an unsupported "controlled variable" claim** about the two-phase
   schedule and now state explicitly that it is a deployment recipe, not an
   ablation.

## Reviewer 1

> *The work does not demonstrate sufficient scientific novelty / resembles an
> engineering or tutorial-style implementation report.*

We agree the original framing oversold a "finding" the data did not support, and
we have removed it. The revision makes two honest claims instead: an operational
recipe (adapter-only cross-GPU handoff under free-tier session limits), and a
**research finding with a mechanism** — that fine-tuning on unverified synthetic
data raises similarity to the synthetic distribution while degrading ground-truth
factual reliability (Section 4.3). The latter is supported by three independent
signals, including a judgment-free, source-verified factuality audit, and is a
transferable caution for practitioners. Crucially, we then audit the training
data itself (Section 4.4) and trace the finding to a concrete mechanism — a weak
2023-era generator (Gemini 1.0 Pro), an unconstrained prompt-template cross-
product, and no factuality gate produced a corpus ~a quarter to a half of which
is factually wrong, which faithful fine-tuning then inherited. A result with a
demonstrated causal mechanism is not an implementation report. We believe this
addresses the concern.

## Reviewer 2

> **2.1** *Evaluated solely by training-loss reduction; report standard NLP
> metrics and compare against the un-fine-tuned baseline.*

Addressed. Section 4.3 now reports a full head-to-head against the un-fine-tuned
Mistral-7B-Instruct-v0.3 baseline on a held-out split: reference-based metrics
(SacreBLEU, ROUGE-L, BERTScore with bootstrap CIs), a blind LLM-as-judge, and a
source-verified factuality audit. Training loss is reported only as training
dynamics (Section 4.1), not as a quality claim.

> **2.2** *Training data is entirely synthetic; collect real interactions or run
> a user survey.*

We treat the fully synthetic nature of the data as a first-class limitation
(Section 5.2) and, importantly, make it the subject of measurement: the
reliability finding is precisely about what training on synthetic data does.
We were unable to collect real student–advisor data for this submission;
Section 5.3 commits to an IRB-approved real-user study and human evaluation as
the primary next step, and we do not claim any real-user results here.

> **2.3** *Specify LoRA hyperparameters and fine-tuning settings.*

Addressed. Table 2 gives the complete configuration (rank, alpha, dropout,
target modules, optimizer, learning rate, scheduler, warmup, gradient clipping,
precision, sequence length), verified against the released `adapter_config.json`.

> **2.4** *Detail the synthetic dataset: prompt templates, topic distribution,
> quality filtering.*

Addressed. Section 3.1 now gives the generation prompts (3.1.2), the eight-topic
distribution (Table 1), and describes the five quality-control scripts with their
results (Table 3). The pipeline figure boxes are described in the text.

## On evaluation honesty

We disclose explicitly that the LLM-as-judge is a single judge model, single
pass, on synthetic-split prompts, and is **not** human evaluation; the originally
planned two-annotator human scoring was not completed and we report no
inter-rater statistic (the prior draft's promise of one has been removed). The
factuality audit verdicts, by contrast, are checked against external
authoritative sources and do not depend on any model's judgment.
