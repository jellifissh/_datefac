# 348N-R7BW local test DB prototype design docs-only

## Task ID

```text
348N-R7BW local test DB prototype design docs-only
```

Task type: docs-only-local-test-db-design.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 65e4843..c9a9f10; R7BW task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -90
PASS: latest history includes c9a9f10 R7BW task doc, 65e4843 R7BV-QA, a7c73b7 R7BV QA hardening, 660bcf3 R7BU-QA, and 64eca71 R7BU skeleton.
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
- `docs/codex_tasks/348N_R7BW_local_test_DB_prototype_design_docs_only.md`
- `docs/agent/348N_R7BV_QA_REPOSITORY_SKELETON_QA_REVIEW.md`
- `docs/agent/348N_R7BV_REPOSITORY_SKELETON_QA_REPORT.md`
- `docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md`
- `docs/agent/348N_R7BU_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_NO_DB_CONNECTION_REPORT.md`
- `docs/agent/348N_R7BT_QA_SCHEMA_MIGRATION_QA_DOCS_ONLY_REVIEW.md`
- `docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md`
- `docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md`

Current repository skeleton and tests reviewed read-only:

- `datefac_agent/review/review_queue_repository.py`
- `tests/agent/test_review_queue_repository_skeleton_348n.py`
- `tests/agent/test_review_queue_repository_skeleton_qa_348n.py`

Related test-only chain reviewed read-only:

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

## R7BV-QA recap

R7BV-QA approved the repository skeleton QA hardening. The current `datefac_agent/review/review_queue_repository.py` module remains a disabled-by-default skeleton only:

- no DB connection;
- no SQL execution;
- no filesystem write;
- no storage client;
- no network client;
- no migration;
- no real repository implementation;
- no production writer hook;
- no clean_data, delivery, export, or readiness mutation path.

R7BV-QA validated the targeted repository skeleton QA suite at `32 passed` and the latest known full `tests/agent` count at `592 passed`. R7BW starts from that approved boundary and does not change code.

## 大白话说明

R7BW 只是在纸面上设计“以后如果要做本地测试数据库原型，该怎么安全地做”。这一轮不连数据库、不建表、不写 SQL、不写 migration、不写 repository adapter、不接生产流程。它的作用是先把安全门画清楚：必须显式 test-only、必须本地环境白名单、必须拒绝生产 DSN、必须事务回滚、必须幂等、必须不存 full source_text/raw payload、必须不碰 clean_data/delivery/readiness。简单说：现在还不造车，只画一个不能冲出测试场的试车规则。

## Current baseline

Current review_queue safety chain:

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
-> disabled-by-default repository interface skeleton
-> repository skeleton QA hardening
```

Current facts:

- current repository skeleton is disabled by default;
- current skeleton has no DB/IO/network behavior;
- current local DB prototype does not exist;
- no real database schema exists;
- no migration exists;
- no production repository exists;
- R7BV-QA approved targeted repository skeleton QA tests at `32 passed`;
- latest known full `tests/agent` is `592 passed`;
- readiness gates remain CLOSED.

## Docs-only scope

R7BW is docs-only because the current safe next step is to design the future test DB boundary before any implementation. The design must be reviewed before code can add:

- a DB dependency/import;
- a local DB adapter;
- schema creation code;
- migration code;
- connection handling;
- transaction/rollback behavior;
- repository factory activation;
- runner/CLI integration.

R7BW creates only this report. It does not modify production code, tests, fixtures, dependency files, outputs, existing docs, migrations, schemas, or readiness gates.

## Local test DB prototype scope

A future local test DB prototype may be used only to prove repository persistence behavior in a controlled test environment:

- schema creation in a temporary/local test context;
- transaction and rollback behavior;
- idempotent retry behavior;
- uniqueness/conflict behavior;
- safe metadata-only persistence;
- cleanup/teardown behavior;
- failure-mode coverage before any production gate discussion.

It must remain a prototype, not a production repository. It must not be called by current production-adjacent skeleton factory, review_queue_builder, clean_data, delivery/export, production adapter, runner, or CLI.

## Candidate local DB choice

Recommended first candidate for a later implementation task:

```text
SQLite in-memory or isolated temporary-file database
```

Why:

- stdlib `sqlite3` is usually available and avoids new dependencies;
- in-memory DB can prove transaction and uniqueness semantics with minimal cost;
- temporary-file DB can prove cleanup/teardown if explicitly allowed in a future test task;
- easier to keep local-only than PostgreSQL/Docker.

Tradeoffs:

- SQLite behavior is not identical to PostgreSQL, especially around concurrency, typing, JSON, and locking;
- in-memory DB does not prove file cleanup unless paired with a temporary-file variant;
- temporary-file DB introduces filesystem side effects that must be restricted to test temp paths.

Alternative future candidate:

```text
PostgreSQL test container
```

Use only if a later task explicitly allows Docker/test containers and dependency/runtime audit. It should not be the first implementation default because it increases setup cost and production-DSN risk.

Keep as valid unit-level baseline:

```text
pure fake repository / in-memory repository boundary
```

The existing fake repository remains valuable for fast boundary and negative-path tests even if a local test DB prototype is later added.

## Activation and environment gate design

A future local DB prototype must require all of the following before any DB connection or schema creation:

```text
explicit test-only flag
explicit local-test environment value
explicit test DSN or in-memory DB selection
hard rejection of production-looking DSNs
hard rejection of non-local hosts
no environment-variable-only activation
no default DB connection
no production writer config
no automatic activation from repository skeleton factory
no automatic activation from validated schema alignment preview
```

Recommended conceptual config for a future implementation:

```text
enabled = true
mode = local_test_db_only
test_only_enable_token = R7BW_LOCAL_TEST_DB_ENABLE
environment = local_test
db_backend = sqlite_memory | sqlite_temp_file
dsn = :memory: or explicit local test path only
allow_filesystem_side_effects = false by default
```

Invalid activation examples that must fail closed:

- missing explicit token;
- token from environment only;
- `environment = production`;
- `production_ready = true`;
- `formal_client_export_allowed = true`;
- DSN containing production-looking host/user/path;
- host not in an allowlist;
- `postgresql://prod...`;
- `mysql://...`;
- `sqlite:///D:/real/output/...`;
- production writer config;
- readiness override.

