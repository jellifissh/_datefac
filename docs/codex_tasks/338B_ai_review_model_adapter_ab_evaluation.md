# 338B AI Review Model Adapter and A/B Evaluation

## Goal
- Generalize 338A from DeepSeek-specific runtime naming to model-agnostic AI review naming.
- Prefer `AI_REVIEW_*` environment variables and fall back to `DEEPSEEK_*` only when needed.
- Re-run the same 50 adjudication rows used by 338A.
- Upgrade prompt context with stronger table and neighboring-row evidence.
- Produce a row-aligned A/B comparison against 338A.

## Scope
- New sidecar trust code only.
- New runner only.
- New tests only.
- New task doc only.
- Do not modify production pipeline, parser, extraction, delivery behavior, official assets, or 337D / 338A outputs in place.
- Do not commit generated output artifacts.

## Inputs
- `D:/_datefac/output/deepseek_text_adjudicator_338a`
- `D:/_datefac/output/deepseek_text_adjudicator_338a/deepseek_text_adjudication_plan_338a.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/reviewed_strictness_year_alignment_337d_before_after.xlsx`

## Output Dir
- `D:/_datefac/output/ai_review_model_ab_338b`

## Expected Artifacts
- `ai_review_model_ab_338b_summary.json`
- `ai_review_model_ab_338b_manifest.json`
- `ai_review_model_ab_338b_qa.json`
- `ai_review_model_ab_338b_report.md`
- `ai_review_model_ab_338b_plan.xlsx`
- `ai_review_model_ab_338b_cache.jsonl`
- `ai_review_model_ab_338b_prompt_preview.jsonl`

## Environment Variable Policy
Prefer:
- `AI_REVIEW_API_KEY`
- `AI_REVIEW_BASE_URL`
- `AI_MODEL`

Fallback only if the preferred set is incomplete:
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`

## Security Rules
- Never print API keys.
- Never write API keys to any file.
- Never include API keys in logs.
- Never commit `.env`.
- Only report whether key variables are `SET` or `MISSING`.
- Report the resolved model name, but not the secret key.

## Prompt Context Upgrade
Compared with 338A, include:
- original row evidence
- table year headers if available
- nearby previous row
- nearby next row
- table role from 337D if available
- source page
- suspicious reason
- deterministic guard result
- metric / year / value / unit before adjudication
- route change context

Important:
- The model must not guess.
- If table year headers are missing and year/value mapping is not recoverable from supplied context, the model should choose `NEEDS_MORE_CONTEXT`.

## Required Model JSON Schema
```json
{
  "decision": "CONFIRM_REVIEWED | DOWNGRADE_TO_NEEDS_REVIEW | REJECT | NEEDS_MORE_CONTEXT",
  "suggested_metric": "string_or_null",
  "suggested_year": "string_or_null",
  "suggested_value": "string_or_null",
  "suggested_unit": "string_or_null",
  "table_role_guess": "CORE_FINANCIAL_SUMMARY | PROFIT_FORECAST_VALUATION | FINANCIAL_STATEMENT_DETAIL | INDUSTRY_DATA_TABLE | RATING_STANDARD_TABLE | LEGAL_DISCLOSURE_TABLE | COMPANY_PROFILE_TABLE | OTHER_TABLE | UNKNOWN",
  "risk_flags": ["string"],
  "confidence": 0.0,
  "reason": "short Chinese explanation",
  "evidence_quote": "short quote copied only from provided evidence"
}
```

## Row Alignment
- Use the same 50 rows as 338A whenever possible.
- Align by `adjudication_id`.
- Keep the original `source_sheet` and `source_row_no`.

## Workbook
`ai_review_model_ab_338b_plan.xlsx`

Sheets:
1. `00_README`
2. `01_AB_SUMMARY`
3. `02_NEW_MODEL_ADJUDICATION_PLAN`
4. `03_DEEPSEEK_338A_BASELINE`
5. `04_ROW_LEVEL_COMPARISON`
6. `05_CHANGED_DECISIONS`
7. `06_INVALID_OR_LOW_CONFIDENCE`
8. `07_RULE_MODEL_CONFLICTS`
9. `08_PROMPT_CONTEXT_UPGRADE`
10. `09_CACHE_AND_COST_SUMMARY`

## Comparison Metrics
- `baseline_model_name`
- `new_model_name`
- `row_count`
- `invalid_response_count_baseline`
- `invalid_response_count_new`
- `low_confidence_count_baseline`
- `low_confidence_count_new`
- `needs_more_context_count_baseline`
- `needs_more_context_count_new`
- `confirm_reviewed_count_baseline`
- `confirm_reviewed_count_new`
- `downgrade_count_baseline`
- `downgrade_count_new`
- `reject_count_baseline`
- `reject_count_new`
- `rule_model_conflict_count_new`
- `decision_changed_count`
- `evidence_quote_valid_count`
- `evidence_quote_invalid_count`

## Recommendation Enum
- `KEEP_DEEPSEEK_FLASH`
- `SWITCH_TO_AI_REVIEW_MODEL`
- `NEED_MORE_PRO_MODEL_TEST`
- `PROMPT_CONTEXT_STILL_TOO_WEAK`

## Recommendation Rules
- Do not switch only because the new model confirms more rows.
- Prefer the new model only if:
  - invalid responses remain low
  - low confidence decreases materially
  - `NEEDS_MORE_CONTEXT` decreases
  - evidence quotes remain grounded
  - deterministic rule conflicts do not increase
  - reasons are still usable for review
- If the new model is more aggressive but less grounded, recommend `NEED_MORE_PRO_MODEL_TEST` or `PROMPT_CONTEXT_STILL_TOO_WEAK`.

## CLI
Create:
- `tools/run_ai_review_model_ab_338b.py`

Arguments:
- `--baseline-338a-dir`
- `--reviewed-strictness-337d-dir`
- `--output-dir`
- `--limit` optional integer, default `50`
- `--dry-run-prompts-only` flag
- `--timeout-seconds` optional integer, default `60`

## Tests
Create:
- `tests/trust/test_ai_review_model_ab_338b.py`

Tests must mock API calls.

Cover:
- `AI_REVIEW_*` preference over `DEEPSEEK_*`
- fallback to `DEEPSEEK_*` when `AI_REVIEW_*` is incomplete
- no key printed or written
- upgraded prompt contains year header context fields
- JSON parsing
- invalid response fallback
- low confidence fallback
- row-aligned comparison
- recommendation logic

## Run
```powershell
python -m py_compile datefac\trust\ai_review_model_ab_338b.py datefac\trust\ai_review_model_ab_338b_report.py tools\run_ai_review_model_ab_338b.py tests\trust\test_ai_review_model_ab_338b.py

python -m pytest tests\trust\test_ai_review_model_ab_338b.py -q

python tools\run_ai_review_model_ab_338b.py --baseline-338a-dir D:\_datefac\output\deepseek_text_adjudicator_338a --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_model_ab_338b --limit 50
```

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
