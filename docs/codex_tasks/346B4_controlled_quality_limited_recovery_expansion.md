# 346B4 Controlled Quality-Limited Recovery Expansion

## Goal

Implement `346B4 Controlled Quality-Limited Recovery Expansion`.

346B recovered 70 demo-only candidates from a 100-row quality-limited pilot.

346B2 audited those 70 candidates and found 38 false-positive suspects, mostly caused by unit semantics:

```text
safe_recovered_candidate_count = 32
false_positive_suspect_count = 38
ratio_multiple_unit_mismatch_count = 24
per_share_unit_mismatch_count = 14
safe_to_expand_recovery = false
```

346B3 refined the recovery rules using semantic metric classes:

```text
refined_candidate_count = 70
refined_safe_candidate_count = 70
remaining_false_positive_suspect_count = 0
corrected_ratio_multiple_unit_count = 24
corrected_per_share_unit_count = 14
preserved_percentage_margin_unit_count = 30
safe_to_reaudit = true
safe_to_expand_recovery = false
```

346B2R independently re-audited the 346B3 refined results and confirmed they are safe enough for controlled expansion:

```text
input_refined_candidate_count = 70
reaudit_candidate_count = 70
reaudit_safe_candidate_count = 70
reaudit_false_positive_suspect_count = 0
ratio_multiple_unit_mismatch_count = 0
per_share_unit_mismatch_count = 0
percentage_margin_unit_mismatch_count = 0
monetary_unit_mismatch_count = 0
semantic_class_unknown_count = 0
semantic_class_disagreement_count = 0
evidence_weakness_count = 0
lineage_audit_passed = true
false_positive_regression_checked_count = 38
false_positive_regression_fixed_count = 38
false_positive_regression_still_risky_count = 0
safe_to_expand_recovery = true
recommended_expansion_scope = 346B4 Controlled Quality-Limited Recovery Expansion
live_vlm_call_count = 0
```

346B4 must answer:

> If the refined and re-audited recovery rules are applied to a controlled expansion subset of the 5558 quality-limited rows, how many additional demo-only recovery candidates can be produced safely, without live VLM calls, OCR, upstream mutation, or formal client export?

This task is a controlled sidecar expansion, not a full production migration.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Freeze excluded rows.
- Work only on quality-limited rows.
- Use deterministic sanitizer before semantic recovery.
- Use scoped context state machine / inheritance.
- Apply the 346B3 semantic-class-aware unit policy.
- Preserve raw values and source lineage.
- Treat recovery outputs as sidecar suggestions only.
- Re-audit before expansion beyond this controlled batch.
- Do not call live VLM/LLM APIs.
- Do not run OCR.
- Do not rerun MinerU.
- Do not write recovered candidates back into upstream datasets.
- Demo-only candidates are not formal client-ready rows.

346B4 is allowed because 346B2R produced `safe_to_expand_recovery = true`, but it must remain controlled and sidecar-only.

---

## Current context

345D full structured demo export package:

```text
D:\_datefac\output\full_structured_demo_export_package_345d
```

346A output:

```text
D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
```

346A2 output:

```text
D:\_datefac\output\mineru_image_path_binding_fix_346a2
```

346B output:

```text
D:\_datefac\output\quality_limited_row_recovery_pilot_346b
```

346B2 output:

```text
D:\_datefac\output\recovery_candidate_qa_audit_346b2
```

346B3 output:

```text
D:\_datefac\output\recovery_rule_refinement_346b3
```

346B2R output:

```text
D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r
```

346B4 output:

```text
D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
```

Known quality-limited pool:

```text
full_quality_limited_row_count = 5558
```

Recommended first expansion size:

```text
controlled_expansion_input_limit = 500
```

