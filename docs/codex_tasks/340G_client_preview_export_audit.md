# 340G Client Preview Export Audit

## Goal

Audit the 340F client preview workbook and confirm that it is suitable for demo or client preview presentation while remaining not production-ready.

This task must not write back to any upstream workbook.
It must not modify production pipeline, parser, extraction, or delivery behavior.
It must not modify official assets.
It must not commit output artifacts.

## Inputs

- `D:/_datefac/output/client_preview_after_human_review_340f`
- `D:/_datefac/output/client_preview_after_human_review_340f/client_preview_after_human_review_340f.xlsx`

## Output Dir

- `D:/_datefac/output/client_preview_export_audit_340g`

## Output Files

- `client_preview_export_audit_340g.xlsx`
- `client_preview_export_audit_340g_summary.json`
- `client_preview_export_audit_340g_manifest.json`
- `client_preview_export_audit_340g_qa.json`
- `client_preview_export_audit_340g_report.md`
- `client_preview_export_audit_340g_no_write_back_proof.json`

## No-Write-Back Boundary

- Do not modify 337D workbook.
- Do not modify 338D workbook.
- Do not modify 340B workbook.
- Do not modify 340C workbook.
- Do not modify 340D workbook.
- Do not modify 340E workbook.
- Do not modify 340F workbook.
- Do not change production pipeline, parser, extraction, or delivery behavior.
- Do not modify official assets.
- Do not commit output artifacts.

## Workbook Sheets

1. `00_README`
2. `01_AUDIT_SUMMARY`
3. `02_CORE_METRIC_AUDIT`
4. `03_UNIT_AUDIT`
5. `04_DUPLICATE_AUDIT`
6. `05_SOURCE_TRACE_AUDIT`
7. `06_NEEDS_REVIEW_AUDIT`
8. `07_REJECTED_AUDIT`
9. `08_CLAIMS_AUDIT`
10. `09_NO_WRITE_BACK_PROOF`
11. `10_NEXT_STEP_RECOMMENDATION`

All sheet names must be `<= 31` characters.

## Audit Focus

1. 340F input workbook exists
2. 340F decision is `CLIENT_PREVIEW_AFTER_HUMAN_REVIEW_340F_READY`
3. core preview count is 34
4. confirmed count is 22
5. corrected count is 12
6. needs review count is 12
7. rejected count is 31
8. all core preview rows have `document / metric / year / value / unit / source_page / evidence`
9. corrected rows use corrected values
10. money metrics do not use `%`
11. percent metrics use `%`
12. EPS unit is `元`
13. PE unit is `倍`
14. there are no duplicate `document + metric + year` rows unless explicitly justified
15. rejected rows are not included in the core preview
16. needs review rows are not included in the core preview
17. no sheet name exceeds 31 characters
18. `client_ready` is not `true`
19. `production_ready` is not `true`
20. there is no investment advice claim
21. there is no write-back to the upstream workbook
22. `qa_fail_count = 0`

## Expected Summary

- `audited_core_metric_count = 34`
- `confirmed_count = 22`
- `corrected_count = 12`
- `needs_review_count = 12`
- `rejected_count = 31`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`
- `client_preview_audit_passed = true`
- `client_ready = false`
- `production_ready = false`
- `decision = CLIENT_PREVIEW_EXPORT_AUDIT_340G_READY`

## Files

- `docs/codex_tasks/340G_client_preview_export_audit.md`
- `datefac/trust/client_preview_export_audit_340g.py`
- `datefac/trust/client_preview_export_audit_340g_report.py`
- `tools/run_client_preview_export_audit_340g.py`
- `tests/trust/test_client_preview_export_audit_340g.py`

## Run

```powershell
python -m py_compile datefac\trust\client_preview_export_audit_340g.py datefac\trust\client_preview_export_audit_340g_report.py tools\run_client_preview_export_audit_340g.py tests\trust\test_client_preview_export_audit_340g.py

python -m pytest tests\trust\test_client_preview_export_audit_340g.py -q

python tools\run_client_preview_export_audit_340g.py --client-preview-340f-dir D:\_datefac\output\client_preview_after_human_review_340f --output-dir D:\_datefac\output\client_preview_export_audit_340g
```
