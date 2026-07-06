# 348N-R7AG lightweight PDF evidence bridge design

## Task ID

```text
348N-R7AG lightweight PDF evidence bridge design
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AG changes the next integration direction from MinerU-first to lightweight PDF evidence bridging so PDF processing cost stays controlled while source_text and clean/readiness boundaries stay closed.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 2723251..39cd2c1
  Fast-forward
  created docs/codex_tasks/348N_R7AG_lightweight_pdf_evidence_bridge_design.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git branch --show-current:
  pivot/348-agent-foundation

git log --oneline -12:
  39cd2c1 docs: update handoff after R7AF QA
  eefd4ce docs: refresh plain-language progress after R7AF QA
  87c173b docs: sync progress after R7AF QA
  1376811 docs: add R7AG lightweight evidence bridge task
  2723251 docs: add R7AF QA review
  d3837dc docs: update handoff after R7AF
  1a48b96 docs: refresh plain-language progress after R7AF
  63f45d1 docs: sync progress after R7AF
  434d780 docs: add R7AF QA task
  3285ca6 test: add source text sidecar loader coverage
  84aa662 docs: update handoff after R7AE
  e204de1 docs: sync progress after R7AE
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
- `docs/codex_tasks/348N_R7AG_lightweight_pdf_evidence_bridge_design.md`
- `docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md`
- `docs/codex_tasks/348N_R7AF_QA_source_text_file_backed_sidecar_loader_review.md`
- `docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md`
- `docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md`

Read-only implementation / boundary files:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tests/agent/source_text_sidecar_loader_348n.py`
- `tests/agent/test_source_text_sidecar_loader_348n.py`
- `tests/agent/fixtures/source_text_sidecars/r7af_source_text_sidecar__basic_positive_negative__v1.json`

## Problem statement

DateFac needs a cheap, conservative way to connect existing extraction products back to the original PDF without making heavy PDF/table parsing the default. The bridge should use already available row hints (`source_pdf`, page number, metric name, period labels, numeric values, unit hints, workbook lineage) plus the original PDF text layer to produce bounded `SourceTextEvidence` snippets.

The intended flow is:

```text
existing extraction product
+ original PDF identity / text layer
+ row anchors: page_number, value, metric_name, period, unit hint
-> lightweight source_text snippet candidates
-> trusted SourceTextEvidence only when binding is safe
-> existing agreement checker / evidence_index / review_queue
```

The bridge is a cost-control and evidence-linking layer. It is not a production PDF parser, not a table reconstruction engine, and not a readiness gate.

## Why MinerU-first is not acceptable as default

MinerU-first is not acceptable as the default path because:

1. It turns every PDF into a heavy extraction job even when the row already has a page number and deterministic numeric anchors.
2. Batch users may provide dozens of PDFs; default heavy parsing would multiply time, compute, and human troubleshooting costs.
3. Most audit rows only need enough source text to validate a value, period, and metric neighborhood; full document reconstruction is overkill.
4. MinerU output can be valuable, but treating it as the entry point risks hiding cheaper text-layer evidence and making fallback cost look mandatory.
5. Heavy parsing can create false confidence if downstream systems treat generated table text as stronger than it is.

Required default:

```text
PDF text layer first when available
targeted page extraction first when page_number exists
candidate search only when page_number is missing
MinerU/OCR/manual review only as fallback
```

## Input assumptions

Minimum useful row-level fields:

```text
source_pdf_path or canonical source_document_id
source_file_sha256 when available
row_id / workbook sheet / row_index
metric_name
period labels
one or more extracted values
unit_hint / scale hint when available
optional explicit_evidence_ref / page_number
optional raw excerpt fields from Excel/JSON
```

When `page_number` exists:

```text
extract only that page by default
optionally include explicit range endpoints only if the evidence ref says a range
do not parse the full PDF
match value + metric keyword + period within that page
produce trusted SourceTextEvidence only if source_id/page/locator binding is deterministic
```

When `page_number` is missing:

```text
treat row as candidate-search mode
use value / metric_name / period as search hints
scan cached page text if available
otherwise extract pages lazily under caps
return UNVERIFIED / REVIEW_REQUIRED unless a unique high-confidence page and snippet are found
```

When metric, period, and values exist but no source_text exists:

```text
row remains evidence-linked only by workbook/PDF identity
agreement_status stays MISSING or UNVERIFIED through existing behavior
review_queue remains the safe default
```

