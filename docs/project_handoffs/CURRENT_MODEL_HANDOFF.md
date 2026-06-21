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
docs/codex_tasks/348N_R6D_QA_guardrails_contract_documentation_review.md
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md
docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md
```

## Current task

```text
348N-R6D-QA Guardrails Contract Documentation Review
```

This is a docs QA/review task.

It should create:

```text
docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md
```

## Current facts

R6D reported:

```text
348N_R6D_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTED
guardrails_contract_documented = yes
count_semantics_documented = yes
future_report_template_documented = yes
code_changes_made = no
```

R6D updated:

```text
.skills/agent_excel_intake_audit_workflow.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md
```

Current focus:

```text
verify .skills documents validate_outputs(...) as current Excel audit runner contract
verify count semantics are clear and correct
verify future report template lists logical and physical CSV counts
verify 项目进程 remains compact
verify 大白话说明 is user-readable
verify no source/test/dependency/input/output/legacy boundaries were violated
```

Important count semantics to verify:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv data-row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv data-row count
unknown_row_count = logical UNKNOWN_ROW classification count
```

Do not modify source code, tests, dependency files, input files, output files, generated output directories, or legacy datefac/.

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.
