# 348S-R3C Unknown Row Refinement

## Goal

Reduce the third workbook `unknown_row_count = 44` identified by `348S-QA Third Workbook Pilot Review`.

This is a narrow row-type / routing refinement task.

Do not modify unit, period, valuation, evidence, or clean-candidate policy unless the task becomes explicitly blocked by a code bug.

---

## Current context

Third workbook pair:

```text
PDF:   D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf
Excel: D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

R3B output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3b_third_taihao_keji_doubaoai
```

R3B / QA metrics:

```text
row_count_total = 158
clean_data_row_count = 94
review_queue_row_count = 64
unknown_row_count = 44
unit_issue_count = 11
period_issue_count = 8
valuation_issue_count = 1
weak_evidence_count = 158
missing_evidence_count = 0
```

QA conclusion:

```text
348S_QA_THIRD_WORKBOOK_REVIEW_CONFIRMED_NEEDS_R3C_UNKNOWN_ROW_REFINEMENT
```

Observed unknown-row families:

```text
report metadata rows
long thesis or risk narrative lines
business matrix rows
North America AIDC comparative table rows
industry table title or layout rows
mixed narrative-plus-valuation row
```

---

## Required context

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348S_QA_THIRD_WORKBOOK_PILOT_REVIEW.md
docs/agent/348S_R3B_THIRD_WORKBOOK_ZERO_ROW_INTAKE_FOLLOWUP_RESULT.md
```

Inspect the R3B output directory read-only before changing code.

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
tests/agent/fixtures/  # only compact row-type fixtures if useful
docs/agent/348S_R3C_UNKNOWN_ROW_REFINEMENT_RESULT.md
```

Do not modify:

```text
datefac_agent/audit/unit_semantic_checker.py
datefac_agent/audit/period_alignment_checker.py
valuation checker logic
evidence policy
clean candidate policy
legacy datefac/
input/
output/
```

---

## Required diagnosis

Before changing code, inspect unknown rows from the R3B output and report:

```text
unknown row count by sheet
unknown row examples by family
which rows should remain UNKNOWN_ROW
which rows should become NARRATIVE_ASSERTION
which rows should become MARKET_REFERENCE_ROW or another existing row type
which rows are layout / section / metadata rows that should be review-only but more explicitly typed
```

Do not turn uncertain rows into clean data.

---

## Fix intent

Implement the smallest row-type or intake classification refinement needed to reduce `UNKNOWN_ROW` noise.

Preferred behavior:

```text
metadata and section rows should not be treated as clean financial rows
long thesis / risk narrative lines should route as NARRATIVE_ASSERTION / NARRATIVE_REVIEW
industry comparative rows should route more explicitly when safe
business matrix rows should be classified consistently, not randomly UNKNOWN
mixed narrative-plus-valuation rows should remain review-required
```

The goal is better explainability, not higher clean-data volume.

Acceptable outcomes:

```text
unknown_row_count decreases
review_queue remains explainable
clean_data stays free from blocking issues
unit / period / valuation issue counts may change only as a consequence of better row typing, not checker edits
```

---

## Required tests

Add compact regression tests for the new row-type behavior.

Tests should be small and not depend on full output files.

Run existing agent tests afterwards.

---

## Required validation

Run:

```powershell
python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
```

Then rerun the third workbook runner to a new output directory:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202605231822706325_1.pdf --excel-path "D:\_datefac_agent\input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348s_r3c_third_taihao_keji_doubaoai
```

Do not commit output files.

---

## Expected result report

Create:

```text
docs/agent/348S_R3C_UNKNOWN_ROW_REFINEMENT_RESULT.md
```

Include:

```text
Task ID
Files modified
Unknown-row root cause
Unknown-row family audit
Narrow fix summary
Regression tests added
Validation results
Third workbook output directory
Before/after manifest metrics
Unknown-row count change
Clean-data QA
Review-queue QA
Boundary discipline
Decision
Recommended next task
```

Decision values:

```text
348S_R3C_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID
348S_R3C_CONFIRMED_PARTIAL_REFINEMENT_NEEDS_UNIT_PERIOD_FOLLOWUP
348S_R3C_CONFIRMED_NEEDS_DEEPER_ROW_TYPE_REDESIGN
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Unknown-row diagnosis.
5. Exact narrow fix made.
6. Tests added.
7. py_compile result.
8. pytest result.
9. Third workbook runner result.
10. Output directory.
11. Before/after metrics.
12. Clean-data QA after R3C.
13. Review-queue QA after R3C.
14. Whether source changes stayed in allowed scope.
15. Whether output files were not committed.
16. Whether LLM/MinerU/OCR calls were zero.
17. git status -sb.
18. Recommended next task.
