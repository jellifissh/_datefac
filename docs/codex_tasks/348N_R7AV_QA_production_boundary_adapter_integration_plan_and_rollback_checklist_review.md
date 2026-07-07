# 348N-R7AV-QA production-boundary adapter integration plan and rollback checklist review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Reason

R7AV completed a docs-only integration plan and rollback checklist. R7AV-QA must verify the plan is conservative, complete, rollback-ready, and still does not authorize implementation or open readiness gates.

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
docs/agent/348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST.md
docs/agent/348N_R7AU_QA_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REPORT.md
docs/agent/348N_R7AT_QA_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN_REVIEW.md
```

Inspect related files read-only:

```text
tests/agent/production_boundary_review_queue_adapter_contract_348n.py
tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
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
R7AV created docs only.
No code, tests, fixtures, outputs, dependencies, DateFac Excel, or MinerU artifacts were changed.
The integration phases are clear.
Allowed future files are explicit.
Forbidden future files and actions are explicit.
The entrypoint plan is disabled-by-default or otherwise gated.
The input contract plan only accepts validated boundary output.
Invalid or uncontrolled inputs are rejected by plan.
Review queue write plan keeps non-VERIFIED rows review-bound.
Clean data gate plan prevents automatic admission.
Delivery gate plan blocks unresolved rows.
Evidence preview plan stays bounded.
Audit metadata plan keeps run_id, adapter_version, input_file_hashes, stable ids, and hashes.
Failure handling is fail-closed.
Rollback checklist covers git, config, and data/output state.
Validation plan and acceptance criteria are sufficient before any implementation.
Readiness gates remain CLOSED.
The recommended next task is safe and does not jump directly to production.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md
```

## Validation commands

```text
python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py -q
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
R7AV recap
Planning review
Rollback checklist review
Input validation plan review
Review queue write plan review
Clean data gate plan review
Delivery gate plan review
Audit metadata plan review
Readiness gate plan review
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
planning_review_result（计划审查结果）=
rollback_checklist_review_result（回滚清单审查结果）=
input_validation_plan_review_result（输入校验计划审查结果）=
review_queue_write_plan_review_result（复核队列写入计划审查结果）=
clean_data_gate_plan_review_result（clean_data闸门计划审查结果）=
delivery_gate_plan_review_result（交付闸门计划审查结果）=
audit_metadata_plan_review_result（审计元数据计划审查结果）=
readiness_gate_plan_review_result（就绪门计划审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7AW test-only production-boundary adapter skeleton under disabled flag
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md
git commit -m "docs: add R7AV QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
