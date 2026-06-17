# 348A-R4-QA Clean Data Candidate Policy Review

## Goal

Review the current clean-data candidate policy after the completed 348S third-workbook R3C/R4 chain.

This is a QA/review task, not a code-fix task.

Do not modify source code, tests, input files, or output files.

---

## Current context

Recently confirmed:

```text
348S_R3C_QA_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID
348S_R4_QA_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID
```

Latest third workbook state after R4:

```text
clean_data_row_count = 94
review_queue_row_count = 64
unknown_row_count = 0
unit_issue_count = 11
period_issue_count = 2
valuation_issue_count = 1
```

The clean-data policy must stay conservative:

```text
no narrative/layout/metadata rows in clean_data
no UNKNOWN_ROW rows in clean_data
no rows with blocking unit/period/valuation issues in clean_data
no human-review-required rows in clean_data
client_ready = false
production_ready = false
formal_client_export_allowed = false
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
docs/agent/348S_R4_QA_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_REVIEW.md
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
docs/agent/348S_R3C_QA_UNKNOWN_ROW_REFINEMENT_REVIEW.md
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

## Output directories to inspect

Inspect available latest output directories under:

```text
D:\_datefac_agent\output
```

At minimum, review the third workbook R4 output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r4_third_taihao_keji_doubaoai
```

If present locally, also review earlier clean-data outputs for first and second real workbook runs.

Do not modify or commit any output files.

---

## QA questions

Answer:

```text
Does clean_data contain only internal clean/reference candidates?
Does clean_data exclude NARRATIVE_ASSERTION rows?
Does clean_data exclude UNKNOWN_ROW rows?
Does clean_data exclude metadata / section-anchor / table-title rows?
Does clean_data exclude percentage_unit_missing rows?
Does clean_data exclude implicit_percentage_unit_confirmation_needed rows?
Does clean_data exclude period_values_missing rows?
Does clean_data exclude monetary_unit_mismatch rows?
Does clean_data exclude valuation_metric_unit_suspicious rows?
Does review_queue preserve rows that still need human review?
Are readiness gates still closed?
Are external call counters still zero?
```

---

## Scope

Allowed to create:

```text
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

Do not modify source code.

Do not modify tests.

Do not modify input or output files.

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

---

## Required validation

Run:

```powershell
python -m pytest tests\agent -q
```

No py_compile is required if no Python files are changed.

---

## Expected report

Create:

```text
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

Include:

```text
Task ID
Reviewed output directories
Available sample coverage
Verified metrics
Clean-data composition QA
Narrative/layout/metadata exclusion QA
Unit issue exclusion QA
Period issue exclusion QA
Valuation issue exclusion QA
Review-queue boundary QA
Readiness gate QA
External call QA
Baseline validation
Decision
Recommended next task
```

Decision values:

```text
348A_R4_QA_CONFIRMED_CLEAN_DATA_CANDIDATE_POLICY_VALID
348A_R4_QA_CONFIRMED_NEEDS_CLEAN_DATA_BOUNDARY_REFINEMENT
348A_R4_QA_BLOCKED_BY_MISSING_OUTPUT
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Reviewed output directories.
5. Sample coverage.
6. Verified metrics.
7. Clean-data composition QA.
8. Narrative/layout/metadata exclusion QA.
9. Unit issue exclusion QA.
10. Period issue exclusion QA.
11. Valuation issue exclusion QA.
12. Review-queue boundary QA.
13. Readiness gate QA.
14. External call QA.
15. pytest result.
16. Whether source code was untouched.
17. Whether output files were not committed.
18. Whether LLM/MinerU/OCR calls were zero.
19. git status -sb.
20. Recommended next task.
