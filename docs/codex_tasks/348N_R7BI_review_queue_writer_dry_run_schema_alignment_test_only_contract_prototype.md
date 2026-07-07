# 348N-R7BI review-queue writer dry-run schema alignment test-only contract prototype

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-schema-alignment-contract-prototype
```

## Goal

R7BH-QA confirmed the docs-only schema alignment plan. R7BI may now add a test-only schema alignment contract prototype.

This remains a test-only boundary. It must not write a database row, create migrations, export files, connect to production, or open readiness gates.

Plain Chinese: 这一步只在测试区做字段闸门，检查 dry-run integration output 和 writer preview 的字段能不能安全映射成未来 review_queue 记录预览。仍然不写库、不建表、不导出、不接生产。

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
docs/agent/348N_R7BH_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BH_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_SCHEMA_ALIGNMENT_PLANNING_SLICE.md
docs/agent/348N_R7BG_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
```

Review current test-only slices:

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

## Allowed tracked files

Create exactly:

```text
tests/agent/review_queue_writer_schema_alignment_contract_348n.py
tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bi_schema_alignment_contract_fixture.json
docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
```

Do not modify production code. Prefer no changes to existing tests or fixtures.

## Prototype contract

Create a test-only in-memory contract that validates this chain:

```text
disabled adapter candidate output
-> dry-run integration boundary output
-> test-only writer dry-run preview
-> future review_queue record preview
```

The contract must be disabled by default and require explicit test-only enable. It must accept only a validated dry-run chain payload. It must reject untrusted or wrong-layer payloads, including adapter-only payloads that did not pass the boundary, direct writer-preview-shaped payloads, full source text, raw extraction payloads, clean_data intent, delivery/export intent, production writer config, and readiness gates not CLOSED.

It returns only an in-memory schema alignment preview. No IO is allowed.

## Field coverage

The prototype must classify at least these fields:

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

Use categories like:

```text
required_persistence_safe
required_audit
required_idempotency
required_delivery_blocking
required_reaudit
optional_bounded_evidence
normalized_derived
dry_run_only
test_only_only
forbidden
```

## Future review_queue preview rules

The future record preview may include safe fields such as ids, versions, hashes, metric identity, candidate value, review status, review reason, blocked delivery reason, re-audit flag, bounded evidence preview, source trace, and schema version.

It must not include full source text, raw extraction payloads, clean_data intent, delivery/export payload, production config, open readiness override, user-supplied direct writer preview, test-only token, or test-only writer config object.

`dry_run_only`, `integration_boundary_version`, and `validation_errors` may appear only in a deterministic test envelope unless the report explicitly explains why they would be future persisted fields.

## Safety rules

The contract must prove:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED rows remain review-bound
unresolved rows keep blocked_delivery_reason
corrected rows remain re-audit-required
bounded evidence_preview is allowed
full source text is forbidden
readiness_gates remain CLOSED
idempotency key is deterministic
normalization is deterministic
no wall-clock timestamp is required
input mutation after validation cannot mutate output
```

## Fixture cases

Create a small fixture covering valid mixed review records, unresolved blocked delivery, corrected re-audit required, missing required audit fields, missing/malformed idempotency key, non-deterministic timestamp-like fields, full source text, raw extraction payloads, clean_data intent, delivery/export intent, production config, readiness open, direct writer-preview payload, writer preview missing dry_run_only, and test-only config leaking into future persistence preview.

No real PDFs, DateFac Excel files, full MinerU output, or large text.

## Test requirements

Add tests for:

```text
default disabled fails closed
explicit test-only enable required
valid dry-run integration output produces schema alignment preview
required fields are classified
future preview keeps audit/idempotency/blocking fields
future preview excludes test-only config and forbidden fields
missing audit field fails closed
missing or malformed idempotency key fails closed
non-deterministic timestamp-like field rejected
full source text rejected
raw extraction payloads rejected
clean_data intent rejected
delivery/export intent rejected
production config rejected
readiness OPEN rejected
writer preview missing dry_run_only rejected
direct writer-preview payload rejected
normalization deterministic
idempotency stable across retries
input mutation after call cannot mutate output
VERIFIED does not become clean_data or STRONG_EVIDENCE
non-VERIFIED remains review-bound
unresolved retains blocked_delivery_reason
corrected retains re_audit_required
no IO/no DB/no export/no production hook exists
```

## Strict boundaries

Forbidden:

```text
modify datefac_agent production code
add production schema implementation
add database model
add repository class
add migrations
write output files
export delivery files
run MinerU/OCR/LLM/VLM or real extraction
open readiness gates
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED directly to clean_data
use git add .
use git add -A
```

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BH-QA recap
大白话说明
Test-only schema alignment scope
Contract design
Field classification
Future persistence preview shape
Required fields
Forbidden fields
Pass-through and normalization rules
Idempotency and duplicate prevention
Audit metadata retention
Evidence preview and source_text boundary
clean_data safety boundary
Delivery gate and blocked_delivery_reason fields
Corrected row and re-audit policy
Dry-run-only and test-only boundary
Failure and fail-closed behavior
No-hook and no-IO boundary
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
schema_alignment_contract_result（schema对齐契约结果）=
field_classification_result（字段分类结果）=
future_persistence_preview_result（未来持久化预览结果）=
required_field_result（必需字段结果）=
forbidden_field_result（禁止字段结果）=
normalization_result（标准化结果）=
idempotency_result（幂等结果）=
audit_metadata_result（审计元数据结果）=
evidence_boundary_result（证据边界结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_gate_boundary_result（交付闸门边界结果）=
dry_run_test_only_boundary_result（dry-run/test-only边界结果）=
no_hook_no_io_result（无hook无IO结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BI-QA review-queue writer dry-run schema alignment test-only contract prototype review
```

## Validation commands

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

If validation passes and only allowed files changed, stage exactly:

```text
git add tests/agent/review_queue_writer_schema_alignment_contract_348n.py
git add tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7bi_schema_alignment_contract_fixture.json
git add docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
git commit -m "test: add review queue schema alignment contract prototype"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
