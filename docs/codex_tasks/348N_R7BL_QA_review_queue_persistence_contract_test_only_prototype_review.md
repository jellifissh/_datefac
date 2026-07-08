# 348N-R7BL-QA review_queue persistence contract test-only prototype review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Plain-language goal

R7BL added a test-only review_queue persistence contract prototype. R7BL-QA checks that it is safe, conservative, and still purely test-only.

In plain Chinese: 这一轮只审查“模拟落库前最后一道闸门”。重点确认它只产生内存里的 persistence candidate batch，不写数据库、不建表、不导出、不接生产、不改 clean_data、不打开 readiness gates。

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
git log --oneline -35
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
docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md
docs/agent/348N_R7BJ_QA_PROJECT_DOCUMENTATION_SYNC_REVIEW_AFTER_REVIEW_QUEUE_DRY_RUN_SCHEMA_ALIGNMENT_MILESTONE.md
docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
```

Review R7BL files:

```text
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
```

Review related test-only slices read-only:

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

## QA checklist

Confirm:

```text
R7BL changed only the intended test-only contract, tests, fixture, and report.
The new contract lives under tests/agent only.
No datefac_agent production code was modified.
No database model, repository class, migration, storage code, output writer, export path, production hook, or readiness gate change was added.
The contract is disabled by default and fails closed.
Explicit test-only persistence flag is required.
Only validated schema alignment preview payloads are accepted.
Schema-alignment bypass is rejected.
Dry-run integration output passed directly into persistence contract is rejected.
Writer preview passed directly into persistence contract is rejected.
Adapter candidate output passed directly into persistence contract is rejected.
Raw extraction payloads are rejected.
Full source_text is rejected.
clean_data write intent is rejected.
delivery/export intent is rejected.
production writer config is rejected.
readiness_gates not CLOSED is rejected.
Missing review_item_id fails closed.
Missing run_id fails closed.
Missing audit_hash fails closed.
Missing idempotency_key fails closed.
Malformed idempotency_key fails closed.
Missing hash identity fails closed.
Unresolved record without blocked_delivery_reason fails closed.
Corrected record without re_audit_required fails closed.
Duplicate idempotency_key fails closed or is handled by an explicitly documented deterministic duplicate policy.
Unbounded evidence text is rejected.
User-provided direct persistence candidate is rejected.
The output is in-memory persistence_candidate_batch only.
Candidate rows contain only allowed deterministic safe fields.
Candidate rows exclude forbidden fields and test-only token/config fields.
record_payload_hash is deterministic.
idempotency_key is deterministic and stable across retries.
Candidate row ordering is deterministic.
Input mutation after call cannot mutate output.
Batch failure returns no partial candidate batch.
VERIFIED does not imply STRONG_EVIDENCE.
VERIFIED does not auto-write clean_data.
non-VERIFIED remains review-bound.
Persistence candidate does not trigger delivery.
Persistence candidate does not mutate clean_data.
Persistence candidate does not open readiness gates.
No IO, DB, export, parser, model, MinerU, OCR, VLM, or production call exists.
readiness_gates remain CLOSED.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
```

No other tracked files may change.

## Validation commands

```text
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
R7BL recap
大白话说明审查
Test-only persistence contract scope review
Contract design review
Accepted input shape review
Rejected bypass shapes review
Persistence candidate batch shape review
Required fields review
Forbidden fields review
Idempotency and duplicate prevention review
Record payload hash strategy review
Batch fail-closed behavior review
Transaction and rollback simulation review
Audit metadata retention review
Evidence preview and source_text boundary review
clean_data safety boundary review
Delivery/export boundary review
Readiness gates boundary review
No-hook and no-IO boundary review
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
persistence_contract_review_result（持久化契约审查结果）=
persistence_candidate_batch_review_result（持久化候选批次审查结果）=
required_field_review_result（必需字段审查结果）=
forbidden_field_review_result（禁止字段审查结果）=
idempotency_review_result（幂等审查结果）=
duplicate_prevention_review_result（去重审查结果）=
record_payload_hash_review_result（记录payload哈希审查结果）=
batch_fail_closed_review_result（批次fail-closed审查结果）=
rollback_simulation_review_result（回滚模拟审查结果）=
audit_metadata_review_result（审计元数据审查结果）=
evidence_boundary_review_result（证据边界审查结果）=
clean_data_boundary_review_result（clean_data边界审查结果）=
delivery_export_boundary_review_result（交付导出边界审查结果）=
readiness_gate_boundary_review_result（就绪门边界审查结果）=
no_hook_no_io_review_result（无hook无IO审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BM review_queue persistence contract negative-path expansion test-only
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
git commit -m "docs: add R7BL QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
