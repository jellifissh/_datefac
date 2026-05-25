# Stage7M2 Slim Three-case GLM Strict Schema Dry Run

## Runtime
- selected_review_request_count: 3
- executed_request_count: 3
- timeout_seconds: 120
- max_tokens: 700
- temperature: 0
- inter_request_interval_seconds: 15
- stop_reason: timeout

## Result
- real_api_response_count: 2
- schema_valid/invalid: 2/1
- validated/rejected: 2/1
- requires_human_approval_count: 2
- rate_limited_count/timeout_count: 0/1
- hallucinated_value_count: 0
- invalid_source_row_reference_count: 0
- bad_eps_ratio_count: 0

## Coverage Facts
- eps_case_available: False
- request_pool_missing_categories: ['unit_semantics_uncertain', 'amount_vs_ratio_collision']

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- ready_for_stage7n_ai_assisted_review_batch_policy: False