# NEXT CODEX TASK

## task_title
Implement pdfplumber-only sandbox asset builder for Stage 1

## project
D:\_datefac

## current_status
The latest sandbox execute wiring run produced a controlled block.

User uploaded/reviewed files:
- D:\_datefac\output\_stage1_safe_runner_trial\25_stage1_safe_runner_sandbox_execute_log.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\26_stage1_safe_runner_sandbox_execute_evaluation.xlsx

Key result from uploaded 25/26:
- execute_status = BLOCKED_NO_SAFE_FULL_PIPELINE
- validate_samples = PASS, samples=3
- create_trial_dirs = PASS
- prepare_asset_dirs = PASS, prepared=3
- execute_pipeline = BLOCKED, reason: No safe full non-vision extraction+standardization pipeline available without factory_core
- production_guard_changed_count = 0
- production delivery before/after = PASS / pass_count=17 / warn_count=0 / fail_count=0
- production 01/02/02A/06 unchanged
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered

Interpretation:
The runner safety and sandbox guard are working, but there is still no executable non-vision full pipeline. The next practical step is to implement a minimum useful sandbox asset builder using pdfplumber only, limited to visually approved pages, and write outputs only under the trial root.

## goal
Extend `tools/run_stage1_safe_nonvision_pipeline.py` to support a minimum useful sandbox execution path:
- pdfplumber-only table extraction for the selected Stage 1 PDFs;
- limited to approved pages from manifest;
- write per-sample sandbox asset files under trial root;
- generate table/candidate summaries;
- do not write into production delivery_package except local report files 27/28 under delivery_package.

This task should not try to produce production 01/06 yet. It should prove that scoped non-vision extraction can create usable sandbox evidence assets.

New local reports:
- D:\_datefac\output\delivery_package\27_stage1_pdfplumber_sandbox_asset_build_log.md
- D:\_datefac\output\delivery_package\27_stage1_pdfplumber_sandbox_asset_build_log.xlsx
- D:\_datefac\output\delivery_package\28_stage1_pdfplumber_sandbox_asset_evaluation.md
- D:\_datefac\output\delivery_package\28_stage1_pdfplumber_sandbox_asset_evaluation.xlsx

Sandbox root:
- D:\_datefac\output\_stage1_safe_runner_trial

Sandbox per-sample asset folders should be under:
- D:\_datefac\output\_stage1_safe_runner_trial\run_YYYYMMDD_HHMMSS\assets\<pdf_stem>_资产包

## selected_stage1_samples
Use exactly these PDFs and pages:

1. H3_AP202605141822317484_1.pdf
   company: 三鑫医疗
   approved_pages: [1, 4, 5]

2. H3_AP202605121822223662_1.pdf
   company: 冠豪高新
   approved_pages: [2, 3]

3. H3_AP202605141822318060_1.pdf
   company: 科锐国际
   approved_pages: [5]
   ignored_pages: [6]

Baseline regression guard:
- H3_AP202605091822098939_1.pdf
Do not process as a Stage 1 sample.

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any model.
4. Do not run OCR.
5. Use pdfplumber only for table extraction.
6. Do not process pages outside approved_pages, except if only metadata listing is needed.
7. Do not process any PDFs beyond the three selected Stage 1 PDFs.
8. Do not modify production delivery files:
   - 01_自动可信核心指标.xlsx
   - 02_人工复核指标队列.xlsx
   - 02A_人工年份修正覆盖表.xlsx
   - 06_最终核心财务指标.xlsx
9. Do not rebuild production delivery_package.
10. Do not run apply_manual_review_corrections.py.
11. Do not submit output artifacts to Git.
12. Worklog must be English only and UTF-8.
13. If pdfplumber is unavailable or extraction fails for a sample, report controlled failure for that sample; do not fall back to vision/OCR.

## implementation_requirements

### 1. Extend runner interface
Update `tools/run_stage1_safe_nonvision_pipeline.py`.

