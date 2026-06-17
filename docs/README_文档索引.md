# DateFac 文档索引 / DateFac Docs Index

这是 DateFac 的文档入口索引。新的聊天、新模型、新 Codex 线程或新协作者，不应从旧里程碑或历史输出里猜当前状态。

## 当前主线

```text
DateFac Agent
金融文档 AI 抽取结果审计与可信交付系统
```

当前工作区与分支：

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

当前有效流程：

```text
intake -> audit -> review -> delivery
```

## 新模型 / 新线程首读顺序

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/datefac_agent_foundation.md`
5. `.skills/agent_excel_intake_audit_workflow.md`
6. `docs/agent/项目进程.md`
7. `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
8. relevant `docs/codex_tasks/*.md`
9. directly related result / QA report under `docs/agent/`

## 当前任务入口

当前任务：

```text
348S-QA Third Workbook Pilot Review
```

任务文档：

```text
docs/codex_tasks/348S_QA_third_workbook_pilot_review.md
```

交接入口：

```text
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
```

## 目录说明

- `docs/agent/`: 当前 DateFac Agent 主线事实、结果与 QA 报告
- `docs/codex_tasks/`: 当前任务说明书
- `docs/project_handoffs/`: 新模型、新聊天、新线程的交接入口
- `.skills/`: 稳定规则、边界和工作流说明
- `datefac_agent/`: 当前 active package
- `tests/agent/`: 当前 agent 相关测试与 fixtures
- `docs/project_milestones/`: 历史账本，默认不再作为当前主线事实源
- `datefac/`: legacy reference，默认不作为当前新功能修改对象

## 当前阶段提醒

- R3B 已修复第三 workbook 的 zero-row intake blocker
- 第三 workbook 当前有 `row_count_total = 158`
- 当前要做的是 QA/review，不是继续改源码
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- 默认不跑 MinerU / OCR / LLM / VLM
- 默认不提交 output 文件

## 使用原则

- 新任务先读当前交接入口和任务文档。
- 不要从旧 `docs/project_milestones/` 或旧 MinerU 任务恢复当前状态。
- 任务完成后更新 `docs/agent/项目进程.md`。
- 输出文件是审查证据，默认不提交。
- Git 只允许精确 add 本次任务文件。
