# 322A Router-driven Sandbox Pipeline

## task_title
Run a router-driven sandbox pipeline over 321G worklists and expand MinerU-body coverage without production integration

## project
D:\_datefac

## current_context
321G router sandbox integration has completed and pushed to `main`.

321G output directory:

```powershell
D:\_datefac\output\router_sandbox_integration_321g
```

321G key results:
- route_total_count: 216
- selected_output_table_count: 38
- no_available_output_count: 139
- mineru_routed_count: 175
- mineru_output_available_count: 20
- structtable_routed_count: 1
- structtable_output_available_count: 16
- docling_backup_routed_count: 134
- docling_output_available_count: 18
- pure_vlm_adjudicator_count: 13
- pure_vlm_output_available_count: 18
- manual_review_count: 17
- semantic_adjudicator_worklist_count: 13
- missing_output_worklist_count: 138
- selected_candidate_total_count: 2564
- selected_trusted_total_count: 854
- selected_review_required_total_count: 1575
- selected_core_trusted_rate: 0.313135
- qa_pass_count: 12
- qa_warn_count: 4
- qa_fail_count: 0
- router_sandbox_integration_decision: `ROUTER_SANDBOX_INTEGRATION_READY_NEEDS_RECOGNIZER_OUTPUTS`

Important interpretation:
- The router works, but output coverage is still low because earlier recognition/mapping probes only covered limited samples.
- The largest gap is not StructEqTable; it is MinerU body route coverage:
  - 175 tables are routed to `MINERU_TABLE_BODY_321D`.
  - only 20 MinerU-body mapped outputs are currently available from 321D phase 1.
- Therefore the next step should not run new OCR/VLM tools.
- The next step should expand the sandbox pipeline over router-selected MinerU-body routes by reading existing MinerU output under `E:\mineru_lab\output_new` and reusing the MinerU-body reader/normalizer/mapper.

Prior policy decisions:
- PDF table_body default route: `MINERU_TABLE_BODY_321D`
- image-table default route: `STRUCTTABLE_INTERVL2`
- Pure VLM: semantic adjudicator only, not bulk default recognizer
- Docling: backup candidate
- PPStructure: weak legacy fallback

## goal
Implement 322A as a sandbox-only router-driven pipeline dry run.

322A should:
1. read the 321G router action plan and missing-output worklist;
2. select a bounded batch of high-priority missing `MINERU_TABLE_BODY_321D` routes;
3. process those routes using existing MinerU outputs under `E:\mineru_lab\output_new` without running MinerU;
4. convert newly processed tables to Unified Tables and MetricCandidate previews using the existing MinerU-body code path where safe;
5. merge newly generated sandbox MinerU-body outputs with existing selected outputs from 321G;
6. regenerate selected trusted/review/rejected preview and route coverage metrics;
7. produce semantic adjudicator and manual review worklists for unresolved candidates;
8. output a clear decision on whether the router-driven sandbox pipeline is ready for a larger 322B batch or needs more recognizer output coverage.

This is still sandbox-only. It is not production integration.