Do not expand directly to all 5558 rows by default. That belongs to a later step after 346B4 QA.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B4 entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B4`
- decision: `CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY`
- input 345D dir
- input 346A dir
- input 346A2 dir
- input 346B dir
- input 346B2 dir
- input 346B3 dir
- input 346B2R dir
- output dir
- full quality-limited row count
- controlled expansion input limit
- controlled expansion input row count
- excluded row touched count, expected `0`
- already demo-ready row touched count, expected `0`
- refined policy source
- value sanitizer success/failure counts
- semantic class distribution
- unit repair action distribution
- recovered candidate count
- safe recovered candidate count
- risky candidate count
- false-positive guardrail hit count
- still quality-limited count
- needs human review count
- needs VLM count
- unit mismatch count
- semantic class unknown count
- evidence weakness count
- lineage audit passed
- safe-to-continue expansion flag
- recommended next step
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false

If the ledger has unrelated dirty changes, append only the 346B4 entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B4_controlled_quality_limited_recovery_expansion.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346A output dir
- 346A2 output dir
- 346B output dir
- 346B2 output dir
- 346B3 output dir
- 346B2R output dir
- the milestone ledger
- the root tactical playbook

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a
--mineru-image-path-binding-fix-346a2-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2
--quality-limited-row-recovery-pilot-346b-dir D:\_datefac\output\quality_limited_row_recovery_pilot_346b
--recovery-candidate-qa-audit-346b2-dir D:\_datefac\output\recovery_candidate_qa_audit_346b2
--recovery-rule-refinement-346b3-dir D:\_datefac\output\recovery_rule_refinement_346b3
--refined-recovery-candidate-qa-reaudit-346b2r-dir D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r
--output-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
```

Optional knobs:

```powershell
--max-expansion-rows 500
--selection-mode priority_then_coverage
--require-346b2r-safe-to-expand true
--strict-guardrails true
--include-image-bound-first true
--include-json-md-context-bound true
--max-context-chars 4000
```

Default behavior:

- read the full 345D quality-limited pool;
- exclude rows already processed in the 346B 100-row pilot unless explicitly configured otherwise;
- select at most 500 controlled expansion rows by priority and recoverability;
- apply the 346B3 semantic-class-aware recovery policy;
- use 346B2R as the go/no-go proof for controlled expansion;
- produce recovered candidates as sidecar/demo-only outputs;
- run built-in guardrail checks on unit semantics, lineage, and evidence;
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

From 346A/346A2:

- 346A manifest and selected pilot rows, mainly to avoid double counting or to reuse priority metadata if useful
- 346A2 manifest, bound rows, image resolution status, JSON/MD context index if useful

From 346B:

- 346B manifest
- 346B recovered demo candidates
- 346B still-limited / human-review / needs-VLM / recovery fail reasons if useful

From 346B2:

- 346B2 manifest
- false-positive suspects and unit repair audit as negative examples / guardrail source

From 346B3:

- `recovery_rule_refinement_346b3_refined_unit_policy.json`
- `recovery_rule_refinement_346b3_refined_unit_policy.md`
- `recovery_rule_refinement_346b3_rule_change_log.json` or `.md`
- `recovery_rule_refinement_346b3_refined_safe_candidates.json` or `.csv`

From 346B2R:

- `refined_recovery_candidate_qa_reaudit_346b2r_manifest.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.json` or `.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.json` or `.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json`

Validate:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 346A decision is `VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY`
- 346A2 decision is `MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY`
- 346B decision is `QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY`
- 346B2 decision is `RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY`
- 346B3 decision is `RECOVERY_RULE_REFINEMENT_346B3_READY`
- 346B2R decision is `REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY`
- all input `qa_fail_count = 0`
- 346B2R `safe_to_expand_recovery = true`
- all live VLM call counts are `0`
- all formal/client/production gates are false

---

## Selection policy

346B4 must select a controlled expansion subset from 345D quality-limited rows.

Default selection limit:

```text
max_expansion_rows = 500
```

Do not include:

- excluded rows;
- already strict demo-ready rows;
- rows already included in the 346B 100-row pilot, unless needed for regression comparison and clearly marked as `REGRESSION_REFERENCE_ONLY`;
- rows without enough minimum lineage fields.

Prefer rows with:

- usable normalized metric or alias-simulated normalized metric;
- parseable numeric value or sanitizer-repairable value;
- period present;
- source trace available;
- quality issue limited to unit/semantic normalization/human-review-pending style recoverable problems;
- metric names covered by the 346B3 semantic policy classes;
- context or evidence availability from existing outputs.

Selection output must preserve why each row was selected.

Recommended selection reason fields:

```text
selection_priority_score
selection_reason_codes
selected_from_quality_limited_pool = true
already_in_346b_pilot = false
minimum_lineage_present = true
```

---

## Recovery policy

Apply the refined 346B3 semantic-class-aware recovery policy.

