# 348N-R7AP DateFac-MinerU discrepancy review workflow design

## Task ID

```text
348N-R7AP DateFac-MinerU discrepancy review workflow design
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AO-QA confirmed the local controlled comparison runner and outputs are valid. R7AP designs how the 49 non-VERIFIED rows become an auditable discrepancy review workflow before any production integration.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 6e02622..0634345
  Fast-forward
  created docs/codex_tasks/348N_R7AP_DateFac_MinerU_discrepancy_review_workflow_design.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git branch --show-current:
  pivot/348-agent-foundation

git log --oneline -12:
  0634345 docs: update handoff after R7AO QA
  607a782 docs: refresh plain-language progress after R7AO QA
  046e66f docs: sync progress after R7AO QA
  6341ad2 docs: add R7AP discrepancy workflow design task
  6e02622 docs: add R7AO QA review
  07ecb4c docs: update handoff after R7AO
  ccc30bd docs: refresh plain-language progress after R7AO
  c1065f5 docs: sync progress after R7AO
  78ddbd6 docs: add R7AO QA review task
  ab8175f docs: update handoff after R7AN
  7ac4823 docs: refresh plain-language progress after R7AN
  d00a921 docs: sync progress after R7AN
```

Worktree was clean after pull and before creating this design report.

## Files reviewed

Required context read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AP_DateFac_MinerU_discrepancy_review_workflow_design.md`
- `docs/agent/348N_R7AO_QA_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_REVIEW.md`
- `docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md`
- `docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md`

Production boundary files reviewed read-only:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/delivery/evidence_index_writer.py`

Local R7AO outputs reviewed read-only:

- `output/comparison/anjing_foods_mineru_adapter_r7ao/r7ao_mineru_adapter_run_metadata.json`
- `output/comparison/anjing_foods_mineru_adapter_r7ao/r7ao_mineru_adapter_unmatched_rows.csv`
- `output/comparison/anjing_foods_mineru_adapter_r7ao/r7ao_mineru_adapter_comparison_summary.md`
- `output/comparison/anjing_foods_mineru_adapter_r7ao/r7ao_mineru_adapter_comparison_report.xlsx`

No local output files were staged or committed.

## R7AO-QA recap

R7AO-QA confirmed:

```text
total rows = 451
VERIFIED = 402
non-VERIFIED = 49
UNVERIFIED = 15
DISAGREED = 5
AMBIGUOUS = 10
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 18
probe_examples_result = VERIFIED:11
MinerU adapter blocks = 89
readiness_gates = CLOSED
R7AO-QA commit = 6e02622
```

The 49 non-VERIFIED rows are the target population for a future discrepancy review workflow.

Observed examples from `r7ao_mineru_adapter_unmatched_rows.csv`:

```text
UNVERIFIED: partial value/metric/period anchors, e.g. price/share rows where anchors were incomplete.
DISAGREED: metric + period present but expected value absent with conflicting numeric candidates.
AMBIGUOUS: multiple MinerU blocks matched value + metric + period, e.g. repeated financial expense values.
MISSING_EVIDENCE: no usable MinerU evidence block for the requested candidate.
PARSE_SKIPPED: candidate row could not satisfy metric + period + single numeric value parsing, e.g. textual key info rows.
```

## Discrepancy taxonomy

Future discrepancy review should distinguish evidence disagreement from parser or candidate-shape limitations:

| Status | Meaning | Primary risk | Human task |
| --- | --- | --- | --- |
| `VERIFIED` | MinerU evidence supports value + metric + period under conservative matching. | False confidence if treated as production-ready. | No discrepancy item by default; may enter sampling QA only. |
| `UNVERIFIED` | Partial evidence exists but anchors are incomplete. | Weak source binding or value-only/metric-only evidence. | Decide whether candidate has sufficient evidence or needs correction. |
| `DISAGREED` | Metric + period evidence exists but numeric value conflicts. | Candidate may be wrong or evidence row/column may be mis-bound. | Compare candidate and evidence, then reject/correct/accept with note. |
| `AMBIGUOUS` | Multiple plausible evidence blocks match. | Wrong duplicate block may be selected. | Choose the correct evidence locator or mark insufficient. |
| `MISSING_EVIDENCE` | No usable evidence block found. | Unsupported candidate entering clean/export. | Locate evidence manually or keep excluded. |
| `PARSE_SKIPPED` | Candidate row lacks metric/period/single numeric value. | Parser issue may be confused with factual disagreement. | Normalize candidate shape, classify as metadata/non-data, or exclude. |

