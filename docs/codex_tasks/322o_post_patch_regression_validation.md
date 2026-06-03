# DateFac 322O Task
## Post-Patch Regression Validation

## 1. Stage context

DateFac has completed 322N official semantic patch application and pushed it to `main`.

322N commit:

```text
35e4c62f9890c2f7a67227a01a024a1419c4976e
```

322N modified files:

```text
datefac/semantic/official_patch_application.py
datefac/semantic/official_patch_application_report.py
tools/run_official_semantic_patch_application_322n.py
data/mapping/formal_scope_rules.json
data/overrides/semantic_alias_candidates.json
```

Official assets modified:

```text
data/mapping/formal_scope_rules.json
data/overrides/semantic_alias_candidates.json
```

322N output dir:

```text
D:\_datefac\output\official_semantic_patch_application_322n
```

322N result:

```text
approved_patch_count = 10
applied_or_idempotent_operation_count = 10
alias_operation_count = 3
scope_operation_count = 7
conflict_count = 0
expected_affected_candidate_count = 287
expected_trusted_gain = 49
expected_review_reduction = 287
expected_out_of_scope_or_rejected_gain = 238
affected_candidate_count = 287
trusted_gain_delta_vs_322i_expected = 0
review_reduction_delta_vs_322i_expected = 0
out_of_scope_or_rejected_gain_delta_vs_322i_expected = 0
affected_candidate_count_delta_vs_322i_expected = 0
qa_fail_count = 0
decision = OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_READY_FOR_322O_POST_PATCH_REGRESSION
```

322N rollback artifacts:

```text
D:\_datefac\output\official_semantic_patch_application_322n\official_semantic_patch_application_322n_rollback_plan.json
D:\_datefac\output\official_semantic_patch_application_322n\official_semantic_patch_application_322n_rollback_instructions.md
D:\_datefac\output\official_semantic_patch_application_322n\rollback_backups\formal_scope_rules.before_322n.json
D:\_datefac\output\official_semantic_patch_application_322n\rollback_backups\semantic_alias_candidates.before_322n.json
```

322O is the next step:

> Post-Patch Regression Validation

322O must prove that the official semantic patch applied in 322N produces the expected system-level behavior and did not introduce regression.

## 2. Goal

Implement 322O: post-patch regression validation.

322O should run a cached-input regression validation using the now-official semantic rule assets and compare the result against 322N / 322I / 322J expected impact.

322O must answer:

1. Did the official assets load successfully?
2. Are the 10 official patch rules visible through the official rule loading path?
3. Does the officially patched system produce the expected trusted gain and review reduction?
4. Did selected core trusted rate improve or at least not regress?
5. Were any core metrics falsely excluded?
6. Were any unit_unknown / unknown_metric / manual_review counts made worse unexpectedly?
7. Are rollback artifacts sufficient if regression appears?
8. Is DateFac ready to mark this official patch closed and move to the next semantic improvement cycle?

## 3. Critical boundary

322O is validation only.

322O must not:

- modify official mapping / override assets;
- modify production pipeline code;
- apply new semantic rules;
- run MinerU / StructEqTable / Docling / PPStructure / VLM;
- commit output artifacts;
- touch `E:\mineru_lab`;
- touch historical dirty files.

322O may read existing cached outputs from previous trusted split / sandbox / delivery stages. It should not regenerate parser outputs.

## 4. Hard constraints

1. Validate 322N readiness before regression.
2. Use official semantic assets after 322N.
3. Do not apply any new rule.
4. Do not modify official semantic assets.
5. Do not run PDF parser / OCR / VLM tools.
6. Use cached candidate / trust split / delivery outputs where possible.
7. Compare official post-patch behavior against 322N expected impact.
8. Detect core metric false exclusion.
9. Detect trusted regression.
10. Detect unexplained count deltas.
11. Generate QA and decision.
12. Do not use `git add -A` or `git add .`.
13. Only precisely add 322O source files if implementation is needed.

Known pre-existing dirty files that must remain untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_outputs_320g.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

Note: if the actual dirty file is `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`, leave it untouched as well.

## 5. Inputs

Primary 322N input:

```text
D:\_datefac\output\official_semantic_patch_application_322n
```

Official assets after 322N:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Regression reference outputs:

```text
D:\_datefac\output\official_semantic_rule_candidates_322i
D:\_datefac\output\official_semantic_rule_candidates_322j
D:\_datefac\output\controlled_official_semantic_patch_proposal_322k
D:\_datefac\output\official_semantic_patch_dry_run_322l
D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed
```

Cached candidate / trust split input previously used:

```text
D:\_datefac\output\router_mineru_trust_split_322b2
```

Use existing project conventions to locate the correct cached candidate data. Do not run parsers.

## 6. Suggested new files

Follow existing project style. Suggested names:

```text
datefac/semantic/post_patch_regression_validation.py
datefac/semantic/post_patch_regression_validation_report.py
tools/run_post_patch_regression_validation_322o.py
```

Only add extra helper files if clearly justified.

## 7. Output directory

322O should write output artifacts to:

```text
D:\_datefac\output\post_patch_regression_validation_322o
```

