# DateFac 325J Task
## Alias Official Rule Candidates from 325I Sandbox Replay

## Context

325I alias human-confirmed sandbox replay is complete and pushed to remote main.

325I commit:

```text
d3446dc99b816bbffe5eadce8d0e89c2333a9357
```

325I output dir:

```text
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
```

325I result:

```text
confirmed_alias_count = 6
sandbox_alias_rule_count = 6
affected_candidate_count = 45
trusted_gain_325i = 45
review_reduction_325i = 45
out_of_scope_or_rejected_gain_325i = 0
duplicate_count = 0
conflict_count = 0
target_conflict_count = 0
official_overlap_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
core_false_mapping_count = 0
official_assets_modified = false
qa_fail_count = 0
decision = ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_READY_FOR_325J_OFFICIAL_RULE_CANDIDATES
```

325J is the next stage:

> Convert the 6 sandbox-validated alias rules into official rule candidates for a controlled proposal stage.

325J must not modify official assets. It only packages candidates and carries forward provenance, sandbox impact, and safety checks.

## Goal

Implement 325J: alias official rule candidate packaging from 325I sandbox replay.

The goal is to produce a deterministic candidate package for the 6 alias rules that passed 325I sandbox replay. These candidates are not official rules yet.

325J must answer:

1. Which sandbox alias rules are eligible for official candidate status?
2. Are there duplicate candidates or conflicting targets?
3. Are any aliases already official after 322/323/324 patches?
4. Are adjusted/diluted/ROE/EBIT semantic constraints still satisfied?
5. What impact metrics should be carried forward into 325K controlled proposal?

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use cached 325I/325H/325G/325E evidence only.
- Process only the 6 sandbox alias rules from 325I.
- Do not create controlled official proposals in 325J.
- Do not run dry run in 325J.
- Do not apply official patches in 325J.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325J source/report/runner files.

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
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
```

Expected files may include:

```text
alias_human_confirmed_sandbox_replay_325i_summary.json
alias_human_confirmed_sandbox_replay_325i_qa.json
alias_human_confirmed_sandbox_replay_325i_sandbox_rules.json
alias_human_confirmed_sandbox_replay_325i_affected_candidates.xlsx
alias_human_confirmed_sandbox_replay_325i_no_apply_proof.json
```

Reference inputs:

```text
D:\_datefac\output\alias_human_confirmation_325h_reviewed
D:\_datefac\output\alias_response_schema_validation_325g
D:\_datefac\output\alias_safe_adjudicator_request_325e
```

Official assets may be read only for overlap/conflict checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/alias_official_rule_candidates_from_325i.py
datefac/semantic/alias_official_rule_candidates_from_325i_report.py
tools/run_alias_official_rule_candidates_from_325i_325j.py
```

## Output directory

```text
D:\_datefac\output\alias_official_rule_candidates_from_325i_325j
```

Suggested outputs:

```text
alias_official_rule_candidates_from_325i_325j_summary.json
alias_official_rule_candidates_from_325i_325j_qa.json
alias_official_rule_candidates_from_325i_325j_candidates.json
alias_official_rule_candidates_from_325i_325j_candidates.xlsx
alias_official_rule_candidates_from_325i_325j_duplicate_conflict_report.xlsx
alias_official_rule_candidates_from_325i_325j_no_apply_proof.json
alias_official_rule_candidates_from_325i_325j_report.md
```

## Required behavior

1. Validate 325I readiness:

```text
decision = ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_READY_FOR_325J_OFFICIAL_RULE_CANDIDATES
qa_fail_count = 0
confirmed_alias_count = 6
sandbox_alias_rule_count = 6
affected_candidate_count = 45
trusted_gain_325i = 45
review_reduction_325i = 45
out_of_scope_or_rejected_gain_325i = 0
duplicate_count = 0
conflict_count = 0
target_conflict_count = 0
official_overlap_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
core_false_mapping_count = 0
official_assets_modified = false
```

