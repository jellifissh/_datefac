# NEXT CODEX TASK

## task_title
Wire guarded sandbox execute mode for Stage 1 safe runner

## project
D:\_datefac

## current_status
The scoped safe non-vision Stage 1 runner has been implemented and committed.

Latest committed runner:
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py

Latest known result:
- py_compile_status = PASS
- help_status = PASS
- dry_run_status = DRY_RUN_BLOCKED_NO_SAFE_FULL_PIPELINE
- current_delivery_status = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production data untouched: yes
- factory_core / marker / surya / vision / PaddleOCR / model downloads avoided: yes

Important code state:
- The runner has argument parsing, manifest loading, strict-scope checks, baseline guard, dry-run reports, and safety entrypoint inventory.
- Execute mode is intentionally blocked because safe end-to-end non-vision wiring is not implemented yet.
- The code currently has `safe_full_pipeline_ready = False` and returns BLOCKED for execute-mode.

Goal now:
Add guarded execute-mode wiring, but only for a sandbox/trial directory first. Do not modify production delivery_package data yet.

## goal
Extend `tools/run_stage1_safe_nonvision_pipeline.py` so it can attempt a controlled sandbox execute run for exactly the three Stage 1 samples, while keeping production delivery files untouched.

Primary local reports:
- D:\_datefac\output\delivery_package\25_stage1_safe_runner_execute_wiring_report.md
- D:\_datefac\output\delivery_package\25_stage1_safe_runner_execute_wiring_report.xlsx
- D:\_datefac\output\delivery_package\26_stage1_sandbox_execute_trial_evaluation.md
- D:\_datefac\output\delivery_package\26_stage1_sandbox_execute_trial_evaluation.xlsx

Sandbox output root:
- D:\_datefac\output\_stage1_safe_runner_trial

Sandbox delivery dir:
- D:\_datefac\output\_stage1_safe_runner_trial\delivery_package

Do not write Stage 1 trial results into the production delivery dir except for the 25/26 local report files under production delivery_package.

## selected_stage1_samples
The runner must support exactly these selected PDFs in the manifest used for validation:

1. H3_AP202605141822317484_1.pdf
   company: 三鑫医疗
   approved pages: 1, 4, 5

2. H3_AP202605121822223662_1.pdf
   company: 冠豪高新
   approved pages: 2, 3

3. H3_AP202605141822318060_1.pdf
   company: 科锐国际
   approved pages: 5
   ignored page: 6

Baseline regression guard:
- H3_AP202605091822098939_1.pdf
Do not process as a new Stage 1 sample.

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any model.
4. Do not modify production delivery files:
   - 01_自动可信核心指标.xlsx
   - 02_人工复核指标队列.xlsx
   - 02A_人工年份修正覆盖表.xlsx
   - 06_最终核心财务指标.xlsx
5. Do not rebuild the production delivery_package in this task.
6. Do not process baseline 091 as a Stage 1 sample.
7. Do not commit output artifacts.
8. Worklog must be English only and UTF-8.
9. If safe sandbox execute cannot be wired without unsafe modules, stop with explicit status:
   - BLOCKED_SANDBOX_EXECUTE_UNSAFE
   or
   - BLOCKED_SAFE_COMPONENTS_MISSING
10. Do not silently fake success. If only dry-run is possible, report that clearly.

## implementation_requirements

### 1. Add sandbox execute arguments
Extend `run_stage1_safe_nonvision_pipeline.py` with safe trial arguments:
- `--trial-root D:\_datefac\output\_stage1_safe_runner_trial`
- `--sandbox-delivery-dir D:\_datefac\output\_stage1_safe_runner_trial\delivery_package`
- `--execute-sandbox`
- `--allow-production-write` default false and not used in this task

Rules:
- `--execute` without `--execute-sandbox` and without `--allow-production-write` must be blocked.
- Production delivery dir must be read-only in this task.
- Sandbox output root must be created if absent.
- Existing sandbox root may be backed up or timestamped before reuse.

### 2. Component discovery and safety audit
Inspect existing scripts/modules and classify them:
- safe_to_execute
- safe_probe_only
- downstream_only
- unsafe_import
- unsafe_runtime
- missing_scope_support

At minimum inspect these if present:
- tools/probe_pdf_tables.py
- tools/probe_pdfplumber_profiles.py
- tools/probe_extractors.py
- tools/build_manual_review_queue.py
- tools/validate_financial_metric_values.py
- tools/build_delivery_package.py
- tools/apply_manual_review_corrections.py
- tools/check_delivery_state.py
- financial_standardizer.py
- any relevant table splitter / pdfplumber / asset-generation modules

Do not import unsafe modules. Prefer static source scan first.
Forbidden strings or imports include:
- marker
- surya
- PaddleOCR
- paddleocr
- vision
- model.safetensors
- datalab
- transformers model download

If a file has forbidden imports only inside optional guarded code, document it and do not call that path.

