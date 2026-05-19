# NEXT CODEX TASK

## task_title
Prepare Stage 1 sandbox AI repair packet

## project
D:\_datefac

## current_status
The Stage 1 sandbox standardizer allowlist/table-prior task has completed.

Latest user-uploaded/reviewed reports:
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.xlsx
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.xlsx

Key result from 35/36:
- task_title = Add Stage 1 sandbox standardizer allowlists and table priors
- py_compile_status = PASS
- help_status = PASS
- sandbox_standardizer_status = WARN
- production_delivery_status_after = PASS / warn_count=0 / fail_count=0
- production_guard_changed_count = 0
- production 01/02/02A/06 unchanged
- factory_core.py not run
- marker/surya/vision/PaddleOCR not triggered
- model download not triggered

Per-sample result:
- S1 / H3_AP202605141822317484_1 / 三鑫医疗: WARN_SEMANTIC_GUARD, metric_rows=3, manual_review_candidate_rows=83
- S2 / H3_AP202605121822223662_1 / 冠豪高新: WARN_NO_METRICS, metric_rows=0, manual_review_candidate_rows=0
- S3 / H3_AP202605141822318060_1 / 科锐国际: WARN_SEMANTIC_GUARD, metric_rows=40, manual_review_candidate_rows=81

Quality metrics:
- safe_promotions_count = 43
- remaining_likely_core_duplicates_count = 0
- source_row_semantic_risk_count = 94
- forbidden_source_label_count = 56
- S2 no-metric diagnosis: raw_table_count=5, year_evidence_count=5, label_fragmented_suspected=1, keyword_hit_examples=none

Interpretation:
The deterministic standardizer now has useful safety properties: hard-risk rows are demoted, duplicate likely-core groups are 0, and production files remain clean. However, S1/S3 still contain many manual candidates and S2 has year evidence but no recoverable metric labels. This is the right point to prepare an AI repair layer input packet. Do not call any AI model in this task. Build evidence packets and strict schemas only.

## goal
Create a sandbox-only AI repair input packet and schema for the Stage 1 samples.

This task must not call an LLM, API, local model, OCR, or vision backend. It only prepares structured repair packets for later AI repair MVP.

Target new helper/tool:
- D:\_datefac\tools\prepare_stage1_ai_repair_packet.py

If integrating into `run_stage1_safe_nonvision_pipeline.py` is cleaner, allowed, but prefer a separate helper to keep AI-repair preparation isolated.

Target local outputs:
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.md
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.xlsx
- D:\_datefac\output\delivery_package\37_stage1_ai_repair_input_packet.jsonl
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.md
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema_and_prompt.xlsx
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_schema.json

Optional validation output:
- D:\_datefac\output\delivery_package\38_stage1_ai_repair_packet_validation.xlsx

## absolute_hard_constraints
1. Do not run factory_core.py.
2. Do not trigger marker / surya / vision / PaddleOCR.
3. Do not download model.safetensors or any model.
4. Do not call any LLM, local model, cloud API, or AI inference endpoint.
5. Do not run OCR.
6. Do not reprocess PDFs.
7. Do not rebuild production delivery_package.
8. Do not run apply_manual_review_corrections.py.
9. Do not modify production delivery files:
   - 01_自动可信核心指标.xlsx
   - 02_人工复核指标队列.xlsx
   - 02A_人工年份修正覆盖表.xlsx
   - 06_最终核心财务指标.xlsx
10. Do not process baseline 091 as Stage 1 sample.
11. Do not commit output artifacts.
12. Worklog must be English only and UTF-8.
13. Packet text must preserve Chinese metric/company names without garbling.

## input_sources
Use existing sandbox/trial and delivery reports only:

Primary trial root:
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315

Read if present:
- D:\_datefac\output\delivery_package\35_stage1_standardizer_allowlist_prior_log.xlsx
- D:\_datefac\output\delivery_package\36_stage1_standardizer_allowlist_prior_evaluation.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\05_stage1_standardized_core_metric_trial.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\standardizer_trial\*\05_stage1_standardizer_diagnostics.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02A_研报原始表格资产.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\02_研报全量结构化数据.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\05_stage1_core_metric_candidates.xlsx
- D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315\assets\*\stage1_sandbox_asset_summary.xlsx

