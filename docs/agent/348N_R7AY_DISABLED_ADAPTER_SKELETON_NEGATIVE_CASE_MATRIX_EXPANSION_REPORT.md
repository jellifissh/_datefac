# 348N-R7AY disabled adapter skeleton negative-case matrix expansion report

## Task ID

```text
348N-R7AY disabled adapter skeleton negative-case matrix expansion
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 904724f..9377b9c
  Fast-forward
  docs/codex_tasks/348N_R7AY_disabled_adapter_skeleton_negative_case_matrix_expansion.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  9377b9c docs: add R7AY negative matrix task
  904724f docs: add R7AX QA review
  1c6ee8a docs: add R7AX QA review task
  f514780 test: harden disabled review queue adapter contract
  17fd029 docs: add R7AX adapter hardening task
  a98ae83 docs: add R7AW QA review
  7ebb8a3 docs: add R7AW QA review task
  cf79fd5 feat: add disabled review queue adapter skeleton
  ef3e1d4 docs: add R7AW disabled adapter skeleton task
  b8bf0c7 docs: add R7AV QA review
  1edcfc9 docs: add R7AV QA review task
  a5d6ff1 docs: add R7AV adapter integration plan
```

Worktree was clean after pull and before R7AY changes.

## Files reviewed

Required context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AY_disabled_adapter_skeleton_negative_case_matrix_expansion.md`
- `docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md`
- `docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md`
- `docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md`
- `docs/agent/348N_R7AW_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REPORT.md`

Current skeleton slice:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`

## R7AX-QA recap

R7AX-QA confirmed the disabled adapter skeleton was already disabled-by-default, explicit-test-token gated, no-hook, no-IO, metadata-first, deterministic, bounded-preview, and fail-closed. It also recommended a broader negative-case matrix before any broader production-boundary implementation.

## 大白话说明

这次没有接生产，也没有让 adapter 真正写 review_queue 或 clean_data。我们做的是“多拿一些假钥匙去试锁”：构造一批看起来像边界输出、但其实缺字段、错版本、乱状态、带全文、带 parser 输出、想打开 clean_data/readiness 的坏输入。结果要求很简单：这些坏输入都必须被拒绝；门继续锁着；VERIFIED 不能偷偷变成强证据或 clean_data。

## Negative-case matrix scope

R7AY added a table-driven matrix with 29 explicit negative cases. The matrix covers:

```text
top-level contract_version
audit metadata presence and type checks
input_file_hashes shape
agreement_status shape
reviewer_action shape and status/action alignment
clean_data and delivery mutation attempts
readiness and external-call mutation attempts
raw parser / MinerU / Excel shapes
nested full-text leak attempts
bounded and required evidence_preview
required row identity fields
mutable nested payload isolation
```

## Fixture design

Created:

```text
tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json
```

Fixture design:

```text
fixture_scope = test_only_r7ay
valid_boundary_output = curated R7AW-shaped payload plus top-level contract_version
negative_case_matrix = compact case table with case_id, category, expected_error, and either mutation or direct bad payload
existing R7AW fixture = unchanged
no full MinerU output / DateFac Excel / local output committed
```

## Input contract negative cases

Covered:

```text
missing top-level contract_version
wrong top-level contract_version
unknown agreement_status
agreement_status with wrong type
parser-like payload shape
raw MinerU-like payload shape
raw Excel-like payload shape
nested full text field at row level
missing source_row_id
missing candidate_metric_name
missing candidate_period
missing candidate_value
```

Adapter hardening added:

```text
top-level contract_version is now required in enabled validation
top-level contract_version must match ADAPTER_CONTRACT_VERSION
blank source_row_id / metric / period / value fail closed
non-string or unknown agreement_status remains rejected
```

## Review action negative cases

Covered:

```text
unknown reviewer_action
reviewer_action with wrong type
OPEN review_status with non-empty reviewer_action
resolved non-VERIFIED delivery candidate still requires valid action and re-audit
```

Adapter hardening added:

```text
review_status / reviewer_action alignment helper
OPEN rows cannot carry reviewer actions
RESOLVED_CORRECTED requires CORRECT_* action
RESOLVED_REJECTED requires reject/not-in-report action
RESOLVED_ACCEPTED requires accept/select-evidence action
UNRESOLVED_NEEDS_SOURCE_CHECK requires source-check style action
```

## Clean data and delivery negative cases

Covered:

```text
clean_data_eligible=true in incoming payload
delivery_blocked=false for unresolved non-VERIFIED blocked row
delivery_clean_admitted=true remains rejected by existing tests
VERIFIED still does not auto-enter clean_data
non-VERIFIED rows stay review-bound
unresolved rows stay blocked from clean delivery
corrected rows still require re-audit
```

Adapter hardening added:

```text
blocked_delivery_rows with explicit delivery_blocked must keep delivery_blocked=true
clean_data and delivery admission guards remain fail-closed
```

