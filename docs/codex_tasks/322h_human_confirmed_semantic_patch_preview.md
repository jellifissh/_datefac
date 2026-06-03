# 322H Human-Confirmed Semantic Patch Preview

## task_title
Replay human-confirmed 322G semantic mapping proposals as sandbox patch preview

## project
D:\_datefac

## current_context
322F apply30 and 322G proposal generation have completed.

322F apply30 output:

```powershell
D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30
```

322F apply30 key results:
- selected_label_case_count: 30
- request_payload_count: 30
- response_available_count: 30
- response_schema_valid_count: 30
- accepted_alias_suggestion_count: 3
- out_of_scope_classification_count: 7
- unit_inference_accept_count: 0
- replay_allowed_instruction_count: 10
- affected_candidate_count: 49
- trusted_gain_322f: 49
- review_reduction_322f: 287
- selected_core_trusted_rate_before_322f: 0.415104
- selected_core_trusted_rate_after_322f: 0.423309
- remaining_unknown_metric_candidate_count: 2897
- remaining_unit_unknown_candidate_count: 491
- qa_fail_count: 0
- semantic_adjudicator_larger_batch_decision: `SEMANTIC_ADJUDICATOR_322F_READY_FOR_HUMAN_CONFIRMED_MAPPING_PROPOSALS`

322G output:

```powershell
D:\_datefac\output\semantic_mapping_proposals_322g
```

322G key results:
- accepted_instruction_count: 10
- proposal_total_count: 10
- alias_mapping_proposal_count: 3
- out_of_scope_proposal_count: 7
- unit_inference_proposal_count: 0
- rejected_noise_proposal_count: 0
- trusted_gain_total: 49
- review_reduction_total: 287
- remaining_manual_review_count_after_322f: 3071
- selected_core_trusted_rate_after_322f: 0.423309
- qa_fail_count: 0
- semantic_mapping_proposals_decision: `SEMANTIC_MAPPING_PROPOSALS_322G_READY_FOR_HUMAN_CONFIRMATION`

A human-reviewed proposal workbook is expected at:

```powershell
D:\_datefac\input\semantic_mapping_proposals_322g_reviewed\semantic_mapping_proposals_322g_reviewed.xlsx
```

The reviewed workbook should contain reviewer decisions, usually:
- `ACCEPT`
- `REJECT`
- `NEEDS_MORE_INFO`

322H must use only human-confirmed `ACCEPT` decisions.

## goal
Implement 322H as a sandbox-only human-confirmed semantic patch preview stage.

322H should:
1. read the human-reviewed 322G workbook;
2. select only proposals with `reviewer_decision = ACCEPT`;
3. convert accepted alias proposals into sandbox mapping patch candidates;
4. convert accepted out-of-scope proposals into sandbox scope-rule patch candidates;
5. optionally support unit/reject-noise proposals if present, but expect zero in this batch;
6. apply accepted proposal effects to the 322B2/322F sandbox candidate state;
7. produce before/after diff and trusted/review/rejected previews;
8. verify no production mapping/override file is modified;
9. decide whether the confirmed patch set is ready for an official rule proposal stage.

This is still sandbox-only. It is not production integration.

## non_goals
Do not do these in 322H:
- Do not call any LLM/API/cloud/network.
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PaddleOCR/PPStructure.
- Do not modify `E:\mineru_lab`.
- Do not modify production delivery files.
- Do not modify official mapping files.
- Do not modify official override files.
- Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
- Do not modify `data/mapping/formal_scope_rules.json`.
- Do not add aliases to official mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not run `factory_core.py`.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/semantic/human_confirmed_patch_preview.py`
- `datefac/semantic/human_confirmed_patch_report.py`
- `tools/run_human_confirmed_semantic_patch_preview_322h.py`
- `docs/codex_tasks/322h_human_confirmed_semantic_patch_preview.md`

Keep all 322H logic in `datefac/semantic` and an independent CLI.

Reuse 322E/322F replay logic if safe, but do not couple this to production entrypoints.

## input_contract
Required inputs:

```powershell
D:\_datefac\input\semantic_mapping_proposals_322g_reviewed\semantic_mapping_proposals_322g_reviewed.xlsx
D:\_datefac\output\semantic_mapping_proposals_322g
D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30
D:\_datefac\output\router_mineru_trust_split_322b2
```

Suggested CLI:

```powershell
python tools/run_human_confirmed_semantic_patch_preview_322h.py ^
  --reviewed-proposal-xlsx D:\_datefac\input\semantic_mapping_proposals_322g_reviewed\semantic_mapping_proposals_322g_reviewed.xlsx ^
  --proposal-dir D:\_datefac\output\semantic_mapping_proposals_322g ^
  --adjudicator-apply-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30 ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\human_confirmed_semantic_patch_preview_322h
