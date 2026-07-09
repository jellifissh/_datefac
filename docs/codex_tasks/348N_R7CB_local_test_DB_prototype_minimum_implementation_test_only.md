# 348N-R7CB local test DB prototype minimum implementation test-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-minimum-local-db-prototype
```

## Plain-language goal

R7CA-QA approved the docs-only implementation plan. R7CB may now implement the smallest possible local test DB prototype, but only under `tests/agent`, only for local test use, and only with in-memory test-owned state. It must not modify production code or create production persistence.

In plain Chinese: 这一轮可以第一次真的做一个“最小本地测试 DB 原型”，但只能是测试目录里的原型。允许在测试里用 Python 标准库的 in-memory SQLite 来证明最小写入、事务回滚和幂等冲突行为。禁止接生产，禁止写正式 schema/migration，禁止改 `datefac_agent/`，禁止让业务链路调用它。

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
git log --oneline -125
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
docs/agent/348N_R7CA_QA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_REVIEW.md
docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md
docs/agent/348N_R7BZ_QA_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BZ_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT.md
docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md
docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md
```

Review existing local test DB boundary files:

```text
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
```

Review repository/fake repository chain read-only if useful:

```text
datefac_agent/review/review_queue_repository.py
tests/agent/test_review_queue_repository_skeleton_348n.py
tests/agent/test_review_queue_repository_skeleton_qa_348n.py
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
```

## Goal

Create a minimum test-only local DB prototype that proves a narrow subset of future persistence behavior using in-memory local test storage.

This is still not production persistence.

## Allowed tracked files

Create exactly:

```text
tests/agent/review_queue_local_test_db_prototype_348n.py
tests/agent/test_review_queue_local_test_db_prototype_348n.py
docs/agent/348N_R7CB_LOCAL_TEST_DB_PROTOTYPE_MINIMUM_IMPLEMENTATION_TEST_ONLY_REPORT.md
```

No production code may change. Do not modify existing tests, fixtures, reports, configs, dependencies, migrations, schema files, or handoff docs.

## Permitted implementation scope

Allowed:

```text
use Python standard library sqlite3 inside tests/agent/review_queue_local_test_db_prototype_348n.py
use only sqlite3.connect(':memory:') or equivalent in-memory connection
create schema only inside test setup / prototype constructor
use parameterized SQL only inside the test-only prototype module
insert a minimal review_queue candidate row after explicit local-test activation gates pass
read back by review_item_id and run_id inside test-only prototype
model transaction rollback using sqlite transaction behavior
model idempotency and uniqueness conflicts using local-only constraints
```

Forbidden:

```text
modify datefac_agent production code
import this prototype from production code
add real production repository implementation
add production database model
add migration file
add schema file
add dependency
connect to PostgreSQL/MySQL/remote DB/Docker
use file-backed SQLite path
read environment variables as the only activation source
write output files
run extraction/MinerU/OCR/LLM/VLM
modify review_queue_builder
modify clean_data
modify delivery/export
open readiness gates
claim production persistence/readiness/client readiness
```

## Required activation gates

The prototype must only be constructible through an explicit test-only config object or factory.

Require all of these:

```text
test_only = True
environment = local_test
storage = sqlite_memory or in_memory_sqlite
explicit_prototype_enabled = True
```

Reject/fail closed on:

```text
missing/false test_only
missing/wrong environment
missing/wrong storage
missing/false explicit_prototype_enabled
production/staging/dev/prod-like environment values
any DSN string
any host/endpoint
any file path DB config
any production writer config
any readiness override
any clean_data intent
any delivery/export intent
environment-variable-only activation
```

## Required minimal row shape

Use the smallest safe row shape needed to test behavior. Suggested fields:

```text
review_item_id
run_id
candidate_id
idempotency_key
record_payload_hash
status
blocked_delivery_reason
evidence_preview
source_trace
created_at
```

Do not store:

```text
full source_text
raw MinerU payload
raw Excel payload
raw parser payload
raw OCR payload
raw LLM/VLM payload
clean_data payload
delivery/export payload
production DSN/secrets/output paths
```

## Required tests

Create tests proving:

