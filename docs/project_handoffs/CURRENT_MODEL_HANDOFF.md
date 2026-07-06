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
execution_mode = single-step / phased-hard-stop / implementation-with-self-QA
reason = why this task needs that level
```

## Current task

```text
348N-R7AF test-only source_text file-backed sidecar loader implementation
```

Task sizing:

```text
task_size = large
recommended_reasoning_level = max
execution_mode = phased-hard-stop + implementation-with-self-QA
reason = R7AF implements the first file-backed test-only source_text loader and fixtures. It should be faster than design-only microtasks, but must keep fail-closed behavior and avoid production integration.
```

Task document:

```text
docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md
```

Task type:

```text
implementation + tests + self-QA
```

R7AF focus:

```text
test-only JSON object v1 sidecar loader
fixture_scope=test_only
strict required keys, no unknown keys
fixtures under tests/agent/fixtures/source_text_sidecars/
fail-closed invalid file handling
text_sha256 recomputed from UTF-8 text
char_count validation
map records to SourceTextEvidence
valid fixture drives VERIFIED through existing wiring
trusted numeric mismatch remains DISAGREED
missing/mismatch cases remain UNVERIFIED
evidence_index metadata-only validation
review_queue compact fields validation
full source_text absent from serialized outputs
no production loader / CLI / runner hook
no workbook rerun
no MinerU / OCR / LLM / VLM
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
docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md
docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
```

## Latest completed result

### R7AE source_text file-backed sidecar loader design

```text
commit = d24abf9 docs: add R7AE source text loader design
Decision = PASS，R7AE source_text file-backed sidecar loader design completed
build_result = PASS
test_result = PASS，pytest tests/agent -q => 134 passed
sidecar_format_result = PASS，JSON object v1
loader_design_result = PASS，test-only first
fail_closed_design_result = PASS
evidence_index_review_queue_design_result = PASS，no full source_text
readiness_gates = CLOSED
```

R7AE concluded:

```text
JSON object v1, not JSONL
schema_version + fixture_scope=test_only + records[]
strict required fields, no unknown keys
fixture location = tests/agent/fixtures/source_text_sidecars/
loader placement = test-only first
malformed/unsafe/hash mismatch/duplicate/unsupported fields reject with no partial records
text_sha256 = recompute UTF-8 SHA-256
full text remains test-only and must not serialize to evidence_index/review_queue
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

Current next step is R7AF.

R7AF is intentionally a larger bounded task. If R7AF passes, expected next step is R7AF-QA before real workbook dry-run or production integration.
