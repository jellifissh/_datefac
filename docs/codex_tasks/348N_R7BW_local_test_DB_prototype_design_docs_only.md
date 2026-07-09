# 348N-R7BW local test DB prototype design docs-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = docs-only-local-test-db-design
```

## Plain-language goal

R7BV-QA approved the repository skeleton QA hardening. R7BW designs the next possible local test database prototype, but still does not implement any database code, migration, repository adapter, DB connection, or persistence behavior.

In plain Chinese: 这一轮只写设计文档，规划“以后如果要做本地测试数据库原型，应该怎么做、怎么开关、怎么防止误接生产、怎么验证事务/回滚/幂等”。不是现在连数据库，不是现在建表，不是现在写 migration，不是现在把 repository 接上数据库。

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
git log --oneline -90
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
docs/agent/348N_R7BV_QA_REPOSITORY_SKELETON_QA_REVIEW.md
docs/agent/348N_R7BV_REPOSITORY_SKELETON_QA_REPORT.md
docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md
docs/agent/348N_R7BU_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_NO_DB_CONNECTION_REPORT.md
docs/agent/348N_R7BT_QA_SCHEMA_MIGRATION_QA_DOCS_ONLY_REVIEW.md
docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md
docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
```

Review current repository skeleton and tests read-only:

```text
datefac_agent/review/review_queue_repository.py
tests/agent/test_review_queue_repository_skeleton_348n.py
tests/agent/test_review_queue_repository_skeleton_qa_348n.py
```

Review related test-only chain read-only if useful:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
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

Create a docs-only design for a future local test DB prototype stage.

The design must explain how a future implementation could test repository persistence safely using a local test database, while preventing accidental production activation.

