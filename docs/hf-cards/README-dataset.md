---
license: mit
language:
- en
size_categories:
- 1K<n<10K
task_categories:
- question-answering
- text-generation
pretty_name: StudyAbroadGPT Dataset
tags:
- education
- study-abroad
- university-applications
- nlp
- domain-adaptation
- lora
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: test
    path: data/test-*
dataset_info:
  features:
  - name: conversations
    list:
    - name: from
      dtype: string
    - name: value
      dtype: string
  splits:
  - name: train
    num_bytes: 13556552.97
    num_examples: 2274
  - name: test
    num_bytes: 2396541.03
    num_examples: 402
  download_size: 7115402
  dataset_size: 15953094.0
---

# StudyAbroadGPT Dataset

A synthetic, domain-specific conversational dataset (2,676 multi-turn conversations) designed for training and fine-tuning language models on study-abroad academic advising topics.

**Current Status**: Structural audit complete ✅ | Source-verified factuality audit complete ✅ (per arXiv:2504.15610v4 §4.4) | Caveat Phrase Usage regression flagged in §5.1

## 🔗 Project Ecosystem

| Resource | Link |
|----------|------|
| LoRA Model (fine-tuned) | [millat/StudyAbroadGPT-7B-LoRa-Kaggle](https://huggingface.co/millat/StudyAbroadGPT-7B-LoRa-Kaggle) |
| Training Code | [codermillat/StudyAbroadGPT](https://github.com/codermillat/StudyAbroadGPT) |
| Dataset Generation | [codermillat/study-abroad-dataset](https://github.com/codermillat/study-abroad-dataset) |
| Evaluation Artifacts | [LoRA Paper evaluation workspace](https://github.com/codermillat/LoRA-Paper) |
| Research Paper | [arXiv:2504.15610](https://arxiv.org/abs/2504.15610) |
| Author ORCID | [0009-0005-7198-9893](https://orcid.org/0009-0005-7198-9893) |

## 📊 Dataset Overview

### Statistics

| Metric | Value |
|--------|-------|
| **Total Conversations** | 2,676 |
| **Training Split** | 2,274 (85%) |
| **Test Split** | 402 (15%) |
| **Total Turns** | 6,941 user + 6,941 assistant |
| **Average Turns/Conversation** | 5.2 ± 1.0 |
| **Turn Range** | 4–6 |
| **Format** | Hugging Face datasets (Parquet) |

### Quality Metrics (Structural Audit)

| Check | Result |
|-------|--------|
| Schema Validity | 100% ✅ |
| Role Alternation | 100% ✅ |
| Empty Values | 0 ✅ |
| Exact Duplicate Groups | 0 ✅ |
| Train/Test Exact Overlap | 0 ✅ |
| Near-Duplicate Pairs (TF-IDF ≥ 0.90) | 0 ✅ |
| Repeated Response Groups | 2 groups |

### Lexical Diversity

| Metric | Value |
|--------|-------|
| Distinct-1 | 0.0054 |
| Distinct-2 | 0.1111 |

**Interpretation**: Low Distinct-1 indicates repeated domain vocabulary (expected for narrow advising corpus). Not overinterpreted as linguistic diversity.

## 🔬 Source-Verified Factuality Audit (arXiv:2504.15610v4 §4.4)

A source-verified audit was performed against authoritative external sources on a random sample (n=40) of training answers.

| Metric | Value | 95% CI (Wilson) |
|--------|------:|-----------------|
| **Hard-error rate** | 11/40 (27.5%) | [16%, 43%] |
| **Inclusive-error rate** | 16/40 (40%) | [26%, 55%] |

**Methodology**: single-judge LLM (different model family from the data generator) anchored to web-verified authoritative sources. Each contested claim checked against official government, university, or program pages.

**Decision rule applied**: report as **indicative** (point estimates 28–40%) rather than as a precise figure, given the modest sample size.

**The 4 known source-verified D-Cases (model errors traced here)**:
- D-Case 1 (Australia healthcare): training answer falsely states international students are eligible for Medicare after 12 months. Ground truth: not eligible; OSHC is compulsory. Source: [Study Australia](https://www.studyaustralia.gov.au/en/plan-your-move/overseas-student-health-cover-oshc).
- D-Case 2 (Brazil→Bangladesh scholarships): training answer invents "Commonwealth Scholarships including Brazil". Ground truth: Brazil is not a Commonwealth member. Source: [British Council](https://study-uk.britishcouncil.org/scholarships-funding/commonwealth-scholarships).
- D-Case 3 ("Bachelor of Medicine at Oxford"): training answer elaborates requirements for a template-generated program label. Ground truth: Oxford's degree is the BM BCh, not "Bachelor of Medicine".
- D-Case 4 ("MS in Data Science at Harvard Medical School"): training answer treats an incoherent prompt as valid. Ground truth: HMS offers no such program.

## 🧠 Data Creation Methodology

### Approach

1. **Research Phase**: Manual review of study-abroad FAQs, student forums, university portals
2. **Synthetic Generation**: Prompted generation using Google Gemini 1.0 Pro API (December 2023-era model)
3. **Quality Validation**: Automated structural checks; **no factuality gate** (this is the documented mechanism behind the v4 §4.4 audit findings)
4. **Manual Review**: Author reviewed ~200 conversations for clarity, realism, and structure

### Generator Provenance (v4 §3.1)

- **Model**: `gemini-1.0-pro` (hardcoded at `study_abroad_dataset/src/generator/conversation_generator.py:79`)
- **Generation date**: 2024
- **Mechanism**: `{program} × {university}` template cross-product (`config.py`); the unconstrained parameter draw can yield factually incoherent prompts (e.g., "MS in Data Science at Harvard Medical School," which does not exist), and the generator answers as if valid rather than rejecting the false premise. This design choice is the documented mechanism behind the v4 reliability finding.

## ⚠️ Limitations and Important Disclaimers

### What This Dataset Is

✅ Useful for **research** on domain-adaptation, parameter-efficient fine-tuning, and the failure modes of synthetic-data pipelines
✅ Structurally sound with no data leakage
✅ Balanced across core study-abroad topics
✅ **Audit artifacts are released** for the v4 source-verified factuality finding (see `docs/audit/v4-dataset-factuality-catalog.md` in the parent repo)

### What This Dataset Is NOT (and v4 documented as such)

❌ **Not an authoritative advising source.** The v4 audit found that **roughly 28–40% of training answers contain a verifiable factual error** (Wilson 95% CI [16%, 55%]; n=40). The errors are confident fabrication of citable-sounding specifics — the signature of a 2023-era generator on a template cross-product with no fact-gate.
❌ **Not factuality-gated.** No stage of the generation pipeline checks the Gemini-generated claims against authoritative sources. The `quality_validator` checks structure/length/dedup only.
❌ **Not a replacement for professional guidance.** Use for experimental/research purposes only.
❌ **Not a safe model to deploy as an advising system.** The companion LoRA fine-tune (`millat/StudyAbroadGPT-7B-LoRa-Kaggle`) inherits these errors: v4 §4.3.1 found 4 source-verified factual errors from the fine-tuned model on policy-sensitive prompts (healthcare, admissions, scholarships) against zero for the un-fine-tuned base.

### Recommended Usage

- **Training**: ✅ For research on LoRA fine-tuning and the limits of synthetic data
- **Research**: ✅ For studying the failure mode documented in arXiv:2504.15610v4
- **Experimentation**: ✅ For prototyping domain-specific assistants under controlled conditions
- **Production without factuality-gating or retrieval**: ❌ **Not recommended**
- **Official policy guidance**: ❌ **Do not use directly**

## 📥 Loading the Dataset

### With Hugging Face `datasets` Library

```python
from datasets import load_dataset

# Load the entire dataset
dataset = load_dataset("millat/StudyAbroadGPT-Dataset")

# Access splits
train_data = dataset["train"]
test_data = dataset["test"]

# Iterate through conversations
for conversation in train_data:
    for turn in conversation["conversations"]:
        print(f"{turn['from']}: {turn['value'][:100]}...")
```

## 📈 Downstream Evaluation

Per arXiv:2504.15610v4 §4.3:
- Base model: `mistralai/Mistral-7B-Instruct-v0.3`
- LoRA model: `millat/StudyAbroadGPT-7B-LoRa-Kaggle` (merged)
- 50-prompt deterministic held-out evaluation
- Source-verified factuality audit: 4 LoRA errors vs 0 base on policy-sensitive prompts

## 📝 Citation

If you use this dataset, please cite the v4 paper:

```bibtex
@article{hosen2026finetuning,
  author = {Hosen, Md Millat},
  title = {Fine-Tuning a 7B Advisor on Free-Tier GPUs: An Adapter-Handoff Recipe and a Synthetic-Data Reliability Caution},
  journal = {arXiv preprint arXiv:2504.15610v4},
  year = {2026},
  doi = {10.48550/arXiv.2504.15610}
}
```

## 🔐 License

[MIT License](https://opensource.org/licenses/MIT) — Free for commercial and educational use with attribution.

---

**Last Updated**: September 2026 (v4 reconciliation: 3-epoch, 41.9M params, Apache 2.0, audit complete)  
**Dataset Version**: 1.0  
**Companion Paper**: arXiv:2504.15610v4
