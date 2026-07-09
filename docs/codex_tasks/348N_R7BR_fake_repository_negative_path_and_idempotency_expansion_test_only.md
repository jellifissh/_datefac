# 348N-R7BR fake repository negative-path and idempotency expansion test-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-negative-path-idempotency-expansion
```

## Plain-language goal

R7BQ-QA approved the test-only fake repository / in-memory repository boundary. R7BR expands the fake repository negative-path, idempotency, conflict, copy-isolation, and batch atomicity coverage before any future database/schema work.

In plain Chinese: 这一轮继续补防线。R7BQ 做了一个假的内存 repository 边界，R7BR 专门拿重复写、冲突写、坏批次、伪造 receipt、绕路输入、隐藏生产配置、状态污染、对象引用污染去撞它。仍然只在 tests/agent 里做，不接真实数据库、不写文件、不建表、不加 migration、不接生产。

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
git log --oneline -65
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
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
docs/agent/348N_R7BQ_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_TEST_ONLY_REPORT.md
docs/agent/348N_R7BP_QA_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BP_REVIEW_QUEUE_PERSISTENCE_IMPLEMENTATION_PLANNING_SLICE_DOCS_ONLY.md
docs/agent/348N_R7BO_QA_PROJECT_DOCUMENTATION_SYNC_AFTER_REVIEW_QUEUE_PERSISTENCE_CONTRACT_MILESTONE_REVIEW.md
docs/agent/348N_R7BN_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
```

Review R7BQ files:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json
```

Review related test-only files read-only:

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

## Goal

Expand test-only negative-path and idempotency coverage for the fake repository / in-memory repository boundary.

The goal is not to add production persistence. The goal is to prove the fake repository boundary will not hide unsafe future repository semantics.

## Allowed tracked files

You may modify these test-only files:

```text
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
```

You may create this new fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json
```

Create this report:

```text
docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
```

Do not modify production code. Do not modify existing fixtures unless absolutely necessary; prefer the new R7BR fixture.

## Negative paths and idempotency cases to expand

Add focused tests for:

```text
repository default disabled / fail-closed behavior if supported by current boundary
missing explicit test-only repository flag
attempted production mode or production writer config
attempted DB DSN / connection string / table name / output path / file path config
attempted network/storage dependency marker
attempted receipt supplied by caller
attempted internal state supplied by caller
raw persistence candidate rows not produced by the persistence contract
raw schema alignment preview passed directly to repository
raw dry-run integration output passed directly to repository
raw writer preview passed directly to repository
adapter candidate output passed directly to repository
single-row write with missing required identity fields
single-row write with malformed idempotency_key
single-row write with malformed record_payload_hash
single-row write with forbidden fields nested at any depth
single-row write with full source_text or raw payload leakage
single-row write with clean_data intent
single-row write with delivery/export intent
single-row write with readiness override
single-row write with production timestamp policy
batch write where first row is valid and later row invalid
batch write where duplicate idempotency_key appears within the same batch
batch write where duplicate review_item_id appears within the same batch
same idempotency_key + same record_payload_hash retry is deterministic no-op or deterministic same receipt, according to documented policy
same idempotency_key + different record_payload_hash fails closed
same review_item_id + different idempotency_key fails closed unless explicitly documented as impossible
same review_item_id + same idempotency_key + changed payload fails closed
same record_payload_hash with different idempotency_key fails closed or has documented deterministic policy
write receipt is stable across retries
write receipt does not contain forbidden/test-only config or raw payload
write receipt cannot be mutated by caller to mutate repository state
read/list/get results cannot be mutated by caller to mutate repository state
repository instances do not share mutable state
repository reset/clear behavior, if present, is test-only and explicit
rollback/retraction behavior, if present, is simulated only and does not destructive-delete by default
```

Keep fixtures small. Do not include real PDF, DateFac Excel, full MinerU output, long source text, raw OCR, raw LLM/VLM output, DB secrets, or real connection strings.

## Required behavior to preserve

```text
fake repository remains under tests/agent only
in-memory only
no IO
no DB
no network
no production hook
no production dependency
no database model
no repository class in datefac_agent production code
no migration
no storage code
no output writer
no export path
no clean_data mutation
no delivery unblock
no readiness gate mutation
readiness_gates remain CLOSED
```

## Repository behavior expectations

The fake repository should make future real repository expectations explicit:

```text
writes are deterministic
write receipts are deterministic and test-only
retry behavior is deterministic
conflicts fail closed or are explicitly documented as deterministic no-op when same identity and same payload
silent duplicate insert is forbidden
batch writes are atomic by default
no partial success by default
internal state is deep-copied and isolated
read methods return copies
invalid writes do not mutate state
```

If existing R7BQ policy already chose a specific same-payload duplicate behavior, preserve it. Do not silently change the policy without documenting the reason in the report.

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
add production persistence implementation
add production repository/model/service code
add database schema
add migration
add database connection
add storage implementation
write output files
export delivery files
run MinerU/OCR/LLM/VLM or extraction
open readiness gates
claim production persistence exists
use git add .
use git add -A
```

## Test requirements

Add tests proving:

```text
bypass inputs are rejected
nested forbidden fields are rejected
raw payload leakage is rejected
production/DB/output config is rejected
idempotent retry is deterministic
same idempotency_key with different payload fails closed
same review_item_id conflict fails closed or is explicitly documented deterministic safe no-op
same batch duplicate conflict fails closed
batch failure leaves repository state unchanged
receipt mutation cannot mutate state
read/list/get copy mutation cannot mutate state
repository instance state is isolated
no IO/DB/network/production hook exists
```

Prefer table-driven tests where it keeps the suite easier to maintain.

## Report requirements

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BQ-QA recap
大白话说明
Negative-path expansion scope
Idempotency policy summary
Duplicate conflict policy summary
Batch atomicity summary
Mutation isolation summary
Receipt safety summary
Forbidden field and raw payload leakage summary
No-IO / no-DB / no-production-hook summary
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
idempotency_expansion_result（幂等扩展结果）=
duplicate_conflict_result（重复冲突结果）=
batch_atomicity_result（批次原子性结果）=
mutation_isolation_result（变更隔离结果）=
receipt_safety_result（receipt安全结果）=
forbidden_field_result（禁止字段结果）=
raw_payload_leakage_result（原始payload泄漏结果）=
production_config_rejection_result（生产配置拒绝结果）=
no_io_no_db_result（无IO无DB结果）=
test_only_boundary_result（test-only边界结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BR-QA fake repository negative-path and idempotency expansion review
```

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

## Commit and push

If validation passes and only allowed files changed, stage exactly the changed allowed files. Example:

```text
git add tests/agent/review_queue_fake_repository_boundary_348n.py
git add tests/agent/test_review_queue_fake_repository_boundary_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7br_fake_repository_negative_path_idempotency_fixture.json
git add docs/agent/348N_R7BR_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_TEST_ONLY_REPORT.md
git commit -m "test: expand fake repository negative paths"
git push origin pivot/348-agent-foundation
```

If `tests/agent/review_queue_fake_repository_boundary_348n.py` does not need changes, do not stage it.

Stop after push. Do not start the next task.
