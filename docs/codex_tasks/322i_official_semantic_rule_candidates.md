# 322I Official Semantic Rule Candidates

## task_title
Convert human-confirmed semantic patch preview into official rule candidate package without modifying production mappings

## project
D:\_datefac

## current_context
322H human-confirmed semantic patch preview has completed and pushed to `main`.

322H output directory:

```powershell
D:\_datefac\output\human_confirmed_semantic_patch_preview_322h
```

322H key results:
- reviewed_proposal_count: 10
- accepted_proposal_count: 10
- rejected_proposal_count: 0
- needs_more_info_proposal_count: 0
- accepted_alias_patch_count: 3
- accepted_out_of_scope_patch_count: 7
- accepted_unit_inference_patch_count: 0
- accepted_rejected_noise_patch_count: 0
- affected_candidate_count: 287
- trusted_total_before_322h: 2479
- trusted_total_after_322h: 2528
- review_required_total_before_322h: 3358
- review_required_total_after_322h: 3071
- rejected_total_before_322h: 135
- rejected_total_after_322h: 373
- trusted_gain_322h: 49
- review_reduction_322h: 287
- selected_core_trusted_rate_before_322h: 0.415104
- selected_core_trusted_rate_after_322h: 0.423309
- remaining_unknown_metric_candidate_count: 2897
- remaining_unit_unknown_candidate_count: 491
- remaining_manual_review_count: 3071
- official_rule_candidate_count: 10
- qa_pass_count: 16
- qa_warn_count: 0
- qa_fail_count: 0
- human_confirmed_patch_preview_decision: `HUMAN_CONFIRMED_PATCH_PREVIEW_322H_READY_FOR_322I_OFFICIAL_RULE_CANDIDATES`

Important interpretation:
- 322H has validated that the human-confirmed semantic proposals produce measurable sandbox benefit.
- The confirmed patch preview increased trusted candidates by 49 and reduced review candidates by 287 with QA failure count 0.
- However, 322H still did not modify official mapping or scope rule files.
- 322I should package the confirmed semantic patches as official rule candidates for later explicit approval/application.
- 322I must not apply rules to production mapping/override files.

## goal
Implement 322I as a sandbox-only official rule candidate packaging stage.

322I should:
1. read 322H official rule candidate preview and candidate diffs;
2. generate official alias mapping rule candidates from accepted alias patches;
3. generate official out-of-scope/scope-rule candidates from accepted out-of-scope patches;
4. detect duplicate or conflicting rule candidates against existing official mapping/scope files in read-only mode;
5. generate a human approval package suitable for future controlled rule application;
6. estimate expected trusted gain / review reduction from applying the candidate rule set;
7. produce machine-readable patch candidate JSON files;
8. produce an Excel workbook with evidence, impact samples, risk notes, and approval columns;
9. decide whether the candidate package is ready for a later 322J sandbox rule application.

This is still proposal packaging only. It is not rule application.

## non_goals
Do not do these in 322I:
- Do not modify official mapping files.
- Do not modify official override files.
- Do not modify `data/overrides/02B_ai_repair_override.xlsx`.
- Do not modify `data/mapping/formal_scope_rules.json`.
- Do not apply aliases to production pipeline.
- Do not call any LLM/API/cloud/network.
- Do not run MinerU.
- Do not run StructEqTable.
- Do not run Docling.
- Do not run PaddleOCR/PPStructure.
- Do not modify `E:\mineru_lab`.
- Do not modify production delivery files.
- Do not run `factory_core.py`.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `datefac/semantic/official_rule_candidates.py`
- `datefac/semantic/official_rule_candidates_report.py`
- `tools/run_official_semantic_rule_candidates_322i.py`
- `docs/codex_tasks/322i_official_semantic_rule_candidates.md`

Keep all 322I logic in `datefac/semantic` and an independent CLI.
Do not modify production mapping/delivery entrypoints.

## input_contract
Required inputs:

```powershell
D:\_datefac\output\human_confirmed_semantic_patch_preview_322h
D:\_datefac\output\semantic_mapping_proposals_322g
D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30
D:\_datefac\output\router_mineru_trust_split_322b2
```

Read-only official reference inputs, if present:

```powershell
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\02B_ai_repair_override.xlsx
```

Suggested CLI:

