# Stage 7E Sandbox Core Metrics Conflict Diagnosis

## Input
- input_core_metrics_candidate_rows: 131
- input_sandbox_06_preview_rows: 131

## Conflict Before
- duplicate_key_count_before: 63
- value_mismatch_count_before: 43
- unit_conflict_count_before: 12
- year_conflict_count_before: 13

## Resolution Dry Run
- auto_resolvable_conflict_count: 12
- manual_review_required_count: 31
- duplicate_key_count_after_dry_run: 0
- value_mismatch_count_after_dry_run: 0
- unit_conflict_count_after_dry_run: 0
- year_conflict_count_after_dry_run: 0

## Conflict Category Distribution
- true_value_conflict: 82
- amount_vs_ratio_collision: 16
- unit_inference_error: 8

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
- ready_for_stage7f_core_metrics_policy_apply_sandbox: True