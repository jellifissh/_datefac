# DateFac 324L Task
## Official Patch Application for 324K Approved Scope Proposal

## Context

324K human approval reviewed validation has passed.

324K reviewed output dir:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed
```

324K reviewed result:

```text
approval_record_count = 1
approved_patch_operation_count = 1
scope_approved_patch_operation_count = 1
alias_approved_patch_operation_count = 0
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_READY_FOR_324L_OFFICIAL_PATCH_APPLICATION
official_assets_modified = false
```

324L is the first step in this 324 cycle that may write an official semantic asset.

Target official asset:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
```

Target group:

```text
core_metric_scope_exclusions
```

Expected patch scope:

```text
approved_patch_operation_count = 1
scope_approved_patch_operation_count = 1
alias_approved_patch_operation_count = 0
operation_type = ADD_SCOPE_EXCLUSION
```

Expected carried impact:

```text
expected_affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
```

## Goal

Implement 324L: apply the single human-approved 324K official patch operation to the official scope rules asset.

324L must update only the intended official semantic asset and must generate full before/after snapshots, applied-operation logs, rollback backups, rollback instructions, QA, and proof of exactly which official file was modified.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official alias override assets.
- Do not mark anything trusted directly in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324K reviewed final approved patch plan and 324J dry-run outputs only.
- Process only the single approved 324K patch operation.
- Write only the intended official scope asset:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
```

- Do not write:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Precisely add only:
  - 324L source/report/runner files
  - `data/mapping/formal_scope_rules.json`

Known existing dirty files to leave untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

## Inputs

Primary input:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed
```

Expected files may include:

```text
controlled_official_proposal_human_approval_324k_reviewed_summary.json
controlled_official_proposal_human_approval_324k_reviewed_qa.json
controlled_official_proposal_human_approval_324k_final_approved_patch_plan.json
controlled_official_proposal_human_approval_324k_reviewed_workbook.xlsx
```

Reference input:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_324k
D:\_datefac\output\controlled_official_proposal_dry_run_324j
D:\_datefac\output\controlled_official_proposal_from_324h_324i
D:\_datefac\output\official_rule_candidate_from_324g_324h
D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
```

Official asset to write:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
```

Official asset to verify unchanged:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

## Suggested files

```text
datefac/semantic/official_patch_application_324l.py
datefac/semantic/official_patch_application_324l_report.py
tools/run_official_patch_application_324l.py
```

## Output directory

```text
D:\_datefac\output\official_patch_application_324l
```

Suggested outputs:

```text
official_patch_application_324l_summary.json
official_patch_application_324l_qa.json
official_patch_application_324l_before_snapshot.json
official_patch_application_324l_after_snapshot.json
official_patch_application_324l_applied_operations.json
official_patch_application_324l_applied_operations.xlsx
official_patch_application_324l_apply_proof.json
official_patch_application_324l_rollback_plan.json
official_patch_application_324l_rollback_instructions.md
rollback_backups/formal_scope_rules.before_324l.json
```

## Required behavior

1. Validate 324K reviewed readiness:

```text
decision = CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_READY_FOR_324L_OFFICIAL_PATCH_APPLICATION
qa_fail_count = 0
approval_record_count = 1
approved_patch_operation_count = 1
scope_approved_patch_operation_count = 1
alias_approved_patch_operation_count = 0
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
```

2. Load exactly one approved patch operation.
3. Validate operation type is `ADD_SCOPE_EXCLUSION`.
4. Validate target asset is exactly:

```text
data/mapping/formal_scope_rules.json
```

5. Validate target group is exactly:

```text
core_metric_scope_exclusions
```

6. Compute before hashes for:
   - `data/mapping/formal_scope_rules.json`
   - `data/overrides/semantic_alias_candidates.json`
7. Create rollback backup for `formal_scope_rules.json` before modification.
8. Apply one official scope exclusion rule into `formal_scope_rules.json`.
9. If the exact rule is already present, treat as idempotent and do not duplicate.
10. Never write alias override asset.
11. Compute after hashes and validate:
    - scope asset changed only if a new rule was applied;
    - scope asset unchanged if operation was idempotent;
    - alias asset unchanged always;
    - no other official assets modified.
12. Generate before/after snapshots, applied operation log, rollback plan, rollback instructions, apply proof, and QA.
13. Commit only the 324L source/report/runner files and `data/mapping/formal_scope_rules.json`.

## Expected result if first application writes one new rule

```text
approved_patch_operation_count = 1
scope_approved_patch_operation_count = 1
alias_approved_patch_operation_count = 0
applied_or_idempotent_operation_count = 1
applied_operation_count = 1
idempotent_operation_count = 0
affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
conflict_count = 0
qa_fail_count = 0
decision = OFFICIAL_PATCH_APPLICATION_324L_READY_FOR_324M_POST_PATCH_REGRESSION
```

## Expected result if rerun is idempotent

```text
approved_patch_operation_count = 1
applied_or_idempotent_operation_count = 1
applied_operation_count = 0
idempotent_operation_count = 1
qa_fail_count = 0
decision = OFFICIAL_PATCH_APPLICATION_324L_READY_FOR_324M_POST_PATCH_REGRESSION
```

## Suggested command

```bash
python tools/run_official_patch_application_324l.py \
  --reviewed-approval-dir D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed \
  --dry-run-dir D:\_datefac\output\controlled_official_proposal_dry_run_324j \
  --output-dir D:\_datefac\output\official_patch_application_324l
```

If safe defaults are implemented:

```bash
python tools/run_official_patch_application_324l.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\official_patch_application_324l.py datefac\semantic\official_patch_application_324l_report.py tools\run_official_patch_application_324l.py
```

Then run the 324L runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/official_patch_application_324l.py
git add datefac/semantic/official_patch_application_324l_report.py
git add tools/run_official_patch_application_324l.py
git add data/mapping/formal_scope_rules.json
```

Suggested commit message:

```text
Apply 324L official scope patch
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Approved patch operation counts.
5. Applied / idempotent counts.
6. Target official asset modified.
7. Alias official asset unchanged confirmation.
8. Affected candidate count and carried impact metrics.
9. Rollback artifact paths.
10. QA fail count.
11. Decision.
12. Git status result.
13. Commit hash.
14. Push result.
