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
docs/codex_tasks/348S_R4_strict_row_unit_period_review_signal_refinement.md
docs/agent/348S_R3C_QA_UNKNOWN_ROW_REFINEMENT_REVIEW.md
docs/agent/348S_R3C_UNKNOWN_ROW_REFINEMENT_RESULT.md
```

## Current task

```text
348S-R4 Strict Row Unit/Period Review Signal Refinement
```

This is a narrow strict-row unit/period review-signal refinement task.

It should create:

```text
docs/agent/348S_R4_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_RESULT.md
```

## Current facts

R3C-QA confirmed unknown-row refinement:

```text
348S_R3C_QA_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID
unknown_row_count: 44 -> 0
clean_data_row_count: 94 -> 94
review_queue_row_count: 64 -> 64
pytest: 36 passed
```

Remaining strict-row signals:

```text
percentage_unit_missing = 10
period_values_missing = 8
```

R4 should inspect and refine those signals without changing evidence policy or clean-candidate policy.

Do not commit output files.

Run baseline:

```text
python -m pytest tests\agent -q
```
