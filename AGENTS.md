# _datefac 项目级工作说明

## 1. 项目概览

- 项目名称：`_datefac`
- 当前主线：`DateFac Agent`
- 当前定位：金融文档 AI 抽取结果审计与可信交付系统
- 当前推荐工作区：`D:\_datefac_agent`
- 当前推荐分支：`pivot/348-agent-foundation`
- 当前 active package：`datefac_agent/`
- 当前流程：`intake -> audit -> review -> delivery`

旧 `datefac/` 包是 legacy extraction / benchmark / recovery / audit reference，不是当前新增功能的默认修改对象。

## 2. 当前状态

当前已经进入：

```text
348N-R2-QA Normalized Testset Schema Support Review
```

最近关键结果：

```text
348N-R2 implemented normalized_testset schema support
unknown_row_count dropped from 367 to 48
normalized_testset_record_row_count increased from 0 to 320
clean_data_row_count stayed 37
current task is QA/review, not code fix
```

当前事实源：

```text
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
```

当前任务文档：

```text
docs/codex_tasks/348N_R2_QA_normalized_testset_schema_support_review.md
```

## 3. 默认必读清单

新任务默认读取：

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
current task under docs/codex_tasks/
directly related result or QA report under docs/agent/
```

新模型、新聊天、新 Codex 线程还必须读取：

```text
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
```

## 4. 当前修改边界

默认允许新增或修改：

```text
datefac_agent/
tests/agent/
docs/agent/
docs/codex_tasks/
docs/project_handoffs/
relevant .skills/ workflow docs when workflow rules change
```

默认禁止，除非任务明确点名：

```text
legacy datefac/ package
old parser / extraction / benchmark code
input/ output/ temp/ data/ directories
bulk output artifacts
client_ready / production_ready / formal_client_export_allowed gates
```

## 5. 当前 gate

除非任务文档明确改变，否则这些 gate 必须保持关闭：

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

默认不做：

```text
MinerU rerun
OCR
PDF re-extraction
LLM/VLM calls
formal client delivery
```

## 6. 执行规范

- 修改前确认影响范围与不改范围。
- 修改后说明验证结果、样本范围与残余风险。
- 如果证据不足，优先补诊断，不做猜测性改规则。
- Agent audit 结论必须分层：intake 层、audit 层、review 层、delivery 层。
- Runner 输出必须写 manifest / run summary，并保留 readiness flags。
- 审计系统宁可进入 REVIEW，也不要无证据 PASS。
- Git 纪律以 `.skills/git_workflow.md` 为准。
