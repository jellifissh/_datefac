# 346B5Q Larger Expansion QA Audit

## Goal

Implement `346B5Q Larger Expansion QA Audit`.

346B5 expanded the QA-cleared recovery policy from the 500-row controlled batch to a bounded 1500-row larger quality-limited batch and produced:

```text
decision = LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION_346B5_READY
qa_fail_count = 0
no_write_back_proof_passed = true
full_quality_limited_row_count = 5558
larger_expansion_input_limit = 1500
larger_expansion_input_row_count = 1500
excluded_row_touched_count = 0
already_demo_ready_row_touched_count = 0
already_346b_pilot_row_count = 0
already_346b4_controlled_batch_row_count = 984
new_quality_limited_row_count = 1500
value_sanitizer_attempt_count = 1500
sanitized_value_success_count = 1500
sanitized_value_failure_count = 0
semantic_class_known_count = 1500
semantic_class_unknown_count = 0
unit_repair_attempt_count = 574
unit_repair_success_count = 1500
unit_semantic_mismatch_count = 0
recovered_candidate_count = 1500
safe_recovered_candidate_count = 1500
risky_candidate_count = 0
false_positive_guardrail_hit_count = 0
still_quality_limited_count = 0
needs_human_review_count = 0
needs_rule_refinement_count = 0
needs_vlm_count = 0
lineage_audit_passed = true
evidence_weakness_count = 0
safe_to_qa_larger_expansion = true
recommended_next_step = 346B5Q Larger Expansion QA Audit
live_vlm_call_count = 0
```

346B5 semantic distribution:

```text
MONETARY_AMOUNT = 926
PERCENTAGE_OR_MARGIN = 319
PER_SHARE = 67
RATIO_MULTIPLE = 188
```

346B5 unit action distribution:

```text
NO_CHANGE = 926
UNIT_PERCENT_FROM_MARGIN_CONTEXT = 319
UNIT_PER_SHARE_CONTEXT = 67
UNIT_RATIO_MULTIPLE_X = 188
```

346B5Q must answer:

> Do the 1500 larger-expansion safe recovered candidates from 346B5 pass an independent QA audit with zero false-positive suspects, zero semantic/unit mismatches, no double-counting risk, intact lineage/evidence, and enough confidence to allow a later full quality-limited recovery expansion?

This is an independent QA audit. It must not recover new rows, select new rows, mutate upstream outputs, modify official rules/assets, or open any formal/client/production gate.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Larger expansions must be independently audited before full expansion.
- Treat `1500 / 1500 safe` as a result to verify, not a result to trust blindly.
- Preserve raw values and source lineage.
- Do not trust a row merely because 346B5 marked it safe.
- Guardrails must remain strict.
- Double-counting and previous-batch leakage must be audited explicitly.
- Do not call live VLM/LLM APIs.
- Do not run OCR.
- Do not rerun MinerU.
- Do not write back to upstream datasets.
- Do not modify official normalization rules or official alias assets.
- Keep all formal/client/production gates closed.

346B5Q is not a full expansion. It is the QA gate after the 1500-row larger controlled expansion.

---

## Critical audit concern

346B5 reported:

```text
exclude_previous_controlled_batch = true
already_346b4_controlled_batch_row_count = 984
new_quality_limited_row_count = 1500
```

346B5Q must resolve this ambiguity.

Audit and classify the meaning of `already_346b4_controlled_batch_row_count = 984`:

```text
PREVIOUS_BATCH_EXCLUDED_REFERENCE_COUNT
PREVIOUS_BATCH_INCLUDED_DUPLICATE_COUNT
FIELD_NAMING_AMBIGUITY_ONLY
AUDIT_INCONCLUSIVE
```

The expected safe interpretation is that 984 refers to previous-batch rows detected/excluded during selection or eligibility accounting, not 984 rows included in the 1500 candidate set.

If any 346B/346B4/346B4R/346B4Q row is actually included and counted again in 346B5 candidates without explicit regression/reference marking, count it as double-counting risk.

