# 348A-R2 Row Type Classification Result

## Scope

This result note records the first-pass row type classification refinement for the 348A workbook audit.

Implemented row types:

- `STRICT_FINANCIAL_TABLE_ROW`
- `MARKET_REFERENCE_ROW`
- `NARRATIVE_ASSERTION`
- `UNKNOWN_ROW`

## Intended Behavioral Change

The R2 goal is triage visibility, not artificial confidence.

Narrative and market-reference rows should remain reviewable when evidence is weak, but they should no longer be indistinguishable from strict financial-table rows in queue and delivery outputs.

## Boundary

This refinement does not:

- undo R1 evidence policy
- fix the `净资产收益率(%)` unit false positive
- define the final clean-data candidate policy
- promote pilot output to client or production readiness
