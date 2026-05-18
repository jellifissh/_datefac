# NEXT CODEX TASK

## task_title
修复 worklog 编码规范并设计多年份人工修正策略

## project
D:\_datefac

## current_status
上一轮已经成功将首批 4 条人工复核值写入 02 并回写到 06。

已确认结果：
- corrected_value_non_empty_rows = 4
- effective_correction_rows = 4
- applied_override_count = 1
- applied_new_manual_count = 3
- duplicate_key_count_final = 0
- check_delivery_state.py --json: PASS
- overall_status = PASS
- pass_count = 12
- warn_count = 0
- fail_count = 0

06 中已验证到：
- 归属母公司净利润 2026E = 288.52，manual_corrected
- 每股收益 2026E = 1.65，manual_added
- P/E 2026E = 29.97，manual_added
- EV/EBITDA 2026E = 22.76，manual_added

剩余核心问题：
1. Codex 写入 docs/codex_worklog/LATEST.md 时中文出现乱码，需要修复后续日志编码规范。
2. 归属母公司净利润仍有多年份小数精度问题：
   - 2025A = 204.59
   - 2027E = 398.83
   - 2028E = 536.53
3. 当前 02_人工复核指标队列.xlsx 中同一行只能填写一个 year，因此不能在同一个 row_index=1 上同时填写 2025A/2026E/2027E/2028E。
4. 需要先设计“同一指标多年份人工修正策略”，不要直接乱改 02 或主流程。

## confirmed_values_from_user_crop
用户已确认 page_001_table_001.png 中“盈利预测和财务指标”表：

| standard_metric | unit | 2025A | 2026E | 2027E | 2028E |
|---|---|---:|---:|---:|---:|
| 归属母公司净利润 | 百万元 | 204.59 | 288.52 | 398.83 | 536.53 |
| 每股收益 | 元/股 | 1.17 | 1.65 | 2.28 | 3.06 |
| P/E | 倍 | 42.27 | 29.97 | 21.68 | 16.12 |
| P/B | 倍 | 4.23 | 3.76 | 3.26 | 2.76 |
| EV/EBITDA | 倍 | 40.31 | 22.76 | 16.08 | 11.46 |

## goals
本任务先做分析和方案，不直接应用多年份修正。

目标：
1. 修复/规范 Codex worklog 写入方式，确保后续中文不乱码。
2. 检查当前 02/06/06A/06D 状态，确认上一轮 4 条人工回写真实成功。
3. 生成多年份人工修正策略文档。
4. 评估至少 3 种方案：
   - A. 在 02 中复制同一指标行，拆成多条单年份复核行
   - B. 扩展 apply_manual_review_corrections.py 支持一个 02 行中多年份 corrected_values
   - C. 新增独立 02A_manual_year_overrides.xlsx 或 02B_manual_year_overrides.xlsx 专门承载多年份人工修正
5. 推荐最稳妥方案，并说明为什么。
6. 不修改 02/06 正式数据。
7. 不修改 apply_manual_review_corrections.py 主逻辑，除非只是修复 worklog 写法示例或文档，不要引入新回写能力。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要修改 02_人工复核指标队列.xlsx
6. 不要修改 06_最终核心财务指标.xlsx
7. 不要扩样本
8. 不要重新处理 PDF
9. 不要提交 output 下 Excel/PDF/截图产物到 Git
10. 本轮不要实现多年份回写，只做策略分析和状态确认

## required_steps

### 1. 同步 Git
执行：

```bat
cd /d D:\_datefac
git fetch origin
git pull origin main
git status --short
git log --oneline --decorate -5
```

读取 NEXT_CODEX_TASK.md 后，先确认 task_title 是：
“修复 worklog 编码规范并设计多年份人工修正策略”

如果不是，停止，不要执行旧任务。

### 2. 修复后续 worklog 编码写法
后续写入 docs/codex_worklog/LATEST.md 和 history 时，必须使用 Python UTF-8 写入，不要用 PowerShell 默认重定向。

建议使用：

```python
from pathlib import Path
Path(path).write_text(content, encoding="utf-8")
```

