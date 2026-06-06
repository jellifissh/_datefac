# DateFac 330G Task
## End-to-End Delivery Quality Report for Unfamiliar Trust Benchmark

## Context

330F4 unfamiliar candidate export smoke is complete and pushed.

330F4 commit:

```text
8981e279cbd8316fc7e5afc3c90818c97ebc93af
```

330F4 result:

```text
selected_pdf_count = 3
selected_pdfs:
  - H3_AP202606061823322397_1.pdf
  - H3_AP202606051823305477_1.pdf
  - H3_AP202606051823305480_1.pdf
extraction/export approach = pdfplumber_table_blocks_plus_existing_row_text_candidate_extractors
prepared_candidate_row_count = 83
can_rerun_330f = true
qa_fail_count = 0
decision = UNFAMILIAR_CANDIDATE_EXPORT_SMOKE_330F4_READY_FOR_330F_RERUN
```

330F was rerun successfully using:

```text
D:\_datefac\output\unfamiliar_trust_split
```

330F rerun result:

```text
unfamiliar_source_status = loaded
unfamiliar_source_dir_count = 1
unfamiliar_candidate_artifact_row_count = 166
unfamiliar_strict_deduped_candidate_count = 83
scored_unfamiliar_record_count = 166
sidecar_trusted_suggestion_count = 153
sidecar_review_required_suggestion_count = 13
qa_fail_count = 0
decision = TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT
```

Known 330F4/330F residual risks:

```text
- 330F4 is a smoke export, not a full 13-PDF unfamiliar benchmark.
- Only 3 PDFs were processed.
- unit is missing for all 83 prepared rows.
- source_page is missing for all 83 prepared rows.
- 330F artifact row count is 166 but strict deduped count is 83, because jsonl/xlsx both exist and are both loaded.
- 330F source_pdf_distribution currently falls back to compatible artifact names rather than true PDF names.
```

330G should convert the successful unfamiliar smoke run into a delivery-oriented quality report.

## Goal

Implement 330G: End-to-End Delivery Quality Report.

330G must summarize the unfamiliar PDF Trust Engine smoke benchmark from a delivery/business-readiness perspective.

It should not claim production readiness. It should clearly distinguish:

```text
smoke benchmark over 3 PDFs
artifact-row scoring count = 166
strict deduped candidate count = 83
sidecar-only trust suggestions
not production routing
```

330G must produce a report that answers:

1. What was processed?
2. What candidate rows were generated?
3. How did Trust Engine score/rout them?
4. What can be trusted from this smoke result?
5. What cannot be claimed yet?
6. What is the next minimum step to move toward a real demo / delivery benchmark?

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify parser/extraction/delivery code behavior.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not call LLM or semantic adjudicator.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not rerun heavy parser.
- Do not change Trust Engine routing behavior.
- Do not start a new alias/scope/unit rule mining cycle.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 330G report/runner/test files.

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
datefac/trust/end_to_end_delivery_quality_report_330g.py
datefac/trust/end_to_end_delivery_quality_report_330g_report.py
tools/run_end_to_end_delivery_quality_report_330g.py
tests/trust/test_end_to_end_delivery_quality_report_330g.py
```

Possible precise updates only if needed:

```text
datefac/trust/__init__.py
```

Do not edit production pipeline modules.

## Inputs

Primary inputs:

```text
D:\_datefac\output\unfamiliar_candidate_export_smoke_330f4
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
D:\_datefac\output\unfamiliar_trust_split
```

References:

```text
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
D:\_datefac\output\routing_policy_calibration_330d
D:\_datefac\output\trust_engine_scoring_330b
```

Official assets may be read only for no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Required behavior

1. Validate 330F4 readiness:

```text
decision = UNFAMILIAR_CANDIDATE_EXPORT_SMOKE_330F4_READY_FOR_330F_RERUN
qa_fail_count = 0
selected_pdf_count = 3
prepared_candidate_row_count = 83
can_rerun_330f = true
no_official_asset_modification_during_330f4 = true
```

2. Validate 330F rerun readiness:

```text
decision = TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT
qa_fail_count = 0
unfamiliar_source_status = loaded
unfamiliar_candidate_artifact_row_count = 166
unfamiliar_strict_deduped_candidate_count = 83
scored_unfamiliar_record_count = 166
sidecar_trusted_suggestion_count = 153
sidecar_review_required_suggestion_count = 13
```

3. Load prepared candidate manifest/rows from:

```text
D:\_datefac\output\unfamiliar_trust_split
```

4. Load 330F summary/distribution/scored records where available.
5. Generate delivery-oriented metrics:

```text
processed_pdf_count
prepared_candidate_row_count
strict_deduped_candidate_count
artifact_row_count
artifact_duplication_factor
sidecar_trusted_suggestion_count
sidecar_review_required_suggestion_count
sidecar_auto_trusted_ratio_artifact_row
sidecar_auto_trusted_ratio_strict_deduped if computable
estimated_human_review_burden_count
unit_missing_count
source_page_missing_count
risk_flag_distribution
confidence_level_distribution
routing_decision_distribution
```

6. Explicitly record smoke limitations:

```text
not_full_13_pdf_benchmark
sidecar_only_not_production_routing
missing_unit_signal
missing_source_page_signal
source_pdf_distribution_fallback_issue
artifact_row_duplication_due_to_jsonl_xlsx
```

7. Generate a delivery readiness judgment:

Suggested categories:

```text
NOT_READY_FOR_CLIENT_DELIVERY
SMOKE_DEMO_READY_INTERNAL_ONLY
DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS
```

For the current result, expected judgment should be conservative, likely:

```text
SMOKE_DEMO_READY_INTERNAL_ONLY
```

Rationale:

```text
Trust Engine can score unfamiliar rows end-to-end on 3 PDFs.
But missing unit/source_page and small PDF sample prevent client delivery claims.
```

8. Recommend next stage:

Primary recommended next step:

```text
330H_FULL_13_PDF_UNFAMILIAR_EXPORT_AND_BENCHMARK
```

Secondary:

```text
330I_SOURCE_ATTRIBUTION_AND_UNIT_SIGNAL_FIX
```

9. Confirm official assets are not modified.
10. Generate QA, no-apply proof, summary, workbook, and markdown report.

## Output directory

```text
D:\_datefac\output\end_to_end_delivery_quality_report_330g
```

Suggested outputs:

```text
end_to_end_delivery_quality_report_330g_summary.json
end_to_end_delivery_quality_report_330g_qa.json
end_to_end_delivery_quality_report_330g_delivery_metrics.json
end_to_end_delivery_quality_report_330g_samples.xlsx
end_to_end_delivery_quality_report_330g_no_apply_proof.json
end_to_end_delivery_quality_report_330g_report.md
```

## Expected summary fields

```text
validated_330f4_smoke_export = true
validated_330f_unfamiliar_benchmark = true
processed_pdf_count = 3
prepared_candidate_row_count = 83
artifact_row_count = 166
strict_deduped_candidate_count = 83
artifact_duplication_factor = 2.0
sidecar_trusted_suggestion_count = 153
sidecar_review_required_suggestion_count = 13
unit_missing_count = 83
source_page_missing_count = 83
delivery_readiness_judgment = SMOKE_DEMO_READY_INTERNAL_ONLY
recommended_next_step = 330H_FULL_13_PDF_UNFAMILIAR_EXPORT_AND_BENCHMARK
no_official_asset_modification_during_330g = true
qa_fail_count = 0
```

Expected decision:

```text
END_TO_END_DELIVERY_QUALITY_REPORT_330G_READY_FOR_330H_FULL_UNFAMILIAR_BENCHMARK
```

If required inputs are missing:

```text
END_TO_END_DELIVERY_QUALITY_REPORT_330G_NOT_READY
```

## Suggested command

```bash
python tools/run_end_to_end_delivery_quality_report_330g.py \
  --unfamiliar-export-smoke-dir D:\_datefac\output\unfamiliar_candidate_export_smoke_330f4 \
  --unfamiliar-trust-benchmark-dir D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f \
  --prepared-unfamiliar-dir D:\_datefac\output\unfamiliar_trust_split \
  --output-dir D:\_datefac\output\end_to_end_delivery_quality_report_330g
```

## Compile checks

```bash
python -m py_compile datefac\trust\end_to_end_delivery_quality_report_330g.py datefac\trust\end_to_end_delivery_quality_report_330g_report.py tools\run_end_to_end_delivery_quality_report_330g.py tests\trust\test_end_to_end_delivery_quality_report_330g.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/end_to_end_delivery_quality_report_330g.py
git add datefac/trust/end_to_end_delivery_quality_report_330g_report.py
git add tools/run_end_to_end_delivery_quality_report_330g.py
git add tests/trust/test_end_to_end_delivery_quality_report_330g.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
```

Commit:

```text
Add 330G end-to-end delivery quality report
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330F4 and 330F validation result.
5. Processed PDF count and candidate counts.
6. Artifact row vs strict deduped counts.
7. Sidecar trusted/review distribution.
8. Missing unit/source page counts.
9. Delivery readiness judgment.
10. Recommended next step.
11. Official asset modification confirmation.
12. QA fail count.
13. Decision.
14. Git status result.
15. Commit hash.
16. Push result.
17. Residual risks.
