# DateFac 330F Task
## Unfamiliar PDF Trust Benchmark

## Context

330E deduped candidate trust benchmark is complete and pushed.

330E commit:

```text
1622a47873a057c827533c980df7b290766d55fe
```

330E output:

```text
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
```

330E result:

```text
validated_330d_calibration = true
artifact_row_count = 12076
strict_deduped_candidate_count = 11974
cross_artifact_deduped_candidate_count = 10911
strict_duplicate_count = 102
cross_artifact_duplicate_count = 1165
source_candidate_id_coverage_count = 0
source_candidate_id_coverage_rate = 0.0
candidate_id_coverage_count = 12076
candidate_id_coverage_rate = 1.0
content_fingerprint_coverage_rate = 1.0
dedup_reliability_level = MEDIUM
policy_calibration_safe_to_continue = true
recommended_next_step = 330F_UNFAMILIAR_PDF_TRUST_BENCHMARK
official_assets_modified = false
no_official_asset_modification_during_330e = true
qa_fail_count = 0
decision = TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_FOR_330F_UNFAMILIAR_PDF_TRUST_BENCHMARK
```

Key 330E observations:

```text
potential_false_trusted_count stays 252 across artifact-row, strict-deduped, and cross-artifact views.
strict dedupe mostly removes internal 322B2 duplicates.
cross-artifact dedupe significantly reduces review-required and TARGET_METRIC_AMBIGUOUS rows.
source_candidate_id coverage is 0, so cross-artifact dedupe remains fingerprint-based.
dedup reliability is MEDIUM.
```

330F is the first Trust Engine benchmark step that should move beyond internal historical cache-only scoring and evaluate the Trust Engine sidecar on unfamiliar PDFs or unfamiliar pipeline outputs.

## Goal

Implement 330F: Unfamiliar PDF Trust Benchmark.

330F should evaluate the Trust Engine sidecar on an unfamiliar PDF benchmark set or, if full fresh parser outputs are not available, on a controlled unfamiliar-output directory supplied by the user. It must produce a delivery-oriented quality report showing how Trust Engine scoring behaves on unseen data.

330F must remain sidecar-only. It must not change production routing, official assets, or previous cached outputs.

The goal is to answer:

1. Can unfamiliar PDF outputs be converted into trust records?
2. What is the Trust Engine score/routing distribution on unfamiliar data?
3. How many records would be suggested as TRUSTED / REVIEW_REQUIRED / NEEDS_MORE_INFO / REJECTED by sidecar policy?
4. What are the dominant risk flags on unfamiliar data?
5. Are potential false-trusted risks acceptable or still too high?
6. Is the current Trust Engine policy ready for an end-to-end delivery-quality benchmark, or does it need stronger candidate IDs / calibration first?

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify parser/extraction/delivery code behavior unless the task explicitly creates new sidecar-only benchmark utilities.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not run LLM or semantic adjudicator.
- Do not let 330F override existing trusted/review routing.
- Do not start a new rule mining cycle.
- Do not commit output, temp, input/semantic_adjudicator_responses_*, unfamiliar PDF inputs, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330F benchmark source/report/runner/test files.

Parser/runtime constraint:

