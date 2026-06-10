# 342M LLM Suggestion Spot-Check Apply Or Real LLM Response Ingestion

## Goal

Build a `342M` sidecar adoption gate on top of completed `342L`.

`342M` must:

- read `342L` simulation outputs
- always generate a human spot-check review template
- always generate a real LLM response schema and ingestion template
- optionally ingest a reviewed human spot-check workbook
- optionally ingest real LLM response jsonl files
- decide whether the next stage can move to `342N`

`342M` remains strictly no-write-back, not client-ready, and not production-ready.

## Required Preflight

Read first:

1. `AGENTS.md`
2. `.skills/README.md`
3. `.skills/git_workflow.md`
4. `.skills/project_milestone_ledger.md`
5. `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
6. `docs/codex_tasks/342L_llm_suggestion_apply_or_human_spot_check_simulation.md`
7. `342L` summary / QA / report / workbook
8. `342K` prompt/request jsonl
9. `342J` summary

## Confirmed Upstream State

Latest real `342L` state:

- `decision = LLM_SUGGESTION_APPLY_SIMULATION_342L_READY`
- `pending_review_count = 1075`
- `auto_confirm_candidate_count = 254`
- `spot_check_sample_count = 50`
- `human_required_count = 717`
- `conflict_count = 763`
- `prefill_review_draft_count = 1075`
- `prompt_pack_count = 358`
- `request_pack_count = 358`
- `jsonl_parse_error_count = 0`
- `theoretical_review_reduction_count = 254`
- `risk_adjusted_reduction_count = 204`
- `required_human_review_after_strategy = 767`
- `ready_for_342m = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Hard Boundaries

Must not:

- rerun `342C6`, `342D`, old `342E`, `342F`, `342G`
- rerun MinerU
- call VLM
- call a real LLM API by default
- fabricate human spot-check results
- fabricate real LLM response files
- treat dry-run suggestions as real LLM outputs
- treat auto-confirm candidates as final confirmations
- write back to `342G` / `342H` / `342I` / `342J` / `342K` / `342L`
- modify production pipeline / parser / extraction / delivery
- claim `client_ready = true`
- claim `production_ready = true`

## Inputs

Required:

- `D:/_datefac/output/llm_suggestion_apply_simulation_342l`
- `D:/_datefac/output/llm_assisted_review_adjudication_342k`
- `D:/_datefac/output/table_first_reviewed_client_preview_pilot_342j`

Optional:

- `D:/_datefac/input/spot_check_reviewed_342m`
- `D:/_datefac/input/llm_review_responses_342m`

## Outputs

Output dir:

- `D:/_datefac/output/llm_suggestion_spot_check_gate_342m`

Output files:

- `llm_suggestion_spot_check_gate_342m.xlsx`
- `llm_suggestion_spot_check_gate_342m_summary.json`
- `llm_suggestion_spot_check_gate_342m_manifest.json`
- `llm_suggestion_spot_check_gate_342m_qa.json`
- `llm_suggestion_spot_check_gate_342m_report.md`
- `llm_suggestion_spot_check_gate_342m_no_write_back_proof.json`
- `llm_suggestion_spot_check_review_template_342m.xlsx`
- `real_llm_response_schema_342m.json`
- `real_llm_response_ingestion_template_342m.jsonl`

Workbook sheets, all `<= 31` chars:

1. `00_README`
2. `01_GATE_SUMMARY`
3. `02_INPUT_342L_SUMMARY`
4. `03_SPOT_CHECK_TEMPLATE`
5. `04_SPOT_CHECK_APPLY`
6. `05_LLM_RESPONSE_SCHEMA`
7. `06_LLM_RESPONSE_INGEST`
8. `07_RULE_LLM_COMPARISON`
9. `08_ADOPTION_POLICY`
10. `09_ADOPTION_CANDIDATES`
11. `10_BLOCKED_CANDIDATES`
12. `11_RISK_GATE`
13. `12_REDUCTION_AFTER_GATE`
14. `13_342N_READINESS`
15. `14_NO_WRITE_BACK`
16. `15_NEXT_STEPS`

