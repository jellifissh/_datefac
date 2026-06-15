# 346B5 Larger Quality-Limited Recovery Expansion

## Goal

Implement `346B5 Larger Quality-Limited Recovery Expansion`.

346B4Q independently audited the 346B4R replay results and confirmed that the controlled 500-row expansion is safe enough for a larger controlled expansion:

```text
same_row_set_replay_verified = true
replay_input_row_count = 500
new_row_selected_count = 0
qa_audited_candidate_count = 234
qa_safe_candidate_count = 234
qa_risky_candidate_count = 0
qa_false_positive_suspect_count = 0
qa_needs_human_review_count = 0
qa_needs_rule_refinement_count = 0
patch_applied_audited_row_count = 22
patch_applied_qa_pass_count = 22
patch_applied_qa_risk_count = 0
patch_applied_qa_fail_count = 0
semantic_class_disagreement_count = 0
unit_semantic_mismatch_count = 0
false_positive_guardrail_hit_count = 0
lineage_audit_passed = true
evidence_weakness_count = 0
qa_safe_to_larger_expansion = true
recommended_larger_expansion_row_limit = 1500
recommended_next_step = 346B5 Larger Quality-Limited Recovery Expansion
live_vlm_call_count = 0
```

346B5 must answer:

> If the refined and QA-audited recovery policy is applied to a larger controlled subset of the 5558 quality-limited rows, capped at 1500 rows, how many additional demo-only recovery candidates can be produced safely without live VLM, OCR, MinerU rerun, upstream mutation, or formal client export?

This task is a larger controlled sidecar expansion, not a full production migration.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Work only on 345D quality-limited rows.
- Do not touch excluded rows.
- Do not touch already strict demo-ready rows.
- Avoid double-counting rows already processed in the 346B pilot and 346B4 controlled batch unless they are explicitly marked as regression/reference rows.
- Use the refined semantic-class-aware recovery policy from 346B3 plus 346B3R patch proposals validated by 346B4R and 346B4Q.
- Preserve raw values and source lineage.
- Treat all outputs as sidecar/demo-only suggestions.
- Keep guardrails strict.
- Do not call live VLM/LLM APIs.
- Do not run OCR.
- Do not rerun MinerU.
- Do not write back to upstream datasets.
- Do not modify official normalization rules or official alias assets.
- Keep all formal/client/production gates closed.

346B5 is allowed because 346B4Q confirmed `qa_safe_to_larger_expansion = true`, but it must remain controlled and sidecar-only.

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

346B5 output:

```text
D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5
```

Known quality-limited pool:

```text
full_quality_limited_row_count = 5558
```

Recommended larger expansion size:

```text
larger_expansion_input_limit = 1500
```

Do not expand directly to all 5558 rows by default. That belongs to a later step after 346B5 QA.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B5 entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B5`
- decision: `LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION_346B5_READY`
- input 345D dir
- input 346B4 dir
- input 346B3R dir
- input 346B4R dir
- input 346B4Q dir
- output dir
- full quality-limited row count
- larger expansion input limit
- larger expansion input row count
- excluded row touched count, expected `0`
- already demo-ready row touched count, expected `0`
- already 346B pilot row count
- already 346B4 controlled batch row count
- new quality-limited row count
- value sanitizer success/failure counts
- semantic class distribution
- unit repair action distribution
- recovered candidate count
- safe recovered candidate count
- risky candidate count
- false-positive guardrail hit count
- still quality-limited count
- needs human review count
- needs rule refinement count
- needs VLM count
- unit semantic mismatch count
- semantic class unknown count
- evidence weakness count
- lineage audit passed
- safe-to-qa-larger-expansion flag
- recommended next step
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false

If the ledger has unrelated dirty changes, append only the 346B5 entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B5_larger_quality_limited_recovery_expansion.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346B4 output dir
- 346B3R output dir
- 346B4R output dir
- 346B4Q output dir
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
--controlled-expansion-qa-audit-346b4q-dir D:\_datefac\output\controlled_expansion_qa_audit_346b4q
--output-dir D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5
```

Optional knobs:

```powershell
--max-expansion-rows 1500
--selection-mode priority_then_coverage
--require-346b4q-safe-to-larger-expansion true
--strict-guardrails true
--exclude-previous-controlled-batch true
--include-image-bound-first true
--include-json-md-context-bound true
--max-context-chars 4000
```

Default behavior:

- read the full 345D quality-limited pool;
- require 346B4Q `qa_safe_to_larger_expansion = true`;
- select at most 1500 rows from quality-limited rows;
- exclude strict demo-ready and excluded rows;
- exclude rows already included in the 346B pilot and 346B4 500-row controlled batch by default;
- apply the refined 346B3 + 346B3R patched semantic-class-aware recovery policy;
- run built-in guardrails on unit semantics, lineage, evidence, and false-positive risk;
- produce larger expansion recovered candidates as sidecar/demo-only outputs;
- do not call live VLM/LLM APIs;
- do not run OCR;
- do not rerun MinerU;
- do not mutate upstream or prior outputs.

---

## Inputs to read

From 345D:

- `full_structured_demo_export_package_345d_manifest.json`
- `full_structured_demo_export_package_345d_quality_limited_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_demo_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_quality_caveats.json` or `.md`
- any available 345D artifact index/summary useful for row counts

From 346B4:

- `controlled_quality_limited_recovery_expansion_346b4_manifest.json`
- `controlled_quality_limited_recovery_expansion_346b4_selected_rows.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_recovery_results.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json` or `.csv`

From 346B3R:

- `recovery_rule_refinement_patch_346b3r_manifest.json`
- `recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json` or `.csv`
- `recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json`
- `recovery_rule_refinement_patch_346b3r_patch_safety_review.json` or `.csv`

From 346B4R:

- `controlled_expansion_replay_with_patched_rules_346b4r_manifest.json`
- `controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json` or `.csv`
- `controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json`

From 346B4Q:

- `controlled_expansion_qa_audit_346b4q_manifest.json`
- `controlled_expansion_qa_audit_346b4q_qa_safe_candidates.json` or `.csv`
- `controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.json` or `.csv`
- `controlled_expansion_qa_audit_346b4q_larger_expansion_readiness_report.json`

Validate:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 346B4 decision is `CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY`
- 346B3R decision is `RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY`
- 346B4R decision is `CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY`
- 346B4Q decision is `CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_READY`
- 346B4Q `qa_safe_to_larger_expansion = true`
- 346B4Q `recommended_larger_expansion_row_limit = 1500`
- all input `qa_fail_count = 0`
- all live VLM call counts are `0`
- all formal/client/production gates are false

---

## Selection policy

346B5 must select a larger controlled expansion subset from 345D quality-limited rows.

Default selection limit:

```text
max_expansion_rows = 1500
```

Do not include:

- excluded rows;
- already strict demo-ready rows;
- rows already included in the 346B 100-row pilot;
- rows already included in the 346B4 500-row controlled batch, unless explicitly marked as regression/reference rows;
- rows without minimum lineage fields.

Prefer rows with:

- usable raw or simulated normalized metric;
- parseable numeric value or sanitizer-repairable value;
- period present;
- source trace available;
- recoverable quality issue class;
- metric names covered by 346B3/346B3R semantic policy classes;
- context or deterministic proof availability.

Selection output must preserve why each row was selected.

Recommended selection reason fields:

```text
selection_priority_score
selection_reason_codes
selected_from_quality_limited_pool = true
already_in_346b_pilot = false
already_in_346b4_controlled_batch = false
minimum_lineage_present = true
```

---

## Recovery policy

Apply the refined 346B3 semantic-class-aware recovery policy plus the 346B3R patch proposals validated by 346B4R and 346B4Q.

Semantic classes:

```text
MONETARY_AMOUNT
PERCENTAGE_OR_MARGIN
RATIO_MULTIPLE
PER_SHARE
COUNT_OR_VOLUME
TEXT_OR_LABEL
UNKNOWN
```

Rows with `UNKNOWN` semantic class must not be auto-promoted.

### Compatibility rules

- `RATIO_MULTIPLE`: x / 倍 / multiple / UNIT_RATIO_MULTIPLE_X / UNIT_NOT_APPLICABLE_RATIO_MULTIPLE. Never `%`.
- `PERCENTAGE_OR_MARGIN`: % / pct / percentage / UNIT_PERCENT_FROM_MARGIN_CONTEXT / UNIT_PERCENT_FROM_RATIO_CONTEXT_COMPATIBLE.
- `PER_SHARE`: 元/股 / 港元/股 / RMB/share / HKD/share / USD/share / UNIT_PER_SHARE_CONTEXT. Never `%`.
- `MONETARY_AMOUNT`: 元 / 万元 / 百万元 / 千万元 / 亿元 / RMB / HKD / USD / clear money variants.
- `COUNT_OR_VOLUME`: 家 / 人 / 万人 / 亿人 / 吨 / 万吨 / 片 / 万片/年 / 次 / 间夜 / 件 / 台 / 套 and compatible count/volume units.
- `TEXT_OR_LABEL`: no numeric unit promotion unless explicitly supported.

