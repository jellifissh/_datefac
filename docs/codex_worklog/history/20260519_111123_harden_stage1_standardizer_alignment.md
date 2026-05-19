# Codex Worklog - Latest

## task_title
Harden Stage 1 sandbox standardizer alignment

## started_at
2026-05-19 10:44:30

## finished_at
2026-05-19 11:11:23

## git_commit_before
6c8c421

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
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02A_研报原始表格资产.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02_研报全量结构化数据.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\05_stage1_core_metric_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\stage1_sandbox_asset_summary.xlsx
- D:\_datefac\output\delivery_package\27_stage1_pdfplumber_selected_samples_manifest.json

## files_changed
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
- D:\_datefac\docs\codex_worklog\LATEST.md
- D:\_datefac\docs\codex_worklog\history\20260519_111123_harden_stage1_standardizer_alignment.md

## files_generated
- D:\_datefac\output\delivery_package\31_stage1_standardizer_alignment_fix_log.md
- D:\_datefac\output\delivery_package\31_stage1_standardizer_alignment_fix_log.xlsx
- D:\_datefac\output\delivery_package\32_stage1_standardizer_alignment_fix_evaluation.md
- D:\_datefac\output\delivery_package\32_stage1_standardizer_alignment_fix_evaluation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\05_stage1_standardized_core_metric_trial.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\05_stage1_standardizer_diagnostics.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\stage1_standardizer_trial_summary.xlsx

## sandbox_standardizer_status
PASS

## per_sample_status_summary
- S1 (H3_AP202605141822317484_1 / 三鑫医疗): PASS_SAFE_TRIAL, metric_rows=70, manual_review_candidate_rows=16
- S2 (H3_AP202605121822223662_1 / 冠豪高新): WARN_NO_METRICS, metric_rows=0, error=STANDARDIZER_NO_METRIC_CANDIDATES
- S3 (H3_AP202605141822318060_1 / 科锐国际): PASS_SAFE_TRIAL, metric_rows=120, manual_review_candidate_rows=1

## result_summary
Hardened sandbox standardizer alignment by preserving stable sample identity from trial metadata + Stage1 manifest, adding conservative multi-metric row ambiguity routing, enforcing risky-flag route constraints, and producing duplicate metric-year diagnostics. The rerun used trial assets only and generated reports 31/32 with explicit identity mapping, risky alignment counts, and duplicate summaries.

## remaining_issues
- S2 still has no standardized metrics and remains a controlled WARN sample.
- Duplicate metric-year groups remain high in S1/S3 and should be reduced in a follow-up de-dup policy pass.

## next_step_suggestion
Add deterministic within-sample de-dup ranking for duplicated metric-year rows in sandbox mode, then rerun alignment evaluation before any sandbox delivery integration trial.

## safety_notes
- Did not run factory_core.py.
- Did not trigger marker/surya/vision/PaddleOCR.
- Did not download model.safetensors or any model.
- Did not reprocess PDFs; used trial assets only.
- Production 01/02/02A/06 remained unchanged.
- Did not commit output artifacts.
