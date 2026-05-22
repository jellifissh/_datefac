# Stage 5H - Draft alias rules and validate sandbox standardization improvement

项目：`D:\_datefac`

## 当前阶段
Stage 5G 已完成并推送。

最新结果：

- commit: `de08efe`
- message: `stage5g: analyze remaining mapping misses after extraction fix`
- push: `origin/main` 成功
- `input_improved_standardization_row_count=130`
- `input_remaining_mapping_miss_count=85`
- `analyzed_remaining_mapping_miss_count=85`
- `true_mapping_gap_count=0`
- `alias_missing_count=5`
- `normalization_dependent_count=0`
- `package_specific_metric_count=0`
- `derived_metric_not_supported_count=60`
- `non_core_metric_count=20`
- `low_value_no_action_count=0`
- `raw_extraction_still_dirty_count=0`
- `header_or_metadata_row_count=0`
- `unknown_count=0`
- `draft_mapping_rule_candidate_count=0`
- `draft_alias_rule_candidate_count=5`
- `filter_non_core_metric_count=20`
- `fix_raw_extraction_again_count=0`
- `need_manual_review_count=0`
- `high_priority_count=5`
- `medium_priority_count=60`
- `low_priority_count=20`
- `production_files_unchanged=true`
- `official_02B_unchanged=true`
- `formal_scope_rules_unchanged=true`
- `formal_mapping_rules_unchanged=true`
- `formal_normalization_rules_unchanged=true`
- `ai_called=false`
- `internet_called=false`
- `factory_core_called=false`
- `ocr_called=false`
- `stage5g_remaining_mapping_miss_analysis_pass=true`
- `check_delivery_state.py --json => overall_status=PASS`

## 关键判断

1. Stage 5G 已证明剩余 85 条 mapping miss 里没有真正的 mapping rule 缺口。
2. 其中 5 条是 `ALIAS_MISSING`，可以进入 alias draft。
3. 60 条是 `DERIVED_METRIC_NOT_SUPPORTED`，暂缓到后续 derived metric rule 阶段。
4. 20 条是 `NON_CORE_METRIC`，后续应过滤，不进入核心标准化链路。
5. 当前不要修改正式 alias / mapping / scope / normalization 规则文件。
6. 本轮只生成 alias draft，并做 sandbox dry-run 验证提升效果。

## 下一任务

Stage 5H - Draft alias rules for 5 alias-missing records and validate sandbox standardization.

## 严格约束

1. 不调用外部 AI。
2. 不联网。
3. 不修改生产 `01 / 02 / 02A / 05 / 06`。
4. 不修改 `data/overrides/02B_ai_repair_override.xlsx`。
5. 不修改正式 mapping / scope / normalization / alias 规则文件。
6. 不执行 real apply。
7. 不提交 `output/*`。
8. 不运行 `factory_core.py`。
9. 不触发 OCR / vision / marker / surya / PaddleOCR。
10. 本轮只基于 Stage 5G 的 5 条 alias_missing 生成 draft alias，并在 sandbox 中验证。

## 输入

- `output/stage5g_remaining_mapping_miss_analysis/138_stage5g_remaining_mapping_miss_analysis.xlsx`
- `output/stage5g_remaining_mapping_miss_analysis/138_stage5g_remaining_mapping_miss_analysis.md`
- `output/stage5g_remaining_mapping_miss_analysis/139_stage5g_remaining_mapping_miss_summary.json`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_structured_02.xlsx`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_standardization_preview.xlsx`
- `output/stage5f_raw_metric_extraction_fix/137_stage5f_raw_metric_extraction_fix_summary.json`
- 当前正式 alias / mapping / scope / normalization 规则文件，只读参考
- 当前生产 `05_核心财务指标标准化.xlsx`，只读参考

## 目标

1. 读取 Stage 5G 中 `remaining_miss_category=ALIAS_MISSING` 的 5 条记录。
2. 为这 5 条生成 alias draft，不写入正式规则文件。
3. 使用 alias draft 对 Stage 5F improved structured 02 做 sandbox-only 标准化 dry-run。
4. 验证 standardized_ok 是否从 Stage 5F 的 40 条提升。
5. 验证 mapping_miss 是否从 Stage 5F 的 85 条下降。
6. 明确剩余未命中是否仍为 derived / non-core，而不是 true mapping gap。

