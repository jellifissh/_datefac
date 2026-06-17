# 348S-R3 Targeted Third Workbook Schema Refinement

## Goal

Fix the third workbook intake crash discovered by `348S Third Real Workbook Pilot`.

The third workbook pair is justified:

```text
PDF:   D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf
Excel: D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

The runner currently fails during intake before manifest generation:

```text
failure type: IndexError: list index out of range
failure stage: intake
failure location: datefac_agent/intake/excel_intake.py
failure trigger: _find_key_value_start() assumed at least two text cells in a row
```

Known workbook-shape evidence:

```text
single-column summary-style rows exist, such as:
('一、报告基本信息',)
('核心盈利预测与估值（摘要版）',)
```

This task should make intake robust to short rows / single-column summary rows.

Do not broadly redesign intake.

---

## Required context

Read:

```text
AGENTS.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/agent/348S_THIRD_REAL_WORKBOOK_PILOT_RESULT.md
docs/agent/348F_QA_FIXTURE_HARVEST_REVIEW.md
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

## Scope

Allowed to modify:

```text
datefac_agent/intake/excel_intake.py
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/fixtures/  # only if adding a compact crash-regression fixture is useful
docs/agent/348S_R3_TARGETED_THIRD_WORKBOOK_SCHEMA_REFINEMENT_RESULT.md
```

Do not modify:

```text
datefac_agent/audit/unit_semantic_checker.py
datefac_agent/audit/period_alignment_checker.py
clean candidate routing policy
legacy datefac/
input/
output/
```

---

## Required fix intent

Implement a narrow defensive fix around `_find_key_value_start()` or its immediate caller.

The fix should:

```text
handle empty rows
handle one-cell rows
handle summary-section rows without value cells
avoid IndexError
preserve existing key-value summary sheet behavior
preserve existing header-row detection behavior
```

The fix should not:

```text
silently classify every one-column row as clean data
turn section-title rows into market/strict rows
hide unrelated parsing failures
rewrite workbook intake architecture
```

---

## Required tests

Add at least one regression test that reproduces the short-row crash shape.

The test should use compact in-memory rows or a small fixture. It must not depend on the full local workbook.

Minimum expected behavior:

```text
_find_key_value_start or public intake helper does not raise IndexError on rows like:
[('一、报告基本信息',), ('核心盈利预测与估值（摘要版）',)]
```

Also preserve current fixture tests:

```text
unit semantic fixtures
period detection fixtures
routing policy fixtures
```

---

## Required validation

Run:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Then rerun the third workbook pilot with the existing runner:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path "D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3_third_taihao_keji_doubaoai
```

Do not submit output files.

---

## Expected result report

Create:

```text
docs/agent/348S_R3_TARGETED_THIRD_WORKBOOK_SCHEMA_REFINEMENT_RESULT.md
```

Include:

```text
Task ID
Files modified
Crash root cause
Narrow fix summary
Regression test added
Validation results
Third workbook output directory
Third workbook manifest metrics if runner now completes
If runner still fails, exact failure stage and stack summary
Baseline regression notes
Boundary discipline
Decision
Recommended next task
```

Decision values:

```text
348S_R3_CONFIRMED_THIRD_WORKBOOK_INTAKE_CRASH_FIXED
348S_R3_CONFIRMED_PARTIAL_FIX_STILL_BLOCKED
348S_R3_CONFIRMED_NEEDS_DEEPER_INTAKE_REDESIGN
```

---

## Non-goals

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract PDFs.

Do not change audit rules unless absolutely required by the crash fix.

Do not add broad row-type mappings.

Do not claim `client_ready` or `production_ready`.

Do not submit output files.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Crash root cause.
5. Exact narrow fix made.
6. Regression test added.
7. py_compile result.
8. pytest result.
9. Third workbook runner result.
10. Output directory.
11. Manifest metrics if generated.
12. If still blocked, exact failure.
13. Whether first/second behavior tests still pass.
14. Whether source changes were limited to intake/tests.
15. Whether output files were not committed.
16. Whether LLM/MinerU/OCR calls were zero.
17. `git status -sb`.
18. Recommended next task.
