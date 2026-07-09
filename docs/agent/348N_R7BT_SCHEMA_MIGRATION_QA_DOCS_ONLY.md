# 348N-R7BT schema/migration QA docs-only

## Task ID

```text
348N-R7BT schema/migration QA docs-only
```

Task type: docs-only QA planning. This report defines future schema/migration QA requirements only; it does not implement schema, migration, repository, database connection, storage, output writer, or production hook.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 9c00bbd..0934c5c; R7BT task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -75
PASS: latest history includes 0934c5c R7BT task doc, 9c00bbd R7BS-QA, 13fdb03 R7BS-QA task doc, and 5c6553d R7BS design.
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
- `docs/codex_tasks/348N_R7BT_schema_migration_QA_docs_only.md`
- `docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md`
- `docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md`

Current test-only files reviewed read-only:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

## R7BS-QA recap

R7BS-QA approved R7BS as a conservative docs-only schema and migration design:

- schema/migration design is conceptual only;
- no real database schema exists;
- no migration exists;
- no production repository exists;
- no database connection exists;
- no production persistence hook exists;
- current persistence stack remains test-only and in-memory;
- full `tests/agent` remains `543 passed`;
- readiness gates remain CLOSED.

R7BS-QA explicitly approved the design only, not implementation.

## 大白话说明

R7BT 是“未来 QA 怎么查”的清单，不是“现在开始建表”的开关。它给后续 R7BU/R7BV/R7BW 这类任务画红线：什么时候必须拦住、哪些字段必须看、哪些行为必须 fail closed、哪些结果绝对不能被误读成 clean_data、delivery/export 或 production readiness。小心驶得万年船，尤其是数据库这条河。

## Current baseline

