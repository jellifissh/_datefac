# NEXT CODEX TASK

## task_title
清理 delivery_package 中的人工复核测试值 20266，并重建 06/07 验收结果

## project
D:\_datefac

## background
当前项目是券商研报 PDF 自动结构化系统。当前阶段不是重新抽取 PDF，而是维护已生成的 delivery_package 与人工复核回写闭环。

当前 delivery 状态检查结果：
- overall_status = FAIL
- pass_count = 9
- warn_count = 2
- fail_count = 1

失败项：
- check_name = test_tokens

问题本质：
- 之前人工复核测试值 20266 被写入了 02_人工复核指标队列.xlsx
- apply_manual_review_corrections.py 又把这个测试值回写到了 06_最终核心财务指标.xlsx 和 06A_人工修正应用明细.xlsx
- 这属于交付级污染，必须先清理再继续正式人工复核

已知污染位置：
1. D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
   - row_index = 0
   - column = corrected_value （注意末尾有空格）
   - value = 20266.0

2. D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
   - row_index = 5
   - columns = final_value / corrected_value
   - value = 20266.0

3. D:\_datefac\output\delivery_package\06A_人工修正应用明细.xlsx
   - row_index = 136
   - columns = corrected_value / final_value
   - value = 20266.0

同时存在的结构问题：
- 02_人工复核指标队列.xlsx 中存在 corrected_value 末尾空格列：`corrected_value `
- check_delivery_state.py 因精确列名检查，认为缺少标准 `corrected_value` 列
- 这会导致 manual_queue_required_review_columns = WARN

## hard_constraints
必须严格遵守：
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要直接修改 01_自动可信核心指标.xlsx
5. 不要扩样本
6. 不要重构主流程
7. 不要修改 PDF、原始资产包、02A、02B、05、08、19、22、23、24、26 等上游产物
8. 只允许修改 02_人工复核指标队列.xlsx 中的人工复核填写列
9. 06/06A/06B/06C/06D/07 是生成结果，可以通过脚本重建
10. 不要提交 PDF 原文、完整 Excel 产物或敏感数据到 Git
11. 本次 Git 提交只提交 docs/codex_worklog 相关日志，不提交 output 下的 Excel 产物

## objectives
本次任务目标：
1. 备份 delivery_package 关键文件
2. 规范 02_人工复核指标队列.xlsx 中 corrected_value 列名
3. 清理 02 中测试复核值 20266
4. 只清空测试行的人工填写字段，不改来源字段
5. 重新运行 apply_manual_review_corrections.py
6. 重新运行 check_delivery_state.py --json
7. 确认 fail_count = 0
8. 确认 06 中不再存在 20266
9. 更新 docs/codex_worklog/LATEST.md
10. 新增 docs/codex_worklog/history/YYYYMMDD_HHMMSS_clean_20266.md
11. git commit + push worklog 文档

## required_steps

### 1. 确认 Git 状态
在 PowerShell 或 cmd 中执行：

```bat
cd /d D:\_datefac
git status
git pull origin main
git log --oneline --decorate -5
```

要求：
- 如果工作区有未提交代码修改，先记录到 worklog，不要覆盖
- 如果只是 output 下未跟踪/修改文件，不要加入 Git
- 记录执行前 commit 作为 git_commit_before

### 2. 创建备份目录
在：

```text
D:\_datefac\output\delivery_package
```

创建目录：

```text
_backup_before_clean_YYYYMMDD_HHMMSS
```

复制以下文件进去，如果存在就复制：
- 02_人工复核指标队列.xlsx
- 06_最终核心财务指标.xlsx
- 06A_人工修正应用明细.xlsx
- 06B_未解决问题清单.xlsx
- 06C_复核模板说明.md
- 06D_人工复核回写诊断.xlsx
- 07_delivery_state_check.xlsx

要求：
- 在 worklog 中记录 backup_dir
- 记录实际备份了哪些文件

### 3. 只清理 02_人工复核指标队列.xlsx
目标文件：

```text
D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
```

建议使用 Python + pandas/openpyxl 处理，不要人工手点 Excel。

#### 3.1 识别 corrected_value 近似列
检查所有列名，识别：
- `corrected_value`
- `corrected_value `
- ` corrected_value`
- `corrected_value.1`
- 其他只因空格、大小写、pandas 后缀导致的 corrected_value 近似列

#### 3.2 规范为唯一 corrected_value 列
规则：
1. 如果只有 `corrected_value ` 末尾空格列：
   - 直接重命名为 `corrected_value`

2. 如果 `corrected_value` 和 `corrected_value ` 同时存在：
   - 逐行合并
   - 优先保留非空值
   - 如果同一行两个列都有非空且值不同：
     - 记录冲突到 worklog
     - 不要静默覆盖
   - 合并后删除多余列

3. 最终 02 中应只有一个标准列：
   - `corrected_value`

#### 3.3 定位测试行
定位方式：
- row_index = 0

或满足以下条件：
- asset_package = H3_AP202605091822098939_1_资产包
- standard_metric = 营业收入
- year = 2026E
- corrected_value = 20266 或 20266.0

