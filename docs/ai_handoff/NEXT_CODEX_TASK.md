# NEXT CODEX TASK

## task_title
Run full safe non-vision pipeline for Stage 1 visually approved samples

## project
D:\_datefac

## current_status
Stage 1 visual confirmation packet has been generated and reviewed.

Reviewed file:
- D:\_datefac\output\delivery_package\20_stage1_visual_confirmation_index.xlsx

Latest 20 packet summary:
- delivery_status = PASS / pass_count=17 / warn_count=0 / fail_count=0
- selected_samples_count = 3
- preview_count = 7
- missing_pdf_count = 0
- overall_recommendation = Run full safe non-vision pipeline for Stage 1 visually approved samples

Visual confirmation index decisions:
- H3_AP202605141822317484_1 = approve_for_full_safe_pipeline
- H3_AP202605121822223662_1 = approve_for_full_safe_pipeline
- H3_AP202605141822318060_1 = approve_for_full_safe_pipeline
- H3_AP202605141822318060_1 page 6 = ignore, likely rating/disclaimer table

Important clarification:
Previous Stage 1 steps only probed and rendered candidate pages. They did not integrate the three samples into 01/02/06. This task is the first attempt to run the full safe non-vision pipeline for the three Stage 1 samples.

## goal
Run the complete available safe non-vision pipeline for the three visually approved Stage 1 samples, one sample at a time.

Expected local reports:
- D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.md
- D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.xlsx
- D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.md
- D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.xlsx

The goal is not perfect extraction accuracy. The goal is:
1. generate full non-vision asset outputs for the three samples if supported by current repo tools;
2. rebuild delivery package safely;
3. route uncertain/low-confidence items into manual review rather than unsafe trusted output;
4. keep delivery health clean;
5. preserve the existing 091 baseline accepted values.

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any vision model.
4. Do not process any PDFs beyond the three selected samples.
5. Do not treat baseline 091 as a new Stage 1 sample.
6. Do not overwrite or delete the accepted 091 results without backup.
7. Do not submit output artifacts to Git.
8. Worklog must be English only and UTF-8.
9. If no complete safe non-vision entrypoint exists, stop and report BLOCKED_NO_SAFE_FULL_PIPELINE. Do not fall back to factory_core.py.
10. If any stop condition triggers, stop immediately and produce partial reports.

## selected_samples
Process exactly these PDFs:

1. H3_AP202605141822317484_1.pdf
   company: 三鑫医疗
   approved pages: 1, 4, 5

2. H3_AP202605121822223662_1.pdf
   company: 冠豪高新
   approved pages: 2, 3

3. H3_AP202605141822318060_1.pdf
   company: 科锐国际
   approved pages: 5
   ignored page: 6, likely rating/disclaimer

Baseline regression guard only:
- H3_AP202605091822098939_1.pdf
Do not reprocess as a new sample.

## mandatory_preflight

### 1. Sync Git and confirm task
Run:
```bat
cd /d D:\_datefac
git fetch origin
git pull origin main
git status --short
git log --oneline --decorate -8
```

Read NEXT_CODEX_TASK.md and confirm task_title is:
Run full safe non-vision pipeline for Stage 1 visually approved samples

If task_title does not match, stop.

### 2. Locate selected PDFs
Find exact local paths under D:\_datefac for:
- H3_AP202605141822317484_1.pdf
- H3_AP202605121822223662_1.pdf
- H3_AP202605141822318060_1.pdf

If any is missing, stop and report missing_files.

### 3. Backup current delivery state
Create:
D:\_datefac\output\delivery_package\_backup_before_stage1_full_pipeline_YYYYMMDD_HHMMSS

Backup existing delivery files if present:
- 01_自动可信核心指标.xlsx
- 01A_自动可信核心指标冲突明细.xlsx
- 02_人工复核指标队列.xlsx
- 02A_人工年份修正覆盖表.xlsx
- 03_非目标报告与失败说明.xlsx
- 04_处理摘要.md
- 05_表格区域截图索引.xlsx
- 06_最终核心财务指标.xlsx
- 06A_人工修正应用明细.xlsx
- 06B_未解决问题清单.xlsx
- 06C_复核模板说明.md
- 06D_人工复核回写诊断.xlsx
- 07_delivery_state_check.xlsx

