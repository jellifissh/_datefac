# 348N-R7BQ-QA fake repository / in-memory repository boundary contract review

## Task ID

```text
348N-R7BQ-QA fake repository / in-memory repository boundary contract review
```

Task type: QA-review-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward c96395b..e1eccb2; R7BQ-QA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -60
PASS: latest history includes e1eccb2 R7BQ-QA task doc, c96395b R7BQ implementation, e66a272 R7BQ task doc, a568487 R7BP-QA, e08f6c6 R7BP, d027e85 R7BO-QA, 214a006 R7BO, b223c05 R7BN-QA, ce10b99 R7BM-QA, and 7713db4 R7BL-QA.
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
- `docs/codex_tasks/348N_R7BQ_QA_fake_repository_in_memory_repository_boundary_contract_review.md`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`
- `docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md`
- `docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md`
- `docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md`
- `docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md`
- `docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md`

R7BQ files reviewed:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`

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

## R7BQ recap

R7BQ added a test-only fake repository / in-memory repository boundary under `tests/agent/`. It accepts only R7BL/R7BM validated persistence candidate batches, simulates repository-layer validation and write semantics in memory, and returns safe write receipts and state snapshots.

R7BQ changed only:

- `tests/agent/review_queue_fake_repository_boundary_348n.py`
- `tests/agent/test_review_queue_fake_repository_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json`
- `docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md`

No `datefac_agent/` production code, dependency file, output artifact, database model, migration, storage implementation, output writer, runner, CLI, production hook, or readiness gate was modified.

## 大白话说明审查

PASS. R7BQ 的边界说法准确：这只是测试目录里的“假 repository 边界”，用于证明未来 repository 层应该如何验输入、幂等、冲突、回滚和隔离。它没有真实落库，不建表、不连 DB、不写 output、不导出、不接生产，也不让 `VERIFIED` 自动进入 `clean_data` 或升级为 `STRONG_EVIDENCE`。

## Test-only fake repository scope review

