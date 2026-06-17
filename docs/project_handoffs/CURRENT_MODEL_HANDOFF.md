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
docs/codex_tasks/348S_R4_QA_strict_row_unit_period_review_signal_refinement.md
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
docs/agent/348S_R3C_QA_UNKNOWN_ROW_REFINEMENT_REVIEW.md
```

## Current task

```text
348S-R4-QA Strict Row Unit/Period Review Signal Refinement Review
```

This is a QA/review task.

It should create:

```text
docs/agent/348S_R4_QA_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_REVIEW.md
```

## Current facts

R4 result:

```text
clean_data_row_count: 94 -> 94
review_queue_row_count: 64 -> 64
unit_issue_count: 11 -> 11
period_issue_count: 8 -> 2
unknown_row_count: 0 -> 0
pytest: 38 passed
```

R4-QA must check whether strict-row unit/period review-signal refinement is valid and did not widen clean-data acceptance.

Do not modify source code, tests, input files, or output files for this review task.

Run baseline:

```text
python -m pytest tests\agent -q
```
