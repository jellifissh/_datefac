# 348N-R7AI real PDF text-layer provider design

## Task ID

```text
348N-R7AI real PDF text-layer provider design
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AI designs the first real PDF text-layer provider boundary after the synthetic lightweight bridge prototype passed QA, without implementation, new dependencies, real PDF runs, heavy fallback, production hook, or readiness leakage.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating d0529a7..17963c2
  Fast-forward
  created docs/codex_tasks/348N_R7AI_real_pdf_text_layer_provider_design.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git branch --show-current:
  pivot/348-agent-foundation

git log --oneline -12:
  17963c2 docs: update handoff after R7AH QA
  3fefad9 docs: refresh plain-language progress after R7AH QA
  f5b52d3 docs: sync progress after R7AH QA
  3012b3d docs: add R7AI real PDF text layer provider design task
  d0529a7 docs: add R7AH QA review
  0bc70a9 docs: update handoff after R7AH
  40312bd docs: refresh plain-language progress after R7AH
  91a596e docs: sync progress after R7AH
  64ad129 docs: add R7AH QA task
  26e2717 test: add lightweight PDF evidence bridge prototype
  6252c84 docs: update handoff after R7AG
  faf5dc8 docs: refresh plain-language progress after R7AG
```

Worktree was clean after pull.

## Files reviewed

Required context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AI_real_pdf_text_layer_provider_design.md`
- `docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md`
- `docs/codex_tasks/348N_R7AH_QA_lightweight_pdf_evidence_bridge_prototype_review.md`
- `docs/codex_tasks/348N_R7AH_lightweight_pdf_evidence_bridge_test_only_prototype.md`
- `docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md`
- `docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md`

Read-only implementation / boundary files:

- `tests/agent/lightweight_pdf_evidence_bridge_348n.py`
- `tests/agent/test_lightweight_pdf_evidence_bridge_348n.py`
- `tests/agent/source_text_sidecar_loader_348n.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/review/clean_candidate_policy.py`

Dependency/config files:

- `requirements.txt` exists and contains `pandas`, `openpyxl`, `requests`, `pyyaml`
- `pyproject.toml` missing
- `setup.cfg` missing
- `setup.py` missing

No existing project dependency on `PyMuPDF`, `fitz`, `pdfplumber`, or `pypdf` was found in the inspected dependency/config files.

## Problem statement

DateFac needs to move from the R7AH synthetic page-text provider toward a real PDF text-layer provider without accidentally creating an uncontrolled PDF parsing product path. The first real-provider design must preserve the R7AG/R7AH lightweight evidence route:

```text
existing extraction row hints
+ original PDF identity
+ targeted real PDF text-layer page extraction
+ value / metric / period anchor matching
-> bounded snippet SourceTextEvidence
-> existing agreement checker / review_queue / evidence_index
```

This design is not a PDF extraction pipeline. It is a bounded provider contract and dependency strategy for a later, QA-gated implementation.

## Provider boundary design

R7AI should mirror the R7AH synthetic provider shape while adding real-file identity, provider metadata, and explicit failure statuses.

Recommended interface, design-only:

```text
PdfTextLayerProvider
  provider_name: str
  provider_version: str
  extraction_config_hash: str
  provider_metadata() -> ProviderMetadata
  page_count(source: PdfSourceIdentity) -> ProviderResult[int]
  has_text_layer(source: PdfSourceIdentity, page_number: int | None = None) -> TextLayerProbeResult
  get_page_text(source: PdfSourceIdentity, page_number: int) -> PageTextResult
  search_pages(source: PdfSourceIdentity, max_pages: int, candidate_pages: list[int] | None = None) -> iterable[PageTextResult]
```

Recommended source identity:

```text
PdfSourceIdentity
  source_document_id
  source_pdf_path
  source_file_sha256
  file_size_bytes
  modified_time_hint
