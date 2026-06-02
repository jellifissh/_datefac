# 322C Semantic Adjudicator Design

## task_title
Design sandbox-only LLM semantic adjudicator input packs, schemas, and decision gates after router MinerU trust split

## project
D:\_datefac

## current_context
322B2 router MinerU trust split calibration has completed and pushed to `main`.

322B2 output directory:

```powershell
D:\_datefac\output\router_mineru_trust_split_322b2
```

322B2 key results:
- input_candidate_count: 5972
- pending_split_before_count: 4597
- pending_split_after_count: 0
- reclassified_candidate_count: 4597
- trusted_total_before_322b2: 527
- trusted_total_after_322b2: 2479
- review_required_total_before_322b2: 5310
- review_required_total_after_322b2: 3358
- rejected_total_after_322b2: 135
- selected_core_trusted_rate_before_322b2: 0.088245
- selected_core_trusted_rate_after_322b2: 0.415104
- selected_all_trusted_rate_after_322b2: 0.415104
- unknown_metric_candidate_count: 3184
- unit_unknown_candidate_count: 491
- value_conflict_candidate_count: 0
- section_context_required_candidate_count: 0
- alias_candidate_count: 271
- semantic_adjudicator_worklist_count: 85
- manual_review_worklist_count: 58
- qa_pass_count: 9
- qa_warn_count: 4
- qa_fail_count: 0
- router_mineru_trust_split_decision: `ROUTER_MINERU_TRUST_SPLIT_READY_FOR_SEMANTIC_ADJUDICATOR_DESIGN`

Top review reasons after split:
- UNKNOWN_METRIC_CODE: 2492
- HAS_MAPPING_REVIEW_TAG: 713
- INVALID_OR_MISSING_YEAR: 148
- VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN: 5

Important interpretation:
- The pending placeholder bottleneck is solved.
- The selected core trusted rate recovered from 0.088245 to 0.415104.
- The remaining bottleneck is now real review burden, mostly unknown metric labels and mapping review tags.
- Do not go straight into broad alias expansion.
- The next step is to design a controlled semantic adjudicator input pack and output schema.
- 322C should not call any LLM/API yet by default. It should prepare deterministic prompt packs, JSON schemas, guardrails, and evaluation worklists for a later 322D execution.

## goal
Implement 322C as a sandbox-only semantic adjudicator design stage.

322C should:
1. read 322B2 review worklists and diagnostics;
2. classify review cases into semantic adjudication categories;
3. build deduplicated LLM input packs for high-value unknown labels, ambiguous mapping review tags, unit context issues, and out-of-scope/core classification;
4. define strict JSON output schemas for LLM adjudication;
5. define deterministic post-LLM acceptance gates;
6. generate prompt templates and sample batches but do not call any LLM/API;
7. estimate expected review burden reduction if adjudicator is applied;
8. output a clear decision on whether the project is ready for 322D limited LLM adjudicator execution.

This is design and packaging only. No external model call.

## non_goals
Do not do these in 322C:
- Do not call OpenAI / VLM / local model / cloud API.
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PaddleOCR/PPStructure.
- Do not modify `E:\mineru_lab`.
- Do not modify production delivery files.
- Do not apply anything into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not perform broad alias expansion.
- Do not auto-trust LLM decisions.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/semantic/__init__.py`
- `datefac/semantic/adjudicator_schema.py`
- `datefac/semantic/adjudicator_pack_builder.py`
- `datefac/semantic/adjudicator_prompt_templates.py`
- `datefac/semantic/adjudicator_readiness.py`
- `tools/run_semantic_adjudicator_design_322c.py`
- `docs/codex_tasks/322c_semantic_adjudicator_design.md`

Keep all 322C logic separate from production mapping and delivery. Do not modify production pipeline entrypoints.

## input_contract
Primary input:

```powershell
D:\_datefac\output\router_mineru_trust_split_322b2
```

Optional reference inputs:

```powershell
D:\_datefac\output\router_driven_sandbox_pipeline_322b
D:\_datefac\output\router_driven_sandbox_pipeline_322a
D:\_datefac\output\router_sandbox_integration_321g
D:\_datefac\output\recognizer_router_321f
D:\_datefac\output\mineru_table_body_ingestion_321d
D:\_datefac\output\structtable_unified_mapping_321e4b
D:\_datefac\output\docling_unified_mapping_321e2
D:\_datefac\output\vlm_mapping_calibration_321b2_pure_vlm
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_semantic_adjudicator_design_322c.py ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --output-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --max-label-pack 120 ^
  --max-case-pack 120
