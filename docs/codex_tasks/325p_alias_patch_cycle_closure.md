# DateFac 325P Task
## Alias Patch Cycle Closure

## Context

325O post-patch regression validation is complete and pushed.

325O commit:

```text
d1842859762851400457497d78940489c6168a44
```

325O output:

```text
D:\_datefac\output\post_patch_regression_validation_325o
```

325O result:

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
decision = POST_PATCH_REGRESSION_VALIDATION_325O_READY_FOR_325P_CYCLE_CLOSURE
```

325N applied 6 official alias rules to:

```text
data/overrides/semantic_alias_candidates.json::profitability
```

325P is the closure step for the 325 alias patch cycle.

## Goal

Implement 325P: close the 325 alias patch cycle and generate a consolidated cycle summary.

325P should summarize the 325A to 325O alias cycle, carry forward impact metrics, compare against previous official semantic patch cycles, record residual risks, and recommend the next project direction.

325P must be read-only and must not modify official assets.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM or semantic adjudicator.
- Use cached 322/323/324/325 evidence only.
- Do not start a new rule mining cycle in 325P.
- Do not implement Trust Engine consolidation in 325P. 325P may recommend it as the next direction.
- Do not commit output, temp, input/semantic_adjudicator_responses_*, or existing dirty files.
- Do not use git add -A or git add .
- Only precisely add 325P source/report/runner files.

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
D:\_datefac\output\post_patch_regression_validation_325o
```

References:

```text
D:\_datefac\output\official_alias_patch_application_325n
D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed
D:\_datefac\output\controlled_official_proposal_dry_run_325l
D:\_datefac\output\controlled_official_proposal_from_325j_325k
D:\_datefac\output\alias_official_rule_candidates_from_325i_325j
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
D:\_datefac\output\alias_human_confirmation_325h_reviewed
D:\_datefac\output\alias_response_schema_validation_325g
D:\_datefac\output\alias_candidate_refinement_325a
D:\_datefac\output\official_scope_patch_cycle_closure_324n
D:\_datefac\output\official_semantic_patch_cycle_closure_323o
D:\_datefac\output\remaining_burden_planning_323p
```

Official assets may be read only:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Suggested files

```text
datefac/semantic/alias_patch_cycle_closure_325p.py
datefac/semantic/alias_patch_cycle_closure_325p_report.py
tools/run_alias_patch_cycle_closure_325p.py
```

## Output directory

```text
D:\_datefac\output\alias_patch_cycle_closure_325p
```

Suggested outputs:

```text
alias_patch_cycle_closure_325p_summary.json
alias_patch_cycle_closure_325p_qa.json
alias_patch_cycle_closure_325p_closure.json
alias_patch_cycle_closure_325p_summary.xlsx
alias_patch_cycle_closure_325p_report.md
alias_patch_cycle_closure_325p_no_apply_proof.json
```

## Required behavior

1. Validate 325O readiness:

```text
decision = POST_PATCH_REGRESSION_VALIDATION_325O_READY_FOR_325P_CYCLE_CLOSURE
qa_fail_count = 0
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
```

2. Load the 325 cycle lineage from 325A through 325O where available.
3. Summarize 325 alias cycle funnel:

```text
325A input alias inventory count
325A safe alias review batch count
325D send_to_adjudicator_count
325E request_count
325G accepted_for_human_confirmation_count
325H confirmed_count
325I sandbox_alias_rule_count
325J ready candidate count
325K ready proposal count
325L patch operation count
325M approved patch operation count
325N applied or idempotent operation count
325O visible official alias rule count
```

4. Summarize official rule impact for this cycle:

```text
official_alias_rule_count_325 = 6
trusted_gain_325 = 45
review_reduction_325 = 45
out_of_scope_or_rejected_gain_325 = 0
affected_candidate_count_325 = 45
```

5. Summarize QA/safety closure:

```text
duplicate_delta_count = 0
target_conflict_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
core_false_mapping_count = 0
rollback_artifact_check_passed = true
```

6. Compare cumulative official semantic rule progress from previous closures if available:

Known prior cycle values from 324N:

```text
cumulative official rule count after 324 = 17
cumulative trusted gain after 324 = 93
cumulative review reduction after 324 = 458
```

After 325, expected cumulative values:

```text
cumulative official rule count after 325 = 23
cumulative trusted gain after 325 = 138
cumulative review reduction after 325 = 503
```

If previous closure artifacts report different numbers, use artifact values and clearly explain the source.

7. Record residual risks:

```text
existing alias asset contains historical mojibake/encoding artifacts
325O is read-only and validates visibility/target mapping/cached impact, not full production semantic recalculation
remaining burden not recomputed unless reliable current artifact exists
```

8. Recommend next direction:

Primary:

```text
330A Trust Engine Consolidation
```

Secondary:

```text
end-to-end unfamiliar PDF benchmark and delivery quality report
```

Do not recommend opening 326A rule mining immediately unless closure data strongly supports it.

9. Confirm official assets are not modified by 325P.
10. Generate QA, no-apply proof, summary workbook, closure JSON, and report.

## Expected summary metrics

```text
official_alias_rule_count_325 = 6
trusted_gain_325 = 45
review_reduction_325 = 45
out_of_scope_or_rejected_gain_325 = 0
affected_candidate_count_325 = 45
cumulative_official_rule_count_after_325 = 23
cumulative_trusted_gain_after_325 = 138
cumulative_review_reduction_after_325 = 503
qa_fail_count = 0
decision = ALIAS_PATCH_CYCLE_325P_CLOSED_READY_FOR_TRUST_ENGINE_CONSOLIDATION
```

If QA passes but residual warnings are present:

```text
ALIAS_PATCH_CYCLE_325P_CLOSED_WITH_WARNINGS_READY_FOR_TRUST_ENGINE_CONSOLIDATION
```

If blocking QA fails:

```text
ALIAS_PATCH_CYCLE_325P_NOT_READY
```

## Suggested command

```bash
python tools/run_alias_patch_cycle_closure_325p.py \
  --post-patch-regression-dir D:\_datefac\output\post_patch_regression_validation_325o \
  --official-patch-application-dir D:\_datefac\output\official_alias_patch_application_325n \
  --previous-cycle-closure-dir D:\_datefac\output\official_scope_patch_cycle_closure_324n \
  --remaining-burden-planning-dir D:\_datefac\output\remaining_burden_planning_323p \
  --output-dir D:\_datefac\output\alias_patch_cycle_closure_325p
```

## Compile check

```bash
python -m py_compile datefac\semantic\alias_patch_cycle_closure_325p.py datefac\semantic\alias_patch_cycle_closure_325p_report.py tools\run_alias_patch_cycle_closure_325p.py
```

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_patch_cycle_closure_325p.py
git add datefac/semantic/alias_patch_cycle_closure_325p_report.py
git add tools/run_alias_patch_cycle_closure_325p.py
```

Commit:

```text
Add 325P alias patch cycle closure
```

## Final report expected from Codex

Report modified files, commands run, output directory, 325 funnel counts, 325 official rule impact, cumulative progress, residual risks, next recommended direction, official asset modification confirmation, QA fail count, decision, git status, commit hash, and push result.