## alias draft 表字段

生成的 alias draft 至少包含：

- `alias_rule_id`
- `raw_metric_name`
- `raw_metric_name_cleaned`
- `target_standard_metric`
- `target_existing_mapping_rule_id`
- `statement_type`
- `asset_package`
- `unit`
- `year_sample`
- `value_sample`
- `source_pdf`
- `source_page`
- `source_table_id`
- `row_trace_id`
- `confidence_level`
- `draft_status`
- `evidence`

`draft_status` 只能使用：

- `DRAFT_ALIAS_READY`
- `DRAFT_ALIAS_NEEDS_REVIEW`
- `DRAFT_ALIAS_REJECTED`

`confidence_level` 只能使用：

- `HIGH`
- `MEDIUM`
- `LOW`

## sandbox dry-run 输出字段

dry-run 标准化结果至少包含：

- `row_trace_id`
- `raw_metric_name`
- `raw_metric_name_cleaned`
- `standard_metric_before`
- `standardization_status_before`
- `standard_metric_after`
- `standardization_status_after`
- `matched_alias_rule_id`
- `change_type`
- `issue_type_after`
- `source_reference`

`change_type` 只能使用：

- `ALIAS_MATCHED_NEW_STANDARDIZED_OK`
- `UNCHANGED_ALREADY_STANDARDIZED`
- `UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED`
- `UNCHANGED_NON_CORE_METRIC`
- `UNCHANGED_MAPPING_MISS`
- `UNCHANGED_OTHER`

## 生成报告

- `output/stage5h_alias_draft_validation/140_stage5h_alias_draft.xlsx`
- `output/stage5h_alias_draft_validation/140_stage5h_alias_dry_run_result.xlsx`
- `output/stage5h_alias_draft_validation/140_stage5h_alias_draft_validation_report.xlsx`
- `output/stage5h_alias_draft_validation/140_stage5h_alias_draft_validation_report.md`
- `output/stage5h_alias_draft_validation/141_stage5h_alias_draft_validation_summary.json`

## summary.json 至少包含

- `input_stage5g_remaining_miss_count`
- `input_alias_missing_count`
- `draft_alias_rule_count`
- `draft_alias_ready_count`
- `draft_alias_needs_review_count`
- `draft_alias_rejected_count`
- `previous_improved_standardized_ok_count`
- `after_alias_standardized_ok_count`
- `standardized_ok_increment_count`
- `previous_mapping_miss_count`
- `after_alias_mapping_miss_count`
- `mapping_miss_reduced_count`
- `alias_matched_new_standardized_ok_count`
- `remaining_derived_metric_not_supported_count`
- `remaining_non_core_metric_count`
- `remaining_true_mapping_gap_count`
- `remaining_unknown_count`
- `ready_for_stage5i_alias_promotion_count`
- `production_files_unchanged`
- `official_02B_unchanged`
- `formal_scope_rules_unchanged`
- `formal_mapping_rules_unchanged`
- `formal_normalization_rules_unchanged`
- `formal_alias_rules_unchanged`
- `ai_called`
- `internet_called`
- `factory_core_called`
- `ocr_called`
- `stage5h_alias_draft_validation_pass`

## pass 判定

- `input_alias_missing_count=5`
- `draft_alias_rule_count=5`
- `after_alias_standardized_ok_count >= previous_improved_standardized_ok_count`
- `after_alias_mapping_miss_count <= previous_mapping_miss_count`
- `ready_for_stage5i_alias_promotion_count > 0`
- `production_files_unchanged=true`
- `official_02B_unchanged=true`
- `formal_scope_rules_unchanged=true`
- `formal_mapping_rules_unchanged=true`
- `formal_normalization_rules_unchanged=true`
- `formal_alias_rules_unchanged=true`
- `ai_called=false`
- `internet_called=false`
- `factory_core_called=false`
- `ocr_called=false`
- `stage5h_alias_draft_validation_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 如果新增脚本，只提交：
   - `tools/build_stage5h_alias_draft_validation.py`
4. 不提交 `output/*`。
5. `git commit -m "stage5h: draft alias rules for sandbox standardization"`
6. `git push origin main`