## Evidence preview negative cases

Covered:

```text
nested full text field inside evidence_preview
oversized evidence_preview
missing required evidence_preview for review-bound row
bounded output evidence_preview remains <= 160 chars
full source_text remains absent from serialized adapter outputs
```

## Audit metadata negative cases

Covered:

```text
missing run_id
empty run_id
missing adapter_version
missing input_file_hashes
input_file_hashes empty
input_file_hashes has non-string value
readiness_gates missing
readiness_gates not CLOSED
external_call_counts not zero
status count mismatches through existing tests
```

Adapter hardening added:

```text
input_file_hashes must contain non-empty string keys and values
readiness_gates must equal CLOSED
external_call_counts must equal zero
```

## Determinism and immutability checks

Preserved positive checks:

```text
adapter_item_id deterministic across repeated calls
adapter_audit_hash deterministic across repeated calls
review_item_id preserved
audit_hash preserved
output input_file_hashes do not share mutable input references
output readiness_gates do not share mutable input references
output evidence_preview does not change after source payload mutation
```

## No-hook and no-IO boundary

Preserved boundary:

```text
adapter disabled by default
explicit test-only enable token still required
no production pipeline import hook
no file write
no database write
no export/report write
no network call
no parser call
no MinerU/OCR/LLM/VLM call
no PDF parser import
no dependency/config change
readiness gates remain CLOSED
```

The adapter module remains in-memory only. Test fixture reading remains in `tests/agent/`.

## Validation outputs

Required commands run:

```text
python -m py_compile datefac_agent/review/production_boundary_review_queue_adapter.py
  PASS

python -m py_compile tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
  PASS

python -m py_compile tests/agent/production_boundary_review_queue_adapter_contract_348n.py tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
  PASS

python -m py_compile tests/agent/discrepancy_review_queue_integration_boundary_348n.py tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py
  PASS

python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
  PASS

python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py -q
  56 passed in 0.21s

pytest tests/agent -q
  296 passed in 1.17s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
   M datefac_agent/review/production_boundary_review_queue_adapter.py
   M tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
  ?? docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md
  ?? tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json

git diff --stat
  datefac_agent/review/production_boundary_review_queue_adapter.py | 88 +++++++++++++++--
  tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py | 103 +++++++++++++++++----
  2 files changed, 163 insertions(+), 28 deletions(-)

git diff --name-only
  datefac_agent/review/production_boundary_review_queue_adapter.py
  tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py

git diff --check
  PASS
```

## Limitations

- R7AY expands negative-case coverage only; it is not production integration.
- The adapter remains disabled by default and does not persist review queues or delivery outputs.
- The R7AY fixture is curated and synthetic, not full R7AO local output.
- The stricter top-level `contract_version` requirement applies to enabled test validation; disabled mode still ignores payload content and returns a closed disabled result.

## Decision

```text
Decision = 348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_VALID
```

R7AY expands the disabled adapter skeleton negative-case matrix and adds minimal hardening where the matrix exposed gaps. The adapter still stays disabled by default, explicit-test-token gated, no-hook, no-IO, metadata-first, deterministic, bounded-preview, and readiness-closed.

## Recommended next task

```text
348N-R7AY-QA disabled adapter skeleton negative-case matrix expansion review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_VALID
build_result（构建结果）= PASS：py_compile validation passed
test_result（测试结果）= PASS：targeted pytest 56 passed；full tests/agent 296 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
negative_matrix_result（负例矩阵结果）= PASS：29 table-driven negative cases reject malformed boundary-like payloads
fixture_result（fixture结果）= PASS：new curated R7AY fixture created; existing R7AW fixture unchanged
input_contract_negative_result（输入契约负例结果）= PASS：contract_version, status, raw parser/MinerU/Excel, nested full text, and required identity fields fail closed
reviewer_action_negative_result（复核动作负例结果）= PASS：unknown/wrong-type/mismatched reviewer actions fail closed
clean_data_delivery_negative_result（clean_data与交付负例结果）= PASS：clean_data_eligible, unsafe delivery_blocked, and delivery admission paths stay closed
evidence_preview_negative_result（证据预览负例结果）= PASS：missing/oversized/object-with-full-text previews fail closed
audit_metadata_negative_result（审计元数据负例结果）= PASS：missing/empty metadata, non-string hashes, opened readiness, and nonzero external calls fail closed
determinism_immutability_result（确定性与不可变性结果）= PASS：stable IDs/hashes and no mutable input reference leakage
no_hook_no_io_result（无hook无IO结果）= PASS：no production hook, IO, parser/model/extraction call, dependency/config change
boundary_check（边界检查）= PASS：only allowed files changed; no output/input/temp/data/legacy/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AY-QA disabled adapter skeleton negative-case matrix expansion review
```
