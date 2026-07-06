# 348N-R7AH-QA lightweight PDF evidence bridge prototype review

## Task ID

```text
348N-R7AH-QA lightweight PDF evidence bridge prototype review
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AH-QA reviews the first lightweight evidence bridge prototype and confirms it remains test-only, synthetic-only, no-heavy-parser, metadata-only, and boundary-safe.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 26e2717..0bc70a9
  Fast-forward
  created docs/codex_tasks/348N_R7AH_QA_lightweight_pdf_evidence_bridge_prototype_review.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git branch --show-current:
  pivot/348-agent-foundation

git log --oneline -12:
  0bc70a9 docs: update handoff after R7AH
  40312bd docs: refresh plain-language progress after R7AH
  91a596e docs: sync progress after R7AH
  64ad129 docs: add R7AH QA task
  26e2717 test: add lightweight PDF evidence bridge prototype
  6252c84 docs: update handoff after R7AG
  faf5dc8 docs: refresh plain-language progress after R7AG
  34e85c6 docs: sync progress after R7AG
  9b9d1fb docs: add R7AH lightweight bridge prototype task
  ea68e33 docs: add R7AG lightweight evidence bridge design
  39cd2c1 docs: update handoff after R7AF QA
  eefd4ce docs: refresh plain-language progress after R7AF QA
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
- `docs/codex_tasks/348N_R7AH_QA_lightweight_pdf_evidence_bridge_prototype_review.md`
- `docs/codex_tasks/348N_R7AH_lightweight_pdf_evidence_bridge_test_only_prototype.md`
- `docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md`
- `docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md`

R7AH implementation:

- `tests/agent/lightweight_pdf_evidence_bridge_348n.py`
- `tests/agent/test_lightweight_pdf_evidence_bridge_348n.py`
- commit `26e2717 test: add lightweight PDF evidence bridge prototype`

Read-only boundary files:

- `tests/agent/source_text_sidecar_loader_348n.py`
- `tests/agent/test_source_text_sidecar_loader_348n.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/review/clean_candidate_policy.py`

## Prototype placement review

QA result: **VALID**.

R7AH was limited to the allowed test helper/test files:

```text
tests/agent/lightweight_pdf_evidence_bridge_348n.py
tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
```

`git diff-tree --no-commit-id --name-only -r 26e2717` lists only those two files.

The helper is explicitly test-only by placement and module docstring. No production file under `datefac_agent/` was modified. Search over `datefac_agent/` and `tools/` found no imports or references to:

```text
lightweight_pdf_evidence_bridge_348n
build_lightweight_pdf_source_text_evidence
SyntheticPageTextProvider
LightweightRowHint
```

No runner, CLI, `run_pilot(...)`, workbook rerun, or production hook was introduced.

## Synthetic provider review

QA result: **VALID**.

The prototype uses only an in-memory synthetic provider:

```text
SyntheticPageTextProvider(
  pages_by_source: dict[str, dict[int, str | None]]
)
```

Provider behavior is bounded and inspectable:

```text
get_page_text(source_document_id, page_number) -> target-page lookup
search_pages(source_document_id, max_pages) -> sorted synthetic pages capped by max_pages
requested_pages / searched_sources record what was touched
```

No real PDF path is accepted or opened. No file IO, subprocess, network call, OCR, MinerU, or parser dependency exists in the helper.

## Anchor matching review

QA result: **VALID**.

Accepted matching requires all three local anchors:

```text
value anchor
metric_name keyword anchor
period anchor
```

The matching path:

1. Normalizes the row value with a narrow test-only numeric normalizer.
2. Extracts numeric occurrences from synthetic page text.
3. Builds a bounded snippet around each matching value.
4. Requires metric tokens and period tokens inside the snippet.
5. Emits exactly one trusted match only when one unambiguous candidate remains.

Page behavior is correct:

```text
page_number present -> only get_page_text(target page), no candidate search
page_number missing -> search_pages(..., candidate_page_limit), capped candidate search
```

Test coverage confirms target-page lookup and capped candidate search through provider call logs.

## Conservative failure review

QA result: **VALID**.

R7AH covers conservative failure paths:

```text
value-only -> NO_KEYWORD_PROXIMITY, no SourceTextEvidence
metric + period but no value -> NO_VALUE_MATCH, no SourceTextEvidence
wrong-page value -> NO_VALUE_MATCH on target page only, no search fallback
duplicate value ambiguous -> AMBIGUOUS_DUPLICATE_VALUE, no SourceTextEvidence
missing page text -> PAGE_TEXT_MISSING, no SourceTextEvidence
scanned/image-only marker -> SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED, fallback_needed=true, no SourceTextEvidence
```

Statuses are deterministic and explainable.

## SourceTextEvidence mapping review

QA result: **VALID**.

Accepted synthetic matches map into `SourceTextEvidence` with:

```text
source_text_id = r7ah:<source_file_sha256-prefix>:p<page>:<start>-<end>:<snippet_hash-prefix>
source_document_id = row_hint.source_document_id
page_number = matched page
locator = page:<n>:text_anchor:<start>-<end>
text_kind = lightweight_page_text_snippet
text = bounded snippet
text_sha256 = sha256(exact UTF-8 snippet text)
char_count = len(exact snippet text)
trusted_source = true
extraction_method = lightweight_pdf_text_bridge_test_fixture
```

The tests assert deterministic/stable ID prefix, deterministic locator, exact snippet text, hash, char count, trusted flag, and extraction method.

Compatibility note: `text_kind = "lightweight_page_text_snippet"` is test-task-required and works with the current dataclass at runtime. It is not currently part of the `SourceTextKind` literal list in `datefac_agent/schemas/audit_models.py`; before any production/schema promotion, R7AI or a later schema task should either add a reviewed literal or normalize this value to an existing production-safe kind.

## No-heavy-parser review

QA result: **VALID**.

Static import review found no heavy parser imports in the helper or tests:

```text
fitz
PyMuPDF / pymupdf
pdfplumber
pypdf
MinerU / mineru
OCR / ocr
LLM / llm
VLM / vlm
openai
requests
subprocess
```

AST import inventory:

```text
tests/agent/lightweight_pdf_evidence_bridge_348n.py:
  __future__
  collections.abc
  dataclasses
  datefac_agent.schemas.audit_models
  decimal
  hashlib
  re

