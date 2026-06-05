# DateFac 324N Task
## Official Scope Patch Cycle Closure

## Context

324M post-patch regression validation is complete and pushed to remote main.

324M commit:

```text
e473d316d3b0945da814217e95474532d0401d74
```

324M output dir:

```text
D:\_datefac\output\post_patch_regression_validation_324m
```

324M result:

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
decision = POST_PATCH_REGRESSION_VALIDATION_324M_READY_WITH_WARNINGS
```

324M warning is historical only:

```text
current_duplicate_count = 3
new_duplicate_delta_count = 0
```

324N is a closure/reporting stage. It must not modify official assets.

## Goal

Implement 324N: close the 324 official scope patch cycle and generate a cycle-closure report.

The closure should summarize the entire 324 path from scope-noise refinement to official patch regression:

```text
324A scope noise refinement
324B human review / escalation
324C safe adjudicator request prep
324D response collection
324E schema validation + deterministic gate
324F human confirmation
324G sandbox replay
324H official rule candidate
324I controlled proposal
324J dry run
324K human approval
324L official patch application
324M post-patch regression
```

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply new semantic rules.
- Do not mark anything trusted directly in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use cached outputs from 324A through 324M only.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324N source/report/runner files.

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
D:\_datefac\output\post_patch_regression_validation_324m
```

Reference inputs:

```text
D:\_datefac\output\scope_noise_refinement_324a
D:\_datefac\output\scope_noise_human_review_324b
D:\_datefac\output\scope_noise_human_review_324b_reviewed
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
D:\_datefac\output\scope_noise_adjudicator_response_collection_324d
D:\_datefac\output\scope_noise_response_schema_validation_324e
D:\_datefac\output\scope_noise_human_confirmation_324f
D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed
D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
D:\_datefac\output\official_rule_candidate_from_324g_324h
D:\_datefac\output\controlled_official_proposal_from_324h_324i
D:\_datefac\output\controlled_official_proposal_dry_run_324j
D:\_datefac\output\controlled_official_proposal_human_approval_324k
D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed
D:\_datefac\output\official_patch_application_324l
D:\_datefac\output\official_semantic_patch_cycle_closure_323o
D:\_datefac\output\remaining_burden_planning_323p
```