If Chinese filenames are difficult to glob because of encoding, locate 02A/02 files by prefix and workbook sheet names, not by exact garbled string.

## required_repair_task_types
Create AI repair packet entries for at least these task types:

1. `row_segment_repair`
   For manual_review_candidate rows where one row contains multiple metric blocks, for example:
   - 营业收入 ... 净利润 ...
   - PE ... 每股指标 ...
   - PB ... 每股收益 ...
   Input should include row_preview, source_label, table year headers, page/table/source row, and raw table context.

2. `metric_year_value_alignment`
   For rows with:
   - ambiguous_year_value_alignment
   - partial_year_value_alignment
   - no_numeric_value_after_metric_match
   Input should include detected years, row cells, table header rows, and candidate metric.

3. `semantic_guard_review`
   For rows demoted by:
   - source_row_semantic_risk
   - forbidden_source_label_for_metric
   - broad_keyword_unsafe
   These must be framed as review questions, not automatic correction requests.

4. `s2_table_level_repair`
   For S2 / 冠豪高新 where no metric rows were found but raw_table_count=5 and year_evidence_count=5.
   Include compact previews of the candidate tables from S2 and ask AI to identify whether target financial metrics exist, without inventing missing values.

## packet_selection_rules
Do not dump everything blindly. Keep packet useful and bounded.

Suggested selection:
- Include all high-value manual candidates from S1/S3 where source_page is a visually approved/core page.
- Include rows from core_metrics or full_financial_forecast table roles first.
- Include S1 page 4 business forecast rows only as lower-priority tasks.
- Include S2 table-level previews because row-level metrics are missing.
- Cap packet entries at around 80 unless more are clearly useful.
- Group similar repeated rows when possible.

Every packet entry must include:
- repair_task_id
- task_type
- sample_id
- company
- pdf_stem or asset_package
- source_page
- source_table_index
- source_row_index if available
- table_role
- standard_metric_hint if available
- detected_years
- row_cells or row_preview
- nearby_rows_context
- risk_flags
- current_route
- reason_for_ai_repair
- expected_output_schema_name
- must_not_invent_values = true
- source_trace_id

## jsonl_schema
Each JSONL line should be one repair task object.

Required top-level fields:
- repair_task_id: string
- task_type: string
- sample_id: string
- company: string
- asset_package: string
- source: object
- evidence: object
- current_rule_result: object
- ai_instruction: object
- output_schema_name: string

`source` fields:
- source_page
- source_table_index
- source_row_index
- table_role
- source_trace_id

`evidence` fields:
- detected_years
- row_cells
- row_preview
- nearby_rows_context
- table_header_context
- raw_table_preview

`current_rule_result` fields:
- standard_metric_hint
- route_recommendation
- confidence
- flags
- semantic_score
- promotion_reason

`ai_instruction` fields:
- task_goal
- allowed_actions
- forbidden_actions
- must_not_invent_values
- require_evidence
- require_json_only

## ai_output_schema
Create `38_stage1_ai_repair_schema.json` with strict schemas for later model output.

Minimum schema:
```json
{
  "repair_task_id": "string",
  "decision": "extract|manual_review|ignore|non_target",
  "repairs": [
    {
      "standard_metric": "string",
      "year": "string",
      "value": "number|string|null",
      "unit": "string|null",
      "confidence": "high|medium|low",
      "evidence": "string",
      "source_cell_or_segment": "string",
      "flags": ["string"]
    }
  ],
  "manual_review_items": [
    {
      "reason": "string",
      "evidence": "string"
    }
  ],
  "notes": "string"
}
```

Constraints in schema/prompt:
- AI must not invent values.
- AI must return JSON only.
- AI must copy numeric values from evidence only.
- AI must preserve year labels exactly unless explicitly normalizing with flag `year_normalized`.
- If table/row is ambiguous, AI must choose `manual_review`, not guess.
- AI repairs are candidates only and must not be written to production 06.

## prompt_requirements
Create `38_stage1_ai_repair_schema_and_prompt.md` with:
1. System prompt for AI repair worker.
2. User prompt template for one repair task.
3. JSON output schema.
4. Good examples:
   - safe segmented row extraction;
   - ambiguous multi-metric row routed to manual review;
   - S2 table-level no-label case routed to manual review.
