# NEXT CODEX TASK

## task_title
Prepare Stage 1 visual confirmation packet

## project
D:\_datefac

## current_status
The Stage 1 manual inspection packet has been reviewed.

Uploaded/reviewed file:
- D:\_datefac\output\delivery_package\19_stage1_manual_inspection_packet.xlsx

Latest 19 packet summary:
- delivery_status = PASS / pass_count=17 / warn_count=0 / fail_count=0
- selected_samples_count = 3
- high_confidence_candidate_count = 0
- medium_confidence_candidate_count = 14
- low_confidence_candidate_count = 40
- proposed gates:
  - H3_AP202605141822317484_1 = NEEDS_VISUAL_CONFIRMATION
  - H3_AP202605121822223662_1 = NEEDS_VISUAL_CONFIRMATION
  - H3_AP202605141822318060_1 = NEEDS_VISUAL_CONFIRMATION

Important interpretation:
The samples are not blocked and not non-target. They have medium-confidence candidate tables, but probe text/keyword evidence is not strong enough to directly promote them to the full safe pipeline. The next step is to generate a visual confirmation packet from existing PDFs/probe candidate pages, without using OCR or vision models.

## goal
Generate a Stage 1 visual confirmation packet for human review.

Local outputs:
- D:\_datefac\output\delivery_package\20_stage1_visual_confirmation_index.md
- D:\_datefac\output\delivery_package\20_stage1_visual_confirmation_index.xlsx

Also create per-sample preview folders:
- D:\_datefac\output\H3_AP202605141822317484_1_资产包\_stage1_visual_confirmation\
- D:\_datefac\output\H3_AP202605121822223662_1_资产包\_stage1_visual_confirmation\
- D:\_datefac\output\H3_AP202605141822318060_1_资产包\_stage1_visual_confirmation\

This task must generate static page/table crop previews using local rendering only, such as PyMuPDF or pdfplumber page rendering. This is not OCR and not model vision.

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
12. Use local static PDF rendering only. No OCR. No AI vision. No external downloads.
13. If crop bbox is unavailable, render the full relevant page instead of failing.

## selected_samples
Use exactly these samples:

1. H3_AP202605141822317484_1.pdf
   company: 三鑫医疗
   candidate pages from 19:
   - page 1: core metric table / Table_MainProfit candidate
   - page 4: business forecast table candidate
   - page 5: full financial forecast table candidate

2. H3_AP202605121822223662_1.pdf
   company: 冠豪高新
   candidate pages from 19:
   - page 2: core indicators table candidate
   - page 3: full financial forecast / income statement / ratio / cash flow candidates

3. H3_AP202605141822318060_1.pdf
   company: 科锐国际
   candidate pages from 19:
   - page 5: full financial forecast / valuation table candidate
   - page 6: likely rating table only, include only as negative/ignore evidence if already present in probe outputs

Baseline sample remains regression guard only:
- H3_AP202605091822098939_1.pdf
Do not render it unless only checking it remains untouched.

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
Prepare Stage 1 visual confirmation packet

If not matched, stop.

### 2. Read delivery state, read-only
Run:
```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```
Record current delivery status.

### 3. Locate PDFs
Locate selected PDFs under D:\_datefac by exact filename:
- H3_AP202605141822317484_1.pdf
- H3_AP202605121822223662_1.pdf
- H3_AP202605141822318060_1.pdf

If any PDF is missing, mark that sample BLOCKED_FOR_VISUAL_CONFIRMATION and continue with other samples.

### 4. Generate static page previews
For each candidate page listed above:
- Render a readable full-page PNG at sufficient zoom, e.g. 180-220 DPI or PyMuPDF matrix scale 2.0.
- If table bboxes are discoverable from existing _stage1_probe outputs, also render table crop PNGs.
- If bbox is unavailable, full-page PNG is acceptable.

Save previews under each sample folder:
D:\_datefac\output\<asset_package>\_stage1_visual_confirmation\

Recommended naming:
- page_001_full.png
- page_004_full.png
- page_005_full.png
- table_candidate_page_005_table_001.png

Do not use OCR. Do not call any vision model.

### 5. Generate confirmation index
Create:
- D:\_datefac\output\delivery_package\20_stage1_visual_confirmation_index.md
- D:\_datefac\output\delivery_package\20_stage1_visual_confirmation_index.xlsx

The index must contain, for each preview:
- sample_id
- company
- candidate_page
- candidate_role
- preview_type: full_page / table_crop
- preview_path
- expected_table_type
- expected_years
- expected_core_metrics
- visual_check_instruction
- proposed_decision_after_visual_check: approve_for_full_safe_pipeline / hold / ignore

Expected core metric checks:
- 三鑫医疗 page 1 should show a core metric table with 营业收入、归属母公司净利润、EPS、ROE、PE、PB style metrics.
- 三鑫医疗 page 5 should show full financial forecast / valuation data.
- 冠豪高新 page 2/3 should show financial forecast tables with negative or abnormal value cases.
- 科锐国际 page 5 should show financial forecast and valuation table, including years without A suffix or mixed 2024/2025/2026E/2027E/2028E.
- 科锐国际 page 6 should be marked as likely rating/disclaimer table and usually ignored.

Markdown structure:

# Stage 1 Visual Confirmation Index

## Summary
- generated_at
- delivery_status
- selected_samples_count
- preview_count
- missing_pdf_count
- overall_recommendation

## Important Clarification
Explain this is static visual confirmation only, not OCR, not vision, not full pipeline.

## Per-Sample Visual Checks
For each sample:
- candidate pages
- preview paths
- what user should check
- likely decision

## Decision Rules
Approve sample for full safe pipeline only if:
1. At least one preview clearly contains a core financial forecast or valuation table.
2. Year columns are visible.
3. Core metrics are visible.
4. Units are visible or inferable from table title.
5. No sign that the table is only a rating/disclaimer/legal table.

Hold sample if:
- table is fragmented beyond readable structure
- only years are visible but no metric rows
- page is mostly rating/disclaimer/legal content

## Recommended Next Step
If all three have usable previews, recommend:
Run full safe non-vision pipeline for Stage 1 visually approved samples

If only some are usable, recommend running only those approved samples.

Excel sheets required:
- summary
- visual_index
- per_sample_checks
- decision_rules
- ignored_candidates
- missing_files

### 6. Validate generated outputs
Verify:
- 20 md/xlsx exist
- preview PNG files exist for each relevant sample/page
- no `????`
- no Unicode replacement char `�`
- current delivery state remains PASS
- 01/02/02A/06 production files unchanged

### 7. Update worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_stage1_visual_confirmation_packet.md

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
- preview_count_by_sample
- missing_pdf_count
- delivery_status
- result_summary
- remaining_issues
- next_step_suggestion
- safety_notes

## git_commit
Only commit worklog:
```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare stage1 visual confirmation packet"
git push origin main
```

Do not commit:
- output/delivery_package/20_stage1_visual_confirmation_index.md
- output/delivery_package/20_stage1_visual_confirmation_index.xlsx
- PNG previews
- any output artifacts

## expected_final_response
After completion, output:
1. task_title
2. delivery_status
3. generated_reports
4. preview_count_by_sample
5. missing_pdf_count
6. whether production data was untouched
7. whether output docs contain garbled text
8. next_step_suggestion
9. commit sha

## safety_notes
- This is static visual confirmation packet generation only.
- Do not run factory_core.py.
- Do not run full delivery pipeline.
- Do not modify production delivery data.
- Do not commit output artifacts.
