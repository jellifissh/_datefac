# 306H-Fix2 Alias Recovery Growth Guard

## Goal
- Fix `306H-Fix` alias recovery bug.
- Rebuild `clean_core_candidates_v3` from `306G-Fix` baseline plus only safe alias recovery rows.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306g_fix_core_semantic_quality_gate/`
- `output/eval_306h_fix_core_metric_alias_recovery/`

## Rebuild Rules
1. Base = `306G-Fix clean core baseline`.
2. Add only safe alias rows.

## Hard Blocks
- If alias target is absolute core metric:
  - `revenue`, `net_profit`, `attributable_net_profit`, `operating_cash_flow`, `total_assets`, `total_liabilities`
  - and metric text contains any of:
    - `增长`, `增长率`, `同比`, `yoy`, `YoY`
  - then hard block.
- Hard block any row from `suspicious_structured` with `suspicious_reasons` containing `core_semantic_false_positive`.
- Hard block dirty flags / suspicious year / merged value / sentence metric / prose value / conflict key.

## Valid Alias Examples
- `营业总收入 / 主营业务收入 -> revenue`
- `市盈率(PE) / P/E -> pe`
- `市净率(PB) / P/B -> pb`
- `EV/EBITDA -> ev_ebitda`

## Outputs
- `output/eval_306h_fix2_alias_recovery_growth_guard/`
  - `306h_fix2_summary.json`
  - `306h_fix2_report.md`
  - `306h_fix2_clean_core_candidates_v3.xlsx`
  - `306h_fix2_valid_recovered_alias_candidates.xlsx`
  - `306h_fix2_blocked_alias_candidates.xlsx`
  - `306h_fix2_unresolved_missing_core_metric_audit.xlsx`
  - `306h_fix2_alias_recovery_rules.json`
  - `306h_fix2_no_apply_proof.json`

## Required Assertions
- `clean_core_candidates_v3` has 0 rows where `raw_metric_name` contains `增长` or `增长率`.
- `clean_core_candidates_v3` has 0 rows where source is `suspicious_structured` and reason has `core_semantic_false_positive`.
- duplicate `(pdf, metric, year)` keys = 0.
- value conflicts = 0.

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production / official / formal rules / standardizer / release unchanged.
