# 348N-R7BS-QA database schema and migration design review

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = QA-review-only
```

## Plain-language goal

R7BS created a docs-only schema and migration design for future review_queue persistence. R7BS-QA checks that the design is accurate, conservative, complete, and still does not implement or authorize real database persistence.

In plain Chinese: 这一轮只审查 R7BS 的“未来表结构/迁移设计”有没有越界。重点确认它只是设计，不是实现；没有建表、没有 migration、没有 repository、没有数据库连接、没有生产 hook，也没有把 readiness_gates 打开。

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
docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md
docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
```

Review current test-only files read-only if needed:

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

## QA checklist

Confirm:

```text
R7BS changed only the allowed docs-only schema/migration design report.
No production code was modified.
No tests or fixtures were modified.
No database schema file was created.
No migration file was created.
No repository/model/service implementation was created.
No database connection, storage code, output writer, export path, production hook, or readiness gate change was added.
The report clearly states R7BS is docs-only.
The report does not claim production persistence exists.
The report does not claim production readiness, client readiness, or formal export readiness.
The current baseline is accurate and ends at fake repository negative-path and idempotency expansion.
The report states the current stack is still test-only and in-memory.
The report states R7BR-QA approved fake repository targeted tests at 63 passed.
The report states latest known full tests/agent is 543 passed.
The report states readiness_gates remain CLOSED.
Conceptual table and columns are clearly planning candidates only.
Identity/hash fields are covered.
Review status/action fields are covered and do not imply clean_data or delivery unblock.
Evidence/source trace fields are bounded and do not allow full source_text or raw payloads.
Audit metadata fields are covered.
Idempotency and uniqueness constraints are covered.
No silent duplicate insert is allowed.
Same identity with changed payload is treated as conflict/fail-closed or explicitly left as a design question.
Index and query patterns are covered for review UI, audit lookup, run/source/status filters, and hash lookup.
Check/enum constraints are covered.
Constraints prevent clean_data/delivery/export/readiness from being implied by stored rows.
Raw-payload exclusion is explicit.
Only bounded evidence_preview/source_trace metadata may be stored.
Transaction and batch atomicity rules are covered.
No partial success by default is preserved.
Rollback on invalid row and idempotent retry are covered.
Audit event for persistence attempt/result is planned.
Soft retraction is preferred over destructive delete by default.
Forward migration over destructive rollback is discussed when data exists.
Migration order is conservative.
Feature gates and environment allowlist are explicit.
No default production database connection is allowed.
No automatic activation from validated schema alignment preview is allowed.
Core safety rules are preserved.
Remaining risks are explicit.
Recommended next task is safe and does not jump directly to production implementation.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, schema files, design report, handoff docs, planning docs, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
```

No other tracked files may change.

## Validation commands

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

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BS recap
大白话说明审查
Docs-only boundary review
Current baseline review
Conceptual table design review
Conceptual column design review
Identity and hash field review
Review status/action field review
Evidence preview and source trace review
Audit metadata review
Idempotency and uniqueness review
Index and query pattern review
Constraint and enum review
Raw-payload exclusion review
Transaction and batch atomicity review
Migration order review
Rollback and forward-fix review
Retention and retraction review
Feature gate and environment planning review
Readiness gate review
Open questions review
Non-goals review
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
schema_design_review_result（schema设计审查结果）=
migration_design_review_result（migration设计审查结果）=
conceptual_table_review_result（概念表审查结果）=
conceptual_column_review_result（概念字段审查结果）=
identity_hash_design_review_result（身份/哈希设计审查结果）=
status_action_design_review_result（状态/动作设计审查结果）=
evidence_trace_design_review_result（证据/trace设计审查结果）=
audit_metadata_design_review_result（审计元数据设计审查结果）=
idempotency_uniqueness_design_review_result（幂等唯一性设计审查结果）=
index_query_design_review_result（索引查询设计审查结果）=
constraint_enum_design_review_result（约束枚举设计审查结果）=
raw_payload_exclusion_design_review_result（原始payload排除设计审查结果）=
transaction_atomicity_design_review_result（事务原子性设计审查结果）=
rollback_forward_fix_design_review_result（回滚/前向修复设计审查结果）=
feature_gate_design_review_result（feature gate设计审查结果）=
readiness_gate_review_result（就绪门审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BT schema/migration QA docs-only
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
git commit -m "docs: add R7BS QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
