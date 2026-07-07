# 348N-R7BL review_queue persistence contract test-only prototype

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-persistence-contract-prototype
```

## Plain-language goal

R7BK-QA confirmed the future persistence boundary design is conservative. R7BL may now add a test-only persistence contract prototype.

This is still not real persistence. It must live under `tests/agent`, produce only in-memory persistence candidates, and prove the safety contract before any real database/model/migration/repository work.

In plain Chinese: 这一步只在测试区做“模拟落库前的最后闸门”。它验证 future review_queue record preview 能不能安全变成“待落库候选”，但不真的写数据库、不建表、不接生产、不导出。

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
docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md
docs/agent/348N_R7BJ_QA_PROJECT_DOCUMENTATION_SYNC_REVIEW_AFTER_REVIEW_QUEUE_DRY_RUN_SCHEMA_ALIGNMENT_MILESTONE.md
docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BI_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
```

Review current test-only slices:

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

## Goal

Create a test-only review_queue persistence contract prototype for this chain:

```text
test-only schema alignment preview
-> test-only persistence boundary
-> in-memory review_queue persistence candidate batch
```

The prototype must validate the future persistence contract without real persistence.

## Allowed tracked files

Create exactly:

```text
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
```

Do not modify production code. Do not modify existing tests or fixtures unless absolutely required; prefer the new files above.

## Prototype requirements

The contract must be test-only and in-memory.

It must enforce:

```text
default disabled fail-closed
explicit test-only persistence flag required
accept only validated schema alignment preview payload
reject schema-alignment bypass
reject dry-run integration output passed directly into persistence contract
reject writer preview passed directly into persistence contract
reject adapter candidate output passed directly into persistence contract
reject raw extraction payloads
reject full source_text
reject clean_data write intent
reject delivery/export intent
reject production writer config
reject readiness_gates not CLOSED
reject missing required persistence fields
reject malformed idempotency_key
reject missing audit_hash
reject missing review_item_id
reject missing run_id
reject missing hash identity
reject unresolved record without blocked_delivery_reason
reject corrected record without re_audit_required
reject unbounded evidence text
reject user-provided direct persistence candidate
produce in-memory persistence_candidate_batch only
no DB write
no file/output write
no export
no migration
no production hook
no clean_data mutation
no readiness gate mutation
```

## Persistence candidate behavior

The output may be named something like:

```text
review_queue_persistence_candidate_batch
```

It must include only deterministic, safe, in-memory candidate rows.

Candidate rows may include:

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
record_payload_hash
```

Do not include real database IDs, migration IDs, connection strings, table names that imply implementation, production writer config, or test-only tokens/config objects.

## Required deterministic behavior

Prove:

```text
record_payload_hash is deterministic
idempotency_key is deterministic and stable across retries
candidate row ordering is deterministic
input mutation after call cannot mutate output
no wall-clock timestamp is required
if a created_at-like value exists, it must be fixed/deterministic test data only and clearly marked not production policy
```

## Transaction and rollback simulation

Because this is test-only and in-memory, do not implement database transactions.

You may simulate transaction rules with pure data:

```text
all valid rows -> candidate batch returned
any invalid row -> entire batch fails closed
no partial candidate batch returned on batch failure
duplicate idempotency_key within batch -> fail closed or deterministic duplicate result, but document the chosen behavior
```

Prefer fail-closed for duplicate idempotency_key unless a prior design explicitly says otherwise.

## Safety rules

The prototype must preserve:

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED rows remain review-bound
unresolved rows keep blocked_delivery_reason
corrected rows remain re-audit-required
persistence candidate does not trigger delivery
persistence candidate does not mutate clean_data
persistence candidate does not open readiness gates
bounded evidence_preview allowed
full source_text forbidden
raw MinerU/raw Excel/raw parser/raw LLM-VLM payloads forbidden
```

## Suggested fixture cases

Create a small curated fixture with:

```text
valid_schema_alignment_preview_mixed_records
valid_unresolved_blocked_delivery_record
valid_corrected_reaudit_required_record
invalid_default_disabled
invalid_missing_test_persistence_flag
invalid_schema_alignment_bypass
invalid_direct_dry_run_integration_output
invalid_direct_writer_preview_output
invalid_direct_adapter_candidate_output
invalid_missing_review_item_id
invalid_missing_run_id
invalid_missing_audit_hash
invalid_missing_idempotency_key
invalid_malformed_idempotency_key
invalid_missing_hash_identity
invalid_unresolved_without_blocked_delivery_reason
invalid_corrected_without_re_audit_required
invalid_duplicate_idempotency_key
invalid_full_source_text
invalid_unbounded_evidence_text
invalid_raw_mineru_output
invalid_raw_excel_workbook_data
invalid_raw_parser_payload
invalid_raw_llm_vlm_response
invalid_clean_data_write_intent
invalid_delivery_export_intent
invalid_production_writer_config
invalid_readiness_open
invalid_user_direct_persistence_candidate
```

Keep fixtures tiny. No real PDF, no DateFac Excel, no full MinerU output, no large text.

## Test requirements

Add tests proving:

```text
default disabled fails closed
explicit test-only persistence flag required
valid schema alignment preview returns in-memory persistence candidate batch
required persistence fields are present
future candidate excludes forbidden fields
future candidate excludes test-only token/config
missing review_item_id fails closed
missing run_id fails closed
missing audit_hash fails closed
missing idempotency_key fails closed
malformed idempotency_key fails closed
missing hash identity fails closed
unresolved without blocked_delivery_reason fails closed
corrected without re_audit_required fails closed
duplicate idempotency_key fails closed
schema-alignment bypass rejected
direct dry-run integration output rejected
direct writer preview output rejected
direct adapter candidate output rejected
full source_text rejected
unbounded evidence text rejected
raw extraction payloads rejected
clean_data intent rejected
delivery/export intent rejected
production writer config rejected
readiness OPEN rejected
user direct persistence candidate rejected
record_payload_hash deterministic
idempotency stable across retries
candidate row ordering deterministic
input mutation after call cannot mutate output
batch failure returns no partial candidate batch
VERIFIED does not become STRONG_EVIDENCE
VERIFIED does not write clean_data
non-VERIFIED remains review-bound
persistence candidate does not trigger delivery
no IO/no DB/no export/no production hook exists
```

## Strict boundaries

Forbidden:

```text
modify datefac_agent production code
add production persistence implementation
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

## Report requirements

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BK-QA recap
大白话说明
Test-only persistence contract scope
Contract design
Accepted input shape
Rejected bypass shapes
Persistence candidate batch shape
Required fields
Forbidden fields
Idempotency and duplicate prevention
Record payload hash strategy
Batch fail-closed behavior
Transaction and rollback simulation
Audit metadata retention
Evidence preview and source_text boundary
clean_data safety boundary
Delivery/export boundary
Readiness gates boundary
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
persistence_contract_result（持久化契约结果）=
persistence_candidate_batch_result（持久化候选批次结果）=
required_field_result（必需字段结果）=
forbidden_field_result（禁止字段结果）=
idempotency_result（幂等结果）=
duplicate_prevention_result（去重结果）=
record_payload_hash_result（记录payload哈希结果）=
batch_fail_closed_result（批次fail-closed结果）=
rollback_simulation_result（回滚模拟结果）=
audit_metadata_result（审计元数据结果）=
evidence_boundary_result（证据边界结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_export_boundary_result（交付导出边界结果）=
readiness_gate_boundary_result（就绪门边界结果）=
no_hook_no_io_result（无hook无IO结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BL-QA review_queue persistence contract test-only prototype review
```

## Validation commands

```text
python -m py_compile tests/agent/review_queue_persistence_contract_348n.py
python -m py_compile tests/agent/test_review_queue_persistence_contract_348n.py
python -m py_compile tests/agent/review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
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
git add tests/agent/review_queue_persistence_contract_348n.py
git add tests/agent/test_review_queue_persistence_contract_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
git add docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
git commit -m "test: add review queue persistence contract prototype"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
