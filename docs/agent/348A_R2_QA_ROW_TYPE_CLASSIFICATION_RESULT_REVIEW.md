# 348A-R2-QA Row Type Classification Result Review

## Task ID

`348A-R2-QA Row Type Classification Result Review`

## Input Output Directory Reviewed

`D:\_datefac_agent\output\agent_excel_intake_audit_348a_r2`

Reviewed files:

- `agent_excel_intake_audit_348a_manifest.json`
- `agent_excel_intake_audit_348a_run_summary.json`
- `audit_report.md`
- `evidence_index.json`
- `review_queue.csv`
- `clean_data.csv`

## Manifest Decision

Primary QA decision:

`348A_R2_QA_CONFIRMED_NEXT_UNIT_CHECKER_REFINEMENT`

Supporting decisions:

- `348A_R2_QA_CONFIRMED_ROW_TYPE_CLASSIFICATION_USEFUL`
- `348A_R2_QA_CONFIRMED_NEXT_CLEAN_DATA_POLICY`

## Verified Key Metrics

Verified from manifest, run summary, review queue, and evidence index:

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
- `strong_evidence_count = 0`
- `weak_evidence_count = 82`
- `missing_evidence_count = 0`
- `not_applicable_evidence_count = 0`
- `strict_financial_table_row_count = 67`
- `market_reference_row_count = 10`
- `narrative_assertion_count = 5`
- `unknown_row_count = 0`
- `review_queue_row_count = 82`
- `clean_data_row_count = 0`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

Cross-check results:

- Row-type counts sum to `82` exactly: `67 + 10 + 5 + 0 = 82`.
- `review_queue.csv` contains `82` rows with decision split `81 REVIEW + 1 FAIL`.
- `evidence_index.json` contains `82` entries with evidence split `82 WEAK_EVIDENCE`.
- `clean_data.csv` contains `0` rows.

## Row-Type Distribution Analysis

### 1. Do row-type counts add up to 82

Yes. The distribution is internally consistent.

### 2. Is `strict_financial_table_row_count = 67` reasonable

Yes for this workbook.

Observed strict-sheet breakdown from `review_queue.csv`:

- `财务估值 = 10`
- `资产负债表 = 26`
- `利润表 = 18`
- `现金流量表 = 13`

These add to `67`, and all four sheets behave like multi-period structured financial tables.

### 3. Is `market_reference_row_count = 10` reasonable

Yes. `市场与基础数据` contributes `10` rows and reads like market/reference data rather than a narrative sheet or a strict statement table.

### 4. Is `narrative_assertion_count = 5` reasonable

Yes. `核心观点` contributes `5` rows:

- `评级`
- `核心逻辑`
- `事件点评`
- `投资建议`
- `风险提示`

These are clearly narrative assertions.

### 5. Is `unknown_row_count = 0` safe

It is safe for this specific workbook, but not globally strong evidence that the classifier is complete.

Why it is acceptable here:

- the workbook has only six reviewed sheets;
- all six sheets fall into the intended explicit mapping;
- no stray sheet or ambiguous row family appeared in the reviewed output.

Why it is still slightly overconfident as a general posture:

- the current classifier is mostly sheet-mapping-driven;
- unseen future workbooks could contain mixed or renamed sheets that should fall back to `UNKNOWN_ROW`.

So `unknown_row_count = 0` is plausible for this file, but should not be treated as proof that `UNKNOWN_ROW` is unnecessary.

## Sheet-To-Row-Type Mapping Analysis

The reviewed output supports the current mapping:

- `财务估值 -> STRICT_FINANCIAL_TABLE_ROW`
- `资产负债表 -> STRICT_FINANCIAL_TABLE_ROW`
- `利润表 -> STRICT_FINANCIAL_TABLE_ROW`
- `现金流量表 -> STRICT_FINANCIAL_TABLE_ROW`
- `市场与基础数据 -> MARKET_REFERENCE_ROW`
- `核心观点 -> NARRATIVE_ASSERTION`

Findings:

- No obvious misclassification was found in `review_queue.csv`.
- Narrative content is no longer presented as if it were a strict financial statement row.
- Market-reference rows are now visibly separated from both narrative assertions and strict financial-table rows.
- The two `period_values_missing` rows both sit inside `现金流量表`, which supports the strict-sheet mapping rather than contradicting it.

## Review Queue Quality Analysis

### 1. Does `review_queue.csv` include `row_type`

Yes.

