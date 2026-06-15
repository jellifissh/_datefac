# 346B2 Recovery Candidate QA Audit

## Goal

Implement `346B2 Recovery Candidate QA Audit`.

346B produced the first deterministic recovery pilot after 346A/346A2 evidence binding:

```text
full_quality_limited_row_count = 5558
pilot_input_row_count = 100
image_bound_input_count = 38
json_md_context_bound_input_count = 70
value_sanitizer_attempt_count = 100
sanitized_value_success_count = 100
sanitized_value_failure_count = 0
unit_injection_attempt_count = 92
unit_injection_success_count = 78
unit_not_applicable_count = 10
period_injection_attempt_count = 0
period_injection_success_count = 0
recovered_demo_candidate_count = 70
still_quality_limited_count = 4
needs_vlm_count = 0
needs_human_review_count = 26
downgraded_excluded_count = 0
live_vlm_call_count = 0
```

346B2 must answer:

> Are the 70 recovered demo candidates from 346B actually safe enough to keep as demo-only recovered candidates, or did the deterministic recovery rules create false positives, especially around unit repair, ratio/multiple handling, percentage handling, per-share metrics, and text/image evidence quality?

This is a QA audit of recovery results. It must not recover additional rows by default, must not call live VLM/LLM APIs, and must not mutate upstream data.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Relevant doctrine:

- Deterministic sanitizer first.
- Context state machine second.
- Text + image evidence third.
- VLM only later and only after explicit approval.
- Human review for conflicts.
- Re-audit and re-rank every repaired row.
- Never overwrite source data.
- Demo-only recovered candidates are not formal client-ready rows.

346B2 is the re-audit stage for 346B. It should be stricter than 346B, because the purpose is to catch false positives before expanding recovery to the full 5558 quality-limited rows.

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

346B recovered 70 demo-only candidates, left 26 rows for human review, and kept 4 rows quality-limited. 346B did not call VLM.

Important risk signal from 346B:

```text
UNIT_PERCENT_FROM_RATIO_CONTEXT = 78
```

346B2 must audit this carefully. It must not blindly accept `UNIT_PERCENT_FROM_RATIO_CONTEXT`, because ratio/multiple, margin/percentage, per-share, and monetary metrics have different unit semantics.

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B2 entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B2`
- decision: `RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY`
- input 345D dir
- input 346A dir
- input 346A2 dir
- input 346B dir
- output dir
- audited recovered candidate count
- safe recovered candidate count
- risky recovered candidate count
- false-positive suspect count
- unit repair risk count
- ratio/multiple unit mismatch count
- percentage unit mismatch count
- per-share unit mismatch count
- monetary unit mismatch count
- unit-not-applicable verified count
- unit-not-applicable risk count
- image-bound recovered count
- text-context-only recovered count
- needs rule refinement count
- human-review triage count
- still-limited triage count
- safe-to-expand recovery flag
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false
- next recommended step

If the ledger has unrelated dirty changes, append only the 346B2 entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B2_recovery_candidate_qa_audit.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346A output dir
- 346A2 output dir
- 346B output dir
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
--output-dir D:\_datefac\output\recovery_candidate_qa_audit_346b2
```

Optional knobs:

```powershell
--strict-audit true
--sample-needs-human-review true
--sample-still-limited true
--max-context-chars 4000
--safe-to-expand-risk-threshold 0
```

Default behavior:

- read 346B recovered demo candidates;
- read 346B still-limited, needs-human-review, needs-VLM, recovery fail reasons, and reaudit summary if present;
- read 346A2 bound rows for evidence/path/context confirmation;
- audit recovered candidates for unit, metric, value, period, and evidence consistency;
- triage 346B human-review and still-limited rows to produce rule-refinement candidates;
- do not recover new rows by default;
- do not call live VLM/LLM APIs;
- do not run OCR;
- do not mutate 345D/346A/346A2/346B outputs, MinerU outputs, official rules, or alias assets;
- write only 346B2 sidecar audit outputs.

---

## Inputs to read

From 345D:

- `full_structured_demo_export_package_345d_manifest.json`
- `full_structured_demo_export_package_345d_quality_limited_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_demo_rows.json` or `.csv`
- `full_structured_demo_export_package_345d_quality_caveats.json` or `.md`

From 346A:

- `vision_assisted_table_evidence_pilot_346a_manifest.json`
- `vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json`
- `vision_assisted_table_evidence_pilot_346a_field_repair_targets.json`
- `vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md`

From 346A2:

- `mineru_image_path_binding_fix_346a2_manifest.json`
- `mineru_image_path_binding_fix_346a2_bound_rows.json`
- `mineru_image_path_binding_fix_346a2_image_resolution_status.json`
- `mineru_image_path_binding_fix_346a2_json_md_context_index.json`
- `mineru_image_path_binding_fix_346a2_vlm_request_package.jsonl`

From 346B:

- `quality_limited_row_recovery_pilot_346b_manifest.json`
- `quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_still_limited_rows.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_needs_human_review_rows.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_needs_vlm_rows.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_downgraded_excluded_rows.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_value_sanitizer_results.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_context_injection_results.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_recovery_fail_reasons.json` or `.csv`
- `quality_limited_row_recovery_pilot_346b_reaudit_summary.json`

Validate:

- 345D decision is `FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY`
- 346A decision is `VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY`
- 346A2 decision is `MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY`
- 346B decision is `QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY`
- all input `qa_fail_count = 0`
- 346A2 `live_vlm_call_count = 0`
- 346B `live_vlm_call_count = 0`
- all formal/client/production gates are false

---

## QA audit logic

### 1. Preserve lineage

Every audited row must preserve:

```text
raw_value
sanitized_value
final_or_suggested_value
raw_metric_name
demo_normalized_metric_name
original_unit
recovered_unit
unit_repair_action
unit_repair_source
period
source_row_id
pilot_row_id
demo_export_row_id
image evidence fields
json/md context fields
346B recovery action fields
346B decision fields
```

346B2 must never overwrite these fields. It may add audit fields only.

---

### 2. Metric semantic class audit

Classify each recovered candidate into a semantic unit class using raw and normalized metric names, table context, and neighbor rows:

```text
MONETARY_AMOUNT
PERCENTAGE_OR_MARGIN
RATIO_MULTIPLE
PER_SHARE
COUNT_OR_VOLUME
TEXT_OR_LABEL
UNKNOWN
```

Use conservative rules. If uncertain, classify as `UNKNOWN` and flag for human review or rule refinement.

Examples:

```text
EV/EBITDA, PE, PB, PS, EV/Sales -> RATIO_MULTIPLE
ROE, ROA, EBIT Margin, 毛利率, 净利率, (+/-%) -> PERCENTAGE_OR_MARGIN
每股收益, 每股净资产, EPS, BVPS -> PER_SHARE
营业收入（百万元）, 净利润(百万元), 总资产, 负债合计 -> MONETARY_AMOUNT
用户数, 酒店数, 出货量, 吨, 万片/年 -> COUNT_OR_VOLUME
```

---

### 3. Unit repair audit

Audit whether the recovered unit or unit action is compatible with the metric semantic class.

Recommended compatibility matrix:

```text
MONETARY_AMOUNT:
  allowed units: 元, 万元, 百万元, 千万元, 亿元, RMB, HKD, USD and clear currency/money variants

PERCENTAGE_OR_MARGIN:
  allowed units/actions: %, pct, percentage, UNIT_NOT_APPLICABLE_PERCENTAGE if represented as percent marker

RATIO_MULTIPLE:
  allowed units/actions: 倍, x, multiple, UNIT_NOT_APPLICABLE_RATIO_MULTIPLE
  high risk: %, 百万元, 亿元, 元

PER_SHARE:
  allowed units/actions: 元/股, 港元/股, RMB/share, HKD/share, USD/share, 元, UNIT_PER_SHARE_CONTEXT
  high risk: %, 百万元, 亿元 unless explicitly part of source context

COUNT_OR_VOLUME:
  allowed units/actions: 家, 人, 万人, 亿人, 吨, 万吨, 片, 万片/年, 次, 间夜 and clear count/volume variants

UNKNOWN:
  no automatic safety approval
```

Audit special cases:

- `UNIT_PERCENT_FROM_RATIO_CONTEXT` must be flagged if applied to `RATIO_MULTIPLE` rows like EV/EBITDA, PE, PB, PS.
- `UNIT_PERCENT_FROM_RATIO_CONTEXT` may be acceptable for `PERCENTAGE_OR_MARGIN` rows only.
- `UNIT_NOT_APPLICABLE` must be split into more specific audit statuses when possible:
  - `UNIT_NOT_APPLICABLE_RATIO_MULTIPLE_VERIFIED`
  - `UNIT_NOT_APPLICABLE_PERCENTAGE_VERIFIED`
  - `UNIT_NOT_APPLICABLE_RISK_UNKNOWN`
- Per-share rows should not be treated as generic no-unit rows.

---

### 4. Evidence audit

For each recovered candidate, verify evidence strength:

