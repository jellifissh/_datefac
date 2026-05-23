# Stage 5L - Semantic table reconstruction and wide review

项目：`D:\_datefac`

## 背景

Stage 5K 已经从原始 PDF 重新跑通 sandbox 02/05：

- `pdf_page_count=5`
- `raw_table_rebuilt_count=5`
- `raw_table_rebuilt_row_count=203`
- `raw_table_rebuilt_cell_count=1161`
- `structured_02_sandbox_row_count=130`
- `structured_02_structured_ok_count=130`
- `standardized_05_sandbox_row_count=130`
- `standardized_ok_count=45`
- `mapping_miss_count=80`
- `derived_metric_not_supported_count=60`
- `non_core_metric_count=20`
- `true_mapping_gap_count=0`
- `diff_with_production_02_count=5`
- `diff_with_production_05_count=11`
- `stage5k_full_sandbox_rebuild_pass=true`

但目前产物主要是机器中间态：raw cell 表、long-form 02、long-form 05。人类审阅时看起来像“融化成一堆”。核心原因不是没有抽表，而是没有做语义拆表和 wide reconstruction。

## 关键问题

当前问题集中在：

1. PDF raw tables 是物理抽取结果，不是业务语义表。
2. 关键财务预测页可能被抽成一个大表，没有按左右区块拆成资产负债表、利润表、现金流量表、主要财务比率等。
3. 部分中文指标名可能被拆裂，例如表头/指标名跨列或断字。
4. 现在直接 raw cells → long-form 02，缺少中间的 human-readable wide table reconstruction。
5. 需要先生成人能看的 wide review 表，再决定是否进入生产替换或进一步修 extractor。

## 下一任务

Stage 5L - Reconstruct semantic wide financial tables from raw tables, then regenerate review-oriented 02/05 views.

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
10. 本轮只生成语义拆表、wide review、质量报告和 sandbox 视图。

## 输入

- `D:\_datefac\input\H3_AP202605121822223662_1.pdf`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_raw_tables_rebuilt.xlsx`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_structured_02_sandbox.xlsx`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_standardized_05_sandbox.xlsx`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_rebuild_diff_report.xlsx`
- `output/stage5k_full_sandbox_rebuild/147_stage5k_full_rebuild_summary.json`
- 当前正式 alias / mapping / scope / normalization 规则文件，只读使用
- 当前生产 `02_研报全量结构化数据.xlsx`，只读参考
- 当前生产 `05_核心财务指标标准化.xlsx`，只读参考

## 目标

1. 读取 Stage 5K raw tables rebuilt。
2. 将 raw cell 表按 `page/table_id/row_index/col_index` 还原成原始 wide grid。
3. 识别真正的财务表，过滤正文、页眉、免责声明、机构信息等非财务表。
4. 对宽表做语义拆分：
   - 将一个大表中的左右并排表拆成多个 semantic table block。
   - 每个 block 应有独立的 `statement_type`、`unit`、`year_columns`、`metric_name_column`。
5. 修复明显的表头/指标名断裂问题，但只做 deterministic 规则，不调用 AI。
6. 生成人类可审阅的 wide financial tables。
7. 基于 semantic wide tables 再生成 review-oriented long-form 02。
8. 基于新的 review-oriented 02 做 sandbox-only 05 标准化预览。
9. 对比 Stage 5K 的 02/05，说明质量提升或未提升的原因。
10. 输出质量报告，明确是否可进入 promotion review，还是需要继续优化 semantic splitter。

## semantic table block 字段

每个语义表块至少包含：

- `semantic_table_id`
- `source_pdf`
- `source_page`
- `source_raw_table_id`
- `block_type`
- `statement_type`
- `unit`
- `start_row_index`
- `end_row_index`
- `start_col_index`
- `end_col_index`
- `metric_name_col_index`
- `year_col_indices`
- `year_labels`
- `block_confidence`
- `block_issue_type`
- `evidence`

`block_type` 只能使用：

- `BALANCE_SHEET`
- `INCOME_STATEMENT`
- `CASH_FLOW_STATEMENT`
- `FINANCIAL_RATIO`
- `VALUATION_TABLE`
- `FORECAST_SUMMARY`
- `NON_FINANCIAL_TEXT`
- `UNKNOWN_TABLE`

`block_issue_type` 只能使用：

- `NONE`
- `SPLIT_REQUIRED`
- `HEADER_BROKEN`
- `YEAR_HEADER_MISSING`
- `UNIT_MISSING`
- `METRIC_COLUMN_AMBIGUOUS`
- `NON_FINANCIAL_TABLE`
- `UNKNOWN`

