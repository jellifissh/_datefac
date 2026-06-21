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
docs/codex_tasks/348N_R7P_FIX2_market_reference_clean_data_admission_policy_alignment.md
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md
docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md
docs/agent/348N_R7_QUALITATIVE_FACTS_NARROW_CLEAN_ADMISSION_POLICY_DESIGN.md
```

## Current task

```text
348N-R7P-FIX2 Market Reference Clean Data Admission Policy Alignment
```

This is a tiny implementation fix task.

Expected result report:

```text
docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md
```

## Current facts

R7P-FIX confirmed the root cause:

```text
MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue currently becomes INTERNAL_REFERENCE_CANDIDATE.
clean_rows includes INTERNAL_REFERENCE_CANDIDATE.
output guardrails forbid MARKET_REFERENCE_ROW in clean_data.
```

Required behavior:

```text
MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
```

Allowed files:

```text
datefac_agent/review/clean_candidate_policy.py
tests/agent/test_agent_excel_intake_audit_348a.py
docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md
```

Do not modify legacy datefac, input/output/temp/data source files, dependencies, readiness gates, or export behavior.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.
