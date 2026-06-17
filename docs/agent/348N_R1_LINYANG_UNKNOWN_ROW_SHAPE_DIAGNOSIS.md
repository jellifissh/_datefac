## Task ID

`348N-R1 Linyang Unknown Row Shape Diagnosis`

## Reviewed Output Directory

`D:\_datefac_agent\output\agent_excel_intake_audit_348n_linyang_energy_testset`

## Available Files Inspected

- `agent_excel_intake_audit_348a_manifest.json`
- `agent_excel_intake_audit_348a_run_summary.json`
- `audit_report.md`
- `review_queue.csv`
- `clean_data.csv`
- `evidence_index.json`
- source workbook shape spot-check:
  `D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx`

## Manifest Metrics Recap

- `row_count_total = 483`
- `clean_data_row_count = 37`
- `review_queue_row_count = 446`
- `unknown_row_count = 367`
- `unit_issue_count = 9`
- `period_issue_count = 0`
- `valuation_issue_count = 0`
- `evidence_issue_count = 397`
- `strong_evidence_count = 86`
- `weak_evidence_count = 397`
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

## Unknown-Row Distribution By Sheet

Unknown rows counted from `evidence_index.json`:

- `normalized_testset = 319`
- `README = 12`
- `data_dictionary = 12`
- `market_base_data = 10`
- `figure_index = 7`
- `doc_metadata = 6`
- `related_research = 1`

Important split:

- `review_queue.csv` contains `357` unknown rows.
- The remaining `10` unknown rows are all from `market_base_data`.
- Those `10` rows are `PASS + STRONG_EVIDENCE`, so they do not enter the review queue.

## Unknown-Row Family Taxonomy

### 1. `normalized_testset` long-record family

- Count: `319`
- Visible pattern:
  `record_id / source_pdf / source_page / table_name / statement / line_item / period / value / unit / value_text_original / confidence / note`
- Metric label pattern:
  `R0001`, `R0002`, `R0003` ... record-style IDs, not normal financial line-item headers.
- Value shape:
  long-record normalized dataset, one record per row, with explicit period/value/unit columns.
- Nearby title / section:
  table names such as `盈利预测与估值`.
- Issue pattern:
  mostly `weak_evidence`; current review queue does not add richer reason text.
- Interpretation:
  this is not a standard wide-table extracted workbook shape. It is a normalized testset schema.

Conclusion:

- This family should not be force-routed into `STRICT_FINANCIAL_TABLE_ROW` under current intake assumptions.
- It needs new schema support before any safe routing change.

### 2. `README` workbook narrative / bookkeeping family

- Count: `12`
- Visible pattern:
  workbook-level notes such as `生成时间`, `源PDF`, `用途`, `口径`, `负数处理`, plus a few summary rows.
- Metric label pattern:
  narrative labels and summary items.
- Value shape:
  mostly text, plus some compact summary values.
- Interpretation:
  workbook metadata and explanatory text, not normal audited financial-table rows.

Sub-families:

- `readme_bookkeeping_or_narrative_row`
- `readme_summary_metric_row`

### 3. `data_dictionary` field-definition family

- Count: `12`
- Visible pattern:
  `字段 / 解释`, then rows like `source_pdf`, `source_page`, `table_name`, `statement`, `line_item`, `period`, `value`, `unit`, `confidence`, `note`.
- Value shape:
  dictionary definitions, not business data.
- Interpretation:
  clear testset bookkeeping / schema-description content.

### 4. `figure_index` chart-index family

- Count: `7`
- Visible pattern:
  `图表编号 / 页码 / 标题 / 图表类型 / 可用结构化数据 / 处理策略 / 备注`
- Value shape:
  narrative descriptions of figures and handling strategy.
- Interpretation:
  table-title / chart-index / extraction-guidance rows, not financial data rows.

### 5. `doc_metadata` metadata family

- Count: `6` unknowns, plus some rows already routed as narrative elsewhere.
- Visible pattern:
  `报告类型`, `行业`, `研究机构`, `发布日期`, `数据来源说明`, `货币单位说明`.
- Value shape:
  metadata fields with text values.
- Interpretation:
  workbook/report metadata, not strict table rows.

### 6. `related_research` reference family

- Count: `1`
- Visible pattern:
  date-title-reference row for related reports.
- Interpretation:
  narrative/reference content.

### 7. `market_base_data` structured market-data family

- Count: `10`
- Visible pattern:
  `类别 / 指标 / 数值 / 单位 / 期间口径 / 来源页 / 置信度 / 备注`
- Examples:
  `收盘价`, `一年最低价`, `一年最高价`, `市净率`, `总市值`, `每股净资产`.
