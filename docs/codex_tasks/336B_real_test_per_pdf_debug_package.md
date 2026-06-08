# 336B Real Test Per-PDF Debug Package

## Goal
Create a per-PDF debug package for the real-test PDFs in `D:/_datefac/input/real_test`.

This task is debug-only, local-only, and sidecar-only.

## Context
`336A` already created a combined preview workbook from the same raw PDF folder.
That combined workbook is useful as a smoke test, but it is not detailed enough for debugging weak extraction quality.

## Required Outcome
Generate one output subfolder per PDF so a user can inspect:
- which pages had text
- which tables and rows were seen
- which metric candidates were produced
- why candidates were routed to reviewed / needs_review / rejected

## Inputs
- `D:/_datefac/input/real_test`

## Output Directory
- `D:/_datefac/output/real_test_debug_336b`

## Expected Output Structure
`D:/_datefac/output/real_test_debug_336b`

- `00_batch_summary.xlsx`
- `00_batch_summary.json`
- `00_batch_report.md`
- `<pdf_stem>/`
  - `document_summary.json`
  - `extracted_page_text.xlsx`
  - `extracted_tables.xlsx`
  - `metric_candidates.xlsx`
  - `routing_preview.xlsx`
  - `client_preview.xlsx`
  - `debug_report.md`

## Per-PDF Requirements

### 1. document_summary.json
Include:
- pdf filename
- file size
- page count
- extracted page count
- detected table count
- candidate count
- reviewed count
- needs_review count
- rejected count
- likely_failure_reason if candidate count is 0

### 2. extracted_page_text.xlsx
Columns:
- `page_no`
- `text_excerpt`
- `full_text_or_long_excerpt`
- `contains_financial_keywords`
- `contains_forecast_years`

### 3. extracted_tables.xlsx
Columns:
- `page_no`
- `table_index`
- `row_index`
- `raw_row_text`
- `normalized_row_text`
- `detected_metric_keywords`
- `detected_years`
- `detected_numbers`

### 4. metric_candidates.xlsx
Columns:
- `candidate_id`
- `page_no`
- `table_index`
- `row_index`
- `metric`
- `metric_display_zh`
- `year`
- `value`
- `unit`
- `evidence`
- `extraction_reason`

### 5. routing_preview.xlsx
Columns:
- `candidate_id`
- `route`
- `route_reason`
- `risk_flags`
- `evidence`

### 6. client_preview.xlsx
Use the same simple sidecar preview style as `336A`, but only for one PDF.

### 7. debug_report.md
Explain:
- what was found
- what failed
- why candidate count is 0 if applicable
- which pages are most likely to contain financial forecast tables

## Batch Summary Requirements
Create `00_batch_summary.xlsx` with one row per PDF:
- `document`
- `page_count`
- `table_count`
- `candidate_count`
- `reviewed_count`
- `needs_review_count`
- `rejected_count`
- `likely_failure_reason`
- `output_folder`
- `recommended_next_action`

## Important Debug Heuristics
Scan page text for financial keywords, including:
- revenue / 营业收入
- net profit / 归母净利润 / 净利润
- EPS / 每股收益
- PE / P/E
- PB / P/B
- ROE
- gross margin / 毛利率
- net margin / 净利率
- forecast / 预测 / 财务数据 / 财务摘要

Scan for forecast years:
- `2024A`
- `2025A`
- `2026E`
- `2027E`
- `2028E`
- `2026`
- `2027`
- `2028`

If a PDF has financial keywords in page text but `candidate_count = 0`, mark:
- `TABLE_EXTRACTION_OR_ROW_MAPPING_MISSED_FINANCIAL_PAGE`

If no page text is extracted, mark:
- `PDF_TEXT_EXTRACTION_FAILED_OR_SCANNED_PDF`

If tables exist but no candidate rows, mark:
- `TABLES_FOUND_BUT_METRIC_RULES_TOO_WEAK`

## Reuse Strategy
- Reuse `336A` logic where safe.
- Do not rewrite `336A` destructively.
- Additional helper functions may be added only in the new `336B` sidecar module.

## Files To Create
- `docs/codex_tasks/336B_real_test_per_pdf_debug_package.md`
- `datefac/trust/real_test_per_pdf_debug_336b.py`
- `datefac/trust/real_test_per_pdf_debug_336b_report.py`
- `tools/run_real_test_per_pdf_debug_336b.py`
- `tests/trust/test_real_test_per_pdf_debug_336b.py`

## Boundaries
- Do not modify production pipeline.
- Do not modify parser / extraction / delivery behavior.
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
python -m py_compile datefac\trust\real_test_per_pdf_debug_336b.py datefac\trust\real_test_per_pdf_debug_336b_report.py tools\run_real_test_per_pdf_debug_336b.py tests\trust\test_real_test_per_pdf_debug_336b.py
python -m pytest tests\trust\test_real_test_per_pdf_debug_336b.py -q
python tools\run_real_test_per_pdf_debug_336b.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\real_test_debug_336b
```

## Final Reporting
After the run, report in simple Chinese:
1. 每个 PDF 的输出文件夹在哪里
2. 每个 PDF 多少页
3. 每个 PDF 检测到多少张表
4. 每个 PDF 抽到多少候选
5. 哪个 PDF 是 0，为什么可能是 0
6. 哪些页面最可能包含财务预测表
7. 下一步应优先修哪个 PDF
