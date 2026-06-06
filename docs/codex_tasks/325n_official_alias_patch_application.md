# DateFac 325N Task
## Official Alias Patch Application

## Context

325M controlled alias proposal human approval reviewed validation has passed.

325M reviewed output dir:

```text
D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed
```

325M reviewed result:

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
official_assets_modified = false
```

325L dry-run output dir:

```text
D:\_datefac\output\controlled_official_proposal_dry_run_325l
```

325L dry-run result:

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

325N is the next stage:

> Apply the 6 approved alias patch operations to the official semantic alias asset.

This is the first 325-stage step that is allowed to modify an official asset. It must be strict, idempotent, rollback-safe, and auditable.

## Goal

Implement 325N: official alias patch application.

The goal is to apply the 6 approved `ADD_ALIAS` operations to:

```text
data/overrides/semantic_alias_candidates.json::profitability
```

325N must:

1. Validate the approved patch plan from 325M reviewed output.
2. Validate consistency with the dry-run patch operations from 325L.
3. Create rollback backups before modifying official assets.
4. Apply only the 6 approved alias patch operations.
5. Be idempotent if rerun after successful application.
6. Prove no unintended official asset changed.
7. Produce apply proof, rollback plan, and QA artifacts.

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify `data/mapping/formal_scope_rules.json`.
- Only modify `data/overrides/semantic_alias_candidates.json` if all QA prechecks pass.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Do not run post-patch regression in 325N.
- Use cached 325M/325L/325K/325J/325I evidence only.
- Process only the 6 approved alias patch operations from 325M reviewed output.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325N source/report/runner files plus the intended official alias asset if it changed.

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

Primary approved plan:

```text
D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed
```

Expected files may include:

```text
controlled_alias_proposal_human_approval_325m_reviewed_summary.json
controlled_alias_proposal_human_approval_325m_reviewed_qa.json
controlled_alias_proposal_human_approval_325m_final_approved_patch_plan.json
```

Dry-run reference:

```text
D:\_datefac\output\controlled_official_proposal_dry_run_325l
```

Expected files may include:

```text
controlled_official_proposal_dry_run_325l_summary.json
controlled_official_proposal_dry_run_325l_qa.json
controlled_official_proposal_dry_run_325l_patch_operations.json
controlled_official_proposal_dry_run_325l_rollback_plan.json
controlled_official_proposal_dry_run_325l_no_apply_proof.json
```

Other references:

```text
D:\_datefac\output\controlled_official_proposal_from_325j_325k
D:\_datefac\output\alias_official_rule_candidates_from_325i_325j
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
```

Official asset to write:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Official asset that must remain unchanged:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Suggested files

```text
datefac/semantic/official_alias_patch_application_325n.py
datefac/semantic/official_alias_patch_application_325n_report.py
tools/run_official_alias_patch_application_325n.py
```

## Output directory

```text
D:\_datefac\output\official_alias_patch_application_325n
```

Suggested outputs:

```text
official_alias_patch_application_325n_summary.json
official_alias_patch_application_325n_qa.json
official_alias_patch_application_325n_applied_operations.json
official_alias_patch_application_325n_apply_proof.json
official_alias_patch_application_325n_before_snapshot.json
official_alias_patch_application_325n_after_snapshot.json
official_alias_patch_application_325n_rollback_plan.json
official_alias_patch_application_325n_rollback_instructions.md
official_alias_patch_application_325n_report.md
rollback_backups\semantic_alias_candidates.before_325n.json
```

## Required behavior

1. Validate 325M reviewed readiness:

```text
decision = CONTROLLED_ALIAS_PROPOSAL_HUMAN_APPROVAL_325M_REVIEWED_READY_FOR_325N_OFFICIAL_PATCH_APPLICATION
qa_fail_count = 0
approval_record_count = 6
approved_patch_operation_count = 6
alias_approved_patch_operation_count = 6
scope_approved_patch_operation_count = 0
rejected_count = 0
needs_more_info_count = 0
pending_count = 0
invalid_decision_count = 0
official_assets_modified = false
```

2. Validate 325L dry-run readiness:

```text
decision = CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_FOR_HUMAN_APPROVAL
qa_fail_count = 0
patch_operation_count = 6
alias_patch_operation_count = 6
scope_patch_operation_count = 0
target_asset_file_count = 1
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

