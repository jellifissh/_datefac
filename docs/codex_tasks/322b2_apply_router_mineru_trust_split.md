# 322B2 Router MinerU Trust Split Calibration

## task_title
Apply proper trust split and review diagnosis to router-driven MinerU body candidates before semantic adjudication

## project
D:\_datefac

## current_context
322B router-driven larger batch review-burden diagnosis has completed and pushed to `main`.

322B output directory:

```powershell
D:\_datefac\output\router_driven_sandbox_pipeline_322b
```

322B key results:
- newly_processed_mineru_table_count: 45
- selected_output_table_count_before_322b: 88
- selected_output_table_count_after_322b: 133
- no_available_output_count_after_322b: 83
- selected_candidate_total_count: 5972
- selected_trusted_total_count: 527
- selected_review_required_total_count: 5310
- selected_core_trusted_rate: 0.088245
- top_review_reason_counts:
  - PENDING_MINERU_BODY_TRUST_SPLIT: 4597
  - HAS_MAPPING_REVIEW_TAG: 713
- unknown_metric_unique_label_count: 363
- alias_candidate_count: 272
- semantic_adjudicator_worklist_count: 98
- manual_review_worklist_count: 103
- qa_fail_count: 0
- router_driven_sandbox_pipeline_decision: `ROUTER_DRIVEN_SANDBOX_PIPELINE_322B_READY_FOR_REVIEW_BURDEN_DECISION`

Important interpretation:
- 322B expanded router-selected coverage successfully.
- However, trusted count stayed at 527 while thousands of new candidates were marked `PENDING_MINERU_BODY_TRUST_SPLIT`.
- This means the current bottleneck is not yet true semantic ambiguity. The first bottleneck is that newly generated router-driven MinerU-body candidates have not been passed through an equivalent trust/review split used in earlier MinerU-body stages.
- Therefore do not jump directly to broad alias expansion or LLM semantic adjudication yet.
- First apply/restore the deterministic trust split, then re-run review-burden diagnosis on real review tags.

## goal
Implement 322B2 as a sandbox-only trust-split calibration for router-driven MinerU-body candidates.

322B2 should:
1. read 322B router-driven selected candidates;
2. identify candidates marked `PENDING_MINERU_BODY_TRUST_SPLIT`;
3. apply the same conservative trust/review/rejected gates used by MinerU-body 321D/322A where safe;
4. preserve all router provenance and selected output source fields;
5. recompute selected trusted/review/rejected previews;
6. regenerate review-burden diagnostics after pending split is removed or minimized;
7. output alias candidate / unit / section / semantic adjudicator worklists based on real review reasons, not pending placeholder tags;
8. decide whether the pipeline is ready for semantic adjudicator design or still needs deterministic gate fixes.

This is sandbox-only. No production integration.

## non_goals
Do not do these in 322B2:
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
- Do not perform broad alias expansion.
- Do not force trusted rate upward by weakening gates.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/pipeline/router_mineru_trust_split.py`
- `datefac/pipeline/router_review_burden_diagnostics.py`
- `tools/run_router_mineru_trust_split_322b2.py`
- `docs/codex_tasks/322b2_apply_router_mineru_trust_split.md`

Likely modified minimally if needed:
- `datefac/pipeline/router_selected_delivery_preview.py`
- `datefac/pipeline/router_driven_sandbox_pipeline.py`
- `datefac/pipeline/router_driven_sandbox_pipeline_322b.py`

Reuse existing MinerU-body candidate mapper/risk splitter where safe, but keep 322B2 as sandbox pipeline logic. Do not modify production pipeline entrypoints.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\router_driven_sandbox_pipeline_322b
D:\_datefac\output\router_driven_sandbox_pipeline_322a
D:\_datefac\output\router_sandbox_integration_321g
D:\_datefac\output\recognizer_router_321f
```

Optional comparison/reference inputs:

```powershell
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\structtable_unified_mapping_321e4b
D:\_datefac\output\docling_unified_mapping_321e2
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_router_mineru_trust_split_322b2.py ^
  --pipeline-322b-dir D:\_datefac\output\router_driven_sandbox_pipeline_322b ^
  --pipeline-322a-dir D:\_datefac\output\router_driven_sandbox_pipeline_322a ^
  --router-integration-dir D:\_datefac\output\router_sandbox_integration_321g ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --mineru-body-reference-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\router_mineru_trust_split_322b2
```

If 322B output is missing, produce blocked summary instead of crashing:
- `BLOCKED_MISSING_322B_PIPELINE_DIR`

## trust_split_requirements
For candidates with `PENDING_MINERU_BODY_TRUST_SPLIT`:

Apply conservative gates:
- trusted only if:
  - metric_code is known and not placeholder;
  - year is valid;
  - numeric value parsed;
  - unit is known or safely inferable from table/metric context;
  - provenance is complete;
  - no unresolved value conflict;
  - not out of scope;
  - not section-context ambiguous;
- review_required if:
  - unknown metric code;
  - unit unknown;
  - invalid/missing year;
  - value parse failed;
  - duplicated label requiring section context;
  - conflict requires semantic/context adjudication;
  - table schema uncertain;
- rejected only for clear noise, empty rows, non-metric rows, impossible values, or out-of-scope rows if existing policy marks them rejected.

Do not weaken existing trusted gates. The goal is to remove placeholder pending tags and reveal real reasons.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary.

### `pending_split_before_after`
- source_stage
- selected_output_source
- pending_before_count
- pending_after_count
- trusted_after_count
- review_required_after_count
- rejected_after_count
- reason

### `selected_candidate_reclassified_322b2`
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
- decision_before
- decision_after
- risk_tags_before
- risk_tags_after
- reclassification_reason
- provenance

### `trusted_preview_322b2`
### `review_required_preview_322b2`
### `rejected_preview_322b2`

### `review_burden_by_reason_322b2`
- review_reason
- candidate_count
- unique_table_count
- unique_label_count
- sample_labels
- recommended_next_action

### `unknown_metric_label_frequency_322b2`
- normalized_label
- raw_label_examples
- candidate_count
- unique_table_count
- table_title_examples
- suggested_action
- priority

Suggested actions:
- `alias_candidate_review`
- `out_of_scope_confirm`
- `semantic_adjudicator_candidate`
- `manual_review_required`

### `unit_unknown_diagnostics_322b2`
- table_asset_id
- table_title
- metric_label
- metric_code
- raw_value
- unit_context_source
- reason
- recommended_action

### `section_context_required_diagnostics_322b2`
- table_asset_id
- table_title
- duplicated_label
- section_context_hint
- affected_candidate_count
- recommended_action

### `alias_candidate_worklist_322b2`
- normalized_label
- raw_label_examples
- suggested_metric_code
- suggested_metric_family
- evidence_table_titles
- candidate_count
- priority
- safety_level
- requires_human_confirmation

### `semantic_adjudicator_worklist_322b2`
- table_asset_id
- source_report_name
- table_title
- adjudication_reason
- affected_candidate_count
- sample_labels
- sample_values
- priority

### `manual_review_worklist_322b2`
- table_asset_id
- source_report_name
- table_title
- manual_review_reason
- selected_output_source
- priority
- notes

### `qa_checks`
### `known_limitations`

## output_contract
Write to:

```powershell
D:\_datefac\output\router_mineru_trust_split_322b2
```

Required files:
1. `router_mineru_trust_split_322b2.xlsx`

Sheets:
- `summary`
- `pending_split_before_after`
- `selected_candidate_reclassified_322b2`
- `trusted_preview_322b2`
- `review_required_preview_322b2`
- `rejected_preview_322b2`
- `review_burden_by_reason_322b2`
- `unknown_metric_label_frequency_322b2`
- `unit_unknown_diagnostics_322b2`
- `section_context_required_diagnostics_322b2`
- `alias_candidate_worklist_322b2`
- `semantic_adjudicator_worklist_322b2`
- `manual_review_worklist_322b2`
- `qa_checks`
- `known_limitations`

2. `router_mineru_trust_split_322b2_summary.json`

3. `router_mineru_trust_split_322b2_report.md`

