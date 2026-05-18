# NEXT CODEX TASK

## task_title
Prepare manual review guide and pre-expansion checklist

## project
D:\_datefac

## current_status
The 02A manual year override support has been implemented and revalidated.

Known validated results from the latest revalidation:
- manual_year_override_file_status = ok
- manual_year_override_rows = 3
- manual_year_override_effective_rows = 3
- manual_year_override_applied_rows = 3
- duplicate_key_count_final = 0
- overall_status = PASS
- warn_count = 0
- fail_count = 0

Final values validated in 06:
- NET_PROFIT_ATTRIB / 2025A = 204.59, source = manual_year_override
- NET_PROFIT_ATTRIB / 2026E = 288.52, source = manual_corrected
- NET_PROFIT_ATTRIB / 2027E = 398.83, source = manual_year_override
- NET_PROFIT_ATTRIB / 2028E = 536.53, source = manual_year_override

Important issue:
- Previous worklog files still contain Chinese garbled text.
- From this task onward, write Codex worklogs in English only to avoid encoding damage.

## goal
Create user-facing operational documentation for the current delivery package workflow and a pre-expansion checklist before increasing the sample size.

Generate local output files:
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.md
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.xlsx
- D:\_datefac\output\delivery_package\13_pre_expansion_checklist.md
- D:\_datefac\output\delivery_package\13_pre_expansion_checklist.xlsx

This task must not change production data.

## hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any vision model.
4. Do not modify 01_自动可信核心指标.xlsx.
5. Do not modify 02_人工复核指标队列.xlsx.
6. Do not modify 02A_人工年份修正覆盖表.xlsx.
7. Do not modify 06_最终核心财务指标.xlsx.
8. Do not rerun apply_manual_review_corrections.py unless only a read-only report requires it; prefer not to rerun it in this task.
9. Do not expand samples.
10. Do not process PDFs again.
11. Do not commit output artifacts under output/delivery_package.
12. Only commit docs/codex_worklog updates.

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
Prepare manual review guide and pre-expansion checklist

If task_title does not match, stop immediately.

### 2. Encoding rule
All newly generated Markdown and worklog files must be written in UTF-8.

For Codex worklog files, use English only.

Use Python writing style:

```python
from pathlib import Path
Path(path).write_text(content, encoding="utf-8")
```

After writing, read files back and verify:
- no `????`
- no Unicode replacement character `�`
- no broken headings

### 3. Read current delivery state, read-only
Run:

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

Read these files without modifying them:
- D:\_datefac\output\delivery_package\01_自动可信核心指标.xlsx
- D:\_datefac\output\delivery_package\02_人工复核指标队列.xlsx
- D:\_datefac\output\delivery_package\02A_人工年份修正覆盖表.xlsx
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\06A_人工修正应用明细.xlsx
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx

Collect key facts:
- final delivery status
- current trusted rows count
- manual queue rows count
- 02A override rows count
- final rows count
- duplicate key status
- high risk flags status
- test token status
- current manual correction sources in 06/06A

### 4. Generate 12 manual review user guide
Create:
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.md
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.xlsx

The guide must explain the current manual review workflow clearly.

Markdown structure:

# Manual Review User Guide

## 1. Purpose
Explain that the delivery package now supports automatic trusted metrics, manual review queue corrections, and manual year override facts.

## 2. File Roles
Explain:
- 01_自动可信核心指标.xlsx = trusted automatic metric output; do not edit directly
- 02_人工复核指标队列.xlsx = manual review queue; use for suspicious or missing candidate metrics, one row should carry one year
- 02A_人工年份修正覆盖表.xlsx = confirmed year-level manual override fact table; use for multi-year manual corrections
- 06_最终核心财务指标.xlsx = final merged metric table; generated output, do not edit directly
- 06A_人工修正应用明细.xlsx = application detail log
- 06B_未解决问题清单.xlsx = unresolved issues
- 06D_人工复核回写诊断.xlsx = diagnostics
- 07_delivery_state_check.xlsx = delivery health check

## 3. When to Use 02
Use 02 when correcting one suspicious candidate row with one specific year.
Include required fields:
- review_status
- use_corrected_value
- corrected_value
- corrected_unit
- year
- reviewer
- reviewed_at
- reviewer_note

## 4. When to Use 02A
Use 02A when adding or overriding multiple confirmed metric-year facts, especially when one original candidate row cannot carry several years.
Explain one row = one metric + one year.

Required 02A fields:
- asset_package
- standard_metric
- year
- corrected_value
- corrected_unit
- review_status
- use_corrected_value
- reviewer
- reviewed_at
- reviewer_note
- evidence_crop_path
- source_note

## 5. Merge Priority
Explain priority:
1. 02A manual_year_override
2. 02 manual correction
3. 01 trusted automatic value

