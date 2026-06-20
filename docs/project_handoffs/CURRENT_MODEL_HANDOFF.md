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
项目进展大白话说明.md
docs/codex_tasks/348N_R6B_FIX_QA_clean_data_csv_row_count_guardrail_review.md
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
```

## Current task

```text
348N-R6B-FIX-QA Clean Data CSV Row Count Guardrail Review
```

This is a focused QA/review task.

It should create:

```text
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
```

## Current facts

R6B-FIX confirmed:

```text
348N_R6B_FIX_CONFIRMED_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_VALID
clean_data_csv_row_count mismatch now raises OutputSchemaGuardrailError
pytest = 75 passed
new_dependency_added = no
pydantic_used = no
pandera_used = no
```

The exact fixed probe:

```text
len(clean_rows) = 1
manifest["clean_data_row_count"] = 1
manifest["clean_data_csv_row_count"] = 999
validate_outputs(...) must raise OutputSchemaGuardrailError
```

Current focus:

```text
independently confirm clean_data_csv_row_count mismatch now loud-fails
confirm clean_data_row_count remains validated
confirm review_queue_csv_row_count remains validated
confirm review_queue_row_count / review_queue_csv_row_count semantics remain unchanged
confirm no dependencies/input/output/legacy boundaries were violated
confirm 75 tests pass
```

Do not modify source code, tests, dependency files, input files, output files, generated output directories, or legacy datefac/.

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.
