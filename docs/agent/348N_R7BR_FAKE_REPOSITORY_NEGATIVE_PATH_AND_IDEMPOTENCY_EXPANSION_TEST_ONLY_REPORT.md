# 348N-R7BR fake repository negative-path and idempotency expansion test-only

## Task ID

```text
348N-R7BR fake repository negative-path and idempotency expansion test-only
```

Task type: test-only-negative-path-idempotency-expansion.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 647e1db..58b4981; R7BR task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -65
PASS: latest history includes 58b4981 R7BR task doc, 647e1db R7BQ-QA, e1eccb2 R7BQ-QA task doc, c96395b R7BQ implementation, a568487 R7BP-QA, e08f6c6 R7BP, d027e85 R7BO-QA, b223c05 R7BN-QA, ce10b99 R7BM-QA, and 7713db4 R7BL-QA.
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
- `docs/codex_tasks/348N_R7BR_fake_repository_negative_path_and_idempotency_expansion_test_only.md`
- `docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md`
- `docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md`
- `docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`

R7BQ files reviewed and extended:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json`

Related test-only files reviewed read-only:

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

## R7BQ-QA recap

R7BQ-QA approved the fake repository boundary as safe, deterministic, test-only, in-memory-only, explicit-token gated, metadata-first, and no-IO/no-DB/no-production-hook.

R7BQ-QA also identified the intended next slice:

```text
348N-R7BR fake repository negative-path and idempotency expansion test-only
```

## 大白话说明

这一轮继续“撞墙测试”。R7BQ 已经有一个假的内存 repository 边界；R7BR 专门拿重复写、冲突写、坏批次、伪造 receipt、伪造 internal state、绕路输入、隐藏生产配置、状态污染和对象引用污染去撞它。

结果仍然只在 `tests/agent/` 内验证，不接真实数据库、不写文件、不建表、不加 migration、不接生产。

## Negative-path expansion scope

R7BR adds a new curated fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json
```

The fixture covers:

- attempted production mode;
- attempted production writer config;
- connection string / table name / file path misuse;
- network/storage dependency markers;
- caller-supplied fake repository receipt;
- caller-supplied internal repository state;
- raw direct persistence candidate rows;
- single-row missing identity/hash fields;
- malformed idempotency and record payload hashes;
- nested raw VLM/OCR payloads;
- production timestamp policy;
- same record payload hash with different idempotency key.

R7BR also expands targeted tests from 31 to 63 cases.

## Idempotency policy summary

The R7BQ idempotency policy is preserved:

```text
same idempotency_key + same record_payload_hash = deterministic no-op on retry
same idempotency_key + different record_payload_hash = fail closed
same batch retry = no duplicate rows
```

R7BR adds tests proving retry receipt behavior is deterministic:

- first independent writes produce identical first-write receipts;
- repeated retry against the same repository produces stable no-op receipt;
- state hash remains stable after retry.

## Duplicate conflict policy summary

R7BR preserves conservative duplicate handling:

- duplicate idempotency key within the same batch fails closed;
- duplicate review item within the same batch fails closed;
- existing idempotency key with changed payload hash fails closed;
- existing review item with a different idempotency key fails closed;
- same review item and same idempotency key with changed payload fails closed via idempotency conflict;
- same record payload hash with a different idempotency key fails closed via record hash mismatch.

Silent duplicate insert remains forbidden.

## Batch atomicity summary

R7BR proves:

- invalid second row prevents writing the first row in an otherwise new batch;
- invalid follow-up batch leaves existing repository state unchanged;
- conflict batches leave repository state unchanged;
- no partial success is returned.

The behavior remains a pure in-memory all-or-nothing simulation, not a real DB transaction.

## Mutation isolation summary

R7BR expands copy-isolation coverage:

- returned receipt mutation cannot mutate repository state;
- returned state snapshot mutation cannot mutate repository state;
- validated candidate list mutation cannot mutate repository state;
- `state_snapshot()` behaves as read-only copy;
- separate repository instances do not share mutable state.

R7BR also confirms no reset/clear/retract/destructive-delete public API exists.

## Receipt safety summary

Write receipts remain deterministic and metadata-only. Tests confirm receipts exclude forbidden/raw fields and keep:

- `writes_database = false`;
- `writes_export = false`;
- closed readiness gates;
- zero clean_data/delivery/filesystem/database/export write counters.

Caller-supplied or forged receipt fields are now explicitly forbidden as input.

## Forbidden field and raw payload leakage summary

The fake repository boundary now also rejects these additional markers:

- `fake_repository_write_receipt`;
- `fake_repository_state_snapshot`;
- `caller_supplied_receipt`;
- `internal_state`;
- `repository_internal_state`;
- `repository_state`;
- `write_receipt`;
- `receipt`;
- `production_mode`;
- `db_connection`;
- `database_connection`;
- `storage_client`;
- `storage_dependency`;
- `network_dependency`;
- `http_client`;
- `api_client`;
- `s3_uri`;
- `persistence_candidate_rows`.

Existing recursive rejection still covers full source text, raw MinerU/Excel/parser/OCR/LLM/VLM payloads, clean_data intent, delivery/export intent, production config, DB/DSN/path/table/migration hints, timestamp-like fields, and readiness overrides.

## No-IO / no-DB / no-production-hook summary

The helper remains under `tests/agent/` only and still:

- imports no `datefac_agent`;
- opens no DB connection;
- writes no files or outputs;
- creates no model/schema/migration;
- imports no storage, network, MinerU, OCR, PDF parser, LLM, or VLM libraries;
- adds no runner, CLI, writer, or production hook.

Static AST tests still enforce no forbidden IO/DB/export/production-hook imports or calls.

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
PASS: 63 passed in 0.50s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.43s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.14s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.23s

python -m pytest tests/agent -q
PASS: 543 passed in 2.34s

git status -sb
PASS before report creation: only allowed R7BR helper/test modifications and new R7BR fixture were present.

git diff --stat
PASS before report creation: tracked diff limited to R7BR helper/test modifications.

git diff --name-only
PASS before report creation: tracked diff limited to tests/agent/review_queue_fake_repository_boundary_348n.py and tests/agent/test_review_queue_fake_repository_boundary_348n.py.

git diff --check
PASS: no whitespace errors.
```

## Limitations

- This remains test-only and in-memory.
- No real review_queue persistence exists.
- No production repository/model/service code exists.
- No DB schema, migration, database connection, storage implementation, output writer, export path, runner, CLI, or production hook exists.
- Atomicity, rollback, and idempotency behavior are simulated only in memory.
- No real DB transaction, lock, isolation-level, concurrency, performance, retention, retraction, or review UI behavior is proven.
- Production persistence remains blocked pending future QA, schema/migration design, disabled skeleton, local test DB prototype, rollback tests, and production gate review.

## Decision

PASS. R7BR expands fake repository negative-path and idempotency coverage while preserving the R7BQ test-only, in-memory-only, fail-closed, metadata-first, no-IO/no-DB/no-production-hook boundary. The boundary now has stronger tests for bypass inputs, forged receipts/state, production/storage/network markers, raw payload leakage, malformed identity/hash fields, duplicate conflicts, atomic batch rollback simulation, deterministic retry behavior, and copy isolation.

## Recommended next task

```text
348N-R7BR-QA fake repository negative-path and idempotency expansion review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BR negative-path and idempotency expansion implemented.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; fake repository targeted tests 63 passed; related suites 76/29/36/24/75 passed; full tests/agent 543 passed.
files_modified（修改文件数）= 4 allowed files.
error_count（错误数）= 0.
negative_path_expansion_result（负路径扩展结果）= PASS; new R7BR fixture and tests cover production, DB/path/table, network/storage markers, forged receipt/state, direct rows, missing/malformed identity/hash, raw payload, timestamp, and forbidden nested fields.
idempotency_expansion_result（幂等扩展结果）= PASS; retry behavior is deterministic no-op with stable state and receipt semantics.
duplicate_conflict_result（重复冲突结果）= PASS; duplicate key, duplicate review item, same key/different payload, same review item/different key, and same hash/different key fail closed.
batch_atomicity_result（批次原子性结果）= PASS; invalid rows prevent partial writes and invalid follow-up batches leave existing state unchanged.
mutation_isolation_result（变更隔离结果）= PASS; receipt, snapshot, validated candidates, and separate repository instances are copy-isolated.
receipt_safety_result（receipt安全结果）= PASS; receipts remain deterministic metadata-only and forged caller receipt fields are rejected.
forbidden_field_result（禁止字段结果）= PASS; recursive forbidden-field list expanded for fake repository state/receipt, production mode, network/storage, and direct candidate-row markers.
raw_payload_leakage_result（原始payload泄漏结果）= PASS; raw MinerU/Excel/parser/OCR/LLM/VLM and full source_text remain rejected.
production_config_rejection_result（生产配置拒绝结果）= PASS; production writer/repository/mode, DB connection, table, file/output path, network/storage dependency markers rejected.
no_io_no_db_result（无IO无DB结果）= PASS; no IO, DB, network, export, migration, storage, or production hook added.
test_only_boundary_result（test-only边界结果）= PASS; changes remain under tests/agent plus docs report only.
boundary_check（边界检查）= PASS; only allowed R7BR files changed.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BR-QA fake repository negative-path and idempotency expansion review.
```
