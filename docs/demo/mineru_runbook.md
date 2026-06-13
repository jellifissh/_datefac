# MinerU Runbook

## Purpose

This runbook explains how MinerU fits into DateFac and where to look before running MinerU-related tasks.
It is intended for new contributors.
It documents the current known workflow.
It does not guarantee that every command is safe to rerun in every context.

## MinerU In DateFac

MinerU is the current primary parser candidate for the real-PDF benchmark path.
In the current DateFac mainline, MinerU is mainly used as:

- a parser benchmark and evidence source
- an upstream input to the MinerU-first / table-first chain
- a source of Markdown and structured JSON artifacts that later table-first tasks consume

MinerU outputs are benchmark evidence.
They are not formal client delivery artifacts.

## Why The Mainline Is MinerU-First / Table-First

The current effective benchmark route prefers:

1. parse real PDFs with MinerU
2. inspect MinerU outputs such as `.md` and `content_list.json`
3. extract table-first evidence from those outputs
4. keep later trust/review/export steps sidecar and no-write-back

This replaced the older direct text-candidate route as the effective route for the current benchmark chain.

## Current Boundary

Current known benchmark state from repo docs and outputs:

- `342C` first pilot run failed largely because of SSL / HuggingFace / environment issues
- `342C2` verified-environment retry produced partial success
- `342C6` recovery rerun exists as a later bounded recovery step
- partial MinerU success is benchmark evidence only
- current docs explicitly warn not to treat benchmark outputs as production-ready

This runbook documents how the chain is organized.
It does not mean MinerU should be rerun by default.

## Where MinerU Inputs Usually Come From

There are two common contexts:

### Manual lab context

Known working local lab context from repo docs:

- conda env: `mineru_new`
- lab input dir: `E:\mineru_lab\input`
- lab output dir: `E:\mineru_lab\output_new`
- model cache dir: `E:\mineru_lab\models`

### DateFac benchmark context

DateFac benchmark tasks usually read PDF paths from prior task outputs, especially:

- `D:\_datefac\output\real_pdf_corpus_intake_342b`

In that path, PDF metadata and file paths are selected by a bounded benchmark task rather than by scanning arbitrary folders.

## Where MinerU Outputs Usually Go

Common benchmark output directories seen in this repo:

- `D:\_datefac\output\mineru_batch_parse_benchmark_342c`
- `D:\_datefac\output\mineru_pilot_retry_verified_env_342c2`
- `D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix`
- `D:\_datefac\output\mineru_pilot_network_recovery_342c6`

These task folders typically include:

- summary JSON
- QA JSON
- manifest JSON
- report Markdown
- workbook output
- `mineru_outputs/` raw parse subdirectories

## Project Files Related To MinerU

Runnable scripts:

- `tools/run_mineru_batch_parse_benchmark_342c.py`
- `tools/run_mineru_pilot_retry_verified_env_342c2.py`
- `tools/run_mineru_pilot_network_recovery_342c6.py`
- `tools/check_mineru_new_env_342c4.ps1`
- `tools/repair_mineru_new_env_342c4.ps1`
- `tools/mineru_new_runner.cmd`

Python modules:

- `datefac/benchmark/mineru_batch_parse_benchmark_342c.py`
- `datefac/benchmark/mineru_pilot_retry_verified_env_342c2.py`
- `datefac/benchmark/mineru_pilot_network_recovery_342c6.py`
- `datefac/benchmark/mineru_benchmark_runner.py`
- `datefac/mineru_body/`
- `datefac/parser/mineru_output_reader.py`

Task specs and history:

- `docs/codex_tasks/320*.md`
- `docs/codex_tasks/337A_mineru_first_real_pdf_intake.md`
- `docs/codex_tasks/337B_mineru_candidate_precision_calibration.md`
- `docs/codex_tasks/342A*.md`
- `docs/codex_tasks/342B*.md`
- `docs/codex_tasks/342C*.md`

## Recommended Pre-Run Checks

Before running any MinerU-related command, check:

1. Python environment
2. whether dependencies are installed
3. whether the input PDFs exist
4. whether the output directory is correct
5. whether rerunning would overwrite important prior results

Suggested checks from repo materials:

```powershell
conda activate mineru_new
where.exe mineru
python -c "import shutil; print(shutil.which('mineru'))"
Test-Path "D:\anaconda\envs\mineru_new\Scripts\mineru.exe"
Get-Process python,mineru -ErrorAction SilentlyContinue
```

