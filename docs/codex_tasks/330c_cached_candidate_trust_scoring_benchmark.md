# DateFac 330C Task
## Cached Candidate Trust Scoring Benchmark

## Context

330B Trust Engine deterministic scoring is complete and pushed.

330B commit:

```text
f17fecff2b0e65ed9906adeefcd25796d3dc7269
```

330B output:

```text
D:\_datefac\output\trust_engine_scoring_330b
```

330B result:

```text
validated_330a_foundation = true
risk_registry_count = 18
scoring_model_component_count = 7
scored_example_count = 5
routing_policy_reused = true
routing_policy_smoke_test_count = 5
routing_policy_smoke_test_passed = true
cached_candidate_sidecar_sample_count = 3
cached_candidate_sidecar_sample_reason = loaded_from_330a_example_trust_records
no_official_asset_modification_during_330b = true
qa_fail_count = 0
decision = TRUST_ENGINE_SCORING_330B_READY_FOR_330C_CACHED_CANDIDATE_TRUST_SCORING_BENCHMARK
```

330B added deterministic sidecar scoring:

```text
datefac/trust/confidence_scoring.py
datefac/trust/trust_engine_scoring_330b_report.py
tools/run_trust_engine_scoring_330b.py
tests/trust/test_trust_engine_scoring_330b.py
```

330C is the next step. It should run the Trust Engine scoring layer against cached candidate-like artifacts to produce a sidecar benchmark. It must not change production routing.

## Goal

Implement 330C: Cached Candidate Trust Scoring Benchmark.

330C should batch-score cached candidate-like rows using the 330B deterministic scoring layer and compare Trust Engine sidecar routing suggestions with existing cached statuses where available.

The goal is not to decide production behavior yet. The goal is to measure distribution and expose calibration questions:

```text
cached candidates -> trust records -> scored trust records -> distribution report
```

330C should answer:

1. How many cached candidates can be converted into trust records?
2. What is the score distribution?
3. What routing decisions would Trust Engine suggest as a sidecar?
4. Where do sidecar suggestions diverge from existing cached trusted/review/rejected statuses?
5. What risk flags dominate?
6. Are there potential false-trusted risks?

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify parser/extraction/delivery code behavior.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM or semantic adjudicator.
- Do not recompute production outputs.
- Do not let 330C override existing trusted/review routing.
- Use cached artifacts only.
- Do not start a new rule mining cycle.
- Do not commit output, temp, input/semantic_adjudicator_responses_*, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330C trust benchmark source/report/runner/test files.

Existing dirty files to leave untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

## Suggested files

New files:

```text
datefac/trust/cached_candidate_benchmark_330c.py
datefac/trust/cached_candidate_benchmark_330c_report.py
tools/run_cached_candidate_trust_scoring_330c.py
tests/trust/test_cached_candidate_benchmark_330c.py
```

Possible precise updates if needed:

```text
datefac/trust/__init__.py
datefac/trust/confidence_scoring.py
datefac/trust/schema.py
```

Do not edit production pipeline modules.

## Inputs

Primary scoring foundation input:

```text
D:\_datefac\output\trust_engine_scoring_330b
```

Candidate-like cached artifact sources. Use best-effort discovery and robust optional loading:

```text
D:\_datefac\output\router_mineru_trust_split_322b2
D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i
D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g
D:\_datefac\output\post_patch_regression_validation_325o
D:\_datefac\output\post_patch_regression_validation_324m
D:\_datefac\output\post_patch_regression_validation_323n
D:\_datefac\output\alias_patch_cycle_closure_325p
```

Official assets may be read only for hash/no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Candidate loading behavior

330C should search likely cached files in the input dirs, such as:

```text
*.json
*.jsonl
*.xlsx
```

but avoid loading huge unrelated files blindly. Prefer known filenames from previous outputs:

```text
*_affected_candidates.xlsx
*_before_after_comparison.xlsx
*_summary.json
*_closure.json
```

If no compatible candidate-level cache is found, 330C must not fail. It should fall back to deterministic benchmark fixtures and report:

```text
cached_candidate_count = 0
fallback_fixture_count > 0
candidate_source_status = fallback_fixtures_only
```

If compatible rows are found, convert them into trust records using best-effort mappings:

```text
candidate_id <- candidate_id / row_id / source_candidate_id / generated stable id
metric_label_raw <- metric_label_raw / label / alias_label / row_text
normalized_metric <- normalized_metric / target_metric / metric_code
value <- value / numeric_value / extracted_value
unit <- unit / unit_raw / normalized_unit
year <- year / fiscal_year / column_year
parser_sources <- parser_source / parser_sources / source_parser
evidence_refs <- page / source_page / table_id / row_text / provenance
risk_flags <- risk_flags / warnings / validation_flags / error_codes
existing_status <- trusted/review_required/rejected/out_of_scope if available
```