- Prefer cached unfamiliar pipeline outputs if available.
- If the user already has unfamiliar parser/trust-split outputs, use those.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM inside 330F unless the task is explicitly expanded later. 330F should benchmark trust scoring over existing unfamiliar outputs, not perform heavy parsing.

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
datefac/trust/unfamiliar_pdf_trust_benchmark_330f.py
datefac/trust/unfamiliar_pdf_trust_benchmark_330f_report.py
tools/run_unfamiliar_pdf_trust_benchmark_330f.py
tests/trust/test_unfamiliar_pdf_trust_benchmark_330f.py
```

Possible precise updates if needed:

```text
datefac/trust/__init__.py
datefac/trust/deduped_candidate_benchmark_330e.py
datefac/trust/cached_candidate_benchmark_330c.py
datefac/trust/confidence_scoring.py
```

Do not edit production pipeline modules.

## Inputs

Primary previous benchmark input:

```text
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
```

Scoring/calibration references:

```text
D:\_datefac\output\routing_policy_calibration_330d
D:\_datefac\output\cached_candidate_trust_scoring_330c
D:\_datefac\output\trust_engine_scoring_330b
D:\_datefac\output\trust_engine_foundation_330a
```

Unfamiliar candidate source inputs. Support one or more `--unfamiliar-source-dir` arguments. Suggested user-provided locations may include:

```text
D:\_datefac\output\unfamiliar_pdf_outputs
D:\_datefac\output\unfamiliar_trust_split
D:\_datefac\output\mineru_unfamiliar_benchmark
D:\_datefac\output\delivery_benchmark_unfamiliar
```

If no unfamiliar source directory is available, 330F must not pretend success. It should produce a readiness/blocked report with:

```text
unfamiliar_source_status = missing_or_empty
scored_unfamiliar_record_count = 0
qa_fail_count = 0
warning_count > 0
decision = TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_WAITING_FOR_UNFAMILIAR_OUTPUTS
```

Official assets may be read only for hash/no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Candidate loading behavior

Reuse the 330C candidate-like loading logic where possible.

Search only inside explicitly provided unfamiliar source dirs.

Prefer files:

```text
*.jsonl
*.json
*.xlsx
*_affected_candidates.xlsx
*_trust_split*.xlsx
*_candidate*.jsonl
*_candidate*.json
*_summary.json
```

Avoid loading huge unrelated files blindly. Record skipped files and reasons.

Best-effort field mapping remains:

```text
candidate_id <- candidate_id / row_id / source_candidate_id / generated stable id
metric_label_raw <- metric_label_raw / label / alias_label / row_text / metric_label
normalized_metric <- normalized_metric / target_metric / metric_code
value <- value / numeric_value / extracted_value
unit <- unit / unit_raw / normalized_unit
year <- year / fiscal_year / column_year
parser_sources <- parser_source / parser_sources / source_parser
evidence_refs <- page / source_page / table_id / row_text / provenance
risk_flags <- risk_flags / warnings / validation_flags / error_codes
existing_status <- trusted/review_required/rejected/out_of_scope if available
source_pdf <- pdf_name / document_name / source_file / source_pdf if available
```

## Required behavior

1. Validate 330E readiness:

```text
decision = TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_FOR_330F_UNFAMILIAR_PDF_TRUST_BENCHMARK
qa_fail_count = 0
policy_calibration_safe_to_continue = true
dedup_reliability_level = MEDIUM or HIGH
no_official_asset_modification_during_330e = true
```

2. Load unfamiliar source dirs from CLI.
3. If no source dirs exist or no compatible candidate rows are found, emit a non-blocking waiting report, not a fake benchmark.
4. If rows are found:
   - convert rows to trust records
   - score with 330B scoring
   - apply sidecar routing policy only in output artifacts
   - dedupe using 330E-style strict and cross-artifact fingerprints where possible
5. Generate distributions:

```text
confidence_level_distribution
routing_decision_distribution
risk_flag_distribution
score_bucket_distribution
source_artifact_distribution
source_pdf_distribution if available
existing_status_distribution if available
sidecar_vs_existing_status_comparison if available
```

6. Generate unfamiliar benchmark quality metrics:

```text
unfamiliar_source_dir_count
unfamiliar_candidate_artifact_row_count
unfamiliar_strict_deduped_candidate_count
unfamiliar_cross_artifact_deduped_candidate_count
scored_unfamiliar_record_count
potential_false_trusted_count
trusted_with_warning_risk_count
trusted_with_low_evidence_count
missing_evidence_count
target_metric_ambiguous_count
value_parse_failed_count
unit_unknown_count
```

7. Generate a delivery-oriented summary:

```text
sidecar_trusted_suggestion_count
sidecar_review_required_suggestion_count
sidecar_needs_more_info_or_rejected_count
estimated_human_review_burden_count
estimated_auto_trusted_ratio
```

8. Generate calibration samples workbook:

```text
unfamiliar_pdf_trust_benchmark_330f_samples.xlsx
```

9. Produce a recommendation:

```text
recommended_next_step = 330G_END_TO_END_DELIVERY_QUALITY_REPORT
```

only if:

```text
scored_unfamiliar_record_count > 0
potential_false_trusted_count is low or explicitly explainable
no blocking QA failures
```

Otherwise recommend:

```text
330F2_UNFAMILIAR_OUTPUT_PREPARATION
```

or

```text
330D2_STRONGER_CANDIDATE_ID_EXTRACTION
```

10. Confirm official assets are not modified.
11. Generate QA, no-apply proof, summary, scored records, comparison artifacts, samples workbook, and report.

## Output directory

```text
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
```

Suggested outputs:

```text
unfamiliar_pdf_trust_benchmark_330f_summary.json
unfamiliar_pdf_trust_benchmark_330f_qa.json
unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl
unfamiliar_pdf_trust_benchmark_330f_distribution.json
unfamiliar_pdf_trust_benchmark_330f_samples.xlsx
unfamiliar_pdf_trust_benchmark_330f_no_apply_proof.json
unfamiliar_pdf_trust_benchmark_330f_report.md
```

## Expected summary fields

When unfamiliar candidate rows exist:

```text
validated_330e_benchmark = true
unfamiliar_source_status = loaded
unfamiliar_source_dir_count >= 1
unfamiliar_candidate_artifact_row_count > 0
scored_unfamiliar_record_count > 0
confidence_level_distribution exists
routing_decision_distribution exists
risk_flag_distribution exists
score_bucket_distribution exists
sidecar_trusted_suggestion_count >= 0
sidecar_review_required_suggestion_count >= 0
estimated_auto_trusted_ratio >= 0
potential_false_trusted_count >= 0
no_official_asset_modification_during_330f = true
qa_fail_count = 0
```

Possible ready decision:

```text
TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_DELIVERY_QUALITY_REPORT
```

If benchmark runs but has material warnings:

```text
TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_WITH_WARNINGS
```

When no unfamiliar candidate rows exist:

```text
unfamiliar_source_status = missing_or_empty
scored_unfamiliar_record_count = 0
qa_fail_count = 0
decision = TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_WAITING_FOR_UNFAMILIAR_OUTPUTS
```

If blocking QA fails:

```text
TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_NOT_READY
```

## Suggested command

With unfamiliar source dirs:

```bash
python tools/run_unfamiliar_pdf_trust_benchmark_330f.py \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --unfamiliar-source-dir D:\_datefac\output\unfamiliar_pdf_outputs \
  --output-dir D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
