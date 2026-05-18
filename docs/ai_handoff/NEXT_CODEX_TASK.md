# NEXT CODEX TASK

## task_title
将首批已确认真实指标写入 02 人工复核队列并回写验证

## project
D:\_datefac

## current_status
用户已上传 09_manual_review_fill_plan.md/xlsx。该计划可用，但存在一个关键注意点：
- row_index=1 同时出现“归属母公司净利润 2025A”和“归属母公司净利润 2026E”两个计划。
- 02_人工复核指标队列.xlsx 的单行只能填写一个 year，不能在同一行同时回写两个年份。
- 因此本轮首批回写只选择 2026E，不同时写 2025A。

当前 delivery 状态：
- overall_status = PASS
- fail_count = 0
- warn_count = 0
- duplicate_keys 为空
- high_risk_flags 为空

## confirmed_values_from_user_crop
用户已上传截图 page_001_table_001.png，表为“盈利预测和财务指标”。

截图确认值：
- 归属母公司净利润 2026E = 288.52，单位：百万元
- 每股收益 2026E = 1.65，单位：元/股
- P/E 2026E = 29.97，单位：倍
- EV/EBITDA 2026E = 22.76，单位：倍

暂不写入：
- 归属母公司净利润 2025A = 204.59
原因：与 2026E 使用同一个 02 row_index=1，当前回写脚本要求单行对应单一年份。后续如需多年份修正，应单独设计“同指标多年份拆行/多修正行”策略。

## target_manual_corrections
本轮只写入以下 4 条，必须逐条匹配 02 中对应行：

| manual_queue_row_index | standard_metric | year | corrected_value | corrected_unit |
|---:|---|---|---:|---|
| 1 | 归属母公司净利润 | 2026E | 288.52 | 百万元 |
| 4 | 每股收益 | 2026E | 1.65 | 元/股 |
| 5 | P/E | 2026E | 29.97 | 倍 |
| 7 | EV/EBITDA | 2026E | 22.76 | 倍 |

人工复核字段统一填写：
- review_status = corrected
- use_corrected_value = 是
- reviewer = 小唐
- reviewed_at = 当前日期，格式 YYYY-MM-DD
- reviewer_note = 根据 page_001_table_001.png 人工复核，按 PDF 表头单位填写，保留小数精度。

## goal
1. 备份 02/06/06A/06B/06D/07。
2. 只修改 02_人工复核指标队列.xlsx 中上述 4 行的人工复核填写字段。
3. 不修改来源字段。
4. 运行 apply_manual_review_corrections.py。
5. 运行 check_delivery_state.py --json。
6. 确认 06 中出现上述 4 条人工修正值。
7. 确认 duplicate_key_count_final = 0。
8. 确认 delivery check 仍为 PASS 或无 FAIL。
9. 更新 worklog 并 git commit + push。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要直接修改 01_自动可信核心指标.xlsx
5. 不要扩样本
6. 不要重构主流程
7. 不要重新处理 PDF
8. 不要提交 output 下 Excel/Markdown/PDF/截图产物到 Git
9. 只允许修改 02_人工复核指标队列.xlsx 的人工复核填写列
10. 不要修改 02 中来源字段，包括 asset_package、standard_metric、source_*、evidence_crop_path、raw_value_examples、recommendation 等

## input_files
读取：
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\09_manual_review_fill_plan.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx

## required_steps

### 1. 同步 Git
执行：

```bat
cd /d D:\_datefac
git pull origin main
git status --short
git log --oneline --decorate -5
```

记录 git_commit_before。

### 2. 备份关键文件
在 delivery_package 下创建：

```text
_backup_before_apply_manual_review_YYYYMMDD_HHMMSS
```

备份存在的以下文件：
- 02_人工复核指标队列.xlsx
- 06_最终核心财务指标.xlsx
- 06A_人工修正应用明细.xlsx
- 06B_未解决问题清单.xlsx
- 06D_人工复核回写诊断.xlsx
- 07_delivery_state_check.xlsx

### 3. 检查并规范 02 的人工复核列
确保存在以下列：
- review_status
- use_corrected_value
- corrected_value
- corrected_unit
- year
- reviewer
- reviewed_at
- reviewer_note

