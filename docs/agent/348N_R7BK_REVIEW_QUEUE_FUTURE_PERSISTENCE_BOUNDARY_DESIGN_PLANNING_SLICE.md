# 348N-R7BK review_queue future persistence boundary design planning slice

## Task ID

```text
348N-R7BK review_queue future persistence boundary design planning slice
```

Task type: docs-only-design-planning.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 3aba954..2fa0232; R7BK task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -35
PASS: latest commits include 2fa0232 R7BK task doc and 3aba954 R7BJ-QA.
```

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
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/agent/348N_R7BJ_QA_PROJECT_DOCUMENTATION_SYNC_REVIEW_AFTER_REVIEW_QUEUE_DRY_RUN_SCHEMA_ALIGNMENT_MILESTONE.md`
- `docs/agent/348N_R7BJ_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_DRY_RUN_SCHEMA_ALIGNMENT_MILESTONE.md`
- `docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BH_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md`

Current implementation and test-only slices reviewed read-only:

- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

Production-adjacent modules reviewed read-only:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BJ-QA recap

R7BJ-QA confirmed the documentation sync was accurate, consistent, conservative, test-only-aware, dry-run-aware, production-safe, and readiness-closed. It recommended this R7BK planning slice as the next safe step before any persistence implementation.

The current proven chain remains:

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> future review_queue record preview
```

## 大白话说明

这一轮只设计“以后如果要把 review_queue 写入存储，门应该长什么样”。它不是现在落库；不建表、不写库、不写文件、不导出、不接生产、不打开 readiness。它把未来落库前必须满足的字段、幂等、审计、回滚、失败处理和 gate 审批先讲清楚。

## Future persistence boundary scope

The future persistence boundary should be a narrow validation and authorization layer between the R7BI schema alignment preview and any real storage candidate:

```text
test-only schema alignment preview
-> future persistence boundary
-> real review_queue storage candidate
```

The boundary should initially produce a persistence candidate or dry-run persistence plan only. A later implementation may decide whether that candidate is written to an in-memory fake store, a temporary test repository, or a real database, but R7BK does not implement any of those paths.

The boundary owns these decisions:

- whether a schema alignment preview is safe to persist;
- whether a batch is idempotent or conflicting;
- whether all records are metadata-first and source_text-safe;
- whether clean_data, delivery/export, readiness, and production writer intent remain blocked;
- whether all records can be committed atomically or must fail closed.

## Current chain position

The planned boundary sits after the R7BI schema alignment contract has produced future review_queue record previews and before any storage mechanism:

```text
R7BI output:
  future_review_queue_record_previews[]
  schema_alignment_summary
  field_classification

Future R7BK/R7BL boundary:
  validate envelope and row preconditions
  classify persistence eligibility
  compute/verify persistence payload hash
  plan idempotent write / duplicate skip / conflict fail
  produce storage candidate only if all records pass

Future storage:
  not implemented in R7BK
