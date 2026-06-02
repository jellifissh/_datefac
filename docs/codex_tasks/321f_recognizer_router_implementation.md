# 321F Recognizer Router Implementation

## task_title
Implement an executable recognizer router policy from 321E5 bakeoff results

## project
`D:\_datefac`

## current_context
- 321E5 full table extraction bakeoff exists under:
  - `D:\_datefac\output\table_extraction_full_bakeoff_321e5`
- 321C2 source-aware router revision exists under:
  - `D:\_datefac\output\source_aware_router_revision_321c2`

321F should convert bakeoff conclusions into a deterministic per-table router policy.

## goal
Create an independent recognizer router implementation that:
- reads 321E5 outputs
- reads this task and 321E5 task document
- does not run StructEqTable / Docling / MinerU / PPStructure / VLM
- does not modify `E:\mineru_lab`

Inputs should include:
- table asset
- table source
- table type
- audit signals
- mapping signals

Per-table output fields must include:
- `recommended_recognizer`
- `fallback_recognizer`
- `semantic_adjudicator_required`
- `manual_review_required`
- `risk_tags`
- `reason`

## routing_principles
- PDF `table_body` default: `MINERU_TABLE_BODY_321D`
- image-table default: `STRUCTTABLE_INTERVL2`
- `PURE_VLM` / LLM is semantic adjudicator only, not batch default extractor
- `Docling` is backup candidate
- `PPStructure` is weak legacy fallback
- acknowledge pure VLM’s stronger core mapping score in 321E5, but do not make it default because of cost / stability / reproducibility / extraction concerns

## expected_files
New sandbox-only files:
- `datefac/router/recognizer_router_321f.py`
- `tools/run_recognizer_router_321f.py`
- `docs/codex_tasks/321f_recognizer_router_implementation.md`

## output_contract
Write to:
- `D:\_datefac\output\recognizer_router_321f`

Required files:
- `recognizer_router_321f.xlsx`
- `recognizer_router_321f_summary.json`
- `recognizer_router_321f_report.md`
- `router_plan_321f.json`

Workbook sheets:
- `summary`
- `router_policy`
- `route_preview`
- `route_counts`
- `adjudicator_worklist`
- `manual_review_worklist`
- `qa_checks`
- `known_limitations`

## allowed_inputs
Primary:
- `D:\_datefac\output\table_extraction_full_bakeoff_321e5`
- `D:\_datefac\output\source_aware_router_revision_321c2`

## non_goals
Do not:
- run StructEqTable / Docling / MinerU / PPStructure / VLM
- modify `E:\mineru_lab`
- modify production pipeline
- modify override / mapping files
- modify old Stage7
- commit `output/`

## validation
Run:

```powershell
python -m py_compile datefac/router/recognizer_router_321f.py
python -m py_compile tools/run_recognizer_router_321f.py
```

Then run:

```powershell
python tools/run_recognizer_router_321f.py ^
  --bakeoff-dir D:\_datefac\output\table_extraction_full_bakeoff_321e5 ^
  --router-revision-dir D:\_datefac\output\source_aware_router_revision_321c2 ^
  --output-dir D:\_datefac\output\recognizer_router_321f
```

## commit_requirements
- start from `git status`
- do not add unrelated dirty files
- do not add `output/`
- only add 321F code and this task doc
- push to `origin/main`

## final_response_requirements
Report:
- pushed branch
- commit hash
- changed files
- output report path
- `route_total_count`
- `mineru_default_count`
- `structtable_default_count`
- `pure_vlm_adjudicator_count`
- `docling_backup_count`
- `ppstructure_fallback_count`
- `manual_review_count`
- `qa_fail_count`
- `router_decision`
