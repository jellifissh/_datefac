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

Task sizing rule:

```text
small = high-risk boundary tasks; use task doc + execution + QA + sync
large = lower-risk or bounded implementation; use phased-hard-stop + implementation-with-self-QA
```

Before writing the local-agent prompt, always include:

```text
task_size = small / medium / large
recommended_reasoning_level = high / very high / max
execution_mode = single-step / phased-hard-stop / implementation-with-self-QA / QA-review-only
reason = why this task needs that level
```

## Current task

```text
348N-R7AF-QA source_text file-backed sidecar loader review
```

Task sizing:

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AF-QA reviews the first file-backed source_text sidecar loader and must confirm it remains test-only, fail-closed, metadata-only, and boundary-safe.
```

Task document:

```text
docs/codex_tasks/348N_R7AF_QA_source_text_file_backed_sidecar_loader_review.md
```

Expected report:

```text
docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md
```

Task type:

```text
QA / review task
```

R7AF-QA focus:

```text
R7AF limited to tests/agent helper/test/fixture files
loader remains test-only
no datefac_agent / runner / CLI / run_pilot hook
JSON object v1 sidecar schema strict
unknown/missing/duplicate/bad hash/bad char_count/untrusted records fail closed
no partial records returned on invalid file
valid sidecar maps to SourceTextEvidence
valid fixture drives VERIFIED through existing wiring
trusted mismatch remains DISAGREED
missing/source/page/locator mismatch remains UNVERIFIED or conservative
metadata-only evidence_index
compact review_queue fields
full source_text absent from serialized outputs
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
docs/codex_tasks/348N_R7AF_QA_source_text_file_backed_sidecar_loader_review.md
docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md
docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
```

## Latest completed result

### R7AF test-only source_text file-backed sidecar loader implementation

```text
commit = 3285ca6 test: add source text sidecar loader coverage
Decision = PASS，R7AF test-only sidecar loader implemented
build_result = PASS
test_result = PASS，pytest tests/agent -q => 162 passed
files_modified = 3
sidecar_loader_result = PASS
fail_closed_result = PASS
evidence_index_validation_result = PASS
review_queue_validation_result = PASS
full_text_serialization_result = PASS
self_qa_result = PASS
readiness_gates = CLOSED
```

R7AF modified:

```text
tests/agent/source_text_sidecar_loader_348n.py
tests/agent/test_source_text_sidecar_loader_348n.py
tests/agent/fixtures/source_text_sidecars/r7af_source_text_sidecar__basic_positive_negative__v1.json
```

R7AF boundaries:

```text
test-only helper under tests/agent/
no datefac_agent production change
no runner / CLI / run_pilot hook
no workbook rerun
no MinerU / OCR / LLM / VLM / PDF extraction
no docs/output/input/temp/data/legacy/config/dependency changes
no clean admission changes
no evidence_level promotion changes
no readiness gate changes
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

Current next step is R7AF-QA.

If R7AF-QA passes, expected next task is R7AG single-real-MinerU-artifact adapter design. Keep it scoped to one real artifact/demo path, not batch production.
