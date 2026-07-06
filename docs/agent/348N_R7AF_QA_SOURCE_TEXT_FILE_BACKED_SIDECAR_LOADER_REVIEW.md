# 348N-R7AF-QA source_text file-backed sidecar loader review

## Task ID

```text
348N-R7AF-QA source_text file-backed sidecar loader review
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AF-QA reviews the first file-backed source_text sidecar loader and must confirm it remains test-only, fail-closed, metadata-only, and boundary-safe.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 3285ca6..d3837dc
  Fast-forward
  created docs/codex_tasks/348N_R7AF_QA_source_text_file_backed_sidecar_loader_review.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  d3837dc docs: update handoff after R7AF
  1a48b96 docs: refresh plain-language progress after R7AF
  63f45d1 docs: sync progress after R7AF
  434d780 docs: add R7AF QA task
  3285ca6 test: add source text sidecar loader coverage
  84aa662 docs: update handoff after R7AE
  e204de1 docs: refresh plain-language progress after R7AE
  a00ad55 docs: sync progress after R7AE
  fe724ba docs: add R7AF source text loader implementation task
  d24abf9 docs: add R7AE source text loader design
  5972291 docs: update handoff after R7AD QA
  7597aaf docs: refresh plain-language progress after R7AD QA
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
- `docs/codex_tasks/348N_R7AF_QA_source_text_file_backed_sidecar_loader_review.md`
- `docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md`
- `docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md`
- `docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md`
- `docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md`

R7AF implementation:

- `tests/agent/source_text_sidecar_loader_348n.py`
- `tests/agent/test_source_text_sidecar_loader_348n.py`
- `tests/agent/fixtures/source_text_sidecars/r7af_source_text_sidecar__basic_positive_negative__v1.json`
- commit `3285ca6 test: add source text sidecar loader coverage`

Read-only boundary files:

- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/output_schema_guardrails.py`

## Loader placement review

QA result: **VALID**.

R7AF modified exactly the allowed test/helper/fixture files:

```text
tests/agent/source_text_sidecar_loader_348n.py
tests/agent/test_source_text_sidecar_loader_348n.py
tests/agent/fixtures/source_text_sidecars/r7af_source_text_sidecar__basic_positive_negative__v1.json
```

The loader lives under `tests/agent/` and is described as a test-only loader. Search/review found loader imports and calls only in:

```text
tests/agent/source_text_sidecar_loader_348n.py
tests/agent/test_source_text_sidecar_loader_348n.py
```

There is no hook into:

```text
datefac_agent/
tools/run_agent_excel_intake_audit_348a.py
run_pilot(...)
CLI args
runner defaults
production paths
```

R7AF did not modify production code.

## Sidecar schema review

QA result: **VALID**.

R7AF implements JSON object v1, not JSONL.

Top-level key contract is exact:

```text
schema_version
fixture_scope
records
```

Record key contract is exact:

```text
source_text_id
source_document_id
page_number
locator
text_kind
text
text_sha256
char_count
trusted_source
extraction_method
```

Required validations are present:

```text
schema_version == 1
fixture_scope == test_only
records is list
page_number is positive integer
text is non-empty
trusted_source is true
text_sha256 equals sha256(exact UTF-8 text)
char_count equals len(text)
```

The committed fixture matches the required shape:

```text
schema_version = 1
fixture_scope = test_only
source_text_id = st-valid-001
source_document_id = source-pdf-001
page_number = 3
locator = p3:table:row:revenue
text_kind = table_row
text = Revenue 2023 123.45
text_sha256 = ce95918070fa9b87529f4b857dd8adfa577c1882836167f58d2b06152c241812
char_count = 19
trusted_source = true
extraction_method = fixture_manual
```

Compatibility note: `text_kind = "table_row"` is accepted by the test-only loader and maps into the current `SourceTextEvidence` dataclass. Current runtime selection treats any non-`page_text` value as locator-bound, which is conservative for this test-only fixture. If this loader is ever promoted to production code, the project should decide whether to normalize `table_row` to the production literal `table_row_text` first.

## Fail-closed review

QA result: **VALID**.

R7AF rejects the whole sidecar file with `SourceTextSidecarValidationError` for:

```text
invalid JSON
non-object top-level JSON
unknown top-level keys
schema_version != 1
fixture_scope != test_only
records not list
unknown record keys
missing required record keys
duplicate source_text_id
source_text_id empty
source_document_id empty
page_number non-int / <= 0
locator empty
text_kind empty / unsupported
text empty
text_sha256 mismatch
char_count mismatch
trusted_source = false
extraction_method empty
```

