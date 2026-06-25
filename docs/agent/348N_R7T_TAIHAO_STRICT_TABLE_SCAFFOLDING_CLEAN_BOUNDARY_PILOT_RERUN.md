## Task ID

`348N-R7T Taihao strict_table scaffolding clean-boundary pilot rerun`

## Task Type

validation / rerun / result-report task. Not an implementation task. No code or tests were modified. One result report was created. One new R7T output directory was generated locally and not committed.

---

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 8d1c063..0e9344c
  Fast-forward
   ...348N_R7T_taihao_strict_table_scaffolding_clean_boundary_pilot_rerun.md | 345 +++++
   1 file changed, 345 insertions(+)

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation (clean)

git log --oneline -10:
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
- `docs/codex_tasks/348N_R7S_QA_strict_table_scaffolding_clean_boundary_review.md`
- `docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md`
- `docs/codex_tasks/348N_R7S_strict_table_pseudo_header_comparison_row_clean_boundary_implementation.md`
- `docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md`
- `datefac_agent/review/clean_candidate_policy.py` (read-only)
- `tests/agent/test_agent_excel_intake_audit_348a.py` (read-only)

R7Q baseline output (read-only comparison):

- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json`
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv`
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/review_queue.csv`

R7T generated output (read for this report, not committed):

- `output/agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun/agent_excel_intake_audit_348a_manifest.json`
- `output/agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun/clean_data.csv`
- `output/agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun/review_queue.csv`

---

## Exact rerun command

```text
D:\anaconda\python.exe tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun"
```

This is the same runner pattern used for the R7P-FIX2-QA Taihao pilot, run against the same input workbook and source PDF, with a new R7T-specific output directory.

---

## R7Q baseline

```text
R7Q clean_data_row_count = 92
R7Q clean_data_csv_row_count = 92
R7Q review_queue_row_count = 66
R7Q review_queue_csv_row_count = 66
R7Q unknown_row_count = 0
R7Q market_reference_row_count = 2
R7Q decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
R7Q client_ready = false
R7Q production_ready = false
R7Q formal_client_export_allowed = false
R7Q demo_export_only = true
```

---

## R7T manifest summary

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
input_stage = AI_EXTRACTED_EXCEL_INTAKE_AUDIT_PILOT_348A
qa_fail_count = 1
source_pdf_path = input\H3_AP202605231822706325_1.pdf
source_excel_path = input\泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
output_dir = output\agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun
sheet_count = 8
row_count_total = 158
row_count_audited = 158
pass_count = 0
review_count = 157
fail_count = 1
issue_count_total = 172
strict_financial_table_row_count = 104
market_reference_row_count = 2
narrative_assertion_count = 52
normalized_testset_record_row_count = 0
testset_supporting_row_count = 0
unknown_row_count = 0
clean_data_row_count = 72
review_queue_row_count = 86
internal_clean_candidate_count = 72
internal_reference_candidate_count = 0
narrative_review_count = 51
review_required_count = 34
excluded_from_clean_data_count = 1
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
legacy_datefac_touched = false
legacy_outputs_touched = false
formal_export_generated = false
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
clean_data_csv_row_count = 72
review_queue_csv_row_count = 86
```

---

## Clean/review count comparison

```text
                          R7Q (pre-R7S)    R7T (post-R7S)    delta
clean_data_row_count      92               72                -20
clean_data_csv_row_count  92               72                -20
review_queue_row_count    66               86                +20
review_queue_csv_row_count 66              86                +20
unknown_row_count         0                0                 0
market_reference_row_count 2               2                 0
strict_financial_table_row_count 104       104               0
row_count_total           158              158               0
```

Direction matches the R7T task expectation:

```text
clean_data count decreased (92 -> 72)
review_queue count increased (66 -> 86)
unknown_row_count remained 0
market_reference_row_count remained stable (2)
readiness gates remained closed
```

Logical and physical counts remained aligned:

```text
clean_data_row_count (72) == clean_data_csv_row_count (72)
review_queue_row_count (86) == review_queue_csv_row_count (86)
```

The 20-row delta is fully accounted for by scaffolding / comparison-dimension rows that moved from clean_data to review_queue (see next section). No row disappeared and no row was mis-routed.

---

## Risky row migration check

Computed the exact set difference between R7Q clean_data and R7T clean_data (by sheet_name, row_index, metric_name). Exactly 20 rows moved out of clean_data:

```text
Pseudo-header / block-header rows (8):
  核心盈利预测与估值,11,市场数据
  行业赛道数据,13,厂商
  行业赛道数据,19,对比维度
  行业赛道数据,29,订单日期
  行业赛道数据,34,厂商
  三大财务报表与核心指标,17,项目
  三大财务报表与核心指标,28,项目
  三大财务报表与核心指标,35,指标

Comparison-dimension rows (7):
  行业赛道数据,20,热效率
  行业赛道数据,21,单机功率
  行业赛道数据,22,交付+部署周期
  行业赛道数据,23,单位建设成本
  行业赛道数据,24,大修间隔
  行业赛道数据,25,燃料灵活性
  行业赛道数据,26,氮氧化物排放

Comparison-table data rows under scaffolding headers (5):
  行业赛道数据,14,卡特彼勒
  行业赛道数据,15,康明斯
  行业赛道数据,16,MTU
  行业赛道数据,30,2025.07.15
  行业赛道数据,31,2025.11.20
```

All 20 moved rows share the deterministic signal identified in R7R: their `period_values` are entirely non-numeric strings (e.g. "型号","最大功率","排量","缸型" / "单循环48-49%，无联合循环" / "3516E","1566KW","78L","V16"). None of them carry a numeric financial fact.

Verification that all 6 R7T-required risky labels left clean_data (exact metric_name match in clean_data.csv):

```text
市场数据  -> not in clean_data (now in review_queue, REVIEW_REQUIRED)
厂商      -> not in clean_data (now in review_queue x2, REVIEW_REQUIRED)
对比维度  -> not in clean_data (now in review_queue, REVIEW_REQUIRED)
订单日期  -> not in clean_data (now in review_queue, REVIEW_REQUIRED)
项目      -> not in clean_data (now in review_queue x2, REVIEW_REQUIRED)
指标      -> not in clean_data (now in review_queue, REVIEW_REQUIRED)
```

All 6 labels now appear in `review_queue.csv` as `STRICT_FINANCIAL_TABLE_ROW` + `REVIEW_REQUIRED`.

---

## Market reference boundary check

```text
收盘价 -> in review_queue.csv (报告核心信息与投资要点,8, MARKET_REFERENCE_ROW, REVIEW_REQUIRED)
总市值 -> in review_queue.csv (报告核心信息与投资要点,9, MARKET_REFERENCE_ROW, REVIEW_REQUIRED)
```

Neither `收盘价` nor `总市值` appears in `clean_data.csv`. The R7P-FIX2 market-reference boundary remains intact after R7S. `market_reference_row_count` remained 2.

---

## Normal financial fact preservation check

Normal numeric financial fact rows remained in clean_data. Verified examples (all `STRICT_FINANCIAL_TABLE_ROW` + `INTERNAL_CLEAN_CANDIDATE` with numeric period_values):

```text
核心盈利预测与估值: 营业总收入, 归母净利润, EPS-最新摊薄, P/E
三大财务报表与核心指标: 营业总收入, 营业成本, 净利润, 归母净利润, 摊薄EPS,
  流动资产合计, 资产总计, 负债合计, 经营活动现金流, 每股净资产, ROIC, ROE-摊薄,
  资产负债率, P/E, P/B
分业务盈利预测明细: 一、应急电源, 收入占比, 收入合计, 期间费用率, 归母净利润
可比公司估值对比: 300153.SZ, 000338.SZ, 002353.SZ, 600590.SH
行业赛道数据: AMER新增算力, 总计新增算力, 累计功率需求, 市场空间, GEV, 西门子, 三菱, 合计
```

The mixed dash/numeric row `PUE系数` (period_values include "-" plus 1.49/1.48/...) remained in clean_data, confirming the guard does not block rows with at least one numeric value.

`clean_data.csv` row_type distribution: `{STRICT_FINANCIAL_TABLE_ROW}` only, 72 data rows. No forbidden row_type entered clean_data.

---

## Readiness gates

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
legacy_datefac_touched = false
legacy_outputs_touched = false
formal_export_generated = false
```

All readiness gates remained closed. Output remained demo-only and not formal-client-export ready.

---

## Output artifact policy

The R7T rerun generated a new output directory:

```text
output/agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun/
```

This directory was created only for this R7T rerun as allowed by the task. No previous output directory was modified. Output files are local generated artifacts only and are not staged or committed.

---

## Validation outputs

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
  -> COMPILE_OK

pytest tests/agent -q
  -> 86 passed in 0.72s

Taihao rerun command:
  D:\anaconda\python.exe tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7t_taihao_scaffolding_boundary_rerun"
  -> completed successfully, no guardrail failure
```

Post-report git checks (run after the report file is created):

