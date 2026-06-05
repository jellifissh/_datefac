# DateFac 325A Task
## Alias Candidate Refinement and Safe High-Impact Batch Planning

## Context

The 324 official scope patch cycle is closed.

324N closure commit:

```text
aed364821a68082ac23c6ec0e7bc7b1647e21bcf
```

324N output dir:

```text
D:\_datefac\output\official_scope_patch_cycle_closure_324n
```

324N result:

```text
official_rule_count_324 = 1
scope_rule_count_324 = 1
alias_rule_count_324 = 0
trusted_gain_324 = 0
review_reduction_324 = 42
out_of_scope_or_rejected_gain_324 = 42
affected_candidate_count_324 = 42
cumulative_official_rule_count = 17
cumulative_trusted_gain = 93
cumulative_review_reduction = 458
warning_status = historical duplicates unchanged only
current_duplicate_count = 3
new_duplicate_delta_count_324 = 0
remaining_burden_status = inherited from 323P / pre-324, not recomputed
recommended_next_cycle_direction_primary = alias_candidates
recommended_next_cycle_direction_secondary = duplicate_cleanup_or_unit_holdout_diagnosis
qa_fail_count = 0
decision = OFFICIAL_SCOPE_PATCH_CYCLE_324N_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING
```

The next cycle should move away from scope-noise mining and back to alias candidates. Scope-noise refined inventory was mostly exhausted in 324A and produced only one official scope rule. Alias candidates have larger upside but higher risk, so 325A must be refinement/planning only.

325A must not call LLM/adjudicator and must not create official proposals. It should deterministically select safe, high-impact alias candidates for later sanity gate / human or adjudicator review.

## Goal

Implement 325A: alias candidate refinement and safe high-impact batch planning.

The goal is to take the alias review-ready inventory from prior mining/repair stages and produce a deterministic, evidence-rich, risk-bucketed alias refinement package for the next cycle.

325A should answer:

1. Which alias candidates remain after 322/323/324 official rules are excluded?
2. Which alias candidates have high expected review reduction or trusted gain potential?
3. Which alias candidates are safe enough to send to the next sanity gate?
4. Which alias candidates should be held out due to ambiguity, unit risk, generic labels, category mismatch, already-official overlap, or weak evidence?

## Hard constraints

- Do not modify production pipeline.
- Do not modify parser/extraction/delivery code.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM / semantic adjudicator.
- Use cached outputs only.
- Do not produce official rule candidates in 325A.
- Do not produce controlled official proposals in 325A.
- Do not produce sandbox replay packages in 325A.
- Do not commit output/, input/semantic_adjudicator_responses_*, temp/, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 325A source/report/runner files.

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

Primary prior-cycle inputs:

```text
D:\_datefac\output\remaining_burden_planning_323p
D:\_datefac\output\candidate_text_repair_323ar
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
D:\_datefac\output\semantic_adjudication_batch_prep_323ab
D:\_datefac\output\adjudication_batch_sanity_gate_323c
D:\_datefac\output\official_scope_patch_cycle_closure_324n
D:\_datefac\output\post_patch_regression_validation_324m
D:\_datefac\output\post_patch_regression_validation_323n
D:\_datefac\output\router_mineru_trust_split_322b2
```

Official assets may be read only for overlap/reference checks:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## Suggested files

```text
datefac/semantic/alias_candidate_refinement_325a.py
datefac/semantic/alias_candidate_refinement_325a_report.py
tools/run_alias_candidate_refinement_325a.py
```

## Output directory

```text
D:\_datefac\output\alias_candidate_refinement_325a
```

Suggested outputs:

```text
alias_candidate_refinement_325a_summary.json
alias_candidate_refinement_325a_qa.json
alias_candidate_refinement_325a_refined_alias_candidates.json
alias_candidate_refinement_325a_refined_alias_candidates.xlsx
alias_candidate_refinement_325a_safe_batch.xlsx
alias_candidate_refinement_325a_holdout_candidates.xlsx
alias_candidate_refinement_325a_already_official_overlap.xlsx
alias_candidate_refinement_325a_risk_bucket_summary.xlsx
alias_candidate_refinement_325a_notes.md
alias_candidate_refinement_325a_no_apply_proof.json
```

## Candidate sources

Prefer the most reliable alias inventory in this order:

1. 323A-R review-ready alias package:

```text
D:\_datefac\output\candidate_text_repair_323ar
```

Known prior count:

```text
review_ready_alias_count = 211
```

2. 323A high-impact semantic mining:

```text
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
```

Known prior counts:

```text
alias_opportunity_group_count = 233
top_alias_opportunity_count = 30
```

3. 323A-B and 323C can be used for prior routing exclusions:

```text
D:\_datefac\output\semantic_adjudication_batch_prep_323ab
D:\_datefac\output\adjudication_batch_sanity_gate_323c
```

Do not blindly reuse 323C holdouts as safe candidates.

## Required behavior

1. Validate 324N readiness:

```text
decision = OFFICIAL_SCOPE_PATCH_CYCLE_324N_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING
qa_fail_count = 0
recommended_next_cycle_direction_primary = alias_candidates
```

