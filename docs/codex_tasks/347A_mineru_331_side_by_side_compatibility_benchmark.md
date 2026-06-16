# 347A MinerU 3.3.1 Side-by-Side Compatibility Benchmark

## Goal

Implement and run `347A MinerU 3.3.1 Side-by-Side Compatibility Benchmark`.

The root guide has already been committed as:

```text
mineru_3.3.1.md
```

That guide is the source of truth for the local MinerU 3.3.1 environment, commands, restrictions, output structure, and DateFac integration doctrine.

347A must answer:

> Can MinerU 3.3.1 run stably in the isolated `mineru331_gpu` environment, and do its pipeline / hybrid medium / hybrid high outputs improve or remain compatible with DateFac's current JSON, Markdown, image evidence binding, and downstream audit pipeline?

This task is a side-by-side compatibility benchmark. It must not replace the current DateFac parser and must not mutate the current 345D/346B/346B4/346B5/346B5Q chain.

---

## Required guide

Read first:

```text
mineru_3.3.1.md
```

The guide defines the mission as a DateFac MinerU 3.3.1 sidecar compatibility validation, not an immediate mainline upgrade. It explicitly requires checking whether MinerU 3.3.1 can run stably, comparing `pipeline / hybrid medium / hybrid high`, validating JSON / Markdown / image evidence binding compatibility, and deciding whether 347B Binding Adapter Fix is needed.

---

## Strategic alignment

Follow:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
mineru_3.3.1.md
```

Required doctrine:

- MinerU 3.3.1 is a sidecar / future extraction candidate.
- Do not directly replace the current parser.
- Do not pollute the current DateFac recovery/audit chain.
- Do not write into existing 345D / 346B / 346B4 / 346B5 / 346B5Q outputs.
- Do not rerun full production extraction.
- Do not do full 5558-row recovery based on new MinerU output.
- Do not mutate official normalization rules or alias assets.
- Do not modify protected dirty files.
- Treat this as a benchmark and compatibility audit, not an adoption migration.

---

## Known local MinerU 3.3.1 environment

Use the environment documented in `mineru_3.3.1.md`:

```text
conda env: mineru331_gpu
working dir: E:\mineru_lab
isolated dir: E:\mineru331
HF cache: E:\mineru331\hf_cache
downloads: E:\mineru331\downloads
smoke input: E:\mineru331\smoke_input_fresh_20260615_215912
existing smoke high output: E:\mineru331\smoke_output_fresh_hybrid_high_gpu_20260616
```

Expected CUDA check:

```text
torch: 2.7.1+cu126
torchvision: 0.22.1+cu126
torch.cuda.is_available(): True
torch.version.cuda: 12.6
```

If CUDA is unavailable, skip hybrid high and mark `hybrid_high_status = CUDA_UNAVAILABLE_SKIPPED`. Do not force GPU runs.

---

## Startup commands

Every new PowerShell session must run:

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

Do not proceed with hybrid high unless `Test-Path` returns `True` and CUDA is available.

---

## Input set

Use the smoke input set already documented:

```text
E:\mineru331\smoke_input_fresh_20260615_215912
```

Also create an input manifest in the 347A output directory containing:

- PDF filename
- file size
- SHA256
- page count if cheaply available
- whether the PDF was already used in old MinerU / 346A / 346A2 evidence work if inferable

Do not use a large all-PDF corpus. This is not full batch mode.

---

## Output directory

Write only under:

```text
D:\_datefac\output\mineru_331_compatibility_benchmark_347a
```

Recommended structure:

```text
D:\_datefac\output\mineru_331_compatibility_benchmark_347a\
  input_manifest\
  old_mineru_reference\
  mineru331_pipeline\
  mineru331_hybrid_medium\
  mineru331_hybrid_high\
  comparison_reports\
  evidence_binding_audit\
```

Do not write into:

```text
D:\_datefac\output\345D*
D:\_datefac\output\346B*
D:\_datefac\output\346B4*
D:\_datefac\output\346B5*
D:\_datefac\output\larger_expansion_qa_audit_346b5q
```

Do not overwrite old MinerU outputs.

---

## MinerU runs

Run three modes where possible.

### 1. pipeline baseline

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o D:\_datefac\output\mineru_331_compatibility_benchmark_347a\mineru331_pipeline -b pipeline
```

### 2. hybrid medium

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o D:\_datefac\output\mineru_331_compatibility_benchmark_347a\mineru331_hybrid_medium -b hybrid-engine --effort medium
```

### 3. hybrid high

Only run if CUDA is available:

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o D:\_datefac\output\mineru_331_compatibility_benchmark_347a\mineru331_hybrid_high -b hybrid-engine --effort high
```

Successful hybrid high logs should include, if available:

```text
Using lmdeploy-engine as the inference engine for VLM
Lmdeploy device is: cuda
lmdeploy backend is: turbomind
Hybrid processing window
```

