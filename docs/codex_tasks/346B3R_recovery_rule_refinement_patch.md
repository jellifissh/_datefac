# 346B3R Recovery Rule Refinement Patch

## Goal

Implement `346B3R Recovery Rule Refinement Patch`.

346B4 performed a controlled expansion after the 346B3 semantic-unit recovery policy passed 346B2R re-audit:

```text
full_quality_limited_row_count = 5558
controlled_expansion_input_limit = 500
controlled_expansion_input_row_count = 500
excluded_row_touched_count = 0
already_demo_ready_row_touched_count = 0
already_346b_pilot_row_count = 0
recovered_candidate_count = 212
safe_recovered_candidate_count = 212
risky_candidate_count = 0
false_positive_guardrail_hit_count = 0
still_quality_limited_count = 252
needs_human_review_count = 14
needs_rule_refinement_count = 22
needs_vlm_count = 0
unit_semantic_mismatch_count = 0
semantic_class_unknown_count = 22
lineage_audit_passed = true
safe_to_continue_expansion = false
recommended_next_step = 346B3R Recovery Rule Refinement Patch
live_vlm_call_count = 0
```

346B4 was successful as a controlled expansion, but it found 22 rows whose semantic class remained unknown. Because `safe_to_continue_expansion = false`, broader expansion is blocked until these rule gaps are audited and patched.

346B3R must answer:

> What are the 22 semantic-class-unknown / needs-rule-refinement rows found by 346B4, which deterministic classifier or unit-policy patches are safe to add, and which rows must remain limited or human-review-only?

This task is a rule-refinement patch over the 346B4 findings. It must not run a new expansion by default, must not recover rows upstream, and must not call live VLM/LLM APIs.

---

## Strategic alignment

Follow the root playbook:

```text
DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md
```

Required doctrine:

- Treat 346B4 as a controlled expansion, not a production migration.
- Patch deterministic semantic classification and unit policy only where evidence supports the rule.
- Keep unknown or ambiguous rows limited or human-review-only.
- Preserve raw values and source lineage.
- Never overwrite source data.
- Do not call live VLM/LLM APIs.
- Do not run OCR.
- Do not rerun MinerU.
- Do not modify official normalization rules or official alias assets.
- Re-audit again after rule patch before any larger expansion.

346B3R is a patch stage, not an expansion stage. Expansion beyond the 500-row controlled batch belongs to a later step only after QA passes.

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

346B4 output:

```text
D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
```

346B3R output:

```text
D:\_datefac\output\recovery_rule_refinement_patch_346b3r
```

---

## Milestone ledger requirement

This task must update:

```text
D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md
```

Append a concise 346B3R entry after successful implementation and validation.

The ledger entry must include:

- task id: `346B3R`
- decision: `RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY`
- input 345D dir
- input 346A dir
- input 346A2 dir
- input 346B dir
- input 346B2 dir
- input 346B3 dir
- input 346B2R dir
- input 346B4 dir
- output dir
- 346B4 controlled expansion input row count
- 346B4 safe recovered candidate count
- 346B4 semantic class unknown count
- 346B4 needs rule refinement count
- audited unknown/refinement row count
- patchable rule gap count
- non-patchable row count
- proposed semantic classifier patch count
- proposed unit policy patch count
- rows converted from UNKNOWN to known semantic class count
- rows kept as human review count
- rows kept quality-limited count
- rows requiring future VLM count
- safe-to-replay-346B4 flag
- safe-to-continue-expansion flag, expected false until replay/QA passes
- live VLM call count: `0`
- no-write-back confirmation
- gate status: all false
- next recommended step

If the ledger has unrelated dirty changes, append only the 346B3R entry. Do not overwrite unrelated edits. Do not use broad reset/checkout commands.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `DATEFAC_TACTICAL_CLEANING_PLAYBOOK.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/346B3R_recovery_rule_refinement_patch.md`

Do not scan the whole repository.

Inspect only:

- 345D output dir
- 346B3 output dir
- 346B2R output dir
- 346B4 output dir
- the milestone ledger
- the root tactical playbook

---

## Runner inputs

Support:

```powershell
--full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d
--recovery-rule-refinement-346b3-dir D:\_datefac\output\recovery_rule_refinement_346b3
--refined-recovery-candidate-qa-reaudit-346b2r-dir D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r
--controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4
--output-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r
```

