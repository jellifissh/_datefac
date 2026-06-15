# 346B2R Refined Recovery Candidate QA Reaudit

## Goal

Implement `346B2R Refined Recovery Candidate QA Reaudit`.

346B produced 70 recovered demo candidates from a 100-row quality-limited pilot.

346B2 audited those 70 candidates and found material false-positive risk:

```text
audited_recovered_candidate_count = 70
safe_recovered_candidate_count = 32
false_positive_suspect_count = 38
unit_repair_risk_count = 38
ratio_multiple_unit_mismatch_count = 24
per_share_unit_mismatch_count = 14
safe_to_expand_recovery = false
```

346B3 then refined the unit repair rules using semantic metric classes and produced corrected sidecar results:

```text
input_recovered_candidate_count = 70
input_safe_recovered_candidate_count = 32
input_false_positive_suspect_count = 38
refined_candidate_count = 70
refined_safe_candidate_count = 70
remaining_false_positive_suspect_count = 0
corrected_ratio_multiple_unit_count = 24
corrected_per_share_unit_count = 14
preserved_percentage_margin_unit_count = 30
demoted_candidate_count = 0
needs_human_review_count = 0
needs_rule_refinement_count = 0
needs_vlm_count = 0
safe_to_reaudit = true
safe_to_expand_recovery = false
live_vlm_call_count = 0
```

346B2R must answer:

> After the 346B3 semantic-class-aware rule refinement, do the 70 refined recovery candidates pass an independent QA re-audit, with zero remaining false-positive suspects and safe enough evidence/unit semantics to allow future expansion to more quality-limited rows?

This is a QA re-audit task. It must not refine rules further by default, must not recover new rows, must not call live VLM/LLM APIs, and must not mutate upstream data.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Deterministic sanitizer first.
- Scoped context state machine second.
- Text + image evidence third.
- Rule-refined recovery must be independently re-audited.
- VLM only later and only after explicit approval.
- Never overwrite source data.
- Demo-only recovered candidates are not formal client-ready rows.
- Do not expand recovery to the full quality-limited pool until QA says the refined rules are safe.

346B2R is the independent QA checkpoint after 346B3. It decides whether the refined rule results are safe enough to support a future 346B4 expansion.

---

## Current context

345D output:

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

346B2R should consume 346B3 refined candidates, 346B3 refined unit policy, and 346B/346B2 lineage, then produce an independent re-audit verdict.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B2R entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B2R`
- decision: `REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY`
- input 345D dir
- input 346A dir
- input 346A2 dir
- input 346B dir
- input 346B2 dir
- input 346B3 dir
- output dir
- input refined candidate count
- reaudit candidate count
- reaudit safe candidate count
- reaudit risky candidate count
- reaudit false-positive suspect count
- ratio/multiple unit mismatch count
- per-share unit mismatch count
- percentage/margin unit mismatch count
- monetary unit mismatch count
- semantic class unknown count
- evidence weakness count
- lineage preservation pass/fail
- safe-to-expand recovery flag
- expansion recommended row scope
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false
- next recommended step

If the ledger has unrelated dirty changes, append only the 346B2R entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B2R_refined_recovery_candidate_qa_reaudit.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346A output dir
- 346A2 output dir
- 346B output dir
- 346B2 output dir
- 346B3 output dir
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
--output-dir D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r
```

Optional knobs:

```powershell
--strict-reaudit true
--require-lineage-preservation true
--require-evidence-or-deterministic-proof true
--safe-to-expand-risk-threshold 0
--max-context-chars 4000
```

Default behavior:

- read 346B3 refined candidates and refined safe candidates;
- read 346B3 refined unit policy and rule change log;
- read 346B2 original false-positive suspects and recovered candidate audit;
- read 346B original recovered candidates for lineage comparison;
- independently reclassify each refined candidate's metric semantic class;
- independently re-check unit compatibility;
- verify that 346B3 corrected ratio/multiple and per-share rows are no longer percent-unit false positives;
- verify that percentage/margin rows still retain compatible percent units;
- verify lineage fields are preserved;
- verify evidence strength remains sufficient for demo-only candidate status;
- output re-audit sidecar verdicts;
- do not refine rules further by default;
- do not recover new rows;
- do not call live VLM/LLM APIs;
- do not run OCR;
- do not rerun MinerU;
- do not mutate 345D/346A/346A2/346B/346B2/346B3 outputs, MinerU outputs, official rules, or alias assets.

