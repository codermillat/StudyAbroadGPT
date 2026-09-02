# Stage 4.5 Final Integrity Report — `main_revised.tex`

Independent from-scratch verification of citations, numbers, and the 7-mode AI
research failure checklist. **Result: PASS** (one issue found and fixed; one
disclosed limitation; no blocking failure modes).

## Phase 1 — References (citation hallucination)
All 11 references are real, well-known works with correct identifiers:
brown2020 (2005.14165), cha2024 (Applied Sciences 14:9 3672), dettmers2023
(2305.14314), frantar2022 (2210.17323), hu2021 (2106.09685), ippolito2020 (ACL
2020), jiang2023 (2310.06825), kaur2022 (GUCON 2022), unsloth2024 (GitHub),
zhao2023 (2303.18223), zheng2023 (2306.05685, MT-Bench — added for LLM-as-judge).
**No fabricated citations.** PASS.

## Phase 2 — Numbers traced to artifacts
| Claim | Source | Status |
|---|---|---|
| P100 1.0125→0.4787, 284 steps, min 0.4109 | `Report_P100/train/train-loss.csv` | ✅ |
| T4 →0.3405, best 0.2963, 142 steps | `Report_T4/train/loss__MAX.csv` | ✅ |
| Peak VRAM 15.888 / 14.741 GB; times | `Report_P100/report.txt`, `Report_T4/report.txt` | ✅ |
| Eff. batch 8 (2×4) / 32 (4×8) | report.txt (both) | ✅ (fixed §4.1 inconsistency) |
| LoRA r16/α32/drop0/224 modules/41.9M/0.60% | `adapter_config.json` | ✅ |
| Dataset 2676/2274/402, 6941+6941 turns, 5.19±0.98, distinct 0.0054/0.1111 | `Dataset_dataset_quality_metrics.json` | ✅ |
| 256 truncation 96%/96% | `Model_automatic_sanity_metrics.csv` | ✅ |
| 512 truncation 24%/20% | `automatic_sanity_metrics_512.csv` | ✅ |
| SacreBLEU 5.71/9.05; ROUGE-L 0.1937/0.2125 (+0.0188 [.0098,.0284]); BERTScore 0.0981/0.1611 (+0.0631 [.0473,.0785]) | `Model_standard_nlp_metrics_summary_512.md` | ✅ |
| Judge domain 2.14/1.74 (−0.40 [−0.62,−0.18]); help 2.14/1.82 (−0.32 [−0.52,−0.12]); pref 23/9/18 | `Model_llm_judge_summary.md` | ✅ |
| Factuality 4 LoRA errors / 0 base; 16 vs 2 of 18 divergent | `Model_factuality_error_catalog.md` + web sources | ✅ |

**Issue found & fixed:** adapter size was stated as "~168 MB" (unverifiable — on-disk
file is a git-LFS pointer). Replaced with the verified parameter count (41.9M) and
an honest size range. No other unverifiable specifics.

## Phase 3 — 7-Mode AI Research Failure Checklist (v3.2)
1. **Citation hallucination** — CLEAR (Phase 1).
2. **Implementation bugs** — CLEAR. Eval scripts released and deterministic; numbers reproduce from artifacts.
3. **Hallucinated results** — CLEAR. Every number traces to a file; factuality verdicts web-sourced.
4. **Shortcut reliance** — N/A.
5. **Bug-as-insight** — CLEAR with disclosed limitation. The reliability finding does not rest on the LLM-judge alone; the judgment-free factuality audit independently corroborates it. Single-judge fragility is disclosed (Section 5.2).
6. **Methodology fabrication** — CLEAR. The false "optimizer-state transferred" claim and the "controlled variable" claim were removed to match the released code.
7. **Pipeline frame-lock** — CLEAR. The original "quantization-boundary" frame was abandoned in favor of what the data supports.

**No mode SUSPECTED.** One disclosed limitation (single-judge reliability signal,
mitigated by the independent factuality audit). Per protocol, user acknowledgment
of this checklist is required before finalization.
