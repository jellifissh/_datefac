# 342H Table-First Human Review Apply Simulation

## Goal

Build a sidecar `342H` apply simulation stage on top of the completed `342G` review package.

`342H` must:

- read the completed `342G` summary / QA / workbook
- look for a human-reviewed workbook under `D:/_datefac/input/table_first_review_342g_reviewed`
- validate `reviewer_decision` and correction fields
- simulate post-review outcomes without writing back to any upstream workbook
- support both:
  - waiting-for-human-review state
  - reviewed-workbook apply-simulation state

`342H` must not:

- modify production pipeline
- modify parser abstraction
- modify production extraction logic
- modify delivery or export logic
- rerun MinerU
- call any visual model or LLM
- invent fake human review conclusions
- write back to `342G` or any upstream workbook
- generate client export
- commit output artifacts

## Confirmed Upstream State

`342G` is completed and is the only formal upstream input for `342H`.

Confirmed `342G` summary:

- `audited_pdf_count = 5`
- `input_long_form_cell_count = 5607`
- `input_trusted_cell_count = 1428`
- `input_review_required_cell_count = 1005`
- `review_queue_count = 1005`
- `trusted_audit_sample_count = 150`
- `unit_year_issue_count = 4128`
- `duplicate_issue_count = 210`
- `growth_row_issue_count = 174`
- `high_priority_review_count = 702`
- `medium_priority_review_count = 437`
- `low_priority_review_count = 16`
- `review_template_row_count = 1155`
- `ready_for_342h = true`
- `recommended_342h_scope = table_first_human_review_apply_simulation`
- `qa_fail_count = 0`
- `decision = TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_READY`
- `no_write_back_proof_passed = true`

## Inputs

- `D:/_datefac/output/table_first_extraction_review_package_342g`
- optional reviewed input dir:
  - `D:/_datefac/input/table_first_review_342g_reviewed`

Preferred reviewed workbook path:

- `D:/_datefac/input/table_first_review_342g_reviewed/table_first_extraction_review_package_342g_reviewed.xlsx`

## Waiting Branch

If the reviewed workbook does not exist:

- do not crash
- do not fabricate apply results
- emit a waiting report
- set:
  - `decision = TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_WAITING_FOR_HUMAN_REVIEW`
  - `ready_for_342i = false`
  - `qa_fail_count = 0`
  - `recommended_next_action = fill_342g_review_template_first`

## Reviewed Workbook Detection

If the reviewed workbook exists, prefer:

1. `10_REVIEW_TEMPLATE`
2. `REVIEW_TEMPLATE`
3. first sheet containing `reviewer_decision`

## Allowed Reviewer Decisions

- `CONFIRM_CELL`
- `CORRECT_AND_CONFIRM`
- `REJECT_CELL`
- `KEEP_REVIEW_REQUIRED`
- `NOT_A_CORE_METRIC`
- `NEEDS_SOURCE_CHECK`

## Validation Rules

1. blank `reviewer_decision` => `PENDING_REVIEW`
2. `CONFIRM_CELL`
   - keep original metric / year / value / unit
   - `human_status = HUMAN_CONFIRMED_CELL`
3. `CORRECT_AND_CONFIRM`
   - must provide at least one corrected field
   - `human_status = HUMAN_CORRECTED_CONFIRMED_CELL`
4. `REJECT_CELL`
   - `human_status = HUMAN_REJECTED_CELL`
5. `NOT_A_CORE_METRIC`
   - `human_status = HUMAN_REJECTED_NOT_CORE`
6. `KEEP_REVIEW_REQUIRED`
   - `human_status = STILL_REVIEW_REQUIRED`
7. `NEEDS_SOURCE_CHECK`
   - `human_status = NEEDS_SOURCE_CHECK`
8. unknown decision is not allowed
9. no fake human decisions generated
10. no write-back to upstream workbooks
11. do not mix `BASIC_DATA` / metadata into confirmed core outputs
12. do not confirm excluded / rejected source rows as core confirmed results

## Outputs

Output dir:

- `D:/_datefac/output/table_first_human_review_apply_simulation_342h`

Output files:

- `table_first_human_review_apply_simulation_342h.xlsx`
- `table_first_human_review_apply_simulation_342h_summary.json`
- `table_first_human_review_apply_simulation_342h_manifest.json`
- `table_first_human_review_apply_simulation_342h_qa.json`
- `table_first_human_review_apply_simulation_342h_report.md`
- `table_first_human_review_apply_simulation_342h_no_write_back_proof.json`

Workbook sheets:

1. `00_README`
2. `01_APPLY_SUMMARY`
3. `02_INPUT_REVIEW_STATUS`
4. `03_VALIDATED_DECISIONS`
5. `04_CONFIRMED_CELLS`
6. `05_CORRECTED_CELLS`
7. `06_REJECTED_CELLS`
8. `07_STILL_REVIEW`
9. `08_NEEDS_SOURCE_CHECK`
10. `09_PENDING_REVIEW`
11. `10_REVIEW_ERRORS`
12. `11_BEFORE_AFTER`
13. `12_SOURCE_TRACE`
14. `13_342I_READINESS`
15. `14_NO_WRITE_BACK`
16. `15_NEXT_STEPS`

All sheet names must remain `<= 31` characters.

## Summary Fields

Must include at least:

- `input_review_template_row_count`
- `reviewed_row_count`
- `pending_review_count`
- `confirmed_cell_count`
- `corrected_cell_count`
- `rejected_cell_count`
- `not_core_metric_count`
- `still_review_required_count`
- `needs_source_check_count`
- `validation_error_count`
- `duplicate_review_item_count`
- `unknown_decision_count`
- `correction_without_change_count`
- `reviewer_value_parse_error_count`
- `source_trace_missing_count`
- `net_confirmed_after_human_count`
- `net_review_reduction_count`
- `ready_for_342i`
- `recommended_342i_scope`
- `recommended_next_action`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision Logic

If reviewed workbook is missing:

- `TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_WAITING_FOR_HUMAN_REVIEW`

If reviewed workbook exists and `qa_fail_count = 0`:

- `TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY`

If reviewed workbook exists but validation errors are serious:

- `TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_NOT_READY`

## Validation

```powershell
python -m py_compile datefac\benchmark\table_first_human_review_apply_simulation_342h.py datefac\benchmark\table_first_human_review_apply_simulation_342h_report.py tools\run_table_first_human_review_apply_simulation_342h.py tests\benchmark\test_table_first_human_review_apply_simulation_342h.py

python -m pytest tests\benchmark\test_table_first_human_review_apply_simulation_342h.py -q

python tools\run_table_first_human_review_apply_simulation_342h.py --review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g --reviewed-input-dir D:\_datefac\input\table_first_review_342g_reviewed --output-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h
```
