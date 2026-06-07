# DateFac 330K Task
## Unit Signal Improvement or Full Review Sample

## Context

330J delivery report refresh is complete and pushed.

330J commit:

```text
8d389f94fa62256e79259c2f149d9fab048eec8a
```

330J output:

```text
D:\_datefac\output\delivery_report_refresh_330j
```

330J result:

```text
validated_330i_unit_fix = true
reran_330f = true
330f_unfamiliar_source_status = loaded
330f_scored_unfamiliar_record_count = 234
processed_pdf_count = 7
source_pdf_unique_count = 7
prepared_candidate_row_count = 117
artifact_row_count = 234
strict_deduped_candidate_count = 117
sidecar_trusted_suggestion_count = 120
sidecar_review_required_suggestion_count = 114
sidecar_auto_trusted_ratio_artifact_row = 0.512821
sidecar_auto_trusted_ratio_strict_deduped = 1.025641
unit_missing_count = 54
source_page_missing_count = 0
unit_unknown_risk_count = 54
unit_conflict_risk_count = 12
confidence_level_distribution = {"HIGH": 120, "MEDIUM": 96, "LOW": 18}
routing_decision_distribution = {"TRUSTED": 120, "REVIEW_REQUIRED": 114}
risk_flag_distribution = {"UNIT_UNKNOWN": 108, "UNIT_CONFLICT": 24, "LABEL_AMBIGUOUS": 16}
unit_missing_before_330i = 64
unit_missing_after_330i = 54
unit_filled_count = 19
source_page_missing_before_330h = 83
source_page_missing_after_330i = 0
trusted_suggestion_delta = -106
review_required_delta = 106
delivery_readiness_judgment = DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS
recommended_next_step = 330K_UNIT_SIGNAL_IMPROVEMENT_OR_FULL_REVIEW_SAMPLE
secondary_next_step = 330L_CLIENT_STYLE_EXPORT_PREVIEW
no_official_asset_modification_during_330j = true
qa_fail_count = 0
decision = DELIVERY_REPORT_REFRESH_330J_READY_FOR_330K_UNIT_SIGNAL_OR_REVIEW_SAMPLE
```

Known 330J residual risks:

```text
- unit_missing_count = 54 remains high.
- UNIT_UNKNOWN and UNIT_CONFLICT risks are significant.
- 330F trusted/review counts are still artifact-row based while strict deduped count is candidate-level, so sidecar_auto_trusted_ratio_strict_deduped can exceed 1.
- 330J used an isolated compatibility input for rerunning 330F; canonical 330I prepared output was not polluted.
- This is demo-ready with manual review caveats, not client-ready.
```

330K should take the next smallest useful step. It should not try to solve the entire parser/unit problem. It should either improve unit signals where safe, or produce a review sample focused on unit ambiguity and Trust Engine routing quality.

## Goal

Implement 330K: Unit Signal Improvement or Full Review Sample.

330K should inspect the 330I/330J candidate rows and produce a unit-focused improvement/review package.

Primary outcome:

```text
A small, auditable unit quality package that identifies why 54 unit-missing candidates remain, which rows can be safely fixed from existing context, and which rows must stay review-required.
```

330K must remain sidecar-only. It must not change production routing, official assets, or previous cached outputs.

## Recommended Codex reasoning level

```text
High
```