5. Bad examples:
   - inventing missing year/value;
   - assigning later metric block values to earlier metric;
   - treating accounts receivable as revenue.

Do not include API keys or model vendor assumptions.

## xlsx_outputs
37 XLSX must include sheets:
- summary
- repair_tasks
- task_type_summary
- sample_summary
- high_priority_tasks
- s2_table_level_tasks
- source_trace_index

38 XLSX must include sheets:
- schema_summary
- allowed_decisions
- required_fields
- prompt_sections
- validation_rules

Optional 38 validation XLSX sheets:
- jsonl_validation
- missing_fields
- duplicate_task_ids
- sample_task_counts

## validation
Validate packet quality:
- all repair_task_id values unique;
- all JSONL lines parse as JSON;
- every task has sample_id/company/source/evidence/ai_instruction;
- no blank company for S1/S2/S3;
- no garbled Chinese text such as `????` or Unicode replacement char `�`;
- task count > 0;
- S2 has at least one table-level repair task;
- production delivery status remains PASS;
- production 01/02/02A/06 unchanged.

Run:
```bat
D:\anaconda\envs\factory_v4\python.exe -m py_compile D:\_datefac\tools\prepare_stage1_ai_repair_packet.py
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\prepare_stage1_ai_repair_packet.py ^
  --trial-run-root D:\_datefac\output\_stage1_safe_runner_trial\run_20260519_101315 ^
  --delivery-dir D:\_datefac\output\delivery_package ^
  --max-tasks 80
D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\check_delivery_state.py --json
```

If no helper is created and runner is extended instead, adjust commands but keep the same outputs and validation.

## report/worklog
The helper should also generate:
- D:\_datefac\output\delivery_package\39_stage1_ai_repair_packet_build_log.md
- D:\_datefac\output\delivery_package\39_stage1_ai_repair_packet_build_log.xlsx

39 report must include:
- task_title
- started_at / finished_at
- commands_run
- input_files_read
- output_files_generated
- task_count
- task_type_counts
- sample_task_counts
- jsonl_validation_status
- production_guard_changed_count
- safety_checks
- next_step_recommendation

Update:
- docs/codex_worklog/LATEST.md

Create:
- docs/codex_worklog/history/YYYYMMDD_HHMMSS_prepare_stage1_ai_repair_packet.md

Worklog must be English only and UTF-8.

## git_commit
Allowed to commit:
- tools/prepare_stage1_ai_repair_packet.py
- tools/run_stage1_safe_nonvision_pipeline.py only if actually modified and necessary
- docs/codex_worklog/LATEST.md
- docs/codex_worklog/history/

Do not commit:
- output/delivery_package/37_stage1_ai_repair_input_packet.md
- output/delivery_package/37_stage1_ai_repair_input_packet.xlsx
- output/delivery_package/37_stage1_ai_repair_input_packet.jsonl
- output/delivery_package/38_stage1_ai_repair_schema_and_prompt.md
- output/delivery_package/38_stage1_ai_repair_schema_and_prompt.xlsx
- output/delivery_package/38_stage1_ai_repair_schema.json
- output/delivery_package/38_stage1_ai_repair_packet_validation.xlsx
- output/delivery_package/39_stage1_ai_repair_packet_build_log.md
- output/delivery_package/39_stage1_ai_repair_packet_build_log.xlsx
- any output artifacts

Commit:
```bat
git add tools/prepare_stage1_ai_repair_packet.py docs/codex_worklog/LATEST.md docs/codex_worklog/history/
git commit -m "prepare stage1 ai repair packet"
git push origin main
```

## expected_final_response
After completion, output:
1. task_title
2. helper_path
3. py_compile_status
4. packet_build_status
5. generated_outputs
6. repair_task_count
7. task_type_counts
8. sample_task_counts
9. s2_table_level_task_count
10. jsonl_validation_status
11. production_delivery_status_after
12. production_files_unchanged
13. factory_core/vision/model_download_status
14. next_step_suggestion
15. commit sha

## safety_notes
- This task only prepares AI repair input/schema/prompt.
- Do not call AI yet.
- Do not write AI results into production delivery_package.
- Do not run factory_core.py.
- Do not trigger vision/OCR/model backends.
- Do not modify production delivery data.