```powershell
python tools/run_official_semantic_rule_candidates_322i.py ^
  --patch-preview-dir D:\_datefac\output\human_confirmed_semantic_patch_preview_322h ^
  --proposal-dir D:\_datefac\output\semantic_mapping_proposals_322g ^
  --adjudicator-apply-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30 ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --formal-scope-rules D:\_datefac\data\mapping\formal_scope_rules.json ^
  --ai-repair-override D:\_datefac\data\overrides\02B_ai_repair_override.xlsx ^
  --output-dir D:\_datefac\output\official_semantic_rule_candidates_322i
```

If reference official files are missing, continue with warnings and mark duplicate/conflict checks as partial.
If 322H output is missing, produce blocked summary instead of crashing:
- `BLOCKED_MISSING_322H_PATCH_PREVIEW_DIR`

## rule_candidate_requirements
### Alias mapping rule candidates
For each accepted alias patch:
- normalized_label
- raw_label_examples
- proposed_metric_code
- proposed_metric_family
- source_case_id
- source_proposal_id
- evidence_table_titles
- sample_values
- affected_candidate_count
- trusted_gain
- review_reduction
- risk_flags
- human_decision
- duplicate_existing_alias_status
- conflict_status
- recommended_action

Recommended actions:
- `READY_FOR_322J_SANDBOX_RULE_APPLICATION`
- `NEEDS_ADDITIONAL_HUMAN_REVIEW`
- `DUPLICATE_EXISTING_RULE`
- `CONFLICT_WITH_EXISTING_RULE`

### Scope-rule / out-of-scope candidates
For each accepted out-of-scope patch:
- normalized_label
- raw_label_examples
- proposed_scope_action, usually `exclude_from_core_metric_mapping`
- source_case_id
- source_proposal_id
- evidence_table_titles
- sample_values
- affected_candidate_count
- review_reduction
- rejected_or_out_of_scope_gain
- risk_flags
- human_decision
- duplicate_existing_scope_status
- conflict_status
- recommended_action

### Conflict checks
322I should check, in read-only mode:
- whether an alias candidate label already maps to a different metric_code;
- whether a proposed out-of-scope label already appears as an official core metric alias;
- whether duplicate candidates exist inside the candidate package;
- whether any accepted candidate lacks evidence/provenance;
- whether any candidate has zero impact.

Do not modify any reference files.

## diagnostics_required
Create these sheets:

### `summary`
One-row summary.

### `official_alias_rule_candidates`
- rule_candidate_id
- normalized_label
- raw_label_examples
- proposed_metric_code
- proposed_metric_family
- source_proposal_id
- source_case_id
- affected_candidate_count
- trusted_gain
- review_reduction
- evidence_table_titles
- sample_row_labels
- sample_values
- risk_flags
- duplicate_existing_alias_status
- conflict_status
- recommended_action
- human_approval_decision
- reviewer_comment

### `official_scope_rule_candidates`
- rule_candidate_id
- normalized_label
- raw_label_examples
- proposed_scope_action
- source_proposal_id
- source_case_id
- affected_candidate_count
- review_reduction
- rejected_or_out_of_scope_gain
- evidence_table_titles
- sample_row_labels
- sample_values
- risk_flags
- duplicate_existing_scope_status
- conflict_status
- recommended_action
- human_approval_decision
- reviewer_comment

### `candidate_impact_evidence`
- rule_candidate_id
- table_asset_id
- source_report_name
- table_title
- row_label
- year
- raw_value
- normalized_value
- decision_before
- decision_after
- metric_code_before
- metric_code_after
- risk_tags_before
- risk_tags_after
- provenance

### `duplicate_conflict_audit`
- rule_candidate_id
- rule_type
- normalized_label
- proposed_metric_code_or_scope_action
- duplicate_status
- conflict_status
- matching_existing_rule_reference
- reason

### `official_patch_json_preview`
- artifact_name
- artifact_type
- candidate_count
- output_path
- notes

### `human_approval_checklist`
- rule_candidate_id
- rule_type
- normalized_label
- proposed_action
- impact_summary
- risk_summary
- required_human_check
- approval_status
- approver_comment

