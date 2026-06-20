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
docs/codex_tasks/348N_R6B_FIX_clean_data_csv_row_count_guardrail_completion.md
docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md
docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
```

## Current task

```text
348N-R6B-FIX Clean Data CSV Row Count Guardrail Completion
```

This is a tiny implementation fix task.

It should create:

```text
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
```

## Current facts

R6B-QA confirmed:

```text
348N_R6B_QA_BLOCKED_BY_GUARDRAIL_COVERAGE_GAP
```

The specific blocker:

```text
clean_data_csv_row_count was added by R6B but validate_outputs(...) does not validate it.
clean_data_row_count is validated.
review_queue_csv_row_count is validated.
clean_data_csv_row_count is not validated.
```

Probe from QA:

```text
len(clean_rows) = 1
manifest["clean_data_row_count"] = 1
manifest["clean_data_csv_row_count"] = 999
validate_outputs(...) passes unexpectedly
```

Current focus:

```text
add clean_data_csv_row_count validation to output_schema_guardrails.py
add negative unit test proving mismatch raises OutputSchemaGuardrailError
keep clean_data_row_count and review_queue_csv_row_count validation intact
rerun py_compile, pytest tests\agent -q, and optionally the Linyang pilot
```

Allowed implementation area is narrow:

```text
datefac_agent/audit/output_schema_guardrails.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
```

Only modify `tools/run_agent_excel_intake_audit_348a.py` if strictly necessary; it probably is not necessary.

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.