### Semantic classes

Classify each row as:

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

### Unit repair compatibility

#### RATIO_MULTIPLE

Allowed:

```text
x
倍
multiple
UNIT_RATIO_MULTIPLE_X
UNIT_NOT_APPLICABLE_RATIO_MULTIPLE
```

Forbidden:

```text
%
pct
percentage
元
百万元
亿元
```

#### PERCENTAGE_OR_MARGIN

Allowed:

```text
%
pct
percentage
UNIT_PERCENT_FROM_MARGIN_CONTEXT
UNIT_PERCENT_FROM_RATIO_CONTEXT_COMPATIBLE
```

#### PER_SHARE

Allowed:

```text
元/股
港元/股
RMB/share
HKD/share
USD/share
UNIT_PER_SHARE_CONTEXT
```

Do not assign `%` to per-share rows.

#### MONETARY_AMOUNT

Allowed:

```text
元
万元
百万元
千万元
亿元
RMB
HKD
USD
clear money/currency variants
```

Do not inherit monetary units into ratio/multiple, percentage/margin, or per-share rows.

---

## Guardrails

346B4 must include strict guardrails before marking any row as safe:

A row can become `CONTROLLED_RECOVERED_DEMO_CANDIDATE` only if:

- it comes from 345D quality-limited pool;
- it is not excluded and not already strict demo-ready;
- raw value is preserved;
- sanitized value is parseable or already valid;
- metric semantic class is known;
- refined unit/action is compatible with semantic class;
- period is present or safely verified;
- source trace/evidence is available;
- no unit semantic mismatch exists;
- no high severity issue remains;
- recovery remains sidecar-only and demo-only;
- no formal/client/production gate is opened.

Rows failing guardrails should be classified as one of:

```text
CONTROLLED_STILL_QUALITY_LIMITED
CONTROLLED_NEEDS_HUMAN_REVIEW
CONTROLLED_NEEDS_RULE_REFINEMENT
CONTROLLED_NEEDS_VLM_REPAIR
CONTROLLED_FALSE_POSITIVE_GUARDRAIL_HIT
```

No row should be silently dropped. Counts must close.

---

## Outputs

Write only under:

```text
D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
```

Generate:

- `controlled_quality_limited_recovery_expansion_346b4_manifest.json`
- `controlled_quality_limited_recovery_expansion_346b4_selected_rows.json`
- `controlled_quality_limited_recovery_expansion_346b4_selected_rows.csv`
- `controlled_quality_limited_recovery_expansion_346b4_recovery_results.json`
- `controlled_quality_limited_recovery_expansion_346b4_recovery_results.csv`
- `controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.json`
- `controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.csv`
- `controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json`
- `controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.csv`
- `controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.json`
- `controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.csv`
- `controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.json`
- `controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.csv`
- `controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json`
- `controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.csv`
- `controlled_quality_limited_recovery_expansion_346b4_needs_vlm_rows.json`
- `controlled_quality_limited_recovery_expansion_346b4_needs_vlm_rows.csv`
- `controlled_quality_limited_recovery_expansion_346b4_false_positive_guardrail_hits.json`
- `controlled_quality_limited_recovery_expansion_346b4_false_positive_guardrail_hits.csv`
- `controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json`
- `controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.csv`
- `controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.json`
- `controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.csv`
- `controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.json`
- `controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.csv`
- `controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json`
- `controlled_quality_limited_recovery_expansion_346b4_expansion_readiness_report.json`
- `controlled_quality_limited_recovery_expansion_346b4_executive_summary.md`
- `controlled_quality_limited_recovery_expansion_346b4_artifact_index.md`
- `controlled_quality_limited_recovery_expansion_346b4_next_plan.md`

Do not modify any previous outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY
input_stage = POST_346B2R_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION
qa_fail_count = 0
no_write_back_proof_passed = true
input_345d_decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY
input_346a_decision = VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY
input_346a2_decision = MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY
input_346b_decision = QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY
input_346b2_decision = RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY
input_346b3_decision = RECOVERY_RULE_REFINEMENT_346B3_READY
input_346b2r_decision = REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY
full_quality_limited_row_count = 5558
controlled_expansion_input_limit
controlled_expansion_input_row_count
excluded_row_touched_count = 0
already_demo_ready_row_touched_count = 0
already_346b_pilot_row_count
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

