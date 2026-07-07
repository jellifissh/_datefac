# 348N-R7AW-QA test-only production-boundary adapter skeleton under disabled flag review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Reason

R7AW completed a disabled-by-default production-boundary adapter skeleton. R7AW-QA must verify the skeleton is inert by default, has no production pipeline hook, performs no IO, preserves fail-closed behavior, keeps clean_data and readiness gates closed, and changed only the allowed files.

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
git log --oneline -12
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
docs/agent/348N_R7AW_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REPORT.md
docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md
docs/agent/348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST.md
docs/agent/348N_R7AU_QA_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REVIEW.md
```

Review R7AW files:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
```

Review related files read-only:

```text
tests/agent/production_boundary_review_queue_adapter_contract_348n.py
tests/agent/discrepancy_review_queue_integration_boundary_348n.py
tests/agent/discrepancy_review_queue_policy_348n.py
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/delivery/evidence_index_writer.py
```

## QA checklist

Confirm:

```text
R7AW changed only the allowed four files.
The adapter skeleton is disabled by default.
Disabled state fails closed.
There is no production pipeline hook.
There is no database write, file export, local output write, or external IO.
The adapter accepts only validated boundary output when explicitly enabled in tests.
Raw MinerU-like input is rejected.
Raw Excel-like input is rejected.
Full source_text input is rejected.
VERIFIED rows do not automatically enter clean_data.
non-VERIFIED rows map to review queue candidate items.
Unresolved rows map to blocked delivery candidate rows.
evidence_preview remains bounded.
run_id, adapter_version, input_file_hashes, review_item_id and audit_hash are preserved or deterministic.
Unsupported or invalid reviewer actions fail closed.
Readiness gates remain CLOSED.
No output, dependency, DateFac Excel, MinerU artifact, OCR, LLM, VLM, or extraction changes occurred.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md
```

## Validation commands

```text
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
pytest tests/agent -q
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
R7AW recap
Allowed files review
Disabled flag review
Input validation review
Review queue candidate review
Delivery gate review
Clean data guard review
Audit metadata review
No-hook and no-IO review
Boundary review
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
allowed_files_review_result（允许文件审查结果）=
skeleton_review_result（skeleton审查结果）=
disabled_flag_review_result（禁用开关审查结果）=
input_validation_review_result（输入校验审查结果）=
review_queue_candidate_review_result（复核队列候选审查结果）=
delivery_gate_review_result（交付闸门审查结果）=
clean_data_guard_review_result（clean_data防护审查结果）=
audit_metadata_review_result（审计元数据审查结果）=
no_hook_no_io_review_result（无hook无IO审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7AX disabled adapter skeleton contract hardening
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md
git commit -m "docs: add R7AW QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
