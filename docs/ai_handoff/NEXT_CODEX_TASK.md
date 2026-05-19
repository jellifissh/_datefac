# NEXT CODEX TASK

## task_title
Add Stage 1 sandbox standardizer allowlists and table priors

## project
D:\_datefac

## current_status
The Stage 1 sandbox standardizer semantic guard task has completed.

Latest known result from user screenshot / local reports:
- task_title = Harden Stage 1 sandbox standardizer semantic guards
- py_compile_status = PASS
- help_status = PASS
- sandbox_standardizer_status = WARN
- production_delivery_status_after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production_guard_changed_count = 0
- production 01/02/02A/06 unchanged
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered

Per-sample result after semantic guards:
- S1 / H3_AP202605141822317484_1 / 三鑫医疗: WARN_SEMANTIC_GUARD, metric_rows=4, manual_review_candidate_rows=82
- S2 / H3_AP202605121822223662_1 / 冠豪高新: WARN_NO_METRICS, metric_rows=0, manual_review_candidate_rows=0
- S3 / H3_AP202605141822318060_1 / 科锐国际: WARN_SEMANTIC_GUARD, metric_rows=40, manual_review_candidate_rows=81

Quality metrics:
- source_row_semantic_risk_count = 94
- broad_keyword_unsafe_count = 0
- forbidden_source_label_count = 56
- duplicate_metric_year_groups_before_after = 61 -> 0
- remaining_likely_core_duplicates_count = 0

Interpretation:
The stricter semantic guard fixed duplicate promotion and routed risky rows away from likely_core_metric_trial. However, it is now overly conservative for S1/S3. The next step is to recover safe coverage using positive metric-specific source-label allowlists and table-role priors, without weakening hard semantic guards.

## goal
Improve sandbox standardizer precision/coverage balance by adding:
1. metric-specific positive source-label allowlists;
2. table-role priors based on trial asset metadata and candidate type;
3. safer promotion rules for S1/S3 only when source labels and table roles are strongly compatible;
4. dedicated diagnosis for S2 no-metric condition.

This task must rerun sandbox standardizer only using existing trial assets.
Do not reprocess PDFs.
Do not modify production delivery data.

Target code:
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py

Target local reports:
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.md
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.xlsx
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.md
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.xlsx

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
12. Do not relax existing hard-risk demotion rules. This task may add safe promotions only when positive evidence is strong.

## required_fixes

### 1. Add metric-specific positive source-label allowlists
Add explicit allowlists for each target metric.

Suggested allowlist examples:

营业收入:
- 营业收入
- 主营业务收入
- 收入
- 合计收入
- 分业务收入

归属母公司净利润:
- 归属母公司净利润
- 归母净利润
- 归属于母公司股东净利润
- 归属于上市公司股东的净利润
- 母公司拥有人应占利润

每股收益:
- 每股收益
- EPS
- 基本每股收益
- 稀释每股收益

P/E:
- P/E
- PE
- 市盈率

P/B:
- P/B
- PB
- 市净率

EV/EBITDA:
- EV/EBITDA
- EVEBITDA
- EV EBITDA

ROE:
- ROE
- 净资产收益率

EBITDA:
- EBITDA

毛利率:
- 毛利率

净利率:
- 净利率

Rules:
- Exact label match or strong source_label match should increase semantic_score.
- Row-text-only match without source_label match should remain lower confidence.
- Do not allow broad `收入` to override forbidden-source checks.

### 2. Add table-role priors
Read table metadata if available from trial assets:
- 02A_研报原始表格资产.xlsx raw_tables_index
- 05_stage1_core_metric_candidates.xlsx
- stage1_sandbox_asset_summary.xlsx

Use candidate_type / confidence / page / metric_keyword_hits if available.

Suggested table role classification:
- core_metrics
- full_financial_forecast
- business_forecast
- rating_or_disclaimer
- other_year_table
- unknown

Promotion prior:
- core_metrics and full_financial_forecast get positive score.
- business_forecast can promote 营业收入 segment rows but should be conservative for valuation metrics.
- rating_or_disclaimer must never promote likely_core_metric_trial.
- unknown can remain manual if semantic evidence is weak.

Add output columns:
- table_role
- table_role_score
- promotion_reason

### 3. Controlled safe promotion after semantic guard
A row can be likely_core_metric_trial only if:
- no hard-risk flags exist;
- source_label is allowed for the metric or table_role strongly supports it;
- duplicate arbitration leaves it preferred;
- year-value mapping is explicit enough;
- amount/rate/valuation value type is plausible.

