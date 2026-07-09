# 348N-R7CA local test DB prototype implementation planning docs-only

## Task ID

```text
348N-R7CA local test DB prototype implementation planning docs-only
```

Task type: docs-only-implementation-planning.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward e9a3099..f86c790; R7CA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -120
PASS: latest history includes f86c790 R7CA task doc, e9a3099 R7BZ-QA, dfdecee R7BZ checkpoint, c1b05dc R7BY-QA, and 06295b5 R7BY negative-path expansion.
```

## Files reviewed

Required context reviewed:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/348N_R7CA_local_test_DB_prototype_implementation_planning_docs_only.md`
- `docs/agent/348N_R7BZ_QA_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BZ_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT.md`
- `docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md`
- `docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md`

Read-only baseline files reviewed:

- `tests/agent/review_queue_local_test_db_adapter_boundary_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py`
- `datefac_agent/review/review_queue_repository.py`
- `tests/agent/test_review_queue_repository_skeleton_348n.py`
- `tests/agent/test_review_queue_repository_skeleton_qa_348n.py`
- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`

## R7BZ-QA recap

R7BZ-QA approved the local test DB boundary handoff checkpoint. It confirmed the checkpoint accurately summarized the post-R7BY-QA baseline:

- local test DB boundary remains test-only under `tests/agent`;
- repository skeleton remains disabled by default;
- no real local DB adapter exists;
- no DB connection, SQL execution, schema, migration, production repository, `review_queue_builder` integration, clean_data integration, or delivery/export integration exists;
- latest known full `tests/agent` is `735 passed`;
- readiness gates remain CLOSED.

R7BZ-QA recommended this docs-only planning task as the next safe slice:

```text
348N-R7CA local test DB prototype implementation planning docs-only
```

## 大白话说明

R7CA 不是写数据库功能，而是给“如果下一轮真要写一个本地测试 DB prototype”画施工图。施工图要说清楚：第一刀只允许在测试区做最小 SQLite `:memory:` 证明，schema 只能在测试 setup 里创建，所有状态必须测试内销毁，生产 repository 继续 disabled，不能接 `review_queue_builder`，不能写 clean_data，不能交付导出，不能打开 readiness。今天仍然不连 SQLite/PostgreSQL/Docker，不写 SQL 文件，不建 migration，不改生产代码。

## Planning scope

R7CA is docs-only implementation planning. It creates exactly:

- `docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md`

It does not implement adapter code, modify tests, modify fixtures, connect to a database, create schema/migration files, execute SQL, write output files, or change production paths.

## Current baseline

Current baseline after R7BZ-QA:

- repository skeleton remains disabled by default;
- local test DB boundary exists only under `tests/agent`;
- negative-path expansion exists only under `tests/agent`;
- no real local DB adapter exists;
- no real DB connection exists;
- no SQL execution exists;
- no schema exists;
- no migration exists;
- no production repository exists;
- no `review_queue_builder` integration exists;
- no clean_data integration exists;
- no delivery/export integration exists;
- latest known full `tests/agent` = `735 passed`;
- readiness gates remain CLOSED.

## Smallest safe future implementation slice

The smallest safe future implementation slice should be a test-only local DB prototype under `tests/agent`, not production code. Recommended first slice:

1. Add a new test-only module that owns an in-memory SQLite adapter prototype.
2. Require an explicit config object with all local-test gates.
3. Use only `sqlite3.connect(":memory:")` inside tests.
4. Create schema only inside test setup or adapter initialization for the test-only object.
5. Insert one metadata-only review_queue candidate row after all gates pass.
6. Prove reads only from the same test-owned in-memory connection.
7. Prove transaction rollback on invalid batch.
8. Prove teardown/close removes all state.
9. Keep `datefac_agent/review/review_queue_repository.py` disabled by default.
10. Keep all production factories unable to construct or import the test-only adapter.

If this slice is considered too much for one task, split further: first implement only connection/config/schema setup tests with no inserts, then add insert/rollback tests in a later slice.

## Candidate future files

Recommended future implementation files:

- `tests/agent/review_queue_local_test_db_adapter_prototype_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_prototype_348n.py`
- `docs/agent/348N_R7CB_LOCAL_TEST_DB_ADAPTER_PROTOTYPE_TEST_ONLY_REPORT.md`

Optional small fixture, only if needed and curated:

- `tests/agent/fixtures/review_queue_local_test_db/r7cb_metadata_only_candidates.json`

Files that must not be changed in the first implementation slice unless a later task explicitly permits:

- `datefac_agent/review/review_queue_repository.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/*`
- dependency/config files
- output/input/temp/data/legacy directories
- migration/schema directories

## Candidate future tests

Future implementation tests should cover:

- module imports only in `tests/agent`;
- no production module imports the test-only adapter;
- default disabled state;
- explicit config required;
- environment variables cannot activate the adapter;
- production/staging/cloud/remote config rejected;
- file path DB rejected by default;
- only `sqlite_memory` + `:memory:` accepted;
- schema created only for the test-owned in-memory connection;
- metadata-only row insert succeeds after all gates pass;
- full `source_text` and raw payload fields are rejected before insert;
- invalid row causes full transaction rollback;
- duplicate idempotency conflict fails closed;
- same idempotency key + same payload returns deterministic no-duplicate behavior;
- teardown closes connection and leaves no accessible state;
- readiness gates remain closed;
- clean_data/delivery/export counters remain zero;
- existing R7BX/R7BY/R7BU/R7BV tests still pass.

## Candidate local DB choice

Recommended first local DB choice:

```text
sqlite3 in-memory database, DSN exactly ":memory:"
```

Reasons:

- available in Python stdlib;
- no dependency addition;
- no Docker;
- no external service;
- no file path by default;
- state disappears when connection closes;
- adequate for first proof of local schema, insert, rollback, uniqueness, and teardown concepts.

Not recommended for first slice:

- SQLite temp-file DB, because file cleanup/path policy adds extra IO risk;
- PostgreSQL container, because Docker/runtime/dependency/audit scope is too large;
- production database, always forbidden.

## Activation gate plan

Future implementation must require all of:

- explicit config object;
- `enabled = true`;
- `test_only = true`;
- `environment = local_test`;
- exact test-only enable token for the future slice;
- `db_selection = sqlite_memory`;
- `dsn = :memory:`;
- explicit activation source, not environment;
- caller declares no production writer config;
- caller declares no clean_data/delivery/export/readiness intent.

Even with valid activation, the adapter must remain test-only and unavailable to production code.

## Config allowlist plan

Allow only these config keys in the first implementation slice:

- `enabled`
- `test_only`
- `environment`
- `db_selection`
- `dsn`
- `activation_source`
- `test_only_enable_token`
- optional `schema_version`
- optional `run_id`

Reject everything else by default, especially:

- production/staging/dev-prod environment values;
- `postgres://`, `postgresql://`, `mysql://`, `sqlite:///`, file path, cloud, remote host, endpoint, or port config;
- `connection_string`;
- secrets, passwords, API keys, tokens other than the explicit test-only token;
- table/schema/migration names supplied by caller;
- production writer config;
- readiness override;
- clean_data intent;
- delivery/export intent.

Failure messages must remain generic and not echo sensitive values.

## Local-only schema setup plan

First implementation slice may create schema only in the test-owned in-memory SQLite connection. Requirements:

- schema creation is inside the test-only module or test setup;
- no schema file is created;
- no migration file is created;
- table names are constants owned by the test-only module, not caller config;
- schema includes only review_queue-like metadata fields;
- no full source text or raw payload columns;
- no clean_data/delivery/export tables;
- schema setup failure leaves no partial usable adapter;
- schema setup is not reachable from production factories.

Minimal first table shape can include:

- `review_item_id`
- `idempotency_key`
- `record_payload_hash`
- `run_id`
- `agreement_status`
- `evidence_preview`
- `evidence_preview_sha256`
- `source_trace_json`
- `created_by_system`

## Transaction and rollback plan

Future tests must prove:

- single-row insert runs inside transaction;
- batch insert runs inside transaction;
- invalid row before SQL prevents transaction start or rolls back;
- invalid row after first insert rolls back entire batch;
- injected mid-batch validation failure leaves zero rows;
- read-after-failed-write returns no rows;
- transaction failure does not mutate input candidates;
- transaction failure does not write clean_data, delivery/export, or readiness metadata.

No partial success is allowed by default.

## Idempotency and uniqueness plan

Future adapter prototype must enforce:

- unique `idempotency_key`;
- unique `review_item_id`;
- deterministic `record_payload_hash`;
- same `idempotency_key` + same `record_payload_hash` produces deterministic no-duplicate retry result;
- same `idempotency_key` + different `record_payload_hash` fails closed;
- same `review_item_id` + conflicting identity fails closed;
- duplicate entries in same batch fail before or within transaction with full rollback;
- caller-supplied DB primary keys are forbidden.

For SQLite in-memory, these can be represented with table `UNIQUE` constraints plus pre-validation. The tests must not overclaim this as production-grade idempotency.

## Raw payload exclusion plan

Future prototype must reject before storage:

- full `source_text`;
- `full_source_text`;
- raw MinerU payload;
- raw Excel payload;
- raw parser payload;
- raw OCR payload;
- raw LLM payload;
- raw VLM payload;
- unbounded evidence text;
- clean_data payload;
- delivery/export payload;
- readiness override;
- caller-supplied DB row;
- caller-supplied DB receipt;
- internal adapter state.

Only bounded metadata fields may be stored, and `evidence_preview` should keep the existing length cap or a stricter future cap.

## Cleanup and teardown plan

Future implementation must include teardown tests:

- close SQLite in-memory connection;
- reject operations after close;
- no filesystem DB file exists;
- repeated test runs produce independent state;
- failed setup does not leave usable adapter;
- failed insert does not leave rows;
- cleanup failure is loud and test-visible.

No temp-file DB should be used in the first slice. If a later task permits temp-file DB, it must add explicit temp-path-only, cleanup, residual-file, and no-output-dir tests.

## No-production-connection guarantees

Future implementation plan must guarantee:

- no production code integration by default;
- no automatic activation from environment variables;
- no production DSN;
- no remote host;
- no cloud endpoint;
- no file path DB by default;
- no migration files in the first implementation slice;
- no `review_queue_builder` integration;
- no production repository factory activation;
- no runner/CLI integration;
- no output writer;
- no claim of production persistence.

The test-only adapter must not be imported by `datefac_agent/`.

## clean_data/delivery/export separation

Future implementation must preserve:

- no clean_data mutation;
- no delivery/export trigger;
- no readiness gate mutation;
- no `VERIFIED -> STRONG_EVIDENCE` promotion;
- no `VERIFIED -> clean_data` automatic admission;
- non-VERIFIED rows remain review-bound;
- unresolved rows stay delivery-blocked;
- corrected rows remain re-audit-required.

The local DB prototype may store only review_queue-like metadata rows in test context.

## Future validation commands

Future implementation should run at least:

```text
python -m py_compile tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
python -m py_compile tests/agent/review_queue_local_test_db_adapter_prototype_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_prototype_348n.py
python -m py_compile datefac_agent/review/review_queue_repository.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_prototype_348n.py -q
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Add source inspection tests for no production import, no file DB path, no network, no Docker, no dependency additions, and no output writes.

## Stop conditions

Future implementation must stop and report BLOCKED if:

- production code must be modified to make the test pass;
- a dependency addition is required;
- a file path DB is required;
- PostgreSQL/Docker is required;
- schema/migration files are required;
- environment-only activation is needed;
- production-looking DSN/host/path must be accepted;
- raw payload/source_text storage is needed;
- clean_data/delivery/export integration is needed;
- readiness gates would need to open;
- tests require output/input/temp/data/legacy writes;
- validation cannot prove no partial writes after failed batch.

## Risks and open questions

Risks:

- SQLite in-memory transaction behavior is useful but not equivalent to production PostgreSQL behavior.
- Schema defined in test-only code may diverge from future production schema.
- Idempotency semantics may need adjustment for real persistence.
- Cleanup is simple for in-memory DB but not representative of file/container DB.
- Concurrency behavior is not meaningfully proven by a first in-memory slice.

Open questions:

- Should the first prototype accept one-row insert only, or batch insert too?
- Should schema be inline constants or generated from a future schema contract fixture?
- Should `evidence_preview_sha256` be required from caller or recomputed by adapter?
- Should the adapter return receipts or only queryable rows?
- When should a later task consider SQLite temp-file or PostgreSQL container?

## Non-goals

R7CA does not:

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
- add file writes;
- add output writer;
- run extraction;
- run MinerU/OCR/LLM/VLM;
- connect to SQLite/PostgreSQL/Docker;
- open readiness gates;
- claim production persistence;
- claim production readiness;
- claim client readiness;
- claim formal export readiness.

## Recommended next task

Recommended next task:

```text
348N-R7CA-QA local test DB prototype implementation planning review
```

R7CA-QA should review this implementation plan for accuracy, conservative scope, no-overclaim, and readiness safety before any prototype code is attempted.

## Validation outputs

```text
python -m py_compile tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
PASS

python -m py_compile datefac_agent/review/review_queue_repository.py
PASS

python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
PASS

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
PASS: 88 passed in 0.17s

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
PASS: 55 passed in 0.13s

python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
PASS: 32 passed in 0.10s

python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
PASS: 17 passed in 0.08s

python -m pytest tests/agent -q
PASS: 735 passed in 2.49s

git status -sb
PASS before report creation: clean.

git diff --stat
PASS before report creation: no tracked diff.

git diff --name-only
PASS before report creation: no tracked diff.

git diff --check
PASS before report creation: no whitespace errors.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7CA docs-only implementation planning completed without implementing DB behavior.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; negative-path tests 88 passed; R7BX boundary tests 55 passed; repository QA 32 passed; repository skeleton 17 passed; full tests/agent 735 passed.
files_modified（修改文件数）= 1; only docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md was created.
error_count（错误数）= 0.
implementation_planning_result（实施计划结果）= PASS; first future implementation slice is specified as test-only planning, not implementation.
smallest_safe_slice_result（最小安全切片结果）= PASS; recommended first slice is explicit-gated in-memory SQLite inside tests/agent only, with no production integration.
candidate_file_plan_result（候选文件计划结果）= PASS; future files are limited to tests/agent prototype/test/report and optional small curated fixture.
candidate_test_plan_result（候选测试计划结果）= PASS; future tests cover activation gates, config rejection, metadata-only insert, rollback, idempotency, teardown, and compatibility.
activation_gate_plan_result（激活门计划结果）= PASS; explicit config/token/local_test/sqlite_memory/:memory: gates required; env-only activation forbidden.
config_allowlist_plan_result（配置白名单计划结果）= PASS; narrow allowlist defined and production DSN/host/path/secret/schema/table/migration/readiness/clean/export config rejected.
local_schema_setup_plan_result（本地schema设置计划结果）= PASS; schema may be created only inside test-owned in-memory connection; no schema/migration files.
transaction_rollback_plan_result（事务回滚计划结果）= PASS; future tests must prove atomic insert, invalid batch rollback, and read-after-failed-write empty state.
idempotency_uniqueness_plan_result（幂等唯一性计划结果）= PASS; unique idempotency/review IDs, deterministic hash, conflict fail-closed, and no duplicate insert required.
raw_payload_exclusion_plan_result（原始payload排除计划结果）= PASS; full source_text and raw MinerU/Excel/parser/OCR/LLM/VLM payloads forbidden before storage.
cleanup_teardown_plan_result（清理teardown计划结果）= PASS; close in-memory connection, reject after close, no file DB, no residual rows, loud cleanup failure required.
no_production_connection_plan_result（无生产连接计划结果）= PASS; no production code integration, no production DSN, no remote host, no file DB, no env activation, no runner/CLI.
clean_data_delivery_boundary_result（clean_data/交付边界结果）= PASS; no clean_data mutation, delivery/export trigger, readiness opening, or evidence promotion allowed.
boundary_check（边界检查）= PASS; docs-only report, no code/tests/fixtures/output/dependencies/schema/migration/readiness changes.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7CA-QA local test DB prototype implementation planning review.
```
