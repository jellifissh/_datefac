# DateFac 323C Task
## Adjudication Batch Sanity Gate and Human Spot-Check Package

## 1. Stage context

DateFac has completed 323A-B semantic adjudication batch preparation.

323A-B commit:

```text
b065f56484339d0b44931df5c2873b293a3ace22
```

323A-B changed files:

```text
datefac/semantic/semantic_adjudication_batch_prep.py
datefac/semantic/semantic_adjudication_batch_prep_report.py
tools/run_semantic_adjudication_batch_prep_323ab.py
```

323A-B output dir:

```text
D:\_datefac\output\semantic_adjudication_batch_prep_323ab
```

323A-B result:

```text
loaded_review_ready_alias_count = 211
loaded_review_ready_scope_count = 11
selected_alias_batch_count = 25
selected_scope_batch_count = 9
total_batch_count = 34
excluded_review_ready_count = 4
excluded_unit_holdout_count = 178
excluded_ambiguous_holdout_count = 122
excluded_unrepairable_holdout_count = 49
excluded_reason_counts = {"LONG_NARRATIVE_POLICY_TEXT": 4}
qa_fail_count = 0
decision = SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW
```

Highest-priority examples include:

```text
alias | 其中：服务 | priority_score=285.6 | affected_review_required_count=28
alias | 其中：设备 | priority_score=285.6 | affected_review_required_count=28
alias | 归属母公司股东权益 | priority_score=252.0 | affected_review_required_count=21
alias | 流动负债 | priority_score=252.0 | affected_review_required_count=21
alias | 流动资产 | priority_score=252.0 | affected_review_required_count=21
```

These examples are readable, but some may be questionable as alias candidates for selected core financial metrics. They may be balance-sheet line items, subline items, or scope/noise candidates rather than metric aliases. 323C must gate them before any LLM / semantic adjudicator call.

## 2. Goal

Implement 323C: adjudication batch sanity gate and human spot-check package.

The goal is to inspect the 323A-B batch deterministically and produce a safer review package that separates:

1. items safe to send to human/adjudicator review;
2. items requiring human spot-check before adjudicator;
3. items that should be held out due to category/type mismatch or high risk.

323C must not call LLMs, must not apply rules, and must not modify official semantic assets.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply semantic rules.
4. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
5. Do not call LLM / semantic adjudicator.
6. Use 323A-B outputs and cached candidate data only.
7. Do not modify `E:\mineru_lab`.
8. Do not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
9. Do not use `git add -A` or `git add .`.
10. Only precisely add 323C source/report/runner files.

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

Primary input:

```text
D:\_datefac\output\semantic_adjudication_batch_prep_323ab
```

Useful references:

```text
D:\_datefac\output\candidate_text_repair_323ar
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
D:\_datefac\output\official_semantic_patch_application_322n
D:\_datefac\output\post_patch_regression_validation_322o
D:\_datefac\output\router_mineru_trust_split_322b2
```

Official assets may be read for reference only:

```text
D:\_datefac\data\mapping\formal_scope_rules.json
D:\_datefac\data\overrides\semantic_alias_candidates.json
```

Do not write official assets.

## 5. Suggested new files

Follow project style. Suggested names:

```text
datefac/semantic/adjudication_batch_sanity_gate.py
datefac/semantic/adjudication_batch_sanity_gate_report.py
tools/run_adjudication_batch_sanity_gate_323c.py
```

Only add extra helpers if clearly justified.

## 6. Output directory

323C should write output artifacts to:

```text
D:\_datefac\output\adjudication_batch_sanity_gate_323c
```

Suggested outputs:

```text
adjudication_batch_sanity_gate_323c_summary.json
adjudication_batch_sanity_gate_323c_qa.json
adjudication_batch_sanity_gate_323c_gated_batch.json
adjudication_batch_sanity_gate_323c_gated_batch.xlsx
adjudication_batch_sanity_gate_323c_human_spot_check.xlsx
adjudication_batch_sanity_gate_323c_send_to_adjudicator.xlsx
adjudication_batch_sanity_gate_323c_holdouts.xlsx
adjudication_batch_sanity_gate_323c_notes.md
```

Do not commit output artifacts.

## 7. Sanity gate policy

323C should not decide financial truth. It should only catch obvious routing and safety issues before review.

### 7.1 Suspicious alias patterns

Alias candidates should be flagged for human spot-check or holdout if they look like:

- balance-sheet totals or line items, such as `流动资产`, `流动负债`, `非流动资产`, `非流动负债`, `股东权益`, `归属母公司股东权益`;
- subline labels beginning with `其中：` or similar;
- raw statement category labels rather than selected core metrics;
- date / stock code / empty label / narrative text;
- labels with high unit ambiguity;
- labels already covered by official 322 rules.

Do not automatically convert these into official rules.

### 7.2 Scope candidates

