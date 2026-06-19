# 348N-DOCS-CLEANUP AI Handoff Documentation Simplification

## Goal

Reduce duplicated AI collaboration and handoff instructions across project docs.

This is a docs-only cleanup task. Do not change code, tests, input files, output files, or historical result reports.

The goal is not to delete evidence. The goal is to make active entry documents clearer and less repetitive.

---

## Current situation

The project now has multiple active guidance layers:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/codex_tasks/*.md
docs/agent/*_RESULT.md
docs/agent/*_QA*.md
docs/agent/项目进程.md
```

This is useful for AI handoff, but some current-stage text has become duplicated across `AGENTS.md`, `CURRENT_MODEL_HANDOFF.md`, and each `docs/codex_tasks/*` file.

---

## Target document roles

After cleanup, keep these roles clear:

```text
README.md = project overview and how to start
AGENTS.md = stable AI collaboration rules and permanent boundaries
.skills/ = stable workflow rules and reusable project skills
CURRENT_MODEL_HANDOFF.md = current stage, current task, short read order, next action
docs/codex_tasks/ = full task books for Codex execution
docs/agent/ = result reports, QA reports, historical evidence
docs/agent/项目进程.md = compact milestone ledger, not a full duplicate of every report
```

---

## Required context

Read:

```text
AGENTS.md
README.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
docs/agent/348N_R3_QA_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_REVIEW.md
docs/codex_tasks/348N_R3_QA_remaining_non_normalized_unknown_family_refinement_review.md
```

---

## Preflight

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## Allowed changes

Allowed docs-only changes:

```text
AGENTS.md
README.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
docs/agent/348N_DOCS_CLEANUP_AI_HANDOFF_SIMPLIFICATION_RESULT.md
```

Only modify files that actually need cleanup.

---

## Forbidden changes

Do not modify:

```text
datefac_agent/
tests/
tools/
legacy datefac/
input/
output/
temp/
bulk result reports under docs/agent/ except the new cleanup result report
old task docs under docs/codex_tasks/ except this active cleanup task if absolutely necessary
```

Do not delete historical result reports or QA reports.

Do not rewrite project history.

Do not run MinerU, OCR, LLM, or VLM.

Do not use `git add .` or `git add -A`.

---

## Cleanup rules

1. `AGENTS.md` should contain stable rules, not detailed per-task instructions.
2. `CURRENT_MODEL_HANDOFF.md` should be short and current-stage focused.
3. `.skills/` should keep reusable workflow rules, not one-off task details.
4. `docs/codex_tasks/` should remain the place for full task instructions.
5. `docs/agent/项目进程.md` should remain a compact milestone ledger.
6. Keep the current AI collaboration model clear:
   - GPT handles architecture, task design, docs, review, git advice.
   - Codex handles implementation, tests, runners, reports.
   - User handles pull, handoff to Codex, commit, push, final decision.
7. Keep the bilingual Data Result requirement, but define it once in stable guidance rather than repeating long instructions everywhere.

---

## Validation

Run:

```powershell
git diff --check
```

No pytest is required unless code or tests were accidentally changed. If code or tests are changed, stop and revert by editing back manually, not with destructive git commands.

---

## Expected report

Create:

```text
docs/agent/348N_DOCS_CLEANUP_AI_HANDOFF_SIMPLIFICATION_RESULT.md
```

Include:

```text
Task ID
Files modified
What duplication was reduced
Document role mapping after cleanup
Files intentionally not touched
Validation result
Boundary discipline
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_DOCS_CLEANUP_CONFIRMED_AI_HANDOFF_SIMPLIFIED
348N_DOCS_CLEANUP_CONFIRMED_NO_CHANGE_NEEDED
348N_DOCS_CLEANUP_BLOCKED_BY_DOC_CONFLICT
```

---

## Completion report

Report:

1. Files modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. What duplication was reduced.
5. Document role mapping after cleanup.
6. Files intentionally not touched.
7. Validation result.
8. Whether code/tests/input/output were untouched.
9. Whether historical result reports were preserved.
10. git status -sb.
11. Recommended next task.
12. Data Result / 数据结果.
