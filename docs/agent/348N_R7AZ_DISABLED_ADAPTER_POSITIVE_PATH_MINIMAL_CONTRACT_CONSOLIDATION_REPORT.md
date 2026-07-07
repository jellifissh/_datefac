# 348N-R7AZ disabled adapter positive-path minimal contract consolidation report

## Task ID

```text
348N-R7AZ disabled adapter positive-path minimal contract consolidation
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 2037d3d..adaf893
  Fast-forward
  docs/codex_tasks/348N_R7AZ_disabled_adapter_positive_path_minimal_contract_consolidation.md created

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  adaf893 docs: add R7AZ positive contract task
  2037d3d docs: add R7AY QA review
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
```

Worktree was clean after pull and before R7AZ changes.

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
- `docs/agent/348N_R7AY_QA_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REVIEW.md`
- `docs/agent/348N_R7AY_DISABLED_ADAPTER_SKELETON_NEGATIVE_CASE_MATRIX_EXPANSION_REPORT.md`
- `docs/agent/348N_R7AX_QA_DISABLED_ADAPTER_SKELETON_CONTRACT_HARDENING_REVIEW.md`
- `docs/agent/348N_R7AW_QA_TEST_ONLY_PRODUCTION_BOUNDARY_ADAPTER_SKELETON_UNDER_DISABLED_FLAG_REVIEW.md`

Current adapter slice:

- `datefac_agent/review/production_boundary_review_queue_adapter.py`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aw_disabled_adapter_skeleton_fixture.json`
- `tests/agent/fixtures/discrepancy_review_queue/r7ay_negative_case_matrix_fixture.json`

R7AZ files:

- `tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json`
- `tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py`
- `docs/agent/348N_R7AZ_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REPORT.md`

## R7AY-QA recap

R7AY-QA confirmed the disabled adapter skeleton rejects malformed or unsafe boundary-like inputs: missing/wrong contract version, malformed audit metadata, unknown statuses/actions, clean delivery mutation attempts, readiness opening, raw parser/MinerU/Excel shapes, nested full text, unbounded previews, and required identity-field omissions. It also confirmed the adapter remains disabled-by-default, explicit-test-token gated, no-hook, no-IO, metadata-only, fail-closed, deterministic, and readiness-closed.

## 大白话说明

前几轮一直在确认“坏数据进不来”。这一轮补上反面：真正最小、合规、测试专用的好数据，在显式 test-only token 下能进入 adapter 的内存候选输出；但它依然不会写 review_queue、不会写 clean_data、不会导出、不会接生产，也不会把 VERIFIED 自动变成强证据或 clean_data。

## Positive-path consolidation scope

R7AZ consolidates positive-path contract coverage only. It adds a curated test-only fixture and test assertions for minimal valid boundary payloads. The production-boundary adapter implementation did not need code changes because the existing enabled validation and candidate-output builder already supported the safe minimal shapes.

Scope intentionally remains:

```text
test-only fixture + tests + implementation report
no production pipeline hook
no persistence
no output artifacts
no dependency/config changes
readiness gates closed
```

## Fixture design

Created:

```text
tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json
```

Fixture properties:

```text
schema_version = r7az_positive_path_minimal_contract_fixture_v1
fixture_scope = test_only_r7az
positive_payload_count = 8
file_size = 47,301 bytes
raw MinerU output = absent
raw Excel rows = absent
full source_text = absent
real PDF data = absent
local output files = absent
```

The fixture contains exactly eight curated positive cases:

```text
verified_only_minimal
disagreed_only_minimal
ambiguous_only_minimal
missing_evidence_only_minimal
unverified_only_minimal
corrected_reaudit_only_minimal
mixed_verified_and_non_verified_minimal
bounded_preview_required_metadata_only
```

## Minimal valid payload review

Each positive payload uses only the accepted boundary top-level fields:

```text
contract_version
review_queue_items
discrepancy_report_rows
delivery_clean_candidates
blocked_delivery_rows
audit_metadata
```

Each audit metadata object uses the required metadata fields only:

```text
run_id
adapter_version
input_file_hashes
comparison_row_count
comparison_status_counts
review_queue_count
review_queue_status_counts
discrepancy_report_count
delivery_clean_candidate_count
blocked_delivery_row_count
verified_without_clean_gate_count
readiness_gates
external_call_counts
boundary_flags
audit_metadata_hash
```

Test result:

```text
PASS: all eight minimal positive payloads pass only when explicitly enabled with the R7AW test-only token.
PASS: default disabled behavior still returns closed empty output.
PASS: enabled mode without the explicit test token still fails closed.
```

## Candidate output schema review

R7AZ asserts stable candidate output keys for:

```text
review_queue_candidate_items
discrepancy_report_candidate_rows
blocked_delivery_candidate_rows
```

The schema remains metadata-first and bounded-preview only. It includes deterministic adapter metadata, review identity, candidate metric/period/value/unit, agreement status, severity, review status/action, evidence preview hash, locator/hash metadata, input hashes, adapter contract version, and creation source. It does not include raw source text, raw MinerU output, raw Excel rows, parser output, table HTML, or PDF text.

## Review queue candidate behavior

Unresolved non-VERIFIED minimal cases are validated:

```text
DISAGREED -> one review_queue candidate + discrepancy row + blocked delivery row
AMBIGUOUS -> one review_queue candidate + discrepancy row + blocked delivery row
MISSING_EVIDENCE -> one review_queue candidate + discrepancy row + blocked delivery row
UNVERIFIED -> one review_queue candidate + discrepancy row + blocked delivery row
```

The mixed payload preserves deterministic ordering:

```text
DISAGREED
AMBIGUOUS
MISSING_EVIDENCE
UNVERIFIED
```

## Clean data guard behavior

Confirmed:

```text
clean_data_admitted_count = 0
review_queue_candidate_items[*].clean_data_eligible = false
delivery_reaudit_candidate_rows[*].delivery_clean_admitted = false
boundary_flags.verified_auto_clean = false
boundary_flags.verified_promotes_to_strong_evidence = false
```

VERIFIED rows remain delivery re-audit / explicit-gate candidates only. They do not enter clean data automatically and do not promote to `STRONG_EVIDENCE`.

## Delivery gate behavior

Confirmed:

```text
unresolved non-VERIFIED rows -> blocked_delivery_candidate_rows
VERIFIED rows -> delivery_reaudit_candidate_rows with EXPLICIT_CLEAN_GATE_REQUIRED
corrected non-VERIFIED rows -> delivery_reaudit_candidate_rows with REQUIRES_REAUDIT_BEFORE_CLEAN_DELIVERY
delivery_clean_admitted remains false
requires_reaudit_before_clean_delivery remains true
```

Corrected rows are represented as re-audit candidates only and cannot become clean delivery without a future explicit gate.

## Audit metadata behavior

Confirmed preserved fields:

```text
run_id
adapter_version
input_file_hashes
contract_version
source_audit_metadata_hash
readiness_gates
external_call_counts
```

The adapter output deep-copies nested metadata, so later input mutation does not alter output hashes, preview text, input file hashes, or readiness gates.

## Determinism and immutability checks

R7AZ adds checks that:

```text
review_item_id is preserved
audit_hash is preserved
adapter_item_id is deterministic across repeated calls
adapter_audit_hash is deterministic across repeated calls
candidate ordering is deterministic
output does not share mutable input_file_hashes, evidence_preview, or readiness_gates references with input
```

Existing R7AW/R7AX deterministic and immutability tests remain intact.

## Negative protections retained

R7AY's 29 negative cases still run through the same parametrized matrix test and continue to fail closed. No R7AZ test weakens the negative protections for malformed contract versions, bad metadata, bad statuses/actions, clean/readiness mutations, raw parser shapes, raw MinerU/Excel fields, nested full text, unbounded previews, or missing identity fields.

## No-hook and no-IO boundary

The adapter module remains unchanged in R7AZ and still has:

```text
no production pipeline import hook
no filesystem writes
no database writes
no export/report writes
no network calls
no parser calls
no MinerU/OCR/LLM/VLM calls
no PDF parser imports
no dependency/config changes
```

R7AZ tests read only compact fixtures under `tests/agent/fixtures/`; the adapter itself remains in-memory only.

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
  75 passed in 0.27s

pytest tests/agent -q
  315 passed in 1.17s
```

