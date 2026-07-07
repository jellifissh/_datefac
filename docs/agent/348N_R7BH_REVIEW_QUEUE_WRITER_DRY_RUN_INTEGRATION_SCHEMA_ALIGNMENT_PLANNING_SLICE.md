# 348N-R7BH review-queue writer dry-run integration schema alignment planning slice

## Task ID

```text
348N-R7BH review-queue writer dry-run integration schema alignment planning slice
```

Task type: docs-only-schema-alignment-planning.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward d4da21a..92ac49c; task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -25
PASS: latest commit before this report is 92ac49c docs: add R7BH schema alignment planning task.
```

Worktree remained clean after pull, so the task continued.

## Files reviewed

Required context reviewed:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7BH_review_queue_writer_dry_run_integration_schema_alignment_planning_slice.md`
- `docs/agent/348N_R7BG_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BG_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT.md`
- `docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md`
- `docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md`
- `docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md`

Current slices reviewed read-only:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`

Related modules reviewed read-only for boundary context:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BG-QA recap

R7BG-QA confirmed that the R7BG handoff checkpoint is accurate and boundary-safe. The current chain is intentionally narrow:

```text
validated adapter candidate output
-> test-only dry-run integration boundary
-> R7BC test-only in-memory writer dry-run preview
```

Important R7BG-QA conclusions retained by this plan:

- Integration and writer logic remain test-only and dry-run-only.
- Valid adapter candidates can reach writer preview only under explicit test tokens.
- Missing/invalid tokens, disabled path, direct writer-preview-shaped payloads, raw MinerU/Excel/parser payloads, full source text, readiness-open payloads, clean_data intent, and schema mismatch fail closed.
- Writer dry-run preview must remain `ENABLED_TEST_ONLY_DRY_RUN`, `dry_run_only = true`, readiness-closed, zero-write, metadata-preserving, and review-bound.
- `VERIFIED` does not become `STRONG_EVIDENCE`, does not auto-write `clean_data`, and does not open readiness gates.

## 大白话说明

这一轮不写代码、不改测试、不建表、不落库。它只是把现在几段 test-only 链路里的字段关系画清楚：哪些字段从 adapter 来，哪些字段由 integration boundary 包起来，哪些字段由 writer dry-run preview 生成，哪些字段以后如果真要进入 `review_queue` 持久化必须保留，哪些字段绝对不能进去。

最核心的原则是：`review_queue` 是“需要复核/阻断交付”的安全通道，不是 `clean_data`，更不是生产交付。即使某条数据将来被 reviewer 修正，也必须重新 audit；即使某条数据是 `VERIFIED`，也不能因此自动进入 `clean_data` 或打开 readiness gates。

## Schema alignment scope

This planning slice aligns fields across four layers only:

1. Disabled adapter candidate output from `datefac_agent/review/production_boundary_review_queue_adapter.py`.
2. Dry-run integration boundary envelope from `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`.
3. Test-only writer dry-run preview records from `tests/agent/review_queue_writer_contract_348n.py`.
4. Future review_queue persistence shape, still unimplemented.

Out of scope:

- No production schema changes.
- No implementation.
- No database models, migrations, repositories, or storage code.
- No test or fixture edits.
- No output files.
- No MinerU/OCR/LLM/VLM/PDF extraction.
- No readiness gate changes.

## Current chain field inventory

### Adapter input boundary payload

The disabled adapter accepts only a validated discrepancy boundary output with top-level fields:

- `contract_version`
- `review_queue_items`
- `discrepancy_report_rows`
- `delivery_clean_candidates`
- `blocked_delivery_rows`
- `audit_metadata`

The adapter rejects unexpected top-level fields and forbidden nested raw/full-content fields.

### Adapter candidate output

Enabled test-only adapter output currently emits:

- `adapter_status`
- `review_queue_candidate_items`
- `discrepancy_report_candidate_rows`
- `blocked_delivery_candidate_rows`
- `delivery_reaudit_candidate_rows`
- `audit_contract`

Review queue candidate rows include compact identity, candidate, status, review, evidence-preview, lineage, audit, and blocking fields, including `review_item_id`, `source_document_id`, `source_row_id`, `candidate_metric_name`, `candidate_period`, `candidate_value`, `candidate_unit`, `agreement_status`, `subqueue`, `risk_reason`, `severity`, `review_status`, `reviewer_action`, `clean_data_eligible`, `delivery_blocked`, `evidence_preview`, `evidence_preview_sha256`, `matched_locator`, `matched_text_sha256`, `run_id`, `adapter_version`, `input_file_hashes`, `audit_hash`, `adapter_contract_version`, and `created_from`.

`audit_contract` includes run and contract metadata, counts, closed readiness gates, zero external-call counts, boundary flags, and `adapter_audit_hash`.

### Integration boundary envelope

The R7BE integration boundary wraps a valid adapter candidate output and a valid R7BC writer preview into:

- `integration_status`
- `dry_run_only`
- `integration_contract_version`
- `adapter_audit_contract`
- `writer_dry_run_preview`
- `integration_summary`

`integration_summary` carries `writer_contract_version`, `source_adapter_contract_version`, `run_id`, `adapter_version`, `input_file_hashes`, `adapter_audit_hash`, `review_queue_dry_run_record_count`, `writer_preview_hash`, dry-run action counts, blocked/re-audit counts, status counts, closed readiness gates, zero external-call counts, closed boundary flags, and `integration_envelope_hash`.

### Writer dry-run preview records

R7BC writer preview emits top-level:

- `writer_status`
- `dry_run_only`
- `review_queue_dry_run_records`
- `dry_run_summary`

Each dry-run record currently includes:

- `review_item_id`
- `run_id`
- `source_file_hash`
- `input_file_hashes`
- `adapter_version`
- `contract_version`
- `adapter_contract_version`
- `audit_hash`
- `metric_name`
- `period`
- `candidate_value`
- `candidate_unit`
- `agreement_status`
- `review_status`
- `reviewer_action`
- `review_reason`
- `blocked_delivery_reason`
- `evidence_preview`
- `source_trace`
- `idempotency_key`
- `dry_run_only`
- `clean_data_write_count`
- `delivery_write_count`
- `dry_run_action`
- `record_payload_hash`

### Future review_queue persistence target

Future persistence should store a metadata-first review-bound record, not raw evidence or clean delivery payload. The minimal target should retain identity, status, review, audit, idempotency, compact evidence, source trace, delivery-blocking, schema/version, and re-audit semantics.

It should not store dry-run test config, tokens, raw artifacts, full source text, direct writer preview payloads, or clean delivery/write intent.

## Field map

| Field | Source layer | Classification | Pass-through / normalized | Why it exists | Missing or malformed behavior | Future persistence may store? |
|---|---|---|---|---|---|---|
| `run_id` | Adapter `audit_metadata` -> `audit_contract` -> writer record/summary -> integration summary | Required audit metadata | Pass-through unchanged | Binds rows to one controlled audit/comparison run | Fail closed on missing, empty, or mismatch across rows/contract | Yes, required row and batch provenance |
| `adapter_version` | Adapter `audit_metadata` and candidate items | Required audit metadata | Pass-through unchanged | Identifies adapter shape that produced candidates | Fail closed on missing or mismatch with audit contract | Yes, required provenance |
| `contract_version` | Adapter input boundary and adapter/writer contracts; writer record currently uses writer contract as `contract_version` | Required but currently overloaded | Normalize naming before persistence: use namespaced contract fields | Prevents shape drift and unknown contracts | Fail closed on unknown contract or ambiguous layer mapping | Yes only if meaning is explicitly row schema/writer contract; otherwise use namespaced fields |
| `integration_boundary_version` | R7BE `integration_contract_version` | Derived/test-only envelope metadata | Pass-through in dry-run envelope | Identifies integration boundary wrapper version | Fail closed if unexpected when integration is used | Not in production review_queue row; yes in dry-run/run audit metadata |
| `writer_contract_version` | R7BC writer config and dry-run summary | Required writer metadata | Pass-through unchanged | Identifies dry-run writer preview schema | Fail closed if missing, unknown, or mismatched | Yes, as writer/schema provenance |
| `input_file_hashes` | Adapter `audit_metadata` -> all candidate rows/audit_contract -> writer record | Required audit metadata | Pass-through unchanged; keys sorted only for idempotency hashing | Reproducibility and source identity without raw files | Fail closed if missing, empty, non-object, or row mismatch | Yes, compact hash map allowed |
| `source_file_hash` | Writer record derived from `input_file_hashes` preferred keys | Derived compact source identity | Deterministically derived | Gives a single source hash for row-level lookup/indexing | Fail closed if no usable input hashes; future should reject unstable selection | Yes, derived compact field |
| `review_item_id` | Boundary `review_queue_items` -> adapter candidate -> writer record | Required row identity | Pass-through unchanged | Stable human-review item identity | Fail closed on missing, empty, duplicate where idempotency conflicts | Yes, required primary logical identity |
| `audit_hash` | Boundary review item -> adapter candidate -> writer record | Required audit integrity metadata | Pass-through unchanged | Detects audit-row provenance drift | Fail closed on missing/empty or idempotency collision with different payload | Yes, required |
| `idempotency_key` | Writer dry-run record | Derived required writer field | Deterministic hash over contract/run/item/status/audit/input hashes | Prevents duplicate writes and detects conflicting retries | Fail closed if missing, malformed, duplicated in batch, or collision with different payload | Yes, unique key / conflict detector |
| `metric_name` | Adapter `candidate_metric_name` -> writer `metric_name` | Required candidate field | Field-name normalized; value pass-through unless a future canonicalizer is explicit | Human-readable metric under review | Fail closed if missing/empty before writer; future canonicalization errors become validation errors | Yes |
| `period` | Adapter `candidate_period` -> writer `period` | Required candidate field | Field-name normalized; value pass-through unless future period normalizer is explicit | Places value in reporting period | Fail closed if missing/empty; malformed period should fail closed or mark validation error before persistence | Yes |
| `candidate_value` | Adapter candidate item -> writer record | Required candidate field | Pass-through as candidate string | Preserves the disputed extracted value for review | Fail closed if missing/empty | Yes, as original candidate value |
| `normalized_candidate_value` | Not currently emitted by R7BC; future deterministic value normalizer | Derived optional-to-required-later | Normalize deterministically from `candidate_value` only with explicit unit/format rules | Enables numeric comparison and duplicate detection | If normalization fails, do not invent value; record validation error and keep row review-bound | Yes when deterministic; otherwise nullable with validation error |
| `agreement_status` | Adapter candidate item -> writer record | Required status | Pass-through unchanged; must be non-`VERIFIED` for review_queue candidates | Drives review queue routing and delivery blocking | Fail closed on unknown status or `VERIFIED` review_queue candidate | Yes |
| `review_status` | Adapter candidate item/block rows -> writer record | Required review workflow state | Pass-through unchanged | Tracks whether review is open/resolved/source-check | Fail closed on missing/malformed or inconsistent reviewer action | Yes |
| `review_reason` | Adapter `risk_reason` -> writer `review_reason` | Required derived/name-normalized field | Field-name normalized; value pass-through | Explains why item is in review_queue | Fail closed if missing/empty in candidate | Yes |
| `reviewer_action` | Adapter `reviewer_action` / source `reviewer_decision` | Optional or conditionally required | Normalize empty to blank/null; validate against enum when present | Captures human review decision/action | Fail closed if unsupported or inconsistent with `review_status` | Yes nullable; required for resolved rows |
| `blocked_delivery_reason` | Adapter blocked rows or writer default by status | Required delivery-blocking field | Derived deterministically when not explicitly provided | Prevents unresolved row from formal delivery | Fail closed if unresolved persisted row lacks blocking reason | Yes, required for unresolved rows |
| `re_audit_required` | Current `requires_reaudit_before_clean_delivery` in delivery re-audit rows; writer summary count | Required for corrected/resolved handoff; not in review dry-run record yet | Normalize future row-level name to `re_audit_required` | Ensures human correction cannot bypass audit | Fail closed if corrected/resolved clean candidate lacks true re-audit requirement | Yes for resolved/corrected review records and delivery handoff metadata |
| `evidence_preview` | Adapter item/row -> writer record | Required bounded evidence field | Whitespace-normalized and bounded by preview limit | Lets reviewer see compact evidence context | Fail closed if missing, oversized, or full-text-like; no silent full dump | Yes, bounded only |
| `source_trace` | Writer record derived from adapter source/evidence metadata | Required compact lineage | Deterministically assembled compact dict | Links review item to source document/row/locator/hash without raw content | Fail closed if required source identity/hash missing or contains raw text | Yes, compact only |
| `dry_run_only` | Writer preview, dry-run record, integration envelope/summary | Required dry-run boundary flag | Pass-through/validated true in dry-run outputs | Proves current operation performs no write | Fail closed if false/missing in dry-run preview | No in actual persisted review_queue row; yes only in dry-run preview/run audit output |
| `readiness_gates` | Adapter audit contract, writer summary, integration summary | Required boundary metadata | Pass-through closed constants | Prevents accidental production/client readiness | Fail closed if any gate opens or shape differs | Store in run/batch audit metadata; not needed per row unless denormalized for audit |
| `schema_version` | Fixtures today; future persistence schema | Required future persistence field | Explicit stable version, not inferred from fixture name | Allows migrations and compatibility checks | Fail closed on unknown/missing future schema version | Yes, required for persisted review_queue records |
| `validation_errors` | Current code raises exceptions; future failed preview/report may expose sanitized errors | Optional failure-output metadata; forbidden in successful row if it hides invalid data | Normalize to bounded machine-readable error codes/messages | Helps debug rejected batches without partial writes | Batch fails closed; errors may be emitted only in dry-run failure report, not partial persistence | No for successful persisted rows; yes in rejected dry-run report/manifest |

Additional fields that should remain aligned even though they are not in the required R7BH field list:

- `source_document_id`, `source_row_id`, `candidate_unit`, `severity`, `subqueue`, `source_text_status`, `evidence_type`, `matched_locator`, `matched_text_sha256`, `evidence_preview_sha256`, `adapter_contract_version`, `adapter_audit_hash`, `record_payload_hash`, `dry_run_action`, `clean_data_write_count`, `delivery_write_count`, `external_call_counts`, and `boundary_flags`.
- Future persistence should keep compact identity/hash/status/blocking fields and reject write-count fields unless the writer is still in dry-run/report mode.

## Required fields

For future persisted review_queue records, the minimal required row fields should be:

- `schema_version`
- `review_item_id`
- `run_id`
- `source_file_hash`
- `input_file_hashes`
- `adapter_version`
- `writer_contract_version`
- `audit_hash`
- `idempotency_key`
- `source_document_id`
- `source_row_id`
- `metric_name`
- `period`
- `candidate_value`
- `candidate_unit`
- `agreement_status`
- `review_status`
- `review_reason`
- `severity`
- `blocked_delivery_reason`
- `evidence_preview`
- `source_trace`
- `clean_data_eligible = false`

For future batch/run metadata, the minimal required fields should be:

- `run_id`
- `schema_version`
- `adapter_version`
- `writer_contract_version`
- `adapter_contract_version`
- `input_file_hashes`
- `adapter_audit_hash`
- row/status counts
- `readiness_gates`
- `external_call_counts`
- `boundary_flags`
- batch/audit hash

## Optional and derived fields

Optional or derived fields should remain deterministic and explicitly documented:

- `normalized_candidate_value`: derived only by a deterministic normalizer; never guessed.
- `reviewer_action`: optional while `review_status = OPEN`; required for resolved statuses.
- `re_audit_required`: required for corrected/resolved clean handoff; may be absent on open unresolved queue rows only if blocked reason already marks delivery blocked.
- `source_trace.adapter_item_id`: useful if the adapter generated it, but future persistence should not require it if another validated adapter shape replaces it.
- `integration_boundary_version`: useful for dry-run run audit, not required for real persistence if the production path no longer uses the test-only boundary.
- `validation_errors`: allowed only in rejected dry-run output/report, not in successful review_queue persistence.
- `dry_run_action` and `record_payload_hash`: dry-run preview/idempotency planning fields; future real writer may convert them to write plan/result metadata, not row content.

## Forbidden fields

These fields or payload classes must not pass into review_queue persistence or dry-run preview as stored full content:

- `full source_text`
- `raw MinerU output`
- `raw Excel workbook data`
- `raw parser payload`
- `raw LLM/VLM response`
- `clean_data write intent`
- `formal delivery/export payload`
- `production writer config`
- `open readiness gate override`
- `user-provided direct writer preview`

Concrete forbidden keys already guarded in current code include `source_text`, `full_source_text`, `source_text_full`, `full_text`, `raw_source_text`, `raw_mineru_block`, `raw_mineru_artifact`, `content_list_v2`, `full_table_html`, `raw_pdf_text`, `raw_excel_row`, `raw_datefac_excel_row`, `datefac_excel_rows`, `workbook_sheets`, `worksheets`, `cells`, `blocks`, `extracted_pages`, `extracted_text`, `html`, `markdown`, `mineru_output`, `ocr_output`, `page_texts`, `parser_output`, `pdf_parser_output`, `pdf_pages`, `raw_pdf_pages`, `table_blocks`, `tables`, and `text_layer`.

Future schema alignment should keep these forbidden by default and should add equivalents for any new raw artifact naming before implementation.

## Pass-through fields

The following fields should pass through unchanged across accepted layers:

- `run_id`
- `adapter_version`
- `input_file_hashes`
- `review_item_id`
- `audit_hash`
- `agreement_status`
- `review_status`
- `candidate_value`
- `candidate_unit`
- `evidence_preview` after deterministic bounding/normalization
- `matched_locator`
- `matched_text_sha256`
- `evidence_preview_sha256`
- closed `readiness_gates`
- zero `external_call_counts`
- closed `boundary_flags`

Any mismatch between row fields and the audit contract should fail closed before future persistence.

## Normalization rules

Field naming should normalize deterministically at layer boundaries:

- `candidate_metric_name` becomes `metric_name` in writer/persistence records.
- `candidate_period` becomes `period` in writer/persistence records.
- `risk_reason` becomes `review_reason` in writer/persistence records.
- `review_subqueue` becomes `subqueue` in adapter candidates; future persistence should pick one canonical name and reject the other unless explicitly mapped.
- `reviewer_decision` becomes `reviewer_action`; empty action remains blank/null only for `OPEN` review status.
- `requires_reaudit_before_clean_delivery` should become `re_audit_required` if added to future persisted review records.
- `contract_version` must be namespaced: `adapter_contract_version`, `writer_contract_version`, `integration_boundary_version`, and persisted `schema_version` must not be collapsed into one ambiguous field.
- `evidence_preview` may be whitespace-normalized and bounded; full text must not be silently truncated into persistence.
- `idempotency_key` must be a deterministic hash over stable fields only; timestamps, execution IDs, database IDs, and dry-run timestamps are excluded.

## Idempotency and duplicate-prevention fields

Current writer dry-run idempotency uses:

- writer contract version
- `run_id`
- `review_item_id`
- `source_row_id`
- `agreement_status`
- `audit_hash`
- sorted `input_file_hashes`

Future persistence should preserve or deliberately version this formula. The persisted record should store:

- `idempotency_key`
- `record_payload_hash` or equivalent immutable row payload hash
- `audit_hash`
- `review_item_id`
- `run_id`
- `input_file_hashes`
- `schema_version`

Duplicate behavior should be:

- Same idempotency key + same payload hash: no-op / duplicate skip.
- Same idempotency key + different payload hash: conflict, fail closed, no partial write.
- Duplicate idempotency key inside the same batch: fail closed.
- Any non-deterministic input to idempotency: fail closed.

## Audit metadata fields

Audit metadata must remain compact and reproducible. Required metadata includes:

- `run_id`
- `adapter_version`
- `adapter_contract_version`
- `writer_contract_version`
- `integration_boundary_version` for dry-run envelopes
- `input_file_hashes`
- `source_file_hash`
- `adapter_audit_hash`
- `audit_hash`
- `review_queue_candidate_count` / persisted record count
- status counts
- blocked delivery count
- re-audit required count
- closed `readiness_gates`
- zero `external_call_counts`
- closed `boundary_flags`

Audit metadata should pass through unchanged from validated structures. Future writers should not recompute it from raw artifacts.

## Evidence preview and source_text boundary

Allowed:

- bounded `evidence_preview`
- `evidence_preview_sha256`
- `matched_locator`
- `matched_text_sha256`
- compact `source_trace`
- source document/row identifiers
- source/input file hashes

Forbidden:

- full `source_text`
- raw page text
- raw MinerU block text
- full table HTML
- raw Excel rows/workbook dumps
- parser/OCR/LLM/VLM raw response bodies
- raw PDF text layer dumps

The safe rule is: preview plus hashes may be persisted; full content remains outside review_queue persistence and outside dry-run preview serialization.

## clean_data safety boundary

Schema alignment must keep review_queue and clean_data separate:

- `VERIFIED` must not imply `STRONG_EVIDENCE`.
- `VERIFIED` must not auto-write `clean_data`.
- `clean_data_eligible = true` is forbidden in current adapter/writer inputs.
- `clean_data_admitted = true` and `delivery_clean_admitted = true` are forbidden at the review_queue writer boundary.
- Future review_queue persistence must not write clean_data, even for corrected rows.
- Corrected rows may only move toward clean delivery through an explicit later policy gate plus re-audit.

## Delivery gate and blocked_delivery_reason fields

Future persistence must retain delivery blocking semantics:

- Non-`VERIFIED` unresolved rows stay review-bound.
- Unresolved rows require `blocked_delivery_reason`.
- `DISAGREED` should map to evidence disagreement unresolved.
- `AMBIGUOUS` should map to evidence ambiguity unresolved.
- `MISSING_EVIDENCE` should map to evidence missing unresolved.
- `PARSE_SKIPPED` should map to parse skipped review required.
- `UNVERIFIED` should map to unverified review required.
- Delivery gate fields must remain closed and must not imply output export.

No formal delivery/export payload may be persisted as part of review_queue rows.

## Corrected row and re-audit fields

Corrected/resolved rows need special protection:

- Reviewer correction does not directly produce clean_data.
- Corrected rows must carry `re_audit_required = true` or equivalent explicit future field.
- Corrected rows must keep source/audit lineage and reviewer action.
- A corrected row may become a future clean candidate only after an explicit re-audit policy gate.
- Future persistence must distinguish unresolved review rows from corrected rows waiting for re-audit.

## Dry-run-only and test-only fields

Current test-only fields are useful in dry-run outputs but should not leak into production review_queue records as operational authority:

- test-only enable tokens
- `enabled` config flags
- `dry_run_only`
- `dry_run_preview_only`
- `writer_called`
- `integration_status`
- `writer_status`
- `adapter_status`
- `integration_boundary_version` when only test boundary exists
- `dry_run_action`
- `clean_data_write_count`
- `delivery_write_count`
- `filesystem_write_count`
- `database_write_count`
- `export_write_count`

Future production persistence should use explicit writer mode and schema version rather than carrying test-only flags as if they authorize writes. Dry-run reports and run manifests may still include these fields.

## Schema mismatch fail-closed rules

Schema mismatch must fail closed before writer call when possible:

- Missing required adapter/audit fields.
- Unexpected top-level fields.
- Unknown contract/schema version.
- Missing or mismatched `run_id`, `adapter_version`, or `input_file_hashes`.
- Missing `review_item_id`, `audit_hash`, metric, period, or candidate value.
- Unknown `agreement_status` or `VERIFIED` review_queue candidate.
- Unsupported reviewer action or inconsistent review status/action pair.
- Open readiness gate.
- Nonzero external-call count.
- Forbidden raw/full-content field.
- clean_data or delivery write intent.
- Oversized or missing evidence preview.

Writer preview mismatch must fail closed after writer call:

- Writer status is not `ENABLED_TEST_ONLY_DRY_RUN`.
- `dry_run_only` is missing or false.
- Records are not a list of review-bound rows.
- Summary counts do not match records.
- Any write count is nonzero.
- Boundary flags open.
- Readiness gates open.
- Writer records mutate audit metadata, idempotency keys, or source trace unexpectedly.

Future persistence mismatch should reject the whole batch and avoid partial writes.

## Future persistence shape notes

Recommended future persisted row shape:

```text
schema_version
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
adapter_contract_version
writer_contract_version
source_document_id
source_row_id
metric_name
period
candidate_value
candidate_unit
normalized_candidate_value
agreement_status
review_status
reviewer_action
review_reason
severity
blocked_delivery_reason
re_audit_required
evidence_preview
evidence_preview_sha256
source_trace
audit_hash
idempotency_key
record_payload_hash
created_at_or_write_time_metadata_not_used_for_idempotency
```

Recommended future batch/run metadata shape:

```text
schema_version
run_id
adapter_version
adapter_contract_version
writer_contract_version
input_file_hashes
source_file_hashes
adapter_audit_hash
batch_audit_hash
record_count
status_counts
blocked_delivery_count
re_audit_required_count
readiness_gates
external_call_counts
boundary_flags
writer_mode
```

Fields excluded from future persisted row shape:

- test-only tokens
- raw artifacts/full content
- direct writer preview payloads from users
- clean_data or formal delivery payloads
- open readiness overrides
- non-deterministic timestamps in idempotency
- database IDs in idempotency

## Future test plan

Later implementation should add tests for:

- field map required-fields positive path
- missing required audit field fails closed
- malformed idempotency key fails closed
- non-deterministic timestamp rejected
- full source_text rejected at all layers
- raw MinerU/raw Excel/raw parser rejected at schema boundary
- clean_data intent rejected at schema boundary
- readiness OPEN rejected at schema boundary
- writer preview missing dry_run_only rejected
- writer preview field mutation rejected
- future persistence shape excludes test-only config fields
- future persistence shape keeps audit/idempotency/blocking fields
- ambiguous `contract_version` naming rejected unless namespaced
- `normalized_candidate_value` absent or malformed remains review-bound and does not create clean_data
- corrected rows require `re_audit_required = true`
- `blocked_delivery_reason` required for unresolved non-VERIFIED rows
- duplicate idempotency key with identical payload no-ops; different payload conflicts
- successful future persistence emits no full source text and no raw artifact bodies

## Remaining risks

- Current `contract_version` naming is overloaded across adapter input, adapter contract, and writer record; future persistence should namespace it before any storage work.
- Current `normalized_candidate_value` is not emitted by the writer dry-run record, so future schema work must decide whether to add it or leave normalization outside persistence.
- Current `re_audit_required` is represented as `requires_reaudit_before_clean_delivery` in delivery re-audit rows and count summaries, not as a review dry-run record field.
- Current chain is test-only and fixture-driven; it proves boundary shape, not production storage behavior.
- No database transaction, rollback, repository, migration, or production writer exists yet.

## Decision

```text
Decision = 348N_R7BH_SCHEMA_ALIGNMENT_PLAN_CREATED
```

R7BH creates a docs-only schema alignment plan. It recommends keeping audit/idempotency/blocking/source-trace fields, namespacing contract/schema version fields, bounding evidence previews, forbidding raw/full-content fields, keeping `clean_data` and delivery writes out of review_queue persistence, requiring re-audit for corrected rows, and failing closed on schema mismatch.

## Recommended next task

```text
348N-R7BH-QA review-queue writer dry-run integration schema alignment planning slice review
```

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
PASS

python -m py_compile tests/agent/review_queue_writer_contract_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
PASS

python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
PASS

python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
PASS

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
36 passed in 0.22s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
24 passed in 0.13s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
75 passed in 0.27s

python -m pytest tests/agent -q
375 passed in 1.73s

git status -sb
PASS：only docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md untracked before staging.

git diff --stat
PASS：no tracked diff before staging.

git diff --name-only
PASS：no tracked diff before staging.

git diff --check
PASS
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：docs-only schema alignment plan created
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：dry-run integration tests 36 passed；writer contract tests 24 passed；adapter skeleton tests 75 passed；full tests/agent 375 passed
files_modified（修改文件数）= 1：docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md
error_count（错误数）= 0
schema_alignment_plan_result（schema对齐规划结果）= PASS：adapter output, integration envelope, writer dry-run preview, and future persistence fields aligned
plain_language_result（大白话说明结果）= PASS：explains this is field-alignment planning only, not implementation or production persistence
field_inventory_result（字段盘点结果）= PASS：current adapter, integration, writer preview, and future persistence field groups inventoried
field_map_result（字段映射结果）= PASS：required R7BH fields mapped with source, classification, normalization, failure behavior, and persistence decision
required_field_result（必需字段结果）= PASS：future persisted row and batch required fields proposed
forbidden_field_result（禁止字段结果）= PASS：full source_text, raw MinerU/Excel/parser/model payloads, clean_data intent, delivery payloads, production writer config, readiness overrides, and direct writer preview payloads remain forbidden
normalization_rule_result（标准化规则结果）= PASS：metric/period/reason/action/contract/re-audit/evidence-preview normalization rules specified
idempotency_field_result（幂等字段结果）= PASS：deterministic idempotency inputs and duplicate/collision behavior specified
audit_metadata_field_result（审计元数据字段结果）= PASS：run/version/input hash/audit hash/count/readiness/external-call metadata preserved
evidence_boundary_result（证据边界结果）= PASS：bounded preview and hashes allowed; full source_text/raw artifacts forbidden
clean_data_boundary_result（clean_data边界结果）= PASS：review_queue remains separate from clean_data; VERIFIED/corrected rows do not bypass clean gate
delivery_gate_boundary_result（交付闸门边界结果）= PASS：unresolved rows keep blocked_delivery_reason; corrected rows require re-audit
dry_run_test_only_boundary_result（dry-run/test-only边界结果）= PASS：dry-run/test-only fields scoped to preview/run audit and not production row authority
future_test_plan_result（未来测试计划结果）= PASS：future required-field, forbidden-field, idempotency, dry-run, persistence, clean/readiness boundary tests listed
boundary_check（边界检查）= PASS：only allowed docs report created; no production/tests/fixtures/output/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BH-QA review-queue writer dry-run integration schema alignment planning slice review
```
