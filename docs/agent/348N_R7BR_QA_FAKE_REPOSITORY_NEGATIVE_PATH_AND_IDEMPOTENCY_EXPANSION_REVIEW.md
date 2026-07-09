# 348N-R7BR-QA fake repository negative-path and idempotency expansion review

## Task ID

```text
348N-R7BR-QA fake repository negative-path and idempotency expansion review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: repository already up to date on pivot/348-agent-foundation.

git status -sb
PASS: clean after pull.

git log --oneline -8
PASS: latest history includes b3e0baf R7BR-QA task doc and ec0dbc8 R7BR implementation.
```

## Files reviewed

Task and required context reviewed:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/348N_R7BR_QA_fake_repository_negative_path_and_idempotency_expansion_review.md`

R7BR reviewed files:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json`
- `docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md`

Related read-only boundary files reviewed:

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

## R7BR recap

R7BR commit `ec0dbc8` modified only four allowed files:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json`
- `docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md`

R7BR expanded the R7BQ fake repository boundary from 31 targeted tests to 63 targeted tests, while preserving the in-memory-only, explicit-token, metadata-first, no-IO/no-DB/no-production-hook boundary.

## 大白话说明审查

PASS. 这一轮没有把“假 repository”悄悄变成真的 persistence。R7BR 只是继续在 `tests/agent/` 里撞墙：伪造 receipt、伪造内部状态、传生产配置、传 DB/路径/网络/存储标记、重复 key、冲突 hash、坏批次、raw payload 和 full source_text 都会 fail closed。它仍然不写数据库、不写文件、不接生产、不改 clean_data、不打开 readiness。

## Negative-path expansion review

PASS. R7BR adds the curated fixture `tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json`, size 5,760 bytes, with 20 negative-path cases and 10 idempotency cases.

The new negative cases cover:

- attempted production mode and production writer config;
- DB connection string, table name, file path, network dependency, and storage dependency markers;
- caller-supplied fake repository receipt and internal repository state;
- direct raw persistence candidate rows;
- missing `review_item_id`, `run_id`, `idempotency_key`, and `record_payload_hash`;
- malformed idempotency key and payload hash;
- nested raw VLM/OCR payloads;
- production timestamp-like fields;
- same record payload hash with different idempotency key.

All expanded negative-path cases are asserted to leave repository state unchanged.

## Idempotency policy review

PASS. The policy remains deterministic and conservative:

- same `idempotency_key` + same `record_payload_hash` retries are deterministic no-ops;
- independent first writes with the same input produce stable receipts;
- retry receipts are stable and preserve state hash;
- same `idempotency_key` + different payload hash fails closed.

No silent duplicate insert behavior was introduced.

## Duplicate conflict policy review

PASS. Duplicate and conflict cases fail closed:

- duplicate `idempotency_key` within the same batch;
- duplicate `review_item_id` within the same batch;
- existing `review_item_id` with a different idempotency key;
- same review item and same key with changed payload;
- same record payload hash with different idempotency key.

The implementation prepares copied next-state dictionaries and replaces repository state only after all rows validate.

## Batch atomicity review

PASS. R7BR proves all-or-nothing in-memory behavior:

- valid first row + invalid second row writes nothing;
- invalid follow-up batch leaves existing state unchanged;
- conflict batches leave existing state unchanged;
- no partial success is returned.

This remains a test-only atomicity simulation, not a real DB transaction.

## Mutation isolation review

PASS. R7BR tests confirm:

- returned receipt mutation does not mutate repository state;
- returned state snapshot mutation does not mutate repository state;
- validated candidate mutation does not mutate repository state;
- separate repository instances do not share mutable state;
- no public `reset`, `clear`, `delete`, `retract`, or `rollback` method exists.

Repository state remains private in-memory dictionaries exposed only through deep-copied snapshots.

## Receipt safety review

PASS. Receipts are metadata-only and deterministic. They include stable counts, ids, payload hashes, repository state hash, closed readiness gates, and zero write counters.

Receipts do not include DB IDs, table names, migration IDs, output paths, production config, raw payloads, full source text, or test-only token values. Caller-supplied receipt fields are rejected recursively as forbidden fields.

## Forbidden field and raw payload leakage review

PASS. Recursive forbidden-field validation rejects:

- full `source_text` / `full_source_text` and raw PDF/Excel/MinerU/parser payloads;
- raw OCR/LLM/VLM payloads;
- schema preview, dry-run output, writer preview, and adapter output shapes;
- fake repository rows, state snapshots, write receipts, and internal state fields;
- clean_data, delivery, export, production hook, readiness, and timestamp-like fields;
- production, DB, storage, network, path, table, migration, and repository-class fields.

`evidence_preview` remains bounded by the persistence contract preview limit.

## Production config rejection review

PASS. `repository_config` is rejected whenever provided. The recursive field scan also rejects production mode/config, writer config, DB DSN/connection/table markers, file/output paths, network/storage clients, API clients, and S3/storage URI fields.

No production configuration can pass into fake repository persistence.

## No-IO / no-DB / no-production-hook review

PASS. The fake repository implementation remains under `tests/agent/` only. It imports stdlib plus the test-only persistence contract helper; it does not import `datefac_agent`, database drivers, storage/network clients, output writers, runner/CLI code, MinerU, OCR, PDF parsers, LLM, or VLM libraries.

The AST boundary test still blocks forbidden IO/DB/export/production-hook imports and calls. R7BR added no database model, migration, repository class, storage implementation, output writer, runner, CLI, production hook, dependency file, output artifact, or readiness-gate change.

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
PASS: 76 passed in 0.42s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.18s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.24s

python -m pytest tests/agent -q
PASS: 543 passed in 2.28s

git status -sb
PASS: clean before QA report creation.

git diff --stat
PASS: no tracked diff before QA report creation.

git diff --name-only
PASS: no tracked diff before QA report creation.

git diff --check
PASS: no whitespace errors.
```

