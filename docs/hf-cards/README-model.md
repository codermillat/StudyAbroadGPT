---
license: apache-2.0
base_model: mistralai/Mistral-7B-Instruct-v0.3
tags:
- unsloth
- mistral
- lora
- education
- study-abroad
- parameter-efficient-tuning
- domain-adaptation
- nlp
- kaggle
datasets:
- millat/StudyAbroadGPT-Dataset
library_name: transformers
---

# StudyAbroadGPT-7B-LoRa-Kaggle

Parameter-efficient LoRA-adapted Mistral-7B-Instruct-v0.3 fine-tuned on synthetic study-abroad conversational data for domain-specific academic advising guidance.

**Status**: Generation and source-verified factuality audit complete ✅ (per arXiv:2504.15610v4 §4.3) | Caveat Phrase Usage regression flagged in §5.1

## ⚠️ Important Disclaimers (read first)

This model is a **research artifact documenting a failure mode**, not a deployable advising system. By the v4 §4.3.1 source-verified audit, the model produces **4 confident factual errors on policy-sensitive topics** (healthcare, admissions, scholarships) against zero for the un-fine-tuned base on the same prompts. The training data is the cause, not the fine-tuning method (see v4 §4.4).

**Do not deploy as a student-advising system without prior factuality-gating or retrieval grounding against authoritative sources.** Institutional deployment is particularly discouraged.

## 🔗 Project Ecosystem

