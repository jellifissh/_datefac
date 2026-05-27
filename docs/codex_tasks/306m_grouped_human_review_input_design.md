# 306M Grouped Human Review Input Design

## Goal
- Create grouped human review input template from 306L-Fix grouped outputs.
- Let reviewers approve/correct one metric series instead of one metric-year row.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306l_fix_grouped_review_risk_rules/306l_fix_grouped_review_table.xlsx`
- `output/eval_306l_fix_grouped_review_risk_rules/306l_fix_group_to_candidate_manifest.xlsx`
- `output/eval_306j_clean_candidate_human_review_input_design/306j_candidate_id_manifest.xlsx`

## Decisions
- `approve_series`
- `reject_series`
- `needs_more_info`
- `correct_series`

## Template Fields
- Group identity / immutable fields from 306L-Fix grouped table
- review fields:
  - `decision`
  - `reviewer_id`
  - `reviewed_at`
  - `review_comment`
  - `extra_info_request`
  - `corrected_2020` ... `corrected_2030`
  - `corrected_unit`

## Validation Policy
1. For all decisions:
   - `reviewer_id` required.
   - `reviewed_at` required and parseable.
2. `decision` must be one of:
   - approve_series / reject_series / needs_more_info / correct_series
3. `needs_more_info`:
   - `extra_info_request` required.
4. `correct_series`:
   - at least one of corrected year columns or `corrected_unit` required.
5. Forbidden fields:
   - must not include `safe_to_apply` / `approve_for_real_apply`.

## Outputs
- `output/eval_306m_grouped_human_review_input_design/`
  - `306m_summary.json`
  - `306m_report.md`
  - `306m_grouped_review_input_template.xlsx`
  - `306m_grouped_review_readme.md`
  - `306m_grouped_review_validation_policy.json`
  - `306m_sample_grouped_review_input.xlsx`
  - `306m_group_id_manifest.xlsx`
  - `306m_group_to_candidate_manifest.xlsx`
  - `306m_no_apply_proof.json`

## Assertions
- group row count equals 306L-Fix grouped row count.
- group_to_candidate mapping preserved from 306L-Fix.
- decision fields and correction fields generated.
- forbidden fields not present.
- production/official/formal rules/standardizer/release unchanged.
- `check_delivery_state.py --json` = PASS.