If using the long-running API service is more stable, follow the `mineru_3.3.1.md` API mode instructions, but still write outputs under the 347A benchmark directory.

---

## Evidence fixation

For each mode output, generate:

- file manifest
- SHA256 list
- file extension count
- output size MB
- runtime seconds
- run status
- observed errors/warnings
- mineru version
- backend
- effort
- CUDA status

Suggested PowerShell for each output root:

```powershell
$out = "D:\_datefac\output\mineru_331_compatibility_benchmark_347a\mineru331_hybrid_high"
$manifestOut = "${out}_manifest.txt"
$hashOut = "${out}_sha256.txt"
Get-ChildItem $out -Recurse -File | Sort-Object FullName | Select-Object FullName, Length, LastWriteTime | Out-File $manifestOut -Encoding utf8
Get-ChildItem $out -Recurse -File | Sort-Object FullName | Get-FileHash -Algorithm SHA256 | Out-File $hashOut -Encoding utf8
Get-ChildItem $out -Recurse -File | Group-Object Extension | Select-Object Name, Count
(Get-ChildItem $out -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
```

---

## Compatibility metrics

For each mode, compute and report:

- processed_pdf_count
- failed_pdf_count
- runtime_seconds
- output_size_mb
- total_file_count
- markdown_file_count
- content_list_json_count
- content_list_v2_json_count
- middle_json_count
- model_json_count
- image_dir_count
- image_file_count
- table_image_count
- chart_image_count if distinguishable
- page_image_count if distinguishable
- table_block_count
- image_block_count
- text_block_count
- formula_block_count if present
- block_type_distribution
- image_path_reference_count_in_md
- image_path_reference_count_in_json
- broken_image_reference_count
- missing_content_list_count
- missing_markdown_count
- json_parse_error_count
- html_table_parse_error_count if table html exists
- suspicious_empty_table_count
- suspicious_tiny_image_count
- suspicious_huge_image_count
- max_single_pdf_runtime_seconds
- timeout_or_hang_count

---

## DateFac evidence binding audit

Build a sidecar compatibility audit against DateFac expectations.

Compare against old/current MinerU reference if available from previous 346A/346A2 or smoke output.

At minimum report:

```text
old_image_bound_count
old_json_md_context_bound_count
old_image_missing_count
old_ambiguous_image_candidate_count
```

and for each MinerU 3.3.1 mode:

```text
mode_image_bound_count
mode_json_md_context_bound_count
mode_image_missing_count
mode_ambiguous_image_candidate_count
mode_binding_adapter_compatible
mode_binding_breakage_count
mode_binding_notes
```

If old binding inputs are unavailable, report `old_reference_availability = false` and still perform structural compatibility analysis.

Do not silently claim improvement without a comparable old reference.

---

## Decision logic

347A must output one decision:

```text
KEEP_OLD_MINERU_FOR_CURRENT_CHAIN
ADOPT_MINERU_331_FOR_FUTURE_EXTRACTION
ADOPT_MINERU_331_AFTER_BINDING_ADAPTER_FIX
RUN_MORE_HIGH_EFFORT_SAMPLES_BEFORE_DECISION
```

Recommended interpretation:

- Use `KEEP_OLD_MINERU_FOR_CURRENT_CHAIN` if outputs are unstable, incomplete, or incompatible.
- Use `ADOPT_MINERU_331_FOR_FUTURE_EXTRACTION` only if structural outputs are stable and DateFac binding compatibility is strong enough without adapter changes.
- Use `ADOPT_MINERU_331_AFTER_BINDING_ADAPTER_FIX` if parsing quality looks better but paths/schema/block conventions require adapter work.
- Use `RUN_MORE_HIGH_EFFORT_SAMPLES_BEFORE_DECISION` if smoke sample is too small or high effort results are incomplete.

Even if adoption is recommended, current 345D/346B/346B4/346B5 outputs must remain frozen.

---

## Required outputs

Write under:

```text
D:\_datefac\output\mineru_331_compatibility_benchmark_347a
```

Generate:

- `mineru_331_compatibility_benchmark_347a_manifest.json`
- `mineru_331_compatibility_benchmark_347a_input_manifest.json`
- `mineru_331_compatibility_benchmark_347a_run_summary.json`
- `mineru_331_compatibility_benchmark_347a_mode_comparison.csv`
- `mineru_331_compatibility_benchmark_347a_mode_comparison.json`
- `mineru_331_compatibility_benchmark_347a_file_type_counts.csv`
- `mineru_331_compatibility_benchmark_347a_block_type_distribution.csv`
- `mineru_331_compatibility_benchmark_347a_image_reference_audit.csv`
- `mineru_331_compatibility_benchmark_347a_json_schema_audit.csv`
- `mineru_331_compatibility_benchmark_347a_table_artifact_audit.csv`
- `mineru_331_compatibility_benchmark_347a_evidence_binding_audit.csv`
- `mineru_331_compatibility_benchmark_347a_decision_report.json`
- `mineru_331_compatibility_benchmark_347a_executive_summary.md`
- `mineru_331_compatibility_benchmark_347a_artifact_index.md`
- `mineru_331_compatibility_benchmark_347a_next_plan.md`

