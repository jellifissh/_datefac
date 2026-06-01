# 321C2 Source-aware Router Revision

## task_title
Revise DateFac recognizer router using pure VLM calibration and source provenance

## project
D:\_datefac

## current_context
321B2 pure-VLM mapping calibration has completed.

Pure VLM sample root:

```powershell
E:\mineru_lab\vlm_table_outputs_321d_pure_vlm
```

Pure VLM 321B2 output:

```powershell
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
```

321B2 result:
- calibrated_total_candidate_count: 815
- calibrated_trusted_total_count: 274
- calibrated_review_required_total_count: 541
- calibrated_trusted_rate: 0.3361963190184049
- table_with_trusted_count: 5
- unknown_metric_code_count: 292
- unreadable_label_count: 0
- unit_unknown_count: 231
- invalid_year_count: 0
- table_not_ready_candidate_count: 145
- table_level_review_count: 1
- true_value_conflict_count: 37
- alias_added_count: 14
- unit_propagated_count: 20
- qa_pass_count: 10
- qa_warn_count: 0
- qa_fail_count: 0
- calibration_decision: PURE_VLM_CALIBRATION_PARTIAL_NEEDS_MORE_PROMPT_OR_ALIAS_WORK

Earlier 321C router result routed many core tables to `VLM_PRIMARY`, but later investigation showed one 321D sample generation run used MinerU table_body/table_caption rather than pure image recognition. This means the router needs source-aware routing and benchmark separation.

Important distinction:
- Pure image-only VLM is usable but not strong enough yet to be the unconditional primary route.
- MinerU table_body/table_caption-assisted structuring may be cheaper and more reliable when MinerU already captured a clean table body.
- PPStructure remains a weak fallback/diagnostic route.
- The router must not mix pure VLM and MinerU-assisted outputs under one `VLM_PRIMARY` label.

## goal
Implement 321C2 as a sandbox-only source-aware router revision.

It should:
1. add explicit source route types for `MINERU_TABLE_BODY_STRUCTURING` and `PURE_VLM_IMAGE_ONLY`;
2. revise router policy using 321B2 pure-VLM calibration evidence;
3. audit existing VLM/manual outputs for `recognition_source` and contamination risk;
4. compare pure VLM, MinerU-assisted structuring, and PPStructure at a high level;
5. generate an updated route preview and integration plan;
6. decide whether to proceed to 321D ingestion, and if yes, which source type should be ingested first.

This is not production integration.

## non_goals
Do not do these in 321C2:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call VLM/API/cloud/network.
- Do not use MinerU table_body to repair pure VLM outputs.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Likely modified:
- `datefac/router/router_policy.py`
- `datefac/router/table_recognizer_router.py`
- `datefac/router/router_benchmark.py`
- `datefac/router/manual_vlm_manifest.py`
- `tools/run_recognizer_router_plan_321c.py`

Suggested new files if cleaner:
- `datefac/router/source_provenance_audit.py`
- `datefac/router/source_aware_router_revision.py`
- `tools/run_source_aware_router_revision_321c2.py`
- `docs/codex_tasks/321c2_source_aware_router_revision.md`

Keep this inside router/VLM planning layers. Do not touch PPStructure pipeline or 320G2 experimental files.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\vlm_mapping_benchmark_321d_pure_vlm
D:\_datefac\output\vlm_output_quality_321d_pure_vlm
D:\_datefac\output\recognizer_router_plan_321c
D:\_datefac\output\batch_row_text_delivery_320g
D:\_datefac\output\mineru_benchmark_320b2
E:\mineru_lab\vlm_table_outputs_321d_pure_vlm
E:\mineru_lab\vlm_table_outputs_321d_sample
E:\mineru_lab\output_new
```

CLI:

```powershell
python tools/run_source_aware_router_revision_321c2.py ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --pure-vlm-output-root E:\mineru_lab\vlm_table_outputs_321d_pure_vlm ^
  --mineru-assisted-output-root E:\mineru_lab\vlm_table_outputs_321d_sample ^
  --previous-router-dir D:\_datefac\output\recognizer_router_plan_321c ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --mineru-benchmark-dir D:\_datefac\output\mineru_benchmark_320b2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --output-dir D:\_datefac\output\source_aware_router_revision_321c2
