## Task ID

`348N-R6D Guardrails Contract Documentation Update`

## Files modified

- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/agent/项目进程.md`
- `项目进展大白话说明.md`
- `docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md`

No source code, tests, dependency files, input files, output files, legacy `datefac/`, readiness gates, or export behavior were modified.

## Documentation updates

### `.skills/agent_excel_intake_audit_workflow.md`

Updated the stable Excel audit workflow skill to document the current output guardrails contract.

Added / clarified:

- `validate_outputs(...)` is part of the current 348A-style / 348N-style Excel audit runner contract.
- The guardrail runs before manifest success output is written.
- Guardrail violations must fail loudly.
- No Pydantic / Pandera / pandas dependency is required for this contract.
- Future output-guarded reports must list both logical and physical CSV counts.
- Manifest Discipline now includes `clean_data_csv_row_count`, `review_queue_csv_row_count`, and `unknown_row_count`.

### `docs/agent/项目进程.md`

Added concise milestone entries for:

```text
348N-R5 qualitative_facts header fix
348N-R6B output schema guardrails
348N-R6B-FIX clean_data_csv_row_count guardrail
348N-R6C adoption review
```

Updated the current task pointer to:

```text
348N-R6D Guardrails Contract Documentation Update
```

Kept the file compact; did not paste full result/QA reports.

### `项目进展大白话说明.md`

Updated the plain-language progress explanation:

- refreshed the "current data state" section to R6B-FIX-QA values;
- replaced the stale R4-next-step explanation with current R4/R5/R6 guardrail story;
- added a new plain-language `output guardrails` section;
- explained why logical counts and physical CSV counts are different;
- clarified that `review_queue_row_count` is not the physical `review_queue.csv` row count;
- listed the fields users should compare in future reports.

## Guardrails contract wording added

The contract is now documented as:

```text
For the current 348A-style / 348N-style Excel audit runner,
datefac_agent.audit.output_schema_guardrails.validate_outputs(...)
is part of the standard runner contract.
```

The documented contract says:

```text
validate_outputs(...) runs before manifest success output is written
guardrail violations must fail loudly
no Pydantic / Pandera / pandas dependency is required for this contract
clean_data must not contain TESTSET_SUPPORTING_ROW / NORMALIZED_TESTSET_RECORD_ROW / MARKET_REFERENCE_ROW / UNKNOWN_ROW
manifest gates must stay closed
external-call counters must stay zero
```

Scope remains limited to the active Agent Excel audit runner; this does not imply legacy runner adoption or production/export readiness.

## Count semantics wording added

The required count definitions are now documented in stable guidance and plain-language docs:

```text
clean_data_row_count = logical clean row count
clean_data_csv_row_count = physical clean_data.csv data-row count
review_queue_row_count = historical logical non-clean / review-required pool count
review_queue_csv_row_count = physical review_queue.csv data-row count
unknown_row_count = logical UNKNOWN_ROW classification count
```

Critical rule documented:

```text
Do not interpret review_queue_row_count as the physical review_queue.csv row count.
When discussing review_queue.csv, use review_queue_csv_row_count.
```

## Future report template wording added

Future output-guarded reports are now expected to include both logical and physical CSV counts:

```text
clean_data_row_count
clean_data_csv_row_count
review_queue_row_count
review_queue_csv_row_count
unknown_row_count
output_guardrails = passed / failed
```

The plain-language doc explains:

```text
逻辑计数告诉你系统怎么分类。
CSV 计数告诉你文件里实际写了多少行。
两个都要看，别拿一个冒充另一个。
```

## Validation result

```text
git pull --ff-only origin pivot/348-agent-foundation
  -> fast-forward to R6D task docs

git status -sb before editing
  -> clean

git branch --show-current
  -> pivot/348-agent-foundation

git diff --check
  -> clean
```

No pytest was run because this is docs-only and no code/tests were modified.

## Boundary check

- No source code modified.
- No tests modified.
- No dependency files modified.
- No input/output files modified.
- No legacy `datefac/` touched.
- No readiness gate semantics changed.
- No export behavior changed.
- No MinerU / OCR / LLM / VLM run.
- No output artifacts committed.
- No `git add .` / `git add -A` used.

## Decision

`348N_R6D_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTED`

The output guardrails contract and logical-vs-physical row count semantics are now documented in stable workflow guidance, the compact project ledger, and the plain-language project progress document.

## Recommended next task

`348N-R6D-QA guardrails contract documentation review`

A focused docs QA should verify:

- `.skills/agent_excel_intake_audit_workflow.md` accurately describes the runner contract;
- `项目进程.md` remains compact and does not duplicate full reports;
- `项目进展大白话说明.md` correctly explains logical vs physical counts in user-facing language;
- no code/test/dependency/input/output/legacy files were modified.

After that, the project can proceed to either:

```text
348N-R7 qualitative_facts narrow clean-admission policy design
```

or:

```text
348N-R7 pilot another workbook family under guardrails
```

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6D_CONFIRMED_GUARDRAILS_CONTRACT_DOCUMENTED
guardrails_contract_documented（护栏契约是否写入文档）= yes
count_semantics_documented（计数语义是否写入文档）= yes
future_report_template_documented（未来报告模板是否写入文档）= yes
code_changes_made（是否改代码）= no
pytest_result（测试结果）= not run / not required
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R6D-QA guardrails contract documentation review
```
