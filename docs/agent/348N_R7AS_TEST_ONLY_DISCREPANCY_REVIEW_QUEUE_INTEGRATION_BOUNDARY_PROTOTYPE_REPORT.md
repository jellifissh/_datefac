# 348N-R7AS test-only discrepancy review queue integration boundary prototype report

## Task ID

```text
348N-R7AS test-only discrepancy review queue integration boundary prototype
```

## Task size / reasoning level used

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = test-only-boundary-prototype
reason = R7AR designed the discrepancy review integration boundary. R7AS proves the boundary with compact test-only comparison rows and no production wiring.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Already up to date.

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git branch --show-current:
  pivot/348-agent-foundation

git log -1 --oneline:
  f01bd54 docs: add R7AR integration boundary design
```

Worktree was clean after pull and before R7AS prototype file creation.

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
- `docs/agent/348N_R7AR_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7AQ_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AQ_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md`

Read-only boundary context:

- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `tests/agent/test_discrepancy_review_queue_policy_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aq_discrepancy_rows_fixture.json`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/delivery/evidence_index_writer.py`

## Files created

Created exactly the requested R7AS files:

- `tests/agent/discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7as_integration_boundary_fixture.json`
- `docs/agent/348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REPORT.md`

No `datefac_agent/` production files, output artifacts, dependency files, DateFac Excel files, or MinerU outputs were modified.

## Fixture result

Fixture:

```text
tests/agent/fixtures/discrepancy_review_queue/r7as_integration_boundary_fixture.json
```

Fixture facts:

```text
schema_version = 1
fixture_scope = test_only_r7as
fixture_size_bytes = 9642
row_count = 8
```

Status coverage:

```text
VERIFIED = 1
DISAGREED = 2
AMBIGUOUS = 1
MISSING_EVIDENCE = 2
PARSE_SKIPPED = 1
UNVERIFIED = 1
resolved reviewer correction row = included
unresolved reviewer action row = included
```

The fixture is compact and curated. It is not full R7AO output, DateFac Excel, or full MinerU `content_list_v2`.

## Integration boundary result

Prototype:

```text
tests/agent/discrepancy_review_queue_integration_boundary_348n.py
```

Implemented test-only helpers:

```text
load_integration_boundary_fixture(...)
run_discrepancy_review_integration_boundary(...)
validate_integration_payload(...)
validate_comparison_result_row(...)
normalize_comparison_result_row(...)
```

Boundary outputs:

```text
review_queue_items
discrepancy_report_rows
delivery_clean_candidates
blocked_delivery_rows
audit_metadata
```

Observed output counts:

```text
comparison_result_rows = 8
review_queue_items = 7
discrepancy_report_rows = 7
delivery_clean_candidates = 1
blocked_delivery_rows = 6
verified_without_clean_gate_count = 1
```

The single `delivery_clean_candidates` row is a resolved reviewer-correction case and remains marked:

```text
delivery_clean_admitted = false
requires_reaudit_before_clean_delivery = true
```

It is therefore not a clean-data admission.

## Review queue output result

Rules proven by tests:

```text
VERIFIED -> no discrepancy review_queue item
DISAGREED -> evidence_conflict_queue
AMBIGUOUS -> evidence_ambiguity_queue
MISSING_EVIDENCE -> missing_evidence_queue
PARSE_SKIPPED -> parse_schema_queue
UNVERIFIED -> partial_anchor_queue
```

Observed review queue status counts:

```text
DISAGREED = 2
AMBIGUOUS = 1
MISSING_EVIDENCE = 2
PARSE_SKIPPED = 1
UNVERIFIED = 1
```

Review item generation reuses the R7AQ test-only policy helper shape and keeps deterministic `review_item_id` and `audit_hash`.

## Discrepancy report result

Discrepancy report rows are metadata-first:

```text
review_item_id
source_row_id
candidate_metric_name
candidate_period
candidate_value
candidate_unit
agreement_status
review_subqueue
severity
review_status
reviewer_decision
source_text_status
evidence_type
matched_locator
matched_text_sha256
evidence_preview
risk_reason
suggested_action
clean_data_eligible
```

Full text fields are rejected from inputs or omitted from outputs:

```text
source_text
full_source_text
source_text_full
full_text
raw_mineru_block
full_table_html
```

`evidence_preview` is bounded by `preview_limit` and is not a full source-text serialization channel.

## Delivery gate result

Delivery guard behavior:

```text
VERIFIED rows do not enter discrepancy review_queue.
VERIFIED rows do not automatically enter delivery clean output.
VERIFIED rows require an explicit future clean gate even to become a delivery candidate.
non-VERIFIED rows enter discrepancy review outputs.
unresolved non-VERIFIED rows enter blocked_delivery_rows.
resolved reviewer-correction rows can become re-audit candidates only, not clean admissions.
```