2. Load exactly 6 sandbox alias rules.
3. Convert each sandbox alias rule into one official rule candidate.
4. Candidate type must be:

```text
alias
```

5. Candidate status should be:

```text
READY_FOR_CONTROLLED_PROPOSAL
```

unless a blocking issue is detected.

6. Each candidate must include:

```text
candidate_id
source_sandbox_rule_id
alias_label
normalized_alias_label
target_metric
candidate_type
status
target_asset_file
target_asset_group
expected_affected_candidate_count
expected_trusted_gain
expected_review_reduction
expected_out_of_scope_or_rejected_gain
safety_checks
provenance
```

7. Target asset should resolve to:

```text
data/overrides/semantic_alias_candidates.json
```

Target group should be appropriate for alias candidates, likely:

```text
profitability
```

or another existing group if the target metric is already organized elsewhere. Do not create new official asset groups in 325J.

8. Check for duplicate candidate ids.
9. Check for duplicate alias label + target metric pairs within the candidate set.
10. Check official alias overlap.
11. Check target conflicts.
12. Check adjusted/diluted semantic constraints again:

```text
EBIT -> EBIT only
ROE -> ROE only
每股收益(最新摊薄) -> diluted_EPS / EPS_diluted only
经调整 EPS -> adjusted_EPS only
经调整归母净利润 -> adjusted_attributable_net_profit / adjusted_parent_net_profit only
归母净利率 -> attributable_net_margin / parent_net_margin only
```

13. Do not apply or write any official rule.
14. Confirm official assets are not modified.
15. Generate QA and no-apply proof.

## Expected summary metrics

```text
source_sandbox_rule_count = 6
candidate_count = 6
alias_candidate_count = 6
ready_for_controlled_proposal_count = 6
needs_review_candidate_count = 0
rejected_candidate_count = 0
duplicate_candidate_id_count = 0
duplicate_alias_target_pair_count = 0
official_overlap_count = 0
target_conflict_count = 0
adjusted_metric_mismatch_count = 0
diluted_eps_mismatch_count = 0
affected_candidate_count = 45
trusted_gain_325j = 45
review_reduction_325j = 45
out_of_scope_or_rejected_gain_325j = 0
qa_fail_count = 0
```

Expected decision if all candidates are ready:

```text
ALIAS_OFFICIAL_RULE_CANDIDATES_325J_READY_FOR_325K_CONTROLLED_PROPOSAL
```

If some candidates require review but at least one is ready:

```text
ALIAS_OFFICIAL_RULE_CANDIDATES_325J_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
ALIAS_OFFICIAL_RULE_CANDIDATES_325J_NOT_READY
```

## Suggested command

```bash
python tools/run_alias_official_rule_candidates_from_325i_325j.py \
  --sandbox-replay-dir D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i \
  --human-confirmation-reviewed-dir D:\_datefac\output\alias_human_confirmation_325h_reviewed \
  --schema-validation-dir D:\_datefac\output\alias_response_schema_validation_325g \
  --output-dir D:\_datefac\output\alias_official_rule_candidates_from_325i_325j
```

If safe defaults are implemented:

```bash
python tools/run_alias_official_rule_candidates_from_325i_325j.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\alias_official_rule_candidates_from_325i.py datefac\semantic\alias_official_rule_candidates_from_325i_report.py tools\run_alias_official_rule_candidates_from_325i_325j.py
```

Then run the 325J runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_official_rule_candidates_from_325i.py
git add datefac/semantic/alias_official_rule_candidates_from_325i_report.py
git add tools/run_alias_official_rule_candidates_from_325i_325j.py
```

Suggested commit message:

```text
Add 325J alias official rule candidates
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Source sandbox rule count.
5. Candidate counts by status.
6. Duplicate / conflict / official overlap counts.
7. Adjusted / diluted mismatch counts.
8. Impact metrics carried forward.
9. Official asset modification confirmation.
10. QA fail count.
11. Decision.
12. Git status result.
13. Commit hash.
14. Push result.
