# Codex Worklog - Latest

## task_title
Run Stage 1 controlled three-sample expansion

## started_at
2026-05-18 22:23:45

## finished_at
2026-05-18 22:28:15

## git_commit_before
0beb824

## git_commit_after
pending

## commands_run
- git -C D:\_datefac fetch origin
- git -C D:\_datefac pull origin main
- git -C D:\_datefac status --short
- git -C D:\_datefac log --oneline --decorate -8
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\probe_pdf_tables.py --pdf D:\_datefac\input\H3_AP202605141822317484_1.pdf --output D:\_datefac\output\H3_AP202605141822317484_1_资产包\_stage1_probe --pages all
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\probe_pdf_tables.py --pdf D:\_datefac\input\H3_AP202605121822223662_1.pdf --output D:\_datefac\output\H3_AP202605121822223662_1_资产包\_stage1_probe --pages all
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\probe_pdf_tables.py --pdf D:\_datefac\input\H3_AP202605141822318060_1.pdf --output D:\_datefac\output\H3_AP202605141822318060_1_资产包\_stage1_probe --pages all
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json

## selected_samples
- H3_AP202605141822317484_1.pdf
- H3_AP202605121822223662_1.pdf
- H3_AP202605141822318060_1.pdf

## baseline_sample
- H3_AP202605091822098939_1.pdf

## entrypoints_used
- D:\_datefac\tools\probe_pdf_tables.py (safe non-vision probe entrypoint)

## files_generated
- D:\_datefac\output\H3_AP202605141822317484_1_资产包\16_stage1_execution_log.md
- D:\_datefac\output\H3_AP202605141822317484_1_资产包\16_stage1_execution_log.xlsx
- D:\_datefac\output\H3_AP202605141822317484_1_资产包\17_stage1_result_evaluation.md
- D:\_datefac\output\H3_AP202605141822317484_1_资产包\17_stage1_result_evaluation.xlsx
- D:\_datefac\output\H3_AP202605121822223662_1_资产包\16_stage1_execution_log.md
- D:\_datefac\output\H3_AP202605121822223662_1_资产包\16_stage1_execution_log.xlsx
- D:\_datefac\output\H3_AP202605121822223662_1_资产包\17_stage1_result_evaluation.md
- D:\_datefac\output\H3_AP202605121822223662_1_资产包\17_stage1_result_evaluation.xlsx
- D:\_datefac\output\H3_AP202605141822318060_1_资产包\16_stage1_execution_log.md
- D:\_datefac\output\H3_AP202605141822318060_1_资产包\16_stage1_execution_log.xlsx
- D:\_datefac\output\H3_AP202605141822318060_1_资产包\17_stage1_result_evaluation.md
- D:\_datefac\output\H3_AP202605141822318060_1_资产包\17_stage1_result_evaluation.xlsx

## files_modified
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/20260518_222815_run_stage1_controlled_three_sample_expansion.md

## final_delivery_status
- overall_status: PASS
- pass_count: 17
- warn_count: 0
- fail_count: 0

## final_stage1_status
PASS

## stop_condition_checks
- model.safetensors download: not triggered
- marker/surya/vision/PaddleOCR backend trigger: not triggered
- factory_core.py trigger: not triggered
- duplicate_key_count_final: 0
- high_risk_flags: 0
- test_token_hits: 0
- output file lock conflict: none detected
- selected sample missing: none

## result_summary
- Controlled execution completed for exactly three Stage 1 samples, one by one.
- Safe non-vision entrypoint was used for all runs.
- Per-sample 16/17 execution and evaluation reports were generated.
- Delivery health remained clean after execution.
- Baseline 091 was not processed as a new sample and remained untouched.

## remaining_issues
- Some optional probe backends reported dependency_missing in sample-level logs; this did not impact stop conditions.

## next_step_suggestion
- Start Stage 1 quality review using generated 16/17 reports, then decide whether to promote selected sample outputs into broader regression runs.

## safety_notes
- Did not run factory_core.py.
- Did not trigger marker/surya/vision/PaddleOCR.
- Did not download model.safetensors.
- Did not modify production delivery files 01/02/02A/06.
- Did not commit output artifacts.