```

Identity policy:

1. `source_file_sha256` is the canonical cache and provider identity.
2. `source_pdf_path` is a locator/hint and must not be trusted alone.
3. `source_document_id` must bind provider output to existing DateFac evidence refs.
4. If path exists but SHA-256 mismatches expected identity, fail closed.

Provider result statuses should be explicit:

```text
OK
MISSING_DEPENDENCY
SOURCE_FILE_MISSING
SOURCE_HASH_MISMATCH
INVALID_PAGE_NUMBER
PDF_ENCRYPTED
PDF_UNREADABLE
PAGE_TEXT_EMPTY
NO_TEXT_LAYER
SCANNED_OR_IMAGE_ONLY
EXTRACTION_ERROR
SEARCH_CAP_EXCEEDED
```

Provider errors should be data results, not uncaught audit-pipeline crashes. Fatal programmer errors may still raise in tests, but runtime provider failures should route rows to `UNVERIFIED` / `REVIEW_REQUIRED`.

## Dependency strategy

Current dependency finding:

```text
requirements.txt = pandas, openpyxl, requests, pyyaml
pyproject.toml = missing
setup.cfg = missing
setup.py = missing
existing PDF text-layer dependency = none found
```

R7AI recommendation:

```text
do not implement R7AJ with a real PDF dependency yet
do a dedicated dependency audit first
```

Dependency policy:

1. Keep the provider behind an adapter boundary.
2. Use optional imports only inside a provider adapter module.
3. Missing dependency returns `MISSING_DEPENDENCY`, not silent fallback and not production failure.
4. Adding `PyMuPDF`, `pdfplumber`, or `pypdf` requires a separate dependency task and QA.
5. Do not add more than one real provider dependency in the first implementation slice.

Library positioning for the audit:

```text
pypdf = pure Python, lighter install, likely enough for text-layer smoke tests, weaker layout fidelity
PyMuPDF = fast page-level extraction and better coordinates, native dependency risk and license/package audit needed
pdfplumber = richer layout/table context, heavier dependency stack and slower default path
```

Because no acceptable project dependency exists today, the recommended next task is:

```text
348N-R7AJ dependency audit for real PDF text-layer provider
```

## Text-layer detection policy

Text-layer detection must be conservative.

Recommended detection inputs:

```text
page_text_normalized_char_count
numeric_token_count
non_whitespace_char_count
printable_ratio
replacement_char_count
control_char_count
provider extraction warnings
```

Per-page text-layer statuses:

```text
TEXT_LAYER_PRESENT
TEXT_LAYER_EMPTY
TEXT_LAYER_GARBLED
NO_TEXT_LAYER
SCANNED_OR_IMAGE_ONLY
EXTRACTION_ERROR
```

A page should be considered text-empty when normalized text is empty or below a conservative minimum, for example:

```text
non_whitespace_char_count < 20
numeric_token_count = 0 for a numeric row target
printable_ratio below threshold
```

Document-level text-layer status should sample only needed pages first. It should not scan every page by default.

Scanned/image-only policy:

```text
do not emit trusted SourceTextEvidence
do not set agreement_status to VERIFIED
return fallback-needed status
route row to REVIEW_REQUIRED / fallback recommendation
do not automatically run OCR or MinerU
```

## Page selection / cost-control policy

Rows with explicit page numbers:

```text
validate page_number is positive and <= page_count if page_count is available cheaply
extract only that page
reuse page cache when available
do not call search_pages
do not scan full PDF
```

Rows without page numbers:

```text
search cached pages first
search provider pages only under max_pages / max_candidates / max_chars limits
stop when a unique high-confidence value + metric + period candidate is found
return ambiguity if multiple pages match
return UNVERIFIED / REVIEW_REQUIRED when cap is exhausted
```

Recommended cost controls:

```text
max_target_pages_per_pdf
max_candidate_pages_without_page_number
max_chars_per_page
max_total_chars_per_pdf
max_provider_errors_per_pdf
cache_first = true
full_document_scan_default = false
```

For dozens of PDFs, default work should scale with referenced pages plus capped candidate search, not with total pages or heavy parsing.

## Cache and manifest design

Recommended cache key:

```text
cache_key = sha256(
  source_file_sha256
  + provider_name
  + provider_version
  + extraction_config_hash
  + page_indexing_policy_version
)
```

Cache payloads:

```text
page_text by page number
page_text_sha256
page_char_count
text_layer_status
provider warnings/errors
provider metadata
page_count if already known
extracted_at
extraction_config_hash
```

Cache manifest shape:

```text
cache_schema_version
cache_key
source_document_id
source_pdf_path_hint
source_file_sha256
source_file_size_bytes
provider_name
provider_version
extraction_config_hash
page_indexing_policy_version
created_at
pages_cached
page_records:
  page_number
  page_text_sha256
  char_count
  text_layer_status
  extraction_status
