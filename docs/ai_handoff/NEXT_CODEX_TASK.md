# NEXT CODEX TASK

## task_title
重新生成无乱码的多年份人工修正策略文档

## project
D:\_datefac

## current_status
用户已上传并检查：
- D:\_datefac\output\delivery_package\10_manual_multi_year_correction_strategy.md
- D:\_datefac\output\delivery_package\10_manual_multi_year_correction_strategy.xlsx

该策略文档方向基本正确，但关键中文内容大面积乱码，例如：
- Current Limitation 中出现大量 `??`
- Remaining Values 中归母净利润说明乱码
- Option A/B/C 的优缺点和风险说明乱码
- Recommendation 与 Next Implementation Plan 中关键解释乱码

可用信息：
- 02 row_index=1/4/5/7 人工字段已填写
- 06 中 4 条人工修正值已验证成功
- delivery check = PASS
- fail_count = 0
- warn_count = 0
- 推荐方向仍倾向 Option C：新增独立人工年份修正覆盖表

当前不能直接实现 Option C，因为策略文档不可读。必须先重新生成干净版策略文档。

## goal
重新生成无乱码、可读、可作为下一步实现依据的策略文档：

- D:\_datefac\output\delivery_package\10A_manual_multi_year_correction_strategy_clean.md
- D:\_datefac\output\delivery_package\10A_manual_multi_year_correction_strategy_clean.xlsx

本任务只生成策略文档，不实现代码，不修改数据。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要修改 02_人工复核指标队列.xlsx
6. 不要修改 06_最终核心财务指标.xlsx
7. 不要运行 apply_manual_review_corrections.py
8. 不要重新处理 PDF
9. 不要扩样本
10. 不要提交 output 下 Excel/Markdown/PDF/截图产物到 Git
11. 本轮只读状态、生成本地 10A 文档、更新 worklog

## encoding_requirements
必须用 Python UTF-8 写入所有 Markdown 文档，禁止用 PowerShell 默认重定向写中文。

建议写法：

```python
from pathlib import Path
Path(path).write_text(content, encoding="utf-8")
```

Excel 使用 openpyxl/pandas 正常写入。

生成后必须读取文件内容验证：
- 不包含 `????`
- 不包含连续 `??` 表示乱码
- 不包含 Unicode replacement char `�`
- 中文标题和中文段落能正常读取

## input_files
只读读取：
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\06A_人工修正应用明细.xlsx
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
- D:\_datefac\output\delivery_package\10_manual_multi_year_correction_strategy.md

## confirmed_current_state
策略文档必须明确记录当前已成功回写的 4 条：

| standard_metric | year | final_value | unit/source | final_value_source |
|---|---|---:|---|---|
| 归属母公司净利润 | 2026E | 288.52 | 百万元 | manual_corrected |
| 每股收益 | 2026E | 1.65 | 元/股 | manual_added |
| P/E | 2026E | 29.97 | 倍 | manual_added |
| EV/EBITDA | 2026E | 22.76 | 倍 | manual_added |

必须记录 delivery 状态：
- overall_status = PASS
- fail_count = 0
- warn_count = 0
- duplicate_key_count_final = 0

## remaining_values
策略文档必须列出尚未应用的归母净利润多年份小数值：

| standard_metric | year | corrected_value | corrected_unit | evidence |
|---|---|---:|---|---|
| 归属母公司净利润 | 2025A | 204.59 | 百万元 | page_001_table_001.png |
| 归属母公司净利润 | 2027E | 398.83 | 百万元 | page_001_table_001.png |
| 归属母公司净利润 | 2028E | 536.53 | 百万元 | page_001_table_001.png |

## required_document_sections
10A Markdown 必须包含以下章节：

# Manual Multi-Year Correction Strategy - Clean Version

## 1. Current Status
说明当前 4 条人工修正已成功，delivery 仍 PASS。

## 2. Current Limitation
说明当前 02_人工复核指标队列.xlsx 的一行只能表达一个 year，所以同一个 row_index=1 不能同时承载 2025A/2026E/2027E/2028E。

## 3. Remaining Multi-Year Values
列出 2025A/2027E/2028E 的归母净利润待覆盖值。

## 4. Option A - Duplicate Rows in 02 Manual Queue
说明：复制 02 中同一指标候选行，拆成多条单年份复核行。

必须分析：
- 优点：改动小，沿用现有 apply 脚本的一行一年模型
- 缺点：污染 02 候选队列，人工复制容易出错，来源字段重复，后续难区分候选行与人工事实行
- 风险：重复 key、行来源混乱、人工误改 source 字段
- 对现有脚本影响：可能不需要大改，但需要保证拆行后的 key 唯一
- 是否推荐：不推荐作为长期方案，只可作为临时手工补救

## 5. Option B - Multi-Value Fields in One 02 Row
说明：在同一 02 行中新增 corrected_values_json 或 corrected_2025A/corrected_2027E 等多值列。

必须分析：
- 优点：不复制行，形式上集中
- 缺点：破坏当前一行一年假设，解析复杂，Excel 人工填写体验差
- 风险：year 歧义、JSON 格式错误、诊断复杂、apply 逻辑变重
- 对现有脚本影响：需要明显改造 year 解析和 correction application
- 是否推荐：不推荐

