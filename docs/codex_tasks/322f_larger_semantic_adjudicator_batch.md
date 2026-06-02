# 322F Larger Semantic Adjudicator Batch

## task_title
Scale the semantic adjudicator from 5-case replay to a larger controlled sandbox batch

## project
D:\_datefac

## current_context
322E semantic adjudicator replay has completed and pushed to `main`.

Latest 322E output directory:

```powershell
D:\_datefac\output\semantic_adjudicator_replay_322e
```

322E key results:
- input_candidate_count: 5972
- replay_instruction_count: 5
- replay_allowed_instruction_count: 1
- replay_blocked_instruction_count: 4
- affected_candidate_count: 22
- trusted_total_before_322e: 2479
- trusted_total_after_322e: 2501
- review_required_total_before_322e: 3358
- review_required_total_after_322e: 3336
- rejected_total_before_322e: 135
- rejected_total_after_322e: 135
- trusted_gain_322e: 22
- review_reduction_322e: 22
- selected_core_trusted_rate_before_322e: 0.415104
- selected_core_trusted_rate_after_322e: 0.418788
- remaining_unknown_metric_candidate_count: 3162
- remaining_unit_unknown_candidate_count: 491
- remaining_manual_review_count: 3336
- qa_pass_count: 11
- qa_warn_count: 4
- qa_fail_count: 0
- semantic_adjudicator_replay_decision: `SEMANTIC_ADJUDICATOR_REPLAY_READY_FOR_322F_LARGER_BATCH`

Important interpretation:
- The full semantic loop is now proven on a small batch:
  1. 322C builds semantic packs and strict schema.
  2. 322D ingests JSONL responses and applies deterministic gates.
  3. 322E replays accepted instructions into sandbox candidates.
- The first 5-case test produced one accepted alias instruction and reduced review by 22 candidates.
- This is not enough for production, but it is enough to justify a larger controlled batch.
- 322F should scale the same pattern to a larger but still bounded batch, with better case selection and stronger audit metrics.

## goal
Implement 322F as a sandbox-only larger semantic adjudicator batch workflow.

322F should:
1. build a larger selected semantic case batch from 322C/322D-compatible packs;
2. prioritize cases likely to reduce review burden, not just the first N labels;
3. generate request payloads for a bounded batch, default 30 label-level cases and 0 candidate-level cases;
4. support dry-run and apply-existing-responses modes;
5. validate JSONL responses against the 322C schema;
6. apply deterministic gates exactly like 322D;
7. replay accepted instructions exactly like 322E;
8. produce before/after review burden and trusted/review/rejected diff;
9. report precision-oriented metrics, not just raw review reduction;
10. decide whether semantic adjudication is ready for human-confirmed mapping proposal generation.

This is still sandbox-only. It is not production integration.

## non_goals
Do not do these in 322F:
- Do not call any LLM/API/cloud/network in default validation.
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PaddleOCR/PPStructure.
- Do not modify `E:\mineru_lab`.
- Do not modify production delivery files.
- Do not apply anything into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not add aliases to official mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not auto-trust LLM output without deterministic gates.
- Do not commit LLM responses if they contain provider metadata, secrets, or unnecessary raw prompts.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/semantic/adjudicator_batch_selector.py`
- `datefac/semantic/adjudicator_larger_batch.py`
- `datefac/semantic/adjudicator_larger_batch_report.py`
- `tools/run_semantic_adjudicator_larger_batch_322f.py`
- `docs/codex_tasks/322f_larger_semantic_adjudicator_batch.md`

Reuse existing 322C/322D/322E modules where safe:
- `datefac/semantic/adjudicator_executor.py`
- `datefac/semantic/adjudicator_response_reader.py`
- `datefac/semantic/adjudicator_gate_applier.py`
- `datefac/semantic/adjudicator_replay.py`
- `datefac/semantic/adjudicator_replay_report.py`

Keep the code inside `datefac/semantic` and independent CLI. Do not modify production entrypoints.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\semantic_adjudicator_design_322c
D:\_datefac\output\router_mineru_trust_split_322b2
D:\_datefac\output\semantic_adjudicator_limited_322d_apply5
D:\_datefac\output\semantic_adjudicator_replay_322e
```

Optional existing response input:

```powershell
D:\_datefac\input\semantic_adjudicator_responses_322f\llm_label_responses_322f.jsonl
D:\_datefac\input\semantic_adjudicator_responses_322f\llm_candidate_responses_322f.jsonl
```

CLI dry-run:

```powershell
python tools/run_semantic_adjudicator_larger_batch_322f.py ^
  --design-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --previous-limited-dir D:\_datefac\output\semantic_adjudicator_limited_322d_apply5 ^
  --previous-replay-dir D:\_datefac\output\semantic_adjudicator_replay_322e ^
  --output-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f ^
  --mode dry_run ^
  --max-label-cases 30 ^
  --max-candidate-cases 0
```

