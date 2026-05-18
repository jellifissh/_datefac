# NEXT CODEX TASK

## task_title
基于已确认截图生成 02 人工复核精确填写方案

## project
D:\_datefac

## current_status
用户已上传并人工查看了 08A 候选对应截图。

结论：
1. 第一张截图可作为正式人工复核依据：
   D:\_datefac\output\H3_AP202605091822098939_1_资产包\02B_table_region_assets\crops\page_001_table_001.png

2. 第二张截图不能用于 EPS/P/E/P/B/EVEBITDA 复核：
   D:\_datefac\output\H3_AP202605141822317484_1_资产包\02B_table_region_assets\crops\page_004_table_001.png
   原因：该截图实际是“分业务收入及毛利率”表，不包含每股收益、P/E、P/B、EV/EBITDA 等指标。不要基于该图填写 02。

当前 delivery 状态：
- overall_status = PASS
- fail_count = 0
- warn_count = 0
- duplicate_keys 为空
- high_risk_flags 为空

## confirmed_values_from_crop
第一张截图中的表为“盈利预测和财务指标”。列：
- 2025A
- 2026E
- 2027E
- 2028E

截图确认值：

| standard_metric | unit | 2025A | 2026E | 2027E | 2028E |
|---|---|---:|---:|---:|---:|
| 营业收入 | 百万元 | 922 | 1224 | 1620 | 2112 |
| EBITDA | 百万元 | 204.33 | 319.32 | 429.35 | 561.01 |
| 归属母公司净利润 | 百万元 | 204.59 | 288.52 | 398.83 | 536.53 |
| 每股收益 | 元/股 | 1.17 | 1.65 | 2.28 | 3.06 |
| P/E | 倍 | 42.27 | 29.97 | 21.68 | 16.12 |
| P/B | 倍 | 4.23 | 3.76 | 3.26 | 2.76 |
| EV/EBITDA | 倍 | 40.31 | 22.76 | 16.08 | 11.46 |

## goal
不要直接修改 02。

请读取 02_人工复核指标队列.xlsx，基于上面的 confirmed_values_from_crop，生成一个“精确填写方案”，告诉用户应该在 02 的哪些行填写哪些人工复核字段。

输出文件：
- D:\_datefac\output\delivery_package\09_manual_review_fill_plan.md
- D:\_datefac\output\delivery_package\09_manual_review_fill_plan.xlsx

该计划必须做到：
1. 给出 3-5 条可以人工填写的真实指标。
2. 每条必须对应到 02 中的具体 row_index 或明确说明未找到匹配行。
3. 每条必须给出完整 suggested fields。
4. 不要修改 02，只生成计划。
5. 不要使用第二张“分业务收入及毛利率”截图里的值。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要修改 02_人工复核指标队列.xlsx
6. 不要修改 06_最终核心财务指标.xlsx
7. 不要扩样本
8. 不要重构主流程
9. 不要重新处理 PDF
10. 不要提交 output 下 Excel/Markdown/PDF/截图产物到 Git
11. 本任务只读 delivery_package 并生成本地 09 fill plan，同时更新 worklog

## input_files
读取：
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\05_表格区域截图索引.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
- D:\_datefac\output\delivery_package\08A_manual_review_shortlist_enhanced.xlsx

## matching_rules
在 02_人工复核指标队列.xlsx 中查找：
- asset_package = H3_AP202605091822098939_1_资产包
- evidence_crop_path 包含 page_001_table_001.png，或 source_table_index 指向同一张截图
- standard_metric 属于：
  - 归属母公司净利润
  - 每股收益
  - P/E
  - P/B
  - EV/EBITDA

优先生成 3-5 条填写方案。

推荐优先级：
1. 归属母公司净利润 2025A = 204.59 百万元
2. 归属母公司净利润 2026E = 288.52 百万元
3. 每股收益 2026E = 1.65 元/股
4. P/E 2026E = 29.97 倍
5. EV/EBITDA 2026E = 22.76 倍

