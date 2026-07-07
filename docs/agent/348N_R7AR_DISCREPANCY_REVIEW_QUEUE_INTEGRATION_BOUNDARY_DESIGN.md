# 348N-R7AR discrepancy review queue integration boundary design

## Task ID

```text
348N-R7AR discrepancy review queue integration boundary design
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

git log --oneline -12:
  a9e1637 docs: add R7AQ QA review
  0fb9a3d test: add discrepancy review queue policy prototype
  f68c59b docs: add R7AP discrepancy workflow design
  0634345 docs: update handoff after R7AO QA
  607a782 docs: refresh plain-language progress after R7AO QA
  046e66f docs: sync progress after R7AO QA
  6341ad2 docs: add R7AP discrepancy workflow design task
  6e02622 docs: add R7AO QA review
  07ecb4c docs: update handoff after R7AO
  ccc30bd docs: refresh plain-language progress after R7AO
  c1065f5 docs: sync progress after R7AO
  78ddbd6 docs: add R7AO QA review task
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
- `docs/agent/348N_R7AQ_QA_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AQ_TEST_ONLY_DISCREPANCY_REVIEW_QUEUE_FIXTURE_AND_POLICY_PROTOTYPE_REPORT.md`
- `docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md`

Read-only R7AQ prototype files:

- `tests/agent/discrepancy_review_queue_policy_348n.py`
- `tests/agent/test_discrepancy_review_queue_policy_348n.py`
- `tests/agent/fixtures/discrepancy_review_queue/r7aq_discrepancy_rows_fixture.json`

Read-only boundary files:

- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/delivery/evidence_index_writer.py`

No production code, tests, fixtures, outputs, or dependency files were modified.

## R7AQ-QA recap

R7AQ-QA confirmed:

```text
R7AQ commit = 0fb9a3d test: add discrepancy review queue policy prototype
QA commit = a9e1637 docs: add R7AQ QA review
fixture = 8-row curated synthetic fixture
review items = 7 non-VERIFIED items
VERIFIED = excluded from discrepancy review_queue and not auto-clean
all non-VERIFIED = review_queue items and clean_data_eligible=false
review_item_id / audit_hash = deterministic
evidence_preview = bounded
full source_text = not copied into review items
unsupported reviewer actions = fail closed
readiness_gates = CLOSED
```

R7AR therefore designs the future integration boundary only; it does not implement production integration.

## Integration boundary design

Decision:

```text
integration_boundary =
  a future boundary layer between comparison/audit results and delivery/review outputs.
  It should not live inside the MinerU adapter, evidence checker, clean-data policy, or runner.
```

Recommended future placement, after a separate implementation task:

```text
datefac_agent/review/discrepancy_review_boundary.py
```

Responsibilities:

```text
consume normalized comparison_result records
validate required run/evidence metadata
map non-VERIFIED rows to review_queue items
preserve metadata-first evidence references
emit review/discrepancy outputs only
set clean_data_eligible=false by default
block delivery clean output for unresolved discrepancy rows
```

Non-responsibilities:

```text
no MinerU parsing
no OCR / LLM / VLM calls
no PDF extraction
no direct clean_data writing
no STRONG_EVIDENCE promotion
no readiness gate changes
no reviewer UI or persistence layer
```

Layering:

```text
comparison runner / evidence adapter
  -> comparison_result rows
  -> discrepancy integration boundary
  -> review_queue / discrepancy report metadata
  -> future reviewer decisions
  -> re-audit / clean gate, not direct clean admission
```

## Allowed / forbidden inputs

Decision:

```text
allowed_inputs =
  structured comparison_result rows
  source_text metadata only
  run metadata
  adapter_version
  input_file_hashes
  source_document_id
  existing row ids / sheet names / row indexes
  bounded evidence_preview
  reviewer decisions with explicit reviewer identity/timestamp in a later workflow
```

Allowed comparison fields:

```text
source_row_id
source_document_id
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
match_reason
risk_reason
suggested_action
source_sheet
excel_row_number
run_id
adapter_version
input_file_hashes
```

Decision:

```text
forbidden_inputs =
  raw unbounded source_text
  full MinerU output as review item payload
  full DateFac Excel as review item payload
  output/comparison files as committed source
  OCR / LLM / VLM generated evidence without explicit future policy
  reviewer notes as factual evidence
  unversioned local paths without file hashes
  rows missing run_id / adapter_version / input_file_hashes
  any input that would imply readiness or clean admission by presence alone
```

Input validation rule:

```text
If required metadata is absent or malformed, fail closed and emit no clean_data eligibility.
```

## Review queue item mapping

Decision:

```text
review_queue_item_mapping =
  VERIFIED -> no discrepancy review item by default
  UNVERIFIED -> partial_anchor_queue
  DISAGREED -> evidence_conflict_queue
  AMBIGUOUS -> evidence_ambiguity_queue
  MISSING_EVIDENCE -> missing_evidence_queue
  PARSE_SKIPPED -> parse_schema_queue
```

Mapping fields:

```text
comparison_result.row_id -> review_item.source_row_id
metric_name -> candidate_metric_name
period -> candidate_period
value -> candidate_value
unit -> candidate_unit
page_number -> candidate_page_number
agreement_status -> agreement_status
source_text_status -> source_text_status
evidence_type -> evidence_type
matched_page / locator / block_index -> matched_page_number / matched_locator / matched_block_index
matched_text_sha256 / char_count -> matched_text_sha256 / matched_char_count
match_reason / risk_reason / suggested_action -> same-name review fields
run metadata -> run_id / adapter_version / input_file_hashes
```

Required review item behavior:

```text
review_item_id is deterministic.
audit_hash is deterministic over source/audit fields.
review_status starts OPEN.
reviewer fields start empty.
clean_data_eligible starts false.
export_bucket starts discrepancy_review_output.
```

Review queue counts must preserve:

```text
review_queue_count = count(non-VERIFIED rows)
status_counts by agreement_status
subqueue_counts by review_subqueue
severity_counts
```

## Clean data gate boundary

Decision:

```text
clean_data_gate_boundary =
  discrepancy boundary never writes clean_data.
  discrepancy boundary only emits review/discrepancy items.
```

Rules:

```text
VERIFIED cannot bypass clean_data gate.
VERIFIED cannot become STRONG_EVIDENCE automatically.
VERIFIED can only be considered by a future clean gate after normal row-family, audit, and evidence checks.
all non-VERIFIED rows are automatically clean_data_eligible=false.
reviewer action can at most set eligible_for_reaudit=true in a future workflow.
eligible_for_reaudit is not clean_data_admitted.
clean_data admission requires a separate re-audit pass and existing output guardrails.
```

Future clean gate checks:

```text
row family allowed for clean_data
metric/period/value/unit normalized
source evidence metadata present and trusted by policy
no unresolved critical/high discrepancy
reviewer decision, if present, is explicit and auditable
output_schema_guardrails still pass
readiness gates remain closed unless explicitly opened by a separate task
```

## Evidence preview boundary

Decision:

```text
evidence_preview_boundary =
  review_queue and evidence_index may store only metadata and bounded previews.
```

Allowed evidence fields:

```text
source_text_id
source_document_id
page_number
locator
block_index
evidence_type
text_sha256
char_count
evidence_preview, bounded to a future configured limit
caption_preview / footnote_preview, bounded
alternative_evidence_candidates, capped and metadata-first
```

Forbidden evidence fields:

```text
source_text
full_source_text
source_text_full
unbounded text
raw MinerU block content
full table HTML
full workbook row dump
```

Preview policy:

```text
default preview_limit should be explicit, e.g. 160 or 240 characters.
all previews must be generated by truncation before serialization.
full text may be used only transiently inside a trusted evidence matcher, not written to review/delivery outputs.
```

## Audit / reproducibility boundary

Decision:

```text
audit_hash_boundary =
  every review item must include run_id, adapter_version, input_file_hashes, source_document_id, source_row_id, locator/hash metadata, and deterministic audit_hash.
```

Required reproducibility fields:

```text
run_id
run_timestamp
git_commit_head
adapter_version
adapter_source_hash when available
input_file_hashes
source_document_id
source_row_id
review_item_id
audit_hash
matched_text_sha256
matched_locator
readiness_gates snapshot
external_call_counts
```

Hash rules:

```text
review_item_id = deterministic from run_id + source_row_id + status + candidate value + matched locator/hash.
audit_hash = deterministic from immutable source/audit fields.
reviewer decision hash, if later added, must be separate from audit_hash.
changing reviewer_note must not mutate the original source audit_hash.
```

Fail-closed audit cases:

```text
missing run_id
missing adapter_version
missing input_file_hashes
missing source_document_id
missing source_row_id
missing hash/locator for a source_text-backed item
non-deterministic item id or audit hash
```

## Reviewer action boundary

Decision:

```text
reviewer_action_boundary =
  reviewer action may resolve review state but cannot directly produce clean_data or readiness.
```

Allowed future reviewer actions:

```text
ACCEPT_CANDIDATE
REJECT_CANDIDATE
CORRECT_VALUE
CORRECT_UNIT
CORRECT_PERIOD
CORRECT_METRIC
MARK_NOT_IN_REPORT
MARK_EVIDENCE_INSUFFICIENT
REQUEST_REEXTRACTION
REQUEST_MANUAL_SOURCE_CHECK
SELECT_EVIDENCE
```

Rules:

```text
unsupported actions fail closed.
reviewer action requires reviewer id and timestamp in future persistent workflows.
ACCEPT_CANDIDATE requires an evidence locator/hash and reviewer note.
CORRECT_* actions require corrected fields and re-audit.
SELECT_EVIDENCE requires one candidate source_text_id/locator from the bounded alternatives.
REQUEST_* actions keep row unresolved.
MARK_NOT_IN_REPORT excludes row from clean_data and delivery clean output.
```

Reviewer decisions can affect only:

```text
review_status
reviewer_decision
reviewer_corrected_* fields
reviewer_selected_* fields
reviewer_note
eligible_for_reaudit
post_review_export_status
```

Reviewer decisions cannot affect directly:

```text
evidence_level = STRONG_EVIDENCE
clean_data admission
client_ready
production_ready
formal_client_export_allowed
```

## Export / delivery boundary

Decision:

```text
export_boundary =
  discrepancy report export is allowed in future controlled runs.
  delivery clean export remains blocked for unresolved discrepancy rows.
```

Allowed future discrepancy report outputs:

```text
discrepancy_review_queue.csv/json
discrepancy_summary.md
review_item_manifest.json
status/severity/subqueue counts
bounded evidence previews
audit metadata and input hashes
```

Forbidden future exports until separate readiness tasks:

```text
formal client clean export
production-ready delivery
rows marked clean only because VERIFIED
rows marked clean only because reviewer accepted without re-audit
unresolved non-VERIFIED rows in clean_data
full source_text in evidence_index or review_queue
```

Delivery rules:

```text
unresolved CRITICAL/HIGH rows block any all-clear claim.
unresolved rows may appear only in discrepancy/review outputs.
resolved rows still require re-audit before clean output.
discrepancy report must carry readiness_gates CLOSED.
```

## Rollback / fail-closed policy

Decision:

```text
rollback_boundary =
  if integration boundary validation fails, produce review-only diagnostics and no clean_data changes.
```

Fail-closed triggers:

```text
unknown agreement_status
missing required comparison fields
missing run_id / adapter_version / input_file_hashes
unbounded evidence_preview
presence of full source_text in review item output
non-deterministic review_item_id or audit_hash
unsupported reviewer action
attempted clean_data_eligible without explicit policy gate and re-audit marker
attempted STRONG_EVIDENCE promotion
attempted readiness gate change
attempted output commit of DateFac Excel, MinerU output, or local comparison output
```

Rollback behavior:

```text
do not mutate clean_data
do not mutate readiness flags
do not emit production delivery
write or report BLOCKED/FAIL diagnostics only
preserve input/run metadata for audit
require a new QA task before retrying integration
```

## Validation boundary

Decision:

```text
validation_boundary =
  future integration must be validated first with test-only fixtures, then controlled local outputs, before any production code path.
```

Minimum validation ladder:

```text
1. test-only fixture prototype under tests/agent
2. QA of fixture prototype
3. integration-boundary design
4. test-only integration-boundary prototype
5. QA of integration-boundary prototype
6. controlled local dry-run, no commit of outputs
7. QA of controlled dry-run
8. production-boundary design, still no readiness changes
```

Required test categories for the next prototype:

```text
VERIFIED excluded from discrepancy queue and not auto-clean
all non-VERIFIED statuses mapped to expected subqueues
metadata-first review item fields
bounded preview enforcement
full source_text rejection
deterministic review_item_id/audit_hash
reviewer action fail-closed behavior
clean gate separation
export bucket separation
readiness gates unchanged
```

## Future implementation slice

Decision:

```text
future_implementation_slice =
  create a test-only integration boundary prototype, not production integration.
```

Recommended next scope:

```text
tests/agent/discrepancy_review_integration_boundary_348n.py
tests/agent/test_discrepancy_review_integration_boundary_348n.py
small fixture or in-test rows only
no real R7AO output
no production datefac_agent/ changes
no runner
no MinerU/OCR/LLM/VLM
```

Prototype goals:

```text
accept normalized comparison_result-like records
validate allowed/forbidden inputs
map to review items using R7AQ policy shape
reject full source_text fields
enforce run_id/adapter_version/input_file_hashes
separate review output from clean output
prove rollback/fail-closed behavior
```

Decision:

```text
next_task_name = 348N-R7AS test-only discrepancy review queue integration boundary prototype
```

## Boundary review

R7AR stayed design-only:

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
python -m py_compile tests/agent/discrepancy_review_queue_policy_348n.py tests/agent/test_discrepancy_review_queue_policy_348n.py
  PASS

python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_discrepancy_review_queue_policy_348n.py -q
  12 passed in 0.09s

pytest tests/agent -q
  213 passed in 0.87s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git diff --stat
  no output before report creation

git diff --name-only
  no output before report creation

git diff --check
  PASS
```

## Limitations

- This report is design-only and does not implement integration.
- R7AQ policy remains test-only and under `tests/agent/`.
- No production module path is created in R7AR.
- No real R7AO output, DateFac Excel, or MinerU artifact is committed.
- The future placement under `datefac_agent/review/` is a design recommendation only.
- Reviewer persistence, UI, authorization, and audit log storage remain future design/implementation work.
- Multi-document dry-run is still useful later, but the immediate next slice should prove the integration boundary with compact test-only inputs first.

## Decision

```text
Decision = 348N_R7AR_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_DESIGN_VALID
```

R7AR defines a conservative integration boundary: structured comparison results can map to metadata-first discrepancy review items, all non-VERIFIED rows remain out of clean_data, VERIFIED cannot bypass clean gates, evidence previews stay bounded, audit metadata remains deterministic, unsupported or unsafe inputs fail closed, and readiness gates remain closed.

## Recommended next task

```text
348N-R7AS test-only discrepancy review queue integration boundary prototype
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AR_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_DESIGN_VALID
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent/test_discrepancy_review_queue_policy_348n.py -q => 12 passed; pytest tests/agent -q => 213 passed
files_modified（修改文件数）= 1，only docs/agent/348N_R7AR_DISCREPANCY_REVIEW_QUEUE_INTEGRATION_BOUNDARY_DESIGN.md
error_count（错误数）= 0
integration_boundary_result（集成边界结果）= PASS，boundary is after comparison results and before review/delivery outputs; no production hook or clean admission
clean_data_gate_boundary_result（clean_data闸门边界结果）= PASS，VERIFIED cannot bypass clean gate; all non-VERIFIED remain clean_data_eligible=false until future re-audit policy
review_queue_mapping_result（复核队列映射结果）= PASS，non-VERIFIED statuses map to partial_anchor/evidence_conflict/evidence_ambiguity/missing_evidence/parse_schema queues
evidence_preview_boundary_result（证据预览边界结果）= PASS，bounded metadata-first previews only; full source_text forbidden from review_queue/evidence_index outputs
audit_boundary_result（审计边界结果）= PASS，run_id/adapter_version/input_file_hashes/review_item_id/audit_hash retained and fail-closed if missing
export_boundary_result（导出边界结果）= PASS，discrepancy report export allowed in future controlled runs; unresolved rows blocked from delivery clean output
boundary_check（边界检查）= PASS，docs-only; no datefac_agent/tests/fixture/output/dependency changes; no MinerU/OCR/LLM/VLM; no readiness change
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AS test-only discrepancy review queue integration boundary prototype
```
