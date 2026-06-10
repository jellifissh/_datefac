# 342D Parser Ensemble Compare Benchmark

## Goal

Create a sidecar parser evidence comparison package based on the completed `342C6` MinerU recovery rerun results.

This task compares parser evidence only.
It must not:

- modify production pipeline
- modify parser abstraction
- modify extraction logic
- modify delivery or export logic
- modify `342B`, `342C`, `342C2`, `342C4`, or `342C6` upstream artifacts
- commit output artifacts

## Current Confirmed Context

`342C6` is now the trusted parser benchmark input for this task.
Its summary confirms:

- `original_success_count = 3`
- `original_failed_count = 2`
- `rerun_target_count = 2`
- `rerun_success_count = 2`
- `rerun_failed_count = 0`
- `final_success_count = 5`
- `final_failed_count = 0`
- `final_empty_output_count = 0`
- `ready_for_342d = true`
- `recommended_342d_scope = full_pilot_set_5`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`

## Inputs

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_pilot_network_recovery_342c6`
- `D:/_datefac/output/mineru_pilot_network_recovery_342c6/mineru_outputs`

## Optional Reference Inputs

- existing `pdfplumber` historical artifacts
- existing `marker` historical artifacts
- existing `docling` probe artifacts
- existing `ppstructure` historical artifacts
- previous real-test parser artifacts

If no reliable same-PDF baseline is discovered, record `baseline_missing` or `no_matching_historical_artifacts` instead of failing the task.

## Output Dir

- `D:/_datefac/output/parser_ensemble_compare_342d`

## Output Files

- `parser_ensemble_compare_342d.xlsx`
- `parser_ensemble_compare_342d_summary.json`
- `parser_ensemble_compare_342d_manifest.json`
- `parser_ensemble_compare_342d_qa.json`
- `parser_ensemble_compare_342d_report.md`
- `parser_ensemble_compare_342d_no_write_back_proof.json`

## Workbook Sheets

1. `00_README`
2. `01_COMPARE_SUMMARY`
3. `02_PDF_LEVEL_COMPARE`
4. `03_MINERU_ARTIFACT_AUDIT`
5. `04_BASELINE_DISCOVERY`
6. `05_TABLE_SIGNAL_COMPARE`
7. `06_MARKDOWN_SIGNAL_AUDIT`
8. `07_CONTENT_LIST_AUDIT`
9. `08_RISK_AND_LIMITATIONS`
10. `09_342E_READINESS`
11. `10_NO_WRITE_BACK_PROOF`
12. `11_NEXT_STEPS`

All sheet names must remain `<= 31` characters.

## Required Behavior

1. Read the `342C6` final pilot rollup and confirm:
   - `final_success_count = 5`
   - `final_failed_count = 0`
   - `ready_for_342d = true`
   - `qa_fail_count = 0`
2. Generate a MinerU artifact audit for all five pilot PDFs:
   - `corpus_pdf_id`
   - `file_name`
   - `source_pdf_path`
   - `mineru_output_dir`
   - `has_auto_dir`
   - `has_md`
   - `md_file_count`
   - `md_size_kb`
   - `has_content_list_json`
   - `content_list_json_count`
   - `content_list_item_count`
   - `has_middle_json`
   - `has_model_json`
   - `image_file_count`
   - `layout_pdf_exists`
   - `span_pdf_exists`
   - `origin_pdf_exists`
   - `output_size_mb`
   - `artifact_complete_flag`
3. Parse `content_list.json` only as parser evidence and record:
   - `text_block_count`
   - `table_block_count`
   - `image_block_count`
   - `equation_block_count`
   - `page_coverage_count`
   - `table_like_text_signal_count`
   - `financial_keyword_signal_count`
4. Read `.md` files and record:
   - `md_line_count`
   - `md_table_line_count`
   - `pipe_table_line_count`
   - `financial_keyword_hit_count`
   - `year_token_hit_count`
   - `unit_token_hit_count`
   - `suspicious_empty_md_flag`
5. Discover historical parser baselines automatically where possible.
   If same-PDF mapping is not reliable, set:
   - `baseline_available = false`
   - `baseline_missing_reason = no_matching_historical_artifacts`
6. Compare only parser evidence signals.
   Do not overclaim stronger parser conclusions when baseline evidence is missing.
7. Generate a per-PDF compare row with:
   - `mineru_artifact_complete_flag`
   - `mineru_table_signal_score`
   - `mineru_financial_signal_score`
   - `mineru_markdown_usable_flag`
   - `baseline_available`
   - `baseline_table_signal_score`
   - `baseline_financial_signal_score`
   - `compare_judgment`
8. `342E` readiness rules:
   - all five MinerU outputs artifact-complete
   - at least three PDFs markdown-usable
   - at least three PDFs with financial keyword signal > 0
   - `qa_fail_count = 0`
9. Safety rules:
   - `client_ready = false`
   - `production_ready = false`
   - benchmark package only

## Implementation Files

- `docs/codex_tasks/342D_parser_ensemble_compare_benchmark.md`
- `datefac/benchmark/parser_ensemble_compare_342d.py`
- `datefac/benchmark/parser_ensemble_compare_342d_report.py`
- `tools/run_parser_ensemble_compare_342d.py`
- `tests/benchmark/test_parser_ensemble_compare_342d.py`

## Run

```powershell
python tools\run_parser_ensemble_compare_342d.py `
  --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b `
  --mineru-342c6-dir D:\_datefac\output\mineru_pilot_network_recovery_342c6 `
  --output-dir D:\_datefac\output\parser_ensemble_compare_342d
```

## Validation

```powershell
python -m py_compile datefac\benchmark\parser_ensemble_compare_342d.py datefac\benchmark\parser_ensemble_compare_342d_report.py tools\run_parser_ensemble_compare_342d.py tests\benchmark\test_parser_ensemble_compare_342d.py

python -m pytest tests\benchmark\test_parser_ensemble_compare_342d.py -q
```
