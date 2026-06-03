# 322G Human-Confirmed Semantic Mapping Proposals

## task_title
Build human-confirmed semantic mapping proposal tables from accepted 322F replay instructions

## project
D:\_datefac

## current_context
322F apply30 has already produced accepted deterministic replay instructions and replay impact diagnostics.

Primary input directories:

```powershell
D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30
D:\_datefac\output\router_mineru_trust_split_322b2
```

Key 322F apply30 facts:
- replay_allowed_instruction_count: 10
- accepted_alias_suggestion_count: 3
- out_of_scope_classification_count: 7
- unit_inference_accept_count: 0
- rejected_noise_count: 0
- trusted_gain_322f: 49
- review_reduction_322f: 287
- qa_fail_count: 0

322G should not change production behavior. It should turn accepted replay instructions into human-review proposal tables only.

## goal
Implement a sandbox-only 322G proposal generation workflow that:
1. reads accepted replay instructions from 322F apply30;
2. filters to deterministic-gate-accepted instruction types only;
3. groups them into alias, out-of-scope, unit inference, and rejected noise proposals;
4. attaches sample candidate impact evidence from existing sandbox outputs;
5. emits an Excel workbook, summary JSON, and markdown report for human confirmation;
6. preserves traceability back to the exact 322F case IDs and replay instructions.

## non_goals
Do not do these in 322G:
- Do not call any LLM/API/cloud/network.
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PPStructure.
- Do not modify `E:\mineru_lab`.
- Do not modify production delivery files.
- Do not modify `data/mapping/*`.
- Do not modify `data/overrides/*`.
- Do not modify old Stage7 or production router code.
- Do not auto-apply proposals into official mappings.
- Do not commit `output/`.
- Do not commit unrelated dirty files or temp scripts.

## expected_new_or_modified_files
Suggested independent files:
- `datefac/semantic/semantic_mapping_proposals.py`
- `datefac/semantic/semantic_mapping_proposals_report.py`
- `tools/run_semantic_mapping_proposals_322g.py`
- `docs/codex_tasks/322g_human_confirmed_semantic_mapping_proposals.md`

Keep all logic isolated from production pipeline entrypoints.

## input_contract
Read only existing outputs:

```powershell
D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30
D:\_datefac\output\router_mineru_trust_split_322b2
```

Minimum required source files:
- `semantic_replay_instructions_322f.jsonl`
- `deterministic_gate_results_322f.jsonl`
- `candidate_replay_diff_322f.jsonl`
- `semantic_adjudicator_larger_batch_322f_summary.json`
- `selected_candidate_reclassified_322b2.jsonl`
- `router_mineru_trust_split_322b2_summary.json`

Allowed replay instruction types:
- `ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY`
- `CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY`
- `ACCEPT_UNIT_INFERENCE_FOR_REPLAY`
- `REJECT_NOISE_FOR_REPLAY`

## output_contract
Write outputs to:

```powershell
D:\_datefac\output\semantic_mapping_proposals_322g
```

Required files:
1. `semantic_mapping_proposals_322g.xlsx`
2. `semantic_mapping_proposals_322g_summary.json`
3. `semantic_mapping_proposals_322g_report.md`

Required workbook sheets:
- `summary`
- `alias_mapping_proposals`
- `out_of_scope_proposals`
- `unit_inference_proposals`
- `rejected_noise_proposals`
- `candidate_impact_samples`
- `human_review_checklist`
- `remaining_review_burden_after_322f`
- `qa_checks`
- `known_limitations`

### `alias_mapping_proposals`
Required columns:
- `proposal_id`
- `source_case_id`
- `normalized_label`
- `proposed_metric_code`
- `proposed_metric_family`
- `confidence_label`
- `affected_candidate_count`
- `trusted_gain`
- `review_reduction`
- `sample_table_titles`
- `sample_row_labels`
- `sample_years`
- `sample_values`
- `risk_flags`
- `recommended_human_decision`
- `reviewer_comment`

### `out_of_scope_proposals`
Required columns:
- `proposal_id`
- `source_case_id`
- `normalized_label`
- `reason`
- `affected_candidate_count`
- `review_reduction`
- `sample_table_titles`
- `sample_row_labels`
- `sample_values`
- `risk_flags`
- `recommended_human_decision`
- `reviewer_comment`

## summary_metrics
Include:
- `accepted_instruction_count`
- `proposal_total_count`
- `alias_mapping_proposal_count`
- `out_of_scope_proposal_count`
- `unit_inference_proposal_count`
- `rejected_noise_proposal_count`
- `candidate_impact_sample_count`
- `alias_affected_candidate_count`
- `out_of_scope_affected_candidate_count`
- `trusted_gain_total`
- `review_reduction_total`
- `remaining_manual_review_count_after_322f`
- `selected_core_trusted_rate_before_322f`
- `selected_core_trusted_rate_after_322f`
- `qa_pass_count`
- `qa_warn_count`
- `qa_fail_count`
- `semantic_mapping_proposals_decision`

Decision rule:
- If `qa_fail_count > 0`:
  `SEMANTIC_MAPPING_PROPOSALS_322G_BLOCKED_BY_QA_FAILURE`
- Else if `proposal_total_count > 0`:
  `SEMANTIC_MAPPING_PROPOSALS_322G_READY_FOR_HUMAN_CONFIRMATION`
- Else:
  `SEMANTIC_MAPPING_PROPOSALS_322G_NO_ACCEPTED_PROPOSALS`

## qa_checks
Required checks:
- 322F apply30 summary exists.
- 322B2 trust split summary exists.
- accepted proposal count reconciles with 322F replay-allowed count.
- all proposals trace to accepted 322F instructions.
- alias trusted gain reconciles with 322F trusted gain.
- review reduction reconciles with 322F review reduction.
- no official mapping or override file writes are required.
- no recognizer or LLM execution is required.
- 322F upstream QA fail count is zero.
- output files written successfully.

Hard requirement:
- `qa_fail_count` must be `0`.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/semantic/semantic_mapping_proposals.py
python -m py_compile datefac/semantic/semantic_mapping_proposals_report.py
python -m py_compile tools/run_semantic_mapping_proposals_322g.py
```

Run actual CLI:

```powershell
python tools/run_semantic_mapping_proposals_322g.py ^
  --apply30-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30 ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\semantic_mapping_proposals_322g
```

## commit_requirements
Before implementation:

```powershell
git status
```

After implementation:
1. only add 322G code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add unrelated dirty files or temp scripts;
5. commit message:
   `Build semantic mapping proposal reports`
6. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- accepted_instruction_count
- proposal_total_count
- alias_mapping_proposal_count
- out_of_scope_proposal_count
- unit_inference_proposal_count
- rejected_noise_proposal_count
- trusted_gain_total
- review_reduction_total
- remaining_manual_review_count_after_322f
- selected_core_trusted_rate_after_322f
- qa_pass_count
- qa_warn_count
- qa_fail_count
- semantic_mapping_proposals_decision
- skipped dirty/untracked files
