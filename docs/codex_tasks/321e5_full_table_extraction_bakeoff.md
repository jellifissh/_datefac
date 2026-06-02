# 321E5 Full Table Extraction Bakeoff

## task_title
Build a read-only full bakeoff across existing 321D / 321B2 / 321E1 / 321E2 / 321E3 / 321E4B outputs and produce a router recommendation

## project
`D:\_datefac`

## current_context
- 321D MinerU table_body ingestion exists.
- 321B2 pure VLM mapping calibration exists.
- 321E1 Docling output audit exists.
- 321E2 Docling unified mapping probe exists.
- 321E3 StructEqTable output audit exists.
- 321E4B StructEqTable mapping calibration exists.

This task is a bakeoff synthesizer only.

## goal
Create a full table extraction bakeoff that reads only existing outputs and compares:
- MinerU table_body
- pure VLM calibrated
- Docling
- StructEqTable / StructTable-InternVL2
- PPStructure row-text fallback

Output:
- `D:\_datefac\output\table_extraction_full_bakeoff_321e5`

The bakeoff must score each route on:
- `extraction_score`
- `all_candidate_mapping_score`
- `core_candidate_mapping_score`
- `review_burden_score`

And must report:
- `all_candidate_trusted_rate`
- `core_candidate_trusted_rate`
- `out_of_scope_candidate_count`
- `review_required_core_count`
- `unit_unknown_count`
- `unknown_metric_code_count`
- `value_conflict_count`
- `provenance_complete_rate`

Also produce a router plan covering:
- default PDF `table_body` route
- default image-table route
- semantic adjudicator scenarios
- manual review scenarios

## allowed_inputs
Only read these existing directories:
- `D:\_datefac\output\structtable_unified_mapping_321e4b`
- `D:\_datefac\output\structtable_output_audit_321e3`
- `D:\_datefac\output\docling_unified_mapping_321e2`
- `D:\_datefac\output\docling_output_audit_321e1`
- `D:\_datefac\output\mineru_table_body_ingestion_321d`
- `D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm`
- `D:\_datefac\output\batch_row_text_delivery_320g`

## non_goals
Do not:
- run StructEqTable
- run Docling
- run MinerU
- run PPStructure
- run VLM
- modify `E:\mineru_lab`
- modify production pipeline
- add new alias rules
- add new unit rules
- commit `output/`

## expected_files
New sandbox-only files:
- `datefac/table_bakeoff/full_table_extraction_bakeoff.py`
- `tools/run_table_extraction_full_bakeoff_321e5.py`
- `docs/codex_tasks/321e5_full_table_extraction_bakeoff.md`

## output_contract
Write to:
- `D:\_datefac\output\table_extraction_full_bakeoff_321e5`

Required files:
- `table_extraction_full_bakeoff_321e5.xlsx`
- `table_extraction_full_bakeoff_321e5_summary.json`
- `table_extraction_full_bakeoff_321e5_report.md`
- `table_extraction_router_plan_321e5.json`

Workbook sheets:
- `summary`
- `route_scorecard`
- `route_rankings`
- `router_plan`
- `qa_checks`
- `known_limitations`

## validation
Run:

```powershell
python -m py_compile datefac/table_bakeoff/full_table_extraction_bakeoff.py
python -m py_compile tools/run_table_extraction_full_bakeoff_321e5.py
```

Then run:

```powershell
python tools/run_table_extraction_full_bakeoff_321e5.py ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --structtable-audit-dir D:\_datefac\output\structtable_output_audit_321e3 ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --docling-audit-dir D:\_datefac\output\docling_output_audit_321e1 ^
  --mineru-body-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\table_extraction_full_bakeoff_321e5
```

## commit_requirements
- start from `git status`
- do not add unrelated dirty files
- do not add `output/`
- only add 321E5 code and this task doc
- push to `origin/main`

## final_response_requirements
Report:
- pushed branch
- commit hash
- changed files
- output report path
- top overall route
- default PDF table_body route
- default image-table route
- top route rankings
- qa counts
- skipped dirty files
