# Stage5X EPS Unit Conflict Apply Report

## Scope
- Limited to EPS / 每股收益 5 reviewed rows from Stage 5W

## Basis
- stage5w summary: D:\_datefac\output\stage5w_eps_unit_conflict_review\173_stage5w_eps_unit_conflict_summary.json
- based_on_stage5w_commit: dd533f9e2e3eb6e5e3385de0701574a71a13ea10

## Apply Detail
- applied_count: 5
- updated_existing_count: 0
- inserted_new_count: 5
- skipped_count: 0
- blocker_count: 0

## Row Count
- production_06_row_count_before: 114
- production_06_row_count_after: 119

## Unit Decision
- recommended_unit: 元/股
- ratio vs 元 conflict normalized to 元/股

## Guard
- formal_rules_modified: False
- official_02b_modified: False
- production_01_unchanged: True
- production_02_unchanged: True
- production_02a_unchanged: True
- production_05_unchanged: True

## Validation
- duplicate_key_count: 0
- value_mismatch_count: 0
- unit_conflict_count: 0
- year_conflict_count: 0
- eps_unit_conflict_remaining_count: 0
- check_delivery_state_overall_status: PASS
- rollback_possible: True
- ready_for_next_stage: True