# NEXT CODEX TASK

## task_title
Harden Stage 1 sandbox standardizer alignment

## project
D:\_datefac

## current_status
The sandbox-only standardizer trial has completed and was committed.

Latest committed result:
- commit: 695303e add stage1 sandbox standardizer trial

User uploaded/reviewed reports:
- D:\_datefac\output\delivery_package\29_stage1_sandbox_standardizer_trial_log.xlsx
- D:\_datefac\output\delivery_package\30_stage1_sandbox_standardizer_trial_evaluation.xlsx

Key result from 29/30:
- sandbox_standardizer_status = WARN
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_guard_changed_count = 0
- production 01/02/02A/06 unchanged
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered

Per-sample metric result:
- S1: metric_rows=0, manual_review_candidate_rows=0, status=WARN, error=STANDARDIZER_NO_METRIC_CANDIDATES
- S2: metric_rows=98, manual_review_candidate_rows=10, status=PASS
- S3: metric_rows=130, manual_review_candidate_rows=0, status=PASS

Important quality concern from user/assistant review:
1. S1/S2 mapping appears suspicious. Earlier asset builder reported:
   - S1 / H3_AP202605141822317484_1 / 三鑫医疗: metric_candidate_rows=25
   - S2 / H3_AP202605121822223662_1 / 冠豪高新: metric_candidate_rows=0
   - S3 / H3_AP202605141822318060_1 / 科锐国际: metric_candidate_rows=13
   But standardizer output shows S1=0 and S2=98. This may be valid only if sample_id assignment changed or folder order was used incorrectly. Must verify and fix sample identity preservation.
2. Some standardized trial rows show row_preview containing multiple metric blocks in a single extracted row, for example:
   `营业收入 | 1640.20 | 1860.07 | 2064.58 | 2292.66 | 净利润 | 290.27 | 322.37 | 360.75 | 404.11`
   The current standardizer may incorrectly assign later metric values to earlier metric years. This is unsafe.
3. This trial must remain sandbox-only. Do not proceed to sandbox delivery integration until alignment is safer.

## goal
Harden deterministic metric-year-value alignment in the sandbox standardizer and rerun the sandbox-only standardizer trial.

Target code:
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py

Target local reports:
- D:\_datefac\output\delivery_package\31_stage1_standardizer_alignment_fix_log.md
- D:\_datefac\output\delivery_package\31_stage1_standardizer_alignment_fix_log.xlsx
- D:\_datefac\output\delivery_package\32_stage1_standardizer_alignment_fix_evaluation.md
- D:\_datefac\output\delivery_package\32_stage1_standardizer_alignment_fix_evaluation.xlsx

Also regenerate sandbox standardizer outputs under:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial

This task must not write to production delivery data.

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any model.
4. Do not run OCR.
5. Do not reprocess PDFs.
6. Do not rebuild production delivery_package.
7. Do not run apply_manual_review_corrections.py on production delivery_dir.
8. Do not modify production delivery files:
   - 01_自动可信核心指标.xlsx
   - 02_人工复核指标队列.xlsx
   - 02A_人工年份修正覆盖表.xlsx
   - 06_最终核心财务指标.xlsx
9. Do not process baseline 091 as Stage 1 sample.
10. Do not commit output artifacts.
11. Worklog must be English only and UTF-8.

## required_fixes

### 1. Preserve sample identity
Fix or verify sample identity mapping.

The standardizer must derive sample identity from stable metadata, not arbitrary folder sort order.

Recommended priority:
1. read sample_id/company/pdf_file from each sample's `stage1_sandbox_asset_summary.xlsx` if present;
2. fallback to `02A_研报原始表格资产.xlsx` raw_tables_index columns;
3. fallback to folder name only as last resort.

The output must show all three mappings explicitly:
- sample_id
- pdf_stem
- asset_package
- company
- source_identity_method

Expected mapping should remain:
- S1 = H3_AP202605141822317484_1 = 三鑫医疗
- S2 = H3_AP202605121822223662_1 = 冠豪高新
- S3 = H3_AP202605141822318060_1 = 科锐国际

If actual trial asset metadata disagrees, report mismatch clearly and do not silently relabel rows.

### 2. Prevent multi-metric row value leakage
If one row contains more than one metric keyword block, do not extract all numeric values for the first matched metric.

Example unsafe row:
`营业收入 | 1640.20 | 1860.07 | 2064.58 | 2292.66 | 净利润 | 290.27 | 322.37 | 360.75 | 404.11`

Required behavior:
- detect multiple metric keyword positions in the row;
- split row into metric segments when possible;
- if segmentation is not reliable, route to `manual_review_candidate` with flag `multi_metric_row_ambiguous`;
- never assign values after a second metric keyword to the first metric.

