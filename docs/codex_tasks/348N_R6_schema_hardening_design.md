# 348N-R6 Schema Hardening Design

## Goal

Design the next schema-hardening step for DateFac Agent after R5/R5-QA confirmed the `qualitative_facts` header fix.

This is a diagnosis/design task, not an implementation task.

The purpose is to decide how to add schema guardrails for `clean_data`, `review_queue`, `evidence_index`, and `manifest` without prematurely adding unnecessary framework complexity.

The key question:

```text
Should DateFac Agent add Pandera, Pydantic, both, or a lightweight internal schema layer first?
```

Do not add dependencies or modify code in this task. Produce a design report that can be used to open a later implementation task.

---

## Current context

R5-QA confirmed:

```text
348N_R5_QA_CONFIRMED_QUALITATIVE_FACTS_HEADER_FIX_VALID
clean_data_row_count_before = 33
clean_data_row_count_after = 0
qualitative_facts_row_count = 34
qualitative_facts_explicit_ref_after = 34 / 34
qualitative_facts_evidence_level_after = STRONG_EVIDENCE
unknown_row_count = 0
normalized_testset_record_row_count = 320
market_reference_row_count = 10
pytest_result = 55 passed
LLM / MinerU / OCR / VLM calls = 0
readiness_gates = closed
```

R5 fixed the root cause in intake/header detection. Now the project needs guardrails so similar boundary inversions are caught earlier and more explicitly.

---

## Required context

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md
docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md
docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

Inspect, read-only:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/intake/excel_intake.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/review/review_queue_builder.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Also inspect dependency/config files if present, for example:

```text
requirements*.txt
pyproject.toml
setup.py
setup.cfg
Pipfile
poetry.lock
```

If none exist or none reference Pandera/Pydantic, state that clearly.

---

## Preflight

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## Allowed changes

This task should only create:

```text
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
```

Do not modify source code, tests, dependency files, input files, output files, generated output directories, or historical result/QA reports.

---

## Forbidden changes

Do not modify:

```text
datefac_agent/
tests/
tools/
requirements*.txt
pyproject.toml
setup.py
setup.cfg
Pipfile
poetry.lock
legacy datefac/
input/
output/
temp/
data/
old docs/agent reports
old docs/codex_tasks files
readiness gates
```

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not commit output artifacts.

Do not install dependencies.

Do not use `git add .` or `git add -A`.

---

## Design questions to answer

### 1. Current schema state

Identify how the project currently represents structured data:

```text
plain dicts
CSV rows
JSON manifest
Dataclass / TypedDict / Enum / custom models
pandas DataFrame if any
```

State whether Pydantic and Pandera are currently used.

### 2. Schema hardening targets

Define the first guardrails that would have caught or reduced the R4/R5 problem:

```text
clean_data must not contain TESTSET_SUPPORTING_ROW
clean_data must not contain NORMALIZED_TESTSET_RECORD_ROW
clean_data must not contain REVIEW_REQUIRED rows
clean_data rows must have required traceability fields
review_queue rows must have reason/decision/evidence fields
manifest must preserve readiness gates and external-call counters
manifest must expose clean/review/unknown row counts
```

### 3. Pandera fit

Assess whether Pandera is appropriate for:

```text
clean_data.csv schema validation
review_queue.csv schema validation
audit table validation
DataFrame/CSV-level checks
row_type enum constraints
non-null constraints
forbidden-row-type constraints
```

Explain benefits and risks.

### 4. Pydantic fit

Assess whether Pydantic is appropriate for:

```text
manifest schema
run summary schema
evidence item schema
review queue item schema if object-level validation is needed
task config / API request/response later
```

Explain benefits and risks.

### 5. Minimal first implementation plan

Recommend the smallest safe implementation task. It may be one of:

```text
A. Lightweight internal validation first, no new dependency
B. Pandera only for output CSV/DataFrame validation
C. Pydantic only for manifest/run-summary validation
D. Pandera + Pydantic together, but only if clearly justified
```

Be conservative. Do not recommend a large refactor.

### 6. Where validation should run

Decide where validation should be called:

```text
inside runner before writing outputs
inside tests only
inside a validation helper after output generation
inside future delivery/export gate
```

For current stage, prefer a low-risk placement.

### 7. Proposed next implementation task

Draft the next task name and scope after R6. For example:

```text
348N-R6B output schema guardrails implementation
```

The proposed task should be narrow and testable.

---

## Validation commands

Since this is docs/design-only, run:

```powershell
git diff --check
```

No pytest is required unless you unexpectedly modify code, which should not happen in this task.

---

## Required report

Create:

```text
docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md
```

The report must include:

```text
Task ID
Reviewed files
Current schema state
Pydantic usage assessment
Pandera usage assessment
Schema hardening targets
Minimal recommended implementation
Where validation should run
Risks and non-goals
Validation result
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R6_RECOMMENDS_LIGHTWEIGHT_SCHEMA_GUARDRAILS_FIRST
348N_R6_RECOMMENDS_PANDERA_OUTPUT_SCHEMA_FIRST
348N_R6_RECOMMENDS_PYDANTIC_MANIFEST_SCHEMA_FIRST
348N_R6_RECOMMENDS_PANDERA_AND_PYDANTIC_PHASED_ADOPTION
348N_R6_BLOCKED_BY_MISSING_CONTEXT
```

---

## Required Data Result / 数据结果 fields

Include at least:

```text
Decision（任务结论）= ...
current_pydantic_usage（当前 Pydantic 使用）= yes/no
current_pandera_usage（当前 Pandera 使用）= yes/no
recommended_first_schema_layer（推荐第一层 schema）= ...
first_guardrail_targets（第一批护栏目标）= ...
code_changes_made（是否改代码）= no
pytest_result（测试结果）= not run / not required
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= ...
```

---

## Completion report

Report back with:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Current schema state.
5. Pydantic usage assessment.
6. Pandera usage assessment.
7. Recommended first schema-hardening layer.
8. Proposed first guardrails.
9. Validation result.
10. Whether code/tests/dependency/input/output boundaries were respected.
11. git status -sb.
12. Recommended next task.
13. Data Result / 数据结果.
