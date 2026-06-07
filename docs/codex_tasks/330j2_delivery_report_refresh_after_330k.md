# DateFac 330J2 Task
## Delivery Report Refresh After 330K Unit Signal Review

## Context

330K unit signal review is complete and pushed.

330K commit:

```text
c1ce7eada85c485f0d92192ab6c5a089a28e5188
```

330K output:

```text
D:\_datefac\output\unit_signal_review_330k
```

330K optional fixed prepared output:

```text
D:\_datefac\output\unfamiliar_trust_split_330k
```

330K result:

```text
validated_330j_delivery_refresh = true
input_candidate_row_count = 117
unit_missing_count_input = 54
unit_conflict_count_input = 12
unit_status_distribution = {
  "unit_inferred_high_confidence": 55,
  "unit_present": 41,
  "unit_conflict": 12,
  "unit_missing_with_unit_unknown": 9
}

unit_missing_category_distribution:
  COUNT_OR_VOLUME_LIKE_METRIC = 10
  PER_SHARE_LIKE_METRIC_WITH_NO_UNIT_MARKER = 7
  PERCENT_LIKE_METRIC_WITH_NO_PERCENT_MARKER = 3
  MONEY_LIKE_METRIC_WITH_NO_TABLE_UNIT_CONTEXT = 1

additional_safe_unit_fix_count = 36
unit_missing_count_after_330k = 18
review_sample_row_count = 21
human_review_workbook_generated = true
unit_review_required_count = 21
unit_conflict_review_count = 12
unit_unknown_review_count = 9
high_confidence_with_unit_risk_count = 0
pdfs_affected_by_unit_risk_count = 4
recommended_next_step = 330J2_DELIVERY_REPORT_REFRESH_AFTER_330K
secondary_next_step = 330L_CLIENT_STYLE_EXPORT_PREVIEW
no_official_asset_modification_during_330k = true
qa_fail_count = 0
decision = UNIT_SIGNAL_REVIEW_330K_READY_FOR_330J2_DELIVERY_REFRESH
```

Key 330K improvement:

```text
unit_missing_count: 54 -> 18
additional_safe_unit_fix_count = 36
```

330K deliberately did not guess unsafe units:

```text
- 18 rows still need human unit review.
- 12 UNIT_CONFLICT rows, mainly EPS vs table-level monetary unit conflicts, remain review-required.
- 330K only used existing 330I/330J row context and did not reopen PDFs.
```

330J2 should refresh the delivery quality report after 330K and determine whether the demo can move toward client-style export preview or needs human unit review first.

## Goal

Implement 330J2: Delivery Report Refresh After 330K.

330J2 should rerun or load 330F over the 330K fixed prepared rows, compare delivery metrics against 330J and 330K, and produce a refreshed delivery readiness judgment.

330J2 must remain sidecar-only. It must not change production routing, parser/extraction/delivery behavior, official assets, or previous cached outputs.

## Recommended Codex reasoning level

```text
Medium
```

Use `Medium` because this is primarily report refresh, rerun orchestration, and comparison. Use `High` only if 330F compatibility loading or artifact-row/candidate-row metrics become inconsistent.

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify parser/extraction/delivery behavior.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not call LLM or semantic adjudicator.
- Do not start a new alias/scope/unit official rule mining cycle.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not install dependencies or download models.
- Do not reopen PDFs.
- Do not overwrite 330I or 330K prepared outputs.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330J2 sidecar report/runner/test files.

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
datefac/trust/delivery_report_refresh_after_330k_330j2.py
datefac/trust/delivery_report_refresh_after_330k_330j2_report.py
tools/run_delivery_report_refresh_after_330k_330j2.py
tests/trust/test_delivery_report_refresh_after_330k_330j2.py
```

Possible precise updates only if needed:

```text
datefac/trust/__init__.py
```

Do not edit production pipeline modules.

## Inputs

Primary inputs:

```text
D:\_datefac\output\unit_signal_review_330k
D:\_datefac\output\unfamiliar_trust_split_330k
```

References:

```text
D:\_datefac\output\delivery_report_refresh_330j
D:\_datefac\output\source_attribution_unit_signal_fix_330i
D:\_datefac\output\unfamiliar_trust_split_330i
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
D:\_datefac\output\trust_engine_scoring_330b
```

Official assets may be read only for no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Output directory

```text
D:\_datefac\output\delivery_report_refresh_after_330k_330j2
```

Suggested outputs:

```text
delivery_report_refresh_after_330k_330j2_summary.json
delivery_report_refresh_after_330k_330j2_qa.json
delivery_report_refresh_after_330k_330j2_delivery_metrics.json
delivery_report_refresh_after_330k_330j2_comparison.json
delivery_report_refresh_after_330k_330j2_samples.xlsx
delivery_report_refresh_after_330k_330j2_no_apply_proof.json
delivery_report_refresh_after_330k_330j2_report.md
```

Preferred 330F rerun output:

```text
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j2
```

## Required behavior

1. Validate 330K readiness:

```text
decision = UNIT_SIGNAL_REVIEW_330K_READY_FOR_330J2_DELIVERY_REFRESH
qa_fail_count = 0
input_candidate_row_count = 117
unit_missing_count_input = 54
additional_safe_unit_fix_count = 36
unit_missing_count_after_330k = 18
review_sample_row_count = 21
human_review_workbook_generated = true
no_official_asset_modification_during_330k = true
```

2. Validate 330K fixed prepared output exists if fixes were applied:

```text
D:\_datefac\output\unfamiliar_trust_split_330k\unfamiliar_candidate_rows.jsonl
D:\_datefac\output\unfamiliar_trust_split_330k\unfamiliar_candidate_rows.xlsx
D:\_datefac\output\unfamiliar_trust_split_330k\unfamiliar_candidate_manifest.json
```

If fixed prepared rows do not exist, fail with a clear not-ready decision.

3. Rerun 330F using the 330K fixed prepared rows:

```bash
python tools\run_unfamiliar_pdf_trust_benchmark_330f.py \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --unfamiliar-source-dir D:\_datefac\output\unfamiliar_trust_split_330k \
  --output-dir D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j2