```

If 322B2 output is missing, produce blocked summary instead of crashing:
- `BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR`

## adjudication_categories
Classify review cases into categories:

1. `UNKNOWN_METRIC_ALIAS_CANDIDATE`
   - raw label looks like a possible financial metric but lacks metric_code.

2. `OUT_OF_SCOPE_OR_CORE_CLASSIFICATION`
   - row may be non-core balance sheet detail / segment detail / metadata.

3. `UNIT_CONTEXT_INFERENCE`
   - unit is missing but table title/header/context may imply it.

4. `MAPPING_REVIEW_TAG_EXPLANATION`
   - candidate has mapping review tag and needs reason normalization.

5. `INVALID_YEAR_OR_SCHEMA_REVIEW`
   - year/header issue likely deterministic, not ideal for LLM trust.

6. `VALUE_PARSE_OR_SCHEMA_UNCERTAIN`
   - value parse or schema uncertainty; generally manual or deterministic repair.

322C should prioritize categories 1, 2, and 3 for later LLM adjudication.

## llm_input_pack_requirements
Create two main input pack types.

### A. Label-level pack
One row per deduplicated normalized label.

Fields:
- `label_case_id`
- `normalized_label`
- `raw_label_examples`
- `candidate_count`
- `unique_table_count`
- `table_title_examples`
- `source_report_examples`
- `value_examples`
- `year_examples`
- `unit_context_examples`
- `current_risk_tags`
- `candidate_category`
- `allowed_metric_codes_sample`
- `allowed_actions`

Allowed actions:
- `map_to_existing_metric_code`
- `classify_out_of_scope`
- `requires_table_context`
- `requires_manual_review`
- `reject_noise`

### B. Candidate-level pack
One row per high-priority review case.

Fields:
- `case_id`
- `table_asset_id`
- `source_report_name`
- `table_title`
- `table_context`
- `row_label`
- `row_values`
- `year_columns`
- `unit_context`
- `current_metric_code`
- `current_risk_tags`
- `current_review_reason`
- `available_provenance`
- `allowed_actions`

## llm_output_schema
Define strict JSON schema for later LLM execution:

```json
{
  "case_id": "",
  "action": "map_to_existing_metric_code | classify_out_of_scope | requires_table_context | requires_manual_review | reject_noise",
  "metric_code": null,
  "metric_family": null,
  "confidence_label": "high | medium | low",
  "is_core_metric": false,
  "unit_inference": {
    "unit": null,
    "source": "table_title | header | row_label | unavailable",
    "confidence_label": "high | medium | low"
  },
  "reason": "",
  "evidence": [""],
  "risk_flags": []
}
```

Rules:
- metric_code must be from DateFac allowed metric codes; otherwise null.
- LLM cannot invent numeric values.
- LLM cannot override invalid year, parse failure, or missing provenance.
- LLM confidence is semantic confidence only, not final trusted confidence.

## deterministic_acceptance_gate
Define deterministic post-LLM acceptance rules:

A LLM suggestion may become trusted only if all are true:
- action is `map_to_existing_metric_code`;
- confidence_label is `high`;
- suggested metric_code is in allowed code list;
- year is valid;
- numeric value parsed;
- unit is known or accepted from high-confidence unit inference;
- provenance complete;
- no value conflict;
- no section-context ambiguity;
- no extraction risk.

Otherwise it may become:
- review_required with LLM explanation;
- out_of_scope;
- manual_review_required;
- rejected only for clear noise.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary.

### `semantic_case_inventory`
- case_id
- category
- table_asset_id
- source_report_name
- table_title
- row_label
- current_review_reason
- risk_tags
- priority
- recommended_adjudication_type

### `label_level_pack`
- label_case_id
- normalized_label
- raw_label_examples
- candidate_count
- unique_table_count
- table_title_examples
- value_examples
- current_risk_tags
- candidate_category
- priority

### `candidate_level_pack`
- case_id
- table_asset_id
- source_report_name
- table_title
- row_label
- row_values
- year_columns
- unit_context
- current_risk_tags
- current_review_reason
- priority

### `allowed_metric_codes`
- metric_code
- metric_family
- description_if_available
- example_aliases_if_available

### `prompt_templates`
- template_name
- purpose
- prompt_text
- output_schema_name

### `acceptance_gate_rules`
- rule_id
- rule_type
- condition
- allowed_result
- reason

### `estimated_review_impact`
- category
- candidate_count
- unique_label_count
- estimated_llm_resolvable_count
- estimated_manual_remaining_count
- reason

### `semantic_adjudicator_batch_plan`
- batch_id
- batch_type
- case_count
- priority
- input_file
- expected_output_file

### `qa_checks`
### `known_limitations`

## output_contract
Write to:

```powershell
D:\_datefac\output\semantic_adjudicator_design_322c
```

Required files:
1. `semantic_adjudicator_design_322c.xlsx`

Sheets:
- `summary`
- `semantic_case_inventory`
- `label_level_pack`
- `candidate_level_pack`
- `allowed_metric_codes`
- `prompt_templates`
- `acceptance_gate_rules`
- `estimated_review_impact`
- `semantic_adjudicator_batch_plan`
- `qa_checks`
- `known_limitations`

2. `semantic_adjudicator_design_322c_summary.json`

3. `semantic_adjudicator_design_322c_report.md`

4. `llm_label_pack_322c.jsonl`

5. `llm_candidate_pack_322c.jsonl`

6. `llm_adjudicator_output_schema_322c.json`

7. `llm_prompt_templates_322c.md`

## summary_metrics
Include:
- input_review_required_count
- unknown_metric_candidate_count
- unit_unknown_candidate_count
- mapping_review_candidate_count
- invalid_year_or_schema_candidate_count
- semantic_case_count
- label_level_case_count
- candidate_level_case_count
- alias_candidate_count
- out_of_scope_classification_case_count
- unit_context_inference_case_count
- manual_review_reserved_count
- estimated_llm_resolvable_candidate_count
- estimated_manual_remaining_count
- prompt_template_count
- output_schema_defined
- acceptance_gate_rule_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_design_decision

Decision rule:
- If qa_fail_count > 0:
  `SEMANTIC_ADJUDICATOR_DESIGN_BLOCKED_BY_QA_FAILURE`
- If output_schema_defined and label_level_case_count > 0 and acceptance_gate_rule_count >= 5:
  `SEMANTIC_ADJUDICATOR_DESIGN_READY_FOR_322D_LIMITED_EXECUTION`
- If semantic_case_count > 0:
  `SEMANTIC_ADJUDICATOR_DESIGN_PARTIAL_NEEDS_SCHEMA_REVIEW`
- Otherwise:
  `SEMANTIC_ADJUDICATOR_DESIGN_NOT_READY`

## qa_checks
Required checks:
- 322B2 trust split output exists;
- no model/API call executed;
- no E-drive files modified;
- no production files modified;
- label and candidate packs have stable case IDs;
- output schema is valid JSON;
- every candidate-level case has provenance or a provenance warning;
- prompt templates forbid numeric invention;
- acceptance gate forbids LLM-only trusted decisions;
- output files written successfully.

Warnings, not failures:
- many unknown metrics remain;
- allowed metric code list may be incomplete;
- LLM adjudicator still requires later validation.

## safety_constraints
Absolute constraints:
1. Do not call any LLM/API/cloud/network.
2. Do not run MinerU.
3. Do not run StructEqTable.
4. Do not run Docling.
5. Do not run PaddleOCR/PPStructure.
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
python -m py_compile datefac/semantic/adjudicator_schema.py
python -m py_compile datefac/semantic/adjudicator_pack_builder.py
python -m py_compile datefac/semantic/adjudicator_prompt_templates.py
python -m py_compile datefac/semantic/adjudicator_readiness.py
python -m py_compile tools/run_semantic_adjudicator_design_322c.py
```

Then run:

```powershell
python tools/run_semantic_adjudicator_design_322c.py ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --router-dir D:\_datefac\output\recognizer_router_321f ^
  --output-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --max-label-pack 120 ^
  --max-case-pack 120
```

PowerShell one-line form is acceptable. Report exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 322C code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Design semantic adjudicator packs`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_review_required_count
- unknown_metric_candidate_count
- unit_unknown_candidate_count
- mapping_review_candidate_count
- invalid_year_or_schema_candidate_count
- semantic_case_count
- label_level_case_count
- candidate_level_case_count
- alias_candidate_count
- out_of_scope_classification_case_count
- unit_context_inference_case_count
- manual_review_reserved_count
- estimated_llm_resolvable_candidate_count
- estimated_manual_remaining_count
- prompt_template_count
- output_schema_defined
- acceptance_gate_rule_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_design_decision
- skipped/untracked files