## Core Modes

### Mode A: no reviewed spot-check workbook and no real LLM responses

- generate spot-check review template
- generate real LLM response schema/template
- generate gate workbook / summary / report
- `decision = LLM_SUGGESTION_SPOT_CHECK_GATE_342M_WAITING_FOR_EVIDENCE`
- `ready_for_342n = false`
- `qa_fail_count = 0`

### Mode B: reviewed human spot-check workbook exists

- validate `reviewer_decision`
- validate required correction / note fields
- compute pass/fail counts
- do not auto-confirm final outputs
- if validation passes, `decision = LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY`

### Mode C: real LLM response jsonl exists

- validate JSONL parseability
- validate schema
- validate `review_item_id` / `request_id`
- compare to `342K` / `342L` baseline suggestions
- do not auto-confirm final outputs
- if validation passes, `decision = REAL_LLM_RESPONSE_INGESTION_342M_READY`

## Summary Fields

Must include at least:

- `pending_review_count`
- `auto_confirm_candidate_count`
- `spot_check_sample_count`
- `reviewed_spot_check_count`
- `spot_check_confirm_count`
- `spot_check_correct_count`
- `spot_check_reject_count`
- `spot_check_validation_error_count`
- `spot_check_pass_rate`
- `response_count`
- `valid_llm_response_count`
- `jsonl_parse_error_count`
- `schema_validation_error_count`
- `agreement_count`
- `decision_conflict_count`
- `adoption_candidate_count`
- `blocked_candidate_count`
- `risk_adjusted_reduction_count`
- `required_human_review_after_gate`
- `conservative_reduction_rate_after_gate`
- `waiting_for_human_spot_check`
- `waiting_for_real_llm_responses`
- `ready_for_342n`
- `recommended_342n_scope`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count`
- `decision`

## Decision Rules

If critical required inputs are missing:

- `decision = LLM_SUGGESTION_SPOT_CHECK_GATE_342M_NOT_READY`

If no human spot-check evidence and no real LLM response evidence:

- `decision = LLM_SUGGESTION_SPOT_CHECK_GATE_342M_WAITING_FOR_EVIDENCE`

If reviewed spot-check evidence exists and validates:

- `decision = LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY`

If real LLM response evidence exists and validates:

- `decision = REAL_LLM_RESPONSE_INGESTION_342M_READY`

## Report Requirements

Report must say:

- `342M` is an adoption gate, not true auto-apply
- no evidence means waiting state only
- dry-run suggestions are not real LLM outputs
- auto-confirm candidates are not final confirmations
- current state remains `client_ready=false` / `production_ready=false`
- next step is evidence collection or `342N`

## Ledger Update

After completion, update:

- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

If waiting state:

- next recommended task = collect reviewed spot-check workbook or real LLM responses

If ready for `342N`:

- next recommended task = `342N Spot-Check Adoption Simulation Or Real LLM Response Apply`

## Validation

```powershell
python -m py_compile datefac\benchmark\llm_suggestion_spot_check_gate_342m.py datefac\benchmark\llm_suggestion_spot_check_gate_342m_report.py tools\run_llm_suggestion_spot_check_gate_342m.py tests\benchmark\test_llm_suggestion_spot_check_gate_342m.py

python -m pytest tests\benchmark\test_llm_suggestion_spot_check_gate_342m.py -q

python tools\run_llm_suggestion_spot_check_gate_342m.py --llm-suggestion-342l-dir D:\_datefac\output\llm_suggestion_apply_simulation_342l --llm-review-342k-dir D:\_datefac\output\llm_assisted_review_adjudication_342k --reviewed-preview-342j-dir D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j --spot-check-reviewed-dir D:\_datefac\input\spot_check_reviewed_342m --llm-response-dir D:\_datefac\input\llm_review_responses_342m --output-dir D:\_datefac\output\llm_suggestion_spot_check_gate_342m
```
