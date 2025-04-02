# Weights & Biases (WandB) Integration Guide for StudyAbroadGPT

## Table of Contents
- [Setup Instructions](#setup-instructions)
- [Metric Tracking](#metric-tracking)
- [Dashboard Navigation](#dashboard-navigation)
- [Report Generation](#report-generation)

## Setup Instructions

### 1. Installation
```bash
pip install wandb
```

### 2. Authentication in Kaggle
```python
# In your Kaggle notebook
from kaggle_secrets import UserSecretsClient
user_secrets = UserSecretsClient()
wandb_key = user_secrets.get_secret("WANDB_API_KEY")
os.environ["WANDB_API_KEY"] = wandb_key
```

### 3. Project Initialization
```python
# Initialize WandB project
wandb.init(
    project="StudyAbroadGPT",
    name="StudyAbroadGPT-7B"
)
```

## Metric Tracking

### 1. Training Configuration
```python
training_args = TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_ratio=0.03,
    num_train_epochs=5,
    learning_rate=2e-4,
    logging_steps=1,
    optim="adamw_8bit",
    max_grad_norm=0.3,
    lr_scheduler_type="linear",
    output_dir="outputs",
    report_to="wandb"
)
```

### 2. Automatically Tracked Metrics
- Training loss
- Learning rate schedule
- Gradient norms
- GPU memory usage
- Training speed

### 3. Quality Metrics
```python
quality_metrics = {
    "length": len(response.split()),
    "has_markdown": "##" in response,
    "has_action_steps": "Action Steps" in response,
    "has_examples": "example" in response.lower()
}
```

### 4. Test Results Structure
```python
test_results = {
    "topic": {
        "prompt": "Input query",
        "response": "Generated text",
        "metrics": {
            "length": int,
            "has_markdown": bool,
            "has_action_steps": bool,
            "has_examples": bool
        }
    }
}
```

## Dashboard Navigation

### 1. Accessing Results
1. Visit `wandb.ai`
2. Navigate to project "StudyAbroadGPT"
3. Select run "StudyAbroadGPT-7B"

### 2. Available Views

#### Training Progress
- Loss curves
- Learning rate schedule
- Gradient tracking
- Speed metrics

#### Quality Assessment
- Response lengths
- Format compliance rates
- Content quality metrics
- Topic coverage

#### System Monitoring
- GPU memory usage
- Training throughput
- Resource utilization

### 3. Interactive Features
- Zoom in/out on charts
- Filter data points
- Export metrics
- Compare runs

## Report Generation

### 1. Available Metrics

#### Training Statistics
```python
wandb.log({
    "training_stats": trainer_stats,
    "test_results": test_results
})
```

#### Quality Metrics
- Response length distribution
- Markdown format compliance
- Action steps inclusion
- Example usage

### 2. Exporting Data

#### Download Options
1. CSV format
   - Training metrics
   - Quality scores
   - System stats

2. JSON format
   - Complete run data
   - Test results
   - Configuration

3. Visualization exports
   - PNG charts
   - Interactive HTML
   - SVG graphics

### 3. Sharing Results

#### Collaboration Features
1. Share Links
   - Project view
   - Specific runs
   - Custom charts

2. Team Access
   - View permissions
   - Download rights
   - Comment access

## Best Practices

### 1. Monitoring Training
- Check loss curves regularly
- Monitor resource usage
- Track quality metrics

### 2. Quality Assessment
- Review response examples
- Check format compliance
- Analyze topic coverage

### 3. Resource Management
- Monitor GPU usage
- Track memory allocation
- Optimize based on metrics

## Troubleshooting

### Common Issues
1. Authentication
   - Verify WANDB_API_KEY in Kaggle secrets
   - Check environment variable setup
   - Confirm internet connectivity

2. Logging
   - Verify `report_to="wandb"` in TrainingArguments
   - Check logging_steps value
   - Confirm metric format

### Support Resources
- WandB Documentation: https://docs.wandb.ai
- GitHub Issues: https://github.com/wandb/wandb/issues
- Community Forums: https://community.wandb.ai
