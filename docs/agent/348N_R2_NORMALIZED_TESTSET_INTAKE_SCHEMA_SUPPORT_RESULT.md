## Task ID

`348N-R2 Normalized Testset Intake Schema Support`

## Files Modified

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/intake/excel_intake.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md`

## Schema Detection Summary

- Added explicit `normalized_testset` header-family detection.
- Recognizes the normalized long-record header set:
  `record_id, source_pdf, source_page, table_name, statement, line_item, period, value, unit, value_text_original, confidence, note`
- The sheet is now treated as a schema-specific intake family, not generic unknown noise.

## Row-Type / Routing Behavior

- `normalized_testset` rows now route to `NORMALIZED_TESTSET_RECORD_ROW`.
- They are review-only by policy and do not enter clean data.
- Normal wide workbook rows continue to use the existing classifier.
- `clean_candidate_policy` explicitly excludes the new row type from clean-data promotion.

## Before/After Metrics

Baseline output:

- `D:\_datefac_agent\output\agent_excel_intake_audit_348n_linyang_energy_testset`

R2 output:

- `D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema`

Metric delta:

- `row_count_total: 483 -> 484`
- `review_queue_row_count: 446 -> 447`
- `clean_data_row_count: 37 -> 37`
- `unknown_row_count: 367 -> 48`
- `normalized_testset_record_row_count: 0 -> 320`
- `unit_issue_count: 9 -> 9`
- `period_issue_count: 0 -> 0`
- `valuation_issue_count: 0 -> 0`
- `evidence_issue_count: 397 -> 78`
- `strong_evidence_count: 86 -> 406`
- `weak_evidence_count: 397 -> 78`

## Clean-Data Boundary QA

Conclusion:

- clean data stayed conservative
- `normalized_testset` rows did not enter clean data
- clean-data row count stayed `37`
- clean data still contains only the previous normal clean/reference candidates

## Review-Queue QA

Conclusion:

- review queue remained large at `447`
- explainability improved materially because `320` rows now carry explicit `NORMALIZED_TESTSET_RECORD_ROW`
- residual review burden is now concentrated in the remaining non-normalized unknown families

## Unknown-Row QA

Conclusion:

- normalized testset rows stopped being generic `UNKNOWN_ROW`
- generic unknown burden fell from `367` to `48`
- remaining unknown rows now belong to other families such as `README`, `data_dictionary`, `doc_metadata`, `figure_index`, and similar non-normalized sheets

## Regression Test Summary

- Added targeted tests for normalized-testset header detection
- Added targeted tests for explicit schema-row routing
- Added tests to ensure normalized-testset rows stay out of clean data
- Added a regression check that wide-workbook classification does not regress

## Validation Commands and Results

- `python -m py_compile datefac_agent\schemas\audit_models.py datefac_agent\intake\excel_intake.py datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py`
  - result: pass
- `python -m pytest tests\agent -q`
  - result: `42 passed`
- `python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf --excel-path "D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema`
  - result: pass

## Boundary Discipline

- no legacy `datefac/` touch
- no input file mutation
- no output file commit
- no MinerU / OCR / LLM / VLM calls
- no broad policy redesign

## Decision

`348N_R2_CONFIRMED_NORMALIZED_TESTSET_SCHEMA_SUPPORT_VALID`

## Recommended Next Task

- `348N-R2-QA normalized testset schema support review`
- then separate the remaining non-normalized unknown families:
  `README`, `data_dictionary`, `doc_metadata`, `figure_index`, `related_research`, `validation_checks`
