# 348N-R7BY local test DB boundary negative-path expansion test-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-negative-path-expansion
```

## Plain-language goal

R7BX-QA approved the test-only local test DB adapter boundary skeleton. R7BY expands the negative-path tests around that boundary so future local test DB work stays fail-closed before any real DB adapter is attempted.

In plain Chinese: 这一轮继续只做 `tests/agent` 防线测试。专门加反例/坏路径：生产 DSN、远程 host、环境变量偷激活、raw payload、clean_data/delivery/export 意图、伪造 DB row、伪造 committed receipt、重复/冲突幂等输入、错误信息泄漏等。仍然不连数据库、不写 SQL、不建表、不写 migration、不改生产代码。

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
git log --oneline -100
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
docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md
docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md
docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md
docs/agent/348N_R7BW_LOCAL_TEST_DB_PROTOTYPE_DESIGN_DOCS_ONLY.md
docs/agent/348N_R7BV_QA_REPOSITORY_SKELETON_QA_REVIEW.md
docs/agent/348N_R7BV_REPOSITORY_SKELETON_QA_REPORT.md
docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md
```

Review current local test DB boundary files:

```text
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
```

Review related repository/fake repository chain read-only if useful:

```text
datefac_agent/review/review_queue_repository.py
tests/agent/test_review_queue_repository_skeleton_348n.py
tests/agent/test_review_queue_repository_skeleton_qa_348n.py
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

Add a test-only negative-path expansion suite for the local test DB adapter boundary skeleton.

The tests must prove the boundary remains fail-closed against malicious, production-looking, malformed, conflicting, and leakage-prone inputs.

## Allowed tracked files

Create exactly:

```text
tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
```

You may modify this test-only boundary file only if the new negative-path tests reveal a missing test-only boundary helper or a safe fail-closed bug:

```text
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
```

Default expectation: no change outside the 2 newly created files.

No production code may change.

## Required negative-path coverage

Create focused tests covering these groups:

```text
activation gate negative paths
production-looking config negative paths
environment-variable activation negative paths
schema preview / repository factory auto-activation negative paths
candidate raw payload negative paths
clean_data/delivery/export/readiness intent negative paths
caller-supplied DB row / committed receipt / internal state negative paths
transaction and idempotency conflict negative paths
input mutation safety negative paths
error leakage negative paths
source inspection negative paths
compatibility with existing R7BX tests
```

## Activation gate negative paths

Test that activation fails closed when any required future condition is missing or invalid:

```text
missing test_only flag
false test_only flag
missing environment value
empty environment value
production environment
staging environment
dev/prod mixed value
missing local DB selection
unsupported DB selection
activation based only on environment variable
activation based only on schema alignment preview
activation based only on repository skeleton factory
```

R7BY must not actually enable database behavior even if all planned flags are present. If the existing boundary exposes a planned-disabled result, assert that it remains planned/disabled, not connected.

## Production-looking config negative paths

Test rejection/fail-closed behavior for:

```text
postgres:// user DSN
postgresql:// user DSN
mysql:// user DSN
sqlite:/// absolute path
file path DB URL
remote host
non-local host
cloud host
port endpoint
http endpoint
https endpoint
connection string
DB password/secret/API key/token
schema name
table name
migration name
output path
file path config
production writer config
readiness override
```

Failure messages must not echo the sensitive values.

## Candidate payload negative paths

Test rejection/fail-closed behavior for candidates containing:

```text
source_text
full_source_text
raw_mineru_payload
raw_excel_payload
raw_parser_payload
raw_ocr_payload
raw_llm_payload
raw_vlm_payload
unbounded evidence text
oversized evidence_preview if a bound exists
clean_data payload
normalized_clean_data
approved_export_payload
delivery/export payload
readiness override
production timestamp override
caller-supplied DB primary key
caller-supplied DB row
caller-supplied committed receipt
caller-supplied internal adapter state
```

Only bounded preview/trace-style metadata may be accepted by future design, and R7BY still does not persist it.

## Transaction and idempotency negative paths

Model future contract failures without real persistence:

```text
missing idempotency_key
malformed idempotency_key
missing record_payload_hash
malformed record_payload_hash
same idempotency_key with different record_payload_hash
same review_item_id with conflicting identity
batch with first invalid row fails whole batch
batch with later invalid row fails whole batch
batch with duplicate conflicting entries fails whole batch
no partial success result is returned by default
no silent duplicate insert is allowed by contract
```

Do not implement real persistence state.

## Source inspection negative paths

Tests must inspect the boundary source and assert absence of:

```text
sqlite3
sqlalchemy
psycopg
psycopg2
pymysql
mysql
asyncpg
redis
boto
Docker/docker
connect(
execute(
SELECT
INSERT
UPDATE
DELETE
CREATE TABLE
ALTER TABLE
open(
write(
requests
urllib
socket
subprocess
```

Adjust exact matching carefully so the test checks source content without causing false positives from the test text itself.

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
claim local DB implementation exists
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
R7BX-QA recap
大白话说明
Negative-path expansion scope
Files changed
Activation gate negative paths
Production-looking config negative paths
Environment activation negative paths
Candidate raw payload negative paths
clean_data/delivery/export/readiness negative paths
Caller-supplied DB row / receipt / internal state negative paths
Transaction/idempotency negative paths
Input mutation safety
Error leakage safety
Source inspection
Compatibility with R7BX boundary tests
No-DB / no-IO / no-network guarantee
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
negative_path_expansion_result（负路径扩展结果）=
activation_gate_negative_path_result（激活门负路径结果）=
production_config_negative_path_result（生产配置负路径结果）=
environment_activation_negative_path_result（环境激活负路径结果）=
candidate_payload_negative_path_result（候选payload负路径结果）=
clean_data_delivery_negative_path_result（clean_data/交付负路径结果）=
caller_supplied_db_state_negative_path_result（调用方伪造DB状态负路径结果）=
transaction_idempotency_negative_path_result（事务/幂等负路径结果）=
input_mutation_safety_result（输入变更安全结果）=
error_leakage_safety_result（错误泄漏安全结果）=
source_inspection_result（源码检查结果）=
no_db_no_io_no_network_result（无DB/IO/网络结果）=
compatibility_with_r7bx_result（与R7BX兼容结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BY-QA local test DB boundary negative-path expansion review
```

## Validation commands

```text
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
python -m py_compile tests/agent/review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
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

If validation passes and only allowed files changed, stage exactly the changed allowed files. Example:

```text
git add tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
git add docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
```

If and only if a safe test-only boundary helper/fix was required, also stage:

```text
git add tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
```

Then commit and push:

```text
git commit -m "test: expand local test DB boundary negative paths"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
