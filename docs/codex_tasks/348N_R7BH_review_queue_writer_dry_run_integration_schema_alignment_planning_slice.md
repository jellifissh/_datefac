# 348N-R7BH review-queue writer dry-run integration schema alignment planning slice

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = docs-only-schema-alignment-planning
```

## Plain-language goal

R7BG-QA confirmed the dry-run integration boundary handoff checkpoint is accurate. R7BH is a planning slice for schema alignment.

Do not implement schema changes. Do not modify tests or fixtures. Plan how the schemas should line up across the current test-only chain:

```text
disabled adapter candidate output
↓
dry-run integration boundary envelope
↓
test-only writer dry-run preview records
↓
future review_queue persistence shape
```

In plain Chinese: 这一轮只做“字段对齐规划”。把 adapter 输出、integration boundary、writer dry-run 预览、未来 review_queue 记录之间的字段关系讲清楚，避免以后真正落库时字段乱接、漏审计字段、误把 clean_data 当 review_queue。现在仍然不写库、不建表、不导出、不接生产。

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
git log --oneline -25
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
docs/agent/348N_R7BG_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BG_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT.md
docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md
```

Review current slices read-only:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
```

Review related modules read-only if needed:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a docs-only schema alignment planning report for the review_queue dry-run integration chain.

The report must describe:

```text
1. Current field sources in adapter candidate output.
2. Current fields added or wrapped by the dry-run integration boundary.
3. Current writer dry-run preview record fields.
4. Future review_queue persistence fields.
5. Which fields are required, optional, derived, forbidden, or test-only.
6. Which fields must pass through unchanged.
7. Which fields must be normalized deterministically.
8. Which fields must never appear in review_queue persistence.
9. Which fields are needed for audit, idempotency, rollback, and delivery blocking.
10. Which schema mismatches must fail closed.
```

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md
```

No other tracked files may change.

## Required schema alignment content

The report must include a field map table or clear structured list covering at least these fields:

```text
run_id
adapter_version
contract_version
integration_boundary_version
writer_contract_version
input_file_hashes
source_file_hash
review_item_id
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
dry_run_only
readiness_gates
schema_version
validation_errors
```

For each field, state:

```text
source layer
required/optional/derived/forbidden/test-only
pass-through or normalized
why it exists
failure behavior if missing or malformed
whether future persistence may store it
```

## Must-stay-forbidden fields

Explicitly document that these must not pass into review_queue persistence or dry-run preview as stored full content:

```text
full source_text
raw MinerU output
raw Excel workbook data
raw parser payload
raw LLM/VLM response
clean_data write intent
formal delivery/export payload
production writer config
open readiness gate override
user-provided direct writer preview
```

## Required safety rules

Document:

```text
VERIFIED must not imply STRONG_EVIDENCE.
VERIFIED must not auto-write clean_data.
non-VERIFIED stays review-bound.
Unresolved rows keep blocked_delivery_reason.
Corrected rows remain re-audit-required.
Dry-run output remains in-memory and dry_run_only.
Idempotency keys must be deterministic.
Audit metadata must pass through unchanged.
Bounded evidence_preview is allowed; full source_text is forbidden.
Schema mismatch fails closed before writer call when possible.
Writer preview mismatch fails closed after writer call.
readiness_gates remain CLOSED.
```

## Future test plan requirements

List future tests for a later implementation task, but do not implement them:

```text
field map required-fields positive path
missing required audit field fails closed
malformed idempotency key fails closed
non-deterministic timestamp rejected
full source_text rejected at all layers
raw MinerU/raw Excel/raw parser rejected at schema boundary
clean_data intent rejected at schema boundary
readiness OPEN rejected at schema boundary
writer preview missing dry_run_only rejected
writer preview field mutation rejected
future persistence shape excludes test-only config fields
future persistence shape keeps audit/idempotency/blocking fields
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
Do not use git add .
Do not use git add -A.
```

## Report requirements

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BG-QA recap
大白话说明
Schema alignment scope
Current chain field inventory
Field map
Required fields
Optional and derived fields
Forbidden fields
Pass-through fields
Normalization rules
Idempotency and duplicate-prevention fields
Audit metadata fields
Evidence preview and source_text boundary
clean_data safety boundary
Delivery gate and blocked_delivery_reason fields
Corrected row and re-audit fields
Dry-run-only and test-only fields
Schema mismatch fail-closed rules
Future persistence shape notes
Future test plan
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
schema_alignment_plan_result（schema对齐规划结果）=
plain_language_result（大白话说明结果）=
field_inventory_result（字段盘点结果）=
field_map_result（字段映射结果）=
required_field_result（必需字段结果）=
forbidden_field_result（禁止字段结果）=
normalization_rule_result（标准化规则结果）=
idempotency_field_result（幂等字段结果）=
audit_metadata_field_result（审计元数据字段结果）=
evidence_boundary_result（证据边界结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_gate_boundary_result（交付闸门边界结果）=
dry_run_test_only_boundary_result（dry-run/test-only边界结果）=
future_test_plan_result（未来测试计划结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BH-QA review-queue writer dry-run integration schema alignment planning slice review
```

## Validation commands

This is docs-only, but still verify the current test-only chain remains green.

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

## Commit and push

If validation passes and only the allowed report is created, stage exactly:

```text
git add docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md
git commit -m "docs: add R7BH schema alignment plan"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