---

## Inputs to read

From 346B3:

- `recovery_rule_refinement_346b3_manifest.json`
- `recovery_rule_refinement_346b3_refined_candidates.json` or `.csv`
- `recovery_rule_refinement_346b3_refined_safe_candidates.json` or `.csv`
- `recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.json` or `.csv`
- `recovery_rule_refinement_346b3_corrected_per_share_rows.json` or `.csv`
- `recovery_rule_refinement_346b3_preserved_percentage_margin_rows.json` or `.csv`
- `recovery_rule_refinement_346b3_demoted_rows.json` or `.csv`
- `recovery_rule_refinement_346b3_refined_unit_policy.json`
- `recovery_rule_refinement_346b3_rule_change_log.json` or `.md`
- `recovery_rule_refinement_346b3_reaudit_preview.json` or `.csv`
- `recovery_rule_refinement_346b3_expansion_readiness_report.json`

From 346B2:

- `recovery_candidate_qa_audit_346b2_manifest.json`
- `recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json` or `.csv`
- `recovery_candidate_qa_audit_346b2_false_positive_suspects.json` or `.csv`
- `recovery_candidate_qa_audit_346b2_unit_repair_audit.json` or `.csv`

From 346B:

- `quality_limited_row_recovery_pilot_346b_manifest.json`
- `quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_context_injection_results.json` or `.csv`

From 346A2, if needed:

- `mineru_image_path_binding_fix_346a2_bound_rows.json`
- `mineru_image_path_binding_fix_346a2_manifest.json`

From 345D/346A, only read manifests and IDs needed for validation.

Validate:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 346A decision is `VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY`
- 346A2 decision is `MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY`
- 346B decision is `QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY`
- 346B2 decision is `RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY`
- 346B3 decision is `RECOVERY_RULE_REFINEMENT_346B3_READY`
- all input `qa_fail_count = 0`
- 346B, 346B2, 346B3 `live_vlm_call_count = 0`
- all formal/client/production gates are false

---

## Re-audit logic

### 1. Candidate closure

Verify:

```text
input_refined_candidate_count = 70
reaudit_candidate_count = 70
```

and classify every refined candidate into exactly one final re-audit decision:

```text
REAUDIT_SAFE_RECOVERED_DEMO_CANDIDATE
REAUDIT_RISKY_RECOVERED_DEMO_CANDIDATE
REAUDIT_FALSE_POSITIVE_SUSPECT
REAUDIT_NEEDS_HUMAN_REVIEW
REAUDIT_NEEDS_RULE_REFINEMENT
```

Counts must close against the input refined candidate count.

---

### 2. Independent semantic class reclassification

Do not simply trust 346B3's semantic class. Recompute semantic class using raw metric name, normalized metric name, context/table body when available, and neighbor rows.

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

Expected examples:

```text
EV/EBITDA, PE, PB, PS, EV/Sales -> RATIO_MULTIPLE
ROE, ROA, EBIT Margin, 毛利率, 净利率, (+/-%) -> PERCENTAGE_OR_MARGIN
每股收益, 每股净资产, EPS, BVPS -> PER_SHARE
营业收入（百万元）, 净利润(百万元), 总资产, 负债合计 -> MONETARY_AMOUNT
```

If 346B3 semantic class and re-audit semantic class disagree, flag `SEMANTIC_CLASS_DISAGREEMENT`.

---

### 3. Unit compatibility re-check

Apply the same compatibility principles independently:

#### RATIO_MULTIPLE

Allowed refined units/actions:

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

Allowed refined units/actions:

