# Codex Worklog - Latest

## task_title
Run full safe non-vision pipeline for Stage 1 visually approved samples

## started_at
2026-05-19 09:16:00

## finished_at
2026-05-19 09:19:26

## git_commit_before
1345e10

## git_commit_after
pending

## commands_run
- git -C D:\_datefac fetch origin
- git -C D:\_datefac pull origin main
- git -C D:\_datefac status --short
- git -C D:\_datefac log --oneline --decorate -8
- D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
- Repository safe-entrypoint discovery by listing and reading tools scripts
- Generated D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.md/xlsx
- Generated D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.md/xlsx

## selected_samples
- H3_AP202605141822317484_1.pdf
- H3_AP202605121822223662_1.pdf
- H3_AP202605141822318060_1.pdf

## baseline_sample
- H3_AP202605091822098939_1.pdf

## safe_entrypoints_discovered
- tools/probe_pdf_tables.py (probe only)
- tools/probe_extractors.py (probe report only)
- tools/probe_pdfplumber_profiles.py (profile probe only)
- tools/build_delivery_package.py (delivery repack only)
- tools/apply_manual_review_corrections.py (post-delivery correction only)

## entrypoints_used
- none for full pipeline run (blocked before execution)

## files_generated
- D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.md
- D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.xlsx
- D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.md
- D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.xlsx

## files_modified
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/20260519_091926_run_stage1_full_safe_pipeline.md

## final_stage1_full_pipeline_status
BLOCKED

## final_delivery_status
- overall_status: PASS
- pass_count: 17
- warn_count: 0
- fail_count: 0
- duplicate_key_count_final: 0
- high_risk_flags: 0
- test_token_hits: 0

## stop_condition_checks
- model download triggered: False
- marker/surya/vision/PaddleOCR triggered: False
- factory_core.py run: False
- no safe full non-vision entrypoint: True
- scope unsafe: True

## result_summary
- Mandatory preflight was completed.
- Selected PDFs exist and delivery state was backed up.
- No complete safe non-vision full-pipeline entrypoint exists for scoped three-sample end-to-end processing outside factory_core.py.
- Execution stopped as BLOCKED_NO_SAFE_FULL_PIPELINE and reports 21/22 were generated.

## remaining_issues
- Missing dedicated safe non-vision full pipeline runner that supports exact sample scoping without factory_core.py.

## next_step_suggestion
Add/approve a dedicated scoped safe non-vision full-pipeline runner, then rerun Stage 1 full pipeline for the three selected samples.

## safety_notes
- Did not run factory_core.py.
- Did not trigger marker/surya/vision/PaddleOCR.
- Did not download model.safetensors.
- Did not process beyond the three selected PDFs.
- Did not commit output artifacts.
