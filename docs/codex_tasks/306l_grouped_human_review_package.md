# 306L Grouped Human Review Package

## Goal
- Create a grouped, risk-based human review package so reviewers do not need to inspect one row per metric-year.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306j_clean_candidate_human_review_input_design/`
- `output/eval_306i_clean_candidate_review_package/`
- `output/eval_306h_fix2_alias_recovery_growth_guard/`

## Grouping Rule
- Group by:
  - `PDF文件名`
  - `标准指标`
  - `指标名`
  - `单位`
  - `来源解析器`
  - `source_panel_id`

## Year Pivot
- Pivot `年份 -> 数值` for:
  - 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030

## Risk Flags
- `missing_year`
- `unit_unknown`
- `alias_recovered`
- `zero_candidate_rescued`
- `multi_panel_source`
- `marker_only`
- `page1_summary`

## Priority
- `review_priority` in:
  - `HIGH`
  - `MEDIUM`
  - `LOW`

## Outputs
- `output/eval_306l_grouped_human_review_package/`
  - `306l_summary.json`
  - `306l_report.md`
  - `306l_grouped_review_table.xlsx`
  - `306l_high_priority_review.xlsx`
  - `306l_medium_priority_review.xlsx`
  - `306l_low_priority_auto_accept_candidates.xlsx`
  - `306l_group_to_candidate_manifest.xlsx`
  - `306l_no_apply_proof.json`

## Mapping Requirement
- Keep candidate_id mapping so group-level review can expand back to candidate-level review.

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production / official / formal rules / standardizer / release unchanged.
