# Current Handoff

## Workspace

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

## Read order

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
docs/codex_tasks/348A_R4_QA_clean_data_candidate_policy_review.md
docs/agent/348S_R4_QA_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_REVIEW.md
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
```

## Current task

```text
348A-R4-QA Clean Data Candidate Policy Review
```

This is a QA/review task.

It should create:

```text
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

## Current facts

Recent validated chain:

```text
348S_R3C_QA_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID
348S_R4_QA_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID
```

Latest third workbook R4 state:

```text
clean_data_row_count = 94
review_queue_row_count = 64
unknown_row_count = 0
unit_issue_count = 11
period_issue_count = 2
valuation_issue_count = 1
```

Current review focus:

```text
clean_data candidate boundary
no review-required rows in clean_data
no narrative/layout/metadata rows in clean_data
no blocking unit/period/valuation rows in clean_data
readiness gates remain closed
```

Do not modify source code, tests, input files, or output files for this review task.

Run baseline:

```text
python -m pytest tests\agent -q
```
