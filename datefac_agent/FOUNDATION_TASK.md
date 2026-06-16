# 348 Foundation Task: Rebuild the DateFac Agent Base

## 1. Task Name

```text
348 Foundation: DateFac Agent Base Rebuild
```

## 2. Goal

Create a clean documentation foundation for the new `datefac_agent/` mainline.

This task does not implement the full agent.

This task does not migrate large legacy code.

This task only establishes the new direction, project background, migration rules, and next-step boundaries.

## 3. Current Situation

The legacy project has useful assets but is too crowded for the new mainline:

- extraction experiments;
- MinerU outputs;
- 346B recovery logic;
- QA audit scripts;
- human review packages;
- many one-off runner scripts;
- milestone documents;
- historical outputs and local dirty files.

A clean new foundation is needed before 348A begins.

## 4. Foundation Deliverables

The first foundation deliverables are:

```text
datefac_agent/README.md
datefac_agent/PROJECT_BACKGROUND.md
datefac_agent/CODE_MIGRATION_PLAN.md
datefac_agent/FOUNDATION_TASK.md
```

These files define:

- what DateFac Agent is;
- what the old project achieved;
- why the pivot is happening;
- what code should be migrated;
- what code should not be migrated;
- what the next implementation stage should be.

## 5. Non-Goals

Do not do the following in this task:

- implement 348A;
- move legacy code wholesale;
- delete old code;
- clean output directories;
- rewrite the entire repository;
- replace MinerU workflows;
- create a generic chat agent;
- open production/client gates.

## 6. Immediate Local Setup Recommendation

Use a clean worktree or clean local checkout.

Recommended local command if using the existing `_datefac` repository as the source:

```powershell
cd /d D:\_datefac
git fetch origin
git worktree add -B pivot/348-agent-foundation D:\_datefac_agent origin/pivot/348-agent-foundation
cd /d D:\_datefac_agent
```

If `D:\_datefac_agent` already exists and is empty, the worktree command should be run from the old repository root.

Do not run this inside the dirty main working tree without a worktree.

## 7. What Comes After This

After the foundation documents are pulled locally and reviewed, the next implementation task should be:

```text
348A AI-Extracted Excel Intake Audit Pilot
```

348A should use an already extracted Excel file and the corresponding PDF to test the new audit-first workflow.

## 8. One-Sentence Summary

This foundation task creates a clean landing zone for DateFac Agent before any code migration or 348A implementation begins.
