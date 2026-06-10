# DateFac 文档索引 / DateFac Docs Index

中文：
这是 DateFac 的文档入口索引。新的聊天、新模型和新的 Codex 线程，不应从零开始猜项目状态，而应先看项目账本，再看任务文档，再看对应的 demo、architecture 或 handoff。

English:
This is the high-level entry index for DateFac documentation. New chats, models, and Codex runs should not guess the project state from scratch; they should start with the project ledger, then read the task spec, then the relevant demo, architecture, or handoff docs.

## 首读顺序 / Recommended Read Order

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/project_milestone_ledger.md`
4. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
5. relevant `docs/codex_tasks/*.md`

## 目录说明 / Folder Responsibilities

- `docs/project_milestones/`: canonical project milestone ledger and stage truth
- `docs/project_timelines/`: chronological rollups and historical timeline summaries
- `docs/project_handoffs/`: handoff packets for new chats, models, or contributors
- `docs/codex_tasks/`: numbered task specs
- `docs/demo/`: demo runbooks, client-preview narratives, operator guides
- `docs/architecture/`: architecture boundaries, module design, migration notes
- `docs/assets/`: artifact-layer and evidence-layer explanations
- `docs/ai_handoff/`: prior handoff notes retained as historical references
- `docs/codex_worklog/`: Codex worklog-style records when present

## 当前正式账本 / Canonical Ledger

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Compatibility pointer / 兼容旧路径:

- `docs/PROJECT_MILESTONE_LEDGER.md`

## 当前阶段提醒 / Current State Reminder

- effective mainline = MinerU-first / table-first
- `342E` old text-candidate route = superseded
- `342E` table-first route = effective
- `342F` = completed
- current next task = `342G Table-First Extraction Review Package`
- `client_ready = false`
- `production_ready = false`

## 使用原则 / Usage Rules

- 新任务先看 ledger，不要从零开始重建项目脉络。
- 任务如果已经 `completed` 且 `qa_fail_count = 0`，不要重复执行。
- 完成编号任务后，立即更新 ledger。
- 每 3 到 5 个编号任务，做一次 ledger rollup refresh。
