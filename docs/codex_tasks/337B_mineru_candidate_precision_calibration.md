# 337B MinerU Candidate Precision Calibration

## Goal
Calibrate the MinerU-first 337A sidecar output for better precision.

The objective is to reduce duplicate tables, suppress weak or non-core reviewed rows, tighten reviewed routing, and improve context handling for `YoY` rows.

This task is still local-only, sidecar-only, preview-only.

## Inputs
- `D:/_datefac/output/mineru_real_test_337a`
- `D:/_datefac/output/mineru_real_test_337a/real_test_mineru_client_export_337a.xlsx`
- `D:/_datefac/input/real_test`

## Output Directory
- `D:/_datefac/output/mineru_candidate_precision_337b`

## Expected Artifacts
- `mineru_candidate_precision_337b_summary.json`
- `mineru_candidate_precision_337b_manifest.json`
- `mineru_candidate_precision_337b_qa.json`
- `mineru_candidate_precision_337b_report.md`
- `mineru_candidate_precision_337b_before_after.xlsx`
- `real_test_mineru_client_export_337b.xlsx`

## Reuse Policy
- Reuse 337A outputs.
- Do not rerun MinerU unless clearly necessary.
- Do not modify 337A output in place.
- Do not modify production pipeline, parser, extraction, delivery, official assets, or protected dirty files.
- Do not commit generated output artifacts.

## Calibration Requirements

### A. Table Deduplication
- Detect duplicate or near-duplicate tables produced from multiple MinerU views.
- Use `table_preview`, page number, row/column structure, and metric-year signature.
- Keep the better table candidate and suppress weaker duplicates.
- Report `duplicate_table_removed_count`.

### B. Table Role Filtering
Map candidate tables into:
- `CORE_FINANCIAL_SUMMARY`
- `PROFIT_FORECAST_VALUATION`
- `FINANCIAL_STATEMENT_DETAIL`
- `INDUSTRY_DATA_TABLE`
- `RATING_STANDARD_TABLE`
- `LEGAL_DISCLOSURE_TABLE`
- `COMPANY_PROFILE_TABLE`
- `OTHER_TABLE`

Only these may produce reviewed rows:
- `CORE_FINANCIAL_SUMMARY`
- `PROFIT_FORECAST_VALUATION`
- selected `FINANCIAL_STATEMENT_DETAIL` rows when metric/year/unit/value are clear

These must not produce reviewed rows:
- `RATING_STANDARD_TABLE`
- `LEGAL_DISCLOSURE_TABLE`
- `INDUSTRY_DATA_TABLE`
- `COMPANY_PROFILE_TABLE`
- `OTHER_TABLE`

### C. Page Filtering
De-prioritize or exclude pages dominated by:
- `分析师承诺`
- `评级说明`
- `免责声明`
- `法律声明`
- pages that are only `风险提示`
- pages that are only `目录`

### D. Metric Filtering
Reviewed rows should focus on:
- `revenue / 营业收入`
- `net_profit / 归母净利润`
- `EPS / 每股收益`
- `PE / P/E`
- `PB / P/B`
- `ROE`
- `gross_margin / 毛利率`
- `net_margin / 净利率`
- `revenue_yoy`
- `net_profit_yoy`

Do not route these as reviewed unless context is very clear:
- generic `YoY` without parent metric
- rating rows from rating-system tables
- broker metadata from disclosure pages
- stock_name from random company profile tables

### E. YoY Context Repair
If a row is `YoY / 同比`:
- infer the parent metric from the nearby previous row when possible
  - `营业收入 -> revenue_yoy`
  - `归母净利润 / 净利润 -> net_profit_yoy`
- if parent cannot be inferred, route to `needs_review`

### F. Reviewed Strictness
A row may be `reviewed` only if:
- table role is allowed
- metric is allowed
- year is clear
- value is not itself a year
- source page exists
- evidence is not from legal/rating/disclaimer context
- row is not duplicate

Otherwise route to `needs_review` or `rejected`.

### G. Before / After Comparison
Create `mineru_candidate_precision_337b_before_after.xlsx` with sheets:
- `00_SUMMARY`
- `01_BEFORE_COUNTS`
- `02_AFTER_COUNTS`
- `03_REVIEWED_AFTER`
- `04_NEEDS_REVIEW_AFTER`
- `05_REJECTED_AFTER`
- `06_DUPLICATE_TABLES_REMOVED`
- `07_TABLE_ROLE_CLASSIFICATION`
- `08_ROUTE_CHANGE_TRACE`

## Final Customer Workbook
Create `real_test_mineru_client_export_337b.xlsx` with sheets:
- `00_README`
- `01_REVIEWED_CORE_METRICS`
- `02_NEEDS_REVIEW`
- `03_REJECTED_OR_EXCLUDED`
- `04_SOURCE_TRACE`
- `05_DOCUMENT_SUMMARY`
- `06_TABLE_CLASSIFICATION_SUMMARY`

## QA Requirements
- 337A summary and workbook exist.
- 3 PDFs are represented.
- Deduplication summary is generated.
- Table role classification is generated.
- reviewed count after calibration is less than or equal to 337A reviewed count.
- `needs_review` or `rejected` absorb unsafe rows.
- no `RATING_STANDARD_TABLE` rows in reviewed.
- no `LEGAL_DISCLOSURE_TABLE` rows in reviewed.
- no `2024/2025/2026/2027/2028` style value enters reviewed as numeric metric value.
- generic `YoY` without parent metric does not enter reviewed.
- `qa_fail_count = 0`
- `client_ready = false`
- `production_ready = false`

## Files To Create
- `docs/codex_tasks/337B_mineru_candidate_precision_calibration.md`
- `datefac/trust/mineru_candidate_precision_337b.py`
- `datefac/trust/mineru_candidate_precision_337b_report.py`
- `tools/run_mineru_candidate_precision_337b.py`
- `tests/trust/test_mineru_candidate_precision_337b.py`

## Boundaries
- Do not modify production pipeline behavior.
- Do not modify parser / extraction / delivery files.
- Do not modify official assets.
- Do not modify protected dirty files.
- Do not use `git add -A`.
- Do not use `git add .`.
- Do not commit unless explicitly asked.

Protected dirty files:
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Validation
Run:

```powershell
python -m py_compile datefac\trust\mineru_candidate_precision_337b.py datefac\trust\mineru_candidate_precision_337b_report.py tools\run_mineru_candidate_precision_337b.py tests\trust\test_mineru_candidate_precision_337b.py
python -m pytest tests\trust\test_mineru_candidate_precision_337b.py -q
python tools\run_mineru_candidate_precision_337b.py --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\mineru_candidate_precision_337b
```

## Final Reporting
After the run, report in simple Chinese:
1. 337A reviewed 数是多少
2. 337B reviewed 数是多少
3. 去掉了多少重复表
4. 有多少 rating/legal/disclosure 表被排除
5. 每个 PDF 最终 reviewed/needs_review/rejected 数
6. 哪些指标质量最好
7. 哪些指标仍然需要人工复核
8. 最终应该打开哪个 Excel
