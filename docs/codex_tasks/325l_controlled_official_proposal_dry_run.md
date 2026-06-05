# DateFac 325L Task
## Controlled Official Proposal Dry Run for 325K Alias Proposals

## Context

325K controlled official proposal packaging is complete and pushed to remote main.

325K commit:

```text
34b7c40603760227cee345b59ef6dc69ac3483d6
```

325K output dir:

```text
D:\_datefac\output\controlled_official_proposal_from_325j_325k
```

325K result:

```text
loaded_ready_candidate_count = 6
proposal_count = 6
alias_proposal_count = 6
scope_proposal_count = 0
ready_for_dry_run_proposal_count = 6
needs_review_proposal_count = 0
rejected_proposal_count = 0
target_asset_plan_count = 6
target_asset_file_count = 1
duplicate_proposal_id_count = 0
already_official_overlap_count = 0
target_conflict_count = 0
missing_target_asset_or_group_count = 0
missing_provenance_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
expected_affected_candidate_count = 45
expected_trusted_gain = 45
expected_review_reduction = 45
expected_out_of_scope_or_rejected_gain = 0
official_assets_modified = false
qa_fail_count = 0
decision = CONTROLLED_OFFICIAL_PROPOSAL_FROM_325J_325K_READY_FOR_325L_DRY_RUN
```

Target asset plan:

```text
target_asset_file = data/overrides/semantic_alias_candidates.json
target_asset_group = profitability
operation = ADD_ALIAS
proposal_count = 6
```

325L is the next stage:

> Dry-run the 6 controlled alias proposals against the official alias asset without modifying the asset.

325L must generate patch operations, target asset diff preview, rollback plan, and no-apply proof. It must not write official assets.

## Goal

Implement 325L: controlled official proposal dry run for the 6 alias proposals from 325K.

The goal is to prove that the 6 alias proposals can be converted into deterministic patch operations targeting `data/overrides/semantic_alias_candidates.json::profitability`, while preserving rollback information and proving no official assets were modified.

325L must answer:

1. What exact patch operations would be applied later?
2. What would the target asset diff look like?
3. Are there duplicates, target conflicts, already-official overlaps, or missing target groups?
4. Are adjusted/diluted/ROE/EBIT semantic constraints still satisfied?
5. Can the patch be safely rolled back if applied later?

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use cached 325K/325J/325I evidence only.
- Process only the 6 `READY_FOR_DRY_RUN` alias proposals from 325K.
- Do not apply official patches in 325L.
- Do not write `data/overrides/semantic_alias_candidates.json`.
- Do not write `data/mapping/formal_scope_rules.json`.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325L source/report/runner files.

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
D:\_datefac\output\controlled_official_proposal_from_325j_325k
```

Expected files may include:

```text
controlled_official_proposal_from_325j_325k_summary.json
controlled_official_proposal_from_325j_325k_qa.json
controlled_official_proposal_from_325j_325k_proposals.json
controlled_official_proposal_from_325j_325k_target_asset_plan.json
controlled_official_proposal_from_325j_325k_no_apply_proof.json
```

Reference inputs:

```text
D:\_datefac\output\alias_official_rule_candidates_from_325i_325j
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
```

Official assets to read only:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/controlled_official_proposal_dry_run_325l.py
datefac/semantic/controlled_official_proposal_dry_run_325l_report.py
tools/run_controlled_official_proposal_dry_run_325l.py
```

## Output directory

```text
D:\_datefac\output\controlled_official_proposal_dry_run_325l
```

Suggested outputs:

```text
controlled_official_proposal_dry_run_325l_summary.json
controlled_official_proposal_dry_run_325l_qa.json
controlled_official_proposal_dry_run_325l_patch_operations.json
controlled_official_proposal_dry_run_325l_patch_operations.xlsx
controlled_official_proposal_dry_run_325l_target_asset_diff_preview.json
controlled_official_proposal_dry_run_325l_target_asset_diff_preview.xlsx
controlled_official_proposal_dry_run_325l_rollback_plan.json
controlled_official_proposal_dry_run_325l_rollback_plan.md
controlled_official_proposal_dry_run_325l_no_apply_proof.json
controlled_official_proposal_dry_run_325l_report.md
```

