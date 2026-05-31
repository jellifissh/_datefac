# 320C4 Cashflow Row-Text Smoke Fix

## task_title
Diagnose 320C3 smoke-check failures and harden cash-flow row-text reconstruction

## project
D:\_datefac

## current_context
320C3 calibrated the legacy PPStructure row-text extraction pipeline.

Latest 320C3 reported:
- pushed branch: main
- commit hash: 8fa21a8
- changed files:
  - `datefac/extraction/row_text_cleaner.py`
  - `datefac/extraction/row_text_repair.py`
  - `datefac/extraction/row_text_metric_extractor.py`
  - `tools/run_legacy_ppstructure_row_text_probe_320c2.py`
- cleaned_human_row_text_count: 24
- skipped_raw_bbox_count: 1
- skipped_raw_html_count: 0
- repaired_row_count: 5
- metric_candidate_count: 85
- numeric_count_mismatch_count: 2
- smoke_check_passed_row_count: 4
- row_text_calibration_decision: ROW_TEXT_REPAIR_NEEDS_MORE_CALIBRATION
- top warning types:
  - ROW_REPAIR_AMBIGUOUS: 5
  - SKIPPED_RAW_BBOX_METADATA: 1
  - HTML_CLEANED_TO_TEXT: 1

Engineering interpretation:
320C3 improved cleaning and candidate generation, but it is not ready for 320D. The candidate count is high, but the known cash-flow table smoke check only passed 4 rows. This means either:
1. row repair is still reconstructing several rows incorrectly;
2. candidate values are correct but smoke-check alias/value comparison is too strict;
3. duplicate or shifted candidates exist;
4. row fragments around `其它`, `经营活动现金流`, and continuation numeric rows are still being mishandled.

Do not proceed to 320D until the known cash-flow table smoke check is strong enough.

## goal
Implement a focused 320C4 diagnostic and fix pass.

Primary goal:
- Make the known cash-flow table smoke check explainable and stronger.

This task should not simply increase candidate count. It should produce a clear expected-vs-actual matrix for the known cash-flow sample and fix the row repair/candidate alignment based on that matrix.

## expected_new_or_modified_files
Likely modified:
- `datefac/extraction/row_text_repair.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `tools/run_legacy_ppstructure_row_text_probe_320c2.py`

Optional new files:
- `datefac/extraction/cashflow_smoke_check.py`
- `datefac/extraction/candidate_matrix.py`
- `docs/codex_tasks/320c4_cashflow_row_text_smoke_fix.md`

Do not delete 320C2/320C3 behavior. Improve it with diagnostics and safer calibration.

## input
Use existing PPStructure result directory:

```powershell
E:\mineru_lab\ppstructure_legacy_test
```

Use sandbox output:

```powershell
D:\_datefac\output\legacy_ppstructure_row_text_320c4
```

Run command:

```powershell
python tools/run_legacy_ppstructure_row_text_probe_320c2.py ^
  --ppstructure-result-dir E:\mineru_lab\ppstructure_legacy_test ^
  --output-dir D:\_datefac\output\legacy_ppstructure_row_text_320c4