Suggested outputs:

```text
post_patch_regression_validation_322o_summary.json
post_patch_regression_validation_322o_qa.json
post_patch_regression_validation_322o_before_after_comparison.xlsx
post_patch_regression_validation_322o_official_rule_visibility.json
post_patch_regression_validation_322o_core_false_exclusion_check.xlsx
post_patch_regression_validation_322o_regression_notes.md
post_patch_regression_validation_322o_decision.md
```

Do not commit output artifacts.

## 8. Required behavior

### Step 1: Validate 322N readiness

Load 322N summary and QA.

Require:

```text
decision = OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_READY_FOR_322O_POST_PATCH_REGRESSION
qa_fail_count = 0
approved_patch_count = 10
applied_or_idempotent_operation_count = 10
alias_operation_count = 3
scope_operation_count = 7
conflict_count = 0
```

If this fails, stop and do not continue.

### Step 2: Validate official assets exist and load

Validate:

- `formal_scope_rules.json` exists and is valid JSON;
- `semantic_alias_candidates.json` exists and is valid JSON;
- official rule loaders can see these assets if loader functions exist;
- no malformed rule entry exists in the newly patched areas.

### Step 3: Validate official rule visibility

Verify that the 10 applied / idempotent operations from 322N are visible in official assets:

```text
alias rules visible = 3
scope rules visible = 7
total visible = 10
```

If any rule is missing, fail.

### Step 4: Run cached-input official regression

Using cached candidate / trust split outputs, rerun the semantic rule application / trust classification stage with the now-official assets.

Do not run parsers.

Expected post-patch behavior should align with:

```text
trusted_gain = 49
review_reduction = 287
out_of_scope_or_rejected_gain = 238
affected_candidate_count = 287
```

If the project has an existing official rule application path, use it. Avoid building a parallel fake evaluator unless no official path exists.

### Step 5: Compare against baseline

Compare official post-patch result against baseline from 322J / 322N:

Expected:

```text
trusted_total_before = 2479
trusted_total_after = 2528
review_required_total_before = 3358
review_required_total_after = 3071
rejected_total_before = 135
rejected_total_after = 373
selected_core_trusted_rate_before = 0.415104
selected_core_trusted_rate_after = 0.423309
remaining_unknown_metric_candidate_count = 2897
remaining_unit_unknown_candidate_count = 491
remaining_manual_review_count = 3071
```

Allow exact match if using identical cached data. If differences exist, require explanations and classify as warning or fail depending on severity.

### Step 6: Core false exclusion check

Validate that out_of_scope official rules did not exclude selected core metrics.

Fail if:

- selected core metric candidate was moved to rejected / out_of_scope unexpectedly;
- selected core trusted rate decreases;
- any trusted selected core row becomes review_required / rejected without explanation.

### Step 7: Regression safety checks

Check:

- no trusted regression;
- no manual_review increase;
- no unknown_metric unexpected increase;
- no unit_unknown unexpected increase;
- no duplicate official rule introduced;
- no conflict between alias and scope rules;
- rollback artifacts from 322N exist and are readable.

### Step 8: QA

QA must include:

- 322N readiness pass;
- official asset load pass;
- official rule visibility pass;
- cached regression run pass;
- expected impact alignment pass;
- selected core trusted rate non-regression pass;
- core false exclusion pass;
- unknown metric / unit unknown non-regression pass;
- duplicate rule check;
- conflict rule check;
- rollback artifact presence check;
- no parser run confirmation;
- no official asset modification confirmation;
- qa_fail_count.

### Step 9: Decision

If all checks pass:

```text
POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE
```

If any blocking issue exists:

```text
POST_PATCH_REGRESSION_VALIDATION_322O_NOT_READY_ROLLBACK_REVIEW_REQUIRED
```

If not ready, include rollback recommendation and blocking reasons.

## 9. Suggested command

```bash
python tools/run_post_patch_regression_validation_322o.py \
  --patch-application-dir D:\_datefac\output\official_semantic_patch_application_322n \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --reference-322j-dir D:\_datefac\output\official_semantic_rule_candidates_322j \
  --output-dir D:\_datefac\output\post_patch_regression_validation_322o
```

If safe defaults are implemented:

```bash
python tools/run_post_patch_regression_validation_322o.py
```

## 10. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\post_patch_regression_validation.py datefac\semantic\post_patch_regression_validation_report.py tools\run_post_patch_regression_validation_322o.py
```

Then run the 322O runner.

## 11. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 322O source files if needed. Example:

```bash
git add datefac/semantic/post_patch_regression_validation.py
git add datefac/semantic/post_patch_regression_validation_report.py
git add tools/run_post_patch_regression_validation_322o.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 322O post-patch regression validation
```

Push to main only after successful checks and after confirming git status contains only intended 322O source files plus the known pre-existing dirty files.

## 12. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 322O output directory.
4. Official rule visibility counts.
5. Regression comparison metrics.
6. Core false exclusion check result.
7. Duplicate / conflict counts.
8. Rollback artifact check result.
9. qa_fail_count.
10. decision.
11. git status result.
12. commit hash.
13. push result.
