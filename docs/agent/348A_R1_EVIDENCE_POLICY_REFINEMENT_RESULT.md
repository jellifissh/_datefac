# 348A-R1 Evidence Policy Refinement Result

## Scope

This note records the R1 evidence-policy refinement for the 348A pilot.

The change scope is intentionally narrow:

- split evidence severity into `STRONG_EVIDENCE`, `WEAK_EVIDENCE`, `MISSING_EVIDENCE`, and `NOT_APPLICABLE`
- keep weak-lineage rows review-worthy
- stop collapsing workbook-lineage rows into true `missing_evidence`

## Intended Behavioral Change

Before R1:

- rows without explicit page/source reference were all counted as `missing_evidence`

After R1:

- explicit page/source reference -> `STRONG_EVIDENCE`
- source PDF + workbook row lineage without page ref -> `WEAK_EVIDENCE`
- no usable lineage -> `MISSING_EVIDENCE`
- `NOT_APPLICABLE` reserved for future row-type policy work

## Boundary

This refinement does not:

- implement row-type classification
- fix the `净资产收益率(%)` unit false positive
- change MinerU / OCR / LLM behavior
- promote any pilot output to client or production readiness