## Repository adapter boundary design

A future local test DB adapter must:

- implement the existing `ReviewQueueRepositoryPort` shape;
- remain separate from `DisabledReviewQueueRepository`;
- remain unavailable by default;
- be constructed only in tests or explicit local-test prototype paths;
- never be returned by `create_disabled_review_queue_repository()`;
- not be called by `review_queue_builder`, clean_data, delivery/export, or production adapter;
- not import `tests/agent` fake repository code into production code;
- not mutate clean_data;
- not trigger delivery/export;
- not open readiness gates.

Recommended module placement for a future prototype should be decided in its own task. Conservative options:

- test-only first: `tests/agent/review_queue_local_test_db_repository_348n.py`;
- production-adjacent disabled adapter later only after QA: `datefac_agent/review/review_queue_local_test_db_repository.py`.

R7BW does not choose an implementation path; it recommends starting test-only first.

## Schema/migration rehearsal design

Future schema/migration rehearsal must be local-test-only:

- schema creation only in test context;
- migration rehearsal only against local test DB;
- clean setup and teardown;
- forward migration preference;
- non-destructive rollback policy by default;
- manual recovery strategy for bad rows;
- no migration file in R7BW;
- no production migration in future prototype without separate gate review.

Future migration test stages:

```text
1. create empty local test DB
2. apply schema creation/migration under explicit test flag
3. validate table/constraint/index shape
4. insert valid metadata-only candidate rows
5. reject invalid/raw/production-like rows
6. run rollback/failure simulation
7. teardown and prove no residual state
```

No migration may enable production persistence. Migration metadata must remain local-test-only and must not imply readiness.

## Transaction and rollback design

Future tests must prove:

- single-row insert atomicity;
- batch insert atomicity;
- no partial success by default;
- invalid row rolls back entire batch;
- transaction failure rolls back all writes;
- read after failed write returns no residual rows;
- idempotent retry after rollback remains deterministic;
- rollback does not mutate clean_data, delivery/export, or readiness metadata.

Batch policy:

```text
validate entire batch -> begin transaction -> insert/update all rows -> commit
any validation/write/constraint error -> rollback -> return/raise fail-closed error
```

No partial success should be allowed unless a later design explicitly introduces and QA-approves a partial-write mode.

## Idempotency and uniqueness design

Future local DB prototype must prove:

- idempotent retry with same identity and payload is deterministic;
- same `idempotency_key` with different payload conflicts / fails closed;
- same `review_item_id` with different identity conflicts / fails closed;
- `record_payload_hash` consistency is enforced;
- no silent duplicate insert;
- batch duplicate `idempotency_key` fails before insert;
- batch duplicate `review_item_id` fails before insert.

Recommended uniqueness constraints:

```text
unique(idempotency_key)
unique(review_item_id)
optional unique(run_id, source_file_hash, metric_name, period, schema_version, contract_version)
```

Recommended retry behavior:

```text
same idempotency_key + same record_payload_hash = deterministic no-op or same receipt
same idempotency_key + different record_payload_hash = conflict / fail closed
same review_item_id + different idempotency_key = conflict / fail closed
```

