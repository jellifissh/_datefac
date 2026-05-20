# Stage 2D Official Rebuild Flow (Dry-Run Integration)

## Scope
- Integrate `02B_ai_repair_override.xlsx` into official `06` rebuild logic as dry-run only.
- No production replacement in Stage 2D.

## Upstream Inputs
- Baseline: `output/delivery_package/01_自动可信核心指标.xlsx`
- Manual layers: `output/delivery_package/02_人工复核指标队列.xlsx`, `output/delivery_package/02A_人工年份修正覆盖表.xlsx`
- AI override layer: `data/overrides/02B_ai_repair_override.xlsx`
- Current output reference: `output/delivery_package/06_最终核心财务指标.xlsx`

## Priority Rule
- `manual correction > AI repair override > auto trusted baseline`

## Conflict & Warning Semantics
- Manual vs override same key with different value/unit: `true_conflict_duplicate` (blocker).
- Source-label-only difference with same value/unit: metadata warning.
- Input-level duplicate before priority resolution: warning.
- Resolved output duplicate or true conflict duplicate: blocker.

## Implementation
- Script: `tools/rebuild_final_core_metrics_with_overrides.py`
- Outputs:
  - `output/stage2d_official_rebuild_dry_run/06_最终核心财务指标.official_rebuilt_with_02B.xlsx`
  - `output/stage2d_official_rebuild_dry_run/83_stage2d_official_rebuild_diff.xlsx`
  - `output/stage2d_official_rebuild_dry_run/83_stage2d_official_rebuild_diff.md`
  - `output/stage2d_official_rebuild_dry_run/84_stage2d_official_rebuild_summary.json`

## Pass Rule
- Business equivalence pass requires:
  - `value_mismatch_count=0`
  - `unit_mismatch_count=0`
  - `missing_in_rebuilt_count=0`
  - `extra_in_rebuilt_count=0`
  - `resolved_output_duplicate_count=0`
  - `true_conflict_duplicate_count=0`
  - `override_records_present_in_rebuilt_06=true`
- Dry-run pass additionally requires:
  - production file hashes unchanged
  - delivery check PASS
