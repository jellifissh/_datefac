# Current Handoff

## Workspace

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

## Operating model

```text
review execution report -> decide result -> write next task doc -> give local-agent prompt -> sync progress docs
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
large = bounded implementation; use phased-hard-stop + implementation-with-self-QA
```

## Current task

```text
348N-R7AG lightweight PDF evidence bridge design
```

Task sizing:

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AG changes the next direction from MinerU-first to lightweight evidence bridging so PDF processing cost stays controlled while audit boundaries stay closed.
```

Task document:

```text
docs/codex_tasks/348N_R7AG_lightweight_pdf_evidence_bridge_design.md
```

Expected report:

```text
docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
```

R7AG focus:

```text
avoid MinerU-first default
use lightweight PDF text-layer/page-text bridge
use extraction product page_number / metric_name / period / value as hints
extract only needed pages when page_number exists
design no-page-number fallback search
numeric anchor matching
keyword and period proximity
repeated-number handling
snippet generation
SourceTextEvidence mapping
source_text_provider and source_text_quality metadata
scanned PDF policy
MinerU/OCR/manual review fallback policy
source_file_sha256 cache policy
cost-control workflow for many PDFs
no real PDF run
no dependencies added
no production parser added
readiness gates remain closed
```

## Latest completed result

```text
R7AF-QA commit = 2723251
qa_result = VALID
test_result = PASS; 162 passed in 0.97s
external calls = 0
readiness_gates = CLOSED
```

R7AF-QA confirmed:

```text
loader test-only under tests/agent/
no production hook
JSON object v1 strict schema
bad sidecars fail closed
no partial records
evidence_index metadata-only
review_queue compact-only
full source_text absent from serialized outputs
VERIFIED does not promote to STRONG_EVIDENCE, clean_data, or readiness
```

## Current boundaries

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
legacy datefac/ stays reference-only by default
output files are not committed
MinerU / OCR / LLM / VLM remain unused unless a task explicitly allows them
qualitative_facts admission remains closed
MARKET_REFERENCE_ROW policy stays conservative
VERIFIED is not automatic clean admission
VERIFIED is not production readiness
agent tasks should stage only explicit allowed paths
```

## Next-step guidance

Current next step is R7AG. If R7AG passes, expected next task is R7AH lightweight PDF evidence bridge test-only prototype. Do not jump to batch production, MinerU-first, or production readiness.
