# 320F Multi-Report Sandbox Benchmark

## task_title
Build a multi-report benchmark harness for row-text delivery outputs and generate recognizer worklist for more reports

## project
D:\_datefac

## current_context
320E completed the first sandbox delivery bundle from row-text mapping.

Latest 320E result:
- pushed branch: main
- commit hash: 1fbe385
- source_candidate_count: 100
- trusted_delivery_count: 95
- review_required_delivery_count: 5
- rejected_source_count: 0
- unique_metric_count: 20
- unique_year_count: 5
- provenance_row_count: 100
- qa_pass_count: 8
- qa_warn_count: 0
- qa_fail_count: 0
- delivery_decision: SANDBOX_DELIVERY_READY_FOR_320F_MULTI_REPORT_BENCHMARK

Engineering interpretation:
- The DateFac row-text route is now viable on one known cash-flow table sample.
- This is not production readiness. One sample success can still be a lucky accident wearing a graduation gown.
- Next stage must test generalization across multiple reports/tables.

Important current reality:
- MinerU has already produced table assets for 10 reports in earlier benchmark stages.
- Legacy PPStructure row-text recognition is local/manual and should not be run by Codex.
- 320F must therefore build a benchmark harness and a worklist for more recognizer runs, while benchmarking any already available delivery/mapping outputs.

## goal
Implement 320F sandbox benchmark tooling with two purposes:

1. Benchmark existing row-text delivery/mapping outputs across available reports/tables.
2. Generate a prioritized recognizer worklist from MinerU table assets for missing reports/tables, so the user can manually run PPStructure later.

This task should answer:
- How many report/table samples are currently benchmarked?
- Is the 320E result only one-table success?
- Which report/table images should be recognized next?
- What is coverage by metric family, year, unit, trust split, and provenance?
- What blocks us from broader readiness?

## non_goals
Do not do these in 320F:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call LLM/VLM/cloud API/network.
- Do not modify production Excel files.
- Do not apply data to `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness from one sample.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/320f_multi_report_sandbox_benchmark.md`
- `datefac/benchmark/row_text_delivery_benchmark.py`
- `datefac/benchmark/recognizer_worklist_builder.py`
- `tools/run_row_text_multi_report_benchmark_320f.py`

Potentially modify only if needed:
- `datefac/benchmark/__init__.py`
- `datefac/parser/mineru_output_reader.py` only for read-only reuse or adapter compatibility.

Keep benchmark logic separate from delivery/extraction/governance logic.

## input_contract
Primary available input directories:

```powershell
D:\_datefac\output\row_text_delivery_320e
D:\_datefac\output\row_text_mapping_320d2
D:\_datefac\output\mineru_benchmark_320b2
E:\mineru_lab\output_new
```

The CLI should support:

```powershell
python tools/run_row_text_multi_report_benchmark_320f.py ^
  --delivery-root D:\_datefac\output ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --mineru-benchmark-dir D:\_datefac\output\mineru_benchmark_320b2 ^
  --output-dir D:\_datefac\output\row_text_multi_report_benchmark_320f
```

If some inputs are missing, do not crash. Produce blocked/partial reports with explicit warnings.

## input_discovery
The benchmark should discover available sandbox outputs recursively under `--delivery-root`.

Recognize these output types if present:
- `row_text_delivery_320e.xlsx`
- `row_text_mapping_320d2.xlsx`
- `legacy_ppstructure_row_text_320c4.xlsx`
- similar future files matching `row_text_delivery_*`, `row_text_mapping_*`, `legacy_ppstructure_row_text_*`

For 320F, prefer delivery bundles over raw mapping files:
1. 320E delivery bundle
2. 320D2 mapping output
3. 320C4 candidate output

Do not double-count the same candidate if it appears in multiple stages. Use candidate_id/provenance_id/source_file/source_row_text/metric_code/year to deduplicate defensively.

## benchmark_outputs
Write to:

```powershell
D:\_datefac\output\row_text_multi_report_benchmark_320f
```

Required files:

1. `row_text_multi_report_benchmark_320f.xlsx`

Required sheets:
- `summary`
- `available_delivery_outputs`
- `benchmark_sample_inventory`
- `report_level_metrics`
- `table_level_metrics`
- `metric_coverage`
- `trust_split_summary`
- `unit_year_context_summary`
- `provenance_coverage`
- `qa_summary`
- `known_limitations`
- `recognizer_worklist`
- `recognizer_worklist_commands`
- `missing_recognizer_outputs`
- `benchmark_decision_audit`

2. `row_text_multi_report_benchmark_320f_summary.json`

3. `row_text_multi_report_benchmark_320f_report.md`

Optional:
- `recognizer_worklist.csv`
- `recognizer_worklist.jsonl`
- `benchmark_samples.jsonl`

## available_delivery_outputs sheet
Columns:
- output_type
- output_dir
- file_path
- detected_stage
- source_candidate_count
- trusted_count
- review_required_count
- rejected_count
- unique_metric_count
- unique_year_count
- qa_fail_count
- decision
- usable_for_benchmark
- warnings

## benchmark_sample_inventory sheet
Each row should represent one benchmark sample unit, ideally a report/table output.

Columns:
- sample_id
- source_report_name
- source_file
- source_table_id
- table_context
- source_stage
- available_delivery_bundle
- candidate_count
- trusted_count
- review_required_count
- rejected_count
- unique_metric_count
- unique_year_count
- has_provenance
- has_qa
- sample_status

Sample statuses:
- `BENCHMARKED_DELIVERY`
- `MAPPING_ONLY_AVAILABLE`
- `CANDIDATES_ONLY_AVAILABLE`
- `MINERU_TABLE_ASSET_ONLY`
- `MISSING_RECOGNIZER_OUTPUT`

## report_level_metrics
Aggregate by report/source document.

Columns:
- report_name
- table_asset_count_from_mineru
- recognized_table_count
- delivery_sample_count
- trusted_count
- review_required_count
- rejected_count
- unique_metric_count
- metric_family_coverage
- provenance_coverage_rate
- qa_fail_count
- report_status

Report statuses:
- `READY_SAMPLE`
- `NEEDS_MORE_TABLE_RECOGNITION`
- `NO_RECOGNIZER_OUTPUT`
- `HAS_QA_FAILURE`

## table_level_metrics
Columns:
- source_report_name
- table_asset_id
- table_role_guess
- image_path
- image_exists
- has_ppstructure_output
- has_320c4_candidates
- has_320d2_mapping
- has_320e_delivery
- candidate_count
- trusted_count
- review_required_count
- key_metric_hit_count
- table_status

## metric_coverage
Compute coverage for important metric families.

Metric families:
- profitability
- valuation
- balance_sheet
- cash_flow
- growth
- margin
- other

For each family include:
- candidate_count
- trusted_count
- review_required_count
- unique_metric_count
- unique_report_count
- coverage_notes

## trust_split_summary
Include:
- total_candidates
- trusted_count
- review_required_count
- rejected_count
- trusted_rate
- review_required_rate
- rejected_rate
- top_review_reasons
- top_risk_tags

## unit_year_context_summary
Include:
- unit_unknown_count
- year_inferred_count
- table_header_year_count
- smoke_context_year_count
- invalid_year_count
- unit_context_sources
- year_context_sources

## provenance_coverage
For every candidate/delivery row, check provenance.

Columns:
- sample_id
- candidate_id
- provenance_id
- has_source_file
- has_source_row_text
- has_source_table_id
- has_source_stage
- has_year_source
- has_unit_source
- provenance_complete
- missing_fields

## recognizer_worklist
Generate a prioritized list of MinerU table images that should be processed next by the user's local PPStructure environment.

Source:
- `E:\mineru_lab\output_new`
- existing 320A/320B/320B2 table asset extraction logic, if available.

Do not run PPStructure. Only produce the worklist.

