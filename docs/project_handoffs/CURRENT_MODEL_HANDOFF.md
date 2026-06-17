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
docs/codex_tasks/348N_new_real_workbook_generalization_pilot.md
docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
docs/agent/348S_R4_QA_STRICT_ROW_UNIT_PERIOD_REVIEW_SIGNAL_REFINEMENT_REVIEW.md
```

## Current task

```text
348N New Real Workbook Generalization Pilot
```

This is a no-code-change generalization pilot.

It should create:

```text
docs/agent/348N_NEW_REAL_WORKBOOK_GENERALIZATION_PILOT_RESULT.md
```

## Current facts

Recent validated chain:

```text
348S_R3C_QA_CONFIRMED_UNKNOWN_ROW_REFINEMENT_VALID
348S_R4_QA_CONFIRMED_STRICT_ROW_UNIT_PERIOD_REFINEMENT_VALID
348A_R4_QA_CONFIRMED_CLEAN_DATA_CANDIDATE_POLICY_VALID
```

Current focus:

```text
find a new real PDF+Excel pair
run current pipeline without code changes
inspect manifest / clean_data / review_queue
report whether current policy generalizes
```

Do not modify source code, tests, input files, or output files.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output files.

Run baseline:

```text
python -m pytest tests\agent -q
```