## Required behavior

1. Validate 330B readiness:

```text
decision = TRUST_ENGINE_SCORING_330B_READY_FOR_330C_CACHED_CANDIDATE_TRUST_SCORING_BENCHMARK
qa_fail_count = 0
routing_policy_smoke_test_passed = true
scored_example_count >= 5
```

2. Discover and load cached candidate-like rows best-effort.
3. Convert compatible rows into 330A/330B trust records.
4. Score all converted trust records with 330B `score_trust_record` or equivalent.
5. Keep this entirely sidecar; do not modify cached input artifacts.
6. Produce distributions:

```text
confidence_level_distribution
routing_decision_distribution
risk_flag_distribution
score_bucket_distribution
source_artifact_distribution
existing_status_distribution if available
sidecar_vs_existing_status_comparison if available
```

7. Flag potential calibration issues:

```text
potential_false_trusted_count
trusted_with_warning_risk_count
trusted_with_low_evidence_count
review_required_high_score_count
rejected_or_needs_more_info_high_score_count
missing_evidence_count
```

8. Generate a small review workbook for calibration candidates:

```text
trust_engine_scoring_330c_calibration_samples.xlsx
```

This workbook is for inspection only. It must not be used to change production behavior.

9. Confirm official assets are not modified.
10. Generate QA, no-apply proof, summary, benchmark records, and report.

## Output directory

```text
D:\_datefac\output\cached_candidate_trust_scoring_330c
```

Suggested outputs:

```text
cached_candidate_trust_scoring_330c_summary.json
cached_candidate_trust_scoring_330c_qa.json
cached_candidate_trust_scoring_330c_scored_records.jsonl
cached_candidate_trust_scoring_330c_distribution.json
cached_candidate_trust_scoring_330c_calibration_samples.xlsx
cached_candidate_trust_scoring_330c_no_apply_proof.json
cached_candidate_trust_scoring_330c_report.md
```

## Expected summary metrics

Metrics should be data-dependent, but these fields must exist:

```text
validated_330b_scoring = true
candidate_source_dir_count >= 1
cached_candidate_count >= 0
fallback_fixture_count >= 0
scored_record_count > 0
confidence_level_distribution exists
routing_decision_distribution exists
risk_flag_distribution exists
score_bucket_distribution exists
calibration_sample_count >= 0
potential_false_trusted_count >= 0
trusted_with_warning_risk_count >= 0
missing_evidence_count >= 0
no_official_asset_modification_during_330c = true
qa_fail_count = 0
decision = TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_READY_FOR_330D_ROUTING_POLICY_CALIBRATION
```

If only fallback fixtures were used:

```text
TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_READY_WITH_WARNINGS
```

If blocking QA fails:

```text
TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_NOT_READY
```

## Suggested command

```bash
python tools/run_cached_candidate_trust_scoring_330c.py \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --candidate-source-dir D:\_datefac\output\router_mineru_trust_split_322b2 \
  --candidate-source-dir D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i \
  --candidate-source-dir D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g \
  --candidate-source-dir D:\_datefac\output\post_patch_regression_validation_325o \
  --output-dir D:\_datefac\output\cached_candidate_trust_scoring_330c
```

## Compile checks

```bash
python -m py_compile datefac\trust\__init__.py datefac\trust\schema.py datefac\trust\risk_registry.py datefac\trust\routing_policy.py datefac\trust\no_apply_proof.py datefac\trust\confidence_scoring.py datefac\trust\cached_candidate_benchmark_330c.py datefac\trust\cached_candidate_benchmark_330c_report.py tools\run_cached_candidate_trust_scoring_330c.py tests\trust\test_cached_candidate_benchmark_330c.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only. Example:

```bash
git add datefac/trust/cached_candidate_benchmark_330c.py
git add datefac/trust/cached_candidate_benchmark_330c_report.py
git add tools/run_cached_candidate_trust_scoring_330c.py
git add tests/trust/test_cached_candidate_benchmark_330c.py
```

If existing trust package files are deliberately updated:

```bash
git add datefac/trust/__init__.py
git add datefac/trust/confidence_scoring.py
git add datefac/trust/schema.py
```

Commit:

```text
Add 330C cached candidate trust benchmark
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330B scoring validation result.
5. Candidate source dirs and loaded record counts.
6. Fallback fixture count and reason if used.
7. Scored record count.
8. Confidence / routing / risk distributions.
9. Calibration issue counts.
10. Calibration workbook path.
11. Official asset modification confirmation.
12. QA fail count.
13. Decision.
14. Git status result.
15. Commit hash.
16. Push result.
17. Verification result and residual risks.
