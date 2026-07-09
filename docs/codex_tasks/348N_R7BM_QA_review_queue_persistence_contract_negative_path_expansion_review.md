# 348N-R7BM-QA review_queue persistence contract negative-path expansion review

## Task sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
```

## Plain-language goal

R7BM expanded negative-path coverage for the test-only review_queue persistence contract. R7BM-QA checks that the new hardening is correct, complete, and still test-only.

In plain Chinese: 这一轮只审查 R7BM 的补防线是否靠谱。重点确认坏输入、绕路输入、嵌套脏字段、重复幂等键、伪造候选、批次异常都会 fail closed；同时确认没有写库、没有建表、没有导出、没有接生产。

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
git log --oneline -40
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
docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
```

Review R7BM files:

```text
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json
docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
```

Review related slices read-only:

```text
tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
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
R7BM changed only allowed test-only files, fixture, and report.
No datefac_agent production code was modified.
No database model, repository class, migration, storage code, output writer, export path, production hook, or readiness gate change was added.
The contract still lives under tests/agent only.
The persistence contract remains disabled by default and fail-closed.
Explicit test-only persistence flag is still required.
Only validated schema alignment preview payloads are accepted.
Schema alignment bypass remains rejected.
Direct dry-run integration output remains rejected.
Direct writer preview output remains rejected.
Direct adapter candidate output remains rejected.
User-provided direct persistence candidate remains rejected.
Nested forbidden fields are rejected at any depth.
Nested full source_text is rejected.
Nested raw MinerU/raw Excel/raw parser/raw LLM/VLM payloads are rejected.
Nested clean_data intent is rejected.
Nested delivery/export intent is rejected.
Nested production writer config is rejected.
Nested readiness override is rejected.
Test-only token/config leaking into candidate row is rejected.
Mixed valid and invalid batch fails as a whole.
Batch failure returns no partial candidate batch.
record_payload_hash cannot be user supplied.
record_payload_hash is derived deterministically.
idempotency_key consistency is enforced.
duplicate idempotency_key conflicts fail closed.
duplicate review_item_id conflicts fail closed.
source/hash identity shape is enforced.
evidence_preview remains bounded.
empty or insufficient evidence is handled according to documented review_reason policy.
non-list input_file_hashes is rejected.
missing source_file_hash plus empty input_file_hashes is rejected.
non-string metric_name or period is rejected.
NaN/Infinity-like candidate values are rejected if applicable.
created_at production timestamp policy is rejected.
reviewer_action cannot imply auto-approve to clean_data.
review_status cannot imply delivery unblock without review.
unexpected persistence destination/table/DSN/output path is rejected.
Input mutation cannot mutate returned candidates.
VERIFIED does not imply STRONG_EVIDENCE.
VERIFIED does not auto-write clean_data.
non-VERIFIED remains review-bound.
persistence candidate does not trigger delivery.
persistence candidate does not mutate clean_data.
persistence candidate does not open readiness gates.
No IO, DB, export, parser, model, MinerU, OCR, VLM, or production call exists.
readiness_gates remain CLOSED.
```

## Strict boundaries

Only create the QA report. Do not modify production code, tests, fixtures, outputs, dependencies, integrations, database models, writer implementations, migrations, or readiness gates. Do not run extraction systems. Do not use broad staging.

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
```

No other tracked files may change.

## Validation commands

```text
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
R7BM recap
大白话说明审查
Negative-path expansion scope review
Contract hardening review
Fixture coverage review
Nested forbidden field coverage review
Batch fail-closed coverage review
Idempotency and hash consistency review
Record payload hash derivation review
Duplicate conflict coverage review
Evidence boundary review
clean_data and delivery/export boundary review
No-hook and no-IO boundary review
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
contract_hardening_review_result（契约加固审查结果）=
fixture_coverage_review_result（fixture覆盖审查结果）=
nested_forbidden_field_review_result（嵌套禁止字段审查结果）=
batch_fail_closed_review_result（批次fail-closed审查结果）=
idempotency_consistency_review_result（幂等一致性审查结果）=
record_payload_hash_review_result（record_payload_hash审查结果）=
duplicate_conflict_review_result（重复冲突审查结果）=
evidence_boundary_review_result（证据边界审查结果）=
clean_data_boundary_review_result（clean_data边界审查结果）=
delivery_export_boundary_review_result（交付导出边界审查结果）=
no_hook_no_io_review_result（无hook无IO审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BN review_queue persistence contract handoff checkpoint
```

## Commit and push

If validation passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7BM_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_REVIEW.md
git commit -m "docs: add R7BM QA review"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
