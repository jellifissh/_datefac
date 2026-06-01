# 321D MinerU Table Body Ingestion

## task_title
Ingest MinerU table_body / markdown / html outputs into DateFac sandbox MetricCandidate and delivery flow

## project
D:\_datefac

## current_context
321C2 source-aware router revision has completed and pushed to `main`.

Latest 321C2 decision:
- router_revision_decision: `SOURCE_AWARE_ROUTER_READY_FOR_321D_MINERU_BODY_INGESTION_FIRST`
- revised_mineru_table_body_structuring_count: 131
- revised_mineru_markdown_direct_count: 38
- revised_pure_vlm_image_only_count: 0
- revised_ppstructure_fallback_count: 0
- revised_manual_review_required_count: 2
- revised_skip_non_core_count: 43
- revised_unsupported_count: 2
- revised_route_total_count: 216
- revised_unique_table_asset_count: 216

The user inspected `D:\_datefac\output\source_aware_router_revision_321c2\source_aware_router_revision_321c2.xlsx` and reported:
- `mineru_table_body_worklist` row count: 131
- top 20 rows look practically relevant after using `effective_role_category / table_title_final`, even though `table_role_guess` has noisy values such as `DISCLAIMER_OR_LEGAL` and `RATING_STANDARD`.
- top 20 effective categories:
  - `FINANCIAL_FORECAST_VALUATION`: 10
  - `BALANCE_SHEET`: 8
  - `INCOME_STATEMENT`: 1
  - `CASH_FLOW_STATEMENT`: 1
- Therefore 321D may proceed, but must use effective route/category/title fields rather than trusting `table_role_guess` blindly.

Previous findings:
- Pure VLM image-only route is usable but still partial after 321B2:
  - calibrated_trusted_rate: 0.3361963190184049
  - unknown_metric_code_count: 292
  - unit_unknown_count: 231
  - calibration_decision: `PURE_VLM_CALIBRATION_PARTIAL_NEEDS_MORE_PROMPT_OR_ALIAS_WORK`
- Earlier strong VLM results were partly MinerU-assisted and therefore should not be mixed with pure VLM evidence.
- 321D should now test the low-cost MinerU table-body route first.

## goal
Implement 321D sandbox ingestion for `MINERU_TABLE_BODY_STRUCTURING`.

Pipeline:

```text
321C2 router worklist
+ existing MinerU outputs under E:\mineru_lab\output_new
-> extract table_body / html table / markdown table / content_list table text
-> normalize into Unified Table JSON
-> map into DateFac MetricCandidate
-> trusted / review_required / rejected preview
-> sandbox delivery bundle
-> benchmark against pure VLM 321B2 and PPStructure 320G
```

This stage should answer:
- Can MinerU table_body / markdown / html be directly structured into useful financial metrics?
- How many top worklist tables generate candidates and trusted rows?
- Is this route stronger/cheaper than pure VLM and PPStructure for the current sample?
- Which table categories need VLM fallback?

This is sandbox-only. Do not touch production delivery files.

## non_goals
Do not do these in 321D:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not use pure VLM outputs to repair MinerU table body outputs.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/321d_mineru_table_body_ingestion.md`
- `datefac/mineru_body/__init__.py`
- `datefac/mineru_body/mineru_table_body_reader.py`
- `datefac/mineru_body/mineru_table_normalizer.py`
- `datefac/mineru_body/mineru_body_candidate_mapper.py`
- `datefac/mineru_body/mineru_body_delivery_builder.py`
- `datefac/mineru_body/mineru_body_benchmark.py`
- `tools/run_mineru_table_body_ingestion_321d.py`

Potentially reuse/read existing modules:
- `datefac/parser/mineru_output_reader.py`
- `datefac/domain/metric_candidate.py`
- `datefac/vlm/vlm_candidate_mapper.py` only for shared alias logic if safe and clean
- `datefac/delivery/sandbox_bundle_builder.py` only if it already supports generic candidates

Keep MinerU-body logic separate from VLM and PPStructure modules. Do not dump everything into one script, because future-you does not deserve that punishment.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\source_aware_router_revision_321c2
E:\mineru_lab\output_new
```

Optional comparison inputs:

```powershell
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_mineru_table_body_ingestion_321d.py ^
  --router-dir D:\_datefac\output\source_aware_router_revision_321c2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --max-tables 20
```

Default should be `--max-tables 20` for phase 1. Allow `--max-tables 131` later, but do not default to full 131 yet.

If router dir is missing, produce blocked output:
- `BLOCKED_MISSING_321C2_ROUTER_DIR`