| Resource | Link |
|----------|------|
| Dataset | [millat/StudyAbroadGPT-Dataset](https://huggingface.co/datasets/millat/StudyAbroadGPT-Dataset) |
| Training Code | [codermillat/StudyAbroadGPT](https://github.com/codermillat/StudyAbroadGPT) |
| Dataset Generation | [codermillat/study-abroad-dataset](https://github.com/codermillat/study-abroad-dataset) |
| Evaluation Artifacts | [LoRA Paper evaluation workspace](https://github.com/codermillat/LoRA-Paper) |
| Research Paper | [arXiv:2504.15610](https://arxiv.org/abs/2504.15610) |
| Author ORCID | [0009-0005-7198-9893](https://orcid.org/0009-0005-7198-9893) |

## 📊 Model Details

### Architecture

| Component | Specification |
|-----------|---|
| **Base Model** | `mistralai/Mistral-7B-Instruct-v0.3` |
| **Base Model Size** | 7.24 billion parameters |
| **Quantization** | 4-bit NF4 (via Unsloth) |
| **Fine-Tuning Method** | LoRA (Low-Rank Adaptation) |
| **LoRA Rank (r)** | 16 |
| **LoRA Alpha (α)** | 32 |
| **Scaling Factor** | α / r = 2.0 |

### Trainable Parameters (verified against `adapter_config.json`)

- **Total Model Parameters**: 7,241,731,200
- **LoRA Trainable Parameters**: **41,943,040** (0.60% of base model)
- **LoRA Adapters**: Applied to all linear projections (q, k, v, o, gate, up, down) of all 32 transformer layers
- **Note**: an earlier v1/v2-era model card reported ~4.7M trainable params (attention-only); the v4 paper and `adapter_config.json` confirm the full 41.9M across all 7 target modules per layer.

### Quantization Details

- **Method**: 4-bit NF4 quantization via Unsloth (with double quantization)
- **Memory**: ~5.5 GB at 4-bit (vs ~14 GB at fp16)
- **Benefit**: Enables fine-tuning on a single 16 GB GPU

## 🎯 Training Details

### Training Data

- **Dataset**: [millat/StudyAbroadGPT-Dataset](https://huggingface.co/datasets/millat/StudyAbroadGPT-Dataset)
- **Training Samples**: 2,274 conversations
- **Test Samples**: 402 conversations
- **Topics Covered**: Admissions, scholarships, visas, accommodation, cultural adaptation
- **Generator**: Gemini 1.0 Pro (December 2023-era); see the dataset card and arXiv:2504.15610v4 §4.4 for the source-verified factuality audit (28–40% data error rate, n=40).

### Training Configuration (verified, v4 §3.2 + `adapter_config.json`)

| Parameter | Value |
|-----------|-------|
| **Total Epochs** | **3** (1 P100 + 2 T4) |
| **Batch Size (P100 / T4)** | 2 / 4 per device |
| **Gradient Accumulation** | 4 / 8 |
| **Effective Batch Size** | 8 / 32 |
| **Learning Rate** | 2 × 10⁻⁴ |
| **Warmup Ratio** | 0.03 |
| **LR Scheduler** | Linear |
| **Max Sequence Length** | 2,048 tokens |
| **Optimizer** | AdamW 8-bit (bitsandbytes) |
| **Max Gradient Norm** | 0.3 |
| **Weight Decay** | 0.0 |
| **Mixed Precision** | bfloat16 |
| **Gradient Checkpointing** | Enabled |
| **Seed** | 42 |
| **LoRA dropout** | 0 |
| **LoRA bias** | False (none) |

> Note: an earlier v1/v2-era model card reported 4 epochs; the v4 paper and training reports confirm **3 epochs total** (1 P100 + 2 T4). The 4-epoch figure is retracted.

### Hardware & Resources

| Setting | Value |
|---------|-------|
| **Phase 1 GPU** | Tesla P100-16GB (Kaggle) |
| **Phase 1 time** | 5h 47m 25s (284 steps) |
| **Phase 1 peak VRAM** | 15.888 GB |
| **Phase 2 GPU** | Tesla T4-16GB (Kaggle) |
| **Phase 2 time** | 5h 26m 18s (142 steps × 2 epochs) |
| **Phase 2 peak VRAM** | 14.741 GB |
| **Adapter-only handoff** | Yes; optimizer and scheduler re-initialized on the second GPU |

## 🚀 Usage

### Option 1: Using Unsloth (Recommended for Inference)

```python
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="millat/StudyAbroadGPT-7B-LoRa-Kaggle",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)

FastLanguageModel.for_inference(model)

prompt = "What documents do I need for a UK student visa?"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.0,
        do_sample=False,
        top_p=1.0
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

### Option 2: Using Transformers Library (merged weights)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "millat/StudyAbroadGPT-7B-LoRa-Kaggle",
    subfolder="merged",
    torch_dtype="auto",
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained(
    "millat/StudyAbroadGPT-7B-LoRa-Kaggle",
    subfolder="merged"
)

prompt = "How much should I budget for accommodation in London?"
inputs = tokenizer(prompt, return_tensors="pt")

outputs = model.generate(
    **inputs,
    max_new_tokens=256,
    temperature=0.0,
    do_sample=False
)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### Option 3: Using LoRA Adapter (Continued Training)

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.3",
    torch_dtype="auto",
    device_map="auto"
)

model = PeftModel.from_pretrained(
    base_model,
    "millat/StudyAbroadGPT-7B-LoRa-Kaggle"
)

tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3")
```

## 📊 Evaluation Results (arXiv:2504.15610v4 §4.3)

### Source-Verified Factuality Audit (the load-bearing signal)

| Metric | Base | LoRA | Direction |
|--------|-----:|-----:|-----------|
| Source-verified factual errors on the 18/50 divergent prompts (4 highest-sensitivity cases verified) | 0 | 4 | LoRA worse on 16/18 |
| Sample size | 50 prompts | 50 prompts | (same prompts, deterministic decoding) |
| Generation settings | do_sample=False, T=0.0, top_p=1.0, max_new_tokens=512 | (same) | (matched) |

**The 4 verified LoRA errors** (all on policy-sensitive topics):
- Harvard Medical School testing: LoRA states HMS "requires all applicants to submit GRE scores"; base correctly states MCAT, not GRE. [HMS source](https://meded.hms.harvard.edu/admissions-eligibility-requirements)
- Australian healthcare: LoRA states students are "eligible for Medicare after at least six months"; base correctly states OSHC is compulsory under visa condition 8501. [Study Australia](https://www.studyaustralia.gov.au/en/plan-your-move/overseas-student-health-cover-oshc)
- "Bachelor of Medicine at Stanford": LoRA elaborates a program that does not exist; base correctly states Stanford offers no direct undergraduate medicine degree.
- Brazil→Bangladesh scholarships: LoRA fabricates named scholarship programs; base correctly states such scholarships are not common. [British Council](https://study-uk.britishcouncil.org/scholarships-funding/commonwealth-scholarships)

### Blind LLM-as-Judge (single judge family, different from data generator)

| Metric | Base | LoRA | Δ (LoRA − Base) | 95% CI on Δ |
|--------|-----:|-----:|----------------:|-------------|
| Domain accuracy (0–3) | 2.14 ± 0.53 | 1.74 ± 0.69 | −0.40 | [−0.62, −0.18] |
| Helpfulness (0–3) | 2.14 ± 0.49 | 1.82 ± 0.59 | −0.32 | [−0.52, −0.12] |
| Preference (3-way) | 23/50 (46%) | 9/50 (18%) | (tie: 18/50) | McNemar-Bowker χ²(2)=9.3, p=0.0095 |

### Reference-Based Metrics (max_new_tokens=512)

| Metric | Base | LoRA | Δ | 95% CI on Δ |
|--------|-----:|-----:|--:|-------------|
| SacreBLEU (corpus) | 5.71 | 9.05 | +3.34 | corpus-level |
| ROUGE-L F1 | 0.1937 | 0.2125 | +0.019 | [+0.010, +0.028] |
| BERTScore F1 (rescaled) | 0.0981 | 0.1611 | +0.063 | [+0.047, +0.078] |

⚠️ These reference-based gains measure **fidelity to the synthetic training distribution**, not ground-truth quality. The synthetic references themselves contain the same factual errors documented in the dataset card and v4 §4.4. Reporting BERTScore alone would invert the conclusion.

### Caveat Phrase Usage (a safety regression flagged in v4 §5.1)

| Indicator | Base | LoRA |
|-----------|-----:|-----:|
| Caveat Phrase Usage | 2.0% | **0.0%** |

The LoRA model **dropped its safety hedges** compared to base. In any deployment setting this would systematically reduce the rate at which the model flags uncertainty, which is a substantive concern for an advising model. v4 §5.1 calls this out as a finding, not just a quality metric.

## ⚠️ Important Limitations (v4 §5.2)

1. Training and evaluation data are **fully synthetic** (Gemini 1.0 Pro).
2. The LLM-as-judge is a single model, single pass, on synthetic-split prompts.
3. The factuality audit is curated (4 highest-sensitivity cases), not exhaustive.
4. The dataset prevalence rate (28–40%) rests on a single judge at n=40.
5. The two LLM-judged signals (model and dataset) are not independent.
6. The reliability finding rests on a single fine-tuning run (no seed variance).
7. Reference-based metrics use synthetic references.
8. The two-phase schedule is a recipe, not an ablation.
9. Single language and domain (English, study-abroad).

### Recommended Usage

**✅ Safe to use for**:
- Educational chatbot prototyping under controlled conditions
- Research on domain adaptation and synthetic-data failure modes
- Fine-tuning experiments (continued training)
- Data augmentation for related research tasks

**❌ NOT safe to use for**:
- Direct immigration, healthcare, or visa advice
- Official policy interpretation
- Time-sensitive information (visas, deadlines)
- High-stakes decision making without expert review and factuality-gating

## 🔄 Model Variants

| Variant | Format | Size | Use Case |
|---------|--------|------|----------|
| `/merged` | Full merged weights | ~14 GB | Inference, GGUF conversion |
| Adapter-only (this repo) | LoRA weights | ~50 MB | Continued training, fine-tuning |

## 📚 Citation

If you use this model or the v4 findings, cite the paper:

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

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) — the upstream Mistral-7B-Instruct-v0.3 license.

> Note: an earlier v1/v2-era model card stated "Mistral Research License"; the v4 paper and the upstream model card confirm **Apache 2.0**.

## 📊 Performance / Hardware Compatibility

| Device | Status | Notes |
|--------|--------|-------|
| NVIDIA T4 (16 GB) | ✅ Tested | Kaggle (Phase 2) |
| NVIDIA P100 (16 GB) | ✅ Tested | Kaggle (Phase 1) |
| NVIDIA A100 (40 GB) | Should work | Not tested |
| CPU only | ❌ Not recommended | Too slow |
| Mac M1/M2 | ⚠️ Requires setup | MPS acceleration possible |

## 🤝 Contributing & Feedback

- **Bug Reports**: Open an issue on [training repo](https://github.com/codermillat/StudyAbroadGPT)
- **Model Improvements**: PRs with new training runs or data are welcome
- **Questions**: Check the v4 paper §5 (Discussion + Limitations + Future Work) and the GitHub workspace

---

**Model Version**: 1.0 (v4 reconciliation, September 2026)  
**Adapter SHA**: matches `data/v4-adapter-config.json`  
**Training Framework**: Unsloth + Transformers + bitsandbytes  
**Base Model Lineage**: Mistral-7B → Instruct-v0.3 → 4-bit NF4 quantized → LoRA fine-tuned