If guardrails catch risks, the task can still be READY if QA passes, but `safe_to_continue_expansion` must be false and the next step must be refinement/audit, not broader expansion.

---

## Reports

Executive summary must explain:

- why 346B4 follows 346B2R;
- how many quality-limited rows exist;
- why the expansion was limited to a controlled subset;
- selection policy and selected row count;
- how many rows were recovered safely;
- how many remain limited/human-review/rule-refinement/VLM;
- semantic class distribution;
- unit repair action distribution;
- false-positive guardrail results;
- lineage and evidence audit results;
- whether expansion can continue;
- why no live VLM/OCR/MinerU rerun happened;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B4R Controlled Expansion QA Audit` if recovered candidates were produced and need independent audit before larger expansion;
- `346B5 Larger Quality-Limited Recovery Expansion` only after 346B4R confirms safety;
- `346B3R Recovery Rule Refinement Patch` if material guardrail risks remain;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B4_controlled_quality_limited_recovery_expansion.md`
- `datefac/benchmark/controlled_quality_limited_recovery_expansion_346b4.py`
- `datefac/benchmark/controlled_quality_limited_recovery_expansion_346b4_report.py`
- `tools/run_controlled_quality_limited_recovery_expansion_346b4.py`
- `tests/benchmark/test_controlled_quality_limited_recovery_expansion_346b4.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

The milestone ledger update is required.

---

## Forbidden

Do not:

- call live VLM/LLM APIs
- run OCR
- rerun MinerU
- mutate 345D outputs
- mutate 346A outputs
- mutate 346A2 outputs
- mutate 346B outputs
- mutate 346B2 outputs
- mutate 346B3 outputs
- mutate 346B2R outputs
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B4 output dir
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
python -m py_compile datefac\benchmark\controlled_quality_limited_recovery_expansion_346b4.py datefac\benchmark\controlled_quality_limited_recovery_expansion_346b4_report.py tools\run_controlled_quality_limited_recovery_expansion_346b4.py tests\benchmark\test_controlled_quality_limited_recovery_expansion_346b4.py
python -m pytest tests\benchmark\test_controlled_quality_limited_recovery_expansion_346b4.py -q
python tools\run_controlled_quality_limited_recovery_expansion_346b4.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a --mineru-image-path-binding-fix-346a2-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2 --quality-limited-row-recovery-pilot-346b-dir D:\_datefac\output\quality_limited_row_recovery_pilot_346b --recovery-candidate-qa-audit-346b2-dir D:\_datefac\output\recovery_candidate_qa_audit_346b2 --recovery-rule-refinement-346b3-dir D:\_datefac\output\recovery_rule_refinement_346b3 --refined-recovery-candidate-qa-reaudit-346b2r-dir D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r --output-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4 --max-expansion-rows 500
```

Tests must verify:

- outputs exist;
- valid 345D/346A/346A2/346B/346B2/346B3/346B2R inputs produce READY;
- invalid required inputs fail clearly;
- 346B2R safe_to_expand is required before expansion;
- selected rows come only from quality-limited pool;
- excluded and strict demo-ready rows are not touched;
- previously processed 346B pilot rows are not double-counted by default;
- row counts close across recovered/still-limited/human-review/rule-refinement/VLM/guardrail buckets;
- raw values and source lineage are preserved;
- semantic class policy is applied;
- ratio/multiple rows are not assigned `%`;
- per-share rows are not assigned `%`;
- percentage/margin rows may keep compatible `%`;
- guardrail hits prevent safe promotion;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- official rules/assets flags remain false;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B4 entry.

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
8. full quality-limited row count and controlled input limit.
9. controlled expansion selected/input row count.
10. excluded/demo-ready/already-pilot touched counts.
11. sanitizer and semantic class counts.
12. recovered/safe/still-limited/human-review/rule-refinement/VLM/guardrail counts.
13. unit action distribution and unit mismatch counts.
14. semantic class distribution.
15. lineage/evidence audit result.
16. safe-to-continue expansion flag and reason.
17. live VLM call count.
18. official rules/assets modified flags.
19. formal export generated / demo export only flags.
20. final gate status.
21. first file to open.
22. next recommended step.
23. `git status -sb`.
24. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
