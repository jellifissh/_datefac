# DateFac 323H Task
## Human-Confirmed Semantic Suggestions Sandbox Replay

## Context

323G prepare and validate-reviewed are complete on `main`.

Relevant commits:

```text
bf9d17112f6d08a1e554adba0134ad5b4d06a010  Add 323G human-confirmed suggestion proposals
fc1d907e9effd28d20e9148fa107fdcea4262a80  Fix 323G reviewed timestamp serialization
```

323G reviewed output:

```text
D:\_datefac\output\human_confirmed_suggestion_proposals_323g_reviewed
```

Reviewed result:

```text
confirmation_record_count = 11
pending_count = 0
invalid_decision_count = 0
confirmed_suggestion_count = 11
rejected_suggestion_count = 0
needs_more_info_count = 0
qa_fail_count = 0
decision = HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_READY_FOR_323H_SANDBOX_REPLAY
decision_distribution = {'CONFIRM': 11}
```

## Goal

Implement 323H: replay the 11 human-confirmed semantic suggestions in sandbox only.

323H must estimate candidate impact and safety before any official rule candidate stage.

Expected composition:

```text
total_confirmed_suggestion_count = 11
alias_confirmed_suggestion_count = 2
scope_confirmed_suggestion_count = 9
```

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to official assets.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use cached candidate / trust split outputs only.
- Process only the 11 confirmed suggestions from 323G reviewed validation.
- Do not include rejected / needs-more-info / pending / invalid suggestions.
- Sandbox output is evidence only, not an official rule change.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 323H source/report/runner files.

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
D:\_datefac\output\human_confirmed_suggestion_proposals_323g_reviewed
```

Cached trust split input:

```text
D:\_datefac\output\router_mineru_trust_split_322b2
```

Reference outputs:

```text
D:\_datefac\output\post_patch_regression_validation_322o
D:\_datefac\output\raw_response_schema_validation_323f
D:\_datefac\output\safe_adjudicator_subset_323d
D:\_datefac\output\human_confirmed_suggestion_proposals_323g
```

Official assets may be read only for conflict/reference checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

## Suggested files

```text
datefac/semantic/human_confirmed_sandbox_replay.py
datefac/semantic/human_confirmed_sandbox_replay_report.py
tools/run_human_confirmed_sandbox_replay_323h.py
```

## Output directory

```text
D:\_datefac\output\human_confirmed_sandbox_replay_323h
```

Suggested outputs:

```text
human_confirmed_sandbox_replay_323h_summary.json
human_confirmed_sandbox_replay_323h_qa.json
human_confirmed_sandbox_replay_323h_sandbox_rule_set.json
human_confirmed_sandbox_replay_323h_affected_candidates.xlsx
human_confirmed_sandbox_replay_323h_before_after_comparison.xlsx
human_confirmed_sandbox_replay_323h_alias_replay.xlsx
human_confirmed_sandbox_replay_323h_scope_replay.xlsx
human_confirmed_sandbox_replay_323h_conflict_report.xlsx
human_confirmed_sandbox_replay_323h_core_false_exclusion_check.xlsx
human_confirmed_sandbox_replay_323h_notes.md
```

## Required behavior

1. Validate 323G reviewed readiness.
2. Load the 11 confirmed suggestions.
3. Build sandbox-only rule set:
   - 2 alias sandbox rules.
   - 9 scope / out-of-scope sandbox rules.
4. Load cached candidates from the trust split output.
5. Apply sandbox rule set in memory/output-only mode.
6. Measure:
   - affected_candidate_count
   - trusted_gain_323h
   - review_reduction_323h
   - out_of_scope_or_rejected_gain_323h
   - alias_trusted_gain_323h
   - scope_review_reduction_323h
7. Check duplicate rules, conflicts, selected-core false exclusions, trusted regression, and unexpected unknown/unit/manual-review regressions.
8. Generate before/after comparison artifacts.
9. Produce QA and decision.

## Required readiness checks

Require from 323G reviewed summary/QA:

```text
decision = HUMAN_CONFIRMED_SUGGESTION_PROPOSALS_323G_REVIEWED_READY_FOR_323H_SANDBOX_REPLAY
qa_fail_count = 0
confirmation_record_count = 11
confirmed_suggestion_count = 11
rejected_suggestion_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
```

## Decision

If sandbox replay succeeds and no blocking QA fails:

```text
HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_323I_OFFICIAL_RULE_CANDIDATES
```

If replay succeeds but has warnings:

```text
HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_REVIEW_WITH_WARNINGS
```

If blocking QA fails:

```text
HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_NOT_READY
```

## Suggested command

```bash
python tools/run_human_confirmed_sandbox_replay_323h.py \
  --reviewed-confirmation-dir D:\_datefac\output\human_confirmed_suggestion_proposals_323g_reviewed \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --post-patch-regression-dir D:\_datefac\output\post_patch_regression_validation_322o \
  --output-dir D:\_datefac\output\human_confirmed_sandbox_replay_323h
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\human_confirmed_sandbox_replay.py datefac\semantic\human_confirmed_sandbox_replay_report.py tools\run_human_confirmed_sandbox_replay_323h.py
```

Then run the 323H runner.

## Git workflow

Use precise adds only, for example:

```bash
git add datefac/semantic/human_confirmed_sandbox_replay.py
git add datefac/semantic/human_confirmed_sandbox_replay_report.py
git add tools/run_human_confirmed_sandbox_replay_323h.py
```

Suggested commit message:

```text
Add 323H human-confirmed sandbox replay
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. 323H output directory.
4. Confirmed suggestion counts.
5. Sandbox rule counts.
6. Affected candidate count.
7. Trusted gain / review reduction / out-of-scope gain.
8. Alias vs scope contribution.
9. Core false exclusion result.
10. Duplicate / conflict counts.
11. qa_fail_count.
12. decision.
13. git status result.
14. commit hash.
15. push result.
