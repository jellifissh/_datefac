# Skill: Project Milestone Ledger

## Purpose

Prevent DateFac tasks from being repeated across chats, Codex runs, or model handoffs.

The canonical ledger is:

```text
docs/PROJECT_MILESTONE_LEDGER.md
```

## Required Preflight For Every Numbered Task

Before starting any numbered DateFac task:

1. Read `AGENTS.md`.
2. Read `.skills/README.md`.
3. Read `.skills/git_workflow.md`.
4. Read `docs/PROJECT_MILESTONE_LEDGER.md`.
5. Read the latest relevant task doc under `docs/codex_tasks/`.
6. Check previous-stage output summary / QA JSON files when available.
7. Confirm whether the requested task is already completed.

If the task is already completed with `qa_fail_count = 0`, stop and report the existing result unless the user explicitly requested a revision or rerun.

## Revision Rule

If a completed task is revised, do not erase history.

Record both:

- the old version as `superseded`;
- the new version as the `effective` current behavior.

Example:

```text
342E old text-candidate route = superseded
342E table-first route = completed / effective_current_342E
```

## Required Ledger Update After Completion

After completing any numbered DateFac task, update `docs/PROJECT_MILESTONE_LEDGER.md` with:

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

## No-Repeat Rules

Do not repeat these completed chains unless explicitly requested:

- legacy 306N-310D demo-ready core metric pipeline;
- 320D-322I parser/router/semantic-adjudicator chain;
- 324/325 official rule governance cycles;
- 330A-330L Trust Engine and client-style preview chain;
- 340B-341A human-reviewed client preview milestone chain;
- 342A-342E current MinerU real-PDF benchmark chain.

Current effective next task after 342F:

```text
342G Table-First Extraction Review Package
```

## Special Current Boundary

342E has two histories:

- old 342E text-candidate audit: superseded;
- effective 342E table-first audit: completed.

Therefore:

- do not use the old 435 text candidate rows as the main 342F input;
- use `05_CORE_EXTRACTABLE` from the 342E table-first workbook;
- do not rerun MinerU;
- do not call VLM/LLM;
- do not redo 342D parser compare.

342F is now completed:

- do not rerun 342F unless revising extraction policy;
- do not mix `BASIC_DATA` into core financial extraction;
- do not use excluded tables for core extraction;
- next task is `342G Table-First Extraction Review Package`.

## Git Discipline

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
```

Use precise `git add <path>` only.
