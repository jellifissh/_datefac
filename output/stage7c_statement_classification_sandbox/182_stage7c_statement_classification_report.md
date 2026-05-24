# Stage 7C Statement Type Classification Sandbox

## Goal
- Focus on statement type refinement and usability layering for Stage 7B full_structured_table.
- Keep all rows; do not drop mapping-miss rows.

## Input
- input_full_structured_rows: 1407
- based_on_stage7b_commit: e041234ae15d618b8b235000f14fe3adda85ca44

## Unknown Reclassification
- unknown_financial_before_count: 36
- unknown_financial_after_count: 0
- reclassified_unknown_count: 36

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

## Usability Layer Counts
- full_structured_only: 1231
- candidate_for_core_metrics: 131
- non_financial_excluded: 45

## EPS Check
- eps_detected_count: 12
- bad_eps_ratio_count: 0

## Safety
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False
- check_delivery_state_overall_status: PASS

## Decision
- ready_for_stage7d_pipeline_entrypoint: True