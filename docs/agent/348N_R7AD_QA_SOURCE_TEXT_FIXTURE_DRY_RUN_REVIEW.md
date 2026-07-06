# 348N-R7AD-QA source_text fixture dry-run review

## Task ID

```text
348N-R7AD-QA source_text fixture dry-run review
```

## Recommended reasoning level used

```text
recommended_reasoning_level = max
reason = R7AD-QA reviews controlled fixture dry-run coverage for source_text wiring. It must verify positive/negative coverage, metadata-only outputs, full-text exclusion, and closed clean/readiness boundaries.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 9cd4ef6..bec322e
  Fast-forward
  created docs/codex_tasks/348N_R7AD_QA_source_text_fixture_dry_run_review.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  bec322e docs: update handoff after R7AD
  c2edfb5 docs: refresh plain-language progress after R7AD
  dba2b8b docs: sync progress after R7AD
  59b9aab docs: add R7AD QA task
  9cd4ef6 test: add source text fixture dry-run coverage
  1f9ee32 docs: update handoff after R7AC
  afb0ee0 docs: refresh plain-language progress after R7AC
  381a457 docs: sync progress after R7AC
  2d11011 docs: add R7AD source text fixture dry-run task
  a3cc7f8 docs: add R7AC source text fixture design
  28c626a docs: update handoff after R7AB QA
  b859afc docs: refresh plain-language progress after R7AB QA
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
- `docs/codex_tasks/348N_R7AD_QA_source_text_fixture_dry_run_review.md`
- `docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md`
- `docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md`
- `docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md`
- `docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md`

R7AD implementation reviewed:

- `tests/agent/test_agent_excel_intake_audit_348a.py`
- commit `9cd4ef6 test: add source text fixture dry-run coverage`

Read-only implementation boundary files:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/conftest.py`
- `datefac_agent/audit/output_schema_guardrails.py`
- `datefac_agent/review/clean_candidate_policy.py`

## Fixture dry-run coverage review

QA result: **VALID**.

R7AD is tests-only. The R7AD commit scope is exactly:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

No production helper, loader, config, dependency, docs, input, output, temp, data, or legacy file was modified by R7AD.

R7AD uses in-test `SourceTextEvidence` objects via `_make_r7ab_source_text(...)`, then passes them directly through `build_row_audit_result(..., source_text_index=...)`. It does not create JSON/JSONL fixture files and does not add a file-backed loader.

R7AD exercises lower-level helpers:

```text
audit_evidence_presence(...)
build_row_audit_result(...)
write_evidence_index(...) inside tempfile
build_review_queue_rows(...) in memory
build_manifest(...) for closed readiness gates
```

It does not call `run_pilot(...)`, does not run a real workbook-family rerun, and does not run MinerU, OCR, LLM, VLM, or PDF extraction.

## Positive case review

QA result: **VALID**.

R7AD confirms a trusted fixture can be selected and used:

```text
test_r7ad_fixture_dry_run_evidence_index_metadata_without_full_text
  source_text_id = r7ad-positive-source-text
  source_document_id = demo.pdf
  page_number = 12
  locator = 营业收入(百万元)
  text_kind = snippet_text
  trusted_source = true
  agreement_status = VERIFIED
  source_text_status = AVAILABLE_USED
  source_text_used_for_agreement = true
```

R7AB baseline tests remain present and also confirm:

```text
trusted matching source_text -> VERIFIED
```

## Negative case review

QA result: **VALID**.

R7AD parameterizes the required negative selection cases:

```text
missing source_text -> UNVERIFIED / MISSING / not used
source_id mismatch -> UNVERIFIED / SOURCE_ID_MISMATCH / not used
page_number mismatch -> UNVERIFIED / PAGE_NUMBER_MISMATCH / not used
locator mismatch -> UNVERIFIED / LOCATOR_MISMATCH / not used
untrusted source_text -> UNVERIFIED / UNTRUSTED / not used
empty source_text -> UNVERIFIED / EMPTY_TEXT / not used
```

It also adds:

```text
test_r7ad_workbook_raw_text_decoys_are_not_trusted_source_text
```

This test confirms workbook raw fields such as `value_text_original`, `source_page`, `来源页`, `页码`, and `摘录/说明` are not treated as trusted `source_text`.

Trusted numeric mismatch is covered by:

```text
test_r7ad_fixture_dry_run_numeric_mismatch_can_disagree_without_evidence_promotion
  agreement_status = DISAGREED
  source_text_status = AVAILABLE_USED
  source_text_used_for_agreement = true
  evidence_level = WEAK_EVIDENCE
```

This is acceptable because `DISAGREED` is an agreement signal only and does not alter clean/readiness boundaries.

## Evidence index validation review

QA result: **VALID**.

R7AD writes evidence index JSON only inside `tempfile.TemporaryDirectory()`. No project `output/` artifact is created or committed.

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

The positive row validates metadata for selected trusted source_text. The missing row validates deterministic unavailable metadata:

```text
source_text_status = MISSING
source_text_id = null
source_text_used_for_agreement = false
source_text_unavailable_reason = MISSING
```

## Review queue validation review

QA result: **VALID**.

R7AD validates review queue output in memory through `build_review_queue_rows(...)`; it does not write a review queue file.

Validated compact fields include:

```text
agreement_status
source_text_status
source_text_page_number
source_text_locator
source_text_unavailable_reason
```

For a selected trusted fixture:

```text
agreement_status = VERIFIED
source_text_status = AVAILABLE_USED
source_text_page_number = 12
source_text_locator = 营业收入(百万元)
source_text_unavailable_reason = ""
```

For missing fixture source_text:

```text
agreement_status = UNVERIFIED
source_text_status = MISSING
source_text_page_number = ""
source_text_locator = ""
source_text_unavailable_reason = MISSING
```

## Full source_text serialization review

QA result: **VALID**.

R7AD asserts full fixture text is absent from serialized evidence index JSON:

```text
assert source_text.text not in raw_payload
```

R7AD also asserts full fixture text is absent from serialized in-memory review queue rows:

```text
serialized_queue = json.dumps(queue_rows, ensure_ascii=False)
assert source_text.text not in serialized_queue
```

Reviewed `datefac_agent/delivery/evidence_index_writer.py` and `datefac_agent/review/review_queue_builder.py`; both write metadata/compact fields and do not serialize `source_text.text`.

## Boundary policy review

QA result: **VALID**.

R7AD proves `VERIFIED` remains separate from evidence promotion and clean admission:

```text
test_r7ad_verified_fixture_keeps_market_policy_and_readiness_closed
  agreement_status = VERIFIED
  evidence_level = WEAK_EVIDENCE
  clean_candidate_type = REVIEW_REQUIRED
```

Read-only review confirms:

1. `clean_candidate_policy.py` does not use `agreement_status` for admission.
2. `MARKET_REFERENCE_ROW` still returns `REVIEW_REQUIRED`.
3. `output_schema_guardrails.py` forbids `MARKET_REFERENCE_ROW` in clean data.
4. qualitative_facts admission was not broadened.
5. evidence-level promotion was not changed.

QA answer:

```text
VERIFIED -> not STRONG_EVIDENCE
VERIFIED -> not clean admission
VERIFIED -> not MARKET_REFERENCE_ROW acceptance
```

## Readiness gates review

QA result: **VALID / CLOSED**.

R7AD checks a manifest built through `build_manifest(...)`:

```text
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
```

Read-only review confirms `tools/run_agent_excel_intake_audit_348a.py` keeps the same readiness defaults and `output_schema_guardrails.py` still enforces closed readiness gates.

External-call counters remain zero in the runner contract:

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

No R7AD test or reviewed path invokes MinerU, OCR, LLM, VLM, workbook rerun, or PDF extraction.

## Test review

QA result: **VALID**.

R7AD added focused tests while preserving prior R7X/R7Y/R7Z/R7AB tests:

```text
test_r7ad_fixture_dry_run_evidence_index_metadata_without_full_text
test_r7ad_fixture_dry_run_negative_selection_cases_stay_unverified
test_r7ad_fixture_dry_run_numeric_mismatch_can_disagree_without_evidence_promotion
test_r7ad_fixture_dry_run_review_queue_compact_fields_without_full_text
test_r7ad_workbook_raw_text_decoys_are_not_trusted_source_text
test_r7ad_verified_fixture_keeps_market_policy_and_readiness_closed
```

`pytest tests/agent -q` passes with all R7X/R7Y/R7Z/R7AB/R7AD coverage together:

```text
134 passed in 0.68s
```

## Compatibility risk review

No blocking compatibility issue found.

Residual risks remain appropriate for future tasks:

1. R7AD validates fixture-level source_text wiring, not a production sidecar file loader.
2. R7AD intentionally does not validate real workbook family reruns.
3. `page_text` remains broad by design; future real sidecars should prefer table-row or snippet locators when available.
4. `VERIFIED` is still an agreement-status signal only; future work must not map it to evidence promotion, clean admission, or readiness without a separate reviewed task.
5. Evidence index and review queue serializers must continue to exclude full `source_text.text`.

Risk level: **acceptable for R7AD-QA**.

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
  134 passed in 0.68s
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
Decision = 348N_R7AD_QA_CONFIRMED_SOURCE_TEXT_FIXTURE_DRY_RUN_VALID
```

R7AD-QA confirms the source_text fixture dry-run implementation is valid. R7AD is tests-only, uses in-test `SourceTextEvidence` objects, avoids loader/workbook rerun/external extraction, covers trusted positive and conservative negative selection paths, validates evidence_index metadata with tempfile, validates review_queue compact fields in memory, excludes full source_text from serialized outputs, and keeps `VERIFIED` separate from `STRONG_EVIDENCE`, clean admission, and readiness.

## Recommended next task

```text
348N-R7AE source_text file-backed sidecar loader design
```

Recommended scope:

```text
design-only first
define a tiny test-only JSON sidecar contract under tests/agent/fixtures/source_text_sidecars/
preserve metadata-only serialization
do not run real workbook reruns yet
keep readiness gates closed
```

Do not jump to production readiness.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7AD-QA confirms source_text fixture dry-run coverage is valid
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 134 passed in 0.68s
files_modified（修改文件数）= 1，only this R7AD-QA report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7AD-QA report
fixture_dry_run_result（fixture dry-run结果）= PASS，tests-only，in-test SourceTextEvidence objects，无 loader / workbook rerun
evidence_index_validation_result（证据索引验证结果）= PASS，tempfile metadata/status/hash/char_count/used flag validation，no full source_text
review_queue_validation_result（复核队列验证结果）= PASS，in-memory compact fields validation，no full source_text
full_text_serialization_result（全文序列化结果）= PASS，evidence_index / review_queue 均断言 full source_text absent
qa_result（QA结果）= VALID
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= 348N-R7AE source_text file-backed sidecar loader design
```
