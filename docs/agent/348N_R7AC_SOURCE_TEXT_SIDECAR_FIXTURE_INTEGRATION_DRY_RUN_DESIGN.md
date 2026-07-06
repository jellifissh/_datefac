# 348N-R7AC source_text sidecar fixture integration / dry-run design

## Task ID

```text
348N-R7AC source_text sidecar fixture integration / dry-run design
```

## Recommended reasoning level used

```text
recommended_reasoning_level = max
reason = R7AC designs the first safe fixture/dry-run path for exercising R7AB source_text wiring without trusting unsafe workbook fields, generating real outputs, or opening readiness gates.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  first attempt failed with transient TLS/schannel handshake error
  retry succeeded:
    Updating 758ec98..28c626a
    Fast-forward
    created docs/codex_tasks/348N_R7AC_source_text_sidecar_fixture_integration_dry_run_design.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  28c626a docs: update handoff after R7AB QA
  b859afc docs: refresh plain-language progress after R7AB QA
  5877611 docs: sync progress after R7AB QA
  5c0e431 docs: add R7AC source text sidecar dry-run design task
  758ec98 docs: add R7AB QA review
  dc6e478 docs: update handoff after R7AB
  2b26d25 docs: refresh plain-language progress after R7AB
  627eb77 docs: sync progress after R7AB
  c13bc7e docs: add R7AB QA task
  12a4726 feat: wire trusted source text metadata
  37316d5 docs: update handoff after R7AA
  2630b1f docs: refresh plain-language progress after R7AA
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
- `docs/codex_tasks/348N_R7AC_source_text_sidecar_fixture_integration_dry_run_design.md`
- `docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md`
- `docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md`
- `docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md`
- `docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md`
- `docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md`

Implementation reviewed read-only:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `tests/agent/conftest.py`

## Fixture sidecar format recommendation

Recommended first format:

```text
Phase 1 / R7AD: in-test Python objects using SourceTextEvidence
Phase 2 / later: compact JSON fixture only after object-level behavior is locked
```

Rationale:

1. The current R7AB interface already accepts `list[SourceTextEvidence]` or `dict[str, SourceTextEvidence]`.
2. In-test objects avoid adding a loader/parser contract before the selection and serialization behavior is fully hardened.
3. In-test objects keep fixture source_text clearly separate from production source_text.
4. In-test objects reduce the risk of accidentally treating committed JSON sidecars as production provenance.

If a future implementation needs a file format, recommend JSON over JSONL for the first file-backed fixture:

```json
{
  "fixture_id": "r7ad_source_text_sidecar_v1",
  "fixture_scope": "test_only",
  "records": [
    {
      "source_text_id": "fixture-demo-p12-revenue",
      "source_document_id": "demo.pdf",
      "page_number": 12,
      "locator": "营业收入(百万元)",
      "text_kind": "snippet_text",
      "text": "2024A 营业收入 1,234 百万元",
      "trusted_source": true,
      "extraction_method": "fixture_sidecar",
      "text_sha256": "<computed in test or checked against SourceTextEvidence>",
      "char_count": 23
    }
  ]
}
```

JSON is preferred over JSONL because the first fixture should be tiny, versioned, easy to inspect, and able to include top-level metadata such as `fixture_scope = test_only`.

Minimum fields:

```text
source_text_id
source_document_id
page_number
locator
text_kind
text
trusted_source
extraction_method
```

Derived / validated metadata:

```text
text_sha256
char_count
```

The loader, if later added, should compute `text_sha256` and `char_count` from `text` and reject mismatches rather than trusting fixture metadata blindly.

## Fixture location recommendation

Recommended first location for future file-backed fixtures:

```text
tests/agent/fixtures/source_text_sidecars/
```

Recommended naming:

```text
r7ad_source_text_sidecar__basic_positive_negative__v1.json
```

Commit policy recommendation:

```text
Phase 1: generate SourceTextEvidence objects in tests, no committed source_text fixture file
Phase 2: commit a tiny JSON fixture only if loader/file-contract behavior is the task target
```

Reasoning:

1. Generated in-test objects are safer for the first dry-run because no standalone source_text artifact can be mistaken for production evidence.
2. A later committed JSON fixture is acceptable if it is very small, clearly test-only, and under `tests/agent/fixtures/`.
3. No fixture should live under `input/`, `output/`, `temp/`, `data/`, or legacy `datefac/`.
4. Full source_text in committed fixtures must be small synthetic text, not client document text.

## Dry-run path recommendation

Recommended first dry-run path:

```text
lower-level test helpers first:
  SpreadsheetRow
  audit_evidence_presence(...)
  build_row_audit_result(..., source_text_index=[SourceTextEvidence(...)] )
  write_evidence_index(...) to tempfile only when serialization must be verified
  build_review_queue_rows(...) in memory
