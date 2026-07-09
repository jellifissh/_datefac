# 348N-R7CB local test DB prototype minimum implementation test-only report

## Task ID

```text
348N-R7CB local test DB prototype minimum implementation test-only
```

Task type: test-only-minimum-local-db-prototype.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward fed1d03..3c5cb89; R7CB task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -125
PASS: latest history includes 3c5cb89 R7CB task doc, fed1d03 R7CA-QA, 0769f8d R7CA planning, e9a3099 R7BZ-QA, c1b05dc R7BY-QA, and b6bf4b7 R7BX boundary skeleton.
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
- `docs/codex_tasks/348N_R7CB_local_test_DB_prototype_minimum_implementation_test_only.md`
- `docs/agent/348N_R7CA_QA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_REVIEW.md`
- `docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md`
- `docs/agent/348N_R7BZ_QA_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BZ_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT.md`
- `docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md`
- `docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md`

Read-only compatibility files reviewed:

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

## R7CA-QA recap

R7CA-QA approved the docs-only implementation plan for a future local test DB prototype. It confirmed the safe next slice should be explicit-gated, test-only, in-memory SQLite under `tests/agent` only, with no production repository integration, no schema/migration files, no output writes, no clean_data/delivery/export mutation, and readiness gates still CLOSED.

## 大白话说明

R7CB 第一次真的连了一个“数据库”，但这个数据库只是测试文件里的 `sqlite3.connect(":memory:")`。它像一张临时便签纸：测试跑完或连接关闭，状态就消失。它证明最小写入、读回、事务回滚和幂等冲突规则，但不代表已经有生产落库，也不代表 `datefac_agent/`、runner、CLI、clean_data 或交付链路能调用它。

## Implementation scope

R7CB implements only a test-owned in-memory SQLite prototype under `tests/agent`. It does not modify production code, existing tests, fixtures, dependencies, schema files, migration files, output files, handoff docs, or readiness gates.

## Files changed

Exactly the allowed files were created:

- `tests/agent/review_queue_local_test_db_prototype_348n.py`
- `tests/agent/test_review_queue_local_test_db_prototype_348n.py`
- `docs/agent/348N_R7CB_LOCAL_TEST_DB_PROTOTYPE_MINIMUM_IMPLEMENTATION_TEST_ONLY_REPORT.md`

## Activation gate implementation

The prototype is constructible only through `make_local_test_db_prototype(config)` with explicit local-test gates:

- `test_only = True`
- `environment = local_test`
- `storage = sqlite_memory` or `in_memory_sqlite`
- `explicit_prototype_enabled = True`
- `activation_source = explicit`
- exact R7CB test-only enable token

It rejects missing/false gates, production/staging/dev-like environments, DSNs, hosts, endpoints, file path DB config, production writer config, readiness override, clean_data intent, delivery/export intent, and environment-variable-only activation.

## In-memory local DB implementation

The prototype uses Python stdlib `sqlite3` only inside:

- `tests/agent/review_queue_local_test_db_prototype_348n.py`

It opens only:

```text
sqlite3.connect(":memory:")
```

No PostgreSQL/MySQL/remote DB/Docker/file-backed SQLite/dependency addition is used.

## Schema setup behavior

Schema setup is inline inside the test-only prototype constructor. It creates one test-owned table in the in-memory connection:

```text
review_queue_items
```

No schema file, migration file, caller-supplied table name, clean_data table, delivery/export table, or production factory is introduced.

## Minimal row shape

The minimal stored row shape is metadata-first:

- `review_item_id`
- `run_id`
- `candidate_id`
- `idempotency_key`
- `record_payload_hash`
- `status`
- `blocked_delivery_reason`
- `evidence_preview`
- `source_trace_json`
- `created_at`

The prototype does not store full `source_text`, raw MinerU/Excel/parser/OCR/LLM/VLM payloads, clean_data payloads, delivery/export payloads, production DSNs, secrets, or output paths.

## Write/read behavior

After all gates pass, `write_batch(...)` inserts metadata-only candidates into the test-owned in-memory table and returns a test-only receipt. `get_by_review_item_id(...)` and `list_by_run_id(...)` read back only from the same test-owned in-memory connection.

## Transaction and rollback behavior

`write_batch(...)` uses SQLite transaction behavior for batch writes. Tests prove:

- valid multi-row batch inserts atomically;
- invalid first row leaves zero rows;
- invalid later row after an earlier valid row rolls back the entire batch;
- read-after-failed-write returns no rows.

No partial success is allowed for invalid batches.

## Idempotency and uniqueness behavior

The prototype enforces local-only uniqueness for:

- `review_item_id`
- `idempotency_key`

Tests prove:

- same `idempotency_key` + same `record_payload_hash` returns deterministic no-duplicate retry behavior;
- same `idempotency_key` + different `record_payload_hash` fails closed;
- same `review_item_id` + conflicting identity fails closed;
- `record_payload_hash` is required.

These are test-only semantics and are not claimed as production-grade idempotency.

## Raw payload exclusion behavior

The prototype rejects forbidden raw or full payload fields before storage:

- `source_text`
- `full_source_text`
- raw MinerU/Excel/parser/OCR/LLM/VLM payloads
- unbounded evidence text
- clean_data payload/intent
- delivery/export payload/intent
- readiness override/gates
- caller-supplied DB rows/receipts/internal adapter state

## clean_data/delivery/export/readiness boundary