---

## Manifest metrics

Manifest must include:

```text
decision
input_stage = MINERU_331_SIDECAR_COMPATIBILITY_BENCHMARK_347A
qa_fail_count
no_write_back_proof_passed = true
mineru331_env_name = mineru331_gpu
cuda_available
pipeline_run_status
hybrid_medium_run_status
hybrid_high_run_status
processed_pdf_count
failed_pdf_count
mode_count_completed
old_reference_availability
best_mode_by_runtime
best_mode_by_structural_completeness
best_mode_by_binding_compatibility
old_image_bound_count
old_json_md_context_bound_count
old_image_missing_count
old_ambiguous_image_candidate_count
pipeline_image_bound_count
pipeline_json_md_context_bound_count
pipeline_image_missing_count
pipeline_ambiguous_image_candidate_count
hybrid_medium_image_bound_count
hybrid_medium_json_md_context_bound_count
hybrid_medium_image_missing_count
hybrid_medium_ambiguous_image_candidate_count
hybrid_high_image_bound_count
hybrid_high_json_md_context_bound_count
hybrid_high_image_missing_count
hybrid_high_ambiguous_image_candidate_count
binding_adapter_required
recommended_next_step
live_vlm_call_count
ocr_rerun_count
mineru_rerun_scope = smoke_or_benchmark_only
official_rules_modified = false
official_alias_assets_modified = false
formal_export_generated = false
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
upstream_data_mutated = false
protected_dirty_files_touched = false
```

`live_vlm_call_count` means DateFac LLM/VLM API calls. MinerU hybrid high may use its local VLM engine, but this must be recorded separately as `mineru_local_vlm_engine_used = true/false`.

---

## Allowed local files

If code is needed, only add/modify:

- `datefac/benchmark/mineru_331_compatibility_benchmark_347a.py`
- `datefac/benchmark/mineru_331_compatibility_benchmark_347a_report.py`
- `tools/run_mineru_331_compatibility_benchmark_347a.py`
- `tests/benchmark/test_mineru_331_compatibility_benchmark_347a.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The root `mineru_3.3.1.md` has already been created and should not be rewritten unless a clear typo/command correction is required.

---

## Forbidden

Do not:

- modify `D:\_datefac` protected dirty files;
- modify `D:\_datefac_worktrees\346b4r` 346B source files;
- mutate old MinerU outputs;
- mutate 345D/346B/346B4/346B5/346B5Q outputs;
- write into existing output directories except `D:\_datefac\output\mineru_331_compatibility_benchmark_347a`;
- delete old MinerU envs or caches;
- do full batch mode;
- commit/push/merge automatically;
- change official normalization rules;
- change official alias assets;
- generate formal client delivery outputs;
- open formal/client/production gates;
- use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`.

---

## Validation

If benchmark helper code is created, run:

```powershell
python -m py_compile datefac\benchmark\mineru_331_compatibility_benchmark_347a.py datefac\benchmark\mineru_331_compatibility_benchmark_347a_report.py tools\run_mineru_331_compatibility_benchmark_347a.py tests\benchmark\test_mineru_331_compatibility_benchmark_347a.py
python -m pytest tests\benchmark\test_mineru_331_compatibility_benchmark_347a.py -q
```

Then run the real benchmark wrapper, for example:

```powershell
python tools\run_mineru_331_compatibility_benchmark_347a.py --input-dir E:\mineru331\smoke_input_fresh_20260615_215912 --output-dir D:\_datefac\output\mineru_331_compatibility_benchmark_347a --old-reference-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2 --run-pipeline true --run-hybrid-medium true --run-hybrid-high true
```

If MinerU runs are already available and should not be rerun, support `--reuse-existing-runs true` with explicit mode output dirs.

---

## Completion report

Report:

1. Files changed.
2. Whether `mineru_3.3.1.md` was read and used.
3. Environment verification result.
4. Which MinerU modes were run or reused.
5. Runtime and status by mode.
6. Output directory.
7. Processed PDF count and failed PDF count.
8. File count and output size by mode.
9. JSON/Markdown/image artifact availability by mode.
10. Block type distribution by mode.
11. Image reference audit result.
12. Table artifact audit result.
13. DateFac evidence binding compatibility result.
14. Old vs MinerU 3.3.1 binding metrics if comparable.
15. Binding adapter required flag.
16. Decision.
17. Recommended next step.
18. No-touch confirmation for 345D/346B/346B4/346B5/346B5Q/protected dirty files.
19. `git status -sb`.
