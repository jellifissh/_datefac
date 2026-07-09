# 348N-R7BQ fake repository / in-memory repository boundary contract test-only

## Task ID

```text
348N-R7BQ fake repository / in-memory repository boundary contract test-only
```

Task type: test-only-fake-repository-boundary-contract.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: already up to date after fast-forward to e66a272.

git status -sb
PASS: clean after pull.

git log --oneline -60
PASS: latest history includes e66a272 R7BQ task doc, a568487 R7BP-QA, e08f6c6 R7BP, d027e85 R7BO-QA, 214a006 R7BO, b223c05 R7BN-QA, ce10b99 R7BM-QA, 9daca34 R7BM, 7713db4 R7BL-QA, and c76499e R7BL.
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
- `docs/codex_tasks/348N_R7BQ_fake_repository_in_memory_repository_boundary_contract_test_only.md`
- `docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md`
- `docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md`
- `docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md`

Current test-only persistence contract reviewed:

- `tests/agent/review_queue_persistence_contract_348n.py`
- `tests/agent/test_review_queue_persistence_contract_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json`

Related slices reviewed read-only:

- `tests/agent/review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py`
- `tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py`
- `tests/agent/review_queue_writer_contract_348n.py`
- `tests/agent/test_review_queue_writer_contract_348n.py`
- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`

## R7BP-QA recap

R7BP-QA approved a docs-only future persistence plan. It explicitly kept real persistence blocked until fake repository, negative-path, schema/migration, disabled skeleton, local test database, rollback, and production gate-review slices are separately completed.

R7BQ implements only the first implementation-adjacent slice: a test-only fake repository boundary under `tests/agent/`.

## 大白话说明

这一轮只是在测试目录里做一个“假的 repository 边界”。它接收 R7BL/R7BM 已经验证过的 in-memory persistence candidate batch，然后模拟未来 repository 层应该如何校验、幂等、冲突、回滚和隔离。

它不建表、不连数据库、不写文件、不导出、不接 production pipeline，也不让 `VERIFIED` 自动进入 `clean_data` 或升级为 `STRONG_EVIDENCE`。

## Fake repository boundary scope

Implemented files:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`

Implemented chain:

```text
test-only persistence contract
-> in-memory persistence candidate batch
-> test-only fake repository boundary
-> in-memory write receipt / fake repository state
```

## Accepted input shape

The boundary accepts only enabled R7BL persistence candidate batches with:

- `persistence_status = ENABLED_TEST_ONLY_PERSISTENCE_CANDIDATE`
- `in_memory_only = true`
- `persistence_candidate_only = true`
- R7BL persistence contract version
- R7BL persistence candidate batch schema version
- closed readiness gates
- zero external-call counts
- zero clean/data/delivery/filesystem/database/export write counts
- closed boundary flags
- `review_queue_persistence_candidate_batch[]` rows containing only required safe candidate fields

The fake repository itself is disabled by default and requires:

```text
allow_test_only_fake_repository = true
test_only_enable_token = R7BQ_TEST_ONLY_FAKE_REPOSITORY_ENABLE
```

## Rejected bypass shapes

The boundary rejects:

- direct schema alignment preview
- direct dry-run integration output
- direct writer preview
- direct adapter candidate output
- user-provided fake repository rows
- production repository config
- DB URL / DSN / connection string
- output path / export path
- opened readiness gates
- clean_data write intent
- delivery/export intent
- production hook intent
- missing required candidate fields
- nested forbidden fields
- raw MinerU / Excel / parser / LLM / VLM payloads
- full source_text / unbounded evidence

## Fake repository state shape

`FakeReviewQueueRepository348N.state_snapshot()` returns only safe in-memory metadata:

- `mode = test_only_fake_repository`
- `boundary_version`
- `in_memory_only = true`
- `record_count`
- `records[]`
- `state_payload_hash`
- zero write counters
- closed readiness gates
- closed boundary flags

Each record contains only the allowed R7BL candidate fields:

- `review_item_id`
- `run_id`
- `source_file_hash`
- `input_file_hashes`
- `adapter_version`
- `contract_version`
- `writer_contract_version`
- `schema_version`
- `audit_hash`
- `idempotency_key`
- `metric_name`
- `period`
- `candidate_value`
- `normalized_candidate_value`
- `agreement_status`
- `review_status`
- `review_reason`
- `reviewer_action`
- `blocked_delivery_reason`
- `re_audit_required`
- `evidence_preview`
- `source_trace`
- `created_by_system`
- `record_payload_hash`

## Write receipt shape

`fake_repository_write_receipt` includes deterministic safe metadata only:

- `status = WRITE_ACCEPTED`
- `mode = test_only_fake_repository`
- `row_count`
- `written_count`
- `idempotent_noop_count`
- `idempotency_keys`
- `record_payload_hashes`
- `batch_payload_hash`
- `repository_state_hash`
- `boundary_version`
- `readiness_gates = CLOSED`
- zero write counters
- closed boundary flags

No DB ids, table names, migration ids, production configs, output paths, full source text, raw parser/model payloads, or test-only enable token values are persisted.

## Required fields

The fake repository requires the exact R7BL persistence candidate row field set. Missing fields fail closed before any state mutation.

Test coverage includes `audit_hash` deletion and confirms the write is rejected with no partial state.

## Forbidden fields

Recursive forbidden-field validation rejects:

- full `source_text` / `full_source_text`
- raw MinerU / Excel / parser / OCR / LLM / VLM payloads
- schema alignment, dry-run writer, and adapter bypass payloads
- fake repository direct rows
- production repository/writer config
- DB DSN / connection strings / table and migration hints
- filesystem/output/export paths
- clean_data / delivery / export intents
- test-only token/config leaks
- non-deterministic timestamp-like fields

## Idempotency behavior

Chosen behavior:

```text
same idempotency_key + same record_payload_hash = deterministic idempotent no-op
same idempotency_key + different record_payload_hash = fail closed
same batch submitted twice = second write has written_count = 0 and idempotent_noop_count = row_count
```

The second write does not duplicate fake repository state.

## Duplicate conflict behavior

The boundary fails closed for:

- duplicate `idempotency_key` inside a single incoming batch
- duplicate `review_item_id` inside a single incoming batch
- existing `idempotency_key` with changed `record_payload_hash`
- existing `review_item_id` with a different `idempotency_key`

## Atomic write / rollback simulation

No DB transaction is implemented. Atomicity is simulated with pure in-memory data:

```text
validate whole batch
prepare next in-memory state on copies
replace fake repository state only after all rows pass
```

Tests prove:

- valid batch writes atomically
- invalid mixed batch leaves existing state unchanged
- idempotency conflict leaves existing state unchanged
- review item conflict leaves existing state unchanged

## Mutation isolation

The fake repository deep-copies input rows, state snapshots, and receipts. Tests mutate:

- the original input batch after write
- returned receipt
- returned state snapshot

The stored fake repository state remains unchanged.

## clean_data and delivery/export separation

The boundary keeps persistence separate from clean_data and delivery/export:

- `VERIFIED` rows do not enter fake repository persistence
- `STRONG_EVIDENCE` promotion is rejected
- `clean_data_write_count = 0`
- `delivery_write_count = 0`
- `export_write_count = 0`
- clean_data and delivery/export intents fail closed

## Readiness gates boundary

Readiness gates remain closed:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Opened readiness gates in the candidate batch fail closed.

## No-IO / no-DB / no-production-hook boundary

The R7BQ module:

- lives under `tests/agent/`
- imports no `datefac_agent`
- performs no filesystem writes
- opens no DB connection
- creates no schema/model/migration
- writes no output files
- performs no network/API calls
- imports no MinerU/OCR/PDF/LLM/VLM libraries
- has no runner / CLI / production hook

Static AST tests check forbidden imports and forbidden calls.

## Fixture coverage

