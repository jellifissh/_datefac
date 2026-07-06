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
348N-R7AD-QA source_text fixture dry-run review
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7AD-QA reviews controlled fixture dry-run coverage for source_text wiring. It must verify positive/negative coverage, metadata-only outputs, and closed clean/readiness boundaries.
```

Task document:

```text
docs/codex_tasks/348N_R7AD_QA_source_text_fixture_dry_run_review.md
```

Expected report:

```text
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
```

Task type:

```text
QA / review task
```

R7AD-QA focus:

```text
R7AD remains tests-only
in-test SourceTextEvidence objects, no loader
no workbook rerun / run_pilot / real family rerun
no MinerU / OCR / LLM / VLM / PDF extraction
trusted fixture verifies
trusted numeric mismatch -> DISAGREED
missing / source_id mismatch / page mismatch / locator mismatch / untrusted / empty -> UNVERIFIED
evidence_index tempfile validation, metadata only, no full source_text
review_queue in-memory validation, compact fields only, no full source_text
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
docs/codex_tasks/348N_R7AD_QA_source_text_fixture_dry_run_review.md
docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
```

## Latest completed result

### R7AD source_text sidecar fixture dry-run implementation

```text
commit = 9cd4ef6 test: add source text fixture dry-run coverage
Decision = PASS，R7AD source_text fixture dry-run coverage implemented
build_result = PASS
test_result = PASS，pytest tests/agent -q => 134 passed
files_modified = 1
fixture_dry_run_result = PASS
evidence_index_validation_result = PASS
review_queue_validation_result = PASS
full_text_serialization_result = PASS
readiness_gates = CLOSED
```

R7AD modified:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

R7AD boundaries:

```text
tests-only
no loader
no workbook rerun
no MinerU / OCR / LLM / VLM / PDF extraction
no docs/input/output/temp/data/legacy/config/dependency changes
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

Current next step is R7AD-QA.

If R7AD-QA passes, decide between a real workbook dry-run design or a file-backed source_text sidecar loader design. Do not jump to production readiness.