Optional knobs:

```powershell
--strict-patch true
--max-patch-rows 22
--include-human-review-triage true
--include-still-limited-triage true
--max-context-chars 4000
```

Default behavior:

- read 346B4 manifest and guardrail summary;
- read 346B4 needs-rule-refinement rows;
- read 346B4 semantic class distribution;
- read 346B4 recovery results;
- read 346B3 refined unit policy as the current baseline;
- read 346B2R manifest as proof that 346B3 policy was safe before expansion;
- classify the 22 unknown/refinement rows into patchable vs non-patchable rule gaps;
- produce a patched semantic classifier/unit policy sidecar;
- do not apply the patch to official rules/assets;
- do not rerun 346B4 by default;
- do not recover or promote new rows upstream;
- output patch recommendations, row triage, and replay-readiness metadata only.

---

## Inputs to read

From 346B4:

- `controlled_quality_limited_recovery_expansion_346b4_manifest.json`
- `controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_recovery_results.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json`
- `controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.json` or `.csv`
- `controlled_quality_limited_recovery_expansion_346b4_expansion_readiness_report.json`

From 346B3:

- `recovery_rule_refinement_346b3_refined_unit_policy.json`
- `recovery_rule_refinement_346b3_refined_unit_policy.md`
- `recovery_rule_refinement_346b3_rule_change_log.json` or `.md`

From 346B2R:

- `refined_recovery_candidate_qa_reaudit_346b2r_manifest.json`
- `refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json`

From 345D if needed:

- `full_structured_demo_export_package_345d_manifest.json`
- quality-limited rows only for source-row context lookup by id

Validate:

- 346B3 decision is `RECOVERY_RULE_REFINEMENT_346B3_READY`
- 346B2R decision is `REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY`
- 346B2R `safe_to_expand_recovery = true`
- 346B4 decision is `CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY`
- 346B4 `qa_fail_count = 0`
- 346B4 `semantic_class_unknown_count = 22`
- 346B4 `needs_rule_refinement_count = 22`
- 346B4 `safe_to_continue_expansion = false`
- all live VLM call counts are `0`
- all formal/client/production gates are false

---

## Patch logic

### 1. Audit the 22 rule-refinement rows

Every 346B4 row in `needs_rule_refinement` must be audited and assigned one patch triage decision:

```text
PATCHABLE_SEMANTIC_CLASS_RULE
PATCHABLE_UNIT_POLICY_RULE
PATCHABLE_ALIAS_PATTERN_RULE
NON_PATCHABLE_NEEDS_HUMAN_REVIEW
NON_PATCHABLE_KEEP_QUALITY_LIMITED
NON_PATCHABLE_NEEDS_VLM_LATER
```

Counts must close against the 346B4 needs-rule-refinement count.

---

### 2. Proposed semantic classes

For patchable rows, propose one of:

```text
MONETARY_AMOUNT
PERCENTAGE_OR_MARGIN
RATIO_MULTIPLE
PER_SHARE
COUNT_OR_VOLUME
TEXT_OR_LABEL
```

Rows that remain ambiguous must stay non-patchable. Do not force UNKNOWN rows into a class just to make metrics look better. The spreadsheet gods do not reward courage, only consistency.

---

### 3. Patch candidate types

Possible safe classifier patches:

```text
COUNT_OR_VOLUME_PATTERN
TEXT_LABEL_PATTERN
SPECIAL_RATIO_PATTERN
SPECIAL_PER_SHARE_PATTERN
SPECIAL_MONETARY_PATTERN
SPECIAL_PERCENTAGE_PATTERN
DOMAIN_SPECIFIC_UNIT_PATTERN
```

Examples:

- `用户数`, `付费用户`, `酒店数`, `门店数`, `出货量`, `销量`, `产能`, `片/年`, `吨`, `万片/年` -> likely `COUNT_OR_VOLUME` if numeric and context supports it.
- `take rate`, `率`, `margin`, `ROE`, `ROA` -> likely `PERCENTAGE_OR_MARGIN` if value/context supports percent semantics.
- `PE`, `PB`, `PS`, `EV/EBITDA`, `EV/Sales` -> `RATIO_MULTIPLE`.
- `EPS`, `BVPS`, `每股收益`, `每股净资产` -> `PER_SHARE`.
- `收入`, `利润`, `资产`, `负债`, `现金流`, `费用` -> `MONETARY_AMOUNT` if unit/context supports money.