R7BW must not implement the prototype.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md
```

No other tracked files may change.

## Required design content

The design report must cover:

```text
1. Current baseline after R7BV-QA.
2. Why R7BW is docs-only.
3. Local test DB prototype scope.
4. Explicit non-goals.
5. Candidate local DB choice and tradeoffs.
6. Test-only activation model.
7. Environment allowlist and default-off behavior.
8. Required schema/migration rehearsal plan.
9. Required repository adapter boundary.
10. Required transaction and rollback behavior.
11. Required idempotency/uniqueness behavior.
12. Required raw-payload exclusion behavior.
13. Required audit/record hash behavior.
14. Required failure-mode tests.
15. Required cleanup/teardown strategy.
16. Required no-production-connection guarantees.
17. Required no-clean_data/no-delivery/no-export guarantees.
18. Required validation commands for future implementation.
19. Risks and open questions.
20. Recommended next task.
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
-> docs-only schema/migration design
-> schema/migration design QA
-> disabled-by-default repository interface skeleton
-> repository skeleton QA hardening
```

Also state:

```text
current repository skeleton is disabled by default
current skeleton has no DB/IO/network behavior
current local DB prototype does not exist
no real database schema exists
no migration exists
no production repository exists
R7BV-QA approved targeted repository skeleton QA tests at 32 passed
latest known full tests/agent = 592 passed
readiness_gates remain CLOSED
```

## Candidate local DB planning

Discuss candidate choices without implementing them:

```text
SQLite in-memory or temporary file for local-only testing
PostgreSQL test container only if later explicitly allowed
pure fake repository remains valid for unit-level boundary tests
```

The design must not require Docker or a real DB now. It may recommend starting with the smallest local test DB option only after a separate implementation task.

## Required activation model

Plan future implementation to require all of the following before any DB prototype can run:

```text
explicit test-only flag
explicit local-test environment value
explicit test DSN or in-memory DB selection
hard rejection of production-looking DSNs
hard rejection of non-local hosts
no environment-variable-only activation
no default DB connection
no production writer config
no automatic activation from repository skeleton factory
no automatic activation from validated schema alignment preview
```

## Required repository adapter boundary planning

The future local test DB adapter must:

```text
implement the existing repository port without changing production flow
remain separate from DisabledReviewQueueRepository
remain unavailable by default
be constructed only in tests or explicit local-test prototype paths
not be called by review_queue_builder, clean_data, delivery/export, or production adapter
not import test fake repository code into production code
not mutate clean_data
not trigger delivery/export
not open readiness gates
```

## Required schema/migration rehearsal planning

The design must plan:

```text
schema creation only in test context
migration rehearsal only against local test DB
clean setup and teardown
forward migration preference
non-destructive rollback policy by default
manual recovery strategy for bad rows
no migration file in R7BW
no production migration in future prototype without separate gate review
```

## Required transaction/idempotency planning

Discuss how future tests must prove:

```text
single-row insert atomicity
batch insert atomicity
no partial success by default
invalid row rolls back entire batch
idempotent retry with same identity and payload is deterministic
same idempotency_key with different payload conflicts / fails closed
same review_item_id with different identity conflicts / fails closed
record_payload_hash consistency is enforced
no silent duplicate insert
```

## Required raw payload and boundary planning

Future local DB prototype must reject and never store:

```text
full source_text
raw MinerU payload
raw Excel payload
raw parser payload
raw OCR payload
raw LLM/VLM response
DB secrets or production DSNs
output path / file path config
production writer config
readiness override
clean_data intent
delivery/export intent
```

Only bounded evidence_preview/source_trace metadata may be stored.

## Required failure-mode tests to plan

Future implementation must include tests for:

```text
missing identity fields
malformed idempotency_key
malformed record_payload_hash
duplicate idempotency_key same payload
duplicate idempotency_key different payload
duplicate review_item_id conflict
batch with later invalid row
transaction failure rollback
bad enum/status value
raw payload leakage attempt
production DSN/config attempt
environment activation attempt
read after failed write
cleanup/teardown leaves no residual state
```

## Required safety rules to preserve

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

Explicitly state R7BW does not:

```text
modify production code
modify tests
modify fixtures
add database adapter
add repository implementation
add database model
add database schema
add migration
add DB connection
add SQL execution
add storage implementation
write output files
run extraction
run MinerU/OCR/LLM/VLM
connect to Docker/PostgreSQL/SQLite
open readiness gates
claim production persistence
claim production readiness
claim client readiness
claim formal export readiness
```

## Required remaining risks

Include:

```text
local test DB prototype is only designed, not implemented
real DB transaction behavior is not proven
real migration behavior is not proven
concurrency behavior is not proven
performance behavior is not proven
cleanup/teardown behavior is not proven
production operation controls are not proven
client/export readiness still not implied
```

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BV-QA recap
大白话说明
Current baseline
Docs-only scope
Local test DB prototype scope
Candidate local DB choice
Activation and environment gate design
Repository adapter boundary design
Schema/migration rehearsal design
Transaction and rollback design
Idempotency and uniqueness design
Raw-payload exclusion design
Audit and record hash design
Failure-mode test plan
Cleanup and teardown strategy
No-production-connection guarantees
clean_data/delivery/export separation
Future validation plan
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
local_test_db_design_result（本地测试DB设计结果）=
activation_gate_design_result（激活门设计结果）=
environment_allowlist_design_result（环境白名单设计结果）=
repository_adapter_boundary_design_result（repository adapter边界设计结果）=
schema_migration_rehearsal_design_result（schema/migration rehearsal设计结果）=
transaction_rollback_design_result（事务回滚设计结果）=
idempotency_uniqueness_design_result（幂等唯一性设计结果）=
raw_payload_exclusion_design_result（原始payload排除设计结果）=
audit_record_hash_design_result（审计/record hash设计结果）=
failure_mode_test_plan_result（失败模式测试计划结果）=
cleanup_teardown_design_result（清理/teardown设计结果）=
no_production_connection_design_result（无生产连接设计结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BW-QA local test DB prototype design review
```

## Validation commands

Docs-only, but still verify the current test-only chain remains green.

```text
python -m py_compile datefac_agent/review/review_queue_repository.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
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
python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
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
git add docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md
git commit -m "docs: design local test DB prototype"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
