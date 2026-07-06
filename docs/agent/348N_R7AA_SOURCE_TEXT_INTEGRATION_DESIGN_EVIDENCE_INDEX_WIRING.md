# 348N-R7AA source_text integration design / evidence index wiring

## Task ID

```text
348N-R7AA source_text integration design / evidence index wiring
```

## Recommended reasoning level used

```text
recommended_reasoning_level = max
reason = This task designs how real source_text should enter the evidence agreement pipeline. A bad design could turn the R7Y/R7Z checker into a false-confidence generator, so no implementation should happen before the wiring contract is reviewed.
```

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 898fa24..c1cee01
  Fast-forward
   docs/agent/项目进程.md                                      |  42 ++-
   docs/codex_tasks/348N_R7AA_source_text_integration_design_evidence_index_wiring.md | 330 +++++++++++++++++++++
   docs/project_handoffs/CURRENT_MODEL_HANDOFF.md               |  83 +++---
   项目进展大白话说明.md                                        |  82 ++---
   4 files changed, 413 insertions(+), 124 deletions(-)
   create mode 100644 docs/codex_tasks/348N_R7AA_source_text_integration_design_evidence_index_wiring.md

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  c1cee01 docs: update handoff after R7Z QA
  ae5a24a docs: refresh plain-language progress after R7Z QA
  3eaecd1 docs: sync progress after R7Z QA
  8da7b06 docs: add R7AA source text integration design task
  898fa24 docs: add R7Z QA review
  5890cf8 docs: update handoff after R7Z
  7814358 docs: refresh plain-language progress after R7Z
  6663f39 docs: sync progress after R7Z
  f8fbf6d docs: add R7Z QA task
  004e307 fix: make agreement checker multiplicity conservative
  eb2e355 docs: update handoff after R7Y QA
  39fd02e docs: refresh plain-language progress after R7Y QA
```

Worktree was clean after pull.

## Files reviewed

Required context, read-only:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AA_source_text_integration_design_evidence_index_wiring.md`
- `docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md`
- `docs/codex_tasks/348N_R7Z_QA_agreement_checker_edge_case_review.md`
- `docs/codex_tasks/348N_R7Z_agreement_checker_edge_case_fixture_coverage.md`
- `docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md`
- `docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md`

Current code inspected read-only:

- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/intake/excel_intake.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/output_schema_guardrails.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `tools/run_agent_excel_intake_audit_348a.py`

Read-only searches run for active source/evidence carriers:

```text
source_text
source_page
page_text
evidence_text
explicit_evidence_ref
locator
evidence_index
source_id
page_number
agreement_status
```

## Current source_text availability review

Current active pipeline status:

```text
source_text is not carried by production row-building today.
```

Findings:

1. `classify_agreement_status(row, evidence_refs, source_text=None)` accepts `source_text`, but only tests currently pass source text directly.
2. `build_row_audit_result(...)` calls `classify_agreement_status(row, list(evidence_refs))` without source text. Therefore explicit/page provenance remains `UNVERIFIED` in the real in-memory audit flow.
3. `audit_workbook(...)` currently builds row-level issues, evidence refs, and evidence level, then immediately calls `build_row_audit_result(...)`. No source text lookup happens between evidence construction and agreement classification.
4. `SpreadsheetRow` carries workbook fields: `source_excel_path`, `sheet_name`, `row_index`, `column_names`, `raw_values`, `metric_name`, `unit_hint`, `period_values`, `explicit_evidence_ref`, and `row_type`. It has no trusted source text field.
5. `EvidenceRef` carries `source_type`, `source_id`, `page_number`, `locator`, and `is_explicit`. It has no text payload, text hash, or source-text trust status.
6. Excel intake recognizes workbook columns such as `source_page`, `value_text_original`, `来源页`, `页码`, and `摘录/说明`, but these are workbook-side extracted or descriptive fields. They are not automatically trusted PDF/source text.
7. `normalized_testset` rows include `source_pdf`, `source_page`, `value_text_original`, and related fields, but they are routed as `NORMALIZED_TESTSET_RECORD_ROW` / review-only support rows. `value_text_original` is an extracted value representation and must not be used to verify the same extracted value.
8. `qualitative_facts` can contain `摘录/说明`, but current policy routes it to `TESTSET_SUPPORTING_ROW` / `REVIEW_REQUIRED`. It is not part of the current deterministic source-text agreement path.
9. `market_base_data` may carry `来源页`, which is useful page provenance, but page provenance alone is not source text and must not become `VERIFIED`.