```

Do not use `run_pilot(...)` in the first implementation slice.

Reasoning:

1. `run_pilot(...)` currently reads real workbook paths and writes standard output artifacts.
2. R7AC's purpose is to test wiring, not workbook ingestion or output directories.
3. Lower-level helpers can validate source_id / page_number / locator binding without workbook rerun.
4. `write_evidence_index(...)` can be exercised using `tempfile.TemporaryDirectory()` inside tests, not project `output/`.
5. `review_queue` can be validated directly as in-memory dict rows.

Second-phase dry-run path, only after first fixture tests pass:

```text
audit_workbook(pdf_path, excel_path, source_text_index=...)
```

This should still use test-generated workbook fixtures or small existing test fixtures, not real client workbook reruns.

## Positive fixture cases

Minimum positive cases for R7AD:

1. **Exact numeric match**
   - row: explicit evidence ref `第12页`, source PDF id `demo.pdf`, locator `营业收入(百万元)`, period value `1234`
   - source_text: trusted snippet, `source_document_id=demo.pdf`, `page_number=12`, matching locator, text contains `1,234`
   - expected: `source_text_status=AVAILABLE_USED`, `agreement_status=VERIFIED`, `source_text_used_for_agreement=true`

2. **Deterministic mismatch**
   - same binding as above, but source_text contains `999`
   - expected: `source_text_status=AVAILABLE_USED`, `agreement_status=DISAGREED`

3. **Duplicate-value safe match**
   - row values: `100`, `100`
   - source_text contains two independent `100` occurrences
   - expected: `VERIFIED`

4. **Review queue compact field display**
   - REVIEW row with source_text selected
   - expected compact fields:
     - `agreement_status`
     - `source_text_status`
     - `source_text_page_number`
     - `source_text_locator`
     - `source_text_unavailable_reason`
   - expected no full source_text in serialized queue row

5. **Evidence index metadata**
   - source_text selected
   - expected metadata:
     - `source_text_status=AVAILABLE_USED`
     - `source_text_id`
     - `source_text_source_id`
     - `source_text_page_number`
     - `source_text_locator`
     - `source_text_kind`
     - `source_text_sha256`
     - `source_text_char_count`
     - `source_text_used_for_agreement=true`
   - expected full `text` absent

## Negative fixture cases

Minimum negative cases for R7AD:

1. **No source_text index**
   - expected: explicit/page row remains `UNVERIFIED`, `source_text_status=MISSING`

2. **No explicit/page provenance**
   - row has no explicit evidence ref
   - source_text exists elsewhere
   - expected: `agreement_status=MISSING`, `source_text_status=NO_EXPLICIT_PAGE_PROVENANCE`

3. **source_id mismatch**
   - `source_document_id=other.pdf`
   - expected: `UNVERIFIED`, `source_text_status=SOURCE_ID_MISMATCH`, `used_for_agreement=false`

4. **page_number mismatch**
   - `page_number=99` for row page 12
   - expected: `UNVERIFIED`, `source_text_status=PAGE_NUMBER_MISMATCH`

5. **locator mismatch**
   - `text_kind=snippet_text`, source locator does not match explicit ref locator
   - expected: `UNVERIFIED`, `source_text_status=LOCATOR_MISMATCH`

6. **untrusted source_text**
   - `trusted_source=false`
   - expected: `UNVERIFIED`, `source_text_status=UNTRUSTED`

7. **empty source_text**
   - `text=""`
   - expected: `UNVERIFIED`, `source_text_status=EMPTY_TEXT`

8. **partial numeric coverage**
   - row values `100`, `200`, source_text contains only `100`
   - expected: `UNVERIFIED`

9. **single duplicate source occurrence**
   - row values `100`, `100`, source_text contains one `100`
   - expected: `UNVERIFIED`

10. **Excel raw field decoy**
    - row raw values include `value_text_original`, `source_page`, `来源页`, `页码`, or `摘录/说明`
    - no explicit source_text_index
    - expected: `UNVERIFIED` or `MISSING`; raw fields are not used as source_text

11. **Boundary invariants**
    - trusted matching source_text produces `VERIFIED`
    - expected still:
      - `evidence_level=WEAK_EVIDENCE`
      - `MARKET_REFERENCE_ROW -> REVIEW_REQUIRED`
      - readiness gates closed

## Evidence index validation design

Recommended validation method:

```text
use tempfile.TemporaryDirectory()
write_evidence_index(temp_path, [row_result])
read JSON payload
assert metadata fields
assert full source_text absent from raw JSON string
```

Required assertions:

```text
payload[0]["source_text_status"] == expected status
payload[0]["source_text_id"] == expected id or null
payload[0]["source_text_source_id"] == expected source id or null
payload[0]["source_text_page_number"] == expected page or null
payload[0]["source_text_locator"] == expected locator or null
payload[0]["source_text_kind"] == expected kind or null
payload[0]["source_text_sha256"] == expected sha256 or null
payload[0]["source_text_char_count"] == expected char count or null
payload[0]["source_text_used_for_agreement"] == expected bool
payload[0]["source_text_unavailable_reason"] == expected reason or null
source_text.text not in output_path.read_text(...)
```

Do not write project `output/` artifacts for this dry-run.

Do not add a debug mode that serializes full source_text in normal evidence_index.

## Review queue validation design

Recommended validation method:

```text
build_review_queue_rows([row_result])
inspect returned dict rows in memory
serialize rows with json.dumps(..., ensure_ascii=False) only inside test assertion
assert compact fields
assert full source_text absent
```

Required assertions:

```text
row["agreement_status"] == expected agreement status
row["source_text_status"] == expected source_text status
row["source_text_page_number"] == expected page or ""
row["source_text_locator"] == expected locator or ""
row["source_text_unavailable_reason"] == expected reason or ""
source_text.text not in json.dumps(queue_rows, ensure_ascii=False)
```

The review queue should remain a triage surface, not a text archive.

## Out-of-scope list

R7AC and the recommended next implementation must not include:

```text
workbook rerun
real client workbook dry-run
MinerU
OCR
LLM / VLM
PDF extraction pipeline
production source_text carrier
formal client delivery
readiness gate changes
STRONG_EVIDENCE promotion from VERIFIED
clean_data admission from VERIFIED
MARKET_REFERENCE_ROW policy change
qualitative_facts admission change
output/input/temp/data/legacy/config/dependency changes
default serialization of full source_text
```

## Risk review

### Risk 1: Fixture text is mistaken for production source_text

Risk: A committed JSON fixture with source_text could look like a real source_text artifact.

Mitigation:

```text
Start with in-test SourceTextEvidence objects.
If JSON is later committed, keep it under tests/agent/fixtures/source_text_sidecars/.
Add fixture_scope = test_only.
Use synthetic snippets only.
```

### Risk 2: File loader becomes a premature production contract

Risk: Implementing a sidecar file loader too early could imply supported production sidecar ingestion.

Mitigation:

```text
First implementation should test SourceTextEvidence objects directly.
Add JSON loader only in a separate reviewed task if needed.
Keep loader test-only unless a later production design explicitly promotes it.
```

### Risk 3: Page-level source_text creates false VERIFIED

Risk: `page_text` can contain unrelated numeric tokens.

Mitigation:

```text
Prefer snippet_text/table_row_text in fixtures.
Include partial coverage and unrelated-number negative cases.
Do not use VERIFIED for evidence promotion or readiness.
```

### Risk 4: Full source_text leaks into outputs

Risk: Evidence index or review queue could become a text archive.

Mitigation:

```text
Assert raw serialized evidence_index / review_queue output does not contain source_text.text.
Keep only id/hash/page/locator/kind/char_count/status metadata.
```

### Risk 5: VERIFIED is misused downstream

Risk: Future code could map `VERIFIED` to `STRONG_EVIDENCE`, clean admission, or readiness.

Mitigation:

```text
Include boundary invariant tests in the next implementation:
VERIFIED keeps WEAK_EVIDENCE
MARKET_REFERENCE_ROW stays REVIEW_REQUIRED
manifest gates stay closed
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
pytest tests/agent -q
  ........................................................................ [ 58%]
  ...................................................                      [100%]
  123 passed in 0.65s
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
Decision = 348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_DRY_RUN_DESIGN_VALID
```

R7AC design is complete. The safest first implementation path is fixture-first and lower-level: generate `SourceTextEvidence` objects in tests, pass them directly into `build_row_audit_result(..., source_text_index=...)`, validate evidence_index metadata via tempfile only, and validate review_queue compact fields in memory. Defer committed JSON sidecar fixtures and any loader until the object-level dry-run is reviewed.

## Recommended next task

```text
348N-R7AD source_text sidecar fixture dry-run implementation
```

Recommended R7AD scope:

```text
add compact tests using in-test SourceTextEvidence objects
cover positive and negative fixture cases from this design
validate evidence_index metadata with tempfile
validate review_queue compact fields in memory
keep full source_text out of serialized outputs
do not run workbook rerun
do not add loader / CLI / OCR / MinerU / LLM / VLM
keep readiness gates closed
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7AC source_text sidecar fixture / dry-run design completed
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 123 passed in 0.65s
files_modified（修改文件数）= 1，only this design report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7AC design report
fixture_design_result（fixture设计结果）= PASS，先用 in-test SourceTextEvidence objects；后续如需文件，使用 tests/agent/fixtures/source_text_sidecars/ 下的 tiny JSON
dry_run_design_result（dry-run设计结果）= PASS，优先 lower-level helpers，不跑真实 workbook，不写项目 output
evidence_index_validation_design_result（证据索引验证设计结果）= PASS，tempfile 写 JSON，验证 metadata/hash/char_count/status，断言 full source_text absent
review_queue_validation_design_result（复核队列验证设计结果）= PASS，内存 dict 验证 compact fields，断言 full source_text absent
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= 348N-R7AD source_text sidecar fixture dry-run implementation
```
