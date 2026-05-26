# 306H-Fix Core Metric Alias Recovery

## Goal
- Audit and fix false missing core metrics caused by incomplete alias normalization in `306H`.
- Recover safe alias rows into clean core candidates v2.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306g_fix_core_semantic_quality_gate/`
- `output/eval_306h_clean_candidate_regression/`

## Alias Recovery Rules
- `营业总收入 / 主营业务收入 -> revenue`
- `归属母公司净利润 / 归母净利润 / 归属于母公司股东的净利润 -> attributable_net_profit`
- `经营活动产生的现金流量净额 / 经营活动现金流净额 -> operating_cash_flow`
- `市盈率(PE) / P/E -> pe`
- `市净率(PB) / P/B -> pb`
- `企业价值倍数 / EV/EBITDA -> ev_ebitda`

## Safety Guard
- Do not recover rows with:
  - dirty flags
  - suspicious year
  - merged value
  - sentence-like metric name
  - prose-like value
  - conflict key (same pdf/metric/year)

## Outputs
- `output/eval_306h_fix_core_metric_alias_recovery/`
  - `306h_fix_summary.json`
  - `306h_fix_report.md`
  - `306h_fix_clean_core_candidates_v2.xlsx`
  - `306h_fix_recovered_alias_candidates.xlsx`
  - `306h_fix_unresolved_missing_core_metric_audit.xlsx`
  - `306h_fix_alias_recovery_rules.json`
  - `306h_fix_no_apply_proof.json`

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production / official / formal rules / standardizer / release unchanged.