#### 3.4 清空测试行人工复核字段
只清空以下人工填写字段：
- review_status
- use_corrected_value
- corrected_value
- corrected_unit
- reviewer
- reviewed_at
- reviewer_note

如果这些列不存在：
- 可以创建缺失的人工复核列为空列
- 但不要改其他来源字段

#### 3.5 禁止修改来源字段
不要修改以下字段：
- asset_package
- standard_metric
- metric_value_status
- value_issue_flags
- raw_value_examples
- source_row_label
- source_table_index
- source_row_index
- evidence_crop_path
- recommendation
- source

#### 3.6 保存 02
保存回：

```text
D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
```

worklog 中记录：
- cleaned_20266_rows
- corrected_value_column_normalized: yes/no
- corrected_value_conflict_count
- touched_rows
- touched_columns

### 4. 重新运行人工复核回写
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\apply_manual_review_corrections.py
```

记录终端输出中的：
- trusted_input_rows
- manual_review_rows
- corrected_value_non_empty_rows
- effective_correction_rows
- applied_override_count
- applied_new_manual_count
- ignored_pending_count
- rejected_or_not_applicable_count
- invalid_missing_key_count
- invalid_missing_year_count
- invalid_multi_year_count
- unresolved_count
- final_rows
- duplicate_key_count_final
- diagnosis_report_path
- output_paths

### 5. 重新运行 delivery 状态检查
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

确认生成：

```text
D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
```

### 6. 读取 07_delivery_state_check.xlsx 验证
读取以下 sheet：
- summary
- checks
- test_token_hits
- manual_review_columns
- manual_review_issues
- duplicate_keys
- high_risk_flags

重点确认：
1. summary 中 fail_count 是否为 0
2. overall_status 是否为 PASS 或 WARN
3. test_token_hits 是否没有 ERROR 级命中
4. duplicate_keys 是否为空
5. high_risk_flags 是否为空
6. manual_review_columns 中 corrected_value 是否 exists_exact=True
7. manual_review_issues 是否还存在 corrected_row_not_ready

如果 fail_count 仍不为 0：
- 不要强行继续
- 在 worklog 中记录失败项
- 给出下一步建议

### 7. 更新 Codex Worklog
必须更新：

```text
docs/codex_worklog/LATEST.md
```

必须新增：

```text
docs/codex_worklog/history/YYYYMMDD_HHMMSS_clean_20266.md
```

日志必须包含以下结构：

```md
# Codex Worklog - Clean 20266

## task_title
清理 delivery_package 测试值 20266

## started_at
实际开始时间

## finished_at
实际结束时间

## git_commit_before
执行前 commit

## git_commit_after
提交后 commit；提交前可先写 pending，提交后补齐

## commands_run
列出实际执行命令

## files_changed
列出修改文件，至少包括：
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\06A_人工修正应用明细.xlsx
- D:\_datefac\output\delivery_package\06B_未解决问题清单.xlsx
- D:\_datefac\output\delivery_package\06C_复核模板说明.md
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_clean_20266.md

注意：output 下文件只记录路径，不加入 Git。

## outputs_generated
列出重新生成的 06/06A/06B/06C/06D/07

## checks_performed
记录：
- 是否运行 apply_manual_review_corrections.py
- 是否运行 check_delivery_state.py --json
- fail_count
- warn_count
- duplicate_keys 是否为空
- high_risk_flags 是否为空
- test_token_hits 是否无 ERROR

## result_summary
必须说明：
- 是否已清理 20266
- cleaned_20266_rows
- 是否已规范 corrected_value 列
- corrected_value_column_normalized
- apply_manual_review_corrections.py 输出摘要
- check_delivery_state.py 输出摘要

## remaining_issues
如果还有 WARN/FAIL，逐条列出；如无阻断问题，写：无阻断问题。

## next_step_suggestion
如果 fail_count=0，建议：
1. 正式人工复核 3～5 条真实指标
2. 然后追踪归母净利润小数精度问题

## safety_notes
必须包含：
- 未运行 factory_core.py
- 未触发 marker/surya/vision/PaddleOCR
- 未下载 model.safetensors
- 未修改 01_自动可信核心指标.xlsx
- 只清理 02 中人工复核测试字段
- 未提交 PDF 原文
- 未提交完整 Excel 产物
```

### 8. Git 提交
只提交 worklog 文档，不提交 output Excel。

执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "clean manual review test value 20266"
git push origin main
```

提交后补齐 LATEST.md 和 history 日志里的 git_commit_after。
如果补齐 git_commit_after 需要第二次提交，可以执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "update clean 20266 worklog commit reference"
git push origin main
```

## expected_final_state
理想结果：
- fail_count = 0
- overall_status = PASS 或 WARN
- 06 中不再存在 20266
- corrected_value 列名规范
- duplicate_keys 为空
- high_risk_flags 为空
- test_token_hits 无 ERROR
- duplicate_key_count_final = 0

## final_terminal_output
最后在终端输出摘要：
- backup_dir
- cleaned_20266_rows
- corrected_value_column_normalized: yes/no
- corrected_value_conflict_count
- apply_manual_review summary
- check_delivery_state summary
- worklog_commit_sha
- 是否可以进入下一步