Manifest must include:

```text
previous_batch_overlap_audited = true
previous_batch_overlap_interpretation
double_counting_risk_count
previous_346b_overlap_in_candidates_count
previous_346b4_overlap_in_candidates_count
previous_346b4r_overlap_in_candidates_count
previous_346b4q_overlap_in_candidates_count
```

If `double_counting_risk_count > 0`, `qa_safe_to_full_quality_limited_expansion` must be false.

---

## Current context

345D full structured demo export package:

```text
D:\_datefac\output\full_structured_demo_export_package_345d
```

346B4 controlled expansion output:

```text
D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
```

346B3R rule patch output:

```text
D:\_datefac\output\recovery_rule_refinement_patch_346b3r
```

346B4R replay output:

```text
D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r
```

346B4Q QA audit output:

```text
D:\_datefac\output\controlled_expansion_qa_audit_346b4q
```

346B5 larger expansion output:

```text
D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5
```

346B5Q output:

```text
D:\_datefac\output\larger_expansion_qa_audit_346b5q
```

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B5Q entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B5Q`
- decision: `LARGER_EXPANSION_QA_AUDIT_346B5Q_READY`
- input dirs: 345D, 346B4, 346B3R, 346B4R, 346B4Q, 346B5
- output dir
- 346B5 input row count
- 346B5 safe recovered candidate count
- QA audited candidate count
- QA safe candidate count
- QA risky candidate count
- QA false-positive suspect count
- QA needs human review count
- QA needs rule refinement count
- semantic class disagreement count
- unit semantic mismatch count
- false-positive guardrail hit count
- evidence weakness count
- lineage audit passed
- previous-batch overlap audited flag
- previous-batch overlap interpretation
- double-counting risk count
- previous 346B/346B4/346B4R/346B4Q overlap-in-candidates counts
- semantic class distribution audit counts
- unit action distribution audit counts
- QA safe-to-full-quality-limited-expansion flag
- recommended next step
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false

If the ledger has unrelated dirty changes, append only the 346B5Q entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B5Q_larger_expansion_qa_audit.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346B4 output dir
- 346B3R output dir
- 346B4R output dir
- 346B4Q output dir
- 346B5 output dir
- milestone ledger
- root tactical playbook

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
--recovery-rule-refinement-patch-346b3r-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r
--controlled-expansion-replay-with-patched-rules-346b4r-dir D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r
--controlled-expansion-qa-audit-346b4q-dir D:\_datefac\output\controlled_expansion_qa_audit_346b4q
--larger-quality-limited-recovery-expansion-346b5-dir D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5
--output-dir D:\_datefac\output\larger_expansion_qa_audit_346b5q
```

Optional knobs:

```powershell
--strict-qa true
--audit-all-candidates true
--audit-double-counting true
--audit-unit-semantics true
--audit-lineage-evidence true
--safe-to-full-expansion-risk-threshold 0
--max-context-chars 4000
```

Default behavior:

- require 346B5 decision READY;
- require 346B5 `safe_to_qa_larger_expansion = true`;
- read all 1500 346B5 safe recovered candidates;
- independently QA all 1500 candidates;
- independently re-check semantic class and unit compatibility;
- audit distribution closure against 346B5 semantic/unit distributions;
- audit previous-batch overlaps/double-counting;
- audit raw value and lineage preservation;
- audit evidence or deterministic proof availability;
- output QA sidecars only;
- do not recover new rows;
- do not select new rows;
- do not mutate 345D/346B4/346B3R/346B4R/346B4Q/346B5 outputs;
- do not modify official rules/assets;
- do not call live VLM/LLM APIs;
- do not run OCR;
- do not rerun MinerU.

---

## Inputs to read

From 346B5:

- `larger_quality_limited_recovery_expansion_346b5_manifest.json`
- `larger_quality_limited_recovery_expansion_346b5_selected_rows.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_recovery_results.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_recovered_demo_candidates.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_safe_recovered_candidates.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_still_limited_rows.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_needs_human_review_rows.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_needs_rule_refinement_rows.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_false_positive_guardrail_hits.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_semantic_class_distribution.json`
- `larger_quality_limited_recovery_expansion_346b5_unit_action_distribution.json`
- `larger_quality_limited_recovery_expansion_346b5_lineage_evidence_audit.json` or `.csv`
- `larger_quality_limited_recovery_expansion_346b5_guardrail_summary.json`
- `larger_quality_limited_recovery_expansion_346b5_expansion_readiness_report.json`

From earlier stages for overlap/double-counting audit:

- 346B4 selected/recovery/safe candidate files;
- 346B4R safe recovered candidates and patched rows;
- 346B4Q QA safe candidates and patch-applied row QA;
- 345D quality-limited/demo/excluded row sets if available.

Validate:

- 346B5 decision is `LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION_346B5_READY`;
- 346B5 `qa_fail_count = 0`;
- 346B5 `safe_to_qa_larger_expansion = true`;
- 346B5 `larger_expansion_input_row_count = 1500`;
- 346B5 `safe_recovered_candidate_count = 1500`;
- 346B5 `semantic_class_unknown_count = 0`;
- 346B5 `unit_semantic_mismatch_count = 0`;
- 346B5 `false_positive_guardrail_hit_count = 0`;
- 346B5 `lineage_audit_passed = true`;
- 346B5 all live VLM/OCR/MinerU rerun counts are zero or absent with no-call proof;
- all formal/client/production gates are false.

---

## QA logic

### 1. Candidate QA closure

Audit all 346B5 safe candidates:

```text
qa_audited_candidate_count = 1500
```

Each candidate receives exactly one QA decision:

```text
QA_SAFE_RECOVERED_DEMO_CANDIDATE
QA_RISKY_RECOVERED_DEMO_CANDIDATE
QA_FALSE_POSITIVE_SUSPECT
QA_NEEDS_HUMAN_REVIEW
QA_NEEDS_RULE_REFINEMENT
```

Counts must close against 1500.

---

### 2. Semantic/unit independent re-check

Independently re-check semantic class and unit policy compatibility.

Expected semantic class distribution from 346B5:

```text
MONETARY_AMOUNT = 926
PERCENTAGE_OR_MARGIN = 319
PER_SHARE = 67
RATIO_MULTIPLE = 188
```

Expected unit action distribution from 346B5:

```text
NO_CHANGE = 926
UNIT_PERCENT_FROM_MARGIN_CONTEXT = 319
UNIT_PER_SHARE_CONTEXT = 67
UNIT_RATIO_MULTIPLE_X = 188
```

Required checks:

- `RATIO_MULTIPLE` rows must not receive `%`;
- `PER_SHARE` rows must not receive `%`;
- `PERCENTAGE_OR_MARGIN` rows must have justified `%`/percentage actions;
- `MONETARY_AMOUNT` rows must not receive ratio/multiple/percent units;
- unknown semantic class must not be marked QA safe;
- any distribution mismatch must be counted and explained.

---

### 3. Double-counting and previous-batch overlap audit

Build row identity keys using the strongest available fields, for example:

```text
row_id
source_row_id
file_id / source_file / pdf_name
page_index / table_id / row_index
raw_metric_name
period
raw_value
```

Audit overlap against:

- 346B 100-row pilot if row identity is available;
- 346B4 selected 500-row controlled batch;
- 346B4R safe recovered candidates and patched rows;
- 346B4Q QA safe candidates.

Manifest must include overlap counts and interpretation. If overlap files are unavailable, report `overlap_audit_limitations`, but do not silently pass ambiguity.

Any unmarked overlap in 346B5 safe candidates counts as double-counting risk.

---

### 4. Lineage/evidence audit

Verify every QA-safe candidate preserves:

```text
source_row_id
raw_metric_name
normalized or demo-normalized metric surrogate
raw_value
sanitized/final value
semantic class
unit action
period/source trace when available
previous 345D quality-limited lineage
346B5 recovery decision
```

