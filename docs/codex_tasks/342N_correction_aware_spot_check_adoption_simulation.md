# 342N Correction-Aware Spot-Check Adoption Simulation

## Goal

Build a `342N` sidecar correction-aware adoption simulation on top of completed `342M`.

`342N` must:

- read real `342M` spot-check apply results and adoption candidates
- extract correction patterns from the 50 reviewed spot-check rows
- simulate direct adoption only for safe metric/unit combinations
- simulate correction-aware adoption only for explicit approved patterns
- keep unresolved rows in human-required state
- compute the post-`342N` review reduction without claiming final confirmation

`342N` remains strictly no-write-back, not client-ready, and not production-ready.

## Required Preflight

Read first:

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. `docs/codex_tasks/342M_llm_suggestion_spot_check_apply_or_real_llm_response_ingestion.md`
7. `342M` summary / QA / report / workbook
8. `342L` summary / QA / workbook
9. `342K` summary / QA / workbook
10. `342J` summary

## Confirmed Upstream State

Latest real `342M` state:

- `decision = LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY`
- `pending_review_count = 1075`
- `auto_confirm_candidate_count = 254`
- `spot_check_sample_count = 50`
- `reviewed_spot_check_count = 50`
- `spot_check_confirm_count = 17`
- `spot_check_correct_count = 33`
- `spot_check_reject_count = 0`
- `spot_check_validation_error_count = 0`
- `response_count = 0`
- `valid_llm_response_count = 0`
- `adoption_candidate_count = 254`
- `blocked_candidate_count = 0`
- `risk_adjusted_reduction_count = 254`
- `required_human_review_after_gate = 821`
- `conservative_reduction_rate_after_gate = 0.236279`
- `waiting_for_human_spot_check = false`
- `waiting_for_real_llm_responses = true`
- `ready_for_342n = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Hard Boundaries

Must not:

- rerun `342C6`, `342D`, old `342E`, `342F`, `342G`
- rerun MinerU
- call VLM
- call a real LLM API by default
- fabricate real LLM responses
- request more manual review input
- treat adoption simulation as final confirmation
- write back to `342G` / `342H` / `342I` / `342J` / `342K` / `342L` / `342M`
- modify production pipeline / parser / extraction / delivery
- claim `client_ready = true`
- claim `production_ready = true`

## Inputs

Required:

- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m`
- `D:/_datefac/output/llm_suggestion_apply_simulation_342l`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

## Outputs

Output dir:

- `D:/_datefac/output/correction_aware_adoption_simulation_342n`

Output files:

- `correction_aware_adoption_simulation_342n.xlsx`
- `correction_aware_adoption_simulation_342n_summary.json`
- `correction_aware_adoption_simulation_342n_manifest.json`
- `correction_aware_adoption_simulation_342n_qa.json`
- `correction_aware_adoption_simulation_342n_report.md`
- `correction_aware_adoption_simulation_342n_no_write_back_proof.json`

Workbook sheets, all `<= 31` chars:

1. `00_README`
2. `01_ADOPTION_SUMMARY`
3. `02_INPUT_342M_SUMMARY`
4. `03_SPOT_CHECK_PATTERNS`
5. `04_ADOPTION_INPUT`
6. `05_DIRECT_ADOPT_SIM`
7. `06_CORRECTION_ADOPT_SIM`
8. `07_STILL_HUMAN_REQUIRED`
9. `08_PATTERN_APPLICATION`
10. `09_RISK_REVIEW`
11. `10_BEFORE_AFTER_SIM`
12. `11_REDUCTION_SIM`
13. `12_342O_READINESS`
14. `13_NO_WRITE_BACK`
15. `14_NEXT_STEPS`

## Core Pattern Rules

Spot-check pattern classification:

- `CONFIRM_SUGGESTION` -> `NO_CORRECTION_REQUIRED`
- `CORRECT_SUGGESTION` + reviewer metric `revenue` + reviewer unit `亿元` -> `REVENUE_AMOUNT_NOT_YOY`
- `CORRECT_SUGGESTION` + reviewer metric `revenue_yoy` + reviewer unit `%` -> `REVENUE_YOY_PERCENT`
- `CORRECT_SUGGESTION` + reviewer metric `net_profit_yoy` + reviewer unit `%` -> `NET_PROFIT_YOY_PERCENT`
- other correction rows -> `OTHER_CORRECTION`
- anything else unresolved -> `UNRESOLVED_PATTERN`

Adoption simulation rules:

- direct adopt only for safe metric/unit pairs
- correction-aware adopt only for:
  - `revenue_yoy + 亿元 -> revenue + 亿元`
  - `revenue + % -> revenue_yoy + %`
  - `net_profit + % -> net_profit_yoy + %`
- unresolved or unsafe rows remain human-required

## Summary Fields

Must include at least:

- `pending_review_count`
- `input_adoption_candidate_count`
- `spot_check_sample_count`
- `spot_check_confirm_count`
- `spot_check_correct_count`
- `spot_check_reject_count`
- `spot_check_correction_rate`
- `direct_adopt_sim_count`
- `correction_adopt_sim_count`
- `still_human_required_count`
- `adoption_sim_total_count`
- `REVENUE_AMOUNT_NOT_YOY_count`
- `REVENUE_YOY_PERCENT_count`
- `NET_PROFIT_YOY_PERCENT_count`
- `source_trace_missing_count`
- `low_confidence_count`
- `unresolved_pattern_count`
- `risk_adjusted_reduction_count`
- `required_human_review_after_342n`
- `conservative_reduction_rate_after_342n`
- `ready_for_342o`
- `recommended_342o_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision Rules

If critical required inputs are missing:

- `decision = CORRECTION_AWARE_ADOPTION_SIMULATION_342N_NOT_READY`

If `ready_for_342o = true`:

- `decision = CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY`

Else:

- `decision = CORRECTION_AWARE_ADOPTION_SIMULATION_342N_NOT_READY`

## Report Requirements

Report must say:

- `342N` is a correction-aware adoption simulation, not final adoption
- 33 corrected rows out of 50 spot-check rows mean raw bulk adoption is unsafe
- explicit correction patterns can be simulated, but unresolved rows stay human-required
- current state remains `client_ready=false` / `production_ready=false`
- next step is `342O`

## Ledger Update

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If `ready_for_342o = true`:

- next recommended task = `342O Post-Adoption Sidecar Simulation Or Review Template Generation`

## Validation

```powershell
python -m py_compile datefac\benchmark\correction_aware_adoption_simulation_342n.py datefac\benchmark\correction_aware_adoption_simulation_342n_report.py tools\run_correction_aware_adoption_simulation_342n.py tests\benchmark\test_correction_aware_adoption_simulation_342n.py

python -m pytest tests\benchmark\test_correction_aware_adoption_simulation_342n.py -q

python tools\run_correction_aware_adoption_simulation_342n.py --spot-check-gate-342m-dir D:\_datefac\output\llm_suggestion_spot_check_gate_342m --llm-suggestion-342l-dir D:\_datefac\output\llm_suggestion_apply_simulation_342l --llm-review-342k-dir D:\_datefac\output\llm_assisted_review_adjudication_342k --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\correction_aware_adoption_simulation_342n
```