## Limitations

- This is still test-only and in-memory.
- No real review_queue database schema, migration, repository class, storage layer, output writer, runner, CLI, or production hook exists.
- Atomicity, rollback, idempotency, and isolation are simulated in memory only.
- No real DB transaction, locking, isolation level, concurrency, retention, retraction, audit table, or review UI behavior is proven.
- Future real persistence remains blocked until database schema/migration design, disabled implementation slices, local test DB prototypes, rollback tests, and production gate review are completed separately.

## Decision

PASS. R7BR safely expands the fake repository negative-path and idempotency matrix while preserving the R7BQ test-only, in-memory-only, fail-closed, metadata-first boundary. The implementation rejects production config, DB/storage/network/path markers, forged receipts/state, raw payload leakage, malformed identity/hash fields, duplicate conflicts, clean/delivery/readiness promotion, and invalid batches without partial writes.

## Recommended next task review

Recommended next task is appropriate:

```text
348N-R7BS database schema and migration design docs-only
```

R7BS should remain docs-only and should not implement real persistence until schema, migration, rollback, local test database, and production readiness gates are separately designed and reviewed.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BR-QA approved the negative-path and idempotency expansion.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; fake repository 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 543 passed.
files_modified（修改文件数）= 1 allowed QA report file in this QA task; R7BR implementation previously changed 4 allowed files.
error_count（错误数）= 0.
negative_path_expansion_review_result（负路径扩展审查结果）= PASS; production, DB/path/table, network/storage, forged receipt/state, direct row, missing/malformed identity/hash, raw payload, and timestamp misuse cases fail closed.
idempotency_expansion_review_result（幂等扩展审查结果）= PASS; retry/no-op and stable receipt/state behavior are deterministic.
duplicate_conflict_review_result（重复冲突审查结果）= PASS; duplicate key, duplicate review item, same key/different hash, same review item/different key, changed payload, and same hash/different key conflicts fail closed.
batch_atomicity_review_result（批次原子性审查结果）= PASS; invalid or conflicting rows prevent partial writes and preserve existing state.
mutation_isolation_review_result（变更隔离审查结果）= PASS; receipts, snapshots, validated candidates, and repository instances are deep-copy isolated.
receipt_safety_review_result（receipt安全审查结果）= PASS; receipt is deterministic metadata-only and contains no raw payload, production config, DB/path identifiers, full source_text, or token leakage.
forbidden_field_review_result（禁止字段审查结果）= PASS; recursive forbidden-field validation covers raw payloads, clean/delivery/export/readiness, fake repository internals, production config, DB/storage/network/path markers, and non-deterministic timestamps.
raw_payload_leakage_review_result（原始payload泄漏审查结果）= PASS; raw MinerU/Excel/parser/PDF/OCR/LLM/VLM and full source_text leakage remains rejected.
production_config_rejection_review_result（生产配置拒绝审查结果）= PASS; repository_config and production/DB/storage/network/output config markers are rejected.
no_io_no_db_review_result（无IO无DB审查结果）= PASS; no file IO, database, network, storage, migration, output writer, export, runner, CLI, or production hook was added.
test_only_boundary_review_result（test-only边界审查结果）= PASS; fake repository remains under tests/agent and uses only in-memory state.
boundary_check（边界检查）= PASS; this QA task creates only docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BS database schema and migration design docs-only.
```
