# NEXT CODEX TASK

## task_title
Run Stage 1 controlled three-sample expansion

## project
D:\_datefac

## current_status
Stage 1 sample manifest and execution plan have been generated and reviewed.

Generated planning docs:
- D:\_datefac\output\delivery_package\14_stage1_sample_manifest.md
- D:\_datefac\output\delivery_package\14_stage1_sample_manifest.xlsx
- D:\_datefac\output\delivery_package\15_stage1_execution_plan.md
- D:\_datefac\output\delivery_package\15_stage1_execution_plan.xlsx

Latest known delivery state before Stage 1 execution:
- overall_status = PASS
- pass_count = 17
- warn_count = 0
- fail_count = 0
- production delivery data 01/02/02A/06 were untouched during planning

Stage 1 selected samples:
1. H3_AP202605141822317484_1.pdf - 三鑫医疗 - stable expansion sample
2. H3_AP202605121822223662_1.pdf - 冠豪高新 - negative/abnormal value sample
3. H3_AP202605141822318060_1.pdf - 科锐国际 - broker layout/year normalization sample

Baseline regression guard only:
- H3_AP202605091822098939_1.pdf - 炬芯科技

Important: 091 is not a new Stage 1 sample. It is only a regression guard/reference.

## goal
Run Stage 1 controlled expansion for exactly the three selected PDFs, one sample at a time, using only the current safe non-vision pipeline already available in the repo.

Generate local reports:
- D:\_datefac\output\delivery_package\16_stage1_execution_log.md
- D:\_datefac\output\delivery_package\16_stage1_execution_log.xlsx
- D:\_datefac\output\delivery_package\17_stage1_result_evaluation.md
- D:\_datefac\output\delivery_package\17_stage1_result_evaluation.xlsx

The goal is not full automatic extraction accuracy. The goal is controlled pipeline stability, artifact generation, delivery health, and safe routing of uncertain metrics into manual review rather than unsafe trusted output.

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any vision model.
4. Do not process more than the three selected Stage 1 PDFs.
5. Do not treat baseline 091 as a new sample.
6. Do not overwrite or delete the existing accepted 091 delivery results without backup.
7. Do not commit output artifacts under output/delivery_package.
8. Worklog must be English only and UTF-8.
9. If any stop condition is triggered, stop immediately and produce a partial failure report.

## selected_samples
Use exactly these local PDF files if they exist in the project input location. If their local location differs, locate them under D:\_datefac by filename only. Do not download anything.

| sample_id | company | role | expected_risk |
|---|---|---|---|
| H3_AP202605141822317484_1.pdf | 三鑫医疗 | stable expansion sample | low_to_medium |
| H3_AP202605121822223662_1.pdf | 冠豪高新 | negative/abnormal value sample | high |
| H3_AP202605141822318060_1.pdf | 科锐国际 | broker layout/year normalization sample | medium_to_high |

## mandatory_preflight
Before running anything that touches PDFs, perform a preflight:

1. Sync Git:
```bat
cd /d D:\_datefac
git fetch origin
git pull origin main
git status --short
git log --oneline --decorate -8
```

2. Confirm task title:
Read D:\_datefac\docs\ai_handoff\NEXT_CODEX_TASK.md.
The task_title must be:
Run Stage 1 controlled three-sample expansion

If not matched, stop.

3. Locate selected PDFs:
Find exact paths for the three selected PDFs under D:\_datefac.
If any selected PDF is missing, stop and report missing_files.

4. Inspect available safe entrypoints:
List relevant tools/scripts under:
- D:\_datefac\tools
- D:\_datefac\scripts if present
- D:\_datefac root-level runner scripts if present

Identify the existing non-vision/pdfplumber-based pipeline entrypoints.
Do not guess blindly.
Do not run factory_core.py.
Do not run any command that imports or launches marker, surya, PaddleOCR, or vision backends.

5. Create backups before any runtime execution:
Create:
D:\_datefac\output\delivery_package\_backup_before_stage1_YYYYMMDD_HHMMSS

Backup existing delivery-package files if present:
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

6. Record pre-run state:
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```
Record output as pre_stage1_delivery_state.

## execution_strategy
Run the three selected samples one by one.

For each sample:
1. Confirm isolated asset output path before execution.
2. Run only the safe non-vision entrypoint identified during preflight.
3. After each sample, run delivery/package rebuild if the existing workflow requires it.
4. Run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\apply_manual_review_corrections.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```
Only run apply_manual_review_corrections.py after the sample's delivery artifacts are generated or updated. Do not use it as a substitute for PDF processing.
5. Record per-sample status, artifacts generated, failures, and stop-condition checks.