Scope/noise candidates can be sent to review if:

- label is readable;
- candidate is not selected core metric-like;
- no core false-exclusion risk flag is present;
- sample texts support non-core status.

### 7.3 Output routing buckets

Every item should receive exactly one routing bucket:

```text
SEND_TO_ADJUDICATOR
HUMAN_SPOT_CHECK_FIRST
HOLDOUT_CATEGORY_MISMATCH
HOLDOUT_AMBIGUOUS
HOLDOUT_ALREADY_OFFICIAL
HOLDOUT_INVALID_TEXT
```

Do not default high-risk items to `SEND_TO_ADJUDICATOR`.

## 8. Required behavior

### Step 1: Validate 323A-B readiness

Load 323A-B summary and QA.

Require:

```text
decision = SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW
qa_fail_count = 0
total_batch_count > 0
selected_alias_batch_count + selected_scope_batch_count = total_batch_count
```

If this fails, stop.

### Step 2: Load 323A-B batch items

Load JSON / XLSX batch items.

Required fields should include:

- batch_item_id
- source_group_id
- candidate_type
- repaired_label
- original_label
- candidate_question
- allowed_decisions
- expected_rule_type_if_accepted
- sample_candidate_ids
- sample_texts
- affected counts
- priority_score
- risk_flags
- provenance
- review_instruction
- default decision

### Step 3: Apply deterministic sanity gates

For each batch item:

- validate readable label;
- detect date / stock code / empty label;
- detect obvious long narrative;
- detect suspicious alias patterns;
- detect already-official 322 rules;
- detect mojibake risk;
- detect missing schema fields;
- detect candidate type mismatch.

Add fields:

```text
sanity_bucket
sanity_reasons
human_spot_check_required
send_to_adjudicator_allowed
```

### Step 4: Generate gated batch

Generate a gated batch package where:

- `SEND_TO_ADJUDICATOR` contains low-risk items only;
- `HUMAN_SPOT_CHECK_FIRST` contains plausible but risky items;
- holdouts contain invalid / category-mismatch / already-official / ambiguous items.

No item should be lost.

### Step 5: Generate human spot-check workbook

Generate a workbook for human spot-check.

Editable fields:

```text
human_decision
human_note
reviewer_name
review_timestamp
```

Allowed human decisions:

```text
SEND_TO_ADJUDICATOR
HOLDOUT
RECLASSIFY_AS_SCOPE_CANDIDATE
RECLASSIFY_AS_ALIAS_CANDIDATE
NEEDS_MORE_INFO
```

Default human decision:

```text
PENDING_HUMAN_SPOT_CHECK
```

### Step 6: QA

QA must include:

- 323A-B readiness pass;
- total item conservation pass;
- every item has exactly one sanity bucket;
- no invalid text in send-to-adjudicator;
- no mojibake in send-to-adjudicator;
- suspicious alias items not automatically sent to adjudicator;
- no already-official 322 item sent to adjudicator;
- schema completeness pass;
- unique batch item ids;
- output artifact presence check;
- no official asset modification confirmation;
- no LLM call confirmation;
- qa_fail_count.

### Step 7: Decision

If sanity gate succeeds:

```text
ADJUDICATION_BATCH_SANITY_GATE_323C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET
```

If not:

```text
ADJUDICATION_BATCH_SANITY_GATE_323C_NOT_READY
```

Include blocking reasons.

## 9. Suggested command

```bash
python tools/run_adjudication_batch_sanity_gate_323c.py \
  --batch-prep-dir D:\_datefac\output\semantic_adjudication_batch_prep_323ab \
  --candidate-text-repair-dir D:\_datefac\output\candidate_text_repair_323ar \
  --patch-application-dir D:\_datefac\output\official_semantic_patch_application_322n \
  --output-dir D:\_datefac\output\adjudication_batch_sanity_gate_323c
```

If safe defaults are implemented:

```bash
python tools/run_adjudication_batch_sanity_gate_323c.py
```

## 10. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\adjudication_batch_sanity_gate.py datefac\semantic\adjudication_batch_sanity_gate_report.py tools\run_adjudication_batch_sanity_gate_323c.py
```

Then run the 323C runner.

## 11. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323C source files if needed. Example:

```bash
git add datefac/semantic/adjudication_batch_sanity_gate.py
git add datefac/semantic/adjudication_batch_sanity_gate_report.py
git add tools/run_adjudication_batch_sanity_gate_323c.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323C adjudication batch sanity gate
```

Push to main only after successful checks.

## 12. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323C output directory.
4. Input batch count.
5. Routing bucket counts.
6. Suspicious alias count.
7. Send-to-adjudicator count.
8. Human spot-check count.
9. Holdout counts.
10. Highest-priority gated examples.
11. qa_fail_count.
12. decision.
13. git status result.
14. commit hash.
15. push result.
