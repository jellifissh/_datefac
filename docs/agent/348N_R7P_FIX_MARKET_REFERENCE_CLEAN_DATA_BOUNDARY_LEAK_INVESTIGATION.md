## Task ID

`348N-R7P-FIX Market Reference Clean Data Boundary Leak Investigation`

## Reviewed files

Read-only review:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md`
- `docs/agent/348N_R7_QUALITATIVE_FACTS_NARROW_CLEAN_ADMISSION_POLICY_DESIGN.md`
- `docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md`
- `docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md`
- `tools/run_agent_excel_intake_audit_348a.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/audit/row_type_classifier.py`
- `datefac_agent/audit/output_schema_guardrails.py`
- `datefac_agent/review/review_queue_builder.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `output/agent_excel_intake_audit_348n_r7p_another_workbook_guardrails_pilot/clean_data.csv` (read-only)
- `output/agent_excel_intake_audit_348n_r7p_another_workbook_guardrails_pilot/evidence_index.json` (read-only)

## Failing row summary

Guardrail-blocking row:

```text
sheet = 报告核心信息与投资要点
metric = 收盘价
row_type = MARKET_REFERENCE_ROW
clean_candidate_type = INTERNAL_REFERENCE_CANDIDATE
evidence_level = WEAK_EVIDENCE
```

Observed in the diagnostic `clean_data.csv` written before the guardrail stopped the run:

```text
报告核心信息与投资要点,8,收盘价,INTERNAL_REFERENCE_CANDIDATE,MARKET_REFERENCE_ROW,WEAK_EVIDENCE,...
```

The output guardrail then correctly raised:

```text
clean_data boundary violation: ... forbidden row_type 'MARKET_REFERENCE_ROW'
```

## Root-cause analysis

Root cause is **not** a clean-row assembly bug and **not** a row-typing bug.

The upstream chain is:

1. `row_type` is assigned when `build_row_audit_result(...)` copies `row.row_type` into `AuditRowResult`.
2. `row.row_type` comes from `classify_row_type(...)` / workbook refinement.
3. `clean_candidate_type` is assigned in `build_row_audit_result(...)` by calling `classify_clean_candidate(result)`.
4. `clean_rows` are assembled in `tools/run_agent_excel_intake_audit_348a.py` by selecting rows whose `clean_candidate_type` is either:

```text
INTERNAL_CLEAN_CANDIDATE
INTERNAL_REFERENCE_CANDIDATE
```

5. Therefore, if `classify_clean_candidate(...)` returns `INTERNAL_REFERENCE_CANDIDATE` for a `MARKET_REFERENCE_ROW`, that row will be emitted into `clean_data.csv` by design.

That is exactly what happened.

So the direct root cause is:

```text
clean_candidate_policy.py still allows MARKET_REFERENCE_ROW with WEAK_EVIDENCE and no unit issue to become INTERNAL_REFERENCE_CANDIDATE, and clean_rows assembly intentionally includes INTERNAL_REFERENCE_CANDIDATE rows.
```

In other words, the new guardrail contract and the old market-reference admission policy are now inconsistent.

## Row typing finding

Conclusion: `row_type` is **correct**.

Why:

- `row_type` for this row is assigned by `datefac_agent.audit.row_type_classifier.classify_row_type(...)`.
- The sheet `报告核心信息与投资要点` belongs to `NARRATIVE_SHEETS`.
- For rows on narrative sheets, if the metric contains any market hint, the classifier returns `MARKET_REFERENCE_ROW`.
- `收盘价` is explicitly in `MARKET_METRIC_HINTS`.

So:

```text
sheet = 报告核心信息与投资要点
metric = 收盘价
-> MARKET_REFERENCE_ROW
```

This is semantically correct. A closing price is market-reference data, not a strict financial-table row and not a narrative-only row.

## Clean admission finding

Conclusion: **yes, this is primarily a clean-admission policy fault**.

The relevant policy code is:

```python
if result.evidence_level != "WEAK_EVIDENCE":
    return "REVIEW_REQUIRED"
...
if result.row_type == "MARKET_REFERENCE_ROW":
    if _has_category_issue(result.issues, "unit"):
        return "REVIEW_REQUIRED"
    return "INTERNAL_REFERENCE_CANDIDATE"
```

For the failing row:

```text
row_type = MARKET_REFERENCE_ROW
evidence_level = WEAK_EVIDENCE
unit issue = none
```

Therefore the policy returns:

```text
INTERNAL_REFERENCE_CANDIDATE
```

That admission path predates the stricter output-guardrail contract and is now incompatible with it.

Under the current guardrail contract, `MARKET_REFERENCE_ROW` must not appear in `clean_data`, so the old policy is too permissive for the current workflow semantics.

## Clean row assembly finding

Conclusion: **no, clean row assembly itself is not the bug**.

