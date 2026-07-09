# 348N-R7BY local test DB boundary negative-path expansion test-only report

## Task ID

```text
348N-R7BY local test DB boundary negative-path expansion test-only
```

Task type: test-only-negative-path-expansion.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward bd3fe1e..727cec0; R7BY task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -100
PASS: latest history includes 727cec0 R7BY task doc, bd3fe1e R7BX-QA, b6bf4b7 R7BX skeleton, d4858fa R7BW-QA, and 93ffd37 R7BW design.
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
- `docs/codex_tasks/348N_R7BY_local_test_DB_boundary_negative_path_expansion_test_only.md`
- `docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md`
- `docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md`
- `docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md`
- `docs/agent/348N_R7BV_QA_REPOSITORY_SKELETON_QA_REVIEW.md`
- `docs/agent/348N_R7BV_REPOSITORY_SKELETON_QA_REPORT.md`
- `docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md`

Current local test DB boundary files reviewed:

- `tests/agent/review_queue_local_test_db_adapter_boundary_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py`

Related repository/fake repository chain reviewed read-only:

- `datefac_agent/review/review_queue_repository.py`
- `tests/agent/test_review_queue_repository_skeleton_348n.py`
- `tests/agent/test_review_queue_repository_skeleton_qa_348n.py`
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

## R7BX-QA recap

R7BX-QA approved the local test DB adapter boundary skeleton as safe test-only work. It confirmed the boundary remained planned-disabled, no-DB/no-IO/no-network, metadata-first, fail-closed, compatible with existing repository skeleton and fake repository chains, and did not modify production code, implement persistence, leak raw payloads/secrets, mutate clean_data/delivery/export, or open readiness gates.

R7BX-QA recommended this task:

```text
348N-R7BY local test DB boundary negative-path expansion test-only
```

## 大白话说明

R7BY 继续只在测试区加“坏路”防线：它拿生产 DSN、远程 host、环境变量偷激活、schema preview 自动激活、raw payload、clean_data/delivery/export 意图、伪造 DB row、伪造 committed receipt、重复/冲突幂等键等输入去撞边界。结果是边界仍然 fail closed，不连库、不建表、不写 SQL、不写 migration、不写文件、不接生产、不打开 readiness。

## Negative-path expansion scope

R7BY added a focused negative-path test suite for the local test DB boundary. It also made a minimal test-only hardening update to the existing boundary module because the new tests exposed missing explicit rejection for a few future-dangerous keys and malformed `idempotency_key`.

No production code was changed.

## Files changed

Changed exactly the allowed files:

- `tests/agent/review_queue_local_test_db_adapter_boundary_348n.py`
- `tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py`
- `docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`

No `datefac_agent/` production code, existing fixtures, output files, dependency files, schema/migration files, runner/CLI paths, or readiness gates were modified.

## Activation gate negative paths

New tests verify activation fails closed when any required future condition is missing or invalid:

- missing `test_only`;
- false `test_only`;
- missing environment;
- empty environment;
- production environment;
- staging environment;
- mixed local/prod environment;
- missing DB selection;
- unsupported DB selection;
- schema preview auto-activation;
- repository skeleton factory auto-activation.

The valid explicit local-test shape still returns planned-disabled metadata only:

- `database_connection_opened = false`
- `schema_created = false`
- `migration_created = false`
- `table_created = false`
- `database_write_count = 0`
- `filesystem_write_count = 0`
- `network_call_count = 0`
- `persists_records = false`

## Production-looking config negative paths

New tests verify rejection without sensitive echo for:

- `postgres://` DSN;
- `postgresql://` DSN;
- `mysql://` DSN;
- `sqlite:///` absolute path;
- file path DB URL;
- remote host;
- non-local host;
- cloud host;
- port endpoint;
- HTTP endpoint;
- HTTPS endpoint;
- connection string;
- DB password;
- DB secret;
- API key;
- token;
- schema name;
- table name;
- migration name;
- output path;
- file path config;
- production writer config;
- readiness override.

The boundary was minimally hardened to reject additional config keys explicitly: API keys/tokens, schema/migration names, and port-style config.

## Environment activation negative paths

New tests set local-test-looking environment variables and production-looking DSN environment variables. The boundary still rejects empty config and rejects `activation_source = environment` / `activation_source = env`.

Environment variables cannot activate the boundary.

