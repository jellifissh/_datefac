# 346B4Q Controlled Expansion QA Audit

## Goal

Implement `346B4Q Controlled Expansion QA Audit`.

346B4 performed a controlled 500-row quality-limited expansion and produced:

```text
controlled_expansion_input_row_count = 500
safe_recovered_candidate_count = 212
false_positive_guardrail_hit_count = 0
unit_semantic_mismatch_count = 0
semantic_class_unknown_count = 22
needs_rule_refinement_count = 22
safe_to_continue_expansion = false
```

346B3R audited the 22 unknown/refinement rows and proposed sidecar classifier/unit-policy patches:

```text
audited_unknown_row_count = 22
patchable_rule_gap_count = 22
rows_converted_from_unknown_to_known_semantic_class_count = 22
patch_requires_reaudit_count = 22
safe_to_replay_346b4 = true
safe_to_continue_expansion = false
```

346B4R replayed the exact same 500-row controlled batch using the 346B3R sidecar patches and produced:

```text
previous_controlled_expansion_input_row_count = 500
replay_input_row_count = 500
same_row_set_replay = true
new_row_selected_count = 0
previous_safe_recovered_candidate_count = 212
replay_safe_recovered_candidate_count = 234
safe_recovered_delta = 22
previous_semantic_class_unknown_count = 22
replay_semantic_class_unknown_count = 0
unknown_resolved_count = 22
needs_rule_refinement_previous_count = 22
needs_rule_refinement_replay_count = 0
patch_applied_row_count = 22
patch_regression_count = 0
false_positive_guardrail_hit_count = 0
unit_semantic_mismatch_count = 0
evidence_weakness_count = 0
lineage_audit_passed = true
safe_to_continue_expansion = true
live_vlm_call_count = 0
```

346B4Q must answer:

> Do the 234 replay-safe recovered candidates from 346B4R, including the 22 patch-applied rows, pass an independent QA audit with zero false-positive suspects, zero unit semantic mismatches, intact lineage/evidence, and enough confidence to allow a larger controlled expansion step?

This is an independent QA audit of the 346B4R replay results. It must not select new rows, must not recover new rows, must not modify official rules/assets, and must not mutate upstream data.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Replay outputs must be independently audited before larger expansion.
- Patch-applied rows deserve extra scrutiny.
- Preserve raw values and source lineage.
- Do not trust a row merely because the replay marked it safe.
- Guardrails must remain strict.
- Do not call live VLM/LLM APIs.
- Do not run OCR.
- Do not rerun MinerU.
- Do not write back to upstream datasets.
- Do not modify official normalization rules or official alias assets.
- Keep all formal/client/production gates closed.

346B4Q is not an expansion. It is the QA gate after 346B4R.

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

346B4Q output:

```text
D:\_datefac\output\controlled_expansion_qa_audit_346b4q
```

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B4Q entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B4Q`
- decision: `CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_READY`
- input 345D dir
- input 346B4 dir
- input 346B3R dir
- input 346B4R dir
- output dir
- replay input row count
- replay safe recovered candidate count
- QA audited candidate count
- QA safe candidate count
- QA risky candidate count
- QA false-positive suspect count
- patch-applied audited row count
- patch-applied QA pass count
- patch-applied QA risk count
- semantic class disagreement count
- unit semantic mismatch count
- false-positive guardrail hit count
- evidence weakness count
- lineage audit passed
- QA safe-to-larger-expansion flag
- recommended next step
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false

If the ledger has unrelated dirty changes, append only the 346B4Q entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B4Q_controlled_expansion_qa_audit.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346B4 output dir
- 346B3R output dir
- 346B4R output dir
- the milestone ledger
- the root tactical playbook

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
--recovery-rule-refinement-patch-346b3r-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r
--controlled-expansion-replay-with-patched-rules-346b4r-dir D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r
--output-dir D:\_datefac\output\controlled_expansion_qa_audit_346b4q
```

