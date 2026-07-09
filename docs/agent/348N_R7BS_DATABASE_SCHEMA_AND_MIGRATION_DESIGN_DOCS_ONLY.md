# 348N-R7BS database schema and migration design docs-only

## Task ID

```text
348N-R7BS database schema and migration design docs-only
```

Task type: docs-only schema and migration design. This report is conceptual only; it does not create a database schema, migration, repository, service, runner, output, or production hook.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 69578a4..408da10; R7BS task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -70
PASS: latest history includes 408da10 R7BS task doc, 69578a4 R7BR-QA, b3e0baf R7BR-QA task doc, and ec0dbc8 R7BR implementation.
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
- `docs/codex_tasks/348N_R7BS_database_schema_and_migration_design_docs_only.md`
- `docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md`
- `docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md`
- `docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`

Current test-only files reviewed read-only:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json`
- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json`
- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

Production-adjacent modules were left unchanged.

## R7BR-QA recap

R7BR-QA approved the fake repository negative-path and idempotency expansion:

- fake repository targeted tests: `63 passed`;
- persistence contract tests: `76 passed`;
- schema alignment tests: `29 passed`;
- dry-run integration tests: `36 passed`;
- writer contract tests: `24 passed`;
- disabled production-boundary adapter skeleton tests: `75 passed`;
- latest known full `tests/agent`: `543 passed`;
- `readiness_gates` remain CLOSED.

R7BR-QA confirmed the fake repository is still test-only, in-memory-only, fail-closed, metadata-first, no-IO, no-DB, no-output, no-production-hook, no clean_data mutation, and no readiness-gate change.

## 大白话说明

这一轮只是把“以后真的要落库时，表和 migration 应该怎么设计”讲清楚。现在仍然不建表、不写 migration、不连数据库、不写 repository、不加生产开关。换句话说，R7BS 是路线图，不是施工队；它的作用是先把字段、唯一约束、幂等、审计、回滚、软撤回、feature gate 和风险边界说清楚，防止后续实现时把测试区 fake repository 误读成生产 persistence。

## Current baseline

Current safe chain:

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> test-only persistence contract
-> in-memory persistence candidate batch
-> test-only fake repository / in-memory repository boundary
-> fake repository negative-path and idempotency expansion
```

Current baseline constraints:

- current persistence stack is still test-only and in-memory;
- no real DB persistence exists;
- no database model exists;
- no repository class exists;
- no migration exists;
- no production persistence hook exists;
- R7BR-QA approved targeted fake repository tests at `63 passed`;
- latest known full `tests/agent` is `543 passed`;
- readiness gates remain CLOSED.

## Docs-only scope

R7BS only designs a future persistence boundary. It does not:

- create DB schema files;
- create migration files;
- add ORM models;
- add repository or service code;
- add DB connection code;
- add storage/output writers;
- change tests or fixtures;
- run extraction systems;
- open production readiness.

The conceptual fields below describe a future design target only. They are not an implemented schema.

## Conceptual table design

Primary conceptual table:

```text
review_queue_items
```

Purpose:

- persist review-bound rows that have already passed adapter, dry-run writer, schema alignment, persistence contract, and future repository validation;
- support reviewer UI queues, audit lookup, deterministic idempotent write behavior, and blocked-delivery traceability;
- store metadata and bounded evidence preview only, never full source text or raw extraction payloads.

Optional conceptual audit tables for a later design review:

```text
review_queue_item_events
review_queue_persistence_attempts
review_queue_migration_runs
```

These optional tables should not be implemented until separately reviewed. They are useful for audit logs, reviewer decisions, persistence attempt receipts, migration ledger entries, and rollback/forward-fix traceability.

## Conceptual column design

Conceptual `review_queue_items` columns:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
contract_version
writer_contract_version
schema_version
audit_hash
idempotency_key
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
evidence_preview_sha256
source_trace
source_document_id
source_row_id
adapter_item_id
matched_locator
matched_text_sha256
subqueue
created_by_system
record_payload_hash
created_at
updated_at
retracted_at
retraction_reason
```

Design notes:

