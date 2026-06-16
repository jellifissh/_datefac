# 348A-R4-QA Clean Data Candidate Policy Review

## Task ID

`348A-R4-QA Clean Data Candidate Policy Review`

## Input Output Directory Reviewed

`D:\_datefac_agent\output\agent_excel_intake_audit_348a_r4`

Reviewed files:

- `agent_excel_intake_audit_348a_manifest.json`
- `agent_excel_intake_audit_348a_run_summary.json`
- `audit_report.md`
- `evidence_index.json`
- `review_queue.csv`
- `clean_data.csv`

## Manifest Decision

Primary QA decision:

`348A_R4_QA_CONFIRMED_INTERNAL_CLEAN_CANDIDATE_POLICY_USEFUL`

Supporting decisions:

- `348A_R4_QA_CONFIRMED_READY_FOR_SECOND_REAL_WORKBOOK`
- `348A_R4_QA_CONFIRMED_READY_FOR_FIXTURE_HARVEST`

## Verified Key Metrics

Verified from manifest, run summary, clean data, review queue, and evidence index:

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `row_count_total = 82`
- `row_count_audited = 82`
- `pass_count = 0`
- `review_count = 82`
- `fail_count = 0`
- `issue_count_total = 84`
- `unit_issue_count = 0`
- `period_issue_count = 2`
- `valuation_issue_count = 0`
- `evidence_issue_count = 82`
- `clean_data_row_count = 75`
- `review_queue_row_count = 7`
- `internal_clean_candidate_count = 65`
- `internal_reference_candidate_count = 10`
- `narrative_review_count = 5`
- `review_required_count = 2`
- `excluded_from_clean_data_count = 0`
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

Cross-check:

- `clean_data.csv` contains `75` rows.
- `review_queue.csv` contains `7` rows.
- `75 + 7 = 82`, matching `row_count_total`.
- `evidence_index.json` contains `82` entries with candidate labels for every row.

## Clean-Data Candidate Quality Analysis

### 1. Does `clean_data.csv` contain 75 rows

Yes.

### 2. Do all clean rows have `clean_candidate_type`

Yes.

Observed clean candidate split:

- `INTERNAL_CLEAN_CANDIDATE = 65`
- `INTERNAL_REFERENCE_CANDIDATE = 10`

### 3. Are strict financial table candidates marked correctly

Yes.

`STRICT_FINANCIAL_TABLE_ROW` rows in clean data are marked `INTERNAL_CLEAN_CANDIDATE`.

### 4. Are market reference rows marked correctly

Yes.

`MARKET_REFERENCE_ROW` rows in clean data are marked `INTERNAL_REFERENCE_CANDIDATE`.

### 5. Are there any `NARRATIVE_ASSERTION` rows in clean data

No.

`clean_data.csv` contains only:

- `STRICT_FINANCIAL_TABLE_ROW = 65`
- `MARKET_REFERENCE_ROW = 10`

### 6. Are there any `period_values_missing` rows in clean data

No.

No clean row contains `period_values_missing`.

### 7. Are there any unit / period / valuation issue rows in clean data

No.

Observed `issue_codes` in clean data:

- only `weak_evidence`

No clean row contains:

- unit issue code
- period issue code
- valuation issue code

### 8. Quality conclusion

The R4 clean-data split is internally coherent and matches the intended policy:

- weak-evidence-only strict financial rows entered internal clean candidates;
- weak-evidence-only market reference rows entered internal reference candidates;
- narrative and period-problem rows stayed out.

## Review Queue Quality Analysis

### 1. Does `review_queue.csv` contain 7 rows

Yes.

### 2. Are the 7 rows the expected groups

Yes.

Observed split:

- `5` rows = `NARRATIVE_ASSERTION` + `NARRATIVE_REVIEW`
- `2` rows = `STRICT_FINANCIAL_TABLE_ROW` + `REVIEW_REQUIRED`

The two strict rows are:

- `现金流量表 / 经营活动现金流`
- `现金流量表 / 每股指标 (元)`

Both carry `period_values_missing;weak_evidence`.

### 3. Does review queue preserve row type, evidence level, and issue codes

Yes.

Observed review queue columns include:

- `clean_candidate_type`
- `row_type`
- `evidence_level`
- `issue_codes`

### 4. Are internal clean candidates duplicated into review queue

No duplication was found.

`INTERNAL_CLEAN_CANDIDATE` and `INTERNAL_REFERENCE_CANDIDATE` rows are absent from `review_queue.csv`.

### 5. Quality conclusion

The R4 review queue is materially cleaner than earlier stages and now acts as a true residual-review bucket rather than a dump of all weak-evidence rows.

## Evidence Index Quality Analysis

`evidence_index.json` includes:

- `row_type`
- `evidence_level`
- `clean_candidate_type`

Observed evidence index split:

- `INTERNAL_CLEAN_CANDIDATE = 65`
- `INTERNAL_REFERENCE_CANDIDATE = 10`
- `NARRATIVE_REVIEW = 5`
- `REVIEW_REQUIRED = 2`

R1 and R2 distinctions are preserved:

- evidence remains `WEAK_EVIDENCE`, not collapsed back to `MISSING_EVIDENCE`
- row types remain explicit
- candidate policy is now layered on top, not replacing those distinctions

## Audit Report Quality Analysis

Positive findings:

- `audit_report.md` includes:
  - `clean_data_row_count`
  - `review_queue_row_count`
  - `internal_clean_candidate_count`
  - `internal_reference_candidate_count`
  - `narrative_review_count`
  - `review_required_count`
  - `excluded_from_clean_data_count`
- The boundary section clearly states internal clean-data candidates do not imply client or production readiness.
- The report keeps the conservative overall decision `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`.

Residual limitation:

- The report still samples issue rows more than candidate rows, so it remains audit-oriented rather than a polished internal delivery summary. That is acceptable for the current stage.

## Gate Discipline Analysis

Verified from manifest:

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`

Verified external-call counters:

- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

Gate discipline remained intact.

## Remaining Risks

- All `82` rows still remain `WEAK_EVIDENCE`, so internal clean candidates remain internal-only and not formal evidence-backed delivery.
- R4 was validated on one workbook only.
- Candidate policy is plausible and useful, but still needs either:
  - a second real workbook sample, or
  - compact fixture coverage built from known legacy edge cases.

## Recommended Refinements

Priority order:

1. `348S Second Real Workbook Pilot`
2. `348F Fixture Harvest from 346B`

Reasoning:

- The current single-sample workflow is now explainable enough to test on another real workbook.
- Fixture harvesting should follow soon after to stabilize regression coverage for candidate-policy edges.

## Decision

Primary decision:

`348A_R4_QA_CONFIRMED_INTERNAL_CLEAN_CANDIDATE_POLICY_USEFUL`

Supporting interpretation:

- `clean_data.csv` is no longer empty and does not contain narrative or period-problem rows.
- `review_queue.csv` now contains only the expected 5 narrative rows and 2 period-problem rows.
- Gate flags remain closed.
- The policy is useful for internal candidate separation and is ready for broader validation on another workbook or fixture set.
