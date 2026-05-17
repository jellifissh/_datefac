# NEXT CODEX TASK

## task_title
准备正式人工复核 3-5 条真实指标候选清单

## project
D:\_datefac

## current_status
上一阶段已完成 delivery_package 清洁验收：
- overall_status = PASS
- pass_count = 12
- warn_count = 0
- fail_count = 0
- test_token_hits 行数 = 0
- duplicate_keys 为空
- high_risk_flags 为空
- 06_final 中不再存在 20266
- 06C 模板中的 TEST / 987654.321 已清理

当前阶段目标不是修改数据，而是为用户准备正式人工复核候选清单。

## goal
从 delivery_package 的人工复核队列中，挑选 3-5 条最适合人工复核的真实指标，生成一个可读的复核候选清单，方便用户打开截图/PDF 核对后填写 02_人工复核指标队列.xlsx。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要修改 02_人工复核指标队列.xlsx
6. 不要修改 06_最终核心财务指标.xlsx
7. 不要扩样本
8. 不要重构主流程
9. 不要提交 output 下 Excel/PDF/截图产物到 Git
10. 本任务只读 delivery_package，并生成候选清单文件到本地 output/delivery_package，同时更新 worklog

## input_files
读取以下本地产物：
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\05_表格区域截图索引.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx

如果存在，也可辅助读取：
- D:\_datefac\output\delivery_package\06B_未解决问题清单.xlsx
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx

## candidate_selection_rules
优先选择符合以下条件的候选项：
1. 来自 02_人工复核指标队列.xlsx
2. 不是 TEST / 20266 / 987654.321 测试值
3. 有明确 asset_package
4. 有明确 standard_metric
5. 有明确 year 或可从 raw_value_examples/source_column 推断单一年份
6. 有 evidence_crop_path 或可通过 source_table_index 在 05_表格区域截图索引.xlsx 找到截图证据
7. 更优先选择当前业务上最关键的指标：
   - 归属母公司净利润
   - 每股收益
   - P/E
   - P/B
   - EV/EBITDA
8. 优先覆盖不同指标，不要 5 条全是同一个指标
9. 如果同一个指标有多个年份，优先选择 2025A、2026E、2027E 中最容易核对的 1-2 条
10. 不要选择已经在 06 中自动可信且没有问题的营业收入，除非它仍在 02 中需要验证

## output_files
在本地生成：

1. Markdown 清单：
D:\_datefac\output\delivery_package\08_manual_review_shortlist.md

2. Excel 清单：
D:\_datefac\output\delivery_package\08_manual_review_shortlist.xlsx

注意：这两个 output 文件不要加入 Git。

## output_content_requirements
每条候选至少包含：
- rank
- asset_package
- source_pdf
- standard_metric
- year
- current_value 或 raw_value_examples
- current_status / recommendation / issue_flags
- source_row_label
- source_table_index
- source_row_index
- evidence_crop_path
- suggested_review_action
- suggested_fields_to_fill
- reviewer_instruction

`suggested_fields_to_fill` 应明确告诉用户如果核对通过，应该在 02 中填写哪些字段，例如：
- review_status = corrected 或 accepted
- use_corrected_value = 是
- corrected_value = 需要用户从 PDF/截图确认后的值
- corrected_unit = 亿元 / 元 / 倍 / %
- year = 单一年份，例如 2026E
- reviewer = 用户自定
- reviewed_at = 当前日期
- reviewer_note = 简短说明

## markdown_format
Markdown 文件应包含：

# Manual Review Shortlist

## Summary
- generated_at
- source_file
- candidate_count
- selection_scope
- warnings

## Candidates
每条候选用二级标题：

### 1. 归属母公司净利润 - 2026E
- asset_package:
- source_pdf:
- current/raw value:
- issue_flags:
- source row:
- evidence crop:
- suggested fill:
- reviewer instruction:

## Notes
说明：
- 本清单只用于人工复核准备
- 未修改 02/06
- 用户核对截图/PDF 后再填写 02

## validation_steps
执行以下检查：

1. 确认 delivery 状态仍为 PASS：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

2. 确认：
- fail_count = 0
- test_token_hits 行数 = 0
- duplicate_keys 为空
- high_risk_flags 为空

3. 确认生成的 shortlist 不包含测试值：
- TEST
- 20266
- 987654.321

## update_worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_manual_review_shortlist.md

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
- 是否生成 08_manual_review_shortlist.md
- 是否生成 08_manual_review_shortlist.xlsx
- 候选数量
- 候选指标列表
- 是否保持 delivery check PASS

next_step_suggestion：
- 用户打开 08_manual_review_shortlist.md 和 evidence_crop_path 对应截图
- 人工确认 3-5 条真实指标
- 再填写 02_人工复核指标队列.xlsx

## git_commit
允许提交：
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package/08_manual_review_shortlist.md
- output/delivery_package/08_manual_review_shortlist.xlsx
- output 下任何 Excel/PDF/截图产物

执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare manual review shortlist"
git push origin main
```

## expected_final_state
- delivery check 仍为 PASS
- 本地生成 08_manual_review_shortlist.md
- 本地生成 08_manual_review_shortlist.xlsx
- 候选数量为 3-5 条
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