Rows with hard-risk flags must remain manual_review_candidate.

Hard-risk flags include at least:
- source_row_semantic_risk
- forbidden_source_label_for_metric
- broad_keyword_unsafe
- multi_metric_row_ambiguous
- ambiguous_year_value_alignment
- ambiguous_multi_numeric_cell
- duplicate_metric_year_non_preferred

### 4. S2 no-metric diagnosis
For S2 / 冠豪高新, do not force extraction.

Instead, add a clear diagnostic table explaining why no metrics are detected:
- raw table count
- year evidence count
- text label examples
- keyword hit examples or lack thereof
- whether labels appear fragmented
- whether negative values exist but labels are missing
- recommended follow-up: extraction heuristic tuning / AI repair / manual visual review

### 5. Evaluation targets
This task should improve or at least diagnose without reintroducing unsafe duplicates.

Expected direction, not a strict requirement:
- S1 likely_core_metric_trial rows should increase from 4 if safe allowlist evidence exists.
- S3 likely_core_metric_trial rows may increase modestly if safe table-role/label evidence exists.
- S2 may remain WARN_NO_METRICS if source labels are not recoverable.
- remaining_likely_core_duplicates_count must stay 0.
- source_row_semantic_risk rows must not become likely_core_metric_trial.

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
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.md
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.xlsx

35 report must include:
- task_title
- started_at / finished_at
- commands_run
- files_read
- files_changed
- allowlist_summary
- table_role_prior_summary
- s2_no_metric_diagnosis_summary
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.md
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.xlsx

36 report must include:
- sandbox_standardizer_status
- production_delivery_status_after
- per_sample_status
- likely_core_metric_trial_rows
- manual_review_candidate_rows
- source_row_semantic_risk_count
- forbidden_source_label_count
- duplicate_metric_year_groups_before_after
- remaining_likely_core_duplicates_count
- safe_promotions_count
- promotion_reason_summary
- target_metric_coverage
- s2_no_metric_diagnosis
- blockers
- recommended_next_step

Excel sheets required:
- summary
- per_sample_status
- standardized_trial_rows
- manual_review_candidates
- safe_promotions
- promotion_reason_summary
- table_role_priors
- s2_no_metric_diagnosis
- target_metric_coverage
- production_guard
- safety_checks
- next_steps

## acceptance_criteria
This task passes if:
1. py_compile passes.
2. --help passes.
3. sandbox standardizer reruns using trial assets only.
4. metric-specific source-label allowlists are implemented.
5. table-role priors are implemented or explicitly reported as unavailable from current trial metadata.
6. hard-risk rows remain manual_review_candidate.
7. duplicate likely_core groups remain 0.
8. S2 no-metric condition is diagnosed, not silently ignored.
9. production 01/02/02A/06 are unchanged.
10. production delivery remains PASS.
11. no factory_core/marker/surya/vision/PaddleOCR/model download occurred.
12. 35/36 reports are generated.
13. output artifacts are not committed.

A WARN/PARTIAL status is acceptable if S2 remains no-metric or S1/S3 still require manual review, provided unsafe rows are not promoted.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_add_stage1_standardizer_allowlists_priors.md

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
- allowlist_summary
- table_role_prior_summary
- s2_no_metric_diagnosis_summary
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
- output/delivery_package/35_stage1_standardizer_allowlist_prior_log.md
- output/delivery_package/35_stage1_standardizer_allowlist_prior_log.xlsx
- output/delivery_package/36_stage1_standardizer_allowlist_prior_evaluation.md
- output/delivery_package/36_stage1_standardizer_allowlist_prior_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_safe_nonvision_pipeline.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add stage1 standardizer allowlists and priors"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. py_compile_status
3. help_status
4. sandbox_standardizer_status
5. per_sample_status_summary
6. safe_promotions_count
7. remaining_likely_core_duplicates_count
8. source_row_semantic_risk_count
9. forbidden_source_label_count
10. s2_no_metric_diagnosis_summary
11. generated_reports
12. production_delivery_status_after
13. production_files_unchanged
14. factory_core/vision/model_download_status
15. next_step_suggestion
16. commit sha

## safety_notes
- This task only improves sandbox standardizer scoring and safe promotion.
- Do not write Stage 1 results into production delivery_package.
- Do not run factory_core.py.
- Do not trigger vision/OCR/model backends.
- Do not modify production delivery data.
