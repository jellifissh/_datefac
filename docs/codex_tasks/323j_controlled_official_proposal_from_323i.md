# DateFac 323J Task
## Controlled Official Proposal from 323I Rule Candidates

## Context

323I official rule candidates from 323H sandbox replay is complete and pushed to remote main.

323I commit:

```text
e790ed5e45b32175a86e9d7d0a1a1901914dd78c
```

323I output dir:

```text
D:\_datefac\output\official_rule_candidates_from_323h_323i
```

323I result:

```text
source_sandbox_rule_count = 11
effective_unique_candidate_count = 6
alias_candidate_count = 2
scope_candidate_count = 4
ready_for_controlled_proposal_count = 6
needs_review_candidate_count = 0
rejected_candidate_count = 0
duplicate_source_group_count = 3
affected_candidate_count = 129
trusted_gain_323i = 44
review_reduction_323i = 129
out_of_scope_or_rejected_gain_323i = 85
carried_forward_core_false_exclusion_count = 0
conflict_group_count = 0
qa_fail_count = 0
decision = OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_FOR_323J_CONTROLLED_PROPOSAL
```

323J is the next step:

> Convert the 6 deduplicated ready candidates from 323I into a controlled official proposal package.

323J must not modify official assets and must not apply rules.

## Goal

Implement 323J: controlled official proposal from 323I candidates.

The goal is to produce a reviewable proposal package that describes exactly how the 6 candidates would later be applied to official semantic assets.

Expected composition:

```text
total_controlled_proposal_count = 6
alias_controlled_proposal_count = 2
scope_controlled_proposal_count = 4
```

Expected carried-forward impact:

```text
affected_candidate_count = 129
expected_trusted_gain = 44
expected_review_reduction = 129
expected_out_of_scope_or_rejected_gain = 85
```

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 323I outputs and cached evidence only.
- Process only 323I candidates with status READY_FOR_CONTROLLED_PROPOSAL.
- Preserve duplicate source suggestions as provenance only.
- Do not re-expand back to 11 source suggestions.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 323J source/report/runner files.

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
D:\_datefac\output\official_rule_candidates_from_323h_323i
```

Expected files may include:

```text
official_rule_candidates_from_323h_323i_summary.json
official_rule_candidates_from_323h_323i_qa.json
official_rule_candidates_from_323h_323i_rule_candidates.json
official_rule_candidates_from_323h_323i_rule_candidates.xlsx
official_rule_candidates_from_323h_323i_alias_candidates.xlsx
official_rule_candidates_from_323h_323i_scope_candidates.xlsx
official_rule_candidates_from_323h_323i_duplicate_source_groups.xlsx
official_rule_candidates_from_323h_323i_conflict_report.xlsx
```

Reference input:

```text
D:\_datefac\output\human_confirmed_sandbox_replay_323h
D:\_datefac\output\human_confirmed_suggestion_proposals_323g_reviewed
```

Official assets may be read for target validation only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/controlled_official_proposal_from_candidates.py
datefac/semantic/controlled_official_proposal_from_candidates_report.py
tools/run_controlled_official_proposal_from_candidates_323j.py
```

## Output directory

```text
D:\_datefac\output\controlled_official_proposal_from_candidates_323j
```

Suggested outputs:

```text
controlled_official_proposal_from_candidates_323j_summary.json
controlled_official_proposal_from_candidates_323j_qa.json
controlled_official_proposal_from_candidates_323j_proposals.json
controlled_official_proposal_from_candidates_323j_proposals.xlsx
controlled_official_proposal_from_candidates_323j_alias_proposals.xlsx
controlled_official_proposal_from_candidates_323j_scope_proposals.xlsx
controlled_official_proposal_from_candidates_323j_duplicate_source_provenance.xlsx
controlled_official_proposal_from_candidates_323j_target_asset_plan.json
controlled_official_proposal_from_candidates_323j_notes.md
```

## Required behavior

1. Validate 323I readiness.
2. Load exactly 6 ready candidates.
3. Build controlled proposal records from these 6 candidates.
4. Keep proposal-only boundary. Do not apply anything.
5. Resolve intended official target asset or target group for each candidate.
6. Preserve source sandbox rule ids, source confirmation ids, source request ids, duplicate-source provenance, sample evidence, and replay impact.
7. Generate rollback notes for future dry-run/application stages.
8. Check already-official overlaps, target conflicts, duplicate proposal ids, missing target assets/groups, and missing provenance.
9. Generate summary, QA, proposal workbook, alias/scope proposal sheets, and target asset plan.

## Proposal record schema

Each proposal should include:

```text
proposal_id
source_candidate_id
candidate_type
operation_type
normalized_label
intended_target_asset
intended_target_group
proposed_change
source_sandbox_rule_ids
source_confirmation_ids
source_request_ids
expected_affected_candidate_count
expected_trusted_gain
expected_review_reduction
expected_out_of_scope_or_rejected_gain
sample_evidence
provenance
risk_note
rollback_note
proposal_status
```

Recommended proposal status:

```text
READY_FOR_DRY_RUN
NEEDS_ADDITIONAL_REVIEW
REJECTED_DUPLICATE
REJECTED_CONFLICT
```

## Readiness checks

Require from 323I:

```text
decision = OFFICIAL_RULE_CANDIDATES_FROM_SANDBOX_323I_READY_FOR_323J_CONTROLLED_PROPOSAL
qa_fail_count = 0
effective_unique_candidate_count = 6
alias_candidate_count = 2
scope_candidate_count = 4
ready_for_controlled_proposal_count = 6
needs_review_candidate_count = 0
rejected_candidate_count = 0
affected_candidate_count = 129
trusted_gain_323i = 44
review_reduction_323i = 129
out_of_scope_or_rejected_gain_323i = 85
carried_forward_core_false_exclusion_count = 0
conflict_group_count = 0
```

## Decision

If all controlled proposals are ready for dry run:

```text
CONTROLLED_OFFICIAL_PROPOSAL_323J_READY_FOR_323K_DRY_RUN
```

If there are only non-blocking warnings:

```text
CONTROLLED_OFFICIAL_PROPOSAL_323J_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
CONTROLLED_OFFICIAL_PROPOSAL_323J_NOT_READY
```

## Suggested command

```bash
python tools/run_controlled_official_proposal_from_candidates_323j.py \
  --official-candidates-dir D:\_datefac\output\official_rule_candidates_from_323h_323i \
  --sandbox-replay-dir D:\_datefac\output\human_confirmed_sandbox_replay_323h \
  --output-dir D:\_datefac\output\controlled_official_proposal_from_candidates_323j
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\controlled_official_proposal_from_candidates.py datefac\semantic\controlled_official_proposal_from_candidates_report.py tools\run_controlled_official_proposal_from_candidates_323j.py
```

Then run the 323J runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/controlled_official_proposal_from_candidates.py
git add datefac/semantic/controlled_official_proposal_from_candidates_report.py
git add tools/run_controlled_official_proposal_from_candidates_323j.py
```

Suggested commit message:

```text
Add 323J controlled official proposal from candidates
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. 323J output directory.
4. Loaded ready candidate count.
5. Proposal counts.
6. Alias / scope proposal counts.
7. Ready / review / rejected proposal counts.
8. Target asset plan summary.
9. Duplicate / conflict counts.
10. Impact metrics carried forward.
11. qa_fail_count.
12. decision.
13. git status result.
14. commit hash.
15. push result.