Decision:

```text
discrepancy_taxonomy = VERIFIED agreement, UNVERIFIED partial-anchor, DISAGREED true evidence conflict, AMBIGUOUS duplicate-evidence, MISSING_EVIDENCE no-evidence, PARSE_SKIPPED parse/schema issue.
```

## Row policy matrix

| Status | Review queue | Clean data | Export | Severity default | Required resolution |
| --- | --- | --- | --- | --- | --- |
| `VERIFIED` | No discrepancy item by default; optional QA sample queue. | Not automatically admitted; eligible only after future clean policy gate. | May appear only in demo/audit summaries while gates closed. | `INFO` | Keep metadata and source evidence id/hash. |
| `UNVERIFIED` | Yes. | Excluded until reviewer confirms evidence and policy gates pass. | Export only in review/discrepancy report, not clean output. | `MEDIUM` | Accept with evidence note, correct, or mark insufficient. |
| `DISAGREED` | Yes. | Automatically excluded. | Export as high-risk discrepancy only. | `CRITICAL` | Reject/correct candidate or document evidence conflict. |
| `AMBIGUOUS` | Yes. | Automatically excluded. | Export as ambiguity requiring locator selection. | `HIGH` | Select canonical evidence or mark insufficient. |
| `MISSING_EVIDENCE` | Yes. | Automatically excluded. | Export as missing-evidence item. | `HIGH` | Attach evidence, request manual check, or exclude. |
| `PARSE_SKIPPED` | Yes if row is candidate-like; otherwise metadata-only classification queue. | Automatically excluded. | Export separately from evidence disagreement. | `LOW` by default, escalated if core metric. | Normalize row or mark non-data/not-in-report. |

Required decisions:

```text
verified_row_policy = keep as comparison-verified only; no discrepancy item by default; no automatic STRONG_EVIDENCE/clean/readiness.
disagreed_row_policy = mandatory critical discrepancy review; clean_data excluded until corrected or rejected.
ambiguous_row_policy = mandatory high-severity review with all candidate locators shown; clean_data excluded until one locator is selected.
missing_evidence_row_policy = mandatory review; clean_data excluded until evidence is supplied and validated.
parse_skipped_row_policy = route to parse/schema review, not evidence-conflict review; clean_data excluded until normalized.
unverified_row_policy = route to partial-anchor review; clean_data excluded until evidence sufficiency is confirmed.
```

## Review queue admission policy

Future implementation policy:

```text
review_queue_admission_policy =
  include all non-VERIFIED statuses:
    UNVERIFIED
    DISAGREED
    AMBIGUOUS
    MISSING_EVIDENCE
    PARSE_SKIPPED
  exclude VERIFIED from discrepancy queue by default, but allow a sampled QA queue.
```

The review queue should include both logical rows and status-specific subqueues:

```text
evidence_conflict_queue = DISAGREED
evidence_ambiguity_queue = AMBIGUOUS
missing_evidence_queue = MISSING_EVIDENCE
partial_anchor_queue = UNVERIFIED
parse_schema_queue = PARSE_SKIPPED
```

This prevents parse failures from being mixed with true source disagreements.

## Clean data exclusion policy

Required decision:

```text
clean_data_exclusion_policy =
  all non-VERIFIED statuses are automatically excluded from clean_data.
  VERIFIED is not automatically admitted to clean_data.
  post-review acceptance grants only clean_data_eligible=true, not clean_data_admitted=true.
```

Future clean admission must still require:

```text
source row family allowed
metric/period/value/unit normalized
evidence binding available
row-level audit checks pass
no unresolved critical/high discrepancy
readiness gates explicitly remain closed unless a later task changes them
```

## Review item schema design

Future discrepancy review items should be generated from the comparison output using deterministic IDs and metadata-only evidence references.

Required fields:

```text
review_item_id
review_item_version
run_id
source_document_id
source_row_id
source_sheet
excel_row_number
candidate_metric_name
candidate_period
candidate_value
candidate_value_normalized
candidate_unit
candidate_page_number
candidate_raw_text_preview
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
reviewer_corrected_metric
reviewer_corrected_period
reviewer_corrected_value
reviewer_corrected_unit
reviewer_selected_source_text_id
reviewer_selected_locator
reviewer_note
reviewed_at
reviewed_by
post_review_clean_data_eligible
post_review_export_status
audit_hash
adapter_version
input_file_hashes
source_content_hashes
created_at
```

