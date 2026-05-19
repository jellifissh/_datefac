# NEXT CODEX TASK

## task_title
Implement scoped safe non-vision Stage 1 runner

## project
D:\_datefac

## current_status
The latest uploaded Stage 1 full pipeline reports show that full execution was blocked before processing.

User uploaded/reviewed reports:
- D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.xlsx
- D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.xlsx

Key result from 21/22:
- final_stage1_full_pipeline_status = BLOCKED
- final_delivery_status = PASS / pass_count=17 / warn_count=0 / fail_count=0
- selected PDFs exist
- samples were not processed
- generated_assets = none
- trusted_output_summary = not_updated
- manual_queue_summary = not_updated
- duplicate_key_count_final = 0
- high_risk_flags = 0
- test_token_hits = 0
- baseline 091 = not_reprocessed_intact
- blocker = BLOCKED_NO_SAFE_FULL_PIPELINE

Reason:
There is no complete safe non-vision full-pipeline entrypoint outside factory_core.py that can process exactly the three selected PDFs end-to-end. The system has safe probe tools, but no scoped safe runner for full Stage 1 processing.

Important Git note:
Remote docs/codex_worklog/LATEST.md may still reflect the previous visual-confirmation task. Treat the user-uploaded 21/22 reports as the current local evidence for this task.

## goal
Implement a scoped safe non-vision Stage 1 runner, but do not use it to modify production delivery data yet.

Primary goal:
- Add a safe runner that can later process exactly the three Stage 1 PDFs without factory_core.py and without vision/OCR backends.

Recommended new tool:
- D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py

If a better file name or location is clearly more consistent with the repo, use that, but explain the choice in the worklog.

The runner should support:
- `--manifest <path>` or `--pdf <path>` repeated
- `--output-root D:\_datefac\output`
- `--delivery-dir D:\_datefac\output\delivery_package`
- `--dry-run`
- `--execute`
- `--strict-scope`
- `--no-vision` default true
- `--skip-apply` optional
- `--stop-on-first-error` default true

This task should implement and validate the runner in dry-run mode only.
Do not run `--execute` yet.

## selected_stage1_samples
The runner must be designed to accept exactly these Stage 1 samples for the first real execution later:

1. H3_AP202605141822317484_1.pdf
   company: 三鑫医疗
   approved pages: 1, 4, 5

2. H3_AP202605121822223662_1.pdf
   company: 冠豪高新
   approved pages: 2, 3

3. H3_AP202605141822318060_1.pdf
   company: 科锐国际
   approved pages: 5
   ignored page: 6, likely rating/disclaimer table

Baseline regression guard only:
- H3_AP202605091822098939_1.pdf
Do not process as a new Stage 1 sample.

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any vision model.
4. Do not run the new runner in execute mode in this task.
5. Do not process PDFs beyond dry-run validation.
6. Do not modify 01_自动可信核心指标.xlsx.
7. Do not modify 02_人工复核指标队列.xlsx.
8. Do not modify 02A_人工年份修正覆盖表.xlsx.
9. Do not modify 06_最终核心财务指标.xlsx.
10. Do not rebuild delivery_package in this task.
11. Do not commit output artifacts.
12. Worklog must be English only and UTF-8.

## implementation_requirements

### 1. Source inspection allowed, execution forbidden
You may inspect source code, including factory_core.py, to understand existing pipeline steps, but you must not run factory_core.py.

Inspect existing scripts/modules to find safe reusable components for:
- pdfplumber-based table extraction
- pdfplumber profile fallback
- glued table splitter
- raw table asset generation
- table-region screenshot/index generation if already safe
- core metric standardization stage
- delivery_package builder
- manual correction apply/check scripts

Do not import modules that have top-level imports or side effects involving marker/surya/PaddleOCR/vision/model downloads.
If a module is unsafe at import time, avoid importing it directly and document it.

### 2. Runner safety guards
The new runner must enforce:
- explicit PDF list or manifest only
- strict scope guard: only the provided PDFs are processed
- baseline 091 is not treated as a new sample unless explicitly included and `--allow-baseline` is passed
- no factory_core invocation
- no marker/surya/PaddleOCR/vision command invocation
- no model.safetensors downloads
- no network downloads
- pre-run check for selected PDF existence
- optional backup requirement before execute mode

Implement visible checks in code, not just comments.

