# 348N New Real Workbook Generalization Pilot Result

## Task ID

`348N New Real Workbook Generalization Pilot`

## Input-Pair Discovery

Discovered local candidate files in `D:\_datefac_agent\input`:

- `6862e6f3995d3dbfbed310b51601fb0a.pdf`
- `linyang_energy_pdf_extracted_testset (1).xlsx`
- previously tested pairs were also present, but were not reused

Pairing basis:

- PDF filename and Excel workbook contents both point to `林洋能源`
- Excel workbook contains a `源PDF` field referencing the same PDF filename
- no OCR or PDF re-extraction was used to establish the pair

## Selected PDF and Excel Pair

- PDF: `D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf`
- Excel: `D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx`

## Runner Command

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf --excel-path "D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348n_linyang_energy_testset
```

## Output Directory

`D:\_datefac_agent\output\agent_excel_intake_audit_348n_linyang_energy_testset`

## Manifest Metrics

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

## Clean-Data QA

Conclusion:

- clean data remained conservative in composition
- clean data was small relative to the workbook size
- clean data did not absorb narrative or unknown rows

## Review-Queue QA

Conclusion:

- review queue remained explainable but very large
- the workbook is dominated by review-required rows
- this is materially noisier than the three previously validated real workbooks

## Unknown-Row QA

Conclusion:

- `unknown_row_count = 367` is a major spike compared with previous samples
- the current pipeline does not generalize cleanly to this input
- this looks like a real generalization gap rather than a clean-data boundary issue

## Unit/Period/Valuation Signal QA

Conclusion:

- `unit_issue_count = 9`
- `period_issue_count = 0`
- `valuation_issue_count = 0`
- the remaining signals look mostly like review burden rather than clear blocking defects
- top issue codes in review queue are `percentage_unit_missing` and `weak_evidence`

## Readiness Gate QA

Conclusion:

- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`

## External Call QA

Conclusion:

- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

## Baseline Validation

- `python -m pytest tests\agent -q`
- result: `38 passed`

## Decision

`348N_CONFIRMED_NEW_REAL_WORKBOOK_NEEDS_TARGETED_REFINEMENT`

## Recommended Next Task

`targeted unknown-row / workbook-shape refinement for 林洋能源 testset, or stop if this testset is intentionally out-of-scope`

