# 348N-R7BI-QA review-queue writer dry-run schema alignment test-only contract prototype review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Plain-language goal

R7BI added a test-only schema alignment contract prototype. R7BI-QA checks that the contract is correct, conservative, and still test-only.

In plain Chinese: 这一轮只审查字段闸门。确认它能把 dry-run integration output 安全映射成未来 review_queue 记录预览，同时挡住 full source_text、raw extraction payload、clean_data intent、production config、readiness OPEN、direct writer-preview payload 等坏输入。仍然不能写库、不能建表、不能导出、不能接生产。

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
git log --oneline -25
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
docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
docs/agent/348N_R7BH_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md
docs/agent/348N_R7BG_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
```

Review R7BI files:

```text
tests/agent/review_queue_writer_schema_alignment_contract_348n.py
tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bi_schema_alignment_contract_fixture.json
docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
```

Review related slices read-only:

```text
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
```

## QA checklist

Confirm:

```text
R7BI changed only the intended test-only contract, tests, fixture, and report.
The new contract lives under tests/agent only.
No datefac_agent production code was modified.
No database model, repository class, migration, output writer, export path, production hook, or readiness gate change was added.
The contract is disabled by default and fails closed.
Explicit test-only enable is required.
Only validated dry-run chain payloads are accepted.
Adapter-only payloads that did not pass integration boundary are rejected.
Direct writer-preview-shaped payloads are rejected.
Raw extraction payloads are rejected.
Full source_text is rejected at all layers.
clean_data write intent is rejected.
formal delivery/export payload is rejected.
production writer config is rejected.
readiness_gates not CLOSED is rejected.
Schema mismatch fails closed before future persistence preview.
Writer preview mismatch fails closed after writer output.
The alignment preview is in-memory only.
Future review_queue record preview contains only safe fields.
Future preview excludes test-only enable token and test-only writer config.
Field classification covers all required R7BH fields.
Required audit fields are preserved.
Idempotency key is deterministic and stable across retries.
normalized_candidate_value is deterministic.
No wall-clock timestamp is required for idempotency.
Input mutation after call cannot mutate output.
VERIFIED does not imply STRONG_EVIDENCE.
VERIFIED does not auto-write clean_data.
non-VERIFIED rows remain review-bound.
Unresolved rows keep blocked_delivery_reason.
Corrected rows remain re-audit-required.
No IO, DB, export, parser, model, MinerU, OCR, VLM, or production call exists.
readiness_gates remain CLOSED.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
```

No other tracked files may change.

## Validation commands

```text
python -m py_compile tests/agent/review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
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
R7BI recap
大白话说明审查
Test-only schema alignment scope review
Contract design review
Field classification review
Future persistence preview shape review
Required fields review
Forbidden fields review
Pass-through and normalization rules review
Idempotency and duplicate prevention review
Audit metadata retention review
Evidence preview and source_text boundary review
clean_data safety boundary review
Delivery gate and blocked_delivery_reason fields review
Corrected row and re-audit policy review
Dry-run-only and test-only boundary review
Failure and fail-closed behavior review
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
schema_alignment_contract_review_result（schema对齐契约审查结果）=
field_classification_review_result（字段分类审查结果）=
future_persistence_preview_review_result（未来持久化预览审查结果）=
required_field_review_result（必需字段审查结果）=
forbidden_field_review_result（禁止字段审查结果）=
normalization_review_result（标准化审查结果）=
idempotency_review_result（幂等审查结果）=
audit_metadata_review_result（审计元数据审查结果）=
evidence_boundary_review_result（证据边界审查结果）=
clean_data_boundary_review_result（clean_data边界审查结果）=
delivery_gate_boundary_review_result（交付闸门边界审查结果）=
dry_run_test_only_boundary_review_result（dry-run/test-only边界审查结果）=
no_hook_no_io_review_result（无hook无IO审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BJ project documentation sync after review_queue dry-run schema alignment milestone
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
git commit -m "docs: add R7BI QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