Columns:
- priority
- source_report_name
- mineru_report_dir
- table_asset_id
- table_role_guess
- image_path
- image_exists
- page_idx
- bbox
- caption
- nearby_text_preview
- reason_selected
- expected_metric_family
- recommended_output_dir
- already_has_recognizer_output

Prioritization:
1. core financial statement tables: profit/loss, balance sheet, cash flow;
2. key financial/valuation indicator tables;
3. tables with image_path exists and role guess is not unknown;
4. diversify across reports, not 20 tables from one report.

Limit default worklist to top 30 table assets, but allow CLI arg:

```powershell
--max-worklist 30
```

## recognizer_worklist_commands
Generate PowerShell-friendly commands/templates for the user to run manually in `ppstructure_legacy` environment.

Do not assume exact PPStructure runner exists, but provide command templates pointing to image path and recommended output dir.

Example command template:

```powershell
conda activate ppstructure_legacy
$env:USERPROFILE="E:\paddle_user_legacy"
$env:HOME="E:\paddle_user_legacy"
python E:\mineru_lab\test_ppstructure_legacy.py --image "<image_path>" --output-dir "<recommended_output_dir>"
```

If current local script does not accept arguments, write `manual_command_note` saying script needs argument support. Do not modify `E:\mineru_lab` scripts.

## missing_recognizer_outputs
List reports/tables that have MinerU table assets but no row-text recognizer output/delivery yet.

Columns:
- source_report_name
- table_asset_count
- existing_recognizer_output_count
- missing_core_table_count
- next_action

## benchmark decision
Summary metrics:
- discovered_delivery_bundle_count
- benchmarked_report_count
- benchmarked_table_count
- mineru_report_count
- mineru_table_asset_count
- recognizer_output_coverage_rate
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- qa_fail_count
- provenance_complete_rate
- worklist_count
- benchmark_decision

Decision rule:
- If qa_fail_count > 0:
  `MULTI_REPORT_BENCHMARK_BLOCKED_BY_QA_FAILURE`
- If benchmarked_report_count >= 5, trusted_rate >= 0.60, provenance_complete_rate >= 0.95, and qa_fail_count == 0:
  `MULTI_REPORT_BENCHMARK_READY_FOR_320G_PIPELINE_INTEGRATION_PLAN`
- If benchmarked_report_count >= 2 and qa_fail_count == 0:
  `MULTI_REPORT_BENCHMARK_PARTIAL_NEEDS_MORE_REPORTS`
- If benchmarked_report_count < 2 but worklist_count > 0:
  `NEED_MORE_RECOGNIZER_OUTPUTS_FROM_WORKLIST`
- Otherwise:
  `MULTI_REPORT_BENCHMARK_NOT_READY`

Given current known state, it is acceptable and expected that 320F may produce:
- `NEED_MORE_RECOGNIZER_OUTPUTS_FROM_WORKLIST`

That is useful, not a failure. It tells us exactly what to run next instead of wandering around like a lost intern with Docker open.

## validation
Run:

```powershell
python -m py_compile datefac/benchmark/row_text_delivery_benchmark.py
python -m py_compile datefac/benchmark/recognizer_worklist_builder.py
python -m py_compile tools/run_row_text_multi_report_benchmark_320f.py
```

Then run:

```powershell
python tools/run_row_text_multi_report_benchmark_320f.py ^
  --delivery-root D:\_datefac\output ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --mineru-benchmark-dir D:\_datefac\output\mineru_benchmark_320b2 ^
  --output-dir D:\_datefac\output\row_text_multi_report_benchmark_320f ^
  --max-worklist 30
```

If local output directories are missing, produce partial/blocked report and keep code compile-clean.

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

## commit_requirements
After implementation:
1. `git status`
2. only add 320F code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Benchmark row text delivery across reports`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- discovered_delivery_bundle_count
- benchmarked_report_count
- benchmarked_table_count
- mineru_report_count
- mineru_table_asset_count
- recognizer_output_coverage_rate
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- qa_fail_count
- provenance_complete_rate
- worklist_count
- benchmark_decision
- skipped/untracked files
