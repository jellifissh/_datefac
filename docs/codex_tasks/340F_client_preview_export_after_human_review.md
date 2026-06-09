# 340F Client Preview Export After Human Review

## Goal

Create a human-reviewed client preview workbook from the 340E post-human-review sidecar result.
This is a preview-only deliverable.

It must not write back to any upstream workbook.
It must not change production pipeline, parser, extraction, or delivery behavior.
It must not modify official assets.
It is not production-ready and it is not investment advice.

## Inputs

- `D:/_datefac/output/post_human_review_sidecar_result_340e`
- `D:/_datefac/output/post_human_review_sidecar_result_340e/post_human_review_sidecar_result_340e.xlsx`

## Output Dir

- `D:/_datefac/output/client_preview_after_human_review_340f`

## Output Files

- `client_preview_after_human_review_340f.xlsx`
- `client_preview_after_human_review_340f_summary.json`
- `client_preview_after_human_review_340f_manifest.json`
- `client_preview_after_human_review_340f_qa.json`
- `client_preview_after_human_review_340f_no_write_back_proof.json`
- `client_preview_after_human_review_340f_report.md`

## No-Write-Back Boundary

- Do not modify 337D workbook.
- Do not modify 338D workbook.
- Do not modify 340B workbook.
- Do not modify 340C workbook.
- Do not modify 340D workbook.
- Do not modify 340E workbook.
- Do not change production pipeline, parser, extraction, or delivery behavior.
- Do not modify official assets.
- Do not commit output artifacts.

## Core Rules

1. Read the reviewed sidecar result from 340E.
2. Merge `reviewed_after_human` and `reviewed_after_human_corrected` into the core client preview.
3. Corrected rows must use `corrected_metric / corrected_year / corrected_value / corrected_unit` as final display values.
4. Confirmed rows must use the original confirmed values from 340E.
5. `rejected_after_human` rows must not enter the core preview.
6. `needs_review_after_human` rows must not enter the core preview.
7. Core preview rows must retain `document / source_page / evidence / reviewer_notes / provenance`.
8. Do not generate investment advice.
9. Do not claim `client_ready` or `production_ready`.
10. All workbook sheet names must be `<= 31` characters.

## Workbook Sheets

1. `00_README`
2. `01_CLIENT_PREVIEW_CORE_METRICS`
3. `02_CLIENT_PREVIEW_CORRECTED`
4. `03_CLIENT_PREVIEW_NEEDS_REVIEW`
5. `04_CLIENT_PREVIEW_REJECTED`
6. `05_SOURCE_TRACE`
7. `06_QUALITY_AND_LIMITATIONS`
8. `07_SUMMARY`
9. `08_NO_WRITE_BACK_PROOF`
10. `09_NEXT_STEP_RECOMMENDATION`

## Suggested Core Preview Fields

- `preview_row_id`
- `document`
- `company_or_document_hint`
- `metric`
- `metric_display_name`
- `year`
- `value`
- `unit`
- `human_review_status`
- `source_page`
- `evidence`
- `reviewer_notes`
- `source_route`
- `risk_flags`

## Metric Display Name Mapping

- `revenue -> 营业收入`
- `net_profit -> 净利润 / 归母净利润`
- `EPS -> 每股收益`
- `PE -> 市盈率`
- `ROE -> 净资产收益率`
- `revenue_yoy -> 营业收入同比`
- `net_profit_yoy -> 归母净利润同比`
- `net_margin -> 净利率`

## README Requirements

README must clearly state:

- This is a human-reviewed client preview.
- Not production-ready.
- Not investment advice.
- Source evidence is provided for traceability.
- Rows marked `needs_review` or `rejected` are not included in the core preview table.
- AI decisions were not directly written back; human review and deterministic validation were used.

## Expected Summary

- `total_340e_input_rows = 77`
- `client_preview_core_metric_count = 34`
- `client_preview_confirmed_count = 22`
- `client_preview_corrected_count = 12`
- `needs_review_after_human_count = 12`
- `rejected_after_human_count = 31`
- `source_trace_count = 34`
- `qa_fail_count = 0`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `decision = CLIENT_PREVIEW_AFTER_HUMAN_REVIEW_340F_READY`

## QA Requirements

- 340E input workbook exists
- 340E decision is ready
- core preview count is 34
- confirmed count is 22
- corrected count is 12
- needs review count is 12
- rejected count is 31
- all core preview rows have `document / metric / year / value / unit / evidence`
- corrected rows use corrected fields
- PE corrected unit is `倍`
- EPS unit is `元`
- money metrics do not use `%`
- percent metrics use `%`
- rejected rows are not included in the core preview
- needs review rows are not included in the core preview
- no sheet name exceeds 31 characters
- no write-back to upstream workbook
- no client-ready claim
- no production-ready claim
- `qa_fail_count = 0`

## Files

- `docs/codex_tasks/340F_client_preview_export_after_human_review.md`
- `datefac/trust/client_preview_export_after_human_review_340f.py`
- `datefac/trust/client_preview_export_after_human_review_340f_report.py`
- `tools/run_client_preview_export_after_human_review_340f.py`
- `tests/trust/test_client_preview_export_after_human_review_340f.py`

## Run

```powershell
python -m py_compile datefac\trust\client_preview_export_after_human_review_340f.py datefac\trust\client_preview_export_after_human_review_340f_report.py tools\run_client_preview_export_after_human_review_340f.py tests\trust\test_client_preview_export_after_human_review_340f.py

python -m pytest tests\trust\test_client_preview_export_after_human_review_340f.py -q

python tools\run_client_preview_export_after_human_review_340f.py --post-human-review-340e-dir D:\_datefac\output\post_human_review_sidecar_result_340e --output-dir D:\_datefac\output\client_preview_after_human_review_340f
```
