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
docs/codex_tasks/348N_R1_linyang_unknown_row_shape_diagnosis.md
docs/agent/348N_NEW_REAL_WORKBOOK_GENERALIZATION_PILOT_RESULT.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

## Current task

```text
348N-R1 Linyang Unknown Row Shape Diagnosis
```

This is a diagnosis task, not a code-fix task.

It should create:

```text
docs/agent/348N_R1_LINYANG_UNKNOWN_ROW_SHAPE_DIAGNOSIS.md
```

## Current facts

348N selected a new Linyang Energy PDF+Excel pair and ran the current pipeline without code changes.

Result:

```text
row_count_total = 483
clean_data_row_count = 37
review_queue_row_count = 446
unknown_row_count = 367
unit_issue_count = 9
period_issue_count = 0
valuation_issue_count = 0
```

Current focus:

```text
diagnose the 367 unknown rows by sheet and row family
determine whether this is normal workbook schema, testset-specific shape, or out-of-scope
do not change routing rules yet
```

Do not modify source code, tests, input files, or output files.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.

Run baseline:

```text
python -m pytest tests\agent -q
```
