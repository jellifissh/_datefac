# 348N-R7BF-QA review-queue writer dry-run integration negative-path test-only coverage review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Plain-language goal

R7BF hardened the test-only dry-run integration boundary with negative-path coverage. R7BF-QA checks that the hardening is correct, conservative, and still test-only.

In plain Chinese: 这一轮只审查 R7BF 的“防坏输入、防伪装 writer preview、防 malformed payload、防缺 token/错 token”是否靠谱。重点确认它仍然只是测试防线，没有写库、没有导出、没有接生产、没有打开 readiness gates。

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
git log --oneline -20
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
docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md
docs/agent/348N_R7BD_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN_REVIEW.md
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
```

Review R7BF files:

```text
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md
```

Review related slices read-only:

```text
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
```

## QA checklist

Confirm:

```text
R7BF changed only the intended R7BF files.
The integration boundary remains under tests/agent only.
No production code was modified.
No database model, repository class, migration, output writer, export path, or production hook was added.
Missing test-only token is rejected.
Invalid test-only token is rejected.
Disabled malformed path fails closed.
Only exact test-only writer config is accepted.
Unsafe or production-like writer preview is blocked.
Direct writer-preview shaped input cannot bypass adapter candidate validation.
Empty payload is rejected.
Minimal malformed payload is rejected.
Raw MinerU-like, Excel-like, parser-like, direct-user, source_text, readiness-open, clean_data-intent, and schema-mismatch cases remain rejected.
Valid R7BE dry-run integration cases still pass.
Writer preview hardening does not break conservative positive path behavior.
Dry-run result remains dry_run_only and in-memory.
review_item_id, audit_hash, run_id, adapter_version, contract_version, input_file_hashes, and idempotency keys remain preserved.
non-VERIFIED rows remain review-bound.
Unresolved rows retain blocked_delivery_reason.
Corrected rows retain re-audit requirement.
VERIFIED rows do not become clean_data.
No IO, DB, export, parser, model, MinerU, OCR, VLM, or production call exists.
readiness_gates remain CLOSED.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
```

No other tracked files may change.

## Validation commands

```text
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
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
R7BF recap
大白话说明审查
Negative-path coverage review
Writer-preview hardening review
Test-only token and config review
Malformed payload review
Fixture review
Positive path regression review
Dry-run output boundary review
Idempotency and metadata review
clean_data safety boundary review
Delivery gate boundary review
No-hook and no-IO boundary review
Boundary review
Validation outputs
Limitations
Decision
Data Result / 数据结果
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
negative_path_review_result（负路径审查结果）=
writer_preview_hardening_review_result（writer预览加固审查结果）=
test_only_token_review_result（test-only token审查结果）=
malformed_payload_review_result（畸形payload审查结果）=
fixture_review_result（fixture审查结果）=
positive_path_regression_review_result（正路径回归审查结果）=
dry_run_boundary_review_result（dry-run边界审查结果）=
idempotency_metadata_review_result（幂等与元数据审查结果）=
clean_data_boundary_review_result（clean_data边界审查结果）=
delivery_gate_boundary_review_result（交付闸门边界审查结果）=
no_hook_no_io_review_result（无hook无IO审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BG review-queue writer dry-run integration boundary handoff checkpoint
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
git commit -m "docs: add R7BF QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
