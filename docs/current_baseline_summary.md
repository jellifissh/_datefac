# _datefac 当前阶段 Baseline 总结

## 1. 项目当前定位
_datefac 当前定位为：面向券商研报 PDF 的本地结构化与评估系统。  
核心目标是形成“可追溯、可复核、可回归”的资产包与评估闭环，而不是单点追求命中率。

## 2. 当前主链路
当前主链路可概括为：

`PDF -> 02A -> 02 -> 05 -> 19 -> 08/23 -> 22 -> 24`

- `02A`：原始表格资产层（抽取证据层）
- `02`：结构化表层（后处理结果）
- `05`：8项核心财务指标标准化
- `19`：指标值可信度校验
- `08/23`：回归与baseline评估（含分层）
- `22`：人工复核队列
- `24`：报告类型识别（目标/非目标口径）

## 3. 核心产物说明
- `02A_研报原始表格资产.xlsx`：抽取层证据，判断是否“抽到了表”。
- `02_研报全量结构化数据.xlsx`：后处理后的可消费结构化表。
- `05_核心财务指标标准化.xlsx`：8项核心指标候选与宽表结果。
- `19_financial_value_validation_report.xlsx`：值有效/可疑/无效判定。
- `08_批量回归报告.xlsx`：资产级回归统计（含可用性tier与scope）。
- `23_baseline_evaluation_report.xlsx`：阶段基线汇总（全量 vs in-scope）。
- `22_manual_review_queue.xlsx`：人工复核优先级与定位线索。
- `24_report_type_diagnostics.xlsx`：报告类型与是否纳入8项评估口径。

## 4. 当前10份样本评估结果
说明：系统当前 `output` 中有历史资产包；“10份样本”指本批 `input` 中的10个 PDF。

### 4.1 全量口径（当前08/23）
- `A/B/C/D/E = 1 / 3 / 0 / 5 / 1`
- `total_label_hit_metrics = 41`
- `total_value_valid_metrics = 20`
- `overall_value_valid_ratio = 0.25`

### 4.2 目标报告口径（in-scope 8项评估）
- `total_assets_in_scope = 8`
- `A/B/C/D/E(in_scope) = 1 / 3 / 0 / 3 / 1`
- `in_scope_total_label_hit_metrics = 41`
- `in_scope_total_value_valid_metrics = 20`
- `in_scope_overall_value_valid_ratio = 0.3125`

### 4.3 非目标样本识别
当前已明确识别至少两类非目标样本，并从主评估口径中区分：
- `H3_AP202605141822320809_1`：`industry_research / non_target`
- `H3_AP202605141822322093_1`：`wealth_management_weekly / non_target`

### 4.4 label_hit 与 value_valid 的区别
- `label_hit`：表示“标签匹配命中”，不等价于“值可用”。
- `value_valid`：表示“值通过可信度校验”，更接近可下游使用质量。
- 当前阶段关键事实：`value_valid_ratio` 明显低于标签命中表现，说明主要瓶颈在值绑定与结构对齐，而非纯别名命中。

## 5. 当前有效能力
- 可识别并区分非目标报告类型（`24`）。
- 可在 `05` 层拦截明显 invalid 值，避免污染宽表。
- 可生成人工复核队列并按优先级排序（`22`）。
- 可输出阶段 baseline，并支持全量口径与in-scope口径对比（`23`）。

## 6. 当前主要瓶颈
- `D_insufficient` 样本仍较多，且失败类型不单一。
- 列绑定（column binding）问题仍存在，导致“命中但值无效”。
- 个别样本存在抽取覆盖不足（extraction coverage gap）。
- hard sample 仍需专门策略，不宜在主链路强行硬修。

## 7. 下一阶段建议
1. 优先审计 `H3_AP202605141822318031_1`（抽取覆盖/质量问题最明确）。
2. 建立人工复核闭环：用 `22` 驱动修复优先级与回填验证。
3. 在不破坏主链路稳定性的前提下，再扩样本到30份进行泛化验证。

## 8. 风险与能力边界
当前系统已经具备较完整诊断与分层能力，但不应夸大自动化可用性。  
尤其在值层，`value_valid_ratio` 仍偏低，说明“可自动命中”与“可直接用于分析”之间仍有明显差距。  
下一阶段应继续坚持“证据先行、口径分层、低风险迭代”。