R7AF uses one list-comprehension over `_validate_record(...)`; if any record fails, `load_source_text_sidecar_fixture(...)` raises and returns no records to the caller. Tests explicitly cover duplicate IDs and a later invalid second record, which validates no partial list is returned for those invalid files.

Residual note: the loader does not separately test `page_number` missing, `char_count` missing, or `text_sha256` missing by field name; missing required record key coverage removes `text` and exercises the exact-key missing-key path. This is acceptable for R7AF-QA because `_validate_exact_keys(...)` is shared for all required record keys.

## Positive integration review

QA result: **VALID**.

R7AF positive tests confirm:

```text
valid JSON sidecar loads exactly one SourceTextEvidence
loaded fields preserve id/source/page/locator/kind/text/hash/char_count/trust/extraction_method
valid fixture drives source_text selection to AVAILABLE_USED
valid fixture drives agreement_status to VERIFIED
trusted numeric mismatch can produce DISAGREED
```

The integration path remains lower-level and test-only:

```text
load_source_text_sidecar_fixture(...)
audit_evidence_presence(...)
build_row_audit_result(..., source_text_index=records)
write_evidence_index(...) to tempfile
build_review_queue_rows(...) in memory
```

No workbook rerun is used.

## Negative behavior review

QA result: **VALID**.

R7AF keeps source_text selection conservative for structurally valid sidecars that do not bind to row provenance:

```text
missing source_text_index -> UNVERIFIED / MISSING / not used
source_id mismatch -> UNVERIFIED / SOURCE_ID_MISMATCH / not used
page mismatch -> UNVERIFIED / PAGE_NUMBER_MISMATCH / not used
locator mismatch -> UNVERIFIED / LOCATOR_MISMATCH / not used
```

Untrusted file-backed records fail closed at loader time rather than becoming in-memory `SourceTextEvidence` records. This matches the R7AF task rule that `trusted_source=false` file records should be rejected entirely.

## Evidence index validation review

QA result: **VALID**.

R7AF validates evidence index output using `tempfile.TemporaryDirectory()`. No project `output/` artifact is created.

Validated metadata includes:

```text
agreement_status
source_text_status
source_text_id
source_text_source_id
source_text_page_number
source_text_locator
source_text_kind
source_text_sha256
source_text_char_count
source_text_used_for_agreement
source_text_unavailable_reason
```

The test asserts:

```text
SOURCE_TEXT not in raw_payload
source_text_status = AVAILABLE_USED
source_text_used_for_agreement = true
source_text_unavailable_reason = null
```

Evidence index remains metadata/hash/count/status only.

## Review queue validation review

QA result: **VALID**.

R7AF validates review queue output in memory via `build_review_queue_rows(...)`; it does not write a review queue file.

Validated compact fields:

```text
agreement_status = VERIFIED
source_text_status = AVAILABLE_USED
source_text_page_number = "3"
source_text_locator = p3:table:row:revenue
source_text_unavailable_reason = ""
```

The test serializes rows only inside the assertion and confirms:

```text
SOURCE_TEXT not in serialized_queue
```

Review queue remains compact fields only.

## Full source_text serialization review

QA result: **VALID**.

Full fixture text is present only in:

```text
tests/agent/fixtures/source_text_sidecars/r7af_source_text_sidecar__basic_positive_negative__v1.json
test helper constants / temporary test payloads
in-memory SourceTextEvidence.text
```

R7AF asserts full text is absent from serialized delivery-like outputs:

```text
evidence_index raw JSON
review_queue serialized in-memory rows
```

Read-only review of `datefac_agent/delivery/evidence_index_writer.py` and `datefac_agent/review/review_queue_builder.py` confirms those serializers write metadata / compact fields and do not serialize `source_text.text`.

## Boundary policy review

QA result: **VALID**.

R7AF confirms `VERIFIED` remains non-promotional:

```text
agreement_status = VERIFIED
evidence_level = WEAK_EVIDENCE
clean_candidate_type = REVIEW_REQUIRED
```

Read-only review confirms:

1. `clean_candidate_policy.py` does not use `agreement_status`.
2. `MARKET_REFERENCE_ROW` still returns `REVIEW_REQUIRED`.
3. `output_schema_guardrails.py` still forbids `MARKET_REFERENCE_ROW` in clean data.
4. `classify_evidence_level(...)` still treats explicit/page provenance as `WEAK_EVIDENCE`, not `STRONG_EVIDENCE`.
5. qualitative_facts admission was not broadened.

QA answer:

```text
VERIFIED -> not STRONG_EVIDENCE
VERIFIED -> not clean_data admission
VERIFIED -> not MARKET_REFERENCE_ROW acceptance
```

## Readiness gates review

QA result: **VALID / CLOSED**.

R7AF builds a manifest through existing `build_manifest(...)` and asserts:

```text
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
```

Read-only review confirms runner defaults remain closed and guardrails still enforce closed gates.

External-call counters remain zero in the runner contract:

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

R7AF did not run or add MinerU, OCR, LLM, VLM, workbook rerun, `run_pilot(...)`, or PDF extraction.

## Test review

QA result: **VALID**.

R7AF added focused tests in:

```text
tests/agent/test_source_text_sidecar_loader_348n.py
```

Coverage includes:

```text
valid fixture load
SourceTextEvidence field preservation
VERIFIED through existing wiring
DISAGREED numeric mismatch
evidence_index metadata-only and no full text
review_queue compact fields and no full text
invalid top-level payloads
invalid record payloads
invalid JSON
non-object JSON
duplicate source_text_id
later invalid record / no partial return
source_id/page/locator mismatches remain UNVERIFIED
missing source_text remains UNVERIFIED
clean/readiness boundaries remain closed
```

All agent tests pass together:

```text
162 passed in 0.97s
```

## Compatibility risk review

No blocking compatibility issue found.

Residual risks:

1. `text_kind = "table_row"` is test-only and not currently a production `SourceTextKind` literal; this is acceptable in test-only loader scope but should be normalized or formally supported before any production promotion.
2. The loader imports `SourceTextEvidence` from production schemas, but the loader itself remains under `tests/agent/` and is not imported by production code.
3. The first file-backed fixture uses synthetic text only; real source_text ingestion remains out of scope.
4. The `Select-String` reference scan encountered ignored `__pycache__` hits after test execution; those are generated cache files, not source hooks and were not staged.
5. Future runner integration must be designed separately before any CLI or production path can read sidecars.

Risk level: **acceptable for R7AF-QA**.

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
  162 passed in 0.97s
```

```text
git status -sb
  before report creation:
    ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
```

```text
git diff --stat
  before report creation:
    no output
```

```text
git diff --name-only
  before report creation:
    no output
```

```text
git diff --check
  before report creation:
    passed, no output
```

## Decision

```text
Decision = 348N_R7AF_QA_CONFIRMED_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_VALID
```

R7AF-QA confirms the file-backed source_text sidecar loader is valid within the intended test-only scope. The loader is isolated under `tests/agent/`, has no production/runner/CLI hook, enforces strict JSON object v1 schema, fails closed for malformed or unsafe files, does not return partial records on invalid files, maps valid records into `SourceTextEvidence`, preserves existing `VERIFIED` / `DISAGREED` / conservative `UNVERIFIED` behavior, keeps evidence_index and review_queue metadata-only, excludes full source_text from serialized outputs, and keeps clean/readiness boundaries closed.

## Recommended next task

```text
348N-R7AG single-real-MinerU-artifact adapter design
```

Recommended scope:

```text
design-only first
single real artifact/demo path only
no batch production integration
no readiness gate opening
no full source_text serialization
```

Do not jump to production readiness.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7AF-QA confirms file-backed source_text sidecar loader is valid and test-only
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 162 passed in 0.97s
files_modified（修改文件数）= 1，only this R7AF-QA report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/fixture/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7AF-QA report
sidecar_loader_result（sidecar loader结果）= PASS，loader stays under tests/agent/ with no production hook
fail_closed_result（失败关闭结果）= PASS，malformed / unknown / missing / duplicate / bad hash / bad char_count / untrusted records fail closed with no partial return
evidence_index_validation_result（证据索引验证结果）= PASS，metadata/hash/count/status only，no full source_text
review_queue_validation_result（复核队列验证结果）= PASS，compact fields only，no full source_text
full_text_serialization_result（全文序列化结果）= PASS，serialized evidence_index / review_queue exclude full source_text
qa_result（QA结果）= VALID
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= 348N-R7AG single-real-MinerU-artifact adapter design
```