tests/agent/test_lightweight_pdf_evidence_bridge_348n.py:
  __future__
  ast
  datefac_agent.delivery.evidence_index_writer
  datefac_agent.review.review_queue_builder
  datefac_agent.schemas.audit_models
  hashlib
  json
  pathlib
  pytest
  tests.agent
  tests.agent.lightweight_pdf_evidence_bridge_348n
  typing
```

The only MinerU/OCR/LLM strings in the test file are zero-counter assertions and forbidden-import assertions. No new dependency file was modified.

## Evidence index serialization review

QA result: **VALID**.

R7AH validates evidence index output with a pytest `tmp_path`, not project `output/`.

Assertions confirm:

```text
full snippet text absent from raw JSON
agreement_status = VERIFIED
source_text_status = AVAILABLE_USED
source_text_id present
source_text_source_id present
source_text_page_number present
source_text_locator present
source_text_kind present
source_text_sha256 present
source_text_char_count present
source_text_used_for_agreement = true
source_text_unavailable_reason = null
```

Read-only review confirms `datefac_agent/delivery/evidence_index_writer.py` writes metadata/hash/count/status fields and does not serialize `source_text.text`.

## Review queue serialization review

QA result: **VALID**.

R7AH validates review queue rows in memory through `build_review_queue_rows(...)`.

Assertions confirm:

```text
full snippet text absent from serialized in-memory rows
agreement_status = VERIFIED
source_text_status = AVAILABLE_USED
source_text_page_number = "3"
source_text_locator = deterministic locator
source_text_unavailable_reason = ""
```

Read-only review confirms `datefac_agent/review/review_queue_builder.py` writes compact source_text fields and does not serialize `source_text.text`.

## Boundary policy review

QA result: **VALID**.

R7AH proves accepted snippet evidence can drive the existing agreement checker to:

```text
agreement_status = VERIFIED
source_text_selection.status = AVAILABLE_USED
source_text_selection.used_for_agreement = true
evidence_level = WEAK_EVIDENCE
```

It also proves `MARKET_REFERENCE_ROW` remains:

```text
clean_candidate_type = REVIEW_REQUIRED
```

Read-only review confirms:

1. `classify_evidence_level(...)` still treats explicit/page provenance as `WEAK_EVIDENCE`, not `STRONG_EVIDENCE`.
2. `classify_clean_candidate(...)` does not use `agreement_status` as an automatic clean admission switch.
3. `MARKET_REFERENCE_ROW` still returns `REVIEW_REQUIRED`.

Therefore:

```text
VERIFIED -> not STRONG_EVIDENCE
VERIFIED -> not clean_data admission
VERIFIED -> not MARKET_REFERENCE_ROW acceptance
```

## Readiness gates review

QA result: **VALID / CLOSED**.

R7AH boundary tests keep readiness closed with a synthetic manifest stub:

```text
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

