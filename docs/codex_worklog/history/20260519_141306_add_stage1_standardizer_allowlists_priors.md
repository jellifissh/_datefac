# Codex Worklog - Latest

## task_title
Add Stage 1 sandbox standardizer allowlists and table priors

## started_at
2026-05-19 12:30:00

## finished_at
2026-05-19 14:13:06

## git_commit_before
13b2197

## git_commit_after
pending

## commands_run
- git fetch origin
- git reset --hard origin/main
- Read D:\_datefac\docs\ai_handoff\NEXT_CODEX_TASK.md
- D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --help
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --standardize-sandbox --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 --delivery-dir D:\_datefac\output\delivery_package --strict-scope
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json

## files_read
- D:\_datefac\docs\ai_handoff\NEXT_CODEX_TASK.md
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02A_研报原始表格资产.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02_研报全量结构化数据.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\05_stage1_core_metric_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\stage1_sandbox_asset_summary.xlsx

## files_changed
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
- D:\_datefac\docs\codex_worklog\LATEST.md
- D:\_datefac\docs\codex_worklog\history\20260519_141306_add_stage1_standardizer_allowlists_priors.md

## files_generated
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.md
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.xlsx
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.md
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.xlsx

## sandbox_standardizer_status
WARN

## per_sample_status_summary
- S1 (H3_AP202605141822317484_1 / 三鑫医疗): WARN_SEMANTIC_GUARD, metric_rows=3, manual_review_candidate_rows=83
- S2 (H3_AP202605121822223662_1 / 冠豪高新): WARN_NO_METRICS, metric_rows=0, manual_review_candidate_rows=0
- S3 (H3_AP202605141822318060_1 / 科锐国际): WARN_SEMANTIC_GUARD, metric_rows=40, manual_review_candidate_rows=81

## allowlist_summary
- Implemented metric-specific positive source-label allowlists.
- Added source-label allowlist score and promotion_reason to standardized rows.
- safe_promotions_count=43

## table_role_prior_summary
- Implemented table-role priors from raw_tables_index + candidate rows.
- Added table_role / table_role_score / table_role_reason columns.
- rating_or_disclaimer role remains non-promotable.

## s2_no_metric_diagnosis_summary
- sample_id=S2
- raw_table_count=5
- year_evidence_count=5
- keyword_hit_examples=none
- label_fragmented_suspected=1
- recommendation=Tune extraction heuristics / AI repair / manual visual review

## result_summary
Added positive allowlist evidence and table-role priors while preserving hard-risk demotion and duplicate arbitration. Sandbox rerun stayed within trial assets and kept production guard files unchanged.

## remaining_issues
- S2 remains WARN_NO_METRICS and requires dedicated upstream extraction strategy.
- S1 remains conservative with few likely_core rows under current hard-risk constraints.

## next_step_suggestion
Add stricter row-block splitting for mixed rows and targeted allowlist expansion for S1 forecast-table labels, then rerun sandbox evaluation.

## safety_notes
- Did not run factory_core.py.
- Did not trigger marker/surya/vision/PaddleOCR.
- Did not download model.safetensors or any model.
- Did not reprocess PDFs; used existing trial assets only.
- Production 01/02/02A/06 remained unchanged.
- Output artifacts were not committed.
