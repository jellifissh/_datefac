# 348S-R3B Third Workbook Zero-Row Intake Follow-up

## Goal

Follow up after `348S-R3 Targeted Third Workbook Schema Refinement`.

R3 fixed the crash:

```text
_find_key_value_start() no longer raises IndexError on short / one-cell rows
```

But the third workbook still produces zero auditable rows:

```text
sheet_count = 8
row_count_total = 0
row_count_audited = 0
clean_data_row_count = 0
review_queue_row_count = 0
```

This task should diagnose and narrowly fix the zero-row intake behavior for the third workbook.

Do not change audit policy.

---

## Third workbook pair

```text
PDF:   D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf
Excel: D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

The pair is justified by report identity:

```text
PDF first page contains 泰豪科技（600590）
Excel filename contains 泰豪科技
```

---

## Required context

Read:

```text
AGENTS.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/agent/348S_R3_TARGETED_THIRD_WORKBOOK_SCHEMA_REFINEMENT_RESULT.md
docs/agent/348S_THIRD_REAL_WORKBOOK_PILOT_RESULT.md
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
tests/agent/fixtures/  # only for compact intake-shape fixture if useful
docs/agent/348S_R3B_THIRD_WORKBOOK_ZERO_ROW_INTAKE_FOLLOWUP_RESULT.md
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

## Diagnosis requirements

Before fixing, inspect why the workbook becomes zero rows.

Report:

```text
sheet names
observed row shapes per sheet
which sheets are one-column summary sheets
which sheets contain later tabular content
why existing header/key-value detection skipped them
```

Use lightweight workbook inspection only.

Do not run MinerU / OCR / LLM.

---

## Fix intent

Implement the smallest intake adaptation needed to avoid zero-row output.

Likely focus:

```text
one-column section/title rows should be skipped safely
later tabular rows should still be discoverable
summary sheets should not force entire workbook to zero rows
```

The fix should not:

```text
turn section-title rows into clean data
classify all one-column rows as auditable rows
change unit / period / routing policy
relabel market/reference/narrative rules broadly
rewrite workbook intake architecture
```

---

## Required tests

Add at least one compact regression test for the third workbook zero-row shape.

The test should prove:

```text
short / one-column section rows do not prevent later tabular rows from being found
```

Preserve existing tests:

```text
python -m pytest tests\agent -q
```

Current expected baseline before new tests:

```text
30 passed
```

---

## Required validation

Run:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Then rerun third workbook runner:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path "D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3b_third_taihao_keji_doubaoai
```

Do not submit output files.

---

## Expected result report

Create:

```text
docs/agent/348S_R3B_THIRD_WORKBOOK_ZERO_ROW_INTAKE_FOLLOWUP_RESULT.md
```

Include:

```text
Task ID
Files modified
Zero-row root cause
Workbook shape observations
Narrow fix summary
Regression test added
Validation results
Third workbook output directory
Third workbook manifest metrics
Top review queue issue codes if generated
Whether row_count_total is now nonzero
Whether clean_data/review_queue are explainable
Baseline regression notes
Boundary discipline
Decision
Recommended next task
```

Decision values:

```text
348S_R3B_CONFIRMED_ZERO_ROW_INTAKE_FIXED
348S_R3B_CONFIRMED_PARTIAL_FIX_STILL_ZERO_OR_LOW_ROWS
348S_R3B_CONFIRMED_NEEDS_DEEPER_INTAKE_REDESIGN
```

---

## Non-goals

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not run OCR.

Do not re-extract PDFs.

Do not change audit policy.

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
4. Zero-row root cause.
5. Workbook shape observations.
6. Exact narrow fix made.
7. Regression test added.
8. py_compile result.
9. pytest result.
10. Third workbook runner result.
11. Output directory.
12. Manifest metrics.
13. Top review_queue issue codes if generated.
14. Whether row_count_total is now nonzero.
15. Whether output files were not committed.
16. Whether LLM/MinerU/OCR calls were zero.
17. `git status -sb`.
18. Recommended next task.
