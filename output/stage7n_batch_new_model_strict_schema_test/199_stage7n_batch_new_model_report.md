# Stage7N Batch New Model Strict Schema Test

## Runtime
- model: gpt-5.4-pro
- base_url_sanitized: https://geek.tm2.xin/v1
- selected_review_request_count: 3
- request_source: stage7m_fix_slim_requests
- request_interval_seconds: 5
- timeout_seconds: 90
- max_tokens: 700
- temperature: 0

## Result
- real_api_response_count: 3
- schema_valid/invalid: 3/0
- missing_required_fields_total: []
- validated/rejected: 3/0
- requires_human_approval_count: 3
- rate_limited_count/timeout_count: 0/0
- hallucinated_value_count: 0
- invalid_source_row_reference_count: 0
- bad_eps_ratio_count: 0
- eps_case_available: False
- avg_latency_seconds/max_latency_seconds: 6.825/7.78

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- new_model_batch_test_pass: True
- failure_reason: 
- recommended_next_step: stage7o_five_case_new_model_batch_test