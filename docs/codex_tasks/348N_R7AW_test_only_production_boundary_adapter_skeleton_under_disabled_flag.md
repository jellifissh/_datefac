# 348N-R7AW test-only production-boundary adapter skeleton under disabled flag

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = disabled-flag-skeleton-only
```

## Reason

R7AV-QA passed. The integration plan is conservative and rollback-ready. R7AW may create the first inert production-boundary adapter skeleton, but it must stay disabled by default, have no pipeline hook, perform no I/O, and keep readiness gates closed.

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
git log --oneline -12
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
docs/agent/348N_R7AV_QA_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST_REVIEW.md
docs/agent/348N_R7AV_PRODUCTION_BOUNDARY_ADAPTER_INTEGRATION_PLAN_AND_ROLLBACK_CHECKLIST.md
docs/agent/348N_R7AU_QA_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REVIEW.md
docs/agent/348N_R7AU_TEST_ONLY_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_CONTRACT_PROTOTYPE_REPORT.md
```

Inspect read-only:

```text
tests/agent/production_boundary_review_queue_adapter_contract_348n.py
tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
tests/agent/discrepancy_review_queue_integration_boundary_348n.py
tests/agent/discrepancy_review_queue_policy_348n.py
datefac_agent/review/review_queue_builder.py
datefac_agent/review/clean_candidate_policy.py
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/delivery/evidence_index_writer.py
```

## Goal

Create a minimal production-boundary adapter skeleton that is disabled by default and tested with curated data only. This is not a production hookup.

The adapter must not be imported by any production pipeline. It must not write review_queue records, clean_data, evidence_index, delivery files, database records, or local output files.

## Allowed tracked files

Create exactly these files:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
docs/agent/348N_R7AW_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REPORT.md
```

No other tracked files may change.

## Required skeleton behavior

The new module must provide an explicit disabled-by-default boundary, for example:

```text
ProductionBoundaryReviewQueueAdapterConfig(enabled=False, contract_version="r7aw-disabled-skeleton")
build_production_boundary_review_queue_adapter_output(payload, config)
```

Required behavior:

```text
1. enabled defaults to false.
2. When enabled is false, adapter fails closed with a structured disabled result or explicit controlled exception.
3. The skeleton has no side effects.
4. The skeleton accepts only validated boundary output shape when explicitly enabled in tests.
5. Raw MinerU-like input is rejected.
6. Raw Excel-like input is rejected.
7. Full source_text input is rejected.
8. VERIFIED rows do not automatically enter clean_data.
9. non-VERIFIED rows map to review_queue candidate items.
10. unresolved rows map to blocked delivery candidate rows.
11. evidence_preview remains bounded.
12. audit metadata is preserved.
13. review_item_id and audit_hash are deterministic.
14. readiness gates remain closed.
```

## Fixture requirements

Use a small curated fixture. Include:

```text
one valid boundary-output case
one disabled-default case
one raw MinerU-like invalid case
one raw Excel-like invalid case
one full-source-text invalid case
one VERIFIED row
one DISAGREED row
one AMBIGUOUS row
one unresolved row
one corrected-but-re-audit-required row
```

## Tests must cover

```text
default disabled fail-closed behavior
explicit test enable behavior
valid boundary output accepted only under test enable
invalid inputs rejected
no source_text accepted
VERIFIED no auto clean admission
non-VERIFIED review queue candidate mapping
blocked delivery candidate mapping
audit metadata preserved
deterministic ids and hashes
bounded evidence preview
no production hook or I/O behavior
```

## Strict boundaries

Forbidden:

```text
modify existing production modules except the single new adapter skeleton file
modify existing tests
modify existing fixtures
modify dependency files
modify output files
commit DateFac Excel or MinerU artifacts
add pipeline imports or hooks
write database records or export files
run MinerU/OCR/LLM/VLM or real extraction
open readiness gates
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED directly to clean_data
git add .
git add -A
```

## Validation commands

```text
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
pytest tests/agent -q
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
R7AV-QA recap
Skeleton design
Disabled flag behavior
Input validation behavior
Review queue candidate mapping
Delivery gate behavior
Clean data guard behavior
Audit metadata behavior
Evidence preview behavior
Boundary review
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
fixture_result（fixture结果）=
skeleton_result（skeleton结果）=
disabled_flag_result（禁用开关结果）=
input_validation_result（输入校验结果）=
review_queue_candidate_result（复核队列候选结果）=
delivery_gate_result（交付闸门结果）=
clean_data_guard_result（clean_data防护结果）=
audit_metadata_result（审计元数据结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7AW-QA test-only production-boundary adapter skeleton under disabled flag review
```

## Commit and push

If validation passes and only the allowed files changed, stage exactly:

```text
git add datefac_agent/review/production_boundary_review_queue_adapter.py
git add tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
git add docs/agent/348N_R7AW_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REPORT.md
git commit -m "feat: add disabled review queue adapter skeleton"
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
