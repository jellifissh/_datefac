# 348N-R7AY-QA disabled adapter skeleton negative-case matrix expansion review

## Task ID

```text
348N-R7AY-QA disabled adapter skeleton negative-case matrix expansion review
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Already up to date.

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  d13e013 docs: add R7AY QA review task
  a29fca1 test: expand disabled adapter negative matrix
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
```

The worktree was clean after pull. R7AY implementation commit reviewed: `a29fca1 test: expand disabled adapter negative matrix`.

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
- `docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md`
- `docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md`
- `docs/agent/348N_R7AX_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REPORT.md`
- `docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md`

R7AY files reviewed:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`
- `docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md`

Related files reviewed read-only:

- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`
- `tests/agent/production_boundary_review_queue_adapter_contract_348n.py`
- `tests/agent/discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/delivery/evidence_index_writer.py`

## R7AY recap

R7AY expanded the disabled production-boundary review queue adapter skeleton with a curated negative-case matrix and minimal contract hardening. The reviewed implementation remains disabled by default, explicit-test-token gated, no-hook, no-IO, metadata-first, deterministic, bounded-preview, and readiness-closed.

## 大白话说明

这轮 QA 审的是“坏输入撞门测试”是不是够硬：缺版本、错状态、乱 reviewer_action、偷开 clean_data/readiness、塞 full source_text、塞 raw MinerU/Excel/parser 形状，都应该被 adapter 拒绝。审查结论是：这些坏输入确实被表驱动测试覆盖，合法的小型边界 payload 仍可通过；但 adapter 仍不接生产、不写 review_queue、不放行 clean_data。

## Allowed files review

R7AY commit `a29fca1` changed exactly the expected four files:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`
- `docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md`

No output, input, temp, data, legacy, dependency/config, DateFac Excel, MinerU artifact, or readiness files were modified by R7AY.

## Negative-case matrix review

The R7AY fixture contains 29 negative cases with 29 unique `case_id` values. Categories are meaningful rather than duplicate-only:

```text
input_contract = 12
audit_metadata = 9
reviewer_action = 3
clean_delivery = 2
evidence_preview = 3
```

The parametrized test `test_r7ay_negative_case_matrix_fails_closed` drives every fixture case through `build_production_boundary_review_queue_adapter_output(..., _enabled_config())` and expects `ProductionBoundaryReviewQueueAdapterError` with each case's declared `expected_error`.

## Fixture review

`tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json` is a small curated test-only fixture:

- `fixture_scope = test_only_r7ay`
- top-level keys are `schema_version`, `fixture_scope`, `valid_boundary_output`, and `negative_case_matrix`
- `valid_boundary_output.contract_version = r7aw_disabled_production_boundary_adapter_skeleton_v1`
- fixture size is guarded by test as `< 50000` bytes
- fixture is not a full R7AO output, not a DateFac Excel dump, and not a MinerU content dump

## Input contract negative-case review

Covered and fail-closed:

- missing top-level `contract_version`
- wrong top-level `contract_version`
- unknown `agreement_status`
- non-string / wrong-type `agreement_status`
- parser-like payload shape
- raw MinerU-like payload shape
- raw Excel-like payload shape
- nested full text at row level
- missing `source_row_id`
- missing `candidate_metric_name`
- missing `candidate_period`
- missing `candidate_value`

The adapter now requires the top-level boundary output contract version during enabled validation while disabled mode remains closed and payload-agnostic.

## Reviewer action negative-case review

Covered and fail-closed:

- unknown `reviewer_action`
- wrong-type `reviewer_action`
- `review_status` / `reviewer_action` mismatch

The alignment guard rejects action leakage on `OPEN` rows and requires status-appropriate actions for resolved corrected, rejected, accepted, and source-check rows.

## Clean data and delivery negative-case review

Covered and fail-closed:

- incoming `clean_data_eligible=true`
- unsafe `delivery_blocked=false` for unresolved non-VERIFIED blocked rows
- unresolved non-VERIFIED rows in delivery-clean candidates
- `STRONG_EVIDENCE` mutation attempts
- readiness mutation attempts

Positive guard tests also confirm VERIFIED rows do not auto-enter review queue or clean data, non-VERIFIED rows stay review-bound, unresolved rows stay blocked from clean delivery, and corrected rows remain re-audit only.

## Evidence preview negative-case review

Covered and fail-closed:

- nested full text inside `evidence_preview`
- oversized `evidence_preview`
- missing required `evidence_preview` for review-bound rows

Output previews remain bounded by the 160-character default, and recursive forbidden-key validation rejects full text fields such as `source_text`, `full_source_text`, raw parser output, raw PDF text, raw Excel rows, table HTML, MinerU artifacts, OCR output, and page text payloads.

## Audit metadata negative-case review

Covered and fail-closed:

- missing `run_id`
- empty `run_id`
- missing `adapter_version`
- missing `input_file_hashes`
- empty `input_file_hashes`
- non-string `input_file_hashes` values
- missing `readiness_gates`
- non-CLOSED `readiness_gates`
- nonzero external call counts

The enabled validator still requires `readiness_gates == CLOSED` and `external_call_counts == ZERO`.

## Determinism and immutability review

Positive tests preserve deterministic `adapter_item_id`, adapter audit hash, item audit hashes, and review item identities across repeated builds. The mutable-reference test mutates input hashes, evidence preview, and readiness fields after output creation and confirms the adapter output keeps deep-copied values.

## No-hook and no-IO review

The adapter module imports only standard in-memory helpers and has no file, network, parser, model, PDF, MinerU, OCR, LLM, or VLM runtime hook. Static tests inspect the adapter AST for forbidden imports/calls and scan `datefac_agent/` for production pipeline references to `production_boundary_review_queue_adapter`; the scan remains empty outside the module itself.

## Boundary review

Boundary status remains safe:

- adapter disabled by default
- explicit test-only enable token required for enabled validation
- no production pipeline hook
- no output/input/temp/data/legacy writes
- no dependency/config changes
- no MinerU/OCR/LLM/VLM/PDF extraction
- no full `source_text` serialization
- VERIFIED does not promote to `STRONG_EVIDENCE`
- VERIFIED does not auto-enter `clean_data`
- non-VERIFIED remains review-bound
- readiness gates remain CLOSED

## Validation outputs

Required validation commands run:

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
  56 passed in 0.20s

pytest tests/agent -q
  296 passed in 1.21s
```