## Candidate raw payload negative paths

New tests verify candidate validation rejects:

- `source_text`;
- `full_source_text`;
- `raw_mineru_payload`;
- `raw_excel_payload`;
- `raw_parser_payload`;
- `raw_ocr_payload`;
- `raw_llm_payload`;
- `raw_vlm_payload`;
- unbounded evidence text;
- oversized `evidence_preview`.

Only bounded preview/trace-style metadata remains acceptable, and accepted metadata is still not persisted.

## clean_data/delivery/export/readiness negative paths

New tests verify fail-closed rejection of:

- `clean_data_payload`;
- `normalized_clean_data`;
- `approved_export_payload`;
- `delivery_payload`;
- `export_payload`;
- `delivery_export_intent`;
- `readiness_override`;
- `readiness_gates`;
- `production_timestamp_override`.

The boundary was minimally hardened to reject `normalized_clean_data` and `approved_export_payload` explicitly.

## Caller-supplied DB row / receipt / internal state negative paths

New tests verify fail-closed rejection of:

- caller-supplied DB primary key;
- caller-supplied DB row;
- database row;
- DB row;
- committed DB receipt;
- committed receipt;
- DB receipt;
- adapter internal state;
- internal adapter state;
- local test DB adapter state;
- generic adapter state.

The boundary was minimally hardened to reject DB primary-key aliases, committed receipt aliases, and generic adapter-state aliases explicitly.

## Transaction/idempotency negative paths

New tests verify:

- missing `review_item_id` fails closed;
- missing `idempotency_key` fails closed;
- malformed `idempotency_key` fails closed;
- missing `record_payload_hash` fails closed;
- malformed `record_payload_hash` fails closed;
- same `idempotency_key` with different `record_payload_hash` fails closed;
- same `review_item_id` with conflicting identity fails closed;
- invalid first row fails whole batch;
- invalid later row fails whole batch;
- duplicate conflicting batch fails whole batch;
- no partial success result is returned by default;
- no silent duplicate insert is allowed by contract.

The boundary was minimally hardened to validate `idempotency_key` as the same 64-character lowercase hex shape required for record hashes.

## Input mutation safety

New tests deep-copy activation payloads and candidate batches before fail-closed validation and assert inputs remain unchanged. Nested forbidden config/candidate fields also fail closed without mutation.

## Error leakage safety

New tests verify activation and candidate errors stay generic and do not echo:

- raw payload values;
- source text values;
- DSNs;
- passwords;
- secrets;
- endpoints;
- table names;
- output paths;
- readiness override values;
- DB receipt/internal-state values.

## Source inspection

New source-inspection tests parse the boundary module with AST and assert no forbidden DB/storage/network/Docker imports or side-effect calls exist. The checks cover:

- `sqlite3`
- `sqlalchemy`
- `psycopg`
- `psycopg2`
- `pymysql`
- `mysql`
- `asyncpg`
- `redis`
- `boto`
- Docker/docker
- `requests`
- `urllib`
- `socket`
- `subprocess`
- `connect`
- `execute`
- `open`
- `write`
- SQL statement markers such as `CREATE TABLE`, `ALTER TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`, and `DROP TABLE`

The test checks import/call behavior rather than forbidding safe string markers used to reject production-looking DSNs.

## Compatibility with R7BX boundary tests

Existing R7BX tests still pass:

```text
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
PASS: 55 passed in 0.14s
```

The new R7BY negative-path suite also passes:

```text
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
PASS: 88 passed in 0.16s
```

## No-DB / no-IO / no-network guarantee

R7BY does not add a DB adapter, database model, migration, schema, database connection, SQL execution, file write, storage implementation, output writer, export path, production hook, MinerU/OCR/LLM/VLM/extraction path, clean_data mutation, delivery unblock, or readiness-gate change.

The boundary still reports:

- `database_connection_opened = false`
- `schema_created = false`
- `migration_created = false`
- `table_created = false`
- `database_write_count = 0`
- `filesystem_write_count = 0`
- `network_call_count = 0`
- `writes_clean_data = false`
- `writes_delivery = false`
- `writes_export = false`
- readiness gates closed.

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

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
PASS: 88 passed in 0.16s

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
PASS: 55 passed in 0.14s

python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
PASS: 32 passed in 0.10s

python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
PASS: 17 passed in 0.08s