```text
%
pct
percentage
UNIT_PERCENT_FROM_MARGIN_CONTEXT
UNIT_PERCENT_FROM_RATIO_CONTEXT_COMPATIBLE
```

#### PER_SHARE

Allowed refined units/actions:

```text
元/股
港元/股
RMB/share
HKD/share
USD/share
UNIT_PER_SHARE_CONTEXT
```

#### MONETARY_AMOUNT

Allowed refined units/actions:

```text
元
万元
百万元
千万元
亿元
RMB
HKD
USD
clear currency/money variants
```

UNKNOWN cannot be safe.

Important checks:

- Ratio/multiple rows must not have `%`.
- Per-share rows must not have `%`.
- Percentage/margin rows may have `%` if value/context support it.
- Monetary rows must not receive `%` or ratio unit.

---

### 4. 346B2 false-positive regression check

For every row previously listed in 346B2 false-positive suspects:

- confirm it exists in 346B3 refined candidates;
- confirm its false-positive reason has been corrected or demoted;
- record regression status:

```text
REGRESSION_FIXED
REGRESSION_STILL_RISKY
REGRESSION_MISSING_FROM_REFINED_OUTPUT
```

Expected high-level result:

```text
false_positive_regression_fixed_count = 38
false_positive_regression_still_risky_count = 0
```

---

### 5. Evidence and lineage audit

Verify every refined candidate preserves source lineage:

```text
source_row_id
pilot_row_id
demo_export_row_id
raw_metric_name
demo_normalized_metric_name
raw_value
sanitized_value or value
period
original quality issue fields
346B recovery action fields or reference
346B3 refined action fields
```

Verify evidence strength:

```text
IMAGE_BOUND_TABLE_CROP
JSON_MD_CONTEXT_BOUND
TEXT_CONTEXT_ONLY
NO_BOUND_EVIDENCE
```

A row can be safe with text/JSON/MD context if deterministic unit semantics are sufficient and no image evidence is required for the specific recovery. But `NO_BOUND_EVIDENCE` should not be safe unless the repair is purely deterministic and explicitly justified.

---

### 6. Expansion readiness decision

Set:

```text
safe_to_expand_recovery = true
```

only if all conditions pass:

- reaudit candidate count closes;
- no false-positive suspects remain;
- no unit mismatch remains;
- no semantic class unknown safe rows exist;
- lineage preservation passes;
- no material evidence weakness exists;
- official/formal/client/production gates remain false;
- no live VLM/OCR/MinerU rerun occurred.

If true, recommend controlled expansion, not uncontrolled full mutation. The next expansion should still be sidecar/demo-only.

Recommended expansion scope:

```text
346B4 Controlled Quality-Limited Recovery Expansion
```

with a configurable max row limit, for example 500 first, before full 5558 expansion.

---

## Outputs

Write only under:

```text
D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r
```

Generate:

- `refined_recovery_candidate_qa_reaudit_346b2r_manifest.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_risky_candidates.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_risky_candidates.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_false_positive_suspects.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_false_positive_suspects.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_semantic_class_reaudit.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_semantic_class_reaudit.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_unit_compatibility_reaudit.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_unit_compatibility_reaudit.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_false_positive_regression_check.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_false_positive_regression_check.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_evidence_lineage_audit.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_evidence_lineage_audit.csv`
- `refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_reaudit_summary.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_executive_summary.md`
- `refined_recovery_candidate_qa_reaudit_346b2r_artifact_index.md`
- `refined_recovery_candidate_qa_reaudit_346b2r_next_plan.md`

