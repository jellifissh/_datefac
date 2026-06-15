# 346B3 Recovery Rule Refinement

## Goal

Implement `346B3 Recovery Rule Refinement`.

346B produced 70 recovered demo candidates from a 100-row quality-limited pilot, but 346B2 audited those candidates and found material false-positive risk:

```text
audited_recovered_candidate_count = 70
safe_recovered_candidate_count = 32
risky_recovered_candidate_count = 0
false_positive_suspect_count = 38
needs_human_review_after_audit_count = 0
needs_rule_refinement_count = 0
unit_repair_audit_count = 70
unit_repair_risk_count = 38
ratio_multiple_unit_mismatch_count = 24
percentage_unit_mismatch_count = 0
per_share_unit_mismatch_count = 14
monetary_unit_mismatch_count = 0
unit_not_applicable_verified_count = 0
unit_not_applicable_risk_count = 0
safe_to_expand_recovery = false
```

The main risk source was:

```text
UNIT_PERCENT_FROM_RATIO_CONTEXT
```

346B2 showed that this rule was compatible for percentage/margin rows, but unsafe for ratio/multiple and per-share rows:

```text
RATIO_MULTIPLE = 24 false-positive suspects
PER_SHARE = 14 false-positive suspects
PERCENTAGE_OR_MARGIN = 30 compatible rows
```

346B3 must answer:

> Can we refine the deterministic recovery rules so that unit repair is semantic-class-aware, preventing percentage units from being applied to ratio/multiple or per-share metrics, while preserving valid percentage/margin recovery candidates?

This task must produce a corrected sidecar recovery simulation. It must not mutate 346B outputs or upstream data.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Python deterministic sanitizer first.
- Context state machine / inheritance second.
- Text + image evidence binding third.
- Re-audit every repaired row.
- VLM only later and only after explicit approval.
- Never overwrite source data.
- Demo-only recovered candidates are not formal client-ready rows.
- Do not industrialize a rule until QA says it is safe.

346B3 is a rule-refinement sidecar stage. It should not expand to the full 5558 quality-limited rows yet. Expansion belongs to a later 346B4 only after refined rules pass a new audit.

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

346B3 should consume 346B recovered candidates and 346B2 false-positive suspects, then produce corrected rule decisions and refined recovered demo candidates as sidecar outputs.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B3 entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B3`
- decision: `RECOVERY_RULE_REFINEMENT_346B3_READY`
- input 345D dir
- input 346A dir
- input 346A2 dir
- input 346B dir
- input 346B2 dir
- output dir
- input recovered candidate count
- input safe candidate count from 346B2
- input false-positive suspect count from 346B2
- refined candidate count
- refined safe candidate count
- remaining false-positive suspect count
- corrected ratio/multiple unit count
- corrected per-share unit count
- preserved percentage/margin unit count
- dropped or demoted candidate count
- needs human review count
- needs VLM count
- safe-to-reaudit flag
- safe-to-expand flag, expected false until a 346B2R audit passes
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false
- next recommended step

If the ledger has unrelated dirty changes, append only the 346B3 entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B3_recovery_rule_refinement.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346A output dir
- 346A2 output dir
- 346B output dir
- 346B2 output dir
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
--output-dir D:\_datefac\output\recovery_rule_refinement_346b3
```

Optional knobs:

```powershell
--strict-refinement true
--preserve-safe-346b2-candidates true
--demote-unresolved-risk true
--max-context-chars 4000
```

Default behavior:

- read 346B recovered demo candidates;
- read 346B2 recovered candidate audit and false-positive suspects;
- build a semantic-class-aware unit repair policy;
- re-evaluate 346B recovered candidates using refined rules;
- preserve safe 346B2 candidates when still compatible;
- correct or demote false-positive suspects;
- produce refined sidecar recovery outputs;
- do not recover new rows outside the 346B recovered candidate set by default;
- do not call live VLM/LLM APIs;
- do not run OCR;
- do not rerun MinerU;
- do not mutate 345D/346A/346A2/346B/346B2 outputs, MinerU outputs, official rules, or alias assets.

