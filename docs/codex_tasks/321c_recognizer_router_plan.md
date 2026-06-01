# 321C Recognizer Router Plan

## task_title
Design and benchmark a DateFac table recognizer router using MinerU assets, VLM mapping results, and PPStructure fallback evidence

## project
D:\_datefac

## current_context
321B completed the VLM mapping benchmark and pushed to `main`.

Latest 321B result:
- pushed branch: main
- commit hash: 83591d7
- input: `E:\mineru_lab\vlm_table_outputs_321a_rerun_strict`
- output: `D:\_datefac\output\vlm_mapping_benchmark_321b`
- vlm_folder_count: 11
- parsed_json_count: 11
- table_ready_count: 9
- mapped_table_count: 11
- table_with_candidates_count: 11
- table_with_trusted_count: 9
- total_candidate_count: 1011
- trusted_total_count: 621
- review_required_total_count: 390
- rejected_total_count: 0
- trusted_rate: 0.6142433234421365
- unit_unknown_count: 10
- year_inferred_count: 0
- conflict_count: 43
- provenance_complete_rate: 1.0
- qa_pass_count: 8
- qa_warn_count: 0
- qa_fail_count: 0
- ppstructure_comparison_available: true
- vlm_benchmark_decision: VLM_MAPPING_READY_FOR_321C_RECOGNIZER_ROUTER_PLAN

Top VLM risk tags:
- TABLE_NOT_READY_321A: 267
- VALUE_CONFLICT: 217
- UNKNOWN_METRIC_CODE: 158
- SCHEMA_REVIEW_REQUIRED: 73
- VLM_ROW_UNCERTAIN: 38

Relevant earlier PPStructure batch result from 320G:
- batch_table_count: 10
- parsed_table_count: 10
- table_with_candidates_count: 8
- table_with_trusted_count: 1
- trusted_total_count: 10
- review_required_total_count: 129
- trusted_rate: 0.07194244604316546
- provenance_complete_rate: 1.0
- batch_delivery_decision: BATCH_ROW_TEXT_DELIVERY_PARTIAL_NEEDS_CALIBRATION

Engineering interpretation:
- VLM strict JSON route is now clearly stronger than PPStructure row-text for complex financial table recognition on the current sample set.
- PPStructure row-text should not remain the primary route for core financial tables.
- MinerU remains the primary table/layout asset parser and table image cropper.
- VLM should become the preferred recognizer for core financial/valuation/statement tables when quality gates pass.
- PPStructure can remain a low-cost fallback or diagnostic route.
- Do not proceed directly to production integration. 321C should design and validate a recognizer router policy and sandbox planning layer first.

Important worktree warning:
Previous messages reported unrelated 320G2 experimental modified/untracked files. 321C must not commit those files. If they are present in the local workspace, leave them untouched or ask the user to stash them before implementation.

## goal
Implement 321C as a sandbox-only recognizer router planning and benchmark layer.

It should consume existing benchmark outputs and produce:
1. a table recognizer routing policy;
2. a per-table router decision preview;
3. a VLM-vs-PPStructure comparison summary;
4. a recommended pipeline plan for 321D/322 integration;
5. an offline manual-VLM workflow manifest until stable VLM API access exists.

This stage should answer:
- Which table types should go to VLM first?
- Which table types can use cheaper PPStructure or MinerU markdown outputs?
- Which tables should be rejected/skipped or sent to manual review?
- What quality gates must pass before VLM outputs enter MetricCandidate mapping?
- What is the next safe integration step?

## non_goals
Do not do these in 321C:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call AI/VLM/cloud/network APIs.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.
- Do not implement live VLM API integration yet, because the previous bare API test returned repeated 503 and is not stable.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/321c_recognizer_router_plan.md`
- `datefac/router/__init__.py`
- `datefac/router/table_recognizer_router.py`
- `datefac/router/router_policy.py`
- `datefac/router/router_benchmark.py`
- `datefac/router/manual_vlm_manifest.py`
- `tools/run_recognizer_router_plan_321c.py`

Potentially modify only if needed:
- `datefac/vlm/vlm_mapping_benchmark.py`
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/parser/mineru_output_reader.py`

Keep router logic separate from VLM and PPStructure implementations.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\vlm_mapping_benchmark_321b
D:\_datefac\output\vlm_output_quality_321a_rerun_strict
D:\_datefac\output\batch_row_text_delivery_320g
D:\_datefac\output\mineru_benchmark_320b2
E:\mineru_lab\output_new
E:\mineru_lab\vlm_table_outputs_321a_rerun_strict
```

CLI:

```powershell
python tools/run_recognizer_router_plan_321c.py ^
  --vlm-benchmark-dir D:\_datefac\output\vlm_mapping_benchmark_321b ^
  --vlm-quality-dir D:\_datefac\output\vlm_output_quality_321a_rerun_strict ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --mineru-benchmark-dir D:\_datefac\output\mineru_benchmark_320b2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321a_rerun_strict ^
  --output-dir D:\_datefac\output\recognizer_router_plan_321c
