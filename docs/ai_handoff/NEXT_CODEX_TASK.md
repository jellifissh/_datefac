# NEXT CODEX TASK

## task_title
重新生成增强版人工复核候选清单，修复 year 为空和中文乱码问题

## project
D:\_datefac

## current_status
上一轮已生成：
- D:\_datefac\output\delivery_package\08_manual_review_shortlist.md
- D:\_datefac\output\delivery_package\08_manual_review_shortlist.xlsx

但用户上传后检查发现该 shortlist 质量不足，不能直接用于正式人工复核。

已发现问题：
1. 5 条候选的 year 全部为空
2. Markdown 与 Excel 中 suggested_fill / reviewer_instruction 出现大量 ?????，疑似编码或模板字符串问题
3. 部分 current_value 是混合文本，例如：
   - 归属母公司净利润: 328.75|现金流量净额|198.73
   - 每股收益: 2.75|每股收益|0.56
   - P/E: 应收票据及应收账款 74|58.0|75.0
   - P/B: 预付款项 4|11.0|16.0
   - EV/EBITDA: 9.15|每股经营现金|0.66
4. 这说明候选能定位截图，但不能直接指导用户填写 02
5. 不能把 mixed_text 里的数字直接当 corrected_value

当前 delivery_package 已是干净状态：
- overall_status = PASS
- fail_count = 0
- warn_count = 0
- test_token_hits = 0
- duplicate_keys 为空
- high_risk_flags 为空

## goal
生成增强版人工复核候选清单：

- D:\_datefac\output\delivery_package\08A_manual_review_shortlist_enhanced.md
- D:\_datefac\output\delivery_package\08A_manual_review_shortlist_enhanced.xlsx

该清单要比 08 更适合用户实际操作：
1. year 不能空
2. 如果不能自动确定 year，必须写 `year_needs_manual`，并解释原因
3. 中文说明必须正常显示，不允许出现 ????? 乱码
4. 每条候选必须有 can_write_to_02 字段
5. 若 year 不明确或 value 是混合文本，can_write_to_02 必须为 no
6. 每条候选必须明确用户下一步应该看哪张截图、该核对什么
7. 不得直接修改 02，只生成候选清单

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
11. 本任务只读 delivery_package，并生成本地 08A shortlist，同时更新 worklog

## input_files
读取：
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\05_表格区域截图索引.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
- D:\_datefac\output\delivery_package\08_manual_review_shortlist.xlsx
- D:\_datefac\output\delivery_package\08_manual_review_shortlist.md

如果存在，也可辅助读取：
- D:\_datefac\output\delivery_package\06B_未解决问题清单.xlsx
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx
- 相关资产包下 05_核心财务指标标准化.xlsx
- 相关资产包下 02A_研报原始表格资产.xlsx
- 相关资产包下 02_研报全量结构化数据.xlsx

## selection_and_enhancement_rules
从 02 人工复核队列或 08 shortlist 中重新挑选 3-5 条候选。

优先指标：
1. 归属母公司净利润
2. 每股收益
3. P/E
4. P/B
5. EV/EBITDA

增强规则：
1. 不要输出空 year。
2. 如果能从 source_column、raw_value_examples、value_year、target_year、year 等字段确定单一年份，则填具体年份，如 2025A / 2026E / 2027E。
3. 如果无法确定单一年份，填 `year_needs_manual`，并在 year_reason 中说明为什么。
4. 如果 current_value/raw_value_examples 是混合文本，不能把其中任意数字直接当 corrected_value。
5. 如果 evidence_crop_path 存在，保留完整路径。
6. 如果 evidence_crop_path 缺失，尝试根据 asset_package + source_table_index 从 05_表格区域截图索引.xlsx 补充。
7. 如果仍找不到截图，写 evidence_missing。
8. 如果候选指向明显错行，例如 P/E 值混入“应收票据及应收账款”，P/B 值混入“预付款项”，必须标记：suspected_row_mismatch。
9. 对 suspected_row_mismatch 的候选，can_write_to_02 必须为 no，用户只能用它定位问题，不能直接照填。
10. 如果候选可以人工核对后填写 02，can_write_to_02 可以为 yes_after_manual_check。

## output_columns
Excel 至少包含以下列：
- rank
- asset_package
- source_pdf
- standard_metric
- year
- year_reason
- current_value
- raw_value_examples
- current_status
- issue_flags
- suspected_problem_type
- can_write_to_02
- source_row_label
- source_table_index
- source_row_index
- evidence_crop_path
- what_to_check_in_crop
- suggested_review_status
- suggested_use_corrected_value
- suggested_corrected_value
- suggested_corrected_unit
- suggested_reviewer_note
- reviewer_instruction

## output_content_rules
### suggested_corrected_value
- 如果值不能从当前数据中可靠确定，写：`manual_from_pdf`
- 不要写 ?????
- 不要写 TEST
- 不要写 987654.321
- 不要写 20266

### suggested_corrected_unit
根据指标给出默认建议：
- 归属母公司净利润：亿元 或 百万元，必须提示用户按 PDF 表头单位确认
- 每股收益：元/股
- P/E：倍
- P/B：倍
- EV/EBITDA：倍

### reviewer_instruction
必须是清楚中文，不允许乱码。例如：
- 打开 evidence_crop_path 对应截图，定位 source_row_label 所在行，核对目标年份列的数值；确认后在 02 中填写 corrected_value、corrected_unit、year、review_status 和 reviewer_note。

## markdown_format
生成：
D:\_datefac\output\delivery_package\08A_manual_review_shortlist_enhanced.md

格式：

# Enhanced Manual Review Shortlist

## Summary
- generated_at
- candidate_count
- delivery_check_status
- main_improvements

## Candidate Table
用 Markdown 表格列出 3-5 条核心字段：
- rank
- metric
- year
- can_write_to_02
- suspected_problem_type
- evidence_crop_path

## Candidate Details
每条候选必须包含：
- metric/year
- asset_package
- current/raw value
- issue_flags
- evidence crop
- what to check
- suggested fill
- reviewer instruction

## Warnings
说明：
- year_needs_manual 的候选不能直接回写
- suspected_row_mismatch 的候选不能直接照填数值

## validation_steps
1. 运行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

2. 确认：
- overall_status = PASS
- fail_count = 0
- warn_count = 0

3. 检查 08A 输出：
- 不包含 TEST
- 不包含 987654.321
- 不包含 20266
- 不包含 ?????
- year 列没有空值
- 如果无法确定年份，必须写 year_needs_manual

## update_worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_enhance_manual_review_shortlist.md

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
- 是否生成 08A md/xlsx
- 08A 候选数量
- 候选指标列表
- year_needs_manual 数量
- suspected_row_mismatch 数量
- can_write_to_02=yes_after_manual_check 数量
- delivery check 是否仍为 PASS

next_step_suggestion：
- 用户查看 08A enhanced shortlist 和截图
- 用户选择 3-5 条真正能确认的指标
- 若用户上传截图/PDF，ChatGPT 可辅助判断该填哪些字段

## git_commit
允许提交：
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package/08A_manual_review_shortlist_enhanced.md
- output/delivery_package/08A_manual_review_shortlist_enhanced.xlsx
- output 下任何 Excel/PDF/截图产物

执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "enhance manual review shortlist"
git push origin main
```

## expected_final_state
- delivery check 仍为 PASS
- 本地生成 08A_manual_review_shortlist_enhanced.md
- 本地生成 08A_manual_review_shortlist_enhanced.xlsx
- 08A 中没有乱码 ?????
- 08A 中 year 没有空值
- 08A 中没有 TEST/20266/987654.321
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