## 6. Option C - Separate Manual Year Overrides File
说明：新增独立人工覆盖事实表，例如：
D:\_datefac\output\delivery_package\02A_人工年份修正覆盖表.xlsx

建议字段：
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
- source_note

必须分析：
- 优点：一行一指标一年，避免多年份歧义；不污染 02 队列；适合批量人工补录；便于审计；与 final key 对齐
- 缺点：需要扩展 apply_manual_review_corrections.py 读取新表；需要新增模板/诊断/check 逻辑
- 风险：两个人工来源的优先级需要定义清楚；需要避免与 02 修正重复冲突
- 对现有脚本影响：新增读取分支、冲突检测、06A/06D 来源标记
- 是否推荐：推荐

## 7. Recommended Architecture
明确推荐 Option C。

建议分层：
- 02_人工复核指标队列.xlsx = 问题候选队列 / 人工复核入口
- 02A_人工年份修正覆盖表.xlsx = 已确认人工覆盖事实表
- apply_manual_review_corrections.py = 同时读取 02 与 02A，按 key 合并
- 06A = 记录人工修正应用明细
- 06D = 记录诊断与冲突

## 8. Merge and Priority Rules
必须定义：
1. key = asset_package + standard_metric + year
2. 如果 02A 与 02 对同一 key 都有修正：
   - 推荐 02A 优先，或标记冲突进入 06B/06D
   - 必须在文档中说明推荐优先级
3. 02A 中每行必须有单一年份 year
4. review_status 必须为 corrected/accepted 等有效状态
5. use_corrected_value 必须为 是/TRUE
6. corrected_value 必须非空且可数值化

## 9. Proposed 02A Template Example
必须给出表格示例：

| asset_package | standard_metric | year | corrected_value | corrected_unit | review_status | use_corrected_value | reviewer | reviewed_at | reviewer_note | evidence_crop_path |
|---|---|---|---:|---|---|---|---|---|---|---|
| H3_AP202605091822098939_1_资产包 | 归属母公司净利润 | 2025A | 204.59 | 百万元 | corrected | 是 | 小唐 | 2026-05-18 | 根据 page_001_table_001.png 人工复核 | D:\...\page_001_table_001.png |
| H3_AP202605091822098939_1_资产包 | 归属母公司净利润 | 2027E | 398.83 | 百万元 | corrected | 是 | 小唐 | 2026-05-18 | 根据 page_001_table_001.png 人工复核 | D:\...\page_001_table_001.png |
| H3_AP202605091822098939_1_资产包 | 归属母公司净利润 | 2028E | 536.53 | 百万元 | corrected | 是 | 小唐 | 2026-05-18 | 根据 page_001_table_001.png 人工复核 | D:\...\page_001_table_001.png |

## 10. Implementation Plan
建议后续实现步骤：
1. 新增生成 02A 模板的工具或在 apply 脚本中自动创建空模板
2. 扩展 apply_manual_review_corrections.py 读取 02A
3. 标准化 02A 列名与布尔/状态字段
4. 按 asset_package + standard_metric + year 形成 override records
5. 与 01 trusted + 02 corrections 合并
6. 06A 增加 source = manual_year_override
7. 06D 增加 02A 读取诊断、重复 key、冲突明细
8. check_delivery_state.py 增加 02A 检查项
9. 用 2025A/2027E/2028E 归母净利润进行验收

## 11. Decision
明确写：
建议进入 Option C 实现阶段，但实现前应先让用户确认是否接受新增 02A 人工年份修正覆盖表。

## output_xlsx_requirements
10A Excel 至少包含这些 sheet：
- summary
- current_status
- remaining_values
- options_comparison
- proposed_02A_template
- implementation_plan

## validation_steps
生成后验证：
1. 读取 10A Markdown，确认没有 `????`、连续 `??`、`�`
2. 读取 10A Excel，确认 sheet 存在
3. 运行 check_delivery_state.py --json，确认仍 PASS
4. 确认 01/02/06 未被修改

## update_worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_regenerate_clean_multi_year_strategy.md

worklog 必须使用 UTF-8 写入，中文不能乱码。

result_summary 必须说明：
- 是否生成 10A md/xlsx
- 是否无乱码
- 推荐方案是否为 Option C
- delivery check 是否仍 PASS
- 是否未修改 01/02/06

next_step_suggestion：
- 用户确认后，下一步实现 Option C：新增 02A 人工年份修正覆盖表并接入 apply 脚本

## git_commit
允许提交：
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package/10A_manual_multi_year_correction_strategy_clean.md
- output/delivery_package/10A_manual_multi_year_correction_strategy_clean.xlsx
- output 下任何 Excel/PDF/截图产物

执行：

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "regenerate clean multi-year correction strategy"
git push origin main
```

## expected_final_state
- 本地生成 10A clean strategy md/xlsx
- 10A 无乱码
- delivery check 仍 PASS
- 推荐 Option C
- 未修改 01/02/06
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