### 4. Record pre-run delivery state
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```
Record as pre_run_delivery_state.

### 5. Discover safe full non-vision entrypoints
Inspect repo scripts under:
- D:\_datefac\tools
- D:\_datefac\scripts, if present
- D:\_datefac root scripts

Find the current safe pipeline steps that can produce:
- raw table assets / table extraction outputs
- table region screenshots or indexes if available
- standardized core metrics output
- delivery_package rebuild

Important:
- Do not use factory_core.py.
- Do not run any tool importing/launching marker, surya, PaddleOCR, or vision backend.
- If only factory_core.py can run a full pipeline, stop with BLOCKED_NO_SAFE_FULL_PIPELINE.
- If safe full pipeline requires multiple tools, execute them step by step and record commands.

Known safe tools that may be used if present and appropriate:
- build_delivery_package.py
- apply_manual_review_corrections.py
- check_delivery_state.py
- any pdfplumber-only extraction/standardization scripts already present

Do not invent missing scripts.

## execution_strategy
Process samples one by one.

For each sample:
1. Confirm asset package output path.
2. Run safe table extraction / asset generation step if available.
3. Run safe standardization step if available.
4. Rebuild delivery package if available.
5. Run apply_manual_review_corrections.py only after delivery artifacts are produced/updated.
6. Run check_delivery_state.py --json after each sample or after each safe batch, depending on tool design.
7. Record all commands and per-sample status.

If the current safe full pipeline only supports batch processing of all input PDFs, first confirm it will not process beyond the three selected Stage 1 PDFs. If it cannot limit scope safely, stop and report BLOCKED_SCOPE_UNSAFE.

## acceptance_criteria
Stage 1 full pipeline passes only if:
1. factory_core.py was not run.
2. marker/surya/vision/PaddleOCR were not triggered.
3. model.safetensors download was not triggered.
4. exactly the three selected samples were processed or explicitly failed with controlled explanations.
5. 091 baseline accepted values remain intact.
6. delivery check reports fail_count = 0.
7. duplicate_key_count_final = 0.
8. test_token_hits = 0.
9. high_risk_flags do not enter 01/06.
10. non-target or failed samples are recorded in 03 rather than crashing.
11. uncertain metrics go to 02 manual review queue, not unsafe 01/06 trust.
12. output reports 21/22 exist and are readable.

WARN is acceptable only if clearly non-blocking and documented.

## stop_conditions
Stop immediately if any occurs:
1. model.safetensors download sign.
2. marker / surya / PaddleOCR / vision backend trigger.
3. factory_core.py becomes required.
4. no safe full non-vision entrypoint exists.
5. pipeline cannot restrict to the three selected samples.
6. duplicate_key_count_final becomes non-zero.
7. test_token_hits becomes non-zero.
8. high_risk_flags enter 01/06.
9. Excel/WPS lock causes write failure or partial corruption.
10. output path would overwrite 091 baseline without backup.

## generated_reports
Generate:
- D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.md
- D:\_datefac\output\delivery_package\21_stage1_full_pipeline_execution_log.xlsx

21 report must include:
- task_title
- started_at / finished_at
- git_commit_before
- pre_run_delivery_state
- selected_samples
- safe_entrypoints_discovered
- entrypoints_used
- exact commands run
- per_sample_status
- files_created_or_modified
- stop_condition_checks
- safety_notes

Generate:
- D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.md
- D:\_datefac\output\delivery_package\22_stage1_full_pipeline_result_evaluation.xlsx

22 report must include:
- final_stage1_full_pipeline_status: PASS / WARN / FAIL / BLOCKED
- final_delivery_status
- sample_result_summary
- generated_asset_summary_by_sample
- trusted_output_summary
- manual_review_queue_summary
- non_target_or_failure_summary
- duplicate_key_status
- high_risk_flag_status
- test_token_status
- baseline_regression_status
- remaining_issues
- recommended_next_step

Excel sheets required:
- summary
- commands_run
- sample_results
- generated_assets
- delivery_status
- trusted_output_summary
- manual_queue_summary
- risk_checks
- baseline_regression
- next_steps

## validation_commands
At minimum run at the end:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

Inspect:
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\03_非目标报告与失败说明.xlsx

Summarize:
- final rows by asset_package/company if possible
- manual queue rows by sample
- failure/non-target rows by sample
- high-risk/test-token/duplicate status

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_run_stage1_full_safe_pipeline.md

Worklog must be English only and UTF-8.

Worklog must include:
- task_title
- started_at
- finished_at
- git_commit_before
- git_commit_after
- commands_run
- selected_samples
- baseline_sample
- safe_entrypoints_discovered
- entrypoints_used
- files_generated
- files_modified
- final_stage1_full_pipeline_status
- final_delivery_status
- stop_condition_checks
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Commit only worklog docs:
```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "run stage1 full safe pipeline"
git push origin main
```

Do not commit:
- output/delivery_package/21_stage1_full_pipeline_execution_log.md
- output/delivery_package/21_stage1_full_pipeline_execution_log.xlsx
- output/delivery_package/22_stage1_full_pipeline_result_evaluation.md
- output/delivery_package/22_stage1_full_pipeline_result_evaluation.xlsx
- any output artifacts

## expected_final_response
After completion, output:
1. task_title
2. final_stage1_full_pipeline_status
3. final_delivery_status: overall_status/pass_count/warn_count/fail_count
4. selected_samples_processed
5. safe_entrypoints_used
6. generated_reports
7. duplicate_key_count_final
8. high_risk_flags status
9. test_token_hits status
10. baseline_regression_status
11. stop_conditions_triggered
12. next_step_suggestion
13. commit sha

## safety_notes
- Do not run factory_core.py.
- Do not trigger marker/surya/vision/PaddleOCR.
- Do not download model.safetensors.
- Stop if safe full non-vision entrypoint is unavailable.
- Do not commit output artifacts.