Raw excerpt fields from Excel/JSON:

```text
can seed search terms or candidate snippets
must not be trusted source_text by default
must not be serialized as full source_text
must not drive VERIFIED unless re-bound to original PDF text layer or manual review
```

Hint-only fields:

```text
Excel raw excerpt
LLM/MinerU generated row text copied into workbook cells
sheet name
row label
metric alias
unit_hint
period label
filename/path text
prior extraction confidence
```

These fields help search. They are not themselves trusted evidence.

## Lightweight provider options

Provider options:

1. `pypdf`: pure Python and lightweight; useful for simple text-layer extraction but weaker layout fidelity.
2. `PyMuPDF`: fast targeted page text and optional coordinates; good candidate for later implementation if dependency policy allows it.
3. `pdfplumber`: richer text/table geometry but slower and heavier; useful when coordinate/table layout matters.
4. abstract provider boundary: safest first design because it avoids committing to a dependency or production parser.

R7AG recommendation:

```text
design an abstract page-text provider boundary first
do not add a dependency in R7AG
do not implement real PDF extraction in R7AG
let R7AH use test-only fake/in-memory page providers first
```

## Recommended provider boundary

Recommended interface shape, design-only:

```text
PdfTextProvider
  provider_name
  provider_version
  supports_text_layer_detection
  get_page_count(source_pdf)
  has_text_layer(source_pdf, page_number | sample_pages)
  extract_page_text(source_pdf, page_number)
  extract_candidate_pages(source_pdf, anchors, limits)
```

Provider output should be page-scoped:

```text
source_document_id
source_file_sha256
page_number
page_text or bounded page_text metadata
page_text_sha256
char_count
text_layer_status
provider_name
provider_version
errors
```

The provider must be lazy and page-bound. It should not extract all pages when the row already has a page number.

## Page text extraction strategy

For rows with explicit page provenance:

1. Validate PDF identity by path plus `source_file_sha256` when available.
2. Convert external page numbers to the provider's internal indexing deterministically.
3. Extract only the required page.
4. Detect text-layer availability by normalized character count, numeric-token count, and non-control text ratio.
5. Run anchor matching on that page.
6. Create a bounded snippet around the winning anchor, not full page text by default.
7. Hash the exact snippet text and record `char_count = len(snippet)`.

If page extraction fails:

```text
source_text_quality = EXTRACTION_ERROR
agreement_status remains UNVERIFIED
row stays REVIEW_REQUIRED
error is reported in cache/manifest diagnostics
```

If the page has no usable text layer:

```text
source_text_quality = NO_TEXT_LAYER or SCANNED_IMAGE
do not emit trusted SourceTextEvidence
route to OCR/MinerU/manual review fallback policy
```

## No-page-number fallback strategy

No-page-number mode should be explicitly weaker and capped.

Recommended search stages:

1. Check page-text cache for the same `source_file_sha256`.
2. If cache exists, score candidate pages using normalized values, metric keywords, and periods.
3. If cache does not exist, lazily extract pages under configurable limits, for example first candidate sections or a small page cap.
4. Stop early only when one page has a clear unique high-confidence anchor set.
5. If multiple pages tie or the match is value-only, keep row UNVERIFIED and REVIEW_REQUIRED.

No-page-number mode must not silently become full-document parsing. It is still lightweight text-layer search with cost caps.

## Evidence anchor matching strategy

Anchor matching should use three independent anchor families:

```text
value anchors = normalized row numeric values
metric anchors = metric_name tokens / approved aliases
period anchors = year, quarter, half-year, trailing period labels
```

Recommended decision rules:

1. `value + metric + period` in a local window can produce a trusted snippet candidate.
2. `value + metric` without period may be a lower-confidence snippet only if the row has a single period and the page is explicit.
3. `value only` must not produce trusted source_text because common numbers repeat.
4. `metric only` or `period only` must not produce trusted source_text.
5. page-level matches without local proximity remain diagnostic hints, not trusted evidence.

The bridge should emit trusted `SourceTextEvidence` only when it can identify the exact local snippet used for deterministic agreement. Candidate diagnostics can exist in an internal cache/manifest, but they must not be passed as trusted source_text.

## Numeric normalization strategy

Normalize row values and PDF text tokens before matching:

```text
commas: 1,234.56 -> 1234.56
percentages: 12.3% -> 0.123 or percent-tagged Decimal, but compare only when row unit is compatible
negative signs: -123, −123, –123 -> -123
parentheses negatives: (123) -> -123
Chinese units: 万, 亿, 千, 百万, 十亿 -> scale-aware candidate values
English units: thousand, million, billion -> scale-aware candidate values
currency symbols: RMB, CNY, HK$, $, 元 -> unit/currency metadata
dash / N/A values -> non-numeric
```

Important safety rule:

```text
scale conversion is allowed only when the row unit_hint and local PDF unit token are compatible
ambiguous unit scale keeps the row REVIEW_REQUIRED
```

The existing agreement checker already does deterministic numeric matching and multiplicity accounting. The bridge should strengthen upstream snippet selection without changing evidence promotion rules.

## Keyword / period proximity strategy

Metric keyword proximity:

```text
tokenize metric_name and approved aliases
normalize Chinese/English punctuation and whitespace
prefer same line, same table row, or ±80 character window around the numeric value
require at least one strong metric token for common financial rows
```

Period proximity:

```text
normalize 2023, FY2023, 2023年, 2023年度, 23年
normalize Q1/Q2/Q3/Q4, H1/H2, 半年度, 年度
prefer same line/header neighborhood as value
support inherited table header only when provider supplies reliable line/block positions
```

If provider only returns plain text with no reliable line/block information, use a conservative character window and mark quality lower.

## Duplicate-number handling

Duplicate numeric values are a primary false-VERIFIED risk.

Recommended handling:

1. Count all normalized occurrences of row values on the candidate page.
2. Count occurrences inside local metric/period windows.
3. If the value appears multiple times but only one local window has metric + period proximity, use that window.
4. If multiple windows remain plausible, mark the match ambiguous.
5. Ambiguous duplicate matches must not be emitted as trusted source_text.

The bridge should preserve the R7Z/R7AF posture:

```text
multiplicity-aware matching first
ambiguous repeated values -> UNVERIFIED / REVIEW_REQUIRED
do not let common values become automatic VERIFIED
```

## SourceTextEvidence mapping

Recommended mapping for trusted lightweight snippets:

```text
source_text_id = deterministic id from source_file_sha256 + page_number + locator + snippet hash
source_document_id = current runner source_id until a future canonical PDF hash identity change is separately designed
page_number = explicit or selected candidate page number
text = exact bounded snippet from PDF text layer
locator = deterministic page/snippet locator
text_kind = snippet_text by default
trusted_source = true only for original PDF text-layer or manually reviewed source text
extraction_method = pdf_text_layer_lightweight:v1 or equivalent provider-qualified value
text_sha256 = sha256(exact UTF-8 snippet text)
char_count = len(exact snippet text)
```

Locator format should be deterministic and page-bound:

```text
pdf_text_layer:p{page}:chars:{start}-{end}:anchor:{anchor_hash}
```

If provider supplies reliable coordinates, a future variant may use:

```text
pdf_text_layer:p{page}:bbox:{x0},{y0},{x1},{y1}:anchor:{anchor_hash}
```

Full page text should not be the default `SourceTextEvidence.text`. Use snippets unless a separate QA approves page-level text serialization behavior.

## Provider / quality metadata design

Current `SourceTextEvidence` does not include `source_text_provider` or `source_text_quality` fields. To avoid schema churn, R7AG recommends representing provider/quality metadata outside delivery serializers first:

```text
bridge candidate manifest
sidecar generation manifest
extraction_method structured string
cache manifest page records
```

Suggested metadata values:

```text
source_text_provider = fake_page_text_provider | pypdf | pymupdf | pdfplumber | manual_review | mineru_cached | ocr_cached
source_text_quality = TEXT_LAYER_TARGET_PAGE | TEXT_LAYER_CANDIDATE_PAGE | TEXT_LAYER_SNIPPET_CONFIRMED | VALUE_ONLY_AMBIGUOUS | NO_TEXT_LAYER | SCANNED_IMAGE | EXTRACTION_ERROR | MANUAL_REVIEWED
```

Existing outputs should remain safe:

```text
evidence_index = metadata/hash/count/status only
review_queue = compact fields only
full source_text absent from serialized outputs
```

If future work adds provider/quality fields directly to `SourceTextEvidence` or delivery outputs, it needs separate schema review and QA.

