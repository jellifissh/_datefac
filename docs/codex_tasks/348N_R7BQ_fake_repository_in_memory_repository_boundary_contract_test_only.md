# 348N-R7BQ fake repository / in-memory repository boundary contract test-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-fake-repository-boundary-contract
```

## Plain-language goal

R7BP-QA approved the docs-only implementation plan for future review_queue persistence. R7BQ starts the first safe implementation-adjacent step: a fake repository / in-memory repository boundary contract under `tests/agent` only.

This is still not real persistence. It must not create a DB schema, repository class in production code, migration, storage implementation, output writer, production hook, or DB connection.

In plain Chinese: 这一轮只在测试区做一个“假的 repository 边界”。它接收 R7BL/R7BM 已经验证过的 in-memory persistence candidate batch，然后模拟“如果未来要交给 repository，边界应该怎么验、怎么幂等、怎么回滚”。它只能写内存，不能写数据库，不能建表，不能接生产。

## Workspace

```text
D:\_datefac_agent
branch = pivot/348-agent-foundation
```

## Preflight

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -60
```

Stop if the worktree is not clean after pull.

## Read first

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md
docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
```

Review current test-only persistence contract files:

```text
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json
```

Review related slices read-only:

```text
tests/agent/review_queue_writer_schema_alignment_contract_348n.py
tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
```

Do not modify production-adjacent files. Read only if needed:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a test-only fake repository boundary contract for the chain:

```text
test-only persistence contract
-> in-memory persistence candidate batch
-> test-only fake repository boundary
-> in-memory write receipt / fake repository state
```

The goal is to prove the future repository boundary rules before any real repository, DB model, migration, or storage code exists.

## Allowed tracked files

Create exactly:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
```

No production files may change.

## Required fake repository behavior

The fake repository boundary must be test-only and in-memory.

It must enforce:

```text
default disabled fail-closed
explicit test-only fake repository flag required
accept only validated test-only persistence_candidate_batch
reject direct schema alignment preview
reject direct dry-run integration output
reject direct writer preview
reject direct adapter candidate output
reject user-provided direct fake repository rows
reject any production repository config
reject any DB URL / DSN / connection string
reject any output path / export path
reject readiness_gates not CLOSED
reject clean_data write intent
reject delivery/export intent
reject production hook intent
reject missing required candidate fields
reject forbidden fields even when nested
reject raw MinerU/raw Excel/raw parser/raw LLM/VLM payloads
reject full source_text / unbounded evidence
produce only in-memory fake repository state and write receipt
no DB write
no file/output write
no migration
no production import side effect
no clean_data mutation
no delivery unblock
no readiness gate mutation
```

## Suggested interface shape

Choose names that fit the existing style, but keep them test-only. A possible shape:

```text
class FakeReviewQueueRepository348N
persist_candidate_batch_to_fake_repository_348n(candidate_batch, *, allow_test_only_fake_repository=False)
```

The output may be named something like:

```text
fake_repository_write_receipt
fake_repository_state_snapshot
```

The receipt may include deterministic safe metadata only:

```text
status
mode = test_only_fake_repository
row_count
written_count
idempotent_noop_count
idempotency_keys
record_payload_hashes
batch_payload_hash
boundary_version
readiness_gates = CLOSED
```

Do not include real database IDs, table names that imply implemented schema, migration IDs, production config, DB connection strings, output paths, full source text, raw parser/model payloads, or test-only enable token/config objects in persisted candidate rows.

## Required idempotency behavior

Plan and implement a deterministic in-memory rule:

```text
same idempotency_key + same record_payload_hash = deterministic idempotent no-op or same receipt semantics
same idempotency_key + different record_payload_hash = fail closed
same review_item_id + conflicting idempotency_key = fail closed
same batch submitted twice = deterministic result, no duplicate stored rows
invalid row anywhere in batch = whole batch fails closed, no partial write
```

Document the chosen same-key/same-hash behavior in the R7BQ report.

## Required transaction / rollback simulation

Because this is fake and in-memory, do not implement real DB transactions.

Simulate transaction expectations with pure data:

```text
valid batch writes atomically to fake repository state
invalid batch leaves fake repository state unchanged
conflicting duplicate leaves fake repository state unchanged
mutation after write cannot mutate repository state
write receipt is deep-copied / caller mutation cannot affect state
```

## Required candidate row safety

