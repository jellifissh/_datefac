## Task ID

`348N-R3 Remaining Non-Normalized Unknown-Family Refinement`

## Files Modified

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/intake/excel_intake.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `docs/agent/348N_R3_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_RESULT.md`

## Target Family Behavior

Implemented behavior:

- `README` -> `TESTSET_SUPPORTING_ROW`
- `data_dictionary` -> `TESTSET_SUPPORTING_ROW`
- `doc_metadata` -> `TESTSET_SUPPORTING_ROW`
- `figure_index` -> `TESTSET_SUPPORTING_ROW`
- `related_research` -> `TESTSET_SUPPORTING_ROW`
- `validation_checks` -> `TESTSET_SUPPORTING_ROW`
- `market_base_data` -> `MARKET_REFERENCE_ROW` only when metric / value / unit / source-page lineage are all present

Policy result:

- `TESTSET_SUPPORTING_ROW` does not enter clean data
- `validation_checks` no longer enters clean data
- `market_base_data` is explicitly recognized rather than left unknown
- `normalized_testset` remains `NORMALIZED_TESTSET_RECORD_ROW`

## Before/After Metrics

Baseline R2 output:

- `D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema`

R3 output:

- `D:\_datefac_agent\output\agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families`

Metric delta:

- `row_count_total: 484 -> 488`
- `pass_count: 398 -> 419`
- `review_count: 86 -> 69`
- `fail_count: 0 -> 0`
- `clean_data_row_count: 37 -> 33`
- `review_queue_row_count: 447 -> 455`
- `unknown_row_count: 48 -> 0`
- `normalized_testset_record_row_count: 320 -> 320`
- `testset_supporting_row_count: 0 -> 49`
- `market_reference_row_count: 2 -> 10`
- `strict_financial_table_row_count: 112 -> 109`
- `unit_issue_count: 9 -> 9`
- `period_issue_count: 0 -> 0`
- `valuation_issue_count: 0 -> 0`
- `evidence_issue_count: 78 -> 61`
- `strong_evidence_count: 406 -> 427`
- `weak_evidence_count: 78 -> 61`

## Unknown-Row QA

Conclusion:

- remaining non-normalized unknown rows dropped from `48` to `0`
- this reduction came from explicit schema-family routing, not row hiding
- row-count increase from `484` to `488` is explained by better header-family recognition:
  some sheets now expose correctly parsed data rows instead of malformed pseudo-header rows

## Clean-Data Boundary QA

Conclusion:

- clean data stayed conservative
- clean-data row count dropped from `37` to `33`
- `TESTSET_SUPPORTING_ROW` does not enter clean data
- `market_base_data` did not expand clean data because its rows are `STRONG_EVIDENCE` and stay out of internal clean/reference promotion
- `validation_checks` was removed from clean data as intended

## Review-Queue QA

Conclusion:

- review queue stayed explainable and became more explicitly family-driven
- it increased from `447` to `455`, which is acceptable because the policy remained conservative
- queue composition is now dominated by explicit `TESTSET_SUPPORTING_ROW` review rows and residual strict-row review rows

Key visible shifts:

- `README` rows are now explicit review-only support rows
- `data_dictionary` rows are now explicit review-only support rows
- `validation_checks` rows are now explicit review-only support rows
- `doc_metadata`, `figure_index`, and `related_research` are no longer generic unknowns

## Market-Base-Data Decision

Decision:

- `market_base_data` was promoted to `MARKET_REFERENCE_ROW`

Reason:

- header family is explicit
- metric / value / unit / source-page lineage is present
- routing is narrow to this sheet/header family
- clean-data acceptance did not widen

Observed result:

- `market_reference_row_count: 2 -> 10`
- all `10` market-base-data rows are `PASS`
- all `10` remain excluded from clean data because they are not weak-evidence internal-reference candidates

## Regression Test Summary

- added tests for `README` review-only routing
- added tests for `data_dictionary` review-only routing
- added tests for `figure_index` review-only routing
- added tests for `validation_checks` clean-data exclusion
- added tests for `market_base_data` narrow `MARKET_REFERENCE_ROW` routing
- preserved R2 normalized-testset behavior
- preserved normal wide-workbook classification regression coverage

## Validation Commands and Results

- `python -m py_compile datefac_agent\schemas\audit_models.py datefac_agent\intake\excel_intake.py datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py`
  - result: pass
- `python -m pytest tests\agent -q`
  - result: `48 passed`
- `python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf --excel-path "D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families`
  - result: pass

## Boundary Discipline

- no legacy `datefac/` touch
- no input file mutation
- no output file commit
- no MinerU / OCR / LLM / VLM calls
- readiness gates remained closed
- no global loosening of unit / period / valuation / evidence / clean-candidate policy

## Decision

`348N_R3_CONFIRMED_REMAINING_UNKNOWN_FAMILY_REFINEMENT_VALID`

## Recommended Next Task

- `348N-R3-QA remaining non-normalized unknown-family refinement review`
- then a separate task for the still-strict but likely testset-specific `qualitative_facts` family if future sample coverage shows it should not remain in clean data
