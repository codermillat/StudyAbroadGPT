# StudyAbroadGPT: LoRA Fine-Tuning on Mistral-7B

Complete training and inference pipeline for fine-tuning Mistral-7B-Instruct with LoRA for domain-specific study-abroad guidance using Kaggle GPUs and Weights & Biases integration.

## 🔗 Ecosystem

| Component | Link |
|-----------|------|
| Dataset | [millat/StudyAbroadGPT-Dataset](https://huggingface.co/datasets/millat/StudyAbroadGPT-Dataset) |
| Model Card | [millat/StudyAbroadGPT-7B-LoRa-Kaggle](https://huggingface.co/millat/StudyAbroadGPT-7B-LoRa-Kaggle) |
| Dataset Generation | [codermillat/study-abroad-dataset](https://github.com/codermillat/study-abroad-dataset) |
| Evaluation Companion | [LoRA Paper workspace](https://github.com/codermillat/StudyAbroadGPT/tree/main) |
| Paper | [arXiv:2504.15610](https://arxiv.org/abs/2504.15610) |

## 📊 Quick Facts

- **Base Model**: `mistralai/Mistral-7B-Instruct-v0.3`
- **Quantization**: 4-bit NF4 via Unsloth
- **Training Method**: LoRA (Low-Rank Adaptation)
- **LoRA Rank**: 16, Alpha: 32
- **Target Modules**: Attention (q_proj, k_proj, v_proj, o_proj) + FFN (gate_proj, up_proj, down_proj)
- **Training Data**: 2,274 synthetic study-abroad conversations
- **Training Time**: ~4-5 epochs
- **Memory Footprint**: ~8GB model + 4GB training buffer
- **Hardware**: Tesla T4 or P100 GPU (Kaggle/Colab)

## 📁 Repository Structure

```
StudyAbroadGPT/
├── Study_Abroad_GPT.ipynb              # Main training notebook (Colab)
├── Study_Abroad_GPT_Kaggle-T4.ipynb    # Kaggle T4 optimized training
├── Study_Abroad_GPT_Kaggle-P100.ipynb  # Kaggle P100 optimized training
├── StudyAbroadGPT_Inference.ipynb      # Inference and testing notebook
├── architecture.md                      # Technical architecture documentation
├── WANDB.md                             # Weights & Biases integration guide
├── training_analysis.md                 # Training metrics and loss analysis
├── paper.md / paper_v2.md               # Paper drafts and methodology
├── conclusions.md                       # Research findings and conclusions
├── documentation.md                     # General documentation
├── readme-dataset.md                    # Dataset-specific notes
├── Report_T4/                           # WandB reports from T4 runs
└── Report_P100/                         # WandB reports from P100 runs
```

## 🚀 Quick Start

### Prerequisites

```bash
pip install transformers peft torch bitsandbytes unsloth
pip install wandb  # for training monitoring
```

### Training on Kaggle

1. Open `Study_Abroad_GPT_Kaggle-T4.ipynb` (or P100 variant) in Kaggle
2. Add your Hugging Face and WandB API keys as Kaggle secrets
3. Run all cells

```python
# Key training parameters
training_args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_ratio=0.03,
    num_train_epochs=4,
    learning_rate=2e-4,
    logging_steps=1,
    optim="adamw_8bit",
    max_grad_norm=0.3,
    output_dir="outputs",
    report_to="wandb"
)
```

### Inference

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import AutoPeftModelForCausalLM

# Load merged model
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

# Generate response
prompt = "What documents do I need for a student visa?"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=256)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

Or use the inference notebook: `StudyAbroadGPT_Inference.ipynb`

## 🏗️ Technical Architecture

### Model Configuration

| Component | Setting |
|-----------|---------|
| Model | Mistral-7B-Instruct-v0.3 |
| Quantization | 4-bit NF4 (Unsloth) |
| Sequence Length | 2048 tokens |
| Model Memory | ~8 GB |
| LoRA Rank | 16 |
| LoRA Alpha | 32 |
| Trainable Parameters | ~4.7M (vs 7B total) |

### Memory Optimization

- **Model Layer**: 8GB (4-bit quantized parameters + LoRA adapters)
- **Training Layer**: 4GB (gradient accumulation, optimizer states)
- **Buffer Layer**: 2GB (forward/backward computation, temp storage)

### Training Loop

```
Data Pipeline → Preprocessing → Training Loop → Evaluation
                                     ↓
                          Gradient Accumulation (4 steps)
                          Learning Rate Scheduling
                          Loss Tracking (WandB)
```

## 📈 Monitoring with Weights & Biases

Training runs are logged to WandB project `StudyAbroadGPT`. Track:

- Training loss curves
- Learning rate schedule
- GPU memory usage
- Gradient norms
- Training speed (tokens/sec)
- Quality metrics per batch

Access reports in `Report_T4/` and `Report_P100/` directories.

## 📊 Evaluation Results

From companion evaluation artifacts (50-sample lightweight run):

- **Base model avg response length**: 1151.88 chars
- **LoRA avg response length**: 1178.74 chars (+26.86)
- **Domain-specific term coverage**:
  - University: base 48%, LoRA 42%
  - Tuition: base 12%, LoRA 22%
  - Scholarship: base 20%, LoRA 16%

**Status**: Manual blinded scoring and factuality audit still pending.

## 📖 Documentation

- **[architecture.md](architecture.md)** — Technical details, memory management, model pipeline
- **[WANDB.md](WANDB.md)** — Setting up monitoring and accessing training reports
- **[training_analysis.md](training_analysis.md)** — Loss analysis, convergence metrics, resource profiling
- **[paper.md](paper.md) / [paper_v2.md](paper_v2.md)** — Research methodology and findings
- **[conclusions.md](conclusions.md)** — Key insights and recommendations
- **[documentation.md](documentation.md)** — General setup and usage guide
- **[readme-dataset.md](readme-dataset.md)** — Dataset-specific notes and preprocessing

## 🎯 Key Features

- ✅ **Parameter-Efficient** — LoRA reduces trainable params to ~4.7M
- ✅ **Memory-Efficient** — Runs on T4 (16GB) with 4-bit quantization
- ✅ **Production-Ready** — Merged weights in HuggingFace model card
- ✅ **Reproducible** — Fixed seed, deterministic generation
- ✅ **Monitored** — Full WandB integration for training transparency
- ✅ **Domain-Focused** — 2274 synthetic study-abroad conversations
- ✅ **Inference-Optimized** — Unsloth for faster generation

## 🛠️ Hardware Requirements

| GPU | RAM | Time | Status |
|-----|-----|------|--------|
| Tesla T4 | 16GB | ~3-4 hours | ✅ Tested |
| Tesla P100 | 16GB+ | ~1-2 hours | ✅ Tested |
| A100 | 40GB+ | <1 hour | Should work |

**Note**: Training on CPU is not recommended. Kaggle provides free GPU access.

## 📝 Citation

If you use this code or model, please cite:

```bibtex
@article{hosen2025lora,
  title={A LoRA-Based Approach to Fine-Tuning LLMs for Educational Guidance in Resource-Constrained Settings},
  author={Hosen, Md Millat},
  journal={arXiv preprint arXiv:2504.15610},
  year={2025},
  doi={10.48550/arXiv.2504.15610}
}
```

## 🔐 License

Apache 2.0

## ⚠️ Important Notes

- This is a domain-adapted model for experimental use. Validate all outputs against official university and immigration sources before operational use.
- The model is not a replacement for official advising.
- Use in production should include additional validation and factuality checking.

## 📧 Questions?

Open an issue on GitHub or check the companion evaluation artifacts in the LoRA Paper workspace.