Do not introduce a rule that re-creates the original `UNIT_PERCENT_FROM_RATIO_CONTEXT` false-positive bug.

---

## Guardrails

A row can become `LARGER_RECOVERED_DEMO_CANDIDATE` only if:

- it comes from 345D quality-limited pool;
- it is not excluded and not already strict demo-ready;
- it was not already counted in prior pilot/controlled batches by default;
- raw value is preserved;
- sanitized value is parseable or already valid;
- metric semantic class is known;
- refined unit/action is compatible with semantic class;
- period is present or safely verified;
- source trace/evidence or deterministic proof is available;
- no unit semantic mismatch exists;
- no false-positive guardrail triggers;
- no high-severity issue remains;
- recovery remains sidecar-only and demo-only;
- no formal/client/production gate is opened.

Rows failing guardrails should be classified as one of:

```text
LARGER_STILL_QUALITY_LIMITED
LARGER_NEEDS_HUMAN_REVIEW
LARGER_NEEDS_RULE_REFINEMENT
LARGER_NEEDS_VLM_REPAIR
LARGER_FALSE_POSITIVE_GUARDRAIL_HIT
```

No row should be silently dropped. Counts must close.

---

## Outputs

Write only under:

```text
D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5
```

Generate:

- `larger_quality_limited_recovery_expansion_346b5_manifest.json`
- `larger_quality_limited_recovery_expansion_346b5_selected_rows.json`
- `larger_quality_limited_recovery_expansion_346b5_selected_rows.csv`
- `larger_quality_limited_recovery_expansion_346b5_recovery_results.json`
- `larger_quality_limited_recovery_expansion_346b5_recovery_results.csv`
- `larger_quality_limited_recovery_expansion_346b5_recovered_demo_candidates.json`
- `larger_quality_limited_recovery_expansion_346b5_recovered_demo_candidates.csv`
- `larger_quality_limited_recovery_expansion_346b5_safe_recovered_candidates.json`
- `larger_quality_limited_recovery_expansion_346b5_safe_recovered_candidates.csv`
- `larger_quality_limited_recovery_expansion_346b5_still_limited_rows.json`
- `larger_quality_limited_recovery_expansion_346b5_still_limited_rows.csv`
- `larger_quality_limited_recovery_expansion_346b5_needs_human_review_rows.json`
- `larger_quality_limited_recovery_expansion_346b5_needs_human_review_rows.csv`
- `larger_quality_limited_recovery_expansion_346b5_needs_rule_refinement_rows.json`
- `larger_quality_limited_recovery_expansion_346b5_needs_rule_refinement_rows.csv`
- `larger_quality_limited_recovery_expansion_346b5_needs_vlm_rows.json`
- `larger_quality_limited_recovery_expansion_346b5_needs_vlm_rows.csv`
- `larger_quality_limited_recovery_expansion_346b5_false_positive_guardrail_hits.json`
- `larger_quality_limited_recovery_expansion_346b5_false_positive_guardrail_hits.csv`
- `larger_quality_limited_recovery_expansion_346b5_semantic_class_distribution.json`
- `larger_quality_limited_recovery_expansion_346b5_semantic_class_distribution.csv`
- `larger_quality_limited_recovery_expansion_346b5_unit_action_distribution.json`
- `larger_quality_limited_recovery_expansion_346b5_unit_action_distribution.csv`
- `larger_quality_limited_recovery_expansion_346b5_lineage_evidence_audit.json`
- `larger_quality_limited_recovery_expansion_346b5_lineage_evidence_audit.csv`
- `larger_quality_limited_recovery_expansion_346b5_guardrail_summary.json`
- `larger_quality_limited_recovery_expansion_346b5_expansion_readiness_report.json`
- `larger_quality_limited_recovery_expansion_346b5_executive_summary.md`
- `larger_quality_limited_recovery_expansion_346b5_artifact_index.md`
- `larger_quality_limited_recovery_expansion_346b5_next_plan.md`