Conclusion:

```text
Current Excel intake carries provenance hints and workbook-side extracted value text, but does not carry trusted source_text suitable for source-value agreement verification.
```

## Current evidence index review

Current `evidence_index.json` writer serializes row-level evidence metadata:

```text
sheet_name
row_index
metric_name
decision
clean_candidate_type
evidence_level
agreement_status
row_type
explicit_evidence_ref
evidence_refs[]
raw_values
```

Each `evidence_refs[]` entry includes:

```text
source_type
source_id
page_number
locator
is_explicit
```

Current gaps for source_text wiring:

```text
no source_text_available flag
no source_text_status / reason
no source_text_id
no source_text_source_id
no source_text_page_number
no source_text_locator
no source_text_hash
no source_text_char_count
no source_text_kind
no source_text_trust_status
```

Current `review_queue.csv` rows include:

```text
sheet_name
row_index
metric_name
decision
clean_candidate_type
issue_count
issue_codes
evidence_level
row_type
unit_hint
period_labels
explicit_evidence_ref
```

Current review queue gaps:

```text
agreement_status is not included
source_text availability is not included
source_text mismatch/unavailable reason is not included
```

Design implication: evidence index should become the detailed audit surface for source-text availability, while review queue should include only compact fields needed by a human reviewer.

## Proposed source_text contract

Do not attach unqualified raw strings to rows. The minimum safe contract should be a provenance-tied source text record, conceptually:

```python
@dataclass(frozen=True)
class SourceTextEvidence:
    source_text_id: str
    source_document_id: str
    page_number: int
    locator: str | None
    text_kind: Literal["page_text", "table_row_text", "snippet_text"]
    text: str
    text_sha256: str
    char_count: int
    trusted_source: bool
    extraction_method: str
```

Required fields and meaning:

```text
source_text_id:
  Stable ID for the source-text record. Used in evidence_index/review_queue. It should not be generated from row index alone.

source_document_id:
  Must match the source PDF identity already represented by source_pdf EvidenceRef.source_id, usually the resolved PDF path or a stable document ID.

page_number:
  Must match parsed explicit/page provenance on the row. If no row page provenance exists, source_text must not be used for VERIFIED.

locator:
  Stable local locator for the source text. For page text this may be "page:<n>". For table-row/snippet text it should identify table / row / span when available.

text_kind:
  Distinguishes broad page text from row-local or snippet-level text. This is important because row-level checker risk is higher on full-page text than on row-local text.

text:
  The actual evidence text passed to the deterministic checker. It must not be an LLM summary or a rephrased value.

text_sha256:
  Hash of the exact text used for verification. Evidence index should serialize the hash, not the full text by default.

trusted_source:
  Must be true before text can be passed to the agreement checker. Untrusted source text keeps agreement_status UNVERIFIED.

extraction_method:
  Records provenance of the text, e.g. precomputed deterministic PDF text artifact, human-reviewed snippet, or fixture. LLM/VLM-generated summaries are not valid for VERIFIED.
```

Mandatory binding rule:

```text
A source_text record may be used only when all of these hold:

1. row/evidence_refs contain explicit page provenance;
2. parsed page_number is not None;
3. source_text.source_document_id matches the row's source_pdf EvidenceRef.source_id;
4. source_text.page_number matches explicit EvidenceRef.page_number;
5. source_text.trusted_source is true;
6. source_text.text is non-empty;
7. locator is compatible with the evidence ref / source_text kind;
8. no row policy explicitly marks the row family as source-text-ineligible.
```

If any binding rule fails:

```text
agreement_status must remain UNVERIFIED, or MISSING when no explicit/page provenance exists.
```

## Proposed integration slice

Recommended first implementation slice after R7AA:

```text
R7AB source_text availability / evidence index wiring implementation
```

Minimal implementation sequence:

1. Define a small `SourceTextEvidence` data model or typed dict in `datefac_agent/schemas/` or a narrow audit helper module.
2. Add an optional source-text index input to the in-memory audit path. Keep the default `None` so current production behavior is unchanged.
3. Implement a pure helper such as:

```python
def select_source_text_for_row(
    row: SpreadsheetRow,
    evidence_refs: list[EvidenceRef],
    source_text_index: SourceTextIndex | None,
) -> SourceTextSelection:
    ...
```

4. The helper returns a source-text selection only when source document ID, page number, trust status, and locator rules pass.
5. Update `build_row_audit_result(...)` or the audit assembly layer to pass `selection.text` into `classify_agreement_status(...)` only after selection is valid.
6. If selection is absent or invalid, preserve current behavior:

```text
explicit/page provenance -> UNVERIFIED
no explicit/page provenance -> MISSING
```

7. Serialize source-text availability metadata in evidence_index, not the full source text.
8. Add compact review_queue fields for reviewer triage.
9. Add tests before any real runner usage.

Preferred integration point:

```text
audit_workbook(...) / audit assembly layer
```

Reason: this layer already has `row`, `evidence_refs`, `evidence_level`, and can accept an optional source-text index. Keeping source_text selection outside `SpreadsheetRow` avoids treating workbook raw fields as trusted evidence text.

Avoid in the first slice:

```text
- storing full source_text on SpreadsheetRow;
- overloading EvidenceRef.source_id with both document ID and raw page ref;
- using raw_values["value_text_original"] as source_text;
- using qualitative_facts 摘录/说明 as source_text automatically;
- adding PDF/OCR extraction inside the audit runner.
```

## Evidence index / review_queue output design

### evidence_index.json

Add compact source-text availability fields at row level:

```text
source_text_status:
  one of: NOT_REQUESTED / UNAVAILABLE / AVAILABLE_TRUSTED / AVAILABLE_UNTRUSTED / PROVENANCE_MISMATCH / USED_FOR_AGREEMENT

source_text_id:
  stable source-text record ID, empty/null when unavailable

source_text_source_id:
  source document ID bound to source_text

source_text_page_number:
  page number bound to source_text

source_text_locator:
  locator for page/table/snippet text

source_text_kind:
  page_text / table_row_text / snippet_text

source_text_sha256:
  hash of exact text used, not the full text

source_text_char_count:
  size of text used

source_text_used_for_agreement:
  boolean

source_text_unavailable_reason:
  missing_index / missing_page_provenance / source_id_mismatch / page_mismatch / untrusted / empty_text / unsupported_row_type / none
```

Do not serialize full source text by default. If future debugging needs text, use a separate controlled sidecar and do not commit bulk text artifacts by default.

### review_queue.csv

Add only compact triage fields:

```text
agreement_status
source_text_status
source_text_page_number
source_text_locator
source_text_unavailable_reason
```

Do not include full source text in review queue CSV. The queue should help reviewers understand why a row is `UNVERIFIED` / `DISAGREED`, not become a text archive.

### manifest / run summary

Future implementation may add aggregate counters, still with readiness gates closed:

```text
source_text_available_count
source_text_used_for_agreement_count
source_text_unavailable_count
source_text_provenance_mismatch_count
verified_agreement_count
disagreed_agreement_count
unverified_agreement_count
```

These counters must not affect:

```text
client_ready
production_ready
formal_client_export_allowed
clean_data admission
```

## Out-of-scope list

R7AA and the recommended first implementation slice must not include:

```text
- MinerU rerun
- OCR
- LLM/VLM calls
- PDF re-extraction
- broad source-text pipeline implementation
- formal client delivery
- production readiness claims
- STRONG_EVIDENCE promotion based on VERIFIED
- clean_data admission changes based on VERIFIED
- MARKET_REFERENCE_ROW policy changes
- qualitative_facts admission changes
- output/input/temp/data/legacy/config/dependency changes
- storing full source text in evidence_index or review_queue by default
- period-aware or coordinate-aware matching unless separately designed
```

## Risk review

### Risk 1: source_text from workbook raw fields becomes circular evidence

`value_text_original` and similar workbook values are extracted data, not independent source evidence. Using them as source_text could verify an extraction against itself.

Mitigation:

```text
Only use source_text from a separate trusted source-text record whose source_document_id/page_number/locator are bound to the source PDF provenance.
```

### Risk 2: page-level text has unrelated numbers

Full page text can include unrelated numeric tokens. R7Z multiplicity reduces one class of false positive, but row-level matching is still not period-aware or coordinate-aware.

Mitigation:

```text
Prefer table-row or snippet text when available. Record text_kind. Keep full-page text as lower-confidence availability and do not promote to STRONG_EVIDENCE by default.
```

### Risk 3: mismatched source_id or page_number

A text snippet from the wrong document or page can create false VERIFIED/DISAGREED.

Mitigation:

```text
Require source_document_id and page_number to match evidence refs before the checker receives source_text. Mismatch -> UNVERIFIED with reason PROVENANCE_MISMATCH.
```

### Risk 4: source_text exists without explicit provenance

Source text alone cannot prove row-level agreement if the row has no explicit/page provenance.

Mitigation:

```text
No explicit/page provenance -> MISSING, even if a source_text record exists somewhere.
```

### Risk 5: VERIFIED is misused downstream

Future code might treat VERIFIED as `STRONG_EVIDENCE`, clean admission, or readiness.

Mitigation:

```text
Keep agreement_status separate from evidence_level, clean_candidate_type, and readiness flags. Add tests that VERIFIED does not change those surfaces.
```

### Risk 6: evidence_index bloat or sensitive text leakage

Storing full text in every row-level evidence index can create large outputs and leak source content.

Mitigation:

```text
Serialize source_text_id, hash, locator, page, kind, and char_count by default. Do not store full source_text in standard evidence_index.json.
```

## Required tests for the next implementation task

The next implementation task should require at least:

```text
1. no source_text index -> explicit/page row remains UNVERIFIED;
2. source_text present but no explicit/page provenance -> MISSING;
3. source_text source_id mismatch -> UNVERIFIED;
4. source_text page_number mismatch -> UNVERIFIED;
5. source_text untrusted -> UNVERIFIED;
6. source_text empty -> UNVERIFIED;
7. trusted matching source_text -> VERIFIED;
8. trusted full mismatch source_text -> DISAGREED;
9. partial coverage remains UNVERIFIED;
10. value_text_original is not used automatically as source_text;
11. qualitative_facts 摘录/说明 is not used automatically as source_text;
12. evidence_index serializes source_text_status/hash/id but not full text;
13. review_queue includes agreement_status/source_text_status compact fields;
14. VERIFIED does not become STRONG_EVIDENCE;
15. VERIFIED does not change clean admission;
16. readiness gates remain closed.
```

## Validation outputs

```text
D:\anaconda\python.exe -m py_compile datefac_agent/review/clean_candidate_policy.py
  passed, no output
```

```text
D:\anaconda\python.exe -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  passed, no output
```

```text
D:\anaconda\python.exe -m pytest tests/agent -q
  ........................................................................ [ 64%]
  .......................................                                  [100%]
  111 passed in 0.69s
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

## Decision

```text
Decision = 348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_VALID
```

R7AA design is complete. The recommended integration contract is conservative: source_text must be provenance-bound, trusted, and selected from a dedicated source-text record/index before it reaches the agreement checker. Missing, untrusted, or mismatched source_text keeps rows `UNVERIFIED` or `MISSING`; source_text alone and page_number alone do not produce `VERIFIED`.

## Recommended next task

```text
348N-R7AB source_text availability / evidence index wiring implementation
```

Recommended scope for R7AB:

```text
- add a minimal source_text sidecar/index model;
- add deterministic source_text selection by source_id/page_number/locator;
- pass selected trusted source_text into classify_agreement_status;
- serialize source_text availability metadata in evidence_index;
- add compact agreement/source_text fields to review_queue;
- keep source_text optional and default behavior unchanged;
- no OCR/MinerU/LLM/VLM/PDF extraction;
- no STRONG_EVIDENCE, clean admission, or readiness changes.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7AA source_text integration design completed
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 111 passed in 0.69s
files_modified（修改文件数）= 1，only this design report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7AA design report
source_text_availability_result（source_text可用性结果）= CURRENT_PIPELINE_HAS_NO_TRUSTED_SOURCE_TEXT，现有 active pipeline 只有 provenance hints / workbook extracted fields / test-only source_text 参数
integration_design_result（接入设计结果）= PASS，设计为 provenance-tied trusted source_text sidecar/index + selection helper + checker-call-time injection
evidence_index_design_result（证据索引设计结果）= PASS，建议记录 source_text_status/id/source_id/page/locator/kind/hash/char_count，不默认存全文
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= R7AB source_text availability / evidence index wiring implementation
```