```

If a separate 320C4 CLI is created, use that instead, but keep backward compatibility with the 320C2 tool if practical.

## hard_sample_expected_values
Known table: `现金流量表（百万元）`
Years:
- 2024
- 2025
- 2026E
- 2027E
- 2028E

Expected rows:
- `net_profit`: 净利润 = 1974, 2371, 3307, 3885, 4526
- `asset_impairment_provision`: 资产减值准备 = 0, 0, 0, 0, 0
- `depreciation_amortization`: 折旧摊销 = 1083, 1299, 1204, 1238, 1282
- `fair_value_change_loss`: 公允价值变动损失 = -45, -135, 0, 0, 0
- `finance_expense`: 财务费用 = 36, 172, -10, -57, -140
- `working_capital_change`: 营运资本变动 = 511, 528, 361, 353, 327
- `other_operating_cf`: 其它 = 14, 38, 53, 62, 72
- `operating_cash_flow`: 经营活动现金流 = 3537, 4102, 4924, 5537, 6207
- `capex`: 资本开支 = 0, -869, -1100, -1100, -1100
- `other_investing_cash_flow`: 其它投资现金流 = 1073, -2449, 0, -1123, -647
- `investing_cash_flow`: 投资活动现金流 = 258, -2705, -1300, -2423, -1947
- `equity_financing`: 权益性融资 = 0, 0, 0, 0, 0
- `debt_net_change`: 负债净变化 = 2784, -1966, 50, 50, 50
- `dividend_interest_paid`: 支付股利、利息 = 0, 0, 0, 0, 0
- `other_financing_cash_flow`: 其它融资现金流 = -6534, 1022, 466, -1138, 0
- `financing_cash_flow`: 融资活动现金流 = -967, -2910, 516, -1088, 50
- `net_cash_change`: 现金净变动 = 2828, -1514, 4141, 2026, 4309
- `cash_beginning_balance`: 货币资金的期初余额 = 5192, 8020, 6506, 10647, 12673
- `cash_ending_balance`: 货币资金的期末余额 = 8020, 6506, 10647, 12673, 16982
- `free_cash_flow_firm`: 企业自由现金流 = 0, 3568, 3737, 4312, 4915
- `free_cash_flow_equity`: 权益自由现金流 = 0, 2486, 4261, 3269, 5077

Do not hardcode these as production extraction output. Use them only as sample smoke-check targets and diagnostics.

## diagnostics_required
Add a strong diagnostic sheet/file that explains every expected row.

Required sheet:
- `expected_vs_actual_matrix`

Columns:
- expected_metric_code
- expected_metric_name
- expected_values_2024
- expected_values_2025
- expected_values_2026E
- expected_values_2027E
- expected_values_2028E
- actual_values_2024
- actual_values_2025
- actual_values_2026E
- actual_values_2027E
- actual_values_2028E
- matched_candidate_row_ids
- matched_source_row_texts
- pass_fail
- failure_reason

Failure reasons should be explicit:
- MISSING_METRIC_ROW
- VALUE_MISMATCH
- YEAR_SHIFTED
- DUPLICATE_CANDIDATES
- ALIAS_NOT_MATCHED
- ROW_REPAIR_FAILED
- SMOKE_CHECK_MAPPING_BUG

Also add:
- `candidate_matrix` sheet: pivot metric_code x year -> value/source row.
- `duplicate_candidates` sheet if duplicate metric/year candidates exist.
- `row_repair_trace` sheet that shows original fragments -> repaired row.

## row_repair_focus
Improve reconstruction around these known difficult fragment patterns:

### Fragment group A
Likely issue:
- `净利润 1974 2371 3307`
- `3885 4526 0 0 0 0`
Expected:
- `净利润 1974 2371 3307 3885 4526`
- remaining zeros can start `资产减值准备` only if label context confirms; otherwise do not invent labels.

### Fragment group B
Likely issue:
- `营运资本变动 353`
- `511 528 361 327 其它`
- `14 38 53 62 72 经营活动现金流`
- `3537 4102 4924 5537 6207`
Expected:
- `营运资本变动 511 528 361 353 327`
- `其它 14 38 53 62 72`
- `经营活动现金流 3537 4102 4924 5537 6207`

This requires handling cases where OCR places one value of a row before earlier values or where label appears at the end of previous numeric row. Apply conservative rules only in cash-flow context.

### Fragment group C
Normal rows must stay stable:
- `融资活动现金流 (967) (2910) 516 (1088) 50`
- `现金净变动 2828 (1514) 4141 2026 4309`

Do not over-repair rows that already have one clear label and 5 values.

## candidate_quality_rules
Add quality checks before declaring readiness:

1. No bbox/html-derived candidates.
2. No metric/year duplicate unless explicitly marked and resolved.
3. Each high-confidence cash-flow row must have exactly 5 year values.
4. Parentheses negatives must normalize correctly.
5. Numeric tokenization must not split 1974 into 197/4.
6. Candidate matrix should pass at least 14 of the 21 expected rows before moving to 320D.
7. Critical rows must pass:
   - net_profit
   - operating_cash_flow
   - investing_cash_flow
   - financing_cash_flow
   - net_cash_change
   - free_cash_flow_firm
   - free_cash_flow_equity

## output_contract
Write to:

```powershell
D:\_datefac\output\legacy_ppstructure_row_text_320c4
```

Files:
1. `legacy_ppstructure_row_text_320c4.xlsx`
   Required sheets:
   - summary
   - cleaned_row_texts
   - repaired_rows
   - row_repair_trace
   - metric_candidate_preview
   - candidate_matrix
   - expected_vs_actual_matrix
   - duplicate_candidates
   - parse_warnings
   - rejected_noise_rows
   - unmatched_rows
   - source_files

2. `legacy_ppstructure_row_text_320c4_summary.json`

3. `legacy_ppstructure_row_text_320c4_report.md`

Optional:
- `candidate_matrix.json`
- `row_repair_trace.jsonl`

## summary_metrics
Include:
- cleaned_human_row_text_count
- skipped_raw_bbox_count
- skipped_raw_html_count
- repaired_row_count
- metric_candidate_count
- duplicate_metric_year_count
- numeric_count_mismatch_count
- smoke_check_expected_row_count
- smoke_check_passed_row_count
- smoke_check_failed_row_count
- critical_smoke_rows_passed_count
- row_text_smoke_fix_decision

Decision rule:
- If bbox/html candidates are generated:
  `ROW_TEXT_SMOKE_FIX_FAILED_NOISE_LEAK`
- If `1974` is split into `197` and `4`:
  `ROW_TEXT_SMOKE_FIX_FAILED_NUMERIC_TOKENIZER`
- If duplicate_metric_year_count > 0 for critical rows:
  `ROW_TEXT_SMOKE_FIX_FAILED_DUPLICATES`
- If smoke_check_passed_row_count >= 14 and all critical rows pass:
  `ROW_TEXT_READY_FOR_320D_SANDBOX_MAPPING`
- If smoke_check_passed_row_count improves over 320C3 but remains below 14:
  `ROW_TEXT_REPAIR_IMPROVED_BUT_NEEDS_MORE_CALIBRATION`
- Otherwise:
  `ROW_TEXT_SMOKE_FIX_NOT_READY`

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure in Codex. Read existing result files first.
3. Do not call cloud APIs, LLMs, VLMs, or network endpoints.
4. Do not modify production delivery files:
   - `01_自动可信核心指标.xlsx`
   - `02_人工复核指标队列.xlsx`
   - `02A_人工年份修正覆盖表.xlsx`
   - `05_核心财务指标标准化.xlsx`
   - `06_最终核心财务指标.xlsx`
5. Do not modify:
   - `data/overrides/02B_ai_repair_override.xlsx`
   - `data/mapping/formal_scope_rules.json`
6. Do not run `factory_core.py`.
7. Do not rewrite old Stage7 pipeline.
8. Do not commit `output/` artifacts.
9. Do not commit anything under `E:\mineru_lab`.
10. Preserve Chinese text as UTF-8. No `????` or replacement characters.

## validation
Run:

```powershell
python -m py_compile datefac/extraction/row_text_repair.py
python -m py_compile datefac/extraction/row_text_metric_extractor.py
```

If new files are added:

```powershell
python -m py_compile datefac/extraction/cashflow_smoke_check.py
python -m py_compile datefac/extraction/candidate_matrix.py
```

Then run:

```powershell
python tools/run_legacy_ppstructure_row_text_probe_320c2.py ^
  --ppstructure-result-dir E:\mineru_lab\ppstructure_legacy_test ^
  --output-dir D:\_datefac\output\legacy_ppstructure_row_text_320c4
```

If a separate 320C4 tool is created, run it instead with equivalent arguments.

## commit_requirements
After implementation:
1. `git status`
2. only add 320C4 code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Harden cashflow row text smoke check`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- cleaned_human_row_text_count
- repaired_row_count
- metric_candidate_count
- duplicate_metric_year_count
- numeric_count_mismatch_count
- smoke_check_passed_row_count
- critical_smoke_rows_passed_count
- row_text_smoke_fix_decision
- top warning types
- skipped/untracked files
