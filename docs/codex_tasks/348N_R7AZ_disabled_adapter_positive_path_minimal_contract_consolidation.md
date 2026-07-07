# 348N-R7AZ disabled adapter positive-path minimal contract consolidation

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = positive-path-contract-consolidation
```

## Plain-language goal

R7AY proved the disabled adapter rejects many bad inputs. R7AZ now checks the opposite side: the smallest good inputs should still pass in a controlled, in-memory, test-only way.

In plain Chinese: 前几轮一直在确认“坏数据进不来”。这一轮确认“真正合规的最小好数据能进到候选输出”，但仍然不接生产、不写库、不导出、不打开 readiness gates。

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
docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md
docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md
docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md
docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md
```

Review current adapter slice:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
```

## Goal

Consolidate a minimal positive-path contract for the disabled adapter skeleton.

This means defining the smallest valid boundary payloads that the adapter is allowed to accept when explicitly enabled in tests, and proving that the output is conservative:

```text
VERIFIED rows do not enter clean_data automatically.
non-VERIFIED rows become review-bound candidate items.
unresolved rows remain blocked from clean delivery.
corrected rows remain re-audit-required or future-gate-required.
outputs are deterministic and metadata-first.
readiness_gates remain CLOSED.
```

## Allowed tracked files

Modify if needed:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
```

Create exactly:

```text
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
docs/agent/348N_R7AZ_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REPORT.md
```

No other tracked files may change.

## Positive-path fixture requirements

Create a small curated fixture with minimal valid boundary payloads. Include at least:

```text
one minimal valid payload with one VERIFIED row
one minimal valid payload with one DISAGREED row
one minimal valid payload with one AMBIGUOUS row
one minimal valid payload with one MISSING_EVIDENCE row
one minimal valid payload with one UNVERIFIED row
one minimal valid payload with one corrected row that still requires re-audit or future gate
one mixed payload with VERIFIED plus non-VERIFIED rows
one payload that includes bounded evidence_preview and required audit metadata only
```

Do not include raw MinerU output, raw Excel rows, full source text, real PDF data, real output files, or any large fixture.

## Positive contract requirements

Tests must confirm:

```text
default disabled behavior still fails closed
explicit test-only enable is still required
minimal valid payloads pass only when explicitly enabled
outputs are in-memory only
output schema is stable for candidate items
VERIFIED rows are represented safely but do not auto-enter clean_data
non-VERIFIED rows map to review_queue candidate items
unresolved rows map to blocked delivery candidate rows
corrected rows do not become clean_data without explicit future gate
bounded evidence_preview is retained
run_id, adapter_version, input_file_hashes, contract_version are retained
review_item_id and audit_hash are deterministic
candidate output ordering is deterministic
output does not share mutable references with input
readiness_gates remain CLOSED
no production hook or IO behavior exists
```

## Keep existing negative protections

Do not weaken R7AY negative cases. The previous 29 negative cases should continue to pass. If a positive-path change breaks any negative case, stop and fix the boundary conservatively.

## Strict boundaries

Forbidden:

```text
modify unrelated datefac_agent modules
modify unrelated tests
modify dependency files
modify output files
commit DateFac Excel or MinerU artifacts
add production pipeline imports or hooks
write database records or export files
run MinerU/OCR/LLM/VLM or real extraction
open readiness gates
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED directly to clean_data
git add .
git add -A
```

## Report requirements

The report must include a short 大白话说明 section explaining what this task did in plain Chinese.

Required sections:

```text
Task ID
Preflight
Files reviewed
R7AY-QA recap
大白话说明
Positive-path consolidation scope
Fixture design
Minimal valid payload review
Candidate output schema review
Review queue candidate behavior
Clean data guard behavior
Delivery gate behavior
Audit metadata behavior
Determinism and immutability checks
Negative protections retained
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
positive_contract_result（正向契约结果）=
fixture_result（fixture结果）=
minimal_valid_payload_result（最小合法输入结果）=
candidate_output_schema_result（候选输出schema结果）=
review_queue_candidate_result（复核队列候选结果）=
clean_data_guard_result（clean_data防护结果）=
delivery_gate_result（交付闸门结果）=
audit_metadata_result（审计元数据结果）=
determinism_immutability_result（确定性与不可变性结果）=
negative_protection_retained_result（负例防护保留结果）=
no_hook_no_io_result（无hook无IO结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7AZ-QA disabled adapter positive-path minimal contract consolidation review
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

## Commit and push

If validation passes and only allowed files changed, stage exactly the changed allowed files. Do not use broad staging.

Likely staging:

```text
git add datefac_agent/review/production_boundary_review_queue_adapter.py
git add tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
git add docs/agent/348N_R7AZ_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REPORT.md
git commit -m "test: consolidate disabled adapter positive contract"
git push origin pivot/348-agent-foundation
```

If adapter code is unchanged, do not stage it.

Stop after push. Do not start the next task.
