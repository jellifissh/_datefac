# 348N-R7BG review-queue writer dry-run integration boundary handoff checkpoint

## Task sizing

```text
task_size = small
recommended_reasoning_level = high
execution_mode = docs-only-handoff-checkpoint
```

## Plain-language goal

R7BE built a test-only dry-run integration boundary, and R7BF hardened its negative paths. R7BG is a checkpoint before moving further.

Do not add functionality. Summarize the current adapter -> dry-run integration boundary -> test-only writer chain, what is proven by tests, what remains forbidden, and what the next safe task should be.

In plain Chinese: 这一轮是阶段总结。把“adapter 候选输出如何经过测试区安全传送带到 writer dry-run 预览”讲清楚，尤其要讲清它仍然不写库、不建表、不导出、不接生产。

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
git log --oneline -20
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
docs/agent/348N_R7BF_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REVIEW.md
docs/agent/348N_R7BF_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_NEGATIVE_PATH_TEST_ONLY_COVERAGE_REPORT.md
docs/agent/348N_R7BE_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BD_QA_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN_REVIEW.md
docs/agent/348N_R7BD_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_DESIGN.md
docs/agent/348N_R7BC_QA_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BC_DISABLED_ADAPTER_REVIEW_QUEUE_WRITER_TEST_ONLY_CONTRACT_PROTOTYPE_REPORT.md
```

Review current slices read-only:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
```

Review related modules read-only if needed:

```text
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
```

## Goal

Create a docs-only handoff checkpoint report for the dry-run integration boundary phase.

The report must explain:

```text
what exists now
which files are test-only
how the flow works
what the positive path proves
what the negative-path hardening proves
what remains forbidden
why readiness_gates remain CLOSED
what risks remain
what next task should be
```

## Allowed tracked file

Create exactly:

```text
docs/agent/348N_R7BG_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT.md
```

No other tracked files may change.

## Required plain-language summary

Include a short section explaining the current phase like this, but write it in your own words:

```text
现在已经有一条测试区安全链路：adapter 候选输出可以在显式 test-only 开关下进入 dry-run integration boundary，再调用 test-only writer 生成 review_queue 预览。它仍然不会写数据库、不会建表、不会导出、不会写 clean_data、不会接生产主流程。
```

## Report requirements

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BE/R7BF recap
大白话总览
Current test-only chain
Current files and ownership
Positive-path coverage summary
Negative-path hardening summary
Writer-preview hardening summary
Test-only token and config boundary
Accepted and rejected inputs
Dry-run output boundary
Idempotency and duplicate prevention
Audit metadata pass-through
Evidence preview and source_text boundary
clean_data safety boundary
Delivery gate boundary
Corrected row and re-audit policy
No-hook and no-IO boundary
Readiness gates status
Remaining risks
Recommended next task
Data Result / 数据结果
```

## Checklist

Confirm and document:

```text
All new integration and writer logic is under tests/agent.
No datefac_agent production code is required for this phase.
The integration boundary is disabled by default.
Explicit test-only enable is required.
The writer config must be exact test-only config.
Valid adapter candidate output reaches dry-run writer preview.
Raw MinerU-like input is rejected.
Raw Excel-like input is rejected.
Raw parser-like input is rejected.
Direct user payload is rejected.
Direct writer-preview shaped payload is rejected.
Full source_text is rejected anywhere.
readiness_gates OPEN is rejected.
clean_data intent is rejected.
Malformed and minimal invalid payloads are rejected.
Unsafe or production-like writer preview is blocked.
Dry-run output remains dry_run_only and in-memory.
review_item_id, audit_hash, run_id, adapter_version, contract_version, input_file_hashes, and idempotency keys are preserved.
VERIFIED does not become STRONG_EVIDENCE or clean_data.
non-VERIFIED rows remain review-bound.
Unresolved rows retain blocked_delivery_reason.
Corrected rows retain re-audit requirement.
No DB/file/export/parser/model/MinerU/OCR/VLM/production call exists.
readiness_gates remain CLOSED.
```

## Forbidden for this task

```text
Do not modify production code.
Do not modify tests.
Do not modify fixtures.
Do not add implementation.
Do not add database models, repositories, migrations, or storage code.
Do not write output files.
Do not run MinerU/OCR/LLM/VLM or extraction.
Do not open readiness gates.
Do not use git add .
Do not use git add -A.
```

## Required Data Result

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
handoff_checkpoint_result（交接检查点结果）=
plain_language_result（大白话说明结果）=
current_chain_summary_result（当前链路总结结果）=
positive_path_summary_result（正路径总结结果）=
negative_path_summary_result（负路径总结结果）=
writer_preview_hardening_summary_result（writer预览加固总结结果）=
test_only_boundary_result（test-only边界结果）=
dry_run_boundary_result（dry-run边界结果）=
idempotency_metadata_result（幂等与元数据结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_gate_boundary_result（交付闸门边界结果）=
remaining_risks_result（剩余风险结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BG-QA review-queue writer dry-run integration boundary handoff checkpoint review
```

## Validation commands

This is docs-only, but still verify the current test-only chain remains green.

```text
python -m py_compile tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
python -m py_compile tests/agent/review_queue_writer_contract_348n.py
python -m py_compile tests/agent/test_review_queue_writer_contract_348n.py
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
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

If validation passes and only the allowed report is created, stage exactly:

```text
git add docs/agent/348N_R7BG_REVIEW_QUEUE_WRITER_DRY_RUN_INTEGRATION_BOUNDARY_HANDOFF_CHECKPOINT.md
git commit -m "docs: add R7BG dry-run integration handoff checkpoint"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