## wide review 输出要求

每个 semantic financial block 都要生成可读 wide 表：

- 第一列：`raw_metric_name`
- 第二列：`metric_name_cleaned`
- 第三列：`statement_type`
- 第四列：`unit`
- 后续列：年份，例如 `2024A / 2025A / 2026E / 2027E / 2028E`
- 追加辅助列：
  - `semantic_table_id`
  - `source_page`
  - `source_raw_table_id`
  - `source_row_index`
  - `metric_reconstruction_status`
  - `metric_reconstruction_issue`
  - `evidence`

`metric_reconstruction_status` 只能使用：

- `RECONSTRUCTED_OK`
- `RECONSTRUCTED_WITH_WARNING`
- `FILTERED_HEADER`
- `FILTERED_NON_FINANCIAL`
- `FAILED`

## 02 review 输出要求

从 semantic wide tables 生成 long-form 02 review 表：

- `row_trace_id`
- `semantic_table_id`
- `source_pdf`
- `source_page`
- `source_raw_table_id`
- `source_row_index`
- `raw_metric_name`
- `metric_name_cleaned`
- `statement_type`
- `unit`
- `year`
- `value`
- `source_reference`
- `structured_status`
- `structured_issue_type`
- `evidence`

## 05 review 输出要求

基于 02 review 做 sandbox-only 标准化：

- `row_trace_id`
- `raw_metric_name`
- `metric_name_cleaned`
- `standard_metric`
- `standardization_status`
- `standardization_issue_type`
- `statement_type`
- `unit`
- `year`
- `value`
- `matched_mapping_rule_id`
- `matched_alias_rule_id`
- `semantic_table_id`
- `source_reference`

## 生成文件

生成到：

- `output/stage5l_semantic_table_reconstruction/148_stage5l_raw_table_grid_review.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_semantic_table_blocks.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_wide_financial_tables.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_structured_02_from_wide_review.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_standardized_05_from_wide_review.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_semantic_reconstruction_report.md`
- `output/stage5l_semantic_table_reconstruction/149_stage5l_semantic_reconstruction_summary.json`

## summary.json 至少包含

- `input_raw_table_count`
- `input_raw_cell_count`
- `raw_grid_reconstructed_count`
- `semantic_table_block_count`
- `financial_semantic_block_count`
- `non_financial_block_count`
- `balance_sheet_block_count`
- `income_statement_block_count`
- `cash_flow_statement_block_count`
- `financial_ratio_block_count`
- `forecast_summary_block_count`
- `wide_financial_table_count`
- `wide_financial_metric_row_count`
- `wide_reconstructed_ok_count`
- `wide_reconstructed_with_warning_count`
- `wide_filtered_header_count`
- `wide_filtered_non_financial_count`
- `structured_02_from_wide_row_count`
- `structured_02_from_wide_ok_count`
- `standardized_05_from_wide_row_count`
- `standardized_ok_count`
- `mapping_miss_count`
- `derived_metric_not_supported_count`
- `non_core_metric_count`
- `true_mapping_gap_count`
- `unknown_count`
- `stage5k_structured_02_row_count`
- `stage5k_standardized_ok_count`
- `stage5k_mapping_miss_count`
- `wide_view_generated`
- `semantic_splitter_pass`
- `ready_for_stage5m_review`
- `recommended_next_stage`
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
- `stage5l_semantic_reconstruction_pass`

## pass 判定

- `input_raw_table_count >= 1`
- `raw_grid_reconstructed_count >= 1`
- `semantic_table_block_count >= 1`
- `financial_semantic_block_count >= 1`
- `wide_financial_table_count >= 1`
- `wide_financial_metric_row_count > 0`
- `structured_02_from_wide_row_count > 0`
- `standardized_05_from_wide_row_count > 0`
- `wide_view_generated=true`
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
- `stage5l_semantic_reconstruction_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`，确认没有 `output/*` 被提交。
4. 如果新增脚本，只提交：
   - `tools/reconstruct_stage5l_semantic_wide_tables.py`
5. 可提交说明文档：
   - `docs/stage5l_semantic_table_reconstruction.md`
6. `git commit -m "stage5l: reconstruct semantic wide financial tables"`
7. `git push origin main`

## 如果发生 blocker

如果无法从 raw tables 识别任何 financial semantic block，或者 wide financial table 为空，停止，不要推进 02/05 promotion，只生成 blocker 报告。