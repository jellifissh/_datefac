# DateFac 324I Task
## Controlled Official Proposal from 324H Rule Candidate

## Context

324H official rule candidate packaging is complete and pushed to remote main.

324H commit:

```text
455eab7443e23aac140d3ee14db18847a196fb04
```

324H output dir:

```text
D:\_datefac\output\official_rule_candidate_from_324g_324h
```

324H result:

```text
source_sandbox_rule_count = 1
candidate_count = 1
scope_candidate_count = 1
ready_for_controlled_proposal_count = 1
needs_review_candidate_count = 0
rejected_candidate_count = 0
affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
duplicate_candidate_id_count = 0
already_official_overlap_count = 0
alias_conflict_count = 0
conflict_count = 0
carried_warnings = historical_duplicates_unchanged_only:new_duplicate_delta_count=0
qa_fail_count = 0
decision = OFFICIAL_RULE_CANDIDATE_FROM_324G_324H_READY_FOR_CONTROLLED_PROPOSAL
```

324I is the next step:

> Convert the single ready 324H official rule candidate into a controlled official proposal package.

324I must not modify official assets and must not apply rules.

## Goal

Implement 324I: controlled official proposal from the single 324H scope rule candidate.

The goal is to produce a reviewable proposal package that describes exactly how the 324H candidate would later be applied to official semantic assets.

Expected composition:

```text
total_controlled_proposal_count = 1
scope_controlled_proposal_count = 1
alias_controlled_proposal_count = 0
```

Expected carried-forward impact:

```text
affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
```

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324H outputs and cached evidence only.
- Process only the single 324H candidate with status READY_FOR_CONTROLLED_PROPOSAL.
- Do not expand back to raw source records.
- Do not produce dry-run patch operations in 324I.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324I source/report/runner files.

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
D:\_datefac\output\official_rule_candidate_from_324g_324h
```

Expected files may include:

```text
official_rule_candidate_from_324g_324h_summary.json
official_rule_candidate_from_324g_324h_qa.json
official_rule_candidate_from_324g_324h_rule_candidates.json
official_rule_candidate_from_324g_324h_rule_candidates.xlsx
official_rule_candidate_from_324g_324h_scope_candidates.xlsx
```

Reference input:

```text
D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
D:\_datefac\output\scope_noise_human_confirmation_324f_reviewed
D:\_datefac\output\scope_noise_response_schema_validation_324e
D:\_datefac\output\scope_noise_safe_adjudicator_request_324c
```

Official assets may be read for target validation only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/controlled_official_proposal_from_324h.py
datefac/semantic/controlled_official_proposal_from_324h_report.py
tools/run_controlled_official_proposal_from_324h_324i.py
```

## Output directory

```text
D:\_datefac\output\controlled_official_proposal_from_324h_324i
```

Suggested outputs:

```text
controlled_official_proposal_from_324h_324i_summary.json
controlled_official_proposal_from_324h_324i_qa.json
controlled_official_proposal_from_324h_324i_proposals.json
controlled_official_proposal_from_324h_324i_proposals.xlsx
controlled_official_proposal_from_324h_324i_scope_proposals.xlsx
controlled_official_proposal_from_324h_324i_target_asset_plan.json
controlled_official_proposal_from_324h_324i_notes.md
controlled_official_proposal_from_324h_324i_no_apply_proof.json
```

## Required behavior

1. Validate 324H readiness.
2. Load exactly one ready scope candidate.
3. Build exactly one controlled proposal record.
4. Keep proposal-only boundary. Do not apply anything.
5. Resolve intended official target asset/group:

```text
data/mapping/formal_scope_rules.json::core_metric_scope_exclusions
```

6. Preserve source ids and evidence from the full chain:
   - 324A refined candidate id
   - 324B review id
   - 324C request id
   - 324D response id
   - 324E validation id
   - 324F confirmation id
   - 324G sandbox rule id
   - 324H candidate id
7. Preserve sample evidence, risk flags, reviewer/adjudicator rationale, and replay impact.
8. Include rollback notes for future dry-run/application stages.
9. Check already-official overlaps, target conflicts, duplicate proposal ids, missing target assets/groups, and missing provenance.
10. Carry historical duplicate warning as non-blocking only if `new_duplicate_delta_count = 0`.
11. Generate summary, QA, proposal workbook, scope proposal sheet, target asset plan, notes, and no-apply proof.

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
source_validation_ids
expected_affected_candidate_count
expected_trusted_gain
expected_review_reduction
expected_out_of_scope_or_rejected_gain
sample_evidence
risk_flags
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

Require from 324H:

```text
decision = OFFICIAL_RULE_CANDIDATE_FROM_324G_324H_READY_FOR_CONTROLLED_PROPOSAL
qa_fail_count = 0
source_sandbox_rule_count = 1
candidate_count = 1
scope_candidate_count = 1
ready_for_controlled_proposal_count = 1
needs_review_candidate_count = 0
rejected_candidate_count = 0
affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
duplicate_candidate_id_count = 0
already_official_overlap_count = 0
alias_conflict_count = 0
conflict_count = 0
```

## Expected 324I summary metrics

```text
loaded_ready_candidate_count = 1
proposal_count = 1
scope_proposal_count = 1
alias_proposal_count = 0
ready_for_dry_run_proposal_count = 1
needs_review_proposal_count = 0
rejected_proposal_count = 0
duplicate_proposal_id_count = 0
already_official_overlap_count = 0
target_conflict_count = 0
missing_target_asset_or_group_count = 0
missing_provenance_count = 0
expected_affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
qa_fail_count = 0
```

## Decision

If the controlled proposal is ready for dry run:

```text
CONTROLLED_OFFICIAL_PROPOSAL_FROM_324H_324I_READY_FOR_324J_DRY_RUN
```

If only non-blocking historical duplicate warnings remain:

```text
CONTROLLED_OFFICIAL_PROPOSAL_FROM_324H_324I_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
CONTROLLED_OFFICIAL_PROPOSAL_FROM_324H_324I_NOT_READY
```

## Suggested command

```bash
python tools/run_controlled_official_proposal_from_324h_324i.py \
  --official-rule-candidate-dir D:\_datefac\output\official_rule_candidate_from_324g_324h \
  --sandbox-replay-dir D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g \
  --output-dir D:\_datefac\output\controlled_official_proposal_from_324h_324i
```

If safe defaults are implemented:

```bash
python tools/run_controlled_official_proposal_from_324h_324i.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\controlled_official_proposal_from_324h.py datefac\semantic\controlled_official_proposal_from_324h_report.py tools\run_controlled_official_proposal_from_324h_324i.py
```

Then run the 324I runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/controlled_official_proposal_from_324h.py
git add datefac/semantic/controlled_official_proposal_from_324h_report.py
git add tools/run_controlled_official_proposal_from_324h_324i.py
```

Suggested commit message:

```text
Add 324I controlled official proposal from 324H
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. 324I output directory.
4. Loaded ready candidate count.
5. Proposal counts.
6. Scope / alias proposal counts.
7. Ready / review / rejected proposal counts.
8. Target asset plan summary.
9. Duplicate / conflict counts.
10. Impact metrics carried forward.
11. Carried warnings.
12. qa_fail_count.
13. decision.
14. git status result.
15. commit hash.
16. push result.