Add or reuse arguments:
- `--execute`
- `--execute-sandbox`
- `--trial-root`
- `--sandbox-delivery-dir`
- `--strict-scope`
- `--no-vision`
- `--pdfplumber-only` default true or equivalent internal guard

Rules:
- `--execute --execute-sandbox` should now attempt pdfplumber-only sandbox extraction.
- `--execute` without `--execute-sandbox` and without `--allow-production-write` must remain blocked.
- `--allow-production-write` must not be used in this task.
- Existing dry-run behavior must still work.

### 2. Manifest support
Create/update manifest:
D:\_datefac\output\delivery_package\27_stage1_pdfplumber_selected_samples_manifest.json

Manifest entries should include:
- pdf_path
- sample_id
- company
- approved_pages
- ignored_pages

The runner should respect approved_pages.

### 3. Sandbox asset outputs
For each sample, create per-sample asset folder under the trial run:
D:\_datefac\output\_stage1_safe_runner_trial\run_YYYYMMDD_HHMMSS\assets\<pdf_stem>_资产包

Generate at least:

1. `02A_研报原始表格资产.xlsx`
   Sheet suggestions:
   - raw_tables_index
   - raw_table_cells
   - extraction_diagnostics

Required columns for raw_tables_index:
- asset_package
- pdf_file
- company
- page
- table_index
- backend
- row_count
- column_count
- detected_year_cells
- metric_keyword_hits
- candidate_type
- confidence
- extraction_status
- source_note

Required columns for raw_table_cells:
- asset_package
- pdf_file
- page
- table_index
- row_index
- col_index
- cell_value

2. `02_研报全量结构化数据.xlsx`
   Minimum acceptable structure:
   - one sheet named `tables_index`
   - optional one sheet per table, e.g. `p005_t001`, `p005_t002`
   - preserve raw cell text without aggressive cleaning

3. `05_stage1_core_metric_candidates.xlsx`
   This is not the production 05 file.
   It should contain heuristic candidate rows only, based on metric keyword + year evidence.

Suggested columns:
- asset_package
- company
- page
- table_index
- metric_keyword
- matched_row_index
- year_cells_in_table
- row_preview
- candidate_confidence
- recommended_route: manual_review_candidate / likely_core_metric / ignore

4. `stage1_sandbox_asset_summary.xlsx`
   Summarize per sample:
- pages_processed
- tables_extracted
- candidate_tables
- metric_candidate_rows
- extraction_errors
- overall_sample_status

### 4. Heuristics
Use only simple deterministic heuristics.

Year-like patterns:
- 2024A, 2025A, 2026E, 2027E, 2028E
- 2024, 2025, 2026, 2027, 2028

Metric keywords:
- 营业收入
- 收入
- 归属母公司净利润
- 归母净利润
- 净利润
- 每股收益
- EPS
- P/E
- PE
- P/B
- PB
- EV/EBITDA
- ROE
- EBITDA
- 毛利率
- 净利率

Candidate confidence rule suggestion:
- high: table has year evidence and >=3 metric keyword hits
- medium: table has year evidence and 1-2 metric keyword hits
- low: table has year evidence but 0 metric keyword hits
- ignore: rating/disclaimer/legal table evidence or no year evidence

### 5. Trial-level aggregate outputs
Under trial run root, generate:
- `stage1_trial_asset_inventory.xlsx`
- `stage1_trial_asset_inventory.md`

Include:
- per sample asset folder
- files generated
- tables extracted
- candidate tables
- metric candidate rows
- sample status

### 6. Production guard
Before and after sandbox execution, hash production guard files:
- 01_自动可信核心指标.xlsx
- 02_人工复核指标队列.xlsx
- 02A_人工年份修正覆盖表.xlsx
- 06_最终核心财务指标.xlsx

If any changed, mark task FAIL and stop.

Also run production delivery check after execution:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