Official assets may be read only for final visibility/reference:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/official_scope_patch_cycle_closure_324n.py
datefac/semantic/official_scope_patch_cycle_closure_324n_report.py
tools/run_official_scope_patch_cycle_closure_324n.py
```

## Output directory

```text
D:\_datefac\output\official_scope_patch_cycle_closure_324n
```

Suggested outputs:

```text
official_scope_patch_cycle_closure_324n_summary.json
official_scope_patch_cycle_closure_324n_qa.json
official_scope_patch_cycle_closure_324n_closure.json
official_scope_patch_cycle_closure_324n_summary.xlsx
official_scope_patch_cycle_closure_324n_stage_timeline.xlsx
official_scope_patch_cycle_closure_324n_report.md
official_scope_patch_cycle_closure_324n_no_apply_proof.json
```

## Required behavior

1. Validate 324M readiness:

```text
decision = POST_PATCH_REGRESSION_VALIDATION_324M_READY_WITH_WARNINGS
qa_fail_count = 0
official_rule_visibility_total = 1
scope_rules_visible = 1
alias_rules_visible = 0
affected_candidate_count = 42
trusted_gain_324m = 0
review_reduction_324m = 42
out_of_scope_or_rejected_gain_324m = 42
core_false_exclusion_count = 0
new_duplicate_delta_count = 0
conflict_count = 0
rollback_artifact_check_passed = true
no_official_asset_modification_during_324m = true
```

2. Summarize 324 cycle counts:

```text
324 official rule count = 1
324 scope rule count = 1
324 alias rule count = 0
324 trusted_gain = 0
324 review_reduction = 42
324 out_of_scope_or_rejected_gain = 42
324 affected_candidate_count = 42
```

3. Combine with previous official patch cycles if available:

From 323O:

```text
322 official rule count = 10
322 trusted_gain = 49
322 review_reduction = 287
323 official rule count = 6
323 trusted_gain = 44
323 review_reduction = 129
combined 322+323 official rule count = 16
combined 322+323 trusted_gain = 93
combined 322+323 review_reduction = 416
```

After 324, expected cumulative:

```text
combined official rule count = 17
combined trusted_gain = 93
combined review_reduction = 458
combined out_of_scope_or_rejected_gain includes +42 from 324
```

If 323O fields differ, use actual source values and clearly report the computed result.

4. Summarize remaining burden using 323P if available:

```text
remaining_unknown_metric_candidate_count = 2897
remaining_unit_unknown_candidate_count = 491
remaining_manual_review_count = 3071
```

If a fresh recomputation is not available, explicitly mark remaining burden as inherited from 323P / pre-324 and do not fabricate a new global count.

5. Record the 324 warning status:

```text
historical duplicates unchanged only
current_duplicate_count = 3
new_duplicate_delta_count = 0
```

6. Confirm official assets were not modified during 324N.
7. Generate closure summary, QA, stage timeline, report, and no-apply proof.
8. Recommend next-cycle direction.

## Next-cycle planning guidance

Because 324 consumed the remaining refined scope-noise candidate and produced only one official scope rule, recommend moving back to high-impact alias candidates or remaining safe scope candidates depending on available review-ready inventory.

At minimum, report:

```text
recommended_next_cycle_direction_primary = alias_candidates
recommended_next_cycle_direction_secondary = duplicate_cleanup_or_unit_holdout_diagnosis
reason = scope_noise refined queue now mostly exhausted after 324A/324L, while alias review-ready inventory remains larger but riskier.
```

Do not propose unit-related automation as primary unless evidence has improved, because unit-related holdout remained unsafe in 323P.

## Expected 324N summary metrics

```text
official_rule_count_324 = 1
scope_rule_count_324 = 1
alias_rule_count_324 = 0
trusted_gain_324 = 0
review_reduction_324 = 42
out_of_scope_or_rejected_gain_324 = 42
affected_candidate_count_324 = 42
core_false_exclusion_count_324 = 0
new_duplicate_delta_count_324 = 0
conflict_count_324 = 0
rollback_artifact_check_passed_324 = true
qa_fail_count = 0
```

Expected decision:

```text
OFFICIAL_SCOPE_PATCH_CYCLE_324N_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING
```

If only historical duplicate warnings remain, still use the closure decision and record warning status separately.

If blocking QA fails:

```text
OFFICIAL_SCOPE_PATCH_CYCLE_324N_NOT_READY
```

## Suggested command

```bash
python tools/run_official_scope_patch_cycle_closure_324n.py \
  --post-patch-regression-dir D:\_datefac\output\post_patch_regression_validation_324m \
  --official-patch-application-dir D:\_datefac\output\official_patch_application_324l \
  --previous-cycle-closure-dir D:\_datefac\output\official_semantic_patch_cycle_closure_323o \
  --remaining-burden-dir D:\_datefac\output\remaining_burden_planning_323p \
  --output-dir D:\_datefac\output\official_scope_patch_cycle_closure_324n
```

If safe defaults are implemented:

```bash
python tools/run_official_scope_patch_cycle_closure_324n.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\official_scope_patch_cycle_closure_324n.py datefac\semantic\official_scope_patch_cycle_closure_324n_report.py tools\run_official_scope_patch_cycle_closure_324n.py
```

Then run the 324N runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/official_scope_patch_cycle_closure_324n.py
git add datefac/semantic/official_scope_patch_cycle_closure_324n_report.py
git add tools/run_official_scope_patch_cycle_closure_324n.py
```

Suggested commit message:

```text
Add 324N official scope patch cycle closure
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 324 cycle summary metrics.
5. Cumulative official patch metrics.
6. Warning status.
7. Remaining burden status.
8. Recommended next-cycle direction.
9. No official asset modification confirmation.
10. QA fail count.
11. Decision.
12. Git status result.
13. Commit hash.
14. Push result.
