# Stage 5K - Full sandbox rebuild 02/05 from PDF

项目：`D:\_datefac`

## 当前阶段
Stage 5J 已完成并推送，PDF → 05 sandbox baseline 已关闭。

最新已知结果：

- Stage 5J commit: `3acad6a`
- message: `stage5j: close pdf to 05 sandbox baseline`
- push: `origin/main` 成功
- `check_delivery_state.py --json => overall_status=PASS`
- `pdf_exists=true`
- `pdf_page_count=5`
- `raw_table_count=5`
- `improved_structured_02_row_count=130`
- `formal_alias_standardized_ok_count=45`
- `formal_alias_mapping_miss_count=80`
- `remaining_derived_metric_not_supported_count=60`
- `remaining_non_core_metric_count=20`
- `remaining_true_mapping_gap_count=0`
- `stage5b_pdf_to_raw_tables_pass=true`
- `stage5f_raw_metric_extraction_fix_pass=true`
- `stage5i_alias_promotion_pass=true`
- `stage5j_pdf_to_05_baseline_closed=true`
- `recommended_next_stage=STAGE5K_DERIVED_METRIC_AND_NON_CORE_FILTER_STRATEGY`

## 关键判断

1. Stage 5B-5J 已经修复并验证了 PDF → raw tables → improved structured 02 → formal alias 05 的 sandbox 链路。
2. 现在需要从原始 PDF 重新跑一遍完整 sandbox rebuild，生成新版 sandbox 02 和 sandbox 05，而不是继续只看阶段中间产物。
3. 本轮只重建 sandbox 产物，不覆盖生产 02/05，不进入 01/06。
4. 目的不是新增规则，而是验证当前最新 extractor、raw metric 修复逻辑、formal alias/mapping/scope/normalization 规则组合后，从头跑出的结构化表质量。

## 下一任务

Stage 5K - Full sandbox rebuild 02/05 from PDF.

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
10. 本轮只从 PDF 重新生成 sandbox 02/05 和 diff/质量报告。

## 输入

- `D:\_datefac\input\H3_AP202605121822223662_1.pdf`
- 当前 Stage 5B PDF raw table extraction 逻辑 / 脚本
- 当前 Stage 5F raw_metric_name extraction fix 逻辑 / 脚本
- 当前正式 alias / mapping / scope / normalization 规则文件，只读使用
- 当前生产 `02_研报全量结构化数据.xlsx`，只读用于 schema / diff 参考
- 当前生产 `05_核心财务指标标准化.xlsx`，只读用于 schema / diff 参考

## 目标

1. 从原始 PDF 开始，在 sandbox 中重新执行：
   - PDF → raw tables
   - raw tables → improved structured 02
   - improved structured 02 → standardized 05
2. 生成新版 sandbox 02 表。
3. 生成新版 sandbox 05 表。
4. 和当前生产 02/05 做只读 diff，说明差异，不覆盖生产文件。
5. 验证当前正式规则下：
   - sandbox 02 row count > 0
   - sandbox 05 standardized_ok_count >= 45
   - true mapping gap = 0
   - derived / non-core 被清晰标记或隔离
6. 生成 full rebuild 报告，明确是否可以进入后续 promotion / 生产替换评估。

## 输出文件

生成到：

- `output/stage5k_full_sandbox_rebuild/146_stage5k_raw_tables_rebuilt.xlsx`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_structured_02_sandbox.xlsx`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_standardized_05_sandbox.xlsx`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_rebuild_diff_report.xlsx`
- `output/stage5k_full_sandbox_rebuild/146_stage5k_full_rebuild_report.md`
- `output/stage5k_full_sandbox_rebuild/147_stage5k_full_rebuild_summary.json`

## summary.json 至少包含

- `input_pdf_file`
- `pdf_exists`
- `pdf_page_count`
- `raw_table_rebuilt_count`
- `raw_table_rebuilt_row_count`
- `raw_table_rebuilt_cell_count`
- `structured_02_sandbox_row_count`
- `structured_02_structured_ok_count`
- `structured_02_filtered_header_count`
- `structured_02_filtered_non_financial_count`
- `standardized_05_sandbox_row_count`
- `standardized_ok_count`
- `mapping_miss_count`
- `derived_metric_not_supported_count`
- `non_core_metric_count`
- `true_mapping_gap_count`
- `unknown_count`
- `production_02_row_count`
- `production_05_row_count`
- `diff_with_production_02_count`
- `diff_with_production_05_count`
- `ready_for_stage5l_promotion_review`
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
- `stage5k_full_sandbox_rebuild_pass`

## pass 判定

- `pdf_exists=true`
- `raw_table_rebuilt_count >= 1`
- `structured_02_sandbox_row_count > 0`
- `standardized_05_sandbox_row_count > 0`
- `standardized_ok_count >= 45`
- `true_mapping_gap_count=0`
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
- `stage5k_full_sandbox_rebuild_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`，确认没有 `output/*` 被提交。
4. 如果新增脚本，只提交：
   - `tools/rebuild_stage5k_full_sandbox_02_05_from_pdf.py`
5. 可提交说明文档：
   - `docs/stage5k_full_sandbox_rebuild_02_05.md`
6. `git commit -m "stage5k: full sandbox rebuild 02 and 05 from pdf"`
7. `git push origin main`

## 如果发生 blocker

如果从 PDF 重新抽取 raw tables 失败、sandbox 02 行数为 0、standardized_ok 无法复现 45 条、或任何生产文件/hash guard 发生变化，停止，不要改生产文件，只生成 blocker 报告。