## Required behavior

1. Validate 325K readiness:

```text
decision = CONTROLLED_OFFICIAL_PROPOSAL_FROM_325J_325K_READY_FOR_325L_DRY_RUN
qa_fail_count = 0
proposal_count = 6
alias_proposal_count = 6
scope_proposal_count = 0
ready_for_dry_run_proposal_count = 6
needs_review_proposal_count = 0
rejected_proposal_count = 0
target_asset_plan_count = 6
target_asset_file_count = 1
duplicate_proposal_id_count = 0
already_official_overlap_count = 0
target_conflict_count = 0
missing_target_asset_or_group_count = 0
missing_provenance_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
official_assets_modified = false
```

2. Load exactly 6 ready alias proposals.
3. Convert each proposal into one patch operation:

```text
operation = ADD_ALIAS
target_asset_file = data/overrides/semantic_alias_candidates.json
target_asset_group = profitability
candidate_type = alias
```

4. Do not write the official alias asset.
5. Produce a diff preview showing the before/after logical alias entries that would be added.
6. Confirm the target asset and target group exist.
7. Check:

```text
duplicate_operation_count
duplicate_alias_target_pair_count
target_conflict_count
already_official_overlap_count
missing_target_asset_or_group_count
missing_provenance_count
adjusted_metric_mismatch_count
diluted_eps_mismatch_count
```

8. Re-check semantic constraints:

```text
EBIT -> EBIT only
ROE -> ROE only
每股收益(最新摊薄) -> diluted_EPS / EPS_diluted only
经调整 EPS -> adjusted_EPS only
经调整归母净利润 -> adjusted_attributable_net_profit / adjusted_parent_net_profit only
归母净利率 -> attributable_net_margin / parent_net_margin only
```

9. Generate rollback plan without applying it. Rollback plan should include sufficient details to remove exactly these proposed aliases if later applied.
10. Confirm official asset hash is unchanged before/after 325L.
11. Generate QA and no-apply proof.

## Expected summary metrics

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
official_asset_hash_unchanged = true
files_written_to_official_assets = []
expected_affected_candidate_count = 45
expected_trusted_gain = 45
expected_review_reduction = 45
expected_out_of_scope_or_rejected_gain = 0
qa_fail_count = 0
```

Expected decision:

```text
CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_FOR_HUMAN_APPROVAL
```

If QA passes with only non-blocking warnings:

```text
CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
CONTROLLED_OFFICIAL_PROPOSAL_DRY_RUN_325L_NOT_READY
```

## Suggested command

```bash
python tools/run_controlled_official_proposal_dry_run_325l.py \
  --controlled-proposal-dir D:\_datefac\output\controlled_official_proposal_from_325j_325k \
  --official-rule-candidate-dir D:\_datefac\output\alias_official_rule_candidates_from_325i_325j \
  --sandbox-replay-dir D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i \
  --output-dir D:\_datefac\output\controlled_official_proposal_dry_run_325l
```

If safe defaults are implemented:

```bash
python tools/run_controlled_official_proposal_dry_run_325l.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\controlled_official_proposal_dry_run_325l.py datefac\semantic\controlled_official_proposal_dry_run_325l_report.py tools\run_controlled_official_proposal_dry_run_325l.py
```

Then run the 325L runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/controlled_official_proposal_dry_run_325l.py
git add datefac/semantic/controlled_official_proposal_dry_run_325l_report.py
git add tools/run_controlled_official_proposal_dry_run_325l.py
```

Suggested commit message:

```text
Add 325L controlled alias proposal dry run
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Proposal and patch operation counts.
5. Target asset diff preview summary.
6. Duplicate / conflict / official overlap counts.
7. Adjusted / diluted mismatch counts.
8. Impact metrics carried forward.
9. Rollback plan path and summary.
10. No official asset modification confirmation.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
