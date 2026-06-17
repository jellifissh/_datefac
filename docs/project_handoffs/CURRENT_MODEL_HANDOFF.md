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
docs/codex_tasks/348N_R2_normalized_testset_intake_schema_support.md
docs/agent/348N_R1_LINYANG_UNKNOWN_ROW_SHAPE_DIAGNOSIS.md
docs/agent/348N_NEW_REAL_WORKBOOK_GENERALIZATION_PILOT_RESULT.md
```

## Current task

```text
348N-R2 Normalized Testset Intake Schema Support
```

This is a targeted implementation task.

It should create:

```text
docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md
```

## Current facts

R1 diagnosis:

```text
348N_R1_CONFIRMED_LINYANG_UNKNOWN_ROW_FAMILIES_DIAGNOSED
normalized_testset unknown rows = 319
normalized_testset is a long-record testset schema, not a normal wide workbook table
```

Current focus:

```text
add narrow schema recognition for normalized_testset
stop treating normalized_testset rows as generic UNKNOWN_ROW
keep normalized_testset rows review-only / schema-specific
avoid widening clean_data
```

Do not route normalized_testset rows directly into STRICT_FINANCIAL_TABLE_ROW or MARKET_REFERENCE_ROW.

Do not modify legacy datefac/.

Do not commit output files.

Do not run MinerU, OCR, LLM, or VLM.
