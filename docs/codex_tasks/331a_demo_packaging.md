# DateFac 331A Task
## Demo Packaging

## Context

330L client-style export preview is complete and pushed.

330L commit:

```text
036a2250e34fa7892349a34d77b7e993a99f2519
```

330L output:

```text
D:\_datefac\output\client_style_export_preview_330l
```

330L preview workbook:

```text
D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_preview.xlsx
```

330L result:

```text
validated_330j2_delivery_refresh = true
preview_workbook_generated = true
source_pdf_unique_count = 7
prepared_candidate_row_count = 117
strict_deduped_candidate_count = 117
unit_missing_count = 18
unit_conflict_risk_count = 12
trusted_sheet_row_count = 96
review_required_sheet_row_count = 21
unit_review_sheet_row_count = 21
source_provenance_sheet_row_count = 14
qa_caveat_count = 7
delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
no_official_asset_modification_during_330l = true
qa_fail_count = 0
decision = CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING
```

330L residual risks:

```text
- This is sidecar client-style preview, not production routing.
- Not client-ready.
- 18 rows still have missing unit.
- 12 rows still have unit conflict risk.
- artifact-row and candidate-row counts differ because of compatibility rerun artifacts.
```

331A should package the current DateFac demo into a clean project/demo artifact set that can be used for GitHub, resume, school internship reporting, and product-style explanation.

## Goal

Implement 331A: Demo Packaging.

331A should generate a demo package summarizing the DateFac Trust Engine milestone from 324-330L, with emphasis on:

1. What the system can currently demonstrate.
2. What outputs exist.
3. What remains manual/review-required.
4. Why the system is not pretending to be production/client-ready.
5. How to present the project in GitHub/resume/interview/demo contexts.

331A must be documentation/report packaging only. It must not change production behavior, parser behavior, trust scoring behavior, or official assets.

## Recommended Codex reasoning level

```text
Medium
```

