# NEXT CODEX TASK

## task_title
实现 02A 人工年份修正覆盖表并接入 apply 回写

## project
D:\_datefac

## current_status
10A 策略文档已生成且无乱码。推荐采用 Option C：新增独立人工年份修正覆盖表。

当前已成功的人工回写：
- 归属母公司净利润 2026E = 288.52，manual_corrected
- 每股收益 2026E = 1.65，manual_added
- P/E 2026E = 29.97，manual_added
- EV/EBITDA 2026E = 22.76，manual_added

当前 delivery 状态：
- overall_status = PASS
- fail_count = 0
- warn_count = 0
- duplicate_key_count_final = 0

仍待解决的多年份小数精度值：
- 归属母公司净利润 2025A = 204.59 百万元
- 归属母公司净利润 2027E = 398.83 百万元
- 归属母公司净利润 2028E = 536.53 百万元

## goal
实现 Option C：新增并接入独立人工年份修正覆盖表。

目标文件：
D:\_datefac\output\delivery_package\02A_人工年份修正覆盖表.xlsx

目标代码：
- D:\_datefac\tools\apply_manual_review_corrections.py
- D:\_datefac\tools\check_delivery_state.py

实现后，apply_manual_review_corrections.py 应同时读取：
1. 01_自动可信核心指标.xlsx
2. 02_人工复核指标队列.xlsx
3. 02A_人工年份修正覆盖表.xlsx（如果存在）

并把 02A 中有效记录合并到 06_最终核心财务指标.xlsx。

## hard_constraints
1. 不要运行 factory_core.py
2. 不要触发 marker / surya / vision / PaddleOCR
3. 不要下载 model.safetensors 或任何视觉模型
4. 不要修改 01_自动可信核心指标.xlsx
5. 不要修改 02_人工复核指标队列.xlsx
6. 不要扩样本
7. 不要重新处理 PDF
8. 不要提交 output 下 Excel/PDF/截图产物到 Git
9. 允许修改 apply_manual_review_corrections.py
10. 允许修改 check_delivery_state.py
11. 允许在本地 output/delivery_package 创建或更新 02A_人工年份修正覆盖表.xlsx 用于验证，但不要加入 Git

## design_requirements

### 1. 02A 文件定位
默认路径：
D:\_datefac\output\delivery_package\02A_人工年份修正覆盖表.xlsx

如果该文件不存在：
- apply_manual_review_corrections.py 不应失败
- 可在 06D 诊断中记录 manual_year_override_file_status = missing
- 可选：生成一个空模板文件，但不要影响正常回写

### 2. 02A 字段
必须支持以下列：
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

列名需要做 strip 归一，兼容尾随空格。

### 3. 02A 有效记录规则
一条 02A 记录只有同时满足以下条件才可应用：
- asset_package 非空
- standard_metric 非空
- year 是单一年份，例如 2025A / 2026E / 2027E / 2028E
- corrected_value 非空且可数值化
- review_status 属于 corrected/accepted/修正/已修正/确认/通过 等有效状态
- use_corrected_value 属于 是/true/1/yes/使用/采用/√ 等真值

无效记录不应用到 06，但要进入 06D 诊断。

### 4. 02A 合并规则
key = asset_package + standard_metric + year

推荐优先级：
1. 02A manual_year_override
2. 02 manual correction
3. 01 trusted automatic value

如果 02A 与 02 对同一个 key 都有人工修正：
- 02A 优先
- 06A 中记录 source_priority = 02A_over_02
- 06D 中记录 conflict detail
- 不允许产生 duplicate key

### 5. 06A / 06D 诊断要求
06A_人工修正应用明细.xlsx 中应能看出 02A 记录来源，例如：
- final_value_source = manual_year_override
或
- correction_source = 02A_manual_year_override

06D_人工复核回写诊断.xlsx 中应新增或扩展诊断信息，至少包含：
- 02A 文件是否存在
- 02A 总行数
- 02A 有效行数
- 02A 无效行数
- 02A 应用行数
- 02A 重复 key 数
- 02A 与 02 冲突 key 数

### 6. check_delivery_state.py 扩展
check_delivery_state.py 应检查：
- 02A 是否存在
- 如果存在，是否可读
- 必要列是否存在
- key 是否重复
- year 是否单一年份
- corrected_value 是否可数值化
- 是否包含 TEST / 20266 / 987654.321

如果 02A 不存在，不应 FAIL；可以 INFO/SKIP。
如果 02A 存在但有无效有效写入风险，应 WARN 或 FAIL，按严重性判断。

## validation_data
创建或更新本地 02A_人工年份修正覆盖表.xlsx，写入以下 3 条已确认值：

