# 346B4R Controlled Expansion Replay With Patched Rules

## Goal

Implement `346B4R Controlled Expansion Replay With Patched Rules`.

346B4 ran a controlled 500-row quality-limited recovery expansion and produced:

```text
controlled_expansion_input_row_count = 500
safe_recovered_candidate_count = 212
false_positive_guardrail_hit_count = 0
unit_semantic_mismatch_count = 0
still_quality_limited_count = 252
needs_human_review_count = 14
needs_rule_refinement_count = 22
semantic_class_unknown_count = 22
safe_to_continue_expansion = false
```

346B3R then audited the 22 unknown/refinement rows and found:

```text
audited_unknown_row_count = 22
patchable_rule_gap_count = 22
non_patchable_row_count = 0
proposed_semantic_classifier_patch_count = 2
proposed_unit_policy_patch_count = 2
rows_converted_from_unknown_to_known_semantic_class_count = 22
rows_kept_quality_limited_count = 22
patch_requires_reaudit_count = 22
safe_to_replay_346b4 = true
safe_to_continue_expansion = false
live_vlm_call_count = 0
```

346B4R must answer:

> If the 346B3R patch proposals are applied as sidecar replay rules to the same 500-row controlled expansion batch from 346B4, do the 22 previously UNKNOWN rows become correctly classifiable without introducing unit mismatches, false-positive guardrail hits, or lineage/evidence regressions?

This task is a replay of the same controlled expansion batch using patched sidecar rules. It must not expand to new rows by default, must not mutate upstream data, and must not modify official rules/assets.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Replay the same controlled batch before larger expansion.
- Apply patch proposals as sidecar rules only.
- Preserve raw values and source lineage.
- Do not silently promote rows that fail guardrails.
- Do not call live VLM/LLM APIs.
- Do not run OCR.
- Do not rerun MinerU.
- Do not write back to upstream datasets.
- Do not modify official normalization rules or official alias assets.
- Keep all formal/client/production gates closed.

346B4R is not a full expansion. It is a replay validation stage after 346B3R.

---

## Current context

345D output:

```text
D:\_datefac\output\full_structured_demo_export_package_345d
```

346B4 output:

```text
D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
```

346B3R output:

```text
D:\_datefac\output\recovery_rule_refinement_patch_346b3r
```

346B4R output:

```text
D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r
```

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B4R entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B4R`
- decision: `CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY`
- input 345D dir
- input 346B4 dir
- input 346B3R dir
- output dir
- replay input row count
- previous 346B4 safe recovered count
- replay safe recovered count
- previous unknown count
- replay unknown count
- unknown resolved count
- patch applied row count
- patch regression count
- false-positive guardrail hit count
- unit semantic mismatch count
- lineage audit passed
- evidence weakness count
- safe-to-continue expansion flag
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false
- next recommended step

If the ledger has unrelated dirty changes, append only the 346B4R entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B4R_controlled_expansion_replay_with_patched_rules.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346B4 output dir
- 346B3R output dir
- the milestone ledger
- the root tactical playbook

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
--recovery-rule-refinement-patch-346b3r-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r
--output-dir D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r
```

Optional knobs:

```powershell
--replay-same-row-set true
--strict-guardrails true
--require-346b3r-safe-to-replay true
--max-context-chars 4000
```

Default behavior:

- read exactly the selected row set from 346B4;
- do not select new rows by default;
- read 346B4 recovery results and unknown/refinement rows;
- read 346B3R proposed classifier patches, proposed unit patches, patch safety review, and replay readiness report;
- apply 346B3R patch proposals as sidecar replay rules;
- recompute semantic class and unit compatibility for the same 500 rows;
- preserve previous 346B4 decisions for comparison;
- produce replay results and delta reports;
- do not mutate 346B4 or 346B3R outputs;
- do not modify official rules/assets;
- do not call live VLM/LLM APIs;
- do not run OCR;
- do not rerun MinerU.

---

## Inputs to read

From 346B4:

- `controlled_quality_limited_recovery_expansion_346b4_manifest.json`
- `controlled_quality_limited_recovery_expansion_346b4_selected_rows.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_recovery_results.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json`

From 346B3R:

- `recovery_rule_refinement_patch_346b3r_manifest.json`
- `recovery_rule_refinement_patch_346b3r_patchable_rows.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json`
- `recovery_rule_refinement_patch_346b3r_patch_safety_review.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_replay_readiness_report.json`

From 345D if needed:

- `full_structured_demo_export_package_345d_manifest.json`
- quality-limited rows only for row id/context lookup

Validate:

- 346B4 decision is `CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY`
- 346B4 `qa_fail_count = 0`
- 346B4 `controlled_expansion_input_row_count = 500`
- 346B4 `semantic_class_unknown_count = 22`
- 346B4 `needs_rule_refinement_count = 22`
- 346B4 `safe_to_continue_expansion = false`
- 346B3R decision is `RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY`
- 346B3R `qa_fail_count = 0`
- 346B3R `safe_to_replay_346b4 = true`
- 346B3R `patch_requires_reaudit_count = 22`
- all live VLM call counts are `0`
- all formal/client/production gates are false

---

## Replay logic

### 1. Same-row-set replay

Replay must use the exact same row set as 346B4:

```text
replay_input_row_count = 500
same_row_set_replay = true
new_row_selected_count = 0
```

No row should be dropped silently. Counts must close.

---

### 2. Patch application

Apply only 346B3R patch proposals that passed patch safety review.

For each patched row, preserve:

```text
previous_346b4_decision
previous_semantic_class
patched_semantic_class
previous_unit_action
patched_unit_action
patch_source
patch_reason
patch_confidence
```

Rows that were not part of the 346B3R patchable set should remain governed by the 346B4 baseline rules.

---

### 3. Guardrail re-check

Every row must be classified into exactly one replay decision:

```text
REPLAY_SAFE_RECOVERED_DEMO_CANDIDATE
REPLAY_STILL_QUALITY_LIMITED
REPLAY_NEEDS_HUMAN_REVIEW
REPLAY_NEEDS_RULE_REFINEMENT
REPLAY_NEEDS_VLM_REPAIR
REPLAY_FALSE_POSITIVE_GUARDRAIL_HIT
```

A row can be replay-safe only if:

- semantic class is known;
- unit policy is compatible;
- value is parseable or already valid;
- source lineage is preserved;
- period/source trace is present;
- evidence or deterministic proof is sufficient;
- no unit semantic mismatch exists;
- no false-positive guardrail is triggered;
- output remains sidecar/demo-only.

---

### 4. Delta analysis

Compare replay results against 346B4:

Required deltas:

```text
safe_recovered_delta = replay_safe_recovered_count - previous_safe_recovered_count
unknown_delta = replay_semantic_class_unknown_count - previous_unknown_count
needs_rule_refinement_delta = replay_needs_rule_refinement_count - previous_needs_rule_refinement_count
still_limited_delta = replay_still_quality_limited_count - previous_still_quality_limited_count
```

Expected improvement:

```text
previous_unknown_count = 22
replay_unknown_count = 0 or materially reduced
patch_regression_count = 0
false_positive_guardrail_hit_count = 0
unit_semantic_mismatch_count = 0
```

---

## Outputs

Write only under:

```text
D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r
```

Generate:

- `controlled_expansion_replay_with_patched_rules_346b4r_manifest.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_replay_results.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_replay_results.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_delta_report.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_delta_report.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_executive_summary.md`
- `controlled_expansion_replay_with_patched_rules_346b4r_artifact_index.md`
- `controlled_expansion_replay_with_patched_rules_346b4r_next_plan.md`

Do not modify 346B4 or 346B3R outputs.

---

## Manifest metrics

Manifest must include:

```text
decision = CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY
input_stage = POST_346B3R_CONTROLLED_EXPANSION_REPLAY
qa_fail_count = 0
no_write_back_proof_passed = true
input_346b4_decision = CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY
input_346b3r_decision = RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY
input_346b4_safe_to_continue_expansion = false
input_346b3r_safe_to_replay_346b4 = true
previous_controlled_expansion_input_row_count = 500
replay_input_row_count = 500
same_row_set_replay = true
new_row_selected_count = 0
previous_safe_recovered_candidate_count = 212
replay_safe_recovered_candidate_count
safe_recovered_delta
previous_semantic_class_unknown_count = 22
replay_semantic_class_unknown_count
unknown_resolved_count
needs_rule_refinement_previous_count = 22
needs_rule_refinement_replay_count
needs_rule_refinement_delta
patch_applied_row_count
patch_regression_count
false_positive_guardrail_hit_count
unit_semantic_mismatch_count
evidence_weakness_count
lineage_audit_passed
safe_to_continue_expansion
safe_to_continue_expansion_reason
recommended_next_step
live_vlm_call_count = 0
vlm_response_count = 0
official_rules_modified = false
official_alias_assets_modified = false
formal_export_generated = false
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
global_strict_human_review_completed = false
upstream_data_mutated = false
milestone_ledger_updated = true
```