```text
prototype module lives under tests/agent and is marked test-only
prototype uses in-memory SQLite only
prototype cannot be constructed without all explicit gates
prototype rejects DSN/host/path/production-like config
prototype does not read environment variables as sufficient activation
prototype creates schema only in test-owned in-memory connection
successful insert and readback of one minimal candidate works after explicit gates
batch insert is atomic
invalid first row rolls back whole batch
invalid later row rolls back whole batch
same idempotency_key + same record_payload_hash is deterministic and does not duplicate silently
same idempotency_key + different record_payload_hash conflicts/fails closed
same review_item_id + conflicting identity conflicts/fails closed
record_payload_hash is required
raw payload fields are rejected before DB write
clean_data/delivery/export/readiness intent is rejected before DB write
input candidate/config objects are not mutated
error messages do not echo raw payloads, DSNs, secrets, hosts, endpoints, or file paths
source inspection confirms sqlite3 appears only in the new test-only prototype module, not production code or existing boundary skeleton
source inspection confirms no network, Docker, file-backed DB path, filesystem writes, or production imports were added
existing R7BX/R7BY boundary tests remain compatible
repository skeleton tests remain compatible
readiness_gates remain CLOSED by report
```

## Required compatibility rules

The existing boundary module must remain stricter than the prototype:

```text
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py must still not import sqlite3
R7BX/R7BY boundary tests must still pass
production repository skeleton must remain disabled by default
production code must not import the new prototype
fake repository tests must still pass
```

## Suggested implementation shape

Keep it small. Suggested names:

```text
LocalTestDBPrototypeConfig
LocalTestDBPrototypeError
LocalTestDBActivationError
LocalTestDBWriteConflictError
LocalTestDBPrototype
make_local_test_db_prototype(config)
```

Suggested methods:

```text
write_batch(candidates) -> receipt-like test-only result
get_by_review_item_id(review_item_id)
list_by_run_id(run_id)
close()
```

The receipt must be clearly test-only and must not imply production persistence.

## Required report sections

```text
Task ID
Preflight
Files reviewed
R7CA-QA recap
大白话说明
Implementation scope
Files changed
Activation gate implementation
In-memory local DB implementation
Schema setup behavior
Minimal row shape
Write/read behavior
Transaction and rollback behavior
Idempotency and uniqueness behavior
Raw payload exclusion behavior
clean_data/delivery/export/readiness boundary
Input mutation safety
Error leakage safety
Source inspection
Compatibility with R7BX/R7BY boundary tests
Repository skeleton compatibility
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
minimum_local_db_prototype_result（最小本地DB原型结果）=
test_only_implementation_result（test-only实现结果）=
activation_gate_result（激活门结果）=
in_memory_sqlite_result（内存SQLite结果）=
schema_setup_result（schema设置结果）=
write_read_result（写入读取结果）=
transaction_rollback_result（事务回滚结果）=
idempotency_uniqueness_result（幂等唯一性结果）=
raw_payload_exclusion_result（原始payload排除结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
input_mutation_safety_result（输入变更安全结果）=
error_leakage_safety_result（错误泄漏安全结果）=
source_inspection_result（源码检查结果）=
compatibility_with_r7bx_r7by_result（与R7BX/R7BY兼容结果）=
repository_skeleton_compatibility_result（repository skeleton兼容结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7CB-QA local test DB prototype minimum implementation review
```

## Validation commands

```text
python -m py_compile tests/agent/review_queue_local_test_db_prototype_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_prototype_348n.py
python -m py_compile tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
python -m py_compile datefac_agent/review/review_queue_repository.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
python -m py_compile tests/agent/review_queue_fake_repository_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_fake_repository_boundary_348n.py
python -m py_compile tests/agent/review_queue_persistence_contract_348n.py
python -m py_compile tests/agent/test_review_queue_persistence_contract_348n.py
python -m pytest tests/agent/test_review_queue_local_test_db_prototype_348n.py -q
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
python -m pytest tests/agent/test_review_queue_fake_repository_boundary_348n.py -q
python -m pytest tests/agent/test_review_queue_persistence_contract_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Commit and push

If validation passes and only allowed files changed, stage exactly:

```text
git add tests/agent/review_queue_local_test_db_prototype_348n.py
git add tests/agent/test_review_queue_local_test_db_prototype_348n.py
git add docs/agent/348N_R7CB_LOCAL_TEST_DB_PROTOTYPE_MINIMUM_IMPLEMENTATION_TEST_ONLY_REPORT.md
git commit -m "test: add minimum local test DB prototype"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
