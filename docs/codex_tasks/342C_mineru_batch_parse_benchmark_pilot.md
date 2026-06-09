# 342C MinerU Batch Parse Benchmark Pilot

## Goal

Run a sidecar MinerU batch parse benchmark for the `pilot_set` selected by 342B.

This task only benchmarks MinerU parsing on the first pilot scope.
It must not extract core metrics.
It must not perform human review.
It must not generate client export artifacts.
It must not modify production pipeline, parser abstraction, extraction logic, or delivery/export logic.

## Current Upstream State

- `342B decision = REAL_PDF_CORPUS_INTAKE_342B_READY`
- `current_pdf_count = 31`
- `unique_pdf_count = 31`
- `duplicate_pdf_count = 0`
- `pilot_set_count = 5`
- `benchmark_set_count = 20`
- `holdout_set_count = 6`
- `ready_for_342c = true`
- `recommended_first_run_pdf_count = 5`
- `qa_fail_count = 0`

## Inputs

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/real_pdf_corpus_intake_342b/real_pdf_corpus_intake_342b.xlsx`

## Output Dir

- `D:/_datefac/output/mineru_batch_parse_benchmark_342c`

## MinerU Raw Output Dir

- `D:/_datefac/output/mineru_batch_parse_benchmark_342c/mineru_outputs`

## Output Files

- `mineru_batch_parse_benchmark_342c.xlsx`
- `mineru_batch_parse_benchmark_342c_summary.json`
- `mineru_batch_parse_benchmark_342c_manifest.json`
- `mineru_batch_parse_benchmark_342c_qa.json`
- `mineru_batch_parse_benchmark_342c_no_write_back_proof.json`
- `mineru_batch_parse_benchmark_342c_report.md`

## Workbook Sheets

1. `00_README`
2. `01_PARSE_SUMMARY`
3. `02_PDF_PARSE_RESULTS`
4. `03_OUTPUT_ARTIFACT_AUDIT`
5. `04_FAILURE_AUDIT`
6. `05_EMPTY_OUTPUT_AUDIT`
7. `06_RUNTIME_AUDIT`
8. `07_NEXT_342D_READINESS`
9. `08_NO_WRITE_BACK_PROOF`
10. `09_NEXT_STEPS`

All sheet names must be `<= 31` characters.

## Required 342B Intake Fields

Read from the 342B workbook and merge:

- `corpus_pdf_id`
- `file_name`
- `file_path`
- `sha256`
- `page_count`
- `assigned_tier`
- `split`

Only select:

- `split = pilot_set`

If `pilot_set` is missing or contains fewer than one PDF, QA must fail.

## Runner Parameters

The runner should support at minimum:

- `--corpus-342b-dir`
- `--output-dir`
- `--mineru-command`
- `--limit`
- `--dry-run`

Behavior:

- `--mineru-command` may point to a MinerU executable or a full command template.
- If a full command template is used, support placeholders:
  - `{pdf_path}`
  - `{mineru_output_root}`
- Default to the project-local MinerU executable if available.
- `--dry-run` must simulate selection and command planning without invoking MinerU.

## Parse Result Fields

Each selected PDF must produce one parse result row with:

- `corpus_pdf_id`
- `file_name`
- `file_path`
- `sha256`
- `split`
- `assigned_tier`
- `page_count`
- `parse_status`
- `runtime_seconds`
- `output_dir`
- `markdown_file_count`
- `json_file_count`
- `html_file_count`
- `image_file_count`
- `table_like_file_count`
- `output_file_count`
- `output_size_mb`
- `empty_output_flag`
- `error_message`
- `command_used`

Allowed `parse_status` values:

- `SUCCESS`
- `FAILED`
- `SKIPPED_DRY_RUN`

## Output Artifact Audit

For each selected PDF output dir, audit:

- whether the dir exists
- whether the dir is empty
- whether it contains `.md`
- whether it contains `.json`
- whether it contains images
- whether it contains table-like files
- whether output size looks abnormally small

## Failure Audit

Create a dedicated failure table with:

- `corpus_pdf_id`
- `file_name`
- `parse_status`
- `error_message`
- `retry_recommendation`

## Empty Output Audit

Create a dedicated empty-or-suspicious-output table with:

- `corpus_pdf_id`
- `file_name`
- `output_file_count`
- `output_size_mb`
- `empty_output_reason`

## Runtime Audit

Capture:

- `total_runtime_seconds`
- `avg_runtime_seconds`
- `max_runtime_seconds`
- `slowest_pdf_id`
- `fastest_pdf_id`

## 342D Readiness

Decide readiness for `342D Parser Ensemble Compare Benchmark`.

Rules:

- `pilot_total_count = 5`
- `mineru_success_count >= 1`
- `qa_fail_count = 0`
- no-write-back proof passed

Decision guidance:

- all 5 success:
  - `ready_for_342d = true`
  - `recommended_next_scope = pilot_set_parser_compare`
- partial success:
  - `ready_for_342d = conditional`
  - `recommended_next_scope = retry_failed_then_compare`
- all fail:
  - `ready_for_342d = false`

## Required Summary Fields

- `pilot_total_count = 5`
- `mineru_success_count`
- `mineru_failed_count`
- `empty_output_count`
- `total_runtime_seconds`
- `avg_runtime_seconds`
- `ready_for_342d`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `decision = MINERU_BATCH_PARSE_BENCHMARK_342C_READY`
- or `MINERU_BATCH_PARSE_BENCHMARK_342C_READY_WITH_FAILURES`

## No-Write-Back Proof

The proof must show:

- no upstream 342B workbook or summary changed
- no official assets changed
- no client export generated
- no parser/extraction/delivery production source modified

## QA Requirements

- 342B input exists
- pilot_set detected
- `selected_pdf_count = 5` unless `limit` is smaller
- every selected PDF has a parse result row
- output artifact audit generated
- failure audit generated
- empty output audit generated
- runtime audit generated
- no parser/extraction/delivery source modified
- no upstream workbook modified
- no `client_ready = true`
- no `production_ready = true`
- no investment advice claim
- no sheet name exceeds 31 chars
- `qa_fail_count = 0`

## Files

- `docs/codex_tasks/342C_mineru_batch_parse_benchmark_pilot.md`
- `datefac/benchmark/mineru_batch_parse_benchmark_342c.py`
- `datefac/benchmark/mineru_batch_parse_benchmark_342c_report.py`
- `tools/run_mineru_batch_parse_benchmark_342c.py`
- `tests/benchmark/test_mineru_batch_parse_benchmark_342c.py`

## Run

```powershell
python -m py_compile datefac\benchmark\mineru_batch_parse_benchmark_342c.py datefac\benchmark\mineru_batch_parse_benchmark_342c_report.py tools\run_mineru_batch_parse_benchmark_342c.py tests\benchmark\test_mineru_batch_parse_benchmark_342c.py

python -m pytest tests\benchmark\test_mineru_batch_parse_benchmark_342c.py -q

python tools\run_mineru_batch_parse_benchmark_342c.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --output-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --limit 5 --dry-run

python tools\run_mineru_batch_parse_benchmark_342c.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --output-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --limit 5
```
