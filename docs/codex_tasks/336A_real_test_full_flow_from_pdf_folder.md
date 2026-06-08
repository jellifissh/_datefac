# 336A Real Test Full Flow From PDF Folder

## Goal
Create a simple local-only sidecar flow that starts from raw PDFs in `D:/_datefac/input/real_test` and produces an easy-to-open Excel preview.

This task is for local testing only.

## Required Behavior
- Scan all PDFs in `D:/_datefac/input/real_test`.
- Reuse the safest existing raw-PDF route available in the repo.
- Prefer existing lightweight extraction utilities over production pipeline changes.
- Produce a simple Excel preview even if some PDFs or pages fail.
- Do not crash the whole run because one PDF fails.
- Be conservative when routing rows:
  - clear metric + plausible value -> reviewed
  - ambiguous row -> needs review
  - obviously wrong or excluded row -> rejected or excluded

## Chosen Safe Route
- Use `pdfplumber_table_extractor.extract_tables_from_pdf(...)` as the existing lightweight raw-PDF table extraction entrypoint.
- Keep the new logic in `datefac/trust/` and `tools/` only.
- Do not modify production pipeline, parser, extraction, delivery, or official asset files.

## Inputs
- `D:/_datefac/input/real_test`

Expected PDFs:
- `H3_AP202606081823352620_1.pdf`
- `H3_AP202606081823352906_1.pdf`
- `H3_AP202606081823356439_1.pdf`

## Output Directory
- `D:/_datefac/output/real_test_full_flow_336a`

## Expected Artifacts
- `real_test_full_flow_336a_summary.json`
- `real_test_full_flow_336a_manifest.json`
- `real_test_full_flow_336a_qa.json`
- `real_test_full_flow_336a_report.md`
- `real_test_client_export_336a.xlsx`

## Workbook Sheets
1. `00_README`
2. `01_REVIEWED_CORE_METRICS`
3. `02_NEEDS_REVIEW`
4. `03_REJECTED_OR_EXCLUDED`
5. `04_SOURCE_TRACE`
6. `05_RUN_SUMMARY`

## User-Facing Sheet Rules
- Do not expose `dry_run_action` in customer sheets.
- Do not expose `preview_routing_bucket` in customer sheets.
- Do not expose `330K / 331 / 332` internal stage names in customer sheets.
- Do not claim client-ready.
- Do not claim production-ready.
- Do not claim 100% accuracy.
- Do not claim investment advice.

Use simple customer columns when possible:
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

## Target Metrics
Attempt to extract or surface the following metrics conservatively:
- `revenue / 营业收入`
- `net_profit / 归母净利润`
- `EPS`
- `PE`
- `PB`
- `ROE`
- `gross_margin / 毛利率`
- `net_margin / 净利率`
- `YoY / 同比`
- `rating / 投资评级` if easy
- `report_date / 报告日期` if easy
- `broker / 机构` if easy
- `stock_code / 股票代码` if easy
- `stock_name / 股票名称` if easy

## Implementation Scope
Create only:
- `docs/codex_tasks/336A_real_test_full_flow_from_pdf_folder.md`
- `datefac/trust/real_test_full_flow_336a.py`
- `datefac/trust/real_test_full_flow_336a_report.py`
- `tools/run_real_test_full_flow_336a.py`
- `tests/trust/test_real_test_full_flow_336a.py`

## Hard Boundaries
- Do not modify production pipeline, parser, extraction, or delivery files.
- Do not modify official assets.
- Do not modify existing output folders.
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
python -m py_compile datefac\trust\real_test_full_flow_336a.py datefac\trust\real_test_full_flow_336a_report.py tools\run_real_test_full_flow_336a.py tests\trust\test_real_test_full_flow_336a.py
python -m pytest tests\trust\test_real_test_full_flow_336a.py -q
python tools\run_real_test_full_flow_336a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\real_test_full_flow_336a
```

## Reporting
After the run, report in simple Chinese:
1. 找到了几个 PDF
2. 成功处理了几个 PDF
3. 每个 PDF 抽到了多少条指标
4. trusted / review / rejected 各多少
5. 最终 Excel 在哪里
6. 哪些 PDF 或页面失败了
7. 下一步用户应该打开哪个文件