Observed columns:

- `sheet_name`
- `row_index`
- `metric_name`
- `decision`
- `issue_count`
- `issue_codes`
- `evidence_level`
- `row_type`
- `unit_hint`
- `period_labels`
- `explicit_evidence_ref`

### 2. Is triage more useful than R1

Yes.

R1 already split `WEAK_EVIDENCE` from `MISSING_EVIDENCE`, but R2 makes the queue much easier to triage because the reviewer can now distinguish:

- `NARRATIVE_ASSERTION + weak_evidence`
- `MARKET_REFERENCE_ROW + weak_evidence`
- `STRICT_FINANCIAL_TABLE_ROW + weak_evidence`
- `STRICT_FINANCIAL_TABLE_ROW + period_values_missing`

That is materially more useful than one flat queue of weak-evidence rows.

### 3. Are `period_values_missing` issues limited to strict financial rows

Yes in the reviewed output.

The two rows are:

- `现金流量表:2 经营活动现金流`
- `现金流量表:11 每股指标 (元)`

Both are `STRICT_FINANCIAL_TABLE_ROW`. No narrative or market-reference row carries `period_values_missing`.

### 4. Is the one `FAIL` still the unit false-positive-style case

Yes.

The only `FAIL` is:

- `市场与基础数据:11`
- metric `净资产收益率(%)`
- row type `MARKET_REFERENCE_ROW`
- issue codes `monetary_unit_mismatch;weak_evidence`

This is still the same false-positive-style case identified earlier. R2 did not create a new blocker there; it only made the row type visible.

## Evidence Index Quality Analysis

### 1. Does `evidence_index.json` include `row_type`

Yes.

Observed evidence entry keys:

- `sheet_name`
- `row_index`
- `metric_name`
- `row_type`
- `decision`
- `evidence_level`
- `explicit_evidence_ref`
- `evidence_refs`
- `raw_values`

### 2. Does row type improve traceability

Yes.

`evidence_level + row_type` is more informative than `evidence_level` alone:

- narrative weak-evidence rows are clearly not pretending to be financial statement lines;
- market-reference rows are visible as a separate family;
- strict-table rows remain reviewable under stricter expectations.

### 3. Are R1 evidence distinctions preserved

Yes.

The reviewed index still shows `WEAK_EVIDENCE` rather than collapsing back into `MISSING_EVIDENCE`. This confirms that R2 did not undo R1.

## Audit Report Quality Analysis

Positive findings:

- `audit_report.md` includes row-type distribution counts.
- The boundary section clearly states:
  - no PDF re-extraction;
  - no MinerU;
  - no OCR;
  - no LLM/VLM API calls;
  - review-oriented output only.
- The report does not imply `client_ready` or `production_ready`.
- Sample issues now show row type, which makes the report easier to scan.

Residual issue:

- `audit_report.md` is still dominated by weak-evidence examples, so the report is clearer than before but still not yet a true clean-data readiness report. That is expected at this stage.

## Remaining Risks

- `clean_data_row_count = 0` remains unchanged, so the pilot still has no clean-output policy beyond conservative review gating.
- The only `FAIL` still appears to be a unit-checker false positive on `净资产收益率(%)`.
- `unknown_row_count = 0` is acceptable for this workbook but should not become an assumption for future workbooks.
- The current row-type classifier appears useful at sheet level, but it has not yet been stress-tested against mixed or renamed sheets.

## Recommended Refinements

Priority order:

1. `348A-R3 Unit Checker False Positive Refinement`
2. `348A-R4 Clean Data Candidate Policy`
3. future fixture harvesting for row-type and unit-edge cases

Reasoning:

- The current row-type refinement already achieved its main purpose: better triage visibility.
- The next blocker is correctness of the single `FAIL`, because a false `FAIL` is more misleading than a conservative `REVIEW`.
- Clean-data policy should come after that, otherwise policy work risks building on a known false-positive severity signal.

## Decision

Primary decision:

`348A_R2_QA_CONFIRMED_NEXT_UNIT_CHECKER_REFINEMENT`

Supporting interpretation:

- R2 row-type classification is useful and should be kept.
- Sheet-to-row-type mapping looks correct for this workbook.
- `review_queue.csv` and `evidence_index.json` both benefited from the added `row_type`.
- The next change should not be broad row-type rework.
- The next focused refinement should be the `净资产收益率(%)` unit false-positive-style case, followed by clean-data candidate policy.
