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

## Current task

```text
348N-R7AI real PDF text-layer provider design
```

Task sizing:

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AI designs the first real PDF text-layer provider boundary after the lightweight synthetic prototype passed QA. It must avoid implementation, new dependencies, real PDF runs, MinerU-first behavior, and readiness leakage.
```

Task document:

```text
docs/codex_tasks/348N_R7AI_real_pdf_text_layer_provider_design.md
```

Expected report:

```text
docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md
```

R7AI focus:

```text
real PDF text-layer provider interface
whether to mirror R7AH synthetic provider API
dependency strategy: PyMuPDF / pdfplumber / pypdf / optional dependency / dependency audit first
text-layer detection policy
scanned/image-only PDF policy
target-page extraction when page_number exists
capped candidate search when page_number is missing
cache key using source_file_sha256 + provider metadata + extraction config
cache manifest and invalidation
SourceTextEvidence mapping
trusted_source / extraction_method / text_kind definitions
agreement and confidence boundaries
MinerU/OCR/manual review fallback policy
R7AJ implementation vs dependency audit recommendation
```

## Latest completed result

```text
R7AH-QA commit = d0529a7
Decision = PASS; 348N_R7AH_QA_CONFIRMED_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_VALID
test_result = PASS; 180 passed in 0.88s
qa_result = VALID
readiness_gates = CLOSED
```

R7AH-QA confirmed:

```text
prototype test-only under tests/agent/
synthetic page-text provider only
no real PDF IO
no PyMuPDF/pdfplumber/pypdf imports
no new dependencies
no MinerU/OCR/LLM/VLM
no production hook
value + metric + period proximity required
conservative failures remain conservative
SourceTextEvidence mapping valid
evidence_index metadata-only
review_queue compact-only
full snippet text absent from serialized outputs
VERIFIED does not affect STRONG_EVIDENCE, clean admission, or readiness
```

## Current boundaries

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
output files are not committed
MinerU / OCR / LLM / VLM remain unused unless explicitly allowed
qualitative_facts admission remains closed
MARKET_REFERENCE_ROW policy stays conservative
VERIFIED is not automatic clean admission
VERIFIED is not production readiness
agent tasks should stage only explicit allowed paths
```

## Next-step guidance

Execute R7AI. If R7AI passes, choose R7AJ based on dependency findings: either real PDF text-layer provider test-only implementation or dependency audit. Do not jump to real PDF batch runs, MinerU-first, OCR, or production readiness.