3. Load exactly 6 approved alias patch operations.
4. Cross-check approved operations against 325L dry-run operations by patch operation id / proposal id / alias label / target metric.
5. Check target asset exists and target group exists:

```text
data/overrides/semantic_alias_candidates.json::profitability
```

6. Before writing, compute and record hashes for:

```text
data/overrides/semantic_alias_candidates.json
data/mapping/formal_scope_rules.json
```

7. Create rollback backup before writing:

```text
D:\_datefac\output\official_alias_patch_application_325n\rollback_backups\semantic_alias_candidates.before_325n.json
```

8. Apply the 6 approved `ADD_ALIAS` operations to the official alias asset.
9. If rerun after success, operations already present with identical target should be counted as idempotent, not failing.
10. Reject or fail if an alias already exists with conflicting target.
11. Re-check semantic constraints:

```text
EBIT -> EBIT only
ROE -> ROE only
每股收益(最新摊薄) -> diluted_EPS / EPS_diluted only
经调整 EPS -> adjusted_EPS only
经调整归母净利润 -> adjusted_attributable_net_profit / adjusted_parent_net_profit only
归母净利率 -> attributable_net_margin / parent_net_margin only
```

12. After writing, compute and record hashes again.
13. Confirm:

```text
semantic_alias_candidates.json hash changed only if new operations were applied
formal_scope_rules.json hash unchanged
```

14. Count historical duplicate alias/target state before and after and require delta = 0 unless the exact 325N operations intentionally add unique aliases.
15. Generate rollback plan sufficient to restore the before backup or remove exactly the 325N-added entries.
16. Generate QA, apply proof, and report.

## Expected first-run summary metrics

If the 6 operations are not already present before running:

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
formal_scope_rules_hash_unchanged = true
semantic_alias_candidates_hash_changed = true
affected_candidate_count = 45
expected_trusted_gain = 45
expected_review_reduction = 45
expected_out_of_scope_or_rejected_gain = 0
qa_fail_count = 0
decision = OFFICIAL_ALIAS_PATCH_APPLICATION_325N_READY_FOR_325O_POST_PATCH_REGRESSION
```

If rerun after successful application:

```text
approved_patch_operation_count = 6
applied_operation_count = 0
idempotent_operation_count = 6
applied_or_idempotent_operation_count = 6
qa_fail_count = 0
decision = OFFICIAL_ALIAS_PATCH_APPLICATION_325N_READY_FOR_325O_POST_PATCH_REGRESSION
```

If blocking QA fails:

```text
OFFICIAL_ALIAS_PATCH_APPLICATION_325N_NOT_READY
```

## Suggested command

```bash
python tools/run_official_alias_patch_application_325n.py \
  --reviewed-approval-dir D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed \
  --dry-run-dir D:\_datefac\output\controlled_official_proposal_dry_run_325l \
  --output-dir D:\_datefac\output\official_alias_patch_application_325n
```

If safe defaults are implemented:

```bash
python tools/run_official_alias_patch_application_325n.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\official_alias_patch_application_325n.py datefac\semantic\official_alias_patch_application_325n_report.py tools\run_official_alias_patch_application_325n.py
```

Then run the 325N runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/official_alias_patch_application_325n.py
git add datefac/semantic/official_alias_patch_application_325n_report.py
git add tools/run_official_alias_patch_application_325n.py
git add data/overrides/semantic_alias_candidates.json
```

Do not add `data/mapping/formal_scope_rules.json` unless it unexpectedly changed; if it changed, treat as blocking and investigate before commit.

Suggested commit message:

```text
Apply 325N official alias patch
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Approved patch operation counts.
5. Applied / idempotent / conflict counts.
6. Target official asset modified confirmation.
7. Official assets unchanged confirmation for formal scope rules.
8. Hash before/after summary.
9. Duplicate delta counts.
10. Impact metrics carried forward.
11. Rollback artifact paths and summary.
12. QA fail count.
13. Decision.
14. Git status result.
15. Commit hash.
16. Push result.
17. Verification result, sample scope, and residual risks.
