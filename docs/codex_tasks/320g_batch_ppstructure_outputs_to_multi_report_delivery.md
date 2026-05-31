# 320G Batch PPStructure Outputs to Multi-Report Delivery

## task_title
Import 320F batch PPStructure outputs and run row-text extraction/mapping/delivery benchmark across multiple tables

## project
D:\_datefac

## current_context
After 320F, the user manually ran legacy PPStructure on a curated 10-table worklist.

Manual batch output summary:
- batch summary file: `E:\mineru_lab\ppstructure_batch_outputs_320f\batch_summary.json`
- total selected tables: 10
- OK: 10
- FAILED: 0
- IMAGE_MISSING: 0

Selected table mix:
- 4 key financial / valuation tables
- 1 income statement
- 3 cash flow statements
- 2 balance sheets

Known output root:

```powershell
E:\mineru_lab\ppstructure_batch_outputs_320f
```

Each subdirectory should contain:
- `table_meta.json`
- `success.json`
- `res_*.txt`
- `*.xlsx`
- possibly generated folders/files from `save_structure_res`

Previous stages:
- 320A/320B/320B2 validated MinerU as primary layout/table asset parser.
- 320C4 fixed row-text reconstruction and smoke check for one cash-flow sample.
- 320D2 mapped context-enriched row-text candidates into trusted/review split.
- 320E created one sandbox delivery bundle.
- 320F proved only one report/table was benchmarked and generated a worklist.

Now 320G must consume the 10 newly generated PPStructure outputs and test whether the row-text pipeline generalizes beyond one table.

## goal
Implement 320G batch integration:

PPStructure batch outputs
-> per-table row-text extraction
-> per-table candidate extraction
-> per-table mapping/trust split
-> combined multi-table delivery bundle
-> multi-report benchmark summary

This is still sandbox-only. Do not modify production files.

The goal is to answer:
- How many of the 10 PPStructure outputs can be parsed into useful row text?
- How many generate metric candidates?
- Which table types work best/fail worst?
- What trusted/review split emerges across multiple tables?
- Is the row-text route ready for a broader 320H pipeline integration plan, or does it need more table-type calibration?

## non_goals
Do not do these in 320G:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call LLM/VLM/cloud API/network.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/320g_batch_ppstructure_outputs_to_multi_report_delivery.md`
- `datefac/pipeline/__init__.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `tools/run_batch_ppstructure_outputs_320g.py`

Potentially modify existing modules only if needed:
- `datefac/recognition/legacy_ppstructure_result_reader.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/extraction/row_text_repair.py`
- `datefac/governance/row_text_candidate_mapper.py`
- `datefac/delivery/sandbox_bundle_builder.py`

Keep orchestration separate from extraction/governance/delivery logic.

## input_contract
Primary input:

```powershell
E:\mineru_lab\ppstructure_batch_outputs_320f
```

Expected structure:

```text
E:\mineru_lab\ppstructure_batch_outputs_320f
├── batch_summary.json
├── p06_...\
│   ├── table_meta.json
│   ├── success.json
│   ├── res_*.txt
│   └── *.xlsx
├── p12_...\
│   └── ...
└── ...
```

CLI:

```powershell
python tools/run_batch_ppstructure_outputs_320g.py ^
  --ppstructure-batch-dir E:\mineru_lab\ppstructure_batch_outputs_320f ^
  --output-dir D:\_datefac\output\batch_row_text_delivery_320g
```

If input dir is missing, generate blocked report:
- `BLOCKED_MISSING_PPSTRUCTURE_BATCH_DIR`

If batch summary is missing, scan subdirectories recursively and continue with warning:
- `WARN_BATCH_SUMMARY_MISSING_SCAN_SUBDIRS`

Do not crash.

## processing_requirements
For each OK table output directory:

1. Load metadata:
   - `table_meta.json`
   - `success.json`
   - derive report/table ids from folder name if metadata missing.

2. Parse PPStructure outputs:
   - reuse `legacy_ppstructure_result_reader.py` where possible;
   - read `res_*.txt` and `*.xlsx`;
   - produce extracted tables and row_texts;
   - classify noise/bbox/html rows safely.

3. Run row-text extraction:
   - reuse row cleaner/repair/extractor logic from 320C4;
   - support cash-flow, valuation/key financial, income statement, and balance sheet rows;
   - do not hardcode only the original cash-flow sample.

4. Map candidates:
   - reuse 320D2 mapping/context/trust logic where possible;
   - propagate table_meta fields into provenance;
   - apply table_type-based context:
     - `cash_flow_statement` monetary rows usually use table-title unit if available;
     - `income_statement` monetary rows similarly need unit context if title/header indicates unit;
     - `balance_sheet` monetary rows need unit context if title/header indicates unit;
     - `key_financial_valuation` may contain mixed units: EPS, PE/PB, ROE, revenue, net profit. Be conservative.

5. Build combined delivery:
   - use existing delivery schema style from 320E;
   - create both per-table and combined sheets.

## table_type_context_rules
Use metadata `table_type` if present from `table_meta.json`:
- `financial_summary_valuation`
- `key_financial_valuation`
- `income_statement`
- `cash_flow_statement`
- `balance_sheet`

Rules:
- `cash_flow_statement`: allow cash-flow-specific metric codes and row repair.
- `income_statement`: prioritize revenue/net profit/profit/loss related rows; avoid wrongly mapping cash-flow row names.
- `balance_sheet`: prioritize assets/liabilities/equity/cash/debt rows; do not treat all generic numbers as cash-flow.
- `key_financial_valuation`: prioritize EPS/ROE/PE/PB/EV_EBITDA/revenue/net profit/growth/margin.

