# 348A-QA Excel Intake Audit Result Review

## Task ID

`348A-QA Excel Intake Audit Result Review`

## Input Output Directory Reviewed

`D:\_datefac_agent\output\agent_excel_intake_audit_348a`

Reviewed files:

- `agent_excel_intake_audit_348a_manifest.json`
- `agent_excel_intake_audit_348a_run_summary.json`
- `audit_report.md`
- `evidence_index.json`
- `review_queue.csv`
- `clean_data.csv`

## Manifest Decision

Primary QA decision:

`348A_QA_CONFIRMED_NEEDS_EVIDENCE_POLICY_REFINEMENT`

Secondary refinement needs were also observed in row classification, but the first-run failure mode is dominated by evidence policy.

## Key Metrics

Verified from manifest and run summary:

- `decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`
- `sheet_count = 6`
- `row_count_total = 82`
- `row_count_audited = 82`
- `pass_count = 0`
- `review_count = 81`
- `fail_count = 1`
- `issue_count_total = 85`
- `unit_issue_count = 1`
- `period_issue_count = 2`
- `valuation_issue_count = 0`
- `evidence_issue_count = 82`
- `clean_data_row_count = 0`
- `review_queue_row_count = 82`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

These numbers are internally consistent with the reviewed outputs:

- `review_queue.csv` contains `82` rows.
- Decision distribution is `81 REVIEW + 1 FAIL`.
- Issue distribution is:
  - `missing_evidence = 82`
  - `period_values_missing = 2`
  - `monetary_unit_mismatch = 1`

## Evidence Issue Analysis

### Why `evidence_issue_count = 82`

All `82` audited rows were assigned `missing_evidence`.

This did not happen because the pilot had zero lineage.

The reviewed `evidence_index.json` shows every row has exactly two evidence references:

- `source_pdf`
- `workbook_row`

That means every row currently preserves:

- source PDF identity
- workbook sheet name
- workbook row index
- row metric label

However, the workbook contains no explicit page/source/evidence column, and the first-run evidence checker treats absence of explicit page/evidence reference as `missing_evidence` for every row.

### Are these truly `MISSING_EVIDENCE`

Not all of them.

The workbook does not contain explicit page numbers or explicit source-trace columns. So `STRONG_EVIDENCE` is not present.

But most rows do have weak lineage:

- source PDF path exists
- sheet-level location exists
- row-level location exists

Under the workflow guidance in `.skills/agent_excel_intake_audit_workflow.md`, this is closer to `WEAK_EVIDENCE` than true `MISSING_EVIDENCE`.

Recommended interpretation:

- `MISSING_EVIDENCE` should mean no usable lineage beyond raw value presence.
- `WEAK_EVIDENCE` should mean workbook row lineage exists but no page-level or section-level proof exists.

Under that framing, the current `82` rows are mostly weak evidence, not true missing evidence.

### Does the workbook contain explicit page/source columns

No explicit page/source/evidence column was found in the reviewed sheet headers:

- `核心观点`: `类别`, `内容详情`
- `市场与基础数据`: `数据类别`, `指标`, `数值`
- `财务估值`: `会计年度`, `2024A`, `2025A`, `2026E`, `2027E`, `2028E`
- `资产负债表`: `会计年度`, `2024A`, `2025A`, `2026E`, `2027E`, `2028E`
- `利润表`: `会计年度`, `2024A`, `2025A`, `2026E`, `2027E`, `2028E`
- `现金流量表`: `会计年度`, `2024A`, `2025A`, `2026E`, `2027E`, `2028E`

No row in `evidence_index.json` had `explicit_evidence_ref`.

## Sheet And Row Classification Analysis

### Workbook Sheet Names

- `核心观点`
- `市场与基础数据`
- `财务估值`
- `资产负债表`
- `利润表`
- `现金流量表`

### Strict Financial Table Sheets

These sheets look like strict financial tables and should remain under stronger table-style audit policy:

- `财务估值`
- `资产负债表`
- `利润表`
- `现金流量表`

Reason:

- they use year columns such as `2024A / 2025A / 2026E / 2027E / 2028E`
- they contain row labels plus multi-period numeric values
- they behave like structured financial statements or valuation tables

### Narrative / Semi-Structured Sheets

These sheets do not look like strict financial statement tables:

- `核心观点`
- `市场与基础数据`

`核心观点` is clearly narrative / investment-summary content:

- 评级
- 核心逻辑
- 事件点评
- 投资建议
- 风险提示

`市场与基础数据` is semi-structured reference data:

- close price
- market cap
- per-share indicators
- not a multi-period statement table

### Should narrative rows use strict financial table policy

No.

Narrative rows should not be audited under the same strict period/evidence expectations as structured financial-table rows.

For example:

- `核心观点:3 核心逻辑`
- `核心观点:4 事件点评`
- `核心观点:5 投资建议`
- `核心观点:6 风险提示`

These rows are meaningful content, but they are not row-based financial statement metrics that naturally map to table-style page evidence or year-column logic.

They still need audit treatment, but likely under a different row type such as:

- `NARRATIVE_ASSERTION`
- `REFERENCE_MARKET_DATA`
- `STRICT_FINANCIAL_TABLE_ROW`

## Review Queue Quality Analysis

