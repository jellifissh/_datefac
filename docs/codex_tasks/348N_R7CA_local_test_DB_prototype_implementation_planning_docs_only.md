# 348N-R7CA local test DB prototype implementation planning docs-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = docs-only-implementation-planning
```

## Plain-language goal

R7BZ-QA approved the local test DB boundary handoff checkpoint. R7CA plans the first future implementation slice for a local test DB prototype, but still does not implement the adapter, does not connect to a database, does not create schema or migration files, and does not change production code.

In plain Chinese: 这一轮只做“实施计划”，把下一步如果真要做 local test DB prototype，应该先做哪一小刀、改哪些文件、哪些文件绝对不能动、怎么验证写清楚。不是现在写 adapter，不是现在连 SQLite/PostgreSQL，不是现在建表，不是现在写 SQL。

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
git log --oneline -120
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
docs/agent/348N_R7BZ_QA_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7BZ_LOCAL_TEST_DB_BOUNDARY_HANDOFF_CHECKPOINT.md
docs/agent/348N_R7BY_QA_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_REVIEW.md
docs/agent/348N_R7BY_LOCAL_TEST_DB_BOUNDARY_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BX_QA_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_REVIEW.md
docs/agent/348N_R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_SKELETON_TEST_ONLY_REPORT.md
docs/agent/348N_R7BW_QA_LOCAL_TEST_DB_PROTOTYPE_DESIGN_REVIEW.md
docs/agent/348N_R7BU_QA_REPOSITORY_INTERFACE_SKELETON_DISABLED_BY_DEFAULT_REVIEW.md
```

Review read-only:

```text
tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
datefac_agent/review/review_queue_repository.py
tests/agent/test_review_queue_repository_skeleton_348n.py
tests/agent/test_review_queue_repository_skeleton_qa_348n.py
tests/agent/review_queue_fake_repository_boundary_348n.py
tests/agent/test_review_queue_fake_repository_boundary_348n.py
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
```

## Goal

Create a docs-only implementation plan for the next safe local test DB prototype slice.

The plan must be specific enough for a future task, but must not implement anything in R7CA.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md
```

No other tracked files may change.

## Required planning content

The implementation plan must cover:

```text
1. Current baseline after R7BZ-QA.
2. Why R7CA remains docs-only.
3. Smallest safe next implementation slice.
4. Candidate file plan for the future implementation task.
5. Candidate test plan for the future implementation task.
6. Candidate local DB choice for first implementation slice.
7. Activation gate requirements.
8. Config allowlist requirements.
9. Schema creation strategy for local-only test context.
10. Transaction/rollback test strategy.
11. Idempotency/uniqueness test strategy.
12. Raw payload exclusion strategy.
13. Cleanup/teardown strategy.
14. No-production-connection guarantees.
15. clean_data/delivery/export separation guarantees.
16. Validation commands for future implementation.
17. Stop conditions for future implementation.
18. Risks and open questions.
19. Recommended next task.
```

## Current baseline to state

```text
repository skeleton remains disabled by default
local test DB boundary exists only under tests/agent
negative-path expansion exists only under tests/agent
no real local DB adapter exists
no real DB connection exists
no SQL execution exists
no schema exists
no migration exists
no production repository exists
no review_queue_builder integration exists
no clean_data integration exists
no delivery/export integration exists
latest known full tests/agent = 735 passed
readiness_gates remain CLOSED
```

## Future implementation slice guidance

The plan should recommend a very small future implementation slice, such as:

```text
create a test-only/local-test-only adapter module or fixture that uses a local in-memory SQLite database only inside tests
create schema inside test setup only
tear down all state inside tests
keep production repository skeleton disabled by default
keep local DB adapter unavailable from production factory
prove activation requires explicit local-test config object, not environment variables alone
prove no production-looking DSN or file path is accepted
prove one successful local-only insert path only after all gates pass
```

The plan may also choose an even more conservative first slice if justified.

## Required boundaries for future implementation plan

The future implementation plan must require:

```text
no production code integration by default
no automatic activation from environment variables
no production DSN
no remote host
no file path DB by default
no migration files in the first implementation slice unless separately approved
no review_queue_builder integration
no clean_data mutation
no delivery/export trigger
no readiness gate mutation
no raw payload storage
no source_text storage
no claim of production persistence
```

## Required non-goals for R7CA

Explicitly state R7CA does not:

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
add file writes
add output writer
run extraction
run MinerU/OCR/LLM/VLM
connect to SQLite/PostgreSQL/Docker
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
R7BZ-QA recap
大白话说明
Planning scope
Current baseline
Smallest safe future implementation slice
Candidate future files
Candidate future tests
Candidate local DB choice
Activation gate plan
Config allowlist plan
Local-only schema setup plan
Transaction and rollback plan
Idempotency and uniqueness plan
Raw payload exclusion plan
Cleanup and teardown plan
No-production-connection guarantees
clean_data/delivery/export separation
Future validation commands
Stop conditions
Risks and open questions
Non-goals
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
implementation_planning_result（实施计划结果）=
smallest_safe_slice_result（最小安全切片结果）=
candidate_file_plan_result（候选文件计划结果）=
candidate_test_plan_result（候选测试计划结果）=
activation_gate_plan_result（激活门计划结果）=
config_allowlist_plan_result（配置白名单计划结果）=
local_schema_setup_plan_result（本地schema设置计划结果）=
transaction_rollback_plan_result（事务回滚计划结果）=
idempotency_uniqueness_plan_result（幂等唯一性计划结果）=
raw_payload_exclusion_plan_result（原始payload排除计划结果）=
cleanup_teardown_plan_result（清理/teardown计划结果）=
no_production_connection_plan_result（无生产连接计划结果）=
clean_data_delivery_boundary_result（clean_data/交付边界结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7CA-QA local test DB prototype implementation planning review
```

## Validation commands

Docs-only planning, but still verify the current boundary chain remains green.

```text
python -m py_compile tests/agent/review_queue_local_test_db_adapter_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py
python -m py_compile datefac_agent/review/review_queue_repository.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_348n.py
python -m py_compile tests/agent/test_review_queue_repository_skeleton_qa_348n.py
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_negative_path_348n.py -q
python -m pytest tests/agent/test_review_queue_local_test_db_adapter_boundary_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_qa_348n.py -q
python -m pytest tests/agent/test_review_queue_repository_skeleton_348n.py -q
python -m pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Commit and push

If validation passes and only the planning report is created, stage exactly:

```text
git add docs/agent/348N_R7CA_LOCAL_TEST_DB_PROTOTYPE_IMPLEMENTATION_PLANNING_DOCS_ONLY.md
git commit -m "docs: plan local test DB prototype implementation"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
