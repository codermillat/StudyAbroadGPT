# Final Experimental Summary

## Models and Data
- Base model: mistralai/Mistral-7B-Instruct-v0.3
- LoRA model: millat/StudyAbroadGPT-7B-LoRa-Kaggle (subfolder: merged)
- Dataset: millat/StudyAbroadGPT-Dataset (split: test)
- Sample size: 50

## Generation Settings
- Deterministic generation: True
- Generation config: {'max_new_tokens': 256, 'do_sample': False, 'temperature': 0.0, 'top_p': 1.0}

## Evaluation Setup
- Blinded evaluation CSV: yes
- Manual scoring completed: no

## Automatic Qualitative Findings
- Avg response length (chars): base 1151.88, LoRA 1178.74 (diff +26.86)
- Bullet/list usage: base 92.0%, LoRA 96.0%
- Caveat phrase usage: base 2.0%, LoRA 0.0%

- Top domain terms by coverage:
  - base: university (48.0%), scholarship (20.0%), admission (20.0%)
  - lora: university (42.0%), tuition (22.0%), scholarship (16.0%)

## Limitations
- No inter-rater agreement is measured.
- No completed factuality verification is included.
- Qualitative findings are exploratory.
- Downstream behavioral improvement is not claimed unless manually validated.