# 348N-R7BD review-queue writer dry-run integration boundary design

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = docs-only-integration-boundary-design
```

## Plain-language goal

R7BC-QA confirmed the test-only in-memory writer contract is safe. R7BD is a design checkpoint before any integration code.

Do not implement the integration. Design the boundary between the disabled adapter candidate output and the test-only dry-run writer preview.

In plain Chinese: 这一步不是接生产，也不是写库。只是先画清楚“adapter 的候选结果以后怎么安全传给 dry-run writer”，中间需要哪些闸门、字段检查、失败策略、回滚策略。

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
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md
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

Review related modules read-only:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a docs-only design report for the future integration boundary between:

```text
disabled production-boundary adapter candidate output
↓
dry-run integration boundary
↓
test-only in-memory review_queue writer preview
```

The design must preserve all current safety gates and must not add implementation.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md
```

No other tracked files may change.

## Design requirements

The report must specify:

```text
1. The integration boundary is disabled by default.
2. It requires explicit test-only enable.
3. It accepts only adapter candidate output already validated by the disabled adapter.
4. It rejects raw MinerU, raw Excel, raw parser output, full source_text, and direct user payloads.
5. It calls only the test-only in-memory writer contract in future tests.
6. It must produce dry-run preview only.
7. It must not write database rows, files, exports, migrations, clean_data, or formal review_queue persistence.
8. readiness_gates remain CLOSED.
9. The integration boundary must not promote VERIFIED to STRONG_EVIDENCE or clean_data.
10. non-VERIFIED rows remain review-bound.
11. unresolved rows remain delivery-blocked.
12. corrected rows remain re-audit-required unless a future explicit gate exists.
13. idempotency and duplicate prevention must be preserved from writer contract.
14. adapter audit metadata must pass through unchanged.
15. bounded evidence_preview only; full source_text remains forbidden.
16. schema mismatch and unsupported status combinations fail closed.
17. future implementation must be preceded by negative tests and positive tests.
18. rollback means deleting or disabling only the integration boundary slice without affecting adapter or writer contract tests.
```

## Suggested future test cases

The design should list future tests but not implement them:

```text
default integration boundary disabled
explicit test-only enable required
valid adapter candidate output reaches dry-run writer preview
invalid raw payload rejected before writer call
adapter metadata passed through unchanged
writer dry-run preview returned unchanged except allowed envelope metadata
VERIFIED rows do not become clean_data
non-VERIFIED rows remain review-bound
unresolved rows retain blocked_delivery_reason
corrected rows retain re-audit requirement
readiness_gates OPEN rejected
full source_text rejected before writer call
idempotency key stable end-to-end
same input retry produces same dry-run preview
no IO/no DB/no export/no production hook
```

## Forbidden for this task

```text
Do not modify production code.
Do not modify tests.
Do not modify fixtures.
Do not add an integration implementation.
Do not add a writer implementation outside tests.
Do not add database models, repositories, migrations, or storage code.
Do not write output files.
Do not run MinerU/OCR/LLM/VLM or extraction.
Do not open readiness gates.
Do not use git add .
Do not use git add -A.
```

## Report requirements

The report must include a short 大白话说明 section.

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BC-QA recap
大白话说明
Integration boundary scope
Proposed flow
Accepted inputs
Rejected inputs
Dry-run writer call boundary
Output envelope design
Idempotency and duplicate prevention
Audit metadata pass-through
Evidence preview and source_text boundary
clean_data safety boundary
Delivery gate boundary
Corrected row and re-audit policy
Failure and fail-closed behavior
Rollback plan
Future tests before implementation
No-hook and no-IO boundary
Remaining risks
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
integration_design_result（集成设计结果）=
plain_language_result（大白话说明结果）=
accepted_input_boundary_result（允许输入边界结果）=
rejected_input_boundary_result（拒绝输入边界结果）=
dry_run_boundary_result（dry-run边界结果）=
idempotency_result（幂等结果）=
audit_metadata_result（审计元数据结果）=
evidence_boundary_result（证据边界结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_gate_boundary_result（交付闸门边界结果）=
rollback_plan_result（回滚计划结果）=
future_test_plan_result（未来测试计划结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BD-QA review-queue writer dry-run integration boundary design review
```

## Validation commands

This is docs-only, but still verify the current adapter and writer test slices remain green.

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

## Commit and push

If validation passes and only the allowed report is created, stage exactly:

```text
git add docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md
git commit -m "docs: add R7BD dry-run integration design"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