```

The boundary must not consume raw adapter payloads, direct writer previews, raw Excel/MinerU/parser artifacts, or user-supplied write payloads. Its only accepted upstream authority should be a validated schema alignment preview.

## Non-goals

R7BK does not:

- implement persistence;
- add database models;
- add repositories;
- add migrations;
- add storage code;
- add a writer;
- add tests or fixtures;
- modify production code;
- run MinerU, OCR, LLM, VLM, or PDF extraction;
- write output files;
- open readiness gates;
- claim `review_queue` persistence exists;
- claim production/client/formal export readiness.

## Required preconditions before any write

A future persistence implementation must fail closed before any write unless all of these are true:

```text
validated schema alignment preview is present
schema_alignment_status = ENABLED_TEST_ONLY_SCHEMA_ALIGNMENT or separately approved production status
dry_run_only status is understood and not silently converted into production authority
readiness_gates still CLOSED unless separately approved
explicit persistence test flag is present for early implementation
no production writer config unless a separate production gate review exists
schema alignment contract version is known
integration boundary contract version is known
writer contract version is known
schema version is known
review_item_id is present
run_id is present
source_file_hash or input_file_hashes is present
audit_hash is present
idempotency_key is present and deterministic
record_payload_hash is present and deterministic
review_status is present
review_reason is present
blocked_delivery_reason is present for unresolved or blocked records
re_audit_required is present for corrected records
evidence_preview is bounded
source_trace is compact and metadata-first
no full source_text is present
no raw extraction payload is present
no clean_data write intent is present
no delivery/export intent is present
no readiness override is present
```

Validation must cover the entire batch before any persistence call. If one record fails, the whole batch should fail before writing unless a later task explicitly designs a safe partial-commit mode.

## Future review_queue row shape planning

A future `review_queue` row should be metadata-first and review-bound. It may include:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
adapter_contract_version
writer_contract_version
integration_boundary_version
schema_alignment_contract_version
schema_version
audit_hash
adapter_audit_hash
idempotency_key
record_payload_hash
metric_name
period
candidate_value
candidate_unit
normalized_candidate_value
agreement_status
review_status
review_reason
reviewer_action
blocked_delivery_reason
re_audit_required
evidence_preview
source_trace
severity
clean_data_eligible
delivery_blocked
created_by_system
created_at or deterministic batch timestamp policy, only if separately designed
updated_at or deterministic update policy, only if separately designed
```

This shape is a planning target only. R7BK does not create a table or database row.

## Allowed fields

Allowed future persistence fields should be limited to:

- stable row identity fields;
- stable run/source identity fields;
- compact input hashes;
- contract and schema versions;
- audit hash and record payload hash;
- deterministic idempotency key;
- metric/period/value/unit and normalized value;
- review-bound status fields;
- blocked delivery and re-audit fields;
- bounded `evidence_preview`;
- compact `source_trace` metadata such as source document id, source row id, matched locator, matched page, matched text hash, and adapter item id;
- optional system provenance fields if separately designed.

Allowed fields must remain sufficient for audit and reviewer workflow without carrying raw source artifacts.

## Forbidden fields

The future persistence boundary must reject these before any write:

```text
full source_text
source_text_full
full_source_text
raw_source_text
raw MinerU output
content_list_v2
raw Excel workbook data
raw Excel rows/cells/sheets
raw parser payload
raw PDF text/pages
raw LLM/VLM response
clean_data write intent
clean_data payload
formal delivery/export payload
production writer config
test-only enable token
test-only writer config object
test-only schema alignment config object
user-provided direct writer preview
unbounded evidence text
unapproved readiness gate override
database-generated authority injected by input
wall-clock timestamp supplied by untrusted input
```

Timestamps are not categorically forbidden forever, but any `created_at` / `updated_at` policy must be designed separately so it cannot break idempotency or become a user-supplied authority field.

## Idempotency strategy

The future persistence boundary should preserve the upstream deterministic `idempotency_key` and independently verify that it is a 64-character SHA-256 hex digest or another explicitly versioned deterministic format.

Recommended uniqueness scope:

```text
storage_namespace
schema_version
idempotency_key
```

The persisted row should also retain `record_payload_hash`. On retry:

- same `idempotency_key` + same `record_payload_hash` => `WOULD_SKIP_DUPLICATE` or idempotent no-op;
- same `idempotency_key` + different `record_payload_hash` => conflict and fail closed;
- duplicate `idempotency_key` within the same incoming batch => fail closed before write;
- missing or malformed idempotency key => fail closed before write.

No wall-clock timestamp should participate in idempotency unless a later design explicitly proves deterministic behavior.

## Audit metadata strategy

The boundary should preserve audit metadata rather than recompute it from raw artifacts:

```text
run_id
adapter_version
adapter_contract_version
writer_contract_version
integration_boundary_version
schema_alignment_contract_version
schema_version
input_file_hashes
source_file_hash
adapter_audit_hash
audit_hash
record_payload_hash
source_trace
readiness_gates
external_call_counts
```