If replay is safe and unknowns are resolved with no regression, `safe_to_continue_expansion` may become true. The next step should still be controlled QA or larger expansion with guardrails, not formal production.

---

## Reports

Executive summary must explain:

- why 346B4R follows 346B3R;
- whether the same 500-row set was replayed;
- how many rows received patched rules;
- how many previously unknown rows were resolved;
- safe recovered candidate count before vs after;
- remaining unknown / rule-refinement count;
- guardrail and unit mismatch results;
- lineage/evidence audit result;
- whether controlled expansion can continue;
- why no live VLM/OCR/MinerU rerun happened;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B4Q Controlled Expansion QA Audit` if replay produced safe candidates and expansion can continue;
- `346B5 Larger Quality-Limited Recovery Expansion` only after QA audit confirms safety;
- `346B3R2 Recovery Rule Refinement Patch Follow-up` if unknowns or regressions remain;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B4R_controlled_expansion_replay_with_patched_rules.md`
- `datefac/benchmark/controlled_expansion_replay_with_patched_rules_346b4r.py`
- `datefac/benchmark/controlled_expansion_replay_with_patched_rules_346b4r_report.py`
- `tools/run_controlled_expansion_replay_with_patched_rules_346b4r.py`
- `tests/benchmark/test_controlled_expansion_replay_with_patched_rules_346b4r.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required.

---

## Forbidden

Do not:

- call live VLM/LLM APIs
- run OCR
- rerun MinerU
- mutate 345D outputs
- mutate 346B4 outputs
- mutate 346B3R outputs
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B4R output dir
- auto commit/push/merge
- use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`

Do not touch protected dirty files:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
- `tools/mineru_new_runner.cmd`

---

## Validation

Run:

```powershell
python -m py_compile datefac\benchmark\controlled_expansion_replay_with_patched_rules_346b4r.py datefac\benchmark\controlled_expansion_replay_with_patched_rules_346b4r_report.py tools\run_controlled_expansion_replay_with_patched_rules_346b4r.py tests\benchmark\test_controlled_expansion_replay_with_patched_rules_346b4r.py
python -m pytest tests\benchmark\test_controlled_expansion_replay_with_patched_rules_346b4r.py -q
python tools\run_controlled_expansion_replay_with_patched_rules_346b4r.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4 --recovery-rule-refinement-patch-346b3r-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r --output-dir D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r
```

Tests must verify:

- outputs exist;
- valid 345D/346B4/346B3R inputs produce READY;
- invalid required inputs fail clearly;
- exact same 500-row set is replayed;
- no new rows are selected;
- patch proposals are applied only to eligible rows;
- unknown count decreases or remains explicitly explained;
- guardrail hits prevent promotion;
- no ratio/multiple or per-share row receives `%`;
- counts close across replay decisions;
- raw values and source lineage are preserved;
- no official rules/assets are modified;
- no prior outputs are mutated;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B4R entry.

---

## Completion report

Report:

1. Files changed.
2. Milestone ledger update summary.
3. py_compile result.
4. pytest result.
5. real runner result.
6. output dir.
7. decision and QA metrics.
8. same-row-set replay proof.
9. previous vs replay safe recovered count.
10. previous vs replay unknown / rule-refinement count.
11. patch applied / regression counts.
12. guardrail and unit mismatch counts.
13. lineage/evidence audit result.
14. safe-to-continue expansion flag and reason.
15. live VLM call count.
16. official rules/assets modified flags.
17. formal export generated / demo export only flags.
18. final gate status.
19. first file to open.
20. next recommended step.
21. `git status -sb`.
22. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