## Confidence and boundary policy

The bridge must not redefine DateFac trust boundaries.

Allowed confidence interpretation:

```text
trusted PDF snippet + source_id/page/locator binding + deterministic numeric match -> agreement_status can be VERIFIED through existing checker
trusted PDF snippet + deterministic numeric mismatch -> DISAGREED through existing checker
missing / mismatch / ambiguous / untrusted / empty -> UNVERIFIED or existing conservative mismatch status
```

Forbidden promotions:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean_data admission
VERIFIED does not imply readiness
value-only match does not create trusted source_text
Excel raw excerpt does not create trusted source_text
```

Cases that should remain REVIEW_REQUIRED:

```text
no usable text layer
no page and no unique candidate page
duplicate values with ambiguous local context
unit scale conflict or missing scale evidence
keyword found but value missing
value found but keyword/period not nearby
source_file_sha256 mismatch
cache manifest invalid or stale
provider error
```

## Scanned PDF policy

Scanned/image-only PDFs must fail safe:

```text
detect empty/near-empty page text or very low text quality
record text_layer_status = NO_TEXT_LAYER or SCANNED_IMAGE
do not emit trusted SourceTextEvidence
do not set VERIFIED from image-only content
route to OCR / MinerU / manual review fallback decision
```

The bridge should make scanned PDFs visible as an audit limitation, not hide them behind successful-looking empty text extraction.

## MinerU fallback policy

MinerU should be recommended only when lightweight evidence bridging is insufficient:

```text
PDF is scanned/image-only and OCR/MinerU is explicitly allowed
table layout is required to disambiguate repeated values
text layer is garbled or missing important table structure
candidate search cannot produce a unique snippet
high-value rows remain blocked after lightweight matching
cached MinerU output for the same source_file_sha256 already exists
user explicitly opts into heavier fallback
```

MinerU should be forbidden as default when:

```text
page_number exists and text layer is usable
cached page text/snippets already satisfy the evidence requirement
batch contains many PDFs and no explicit fallback budget was approved
task boundary says no MinerU/OCR/LLM/VLM
```

Fallback should be represented as a cost-control policy:

```text
default = lightweight text-layer only
fallback = manual approval or explicit run mode
cached heavy outputs = reuse before rerun
external call / heavy parser counters = reported separately
```

## Caching / manifest design

Use `source_file_sha256` as the primary cache key. Path and filename are hints, not identity.

Recommended cache manifest fields:

```text
cache_schema_version
source_file_sha256
source_pdf_path_hint
source_file_size
page_count
provider_name
provider_version
normalization_version
bridge_policy_version
created_at
pages_extracted
page_text_sha256_by_page
page_char_count_by_page
snippet_records
sidecar_records
errors
fallback_recommendations
mineru_run_count
ocr_run_count
llm_api_call_count
```

Cache payloads:

```text
page text for extracted pages only
snippet text for selected anchors
snippet sha256 / char_count
provider and quality metadata
candidate diagnostics
sidecar generation manifest
```

Invalidation triggers:

```text
source_file_sha256 changes
provider version changes
normalization version changes
bridge policy version changes
page indexing policy changes
cache schema version changes
manual review override changes
```

## Cost-control workflow

Recommended runtime workflow:

1. Group rows by source PDF identity.
2. Hash each source PDF once.
3. For rows with page numbers, extract unique pages only.
4. Reuse page text cache for repeated rows on the same page.
5. For rows without page numbers, search cache first and extract additional pages only under a cap.
6. Emit trusted snippets only for unique high-confidence local matches.
7. Send ambiguous/missing cases to review queue or fallback recommendation.
8. Never run MinerU/OCR/LLM/VLM without explicit fallback mode or cached artifacts.

Cost counters should be explicit:

```text
pdf_text_pages_extracted_count
pdf_text_cache_hit_count
pdf_text_cache_miss_count
candidate_page_search_count
mineru_run_count = 0 by default
ocr_run_count = 0 by default
llm_api_call_count = 0 by default
```

This supports dozens of PDFs because the default cost is proportional to referenced pages and capped candidate search, not full heavy parsing.

## Risks and failure modes

Key risks:

1. Value-only matches could incorrectly become VERIFIED if emitted as trusted snippets.
2. Repeated financial values can appear in multiple rows, notes, and summary tables.
3. Unit scale mismatches (`万` vs `亿`, percent vs ratio) can produce false numeric agreement.
4. Plain text extraction may lose table headers, making period association ambiguous.
5. PDF page labels may differ from physical page indices.
6. Cached page text could be stale if keyed by path instead of `source_file_sha256`.
7. Raw Excel excerpts may be mistaken for original PDF text.
8. Provider differences can change tokenization and snippet offsets.

Mitigations:

```text
source_file_sha256 identity
provider/versioned cache manifest
metric + period + value proximity
multiplicity-aware duplicate handling
snippet-only trusted SourceTextEvidence
raw excerpts as hints only
fail closed to UNVERIFIED / REVIEW_REQUIRED
separate QA before schema/output promotion
```

## R7AH implementation recommendation

Recommended next task:

```text
348N-R7AH lightweight PDF evidence bridge test-only prototype
```

R7AH should implement first:

```text
test-only fake/in-memory page-text provider
anchor matching helper for value + metric + period proximity
numeric normalization fixture cases
duplicate-number ambiguity cases
snippet + locator generation
SourceTextEvidence mapping from trusted fake PDF page text
metadata-only evidence_index validation
compact review_queue validation
boundary tests proving VERIFIED is non-promotional
```

R7AH should not implement first:

```text
real PDF parser
new dependency
production runner hook
batch PDF platform
MinerU/OCR/LLM/VLM fallback execution
clean admission changes
readiness changes
```

Recommended R7AH execution mode:

```text
implementation + tests
test-only or demo-only
no real PDF input
no output/input/temp/data modifications
```

## Out-of-scope list

R7AG did not and should not include:

```text
code implementation
test modification
fixture modification
real PDF processing
workbook rerun
run_pilot(...)
MinerU
OCR
LLM/VLM
PDF extraction code
new dependencies
production PDF parser
sidecar loader behavior changes
clean admission changes
evidence_level promotion changes
readiness gate changes
output/input/temp/data/legacy/config changes
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
pytest tests/agent -q
  ........................................................................ [ 44%]
  ........................................................................ [ 88%]
  ..................                                                       [100%]
  162 passed in 0.94s