### 7. Reports 27/28
Generate:
- D:\_datefac\output\delivery_package\27_stage1_pdfplumber_sandbox_asset_build_log.md
- D:\_datefac\output\delivery_package\27_stage1_pdfplumber_sandbox_asset_build_log.xlsx

27 report must include:
- task_title
- runner_path
- started_at / finished_at
- command_run
- manifest_path
- trial_run_root
- per_sample_pages_processed
- per_sample_tables_extracted
- files_generated_by_sample
- production_guard_changed_count
- safety_checks

Generate:
- D:\_datefac\output\delivery_package\28_stage1_pdfplumber_sandbox_asset_evaluation.md
- D:\_datefac\output\delivery_package\28_stage1_pdfplumber_sandbox_asset_evaluation.xlsx

28 report must include:
- sandbox_asset_build_status: PASS / WARN / FAIL / PARTIAL
- production_delivery_status_after
- selected_samples
- per_sample_status
- per_sample_candidate_table_count
- per_sample_metric_candidate_rows
- high_medium_low_candidate_counts
- samples_ready_for_standardizer_trial
- samples_needing_manual_review
- blockers
- recommended_next_step

Excel sheets required:
- summary
- per_sample_status
- tables_extracted
- metric_candidates
- generated_files
- production_guard
- safety_checks
- next_steps

### 8. Validation commands
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py --help
```

Run sandbox execute:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\run_stage1_safe_nonvision_pipeline.py ^
  --manifest D:\_datefac\output\delivery_package\27_stage1_pdfplumber_selected_samples_manifest.json ^
  --output-root D:\_datefac\output ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --trial-root D:\_datefac\output\_stage1_safe_runner_trial ^
  --sandbox-delivery-dir D:\_datefac\output\_stage1_safe_runner_trial\delivery_package ^
  --execute ^
  --execute-sandbox ^
  --strict-scope
```

Then run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

### 9. Acceptance criteria
This task passes if:
1. py_compile passes.
2. --help passes.
3. sandbox execute creates trial run directory.
4. each selected sample is attempted on approved pages only.
5. at least one output xlsx is generated per sample, or a controlled per-sample failure is recorded.
6. production 01/02/02A/06 are unchanged.
7. production delivery remains PASS.
8. no factory_core/marker/surya/vision/PaddleOCR/model download occurred.
9. 27/28 reports are generated.
10. output artifacts are not committed.

A result of PARTIAL is acceptable if some samples have poor extraction but the safety guarantees hold.

## update_worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_implement_pdfplumber_sandbox_assets.md

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
- sandbox_asset_build_status
- production_delivery_status_after
- per_sample_status_summary
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Allowed to commit:
- tools/run_stage1_safe_nonvision_pipeline.py
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

If a small helper module is created, commit it only if necessary and explain why.

Do not commit:
- output/delivery_package/27_stage1_pdfplumber_sandbox_asset_build_log.md
- output/delivery_package/27_stage1_pdfplumber_sandbox_asset_build_log.xlsx
- output/delivery_package/28_stage1_pdfplumber_sandbox_asset_evaluation.md
- output/delivery_package/28_stage1_pdfplumber_sandbox_asset_evaluation.xlsx
- output/_stage1_safe_runner_trial/**
- any output artifacts

Commit:
```bat
git add tools/run_stage1_safe_nonvision_pipeline.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "add pdfplumber sandbox asset builder"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. runner_path
3. py_compile_status
4. help_status
5. sandbox_asset_build_status
6. generated_reports
7. trial_run_root
8. per_sample_status_summary
9. production_delivery_status_after
10. production_files_unchanged
11. factory_core/vision/model_download_status
12. next_step_suggestion
13. commit sha

## safety_notes
- This task creates sandbox assets only.
- Do not write Stage 1 results into production delivery_package.
- Do not run factory_core.py.
- Do not trigger vision/OCR/model backends.
- Do not modify production delivery data.
