# 348N-R7BB-QA disabled adapter review-queue persistence planning slice review

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = QA-review-only
```

## Plain-language goal

R7BB wrote a docs-only plan for future review_queue persistence. R7BB-QA checks that the plan is conservative, complete, and does not sneak in implementation.

In plain Chinese: 这一轮不写代码，只审查“以后怎么把 adapter 候选复核项安全存起来”的计划是否靠谱。重点确认现在仍然没有建表、没有写库、没有接生产、没有打开 readiness gates。

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
docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md
docs/agent/348N_R7BA_QA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT.md
docs/agent/348N_R7AZ_QA_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REVIEW.md
docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md
docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md
```

Review current adapter slice read-only:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
```

Review related files read-only if needed:

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
R7BB changed only the allowed docs report.
The report is docs-only and does not implement persistence.
The 大白话说明 is clear to a non-expert.
Future writer is planned as disabled by default.
Future writer accepts only adapter candidate output, not raw MinerU/raw Excel/raw parser/full source_text.
Future writer rejects readiness_gates not CLOSED unless a future explicit readiness task changes that.
Future writer does not write clean_data.
Future writer does not export delivery files.
Future writer persists only review-bound records, not auto-approved clean records.
Required audit metadata is listed: run_id, adapter_version, contract_version, input_file_hashes, review_item_id, audit_hash.
Bounded evidence_preview is allowed, full source_text is forbidden.
Deterministic idempotency key is planned.
Duplicate writes on retry are addressed.
blocked_delivery_reason is retained for unresolved rows.
Corrected rows remain re-audit-required unless a future explicit gate exists.
Schema mismatch fails closed.
Dry-run preview is required before future real write.
Rollback plan is included.
Tests-before-implementation plan is included.
Remaining risks are explicit.
Readiness gates remain CLOSED.
Recommended next task is safe and does not jump straight to production enablement.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, migrations, database models, writer implementations, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md
```

No other tracked files may change.

## Validation commands

```text
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
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
R7BB recap
大白话说明审查
Planning scope review
Candidate output persistence review
Forbidden inputs and writes review
Proposed review_queue record shape review
Idempotency and duplicate prevention review
Audit metadata retention review
Evidence preview and source_text boundary review
clean_data safety boundary review
Delivery gate boundary review
Corrected row and re-audit policy review
Dry-run preview review
Failure and fail-closed behavior review
Rollback plan review
Validation plan review
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
planning_review_result（计划审查结果）=
plain_language_review_result（大白话说明审查结果）=
record_shape_review_result（记录结构审查结果）=
idempotency_review_result（幂等设计审查结果）=
audit_metadata_review_result（审计元数据审查结果）=
evidence_boundary_review_result（证据边界审查结果）=
clean_data_boundary_review_result（clean_data边界审查结果）=
delivery_gate_boundary_review_result（交付闸门边界审查结果）=
dry_run_preview_review_result（dry-run预览审查结果）=
rollback_plan_review_result（回滚计划审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BC disabled adapter review-queue writer test-only contract prototype
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md
git commit -m "docs: add R7BB QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