```text
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

(See the execution report section for these outputs. Output files appear as untracked and are not staged.)

---

## Validation Questions (answers)

1. **Did the rerun complete without a new guardrail failure?** Yes. The runner completed and wrote a valid manifest. No `OutputSchemaGuardrailError` was raised.

2. **What is the new manifest decision?** `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`. This reflects review pressure under weak evidence (qa_fail_count=1), not a guardrail failure or unknown-row collapse.

3. **What are the new clean_data and review_queue logical counts?** `clean_data_row_count = 72`, `review_queue_row_count = 86`.

4. **What are the new clean_data.csv and review_queue.csv physical counts?** `clean_data_csv_row_count = 72`, `review_queue_csv_row_count = 86`.

5. **Did logical and physical counts remain aligned?** Yes. `clean_data_row_count == clean_data_csv_row_count == 72`; `review_queue_row_count == review_queue_csv_row_count == 86`.

6. **Did the risky rows identified by R7Q/R7R move out of clean_data?** Yes. All 20 scaffolding / comparison-dimension rows moved from clean_data to review_queue.

7. **Specific label check (市场数据 / 厂商 / 对比维度 / 订单日期 / 项目 / 指标)?** All 6 labels are absent from clean_data (exact metric_name match) and present in review_queue as `STRICT_FINANCIAL_TABLE_ROW` + `REVIEW_REQUIRED`.

8. **Did 收盘价 and 总市值 remain in review_queue and stay out of clean_data?** Yes. Both remain in review_queue as `MARKET_REFERENCE_ROW` + `REVIEW_REQUIRED`. Neither is in clean_data.

9. **Did any forbidden row_type enter clean_data?** No. clean_data row_type set = `{STRICT_FINANCIAL_TABLE_ROW}` only.

10. **Did normal numeric financial fact rows remain in clean_data?** Yes. 营业总收入 / 归母净利润 / EPS / P/E / ROE / 资产总计 / PUE系数 (mixed dash/numeric) and all other numeric fact rows remained as `INTERNAL_CLEAN_CANDIDATE`.

11. **Did readiness gates remain closed?** Yes. `client_ready=false`, `production_ready=false`, `formal_client_export_allowed=false`, `demo_export_only=true`.

12. **Did the output remain demo-only and not formal-client-export ready?** Yes. `formal_export_generated=false`, `demo_export_only=true`, `formal_client_export_allowed=false`.

---

## Decision

`348N_R7T_CONFIRMED_STRICT_TABLE_SCAFFOLDING_GUARD_REAL_OUTPUT_IMPACT_VALID`

The R7S scaffolding guard has a confirmed, correct real-output impact on the Taihao workbook family:

- 20 scaffolding / comparison-dimension rows moved from clean_data to review_queue;
- all 6 R7T-required risky labels (市场数据 / 厂商 / 对比维度 / 订单日期 / 项目 / 指标) left clean_data;
- normal numeric financial fact rows (including mixed dash/numeric rows like PUE系数) remained in clean_data;
- 收盘价 / 总市值 MARKET_REFERENCE_ROW boundary remained intact;
- no forbidden row_type entered clean_data;
- logical and physical counts remained aligned;
- no new guardrail failure;
- all readiness gates remained closed;
- no external calls were made.

The guard behaves exactly as designed in R7R and validated in R7S-QA.

---

## Recommended next task

```text
348N-R7U Linyang / Anjing workbook family regression check
```

Purpose:

- rerun the Linyang and Anjing workbook families under the committed R7S policy;
- confirm the scaffolding guard does not regress clean_data / review_queue counts for those families (their numeric fact rows should remain in clean_data);
- confirm no new guardrail failure and readiness gates remain closed;
- keep all readiness gates closed.

This is a separate task. This R7T task does not start it.

---

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7T_CONFIRMED_STRICT_TABLE_SCAFFOLDING_GUARD_REAL_OUTPUT_IMPACT_VALID
build_result（构建结果）= COMPILE_OK
test_result（测试结果）= tests/agent 86 passed
rerun_result（重跑结果）= completed, no guardrail failure, decision=AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count_before（R7Q clean逻辑行数）= 92
clean_data_row_count_after（R7T clean逻辑行数）= 72
review_queue_row_count_before（R7Q review逻辑行数）= 66
review_queue_row_count_after（R7T review逻辑行数）= 86
unknown_row_count_after（R7T unknown行数）= 0
market_reference_row_count_after（R7T market reference行数）= 2
risky_rows_in_clean_after（风险行是否仍在clean）= no (all 6 labels and 20 scaffolding rows moved to review_queue)
readiness_gates（就绪门）= closed (client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true)
output_committed（是否提交output）= no (output generated locally, not staged, not committed)
files_modified（修改文件数）= 1 (this R7T report only; no code/test/input/output-modification)
error_count（错误数）= 0
boundary_check（边界检查）= passed (only the allowed R7T report created; no code/test/input/previous-output/temp/data/legacy/config/guardrails/row_type_classifier/qualitative_facts/MARKET_REFERENCE_ROW/readiness-gate changes; output not committed)
recommended_next_task（推荐下一任务）= 348N-R7U Linyang / Anjing workbook family regression check
```
