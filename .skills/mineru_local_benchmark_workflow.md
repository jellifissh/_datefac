# Skill: MinerU Local Benchmark Workflow

## Purpose
This is the local MinerU benchmark workflow.
It is for parser benchmarking and evidence collection, not production integration.

## Environment Split
- base / DateFac env:
  - run DateFac runner
  - run pandas / Excel / sidecar / report logic
- `mineru_new`:
  - run MinerU CLI
  - load models
  - parse PDFs
- Do not stuff the full DateFac dependency stack into `mineru_new`
- Do not call `mineru` from base unless PATH is explicitly correct

## Verified MinerU Environment
- conda env = `mineru_new`
- lab dir = `E:\mineru_lab`
- lab input = `E:\mineru_lab\input`
- lab output = `E:\mineru_lab\output_new`
- model/cache dir = `E:\mineru_lab\models`
- known working command:

```powershell
mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true
```

## DateFac Benchmark Invocation
Recommended command:

```powershell
python tools\run_mineru_pilot_retry_verified_env_342c2.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --mineru-342c-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --output-dir D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix --limit 5 --mineru-command "D:/anaconda/envs/mineru_new/Scripts/mineru.exe"
```

Notes:
- This command reads pilot-set PDFs from the `342B` corpus intake workbook / manifest
- It does not read directly from `E:\mineru_lab\input`
- `E:\mineru_lab\input` is only for manual MinerU validation
- The actual PDF paths come from `342B` `file_path`
- Output goes to:
  - `D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix\mineru_outputs`

## Output Structure
Typical MinerU parse package may include:
- `auto/`
- `images/`
- `.md`
- `*_content_list.json`
- `*_middle.json`
- `*_model.json`
- `*_layout.pdf`
- `*_origin.pdf`
- `*_span.pdf`

DateFac should prefer consuming:
- markdown
- `content_list.json`
- table-related structured JSON

Do not prioritize raw images as the main downstream signal.

## Current Known Status
- MinerU manual workflow verified
- `342C2` after env fix generated real parse artifacts for pilot PDFs
- `342C2` summary currently shows `3/5` success and `2/5` failed or empty
- `ready_for_342d = conditional`
- Must inspect failed retry rows before parser ensemble compare
- Do not claim full MinerU benchmark pass

## Common Failure Modes
- SSL certificate verify failed
- HuggingFace / hf-mirror inaccessible
- user site-packages pollution from `C:\Users\哥哥\AppData\Roaming\Python\Python312\site-packages`
- `huggingface_hub >= 1.0` incompatible with current `transformers / tokenizers`
- base env cannot find `mineru`
- `mineru_new` env missing `pandas` when running DateFac runner directly
- Windows subprocess path issue for `.exe` / `.cmd`
- runner may appear silent while MinerU is processing

## Debug Commands
```powershell
conda activate mineru_new
where.exe mineru
python -c "import shutil; print(shutil.which('mineru'))"
Test-Path "D:\anaconda\envs\mineru_new\Scripts\mineru.exe"
Get-Process python,mineru -ErrorAction SilentlyContinue
Get-ChildItem D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix\mineru_outputs -Recurse | Select-Object -First 50
Get-Content D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix\mineru_pilot_retry_verified_env_342c2_summary.json
```

## Safety Boundaries
- do not modify production pipeline/parser/extraction/delivery
- do not claim `client_ready`
- do not claim `production_ready`
- do not treat partial MinerU output as `342D` readiness
- do not submit output artifacts
- do not enter `342D` until failed retry rows are inspected and `qa_fail_count = 0`

