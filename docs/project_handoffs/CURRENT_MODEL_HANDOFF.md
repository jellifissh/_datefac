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
docs/codex_tasks/348N_R6_schema_hardening_design.md
docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md
docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md
docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

## Current task

```text
348N-R6 Schema Hardening Design
```

This is a diagnosis/design task, not an implementation task.

It should create:

```text
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
```

## Current facts

R5-QA confirmed:

```text
348N_R5_QA_CONFIRMED_QUALITATIVE_FACTS_HEADER_FIX_VALID
clean_data_row_count: 33 -> 0
qualitative_facts_explicit_ref: 0/33 -> 34/34
qualitative_facts_evidence_level: WEAK_EVIDENCE -> STRONG_EVIDENCE
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
pytest = 55 passed
LLM / MinerU / OCR / VLM calls = 0
readiness_gates = closed
```

Current focus:

```text
design schema guardrails for clean_data, review_queue, evidence_index, and manifest
assess whether to use Pandera, Pydantic, both, or lightweight internal validation first
recommend the smallest safe next implementation task
```

Do not modify source code, tests, dependency files, input files, output files, generated output directories, or legacy datefac/.

Do not install dependencies.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.
