# 338C Grounded AI Review Schema Tightening

## Goal
- Tighten the 338B grounded evidence rules for AI review dry-run adjudication.
- Split raw evidence quote and supporting context quote into separate schema fields.
- Re-run the same 50 adjudication rows with the AI review model.
- Keep this stage sidecar only and do not write back to 337D.

## Scope
- New sidecar trust code only.
- New runner only.
- New tests only.
- New task doc only.
- Do not modify production pipeline, parser, extraction, delivery behavior, official assets, or 337D / 338A / 338B outputs in place.
- Do not commit generated output artifacts.

## Inputs
- `D:/_datefac/output/ai_review_model_ab_338b`
- `D:/_datefac/output/ai_review_model_ab_338b/ai_review_model_ab_338b_plan.xlsx`
- `D:/_datefac/output/deepseek_text_adjudicator_338a`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/reviewed_strictness_year_alignment_337d_before_after.xlsx`

## Output Dir
- `D:/_datefac/output/grounded_ai_review_338c`

## Expected Artifacts
- `grounded_ai_review_338c_summary.json`
- `grounded_ai_review_338c_manifest.json`
- `grounded_ai_review_338c_qa.json`
- `grounded_ai_review_338c_report.md`
- `grounded_ai_review_338c_plan.xlsx`
- `grounded_ai_review_338c_cache.jsonl`
- `grounded_ai_review_338c_prompt_preview.jsonl`

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
- Never commit `.env`.
- Only report `SET` / `MISSING` for key variables.
- Report model name only.

## Core Schema Change
Replace the old single quote field with:

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
  "raw_evidence_quote": "short quote copied only from the original evidence field",
  "supporting_context_quote": "short quote copied only from table headers / nearby rows / route context, or null",
  "grounding_source": "RAW_EVIDENCE | SUPPORTING_CONTEXT | BOTH | INSUFFICIENT"
}
```

## Validation Rules
- JSON must parse.
- `decision` must be a valid enum.
- `confidence` must be between `0` and `1`.
- `raw_evidence_quote` must be grounded in the original `evidence` field when provided.
- `supporting_context_quote` must be grounded in the expanded supporting context when provided.
- `grounding_source` must match available valid quotes:
  - `RAW_EVIDENCE` requires valid raw quote
  - `SUPPORTING_CONTEXT` requires valid context quote
  - `BOTH` requires both valid
  - `INSUFFICIENT` means confirm cannot be accepted
- `CONFIRM_REVIEWED` should only be accepted if `grounding_source` is `RAW_EVIDENCE` or `BOTH`.
- If confirmation relies only on `SUPPORTING_CONTEXT`, final action should usually become `NEEDS_MORE_CONTEXT` unless deterministic row fields already fully agree.
- Invalid quote or invalid grounding source must produce:
  - `model_decision_status = INVALID_RESPONSE`
  - `recommended_final_action = NEEDS_MORE_CONTEXT`

## Prompt Rules
- The model may use table headers and nearby rows as supporting context.
- It must not place supporting context into `raw_evidence_quote`.
- It must not invent quotes.
- If raw evidence and supporting context conflict, choose `NEEDS_MORE_CONTEXT`.
- It must not provide investment advice.
- It must only judge the provided row.

## Deterministic Guards
Keep all 338B guards:
- `revenue` / `net_profit` cannot have unit `%`
- `revenue` / `net_profit` cannot have value containing `%`
- reviewed `revenue` / `net_profit` rows must have money unit
- `PE` / `PB` unit should be `倍`
- `EPS` unit should be `元`
- `ROE` / `gross_margin` / `net_margin` / `revenue_yoy` / `net_profit_yoy` unit should be `%`
- legal / rating / disclosure rows cannot be confirmed reviewed
- AI model cannot override deterministic hard rejects

## Adoption Threshold For Accepted Confirm
`recommended_final_action = CONFIRM_REVIEWED` only if:
- model decision is `CONFIRM_REVIEWED`
- `confidence >= 0.80`
- `grounding_source` is `RAW_EVIDENCE` or `BOTH`
- deterministic guard is `PASS`
- no invalid quote
- no legal / rating / disclosure role

Otherwise downgrade to `NEEDS_MORE_CONTEXT` or keep the safer route.

## Workbook
`grounded_ai_review_338c_plan.xlsx`

Sheets:
1. `00_README`
2. `01_GROUNDED_SUMMARY`
3. `02_GROUNDED_ADJUDICATION_PLAN`
4. `03_338B_COMPARISON`
5. `04_CHANGED_AFTER_GROUNDING`
6. `05_INVALID_OR_UNGROUNDED`
7. `06_CONFIRM_REVIEWED_CANDIDATES`
8. `07_NEEDS_MORE_CONTEXT_AFTER_GROUNDING`
9. `08_RULE_MODEL_CONFLICTS`
10. `09_PROMPT_AND_SCHEMA_NOTES`
11. `10_CACHE_AND_COST_SUMMARY`

## Comparison Metrics
- `invalid_response_count_338b`
- `invalid_response_count_338c`
- `confirm_reviewed_count_338b`
- `confirm_reviewed_count_338c`
- `needs_more_context_count_338b`
- `needs_more_context_count_338c`
- `raw_quote_valid_count`
- `context_quote_valid_count`
- `grounding_source_counts`
- `confirm_with_raw_evidence_count`
- `confirm_with_both_count`
- `confirm_with_context_only_count`
- `confirm_rejected_by_grounding_count`
- `rule_model_conflict_count`
- `final_recommendation`

## Final Recommendation Enum
- `SWITCH_TO_AI_REVIEW_MODEL`
- `KEEP_DEEPSEEK_FLASH`
- `NEED_MORE_PRO_MODEL_TEST`
- `GROUNDING_STILL_TOO_WEAK`
- `PROMPT_CONTEXT_STILL_TOO_WEAK`

## Recommendation Rules
Recommend `SWITCH_TO_AI_REVIEW_MODEL` only if:
- invalid responses are zero or very low
- low confidence remains low
- `NEEDS_MORE_CONTEXT` remains materially below the DeepSeek flash baseline
- accepted confirms are grounded in `RAW_EVIDENCE` or `BOTH`
- deterministic conflicts do not increase
- sampled reasons remain useful and conservative

Do not recommend switch if:
- many confirms depend on context-only grounding
- quote grounding is weak
- invalid responses remain material
- the model is aggressive without evidence

## CLI
Create:
- `tools/run_grounded_ai_review_338c.py`

Arguments:
- `--ab-338b-dir`
- `--reviewed-strictness-337d-dir`
- `--output-dir`
- `--limit` optional integer, default `50`
- `--dry-run-prompts-only` flag
- `--timeout-seconds` optional integer, default `60`

## Tests
Create:
- `tests/trust/test_grounded_ai_review_338c.py`

Tests must mock API calls.

Cover:
- raw evidence quote validation
- supporting context quote validation
- grounding source validation
- context-only confirm downgrade behavior
- deterministic guard priority
- invalid JSON fallback
- invalid quote fallback
- recommendation logic
- workbook generation

## Run
```powershell
python -m py_compile datefac\trust\grounded_ai_review_338c.py datefac\trust\grounded_ai_review_338c_report.py tools\run_grounded_ai_review_338c.py tests\trust\test_grounded_ai_review_338c.py

python -m pytest tests\trust\test_grounded_ai_review_338c.py -q

python tools\run_grounded_ai_review_338c.py --ab-338b-dir D:\_datefac\output\ai_review_model_ab_338b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\grounded_ai_review_338c --limit 50
```

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