## Raw-payload exclusion design

Future local DB prototype must reject and never store:

```text
full source_text
raw MinerU payload
raw Excel payload
raw parser payload
raw OCR payload
raw LLM/VLM response
DB secrets or production DSNs
output path / file path config
production writer config
readiness override
clean_data intent
delivery/export intent
```

Allowed storage should be restricted to metadata-first fields:

- bounded `evidence_preview`;
- `evidence_preview_sha256`;
- constrained `source_trace`;
- candidate identity fields;
- status/action fields;
- run/input/version metadata;
- audit/hash fields.

Recommended enforcement layers:

1. upstream persistence contract validation;
2. local DB repository adapter validation;
3. DB schema allowlisted columns only;
4. metadata-only receipt;
5. source inspection tests for forbidden serialization.

## Audit and record hash design

Future local DB prototype must recompute and enforce hashes before writing:

- `audit_hash`;
- `record_payload_hash`;
- `idempotency_key`;
- `evidence_preview_sha256`;
- `matched_text_sha256` where present.

Rules:

- hashes must be deterministic, lowercase, 64-character SHA-256 hex strings;
- caller-supplied `record_payload_hash` must match recomputed payload hash;
- caller-supplied hash cannot override repository-computed hash;
- stored payload hash is immutable for the accepted record;
- changed payload requires a new explicit reviewed version/retraction design, not silent overwrite;
- metadata-only audit event should record attempt/result/error category if an audit event table is later allowed.

## Failure-mode test plan

Future implementation must include tests for:

```text
missing identity fields
malformed idempotency_key
malformed record_payload_hash
duplicate idempotency_key same payload
duplicate idempotency_key different payload
duplicate review_item_id conflict
batch with later invalid row
transaction failure rollback
bad enum/status value
raw payload leakage attempt
production DSN/config attempt
environment activation attempt
read after failed write
cleanup/teardown leaves no residual state
```

Additional recommended negative cases:

- non-local host in DSN;
- missing explicit test-only token;
- environment variable tries to enable without explicit config;
- clean_data intent in nested payload;
- delivery/export intent in nested payload;
- readiness override in nested payload;
- output path/file path config;
- user-supplied fake receipt or DB internal state;
- concurrent-ish duplicate retry if supported by chosen backend.

## Cleanup and teardown strategy

Future local DB tests must prove cleanup:

- in-memory DB connections close at test end;
- temporary file DB uses test temp directories only;
- teardown removes temp files when a temp-file DB is used;
- failed setup leaves no partial schema or files;
- failed write leaves no residual rows;
- repeated test runs are deterministic;
- cleanup failure is reported loudly, not ignored.

No future prototype should write to `output/`, `input/`, `temp/`, `data/`, legacy folders, or repository root DB files.

## No-production-connection guarantees

Future implementation must reject:

- production-looking DSNs;
- non-local hosts;
- default DB URLs;
- cloud/storage endpoints;
- environment-variable-only activation;
- production writer config;
- production readiness flags;
- formal export flags.

Recommended allowlist:

```text
backend = sqlite_memory
dsn = :memory:

or, if explicitly allowed later:
backend = sqlite_temp_file
path under pytest tmp_path only
```

PostgreSQL test container must remain blocked unless a later task explicitly allows it and adds:

- dependency/runtime audit;
- local host allowlist;
- container lifecycle plan;
- production-DSN rejection tests;
- teardown tests;
- QA review.

## clean_data/delivery/export separation

Future local DB prototype must preserve these safety rules:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED rows remain review-bound
unresolved rows keep blocked_delivery_reason
corrected rows remain re-audit-required
persistence candidate does not trigger delivery
persistence candidate does not mutate clean_data
persistence candidate does not open readiness gates
bounded evidence_preview allowed
full source_text forbidden
raw MinerU/raw Excel/raw parser/raw LLM-VLM payloads forbidden
```

The local DB prototype may persist only future review_queue-like metadata rows for tests. It must not persist clean_data, delivery rows, export manifests, client-ready artifacts, or formal delivery output.

## Future validation plan

A future implementation task must at minimum run:

```text
python -m py_compile datefac_agent/review/review_queue_repository.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
python -m py_compile <future local test DB adapter/test files>
python -m pytest <future local test DB targeted tests> -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Future local DB implementation validation should also include tests proving:

- no production DSN acceptance;
- no environment-only activation;
- transaction rollback on invalid batch;
- cleanup/teardown removes residual state;
- serialized receipts remain metadata-only;
- readiness gates remain closed.

## Open questions

