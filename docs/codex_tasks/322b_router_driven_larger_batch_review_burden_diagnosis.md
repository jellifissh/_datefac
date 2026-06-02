# 322B Router-driven Larger Batch Review-burden Diagnosis

## task_title
Continue the router-driven sandbox pipeline after 322A, process the remaining eligible MinerU-body missing routes, and add review-burden diagnostics without changing mapping rules

## project
D:\_datefac

## current_context
322A completed a bounded MinerU-body sandbox expansion and produced:

```powershell
D:\_datefac\output\router_driven_sandbox_pipeline_322a
```

Key 322A results:
- selected_output_table_count_after_322a: 88
- no_available_output_count_after_322a: 89
- newly_processed_mineru_table_count: 50
- selected_candidate_total_count: 4167
- selected_review_required_total_count: 3505
- selected_core_trusted_rate: 0.12647
- remaining_missing_output_worklist_count: 87
- router_driven_sandbox_pipeline_decision: `ROUTER_DRIVEN_SANDBOX_PIPELINE_READY_FOR_322B_LARGER_BATCH`

Important interpretation:
- 322A materially improved MinerU-body coverage.
- The dominant remaining problem is review burden, not missing router policy.
- Many new MinerU-body outputs are review-heavy because of unknown labels, invalid years, unit ambiguity, and context-sensitive rows.
- 322B should expand the larger batch while diagnosing review burden instead of adding new alias or unit rules.

## goal
Implement and execute a larger-batch sandbox-only continuation of 322A.

322B should:
1. read 322A output as the selected-output baseline;
2. read 321G/321F routing outputs and existing sandbox outputs;
3. continue processing remaining eligible `MINERU_TABLE_BODY_321D` routes using existing MinerU outputs under `E:\mineru_lab\output_new`;
4. merge new 322B MinerU-body outputs with already selected 322A outputs;
5. regenerate selected preview / candidate / trusted / review / rejected views;
6. add review-burden diagnostics and worklists;
7. produce a clear sandbox decision for next-step adjudication or manual review planning.

## non_goals
Do not do these in 322B:
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PPStructure.
- Do not run VLM.
- Do not modify `E:\mineru_lab`.
- Do not modify production pipeline.
- Do not add alias mappings.
- Do not add new unit rules.
- Do not change trusted-rate logic just to improve metrics.

## input_contract
Read-only inputs:

```powershell
D:\_datefac\output\router_driven_sandbox_pipeline_322a
D:\_datefac\output\router_sandbox_integration_321g
D:\_datefac\output\recognizer_router_321f
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\structtable_unified_mapping_321e4b
D:\_datefac\output\docling_unified_mapping_321e2
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
E:\mineru_lab\output_new
```

CLI:

```powershell
python tools/run_router_driven_sandbox_pipeline_322b.py ^
  --router-integration-dir D:\_datefac\output\router_sandbox_integration_321g ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --existing-mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --prior-322a-output-dir D:\_datefac\output\router_driven_sandbox_pipeline_322a ^
  --output-dir D:\_datefac\output\router_driven_sandbox_pipeline_322b ^
  --max-new-mineru-tables 45
```

Default `--max-new-mineru-tables` should be 45 or all remaining eligible when fewer remain.

## selection_requirements
Continue only the remaining eligible routes where:
- `recommended_recognizer == MINERU_TABLE_BODY_321D`
- `final_sandbox_action == NEEDS_MINERU_BODY_INGESTION`
- the route is in the core role set
- the route was not already selected into 322A selected outputs
- the route is not manual-review-only

Selection rules:
1. preserve router provenance and risk context;
2. do not reprocess already selected 322A outputs;
3. process up to `--max-new-mineru-tables`, which defaults to 45;
4. if 45 or fewer eligible routes remain, process all of them.

## diagnostics_required
Output directory:

```powershell
D:\_datefac\output\router_driven_sandbox_pipeline_322b
```

Required sheets / reports:
- `summary`
- `selected_322b_mineru_worklist`
- `mineru_body_processing_audit`
- `router_selected_output_preview_322b`
- `metric_candidates_all_322b`
- `trusted_preview_322b`
- `review_required_preview_322b`
- `rejected_preview_322b`
- `review_burden_by_reason`
- `unknown_metric_label_frequency`
- `unit_unknown_diagnostics`
- `section_context_required_diagnostics`
- `out_of_scope_candidate_summary`
- `alias_candidate_worklist`
- `semantic_adjudicator_worklist_322b`
- `manual_review_worklist_322b`
- `remaining_missing_output_worklist`
- `coverage_by_route_322b`
- `qa_checks`

## required_summary_metrics
Report these metrics:
- `newly_processed_mineru_table_count`
- `selected_output_table_count_before_322b`
- `selected_output_table_count_after_322b`
- `no_available_output_count_after_322b`
- `selected_candidate_total_count`
- `selected_trusted_total_count`
- `selected_review_required_total_count`
- `selected_core_trusted_rate`
- `top_review_reason_counts`
- `unknown_metric_unique_label_count`
- `alias_candidate_count`
- `semantic_adjudicator_worklist_count`
- `manual_review_worklist_count`
- `qa_fail_count`
- `router_driven_sandbox_pipeline_decision`

## validation
Required validation:
1. `py_compile` for new 322B files
2. actual CLI run using the command above
3. confirm no recognizer execution occurred
4. confirm `output/` and `E:\mineru_lab` are not staged
5. commit only 322B-related code and task doc