CLI apply-existing-responses:

```powershell
python tools/run_semantic_adjudicator_larger_batch_322f.py ^
  --design-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --previous-limited-dir D:\_datefac\output\semantic_adjudicator_limited_322d_apply5 ^
  --previous-replay-dir D:\_datefac\output\semantic_adjudicator_replay_322e ^
  --response-dir D:\_datefac\input\semantic_adjudicator_responses_322f ^
  --output-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply ^
  --mode apply_existing_responses ^
  --max-label-cases 30 ^
  --max-candidate-cases 0
```

Default validation path must be dry-run and must not call any model.

If required inputs are missing, produce blocked summaries instead of crashing:
- `BLOCKED_MISSING_322C_DESIGN_DIR`
- `BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR`

## batch_selection_requirements
Do not simply pick the first 30 labels.

Build a selection score that prioritizes:
1. high candidate_count labels;
2. labels with readable Chinese/English text;
3. likely alias candidates where allowed metric codes have plausible match;
4. likely out-of-scope rows that can safely reduce core review burden;
5. labels occurring across multiple tables/reports;
6. labels from core financial statement / forecast / valuation tables;
7. cases not already accepted/replayed in 322E.

Avoid or down-rank:
- unreadable/mojibake labels;
- invalid-year-only cases;
- value-parse-failure-only cases;
- low-evidence labels with no table/title/value examples;
- labels already handled in 322E.

Create a `batch_selection_audit` sheet explaining why each case was selected or skipped.

## request_payload_requirements
Generate:
- `llm_label_requests_322f.jsonl`
- `llm_candidate_requests_322f.jsonl`

Each request must include:
- stable case_id;
- prompt text;
- input context;
- output schema;
- allowed metric codes;
- allowed actions;
- safety rules;
- source pack row;
- selection score and reason.

The prompt must explicitly forbid:
- inventing numeric values;
- modifying years;
- bypassing provenance;
- direct trusted decision;
- metric_code outside allowed list.

## response_and_gate_requirements
In `apply_existing_responses` mode:
1. read response JSONL from `--response-dir`;
2. parse one JSON object per line;
3. validate against 322C schema;
4. deduplicate duplicate case IDs conservatively;
5. apply deterministic gates from 322D;
6. produce replay instructions;
7. apply replay to 322B2 candidates using 322E replay logic;
8. produce before/after diff.

Accepted gate results:
- `ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY`
- `CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY`
- `ACCEPT_UNIT_INFERENCE_FOR_REPLAY`
- `REJECT_NOISE_FOR_REPLAY`

Rejected/held gate results:
- `KEEP_REVIEW_REQUIRED`
- `REQUIRES_MANUAL_REVIEW`
- `LLM_RESPONSE_SCHEMA_INVALID`
- `LLM_RESPONSE_LOW_CONFIDENCE`
- `LLM_RESPONSE_UNSUPPORTED_METRIC_CODE`

No LLM-only trusted decision is allowed.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary.

### `batch_selection_audit`
- case_id
- normalized_label
- candidate_count
- unique_table_count
- candidate_category
- selection_score
- selected
- selection_reason
- skip_reason

### `selected_label_cases_322f`
- label_case_id
- normalized_label
- candidate_count
- unique_table_count
- candidate_category
- priority
- selection_score
- selection_reason

### `llm_request_inventory_322f`
- case_id
- case_type
- request_file
- prompt_template
- allowed_actions
- selected_for_execution
- mode

### `llm_response_validation_322f`
- case_id
- response_available
- json_parse_ok
- schema_valid
- action
- metric_code
- confidence_label
- validation_errors

### `deterministic_gate_results_322f`
- case_id
- action
- metric_code
- confidence_label
- gate_result
- affected_candidate_count
- estimated_trusted_candidate_gain
- estimated_review_reduction
- reason

### `replay_instruction_inventory_322f`
- instruction_id
- case_id
- instruction_type
- normalized_label
- proposed_metric_code
- proposed_metric_family
- proposed_unit
- confidence_label
- affected_candidate_count
- replay_allowed
- replay_block_reason

### `candidate_replay_diff_322f`
- table_asset_id
- source_report_name
- row_label
- year
- raw_value
- normalized_value
- unit_before
- unit_after
- metric_code_before
- metric_code_after
- decision_before
- decision_after
- risk_tags_before
- risk_tags_after
- replay_instruction_id
- replay_reason
- provenance

### `trusted_preview_322f`
### `review_required_preview_322f`
### `rejected_preview_322f`

### `review_reduction_by_instruction_322f`
- instruction_id
- case_id
- instruction_type
- candidates_affected
- trusted_gain
- review_reduction
- rejected_or_out_of_scope_count
- notes