If MinerU output root is missing, produce blocked output:
- `BLOCKED_MISSING_MINERU_OUTPUT_ROOT`

Do not crash.

## worklist_selection
Read from 321C2 output workbook:

```text
source_aware_router_revision_321c2.xlsx
```

Required sheets to try:
- `mineru_table_body_worklist`
- `table_route_preview_revised`
- `revised_router_policy`

Selection rules:
1. Prefer rows with route `MINERU_TABLE_BODY_STRUCTURING`.
2. Use `effective_role_category`, `table_title_final`, `route_reason`, or equivalent if available.
3. Do not rely only on `table_role_guess`, because inspection showed it may label useful tables as `DISCLAIMER_OR_LEGAL` or `RATING_STANDARD`.
4. Prioritize:
   - `FINANCIAL_FORECAST_VALUATION`
   - `BALANCE_SHEET`
   - `INCOME_STATEMENT`
   - `CASH_FLOW_STATEMENT`
   - key financial / valuation metric tables
5. Diversify across source reports when possible.
6. Exclude obvious non-core tables unless the effective category says they are useful.
7. Keep `--max-tables` cap.

Output selected worklist as `selected_worklist` sheet.

## MinerU table body extraction requirements
For each selected table asset:

Inputs may include, depending on MinerU output:
- `*_content_list.json`
- `*_content_list_v2.json`
- markdown `.md`
- html fragments/tables
- table image path
- caption / footnote / nearby text
- bbox / page_idx

Implement robust extraction attempts:
1. Locate the report directory under `E:\mineru_lab\output_new\<report>`.
2. Read content_list JSON files if present.
3. Match table by `table_asset_id`, image_path, caption, bbox, page_idx, or nearby text where possible.
4. Extract table body from fields such as:
   - `table_body`
   - `html`
   - `table_html`
   - `text`
   - markdown table block
   - any known MinerU table item content
5. Preserve provenance for all extraction attempts.
6. If exact table match fails, mark table as `TABLE_BODY_NOT_FOUND`, not crash.

Do not run OCR or external parsers.

## Unified Table JSON schema
Normalize extracted table body into a common structure:

```json
{
  "table_id": "",
  "source_report_name": "",
  "table_asset_id": "",
  "table_title": "",
  "unit": "",
  "currency": null,
  "columns": ["2024A", "2025A", "2026E"],
  "rows": [
    {
      "row_index": 1,
      "metric_name_raw": "营业收入",
      "metric_name_cn": "营业收入",
      "values": [
        {
          "column": "2024A",
          "raw_value": "1234",
          "normalized_value": 1234
        }
      ],
      "source_row_text": "",
      "warnings": []
    }
  ],
  "provenance": {}
}
```

Support tables parsed from:
- html table rows/cells;
- markdown tables;
- row text table_body;
- loose delimited text when safe.

## mapping_requirements
Map normalized tables into MetricCandidate records.

Reuse safe alias mappings from VLM 321B where useful, but keep source stage distinct:
- `source_stage = mineru_table_body_321d`
- `recognition_source = MINERU_TABLE_BODY_STRUCTURING`

Metric families to support:
- valuation
- profitability
- income_statement
- balance_sheet
- cash_flow
- growth
- margin
- other

Use the same conservative trust philosophy:
- trusted only when metric/year/value/unit/provenance are credible;
- review when unit/label/schema/conflict is uncertain;
- rejected only for clear noise or impossible rows.

## unit_and_year_rules
Use table title, caption, header, and row labels.

Rules:
- `百万元`, `亿元`, `万元`, `元`, `%` should be detected.
- table-level monetary unit applies to statement rows unless metric is ratio/percentage/per-share.
- valuation tables are mixed-unit; row-level unit or metric implication has priority.
- years may include `2024`, `2024A`, `2025E`, `2026E`, etc.
- do not turn non-year columns into year candidates.

## diagnostics_required
Add diagnostics sheets:

### `table_body_extraction_audit`
Columns:
- selected_rank
- source_report_name
- table_asset_id
- image_path
- match_status
- matched_by
- content_source_file
- content_item_index
- has_table_body
- has_html
- has_markdown_table
- extracted_row_count
- extracted_column_count
- warnings

### `normalization_audit`
Columns:
- table_id
- raw_table_title
- normalized_table_title
- raw_columns
- normalized_columns
- unit_detected
- unit_source
- row_count
- value_cell_count
- warnings

### `mapping_diagnostics`
Columns:
- table_id
- row_index
- raw_metric_name
- metric_code
- metric_family
- year
- raw_value
- normalized_value
- unit
- split_decision
- risk_tags
- reason

