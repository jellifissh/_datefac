# Skill: MinerU Local Benchmark Workflow

## Purpose

This skill defines MinerU local benchmark boundaries.

Current status after the Agent pivot:

```text
MinerU is a sidecar extractor candidate, not the active 348A mainline.
```

Use this skill only when a task explicitly touches MinerU, parser benchmarking, extraction artifact comparison, or evidence binding.

Do not apply this skill to ordinary `datefac_agent` Excel intake audit tasks.

## Mainline Boundary After 348 Pivot

Current active mainline:

```text
DateFac Agent / extraction audit workflow
```

348A-style work must not run MinerU.

For 348A:

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

MinerU outputs may be used only as pre-existing external extraction artifacts or future sidecar evidence candidates, not as a required step in the Excel intake audit pilot.

## Legacy MinerU Environment

Legacy benchmark environment:

```text
conda env = mineru_new
lab dir = E:\mineru_lab
lab input = E:\mineru_lab\input
lab output = E:\mineru_lab\output_new
model/cache dir = E:\mineru_lab\models
```

Legacy known working command:

```powershell
conda activate mineru_new
mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true
```

Legacy DateFac benchmark invocation:

```powershell
python tools\run_mineru_pilot_retry_verified_env_342c2.py --corpus-342b-dir D:\_datefac\output\real_pdf_corpus_intake_342b --mineru-342c-dir D:\_datefac\output\mineru_batch_parse_benchmark_342c --output-dir D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix --limit 5 --mineru-command "D:/anaconda/envs/mineru_new/Scripts/mineru.exe"
```

This legacy route remains reference-only unless the task explicitly revisits old MinerU benchmarks.

## MinerU 3.3.1 Sidecar Candidate

The current newer MinerU environment is documented in:

```text
mineru_3.3.1.md
```

Read that file before any future MinerU 3.3.1 task.

Verified newer environment:

```text
conda env: mineru331_gpu
working dir: E:\mineru_lab
isolated dir: E:\mineru331
model cache: E:\mineru331\hf_cache
download dir: E:\mineru331\downloads
```

Key dependency expectation:

```text
torch: 2.7.1+cu126
torchvision: 0.22.1+cu126
torchaudio: 2.7.1+cu126
CUDA: 12.6
```

Preflight for a new PowerShell:

```powershell
conda activate mineru331_gpu

$env:HF_ENDPOINT="https://hf-mirror.com"
$env:HF_HOME="E:\mineru331\hf_cache"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
$env:HF_HUB_DOWNLOAD_TIMEOUT="300"
$env:HF_HUB_ETAG_TIMEOUT="120"

$env:CUDA_PATH="D:\anaconda\envs\mineru331_gpu\Library"
$env:PATH="$env:CUDA_PATH\bin;$env:PATH"

Test-Path "$env:CUDA_PATH\bin"
python -c "import torch, torchvision; print(torch.__version__); print(torchvision.__version__); print(torch.cuda.is_available()); print(torch.version.cuda)"
mineru --version
mineru --help
```

If `torch.cuda.is_available()` is not `True`, do not run hybrid high.

## MinerU 3.3.1 Run Modes

### pipeline baseline

Use for installation smoke tests and stable low-cost baseline:

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o E:\mineru331\smoke_output_fresh_pipeline_20260616 -b pipeline
```

### hybrid medium

Use as future ordinary PDF extraction candidate after compatibility validation:

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o E:\mineru331\smoke_output_fresh_hybrid_medium_20260616 -b hybrid-engine --effort medium
```

Notes:

- medium is speed-oriented;
- it may disable image/chart analysis;
- it cannot directly replace old pipelines without JSON / Markdown / image path compatibility checks.

### hybrid high

Use only for complex financial PDFs, chart/table image recovery, or high-value sidecar reruns:

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o E:\mineru331\smoke_output_fresh_hybrid_high_gpu_20260616 -b hybrid-engine --effort high
```

Expected success signals may include:

```text
Using lmdeploy-engine as the inference engine for VLM
Lmdeploy device is: cuda
lmdeploy backend is: turbomind
Hybrid processing window
```

Do not use hybrid high as a default full-batch path.

## Recommended Future Service Mode

For future sidecar integration, prefer a persistent service instead of spawning MinerU per file:

```powershell
conda activate mineru331_gpu

$env:HF_ENDPOINT="https://hf-mirror.com"
$env:HF_HOME="E:\mineru331\hf_cache"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
$env:HF_HUB_DOWNLOAD_TIMEOUT="300"
$env:HF_HUB_ETAG_TIMEOUT="120"

$env:CUDA_PATH="D:\anaconda\envs\mineru331_gpu\Library"
$env:PATH="$env:CUDA_PATH\bin;$env:PATH"

mineru-api --host 127.0.0.1 --port 18080 --enable-vlm-preload true
```

This is for future sidecar tasks, not 348A.

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

- Markdown;
- `content_list.json`;
- table-related structured JSON;
- explicit image/table crop evidence only when needed.

Do not prioritize raw images as the main downstream signal.

## Current Known Status

Legacy `342C2` status:

- manual MinerU workflow verified;
- `342C2` after env fix generated real parse artifacts for pilot PDFs;
- `342C2` summary showed partial success, not full pass;
- do not claim full legacy MinerU benchmark pass.

MinerU 3.3.1 status:

- side-by-side compatibility benchmark is documented separately;
- treat it as a future sidecar candidate;
- do not let MinerU 3.3.1 output contaminate current Agent audit chain without adapter validation.

## Common Failure Modes

- SSL certificate verify failed;
- HuggingFace / hf-mirror inaccessible;
- user site-packages pollution from `C:\Users\哥哥\AppData\Roaming\Python\Python312\site-packages`;
- incompatible `huggingface_hub` / `transformers` / `tokenizers` versions;
- base env cannot find `mineru`;
- wrong conda env;
- CUDA path missing;
- Windows subprocess path issues for `.exe` / `.cmd`;
- runner may appear silent while MinerU is processing.

## Safety Boundaries

- do not modify production pipeline/parser/extraction/delivery;
- do not claim `client_ready`;
- do not claim `production_ready`;
- do not treat partial MinerU output as full benchmark pass;
- do not submit bulk output artifacts;
- do not rerun old MinerU chains unless the task explicitly requests it;
- do not run MinerU inside 348A Excel intake audit tasks;
- do not treat MinerU 3.3.1 as a drop-in replacement before compatibility benchmark and binding adapter review.