The fake repository state may contain only safe candidate row fields already allowed by the persistence contract, such as:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
contract_version
writer_contract_version
schema_version
audit_hash
idempotency_key
metric_name
period
candidate_value
normalized_candidate_value
agreement_status
review_status
review_reason
reviewer_action
blocked_delivery_reason
re_audit_required
evidence_preview
source_trace
created_by_system
record_payload_hash
```

Do not add production timestamps as policy. If fixed test timestamps are unavoidable, mark them as deterministic test data only.

## Required tests

Add focused tests proving:

```text
default disabled fails closed
explicit test-only fake repository flag required
valid persistence_candidate_batch writes to in-memory fake repository only
write receipt contains safe deterministic metadata
fake repository state contains safe candidate rows only
schema alignment preview rejected directly
dry-run integration output rejected directly
writer preview rejected directly
adapter candidate output rejected directly
user direct fake repository row rejected
production repository config rejected
DB URL / DSN / connection string rejected
output path / export path rejected
readiness OPEN rejected
clean_data intent rejected
delivery/export intent rejected
production hook intent rejected
missing required candidate fields rejected
nested forbidden fields rejected
raw MinerU/Excel/parser/LLM/VLM rejected
full source_text rejected
unbounded evidence rejected
same idempotency_key + same record_payload_hash is deterministic no-op or documented deterministic behavior
same idempotency_key + different record_payload_hash fails closed
same review_item_id + conflicting idempotency_key fails closed
same batch submitted twice does not duplicate stored rows
invalid row in mixed batch fails whole batch
invalid batch leaves fake repository state unchanged
conflicting duplicate leaves fake repository state unchanged
caller mutation after write cannot mutate fake repository state
caller mutation after receipt cannot mutate fake repository state
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED remains review-bound
persistence/fake repository write does not trigger delivery
persistence/fake repository write does not open readiness gates
no IO/no DB/no export/no production hook exists
```

## Fixture requirements

Create a small curated fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
```

Suggested fixture cases:

```text
valid_candidate_batch
valid_duplicate_retry_same_key_same_hash
invalid_missing_test_fake_repo_flag
invalid_direct_schema_alignment_preview
invalid_direct_writer_preview
invalid_direct_adapter_candidate
invalid_user_direct_fake_repository_row
invalid_db_dsn
invalid_output_path
invalid_readiness_open
invalid_clean_data_intent
invalid_delivery_export_intent
invalid_nested_forbidden_payload
invalid_duplicate_idempotency_conflict
invalid_review_item_conflict
invalid_mixed_batch_partial_write_attempt
```

Keep fixtures tiny. No real PDFs, no DateFac Excel, no full MinerU output, no raw source text, no real secrets.

## Strict boundaries

Forbidden:

```text
modify datefac_agent production code
add production repository/model/service code
add DB schema
add migration
add DB connection
add storage implementation
write output files
export delivery files
run MinerU/OCR/LLM/VLM or real extraction
open readiness gates
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED directly to clean_data
use git add .
use git add -A
```

## Report requirements

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BP-QA recap
大白话说明
Fake repository boundary scope
Accepted input shape
Rejected bypass shapes
Fake repository state shape
Write receipt shape
Required fields
Forbidden fields
Idempotency behavior
Duplicate conflict behavior
Atomic write / rollback simulation
Mutation isolation
clean_data and delivery/export separation
Readiness gates boundary
No-IO / no-DB / no-production-hook boundary
Fixture coverage
Test coverage
Validation outputs
Limitations
Decision
Recommended next task
Data Result / 数据结果
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
fake_repository_boundary_result（fake repository边界结果）=
in_memory_state_result（内存状态结果）=
write_receipt_result（写入回执结果）=
required_field_result（必需字段结果）=
forbidden_field_result（禁止字段结果）=
idempotency_result（幂等结果）=
duplicate_conflict_result（重复冲突结果）=
atomic_rollback_simulation_result（原子/回滚模拟结果）=
mutation_isolation_result（变更隔离结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
readiness_gate_boundary_result（就绪门边界结果）=
no_io_no_db_result（无IO无DB结果）=
fixture_coverage_result（fixture覆盖结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BQ-QA fake repository / in-memory repository boundary contract review
```

## Validation commands

```text
python -m py_compile tests/agent/review_queue_fake_repository_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_fake_repository_boundary_348n.py
python -m py_compile tests/agent/review_queue_persistence_contract_348n.py
python -m py_compile tests/agent/test_review_queue_persistence_contract_348n.py
python -m py_compile tests/agent/review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
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

## Commit and push

If validation passes and only allowed files changed, stage exactly:

```text
git add tests/agent/review_queue_fake_repository_boundary_348n.py
git add tests/agent/test_review_queue_fake_repository_boundary_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
git add docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
git commit -m "test: add fake review queue repository boundary"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
