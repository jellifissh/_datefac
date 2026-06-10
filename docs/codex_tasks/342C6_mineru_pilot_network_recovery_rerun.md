# 342C6 MinerU Pilot Network Recovery Rerun

## Goal

Create a sidecar recovery rerun package that reads the completed `342C2 after env fix` results, reruns only the failed or empty-output pilot PDFs, and merges those rerun results with the original successful `342C2` outputs.

This task is a recovery benchmark only.
It must not:

- enter `342D`
- modify production pipeline, parser abstraction, extraction, or delivery behavior
- modify `342B`, `342C`, `342C2`, or `342C4` upstream artifacts
- commit output artifacts

## Current Confirmed Context

- MinerU environment has already been repaired.
- `342C2 after env fix` is the current trusted retry input.
- `342C2` summary shows:
  - `retry_pilot_total_count = 5`
  - `retry_mineru_success_count = 3`
  - `retry_mineru_failed_count = 2`
  - `empty_output_count = 2`
  - `ready_for_342d = conditional`
  - `recommended_next_scope = inspect_failed_retry_rows_then_compare`
  - `qa_fail_count = 0`
  - `decision = MINERU_PILOT_RETRY_VERIFIED_ENV_342C2_READY`
- User confirmed the two failed or empty rows were mainly caused by network interruption rather than confirmed PDF-level unparseability.

## Inputs

- `D:/_datefac/output/real_pdf_corpus_intake_342b`
- `D:/_datefac/output/mineru_pilot_retry_verified_env_342c2_after_env_fix`

## Output Dir

- `D:/_datefac/output/mineru_pilot_network_recovery_342c6`

## Output Files

- `mineru_pilot_network_recovery_342c6.xlsx`
- `mineru_pilot_network_recovery_342c6_summary.json`
- `mineru_pilot_network_recovery_342c6_manifest.json`
- `mineru_pilot_network_recovery_342c6_qa.json`
- `mineru_pilot_network_recovery_342c6_no_write_back_proof.json`
- `mineru_pilot_network_recovery_342c6_report.md`

## Workbook Sheets

1. `00_README`
2. `01_RECOVERY_SUMMARY`
3. `02_FAILED_ROWS_TO_RERUN`
4. `03_RERUN_RESULTS`
5. `04_FINAL_PILOT_ROLLUP`
6. `05_ARTIFACT_AUDIT`
7. `06_342D_READINESS`
8. `07_NO_WRITE_BACK_PROOF`
9. `08_NEXT_STEPS`

All sheet names must remain `<= 31` characters.

## Required Behavior

1. Read the `342C2 after env fix` summary and parse workbook.
2. Detect failed or empty retry rows only.
3. Rerun only those failed or empty rows.
4. Reuse the original three successful `342C2` outputs without rerunning them.
5. Write new recovery rerun outputs only under:
   - `D:/_datefac/output/mineru_pilot_network_recovery_342c6/mineru_outputs`
6. Generate a final five-row merged rollup with:
   - `corpus_pdf_id`
   - `file_name`
   - `source`
   - `final_parse_status`
   - `output_dir`
   - `md_file_count`
   - `content_list_json_count`
   - `middle_json_count`
   - `image_file_count`
   - `output_file_count`
   - `output_size_mb`
   - `error_message`
7. Status rules:
   - if a rerun PDF produces `.md` and `content_list.json`, `final_parse_status = SUCCESS`
   - if it still has no usable output, `final_parse_status = FAILED_OR_EMPTY`
8. Readiness rules:
   - if `final_success_count = 5` and `qa_fail_count = 0`, `ready_for_342d = true` and `recommended_342d_scope = full_pilot_set_5`
   - if `final_success_count = 3` or `4`, `ready_for_342d = conditional` and `recommended_342d_scope = successful_pilot_outputs_only`
   - if `final_success_count < 3`, `ready_for_342d = false`
9. Safety rules:
   - `client_ready = false`
   - `production_ready = false`
   - `qa_fail_count = 0` when the sidecar package is internally valid even if some pilot failures remain

## Implementation Files

- `docs/codex_tasks/342C6_mineru_pilot_network_recovery_rerun.md`
- `datefac/benchmark/mineru_pilot_network_recovery_342c6.py`
- `datefac/benchmark/mineru_pilot_network_recovery_342c6_report.py`
- `tools/run_mineru_pilot_network_recovery_342c6.py`
- `tests/benchmark/test_mineru_pilot_network_recovery_342c6.py`

## Run

```powershell
python tools\run_mineru_pilot_network_recovery_342c6.py `
  --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b `
  --mineru-342c2-dir D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix `
  --output-dir D:\_datefac\output\mineru_pilot_network_recovery_342c6 `
  --mineru-command "D:/anaconda/envs/mineru_new/Scripts/mineru.exe"
```

## Validation

```powershell
python -m py_compile datefac\benchmark\mineru_pilot_network_recovery_342c6.py datefac\benchmark\mineru_pilot_network_recovery_342c6_report.py tools\run_mineru_pilot_network_recovery_342c6.py tests\benchmark\test_mineru_pilot_network_recovery_342c6.py

python -m pytest tests\benchmark\test_mineru_pilot_network_recovery_342c6.py -q
```
