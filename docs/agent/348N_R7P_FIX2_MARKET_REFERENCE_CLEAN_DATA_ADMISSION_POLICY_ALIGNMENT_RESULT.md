## Task ID

`348N-R7P-FIX2 Market Reference Clean Data Admission Policy Alignment`

## Files modified

- `datefac_agent/review/clean_candidate_policy.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md`

No other source, dependency, input, output, legacy, or historical report files were modified.

## Policy change

Implemented the tiny policy alignment required by R7P-FIX root-cause diagnosis.

Before:

```text
MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> INTERNAL_REFERENCE_CANDIDATE
```

After:

```text
MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
```

Current code change in `datefac_agent/review/clean_candidate_policy.py`:

```python
if result.row_type == "MARKET_REFERENCE_ROW":
    return "REVIEW_REQUIRED"
```

This does **not** change row typing, output guardrails, clean row assembly, readiness gates, or export behavior. It only aligns clean admission policy with the already-adopted output guardrail contract, which forbids `MARKET_REFERENCE_ROW` in `clean_data`.

## Tests added/updated

Updated tests in `tests/agent/test_agent_excel_intake_audit_348a.py`:

1. Replaced the old expectation:
   - old: `test_market_reference_weak_evidence_row_becomes_internal_reference_candidate`
   - new: `test_market_reference_weak_evidence_row_now_stays_review_required`

2. Added explicit unit-issue case:
   - `test_market_reference_weak_evidence_row_with_unit_issue_stays_review_required`

3. Updated fixture-routing expectation for the market-reference case in:
   - `test_clean_candidate_routing_fixture_cases`
   - The case `market_reference_row__becomes_internal_reference_candidate` is now asserted as `REVIEW_REQUIRED` to match the post-R6 guardrail contract.

These changes prove:

```text
MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> REVIEW_REQUIRED
MARKET_REFERENCE_ROW + WEAK_EVIDENCE + unit issue -> REVIEW_REQUIRED
no market-reference row can still become INTERNAL_REFERENCE_CANDIDATE
```

## Validation commands and results

```text
python -m py_compile datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py
  -> OK

python -m pytest tests\agent -q
  -> 76 passed in 0.62s

python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_fix2_market_reference_boundary"
  -> completed; previous guardrail failure gone

git diff --check
  -> no whitespace/conflict errors
     (Windows LF->CRLF warning only on clean_candidate_policy.py)
```

## Taihao pilot rerun result

Rerun output directory:

```text
output/agent_excel_intake_audit_348n_r7p_fix2_market_reference_boundary
```

Key manifest values after the fix:

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
market_reference_row_count = 2
normalized_testset_record_row_count = 0
testset_supporting_row_count = 0
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Output guardrails result

```text
previous_market_reference_guardrail_failure_fixed = yes
new_guardrail_failure = no
```

The specific prior failure:

```text
clean_data boundary violation ... forbidden row_type 'MARKET_REFERENCE_ROW'
```

no longer appears after the policy alignment.

## Boundary check

- No dependency added.
- No Pydantic / Pandera / pandas used.
- No input file modified.
- No output artifact committed.
- No legacy `datefac/` touched.
- No readiness gate meaning changed.
- No export behavior changed.
- No row_type semantics changed.
- No output guardrail contract weakened.

## Decision

`348N_R7P_FIX2_IMPLEMENTED_MARKET_REFERENCE_POLICY_ALIGNMENT`

This is a valid tiny fix. The root cause was unambiguous, the change was local and minimal, tests prove the behavior change, and the previous Taihao guardrail failure is gone without weakening the guardrail contract.

## Recommended next task

`348N-R7P-FIX2-QA market_reference clean_data admission policy review`

A focused QA should independently verify:

- `MARKET_REFERENCE_ROW` no longer becomes `INTERNAL_REFERENCE_CANDIDATE`
- the Taihao pilot no longer fails on the previous boundary
- no new cross-sample regression appears
- the output guardrails contract remains strict

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7P_FIX2_IMPLEMENTED_MARKET_REFERENCE_POLICY_ALIGNMENT
policy_change（策略变更）= MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
market_reference_internal_reference_candidate_allowed（是否仍允许 MARKET_REFERENCE_ROW -> INTERNAL_REFERENCE_CANDIDATE）= no
pytest_result（测试结果）= 76 passed
taihao_pilot_rerun（泰豪 pilot 重跑）= passed previous boundary; runner completed with AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
previous_market_reference_guardrail_failure_fixed（此前 MARKET_REFERENCE_ROW clean_data guardrail failure 是否消失）= yes
new_guardrail_failure（是否出现新 guardrail failure）= no
code_changes_made（是否改代码）= yes
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R7P-FIX2-QA market_reference clean_data admission policy review
```
