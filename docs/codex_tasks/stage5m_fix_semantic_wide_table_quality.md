# Stage 5M - Fix semantic wide table reconstruction quality

项目：`D:\_datefac`

## 当前阶段

Stage 5L 已完成，已经从 Stage 5K 的 raw tables 中重建出 wide financial tables，并成功拆出四类财务表：资产负债表、利润表、现金流量表、主要财务比率。

Stage 5L summary 关键结果：

- `input_raw_table_count=5`
- `input_raw_cell_count=1161`
- `raw_grid_reconstructed_count=5`
- `semantic_table_block_count=9`
- `financial_semantic_block_count=4`
- `non_financial_block_count=4`
- `forecast_summary_block_count=1`
- `balance_sheet_block_count=1`
- `income_statement_block_count=1`
- `cash_flow_statement_block_count=1`
- `financial_ratio_block_count=1`
- `wide_financial_table_count=4`
- `wide_financial_metric_row_count=90`
- `structured_02_from_wide_row_count=450`
- `standardized_05_from_wide_row_count=450`
- `standardized_ok_count=45`
- `stage5l_semantic_reconstruction_pass=true`
- 生产文件、正式规则均未修改

## 已发现的质量问题

Stage 5L 方向正确，但 wide 表还不能直接进入 promotion review。人工审阅 `output/stage5l_semantic_table_reconstruction/148_stage5l_wide_financial_tables.xlsx` 后发现：

1. 表头行被当作指标行进入 wide 表，例如 `产负债表(百万元)`、`金流量表(百万元)`、`主要财务比率`。
2. 个别指标名被截断或丢首字，例如 `非流动资产` 被重建成 `流动资产`，`非流动负债` 被重建成 `流动负债`，`现金流量表(百万元)` 被重建成 `金流量表(百万元)`。
3. 现金流量表中值序列 `477/572/-536/-594/-513` 不应标记为 `投资活动现金流`，应从 raw grid 证据确认真实名称，优先判断为 `筹资活动现金流`。
4. `EPS(元)` 的 unit 不应为 `百万元`，应为 `元`。
5. 比率类指标的 unit 应修正为 `%`、`倍` 或 `ratio`，不得错误保留为 `百万元`。
6. `现金`、`存货`、`股本`、`EBITDA`、`EPS(元)`、`P/E`、`P/B` 等短但合法的指标不应被标记为 `HEADER_BROKEN`。
7. Stage 5L 虽生成 450 条 long-form 02，但标准化成功数仍为 45，说明 semantic wide 目前主要改善可读性，还没有改善标准化命中。

## 关键判断

1. Stage 5L 已验证“语义拆表”方向可行。
2. 但当前 wide 表仍存在表头污染、指标名丢字、现金流错配、单位错误、误报 warning 等问题。
3. 下一步不应进入生产 promotion review。
4. 下一步应先修复 semantic wide table 质量，得到真正可人工审阅的 clean wide financial tables。
5. 本轮不新增正式 mapping/alias，不修改生产文件，不进入 01/06。

## 下一任务

Stage 5M - Fix semantic wide table reconstruction quality and regenerate clean wide review tables.

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
10. 本轮只修复 semantic wide reconstruction 质量，重新生成 clean wide review、clean 02 review、clean 05 preview 和质量报告。

## 输入

- `output/stage5l_semantic_table_reconstruction/148_stage5l_raw_table_grid_review.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_semantic_table_blocks.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_wide_financial_tables.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_structured_02_from_wide_review.xlsx`
- `output/stage5l_semantic_table_reconstruction/148_stage5l_standardized_05_from_wide_review.xlsx`
- `output/stage5l_semantic_table_reconstruction/149_stage5l_semantic_reconstruction_summary.json`
- Stage 5L 脚本：`tools/reconstruct_stage5l_semantic_wide_tables.py`
- 当前正式 alias / mapping / scope / normalization 规则文件，只读参考

## 目标

1. 修复 Stage 5L semantic reconstruction 的已知质量问题。
2. 不重写整个 pipeline，只在 Stage 5L 逻辑上增加 deterministic clean-up / row filtering / unit correction / label correction。
3. 生成 clean wide financial tables。
4. 基于 clean wide 表生成 clean long-form 02 review。
5. 基于 clean 02 review 生成 sandbox 05 preview。
6. 输出质量报告，明确是否可以进入 Stage 5N promotion review。

## 必须修复的问题

### A. 表头行过滤

以下类型行不得进入 clean wide metric rows：

- 表名行：如 `资产负债表(百万元)`、`利润表（百万元）`、`现金流量表(百万元)`、`主要财务比率`
- 年份表头行：值列为 `2024/2025/2026/2027/2028` 或 `2024A/2025A/2026E/2027E/2028E` 的行
- 空指标行

### B. 指标名丢字修复

必须基于 raw grid 邻接单元格修复以下已知模式：

