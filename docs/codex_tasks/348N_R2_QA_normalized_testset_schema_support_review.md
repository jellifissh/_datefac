# 348N-R2-QA Normalized Testset Schema Support Review

## Goal

Review the 348N-R2 implementation that added explicit support for the `normalized_testset` long-record schema.

This is a QA/review task, not a code-fix task.

Do not modify source code, tests, input files, or output files.

---

## Current implementation result

R2 decision:

```text
348N_R2_CONFIRMED_NORMALIZED_TESTSET_SCHEMA_SUPPORT_VALID
```

R2 changed files:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/intake/excel_intake.py
datefac_agent/review/clean_candidate_policy.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md
```

R2 key behavior:

```text
normalized_testset header-family detection added
normalized_testset rows route to NORMALIZED_TESTSET_RECORD_ROW
NORMALIZED_TESTSET_RECORD_ROW stays review-only / schema-specific
NORMALIZED_TESTSET_RECORD_ROW is explicitly excluded from clean_data promotion
normal wide workbook classification should remain unchanged
```

R2 metrics:

```text
row_count_total: 483 -> 484
review_queue_row_count: 446 -> 447
clean_data_row_count: 37 -> 37
unknown_row_count: 367 -> 48
normalized_testset_record_row_count: 0 -> 320
unit_issue_count: 9 -> 9
period_issue_count: 0 -> 0
valuation_issue_count: 0 -> 0
evidence_issue_count: 397 -> 78
strong_evidence_count: 86 -> 406
weak_evidence_count: 397 -> 78
pytest: 42 passed
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
docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md
docs/agent/348N_R1_LINYANG_UNKNOWN_ROW_SHAPE_DIAGNOSIS.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
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

## Files to review

Review the R2 diff and current implementation:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/intake/excel_intake.py
datefac_agent/review/clean_candidate_policy.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md
```

Confirm:

```text
runner changes are only count/manifest/summary reporting support
clean_candidate_policy explicitly excludes NORMALIZED_TESTSET_RECORD_ROW
schema detection is header-family based, not filename-only
wide workbook classification regression tests still exist
no output files are committed
```

---

## Output to inspect

Inspect R2 output read-only:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema
```

Compare against baseline output read-only:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348n_linyang_energy_testset
```

Do not modify or commit output files.

---

## QA questions

Answer:

```text
Did normalized_testset rows stop being generic UNKNOWN_ROW?
Is NORMALIZED_TESTSET_RECORD_ROW review-only / schema-specific?
Is NORMALIZED_TESTSET_RECORD_ROW excluded from clean_data?
Did clean_data_row_count stay stable at 37?
Did unknown_row_count drop for the intended reason rather than by hiding rows?
Did review_queue become more explainable rather than artificially smaller?
Did runner changes stay limited to statistics/reporting?
Did normal wide workbook classification remain protected by tests?
Did readiness gates remain closed?
Did external call counters remain zero?
```

---

## Scope

Allowed to create:

```text
docs/agent/348N_R2_QA_NORMALIZED_TESTSET_SCHEMA_SUPPORT_REVIEW.md
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
docs/agent/348N_R2_QA_NORMALIZED_TESTSET_SCHEMA_SUPPORT_REVIEW.md
```

Include:

```text
Task ID
Reviewed files
Reviewed output directories
Implementation boundary QA
Schema detection QA
Row-type/routing QA
Clean-data boundary QA
Review-queue explainability QA
Runner reporting QA
Regression test QA
Readiness gate QA
External call QA
Baseline validation
Decision
Recommended next task
```

Decision values:

```text
348N_R2_QA_CONFIRMED_NORMALIZED_TESTSET_SCHEMA_SUPPORT_VALID
348N_R2_QA_CONFIRMED_NEEDS_SCHEMA_SUPPORT_REFINEMENT
348N_R2_QA_BLOCKED_BY_MISSING_OUTPUT
348N_R2_QA_BLOCKED_BY_REGRESSION_RISK
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Reviewed files.
5. Reviewed output directories.
6. Implementation boundary QA.
7. Schema detection QA.
8. Row-type/routing QA.
9. Clean-data boundary QA.
10. Review-queue explainability QA.
11. Runner reporting QA.
12. Regression test QA.
13. Readiness gate QA.
14. External call QA.
15. pytest result.
16. Whether source code was untouched.
17. Whether output files were not committed.
18. Whether LLM/MinerU/OCR calls were zero.
19. git status -sb.
20. Recommended next task.
