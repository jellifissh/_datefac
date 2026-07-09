# 348N-R7BY-QA local test DB boundary negative-path expansion review

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = QA-review-only
```

## Plain-language goal

R7BY expanded the test-only negative-path suite for the local test DB adapter boundary. R7BY-QA reviews that expansion and confirms it stays test-only, fail-closed, and free of real database, IO, network, schema, migration, SQL, production hook, or readiness-gate behavior.

In plain Chinese: 这一轮只审查 R7BY 的坏路径测试。确认它只是在 `tests/agent` 里补防线，不连数据库、不写 SQL、不建表、不写 migration、不改生产代码。

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
docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md
docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md
docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md
docs/agent/348N_R7BV_QA_REPOSITORY_SKELETON_QA_REVIEW.md
```

Review R7BY files:

```text
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
```

Review related baseline files read-only if needed:

```text
tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
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

## QA checklist

Confirm:

```text
R7BY changed only the allowed files.
Only tests/agent boundary/helper, new negative-path tests, and report changed.
No datefac_agent production code changed.
No output/dependency/config/readiness files changed.
No real DB adapter, model, schema, migration, DB connection, SQL execution, file write, storage implementation, export/delivery path, production hook, or readiness gate change was added.
The modified boundary helper remains under tests/agent only and is clearly test-only.
The boundary helper imports without DB/storage/network dependencies.
Activation negative paths cover missing or invalid explicit flags, production/staging-like environment values, missing or unsupported local DB selection, environment-only activation, schema preview auto-activation, and repository factory auto-activation.
Production-looking config negative paths cover DB URLs, local file DB URLs, remote/non-local/cloud hosts, endpoints, connection strings, sensitive runtime config, schema/table/migration names, output/file paths, production writer config, and readiness override.
Candidate negative paths cover source_text/full_source_text, raw MinerU/Excel/parser/OCR/LLM/VLM payloads, unbounded evidence, clean_data payloads, export/delivery payloads, readiness override, production timestamp override, caller-supplied DB identifiers/rows, committed receipts, and internal adapter state.
Transaction/idempotency negative paths cover missing/malformed idempotency_key, missing/malformed record_payload_hash, same key with different hash, same review_item_id with conflicting identity, invalid rows anywhere in batch, duplicate conflicts, no partial success, and no silent duplicate insert.
Input config and candidate objects are not mutated.
Failure messages do not echo raw payloads or sensitive config values.
Source inspection confirms no forbidden DB/storage imports, SQL markers, file-write markers, network markers, Docker markers, or production fake-repository imports.
R7BY remains compatible with existing R7BX boundary tests.
R7BY does not weaken repository skeleton tests or fake repository tests.
R7BY does not claim local DB implementation, production persistence, client readiness, or production readiness.
Validation result matches R7BY summary: full tests/agent = 735 passed.
readiness_gates remain CLOSED.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, adapter implementations, migrations, schema files, R7BY files, existing reports, handoff docs, planning docs, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md
```

No other tracked files may change.

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

## Report sections

```text
Task ID
Preflight
Files reviewed
R7BY recap
大白话说明审查
Allowed file boundary review
Test-only boundary/helper review
Negative-path expansion scope review
Activation gate negative-path review
Production-looking config negative-path review
Environment activation negative-path review
Candidate raw payload negative-path review
clean_data/delivery/export/readiness negative-path review
Caller-supplied DB row / receipt / internal state negative-path review
Transaction/idempotency negative-path review
Input mutation safety review
Error leakage safety review
Source inspection review
Compatibility with R7BX boundary tests
No-DB / no-IO / no-network review
Validation outputs
Limitations
Decision
Recommended next task review
Data Result / 数据结果
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
negative_path_expansion_review_result（负路径扩展审查结果）=
activation_gate_negative_path_review_result（激活门负路径审查结果）=
production_config_negative_path_review_result（生产配置负路径审查结果）=
environment_activation_negative_path_review_result（环境激活负路径审查结果）=
candidate_payload_negative_path_review_result（候选payload负路径审查结果）=
clean_data_delivery_negative_path_review_result（clean_data/交付负路径审查结果）=
caller_supplied_db_state_negative_path_review_result（调用方伪造DB状态负路径审查结果）=
transaction_idempotency_negative_path_review_result（事务/幂等负路径审查结果）=
input_mutation_safety_review_result（输入变更安全审查结果）=
error_leakage_safety_review_result（错误泄漏安全审查结果）=
source_inspection_review_result（源码检查审查结果）=
no_db_no_io_no_network_review_result（无DB/IO/网络审查结果）=
compatibility_with_r7bx_review_result（与R7BX兼容审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BZ local test DB boundary handoff checkpoint
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md
git commit -m "docs: add R7BY QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