Schema rules:

```text
review_item_id = deterministic hash of run_id + source_row_id + agreement_status + candidate value + matched locator/hash.
audit_hash = hash of stable review item fields excluding mutable reviewer fields.
alternative_evidence_candidates = compact list of source_text_id/page/locator/hash/preview only.
candidate_raw_text_preview = bounded preview, not full workbook text dump.
```

Required decision:

```text
review_item_schema = deterministic, auditable, metadata-first schema with bounded previews and mutable reviewer decision fields separated from source/audit fields.
```

## Reviewer action model

Future reviewer actions:

| Action | Applies to | Effect |
| --- | --- | --- |
| `ACCEPT_CANDIDATE` | `UNVERIFIED`, selected `AMBIGUOUS`, rare `DISAGREED` with note | Marks candidate accepted by human, requires note and evidence locator. |
| `REJECT_CANDIDATE` | all non-VERIFIED | Keeps row out of clean_data and marks export as excluded. |
| `CORRECT_VALUE` | `DISAGREED`, `UNVERIFIED`, `PARSE_SKIPPED` | Stores corrected value and marks row eligible for re-audit. |
| `CORRECT_UNIT` | unit mismatch or parse issues | Stores corrected unit and requires re-audit. |
| `CORRECT_PERIOD` | period mismatch or parse issues | Stores corrected period and requires re-audit. |
| `CORRECT_METRIC` | alias/metric parsing issue | Stores corrected metric and requires re-audit. |
| `SELECT_EVIDENCE` | `AMBIGUOUS` | Selects canonical source_text_id/locator among alternatives. |
| `MARK_NOT_IN_REPORT` | metadata/non-financial row | Keeps out of clean_data and excludes from discrepancy denominator if policy permits. |
| `MARK_EVIDENCE_INSUFFICIENT` | missing or weak evidence | Keeps row in review/export as unresolved. |
| `REQUEST_REEXTRACTION` | likely source extraction failure | Creates follow-up task; no clean admission. |
| `REQUEST_MANUAL_SOURCE_CHECK` | source ambiguity/conflict | Requires human source check; no clean admission. |

Reviewer status lifecycle:

```text
OPEN -> IN_REVIEW -> RESOLVED_ACCEPTED | RESOLVED_CORRECTED | RESOLVED_REJECTED | UNRESOLVED_NEEDS_SOURCE_CHECK | OUT_OF_SCOPE_NOT_DATA
```

Required decision:

```text
reviewer_action_model = explicit action enum with correction fields, selected evidence locator, reviewer note, reviewer identity, and timestamp; no silent auto-fix.
```

## Evidence preview policy

Evidence previews must be useful but not leak full source text.

Policy:

```text
evidence_preview_policy =
  store source_text_id/page/locator/block_index/hash/char_count.
  store bounded evidence_preview only, recommended 160-240 characters.
  store table cell coordinate or row/column labels when available.
  store caption_preview/footnote_preview only as bounded previews.
  never serialize full source_text into review_queue, evidence_index, or discrepancy summary.
  for ambiguous rows, store a capped list of alternatives, e.g. max 5 candidates.
```

Repeated ambiguous values display:

```text
show candidate metric/period/value once
show each alternative as page + block + locator + text_sha256 + preview + evidence_type
sort alternatives by table evidence first, then paragraph, then page/block order
force reviewer to SELECT_EVIDENCE or MARK_EVIDENCE_INSUFFICIENT
```

Table-vs-paragraph conflict display:

```text
show table evidence and paragraph evidence in separate panels/rows
include evidence_type, locator, block_index, text_sha256, preview, and match_reason
do not collapse table and paragraph matches into one generic conflict
```

## Severity model

Default severity ranking:

```text
CRITICAL = DISAGREED on numeric financial candidate, especially core metrics or valuation outputs.
HIGH = AMBIGUOUS or MISSING_EVIDENCE for financial candidate.
MEDIUM = UNVERIFIED partial-anchor row with candidate-like metric/period/value.
LOW = PARSE_SKIPPED nonnumeric metadata or obvious non-financial row.
INFO = VERIFIED rows in optional sample QA only.
```

