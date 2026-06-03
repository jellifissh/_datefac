# DateFac 323A-B Task
## Semantic Adjudication Batch Preparation

## 1. Stage context

DateFac has completed 323A and 323A-R.

323A mined high-impact semantic opportunities from remaining unresolved / review-required candidates.

323A result:

```text
loaded_candidate_count = 5972
loaded_unresolved_review_required_candidate_count = 3358
review_required_unknown_metric_count = 3184
review_required_unit_unknown_count = 491
grouped_candidate_count = 552
alias_opportunity_group_count = 233
scope_noise_group_count = 19
unit_related_group_count = 178
ambiguous_group_count = 122
top_alias_opportunity_count = 30
top_scope_noise_opportunity_count = 19
unit_holdout_count = 178
ambiguous_holdout_count = 122
qa_fail_count = 0
decision = HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP
```

323A-R repaired / checked candidate text readiness.

323A-R commit:

```text
3df21fb
```

323A-R changed files:

```text
datefac/semantic/candidate_text_repair.py
datefac/semantic/candidate_text_repair_report.py
tools/run_candidate_text_repair_323ar.py
```

323A-R output dir:

```text
D:\_datefac\output\candidate_text_repair_323ar
```

323A-R result:

```text
mojibake_group_count = 0
mojibake_top_alias_count = 0
mojibake_top_scope_count = 0
mojibake_sample_text_count = 0
deterministic_repair_count = 0
unrepairable_holdout_count = 49
review_ready_alias_count = 211
review_ready_scope_count = 11
qa_fail_count = 0
decision = CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP
```

Key finding:

```text
323A persisted outputs do not contain true mojibake contamination. The earlier mojibake-looking examples were likely display-layer encoding issues. The real unsafe records are non-encoding anomalies such as dates, stock codes, and empty labels, already isolated into holdout.
```

323A-B is the next step:

> Prepare a deterministic semantic adjudication / human review batch from review-ready 323A-R candidates.

323A-B must not call LLM / semantic adjudicator. It only prepares the batch.

## 2. Goal

Implement 323A-B: semantic adjudication batch preparation.

The goal is to turn the clean review-ready candidate groups from 323A-R into a compact, high-impact, schema-valid adjudication batch package.

The output should be suitable for either:

1. human review, or
2. a later semantic adjudicator call task.

