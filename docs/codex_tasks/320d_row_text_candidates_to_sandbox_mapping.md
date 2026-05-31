# 320D Row-Text Candidates to Sandbox Mapping

## task_title
Map calibrated row-text metric candidates into DateFac sandbox MetricCandidate schema with risk split preview

## project
D:\_datefac

## current_context
320C4 has completed and passed the row-text smoke gate.

Latest 320C4 result:
- pushed branch: main
- commit hash: 98f7ad4
- cleaned_human_row_text_count: 24
- repaired_row_count: 6
- metric_candidate_count: 100
- duplicate_metric_year_count: 0
- numeric_count_mismatch_count: 0
- smoke_check_passed_row_count: 18
- critical_smoke_rows_passed_count: 7
- row_text_smoke_fix_decision: ROW_TEXT_READY_FOR_320D_SANDBOX_MAPPING

Interpretation:
- MinerU is already validated as primary layout/table asset parser.
- Legacy PPStructure is not reliable as a full cell-grid recognizer, but it can produce row text.
- 320C4 proved that DateFac can reconstruct high-value cash-flow rows from row text.
- The next stage is to map these calibrated row-text candidates into DateFac-style normalized candidates and produce a sandbox trusted/review_required preview.

This stage is still sandbox-only. Do not write production delivery files.

## goal
Implement 320D sandbox mapping:

320C4 metric_candidate_preview
-> normalized MetricCandidate records
-> metric/unit/year/value validation
-> duplicate/conflict checks
-> risk tags
-> sandbox trusted/review_required split preview
-> Excel/JSON/Markdown diagnostics

The output should help decide whether row-text extraction can be connected to the existing DateFac downstream governance pipeline.

## non_goals
Do not do these in 320D:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call LLM/VLM/cloud API/network.
- Do not modify production Excel files.
- Do not apply candidates into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/320d_row_text_candidates_to_sandbox_mapping.md`
- `datefac/domain/metric_candidate.py`
- `datefac/governance/__init__.py`
- `datefac/governance/row_text_candidate_mapper.py`
- `datefac/governance/risk_splitter.py`
- `tools/run_row_text_candidates_to_sandbox_mapping_320d.py`

Potentially modify existing files only if needed:
- `datefac/extraction/row_text_metric_extractor.py` for export compatibility only.
- `datefac/domain/extracted_table.py` if required for schema references.

Keep the tool modular. Do not dump all logic into one giant script, because apparently humans enjoy building future maintenance traps. Avoid that.

## input_contract
Primary input:

```powershell
D:\_datefac\output\legacy_ppstructure_row_text_320c4
```

Expected files inside may include:
- `legacy_ppstructure_row_text_320c4.xlsx`
- `legacy_ppstructure_row_text_320c4_summary.json`
- `legacy_ppstructure_row_text_320c4_report.md`
- optional JSONL files if present

The CLI should support:

```powershell
python tools/run_row_text_candidates_to_sandbox_mapping_320d.py ^
  --input-dir D:\_datefac\output\legacy_ppstructure_row_text_320c4 ^
  --output-dir D:\_datefac\output\row_text_mapping_320d
```

If input is missing, generate a clear blocked report with:
- `BLOCKED_MISSING_320C4_INPUT`
- no crash
- code still py_compile clean

## source_candidate_loading
The tool should load candidates from the 320C4 Excel first:
- sheet: `metric_candidate_preview`

If JSONL candidate files exist, they may be used as fallback or supplement.

Required source fields to preserve if available:
- source_file
- extracted_table_id
- row_index
- row_text
- repaired_row_text
- metric_code
- raw_metric_name
- year
- raw_value
- normalized_value
- raw_unit
- alignment_status
- risk_tags
- confidence
- source_row_text
- repair_trace_id

Do not silently drop unknown source columns. Preserve them in `source_meta_json` if needed.

## MetricCandidate schema
Create a dataclass or typed record with at least:

```python
class MetricCandidate:
    candidate_id: str
    source_stage: str
    source_file: str
    source_doc_name: str | None
    source_table_id: str | None
    source_row_index: int | None
    source_row_text: str
    metric_code: str
    canonical_metric_name: str
    raw_metric_name: str
    year: str
    period_type: str
    raw_value: str
    normalized_value: float | None
    unit: str | None
    unit_source: str
    currency: str | None
    confidence: float
    risk_tags: list[str]
    split_decision: str
    split_reason: str
    provenance_json: dict
