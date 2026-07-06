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
348N-R7AC source_text sidecar fixture integration / dry-run design
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7AC designs the first safe fixture/dry-run path for exercising R7AB source_text wiring without trusting unsafe workbook fields or opening readiness gates.
```

Task document:

```text
docs/codex_tasks/348N_R7AC_source_text_sidecar_fixture_integration_dry_run_design.md
```

Expected report:

```text
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
```

Task type:

```text
design / review task
```

R7AC focus:

```text
fixture sidecar format recommendation
fixture location recommendation
dry-run path recommendation
positive fixture cases
negative fixture cases
evidence_index metadata validation design
review_queue compact field validation design
no workbook rerun
no MinerU / OCR / LLM / VLM
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
docs/codex_tasks/348N_R7AC_source_text_sidecar_fixture_integration_dry_run_design.md
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
```

## Latest completed result

### R7AB-QA source_text availability / evidence index wiring review

```text
commit = 758ec98 docs: add R7AB QA review
Decision = PASS，R7AB-QA confirms source_text wiring valid
build_result = PASS
test_result = PASS，pytest tests/agent -q => 123 passed
files_modified = 1
boundary_check = PASS
qa_result = VALID
readiness_gates = CLOSED
```

R7AB-QA confirmed:

```text
source text contract review = PASS
source text selection review = PASS
agreement checker injection review = PASS
evidence index metadata review = PASS, metadata/hash only, no full source_text
review queue compact fields review = PASS, no full source_text
VERIFIED does not affect STRONG_EVIDENCE, clean admission, or readiness
```

## Current boundaries

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
legacy datefac/ stays reference-only by default
input/output/temp/data source files stay untouched unless a task explicitly allows generated output
output files are not committed
MinerU / OCR / LLM / VLM remain unused unless a task explicitly allows them
qualitative_facts admission remains closed
MARKET_REFERENCE_ROW policy stays conservative
page_number parsing is not source-value verification
VERIFIED is not automatic clean admission
VERIFIED is not production readiness
agent tasks should stage only explicit allowed paths
```

## Next-step guidance

Current next step is R7AC.

R7AC is design-only. If it passes, likely next step is R7AD fixture sidecar dry-run implementation, followed by R7AD-QA.