Current approved chain:

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> test-only persistence contract
-> in-memory persistence candidate batch
-> test-only fake repository / in-memory repository boundary
-> fake repository negative-path and idempotency expansion
-> docs-only schema/migration design
-> schema/migration design QA
```

Baseline facts to preserve:

- current persistence stack is still test-only and in-memory;
- no real database schema exists;
- no migration exists;
- no production repository exists;
- R7BS-QA approved only the design, not implementation;
- latest known full `tests/agent` = `543 passed`;
- readiness gates remain CLOSED.

## Docs-only scope

R7BT only defines QA planning requirements for future schema/migration work. It does not:

- modify production code;
- modify tests;
- modify fixtures;
- add repository/model/service code;
- add database schema;
- add migration;
- add database connection;
- add storage implementation;
- write output files;
- run extraction;
- run MinerU/OCR/LLM/VLM;
- open readiness gates;
- claim production persistence;
- claim production readiness;
- claim client readiness;
- claim formal export readiness.

## Future schema QA checklist

Future reviewers must verify:

- conceptual table remains clearly mapped to `review_queue` only;
- schema does not become a clean_data, delivery, export, or production-readiness table;
- identity/hash fields are present and non-ambiguous;
- `review_item_id`, `run_id`, `source_file_hash`, `input_file_hashes`, `audit_hash`, `idempotency_key`, and `record_payload_hash` have clear ownership;
- status/action fields cannot imply clean_data admission or delivery unblock;
- only bounded `evidence_preview` and source_trace metadata are allowed;
- raw payload fields are absent;
- created/updated/retracted timestamps are DB-controlled or otherwise safely defined;
- caller-supplied non-deterministic timestamp fields remain rejected before persistence;
- soft retraction is supported without destructive delete by default;
- field names and versions match persistence contract vocabulary;
- schema versioning is explicit and monotonic;
- `candidate_unit`, if included, is either first-class and validated or deliberately excluded with rationale.

Blocker examples:

- schema includes full `source_text`;
- schema stores raw artifact JSON;
- schema includes `clean_data_eligible` as a writable promotion flag;
- schema allows `VERIFIED` rows to auto-enter clean_data or delivery.

## Future migration QA checklist

Future reviewers must verify:

- migration order is explicit and documented;
- migration can be applied in a clean local/test environment;
- migration has a safe forward-fix path;
- rollback policy avoids destructive data loss by default;
- migration does not auto-enable production persistence;
- migration does not create a default production connection;
- migration does not create export/delivery side effects;
- migration has a test-only rehearsal plan before production gate review;
- migration ledger/audit metadata is planned;
- migration is reversible only while no persisted data exists, otherwise forward-fix is preferred;
- migration does not change clean_data, delivery, export, or readiness behavior.

Required evidence before implementation proceeds:

- design review PASS;
- migration QA review PASS;
- explicit disabled skeleton scope;
- local test DB rehearsal plan;
- negative-path and rollback test plan.

## Future idempotency and uniqueness QA checklist

Future reviewers must verify:

- `idempotency_key` uniqueness is enforced;
- `review_item_id` uniqueness is enforced or explicitly scoped for active-row soft retraction;
- `record_payload_hash` consistency is recomputed by repository validation;
- same identity + same payload has deterministic no-op or same-receipt behavior;
- same identity + different payload is conflict/fail-closed;
- same `review_item_id` + different `idempotency_key` is conflict/fail-closed;
- no silent duplicate insert is possible;
- duplicate keys in the same batch are detected before write;
- transient retry behavior is safe and deterministic;
- idempotency behavior is covered by tests before any DB-backed repository is considered;
- conflict receipts/logs are metadata-only and do not leak raw payloads.

## Future index and query QA checklist

Future reviewers must verify indexes support:

- lookup by `review_item_id`;
- lookup by `idempotency_key`;
- lookup by `run_id`;
- lookup by `source_file_hash`;
- filtering by `review_status`;
- filtering by `agreement_status`;
- filtering by `re_audit_required`;
- ordering by `created_at` / `updated_at`;
- reviewer UI pagination;
- audit/debug lookup by `record_payload_hash`;
- source/debug lookup by `source_document_id`, `source_row_id`, and `matched_locator`.

QA must also verify:

- composite indexes do not imply unintended uniqueness;
- JSON/JSONB indexes are not added without backend-specific performance reasoning;
- index additions do not trigger production activation or writer side effects;
- query plans preserve review-only semantics.

## Future enum and constraint QA checklist

Future reviewers must verify:

- `agreement_status` is constrained to review-bound values unless separately approved;
- `review_status` cannot represent clean_data approval, delivery unblock, export readiness, or production readiness;
- `reviewer_action` cannot bypass explicit policy gates;
- corrective actions require `re_audit_required = true`;
- `blocked_delivery_reason` remains non-empty for unresolved rows;
- `created_by_system` is allowlisted;
- hash fields are 64-character lowercase SHA-256 hex strings;
- `evidence_preview` is non-empty and bounded;
- `retracted_at` requires `retraction_reason`;
- constraints prevent `STRONG_EVIDENCE` promotion from review_queue persistence.

Reviewers must block any enum that encodes:

- `CLEAN_DATA_APPROVED`;
- `DELIVERY_UNBLOCKED`;
- `READY_FOR_EXPORT`;
- `PRODUCTION_READY`;
- automatic `STRONG_EVIDENCE`.

## Future raw-payload exclusion QA checklist

Future schema/repository QA must require rejection of:

```text
full source_text
raw MinerU payload
raw Excel payload
raw parser/OCR payload
raw LLM/VLM response
connection secrets or runtime endpoints
output path/file path config
production writer config
readiness override
clean_data intent
delivery/export intent
```

Allowed evidence storage:

- bounded `evidence_preview`;
- `evidence_preview_sha256`;
- `source_trace` metadata;
- `matched_text_sha256`;
- source locator metadata.

Required QA methods:

- recursive forbidden-field tests;
- serialization inspection tests;
- receipt/output leak checks;
- nested payload negative cases;
- malformed source_trace negative cases.

## Future transaction and batch atomicity QA checklist

Future reviewers must verify:

- single-row atomic behavior;
- batch atomic behavior by default;
- no partial success by default;
- invalid row does not mutate persisted state;
- uniqueness conflict does not mutate persisted state;
- hash mismatch does not mutate persisted state;
- forbidden field does not mutate persisted state;
- audit event for attempt/result is metadata-only;
- safe retry after transient failure;
- manual recovery path for bad rows;
- transaction rollback is tested against a local test DB before production gate review.

Required tests before implementation proceeds:

- valid batch writes all rows;
- valid first row + invalid later row writes zero rows;
- retry same batch is deterministic;
- changed payload under same idempotency key fails closed;
- duplicate key in batch fails closed;
- DB exception simulation leaves state unchanged.

## Future rollback and forward-fix QA checklist

Future reviewers must verify:

- rollback is safe before data exists;
- after data exists, forward-fix is preferred over destructive rollback;
- bad rows are soft-retracted or quarantined;
- retraction preserves hash identities and audit metadata;
- manual recovery is documented;
- rollback does not alter clean_data eligibility;
- rollback does not unblock delivery/export;
- rollback does not open readiness gates;
- destructive delete requires separate retention/privacy design and QA approval.

## Future retention and retraction QA checklist

Future reviewers must verify:

- retention policy is documented before production persistence;
- retention does not require storing raw source payloads in review_queue;
- soft retraction uses `retracted_at` and `retraction_reason`;
- retracted rows remain audit-visible unless a separate privacy/delete policy applies;
- retracted rows remain excluded from clean_data and delivery/export;
- retraction cannot be used to rewrite idempotency history silently;
- reviewer-visible status for retracted/quarantined rows is explicit.

## Future feature gate and environment QA checklist

Future reviewers must verify:

- local test DB stages require an explicit test-only DB flag;
- repository remains disabled by default;
- no default production database connection exists;
- no production writer config is accepted in test-only paths;
- environment allowlist is explicit;
- environment variables alone cannot activate persistence;
- validated schema alignment preview cannot auto-activate persistence;
- production persistence flag is separate and blocked until production gate review;
- disabled production skeleton returns safe no-op metadata when disabled;
- readiness gates remain CLOSED during all test-only stages.

## Future audit and record hash QA checklist

Future reviewers must verify:

- `record_payload_hash` is recomputed from canonical payload;
- hash excludes only the hash field itself;
- hash canonicalization is deterministic;
- `audit_hash`, `idempotency_key`, `record_payload_hash`, `evidence_preview_sha256`, and `matched_text_sha256` are validated;
- persistence attempt/result audit event is metadata-only;
- audit records include input hashes, versions, run id, and status counts;
- audit records do not include raw source payloads or connection secrets;
- retry receipts are stable and deterministic;
- conflict receipts explain reason without leaking payload.

## Future clean_data/delivery/export separation QA checklist

Future reviewers must verify:

- `VERIFIED` does not imply `STRONG_EVIDENCE`;
- `VERIFIED` does not auto-write clean_data;
- non-VERIFIED rows remain review-bound;
- unresolved rows keep `blocked_delivery_reason`;
- corrected rows remain `re_audit_required`;
- persistence candidate does not trigger delivery;
- persistence candidate does not mutate clean_data;
- persistence candidate does not open readiness gates;
- stored review_queue rows do not contain clean_data write intent;
- stored review_queue rows do not contain delivery/export intent;
- review completion requires a separate explicit policy gate before any clean_data eligibility change.

## Performance and concurrency questions

Future QA must require answers before production gate review:

- expected row volume per run;
- expected total retained review_queue records;
- expected reviewer UI pagination size;
- concurrency model for multiple writers/runs;
- transaction isolation level;
- lock strategy for idempotency keys;
- behavior under duplicate concurrent insert attempts;
- timeout/retry policy;
- index cost under expected workload;
- migration runtime and lock impact;
- retention cleanup performance;
- backup/restore and disaster recovery expectations.

These are questions, not approvals. Lack of answers must block production gate review.

## Production gate prerequisites

Before any production hook consideration, reviewers must require:

- R7BT-QA PASS;
- schema/migration design QA PASS;
- disabled repository skeleton PASS;
- local test DB prototype behind explicit test flag PASS;
- local test DB negative-path tests PASS;
- local test DB rollback/forward-fix tests PASS;
- idempotency/concurrency tests PASS;
- raw-payload leakage tests PASS;
- clean_data/delivery/readiness separation tests PASS;
- migration rehearsal report PASS;
- production operational controls design PASS;
- explicit production gate review PASS.

Production hook consideration remains forbidden until all prerequisites pass.

## Implementation blockers / red flags

Any future reviewer must block implementation if:

- schema implies clean_data promotion;
- schema implies delivery/export readiness;
- migration enables production by default;
- repository can run without explicit test flag in test stages;
- production DB connection is defaulted or guessed;
- raw payloads can be stored;
- full `source_text` can be stored;
- duplicates can silently insert;
- batch can partially commit without explicit design approval;
- rollback requires destructive delete by default;
- readiness gates are opened without separate gate review;
- `VERIFIED` becomes `STRONG_EVIDENCE`;
- `VERIFIED` auto-enters clean_data;
- non-VERIFIED rows can bypass review_queue;
- connection secrets or runtime endpoints are stored;
- output path/file path config is accepted as persistence data;
- production writer config is accepted in test-only paths;
- migration creates delivery/export side effects.

## Open questions

- Which DB backend should be used for local test DB prototype?
- Should source trace be JSON/JSONB, normalized columns, or both?
- Should `review_item_id` be globally unique or active-row unique with retraction?
- Should audit events be a separate table in the first local DB prototype?
- How should reviewer corrections be versioned?
- What retention period is required?
- What concurrency target must be proven?
- What migration tooling should be used?
- What privacy/delete policy applies to review_queue metadata?
- What exact production gate checklist will R7BW/R7BX require?

## Non-goals

R7BT does not:

- modify production code;
- modify tests;
- modify fixtures;
- add repository/model/service code;
- add database schema;
- add migration;
- add database connection;
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

- QA plan is docs-only and not executable.
- No real database behavior is proven.
- No local DB prototype exists.
- Transaction/rollback behavior remains unimplemented.
- Concurrency/performance behavior remains unknown.
- Migration tooling and DB backend remain undecided.
- Production operational controls remain unimplemented.
- Readiness and formal export remain closed.

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
PASS: 63 passed in 0.49s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.40s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.14s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.24s

python -m pytest tests/agent -q
PASS: 543 passed in 2.23s

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
348N-R7BT-QA schema/migration QA docs-only review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BT docs-only schema/migration QA plan completed.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; fake repository 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 543 passed.
files_modified（修改文件数）= 1 allowed docs-only QA planning report file.
error_count（错误数）= 0.
schema_qa_plan_result（schema QA计划结果）= PASS; future schema QA checks cover review_queue-only mapping, identity/hash fields, bounded evidence metadata, version vocabulary, timestamps, and soft retraction.
migration_qa_plan_result（migration QA计划结果）= PASS; future migration QA checks cover order, clean apply, forward-fix, non-destructive rollback, no production activation, and rehearsal before production gate.
idempotency_uniqueness_qa_plan_result（幂等唯一性QA计划结果）= PASS; future QA checks cover unique keys, hash consistency, deterministic retry, conflict/fail-closed behavior, no silent duplicates, and batch duplicate detection.
index_query_qa_plan_result（索引查询QA计划结果）= PASS; future QA checks cover review UI, audit/debug, run/source/status/re-audit/hash lookup, pagination, and backend-specific index questions.
constraint_enum_qa_plan_result（约束枚举QA计划结果）= PASS; future QA checks cover review-bound enums, blocked delivery reason, corrective action re-audit, SHA-256 fields, bounded preview, and no clean/delivery/readiness implication.
raw_payload_exclusion_qa_plan_result（原始payload排除QA计划结果）= PASS; future QA must reject full source_text, raw MinerU/Excel/parser/OCR/LLM/VLM, secrets/endpoints, path/config, readiness, clean_data, and delivery/export intent.
transaction_atomicity_qa_plan_result（事务原子性QA计划结果）= PASS; future QA checks cover single-row and batch atomicity, no partial success, invalid-row no-mutation, audit attempt/result, retry, and recovery.
rollback_forward_fix_qa_plan_result（回滚/前向修复QA计划结果）= PASS; future QA checks cover rollback before data, forward-fix after data, soft retraction/quarantine, and no readiness/clean/delivery changes.
feature_gate_qa_plan_result（feature gate QA计划结果）= PASS; future QA checks cover explicit test-only DB flag, disabled default repository, environment allowlist, no default production DB, and no auto-activation from env/schema preview.
clean_data_delivery_boundary_qa_plan_result（clean_data/交付边界QA计划结果）= PASS; future QA preserves VERIFIED non-promotion, no auto clean_data, review-bound non-VERIFIED, blocked delivery reasons, and no delivery/export/readiness mutation.
production_gate_prerequisite_result（生产gate前置条件结果）= PASS; production hook consideration remains blocked until disabled skeleton, local test DB prototype, negative/rollback/concurrency/leakage tests, rehearsal, operations design, and production gate review pass.
red_flag_blocker_result（红线阻断项结果）= PASS; blocker list includes clean_data/export/readiness implication, default production activation, raw payload storage, silent duplicates, partial commits, destructive rollback, and readiness gate opening.
boundary_check（边界检查）= PASS; only docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BT-QA schema/migration QA docs-only review.
```