### `remaining_review_burden_after_candidate_rules`
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
D:\_datefac\output\official_semantic_rule_candidates_322i
```

Required files:
1. `official_semantic_rule_candidates_322i.xlsx`

Sheets:
- `summary`
- `official_alias_rule_candidates`
- `official_scope_rule_candidates`
- `candidate_impact_evidence`
- `duplicate_conflict_audit`
- `official_patch_json_preview`
- `human_approval_checklist`
- `remaining_review_burden_after_candidate_rules`
- `qa_checks`
- `known_limitations`

2. `official_semantic_rule_candidates_322i_summary.json`

3. `official_semantic_rule_candidates_322i_report.md`

4. `alias_rule_candidates_322i.json`

5. `scope_rule_candidates_322i.json`

6. `official_rule_candidate_package_322i.json`

## summary_metrics
Include:
- input_official_rule_candidate_count
- alias_rule_candidate_count
- scope_rule_candidate_count
- unit_rule_candidate_count
- rejected_noise_rule_candidate_count
- duplicate_rule_candidate_count
- conflict_rule_candidate_count
- ready_for_sandbox_application_count
- needs_additional_review_count
- affected_candidate_count
- expected_trusted_gain
- expected_review_reduction
- expected_out_of_scope_or_rejected_gain
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- remaining_manual_review_count
- official_reference_scope_rules_loaded
- official_reference_override_loaded
- qa_pass_count
- qa_warn_count
- qa_fail_count
- official_rule_candidates_decision

Decision rule:
- If qa_fail_count > 0:
  `OFFICIAL_RULE_CANDIDATES_322I_BLOCKED_BY_QA_FAILURE`
- If conflict_rule_candidate_count > 0:
  `OFFICIAL_RULE_CANDIDATES_322I_NEEDS_CONFLICT_REVIEW`
- If ready_for_sandbox_application_count > 0 and expected_review_reduction > 0:
  `OFFICIAL_RULE_CANDIDATES_322I_READY_FOR_322J_SANDBOX_APPLICATION`
- If input_official_rule_candidate_count > 0:
  `OFFICIAL_RULE_CANDIDATES_322I_PARTIAL_NEEDS_REVIEW`
- Otherwise:
  `OFFICIAL_RULE_CANDIDATES_322I_NO_RULE_CANDIDATES`

## qa_checks
Required checks:
- 322H patch preview output exists;
- no model/API call executed;
- no recognizer command executed;
- no E-drive files modified;
- no production files modified;
- no official mapping/override files modified;
- every rule candidate traces to one 322H accepted proposal;
- every candidate has evidence rows;
- alias candidates have proposed metric_code;
- out-of-scope candidates have proposed scope action;
- conflicts and duplicates are audited;
- output JSON files are valid;
- output Excel/JSON/report written successfully.

Warnings, not failures:
- official reference files missing;
- small rule candidate set;
- human approval still required before production mapping updates;
- scope exclusions should be reviewed carefully before official application.

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
python -m py_compile datefac/semantic/official_rule_candidates.py
python -m py_compile datefac/semantic/official_rule_candidates_report.py
python -m py_compile tools/run_official_semantic_rule_candidates_322i.py
```

Then run:

```powershell
python tools/run_official_semantic_rule_candidates_322i.py ^
  --patch-preview-dir D:\_datefac\output\human_confirmed_semantic_patch_preview_322h ^
  --proposal-dir D:\_datefac\output\semantic_mapping_proposals_322g ^
  --adjudicator-apply-dir D:\_datefac\output\semantic_adjudicator_larger_batch_322f_apply30 ^
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 ^
  --formal-scope-rules D:\_datefac\data\mapping\formal_scope_rules.json ^
  --ai-repair-override D:\_datefac\data\overrides\02B_ai_repair_override.xlsx ^
  --output-dir D:\_datefac\output\official_semantic_rule_candidates_322i
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
1. only add 322I code and this task document;
2. do not add `output/`;
3. do not add `E:\mineru_lab`;
4. do not add `input/semantic_adjudicator_responses_*`;
5. do not add unrelated 320G2 leftovers or temp scripts;
6. commit message:
   `Package official semantic rule candidates`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- input_official_rule_candidate_count
- alias_rule_candidate_count
- scope_rule_candidate_count
- unit_rule_candidate_count
- rejected_noise_rule_candidate_count
- duplicate_rule_candidate_count
- conflict_rule_candidate_count
- ready_for_sandbox_application_count
- needs_additional_review_count
- affected_candidate_count
- expected_trusted_gain
- expected_review_reduction
- expected_out_of_scope_or_rejected_gain
- remaining_unknown_metric_candidate_count
- remaining_unit_unknown_candidate_count
- remaining_manual_review_count
- official_reference_scope_rules_loaded
- official_reference_override_loaded
- qa_pass_count
- qa_warn_count
- qa_fail_count
- official_rule_candidates_decision
- skipped/untracked files