R7AH did not add any runner or manifest production hook. It did not run or add real PDFs, workbook reruns, `run_pilot(...)`, MinerU, OCR, LLM, VLM, or PDF extraction.

## Test review

QA result: **VALID**.

R7AH added 18 focused tests covering:

```text
page-number positive match
no-page capped candidate search
accepted evidence drives VERIFIED through existing checker
evidence_index metadata-only and no full snippet text
review_queue compact-only and no full snippet text
value-only conservative failure
metric + period but no value conservative failure
wrong-page conservative failure
duplicate ambiguous conservative failure
missing page text conservative failure
scanned marker fallback-needed behavior
common synthetic numeric normalization examples
VERIFIED boundary checks
no heavy parser / production hook imports
```

Existing R7AF sidecar tests still pass as part of the full agent suite.

## Compatibility risk review

No blocking compatibility issue found for the test-only prototype.

Residual risks before a real PDF text-layer provider:

1. `text_kind = "lightweight_page_text_snippet"` needs explicit schema review before production promotion.
2. The numeric normalizer is intentionally narrow and synthetic-only; real PDFs need a separate unit/scale policy, especially for Chinese units, percentages, negatives, and table-level units.
3. The token/proximity logic is line/snippet based; real PDF text extraction can scramble table headers or row order.
4. Candidate search currently sorts synthetic pages and applies a simple cap; real provider design must define physical page labels, page-index conversion, and cache behavior.
5. Source text is synthetic provider text, not production PDF extraction; R7AI must stay design-first before real PDF integration.

Risk level: **acceptable for R7AH-QA**.

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
  180 passed in 0.88s
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
   A docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md

git diff --name-only
  docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md

git diff --check
  exit code 0
  warnings only: LF will be replaced by CRLF when Git touches the report
```

## Decision

```text
Decision = 348N_R7AH_QA_CONFIRMED_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_VALID
```

R7AH-QA confirms the lightweight PDF evidence bridge prototype is valid within test-only scope. It is isolated under `tests/agent/`, uses synthetic page text only, introduces no real PDF parser, no PyMuPDF/pdfplumber/pypdf dependency, no MinerU/OCR/LLM/VLM path, and no production hook. Matching is conservative, `SourceTextEvidence` mapping is deterministic, evidence_index and review_queue remain metadata/compact-only, full snippet text is not serialized, and `VERIFIED` does not promote to `STRONG_EVIDENCE`, clean admission, or readiness.

## Recommended next task

```text
348N-R7AI real PDF text-layer provider design
```

Recommended scope:

```text
design-only first
provider boundary and dependency policy
real PDF text-layer cost controls
page-index/page-label strategy
cache manifest strategy
no production readiness
no MinerU-first default
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AH_QA_CONFIRMED_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_VALID
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 180 passed in 0.88s
files_modified（修改文件数）= 1，only this R7AH-QA report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/fixture/output/input/temp/data/legacy/config/dependencies/datefac_agent；仅创建允许的 R7AH-QA report
lightweight_bridge_prototype_result（轻量桥原型结果）= PASS，prototype remains test-only and synthetic-only under tests/agent/
anchor_matching_result（锚点匹配结果）= PASS，requires value + metric + period proximity and fails conservatively for unsafe cases
source_text_mapping_result（source_text映射结果）= PASS，deterministic source_text_id/locator/hash/char_count from accepted snippet
no_heavy_parser_result（无重型解析器结果）= PASS，无真实 PDF parser、无 PyMuPDF/pdfplumber/pypdf、无 MinerU/OCR/LLM/VLM、无新增依赖
evidence_index_validation_result（证据索引验证结果）= PASS，metadata/hash/count/status only，no full snippet text
review_queue_validation_result（复核队列验证结果）= PASS，compact fields only，no full snippet text
qa_result（QA结果）= VALID
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= 348N-R7AI real PDF text-layer provider design
```