Do not modify any previous outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION_346B5_READY
input_stage = POST_346B4Q_LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION
qa_fail_count = 0
no_write_back_proof_passed = true
input_345d_decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY
input_346b4_decision = CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY
input_346b3r_decision = RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY
input_346b4r_decision = CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY
input_346b4q_decision = CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_READY
input_346b4q_qa_safe_to_larger_expansion = true
full_quality_limited_row_count = 5558
larger_expansion_input_limit
larger_expansion_input_row_count
excluded_row_touched_count = 0
already_demo_ready_row_touched_count = 0
already_346b_pilot_row_count
already_346b4_controlled_batch_row_count
new_quality_limited_row_count
value_sanitizer_attempt_count
sanitized_value_success_count
sanitized_value_failure_count
semantic_class_known_count
semantic_class_unknown_count
unit_repair_attempt_count
unit_repair_success_count
unit_semantic_mismatch_count
recovered_candidate_count
safe_recovered_candidate_count
risky_candidate_count
false_positive_guardrail_hit_count
still_quality_limited_count
needs_human_review_count
needs_rule_refinement_count
needs_vlm_count
lineage_audit_passed
evidence_weakness_count
safe_to_qa_larger_expansion
safe_to_qa_larger_expansion_reason
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

If guardrails catch material risks, the task can still be READY if QA passes technically, but `safe_to_qa_larger_expansion` must be false and the next step must be refinement/audit, not broader expansion.

---

## Reports

Executive summary must explain:

- why 346B5 follows 346B4Q;
- how many quality-limited rows exist;
- why the expansion was capped at 1500;
- whether previous pilot/controlled rows were excluded;
- selection policy and selected row count;
- how many rows were recovered safely;
- how many remain limited/human-review/rule-refinement/VLM;
- semantic class distribution;
- unit repair action distribution;
- false-positive guardrail results;
- lineage and evidence audit results;
- whether the 1500-row expansion is ready for QA;
- why no live VLM/OCR/MinerU rerun happened;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B5Q Larger Expansion QA Audit` if recovered candidates were produced and ready for independent QA;
- `346B3R2 Recovery Rule Refinement Patch Follow-up` if material rule gaps remain;
- `346B6 Full Quality-Limited Recovery Expansion` only after 346B5Q confirms safety;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `347A MinerU 3.3.1 Side-by-Side Compatibility Benchmark` if the team chooses to evaluate MinerU upgrade in parallel;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B5_larger_quality_limited_recovery_expansion.md`
- `datefac/benchmark/larger_quality_limited_recovery_expansion_346b5.py`
- `datefac/benchmark/larger_quality_limited_recovery_expansion_346b5_report.py`
- `tools/run_larger_quality_limited_recovery_expansion_346b5.py`
- `tests/benchmark/test_larger_quality_limited_recovery_expansion_346b5.py`
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
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B5 output dir
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
python -m py_compile datefac\benchmark\larger_quality_limited_recovery_expansion_346b5.py datefac\benchmark\larger_quality_limited_recovery_expansion_346b5_report.py tools\run_larger_quality_limited_recovery_expansion_346b5.py tests\benchmark\test_larger_quality_limited_recovery_expansion_346b5.py
python -m pytest tests\benchmark\test_larger_quality_limited_recovery_expansion_346b5.py -q
python tools\run_larger_quality_limited_recovery_expansion_346b5.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4 --recovery-rule-refinement-patch-346b3r-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r --controlled-expansion-replay-with-patched-rules-346b4r-dir D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r --controlled-expansion-qa-audit-346b4q-dir D:\_datefac\output\controlled_expansion_qa_audit_346b4q --output-dir D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5 --max-expansion-rows 1500
```

Tests must verify:

- outputs exist;
- valid 345D/346B4/346B3R/346B4R/346B4Q inputs produce READY;
- invalid required inputs fail clearly;
- 346B4Q qa_safe_to_larger_expansion is required;
- selected rows come only from quality-limited pool;
- excluded and strict demo-ready rows are not touched;
- prior 346B pilot and 346B4 controlled-batch rows are not double-counted by default;
- row counts close across recovered/still-limited/human-review/rule-refinement/VLM/guardrail buckets;
- raw values and source lineage are preserved;
- semantic class policy and patched rules are applied;
- ratio/multiple rows are not assigned `%`;
- per-share rows are not assigned `%`;
- guardrail hits prevent safe promotion;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- official rules/assets flags remain false;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B5 entry.

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
8. full quality-limited row count and larger input limit.
9. selected/input row count and previous-batch exclusion counts.
10. sanitizer and semantic class counts.
11. recovered/safe/still-limited/human-review/rule-refinement/VLM/guardrail counts.
12. unit action distribution and unit mismatch counts.
13. semantic class distribution.
14. lineage/evidence audit result.
15. safe-to-QA-larger-expansion flag and reason.
16. live VLM call count.
17. official rules/assets modified flags.
18. formal export generated / demo export only flags.
19. final gate status.
20. first file to open.
21. next recommended step.
22. `git status -sb`.
23. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
