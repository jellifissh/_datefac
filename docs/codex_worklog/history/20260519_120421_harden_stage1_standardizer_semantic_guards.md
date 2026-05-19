# Codex Worklog - Latest

## task_title
Harden Stage 1 sandbox standardizer semantic guards

## started_at
2026-05-19 11:20:00

## finished_at
2026-05-19 12:04:21

## git_commit_before
86fa8cf

## git_commit_after
pending

## commands_run
- git -C D:\_datefac fetch origin
- git -C D:\_datefac pull origin main
- Read D:\_datefac\docs\ai_handoff\NEXT_CODEX_TASK.md
- D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --help
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --standardize-sandbox --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 --delivery-dir D:\_datefac\output\delivery_package --strict-scope
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json

## files_read
- D:\_datefac\docs\ai_handoff\NEXT_CODEX_TASK.md
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02A_????????.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02_?????????.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\05_stage1_core_metric_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\stage1_sandbox_asset_summary.xlsx
- D:\_datefac\output\delivery_package\27_stage1_pdfplumber_selected_samples_manifest.json

## files_changed
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
- D:\_datefac\docs\codex_worklog\LATEST.md
- D:\_datefac\docs\codex_worklog\history\20260519_120421_harden_stage1_standardizer_semantic_guards.md

## files_generated
- D:\_datefac\output\delivery_package\33_stage1_standardizer_semantic_guard_log.md
- D:\_datefac\output\delivery_package\33_stage1_standardizer_semantic_guard_log.xlsx
- D:\_datefac\output\delivery_package\34_stage1_standardizer_semantic_guard_evaluation.md
- D:\_datefac\output\delivery_package\34_stage1_standardizer_semantic_guard_evaluation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\05_stage1_standardized_core_metric_trial.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\05_stage1_standardizer_diagnostics.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\stage1_standardizer_trial_summary.xlsx

## sandbox_standardizer_status
WARN

## per_sample_status_summary
- S1 (H3_AP202605141822317484_1 / ????): WARN_SEMANTIC_GUARD, metric_rows=4, manual_review_candidate_rows=82
- S2 (H3_AP202605121822223662_1 / ????): WARN_NO_METRICS, metric_rows=0, manual_review_candidate_rows=0
- S3 (H3_AP202605141822318060_1 / ????): WARN_SEMANTIC_GUARD, metric_rows=40, manual_review_candidate_rows=81

## semantic_guard_summary
- source_row_semantic_risk_count=94
- broad_keyword_unsafe_count=0
- forbidden_source_label_count=56

## duplicate_arbitration_summary
- duplicate_metric_year_groups_before=61
- duplicate_metric_year_groups_after=0
- remaining_likely_core_duplicates_count=0

## result_summary
Hardened sandbox standardizer semantic guards with source-label extraction, forbidden source-label filtering, valuation/rate guardrails, risky-row demotion, and deterministic duplicate arbitration. Rerun stayed sandbox-only and kept production delivery files unchanged.

## remaining_issues
- S1 and S3 remain WARN_SEMANTIC_GUARD due to many rows routed to manual review by stricter guards.
- S2 remains WARN_NO_METRICS and needs dedicated extraction strategy.

## next_step_suggestion
Add metric-specific positive source-label allowlists and table-role priors for S1/S3 to recover safe likely_core rows without reintroducing semantic leakage.

## safety_notes
- Did not run factory_core.py.
- Did not trigger marker/surya/vision/PaddleOCR.
- Did not download model.safetensors or any model.
- Did not reprocess PDFs; used existing trial assets only.
- Production 01/02/02A/06 remained unchanged.
- Did not commit output artifacts.
