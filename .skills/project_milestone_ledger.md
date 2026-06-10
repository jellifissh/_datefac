# Skill: Project Milestone Ledger / 项目进程账本技能

## Purpose / 用途

中文：
这个 skill 用来防止 DateFac 的编号任务在不同聊天、不同模型、不同 Codex 线程中被重复执行，同时也规定了任务完成后必须如何更新 ledger。

English:
This skill prevents numbered DateFac work from being repeated across chats, models, and Codex runs, and defines how the milestone ledger must be maintained after each task.

The canonical ledger is / 正式账本路径:

```text
docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md
```

Compatibility pointer / 兼容指针路径:

```text
docs/PROJECT_MILESTONE_LEDGER.md
```

## Required Preflight For Every Numbered Task / 每个编号任务的前置读取

Before starting any numbered DateFac task, read:

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. the latest relevant task doc under `docs/codex_tasks/`
7. previous-stage summary / QA JSON / report files when available

If the task is already completed with `qa_fail_count = 0`, do not repeat it unless the user explicitly requested a revision or rerun.

如果任务已经 `completed` 且 `qa_fail_count = 0`，不要重复执行，除非用户明确要求 revision 或 rerun。

## Revision Rule / 修订规则

If a completed task is revised, do not erase history.

Record both:

- the old version as `superseded`
- the new version as the `effective` current behavior

Example:

```text
342E old text-candidate route = superseded
342E table-first route = completed / effective_current_342E
```

## Required Ledger Update After Completion / 完成后必须更新账本

After completing any numbered DateFac task, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- and any related `.skills/*.md` file if workflow rules changed

Minimum update fields:

```text
Task ID:
Status:
Effective version:
Input dirs/files:
Output dir:
Output workbook/report:
Key metrics:
QA result:
Decision:
Next recommended task:
Do not repeat:
Touched source files:
Validation commands:
Commit SHA, if known:
```

Failure to update the ledger after a milestone is a process bug.

完成编号任务后不更新 ledger，属于流程 bug。

## Rollup Refresh Rule / 3-5 个任务一次汇总刷新

After every 3 to 5 numbered tasks, perform a ledger rollup refresh.

That refresh must:

- merge overly scattered records
- update the current effective mainline
- update the next recommended task
- update superseded routes
- update no-repeat rules
- verify `client_ready` and `production_ready` were not accidentally changed

每完成 3 到 5 个编号任务，必须做一次 ledger rollup refresh，集中刷新主线、next task、superseded routes、no-repeat rules 和 readiness flags。

## Skills vs Docs Responsibility Split / `.skills` 与 `docs` 的职责分工

- `.skills/`: workflow rules, preflight, validation boundaries, and git discipline
- `docs/project_milestones/`: project facts, stage status, and the no-repeat source of truth
- `docs/codex_tasks/`: single numbered task specs
- `docs/project_handoffs/`: handoffs for new chats / models / contributors
- `docs/project_timelines/`: chronological project history
- `docs/demo/`: external demo material and runbooks
- `docs/architecture/`: architecture boundaries and module responsibilities

## No-Repeat Rules / 防重复规则

Do not repeat these completed chains unless explicitly requested:

- legacy `306N-310D` demo-ready core metric pipeline
- `320D-322I` parser / router / semantic adjudicator chain
- `324 / 325` official rule governance cycles
- `330A-330L` Trust Engine and client-style preview chain
- `340B-341A` human-reviewed client preview milestone chain
- `342A-342F` current MinerU real-PDF benchmark chain

Current effective next task after 342F:

```text
342G Table-First Extraction Review Package
```

## Special Current Boundary / 当前强制边界

Current forced state after 342F:

- `342E` old text-candidate route = superseded
- `342E` table-first route = effective
- `342F` = completed
- do not rerun MinerU
- do not call VLM/LLM
- do not redo `342D`
- do not use the old 435 text-candidate route as the primary input
- do not rerun `342F` unless revising extraction policy
- do not mix `BASIC_DATA` into core financial extraction
- current next task = `342G Table-First Extraction Review Package`

## Git Discipline / Git 纪律

Follow `.skills/git_workflow.md`.

Never use:

```text
git add -A
git add .
```

Never stage:

```text
output/
temp/
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
protected dirty files
tools/mineru_new_runner.cmd
```

Use precise `git add <path>` only.