```

Recommended `source_stage`:
- `mineru_ppstructure_row_text_320c4`

Recommended split decisions:
- `trusted_preview`
- `review_required_preview`
- `rejected_preview`

This is sandbox preview naming on purpose. Do not pretend this is production trust.

## metric normalization
Create or use a mapping table for canonical names.

At minimum support these codes from 320C4:
- `net_profit`
- `asset_impairment_provision`
- `depreciation_amortization`
- `fair_value_change_loss`
- `finance_expense`
- `working_capital_change`
- `other_operating_cf`
- `operating_cash_flow`
- `capex`
- `other_investing_cash_flow`
- `investing_cash_flow`
- `equity_financing`
- `debt_net_change`
- `dividend_interest_paid`
- `other_financing_cash_flow`
- `financing_cash_flow`
- `net_cash_change`
- `cash_beginning_balance`
- `cash_ending_balance`
- `free_cash_flow_firm`
- `free_cash_flow_equity`

Also keep support for core valuation/financial metrics:
- EPS / `eps`
- ROE / `roe`
- PE / `pe`
- PB / `pb`
- EV/EBITDA / `ev_ebitda`
- Revenue / `revenue`
- Gross Margin / `gross_margin`
- Revenue Growth / `revenue_growth`
- Net Profit Growth / `net_profit_growth`
- Debt Ratio / `debt_ratio`

If an unknown metric_code appears, keep it but mark:
- `UNKNOWN_METRIC_CODE`
- review_required_preview

## value normalization rules
Normalize values conservatively:
- `(967)` -> `-967`
- `（967）` -> `-967`
- `12,488` -> `12488`
- `15.2%` -> `15.2` with unit `%`
- empty / `--` / `N/A` -> None and risk tag `VALUE_MISSING`

Do not scale units unless unit is explicit.

For this known cash-flow sample:
- table title `现金流量表（百万元）` means unit should be `百万元` if detected from table title/header/source context.
- If unit cannot be detected, mark `UNIT_UNKNOWN`.

Do not guess currency unless present. If title says `百万元`, currency may remain unknown unless source context says RMB/CNY.

## year validation
Supported years:
- 2024
- 2025
- 2026E
- 2027E
- 2028E
- also allow 2024A / 2025A where present.

Rules:
- invalid year -> `INVALID_YEAR`, review_required_preview
- missing year -> `YEAR_MISSING`, review_required_preview
- inferred year from canonical sequence -> keep but tag `YEAR_INFERRED`

## duplicate and conflict checks
Check duplicate candidates by:
- source_file + source_table_id + metric_code + year

If exact duplicates have same normalized_value:
- keep one canonical row
- write duplicates to duplicate sheet
- tag `DUPLICATE_SAME_VALUE_COLLAPSED`

If duplicates disagree:
- do not trust either blindly
- tag `VALUE_CONFLICT`
- split as review_required_preview

## risk split rules
This is only sandbox preview. Keep strict.

`trusted_preview` only if all conditions hold:
- metric_code is known
- year is valid
- normalized_value is not None
- no `NUMERIC_COUNT_MISMATCH`
- no `VALUE_CONFLICT`
- no `ROW_REPAIR_AMBIGUOUS`
- no `LOW_CONFIDENCE`
- no `UNKNOWN_METRIC_CODE`
- duplicate_metric_year_count for this metric/year is zero after collapse
- confidence >= 0.80 if confidence is available

For repaired rows:
- If risk tag includes `ROW_REPAIRED_CONTINUATION` or equivalent, default to review_required_preview unless confidence >= 0.90 and row appears in smoke-check passed rows.

`review_required_preview` if:
- repaired row but not smoke-proven
- unit unknown for metrics where unit matters
- value is negative where unexpected for balance rows
- generic `其它` metrics
- low/medium confidence
- any warning/risk tag not explicitly safe

`rejected_preview` if:
- bbox/html/noise-derived candidate leaked
- invalid year cannot be repaired
- normalized_value is None and raw value is not meaningful

## expected output
Write to:

```powershell
D:\_datefac\output\row_text_mapping_320d
```

Required files:

1. `row_text_mapping_320d.xlsx`
   Sheets:
   - `summary`
   - `normalized_candidates`
   - `trusted_preview`
   - `review_required_preview`
   - `rejected_preview`
   - `duplicates`
   - `conflicts`
   - `risk_tag_counts`
   - `metric_counts`
   - `source_candidate_rows`
   - `mapping_audit`

2. `row_text_mapping_320d_summary.json`

3. `row_text_mapping_320d_report.md`

Optional:
- `normalized_candidates.jsonl`
- `trusted_preview.jsonl`
- `review_required_preview.jsonl`

## summary metrics
Include:
- source_candidate_count
- normalized_candidate_count
- trusted_preview_count
- review_required_preview_count
- rejected_preview_count
- duplicate_same_value_count
- conflict_count
- unknown_metric_code_count
- invalid_year_count
- value_missing_count
- unit_unknown_count
- risk_tag_counts
- sandbox_mapping_decision

Decision rule:
- If any bbox/html/noise candidate reaches normalized candidates:
  `MAPPING_FAILED_NOISE_LEAK`
- If conflict_count > 0:
  `MAPPING_READY_WITH_REVIEW_REQUIRED_CONFLICTS`
- If normalized_candidate_count >= 50 and trusted_preview_count >= 30 and rejected_preview_count == 0:
  `ROW_TEXT_MAPPING_READY_FOR_320E_SANDBOX_INTEGRATION`
- If normalized_candidate_count >= 20 and review_required_preview_count > 0:
  `ROW_TEXT_MAPPING_USABLE_NEEDS_REVIEW_GATE`
- Otherwise:
  `ROW_TEXT_MAPPING_NOT_READY`

## safety constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
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
python -m py_compile datefac/domain/metric_candidate.py
python -m py_compile datefac/governance/row_text_candidate_mapper.py
python -m py_compile datefac/governance/risk_splitter.py
python -m py_compile tools/run_row_text_candidates_to_sandbox_mapping_320d.py
```

Then run:

```powershell
python tools/run_row_text_candidates_to_sandbox_mapping_320d.py ^
  --input-dir D:\_datefac\output\legacy_ppstructure_row_text_320c4 ^
  --output-dir D:\_datefac\output\row_text_mapping_320d
```

If the input dir is missing, produce a clear blocked report and keep the code compile-clean.

## commit requirements
After implementation:
1. `git status`
2. only add 320D code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Map row text candidates to sandbox metrics`
7. push to remote `main`.

## final response requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- source_candidate_count
- normalized_candidate_count
- trusted_preview_count
- review_required_preview_count
- rejected_preview_count
- duplicate_same_value_count
- conflict_count
- unknown_metric_code_count
- unit_unknown_count
- sandbox_mapping_decision
- top risk tags
- skipped/untracked files
