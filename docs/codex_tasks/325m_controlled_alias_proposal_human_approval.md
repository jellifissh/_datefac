# DateFac 325M Task
## Controlled Alias Proposal Human Approval

## Context

325L controlled official proposal dry run for the 325 alias cycle is complete and pushed to remote main.

325L commit:

```text
d1b7a37a50c20d7684731290581b1689e66d8c55
```

325L output dir:

```text
D:\_datefac\output\controlled_official_proposal_dry_run_325l
```

325L result:

```text
proposal_count = 6
patch_operation_count = 6
alias_patch_operation_count = 6
scope_patch_operation_count = 0
target_asset_file_count = 1
target_asset_plan_count = 6
duplicate_operation_count = 0
duplicate_alias_target_pair_count = 0
target_conflict_count = 0
already_official_overlap_count = 0
missing_target_asset_or_group_count = 0
missing_provenance_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
expected_affected_candidate_count = 45
expected_trusted_gain = 45
expected_review_reduction = 45
expected_out_of_scope_or_rejected_gain = 0
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_FOR_HUMAN_APPROVAL
```

Target asset diff preview:

```text
target_asset_file = data/overrides/semantic_alias_candidates.json
target_asset_group = profitability
before profitability count = 3
after preview profitability count = 9
operation = ADD_ALIAS
operation_count = 6
example = EBIT -> EBIT
```

No official assets were modified in 325L:

```text
official_asset_hash_unchanged = true
files_written_to_official_assets = []
```

325M is the next stage:

> Prepare a human approval package for the 6 dry-run alias patch operations, and support reviewed validation of the filled approval workbook.

325M must not apply official patches. It only creates and validates an approval package.

## Goal

Implement 325M: controlled alias proposal human approval workflow.

Prepare mode should create a human approval workbook/package for the 6 dry-run `ADD_ALIAS` patch operations produced by 325L.

Validate-reviewed mode should read the filled approval workbook and produce a final approved alias patch plan for 325N official patch application.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use cached 325L/325K/325J/325I evidence only.
- Process only the 6 dry-run alias patch operations from 325L.
- Do not apply official patches in 325M.
- Do not write `data/overrides/semantic_alias_candidates.json`.
- Do not write `data/mapping/formal_scope_rules.json`.
- Do not run post-patch regression in 325M.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325M source/report/runner files.

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
D:\_datefac\output\controlled_official_proposal_dry_run_325l
```

Expected files may include:

```text
controlled_official_proposal_dry_run_325l_summary.json
controlled_official_proposal_dry_run_325l_qa.json
controlled_official_proposal_dry_run_325l_patch_operations.json
controlled_official_proposal_dry_run_325l_target_asset_diff_preview.json
controlled_official_proposal_dry_run_325l_rollback_plan.json
controlled_official_proposal_dry_run_325l_no_apply_proof.json
```

Reference inputs:

```text
D:\_datefac\output\controlled_official_proposal_from_325j_325k
D:\_datefac\output\alias_official_rule_candidates_from_325i_325j
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
```

Official assets may be read only for context and hash checks:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/controlled_alias_proposal_human_approval_325m.py
datefac/semantic/controlled_alias_proposal_human_approval_325m_report.py
tools/run_controlled_alias_proposal_human_approval_325m.py
```

## Output directories

Prepare mode:

```text
D:\_datefac\output\controlled_alias_proposal_human_approval_325m
```

Reviewed mode:

```text
D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed
```

Suggested prepare outputs:

```text
controlled_alias_proposal_human_approval_325m_summary.json
controlled_alias_proposal_human_approval_325m_qa.json
controlled_alias_proposal_human_approval_325m_workbook.xlsx
controlled_alias_proposal_human_approval_325m_package.json
controlled_alias_proposal_human_approval_325m_review_notes.md
controlled_alias_proposal_human_approval_325m_no_apply_proof.json
```

Suggested reviewed outputs:

```text
controlled_alias_proposal_human_approval_325m_reviewed_summary.json
controlled_alias_proposal_human_approval_325m_reviewed_qa.json
controlled_alias_proposal_human_approval_325m_final_approved_patch_plan.json
controlled_alias_proposal_human_approval_325m_reviewed_workbook.xlsx
controlled_alias_proposal_human_approval_325m_rejected_or_needs_more_info.xlsx
controlled_alias_proposal_human_approval_325m_no_apply_proof.json
```

## Prepare mode required behavior

1. Validate 325L readiness:

```text
decision = CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_FOR_HUMAN_APPROVAL
qa_fail_count = 0
proposal_count = 6
patch_operation_count = 6
alias_patch_operation_count = 6
scope_patch_operation_count = 0
target_asset_file_count = 1
target_asset_plan_count = 6
duplicate_operation_count = 0
duplicate_alias_target_pair_count = 0
target_conflict_count = 0
already_official_overlap_count = 0
missing_target_asset_or_group_count = 0
missing_provenance_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
official_asset_hash_unchanged = true
files_written_to_official_assets = []
```

2. Load exactly 6 dry-run alias patch operations.
3. Generate exactly 6 approval records.
4. Default decision:

```text
PENDING_HUMAN_APPROVAL
```

5. Allowed approval decisions:

```text
APPROVE
REJECT
NEEDS_MORE_INFO
```

6. Each approval record must include:

```text
approval_record_id
patch_operation_id
proposal_id
candidate_id
operation
alias_label
normalized_alias_label
target_metric
target_asset_file
target_asset_group
expected_affected_candidate_count
expected_trusted_gain
expected_review_reduction
expected_out_of_scope_or_rejected_gain
safety_checks
semantic_constraint_summary
dry_run_diff_preview
rollback_reference
provenance
human_approval_decision
reviewer_name
reviewer_note
review_timestamp
```

7. Explicitly warn that approval enables only 325N official patch application, not direct production trusted marking.
8. Confirm official assets are not modified.
9. Generate QA and no-apply proof.

## Validate-reviewed mode required behavior

1. Read the reviewed approval workbook.
2. Validate exactly 6 approval records.
3. Require every reviewed record to have one allowed decision.
4. Require no pending decisions.
5. If decision is `APPROVE`, include the patch operation in the final approved patch plan for 325N.
6. If `REJECT` or `NEEDS_MORE_INFO`, exclude it from 325N and preserve it in rejected/needs-more-info output.
7. Do not apply official patches.
8. Do not write official assets.
9. Confirm official assets are not modified.

## Expected prepare result

```text
approval_record_count = 6
alias_approval_count = 6
scope_approval_count = 0
pending_count = 6
approved_patch_operation_count = 0
rejected_count = 0
needs_more_info_count = 0
qa_fail_count = 0
decision = CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_READY_FOR_HUMAN_REVIEW
```

## Expected reviewed result if all six are approved

```text
approval_record_count = 6
approved_patch_operation_count = 6
alias_approved_patch_operation_count = 6
scope_approved_patch_operation_count = 0
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_READY_FOR_325N_OFFICIAL_PATCH_APPLICATION
```

If at least one operation is approved and QA passes:

```text
CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_READY_FOR_325N_OFFICIAL_PATCH_APPLICATION
```

If no operation is approved:

```text
CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_NO_APPROVED_PATCH_OPERATIONS
```

If pending/invalid decisions remain:

```text
CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_NOT_READY
```

## Suggested commands

Prepare mode:

```bash
python tools/run_controlled_alias_proposal_human_approval_325m.py \
  --mode prepare \
  --dry-run-dir D:\_datefac\output\controlled_official_proposal_dry_run_325l \
  --output-dir D:\_datefac\output\controlled_alias_proposal_human_approval_325m
```

Validate-reviewed mode:

```bash
python tools/run_controlled_alias_proposal_human_approval_325m.py \
  --mode validate-reviewed \
  --dry-run-dir D:\_datefac\output\controlled_official_proposal_dry_run_325l \
  --reviewed-workbook D:\_datefac\output\controlled_alias_proposal_human_approval_325m\controlled_alias_proposal_human_approval_325m_workbook.xlsx \
  --output-dir D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\controlled_alias_proposal_human_approval_325m.py datefac\semantic\controlled_alias_proposal_human_approval_325m_report.py tools\run_controlled_alias_proposal_human_approval_325m.py
```

Then run prepare mode at minimum.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/controlled_alias_proposal_human_approval_325m.py
git add datefac/semantic/controlled_alias_proposal_human_approval_325m_report.py
git add tools/run_controlled_alias_proposal_human_approval_325m.py
```

Suggested commit message:

```text
Add 325M controlled alias proposal human approval
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Mode used.
5. Approval record count.
6. Alias / scope approval counts.
7. Pending / approved / rejected / needs-more-info counts.
8. Top approval examples.
9. Whether validate-reviewed mode was implemented.
10. Official asset modification confirmation.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