### `mineru_vs_vlm_ppstructure_summary`
Compare against optional pure VLM 321B2 and PPStructure 320G:
- route_name
- candidate_count
- trusted_count
- review_required_count
- trusted_rate
- unit_unknown_count
- unknown_metric_count
- conflict_count
- qa_fail_count
- notes

## output_contract
Write to:

```powershell
D:\_datefac\output\mineru_table_body_ingestion_321d
```

Required files:

1. `mineru_table_body_ingestion_321d.xlsx`

Sheets:
- `summary`
- `selected_worklist`
- `table_body_extraction_audit`
- `unified_tables`
- `normalized_rows`
- `metric_candidates_all`
- `trusted_preview`
- `review_required_preview`
- `rejected_preview`
- `per_table_summary`
- `metric_coverage`
- `unit_year_context_summary`
- `risk_tag_counts`
- `provenance_coverage`
- `normalization_audit`
- `mapping_diagnostics`
- `mineru_vs_vlm_ppstructure_summary`
- `qa_checks`
- `known_limitations`

2. `mineru_table_body_ingestion_321d_summary.json`

3. `mineru_table_body_ingestion_321d_report.md`

Optional:
- `unified_tables.jsonl`
- `metric_candidates_all.jsonl`
- `trusted_preview.jsonl`
- `review_required_preview.jsonl`

## summary_metrics
Include:
- selected_table_count
- attempted_table_count
- table_body_found_count
- table_body_missing_count
- parsed_table_count
- unified_table_count
- table_with_candidates_count
- table_with_trusted_count
- total_candidate_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- unit_unknown_count
- year_invalid_count
- unknown_metric_code_count
- conflict_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- pure_vlm_calibrated_trusted_rate
- ppstructure_trusted_rate
- mineru_body_ingestion_decision

Decision rule:
- If qa_fail_count > 0:
  `MINERU_BODY_INGESTION_BLOCKED_BY_QA_FAILURE`
- If table_body_found_count < attempted_table_count * 0.5:
  `MINERU_BODY_INGESTION_BLOCKED_LOW_TABLE_BODY_COVERAGE`
- If parsed_table_count >= 10, table_with_trusted_count >= 6, trusted_rate >= 0.45, provenance_complete_rate >= 0.95:
  `MINERU_BODY_INGESTION_READY_FOR_321E_ROUTE_COMPARISON`
- If parsed_table_count >= 5 and table_with_candidates_count >= 5:
  `MINERU_BODY_INGESTION_PARTIAL_NEEDS_NORMALIZATION_CALIBRATION`
- Otherwise:
  `MINERU_BODY_INGESTION_NOT_READY`

## qa_checks
Required checks:
- selected worklist loaded from 321C2;
- no production files modified;
- no E-drive files modified;
- no MinerU/PPStructure/VLM commands executed;
- no non-core table silently trusted;
- no invalid year in trusted output;
- no unknown metric code in trusted output;
- provenance complete for trusted output;
- every candidate has source table id and source stage;
- Chinese text preserved.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call VLM/API/cloud/network.
4. Do not modify E-drive input/output folders.
5. Do not modify production delivery files.
6. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
7. Do not modify `data/mapping/formal_scope_rules.json`.
8. Do not run `factory_core.py`.
9. Do not rewrite old Stage7 pipeline.
10. Do not commit `output/` artifacts.
11. Do not commit anything under `E:\mineru_lab`.
12. Do not commit unrelated 320G2 experimental files or temp scripts.
13. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/mineru_body/mineru_table_body_reader.py
python -m py_compile datefac/mineru_body/mineru_table_normalizer.py
python -m py_compile datefac/mineru_body/mineru_body_candidate_mapper.py
python -m py_compile datefac/mineru_body/mineru_body_delivery_builder.py
python -m py_compile datefac/mineru_body/mineru_body_benchmark.py
python -m py_compile tools/run_mineru_table_body_ingestion_321d.py
```

Then run:

```powershell
python tools/run_mineru_table_body_ingestion_321d.py ^
  --router-dir D:\_datefac\output\source_aware_router_revision_321c2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --max-tables 20
```

If PowerShell one-line form is safer, use it and report exact command.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321D code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Ingest MinerU table body tables`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- selected_table_count
- attempted_table_count
- table_body_found_count
- table_body_missing_count
- parsed_table_count
- unified_table_count
- table_with_candidates_count
- table_with_trusted_count
- total_candidate_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- unit_unknown_count
- year_invalid_count
- unknown_metric_code_count
- conflict_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- pure_vlm_calibrated_trusted_rate
- ppstructure_trusted_rate
- mineru_body_ingestion_decision
- top risk tags
- skipped/untracked files
