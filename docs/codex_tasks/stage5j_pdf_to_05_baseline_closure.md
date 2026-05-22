# Stage 5J - Close PDF-to-05 sandbox baseline after formal alias promotion

项目：`D:\_datefac`

## 当前阶段
Stage 5I 已完成并推送。

最新结果：

- commit: `1dc5e2d`
- push: `origin/main` 成功
- `check_delivery_state.py --json => overall_status=PASS`
- `input_draft_alias_rule_count=5`
- `input_draft_alias_ready_count=5`
- `precheck_pass=true`
- `unknown_count_precheck_pass=true`
- `promoted_alias_rule_count=1`
- `skipped_existing_alias_count=4`
- `blocked_duplicate_alias_key_count=0`
- `blocked_conflict_alias_count=0`
- `formal_alias_rules_changed=true`
- `formal_alias_standardized_ok_count=45`
- `formal_alias_mapping_miss_count=80`
- `remaining_true_mapping_gap_count=0`
- `production_files_unchanged=true`
- `official_02B_unchanged=true`
- `formal_scope_rules_unchanged=true`
- `formal_mapping_rules_unchanged=true`
- `formal_normalization_rules_unchanged=true`
- `stage5i_alias_promotion_pass=true`

## 关键判断

1. Stage 5I 已经把 Stage 5H 验证通过的 alias draft 晋升到正式 alias rules。
2. 5 条 alias 中 1 条新增，4 条已存在并被跳过；正式 alias rules 已覆盖 5 条候选。
3. 使用正式 alias rules 后，sandbox 标准化结果达到：`standardized_ok=45`，`mapping_miss=80`。
4. 剩余 80 条并非真实 mapping gap：其中主要是 derived metric / non-core metric。
5. 当前不要继续新增 mapping / alias，不要进入生产 01/06，不要处理 derived metric。
6. 下一步应做 Stage 5 的 PDF-to-05 sandbox baseline closure：重新验证从 PDF/raw tables 到 improved 02 再到 formal alias 05 的链路，并产出闭环报告。

## 下一任务

Stage 5J - Verify and close the PDF-to-05 sandbox baseline after Stage 5I formal alias promotion.

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
10. 本轮只做 sandbox baseline closure 与报告，不做新规则晋升。

## 输入

- `D:\_datefac\input\H3_AP202605121822223662_1.pdf`
- `output/stage5b_table_extraction_restore/raw_tables.xlsx`
- `output/stage5b_table_extraction_restore/raw_tables.json`
- `output/stage5b_table_extraction_restore/129_stage5b_table_extraction_restore_summary.json`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_structured_02.xlsx`
- `output/stage5f_raw_metric_extraction_fix/136_stage5f_improved_standardization_preview.xlsx`
- `output/stage5f_raw_metric_extraction_fix/137_stage5f_raw_metric_extraction_fix_summary.json`
- `output/stage5i_alias_promotion/142_stage5i_alias_promotion_log.xlsx`
- `output/stage5i_alias_promotion/142_stage5i_alias_promotion_verification.xlsx`
- `output/stage5i_alias_promotion/143_stage5i_alias_promotion_summary.json`
- 当前正式 alias / mapping / scope / normalization 规则文件，只读参考
- 当前生产 `05_核心财务指标标准化.xlsx`，只读参考

## 目标

1. 校验 Stage 5B/5F/5I 的输入产物完整存在。
2. 重新读取 raw tables 与 improved structured 02。
3. 使用当前正式 alias / mapping / scope / normalization 规则，对 improved structured 02 做 sandbox-only 标准化验证。
4. 验证正式规则下结果与 Stage 5I 一致：
   - `formal_alias_standardized_ok_count >= 45`
   - `formal_alias_mapping_miss_count <= 80`
   - `remaining_true_mapping_gap_count=0`
5. 生成 PDF-to-05 baseline closure 报告，明确：
   - PDF → raw tables 是否已通
   - raw tables → improved 02 是否已通
   - improved 02 → formal alias 05 是否已通
   - 当前剩余问题是否应延后到 derived metric / non-core filter 阶段
6. 不新增任何正式规则。
7. 不修改任何生产 Excel。

## closure report 至少覆盖

- PDF 输入状态
- raw table extraction 状态
- raw table row/cell 规模
- improved structured 02 规模
- 结构化过滤效果
- formal alias 标准化结果
- standardized_ok 数量
- mapping_miss 数量
- derived metric 剩余数量
- non-core metric 剩余数量
- true mapping gap 数量
- 是否可关闭 Stage 5 PDF-to-05 baseline
- 下一阶段建议

## 生成文件

- `output/stage5j_pdf_to_05_baseline_closure/144_stage5j_pdf_to_05_baseline_verification.xlsx`
- `output/stage5j_pdf_to_05_baseline_closure/144_stage5j_pdf_to_05_baseline_closure_report.md`
- `output/stage5j_pdf_to_05_baseline_closure/145_stage5j_pdf_to_05_baseline_closure_summary.json`

## summary.json 至少包含

- `input_pdf_file`
- `pdf_exists`
- `pdf_page_count`
- `raw_table_file_exists`
- `raw_table_count`
- `raw_table_total_row_count`
- `raw_table_total_cell_count`
- `improved_structured_02_file_exists`
- `improved_structured_02_row_count`
- `formal_alias_rules_available`
- `sandbox_05_verification_row_count`
- `formal_alias_standardized_ok_count`
- `formal_alias_mapping_miss_count`
- `remaining_derived_metric_not_supported_count`
- `remaining_non_core_metric_count`
- `remaining_true_mapping_gap_count`
- `remaining_unknown_count`
- `stage5b_pdf_to_raw_tables_pass`
- `stage5f_raw_metric_extraction_fix_pass`
- `stage5i_alias_promotion_pass`
- `stage5j_pdf_to_05_baseline_closed`
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
- `stage5j_closure_pass`

## pass 判定

- `pdf_exists=true`
- `raw_table_count=5`
- `improved_structured_02_row_count=130`
- `formal_alias_standardized_ok_count >= 45`
- `formal_alias_mapping_miss_count <= 80`
- `remaining_true_mapping_gap_count=0`
- `stage5b_pdf_to_raw_tables_pass=true`
- `stage5f_raw_metric_extraction_fix_pass=true`
- `stage5i_alias_promotion_pass=true`
- `stage5j_pdf_to_05_baseline_closed=true`
- `recommended_next_stage` 不为空
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
- `stage5j_closure_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`，确认没有 `output/*` 被提交。
4. 如果新增脚本，只提交：
   - `tools/verify_stage5j_pdf_to_05_baseline_closure.py`
5. 可提交 closure 文档：
   - `docs/stage5_pdf_to_05_baseline_closure.md`
6. `git commit -m "stage5j: close pdf to 05 sandbox baseline"`
7. `git push origin main`

## 如果发生 blocker

如果正式 alias rules 下无法复现 Stage 5I 结果，或者生产文件/hash guard 发生变化，停止 closure，只生成 blocker 报告，不要修改任何正式规则。