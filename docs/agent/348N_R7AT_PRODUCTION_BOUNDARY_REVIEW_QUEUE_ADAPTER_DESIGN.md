# 348N-R7AT production-boundary review queue adapter design

## Task ID

```text
348N-R7AT production-boundary review queue adapter design
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Already up to date.

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

current branch:
  pivot/348-agent-foundation

latest reviewed commit:
  b402e57 docs: add R7AS QA review
```

Worktree was clean after pull and before creating this design report.

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
- `docs/agent/348N_R7AS_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AS_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7AR_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7AQ_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md`

Read-only implementation context:

- `tests/agent/discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py`
- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `tests/agent/test_discrepancy_review_queue_policy_348n.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/delivery/evidence_index_writer.py`

No code, tests, fixtures, outputs, dependencies, or production pipeline files were modified.

## R7AS-QA recap

R7AS-QA confirmed:

```text
commit = b402e57 docs: add R7AS QA review
R7AS prototype = test-only under tests/agent/
fixture = 8-row curated test fixture
comparison_result_rows = 8
review_queue_items = 7
discrepancy_report_rows = 7
delivery_clean_candidates = 1
blocked_delivery_rows = 6
VERIFIED without explicit clean gate = 1
readiness_gates = CLOSED
external_call_counts = all zero
full_source_text serialized = false
production_hook = false
```

The test-only prototype proved the shape:

```text
comparison_result rows
  -> integration boundary
  -> review_queue_items
  -> discrepancy_report_rows
  -> delivery guard outputs
  -> audit_metadata
```

It did not create or modify production code.

## Production boundary goal

Goal:

```text
Design the future production-boundary review queue adapter contract that can safely convert validated comparison/discrepancy-boundary outputs into production review_queue candidate inputs.
```

Non-goal:

```text
Do not implement the adapter in R7AT.
Do not wire datefac_agent/ production modules.
Do not create a runner, fixture, or output artifact.
Do not change clean_data, evidence_level, or readiness behavior.
```

The adapter must be a boundary layer, not a matcher, parser, evidence extractor, reviewer UI, or delivery writer.

## Adapter boundary design

Required decision:

```text
adapter_boundary =
  after comparison/discrepancy boundary validation
  before production review_queue persistence or delivery report writing
```

Recommended future module, when implementation is explicitly assigned:

```text
datefac_agent/review/discrepancy_review_queue_adapter.py
```

Recommended boundary flow:

```text
comparison/evidence runner
  -> normalized comparison_result records
  -> discrepancy integration boundary
  -> production-boundary review queue adapter
  -> review_queue candidate records
  -> future review persistence/export layer
```

The adapter may receive only validated boundary outputs, not raw MinerU blocks or raw Excel rows. It must preserve audit metadata and fail closed when the upstream boundary is absent, incomplete, or stale.

Adapter responsibilities:

```text
validate adapter input contract
map non-VERIFIED rows to production review_queue candidate records
preserve discrepancy_report_rows as auditable report outputs
preserve blocked_delivery_rows as delivery blockers
retain run_id / adapter_version / input_file_hashes / audit hashes
enforce bounded previews and metadata-only evidence references
emit structured diagnostics on blocked or invalid input
```

Adapter non-responsibilities:

```text
no MinerU parsing
no OCR / LLM / VLM calls
no PDF extraction
no source_text matching
no clean_data writing
no STRONG_EVIDENCE promotion
no readiness gate mutation
no reviewer UI or authorization logic
```

## Allowed inputs

Required decision:

```text
allowed_input_contract =
  validated comparison_result rows
  validated discrepancy boundary outputs
  metadata-only evidence references
  deterministic audit metadata
  closed readiness snapshot
```

Allowed top-level payload fields:

```text
run_id
run_timestamp
adapter_version
adapter_contract_version
git_branch
git_commit_head
input_file_hashes
source_document_id
comparison_result_rows
review_queue_items
discrepancy_report_rows
blocked_delivery_rows
audit_metadata
readiness_gates
external_call_counts
```

Allowed row/evidence fields:

```text
source_row_id
source_document_id
source_sheet
excel_row_number
candidate_metric_name
candidate_period
candidate_value
candidate_unit
candidate_page_number
agreement_status
source_text_status
evidence_type
matched_source_text_id
matched_page_number
matched_locator
matched_block_index
matched_text_sha256
matched_char_count
evidence_preview
evidence_preview_sha256
alternative_evidence_candidates
match_reason
risk_reason
suggested_action
severity
review_status
reviewer_decision
audit_hash
review_item_id
```

Input integrity rules:

```text
run_id must be present and stable.
adapter_version must be present.
input_file_hashes must be non-empty and bind the source files.
readiness_gates must remain closed.
external_call_counts must be present and must not imply unapproved MinerU/OCR/LLM/VLM runs.
review_item_id and audit_hash must be deterministic and non-empty for review_queue candidates.
```

## Forbidden inputs

Required decision:

```text
forbidden_input_contract =
  reject raw/full source payloads, raw extraction dumps, unstamped outputs, and any input that implies clean/readiness promotion.
```

Forbidden inputs:

```text
full source_text
full_source_text
source_text_full
raw_mineru_block
full_table_html
raw PDF text dump
raw DateFac workbook row dump
complete MinerU content_list_v2
committed output/comparison artifacts
rows without run_id
rows without adapter_version
rows without input_file_hashes
reviewer notes used as source evidence
unbounded evidence_preview
unknown agreement_status
clean_data_admitted=true
evidence_level=STRONG_EVIDENCE caused only by VERIFIED
client_ready=true
production_ready=true
formal_client_export_allowed=true
```

Forbidden source paths:

```text
output/
input/
temp/
data/
legacy output folders
DateFac Excel files as committed adapter payloads
MinerU output as committed adapter payloads
```

If any forbidden field or stale/untrusted payload is present, the adapter must fail closed before producing review_queue or delivery-clean outputs.

## Comparison result mapping

Required decision:

```text
comparison_result_mapping =
  map validated comparison_result rows by agreement_status, never by raw text or implicit trust.
```

Status mapping:

```text
VERIFIED -> no discrepancy review_queue item by default; retain audit summary only
UNVERIFIED -> production review_queue candidate, partial_anchor_queue
DISAGREED -> production review_queue candidate, evidence_conflict_queue
AMBIGUOUS -> production review_queue candidate, evidence_ambiguity_queue
MISSING_EVIDENCE -> production review_queue candidate, missing_evidence_queue
PARSE_SKIPPED -> production review_queue candidate, parse_schema_queue
unknown status -> fail closed
```

Mapping invariants:

```text
non-VERIFIED rows must enter review_queue candidate output.
VERIFIED rows must not bypass clean gate.
VERIFIED rows must not become STRONG_EVIDENCE by status alone.
VERIFIED rows may appear in audit summaries or sampled QA only while readiness is closed.
row counts must reconcile: total = VERIFIED + non-VERIFIED.
review_queue candidate count must equal count(non-VERIFIED rows) unless explicit fail-closed diagnostics explain exclusion.
```

## Review queue item mapping

Required decision:

```text
review_queue_item_mapping =
  convert validated review_queue_items into production review_queue candidate records with immutable source/audit fields and separate mutable reviewer fields.
```

Production review_queue candidate fields:

```text
review_item_id
review_item_version
adapter_contract_version
run_id
source_document_id
source_row_id
source_sheet
excel_row_number
candidate_metric_name
candidate_period
candidate_value
candidate_unit
candidate_page_number
agreement_status
source_text_status
evidence_type
matched_source_text_id
matched_page_number
matched_locator
matched_block_index
matched_text_sha256
matched_char_count
evidence_preview
evidence_preview_sha256
alternative_evidence_candidates
match_reason
risk_reason
suggested_action
severity
review_subqueue
review_status
reviewer_decision
reviewer_corrected_metric
reviewer_corrected_period
reviewer_corrected_value
reviewer_corrected_unit
reviewer_selected_source_text_id
reviewer_selected_locator
reviewer_note
reviewed_by
reviewed_at
post_review_policy_gate_status
post_review_clean_data_eligible
audit_hash
review_decision_hash
adapter_version
input_file_hashes
created_at
```

Separation rules:

```text
source/audit fields are immutable after adapter creation.
reviewer fields are mutable only through a future reviewer action workflow.
audit_hash covers immutable source/audit fields.
review_decision_hash, if present, covers mutable reviewer decision fields.
clean_data eligibility is not clean_data admission.
```

## Discrepancy report mapping

Required decision:

```text
discrepancy_report_mapping =
  keep discrepancy_report_rows as audit/report output, not as clean data or source evidence.
```

Discrepancy report rows should include:

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
source_text_status
evidence_type
matched_locator
matched_text_sha256
evidence_preview
risk_reason
suggested_action
clean_data_eligible
audit_hash
run_id
adapter_version
```

Discrepancy report rows may be exported in demo/review outputs only while readiness gates are closed. They must not be interpreted as production-ready clean data.

## Blocked delivery mapping

Required decision:

```text
blocked_delivery_mapping =
  unresolved or ineligible discrepancy rows must produce delivery blockers, not clean rows.
```

Blocked delivery rows should carry:

```text
review_item_id
source_row_id
agreement_status
review_subqueue
severity
review_status
reviewer_decision
blocked_reason
blocking_scope
source_document_id
run_id
audit_hash
```

Blocking policy:

```text
unresolved DISAGREED -> block affected row and high-risk summary claim
unresolved AMBIGUOUS -> block affected row until evidence selected or marked insufficient
unresolved MISSING_EVIDENCE -> block affected row until evidence supplied or excluded
unresolved UNVERIFIED -> block affected row until evidence sufficiency decision
unresolved PARSE_SKIPPED -> block affected row if candidate-like; otherwise route to metadata/non-data exclusion
```

Blocked rows may appear in review/discrepancy outputs. They must not appear in delivery clean output.

## Clean data gate boundary

Required decision:

```text
clean_data_gate_policy =
  adapter can prepare review/re-audit candidates but never writes clean_data and never admits rows to clean delivery.
```

Rules:

```text
VERIFIED cannot bypass clean gate.
VERIFIED cannot become STRONG_EVIDENCE automatically.
VERIFIED cannot enter clean_data by adapter mapping alone.
non-VERIFIED rows default clean_data_eligible=false.
reviewer action may only set eligible_for_reaudit after explicit policy checks.
eligible_for_reaudit is not clean_data_admitted.
clean_data admission requires a separate future clean gate and re-audit pass.
```

Future clean gate prerequisites:

```text
row family allowed by clean_candidate_policy
metric/period/value/unit normalized
evidence binding is trusted and metadata-bound
no unresolved critical/high review item
reviewer decision, if any, is explicit and auditable
output_schema_guardrails pass
readiness remains closed unless explicitly changed by a separate readiness task
```

## Evidence preview boundary

Required decision:

```text
evidence_preview_policy =
  previews remain bounded, metadata-first, and never become a full source_text channel.
```

Allowed evidence preview payload:

```text
source_text_id
source_document_id
page_number
locator
block_index
evidence_type
text_sha256
char_count
evidence_preview, bounded to a configured limit such as 160 or 240 characters
caption_preview / footnote_preview, bounded
alternative_evidence_candidates, capped
```

Forbidden evidence preview payload:

```text
source_text
full_source_text
unbounded text
raw MinerU block
full table HTML
raw workbook row dump
raw PDF page text dump
```

Validation:

```text
preview length must be checked before serialization.
alternative evidence lists must be capped and sorted deterministically.
hash and locator metadata must be retained when evidence is source-text-backed.
missing locator/hash should fail closed for source-text-backed review candidates.
```

## Audit / reproducibility boundary

Required decision:

```text
audit_metadata_policy =
  every adapter output must preserve enough immutable metadata to reproduce and audit the boundary decision without storing full source text.
