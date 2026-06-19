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
docs/codex_tasks/348N_R4_clean_data_candidate_policy_review.md
docs/agent/348N_R3_QA_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_REVIEW.md
```

## Current task

```text
348N-R4 Clean Data Candidate Policy Review
```

This is a diagnosis/review task, not an implementation task.

It should create:

```text
docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

## Current facts

R3-QA confirmed:

```text
348N_R3_QA_CONFIRMED_REMAINING_UNKNOWN_FAMILY_REFINEMENT_VALID
unknown_row_count = 0
clean_data_row_count = 33
review_queue_row_count = 455
pytest = 48 passed
```

Current focus:

```text
inspect the remaining 33 qualitative_facts clean_data rows
judge whether they should remain clean_data or move to review-only
recommend whether an implementation task is needed
```

Do not modify code, tests, input files, output files, or legacy datefac/.

Do not run MinerU, OCR, LLM, or VLM.