Explain duplicate/conflict principle.

## 6. Safe Operating Procedure
Step-by-step:
1. Open screenshots/PDF evidence.
2. Fill 02 or 02A depending on case.
3. Run apply_manual_review_corrections.py.
4. Run check_delivery_state.py --json.
5. Open 06/06A/06D/07 for verification.

## 7. Do Not Do
Include:
- Do not edit 01 directly.
- Do not edit 06 directly.
- Do not put multiple years into one 02 row.
- Do not use TEST / 20266 / 987654.321.
- Do not run factory_core.py during manual review validation.
- Do not trigger OCR/vision backends.

## 8. Current Accepted Sample
Summarize current accepted sample values:
- NET_PROFIT_ATTRIB 2025A = 204.59
- NET_PROFIT_ATTRIB 2026E = 288.52
- NET_PROFIT_ATTRIB 2027E = 398.83
- NET_PROFIT_ATTRIB 2028E = 536.53
- EPS 2026E = 1.65
- PE 2026E = 29.97
- EV_EBITDA 2026E = 22.76

## 9. Troubleshooting
Explain likely problems:
- file locked by WPS/Excel
- duplicated corrected_value columns
- year blank or multi-year
- corrected_value non-numeric
- check_delivery_state FAIL
- worklog encoding issue

Excel guide should include sheets:
- file_roles
- field_reference_02
- field_reference_02A
- safe_procedure
- accepted_sample
- troubleshooting

### 5. Generate 13 pre-expansion checklist
Create:
- D:\_datefac\output\delivery_package\13_pre_expansion_checklist.md
- D:\_datefac\output\delivery_package\13_pre_expansion_checklist.xlsx

Markdown structure:

# Pre-Expansion Checklist

## 1. Current Gate Status
State current delivery check result.

## 2. Must Pass Before Expanding to 30 Reports
Checklist items:
- delivery check PASS
- fail_count = 0
- warn_count = 0 or only accepted non-blocking warnings
- duplicate_key_count_final = 0
- high_risk_flags empty in 01/06
- test_token_hits empty
- 02A override diagnostics clean
- 06A has application details
- 06D diagnostics readable
- worklog readable enough for tracking

## 3. Suggested Expansion Plan
Recommend staged expansion:
- Stage 1: 3 reports
- Stage 2: 10 reports
- Stage 3: 30 reports

For each stage, list checks and stop conditions.

## 4. Stop Conditions
Stop expansion if:
- factory_core wants to download model.safetensors
- OCR/vision backends are triggered unexpectedly
- duplicate keys appear
- high-risk flags enter 01/06
- 02A conflicts unresolved
- final rows explode unexpectedly
- evidence crop paths missing in many records

## 5. Metrics to Track
Track:
- reports processed
- target reports count
- failed/non-target reports count
- 01 trusted rows
- 02 manual queue rows
- 02A override rows
- 06 final rows
- duplicate keys
- high risk rows
- test token hits
- manual applied rows
- unresolved rows

## 6. Recommended Next Technical Work
List:
- stabilize worklog encoding by using English-only Codex logs
- add a small script to summarize delivery state in Markdown
- improve 02A template generation
- add conflict tests for 02 vs 02A
- later expand samples

Excel checklist should include sheets:
- gate_status
- checklist
- expansion_plan
- stop_conditions
- metrics_to_track
- next_technical_work

### 6. Validation
After generating 12/13 files:
- Check that all Markdown files are UTF-8 readable.
- Check they do not contain `????` or `�`.
- Run check_delivery_state.py --json and confirm delivery remains PASS.
- Confirm 01/02/02A/06 were not modified by this task.

### 7. Update worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_manual_review_guide_and_expansion_checklist.md

Worklog must be English only.

result_summary must include:
- generated 12 guide md/xlsx
- generated 13 checklist md/xlsx
- delivery status
- whether output docs are free of garbled text
- whether production data files were untouched

next_step_suggestion:
- User should review 12/13 docs.
- If accepted, proceed to staged expansion starting from 3 reports, not 30 immediately.

## git_commit
Only commit worklog docs:

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare manual review guide and expansion checklist"
git push origin main
```

Do not commit output artifacts.

## expected_final_state
- Local 12 guide md/xlsx exists.
- Local 13 checklist md/xlsx exists.
- No garbled text in newly generated docs or worklog.
- delivery check remains PASS.
- 01/02/02A/06 are not modified.
- Only worklog files committed to Git.

## safety_notes
- Do not run factory_core.py.
- Do not trigger marker/surya/vision/PaddleOCR.
- Do not download model.safetensors.
- Do not modify 01/02/02A/06.
- Do not commit output artifacts.
