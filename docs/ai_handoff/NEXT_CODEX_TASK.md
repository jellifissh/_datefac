# NEXT CODEX TASK

## task_title
Prepare Stage 1 manual inspection packet from probe outputs

## project
D:\_datefac

## current_status
Stage 1 probe quality review has been completed.

Latest review result:
- delivery_status = PASS / pass_count=17 / warn_count=0 / fail_count=0
- ready_count = 0
- manual_inspection_count = 3
- blocked_count = 0
- non_target_count = 0

Per-sample gate decisions:
- H3_AP202605141822317484_1 = NEEDS_MANUAL_INSPECTION
- H3_AP202605121822223662_1 = NEEDS_MANUAL_INSPECTION
- H3_AP202605141822318060_1 = NEEDS_MANUAL_INSPECTION

Important clarification:
The probe stage only proved safe table detection did not break anything. It did not integrate the three samples into 01/02/06. The next step is to inspect the probe outputs and decide whether there is enough table evidence to run the full safe non-vision pipeline later.

## goal
Create a human-readable Stage 1 manual inspection packet from existing probe outputs.

Generate local reports:
- D:\_datefac\output\delivery_package\19_stage1_manual_inspection_packet.md
- D:\_datefac\output\delivery_package\19_stage1_manual_inspection_packet.xlsx

The packet should help the user decide whether each sample can proceed to the full safe non-vision pipeline.

This is a review/inspection task only. Do not run full processing.

## hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any vision model.
4. Do not run full extraction / standardization / delivery rebuild.
5. Do not run apply_manual_review_corrections.py.
6. Do not modify 01_自动可信核心指标.xlsx.
7. Do not modify 02_人工复核指标队列.xlsx.
8. Do not modify 02A_人工年份修正覆盖表.xlsx.
9. Do not modify 06_最终核心财务指标.xlsx.
10. Do not commit output artifacts.
11. Worklog must be English only and UTF-8.
12. Prefer reading existing _stage1_probe outputs. Do not rerun probe_pdf_tables.py unless a selected sample has missing or unreadable probe output.
13. If rerunning probe is absolutely required, use only probe_pdf_tables.py with the same safe non-vision constraints.

## selected_samples
Inspect exactly these asset folders:

1. D:\_datefac\output\H3_AP202605141822317484_1_资产包
   - company: 三鑫医疗
   - expected target evidence: page 1 core metric table, page 4 business forecast table, page 5 full financial forecast table

2. D:\_datefac\output\H3_AP202605121822223662_1_资产包
   - company: 冠豪高新
   - expected target evidence: financial summary / forecast tables with negative or abnormal values

3. D:\_datefac\output\H3_AP202605141822318060_1_资产包
   - company: 科锐国际
   - expected target evidence: core forecast / valuation tables, possible years like 2024/2025/2026E/2027E/2028E without A suffix

Baseline sample remains regression guard only:
- H3_AP202605091822098939_1.pdf
Do not inspect it as a Stage 1 selected sample unless only checking that it remains untouched.

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
Prepare Stage 1 manual inspection packet from probe outputs

If not matched, stop.

