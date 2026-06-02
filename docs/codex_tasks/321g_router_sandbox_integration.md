# 321G Router Sandbox Integration

## task_title
Integrate 321F recognizer router into sandbox route manifests and selected-output preview

## project
D:\_datefac

## current_context
321F recognizer router implementation has completed and pushed to `main`.

321F output directory:

```powershell
D:\_datefac\output\recognizer_router_321f
```

321F key results:
- route_total_count: 216
- mineru_default_count: 175
- structtable_default_count: 1
- pure_vlm_adjudicator_count: 13
- docling_backup_count: 134
- ppstructure_fallback_count: 0
- manual_review_count: 17
- qa_fail_count: 0
- router_decision: `RECOGNIZER_ROUTER_321F_READY_FOR_SANDBOX_INTEGRATION`

321F policy decisions:
- PDF `table_body` default route is `MINERU_TABLE_BODY_321D`.
- image-table default route is `STRUCTTABLE_INTERVL2`.
- `PURE_VLM` is a semantic adjudicator signal only, not a bulk recommended recognizer.
- `Docling` is retained as backup candidate.
- `PPStructure` is retained only as weak legacy fallback.

Prior major evidence:
- 321E5 overall route ranking:
  1. `MINERU_TABLE_BODY_321D` overall `71.88`
  2. `STRUCTTABLE_INTERVL2_321E4B` overall `64.61`
  3. `PURE_VLM_321B2_CALIBRATED` overall `64.09`
  4. `DOCLING_TABLE_GRID_321E2` overall `61.52`
  5. `PPSTRUCTURE_320G` overall `42.66`
- MinerU body is the current PDF table_body baseline.
- StructEqTable is the strongest image-table extraction candidate.
- Pure VLM is better positioned as semantic adjudicator / review helper.
- Docling is a backup candidate.
- PPStructure is not a mainline route.

Important interpretation:
- 321F is still a plan/report layer.
- The next step is not production integration.
- The next step is a sandbox integration dry-run that joins the router plan with available recognizer outputs, builds missing-output worklists, and shows what DateFac would select per table if the router were active.

## goal
Implement 321G as a sandbox-only router integration dry-run.

321G should:
1. read the 321F router plan for all 216 table assets;
2. resolve whether each recommended recognizer already has available sandbox output;
3. select the best currently available candidate source per table without running any recognizer;
4. produce route-specific worklists for missing outputs;
5. produce a router-selected candidate preview where available;
6. summarize coverage, gaps, semantic adjudicator needs, manual review burden, and readiness for 322A sandbox pipeline integration.

This is a dry-run integration layer. It must not run external recognizers and must not modify production files.

## non_goals
Do not do these in 321G:
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not modify E:\mineru_lab.
- Do not modify production delivery files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not continue 321D2 normalizer expansion.
- Do not change router policy unless a clear QA inconsistency is found.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/router/route_output_resolver.py`
- `datefac/router/router_sandbox_integration.py`
- `tools/run_router_sandbox_integration_321g.py`
- `docs/codex_tasks/321g_router_sandbox_integration.md`

Likely reused files:
- `datefac/router/recognizer_router_321f.py`
- existing table bakeoff output schemas/readers where safe

Keep this inside the router/sandbox planning layer. Do not modify production pipeline, MinerU-body, VLM, PPStructure, or old Stage7 modules.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\recognizer_router_321f
D:\_datefac\output\table_extraction_full_bakeoff_321e5
D:\_datefac\output\source_aware_router_revision_321c2
```

Available sandbox output inputs:

```powershell
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\structtable_unified_mapping_321e4b
D:\_datefac\output\docling_unified_mapping_321e2
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

Optional audit inputs:

```powershell
D:\_datefac\output\structtable_output_audit_321e3
D:\_datefac\output\docling_output_audit_321e1
D:\_datefac\output\mineru_benchmark_320b2
```

CLI:

```powershell
python tools/run_router_sandbox_integration_321g.py ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --bakeoff-dir D:\_datefac\output\table_extraction_full_bakeoff_321e5 ^
  --router-revision-dir D:\_datefac\output\source_aware_router_revision_321c2 ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\router_sandbox_integration_321g
