## Task ID

`348N-R7U Linyang / Anjing workbook family regression check`

## Task Type

regression validation / rerun / result-report task. Not an implementation task. No code or tests were modified. One result report was created. Two new R7U output directories were generated locally and not committed.

---

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 7a8f35a..bb4ae21
  Fast-forward
   ...348N_R7U_linyang_anjing_workbook_family_regression_check.md | 311 +++++
   1 file changed, 311 insertions(+)

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation (clean)

git log --oneline -12:
  bb4ae21 docs: add R7U workbook regression task
  7a8f35a docs: add R7T Taihao rerun review
  0e9344c docs: add R7T Taihao rerun task
  8d1c063 docs: add R7S QA review
  b623c58 docs: add R7S QA task
  0e09901 fix: narrow strict table clean admission
  96fb1aa docs: add R7S implementation task
  fd2325b docs: add R7R clean-boundary design
  12c451d docs: sync R7Q pilot review progress
  c7df270 docs: add R7Q workbook family pilot review
  84783a9 docs: update handoff for R7Q pilot review
  1124183 docs: add R7Q workbook family pilot review task
```

Worktree was clean after pull.

---

## Files and artifacts reviewed

Read-only review:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/项目进程.md`
- `项目进展大白话说明.md`
- `docs/codex_tasks/348N_R7T_taihao_strict_table_scaffolding_clean_boundary_pilot_rerun.md`
- `docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md`
- `docs/codex_tasks/348N_R7S_QA_strict_table_scaffolding_clean_boundary_review.md`
- `docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md`
- `docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md`
- `datefac_agent/review/clean_candidate_policy.py` (read-only)
- `tests/agent/test_agent_excel_intake_audit_348a.py` (read-only)

Baseline outputs (read-only):

- `output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail/agent_excel_intake_audit_348a_manifest.json` (Linyang baseline)
- `output/agent_excel_intake_audit_348a_r4/agent_excel_intake_audit_348a_manifest.json` (Anjing baseline)

R7U generated outputs (read for this report, not committed):

- `output/agent_excel_intake_audit_348n_r7u_linyang_regression_check/` (manifest, clean_data.csv, review_queue.csv)
- `output/agent_excel_intake_audit_348n_r7u_anjing_regression_check/` (manifest, clean_data.csv, review_queue.csv)

---

## Discovered Linyang inputs and baselines

```text
Linyang workbook:
  input/linyang_energy_pdf_extracted_testset (1).xlsx

Linyang source PDF:
  input/6862e6f3995d3dbfbed310b51601fb0a.pdf

Linyang baseline output (post-R6B-FIX, pre-R7P-FIX2, pre-R7S):
  output/agent_excel_intake_audit_348n_r6b_fix_clean_data_csv_row_count_guardrail/

Linyang baseline manifest key values:
  clean_data_row_count = 0
  clean_data_csv_row_count = 0
  review_queue_row_count = 489
  review_queue_csv_row_count = 46
  unknown_row_count = 0
  market_reference_row_count = 10
  strict_financial_table_row_count = 76
  normalized_testset_record_row_count = 320
  testset_supporting_row_count = 83
```

Note: the Linyang baseline is from the R6B-FIX stage. It predates R7P-FIX2 (MARKET_REFERENCE_ROW policy) and R7S (scaffolding guard). Linyang clean_data was already 0 at that baseline because R5 moved qualitative_facts rows to review-only. Therefore R7S is not expected to change Linyang clean_data (it is already 0, and Linyang strict-table rows are STRONG_EVIDENCE, not WEAK_EVIDENCE, so the R7S guard does not apply).

---

## Discovered Anjing inputs and baselines

```text
Anjing workbook:
  input/安井食品研报数据汇总.xlsx

Anjing source PDF:
  input/H3_AP202606081823352906_1_331fresh_20260615_21591.pdf

Anjing baseline output (R4 stage, pre-R7P-FIX2, pre-R7S):
  output/agent_excel_intake_audit_348a_r4/

Anjing baseline manifest key values:
  clean_data_row_count = 75
  review_queue_row_count = 7
  unknown_row_count = 0
  market_reference_row_count = 10
  strict_financial_table_row_count = 67
  internal_clean_candidate_count = 65
  internal_reference_candidate_count = 10
  (clean_data_csv_row_count field absent: R4 predates R6B csv-count fields)
```