Evidence can be image-bound, JSON/MD/context-bound, or deterministic-proof based. Rows with no evidence and no deterministic proof must not be QA safe.

---

### 5. Full expansion readiness

Set:

```text
qa_safe_to_full_quality_limited_expansion = true
```

only if:

- all 1500 candidates are QA safe;
- false-positive suspects are zero;
- semantic/unit mismatches are zero;
- double-counting risk is zero;
- semantic distribution audit closes;
- unit action distribution audit closes;
- lineage/evidence audit passes;
- no live VLM/OCR/MinerU rerun occurred;
- all formal/client/production gates remain false.

If true, recommend:

```text
346B6 Full Quality-Limited Recovery Expansion
```

If false, recommend either rule refinement or 346B5R/346B5Q2 follow-up depending on failure mode.

---

## Outputs

Write only under:

```text
D:\_datefac\output\larger_expansion_qa_audit_346b5q
```

Generate:

- `larger_expansion_qa_audit_346b5q_manifest.json`
- `larger_expansion_qa_audit_346b5q_candidate_qa.json`
- `larger_expansion_qa_audit_346b5q_candidate_qa.csv`
- `larger_expansion_qa_audit_346b5q_qa_safe_candidates.json`
- `larger_expansion_qa_audit_346b5q_qa_safe_candidates.csv`
- `larger_expansion_qa_audit_346b5q_qa_risky_candidates.json`
- `larger_expansion_qa_audit_346b5q_qa_risky_candidates.csv`
- `larger_expansion_qa_audit_346b5q_false_positive_suspects.json`
- `larger_expansion_qa_audit_346b5q_false_positive_suspects.csv`
- `larger_expansion_qa_audit_346b5q_semantic_unit_recheck.json`
- `larger_expansion_qa_audit_346b5q_semantic_unit_recheck.csv`
- `larger_expansion_qa_audit_346b5q_distribution_audit.json`
- `larger_expansion_qa_audit_346b5q_distribution_audit.csv`
- `larger_expansion_qa_audit_346b5q_previous_batch_overlap_audit.json`
- `larger_expansion_qa_audit_346b5q_previous_batch_overlap_audit.csv`
- `larger_expansion_qa_audit_346b5q_lineage_evidence_audit.json`
- `larger_expansion_qa_audit_346b5q_lineage_evidence_audit.csv`
- `larger_expansion_qa_audit_346b5q_full_expansion_readiness_report.json`
- `larger_expansion_qa_audit_346b5q_executive_summary.md`
- `larger_expansion_qa_audit_346b5q_artifact_index.md`
- `larger_expansion_qa_audit_346b5q_next_plan.md`

Do not modify 346B5 outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = LARGER_EXPANSION_QA_AUDIT_346B5Q_READY
input_stage = POST_346B5_LARGER_EXPANSION_QA_AUDIT
qa_fail_count = 0
no_write_back_proof_passed = true
input_345d_decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY
input_346b4_decision = CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY
input_346b3r_decision = RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY
input_346b4r_decision = CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY
input_346b4q_decision = CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_READY
input_346b5_decision = LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION_346B5_READY
input_346b5_safe_to_qa_larger_expansion = true
full_quality_limited_row_count = 5558
larger_expansion_input_row_count = 1500
larger_expansion_safe_recovered_candidate_count = 1500
qa_audited_candidate_count
qa_safe_candidate_count
qa_risky_candidate_count
qa_false_positive_suspect_count
qa_needs_human_review_count
qa_needs_rule_refinement_count
semantic_class_disagreement_count
unit_semantic_mismatch_count
false_positive_guardrail_hit_count
evidence_weakness_count
lineage_audit_passed
previous_batch_overlap_audited
previous_batch_overlap_interpretation
double_counting_risk_count
previous_346b_overlap_in_candidates_count
previous_346b4_overlap_in_candidates_count
previous_346b4r_overlap_in_candidates_count
previous_346b4q_overlap_in_candidates_count
semantic_distribution_audit_passed
unit_action_distribution_audit_passed
qa_safe_to_full_quality_limited_expansion
qa_safe_to_full_quality_limited_expansion_reason
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

