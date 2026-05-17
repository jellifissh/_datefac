# NEXT CODEX TASK

## task_title
覆盖旧 06 文件并完成 delivery 最终验收

## project
D:\_datefac

## current_status
当前 check_delivery_state.py 结果：
- overall_status = FAIL
- pass_count = 11
- warn_count = 0
- fail_count = 1

唯一失败项：
- check_name = test_tokens

当前 test_token_hits：
- file_key = 06_final, row_index = 5, column = final_value, token = 20266, cell_value = 20266.0, severity = ERROR
- file_key = 06_final, row_index = 5, column = corrected_value, token = 20266, cell_value = 20266.0, severity = ERROR

结论：
- 02_人工复核指标队列.xlsx 中的 20266 已经清理
- corrected_value 列名问题已经处理
- 06A/06B/06C/06D 已重建
- duplicate_keys 为空
- high_risk_flags 为空
- 当前只剩旧的 06_最终核心财务指标.xlsx 仍含 20266
- 上一轮生成过干净副本，但原 06 文件疑似被 Excel/WPS/预览器占用，导致覆盖失败

已知干净副本路径：
D:\_datefac\output\delivery_package\06_最终核心财务指标_copy_20260517_212724.xlsx

目标：
1. 关闭/解除 06_最终核心财务指标.xlsx 文件占用
2. 用干净副本覆盖原始 06 文件
3. 重新运行 check_delivery_state.py --json
4. 确认 fail_count = 0
5. 更新 docs/codex_worklog/LATEST.md 和 history
6. git commit + push worklog 文档

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要扩样本
6. 不要重构主流程
7. 不要重新处理 PDF
8. 不要提交 output 下 Excel 文件到 Git
9. 本次只做 06 覆盖和验收，不要再改 02，除非检查发现 02 又出现 20266

## required_steps

### 1. 同步代码与确认状态
执行：

```bat
cd /d D:\_datefac
git pull origin main
git status --short
git log --oneline --decorate -5
```

记录执行前 commit。

### 2. 关闭文件占用
请人工/程序确认以下文件没有被打开：

```text
D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
```

重点检查：
- Excel
- WPS
- VSCode Excel 插件
- Windows 资源管理器预览窗格
- Python/Jupyter 进程

如果文件被占用：
- 先关闭相关程序
- 不要强行删除
- 在 worklog 中记录文件锁原因

### 3. 备份当前旧 06 文件
在 delivery_package 下创建或使用已有备份目录：

```text
_backup_before_final_06_overwrite_YYYYMMDD_HHMMSS
```

把当前旧文件复制进去：

```text
06_最终核心财务指标.xlsx
```

### 4. 用干净副本覆盖原 06 文件
确认副本存在：

```text
D:\_datefac\output\delivery_package\06_最终核心财务指标_copy_20260517_212724.xlsx
```

覆盖目标：

```text
D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
```

建议用 Python/shutil.copy2 或 PowerShell Copy-Item 执行。

覆盖后立即读取新 06，确认：
- final_value 不含 20266
- corrected_value 不含 20266

如果副本不存在：
- 不要猜
- 重新运行 apply_manual_review_corrections.py 前先确认 02 中 corrected_value 已为空且无 20266
- 然后运行 apply_manual_review_corrections.py 生成新的干净 06

### 5. 重新运行状态检查
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

然后读取：

```text
D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
```

检查 sheet：
- checks
- test_token_hits
- duplicate_keys
- high_risk_flags

必须确认：
- fail_count = 0
- test_token_hits 无 ERROR
- duplicate_keys 为空
- high_risk_flags 为空
- 06_final 不再有 20266

06C_template 中如果仍有 TEST/987654.321 WARN，不作为阻断，但建议后续单独优化模板示例。

### 6. 更新 Codex Worklog
更新：

```text
docs/codex_worklog/LATEST.md
```

新增：

```text
docs/codex_worklog/history/YYYYMMDD_HHMMSS_finalize_06_overwrite.md
```

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

result_summary 必须写清楚：
- 是否成功覆盖 06
- 覆盖前备份目录
- 最终 overall_status
- 最终 fail_count
- test_token_hits 是否仍有 ERROR
- duplicate_keys 是否为空
- high_risk_flags 是否为空

safety_notes 必须写：
- 未运行 factory_core.py
- 未触发 marker/surya/vision/PaddleOCR
- 未下载 model.safetensors
- 未修改 01_自动可信核心指标.xlsx
- 未提交 PDF 原文或完整 Excel 产物

### 7. Git 提交
只提交 worklog 文档：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "finalize 06 clean validation"
git push origin main
```

## expected_final_state
- overall_status = PASS 或 WARN
- fail_count = 0
- 06_final 中不存在 20266
- test_token_hits 无 ERROR
- duplicate_keys = 空
- high_risk_flags = 空

## next_expected_phase
如果 fail_count=0：
下一步进入正式人工复核 3~5 条真实指标。
之后再追踪归母净利润小数精度问题。
