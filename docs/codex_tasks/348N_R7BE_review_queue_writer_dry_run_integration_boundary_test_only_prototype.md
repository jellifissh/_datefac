# 348N-R7BE review-queue writer dry-run integration boundary test-only prototype

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-integration-boundary-prototype
```

## Plain-language goal

R7BD-QA confirmed the dry-run integration boundary design is safe. R7BE may now create a test-only integration boundary prototype.

This is still not production integration. It must live under tests, require explicit test-only enable, call only the test-only in-memory writer contract, and return dry-run preview only.

In plain Chinese: 这一步只在测试区做一条“安全传送带”：adapter 候选输出 -> dry-run integration boundary -> test-only writer 预览。它不写数据库、不建表、不导出、不接生产。

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
docs/agent/348N_R7BD_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN_REVIEW.md
docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
docs/agent/348N_R7BB_QA_DISABLED_ADAPTER_REVIEW_QUEUE_PERSISTENCE_PLANNING_SLICE_REVIEW.md
```

Review current slices:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
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

Create a test-only dry-run integration boundary prototype that connects validated adapter candidate output to the test-only in-memory review_queue writer contract.

It should prove the boundary shape without adding any production hook or real persistence.

## Allowed tracked files

Create exactly:

```text
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
```

Do not modify production code. Do not modify existing tests or fixtures unless absolutely required; prefer the new test-only files above.

## Prototype requirements

The integration boundary must enforce:

```text
default disabled fail-closed
explicit test-only enable required
accept only validated adapter candidate output
reject raw MinerU-like payload
reject raw Excel-like payload
reject raw parser-like payload
reject direct user payload
reject full source_text anywhere
reject readiness_gates not CLOSED
reject schema mismatch
call only tests/agent/review_queue_writer_contract_348n.py
return dry-run preview only
include an integration envelope only if deterministic
preserve adapter metadata unchanged
preserve writer dry-run preview unchanged except allowed deterministic envelope metadata
preserve review_item_id, audit_hash, run_id, adapter_version, contract_version, input_file_hashes
preserve idempotency keys from writer output
non-VERIFIED rows remain review-bound
unresolved rows retain blocked_delivery_reason
corrected rows retain re-audit requirement
VERIFIED rows do not become clean_data
no DB write
no file write
no export
no migration
no production pipeline hook
no parser/model/MinerU/OCR/VLM call
readiness_gates remain CLOSED
```

## Suggested fixture cases

Create a small curated fixture with:

```text
valid_adapter_candidate_to_writer_preview
valid_mixed_verified_and_non_verified_candidate
valid_unresolved_blocked_delivery_candidate
valid_corrected_reaudit_required_candidate
invalid_raw_mineru_like_payload
invalid_raw_excel_like_payload
invalid_raw_parser_like_payload
invalid_direct_user_payload
invalid_full_source_text_payload
invalid_readiness_open_payload
invalid_schema_mismatch_payload
invalid_clean_data_intent_payload
```

Keep it small. No real PDF, no DateFac Excel, no full MinerU output, no large text.

## Test requirements

Add tests proving:

```text
default disabled integration fails closed
explicit test-only enable is required
valid adapter candidate reaches test-only writer preview
integration output is dry-run only
writer preview records are preserved conservatively
adapter metadata passes through unchanged
idempotency is stable end-to-end
same input retry produces identical dry-run result
input mutation after call cannot mutate output
raw MinerU-like input rejected before writer call
raw Excel-like input rejected before writer call
raw parser-like input rejected before writer call
direct user payload rejected
full source_text rejected before writer call
readiness_gates OPEN rejected
clean_data write intent rejected
schema mismatch rejected
VERIFIED rows do not become clean_data
non-VERIFIED rows remain review-bound
unresolved rows retain blocked_delivery_reason
corrected rows retain re-audit requirement
no IO/no DB/no export/no hook behavior exists
```

## Strict boundaries

Forbidden:

```text
modify datefac_agent production code
add production integration implementation
add database model
add repository class
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
R7BD-QA recap
大白话说明
Test-only integration boundary scope
Integration flow
Input validation
Writer call boundary
Dry-run output envelope
Idempotency and duplicate prevention
Audit metadata pass-through
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
integration_boundary_result（集成边界结果）=
dry_run_preview_result（dry-run预览结果）=
fixture_result（fixture结果）=
input_rejection_result（输入拒绝结果）=
writer_call_boundary_result（writer调用边界结果）=
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
348N-R7BE-QA review-queue writer dry-run integration boundary test-only prototype review
```

## Validation commands

```text
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
pytest tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py -q
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
git add tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
git add tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
git add docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
git commit -m "test: add dry-run writer integration boundary prototype"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