The runner assembles `clean_rows` with this logic:

```python
clean_rows = [
    _row_to_clean_csv(result)
    for result in row_results
    if result.clean_candidate_type in {"INTERNAL_CLEAN_CANDIDATE", "INTERNAL_REFERENCE_CANDIDATE"}
]
```

This is internally consistent with the policy model:

- `INTERNAL_CLEAN_CANDIDATE` means eligible for clean output
- `INTERNAL_REFERENCE_CANDIDATE` also means eligible for clean output

So the assembly did exactly what it was told to do.

The issue is that `MARKET_REFERENCE_ROW -> INTERNAL_REFERENCE_CANDIDATE` is no longer a valid admission rule under the current guardrail contract.

## Recommended fix

Recommended fix (diagnosis only, not implemented here):

```text
Update clean_candidate_policy.py so MARKET_REFERENCE_ROW is no longer eligible for INTERNAL_REFERENCE_CANDIDATE in the current 348A/348N runner contract.
Instead, MARKET_REFERENCE_ROW should fall back to REVIEW_REQUIRED (or a future separate market-reference output path) under the current workflow.
```

Narrowest safe fix:

- local to `datefac_agent/review/clean_candidate_policy.py`
- no policy broadening
- aligns the policy with the already-adopted output guardrail contract
- does not require changing row typing or clean-row assembly

Possible implementation shape (not applied here):

```text
MARKET_REFERENCE_ROW -> REVIEW_REQUIRED
```

or an equally small conditional that prevents `INTERNAL_REFERENCE_CANDIDATE` in the current runner.

What tests would prove the fix:

1. a `MARKET_REFERENCE_ROW` with `WEAK_EVIDENCE` and no unit issue must now resolve to `REVIEW_REQUIRED`
2. the prior `INTERNAL_REFERENCE_CANDIDATE` market-reference unit test must be updated accordingly
3. the Taihao R7P pilot should no longer fail on `MARKET_REFERENCE_ROW` in clean_data (it may surface a different boundary afterward, which is acceptable)
4. existing normalized_testset / qualitative_facts / guardrail tests must remain green

## Whether code was changed

```text
code_changes_made = no
```

Root cause is clear, but per task preference this report stops at diagnosis-first and recommended fix plan.

## Validation result

```text
python -m py_compile tools\run_agent_excel_intake_audit_348a.py
  -> passed

python -m pytest tests\agent -q
  -> 75 passed

git diff --check
  -> clean
```

The failing R7P pilot was not rerun in this task because no code was changed.

## Boundary check

- No source code modified.
- No tests modified.
- No input/output source artifacts modified.
- No legacy `datefac/` touched.
- No dependencies added.
- No readiness gate semantics changed.
- No export behavior changed.
- No MinerU / OCR / LLM / VLM run.
- No output artifacts committed.

## Decision

`348N_R7P_FIX_CONFIRMED_MARKET_REFERENCE_BOUNDARY_ROOT_CAUSE`

Root cause is clear and localized: `clean_candidate_policy.py` still permits `MARKET_REFERENCE_ROW` with `WEAK_EVIDENCE` and no unit issue to become `INTERNAL_REFERENCE_CANDIDATE`, while `output_schema_guardrails` now correctly forbids `MARKET_REFERENCE_ROW` from entering `clean_data`.

## Recommended next task

`348N-R7P-FIX2 market_reference clean_data admission policy alignment`

Scope:

- tiny change in `clean_candidate_policy.py`
- update/add tests in `tests/agent/test_agent_excel_intake_audit_348a.py`
- rerun the Taihao pilot to confirm the specific boundary leak is gone
- keep the current guardrail contract strict

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7P_FIX_CONFIRMED_MARKET_REFERENCE_BOUNDARY_ROOT_CAUSE
root_cause（根因）= clean_candidate_policy.py still maps MARKET_REFERENCE_ROW + WEAK_EVIDENCE + no unit issue -> INTERNAL_REFERENCE_CANDIDATE, and clean_rows assembly includes INTERNAL_REFERENCE_CANDIDATE
failing_row（失败行）= sheet='报告核心信息与投资要点', metric='收盘价', row_type='MARKET_REFERENCE_ROW'
row_typing_correct（row_type 是否正确）= yes
clean_admission_fault（是否 clean admission 问题）= yes
clean_row_assembly_fault（是否 clean row assembly 问题）= no
recommended_fix（推荐修复）= align clean_candidate_policy with current guardrail contract so MARKET_REFERENCE_ROW no longer becomes INTERNAL_REFERENCE_CANDIDATE in this runner; route to REVIEW_REQUIRED (or later separate market-reference output)
code_changes_made（是否改代码）= no
pytest_result（测试结果）= 75 passed
rerun_pilot_result（是否重跑 pilot）= no
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R7P-FIX2 market_reference clean_data admission policy alignment
```
