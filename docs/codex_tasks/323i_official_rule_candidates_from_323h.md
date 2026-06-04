# DateFac 323I Task
## Official Rule Candidates from 323H Sandbox Replay

## Context

323H human-confirmed sandbox replay is complete and pushed to remote main.

323H commit:

```text
58bc164c91c6c1954b3102ae714221e2106d7104
```

323H output dir:

```text
D:\_datefac\output\human_confirmed_sandbox_replay_323h
```

323H result:

```text
confirmed_suggestion_count = 11
alias_confirmed_suggestion_count = 2
scope_confirmed_suggestion_count = 9
sandbox_rule_count = 11
alias_sandbox_rule_count = 2
scope_sandbox_rule_count = 9
effective_unique_rule_count = 6
affected_candidate_count = 129
trusted_gain_323h = 44
review_reduction_323h = 129
out_of_scope_or_rejected_gain_323h = 85
alias_trusted_gain_323h = 44
alias_review_reduction_323h = 44
scope_trusted_gain_323h = 0
scope_review_reduction_323h = 85
scope_out_of_scope_gain_323h = 85
core_false_exclusion_count = 0
duplicate_count = 3
conflict_count = 0
qa_fail_count = 0
decision = HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_REVIEW_WITH_WARNINGS
```

Important warning:

```text
323H found duplicate source scope labels. This is not a blocking replay failure, but 323I must dedupe and generate candidates from effective unique sandbox rules rather than blindly promoting all 11 source suggestions.
```

## Goal

Implement 323I: convert 323H sandbox replay evidence into official rule candidates.

323I is a candidate-generation stage only. It must not modify official semantic assets and must not apply rules.

The expected result is a candidate package suitable for the later controlled proposal / dry-run / human approval flow.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to official assets.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 323H outputs and cached evidence only.
- Process only 323H sandbox replay outputs.
- Do not promote all 11 source suggestions directly. Use effective unique rule candidates.
- Preserve duplicate source suggestions as provenance, not as separate duplicate official candidates.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 323I source/report/runner files.

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
D:\_datefac\output\human_confirmed_sandbox_replay_323h
```

Expected files may include:

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
```

Reference inputs:

```text
D:\_datefac\output\human_confirmed_suggestion_proposals_323g_reviewed
D:\_datefac\output\raw_response_schema_validation_323f
D:\_datefac\output\post_patch_regression_validation_322o
```

Official assets may be read for conflict/reference checks only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

## Suggested files

```text
datefac/semantic/official_rule_candidates_from_sandbox.py
datefac/semantic/official_rule_candidates_from_sandbox_report.py
tools/run_official_rule_candidates_from_sandbox_323i.py
```

## Output directory

```text
D:\_datefac\output\official_rule_candidates_from_sandbox_323i
```

Suggested outputs:

```text
official_rule_candidates_from_sandbox_323i_summary.json
official_rule_candidates_from_sandbox_323i_qa.json
official_rule_candidates_from_sandbox_323i_rule_candidates.json
official_rule_candidates_from_sandbox_323i_rule_candidates.xlsx
official_rule_candidates_from_sandbox_323i_alias_candidates.xlsx
official_rule_candidates_from_sandbox_323i_scope_candidates.xlsx
official_rule_candidates_from_sandbox_323i_duplicate_source_groups.xlsx
official_rule_candidates_from_sandbox_323i_conflict_report.xlsx
official_rule_candidates_from_sandbox_323i_notes.md
```

## Required behavior

1. Validate 323H readiness.
2. Load 323H sandbox rule set and replay evidence.
3. Deduplicate source rules into effective unique candidate rules.
4. Preserve duplicate source confirmations in provenance.
5. Generate official rule candidate records, not official rules.
6. Verify candidate composition:
   - expected source sandbox rules = 11
   - expected effective unique candidates = 6, unless replay evidence proves a different safe unique count
   - expected alias candidates = 2
   - expected unique scope candidates should be derived from 323H duplicate grouping
7. Preserve impact metrics:
   - affected_candidate_count = 129
   - trusted_gain = 44
   - review_reduction = 129
   - out_of_scope_or_rejected_gain = 85
8. Check duplicates, conflicts, already-official overlaps, and core false exclusion evidence.
9. Generate candidate package and QA.

## Candidate record schema

Each candidate should include:

```text
candidate_id
candidate_type
operation_type
normalized_label
source_sandbox_rule_ids
source_confirmation_ids
source_request_ids
suggested_target_metric_if_any
candidate_action
expected_affected_candidate_count
expected_trusted_gain
expected_review_reduction
expected_out_of_scope_or_rejected_gain
sample_evidence
provenance
risk_flags
sandbox_replay_evidence
rollback_note
candidate_status
```

Recommended candidate status:

```text
READY_FOR_CONTROLLED_PROPOSAL
NEEDS_ADDITIONAL_REVIEW
REJECTED_DUPLICATE
REJECTED_CONFLICT
```

Only candidates with no conflict and valid replay evidence should be `READY_FOR_CONTROLLED_PROPOSAL`.

## Readiness checks

Require from 323H:

```text
qa_fail_count = 0
core_false_exclusion_count = 0
conflict_count = 0
affected_candidate_count = 129
trusted_gain_323h = 44
review_reduction_323h = 129
out_of_scope_or_rejected_gain_323h = 85
```

Allow the 323H decision:

```text
HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_REVIEW_WITH_WARNINGS
```

only if the only warning is duplicate source rules and 323I successfully deduplicates them.

## Decision

If candidate generation succeeds and all ready candidates are deduped and conflict-free:

```text
OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_FOR_323J_CONTROLLED_PROPOSAL
```

If only non-blocking warnings remain:

```text
OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_NOT_READY
```

## Suggested command

```bash
python tools/run_official_rule_candidates_from_sandbox_323i.py \
  --sandbox-replay-dir D:\_datefac\output\human_confirmed_sandbox_replay_323h \
  --reviewed-confirmation-dir D:\_datefac\output\human_confirmed_suggestion_proposals_323g_reviewed \
  --output-dir D:\_datefac\output\official_rule_candidates_from_sandbox_323i
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\official_rule_candidates_from_sandbox.py datefac\semantic\official_rule_candidates_from_sandbox_report.py tools\run_official_rule_candidates_from_sandbox_323i.py
```

Then run the 323I runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/official_rule_candidates_from_sandbox.py
git add datefac/semantic/official_rule_candidates_from_sandbox_report.py
git add tools/run_official_rule_candidates_from_sandbox_323i.py
```

Suggested commit message:

```text
Add 323I official rule candidates from sandbox
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. 323I output directory.
4. Source sandbox rule count.
5. Effective unique candidate count.
6. Alias / scope candidate counts.
7. Ready / review / rejected candidate counts.
8. Duplicate source grouping result.
9. Impact metrics carried forward.
10. Core false exclusion result.
11. Conflict count.
12. qa_fail_count.
13. decision.
14. git status result.
15. commit hash.
16. push result.
