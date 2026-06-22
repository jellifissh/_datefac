## Task ID

`348N-R7P-FIX2-QA Market Reference Clean Data Admission Policy Review`

## Reviewed files

Read-only review:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md`
- `docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md`
- `docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md`
- `datefac_agent/review/clean_candidate_policy.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json` (read-only)

## Policy behavior verification

Conclusion: VALID.

Confirmed in `datefac_agent/review/clean_candidate_policy.py`:

```python
if result.row_type == "MARKET_REFERENCE_ROW":
    return "REVIEW_REQUIRED"
```

This confirms:

- `MARKET_REFERENCE_ROW` is now routed to `REVIEW_REQUIRED`
- there is no path in `clean_candidate_policy.py` that still returns `INTERNAL_REFERENCE_CANDIDATE` for `MARKET_REFERENCE_ROW`
- the fix happened in policy, not in row typing or runner assembly

Also confirmed:

- `row_type_classifier` semantics were not changed in this QA scope
- `output_schema_guardrails` contract was not weakened
- `clean_rows` assembly in `tools/run_agent_excel_intake_audit_348a.py` remains unchanged and still includes only `INTERNAL_CLEAN_CANDIDATE` / `INTERNAL_REFERENCE_CANDIDATE`; therefore the policy change is the effective fix layer

## Test coverage verification

Conclusion: VALID.

Confirmed tests cover both required behaviors:

1. `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> REVIEW_REQUIRED`
   - `test_market_reference_weak_evidence_row_now_stays_review_required`

2. `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + unit issue -> REVIEW_REQUIRED`
   - `test_market_reference_weak_evidence_row_with_unit_issue_stays_review_required`

Also confirmed:

- existing routing fixture expectations were updated consistently in `test_clean_candidate_routing_fixture_cases`
- no previous guardrail tests were removed or weakened
- the full agent suite passes

## Taihao pilot rerun verification

Conclusion: VALID.

Rerun command:

```text
python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary"
```

Observed manifest values:

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
market_reference_row_count = 2
normalized_testset_record_row_count = 0
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

The prior failure:

```text
clean_data boundary violation ... forbidden row_type 'MARKET_REFERENCE_ROW'
```

no longer appeared.

## Output guardrails verification

Conclusion: VALID.

- The previous guardrail failure is fixed.
- No new guardrail failure appeared during the Taihao rerun.
- `validate_outputs(...)` still ran before manifest write, because the runner completed only after producing a valid manifest.
- The output guardrails contract remains strict; it was not bypassed or relaxed.

## Boundary check

Conclusion: VALID.

- No source code was modified by this QA task.
- No tests were modified by this QA task.
- No dependency files were modified.
- No input files were modified.
- No output artifacts were committed.
- No legacy `datefac/` files were touched.
- No readiness gates were changed.
- No export behavior was changed.
- No MinerU / OCR / LLM / VLM calls were made.

## Validation commands and results

```text
python -m py_compile datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py
  -> OK

python -m pytest tests\agent -q
  -> 76 passed in 0.51s

python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary"
  -> completed successfully with no market-reference clean-data guardrail failure

git diff --check
  -> clean
```

## Decision

`348N_R7P_FIX2_QA_CONFIRMED_MARKET_REFERENCE_POLICY_ALIGNMENT_VALID`

The FIX2 policy alignment is independently confirmed valid: `MARKET_REFERENCE_ROW` no longer becomes `INTERNAL_REFERENCE_CANDIDATE`, tests cover the intended behavior, the full suite passes, the previous Taihao guardrail failure is gone, and no new guardrail failure appeared.

## Recommended next task

`348N-R7Q another workbook family pilot review`

Purpose:

- review the Taihao guarded pilot as a standalone result,
- characterize the new clean/review shape after market-reference alignment,
- decide whether to run another workbook-family pilot or revisit a narrower future clean-admission design.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7P_FIX2_QA_CONFIRMED_MARKET_REFERENCE_POLICY_ALIGNMENT_VALID
market_reference_policy_valid（market reference 策略是否有效）= yes
market_reference_internal_reference_candidate_allowed（是否仍允许 MARKET_REFERENCE_ROW -> INTERNAL_REFERENCE_CANDIDATE）= no
pytest_result（测试结果）= 76 passed
taihao_pilot_rerun（泰豪 pilot 重跑）= completed
previous_market_reference_guardrail_failure_fixed（此前 MARKET_REFERENCE_ROW clean_data guardrail failure 是否消失）= yes
new_guardrail_failure（是否出现新 guardrail failure）= no
code_changes_made（是否改代码）= no
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R7Q another workbook family pilot review
```