Escalation rules:

```text
core metric names, valuation metrics, or required probe-like rows increase severity by one level.
rows marked source_page_status=NO_PAGE_CAPPED_SEARCH increase severity by one level.
conflicts involving unit/period ambiguity increase severity to at least HIGH.
PARSE_SKIPPED with numeric-looking value or financial sheet source escalates to MEDIUM.
```

Required decision:

```text
severity_model = status-first severity with metric/materiality and source-binding escalation.
```

## Post-review clean_data policy

Post-review decisions do not write directly to clean_data.

Policy:

```text
post_review_clean_data_policy =
  reviewer decisions can set clean_data_eligible=true only after required fields and evidence are present.
  corrected rows must be re-run through audit checks before clean admission.
  accepted rows retain reviewer provenance and evidence locator/hash.
  rejected/out-of-scope/unresolved rows remain excluded.
  readiness gates remain CLOSED unless a future explicit task changes them.
```

Decision-to-eligibility mapping:

| Reviewer decision | Eligibility result |
| --- | --- |
| `ACCEPT_CANDIDATE` | Eligible for re-audit if evidence locator/hash and note present. |
| `CORRECT_VALUE` / `CORRECT_UNIT` / `CORRECT_PERIOD` / `CORRECT_METRIC` | Eligible only after corrected row is re-audited. |
| `SELECT_EVIDENCE` | Eligible only if selected evidence supports metric + period + value and audit passes. |
| `REJECT_CANDIDATE` | Not eligible. |
| `MARK_NOT_IN_REPORT` | Not eligible; excluded as non-data/out-of-scope. |
| `MARK_EVIDENCE_INSUFFICIENT` | Not eligible. |
| `REQUEST_REEXTRACTION` / `REQUEST_MANUAL_SOURCE_CHECK` | Not eligible until follow-up resolution. |

## Export / delivery policy

Required decision:

```text
export_policy =
  unresolved non-VERIFIED rows block formal clean export for affected rows.
  unresolved rows may appear only in review/discrepancy reports.
  demo exports must clearly label unresolved rows and exclude them from clean_data.
  no formal_client_export_allowed until production boundary and readiness tasks explicitly open gates.
```

Export fields should include:

```text
resolved_count
unresolved_count
critical_open_count
high_open_count
rows_excluded_from_clean_data
reviewer_decision_counts
open_items_by_status
open_items_by_sheet
open_items_by_metric
```

Unresolved row rule:

```text
critical/high unresolved rows block any "all rows verified" claim.
medium/low unresolved rows require explicit exclusion notes.
```

## Reporting metrics

Future discrepancy reports should include:

```text
total_candidate_rows
verified_count
non_verified_count
review_queue_count
status_counts
severity_counts
open_review_count
resolved_review_count
reviewer_decision_counts
clean_data_eligible_after_review_count
clean_data_excluded_count
core_metric_discrepancy_count
missing_evidence_count
ambiguous_evidence_count
parse_skipped_count
source_page_missing_count
table_evidence_count
paragraph_evidence_count
table_vs_paragraph_conflict_count
probe_verified_count
external_call_counts
readiness_gates
```

Metrics should distinguish:

```text
true evidence disagreement = DISAGREED
evidence ambiguity = AMBIGUOUS
evidence absence = MISSING_EVIDENCE
partial evidence = UNVERIFIED
candidate parse/schema issue = PARSE_SKIPPED
```

## Reproducibility and audit policy

Required decision:

```text
reproducibility_policy =
  every discrepancy review item must be tied to run_id, adapter_version, git commit, input file hashes, source_document_id, source row id, and evidence locator/hash.
```

Required audit fields:

```text
run_id
run_timestamp
git_branch
git_commit_head
adapter_module
adapter_version_or_source_hash
DateFac Excel path and sha256
MinerU content_list_v2 path and sha256
source_document_id
review_item_id
audit_hash
reviewer identity/timestamp for mutable review actions
readiness gates snapshot
external_call_counts
```

Hash rules:

```text
input_file_hashes bind the comparison run.
matched_text_sha256 binds the evidence preview to a source block without storing full text.
audit_hash makes source-side review item fields tamper-evident.
review_decision_hash may be added after reviewer action.
```

## Future implementation slice

Required decision:

```text
future_implementation_scope =
  implement a test-only discrepancy review queue fixture and policy prototype, not production integration.
```

Recommended R7AQ scope:

```text
create compact in-test rows for VERIFIED/UNVERIFIED/DISAGREED/AMBIGUOUS/MISSING_EVIDENCE/PARSE_SKIPPED.
implement pure test-only policy helper for review_queue admission and clean_data exclusion.
create compact review item schema as test object or small helper under tests/agent.
verify metadata-only evidence preview behavior.
verify reviewer action model transitions.
verify VERIFIED remains non-promotional.
do not read real local R7AO output in committed tests.
do not modify production datefac_agent/ yet.
```

Out of scope for R7AQ unless a future task says otherwise:

```text
production adapter integration
database-backed reviewer UI
real workbook rerun
MinerU/OCR/LLM/VLM calls
formal client export
readiness gate changes
full source_text serialization
```

Required decision:

```text
next_task_name = 348N-R7AQ test-only discrepancy review queue fixture and policy prototype
```

## Boundary review

R7AP stayed design-only:

```text
datefac_agent/ modified = no
tests/ modified = no
implementation created = no
runner script created = no
fixture created = no
local output files committed = no
DateFac Excel committed = no
MinerU output committed = no
MinerU run = no
OCR / LLM / VLM run = no
real PDF extraction = no
dependencies added = no
VERIFIED -> STRONG_EVIDENCE promotion = no
VERIFIED -> direct clean_data admission = no
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
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_mineru_artifact_adapter_348n.py -q
  21 passed in 0.14s

pytest tests/agent -q
  201 passed in 1.04s

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

- This report is design-only and does not implement a discrepancy queue.
- R7AP uses one local Anjing dry-run as the evidence base; multi-document behavior remains future work.
- R7AO local output is not committed and should remain non-source artifact.
- The current R7AM adapter is test-only; production boundary design remains future work.
- Severity/materiality rules are proposed policy and need fixture-backed validation before production use.
- Reviewer actions are workflow design only; there is no UI or persistence implementation yet.
- `VERIFIED` still does not mean `STRONG_EVIDENCE`, clean admission, client readiness, or production readiness.

## Decision

```text
Decision = 348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN_VALID
```

R7AP defines an auditable discrepancy workflow for the 49 R7AO non-VERIFIED rows. All non-VERIFIED rows enter review, all are excluded from clean_data until explicit review/re-audit gates pass, evidence previews remain bounded and metadata-first, and readiness gates remain closed.

## Recommended next task

```text
348N-R7AQ test-only discrepancy review queue fixture and policy prototype
```

Rationale:

```text
Before production integration, the policy should be reduced into compact fixtures and pure test-only helpers that prove review_queue admission, clean_data exclusion, evidence-preview metadata safety, and reviewer action transitions.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN_VALID
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent/test_mineru_artifact_adapter_348n.py -q => 21 passed; pytest tests/agent -q => 201 passed
files_modified（修改文件数）= 1，only docs/agent/348N_R7AP_DATEFAC_MINERU_DISCREPANCY_REVIEW_WORKFLOW_DESIGN.md
error_count（错误数）= 0
discrepancy_taxonomy_result（差异分类结果）= PASS，VERIFIED / UNVERIFIED / DISAGREED / AMBIGUOUS / MISSING_EVIDENCE / PARSE_SKIPPED are separated by evidence semantics
review_queue_policy_result（复核队列策略结果）= PASS，all non-VERIFIED rows enter future review_queue; VERIFIED excluded from discrepancy queue by default
review_item_schema_result（复核项schema结果）= PASS，deterministic metadata-first review item schema designed with bounded previews and audit hashes
reviewer_action_model_result（复核动作模型结果）= PASS，explicit reviewer actions and lifecycle designed; no silent auto-fix
clean_data_policy_result（clean_data策略结果）= PASS，all non-VERIFIED rows excluded; VERIFIED and post-review rows are only eligible after future policy/audit gates
export_policy_result（导出策略结果）= PASS，unresolved rows excluded from clean export and shown only in review/discrepancy outputs while readiness gates remain closed
boundary_check（边界检查）= PASS，docs-only; no datefac_agent/tests/output/dependency changes; no MinerU/OCR/LLM/VLM; no production hook
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AQ test-only discrepancy review queue fixture and policy prototype
```
