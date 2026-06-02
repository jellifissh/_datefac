# 321E3 StructEqTable Output Audit

## task_title
Audit StructEqTable / StructTable-InternVL2 outputs for the 321E table extraction benchmark

## project
D:\_datefac

## current_context
StructEqTable / StructTable-InternVL2 has been installed and batch-run locally on the fixed 321E image benchmark.

Tool repo:

```powershell
E:\mineru_lab\StructEqTable-Deploy-main\StructEqTable-Deploy-main
```

Fixed benchmark input images:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
```

StructEqTable output root:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2
```

Observed batch run result from terminal:
- 10 images processed.
- 10/10 status ok after rerun.
- Each image folder should contain:
  - `raw_response_markdown_utf8.txt`
  - `table_output_markdown.md`
  - `table_output_from_markdown.xlsx`
  - `table_output_from_markdown.csv`
  - `run_meta.txt`
- Batch summary files should exist:
  - `structtable_intervl2_batch_summary.xlsx`
  - `structtable_intervl2_batch_summary.csv`

Observed early manual inspection:
- StructEqTable appears stronger than Docling on table reconstruction for regular financial table images.
- It preserves row/column structure and numeric cells well in many cases.
- It may still have quality issues:
  - missing one row;
  - missing one or more Chinese characters in labels;
  - some table titles missing;
  - some complex tables may have weak/empty title;
  - Markdown output is preferred because HTML output may be truncated on long tables.

Prior baselines:
- Docling 321E1 audit decision: `DOCLING_READY_FOR_321E_TOOL_BAKEOFF`
- Docling 321E2 mapping decision: `DOCLING_MAPPING_PARTIAL_INCLUDE_IN_BAKEOFF`
- Docling trusted_rate: about `0.3068`
- MinerU body 321D trusted_rate: about `0.3833`
- Pure VLM 321B2 trusted_rate: about `0.3362`
- PPStructure 320G trusted_rate: about `0.0719`

Engineering interpretation:
- StructEqTable is now the strongest-looking table-image reconstruction candidate by manual inspection.
- But it must be audited before mapping or integration.
- Do not directly integrate it into production.

## goal
Implement a sandbox-only StructEqTable output audit for 321E3.

321E3 should answer:
1. Did StructEqTable generate usable outputs for all 10 benchmark images?
2. Are Markdown/XLSX/CSV files present and parseable for every image?
3. Are year columns detected correctly?
4. Are Chinese row labels preserved or corrupted/missing?
5. Are numeric cells parseable?
6. Are row/column counts plausible compared with the model-produced summary?
7. Which tables require manual review due suspected missing rows, label truncation, empty titles, or schema irregularities?
8. Is StructEqTable ready for 321E4 full bakeoff against MinerU body, Docling, pure VLM, and PPStructure?

This stage is table extraction audit only. It should not do DateFac MetricCandidate mapping yet.

## non_goals
Do not do these in 321E3:
- Do not run StructEqTable again.
- Do not run Docling.
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not modify E:\mineru_lab.
- Do not modify production delivery files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not continue 321D2 normalizer expansion.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/table_bakeoff/structtable_output_reader.py`
- `datefac/table_bakeoff/structtable_table_normalizer.py`
- `datefac/table_bakeoff/structtable_output_audit.py`
- `tools/run_structtable_output_audit_321e3.py`
- `docs/codex_tasks/321e3_structtable_output_audit.md`

Reuse existing table_bakeoff utilities only if safe.
Do not modify MinerU/VLM/PPStructure production or old Stage7 modules.

## input_contract
Primary inputs:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2
```

Optional comparison inputs:

```powershell
D:\_datefac\output\docling_output_audit_321e1
D:\_datefac\output\docling_unified_mapping_321e2
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_structtable_output_audit_321e3.py ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --structtable-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2 ^
  --docling-audit-dir D:\_datefac\output\docling_output_audit_321e1 ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\structtable_output_audit_321e3
```

If optional comparison dirs are missing, continue with warnings.
If primary input/output dirs are missing, write blocked summary instead of crashing:
- `BLOCKED_MISSING_INPUT_IMAGE_DIR`
- `BLOCKED_MISSING_STRUCTTABLE_OUTPUT_DIR`

## reader_requirements
The reader should discover per-image folders under `--structtable-output-dir`.

Expected files per folder:
- `raw_response_markdown_utf8.txt`
- `table_output_markdown.md`
- `table_output_from_markdown.xlsx`
- `table_output_from_markdown.csv`
- `run_meta.txt`
- optional `error.txt`

Batch summary files may also exist at root:
- `structtable_intervl2_batch_summary.xlsx`
- `structtable_intervl2_batch_summary.csv`

