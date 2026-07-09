# 348N-R7BV repository skeleton QA

## Task sizing

```text
task_size = medium
recommended_reasoning_level = high
execution_mode = test-only-repository-skeleton-QA-hardening
```

## Plain-language goal

R7BU-QA approved the disabled-by-default review_queue repository interface skeleton. R7BV adds a focused test-only QA hardening layer around that skeleton, proving it stays disabled, fail-closed, dependency-free, and unable to perform persistence side effects.

In plain Chinese: R7BU 已经把 repository 骨架放进 `datefac_agent/`，R7BU-QA 已经审过。R7BV 不是继续做数据库，也不是接生产，而是再加一组更硬的 QA 测试，专门撞这个骨架：看它会不会偷偷接受 DB 配置、环境变量、路径、生产开关、raw payload、clean_data/delivery/export 意图，或者悄悄保存状态。结论必须仍然是默认关闭、fail-closed、无 DB、无 IO、无网络、无生产 hook。

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
git log --oneline -85
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
docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md
docs/agent/348N_R7BU_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_NO_DB_CONNECTION_REPORT.md
docs/agent/348N_R7BT_QA_SCHEMA_MIGRATION_QA_DOCS_ONLY_REVIEW.md
docs/agent/348N_R7BT_SCHEMA_MIGRATION_QA_DOCS_ONLY.md
docs/agent/348N_R7BS_QA_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_REVIEW.md
docs/agent/348N_R7BS_DATABASE_SCHEMA_AND_MIGRATION_DESIGN_DOCS_ONLY.md
docs/agent/348N_R7BR_QA_FAKE_REPOSITORY_NEGATIVE_PATH_AND_IDEMPOTENCY_EXPANSION_REVIEW.md
docs/agent/348N_R7BQ_QA_FAKE_REPOSITORY_IN_MEMORY_REPOSITORY_BOUNDARY_CONTRACT_REVIEW.md
```

Review current repository skeleton and tests:

```text
datefac_agent/review/review_queue_repository.py
tests/agent/test_review_queue_repository_skeleton_348n.py
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

Create a test-only QA hardening suite for `datefac_agent/review/review_queue_repository.py`.

This task should strengthen confidence that the skeleton is still only a disabled boundary and cannot be mistaken for a persistence implementation.

## Allowed tracked files

Create exactly:

```text
tests/agent/test_review_queue_repository_skeleton_qa_348n.py
docs/agent/348N_R7BV_REPOSITORY_SKELETON_QA_REPORT.md
```

You may modify the skeleton only if a QA test exposes a boundary bug that cannot be addressed otherwise:

```text
datefac_agent/review/review_queue_repository.py
```

Default expectation: no production code change. If the skeleton is modified, the report must explain why, and the change must remain strictly disabled-by-default with no DB/IO/network/storage behavior.

Do not modify existing tests or fixtures unless absolutely necessary.

## Required QA test coverage

Add focused tests proving:

```text
repository module imports without DB/storage/network dependencies
public factory remains disabled by default
factory cannot be enabled by arbitrary kwargs
factory cannot be enabled by production-like config dicts
factory cannot be enabled by environment variables
write_batch always fails closed on the disabled repository
get_by_review_item_id/list_by_run_id fail closed or preserve explicit disabled behavior
error type is specific and stable
error messages include a disabled reason but do not leak raw payloads or secrets
input candidates are not mutated after failed write
input config dictionaries are not mutated
caller-supplied receipt-like objects are rejected or ignored fail-closed
caller-supplied internal-state-like objects are rejected or ignored fail-closed
production-looking values are rejected or fail closed: DSN, connection string, table name, output path, endpoint, production flag, readiness override
raw payload values are never echoed: source_text, raw_mineru_payload, raw_excel_payload, raw_parser_payload, raw_ocr_payload, raw_llm_payload, raw_vlm_payload
clean_data intent is rejected or absent
delivery/export intent is rejected or absent
readiness gate mutation is absent
repository object has no persistence state that grows after failed writes
repository skeleton source contains no forbidden DB/storage imports
repository skeleton source contains no SQL execution markers
repository skeleton source contains no filesystem write markers
repository skeleton source contains no network call markers
repository skeleton source does not import tests/agent fake repository code
```

Keep tests lightweight and deterministic. Do not create temp files. Do not monkeypatch real database libraries. Do not call external systems.

## Optional skeleton adjustment rules

If the existing skeleton does not expose enough explicit fail-closed behavior for the QA tests, you may add the smallest safe adjustment to the skeleton only.

Allowed skeleton adjustments:

```text
clearer disabled exception message
stricter constructor/factory config rejection
stronger defensive copy / no-mutation behavior
explicit disabled reason constant
explicit method stubs that raise disabled error
```

Forbidden skeleton adjustments:

```text
any real persistence behavior
in-memory production state
DB connection placeholder that accepts DSN
table/schema/migration name as runtime config
SQL construction/execution
file writes
network/storage clients
environment-variable activation
production hook
clean_data/delivery/export integration
readiness gate mutation
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
R7BU-QA recap
大白话说明
QA hardening scope
Files changed
Repository skeleton behavior reviewed
Disabled-by-default QA
Factory/config rejection QA
Environment activation QA
Write/read fail-closed QA
Error and leakage QA
Input/config mutation safety QA
Production-looking config rejection QA
Raw payload rejection / non-echo QA
clean_data/delivery/export/readiness boundary QA
Source inspection QA
Fake repository compatibility
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
repository_skeleton_qa_result（repository骨架QA结果）=
disabled_by_default_qa_result（默认关闭QA结果）=
factory_config_rejection_result（factory配置拒绝结果）=
environment_activation_rejection_result（环境变量激活拒绝结果）=
write_read_fail_closed_result（读写fail-closed结果）=
error_leakage_safety_result（错误泄漏安全结果）=
input_mutation_safety_result（输入变更安全结果）=
production_config_rejection_result（生产配置拒绝结果）=
raw_payload_non_echo_result（原始payload不回显结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
source_inspection_result（源码检查结果）=
no_db_no_io_no_network_result（无DB/IO/网络结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BV-QA repository skeleton QA review
```

## Validation commands

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

If validation passes and only allowed files changed, stage exactly the changed allowed files. Example:

```text
git add tests/agent/test_review_queue_repository_skeleton_qa_348n.py
git add docs/agent/348N_R7BV_REPOSITORY_SKELETON_QA_REPORT.md
```

If and only if the skeleton required a safe boundary fix, also stage:

```text
git add datefac_agent/review/review_queue_repository.py
```

Then commit and push:

```text
git commit -m "test: harden review queue repository skeleton QA"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