errors
fallback_recommendations
mineru_run_count = 0
ocr_run_count = 0
llm_api_call_count = 0
```

Cache storage policy:

```text
cache output is generated artifact
cache output is not committed by default
cache lives under task-specific output/cache or temp cache only when a future task allows it
```

Invalidation triggers:

```text
source_file_sha256 changes
provider_name/version changes
extraction_config_hash changes
page indexing policy changes
normalization / anchor policy version changes
cache schema version changes
manual override changes
```

Stale cache prevention:

1. Always verify `source_file_sha256` before cache use.
2. Treat path-only cache hits as invalid.
3. Fail closed on manifest/source mismatch.
4. Preserve provider metadata and extraction config in cache records.

## Bridge integration design

Provider output should flow into the existing R7AH anchor path through a page-text adapter, not by changing downstream audit rules.

Design flow:

```text
PdfSourceIdentity
-> PdfTextLayerProvider.get_page_text(...) or search_pages(...)
-> PageTextResult(status, page_number, text, provider metadata)
-> lightweight bridge anchor matcher
-> accepted bounded snippet
-> SourceTextEvidence
-> existing select_source_text_for_row / classify_agreement_status
-> evidence_index / review_queue
```

R7AJ should not move the R7AH test helper into production directly. If production code is introduced later, minimal module boundaries should be:

```text
datefac_agent/pdf_text/provider_contract.py
datefac_agent/pdf_text/<chosen_provider>_adapter.py
datefac_agent/pdf_text/cache_manifest.py
datefac_agent/pdf_text/bridge_adapter.py
```

However, because no dependency is present today, R7AJ should first be dependency audit. A later implementation can be test-only or demo-only after the dependency decision.

## SourceTextEvidence mapping

Real text-layer accepted snippets should map to `SourceTextEvidence` similarly to R7AG/R7AH, but with production-safe kind and provider-qualified extraction method:

```text
source_text_id = deterministic id from source_file_sha256 + provider + page_number + locator + snippet_sha256
source_document_id = PdfSourceIdentity.source_document_id
page_number = provider/external page number after page-index policy conversion
locator = pdf_text_layer:p{page}:chars:{start}-{end}:anchor:{anchor_hash}
text_kind = snippet_text unless a future schema task adds a reviewed real-PDF-specific kind
text = exact bounded snippet only
text_sha256 = sha256(exact UTF-8 snippet)
char_count = len(exact snippet)
trusted_source = true only when source_file_sha256 is verified, provider status is OK, page binding is explicit/safe, and anchor match is unique
extraction_method = pdf_text_layer:<provider_name>:<provider_version>:config:<hash>
```

Do not use full page text as `SourceTextEvidence.text` by default. Full page text may be cached as generated artifact, but not serialized to evidence_index or review_queue.

## Agreement and confidence boundary

Real PDF text-layer snippets may drive `VERIFIED` only through the existing agreement checker and only when all conditions are met:

```text
source_file_sha256 verified
source_document_id matches evidence refs
page_number binding is explicit or uniquely selected under capped search
snippet is bounded and from provider status OK
value + metric + period proximity is unique
no duplicate ambiguity
unit / scale context is not contradictory
```

Even then:

```text
VERIFIED remains separate from evidence_level
evidence_level remains WEAK_EVIDENCE in this phase
no STRONG_EVIDENCE promotion
no automatic clean_data admission
no readiness gate opening
```

Must remain `UNVERIFIED` / `REVIEW_REQUIRED`:

```text
missing dependency
missing source file
source hash mismatch
encrypted/unreadable PDF
invalid page number
empty/garbled/no text layer
scanned/image-only PDF
value-only match
metric + period without value
value found but metric/period not nearby
duplicate ambiguous value
unit scale conflict
search cap exhausted
stale cache
provider error
```

Ambiguity should be represented explicitly, for example:

```text
AMBIGUOUS_DUPLICATE_VALUE
MULTIPLE_CANDIDATE_PAGES
PAGE_LABEL_MISMATCH
UNIT_SCALE_AMBIGUOUS
```

## Fallback policy

Fallback remains explicit, not automatic.

MinerU recommended when:

```text
text layer is missing/garbled but user explicitly approves heavier fallback
table layout is required to disambiguate repeated values
cached MinerU output already exists for the same source_file_sha256
high-value rows remain blocked after lightweight provider attempt
```

OCR recommended when:

```text
document/page is scanned image-only
text layer detection returns SCANNED_OR_IMAGE_ONLY
user explicitly approves OCR fallback
```

Manual review recommended when:

```text
dependency missing
source hash mismatch
page label/index uncertainty
duplicate ambiguity
unit scale conflict
fallback budget is not approved
```

Fallback-needed statuses should enter review_queue as compact metadata / reason codes. They must not create trusted `SourceTextEvidence`, `VERIFIED`, or clean/readiness changes.

## Implementation slice recommendation

Because no acceptable PDF text dependency exists in current dependency/config files, R7AI recommends:

```text
348N-R7AJ dependency audit for real PDF text-layer provider
```

R7AJ should evaluate:

```text
pypdf
PyMuPDF
pdfplumber
license/package risk
Windows install risk
optional dependency pattern
page-level text extraction capability
coordinate/snippet support
performance for target-page extraction
test strategy without committing real PDF artifacts
```

Only after R7AJ dependency audit passes should a real provider implementation task be created.

## Test plan for R7AJ

If R7AJ is dependency audit:

```text
inspect dependency options and project constraints
no code modification
no dependency installation
no real PDF run
recommend one provider or no-go
define QA gates for dependency addition
```

If a later task implements provider after dependency approval, tests should require:

```text
missing dependency returns MISSING_DEPENDENCY
missing file returns SOURCE_FILE_MISSING
source hash mismatch fails closed
invalid page number fails closed
target page extraction does not search all pages
no-page search respects candidate cap
empty text returns PAGE_TEXT_EMPTY / NO_TEXT_LAYER
scanned marker or generated image-only fixture returns fallback-needed
cache key includes source_file_sha256 + provider metadata + extraction_config_hash
stale cache rejected
accepted snippet maps to SourceTextEvidence
accepted snippet can drive VERIFIED
VERIFIED remains WEAK_EVIDENCE / not clean / not readiness
evidence_index metadata-only
review_queue compact-only
```

The later provider implementation should still avoid batch production and readiness.

## Out-of-scope list

R7AI did not and must not include:

```text
code implementation
test modification
fixture modification
datefac_agent modification
dependency addition
real PDF run
workbook rerun
run_pilot(...)
MinerU
OCR
LLM/VLM
PDF extraction pipeline
sidecar loader changes
lightweight bridge prototype changes
clean admission changes
evidence_level promotion changes
readiness gate changes
output/input/temp/data/legacy/config changes
```

## Risk review

Main risks before real-provider implementation:

1. Dependency creep: adding a parser without optional boundary or QA can turn lightweight evidence into a production parser path.
2. Page-index mismatch: PDF physical pages, printed labels, and workbook references can diverge.
3. Text-layer false confidence: extracted text may be garbled or lose table headers.
4. Scanned PDFs: empty text-layer extraction must not silently pass.
5. Stale cache: path-based cache can bind rows to the wrong PDF.
6. Full-text leakage: page text cache/snippets must not leak into evidence_index or review_queue.
7. Evidence promotion leakage: `VERIFIED` can be misread as `STRONG_EVIDENCE`, clean admission, or readiness.

Mitigations:

```text
dependency audit first
optional provider adapter
source_file_sha256 identity
cache manifest with provider/config hash
target-page-first extraction
capped candidate search
explicit fallback-needed statuses
snippet-only SourceTextEvidence
metadata-only delivery outputs
separate QA before implementation and before any production hook
```

## Validation outputs

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
  passed, no output
```

