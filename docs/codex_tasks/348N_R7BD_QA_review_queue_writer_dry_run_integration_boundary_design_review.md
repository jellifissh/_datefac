# 348N-R7BD-QA review-queue writer dry-run integration boundary design review

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = QA-review-only
```

## Plain-language goal

R7BD created a docs-only design for the future dry-run integration boundary between the disabled adapter output and the test-only review_queue writer. R7BD-QA checks that the design is safe, accurate, and still does not implement integration.

In plain Chinese: 这一轮只审查设计文档。确认它只是设计“adapter 候选输出怎么安全传给 dry-run writer”，没有写代码、没有接生产、没有写库、没有导出，readiness_gates 仍然关闭。

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
git log --oneline -15
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
docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BA_QA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT_REVIEW.md
```

Review current slices read-only:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
```

Review related modules read-only if needed:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## QA checklist

Confirm:

```text
R7BD changed only the allowed docs design report.
The report is docs-only and does not implement integration.
The 大白话说明 is clear to a non-expert.
The proposed flow is clear: disabled adapter candidate output -> dry-run integration boundary -> test-only writer preview.
The integration boundary is designed as disabled by default.
Explicit test-only enable is required.
Only validated adapter candidate output is accepted.
Raw MinerU, raw Excel, raw parser output, full source_text, and direct user payloads are rejected.
Future boundary calls only the test-only in-memory writer contract.
Future boundary produces dry-run preview only.
No database write, file write, export, migration, clean_data write, or formal review_queue persistence is allowed.
readiness_gates remain CLOSED.
VERIFIED is not promoted to STRONG_EVIDENCE or clean_data.
non-VERIFIED rows remain review-bound.
Unresolved rows remain delivery-blocked.
Corrected rows remain re-audit-required unless a future explicit gate exists.
Idempotency and duplicate prevention are preserved from writer contract.
Adapter audit metadata passes through unchanged.
Only bounded evidence_preview is allowed; full source_text remains forbidden.
Schema mismatch and unsupported status combinations fail closed.
Future negative and positive tests are listed before implementation.
Rollback plan is conservative and local to the integration boundary slice.
No-hook and no-IO boundary is explicit.
Remaining risks are explicit.
Recommended next task is safe and does not jump directly to production enablement.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BD_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN_REVIEW.md
```

No other tracked files may change.

## Validation commands

```text
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
pytest tests/agent/test_review_queue_writer_contract_348n.py -q
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
R7BD recap
大白话说明审查
Integration boundary scope review
Proposed flow review
Accepted inputs review
Rejected inputs review
Dry-run writer call boundary review
Output envelope design review
Idempotency and duplicate prevention review
Audit metadata pass-through review
Evidence preview and source_text boundary review
clean_data safety boundary review
Delivery gate boundary review
Corrected row and re-audit policy review
Failure and fail-closed behavior review
Rollback plan review
Future tests before implementation review
No-hook and no-IO boundary review
Remaining risks review
Recommended next task review
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
integration_design_review_result（集成设计审查结果）=
plain_language_review_result（大白话说明审查结果）=
accepted_input_boundary_review_result（允许输入边界审查结果）=
rejected_input_boundary_review_result（拒绝输入边界审查结果）=
dry_run_boundary_review_result（dry-run边界审查结果）=
idempotency_review_result（幂等审查结果）=
audit_metadata_review_result（审计元数据审查结果）=
evidence_boundary_review_result（证据边界审查结果）=
clean_data_boundary_review_result（clean_data边界审查结果）=
delivery_gate_boundary_review_result（交付闸门边界审查结果）=
rollback_plan_review_result（回滚计划审查结果）=
future_test_plan_review_result（未来测试计划审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BE review-queue writer dry-run integration boundary test-only prototype
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BD_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN_REVIEW.md
git commit -m "docs: add R7BD QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
