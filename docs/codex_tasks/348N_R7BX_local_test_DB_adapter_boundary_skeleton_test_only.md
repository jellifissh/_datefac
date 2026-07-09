# 348N-R7BX local test DB adapter boundary skeleton test-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-local-db-adapter-boundary-skeleton
```

## Plain-language goal

R7BW-QA approved the docs-only local test DB prototype design. R7BX may now add a test-only local test DB adapter boundary skeleton, but it must not connect to any real database, must not create schema/migrations, and must not implement persistence.

In plain Chinese: 这一轮可以开始做“本地测试 DB adapter 的边界骨架”，但只能放在 `tests/agent` 里，只能是 test-only 的假边界/合同原型。它不是 SQLite/PostgreSQL adapter，不连数据库，不建表，不写 SQL，不写 migration，不把 repository 接生产。目标是先把未来 local test DB adapter 的激活门、配置拒绝、fail-closed、raw payload 拦截、事务/回滚语义这些边界用测试固定住。

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
git log --oneline -95
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
docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md
docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md
docs/agent/348N_R7BV_QA_REPOSITORY_SKELETON_QA_REVIEW.md
docs/agent/348N_R7BV_REPOSITORY_SKELETON_QA_REPORT.md
docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md
docs/agent/348N_R7BU_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_NO_DB_CONNECTION_REPORT.md
docs/agent/348N_R7BT_QA_SCHEMA_MIGRATION_QA_DOCS_ONLY_REVIEW.md
docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
```

Review current repository skeleton and QA tests:

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

Create a test-only local test DB adapter boundary skeleton.

The skeleton must model the boundary and activation contract for a future local test DB adapter, without using a real database.

## Allowed tracked files

Create exactly:

```text
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md
```

No production code may change.

Do not modify existing tests or fixtures unless absolutely necessary. Default expectation: only the 3 files above change.

## Required boundary skeleton behavior

The test-only boundary skeleton must:

```text
live under tests/agent only
be clearly marked test-only
not be imported by production code
not import sqlite3/sqlalchemy/psycopg/psycopg2/pymysql/mysql/asyncpg/redis/boto/cloud storage clients
not open files
not create temp files
not use Docker
not connect to SQLite/PostgreSQL or any real DB
not execute SQL
not create schema
not create migration
not create tables
not write output files
not mutate clean_data
not trigger delivery/export
not open readiness gates
```

## Suggested test-only interface shape

Use the smallest possible shape. Suggested concepts:

```text
LocalTestDBAdapterBoundaryError
LocalTestDBAdapterActivationError
LocalTestDBAdapterConfig
LocalTestDBAdapterBoundary
make_disabled_local_test_db_adapter_boundary()
validate_local_test_db_activation_request(config)
```

The exact names may be adjusted to fit current test style.

## Required activation gate behavior

The skeleton must prove future local test DB adapter activation is fail-closed unless all conditions are explicit.

For this R7BX test-only skeleton, do not actually enable DB behavior even if all flags are present. Instead, return a planned/disabled boundary result or raise a planned-disabled exception.

Required rejected inputs:

```text
missing test_only flag
missing local_test environment value
production environment value
staging environment value
production-looking DSN
non-local host
network endpoint
connection string
DB secret
production writer config
output path / file path config
readiness override
clean_data intent
delivery/export intent
environment-variable-only activation
schema alignment preview auto-activation
repository skeleton factory auto-activation
```

## Required candidate payload validation behavior

The test-only boundary must reject or fail closed on candidates containing:

```text
full source_text
raw_mineru_payload
raw_excel_payload
raw_parser_payload
raw_ocr_payload
raw_llm_payload
raw_vlm_payload
unbounded evidence text
clean_data payload
delivery/export payload
readiness override
production timestamp override
caller-supplied DB row
caller-supplied receipt claiming committed DB write
caller-supplied internal adapter state
```

Only bounded evidence_preview/source_trace-style metadata may be accepted by future design. R7BX does not persist it.

## Required transaction/idempotency boundary behavior

Because this is not a real DB adapter, the skeleton should model required future semantics without storing records:

```text
batch is atomic by contract
no partial success by default
invalid row makes entire batch fail closed
same idempotency_key + same record_payload_hash planned deterministic retry policy is documented/test-visible
same idempotency_key + different record_payload_hash planned conflict/fail-closed policy is documented/test-visible
same review_item_id + conflicting identity planned conflict/fail-closed policy is documented/test-visible
no silent duplicate insert is allowed by contract
record_payload_hash is required for future persistence candidates
```

Do not implement real persistence state.

## Required tests

Create focused tests proving:

```text
boundary module imports without DB/storage/network dependencies
boundary is test-only by name/path/metadata
activation fails closed by default
activation cannot be driven only by environment variables
activation rejects production/staging environment values
activation rejects production-looking DSNs, non-local hosts, endpoints, secrets, output paths, table names, writer configs
activation rejects auto-activation from schema alignment preview or repository skeleton factory
candidate validation rejects raw payload fields and full source_text
candidate validation rejects clean_data/delivery/export/readiness intent
candidate validation rejects caller-supplied DB rows, committed receipts, and internal adapter state
invalid batch fails as a whole
duplicate idempotency/conflict policy is explicit and fail-closed at boundary
input config and candidate objects are not mutated
error messages do not echo raw payloads, secrets, DSNs, endpoints, or output paths
source inspection confirms no DB imports, SQL markers, file-write markers, network markers, Docker markers, or production fake-repository import
readiness_gates remain CLOSED by report and no code path mutates them
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

## Strict boundaries

Forbidden:

```text
modify datefac_agent production code
add real DB adapter
add database model
add migration
add database schema
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
claim client readiness
use git add .
use git add -A
```

## Report requirements

Create the report with these sections:

```text
Task ID
Preflight
Files reviewed
R7BW-QA recap
大白话说明
Test-only boundary scope
Files changed
Boundary skeleton behavior
Activation gate behavior
Candidate payload validation behavior
Transaction/idempotency boundary behavior
No-DB / no-IO / no-network guarantee
Source inspection
Input mutation safety
Raw payload and secret leakage safety
clean_data/delivery/export/readiness boundary
Fake repository and repository skeleton compatibility
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
local_test_db_adapter_boundary_result（本地测试DB adapter边界结果）=
test_only_boundary_result（test-only边界结果）=
activation_gate_result（激活门结果）=
environment_rejection_result（环境拒绝结果）=
production_config_rejection_result（生产配置拒绝结果）=
candidate_payload_validation_result（候选payload校验结果）=
transaction_idempotency_boundary_result（事务/幂等边界结果）=
input_mutation_safety_result（输入变更安全结果）=
raw_payload_leakage_result（原始payload泄漏结果）=
no_db_no_io_no_network_result（无DB/IO/网络结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
fake_repository_compatibility_result（fake repository兼容结果）=
repository_skeleton_compatibility_result（repository skeleton兼容结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BX-QA local test DB adapter boundary skeleton review
```

## Validation commands

```text
python -m py_compile tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
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
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
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

If validation passes and only allowed files changed, stage exactly:

```text
git add tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
git add tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
git add docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md
git commit -m "test: add local test DB adapter boundary skeleton"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