- `流动资产` + 值序列 `6603/7313/7399/7458/7521` 应恢复为 `非流动资产`
- `流动负债` + 值序列 `1552/2090/1695/1288/879` 应恢复为 `非流动负债`
- `金流量表(百万元)` 应识别为表头并过滤，不作为指标；如保留表名，应恢复为 `现金流量表(百万元)`

### C. 现金流错配修复

现金流量表中：

- 值序列 `477/572/-536/-594/-513` 不应标记为 `投资活动现金流`
- 应从 raw grid 证据中确认其真实指标名，优先判断为 `筹资活动现金流`
- 修复后不得存在重复的 `投资活动现金流` 指标行，除非 raw evidence 明确支持

### D. 单位修复

- `EPS(元)` 的 unit 必须为 `元`
- 比率类指标如果 raw_metric_name 包含 `(%)`，unit 应为 `%`
- `P/E`、`P/B`、`EV/EBITDA` unit 可为 `倍` 或 `ratio`，但不得为 `百万元`
- 普通金额类指标继续使用 `百万元`

### E. warning 修复

以下短但合法的财务指标不应因为短而标记 `HEADER_BROKEN`：

- `现金`
- `存货`
- `股本`
- `EBITDA`
- `EPS(元)`
- `P/E`
- `P/B`

## clean wide 输出要求

生成 clean wide 表字段至少包括：

- `raw_metric_name`
- `metric_name_cleaned`
- `statement_type`
- `unit`
- `2024A`
- `2025A`
- `2026E`
- `2027E`
- `2028E`
- `semantic_table_id`
- `source_page`
- `source_raw_table_id`
- `source_row_index`
- `metric_reconstruction_status`
- `metric_reconstruction_issue`
- `cleanup_action`
- `evidence`

`cleanup_action` 只能使用：

- `NONE`
- `FILTER_HEADER_ROW`
- `FIX_DROPPED_PREFIX`
- `FIX_CASH_FLOW_LABEL`
- `FIX_UNIT`
- `FIX_WARNING_ONLY`
- `FILTER_EMPTY_ROW`

## 生成文件

生成到：

- `output/stage5m_clean_semantic_wide_tables/150_stage5m_clean_wide_financial_tables.xlsx`
- `output/stage5m_clean_semantic_wide_tables/150_stage5m_clean_structured_02_from_wide.xlsx`
- `output/stage5m_clean_semantic_wide_tables/150_stage5m_clean_standardized_05_from_wide.xlsx`
- `output/stage5m_clean_semantic_wide_tables/150_stage5m_clean_reconstruction_quality_report.xlsx`
- `output/stage5m_clean_semantic_wide_tables/150_stage5m_clean_reconstruction_report.md`
- `output/stage5m_clean_semantic_wide_tables/151_stage5m_clean_reconstruction_summary.json`

## summary.json 至少包含

- `stage5l_wide_metric_row_count`
- `clean_wide_metric_row_count`
- `header_row_filtered_count`
- `empty_row_filtered_count`
- `dropped_prefix_fixed_count`
- `cash_flow_label_fixed_count`
- `unit_fixed_count`
- `warning_only_fixed_count`
- `remaining_header_row_count`
- `remaining_duplicate_metric_with_conflicting_values_count`
- `remaining_unit_issue_count`
- `clean_balance_sheet_metric_count`
- `clean_income_statement_metric_count`
- `clean_cash_flow_statement_metric_count`
- `clean_financial_ratio_metric_count`
- `clean_structured_02_row_count`
- `clean_standardized_05_row_count`
- `clean_standardized_ok_count`
- `clean_mapping_miss_count`
- `clean_true_mapping_gap_count`
- `stage5l_standardized_ok_count`
- `stage5l_mapping_miss_count`
- `ready_for_stage5n_promotion_review`
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
- `stage5m_clean_reconstruction_pass`

## pass 判定

- `clean_wide_metric_row_count > 0`
- `header_row_filtered_count >= 1`
- `dropped_prefix_fixed_count >= 2`
- `cash_flow_label_fixed_count >= 1`
- `unit_fixed_count >= 1`
- `remaining_header_row_count=0`
- `remaining_duplicate_metric_with_conflicting_values_count=0` 或清楚解释不是 blocker
- `remaining_unit_issue_count=0`
- `clean_structured_02_row_count > 0`
- `clean_standardized_05_row_count > 0`
- `clean_standardized_ok_count >= stage5l_standardized_ok_count`
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
- `stage5m_clean_reconstruction_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`，确认没有 `output/*` 被提交。
4. 如果新增脚本，只提交：
   - `tools/fix_stage5m_semantic_wide_table_quality.py`
5. 可提交说明文档：
   - `docs/stage5m_clean_semantic_wide_table_quality.md`
6. `git commit -m "stage5m: fix semantic wide table reconstruction quality"`
7. `git push origin main`

## 如果发生 blocker

如果无法修复表头污染、指标名丢字、现金流错配或单位错误，不要进入 promotion review，只生成 blocker 报告。