```

Required audit metadata:

```text
run_id
run_timestamp
git_branch
git_commit_head
adapter_contract_version
adapter_version
input_file_hashes
source_document_id
comparison_row_count
review_queue_count
discrepancy_report_count
blocked_delivery_row_count
verified_without_clean_gate_count
readiness_gates
external_call_counts
audit_metadata_hash
```

Hash policy:

```text
review_item_id = deterministic from run_id + source_row_id + status + candidate value + matched locator/hash.
audit_hash = deterministic from immutable source/audit fields.
audit_metadata_hash = deterministic from run-level immutable metadata.
review_decision_hash = separate future hash over reviewer decision fields.
```

Fail closed if:

```text
run_id missing
adapter_version missing
input_file_hashes missing or empty
source_document_id missing
review_item_id missing for non-VERIFIED candidate
audit_hash missing or non-deterministic
readiness snapshot missing
external_call_counts missing
```

## Reviewer action boundary

Required decision:

```text
reviewer_action_policy =
  reviewer actions can resolve review state or prepare re-audit candidates, but cannot directly create clean_data, STRONG_EVIDENCE, or readiness.
```

Allowed future reviewer actions:

```text
ACCEPT_CANDIDATE
REJECT_CANDIDATE
CORRECT_VALUE
CORRECT_UNIT
CORRECT_PERIOD
CORRECT_METRIC
SELECT_EVIDENCE
MARK_NOT_IN_REPORT
MARK_EVIDENCE_INSUFFICIENT
REQUEST_REEXTRACTION
REQUEST_MANUAL_SOURCE_CHECK
```

Reviewer action requirements:

```text
reviewer_id
reviewed_at
reviewer_note for accept/correct/select actions
selected locator/hash for SELECT_EVIDENCE
corrected field value for CORRECT_* actions
explicit_policy_gate marker for any eligible_for_reaudit transition
```

Reviewer action cannot:

```text
set clean_data_admitted=true
set evidence_level=STRONG_EVIDENCE
open client_ready / production_ready / formal_client_export_allowed
erase source audit_hash
replace source evidence without locator/hash
```

Unsupported reviewer action must fail closed.

## Fail-closed / rollback policy

Required decision:

```text
fail_closed_policy =
  invalid adapter input produces diagnostics and no review_queue persistence or clean delivery output.
```

Fail-closed triggers:

```text
unknown agreement_status
missing required comparison fields
missing run_id / adapter_version / input_file_hashes
stale or mismatched input_file_hashes
unbounded evidence_preview
presence of full source_text in adapter payload
source-text-backed candidate without locator/hash
non-deterministic review_item_id or audit_hash
unsupported reviewer action
attempted clean_data admission
attempted STRONG_EVIDENCE promotion
attempted readiness gate mutation
output artifacts staged as source
```

Required decision:

```text
rollback_policy =
  if adapter validation fails after partial processing, discard generated adapter outputs and emit BLOCKED diagnostics only.
```

Rollback behavior:

```text
do not mutate clean_data.
do not write production review_queue records.
do not update delivery manifests as success.
do not alter readiness gates.
record run_id, validation errors, and blocked reason.
require QA before retrying integration.
```

## Readiness gate policy

Required decision:

```text
readiness_gate_policy =
  R7AT keeps all readiness gates closed; future adapter implementation cannot open gates.
```

Demo export may be allowed only when:

```text
output is explicitly labeled demo/review-only.
unresolved rows are excluded from clean_data.
readiness_gates are recorded as closed.
external_call_counts are recorded.
review/discrepancy outputs are metadata-first.
no full source_text is serialized.
```

Readiness gates can be considered in a future task only after:

```text
production-boundary adapter contract has implementation and QA.
multi-document fixtures pass.
controlled local dry-run passes.
output_schema_guardrails pass.
reviewer action workflow and audit logging are implemented.
clean_data gate is separately designed, implemented, and QA-reviewed.
no unresolved critical/high review items remain for the target export scope.
evidence_index/review_queue outputs remain metadata-only.
manual approval explicitly changes readiness flags.
```

R7AT decision:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Future implementation slice

Required decision:

```text
future_implementation_scope =
  first implement a test-only production-boundary adapter contract prototype, not production wiring.