```

```text
git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
   A docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
```

```text
git diff --stat
  ..._R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md | 781 +++++++++++++++++++++
  1 file changed, 781 insertions(+)
```

```text
git diff --name-only
  docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
```

```text
git diff --check
  exit code 0
  warnings only: LF will be replaced by CRLF when Git touches the report
```

## Decision

```text
Decision = 348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN_VALID
```

R7AG design is complete. The recommended next direction is a lightweight PDF text-layer evidence bridge that extracts only needed pages when page numbers exist, uses capped candidate-page search when they do not, requires value + metric + period proximity for trusted snippets, treats raw extracted excerpts as hints only, maps bounded snippets into `SourceTextEvidence`, records provider/quality metadata outside delivery serializers first, uses `source_file_sha256` for caching, and keeps MinerU/OCR/manual review as explicit fallback rather than default.

Boundary decision:

```text
MinerU is not the default path
full source_text is not serialized by default
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean_data admission
VERIFIED does not imply readiness
readiness gates remain CLOSED
```

## Recommended next task

```text
348N-R7AH lightweight PDF evidence bridge test-only prototype
```

Recommended scope:

```text
test-only fake/in-memory page-text provider
no real PDFs
no new dependency
no MinerU/OCR/LLM/VLM
anchor matching and snippet mapping tests
metadata-only evidence_index validation
compact review_queue validation
boundary tests for non-promotional VERIFIED
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7AG lightweight PDF evidence bridge design completed and valid
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 162 passed in 0.94s
files_modified（修改文件数）= 1，only this R7AG design report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/fixture/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7AG design report
mineru_default_policy（MinerU 默认策略）= NOT_DEFAULT，MinerU/OCR/manual review only as explicit fallback or cached reuse
lightweight_bridge_design_result（轻量桥设计结果）= PASS，targeted page text + capped candidate search + snippet SourceTextEvidence design completed
evidence_anchor_design_result（证据锚点设计结果）= PASS，value + metric + period proximity with duplicate-number and unit-scale safeguards
cost_control_result（成本控制结果）= PASS，source_file_sha256 cache, unique-page extraction, cache-first search, and heavy fallback counters designed
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= 348N-R7AH lightweight PDF evidence bridge test-only prototype
```
