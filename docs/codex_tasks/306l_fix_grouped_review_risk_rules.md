# 306L-Fix Grouped Review Risk Rules

## Goal
- Fix risk rules in `306L` grouped human review package.
- Ensure LOW priority never contains unsafe/noisy rows.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306l_grouped_human_review_package/`
- `output/eval_306j_clean_candidate_human_review_input_design/`
- `output/eval_306i_clean_candidate_review_package/`

## Rule Fixes
1. LOW priority must exclude rows where any year value contains Chinese text or mixed metric text (e.g. `货币资金 740`).
2. LOW priority must exclude fragmented values such as `.19%` or inconsistent percent formatting.
3. LOW priority must exclude `unit_unknown` for core metrics, except valuation metrics (`PE/PB/EV_EBITDA`) with clean numeric formatting.
4. LOW priority must exclude noisy pdfplumber rows unless:
   - clean value format
   - continuous years
   - no suspicious text
5. Detect missing year gaps in each group (e.g. `2024,2027,2028` => `missing_year=true`).
6. If `candidate_count <= 2` for core metric => priority at least `MEDIUM`.
7. If `multi_panel_source=true` => `HIGH`.
8. If `zero_candidate_rescued=true` or `alias_recovered=true` => `HIGH`.
9. If value contains Chinese chars, letters mixed with numbers, or prose fragments => `HIGH` or blocked from auto-accept.

## Outputs
- `output/eval_306l_fix_grouped_review_risk_rules/`
  - `306l_fix_summary.json`
  - `306l_fix_report.md`
  - `306l_fix_grouped_review_table.xlsx`
  - `306l_fix_high_priority_review.xlsx`
  - `306l_fix_medium_priority_review.xlsx`
  - `306l_fix_low_priority_auto_accept_candidates.xlsx`
  - `306l_fix_blocked_auto_accept_candidates.xlsx`
  - `306l_fix_group_to_candidate_manifest.xlsx`
  - `306l_fix_risk_rules.json`
  - `306l_fix_no_apply_proof.json`

## Assertions
- LOW priority rows with Chinese text in year value count = 0.
- LOW priority fragmented value count = 0.
- LOW priority obvious pdfplumber noise count = 0.
- `missing_year=true` for groups with year gaps.
- `group_to_candidate_manifest` maps back to all 372 candidates.
- production/official/formal rules/standardizer/release unchanged.
- `check_delivery_state.py --json` = PASS.