### `remaining_review_burden_322f`
- review_reason
- candidate_count
- unique_table_count
- unique_label_count
- sample_labels
- recommended_next_action

### `qa_checks`
### `known_limitations`

## output_contract
Write dry-run output to:

```powershell
D:\_datefac\output\semantic_adjudicator_larger_batch_322f
```

Write apply output to caller-provided output dir, suggested:

```powershell
D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply
```

Required files:
1. `semantic_adjudicator_larger_batch_322f.xlsx`

Sheets:
- `summary`
- `batch_selection_audit`
- `selected_label_cases_322f`
- `llm_request_inventory_322f`
- `llm_response_validation_322f`
- `deterministic_gate_results_322f`
- `replay_instruction_inventory_322f`
- `candidate_replay_diff_322f`
- `trusted_preview_322f`
- `review_required_preview_322f`
- `rejected_preview_322f`
- `review_reduction_by_instruction_322f`
- `remaining_review_burden_322f`
- `qa_checks`
- `known_limitations`

2. `semantic_adjudicator_larger_batch_322f_summary.json`

3. `semantic_adjudicator_larger_batch_322f_report.md`

4. `llm_label_requests_322f.jsonl`

5. `llm_candidate_requests_322f.jsonl`

Optional if applying existing responses:
- `llm_label_responses_validated_322f.jsonl`
- `deterministic_gate_results_322f.jsonl`
- `candidate_replay_diff_322f.jsonl`
- `semantic_replay_instructions_322f.jsonl`

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
- replay_instruction_count
- replay_allowed_instruction_count
- replay_blocked_instruction_count
- affected_candidate_count
- trusted_total_before_322f
- trusted_total_after_322f
- review_required_total_before_322f
- review_required_total_after_322f
- rejected_total_before_322f
- rejected_total_after_322f
- trusted_gain_322f
- review_reduction_322f
- selected_core_trusted_rate_before_322f
- selected_core_trusted_rate_after_322f
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- remaining_manual_review_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_larger_batch_decision

Decision rule:
- If qa_fail_count > 0:
  `SEMANTIC_ADJUDICATOR_322F_BLOCKED_BY_QA_FAILURE`
- If mode is `dry_run` and request_payload_count > 0:
  `SEMANTIC_ADJUDICATOR_322F_REQUESTS_READY_FOR_EXTERNAL_EXECUTION`
- If replay_allowed_instruction_count > 0 and review_reduction_322f > 0:
  `SEMANTIC_ADJUDICATOR_322F_READY_FOR_HUMAN_CONFIRMED_MAPPING_PROPOSALS`
- If response_available_count > 0:
  `SEMANTIC_ADJUDICATOR_322F_RESPONSES_NEED_REVIEW`
- Otherwise:
  `SEMANTIC_ADJUDICATOR_322F_NO_RESPONSES_YET`

## qa_checks
Required checks:
- 322C design output exists;
- 322B2 trust split output exists;
- no model/API call executed in dry-run;
- no recognizer command executed;
- no E-drive files modified;
- no production files modified;
- request payloads have stable case IDs;
- every prompt forbids numeric invention;
- every replayed candidate has provenance;
- no LLM-only trusted decision exists;
- trusted candidates after replay still satisfy deterministic gates;
- candidate counts reconcile before/after;
- output files written successfully.

Warnings, not failures:
- limited sample size;
- LLM response files may be absent in dry-run;
- many review cases may remain unresolved;
- human confirmation is still needed before official alias updates.

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
python -m py_compile datefac/semantic/adjudicator_batch_selector.py
python -m py_compile datefac/semantic/adjudicator_larger_batch.py
python -m py_compile datefac/semantic/adjudicator_larger_batch_report.py
python -m py_compile tools/run_semantic_adjudicator_larger_batch_322f.py
```

Then run dry-run validation:

```powershell
python tools/run_semantic_adjudicator_larger_batch_322f.py ^
  --design-dir D:\_datefac\output\semantic_adjudicator_design_322c ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --previous-limited-dir D:\_datefac\output\semantic_adjudicator_limited_322d_apply5 ^
  --previous-replay-dir D:\_datefac\output\semantic_adjudicator_replay_322e ^
  --output-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f ^
  --mode dry_run ^
  --max-label-cases 30 ^
  --max-candidate-cases 0
```

Do not require actual network execution for validation.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 322F code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Prepare larger semantic adjudicator batch`
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
- response_schema_valid_count
- accepted_alias_suggestion_count
- out_of_scope_classification_count
- unit_inference_accept_count
- replay_allowed_instruction_count
- affected_candidate_count
- trusted_gain_322f
- review_reduction_322f
- selected_core_trusted_rate_before_322f
- selected_core_trusted_rate_after_322f
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_larger_batch_decision
- skipped/untracked files