If patch confidence is low, leave the row in human review or still-limited.

---

### 4. Unit policy patching

Only propose unit policy patches that are compatible with semantic class:

- `COUNT_OR_VOLUME`: 家, 人, 万人, 亿人, 吨, 万吨, 片, 万片/年, 次, 间夜, 件, 台, 套, %, only when the metric is explicitly a rate/share of count.
- `TEXT_OR_LABEL`: no numeric unit promotion.
- `SPECIAL_RATIO_PATTERN`: x / 倍 / UNIT_RATIO_MULTIPLE_X.
- `SPECIAL_PER_SHARE_PATTERN`: 元/股 / 港元/股 / RMB/share / HKD/share / USD/share, or keep limited if currency/share is missing.
- `MONETARY_AMOUNT`: 元 / 万元 / 百万元 / 亿元 / currency variants.
- `PERCENTAGE_OR_MARGIN`: % / pct / percentage.

Do not introduce rules that would re-create the 346B `UNIT_PERCENT_FROM_RATIO_CONTEXT` bug.

---

### 5. Patch safety decision

Each row gets one final patch safety decision:

```text
PATCH_SAFE_TO_REPLAY
PATCH_REQUIRES_REAUDIT
PATCH_UNSAFE_KEEP_LIMITED
PATCH_UNSAFE_HUMAN_REVIEW
PATCH_UNSAFE_VLM_LATER
```

A row can be `PATCH_SAFE_TO_REPLAY` only if:

- semantic class is known after proposed patch;
- unit policy is compatible;
- value is parseable or sanitizer-repairable;
- period/source lineage are present;
- no evidence conflict is detected;
- no formal/client/production gate is opened.

Even if patches are safe to replay, `safe_to_continue_expansion` should remain false until a replay/audit step verifies them.

---

## Outputs

Write only under:

```text
D:\_datefac\output\recovery_rule_refinement_patch_346b3r
```

Generate:

- `recovery_rule_refinement_patch_346b3r_manifest.json`
- `recovery_rule_refinement_patch_346b3r_unknown_row_audit.json`
- `recovery_rule_refinement_patch_346b3r_unknown_row_audit.csv`
- `recovery_rule_refinement_patch_346b3r_patchable_rows.json`
- `recovery_rule_refinement_patch_346b3r_patchable_rows.csv`
- `recovery_rule_refinement_patch_346b3r_non_patchable_rows.json`
- `recovery_rule_refinement_patch_346b3r_non_patchable_rows.csv`
- `recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json`
- `recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.csv`
- `recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json`
- `recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.csv`
- `recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json`
- `recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.md`
- `recovery_rule_refinement_patch_346b3r_patch_safety_review.json`
- `recovery_rule_refinement_patch_346b3r_patch_safety_review.csv`
- `recovery_rule_refinement_patch_346b3r_replay_readiness_report.json`
- `recovery_rule_refinement_patch_346b3r_executive_summary.md`
- `recovery_rule_refinement_patch_346b3r_artifact_index.md`
- `recovery_rule_refinement_patch_346b3r_next_plan.md`

Do not modify 346B4 outputs. Do not create formal client delivery files.

---

## Manifest metrics

Manifest must include:

```text
decision = RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY
input_stage = POST_346B4_RECOVERY_RULE_REFINEMENT_PATCH
qa_fail_count = 0
no_write_back_proof_passed = true
input_346b3_decision = RECOVERY_RULE_REFINEMENT_346B3_READY
input_346b2r_decision = REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY
input_346b4_decision = CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY
input_346b2r_safe_to_expand_recovery = true
input_346b4_safe_to_continue_expansion = false
input_346b4_controlled_expansion_input_row_count = 500
input_346b4_safe_recovered_candidate_count = 212
input_346b4_semantic_class_unknown_count = 22
input_346b4_needs_rule_refinement_count = 22
audited_unknown_row_count
patchable_rule_gap_count
non_patchable_row_count
proposed_semantic_classifier_patch_count
proposed_unit_policy_patch_count
rows_converted_from_unknown_to_known_semantic_class_count
rows_kept_human_review_count
rows_kept_quality_limited_count
rows_requiring_future_vlm_count
patch_safe_to_replay_count
patch_requires_reaudit_count
patch_unsafe_count
safe_to_replay_346b4
safe_to_continue_expansion = false
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

`safe_to_continue_expansion` should remain false until a replay/audit step confirms the patched rules.

---

## Reports

Executive summary must explain:

- why 346B3R follows 346B4;
- what blocked continuation after 346B4;
- how many unknown/refinement rows were audited;
- how many are patchable;
- how many must remain human-review or quality-limited;
- proposed semantic classifier patches;
- proposed unit policy patches;
- whether the patch is safe to replay;
- why no live VLM/OCR/MinerU rerun happened;
- why outputs remain demo-only and sidecar-only;
- next recommended step.

Next plan must recommend one of:

- `346B4R Controlled Expansion Replay With Patched Rules` if patches are safe to replay;
- `346B3R2 Recovery Rule Refinement Patch Follow-up` if many unknown rows remain non-patchable but rule clues exist;
- `346B4Q Controlled Expansion QA Audit` after replay produces updated recovered candidates;
- `346C0 Live VLM Pilot Request Execution` only if the team explicitly decides to run prepared VLM requests;
- `345G Demo Presentation Slide Outline` if the project returns to presentation work;
- `344G Strict Human Review Ingestion` only after a genuinely human-filled 344F workbook exists.

Also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/346B3R_recovery_rule_refinement_patch.md`
- `datefac/benchmark/recovery_rule_refinement_patch_346b3r.py`
- `datefac/benchmark/recovery_rule_refinement_patch_346b3r_report.py`
- `tools/run_recovery_rule_refinement_patch_346b3r.py`
- `tests/benchmark/test_recovery_rule_refinement_patch_346b3r.py`
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
- mutate 346B4 outputs
- mutate MinerU outputs
- modify official normalization rules
- modify official alias assets
- apply recovery suggestions upstream
- generate formal client delivery artifacts
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify previous LLM response dirs
- modify `input/`, `temp/`, or existing `output/` content except the new 346B3R output dir
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
python -m py_compile datefac\benchmark\recovery_rule_refinement_patch_346b3r.py datefac\benchmark\recovery_rule_refinement_patch_346b3r_report.py tools\run_recovery_rule_refinement_patch_346b3r.py tests\benchmark\test_recovery_rule_refinement_patch_346b3r.py
python -m pytest tests\benchmark\test_recovery_rule_refinement_patch_346b3r.py -q
python tools\run_recovery_rule_refinement_patch_346b3r.py --full-structured-demo-export-package-345d-dir D:\_datefac\output\full_structured_demo_export_package_345d --recovery-rule-refinement-346b3-dir D:\_datefac\output\recovery_rule_refinement_346b3 --refined-recovery-candidate-qa-reaudit-346b2r-dir D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r --controlled-quality-limited-recovery-expansion-346b4-dir D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4 --output-dir D:\_datefac\output\recovery_rule_refinement_patch_346b3r
```

Tests must verify:

- outputs exist;
- valid 345D/346B3/346B2R/346B4 inputs produce READY;
- invalid required inputs fail clearly;
- 346B4 needs-rule-refinement rows are audited;
- unknown/refinement counts close;
- patchable and non-patchable counts close;
- proposed semantic classifier patches do not recreate `%` on ratio/multiple or per-share rows;
- unit policy patches are compatible with proposed semantic classes;
- non-patchable rows remain limited/human-review/VLM-later;
- no official rules/assets are modified;
- no prior outputs are mutated;
- no live VLM calls occur;
- no OCR/MinerU rerun occurs;
- formal/client/production gates remain false;
- milestone ledger is updated with 346B3R entry.

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
8. input 346B4 controlled/safe/unknown/refinement counts.
9. audited unknown/refinement row count.
10. patchable vs non-patchable counts.
11. proposed semantic classifier patch count.
12. proposed unit policy patch count.
13. rows converted from UNKNOWN to known semantic class count.
14. rows kept human-review / quality-limited / future VLM counts.
15. patch safe-to-replay / requires-reaudit / unsafe counts.
16. safe-to-replay 346B4 and safe-to-continue expansion flags.
17. live VLM call count.
18. official rules/assets modified flags.
19. formal export generated / demo export only flags.
20. final gate status.
21. first file to open.
22. next recommended step.
23. `git status -sb`.
24. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/MinerU outputs/protected dirty files.
