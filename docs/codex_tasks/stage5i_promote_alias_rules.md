# Stage 5I - Promote approved alias drafts to formal alias rules

项目：`D:\_datefac`

## 当前阶段
Stage 5H 已完成并推送。

最新结果：

- commit: `cc2ed6b`
- push: `origin/main` 成功
- `check_delivery_state.py --json => overall_status=PASS`
- `input_stage5g_remaining_miss_count=85`
- `input_alias_missing_count=5`
- `draft_alias_rule_count=5`
- `draft_alias_ready_count=5`
- `draft_alias_needs_review_count=0`
- `draft_alias_rejected_count=0`
- `previous_improved_standardized_ok_count=40`
- `after_alias_standardized_ok_count=45`
- `standardized_ok_increment_count=5`
- `previous_mapping_miss_count=85`
- `after_alias_mapping_miss_count=80`
- `mapping_miss_reduced_count=5`
- `alias_matched_new_standardized_ok_count=5`
- `remaining_derived_metric_not_supported_count=60`
- `remaining_non_core_metric_count=20`
- `remaining_true_mapping_gap_count=0`
- `remaining_unknown_count=5`
- `ready_for_stage5i_alias_promotion_count=5`
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

## 关键判断

1. Stage 5H 证明 5 条 alias draft 有效：`standardized_ok` 从 40 提升到 45，`mapping_miss` 从 85 降到 80。
2. 这 5 条 alias draft 已经满足晋升候选条件：`ready_for_stage5i_alias_promotion_count=5`。
3. 当前不应新增 mapping rule，不应处理 derived metric，不应进入生产 01/06。
4. 本轮只把 5 条已验证 alias draft 晋升到正式 alias rules，并做 sandbox-only 验证。
5. 注意 Stage 5H summary 中 `remaining_unknown_count=5` 与 `remaining_derived_metric_not_supported_count=60` + `remaining_non_core_metric_count=20` + `after_alias_mapping_miss_count=80` 存在统计口径疑点。Stage 5I 必须先做 precheck：确认这 5 条 unknown 是否只是已被 alias 解决的 5 条在 summary 分类里残留。如果不是，停止晋升并报告 blocker。

## 下一任务

Stage 5I - Promote approved Stage 5H alias drafts to formal alias rules and verify sandbox standardization.

## 严格约束

1. 不调用外部 AI。
2. 不联网。
3. 不修改生产 `01 / 02 / 02A / 05 / 06`。
4. 不修改 `data/overrides/02B_ai_repair_override.xlsx`。
5. 不修改正式 mapping / scope / normalization 规则文件。
6. 只允许修改正式 alias rules 文件，以及新增本轮工具脚本。
7. 不执行 real apply。
8. 不提交 `output/*`。
9. 不运行 `factory_core.py`。
10. 不触发 OCR / vision / marker / surya / PaddleOCR。
11. 本轮只晋升 Stage 5H 验证通过的 5 条 alias，不处理 derived metric / non-core metric。

## 输入

- `output/stage5h_alias_draft_validation/140_stage5h_alias_draft.xlsx`
- `output/stage5h_alias_draft_validation/140_stage5h_alias_dry_run_result.xlsx`
- `output/stage5h_alias_draft_validation/140_stage5h_alias_draft_validation_report.xlsx`
- `output/stage5h_alias_draft_validation/141_stage5h_alias_draft_validation_summary.json`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_structured_02.xlsx`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_standardization_preview.xlsx`
- 当前正式 alias rules 文件
- 当前正式 mapping / scope / normalization 规则文件，只读参考
- 当前生产 `05_核心财务指标标准化.xlsx`，只读参考

## 目标

1. 找到当前项目中的正式 alias rules 文件。
2. 读取 Stage 5H 中 `draft_status=DRAFT_ALIAS_READY` 的 5 条 alias draft。
3. 做 precheck：
   - 校验 `draft_alias_ready_count=5`。
   - 校验 `ready_for_stage5i_alias_promotion_count=5`。
   - 校验 5 条 draft 不与已有 alias rule 冲突。
   - 校验不会引入重复 alias key。
   - 校验不会改动 mapping / scope / normalization rules。
   - 核验 `remaining_unknown_count=5` 是否只是已被 alias 解决记录的统计残留；如不是，停止并报告 blocker。
4. 将 5 条 alias draft 晋升到正式 alias rules 文件。
5. 使用晋升后的正式 alias rules 对 Stage 5F improved structured 02 重新做 sandbox-only 标准化 dry-run。
6. 验证正式规则下结果与 Stage 5H dry-run 一致：
   - `standardized_ok_count >= 45`
   - `mapping_miss_count <= 80`
   - `remaining_true_mapping_gap_count=0`
7. 生成晋升日志和验证报告。

