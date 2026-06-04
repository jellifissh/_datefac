# DateFac 323N Task
## Post-Patch Regression Validation after 323M Official Patch Application

## Context

323M official patch application is complete and pushed to remote main.

323M commit:

```text
104c4725f948ccaed4f5e9ca71b5ccd35393d2dc
```

323M output dir:

```text
D:\_datefac\output\official_patch_application_323m
```

323M result:

```text
approved_patch_count = 6
alias_approved_patch_count = 2
scope_approved_patch_count = 4
applied_or_idempotent_operation_count = 6
applied_operation_count = 0
idempotent_operation_count = 6
affected_candidate_count = 129
expected_trusted_gain = 44
expected_review_reduction = 129
expected_out_of_scope_or_rejected_gain = 85
qa_fail_count = 0
decision = OFFICIAL_PATCH_APPLICATION_323M_READY_FOR_323N_POST_PATCH_REGRESSION
```

Important note:

```text
The first 323M run applied the 6 operations. A later idempotency rerun reported applied_operation_count = 0 and idempotent_operation_count = 6, which is expected because the official assets already contain the 323M rules.
```

Official assets modified by 323M:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

Expected 323M official patch content:

```text
alias rules = 2
scope rules = 4
```

Expected impact:

```text
affected_candidate_count = 129
expected_trusted_gain = 44
expected_review_reduction = 129
expected_out_of_scope_or_rejected_gain = 85
```

323N is the mandatory post-patch regression validation stage.

## Goal

Implement 323N: post-patch regression validation after the official 323M semantic patch application.

323N must verify that the newly applied 323M official rules are visible, that their sandbox-proven impact is preserved, and that no regression or false exclusion appears.

323N must not modify official assets and must not apply any additional rules.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply additional semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use existing official assets, 323M outputs, and cached trust split / replay evidence only.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 323N source/report/runner files.

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

Primary 323M output:

```text
D:\_datefac\output\official_patch_application_323m
```

Reference outputs:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_323lr
D:\_datefac\output\controlled_official_proposal_dry_run_323k
D:\_datefac\output\controlled_official_proposal_from_323i_323j
D:\_datefac\output\official_rule_candidates_from_323h_323i
D:\_datefac\output\human_confirmed_sandbox_replay_323h
D:\_datefac\output\post_patch_regression_validation_322o
D:\_datefac\output\router_mineru_trust_split_322b2
```

Official assets to read only:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/post_patch_regression_validation_323n.py
datefac/semantic/post_patch_regression_validation_323n_report.py
tools/run_post_patch_regression_validation_323n.py
```

## Output directory

```text
D:\_datefac\output\post_patch_regression_validation_323n
```

Suggested outputs:

```text
post_patch_regression_validation_323n_summary.json
post_patch_regression_validation_323n_qa.json
post_patch_regression_validation_323n_official_rule_visibility.xlsx
post_patch_regression_validation_323n_before_after_comparison.xlsx
post_patch_regression_validation_323n_affected_candidates.xlsx
post_patch_regression_validation_323n_core_false_exclusion_check.xlsx
post_patch_regression_validation_323n_duplicate_conflict_check.xlsx
post_patch_regression_validation_323n_rollback_artifact_check.xlsx
post_patch_regression_validation_323n_notes.md
```

## Required behavior

1. Validate 323M readiness.
2. Read official semantic assets and verify 323M rules are visible:
   - 2 alias rules with promotion/status from 323M.
   - 4 scope rules with promotion/status from 323M.
3. Verify expected source linkage is present:
   - source approval id
   - source dry-run patch operation id
   - source controlled proposal id
   - source rule candidate id
   - source request / confirmation / group ids
4. Verify no new duplicate or conflict was introduced by 323M.
   - Existing historical duplicates may be reported as warnings if unchanged.
   - New 323M duplicate delta must be zero.
5. Validate carried-forward impact metrics:
   - affected_candidate_count = 129
   - trusted_gain = 44
   - review_reduction = 129
   - out_of_scope_or_rejected_gain = 85
6. Verify no selected-core false exclusion.
7. Verify no trusted regression, no manual review increase, and no unexpected unknown/unit unknown increase against cached replay evidence.
8. Verify rollback artifacts from 323M exist and are readable.
9. Produce QA and decision.

## Readiness checks

Require from 323M summary/QA:

```text
decision = OFFICIAL_PATCH_APPLICATION_323M_READY_FOR_323N_POST_PATCH_REGRESSION
qa_fail_count = 0
approved_patch_count = 6
alias_approved_patch_count = 2
scope_approved_patch_count = 4
applied_or_idempotent_operation_count = 6
affected_candidate_count = 129
expected_trusted_gain = 44
expected_review_reduction = 129
expected_out_of_scope_or_rejected_gain = 85
```

## Expected 323N summary metrics

```text
official_rule_visibility_total = 6
alias_rules_visible = 2
scope_rules_visible = 4
affected_candidate_count = 129
trusted_gain_323n = 44
review_reduction_323n = 129
out_of_scope_or_rejected_gain_323n = 85
core_false_exclusion_count = 0
new_duplicate_delta_count = 0
conflict_count = 0
rollback_artifact_check_passed = true
qa_fail_count = 0
```

## Decision

If all regression checks pass:

```text
POST_PATCH_REGRESSION_VALIDATION_323N_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE
```

If only non-blocking historical duplicate warnings remain:

```text
POST_PATCH_REGRESSION_VALIDATION_323N_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
POST_PATCH_REGRESSION_VALIDATION_323N_NOT_READY
```

## Suggested command

```bash
python tools/run_post_patch_regression_validation_323n.py \
  --official-patch-dir D:\_datefac\output\official_patch_application_323m \
  --sandbox-replay-dir D:\_datefac\output\human_confirmed_sandbox_replay_323h \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --previous-regression-dir D:\_datefac\output\post_patch_regression_validation_322o \
  --output-dir D:\_datefac\output\post_patch_regression_validation_323n
```

If safe defaults are implemented:

```bash
python tools/run_post_patch_regression_validation_323n.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\post_patch_regression_validation_323n.py datefac\semantic\post_patch_regression_validation_323n_report.py tools\run_post_patch_regression_validation_323n.py
```

Then run the 323N runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/post_patch_regression_validation_323n.py
git add datefac/semantic/post_patch_regression_validation_323n_report.py
git add tools/run_post_patch_regression_validation_323n.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323N post-patch regression validation
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. 323N output directory.
4. Official rule visibility counts.
5. Impact metrics validated.
6. Core false exclusion result.
7. Duplicate / conflict counts.
8. Rollback artifact check result.
9. qa_fail_count.
10. decision.
11. git status result.
12. commit hash.
13. push result.
