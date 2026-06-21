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
docs/codex_tasks/348N_R7P_FIX_market_reference_clean_data_boundary_leak_investigation.md
docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md
docs/agent/348N_R7_QUALITATIVE_FACTS_NARROW_CLEAN_ADMISSION_POLICY_DESIGN.md
docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md
```

## Current task

```text
348N-R7P-FIX Market Reference Clean Data Boundary Leak Investigation
```

This is a focused diagnosis / root-cause task.

It should create:

```text
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
```

## Current facts

R7P reported:

```text
348N_R7P_BLOCKED_BY_OUTPUT_GUARDRAIL_FAILURE
```

The failing workbook was:

```text
input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

The guardrail failure was:

```text
clean_data boundary violation: row 0
sheet = 报告核心信息与投资要点
metric = 收盘价
row_type = MARKET_REFERENCE_ROW
```

The current output guardrails contract forbids these row types in clean_data:

```text
TESTSET_SUPPORTING_ROW
NORMALIZED_TESTSET_RECORD_ROW
MARKET_REFERENCE_ROW
UNKNOWN_ROW
```

Current focus:

```text
investigate why MARKET_REFERENCE_ROW became eligible for clean_data
identify whether row typing, clean admission policy, clean row assembly, or workbook-family-specific logic is at fault
prefer diagnosis report first
only implement a tiny fix if root cause is unambiguous and tests can prove it
```

Do not modify legacy datefac/.

Do not modify input/output/temp/data.

Do not add dependencies.

Do not use Pydantic, Pandera, or pandas.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.
