# 340A Milestone Acceptance Audit After MinerU And AI Review Pipeline

## Goal

Create a sidecar milestone acceptance audit that verifies the current DateFac real PDF pipeline is reproducible, understandable, and ready for demo / research-preview use.

This task is validation and reporting only.

## Boundaries

- Do not modify production pipeline behavior.
- Do not modify parser / extraction / delivery files.
- Do not modify official assets.
- Do not modify existing outputs in place.
- Do not commit generated output artifacts.
- Do not use `git add -A`.
- Do not use `git add .`.

## Inputs To Check

- `D:/_datefac/input/real_test`
- `D:/_datefac/output/mineru_real_test_337a`
- `D:/_datefac/output/mineru_candidate_precision_337b`
- `D:/_datefac/output/core_financial_context_repair_337c`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/deepseek_text_adjudicator_338a`
- `D:/_datefac/output/ai_review_model_ab_338b`
- `D:/_datefac/output/grounded_ai_review_338c`
- `D:/_datefac/output/ai_review_adoption_simulation_338d`

## Docs To Check

- `README.md`
- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md`
- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md`
- `docs/demo/datefac_ai_review_architecture_339a_zh.md`
- `docs/demo/datefac_ai_review_architecture_339a_en.md`

## Expected Output Dir

- `D:/_datefac/output/milestone_acceptance_audit_340a`

## Expected Artifacts

- `milestone_acceptance_audit_340a_summary.json`
- `milestone_acceptance_audit_340a_manifest.json`
- `milestone_acceptance_audit_340a_qa.json`
- `milestone_acceptance_audit_340a_report.md`
- `milestone_acceptance_audit_340a.xlsx`

## Audit Requirements

### 1. Input PDF Audit

- Count PDFs in `D:/_datefac/input/real_test`
- Confirm the 3 expected PDFs exist

Expected:

- `H3_AP202606081823352620_1.pdf`
- `H3_AP202606081823352906_1.pdf`
- `H3_AP202606081823356439_1.pdf`

### 2. Main Pipeline Output Audit

Confirm these files exist:

- `D:/_datefac/output/mineru_real_test_337a/real_test_mineru_client_export_337a.xlsx`
- `D:/_datefac/output/mineru_candidate_precision_337b/real_test_mineru_client_export_337b.xlsx`
- `D:/_datefac/output/core_financial_context_repair_337c/real_test_mineru_client_export_337c.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx`
- `D:/_datefac/output/grounded_ai_review_338c/grounded_ai_review_338c_plan.xlsx`
- `D:/_datefac/output/ai_review_adoption_simulation_338d/ai_review_adoption_simulation_338d_plan.xlsx`

### 3. Key Metric Audit

Use existing summaries or workbook data to confirm:

- 337A parsed `3` PDFs
- 337A metric candidates:
  - `352620_1 = 134`
  - `352906_1 = 111`
  - `356439_1 = 102`
- 337B reviewed = `98`
- 337C reviewed = `148`
- 337D reviewed = `112`
- 338D input rows = `50`
- 338D `ACCEPT_MODEL_CONFIRM = 39`
- 338D `ACCEPT_MODEL_REJECT = 3`
- 338D `HOLD_FOR_HUMAN_REVIEW = 3`
- 338D `INVALID_MODEL_RESPONSE = 1`
- 338D `deterministic_rule_override_count = 0`

### 4. Manual Sample Audit Sheet

From 337D reviewed rows:

- sample up to `10` rows from each PDF, or all if fewer
- include document, metric, year, value, unit, source_page, evidence excerpt, table role if available
- add:
  - `audit_status_placeholder`
  - `audit_notes_placeholder`

This is not manual review itself. It is a review-ready sample sheet.

### 5. AI Adoption Audit Sheet

From 338D, include:

- accepted confirms
- accepted rejects
- holds
- invalid responses
- deterministic rule rejects

Include:

- `model_name`
- `confidence`
- `grounding_source`
- `adoption_action`
- `adoption_reason`

### 6. Documentation Consistency Audit

Check the docs mention:

- MinerU-first real PDF intake
- AI review dry-run / no-write-back
- not client-ready
- not production-ready
- `AI_REVIEW_MODEL` as candidate text adjudicator
- DeepSeek flash as fallback / baseline
- vision model only for future visual / layout uncertainty

### 7. Unsafe Claim Audit

Fail if docs or generated report contain unsafe positive claims:

- `client-ready`
- `production-ready`
- `fully automatic commercial SaaS`
- `100% accurate`
- `no human review needed`
- `AI decisions are final`

Allow negative forms:

- `not client-ready`
- `not production-ready`
- `not 100% accurate`
- `AI decisions are dry-run only`

### 8. Final Judgment

Allowed judgments:

- `MILESTONE_ACCEPTED_FOR_DEMO_RESEARCH_PREVIEW`
- `MILESTONE_ACCEPTED_WITH_REVIEW_CAVEATS`
- `MILESTONE_BLOCKED`

Current expected outcome:

- `MILESTONE_ACCEPTED_WITH_REVIEW_CAVEATS`

The report must clearly say:

- suitable for demo / research-preview
- not client-ready
- not production-ready
- AI adoption is dry-run only
- human review remains necessary

## Files To Create

- `docs/codex_tasks/340A_milestone_acceptance_audit_after_mineru_ai_review.md`
- `datefac/trust/milestone_acceptance_audit_340a.py`
- `datefac/trust/milestone_acceptance_audit_340a_report.py`
- `tools/run_milestone_acceptance_audit_340a.py`
- `tests/trust/test_milestone_acceptance_audit_340a.py`

## Run

```powershell
python -m py_compile datefac\trust\milestone_acceptance_audit_340a.py datefac\trust\milestone_acceptance_audit_340a_report.py tools\run_milestone_acceptance_audit_340a.py tests\trust\test_milestone_acceptance_audit_340a.py

python -m pytest tests\trust\test_milestone_acceptance_audit_340a.py -q

python tools\run_milestone_acceptance_audit_340a.py --input-pdf-dir D:\_datefac\input\real_test --output-root D:\_datefac\output --docs-root D:\_datefac\docs --repo-root D:\_datefac --output-dir D:\_datefac\output\milestone_acceptance_audit_340a
```

## Protected Dirty Files

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
