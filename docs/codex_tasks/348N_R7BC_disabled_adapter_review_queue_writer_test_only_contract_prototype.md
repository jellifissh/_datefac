# 348N-R7BC disabled adapter review-queue writer test-only contract prototype

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-contract-prototype
```

## Plain-language goal

R7BB-QA confirmed the future review_queue persistence plan is safe. R7BC may now build a test-only in-memory writer contract prototype.

This is still not real persistence. Do not write a database row, do not create migrations, do not export files, and do not connect to the production pipeline.

In plain Chinese: 这一步只是在测试区模拟“以后怎么把 adapter 候选复核项变成可持久化记录”。它像数据库写入前的沙盘演练，不是真的写库。

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
git log --oneline -15
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
docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BB_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE.md
docs/agent/348N_R7BA_QA_DISABLED_ADAPTER_CONTRACT_SUMMARY_AND_HANDOFF_CHECKPOINT_REVIEW.md
docs/agent/348N_R7AZ_QA_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REVIEW.md
docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md
```

Review current adapter slice:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
```

Review related modules read-only:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a test-only in-memory review_queue writer contract prototype that accepts only safe adapter candidate output and returns a dry-run persistence preview.

The prototype must prove the future writer contract without adding real persistence.

## Allowed tracked files

Create exactly:

```text
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
```

Do not modify production code. Do not modify existing tests or fixtures unless absolutely required; prefer new test-only files above.

## Prototype requirements

The test-only writer contract should be in memory only. It should accept candidate output shaped like the disabled adapter output and return a dry-run preview of review_queue records.

It must enforce:

```text
writer disabled by default
explicit test-only enable required
input must be adapter candidate output, not raw MinerU/raw Excel/raw parser/full source_text
readiness_gates must remain CLOSED
no clean_data write
no export write
no filesystem write
no database write
only review-bound records are previewed for persistence
VERIFIED rows are not auto-persisted as clean records
non-VERIFIED rows can become review_queue preview records
unresolved rows retain blocked_delivery_reason
corrected rows remain re-audit-required unless future gate exists
bounded evidence_preview only
full source_text rejected anywhere in payload
run_id, adapter_version, contract_version, input_file_hashes retained
review_item_id and audit_hash retained
idempotency_key deterministic
retrying same input produces same dry-run records and no duplicate plan
schema mismatch fails closed
```

## Suggested dry-run record fields

Use a minimal in-memory record shape such as:

```text
review_item_id
run_id
source_file_hash
input_file_hashes
adapter_version
contract_version
audit_hash
metric_name
period
candidate_value
agreement_status
review_status
reviewer_action
review_reason
blocked_delivery_reason
evidence_preview
source_trace
idempotency_key
dry_run_only
```

Do not add created_at unless it is deterministic in tests. Avoid wall-clock timestamps.

## Fixture requirements

Create a small curated fixture:

```text
valid_adapter_candidate_payload
candidate_payload_with_verified_only
candidate_payload_with_non_verified_review_bound_rows
candidate_payload_with_unresolved_blocked_delivery_rows
candidate_payload_with_corrected_reaudit_required_row
invalid_raw_mineru_like_payload
invalid_raw_excel_like_payload
invalid_full_source_text_payload
invalid_readiness_open_payload
invalid_clean_data_write_payload
invalid_missing_audit_metadata_payload
invalid_duplicate_idempotency_collision_payload
```

Keep it small. No real PDFs, no DateFac Excel, no full MinerU output, no large source text.

## Test requirements

Add tests proving:

```text
default disabled writer fails closed
explicit test-only enable is required
valid candidate output produces dry-run preview only
preview records contain required fields
preview records are review_queue records, not clean_data records
VERIFIED-only input produces no clean persistence and remains conservative
non-VERIFIED rows produce review-bound preview records
unresolved rows keep blocked_delivery_reason
corrected rows keep re-audit requirement
idempotency_key is deterministic
same input on retry yields same preview and no duplicate plan
input mutation after call cannot mutate output
raw MinerU-like input rejected
raw Excel-like input rejected
full source_text rejected
readiness_gates not CLOSED rejected
clean_data write intent rejected
missing audit metadata rejected
schema mismatch rejected
no IO behavior exists
```

## Strict boundaries

Forbidden:

```text
modify datefac_agent production code
add database model
add repository class
add writer implementation outside tests
add migrations
write output files
export delivery files
run MinerU/OCR/LLM/VLM or real extraction
open readiness gates
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED directly to clean_data
use git add .
use git add -A
```

## Report requirements

The report must include a short 大白话说明 section.

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BB-QA recap
大白话说明
Test-only writer contract scope
In-memory dry-run design
Input contract
Dry-run record shape
Idempotency and duplicate prevention
Audit metadata retention
Evidence preview and source_text boundary
clean_data safety boundary
Delivery gate boundary
Corrected row and re-audit policy
Failure and fail-closed behavior
No-hook and no-IO boundary
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
writer_contract_result（writer契约结果）=
dry_run_preview_result（dry-run预览结果）=
fixture_result（fixture结果）=
input_rejection_result（输入拒绝结果）=
idempotency_result（幂等结果）=
audit_metadata_result（审计元数据结果）=
evidence_boundary_result（证据边界结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_gate_boundary_result（交付闸门边界结果）=
no_hook_no_io_result（无hook无IO结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BC-QA disabled adapter review-queue writer test-only contract prototype review
```

## Validation commands

```text
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
pytest tests/agent/test_review_queue_writer_contract_348n.py -q
pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

## Commit and push

If validation passes and only allowed files changed, stage exactly:

```text
git add tests/agent/review_queue_writer_contract_348n.py
git add tests/agent/test_review_queue_writer_contract_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
git add docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
git commit -m "test: add review queue writer contract prototype"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