### 3. Dry-run behavior
`--dry-run` must:
- validate arguments
- locate PDFs
- list planned asset output folders
- list planned safe pipeline steps
- identify discovered safe entrypoints/scripts
- identify unsafe or blocked entrypoints with reason
- confirm no production delivery files would be modified
- write a dry-run report locally
- exit with code 0 only if the plan is executable in principle
- exit non-zero if no safe full pipeline path can be constructed

Dry-run output files:
- D:\_datefac\output\delivery_package\23_stage1_safe_runner_dry_run.md
- D:\_datefac\output\delivery_package\23_stage1_safe_runner_dry_run.xlsx

### 4. Execute behavior design
`--execute` does not need to be run in this task, but the code structure should be ready for later.

Execute mode should eventually:
- backup delivery files first
- process samples one by one
- run safe extraction/standardization steps
- rebuild delivery package
- run apply_manual_review_corrections.py
- run check_delivery_state.py --json
- stop on stop conditions
- generate execution/evaluation reports

If some execute steps cannot yet be wired because safe modules are missing or unsafe to import, implement a clear `BLOCKED_NOT_IMPLEMENTED` or `BLOCKED_UNSAFE_IMPORT` path rather than silently skipping.

### 5. Test/validation requirements
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --help
```

Create a local manifest for dry run only, for example:
D:\_datefac\output\delivery_package\23_stage1_selected_samples_manifest.json

Run dry-run only:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py ^
  --manifest D:\_datefac\output\delivery_package\23_stage1_selected_samples_manifest.json ^
  --output-root D:\_datefac\output ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --dry-run ^
  --strict-scope
```

Also run read-only delivery check:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

Do not run execute mode.

### 6. Reports
Generate local validation report:
- D:\_datefac\output\delivery_package\24_stage1_safe_runner_implementation_report.md
- D:\_datefac\output\delivery_package\24_stage1_safe_runner_implementation_report.xlsx

24 report must include:
- implemented_runner_path
- safe_entrypoints_discovered
- unsafe_entrypoints_blocked
- import_safety_findings
- dry_run_status
- dry_run_commands
- dry_run_planned_steps
- dry_run_planned_samples
- why execute was not run
- current_delivery_status
- next recommended task

Excel sheets required:
- summary
- runner_interface
- safe_entrypoints
- unsafe_entrypoints
- dry_run_plan
- dry_run_results
- delivery_status
- next_steps

## acceptance_criteria
This task passes if:
1. New scoped runner is added or an equivalent safe runner is implemented.
2. `py_compile` passes.
3. `--help` works.
4. `--dry-run` works and produces 23 report.
5. 24 implementation report is generated.
6. No production delivery files 01/02/02A/06 are modified.
7. delivery check remains PASS.
8. factory_core.py is not run.
9. marker/surya/vision/PaddleOCR are not triggered.
10. model.safetensors is not downloaded.
11. output artifacts are not committed.

If the runner cannot be implemented safely, fail explicitly with:
- BLOCKED_RUNNER_IMPLEMENTATION_UNSAFE
and explain which dependency/import/entrypoint blocks it.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_implement_stage1_safe_runner.md

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
- dry_run_status
- current_delivery_status
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_safe_nonvision_pipeline.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

If you modify small helper code or tests to support the runner, include only those necessary source files and explain why.

Do not commit:
- output/delivery_package/23_stage1_safe_runner_dry_run.md
- output/delivery_package/23_stage1_safe_runner_dry_run.xlsx
- output/delivery_package/24_stage1_safe_runner_implementation_report.md
- output/delivery_package/24_stage1_safe_runner_implementation_report.xlsx
- any output artifacts

Commit:
```bat
git add tools/run_stage1_safe_nonvision_pipeline.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add scoped stage1 safe nonvision runner"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. runner_path
3. py_compile_status
4. help_status
5. dry_run_status
6. generated_reports
7. current_delivery_status: overall_status/pass_count/warn_count/fail_count
8. whether production data was untouched
9. whether factory_core/vision/model downloads were avoided
10. next_step_suggestion
11. commit sha

## safety_notes
- This task implements and dry-runs the runner only.
- Do not execute the full pipeline yet.
- Do not run factory_core.py.
- Do not trigger vision/OCR/model backends.
- Do not modify production delivery data.
