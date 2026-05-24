# Stage 7G Manual Review Reduction Analysis

## Scope
- Sandbox analysis only. No real apply.
- No production/official/rules/release changes.

## Inputs
- based_on_stage7f_commit: e11e0eb45c1f496ee293508215d5330829df3fe1
- input_manual_review_queue_rows: 82
- clean_06_preview_rows_before: 37

## Reduction Result
- auto_resolvable_candidate_rows: 25
- remaining_manual_review_rows: 57
- manual_review_reduction_count: 25
- manual_review_reduction_rate: 0.304878
- reduced_clean_06_preview_rows: 62

## Conflict After Preview
- duplicate_key_count_after_preview: 0
- value_mismatch_count_after_preview: 0
- unit_conflict_count_after_preview: 0
- year_conflict_count_after_preview: 0

## Manual Review Reason Distribution
- year_semantics_uncertain: 82

## EPS Check
- eps_detected_count: 5
- bad_eps_ratio_count: 0

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- ready_for_stage7h_ai_assisted_review_design: True