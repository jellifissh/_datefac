# Stage 5O - Promotion review from clean semantic wide tables

项目：`D:\_datefac`

## 当前状态

Stage 5N 已完成，clean semantic wide tables 已基本可人工审阅：

- 已识别第 2 页 `财务摘要和估值指标` 表
- 已按 sheet 拆出：`overview_index / balance_sheet / income_statement / cash_flow_statement / financial_ratio / valuation_summary / exceptions / non_year_table`
- `valuation_summary_detected=true`
- `valuation_summary_metric_count=10`
- `separated_sheet_count=8`
- `non_year_table_guard_enabled=true`
- `valuation_summary_conflict_count=0`
- `remaining_header_row_count=0`
- `remaining_unit_issue_count=0`
- `stage5n_wide_layout_fix_pass=true`

人工检查认为当前 wide review 质量“差不多”，可以进入 promotion review。

## 下一任务

Stage 5O - Review clean wide tables and build promotion candidates for formal 02/05, without applying to production.

## 核心目标

从 Stage 5N 的 clean wide tables 出发，生成正式结构化层的候选包：

1. 生成候选 02 全量结构化表。
2. 生成候选 05 标准化表。
3. 与当前生产 02/05 做只读 diff。
4. 标记哪些记录可晋升、哪些需要人工复核、哪些只保留在 review 层。
5. 不覆盖生产文件，不 real apply。

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
10. 本轮只做 promotion review 和候选包，不做生产替换。

## 输入

- `output/stage5n_wide_review_layout_fix/152_stage5n_clean_wide_financial_tables_by_sheet.xlsx`
- `output/stage5n_wide_review_layout_fix/152_stage5n_structured_02_from_wide.xlsx`
- `output/stage5n_wide_review_layout_fix/152_stage5n_standardized_05_from_wide.xlsx`
- `output/stage5n_wide_review_layout_fix/152_stage5n_valuation_summary_crosscheck.xlsx`
- `output/stage5n_wide_review_layout_fix/153_stage5n_wide_layout_summary.json`
- 当前生产 `02_研报全量结构化数据.xlsx`，只读 diff
- 当前生产 `05_核心财务指标标准化.xlsx`，只读 diff
- 当前正式 alias / mapping / scope / normalization 规则文件，只读参考

## promotion review 规则

### 1. 来源优先级

- 第 3 页详细财务表作为主数据源：
  - balance_sheet
  - income_statement
  - cash_flow_statement
  - financial_ratio
- 第 2 页 valuation_summary 作为摘要/交叉校验源，不应和详细表重复进入候选 02/05。
- 如果 valuation_summary 中的指标已在详细表存在且数值一致：标记 `SUMMARY_CONSISTENT_REFERENCE_ONLY`。
- 如果 valuation_summary 中存在详细表没有的指标：可进入 `PROMOTION_REVIEW_REQUIRED`，不得自动晋升。
- 如果 valuation_summary 与详细表冲突：标记 `BLOCKED_SUMMARY_DETAIL_CONFLICT`。

### 2. 候选 02 规则

候选 02 应从 clean wide financial tables 生成 long-form：

- 一行 = 一个指标 + 一个年份 + 一个数值
- 必须保留 provenance：source_pdf / page / sheet / source_row_index / semantic_table_id / source_reference
- 表头、空行、non_year_table 不得进入候选 02
- valuation_summary 默认不重复进入候选 02，只进入 crosscheck/reference，除非该指标详细表缺失且人工 review 标记允许

### 3. 候选 05 规则

候选 05 应基于候选 02 和现有正式规则做 sandbox-only 标准化：

- 标准化成功的核心指标进入 `PROMOTE_TO_05_CANDIDATE`
- derived metric 标记 `DEFER_DERIVED_METRIC`
- non-core metric 标记 `FILTER_NON_CORE_METRIC`
- mapping miss 但明显核心指标标记 `NEED_MAPPING_OR_ALIAS_REVIEW`
- true mapping gap 必须单独报告

### 4. diff 规则

与生产 02/05 对比时，至少分类：

- `NEW_RECORD`
- `SAME_AS_PRODUCTION`
- `VALUE_CHANGED`
- `UNIT_CHANGED`
- `YEAR_CHANGED`
- `METRIC_NAME_CHANGED`
- `STANDARD_METRIC_CHANGED`
- `ONLY_IN_PRODUCTION`
- `ONLY_IN_CANDIDATE`
- `DUPLICATE_CANDIDATE`

## 输出文件

生成到：

- `output/stage5o_promotion_review/154_stage5o_candidate_02.xlsx`
- `output/stage5o_promotion_review/154_stage5o_candidate_05.xlsx`
- `output/stage5o_promotion_review/154_stage5o_promotion_review.xlsx`
- `output/stage5o_promotion_review/154_stage5o_diff_with_production_02_05.xlsx`
- `output/stage5o_promotion_review/154_stage5o_promotion_review_report.md`
- `output/stage5o_promotion_review/155_stage5o_promotion_review_summary.json`

## summary.json 至少包含

- `input_clean_wide_sheet_count`
- `input_clean_wide_metric_row_count`
- `candidate_02_row_count`
- `candidate_05_row_count`
- `candidate_05_standardized_ok_count`
- `candidate_05_mapping_miss_count`
- `candidate_05_true_mapping_gap_count`
- `derived_metric_defer_count`
- `non_core_filter_count`
- `valuation_summary_reference_only_count`
- `valuation_summary_review_required_count`
- `valuation_summary_conflict_count`
- `new_record_count_02`
- `same_as_production_count_02`
- `diff_with_production_02_count`
- `new_record_count_05`
- `same_as_production_count_05`
- `diff_with_production_05_count`
- `promote_to_02_candidate_count`
- `promote_to_05_candidate_count`
- `need_manual_review_count`
- `blocked_count`
- `ready_for_stage5p_apply_review`
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
- `stage5o_promotion_review_pass`

## pass 判定

- `input_clean_wide_metric_row_count > 0`
- `candidate_02_row_count > 0`
- `candidate_05_row_count > 0`
- `valuation_summary_conflict_count=0`
- `candidate_05_true_mapping_gap_count=0` 或者所有 true gap 均进入 `need_manual_review`
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
- `stage5o_promotion_review_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`，确认没有 `output/*` 被提交。
4. 如果新增脚本，只提交：
   - `tools/build_stage5o_promotion_review.py`
5. 可提交说明文档：
   - `docs/stage5o_promotion_review_from_clean_wide.md`
6. `git commit -m "stage5o: build promotion review from clean wide tables"`
7. `git push origin main`

## 如果发生 blocker

如果 candidate 02/05 为空、valuation summary 与详细表冲突、生产文件被修改、或 diff 无法生成，停止，不要进入 apply，只生成 blocker 报告。