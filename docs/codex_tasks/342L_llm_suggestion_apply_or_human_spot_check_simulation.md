# 342L LLM Suggestion Apply Or Human Spot-Check Simulation

## Goal

Build a `342L` sidecar that reads the completed `342K` LLM-assisted adjudication pilot and turns it into:

- a suggestion-apply simulation
- a mandatory human spot-check package
- a prefilled review draft for the next stage

`342L` must remain strictly no-write-back and must not claim real LLM execution, real human confirmation, client-ready delivery, or production readiness.

## Required Preflight

Read first:

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. `docs/codex_tasks/342K_llm_assisted_review_adjudication_pilot.md`
7. `342K` output summary / QA / report / workbook / prompt pack / request pack
8. `342J` output summary / QA / workbook for current preview boundaries

## Confirmed Upstream State

Latest real `342K` state:

- `decision = LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY`
- `pending_review_count = 1075`
- `llm_candidate_pool_count = 1075`
- `prompt_package_count = 358`
- `request_pack_count = 358`
- `rule_baseline_count = 1075`
- `dry_run_suggestion_count = 1075`
- `human_required_count = 717`
- `auto_confirm_candidate_count = 254`
- `conflict_count = 763`
- `unit_year_risk_count = 577`
- `duplicate_risk_count = 348`
- `growth_row_risk_count = 152`
- `source_trace_risk_count = 498`
- `metric_mapping_risk_count = 309`
- `ready_for_342l = true`
- `recommended_342l_scope = llm_suggestion_apply_or_human_spot_check_simulation`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Boundaries

Must not:

- rerun `342C6` / `342D` / old `342E` / `342F` / `342G`
- rerun MinerU
- call VLM
- call a real LLM API by default
- treat 342K dry-run suggestions as real LLM responses
- treat 342K auto-confirm candidates as final confirmations
- write back to `342G` / `342H` / `342I` / `342J` / `342K`
- modify production pipeline / parser / extraction / delivery
- generate a formal client export
- claim `client_ready = true`
- claim `production_ready = true`
- claim full human review completion

## Inputs

- `D:/_datefac/output/llm_assisted_review_adjudication_342k`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Key input files:

- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k.xlsx`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_summary.json`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_qa.json`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_prompt_pack.jsonl`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k/llm_assisted_review_adjudication_342k_request_pack.jsonl`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j/table_first_reviewed_client_preview_pilot_342j_summary.json`

## Outputs

Output dir:

- `D:/_datefac/output/llm_suggestion_apply_simulation_342l`

Output files:

- `llm_suggestion_apply_simulation_342l.xlsx`
- `llm_suggestion_apply_simulation_342l_summary.json`
- `llm_suggestion_apply_simulation_342l_manifest.json`
- `llm_suggestion_apply_simulation_342l_qa.json`
- `llm_suggestion_apply_simulation_342l_report.md`
- `llm_suggestion_apply_simulation_342l_no_write_back_proof.json`

Workbook sheets, all `<= 31` chars:

1. `00_README`
2. `01_SIM_SUMMARY`
3. `02_INPUT_342K_SUMMARY`
4. `03_AUTO_CANDIDATES`
5. `04_SPOT_CHECK_SAMPLE`
6. `05_PREFILL_REVIEW_DRAFT`
7. `06_HUMAN_REQUIRED`
8. `07_CONFLICT_BLOCKERS`
9. `08_REDUCTION_SIMULATION`
10. `09_RISK_AUDIT`
11. `10_PROMPT_REQUEST_TRACE`
12. `11_DECISION_POLICY`
13. `12_342M_READINESS`
14. `13_NO_WRITE_BACK`
15. `14_NEXT_STEPS`

## Core Logic

### Input Gates

Must confirm:

- `342K output dir exists`
- `342K summary exists`
- `342K qa exists`
- `342K workbook exists`
- `342K prompt_pack.jsonl exists`
- `342K request_pack.jsonl exists`
- `342K decision = LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY`
- `342K ready_for_342l = true`
- `342K qa_fail_count = 0`
- `342K workbook includes`
  - `03_LLM_CANDIDATE_POOL`
  - `04_RULE_BASELINE`
  - `05_PROMPT_PACKAGE`
  - `06_EXPECTED_SCHEMA`
  - `07_DRY_RUN_SUGGESTIONS`
  - `08_HUMAN_REQUIRED`
  - `09_AUTO_CONFIRM_CANDIDATES`
  - `10_CONFLICTS`
  - `11_RISK_BUCKETS`
  - `12_REVIEW_TEMPLATE_DRAFT`
  - `13_342L_READINESS`
  - `14_NO_WRITE_BACK`

If any required input fails:

- `decision = LLM_SUGGESTION_APPLY_SIMULATION_342L_NOT_READY`
- `ready_for_342m = false`
- do not fabricate misleading suggestion-apply outputs

### Auto Candidates

Read `342K 09_AUTO_CONFIRM_CANDIDATES` and enrich with source evidence from the candidate pool / rule baseline.

Must keep:

- `review_item_id`
- `rule_suggested_decision`
- `dry_run_suggested_decision`
- `suggested_metric_standardized`
- `suggested_year_standardized`
- `suggested_value_numeric`
- `suggested_normalized_unit`
- `suggested_confidence`
- `human_required`
- `candidate_reason`
- `risk_flags`
- `review_reason`
- `source_page`
- `bbox`
- `image_path`
- `source_html_snippet`

Must mark only:

- `simulation_status = AUTO_CONFIRM_CANDIDATE`
- `not_final_confirmation = true`

Never turn them into:

- `HUMAN_CONFIRMED_CELL`
- `POST_HUMAN_CONFIRMED`
- `client_ready`

### Spot-Check Sample

Build a human spot-check sample from auto-confirm candidates.

Sampling policy:

- at least one sample per `metric_standardized` where practical
- at least one sample per `table_type` where practical
- cover each `corpus_pdf_id` where practical
- prioritize value classes like percentages / multiples / negatives / high-value financial metrics
- weak source-trace candidates must be sampled
- unit-year / duplicate / growth risk candidates must be sampled
- default sample size = `min(50, auto_confirm_candidate_count)`
- if auto-confirm count `< 50`, sample all of them

Keep reviewer fields blank:

- `reviewer_decision`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`

### Prefill Review Draft

Generate a prefilled draft from `342K 12_REVIEW_TEMPLATE_DRAFT`.

Prefill only suggestion fields, not human fields.

Must preserve blank reviewer fields:

- `reviewer_decision`
- `reviewer_metric_standardized`
- `reviewer_year_standardized`
- `reviewer_value_numeric`
- `reviewer_normalized_unit`
- `reviewer_note`
- `reviewer_id`
- `reviewed_at`

### Human Required

Read `342K 08_HUMAN_REQUIRED`.

All human-required rows must remain outside any auto-apply simulation.

Add:

- `human_required_reason`
- `risk_bucket`
- `conflict_type`
- `suggested_decision`
- `recommended_human_action`

### Conflict Blockers

Read `342K 10_CONFLICTS`.

Every conflict must become a blocker with:

- `blocker_severity = HIGH | MEDIUM | LOW`
- `auto_apply_allowed = false`
- `human_required = true`

Conflict classes:

- `METRIC_CONFLICT`
- `UNIT_CONFLICT`
- `YEAR_CONFLICT`
- `DUPLICATE_CONFLICT`
- `GROWTH_ROW_CONFLICT`
- `SOURCE_TRACE_MISSING`
- `VALUE_PARSE_CONFLICT`
- `SUSPICIOUS_ZERO_VALUE`
- `CORE_METRIC_HIGH_RISK`

### Reduction Simulation

Compute:

- `original_pending_review_count = 1075`
- `auto_confirm_candidate_count`
- `spot_check_sample_count`
- `human_required_count`
- `conflict_count`
- `theoretical_review_reduction_count`
- `required_human_review_after_strategy`
- `reduction_rate`
- `conservative_reduction_rate`
- `risk_adjusted_reduction_count`

Rules:

- `theoretical_review_reduction_count = auto_confirm_candidate_count`
- `required_human_review_after_strategy = human_required_count + spot_check_sample_count`
- `risk_adjusted_reduction_count = auto_confirm_candidate_count - spot_check_sample_count`
- `conservative_reduction_rate = risk_adjusted_reduction_count / original_pending_review_count`

Important:

- do not claim any row is truly confirmed
- only claim “possible reduction of human review workload under simulation”

### Prompt / Request Trace

Parse `prompt_pack.jsonl` and `request_pack.jsonl`.

Must prove:

- both files exist
- each line can be parsed by `json.loads`
- `request_id` and `review_item_id` remain traceable

### 342M Readiness

If:

- `qa_fail_count = 0`
- `auto_confirm_candidate_count > 0`
- `spot_check_sample_count > 0`
- `prefill_review_draft_count > 0`
- prompt/request trace is valid
- `no_write_back_proof_passed = true`

Then:

- `ready_for_342m = true`
- `recommended_342m_scope = llm_suggestion_spot_check_apply_or_real_llm_response_ingestion`

Else:

- `ready_for_342m = false`

## Summary Fields

Must include at least:

- `pending_review_count`
- `auto_confirm_candidate_count`
- `spot_check_sample_count`
- `human_required_count`
- `conflict_count`
- `prefill_review_draft_count`
- `prompt_pack_count`
- `request_pack_count`
- `jsonl_parse_error_count`
- `theoretical_review_reduction_count`
- `risk_adjusted_reduction_count`
- `required_human_review_after_strategy`
- `reduction_rate`
- `conservative_reduction_rate`
- `unit_year_risk_count`
- `duplicate_risk_count`
- `growth_row_risk_count`
- `source_trace_risk_count`
- `metric_mapping_risk_count`
- `ready_for_342m`
- `recommended_342m_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision

If `ready_for_342m = true`:

- `LLM_SUGGESTION_APPLY_SIMULATION_342L_READY`

Otherwise:

- `LLM_SUGGESTION_APPLY_SIMULATION_342L_NOT_READY`

## QA

Must check:

- `342K` input exists
- `342K ready_for_342l = true`
- `342K qa_fail_count = 0`
- auto-confirm candidates remain candidates, not confirmations
- human-required rows are not auto-applied
- conflict blockers are not auto-applied
- reviewer fields stay blank in the prefill draft
- spot-check sample generated
- reduction simulation generated
- prompt/request jsonl parsed successfully
- no fake real LLM response generated
- dry-run suggestions stay clearly labeled
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

- `llm_suggestion_apply_simulation_342l_report.md`

The report must state:

- `342L` is a suggestion-apply simulation, not a real LLM apply
- dry-run suggestions are not actual LLM outputs
- auto-confirm candidates are not final confirmations
- human spot-check is still mandatory before any broader adoption
- `client_ready = false`
- `production_ready = false`
- the value of 342L is estimating review reduction and producing spot-check / prefill artifacts
- next step is `342M`

## Ledger

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If `ready_for_342m = true`:

- next recommended task = `342M LLM Suggestion Spot-Check Apply Or Real LLM Response Ingestion`

## Validation

```powershell
python -m py_compile datefac\benchmark\llm_suggestion_apply_simulation_342l.py datefac\benchmark\llm_suggestion_apply_simulation_342l_report.py tools\run_llm_suggestion_apply_simulation_342l.py tests\benchmark\test_llm_suggestion_apply_simulation_342l.py

python -m pytest tests\benchmark\test_llm_suggestion_apply_simulation_342l.py -q

python tools\run_llm_suggestion_apply_simulation_342l.py --llm-review-342k-dir D:\_datefac\output\llm_assisted_review_adjudication_342k --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --output-dir D:\_datefac\output\llm_suggestion_apply_simulation_342l
```
