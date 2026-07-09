# 348N-R7BT schema/migration QA docs-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = high
execution_mode = docs-only-QA-planning
```

## Plain-language goal

R7BS-QA approved the docs-only database schema and migration design. R7BT creates a docs-only QA plan for how future schema/migration work must be reviewed before any implementation can proceed.

In plain Chinese: 这一轮不是再建表，也不是写 migration，而是写一份“未来真的要做 schema/migration 时，QA 要怎么查、查哪些风险、哪些情况必须拦住”的文档。它是给后续 R7BU/R7BV/R7BW 之前用的安全检查清单。

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
git log --oneline -75
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
docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md
docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
```

Review current test-only files read-only if useful:

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

Create a docs-only QA plan for future review_queue schema/migration work.

The QA plan must define what future reviewers must verify before any of these later steps are allowed:

```text
disabled repository skeleton
local test database prototype behind explicit test flag
negative-path / rollback tests against local test database
production gate review
production hook consideration
```

R7BT itself must not implement any of these steps.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md
```

No other tracked files may change.

## Required QA planning content

The report must cover:

```text
1. Current baseline after R7BS-QA.
2. Why R7BT is docs-only.
3. Future schema QA checklist.
4. Future migration QA checklist.
5. Future idempotency/uniqueness QA checklist.
6. Future index/query-pattern QA checklist.
7. Future enum/check-constraint QA checklist.
8. Future raw-payload exclusion QA checklist.
9. Future transaction and batch atomicity QA checklist.
10. Future rollback / forward-fix QA checklist.
11. Future retention/retraction QA checklist.
12. Future feature flag and environment gate QA checklist.
13. Future audit trail and record hash QA checklist.
14. Future no-clean-data/no-delivery/no-export QA checklist.
15. Future performance/concurrency questions.
16. Future production gate prerequisites.
17. Red flags that must block implementation.
18. Open questions.
19. Non-goals.
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
```

Also state:

```text
current persistence stack is still test-only and in-memory
no real database schema exists
no migration exists
no production repository exists
R7BS-QA approved only the design, not implementation
latest known full tests/agent = 543 passed
readiness_gates remain CLOSED
```

## Future schema QA checklist

Include checks for:

```text
conceptual table remains clearly mapped to review_queue only
identity/hash fields are present and non-ambiguous
status/action fields cannot imply clean_data or delivery unblock
bounded evidence_preview/source_trace only
raw payload fields are absent
created/updated/retracted timestamps are defined safely
soft retraction is supported without destructive delete by default
field names and versions match the persistence contract vocabulary
```

## Future migration QA checklist

Include checks for:

```text
migration order is explicit
migration can be applied in a clean environment
migration has a safe forward-fix path
rollback policy avoids destructive data loss by default
no default production activation
no default production connection
migration does not create export/delivery side effects
migration has a test-only rehearsal plan before production gate review
```

## Future idempotency and uniqueness QA checklist

Include checks for:

```text
idempotency_key uniqueness
review_item_id uniqueness
record_payload_hash consistency
same identity + same payload deterministic behavior
same identity + different payload conflict/fail-closed behavior
no silent duplicate insert
batch duplicate detection
transient retry behavior
```

## Future transaction and rollback QA checklist

Include checks for:

```text
single-row atomic behavior
batch atomic behavior by default
no partial success by default
invalid row does not mutate persisted state
audit event for attempt/result
safe retry after transient failure
manual recovery path for bad rows
```

## Future raw-payload and boundary QA checklist

The QA plan must require future schema/repository checks to reject:

```text
full source_text
raw MinerU payload
raw Excel payload
raw parser/OCR payload
raw LLM/VLM response
connection secrets or runtime endpoints
output path/file path config
production writer config
readiness override
clean_data intent
delivery/export intent
```

Only bounded evidence_preview/source_trace metadata may be stored.

## Red flags that must block implementation

List blockers such as:

```text
schema implies clean_data promotion
schema implies delivery/export readiness
migration enables production by default
repository can run without explicit test flag in test stages
raw payloads can be stored
duplicates can silently insert
batch can partially commit without explicit design approval
rollback requires destructive delete by default
readiness_gates are opened without separate gate review
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

Explicitly state R7BT does not:

```text
modify production code
modify tests
modify fixtures
add repository/model/service code
add database schema
add migration
add database connection
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

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BS-QA recap
大白话说明
Current baseline
Docs-only scope
Future schema QA checklist
Future migration QA checklist
Future idempotency and uniqueness QA checklist
Future index and query QA checklist
Future enum and constraint QA checklist
Future raw-payload exclusion QA checklist
Future transaction and batch atomicity QA checklist
Future rollback and forward-fix QA checklist
Future retention and retraction QA checklist
Future feature gate and environment QA checklist
Future audit and record hash QA checklist
Future clean_data/delivery/export separation QA checklist
Performance and concurrency questions
Production gate prerequisites
Implementation blockers / red flags
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
schema_qa_plan_result（schema QA计划结果）=
migration_qa_plan_result（migration QA计划结果）=
idempotency_uniqueness_qa_plan_result（幂等唯一性QA计划结果）=
index_query_qa_plan_result（索引查询QA计划结果）=
constraint_enum_qa_plan_result（约束枚举QA计划结果）=
raw_payload_exclusion_qa_plan_result（原始payload排除QA计划结果）=
transaction_atomicity_qa_plan_result（事务原子性QA计划结果）=
rollback_forward_fix_qa_plan_result（回滚/前向修复QA计划结果）=
feature_gate_qa_plan_result（feature gate QA计划结果）=
clean_data_delivery_boundary_qa_plan_result（clean_data/交付边界QA计划结果）=
production_gate_prerequisite_result（生产gate前置条件结果）=
red_flag_blocker_result（红线阻断项结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BT-QA schema/migration QA docs-only review
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

If validation passes and only the QA planning report is created, stage exactly:

```text
git add docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md
git commit -m "docs: plan schema migration QA"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
