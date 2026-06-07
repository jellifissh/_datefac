# DateFac 330I Task
## Source Attribution and Unit Signal Fix

## Context

330H full 13-PDF unfamiliar export and benchmark is complete and pushed.

330H commit:

```text
ae2d59d4a7ec6963c9e15fd5c1836e9ef22935d7
```

330H output directories:

```text
D:\_datefac\output\full_unfamiliar_export_benchmark_330h
D:\_datefac\output\unfamiliar_trust_split_330h
```

330H result:

```text
unfamiliar_pdf_count = 13
processed_pdf_count = 13
failed_pdf_count = 0
no_candidate_pdf_count = 6
pdf_with_candidate_count = 7
prepared_candidate_row_count = 117
prepared_output_dir = D:\_datefac\output\unfamiliar_trust_split_330h
source_pdf_preserved = true
missing unit count = 64
missing source_page count = 0
reran_330f = true
330f_unfamiliar_source_status = loaded
330f_scored_unfamiliar_record_count = 234
330f_decision = TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT
no_official_asset_modification_during_330h = true
qa_fail_count = 0
decision = FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_READY_FOR_330I_SOURCE_ATTRIBUTION_UNIT_FIX
```

330H improved source-page attribution compared with the 330G smoke report:

```text
source_page missing count: 83 -> 0
```

But unit signal is still weak:

```text
unit missing count = 64 / 117
```

330I should focus on source attribution hygiene and unit signal improvement for the 13-PDF unfamiliar benchmark, without changing production behavior.

## Goal

Implement 330I: Source Attribution and Unit Signal Fix.

330I should take the 330H unfamiliar candidate rows and produce an improved sidecar candidate dataset with:

1. True source PDF names preserved.
2. Source page presence verified.
3. Artifact duplication controlled for downstream 330F reruns.
4. Unit signal improved where safely inferable from row/table context.
5. Missing unit cases explicitly categorized.

330I must remain sidecar-only. It must not modify production pipeline behavior, official assets, or previous cached outputs.

## Recommended Codex reasoning level

```text
High
```

