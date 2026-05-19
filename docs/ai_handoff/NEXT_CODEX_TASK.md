# NEXT CODEX TASK

## task_title
Harden Stage 1 sandbox standardizer semantic guards

## project
D:\_datefac

## current_status
The Stage 1 sandbox standardizer alignment hardening task has completed and was committed.

Latest committed result:
- commit: 4842314 harden stage1 sandbox standardizer alignment

User uploaded/reviewed reports:
- D:\_datefac\output\delivery_package\31_stage1_standardizer_alignment_fix_log.xlsx
- D:\_datefac\output\delivery_package\32_stage1_standardizer_alignment_fix_evaluation.xlsx

Key result from 31/32:
- sandbox_standardizer_status = PASS
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_guard_changed_count = 0
- production 01/02/02A/06 unchanged
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered

Sample identity mapping is now correct:
- S1 = H3_AP202605141822317484_1 = 三鑫医疗
- S2 = H3_AP202605121822223662_1 = 冠豪高新
- S3 = H3_AP202605141822318060_1 = 科锐国际

Per-sample status from 32:
- S1: PASS_SAFE_TRIAL, metric_rows=70, manual_review_candidate_rows=16
- S2: WARN_NO_METRICS, metric_rows=0, manual_review_candidate_rows=0, error=STANDARDIZER_NO_METRIC_CANDIDATES
- S3: PASS_SAFE_TRIAL, metric_rows=120, manual_review_candidate_rows=1

Important remaining quality concerns:
1. risky_alignment_rows_count = 17; these rows are routed to manual review, which is good.
2. duplicate_metric_year_groups = 61; duplicate_metric_year_in_sample appears very frequently.
3. Some rows still appear unsafe in standardized_trial_rows even after alignment hardening.

Observed unsafe examples from 32 standardized_trial_rows:
- Row preview: `净利润 | 290.27 | 322.37 | 360.75 | 404.11 | 其他 | -27.17 | -22.62 | -5.00 | -6.00`
  Problem: values after `其他` may be incorrectly assigned to 归属母公司净利润.
- Row preview: `归属母公司股东净利润 | 264.94 | 294.37 | 328.75 | 368.11 | 现金流量净额 | 138.24 | 198.73 | 273.23 | 278.57`
  Problem: cash-flow values may be incorrectly assigned to 归属母公司净利润.
- Row preview: `应收和预付款项 | 98.04 | 123.36 | 133.22 | 147.29 | 销售收入增长率 | 9.31% | 13.41% | 11.00% | 11.05%`
  Problem: row is not 营业收入; broad keyword `收入` causes semantic mismatch.

Interpretation:
The standardizer now has correct identity mapping and safer multi-metric flagging, but source-row semantic guards are still too weak. Rows with account names, cash-flow fragments, or ratio fragments can still be promoted to likely_core_metric_trial. This must be fixed before sandbox delivery integration.

## goal
Harden sandbox standardizer source-row semantic guards and duplicate arbitration.

This task must rerun sandbox standardizer only using existing trial assets. Do not reprocess PDFs and do not modify production delivery data.

Target code:
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py

Target local reports:
- D:\_datefac\output\delivery_package\33_stage1_standardizer_semantic_guard_log.md
- D:\_datefac\output\delivery_package\33_stage1_standardizer_semantic_guard_log.xlsx
- D:\_datefac\output\delivery_package\34_stage1_standardizer_semantic_guard_evaluation.md
- D:\_datefac\output\delivery_package\34_stage1_standardizer_semantic_guard_evaluation.xlsx

Rerun output remains under:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial

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

### 1. Stronger source-row semantic guard
Before promoting any row to `likely_core_metric_trial`, verify that the row's leading semantic label is compatible with the target standard_metric.

Add a deterministic label extraction function:
- take the first non-empty cell before the first numeric value as `source_label`;
- if the table is flattened and multiple label/value blocks exist, split into blocks by text label positions;
- if reliable block splitting is not possible, route to manual_review_candidate.

### 2. Disallow broad keyword false positives
The keyword `收入` is too broad.

Rules:
- `收入` can match 营业收入 only when source_label is exactly or strongly similar to:
  - 营业收入
  - 主营业务收入
  - 收入
  - 合计收入
  - 产品/业务 segment + 收入 pattern in business forecast table
- `销售收入增长率`, `现金流量/营业收入`, `应收和预付款项`, `预收账款`, `营业成本`, `营业税金及附加` must not be promoted as 营业收入.
- If such rows contain `收入` only as part of a ratio/growth/account description, route to manual_review_candidate or ignore.

### 3. Add forbidden source label guards by metric
Examples:
- For 营业收入, forbidden labels include:
  - 应收和预付款项
  - 预收账款
  - 营业成本
  - 营业税金及附加
  - 销售收入增长率
  - 销售商品提供劳务收到现金/营业收入
- For 归属母公司净利润, forbidden labels include:
  - 现金流量净额
  - 经营活动现金流
  - 其他
  - 少数股东损益
