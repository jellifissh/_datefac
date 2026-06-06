# DateFac 330E Task
## Deduped Candidate Trust Benchmark

## Context

330D routing policy calibration is complete and pushed.

330D commit:

```text
039742c20d927c381f507c51c6982cd125e28296
```

330D output:

```text
D:\_datefac\output\routing_policy_calibration_330d
```

330D result:

```text
validated_330c_benchmark = true
qa_fail_count = 0
scored_record_count = 12076
fallback_fixture_count = 0
candidate_source_status = cached_candidates_loaded
artifact_row_benchmark = true
deduped_candidate_benchmark = false
artifact_row_count = 12076
deduped_candidate_count = 11974
duplicate_artifact_row_count = 102
cross_artifact_row_fingerprint_duplicate_artifact_row_count = 1165
potential_false_trusted_count = 252
target_metric_ambiguous_count = 6720
production_routing_modified = false
official_assets_modified = false
no_official_asset_modification_during_330d = true
decision = TRUST_ENGINE_ROUTING_POLICY_CALIBRATION_330D_READY_WITH_WARNINGS
```

330D residual warning:

```text
The deduped candidate view is still best-effort and has not been validated as a true candidate-level benchmark.
source_candidate_id coverage is 0.
artifact-row benchmark may inflate distribution and calibration counts.
```

330E should address this warning before unfamiliar-PDF benchmarking or production routing integration.

## Goal

Implement 330E: Deduped Candidate Trust Benchmark.

330E should build a stronger candidate-level deduplication layer over the 330C scored artifact rows, produce deduped trust scoring distributions, compare artifact-row vs deduped-candidate results, and identify how calibration metrics change after deduplication.