Post-report git checks were run before staging:

```text
git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md

git diff --stat
  no tracked diff before staging; QA report is untracked

git diff --name-only
  no tracked diff before staging; QA report is untracked

git diff --check
  PASS
```

## Limitations

- This is QA of a disabled adapter skeleton and its negative-case matrix, not production review queue integration.
- The valid payload and matrix fixture are curated test artifacts, not complete R7AO local output.
- The adapter still does not persist review queue items, delivery rows, or client outputs.
- Broader positive-path production-boundary consolidation remains a future task.

## Decision

```text
Decision = PASS: 348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW_VALID
```

R7AY's negative-case matrix is real, meaningful, and boundary-safe. The adapter remains disabled-by-default, explicit-test-token gated, no-hook, no-IO, metadata-only, fail-closed, deterministic, and readiness-closed.

## Recommended next task

```text
348N-R7AZ disabled adapter positive-path minimal contract consolidation
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：R7AY-QA 通过，negative-case matrix expansion 有效且边界安全
build_result（构建结果）= PASS：required py_compile commands passed
test_result（测试结果）= PASS：targeted pytest 56 passed；tests/agent 296 passed
files_modified（修改文件数）= 1（仅新增本 QA report）
error_count（错误数）= 0
allowed_files_review_result（允许文件审查结果）= PASS：R7AY changed exactly 4 expected files；R7AY-QA only creates the allowed QA report
negative_matrix_review_result（负例矩阵审查结果）= PASS：29 unique negative cases across input_contract/audit_metadata/reviewer_action/clean_delivery/evidence_preview
fixture_review_result（fixture审查结果）= PASS：small curated test_only_r7ay fixture；not full R7AO/MinerU/DateFac output
input_contract_negative_review_result（输入契约负例审查结果）= PASS：contract_version/status/raw shape/full text/identity-field cases fail closed
reviewer_action_negative_review_result（复核动作负例审查结果）= PASS：unknown/wrong-type/mismatched reviewer actions fail closed
clean_data_delivery_negative_review_result（clean_data与交付负例审查结果）= PASS：clean_data_eligible, delivery_blocked, unresolved delivery, STRONG_EVIDENCE, readiness mutations fail closed
evidence_preview_negative_review_result（证据预览负例审查结果）= PASS：missing/oversized/nested-full-text previews fail closed；preview remains bounded
audit_metadata_negative_review_result（审计元数据负例审查结果）= PASS：run_id/adapter_version/input_file_hashes/readiness/external-call metadata fail closed when malformed
determinism_immutability_review_result（确定性与不可变性审查结果）= PASS：IDs/hashes deterministic；output deep-copied from mutable inputs
no_hook_no_io_review_result（无hook无IO审查结果）= PASS：no production hook, IO, parser/model/extraction call, PDF dependency, or dependency/config change
boundary_check（边界检查）= PASS：disabled by default；explicit test-only token；no source_text serialization；no clean/readiness promotion
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AZ disabled adapter positive-path minimal contract consolidation
```