| asset_package | standard_metric | year | corrected_value | corrected_unit | review_status | use_corrected_value | reviewer | reviewed_at | reviewer_note | evidence_crop_path | source_note |
|---|---|---|---:|---|---|---|---|---|---|---|---|
| H3_AP202605091822098939_1_资产包 | 归属母公司净利润 | 2025A | 204.59 | 百万元 | corrected | 是 | 小唐 | 2026-05-18 | 根据 page_001_table_001.png 人工复核，保留两位小数 | D:\_datefac\output\H3_AP202605091822098939_1_资产包\02B_table_region_assets\crops\page_001_table_001.png | 02A manual year override validation |
| H3_AP202605091822098939_1_资产包 | 归属母公司净利润 | 2027E | 398.83 | 百万元 | corrected | 是 | 小唐 | 2026-05-18 | 根据 page_001_table_001.png 人工复核，保留两位小数 | D:\_datefac\output\H3_AP202605091822098939_1_资产包\02B_table_region_assets\crops\page_001_table_001.png | 02A manual year override validation |
| H3_AP202605091822098939_1_资产包 | 归属母公司净利润 | 2028E | 536.53 | 百万元 | corrected | 是 | 小唐 | 2026-05-18 | 根据 page_001_table_001.png 人工复核，保留两位小数 | D:\_datefac\output\H3_AP202605091822098939_1_资产包\02B_table_region_assets\crops\page_001_table_001.png | 02A manual year override validation |

注意：不要在 02 中写这些值。

## required_steps

### 1. 同步 Git 并确认任务
执行：

```bat
cd /d D:\_datefac
git fetch origin
git pull origin main
git status --short
git log --oneline --decorate -5
```

读取 NEXT_CODEX_TASK.md，确认 task_title 是：
“实现 02A 人工年份修正覆盖表并接入 apply 回写”

如果 task_title 不匹配，停止。

### 2. 修改代码
实现：
- apply_manual_review_corrections.py 读取 02A
- 标准化 02A 字段
- 校验 02A 有效行
- 将 02A 覆盖记录合并到 final_df
- 06A/06D 输出 02A 来源与诊断
- check_delivery_state.py 增加 02A 检查

### 3. 备份本地产物
在 delivery_package 下创建：

```text
_backup_before_02A_year_override_YYYYMMDD_HHMMSS
```

备份：
- 02_人工复核指标队列.xlsx
- 02A_人工年份修正覆盖表.xlsx（如果已存在）
- 06_最终核心财务指标.xlsx
- 06A_人工修正应用明细.xlsx
- 06B_未解决问题清单.xlsx
- 06D_人工复核回写诊断.xlsx
- 07_delivery_state_check.xlsx

### 4. 创建/更新 02A 验证表
创建或更新：
D:\_datefac\output\delivery_package\02A_人工年份修正覆盖表.xlsx

写入 validation_data 中的 3 条记录。

### 5. 运行脚本
执行：

```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\apply_manual_review_corrections.py D:\_datefac\tools\check_delivery_state.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\apply_manual_review_corrections.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

### 6. 验证 06 最终表
读取 06_最终核心财务指标.xlsx，确认：
- 归属母公司净利润 2025A = 204.59，final_value_source = manual_year_override 或等价来源
- 归属母公司净利润 2026E = 288.52，仍保留 manual_corrected 或不被错误覆盖
- 归属母公司净利润 2027E = 398.83，final_value_source = manual_year_override 或等价来源
- 归属母公司净利润 2028E = 536.53，final_value_source = manual_year_override 或等价来源
- duplicate_key_count_final = 0
- fail_count = 0

### 7. 验证 06A/06D
确认：
- 06A 中有 02A 应用明细
- 06D 中有 02A 读取/有效/无效/应用/冲突诊断
- 06B 没有新增不合理阻断项

### 8. 更新 worklog
必须更新：
- docs/codex_worklog/LATEST.md

必须新增：
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_implement_02A_year_overrides.md

worklog 必须使用 UTF-8 写入，中文不能乱码。

result_summary 必须说明：
- 是否实现 02A 读取
- 是否生成/更新 02A 验证表
- 02A 有效记录数
- 02A 应用记录数
- 06 是否出现 2025A/2027E/2028E 归母净利润覆盖值
- duplicate_key_count_final
- delivery check 是否 PASS

next_step_suggestion：
- 如果成功，下一步整理 delivery_package 人工复核使用说明，准备扩样本前检查

## git_commit
允许提交：
- tools/apply_manual_review_corrections.py
- tools/check_delivery_state.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

不要提交：
- output/delivery_package/02A_人工年份修正覆盖表.xlsx
- output 下任何 Excel/PDF/截图产物

执行：

```bat
git add tools/apply_manual_review_corrections.py tools/check_delivery_state.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add manual year override support"
git push origin main
```

## expected_final_state
- 代码支持 02A 人工年份修正覆盖表
- 本地 02A 写入 3 条归母净利润多年份覆盖记录
- 06 中 2025A/2027E/2028E 精度值正确
- 2026E 既有人工修正不被破坏
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
