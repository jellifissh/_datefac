# Current Handoff

## Workspace

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

## Operating model

After each meaningful completed task, the workflow is:

```text
review execution report -> decide result -> write next task doc -> give short local-agent prompt -> sync progress docs
```

Progress sync targets:

```text
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
```

Before writing the local-agent prompt, always include a reasoning-level recommendation:

```text
recommended_reasoning_level = high / very high / max
reason = why this task needs that level
```

Default rule:

```text
high = ordinary docs sync / simple QA / small bounded changes
very high = implementation + tests, QA touching evidence / clean_data / guardrails
max = architecture, readiness, cross-family regression, evidence-strength semantics, production-boundary decisions
```

Full task specs live in `docs/codex_tasks/`. Chat output should normally include only the decision, next task document path, reasoning-level recommendation, and short local-agent prompt.

## Current task

```text
348N-R7Y deterministic source-value agreement checker / evidence agreement verification slice
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7Y touches VERIFIED / DISAGREED evidence agreement semantics. A wrong implementation can pollute future evidence_strength and readiness interpretation.
```

Task document:

```text
docs/codex_tasks/348N_R7Y_deterministic_source_value_agreement_checker.md
```

Task type:

```text
implementation + tests
```

R7Y focus:

```text
Add deterministic source-value agreement checking.
Populate VERIFIED only when structured numeric values are deterministically found in trusted source evidence text.
Populate DISAGREED only when deterministic comparison proves mismatch.
Keep unavailable / ambiguous / partial evidence as UNVERIFIED.
Do not map VERIFIED to production readiness.
Do not make VERIFIED automatic clean admission.
```

## Minimum read order

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
docs/codex_tasks/348N_R7Y_deterministic_source_value_agreement_checker.md
```

## Latest completed result

### R7X-QA evidence provenance parsing review

```text
commit = 6fb00ec docs: add R7X QA review
Decision = 348N_R7X_QA_CONFIRMED_EVIDENCE_PROVENANCE_PARSING_VALID
build_result = COMPILE_OK
test_result = tests/agent 95 passed
qa_result = VALID
page_number_parsing_result = valid
agreement_status_result = valid
strong_evidence_claim_result = valid
readiness_gates = closed
```

R7X-QA confirmed:

```text
page_number parsed = provenance anchor exists
agreement_status = UNVERIFIED = source-value agreement not checked yet
UNVERIFIED provenance remains WEAK_EVIDENCE
parsed page_number does not automatically become VERIFIED or STRONG_EVIDENCE
MARKET_REFERENCE_ROW policy unchanged
qualitative_facts admission unchanged
R7S strict-table clean-boundary unchanged
readiness gates closed
```

### R7X evidence provenance parsing

```text
commit = 5d8aa24 feat: add evidence provenance parsing
modified files = 5
pytest tests/agent -q = 95 passed
full pytest = 33 historical legacy failures, unrelated to R7X
```

R7X implemented:

```text
page_number parsing from explicit_evidence_ref
agreement_status field on AuditRowResult
evidence_index_writer emits agreement_status
explicit/page provenance + UNVERIFIED remains WEAK_EVIDENCE
VERIFIED / DISAGREED reserved for a future deterministic value-agreement checker
```

Important boundary:

```text
page_number parsed != VERIFIED
UNVERIFIED != STRONG_EVIDENCE
```

## Clean-boundary summary

```text
R7P-FIX2 fixed MARKET_REFERENCE_ROW clean_data leak.
R7S narrowed STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE clean admission for scaffolding / pseudo-header / comparison rows.
R7T confirmed Taihao: clean_data 92 -> 72, review_queue 66 -> 86, 20 risky rows moved to review_queue.
R7U confirmed no R7S regression on Linyang and Anjing.
R7V confirmed cross-family clean-boundary valid, readiness gates remain closed.
```

Current data state:

```text
Taihao R7T clean_data_row_count = 72
Taihao R7T review_queue_row_count = 86
Taihao R7T risky_rows_in_clean_after = no
Linyang R7U clean_data_row_count = 0
Linyang R7U review_queue_row_count = 489
Anjing R7U clean_data_row_count = 65
Anjing R7U review_queue_row_count = 17
```

Readiness gates:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Next-step guidance

Current next step is R7Y.

R7Y should move from page provenance to deterministic source-value agreement verification.

R7Y should still keep readiness gates closed.

After R7Y, the expected next task is R7Y-QA before any workbook-family rerun or readiness claim.

## Boundaries

```text
legacy datefac/ stays reference-only by default
input/output/temp/data source files stay untouched unless a task explicitly allows generated output
output files are not committed
MinerU / OCR / LLM / VLM remain unused unless a task explicitly allows them
readiness gates stay closed
qualitative_facts admission remains closed
MARKET_REFERENCE_ROW policy stays conservative
page_number parsing is not source-value verification
VERIFIED is not automatic clean admission
VERIFIED is not production readiness
agent tasks should stage only explicit allowed paths
```