Git validation before staging:

```text
git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
   M tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
  ?? docs/agent/348N_R7AZ_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_REPORT.md
  ?? tests/agent/fixtures/discrepancy_review_queue/r7az_positive_path_minimal_contract_fixture.json

git diff --stat
  tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py | 298 +++++++++++++++++++++

git diff --name-only
  tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py

git diff --check
  PASS; only Git line-ending normalization warnings were printed
```

## Limitations

- R7AZ consolidates minimal positive-path contract coverage; it is not production integration.
- The positive fixture is curated and synthetic, not full R7AO local output.
- The adapter still does not write actual review queue, clean data, delivery output, or reports.
- Corrected rows are represented as future re-audit/future-gate candidates only.
- A follow-up QA task should review whether the positive-path consolidation is sufficiently minimal and whether any hidden production boundary risk remains.

## Decision

```text
Decision = 348N_R7AZ_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_VALID
```

R7AZ confirms that smallest valid positive payloads are accepted only under explicit test enablement, while all clean-data, delivery, evidence-promotion, full-text, IO, and readiness boundaries remain closed.

## Recommended next task

```text
348N-R7AZ-QA disabled adapter positive-path minimal contract consolidation review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：348N_R7AZ_DISABLED_ADAPTER_POSITIVE_PATH_MINIMAL_CONTRACT_CONSOLIDATION_VALID
build_result（构建结果）= PASS：required py_compile validation passed
test_result（测试结果）= PASS：targeted pytest 75 passed；full tests/agent 315 passed
files_modified（修改文件数）= 3
error_count（错误数）= 0
positive_contract_result（正向契约结果）= PASS：minimal positive payloads pass only with explicit test-only enable token
fixture_result（fixture结果）= PASS：new small curated R7AZ fixture with 8 positive payloads; no raw output/full text
minimal_valid_payload_result（最小合法输入结果）= PASS：VERIFIED, DISAGREED, AMBIGUOUS, MISSING_EVIDENCE, UNVERIFIED, corrected, mixed, bounded-preview cases covered
candidate_output_schema_result（候选输出schema结果）= PASS：review/discrepancy/blocked candidate schemas asserted stable and metadata-first
review_queue_candidate_result（复核队列候选结果）= PASS：unresolved non-VERIFIED rows map to review-bound candidate outputs
clean_data_guard_result（clean_data防护结果）= PASS：clean_data_admitted_count=0; clean_data_eligible=false; VERIFIED does not auto-clean
delivery_gate_result（交付闸门结果）= PASS：unresolved rows blocked; VERIFIED/corrected rows remain re-audit or explicit future gate required
audit_metadata_result（审计元数据结果）= PASS：run_id, adapter_version, input_file_hashes, contract_version, readiness, external calls retained
determinism_immutability_result（确定性与不可变性结果）= PASS：IDs/hashes/order deterministic; output does not share mutable input references
negative_protection_retained_result（负例防护保留结果）= PASS：R7AY 29 negative cases still pass and fail closed
no_hook_no_io_result（无hook无IO结果）= PASS：adapter unchanged; no production hook, IO, parser/model/extraction call, or dependency change
boundary_check（边界检查）= PASS：allowed files only; no output/input/temp/data/legacy/dependency/readiness changes
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AZ-QA disabled adapter positive-path minimal contract consolidation review
```
