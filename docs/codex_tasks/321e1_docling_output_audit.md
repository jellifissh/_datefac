# 321E1 Docling Output Audit

## task_title
Audit Docling table extraction outputs before broader table extraction bakeoff

## project
D:\_datefac

## current_context
The user has run Docling on the fixed 321E table extraction benchmark images.

Local Docling benchmark folders:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling
```

Observed from the first uploaded sample:
- Docling successfully produced a structured table JSON for an asset-balance-sheet image.
- The JSON contained real table/cell structure rather than plain OCR text:
  - tables: 1
  - num_rows: 26
  - num_cols: 6
  - table_cells: 150
- Strengths in that sample:
  - table title preserved;
  - Chinese row labels mostly preserved;
  - year headers mostly aligned;
  - most numeric cells recognized;
  - output has row/column cell structure usable by DateFac.
- Weaknesses in that sample:
  - some visible numeric cells were missing;
  - some comma-formatted numbers were spaced as `1, 008` / `2, 823`;
  - structure looked promising but not yet proven across all 10 images.

The user has now batch-run Docling, and the output directory contains 10 folders plus at least one directly generated JSON file from an earlier single-image run.

## goal
Implement a sandbox-only Docling output audit and normalizing probe for 321E1.

This stage should answer:
1. Did Docling produce valid JSON outputs for all benchmark images?
2. How many tables/cells/rows/columns did it detect per image?
3. Does each output contain a real table structure, not just free text?
4. Are year columns detected and normalized correctly?
5. Are Chinese row labels preserved?
6. How many empty/missing cells and suspicious numeric cells appear?
7. Is Docling strong enough to enter 321E full tool bakeoff against MinerU/StructTable/VLM?

This is not production integration.

## non_goals
Do not do these in 321E1:
- Do not run Docling again unless the CLI explicitly has a `--rerun-docling` flag defaulting to false.
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not modify E:\mineru_lab.
- Do not modify production delivery files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not continue 321D2 normalizer rule expansion.
- Do not claim Docling is best before benchmark evidence.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/321e1_docling_output_audit.md`
- `datefac/table_bakeoff/__init__.py`
- `datefac/table_bakeoff/docling_output_reader.py`
- `datefac/table_bakeoff/docling_table_normalizer.py`
- `datefac/table_bakeoff/docling_output_audit.py`
- `tools/run_docling_output_audit_321e1.py`

Keep this in a new table bakeoff / audit namespace. Do not mix it into `datefac/mineru_body`, VLM, or old PPStructure code.

## input_contract
Primary inputs:

```powershell
E:\mineru_lab\benchmarks\table_extraction_321e\input_images
E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling
```

Optional reference inputs:

```powershell
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\mineru_table_body_calibration_321d2
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_docling_output_audit_321e1.py ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --docling-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling ^
  --output-dir D:\_datefac\output\docling_output_audit_321e1
```

If input or Docling output directory is missing, write a blocked summary instead of crashing:
- `BLOCKED_MISSING_INPUT_IMAGE_DIR`
- `BLOCKED_MISSING_DOCLING_OUTPUT_DIR`

## reader_requirements
Docling output may contain:
- one JSON directly under the docling output root from an earlier single-image run;
- per-image subdirectories with JSON, md, html, stdout/stderr/returncode files;
- multiple JSON files per folder depending on Docling version/export mode.

Reader should:
1. recursively discover JSON files under `--docling-output-dir`;
2. associate each JSON with an input image by file stem, folder name, or nearest path match;
3. parse Docling JSON robustly without assuming one exact schema;
4. extract tables from common Docling structures, including:
   - top-level `tables`;
   - nested table objects;
   - cell lists with row/col indexes;
   - exported document structures that contain table nodes;
5. preserve raw path/provenance for every extracted table;
6. never modify Docling output files.

## normalized_table_schema
Normalize Docling tables into this internal shape:

```json
{
  "tool": "docling",
  "image_name": "",
  "docling_json_path": "",
  "table_index": 0,
  "table_title": "",
  "unit": "",
  "num_rows": 0,
  "num_cols": 0,
  "cells": [
    {
      "row_index": 0,
      "col_index": 0,
      "row_span": 1,
      "col_span": 1,
      "text": "",
      "is_header": false
    }
  ],
  "columns": [],
  "rows": [],
  "warnings": []
}
```

The normalizer should not attempt full DateFac MetricCandidate mapping yet. It should only assess table extraction quality.

## audit_metrics
Compute per image/table:
- json_parse_ok
- table_count
- selected_table_count
- num_rows
- num_cols
- cell_count
- non_empty_cell_count
- empty_cell_count
- empty_cell_rate
- header_cell_count
- detected_year_columns
- year_column_count
- invalid_year_header_count
- chinese_label_cell_count
- numeric_cell_count
- numeric_parse_success_count
- numeric_parse_success_rate
- comma_space_number_count, e.g. `1, 008`
- parentheses_negative_count
- percent_value_count
- possible_missing_value_count
- has_table_title
- detected_unit
- has_real_cell_grid
- returncode if available
- stderr_warning_count if available

Recommended simple heuristics:
- valid year labels: `2022`, `2023`, `2024`, `2024A`, `2025E`, `2026E`, etc.
- numeric values may include commas, spaces after commas, parentheses negatives, `-`, `—`, `%`.
- Chinese label cells are cells containing CJK characters.
- possible missing values are empty cells inside a row that otherwise has numeric neighbors or inside a numeric year column.

## diagnostics_required
Create these sheets:

### `docling_file_inventory`
Columns:
- image_name
- input_image_path
- matched_output_folder
- json_file_count
- json_paths
- md_file_count
- html_file_count
- stdout_path
- stderr_path
- returncode
- warnings

### `docling_table_inventory`
Columns:
- image_name
- docling_json_path
- table_index
- table_title
- detected_unit
- num_rows
- num_cols
- cell_count
- non_empty_cell_count
- empty_cell_count
- empty_cell_rate
- has_real_cell_grid
- warning_count
- warnings

### `docling_cell_preview`
Columns:
- image_name
- table_index
- row_index
- col_index
- row_span
- col_span
- text
- normalized_text
- is_header
- cell_type_guess
- warnings

### `docling_header_year_audit`
Columns:
- image_name
- table_index
- raw_header_text
- normalized_header_text
- is_valid_year
- reason

### `docling_numeric_audit`
Columns:
- image_name
- table_index
- row_index
- col_index
- raw_text
- normalized_value
- parse_status
- numeric_issue_type
- reason

### `docling_missing_cell_audit`
Columns:
- image_name
- table_index
- row_index
- col_index
- row_label_preview
- column_header_preview
- neighbor_values_preview
- suspicion_level
- reason

### `docling_quality_summary`
Columns:
- image_name
- table_count
- best_table_rows
- best_table_cols
- year_column_count
- chinese_label_cell_count
- numeric_parse_success_rate
- empty_cell_rate
- comma_space_number_count
- possible_missing_value_count
- quality_score
- decision
- reason

Decisions:
- `DOCLING_TABLE_EXTRACTION_GOOD_CANDIDATE`
- `DOCLING_TABLE_EXTRACTION_PARTIAL_REVIEW_NEEDED`
- `DOCLING_TABLE_EXTRACTION_POOR_OR_TEXT_ONLY`
- `DOCLING_OUTPUT_MISSING_OR_INVALID`

## output_contract
Write to:

```powershell
D:\_datefac\output\docling_output_audit_321e1
```

Required files:
1. `docling_output_audit_321e1.xlsx`

Sheets:
- `summary`
- `docling_file_inventory`
- `docling_table_inventory`
- `docling_cell_preview`
- `docling_header_year_audit`
- `docling_numeric_audit`
- `docling_missing_cell_audit`
- `docling_quality_summary`
- `qa_checks`
- `known_limitations`

2. `docling_output_audit_321e1_summary.json`

3. `docling_output_audit_321e1_report.md`

Optional:
- `normalized_docling_tables.jsonl`
- `docling_cell_preview.jsonl`

## summary_metrics
Include:
- input_image_count
- discovered_docling_folder_count
- discovered_json_file_count
- matched_image_count
- unmatched_image_count
- json_parse_success_count
- json_parse_failed_count
- total_table_count
- image_with_table_count
- image_with_real_cell_grid_count
- total_cell_count
- total_empty_cell_count
- overall_empty_cell_rate
- total_chinese_label_cell_count
- total_numeric_cell_count
- numeric_parse_success_rate
- total_year_header_count
- valid_year_header_count
- invalid_year_header_count
- comma_space_number_count
- possible_missing_value_count
- good_candidate_count
- partial_review_needed_count
- poor_or_text_only_count
- output_missing_or_invalid_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- docling_audit_decision

Decision rule:
- If qa_fail_count > 0:
  `DOCLING_AUDIT_BLOCKED_BY_QA_FAILURE`
- If image_with_real_cell_grid_count >= input_image_count * 0.8 and good_candidate_count >= input_image_count * 0.5:
  `DOCLING_READY_FOR_321E_TOOL_BAKEOFF`
- If image_with_real_cell_grid_count >= input_image_count * 0.5:
  `DOCLING_PARTIAL_INCLUDE_AS_BAKEOFF_CANDIDATE`
- Otherwise:
  `DOCLING_NOT_READY_FOR_BAKEOFF`

## qa_checks
Required checks:
- input image directory exists;
- Docling output directory exists;
- no E-drive files modified;
- no Docling/MinerU/VLM/PPStructure command executed by default;
- JSON parse failures are captured as warnings, not crashes;
- every parsed table has source JSON path;
- Chinese text is preserved as UTF-8;
- output Excel/JSON/report written successfully.

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
10. Do not continue 321D2 normalizer expansion.
11. Do not commit `output/` artifacts.
12. Do not commit anything under `E:\mineru_lab`.
13. Do not commit unrelated 320G2 leftovers or temp scripts.
14. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/table_bakeoff/docling_output_reader.py
python -m py_compile datefac/table_bakeoff/docling_table_normalizer.py
python -m py_compile datefac/table_bakeoff/docling_output_audit.py
python -m py_compile tools/run_docling_output_audit_321e1.py
```

Then run:

```powershell
python tools/run_docling_output_audit_321e1.py ^
  --input-image-dir E:\mineru_lab\benchmarks\table_extraction_321e\input_images ^
  --docling-output-dir E:\mineru_lab\benchmarks\table_extraction_321e\outputs\docling ^
  --output-dir D:\_datefac\output\docling_output_audit_321e1
```

If using PowerShell one-line form, report the exact command.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321E1 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Audit Docling table extraction outputs`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_image_count
- discovered_docling_folder_count
- discovered_json_file_count
- matched_image_count
- json_parse_success_count
- total_table_count
- image_with_table_count
- image_with_real_cell_grid_count
- total_cell_count
- overall_empty_cell_rate
- numeric_parse_success_rate
- valid_year_header_count
- invalid_year_header_count
- comma_space_number_count
- possible_missing_value_count
- good_candidate_count
- partial_review_needed_count
- poor_or_text_only_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- docling_audit_decision
- skipped/untracked files