```

4. Load rerun 330F summary/distribution/scored records where available.

5. Generate refreshed delivery metrics:

```text
prepared_candidate_row_count
artifact_row_count
strict_deduped_candidate_count
source_pdf_unique_count
source_page_missing_count
unit_missing_count
unit_unknown_risk_count
unit_conflict_risk_count
sidecar_trusted_suggestion_count
sidecar_review_required_suggestion_count
sidecar_auto_trusted_ratio_artifact_row
confidence_level_distribution
routing_decision_distribution
risk_flag_distribution
```

6. Compare against 330J baseline:

```text
unit_missing_delta_vs_330j
unit_unknown_risk_delta_vs_330j
unit_conflict_risk_delta_vs_330j
trusted_suggestion_delta_vs_330j
review_required_delta_vs_330j
confidence_level_delta_vs_330j
routing_decision_delta_vs_330j
```

330J baseline:

```text
unit_missing_count = 54
unit_unknown_risk_count = 54
unit_conflict_risk_count = 12
sidecar_trusted_suggestion_count = 120
sidecar_review_required_suggestion_count = 114
confidence_level_distribution = {"HIGH": 120, "MEDIUM": 96, "LOW": 18}
routing_decision_distribution = {"TRUSTED": 120, "REVIEW_REQUIRED": 114}
risk_flag_distribution = {"UNIT_UNKNOWN": 108, "UNIT_CONFLICT": 24, "LABEL_AMBIGUOUS": 16}
```

7. Compare against 330K unit review:

```text
unit_missing_count_after_330k = 18
unit_review_required_count = 21
unit_conflict_review_count = 12
unit_unknown_review_count = 9
review_sample_row_count = 21
```

8. Delivery readiness judgment:

Do not claim client-ready.

Suggested logic:

```text
If 330F rerun succeeds, source_page_missing_count = 0, and unit_missing_count <= 18:
  delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
else:
  delivery_readiness_judgment = DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS
```

9. Recommended next step:

If remaining unit review burden is small and review workbook exists:

```text
recommended_next_step = 330K2_HUMAN_UNIT_REVIEW_OR_330L_CLIENT_STYLE_EXPORT_PREVIEW
```

Secondary:

```text
330L_CLIENT_STYLE_EXPORT_PREVIEW
```

If 330F rerun fails:

```text
recommended_next_step = 330J2_FIX_330F_COMPATIBILITY_RERUN
```

10. Confirm official assets are not modified.
11. Generate QA, no-apply proof, summary, workbook, comparison JSON, and markdown report.

## Expected summary fields

Data-dependent values are allowed, but these fields must exist:

```text
validated_330k_unit_review = true
reran_330f = true
330f_unfamiliar_source_status = loaded
prepared_candidate_row_count = 117
source_page_missing_count = 0
unit_missing_count <= 18
unit_missing_delta_vs_330j <= -36
sidecar_trusted_suggestion_count >= 0
sidecar_review_required_suggestion_count >= 0
delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
recommended_next_step = 330K2_HUMAN_UNIT_REVIEW_OR_330L_CLIENT_STYLE_EXPORT_PREVIEW
no_official_asset_modification_during_330j2 = true
qa_fail_count = 0
```

Expected decision if rerun succeeds:

```text
DELIVERY_REPORT_REFRESH_330J2_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_330L_EXPORT_PREVIEW
```

If blocking QA fails:

```text
DELIVERY_REPORT_REFRESH_330J2_NOT_READY
```

## Suggested command

```bash
python tools/run_delivery_report_refresh_after_330k_330j2.py \
  --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k \
  --fixed-prepared-dir D:\_datefac\output\unfamiliar_trust_split_330k \
  --previous-delivery-report-dir D:\_datefac\output\delivery_report_refresh_330j \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --rerun-330f \
  --output-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2
```

## Compile checks

```bash
python -m py_compile datefac\trust\delivery_report_refresh_after_330k_330j2.py datefac\trust\delivery_report_refresh_after_330k_330j2_report.py tools\run_delivery_report_refresh_after_330k_330j2.py tests\trust\test_delivery_report_refresh_after_330k_330j2.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/delivery_report_refresh_after_330k_330j2.py
git add datefac/trust/delivery_report_refresh_after_330k_330j2_report.py
git add tools/run_delivery_report_refresh_after_330k_330j2.py
git add tests/trust/test_delivery_report_refresh_after_330k_330j2.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
```

Commit:

```text
Add 330J2 delivery report refresh after 330K
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330K validation result.
5. 330F rerun result.
6. Refreshed delivery metrics.
7. Comparison against 330J baseline.
8. Comparison against 330K unit review.
9. Delivery readiness judgment.
10. Recommended next step.
11. Official asset modification confirmation.
12. QA fail count.
13. Decision.
14. Git status result.
15. Commit hash.
16. Push result.
17. Residual risks.
