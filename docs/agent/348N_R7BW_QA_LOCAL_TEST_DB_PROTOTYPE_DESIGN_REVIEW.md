# 348N-R7BW-QA local test DB prototype design review

## Task ID

```text
348N-R7BW-QA local test DB prototype design review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 93ffd37..e614224; R7BW-QA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -90
PASS: latest history includes e614224 R7BW-QA task doc, 93ffd37 R7BW design, c9a9f10 R7BW task doc, 65e4843 R7BV-QA, and a7c73b7 R7BV QA hardening.
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
- `docs/codex_tasks/348N_R7BW_QA_local_test_DB_prototype_design_review.md`
- `docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md`
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

## R7BW recap

R7BW created exactly one docs-only design report:

```text
docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md
```

It did not modify production code, tests, fixtures, dependencies, outputs, database files, schemas, migrations, repository implementations, or readiness gates. It did not connect to SQLite, PostgreSQL, Docker, or any other database.

## 大白话说明审查

PASS. R7BW 说得清楚：这一轮只是设计未来“本地测试 DB 原型”的安全边界，不是现在实现数据库。它没有偷偷写 adapter、没有建表、没有 migration、没有 SQL、没有 SQLite/PostgreSQL/Docker 连接，也没有把 disabled repository skeleton 变成可写 repository。它是在画测试场围栏，不是在打开生产闸门。

## Allowed file boundary review

PASS. R7BW changed only the allowed design report. No production code, existing tests, fixtures, outputs, dependencies, schema files, migrations, repository implementation, local DB adapter, handoff docs, planning docs, or readiness gates were modified.

## Docs-only scope review

PASS. The report explicitly states R7BW is docs-only and that the design must be reviewed before any code can add DB imports, local DB adapter, schema creation, migration, connection handling, transaction behavior, repository factory activation, runner integration, or CLI integration.

The report does not claim a local test DB prototype exists.

## Current baseline review

PASS. The baseline is accurate and includes:

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

The report states the current repository skeleton is disabled by default, has no DB/IO/network behavior, no local DB prototype exists, no real schema exists, no migration exists, no production repository exists, R7BV-QA approved targeted repository skeleton QA at `32 passed`, full `tests/agent` is `592 passed`, and readiness gates remain CLOSED.

## Local test DB prototype scope review

PASS. The future prototype scope is limited to controlled local-test proof of repository persistence behavior: local schema rehearsal, transaction/rollback, idempotency, uniqueness/conflict behavior, metadata-only storage, teardown, and failure-mode coverage.

It remains a prototype and is not allowed to be called by the disabled skeleton factory, review_queue_builder, clean_data, delivery/export, production adapter, runner, or CLI.

## Candidate local DB choice review

PASS. The report discusses candidate choices without requiring implementation now:

- SQLite in-memory or isolated temporary-file DB as the likely first future option;
- PostgreSQL test container only if a later task explicitly allows Docker/container/runtime audit;
- pure fake repository remains valid for unit-level boundary tests.

The tradeoffs are stated safely, including SQLite/PostgreSQL behavioral differences and the extra risk of temp-file filesystem side effects.

## Activation and environment gate review

PASS. The activation model requires all of:

- explicit test-only flag;
- explicit local-test environment value;
- explicit test DSN or in-memory DB selection;
- hard rejection of production-looking DSNs;
- hard rejection of non-local hosts;
- no environment-variable-only activation;
- no default DB connection;
- no production writer config;
- no automatic activation from repository skeleton factory;
- no automatic activation from validated schema alignment preview.

Invalid activation examples include missing token, environment-only token, production environment, opened readiness flags, production-looking DSNs, non-allowlisted hosts, production writer config, and readiness override.

## Repository adapter boundary review

PASS. The design keeps a future adapter separate from `DisabledReviewQueueRepository`, unavailable by default, and constructed only in tests or explicit local-test prototype paths.

It explicitly forbids future adapter calls from `review_queue_builder`, clean_data, delivery/export, production adapter, runner, or CLI without later reviewed gates. It also forbids importing `tests/agent` fake repository code into production code.

## Schema/migration rehearsal review

PASS. Schema/migration rehearsal is constrained to local test context only:

- schema creation only in test context;
- migration rehearsal only against local test DB;
- clean setup and teardown;
- forward migration preference;
- non-destructive rollback policy by default;
- manual recovery strategy for bad rows;
- no migration file in R7BW;
- no production migration without separate gate review.

No migration, schema, or SQL file was created in R7BW.

## Transaction and rollback review

PASS. The design requires future tests to prove:

- single-row insert atomicity;
- batch insert atomicity;
- no partial success by default;
- invalid row rolls back entire batch;
- transaction failure rolls back all writes;
- read after failed write returns no residual rows;
- idempotent retry after rollback is deterministic;
- rollback does not mutate clean_data, delivery/export, or readiness metadata.

The batch policy is conservative: validate entire batch, begin transaction, commit all rows, or rollback all rows on any failure.

## Idempotency and uniqueness review

PASS. The design covers deterministic retry and conflict rules:

- same `idempotency_key` + same `record_payload_hash` = deterministic no-op or same receipt;
- same `idempotency_key` + different payload = conflict/fail closed;
- same `review_item_id` + different identity = conflict/fail closed;
- `record_payload_hash` consistency enforced;
- no silent duplicate insert;
- batch duplicate keys fail before insert.

Recommended uniqueness constraints are documented for `idempotency_key`, `review_item_id`, and an optional run/source/metric/period/schema/contract composite.

## Raw-payload exclusion review

PASS. The report explicitly forbids storing:

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

Only bounded `evidence_preview`, `evidence_preview_sha256`, constrained `source_trace`, identity fields, status/action fields, run/input/version metadata, and audit/hash fields may be stored.

## Audit and record hash review

PASS. The design requires future repository validation to recompute and enforce deterministic SHA-256 metadata:

- `audit_hash`;
- `record_payload_hash`;
- `idempotency_key`;
- `evidence_preview_sha256`;
- `matched_text_sha256` where present.

Caller-supplied hashes cannot override repository-computed hash validation, and payload changes require reviewed version/retraction design rather than silent overwrite.

## Failure-mode test plan review

PASS. The future failure-mode plan is complete enough for an implementation slice. It includes missing identity fields, malformed hashes, duplicate idempotency/review IDs, later invalid batch row, transaction failure rollback, bad enum/status, raw payload leakage, production DSN/config, environment activation attempt, read-after-failed-write, and cleanup/teardown residual-state checks.

Additional negative cases cover non-local hosts, missing explicit token, environment-only activation, nested clean/delivery/readiness intent, output/file path config, user-supplied receipt/internal state, and concurrency-ish duplicate retry if supported.

## Cleanup and teardown strategy review

PASS. Cleanup/teardown is explicit:

- close in-memory DB connections;
- use test temp directories only for temp-file DB;
- remove temp files;
- failed setup leaves no partial schema/files;
- failed write leaves no rows;
- repeated runs are deterministic;
- cleanup failure reports loudly.

The design forbids writing DB files into `output/`, `input/`, `temp/`, `data/`, legacy folders, or repository root DB files.

## No-production-connection guarantee review

PASS. The no-production-connection guarantee is explicit and conservative. Future code must reject production-looking DSNs, non-local hosts, default DB URLs, cloud/storage endpoints, environment-variable-only activation, production writer config, production readiness flags, and formal export flags.

The recommended allowlist starts with `sqlite_memory` and `:memory:` only; `sqlite_temp_file` and PostgreSQL containers require later explicit authorization and QA.

## clean_data/delivery/export separation review

PASS. R7BW preserves safety rules:

- `VERIFIED` does not imply `STRONG_EVIDENCE`;
- `VERIFIED` does not auto-write clean_data;
- non-VERIFIED rows remain review-bound;
- unresolved rows keep `blocked_delivery_reason`;
- corrected rows remain `re_audit_required`;
- persistence candidate does not trigger delivery;
- persistence candidate does not mutate clean_data;
- persistence candidate does not open readiness gates;
- bounded `evidence_preview` is allowed;
- full `source_text` and raw payloads remain forbidden.

The future local DB prototype may persist only review_queue-like metadata rows for tests, not clean_data, delivery rows, export manifests, client-ready artifacts, or formal delivery output.

## Future validation plan review

PASS. The future validation plan is conservative. It includes py_compile of repository skeleton and future adapter/test files, targeted local DB tests, existing repository QA/skeleton/fake repository/persistence/schema/dry-run/writer/adapter skeleton tests, full `tests/agent`, and git status/diff checks.

It also requires future tests for production DSN rejection, environment-only activation rejection, transaction rollback on invalid batch, cleanup/teardown residual state, metadata-only receipts, and closed readiness gates.

## Open questions review

PASS. Open questions are explicit and appropriately defer unresolved design choices: SQLite memory versus temp file, test-only versus production-adjacent disabled module placement, raw SQL versus abstraction, audit events timing, concurrency threshold, first indexes, soft retraction/versioning timing, and PostgreSQL container operational review.

## Non-goals review

PASS. The non-goals are explicit. R7BW does not modify code/tests/fixtures, add database adapter, repository implementation, model, schema, migration, DB connection, SQL execution, storage implementation, output writer, extraction, MinerU/OCR/LLM/VLM, Docker/PostgreSQL/SQLite connection, readiness gates, production persistence, production readiness, client readiness, or formal export readiness.

## Remaining risks review

PASS. Remaining risks are accurate and conservative: local test DB prototype is only designed, real DB transaction behavior is not proven, migration behavior is not proven, concurrency/performance/cleanup/production controls are not proven, and client/export readiness is not implied.

## Recommended next task review

PASS. Recommended next task is safe:

```text
348N-R7BX local test DB adapter boundary skeleton test-only
```

R7BX should remain test-only and boundary-skeleton oriented. It must not jump directly to production persistence, production repository activation, production DSN, migration, clean_data mutation, delivery/export, or readiness gates.

## Boundary review

PASS. R7BW-QA creates only this QA report. No production code, tests, fixtures, outputs, dependencies, integrations, DB models, repository implementations, migrations, schema files, R7BW design report, handoff docs, planning docs, or readiness gates were modified.

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
PASS: 63 passed in 0.53s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.41s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.18s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.24s

python -m pytest tests/agent -q
PASS: 592 passed in 2.25s
```