如果 02 中不存在对应 metric 行：
- 不要伪造
- 在 plan 中写 match_status = not_found_in_02
- 给出原因

如果同一 metric 在 02 中只有一行，但只能填写单一年份：
- 只选择一个最适合的年份
- 优先选择 2026E
- 对归属母公司净利润可优先选择 2025A 或 2026E，用于验证小数精度保留

## output_columns
Excel 至少包含：
- plan_rank
- match_status
- manual_queue_row_index
- asset_package
- standard_metric
- year
- corrected_value
- corrected_unit
- review_status
- use_corrected_value
- reviewer
- reviewed_at
- reviewer_note
- evidence_crop_path
- source_row_label
- source_table_index
- source_row_index
- why_this_candidate
- exact_user_action

## suggested_field_rules
对可填写的行，字段建议如下：

- review_status = corrected
- use_corrected_value = 是
- corrected_value = confirmed_values_from_crop 中对应数值
- corrected_unit = confirmed_values_from_crop 中对应单位
- year = 单一年份，如 2026E
- reviewer = 小唐
- reviewed_at = 当前日期，格式 YYYY-MM-DD
- reviewer_note = 根据表格截图 page_001_table_001.png 人工复核，按 PDF 表头单位填写，保留小数精度。

## markdown_format
生成：
D:\_datefac\output\delivery_package\09_manual_review_fill_plan.md

内容包括：

# Manual Review Fill Plan

## Summary
- generated_at
- source_crop
- plan_count
- found_count
- not_found_count
- delivery_status

## Fill Plan Table
列出 3-5 条核心字段：
- row_index
- metric
- year
- corrected_value
- corrected_unit
- exact_user_action

## Details
每条写明：
- 为什么选这条
- 对应截图
- 02 中具体行
- 用户应该填写哪些字段
- 哪些字段不要改

## Do Not Use
说明：
- 不要使用 H3_AP202605141822317484_1_资产包 page_004_table_001.png 填 EPS/P/E/P/B/EV/EBITDA，因为该图是分业务收入及毛利率表。

## validation_steps
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

确认：
- delivery 仍 PASS
- fail_count = 0
- warn_count = 0

检查 09 输出：
- 不包含 TEST
- 不包含 20266
- 不包含 987654.321
- 不包含 ?????
- corrected_value 都来自 confirmed_values_from_crop
- 所有可填写行 year 都是单一年份

## update_worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_manual_review_fill_plan.md

日志必须包含：
- task_title
- started_at
- finished_at
- git_commit_before
- git_commit_after
- commands_run
- files_changed
- outputs_generated
- checks_performed
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

result_summary 必须说明：
- 是否生成 09 md/xlsx
- plan_count
- found_count
- not_found_count
- 推荐填写的 metric/year/value/unit
- delivery check 是否仍为 PASS

next_step_suggestion：
- 用户根据 09 fill plan 手动填写 02
- 填完后运行 apply_manual_review_corrections.py
- 再运行 check_delivery_state.py --json

## git_commit
允许提交：
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package/09_manual_review_fill_plan.md
- output/delivery_package/09_manual_review_fill_plan.xlsx
- output 下任何 Excel/PDF/截图产物

执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare manual review fill plan"
git push origin main
```

## expected_final_state
- delivery check 仍为 PASS
- 本地生成 09_manual_review_fill_plan.md
- 本地生成 09_manual_review_fill_plan.xlsx
- 09 中有 3-5 条候选填写方案，或明确说明缺失原因
- 未修改 01/02/06 正式数据
- 未提交 output 产物到 Git

## safety_notes
- 未运行 factory_core.py
- 未触发 marker/surya/vision/PaddleOCR
- 未下载 model.safetensors
- 未修改 01_自动可信核心指标.xlsx
- 未修改 02_人工复核指标队列.xlsx
- 未修改 06_最终核心财务指标.xlsx
- 未提交 PDF 原文
- 未提交完整 Excel 产物
