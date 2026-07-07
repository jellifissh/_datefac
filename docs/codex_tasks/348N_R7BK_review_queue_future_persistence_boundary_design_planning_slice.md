# 348N-R7BK review_queue future persistence boundary design planning slice

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = docs-only-design-planning
```

## Plain-language goal

R7BJ-QA confirmed the project documentation sync is accurate and not overclaiming production readiness. R7BK is the next planning slice: design the future persistence boundary for review_queue, without implementing it.

In plain Chinese: 这一轮只设计“以后怎么安全落库”，不是现在落库。目标是把 test-only dry-run preview 未来变成真实 review_queue persistence 之前，需要哪些边界、字段、幂等、审计、回滚、失败处理、gate 审批都讲清楚。现在仍然不建表、不写库、不接生产。

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
docs/agent/348N_R7BJ_QA_PROJECT_DOCUMENTATION_SYNC_REVIEW_AFTER_REVIEW_QUEUE_DRY_RUN_SCHEMA_ALIGNMENT_MILESTONE.md
docs/agent/348N_R7BJ_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_DRY_RUN_SCHEMA_ALIGNMENT_MILESTONE.md
docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
docs/agent/348N_R7BH_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
```

Review current implementation/test-only slices read-only:

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

Review related production-adjacent modules read-only if useful:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a docs-only design planning report for future review_queue persistence boundary.

The report must design, not implement, how a future persistence slice should move from:

```text
test-only schema alignment preview
-> future persistence boundary
-> real review_queue storage candidate
```

The design must preserve all safety rules and state clearly that persistence is not implemented in R7BK.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md
```

No other tracked files may change.

## Required design content

The report must cover:

```text
1. Future persistence boundary purpose.
2. Where the boundary would sit in the chain.
3. What must be true before persistence is allowed.
4. Which fields are allowed to persist.
5. Which fields are forbidden forever or until separate design.
6. Idempotency key strategy.
7. Audit hash and metadata strategy.
8. Duplicate prevention strategy.
9. Transaction and rollback expectations.
10. Failure behavior and fail-closed rules.
11. Review status lifecycle.
12. Blocked delivery behavior.
13. Corrected row re-audit behavior.
14. Evidence preview and source_text boundary.
15. Readiness gate conditions.
16. Test plan for a later implementation slice.
17. Migration and schema design questions to answer later.
18. Rollback and recovery risks.
```

## Future persistence boundary must require

Document that a future persistence implementation must require all of these before any write:

```text
validated schema alignment preview
readiness_gates still CLOSED unless separately approved
explicit persistence test flag in early implementation
no production writer config unless a separate production gate review exists
dry-run contract version known
schema version known
review_item_id present
run_id present
source_file_hash or input_file_hashes present
audit_hash present
idempotency_key present and deterministic
review_status present
review_reason present
blocked_delivery_reason present for unresolved/blocked records
re_audit_required present for corrected records
bounded evidence_preview only
no full source_text
no raw extraction payload
no clean_data write intent
no delivery/export intent
```

## Allowed future persistence fields

Discuss the future review_queue row shape. It may include fields like:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
contract_version
writer_contract_version
schema_version
audit_hash
idempotency_key
metric_name
period
candidate_value
normalized_candidate_value
agreement_status
review_status
review_reason
reviewer_action
blocked_delivery_reason
re_audit_required
evidence_preview
source_trace
created_by_system
created_at or deterministic batch timestamp policy, only if separately designed
record_payload_hash
```

Do not claim these already exist in a database.

## Forbidden persistence content

Explicitly forbid:

```text
full source_text
raw MinerU output
raw Excel workbook data
raw parser payload
raw LLM/VLM response
clean_data write intent
formal delivery/export payload
production writer config
test-only enable token
test-only writer config object
user-provided direct writer preview
unbounded evidence text
unapproved readiness gate override
```

## Required safety rules

Preserve:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED rows remain review-bound
unresolved rows keep blocked_delivery_reason
corrected rows remain re-audit-required
review_queue persistence must not trigger delivery
review_queue persistence must not mutate clean_data
review_queue persistence must not open readiness gates
bounded evidence_preview allowed
full source_text forbidden
```

## Later implementation test plan

List tests for a future implementation task, but do not implement them:

```text
persistence disabled by default
explicit persistence test flag required
valid schema alignment preview creates persistence candidate only
missing review_item_id fails closed
missing audit_hash fails closed
missing idempotency_key fails closed
malformed idempotency_key fails closed
duplicate idempotency_key does not create duplicate record
schema mismatch fails before write
forbidden fields fail before write
full source_text rejected before write
raw extraction payload rejected before write
clean_data intent rejected before write
delivery/export intent rejected before write
unresolved without blocked_delivery_reason rejected
corrected without re_audit_required rejected
VERIFIED does not write clean_data
write failure rolls back all records
partial batch failure produces no partial committed state unless separately designed
record_payload_hash stable across equivalent input
no IO beyond explicitly mocked test persistence boundary
```

## Forbidden for this task

```text
Do not modify production code.
Do not modify tests.
Do not modify fixtures.
Do not add implementation.
Do not add database models, repositories, migrations, or storage code.
Do not write output files.
Do not run MinerU/OCR/LLM/VLM or extraction.
Do not open readiness gates.
Do not claim production persistence exists.
Do not claim production readiness.
Do not claim client readiness.
Do not claim formal export readiness.
Do not use git add .
Do not use git add -A.
```

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BJ-QA recap
大白话说明
Future persistence boundary scope
Current chain position
Non-goals
Required preconditions before any write
Future review_queue row shape planning
Allowed fields
Forbidden fields
Idempotency strategy
Audit metadata strategy
Duplicate prevention strategy
Transaction and rollback expectations
Failure and fail-closed behavior
Review status lifecycle
Blocked delivery behavior
Corrected row re-audit behavior
Evidence preview and source_text boundary
clean_data safety boundary
Delivery/export boundary
Readiness gates and approval boundary
Future implementation test plan
Migration and schema questions for later
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
future_persistence_design_result（未来持久化设计结果）=
plain_language_result（大白话说明结果）=
boundary_scope_result（边界范围结果）=
precondition_result（写入前置条件结果）=
future_row_shape_result（未来行形状结果）=
allowed_field_result（允许字段结果）=
forbidden_field_result（禁止字段结果）=
idempotency_strategy_result（幂等策略结果）=
audit_metadata_strategy_result（审计元数据策略结果）=
duplicate_prevention_result（去重策略结果）=
rollback_strategy_result（回滚策略结果）=
fail_closed_strategy_result（fail-closed策略结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_export_boundary_result（交付导出边界结果）=
readiness_gate_boundary_result（就绪门边界结果）=
future_test_plan_result（未来测试计划结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BK-QA review_queue future persistence boundary design planning slice review
```

## Validation commands

Docs-only, but still verify the current test-only chain remains green.

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

## Commit and push

If validation passes and only the allowed report is created, stage exactly:

```text
git add docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md
git commit -m "docs: add R7BK future persistence boundary design"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