Reader should:
1. associate each input image with one output folder by stem;
2. parse `run_meta.txt` when present;
3. parse Markdown table when present;
4. parse CSV/XLSX when present;
5. prefer Markdown/CSV over XLSX for audit text preservation;
6. preserve raw output path and provenance;
7. never modify E-drive files;
8. capture parse failures as warnings, not crashes.

## normalized_table_schema
Normalize each StructEqTable output into:

```json
{
  "tool": "structtable_intervl2",
  "recognition_source": "STRUCTTABLE_MARKDOWN",
  "image_name": "",
  "table_id": "",
  "table_title": "",
  "columns": [],
  "rows": [
    {
      "row_index": 0,
      "label": "",
      "values": [],
      "warnings": []
    }
  ],
  "cells": [
    {
      "row_index": 0,
      "col_index": 0,
      "text": "",
      "cell_type_guess": "label|year|numeric|percent|empty|unknown"
    }
  ],
  "provenance": {},
  "warnings": []
}
```

Do not map to MetricCandidate in 321E3.

## audit_metrics
Compute per image/table:
- output_folder_exists
- raw_response_exists
- markdown_exists
- xlsx_exists
- csv_exists
- error_exists
- raw_response_has_markdown_marker
- raw_response_timeout_warning_count
- parse_status
- table_title
- row_count
- col_count
- detected_year_columns
- year_column_count
- invalid_year_header_count
- chinese_label_row_count
- label_corruption_count
- suspicious_short_label_count
- duplicated_label_count
- numeric_cell_count
- numeric_parse_success_count
- numeric_parse_success_rate
- comma_space_number_count
- parentheses_negative_count
- percent_value_count
- empty_cell_count
- empty_cell_rate
- possible_missing_value_count
- possible_missing_row_or_truncated_output
- has_real_table_grid
- quality_score
- decision

Recommended heuristics:
- valid year labels: `2022`, `2023`, `2024`, `2024A`, `2025E`, `2026E`, etc.
- Chinese label cells should contain CJK characters.
- label corruption signals: `�`, `?`, mojibake-like sequences, very short labels in rows with many values, or labels with high non-CJK noise.
- suspicious missing row signal: very low row_count for common financial statement type, or model output cut before expected table end.
- possible missing value signal: empty numeric year-column cells among otherwise numeric rows.
- timeout warning should be recorded but not automatically fatal.

## diagnostics_required
Create these sheets:

### `structtable_file_inventory`
- image_name
- input_image_path
- output_folder
- raw_response_exists
- markdown_exists
- xlsx_exists
- csv_exists
- run_meta_exists
- error_exists
- error_text
- returncode
- warnings

### `structtable_table_inventory`
- image_name
- table_id
- table_title
- row_count
- col_count
- year_column_count
- has_real_table_grid
- raw_response_timeout_warning_count
- warning_count
- warnings

### `structtable_cell_preview`
- image_name
- table_id
- row_index
- col_index
- raw_text
- normalized_text
- cell_type_guess
- warnings

### `structtable_header_year_audit`
- image_name
- table_id
- raw_header_text
- normalized_header_text
- is_valid_year
- reason

### `structtable_label_audit`
- image_name
- table_id
- row_index
- raw_label
- normalized_label
- label_issue_type
- suspicion_level
- reason

### `structtable_numeric_audit`
- image_name
- table_id
- row_index
- col_index
- raw_text
- normalized_value
- parse_status
- numeric_issue_type
- reason

### `structtable_missing_value_audit`
- image_name
- table_id
- row_index
- col_index
- row_label_preview
- column_header_preview
- neighbor_values_preview
- suspicion_level
- reason

### `structtable_quality_summary`
- image_name
- table_title
- row_count
- col_count
- year_column_count
- chinese_label_row_count
- label_corruption_count
- suspicious_short_label_count
- numeric_parse_success_rate
- empty_cell_rate
- possible_missing_value_count
- quality_score
- decision
- reason

Decisions:
- `STRUCTTABLE_TABLE_EXTRACTION_GOOD_CANDIDATE`
- `STRUCTTABLE_TABLE_EXTRACTION_PARTIAL_REVIEW_NEEDED`
- `STRUCTTABLE_TABLE_EXTRACTION_POOR_OR_TEXT_ONLY`
- `STRUCTTABLE_OUTPUT_MISSING_OR_INVALID`

### `tool_readiness_comparison`
Compare available routes at audit level:
- route_name
- sample_count
- extraction_success_count
- good_candidate_count
- partial_review_needed_count
- poor_count
- numeric_parse_success_rate
- label_issue_count
- missing_value_count
- known_mapping_trusted_rate_if_available
- decision
- notes

## output_contract
Write to:

```powershell
D:\_datefac\output\structtable_output_audit_321e3
```

Required files:
1. `structtable_output_audit_321e3.xlsx`