Note: the Anjing R4 baseline predates R7P-FIX2 and R7S. At R4, clean_data = 75 = 65 INTERNAL_CLEAN_CANDIDATE + 10 INTERNAL_REFERENCE_CANDIDATE (MARKET_REFERENCE_ROW). After R7P-FIX2, those 10 MARKET_REFERENCE_ROW rows must move to review. R7S is not expected to remove any of the 65 numeric INTERNAL_CLEAN_CANDIDATE rows because Anjing strict-table rows carry numeric period_values.

---

## Exact rerun commands

```text
Linyang:
  D:\anaconda\python.exe tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/6862e6f3995d3dbfbed310b51601fb0a.pdf" --excel-path "input/linyang_energy_pdf_extracted_testset (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7u_linyang_regression_check"

Anjing:
  D:\anaconda\python.exe tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202606081823352906_1_331fresh_20260615_21591.pdf" --excel-path "input/安井食品研报数据汇总.xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7u_anjing_regression_check"
```

Same runner pattern as R7T.

---

## Manifest summary for each family

### Linyang R7U manifest

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
sheet_count = 14
row_count_total = 489
row_count_audited = 489
strict_financial_table_row_count = 76
market_reference_row_count = 10
narrative_assertion_count = 0
normalized_testset_record_row_count = 320
testset_supporting_row_count = 83
unknown_row_count = 0
clean_data_row_count = 0
clean_data_csv_row_count = 0
review_queue_row_count = 489
review_queue_csv_row_count = 46
internal_clean_candidate_count = 0
internal_reference_candidate_count = 0
review_required_count = 489
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

### Anjing R7U manifest

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
sheet_count = 6
row_count_total = 82
row_count_audited = 82
strict_financial_table_row_count = 67
market_reference_row_count = 10
narrative_assertion_count = 5
normalized_testset_record_row_count = 0
testset_supporting_row_count = 0
unknown_row_count = 0
clean_data_row_count = 65
clean_data_csv_row_count = 65
review_queue_row_count = 17
review_queue_csv_row_count = 17
internal_clean_candidate_count = 65
internal_reference_candidate_count = 0
narrative_review_count = 5
review_required_count = 12
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Both reruns completed with no guardrail failure.

---

## Clean/review count comparison

### Linyang

```text
                          R6B-FIX baseline    R7U (post-R7S)    delta
clean_data_row_count      0                   0                 0
clean_data_csv_row_count  0                   0                 0
review_queue_row_count    489                 489               0
review_queue_csv_row_count 46                 46                0
unknown_row_count         0                   0                 0
market_reference_row_count 10                 10                0
```

Linyang: no change. R7S did not regress Linyang.

### Anjing

```text
                          R4 baseline         R7U (post-R7S)    delta    cause
clean_data_row_count      75                  65                -10      R7P-FIX2 (MARKET_REFERENCE_ROW moved out)
review_queue_row_count    7                   17                +10      R7P-FIX2 (MARKET_REFERENCE_ROW moved in)
unknown_row_count         0                   0                 0
market_reference_row_count 10                 10                0
internal_clean_candidate_count 65             65                0        R7S did not change this
internal_reference_candidate_count 10         0                 -10      R7P-FIX2 (no longer INTERNAL_REFERENCE_CANDIDATE)
```

Anjing: the clean_data drop from 75 to 65 is entirely attributable to R7P-FIX2 (MARKET_REFERENCE_ROW no longer enters clean_data). The R7S scaffolding guard did not remove any row: `internal_clean_candidate_count` remained 65 (65 -> 65). R7S did not regress Anjing.

Note: the Anjing R4 baseline predates R6B csv-count fields, so direct csv-row-count comparison is not available for R4. The R7U csv counts (65 / 17) are internally consistent with the logical counts.

---

## Forbidden clean row_type check

```text
Linyang clean_data.csv: 0 data rows; row_type set = EMPTY (no forbidden row_type)
Anjing clean_data.csv: 65 data rows; row_type set = {STRICT_FINANCIAL_TABLE_ROW}; candidate_type set = {INTERNAL_CLEAN_CANDIDATE}
forbidden_clean_row_type_found = no (neither MARKET_REFERENCE_ROW / TESTSET_SUPPORTING_ROW / NORMALIZED_TESTSET_RECORD_ROW / UNKNOWN_ROW appears in either clean_data.csv)
```

---

## Market reference boundary check