要求：
- 本次 LATEST.md 不得出现 ????? 乱码
- 中文必须正常显示
- 文件可以是 UTF-8 或 UTF-8 with BOM，但优先 UTF-8

### 3. 检查上一轮人工回写状态
读取：
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\06A_人工修正应用明细.xlsx
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx

确认：
- 02 row_index=1/4/5/7 的人工字段已填写
- 06 中存在 4 条人工修正结果
- duplicate_key_count_final=0
- check_delivery_state.py --json 仍 PASS

### 4. 生成策略文档
在本地生成：

```text
D:\_datefac\output\delivery_package\10_manual_multi_year_correction_strategy.md
D:\_datefac\output\delivery_package\10_manual_multi_year_correction_strategy.xlsx
```

不要加入 Git。

文档必须包含：

## Current Limitation
说明当前 02 单行只能表达一个 year，因此无法在同一 row_index=1 上同时修正 2025A/2026E/2027E/2028E。

## Remaining Values
列出尚未应用的归母净利润多年份值：
- 2025A = 204.59 百万元
- 2027E = 398.83 百万元
- 2028E = 536.53 百万元

## Option A: Duplicate Manual Queue Rows
说明如何复制 02 中 row_index=1 的来源字段，拆成多条人工复核行，每行一个 year。

分析：
- 优点
- 缺点
- 风险
- 对现有 apply_manual_review_corrections.py 的影响
- 是否推荐

## Option B: Multi-value Columns in Same Row
例如 corrected_values_json 或 corrected_2025A/corrected_2027E/corrected_2028E。

分析：
- 优点
- 缺点
- 风险
- 对现有脚本影响
- 是否推荐

## Option C: Separate Manual Year Overrides File
新增独立文件承载人工多年份修正，例如：
D:\_datefac\output\delivery_package\02A_人工年份修正覆盖表.xlsx

字段建议：
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

分析：
- 优点
- 缺点
- 风险
- 对现有脚本影响
- 是否推荐

## Recommendation
给出推荐方案。

倾向：推荐 Option C，理由是：
- 不污染原 02 队列结构
- 一行一指标一年，天然避免多年份歧义
- 适合后续批量人工补录
- 对 apply_manual_review_corrections.py 可通过新增读取分支接入
- 保留 02 作为候选队列，02A 作为人工覆盖事实表，更符合数据工程分层

## Next Implementation Plan
如果推荐 Option C，给出后续实现计划：
1. 创建 02A_人工年份修正覆盖表.xlsx 模板生成工具或由 apply 脚本自动识别
2. 扩展 apply_manual_review_corrections.py 读取该表
3. 合并进 final_df 时使用同一 key：asset_package + standard_metric + year
4. 生成 06A 明细和 06D 诊断
5. check_delivery_state.py 增加对 02A overrides 的检查

### 5. 更新 worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_multi_year_strategy.md

本次 worklog 必须中文正常，不允许乱码。

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
- 上一轮 4 条人工修正是否仍有效
- delivery check 是否 PASS
- 是否生成 10 strategy md/xlsx
- 推荐方案是什么
- 为什么不直接改 02 或 06

next_step_suggestion：
- 若用户确认，下一步实现 Option C：人工年份修正覆盖表 02A 与 apply 脚本接入

## git_commit
允许提交：
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package/10_manual_multi_year_correction_strategy.md
- output/delivery_package/10_manual_multi_year_correction_strategy.xlsx
- output 下任何 Excel/PDF/截图产物

执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "plan multi-year manual correction strategy"
git push origin main
```

## expected_final_state
- delivery check 仍 PASS
- worklog 中文不乱码
- 本地生成 10_manual_multi_year_correction_strategy.md
- 本地生成 10_manual_multi_year_correction_strategy.xlsx
- 没有修改 01/02/06 正式数据
- 没有提交 output 产物到 Git

## safety_notes
- 未运行 factory_core.py
- 未触发 marker/surya/vision/PaddleOCR
- 未下载 model.safetensors
- 未修改 01_自动可信核心指标.xlsx
- 未修改 02_人工复核指标队列.xlsx
- 未修改 06_最终核心财务指标.xlsx
- 未提交 PDF 原文
- 未提交完整 Excel 产物
