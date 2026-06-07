# DateFac 330L Task
## Client-Style Export Preview

## Context

330J2 delivery report refresh after 330K is complete and pushed.

330J2 commit:

```text
3fb063c4c414c52fbe484810de62453c22378fca
```

330J2 output:

```text
D:\_datefac\output\delivery_report_refresh_after_330k_330j2
```

330J2 result:

```text
validated_330k_unit_review = true
reran_330f = true
330f_unfamiliar_source_status = loaded
prepared_candidate_row_count = 117
artifact_row_count = 234
strict_deduped_candidate_count = 117
source_pdf_unique_count = 7
source_page_missing_count = 0
unit_missing_count = 18
unit_unknown_risk_count = 18
unit_conflict_risk_count = 12
sidecar_trusted_suggestion_count = 192
sidecar_review_required_suggestion_count = 42
unit_missing_delta_vs_330j = -36
unit_unknown_risk_delta_vs_330j = -36
unit_conflict_risk_delta_vs_330j = 0
trusted_suggestion_delta_vs_330j = 72
review_required_delta_vs_330j = -72
unit_review_required_count = 21
unit_conflict_review_count = 12
unit_unknown_review_count = 9
review_sample_row_count = 21
delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
recommended_next_step = 330K2_HUMAN_UNIT_REVIEW_OR_330L_CLIENT_STYLE_EXPORT_PREVIEW
no_official_asset_modification_during_330j2 = true
qa_fail_count = 0
decision = DELIVERY_REPORT_REFRESH_330J2_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_330L_EXPORT_PREVIEW
```

330L should produce a client-style export preview that shows DateFac's current value in a form a non-engineer can inspect. It must be clear that this is a demo preview with manual review caveats, not a production/client-ready delivery.

## Goal

Implement 330L: Client-Style Export Preview.

330L should package the current unfamiliar 13-PDF sidecar benchmark into a client-style Excel/report preview with:

1. A clean summary sheet.
2. Trusted suggestion sheet.
3. Review-required sheet.
4. Unit-risk review sheet.
5. Source/provenance sheet.
6. QA/caveats sheet.
7. Optional markdown report.

This is a preview artifact for demo/product inspection. It must not alter production routing or official assets.

## Recommended Codex reasoning level

```text
Medium
```