The prototype stores only test-only review_queue-like metadata. It does not:

- mutate clean_data;
- trigger delivery/export;
- promote `VERIFIED` to `STRONG_EVIDENCE`;
- auto-admit `VERIFIED` into clean_data;
- unblock delivery;
- open readiness gates.

Metadata and receipts keep:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Input mutation safety

The prototype deep-copies config and candidate payloads before validation/storage. Tests confirm caller config and candidate objects remain unchanged after successful writes and rejected paths.

## Error leakage safety

Activation, candidate, and conflict errors use generic messages. Tests confirm errors do not echo raw payloads, full source text, DSNs, secrets, hosts, endpoints, tokens, or file paths.

## Source inspection

Source inspection tests confirm:

- `sqlite3` appears in the new test-only prototype module;
- existing R7BX/R7BY boundary module still does not import `sqlite3`;
- production repository skeleton still does not import `sqlite3`;
- production code does not import `review_queue_local_test_db_prototype_348n`;
- the new prototype has no network, Docker, file-backed DB path, filesystem writes, or production imports.

## Compatibility with R7BX/R7BY boundary tests

R7BX/R7BY boundary tests still pass. The existing boundary skeleton remains stricter than R7CB: it is still planned-disabled and still performs no DB behavior.

## Repository skeleton compatibility

Repository skeleton tests still pass. `datefac_agent/review/review_queue_repository.py` remains disabled by default and was not modified.

## Validation outputs

Validation was run after implementation. Results:

```text
python -m py_compile tests/agent/review_queue_local_test_db_prototype_348n.py
PASS

python -m py_compile tests/agent/test_review_queue_local_test_db_prototype_348n.py
PASS

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

python -m pytest tests/agent/test_review_queue_local_test_db_prototype_348n.py -q
PASS: 57 passed in 0.37s

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
PASS: 88 passed in 0.28s

python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
PASS: 55 passed in 0.23s

python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
PASS: 32 passed in 0.16s

python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
PASS: 17 passed in 0.15s

python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
PASS: 63 passed in 0.69s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.64s

python -m pytest tests/agent -q
PASS: 792 passed in 4.03s

git status -sb
PASS before staging: only the three allowed R7CB files were untracked.

git diff --stat
PASS before staging: no tracked diff outside untracked allowed R7CB files.

git diff --name-only
PASS before staging: no tracked diff outside untracked allowed R7CB files.

git diff --check
PASS: no whitespace errors.
```

## Limitations

- This is still a test-only prototype.
- It is not production persistence.
- It is not a production repository.
- It creates no schema/migration files.
- It uses only in-memory SQLite and does not prove PostgreSQL/container/file DB behavior.
- It does not prove production concurrency, operational cleanup, performance, backup, or recovery behavior.
- It is not imported by `datefac_agent/`, runner, CLI, `review_queue_builder`, clean_data, delivery, or export paths.

## Decision

PASS. R7CB implements the minimum local test DB prototype in `tests/agent` only, with explicit activation gates, in-memory SQLite, metadata-only row shape, transaction rollback, idempotency/uniqueness conflict behavior, raw payload exclusion, input mutation safety, error leakage safety, and compatibility with existing boundaries.

## Recommended next task

```text
348N-R7CB-QA local test DB prototype minimum implementation review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; minimum local test DB prototype implemented safely as test-only.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; new R7CB prototype tests 57 passed; R7BY negative-path tests 88 passed; R7BX boundary tests 55 passed; repository QA 32 passed; repository skeleton 17 passed; fake repository 63 passed; persistence contract 76 passed; full tests/agent 792 passed.
files_modified（修改文件数）= 3.
error_count（错误数）= 0.
minimum_local_db_prototype_result（最小本地DB原型结果）= PASS; in-memory test-only prototype implemented under tests/agent.
test_only_implementation_result（test-only实现结果）= PASS; no production code modified or imported.
activation_gate_result（激活门结果）= PASS; explicit local-test gates required and env-only activation rejected.
in_memory_sqlite_result（内存SQLite结果）= PASS; sqlite3.connect(":memory:") only.
schema_setup_result（schema设置结果）= PASS; inline schema created only inside test-owned in-memory connection.
write_read_result（写入读取结果）= PASS; metadata-only write/read covered by tests.
transaction_rollback_result（事务回滚结果）= PASS; atomic batch and rollback covered by tests.
idempotency_uniqueness_result（幂等唯一性结果）= PASS; deterministic retry and conflict fail-closed behavior covered.
raw_payload_exclusion_result（原始payload排除结果）= PASS; full/raw payloads rejected before storage.
clean_data_delivery_boundary_result（clean_data/交付边界结果）= PASS; no clean_data/delivery/export/readiness mutation.
input_mutation_safety_result（输入变更安全结果）= PASS; config/candidates not mutated.
error_leakage_safety_result（错误泄漏安全结果）= PASS; generic errors do not echo sensitive values.
source_inspection_result（源码检查结果）= PASS; no network/Docker/file-backed DB/filesystem write/production import added.
compatibility_with_r7bx_r7by_result（与R7BX/R7BY兼容结果）= PASS; R7BY negative-path tests 88 passed and R7BX boundary tests 55 passed.
repository_skeleton_compatibility_result（repository skeleton兼容结果）= PASS; repository QA 32 passed and repository skeleton 17 passed.
boundary_check（边界检查）= PASS; only allowed R7CB files changed.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7CB-QA local test DB prototype minimum implementation review.
```
