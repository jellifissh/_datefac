# 322D Limited Semantic Adjudicator Execution

## task_title
Run a limited, auditable semantic adjudicator batch from 322C packs and apply deterministic post-LLM gates in sandbox

## project
D:\_datefac

## current_context
322C semantic adjudicator design has completed and pushed to `main`.

322C output directory:

```powershell
D:\_datefac\output\semantic_adjudicator_design_322c
```

322C key results:
- input_review_required_count: 3358
- unknown_metric_candidate_count: 3184
- unit_unknown_candidate_count: 491
- mapping_review_candidate_count: 713
- invalid_year_or_schema_candidate_count: 153
- semantic_case_count: 120
- label_level_case_count: 120
- candidate_level_case_count: 0
- alias_candidate_count: 20
- out_of_scope_classification_case_count: 66
- unit_context_inference_case_count: 0
- manual_review_reserved_count: 0
- estimated_llm_resolvable_candidate_count: 1283
- estimated_manual_remaining_count: 2075
- prompt_template_count: 3
- output_schema_defined: true
- acceptance_gate_rule_count: 6
- qa_pass_count: 10
- qa_warn_count: 2
- qa_fail_count: 0
- semantic_adjudicator_design_decision: `SEMANTIC_ADJUDICATOR_DESIGN_READY_FOR_322D_LIMITED_EXECUTION`

Important interpretation:
- 322B2 restored deterministic trust split and raised selected_core_trusted_rate to about 0.4151.
- Remaining review burden is real, mostly UNKNOWN_METRIC_CODE and HAS_MAPPING_REVIEW_TAG.
- 322C produced controlled label/candidate packs, output schema, prompt templates, and acceptance gates.
- 322D should test a small LLM semantic adjudicator batch.
- LLM decisions must never auto-trust data by themselves. They only produce semantic suggestions that deterministic gates may accept, downgrade, or route to review/out-of-scope.

## goal
Implement 322D as a limited sandbox-only semantic adjudicator execution stage.

322D should:
1. read 322C label-level and candidate-level packs;
2. select a bounded high-priority subset, default 20 label-level cases and 0 candidate-level cases unless explicitly configured;
3. prepare strict prompt payloads using the 322C templates and JSON schema;
4. support two execution modes:
   - `dry_run`: only emits request payloads, no model/API call;
   - `apply_existing_responses`: reads pre-generated LLM response JSONL from disk and applies gates;
5. optionally support `execute_llm` only when explicit CLI flag and provider config are supplied, but do not make it the default validation path;
6. parse adjudicator responses robustly;
7. validate every response against schema;
8. apply deterministic acceptance gates from 322C;
9. generate adjudicated alias/out-of-scope/unit/review decisions;
10. estimate and report review burden reduction;
11. produce a clear decision on whether semantic adjudication is ready for 322E candidate application/replay.

The default task implementation should pass validation without calling any external model.

## non_goals
Do not do these in 322D:
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
- Do not commit LLM secrets, API keys, raw credentials, or provider configs containing secrets.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/semantic/adjudicator_executor.py`
- `datefac/semantic/adjudicator_response_reader.py`
- `datefac/semantic/adjudicator_gate_applier.py`
- `datefac/semantic/adjudicator_result_report.py`
- `tools/run_semantic_adjudicator_limited_322d.py`
- `docs/codex_tasks/322d_limited_semantic_adjudicator_execution.md`

Keep all 322D logic in `datefac/semantic` and the independent CLI. Do not modify production mapping/delivery entrypoints.

## input_contract
Primary input:

```powershell
D:\_datefac\output\semantic_adjudicator_design_322c
```

Reference input:

```powershell
D:\_datefac\output\router_mineru_trust_split_322b2
```

Optional response input for no-network validation:

```powershell
D:\_datefac\input\semantic_adjudicator_responses_322d\llm_label_responses_322d.jsonl
D:\_datefac\input\semantic_adjudicator_responses_322d\llm_candidate_responses_322d.jsonl
```

CLI dry-run validation:

```powershell
python tools/run_semantic_adjudicator_limited_322d.py ^
  --design-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\semantic_adjudicator_limited_322d ^
  --mode dry_run ^
  --max-label-cases 20 ^
  --max-candidate-cases 0
