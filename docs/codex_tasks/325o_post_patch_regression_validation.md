# DateFac 325O Task
## Post-Patch Regression Validation for 325N Official Alias Patch

## Context

325N official alias patch application is complete and pushed.

325N commit:

```text
e267d7d1b609d8b25fcfcc526346489ce256def5
```

325N output:

```text
D:\_datefac\output\official_alias_patch_application_325n
```

325N result:

```text
approved_patch_operation_count = 6
alias_approved_patch_operation_count = 6
scope_approved_patch_operation_count = 0
applied_operation_count = 6
idempotent_operation_count = 0
applied_or_idempotent_operation_count = 6
conflicting_existing_alias_count = 0
target_conflict_count = 0
duplicate_delta_count = 0
affected_candidate_count = 45
expected_trusted_gain = 45
expected_review_reduction = 45
expected_out_of_scope_or_rejected_gain = 0
qa_fail_count = 0
decision = OFFICIAL_ALIAS_PATCH_APPLICATION_325N_READY_FOR_325O_POST_PATCH_REGRESSION
```

Official asset modified by 325N:

```text
data/overrides/semantic_alias_candidates.json
```

Asset that must remain unchanged:

```text
data/mapping/formal_scope_rules.json
```

325O is a read-only post-patch regression validation stage.

## Goal

Implement 325O to verify that the 6 alias rules applied by 325N are visible in the official alias asset and reproduce the expected 325I impact.

Expected impact:

```text
affected_candidate_count = 45
trusted_gain_325o = 45
review_reduction_325o = 45
out_of_scope_or_rejected_gain_325o = 0
```

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM or semantic adjudicator.
- Use cached 325N/325M/325L/325K/325J/325I evidence only.
- Process only the 6 alias rules applied by 325N.
- Do not commit output, temp, input/semantic_adjudicator_responses_*, or existing dirty files.
- Do not use git add -A or git add .
- Only precisely add 325O source/report/runner files.

Existing dirty files to leave untouched:

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
D:\_datefac\output\official_alias_patch_application_325n
```

References:

```text
D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed
D:\_datefac\output\controlled_official_proposal_dry_run_325l
D:\_datefac\output\controlled_official_proposal_from_325j_325k
D:\_datefac\output\alias_official_rule_candidates_from_325i_325j
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
D:\_datefac\output\router_mineru_trust_split_322b2
```

Official assets to read only:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Suggested files

```text
datefac/semantic/post_patch_regression_validation_325o.py
datefac/semantic/post_patch_regression_validation_325o_report.py
tools/run_post_patch_regression_validation_325o.py
```

## Output directory

```text
D:\_datefac\output\post_patch_regression_validation_325o
```

Suggested outputs:

```text
post_patch_regression_validation_325o_summary.json
post_patch_regression_validation_325o_qa.json
post_patch_regression_validation_325o_before_after_comparison.xlsx
post_patch_regression_validation_325o_affected_candidates.xlsx
post_patch_regression_validation_325o_official_rule_visibility.json
post_patch_regression_validation_325o_duplicate_conflict_report.xlsx
post_patch_regression_validation_325o_rollback_artifact_check.json
post_patch_regression_validation_325o_no_apply_proof.json
post_patch_regression_validation_325o_report.md
```

## Required behavior

1. Validate 325N readiness:

```text
decision = OFFICIAL_ALIAS_PATCH_APPLICATION_325N_READY_FOR_325O_POST_PATCH_REGRESSION
qa_fail_count = 0
applied_or_idempotent_operation_count = 6
alias_approved_patch_operation_count = 6
duplicate_delta_count = 0
target_conflict_count = 0
affected_candidate_count = 45
expected_trusted_gain = 45
expected_review_reduction = 45
expected_out_of_scope_or_rejected_gain = 0
```

2. Load exactly 6 applied alias operations from 325N.
3. Confirm all 6 aliases are visible in `data/overrides/semantic_alias_candidates.json::profitability`.
4. Confirm each official alias maps to the expected target metric.
5. Confirm `data/mapping/formal_scope_rules.json` remains unchanged relative to 325N hash summary.
6. Confirm 325O itself does not modify official assets by comparing hashes before and after 325O.
7. Re-check semantic constraints:

```text
EBIT -> EBIT only
ROE -> ROE only
每股收益(最新摊薄) -> diluted_EPS or EPS_diluted only
经调整 EPS -> adjusted_EPS only
经调整归母净利润 -> adjusted_attributable_net_profit or adjusted_parent_net_profit only
归母净利率 -> attributable_net_margin or parent_net_margin only
```

8. Validate rollback artifacts from 325N exist.
9. Generate QA, no-apply proof, report, and visibility artifacts.

## Expected summary metrics

```text
official_rule_visibility_total = 6
official_alias_rules_visible = 6
missing_official_alias_rule_count = 0
wrong_target_metric_count = 0
affected_candidate_count = 45
trusted_gain_325o = 45
review_reduction_325o = 45
out_of_scope_or_rejected_gain_325o = 0
target_conflict_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
core_false_mapping_count = 0
rollback_artifact_check_passed = true
no_official_asset_modification_during_325o = true
qa_fail_count = 0
```

Expected decision:

```text
POST_PATCH_REGRESSION_VALIDATION_325O_READY_FOR_325P_CYCLE_CLOSURE
```

If QA passes with only historical warnings:

```text
POST_PATCH_REGRESSION_VALIDATION_325O_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
POST_PATCH_REGRESSION_VALIDATION_325O_NOT_READY
```

## Suggested command

```bash
python tools/run_post_patch_regression_validation_325o.py \
  --official-patch-application-dir D:\_datefac\output\official_alias_patch_application_325n \
  --sandbox-replay-dir D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --output-dir D:\_datefac\output\post_patch_regression_validation_325o
```

## Compile check

```bash
python -m py_compile datefac\semantic\post_patch_regression_validation_325o.py datefac\semantic\post_patch_regression_validation_325o_report.py tools\run_post_patch_regression_validation_325o.py
```

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/post_patch_regression_validation_325o.py
git add datefac/semantic/post_patch_regression_validation_325o_report.py
git add tools/run_post_patch_regression_validation_325o.py
```

Commit:

```text
Add 325O post-patch regression validation
```

## Final report expected from Codex

Report modified files, commands run, output dir, official rule visibility counts, missing/wrong target counts, impact metrics, duplicate/conflict/semantic mismatch counts, rollback artifact check, no official asset modification confirmation, QA fail count, decision, git status, commit hash, push result, verification result, sample scope, and residual risks.
