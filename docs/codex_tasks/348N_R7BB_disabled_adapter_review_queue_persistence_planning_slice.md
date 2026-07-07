# 348N-R7BB disabled adapter review-queue persistence planning slice

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = docs-only-planning-slice
```

## Plain-language goal

R7BA-QA confirmed the disabled adapter phase is summarized correctly. R7BB is the next planning slice: decide how the adapter candidate output could later become persisted review_queue records, without implementing persistence yet.

In plain Chinese: 这一步不是写入数据库，也不是接生产。只是先把“以后如果要把候选复核项真正存起来，该怎么存、哪些字段必须有、哪些情况必须拒绝、怎么回滚”写清楚。

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
docs/agent/348N_R7BA_QA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT.md
docs/agent/348N_R7AZ_QA_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REVIEW.md
docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md
docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md
docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md
```

Review current adapter slice read-only:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
```

Review related persistence-ish modules read-only if they exist:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a docs-only planning report for a future review_queue persistence layer. Do not implement it.

The plan must describe:

```text
what candidate output from the disabled adapter would be allowed to persist later
what fields a persisted review_queue record would require
what must never be persisted
how idempotency should work
how audit metadata should be retained
how duplicate writes should be prevented
how clean_data must remain protected
how delivery must remain blocked for unresolved rows
how the future writer should be disabled by default
how rollback should work
what tests should come before implementation
```

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md
```

No other tracked files may change.

## Planning requirements

The report must include a conservative future design for review_queue persistence.

Cover at least:

```text
1. Future writer must be disabled by default.
2. Future writer must accept only adapter candidate output, not raw MinerU, raw Excel, raw parser, or full source_text.
3. Future writer must reject any candidate with readiness_gates not CLOSED until an explicit future readiness task says otherwise.
4. Future writer must not write clean_data.
5. Future writer must not export delivery files.
6. Future writer must persist only review-bound records, not auto-approved clean records.
7. Future writer must keep run_id, adapter_version, contract_version, input_file_hashes, review_item_id, audit_hash.
8. Future writer must store bounded evidence_preview only, never full source_text.
9. Future writer must enforce deterministic idempotency keys.
10. Future writer must prevent duplicate rows on retry.
11. Future writer must record blocked_delivery_reason for unresolved rows.
12. Future writer must keep corrected rows re-audit-required unless a future explicit gate exists.
13. Future writer must fail closed on schema mismatch.
14. Future writer must produce a dry-run preview before any real write.
15. Future writer must have a rollback plan.
16. Future writer must have tests before implementation.
```

## Suggested future record fields

Discuss a minimal persisted review_queue record shape. Include but do not implement fields like:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
contract_version
audit_hash
metric_name
period
candidate_value
agreement_status
review_status
reviewer_action
review_reason
blocked_delivery_reason
evidence_preview
created_at
source_trace
idempotency_key
```

Explain which fields are required, which are optional, and which are forbidden.

## Forbidden for this task

```text
Do not modify production code.
Do not modify tests.
Do not modify fixtures.
Do not add a database model.
Do not add a repository class.
Do not add a writer implementation.
Do not add migrations.
Do not write output files.
Do not run MinerU/OCR/LLM/VLM or extraction.
Do not open readiness gates.
Do not promote VERIFIED to STRONG_EVIDENCE.
Do not promote VERIFIED directly to clean_data.
Do not use git add .
Do not use git add -A.
```

## Report sections

The report must include a short 大白话说明 section.

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BA-QA recap
大白话说明
Persistence planning scope
Candidate output allowed for future persistence
Forbidden inputs and forbidden writes
Proposed review_queue record shape
Idempotency and duplicate prevention
Audit metadata retention
Evidence preview and source_text boundary
clean_data safety boundary
Delivery gate boundary
Corrected row and re-audit policy
Dry-run preview requirement
Failure and fail-closed behavior
Rollback plan
Validation plan before future implementation
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
planning_result（计划结果）=
plain_language_result（大白话说明结果）=
record_shape_result（记录结构结果）=
idempotency_result（幂等设计结果）=
audit_metadata_result（审计元数据结果）=
evidence_boundary_result（证据边界结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_gate_boundary_result（交付闸门边界结果）=
dry_run_preview_result（dry-run预览结果）=
rollback_plan_result（回滚计划结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BB-QA disabled adapter review-queue persistence planning slice review
```

## Validation commands

Run lightweight validation only. This is docs-only, but still verify current adapter tests remain green.

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

## Commit and push

If validation passes and only the allowed report is created, stage exactly:

```text
git add docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md
git commit -m "docs: add R7BB review queue persistence plan"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
