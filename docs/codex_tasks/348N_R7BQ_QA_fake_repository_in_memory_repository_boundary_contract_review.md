# 348N-R7BQ-QA fake repository / in-memory repository boundary contract review

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = QA-review-only
```

## Plain-language goal

R7BQ added a test-only fake repository / in-memory repository boundary for future review_queue persistence. R7BQ-QA checks that this boundary is safe, deterministic, in-memory only, and still does not introduce real persistence.

In plain Chinese: 这一轮只审查假的内存 repository 边界。重点确认它只是 tests/agent 里的 test-only 假仓库，不接真实数据库、不写文件、不建表、不加 migration、不接生产；它只验证未来 repository 的写入契约、幂等、receipt、内存状态和 fail-closed 行为。

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
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md
docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
```

Review R7BQ files:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
```

Review related test-only files read-only:

```text
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
R7BQ changed only allowed test-only boundary, tests, fixture, and report.
No datefac_agent production code was modified.
No database model, repository class, migration, storage code, output writer, export path, production hook, or readiness gate change was added.
The fake repository boundary lives under tests/agent only.
The fake repository is in-memory only.
The fake repository performs no IO.
The fake repository performs no DB/network call.
The fake repository imports no production database/storage dependency.
The fake repository requires explicit test-only use and cannot be accidentally production-enabled.
The fake repository accepts only validated persistence candidate batches from the test-only persistence contract.
The fake repository rejects raw schema alignment preview, raw dry-run output, raw writer preview, adapter candidate output, and user direct rows.
The fake repository preserves required persistence candidate fields.
The fake repository rejects missing review_item_id, run_id, audit_hash, idempotency_key, record_payload_hash, and hash identity.
The fake repository rejects forbidden fields and raw payload leakage.
The fake repository does not allow source_text, raw MinerU, raw Excel, raw parser payload, raw LLM/VLM response, clean_data intent, delivery/export intent, production writer config, readiness override, DSN/table/output path, or production timestamp policy.
The write receipt is deterministic and test-only.
The write receipt does not imply DB persistence.
The write receipt does not imply delivery, export, clean_data mutation, or readiness gate opening.
In-memory state is deterministic and isolated per repository instance.
Input mutation after write cannot mutate repository state or returned receipts.
Idempotent retry behavior is deterministic.
Duplicate idempotency_key behavior is deterministic and fail-closed or documented no-op, with no silent duplicate insert.
Duplicate review_item_id conflict behavior is deterministic and fail-closed or documented safe no-op.
Batch write fails closed on any invalid row.
Batch write returns no partial success unless explicitly documented as impossible or deferred.
Read/list/get operations, if present, are read-only copies and cannot mutate internal state.
Rollback/retraction behavior, if present, is simulated only and does not delete destructively by default.
VERIFIED does not imply STRONG_EVIDENCE.
VERIFIED does not auto-write clean_data.
non-VERIFIED remains review-bound.
Persistence candidate does not trigger delivery.
Persistence candidate does not mutate clean_data.
Persistence candidate does not open readiness gates.
readiness_gates remain CLOSED.
Validation counts match R7BQ result: fake repository targeted tests 31 passed; persistence contract 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 511 passed.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, handoff docs, planning docs, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
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
R7BQ recap
大白话说明审查
Test-only fake repository scope review
In-memory boundary review
Accepted input shape review
Rejected bypass shapes review
Write receipt review
In-memory state review
Idempotency and duplicate behavior review
Batch fail-closed review
Mutation isolation review
Read/list/get copy behavior review
Forbidden field and raw payload leakage review
clean_data and delivery/export boundary review
Readiness gates review
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
fake_repository_boundary_review_result（fake repository边界审查结果）=
in_memory_state_review_result（内存状态审查结果）=
accepted_input_review_result（允许输入审查结果）=
rejected_bypass_review_result（绕路输入审查结果）=
write_receipt_review_result（写入receipt审查结果）=
idempotency_review_result（幂等审查结果）=
duplicate_behavior_review_result（重复行为审查结果）=
batch_fail_closed_review_result（批次fail-closed审查结果）=
mutation_isolation_review_result（变更隔离审查结果）=
forbidden_field_review_result（禁止字段审查结果）=
raw_payload_leakage_review_result（原始payload泄漏审查结果）=
clean_data_delivery_boundary_review_result（clean_data/交付边界审查结果）=
readiness_gate_review_result（就绪门审查结果）=
no_io_no_db_review_result（无IO无DB审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BR fake repository negative-path and idempotency expansion test-only
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
git commit -m "docs: add R7BQ QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
