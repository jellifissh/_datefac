# NEXT CODEX TASK

## task_title
Fix manual review guide accepted sample validation

## project
D:\_datefac

## current_status
The previous task generated:
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.xlsx
- D:\_datefac\output\delivery_package\13_pre_expansion_checklist.xlsx

User review found:
- 13_pre_expansion_checklist.xlsx is mostly acceptable.
- 12_manual_review_user_guide.xlsx has a problem in sheet `accepted_sample`.

Observed issue in 12_manual_review_user_guide.xlsx:
- NET_PROFIT_ATTRIB rows show expected values but `actual_final_value` is blank and `value_match=false`.
- EPS 2026E also shows blank actual_final_value and `value_match=false`.
- PE 2026E and EV_EBITDA 2026E are matched correctly.

Likely cause:
- The guide generator used English metric_code values such as NET_PROFIT_ATTRIB and EPS, but 06_最终核心财务指标.xlsx may store Chinese standard_metric values such as 归属母公司净利润 and 每股收益.
- This makes the user guide look like the accepted sample failed, even though previous validation proved 02A and 06 values are correct.

## goal
Regenerate only the 12 manual review guide files so that `accepted_sample` correctly reflects the verified final values.

Target local files:
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.md
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.xlsx

Do not regenerate 13 unless needed.
Do not modify production data.

## hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any vision model.
4. Do not modify 01_自动可信核心指标.xlsx.
5. Do not modify 02_人工复核指标队列.xlsx.
6. Do not modify 02A_人工年份修正覆盖表.xlsx.
7. Do not modify 06_最终核心财务指标.xlsx.
8. Do not rerun apply_manual_review_corrections.py.
9. Do not expand samples.
10. Do not process PDFs again.
11. Do not commit output artifacts under output/delivery_package.
12. Only commit docs/codex_worklog updates.
13. Worklog must be English only and UTF-8.

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
Fix manual review guide accepted sample validation

If task_title does not match, stop immediately.

### 2. Read current delivery state, read-only
Run:

```bat
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

Read without modifying:
- D:\_datefac\output\delivery_package\06_最终核心财务指标.xlsx
- D:\_datefac\output\delivery_package\06A_人工修正应用明细.xlsx
- D:\_datefac\output\delivery_package\06D_人工复核回写诊断.xlsx
- D:\_datefac\output\delivery_package\07_delivery_state_check.xlsx
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.xlsx

### 3. Fix accepted_sample matching logic
The corrected accepted_sample table must include these expected rows and must match them from 06 using Chinese standard_metric values if needed:

| metric_code | standard_metric_alias | year | expected_value | expected_source_hint |
|---|---|---|---:|---|
| NET_PROFIT_ATTRIB | 归属母公司净利润 | 2025A | 204.59 | manual_year_override |
| NET_PROFIT_ATTRIB | 归属母公司净利润 | 2026E | 288.52 | manual_corrected |
| NET_PROFIT_ATTRIB | 归属母公司净利润 | 2027E | 398.83 | manual_year_override |
| NET_PROFIT_ATTRIB | 归属母公司净利润 | 2028E | 536.53 | manual_year_override |
| EPS | 每股收益 | 2026E | 1.65 | manual_added |
| PE | P/E | 2026E | 29.97 | manual_added |
| EV_EBITDA | EV/EBITDA | 2026E | 22.76 | manual_added |

The regenerated accepted_sample sheet should contain:
- metric_code
- standard_metric_alias
- year
- expected_value
- actual_final_value
- expected_source_hint
- actual_final_source
- value_match
- source_match
- validation_note

All seven rows should have:
- value_match = TRUE
- source_match = TRUE or source_match = acceptable if source names are equivalent

### 4. Regenerate 12 guide
Regenerate:
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.md
- D:\_datefac\output\delivery_package\12_manual_review_user_guide.xlsx

Keep existing useful sheets:
- file_roles
- field_reference_02
- field_reference_02A
- safe_procedure
- accepted_sample
- troubleshooting

Add or improve a sheet if useful:
- accepted_sample_validation

Do not introduce garbled text. Prefer English in generated guide text where possible, while preserving file names and metric names.

### 5. Validation
After regeneration:
- Verify 12_manual_review_user_guide.xlsx accepted_sample has no blank actual_final_value for the seven accepted rows.
- Verify all seven expected accepted rows pass value matching.
- Verify no `????` or `�` appears in 12 md/xlsx text cells.
- Verify delivery state remains PASS.
- Verify 01/02/02A/06 were not modified.

### 6. Update worklog
Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_fix_manual_guide_accepted_sample.md

Worklog must be English only.

result_summary must include:
- regenerated 12 guide md/xlsx
- accepted_sample row count
- accepted_sample matched row count
- delivery status
- whether output docs are free of garbled text
- whether production data files were untouched

next_step_suggestion:
- If accepted_sample is fixed, review 12/13 docs and then prepare staged expansion starting from 3 reports.

## git_commit
Only commit worklog docs:

```bat
git add docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "fix manual guide accepted sample validation"
git push origin main
```

Do not commit output artifacts.

## expected_final_state
- Local 12 guide md/xlsx regenerated.
- accepted_sample correctly validates all seven accepted sample rows.
- delivery check remains PASS.
- 01/02/02A/06 are not modified.
- Only worklog files committed to Git.

## safety_notes
- Do not run factory_core.py.
- Do not trigger marker/surya/vision/PaddleOCR.
- Do not download model.safetensors.
- Do not modify 01/02/02A/06.
- Do not commit output artifacts.