Sheets:
- `summary`
- `structtable_file_inventory`
- `structtable_table_inventory`
- `structtable_cell_preview`
- `structtable_header_year_audit`
- `structtable_label_audit`
- `structtable_numeric_audit`
- `structtable_missing_value_audit`
- `structtable_quality_summary`
- `tool_readiness_comparison`
- `qa_checks`
- `known_limitations`

2. `structtable_output_audit_321e3_summary.json`

3. `structtable_output_audit_321e3_report.md`

Optional:
- `normalized_structtable_tables.jsonl`
- `structtable_cell_preview.jsonl`

## summary_metrics
Include:
- input_image_count
- discovered_structtable_folder_count
- matched_image_count
- output_folder_missing_count
- raw_response_exists_count
- markdown_exists_count
- xlsx_exists_count
- csv_exists_count
- parse_success_count
- parse_failed_count
- table_count
- image_with_table_count
- image_with_real_table_grid_count
- total_row_count
- total_col_count_sum
- total_cell_count
- total_numeric_cell_count
- numeric_parse_success_rate
- total_year_header_count
- valid_year_header_count
- invalid_year_header_count
- chinese_label_row_count
- label_corruption_count
- suspicious_short_label_count
- duplicated_label_count
- comma_space_number_count
- possible_missing_value_count
- timeout_warning_count
- good_candidate_count
- partial_review_needed_count
- poor_or_text_only_count
- output_missing_or_invalid_count
- docling_audit_decision_if_available
- docling_mapping_decision_if_available
- mineru_body_trusted_rate_if_available
- pure_vlm_trusted_rate_if_available
- ppstructure_trusted_rate_if_available
- qa_pass_count
- qa_warn_count
- qa_fail_count
- structtable_audit_decision

Decision rule:
- If qa_fail_count > 0:
  `STRUCTTABLE_AUDIT_BLOCKED_BY_QA_FAILURE`
- If image_with_real_table_grid_count >= input_image_count * 0.8 and good_candidate_count >= input_image_count * 0.6:
  `STRUCTTABLE_READY_FOR_321E4_FULL_BAKEOFF`
- If image_with_real_table_grid_count >= input_image_count * 0.5:
  `STRUCTTABLE_PARTIAL_INCLUDE_AS_BAKEOFF_CANDIDATE`
- Otherwise:
  `STRUCTTABLE_NOT_READY_FOR_BAKEOFF`

## qa_checks
Required checks:
- input image directory exists;
- StructEqTable output directory exists;
- no E-drive files modified;
- no StructEqTable/Docling/MinerU/VLM/PPStructure command executed;
- every parsed table has source folder/provenance;
- Chinese text is preserved as UTF-8;
- parse failures are captured as warnings, not crashes;
- output Excel/JSON/report written successfully.

## safety_constraints
Absolute constraints:
1. Do not run StructEqTable.
2. Do not run Docling.
3. Do not run MinerU.
4. Do not run PaddleOCR/PPStructure.
5. Do not call VLM/API/cloud/network.
6. Do not modify E-drive input/output folders.
7. Do not modify production delivery files.
8. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
9. Do not modify `data/mapping/formal_scope_rules.json`.
10. Do not run `factory_core.py`.
11. Do not rewrite old Stage7 pipeline.
12. Do not continue 321D2 normalizer expansion.
13. Do not commit `output/` artifacts.
14. Do not commit anything under `E:\mineru_lab`.
15. Do not commit unrelated 320G2 leftovers or temp scripts.
16. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/table_bakeoff/structtable_output_reader.py
python -m py_compile datefac/table_bakeoff/structtable_table_normalizer.py
python -m py_compile datefac/table_bakeoff/structtable_output_audit.py
python -m py_compile tools/run_structtable_output_audit_321e3.py
```

Then run:

```powershell
python tools/run_structtable_output_audit_321e3.py ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --structtable-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\structtable_intervl2 ^
  --docling-audit-dir D:\_datefac\output\docling_output_audit_321e1 ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\structtable_output_audit_321e3
```

PowerShell one-line form is acceptable. Report the exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321E3 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Audit StructEqTable table extraction outputs`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_image_count
- discovered_structtable_folder_count
- matched_image_count
- raw_response_exists_count
- markdown_exists_count
- xlsx_exists_count
- csv_exists_count
- parse_success_count
- table_count
- image_with_real_table_grid_count
- numeric_parse_success_rate
- valid_year_header_count
- invalid_year_header_count
- chinese_label_row_count
- label_corruption_count
- suspicious_short_label_count
- possible_missing_value_count
- timeout_warning_count
- good_candidate_count
- partial_review_needed_count
- poor_or_text_only_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- structtable_audit_decision
- comparison summary vs Docling/MinerU/VLM/PPStructure if available
- skipped/untracked files
