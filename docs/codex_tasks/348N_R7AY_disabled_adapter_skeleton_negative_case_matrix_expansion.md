# 348N-R7AY disabled adapter skeleton negative-case matrix expansion

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = negative-case-matrix-expansion
```

## Plain-language goal

R7AX already hardened the disabled adapter skeleton. R7AY is not a new feature and not production integration.

The goal is to make a larger test matrix of bad inputs and confirm the adapter keeps refusing them. In plain words: keep trying to trick the locked door with many fake keys, and make sure the door stays locked.

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
docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md
docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md
docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md
docs/agent/348N_R7AW_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REPORT.md
```

Review current skeleton slice:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json
```

## Goal

Expand the negative-case test matrix around the disabled adapter skeleton. The adapter must still be disabled by default, require explicit test-only enable, perform no IO, have no pipeline hook, and keep readiness gates closed.

This task should mostly add tests and fixture cases. Only change the adapter code if a new negative case exposes a real validation gap.

## Allowed tracked files

Modify if needed:

```text
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
```

Create exactly:

```text
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md
```

Do not modify the existing R7AW fixture unless there is a strong reason. Prefer the new R7AY fixture.

## Negative-case matrix requirements

Add parametrized or table-driven tests for malformed boundary-looking payloads. Cover at least:

```text
missing top-level contract_version
wrong top-level contract_version
missing run_id
empty run_id
missing adapter_version
missing input_file_hashes
input_file_hashes is empty
input_file_hashes has non-string values
unknown agreement_status
agreement_status with wrong type
unknown reviewer_action
reviewer_action with wrong type
review_status and reviewer_action mismatch
clean_data_eligible true in incoming payload
delivery_blocked false for unresolved non-VERIFIED row
readiness_gates missing
readiness_gates not CLOSED
external_calls not zero or equivalent safe value
parser-like payload shape
raw MinerU-like payload shape
raw Excel-like payload shape
nested full text field at row level
nested full text field inside evidence preview
oversized evidence preview
missing required evidence preview for review-bound row
missing source row id
missing metric name
missing period
missing candidate value
mutable nested payload should not leak into output
```

## Positive guard cases

Keep at least these positive checks:

```text
default disabled still fails closed
explicit test-only enable still required
valid curated boundary payload still produces in-memory candidates only
VERIFIED does not auto-enter clean_data
non-VERIFIED stays review-bound
unresolved rows stay blocked from clean delivery
corrected rows still require re-audit or future explicit gate
review_item_id and audit_hash remain deterministic across repeated calls
```

## Behavior constraints

The adapter must not:

```text
write files
write database records
export reports
call network
call parser
call MinerU
call OCR
call LLM
call VLM
import into the production pipeline
open readiness gates
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED directly to clean_data
```

## Report requirements

The report must include a short 大白话说明 section explaining what this task did in plain Chinese.

Required sections:

```text
Task ID
Preflight
Files reviewed
R7AX-QA recap
大白话说明
Negative-case matrix scope
Fixture design
Input contract negative cases
Review action negative cases
Clean data and delivery negative cases
Evidence preview negative cases
Audit metadata negative cases
Determinism and immutability checks
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
negative_matrix_result（负例矩阵结果）=
fixture_result（fixture结果）=
input_contract_negative_result（输入契约负例结果）=
reviewer_action_negative_result（复核动作负例结果）=
clean_data_delivery_negative_result（clean_data与交付负例结果）=
evidence_preview_negative_result（证据预览负例结果）=
audit_metadata_negative_result（审计元数据负例结果）=
determinism_immutability_result（确定性与不可变性结果）=
no_hook_no_io_result（无hook无IO结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7AY-QA disabled adapter skeleton negative-case matrix expansion review
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
git add tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
git add docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md
git commit -m "test: expand disabled adapter negative matrix"
git push origin pivot/348-agent-foundation
```

If adapter code is unchanged, do not stage it.

Stop after push. Do not start the next task.