### 3. Align values only to detected year columns or segment-local values
Preferred rules:
- If table has explicit year columns, use only cells under those year columns for the matched metric row.
- If no explicit year columns but row has pattern `[metric, value1, value2, value3, value4]` and table-level year header exists, map values by position only if count matches year count.
- If count mismatch, route to manual review with `ambiguous_year_value_alignment`.
- Do not infer missing years from random numeric cells.

### 4. Guard against duplicate metric-year rows
For sandbox trial output, duplicate metric-year rows are allowed only if clearly sourced from different table roles, but must be flagged.

Add flags:
- duplicate_metric_year_in_sample
- multiple_source_tables_for_metric_year

Generate a duplicate summary by:
- sample_id + standard_metric + year

### 5. Keep risky rows out of likely_core_metric_trial
Rows with any of these flags should route to manual_review_candidate, not likely_core_metric_trial:
- multi_metric_row_ambiguous
- ambiguous_year_value_alignment
- ambiguous_multi_numeric_cell
- no_year_columns
- standardizer_no_metric_candidates

### 6. Add quality status per sample
Per-sample status should be more informative:
- PASS_SAFE_TRIAL if metric rows exist and risky alignment rows are routed to manual review
- WARN_NO_METRICS if no metrics found but no error
- WARN_RISKY_ALIGNMENT if many ambiguous rows exist
- PARTIAL if some metrics exist but major target coverage missing
- FAIL only for actual read/logic failures

## rerun_requirements
Use existing trial assets only:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315

Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --help
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py ^
  --standardize-sandbox ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --strict-scope
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

Do not reprocess PDFs.

## report_requirements
Generate:
- D:\_datefac\output\delivery_package\31_stage1_standardizer_alignment_fix_log.md
- D:\_datefac\output\delivery_package\31_stage1_standardizer_alignment_fix_log.xlsx

31 report must include:
- task_title
- started_at / finished_at
- commands_run
- files_read
- files_changed
- sample_identity_mapping
- alignment_fix_summary
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\32_stage1_standardizer_alignment_fix_evaluation.md
- D:\_datefac\output\delivery_package\32_stage1_standardizer_alignment_fix_evaluation.xlsx

32 report must include:
- sandbox_standardizer_status
- production_delivery_status_after
- sample_identity_mapping
- per_sample_metric_rows
- per_sample_manual_review_candidate_rows
- risky_alignment_rows_count
- duplicate_metric_year_summary
- target_metric_coverage
- rows_promoted_to_likely_core_metric_trial
- rows_routed_to_manual_review_candidate
- blockers
- recommended_next_step

Excel sheets required:
- summary
- sample_identity_mapping
- per_sample_status
- standardized_trial_rows
- manual_review_candidates
- risky_alignment_rows
- duplicate_metric_year_summary
- target_metric_coverage
- production_guard
- safety_checks
- next_steps

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. --help passes.
3. sandbox standardizer reruns using trial assets only.
4. sample identity mapping is explicit and stable.
5. multi-metric row leakage is prevented or flagged and routed to manual review.
6. risky rows are not marked likely_core_metric_trial.
7. production 01/02/02A/06 are unchanged.
8. production delivery remains PASS.
9. no factory_core/marker/surya/vision/PaddleOCR/model download occurred.
10. 31/32 reports are generated.
11. output artifacts are not committed.

A WARN/PARTIAL status is acceptable if S1 or S2 still needs manual review, provided it is accurately diagnosed.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_harden_stage1_standardizer_alignment.md

Worklog must be English only and UTF-8.

Worklog must include:
- task_title
- started_at
- finished_at
- git_commit_before
- git_commit_after
- commands_run
- files_read
- files_changed
- files_generated
- sandbox_standardizer_status
- per_sample_status_summary
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_safe_nonvision_pipeline.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/31_stage1_standardizer_alignment_fix_log.md
- output/delivery_package/31_stage1_standardizer_alignment_fix_log.xlsx
- output/delivery_package/32_stage1_standardizer_alignment_fix_evaluation.md
- output/delivery_package/32_stage1_standardizer_alignment_fix_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_safe_nonvision_pipeline.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "harden stage1 sandbox standardizer alignment"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. py_compile_status
3. help_status
4. sandbox_standardizer_status
5. sample_identity_mapping
6. per_sample_status_summary
7. risky_alignment_rows_count
8. duplicate_metric_year_summary
9. generated_reports
10. production_delivery_status_after
11. production_files_unchanged
12. factory_core/vision/model_download_status
13. next_step_suggestion
14. commit sha

## safety_notes
- This task only hardens sandbox standardizer trial output.
- Do not write Stage 1 results into production delivery_package.
- Do not run factory_core.py.
- Do not trigger vision/OCR/model backends.
- Do not modify production delivery data.
