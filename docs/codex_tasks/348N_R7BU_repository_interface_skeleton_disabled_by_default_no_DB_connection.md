# 348N-R7BU repository interface skeleton disabled-by-default, no DB connection

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = disabled-production-adjacent-skeleton-no-db
```

## Plain-language goal

R7BT-QA approved the docs-only schema/migration QA plan. R7BU may now add the smallest possible production-adjacent repository interface skeleton for future review_queue persistence, but it must be disabled by default and must not connect to any database.

In plain Chinese: 这一轮可以第一次在 `datefac_agent/` 里放一个“未来 repository 的接口骨架”，但它只能是骨架。默认必须关闭，不能连数据库，不能写文件，不能建表，不能 migration，不能真的保存 review_queue，不能接生产流程。它的作用只是把未来 repository 该长什么样、默认关闭时怎么 fail-closed 固定下来。

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
git log --oneline -80
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
docs/agent/348N_R7BT_QA_SCHEMA_MIGRATION_QA_DOCS_ONLY_REVIEW.md
docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md
docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md
docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
```

Review current test-only files:

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

Review production-adjacent modules read-only if needed:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Add a minimal repository interface skeleton that is disabled by default and has no database connection.

This is not a real persistence implementation. It should provide a safe future boundary only.

## Allowed tracked files

You may create exactly:

```text
datefac_agent/review/review_queue_repository.py
tests/agent/test_review_queue_repository_skeleton_348n.py
docs/agent/348N_R7BU_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_NO_DB_CONNECTION_REPORT.md
```

No other tracked files may change unless a package import file absolutely requires it. If an import file change is needed, stop and document the reason before changing it.

## Required skeleton behavior

The production-adjacent skeleton must:

```text
live under datefac_agent/review/
be disabled by default
perform no IO
perform no DB access
perform no network access
perform no filesystem writes
create no database schema
create no migration
create no table
create no storage adapter
write no output files
mutate no clean_data
trigger no delivery/export
open no readiness gate
include no default production DB connection
include no DSN/connection string/table-name/path config
not import sqlite3/sqlalchemy/psycopg/psycopg2/pymysql/mysql/asyncpg/redis/boto/cloud storage clients
not import tests/agent fake repository code into production code
```

## Suggested interface shape

Use the smallest shape that matches the prior planning docs. You may refine names if the existing project style requires it.

Suggested concepts:

```text
ReviewQueueRepositoryError
ReviewQueueRepositoryDisabledError
ReviewQueueRepositoryWriteReceipt
ReviewQueueRepositoryPort / Protocol or ABC
DisabledReviewQueueRepository
create_disabled_review_queue_repository()
```

Suggested methods for the port / skeleton:

```text
write_batch(candidates, *, run_id=None) -> ReviewQueueRepositoryWriteReceipt
get_by_review_item_id(review_item_id)
list_by_run_id(run_id)
```

Default implementation must be disabled and fail closed. It must not silently succeed, pretend to persist, or return a DB-like success receipt.

## Required disabled-by-default semantics

The disabled repository must:

```text
raise ReviewQueueRepositoryDisabledError on write attempts
raise ReviewQueueRepositoryDisabledError on read/list attempts, or return an explicit disabled result if the project style strongly prefers that
include an explicit disabled reason
make it impossible to accidentally enable persistence by passing arbitrary config
not accept production flags, DSNs, table names, paths, or runtime endpoints
not use environment variables to enable itself
not mutate input candidates
not store candidates in memory as production state
not claim persistence happened
```

If choosing exception-based behavior, tests must assert the exception message does not contain raw payloads or secrets.

## Required receipt constraints

If a receipt dataclass is included, it must be non-persisting / disabled-only or interface-only. It must not imply a database write.

The receipt must not include:

```text
raw source_text
raw MinerU payload
raw Excel payload
raw parser/OCR payload
raw LLM/VLM response
DB DSN / connection string
output path / file path config
production writer config
readiness override
clean_data intent
delivery/export intent
```

## Required tests

Create focused tests proving:

```text
module imports without DB/storage dependencies
repository factory returns disabled repository by default
write_batch fails closed by default
read/list/get fails closed or explicit disabled behavior is preserved
passing arbitrary production-looking config is rejected or ignored fail-closed
no DB/IO/network/storage imports exist in the skeleton source
no DSN/table/output path config is accepted
write failure does not mutate input candidate objects
failure messages do not leak raw payloads
receipt, if present, does not imply persistence
clean_data/delivery/export/readiness flags are absent or rejected
readiness_gates remain CLOSED by report and no code path mutates them
```

Keep tests deterministic and lightweight. Do not use real DBs. Do not create temp files. Do not run extraction.

## Compatibility with prior fake repository work

R7BU must not replace or weaken the R7BQ/R7BR fake repository tests.

The new skeleton should be a future production boundary. The existing fake repository remains test-only and in-memory under `tests/agent`.

The production skeleton must not import the fake repository.

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

## Strict boundaries

Forbidden:

```text
add real repository implementation
add database model
add migration
add database connection
add SQL execution
add file writes
add storage implementation
add output writer
add export path
add production hook
modify review_queue_builder to call repository
modify clean_data code
modify delivery/export code
run MinerU/OCR/LLM/VLM or extraction
open readiness gates
claim production persistence
claim production readiness
use git add .
use git add -A
```

## Report requirements

Create the report with these sections:

```text
Task ID
Preflight
Files reviewed
R7BT-QA recap
大白话说明
Skeleton scope
Disabled-by-default behavior
Interface shape
No-DB / no-IO / no-network guarantee
Factory behavior
Receipt behavior
Input mutation safety
Raw payload and secret leakage safety
Compatibility with fake repository boundary
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
repository_skeleton_result（repository骨架结果）=
disabled_by_default_result（默认关闭结果）=
no_db_connection_result（无DB连接结果）=
no_io_no_network_result（无IO无网络结果）=
factory_behavior_result（factory行为结果）=
write_fail_closed_result（写入fail-closed结果）=
read_fail_closed_result（读取fail-closed结果）=
config_rejection_result（配置拒绝结果）=
input_mutation_safety_result（输入变更安全结果）=
raw_payload_leakage_result（原始payload泄漏结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
test_only_fake_repository_compatibility_result（test-only fake repository兼容结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BU-QA repository interface skeleton disabled-by-default review
```

## Validation commands

```text
python -m py_compile datefac_agent/review/review_queue_repository.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
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

If validation passes and only allowed files changed, stage exactly:

```text
git add datefac_agent/review/review_queue_repository.py
git add tests/agent/test_review_queue_repository_skeleton_348n.py
git add docs/agent/348N_R7BU_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_NO_DB_CONNECTION_REPORT.md
git commit -m "test: add disabled review queue repository skeleton"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
