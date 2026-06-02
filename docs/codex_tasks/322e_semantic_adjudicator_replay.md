# 322E Semantic Adjudicator Replay

## task_title
Replay accepted 322D semantic adjudicator decisions into sandbox candidates with deterministic gates

## project
D:\_datefac

## current_context
322D limited semantic adjudicator dry-run and apply-existing-responses path have been validated.

Latest 322D apply output:

```powershell
D:\_datefac\output\semantic_adjudicator_limited_322d_apply5
```

Latest key results:
- mode: `apply_existing_responses`
- selected_label_case_count: 5
- selected_candidate_case_count: 0
- request_payload_count: 5
- response_available_count: 5
- response_json_parse_ok_count: 5
- response_schema_valid_count: 5
- accepted_alias_suggestion_count: 1
- out_of_scope_classification_count: 0
- unit_inference_accept_count: 0
- rejected_noise_count: 0
- keep_review_required_count: 0
- manual_review_after_llm_count: 4
- estimated_trusted_candidate_gain: 22
- estimated_review_reduction: 22
- estimated_manual_remaining: 3336
- qa_fail_count: 0
- semantic_adjudicator_limited_decision: `SEMANTIC_ADJUDICATOR_LIMITED_READY_FOR_322E_REPLAY`

Important interpretation:
- The 322D response ingestion path is working.
- JSONL response parsing and schema validation are working.
- The deterministic post-LLM gate accepted one alias suggestion.
- The first measured review reduction is small but real: 22 candidates.
- 322E should replay only accepted 322D instructions into sandbox candidate previews.
- 322E must not modify official mapping/override files or production delivery.

## goal
Implement 322E as a sandbox-only semantic replay stage.

322E should:
1. read 322D accepted replay instructions;
2. read 322B2 trusted/review/rejected candidate outputs;
3. apply accepted alias/out-of-scope/unit/reject-noise replay instructions to matching candidates only in sandbox;
4. recompute split decisions using deterministic gates;
5. produce before/after trusted/review/rejected summaries;
6. verify that no LLM-only decision becomes trusted without passing hard gates;
7. output an auditable replay diff;
8. decide whether semantic adjudicator replay is ready for a larger 322F batch.

This is sandbox replay only. It is not production integration.

## non_goals
Do not do these in 322E:
- Do not call any LLM/API/cloud/network.
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
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/semantic/adjudicator_replay.py`
- `datefac/semantic/adjudicator_replay_report.py`
- `tools/run_semantic_adjudicator_replay_322e.py`
- `docs/codex_tasks/322e_semantic_adjudicator_replay.md`

Keep all 322E logic in `datefac/semantic` and an independent CLI. Do not modify production entrypoints.

## input_contract
Primary inputs:

```powershell
D:\_datefac\output\semantic_adjudicator_limited_322d_apply5
D:\_datefac\output\router_mineru_trust_split_322b2
```

Optional reference inputs:

```powershell
D:\_datefac\output\semantic_adjudicator_design_322c
D:\_datefac\output\router_driven_sandbox_pipeline_322b
D:\_datefac\output\router_driven_sandbox_pipeline_322a
D:\_datefac\output\recognizer_router_321f
```

CLI:

```powershell
python tools/run_semantic_adjudicator_replay_322e.py ^
  --adjudicator-limited-dir D:\_datefac\output\semantic_adjudicator_limited_322d_apply5 ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\semantic_adjudicator_replay_322e