```

Recommended next implementation after QA:

```text
tests/agent/production_boundary_review_queue_adapter_contract_348n.py
tests/agent/test_production_boundary_review_queue_adapter_contract_348n.py
small in-test payloads or compact fixture only
no datefac_agent/ production code
no runner
no real R7AO output
no MinerU/OCR/LLM/VLM
no readiness change
```

Prototype should prove:

```text
validated R7AS-shaped output maps to production review_queue candidate contract.
forbidden inputs fail closed.
metadata-only evidence preview remains bounded.
blocked_delivery_rows prevent clean delivery.
VERIFIED remains non-promotional and not auto-clean.
reviewer action outputs require future policy gates.
audit metadata and hashes are retained.
```

Required decision:

```text
next_task_name = 348N-R7AT-QA production-boundary review queue adapter design review
```

Rationale:

```text
Because R7AT is design-only, the next safe task is QA review of this design before any contract prototype is written.
```

## Boundary review

R7AT stayed design-only:

```text
datefac_agent/ modified = no
tests/ modified = no
implementation created = no
runner created = no
fixture created = no
output committed = no
DateFac Excel committed = no
MinerU output committed = no
MinerU run = no
OCR / LLM / VLM run = no
real PDF extraction = no
dependencies added = no
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
  ?? docs/agent/348N_R7AT_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN.md

git diff --stat
  no tracked diff before staging because the design report was untracked

git diff --name-only
  no tracked diff before staging because the design report was untracked

git diff --check
  PASS
```

## Limitations

- This is a design-only report.
- No production adapter module exists yet.
- No test-only contract prototype is created in this task.
- No reviewer persistence, reviewer identity store, UI, authorization, or production audit log is implemented.
- The future production module path is a recommendation only.
- Readiness gates remain closed.
- `VERIFIED` remains a non-promotional comparison status, not clean admission.

## Decision

```text
Decision = 348N_R7AT_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN_VALID
```

R7AT defines a conservative production-boundary adapter design. The adapter should sit after validated comparison/discrepancy outputs and before future production review_queue persistence. It must accept only metadata-first, bounded, hash-bound inputs; route all non-VERIFIED rows into review_queue candidates; preserve discrepancy and blocked-delivery outputs; keep VERIFIED non-promotional; require separate clean/re-audit gates; fail closed on unsafe inputs; and keep readiness gates closed.

## Recommended next task

```text
348N-R7AT-QA production-boundary review queue adapter design review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS：348N_R7AT_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN_VALID
build_result（构建结果）= PASS：py_compile validation passed
test_result（测试结果）= PASS：pytest tests/agent/test_discrepancy_review_queue_integration_boundary_348n.py -q => 14 passed；pytest tests/agent -q => 227 passed
files_modified（修改文件数）= 1：docs/agent/348N_R7AT_PRODUCTION_BOUNDARY_REVIEW_QUEUE_ADAPTER_DESIGN.md
error_count（错误数）= 0
adapter_boundary_result（adapter边界结果）= PASS：adapter sits after validated comparison/discrepancy boundary and before future production review_queue persistence; no parser/runner/delivery responsibility
input_contract_result（输入契约结果）= PASS：allowed metadata-first inputs and forbidden raw/full/untrusted inputs are explicitly defined
review_queue_mapping_result（复核队列映射结果）= PASS：all non-VERIFIED rows route to production review_queue candidates; VERIFIED excluded from discrepancy queue and remains non-promotional
delivery_gate_policy_result（交付闸门策略结果）= PASS：blocked_delivery_rows prevent unresolved rows from delivery clean output; demo-only outputs remain separated
clean_data_gate_policy_result（clean_data闸门策略结果）= PASS：adapter cannot write clean_data or admit rows; reviewer actions can only prepare future re-audit candidates
audit_metadata_policy_result（审计元数据策略结果）= PASS：run_id / adapter_version / input_file_hashes / audit_hash / review_item_id / readiness snapshot retention specified
fail_closed_policy_result（fail-closed策略结果）= PASS：unknown statuses, missing metadata, full source_text, unbounded previews, unsupported actions, clean/readiness mutation all fail closed
readiness_gate_policy_result（就绪门策略结果）= PASS：future conditions listed; R7AT keeps client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true
boundary_check（边界检查）= PASS：docs-only; no datefac_agent/tests/fixture/output/dependency changes; no MinerU/OCR/LLM/VLM/PDF extraction
readiness_gates（就绪门）= CLOSED：client_ready=false；production_ready=false；formal_client_export_allowed=false；demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AT-QA production-boundary review queue adapter design review
```
