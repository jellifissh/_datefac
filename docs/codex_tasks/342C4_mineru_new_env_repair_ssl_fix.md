# 342C4 MinerU New Environment Repair And SSL Fix

## Goal

Repair the existing `mineru_new` conda environment so that MinerU can initialize its model download stack without being blocked by user-site package pollution, dependency version conflicts, or SSL/HuggingFace access failures.

This task is environment repair and diagnosis only.

It must not:

- modify DateFac production pipeline
- modify parser abstraction
- modify extraction behavior
- modify delivery behavior
- modify 342B / 342C / 342C2 upstream artifacts
- commit output artifacts

## Current Problem Summary

Current MinerU pilot runs in 342C and 342C2 failed before useful parse output was produced:

- `mineru_success_count = 0`
- `mineru_failed_count = 5`
- `empty_output_count = 5`
- failure text included `huggingface.co` SSL certificate verification errors
- `ready_for_342d = false`

This is not evidence that PDF parsing capability itself is broken.
The dominant failure point is MinerU model initialization and remote model access during startup.

## Confirmed Environment Facts

Manual inspection showed:

- main conda env: `mineru_new`
- `python = D:\anaconda\envs\mineru_new\python.exe`
- `requests` came from the conda env
- `urllib3` and `certifi` were polluted by user site-packages under:
  `C:\Users\哥哥\AppData\Roaming\Python\Python312\site-packages`
- `ENABLE_USER_SITE = True`
- `huggingface_hub = 1.18.0`

This is unsafe because current MinerU dependencies also rely on `transformers` and `tokenizers` constraints that require `huggingface_hub < 1.0`.

## Why `PYTHONNOUSERSITE=1` Matters

`PYTHONNOUSERSITE=1` prevents Python from loading user-level packages from `AppData\Roaming\Python\Python312\site-packages`.

Without this guard:

- conda env packages can be silently mixed with user-site packages
- SSL stack pieces such as `urllib3` and `certifi` may come from the wrong location
- package resolution becomes non-reproducible
- environment debugging becomes misleading

## Why `huggingface_hub 1.18.0` Is Unsafe Here

The current MinerU-related stack still depends on:

- `transformers 4.52.4` requiring `huggingface-hub < 1.0`
- `tokenizers 0.21.4` requiring `huggingface-hub < 1.0`

So `huggingface_hub 1.18.0` is outside the expected compatibility range.

For this repair task, the safe target is:

- `huggingface_hub == 0.36.2`

## Why `verify=False` Is Not an Acceptable Primary Fix

Disabling SSL verification is not a safe formal fix because it:

- weakens transport security
- hides real certificate or trust-store problems
- makes the environment harder to audit
- is not suitable as a stable benchmark or production-adjacent repair pattern

For 342C4, SSL must be fixed by:

- using the correct `certifi` bundle inside `mineru_new`
- preventing user-site pollution
- testing the official HuggingFace endpoint first
- falling back to a mirror endpoint only when needed

## New Files

- `docs/codex_tasks/342C4_mineru_new_env_repair_ssl_fix.md`
- `tools/repair_mineru_new_env_342c4.ps1`
- `tools/check_mineru_new_env_342c4.ps1`
- `datefac/benchmark/mineru_env_repair_notes_342c4.py`
- `tests/benchmark/test_mineru_env_repair_notes_342c4.py`

## Repair Script

`tools/repair_mineru_new_env_342c4.ps1`

This script must:

1. require the user to already be in `conda activate mineru_new`
2. set session guards:
   - `PYTHONNOUSERSITE=1`
   - `PIP_USER=0`
3. print current Python and pip information
4. print pip config
5. force-reinstall only the safe dependency set:
   - `requests`
   - `urllib3<3`
   - `certifi`
   - `idna`
   - `charset-normalizer`
   - `sniffio`
   - `huggingface_hub==0.36.2`
6. verify that `requests / urllib3 / certifi / huggingface_hub` are no longer coming from the user site directory
7. set:
   - `REQUESTS_CA_BUNDLE`
   - `SSL_CERT_FILE`
8. test official HuggingFace access first
9. if official access fails, test `HF_ENDPOINT=https://hf-mirror.com`
10. persist only safe env vars with `conda env config vars set`
11. instruct the user to deactivate and reactivate the environment
12. run `mineru --help`
13. print the recommended lab command:

```powershell
mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true
```

## Check Script

`tools/check_mineru_new_env_342c4.ps1`

This script is check-only and must not repair anything.

It must report:

- current conda env
- python path
- pip path
- `ENABLE_USER_SITE`
- `requests` path
- `urllib3` path
- `certifi` path
- `huggingface_hub` version
- `REQUESTS_CA_BUNDLE`
- `SSL_CERT_FILE`
- `HF_ENDPOINT`
- masked proxy values
- official HuggingFace API check result
- HF mirror API check result
- whether `mineru --help` runs

It must also output actionable suggestions when:

- user-site pollution is detected
- `urllib3` is missing
- `huggingface_hub >= 1.0`
- official HF fails but mirror succeeds
- both official and mirror fail

## Python Notes File

`datefac/benchmark/mineru_env_repair_notes_342c4.py`

This file is intentionally lightweight.
It only stores safe constants and explanatory notes for this repair task.
It does not perform real environment mutation.

## Validation

```powershell
python -m py_compile datefac\benchmark\mineru_env_repair_notes_342c4.py tests\benchmark\test_mineru_env_repair_notes_342c4.py

python -m pytest tests\benchmark\test_mineru_env_repair_notes_342c4.py -q
```

Tests must not:

- make real HuggingFace network calls
- mutate the real conda environment

## Manual Execution Order

```powershell
conda activate mineru_new

cd D:\_datefac

powershell -ExecutionPolicy Bypass -File tools\repair_mineru_new_env_342c4.ps1

conda deactivate
conda activate mineru_new

powershell -ExecutionPolicy Bypass -File tools\check_mineru_new_env_342c4.ps1
```

If the check passes, then run:

```powershell
mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true
```

If the MinerU lab command succeeds, then DateFac can retry:

```powershell
python tools\run_mineru_pilot_retry_verified_env_342c2.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --mineru-342c-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --output-dir D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix --limit 5 --mineru-command "mineru"
```

or continue with a later lab-bridge retry stage.

## Readiness Boundary

342C4 does not unlock 342D by itself.

342D must still remain blocked unless MinerU pilot retry produces at least one successful output.
