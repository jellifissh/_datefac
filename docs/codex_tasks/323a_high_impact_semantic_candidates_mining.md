# DateFac 323A Task
## High-Impact Semantic Candidates Mining

## 1. Stage context

DateFac has completed the full 322 official semantic patch cycle.

Closed cycle:

```text
322F semantic adjudicator apply30
322G human-confirmed semantic mapping proposals
322H human-confirmed patch preview
322I official rule candidates
322J sandbox application
322K controlled official patch proposal
322L official patch dry run
322M human approval package
322M-R validate-reviewed hardening
322M reviewed validation
322N official semantic patch application
322O post-patch regression validation
```

322O commit:

```text
06a914d686a8beaaaa8e462213b03e0df2838658
```

322O result:

```text
official_rule_visibility_total = 10
alias_rules_visible = 3
scope_rules_visible = 7
trusted_total_before_322o = 2479
trusted_total_after_322o = 2528
review_required_total_before_322o = 3358
review_required_total_after_322o = 3071
rejected_total_before_322o = 135
rejected_total_after_322o = 373
trusted_gain_322o = 49
review_reduction_322o = 287
out_of_scope_or_rejected_gain_322o = 238
affected_candidate_count = 287
selected_core_trusted_rate_before_322o = 0.415104
selected_core_trusted_rate_after_322o = 0.423309
remaining_unknown_metric_candidate_count = 2897
remaining_unit_unknown_candidate_count = 491
remaining_manual_review_count = 3071
core_false_exclusion_count = 0
duplicate_count = 0
conflict_count = 0
qa_fail_count = 0
decision = POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE
```

The 322 cycle is closed. 323A starts the next improvement cycle.

## 2. Goal

Implement 323A: high-impact semantic candidates mining.

The goal is to mine the remaining unresolved / review-required candidates and identify the next high-impact batch of semantic rule opportunities.

323A should not generate official rules, should not call LLMs by default, and should not modify official semantic assets.

323A should produce a ranked candidate mining package for the next semantic adjudication / human review cycle.

The focus is business value:

- reduce manual review count;
- increase trusted core metrics safely;
- remove out-of-scope noise;
- identify high-frequency aliases;
- avoid unit-risky or ambiguous candidates unless explicitly separated for later unit work.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply new semantic rules.
4. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
5. Do not call LLM / semantic adjudicator unless explicitly requested in a later task.
6. Use cached candidate / trust split / delivery outputs.
7. Do not modify `E:\mineru_lab`.
8. Do not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
9. Do not use `git add -A` or `git add .`.
10. Only precisely add 323A source / report / runner files.

Known pre-existing dirty files that must remain untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

## 4. Inputs

Primary regression baseline:

```text
D:\_datefac\output\post_patch_regression_validation_322o
```

Official assets after 322N / 322O:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Cached candidate / trust split input:

```text
D:\_datefac\output\router_mineru_trust_split_322b2
```

Useful upstream references:

```text
D:\_datefac\output\official_semantic_rule_candidates_322j
D:\_datefac\output\official_semantic_patch_application_322n
D:\_datefac\output\post_patch_regression_validation_322o
```

Use existing project conventions to locate candidate rows, delivery previews, trust split data, and review_required rows.

## 5. Suggested new files

Follow project style. Suggested names:

```text
datefac/semantic/high_impact_semantic_candidates_mining.py
datefac/semantic/high_impact_semantic_candidates_report.py
tools/run_high_impact_semantic_candidates_mining_323a.py
```

Only add extra helpers if clearly justified.

## 6. Output directory

323A should write output artifacts to:

```text
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
```

Suggested outputs:

```text
high_impact_semantic_candidates_mining_323a_summary.json
high_impact_semantic_candidates_mining_323a_ranked_groups.xlsx
high_impact_semantic_candidates_mining_323a_top_alias_opportunities.xlsx
high_impact_semantic_candidates_mining_323a_top_scope_noise_opportunities.xlsx
high_impact_semantic_candidates_mining_323a_risk_buckets.xlsx
high_impact_semantic_candidates_mining_323a_sampling_plan.json
high_impact_semantic_candidates_mining_323a_qa.json
high_impact_semantic_candidates_mining_323a_notes.md
```

Do not commit output artifacts.

## 7. Candidate mining categories

323A should mine and rank at least these categories:

### 7.1 Alias opportunities

Potential metric alias rules where unresolved labels likely map to existing selected core metrics.

Rank by:

- affected candidate count;
- repeated label / normalized text frequency;
- proximity to known core metric names;
- low unit ambiguity;
- low scope ambiguity;
- expected trusted gain potential.

### 7.2 Scope / out-of-scope noise opportunities

Potential scope exclusions where repeated labels or groups are likely not selected core metrics.

Rank by:

- affected review_required count;
- strong evidence of non-core status;
- no selected core false exclusion risk;
- expected review reduction potential.

### 7.3 Ambiguous / risky candidates

