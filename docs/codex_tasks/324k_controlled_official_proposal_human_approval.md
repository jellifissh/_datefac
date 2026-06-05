# DateFac 324K Task
## Human Approval Package for 324J Controlled Official Proposal Dry Run

## Context

324J controlled official proposal dry run is complete and pushed to remote main.

324J commit:

```text
b5b4d3aa3a91c2ac7aa94d3d7f7c407a2ac47c24
```

324J output dir:

```text
D:\_datefac\output\controlled_official_proposal_dry_run_324j
```

324J result:

```text
proposal_count = 1
patch_operation_count = 1
scope_patch_operation_count = 1
alias_patch_operation_count = 0
duplicate_operation_count = 0
target_conflict_count = 0
already_official_overlap_count = 0
official_asset_hash_unchanged = true
files_written_to_official_assets = []
expected_affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
carried_warnings = historical_duplicates_unchanged_only:new_duplicate_delta_count=0
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_324J_READY_WITH_WARNINGS
```

324K is the next step:

> Generate a human approval workbook/package for the single dry-run patch operation from 324J.

324K must not modify official assets and must not apply rules.

## Goal

Implement 324K: human approval package for the single 324J dry-run patch operation.

Prepare mode should generate one approval record with default decision:

```text
PENDING_HUMAN_APPROVAL
```

Validate-reviewed mode, if implemented, should validate the filled approval workbook and produce a final approved patch operation plan only if the user approves it.

## Hard constraints

- Do not modify production pipeline.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use 324J dry-run output and cached evidence only.
- Process only the single 324J dry-run patch operation.
- Do not create official patch application in 324K.
- Do not modify official assets.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 324K source/report/runner files.

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
D:\_datefac\output\controlled_official_proposal_dry_run_324j
```

Expected files may include:

```text
controlled_official_proposal_dry_run_324j_summary.json
controlled_official_proposal_dry_run_324j_qa.json
controlled_official_proposal_dry_run_324j_patch_operations.json
controlled_official_proposal_dry_run_324j_target_asset_diff_preview.json
controlled_official_proposal_dry_run_324j_target_asset_diff_preview.xlsx
controlled_official_proposal_dry_run_324j_rollback_plan.json
controlled_official_proposal_dry_run_324j_rollback_plan.md
controlled_official_proposal_dry_run_324j_no_apply_proof.json
```

Reference inputs:

```text
D:\_datefac\output\controlled_official_proposal_from_324h_324i
D:\_datefac\output\official_rule_candidate_from_324g_324h
D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
```

Official assets may be read only for approval context:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/controlled_official_proposal_human_approval_324k.py
datefac/semantic/controlled_official_proposal_human_approval_324k_report.py
tools/run_controlled_official_proposal_human_approval_324k.py
```

## Output directories

Prepare mode:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_324k
```

Reviewed mode:

```text
D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed
```

Suggested prepare outputs:

```text
controlled_official_proposal_human_approval_324k_summary.json
controlled_official_proposal_human_approval_324k_qa.json
controlled_official_proposal_human_approval_324k_workbook.xlsx
controlled_official_proposal_human_approval_324k_package.json
controlled_official_proposal_human_approval_324k_review_notes.md
controlled_official_proposal_human_approval_324k_no_apply_proof.json
```

Suggested reviewed outputs:

```text
controlled_official_proposal_human_approval_324k_reviewed_summary.json
controlled_official_proposal_human_approval_324k_reviewed_qa.json
controlled_official_proposal_human_approval_324k_final_approved_patch_plan.json
controlled_official_proposal_human_approval_324k_reviewed_workbook.xlsx
controlled_official_proposal_human_approval_324k_rejected_or_needs_more_info.xlsx
controlled_official_proposal_human_approval_324k_no_apply_proof.json
```

## Prepare mode required behavior

1. Validate 324J readiness:

```text
decision = CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_324J_READY_WITH_WARNINGS
qa_fail_count = 0
proposal_count = 1
patch_operation_count = 1
scope_patch_operation_count = 1
alias_patch_operation_count = 0
duplicate_operation_count = 0
target_conflict_count = 0
already_official_overlap_count = 0
official_asset_hash_unchanged = true
files_written_to_official_assets = []
expected_affected_candidate_count = 42
expected_trusted_gain = 0
expected_review_reduction = 42
expected_out_of_scope_or_rejected_gain = 42
```

2. Load exactly one dry-run patch operation.
3. Generate exactly one human approval record.
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

6. Include patch operation id, proposal id, candidate id, operation type, target asset/group, proposed change, expected impact, provenance, dry-run evidence, rollback note, and warning notes.
7. Carry historical duplicate warning as non-blocking only if `new_duplicate_delta_count = 0`.
8. Confirm no official assets were modified.

## Validate-reviewed mode required behavior

1. Read reviewed approval workbook.
2. Validate exactly one approval record.
3. Require decision in the allowed set.
4. Require no pending decision.
5. If `APPROVE`, produce a final approved patch operation plan for 324L official patch application.
6. If `REJECT` or `NEEDS_MORE_INFO`, do not produce an official application plan.
7. Preserve reviewer notes and approval evidence.
8. Confirm official assets were not modified.

## Expected prepare result

```text
approval_record_count = 1
scope_approval_count = 1
alias_approval_count = 0
pending_count = 1
approved_patch_operation_count = 0
rejected_count = 0
needs_more_info_count = 0
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_READY_FOR_HUMAN_REVIEW
```

## Expected reviewed result if approved

```text
approval_record_count = 1
approved_patch_operation_count = 1
scope_approved_patch_operation_count = 1
alias_approved_patch_operation_count = 0
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_READY_FOR_324L_OFFICIAL_PATCH_APPLICATION
```

## Expected reviewed result if rejected

```text
approval_record_count = 1
approved_patch_operation_count = 0
rejected_count = 1
pending_count = 0
invalid_decision_count = 0
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_HUMAN_APPROVAL_324K_REVIEWED_REJECTED_NO_OFFICIAL_PATCH_APPLICATION
```

## Suggested commands

Prepare mode:

```bash
python tools/run_controlled_official_proposal_human_approval_324k.py \
  --mode prepare \
  --dry-run-dir D:\_datefac\output\controlled_official_proposal_dry_run_324j \
  --output-dir D:\_datefac\output\controlled_official_proposal_human_approval_324k
```

Validate-reviewed mode:

```bash
python tools/run_controlled_official_proposal_human_approval_324k.py \
  --mode validate-reviewed \
  --dry-run-dir D:\_datefac\output\controlled_official_proposal_dry_run_324j \
  --reviewed-workbook D:\_datefac\output\controlled_official_proposal_human_approval_324k\controlled_official_proposal_human_approval_324k_workbook.xlsx \
  --output-dir D:\_datefac\output\controlled_official_proposal_human_approval_324k_reviewed
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\controlled_official_proposal_human_approval_324k.py datefac\semantic\controlled_official_proposal_human_approval_324k_report.py tools\run_controlled_official_proposal_human_approval_324k.py
```

Then run prepare mode at minimum.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/controlled_official_proposal_human_approval_324k.py
git add datefac/semantic/controlled_official_proposal_human_approval_324k_report.py
git add tools/run_controlled_official_proposal_human_approval_324k.py
```

Suggested commit message:

```text
Add 324K controlled proposal human approval workflow
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Mode used.
5. Approval record count.
6. Scope / alias approval counts.
7. Pending / approved / rejected / needs-more-info counts.
8. qa_fail_count.
9. decision.
10. Whether validate-reviewed mode was implemented.
11. Whether official assets were modified.
12. git status result.
13. commit hash.
14. push result.
