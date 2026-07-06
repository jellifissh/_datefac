# 348N-R7AE source_text file-backed sidecar loader design

## Task ID

```text
348N-R7AE source_text file-backed sidecar loader design
```

## Recommended reasoning level used

```text
recommended_reasoning_level = max
reason = R7AE designs the first file-backed source_text sidecar loader after fixture dry-run QA. A bad loader contract could turn fixture-only evidence into unsafe production-like evidence, serialize full text, or weaken provenance binding.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 39e01ba..5972291
  Fast-forward
  created docs/codex_tasks/348N_R7AE_source_text_file_backed_sidecar_loader_design.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  5972291 docs: update handoff after R7AD QA
  7597aaf docs: refresh plain-language progress after R7AD QA
  de98cd9 docs: sync progress after R7AD QA
  a984758 docs: add R7AE source text loader design task
  39e01ba docs: add R7AD QA review
  bec322e docs: update handoff after R7AD
  c2edfb5 docs: refresh plain-language progress after R7AD
  dba2b8b docs: sync progress after R7AD
  59b9aab docs: add R7AD QA task
  9cd4ef6 test: add source text fixture dry-run coverage
  1f9ee32 docs: update handoff after R7AC
  afb0ee0 docs: refresh plain-language progress after R7AC
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
- `docs/codex_tasks/348N_R7AE_source_text_file_backed_sidecar_loader_design.md`
- `docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md`
- `docs/codex_tasks/348N_R7AD_QA_source_text_fixture_dry_run_review.md`
- `docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md`
- `docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md`
- `docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md`

Implementation reviewed read-only:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `tests/agent/conftest.py`

## Sidecar format recommendation

Recommendation: **JSON object first, not JSONL**.

Rationale:

1. The first file-backed loader should be tiny, schema-versioned, and easy to inspect in code review.
2. A single JSON object supports top-level safety metadata such as `schema_version`, `fixture_scope`, and `sidecar_id`.
3. JSONL is useful for large append-only logs, but R7AE/R7AF should not optimize for large production source_text corpora.
4. JSON object format makes it easier to reject unknown top-level keys and malformed structure before any `SourceTextEvidence` is created.

Recommended file shape:

```json
{
  "schema_version": "source_text_sidecar.v1",
  "fixture_scope": "test_only",
  "sidecar_id": "r7af_source_text_sidecar__basic_positive_negative__v1",
  "description": "Synthetic source_text sidecar fixture for R7AF tests only.",
  "records": [
    {
      "source_text_id": "r7af-demo-p12-revenue",
      "source_document_id": "demo.pdf",
      "page_number": 12,
      "locator": "营业收入(百万元)",
      "text_kind": "snippet_text",
      "text": "2024A 营业收入 1,234 百万元",
      "trusted_source": true,
      "extraction_method": "fixture_sidecar",
      "text_sha256": "<sha256 of exact UTF-8 text>",
      "char_count": 22
    }
  ]
}
```

## Sidecar schema recommendation

Top-level required fields:

```text
schema_version = "source_text_sidecar.v1"
fixture_scope = "test_only"
records = list[record]
```

Top-level optional fields:

```text
sidecar_id
description
created_for_task
```

Top-level unknown fields should be rejected.

Record required fields:

```text
source_text_id
source_document_id
page_number
locator
text_kind
text
trusted_source
extraction_method
text_sha256
```

Record optional fields:

```text
char_count
notes
```

Record unknown fields should be rejected.

Recommended first-slice restrictions:

```text
text_kind must be "snippet_text" or "table_row_text"
page_text should be rejected in the first file-backed loader
locator must be non-empty
trusted_source must be true
text must be non-empty after stripping
source_text_id must be unique within the file
```

Why reject `page_text` first:

1. Current selection treats `page_text` as broad page-compatible.
2. Broad page text can contain unrelated numeric tokens.
3. R7AD/R7AB already proved source_text wiring; R7AF should validate narrow provenance-bound fixtures first.
4. A later task can design page-level evidence policies separately.

Mapping to current model:

```text
record.source_text_id -> SourceTextEvidence.source_text_id
record.source_document_id -> SourceTextEvidence.source_document_id
record.page_number -> SourceTextEvidence.page_number
record.locator -> SourceTextEvidence.locator
record.text_kind -> SourceTextEvidence.text_kind
record.text -> SourceTextEvidence.text
record.trusted_source -> SourceTextEvidence.trusted_source
record.extraction_method -> SourceTextEvidence.extraction_method
validated text_sha256 -> SourceTextEvidence.text_sha256
computed/validated char_count -> SourceTextEvidence.char_count
```

## Fixture location recommendation

Committed test fixtures should live under:

```text
tests/agent/fixtures/source_text_sidecars/
```

Recommended first fixture name:

```text
r7af_source_text_sidecar__basic_positive_negative__v1.json
```

Rules:

1. Use synthetic source_text only.
2. Do not place sidecars under `input/`, `output/`, `temp/`, `data/`, or legacy `datefac/`.
3. Keep the first fixture small enough for direct review.
4. Include `fixture_scope = test_only`.
5. Do not commit real client document text.

## Loader placement recommendation

Recommendation: **test-only loader first**.

R7AF should implement either:

```text
tests/agent/source_text_sidecar_loader.py
```

or a small helper local to:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

The first loader should not be connected to:

```text
tools/run_agent_excel_intake_audit_348a.py
run_pilot(...)
CLI args
real workbook-family reruns
```

Reasoning:

1. `audit_workbook(..., source_text_index=...)` already accepts an in-memory index.
2. `run_pilot(...)` currently has no explicit safe sidecar CLI contract.
3. Runner-visible sidecar loading could be mistaken for production source_text support.
4. Test-only loading can validate file schema without expanding operational scope.

Later promotion path, only after R7AF-QA:

```text
datefac_agent/intake/source_text_sidecar_loader.py
```

That promotion should be a separate reviewed task with explicit runner/CLI boundaries.

## Validation and fail-closed rules

Loader should fail closed. No partial records should be returned after a structural validation error.

Structural validation failures should raise a deterministic validation error and produce no `source_text_index`:

```text
malformed JSON
top-level payload is not an object
missing schema_version / fixture_scope / records
unsupported schema_version
fixture_scope != test_only
records is not a list
unknown top-level key
unknown record key
missing required record field
duplicate source_text_id
source_text_id empty
source_document_id empty
page_number not int
page_number <= 0
locator empty
unsupported text_kind
text_kind == page_text in v1
trusted_source is not true
text empty after strip
extraction_method empty
text_sha256 missing or invalid hex length
text_sha256 mismatch
char_count present but mismatched
```

Provenance mismatch is not fully knowable at file-load time because it depends on row `EvidenceRef` values. The loader should accept structurally valid records, then downstream selection must still fail closed:

```text
source_document_id mismatch -> SOURCE_ID_MISMATCH -> UNVERIFIED
page_number mismatch -> PAGE_NUMBER_MISMATCH -> UNVERIFIED
locator mismatch -> LOCATOR_MISMATCH -> UNVERIFIED
no explicit/page provenance -> NO_EXPLICIT_PAGE_PROVENANCE -> MISSING/UNVERIFIED behavior preserved
```

If the implementation catches loader validation errors in tests, it should pass no `source_text_index` to row builders; this keeps agreement status conservative rather than silently using questionable records.

## Hash and text handling design

Hash rule:

```text
computed_sha256 = sha256(exact text encoded as UTF-8).hexdigest()
```

The loader should:

1. Require `text_sha256` in the JSON record.
2. Recompute the hash from exact `text`.
3. Reject the record/file if the provided hash does not match.
4. Compute `char_count` as Python `len(text)`.
5. Reject if provided `char_count` does not match computed `len(text)`.
6. Pass computed metadata into `SourceTextEvidence`.

Text handling:

```text
For R7AF test fixtures, inline full synthetic text is acceptable.
For production-like source_text, inline full source_text remains out of scope.
```

Inline full text is allowed only because the file is test-only and synthetic. Normal delivery outputs must continue to serialize only metadata:

```text
source_text_id
source_text_source_id
source_text_page_number
source_text_locator
source_text_kind
source_text_sha256
source_text_char_count
source_text_status
source_text_used_for_agreement
source_text_unavailable_reason
```

They must not serialize:

```text
source_text.text
record["text"]
full source_text snippets
```

## Integration boundary design

Recommended R7AF integration path:

```text
load_source_text_sidecar_fixture(path) -> list[SourceTextEvidence]
build_row_audit_result(..., source_text_index=loaded_records)
write_evidence_index(tempfile_path, [row_result])
build_review_queue_rows([row_result])
```

The loader should not change:

```text
SourceTextEvidence semantics
select_source_text_for_row(...)
classify_agreement_status(...)
clean_candidate_policy.py
evidence_index_writer.py serialization policy
review_queue_builder.py serialization policy
tools/run_agent_excel_intake_audit_348a.py run_pilot(...)
readiness gates
```

Source document binding:

```text
source_document_id must equal the source_pdf EvidenceRef.source_id
```

The loader should not infer `source_document_id` from workbook fields, file names, or Excel raw values. It should only load the explicit sidecar record value and rely on `select_source_text_for_row(...)` to bind it to row evidence.

## Positive loader cases

R7AF implementation should require:

1. Valid JSON sidecar loads one trusted `snippet_text` record into `SourceTextEvidence`.
2. Loader computes/validates `text_sha256` and `char_count`.
3. Matching `source_document_id`, `page_number`, and `locator` yields `AVAILABLE_USED`.
4. Matching trusted source_text can produce `VERIFIED`.
5. Trusted source_text with numeric mismatch can produce `DISAGREED`.
6. Evidence index written to tempfile contains metadata/hash/count/status only.
7. Review queue built in memory contains compact fields only.
8. Full source_text is absent from serialized evidence index and review queue rows.
9. `VERIFIED` keeps `evidence_level = WEAK_EVIDENCE`.
10. `MARKET_REFERENCE_ROW` remains `REVIEW_REQUIRED`.
11. Readiness gates remain closed.

## Negative loader cases

R7AF implementation should require:

Structural fail-closed cases:

```text
malformed JSON -> loader validation error, no records
wrong root type -> loader validation error, no records
missing schema_version -> loader validation error, no records
unsupported schema_version -> loader validation error, no records
fixture_scope != test_only -> loader validation error, no records
unknown top-level key -> loader validation error, no records
records not list -> loader validation error, no records
unknown record key -> loader validation error, no records
missing required record field -> loader validation error, no records
duplicate source_text_id -> loader validation error, no records
page_number <= 0 / non-int -> loader validation error, no records
unsupported text_kind -> loader validation error, no records
page_text in v1 -> loader validation error, no records
trusted_source false -> loader validation error, no records
empty text -> loader validation error, no records
text_sha256 mismatch -> loader validation error, no records
char_count mismatch -> loader validation error, no records
```

Selection fail-closed cases using structurally valid records:

```text
missing sidecar file or no source_text_index -> UNVERIFIED / MISSING
source_document_id mismatch -> UNVERIFIED / SOURCE_ID_MISMATCH / not used
page_number mismatch -> UNVERIFIED / PAGE_NUMBER_MISMATCH / not used
locator mismatch -> UNVERIFIED / LOCATOR_MISMATCH / not used
no explicit page provenance -> MISSING or UNVERIFIED conservative status / not used
Excel raw field decoys -> not trusted source_text
```

## Evidence index / review queue validation design

Evidence index validation:

```text
use tempfile.TemporaryDirectory()
write_evidence_index(temp_path, [row_result])
read raw JSON string
assert source_text metadata fields are present
assert source_text_sha256 equals expected hash
assert source_text_char_count equals len(text)
assert source_text_used_for_agreement is true only for selected records
assert source_text_unavailable_reason is deterministic for not-used records
assert record["text"] / full source_text not in raw JSON
```

Review queue validation:

```text
build_review_queue_rows([row_result]) in memory
serialize rows with json.dumps(..., ensure_ascii=False)
assert agreement_status present
assert source_text_status present
assert source_text_page_number compact
assert source_text_locator compact
assert source_text_unavailable_reason compact
assert full source_text not in serialized rows
```

Boundary validation:

```text
VERIFIED does not become STRONG_EVIDENCE
VERIFIED does not become clean admission
VERIFIED does not open readiness gates
MARKET_REFERENCE_ROW remains REVIEW_REQUIRED
```

## Out-of-scope list

R7AE and the recommended first implementation must not include:

```text
production source_text ingestion
runner CLI sidecar argument
run_pilot(...) integration
real workbook rerun
real client workbook dry-run
MinerU
OCR
LLM / VLM
PDF extraction pipeline
production readiness
formal client export
full source_text in evidence_index
full source_text in review_queue
STRONG_EVIDENCE promotion from VERIFIED
clean_data admission from VERIFIED
MARKET_REFERENCE_ROW policy change
qualitative_facts admission change
output/input/temp/data/legacy/config/dependency changes
```

## Risk review

### Risk 1: Test sidecar mistaken for production source_text

Mitigation:

```text
fixture_scope = test_only
fixture location under tests/agent/fixtures/source_text_sidecars/
synthetic snippets only
test-only loader first
no runner/CLI hook in R7AF
```

### Risk 2: Loader admits broad page-level text and creates false VERIFIED

Mitigation:

```text
reject page_text in v1
require snippet_text/table_row_text
require locator
include mismatch / unrelated-number negative cases
```

### Risk 3: Hash metadata is trusted without verification

Mitigation:

```text
recompute sha256 from exact UTF-8 text
reject hash mismatch
compute char_count locally
reject char_count mismatch when provided
```

### Risk 4: Full source_text leaks into delivery outputs

Mitigation:

```text
do not change evidence_index_writer.py or review_queue_builder.py serialization policy
assert full source_text absent from raw evidence_index JSON
assert full source_text absent from serialized review_queue rows
keep metadata/hash/count/status only
```

### Risk 5: VERIFIED is misread as clean/readiness

Mitigation:

```text
keep VERIFIED as agreement_status only
assert evidence_level remains WEAK_EVIDENCE
assert MARKET_REFERENCE_ROW remains REVIEW_REQUIRED
assert manifest gates remain closed
```

### Risk 6: Partial-load behavior hides invalid sidecar records

Mitigation:

```text
fail the whole file on structural validation error
do not return partial records
tests must assert no records are produced after validation failure
```

Risk level: **acceptable if R7AF remains test-only and fail-closed**.

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
pytest tests/agent -q
  ........................................................................ [ 53%]
  ..............................................................           [100%]
  134 passed in 0.63s
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
Decision = 348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN_VALID
```

