# 348N-R7BS database schema and migration design docs-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = docs-only-schema-migration-design
```

## Plain-language goal

R7BR-QA approved the test-only fake repository negative-path and idempotency expansion. R7BS designs the future database schema and migration strategy for review_queue persistence, but still does not implement any database code, migration file, repository, service, or production hook.

In plain Chinese: 这一轮只设计“以后如果真要落库，表结构和迁移应该怎么规划”。不是现在建表，不是现在写 migration，不是现在写 repository，不是现在连数据库。目标是把字段、索引、唯一约束、幂等、审计、回滚、软删除/撤回、迁移顺序和风险讲清楚，为后续真正实现前再做一次设计评审。

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
git log --oneline -70
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
docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md
docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md
docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
```

Review current test-only files read-only:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
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

Create a docs-only schema and migration design report for future review_queue persistence.

The design must cover the future database persistence layer without creating it. It must be conservative and must keep production readiness gates closed.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
```

No other tracked files may change.

## Required design content

The design report must cover:

```text
1. Current baseline after R7BR-QA.
2. Why this is still docs-only and not implementation.
3. Proposed conceptual table(s).
4. Proposed conceptual columns.
5. Required identity fields and hash fields.
6. Required review status/action fields.
7. Required evidence preview/source trace fields.
8. Required audit metadata fields.
9. Required idempotency and uniqueness constraints.
10. Required indexes and query patterns.
11. Required check constraints / enum constraints.
12. Required raw-payload exclusion constraints.
13. Required transaction and batch atomicity rules.
14. Required migration order.
15. Required rollback/forward-fix strategy.
16. Required backfill strategy, if any.
17. Required retention/retraction strategy.
18. Required environment and feature-flag gates.
19. Required readiness gate review before production hook.
20. Open questions and non-goals.
```

## Current baseline to state

```text
adapter candidate output
-> test-only dry-run integration boundary
-> test-only writer dry-run preview
-> test-only schema alignment contract
-> test-only persistence contract
-> in-memory persistence candidate batch
-> test-only fake repository / in-memory repository boundary
-> fake repository negative-path and idempotency expansion
```

Also state:

```text
current persistence stack is still test-only and in-memory
R7BR-QA approved targeted fake repository tests at 63 passed
latest known full tests/agent = 543 passed
readiness_gates remain CLOSED
```

## Conceptual schema planning

Plan a future table conceptually. Do not create a migration.

Suggested conceptual table name:

```text
review_queue_items
```

Possible conceptual columns to discuss:

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

The report must explicitly say these are conceptual fields only and not an implemented schema.

## Required uniqueness/idempotency design

Discuss candidate constraints such as:

```text
unique(idempotency_key)
unique(review_item_id)
unique(run_id, source_file_hash, metric_name, period, schema_version, contract_version)
record_payload_hash consistency with idempotency_key
no silent duplicate insert
same idempotency_key + same payload = deterministic no-op or same receipt policy
same idempotency_key + different payload = conflict / fail closed
same review_item_id + different idempotency_key = conflict / fail closed
```

Do not decide irreversible production behavior without listing it as a design question if uncertain.

## Required index and query planning

Discuss future query patterns and likely indexes:

```text
lookup by review_item_id
lookup by idempotency_key
lookup by run_id
lookup by source_file_hash
lookup by review_status
lookup by agreement_status
lookup by re_audit_required
lookup by created_at / updated_at
review queue UI pagination
audit/debug lookup by record_payload_hash
```

## Required constraints and enum planning

Plan allowed values for fields such as:

```text
agreement_status
review_status
reviewer_action
blocked_delivery_reason
created_by_system
```

State that constraints must prevent clean_data/delivery/export readiness from being implied by stored review_queue records.

## Required raw-payload exclusion planning

State future schema/repository validation must reject and never store:

```text
full source_text
raw MinerU payload
raw Excel payload
raw parser payload
raw OCR payload
raw LLM/VLM response
DB DSN / connection string
output path / file path config
production writer config
readiness override
clean_data intent
delivery/export intent
```

Only bounded evidence_preview/source_trace metadata may be stored.

## Required transaction and rollback planning

Discuss:

```text
single-row atomic insert/update
batch atomic write by default
no partial success by default
rollback on any invalid row
idempotent retry after transient failure
audit event for persistence attempt and result
soft retraction over destructive delete by default
forward migration over destructive rollback when data exists
manual recovery path for bad rows
```

## Required migration planning

Plan a conservative migration sequence:

```text
schema design review
migration design QA
disabled repository skeleton
local test DB prototype behind explicit test flag
negative-path / rollback tests against local test DB
production gate review docs-only
only then consider production hook
```

Do not create actual migration files.

## Required feature gate planning

State future implementation must require:

```text
readiness_gates remain CLOSED until separate production gate review
explicit test-only DB flag for local test DB stages
separate production persistence flag only after production gate review
environment allowlist
no default production DB connection
no production writer config in test-only paths
no automatic activation from validated schema alignment preview
```

## Safety rules to preserve

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

Explicitly state R7BS does not:

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
schema is only conceptual
migration is only planned
no real database behavior is proven
no local test DB adapter exists yet
transaction/rollback behavior is not implemented
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
R7BR-QA recap
大白话说明
Current baseline
Docs-only scope
Conceptual table design
Conceptual column design
Identity and hash field design
Review status/action field design
Evidence preview and source trace design
Audit metadata design
Idempotency and uniqueness design
Index and query pattern design
Constraint and enum design
Raw-payload exclusion design
Transaction and batch atomicity design
Migration order design
Rollback and forward-fix design
Retention and retraction design
Feature gate and environment planning
Readiness gate requirements
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
schema_design_result（schema设计结果）=
migration_design_result（migration设计结果）=
conceptual_table_result（概念表设计结果）=
conceptual_column_result（概念字段设计结果）=
identity_hash_design_result（身份/哈希设计结果）=
status_action_design_result（状态/动作设计结果）=
evidence_trace_design_result（证据/trace设计结果）=
audit_metadata_design_result（审计元数据设计结果）=
idempotency_uniqueness_design_result（幂等唯一性设计结果）=
index_query_design_result（索引查询设计结果）=
constraint_enum_design_result（约束枚举设计结果）=
raw_payload_exclusion_design_result（原始payload排除设计结果）=
transaction_atomicity_design_result（事务原子性设计结果）=
rollback_forward_fix_design_result（回滚/前向修复设计结果）=
feature_gate_design_result（feature gate设计结果）=
readiness_gate_result（就绪门结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BS-QA database schema and migration design review
```

## Validation commands

Docs-only, but still verify the current test-only chain remains green.

```text
python -m py_compile tests/agent/review_queue_fake_repository_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_fake_repository_boundary_348n.py
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
python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
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

If validation passes and only the design report is created, stage exactly:

```text
git add docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
git commit -m "docs: design review queue schema migration"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