---

## Inputs to read

From 346B:

- `quality_limited_row_recovery_pilot_346b_manifest.json`
- `quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_context_injection_results.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_value_sanitizer_results.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_reaudit_summary.json`

From 346B2:

- `recovery_candidate_qa_audit_346b2_manifest.json`
- `recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json` or `.csv`
- `recovery_candidate_qa_audit_346b2_safe_recovered_candidates.json` or `.csv`
- `recovery_candidate_qa_audit_346b2_false_positive_suspects.json` or `.csv`
- `recovery_candidate_qa_audit_346b2_unit_repair_audit.json` or `.csv`
- `recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.json` or `.csv`
- `recovery_candidate_qa_audit_346b2_expansion_readiness_report.json`
- `recovery_candidate_qa_audit_346b2_reaudit_summary.json`

From 346A2, if needed for evidence confirmation:

- `mineru_image_path_binding_fix_346a2_bound_rows.json`
- `mineru_image_path_binding_fix_346a2_manifest.json`

From 345D/346A, only read manifests and row IDs needed for validation.

Validate:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 346A decision is `VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY`
- 346A2 decision is `MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY`
- 346B decision is `QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY`
- 346B2 decision is `RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY`
- all input `qa_fail_count = 0`
- 346B and 346B2 `live_vlm_call_count = 0`
- all formal/client/production gates are false

---

## Refined unit policy

Build a deterministic policy around semantic metric classes.

### Semantic classes

Classify each row as one of:

```text
MONETARY_AMOUNT
PERCENTAGE_OR_MARGIN
RATIO_MULTIPLE
PER_SHARE
COUNT_OR_VOLUME
TEXT_OR_LABEL
UNKNOWN
```

Use raw metric name, normalized metric name, row context, table body, and neighbor rows.

Examples:

```text
EV/EBITDA, PE, PB, PS, EV/Sales -> RATIO_MULTIPLE
ROE, ROA, EBIT Margin, 毛利率, 净利率, (+/-%) -> PERCENTAGE_OR_MARGIN
每股收益, 每股净资产, EPS, BVPS -> PER_SHARE
营业收入（百万元）, 净利润(百万元), 总资产, 负债合计 -> MONETARY_AMOUNT
用户数, 酒店数, 出货量, 吨, 万片/年 -> COUNT_OR_VOLUME
```

### Unit compatibility rules

#### RATIO_MULTIPLE

Allowed refined unit/action:

```text
x
倍
multiple
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

For EV/EBITDA, PE, PB, PS, EV/Sales with numeric values like `15.3`, `11.7`, `10.4`, use:

```text
refined_unit = x
refined_unit_repair_action = UNIT_RATIO_MULTIPLE_X
```

or, if the project prefers blank display unit:

```text
refined_unit = ""
refined_unit_repair_action = UNIT_NOT_APPLICABLE_RATIO_MULTIPLE
```

The chosen convention must be consistent and recorded in the manifest.

#### PERCENTAGE_OR_MARGIN

Allowed refined unit/action:

```text
%
pct
percentage
UNIT_PERCENT_FROM_MARGIN_CONTEXT
UNIT_PERCENT_FROM_RATIO_CONTEXT_COMPATIBLE
```

346B3 may preserve `%` for ROE, ROA, EBIT Margin, 毛利率, 净利率, (+/-%) rows when context supports it.

#### PER_SHARE

Allowed refined unit/action:

```text
元/股
港元/股
RMB/share
HKD/share
USD/share
UNIT_PER_SHARE_CONTEXT
```

For 每股收益 / 每股净资产 / EPS / BVPS rows with values like `8.59`, `9.6`, `10.98`, do not use `%`.

If the source context only says `每股净资产` without explicit currency, use a conservative sidecar action:

```text
refined_unit = ""
refined_unit_repair_action = NEEDS_UNIT_CURRENCY_CONTEXT_PER_SHARE
refined_recovery_decision = NEEDS_HUMAN_REVIEW or NEEDS_RULE_REFINEMENT
```

Unless the table/header/context explicitly supports 元/股 or currency/share.

#### MONETARY_AMOUNT

Allowed refined unit/action:

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

Do not inherit monetary units into percentage, ratio/multiple, or per-share rows.

#### UNKNOWN

Do not promote automatically.

---

## Refinement decisions

Each input recovered candidate receives one of:

```text
REFINED_SAFE_RECOVERED_DEMO_CANDIDATE
REFINED_DEMOTED_TO_HUMAN_REVIEW
REFINED_DEMOTED_TO_STILL_LIMITED
REFINED_NEEDS_RULE_REFINEMENT
REFINED_FALSE_POSITIVE_CONFIRMED
```

Recommended behavior:

- Existing 346B2 safe candidates can remain safe if refined policy still approves them.
- `RATIO_MULTIPLE` rows previously repaired with `%` should be corrected to `x`/`UNIT_RATIO_MULTIPLE_X` or `UNIT_NOT_APPLICABLE_RATIO_MULTIPLE`, then marked safe only if value, period, metric, and evidence are otherwise valid.
- `PER_SHARE` rows previously repaired with `%` should not be automatically marked safe unless source context proves per-share currency unit. Otherwise demote to human review or rule refinement.
- `PERCENTAGE_OR_MARGIN` rows repaired with `%` can remain safe if value/period/evidence are valid.
- Any row with unknown semantic class or conflicting evidence must not be safe.

---

## Outputs

Write only under:

```text
D:\_datefac\output\recovery_rule_refinement_346b3
```

Generate:

- `recovery_rule_refinement_346b3_manifest.json`
- `recovery_rule_refinement_346b3_refined_candidates.json`
- `recovery_rule_refinement_346b3_refined_candidates.csv`
- `recovery_rule_refinement_346b3_refined_safe_candidates.json`
- `recovery_rule_refinement_346b3_refined_safe_candidates.csv`
- `recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.json`
- `recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.csv`
- `recovery_rule_refinement_346b3_corrected_per_share_rows.json`
- `recovery_rule_refinement_346b3_corrected_per_share_rows.csv`
- `recovery_rule_refinement_346b3_preserved_percentage_margin_rows.json`
- `recovery_rule_refinement_346b3_preserved_percentage_margin_rows.csv`
- `recovery_rule_refinement_346b3_demoted_rows.json`
- `recovery_rule_refinement_346b3_demoted_rows.csv`
- `recovery_rule_refinement_346b3_refined_unit_policy.json`
- `recovery_rule_refinement_346b3_refined_unit_policy.md`
- `recovery_rule_refinement_346b3_rule_change_log.json`
- `recovery_rule_refinement_346b3_rule_change_log.md`
- `recovery_rule_refinement_346b3_reaudit_preview.json`
- `recovery_rule_refinement_346b3_reaudit_preview.csv`
- `recovery_rule_refinement_346b3_expansion_readiness_report.json`
- `recovery_rule_refinement_346b3_executive_summary.md`
- `recovery_rule_refinement_346b3_artifact_index.md`
- `recovery_rule_refinement_346b3_next_plan.md`

Do not modify 346B or 346B2 outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = RECOVERY_RULE_REFINEMENT_346B3_READY
input_stage = POST_346B2_RECOVERY_RULE_REFINEMENT
qa_fail_count = 0
no_write_back_proof_passed = true
input_345d_decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY
input_346a_decision = VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY
input_346a2_decision = MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY
input_346b_decision = QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY
input_346b2_decision = RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY
input_recovered_candidate_count = 70
input_safe_recovered_candidate_count = 32
input_false_positive_suspect_count = 38
refined_candidate_count
refined_safe_candidate_count
remaining_false_positive_suspect_count
corrected_ratio_multiple_unit_count
corrected_per_share_unit_count
preserved_percentage_margin_unit_count
demoted_candidate_count
needs_human_review_count
needs_rule_refinement_count
needs_vlm_count
unit_percent_from_ratio_context_deprecated = true
semantic_unit_policy_applied = true
safe_to_reaudit
safe_to_expand_recovery
safe_to_expand_recovery_reason
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

`safe_to_expand_recovery` should generally remain false until a follow-up QA audit, such as `346B2R Refined Recovery Candidate QA Reaudit`, confirms the refined results.

---

## Reports

Executive summary must explain:

- why 346B3 follows 346B2;
- what went wrong in 346B unit recovery;
- how semantic unit classes fix the problem;
- how many ratio/multiple rows were corrected;
- how many per-share rows were corrected or demoted;
- how many percentage/margin rows were preserved;
- refined safe candidate count;
- remaining false-positive suspect count;
- whether the refined result is ready for re-audit;
- why no live VLM calls were made;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B2R Refined Recovery Candidate QA Reaudit` if refined candidates were produced and need independent QA;
- `346B3R Recovery Rule Refinement Patch` if material risks remain after refinement;
- `346B4 Full Quality-Limited Recovery Expansion` only after a re-audit confirms `safe_to_expand_recovery = true`;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B3_recovery_rule_refinement.md`
- `datefac/benchmark/recovery_rule_refinement_346b3.py`
- `datefac/benchmark/recovery_rule_refinement_346b3_report.py`
- `tools/run_recovery_rule_refinement_346b3.py`
- `tests/benchmark/test_recovery_rule_refinement_346b3.py`
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
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B3 output dir
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
python -m py_compile datefac\benchmark\recovery_rule_refinement_346b3.py datefac\benchmark\recovery_rule_refinement_346b3_report.py tools\run_recovery_rule_refinement_346b3.py tests\benchmark\test_recovery_rule_refinement_346b3.py
python -m pytest tests\benchmark\test_recovery_rule_refinement_346b3.py -q
python tools\run_recovery_rule_refinement_346b3.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a --mineru-image-path-binding-fix-346a2-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2 --quality-limited-row-recovery-pilot-346b-dir D:\_datefac\output\quality_limited_row_recovery_pilot_346b --recovery-candidate-qa-audit-346b2-dir D:\_datefac\output\recovery_candidate_qa_audit_346b2 --output-dir D:\_datefac\output\recovery_rule_refinement_346b3
```

