# DateFac 323A-R Task
## Candidate Text Encoding Repair and Review Readiness

## 1. Stage context

DateFac has completed 323A high-impact semantic candidates mining.

323A commit:

```text
325d7944c7c77e7064b80a765f006e86a47deb1e
```

323A changed files:

```text
datefac/semantic/high_impact_semantic_candidates_mining.py
datefac/semantic/high_impact_semantic_candidates_report.py
tools/run_high_impact_semantic_candidates_mining_323a.py
```

323A output dir:

```text
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
```

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

However, the highest-priority examples show mojibake / encoding corruption:

```text
alias | 鍏朵腑锛氭湇鍔? | priority_score=285.6 | affected_review_required_count=28
alias | 鍏朵腑锛氳澶? | priority_score=285.6 | affected_review_required_count=28
scope_noise | 鍏朵粬闈炴祦鍔ㄨ礋鍊? | priority_score=252.0 | affected_review_required_count=21
scope_noise | 鍏朵粬闈炴祦鍔ㄨ祫浜? | priority_score=252.0 | affected_review_required_count=21
alias | 褰掑睘姣嶅叕鍙歌偂涓滄潈鐩? | priority_score=252.0 | affected_review_required_count=21
```

These likely correspond to common Chinese financial labels but are not currently human-readable. 323A-R must fix or isolate this before any semantic adjudication or human review.

## 2. Goal

Implement 323A-R: candidate text encoding repair and review readiness.

The goal is to repair, normalize, or explicitly flag mojibake/corrupted candidate labels in the 323A mining outputs so the next review/adjudication batch is human-readable and safe.

323A-R should not create semantic rules, should not call LLMs, should not modify official assets, and should not run parsers.

It should produce a cleaned review-ready candidate package and a QA report showing whether 323A outputs are ready for adjudication batch prep.

## 3. Hard constraints

1. Do not modify production pipeline.
2. Do not modify official mapping / override assets.
3. Do not apply semantic rules.
4. Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
5. Do not call LLM / semantic adjudicator.
6. Use cached 323A outputs and cached candidate data only.
7. Do not modify `E:\mineru_lab`.
8. Do not commit `output/`, `input/semantic_adjudicator_responses_*`, `temp/`, or historical dirty files.
9. Do not use `git add -A` or `git add .`.
10. Only precisely add or modify 323A-R source/report/runner files and, if needed, narrowly patch 323A mining code to improve text decoding for future runs.

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

Primary 323A output:

```text
D:\_datefac\output\high_impact_semantic_candidates_mining_323a
```

Cached candidate / trust split input:

```text
D:\_datefac\output\router_mineru_trust_split_322b2
```

Official post-patch baseline:

```text
D:\_datefac\output\post_patch_regression_validation_322o
```

Use existing project conventions to locate candidate rows, labels, row text, metric text, and source provenance.

## 5. Suggested files

Follow existing project style. Suggested new files:

```text
datefac/semantic/candidate_text_repair.py
datefac/semantic/candidate_text_repair_report.py
tools/run_candidate_text_repair_323ar.py
```

If the bug belongs inside 323A mining itself, a narrow patch to these files is allowed:

```text
datefac/semantic/high_impact_semantic_candidates_mining.py
datefac/semantic/high_impact_semantic_candidates_report.py
tools/run_high_impact_semantic_candidates_mining_323a.py
```

Only patch existing 323A code if it prevents future mojibake at source.

## 6. Output directory

323A-R should write output artifacts to:

```text
D:\_datefac\output\candidate_text_repair_323ar
```

Suggested outputs:

```text
candidate_text_repair_323ar_summary.json
candidate_text_repair_323ar_qa.json
candidate_text_repair_323ar_repaired_ranked_groups.xlsx
candidate_text_repair_323ar_repaired_top_alias_opportunities.xlsx
candidate_text_repair_323ar_repaired_top_scope_noise_opportunities.xlsx
candidate_text_repair_323ar_mojibake_groups.xlsx
candidate_text_repair_323ar_unrepairable_holdouts.xlsx
candidate_text_repair_323ar_review_ready_package.xlsx
candidate_text_repair_323ar_notes.md
```

Do not commit output artifacts.

## 7. Required behavior

### Step 1: Validate 323A readiness

Load 323A summary and QA.

Require:

```text
decision = HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP
qa_fail_count = 0
grouped_candidate_count > 0
top_alias_opportunity_count > 0 or top_scope_noise_opportunity_count > 0
```

If this fails, stop and do not repair.

### Step 2: Detect mojibake / corrupted text

Scan all 323A group labels, sample labels, row text, metric labels, and review package fields for mojibake patterns.

