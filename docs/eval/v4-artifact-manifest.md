# Artifact Manifest

All files listed below are expected outputs. Paths reflect the existing location if found.
- evaluation_prompts.csv: Held-out prompts used for generation. (/content/drive/MyDrive/LoRA_Paper/outputs/evaluation_prompts.csv)
- base_model_outputs.csv: Base model responses and metadata. (/content/drive/MyDrive/LoRA_Paper/outputs/base_model_outputs.csv)
- lora_model_outputs.csv: LoRA/merged model responses and metadata. (/content/drive/MyDrive/LoRA_Paper/outputs/lora_model_outputs.csv)
- downstream_raw_model_outputs.csv: Merged base/LoRA outputs and timing metadata. (/content/drive/MyDrive/LoRA_Paper/outputs/downstream_raw_model_outputs.csv)
- downstream_generation_metadata.csv: Generation-time metadata for both models. (/content/drive/MyDrive/LoRA_Paper/outputs/downstream_generation_metadata.csv)
- downstream_blinded_evaluation.csv: Blinded A/B evaluation sheet for manual scoring. (/content/drive/MyDrive/LoRA_Paper/outputs/downstream_blinded_evaluation.csv)
- downstream_blinded_mapping_revealed.csv: Revealed A/B mappings after scoring. (/content/drive/MyDrive/LoRA_Paper/outputs/downstream_blinded_mapping_revealed.csv)
- automatic_sanity_metrics.csv: Length, timing, and truncation diagnostics. (/content/drive/MyDrive/LoRA_Paper/outputs/automatic_sanity_metrics.csv)
- downstream_post_scoring_analysis.csv: Post-scoring analysis outputs (if scored). (/content/drive/MyDrive/LoRA_Paper/outputs/downstream_post_scoring_analysis.csv)
- evaluation_config.json: Configuration and reproducibility metadata. (/content/drive/MyDrive/LoRA_Paper/outputs/evaluation_config.json)
- domain_specificity_metrics.csv: Domain term coverage metrics (this section). (/content/outputs/domain_specificity_metrics.csv)
- qualitative_flags.csv: Flagged long/short/caveat/risk responses. (/content/outputs/qualitative_flags.csv)
- final_experimental_summary.md: Auto-generated experimental summary. (/content/outputs/final_experimental_summary.md)
- artifact_manifest.md: This manifest of outputs. (/content/outputs/artifact_manifest.md)