Use `High` because this task improves evidence attribution and unit inference, both of which directly affect Trust Engine confidence scoring. Use `Ultra/Very High` only if debugging malformed PDF/table extraction outputs becomes necessary.

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify existing parser/extraction/delivery behavior unless only adding a new sidecar normalization/fix utility.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not call LLM or semantic adjudicator.
- Do not start a new alias/scope/unit rule mining cycle.
- Do not run MinerU / StructEqTable / Docling / PPStructure / VLM.
- Do not install dependencies or download models.
- Do not fabricate units or page numbers.
- Do not overwrite the 330H prepared output directory. Write to a new 330I output/prepared directory.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330I sidecar source/report/runner/test files.

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
datefac/trust/source_attribution_unit_signal_fix_330i.py
datefac/trust/source_attribution_unit_signal_fix_330i_report.py
tools/run_source_attribution_unit_signal_fix_330i.py
tests/trust/test_source_attribution_unit_signal_fix_330i.py
```

Possible precise updates only if needed:

```text
datefac/trust/__init__.py
datefac/trust/full_unfamiliar_export_benchmark_330h.py
```

Do not edit production pipeline modules.

## Inputs

Primary inputs:

```text
D:\_datefac\output\full_unfamiliar_export_benchmark_330h
D:\_datefac\output\unfamiliar_trust_split_330h
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330h
```

Fallback 330F rerun output may be:

```text
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
```

Official assets may be read only for no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Output directories

Runner/report output:

```text
D:\_datefac\output\source_attribution_unit_signal_fix_330i
```

Prepared fixed source for optional 330F rerun:

```text
D:\_datefac\output\unfamiliar_trust_split_330i
```

Suggested prepared outputs:

```text
D:\_datefac\output\unfamiliar_trust_split_330i\unfamiliar_candidate_rows.jsonl
D:\_datefac\output\unfamiliar_trust_split_330i\unfamiliar_candidate_rows.xlsx
D:\_datefac\output\unfamiliar_trust_split_330i\unfamiliar_candidate_manifest.json
```

Suggested 330I outputs:

```text
source_attribution_unit_signal_fix_330i_summary.json
source_attribution_unit_signal_fix_330i_qa.json
source_attribution_unit_signal_fix_330i_manifest.json
source_attribution_unit_signal_fix_330i_unit_fix_report.xlsx
source_attribution_unit_signal_fix_330i_no_apply_proof.json
source_attribution_unit_signal_fix_330i_report.md
```

## Required behavior

1. Validate 330H readiness:

```text
decision = FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_READY_FOR_330I_SOURCE_ATTRIBUTION_UNIT_FIX
qa_fail_count = 0
unfamiliar_pdf_count = 13
processed_pdf_count = 13
failed_pdf_count = 0
prepared_candidate_row_count = 117
source_pdf_preserved = true
missing source_page count = 0
missing unit count = 64
no_official_asset_modification_during_330h = true
```

2. Load 330H prepared candidate rows from:

```text
D:\_datefac\output\unfamiliar_trust_split_330h
```

3. Verify and preserve required fields:

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

4. Source attribution checks:

```text
source_pdf_nonempty_count
source_pdf_unique_count
source_page_nonempty_count
source_page_missing_count
source_artifact_nonempty_count
candidate_id_stability_check
```

5. Deduplication/export hygiene:

- Write only one canonical JSONL plus one XLSX for inspection.
- Make sure each row has a stable `candidate_id`.
- Do not duplicate rows between JSONL and XLSX in the prepared row count. The prepared row count should refer to unique candidate rows, not artifact-row count.
- Record explicit metadata indicating that XLSX is an inspection mirror, not an additional candidate source.

6. Unit signal improvement:

Attempt safe unit inference only from existing row/table context fields such as:

```text
row_text
metric_label_raw
table_id
evidence_refs
source_artifact
nearby table/block text if already present in the 330H row
```

Do not reopen PDFs and do not run new parser unless the row already contains enough cached context.

Unit inference must be conservative. Examples:

```text
If row/table context contains 百万元 / 百萬 / RMB mn / RMB million -> unit = RMB_mn
If row/table context contains 亿元 / 人民币亿元 / RMB bn -> unit = RMB_100m or RMB_bn, but record exact source text
If row/table context contains % / pct / percentage -> unit = percent
If row/table context contains 元/股 / RMB/share -> unit = RMB_per_share
If ambiguous or absent -> leave blank and add UNIT_UNKNOWN risk flag
```

7. Unit fix provenance:

For every unit-filled row, record:

```text
unit_fix_method
unit_fix_source_text
unit_fix_confidence = HIGH | MEDIUM | LOW
unit_fix_notes
```

8. Risk flag updates:

- If unit remains missing, ensure `UNIT_UNKNOWN` appears in `risk_flags`.
- If unit is inferred with low confidence, add or preserve `UNIT_UNKNOWN` or a warning risk as appropriate.
- Do not remove existing risk flags unless the reason is explicit and safe.

9. Generate before/after unit metrics:

```text
unit_missing_count_before
unit_missing_count_after
unit_filled_count
unit_inference_high_confidence_count
unit_inference_medium_confidence_count
unit_inference_low_confidence_count
unit_unknown_risk_added_count
```

10. If rows are prepared, optionally rerun 330F against the new 330I prepared directory and record the 330F rerun summary if successful.

11. Confirm official assets are not modified.
12. Generate QA, no-apply proof, manifest, workbook, and markdown report.

## Expected successful result

Data-dependent counts are allowed, but expected fields must exist:

```text
validated_330h_full_benchmark = true
input_candidate_row_count = 117
output_candidate_row_count = 117
source_pdf_preserved = true
source_page_missing_count_after = 0
unit_missing_count_before = 64
unit_missing_count_after <= 64
unit_filled_count >= 0
unit_unknown_risk_added_count >= 0
prepared_output_dir = D:\_datefac\output\unfamiliar_trust_split_330i
can_rerun_330f = true
no_official_asset_modification_during_330i = true
qa_fail_count = 0
```

If 330F is rerun inside 330I and succeeds:

```text
reran_330f = true
330f_unfamiliar_source_status = loaded
330f_scored_unfamiliar_record_count > 0
```

Expected decision if fixed rows are prepared:

```text
SOURCE_ATTRIBUTION_UNIT_SIGNAL_FIX_330I_READY_FOR_330F_RERUN_OR_330J_DELIVERY_REPORT_REFRESH
```

If fixed rows are prepared and 330F rerun succeeds:

```text
SOURCE_ATTRIBUTION_UNIT_SIGNAL_FIX_330I_READY_FOR_330J_DELIVERY_REPORT_REFRESH
```

If blocking QA fails:

```text
SOURCE_ATTRIBUTION_UNIT_SIGNAL_FIX_330I_NOT_READY
```

## Suggested command

```bash
python tools/run_source_attribution_unit_signal_fix_330i.py \
  --full-unfamiliar-benchmark-dir D:\_datefac\output\full_unfamiliar_export_benchmark_330h \
  --prepared-unfamiliar-dir D:\_datefac\output\unfamiliar_trust_split_330h \
  --fixed-prepared-output-dir D:\_datefac\output\unfamiliar_trust_split_330i \
  --output-dir D:\_datefac\output\source_attribution_unit_signal_fix_330i
```

If implementing optional 330F rerun inside the runner, expose:

```bash
  --rerun-330f \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b
```

## 330F rerun command after 330I

```bash
python tools\run_unfamiliar_pdf_trust_benchmark_330f.py \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --unfamiliar-source-dir D:\_datefac\output\unfamiliar_trust_split_330i \
  --output-dir D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330i
```

## Compile checks

```bash
python -m py_compile datefac\trust\source_attribution_unit_signal_fix_330i.py datefac\trust\source_attribution_unit_signal_fix_330i_report.py tools\run_source_attribution_unit_signal_fix_330i.py tests\trust\test_source_attribution_unit_signal_fix_330i.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/source_attribution_unit_signal_fix_330i.py
git add datefac/trust/source_attribution_unit_signal_fix_330i_report.py
git add tools/run_source_attribution_unit_signal_fix_330i.py
git add tests/trust/test_source_attribution_unit_signal_fix_330i.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
git add datefac/trust/full_unfamiliar_export_benchmark_330h.py
```

Commit:

```text
Add 330I source attribution unit signal fix
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330H validation result.
5. Input/output candidate row counts.
6. Source PDF/page attribution metrics.
7. Unit missing before/after and unit-filled counts.
8. Unit inference methods and confidence distribution.
9. Risk flag update counts.
10. Prepared fixed output directory.
11. Whether 330F was rerun, and rerun result if yes.
12. Recommended next step.
13. Official asset modification confirmation.
14. QA fail count.
15. Decision.
16. Git status result.
17. Commit hash.
18. Push result.
19. Residual risks.
