# NEXT CODEX TASK

## task_title
验收 02A 人工年份修正覆盖表实现并修复 worklog 乱码

## project
D:\_datefac

## current_status
上一轮 Codex 已提交代码：
- commit: 96b633a add manual year override support
- 修改文件：
  - tools/apply_manual_review_corrections.py
  - tools/check_delivery_state.py

上一轮 worklog 显示：
- 已创建/更新 02A_人工年份修正覆盖表.xlsx
- 已运行 apply_manual_review_corrections.py
- 已运行 check_delivery_state.py --json
- 06 中已验证：
  - 归属母公司净利润 2025A = 204.59
  - 归属母公司净利润 2027E = 398.83
  - 归属母公司净利润 2028E = 536.53
  - 归属母公司净利润 2026E = 288.52 仍保留
- duplicate_key_count_final = 0
- overall_status = PASS
- fail_count = 0
- warn_count = 0

但上一轮 worklog 中文再次出现乱码，因此需要重新用 UTF-8 写入一份干净验收报告和干净 worklog。

## goal
本轮只做验收和报告，不改业务数据，不再实现新功能。

目标：
1. 只读验证 02A 实现是否真实生效。
2. 生成本地验收报告：
   - D:\_datefac\output\delivery_package\11_02A_year_override_validation.md
   - D:\_datefac\output\delivery_package\11_02A_year_override_validation.xlsx
3. 更新 docs/codex_worklog/LATEST.md，确保中文不乱码。
4. 新增 docs/codex_worklog/history/YYYYMMDD_HHMMSS_validate_02A_year_overrides.md。
5. 不修改 01/02/02A/06 正式数据。
6. 不运行 factory_core.py。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要修改 02_人工复核指标队列.xlsx
6. 不要修改 02A_人工年份修正覆盖表.xlsx
7. 不要修改 06_最终核心财务指标.xlsx
8. 不要扩样本
9. 不要重新处理 PDF
10. 不要提交 output 下 Excel/Markdown/PDF/截图产物到 Git
11. 只允许提交 worklog 文档

## required_steps

### 1. 同步 Git 并确认任务
执行：

```bat
cd /d D:\_datefac
git fetch origin
git pull origin main
git status --short
git log --oneline --decorate -8
```

读取 NEXT_CODEX_TASK.md，确认 task_title 是：
“验收 02A 人工年份修正覆盖表实现并修复 worklog 乱码”

如果 task_title 不匹配，停止，不要执行旧任务。

### 2. UTF-8 写入要求
本轮所有 Markdown / worklog 必须用 Python UTF-8 写入，禁止 PowerShell 默认重定向。

建议：

```python
from pathlib import Path
Path(path).write_text(content, encoding="utf-8")
```

生成后必须读取验证：
- 不包含 `????`
- 不包含连续 `??` 作为乱码
- 不包含 `�`
- 中文段落正常显示

### 3. 运行状态检查
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

记录：
- overall_status
- pass_count
- warn_count
- fail_count
- report_path

### 4. 只读读取关键产物
读取以下文件：
- D:\_datefac\output\delivery_package\02A_人工年份修正覆盖表.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\06A_人工修正应用明细.xlsx
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx

验证以下内容：

#### 02A 验证
02A 必须存在并可读。
必须有以下 3 条：
- 归属母公司净利润 2025A = 204.59，单位百万元
- 归属母公司净利润 2027E = 398.83，单位百万元
- 归属母公司净利润 2028E = 536.53，单位百万元

字段检查：
- asset_package 非空
- standard_metric = 归属母公司净利润
- year 为单一年份
- corrected_value 可数值化
- corrected_unit 非空
- review_status 有效
- use_corrected_value 为真值

#### 06 验证
06 必须包含：
- 归属母公司净利润 2025A = 204.59，来源 manual_year_override 或等价
- 归属母公司净利润 2026E = 288.52，来源 manual_corrected 或等价
- 归属母公司净利润 2027E = 398.83，来源 manual_year_override 或等价
- 归属母公司净利润 2028E = 536.53，来源 manual_year_override 或等价

同时确认：
- duplicate_key_count_final = 0 或 07 中 duplicate_keys 为空
- test_token_hits 为空
- high_risk_flags 为空

#### 06A 验证
06A 应能看到 02A 应用明细：
- 至少 3 条 correction_source / final_value_source / source 字段能体现 manual_year_override 或 02A 来源。

#### 06D 验证
06D 应能看到 02A 诊断信息：
- 02A 文件存在
- 02A 总行数
- 02A 有效行数
- 02A 应用行数
- 02A 重复 key 数
- 02A 与 02 冲突 key 数，如有

### 5. 生成 11 验收报告
生成：
- D:\_datefac\output\delivery_package\11_02A_year_override_validation.md
- D:\_datefac\output\delivery_package\11_02A_year_override_validation.xlsx

Markdown 必须包含：

# 02A Manual Year Override Validation

## Summary
- generated_at
- overall_status
- pass_count
- warn_count
- fail_count
- validation_result: PASS / WARN / FAIL

## 02A Input Validation
列出 3 条 02A 输入记录及字段检查结果。

## 06 Final Validation
列出 2025A/2026E/2027E/2028E 归母净利润最终值、来源和是否匹配期望。

## 06A Application Detail Validation
说明 02A 应用明细是否存在。

## 06D Diagnosis Validation
说明 02A 诊断是否存在，是否有重复 key / 冲突 / 无效行。

## Risk Assessment
说明是否存在交付阻断风险。

## Decision
如果全部通过，写：
02A manual year override support is accepted for current sample.

## Next Step
建议：
- 整理 delivery_package 人工复核使用说明
- 准备扩样本前的验收清单

Excel 至少包含 sheet：
- summary
- input_02A_validation
- final_06_validation
- application_06A_validation
- diagnosis_06D_validation
- risks

### 6. 更新 worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_validate_02A_year_overrides.md

worklog 必须中文正常，不允许乱码。

result_summary 必须说明：
- 是否生成 11 验收 md/xlsx
- 02A 是否存在并有效
- 06 是否验证到 2025A/2026E/2027E/2028E
- 06A 是否有 02A 应用明细
- 06D 是否有 02A 诊断
- delivery check 是否 PASS
- 是否未修改 01/02/02A/06

next_step_suggestion：
- 如果验收通过，下一步整理 delivery_package 人工复核使用说明和扩样本前检查清单。

## git_commit
允许提交：
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package/11_02A_year_override_validation.md
- output/delivery_package/11_02A_year_override_validation.xlsx
- output 下任何 Excel/PDF/截图产物

执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "validate manual year override support"
git push origin main
```

## expected_final_state
- 本地生成 11_02A_year_override_validation.md
- 本地生成 11_02A_year_override_validation.xlsx
- delivery check PASS
- 02A 输入有效
- 06 最终表多年份归母净利润正确
- 06A/06D 有 02A 应用和诊断痕迹
- worklog 中文无乱码
- 未修改 01/02/02A/06
- 未提交 output 产物到 Git

## safety_notes
- 未运行 factory_core.py
- 未触发 marker/surya/vision/PaddleOCR
- 未下载 model.safetensors
- 未修改 01_自动可信核心指标.xlsx
- 未修改 02_人工复核指标队列.xlsx
- 未修改 02A_人工年份修正覆盖表.xlsx
- 未修改 06_最终核心财务指标.xlsx
- 未提交 PDF 原文
- 未提交完整 Excel 产物
