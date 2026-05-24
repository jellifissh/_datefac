# Stage 7F Policy Apply Sandbox

## Input
- input_core_metrics_candidate_rows: 131
- policy_source: 184_stage7e_resolution_policy_draft.json

## Output
- clean_sandbox_06_preview_rows: 37
- manual_review_queue_rows: 82
- excluded_conflict_rows: 94

## Conflict After
- duplicate_key_count_after: 0
- value_mismatch_count_after: 0
- unit_conflict_count_after: 0
- year_conflict_count_after: 0

## EPS
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
- ready_for_stage7g_ai_runtime_design_or_client_package: True