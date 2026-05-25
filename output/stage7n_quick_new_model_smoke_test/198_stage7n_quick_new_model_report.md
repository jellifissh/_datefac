# Stage7N Quick New Model Smoke Test

## Runtime
- model: gpt-5.4-pro
- base_url_sanitized: https://geek.tm2.xin/v1
- socket_host/socket_ok: geek.tm2.xin/True
- selected_review_request_count: 1
- external_api_called: True

## Result
- http_status: 200
- rate_limited/timeout: False/False
- real_api_response_count: 1
- schema_valid/invalid: 1/0
- missing_required_fields: []
- validated/rejected: 1/0
- hallucinated_value_count: 0
- invalid_source_row_reference_count: 0
- bad_eps_ratio_count: 0
- requires_human_approval_count: 1
- latency_seconds: 7.213

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- new_model_smoke_test_pass: True
- recommended_next_step: proceed_to_stage7n_batch_policy_with_guardrails