```

If optional inputs are missing, continue with warnings and produce a partial plan.
If `--vlm-benchmark-dir` is missing, produce blocked report:
- `BLOCKED_MISSING_321B_VLM_BENCHMARK`

Do not crash.

## router_policy_requirements
Define a deterministic router policy.

Recognizer routes:
- `VLM_PRIMARY`
- `MINERU_MARKDOWN_DIRECT`
- `PPSTRUCTURE_FALLBACK`
- `MANUAL_REVIEW_REQUIRED`
- `SKIP_NON_CORE_TABLE`
- `UNSUPPORTED_TABLE_TYPE`

Recommended default policy:

### Route to VLM_PRIMARY
For table roles/types likely to contain core financial metrics:
- cash flow statement / 现金流量表
- income statement / 利润表
- balance sheet / 资产负债表
- key financial and valuation table / 关键财务与估值指标
- financial forecast table / 盈利预测和财务指标
- segment table only if 321A quality passes or schema has been relaxed later

Conditions:
- table image path exists;
- table is core or high-value;
- historical VLM benchmark supports the family;
- expected candidate value is high enough to justify cost.

### Route to MINERU_MARKDOWN_DIRECT
For tables where MinerU markdown/content JSON already gives clean text rows or simple tables, if:
- image table is simple;
- no need for VLM visual reconstruction;
- markdown has usable row/column structure.

### Route to PPSTRUCTURE_FALLBACK
Use only when:
- VLM output is missing;
- VLM API/manual result unavailable;
- table is lower-value but still potentially useful;
- cost saving matters;
- row-text extractor has known support for this family.

### Route to MANUAL_REVIEW_REQUIRED
Use when:
- VLM JSON failed 321A quality gate;
- label corruption exists;
- table schema is invalid but potentially valuable;
- conflict rate is high;
- no reliable recognizer output exists.

### Route to SKIP_NON_CORE_TABLE
For:
- rating standard explanation tables;
- author/contact tables;
- disclaimers;
- small metadata tables;
- tables with no target financial metrics.

### Route to UNSUPPORTED_TABLE_TYPE
For:
- hierarchical/segment/multi-panel tables not yet supported by mapping schema;
- tables with natural missing-column rows unless later schema support is added.

## routing_features
For each MinerU table asset / benchmark table, compute or preserve:
- source_report_name
- report_dir
- table_asset_id
- table_role_guess
- table_type if known
- page_idx
- bbox
- image_path
- image_exists
- caption
- nearby_text_preview
- mineru_asset_available
- ppstructure_output_available
- vlm_output_available
- vlm_quality_decision
- vlm_candidate_count
- vlm_trusted_count
- ppstructure_candidate_count
- ppstructure_trusted_count
- estimated_value_score
- estimated_cost_class
- recommended_route
- route_reason
- blocker_reason

## scoring_rules
Create simple deterministic scores:

### value_score
High value if table likely contains:
- EPS / ROE / PE / PB / EV_EBITDA
- revenue / net profit / margin / growth
- cash flow statement rows
- income statement rows
- balance sheet rows

### cost_class
- `LOW`: MinerU markdown direct / already clean text
- `MEDIUM`: PPStructure row-text
- `HIGH`: VLM
- `MANUAL`: human review

### confidence_score
Use evidence:
- 321A quality pass
- 321B trusted rate by table/family
- provenance completeness
- conflict count
- missing unit/year count

## output_contract
Write to:

```powershell
D:\_datefac\output\recognizer_router_plan_321c
```

Required files:

1. `recognizer_router_plan_321c.xlsx`

Sheets:
- `summary`
- `router_policy`
- `table_route_preview`
- `route_counts`
- `vlm_vs_ppstructure_comparison`
- `core_table_worklist`
- `manual_vlm_manifest`
- `ppstructure_fallback_worklist`
- `manual_review_worklist`
- `skip_non_core_tables`
- `unsupported_tables`
- `quality_gate_requirements`
- `cost_value_summary`
- `pipeline_integration_plan`
- `known_limitations`
- `qa_checks`

2. `recognizer_router_plan_321c_summary.json`

3. `recognizer_router_plan_321c_report.md`

4. `manual_vlm_manifest_321c.jsonl`

5. `recognizer_router_policy_321c.json`

## manual_vlm_manifest
Because live VLM API is not yet stable, generate an offline/manual VLM manifest.

Each row:
- manifest_id
- source_report_name
- table_asset_id
- image_path
- table_role_guess
- recommended_prompt_version
- recommended_output_dir
- expected_output_files
- priority
- reason_selected

Recommended output layout:

```text
E:\mineru_lab\vlm_table_outputs_router_321c\<manifest_id>\
  table_meta.json
  raw_response.txt
  vlm_output.json