Use `Medium` because this is primarily export/report packaging, not parser work or trust-policy design. Use `High` only if row-level artifact compatibility issues block export generation.

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
- Do not overwrite 330I/330K prepared outputs or 330J2 outputs.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330L sidecar export/report/runner/test files.

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
datefac/trust/client_style_export_preview_330l.py
datefac/trust/client_style_export_preview_330l_report.py
tools/run_client_style_export_preview_330l.py
tests/trust/test_client_style_export_preview_330l.py
```

Possible precise updates only if needed:

```text
datefac/trust/__init__.py
```

Do not edit production pipeline modules.

## Inputs

Primary inputs:

```text
D:\_datefac\output\delivery_report_refresh_after_330k_330j2
D:\_datefac\output\unfamiliar_trust_split_330k
D:\_datefac\output\unit_signal_review_330k
```

References:

```text
D:\_datefac\output\delivery_report_refresh_330j
D:\_datefac\output\source_attribution_unit_signal_fix_330i
D:\_datefac\output\full_unfamiliar_export_benchmark_330h
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
D:\_datefac\output\trust_engine_scoring_330b
```

330F rerun output from 330J2 may exist:

```text
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j2
```

Official assets may be read only for no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Output directory

```text
D:\_datefac\output\client_style_export_preview_330l
```

Suggested outputs:

```text
client_style_export_preview_330l_summary.json
client_style_export_preview_330l_qa.json
client_style_export_preview_330l_preview.xlsx
client_style_export_preview_330l_report.md
client_style_export_preview_330l_no_apply_proof.json
client_style_export_preview_330l_manifest.json
```

## Required behavior

1. Validate 330J2 readiness:

```text
decision = DELIVERY_REPORT_REFRESH_330J2_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_330L_EXPORT_PREVIEW
qa_fail_count = 0
prepared_candidate_row_count = 117
strict_deduped_candidate_count = 117
source_page_missing_count = 0
unit_missing_count = 18
unit_unknown_risk_count = 18
unit_conflict_risk_count = 12
sidecar_trusted_suggestion_count = 192
sidecar_review_required_suggestion_count = 42
delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
no_official_asset_modification_during_330j2 = true
```

2. Load 330K fixed prepared rows from:

```text
D:\_datefac\output\unfamiliar_trust_split_330k
```

3. Load 330J2 delivery metrics and, if available, 330F scored records from:

```text
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j2
```

4. Produce a client-style Excel preview workbook with sheets:

### `00_README`

Must include:

```text
DateFac client-style export preview
Demo readiness: DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
Scope: 13 unfamiliar PDFs, 7 with candidates
Candidate rows: 117
This is sidecar trust scoring, not production routing
Not client-ready; manual unit review caveats remain
```

### `01_EXEC_SUMMARY`

Include key metrics:

```text
source_pdf_unique_count
prepared_candidate_row_count
strict_deduped_candidate_count
sidecar_trusted_suggestion_count
sidecar_review_required_suggestion_count
unit_missing_count
unit_unknown_risk_count
unit_conflict_risk_count
source_page_missing_count
delivery_readiness_judgment
recommended_next_step
```

### `02_TRUSTED_SUGGESTIONS`

Rows suggested as trusted by sidecar if scored records are available. If row-level sidecar routing cannot be joined exactly, include best-effort candidate rows and clearly mark `routing_join_status`.

Required columns where available:

```text
candidate_id
source_pdf
source_page
metric_label_raw
normalized_metric
value
unit
year
confidence_score
confidence_level
routing_decision
risk_flags
evidence_refs
row_text
```

### `03_REVIEW_REQUIRED`

Rows requiring review, especially unit-risk rows.

### `04_UNIT_REVIEW_SAMPLE`

Load or reproduce the 330K human review sample. Include human decision columns:

```text
human_unit_decision
human_unit_value
human_notes
```

Allowed decisions:

```text
CONFIRM_UNIT
REJECT_UNIT
KEEP_UNIT_UNKNOWN
NEEDS_MORE_CONTEXT
```

### `05_SOURCE_PROVENANCE`

Group by PDF and page:

```text
source_pdf
source_page
candidate_count
trusted_suggestion_count
review_required_count
unit_risk_count
```

### `06_QA_CAVEATS`

Must explicitly include:

```text
sidecar_only_not_production_routing
not_client_ready
unit_review_remaining
unit_conflict_remaining
artifact_row_vs_candidate_row_difference
only_7_of_13_pdfs_produced_candidates
no_official_assets_modified
```

5. Produce a markdown report summarizing the preview.

6. Compute export metrics:

```text
preview_workbook_generated
trusted_sheet_row_count
review_required_sheet_row_count
unit_review_sheet_row_count
source_provenance_sheet_row_count
qa_caveat_count
```

7. Use conservative wording. Do not claim production readiness or paid-client readiness.

8. Recommended next step:

If preview workbook is generated:

```text
recommended_next_step = 330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING
```

Secondary:

```text
331A_DEMO_PACKAGING
```

9. Confirm official assets are not modified.
10. Generate QA, no-apply proof, summary, workbook, and markdown report.

## Expected summary fields

Data-dependent values are allowed, but these fields must exist:

```text
validated_330j2_delivery_refresh = true
preview_workbook_generated = true
source_pdf_unique_count = 7
prepared_candidate_row_count = 117
strict_deduped_candidate_count = 117
unit_missing_count = 18
unit_conflict_risk_count = 12
delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
trusted_sheet_row_count >= 0
review_required_sheet_row_count >= 0
unit_review_sheet_row_count >= 21
qa_caveat_count >= 1
no_official_asset_modification_during_330l = true
qa_fail_count = 0
```

Expected decision:

```text
CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING
```

If blocking QA fails:

```text
CLIENT_STYLE_EXPORT_PREVIEW_330L_NOT_READY
```

## Suggested command

```bash
python tools/run_client_style_export_preview_330l.py \
  --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 \
  --fixed-prepared-dir D:\_datefac\output\unfamiliar_trust_split_330k \
  --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k \
  --output-dir D:\_datefac\output\client_style_export_preview_330l
```

## Compile checks

```bash
python -m py_compile datefac\trust\client_style_export_preview_330l.py datefac\trust\client_style_export_preview_330l_report.py tools\run_client_style_export_preview_330l.py tests\trust\test_client_style_export_preview_330l.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/client_style_export_preview_330l.py
git add datefac/trust/client_style_export_preview_330l_report.py
git add tools/run_client_style_export_preview_330l.py
git add tests/trust/test_client_style_export_preview_330l.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
```

Commit:

```text
Add 330L client-style export preview
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330J2 validation result.
5. Preview workbook path.
6. Sheet names and row counts.
7. Trusted/review/unit-review counts.
8. Delivery readiness wording.
9. Recommended next step.
10. Official asset modification confirmation.
11. QA fail count.
12. Decision.
13. Git status result.
14. Commit hash.
15. Push result.
16. Residual risks.
