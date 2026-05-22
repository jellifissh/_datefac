# 项目阶段总结（Stage 1 ~ Stage 4）

## 背景
本项目的目标不是“手工修几格 Excel”，而是建立可追溯、可重建、可审计的数据修复治理链路。  
Stage 1 到 Stage 4 的重点是把修复动作从临时补丁，升级为可复现的工程流程。

![数据工厂 Pipeline 架构图](docs/assets/data_factory_pipeline_architecture_stage1_4.png)

## 阶段总览表
| Stage | 目标 | 输入 | 输出 | 是否修改生产数据 | 关键结果 | 状态 |
|---|---|---|---|---|---|---|
| Stage 1 | 安全应用 AI extract-positive 修复候选 | Stage1 候选包、生产 06 | 生产 06 更新、apply/diff 报告、closure | 是（仅 06） | 06: 62 -> 75 | PASS |
| Stage 2 | 建立可重建、可追溯的 override 输入层 | Stage1 已应用结果、回溯证据 | `data/overrides/02B_ai_repair_override.xlsx`、rebuild policy | 否 | 建立 official 02B，证明 override-first rebuild 可行 | PASS |
| Stage 3 | 处理 override-first backlog（final metric） | Stage3 draft/mapping/dry-run/approval 输入 | 02B: 13 -> 17，06: 75 -> 79，Stage3 closure | 是（06，按官方重建结果更新） | 新增 4 条 `FINAL_METRIC_OVERRIDE_ONLY`，原 75 行保持一致 | PASS |
| Stage 4 | 修复 structured-layer scope rule 命中问题 | Stage4 inventory/classification/draft/validation 输入 | 正式 scope rule 修复与验证、Stage4 closure | 否 | 15 条 scope fix 正式晋升并验证命中，下游 dry-run 无冲突 | PASS |

## Stage 1 详细说明
- 目标：在严格门禁下应用 AI extract-positive safe candidates。
- 核心机制：allowlist gate、merge simulation、dry-run apply、backup/hash guard。
- 结果：生产 `06_最终核心财务指标.xlsx` 行数从 62 增至 75。
- 边界：不重跑全流程，不改上游结构化层。

## Stage 2 详细说明
- 目标：让 Stage 1 修复具备可重建性与来源可追溯性。
- 核心机制：将修复沉淀为官方 override 输入层（02B），并建立 rebuild equivalence policy。
- 结果：`data/overrides/02B_ai_repair_override.xlsx` 建立完成，`06` 可由 override-first 流程重建。
- 价值：从“结果表修补”升级为“可审计输入驱动”。

## Stage 3 详细说明
- 目标：处理 Stage 1 backlog 中适合 final metric override 的候选。
- 关键链路：draft -> structured mapping -> dry-run rebuild -> approval -> promotion -> official rebuild dry-run -> production update -> closure。
- 结果：
  - official 02B：13 -> 17
  - production 06：75 -> 79
  - 新增 4 条 `FINAL_METRIC_OVERRIDE_ONLY`
- 验证：原 75 行 key/value/unit 保留；duplicate/conflict 为 0；delivery PASS。
- 说明：本阶段没有修复完整结构化表（02/05），而是完成 final metric override 闭环。

## Stage 4 详细说明
- 目标：修复“已有 mapping rule 未命中”的结构化链路问题。
- 发现：大量 gap 不是缺规则，而是 normalization/scope mismatch。
- 关键进展：
  - Stage 4E 生成 fix draft（scope 15，normalization 2）
  - Stage 4F dry-run 证明 15 条 scope fix 有效
  - Stage 4G 全部批准晋升
  - Stage 4H 晋升到 `data/mapping/formal_scope_rules.json`
  - Stage 4I 验证 15 条正式 scope rule 全命中
  - Stage 4J downstream dry-run 验证无 05/01/06/02B 冲突
- 结果：
  - `promoted_scope_fix_count=15`
  - `matched_formal_scope_rule_count=15`
  - `conflict_with_05/01/06/02B_count=0`
  - `duplicate_after_dry_run_count=0`
- 说明：Stage 4 没有直接更新生产 05/01/06，只修复正式 scope rules。

## 当前系统架构总结
- 修复不直接写结果层，优先写“可重建输入层/规则层”。
- 流程固定为：
  1. 发现问题（inventory/classification）
  2. 生成草案（draft）
  3. 沙箱验证（dry-run）
  4. 审批晋升（approval/promotion）
  5. 收口验证（post verification + closure）
- 这让修复具备：可追溯、可复现、可回滚、可审计。

## 数据安全与回滚设计
- backup + hash guard：关键动作前后均做校验。
- dry-run 先行：先证明不会冲突/重复，再决定是否晋升。
- approval package：避免未审核规则/修复直接进入正式层。
- closure 校验：每阶段都通过 summary + delivery check 做收口。
- `output/*` 不入库：运行产物不污染代码与规则主干。

## 本轮没有做什么
- 没有重新 OCR / marker 抽取。
- 没有运行 `factory_core.py`。
- 没有继续更新生产 `05 / 01 / 06`。
- 没有修改 official `02B`（Stage 4 期间）。
- 没有把 `output/*` 入库。

## 项目展示话术（评审/简历）
- 这不是“调一个 AI API”，而是完整的数据治理工程。
- 修复动作可重建，不依赖人工记忆或一次性表格修改。
- 规则、输入、结果三层分离，便于审计和回滚。
- 能区分 final metric override 修复与 structured-layer 规则修复。
- 每次变更都经过 dry-run、approval、verification 的闭环控制。
- 冲突、重复、覆盖风险有明确量化校验，不靠主观判断。
- 结果可直接支撑后续报告生成与自动化扩展。

## 现阶段结论
Stage 1~4 已完成并封账，当前系统处于“可维护、可追溯、可重建”的稳定状态。  
建议在后续阶段继续处理 normalization/overlap/derived/package-specific 等未闭合项，而不是直接改生产结果表。
