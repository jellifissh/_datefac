# Stage 7D Unified Sandbox Pipeline

## Run
- entrypoint: tools/run_stage7d_sandbox_pipeline.py
- input_pdf_count: 5
- parse_success_count: 5
- raw_extract_success_count: 5

## Output Rows
- full_structured_rows: 1407
- classified_rows: 1407
- core_metrics_candidate_rows: 131
- sandbox_06_preview_rows: 131

## Statement Type Counts
- financial_ratios: 396
- income_statement: 341
- balance_sheet: 249
- valuation_metrics: 146
- cash_flow_statement: 142
- per_share_metrics: 64
- financial_data_and_valuation: 24
- company_profile: 16
- non_financial_table: 16
- rating_explanation: 13

## EPS & Conflicts
- eps_detected_count: 12
- bad_eps_ratio_count: 0
- duplicate_key_count: 63
- value_mismatch_count: 43
- unit_conflict_count: 12
- year_conflict_count: 13

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- ready_for_stage7e_ai_runtime_design: True