```text
Linyang: market_reference_row_count = 10 (stable vs baseline 10); clean_data has no MARKET_REFERENCE_ROW
Anjing: market_reference_row_count = 10 (stable vs baseline 10); all 10 MARKET_REFERENCE_ROW rows are in review_queue.csv (verified: 总市值, 总股本, 流通A股市值, 每股净资产, etc.); clean_data has no MARKET_REFERENCE_ROW
market_reference_boundary_ok = yes
```

---

## Normal financial fact preservation check

```text
Linyang: clean_data_row_count = 0 (unchanged from baseline; Linyang has no clean_data by design, so nothing to preserve)
Anjing: clean_data contains 65 INTERNAL_CLEAN_CANDIDATE STRICT_FINANCIAL_TABLE_ROW rows with numeric period_values.
  Sample metric_names preserved: 营业收入(百万元), YoY(%), 净利润(百万元), YoY(%), 毛利率(%), ...
  internal_clean_candidate_count = 65 (unchanged from R4 baseline 65)
normal_fact_preservation_ok = yes
```

R7S did not over-filter any legitimate numeric fact row in either family.

---

## Over-filter risk check

```text
Linyang over-filter risk = none
  - clean_data remained 0 (no rows to over-filter)
  - Linyang strict-table rows are STRONG_EVIDENCE (461 strong / 28 weak), so the R7S WEAK_EVIDENCE-only guard does not apply to most rows
  - review_queue_row_count and review_queue_csv_row_count unchanged

Anjing over-filter risk = none
  - internal_clean_candidate_count remained 65 (65 -> 65)
  - the 10-row clean_data decrease is fully explained by R7P-FIX2 (internal_reference_candidate_count 10 -> 0), not by R7S
  - no numeric fact row was routed to review by the scaffolding guard
  - review_queue increase (+10) matches exactly the MARKET_REFERENCE_ROW migration, with no extra rows from R7S
```

R7S scaffolding guard over-filtered zero legitimate rows across both families.

---

## Readiness gates

```text
                          Linyang R7U         Anjing R7U
client_ready               false               false
production_ready           false               false
formal_client_export_allowed false             false
demo_export_only           true                true
llm_api_call_count         0                   0
mineru_run_count           0                   0
ocr_run_count              0                   0
legacy_datefac_touched     false               false
legacy_outputs_touched     false               false
formal_export_generated    false               false
```

All readiness gates remained closed for both families. Output remained demo-only and not formal-client-export ready.

---

## Output artifact policy

Two new R7U output directories were generated locally:

```text
output/agent_excel_intake_audit_348n_r7u_linyang_regression_check/
output/agent_excel_intake_audit_348n_r7u_anjing_regression_check/
```

These directories were created only for this R7U regression check as allowed by the task. No previous output directory was modified. Output files are local generated artifacts only and are not staged or committed (output/ is gitignored).

---

## Validation outputs

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
  -> COMPILE_OK

pytest tests/agent -q
  -> 86 passed in 1.14s

Linyang rerun:
  -> completed successfully, no guardrail failure

Anjing rerun:
  -> completed successfully, no guardrail failure

git status -sb (after report, before staging):
  -> ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
     ?? docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md
     (R7U output dirs are gitignored, do not appear)

