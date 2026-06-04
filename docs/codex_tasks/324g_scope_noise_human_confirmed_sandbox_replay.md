# DateFac 324G Task
## Scope Noise Human-Confirmed Sandbox Replay

## Context

324F scope noise human confirmation is complete and synced to remote main.

324F remote/main commit:

```text
ae1bc9638b460e738307a35d60dd7a1d2480967f
```

324F reviewed output dir:

```text
D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed
```

324F reviewed result:

```text
confirmation_record_count = 1
confirmed_count = 1
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_READY_FOR_324G_SANDBOX_REPLAY
```

The confirmed item is a long narrative investment-rating/disclosure text that has already passed:

```text
324A deterministic scope-noise refinement
324B human escalation to adjudicator
324C safe adjudicator request prep
324D manual raw response collection
324E schema validation + deterministic gate
324F human confirmation
```

Important interpretation:

```text
324G may sandbox replay this single human-confirmed scope-noise suggestion. It must not modify official assets and must not create official candidates directly.
```

## Goal

Implement 324G: sandbox replay for the single 324F human-confirmed scope-noise suggestion.

The goal is to simulate the effect of applying this suggestion as a sandbox scope exclusion and verify:

1. expected review reduction;
2. no selected-core false exclusion;
3. no conflicts or duplicate candidate operations;
4. no trusted regression;
5. no official asset modification.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply official semantic rules.
- Do not mark anything trusted directly in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324F reviewed output, 324E validation output, 324A/324C evidence, and cached trust split/replay evidence only.
- Process only the single confirmed 324F scope-noise suggestion.
- Do not produce official rule candidates in 324G.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324G source/report/runner files.

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
D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed
```

Expected files may include:

```text
scope_noise_human_confirmation_324f_reviewed_summary.json
scope_noise_human_confirmation_324f_reviewed_qa.json
scope_noise_human_confirmation_324f_human_confirmed_plan.json
scope_noise_human_confirmation_324f_reviewed_workbook.xlsx
```

Reference inputs:

```text
D:\_datefac\output\scope_noise_response_schema_validation_324e
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
D:\_datefac\output\scope_noise_refinement_324a
D:\_datefac\output\router_mineru_trust_split_322b2
D:\_datefac\output\post_patch_regression_validation_323n
```

Official assets may be read only for reference checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/scope_noise_human_confirmed_sandbox_replay_324g.py
datefac/semantic/scope_noise_human_confirmed_sandbox_replay_324g_report.py
tools/run_scope_noise_human_confirmed_sandbox_replay_324g.py
```

## Output directory

```text
D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
```

Suggested outputs:

```text
scope_noise_human_confirmed_sandbox_replay_324g_summary.json
scope_noise_human_confirmed_sandbox_replay_324g_qa.json
scope_noise_human_confirmed_sandbox_replay_324g_sandbox_rule_set.json
scope_noise_human_confirmed_sandbox_replay_324g_before_after_comparison.xlsx
scope_noise_human_confirmed_sandbox_replay_324g_affected_candidates.xlsx
scope_noise_human_confirmed_sandbox_replay_324g_core_false_exclusion_check.xlsx
scope_noise_human_confirmed_sandbox_replay_324g_duplicate_conflict_check.xlsx
scope_noise_human_confirmed_sandbox_replay_324g_notes.md
scope_noise_human_confirmed_sandbox_replay_324g_no_apply_proof.json
```

## Required behavior

1. Validate 324F reviewed readiness:

```text
decision = SCOPE_NOISE_HUMAN_CONFIRMATION_324F_REVIEWED_READY_FOR_324G_SANDBOX_REPLAY
qa_fail_count = 0
confirmation_record_count = 1
confirmed_count = 1
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
```

2. Load exactly one human-confirmed scope-noise suggestion.
3. Build exactly one sandbox scope exclusion rule.
4. Ensure it is not already official, or if it is already official, report idempotent/no new gain and do not double-count.
5. Replay the candidate against cached trust split / review-required data.
6. Compute before/after counts:
   - trusted total before/after;
   - review_required total before/after;
   - rejected/out-of-scope total before/after;
   - affected_candidate_count;
   - review_reduction;
   - out_of_scope_or_rejected_gain;
   - trusted_gain.
7. Verify no selected-core false exclusion.
8. Verify no conflict with existing official scope/alias rules.
9. Verify no duplicate sandbox operation.
10. Confirm official assets were not modified.
11. Generate QA, evidence workbooks, no-apply proof, and decision.

## Expected impact

Based on 324A / 324F evidence, expected impact is approximately:

```text
affected_candidate_count = 42
review_reduction_324g = 42
out_of_scope_or_rejected_gain_324g = 42
trusted_gain_324g = 0
```

The implementation should use actual cached candidate evidence as source of truth. Do not hard-code pass metrics blindly.

## Expected result if replay passes

```text
confirmed_scope_noise_count = 1
sandbox_rule_count = 1
affected_candidate_count = 42
trusted_gain_324g = 0
review_reduction_324g = 42
out_of_scope_or_rejected_gain_324g = 42
core_false_exclusion_count = 0
duplicate_count = 0
conflict_count = 0
qa_fail_count = 0
decision = SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_FOR_324H_OFFICIAL_RULE_CANDIDATE
```

If only non-blocking warnings remain, use:

```text
SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_WITH_WARNINGS
```

If blocking checks fail, use:

```text
SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_NOT_READY
```

## Suggested command

```bash
python tools/run_scope_noise_human_confirmed_sandbox_replay_324g.py \
  --human-confirmed-dir D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --previous-regression-dir D:\_datefac\output\post_patch_regression_validation_323n \
  --output-dir D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
```

If safe defaults are implemented:

```bash
python tools/run_scope_noise_human_confirmed_sandbox_replay_324g.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\scope_noise_human_confirmed_sandbox_replay_324g.py datefac\semantic\scope_noise_human_confirmed_sandbox_replay_324g_report.py tools\run_scope_noise_human_confirmed_sandbox_replay_324g.py
```

Then run the 324G runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/scope_noise_human_confirmed_sandbox_replay_324g.py
git add datefac/semantic/scope_noise_human_confirmed_sandbox_replay_324g_report.py
git add tools/run_scope_noise_human_confirmed_sandbox_replay_324g.py
```

Suggested commit message:

```text
Add 324G scope noise human-confirmed sandbox replay
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Confirmed scope-noise count.
5. Sandbox rule count.
6. Affected candidate count.
7. Trusted gain / review reduction / out-of-scope gain.
8. Core false exclusion result.
9. Duplicate / conflict counts.
10. Whether official assets were modified.
11. qa_fail_count.
12. decision.
13. git status result.
14. commit hash.
15. push result.