No prototype behavior writes clean data, promotes evidence to `STRONG_EVIDENCE`, or opens readiness.

## Audit metadata result

Audit metadata retained:

```text
run_id = r7as_fixture_run_001
adapter_version = r7as_integration_boundary_test_only_v1
input_file_hashes.datefac_excel = sha256:r7as-datefac-fixture
input_file_hashes.mineru_content_list_v2 = sha256:r7as-mineru-fixture
audit_metadata_hash = c25c60580d823829f70fe2da727cc6d64e6ce81ae7eacbe5d1abd2b2e2feecf7
```

Readiness snapshot:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

External call counts:

```text
mineru_run_count = 0
ocr_run_count = 0
llm_api_call_count = 0
vlm_api_call_count = 0
```

Boundary flags:

```text
test_only = true
production_hook = false
verified_auto_clean = false
verified_promotes_to_strong_evidence = false
full_source_text_serialized = false
```

## Clean data guard result

Clean-data constraints proven:

```text
clean_data_eligible defaults false.
unsupported reviewer action fails closed.
readiness gate changes are rejected.
missing run_id / adapter_version / input_file_hashes fail closed.
forbidden full source-text fields fail closed.
delivery_clean_admitted remains false in all emitted delivery candidates.
requires_reaudit_before_clean_delivery remains true for any candidate emitted after review action.
```

This matches R7AR's boundary: review/discrepancy outputs can be produced, but clean-data admission remains a future separate gate.

## Validation outputs

Required commands run:

```text
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

pytest tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py -q
  14 passed

pytest tests/agent -q
  227 passed

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REPORT.md
  ?? tests/agent/discrepancy_review_queue_integration_boundary_348n.py
  ?? tests/agent/fixtures/discrepancy_review_queue/r7as_integration_boundary_fixture.json
  ?? tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py

git diff --stat
  no tracked diff before staging because new files were untracked

git diff --name-only
  no tracked diff before staging because new files were untracked

git diff --check
  PASS
```

## Boundary review

R7AS stayed within scope:

```text
datefac_agent/ modified = no
production pipeline modified = no
output committed = no
DateFac Excel committed = no
MinerU output committed = no
MinerU run = no
OCR / LLM / VLM run = no
real PDF extraction = no
new dependency added = no
VERIFIED -> STRONG_EVIDENCE promotion = no
VERIFIED -> clean_data admission = no
readiness gates opened = no
```

Readiness remains:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Decision

```text
Decision = 348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_VALID
```

R7AS proves a compact test-only integration boundary from comparison-result rows to review/discrepancy/delivery-guard outputs. All non-VERIFIED rows route to review/discrepancy outputs, unresolved rows are blocked from clean delivery, VERIFIED rows do not bypass clean gates, full source text is not serialized, audit metadata remains deterministic, and readiness gates remain closed.

## Recommended next task

```text
348N-R7AS-QA test-only discrepancy review queue integration boundary prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_VALID
build_result（构建结果）= PASS：py_compile validation passed
test_result（测试结果）= PASS：pytest tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py -q => 14 passed；pytest tests/agent -q => 227 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
fixture_result（fixture结果）= PASS：8-row curated test-only fixture covers VERIFIED / DISAGREED / AMBIGUOUS / MISSING_EVIDENCE / PARSE_SKIPPED / UNVERIFIED plus resolved and unresolved reviewer-action cases
integration_boundary_result（集成边界结果）= PASS：comparison rows produce review_queue_items / discrepancy_report_rows / delivery_clean_candidates / blocked_delivery_rows / audit_metadata without production hook
review_queue_output_result（复核队列输出结果）= PASS：7 non-VERIFIED rows map to conservative subqueues with deterministic review_item_id/audit_hash
discrepancy_report_result（差异报告结果）= PASS：7 metadata-first discrepancy report rows with bounded evidence_preview and no full source_text
delivery_gate_result（交付闸门结果）= PASS：VERIFIED not auto-clean；unresolved non-VERIFIED blocked；resolved correction remains re-audit-only and delivery_clean_admitted=false
audit_metadata_result（审计元数据结果）= PASS：run_id / adapter_version / input_file_hashes / readiness snapshot / external call counts / deterministic audit_metadata_hash retained
clean_data_guard_result（clean_data防护结果）= PASS：clean_data_eligible defaults false；unsupported actions, missing metadata, forbidden source_text fields, and readiness changes fail closed
boundary_check（边界检查）= PASS：tests/docs/fixture only；no datefac_agent/ changes；no output/DateFac/MinerU/dependency commits；no MinerU/OCR/LLM/VLM/PDF extraction
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AS-QA test-only discrepancy review queue integration boundary prototype review
```