```

## pipeline_integration_plan
Generate a staged plan for the next tasks:

Recommended next stage after 321C:
- 321D: implement VLM recognizer ingestion adapter using router-selected manual VLM outputs, still sandbox-only;
- later: 322A live VLM API adapter only after stable API access is available;
- later: 322B production-safe feature flag integration.

Do not suggest direct production apply.

## summary_metrics
Include:
- total_table_asset_count
- routable_table_count
- vlm_primary_count
- mineru_markdown_direct_count
- ppstructure_fallback_count
- manual_review_required_count
- skip_non_core_count
- unsupported_table_count
- vlm_benchmark_trusted_rate
- ppstructure_benchmark_trusted_rate
- vlm_advantage_score
- manual_vlm_manifest_count
- router_qa_pass_count
- router_qa_warn_count
- router_qa_fail_count
- router_decision

Decision rule:
- If router_qa_fail_count > 0:
  `ROUTER_PLAN_BLOCKED_BY_QA_FAILURE`
- If VLM trusted rate is at least 3x PPStructure trusted rate, VLM benchmark has qa_fail_count == 0, and manual_vlm_manifest_count > 0:
  `ROUTER_PLAN_READY_FOR_321D_MANUAL_VLM_INGESTION`
- If VLM is better but router coverage is weak:
  `ROUTER_PLAN_PARTIAL_NEEDS_MORE_VLM_SAMPLES`
- Otherwise:
  `ROUTER_PLAN_NOT_READY`

## qa_checks
Required checks:
- 321B VLM benchmark exists and decision is ready/partial;
- no production files modified;
- router policy JSON valid;
- every route preview row has a route reason;
- VLM primary route only assigned to image-existing tables;
- unsupported segment tables are not silently routed to trusted mapping;
- manual VLM manifest output paths are outside git-tracked output;
- Chinese text preserved.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call AI/VLM/cloud/network APIs.
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
10. Do not commit unrelated 320G2 experimental files.
11. Preserve Chinese text as UTF-8.

## validation
Run:

```powershell
python -m py_compile datefac/router/table_recognizer_router.py
python -m py_compile datefac/router/router_policy.py
python -m py_compile datefac/router/router_benchmark.py
python -m py_compile datefac/router/manual_vlm_manifest.py
python -m py_compile tools/run_recognizer_router_plan_321c.py
```

Then run:

```powershell
python tools/run_recognizer_router_plan_321c.py ^
  --vlm-benchmark-dir D:\_datefac\output\vlm_mapping_benchmark_321b ^
  --vlm-quality-dir D:\_datefac\output\vlm_output_quality_321a_rerun_strict ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --mineru-benchmark-dir D:\_datefac\output\mineru_benchmark_320b2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321a_rerun_strict ^
  --output-dir D:\_datefac\output\recognizer_router_plan_321c
```

If optional directories are missing, produce partial output and warnings.

## commit_requirements
Before implementation, run:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them. If the workspace is too dirty, ask the user to stash unrelated 320G2 files before continuing.

After implementation:
1. `git status`
2. only add 321C code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated files such as:
   - `datefac/benchmark/batch_row_text_delivery_benchmark.py` if it only contains 320G2 work
   - `datefac/extraction/row_text_metric_extractor.py` if it only contains 320G2 work
   - `datefac/pipeline/batch_ppstructure_row_text_pipeline.py` if it only contains 320G2 work
   - `tools/run_batch_ppstructure_outputs_320g.py` if it only contains 320G2 work
   - `datefac/pipeline/batch_conflict_diagnostics.py`
   - `datefac/pipeline/table_context_detector.py`
   - `datefac/pipeline/table_type_calibration.py`
   - `fix_307e_reviewed_at.py`
   - `temp_321a_strict_rerun.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Plan recognizer router for VLM and PPStructure`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- total_table_asset_count
- routable_table_count
- vlm_primary_count
- mineru_markdown_direct_count
- ppstructure_fallback_count
- manual_review_required_count
- skip_non_core_count
- unsupported_table_count
- vlm_benchmark_trusted_rate
- ppstructure_benchmark_trusted_rate
- vlm_advantage_score
- manual_vlm_manifest_count
- router_qa_pass_count
- router_qa_warn_count
- router_qa_fail_count
- router_decision
- skipped/untracked files
