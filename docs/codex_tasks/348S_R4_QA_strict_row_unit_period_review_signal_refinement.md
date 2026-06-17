# 348S-R4-QA Strict Row Unit/Period Review Signal Refinement Review

## Goal

Review the R4 strict-row unit/period review signal refinement.

This is a QA/review task, not a code-fix task.

Do not modify source code, tests, input files, or output files.

---

## Current result to review

R4 result document:

```text
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
```

R4 output directory, read-only:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348s_r4_third_taihao_keji_doubaoai
```

Known R4 metrics:

```text
clean_data_row_count: 94 -> 94
review_queue_row_count: 64 -> 64
unit_issue_count: 11 -> 11
period_issue_count: 8 -> 2
strict_financial_table_row_count: 110 -> 104
narrative_assertion_count: 46 -> 52
issue_count_total: 178 -> 172
unknown_row_count: 0 -> 0
pytest: 38 passed
```

R4 decision:

```text
348S_R4_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID
```

The QA should verify whether that decision is acceptable.

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
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
docs/agent/348S_R3C_QA_UNKNOWN_ROW_REFINEMENT_REVIEW.md
docs/agent/348S_R3C_UNKNOWN_ROW_REFINEMENT_RESULT.md
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

## Review focus

Check whether R4 safely refined strict-row unit/period review signals.

Answer:

```text
Did clean_data stay unchanged and free from blocking issues?
Did review_queue stay unchanged in size and become more accurate?
Were the 10 implicit percentage rows correctly changed from percentage_unit_missing to implicit_percentage_unit_confirmation_needed?
Did those 10 rows stay in review and out of clean_data?
Were the six removed period issues actually section-anchor / table-title rows?
Did the two remaining period signals remain valid review signals?
Did strict_financial_table_row_count 110 -> 104 reflect only section-anchor retyping?
Did unit/period changes stay narrow and not globally loosen checks?
Were evidence policy and clean candidate policy unchanged?
```

---

## Scope

Allowed to create:

```text
docs/agent/348S_R4_QA_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_REVIEW.md
```

Do not modify source code.

Do not modify tests.

Do not modify input or output files.

Do not commit output files.

Do not run MinerU, OCR, LLM, or VLM.

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
docs/agent/348S_R4_QA_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_REVIEW.md
```

Include:

```text
Task ID
Reviewed result and output directory
Before/after metrics
Clean-data QA
Review-queue QA
Implicit-percentage unit signal QA
Period signal QA
Strict-row retyping QA
Policy stability QA
Boundary discipline
Baseline validation
Decision
Recommended next task
```

Decision values:

```text
348S_R4_QA_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID
348S_R4_QA_CONFIRMED_NEEDS_UNIT_SIGNAL_ADJUSTMENT
348S_R4_QA_CONFIRMED_NEEDS_PERIOD_SIGNAL_ADJUSTMENT
348S_R4_QA_BLOCKED_BY_MISSING_OUTPUT
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Reviewed result and output directory.
5. Clean-data QA conclusion.
6. Review-queue QA conclusion.
7. Implicit-percentage unit signal QA conclusion.
8. Period signal QA conclusion.
9. Strict-row retyping QA conclusion.
10. Policy stability QA conclusion.
11. pytest result.
12. Whether source code was untouched.
13. Whether output files were not committed.
14. Whether LLM/MinerU/OCR calls were zero.
15. git status -sb.
16. Recommended next task.
