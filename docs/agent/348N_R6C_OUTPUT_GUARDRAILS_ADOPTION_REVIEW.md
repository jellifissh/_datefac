## Task ID

`348N-R6C Output Guardrails Adoption Review`

## Reviewed files

Read-only review:

- `datefac_agent/audit/output_schema_guardrails.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/agent/项目进程.md`
- `项目进展大白话说明.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/348N_R6B_FIX_QA_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_REVIEW.md`
- `docs/agent/348N_R6B_FIX_CLEAN_DATA_CSV_ROW_COUNT_GUARDRAIL_RESULT.md`
- `docs/agent/348N_R6B_QA_OUTPUT_SCHEMA_GUARDRAILS_REVIEW.md`
- `docs/agent/348N_R6B_OUTPUT_SCHEMA_GUARDRAILS_IMPLEMENTATION_RESULT.md`
- `docs/agent/348N_R6_SCHEMA_HARDENING_DESIGN.md`

No source, tests, dependency files, input, output, legacy files, or historical reports were modified by this task.

## Contract adoption decision

Decision: **yes — adopt `output_schema_guardrails.validate_outputs(...)` as the standard runner contract for the current 348A-style DateFac Agent Excel intake/audit runner.**

Scope of adoption:

```text
Applies now:
- tools/run_agent_excel_intake_audit_348a.py
- 348A-style / 348N-style Excel intake audit pilots
- outputs: clean_data.csv, review_queue.csv, manifest

Does not automatically apply yet:
- legacy datefac/ runners
- old MinerU / parser / benchmark chains
- formal client export paths
- future delivery/export gates not yet implemented
```

Reason:

- R4/R5 showed that output boundary inversions can pass without a code crash: `qualitative_facts` entered `clean_data` because of a header-detection issue.
- R6B/R6B-FIX created a low-cost stdlib-only guardrail layer that catches exactly that class of failure before the manifest is written.
- The guardrails now enforce closed gates, zero external-call counters, clean-data forbidden row types, clean candidate types, and logical/physical count consistency.
- The validated behavior is part of the safety story of this runner, not an optional QA convenience.

Adoption should be called a **runner contract** for this workflow, while explicitly limiting the scope to the active Agent Excel audit runner to avoid implying legacy production readiness.

## Count semantics standardization

Recommended standard definitions:

```text
clean_data_row_count
  Type: logical count
  Meaning: number of rows classified as clean/reference candidates by the audit policy
  Source: AuditSummary.clean_data_row_count = internal_clean_candidate_count + internal_reference_candidate_count
  In current runner: should equal len(clean_rows) and clean_data_csv_row_count

clean_data_csv_row_count
  Type: physical CSV count
  Meaning: number of data rows written to clean_data.csv
  Source: len(clean_rows)
  Status: additive manifest field introduced by R6B, validated by R6B-FIX

review_queue_row_count
  Type: historical logical count
  Meaning: total non-clean / review-required pool count, including rows that may be PASS but still not clean-data candidates
  Source: AuditSummary.review_queue_row_count = narrative_review_count + review_required_count + excluded_from_clean_data_count
  Important: NOT the physical review_queue.csv row count

review_queue_csv_row_count
  Type: physical CSV count
  Meaning: number of data rows written to review_queue.csv (currently REVIEW/FAIL rows excluding clean candidates)
  Source: len(review_rows)
  Status: additive manifest field introduced by R6B, validated by R6B

unknown_row_count
  Type: logical classification count
  Meaning: number of audited rows with row_type == UNKNOWN_ROW
  Source: AuditSummary.unknown_row_count
  Required invariant for the current Linyang/R5+ line: should remain 0 unless a new workbook family deliberately introduces unknowns for diagnosis
```

Key rule for future language:

```text
Do not call review_queue_row_count the CSV row count.
Use review_queue_csv_row_count when discussing the physical review_queue.csv file.
```

## Future report template recommendation

Future DateFac Agent result/QA reports for this runner should include **both logical and physical counts** whenever output guardrails are active.

Minimum recommended Data Result fields:

```text
clean_data_row_count（逻辑清洗行数）= ...
clean_data_csv_row_count（clean_data.csv 物理行数）= ...
review_queue_row_count（逻辑 review/non-clean 池行数）= ...
review_queue_csv_row_count（review_queue.csv 物理行数）= ...
unknown_row_count（未知行数）= ...
output_guardrails（输出护栏）= passed / failed
```