### 2. Read delivery state, read-only
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```
Record current delivery status.

### 3. Read existing Stage 1 probe outputs
For each selected asset folder, inspect:
- 16_stage1_execution_log.md/xlsx
- 17_stage1_result_evaluation.md/xlsx
- _stage1_probe directory
- any CSV / XLSX / JSON / TXT / MD / HTML outputs created by probe_pdf_tables.py

Do not assume file names. Recursively list _stage1_probe and summarize relevant files.

### 4. Extract candidate table previews
For each sample, find likely target tables using keyword and year-column heuristics.

Year-like columns / cells:
- 2024A, 2025A, 2026E, 2027E, 2028E
- 2024, 2025, 2026, 2027, 2028
- 2024/2025/2026E/2027E/2028E style variants

Core metric keywords:
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

For each candidate table, record:
- sample_id
- company
- source_file
- page number if available
- table index if available
- row_count
- column_count
- detected_year_cells
- metric_keyword_hits
- raw_text_preview
- top 15 rows or readable compact preview
- confidence: high / medium / low
- candidate_type: core_metrics / full_financial_forecast / business_forecast / other_year_table
- recommended_action: inspect_visual / ready_for_full_safe_pipeline_candidate / ignore

### 5. Optional safe visual support
If existing probe outputs include table bbox/page references and local PDF files are available, it is allowed to generate non-vision static table/page crop previews for human inspection using pdfplumber/PyMuPDF/local rendering only.

Rules:
- This is not OCR and not vision model inference.
- Do not use marker/surya/PaddleOCR/vision.
- Save any previews under the related asset folder, for example:
  D:\_datefac\output\<asset_package>\_stage1_manual_inspection\
- If safe crop generation is not straightforward, skip it and rely on table text previews.
- Do not fail the task just because crops are unavailable.

### 6. Gate recommendation after manual inspection packet
For each sample, assign a proposed next gate:
- READY_FOR_FULL_SAFE_PIPELINE_CANDIDATE if there is at least one high/medium confidence table that has both year cells and multiple core metric keyword hits.
- NEEDS_VISUAL_CONFIRMATION if table text exists but metric semantics are incomplete/fragmented.
- HOLD if no usable target table is found but sample is still a company report.
- NON_TARGET if clearly not a target company financial forecast report.

Important: do not mark a sample as fully ready merely because it has year-like rows. It must have metric keyword evidence.

### 7. Generate 19 manual inspection packet
Create:
- D:\_datefac\output\delivery_package\19_stage1_manual_inspection_packet.md
- D:\_datefac\output\delivery_package\19_stage1_manual_inspection_packet.xlsx

Markdown must contain:

# Stage 1 Manual Inspection Packet

## Summary
- generated_at
- delivery_status
- selected_samples_count
- high_confidence_candidate_count
- medium_confidence_candidate_count
- low_confidence_candidate_count
- proposed_next_gate_summary

## Important Clarification
Explain that this packet is based on probe outputs and table previews, not full delivery integration.

## Per-Sample Candidate Tables
For each sample:
- sample_id
- company
- candidate tables found
- year evidence
- metric keyword evidence
- compact table previews
- confidence
- proposed next gate

## Manual Inspection Checklist
For each sample, list exactly what the user should visually confirm before full pipeline:
- Does the candidate table contain core financial metrics?
- Are year columns correctly recognized?
- Are units clear?
- Are negative values valid rather than parsing errors?
- Are metrics split across multiple pages/tables?

## Recommended Next Action
Choose one:
- Run full safe non-vision pipeline for candidates that pass inspection
- Ask user to upload/inspect specific table screenshots first
- Hold blocked samples

Excel must include sheets:
- summary
- file_inventory
- candidate_tables
- keyword_hits
- table_previews
- proposed_gates
- manual_checklist

### 8. Validate generated docs
Verify:
- 19 md/xlsx exist
- no `????`
- no Unicode replacement char `�`
- output docs are readable
- 01/02/02A/06 production files unchanged
- current delivery state remains PASS

### 9. Update worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_stage1_manual_inspection_packet.md

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
- selected_samples
- candidate_table_summary
- proposed_gates
- delivery_status
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Only commit worklog:
```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare stage1 manual inspection packet"
git push origin main
```

Do not commit:
- output/delivery_package/19_stage1_manual_inspection_packet.md
- output/delivery_package/19_stage1_manual_inspection_packet.xlsx
- any output artifacts

## expected_final_response
After completion, output:
1. task_title
2. delivery_status
3. generated_reports
4. candidate_table_counts_by_sample
5. proposed_gates_by_sample
6. whether production data was untouched
7. whether output docs contain garbled text
8. next_step_suggestion
9. commit sha

## safety_notes
- This is manual inspection packet generation only.
- Do not run factory_core.py.
- Do not run full delivery pipeline.
- Do not modify production delivery data.
- Do not commit output artifacts.