Do not modify 346B3 outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY
input_stage = POST_346B3_REFINED_RECOVERY_CANDIDATE_QA_REAUDIT
qa_fail_count = 0
no_write_back_proof_passed = true
input_345d_decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY
input_346a_decision = VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY
input_346a2_decision = MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY
input_346b_decision = QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY
input_346b2_decision = RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY
input_346b3_decision = RECOVERY_RULE_REFINEMENT_346B3_READY
full_quality_limited_row_count = 5558
input_refined_candidate_count = 70
reaudit_candidate_count
reaudit_safe_candidate_count
reaudit_risky_candidate_count
reaudit_false_positive_suspect_count
reaudit_needs_human_review_count
reaudit_needs_rule_refinement_count
ratio_multiple_unit_mismatch_count
per_share_unit_mismatch_count
percentage_margin_unit_mismatch_count
monetary_unit_mismatch_count
semantic_class_unknown_count
semantic_class_disagreement_count
evidence_weakness_count
lineage_audit_passed
false_positive_regression_checked_count
false_positive_regression_fixed_count
false_positive_regression_still_risky_count
safe_to_expand_recovery
safe_to_expand_recovery_reason
recommended_expansion_scope
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

If re-audit fails, the task should still be READY if QA passes, but `safe_to_expand_recovery` must remain false and the next step must be a refinement patch, not expansion.

---

## Reports

Executive summary must explain:

- why 346B2R follows 346B3;
- how many refined candidates were re-audited;
- safe/risky/false-positive counts;
- whether ratio/multiple and per-share regressions were fixed;
- whether percentage/margin rows remained compatible;
- evidence and lineage audit result;
- false-positive regression check result;
- safe-to-expand decision and reason;
- recommended expansion scope if safe;
- why no live VLM calls were made;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B3R Recovery Rule Refinement Patch` if false-positive suspects or material unit risks remain;
- `346B4 Controlled Quality-Limited Recovery Expansion` if `safe_to_expand_recovery = true`;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B2R_refined_recovery_candidate_qa_reaudit.md`
- `datefac/benchmark/refined_recovery_candidate_qa_reaudit_346b2r.py`
- `datefac/benchmark/refined_recovery_candidate_qa_reaudit_346b2r_report.py`
- `tools/run_refined_recovery_candidate_qa_reaudit_346b2r.py`
- `tests/benchmark/test_refined_recovery_candidate_qa_reaudit_346b2r.py`
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
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B2R output dir
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
python -m py_compile datefac\benchmark\refined_recovery_candidate_qa_reaudit_346b2r.py datefac\benchmark\refined_recovery_candidate_qa_reaudit_346b2r_report.py tools\run_refined_recovery_candidate_qa_reaudit_346b2r.py tests\benchmark\test_refined_recovery_candidate_qa_reaudit_346b2r.py
python -m pytest tests\benchmark\test_refined_recovery_candidate_qa_reaudit_346b2r.py -q
python tools\run_refined_recovery_candidate_qa_reaudit_346b2r.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a --mineru-image-path-binding-fix-346a2-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2 --quality-limited-row-recovery-pilot-346b-dir D:\_datefac\output\quality_limited_row_recovery_pilot_346b --recovery-candidate-qa-audit-346b2-dir D:\_datefac\output\recovery_candidate_qa_audit_346b2 --recovery-rule-refinement-346b3-dir D:\_datefac\output\recovery_rule_refinement_346b3 --output-dir D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r
```

Tests must verify:

- outputs exist;
- valid 345D/346A/346A2/346B/346B2/346B3 inputs produce READY;
- invalid required inputs fail clearly;
- 70 refined candidates are re-audited when present;
- counts close against refined candidate count;
- raw values and source lineage are preserved;
- semantic classes are recomputed independently;
- ratio/multiple rows are not assigned `%`;
- per-share rows are not assigned `%`;
- percentage/margin rows keep compatible `%` when valid;
- previously false-positive suspect rows are checked for regression fixes;
- safe_to_expand_recovery is true only if zero material risks remain;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- official rules/assets flags remain false;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B2R entry.

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
8. input refined candidate count.
9. re-audit safe/risky/false-positive/human-review/rule-refinement counts.
10. unit mismatch counts.
11. semantic class unknown/disagreement counts.
12. false-positive regression check counts.
13. evidence/lineage audit result.
14. safe-to-expand flag and reason.
15. recommended expansion scope.
16. live VLM call count.
17. official rules/assets modified flags.
18. formal export generated / demo export only flags.
19. final gate status.
20. first file to open.
21. next recommended step.
22. `git status -sb`.
23. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
