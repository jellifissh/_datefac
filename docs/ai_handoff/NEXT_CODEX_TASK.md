# NEXT CODEX TASK

## task_title
清理 06C 模板示例中的 TEST/987654.321 警告，并完成 PASS 验收

## project
D:\_datefac

## current_status
用户已手动完成 06 文件覆盖，并重新运行 check_delivery_state.py。

当前检查结果：
- overall_status = WARN
- pass_count = 11
- warn_count = 1
- fail_count = 0
- check_count = 13

当前非 PASS 项：
1. 06_final_high_risk_flags
   - status = SKIP
   - severity = INFO
   - detail = no_flag_columns
   - 这不是问题，不阻断

2. test_tokens
   - status = WARN
   - severity = WARN
   - detail = hard_hits=0; template_hits=2
   - 仅剩模板示例中存在 TEST 和 987654.321

当前 test_token_hits：
- file_key = 06C_template, token = TEST, severity = WARN
- file_key = 06C_template, token = 987654.321, severity = WARN

结论：
- 正式数据中的 20266 污染已清理
- 06_final 中已无 20266
- duplicate_keys 为空
- high_risk_flags 为空
- manual_review_issues 为空
- 当前只剩模板示例值导致 WARN

## goal
把 06C_复核模板说明.md 中的示例值从测试风格改成业务风格，使 check_delivery_state.py 达到 PASS 或仅剩非阻断 INFO。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要扩样本
6. 不要重构主流程
7. 不要重新处理 PDF
8. 不要提交 output 下 Excel 或 md 产物到 Git
9. 只允许修改生成 06C 模板说明的代码，或在本地重建 06C 验证效果

## target_files_to_inspect
优先检查：
- D:\_datefac\tools\apply_manual_review_corrections.py

查找以下测试示例字符串：
- TEST
- 987654.321
- 20266

## required_changes
在生成 06C_复核模板说明.md 的模板内容中：

把测试示例：
- corrected_value = 987654.321
- reviewer_note = TEST 或含 TEST 的示例

替换成业务示例：
- corrected_value = 204.59
- corrected_unit = 亿元
- reviewer_note = 根据 PDF 原表复核，归母净利润保留两位小数

要求：
- 不要使用 TEST
- 不要使用 987654.321
- 不要使用 20266
- 示例应贴近当前项目的金融指标语境

## validation_steps
### 1. 检查代码中是否仍有测试 token
在项目代码中搜索：
- TEST
- 987654.321
- 20266

要求：
- 如果测试 token 只存在于历史文档或 worklog，可记录但不视为阻断
- 如果存在于会生成 delivery 产物的代码中，应清理

### 2. 重新运行人工复核回写
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\apply_manual_review_corrections.py
```

目的：
- 重新生成 06C_复核模板说明.md
- 不改变 01
- 不运行 factory_core.py

### 3. 重新运行状态检查
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

确认：
- fail_count = 0
- test_token_hits 无 ERROR
- template_hits = 0 或不再包含 TEST/987654.321
- duplicate_keys 为空
- high_risk_flags 为空

### 4. 读取 07_delivery_state_check.xlsx 验证
读取：
- summary
- checks
- test_token_hits

记录：
- overall_status
- pass_count
- warn_count
- fail_count
- test_token_hits 行数

## update_worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_clean_template_tokens.md

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
- 是否清理了 06C 模板中的 TEST/987654.321
- 是否重跑 apply_manual_review_corrections.py
- 是否重跑 check_delivery_state.py
- 最终 overall_status/pass/warn/fail

next_step_suggestion：
如果 fail_count=0 且无 test token WARN，下一步进入：
1. 正式人工复核 3~5 条真实指标
2. 之后追踪归母净利润小数精度问题

## git_commit
允许提交：
- tools/apply_manual_review_corrections.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package 下任何 Excel/md 产物
- PDF 原文
- 截图资产

执行：

```bat
git add tools/apply_manual_review_corrections.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "clean manual review template examples"
git push origin main
```

## expected_final_state
- overall_status = PASS 或仅剩非阻断 INFO/SKIP
- fail_count = 0
- test_token_hits 不再包含 TEST / 987654.321 / 20266
- 06_final 中无 20266
- duplicate_keys 为空
- high_risk_flags 为空

## safety_notes
- 未运行 factory_core.py
- 未触发 marker/surya/vision/PaddleOCR
- 未下载 model.safetensors
- 未修改 01_自动可信核心指标.xlsx
- 未提交 PDF 原文
- 未提交完整 Excel 产物
