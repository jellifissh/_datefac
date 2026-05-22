# Stage 5G - Analyze remaining mapping misses after raw metric extraction fix

项目：`D:\_datefac`

## 当前阶段
Stage 5F 已完成并推送。

最新结果：

- commit: `00c759a`
- message: `stage5f: improve raw metric extraction for sandbox pipeline`
- `input_raw_table_count=5`
- `previous_structured_02_row_count=604`
- `improved_structured_02_row_count=130`
- `previous_raw_metric_name_parse_issue_count=360`
- `improved_raw_metric_name_parse_issue_count=0`
- `parse_issue_reduced_count=360`
- `previous_ready_for_standardization_count=442`
- `improved_ready_for_standardization_count=130`
- `previous_standardized_ok_count=5`
- `improved_standardized_ok_count=40`
- `previous_mapping_miss_count=432`
- `improved_mapping_miss_count=85`
- `header_filtered_count=20`
- `non_financial_filtered_count=136`
- `metric_name_inferred_count=4`
- `metric_name_cleaned_count=0`
- `production_files_unchanged=true`
- `official_02B_unchanged=true`
- `formal_scope_rules_unchanged=true`
- `formal_mapping_rules_unchanged=true`
- `formal_normalization_rules_unchanged=true`
- `ai_called=false`
- `internet_called=false`
- `factory_core_called=false`
- `ocr_called=false`
- `stage5f_raw_metric_extraction_fix_pass=true`
- `check_delivery_state.py --json => overall_status=PASS`

## 关键判断

1. Stage 5F 已经证明主要 blocker 不是 PDF 表格抽取，而是 raw table → 02 的指标名解析质量。
2. Stage 5F 已将 raw_metric_name parse issue 从 360 降到 0。
3. 标准化命中从 5 提升到 40，mapping miss 从 432 降到 85。
4. 当前不要进入 01 / 06，也不要修改正式规则。
5. 下一步先分析剩余 85 条 mapping miss，判断它们到底是：
   - 真正缺 mapping rule
   - 缺 alias / normalization
   - 非核心指标或低价值指标
   - package-specific 指标
   - derived metric
   - 仍然需要继续改 raw extraction / row filtering

## 下一任务

Stage 5G - Analyze remaining mapping misses after Stage 5F improved extraction.

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
10. 本轮只分析 Stage 5F improved standardization preview 中剩余 mapping misses，不做正式规则晋升。

## 输入

- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_structured_02.xlsx`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_standardization_preview.xlsx`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_raw_metric_extraction_fix_report.xlsx`
- `output/stage5f_raw_metric_extraction_fix/137_stage5f_raw_metric_extraction_fix_summary.json`
- 当前正式 mapping / scope / normalization / alias 规则文件，只读参考
- 当前生产 `05_核心财务指标标准化.xlsx`，只读参考

## 目标

1. 读取 Stage 5F improved standardization preview。
2. 只分析剩余 `improved_mapping_miss_count=85` 的记录。
3. 对剩余 miss 做分组、归因和优先级排序。
4. 识别哪些可以进入后续 draft mapping / alias，哪些应该过滤或暂缓。
5. 生成 Stage 5H 的输入清单，但本轮不新增正式规则。

## 每条记录输出字段

- `row_trace_id`
- `source_pdf`
- `source_page`
- `source_table_id`
- `raw_metric_name`
- `raw_metric_name_cleaned`
- `year`
- `value`
- `unit`
- `statement_type`
- `asset_package`
- `source_reference`
- `nearest_existing_standard_metric`
- `nearest_existing_mapping_rule_id`
- `similarity_score`（如可计算）
- `remaining_miss_category`
- `root_cause`
- `recommended_action`
- `priority_level`
- `confidence_level`
- `evidence`

## 枚举要求

`remaining_miss_category` 只能使用：

- `TRUE_MAPPING_GAP`
- `ALIAS_MISSING`
- `NORMALIZATION_DEPENDENT`
- `PACKAGE_SPECIFIC_METRIC`
- `DERIVED_METRIC_NOT_SUPPORTED`
- `NON_CORE_METRIC`
- `LOW_VALUE_NO_ACTION`
- `RAW_EXTRACTION_STILL_DIRTY`
- `HEADER_OR_METADATA_ROW`
- `UNKNOWN`

`recommended_action` 只能使用：

- `DRAFT_MAPPING_RULE`
- `DRAFT_ALIAS_RULE`
- `DEFER_PACKAGE_SPECIFIC_RULE`
- `DEFER_DERIVED_METRIC_RULE`
- `FILTER_NON_CORE_METRIC`
- `FIX_RAW_EXTRACTION_AGAIN`
- `NEED_MANUAL_REVIEW`
- `NO_ACTION`

`priority_level` 只能使用：

- `HIGH`
- `MEDIUM`
- `LOW`

`confidence_level` 只能使用：

- `HIGH`
- `MEDIUM`
- `LOW`

## 分组统计要求

1. 按 `raw_metric_name_cleaned` 分组。
2. 按 `source_table_id` 分组。
3. 按 `statement_type` 分组。
4. 按 `remaining_miss_category` 分组。
5. 识别 top 高频未命中指标名。
6. 标记可进入 Stage 5H draft mapping / alias 的候选。
7. 标记应过滤的非核心指标 / 低价值项。

## 生成报告

- `output/stage5g_remaining_mapping_miss_analysis/138_stage5g_remaining_mapping_miss_analysis.xlsx`
- `output/stage5g_remaining_mapping_miss_analysis/138_stage5g_remaining_mapping_miss_analysis.md`
- `output/stage5g_remaining_mapping_miss_analysis/139_stage5g_remaining_mapping_miss_summary.json`

## summary.json 至少包含

- `input_improved_standardization_row_count`
- `input_remaining_mapping_miss_count`
- `analyzed_remaining_mapping_miss_count`
- `true_mapping_gap_count`
- `alias_missing_count`
- `normalization_dependent_count`
- `package_specific_metric_count`
- `derived_metric_not_supported_count`
- `non_core_metric_count`
- `low_value_no_action_count`
- `raw_extraction_still_dirty_count`
- `header_or_metadata_row_count`
- `unknown_count`
- `draft_mapping_rule_candidate_count`
- `draft_alias_rule_candidate_count`
- `filter_non_core_metric_count`
- `fix_raw_extraction_again_count`
- `need_manual_review_count`
- `high_priority_count`
- `medium_priority_count`
- `low_priority_count`
- `production_files_unchanged`
- `official_02B_unchanged`
- `formal_scope_rules_unchanged`
- `formal_mapping_rules_unchanged`
- `formal_normalization_rules_unchanged`
- `ai_called`
- `internet_called`
- `factory_core_called`
- `ocr_called`
- `stage5g_remaining_mapping_miss_analysis_pass`

## pass 判定

- `input_remaining_mapping_miss_count=85`
- `analyzed_remaining_mapping_miss_count=85`
- 至少一个分类计数大于 0
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

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 如果新增脚本，只提交：
   - `tools/analyze_stage5g_remaining_mapping_miss.py`
4. 不提交 `output/*`。
5. `git commit -m "stage5g: analyze remaining mapping misses after extraction fix"`
6. `git push origin main`
