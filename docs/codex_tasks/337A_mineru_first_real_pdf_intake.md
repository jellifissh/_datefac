# 337A MinerU-First Real PDF Intake

## Goal
Create a sidecar local-only raw PDF intake flow that starts from `D:/_datefac/input/real_test`, runs or reuses MinerU outputs, converts them into DateFac-readable debug artifacts, and produces a combined Excel preview workbook.

This task is still preview-only. It is not client-ready and not production-ready.

## Decision
- MinerU is the primary parser path.
- `pdfplumber` may be used only for lightweight fallback or debug helpers if needed.
- Marker is not required in this task.
- Do not build a parser ensemble in 337A.

## Input
- `D:/_datefac/input/real_test`

Expected PDFs:
- `H3_AP202606081823352620_1.pdf`
- `H3_AP202606081823352906_1.pdf`
- `H3_AP202606081823356439_1.pdf`

## Output Directory
- `D:/_datefac/output/mineru_real_test_337a`

## Expected Output Structure
`D:/_datefac/output/mineru_real_test_337a`

- `00_batch_summary.xlsx`
- `00_batch_summary.json`
- `00_batch_report.md`
- `mineru_outputs/`
  - `<pdf_stem>/`
- `datefac_debug/`
  - `<pdf_stem>/`
    - `document_summary.json`
    - `mineru_artifact_inventory.xlsx`
    - `extracted_page_text.xlsx`
    - `extracted_tables.xlsx`
    - `financial_table_candidates.xlsx`
    - `metric_candidates.xlsx`
    - `routing_preview.xlsx`
    - `client_preview.xlsx`
    - `debug_report.md`
- `real_test_mineru_client_export_337a.xlsx`
- `real_test_mineru_337a_qa.json`
- `real_test_mineru_337a_manifest.json`

## MinerU Behavior
1. Inspect local MinerU availability and prefer the real local executable path.
2. If a valid MinerU parse folder already exists for a PDF under `mineru_outputs/<pdf_stem>/auto`, reuse it.
3. Otherwise run MinerU for that PDF and write outputs under:
   - `D:/_datefac/output/mineru_real_test_337a/mineru_outputs`
4. If MinerU cannot be invoked automatically:
   - do not fake success
   - generate a blocked report
   - include the exact manual MinerU command for each PDF
   - still produce summary and QA artifacts describing what is missing

Expected real command shape:

```powershell
D:\anaconda\envs\mineru_new\Scripts\mineru.exe -p <pdf_path> -o D:\_datefac\output\mineru_real_test_337a\mineru_outputs -b pipeline -m auto -l ch
```

## DateFac-Side Extraction Scope
Read MinerU outputs and surface:
- markdown text if present
- content list JSON blocks if present
- html tables from MinerU table blocks if present
- page-level text evidence when recoverable
- source trace fields for every routed candidate

## Financial Table Candidate Detection
Use conservative keyword-driven table scoring. Relevant terms include:
- `财务数据`
- `估值`
- `财务摘要`
- `盈利预测`
- `营业收入`
- `归母净利润`
- `净利润`
- `EPS`
- `每股收益`
- `PE`
- `P/E`
- `PB`
- `P/B`
- `ROE`
- `毛利率`
- `净利率`
- `同比`
- `2024A`
- `2025A`
- `2026E`
- `2027E`
- `2028E`

## Core Metric Extraction
Extract conservatively:
- `revenue / 营业收入`
- `net_profit / 归母净利润`
- `EPS / 每股收益`
- `PE / P/E`
- `PB / P/B`
- `ROE`
- `gross_margin / 毛利率`
- `net_margin / 净利率`
- `YoY / 同比增长`
- `rating / 投资评级` if easy
- `report_date / 报告日期` if easy
- `broker / 机构` if easy
- `stock_code / 股票代码` if easy
- `stock_name / 股票名称` if easy

## Routing Policy
- Route to `reviewed_preview` only when metric, value, source page, and surrounding context are clear.
- Route to `needs_review` when unit is missing, year is ambiguous, value may actually be a year, or source context is weak.
- Route to `rejected_or_excluded` when the row is obvious disclaimer noise, rating-system explanation, or non-financial junk.
- Be conservative. Prefer `needs_review` over aggressive promotion.

## Per-PDF Debug Package
Create one folder under `datefac_debug/<pdf_stem>` for each PDF.

Required files:
1. `document_summary.json`
2. `mineru_artifact_inventory.xlsx`
3. `extracted_page_text.xlsx`
4. `extracted_tables.xlsx`
5. `financial_table_candidates.xlsx`
6. `metric_candidates.xlsx`
7. `routing_preview.xlsx`
8. `client_preview.xlsx`
9. `debug_report.md`

### document_summary.json
Include:
- pdf filename
- parse status
- page count
- MinerU table count
- financial table candidate count
- metric candidate count
- reviewed count
- needs review count
- rejected count
- likely forecast pages
- manual MinerU command
- failure reason if blocked or partial

## Combined Workbook
Create:
- `D:/_datefac/output/mineru_real_test_337a/real_test_mineru_client_export_337a.xlsx`

Sheets:
1. `00_README`
2. `01_REVIEWED_CORE_METRICS`
3. `02_NEEDS_REVIEW`
4. `03_REJECTED_OR_EXCLUDED`
5. `04_SOURCE_TRACE`
6. `05_DOCUMENT_SUMMARY`
7. `06_FINANCIAL_TABLE_CANDIDATES`

Customer-facing columns:
- `row_no`
- `document`
- `metric`
- `metric_display_zh`
- `year`
- `value`
- `unit`
- `source_page`
- `status`
- `source_evidence_excerpt`
- `notes`

Rules:
- Do not expose unnecessary internal stage noise in customer-facing sheets.
- Do not claim client-ready.
- Do not claim production-ready.
- Do not claim 100% accuracy.
- Do not claim investment advice.

## Files To Create
- `docs/codex_tasks/337A_mineru_first_real_pdf_intake.md`
- `datefac/trust/mineru_real_pdf_intake_337a.py`
- `datefac/trust/mineru_real_pdf_intake_337a_report.py`
- `tools/run_mineru_real_pdf_intake_337a.py`
- `tests/trust/test_mineru_real_pdf_intake_337a.py`

## Boundaries
- Do not modify production pipeline behavior.
- Do not modify parser / extraction / delivery files.
- Do not modify official assets.
- Do not modify protected dirty files.
- Do not commit generated output artifacts.
- Do not use `git add -A`.
- Do not use `git add .`.

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
python -m py_compile datefac\trust\mineru_real_pdf_intake_337a.py datefac\trust\mineru_real_pdf_intake_337a_report.py tools\run_mineru_real_pdf_intake_337a.py tests\trust\test_mineru_real_pdf_intake_337a.py
python -m pytest tests\trust\test_mineru_real_pdf_intake_337a.py -q
python tools\run_mineru_real_pdf_intake_337a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\mineru_real_test_337a
```

## Final Reporting
After the run, report in simple Chinese:
1. MinerU 是否成功运行
2. 找到几个 PDF
3. 成功解析几个 PDF
4. 每个 PDF 有多少页
5. 每个 PDF 检测到多少个 MinerU 表格 / 表格候选
6. 每个 PDF 抽到多少核心指标候选
7. reviewed / needs_review / rejected 各多少
8. 哪些页面最像财务预测表
9. 最终应该打开哪个 Excel
10. 如果 MinerU 没跑起来，下一步手动命令是什么