- `candidate_unit` appears in upstream schema-alignment previews and should be preserved or explicitly ruled out by R7BS-QA/R7BT before implementation.
- `input_file_hashes` and `source_trace` may be stored as constrained JSON/JSONB or normalized child columns, depending on the eventual DB backend.
- `created_at`, `updated_at`, and `retracted_at` are future DB-controlled timestamps only; caller-supplied timestamp fields must remain forbidden.
- `retracted_at` and `retraction_reason` support soft retraction, not destructive delete.

## Identity and hash field design

Required identity fields:

- `review_item_id`: stable logical item id; unique.
- `run_id`: identifies the audit/comparison run.
- `source_file_hash`: source file identity for lookup and grouping.
- `input_file_hashes`: bounded hash identity object for all inputs.
- `metric_name`, `period`, and `candidate_value`: business identity fields for reviewer context.
- `source_document_id`, `source_row_id`, `adapter_item_id`: source trace identity fields.

Required hash fields:

- `audit_hash`: upstream audit identity.
- `idempotency_key`: deterministic write identity; unique.
- `record_payload_hash`: deterministic canonical payload hash excluding `record_payload_hash` itself.
- `evidence_preview_sha256`: hash of bounded `evidence_preview`.
- `matched_text_sha256`: hash of matched evidence text/snippet, not the text itself.

Hash policy:

- hashes must be lowercase 64-character SHA-256 hex strings;
- payload hash must be recomputed by repository validation before insert/update;
- stored hash fields must be immutable after initial accepted write unless a new versioned record/retraction event is created;
- hash mismatch must fail closed before any DB state mutation.

## Review status/action field design

Future DB persistence should admit only review-bound non-VERIFIED statuses unless a later production gate review explicitly changes the policy:

```text
UNVERIFIED
DISAGREED
AMBIGUOUS
MISSING_EVIDENCE
PARSE_SKIPPED
```

`VERIFIED` must not automatically enter this review_queue persistence table. If a future design needs to persist VERIFIED audit traces, it should use a separately reviewed metadata/audit table, not this review-bound queue.

Conceptual `review_status` enum:

```text
PENDING_REVIEW
REVIEW_IN_PROGRESS
NEEDS_REAUDIT
RESOLVED_REQUIRES_REAUDIT
RESOLVED_REJECTED
RETRACTED
```

Forbidden `review_status` values:

```text
CLEAN_DATA_APPROVED
AUTO_CLEAN_APPROVED
DELIVERY_UNBLOCKED
READY_FOR_DELIVERY
APPROVED_FOR_EXPORT
```

Conceptual `reviewer_action` enum:

```text
NONE
ACCEPT_CANDIDATE_FOR_REVIEW_ONLY
REJECT_CANDIDATE
CORRECT_VALUE
CORRECT_UNIT
CORRECT_PERIOD
CORRECT_METRIC
MARK_NOT_IN_REPORT
MARK_EVIDENCE_INSUFFICIENT
REQUEST_REEXTRACTION
REQUEST_MANUAL_SOURCE_CHECK
```

Corrective reviewer actions must set `re_audit_required = true`. Reviewer action alone must never imply clean_data admission, delivery unblocking, export readiness, or evidence-level promotion.

## Evidence preview and source trace design

Allowed evidence fields:

- `evidence_preview`: bounded text preview, current preview limit `160` characters unless future schema version changes it;
- `evidence_preview_sha256`: SHA-256 hash of the bounded preview;
- `source_trace`: constrained metadata object;
- denormalized source trace columns for indexing and UI display.

Required conceptual `source_trace` fields:

```text
source_document_id
source_row_id
adapter_item_id
matched_locator
matched_text_sha256
subqueue
evidence_preview_sha256
```

Forbidden evidence behavior:

- never store full `source_text`;
- never store raw PDF text pages;
- never store raw MinerU, Excel, parser, OCR, LLM, or VLM payloads;
- never store unbounded snippets;
- never serialize DB DSN, file path, output path, production writer config, readiness override, clean_data intent, or delivery/export intent.

## Audit metadata design

Required audit metadata:

- `run_id`;
- `adapter_version`;
- `contract_version`;
- `writer_contract_version`;
- `schema_version`;
- `source_file_hash`;
- `input_file_hashes`;
- `audit_hash`;
- `record_payload_hash`;
- `idempotency_key`;
- DB-controlled `created_at` / `updated_at`;
- optional `created_by_system` fixed to an allowlisted system identifier.

Optional future audit-event metadata:

- persistence attempt id;
- request batch hash;
- validation result;
- conflict reason;
- transaction id or local test DB transaction marker;
- actor type: system, reviewer, migration;
- migration id for rows created/changed by migration;
- soft-retraction actor and reason.

Audit metadata must be metadata-first. It should help reproduce and explain state transitions without storing raw source payloads.

## Idempotency and uniqueness design

Candidate uniqueness constraints:

```text
unique(idempotency_key)
unique(review_item_id)
unique(run_id, source_file_hash, metric_name, period, schema_version, contract_version)
```

Candidate consistency rules:

- same `idempotency_key` + same `record_payload_hash` = deterministic no-op or same receipt policy;
- same `idempotency_key` + different `record_payload_hash` = conflict / fail closed;
- same `review_item_id` + different `idempotency_key` = conflict / fail closed;
- same `review_item_id` + same `idempotency_key` + changed payload = conflict / fail closed;
- same `record_payload_hash` with different identity must fail closed or be explicitly documented as a safe dedupe policy before implementation;
- no silent duplicate insert;
- batch duplicate `idempotency_key` or `review_item_id` must fail before insert.

Open decision for R7BT/R7BU:

- whether uniqueness should be global across all history or partial on active rows only when soft retraction exists.

Conservative recommendation:

- use global uniqueness for `idempotency_key`;
- use active-row uniqueness for `review_item_id` only if soft retraction/versioning is designed and QA-approved;
- otherwise keep `review_item_id` globally unique.

## Index and query pattern design

Required future query patterns:

- lookup by `review_item_id`;
- lookup by `idempotency_key`;
- lookup by `run_id`;
- lookup by `source_file_hash`;
- lookup by `review_status`;
- lookup by `agreement_status`;
- lookup by `re_audit_required`;
- lookup by `created_at` / `updated_at`;
- reviewer UI pagination by status/severity/subqueue/time;
- audit/debug lookup by `record_payload_hash`;
- source/debug lookup by `source_document_id`, `source_row_id`, and `matched_locator`.

Candidate indexes:

```text
primary key or unique index on review_item_id
unique index on idempotency_key
index on run_id
index on source_file_hash
index on agreement_status
index on review_status
index on re_audit_required
index on created_at
index on updated_at
index on record_payload_hash
composite index on (review_status, re_audit_required, updated_at)
composite index on (run_id, source_file_hash)
composite unique index on (run_id, source_file_hash, metric_name, period, schema_version, contract_version)
```

Any JSON/JSONB indexing for `input_file_hashes` or `source_trace` should wait until DB backend selection and performance testing.

## Constraint and enum design

Conceptual check constraints:

- `agreement_status` in the review-bound enum only;
- `review_status` in the future review status enum;
- `reviewer_action` in the future reviewer action enum;
- `blocked_delivery_reason` non-empty for unresolved or review-bound rows;
- `re_audit_required` boolean;
- `created_by_system` in an allowlisted system enum;
- `evidence_preview` non-empty and bounded;
- `evidence_preview_sha256`, `matched_text_sha256`, `audit_hash`, `idempotency_key`, and `record_payload_hash` match SHA-256 hex format;
- `record_payload_hash` consistency enforced by repository validation before DB write;
- `retracted_at` requires `retraction_reason`.

Forbidden implications:

- stored review_queue rows must not imply `STRONG_EVIDENCE`;
- stored review_queue rows must not imply clean_data admission;
- stored review_queue rows must not imply delivery/export unblocking;
- stored review_queue rows must not open readiness gates.

## Raw-payload exclusion design

Future schema and repository validation must reject and never store:

```text
full source_text
raw MinerU payload
raw Excel payload
raw parser payload
raw OCR payload
raw LLM/VLM response
DB DSN / connection string
output path / file path config
production writer config
readiness override
clean_data intent
delivery/export intent
```

Recommended enforcement layers:

1. contract validation rejects forbidden keys recursively before repository calls;
2. repository validation repeats recursive forbidden-key checks;
3. DB schema stores only allowlisted columns;
4. audit event table stores metadata and hashes only;
5. QA tests inspect serialized rows/receipts for full-source/raw-payload leakage.

## Transaction and batch atomicity design

Future repository rules:

- single-row insert/update is atomic;
- batch write is atomic by default;
- no partial success by default;
- rollback transaction on any invalid row, hash mismatch, uniqueness conflict, forbidden field, enum violation, or readiness/clean/delivery implication;
- idempotent retry after transient failure must be safe;
- persistence attempt and result should emit metadata-only audit event;
- invalid writes must not mutate state;
- no destructive reset/clear by default.

The existing fake repository simulates this by preparing copied next-state dictionaries and replacing state only after validation. Future DB implementation must prove equivalent behavior with real transactions and rollback tests before any production hook.

## Migration order design

Conservative migration sequence:

```text
1. schema design review
2. migration design QA
3. disabled repository skeleton
4. local test DB prototype behind explicit test flag
5. negative-path / rollback tests against local test DB
6. idempotency and concurrency tests against local test DB
7. metadata-only audit event design
8. production gate review docs-only
9. disabled production config skeleton
10. only then consider production hook
```

Do not create actual migration files in R7BS.

Migration execution requirements for a future implementation:

- migration must be reversible only while no persisted data exists;
- once data exists, prefer forward-fix migrations over destructive rollback;
- migration must have a metadata ledger entry;
- migration must never auto-enable production persistence;
- migration must never change clean_data or delivery/export behavior.

## Rollback and forward-fix design

Rollback/forward-fix policy:

- invalid migration before data exists can be rolled back normally;
- invalid migration after data exists should use forward-fix migration by default;
- bad rows should be soft-retracted or quarantined, not destructively deleted;
- manual recovery path must preserve original metadata, hash identities, and retraction reason;
- rollback must not open readiness gates or trigger delivery/export;
- rollback must not change clean_data eligibility.

Persistence failure policy:

- transaction rollback on validation or DB write failure;
- retry with same idempotency key/hash should be deterministic;
- retry with changed payload should fail closed;
- persistence attempt audit should record metadata-only result and error category.

## Retention and retraction design

Retention:

- review_queue records should be retained long enough to reproduce audit decisions;
- retention windows should be policy-controlled and separately reviewed;
- raw source payload retention is out of scope and remains forbidden in review_queue persistence.

Retraction:

- use soft retraction by default: `retracted_at` + `retraction_reason`;
- keep `review_item_id`, `idempotency_key`, and `record_payload_hash` for audit trace;
- retracted rows must stay excluded from clean_data and delivery/export;
- destructive delete should require a separate data retention/privacy design and QA review.

## Feature gate and environment planning

Future implementation must require:

- readiness gates remain CLOSED until separate production gate review;
- explicit test-only DB flag for local test DB stages;
- separate production persistence flag only after production gate review;
- environment allowlist;
- no default production DB connection;
- no production writer config in test-only paths;
- no automatic activation from validated schema alignment preview;
- no activation from environment variables alone without explicit config and gate review.

Recommended gate sequence:

```text
test-only in-memory = current
test-only local DB = future explicit flag only
disabled production skeleton = future no-op by default
production persistence = separate gate review only
```

## Readiness gate requirements

Readiness requirements to preserve:

- `client_ready = false`;
- `production_ready = false`;
- `formal_client_export_allowed = false`;
- `demo_export_only = true`;
- `VERIFIED` does not imply `STRONG_EVIDENCE`;
- `VERIFIED` does not auto-write clean_data;
- non-VERIFIED rows remain review-bound;
- unresolved rows keep `blocked_delivery_reason`;
- corrected rows remain `re_audit_required`;
- persistence candidate does not trigger delivery;
- persistence candidate does not mutate clean_data;
- persistence candidate does not open readiness gates;
- bounded `evidence_preview` is allowed;
- full `source_text` is forbidden;
- raw MinerU/raw Excel/raw parser/raw OCR/raw LLM/VLM payloads are forbidden.

Any future DB implementation must pass a separate production gate review before a production hook can be considered.

## Open questions

- Which DB backend will be used for the first local test DB prototype?
- Should `candidate_unit` be first-class or remain part of source/review metadata?
- Should `source_trace` be stored as constrained JSON/JSONB, normalized columns, or both?
- Should `review_item_id` uniqueness be global or active-row partial when retraction/versioning is introduced?
- Should audit events be stored in a separate table from day one of local test DB prototype?
- What retention period is required for review_queue records?
- What reviewer UI pagination/sorting requirements should drive composite indexes?
- What concurrency level must be supported before production persistence?
- What manual retraction/repair workflow is required for privacy or mistaken rows?

