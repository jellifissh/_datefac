# Stage 2C Rebuild Equivalence Policy

## Positioning
- `06_最终核心财务指标.xlsx` is a delivery-facing derived output, not the source of truth.
- `02B_ai_repair_override.xlsx` is a rebuildable input layer for Stage 1 real-applied AI repair records.
- Stage 2C-R proved that `01 + 02/02A + 02B` can reconstruct the current `06` at business-equivalence level.

## Hard Equivalence Criteria
The rebuild is considered business-equivalent only when all of the following are true:
- `value_mismatch_count = 0`
- `unit_mismatch_count = 0`
- `missing_in_rebuilt_count = 0`
- `extra_in_rebuilt_count = 0`
- `resolved_output_duplicate_count = 0`
- `true_conflict_duplicate_count = 0`
- `override_records_present_in_rebuilt_06 = true`

## Metadata vs Business Semantics
- `SOURCE_ONLY_MISMATCH` is a metadata warning when `value` and `unit` are identical and only `final_value_source` differs.
- `manual_corrected` vs `manual_added` is a source-label semantic divergence.
- This divergence does not block business-equivalence pass.

## Duplicate Semantics
- `input_duplicate_before_priority_resolution` is a warning.
- `resolved_output_duplicate` is a blocker.
- `true_conflict_duplicate` is a blocker.

## Pass Semantics
- `stage2c_rebuild_business_equivalence_pass` means business values are equivalent.
- `stage2c_reconciliation_pass` additionally requires production files unchanged and delivery check PASS.

## Operational Note
- Future metadata normalization may align `manual_corrected` and `manual_added`, but no production mutation is required for Stage 2C closure.
