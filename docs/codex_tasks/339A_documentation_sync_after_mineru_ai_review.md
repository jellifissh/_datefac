# 339A Documentation Sync After MinerU And AI Review Pipeline

## Goal

Incrementally sync repository-facing documentation after the new real PDF, MinerU-first, precision repair, strict reviewed QA, and AI review dry-run stages.

This is documentation-only.

## Scope

- Update repository docs so the current pipeline is understandable and current.
- Keep the project positioned as sidecar / demo / preview / no-write-back.
- Do not modify production pipeline, parser, extraction, delivery behavior, official assets, or output artifacts.
- Do not touch protected dirty files.

## Files To Update If Needed

- `README.md`
- `docs/demo/（中文新手指南）datefac_newbie_operator_guide_333a_zh.md`
- `docs/demo/（英文新手指南）datefac_newbie_operator_guide_333a_en.md`
- `docs/demo/（中文运行手册）datefac_current_runbook_333a_zh.md`
- `docs/demo/（英文运行手册）datefac_current_runbook_333a_en.md`
- `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
- `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/datefac_interview_talking_points_332a.md`

## New Docs To Create

- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md`
- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md`
- `docs/demo/datefac_ai_review_architecture_339a_zh.md`
- `docs/demo/datefac_ai_review_architecture_339a_en.md`

## Must Reflect

- DateFac now has a MinerU-first real PDF intake preview.
- It has rule-based precision repair and strict reviewed QA.
- It has AI review text adjudication dry-run and adoption simulation.
- It is still not client-ready.
- It is still not production-ready.
- AI model decisions are dry-run only and do not write back.
- `AI_REVIEW_MODEL` is a main text adjudication candidate.
- DeepSeek flash remains fallback / baseline.
- Vision models are reserved for future visual/layout/image-table uncertainty.

## Current Pipeline Overview

```powershell
python tools\run_mineru_real_pdf_intake_337a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\mineru_real_test_337a

python tools\run_mineru_candidate_precision_337b.py --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\mineru_candidate_precision_337b

python tools\run_core_financial_context_repair_337c.py --precision-337b-dir D:\_datefac\output\mineru_candidate_precision_337b --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\core_financial_context_repair_337c

python tools\run_reviewed_strictness_year_alignment_337d.py --context-repair-337c-dir D:\_datefac\output\core_financial_context_repair_337c --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d

python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50

python tools\run_ai_review_model_ab_338b.py --baseline-338a-dir D:\_datefac\output\deepseek_text_adjudicator_338a --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_model_ab_338b --limit 50

python tools\run_grounded_ai_review_338c.py --ab-338b-dir D:\_datefac\output\ai_review_model_ab_338b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\grounded_ai_review_338c --limit 50

python tools\run_ai_review_adoption_simulation_338d.py --grounded-ai-review-338c-dir D:\_datefac\output\grounded_ai_review_338c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_adoption_simulation_338d
```

## Latest Metrics To Surface

- 337A parsed 3 PDFs successfully with MinerU.
- 337A candidates:
  - `352620_1 = 134`
  - `352906_1 = 111`
  - `356439_1 = 102`
- 337B reviewed reduced from `303` to `98`.
- 337C reviewed became `148`.
- 337C `unit_filled_count = 119`.
- 337D reviewed became `112`.
- 338A DeepSeek flash baseline:
  - `low_confidence = 34 / 50`
  - `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B AI_REVIEW_MODEL comparison:
  - `low_confidence = 0 / 50`
  - `NEEDS_MORE_CONTEXT = 3 / 50`
  - `invalid_response = 3`
- 338C grounded review:
  - `invalid_response = 1`
  - `grounding_source BOTH = 49`
- 338D adoption simulation:
  - `ACCEPT_MODEL_CONFIRM = 39`
  - `ACCEPT_MODEL_REJECT = 3`
  - `HOLD_FOR_HUMAN_REVIEW = 3`
  - `INVALID_MODEL_RESPONSE = 1`
  - `deterministic_rule_override_count = 0`

## Forbidden Claims

- client-ready
- production-ready
- 100% accurate
- fully automatic commercial SaaS
- direct investment decision
- no human review needed
- AI decisions are final

## Required Negative Claims

- not client-ready
- not production-ready
- does not guarantee 100% accuracy
- AI decisions are dry-run only
- human review remains necessary

## Validation

- Check updated docs for unsafe positive claims.
- Check README mentions MinerU-first, AI review dry-run, and not production-ready.
- Check beginner docs explain the simple real PDF flow.
- Check runbooks include commands.
- Check AI architecture docs mention dry-run / no-write-back / hard-rule priority.

## Protected Dirty Files

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