```

If reviewed proposal workbook is missing, write a blocked summary instead of crashing:
- `BLOCKED_MISSING_REVIEWED_PROPOSAL_XLSX`

If required 322G/322F/322B2 outputs are missing, write a blocked summary instead of crashing:
- `BLOCKED_MISSING_322G_PROPOSAL_DIR`
- `BLOCKED_MISSING_322F_APPLY_DIR`
- `BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR`

## reviewed_workbook_contract
The reviewed workbook may contain one or more of these sheets:
- `reviewer_decisions`
- `alias_mapping_proposals`
- `out_of_scope_proposals`
- `unit_inference_proposals`
- `rejected_noise_proposals`

322H should be tolerant of column naming variants:
- `reviewer_decision`
- `recommended_human_decision`
- `human_decision`

Canonical decisions:
- `ACCEPT`
- `REJECT`
- `NEEDS_MORE_INFO`

Only `ACCEPT` may be applied.

Do not treat blank decision, `NEEDS_CONFIRMATION`, `NEEDS_MORE_INFO`, or `REJECT` as accepted.

## patch_preview_requirements
For accepted alias proposals:
- generate alias patch preview rows;
- include source normalized label;
- include proposed metric_code;
- include affected candidate examples;
- apply only to matching candidates in sandbox preview;
- candidate can become trusted only if deterministic gates still pass;
- preserve before/after metric_code, decision, and risk tags.

For accepted out-of-scope proposals:
- generate scope patch preview rows;
- mark matching candidates as review-excluded / rejected / out-of-scope according to existing sandbox convention;
- do not count excluded rows in core review burden if existing preview supports that field;
- preserve before/after diff and reason.

For accepted unit inference proposals:
- generate unit patch preview rows if any exist;
- apply only if high-confidence and already accepted by previous deterministic gate;
- do not infer units from scratch.

For accepted reject-noise proposals:
- generate noise patch preview rows if any exist;
- reject only exact matched noise cases.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary.

### `reviewed_proposal_inventory`
- proposal_id
- proposal_type
- source_case_id
- normalized_label
- proposed_metric_code
- proposed_metric_family
- reviewer_decision
- reviewer_comment
- accepted_for_patch_preview
- skip_reason

### `alias_patch_preview`
- patch_id
- proposal_id
- normalized_label
- proposed_metric_code
- proposed_metric_family
- affected_candidate_count
- trusted_gain
- review_reduction
- sample_table_titles
- sample_row_labels
- sample_values
- risk_flags
- patch_status

### `out_of_scope_patch_preview`
- patch_id
- proposal_id
- normalized_label
- affected_candidate_count
- review_reduction
- sample_table_titles
- sample_row_labels
- sample_values
- risk_flags
- patch_status

### `unit_inference_patch_preview`
### `rejected_noise_patch_preview`

These two sheets may be empty but should still exist.

### `candidate_before_after_diff_322h`
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
- proposal_id
- patch_id
- patch_reason
- provenance

### `trusted_after_patch_preview_322h`
### `review_required_after_patch_preview_322h`
### `rejected_after_patch_preview_322h`

### `patch_impact_by_proposal_322h`
- proposal_id
- proposal_type
- normalized_label
- affected_candidate_count
- trusted_gain
- review_reduction
- rejected_or_out_of_scope_count
- notes

### `remaining_review_burden_322h`
- review_reason
- candidate_count
- unique_table_count
- unique_label_count
- sample_labels
- recommended_next_action

### `official_rule_candidate_preview`
This sheet is only a preview. Do not modify official files.

Fields:
- rule_candidate_id
- rule_type (`alias_mapping`, `out_of_scope_scope_rule`, `unit_inference`, `reject_noise`)
- normalized_label
- proposed_metric_code
- proposed_metric_family
- proposed_scope_action
- source_proposal_id
- evidence_summary
- affected_candidate_count
- trusted_gain
- review_reduction
- human_decision
- ready_for_official_proposal

### `qa_checks`
### `known_limitations`

## output_contract
Write to:

```powershell
D:\_datefac\output\human_confirmed_semantic_patch_preview_322h
```

Required files:
1. `human_confirmed_semantic_patch_preview_322h.xlsx`

Sheets:
- `summary`
- `reviewed_proposal_inventory`
- `alias_patch_preview`
- `out_of_scope_patch_preview`
- `unit_inference_patch_preview`
- `rejected_noise_patch_preview`
- `candidate_before_after_diff_322h`
- `trusted_after_patch_preview_322h`
- `review_required_after_patch_preview_322h`
- `rejected_after_patch_preview_322h`
- `patch_impact_by_proposal_322h`
- `remaining_review_burden_322h`
- `official_rule_candidate_preview`
- `qa_checks`
- `known_limitations`

2. `human_confirmed_semantic_patch_preview_322h_summary.json`

3. `human_confirmed_semantic_patch_preview_322h_report.md`

4. `candidate_before_after_diff_322h.jsonl`

5. `official_rule_candidate_preview_322h.jsonl`

## summary_metrics
Include:
- reviewed_proposal_count
- accepted_proposal_count
- rejected_proposal_count
- needs_more_info_proposal_count
- accepted_alias_patch_count
- accepted_out_of_scope_patch_count
- accepted_unit_inference_patch_count
- accepted_rejected_noise_patch_count
- affected_candidate_count
- trusted_total_before_322h
- trusted_total_after_322h
- review_required_total_before_322h
- review_required_total_after_322h
- rejected_total_before_322h
- rejected_total_after_322h
- trusted_gain_322h
- review_reduction_322h
- out_of_scope_or_rejected_gain_322h
- selected_core_trusted_rate_before_322h
- selected_core_trusted_rate_after_322h
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- remaining_manual_review_count
- official_rule_candidate_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- human_confirmed_patch_preview_decision

Decision rule:
- If qa_fail_count > 0:
  `HUMAN_CONFIRMED_PATCH_PREVIEW_322H_BLOCKED_BY_QA_FAILURE`
- If accepted_proposal_count > 0 and review_reduction_322h > 0:
  `HUMAN_CONFIRMED_PATCH_PREVIEW_322H_READY_FOR_322I_OFFICIAL_RULE_CANDIDATES`
- If accepted_proposal_count > 0:
  `HUMAN_CONFIRMED_PATCH_PREVIEW_322H_PARTIAL_NO_REDUCTION`
- Otherwise:
  `HUMAN_CONFIRMED_PATCH_PREVIEW_322H_NO_ACCEPTED_PROPOSALS`

## qa_checks
Required checks:
- reviewed proposal workbook exists;
- 322G proposal output exists;
- 322F apply30 output exists;
- 322B2 trust split output exists;
- only reviewer_decision = ACCEPT proposals are applied;
- no model/API call executed;
- no recognizer command executed;
- no E-drive files modified;
- no production files modified;
- no official mapping/override files modified;
- every patch candidate traces to one 322G proposal;
- every applied candidate has provenance;
- no LLM-only trusted decision exists;
- trusted candidates after patch preview still satisfy deterministic gates;
- candidate counts reconcile before/after;
- output files written successfully.

Warnings, not failures:
- small proposal set;
- human-reviewed workbook may be derived from manual inspection;
- official mapping still requires a later explicit rule proposal stage;
- scope exclusions should be rechecked before production.

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
10. Do not modify any official mapping or override file.
11. Do not run `factory_core.py`.
12. Do not rewrite old Stage7 pipeline.
13. Do not commit `output/` artifacts.
14. Do not commit anything under `E:\mineru_lab`.
15. Do not commit `input/semantic_adjudicator_responses_*`.
16. Do not commit unrelated 320G2 leftovers or temp scripts.
17. Preserve Chinese text as UTF-8.
18. Never commit API keys or credentials.

## validation
Run compile checks:

```powershell
python -m py_compile datefac/semantic/human_confirmed_patch_preview.py
python -m py_compile datefac/semantic/human_confirmed_patch_report.py
python -m py_compile tools/run_human_confirmed_semantic_patch_preview_322h.py
```

Then run:

```powershell
python tools/run_human_confirmed_semantic_patch_preview_322h.py ^
  --reviewed-proposal-xlsx D:\_datefac\input\semantic_mapping_proposals_322g_reviewed\semantic_mapping_proposals_322g_reviewed.xlsx ^
  --proposal-dir D:\_datefac\output\semantic_mapping_proposals_322g ^
  --adjudicator-apply-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30 ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --output-dir D:\_datefac\output\human_confirmed_semantic_patch_preview_322h
```

PowerShell one-line form is acceptable. Report exact command used.

## commit_requirements
Before implementation:

```powershell
git status
git pull origin main
```

If unrelated modified/untracked files are present, do not add them.

After implementation:
1. only add 322H code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add `input/semantic_adjudicator_responses_*`;
5. do not add unrelated 320G2 leftovers or temp scripts;
6. commit message:
   `Preview human confirmed semantic patches`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- reviewed_proposal_count
- accepted_proposal_count
- rejected_proposal_count
- needs_more_info_proposal_count
- accepted_alias_patch_count
- accepted_out_of_scope_patch_count
- accepted_unit_inference_patch_count
- accepted_rejected_noise_patch_count
- affected_candidate_count
- trusted_total_before_322h
- trusted_total_after_322h
- review_required_total_before_322h
- review_required_total_after_322h
- rejected_total_before_322h
- rejected_total_after_322h
- trusted_gain_322h
- review_reduction_322h
- selected_core_trusted_rate_before_322h
- selected_core_trusted_rate_after_322h
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- remaining_manual_review_count
- official_rule_candidate_count
- qa_pass_count
- qa_warn_count
- qa_fail_count
- human_confirmed_patch_preview_decision
- skipped/untracked files
