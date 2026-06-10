# 342K LLM-Assisted Review Adjudication Pilot

## Goal

Build a `342K` LLM-assisted review adjudication pilot on top of the completed `342J` reviewed client preview pilot, while defaulting to a no-real-LLM dry-run baseline unless the repository already has an explicit LLM runtime path and the user explicitly asks to use it.

`342K` must:

- read the current real `342J` summary / QA / workbook
- read `342I` sidecar outputs to exclude already human-reviewed rows
- read `342G` review package outputs to reuse the original review queue / template context
- build an LLM candidate pool from still-pending rows only
- generate a rule baseline, prompt package, request package, dry-run suggestions, and a human-review draft template
- remain strictly no-write-back

`342K` must not:

- rerun `342C6` / `342D` / old `342E` / `342F` / `342G`
- rerun MinerU
- call VLM
- call a real LLM API by default
- treat dry-run suggestions as real LLM output
- treat LLM suggestions as final human-review results
- write back to `342G` / `342H` / `342I` / `342J` workbooks
- modify production pipeline / parser / extraction / delivery
- claim `client_ready = true`
- claim `production_ready = true`
- claim full human review completion

## Confirmed Upstream State

Latest real `342J` state:

- `decision = TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY`
- `input_review_template_row_count = 1155`
- `reviewed_row_count = 80`
- `pending_review_count = 1075`
- `reviewed_preview_row_count = 41`
- `confirmed_preview_row_count = 31`
- `corrected_preview_row_count = 10`
- `rejected_in_batch_count = 39`
- `metric_covered_count = 5`
- `metric_year_pair_count = 25`
- `remaining_review_count = 1075`
- `unit_year_remaining_count = 889`
- `duplicate_remaining_count = 348`
- `growth_row_remaining_count = 140`
- `ready_for_342k = true`
- `recommended_342k_scope = llm_assisted_review_adjudication_or_preview_polish`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Inputs

- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i`
- `D:/_datefac/output/table_first_extraction_review_package_342g`

Key input workbooks:

- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j.xlsx`
- `D:/_datefac/output/table_first_post_human_review_sidecar_result_342i/table_first_post_human_review_sidecar_result_342i.xlsx`
- `D:/_datefac/output/table_first_extraction_review_package_342g/table_first_extraction_review_package_342g.xlsx`

## Outputs

Output dir:

- `D:/_datefac/output/llm_assisted_review_adjudication_342k`

Output files:

- `llm_assisted_review_adjudication_342k.xlsx`
- `llm_assisted_review_adjudication_342k_summary.json`
- `llm_assisted_review_adjudication_342k_manifest.json`
- `llm_assisted_review_adjudication_342k_qa.json`
- `llm_assisted_review_adjudication_342k_report.md`
- `llm_assisted_review_adjudication_342k_no_write_back_proof.json`
- `llm_assisted_review_adjudication_342k_prompt_pack.jsonl`
- `llm_assisted_review_adjudication_342k_request_pack.jsonl`

Workbook sheets:

1. `00_README`
2. `01_LLM_REVIEW_SUMMARY`
3. `02_INPUT_342J_SUMMARY`
4. `03_LLM_CANDIDATE_POOL`
5. `04_RULE_BASELINE`
6. `05_PROMPT_PACKAGE`
7. `06_EXPECTED_SCHEMA`
8. `07_DRY_RUN_SUGGESTIONS`
9. `08_HUMAN_REQUIRED`
10. `09_AUTO_CONFIRM_CANDIDATES`
11. `10_CONFLICTS`
12. `11_RISK_BUCKETS`
13. `12_REVIEW_TEMPLATE_DRAFT`
14. `13_342L_READINESS`
15. `14_NO_WRITE_BACK`
16. `15_NEXT_STEPS`

All sheet names must remain `<= 31` chars.

## Core Output Logic

### Input Gates

Must confirm:

- `342J output dir exists`
- `342J summary exists`
- `342J qa exists`
- `342J workbook exists`
- `342J decision = TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY`
- `342J ready_for_342k = true`
- `342J qa_fail_count = 0`
- `342I workbook exists`
- `342G workbook exists`
- `342G workbook includes`
  - `10_REVIEW_TEMPLATE`
  - `03_REVIEW_QUEUE`
  - `04_TRUSTED_AUDIT`
  - `05_UNIT_YEAR_ISSUES`
  - `06_DUPLICATE_ISSUES`
  - `07_GROWTH_ROW_ISSUES`
  - `08_TABLE_TRACE`
- `342I workbook includes`
  - `04_FINAL_CONFIRMED`
  - `05_FINAL_CORRECTED`
  - `06_FINAL_REJECTED`
  - `07_PENDING_REVIEW`

If any key gate fails:

- `decision = LLM_ASSISTED_REVIEW_ADJUDICATION_342K_NOT_READY`
- `ready_for_342l = false`
- do not fabricate misleading LLM suggestions

### Candidate Pool

`03_LLM_CANDIDATE_POOL`

- primarily use `342I 07_PENDING_REVIEW`
- align with `342G 10_REVIEW_TEMPLATE` on `review_item_id`
- exclude:
  - rows already human-reviewed in `342I`
  - rejected / not-core reviewed rows
  - metadata / `BASIC_DATA`
  - excluded tables

Each candidate row must include:

- `review_item_id`
- `review_priority`
- `review_bucket`
- `corpus_pdf_id`
- `file_name`
- `table_id`
- `table_type`
- `source_page`
- `bbox`
- `image_path`
- `metric_raw`
- `metric_standardized`
- `year_raw`
- `year_standardized`
- `value_raw`
- `value_numeric`
- `unit_raw`
- `normalized_unit`
- `extraction_status`
- `review_reason`
- `risk_flags`
- `confidence_signal`
- `source_html_snippet`
- `candidate_reason`
- `llm_route`

Allowed `llm_route`:

- `LLM_UNIT_YEAR_CHECK`
- `LLM_METRIC_MAPPING_CHECK`
- `LLM_DUPLICATE_CHECK`
- `LLM_GROWTH_ROW_CHECK`
- `LLM_SOURCE_TRACE_CHECK`
- `HUMAN_ONLY_HIGH_RISK`

### Rule Baseline

`04_RULE_BASELINE`

Generate deterministic baseline suggestions without calling a real LLM.

Fields:

- `rule_suggested_decision`
- `rule_suggested_metric_standardized`
- `rule_suggested_year_standardized`
- `rule_suggested_value_numeric`
- `rule_suggested_normalized_unit`
- `rule_confidence`
- `rule_reason`
- `rule_human_required`

Important:

- rule baseline is only a suggestion
- it is not a final review result

### Prompt Package

`05_PROMPT_PACKAGE`

Generate prompt package rows for LLM-reviewable candidates.

Each row must include:

- `request_id`
- `review_item_id`
- `prompt_version`
- `system_prompt`
- `user_prompt`
- `evidence_json`
- `expected_schema_name`
- `max_tokens_hint`
- `temperature_hint`

System prompt must clearly state:

- the model is a financial table review assistant
- it can only judge from the provided table evidence
- it must not invent evidence outside the table
- it must not provide investment advice
- it must return JSON only
- if evidence is insufficient it must output `NEEDS_SOURCE_CHECK` or `KEEP_REVIEW_REQUIRED`
- any LLM suggestion is not a final human-review result

### Expected Schema

`06_EXPECTED_SCHEMA`

Define the expected JSON schema:

```json
{
  "review_item_id": "string",
  "llm_suggested_decision": "CONFIRM_CELL | CORRECT_AND_CONFIRM | REJECT_CELL | KEEP_REVIEW_REQUIRED | NOT_A_CORE_METRIC | NEEDS_SOURCE_CHECK",
  "llm_suggested_metric_standardized": "string",
  "llm_suggested_year_standardized": "string",
  "llm_suggested_value_numeric": "number|string|null",
  "llm_suggested_normalized_unit": "string",
  "llm_confidence": "number 0-1",
  "llm_evidence": "string",
  "llm_risk_reason": "string",
  "human_required": "boolean"
}
```

### Dry-Run Suggestions

`07_DRY_RUN_SUGGESTIONS`

Without calling a real LLM, generate deterministic dry-run suggestions from the rule baseline.

Fields:

- `review_item_id`
- `dry_run_suggested_decision`
- `dry_run_suggested_metric_standardized`
- `dry_run_suggested_year_standardized`
- `dry_run_suggested_value_numeric`
- `dry_run_suggested_normalized_unit`
- `dry_run_confidence`
- `dry_run_reason`
- `human_required`
- `can_auto_confirm_candidate`

Important:

- dry-run suggestions must be clearly labeled as `dry_run_*`
- they must not be presented as real LLM output

### Human-Required And Auto-Confirm Candidate Views

`08_HUMAN_REQUIRED`

Collect rows that still must be human-reviewed.

`09_AUTO_CONFIRM_CANDIDATES`

Collect rows that are good auto-confirm candidates, but do not auto-confirm them.

Suggested candidate conditions:

- `rule_confidence >= 0.95`
- source trace complete
- metric / year / value / unit are all complete
- not in high-risk bucket
- no duplicate conflict
- not a critical financial conflict
- `human_required = false`

### Conflicts And Risk Buckets

`10_CONFLICTS`

Record rule conflicts such as:

- metric mismatch
- unit mismatch
- year mismatch
- duplicate conflict
- source trace missing
- `NOT_A_CORE_METRIC` mismatch
- value parse conflict
- suspicious zero value
- growth-row binding conflict

`11_RISK_BUCKETS`

Summarize:

- `unit_year_risk`
- `duplicate_risk`
- `growth_row_risk`
- `source_trace_risk`
- `metric_mapping_risk`
- `high_priority_risk`
- `low_confidence_risk`

### Review Template Draft

`12_REVIEW_TEMPLATE_DRAFT`

Generate a next-stage human + LLM assisted review template draft.

Fields must include:

- `review_item_id`
- `rule_suggested_decision`
- `dry_run_suggested_decision`
- `suggested_metric_standardized`
- `suggested_year_standardized`
- `suggested_value_numeric`
- `suggested_normalized_unit`
- `suggested_confidence`
- `human_required`
- `reviewer_decision`
- `reviewer_metric_standardized`
- `reviewer_year_standardized`
- `reviewer_value_numeric`
- `reviewer_normalized_unit`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`

Human entry fields must remain blank:

- `reviewer_decision`
- `reviewer_metric_standardized`
- `reviewer_year_standardized`
- `reviewer_value_numeric`
- `reviewer_normalized_unit`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`

### 342L Readiness

`13_342L_READINESS`

If:

- `qa_fail_count = 0`
- `llm_candidate_pool_count > 0`
- `prompt_package_count > 0`
- `dry_run_suggestion_count > 0`
- `review_template_draft_count > 0`
- `no_write_back_proof_passed = true`

Then:

- `ready_for_342l = true`
- `recommended_342l_scope = llm_suggestion_apply_or_human_spot_check_simulation`

## Summary Fields

Must include at least:

- `input_review_template_row_count`
- `reviewed_row_count`
- `pending_review_count`
- `llm_candidate_pool_count`
- `prompt_package_count`
- `request_pack_count`
- `rule_baseline_count`
- `dry_run_suggestion_count`
- `human_required_count`
- `auto_confirm_candidate_count`
- `conflict_count`
- `unit_year_risk_count`
- `duplicate_risk_count`
- `growth_row_risk_count`
- `source_trace_risk_count`
- `metric_mapping_risk_count`
- `high_priority_risk_count`
- `review_template_draft_count`
- `ready_for_342l`
- `recommended_342l_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision

If `ready_for_342l = true`:

- `LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY`

Otherwise:

- `LLM_ASSISTED_REVIEW_ADJUDICATION_342K_NOT_READY`

## QA

Must check:

- `342J input exists`
- `342J ready_for_342k = true`
- `342J qa_fail_count = 0`
- `342G / 342I input exists`
- already-reviewed 80 rows are excluded from the LLM candidate pool
- rejected / not-core reviewed rows are excluded from the candidate pool
- prompt package generated
- expected schema generated
- dry-run suggestions are clearly labeled and not presented as real LLM output
- auto-confirm candidates remain candidates only
- human-required rows generated
- review template draft generated with blank reviewer fields
- no upstream workbook modified
- no production pipeline / parser / extraction / delivery modified
- no output artifacts staged
- no reviewed input workbook staged
- no `client_ready = true`
- no `production_ready = true`
- no investment advice claim
- all sheet names `<= 31`
- no-write-back proof generated

## Report

Generate:

- `llm_assisted_review_adjudication_342k_report.md`

The report must state:

- `342K` is an LLM-assisted review adjudication pilot
- by default it only generates LLM request / prompt packages plus rule-baseline dry-run suggestions
- dry-run suggestions are not final LLM output
- LLM suggestions are not human-review results
- `client_ready = false`
- `production_ready = false`
- the goal is to reduce later human review effort
- next step is `342L` suggestion-apply or human spot-check simulation

## Ledger

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

Record:

- `342K` completed
- status
- input
- output
- key metrics
- QA result
- decision
- next recommended task

If `342K ready_for_342l = true`:

- next recommended task = `342L LLM Suggestion Apply Or Human Spot-Check Simulation`

## Validation

```powershell
python -m py_compile datefac\benchmark\llm_assisted_review_adjudication_342k.py datefac\benchmark\llm_assisted_review_adjudication_342k_report.py tools\run_llm_assisted_review_adjudication_342k.py tests\benchmark\test_llm_assisted_review_adjudication_342k.py

python -m pytest tests\benchmark\test_llm_assisted_review_adjudication_342k.py -q

python tools\run_llm_assisted_review_adjudication_342k.py --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --post-human-review-342i-dir D:\_datefac\output\table_first_post_human_review_sidecar_result_342i --review-package-342g-dir D:\_datefac\output\table_first_extraction_review_package_342g --output-dir D:\_datefac\output\llm_assisted_review_adjudication_342k
```
