# 348N-R7BR-QA fake repository negative-path and idempotency expansion review

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = QA-review-only
```

## Plain-language goal

R7BR expanded negative-path and idempotency coverage for the test-only fake repository / in-memory repository boundary. R7BR-QA checks that the expansion is safe, complete, deterministic, and still does not introduce real persistence.

In plain Chinese: 这一轮只审查 R7BR 的补防线是否靠谱。重点确认重复写、冲突写、坏批次、伪造 receipt、绕路输入、隐藏生产配置、对象引用污染都会被正确挡住；仍然只是 tests/agent 里的内存假仓库，不接数据库、不写文件、不建表、不加 migration、不接生产。

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
git log --oneline -65
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
docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md
docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
```

Review R7BR files:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json
docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
```

Review related test-only files read-only:

```text
tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json
tests/agent/review_queue_writer_schema_alignment_contract_348n.py
tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
```

## QA checklist

Confirm:

```text
R7BR changed only allowed test-only fake repository files, fixture, and report.
No datefac_agent production code was modified.
No database model, repository class, migration, storage code, output writer, export path, production hook, or readiness gate change was added.
The fake repository remains under tests/agent only.
The fake repository remains in-memory only.
No IO, DB, network, storage dependency, or production hook exists.
Repository default-disabled or explicit test-only behavior is preserved if supported by the current boundary.
Attempted production mode / production writer config is rejected.
Attempted DB DSN / connection string / table name / output path / file path config is rejected.
Attempted network/storage dependency marker is rejected.
Caller-supplied receipt is rejected.
Caller-supplied internal state is rejected.
Raw persistence rows not produced by persistence contract are rejected.
Raw schema alignment preview, dry-run output, writer preview, and adapter candidate output are rejected.
Missing required identity fields fail closed.
Malformed idempotency_key fails closed.
Malformed record_payload_hash fails closed.
Nested forbidden fields are rejected at any depth.
Full source_text and raw payload leakage are rejected.
clean_data intent is rejected.
delivery/export intent is rejected.
readiness override is rejected.
production timestamp policy is rejected.
Batch with valid first row and later invalid row fails as a whole.
Duplicate idempotency_key within same batch fails closed.
Duplicate review_item_id within same batch fails closed.
Same idempotency_key + same record_payload_hash retry has deterministic same-receipt or documented deterministic no-op behavior.
Same idempotency_key + different record_payload_hash fails closed.
Same review_item_id + different idempotency_key fails closed unless explicitly documented safe no-op.
Same review_item_id + same idempotency_key + changed payload fails closed.
Same record_payload_hash with different idempotency_key fails closed or has documented deterministic policy.
Write receipt is stable across retries.
Write receipt contains no forbidden config or raw payload.
Write receipt mutation cannot mutate repository state.
Read/list/get copy mutation cannot mutate repository state.
Repository instances do not share mutable state.
Reset/clear behavior, if present, is explicit test-only.
Rollback/retraction behavior, if present, is simulated only and does not destructive-delete by default.
Invalid writes do not mutate state.
Silent duplicate insert is forbidden.
Batch writes are atomic by default.
No partial success by default.
VERIFIED does not imply STRONG_EVIDENCE.
VERIFIED does not auto-write clean_data.
non-VERIFIED remains review-bound.
persistence candidate does not trigger delivery.
persistence candidate does not mutate clean_data.
persistence candidate does not open readiness gates.
readiness_gates remain CLOSED.
Validation counts match R7BR result: fake repository targeted tests 63 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 543 passed.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, handoff docs, planning docs, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md
```

No other tracked files may change.

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

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BR recap
大白话说明审查
Negative-path expansion review
Idempotency policy review
Duplicate conflict policy review
Batch atomicity review
Mutation isolation review
Receipt safety review
Forbidden field and raw payload leakage review
Production config rejection review
No-IO / no-DB / no-production-hook review
Validation outputs
Limitations
Decision
Recommended next task review
Data Result / 数据结果
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
negative_path_expansion_review_result（负路径扩展审查结果）=
idempotency_expansion_review_result（幂等扩展审查结果）=
duplicate_conflict_review_result（重复冲突审查结果）=
batch_atomicity_review_result（批次原子性审查结果）=
mutation_isolation_review_result（变更隔离审查结果）=
receipt_safety_review_result（receipt安全审查结果）=
forbidden_field_review_result（禁止字段审查结果）=
raw_payload_leakage_review_result（原始payload泄漏审查结果）=
production_config_rejection_review_result（生产配置拒绝审查结果）=
no_io_no_db_review_result（无IO无DB审查结果）=
test_only_boundary_review_result（test-only边界审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BS database schema and migration design docs-only
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md
git commit -m "docs: add R7BR QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