If QA finds risks, the task can still be READY if QA completes, but `qa_safe_to_full_quality_limited_expansion` must be false and the next step must be a follow-up audit/refinement, not 346B6.

---

## Reports

Executive summary must explain:

- why 346B5Q follows 346B5;
- why `1500 / 1500 safe` needed independent QA;
- how many candidates were audited;
- QA safe/risky/false-positive/human-review/rule-refinement counts;
- semantic/unit recheck results;
- distribution audit results;
- previous-batch overlap and double-counting result;
- interpretation of `already_346b4_controlled_batch_row_count = 984`;
- lineage/evidence audit result;
- whether full quality-limited expansion is allowed;
- why no live VLM/OCR/MinerU rerun happened;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B6 Full Quality-Limited Recovery Expansion` if QA confirms full expansion readiness;
- `346B5R Larger Expansion Replay/Selection Fix` if overlap/double-counting or selection ambiguity exists;
- `346B3R2 Recovery Rule Refinement Patch Follow-up` if semantic/unit issues remain;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `347A MinerU 3.3.1 Side-by-Side Compatibility Benchmark` if the team chooses to evaluate MinerU upgrade in parallel;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B5Q_larger_expansion_qa_audit.md`
- `datefac/benchmark/larger_expansion_qa_audit_346b5q.py`
- `datefac/benchmark/larger_expansion_qa_audit_346b5q_report.py`
- `tools/run_larger_expansion_qa_audit_346b5q.py`
- `tests/benchmark/test_larger_expansion_qa_audit_346b5q.py`
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
- mutate 346B4Q outputs
- mutate 346B5 outputs
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B5Q output dir
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
python -m py_compile datefac\benchmark\larger_expansion_qa_audit_346b5q.py datefac\benchmark\larger_expansion_qa_audit_346b5q_report.py tools\run_larger_expansion_qa_audit_346b5q.py tests\benchmark\test_larger_expansion_qa_audit_346b5q.py
python -m pytest tests\benchmark\test_larger_expansion_qa_audit_346b5q.py -q
python tools\run_larger_expansion_qa_audit_346b5q.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4 --recovery-rule-refinement-patch-346b3r-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r --controlled-expansion-replay-with-patched-rules-346b4r-dir D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r --controlled-expansion-qa-audit-346b4q-dir D:\_datefac\output\controlled_expansion_qa_audit_346b4q --larger-quality-limited-recovery-expansion-346b5-dir D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5 --output-dir D:\_datefac\output\larger_expansion_qa_audit_346b5q
```

Tests must verify:

- outputs exist;
- valid inputs produce READY;
- invalid required inputs fail clearly;
- 346B5 `safe_to_qa_larger_expansion` is required;
- all 1500 candidates are QA audited;
- QA counts close;
- semantic distribution closes;
- unit action distribution closes;
- ratio/multiple rows are not assigned `%`;
- per-share rows are not assigned `%`;
- no unknown semantic class is QA safe;
- previous-batch overlap audit is performed;
- double-counting risk blocks full expansion readiness;
- raw values and source lineage are preserved;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- official rules/assets flags remain false;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B5Q entry.

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
8. QA audited candidate count.
9. QA safe/risky/false-positive/human-review/rule-refinement counts.
10. semantic/unit recheck counts.
11. distribution audit result.
12. previous-batch overlap audit result and interpretation of `already_346b4_controlled_batch_row_count = 984`.
13. double-counting risk count.
14. lineage/evidence audit result.
15. QA safe-to-full-quality-limited-expansion flag and reason.
16. live VLM call count.
17. official rules/assets modified flags.
18. formal export generated / demo export only flags.
19. final gate status.
20. first file to open.
21. next recommended step.
22. `git status -sb`.
23. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