The boundary should also produce a `persistence_plan_hash` over the normalized storage candidate batch. This hash should be deterministic and exclude volatile timestamps unless a deterministic timestamp policy is separately approved.

## Duplicate prevention strategy

Duplicate prevention should happen at three layers:

1. **Batch preflight:** reject duplicate `idempotency_key` values inside the incoming batch.
2. **Existing-record check:** compare incoming `idempotency_key` against existing storage metadata before writing.
3. **Storage constraint:** future database schema should enforce a unique key on the agreed idempotency scope.

The planned behavior should be:

```text
new key -> eligible for persistence candidate
same key + same payload hash -> duplicate no-op / WOULD_SKIP_DUPLICATE
same key + different payload hash -> conflict, fail closed, no write
duplicate key inside batch -> fail closed, no write
```

## Transaction and rollback expectations

Future persistence must be atomic by default:

- validate the full envelope and all rows before opening a write transaction;
- write all records in a single transaction if real storage is used;
- roll back all records on any write error;
- return an explicit failure plan/report after rollback;
- never leave a partially committed batch unless a separate partial-commit design is approved;
- never mutate `clean_data` or delivery outputs in the same transaction;
- never open readiness gates as a side effect of a successful write.

For early implementation, a fake or in-memory persistence adapter should simulate transaction failure and rollback without touching real storage.

## Failure and fail-closed behavior

Failures should happen before write whenever possible. Required fail-closed cases:

- missing required envelope fields;
- unknown contract or schema version;
- readiness gates unexpectedly open;
- missing `review_item_id`;
- missing `run_id`;
- missing source hash metadata;
- missing `audit_hash`;
- missing or malformed `idempotency_key`;
- missing or malformed `record_payload_hash`;
- schema mismatch;
- forbidden fields anywhere in the payload;
- unbounded evidence preview;
- full source_text present;
- raw extraction payload present;
- clean_data write intent present;
- delivery/export intent present;
- production writer config present;
- unresolved/blocked row without `blocked_delivery_reason`;
- corrected row without `re_audit_required`;
- duplicate idempotency conflict;
- write transaction error.

Every failure path should return no storage writes and no clean/delivery mutation.

## Review status lifecycle

Future persistence should preserve the review-bound lifecycle rather than resolving it prematurely:

```text
PENDING_REVIEW / REVIEW_REQUIRED -> stored for reviewer workflow
DISAGREED -> high-severity review-bound item
AMBIGUOUS -> medium-high severity review-bound item
MISSING_EVIDENCE -> medium severity review-bound item
PARSE_SKIPPED -> parse or ingestion issue, not evidence disagreement
UNVERIFIED -> conservative review-bound item
RESOLVED_* / CORRECT_* -> re_audit_required until separate re-audit passes
```

`VERIFIED` rows should not be written to review_queue by default. If future product requirements need an audit-only mirror of `VERIFIED` rows, that must be a separate design that still does not imply clean_data admission.

## Blocked delivery behavior

Blocked or unresolved records must retain `blocked_delivery_reason`. Future persistence should store this reason as a delivery-blocking signal, not as delivery authorization.

Rules:

- non-`VERIFIED` records remain review-bound;
- unresolved rows require `blocked_delivery_reason`;
- `delivery_blocked` should remain true for persisted review-bound records;
- persistence must not create delivery artifacts;
- persistence must not mark a row as export-ready.

## Corrected row re-audit behavior

Corrected rows must remain re-audit-required. A future persistence boundary should require `re_audit_required = true` for corrected rows or any row carrying correction actions such as:

```text
CORRECT_VALUE
CORRECT_UNIT
CORRECT_PERIOD
CORRECT_METRIC
```

Reviewer correction should not bypass evidence review, clean candidate policy, or delivery gates. A corrected row may be stored as a review workflow state, but it must not become `clean_data` until a separate explicit re-audit path passes.

## Evidence preview and source_text boundary

Future persistence may store bounded `evidence_preview` and compact source metadata, but must not store full source text.