Detect common Chinese mojibake indicators such as:

- `鍏`
- `锛`
- `姣`
- `涓`
- `祫`
- `偂`
- replacement character `�`
- excessive `?` inside Chinese-like strings
- strings with high ratio of mojibake fragments

Generate counts:

```text
mojibake_group_count
mojibake_top_alias_count
mojibake_top_scope_count
mojibake_sample_text_count
```

### Step 3: Repair candidate text where deterministic and safe

Try deterministic repair only.

Recommended approach:

- attempt `latin1 -> utf8` repair when applicable;
- attempt `gbk/cp936` reinterpretation when applicable;
- compare repaired text against known source candidate text if available;
- prefer original cached raw text if a non-corrupted version exists elsewhere in candidate records;
- preserve original corrupted text in a separate field.

Do not invent labels.

If repair confidence is low, do not repair. Flag as holdout.

### Step 4: Add repaired-text fields

For each group/opportunity, preserve both original and repaired fields:

```text
original_label
repaired_label
repair_method
repair_confidence
is_mojibake
repair_status
```

Recommended repair statuses:

```text
REPAIRED_DETERMINISTIC
ALREADY_CLEAN
UNREPAIRABLE_HOLDOUT
NEEDS_SOURCE_TEXT_RECHECK
```

### Step 5: Rebuild review-ready package

Generate repaired top alias and scope opportunity tables.

Only include groups in the review-ready package if:

- repair_status is ALREADY_CLEAN or REPAIRED_DETERMINISTIC;
- repaired_label is human-readable;
- required provenance exists;
- group type and score are preserved;
- official 322 closed rules are not rediscovered as new.

Send unrepairable groups to holdout, not adjudication.

### Step 6: Validate ranking stability

The repair should not change impact counts or priority scores except for display text.

Check:

- grouped_candidate_count remains aligned with 323A;
- top alias / scope counts may decrease only if mojibake groups are held out;
- affected candidate counts preserved;
- priority scores preserved;
- no duplicate group id introduced.

### Step 7: QA

QA must include:

- 323A readiness pass;
- mojibake detection count;
- deterministic repair count;
- unrepairable holdout count;
- review-ready alias count;
- review-ready scope count;
- original/repaired field preservation pass;
- no official assets modified pass;
- no parser run confirmation;
- no LLM call confirmation;
- ranking stability check;
- duplicate group id check;
- output artifact presence check;
- qa_fail_count.

### Step 8: Decision

If enough high-impact groups are clean/repaired and no QA fails:

```text
CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP
```

If mojibake remains in top review-ready package or repair is unsafe:

```text
CANDIDATE_TEXT_REPAIR_323AR_NOT_READY_SOURCE_TEXT_RECHECK_REQUIRED
```

## 8. Suggested command

```bash
python tools/run_candidate_text_repair_323ar.py \
  --mining-dir D:\_datefac\output\high_impact_semantic_candidates_mining_323a \
  --trust-split-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --output-dir D:\_datefac\output\candidate_text_repair_323ar
```

If safe defaults are implemented:

```bash
python tools/run_candidate_text_repair_323ar.py
```

## 9. Compile / run checks

Run:

```bash
python -m py_compile datefac\semantic\candidate_text_repair.py datefac\semantic\candidate_text_repair_report.py tools\run_candidate_text_repair_323ar.py
```

If 323A code is patched, include it in py_compile too.

Then run the 323A-R runner.

## 10. Git workflow

Before changes:

```bash
git status --short
```

After implementation and successful run:

```bash
git status --short
```

Only add precise 323A-R source files and narrowly patched 323A files if needed. Examples:

```bash
git add datefac/semantic/candidate_text_repair.py
git add datefac/semantic/candidate_text_repair_report.py
git add tools/run_candidate_text_repair_323ar.py
```

If 323A mining code was narrowly patched:

```bash
git add datefac/semantic/high_impact_semantic_candidates_mining.py
git add datefac/semantic/high_impact_semantic_candidates_report.py
git add tools/run_high_impact_semantic_candidates_mining_323a.py
```

Do not add output files or known dirty files.

Suggested commit message:

```text
Add 323A-R candidate text repair readiness check
```

Push to main only after successful checks.

## 11. Final report expected from Codex

After completion, report:

1. Modified files.
2. Commands run.
3. 323A-R output directory.
4. Mojibake group counts.
5. Deterministic repair counts.
6. Unrepairable holdout counts.
7. Review-ready alias / scope counts.
8. Highest-priority repaired examples.
9. qa_fail_count.
10. decision.
11. Whether 323A source code was patched.
12. git status result.
13. commit hash.
14. push result.