### 3. Safe sandbox execute plan
The runner should attempt to build a safe staged command plan using only safe components.

Possible stages:
1. pdfplumber-only raw table extraction / probe-to-raw-table asset generation
2. table post-processing / glued splitter if safe
3. core metric standardization if safe and scope-able
4. delivery package build into sandbox delivery dir if safe and scope-able
5. manual correction apply only inside sandbox delivery dir if supported
6. delivery check on sandbox delivery dir if supported

If an existing script does not support custom output root / delivery dir / scoped PDF list, do not use it for execute; mark it as missing_scope_support.

### 4. Minimum useful sandbox execution
If full 01/02/05/06 generation cannot be wired safely yet, implement a minimum useful sandbox execution path:
- run pdfplumber-only table extraction/probe for the three PDFs into sandbox asset folders;
- generate a sandbox manifest of extracted candidate tables;
- generate a trial report explaining which downstream stages are blocked and why.

This is acceptable only if clearly reported as:
- SANDBOX_EXECUTE_PARTIAL
not PASS.

### 5. Reports
Generate:
- D:\_datefac\output\delivery_package\25_stage1_safe_runner_execute_wiring_report.md
- D:\_datefac\output\delivery_package\25_stage1_safe_runner_execute_wiring_report.xlsx

25 report must include:
- runner_path
- new_arguments
- component_inventory
- safe_components
- blocked_components
- scope_support_findings
- execute_plan
- production_write_guard_status
- sandbox_paths
- implementation_status

Generate:
- D:\_datefac\output\delivery_package\26_stage1_sandbox_execute_trial_evaluation.md
- D:\_datefac\output\delivery_package\26_stage1_sandbox_execute_trial_evaluation.xlsx

26 report must include:
- sandbox_execute_status: PASS / WARN / FAIL / BLOCKED / SANDBOX_EXECUTE_PARTIAL
- selected_samples
- sandbox_outputs_created
- per_sample_trial_status
- stages_completed
- stages_blocked
- safety_checks
- production_delivery_status_before
- production_delivery_status_after
- production_files_unchanged_check
- recommended_next_step

Excel sheets required:
- summary
- component_inventory
- execute_plan
- sample_trial_results
- stages_completed
- stages_blocked
- safety_checks
- production_guard
- next_steps

### 6. Validation commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --help
```

Create/update manifest:
- D:\_datefac\output\delivery_package\25_stage1_selected_samples_manifest.json

Run sandbox execute only:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py ^
  --manifest D:\_datefac\output\delivery_package\25_stage1_selected_samples_manifest.json ^
  --output-root D:\_datefac\output ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --trial-root D:\_datefac\output\_stage1_safe_runner_trial ^
  --sandbox-delivery-dir D:\_datefac\output\_stage1_safe_runner_trial\delivery_package ^
  --execute ^
  --execute-sandbox ^
  --strict-scope
```

Then run production delivery state check read-only:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

Do not use `--allow-production-write`.

### 7. Acceptance criteria
This task passes if:
1. runner py_compile passes.
2. runner help passes.
3. sandbox execute command runs and produces 25/26 reports.
4. sandbox execute either:
   - completes a safe partial pipeline with clear SANDBOX_EXECUTE_PARTIAL status, or
   - reaches a clear BLOCKED status with exact blocker reasons.
5. production delivery state remains PASS.
6. production 01/02/02A/06 are unchanged.
7. factory_core.py is not run.
8. marker/surya/vision/PaddleOCR are not triggered.
9. model.safetensors is not downloaded.
10. no output artifacts are committed.

A full PASS is not required yet. Clear partial or blocked status is acceptable if technically honest.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_wire_stage1_sandbox_execute.md

Worklog must be English only and UTF-8.

Worklog must include:
- task_title
- started_at
- finished_at
- git_commit_before
- git_commit_after
- commands_run
- files_read
- files_changed
- files_generated
- runner_path
- sandbox_execute_status
- production_delivery_status_before_after
- component_inventory_summary
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_safe_nonvision_pipeline.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/25_stage1_safe_runner_execute_wiring_report.md
- output/delivery_package/25_stage1_safe_runner_execute_wiring_report.xlsx
- output/delivery_package/26_stage1_sandbox_execute_trial_evaluation.md
- output/delivery_package/26_stage1_sandbox_execute_trial_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_safe_nonvision_pipeline.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "wire stage1 sandbox execute mode"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. runner_path
3. py_compile_status
4. help_status
5. sandbox_execute_status
6. generated_reports
7. production_delivery_status_before_after
8. production_files_unchanged
9. factory_core/vision/model_download_status
10. component_blockers
11. next_step_suggestion
12. commit sha

## safety_notes
- This task may run sandbox execute only.
- Do not write Stage 1 results into production delivery_package.
- Do not run factory_core.py.
- Do not trigger vision/OCR/model backends.
- Do not modify production delivery data.
