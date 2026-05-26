# 306I Clean Candidate Review Package

## Goal
- Generate a human-readable review package for `306H-Fix2 clean core candidates v3`.

## Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API / LLM / OCR.
- Do not modify production.

## Inputs
- `output/eval_306h_fix2_alias_recovery_growth_guard/`
- `output/eval_306h_clean_candidate_regression/`
- `output/eval_306g_fix_core_semantic_quality_gate/`

## Source Rule
- Use `clean_core_candidates_v3` as the only clean core candidate source.

## Outputs
- `output/eval_306i_clean_candidate_review_package/`
  - `306i_summary.json`
  - `306i_report.md`
  - `306i_per_pdf_candidate_summary.xlsx`
  - `306i_clean_core_candidates_review.xlsx`
  - `306i_missing_metric_review.xlsx`
  - `306i_rescued_zero_candidate_review.xlsx`
  - `306i_manual_spot_check_package.xlsx`
  - `306i_no_apply_proof.json`

## Readable Columns
- `PDF文件名`, `页码`, `指标名`, `标准指标`, `年份`, `数值`, `单位`,
  `来源解析器`, `来源原因`, `是否别名恢复`, `是否zero-candidate救回`

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production / official / formal rules / standardizer / release unchanged.
