# 348N-R7BH-QA review-queue writer dry-run integration schema alignment planning slice review

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = QA-review-only
```

## Plain-language goal

R7BH created a docs-only schema alignment plan for the dry-run integration chain. R7BH-QA checks that the field map is complete, conservative, and boundary-safe.

In plain Chinese: 这一轮只审查“字段对齐规划”。确认 adapter 输出、dry-run integration boundary、writer 预览、未来 review_queue 记录之间的字段关系讲清楚；同时确认 full source_text、raw MinerU、raw Excel、clean_data intent、production config 等禁止字段没有被放行。

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
docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md
docs/agent/348N_R7BG_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BG_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT.md
docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
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

## QA checklist

Confirm:

```text
R7BH changed only the allowed docs-only schema alignment plan.
The report does not implement schema changes.
The report does not modify tests, fixtures, production code, persistence, output, dependencies, or readiness gates.
The 大白话说明 is clear to a non-expert.
The current chain is accurate: disabled adapter candidate output -> dry-run integration boundary envelope -> test-only writer preview records -> future review_queue persistence shape.
The field inventory covers adapter output, integration envelope, writer preview, and future persistence shape.
The field map includes all required fields listed in R7BH task.
For each mapped field, the report states source layer, required/optional/derived/forbidden/test-only status, pass-through or normalization behavior, purpose, failure behavior, and whether future persistence may store it.
Required audit fields are clearly marked: run_id, adapter_version, contract_version, input_file_hashes, review_item_id, audit_hash.
Integration/writer version fields are handled conservatively: integration_boundary_version and writer_contract_version are deterministic and not production config.
Idempotency fields are deterministic and sufficient for duplicate prevention.
No wall-clock or non-deterministic timestamp is required for idempotency.
Evidence boundary is correct: bounded evidence_preview is allowed, full source_text is forbidden.
Forbidden fields are explicit: full source_text, raw MinerU output, raw Excel workbook data, raw parser payload, raw LLM/VLM response, clean_data write intent, formal delivery/export payload, production writer config, open readiness gate override, user-provided direct writer preview.
clean_data boundary is correct: VERIFIED does not imply STRONG_EVIDENCE or clean_data.
Delivery gate boundary is correct: unresolved rows keep blocked_delivery_reason.
Corrected row policy is correct: corrected rows remain re-audit-required.
Dry-run/test-only fields are not confused with future persistence fields.
Future persistence shape notes are conservative and do not claim actual persistence exists.
Schema mismatch fail-closed rules are explicit before writer call and after writer preview mismatch.
Future test plan is concrete and safe.
Remaining risks are explicit.
readiness_gates remain CLOSED.
Recommended next task is safe and does not jump directly to production enablement.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BH_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE_REVIEW.md
```

No other tracked files may change.

## Validation commands

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

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BH recap
大白话说明审查
Schema alignment scope review
Current chain field inventory review
Field map review
Required fields review
Optional and derived fields review
Forbidden fields review
Pass-through fields review
Normalization rules review
Idempotency and duplicate-prevention fields review
Audit metadata fields review
Evidence preview and source_text boundary review
clean_data safety boundary review
Delivery gate and blocked_delivery_reason fields review
Corrected row and re-audit fields review
Dry-run-only and test-only fields review
Schema mismatch fail-closed rules review
Future persistence shape notes review
Future test plan review
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
schema_alignment_plan_review_result（schema对齐规划审查结果）=
plain_language_review_result（大白话说明审查结果）=
field_inventory_review_result（字段盘点审查结果）=
field_map_review_result（字段映射审查结果）=
required_field_review_result（必需字段审查结果）=
forbidden_field_review_result（禁止字段审查结果）=
normalization_rule_review_result（标准化规则审查结果）=
idempotency_field_review_result（幂等字段审查结果）=
audit_metadata_field_review_result（审计元数据字段审查结果）=
evidence_boundary_review_result（证据边界审查结果）=
clean_data_boundary_review_result（clean_data边界审查结果）=
delivery_gate_boundary_review_result（交付闸门边界审查结果）=
dry_run_test_only_boundary_review_result（dry-run/test-only边界审查结果）=
future_test_plan_review_result（未来测试计划审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BI review-queue writer dry-run schema alignment test-only contract prototype
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BH_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE_REVIEW.md
git commit -m "docs: add R7BH QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