Environment diagnosis helpers already present in the repo:

```powershell
powershell -ExecutionPolicy Bypass -File tools\check_mineru_new_env_342c4.ps1
powershell -ExecutionPolicy Bypass -File tools\repair_mineru_new_env_342c4.ps1
```

## Known Manual Lab Command

The repo contains a known working command pattern for manual MinerU validation:

```powershell
mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true
```

This is documented in the repo as a known working lab command.
It is not the same as a DateFac benchmark command reading 342B inputs.

## Known DateFac Benchmark Commands

### 342C pilot benchmark

```powershell
python tools\run_mineru_batch_parse_benchmark_342c.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --output-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --limit 5 --dry-run
```

Real invocation shape documented in the task:

```powershell
python tools\run_mineru_batch_parse_benchmark_342c.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --output-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --limit 5
```

### 342C2 verified-environment retry

```powershell
python tools\run_mineru_pilot_retry_verified_env_342c2.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --mineru-342c-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --output-dir D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix --limit 5 --mineru-command "D:/anaconda/envs/mineru_new/Scripts/mineru.exe"
```

### 342C6 network recovery rerun

```powershell
python tools\run_mineru_pilot_network_recovery_342c6.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --mineru-342c2-dir D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix --output-dir D:\_datefac\output\mineru_pilot_network_recovery_342c6 --mineru-command "D:/anaconda/envs/mineru_new/Scripts/mineru.exe"
```

### Helper command wrapper

The repo also contains:

```text
tools/mineru_new_runner.cmd
```

It activates `mineru_new` and forwards arguments to `mineru`.

`TODO: verify command before running`

## How To Inspect Results After Running

After a MinerU-related task finishes, inspect:

1. summary JSON
2. QA JSON
3. report Markdown
4. workbook output
5. `mineru_outputs/` structured files

Typical file names seen in this repo:

- `*_summary.json`
- `*_qa.json`
- `*_report.md`
- `*.xlsx`

Typical structured raw outputs inside `mineru_outputs/` may include:

- `.md`
- `*_content_list.json`
- `*_middle.json`
- `*_model.json`
- `images/`

DateFac guidance in repo docs prefers consuming:

- Markdown
- `content_list.json`
- table-related structured JSON

Do not treat raw images as the primary downstream signal by default.

## Common Failure Situations

### Input file not found

Likely causes:

- wrong `--corpus-342b-dir`
- upstream workbook or manifest missing
- PDF path moved outside the expected benchmark artifact

### Output is empty

Likely causes:

- MinerU command failed before useful parse output
- model initialization failed
- path or permission problem
- parse produced only partial artifacts

### OCR or table recognition looks empty

Likely causes:

- parser failed on the PDF layout
- output directory is present but lacks `.md` or expected JSON files
- the run completed with empty or suspicious output and needs artifact audit review

### Wrong disk or path

The repo contains both `D:\_datefac` and known manual lab paths on `E:\mineru_lab`.
Be careful not to confuse:

- DateFac benchmark input/output paths on `D:`
- manual MinerU lab validation paths on `E:`

### CPU mode is slow

The repo warns that MinerU may appear silent while still processing.
Slow runs are not necessarily stuck runs.

### Dependency or model file missing

Known documented issues include:

- SSL certificate verify failed
- official HuggingFace unavailable
- mirror unavailable
- user site-package pollution
- incompatible `huggingface_hub >= 1.0`
- base env cannot find `mineru`
- `mineru_new` env missing runtime pieces needed by the runner

## Relationship To The Table-First Benchmark Chain

MinerU parsing is upstream evidence for the later table-first chain.
In the current repo history, later tasks consume MinerU outputs rather than skipping directly to text-only candidate extraction.

That means:

- MinerU parse outputs matter as evidence
- later benchmark tasks should inspect structured parse artifacts first
- parser conclusions should be evidence-driven, not guessed from downstream symptoms alone

## Current Task Boundary Reminder

This runbook is documentation only.
It does not run MinerU.
It does not repair the environment.
It does not rerun any benchmark.

If a command needs to be executed later, verify it against the current task doc and current environment first.

## Safety Boundary

- Do not delete old outputs by default.
- Do not overwrite completed stage outputs by default.
- Do not commit large generated MinerU outputs to Git.
- Do not rerun MinerU unless the user explicitly asks for it.
- Do not treat partial benchmark outputs as production readiness.