```

If a primary router input is missing, produce blocked output rather than crashing:
- `BLOCKED_MISSING_321F_ROUTER_DIR`
- `BLOCKED_MISSING_321E5_BAKEOFF_DIR`

If optional recognizer outputs are missing, continue with warnings and mark corresponding routes as output unavailable.

## route_resolution_requirements
For each table asset in the 321F route plan:

Resolve:
- `table_asset_id`
- `source_report_name`
- `table_title`
- `table_role/effective_category` if available
- `recommended_recognizer`
- `fallback_recognizer`
- `semantic_adjudicator_required`
- `manual_review_required`
- `router_risk_tags`
- `router_reason`

Then determine:
- whether recommended recognizer output exists in sandbox outputs;
- whether backup recognizer output exists;
- whether selected output has candidates;
- whether selected output has trusted candidates;
- whether selected output requires semantic adjudication;
- final sandbox action.

Final sandbox actions:
- `SELECT_MINERU_BODY_OUTPUT`
- `SELECT_STRUCTTABLE_OUTPUT`
- `SELECT_DOCLING_BACKUP_OUTPUT`
- `SELECT_PURE_VLM_ADJUDICATED_OUTPUT`
- `NEEDS_STRUCTTABLE_RUN`
- `NEEDS_MINERU_BODY_INGESTION`
- `NEEDS_SEMANTIC_ADJUDICATOR`
- `NEEDS_MANUAL_REVIEW`
- `SKIP_NON_CORE_TABLE`
- `UNSUPPORTED_TABLE_TYPE`
- `NO_AVAILABLE_OUTPUT`

Do not synthesize values. Only select among already existing sandbox outputs.

## output_resolution_notes
Existing output sets may not cover all 216 router assets:
- MinerU body 321D covered only the first 20 selected tables.
- StructEqTable 321E4B covered the fixed 10 image benchmark images.
- Docling 321E2 covered the fixed 10 image benchmark images.
- Pure VLM 321B2 covered 10/11 manual samples.
- PPStructure 320G covered a limited 10-table batch.

321G must report this honestly. Missing outputs are expected and are not QA failures unless the router output itself is malformed.

## diagnostics_required
Create these sheets:

### `router_integration_summary`
One-row summary with all main metrics.

### `router_route_inventory`
Columns:
- table_asset_id
- source_report_name
- table_title
- effective_category
- recommended_recognizer
- fallback_recognizer
- semantic_adjudicator_required
- manual_review_required
- router_risk_tags
- router_reason

### `output_availability_matrix`
Columns:
- table_asset_id
- source_report_name
- recommended_recognizer
- mineru_body_output_available
- structtable_output_available
- docling_output_available
- pure_vlm_output_available
- ppstructure_output_available
- any_output_available
- selected_output_source
- final_sandbox_action
- reason

### `router_selected_candidate_preview`
Columns:
- table_asset_id
- selected_output_source
- candidate_count
- trusted_count
- review_required_count
- rejected_count
- core_candidate_trusted_rate
- all_candidate_trusted_rate
- risk_tags
- provenance_status
- notes

### `missing_output_worklist`
Columns:
- table_asset_id
- source_report_name
- table_title
- recommended_recognizer
- required_action
- priority
- reason

### `semantic_adjudicator_worklist`
Columns:
- table_asset_id
- source_report_name
- table_title
- selected_output_source
- adjudication_reason
- risk_tags
- candidate_count_affected
- priority

Adjudication reasons:
- `UNKNOWN_METRIC_CODE_CORE_CONTEXT`
- `UNIT_UNKNOWN_WITH_CLEAR_TABLE_CONTEXT`
- `VALUE_CONFLICT_SECTION_CONTEXT`
- `DUPLICATED_LABEL_SECTION_CONTEXT`
- `OUT_OF_SCOPE_OR_CORE_CLASSIFICATION`

### `manual_review_worklist`
Columns:
- table_asset_id
- source_report_name
- table_title
- manual_review_reason
- selected_output_source
- priority
- notes

### `route_coverage_by_recognizer`
Columns:
- recognizer
- routed_count
- available_output_count
- selected_count
- missing_output_count
- trusted_candidate_count
- review_required_candidate_count
- coverage_rate

### `qa_checks`
Required QA checks and pass/warn/fail status.

### `known_limitations`
Explain limited sample coverage and why 321G is not production integration.

## output_contract
Write to:

```powershell
D:\_datefac\output\router_sandbox_integration_321g
```

Required files:
1. `router_sandbox_integration_321g.xlsx`

Sheets:
- `summary`
- `router_route_inventory`
- `output_availability_matrix`
- `router_selected_candidate_preview`
- `missing_output_worklist`
- `semantic_adjudicator_worklist`
- `manual_review_worklist`
- `route_coverage_by_recognizer`
- `qa_checks`
- `known_limitations`

2. `router_sandbox_integration_321g_summary.json`

3. `router_sandbox_integration_321g_report.md`

4. `router_sandbox_action_plan_321g.json`

Optional:
- `missing_output_worklist.jsonl`
- `semantic_adjudicator_worklist.jsonl`

## summary_metrics
Include:
- route_total_count
- route_inventory_count
- selected_output_table_count
- no_available_output_count
- mineru_routed_count
- mineru_output_available_count
- structtable_routed_count
- structtable_output_available_count
- docling_backup_routed_count
- docling_output_available_count
- pure_vlm_adjudicator_count
- pure_vlm_output_available_count
- ppstructure_fallback_count
- ppstructure_output_available_count
- manual_review_count
- semantic_adjudicator_worklist_count
- missing_output_worklist_count
- selected_candidate_total_count
- selected_trusted_total_count
- selected_review_required_total_count
- selected_rejected_total_count
- selected_core_trusted_rate
- selected_all_trusted_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- router_sandbox_integration_decision

Decision rule:
- If qa_fail_count > 0:
  `ROUTER_SANDBOX_INTEGRATION_BLOCKED_BY_QA_FAILURE`
- If route_inventory_count == route_total_count and missing_output_worklist_count > 0:
  `ROUTER_SANDBOX_INTEGRATION_READY_NEEDS_RECOGNIZER_OUTPUTS`
- If selected_output_table_count >= route_total_count * 0.5 and qa_fail_count == 0:
  `ROUTER_SANDBOX_INTEGRATION_READY_FOR_322A_SANDBOX_PIPELINE`
- Otherwise:
  `ROUTER_SANDBOX_INTEGRATION_PARTIAL_NEEDS_MORE_OUTPUT_COVERAGE`

## qa_checks
Required checks:
- 321F router dir exists;
- 321F route_total_count matches loaded route inventory count;
- no E-drive files modified;
- no recognizer command executed;
- every route has recommended_recognizer;
- every final_sandbox_action has reason;
- pure VLM is not used as recommended bulk recognizer;
- StructEqTable remains image-table default where applicable;
- MinerU remains PDF table_body default where applicable;
- selected candidates, if any, have provenance reference;
- output files written successfully.

Warnings, not failures:
- missing sandbox outputs for routes not yet run;
- limited sample coverage;
- benchmark outputs not one-to-one aligned with all 216 router assets.

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
12. Do not continue 321D2 normalizer expansion.
13. Do not commit `output/` artifacts.
14. Do not commit anything under `E:\mineru_lab`.
15. Do not commit unrelated 320G2 leftovers or temp scripts.
16. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/router/route_output_resolver.py
python -m py_compile datefac/router/router_sandbox_integration.py
python -m py_compile tools/run_router_sandbox_integration_321g.py
```

Then run:

```powershell
python tools/run_router_sandbox_integration_321g.py ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --bakeoff-dir D:\_datefac\output\table_extraction_full_bakeoff_321e5 ^
  --router-revision-dir D:\_datefac\output\source_aware_router_revision_321c2 ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\router_sandbox_integration_321g
```

PowerShell one-line form is acceptable. Report exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321G code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Integrate recognizer router sandbox plan`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- route_total_count
- selected_output_table_count
- no_available_output_count
- mineru_routed_count
- mineru_output_available_count
- structtable_routed_count
- structtable_output_available_count
- docling_backup_routed_count
- docling_output_available_count
- pure_vlm_adjudicator_count
- pure_vlm_output_available_count
- manual_review_count
- semantic_adjudicator_worklist_count
- missing_output_worklist_count
- selected_candidate_total_count
- selected_trusted_total_count
- selected_review_required_total_count
- selected_core_trusted_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- router_sandbox_integration_decision
- skipped/untracked files
