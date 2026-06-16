# 348P4 Agent Skill and AGENTS Sync

## 1. Goal

Synchronize top-level repository instructions and `.skills/` workflow files with the DateFac Agent pivot.

This task updates the AI/Codex operating instructions so future tasks do not accidentally drift back to the old 342/MinerU/table-extraction mainline.

## 2. Scope

This task is documentation-only.

Updated or added files:

```text
AGENTS.md
.skills/README.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
.skills/project_milestone_ledger.md
.skills/mineru_local_benchmark_workflow.md
docs/codex_tasks/348P4_agent_skill_and_agents_sync.md
```

## 3. Mainline Change

The current effective mainline is now documented as:

```text
348 Agent Pivot / DateFac Agent foundation / extraction audit workflow
```

The active new package is:

```text
datefac_agent/
```

The recommended worktree is:

```text
D:\_datefac_agent
```

The recommended branch is:

```text
pivot/348-agent-foundation
```

## 4. Legacy Status

The following remain valuable reference assets, but are not the immediate active mainline:

```text
340B-341B human-reviewed client preview chain
342A-342F MinerU real-PDF benchmark chain
345D full structured demo export package
346B-346B5Q quality-limited recovery / expansion / QA chain
```

`346B6` is paused as the immediate mainline.

Old raw PDF extraction is no longer treated as the primary moat.

## 5. MinerU Status

MinerU is now documented as a sidecar extractor candidate, not the 348A mainline.

Future MinerU 3.3.1 tasks must read:

```text
mineru_3.3.1.md
.skills/mineru_local_benchmark_workflow.md
```

348A-style Excel intake audit tasks must not run MinerU, OCR, LLM, or VLM.

## 6. New Skill Files

Two new skills were introduced:

```text
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
```

They define:

- the DateFac Agent pivot boundary;
- the new package structure;
- legacy freeze / capability harvest rules;
- fixture harvest posture;
- Excel intake audit workflow boundaries;
- manifest and validation expectations.

## 7. Non-Goals

This task did not:

- modify `datefac/` legacy source;
- modify 348A implementation code;
- run MinerU;
- call LLM/VLM/OCR;
- touch old `D:\_datefac` outputs;
- modify input/output/temp/data directories;
- claim client or production readiness.

## 8. Recommended Next Step

If 348A has been pushed and this documentation sync is pulled locally, the next likely task is:

```text
348A-QA Excel Intake Audit Result Review
```

That task should review the first 348A real-run outputs, especially evidence classification and narrative-vs-financial row handling.