Optional but useful for debugging:

```text
internal_clean_candidate_count
internal_reference_candidate_count
review_required_count
narrative_review_count
excluded_from_clean_data_count
```

Why include both:

- `review_queue_row_count` and `review_queue_csv_row_count` intentionally differ in current design.
- Reports that only list `review_queue_row_count` can be misread as physical CSV row count.
- The guardrails validate both categories, so reports should expose both categories.

## Skill/handoff documentation recommendation

Do not modify docs in this R6C task. Recommend a follow-up docs task to update active guidance, because the runner contract is now stable enough to document.

Recommended future updates:

1. `.skills/agent_excel_intake_audit_workflow.md`
   - Add a short "Output Guardrails Contract" section.
   - State that `validate_outputs(...)` is part of the standard 348A-style runner contract.
   - Define logical vs physical row counts.
   - Add required manifest fields:
     - `clean_data_csv_row_count`
     - `review_queue_csv_row_count`
   - Clarify `review_queue_row_count` is not the CSV row count.

2. `docs/agent/项目进程.md`
   - Add a compact 348N-R6/R6B/R6B-FIX milestone entry.
   - Record that output guardrails are active and validated.
   - Keep it as a ledger, not a full technical contract.

3. `项目进展大白话说明.md`
   - Add a plain-language explanation:
     - logical count = system decision pool
     - CSV count = rows physically written in files
     - guardrails = automatic safety checks before runner finishes
   - This will help humans understand why `review_queue_row_count=489` while `review_queue.csv` has 46 rows.

4. `CURRENT_MODEL_HANDOFF.md`
   - Only keep a pointer to the current stage and next task.
   - Do not duplicate full guardrail definitions there.

## Risks and non-goals

Risks if not documented:

- Future reports may continue mixing logical and physical counts.
- A reviewer may think `review_queue.csv` is missing rows because `review_queue_row_count` is larger than the CSV.
- Future runner tasks might accidentally remove or bypass `validate_outputs(...)` if the contract is not documented.

Non-goals for adoption:

- Do not apply this contract retroactively to legacy `datefac/` runners.
- Do not claim client-ready or production-ready status.
- Do not add Pandera/Pydantic/pandas just because guardrails now exist.
- Do not change export/delivery gate behavior.
- Do not redesign review_queue semantics in this step.

## Validation result

```text
git pull --ff-only origin pivot/348-agent-foundation
  -> fast-forward to R6C task docs

git status -sb before editing
  -> clean

git branch --show-current
  -> pivot/348-agent-foundation

git diff --check
  -> clean
```

No pytest required because this is docs/design-only and no code was modified. No external calls or output generation were performed.

## Decision

`348N_R6C_RECOMMENDS_ADOPT_OUTPUT_GUARDRAILS_AS_RUNNER_CONTRACT`

Adopt the output schema guardrails as the standard contract for the active 348A-style Excel intake/audit runner, not for legacy runners or production export paths. Future reports should consistently list both logical row counts and physical CSV row counts.

## Recommended next task

`348N-R6D guardrails contract documentation update`

Why this next:

- R6C establishes the adoption decision.
- The next safest step is documentation, not new code.
- Updating `.skills/agent_excel_intake_audit_workflow.md`, `docs/agent/项目进程.md`, and `项目进展大白话说明.md` will prevent count-semantics confusion in future tasks.
- After the contract is documented, the project can return to either:
  - `348N-R7 qualitative_facts narrow clean-admission policy design`, or
  - `348N-R7 pilot another workbook family under guardrails`.

Recommended sequence:

```text
R6D docs contract update
-> R7 qualitative_facts clean-admission policy design OR another workbook-family pilot
-> later delivery/export gate preparation
```

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R6C_RECOMMENDS_ADOPT_OUTPUT_GUARDRAILS_AS_RUNNER_CONTRACT
guardrails_contract_adoption（护栏契约采用）= yes, for current 348A-style Excel audit runner only
logical_counts（逻辑计数字段）= clean_data_row_count, review_queue_row_count, unknown_row_count
physical_csv_counts（物理 CSV 计数字段）= clean_data_csv_row_count, review_queue_csv_row_count
future_reports_include_both_counts（未来报告是否同时列出两类计数）= yes
code_changes_made（是否改代码）= no
pytest_result（测试结果）= not run / not required
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R6D guardrails contract documentation update
```
