# Stage7O Five-case New Model Strict Schema Batch Test

## Runtime
- model: gpt-5.4-pro
- selected_review_request_count: 5
- request_interval_seconds: 5
- timeout_seconds: 90
- max_tokens: 700
- temperature: 0

## Result
- real_api_response_count: 4
- schema_valid/invalid: 3/2
- missing_required_fields_total: []
- validated/rejected: 3/2
- requires_human_approval_count: 4
- rate_limited_count/timeout_count: 0/0
- hallucinated_value_count: 0
- invalid_source_row_reference_count: 0
- bad_eps_ratio_count: 0
- eps_case_available: False
- avg_latency_seconds/max_latency_seconds: 6.103/8.814

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- new_model_five_case_test_pass: False
- failure_reason: schema_invalid
- recommended_next_step: fix_schema_invalid_and_retry_stage7o