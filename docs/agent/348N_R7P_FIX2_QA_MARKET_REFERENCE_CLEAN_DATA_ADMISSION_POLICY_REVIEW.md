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

This means:

- `MARKET_REFERENCE_ROW` no longer becomes `INTERNAL_REFERENCE_CANDIDATE`
- the old market-reference clean admission path has been removed
- the policy now matches the current output guardrail contract, which forbids `MARKET_REFERENCE_ROW` in `clean_data`

Also confirmed:

- there is no remaining `MARKET_REFERENCE_ROW -> INTERNAL_REFERENCE_CANDIDATE` path in the policy file
- `row_type_classifier` semantics were not changed
- `output_schema_guardrails` contract was not weakened
- `clean_rows` assembly logic in the runner was not changed; the fix correctly happened in policy rather than assembly

## Test coverage verification

Conclusion: VALID.

Confirmed test coverage includes:

1. `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> REVIEW_REQUIRED`
   - `test_market_reference_weak_evidence_row_now_stays_review_required`

2. `MARKET_REFERENCE_ROW + WEAK_EVIDENCE + unit issue -> REVIEW_REQUIRED`
   - `test_market_reference_weak_evidence_row_with_unit_issue_stays_review_required`

3. Existing routing fixture expectations were updated consistently:
   - `test_clean_candidate_routing_fixture_cases`
   - the fixture case `market_reference_row__becomes_internal_reference_candidate` is now asserted as `REVIEW_REQUIRED`

4. Existing guardrail and routing tests remain present; none were removed or weakened.

Full suite result:

```text
pytest = 76 passed
```

## Taihao pilot rerun verification

Conclusion: VALID.

Rerun command:

```text
python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary"
```

Observed result:

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

The previous blocked error:

```text
clean_data boundary violation ... forbidden row_type 'MARKET_REFERENCE_ROW'
```

did **not** appear in the rerun.

## Output guardrails verification

Conclusion: VALID.

- The previous market-reference clean-data guardrail failure is gone.
- No new guardrail failure appeared in the Taihao pilot rerun.
- The output guardrail contract remains strict: it was not relaxed or bypassed.
- The runner completed normally and wrote a manifest, meaning `validate_outputs(...)` accepted the outputs.

## Boundary check

Conclusion: VALID.

- No source files outside `clean_candidate_policy.py` were modified for the implementation under review.
- No tests outside the targeted test file were modified.
- No legacy `datefac/` files were touched.
- No input files were modified.
- No output artifacts were committed.
- No dependency files were changed.
- No readiness gate semantics changed.
- No export behavior changed.
- No MinerU / OCR / LLM / VLM run.

## Validation commands and results

Commands run:

```text
python -m py_compile datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py
  -> OK

python -m pytest tests\agent -q
  -> 76 passed in 1.33s

python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary"
  -> completed, no previous market-reference guardrail failure

git diff --check
  -> clean
```

## Decision

`348N_R7P_FIX2_QA_CONFIRMED_MARKET_REFERENCE_POLICY_ALIGNMENT_VALID`

R7P-FIX2 correctly aligned policy with the current output guardrail contract: `MARKET_REFERENCE_ROW` no longer becomes `INTERNAL_REFERENCE_CANDIDATE`, tests cover the new behavior, full tests pass, the Taihao rerun no longer hits the previous clean-data guardrail failure, and no new guardrail failure appeared.

## Recommended next task

`348N-R7Q another workbook family pilot review`

Recommended purpose:

- review the Taihao guarded pilot results as a standalone QA/reporting step,
- characterize the new clean/review shape after market-reference alignment,
- decide whether the next action should be:
  - another workbook-family pilot under guardrails, or
  - a narrower design task for future facts-like clean admission categories.

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