python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
PASS: 63 passed in 0.47s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.41s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.18s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.13s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.23s

python -m pytest tests/agent -q
PASS: 735 passed in 2.23s

git status -sb
PASS before report creation: only allowed R7BY boundary/test changes present.

git diff --stat
PASS before report creation: only the allowed boundary module tracked diff was shown; new test/report files were untracked.

git diff --name-only
PASS before report creation: only tests/agent/review_queue_local_test_db_adapter_boundary_348n.py tracked diff was shown.

git diff --check
PASS: no whitespace errors.
```

## Limitations

- R7BY is still test-only.
- No real local test DB adapter exists.
- No SQLite/PostgreSQL connection behavior is implemented.
- No schema/model/migration/table/SQL/transaction/rollback/cleanup/concurrency behavior is implemented.
- No production persistence, production hook, client readiness, production readiness, or formal export readiness is implied.

## Decision

PASS. R7BY expands local test DB boundary negative-path coverage and applies minimal test-only fail-closed hardening for explicit config/candidate key rejection and malformed idempotency keys. The boundary remains test-only, planned-disabled, no-DB/no-IO/no-network, metadata-first, raw-payload-safe, clean_data/delivery/export-safe, compatibility-safe, and readiness-closed.

## Recommended next task

```text
348N-R7BY-QA local test DB boundary negative-path expansion review
```

The next task should remain QA-review-only and confirm this negative-path expansion did not add a real DB adapter, DB model, migration, schema, SQL execution, production hook, output writer, clean_data mutation, delivery/export path, dependency, or readiness-gate change.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BY negative-path expansion completed safely.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; new negative-path tests 88 passed; existing R7BX tests 55 passed; repository QA 32 passed; repository skeleton 17 passed; fake repository 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; production boundary adapter skeleton 75 passed; full tests/agent 735 passed.
files_modified（修改文件数）= 3; allowed negative-path test, allowed report, and necessary test-only boundary hardening file.
error_count（错误数）= 0.
negative_path_expansion_result（负路径扩展结果）= PASS; malicious, production-looking, malformed, conflicting, and leakage-prone paths now have focused tests.
activation_gate_negative_path_result（激活门负路径结果）= PASS; missing/false flags, invalid environments, missing/unsupported DB selection, and auto-activation attempts fail closed.
production_config_negative_path_result（生产配置负路径结果）= PASS; production DSNs, remote/cloud hosts, endpoints, connection strings, secrets, schema/table/migration names, paths, writer config, and readiness overrides are rejected without echo.
environment_activation_negative_path_result（环境激活负路径结果）= PASS; environment variables and env activation sources cannot activate the boundary.
candidate_payload_negative_path_result（候选payload负路径结果）= PASS; source_text, full_source_text, raw MinerU/Excel/parser/OCR/LLM/VLM payloads, and unbounded evidence text fail closed.
clean_data_delivery_negative_path_result（clean_data/交付负路径结果）= PASS; clean_data, normalized clean data, approved export, delivery/export, readiness, and production timestamp intents fail closed.
caller_supplied_db_state_negative_path_result（调用方伪造DB状态负路径结果）= PASS; caller-supplied DB primary keys/rows/receipts/internal states fail closed.
transaction_idempotency_negative_path_result（事务/幂等负路径结果）= PASS; missing/malformed identity/hash fields, conflicting idempotency, conflicting review IDs, invalid batches, and duplicates fail closed with no partial success.
input_mutation_safety_result（输入变更安全结果）= PASS; activation payloads and candidate batches remain unchanged after fail-closed validation.
error_leakage_safety_result（错误泄漏安全结果）= PASS; errors do not echo raw payloads, source text, secrets, DSNs, endpoints, paths, table names, or internal state.
source_inspection_result（源码检查结果）= PASS; AST/source checks find no DB/storage/network/Docker imports, SQL execution calls, file-write calls, or SQL statement markers.
no_db_no_io_no_network_result（无DB/IO/网络结果）= PASS; no DB adapter/model/migration/schema/connection/SQL/file/network/output/export/production hook was added.
compatibility_with_r7bx_result（与R7BX兼容结果）= PASS; existing R7BX target tests still pass at 55 passed.
boundary_check（边界检查）= PASS; only allowed R7BY files changed; no production code, output, dependency, fixture, schema, migration, or readiness change.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7BY-QA local test DB boundary negative-path expansion review.
```