If table type is unknown, keep conservative and send more to review.

## outputs
Write to:

```powershell
D:\_datefac\output\batch_row_text_delivery_320g
```

Required files:

1. `batch_row_text_delivery_320g.xlsx`

Required sheets:
- `summary`
- `table_run_inventory`
- `extracted_row_texts_all`
- `metric_candidates_all`
- `normalized_candidates_all`
- `trusted_preview_all`
- `review_required_preview_all`
- `rejected_preview_all`
- `per_table_summary`
- `per_report_summary`
- `metric_coverage`
- `table_type_performance`
- `risk_tag_counts`
- `provenance_coverage`
- `qa_checks`
- `known_limitations`

2. `batch_row_text_delivery_320g_summary.json`

3. `batch_row_text_delivery_320g_report.md`

Optional:
- `metric_candidates_all.jsonl`
- `normalized_candidates_all.jsonl`
- `trusted_preview_all.jsonl`
- `review_required_preview_all.jsonl`
- `table_run_inventory.jsonl`

## table_run_inventory columns
- table_run_id
- priority
- report
- table_asset_id
- table_type
- image_path
- ppstructure_output_dir
- status_from_batch
- parse_status
- extracted_table_count
- row_text_count
- metric_candidate_count
- normalized_candidate_count
- trusted_count
- review_required_count
- rejected_count
- warnings

## per_table_summary columns
- table_run_id
- report
- table_asset_id
- table_type
- metric_candidate_count
- normalized_candidate_count
- trusted_count
- review_required_count
- rejected_count
- unique_metric_count
- unique_year_count
- unit_unknown_count
- year_inferred_count
- conflict_count
- qa_status
- table_decision

Suggested table decisions:
- `TABLE_DELIVERY_READY`
- `TABLE_USABLE_NEEDS_REVIEW`
- `TABLE_ROW_TEXT_PARSED_NO_CANDIDATES`
- `TABLE_PARSE_FAILED`
- `TABLE_BLOCKED_MISSING_OUTPUT`

## per_report_summary columns
- report
- table_count_processed
- table_count_ready
- trusted_count
- review_required_count
- rejected_count
- unique_metric_count
- unique_table_type_count
- report_decision

Suggested report decisions:
- `REPORT_HAS_DELIVERABLE_TABLES`
- `REPORT_NEEDS_MORE_TABLES`
- `REPORT_NO_USEFUL_ROW_TEXT`

## metric_coverage
Compute by metric family and metric code:
- table_type
- metric_family
- metric_code
- candidate_count
- trusted_count
- review_required_count
- unique_report_count
- unique_table_count
- years_covered

Families:
- profitability
- valuation
- balance_sheet
- cash_flow
- growth
- margin
- other

## qa_checks
Global QA checks:
- all OK batch dirs parsed or warned;
- no bbox/html/noise candidates in normalized output;
- no invalid year in trusted output;
- no unknown metric code in trusted output;
- no duplicate conflict in trusted output;
- provenance complete for trusted output;
- output counts match source tables;
- each table has table_meta or explicit warning;
- Chinese text preserved.

Each check:
- check_name
- status: PASS/WARN/FAIL
- detail

## summary_metrics
Include:
- batch_table_count
- batch_ok_count
- parsed_table_count
- table_with_row_text_count
- table_with_candidates_count
- table_with_trusted_count
- report_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- review_required_rate
- rejected_rate
- unique_metric_count
- unique_year_count
- unique_report_count
- unit_unknown_count
- year_inferred_count
- conflict_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- batch_delivery_decision

Decision rule:
- If qa_fail_count > 0:
  `BATCH_DELIVERY_BLOCKED_BY_QA_FAILURE`
- If parsed_table_count >= 8, table_with_trusted_count >= 5, trusted_rate >= 0.50, provenance_complete_rate >= 0.95, and qa_fail_count == 0:
  `BATCH_ROW_TEXT_DELIVERY_READY_FOR_320H_PIPELINE_PLAN`
- If parsed_table_count >= 5 and table_with_candidates_count >= 3 and qa_fail_count == 0:
  `BATCH_ROW_TEXT_DELIVERY_PARTIAL_NEEDS_CALIBRATION`
- If parsed_table_count > 0:
  `BATCH_ROW_TEXT_DELIVERY_WEAK_NEEDS_MORE_RECOGNITION_OR_RULES`
- Otherwise:
  `BATCH_ROW_TEXT_DELIVERY_NOT_READY`

## important_quality_constraint
Do not let candidate count alone drive success. A table with 200 noisy candidates and no trusted rows is not success. This should be obvious, but software metrics love becoming nonsense trophies.

## safety_constraints
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
python -m py_compile datefac/pipeline/batch_ppstructure_row_text_pipeline.py
python -m py_compile datefac/benchmark/batch_row_text_delivery_benchmark.py
python -m py_compile tools/run_batch_ppstructure_outputs_320g.py
```

Then run:

```powershell
python tools/run_batch_ppstructure_outputs_320g.py ^
  --ppstructure-batch-dir E:\mineru_lab\ppstructure_batch_outputs_320f ^
  --output-dir D:\_datefac\output\batch_row_text_delivery_320g
```

If input dirs are missing, produce blocked/partial output and keep compile-clean.

## commit_requirements
After implementation:
1. `git status`
2. only add 320G code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Integrate batch PPStructure row text outputs`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- batch_table_count
- batch_ok_count
- parsed_table_count
- table_with_row_text_count
- table_with_candidates_count
- table_with_trusted_count
- report_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- batch_delivery_decision
- top risk tags
- skipped/untracked files
