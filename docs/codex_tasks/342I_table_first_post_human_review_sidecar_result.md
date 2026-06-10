# 342I Table-First Post-Human-Review Sidecar Result

## Goal

Build a sidecar `342I` stage on top of the completed `342H` human review apply simulation.

`342I` must:

- read the current real `342H` summary / QA / workbook
- confirm `342H` is ready before generating any post-human sidecar result
- package only the currently applied human-reviewed cells
- preserve pending review rows and remaining risks
- remain strictly no-write-back

`342I` must not:

- rerun `342C6` / `342D` / old `342E` / `342F` / `342G`
- rerun `342H` unless its output is missing or not ready
- rerun MinerU
- call VLM / LLM
- modify production pipeline / parser / extraction / delivery
- write back to any upstream workbook
- generate a formal client export
- claim `client_ready = true`
- claim `production_ready = true`

## Confirmed Upstream State

Latest real `342H` state:

- `decision = TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY`
- `reviewed_workbook_exists = true`
- `input_review_template_row_count = 1155`
- `reviewed_row_count = 30`
- `pending_review_count = 1125`
- `confirmed_cell_count = 20`
- `corrected_cell_count = 10`
- `rejected_cell_count = 0`
- `still_review_required_count = 0`
- `needs_source_check_count = 0`
- `validation_error_count = 0`
- `net_confirmed_after_human_count = 30`
- `net_review_reduction_count = 30`
- `ready_for_342i = true`
- `recommended_342i_scope = table_first_post_human_review_sidecar_result`
- `recommended_next_action = proceed_to_342i`
- `qa_fail_count = 0`

## Inputs

- `D:/_datefac/output/table_first_human_review_apply_simulation_342h`
- key workbook:
  - `D:/_datefac/output/table_first_human_review_apply_simulation_342h/table_first_human_review_apply_simulation_342h.xlsx`

Preferred `342H` sheets:

- `01_APPLY_SUMMARY`
- `03_VALIDATED_DECISIONS`
- `04_CONFIRMED_CELLS`
- `05_CORRECTED_CELLS`
- `06_REJECTED_CELLS`
- `07_STILL_REVIEW`
- `08_NEEDS_SOURCE_CHECK`
- `09_PENDING_REVIEW`
- `10_REVIEW_ERRORS`
- `11_BEFORE_AFTER`
- `12_SOURCE_TRACE`
- `13_342I_READINESS`
- `14_NO_WRITE_BACK`

## Outputs

Output dir:

- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`

Output files:

- `table_first_post_human_review_sidecar_result_342i.xlsx`
- `table_first_post_human_review_sidecar_result_342i_summary.json`
- `table_first_post_human_review_sidecar_result_342i_manifest.json`
- `table_first_post_human_review_sidecar_result_342i_qa.json`
- `table_first_post_human_review_sidecar_result_342i_report.md`
- `table_first_post_human_review_sidecar_result_342i_no_write_back_proof.json`

Workbook sheets:

1. `00_README`
2. `01_RESULT_SUMMARY`
3. `02_INPUT_342H_SUMMARY`
4. `03_HUMAN_REVIEWED_CELLS`
5. `04_FINAL_CONFIRMED`
6. `05_FINAL_CORRECTED`
7. `06_FINAL_REJECTED`
8. `07_PENDING_REVIEW`
9. `08_BEFORE_AFTER`
10. `09_SOURCE_TRACE`
11. `10_METRIC_COVERAGE_AFTER`
12. `11_UNIT_YEAR_AFTER`
13. `12_REMAINING_RISKS`
14. `13_342J_READINESS`
15. `14_NO_WRITE_BACK`
16. `15_NEXT_STEPS`

All sheet names must remain `<= 31` chars.

## Core Output Logic

### Input Gates

Must confirm:

- `342H output dir exists`
- `342H summary exists`
- `342H qa exists`
- `342H workbook exists`
- `342H decision = TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY`
- `342H ready_for_342i = true`
- `342H reviewed_row_count > 0`
- `342H validation_error_count = 0`
- `342H qa_fail_count = 0`

If any key gate fails:

- `decision = TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_NOT_READY`
- `ready_for_342j = false`
- do not fabricate a misleading sidecar result

### Result Packaging

`03_HUMAN_REVIEWED_CELLS`

- merge:
  - `04_CONFIRMED_CELLS`
  - `05_CORRECTED_CELLS`
  - `06_REJECTED_CELLS`
  - `07_STILL_REVIEW`
  - `08_NEEDS_SOURCE_CHECK`

`04_FINAL_CONFIRMED`

- only `HUMAN_CONFIRMED_CELL`
- final fields use original metric / year / value / unit
- `final_status = POST_HUMAN_CONFIRMED`

`05_FINAL_CORRECTED`

- only `HUMAN_CORRECTED_CONFIRMED_CELL`
- final fields use reviewer-corrected values
- `final_status = POST_HUMAN_CORRECTED_CONFIRMED`

`06_FINAL_REJECTED`

- `HUMAN_REJECTED_CELL`
- `HUMAN_REJECTED_NOT_CORE`
- `final_status = POST_HUMAN_REJECTED`

Current first reviewed batch is expected to have:

- `rejected_cell_count = 0`

So `06_FINAL_REJECTED` may be empty but must exist.

`07_PENDING_REVIEW`

- directly preserves `342H 09_PENDING_REVIEW`
- current expectation:
  - `pending_review_count = 1125`

`08_BEFORE_AFTER`

- compare original vs final fields for each human-reviewed row
- `change_type` can be:
  - `UNCHANGED_CONFIRMED`
  - `METRIC_CORRECTED`
  - `YEAR_CORRECTED`
  - `VALUE_CORRECTED`
  - `UNIT_CORRECTED`
  - `MULTI_FIELD_CORRECTED`
  - `REJECTED`
  - `STILL_REVIEW_REQUIRED`
  - `NEEDS_SOURCE_CHECK`

`09_SOURCE_TRACE`

- preserve source evidence for all human-reviewed rows

`10_METRIC_COVERAGE_AFTER`

- summarize post-human confirmed + corrected metric coverage

`11_UNIT_YEAR_AFTER`

- summarize post-human unit / year state

`12_REMAINING_RISKS`

- summarize remaining pending / still-review / source-check risks

`13_342J_READINESS`

If:

- `342I qa_fail_count = 0`
- `post_human_confirmed_count > 0`
- `validation_error_count = 0`
- `no_write_back_proof_passed = true`

Then:

- `ready_for_342j = true`
- `recommended_342j_scope = table_first_reviewed_client_preview_pilot`

But still keep:

- `client_ready = false`
- `production_ready = false`

## Summary Fields

Must include at least:

- `input_review_template_row_count`
- `reviewed_row_count`
- `pending_review_count`
- `input_confirmed_cell_count`
- `input_corrected_cell_count`
- `input_rejected_cell_count`
- `final_confirmed_cell_count`
- `final_corrected_cell_count`
- `final_rejected_cell_count`
- `post_human_confirmed_count`
- `post_human_reviewed_cell_count`
- `metric_covered_after_human_count`
- `metric_year_pair_after_human_count`
- `pending_review_after_human_count`
- `remaining_review_count`
- `unit_year_remaining_count`
- `duplicate_remaining_count`
- `growth_row_remaining_count`
- `source_check_remaining_count`
- `validation_error_count`
- `ready_for_342j`
- `recommended_342j_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision

If `ready_for_342j = true`:

- `TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY`

Otherwise:

- `TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_NOT_READY`

## QA

Must check:

- `342H input exists`
- `342H ready_for_342i = true`
- `342H qa_fail_count = 0`
- `342H validation_error_count = 0`
- `reviewed_row_count > 0`
- no fake human decisions generated
- final confirmed rows come only from `CONFIRM_CELL / CORRECT_AND_CONFIRM`
- corrected rows actually use reviewer corrected fields
- rejected rows are not mixed into final confirmed
- pending rows are preserved
- source trace is preserved
- no upstream workbook modified
- no production pipeline / parser / extraction / delivery modified
- no output artifacts staged
- no reviewed input workbook staged
- no `client_ready = true`
- no `production_ready = true`
- no investment advice claim
- all sheet names `<= 31`
- no-write-back proof generated

## Report

Generate:

- `table_first_post_human_review_sidecar_result_342i_report.md`

The report must state:

- `342I` is a post-human-review sidecar result, not a formal financial result
- this run only applies the first reviewed batch of `30` cells
- `1125` pending review rows remain
- `client_ready = false`
- `production_ready = false`
- next step can be `342J reviewed client preview pilot`, or continued `342H1 / 342H2` review expansion

## Ledger

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Record:

- `342H` first reviewed batch applied
- `342I` completed
- status
- input
- output
- key metrics
- QA result
- decision
- next recommended task

If `342I ready_for_342j = true`:

- next recommended task = `342J Table-First Reviewed Client Preview Pilot`

Also state clearly:

- `342I` is only a sidecar result
- it covers only the first reviewed batch of `30` human-reviewed cells
- do not claim full human review completion
- do not claim `client_ready / production_ready`

## Validation

```powershell
python -m py_compile datefac\benchmark\table_first_post_human_review_sidecar_result_342i.py datefac\benchmark\table_first_post_human_review_sidecar_result_342i_report.py tools\run_table_first_post_human_review_sidecar_result_342i.py tests\benchmark\test_table_first_post_human_review_sidecar_result_342i.py

python -m pytest tests\benchmark\test_table_first_post_human_review_sidecar_result_342i.py -q

python tools\run_table_first_post_human_review_sidecar_result_342i.py --human-review-342h-dir D:\_datefac\output\table_first_human_review_apply_simulation_342h --output-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i
```