Created small curated fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
```

Fixture cases cover:

- valid candidate batch
- duplicate retry with same key/hash
- missing fake repository flag
- direct schema alignment preview
- direct dry-run integration output
- direct writer preview
- direct adapter candidate
- user direct fake repository row
- DB DSN
- output path
- opened readiness gate
- clean_data intent
- delivery/export intent
- nested forbidden payload
- duplicate idempotency conflict
- review item conflict
- mixed batch partial-write attempt

The fixture is tiny and contains no real PDFs, DateFac Excel, full MinerU output, raw source text, or secrets.

## Test coverage

Targeted tests cover:

- disabled default
- explicit test-only fake repository token
- valid in-memory write
- deterministic safe receipt
- safe repository state only
- bypass layer rejection
- production config / DB / output rejection
- readiness / clean_data / delivery / production hook rejection
- required field rejection
- nested forbidden raw payload rejection
- full source text and unbounded evidence rejection
- idempotent no-op retry
- duplicate conflict fail-closed behavior
- atomic rollback simulation
- mutation isolation
- VERIFIED / STRONG_EVIDENCE / clean_data / delivery / readiness boundaries
- no-IO / no-DB / no-export / no-production-hook AST boundary

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
PASS: 31 passed in 0.25s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.40s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.12s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.25s

python -m pytest tests/agent -q
PASS: 511 passed in 1.98s
```

## Limitations

- This remains test-only and in-memory.
- No real repository class in production code exists.
- No DB schema, model, migration, storage implementation, DB connection, output writer, runner, CLI, or production hook exists.
- Atomicity is a pure in-memory simulation, not a real database transaction.
- Idempotent retry and conflict behavior are proven only for fake repository state.
- Production persistence remains blocked pending future QA, schema/migration design, disabled skeleton, local test DB prototype, rollback tests, and production gate review.

## Decision

PASS. R7BQ adds a bounded test-only fake repository / in-memory repository boundary contract. It accepts only validated R7BL/R7BM persistence candidate batches, writes only in-memory state, emits safe deterministic receipts, fails closed on bypass/production/raw/full-text/clean/delivery/readiness misuse, and proves idempotency, duplicate conflict, atomic rollback simulation, mutation isolation, and no-IO/no-DB/no-production-hook boundaries.

## Recommended next task

```text
348N-R7BQ-QA fake repository / in-memory repository boundary contract review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; test-only fake repository boundary implemented.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; R7BQ targeted tests 31 passed; related suites 76/29/36/24/75 passed; full tests/agent 511 passed.
files_modified（修改文件数）= 4 allowed files.
error_count（错误数）= 0.
fake_repository_boundary_result（fake repository边界结果）= PASS; disabled by default, explicit R7BQ token required, accepts only R7BL candidate batch.
in_memory_state_result（内存状态结果）= PASS; state remains in-memory-only and metadata-first.
write_receipt_result（写入回执结果）= PASS; deterministic safe receipt includes counts, keys, hashes, closed gates, and zero write counters.
required_field_result（必需字段结果）= PASS; exact persistence candidate row fields enforced.
forbidden_field_result（禁止字段结果）= PASS; bypass shapes, production config, DB/DSN/path, raw artifacts, full source_text, clean_data/delivery/export intent, and token leaks rejected.
idempotency_result（幂等结果）= PASS; same idempotency_key + same record_payload_hash is deterministic no-op on retry.
duplicate_conflict_result（重复冲突结果）= PASS; same key/different hash and same review_item/different key fail closed.
atomic_rollback_simulation_result（原子/回滚模拟结果）= PASS; invalid/conflicting batches leave fake repository state unchanged.
mutation_isolation_result（变更隔离结果）= PASS; input, returned receipt, and returned snapshot mutations cannot mutate repository state.
clean_data_delivery_boundary_result（clean_data/交付边界结果）= PASS; no clean_data write/admission, no delivery/export trigger, no VERIFIED promotion.
readiness_gate_boundary_result（就绪门边界结果）= PASS; readiness gates remain CLOSED and opened gates fail closed.
no_io_no_db_result（无IO无DB结果）= PASS; AST checks confirm no forbidden IO/DB/export/production-hook imports or calls.
fixture_coverage_result（fixture覆盖结果）= PASS; small curated fixture covers valid, retry, bypass, production, raw, clean/delivery, readiness, conflict, and partial-write cases.
boundary_check（边界检查）= PASS; only allowed R7BQ files changed.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BQ-QA fake repository / in-memory repository boundary contract review.
```