Optional knobs:

```powershell
--strict-qa true
--audit-patch-applied-rows true
--require-same-row-set-proof true
--require-lineage-preservation true
--require-evidence-or-deterministic-proof true
--safe-to-larger-expansion-risk-threshold 0
--max-context-chars 4000
```

Default behavior:

- read 346B4R manifest and replay results;
- read 346B4R safe recovered candidates;
- read 346B4R patched rows;
- read 346B4R guardrail hits, remaining unknowns, lineage/evidence audit, delta report, expansion readiness report;
- read 346B4 baseline results for before/after comparison;
- read 346B3R patch safety review and patch proposals;
- independently QA all 346B4R replay-safe recovered candidates;
- separately QA the 22 patch-applied rows;
- validate same-row-set replay proof;
- validate lineage/evidence preservation;
- validate unit semantic compatibility and guardrail status;
- output QA sidecar results only;
- do not select new rows;
- do not recover new rows;
- do not mutate 346B4/346B3R/346B4R outputs;
- do not modify official rules/assets;
- do not call live VLM/LLM APIs;
- do not run OCR;
- do not rerun MinerU.

---

## Inputs to read

From 346B4R:

- `controlled_expansion_replay_with_patched_rules_346b4r_manifest.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_replay_results.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_delta_report.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json`

From 346B4:

- `controlled_quality_limited_recovery_expansion_346b4_manifest.json`
- `controlled_quality_limited_recovery_expansion_346b4_selected_rows.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_recovery_results.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json`

From 346B3R:

- `recovery_rule_refinement_patch_346b3r_manifest.json`
- `recovery_rule_refinement_patch_346b3r_patchable_rows.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_patch_safety_review.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_replay_readiness_report.json`

From 345D if needed:

- `full_structured_demo_export_package_345d_manifest.json`
- quality-limited rows only for row id/context lookup

Validate:

- 346B4 decision is `CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY`
- 346B3R decision is `RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY`
- 346B4R decision is `CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY`
- 346B4R `qa_fail_count = 0`
- 346B4R `same_row_set_replay = true`
- 346B4R `new_row_selected_count = 0`
- 346B4R `safe_to_continue_expansion = true`
- 346B4R `replay_safe_recovered_candidate_count = 234`
- 346B4R `patch_applied_row_count = 22`
- 346B4R `false_positive_guardrail_hit_count = 0`
- 346B4R `unit_semantic_mismatch_count = 0`
- 346B4R `lineage_audit_passed = true`
- all live VLM call counts are `0`
- all formal/client/production gates are false

---

## QA logic

### 1. Same-row-set and replay closure

Confirm:

```text
previous_controlled_expansion_input_row_count = 500
replay_input_row_count = 500
same_row_set_replay = true
new_row_selected_count = 0
```

Do not audit a different row set.

---

### 2. Candidate QA closure

QA all replay-safe candidates:

```text
replay_safe_recovered_candidate_count = 234
qa_audited_candidate_count = 234
```

Each audited candidate receives exactly one QA decision:

```text
QA_SAFE_RECOVERED_DEMO_CANDIDATE
QA_RISKY_RECOVERED_DEMO_CANDIDATE
QA_FALSE_POSITIVE_SUSPECT
QA_NEEDS_HUMAN_REVIEW
QA_NEEDS_RULE_REFINEMENT
```

Counts must close against `qa_audited_candidate_count`.

---

### 3. Patch-applied row QA

The 22 patch-applied rows need separate QA:

```text
patch_applied_row_count = 22
patch_applied_audited_row_count = 22
```

For each patch-applied row verify:

- previous 346B4 decision was `needs_rule_refinement` or semantic unknown;
- 346B3R proposed patch exists;
- 346B4R applied the patch;
- semantic class is now known;
- unit policy is compatible;
- no false-positive guardrail is triggered;
- lineage/evidence are intact;
- the row remains sidecar/demo-only.

