# DateFac 330H Task
## Full 13-PDF Unfamiliar Export and Benchmark

## Context

330G end-to-end delivery quality report is complete and pushed.

330G commit:

```text
4b7b1bbde11bc4bc95d2e176294e0e22858eb455
```

330G output:

```text
D:\_datefac\output\end_to_end_delivery_quality_report_330g
```

330G result:

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
official assets modified = false
qa_fail_count = 0
decision = END_TO_END_DELIVERY_QUALITY_REPORT_330G_READY_FOR_330H_FULL_UNFAMILIAR_BENCHMARK
```

Known residual risks from 330G:

```text
- Smoke scope covered only 3 PDFs, not all 13 unfamiliar PDFs.
- unit is missing for all 83 prepared rows.
- source_page is missing for all 83 prepared rows.
- 330F compatibility loading duplicates artifact rows across JSONL/XLSX.
- 330F source_pdf_distribution falls back to artifact name instead of true PDF names.
```

330H should expand from the 3-PDF smoke benchmark to all 13 unfamiliar PDFs while keeping the workflow sidecar-only.

## Goal

Implement 330H: Full 13-PDF Unfamiliar Export and Benchmark.

330H should process all 13 PDFs under:

```text
D:\_datefac\input\unfamiliar
```

It should generate 330F-consumable candidate rows for all 13 PDFs, rerun or enable rerun of 330F, and produce a full 13-PDF unfamiliar benchmark summary.

330H must remain sidecar-only. It must not modify production routing, parser/extraction/delivery behavior, official assets, or existing dirty files.

## Recommended Codex reasoning level

```text
High
```

Use `High` because 330H expands from 3 PDFs to 13 PDFs and touches the boundary between local extraction utilities and Trust Engine sidecar benchmark. Use `Ultra/Very High` only if parser/runtime debugging becomes necessary.

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify existing parser/extraction/delivery behavior unless only adding a new sidecar wrapper/export utility.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not call LLM or semantic adjudicator.
- Do not start a new alias/scope/unit rule mining cycle.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM unless explicitly expanded later.
- Prefer the same lightweight pdfplumber + existing row-text candidate extractor path used by 330F4.
- Do not install dependencies or download models.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330H sidecar export/benchmark source/report/runner/test files.

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
datefac/trust/full_unfamiliar_export_benchmark_330h.py
datefac/trust/full_unfamiliar_export_benchmark_330h_report.py
tools/run_full_unfamiliar_export_benchmark_330h.py
tests/trust/test_full_unfamiliar_export_benchmark_330h.py
```

Possible precise updates only if needed:

```text
datefac/trust/__init__.py
datefac/trust/unfamiliar_candidate_export_smoke_330f4.py
```

Do not edit production pipeline modules.

## Inputs

Primary unfamiliar input directory:

```text
D:\_datefac\input\unfamiliar
```

Previous outputs:

```text
D:\_datefac\output\end_to_end_delivery_quality_report_330g
D:\_datefac\output\unfamiliar_candidate_export_smoke_330f4
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
D:\_datefac\output\unfamiliar_trust_split
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
D:\_datefac\output\trust_engine_scoring_330b
```

Official assets may be read only for no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Output directories

Runner/report output:

```text
D:\_datefac\output\full_unfamiliar_export_benchmark_330h
```

Prepared 13-PDF candidate source for 330F rerun:

```text
D:\_datefac\output\unfamiliar_trust_split_330h
```

Do not overwrite the 330F4 smoke output directory unless explicitly backing it up and reporting it. Prefer a new 330H-specific prepared directory.

Suggested prepared outputs:

```text
D:\_datefac\output\unfamiliar_trust_split_330h\unfamiliar_candidate_rows.jsonl
D:\_datefac\output\unfamiliar_trust_split_330h\unfamiliar_candidate_rows.xlsx
D:\_datefac\output\unfamiliar_trust_split_330h\unfamiliar_candidate_manifest.json
```

Suggested 330H outputs:

```text
full_unfamiliar_export_benchmark_330h_summary.json
full_unfamiliar_export_benchmark_330h_qa.json
full_unfamiliar_export_benchmark_330h_manifest.json
full_unfamiliar_export_benchmark_330h_pdf_summary.xlsx
full_unfamiliar_export_benchmark_330h_no_apply_proof.json
full_unfamiliar_export_benchmark_330h_report.md
```

## Required behavior

1. Validate 330G readiness:

```text
decision = END_TO_END_DELIVERY_QUALITY_REPORT_330G_READY_FOR_330H_FULL_UNFAMILIAR_BENCHMARK
qa_fail_count = 0
processed_pdf_count = 3
prepared_candidate_row_count = 83
strict_deduped_candidate_count = 83
delivery_readiness_judgment = SMOKE_DEMO_READY_INTERNAL_ONLY
recommended_next_step = 330H_FULL_13_PDF_UNFAMILIAR_EXPORT_AND_BENCHMARK
```

2. Discover all PDFs under `D:\_datefac\input\unfamiliar` and require:

```text
unfamiliar_pdf_count = 13
```

3. Reuse the 330F4 lightweight extraction/export approach where possible:

```text
pdfplumber_table_blocks_plus_existing_row_text_candidate_extractors
```

Specifically prefer existing functions used by 330F4:

```text
extract_pdfplumber_table_blocks
clean_row_texts
repair_row_fragments
extract_metric_candidates_from_repaired_rows
```

4. Process all 13 PDFs best-effort.
5. For each PDF, record:

```text
source_pdf
processed / failed / no_candidates
candidate_row_count
error_message if any
```

6. Write 330F-compatible rows with required fields:

```text
candidate_id
metric_label_raw
normalized_metric
value
unit
year
parser_sources
evidence_refs
risk_flags
existing_status
source_pdf
source_artifact
source_page
row_text
table_id
```

7. Candidate IDs must be deterministic and stable.
8. Preserve true source PDF names in every row.
9. Try to improve source attribution from 330F4:
   - If page number is available from pdfplumber extraction, set `source_page`.
   - If unavailable, leave blank and count missing.
   - Do not fabricate page numbers.
10. Try to improve unit signal:
   - If unit is present in row/table context, populate `unit`.
   - If unavailable, leave blank and count missing.
   - Do not fabricate units.
11. Generate per-PDF summary and aggregate missing-field counts.
12. If candidate rows are generated, optionally rerun 330F against the new prepared directory and record the 330F rerun summary if successful.
13. If 330F rerun is not performed by 330H, emit the exact rerun command.
14. Confirm official assets are not modified.
15. Generate QA, no-apply proof, manifest, workbook, and markdown report.

## Expected successful result

Data-dependent counts are allowed, but expected fields must exist:

```text
validated_330g_delivery_report = true
unfamiliar_pdf_count = 13
processed_pdf_count >= 3
failed_pdf_count >= 0
pdf_with_candidate_count >= 1
prepared_candidate_row_count > 0
prepared_output_dir = D:\_datefac\output\unfamiliar_trust_split_330h
can_rerun_330f = true
source_pdf_preserved = true
missing_required_field_count_by_field exists
no_official_asset_modification_during_330h = true
qa_fail_count = 0
```

If 330F is rerun inside 330H and succeeds:

```text
reran_330f = true
330f_unfamiliar_source_status = loaded
330f_scored_unfamiliar_record_count > 0
330f_decision = TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT
```

Expected decision if rows are prepared successfully:

```text
FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_READY_FOR_330F_RERUN_OR_330I_SOURCE_ATTRIBUTION_UNIT_FIX
```

If rows are prepared and 330F rerun succeeds:

```text
FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_READY_FOR_330I_SOURCE_ATTRIBUTION_UNIT_FIX
```

If no rows are produced:

```text
FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_WAITING_FOR_SAFE_EXPORT_PATH
```

If blocking QA fails:

```text
FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_NOT_READY
```

## Suggested command

```bash
python tools/run_full_unfamiliar_export_benchmark_330h.py \
  --unfamiliar-input-dir D:\_datefac\input\unfamiliar \
  --previous-delivery-report-dir D:\_datefac\output\end_to_end_delivery_quality_report_330g \
  --prepared-output-dir D:\_datefac\output\unfamiliar_trust_split_330h \
  --output-dir D:\_datefac\output\full_unfamiliar_export_benchmark_330h
```

If implementing optional 330F rerun inside the runner, expose:

```bash
  --rerun-330f \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b
```

## 330F rerun command after 330H

```bash
python tools\run_unfamiliar_pdf_trust_benchmark_330f.py \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --unfamiliar-source-dir D:\_datefac\output\unfamiliar_trust_split_330h \
  --output-dir D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330h
```

## Compile checks

```bash
python -m py_compile datefac\trust\full_unfamiliar_export_benchmark_330h.py datefac\trust\full_unfamiliar_export_benchmark_330h_report.py tools\run_full_unfamiliar_export_benchmark_330h.py tests\trust\test_full_unfamiliar_export_benchmark_330h.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/full_unfamiliar_export_benchmark_330h.py
git add datefac/trust/full_unfamiliar_export_benchmark_330h_report.py
git add tools/run_full_unfamiliar_export_benchmark_330h.py
git add tests/trust/test_full_unfamiliar_export_benchmark_330h.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
git add datefac/trust/unfamiliar_candidate_export_smoke_330f4.py
```

Commit:

```text
Add 330H full unfamiliar export benchmark
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. Unfamiliar PDF count and selected/full file list summary.
5. Processed / failed / no-candidate PDF counts.
6. Prepared output directory.
7. Prepared candidate row count.
8. Missing unit/source_page and other field counts.
9. Whether true source PDF names are preserved.
10. Whether 330F was rerun, and rerun result if yes.
11. Recommended next step.
12. Official asset modification confirmation.
13. QA fail count.
14. Decision.
15. Git status result.
16. Commit hash.
17. Push result.
18. Residual risks.
