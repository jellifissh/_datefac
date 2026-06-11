# 342P Reviewed Plus Simulated Client Preview Pilot

## Goal

Build `342P` as a reviewed plus simulated client preview pilot on top of completed `342J` and completed `342O`.

`342P` must:

- read real `342J` human-reviewed preview rows
- read real `342O` simulated adopted cells and still-human-required rows
- read `342I` / `342N` metadata and boundary summaries
- merge reviewed and simulated rows into one bounded internal preview workbook
- log collisions instead of hiding them
- keep human-reviewed rows higher priority than simulated rows
- remain strictly no-write-back, not client-ready, and not production-ready

`342P` is not full human-review completion, not real LLM-review completion, not formal client export, and not investment advice.

## Required Preflight

Read first:

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. `docs/codex_tasks/342O_post_adoption_sidecar_simulation.md`
7. `docs/codex_tasks/342J_table_first_reviewed_client_preview_pilot.md`
8. `342O` summary / QA / report / workbook
9. `342J` summary / QA / workbook
10. `342I` summary / QA / workbook
11. `342N` summary / QA / workbook

## Confirmed Upstream State

Latest real `342O` state:

- `decision = POST_ADOPTION_SIDECAR_SIMULATION_342O_READY`
- `pending_review_count = 1075`
- `input_adoption_candidate_count = 254`
- `direct_adopted_count = 110`
- `corrected_adopted_count = 78`
- `simulated_adopted_cell_count = 188`
- `still_human_required_count = 66`
- `remaining_review_count = 887`
- `reduction_rate_after_342o = 0.174884`
- `metric_covered_count = 17`
- `metric_year_pair_count = 50`
- `ready_for_342p = true`
- `recommended_342p_scope = reviewed_plus_simulated_client_preview_pilot`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

Latest real `342J` state:

- `decision = TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY`
- `reviewed_preview_row_count = 41`
- `confirmed_preview_row_count = 31`
- `corrected_preview_row_count = 10`
- `pending_review_count = 1075`
- `metric_covered_count = 5`
- `metric_year_pair_count = 25`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Hard Boundaries

Must not:

- rerun MinerU
- rerun `342E / 342F / 342G / 342H / 342I / 342J / 342K / 342L / 342M / 342N / 342O`
- call VLM
- call a real LLM API
- fabricate real LLM responses
- request more human review input
- treat simulated adoption as final confirmation
- treat reviewed + simulated preview as formal client export
- write `342P` output back to any upstream workbook
- modify production pipeline / parser / extraction / delivery
- claim `client_ready = true`
- claim `production_ready = true`
- claim full human review completion

## Inputs

Required dirs:

- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/correction_aware_adoption_simulation_342n`

## Outputs

Output dir:

- `D:/_datefac/output/reviewed_plus_simulated_client_preview_342p`

Output files:

- `reviewed_plus_simulated_client_preview_342p.xlsx`
- `reviewed_plus_simulated_client_preview_342p_summary.json`
- `reviewed_plus_simulated_client_preview_342p_manifest.json`
- `reviewed_plus_simulated_client_preview_342p_qa.json`
- `reviewed_plus_simulated_client_preview_342p_report.md`
- `reviewed_plus_simulated_client_preview_342p_no_write_back_proof.json`

Workbook sheets, all `<= 31` chars:

1. `00_README`
2. `01_PREVIEW_SUMMARY`
3. `02_INPUT_342O_SUMMARY`
4. `03_INPUT_342J_SUMMARY`
5. `04_COMBINED_PREVIEW`
6. `05_HUMAN_REVIEWED`
7. `06_SIM_DIRECT`
8. `07_SIM_CORRECTED`
9. `08_STILL_HUMAN_REQUIRED`
10. `09_COLLISION_CHECK`
11. `10_METRIC_COVERAGE`
12. `11_PREVIEW_BOUNDARY`
13. `12_342Q_READINESS`
14. `13_NO_WRITE_BACK`
15. `14_NEXT_STEPS`

## Core Logic

### `05_HUMAN_REVIEWED`

Read `342J` reviewed preview rows and standardize at least:

- `preview_row_id`
- `review_item_id`
- `source_stage = 342J`
- `preview_source_type = HUMAN_REVIEWED`
- `data_trust_level = HUMAN_REVIEWED`
- `reviewer_decision`
- `metric_standardized = final_metric_standardized`
- `year_standardized = final_year_standardized`
- `value_numeric = final_value_numeric`
- `normalized_unit = final_normalized_unit`
- `source_page`
- `bbox`
- `image_path`
- `evidence = source_html_snippet`
- `not_final_confirmation = false`
- `client_ready = false`
- `production_ready = false`

### `06_SIM_DIRECT`

Read `342O / 04_DIRECT_ADOPTED`, then enrich with `342O / 03_SIM_ADOPTED_CELLS` plus `342N` metadata.

Required fields:

- `preview_row_id`
- `review_item_id`
- `source_stage = 342O`
- `preview_source_type = SIMULATED_DIRECT`
- `data_trust_level = SIMULATED_DIRECT_ADOPTED`
- `metric_standardized = simulated_metric_standardized`
- `year_standardized = simulated_year_standardized`
- `value_numeric = simulated_value_numeric`
- `normalized_unit = simulated_normalized_unit`
- `source_page`
- `bbox`
- `image_path`
- `evidence = source_html_snippet`
- `adoption_confidence`
- `adoption_evidence`
- `not_final_confirmation = true`
- `client_ready = false`
- `production_ready = false`

### `07_SIM_CORRECTED`

Read `342O / 05_CORRECTED_ADOPTED`, then enrich with `342O / 03_SIM_ADOPTED_CELLS` plus `342N` before/after metadata.

Required fields:

- `preview_row_id`
- `review_item_id`
- `source_stage = 342O`
- `preview_source_type = SIMULATED_CORRECTED`
- `data_trust_level = SIMULATED_CORRECTION_ADOPTED`
- `metric_standardized = simulated_metric_standardized`
- `year_standardized = simulated_year_standardized`
- `value_numeric = simulated_value_numeric`
- `normalized_unit = simulated_normalized_unit`
- `source_page`
- `bbox`
- `image_path`
- `evidence = source_html_snippet`
- `correction_pattern`
- `correction_reason`
- `not_final_confirmation = true`
- `client_ready = false`
- `production_ready = false`

Correction trace must remain visible for:

- `revenue_yoy + 亿元 -> revenue + 亿元`
- `revenue + % -> revenue_yoy + %`
- `net_profit + % -> net_profit_yoy + %`

### `04_COMBINED_PREVIEW`

Merge:

- HUMAN_REVIEWED rows
- SIMULATED_DIRECT rows
- SIMULATED_CORRECTED rows

Trust priority:

1. `HUMAN_REVIEWED`
2. `SIMULATED_CORRECTION_ADOPTED`
3. `SIMULATED_DIRECT_ADOPTED`

Collision rules:

- if duplicate `review_item_id` exists, keep the higher-trust row
- if duplicate `metric + year + value + unit + source_page + bbox` exists, keep the higher-trust row
- log dropped rows in `09_COLLISION_CHECK`
- do not allow any simulated row to become final confirmed
- keep `client_ready = false`
- keep `production_ready = false`

Required combined fields:

- `preview_source_type`
- `data_trust_level`
- `review_status_for_client_display`
- `display_warning`

Display rules:

- HUMAN_REVIEWED -> `REVIEWED`
- SIMULATED_DIRECT -> `SIMULATED`
- SIMULATED_CORRECTED -> `SIMULATED_CORRECTED`

### `08_STILL_HUMAN_REQUIRED`

Carry `342O / 06_STILL_HUMAN_REQUIRED` forward and keep:

- `review_item_id`
- `human_required_reason`
- `failed_pattern_reason`
- `recommended_human_action`
- `auto_apply_allowed = false`
- `included_in_preview = false`

### `09_COLLISION_CHECK`

Must output collision log rows and summary counts:

- `duplicate_review_item_id_count`
- `duplicate_metric_year_source_count`
- `human_over_simulation_override_count`
- `simulated_duplicate_dropped_count`
- `collision_logged_count`

### `10_METRIC_COVERAGE`

Aggregate final combined preview by metric:

- `metric_standardized`
- `preview_row_count`
- `unique_year_count`
- `years_covered`
- `human_reviewed_count`
- `simulated_direct_count`
- `simulated_corrected_count`
- `unit_set`
- `min_value`
- `max_value`

Also summarize:

- `combined_preview_row_count`
- `human_reviewed_preview_count`
- `simulated_preview_count`
- `simulated_direct_preview_count`
- `simulated_corrected_preview_count`
- `metric_covered_count`
- `metric_year_pair_count`
- `human_metric_year_pair_count`
- `simulated_metric_year_pair_count`

### `11_PREVIEW_BOUNDARY`

Must state clearly:

- `342P` is a reviewed + simulated preview pilot
- not formal client export
- not production-ready
- not investment advice
- simulated rows require later audit
- still-human-required rows remain outside preview
- `client_ready = false`
- `production_ready = false`

### `12_342Q_READINESS`

If:

- `qa_fail_count = 0`
- `combined_preview_row_count > 0`
- `human_reviewed_preview_count > 0`
- `simulated_preview_count > 0`
- `no_write_back_proof_passed = true`
- `client_ready = false`
- `production_ready = false`

Then:

- `ready_for_342q = true`
- `recommended_342q_scope = preview_audit_and_export_readiness_gate`

Else:

- `ready_for_342q = false`

## Summary Fields

Must include at least:

- `human_reviewed_preview_count`
- `simulated_preview_count`
- `simulated_direct_preview_count`
- `simulated_corrected_preview_count`
- `combined_preview_row_count`
- `still_human_required_count`
- `remaining_review_count`
- `metric_covered_count`
- `metric_year_pair_count`
- `human_metric_year_pair_count`
- `simulated_metric_year_pair_count`
- `duplicate_review_item_id_count`
- `duplicate_metric_year_source_count`
- `human_over_simulation_override_count`
- `simulated_duplicate_dropped_count`
- `collision_logged_count`
- `ready_for_342q`
- `recommended_342q_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision Rules

