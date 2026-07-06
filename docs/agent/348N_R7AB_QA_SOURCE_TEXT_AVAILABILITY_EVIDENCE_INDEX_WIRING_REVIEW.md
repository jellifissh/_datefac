# 348N-R7AB-QA source_text availability / evidence index wiring review

## Task ID

```text
348N-R7AB-QA source_text availability / evidence index wiring review
```

## Recommended reasoning level used

```text
recommended_reasoning_level = max
reason = R7AB-QA reviews the first trusted source_text metadata and checker injection implementation. It must verify conservative defaults, metadata-only serialization, and closed clean/readiness boundaries.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  first attempt failed with transient TLS/schannel handshake error
  retry succeeded:
    Updating 12a4726..dc6e478
    Fast-forward
    created docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  dc6e478 docs: update handoff after R7AB
  2b26d25 docs: refresh plain-language progress after R7AB
  627eb77 docs: sync progress after R7AB
  c13bc7e docs: add R7AB QA task
  12a4726 feat: wire trusted source text metadata
  37316d5 docs: update handoff after R7AA
  2630b1f docs: refresh plain-language progress after R7AA
  35684d1 docs: sync progress after R7AA
  a60d870 docs: add R7AB source text wiring task
  e5ec327 docs: add R7AA source text integration design
  c1cee01 docs: update handoff after R7Z QA
  ae5a24a docs: refresh plain-language progress after R7Z QA
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
- `docs/codex_tasks/348N_R7AB_QA_source_text_availability_evidence_index_wiring_review.md`
- `docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md`
- `docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md`
- `docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md`
- `docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md`
- `docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md`

R7AB implementation and tests:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `tests/agent/conftest.py`

Additional read-only boundary files:

- `datefac_agent/intake/excel_intake.py`
- `datefac_agent/audit/output_schema_guardrails.py`
- `datefac_agent/review/clean_candidate_policy.py`

## Source text contract review

R7AB defines `SourceTextEvidence` in `datefac_agent/schemas/audit_models.py` with:

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
char_count
```

QA result: **VALID**.

Findings:

1. The contract is a separate sidecar-style dataclass, not a field on `SpreadsheetRow`.
2. `text_sha256` is derived from exact `text` when not provided.
3. `char_count` is derived from exact `text` when not provided.
4. `trusted_source` defaults to `False`, so source_text is not trusted by presence alone.
5. `SourceTextSelection` records `status`, optional `source_text`, `used_for_agreement`, and deterministic `unavailable_reason`.

This satisfies the minimum R7AA contract.

## Source text selection review

Reviewed `select_source_text_for_row(...)` in `datefac_agent/audit/evidence_checker.py`.

Selection requires:

```text
explicit/page provenance with parsed page_number
source_text_index provided
source_text.source_document_id == source_pdf EvidenceRef.source_id
source_text.page_number == explicit EvidenceRef.page_number
locator compatibility
trusted_source == true
non-empty text
```

Failure status mapping:

```text
no explicit/page provenance -> NO_EXPLICIT_PAGE_PROVENANCE
no source_text_index / no records -> MISSING
source id mismatch -> SOURCE_ID_MISMATCH
page mismatch -> PAGE_NUMBER_MISMATCH
locator mismatch -> LOCATOR_MISMATCH
untrusted -> UNTRUSTED
empty text -> EMPTY_TEXT
valid binding -> AVAILABLE_USED
```

QA result: **VALID**.

Question answers:

1. Explicit/page provenance is required: **yes**.
2. Parsed `page_number` is required: **yes**.
3. Source document id is matched against the `source_pdf` EvidenceRef source id: **yes**.
4. Page number is matched against the explicit EvidenceRef page number: **yes**.
5. Untrusted source_text is rejected and keeps agreement `UNVERIFIED`: **yes**.
6. Empty source_text is rejected and keeps agreement `UNVERIFIED`: **yes**.
7. Locator mismatch is rejected for non-page text when both locator values are available: **yes**.

Residual compatibility note: `page_text` is treated as page-level compatible without strict locator equality. This matches the broad page-text design, but row-level / coordinate-aware matching remains future work before any evidence promotion.

## Agreement checker injection review

Reviewed `build_row_audit_result(...)` in `datefac_agent/review/review_queue_builder.py`.

Behavior:

```text
if selection.used_for_agreement and selection.source_text:
    classify_agreement_status(..., source_text=selection.source_text.text)
else:
    classify_agreement_status(...)
```

QA result: **VALID**.

Findings:

1. Without a `source_text_index`, default page provenance rows remain `UNVERIFIED`.
2. With trusted matching source_text, checker can produce `VERIFIED`.
3. With trusted matching source_text and numeric mismatch, checker can produce `DISAGREED`.
4. Mismatch / untrusted / empty source_text never reaches checker, so agreement remains conservative.
5. `tools/run_agent_excel_intake_audit_348a.py` adds an optional `source_text_index` parameter but `run_pilot(...)` does not pass one, so normal runner behavior remains unchanged.

## Evidence index metadata review

Reviewed `datefac_agent/delivery/evidence_index_writer.py`.

R7AB adds row-level metadata:

```text
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

QA result: **VALID**.

Findings:

1. Full `source_text.text` is not serialized.
2. The metadata is enough to audit used / unavailable / mismatch states.
3. Existing `raw_values` behavior remains unchanged; it is workbook payload, not source_text sidecar text.
4. R7AB test `test_r7ab_evidence_index_serializes_metadata_without_full_source_text` verifies full text exclusion.

## Review queue compact fields review

Reviewed `build_review_queue_rows(...)`.

R7AB adds compact fields:

```text
agreement_status
source_text_status
source_text_page_number
source_text_locator
source_text_unavailable_reason
```

QA result: **VALID**.

Findings:

1. Review queue does not serialize full source_text.
2. Added fields are compact reviewer triage metadata.
3. Existing required review fields remain present.
4. `output_schema_guardrails.py` still requires only `decision`, `clean_candidate_type`, and `evidence_level`, so the additive fields do not weaken guardrails.
5. R7AB test `test_r7ab_review_queue_adds_compact_source_text_fields_without_full_text` verifies no full text leakage.

## Boundary policy review

QA result: **VALID**.

Reviewed boundaries:

1. `classify_evidence_level(...)` was not changed to promote `VERIFIED` to `STRONG_EVIDENCE`.
2. `clean_candidate_policy.py` does not reference `agreement_status`.
3. `MARKET_REFERENCE_ROW` remains `REVIEW_REQUIRED`.
4. `TESTSET_SUPPORTING_ROW` remains `REVIEW_REQUIRED`.
5. qualitative_facts admission was not broadened.
6. Excel raw fields such as `value_text_original`, `source_page`, `来源页`, `页码`, and `摘录/说明` are not used as trusted source_text.
7. The runner did not add OCR / PDF extraction / LLM / VLM / MinerU calls.

R7AB test `test_r7ab_verified_still_does_not_change_evidence_level_or_market_policy` confirms:

```text
agreement_status = VERIFIED
evidence_level = WEAK_EVIDENCE
MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
```

## Readiness gates review

QA result: **VALID / CLOSED**.

Reviewed `tools/run_agent_excel_intake_audit_348a.py` and `datefac_agent/audit/output_schema_guardrails.py`.

Readiness defaults remain:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

External-call counters remain:

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

R7AB did not connect `VERIFIED` to readiness.

## Test review

QA result: **VALID**.

R7AB test coverage includes:

```text
no source_text sidecar -> UNVERIFIED
trusted matching source_text -> VERIFIED
trusted matching source_text with mismatch -> DISAGREED
source_id mismatch -> UNVERIFIED
page_number mismatch -> UNVERIFIED
locator mismatch -> UNVERIFIED
untrusted source_text -> UNVERIFIED
empty source_text -> UNVERIFIED
no explicit page provenance -> MISSING
evidence_index metadata without full text
review_queue compact fields without full text
VERIFIED does not change evidence_level or MARKET_REFERENCE_ROW policy
```

Existing R7X/R7Y/R7Z tests pass together under `pytest tests/agent -q`.

`tests/agent/conftest.py` review:

```text
only inserts project root into sys.path for direct pytest tests/agent -q invocation
does not import or modify production code
does not affect runtime runner behavior
```

QA result for `conftest.py`: **VALID / test-only bootstrap**.

## Compatibility risk review

No blocking compatibility issue found.

Known residual risks:

1. Row-level numeric agreement is still not period-aware or coordinate-aware.
2. `page_text` locator compatibility is intentionally broad; future source_text pipeline work should prefer table-row/snippet text with stronger locators.
3. `SourceTextSelection` stores a `SourceTextEvidence` object in memory, but standard evidence_index/review_queue serialization excludes full text. Future serializers should preserve this rule.
4. `VERIFIED` remains an agreement-status signal only; future code must not map it to evidence promotion, clean admission, or readiness without a separate reviewed task.

Risk level: **acceptable for R7AB-QA**.

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
  123 passed in 0.67s
```

```text
git status -sb
  before report creation:
    ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  after report creation:
    ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
    ?? docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
```

```text
git diff --stat
  before report creation:
    no output
  after report creation:
    no output because the QA report is untracked before staging
```

```text
git diff --name-only
  before report creation:
    no output
  after report creation:
    no output because the QA report is untracked before staging
```

```text
git diff --check
  before report creation:
    passed, no output
  after report creation:
    passed, no output
```

## Decision

```text
Decision = 348N_R7AB_QA_CONFIRMED_SOURCE_TEXT_WIRING_VALID
```

R7AB-QA confirms the source_text availability and evidence index wiring implementation is valid. Trusted source_text reaches the agreement checker only after explicit provenance, source document id, page number, locator compatibility, trust, and non-empty text checks pass. Missing, mismatched, untrusted, or empty source_text remains conservative. Full source_text is not serialized by default. `VERIFIED` remains separate from `STRONG_EVIDENCE`, clean admission, and readiness.

## Recommended next task

```text
348N-R7AC source_text sidecar fixture integration / dry-run design
```

Recommended scope:

```text
define a small fixture sidecar format
exercise audit_workbook(..., source_text_index=...) without workbook rerun
keep full text out of normal evidence_index / review_queue
keep readiness gates closed
```

Do not jump to production readiness.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7AB-QA confirms source_text availability / evidence index wiring is valid
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 123 passed in 0.67s
files_modified（修改文件数）= 1，only this QA report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7AB-QA report
source_text_contract_result（source_text契约结果）= PASS，SourceTextEvidence / SourceTextSelection 契约满足 R7AA 最小要求
source_text_selection_result（source_text选择结果）= PASS，仅 explicit provenance + source_id/page_number/locator/trust/non-empty 绑定通过时使用
agreement_injection_result（一致性检查注入结果）= PASS，仅 AVAILABLE_USED 时注入 checker；默认仍 UNVERIFIED
evidence_index_wiring_result（证据索引接线结果）= PASS，写入 source_text metadata/hash/char_count/status，不写全文
review_queue_wiring_result（复核队列接线结果）= PASS，compact fields 安全添加，不写全文
full_text_serialization_result（全文序列化结果）= PASS，标准 evidence_index / review_queue 不序列化 full source_text
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
qa_result（QA结果）= VALID
recommended_next_task（推荐下一任务）= 348N-R7AC source_text sidecar fixture integration / dry-run design
```
