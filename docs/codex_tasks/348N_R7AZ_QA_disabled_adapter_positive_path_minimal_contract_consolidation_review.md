# 348N-R7AZ-QA disabled adapter positive-path minimal contract consolidation review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Plain-language goal

R7AZ added the smallest good-input cases for the disabled adapter skeleton. R7AZ-QA checks that those good-input cases are valid and conservative.

In plain Chinese: 前面确认“坏数据进不来”。R7AZ 确认“真正合规的最小好数据，在测试开关打开时，可以生成安全候选输出”。这一轮 QA 就是检查这个结论靠不靠谱，同时确认它仍然没有接生产、没有写库、没有导出、没有打开 readiness gates。

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
docs/agent/348N_R7AZ_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REPORT.md
docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md
docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md
docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md
```

Review R7AZ files:

```text
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
```

Review related files read-only:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
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
R7AZ changed only the allowed files.
R7AZ did not modify adapter code unless the report clearly justifies it.
The new positive fixture is small and test-only.
The positive fixture does not include raw MinerU output, raw Excel rows, full source text, real PDF data, output files, or large data.
Minimal valid VERIFIED payload is covered.
Minimal valid DISAGREED payload is covered.
Minimal valid AMBIGUOUS payload is covered.
Minimal valid MISSING_EVIDENCE payload is covered.
Minimal valid UNVERIFIED payload is covered.
Corrected-but-re-audit-required behavior is covered.
Mixed VERIFIED plus non-VERIFIED payload is covered.
Bounded evidence_preview and required audit metadata are covered.
Default disabled behavior still fails closed.
Explicit test-only enable is still required.
Minimal valid payloads pass only under explicit test enable.
Outputs are in-memory only.
Candidate output schema is stable.
VERIFIED rows are safe and do not auto-enter clean_data.
non-VERIFIED rows map to review_queue candidate items.
Unresolved rows map to blocked delivery candidate rows.
Corrected rows do not become clean_data without explicit future gate.
run_id, adapter_version, input_file_hashes, and contract_version are retained.
review_item_id and audit_hash remain deterministic.
Candidate output ordering is deterministic.
Output does not share mutable input references.
R7AY negative protections remain intact.
No production hook, no IO, no parser/model/extraction call exists.
readiness_gates remain CLOSED.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7AZ_QA_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REVIEW.md
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
R7AZ recap
大白话说明
Allowed files review
Positive-path contract review
Fixture review
Minimal valid payload review
Candidate output schema review
Review queue candidate review
Clean data guard review
Delivery gate review
Audit metadata review
Determinism and immutability review
Negative protections retained review
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
positive_contract_review_result（正向契约审查结果）=
fixture_review_result（fixture审查结果）=
minimal_valid_payload_review_result（最小合法输入审查结果）=
candidate_output_schema_review_result（候选输出schema审查结果）=
review_queue_candidate_review_result（复核队列候选审查结果）=
clean_data_guard_review_result（clean_data防护审查结果）=
delivery_gate_review_result（交付闸门审查结果）=
audit_metadata_review_result（审计元数据审查结果）=
determinism_immutability_review_result（确定性与不可变性审查结果）=
negative_protection_retained_review_result（负例防护保留审查结果）=
no_hook_no_io_review_result（无hook无IO审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BA disabled adapter contract summary and handoff checkpoint
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7AZ_QA_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REVIEW.md
git commit -m "docs: add R7AZ QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