git diff --stat       -> (no output; clean)
git diff --name-only  -> (no output; clean)
git diff --check      -> (no output; clean)
```

---

## Validation Questions (answers per family)

### Linyang

1. **Did the rerun complete without a new guardrail failure?** Yes.
2. **Manifest decision?** `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX` (qa_fail_count=0, review pressure only).
3. **clean_data logical and physical counts?** logical 0, physical csv 0.
4. **review_queue logical and physical counts?** logical 489, physical csv 46.
5. **Logical and physical aligned?** Yes (0==0, 489 logical vs 46 csv — the csv count is the REVIEW/FAIL-only physical subset per runner semantics, consistent with baseline).
6. **unknown_row_count acceptable?** Yes, 0 (unchanged).
7. **market_reference behavior stable?** Yes, 10 (unchanged), none in clean_data.
8. **Forbidden row_type in clean_data?** No.
9. **Normal numeric fact rows remained in clean_data?** N/A — clean_data is 0 by Linyang design (qualitative_facts routed to review in R5); nothing to preserve, nothing lost.
10. **R7S over-filter legitimate rows?** No. clean_data stayed 0; no row was newly routed to review by R7S.
11. **Readiness gates closed?** Yes.
12. **Output demo-only?** Yes.

### Anjing

1. **Did the rerun complete without a new guardrail failure?** Yes.
2. **Manifest decision?** `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX` (qa_fail_count=0, review pressure only).
3. **clean_data logical and physical counts?** logical 65, physical csv 65.
4. **review_queue logical and physical counts?** logical 17, physical csv 17.
5. **Logical and physical aligned?** Yes (65==65, 17==17).
6. **unknown_row_count acceptable?** Yes, 0 (unchanged).
7. **market_reference behavior stable?** Yes, 10 (unchanged); all 10 in review_queue, none in clean_data.
8. **Forbidden row_type in clean_data?** No. clean_data row_type set = {STRICT_FINANCIAL_TABLE_ROW}.
9. **Normal numeric fact rows remained in clean_data?** Yes. internal_clean_candidate_count = 65 (unchanged from R4 baseline 65). Sample: 营业收入, YoY, 净利润, 毛利率.
10. **R7S over-filter legitimate rows?** No. The 10-row clean_data decrease is entirely from R7P-FIX2 (MARKET_REFERENCE_ROW). internal_clean_candidate_count 65->65 proves R7S removed zero numeric fact rows.
11. **Readiness gates closed?** Yes.
12. **Output demo-only?** Yes.

---

## Decision

`348N_R7U_CONFIRMED_NO_R7S_REGRESSION_ACROSS_LINYANG_AND_ANJING`

The R7S strict-table scaffolding clean-boundary guard did not regress either prior workbook family:

- **Linyang**: clean_data 0 (unchanged), review_queue 489 (unchanged), review_queue_csv 46 (unchanged), unknown 0, market_reference 10. No change at all.
- **Anjing**: clean_data 75 -> 65, but the entire -10 delta is attributable to R7P-FIX2 (MARKET_REFERENCE_ROW no longer enters clean_data; internal_reference_candidate_count 10 -> 0). The R7S guard removed zero rows: internal_clean_candidate_count stayed 65 (65 -> 65). All 65 numeric fact rows preserved.
- No forbidden row_type entered clean_data in either family.
- 收盘价/总市值 market reference boundary intact in both families.
- No guardrail failure in either rerun.
- All readiness gates remained closed.
- No external calls were made.

The R7S guard is confirmed safe across all three workbook families (Taihao in R7T, Linyang and Anjing in R7U).

---

## Recommended next task

```text
348N-R7V cross-family clean-boundary summary and readiness review
```

Purpose:

- summarize the R7R design, R7S implementation, R7S-QA review, R7T Taihao rerun, and R7U Linyang/Anjing regression check into a single cross-family clean-boundary status report;
- confirm the strict-table scaffolding guard is stable across all three workbook families;
- update the project milestone ledger / handoff to reflect the completed R7S-R7U clean-boundary work;
- keep all readiness gates closed;
- recommend whether to open the next workbook family pilot or move to a different mainline topic.

This is a separate task. This R7U task does not start it.

---

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7U_CONFIRMED_NO_R7S_REGRESSION_ACROSS_LINYANG_AND_ANJING
build_result（构建结果）= COMPILE_OK
test_result（测试结果）= tests/agent 86 passed
linyang_rerun_result（林洋重跑结果）= completed, no guardrail failure, clean_data=0 (unchanged), review_queue=489 (unchanged)
anjing_rerun_result（安井重跑结果）= completed, no guardrail failure, clean_data=65 (R7S removed 0 rows; -10 vs R4 baseline is from R7P-FIX2 MARKET_REFERENCE_ROW)
linyang_clean_data_row_count（林洋clean逻辑行数）= 0
linyang_review_queue_row_count（林洋review逻辑行数）= 489
anjing_clean_data_row_count（安井clean逻辑行数）= 65
anjing_review_queue_row_count（安井review逻辑行数）= 17
forbidden_clean_row_type_found（clean中是否发现禁止row_type）= no
market_reference_boundary_ok（市场引用边界是否正常）= yes
normal_fact_preservation_ok（正常事实是否保留）= yes
readiness_gates（就绪门）= closed (client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true)
output_committed（是否提交output）= no (output generated locally, gitignored, not staged, not committed)
files_modified（修改文件数）= 1 (R7U report only; no code/test/input/output changes)
error_count（错误数）= 0
boundary_check（边界检查）= passed (only the allowed R7U report created; no code/test/input/previous-output/temp/data/legacy/config/guardrails/row_type_classifier/qualitative_facts/MARKET_REFERENCE_ROW/readiness-gate changes; output not committed)
recommended_next_task（推荐下一任务）= 348N-R7V cross-family clean-boundary summary and readiness review
```