PASS. The fake repository implementation lives only in:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
```

The module imports stdlib plus the R7BL test-only persistence contract constants. It does not import `datefac_agent`, database drivers, storage clients, output writers, runner code, MinerU, OCR, PDF parsers, LLM/VLM clients, or network libraries.

The R7BQ commit scope check confirms only the allowed boundary, test, fixture, and report files were created.

## In-memory boundary review

PASS. `FakeReviewQueueRepository348N` stores rows only in private in-memory dictionaries:

```text
_records_by_idempotency_key
_review_item_to_idempotency_key
```

The enabled path prepares copied next-state dictionaries and replaces internal state only after all candidate rows pass validation. No file, database, network, migration, schema, export, or production write path exists.

## Accepted input shape review

PASS. The boundary accepts only R7BL persistence candidate batch envelopes with:

- `persistence_status = ENABLED_TEST_ONLY_PERSISTENCE_CANDIDATE`;
- `in_memory_only = true`;
- `persistence_candidate_only = true`;
- expected R7BL persistence contract version;
- expected persistence candidate batch schema version;
- matching run / adapter / input hash metadata;
- closed readiness gates;
- zero external-call counts;
- zero clean/data/delivery/filesystem/database/export write counts;
- closed boundary flags;
- exact R7BL candidate row fields.

The fake repository itself is disabled by default and requires explicit test-only use:

```text
allow_test_only_fake_repository = true
test_only_enable_token = R7BQ_TEST_ONLY_FAKE_REPOSITORY_ENABLE
```

Missing or invalid explicit enablement fails closed.

## Rejected bypass shapes review

PASS. Tests and fixture cover rejection of:

- raw schema alignment preview;
- raw dry-run integration output;
- raw writer preview;
- adapter candidate output;
- user direct fake repository rows;
- direct production repository config;
- DB URL / DSN / connection string;
- output/export/file paths;
- opened readiness gates;
- clean_data write intent;
- delivery/export intent;
- production hook intent;
- nested forbidden raw payloads.

The module rejects these recursively before any fake repository state mutation.

## Write receipt review

PASS. The write receipt is deterministic and safe. It contains only:

- status and mode;
- row/written/no-op counts;
- idempotency keys;
- record payload hashes;
- batch payload hash;
- repository state hash;
- boundary version;
- closed readiness gates;
- zero write counters;
- closed boundary flags.

The receipt does not contain DB IDs, table names, migration IDs, output paths, production config, raw payloads, full source text, or test-only enable token values. It does not imply real database persistence or delivery/export readiness.

## In-memory state review

PASS. `state_snapshot()` returns a deep-copied snapshot with:

- `mode = test_only_fake_repository`;
- `in_memory_only = true`;
- deterministic record list;
- deterministic `state_payload_hash`;
- zero write counters;
- closed readiness gates;
- closed boundary flags.

Stored records contain only the exact R7BL persistence candidate fields:

```text
review_item_id, run_id, source_file_hash, input_file_hashes,
adapter_version, contract_version, writer_contract_version, schema_version,
audit_hash, idempotency_key, metric_name, period, candidate_value,
normalized_candidate_value, agreement_status, review_status, review_reason,
reviewer_action, blocked_delivery_reason, re_audit_required,
evidence_preview, source_trace, created_by_system, record_payload_hash
```

## Idempotency and duplicate behavior review

PASS. R7BQ documents and tests the chosen deterministic idempotency rule:

```text
same idempotency_key + same record_payload_hash = idempotent no-op
same idempotency_key + different record_payload_hash = fail closed
same review_item_id + different idempotency_key = fail closed
same batch submitted twice = no duplicate stored rows
```

Targeted tests verify second submission returns `written_count = 0`, `idempotent_noop_count = 2`, and repository state remains at two records.

## Batch fail-closed review

PASS. Validation is all-or-nothing. Invalid rows anywhere in the batch raise `FakeReviewQueueRepositoryBoundaryError` and leave repository state unchanged.

Covered fail-closed cases include missing required fields, direct wrong-layer inputs, raw/full source payloads, unbounded evidence, DB/DSN/path fields, clean/delivery/export intent, readiness override, duplicate idempotency conflict, duplicate review item conflict, and mixed valid/invalid batches.

## Mutation isolation review

PASS. The boundary deep-copies:

- input candidate rows before storing;
- state snapshots returned to callers;
- write receipts returned to callers;
- validated candidate lists returned by `validate_persistence_candidate_batch_for_fake_repository_348n`.

Tests mutate the original input, returned receipt, and returned state snapshot after write. Fresh repository state remains unchanged.

## Read/list/get copy behavior review

PASS. R7BQ implements only `state_snapshot()` as a read/list-like operation. It returns a deep-copied state snapshot and cannot mutate internal state. There is no destructive read, no DB lookup, no repository query API, and no production-facing getter.

No rollback/retraction API is implemented; rollback behavior is simulated only by all-or-nothing in-memory state replacement.

## Forbidden field and raw payload leakage review

PASS. Recursive validation rejects:

- `source_text`, `full_source_text`, `raw_source_text`;
- raw MinerU / Excel / parser / PDF / OCR / LLM / VLM payloads;
- schema alignment / dry-run writer / adapter bypass payloads;
- fake repository direct rows;
- production repository or writer configs;
- DB URL / DSN / connection string / table / migration hints;
- output/export/filesystem paths;
- clean_data / delivery / export intents;
- test-only token/config leaks;
- timestamp-like nondeterministic fields.

Targeted tests also verify final state rows do not contain forbidden keys.

## clean_data and delivery/export boundary review

PASS. R7BQ keeps persistence separate from clean_data and delivery/export:

- `VERIFIED` is rejected from fake repository persistence;
- `STRONG_EVIDENCE` promotion is rejected;
- `clean_data_write_count = 0`;
- `delivery_write_count = 0`;
- `export_write_count = 0`;
- clean_data and delivery/export intents fail closed;
- non-VERIFIED candidates remain review-bound.

The fake repository does not admit rows into clean_data and does not unblock delivery.

## Readiness gates review

PASS. R7BQ keeps readiness gates closed:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Opened readiness gates fail closed. Receipt and state snapshots both report closed readiness gates.

## No-IO / no-DB / no-production-hook review

PASS. Static AST tests and QA review confirm the R7BQ module has no forbidden imports or calls:

- no `datefac_agent` import;
- no `sqlite3`, `sqlalchemy`, `psycopg2`, `pymysql`, DB connector, or storage dependency;
- no `open`, `write`, `write_text`, `to_csv`, `to_excel`, or filesystem write call;
- no network/API imports;
- no MinerU / OCR / PDF parser / LLM / VLM imports;
- no production hook.

PowerShell text scan found only defensive constants/tests for forbidden terms, not actual side effects.

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
PASS: 31 passed in 0.24s

python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
PASS: 76 passed in 0.40s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.19s

python -m pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
PASS: 36 passed in 0.15s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.15s

python -m pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
PASS: 75 passed in 0.23s

python -m pytest tests/agent -q
PASS: 511 passed in 2.08s

git status -sb
PASS before QA report creation: clean.

git diff --stat
PASS before QA report creation: no tracked diff.

git diff --name-only
PASS before QA report creation: no tracked diff.

git diff --check
PASS before QA report creation: no whitespace errors.
```

