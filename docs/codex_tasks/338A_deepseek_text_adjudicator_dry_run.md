# 338A DeepSeek Text Adjudicator Dry Run

## Goal
- Add a sidecar DeepSeek-based text adjudicator on top of 337D.
- Read 337D suspicious rows and needs-review rows.
- Produce a dry-run adjudication plan only.
- Use text evidence only, not images, not PDF rendering, not write-back.

## Scope
- New sidecar trust code only.
- New runner only.
- New tests only.
- New task doc only.
- Do not modify production pipeline, parser, extraction, delivery behavior, official assets, or 337D outputs in place.
- Do not commit generated output artifacts.

## Environment Variables
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`

## Security Rules
- Never print `DEEPSEEK_API_KEY`.
- Never write `DEEPSEEK_API_KEY` to output files.
- Never include the API key in logs.
- Never commit `.env` files.
- If `DEEPSEEK_API_KEY` is missing:
  - do not crash
  - generate a blocked summary
  - still allow prompt-preview generation

## Inputs
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/reviewed_strictness_year_alignment_337d_before_after.xlsx`
- `D:/_datefac/input/real_test`

## Output Dir
- `D:/_datefac/output/deepseek_text_adjudicator_338a`

## Expected Artifacts
- `deepseek_text_adjudicator_338a_summary.json`
- `deepseek_text_adjudicator_338a_manifest.json`
- `deepseek_text_adjudicator_338a_qa.json`
- `deepseek_text_adjudicator_338a_report.md`
- `deepseek_text_adjudication_plan_338a.xlsx`
- `deepseek_text_adjudication_cache_338a.jsonl`
- `deepseek_text_adjudication_prompts_preview_338a.jsonl`

## Rows To Adjudicate
1. All rows from `08_SUSPICIOUS_REVIEWED_AUDIT`
2. All rows from `02_NEEDS_REVIEW`
3. Optionally high-risk reviewed rows from `H3_AP202606081823356439_1.pdf`

Default runtime must cap API calls with `--limit 50`.

## Evidence Payload
Only send compact text evidence:
- `document`
- `metric`
- `metric_display_zh`
- `year`
- `value`
- `unit`
- `source_page`
- `status before adjudication`
- `source_evidence_excerpt`
- `suspicious_reason`
- `notes`
- nearby route-change context when available

Do not send whole PDFs and do not send images.

## Prompt Rules
- DeepSeek must judge only from provided evidence.
- It must not invent data.
- It must not use outside knowledge.
- It must not provide investment advice.
- It must return strict JSON only.

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

## Response Validation
- JSON must parse.
- `decision` must be in the allowed enum.
- `confidence` must be between `0` and `1`.
- `evidence_quote` must be a substring or close excerpt from provided evidence.
- Invalid response:
  - `model_decision_status = INVALID_RESPONSE`
  - `recommended_final_action = NEEDS_MORE_CONTEXT`
- If `confidence < 0.70`:
  - `recommended_final_action = NEEDS_MORE_CONTEXT`
- If DeepSeek suggests `CONFIRM_REVIEWED` but deterministic rules disagree:
  - deterministic rule wins
  - mark rule/model conflict

## Deterministic Safety Rules
- `revenue` / `net_profit` cannot have unit `%`
- `revenue` / `net_profit` cannot have value containing `%`
- reviewed `revenue` / `net_profit` rows must have money unit
- `PE` / `PB` unit should be `倍`
- `EPS` unit should be `元`
- `ROE` / `gross_margin` / `net_margin` / `revenue_yoy` / `net_profit_yoy` unit should be `%`
- legal / rating / disclosure rows cannot be confirmed reviewed
- DeepSeek cannot override deterministic hard rejects

## Workbook
`deepseek_text_adjudication_plan_338a.xlsx`

Sheets:
1. `00_README`
2. `01_ADJUDICATION_SUMMARY`
3. `02_MODEL_ADJUDICATION_PLAN`
4. `03_PROMPT_PREVIEW`
5. `04_INVALID_OR_LOW_CONFIDENCE`
6. `05_RULE_MODEL_CONFLICTS`
7. `06_COST_AND_CACHE_SUMMARY`

## 02_MODEL_ADJUDICATION_PLAN Required Columns
- `adjudication_id`
- `document`
- `source_sheet`
- `source_row_no`
- `metric_before`
- `year_before`
- `value_before`
- `unit_before`
- `evidence`
- `suspicious_reason`
- `model_decision`
- `suggested_metric`
- `suggested_year`
- `suggested_value`
- `suggested_unit`
- `table_role_guess`
- `confidence`
- `risk_flags`
- `reason`
- `evidence_quote`
- `deterministic_guard_result`
- `recommended_final_action`
- `model_name`
- `prompt_hash`
- `cache_hit`

## Cache Key
Use:
- `prompt_version`
- `document`
- `metric/year/value/unit`
- evidence text hash
- suspicious reason

If cache exists, reuse it and mark `cache_hit = true`.

## CLI
Create:
- `tools/run_deepseek_text_adjudicator_338a.py`

Arguments:
- `--reviewed-strictness-337d-dir`
- `--output-dir`
- `--limit` optional integer, default `50`
- `--dry-run-prompts-only` flag
- `--timeout-seconds` optional, default `60`

## Prompt-Only Mode
If `--dry-run-prompts-only`:
- do not call API
- only generate prompt preview and blocked/dry-run summary

## Tests
Create:
- `tests/trust/test_deepseek_text_adjudicator_338a.py`

Tests must avoid real API calls and use mocked responses.

Test:
- prompt construction
- JSON parsing
- invalid JSON handling
- deterministic guard priority
- low-confidence fallback
- cache key stability
- workbook generation with mocked rows

## Run
```powershell
python -m py_compile datefac\trust\deepseek_text_adjudicator_338a.py datefac\trust\deepseek_text_adjudicator_338a_report.py tools\run_deepseek_text_adjudicator_338a.py tests\trust\test_deepseek_text_adjudicator_338a.py

python -m pytest tests\trust\test_deepseek_text_adjudicator_338a.py -q

python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50
```

Prompt-only fallback:
```powershell
python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50 --dry-run-prompts-only
```

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