Use `High` because unit inference affects financial data correctness. Do not use aggressive guessing. Wrong unit inference is worse than missing unit.

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
- Do not reopen PDFs unless explicitly necessary for read-only diagnostics; prefer existing prepared rows only.
- Do not fabricate units.
- Do not overwrite the 330I prepared output directory. Write to a new 330K output/prepared directory if producing revised rows.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 330K sidecar source/report/runner/test files.

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
datefac/trust/unit_signal_review_330k.py
datefac/trust/unit_signal_review_330k_report.py
tools/run_unit_signal_review_330k.py
tests/trust/test_unit_signal_review_330k.py
```

Possible precise updates only if needed:

```text
datefac/trust/__init__.py
```

Do not edit production pipeline modules.

## Inputs

Primary inputs:

```text
D:\_datefac\output\delivery_report_refresh_330j
D:\_datefac\output\source_attribution_unit_signal_fix_330i
D:\_datefac\output\unfamiliar_trust_split_330i
```

References:

```text
D:\_datefac\output\full_unfamiliar_export_benchmark_330h
D:\_datefac\output\unfamiliar_trust_split_330h
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
D:\_datefac\output\unit_signal_review_330k
```

Optional fixed prepared output if safe unit fixes are found:

```text
D:\_datefac\output\unfamiliar_trust_split_330k
```

Suggested outputs:

```text
unit_signal_review_330k_summary.json
unit_signal_review_330k_qa.json
unit_signal_review_330k_unit_categories.json
unit_signal_review_330k_review_sample.xlsx
unit_signal_review_330k_no_apply_proof.json
unit_signal_review_330k_report.md
```

Optional prepared outputs if fixes are applied:

```text
D:\_datefac\output\unfamiliar_trust_split_330k\unfamiliar_candidate_rows.jsonl
D:\_datefac\output\unfamiliar_trust_split_330k\unfamiliar_candidate_rows.xlsx
D:\_datefac\output\unfamiliar_trust_split_330k\unfamiliar_candidate_manifest.json
```

## Required behavior

1. Validate 330J readiness:

```text
decision = DELIVERY_REPORT_REFRESH_330J_READY_FOR_330K_UNIT_SIGNAL_OR_REVIEW_SAMPLE
qa_fail_count = 0
prepared_candidate_row_count = 117
strict_deduped_candidate_count = 117
unit_missing_count = 54
unit_unknown_risk_count = 54
unit_conflict_risk_count = 12
source_page_missing_count = 0
delivery_readiness_judgment = DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS
no_official_asset_modification_during_330j = true
```

2. Load 330I canonical prepared rows from:

```text
D:\_datefac\output\unfamiliar_trust_split_330i
```

3. Identify rows by unit status:

```text
unit_present
unit_missing_with_unit_unknown
unit_conflict
unit_missing_without_unit_unknown
unit_inferred_high_confidence
unit_inferred_medium_confidence
unit_inferred_low_confidence
```

4. Categorize unit-missing rows into actionable categories:

```text
PERCENT_LIKE_METRIC_WITH_NO_PERCENT_MARKER
PER_SHARE_LIKE_METRIC_WITH_NO_UNIT_MARKER
MONEY_LIKE_METRIC_WITH_NO_TABLE_UNIT_CONTEXT
COUNT_OR_VOLUME_LIKE_METRIC
AMBIGUOUS_LABEL_OR_TARGET
NO_SAFE_UNIT_CONTEXT
OTHER
```

5. Conservative additional inference pass from existing fields only:

Use existing row fields only:

```text
row_text
metric_label_raw
normalized_metric
table_id
evidence_refs
source_artifact
unit_fix_source_text
```

Do not reopen PDFs. Do not use surrounding PDF context that is not already present in rows.

Safe examples:

```text
labels containing EPS / 每股收益 and row text contains 元/股 or RMB/share -> RMB_per_share
labels containing margin / 利率 / 比率 and row text contains % -> percent
labels containing revenue / net profit / 营业收入 / 净利润 and row text contains 百万元 -> RMB_mn
```

Unsafe examples that must remain review-required:

```text
EPS row with only 亿元 context inherited from table-wide monetary unit
margin-like label with no percent marker
money-like label with no explicit unit marker
any row with conflicting unit evidence
```

6. If safe fixes are found:

- Write optional fixed rows to `unfamiliar_trust_split_330k`.
- Preserve original candidate IDs unless unit change requires explicit revision metadata.
- Add fields:

```text
unit_fix_330k_method
unit_fix_330k_source_text
unit_fix_330k_confidence
unit_fix_330k_notes
```

7. If no additional safe fixes are found:

- Do not force fixes.
- Produce a review package and recommendation.

8. Generate a human review sample workbook containing:

```text
missing-unit candidates
unit-conflict candidates
high-impact TRUSTED or HIGH confidence candidates with unit risk
examples by source_pdf
examples by normalized_metric
recommended human decision column
notes column
```

Recommended human decision values:

```text
CONFIRM_UNIT
REJECT_UNIT
KEEP_UNIT_UNKNOWN
NEEDS_MORE_CONTEXT
```

9. Produce review burden metrics:

```text
unit_review_required_count
unit_conflict_review_count
unit_unknown_review_count
high_confidence_with_unit_risk_count
pdfs_affected_by_unit_risk_count
```

10. Decide next step:

If additional safe fixes materially reduce unit_missing_count:

```text
recommended_next_step = 330J2_DELIVERY_REPORT_REFRESH_AFTER_330K
```

If no safe fixes are available but review package is ready:

```text
recommended_next_step = 330K2_HUMAN_UNIT_REVIEW
```

If the review sample is sufficient for demo delivery caveats:

```text
secondary_next_step = 330L_CLIENT_STYLE_EXPORT_PREVIEW
```

11. Confirm official assets are not modified.
12. Generate QA, no-apply proof, summary, review workbook, and markdown report.

## Expected summary fields

Data-dependent values are allowed, but these fields must exist:

```text
validated_330j_delivery_refresh = true
input_candidate_row_count = 117
unit_missing_count_input = 54
unit_conflict_count_input = 12
unit_review_required_count >= 0
unit_unknown_review_count >= 0
unit_conflict_review_count >= 0
additional_safe_unit_fix_count >= 0
unit_missing_count_after_330k <= 54
review_sample_row_count > 0
human_review_workbook_generated = true
no_official_asset_modification_during_330k = true
qa_fail_count = 0
```

Decision if fixes are applied and rows are prepared:

```text
UNIT_SIGNAL_REVIEW_330K_READY_FOR_330J2_DELIVERY_REFRESH
```

Decision if no fixes are applied but review sample is ready:

```text
UNIT_SIGNAL_REVIEW_330K_READY_FOR_HUMAN_UNIT_REVIEW
```

Decision if blocking QA fails:

```text
UNIT_SIGNAL_REVIEW_330K_NOT_READY
```

## Suggested command

```bash
python tools/run_unit_signal_review_330k.py \
  --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_330j \
  --source-attribution-unit-fix-dir D:\_datefac\output\source_attribution_unit_signal_fix_330i \
  --fixed-prepared-dir D:\_datefac\output\unfamiliar_trust_split_330i \
  --output-dir D:\_datefac\output\unit_signal_review_330k \
  --optional-fixed-prepared-output-dir D:\_datefac\output\unfamiliar_trust_split_330k
```

## Compile checks

```bash
python -m py_compile datefac\trust\unit_signal_review_330k.py datefac\trust\unit_signal_review_330k_report.py tools\run_unit_signal_review_330k.py tests\trust\test_unit_signal_review_330k.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/unit_signal_review_330k.py
git add datefac/trust/unit_signal_review_330k_report.py
git add tools/run_unit_signal_review_330k.py
git add tests/trust/test_unit_signal_review_330k.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
```

Commit:

```text
Add 330K unit signal review
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330J validation result.
5. Input candidate/unit status counts.
6. Unit missing category distribution.
7. Additional safe unit fix count.
8. Unit missing after 330K.
9. Review sample row count and workbook path.
10. Review burden metrics.
11. Recommended next step.
12. Official asset modification confirmation.
13. QA fail count.
14. Decision.
15. Git status result.
16. Commit hash.
17. Push result.
18. Residual risks.