- For P/E, P/B, EV/EBITDA, forbidden labels include:
  - 每股指标
  - 每股收益
  - 每股经营现金
  - 权益自由现金流
  - 评级
  - 投资建议

If forbidden label appears in the same row segment after the matched metric label and cannot be split safely, route to manual_review_candidate with flag `source_row_semantic_risk`.

### 4. Duplicate arbitration
For sandbox trial, do not promote all duplicates to likely_core_metric_trial.

For each `sample_id + standard_metric + year`:
- if multiple rows exist, choose at most one preferred row as likely_core_metric_trial;
- all other duplicates must be routed to manual_review_candidate or flagged `duplicate_metric_year_non_preferred`.

Preferred row scoring suggestion:
- exact metric label match > fuzzy/broad match;
- source_label exact target metric > derived ratio/account label;
- source table page/role closer to core forecast table > business breakdown table if available;
- fewer semantic flags > more flags;
- non-percent values preferred for amount metrics;
- percent values preferred only for rate metrics like ROE/毛利率/净利率.

Add fields if helpful:
- source_label
- semantic_score
- preferred_duplicate
- duplicate_resolution_reason

### 5. Manual routing flags
Rows with these flags must not be likely_core_metric_trial:
- source_row_semantic_risk
- forbidden_source_label_for_metric
- duplicate_metric_year_non_preferred
- broad_keyword_unsafe
- multi_metric_row_ambiguous
- ambiguous_year_value_alignment
- ambiguous_multi_numeric_cell

### 6. Status logic
A sample should be PASS_SAFE_TRIAL only if:
- it has at least one likely_core_metric_trial row;
- risky semantic rows are routed away from likely_core_metric_trial;
- duplicate arbitration has been applied.

If metrics exist but many rows are manual due semantic risk, use WARN_SEMANTIC_GUARD.

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
- D:\_datefac\output\delivery_package\33_stage1_standardizer_semantic_guard_log.md
- D:\_datefac\output\delivery_package\33_stage1_standardizer_semantic_guard_log.xlsx

33 report must include:
- task_title
- started_at / finished_at
- commands_run
- files_read
- files_changed
- semantic_guard_summary
- duplicate_arbitration_summary
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\34_stage1_standardizer_semantic_guard_evaluation.md
- D:\_datefac\output\delivery_package\34_stage1_standardizer_semantic_guard_evaluation.xlsx

34 report must include:
- sandbox_standardizer_status
- production_delivery_status_after
- per_sample_status
- likely_core_metric_trial_rows
- manual_review_candidate_rows
- source_row_semantic_risk_count
- broad_keyword_unsafe_count
- forbidden_source_label_count
- duplicate_metric_year_groups_before_after
- duplicate_metric_year_non_preferred_count
- remaining_likely_core_duplicates_count
- target_metric_coverage
- blockers
- recommended_next_step

Excel sheets required:
- summary
- per_sample_status
- standardized_trial_rows
- manual_review_candidates
- semantic_risk_rows
- duplicate_arbitration
- target_metric_coverage
- production_guard
- safety_checks
- next_steps

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. --help passes.
3. sandbox standardizer reruns using trial assets only.
4. obvious semantic false positives are not likely_core_metric_trial.
5. rows with source_row_semantic_risk or forbidden_source_label_for_metric are routed to manual_review_candidate.
6. duplicate arbitration reduces likely_core duplicate groups to 0, or every remaining duplicate is explicitly justified.
7. production 01/02/02A/06 are unchanged.
8. production delivery remains PASS.
9. no factory_core/marker/surya/vision/PaddleOCR/model download occurred.
10. 33/34 reports are generated.
11. output artifacts are not committed.

A WARN/PARTIAL status is acceptable if S1/S2/S3 still require manual review, provided unsafe rows are not promoted.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_harden_stage1_standardizer_semantic_guards.md

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
- semantic_guard_summary
- duplicate_arbitration_summary
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
- output/delivery_package/33_stage1_standardizer_semantic_guard_log.md
- output/delivery_package/33_stage1_standardizer_semantic_guard_log.xlsx
- output/delivery_package/34_stage1_standardizer_semantic_guard_evaluation.md
- output/delivery_package/34_stage1_standardizer_semantic_guard_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_safe_nonvision_pipeline.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "harden stage1 standardizer semantic guards"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. py_compile_status
3. help_status
4. sandbox_standardizer_status
5. per_sample_status_summary
6. source_row_semantic_risk_count
7. broad_keyword_unsafe_count
8. forbidden_source_label_count
9. duplicate_metric_year_groups_before_after
10. remaining_likely_core_duplicates_count
11. generated_reports
12. production_delivery_status_after
13. production_files_unchanged
14. factory_core/vision/model_download_status
15. next_step_suggestion
16. commit sha

## safety_notes
- This task only hardens sandbox standardizer trial output.
- Do not write Stage 1 results into production delivery_package.
- Do not run factory_core.py.
- Do not trigger vision/OCR/model backends.
- Do not modify production delivery data.
