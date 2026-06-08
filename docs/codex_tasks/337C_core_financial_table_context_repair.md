# 337C Core Financial Table Recognition and Context Repair

## Goal
Improve 337B precision by:
- rescuing true core financial summary and forecast tables
- separating real financial appendix tables from legal disclosure tables
- repairing unit inheritance
- repairing `YoY` parent metric context
- auditing the still-high reviewed output for `H3_AP202606081823356439_1.pdf`

This task remains local-only, sidecar-only, preview-only.

## Inputs
- `D:/_datefac/output/mineru_candidate_precision_337b`
- `D:/_datefac/output/mineru_candidate_precision_337b/real_test_mineru_client_export_337b.xlsx`
- `D:/_datefac/output/mineru_candidate_precision_337b/mineru_candidate_precision_337b_before_after.xlsx`
- `D:/_datefac/output/mineru_real_test_337a`
- `D:/_datefac/input/real_test`

## Output Directory
- `D:/_datefac/output/core_financial_context_repair_337c`

## Expected Artifacts
- `core_financial_context_repair_337c_summary.json`
- `core_financial_context_repair_337c_manifest.json`
- `core_financial_context_repair_337c_qa.json`
- `core_financial_context_repair_337c_report.md`
- `core_financial_context_repair_337c_before_after.xlsx`
- `real_test_mineru_client_export_337c.xlsx`

## Reuse Policy
- Reuse 337B outputs.
- Do not rerun MinerU unless clearly necessary.
- Do not modify 337A or 337B outputs in place.
- Do not modify production pipeline, parser, extraction, delivery, official assets, or protected dirty files.
- Do not commit generated output artifacts.

## Core Repairs

### A. Core Financial Summary Table Rescue
If a table has:
- year columns like `2024A / 2025A / 2026E / 2027E / 2028E`
- and row labels containing at least two of:
  - `营业收入`
  - `归母净利润`
  - `净利润`
  - `EPS`
  - `每股收益`
  - `PE / P-E`
  - `PB / P-B`
  - `ROE`
  - `毛利率`
  - `净利率`

Then classify or upgrade it as:
- `CORE_FINANCIAL_SUMMARY`
or
- `PROFIT_FORECAST_VALUATION`

This must override weak `INDUSTRY_DATA_TABLE` classification unless the table clearly contains peer company codes/names or market-size style industry content.

### B. Financial Appendix Table Rescue
Do not classify these as `LEGAL_DISCLOSURE_TABLE` only because they are near the end:
- `资产负债表`
- `利润表`
- `现金流量表`
- `主要财务比率`
- `财务预测摘要`

Classify them as:
- `FINANCIAL_STATEMENT_DETAIL`
or
- `PROFIT_FORECAST_VALUATION`

unless the table is actually legal or rating-system content.

### C. Legal / Rating Exclusion Remains Strict
Keep excluding:
- `投资评级说明`
- `股票投资评级说明`
- `分析师承诺`
- `免责声明`
- `法律声明`
- `评级体系`
- `适当性管理`
- explanation tables for `买入 / 增持 / 中性 / 减持`

### D. Unit Inheritance Repair
If row unit is empty:
- inherit from row label when it contains:
  - `(百万元)`
  - `(亿元)`
  - `(元)`
  - `(%)`
  - `(倍)`
- otherwise inherit from table title / header / context when it contains:
  - `利润表(百万元)`
  - `资产负债表(百万元)`
  - `现金流量表(百万元)`
  - `财务预测摘要(百万元)`
- `EPS` defaults to `元`
- `PE / PB` defaults to `倍`
- `ROE / gross_margin / net_margin / revenue_yoy / net_profit_yoy` default to `%`

Report:
- `unit_filled_count`
- `unit_still_missing_count`

### E. YoY Parent Repair
For `YoY / 同比` rows:
- infer parent metric from the nearest previous non-YoY metric row in the same table
- `营业收入 -> revenue_yoy`
- `归母净利润 / 净利润 -> net_profit_yoy`
- if parent cannot be inferred, route to `needs_review`
- do not let net_profit `YoY` become `revenue_yoy`

Report:
- `yoy_parent_repaired_count`
- `yoy_parent_ambiguous_count`

### F. High-Reviewed Audit For `H3_AP202606081823356439_1.pdf`
Create an audit sheet listing all reviewed rows for that PDF:
- page
- table role
- metric
- year
- value
- unit
- evidence
- reason why reviewed

Then tighten:
- if source table is industry / macro / company-history / product / channel style, move rows to `needs_review` or `rejected`
- if source table is a real forecast / valuation / core summary table, keep reviewed

### G. Before / After Workbook
Create `core_financial_context_repair_337c_before_after.xlsx` with sheets:
- `00_SUMMARY`
- `01_337B_COUNTS`
- `02_337C_COUNTS`
- `03_TABLE_ROLE_REPAIRS`
- `04_UNIT_REPAIRS`
- `05_YOY_PARENT_REPAIRS`
- `06_REVIEWED_AFTER_337C`
- `07_NEEDS_REVIEW_AFTER_337C`
- `08_REJECTED_AFTER_337C`
- `09_356439_REVIEWED_AUDIT`
- `10_ROUTE_CHANGE_TRACE`

## Final Customer Workbook
Create `real_test_mineru_client_export_337c.xlsx` with sheets:
- `00_README`
- `01_REVIEWED_CORE_METRICS`
- `02_NEEDS_REVIEW`
- `03_REJECTED_OR_EXCLUDED`
- `04_SOURCE_TRACE`
- `05_DOCUMENT_SUMMARY`
- `06_TABLE_CLASSIFICATION_SUMMARY`
- `07_CONTEXT_REPAIR_SUMMARY`

## QA Requirements
- 337B workbook exists.
- 3 PDFs are represented.
- no legal / rating / disclosure table rows in reviewed.
- true financial summary tables are not classified as `INDUSTRY_DATA_TABLE` when they match the core summary pattern.
- financial statement appendix tables are not classified as `LEGAL_DISCLOSURE_TABLE` unless actually legal/rating content.
- `unit_filled_count` is reported.
- `yoy_parent_repaired_count` is reported.
- no `net_profit_yoy` rows are mislabeled as `revenue_yoy`.
- reviewed rows have `source_page`.
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Files To Create
- `docs/codex_tasks/337C_core_financial_table_context_repair.md`
- `datefac/trust/core_financial_context_repair_337c.py`
- `datefac/trust/core_financial_context_repair_337c_report.py`
- `tools/run_core_financial_context_repair_337c.py`
- `tests/trust/test_core_financial_context_repair_337c.py`

## Validation
Run:

```powershell
python -m py_compile datefac\trust\core_financial_context_repair_337c.py datefac\trust\core_financial_context_repair_337c_report.py tools\run_core_financial_context_repair_337c.py tests\trust\test_core_financial_context_repair_337c.py
python -m pytest tests\trust\test_core_financial_context_repair_337c.py -q
python tools\run_core_financial_context_repair_337c.py --precision-337b-dir D:\_datefac\output\mineru_candidate_precision_337b --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\core_financial_context_repair_337c
```

## Final Reporting
After the run, report in simple Chinese:
1. 337B reviewed 数
2. 337C reviewed 数
3. 修复了多少张表格分类
4. 填补了多少单位
5. 修复了多少 YoY 父指标
6. `356439` 的 reviewed 是否下降或更干净
7. 每个 PDF 的 reviewed / needs_review / rejected
8. 最终应该打开哪个 Excel
