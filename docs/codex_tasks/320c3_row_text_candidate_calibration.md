# 320C3 Row-Text Candidate Calibration

## task_title
Fix false-positive row-text metric extraction and calibrate cash-flow row reconstruction

## project
D:\_datefac

## current_context
320C2 implemented legacy PPStructure row-text ingestion and a deterministic row-text metric extractor.

320C2 reported:
- source_result_file_count: 2
- extracted_table_count: 2
- recognized_row_text_count: 2
- metric_candidate_count: 22
- numeric_count_mismatch_count: 3
- row_text_probe_decision: ROW_TEXT_RECOGNITION_READY_FOR_320D_CANDIDATE_MAPPING

Manual review showed this decision is a false positive.

Observed problems in the 320C2 output:
1. `res_0.txt` raw metadata was treated as row text.
   - Candidate rows were generated from bbox coordinates such as `1.0057191848754883`, `615.0139770507812`, etc.
   - This must be forbidden.
2. HTML strings were treated as normal row text.
   - Candidate rows were generated from HTML text where year fragments were parsed incorrectly.
   - HTML must be converted to clean text rows or skipped if not safely parseable.
3. Numeric token regex split four-digit values incorrectly.
   - Example: `1974` became `197` and `4`.
   - This is unacceptable for financial statements.
4. PPStructure XLSX output often splits one real financial row into multiple row-text fragments.
   - Example target image row:
     `净利润 1974 2371 3307 3885 4526`
   - Current row-text fragments included:
     `净利润 1974 2371 3307`
     `3885 4526 0 0 0 0`
   - The extractor must support conservative continuation-row repair.
5. Some rows have values before a metric label due OCR/Excel layout disorder.
   - Example fragments:
     `营运资本变动 353`
     `511 528 361 327 其它`
     `14 38 53 62 72 经营活动现金流`
     `3537 4102 4924 5537 6207`
   - The row repair stage should handle label-before-values and values-before-label cases conservatively.
6. Many valid cash-flow rows were placed in `unmatched_rows`, even though they are important and parseable.

Therefore, do not proceed to 320D yet. 320C3 must calibrate row-text extraction first.

## goal
Implement a safer and more accurate row-text candidate extraction calibration.

The task should:
1. filter out non-human row text such as bbox dictionaries and raw HTML;
2. clean/extract HTML only when safe;
3. fix numeric tokenization;
4. add a row-fragment repair pass for PPStructure XLSX row text;
5. improve cash-flow metric matching;
6. generate calibrated candidate preview and quality diagnostics;
7. update decision logic so false positives cannot pass.

Still sandbox-only. Do not touch production delivery files.

## expected_new_or_modified_files
Suggested modifications:
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/recognition/legacy_ppstructure_result_reader.py`
- `tools/run_legacy_ppstructure_row_text_probe_320c2.py` if necessary to enable calibrated mode/output naming

Suggested new files if cleaner:
- `datefac/extraction/row_text_cleaner.py`
- `datefac/extraction/row_text_repair.py`
- `docs/codex_tasks/320c3_row_text_candidate_calibration.md`

Do not delete existing 320C2 outputs or old logic unless replacing it safely.

## input
Use existing local 320C2 result directory:

```powershell
D:\_datefac\output\legacy_ppstructure_row_text_320c2
```

Use existing PPStructure result directory if needed:

```powershell
E:\mineru_lab\ppstructure_legacy_test
```

The tool must also support rerunning from:

```powershell
python tools/run_legacy_ppstructure_row_text_probe_320c2.py ^
  --ppstructure-result-dir E:\mineru_lab\ppstructure_legacy_test ^
  --output-dir D:\_datefac\output\legacy_ppstructure_row_text_320c3
