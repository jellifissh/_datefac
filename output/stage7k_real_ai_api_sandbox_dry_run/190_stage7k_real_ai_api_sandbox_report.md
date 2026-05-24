# Stage7K Real AI API Sandbox Dry Run

- selected_review_request_count: 5
- real_api_response_count: 0
- schema_valid/invalid: 0/5
- validated/rejected: 0/5
- requires_human_approval_count: 5
- bad_eps_ratio_count: 0
- hallucinated_value_count: 0
- invalid_source_row_reference_count: 0
- provider/model: openai_compatible/glm-4.7

## Selection Notes
- Stage7I request pool has no EPS/unit_semantics_uncertain/amount_vs_ratio labels; selected representative ambiguity groups.
- selected_metrics: 毛利率, 营业收入, 归属母公司净利润, P/B, P/E
- eps_case_included: False

## Safety
- external_api_called: True
- api_key_committed: False
- api_key_logged: False
- check_delivery_state_overall_status: PASS
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False

## Decision
- ready_for_stage7l_ai_output_evaluation: True