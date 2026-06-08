# 338D AI Review Adoption Simulation

## Goal
- Simulate a safe dry-run adoption policy on top of 338C grounded AI review results.
- Decide which model recommendations are safe to accept, which must stay in human review, and which are rejected by deterministic rules.
- Do not write back to 337D or any upstream workbook.

## Scope
- New sidecar trust code only.
- New runner only.
- New tests only.
- New task doc only.
- Do not modify production pipeline, parser, extraction, delivery behavior, official assets, or 337D / 338A / 338B / 338C outputs in place.
- Do not commit generated output artifacts.

## Inputs
- `D:/_datefac/output/grounded_ai_review_338c`
- `D:/_datefac/output/grounded_ai_review_338c/grounded_ai_review_338c_plan.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx`

## Output Dir
- `D:/_datefac/output/ai_review_adoption_simulation_338d`

## Expected Artifacts
- `ai_review_adoption_simulation_338d_summary.json`
- `ai_review_adoption_simulation_338d_manifest.json`
- `ai_review_adoption_simulation_338d_qa.json`
- `ai_review_adoption_simulation_338d_report.md`
- `ai_review_adoption_simulation_338d_plan.xlsx`

## Adoption Actions
- `ACCEPT_MODEL_CONFIRM`
- `ACCEPT_MODEL_DOWNGRADE`
- `ACCEPT_MODEL_REJECT`
- `HOLD_FOR_HUMAN_REVIEW`
- `REJECT_BY_DETERMINISTIC_RULE`
- `INVALID_MODEL_RESPONSE`

## Adoption Rules
### Confirm
Accept `CONFIRM_REVIEWED` only if:
- `model_decision = CONFIRM_REVIEWED`
- `confidence >= 0.80`
- `grounding_source` is `RAW_EVIDENCE` or `BOTH`
- `raw_quote_valid = true`
- `context_quote_valid = true` if `grounding_source = BOTH`
- `deterministic_guard_result = PASS`
- no legal / rating / disclosure role
- metric / year / value / unit are complete
- if `grounding_source = BOTH`, table year headers or equivalent context exists

### Downgrade
Accept `DOWNGRADE_TO_NEEDS_REVIEW` if:
- `model_decision = DOWNGRADE_TO_NEEDS_REVIEW`
- `confidence >= 0.70`
- reason and risk flags are grounded enough for routing
- deterministic rules do not contradict

### Reject
Accept `REJECT` only if:
- `model_decision = REJECT`
- `confidence >= 0.80`
- evidence or supporting context clearly marks legal / rating / disclosure / noise / duplicate / non-financial status
- or deterministic guard already rejects it

### Needs More Context
- `NEEDS_MORE_CONTEXT` always becomes `HOLD_FOR_HUMAN_REVIEW`

### Invalid
- invalid model response always becomes `INVALID_MODEL_RESPONSE`
- invalid rows still require human review

## Workbook
`ai_review_adoption_simulation_338d_plan.xlsx`

Sheets:
1. `00_README`
2. `01_ADOPTION_SUMMARY`
3. `02_ADOPTION_PLAN`
4. `03_ACCEPTED_CONFIRMS`
5. `04_ACCEPTED_DOWNGRADES`
6. `05_ACCEPTED_REJECTS`
7. `06_HOLD_FOR_HUMAN_REVIEW`
8. `07_REJECTED_BY_RULE`
9. `08_INVALID_MODEL_RESPONSES`
10. `09_ADOPTION_POLICY_NOTES`

## Required Columns
- `adoption_id`
- `adjudication_id`
- `document`
- `source_sheet`
- `source_row_no`
- `metric_before`
- `year_before`
- `value_before`
- `unit_before`
- `model_decision`
- `confidence`
- `grounding_source`
- `raw_quote_valid`
- `context_quote_valid`
- `deterministic_guard_result`
- `adoption_action`
- `adoption_reason`
- `recommended_route_after_adoption`
- `human_review_required`
- `model_name`

## QA Requirements
- input 338C workbook exists
- exactly 50 rows are represented
- no invalid model response is accepted
- no low-confidence confirm is accepted
- no legal / rating / disclosure row is accepted as reviewed
- no deterministic hard reject is overridden by model
- accepted confirm count <= 338C confirm count
- hold-for-human-review rows are preserved
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Run
```powershell
python -m py_compile datefac\trust\ai_review_adoption_simulation_338d.py datefac\trust\ai_review_adoption_simulation_338d_report.py tools\run_ai_review_adoption_simulation_338d.py tests\trust\test_ai_review_adoption_simulation_338d.py

python -m pytest tests\trust\test_ai_review_adoption_simulation_338d.py -q

python tools\run_ai_review_adoption_simulation_338d.py --grounded-ai-review-338c-dir D:\_datefac\output\grounded_ai_review_338c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_adoption_simulation_338d
```

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`
