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

Before writing the local-agent prompt, always include:

```text
recommended_reasoning_level = high / very high / max
reason = why this task needs that level
```

Full task specs live in `docs/codex_tasks/`.

## Current task

```text
348N-R7AB source_text availability / evidence index wiring implementation
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7AB introduces the first source_text metadata and checker injection implementation. It must preserve conservative defaults and avoid clean/readiness changes.
```

Task document:

```text
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
```

Task type:

```text
implementation + tests
```

R7AB focus:

```text
source_text sidecar/index contract
trusted source_text selection by source_id/page_number/locator
checker-call-time source_text injection
evidence_index source_text metadata
review_queue compact fields if safe
default behavior remains UNVERIFIED without trusted source_text
no OCR / LLM / VLM
no readiness gate changes
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
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

## Latest completed result

### R7AA source_text integration design

```text
commit = e5ec327 docs: add R7AA source text integration design
Decision = PASS，R7AA source_text integration design completed
build_result = PASS
test_result = PASS，pytest tests/agent -q => 111 passed
source_text_availability_result = CURRENT_PIPELINE_HAS_NO_TRUSTED_SOURCE_TEXT
integration_design_result = PASS
evidence_index_design_result = PASS
readiness_gates = CLOSED
```

R7AA concluded:

```text
active pipeline has no trusted production source_text carrier
workbook fields are provenance hints / extracted workbook fields, not trusted source evidence text
source_text should use a provenance-tied sidecar/index
missing / untrusted / mismatched source_text remains UNVERIFIED
full source_text should not be serialized by default
```

## Clean-boundary summary

```text
R7P-FIX2 fixed MARKET_REFERENCE_ROW clean_data leak.
R7S narrowed strict-table scaffolding clean admission.
R7T confirmed Taihao clean 92 -> 72, review 66 -> 86.
R7U confirmed no R7S regression on Linyang and Anjing.
R7V confirmed cross-family clean-boundary valid, readiness gates remain closed.
```

Readiness gates:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Next-step guidance

Current next step is R7AB.

After R7AB, expected next task is R7AB-QA before any real workbook rerun or wider source_text pipeline.

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