## alias promotion 输出字段

晋升日志至少包含：

- `alias_rule_id`
- `raw_metric_name`
- `raw_metric_name_cleaned`
- `target_standard_metric`
- `target_existing_mapping_rule_id`
- `statement_type`
- `asset_package`
- `unit`
- `source_pdf`
- `source_page`
- `source_table_id`
- `row_trace_id`
- `promotion_status`
- `promotion_issue_type`
- `evidence`

`promotion_status` 只能使用：

- `PROMOTED_TO_FORMAL_ALIAS`
- `SKIPPED_ALREADY_EXISTS`
- `BLOCKED_DUPLICATE_ALIAS_KEY`
- `BLOCKED_CONFLICT_WITH_EXISTING_ALIAS`
- `BLOCKED_PRECHECK_FAILED`

`promotion_issue_type` 只能使用：

- `NONE`
- `DUPLICATE_ALIAS_KEY`
- `CONFLICT_WITH_EXISTING_ALIAS`
- `UNKNOWN_COUNT_PRECHECK_FAILED`
- `SCHEMA_MISMATCH`
- `UNKNOWN`

## sandbox verification 输出字段

正式 alias rules 验证结果至少包含：

- `row_trace_id`
- `raw_metric_name`
- `standard_metric_after_formal_alias`
- `standardization_status_after_formal_alias`
- `matched_formal_alias_rule_id`
- `change_type`
- `issue_type_after`
- `source_reference`

`change_type` 只能使用：

- `FORMAL_ALIAS_MATCHED_STANDARDIZED_OK`
- `UNCHANGED_ALREADY_STANDARDIZED`
- `UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED`
- `UNCHANGED_NON_CORE_METRIC`
- `UNCHANGED_MAPPING_MISS`
- `UNCHANGED_OTHER`

## 生成报告

- `output/stage5i_alias_promotion/142_stage5i_alias_promotion_log.xlsx`
- `output/stage5i_alias_promotion/142_stage5i_alias_promotion_verification.xlsx`
- `output/stage5i_alias_promotion/142_stage5i_alias_promotion_report.md`
- `output/stage5i_alias_promotion/143_stage5i_alias_promotion_summary.json`

## summary.json 至少包含

- `input_draft_alias_rule_count`
- `input_draft_alias_ready_count`
- `precheck_pass`
- `unknown_count_precheck_pass`
- `unknown_count_precheck_reason`
- `promoted_alias_rule_count`
- `skipped_existing_alias_count`
- `blocked_duplicate_alias_key_count`
- `blocked_conflict_alias_count`
- `formal_alias_rules_changed`
- `previous_stage5h_after_alias_standardized_ok_count`
- `formal_alias_standardized_ok_count`
- `standardized_ok_matches_stage5h`
- `previous_stage5h_after_alias_mapping_miss_count`
- `formal_alias_mapping_miss_count`
- `mapping_miss_matches_stage5h`
- `remaining_derived_metric_not_supported_count`
- `remaining_non_core_metric_count`
- `remaining_true_mapping_gap_count`
- `remaining_unknown_count_after_precheck`
- `production_files_unchanged`
- `official_02B_unchanged`
- `formal_scope_rules_unchanged`
- `formal_mapping_rules_unchanged`
- `formal_normalization_rules_unchanged`
- `ai_called`
- `internet_called`
- `factory_core_called`
- `ocr_called`
- `stage5i_alias_promotion_pass`

## pass 判定

- `input_draft_alias_ready_count=5`
- `precheck_pass=true`
- `unknown_count_precheck_pass=true`
- `promoted_alias_rule_count=5` 或者 `promoted_alias_rule_count + skipped_existing_alias_count = 5`
- `formal_alias_rules_changed=true`，除非 5 条全部已存在且验证一致
- `formal_alias_standardized_ok_count >= 45`
- `formal_alias_mapping_miss_count <= 80`
- `remaining_true_mapping_gap_count=0`
- `production_files_unchanged=true`
- `official_02B_unchanged=true`
- `formal_scope_rules_unchanged=true`
- `formal_mapping_rules_unchanged=true`
- `formal_normalization_rules_unchanged=true`
- `ai_called=false`
- `internet_called=false`
- `factory_core_called=false`
- `ocr_called=false`
- `stage5i_alias_promotion_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`，确认没有 `output/*` 被提交。
4. 只提交：
   - 新增或修改的 Stage 5I 工具脚本
   - 正式 alias rules 文件
5. `git commit -m "stage5i: promote validated alias rules"`
6. `git push origin main`

## 如果发生 blocker

如果 unknown precheck 不通过、alias 冲突、重复 key、正式规则验证无法复现 Stage 5H 结果，停止晋升，不要修改正式 alias rules 文件。只生成 blocker 报告并提交诊断脚本。