# 348N-R7BP review_queue persistence implementation planning slice docs-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = docs-only-implementation-planning
```

## Plain-language goal

R7BO-QA approved the documentation sync after the review_queue persistence contract milestone. R7BP plans a future implementation path for real review_queue persistence, but still does not implement it.

In plain Chinese: 这一轮只写“以后真落库该怎么分步骤做”的实施计划。不是现在建表，不是现在写 repository，不是现在接生产。目标是把未来从 test-only / in-memory persistence candidate batch 走到真实 review_queue persistence 的步骤、前置门槛、文件边界、测试顺序、回滚要求讲清楚，避免直接一脚踩进生产。

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
git log --oneline -55
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
docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md
docs/agent/348N_R7BO_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE.md
docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BN_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT.md
docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BK_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE.md
```

Review current test-only files read-only:

```text
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json
tests/agent/review_queue_writer_schema_alignment_contract_348n.py
tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
```

Review production-adjacent modules read-only only if needed:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a docs-only implementation planning report for future review_queue persistence.

The report must plan the safe path from:

```text
test-only persistence contract
-> in-memory persistence candidate batch
-> future fake repository / in-memory repository boundary
-> future database schema planning
-> future migration planning
-> future real repository implementation
-> future production gate review
```

Do not implement any of those steps in R7BP.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
```

No other tracked files may change.

## Required planning content

The planning report must cover:

```text
1. Current baseline after R7BO-QA.
2. Why real persistence is still blocked.
3. Proposed implementation sequence.
4. Future file/module boundaries.
5. Future database/schema planning questions.
6. Future repository interface shape.
7. Future fake/in-memory repository test stage.
8. Future migration planning stage.
9. Future real DB repository stage.
10. Required feature flags and environment allowlist.
11. Required idempotency and uniqueness strategy.
12. Required transaction and rollback strategy.
13. Required audit and payload hash strategy.
14. Required observability/logging constraints.
15. Required no-raw-payload leakage checks.
16. Required clean_data and delivery/export separation.
17. Required readiness gate review before any production hook.
18. Required QA sequence before real persistence can be considered.
19. Open questions.
20. Non-goals for R7BP.
```

## Current baseline to state

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> test-only persistence contract
-> in-memory persistence candidate batch
```

Also state:

```text
current persistence contract is test-only and in-memory
R7BL/R7BM/R7BN/R7BO are approved through QA
latest known validation: persistence targeted 76 passed; schema alignment 29 passed; dry-run integration 36 passed; writer contract 24 passed; adapter skeleton 75 passed; full tests/agent 480 passed
readiness_gates remain CLOSED
```

## Proposed future implementation sequence

The report must propose a conservative sequence. Use or refine this sequence:

```text
R7BQ: fake repository / in-memory repository boundary contract test-only
R7BR: fake repository negative-path and idempotency expansion test-only
R7BS: database schema and migration design docs-only
R7BT: schema/migration QA docs-only
R7BU: repository interface skeleton disabled-by-default, no DB connection
R7BV: repository skeleton QA
R7BW: local test database adapter prototype behind explicit test flag only
R7BX: local test database negative-path and rollback tests
R7BY: production gate review docs-only before any production hook
```

Do not start any of those tasks.

## Future file/module boundary planning

Discuss possible future locations without creating them:

```text
datefac_agent/review/review_queue_persistence_models.py
datefac_agent/review/review_queue_repository.py
datefac_agent/review/review_queue_persistence_service.py
datefac_agent/review/review_queue_persistence_policy.py
tests/agent/test_review_queue_persistence_repository_348n.py
tests/agent/test_review_queue_persistence_service_348n.py
```

Do not claim these files exist.

## Future data model planning

Plan candidate conceptual fields only. Do not create schema or migration.

The future persisted record may need fields like:

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
created_at
updated_at
retracted_at
retraction_reason
```

The report must say these are planning candidates only, not an implemented schema.

## Required uniqueness/idempotency planning

Plan uniqueness around:

```text
idempotency_key
record_payload_hash
review_item_id
run_id
source_file_hash / input_file_hashes
schema_version
contract_version
```

Plan that duplicate behavior must be fail-closed or deterministic no-op, but not silent duplicate insert.

## Required transaction/rollback planning

State future implementation must handle:

```text
single-row atomic write
batch atomic write or explicitly designed partial mode
no partial commit by default
rollback on any invalid row
retraction/disable strategy for bad persisted rows
no destructive delete as default recovery
write audit event with persistence attempt/result
idempotent retry after transient failure
```

## Required gate and flag planning

State future implementation must require:

```text
readiness_gates remain CLOSED until a separate gate review
explicit test-only persistence flag for test DB stages
separate production persistence flag only after production gate review
environment allowlist
no default production DB connection
no production writer config in test-only paths
no automatic activation from validated schema alignment preview
```

## Required safety rules

Preserve:

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

## Required non-goals

Explicitly state R7BP does not:

```text
modify production code
modify tests
modify fixtures
add repository/model/service code
add DB schema
add migration
add DB connection
add storage implementation
write output files
run extraction
run MinerU/OCR/LLM/VLM
open readiness gates
claim production persistence
claim production readiness
claim client readiness
claim formal export readiness
```

## Required remaining risks

Include:

```text
real database schema still not implemented
migration/rollback still not implemented
transaction behavior is still only planned
storage performance/concurrency not proven
real review UI integration not proven
production operational controls not proven
client/export readiness still not implied
```

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BO-QA recap
大白话说明
Current baseline
Why real persistence remains blocked
Implementation planning scope
Proposed future task sequence
Future file/module boundaries
Future data model planning
Future repository interface planning
Fake repository stage planning
Database schema and migration planning
Idempotency and uniqueness planning
Transaction and rollback planning
Audit and record hash planning
Feature flag and environment gate planning
Observability and leakage constraints
clean_data and delivery/export separation
Production gate review requirements
QA sequence before real persistence
Open questions
Non-goals
Remaining risks
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
implementation_planning_result（实施规划结果）=
current_baseline_result（当前基线结果）=
future_sequence_result（未来任务顺序结果）=
module_boundary_planning_result（模块边界规划结果）=
data_model_planning_result（数据模型规划结果）=
repository_interface_planning_result（repository接口规划结果）=
fake_repository_stage_planning_result（fake repository阶段规划结果）=
schema_migration_planning_result（schema/migration规划结果）=
idempotency_uniqueness_planning_result（幂等唯一性规划结果）=
transaction_rollback_planning_result（事务回滚规划结果）=
audit_hash_planning_result（审计哈希规划结果）=
feature_gate_planning_result（feature gate规划结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
production_gate_planning_result（生产gate规划结果）=
remaining_risk_result（剩余风险结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BP-QA review_queue persistence implementation planning slice review
```

## Validation commands

Docs-only, but still verify the current test-only chain remains green.

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

If validation passes and only the planning report is created, stage exactly:

```text
git add docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
git commit -m "docs: plan review queue persistence implementation"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