```

If unfamiliar outputs are not ready yet, run without source dirs to produce a readiness/waiting report:

```bash
python tools/run_unfamiliar_pdf_trust_benchmark_330f.py \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --output-dir D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
```

## Compile checks

```bash
python -m py_compile datefac\trust\unfamiliar_pdf_trust_benchmark_330f.py datefac\trust\unfamiliar_pdf_trust_benchmark_330f_report.py tools\run_unfamiliar_pdf_trust_benchmark_330f.py tests\trust\test_unfamiliar_pdf_trust_benchmark_330f.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/unfamiliar_pdf_trust_benchmark_330f.py
git add datefac/trust/unfamiliar_pdf_trust_benchmark_330f_report.py
git add tools/run_unfamiliar_pdf_trust_benchmark_330f.py
git add tests/trust/test_unfamiliar_pdf_trust_benchmark_330f.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
git add datefac/trust/deduped_candidate_benchmark_330e.py
git add datefac/trust/cached_candidate_benchmark_330c.py
git add datefac/trust/confidence_scoring.py
```

Commit:

```text
Add 330F unfamiliar PDF trust benchmark
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330E validation result.
5. Unfamiliar source status and source dirs.
6. Loaded/scored unfamiliar record counts.
7. Dedupe counts if rows exist.
8. Confidence/routing/risk distributions if rows exist.
9. Delivery-oriented metrics if rows exist.
10. Samples workbook path if generated.
11. Recommendation / next step.
12. Official asset modification confirmation.
13. QA fail count.
14. Decision.
15. Git status result.
16. Commit hash.
17. Push result.
18. Residual risks.
