# DateFac Real PDF + MinerU + AI Review Runbook 339A (English)

## 1. Purpose

This runbook describes the most realistic current path:

> start from real research PDFs, parse them with MinerU, tighten the result with deterministic repair and stricter QA, and then optionally evaluate AI text adjudication in dry-run form.

This is not a production manual. It does not authorize official write-back.

## 2. Preconditions

- input directory: `D:\_datefac\input\real_test`
- current sample size: `3` PDFs
- local MinerU available
- Python available

## 3. Recommended Command Order

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

## 4. What To Inspect At Each Step

### 337A

Inspect:

- `00_batch_summary.json`
- `real_test_mineru_client_export_337a.xlsx`

Current result:

- all 3 PDFs succeeded
- reviewed `303`
- needs_review `42`
- rejected `2`

### 337B

Inspect:

- `mineru_candidate_precision_337b_summary.json`

Current result:

- reviewed reduced from `303` to `98`

### 337C

Inspect:

- `core_financial_context_repair_337c_summary.json`

Current result:

- reviewed increased to `148`
- `unit_filled_count = 119`

### 337D

Inspect:

- `reviewed_strictness_year_alignment_337d_summary.json`

Current result:

- reviewed tightened to `112`

### 338A-338D

Core story:

- DeepSeek flash baseline is conservative and often low-confidence
- `gpt-5.5` is stronger as a text adjudicator candidate, but still produces some invalid responses
- grounded schema tightening reduces invalid output further
- adoption simulation still does not recommend immediate default adoption

## 5. Boundaries That Matter Most

- not client-ready
- not production-ready
- AI outputs do not write back
- deterministic rules outrank model suggestions
- human review remains necessary

## 6. Recommended Files To Open First

- `README.md`
- `docs/demo/datefac_ai_review_architecture_339a_en.md`
- `D:\_datefac\output\mineru_real_test_337a\00_batch_summary.json`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\reviewed_strictness_year_alignment_337d_summary.json`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_summary.json`

## 7. One-Line Summary

> The purpose of this path is not to present AI as the final decision-maker, but to make the path from real PDFs to explainable preview state technically disciplined and auditable.
