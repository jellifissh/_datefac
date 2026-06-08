# 337D Reviewed Strictness, Year Alignment, and Suspicious Row QA

## Goal
- Reuse the 337C local preview output and apply stricter reviewed QA.
- Fix confident year/value alignment issues.
- Prevent percentage-as-amount mistakes.
- Enforce reviewed unit strictness.
- Deduplicate reviewed customer rows.
- Add targeted 356439 review tightening.
- Produce a suspicious-row audit sheet and route-change trace.

## Boundaries
- Sidecar/local preview only.
- Do not rerun MinerU unless absolutely necessary.
- Do not modify 337A/337B/337C outputs in place.
- Do not modify production pipeline, parser, extraction, delivery behavior, official assets, or protected dirty files.
- Do not commit output artifacts.

## Inputs
- `D:/_datefac/output/core_financial_context_repair_337c`
- `D:/_datefac/output/core_financial_context_repair_337c/real_test_mineru_client_export_337c.xlsx`
- `D:/_datefac/output/mineru_candidate_precision_337b`
- `D:/_datefac/output/mineru_real_test_337a`
- `D:/_datefac/input/real_test`

## Output Dir
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`

## Expected Artifacts
- `reviewed_strictness_year_alignment_337d_summary.json`
- `reviewed_strictness_year_alignment_337d_manifest.json`
- `reviewed_strictness_year_alignment_337d_qa.json`
- `reviewed_strictness_year_alignment_337d_no_apply_proof.json`
- `reviewed_strictness_year_alignment_337d_report.md`
- `reviewed_strictness_year_alignment_337d_before_after.xlsx`
- `real_test_mineru_client_export_337d.xlsx`

## Core Repairs

### A. Year/value alignment QA and repair
- Detect reviewed rows where the same evidence row produced multiple values but all rows were assigned to the same year.
- Use table header years from table preview/context when the value count and year count align confidently.
- If confident, repair the year assignment.
- If not confident, downgrade the row to `needs_review`.
- Report:
  - `year_alignment_repaired_count`
  - `year_alignment_downgraded_count`

### B. Percentage-as-amount guard
- If metric is `revenue` or `net_profit` and value contains `%` or unit is `%`, it must not remain reviewed as an amount metric.
- If the evidence row clearly represents growth/YoY, remap to `revenue_yoy` or `net_profit_yoy`.
- Otherwise downgrade to `needs_review`.
- Report:
  - `percent_amount_guard_downgraded_count`
  - `percent_amount_guard_remapped_count`

### C. Unit strictness
- Reviewed rows must have a valid unit.
- Accepted implicit units:
  - `PE` / `PB` => `倍`
  - `EPS` => `元`
  - `ROE` / `gross_margin` / `net_margin` / `revenue_yoy` / `net_profit_yoy` => `%`
- `revenue` / `net_profit` must have a monetary unit.
- If a valid unit can be filled confidently, fill it.
- Otherwise downgrade from reviewed to `needs_review`.
- Report:
  - `unit_strictness_downgraded_count`
  - `unit_strictness_filled_count`

### D. Reviewed deduplication
- Deduplicate reviewed customer rows by:
  - `document`
  - `metric`
  - `year`
  - normalized `value`
  - normalized `unit`
- Source priority:
  1. `CORE_FINANCIAL_SUMMARY`
  2. `PROFIT_FORECAST_VALUATION`
  3. `FINANCIAL_STATEMENT_DETAIL`
  4. others
- Keep the best reviewed row and exclude duplicates from the reviewed sheet.
- Leave `duplicate_of` trace in source trace.
- Report:
  - `reviewed_duplicate_removed_count`

### E. 356439 targeted audit
- For `H3_AP202606081823356439_1.pdf`:
  - report reviewed rows before and after
  - downgrade suspicious year/value alignment rows
  - downgrade percentage-as-amount rows that cannot be safely remapped
  - keep only clear core forecast / valuation / statement rows
- Report:
  - `reviewed_356439_before_count`
  - `reviewed_356439_after_count`
  - `reviewed_356439_downgraded_count`

### F. Suspicious reviewed audit sheet
- Include rows that were reviewed in 337C but flagged by 337D.
- Columns:
  - `candidate_id`
  - `document`
  - `metric`
  - `year`
  - `value`
  - `unit`
  - `source_page`
  - `evidence`
  - `suspicious_reason`
  - `337d_action`

## Final Workbook Sheets
- `00_README`
- `01_REVIEWED_CORE_METRICS`
- `02_NEEDS_REVIEW`
- `03_REJECTED_OR_EXCLUDED`
- `04_SOURCE_TRACE`
- `05_DOCUMENT_SUMMARY`
- `06_TABLE_CLASSIFICATION_SUMMARY`
- `07_CONTEXT_REPAIR_SUMMARY`
- `08_SUSPICIOUS_REVIEWED_AUDIT`
- `09_ROUTE_CHANGE_TRACE`

## QA Requirements
- Input 337C workbook exists.
- 3 PDFs are represented.
- Reviewed count after 337D is `<=` reviewed count after 337C.
- No reviewed `revenue` / `net_profit` row has unit `%`.
- No reviewed `revenue` / `net_profit` row has value containing `%`.
- No reviewed `revenue` / `net_profit` row has empty unit.
- No duplicate reviewed rows remain by `document/metric/year/value/unit`.
- 356439 reviewed count after 337D is `<=` 337C count.
- Rows downgraded from reviewed appear in route change trace.
- `client_ready = false`
- `production_ready = false`
- Official assets remain unchanged.
- Protected dirty files remain unstaged.

## Files To Create
- `docs/codex_tasks/337D_reviewed_strictness_year_alignment_qa.md`
- `datefac/trust/reviewed_strictness_year_alignment_337d.py`
- `datefac/trust/reviewed_strictness_year_alignment_337d_report.py`
- `tools/run_reviewed_strictness_year_alignment_337d.py`
- `tests/trust/test_reviewed_strictness_year_alignment_337d.py`

## Run
```powershell
python -m py_compile datefac\trust\reviewed_strictness_year_alignment_337d.py datefac\trust\reviewed_strictness_year_alignment_337d_report.py tools\run_reviewed_strictness_year_alignment_337d.py tests\trust\test_reviewed_strictness_year_alignment_337d.py

python -m pytest tests\trust\test_reviewed_strictness_year_alignment_337d.py -q

python tools\run_reviewed_strictness_year_alignment_337d.py --context-repair-337c-dir D:\_datefac\output\core_financial_context_repair_337c --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d
```

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
