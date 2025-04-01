# StudyAbroadGPT Training Documentation

This guide explains how to use the StudyAbroadGPT training notebook on Kaggle, including API setup, dataset configuration, and model publishing.

## Table of Contents
- [Prerequisites](#prerequisites)
- [API Configuration](#api-configuration)
- [Dataset Setup](#dataset-setup)
- [Training Configuration](#training-configuration)
- [Model Publishing](#model-publishing)

## Prerequisites

### Required Accounts and Access
1. Kaggle Account with GPU access
2. Hugging Face Account
3. Weights & Biases Account
4. Access to StudyAbroadGPT Dataset

### Hardware Requirements
- GPU: Tesla T4 (Kaggle)
- RAM: 16GB
- Storage: 20GB minimum

## API Configuration

### 1. Kaggle API Setup
1. Generate Kaggle API token:
   - Go to [Kaggle Settings](https://www.kaggle.com/settings)
   - Scroll to "API" section
   - Click "Create New API Token"
   - Save `kaggle.json` file

2. Configure credentials:
```bash
# Linux/Mac
mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows
mkdir %USERPROFILE%\.kaggle
copy kaggle.json %USERPROFILE%\.kaggle\
```

### 2. Hugging Face Setup
1. Create access token:
   - Visit [HF Settings](https://huggingface.co/settings/tokens)
   - Click "New token"
   - Select "write" access
   - Copy token value

2. Add to Kaggle secrets:
   - Go to Kaggle Settings > Secrets
   - Add new secret:
     - Name: `HF_TOKEN`
     - Value: `your_huggingface_token`

### 3. WandB Configuration
1. Get WandB API key:
   - Sign up at [wandb.ai](https://wandb.ai)
   - Go to Settings > API Keys
   - Copy API key

2. Add to Kaggle secrets:
   - Add new secret:
     - Name: `WANDB_KEY`
     - Value: `your_wandb_key`

## Dataset Setup

### Using StudyAbroadGPT Dataset
```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("millat/StudyAbroadGPT-Dataset", split="train")
```

### Custom Dataset Format
Your dataset should follow this structure:
```json
{
    "conversations": [
        {
            "human": "Question about studying abroad",
            "assistant": "Detailed response with markdown formatting"
        }
    ]
}
```

### Data Processing
1. Format requirements:
   - Human queries marked with "Human: "
   - Assistant responses marked with "Assistant: "
   - Include EOS token after assistant responses
   - Use markdown formatting for structure

2. Dataset processing code:
```python
def format_prompt(examples):
    texts = []
    for conversation in examples["conversations"]:
        full_text = ""
        for turn in conversation:
            if turn["from"] == "human":
                full_text += f"Human: {turn['value']}\n\n"
            else:
                full_text += f"Assistant: {turn['value']}{tokenizer.eos_token}\n\n"
        texts.append(full_text.strip())
    return {"text": texts}

dataset = dataset.map(format_prompt, batched=True, remove_columns=dataset.column_names)
```

## Training Configuration

### Model Settings
```python
model_config = {
    "base_model": "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    "max_seq_length": 2048,
    "load_in_4bit": True,
    "lora_r": 16,
    "lora_alpha": 32
}
```

### Training Parameters
```python
training_args = {
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 4,
    "num_train_epochs": 4,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.03,
    "max_grad_norm": 0.3
}
```

## Model Publishing

### 1. Save Model Locally
```python
model.save_pretrained_merged(
    "StudyAbroadGPT-7B",
    tokenizer,
    save_method="merged_16bit",
    safe_serialization=True
)
```

### 2. Push to Hugging Face
```python
model.push_to_hub_merged(
    "your-username/StudyAbroadGPT-7B",
    tokenizer=tokenizer,
    save_method="merged_16bit",
    use_auth_token=hf_token,
    private=False
)
```

### 3. Create Kaggle Dataset
```python
# Configure metadata
dataset_metadata = {
    "title": "StudyAbroadGPT-7B",
    "id": f"{username}/studyabroad-gpt-model",
    "licenses": [{"name": "MIT"}]
}

# Create dataset
!kaggle datasets create -p ./model_output
```

## Troubleshooting

### Common Issues
1. Memory Errors:
   - Use gradient checkpointing
   - Reduce batch size
   - Enable 4-bit quantization

2. API Authentication:
   - Verify secret names match exactly
   - Check token permissions
   - Ensure tokens are current

3. Training Issues:
   - Monitor GPU memory usage
   - Check learning rate
   - Validate dataset format

### Support
- Report issues on GitHub
- Join Discord community
- Check documentation updates

## Contributing
Feel free to contribute by:
1. Reporting bugs
2. Suggesting improvements
3. Submitting pull requests
4. Sharing training configs
