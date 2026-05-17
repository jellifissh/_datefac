# NEXT CODEX TASK

## task_title
清理 delivery_package 中的测试值 20266

## project
D:\_datefac

## current_problem
check_delivery_state.py 当前结果：
- overall_status=FAIL
- fail_count=1
- warn_count=2

失败原因：
- test_tokens 检测到正式数据中存在测试值 20266

污染位置：
- 02_人工复核指标队列.xlsx
- 06_最终核心财务指标.xlsx
- 06A_人工修正应用明细.xlsx

同时存在：
- corrected_value 列尾随空格问题（corrected_value ）

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors
4. 不要直接修改 01_自动可信核心指标.xlsx
5. 只允许修改 02_人工复核指标队列.xlsx 中人工复核填写列
6. 不要扩样本
7. 不要重构主流程

## objectives
1. 备份 delivery_package 关键文件
2. 清理 02 中测试复核值 20266
3. 规范 corrected_value 列名
4. 重跑 apply_manual_review_corrections.py
5. 重跑 check_delivery_state.py
6. 确认 fail_count=0
7. 更新 codex_worklog
8. git commit + push

## required_steps
### 1. 检查 Git 状态
执行：
- git status
- git pull origin main
- git log --oneline --decorate -5

### 2. 备份文件
在 output/delivery_package 下创建：
- _backup_before_clean_YYYYMMDD_HHMMSS

备份：
- 02_人工复核指标队列.xlsx
- 06_最终核心财务指标.xlsx
- 06A_人工修正应用明细.xlsx
- 06B_未解决问题清单.xlsx
- 06C_复核模板说明.md
- 06D_人工复核回写诊断.xlsx
- 07_delivery_state_check.xlsx

### 3. 清理测试值
文件：
- 02_人工复核指标队列.xlsx

要求：
- 规范 corrected_value 列名
- 去除 corrected_value 尾随空格列
- 清理 20266 / 20266.0
- 清空测试行人工复核字段
- 不修改来源字段

### 4. 重新生成结果
执行：
- apply_manual_review_corrections.py
- check_delivery_state.py --json

确认：
- fail_count=0
- duplicate_keys 空
- high_risk_flags 空
- test_token_hits 无 ERROR

### 5. 更新 Worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_clean_20266.md

日志中必须记录：
- backup_dir
- cleaned_20266_rows
- corrected_value_column_normalized
- apply_manual_review summary
- check_delivery_state summary
- remaining_issues
- next_step_suggestion

## expected_final_state
理想结果：
- fail_count = 0
- overall_status = PASS 或 WARN
- 06 中不再存在 20266
- corrected_value 列规范
- duplicate_key_count_final = 0

## safety_notes
- 不要运行 factory_core.py
- 不要触发视觉模型
- 不要下载模型
- 不要修改 01
- 不要提交 PDF 原文
- 不要提交完整 Excel 数据
