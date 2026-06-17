# _datefac 项目级工作说明

## 1. 项目概览

- 项目名称：`_datefac`
- 当前主线：`DateFac Agent`，即金融文档 AI 抽取结果审计与可信交付工作流。
- 当前新主线目录：`datefac_agent/`
- 当前推荐工作区：`D:\_datefac_agent`
- 当前推荐分支：`pivot/348-agent-foundation`
- 旧 `datefac/` 包定位：legacy extraction / benchmark / recovery / audit reference，不是当前新增功能的默认修改对象。

当前项目已经从：

```text
金融 PDF 表格抽取 / 结构化 benchmark / demo 系统
```

转向：

```text
接收 LLM、MinerU、Excel 或其他工具抽取出的金融数据，审计其正确性、完整性、证据链和交付风险。
```

当前核心工作流：

```text
intake -> audit -> review -> delivery
```

## 2. 当前状态

除非任务文档明确改变，否则这些 gate 必须保持关闭：

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

AI / LLM / VLM 判断不具备权威性，除非任务明确要求并定义人工复核流程。

## 3. 当前有效主线

当前有效主线是 `348 Agent Pivot / DateFac Agent foundation / extraction audit workflow`。

当前阶段已经进入：

```text
348A AI-Extracted Excel Intake Audit Pilot
348A-R1/R2/R3/R4 refinements
348S Second Real Workbook Pilot
348S-R1 Intake Schema Generalization
348S-R2 Unit/Period Residual Refinement
```

当前项目进程事实源：

```text
docs/agent/项目进程.md
```

旧 `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` 已降级为 historical archive，不再作为默认必读事实源。

## 4. Codex 默认必读清单

每次新任务默认只读这些文件，避免把旧历史文档全塞进上下文：

```text
AGENTS.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
当前任务对应 docs/codex_tasks/*.md
上一阶段相关 result / QA report
```

如果上述文件缺失，先停止并报告，不要自行补一套相互冲突的新规则。

## 5. 按需读取清单

只有任务明确触及对应领域时才读这些文档：

### 方向 / 背景 / 迁移类

```text
datefac_agent/README.md
datefac_agent/PROJECT_BACKGROUND.md
datefac_agent/CODE_MIGRATION_PLAN.md
docs/project_strategy/348_agent_pivot_brief.md
docs/agent/AGENT_ARCHITECTURE.md
```

适用场景：新聊天交接、架构调整、迁移能力、解释项目方向。

### 合约 / fixture / legacy 类

```text
docs/agent/348A_INPUT_OUTPUT_CONTRACT.md
docs/agent/FIXTURE_STRATEGY.md
docs/legacy/LEGACY_ASSET_MAP.md
```

适用场景：输出契约变更、fixture harvest、legacy 能力盘点、旧代码检查。

### MinerU / extraction 类

```text
mineru_3.3.1.md
.skills/mineru_local_benchmark_workflow.md
.skills/real_pdf_benchmark_workflow.md
.skills/table_extraction.md
```

适用场景：任务明确要求 MinerU、PDF extraction、sidecar extractor、legacy benchmark。

## 6. 当前修改边界

默认允许新增或修改：

```text
datefac_agent/
tests/agent/
docs/agent/
docs/codex_tasks/
relevant .skills/ workflow docs when workflow rules change
```

默认禁止，除非任务明确点名：

```text
legacy datefac/ 包
旧 parser / extraction / benchmark 代码
input/ output/ temp/ data/ 目录
bulk output artifacts
346B6 作为当前主线
旧 MinerU recovery 作为当前 Agent 主线
client_ready / production_ready / formal_client_export_allowed gate
```

## 7. Legacy reference workflows

以下历史路线仍可作为参考和 fixture source，但不是当前主线：

```text
340B-341B human-reviewed client preview chain
342A-342F real PDF / MinerU benchmark chain
345D full structured demo export
346B-346B5Q quality-limited recovery and QA chain
```

不要重复这些路线，除非任务明确要求 revision、audit、fixture harvest 或 one-file inspection。

## 8. MinerU Boundary

MinerU 是 sidecar extractor candidate，不是 348A/348S 主线。

```text
348A / 348S 默认不跑 MinerU
默认不调用 OCR
默认不调用 LLM / VLM
默认不重新抽 PDF
```

只有任务明确写明 MinerU / OCR / LLM/VLM 才能突破这个边界。

## 9. 执行规范

- 修改前必须说明影响范围与不改范围。
- 修改后必须说明验证结果、样本范围与残余风险。
- 如果证据不足，优先补诊断，不做猜测性改规则。
- Agent audit 结论必须分层：intake 层、audit 层、review 层、delivery 层。
- Runner 输出必须写 manifest / run summary，并保留 readiness flags。
- 审计系统宁可进入 REVIEW，也不要无证据 PASS。
- 对旧资产的正确处理方式是 capability harvest / fixture harvest，不是 wholesale migration。

## 10. Git 纪律

遵守 `.skills/git_workflow.md`。

永远不要使用：

```text
git add .
git add -A
git reset --hard
git checkout --
```

只允许精确 add 本次任务明确涉及的文件。