```

If 322D apply output is missing, produce blocked summary instead of crashing:
- `BLOCKED_MISSING_322D_APPLY_DIR`

If 322B2 trust split output is missing, produce blocked summary instead of crashing:
- `BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR`

## replay_requirements
Replay only deterministic-gate-approved instructions.

Accepted replay instruction types:
- `ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY`
- `CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY`
- `ACCEPT_UNIT_INFERENCE_FOR_REPLAY`
- `REJECT_NOISE_FOR_REPLAY`

Do not replay:
- `KEEP_REVIEW_REQUIRED`
- `REQUIRES_MANUAL_REVIEW`
- `LLM_RESPONSE_SCHEMA_INVALID`
- `LLM_RESPONSE_LOW_CONFIDENCE`
- `LLM_RESPONSE_UNSUPPORTED_METRIC_CODE`

For alias replay:
- match by `normalized_label` / case ID mapping;
- update candidate metric_code only in sandbox replay output;
- preserve original metric_code and risk tags in before fields;
- remove `UNKNOWN_METRIC_CODE` only if the proposed metric_code is allowed and accepted;
- after applying alias, candidate can become trusted only if year, numeric value, unit, provenance, conflict, and extraction-risk gates all pass.

For out-of-scope replay:
- mark affected candidates as out-of-scope/rejected or review-excluded according to existing sandbox convention;
- do not count them in core trusted-rate denominator if the existing sandbox supports that field;
- preserve original rows in diff.

For unit inference replay:
- apply only high-confidence unit inference accepted by 322D gates;
- candidate can become trusted only if all other gates pass.

For reject-noise replay:
- only reject clear noise; preserve audit reason.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary.

### `replay_instruction_inventory`
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

### `candidate_replay_diff`
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

### `trusted_preview_322e`
### `review_required_preview_322e`
### `rejected_preview_322e`

### `review_reduction_by_instruction`
- instruction_id
- case_id
- instruction_type
- candidates_affected
- trusted_gain
- review_reduction
- rejected_or_out_of_scope_count
- notes

### `remaining_review_burden_322e`
- review_reason
- candidate_count
- unique_table_count
- unique_label_count
- sample_labels
- recommended_next_action

### `qa_checks`
### `known_limitations`

## output_contract
Write to:

```powershell
D:\_datefac\output\semantic_adjudicator_replay_322e
```

Required files:
1. `semantic_adjudicator_replay_322e.xlsx`

Sheets:
- `summary`
- `replay_instruction_inventory`
- `candidate_replay_diff`
- `trusted_preview_322e`
- `review_required_preview_322e`
- `rejected_preview_322e`
- `review_reduction_by_instruction`
- `remaining_review_burden_322e`
- `qa_checks`
- `known_limitations`

2. `semantic_adjudicator_replay_322e_summary.json`

3. `semantic_adjudicator_replay_322e_report.md`

4. `candidate_replay_diff_322e.jsonl`

Optional:
- `semantic_replay_instructions_322e.jsonl`

## summary_metrics
Include:
- input_candidate_count
- replay_instruction_count
- replay_allowed_instruction_count
- replay_blocked_instruction_count
- affected_candidate_count
- trusted_total_before_322e
- trusted_total_after_322e
- review_required_total_before_322e
- review_required_total_after_322e
- rejected_total_before_322e
- rejected_total_after_322e
- trusted_gain_322e
- review_reduction_322e
- out_of_scope_or_rejected_gain_322e
- selected_core_trusted_rate_before_322e
- selected_core_trusted_rate_after_322e
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- remaining_manual_review_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_replay_decision

Decision rule:
- If qa_fail_count > 0:
  `SEMANTIC_ADJUDICATOR_REPLAY_BLOCKED_BY_QA_FAILURE`
- If replay_allowed_instruction_count > 0 and review_reduction_322e > 0:
  `SEMANTIC_ADJUDICATOR_REPLAY_READY_FOR_322F_LARGER_BATCH`
- If replay_allowed_instruction_count > 0:
  `SEMANTIC_ADJUDICATOR_REPLAY_PARTIAL_NO_REDUCTION`
- Otherwise:
  `SEMANTIC_ADJUDICATOR_REPLAY_NO_ACCEPTED_INSTRUCTIONS`

## qa_checks
Required checks:
- 322D apply output exists;
- 322B2 trust split output exists;
- no model/API call executed;
- no recognizer command executed;
- no E-drive files modified;
- no production files modified;
- every replayed candidate has provenance;
- no LLM-only trusted decision exists;
- trusted candidates after replay still satisfy deterministic gates;
- candidate counts reconcile before/after;
- output files written successfully.

Warnings, not failures:
- small 5-case sample size;
- only one accepted instruction may be available;
- most review cases may remain manual/review_required;
- human confirmation is still recommended before official mapping updates.

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
17. Never commit API keys or credentials.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/semantic/adjudicator_replay.py
python -m py_compile datefac/semantic/adjudicator_replay_report.py
python -m py_compile tools/run_semantic_adjudicator_replay_322e.py
```

Then run:

```powershell
python tools/run_semantic_adjudicator_replay_322e.py ^
  --adjudicator-limited-dir D:\_datefac\output\semantic_adjudicator_limited_322d_apply5 ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\semantic_adjudicator_replay_322e
```

PowerShell one-line form is acceptable. Report exact command used.

## commit_requirements
Before implementation:

```powershell
git status
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 322E code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated 320G2 leftovers or temp scripts;
5. commit message:
   `Replay limited semantic adjudicator decisions`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_candidate_count
- replay_instruction_count
- replay_allowed_instruction_count
- replay_blocked_instruction_count
- affected_candidate_count
- trusted_total_before_322e
- trusted_total_after_322e
- review_required_total_before_322e
- review_required_total_after_322e
- rejected_total_before_322e
- rejected_total_after_322e
- trusted_gain_322e
- review_reduction_322e
- selected_core_trusted_rate_before_322e
- selected_core_trusted_rate_after_322e
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- remaining_manual_review_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_adjudicator_replay_decision
- skipped/untracked files