## Limitations

- This remains test-only and in-memory.
- No real review_queue persistence exists.
- No production repository class, database model, migration, storage implementation, output writer, runner, CLI, or production hook exists.
- Atomicity/rollback behavior is simulated in memory only.
- Idempotent retry and conflict handling are proven only for the fake repository boundary.
- No real DB transaction, concurrency, performance, retention, retraction, or review UI behavior is proven.
- Production persistence remains blocked pending future negative-path expansion, schema/migration design, disabled skeleton, local test DB prototype, rollback tests, and production gate review.

## Decision

PASS. R7BQ is safe, deterministic, test-only, and in-memory-only. It accepts only validated R7BL persistence candidate batches, rejects bypass/production/raw/full-text/clean/delivery/readiness misuse, emits safe deterministic receipts, preserves isolated in-memory state, and introduces no real persistence, DB, filesystem output, production hook, dependency, or readiness-gate change.

## Recommended next task review

Recommended next task is appropriate:

```text
348N-R7BR fake repository negative-path and idempotency expansion test-only
```

R7BR should remain test-only and focus on expanding fake repository misuse, idempotency, conflict, rollback simulation, and leakage negative-path coverage before any schema/migration or real repository work.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7BQ QA approved.
build_result（构建结果）= PASS; all required py_compile commands passed.
test_result（测试结果）= PASS; fake repository targeted tests 31 passed; related suites 76/29/36/24/75 passed; full tests/agent 511 passed.
files_modified（修改文件数）= 1 QA report only.
error_count（错误数）= 0.
fake_repository_boundary_review_result（fake repository边界审查结果）= PASS; boundary is tests/agent-only, disabled by default, explicit-token gated, and no production hook.
in_memory_state_review_result（内存状态审查结果）= PASS; state is private in-memory dictionaries with deep-copied deterministic snapshots.
accepted_input_review_result（允许输入审查结果）= PASS; accepts only enabled R7BL persistence candidate batch shape.
rejected_bypass_review_result（绕路输入审查结果）= PASS; schema preview, dry-run output, writer preview, adapter output, and user direct rows are rejected.
write_receipt_review_result（写入receipt审查结果）= PASS; receipt is deterministic safe metadata only and does not imply DB persistence.
idempotency_review_result（幂等审查结果）= PASS; same key/hash retry is deterministic no-op with no duplicate rows.
duplicate_behavior_review_result（重复行为审查结果）= PASS; same key/different hash and same review item/different key fail closed.
batch_fail_closed_review_result（批次fail-closed审查结果）= PASS; invalid row anywhere prevents state mutation.
mutation_isolation_review_result（变更隔离审查结果）= PASS; input, receipt, returned candidates, and state snapshots are deep-copy isolated.
forbidden_field_review_result（禁止字段审查结果）= PASS; recursive validation rejects source_text, DB/storage/path, clean/delivery/export, production, token, timestamp, and readiness misuse fields.
raw_payload_leakage_review_result（原始payload泄漏审查结果）= PASS; raw MinerU/Excel/parser/OCR/LLM/VLM payloads and full source text are rejected.
clean_data_delivery_boundary_review_result（clean_data/交付边界审查结果）= PASS; no VERIFIED promotion, no STRONG_EVIDENCE promotion, no clean_data write/admission, no delivery/export trigger.
readiness_gate_review_result（就绪门审查结果）= PASS; gates remain CLOSED and opened gates fail closed.
no_io_no_db_review_result（无IO无DB审查结果）= PASS; no IO, DB, network, export, migration, storage, or production-hook side effect found.
boundary_check（边界检查）= PASS; only this QA report is created.
readiness_gates（就绪门）= CLOSED.
recommended_next_task（推荐下一任务）= 348N-R7BR fake repository negative-path and idempotency expansion test-only.
```