Optional:
- `selected_candidate_reclassified_322b2.jsonl`
- `alias_candidate_worklist_322b2.jsonl`
- `semantic_adjudicator_worklist_322b2.jsonl`

## summary_metrics
Include:
- input_candidate_count
- pending_split_before_count
- pending_split_after_count
- reclassified_candidate_count
- trusted_total_before_322b2
- trusted_total_after_322b2
- review_required_total_before_322b2
- review_required_total_after_322b2
- rejected_total_after_322b2
- selected_core_trusted_rate_before_322b2
- selected_core_trusted_rate_after_322b2
- selected_all_trusted_rate_after_322b2
- unknown_metric_candidate_count
- unit_unknown_candidate_count
- value_conflict_candidate_count
- section_context_required_candidate_count
- alias_candidate_count
- semantic_adjudicator_worklist_count
- manual_review_worklist_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- router_mineru_trust_split_decision

Decision rule:
- If qa_fail_count > 0:
  `ROUTER_MINERU_TRUST_SPLIT_BLOCKED_BY_QA_FAILURE`
- If pending_split_after_count == 0 and reclassified_candidate_count > 0:
  `ROUTER_MINERU_TRUST_SPLIT_READY_FOR_SEMANTIC_ADJUDICATOR_DESIGN`
- If pending_split_after_count < pending_split_before_count * 0.1:
  `ROUTER_MINERU_TRUST_SPLIT_PARTIAL_READY_FOR_REVIEW_ACTIONS`
- Otherwise:
  `ROUTER_MINERU_TRUST_SPLIT_NEEDS_GATE_FIXES`

## qa_checks
Required checks:
- 322B pipeline dir exists;
- no E-drive files modified;
- no recognizer command executed;
- no production files modified;
- every candidate has table_asset_id and source_stage;
- trusted candidates have valid year, known metric code, parsed numeric value, and provenance;
- no trusted candidate retains pending split tag;
- pending split count reduced;
- output files written successfully.

Warnings, not failures:
- many candidates remain review_required after real split;
- unknown metric labels remain high;
- unit unknown remains high;
- semantic adjudicator is still needed.

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
12. Do not perform broad alias expansion.
13. Do not commit `output/` artifacts.
14. Do not commit anything under `E:\mineru_lab`.
15. Do not commit unrelated 320G2 leftovers or temp scripts.
16. Preserve Chinese text as UTF-8.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/pipeline/router_mineru_trust_split.py
python -m py_compile datefac/pipeline/router_review_burden_diagnostics.py
python -m py_compile tools/run_router_mineru_trust_split_322b2.py
```

Then run:

```powershell
python tools/run_router_mineru_trust_split_322b2.py ^
  --pipeline-322b-dir D:\_datefac\output\router_driven_sandbox_pipeline_322b ^
  --pipeline-322a-dir D:\_datefac\output\router_driven_sandbox_pipeline_322a ^
  --router-integration-dir D:\_datefac\output\router_sandbox_integration_321g ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --mineru-body-reference-dir D:\_datefac\output\mineru_table_body_ingestion_321d ^
  --structtable-mapping-dir D:\_datefac\output\structtable_unified_mapping_321e4b ^
  --docling-mapping-dir D:\_datefac\output\docling_unified_mapping_321e2 ^
  --pure-vlm-calibration-dir D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\router_mineru_trust_split_322b2
```

PowerShell one-line form is acceptable. Report exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 322B2 code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Apply router MinerU trust split`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_candidate_count
- pending_split_before_count
- pending_split_after_count
- reclassified_candidate_count
- trusted_total_before_322b2
- trusted_total_after_322b2
- review_required_total_before_322b2
- review_required_total_after_322b2
- rejected_total_after_322b2
- selected_core_trusted_rate_before_322b2
- selected_core_trusted_rate_after_322b2
- selected_all_trusted_rate_after_322b2
- unknown_metric_candidate_count
- unit_unknown_candidate_count
- value_conflict_candidate_count
- section_context_required_candidate_count
- alias_candidate_count
- semantic_adjudicator_worklist_count
- manual_review_worklist_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- router_mineru_trust_split_decision
- top review reasons after split
- skipped/untracked files
