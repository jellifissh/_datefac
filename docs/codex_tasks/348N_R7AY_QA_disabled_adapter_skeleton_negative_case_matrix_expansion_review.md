# 348N-R7AY-QA disabled adapter skeleton negative-case matrix expansion review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Plain-language goal

R7AY added a bigger set of bad-input tests for the disabled adapter skeleton. R7AY-QA checks that those tests are real, useful, and safe.

In plain Chinese: 这一轮不是做新功能，而是审查“坏输入撞门测试”是否覆盖够、是否没有偷偷接生产、是否仍然默认关门。

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
docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md
docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md
docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md
docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md
```

Review R7AY files:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
```

Review related files read-only:

```text
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
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
R7AY changed only the allowed files.
Negative matrix contains the claimed 29 negative cases or more.
Negative cases are meaningful and not duplicate-only.
Missing/wrong contract_version cases are covered.
Missing/empty run_id cases are covered.
Missing/invalid adapter_version or input_file_hashes cases are covered.
Unknown agreement_status and wrong type cases are covered.
Unknown reviewer_action and wrong type cases are covered.
review_status and reviewer_action mismatch is covered.
Incoming clean_data_eligible true is rejected.
Unsafe delivery state for unresolved non-VERIFIED rows is rejected.
Missing or non-CLOSED readiness_gates is rejected.
Unsafe external_calls metadata is rejected.
Parser-like, raw MinerU-like, and raw Excel-like shapes are rejected.
Nested source_text is rejected at row/evidence levels.
Oversized evidence_preview is rejected.
Required evidence_preview is enforced where appropriate.
Missing source_row_id, metric name, period, and candidate value cases are covered.
Mutable nested payload does not leak into output.
Valid curated boundary payload still passes.
Default disabled behavior remains fail-closed.
Explicit test-only enable is still required.
VERIFIED does not auto-enter clean_data.
non-VERIFIED stays review-bound.
Unresolved rows stay blocked from clean delivery.
review_item_id and audit_hash remain deterministic.
No production hook, no IO, no parser/model/extraction calls.
readiness_gates remain CLOSED.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md
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
R7AY recap
大白话说明
Allowed files review
Negative-case matrix review
Fixture review
Input contract negative-case review
Reviewer action negative-case review
Clean data and delivery negative-case review
Evidence preview negative-case review
Audit metadata negative-case review
Determinism and immutability review
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
negative_matrix_review_result（负例矩阵审查结果）=
fixture_review_result（fixture审查结果）=
input_contract_negative_review_result（输入契约负例审查结果）=
reviewer_action_negative_review_result（复核动作负例审查结果）=
clean_data_delivery_negative_review_result（clean_data与交付负例审查结果）=
evidence_preview_negative_review_result（证据预览负例审查结果）=
audit_metadata_negative_review_result（审计元数据负例审查结果）=
determinism_immutability_review_result（确定性与不可变性审查结果）=
no_hook_no_io_review_result（无hook无IO审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7AZ disabled adapter positive-path minimal contract consolidation
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md
git commit -m "docs: add R7AY QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
