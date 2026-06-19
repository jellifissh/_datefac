## Task ID

`348N-DOCS-CLEANUP AI Handoff Documentation Simplification`

## Files modified

- `AGENTS.md`
- `.skills/README.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/agent/项目进程.md`

All changes are docs-only. No code, tests, tools, input, output, temp, or legacy `datefac/` files were touched.

## What duplication was reduced

1. **R3-QA result numbers removed from `AGENTS.md` §2.**
   `AGENTS.md` previously duplicated the current stage name and the R3-QA metric block (`unknown_row_count`, `clean_data_row_count`, `review_queue_row_count`, `pytest`). These already live in `CURRENT_MODEL_HANDOFF.md` and `项目进程.md`. §2 now points to those two fact sources without re-printing the numbers, so the metrics no longer have to be edited in three places each task.

2. **Read order single-sourced.**
   `AGENTS.md` §3 and `.skills/README.md` both listed the default read order verbatim. §3 now states the full read order lives in `.skills/README.md` (single source) and keeps only the minimal must-read list. `.skills/README.md` now explicitly declares itself the single source so future edits happen in one place.

3. **Git rules de-duplicated.**
   `.skills/datefac_agent_foundation.md` had a `Git Rule` block re-listing `git add .` / `git add -A` / `git reset --hard` / `git checkout --` that already appears in `.skills/git_workflow.md` (Hard Staging Rules + Risk Rules). The foundation skill now references `git_workflow.md` for the full rule set and keeps only a 3-line invariant summary.

4. **Readiness gates de-duplicated.**
   The closed-default gates (`client_ready` / `production_ready` / `formal_client_export_allowed` / `demo_export_only`) were stated in three places: `AGENTS.md` §5, `.skills/datefac_agent_foundation.md` (Default Safety Flags), and `.skills/agent_excel_intake_audit_workflow.md` (Manifest Discipline). `AGENTS.md` §5 now keeps the stable 4-flag summary but points to the foundation skill for the full definition; the audit-workflow skill's Manifest Discipline keeps the manifest field list (its own concern) and points to the foundation skill for the gate defaults instead of redefining them.

5. **Stale current-task pointer fixed in `项目进程.md`.**
   The "当前任务" section still pointed at `348S-R3C-QA` (a completed earlier milestone) while the project is on the `348N` mainline. It was updated to the current `348N-DOCS-CLEANUP` task with a compact `348N-R1/R2/R3` milestone summary. All historical milestones (第一/第二/第三 workbook, 348S-R3C, fixture harvest) were preserved unchanged — only the current-task pointer and a 348N summary block were refreshed.

## Document role mapping after cleanup

```text
README.md                     = project overview and how to start (legacy 341A-era intro, not an AI-collaboration doc; left intact)
AGENTS.md                     = stable AI collaboration rules and permanent boundaries (no per-task numbers)
.skills/                      = stable reusable workflow rules and project skills (single source for read order, git rules, safety flags, audit workflow)
CURRENT_MODEL_HANDOFF.md      = current stage, current task, short read order, next action (already short; left intact)
docs/codex_tasks/             = full task books for Codex execution (not edited this task)
docs/agent/*_RESULT.md / *_QA*.md = result reports and QA reports, historical evidence (not deleted or rewritten)
docs/agent/项目进程.md          = compact milestone ledger + current-task pointer (history preserved, pointer refreshed)
```

## Files intentionally not touched

- `README.md` — its role is already "project overview for external readers"; it carries legacy 341A history that the task forbids rewriting, and it does not duplicate AI-collaboration instructions.
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md` — already short and current-stage focused; no duplication to reduce.
- `.skills/git_workflow.md` — the canonical git rule source; referenced by others, not modified.
- All `docs/agent/*_RESULT.md` and `docs/agent/*_QA*.md` reports — historical evidence, preserved.
- All `docs/codex_tasks/*.md` task books — out of scope for this cleanup.
- All code: `datefac_agent/`, `tests/`, `tools/`, `input/`, `output/`, `temp/`, legacy `datefac/`.

## Validation result

- `git pull --ff-only origin pivot/348-agent-foundation` -> `Already up to date`
- `git status -sb` before editing -> clean (`## pivot/348-agent-foundation...origin/pivot/348-agent-foundation`)
- `git diff --check` -> no output (no whitespace errors, no conflict markers)
- No pytest required (no code or tests changed); `git diff --name-only` confirms only the 5 docs/skills files changed.

## Boundary discipline

- No code, tests, tools, input, output, temp, or legacy `datefac/` changes.
- No historical result or QA report deleted or rewritten.
- No project history rewritten; `项目进程.md` milestones preserved, only the current-task pointer refreshed.
- No MinerU / OCR / LLM / VLM runs.
- No `git add .` / `git add -A`; precise path staging only (none performed yet — changes left for the user to review and stage).
- Files changed are exactly the allowed set in the task doc's "Allowed changes" list (minus those that needed no cleanup).

## Decision

`348N_DOCS_CLEANUP_CONFIRMED_AI_HANDOFF_SIMPLIFIED`

## Recommended next task

- `348N-R4 clean data candidate policy review` (the R3 manifest `recommended_next_step` already points to `348A-R4-QA Clean Data Candidate Policy Review`), now that the docs layer is de-duplicated and the current-stage pointers are consistent.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_DOCS_CLEANUP_CONFIRMED_AI_HANDOFF_SIMPLIFIED
files_modified（修改文件数）= 5
files_deleted（删除文件数）= 0
historical_reports_preserved（保留历史报告）= all docs/agent/*_RESULT.md and *_QA*.md intact
code_tests_touched（代码/测试是否改动）= no
git_diff_check（diff 检查）= clean, no whitespace/conflict errors
docs_only（是否仅文档）= yes
LLM / MinerU / OCR calls（外部调用次数）= 0
```
