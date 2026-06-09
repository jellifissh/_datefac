# DateFac Real PDF + MinerU + AI Review Runbook 339A (Synced To 341A State)

## 1. What This Runbook Now Covers

This document still focuses on the `337A-338D` real-PDF, MinerU, and AI dry-run path, but it is now synchronized to the `341A` milestone state.

Its job now is to explain:

> AI review is only a mid-chain governance layer. The strongest current external story continues through human review, client preview, and preview audit rather than stopping at adoption simulation.

## 2. Current Overall Status

- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `not investment advice`

## 3. Where 339A Sits In Today’s Chain

339A explains the front half:

1. real PDFs enter MinerU-first intake
2. deterministic rules perform precision calibration and context repair
3. reviewed strictness and year alignment QA tighten the reviewed pool
4. AI review provides dry-run suggestions for ambiguous rows

But the complete current chain is now:

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

## 4. Recommended Reading Order

1. `README.md`
2. this document
3. `docs/demo/datefac_ai_review_architecture_339a_en.md`
4. `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_en.md`
5. `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_en.md`

## 5. Recommended 337A-338D Command Order

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

## 6. Front-Half Results That Still Matter

### 337A-337D

- 337A parsed `3` real PDFs successfully
- 337A reviewed / needs_review / rejected = `303 / 42 / 2`
- 337B reduced reviewed from `303` to `98`
- 337C raised reviewed to `148`
- 337D tightened reviewed to `112`

### 338A-338D

- 338A DeepSeek baseline `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B shows `gpt-5.5` is stronger on the sampled adjudication task
- 338C reduces invalid responses further with grounded review
- 338D still does not approve default formal adoption because `suggest_set_ai_review_model_default = false`

## 7. New Milestone Counts Synced From 341A

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`

## 8. The Boundaries That Matter Most Now

- AI decisions are dry-run only
- human review was used before client preview
- `340F` is a human-reviewed client preview, not official delivery
- `340G` passed audit, but the system is still not production-ready
- the benchmark is still a limited real-PDF sample set, not evidence of scalable stability

## 9. Best Files To Open Now

- `D:\_datefac\output\mineru_real_test_337a\00_batch_summary.json`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\reviewed_strictness_year_alignment_337d_summary.json`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_summary.json`
- `D:\_datefac\output\human_reviewed_client_preview_milestone_341a\human_reviewed_client_preview_milestone_341a.xlsx`
- `D:\_datefac\output\client_preview_export_audit_340g\client_preview_export_audit_340g.xlsx`

## 10. Final Line

> 339A is no longer only an AI-review runbook. It is now the front-half explanation layer for the 341A milestone, showing why AI dry-run still must be followed by human review and preview audit. 
