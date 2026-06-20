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
docs/codex_tasks/348N_R6D_guardrails_contract_documentation_update.md
docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md
```

## Current task

```text
348N-R6D Guardrails Contract Documentation Update
```

This is a docs-only contract update task.

It should create:

```text
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
```

## Current facts

R6C recommended:

```text
348N_R6C_RECOMMENDS_ADOPT_OUTPUT_GUARDRAILS_AS_RUNNER_CONTRACT
guardrails_contract_adoption = yes, for current 348A-style Excel audit runner only
future_reports_include_both_counts = yes
```

Important count semantics:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv data-row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv data-row count
unknown_row_count = logical UNKNOWN_ROW classification count
```

Current focus:

```text
document output guardrails as current Excel audit runner contract
write count semantics into stable workflow guidance
state future reports must include both logical and physical CSV counts
update .skills/agent_excel_intake_audit_workflow.md
update docs/agent/项目进程.md
update 项目进展大白话说明.md
create R6D result report
```

Allowed docs-only files:

```text
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
```

Do not modify source code, tests, dependency files, input files, output files, generated output directories, or legacy datefac/.

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.
