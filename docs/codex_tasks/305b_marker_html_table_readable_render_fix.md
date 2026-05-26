# Task 305B: Marker HTML Table Readable Render Fix

## Stage
- `EVAL-MARKER-1B`

## Goal
- Fix readable export quality by converting existing Marker HTML tables into:
  - human-readable Markdown tables (not fenced HTML blocks)
  - Excel workbooks with one sheet per table where possible

## Scope
- Read only existing `EVAL-MARKER-1` Marker outputs:
  - `output/eval_marker1_no_llm_parser_benchmark/marker_outputs/`
  - `output/eval_marker1_no_llm_parser_benchmark/304_eval_marker1_no_llm_benchmark_summary.json`
  - `output/eval_marker1_no_llm_parser_benchmark/304_eval_marker1_per_pdf_benchmark.xlsx`
  - `output/eval_marker1_no_llm_parser_benchmark/304_eval_marker1_marker_table_inventory.xlsx`
- Write new outputs to:
  - `output/eval_marker1b_html_table_readable_render_fix/`

## Hard Constraints
- Do not rerun Marker.
- Do not call external API.
- Do not call LLM API.
- Do not call OCR.
- Do not modify production files / official 02B / formal rules / `financial_standardizer.py` / release package.
- Do not modify input PDFs.
- Keep `check_delivery_state.py --json` at `PASS`.

## Required Outputs
- `output/eval_marker1b_html_table_readable_render_fix/readable_markdown_v2/*.md`
- `output/eval_marker1b_html_table_readable_render_fix/readable_excel/*.xlsx`
- `output/eval_marker1b_html_table_readable_render_fix/305b_summary.json`
- `output/eval_marker1b_html_table_readable_render_fix/305b_report.md`
- `output/eval_marker1b_html_table_readable_render_fix/305b_table_render_index.xlsx`
- `output/eval_marker1b_html_table_readable_render_fix/305b_no_apply_proof.json`

## Rendering Rules
- Parse table HTML using `pandas.read_html` or `BeautifulSoup`.
- Markdown must render actual pipe tables, not ```html fenced code blocks.
- Excel export should use one sheet per parsed table when possible.
- Remove/replace base64 image payloads from exported content.

## Run
1. `python tools/run_eval_marker1b_html_table_readable_render_fix.py`
2. `python tools/check_delivery_state.py --json`

## Git Hygiene
- Commit only task doc + runner implementation needed for this stage.
- Do not stage historical untracked files:
  - `tools/run_stage7a_5pdf_regression_sandbox.py`
  - `tools/update_stage5v_production_06_safe_rows.py`
- Do not commit bulky runtime artifacts.