Tests must verify:

- outputs exist;
- valid 345D/346A/346A2/346B/346B2 inputs produce READY;
- invalid required inputs fail clearly;
- 70 input recovered candidates are processed;
- raw values and source lineage are preserved;
- `UNIT_PERCENT_FROM_RATIO_CONTEXT` is deprecated or replaced;
- EV/EBITDA / PE / PB / PS rows are no longer assigned `%`;
- ratio/multiple rows receive compatible refined unit/action;
- per-share rows are no longer assigned `%`;
- per-share rows are either repaired with compatible per-share unit evidence or demoted;
- percentage/margin rows preserve compatible `%` when valid;
- refined/demoted/count metrics close against input recovered candidates;
- safe_to_expand_recovery remains false until re-audit;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- official rules/assets flags remain false;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B3 entry.

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
8. input recovered/safe/false-positive counts.
9. refined candidate and refined safe counts.
10. remaining false-positive suspect count.
11. corrected ratio/multiple unit count.
12. corrected per-share unit count.
13. preserved percentage/margin unit count.
14. demoted/human-review/rule-refinement/VLM counts.
15. UNIT_PERCENT_FROM_RATIO_CONTEXT replacement summary.
16. safe-to-reaudit and safe-to-expand flags.
17. live VLM call count.
18. official rules/assets modified flags.
19. formal export generated / demo export only flags.
20. final gate status.
21. first file to open.
22. next recommended step.
23. `git status -sb`.
24. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