Candidates should be isolated rather than promoted when they show:

- unit ambiguity;
- possible core metric overlap;
- conflicting labels;
- mixed metric groups;
- low support count;
- possible parser noise.

### 7.4 Unit-related candidates

Unit-related candidates should be counted and bucketed, but not solved in 323A unless clearly safe.

The dedicated unit cycle should be later, likely 323B.

## 8. Required behavior

### Step 1: Validate 322O closed state

Load 322O summary and QA.

Require:

```text
decision = POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE
qa_fail_count = 0
official_rule_visibility_total = 10
trusted_gain_322o = 49
review_reduction_322o = 287
core_false_exclusion_count = 0
duplicate_count = 0
conflict_count = 0
```

If this fails, stop and do not mine new candidates.

### Step 2: Load cached unresolved / review-required candidate data

Use cached outputs, not parser runs.

Load enough fields to group candidates by:

- candidate id;
- source file / report id;
- row text or label;
- normalized label if available;
- current metric status;
- current unit status;
- current trust status;
- selected core / non-core indicators;
- provenance / parser source;
- any existing reason / risk flags.

### Step 3: Exclude already official patched rules

323A must not rediscover the 10 rules closed in 322O as new candidates.

Use 322N / 322O applied operation ids, source rule ids, labels, and target groups to filter or mark them as already official.

### Step 4: Build grouped opportunity table

Group unresolved / review-required rows by stable features, for example:

- normalized label;
- row text signature;
- candidate metric label;
- parser source;
- unit signature;
- scope label;
- target metric hint if available.

Each group should include:

- group id;
- group type candidate: alias / scope_noise / unit_related / ambiguous;
- affected candidate count;
- affected review_required count;
- affected unknown_metric count;
- affected unit_unknown count;
- sample candidate ids;
- sample labels / row texts;
- risk flags;
- suggested next action.

### Step 5: Rank candidates

Rank by impact and safety.

Recommended scoring dimensions:

```text
impact_score = affected_review_required_count + affected_unknown_metric_count
safety_score = low ambiguity + no core false exclusion risk + no unit ambiguity
priority_score = impact_score * safety_score
```

The exact formula can be simple and deterministic. Avoid overengineering.

### Step 6: Generate top candidate package

Generate top candidate sets for the next stage:

- top alias opportunities;
- top scope noise opportunities;
- ambiguous holdout list;
- unit-related holdout list.

Recommended top counts:

```text
top_alias_opportunity_count <= 30
top_scope_noise_opportunity_count <= 30
ambiguous_holdout_count reported
unit_related_holdout_count reported
```

323A should not automatically send these to LLM. It only prepares mining results.

### Step 7: Sampling plan

Generate a sampling plan for human or semantic adjudicator review.

For each top opportunity, provide:

- group id;
- why it is high impact;
- why it may be safe or risky;
- sample rows to inspect;
- suggested review question;
- expected rule type if confirmed.

### Step 8: QA

QA must include:

- 322O closed state validation;
- cached input found;
- parser not run confirmation;
- official assets not modified confirmation;
- already-official 322 rules not rediscovered as new;
- grouped candidate count > 0 if unresolved candidates exist;
- alias opportunity count;
- scope noise opportunity count;
- unit holdout count;
- ambiguous holdout count;
- required output artifact presence;
- duplicate group id check;
- qa_fail_count.

### Step 9: Decision

If mining succeeds:

```text
HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP
```

If mining fails:

```text
HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_NOT_READY
```

Include blocking reasons.

## 9. Suggested command

```bash
python tools/run_high_impact_semantic_candidates_mining_323a.py \
  --post-patch-regression-dir D:\_datefac\output\post_patch_regression_validation_322o \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --patch-application-dir D:\_datefac\output\official_semantic_patch_application_322n \
  --output-dir D:\_datefac\output\high_impact_semantic_candidates_mining_323a
```

If safe defaults are implemented:

```bash
python tools/run_high_impact_semantic_candidates_mining_323a.py
```

## 10. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\high_impact_semantic_candidates_mining.py datefac\semantic\high_impact_semantic_candidates_report.py tools\run_high_impact_semantic_candidates_mining_323a.py
```

Then run the 323A runner.

## 11. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323A source files if needed. Example:

```bash
git add datefac/semantic/high_impact_semantic_candidates_mining.py
git add datefac/semantic/high_impact_semantic_candidates_report.py
git add tools/run_high_impact_semantic_candidates_mining_323a.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323A high-impact semantic candidates mining
```

Push to main only after successful checks and after confirming git status contains only intended 323A source files plus the known pre-existing dirty files.

## 12. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323A output directory.
4. Loaded unresolved / review-required candidate counts.
5. Grouped candidate counts.
6. Top alias opportunity count.
7. Top scope noise opportunity count.
8. Unit holdout count.
9. Ambiguous holdout count.
10. Highest-priority candidate examples.
11. qa_fail_count.
12. decision.
13. git status result.
14. commit hash.
15. push result.
