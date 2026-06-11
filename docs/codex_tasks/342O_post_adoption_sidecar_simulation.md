# 342O Post-Adoption Sidecar Simulation

## Goal

Build `342O` as a bounded post-adoption sidecar simulation on top of completed `342N`.

`342O` must:

- read real `342N` direct adoption and correction-aware adoption simulation outputs
- merge them into a simulated adopted sidecar result
- preserve correction-aware before/after trace
- keep unresolved rows in human-required state
- compute post-`342O` remaining review burden and coverage
- stay strictly no-write-back, not client-ready, and not production-ready

`342O` is not final human confirmation, not a formal client export, and not production output.

## Required Preflight

Read first:

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. `docs/codex_tasks/342N_correction_aware_spot_check_adoption_simulation.md`
7. `342N` summary / QA / report / workbook
8. `342M` summary
9. `342J` summary
10. `342I` summary

## Confirmed Upstream State

Latest real `342N` state:

- `decision = CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY`
- `pending_review_count = 1075`
- `input_adoption_candidate_count = 254`
- `direct_adopt_sim_count = 110`
- `correction_adopt_sim_count = 78`
- `still_human_required_count = 66`
- `adoption_sim_total_count = 188`
- `risk_adjusted_reduction_count = 188`
- `required_human_review_after_342n = 887`
- `conservative_reduction_rate_after_342n = 0.174884`
- `ready_for_342o = true`
- `recommended_342o_scope = post_adoption_sidecar_simulation_or_review_template_generation`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `no-write-back proof passed`

## Hard Boundaries

Must not:

- rerun MinerU
- rerun `342E / 342F / 342G / 342H / 342I / 342J / 342K / 342L / 342M / 342N`
- call VLM
- call a real LLM API
- fabricate real LLM responses
- request more human review input
- treat simulated adoption as final confirmation
- write simulated adoption back to upstream workbooks
- modify production pipeline / parser / extraction / delivery
- claim `client_ready = true`
- claim `production_ready = true`
- generate a formal client export

## Inputs

Required:

- `D:/_datefac/output/correction_aware_adoption_simulation_342n`
- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`

## Outputs

Output dir:

- `D:/_datefac/output/post_adoption_sidecar_simulation_342o`

Output files:

- `post_adoption_sidecar_simulation_342o.xlsx`
- `post_adoption_sidecar_simulation_342o_summary.json`
- `post_adoption_sidecar_simulation_342o_manifest.json`
- `post_adoption_sidecar_simulation_342o_qa.json`
- `post_adoption_sidecar_simulation_342o_report.md`
- `post_adoption_sidecar_simulation_342o_no_write_back_proof.json`

Workbook sheets, all `<= 31` chars:

1. `00_README`
2. `01_SIDECAR_SUMMARY`
3. `02_INPUT_342N_SUMMARY`
4. `03_SIM_ADOPTED_CELLS`
5. `04_DIRECT_ADOPTED`
6. `05_CORRECTED_ADOPTED`
7. `06_STILL_HUMAN_REQUIRED`
8. `07_BEFORE_AFTER_TRACE`
9. `08_METRIC_COVERAGE`
10. `09_REMAINING_REVIEW`
11. `10_RISK_BOUNDARY`
12. `11_342P_READINESS`
13. `12_NO_WRITE_BACK`
14. `13_NEXT_STEPS`

## Core Logic

### `03_SIM_ADOPTED_CELLS`

Merge:

- `342N / 05_DIRECT_ADOPT_SIM`
- `342N / 06_CORRECTION_ADOPT_SIM`

Required fields:

- `sidecar_cell_id`
- `source_stage = 342N`
- `review_item_id`
- `simulation_status`
- `simulated_metric_standardized`
- `simulated_year_standardized`
- `simulated_value_numeric`
- `simulated_normalized_unit`
- `adoption_type = DIRECT / CORRECTION_AWARE`
- `correction_pattern`
- `adoption_evidence`
- `adoption_confidence`
- `not_final_confirmation = true`
- `client_ready = false`
- `production_ready = false`

Must not allow:

- `final_confirmed = true`
- `human_confirmed = true`
- `client_ready = true`
- `production_ready = true`

### `04_DIRECT_ADOPTED`

Keep direct rows only and preserve:

- `review_item_id`
- `simulated_metric_standardized`
- `simulated_year_standardized`
- `simulated_value_numeric`
- `simulated_normalized_unit`
- `adoption_confidence`
- `adoption_evidence`
- `not_final_confirmation = true`

### `05_CORRECTED_ADOPTED`

Keep correction-aware rows only and preserve:

- `review_item_id`
- `original_suggested_metric_standardized`
- `simulated_metric_standardized`
- `original_suggested_normalized_unit`
- `simulated_normalized_unit`
- `simulated_year_standardized`
- `simulated_value_numeric`
- `correction_pattern`
- `correction_reason`
- `not_final_confirmation = true`

Must preserve these mapping examples:

- `revenue_yoy + 亿元 -> revenue + 亿元`
- `revenue + % -> revenue_yoy + %`
- `net_profit + % -> net_profit_yoy + %`

### `06_STILL_HUMAN_REQUIRED`

Inherit unresolved rows and preserve:

- `review_item_id`
- `human_required_reason`
- `failed_pattern_reason`
- `recommended_human_action`
- `auto_apply_allowed = false`

### `07_BEFORE_AFTER_TRACE`

Generate correction-aware before/after trace:

- `review_item_id`
- `original_metric`
- `simulated_metric`
- `original_unit`
- `simulated_unit`
- `original_value`
- `simulated_value`
- `original_year`
- `simulated_year`
- `correction_pattern`
- `correction_reason`
- `sidecar_note`

### `08_METRIC_COVERAGE`

Aggregate simulated adopted cells by metric:

- `metric_standardized`
- `adopted_cell_count`
- `unique_year_count`
- `years_covered`
- `direct_count`
- `correction_count`
- `unit_set`
- `min_value`
- `max_value`

Also compute:

- `metric_covered_count`
- `metric_year_pair_count`
- `direct_metric_year_pair_count`
- `correction_metric_year_pair_count`

### `09_REMAINING_REVIEW`

Compute:

- `original_pending_review_count = 1075`
- `input_adoption_candidate_count = 254`
- `simulated_adopted_cell_count = direct_adopted_count + corrected_adopted_count`
- `still_human_required_count`
- `remaining_review_count = original_pending_review_count - simulated_adopted_cell_count`
- `reduction_rate_after_342o = simulated_adopted_cell_count / original_pending_review_count`

Real expected current values:

- `simulated_adopted_cell_count = 188`
- `remaining_review_count = 887`
- `reduction_rate_after_342o = 0.174884`

### `10_RISK_BOUNDARY`

Must state:

- sidecar result is simulation only
- not final confirmed
- not full human review completion
- not real LLM response ingestion
- not client-ready
- not production-ready
- `66` adoption candidates still need human handling
- `887` broader review rows remain after simulation
- high correction rate means direct client export is unsafe

### `11_342P_READINESS`

If:

- `qa_fail_count = 0`
- `simulated_adopted_cell_count > 0`
- `still_human_required_count >= 0`
- `no_write_back_proof_passed = true`
- `client_ready = false`
- `production_ready = false`

Then:

- `ready_for_342p = true`
- `recommended_342p_scope = reviewed_plus_simulated_client_preview_pilot`

Else:

- `ready_for_342p = false`

## Summary Fields

Must include at least:

- `pending_review_count`
- `input_adoption_candidate_count`
- `direct_adopted_count`
- `corrected_adopted_count`
- `simulated_adopted_cell_count`
- `still_human_required_count`
- `remaining_review_count`
- `reduction_rate_after_342o`
- `metric_covered_count`
- `metric_year_pair_count`
- `correction_pattern_count`
- `REVENUE_AMOUNT_NOT_YOY_count`
- `REVENUE_YOY_PERCENT_count`
- `NET_PROFIT_YOY_PERCENT_count`
- `ready_for_342p`
- `recommended_342p_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision Rules

If critical inputs are missing or not ready:

- `decision = POST_ADOPTION_SIDECAR_SIMULATION_342O_NOT_READY`

If `ready_for_342p = true`:

- `decision = POST_ADOPTION_SIDECAR_SIMULATION_342O_READY`

Else:

- `decision = POST_ADOPTION_SIDECAR_SIMULATION_342O_NOT_READY`

## Report Requirements

Report must say:

- `342O` is a post-adoption sidecar simulation, not final adoption
- `342N` contributes `188` simulated adopted rows
- `110` are direct adoption rows
- `78` are correction-aware adoption rows
- `66` remain human-required inside the adoption candidate subset
- current broader remaining review count is `887`
- `client_ready=false` and `production_ready=false`
- next step is `342P reviewed + simulated client preview pilot`
- do not use this result as formal client delivery or investment advice

## Ledger Update

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If `ready_for_342p = true`:

- next recommended task = `342P Reviewed Plus Simulated Client Preview Pilot`

Must keep explicit:

- `342O` is not final human review completion
- `342O` is not real LLM review completion
- `342O` is not client-ready
- `342O` is not production-ready
- sidecar result is simulation only

## Validation

```powershell
python -m py_compile datefac\benchmark\post_adoption_sidecar_simulation_342o.py datefac\benchmark\post_adoption_sidecar_simulation_342o_report.py tools\run_post_adoption_sidecar_simulation_342o.py tests\benchmark\test_post_adoption_sidecar_simulation_342o.py

python -m pytest tests\benchmark\test_post_adoption_sidecar_simulation_342o.py -q

python tools\run_post_adoption_sidecar_simulation_342o.py --adoption-simulation-342n-dir D:\_datefac\output\correction_aware_adoption_simulation_342n --spot-check-gate-342m-dir D:\_datefac\output\llm_suggestion_spot_check_gate_342m --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-sidecar-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --output-dir D:\_datefac\output\post_adoption_sidecar_simulation_342o
```