Final git status/diff checks are recorded after report creation and before commit.

## Limitations

- R7BW-QA is a docs-only review and does not implement a local test DB prototype.
- No DB transaction, migration, schema, adapter, repository implementation, cleanup, concurrency, or performance behavior is proven by this QA review.
- Future R7BX work must still be test-only and explicitly gated.
- Production persistence remains blocked pending separate design, implementation, negative-path tests, and QA gates.

## Decision

PASS. R7BW is conservative, complete for a docs-only local test DB prototype design, and does not cross implementation boundaries. It clearly states no prototype exists yet, no DB behavior is proven, no schema/migration/adapter/SQL/connection exists, no production activation is allowed, raw payloads remain forbidden, clean_data/delivery/export remain separated, and readiness gates remain CLOSED.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BW-QA approves the docs-only local test DB prototype design.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; repository QA 32 passed, skeleton 17 passed, fake repository 63 passed, persistence contract 76 passed, schema alignment 29 passed, dry-run integration 36 passed, writer contract 24 passed, adapter skeleton 75 passed, full tests/agent 592 passed.
files_modified（修改文件数）= 1; QA report only.
error_count（错误数）= 0.
local_test_db_design_review_result（本地测试DB设计审查结果）= PASS; design is docs-only, conservative, and does not claim a prototype exists.
activation_gate_design_review_result（激活门设计审查结果）= PASS; explicit test-only flag, token, local-test mode, explicit DB selection, and no automatic activation are required.
environment_allowlist_design_review_result（环境白名单设计审查结果）= PASS; local-only allowlist is planned and production/non-local/env-only activation must fail closed.
repository_adapter_boundary_design_review_result（repository adapter边界设计审查结果）= PASS; future adapter remains separate, default-unavailable, test/local-prototype-only, and not called by production paths.
schema_migration_rehearsal_design_review_result（schema/migration rehearsal设计审查结果）= PASS; schema/migration rehearsal is test-context-only with no R7BW migration file or production migration.
transaction_rollback_design_review_result（事务回滚设计审查结果）= PASS; single/batch atomicity, rollback, no partial success, and read-after-failed-write checks are required.
idempotency_uniqueness_design_review_result（幂等唯一性设计审查结果）= PASS; deterministic retry, uniqueness, conflict fail-closed behavior, and no silent duplicate insert are specified.
raw_payload_exclusion_design_review_result（原始payload排除设计审查结果）= PASS; full source_text, raw artifacts, secrets, DSNs, paths, readiness, clean_data, and delivery/export intents remain forbidden.
audit_record_hash_design_review_result（审计record hash设计审查结果）= PASS; deterministic audit/record/evidence hash recomputation and immutability are specified.
failure_mode_test_plan_review_result（失败模式测试计划审查结果）= PASS; future negative-path coverage is broad enough for implementation planning.
cleanup_teardown_design_review_result（清理teardown设计审查结果）= PASS; cleanup, temp-path-only behavior, no residual state, and loud cleanup failure are required.
no_production_connection_design_review_result（无生产连接设计审查结果）= PASS; production DSNs, non-local hosts, cloud endpoints, env-only activation, writer config, and readiness flags are rejected.
clean_data_delivery_boundary_review_result（clean_data/交付边界审查结果）= PASS; future prototype must not mutate clean_data, trigger delivery/export, promote evidence, or open readiness gates.
boundary_check（边界检查）= PASS; only docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md is created.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7BX local test DB adapter boundary skeleton test-only.
```
