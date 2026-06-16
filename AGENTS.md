# _datefac 项目级工作说明

## 项目概览

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

## 当前状态

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `demo_export_only = true` unless a task explicitly says otherwise
- AI / LLM / VLM decisions are not authoritative unless a task explicitly defines a reviewed workflow
- Human review remains required before any client-facing promotion

## 当前有效主线

当前有效主线是 348 Agent pivot chain:

```text
348 Agent Pivot
348P2 Agent Foundation Cleanup
348P3 Agent Root README and Fixture Foundation
348A AI-Extracted Excel Intake Audit Pilot
```

348A 的核心边界：

```text
already extracted Excel + source PDF reference
-> intake
-> audit
-> review queue
-> delivery artifacts
```

348A 不做：

```text
PDF re-extraction
MinerU run
LLM/VLM API call
OCR
346B6 continuation
client/production delivery
```

## Codex 执行前必读

每次修改前，必须先阅读以下文档并按其约束执行：

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/datefac_agent_foundation.md`
5. `.skills/agent_excel_intake_audit_workflow.md`
6. `.skills/project_milestone_ledger.md`
7. `datefac_agent/README.md`
8. `datefac_agent/PROJECT_BACKGROUND.md`
9. `datefac_agent/CODE_MIGRATION_PLAN.md`
10. `docs/project_strategy/348_agent_pivot_brief.md`
11. `docs/agent/AGENT_ARCHITECTURE.md`
12. `docs/agent/348A_INPUT_OUTPUT_CONTRACT.md`
13. `docs/agent/FIXTURE_STRATEGY.md`
14. `docs/legacy/LEGACY_ASSET_MAP.md`
15. latest relevant task doc under `docs/codex_tasks/`

如果上述文件缺失，先停止并报告，不要自行补一套相互冲突的新规则。

## 当前修改边界与禁止事项

默认允许新增或修改：

- `datefac_agent/`
- `tests/agent/`
- `docs/agent/`
- `docs/legacy/`
- relevant `docs/codex_tasks/`
- relevant `.skills/` workflow docs when workflow rules change

默认禁止，除非任务明确点名：

- 不要修改 legacy `datefac/` 包
- 不要移动旧 parser / extraction / benchmark 代码
- 不要删除历史资产包或历史产物
- 不要清理 `input/`, `output/`, `temp/`, `data/`
- 不要提交 bulk output artifacts
- 不要继续 346B6 作为当前主线
- 不要把旧 MinerU recovery 当成当前 Agent 主线
- 不要把 `client_preview_ready` 写成 `client_ready`
- 不要把 `production_ready = false` 改成 true
- 不要把 benchmark / pilot / sidecar 输出写成 formal client delivery

## 当前重点工作流

### 1. DateFac Agent foundation / audit workflow

- `datefac_agent/intake/`: Excel / extraction artifact intake
- `datefac_agent/audit/`: unit, period, valuation, evidence and other pure audit checkers
- `datefac_agent/review/`: review queue and risk classification
- `datefac_agent/delivery/`: audit report, evidence index and clean/review outputs
- `datefac_agent/schemas/`: shared data models
- `datefac_agent/llm/`: future isolation area for model clients and prompts, not business logic

### 2. Legacy reference workflows

The following historical workflows remain useful as references and fixture sources, but they are not the active mainline:

- `340B-341B` human-reviewed client preview chain
- `342A-342F` real PDF / MinerU benchmark chain
- `345D` full structured demo export
- `346B-346B5Q` quality-limited recovery and QA chain

Do not repeat them unless the task explicitly asks for a revision, audit, or fixture harvest.

## MinerU Boundary

MinerU is now a sidecar extractor candidate, not the 348A mainline.

- Old `mineru_new` / `342C2` workflow = legacy benchmark reference.
- New MinerU 3.3.1 workflow = side-by-side / sidecar candidate. Read `mineru_3.3.1.md` before any future MinerU task.
- 348A must not run MinerU.
- 348A must not call OCR, LLM, or VLM.

## 执行规范

- 修改前必须说明影响范围与不改范围。
- 修改后必须说明验证结果、样本范围与残余风险。
- 如果证据不足，优先补诊断，不做猜测性改规则。
- Agent audit 结论必须分层：intake 层、audit 层、review 层、delivery 层。
- Runner 输出必须写 manifest / run summary，并保留 readiness flags。
- 审计系统宁可进入 REVIEW，也不要无证据 PASS。
- 对旧资产的正确处理方式是 capability harvest / fixture harvest，不是 wholesale migration。

## Git 纪律

遵守 `.skills/git_workflow.md`。

永远不要使用：

```text
git add .
git add -A
git reset --hard
git checkout --
```

只允许精确 add 本次任务明确涉及的文件。
