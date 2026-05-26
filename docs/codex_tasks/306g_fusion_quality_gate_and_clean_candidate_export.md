# 306G Fusion Quality Gate And Clean Candidate Export

## Goal
- Add a sandbox-only quality gate on top of `306E` fusion outputs using `306F` audit evidence.
- Export:
  - clean structured rows
  - clean core metric candidates
  - suspicious rows
  - blocked rows

## Scope
- Input only:
  - `output/eval_306e_parser_fusion_pipeline_design/`
  - `output/eval_306f_fusion_result_quality_validation/`
- No rerun of Marker/pdfplumber.
- No API/LLM/OCR.
- No production write or apply action.

## Quality Gate Principles
1. Keep `306F` PASS-like core candidates as the clean baseline.
2. Quarantine rows with suspicious metric/value text patterns.
3. Block rows with hard-risk signals:
   - dirty confidence flags
   - cross-source conflict keys
   - sentence-like/report/disclaimer/rating/index metric names
   - prose-like value text
   - value cells containing multiple unrelated numbers

## Required Outputs
Directory:
- `output/eval_306g_fusion_quality_gate_and_clean_candidate_export/`

Artifacts:
- `306g_summary.json`
- `306g_report.md`
- `306g_clean_core_candidates.xlsx`
- `306g_clean_structured_rows.xlsx`
- `306g_suspicious_structured_rows.xlsx`
- `306g_blocked_structured_rows.xlsx`
- `306g_quality_gate_rules.json`
- `306g_manual_review_samples.xlsx`
- `306g_no_apply_proof.json`

## Validation
- Run `python tools/check_delivery_state.py --json` and keep `PASS`.
- Confirm production/official/formal rules/standardizer/release package unchanged.
