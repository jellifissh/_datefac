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
348N-R7AD source_text sidecar fixture dry-run implementation
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7AD implements controlled fixture dry-run coverage for source_text wiring. It must prove metadata and review_queue behavior without real reruns, full text serialization, or readiness changes.
```

Task document:

```text
docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md
```

Task type:

```text
implementation + tests, tests-only preferred
```

R7AD focus:

```text
in-test SourceTextEvidence objects
tempfile evidence_index validation
in-memory review_queue validation
positive trusted source_text cases
negative missing/mismatch/untrusted/empty source_text cases
full source_text absent from serialized outputs
VERIFIED does not become STRONG_EVIDENCE
VERIFIED does not become clean admission
readiness gates remain closed
no workbook rerun
no MinerU / OCR / LLM / VLM
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
docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
```

## Latest completed result

### R7AC source_text sidecar fixture integration / dry-run design

```text
commit = a3cc7f8 docs: add R7AC source text fixture design
Decision = PASS，R7AC design completed
build_result = PASS
test_result = PASS，pytest tests/agent -q => 123 passed
fixture_design_result = PASS
dry_run_design_result = PASS
evidence_index_validation_design_result = PASS
review_queue_validation_design_result = PASS
readiness_gates = CLOSED
```

R7AC concluded:

```text
fixture format: in-test SourceTextEvidence objects first
future file-backed fixtures: tests/agent/fixtures/source_text_sidecars/
dry-run path: lower-level helpers first, not run_pilot(...) or real workbook reruns
evidence_index validation: tempfile
review_queue validation: in-memory
full source_text must not be serialized
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

Current next step is R7AD.

If R7AD passes, expected next task is R7AD-QA before any real workbook dry-run or file-backed sidecar loader.