330E must remain sidecar-only. It must not change production routing or official assets.

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify parser/extraction/delivery code behavior.
- Do not modify official mapping / override assets.
- Do not apply semantic rules.
- Do not mark anything trusted in production.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not call LLM or semantic adjudicator.
- Do not recompute production outputs.
- Do not let 330E override existing trusted/review routing.
- Use cached 330C/330D/330B/330A artifacts only.
- Do not start a new rule mining cycle.
- Do not commit output, temp, input/semantic_adjudicator_responses_*, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330E trust benchmark source/report/runner/test files.

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
datefac/trust/deduped_candidate_benchmark_330e.py
datefac/trust/deduped_candidate_benchmark_330e_report.py
tools/run_deduped_candidate_trust_benchmark_330e.py
tests/trust/test_deduped_candidate_benchmark_330e.py
```

Possible precise updates if needed:

```text
datefac/trust/__init__.py
datefac/trust/cached_candidate_benchmark_330c.py
datefac/trust/routing_policy_calibration_330d.py
```

Do not edit production pipeline modules.

## Inputs

Primary benchmark input:

```text
D:\_datefac\output\cached_candidate_trust_scoring_330c
```

Calibration reference:

```text
D:\_datefac\output\routing_policy_calibration_330d
```

Scoring reference:

```text
D:\_datefac\output\trust_engine_scoring_330b
```

Optional calibration workbook:

```text
D:\_datefac\output\routing_policy_calibration_330d\routing_policy_calibration_330d_samples.xlsx
```

Official assets may be read only for hash/no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Deduplication requirements

330E must explicitly define benchmark units:

```text
artifact_row: one scored row loaded from a cache artifact
candidate_fingerprint: deterministic best-effort identity over candidate content
source_candidate_id: only if available; current expected coverage may be 0
```

Deduplication should compute at least these keys:

1. `strict_candidate_key`
   - Prefer stable `candidate_id` / `source_candidate_id` if present.
   - If unavailable, use source artifact + row id.

2. `content_fingerprint_key`
   - Hash normalized fields such as:

```text
metric_label_raw
normalized_metric
value
unit
year
parser_sources
evidence_refs/page/table/row_text/provenance
existing_status
```

3. `cross_artifact_fingerprint_key`
   - Similar to content fingerprint, but excludes artifact filename when safe, so jsonl/xlsx duplicate rows can collapse.

330E should produce both:

```text
strict_deduped_view
cross_artifact_deduped_view
```

If fields are insufficient for reliable deduplication, report reliability warnings instead of pretending certainty.

## Required behavior

1. Validate 330D readiness:

```text
decision = TRUST_ENGINE_ROUTING_POLICY_CALIBRATION_330D_READY_WITH_WARNINGS
qa_fail_count = 0
scored_record_count = 12076
artifact_row_benchmark = true
deduped_candidate_benchmark = false
production_routing_modified = false
official_assets_modified = false
```

2. Load 330C scored records, preferably:

```text
D:\_datefac\output\cached_candidate_trust_scoring_330c\cached_candidate_trust_scoring_330c_scored_records.jsonl
```

3. Build strict and cross-artifact deduped views.
4. Recompute distributions for each view:

```text
confidence_level_distribution
routing_decision_distribution
risk_flag_distribution
score_bucket_distribution
source_artifact_distribution
potential_false_trusted_count
trusted_with_warning_risk_count
trusted_with_low_evidence_count
missing_evidence_count
```

5. Compare artifact-row vs strict-deduped vs cross-artifact-deduped:

```text
artifact_row_count
strict_deduped_candidate_count
cross_artifact_deduped_candidate_count
strict_duplicate_count
cross_artifact_duplicate_count
potential_false_trusted_delta
trusted_count_delta
review_required_count_delta
target_metric_ambiguous_delta
```

6. Assess dedup reliability:

```text
source_candidate_id_coverage_count
source_candidate_id_coverage_rate
candidate_id_coverage_count
candidate_id_coverage_rate
content_fingerprint_coverage_rate
dedup_reliability_level = HIGH | MEDIUM | LOW
```

7. Generate calibration samples for duplicates and potential false trusted rows:

```text
deduped_candidate_trust_benchmark_330e_samples.xlsx
```

8. Propose whether 330D calibration policy should be trusted for next stage:

```text
policy_calibration_safe_to_continue = true/false
recommended_next_step = 330F_UNFAMILIAR_PDF_TRUST_BENCHMARK or 330D2_STRONGER_CANDIDATE_ID_EXTRACTION
```

9. Confirm official assets are not modified.
10. Generate QA, no-apply proof, summary, deduped records, comparison artifacts, and report.

## Output directory

```text
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
```

Suggested outputs:

```text
deduped_candidate_trust_benchmark_330e_summary.json
deduped_candidate_trust_benchmark_330e_qa.json
deduped_candidate_trust_benchmark_330e_artifact_vs_deduped_comparison.json
deduped_candidate_trust_benchmark_330e_strict_deduped_records.jsonl
deduped_candidate_trust_benchmark_330e_cross_artifact_deduped_records.jsonl
deduped_candidate_trust_benchmark_330e_samples.xlsx
deduped_candidate_trust_benchmark_330e_no_apply_proof.json
deduped_candidate_trust_benchmark_330e_report.md
```

## Expected summary fields

Data-dependent values are allowed, but these fields must exist:

```text
validated_330d_calibration = true
artifact_row_count = 12076
strict_deduped_candidate_count >= 0
cross_artifact_deduped_candidate_count >= 0
strict_duplicate_count >= 0
cross_artifact_duplicate_count >= 0
source_candidate_id_coverage_rate >= 0
candidate_id_coverage_rate >= 0
content_fingerprint_coverage_rate >= 0
dedup_reliability_level exists
artifact_row_benchmark_retained = true
strict_deduped_benchmark_generated = true
cross_artifact_deduped_benchmark_generated = true
policy_calibration_safe_to_continue exists
no_official_asset_modification_during_330e = true
qa_fail_count = 0
```

Recommended decision if deduped benchmark is generated but reliability remains limited:

```text
TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_WITH_WARNINGS
```

Decision if dedup reliability is strong enough for next stage:

```text
TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_FOR_330F_UNFAMILIAR_PDF_TRUST_BENCHMARK
```

Decision if blocking QA fails:

```text
TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_NOT_READY
```

## Suggested command

```bash
python tools/run_deduped_candidate_trust_benchmark_330e.py \
  --cached-candidate-benchmark-dir D:\_datefac\output\cached_candidate_trust_scoring_330c \
  --routing-policy-calibration-dir D:\_datefac\output\routing_policy_calibration_330d \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --output-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e
```

## Compile checks

```bash
python -m py_compile datefac\trust\deduped_candidate_benchmark_330e.py datefac\trust\deduped_candidate_benchmark_330e_report.py tools\run_deduped_candidate_trust_benchmark_330e.py tests\trust\test_deduped_candidate_benchmark_330e.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/deduped_candidate_benchmark_330e.py
git add datefac/trust/deduped_candidate_benchmark_330e_report.py
git add tools/run_deduped_candidate_trust_benchmark_330e.py
git add tests/trust/test_deduped_candidate_benchmark_330e.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
git add datefac/trust/cached_candidate_benchmark_330c.py
git add datefac/trust/routing_policy_calibration_330d.py
```

Commit:

```text
Add 330E deduped candidate trust benchmark
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330D validation result.
5. Artifact-row vs strict/cross-artifact deduped counts.
6. Duplicate counts and coverage rates.
7. Distribution deltas.
8. Potential false trusted deltas.
9. Dedup reliability level.
10. Policy calibration continuation recommendation.
11. Calibration workbook path.
12. Official asset modification confirmation.
13. QA fail count.
14. Decision.
15. Git status result.
16. Commit hash.
17. Push result.
18. Residual risks.
