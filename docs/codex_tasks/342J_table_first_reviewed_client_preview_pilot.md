# 342J Table-First Reviewed Client Preview Pilot

## Goal

Build a `342J` reviewed client preview pilot on top of the current real `342I` post-human-review sidecar result.

`342J` must:

- read the current real `342I` summary / QA / workbook
- confirm `342I` is ready before generating any reviewed preview
- package only the currently human-confirmed or human-corrected rows into a demo-facing preview workbook
- preserve remaining review counts and limitation statements
- remain strictly no-write-back

`342J` must not:

- rerun `342C6` / `342D` / old `342E` / `342F` / `342G`
- rerun MinerU
- call VLM / LLM
- modify production pipeline / parser / extraction / delivery
- write back to any upstream workbook
- claim this is a full client preview
- claim `client_ready = true`
- claim `production_ready = true`
- claim full human review completion

## Confirmed Upstream State

Latest real `342I` state:

- `decision = TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY`
- `input_review_template_row_count = 1155`
- `reviewed_row_count = 80`
- `pending_review_count = 1075`
- `final_confirmed_cell_count = 31`
- `final_corrected_cell_count = 10`
- `final_rejected_cell_count = 39`
- `post_human_confirmed_count = 41`
- `metric_covered_after_human_count = 5`
- `metric_year_pair_after_human_count = 25`
- `remaining_review_count = 1075`
- `unit_year_remaining_count = 889`
- `duplicate_remaining_count = 348`
- `growth_row_remaining_count = 140`
- `ready_for_342j = true`
- `recommended_342j_scope = table_first_reviewed_client_preview_pilot`
- `qa_fail_count = 0`

## Inputs

- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- key workbook:
  - `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i/table_first_post_human_review_sidecar_result_342i.xlsx`

Preferred `342I` sheets:

- `01_RESULT_SUMMARY`
- `03_HUMAN_REVIEWED_CELLS`
- `04_FINAL_CONFIRMED`
- `05_FINAL_CORRECTED`
- `06_FINAL_REJECTED`
- `07_PENDING_REVIEW`
- `08_BEFORE_AFTER`
- `09_SOURCE_TRACE`
- `10_METRIC_COVERAGE_AFTER`
- `11_UNIT_YEAR_AFTER`
- `12_REMAINING_RISKS`
- `13_342J_READINESS`
- `14_NO_WRITE_BACK`

## Outputs

Output dir:

- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Output files:

- `table_first_reviewed_client_preview_pilot_342j.xlsx`
- `table_first_reviewed_client_preview_pilot_342j_summary.json`
- `table_first_reviewed_client_preview_pilot_342j_manifest.json`
- `table_first_reviewed_client_preview_pilot_342j_qa.json`
- `table_first_reviewed_client_preview_pilot_342j_report.md`
- `table_first_reviewed_client_preview_pilot_342j_no_write_back_proof.json`

Workbook sheets:

1. `00_README`
2. `01_PREVIEW_SUMMARY`
3. `02_INPUT_342I_SUMMARY`
4. `03_REVIEWED_PREVIEW`
5. `04_CONFIRMED_PREVIEW`
6. `05_CORRECTED_PREVIEW`
7. `06_METRIC_YEAR_MATRIX`
8. `07_BEFORE_AFTER`
9. `08_SOURCE_TRACE`
10. `09_REMAINING_REVIEW`
11. `10_DEMO_NOTES`
12. `11_LIMITATIONS`
13. `12_342K_READINESS`
14. `13_NO_WRITE_BACK`
15. `14_NEXT_STEPS`

All sheet names must remain `<= 31` chars.

## Core Output Logic

### Input Gates

Must confirm:

- `342I output dir exists`
- `342I summary exists`
- `342I qa exists`
- `342I workbook exists`
- `342I decision = TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY`
- `342I ready_for_342j = true`
- `342I qa_fail_count = 0`
- `342I post_human_confirmed_count > 0`
- `342I reviewed_row_count > 0`

If any key gate fails:

- `decision = TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_NOT_READY`
- `ready_for_342k = false`
- do not fabricate a misleading preview

### Preview Packaging

`03_REVIEWED_PREVIEW`

- merge only:
  - `04_FINAL_CONFIRMED`
  - `05_FINAL_CORRECTED`
- exclude:
  - rejected rows
  - pending review rows
  - `NOT_A_CORE_METRIC` rows

Each row must include at least:

- `preview_row_id`
- `review_item_id`
- `final_status`
- `reviewer_decision`
- `corpus_pdf_id`
- `file_name`
- `table_id`
- `table_type`
- `source_page`
- `bbox`
- `image_path`
- `metric_raw`
- `metric_standardized`
- `year_standardized`
- `value_numeric`
- `normalized_unit`
- `final_metric_standardized`
- `final_year_standardized`
- `final_value_numeric`
- `final_normalized_unit`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`
- `source_html_snippet`
- `preview_confidence_label`
- `preview_limit_note`

`preview_confidence_label`:

- `HUMAN_CONFIRMED`
- `HUMAN_CORRECTED`

`preview_limit_note` must clearly state:

- `first_batch_review_only`
- `not_full_human_review`
- `not_client_ready`
- `not_production_ready`

`04_CONFIRMED_PREVIEW`

- only rows from `342I final confirmed`

`05_CORRECTED_PREVIEW`

- only rows from `342I final corrected`

`06_METRIC_YEAR_MATRIX`

- build matrix rows from `03_REVIEWED_PREVIEW`
- preserve:
  - `final_metric_standardized`
  - `final_year_standardized`
  - `final_value_numeric`
  - `final_normalized_unit`
  - `final_status`
  - `corpus_pdf_id`
  - `table_id`
  - `source_page`
  - `reviewer_decision`
- also summarize:
  - `metric_covered_count`
  - `metric_year_pair_count`
  - `pdf_covered_count`
  - `table_covered_count`

`07_BEFORE_AFTER`

- filter `342I 08_BEFORE_AFTER` to preview rows only

`08_SOURCE_TRACE`

- filter `342I source trace` to preview rows only
- preserve:
  - `source_page`
  - `bbox`
  - `image_path`
  - `source_html_snippet`

`09_REMAINING_REVIEW`

- preserve pending review rows
- also expose:
  - `pending_review_count = 1075`
  - `remaining_review_count = 1075`
  - `unit_year_remaining_count = 889`
  - `duplicate_remaining_count = 348`
  - `growth_row_remaining_count = 140`

`10_DEMO_NOTES`

- generate a Chinese-first, English-supported demo note sheet
- state clearly:
  - `342J` is a reviewed client preview pilot
  - only the current reviewed batch enters preview
  - rows remain traceable to source page / bbox / image / HTML snippet
  - this is not formal client delivery
  - this is not investment advice

`11_LIMITATIONS`

- state clearly:
  - only the first `80` review rows were processed
  - `1075` rows still pending review
  - `39` rows were rejected or marked not core in this batch
  - `client_ready = false`
  - `production_ready = false`
  - no full corpus human review is complete
  - preview pilot only

`12_342K_READINESS`

If:

- `342J qa_fail_count = 0`
- `reviewed_preview_row_count > 0`
- `no_write_back_proof_passed = true`

Then:

- `ready_for_342k = true`
- `recommended_342k_scope = llm_assisted_review_adjudication_or_preview_polish`

But still keep:

- `client_ready = false`
- `production_ready = false`

## Summary Fields

Must include at least:

- `input_review_template_row_count`
- `reviewed_row_count`
- `pending_review_count`
- `input_post_human_confirmed_count`
- `reviewed_preview_row_count`
- `confirmed_preview_row_count`
- `corrected_preview_row_count`
- `rejected_in_batch_count`
- `metric_covered_count`
- `metric_year_pair_count`
- `pdf_covered_count`
- `table_covered_count`
- `remaining_review_count`
- `unit_year_remaining_count`
- `duplicate_remaining_count`
- `growth_row_remaining_count`
- `source_trace_missing_count`
- `ready_for_342k`
- `recommended_342k_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision

If `ready_for_342k = true`:

- `TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY`

Otherwise:

- `TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_NOT_READY`

## QA

Must check:

- `342I input exists`
- `342I ready_for_342j = true`
- `342I qa_fail_count = 0`
- preview rows come only from confirmed / corrected rows
- rejected rows are not included in preview
- pending review rows are not included in preview
- `NOT_A_CORE_METRIC` rows are not included in preview
- source trace fields are preserved
- limitations sheet exists
- demo notes sheet exists
- `client_ready` remains false
- `production_ready` remains false
- no investment advice claim
- no upstream workbook modified
- no production pipeline / parser / extraction / delivery modified
- no output artifacts staged
- no reviewed input workbook staged
- all sheet names `<= 31`
- no-write-back proof generated

## Report

Generate:

- `table_first_reviewed_client_preview_pilot_342j_report.md`

The report must state:

- `342J` is a reviewed client preview pilot, not a formal client delivery package
- this run is based on `80` reviewed rows, with `41` confirmed / corrected preview rows
- `1075` pending review rows remain
- `client_ready = false`
- `production_ready = false`
- next step can be:
  1. expand the `342H` human review batch
  2. or move to `342K` LLM-assisted review adjudication
  3. or do preview polish while preserving pilot boundaries

## Ledger

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Record:

- `342H` second reviewed batch applied
- `342I` rerun with `80` reviewed rows
- `342J` completed
- status
- input
- output
- key metrics
- QA result
- decision
- next recommended task

If `342J ready_for_342k = true`:

- next recommended task = `342K LLM-Assisted Review Adjudication` or `342K Reviewed Preview Polish`

## Validation

```powershell
python -m py_compile datefac\benchmark\table_first_reviewed_client_preview_pilot_342j.py datefac\benchmark\table_first_reviewed_client_preview_pilot_342j_report.py tools\run_table_first_reviewed_client_preview_pilot_342j.py tests\benchmark\test_table_first_reviewed_client_preview_pilot_342j.py

python -m pytest tests\benchmark\test_table_first_reviewed_client_preview_pilot_342j.py -q

python tools\run_table_first_reviewed_client_preview_pilot_342j.py --post-human-review-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --output-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j
```
