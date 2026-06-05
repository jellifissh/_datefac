# DateFac 324M Task
## Post-Patch Regression Validation after 324L Official Scope Patch

## Context

324L official patch application is complete and pushed to remote main.

324L commit:

```text
c03a71e0621f664a8b54c92410c4794cd172f5b3
```

324L output dir:

```text
D:\_datefac\output\official_patch_application_324l
```

324L result:

```text
approved_patch_operation_count = 1
alias_approved_patch_operation_count = 0
scope_approved_patch_operation_count = 1
applied_operation_count = 1
idempotent_operation_count = 0
applied_or_idempotent_operation_count = 1
target_official_asset_modified = D:\_datefac\data\mapping\formal_scope_rules.json
alias_official_asset_unchanged = true
affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
duplicate_count_before = 3
duplicate_count_after = 3
duplicate_count_delta = 0
qa_fail_count = 0
decision = OFFICIAL_PATCH_APPLICATION_324L_READY_FOR_324M_POST_PATCH_REGRESSION
```

324M is mandatory because 324L modified an official semantic asset.

Target official asset now containing the 324L rule:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
```

Rule expected to be visible:

```text
SEM_SCOPE_324L_001
```

Expected target group:

```text
core_metric_scope_exclusions
```

Expected normalized label is a long narrative investment-rating/disclosure text, not a financial metric.

## Goal

Implement 324M: post-patch regression validation for the official 324L scope patch.

The goal is to prove that the newly applied official scope rule is visible, has the expected effect, does not introduce new duplicates/conflicts, does not falsely exclude selected core metrics, and has readable rollback artifacts.

324M must not modify official assets.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets in 324M.
- Do not apply new semantic rules.
- Do not mark anything trusted directly in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use official assets after 324L plus cached 324L/324G/324J evidence only.
- Process only the single 324L official rule.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324M source/report/runner files.

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
D:\_datefac\output\official_patch_application_324l
```

Expected files may include:

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

Reference inputs:

```text
D:\_datefac\output\controlled_official_proposal_dry_run_324j
D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
D:\_datefac\output\post_patch_regression_validation_323n
D:\_datefac\output\router_mineru_trust_split_322b2
```

Official assets to read only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/post_patch_regression_validation_324m.py
datefac/semantic/post_patch_regression_validation_324m_report.py
tools/run_post_patch_regression_validation_324m.py
```

## Output directory

```text
D:\_datefac\output\post_patch_regression_validation_324m
```

Suggested outputs:

```text
post_patch_regression_validation_324m_summary.json
post_patch_regression_validation_324m_qa.json
post_patch_regression_validation_324m_before_after_comparison.xlsx
post_patch_regression_validation_324m_affected_candidates.xlsx
post_patch_regression_validation_324m_official_rule_visibility.xlsx
post_patch_regression_validation_324m_core_false_exclusion_check.xlsx
post_patch_regression_validation_324m_duplicate_conflict_check.xlsx
post_patch_regression_validation_324m_rollback_artifact_check.json
post_patch_regression_validation_324m_no_apply_proof.json
post_patch_regression_validation_324m_report.md
```

## Required behavior

1. Validate 324L readiness:

```text
decision = OFFICIAL_PATCH_APPLICATION_324L_READY_FOR_324M_POST_PATCH_REGRESSION
qa_fail_count = 0
approved_patch_operation_count = 1
scope_approved_patch_operation_count = 1
alias_approved_patch_operation_count = 0
applied_or_idempotent_operation_count = 1
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
expected_trusted_gain = 0
```

2. Confirm official rule visibility in `formal_scope_rules.json`:

```text
rule_id = SEM_SCOPE_324L_001
target_group = core_metric_scope_exclusions
scope_action = exclude_from_core_metric_mapping
promotion_status = PROMOTED_324L_OFFICIAL_PATCH
```

3. Confirm alias official asset is unchanged from the 324L before/after hash proof.
4. Reproduce or verify impact using cached replay/trust-split evidence:

```text
affected_candidate_count = 42
trusted_gain_324m = 0
review_reduction_324m = 42
out_of_scope_or_rejected_gain_324m = 42
```

5. Confirm no selected-core false exclusion:

```text
core_false_exclusion_count = 0
```

6. Confirm no new duplicate or conflict:

```text
new_duplicate_delta_count = 0
conflict_count = 0
```

Historical duplicate count may remain at 3 if unchanged.

7. Confirm rollback artifacts are present and readable:

```text
official_patch_application_324l_rollback_plan.json
official_patch_application_324l_rollback_instructions.md
rollback_backups/formal_scope_rules.before_324l.json
```

8. Confirm official assets are not modified during 324M:

```text
no_official_asset_modification_during_324m = true
```

9. Generate summary, QA, evidence workbooks, rollback artifact check, no-apply proof, and report.

## Expected 324M summary metrics

```text
official_rule_visibility_total = 1
scope_rules_visible = 1
alias_rules_visible = 0
affected_candidate_count = 42
trusted_gain_324m = 0
review_reduction_324m = 42
out_of_scope_or_rejected_gain_324m = 42
core_false_exclusion_count = 0
current_duplicate_count = 3
new_duplicate_delta_count = 0
conflict_count = 0
rollback_artifact_check_passed = true
no_official_asset_modification_during_324m = true
qa_fail_count = 0
```

## Decision

If all blocking checks pass and only historical duplicate warning remains:

```text
POST_PATCH_REGRESSION_VALIDATION_324M_READY_WITH_WARNINGS
```

If all checks pass with no warnings:

```text
POST_PATCH_REGRESSION_VALIDATION_324M_READY_TO_CLOSE_324_SCOPE_PATCH_CYCLE
```

If blocking QA fails:

```text
POST_PATCH_REGRESSION_VALIDATION_324M_NOT_READY
```

## Suggested command

```bash
python tools/run_post_patch_regression_validation_324m.py \
  --official-patch-application-dir D:\_datefac\output\official_patch_application_324l \
  --sandbox-replay-dir D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --output-dir D:\_datefac\output\post_patch_regression_validation_324m
```

If safe defaults are implemented:

```bash
python tools/run_post_patch_regression_validation_324m.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\post_patch_regression_validation_324m.py datefac\semantic\post_patch_regression_validation_324m_report.py tools\run_post_patch_regression_validation_324m.py
```

Then run the 324M runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/post_patch_regression_validation_324m.py
git add datefac/semantic/post_patch_regression_validation_324m_report.py
git add tools/run_post_patch_regression_validation_324m.py
```

Suggested commit message:

```text
Add 324M post-patch regression validation
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Official rule visibility counts.
5. Impact metrics.
6. Core false exclusion result.
7. Duplicate / conflict counts.
8. Rollback artifact check result.
9. No official asset modification confirmation.
10. QA fail count.
11. Decision.
12. Git status result.
13. Commit hash.
14. Push result.