如果存在 corrected_value 尾随空格列或重复近似列：
- 先规范为唯一 corrected_value
- 不要引入 corrected_value.1 等重复列
- 若发现冲突，记录到 worklog，不要静默覆盖

### 4. 写入 4 条人工复核字段
只写以下 4 行：

#### row_index=1
- standard_metric 应为：归属母公司净利润
- year = 2026E
- corrected_value = 288.52
- corrected_unit = 百万元
- review_status = corrected
- use_corrected_value = 是
- reviewer = 小唐
- reviewed_at = 当前日期
- reviewer_note = 根据 page_001_table_001.png 人工复核，按 PDF 表头单位填写，保留小数精度。

#### row_index=4
- standard_metric 应为：每股收益
- year = 2026E
- corrected_value = 1.65
- corrected_unit = 元/股
- review_status = corrected
- use_corrected_value = 是
- reviewer = 小唐
- reviewed_at = 当前日期
- reviewer_note = 根据 page_001_table_001.png 人工复核，按 PDF 表头单位填写，保留小数精度。

#### row_index=5
- standard_metric 应为：P/E
- year = 2026E
- corrected_value = 29.97
- corrected_unit = 倍
- review_status = corrected
- use_corrected_value = 是
- reviewer = 小唐
- reviewed_at = 当前日期
- reviewer_note = 根据 page_001_table_001.png 人工复核，按 PDF 表头单位填写，保留小数精度。

#### row_index=7
- standard_metric 应为：EV/EBITDA
- year = 2026E
- corrected_value = 22.76
- corrected_unit = 倍
- review_status = corrected
- use_corrected_value = 是
- reviewer = 小唐
- reviewed_at = 当前日期
- reviewer_note = 根据 page_001_table_001.png 人工复核，按 PDF 表头单位填写，保留小数精度。

如果 row_index 对应 standard_metric 不一致：
- 不要写入该行
- 记录 mismatch 到 worklog
- 不要自行寻找替代行，除非能唯一匹配 asset_package + standard_metric + evidence_crop_path

### 5. 运行人工回写
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\apply_manual_review_corrections.py
```

记录输出：
- corrected_value_non_empty_rows
- effective_correction_rows
- applied_override_count
- applied_new_manual_count
- unresolved_count
- final_rows
- duplicate_key_count_final

### 6. 运行状态检查
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

确认：
- fail_count = 0
- duplicate_keys 为空
- high_risk_flags 为空
- test_token_hits 行数 = 0

### 7. 验证 06 最终表
读取：

```text
D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
```

确认存在以下最终值：
- 归属母公司净利润 2026E = 288.52，final_value_source 应体现人工修正或 manual correction
- 每股收益 2026E = 1.65，final_value_source 应体现人工修正或 manual correction
- P/E 2026E = 29.97，final_value_source 应体现人工修正或 manual correction
- EV/EBITDA 2026E = 22.76，final_value_source 应体现人工修正或 manual correction

同时确认：
- duplicate_key_count_final = 0

## update_worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_apply_confirmed_manual_review.md

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
- 是否成功写入 4 条 02 人工字段
- applied_override_count
- applied_new_manual_count
- duplicate_key_count_final
- delivery check 是否 PASS/FAIL
- 06 中是否验证到 4 条人工修正值

next_step_suggestion：
- 如果成功，下一步追踪归母净利润 2025A/2027E/2028E 多年份小数精度问题
- 或设计“同一 02 行多年份人工修正拆行策略”

## git_commit
只提交 worklog 文档：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "apply confirmed manual review corrections"
git push origin main
```

不要提交 output 下任何 Excel/PDF/截图产物。

## expected_final_state
- 02 中 4 行人工复核字段已填写
- apply_manual_review_corrections.py 成功应用
- 06 中有 4 条人工修正值
- duplicate_key_count_final = 0
- check_delivery_state.py 无 FAIL
- 未修改 01
- 未提交 output 产物到 Git

## safety_notes
- 未运行 factory_core.py
- 未触发 marker/surya/vision/PaddleOCR
- 未下载 model.safetensors
- 未修改 01_自动可信核心指标.xlsx
- 未提交 PDF 原文
- 未提交完整 Excel 产物