```

## hard_sample_expected_values
For the uploaded/known cash-flow table image, the calibrated extractor should be able to recover these rows at least from row text if present:

Header years:
- 2024, 2025, 2026E, 2027E, 2028E

Expected row examples:
- 净利润: 1974, 2371, 3307, 3885, 4526
- 资产减值准备: 0, 0, 0, 0, 0
- 折旧摊销: 1083, 1299, 1204, 1238, 1282
- 公允价值变动损失: (45), (135), 0, 0, 0
- 财务费用: 36, 172, (10), (57), (140)
- 营运资本变动: 511, 528, 361, 353, 327
- 其它: 14, 38, 53, 62, 72
- 经营活动现金流: 3537, 4102, 4924, 5537, 6207
- 投资活动现金流: 258, (2705), (1300), (2423), (1947)
- 融资活动现金流: (967), (2910), 516, (1088), 50
- 现金净变动: 2828, (1514), 4141, 2026, 4309
- 企业自由现金流: 0, 3568, 3737, 4312, 4915
- 权益自由现金流: 0, 2486, 4261, 3269, 5077

These expected values are only a smoke-test target for this known sample. They must not be hardcoded as final output. Use them for validation assertions or diagnostics.

## cleaning_rules
Before metric extraction, classify each row_text as one of:
- HUMAN_ROW_TEXT
- RAW_BBOX_METADATA
- RAW_HTML
- EMPTY_OR_NOISE

Rules:
- Rows starting with `{` and containing `cell_bbox` must not be used for metric extraction.
- Rows containing long bbox float sequences must not be used.
- Rows starting with `<html`, `<table`, `<tbody`, `<tr`, `<td` must not be used directly.
- HTML may be converted to clean row text only if tags can be removed safely and resulting text is not polluted by markup.
- Very long rows dominated by bbox floats should be skipped.

Add warning/tag types:
- SKIPPED_RAW_BBOX_METADATA
- SKIPPED_RAW_HTML
- SKIPPED_NOISE_ROW
- HTML_CLEANED_TO_TEXT

## numeric_tokenization_rules
Fix number parsing.

Requirements:
- `1974` must parse as one token, not `197` and `4`.
- `12,488` must parse as `12488`.
- `(967)` must parse as `-967`.
- `（967）` must parse as `-967`.
- `(57)` -> `-57`.
- `(1100)` -> `-1100`.
- `15.2%` must remain one percentage token.
- Avoid matching bbox-like long floats when row is metadata.

Recommended regex direction:
- Allow grouped comma numbers OR normal integers of any length OR decimals.
- Use boundary guards to avoid splitting inside words.

## row_repair_rules
Implement a conservative row-fragment repair pass before metric extraction.

Definitions:
- `expected_year_count` is usually 5 for 2024-2028E.
- A financial row is complete when it has one clear metric label and exactly expected_year_count numeric tokens.

Repair patterns to support:

### Pattern 1: metric label + partial values, followed by numeric continuation row
Example:
- row A: `净利润 1974 2371 3307`
- row B: `3885 4526 0 0 0 0`
Repair:
- Use only the first needed numeric tokens from row B to complete row A.
- Result: `净利润 1974 2371 3307 3885 4526`
- Keep unused trailing tokens as a separate unmatched/noise row unless they can form another valid row.

### Pattern 2: metric label + one value, followed by values before next metric label
Example:
- row A: `营运资本变动 353`
- row B: `511 528 361 327 其它`
Repair:
- Complete row A with leading numeric tokens from row B.
- Then create a pending label `其它` with no values.

### Pattern 3: values before metric label, next row starts values
Example:
- row B: `14 38 53 62 72 经营活动现金流`
- row C: `3537 4102 4924 5537 6207`
Repair:
- The leading values belong to previous pending label `其它` if any.
- `经营活动现金流` becomes next pending label.
- The next numeric-only row completes `经营活动现金流`.

### Pattern 4: normal row
Example:
- `融资活动现金流 (967) (2910) 516 (1088) 50`
Repair:
- Keep as is and parse directly.

Do not over-repair ambiguous rows. Mark risk tags:
- ROW_REPAIRED_CONTINUATION
- ROW_REPAIRED_VALUES_BEFORE_LABEL
- ROW_REPAIR_AMBIGUOUS

## metric_matching_rules
Improve cash-flow row matching.

Add or confirm metric codes:
- net_profit: 净利润
- asset_impairment_provision: 资产减值准备
- depreciation_amortization: 折旧摊销
- fair_value_change_loss: 公允价值变动损失
- finance_expense: 财务费用
- working_capital_change: 营运资本变动
- other_operating_cf: 其它 / 其他, only inside cash-flow context
- operating_cash_flow: 经营活动现金流
- capex: 资本开支
- other_investing_cash_flow: 其它投资现金流
- investing_cash_flow: 投资活动现金流
- equity_financing: 权益性融资
- debt_net_change: 负债净变化
- dividend_interest_paid: 支付股利、利息
- other_financing_cash_flow: 其它融资现金流
- financing_cash_flow: 融资活动现金流
- net_cash_change: 现金净变动
- cash_beginning_balance: 货币资金的期初余额
- cash_ending_balance: 货币资金的期末余额
- free_cash_flow_firm: 企业自由现金流
- free_cash_flow_equity: 权益自由现金流

Keep previous core metrics too:
EPS, ROE, PE, PB, EV/EBITDA, revenue, net_profit, gross_margin, revenue_growth, net_profit_growth, debt_ratio.

Context matters:
- If table title/header contains `现金流量表`, allow cash-flow-specific row names.
- Generic `其它` should not be extracted unless a cash-flow context or pending row repair context exists.

## output_contract
Write to a new sandbox output dir:

```powershell
D:\_datefac\output\legacy_ppstructure_row_text_320c3
```

Files:
1. `legacy_ppstructure_row_text_320c3.xlsx`
   Sheets:
   - summary
   - cleaned_row_texts
   - repaired_rows
   - metric_candidate_preview
   - expected_value_smoke_check
   - parse_warnings
   - rejected_noise_rows
   - unmatched_rows
   - source_files

2. `legacy_ppstructure_row_text_320c3_summary.json`

3. `legacy_ppstructure_row_text_320c3_report.md`

Optional:
- `cleaned_row_texts.jsonl`
- `repaired_rows.jsonl`
- `metric_candidate_preview.jsonl`

## summary_metrics
Include:
- source_result_file_count
- raw_row_text_count
- cleaned_human_row_text_count
- skipped_raw_bbox_count
- skipped_raw_html_count
- repaired_row_count
- metric_candidate_count
- high_confidence_candidate_count
- medium_confidence_candidate_count
- low_confidence_candidate_count
- numeric_count_mismatch_count
- smoke_check_expected_row_count
- smoke_check_passed_row_count
- smoke_check_failed_row_count
- row_text_calibration_decision

Decision rule:
- If bbox/html candidates are generated, decision must be `ROW_TEXT_CALIBRATION_FAILED_NOISE_LEAK`.
- If numeric tokenization still splits `1974` into `197` and `4`, decision must be `ROW_TEXT_CALIBRATION_FAILED_NUMERIC_TOKENIZER`.
- If smoke_check_passed_row_count >= 8 and numeric_count_mismatch_count <= 3:
  `ROW_TEXT_CALIBRATION_READY_FOR_320D`
- If repaired rows exist but smoke check is weak:
  `ROW_TEXT_REPAIR_NEEDS_MORE_CALIBRATION`
- Otherwise:
  `ROW_TEXT_CALIBRATION_NOT_READY`

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure in Codex unless explicitly requested later. Read existing result files first.
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
python -m py_compile datefac/extraction/row_text_metric_extractor.py
```

If new files are added:

```powershell
python -m py_compile datefac/extraction/row_text_cleaner.py
python -m py_compile datefac/extraction/row_text_repair.py
```

Then run:

```powershell
python tools/run_legacy_ppstructure_row_text_probe_320c2.py ^
  --ppstructure-result-dir E:\mineru_lab\ppstructure_legacy_test ^
  --output-dir D:\_datefac\output\legacy_ppstructure_row_text_320c3
```

If a separate 320C3 tool is created, run it instead with the same input/output directories.

## commit_requirements
After implementation:
1. `git status`
2. only add 320C3 code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Calibrate row text metric extraction`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- cleaned_human_row_text_count
- skipped_raw_bbox_count
- skipped_raw_html_count
- repaired_row_count
- metric_candidate_count
- numeric_count_mismatch_count
- smoke_check_passed_row_count
- row_text_calibration_decision
- top warning types
- skipped/untracked files
