# 306G-Fix Core Semantic Quality Gate

## Goal
- Fix semantic false positives in `306G` clean core candidates.
- Keep sandbox-only audit/export behavior.

## Input
- `output/eval_306g_fusion_quality_gate_and_clean_candidate_export/`

## Hard Constraints
- Do not rerun Marker.
- Do not rerun pdfplumber.
- Do not call API/LLM/OCR.
- Do not modify production.

## Fix Rules
1. Growth semantic guard:
   - If `raw_metric_name` contains `增长率 / 增长 / yoy / YoY` and metric is absolute core metric
     (`revenue / net_profit / attributable_net_profit`), do not keep as clean core candidate.
2. Sentence-like metric guard:
   - Block clean core rows with sentence-like `raw_metric_name`.
3. Year range guard:
   - Block clean core rows where `year < 2020` or `year > 2032`.
4. Value semantic guard:
   - Block clean core rows where `value_raw` looks like ID/code/prose rather than financial value.

## Outputs
- `output/eval_306g_fix_core_semantic_quality_gate/`
  - `306g_fix_summary.json`
  - `306g_fix_report.md`
  - `306g_fix_clean_core_candidates.xlsx`
  - `306g_fix_removed_core_false_positives.xlsx`
  - `306g_fix_clean_structured_rows.xlsx`
  - `306g_fix_suspicious_structured_rows.xlsx`
  - `306g_fix_quality_gate_rules.json`
  - `306g_fix_no_apply_proof.json`

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm unchanged production / official / formal rules / standardizer / release.
