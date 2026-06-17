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
docs/codex_tasks/348S_R3C_unknown_row_refinement.md
docs/agent/348S_QA_THIRD_WORKBOOK_PILOT_REVIEW.md
docs/agent/348S_R3B_THIRD_WORKBOOK_ZERO_ROW_INTAKE_FOLLOWUP_RESULT.md
```

## Current task

```text
348S-R3C Unknown Row Refinement
```

This is a narrow row-type / routing refinement task.

It should create:

```text
docs/agent/348S_R3C_UNKNOWN_ROW_REFINEMENT_RESULT.md
```

## Current facts

Third workbook QA decision:

```text
348S_QA_THIRD_WORKBOOK_REVIEW_CONFIRMED_NEEDS_R3C_UNKNOWN_ROW_REFINEMENT
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

R3C focus:

```text
reduce unknown_row_count = 44
classify metadata / narrative / business matrix / industry comparison / layout rows more explicitly
keep clean_data clean
keep review_queue explainable
```

Do not modify unit, period, valuation, evidence, or clean-candidate policy for this task.

Do not commit output files.

Run baseline:

```text
python -m pytest tests\agent -q
```