```

CLI apply-existing-responses mode:

```powershell
python tools/run_semantic_adjudicator_limited_322d.py ^
  --design-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --response-dir D:\_datefac\input\semantic_adjudicator_responses_322d ^
  --output-dir D:\_datefac\output\semantic_adjudicator_limited_322d ^
  --mode apply_existing_responses ^
  --max-label-cases 20 ^
  --max-candidate-cases 0
```

Optional actual execution mode, only if implemented safely:

```powershell
python tools/run_semantic_adjudicator_limited_322d.py ^
  --design-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\semantic_adjudicator_limited_322d ^
  --mode execute_llm ^
  --provider openai_compatible ^
  --model <MODEL_NAME> ^
  --max-label-cases 20 ^
  --max-candidate-cases 0
```

Actual execution must require explicit flags. Do not execute network calls in default validation.

If 322C output is missing, produce blocked summary instead of crashing:
- `BLOCKED_MISSING_322C_DESIGN_DIR`

## selection_requirements
Default selected cases:
- choose up to 20 label-level cases;
- prioritize:
  1. high candidate_count unknown labels;
  2. likely alias candidates;
  3. likely out-of-scope/core classification cases;
  4. labels appearing in core financial statement or forecast/valuation tables;
- do not include invalid year/schema cases by default;
- do not include value parse failures by default;
- candidate-level pack default is 0 unless explicitly requested.

## request_payload_requirements
For each selected label/candidate case, create a request payload:

Fields:
- `case_id`
- `case_type`
- `prompt_text`
- `input_context`
- `output_schema`
- `allowed_metric_codes`
- `allowed_actions`
- `safety_rules`
- `source_pack_row`

Write request payloads to:
- `llm_label_requests_322d.jsonl`
- `llm_candidate_requests_322d.jsonl`

## response_schema
Responses must match the 322C schema:

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

Invalid JSON or schema-invalid responses must become `LLM_RESPONSE_SCHEMA_INVALID` and not affect mapping.

## deterministic_gate_requirements
Apply deterministic gates after LLM response validation.

Gate outcomes:
- `ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY`
- `CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY`
- `ACCEPT_UNIT_INFERENCE_FOR_REPLAY`
- `KEEP_REVIEW_REQUIRED`
- `REQUIRES_MANUAL_REVIEW`
- `REJECT_NOISE_FOR_REPLAY`
- `LLM_RESPONSE_SCHEMA_INVALID`
- `LLM_RESPONSE_LOW_CONFIDENCE`
- `LLM_RESPONSE_UNSUPPORTED_METRIC_CODE`

A label/candidate may be eligible for future trusted replay only if:
- LLM action is `map_to_existing_metric_code`;
- confidence_label is `high`;
- metric_code is in allowed codes;
- affected underlying candidates still have valid year, parsed numeric value, unit known or accepted high-confidence unit inference, complete provenance, no conflict, no extraction risk.

322D does not directly rewrite the candidate table. It produces replay instructions for a later 322E.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary.

### `selected_label_cases`
- label_case_id
- normalized_label
- candidate_count
- unique_table_count
- candidate_category
- priority
- selection_reason

### `selected_candidate_cases`
- case_id
- table_asset_id
- table_title
- row_label
- current_review_reason
- priority
- selection_reason

### `llm_request_inventory`
- case_id
- case_type
- request_file
- prompt_template
- allowed_actions
- selected_for_execution
- mode

### `llm_response_validation`
- case_id
- response_available
- json_parse_ok
- schema_valid
- action
- metric_code
- confidence_label
- validation_errors

### `deterministic_gate_results`
- case_id
- action
- metric_code
- confidence_label
- gate_result
- affected_candidate_count
- estimated_trusted_candidate_gain
- estimated_review_reduction
- reason

### `alias_replay_instructions`
- normalized_label
- proposed_metric_code
- proposed_metric_family
- confidence_label
- affected_candidate_count
- replay_allowed
- replay_block_reason
- requires_human_confirmation

### `out_of_scope_replay_instructions`
- normalized_label
- affected_candidate_count
- replay_allowed
- reason

### `unit_inference_replay_instructions`
- case_id
- proposed_unit
- unit_source
- confidence_label
- affected_candidate_count
- replay_allowed
- reason

### `manual_review_after_llm`
- case_id
- normalized_label_or_row
- reason
- priority

### `estimated_impact_322d`
- input_review_required_count
- selected_case_count
- response_valid_count
- accepted_alias_count
- out_of_scope_count
- unit_inference_count
- rejected_noise_count
- estimated_trusted_gain
- estimated_review_reduction
- estimated_manual_remaining

### `qa_checks`
### `known_limitations`

## output_contract
Write to:

```powershell
D:\_datefac\output\semantic_adjudicator_limited_322d
```

Required files:
1. `semantic_adjudicator_limited_322d.xlsx`

Sheets:
- `summary`
- `selected_label_cases`
- `selected_candidate_cases`
- `llm_request_inventory`
- `llm_response_validation`
- `deterministic_gate_results`
- `alias_replay_instructions`
- `out_of_scope_replay_instructions`
- `unit_inference_replay_instructions`
- `manual_review_after_llm`
- `estimated_impact_322d`
- `qa_checks`
- `known_limitations`

2. `semantic_adjudicator_limited_322d_summary.json`

3. `semantic_adjudicator_limited_322d_report.md`

4. `llm_label_requests_322d.jsonl`

5. `llm_candidate_requests_322d.jsonl`

Optional if applying existing responses or executing LLM:
- `llm_label_responses_validated_322d.jsonl`
- `deterministic_gate_results_322d.jsonl`
- `alias_replay_instructions_322d.jsonl`

## summary_metrics
Include:
- mode
- selected_label_case_count
- selected_candidate_case_count
- request_payload_count
- response_available_count
- response_json_parse_ok_count
- response_schema_valid_count
- accepted_alias_suggestion_count
- out_of_scope_classification_count
- unit_inference_accept_count
- rejected_noise_count
- keep_review_required_count
- manual_review_after_llm_count
- estimated_trusted_candidate_gain
- estimated_review_reduction
- estimated_manual_remaining
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_limited_decision

Decision rule:
- If qa_fail_count > 0:
  `SEMANTIC_ADJUDICATOR_LIMITED_BLOCKED_BY_QA_FAILURE`
- If mode is `dry_run` and request_payload_count > 0:
  `SEMANTIC_ADJUDICATOR_LIMITED_REQUESTS_READY_FOR_EXTERNAL_EXECUTION`
- If response_schema_valid_count > 0 and accepted_alias_suggestion_count + out_of_scope_classification_count + unit_inference_accept_count > 0:
  `SEMANTIC_ADJUDICATOR_LIMITED_READY_FOR_322E_REPLAY`
- If response_available_count > 0:
  `SEMANTIC_ADJUDICATOR_LIMITED_RESPONSES_NEED_REVIEW`
- Otherwise:
  `SEMANTIC_ADJUDICATOR_LIMITED_NO_RESPONSES_YET`

## qa_checks
Required checks:
- 322C design output exists;
- no recognizer command executed;
- no E-drive files modified;
- no production files modified;
- default validation mode does not call any model/API;
- request payloads have stable case IDs;
- every prompt forbids numeric invention;
- output schema is included in every request payload;
- deterministic gate forbids LLM-only trusted decisions;
- output files written successfully.

Warnings, not failures:
- dry_run has no responses;
- limited sample size;
- actual LLM execution requires manual provider configuration;
- human confirmation may still be required before replaying aliases.

## safety_constraints
Absolute constraints:
1. Default validation must not call any LLM/API/cloud/network.
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
17. Never commit API keys or credentials.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/semantic/adjudicator_executor.py
python -m py_compile datefac/semantic/adjudicator_response_reader.py
python -m py_compile datefac/semantic/adjudicator_gate_applier.py
python -m py_compile datefac/semantic/adjudicator_result_report.py
python -m py_compile tools/run_semantic_adjudicator_limited_322d.py
```

Then run dry-run validation:

```powershell
python tools/run_semantic_adjudicator_limited_322d.py ^
  --design-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\semantic_adjudicator_limited_322d ^
  --mode dry_run ^
  --max-label-cases 20 ^
  --max-candidate-cases 0
```

If implementing apply-existing-responses mode, also run it only when a response dir is present. Do not require actual network execution for validation.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 322D code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Prepare limited semantic adjudicator execution`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- mode
- selected_label_case_count
- selected_candidate_case_count
- request_payload_count
- response_available_count
- response_json_parse_ok_count
- response_schema_valid_count
- accepted_alias_suggestion_count
- out_of_scope_classification_count
- unit_inference_accept_count
- rejected_noise_count
- keep_review_required_count
- manual_review_after_llm_count
- estimated_trusted_candidate_gain
- estimated_review_reduction
- estimated_manual_remaining
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_limited_decision
- skipped/untracked files
