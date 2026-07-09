# 348N-R7BU repository interface skeleton disabled-by-default, no DB connection

## Task ID

```text
348N-R7BU repository interface skeleton disabled-by-default, no DB connection
```

Task type: disabled-production-adjacent-skeleton-no-db.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward d2e5dc0..b65b546; R7BU task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -80
PASS: latest history includes b65b546 R7BU task doc, d2e5dc0 R7BT-QA, 314a96f R7BT-QA task doc, and 6254c42 R7BT QA plan.
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
- `docs/codex_tasks/348N_R7BU_repository_interface_skeleton_disabled_by_default_no_DB_connection.md`
- `docs/agent/348N_R7BT_QA_SCHEMA_MIGRATION_QA_DOCS_ONLY_REVIEW.md`
- `docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md`
- `docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md`
- `docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md`

Current test-only files reviewed:

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

Production-adjacent modules reviewed read-only:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`

## R7BT-QA recap

R7BT-QA approved the docs-only schema/migration QA plan. It confirmed future schema/migration work must remain blocked by conservative QA gates for:

- review_queue-only schema mapping;
- migration order and forward-fix policy;
- idempotency/uniqueness;
- index/query patterns;
- enum/check constraints;
- raw-payload exclusion;
- transaction/batch atomicity;
- rollback/retraction;
- feature flags/environment gates;
- audit/hash consistency;
- clean_data/delivery/export separation.

R7BT-QA recommended this task as the next safe slice:

```text
348N-R7BU repository interface skeleton disabled-by-default, no DB connection
```

## 大白话说明

这轮只放了一个“未来 repository 长什么样”的空骨架。它默认关闭，所有写、读、列表操作都会 fail closed；不连数据库、不写文件、不建表、不 migration、不接 runner、不接生产。它像一扇未来可能会有门锁的门框，但现在没有钥匙、没有门、没有通向数据库的小暗道。

## Skeleton scope

Created production-adjacent skeleton:

- `datefac_agent/review/review_queue_repository.py`

Created focused tests:

- `tests/agent/test_review_queue_repository_skeleton_348n.py`

Created this report:

- `docs/agent/348N_R7BU_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_NO_DB_CONNECTION_REPORT.md`

No package import file change was required; tests import the module directly.

## Disabled-by-default behavior

The skeleton exposes only disabled behavior:

- `DisabledReviewQueueRepository.write_batch(...)` raises `ReviewQueueRepositoryDisabledError`;
- `DisabledReviewQueueRepository.get_by_review_item_id(...)` raises `ReviewQueueRepositoryDisabledError`;
- `DisabledReviewQueueRepository.list_by_run_id(...)` raises `ReviewQueueRepositoryDisabledError`;
- `create_disabled_review_queue_repository()` returns a disabled repository by default;
- arbitrary config passed to the factory is rejected fail-closed;
- custom disabled reasons are rejected to prevent secret/raw payload leakage through receipts or messages.

No method silently succeeds or claims persistence happened.

## Interface shape

The module defines:

- `ReviewQueueRepositoryError`;
- `ReviewQueueRepositoryDisabledError`;
- `ReviewQueueRepositoryWriteReceipt`;
- `ReviewQueueRepositoryPort`;
- `DisabledReviewQueueRepository`;
- `create_disabled_review_queue_repository()`.

The port shape matches the planned future boundary:

```text
write_batch(candidates, *, run_id=None)
get_by_review_item_id(review_item_id)
list_by_run_id(run_id)
```

This is interface shape only; it is not a real repository implementation.

## No-DB / no-IO / no-network guarantee

The skeleton imports only:

- `copy.deepcopy`;
- `dataclasses.dataclass`;
- typing helpers.

It does not import:

- `sqlite3`;
- `sqlalchemy`;
- `psycopg` / `psycopg2`;
- `pymysql` / `mysql` / `asyncpg`;
- `redis`;
- `boto3` / `botocore`;
- network clients;
- filesystem/path modules;
- `tests/agent` fake repository code.

Static AST tests verify no forbidden DB/IO/network/storage imports or calls exist.

## Factory behavior

`create_disabled_review_queue_repository()`:

- takes no enabling token;
- reads no environment variables;
- accepts no DB/runtime config;
- rejects arbitrary production-looking config without echoing values;
- returns `DisabledReviewQueueRepository` only.

Passing DSNs, connection strings, table names, file paths, output paths, runtime endpoints, or production writer config fails closed.

## Receipt behavior

`ReviewQueueRepositoryWriteReceipt` is disabled-only and non-persisting.

`DisabledReviewQueueRepository.disabled_receipt().as_dict()` reports:

- `repository_status = DISABLED`;
- `persistence_status = NOT_PERSISTED`;
- all write flags false;
- all write counters zero;
- readiness gates closed.

The receipt has no DB IDs, table names, DSNs, paths, raw payloads, full source text, clean_data intent, delivery/export intent, or production writer config.

## Input mutation safety

`write_batch(...)` fails closed without mutating candidate input objects. It does not store candidates in memory as production state.

Tests pass candidate objects containing raw/source/secret-looking fields and assert:

- the original input remains unchanged;
- error messages do not include raw payload values;
- error messages do not include secrets or connection strings.

## Raw payload and secret leakage safety

Tests verify failure messages and disabled receipts do not leak:

- full `source_text`;
- raw MinerU payload;
- raw Excel payload;
- raw OCR/parser/model payloads;
- connection strings;
- runtime endpoints;
- unsafe paths;
- production writer config values.

The skeleton keeps messages generic and metadata-only.

## Compatibility with fake repository boundary

The R7BQ/R7BR fake repository remains test-only under `tests/agent/`.

The new production-adjacent skeleton:

- does not replace fake repository tests;
- does not weaken fake repository idempotency/negative-path tests;
- does not import `tests.agent`;
- does not import fake repository helpers into production code;
- does not provide an in-memory production substitute.

R7BQ/R7BR fake repository targeted tests still pass.

## Validation outputs

```text
python -m py_compile datefac_agent/review/review_queue_repository.py
PASS