If critical inputs are missing or not ready:

- `decision = REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_NOT_READY`

If `ready_for_342q = true`:

- `decision = REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY`

Else:

- `decision = REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_NOT_READY`

## Report Requirements

Report must say:

- `342P` is a reviewed + simulated client preview pilot
- it merges `342J` human-reviewed rows with `342O` simulated adopted cells
- HUMAN_REVIEWED and SIMULATED rows remain explicitly separated
- simulated rows are not final confirmation
- remaining review backlog still exists
- current `client_ready=false` / `production_ready=false`
- next step is `342Q preview audit and export-readiness gate`
- do not use this result as formal client delivery or investment advice

## Ledger Update

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If `ready_for_342q = true`:

- next recommended task = `342Q Preview Audit And Export Readiness Gate`

Must keep explicit:

- `342P` is not final human review completion
- `342P` is not real LLM review completion
- `342P` is not client-ready
- `342P` is not production-ready
- `342P` is reviewed + simulated preview pilot only

## Validation

```powershell
python -m py_compile datefac\benchmark\reviewed_plus_simulated_client_preview_342p.py datefac\benchmark\reviewed_plus_simulated_client_preview_342p_report.py tools\run_reviewed_plus_simulated_client_preview_342p.py tests\benchmark\test_reviewed_plus_simulated_client_preview_342p.py

python -m pytest tests\benchmark\test_reviewed_plus_simulated_client_preview_342p.py -q

python tools\run_reviewed_plus_simulated_client_preview_342p.py --post-adoption-sidecar-342o-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-sidecar-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --adoption-simulation-342n-dir D:\_datefac\output\correction_aware_adoption_simulation_342n --output-dir D:\_datefac\output\reviewed_plus_simulated_client_preview_342p
```
