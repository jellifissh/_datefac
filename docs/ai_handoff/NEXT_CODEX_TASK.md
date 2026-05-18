# NEXT CODEX TASK

## task_title
Review Stage 1 probe results and decide next execution gate

## project
D:\_datefac

## current_status
The previous task ran Stage 1 controlled three-sample probe execution using:
- D:\_datefac\tools\probe_pdf_tables.py

Latest worklog says:
- task_title = Run Stage 1 controlled three-sample expansion
- selected samples processed:
  - H3_AP202605141822317484_1.pdf
  - H3_AP202605121822223662_1.pdf
  - H3_AP202605141822318060_1.pdf
- baseline sample H3_AP202605091822098939_1.pdf was not reprocessed
- entrypoint used = probe_pdf_tables.py
- factory_core.py was not run
- marker/surya/vision/PaddleOCR were not triggered
- model.safetensors download was not triggered
- final_delivery_status = PASS / warn_count=0 / fail_count=0

Important clarification:
The previous run was a safe probe/table-detection stage, not a full delivery-package integration stage.
Since 01/02/02A/06 production delivery files were not modified, the current PASS only proves that the probe stage was safe and that existing delivery state stayed clean. It does not prove that the three new samples have been fully standardized into 01/02/06.

## goal
Review the per-sample Stage 1 probe reports and produce a consolidated quality review.

Generate local reports:
- D:\_datefac\output\delivery_package\18_stage1_probe_quality_review.md
- D:\_datefac\output\delivery_package\18_stage1_probe_quality_review.xlsx

This task must decide whether each sample is ready for the next gate:
- READY_FOR_FULL_SAFE_PIPELINE
- NEEDS_MANUAL_INSPECTION
- BLOCKED
- NON_TARGET

This task must not run full PDF processing and must not modify production delivery data.

## hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any vision model.
4. Do not rerun probe_pdf_tables.py unless an existing 16/17 report is missing and rerun is strictly needed.
5. Do not run full extraction/standardization/delivery rebuild.
6. Do not run apply_manual_review_corrections.py.
7. Do not modify 01_自动可信核心指标.xlsx.
8. Do not modify 02_人工复核指标队列.xlsx.
9. Do not modify 02A_人工年份修正覆盖表.xlsx.
10. Do not modify 06_最终核心财务指标.xlsx.
11. Do not commit output artifacts.
12. Worklog must be English only and UTF-8.

## selected_samples
Review exactly these sample asset folders:

1. D:\_datefac\output\H3_AP202605141822317484_1_资产包
2. D:\_datefac\output\H3_AP202605121822223662_1_资产包
3. D:\_datefac\output\H3_AP202605141822318060_1_资产包

For each folder, read if present:
- 16_stage1_execution_log.md
- 16_stage1_execution_log.xlsx
- 17_stage1_result_evaluation.md
- 17_stage1_result_evaluation.xlsx
- _stage1_probe outputs under that asset folder

## required_steps

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
Review Stage 1 probe results and decide next execution gate

If not matched, stop.

### 2. Read delivery state, read-only
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```
Record current delivery status.

### 3. Read per-sample 16/17 reports
For each selected sample, collect:
- sample_id
- company
- probe command used
- probe status
- pages scanned
- tables detected count
- candidate target tables count
- whether Table_MainProfit / core financial metrics table was detected
- whether full financial forecast table was detected
- whether screenshots/crops were generated
- dependency_missing warnings
- errors or exceptions
- stop conditions
- recommended next gate

If 16/17 reports are too sparse, inspect _stage1_probe files to extract the above details.

### 4. Gate decision logic
Apply these rules:

READY_FOR_FULL_SAFE_PIPELINE if:
- probe completed without fatal error
- at least one likely core financial metric table or main profit table was detected
- no stop condition triggered
- no vision/OCR/model dependency required

NEEDS_MANUAL_INSPECTION if:
- probe completed but target table confidence is unclear
- target tables are present but table structure looks fragmented or ambiguous
- dependency_missing warnings may reduce coverage but do not block safety

BLOCKED if:
- selected PDF missing
- probe failed fatally
- output folder missing or corrupt
- any stop condition triggered

NON_TARGET if:
- probe indicates report is not a company financial forecast / target report

### 5. Generate 18 consolidated review
Create:
- D:\_datefac\output\delivery_package\18_stage1_probe_quality_review.md
- D:\_datefac\output\delivery_package\18_stage1_probe_quality_review.xlsx

Markdown must contain:

# Stage 1 Probe Quality Review

## Summary
- generated_at
- delivery_status
- selected_samples_count
- ready_count
- manual_inspection_count
- blocked_count
- non_target_count
- overall_recommendation

## Important Clarification
Explain clearly that the previous Stage 1 run used probe_pdf_tables.py only and did not integrate the three samples into 01/02/06. Therefore PASS means safe probe PASS, not full extraction PASS.

## Per-Sample Review
For each sample:
- sample_id
- company
- role
- probe_status
- tables_detected_count
- target_table_evidence
- warnings
- errors
- gate_decision
- reason

## Dependency and Safety Review
Summarize:
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model.safetensors not downloaded
- dependency_missing warnings if any

## Next Gate Recommendation
Recommend exactly one of:
- Proceed to full safe non-vision pipeline for READY samples only
- Manual inspect selected sample crops before full pipeline
- Fix probe/report quality first

Do not recommend direct 30-sample expansion.

## Proposed Next Task
If at least one sample is READY_FOR_FULL_SAFE_PIPELINE, draft a recommended next task title:
Run full safe non-vision pipeline for Stage 1 ready samples

If none are ready, draft:
Manual inspect Stage 1 probe outputs before full pipeline

Excel must include sheets:
- summary
- per_sample_review
- table_detection_summary
- safety_review
- gate_decisions
- next_recommendation

### 6. Validate generated docs
Verify:
- 18 md/xlsx exist
- no `????`
- no Unicode replacement char `�`
- no output artifacts committed
- 01/02/02A/06 unchanged

### 7. Update worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_review_stage1_probe_quality.md

Worklog must be English only and UTF-8.

Worklog must include:
- task_title
- started_at
- finished_at
- git_commit_before
- git_commit_after
- commands_run
- files_read
- files_generated
- per_sample_gate_decisions
- delivery_status
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Only commit worklog:
```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "review stage1 probe quality"
git push origin main
```

Do not commit:
- output/delivery_package/18_stage1_probe_quality_review.md
- output/delivery_package/18_stage1_probe_quality_review.xlsx
- any output artifacts

## expected_final_response
After completion, output:
1. task_title
2. delivery_status
3. per_sample_gate_decisions
4. ready_count / manual_inspection_count / blocked_count / non_target_count
5. generated_reports
6. whether production data was untouched
7. whether output docs contain garbled text
8. next_step_suggestion
9. commit sha

## safety_notes
- This is a review-only task.
- Do not run factory_core.py.
- Do not run full delivery pipeline.
- Do not modify production delivery data.
- Do not commit output artifacts.