Patch-applied rows should be marked:

```text
PATCH_QA_PASS
PATCH_QA_RISK
PATCH_QA_FAIL
```

---

### 4. Independent semantic/unit re-check

Do not simply trust 346B4R labels. Recompute semantic class and unit compatibility independently where fields are available.

Check:

- ratio/multiple rows do not receive `%`;
- per-share rows do not receive `%`;
- percentage/margin rows have compatible `%` only when justified;
- monetary rows do not receive ratio/multiple or percent units;
- count/volume rows have count/volume-compatible units or remain limited;
- unknown semantic class is not marked safe.

Any disagreement must be counted.

---

### 5. Lineage/evidence audit

Verify every QA-safe candidate preserves:

```text
source_row_id
raw_metric_name
demo_normalized_metric_name or normalized metric surrogate
raw_value
sanitized_value or final value
period/source trace when available
previous 346B4 decision
replay 346B4R decision
patch source if patched
```

Evidence may be image-bound, JSON/MD/context-bound, or deterministic proof based, but rows with no evidence and no deterministic proof must not be QA-safe.

---

### 6. Larger expansion readiness

Set:

```text
qa_safe_to_larger_expansion = true
```

only if:

- QA candidate closure passes;
- patch-applied QA passes;
- no QA false-positive suspects remain;
- no unit semantic mismatches remain;
- no semantic unknown safe rows remain;
- lineage/evidence audit passes;
- all formal/client/production gates remain false;
- no live VLM/OCR/MinerU rerun occurred.

If true, recommend a larger but still controlled expansion, not formal production.

Recommended next step:

```text
346B5 Larger Quality-Limited Recovery Expansion
```

with a row limit such as 1500 or 2000 before full 5558 expansion.

---

## Outputs

Write only under:

```text
D:\_datefac\output\controlled_expansion_qa_audit_346b4q
```

Generate:

- `controlled_expansion_qa_audit_346b4q_manifest.json`
- `controlled_expansion_qa_audit_346b4q_candidate_qa.json`
- `controlled_expansion_qa_audit_346b4q_candidate_qa.csv`
- `controlled_expansion_qa_audit_346b4q_qa_safe_candidates.json`
- `controlled_expansion_qa_audit_346b4q_qa_safe_candidates.csv`
- `controlled_expansion_qa_audit_346b4q_qa_risky_candidates.json`
- `controlled_expansion_qa_audit_346b4q_qa_risky_candidates.csv`
- `controlled_expansion_qa_audit_346b4q_false_positive_suspects.json`
- `controlled_expansion_qa_audit_346b4q_false_positive_suspects.csv`
- `controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.json`
- `controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.csv`
- `controlled_expansion_qa_audit_346b4q_semantic_unit_recheck.json`
- `controlled_expansion_qa_audit_346b4q_semantic_unit_recheck.csv`
- `controlled_expansion_qa_audit_346b4q_lineage_evidence_audit.json`
- `controlled_expansion_qa_audit_346b4q_lineage_evidence_audit.csv`
- `controlled_expansion_qa_audit_346b4q_larger_expansion_readiness_report.json`
- `controlled_expansion_qa_audit_346b4q_reaudit_summary.json`
- `controlled_expansion_qa_audit_346b4q_executive_summary.md`
- `controlled_expansion_qa_audit_346b4q_artifact_index.md`
- `controlled_expansion_qa_audit_346b4q_next_plan.md`