- Should the first local DB prototype use SQLite `:memory:` only, or also a `tmp_path` temporary file variant?
- Should the first adapter live entirely under `tests/agent/` or add a production-adjacent disabled local-test module after another gate?
- Should future schema creation be raw SQL for local tests or an abstraction that can later align with PostgreSQL?
- Should audit events be part of the first local DB prototype or a later slice?
- How much concurrency behavior must be proven before any production persistence discussion?
- Which fields require indexes in the first test DB prototype versus later performance work?
- Should soft retraction/versioning be included in the first local DB prototype or deferred?
- What operational review is required before a PostgreSQL test container can be allowed?

## Non-goals

R7BW does not:

- modify production code;
- modify tests;
- modify fixtures;
- add database adapter;
- add repository implementation;
- add database model;
- add database schema;
- add migration;
- add DB connection;
- add SQL execution;
- add storage implementation;
- write output files;
- run extraction;
- run MinerU/OCR/LLM/VLM;
- connect to Docker/PostgreSQL/SQLite;
- open readiness gates;
- claim production persistence;
- claim production readiness;
- claim client readiness;
- claim formal export readiness.

## Remaining risks

- local test DB prototype is only designed, not implemented;
- real DB transaction behavior is not proven;
- real migration behavior is not proven;
- concurrency behavior is not proven;
- performance behavior is not proven;
- cleanup/teardown behavior is not proven;
- production operation controls are not proven;
- client/export readiness still not implied.

## Recommended next task

```text
348N-R7BW-QA local test DB prototype design review
```

R7BW-QA should review this design before any local test DB implementation task begins.

## Validation outputs

```text
python -m py_compile datefac_agent/review/review_queue_repository.py
PASS

python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
PASS

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

python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
PASS: 32 passed in 0.10s

python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
PASS: 17 passed in 0.08s

python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
PASS: 63 passed in 0.49s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.41s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.17s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.16s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.39s

python -m pytest tests/agent -q
PASS: 592 passed in 2.98s
```

Final git status/diff checks are recorded after report creation.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BW docs-only local test DB prototype design completed without implementation.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; repository QA 32 passed, skeleton 17 passed, fake repository 63 passed, persistence contract 76 passed, schema alignment 29 passed, dry-run integration 36 passed, writer contract 24 passed, adapter skeleton 75 passed, full tests/agent 592 passed.
files_modified（修改文件数）= 1; only the allowed R7BW design report was created.
error_count（错误数）= 0.
local_test_db_design_result（本地测试DB设计结果）= PASS; future local test DB prototype scope, candidate backend choices, and safe test-only purpose are documented.
activation_gate_design_result（激活门设计结果）= PASS; explicit test-only flag, token, local-test mode, and no automatic activation are required.
environment_allowlist_design_result（环境白名单设计结果）= PASS; local-only backend/DSN selection and rejection of production/non-local hosts are required.
repository_adapter_boundary_design_result（repository adapter边界设计结果）= PASS; future adapter must remain separate from disabled skeleton, unavailable by default, and not called by production paths.
schema_migration_rehearsal_design_result（schema/migration rehearsal设计结果）= PASS; schema creation/migration rehearsal is test-context-only with clean setup/teardown and no R7BW migration file.
transaction_rollback_design_result（事务回滚设计结果）= PASS; future tests must prove atomic single/batch writes, rollback on invalid rows, and no partial success by default.
idempotency_uniqueness_design_result（幂等唯一性设计结果）= PASS; same-key/same-hash retry, conflict handling, uniqueness constraints, and no duplicate insert behavior are specified.
raw_payload_exclusion_design_result（原始payload排除设计结果）= PASS; full source_text, raw MinerU/Excel/parser/OCR/LLM/VLM, secrets, production DSNs, paths, clean/delivery/readiness intents remain forbidden.
audit_record_hash_design_result（审计record hash设计结果）= PASS; deterministic SHA-256 audit/record/evidence hash recomputation and immutability rules are specified.
failure_mode_test_plan_result（失败模式测试计划结果）= PASS; required future negative-path, rollback, duplicate, env, production config, raw payload, and cleanup tests are listed.
cleanup_teardown_design_result（清理teardown设计结果）= PASS; future local DB tests must close connections, remove temp files if used, and prove no residual state.
no_production_connection_design_result（无生产连接设计结果）= PASS; production-looking DSNs, non-local hosts, default DB URLs, cloud endpoints, and env-only activation must fail closed.
clean_data_delivery_boundary_result（clean_data/交付边界结果）= PASS; future prototype must not mutate clean_data, trigger delivery/export, promote evidence, or open readiness gates.
boundary_check（边界检查）= PASS; R7BW creates only docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7BW-QA local test DB prototype design review.
```