Allowed evidence metadata examples:

```text
evidence_preview
evidence_preview_sha256
matched_locator
matched_page_number
matched_block_index
matched_text_sha256
source_document_id
source_row_id
source_file_hash
```

Forbidden evidence payload examples:

```text
source_text
full_source_text
raw_source_text
full_table_html
raw page text
raw MinerU block
raw Excel row/cells
raw parser page output
LLM/VLM response body
```

The persistence boundary should apply recursive forbidden-key scanning and preview-length checks before any write.

## clean_data safety boundary

Future review_queue persistence must not mutate `clean_data`.

Rules:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
review_queue persistence does not imply clean_data eligibility
clean_data_eligible must remain false for review-bound records
clean_data write intent fails closed before persistence
corrected rows require re-audit before any future clean path
```

Any future clean_data write must remain a separate reviewed delivery-stage action with its own tests and gates.

## Delivery/export boundary

Future review_queue persistence must not trigger delivery/export.

Rules:

```text
review_queue persistence does not generate client delivery
review_queue persistence does not generate formal export
delivery/export payloads fail closed
formal_client_export_allowed remains false
blocked_delivery_reason remains blocking metadata
delivery_blocked remains true for unresolved review-bound records
```

If future tooling needs to export a reviewer worklist, that should be designed as a separate review artifact with metadata-only evidence and explicit output boundaries.

## Readiness gates and approval boundary

Readiness gates must remain closed through this planning slice and any early test-only persistence prototype:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Opening any gate requires a separate gate review. A successful review_queue persistence test must not imply production readiness, client readiness, or formal export readiness.

Early implementation should require an explicit persistence test flag. Production writer config must remain forbidden unless a separate production boundary and rollback review exists.

## Future implementation test plan

A later implementation slice should add tests for:

```text
persistence disabled by default
explicit persistence test flag required
valid schema alignment preview creates persistence candidate only
missing review_item_id fails closed
missing run_id fails closed
missing source hash metadata fails closed
missing audit_hash fails closed
missing idempotency_key fails closed
malformed idempotency_key fails closed
missing record_payload_hash fails closed
malformed record_payload_hash fails closed
duplicate idempotency_key inside batch fails closed
existing duplicate with same payload hash becomes no-op / WOULD_SKIP_DUPLICATE
existing duplicate with changed payload hash fails closed
schema mismatch fails before write
unknown contract version fails before write
readiness gate override fails before write
forbidden fields fail before write
full source_text rejected before write
raw extraction payload rejected before write
clean_data intent rejected before write
delivery/export intent rejected before write
production writer config rejected before write
unbounded evidence_preview rejected before write
unresolved without blocked_delivery_reason rejected
corrected without re_audit_required rejected
VERIFIED does not write clean_data
review_queue persistence does not trigger delivery/export
write failure rolls back all records
partial batch failure produces no partial committed state unless separately designed
record_payload_hash stable across equivalent input
persistence_plan_hash stable across equivalent input
input mutation after call cannot mutate output
no IO beyond explicitly mocked test persistence boundary
no production hook, DB, network, parser, MinerU, OCR, LLM, VLM call in test-only prototype
```

The first implementation should likely be a test-only persistence candidate builder, not a real database writer.

## Migration and schema questions for later

Later tasks must answer before production persistence:

- Is storage file-based, SQLite, Postgres, or application-managed JSON/CSV?
- What is the canonical table name and schema namespace?
- What is the unique constraint for idempotency?
- How are schema migrations versioned and rolled back?
- Which fields are indexed for reviewer lookup?
- How are `input_file_hashes` stored: JSON column, normalized child table, or compact string?
- How are review status transitions audited?
- Is `created_at` deterministic, database-generated, or omitted from idempotency?
- Is `updated_at` allowed, and if so, how does it interact with record hashes?
- How is `record_payload_hash` recomputed and compared?
- How are duplicate retries reported to callers?
- What is the recovery procedure after a failed transaction?
- How are reviewer actions and corrected values represented without authorizing clean_data?
- How is evidence preview length enforced at storage layer?
- How are raw source_text and raw payload fields prevented by schema and code?
- What backup, retention, and deletion policy applies?
- What manual rollback command or script is allowed?
- Which gate review is required before any production writer config exists?

## Remaining risks

- Future developers may mistake a persistence candidate for production persistence unless names and gates stay explicit.
- Storage timestamp policy can break idempotency if not separately designed.
- Partial batch behavior is dangerous and should remain forbidden by default.
- Reviewer corrections can be misread as clean_data eligibility unless re-audit remains mandatory.
- Evidence preview could accidentally expand into full source text without recursive forbidden-field checks.
- Production readiness may be overclaimed if persistence tests pass but delivery gates remain unreviewed.

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_writer_schema_alignment_contract_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
PASS

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

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
24 passed in 0.15s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
75 passed in 0.25s

python -m pytest tests/agent -q
404 passed in 1.50s

git status -sb
## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
?? docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md

git diff --stat
PASS: no tracked diff before staging because the R7BK report is untracked.

git diff --name-only
PASS: no tracked diff before staging because the R7BK report is untracked.

git diff --check
PASS
```