### Are review reasons specific and useful

Currently, mostly no.

The queue is technically explicit, but not diagnostically rich.

`review_queue.csv` is dominated by one generic reason:

- `missing_evidence`

Issue distribution from the queue:

- `missing_evidence = 82`
- `period_values_missing = 2`
- `monetary_unit_mismatch = 1`

As a result, the queue explains very little beyond:

```text
this row lacks explicit page/source evidence
```

### Can a reviewer understand why each row needs review

Only at a coarse level.

A reviewer can tell that:

- the row identity is preserved
- the row lacks explicit evidence reference

But the queue does not distinguish:

- weak lineage vs total evidence absence
- narrative row vs strict financial row
- page-trace gap vs structural row quality gap

So most rows are pushed into one generic review bucket rather than a useful triage structure.

### Which issue codes dominate

Dominant issue code:

- `missing_evidence`

This is the main reason `clean_data_row_count = 0` and `review_queue_row_count = 82`.

## Clean Data Policy Analysis

### Is `clean_data_row_count = 0` expected

Yes, under the current evidence policy.

Because every row gets `missing_evidence`, every row becomes at least `REVIEW`, even when:

- unit semantics are fine
- period structure is fine
- valuation labeling is fine
- row lineage is still present at workbook level

### Is this mainly evidence policy, not checker failure

Yes.

The zero-pass result is primarily caused by evidence policy strictness, not by broad failure of unit/period/valuation checkers.

### Which row types could likely become `PASS` after evidence policy refinement

Most plausible first-pass candidates:

- clean multi-period rows in `财务估值`
- clean structured rows in `资产负债表`
- clean structured rows in `利润表`
- clean populated rows in `现金流量表`
- selected market-reference rows in `市场与基础数据`

These could become `PASS` or at least separate into `WEAK_EVIDENCE_REVIEW` rather than hard `MISSING_EVIDENCE_REVIEW`, depending on pilot policy.

For an early non-client pilot, it is reasonable to allow weak lineage for internal clean-output candidates while keeping formal delivery gates closed.

## Checker Behavior Analysis

### `unit_issue_count = 1`

This is plausible for the current implementation, but the one detected case looks like a false positive or over-broad heuristic:

- `市场与基础数据:11`
- metric: `净资产收益率(%)`
- issues: `monetary_unit_mismatch;missing_evidence`
- decision: `FAIL`

`净资产收益率(%)` is a percentage metric, not a monetary amount. The `FAIL` appears to come from the unit checker treating `资产` inside the metric label as if it were a monetary-amount clue.

So the count itself is plausible under the current heuristic, but the single flagged case suggests checker refinement will eventually be needed.

### `period_issue_count = 2`

This is plausible and appears justified from the workbook structure.

The two flagged rows are:

- `现金流量表:2 经营活动现金流`
- `现金流量表:11 每股指标 (元)`

Both rows have period columns in the sheet header but no populated period values in that row.

That is a reasonable first-pass `period_values_missing` flag.

### `valuation_issue_count = 0`

This is plausible for this workbook.

The valuation rows in `财务估值` such as:

- `P/E(倍)`
- `P/B(倍)`

already carry multiple-like labels, so zero valuation issues is not obviously wrong.

### Are there obvious false negatives

No strong evidence of major valuation false negatives was found from the reviewed outputs.

The more visible problem is not valuation coverage. It is:

- evidence overclassification
- lack of row-type separation
- one apparent unit false positive on `净资产收益率(%)`

## Risks

- `missing_evidence` currently overstates the severity of rows that still have workbook lineage.
- narrative and strict table rows are mixed into one review policy.
- the queue is too flat to support efficient human triage.
- one current unit `FAIL` appears to be driven by label-token ambiguity rather than a clear real-world unit mismatch.
- zero clean rows may mislead downstream readers into thinking the workbook content is broadly unusable, when the real issue is mostly traceability policy.

## Recommended Refinements

Priority order:

1. Evidence policy refinement
2. Row type classification refinement
3. Checker refinement

### 1. Evidence policy refinement

Highest priority.

Refine evidence levels into something like:

- `STRONG_EVIDENCE`
- `WEAK_EVIDENCE`
- `MISSING_EVIDENCE`
- `NOT_APPLICABLE`

For this pilot, `source_pdf + sheet_name + row_index` should usually be treated as weak evidence, not total absence.

### 2. Row type classification refinement

Second priority.

Split rows at least into:

- strict financial table rows
- market/reference rows
- narrative rows

Then apply different evidence and review expectations by row type.

### 3. Checker refinement

Third priority.

The first visible checker-level target is the `净资产收益率(%)` false-positive-style `FAIL`.

That looks narrower than the current evidence-policy problem and should not be treated as the primary blocker.

## Decision

Primary decision:

`348A_QA_CONFIRMED_NEEDS_EVIDENCE_POLICY_REFINEMENT`

Supporting decision:

`348A_QA_CONFIRMED_NEEDS_ROW_CLASSIFICATION_REFINEMENT`

Rationale:

The first real pilot did not fail because the workbook lacked all traceability or because the core unit/period/valuation checkers broadly malfunctioned.

It failed mainly because the current evidence policy collapses weak lineage into `missing_evidence`, which in turn forces all rows into review and prevents any clean-data output.