Use `Medium` because this is packaging/reporting, not parser work or trust-policy design. Use `High` only if reconstructing milestone history from artifacts becomes difficult.

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
- Do not overwrite 330L outputs.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add/update 331A demo packaging source/report/runner/test/docs files.

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
datefac/trust/demo_packaging_331a.py
datefac/trust/demo_packaging_331a_report.py
tools/run_demo_packaging_331a.py
tests/trust/test_demo_packaging_331a.py
```

Documentation outputs to create/update if appropriate:

```text
docs/demo/datefac_demo_overview_331a.md
docs/demo/datefac_resume_bullets_331a.md
docs/demo/datefac_github_readme_section_331a.md
docs/demo/datefac_demo_script_331a.md
```

Possible precise update only if needed:

```text
datefac/trust/__init__.py
```

Do not edit production pipeline modules.

## Inputs

Primary input:

```text
D:\_datefac\output\client_style_export_preview_330l
```

References:

```text
D:\_datefac\output\delivery_report_refresh_after_330k_330j2
D:\_datefac\output\unit_signal_review_330k
D:\_datefac\output\source_attribution_unit_signal_fix_330i
D:\_datefac\output\full_unfamiliar_export_benchmark_330h
D:\_datefac\output\delivery_report_refresh_330j
D:\_datefac\output\alias_patch_cycle_closure_325p
D:\_datefac\output\official_scope_patch_cycle_closure_324n
D:\_datefac\output\trust_engine_foundation_330a
D:\_datefac\output\trust_engine_scoring_330b
D:\_datefac\output\cached_candidate_trust_scoring_330c
```

Official assets may be read only for no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Output directory

```text
D:\_datefac\output\demo_packaging_331a
```

Suggested outputs:

```text
demo_packaging_331a_summary.json
demo_packaging_331a_qa.json
demo_packaging_331a_demo_manifest.json
demo_packaging_331a_report.md
demo_packaging_331a_no_apply_proof.json
demo_packaging_331a_project_brief.md
demo_packaging_331a_resume_bullets.md
demo_packaging_331a_github_readme_section.md
demo_packaging_331a_demo_script.md
```

## Required behavior

1. Validate 330L readiness:

```text
decision = CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING
qa_fail_count = 0
preview_workbook_generated = true
prepared_candidate_row_count = 117
strict_deduped_candidate_count = 117
unit_missing_count = 18
unit_conflict_risk_count = 12
delivery_readiness_judgment = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
no_official_asset_modification_during_330l = true
```

2. Load 330L summary and manifest.
3. Load key closure summaries when available:

```text
324N scope closure
325P alias closure
330A-330L Trust Engine milestones
```

4. Generate milestone summary:

```text
scope_rule_count_324 = 1 if available
alias_rule_count_325 = 6 if available
cumulative_official_rule_count_after_325 = 23 if available
cumulative_trusted_gain_after_325 = 138 if available
cumulative_review_reduction_after_325 = 503 if available
330L prepared_candidate_row_count = 117
330L trusted_sheet_row_count = 96
330L review_required_sheet_row_count = 21
330L unit_review_sheet_row_count = 21
```

5. Generate demo positioning:

Required wording must include:

```text
DateFac is a financial PDF core-metric extraction and trust-routing demo.
Current status: demo-ready with manual review caveats.
The system demonstrates parser-output normalization, semantic rule curation, sidecar trust scoring, risk flagging, provenance preservation, and client-style Excel preview generation.
It is not production-ready or client-ready yet.
```

6. Generate project brief sections:

```text
Problem
System capability
Architecture summary
Trust Engine workflow
Demo output artifacts
What is safe to claim
What is not safe to claim
Next steps
```

7. Generate resume bullets in Chinese and optionally English:

Must be truthful and not overclaim.

Suggested Chinese tone:

```text
参与/独立构建金融研报 PDF 核心指标可信提取原型，设计 parser 输出规范化、候选指标风险标记、人工复核闭环与 sidecar Trust Engine 打分流程；在 13 份陌生 PDF benchmark 上生成 117 条候选指标、96 条可信建议、21 条复核样本，并输出客户视角 Excel 预览包。
```

8. Generate GitHub README section:

Must include:

```text
Current status
Architecture
What the demo shows
How to run key sidecar reports
Known limitations
```

9. Generate demo script:

For a 3-5 minute walkthrough:

```text
open problem statement
show pipeline concept
show 330L Excel preview
explain trusted vs review-required
explain unit caveats
explain next steps
```

10. Generate QA checks:

```text
no_production_claims
no_client_ready_claims
required_artifacts_exist
resume_bullets_not_overclaiming
official_assets_unchanged
```

11. Confirm official assets are not modified.
12. Generate summary, QA, no-apply proof, manifest, and markdown reports.

## Expected summary fields

Data-dependent values are allowed, but these fields must exist:

```text
validated_330l_export_preview = true
project_status = DEMO_READY_WITH_UNIT_REVIEW_CAVEATS
client_ready = false
production_ready = false
preview_workbook_path exists
prepared_candidate_row_count = 117
trusted_sheet_row_count = 96
review_required_sheet_row_count = 21
unit_review_sheet_row_count = 21
project_brief_generated = true
resume_bullets_generated = true
github_readme_section_generated = true
demo_script_generated = true
no_official_asset_modification_during_331a = true
qa_fail_count = 0
```

Expected decision:

```text
DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW
```

If blocking QA fails:

```text
DEMO_PACKAGING_331A_NOT_READY
```

## Suggested command

```bash
python tools/run_demo_packaging_331a.py \
  --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l \
  --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 \
  --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k \
  --output-dir D:\_datefac\output\demo_packaging_331a
```

## Compile checks

```bash
python -m py_compile datefac\trust\demo_packaging_331a.py datefac\trust\demo_packaging_331a_report.py tools\run_demo_packaging_331a.py tests\trust\test_demo_packaging_331a.py
```

Run only the new lightweight trust tests if tests are added.

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/demo_packaging_331a.py
git add datefac/trust/demo_packaging_331a_report.py
git add tools/run_demo_packaging_331a.py
git add tests/trust/test_demo_packaging_331a.py
```

If docs are generated/updated deliberately:

```bash
git add docs/demo/datefac_demo_overview_331a.md
git add docs/demo/datefac_resume_bullets_331a.md
git add docs/demo/datefac_github_readme_section_331a.md
git add docs/demo/datefac_demo_script_331a.md
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
```

Commit:

```text
Add 331A demo packaging
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Output directory.
4. 330L validation result.
5. Generated demo package artifacts.
6. Project status wording.
7. Resume/GitHub/demo script outputs.
8. QA checks.
9. Official asset modification confirmation.
10. QA fail count.
11. Decision.
12. Git status result.
13. Commit hash.
14. Push result.
15. Residual risks.
