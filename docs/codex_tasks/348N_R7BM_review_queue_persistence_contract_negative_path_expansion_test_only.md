# 348N-R7BM review_queue persistence contract negative-path expansion test-only

## Task sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-negative-path-expansion
```

## Plain-language goal

R7BL-QA confirmed the test-only persistence contract prototype is safe. R7BM expands negative-path coverage around that contract before any future real persistence work.

In plain Chinese: 这一轮继续补防线。R7BL 已经有“模拟落库前最后一道闸门”，R7BM 专门拿坏输入、绕路输入、嵌套脏字段、批次异常、重复幂等键、伪造候选等情况去撞它，确认它会 fail closed。仍然不写库、不建表、不导出、不接生产。

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
docs/agent/348N_R7BL_QA_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REVIEW.md
docs/agent/348N_R7BL_REVIEW_QUEUE_PERSISTENCE_CONTRACT_TEST_ONLY_PROTOTYPE_REPORT.md
docs/agent/348N_R7BK_QA_REVIEW_QUEUE_FUTURE_PERSISTENCE_BOUNDARY_DESIGN_PLANNING_SLICE_REVIEW.md
docs/agent/348N_R7BI_QA_REVIEW_QUEUE_WRITER_DRY_RUN_SCHEMA_ALIGNMENT_TEST_ONLY_CONTRACT_PROTOTYPE_REVIEW.md
```

Review current R7BL files:

```text
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json
```

Review related slices read-only:

```text
tests/agent/review_queue_writer_schema_alignment_contract_348n.py
tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py
tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/test_review_queue_writer_dry_run_integration_boundary_348n.py
tests/agent/review_queue_writer_contract_348n.py
tests/agent/test_review_queue_writer_contract_348n.py
datefac_agent/review/production_boundary_review_queue_adapter.py
tests/agent/test_production_boundary_review_queue_adapter_skeleton_348n.py
```

## Goal

Expand test-only negative-path coverage for the review_queue persistence contract.

The goal is not to add new product behavior. The goal is to prove bad payloads cannot become persistence candidates.

## Allowed tracked files

You may modify these test-only files:

```text
tests/agent/review_queue_persistence_contract_348n.py
tests/agent/test_review_queue_persistence_contract_348n.py
```

You may create this new fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json
```

Create this report:

```text
docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
```

Do not modify production code. Do not modify existing fixtures unless absolutely necessary; prefer the new R7BM fixture.

## Negative paths to expand

Add focused negative cases for:

```text
schema alignment preview missing trusted marker
schema alignment preview wrong contract version
schema alignment preview wrong schema version
payload with mixed trusted/untrusted rows
payload with one valid row and one invalid row fails entire batch
payload with nested full source_text under evidence_preview
payload with nested raw_mineru under source_trace
payload with nested raw_excel under metadata-like field
payload with nested raw_parser_payload under audit-like field
payload with nested raw_llm_response or raw_vlm_response
payload with clean_data intent hidden in nested dict
payload with delivery/export intent hidden in nested dict
payload with production writer config hidden in nested dict
payload with readiness override hidden in nested dict
payload with test-only token leaking into candidate row
payload with direct persistence candidate shape but missing upstream schema alignment proof
payload with idempotency_key inconsistent with row payload
payload with record_payload_hash pre-supplied by user instead of derived
payload with duplicate review_item_id and different idempotency_key
payload with duplicate idempotency_key and different review_item_id
payload with empty evidence_preview when review_reason requires evidence
payload with oversized evidence_preview
payload with non-list input_file_hashes
payload with empty input_file_hashes and missing source_file_hash
payload with non-string metric_name or period
payload with NaN/Infinity-like candidate value if applicable
payload with mutable nested objects after validation
payload with unexpected top-level persistence destination or table name
payload with database connection string / DSN / file path / output path
payload with created_at production timestamp policy
payload with reviewer_action implying auto-approve to clean_data
payload with review_status implying delivery unblock without review
```

Keep fixtures small. Do not include real PDF, DateFac Excel, full MinerU output, long source text, or actual secrets.

## Required behavior

The contract must continue to enforce:

```text
default disabled fail-closed
explicit test-only persistence flag required
only validated schema alignment preview accepted
all invalid batch rows fail the whole batch
no partial candidate batch on failure
forbidden fields rejected even when nested
user-provided direct persistence candidate rejected
record_payload_hash must be derived deterministically
idempotency_key must be deterministic and consistent
candidate rows are deep-copied / immutable from caller mutation
no DB write
no file/output write
no export
no migration
no production hook
no clean_data mutation
no readiness gate mutation
```

## Existing safety rules must remain true

```text
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not auto-write clean_data
non-VERIFIED rows remain review-bound
unresolved rows keep blocked_delivery_reason
corrected rows remain re-audit-required
persistence candidate does not trigger delivery
persistence candidate does not mutate clean_data
persistence candidate does not open readiness gates
bounded evidence_preview allowed
full source_text forbidden
raw MinerU/raw Excel/raw parser/raw LLM-VLM payloads forbidden
```

## Test requirements

Add tests proving the expanded negative paths fail closed. Prefer table-driven tests where it makes the suite easier to maintain.

At minimum, prove:

```text
nested forbidden fields are rejected at any depth
hidden clean_data / delivery / production config intent is rejected
mixed valid and invalid batch fails as a whole
record_payload_hash cannot be user supplied
record_payload_hash remains deterministic when derived
idempotency mismatch fails closed
duplicate idempotency/review item conflicts fail closed
source/hash identity shape is enforced
evidence preview remains bounded
review status cannot imply clean_data or delivery unblock
unexpected persistence destination/table/DSN/output path is rejected
input mutation cannot mutate returned candidates
no IO/no DB/no export/no production hook exists
```

## Strict boundaries

Forbidden:

```text
modify datefac_agent production code
add production persistence implementation
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

Required sections:

```text
Task ID
Preflight
Files reviewed
R7BL-QA recap
大白话说明
Negative-path expansion scope
Contract hardening changes
Fixture coverage
Nested forbidden field coverage
Batch fail-closed coverage
Idempotency and hash consistency coverage
Evidence boundary coverage
clean_data and delivery/export boundary coverage
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
negative_path_expansion_result（负路径扩展结果）=
contract_hardening_result（契约加固结果）=
fixture_coverage_result（fixture覆盖结果）=
nested_forbidden_field_result（嵌套禁止字段结果）=
batch_fail_closed_result（批次fail-closed结果）=
idempotency_consistency_result（幂等一致性结果）=
record_payload_hash_result（record_payload_hash结果）=
evidence_boundary_result（证据边界结果）=
clean_data_boundary_result（clean_data边界结果）=
delivery_export_boundary_result（交付导出边界结果）=
no_hook_no_io_result（无hook无IO结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task:

```text
348N-R7BM-QA review_queue persistence contract negative-path expansion review
```

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

## Commit and push

If validation passes and only allowed files changed, stage exactly the changed allowed files. Example:

```text
git add tests/agent/review_queue_persistence_contract_348n.py
git add tests/agent/test_review_queue_persistence_contract_348n.py
git add tests/agent/fixtures/discrepancy_review_queue/r7bm_persistence_contract_negative_path_fixture.json
git add docs/agent/348N_R7BM_REVIEW_QUEUE_PERSISTENCE_CONTRACT_NEGATIVE_PATH_EXPANSION_TEST_ONLY_REPORT.md
git commit -m "test: expand review queue persistence negative paths"
git push origin pivot/348-agent-foundation
```

If `tests/agent/review_queue_persistence_contract_348n.py` does not need changes, do not stage it.

Stop after push. Do not start the next task.