- Value shape:
  structured numeric rows with unit and source page.
- Interpretation:
  these look like legitimate market/reference rows.

Note:

- They are still counted as `UNKNOWN_ROW` in the manifest, but they already pass with `STRONG_EVIDENCE`.
- They are the only unknown family that looks like a plausible future `MARKET_REFERENCE_ROW` candidate.

## Normal Workbook Schema Or Testset-Specific Shape

Primary conclusion:

- The unknown-row spike is mostly **testset-specific workbook structure**, not normal financial workbook schema unfamiliarity.

Why:

- `normalized_testset` alone contributes `319 / 367` unknown rows.
- That sheet is a normalized long-record extraction dataset, not a standard wide financial table.
- `README`, `data_dictionary`, `figure_index`, and `doc_metadata` reinforce that this workbook is packaged like a curated extraction testset rather than a normal downstream audit workbook.

## Clean-Data Boundary Check

Verified from `clean_data.csv`:

- `clean_data_row_count = 37`
- `STRICT_FINANCIAL_TABLE_ROW = 35`
- `MARKET_REFERENCE_ROW = 2`
- `UNKNOWN_ROW = 0`
- `NARRATIVE_ASSERTION = 0`

Conclusion:

- Current clean-data boundary is still conservative.
- Unknown rows are not leaking into clean data.
- Any future rerouting must preserve this boundary, especially for normalized testset rows.

## Review-Queue Burden Analysis

- `review_queue_row_count = 446`
- Unknown rows inside review queue = `357`
- Unknown review rows are dominated by:
  `normalized_testset = 319`
- Current unknown review rows are mostly surfaced as `weak_evidence` without richer reason granularity.

Interpretation:

- Review burden is high mainly because the runner is trying to audit a testset workbook shape with the standard workbook intake assumptions.
- This is not primarily a checker-quality issue.
- It is mostly an intake/schema-recognition mismatch plus workbook packaging noise.

## Out-of-Scope Assessment

Likely out-of-scope at current stage:

- `data_dictionary`
- `figure_index`
- most `README` explanatory rows
- `related_research`
- possibly much of `doc_metadata` if the goal remains table-value auditing rather than report metadata capture

Conditionally out-of-scope until dedicated support exists:

- `normalized_testset` long-record rows

Reason:

- They are valid extracted data, but not in the currently supported intake shape.
- Treating them as normal strict-table rows under the current parser would be unsafe.

## Candidate Safe Refinement Targets

Safe candidates for future `NARRATIVE_ASSERTION` routing:

- `doc_metadata` rows
- `README` bookkeeping/narrative rows
- `figure_index` rows
- `related_research` row

Possibly safe candidates for future `MARKET_REFERENCE_ROW` routing:

- `market_base_data` structured numeric rows with page/unit lineage

These changes look relatively low-risk because they should stay review-only or reference-only and do not require pretending the workbook is a strict financial-table schema.

## Candidate Unsafe Refinement Targets

Unsafe to reroute immediately:

- `normalized_testset` long-record rows to `STRICT_FINANCIAL_TABLE_ROW`
- `normalized_testset` long-record rows to `MARKET_REFERENCE_ROW`
- `README` summary metric rows directly into clean data
- `data_dictionary` rows into any clean-data path

Why:

- `normalized_testset` is structurally a different schema and needs dedicated intake support first.
- Naive rerouting could convert many numeric rows into false clean candidates.
- That would pollute `clean_data` and hide unresolved schema assumptions.

## Risk Assessment

Main risk:

- treating testset-format rows as if they were standard workbook rows.

Likely consequence if handled too aggressively:

- inflated clean-data counts
- misleading PASS decisions
- reduced explainability in review queue
- regression against the existing conservative gate discipline

Safer direction:

- keep current clean-data boundary
- add explicit schema handling for normalized testset format before any major rerouting
- optionally reroute obvious metadata/narrative families separately

## Baseline Validation

Validation run:

```powershell
python -m pytest tests\agent -q
```

Result:

- `38 passed`

## Decision

`348N_R1_CONFIRMED_LINYANG_UNKNOWN_ROW_FAMILIES_DIAGNOSED`

## Recommended Next Task

Recommended next task:

- `348N-R2 normalized_testset intake schema support diagnosis-to-implementation split`

Suggested scope:

- first add dedicated support for the `normalized_testset` long-record schema
- keep `README / data_dictionary / figure_index / doc_metadata / related_research` on a separate metadata-routing track
- only consider `market_base_data` row-type refinement if it does not expand clean-data acceptance