Do not modify 346B4R outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_READY
input_stage = POST_346B4R_CONTROLLED_EXPANSION_QA_AUDIT
qa_fail_count = 0
no_write_back_proof_passed = true
input_345d_decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY
input_346b4_decision = CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY
input_346b3r_decision = RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY
input_346b4r_decision = CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY
input_346b4r_safe_to_continue_expansion = true
same_row_set_replay_verified = true
new_row_selected_count = 0
replay_input_row_count = 500
replay_safe_recovered_candidate_count = 234
qa_audited_candidate_count
qa_safe_candidate_count
qa_risky_candidate_count
qa_false_positive_suspect_count
qa_needs_human_review_count
qa_needs_rule_refinement_count
patch_applied_audited_row_count
patch_applied_qa_pass_count
patch_applied_qa_risk_count
patch_applied_qa_fail_count
semantic_class_disagreement_count
unit_semantic_mismatch_count
false_positive_guardrail_hit_count
evidence_weakness_count
lineage_audit_passed
qa_safe_to_larger_expansion
qa_safe_to_larger_expansion_reason
recommended_larger_expansion_row_limit
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

If QA fails, the task can still be READY if QA passes technically, but `qa_safe_to_larger_expansion` must be false and the next step must be refinement/audit, not larger expansion.

---

## Reports

Executive summary must explain:

- why 346B4Q follows 346B4R;
- how many replay-safe candidates were audited;
- safe/risky/false-positive QA counts;
- patch-applied row QA results;
- semantic/unit recheck results;
- lineage/evidence audit results;
- whether larger expansion is allowed;
- recommended larger expansion row limit;
- why no live VLM/OCR/MinerU rerun happened;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B5 Larger Quality-Limited Recovery Expansion` if QA confirms larger expansion readiness;
- `346B3R2 Recovery Rule Refinement Patch Follow-up` if patch-applied rows or semantic/unit checks fail;
- `346B4R2 Controlled Expansion Replay Follow-up` if replay issues remain;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B4Q_controlled_expansion_qa_audit.md`
- `datefac/benchmark/controlled_expansion_qa_audit_346b4q.py`
- `datefac/benchmark/controlled_expansion_qa_audit_346b4q_report.py`
- `tools/run_controlled_expansion_qa_audit_346b4q.py`
- `tests/benchmark/test_controlled_expansion_qa_audit_346b4q.py`
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
- mutate 346B4R outputs
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B4Q output dir
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
python -m py_compile datefac\benchmark\controlled_expansion_qa_audit_346b4q.py datefac\benchmark\controlled_expansion_qa_audit_346b4q_report.py tools\run_controlled_expansion_qa_audit_346b4q.py tests\benchmark\test_controlled_expansion_qa_audit_346b4q.py
python -m pytest tests\benchmark\test_controlled_expansion_qa_audit_346b4q.py -q
python tools\run_controlled_expansion_qa_audit_346b4q.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4 --recovery-rule-refinement-patch-346b3r-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r --controlled-expansion-replay-with-patched-rules-346b4r-dir D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r --output-dir D:\_datefac\output\controlled_expansion_qa_audit_346b4q
```

Tests must verify:

- outputs exist;
- valid 345D/346B4/346B3R/346B4R inputs produce READY;
- invalid required inputs fail clearly;
- 346B4R safe_to_continue_expansion is required;
- same-row-set replay proof is verified;
- 234 replay-safe candidates are QA-audited;
- 22 patch-applied rows are separately QA-audited;
- no ratio/multiple or per-share row receives `%`;
- QA counts close;
- patch-applied QA counts close;
- raw values and source lineage are preserved;
- no official rules/assets are modified;
- no prior outputs are mutated;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B4Q entry.

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
8. same-row-set replay verification.
9. QA audited candidate count.
10. QA safe/risky/false-positive/human-review/rule-refinement counts.
11. patch-applied row QA counts.
12. semantic/unit recheck counts.
13. lineage/evidence audit result.
14. QA safe-to-larger-expansion flag and reason.
15. recommended larger expansion row limit.
16. live VLM call count.
17. official rules/assets modified flags.
18. formal export generated / demo export only flags.
19. final gate status.
20. first file to open.
21. next recommended step.
22. `git status -sb`.
23. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