## Non-goals

R7BS does not:

- modify production code;
- modify tests;
- modify fixtures;
- add repository/model/service code;
- add DB schema;
- add migration;
- add DB connection;
- add storage implementation;
- write output files;
- run extraction;
- run MinerU/OCR/LLM/VLM;
- open readiness gates;
- claim production persistence;
- claim production readiness;
- claim client readiness;
- claim formal export readiness.

## Remaining risks

- Schema is only conceptual.
- Migration is only planned.
- No real database behavior is proven.
- No local test DB adapter exists yet.
- Transaction/rollback behavior is not implemented.
- Storage performance/concurrency is not proven.
- Real review UI integration is not proven.
- Production operational controls are not proven.
- Client/export readiness is still not implied.

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_fake_repository_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_fake_repository_boundary_348n.py
PASS

python -m py_compile tests/agent/review_queue_persistence_contract_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_persistence_contract_348n.py
PASS

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

python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
PASS: 63 passed in 0.51s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.42s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.16s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.24s

python -m pytest tests/agent -q
PASS: 543 passed in 2.40s

git status -sb
PASS before report creation: clean.

git diff --stat
PASS before report creation: no tracked diff.

git diff --name-only
PASS before report creation: no tracked diff.

git diff --check
PASS before report creation: no whitespace errors.
```

## Recommended next task

```text
348N-R7BS-QA database schema and migration design review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BS docs-only database schema and migration design completed.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; fake repository 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 543 passed.
files_modified（修改文件数）= 1 allowed docs-only report file.
error_count（错误数）= 0.
schema_design_result（schema设计结果）= PASS; future review_queue persistence schema is conceptual, metadata-first, review-bound, and raw-payload-safe.
migration_design_result（migration设计结果）= PASS; conservative design sequence requires QA, disabled skeleton, local test DB prototype, negative/rollback tests, and production gate review before production hook.
conceptual_table_result（概念表设计结果）= PASS; primary conceptual table review_queue_items plus optional audit/migration tables documented as future-only.
conceptual_column_result（概念字段设计结果）= PASS; identity, review, evidence, audit, idempotency, timestamp, and soft-retraction conceptual columns documented.
identity_hash_design_result（身份/哈希设计结果）= PASS; review_item_id, idempotency_key, audit_hash, record_payload_hash, evidence_preview_sha256, and matched_text_sha256 rules defined.
status_action_design_result（状态/动作设计结果）= PASS; review-bound agreement statuses and conservative review_status/reviewer_action enums designed without clean_data/delivery implication.
evidence_trace_design_result（证据/trace设计结果）= PASS; bounded evidence_preview and source_trace metadata allowed; full source_text and raw payloads forbidden.
audit_metadata_design_result（审计元数据设计结果）= PASS; run/input/version/hash metadata and future metadata-only audit event concepts documented.
idempotency_uniqueness_design_result（幂等唯一性设计结果）= PASS; unique idempotency/review item rules, retry no-op, conflict fail-closed, and no silent duplicate insert documented.
index_query_design_result（索引查询设计结果）= PASS; review UI, idempotency, run/source/status/re-audit/hash lookup indexes planned.
constraint_enum_design_result（约束枚举设计结果）= PASS; check/enum constraints planned to block invalid status/action/hash/preview/readiness/clean/delivery implications.
raw_payload_exclusion_design_result（原始payload排除设计结果）= PASS; schema/repository validation must reject full source_text, raw MinerU/Excel/parser/OCR/LLM/VLM, DB/path/config, readiness, clean_data, and delivery/export intent.
transaction_atomicity_design_result（事务原子性设计结果）= PASS; single-row atomicity, batch all-or-nothing, rollback on invalid row, and idempotent retry policy documented.
rollback_forward_fix_design_result（回滚/前向修复设计结果）= PASS; forward-fix after data exists, soft retraction, metadata-only persistence attempt audit, and manual recovery path documented.
feature_gate_design_result（feature gate设计结果）= PASS; explicit test-only DB flag, environment allowlist, disabled production skeleton, and separate production gate review required.
readiness_gate_result（就绪门结果）= PASS; readiness gates remain CLOSED and no production/client/formal export readiness is claimed.
boundary_check（边界检查）= PASS; only docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BS-QA database schema and migration design review.
```