## non_goals
Do not do these in 322A:
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not modify `E:\mineru_lab`.
- Do not modify production delivery files.
- Do not apply anything into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not continue broad 321D2 normalizer expansion.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/pipeline/router_driven_sandbox_pipeline.py`
- `datefac/pipeline/router_selected_delivery_preview.py`
- `tools/run_router_driven_sandbox_pipeline_322a.py`
- `docs/codex_tasks/322a_router_driven_sandbox_pipeline.md`

Likely reused modules:
- `datefac/router/router_sandbox_integration.py`
- `datefac/router/route_output_resolver.py`
- `datefac/mineru_body/mineru_table_body_reader.py`
- `datefac/mineru_body/mineru_table_normalizer.py`
- `datefac/mineru_body/mineru_body_candidate_mapper.py`
- `datefac/mineru_body/mineru_body_delivery_builder.py`
- `datefac/table_bakeoff/*` only for reading existing StructEqTable/Docling mapped outputs, not for running recognizers.

Keep new code in sandbox pipeline/planning layers. Do not modify production pipeline entrypoints.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\router_sandbox_integration_321g
D:\_datefac\output\recognizer_router_321f
E:\mineru_lab\output_new
```

Existing sandbox output inputs:

```powershell
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\structtable_unified_mapping_321e4b
D:\_datefac\output\docling_unified_mapping_321e2
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

Optional audit/planning inputs:

```powershell
D:\_datefac\output\table_extraction_full_bakeoff_321e5
D:\_datefac\output\source_aware_router_revision_321c2
D:\_datefac\output\mineru_benchmark_320b2
```

CLI:

```powershell
python tools/run_router_driven_sandbox_pipeline_322a.py ^
  --router-integration-dir D:\_datefac\output\router_sandbox_integration_321g ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --existing-mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\router_driven_sandbox_pipeline_322a ^
  --max-new-mineru-tables 50
```

Default `--max-new-mineru-tables` should be 50. Allow smaller values for smoke tests and larger values later, but do not default to all 175.

If primary inputs are missing, produce blocked summary instead of crashing:
- `BLOCKED_MISSING_321G_ROUTER_INTEGRATION_DIR`
- `BLOCKED_MISSING_321F_ROUTER_DIR`
- `BLOCKED_MISSING_MINERU_OUTPUT_ROOT`

## selection_requirements
Read 321G outputs, preferably:
- `router_sandbox_action_plan_321g.json`
- `missing_output_worklist` sheet/jsonl
- `output_availability_matrix`

Select tables where:
- `recommended_recognizer == MINERU_TABLE_BODY_321D`
- `final_sandbox_action` is `NEEDS_MINERU_BODY_INGESTION` or equivalent missing-output action
- table is not manual-review-only or unsupported
- priority is high or category is core financial/valuation where available

Selection rules:
1. Preserve router reason and risk tags.
2. Prefer core categories: income statement, balance sheet, cash flow, financial forecast/valuation.
3. Diversify across source reports where possible.
4. Do not process more than `--max-new-mineru-tables`.
5. If no eligible MinerU-body missing routes exist, produce a clear no-op report.

## mineru_body_processing_requirements
For each selected table:
1. locate the corresponding MinerU report output under `E:\mineru_lab\output_new`;
2. extract table_body/html/markdown/content_list table text using existing MinerU-body reader logic;
3. normalize into Unified Table JSON;
4. map into MetricCandidate-like records with `source_stage = router_driven_mineru_body_322a`;
5. preserve route provenance and original table_asset_id;
6. split candidates into trusted/review_required/rejected using conservative gates;
7. do not invent values or use VLM to repair.

If exact table match fails:
- mark `MINERU_BODY_OUTPUT_NOT_FOUND`;
- include it in missing output report;
- do not crash.

## merge_requirements
Merge newly generated 322A MinerU-body outputs with existing sandbox outputs selected by 321G.

Priority order for selected output preview:
1. newly generated 322A MinerU-body output for the table if route recommends MinerU and output is valid;
2. existing MinerU-body 321D output;
3. existing StructEqTable 321E4B output if route recommends StructEqTable;
4. existing Docling 321E2 backup output if recommended/fallback route allows it;
5. existing pure VLM calibrated output only as adjudicated/semantic output, not bulk selected recognizer;
6. manual review / no available output.

Do not double-count the same table asset across multiple sources.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary with all key metrics.

### `selected_322a_mineru_worklist`
- table_asset_id
- source_report_name
- table_title
- effective_category
- router_reason
- priority
- selected_for_processing
- reason

### `mineru_body_processing_audit`
- table_asset_id
- source_report_name
- match_status
- matched_by
- content_source_file
- has_table_body
- has_html
- has_markdown_table
- parsed_row_count
- parsed_column_count
- candidate_count
- trusted_count
- review_required_count
- rejected_count
- warnings

### `router_selected_output_preview_322a`
- table_asset_id
- selected_output_source
- output_origin
- candidate_count
- trusted_count
- review_required_count
- rejected_count
- core_candidate_trusted_rate
- all_candidate_trusted_rate
- semantic_adjudicator_required
- manual_review_required
- risk_tags
- notes

### `metric_candidates_all_322a`
- table_asset_id
- source_report_name
- selected_output_source
- source_stage
- metric_code
- metric_family
- year
- raw_value
- normalized_value
- unit
- split_decision
- risk_tags
- provenance

### `trusted_preview_322a`
### `review_required_preview_322a`
### `rejected_preview_322a`

### `semantic_adjudicator_worklist_322a`
- table_asset_id
- source_report_name
- table_title
- selected_output_source
- adjudication_reason
- risk_tags
- candidate_count_affected
- sample_labels
- priority

### `manual_review_worklist_322a`
- table_asset_id
- source_report_name
- table_title
- manual_review_reason
- selected_output_source
- priority
- notes

### `remaining_missing_output_worklist`
- table_asset_id
- source_report_name
- table_title
- recommended_recognizer
- required_action
- priority
- reason

### `coverage_by_route_322a`
- recognizer
- routed_count
- existing_output_count_before_322a
- newly_processed_count_322a
- selected_count_after_322a
- missing_count_after_322a
- coverage_rate_after_322a

### `qa_checks`
### `known_limitations`

## output_contract
Write to:

```powershell
D:\_datefac\output\router_driven_sandbox_pipeline_322a
```

Required files:
1. `router_driven_sandbox_pipeline_322a.xlsx`

Sheets:
- `summary`
- `selected_322a_mineru_worklist`
- `mineru_body_processing_audit`
- `router_selected_output_preview_322a`
- `metric_candidates_all_322a`
- `trusted_preview_322a`
- `review_required_preview_322a`
- `rejected_preview_322a`
- `semantic_adjudicator_worklist_322a`
- `manual_review_worklist_322a`
- `remaining_missing_output_worklist`
- `coverage_by_route_322a`
- `qa_checks`
- `known_limitations`

2. `router_driven_sandbox_pipeline_322a_summary.json`

3. `router_driven_sandbox_pipeline_322a_report.md`

4. `router_selected_delivery_preview_322a.jsonl`

Optional:
- `metric_candidates_all_322a.jsonl`
- `semantic_adjudicator_worklist_322a.jsonl`

## summary_metrics
Include:
- router_route_total_count
- eligible_mineru_missing_count
- selected_new_mineru_table_count
- attempted_new_mineru_table_count
- newly_processed_mineru_table_count
- newly_failed_mineru_table_count
- selected_output_table_count_before_322a
- selected_output_table_count_after_322a
- no_available_output_count_before_322a
- no_available_output_count_after_322a
- selected_candidate_total_count
- selected_trusted_total_count
- selected_review_required_total_count
- selected_rejected_total_count
- selected_core_trusted_rate
- selected_all_trusted_rate
- semantic_adjudicator_worklist_count
- manual_review_worklist_count
- remaining_missing_output_worklist_count
- mineru_coverage_before_322a
- mineru_coverage_after_322a
- structtable_coverage_after_322a
- docling_backup_coverage_after_322a
- qa_pass_count
- qa_warn_count
- qa_fail_count
- router_driven_sandbox_pipeline_decision

Decision rule:
- If qa_fail_count > 0:
  `ROUTER_DRIVEN_SANDBOX_PIPELINE_BLOCKED_BY_QA_FAILURE`
- If newly_processed_mineru_table_count >= selected_new_mineru_table_count * 0.8 and selected_output_table_count_after_322a > selected_output_table_count_before_322a:
  `ROUTER_DRIVEN_SANDBOX_PIPELINE_READY_FOR_322B_LARGER_BATCH`
- If selected_new_mineru_table_count == 0 and no_available_output_count_after_322a > 0:
  `ROUTER_DRIVEN_SANDBOX_PIPELINE_NOOP_NEEDS_RECOGNIZER_RUNS`
- Otherwise:
  `ROUTER_DRIVEN_SANDBOX_PIPELINE_PARTIAL_NEEDS_EXTRACTION_COVERAGE`

## qa_checks
Required checks:
- 321G router integration dir exists;
- 321F router dir exists;
- MinerU output root exists;
- no E-drive files modified;
- no external recognizer command executed;
- no production files modified;
- every selected 322A candidate has table_asset_id and source_stage;
- trusted candidates have valid year, known metric code, parsed value, and provenance;
- no table_asset_id is double-counted in selected output preview;
- selected_output_table_count_after_322a >= selected_output_table_count_before_322a;
- output files written successfully.

Warnings, not failures:
- some selected MinerU-body outputs not found;
- remaining missing outputs after max batch cap;
- semantic adjudicator still needed for review-heavy candidates;
- limited benchmark-to-router alignment.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run StructEqTable.
3. Do not run Docling.
4. Do not run PaddleOCR/PPStructure.
5. Do not call VLM/API/cloud/network.
6. Do not modify E-drive input/output folders.
7. Do not modify production delivery files.
8. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
9. Do not modify `data/mapping/formal_scope_rules.json`.
10. Do not run `factory_core.py`.
11. Do not rewrite old Stage7 pipeline.
12. Do not continue broad 321D2 normalizer expansion.
13. Do not commit `output/` artifacts.
14. Do not commit anything under `E:\mineru_lab`.
15. Do not commit unrelated 320G2 leftovers or temp scripts.
16. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/pipeline/router_driven_sandbox_pipeline.py
python -m py_compile datefac/pipeline/router_selected_delivery_preview.py
python -m py_compile tools/run_router_driven_sandbox_pipeline_322a.py
```

Then run:

```powershell
python tools/run_router_driven_sandbox_pipeline_322a.py ^
  --router-integration-dir D:\_datefac\output\router_sandbox_integration_321g ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --existing-mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\router_driven_sandbox_pipeline_322a ^
  --max-new-mineru-tables 50
```

PowerShell one-line form is acceptable. Report exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 322A code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Run router driven sandbox pipeline`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- router_route_total_count
- eligible_mineru_missing_count
- selected_new_mineru_table_count
- attempted_new_mineru_table_count
- newly_processed_mineru_table_count
- newly_failed_mineru_table_count
- selected_output_table_count_before_322a
- selected_output_table_count_after_322a
- no_available_output_count_before_322a
- no_available_output_count_after_322a
- selected_candidate_total_count
- selected_trusted_total_count
- selected_review_required_total_count
- selected_core_trusted_rate
- selected_all_trusted_rate
- semantic_adjudicator_worklist_count
- manual_review_worklist_count
- remaining_missing_output_worklist_count
- mineru_coverage_before_322a
- mineru_coverage_after_322a
- qa_pass_count
- qa_warn_count
- qa_fail_count
- router_driven_sandbox_pipeline_decision
- skipped/untracked files