```text
IMAGE_BOUND_TABLE_CROP
JSON_MD_CONTEXT_BOUND
TEXT_CONTEXT_ONLY
NO_BOUND_EVIDENCE
```

Rows promoted with `NO_BOUND_EVIDENCE` should be high risk unless the repair is purely deterministic and non-semantic.

Rows with image evidence should record the chosen image path, but 346B2 must not inspect image pixels, run OCR, or call VLM.

---

### 5. Value and period audit

Verify:

- sanitized value is parseable unless row is non-numeric by design;
- accounting negatives are preserved;
- percentage markers are not destroyed;
- period is present and not suspiciously blank;
- actual/estimate suffixes such as `A`, `E`, `Q1`, `2026Q1` are preserved when present;
- no period injection was needed in 346B unless explicitly supported.

---

### 6. Promotion safety decision

Each recovered candidate receives one of:

```text
SAFE_RECOVERED_DEMO_CANDIDATE
RISKY_RECOVERED_DEMO_CANDIDATE
FALSE_POSITIVE_SUSPECT
NEEDS_HUMAN_REVIEW
NEEDS_RULE_REFINEMENT
```

A row can be `SAFE_RECOVERED_DEMO_CANDIDATE` only if:

- value parse is valid;
- metric semantic class is not UNKNOWN;
- unit/action is compatible with metric semantic class;
- period is present or safely verified;
- evidence is bound or deterministic repair is enough;
- no high-severity issue remains;
- no text/context/evidence conflict exists;
- output remains demo-only sidecar.

Rows with incompatible unit actions must not be safe.

---

### 7. Human-review and still-limited triage

346B2 should also inspect:

```text
346B needs_human_review_rows = 26
346B still_quality_limited_rows = 4
```

Produce a triage explaining whether rows need:

```text
RULE_REFINEMENT_UNIT_CLASSIFICATION
RULE_REFINEMENT_CONTEXT_SCOPE
RULE_REFINEMENT_EVIDENCE_BINDING
HUMAN_REVIEW_REQUIRED
FUTURE_VLM_REPAIR
KEEP_LIMITED
```

Do not promote them in 346B2. This is audit/triage only.

---

## Outputs

Write only under:

```text
D:\_datefac\output\recovery_candidate_qa_audit_346b2
```

Generate:

- `recovery_candidate_qa_audit_346b2_manifest.json`
- `recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json`
- `recovery_candidate_qa_audit_346b2_recovered_candidate_audit.csv`
- `recovery_candidate_qa_audit_346b2_safe_recovered_candidates.json`
- `recovery_candidate_qa_audit_346b2_safe_recovered_candidates.csv`
- `recovery_candidate_qa_audit_346b2_risky_recovered_candidates.json`
- `recovery_candidate_qa_audit_346b2_risky_recovered_candidates.csv`
- `recovery_candidate_qa_audit_346b2_false_positive_suspects.json`
- `recovery_candidate_qa_audit_346b2_false_positive_suspects.csv`
- `recovery_candidate_qa_audit_346b2_unit_repair_audit.json`
- `recovery_candidate_qa_audit_346b2_unit_repair_audit.csv`
- `recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.json`
- `recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.csv`
- `recovery_candidate_qa_audit_346b2_evidence_strength_distribution.json`
- `recovery_candidate_qa_audit_346b2_evidence_strength_distribution.csv`
- `recovery_candidate_qa_audit_346b2_needs_human_review_triage.json`
- `recovery_candidate_qa_audit_346b2_needs_human_review_triage.csv`
- `recovery_candidate_qa_audit_346b2_still_limited_triage.json`
- `recovery_candidate_qa_audit_346b2_still_limited_triage.csv`
- `recovery_candidate_qa_audit_346b2_rule_refinement_candidates.json`
- `recovery_candidate_qa_audit_346b2_rule_refinement_candidates.csv`
- `recovery_candidate_qa_audit_346b2_expansion_readiness_report.json`
- `recovery_candidate_qa_audit_346b2_reaudit_summary.json`
- `recovery_candidate_qa_audit_346b2_executive_summary.md`
- `recovery_candidate_qa_audit_346b2_artifact_index.md`
- `recovery_candidate_qa_audit_346b2_next_plan.md`

