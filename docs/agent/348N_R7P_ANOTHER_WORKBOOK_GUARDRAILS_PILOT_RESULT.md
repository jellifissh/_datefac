## Task ID

`348N-R7P Another Workbook Guardrails Pilot`

## Input workbook selected

```text
input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

## Why this workbook family was selected

- It is a real, existing, non-Linyang workbook family already present in `input/`.
- It is known to be structurally richer and more mixed than a simple wide financial workbook.
- It is therefore a good candidate for checking whether facts-like schemas, strongly-evidenced supporting rows, or new clean/review boundary issues appear under the now-stable output guardrails.
- It exercises a different family than the Linyang testset path without introducing mock data or rerunning extraction.

## Runner command used

```text
python tools\run_agent_excel_intake_audit_348a.py --pdf-path "input/H3_AP202605231822706325_1.pdf" --excel-path "input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx" --output-dir "output/agent_excel_intake_audit_348n_r7p_another_workbook_guardrails_pilot"
```

## Output directory

```text
output/agent_excel_intake_audit_348n_r7p_another_workbook_guardrails_pilot
```

This directory was generated read/write by the runner but is **not** committed or tracked by git.

## Manifest summary

The runner did **not** complete successfully. The pilot was blocked by output guardrails before a normal success result could be accepted.

The blocking exception was:

```text
datefac_agent.audit.output_schema_guardrails.OutputSchemaGuardrailError:
clean_data boundary violation: row 0
(sheet='报告核心信息与投资要点' metric='收盘价')
has forbidden row_type 'MARKET_REFERENCE_ROW';
clean_data must not contain ['MARKET_REFERENCE_ROW', 'NORMALIZED_TESTSET_RECORD_ROW', 'TESTSET_SUPPORTING_ROW', 'UNKNOWN_ROW']
```

This is a valid pilot finding, not an execution mistake to be bypassed.

## Logical vs physical count table

Not available as a final validated manifest summary, because the run was blocked before the output could be accepted as a successful pilot result.

What is known:

```text
output_guardrails = failed
blocking invariant = clean_data must not contain MARKET_REFERENCE_ROW
```

Any partially written artifact in the output directory must be treated as diagnostic only, not as an accepted pilot result.

## Row type distribution

Not accepted as final pilot output because the runner failed at guardrail validation.

The only independently confirmed row-type fact from the failure is:

```text
at least one row was treated as MARKET_REFERENCE_ROW
```

Specifically:

```text
sheet = 报告核心信息与投资要点
metric = 收盘价
row_type = MARKET_REFERENCE_ROW
```

## Evidence level distribution

Not accepted as a final pilot summary because the pilot was blocked at guardrail validation.

The important diagnostic fact is not evidence-level distribution, but that a `MARKET_REFERENCE_ROW` was present in `clean_data`, which violates the current guardrail contract.

## Clean data boundary result

Blocked / FAILED.

The pilot exposed a cross-sample boundary problem:

```text
clean_data contained a MARKET_REFERENCE_ROW
```

That violates the current output guardrails contract, which forbids these row types in clean_data:

```text
TESTSET_SUPPORTING_ROW
NORMALIZED_TESTSET_RECORD_ROW
MARKET_REFERENCE_ROW
UNKNOWN_ROW
```

This is not a `qualitative_facts` issue. It is a new workbook-family boundary finding: another workbook family can still leak `MARKET_REFERENCE_ROW` into `clean_data`.

## Review queue result

No accepted final review-queue summary is reported, because the pilot was blocked before completion.

The relevant conclusion is that the current runner/guardrail combination successfully prevented a bad clean-data admission from passing silently.

## Facts / qualitative-like schema observation

```text
facts_like_schema_found = no confirmed qualitative_facts-like schema in this blocked pilot result
qualitative_facts_like_rows = not established from the blocked run
```

The key finding from this run is not a new `qualitative_facts`-like facts schema, but a different cross-sample problem:

```text
MARKET_REFERENCE_ROW can still leak into clean_data on another workbook family.
```

This means the next issue to investigate is market-reference clean-data boundary handling, not qualitative_facts re-admission.

## Output guardrails result

```text
output_guardrails = failed
```

More precisely:

- The guardrails worked as intended.
- The runner was **loudly blocked** by `OutputSchemaGuardrailError`.
- The failure prevented a boundary-violating result from being accepted as a successful pilot.

## External call check

```text
LLM / MinerU / OCR / VLM calls = 0
```

No MinerU, OCR, LLM, or VLM run was performed.

## Readiness gate check

```text
readiness_gates = unchanged / closed
```

No readiness gate was changed or opened in this task.

## Validation commands and results

```text
python -m py_compile tools\run_agent_excel_intake_audit_348a.py
  -> passed

python -m pytest tests\agent -q
  -> 75 passed

git diff --check
  -> clean
```

## Boundary check

- No source code changed.
- No tests changed.
- No clean admission policy changed.
- No output guardrail implementation changed.
- No dependency added.
- No input/output/legacy source artifacts modified.
- The output directory was generated for diagnosis only and was not committed.

## Decision

`348N_R7P_BLOCKED_BY_OUTPUT_GUARDRAIL_FAILURE`

This blocked result is valid and useful. The pilot showed that another workbook family exposes a new cross-sample boundary issue:

```text
MARKET_REFERENCE_ROW entered clean_data
```

The guardrails correctly caught and stopped it.

## Recommended next task

`348N-R7P-FIX market_reference clean_data boundary leak investigation`

This should be a focused diagnosis task to answer:

- why `MARKET_REFERENCE_ROW` is still eligible for `clean_data` on this workbook family,
- whether the leak comes from row typing, clean candidate policy, or a workbook-family-specific path,
- whether the fix belongs in policy, row typing, or stronger output contract restrictions.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7P_BLOCKED_BY_OUTPUT_GUARDRAIL_FAILURE
input_workbook（输入 workbook）= input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
output_guardrails（输出护栏）= failed
clean_data_row_count（逻辑 clean 行数）= blocked / not accepted
clean_data_csv_row_count（clean CSV 物理行数）= blocked / not accepted
review_queue_row_count（逻辑 review/non-clean 池行数）= blocked / not accepted
review_queue_csv_row_count（review_queue CSV 物理行数）= blocked / not accepted
unknown_row_count（UNKNOWN_ROW 逻辑计数）= blocked / not accepted
facts_like_schema_found（是否发现 facts-like schema）= no
qualitative_facts_like_rows（类似 qualitative_facts 行）= not established
clean_admission_policy_changed（是否改 clean admission 策略）= no
code_changes_made（是否改代码）= no
pytest_result（测试结果）= 75 passed
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R7P-FIX market_reference clean_data boundary leak investigation
```