323A-B must not generate official rules, must not apply rules, and must not call LLMs.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply semantic rules.
4. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
5. Do not call LLM / semantic adjudicator.
6. Use 323A-R review-ready outputs and cached candidate data only.
7. Do not modify `E:\mineru_lab`.
8. Do not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
9. Do not use `git add -A` or `git add .`.
10. Only precisely add 323A-B source/report/runner files.

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
D:\_datefac\output\candidate_text_repair_323ar
```

Upstream references:

```text
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
D:\_datefac\output\post_patch_regression_validation_322o
D:\_datefac\output\official_semantic_patch_application_322n
D:\_datefac\output\router_mineru_trust_split_322b2
```

Use existing project conventions to load review-ready alias / scope opportunities, group metadata, sample rows, risk flags, and holdouts.

## 5. Suggested new files

Follow existing project style. Suggested names:

```text
datefac/semantic/semantic_adjudication_batch_prep.py
datefac/semantic/semantic_adjudication_batch_prep_report.py
tools/run_semantic_adjudication_batch_prep_323ab.py
```

Only add extra helpers if clearly justified.

## 6. Output directory

323A-B should write output artifacts to:

```text
D:\_datefac\output\semantic_adjudication_batch_prep_323ab
```

Suggested outputs:

```text
semantic_adjudication_batch_prep_323ab_summary.json
semantic_adjudication_batch_prep_323ab_batch.json
semantic_adjudication_batch_prep_323ab_batch.xlsx
semantic_adjudication_batch_prep_323ab_alias_items.xlsx
semantic_adjudication_batch_prep_323ab_scope_items.xlsx
semantic_adjudication_batch_prep_323ab_holdouts.xlsx
semantic_adjudication_batch_prep_323ab_schema.json
semantic_adjudication_batch_prep_323ab_qa.json
semantic_adjudication_batch_prep_323ab_review_instructions.md
```

Do not commit output artifacts.

## 7. Batch composition policy

323A-B should prepare a compact batch, not dump all 222 review-ready groups.

Recommended default batch size:

```text
max_total_batch_items = 40
max_alias_batch_items = 25
max_scope_batch_items = 15
```

Since 323A-R found:

```text
review_ready_alias_count = 211
review_ready_scope_count = 11
```

A reasonable default is:

```text
alias_batch_items <= 25
scope_batch_items <= 11
```

Do not include unit-related holdouts or ambiguous holdouts in this batch.

Do not include unrepairable holdouts.

## 8. Required behavior

### Step 1: Validate 323A-R readiness

Load 323A-R summary and QA.

Require:

```text
decision = CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP
qa_fail_count = 0
review_ready_alias_count > 0 or review_ready_scope_count > 0
unrepairable_holdout_count >= 0
```

If this fails, stop and do not prepare a batch.

### Step 2: Load review-ready candidates

Load repaired / review-ready alias and scope candidates from 323A-R outputs.

Each item should include:

- group id;
- group type: alias or scope_noise;
- repaired label;
- original label;
- priority score;
- affected review_required count;
- affected candidate count;
- sample candidate ids;
- sample row texts;
- parser/source provenance;
- risk flags;
- suggested next action.

### Step 3: Exclude unsafe candidates

Exclude:

- unit-related holdouts;
- ambiguous holdouts;
- unrepairable holdouts;
- dates;
- stock codes;
- empty labels;
- groups already applied in 322 official cycle;
- groups with missing repaired label;
- groups with high mojibake / display risk.

### Step 4: Select adjudication batch items

Select top items by priority and safety.

Recommended selection:

```text
alias_batch_count <= 25
scope_batch_count <= 15
actual scope count can be lower if only 11 review-ready scope groups exist
```

The selection should preserve ranking from 323A / 323A-R unless safety filters exclude an item.

### Step 5: Build adjudication item schema

Each batch item should be schema-valid and self-contained.

Recommended fields:

```text
batch_item_id
source_group_id
candidate_type
repaired_label
original_label
candidate_question
allowed_decisions
expected_rule_type_if_accepted
sample_candidate_ids
sample_texts
affected_candidate_count
affected_review_required_count
priority_score
risk_flags
provenance
review_instruction
```

Allowed decisions should be explicit:

For alias candidates:

```text
ACCEPT_ALIAS
REJECT_ALIAS
NEEDS_MORE_INFO
OUT_OF_SCOPE
```

For scope noise candidates:

```text
ACCEPT_OUT_OF_SCOPE
REJECT_OUT_OF_SCOPE
NEEDS_MORE_INFO
POSSIBLE_CORE_METRIC
```

### Step 6: Generate review questions

Generate deterministic review questions, not LLM answers.

Example alias question:

```text
Does the candidate label '<label>' safely map to an existing selected core metric alias? If yes, identify the target metric; otherwise reject or mark needs_more_info.
```

Example scope question:

```text
Is the candidate label '<label>' safely out of scope for selected core metric extraction? If yes, mark ACCEPT_OUT_OF_SCOPE; otherwise reject or mark possible_core_metric.
```

### Step 7: Generate human review workbook and JSON batch

Produce both:

- machine-readable JSON batch;
- human-readable XLSX workbook;
- review instructions markdown.

No decisions should be pre-approved.

Default decision should be:

```text
PENDING_REVIEW
```

### Step 8: QA

QA must include:

- 323A-R readiness pass;
- review-ready candidate load pass;
- unsafe candidate exclusion pass;
- batch item count check;
- alias batch count check;
- scope batch count check;
- no unit holdout included;
- no ambiguous holdout included;
- no unrepairable holdout included;
- no already-official 322 rule included;
- no mojibake item included;
- no empty label item included;
- no stock-code/date-only item included;
- unique batch item id check;
- required schema fields check;
- default decisions all PENDING_REVIEW;
- output artifact presence check;
- qa_fail_count.

### Step 9: Decision

If batch prep succeeds:

```text
SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW
```

If not:

```text
SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_NOT_READY
```

Include blocking reasons.

## 9. Suggested command

```bash
python tools/run_semantic_adjudication_batch_prep_323ab.py \
  --candidate-text-repair-dir D:\_datefac\output\candidate_text_repair_323ar \
  --mining-dir D:\_datefac\output\high_impact_semantic_candidates_mining_323a \
  --patch-application-dir D:\_datefac\output\official_semantic_patch_application_322n \
  --output-dir D:\_datefac\output\semantic_adjudication_batch_prep_323ab
```

If safe defaults are implemented:

```bash
python tools/run_semantic_adjudication_batch_prep_323ab.py
```

## 10. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\semantic_adjudication_batch_prep.py datefac\semantic\semantic_adjudication_batch_prep_report.py tools\run_semantic_adjudication_batch_prep_323ab.py
```

Then run the 323A-B runner.

## 11. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323A-B source files if needed. Example:

```bash
git add datefac/semantic/semantic_adjudication_batch_prep.py
git add datefac/semantic/semantic_adjudication_batch_prep_report.py
git add tools/run_semantic_adjudication_batch_prep_323ab.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323A-B semantic adjudication batch prep
```

Push to main only after successful checks and after confirming git status contains only intended 323A-B source files plus the known pre-existing dirty files.

## 12. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323A-B output directory.
4. Loaded review-ready alias / scope counts.
5. Selected alias / scope batch counts.
6. Excluded unsafe / holdout counts.
7. Highest-priority batch examples.
8. qa_fail_count.
9. decision.
10. git status result.
11. commit hash.
12. push result.
