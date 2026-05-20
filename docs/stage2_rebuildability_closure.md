# Stage 2 Rebuildability and Provenance Closure

## Stage Timeline
- Stage 2A: Designed the AI repair override layer.
- Stage 2B: Materialized `02B_ai_repair_override.xlsx`.
- Stage 2C: Verified dry-run rebuild business equivalence.
- Stage 2C-R: Defined rebuild equivalence policy and warning semantics.
- Stage 2D: Integrated `02B` into the official rebuild flow in dry-run mode.

## Final Architecture
- `06_最终核心财务指标.xlsx` is a delivery-facing derived output, not source-of-truth.
- `02B_ai_repair_override.xlsx` is a rebuildable input layer.
- Official rebuild flow:
  - `01` auto trusted baseline
  - `02` / `02A` manual review and year override
  - `02B` AI repair override
  - -> `06` final core financial metrics

## Stage 2D Validation
- `rebuilt_row_count=75`
- `current_06_row_count=75`
- `row_count_match=true`
- `key_set_match=true`
- `business_value_equivalence_pass=true`
- `metadata_warning_count=3`
- `input_duplicate_warning_count=4`
- `hard_blocker_count=0`
- `override_records_present_in_rebuilt_06=true`
- `resolved_output_duplicate_count=0`
- `true_conflict_duplicate_count=0`
- `check_delivery_state.py --json overall_status=PASS`

## Warning Semantics
- `metadata_warning_count=3` comes from `final_value_source` label divergence only.
- `input_duplicate_warning_count=4` is pre-resolution input overlap, not final output duplication.
- `hard_blocker_count=0` is the closure gate for Stage 2.

## Provenance Conclusion
- Stage 2 proves the final `06` can be rebuilt from the official input layers without losing the Stage 1 AI repair records.
- Provenance is preserved through `02B`, not by treating `06` as source-of-truth.