```text
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  passed, no output
```

```text
python -m py_compile tests/agent/source_text_sidecar_loader_348n.py tests/agent/test_source_text_sidecar_loader_348n.py tests/agent/test_agent_excel_intake_audit_348a.py
  passed, no output
```

```text
python -m py_compile tests/agent/lightweight_pdf_evidence_bridge_348n.py tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
  passed, no output
```

```text
pytest tests/agent -q
  ........................................................................ [ 40%]
  ........................................................................ [ 80%]
  ....................................                                     [100%]
  180 passed in 0.86s
```

```text
git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
```

```text
git diff --stat
  no output
```

```text
git diff --name-only
  no output
```

```text
git diff --check
  passed, no output
```

Final pre-stage guard after creating this report:

```text
git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
   A docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md

git diff --name-only
  docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md

git diff --check
  exit code 0
  warnings only: LF will be replaced by CRLF when Git touches the report
```

## Decision

```text
Decision = 348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN_VALID
```

R7AI design is complete. The first real PDF text-layer provider must be optional, identity-bound by `source_file_sha256`, page-targeted, cache-aware, and conservative. It should feed existing lightweight anchor matching with bounded page text/snippets only; it must not serialize full source text, default to MinerU/OCR, promote evidence level, clean-admit rows, or open readiness gates.

Because current dependency/config files do not include an acceptable PDF text-layer dependency, the next task should be dependency audit rather than implementation.

## Recommended next task

```text
348N-R7AJ dependency audit for real PDF text-layer provider
```

Recommended scope:

```text
design/review-only dependency audit
compare pypdf / PyMuPDF / pdfplumber
no dependency installation
no real PDF run
no code modification
recommend one optional provider path or no-go
define QA gates for any future dependency addition
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN_VALID
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 180 passed in 0.86s
files_modified（修改文件数）= 1，only this R7AI design report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/fixture/output/input/temp/data/legacy/config/dependencies/datefac_agent；仅创建允许的 R7AI design report
provider_design_result（provider设计结果）= PASS，real PDF text-layer provider boundary designed with target-page, capped-search, status, metadata, and identity contracts
dependency_strategy_result（依赖策略结果）= PASS，no current PDF text dependency found；recommend dependency audit before implementation
cost_control_result（成本控制结果）= PASS，target-page-first, cache-first, capped candidate search, no full-document default
cache_design_result（缓存设计结果）= PASS，source_file_sha256 + provider metadata + extraction_config_hash cache key and manifest designed
fallback_policy_result（fallback策略结果）= PASS，MinerU/OCR/manual review are explicit fallback only, not default
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= 348N-R7AJ dependency audit for real PDF text-layer provider
```