## Decision

```text
Decision = 348N_R7BK_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_ADDED
```

R7BK defines a conservative future persistence boundary design for `review_queue`. It preserves test-only/dry-run lessons from R7BE-R7BI, requires explicit preconditions before any write, keeps persistence metadata-first, forbids raw/full-source payloads, preserves idempotency and audit metadata, requires atomic rollback semantics, and keeps clean_data, delivery/export, production readiness, and readiness gates closed.

## Recommended next task

```text
348N-R7BK-QA review_queue future persistence boundary design planning slice review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：future review_queue persistence boundary design planning slice added
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：schema alignment tests 29 passed；dry-run integration tests 36 passed；writer contract tests 24 passed；adapter skeleton tests 75 passed；full tests/agent 404 passed
files_modified（修改文件数）= 1：docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md
error_count（错误数）= 0
future_persistence_design_result（未来持久化设计结果）= PASS：future persistence boundary designed without implementation
plain_language_result（大白话说明结果）= PASS：plain-language section states this is future design, not current persistence
boundary_scope_result（边界范围结果）= PASS：boundary sits after schema alignment preview and before any storage candidate
precondition_result（写入前置条件结果）= PASS：required preconditions before any write are enumerated
future_row_shape_result（未来行形状结果）= PASS：metadata-first future review_queue row shape planned
allowed_field_result（允许字段结果）= PASS：safe identity/audit/idempotency/review/evidence metadata fields listed
forbidden_field_result（禁止字段结果）= PASS：full source_text/raw artifacts/clean intent/delivery export/production config/test-token leaks forbidden
idempotency_strategy_result（幂等策略结果）= PASS：deterministic key and payload-hash comparison strategy defined
audit_metadata_strategy_result（审计元数据策略结果）= PASS：run/version/input hash/audit hash/source trace retention strategy defined
duplicate_prevention_result（去重策略结果）= PASS：batch duplicate, existing duplicate, and collision behavior defined
rollback_strategy_result（回滚策略结果）= PASS：atomic all-or-nothing default and rollback expectations defined
fail_closed_strategy_result（fail-closed策略结果）= PASS：failure cases fail before write with no partial persistence
clean_data_boundary_result（clean_data边界结果）= PASS：review_queue persistence must not mutate clean_data or promote VERIFIED
delivery_export_boundary_result（交付导出边界结果）= PASS：persistence must not trigger delivery/export
readiness_gate_boundary_result（就绪门边界结果）= PASS：readiness gates remain closed and require separate review
future_test_plan_result（未来测试计划结果）= PASS：later implementation test matrix listed
boundary_check（边界检查）= PASS：docs-only report; no code/tests/fixtures/output/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7BK-QA review_queue future persistence boundary design planning slice review
```