If the project currently has no safe non-vision entrypoint for adding a single new PDF without factory_core.py, stop and report this clearly. Do not fall back to factory_core.py.

## required_outputs_to_check
For each Stage 1 sample, evaluate whether the pipeline produced or updated:
- raw table assets / 02A equivalent original table assets if available
- table-region screenshot/crop index if available
- standardized core metrics stage output if available
- delivery package files
- manual review queue entries or failure/non-target explanation

At minimum, final delivery package should include updated or validated:
- 01_自动可信核心指标.xlsx
- 02_人工复核指标队列.xlsx
- 03_非目标报告与失败说明.xlsx
- 04_处理摘要.md
- 05_表格区域截图索引.xlsx
- 06_最终核心财务指标.xlsx
- 06A_人工修正应用明细.xlsx
- 06B_未解决问题清单.xlsx
- 06D_人工复核回写诊断.xlsx
- 07_delivery_state_check.xlsx

## acceptance_criteria
Stage 1 passes only if:
1. No model.safetensors download was triggered.
2. No marker/surya/PaddleOCR/vision backend was triggered.
3. factory_core.py was not run.
4. The three selected samples were handled one by one.
5. Each selected sample either generated expected artifacts or produced explicit failure/non-target explanation.
6. check_delivery_state.py reports fail_count = 0.
7. warn_count = 0 or only clearly documented non-blocking warnings.
8. duplicate_key_count_final = 0.
9. high_risk_flags do not enter 01/06.
10. test_token_hits = 0.
11. uncertain metrics route to 02 manual review queue rather than forced 01/06 trust.
12. baseline 091 accepted values are not broken.

## stop_conditions
Stop immediately if any of these occur:
1. model.safetensors download sign.
2. marker / surya / PaddleOCR / vision backend trigger.
3. factory_core.py is required to proceed.
4. output path would overwrite baseline 091 without backup.
5. duplicate_key_count_final becomes non-zero.
6. high_risk_flags enter 01/06.
7. test token hits become non-zero.
8. Excel/WPS file lock blocks write or causes partial corruption.
9. selected PDF missing.
10. no safe non-vision entrypoint exists.

## generated_reports
Generate local report:
D:\_datefac\output\delivery_package\16_stage1_execution_log.md
D:\_datefac\output\delivery_package\16_stage1_execution_log.xlsx

16 report must contain:
- task_title
- started_at / finished_at
- git_commit_before
- pre_stage1_delivery_state
- selected sample paths
- entrypoints discovered
- exact commands run
- per_sample_execution_log
- per_sample_artifacts
- per_sample_delivery_status
- stop_condition_checks
- files_modified
- safety_notes

Generate local report:
D:\_datefac\output\delivery_package\17_stage1_result_evaluation.md
D:\_datefac\output\delivery_package\17_stage1_result_evaluation.xlsx

17 report must contain:
- final_stage1_status: PASS / WARN / FAIL
- final_delivery_status
- sample_result_summary
- trusted_output_summary
- manual_review_queue_summary
- non_target_or_failure_summary
- duplicate_key_status
- high_risk_flag_status
- test_token_status
- baseline_regression_status
- recommended_next_step

## validation_commands
At the end, run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

Also inspect 07_delivery_state_check.xlsx and summarize all FAIL/WARN sheets.

If possible, inspect 06_最终核心财务指标.xlsx and summarize rows by sample/company/source.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_run_stage1_controlled_expansion.md

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
- entrypoints_used
- files_generated
- files_modified
- final_delivery_status
- final_stage1_status
- stop_condition_checks
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit only:
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/16_stage1_execution_log.md
- output/delivery_package/16_stage1_execution_log.xlsx
- output/delivery_package/17_stage1_result_evaluation.md
- output/delivery_package/17_stage1_result_evaluation.xlsx
- any output Excel/PDF/PNG assets

Commit:
```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "run stage1 controlled expansion"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. selected_samples_processed
3. entrypoints_used
4. generated_reports
5. final_stage1_status
6. final_delivery_status: overall_status/pass_count/warn_count/fail_count
7. duplicate_key_count_final
8. high_risk_flags status
9. test_token_hits status
10. baseline_regression_status
11. stop_conditions_triggered
12. commit sha

## safety_notes
- Do not run factory_core.py.
- Do not trigger marker/surya/vision/PaddleOCR.
- Do not download model.safetensors.
- Stop if safe non-vision entrypoint is not available.
- Do not commit output artifacts.