R7AE design is complete. The safest first file-backed loader is a JSON-object, schema-versioned, `test_only` sidecar under `tests/agent/fixtures/source_text_sidecars/`, loaded by test-only code first. It should reject malformed or unsafe files, verify `text_sha256` from exact UTF-8 text, map valid records into `SourceTextEvidence`, rely on existing provenance binding for row-level selection, keep evidence_index/review_queue metadata-only, and keep `VERIFIED` separate from `STRONG_EVIDENCE`, clean admission, and readiness.

## Recommended next task

```text
348N-R7AF test-only source_text file-backed sidecar loader implementation
```

Recommended R7AF scope:

```text
add one tiny synthetic JSON sidecar under tests/agent/fixtures/source_text_sidecars/
add a test-only loader helper
validate schema/hash/fail-closed behavior
map valid records into SourceTextEvidence
reuse R7AD lower-level dry-run path
assert evidence_index/review_queue exclude full source_text
do not connect run_pilot or real workbook reruns
keep readiness gates closed
```

Do not jump to production readiness or real workbook rerun.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7AE source_text file-backed sidecar loader design completed
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 134 passed in 0.63s
files_modified（修改文件数）= 1，only this R7AE design report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7AE design report
sidecar_format_result（sidecar格式结果）= PASS，推荐 JSON object v1，不推荐 JSONL 作为首个 loader 格式
loader_design_result（loader设计结果）= PASS，test-only loader first，不接 run_pilot / CLI / production path
fail_closed_design_result（失败关闭设计结果）= PASS，malformed / unsafe / hash mismatch / duplicate / unsupported fields 全部 fail closed，无 partial records
evidence_index_review_queue_design_result（证据索引/复核队列设计结果）= PASS，仅 metadata/hash/count/status/compact fields，不写 full source_text
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= 348N-R7AF test-only source_text file-backed sidecar loader implementation
```
