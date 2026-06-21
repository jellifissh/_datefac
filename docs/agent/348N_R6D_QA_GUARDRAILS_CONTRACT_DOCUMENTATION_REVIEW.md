## Task ID

`348N-R6D-QA Guardrails Contract Documentation Review`

## Reviewed files

Read-only review:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md`
- `docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md`
- `docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md`
- `docs/agent/项目进程.md`

## Contract documentation QA

Conclusion: VALID.

Confirmed in `.skills/agent_excel_intake_audit_workflow.md`:

- `validate_outputs(...)` is explicitly documented as part of the current `348A-style / 348N-style Excel audit runner` contract.
- It is explicitly stated that the guardrail runs **before manifest success output is written**.
- It is explicitly stated that **guardrail violations must fail loudly**.
- It is explicitly stated that **no Pydantic / Pandera / pandas dependency is required** for this contract.
- The scope is clearly limited to the **current Agent Excel audit runner**. The documentation does **not** say this automatically extends to legacy `datefac/` runners, and it does **not** imply production/export readiness.

This matches the R6C adoption decision precisely and uses stable wording appropriate for workflow guidance.

## Count semantics QA

Conclusion: VALID.

The required count semantics are documented explicitly and correctly in both `.skills/agent_excel_intake_audit_workflow.md` and `项目进展大白话说明.md`:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv data-row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv data-row count
unknown_row_count = logical UNKNOWN_ROW classification count
```

Also confirmed:

- The documentation explicitly says **do not interpret `review_queue_row_count` as the physical `review_queue.csv` row count**.
- It explicitly says **when discussing `review_queue.csv`, use `review_queue_csv_row_count`**.
- No contradictory wording was found in the updated files.

## Future report template QA

Conclusion: VALID.

R6D documents that future output-guarded reports must include both logical and physical counts.

Confirmed required template wording exists:

```text
clean_data_row_count
clean_data_csv_row_count
review_queue_row_count
review_queue_csv_row_count
unknown_row_count
output_guardrails = passed / failed
```

This appears both in the R6D result report and is reflected in the stable workflow guidance / plain-language explanation, which is the correct place for long-term reuse.

## Project ledger QA

Conclusion: VALID.

`docs/agent/项目进程.md` remains a **compact milestone ledger**.

Confirmed:

- It adds only concise R5 / R6B / R6B-FIX / R6C milestone entries.
- It updates the current task pointer to `348N-R6D Guardrails Contract Documentation Update`.
- It does **not** paste full report bodies, validation transcripts, or long contract text into the ledger.

This satisfies the requirement to keep the ledger compact and not turn it into a duplicate of result/QA reports.

## Plain-language explanation QA

Conclusion: VALID.

`项目进展大白话说明.md` now explains the guardrails in user-facing language rather than technical-contract language.

Confirmed it clearly explains:

- what `output guardrails` are in plain language;
- why logical counts and physical CSV counts are different;
- why `review_queue_row_count` is not equal to `review_queue.csv` row count;
- which fields users should compare in future reports.

The explanations are understandable to a non-implementer, e.g.:

```text
逻辑计数告诉你系统怎么分类。
CSV 计数告诉你文件里实际写了多少行。
两个都要看，别拿一个冒充另一个。
```

This meets the task's "user can understand it" standard.

## Boundary QA

Conclusion: VALID.

R6D stayed within the docs-only boundary.

Confirmed from the R6D result report and current repo state:

- No source code was modified.
- No tests were modified.
- No dependency files were modified.
- No `input/`, `output/`, `legacy datefac/`, `temp/`, or `data/` changes were made.
- No readiness gate semantics were changed.
- No export behavior was changed.
- No MinerU / OCR / LLM / VLM execution occurred.

This QA task itself also made no source/test/dependency/input/output changes before creating this QA report.

## Validation result

```text
git pull --ff-only origin pivot/348-agent-foundation
  -> Already up to date after fast-forward to R6D-QA docs

git status -sb before editing
  -> clean

git branch --show-current
  -> pivot/348-agent-foundation

git diff --check
  -> clean
```

No pytest required because this is a docs QA/review task and no code/tests were modified.

## Decision

`348N_R6D_QA_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTATION_VALID`

R6D correctly documented the current Excel audit runner guardrails contract, the logical-vs-physical count semantics, the future report template requirement, and the user-facing explanation, without scope violation.

## Recommended next task

`348N-R7 qualitative_facts narrow clean-admission policy design`

Why this next:

- The runner contract is now implemented, validated, adopted, documented, and QA-reviewed.
- The next unresolved product/design question is no longer schema safety but **whether any correctly-parsed `qualitative_facts` rows should ever be admitted to clean_data under a deliberately narrow policy**.
- That is the next highest-value decision before expanding to another workbook family or moving closer to delivery/export planning.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6D_QA_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTATION_VALID
guardrails_contract_documented（护栏契约是否写入文档）= yes
count_semantics_documented（计数语义是否写入文档）= yes
future_report_template_documented（未来报告模板是否写入文档）= yes
plain_language_doc_updated（大白话说明是否更新）= yes
project_ledger_updated（项目进程是否更新）= yes
code_changes_made（是否改代码）= no
pytest_result（测试结果）= not run / not required
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R7 qualitative_facts narrow clean-admission policy design
```