2. Load alias review-ready inventory from 323A-R / 323A.
3. Exclude candidates that are already official after 322/323/324 patches.
4. Exclude candidates already resolved by 322/323 official alias rules.
5. Exclude candidates with obvious category mismatch or scope-noise behavior.
6. Exclude candidates with unit-related ambiguity or unit-bearing labels unless they are explicit safe alias labels.
7. Exclude very generic labels that can map to multiple metrics without strong evidence, e.g. bare:

```text
流动资产
流动负债
资产
负债
权益
利润
收入
成本
费用
现金
```

These may be high-impact but should be marked as holdout unless evidence proves safe.

8. Exclude long narrative labels and policy/disclosure text.
9. Score remaining alias candidates by expected review impact, evidence strength, label specificity, official overlap risk, and ambiguity risk.
10. Produce a safe refined alias candidate batch for the next stage.
11. Keep batch small enough for human/adjudicator review. Recommended default:

```text
max_safe_batch_count = 15
```

12. Preserve provenance and sample evidence for every candidate.
13. Confirm official assets are not modified.
14. Generate QA and no-apply proof.

## Risk buckets

Every alias candidate should be assigned one bucket:

```text
SAFE_ALIAS_REVIEW_BATCH
HOLDOUT_ALREADY_OFFICIAL
HOLDOUT_CATEGORY_MISMATCH
HOLDOUT_SCOPE_NOISE_OR_DISCLOSURE_TEXT
HOLDOUT_UNIT_RELATED
HOLDOUT_GENERIC_AMBIGUOUS_LABEL
HOLDOUT_WEAK_EVIDENCE
HOLDOUT_DUPLICATE_OR_CONFLICT
HOLDOUT_NEEDS_MORE_INFO
```

## Suggested safe alias preference

Prefer candidates that are:

- specific and canonical;
- unlikely to be scope-noise;
- not unit-bearing;
- not generic balance-sheet headings;
- not already official;
- supported by multiple candidate examples or strong table evidence;
- likely to map to one stable core metric.

Examples that may be safer than generic headings, depending on evidence:

```text
EBITDA
归属母公司净利润
归母净利润
扣非归母净利润
经营活动现金流净额
基本每股收益
摊薄每股收益
毛利率
净利率
ROE
```

Do not hard-code acceptance. Use evidence and official-overlap checks.

## Expected summary metrics

Because source inventories may differ, do not hard-code counts except where used as prior references. Compute actual counts.

Expected fields:

```text
input_alias_inventory_count
excluded_already_official_count
excluded_category_mismatch_count
excluded_scope_noise_or_disclosure_text_count
excluded_unit_related_count
excluded_generic_ambiguous_label_count
excluded_weak_evidence_count
excluded_duplicate_or_conflict_count
safe_alias_review_batch_count
holdout_count
top_safe_alias_candidate_count
qa_fail_count
```

Expected decision if safe batch is produced:

```text
ALIAS_CANDIDATE_REFINEMENT_325A_READY_FOR_325B_ALIAS_REVIEW_BATCH
```

Expected decision if no safe candidates remain but QA passes:

```text
ALIAS_CANDIDATE_REFINEMENT_325A_NO_SAFE_BATCH_RECOMMEND_REMINING
```

If blocking checks fail:

```text
ALIAS_CANDIDATE_REFINEMENT_325A_NOT_READY
```

## Suggested command

```bash
python tools/run_alias_candidate_refinement_325a.py \
  --remaining-burden-dir D:\_datefac\output\remaining_burden_planning_323p \
  --candidate-text-repair-dir D:\_datefac\output\candidate_text_repair_323ar \
  --high-impact-mining-dir D:\_datefac\output\high_impact_semantic_candidates_mining_323a \
  --previous-batch-prep-dir D:\_datefac\output\semantic_adjudication_batch_prep_323ab \
  --previous-sanity-gate-dir D:\_datefac\output\adjudication_batch_sanity_gate_323c \
  --cycle-closure-dir D:\_datefac\output\official_scope_patch_cycle_closure_324n \
  --output-dir D:\_datefac\output\alias_candidate_refinement_325a
```

If safe defaults are implemented:

```bash
python tools/run_alias_candidate_refinement_325a.py
```

## Compile / run checks

```bash
python -m py_compile datefac\semantic\alias_candidate_refinement_325a.py datefac\semantic\alias_candidate_refinement_325a_report.py tools\run_alias_candidate_refinement_325a.py
```

Then run the 325A runner.

## Git workflow

Use precise adds only:

```bash
git add datefac/semantic/alias_candidate_refinement_325a.py
git add datefac/semantic/alias_candidate_refinement_325a_report.py
git add tools/run_alias_candidate_refinement_325a.py
```

Suggested commit message:

```text
Add 325A alias candidate refinement
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Input alias inventory count.
5. Exclusion counts by bucket.
6. Safe alias review batch count.
7. Holdout count.
8. Top safe alias examples.
9. Official asset modification confirmation.
10. QA fail count.
11. Decision.
12. Git status result.
13. Commit hash.
14. Push result.
