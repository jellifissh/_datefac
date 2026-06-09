# 342C2 MinerU Pilot Retry With Verified Local Environment

## Goal

Create a sidecar retry package that reruns the 342B `pilot_set` PDFs with the verified local MinerU environment and command shape.

This task is only for retry benchmarking and environment verification.
It must help answer whether the original 342C failure was caused by runner environment or model-cache path issues.

This task must not:

- modify production pipeline, parser abstraction, extraction, or delivery behavior
- modify 342B or 342C upstream artifacts
- generate client export artifacts
- commit output artifacts

## Confirmed Working Local MinerU Context

- conda env: `mineru_new`
- working lab dir: `E:/mineru_lab`
- model cache dir: `E:/mineru_lab/models`
- known working command pattern:

```powershell
mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true
```

## Inputs

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_batch_parse_benchmark_342c`

## Output Dir

- `D:/_datefac/output/mineru_pilot_retry_verified_env_342c2`

## Output Files

- `mineru_pilot_retry_verified_env_342c2.xlsx`
- `mineru_pilot_retry_verified_env_342c2_summary.json`
- `mineru_pilot_retry_verified_env_342c2_manifest.json`
- `mineru_pilot_retry_verified_env_342c2_qa.json`
- `mineru_pilot_retry_verified_env_342c2_no_write_back_proof.json`
- `mineru_pilot_retry_verified_env_342c2_report.md`

## Workbook Sheets

1. `00_README`
2. `01_RETRY_SUMMARY`
3. `02_RETRY_PARSE_RESULTS`
4. `03_OUTPUT_ARTIFACT_AUDIT`
5. `04_ORIG_342C_RECAP`
6. `05_RETRY_FAILURE_AUDIT`
7. `06_EMPTY_OUTPUT_AUDIT`
8. `07_342D_READINESS`
9. `08_ENV_CONTEXT`
10. `09_NO_WRITE_BACK_PROOF`
11. `10_NEXT_STEPS`

All sheet names must remain `<= 31` characters.

## Required Behavior

1. Read the 342B `pilot_set` rows and rerun the selected PDFs.
2. Read the original 342C outputs and record:
   - original pilot count
   - original success/failure counts
   - original empty output count
   - whether SSL certificate failure was detected
   - whether `huggingface.co` was detected in failure text
3. Run MinerU with:
   - executable default `mineru`
   - required args `-b pipeline --formula false --table true`
4. Support running from an already activated `mineru_new` shell.
5. Also support explicit verified-environment hints:
   - `working_lab_dir`
   - `model_cache_dir`
   - `mineru_config_path`
6. For each retried PDF, record:
   - `parse_status`
   - `execution_mode`
   - `runtime_seconds`
   - `output_dir`
   - `output_file_count`
   - `markdown_file_count`
   - `json_file_count`
   - `html_file_count`
   - `image_file_count`
   - `table_like_file_count`
   - `error_message`
   - `command_used`
7. Generate:
   - retry summary
   - output artifact audit
   - original 342C failure recap
   - retry failure audit
   - empty output audit
   - 342D readiness recommendation
   - no-write-back proof
8. Readiness rules:
   - if `retry_mineru_success_count >= 1`, `ready_for_342d = conditional`
   - if all selected retry PDFs succeed, `ready_for_342d = true`
   - otherwise `ready_for_342d = false`
9. Safety rules:
   - `client_ready = false`
   - `production_ready = false`
   - `qa_fail_count = 0` when the sidecar package is valid even if parse failures remain

## Implementation Files

- `docs/codex_tasks/342C2_mineru_pilot_retry_verified_env.md`
- `datefac/benchmark/mineru_pilot_retry_verified_env_342c2.py`
- `datefac/benchmark/mineru_pilot_retry_verified_env_342c2_report.py`
- `tools/run_mineru_pilot_retry_verified_env_342c2.py`
- `tests/benchmark/test_mineru_pilot_retry_verified_env_342c2.py`

## Run

Real retry should be launched from the verified MinerU environment:

```powershell
conda activate mineru_new
cd D:\_datefac

python tools\run_mineru_pilot_retry_verified_env_342c2.py `
  --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b `
  --mineru-342c-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c `
  --output-dir D:\_datefac\output\mineru_pilot_retry_verified_env_342c2 `
  --limit 5 `
  --mineru-command "mineru"
```

## Validation

```powershell
python -m py_compile datefac\benchmark\mineru_pilot_retry_verified_env_342c2.py datefac\benchmark\mineru_pilot_retry_verified_env_342c2_report.py tools\run_mineru_pilot_retry_verified_env_342c2.py tests\benchmark\test_mineru_pilot_retry_verified_env_342c2.py

python -m pytest tests\benchmark\test_mineru_pilot_retry_verified_env_342c2.py -q
```