python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
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

python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
PASS: 17 passed in 0.08s

python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
PASS: 63 passed in 0.49s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.42s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.24s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.14s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.25s

python -m pytest tests/agent -q
PASS: 560 passed in 2.26s

git status -sb
PASS before report creation: only allowed new skeleton and test files were untracked.

git diff --stat
PASS before report creation: no tracked diff; new allowed files untracked.

git diff --name-only
PASS before report creation: no tracked diff; new allowed files untracked.

git diff --check
PASS: no whitespace errors.
```

## Limitations

- No real repository implementation exists.
- No database schema exists.
- No migration exists.
- No database connection exists.
- No SQL execution exists.
- No storage adapter exists.
- No output writer/export path exists.
- No production hook exists.
- No transaction, rollback, concurrency, local test DB, or production persistence behavior is proven.

## Decision

PASS. R7BU adds a minimal production-adjacent review_queue repository interface skeleton that is disabled by default, fails closed for write/read/list, performs no DB/IO/network/storage actions, accepts no production config, leaks no raw payloads/secrets, does not import fake repository test code, and does not mutate clean_data, delivery/export, or readiness gates.

## Recommended next task

```text
348N-R7BU-QA repository interface skeleton disabled-by-default review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; disabled no-DB repository interface skeleton implemented.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; repository skeleton 17 passed; fake repository 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 560 passed.
files_modified（修改文件数）= 3 allowed files.
error_count（错误数）= 0.
repository_skeleton_result（repository骨架结果）= PASS; minimal ReviewQueueRepositoryPort, DisabledReviewQueueRepository, errors, factory, and disabled receipt added.
disabled_by_default_result（默认关闭结果）= PASS; factory returns disabled repository and every write/read/list operation fails closed.
no_db_connection_result（无DB连接结果）= PASS; no DB imports, connection strings, SQL execution, table creation, migration, schema creation, or default DB config.
no_io_no_network_result（无IO无网络结果）= PASS; no filesystem write, network, storage, output writer, or export behavior.
factory_behavior_result（factory行为结果）= PASS; factory accepts no production/runtime config and rejects arbitrary config without leaking values.
write_fail_closed_result（写入fail-closed结果）= PASS; write_batch raises disabled error and persists nothing.
read_fail_closed_result（读取fail-closed结果）= PASS; get/list methods raise disabled error and expose no state.
config_rejection_result（配置拒绝结果）= PASS; DSN, connection string, table name, file/output path, production writer config, and runtime endpoint inputs are rejected.
input_mutation_safety_result（输入变更安全结果）= PASS; failed writes do not mutate candidate objects or retain production state.
raw_payload_leakage_result（原始payload泄漏结果）= PASS; messages and disabled receipts do not leak full source_text, raw MinerU/Excel/OCR/parser/LLM/VLM payloads, secrets, endpoints, or paths.
clean_data_delivery_boundary_result（clean_data/交付边界结果）= PASS; skeleton has no clean_data, delivery, export, or readiness mutation path.
test_only_fake_repository_compatibility_result（test-only fake repository兼容结果）= PASS; production-adjacent skeleton does not import or replace tests/agent fake repository; existing fake repository tests still pass.
boundary_check（边界检查）= PASS; only allowed files created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BU-QA repository interface skeleton disabled-by-default review.
```