```

If optional inputs are missing, continue with warnings and produce partial output.
If pure-VLM calibration dir is missing, produce blocked output:
- `BLOCKED_MISSING_321B2_PURE_VLM_CALIBRATION`

## route_types
Support these route types:
- `MINERU_TABLE_BODY_STRUCTURING`
- `PURE_VLM_IMAGE_ONLY`
- `VLM_API_LATER`
- `MINERU_MARKDOWN_DIRECT`
- `PPSTRUCTURE_FALLBACK`
- `MANUAL_REVIEW_REQUIRED`
- `SKIP_NON_CORE_TABLE`
- `UNSUPPORTED_TABLE_TYPE`

## policy_revision_requirements
Default revised policy:

### Prefer MINERU_TABLE_BODY_STRUCTURING when
- MinerU output has a clean `table_body`, html table, markdown table, or clearly recoverable row/column text;
- Chinese labels are preserved;
- table title/unit/year context is present or recoverable;
- table is a core financial table.

This route is cheaper than pure VLM and should be tested before expensive VLM.

### Use PURE_VLM_IMAGE_ONLY when
- MinerU table_body/markdown is missing, incomplete, scrambled, or loses row/column structure;
- table image exists;
- table is core/high-value;
- pure VLM quality gate passes;
- expected value justifies cost.

Given 321B2 result, pure VLM should be considered promising but still calibration-needed, not unconditional primary.

### Use PPSTRUCTURE_FALLBACK when
- VLM output unavailable;
- MinerU table body unavailable;
- table is lower-value but row text may still help;
- cost must be minimized.

### Use MANUAL_REVIEW_REQUIRED when
- pure VLM output has table-not-ready issues;
- unknown metric/units/conflicts are high;
- table is core but no reliable recognizer output exists.

### Use SKIP_NON_CORE_TABLE when
- rating standard explanation, author tables, disclaimers, metadata, charts without target metrics.

### Use UNSUPPORTED_TABLE_TYPE when
- segment/hierarchical/multi-panel table still lacks supported schema.

## provenance_audit_requirements
Audit each output folder if present.

For `E:\mineru_lab\vlm_table_outputs_321d_pure_vlm`:
- assert `table_meta.json.recognition_source == PURE_VLM_IMAGE_ONLY`;
- assert `is_pure_vlm == true` if present;
- flag if table_meta mentions MinerU table_body/table_caption.

For `E:\mineru_lab\vlm_table_outputs_321d_sample`:
- if table_meta indicates pure VLM but generation notes show MinerU table_body usage, flag as `SOURCE_CONTAMINATION_RISK`;
- recommend relabeling to `MINERU_TABLE_BODY_ASSISTED` / `MINERU_TABLE_BODY_STRUCTURING` rather than pure VLM.

Do not modify E-drive files. Only report/audit.

## comparison_requirements
Produce high-level comparison across available routes:

Routes:
- pure VLM 321B2 calibrated result
- PPStructure 320G result
- previous 321B strict VLM result if available
- MinerU-assisted 321D sample if output exists and can be quality-gated/mapped without calling models

Metrics:
- candidate count
- trusted count
- trusted rate
- review required count
- unit unknown count
- unknown metric count
- conflict count
- QA pass/fail
- provenance/source confidence

Explicitly mark benchmark limitations:
- pure VLM and MinerU-assisted samples may not be apples-to-apples;
- manual generation can bias results;
- current live VLM API is not stable due repeated 503 in earlier tests.

## output_contract
Write to:

```powershell
D:\_datefac\output\source_aware_router_revision_321c2
```

Required files:

1. `source_aware_router_revision_321c2.xlsx`

Sheets:
- `summary`
- `revised_router_policy`
- `source_provenance_audit`
- `route_comparison_summary`
- `table_route_preview_revised`
- `mineru_table_body_worklist`
- `pure_vlm_worklist`
- `ppstructure_fallback_worklist`
- `manual_review_worklist`
- `unsupported_tables`
- `integration_plan`
- `known_limitations`
- `qa_checks`

2. `source_aware_router_revision_321c2_summary.json`

3. `source_aware_router_revision_321c2_report.md`

4. `recognizer_router_policy_321c2.json`

## summary_metrics
Include:
- pure_vlm_calibrated_trusted_rate
- pure_vlm_table_with_trusted_count
- pure_vlm_unit_unknown_count
- pure_vlm_unknown_metric_count
- pure_vlm_calibration_decision
- ppstructure_trusted_rate
- previous_router_vlm_primary_count
- revised_mineru_table_body_structuring_count
- revised_pure_vlm_image_only_count
- revised_ppstructure_fallback_count
- revised_manual_review_required_count
- revised_skip_non_core_count
- revised_unsupported_count
- source_audit_folder_count
- pure_vlm_source_verified_count
- source_contamination_risk_count
- router_qa_pass_count
- router_qa_warn_count
- router_qa_fail_count
- router_revision_decision

Decision rule:
- If router_qa_fail_count > 0:
  `SOURCE_AWARE_ROUTER_BLOCKED_BY_QA_FAILURE`
- If pure VLM is partial but MinerU-table-body route is available for many core tables:
  `SOURCE_AWARE_ROUTER_READY_FOR_321D_MINERU_BODY_INGESTION_FIRST`
- If pure VLM calibrated trusted rate >= 0.45 and source audit passes:
  `SOURCE_AWARE_ROUTER_READY_FOR_321D_PURE_VLM_INGESTION`
- If both routes need more samples:
  `SOURCE_AWARE_ROUTER_PARTIAL_NEEDS_MORE_ROUTE_BENCHMARKS`
- Otherwise:
  `SOURCE_AWARE_ROUTER_NOT_READY`

## qa_checks
Required checks:
- pure VLM calibration dir exists;
- pure VLM source meta is not contaminated;
- no production files modified;
- router policy JSON valid;
- every revised route has reason;
- pure VLM route only assigned to tables with image path;
- MinerU table body route is not mislabeled as pure VLM;
- unsupported tables are not silently trusted;
- Chinese text preserved.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call VLM/API/cloud/network.
4. Do not use MinerU table_body to repair pure VLM outputs.
5. Do not modify E-drive input/output folders.
6. Do not modify production delivery files.
7. Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
8. Do not modify `data/mapping/formal_scope_rules.json`.
9. Do not run `factory_core.py`.
10. Do not rewrite old Stage7 pipeline.
11. Do not commit `output/` artifacts.
12. Do not commit anything under `E:\mineru_lab`.
13. Do not commit unrelated 320G2 experimental files or temp scripts.
14. Preserve Chinese text as UTF-8.

## validation
Run compile checks for all new/modified router files, for example:

```powershell
python -m py_compile datefac/router/source_provenance_audit.py
python -m py_compile datefac/router/source_aware_router_revision.py
python -m py_compile tools/run_source_aware_router_revision_321c2.py
```

Then run:

```powershell
python tools/run_source_aware_router_revision_321c2.py ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --pure-vlm-output-root E:\mineru_lab\vlm_table_outputs_321d_pure_vlm ^
  --mineru-assisted-output-root E:\mineru_lab\vlm_table_outputs_321d_sample ^
  --previous-router-dir D:\_datefac\output\recognizer_router_plan_321c ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --mineru-benchmark-dir D:\_datefac\output\mineru_benchmark_320b2 ^
  --mineru-output-root E:\mineru_lab\output_new ^
  --output-dir D:\_datefac\output\source_aware_router_revision_321c2
```

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 321C2 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Revise recognizer router with source-aware policy`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- pure_vlm_calibrated_trusted_rate
- pure_vlm_table_with_trusted_count
- pure_vlm_unit_unknown_count
- pure_vlm_unknown_metric_count
- pure_vlm_calibration_decision
- ppstructure_trusted_rate
- previous_router_vlm_primary_count
- revised_mineru_table_body_structuring_count
- revised_pure_vlm_image_only_count
- revised_ppstructure_fallback_count
- revised_manual_review_required_count
- revised_skip_non_core_count
- revised_unsupported_count
- source_audit_folder_count
- pure_vlm_source_verified_count
- source_contamination_risk_count
- router_qa_pass_count
- router_qa_warn_count
- router_qa_fail_count
- router_revision_decision
- skipped/untracked files
