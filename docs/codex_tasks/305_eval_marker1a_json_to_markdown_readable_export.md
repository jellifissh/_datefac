# Task 305: EVAL-MARKER-1A JSON to Markdown Readable Export

## Stage
- `EVAL-MARKER-1A`

## Goal
- Convert existing Marker JSON outputs from `EVAL-MARKER-1` into human-readable review files (`.md`) with HTML-style table content preserved where available.
- Do this **without rerunning Marker**, **without API/LLM/OCR**, and **without modifying production paths or rules**.

## Scope
- Read only previously generated Marker artifacts:
  - `output/eval_marker1_no_llm_parser_benchmark/marker_outputs/`
  - `output/eval_marker1_no_llm_parser_benchmark/304_eval_marker1_no_llm_benchmark_summary.json`
  - `output/eval_marker1_no_llm_parser_benchmark/304_eval_marker1_per_pdf_benchmark.xlsx`
  - `output/eval_marker1_no_llm_parser_benchmark/304_eval_marker1_marker_table_inventory.xlsx`
- Produce readable exports under:
  - `output/eval_marker1a_json_to_markdown_readable_export/`

## Hard Constraints
- No external API calls.
- No LLM API calls.
- No OCR calls.
- Do not rerun Marker.
- Do not modify extraction logic.
- Do not modify candidate rules.
- Do not modify production files / official 02B / formal rules / `financial_standardizer.py` / release package.
- Do not modify input PDFs.
- Must keep `check_delivery_state.py --json` as `PASS`.

## Required Outputs
- `output/eval_marker1a_json_to_markdown_readable_export/305_eval_marker1a_summary.json`
- `output/eval_marker1a_json_to_markdown_readable_export/305_eval_marker1a_report.md`
- `output/eval_marker1a_json_to_markdown_readable_export/305_eval_marker1a_per_pdf_export_status.xlsx`
- `output/eval_marker1a_json_to_markdown_readable_export/305_eval_marker1a_table_index.xlsx`
- `output/eval_marker1a_json_to_markdown_readable_export/305_eval_marker1a_no_apply_proof.json`
- `output/eval_marker1a_json_to_markdown_readable_export/readable_markdown/*.md` (one per PDF)

## Export Rules
- For each PDF:
  1. Read Marker `*.json` and `*_meta.json` if present.
  2. Collect page-level block information.
  3. For table-like blocks (`Table`, `TableGroup`) output:
     - page number
     - block id
     - bbox
     - plain-text preview
     - row/column estimates if derivable from HTML
     - HTML table snippet (trimmed if huge)
  4. Include page stats from meta (`block_counts`) for context.
- Base64 images:
  - Any `data:image/...;base64,...` in HTML or text must be removed/replaced with placeholder.
  - Report whether base64 payloads were excluded.

## Summary Fields
- `stage = "EVAL-MARKER-1A"`
- `mode = "marker_json_to_markdown_readable_export"`
- `external_api_called = false`
- `llm_api_called = false`
- `ocr_called = false`
- `marker_rerun_executed = false`
- `eval_marker1_summary_loaded = true`
- `input_pdf_count = 10`
- `readable_markdown_generated_count`
- `table_index_generated = true`
- `base64_images_excluded = true`
- `production_files_modified = false`
- `official_02b_modified = false`
- `formal_rules_modified = false`
- `standardizer_modified = false`
- `release_package_modified = false`
- `check_delivery_state_overall_status = "PASS"`

## Run
1. `python tools/run_eval_marker1a_json_to_markdown_readable_export.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only minimal required code/docs changes for this stage.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
- Do not commit bulky generated runtime folders unless explicitly required.
