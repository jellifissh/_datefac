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
348N-R7AE source_text file-backed sidecar loader design
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7AE designs the file-backed source_text sidecar loader contract after fixture dry-run QA. It must keep fail-closed behavior and avoid turning fixture evidence into production readiness.
```

Task document:

```text
docs/codex_tasks/348N_R7AE_source_text_file_backed_sidecar_loader_design.md
```

Expected report:

```text
docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
```

Task type:

```text
design / review task
```

R7AE focus:

```text
JSON vs JSONL sidecar format
sidecar schema and required fields
fixture location
loader placement: test-only first or runner-visible later
fail-closed validation rules
text_sha256 calculation and validation
full source_text handling
mapping file records into SourceTextEvidence
source_document_id to EvidenceRef.source_id binding
evidence_index / review_queue metadata-only validation
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
docs/codex_tasks/348N_R7AE_source_text_file_backed_sidecar_loader_design.md
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
docs/codex_tasks/348N_R7AD_QA_source_text_fixture_dry_run_review.md
docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
```

## Latest completed result

### R7AD-QA source_text fixture dry-run review

```text
commit = 39e01ba docs: add R7AD QA review
Decision = PASS，R7AD-QA confirms fixture dry-run is valid
build_result = PASS
test_result = PASS，pytest tests/agent -q => 134 passed
files_modified = 1
fixture_dry_run_result = PASS
evidence_index_validation_result = PASS
review_queue_validation_result = PASS
full_text_serialization_result = PASS
qa_result = VALID
readiness_gates = CLOSED
```

R7AD-QA confirmed:

```text
R7AD is tests-only
in-test SourceTextEvidence objects, no loader
trusted fixture verifies
trusted mismatch DISAGREED
missing / mismatch / untrusted / empty -> UNVERIFIED
evidence_index metadata-only, no full source_text
review_queue compact fields, no full source_text
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

Current next step is R7AE.

If R7AE passes, likely next task is R7AF file-backed source_text sidecar loader implementation. Do not jump to real workbook rerun or production readiness.
