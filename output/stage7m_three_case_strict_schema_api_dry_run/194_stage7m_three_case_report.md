# Stage7M Three-case Strict Schema GLM API Dry Run

## Setup
- selected_review_request_count: 3
- executed_request_count: 1
- provider/model: openai_compatible/GLM-4.7
- timeout_seconds: 90
- max_tokens: 1000
- temperature: 0
- inter_request_sleep_seconds: 10

## Result
- real_api_response_count: 0
- schema_valid/invalid: 0/1
- validated/rejected: 0/1
- requires_human_approval_count: 0
- rate_limited_count/timeout_count: 0/1
- hallucinated_value_count: 0
- invalid_source_row_reference_count: 0
- bad_eps_ratio_count: 0

## Selection Constraints
- requested_reason_constraints_fully_met: False
- requested_reason_available_counts: {'true_value_conflict': 0, 'unit_semantics_uncertain': 0, 'amount_vs_ratio_collision': 0}
- eps_case_available_count: 0
- eps_case_included: False
- selection_note: No true_value_conflict/unit_semantics_uncertain/amount_vs_ratio_collision in Stage7I pool; selected 3 representative ambiguity groups.

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- ready_for_stage7n_ai_assisted_review_batch_policy: False