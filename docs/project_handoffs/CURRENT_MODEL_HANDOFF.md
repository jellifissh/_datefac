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

## Current task

```text
348N-R7AB-QA source_text availability / evidence index wiring review
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7AB-QA reviews the first trusted source_text metadata and checker injection implementation. It must verify conservative defaults, metadata-only serialization, and closed readiness gates.
```

Task document:

```text
docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md
```

Expected report:

```text
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
```

Task type:

```text
QA / review task
```

R7AB-QA focus:

```text
SourceTextEvidence / SourceTextSelection contract
trusted selection by explicit provenance + source_id + page_number + locator
untrusted / empty / mismatched source_text remains UNVERIFIED
default behavior remains UNVERIFIED without source_text index
checker receives source_text only when selected
evidence_index writes metadata but not full text
review_queue compact fields are safe
VERIFIED does not become STRONG_EVIDENCE
VERIFIED does not become clean admission
readiness gates remain closed
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
docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

## Latest completed result

### R7AB source_text availability / evidence index wiring implementation

```text
commit = 12a4726 feat: wire trusted source text metadata
Decision = PASS，R7AB implementation completed and pushed
build_result = PASS
test_result = PASS，pytest tests/agent -q => 123 passed
files_modified = 7
source_text_contract_result = PASS
source_text_selection_result = PASS
agreement_injection_result = PASS
evidence_index_wiring_result = PASS
review_queue_wiring_result = ADDED compact fields
readiness_gates = CLOSED
```

R7AB modified:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/conftest.py
```

R7AB boundaries:

```text
no workbook rerun
no MinerU / OCR / LLM / VLM / PDF extraction
no docs/input/output/temp/data/legacy/config/dependency changes
no clean admission changes
no evidence_level promotion changes
no readiness gate changes
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

Current next step is R7AB-QA.

If R7AB-QA passes, decide whether the next task should be a real fixture/sidecar integration slice or a small workbook-family dry-run review. Do not jump to production readiness.

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