Do not modify 346B outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY
input_stage = POST_346B_RECOVERY_CANDIDATE_QA_AUDIT
qa_fail_count = 0
no_write_back_proof_passed = true
input_345d_decision = FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY
input_346a_decision = VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY
input_346a2_decision = MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY
input_346b_decision = QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY
full_quality_limited_row_count = 5558
input_recovered_demo_candidate_count = 70
input_needs_human_review_count = 26
input_still_quality_limited_count = 4
audited_recovered_candidate_count
safe_recovered_candidate_count
risky_recovered_candidate_count
false_positive_suspect_count
needs_human_review_after_audit_count
needs_rule_refinement_count
unit_repair_audit_count
unit_repair_risk_count
ratio_multiple_unit_mismatch_count
percentage_unit_mismatch_count
per_share_unit_mismatch_count
monetary_unit_mismatch_count
unit_not_applicable_verified_count
unit_not_applicable_risk_count
image_bound_recovered_count
text_context_only_recovered_count
no_bound_evidence_recovered_count
human_review_triage_count
still_limited_triage_count
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

If many recovered rows are risky, the task should still be READY if QA passes. It must recommend rule refinement instead of pretending recovery is safe. Humans dislike bad news, which is unfortunate because databases love producing it.

---

## Reports

Executive summary must explain:

- why 346B2 follows 346B;
- how many recovered candidates were audited;
- safe vs risky vs false-positive suspect counts;
- unit repair audit results;
- semantic class distribution;
- evidence strength distribution;
- whether `UNIT_PERCENT_FROM_RATIO_CONTEXT` was safe or risky;
- triage of 26 human-review rows and 4 still-limited rows;
- whether recovery can be safely expanded beyond the 100-row pilot;
- why no live VLM calls were made;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B3 Recovery Rule Refinement` if false-positive suspects or rule risks are found;
- `346B4 Full Quality-Limited Recovery Expansion` only if `safe_to_expand_recovery = true`;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `346C Vision-Assisted Repair Response Ingestion` only after live VLM responses exist;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B2_recovery_candidate_qa_audit.md`
- `datefac/benchmark/recovery_candidate_qa_audit_346b2.py`
- `datefac/benchmark/recovery_candidate_qa_audit_346b2_report.py`
- `tools/run_recovery_candidate_qa_audit_346b2.py`
- `tests/benchmark/test_recovery_candidate_qa_audit_346b2.py`
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
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B2 output dir
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
python -m py_compile datefac\benchmark\recovery_candidate_qa_audit_346b2.py datefac\benchmark\recovery_candidate_qa_audit_346b2_report.py tools\run_recovery_candidate_qa_audit_346b2.py tests\benchmark\test_recovery_candidate_qa_audit_346b2.py
python -m pytest tests\benchmark\test_recovery_candidate_qa_audit_346b2.py -q
python tools\run_recovery_candidate_qa_audit_346b2.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --vision-assisted-table-evidence-pilot-346a-dir D:\_datefac\output\vision_assisted_table_evidence_pilot_346a --mineru-image-path-binding-fix-346a2-dir D:\_datefac\output\mineru_image_path_binding_fix_346a2 --quality-limited-row-recovery-pilot-346b-dir D:\_datefac\output\quality_limited_row_recovery_pilot_346b --output-dir D:\_datefac\output\recovery_candidate_qa_audit_346b2
```

Tests must verify:

- outputs exist;
- valid 345D/346A/346A2/346B inputs produce READY;
- invalid required inputs fail clearly;
- 70 recovered candidates are audited when present;
- raw values and source lineage are preserved;
- `EV/EBITDA` / PE / PB type metrics are classified as `RATIO_MULTIPLE`;
- margin/rate metrics are classified as `PERCENTAGE_OR_MARGIN`;
- per-share metrics are classified as `PER_SHARE`;
- monetary metrics are classified as `MONETARY_AMOUNT`;
- `UNIT_PERCENT_FROM_RATIO_CONTEXT` applied to ratio/multiple rows is flagged as risky;
- safe/risky/false-positive/human-review/rule-refinement counts close against audited recovered count;
- human-review and still-limited triage outputs are generated;
- `safe_to_expand_recovery` is false when false-positive suspects or material unit risks exist;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- official rules/assets flags remain false;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B2 entry.

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
8. audited recovered candidate count.
9. safe/risky/false-positive/human-review/rule-refinement counts.
10. unit repair audit counts.
11. semantic class distribution.
12. evidence strength distribution.
13. UNIT_PERCENT_FROM_RATIO_CONTEXT audit result.
14. human-review and still-limited triage summary.
15. safe-to-expand flag and reason.
16. live VLM call count.
17. official rules/assets modified flags.
18. formal export generated / demo export only flags.
19. final gate status.
20. first file to open.
21. next recommended step.
22. `git status -sb`.
23. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
