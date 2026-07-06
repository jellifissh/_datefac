# 348N-R7AA source_text integration design / evidence index wiring

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = This task designs how real source_text should enter the evidence agreement pipeline. A bad design could turn the R7Y/R7Z checker into a false-confidence generator, so no implementation should happen before the wiring contract is reviewed.
```

## Task Goal

Design the source_text integration path for deterministic evidence agreement.

Task ID:

```text
348N-R7AA source_text integration design / evidence index wiring
```

This is a design / review task, not an implementation task.

Do not modify implementation code.

Do not modify tests.

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Create one design report only.

---

## Background

The current evidence path is:

```text
R7X: page_number parsing + agreement_status
R7Y: deterministic source-value agreement checker
R7Z: multiplicity-aware numeric matching to reduce VERIFIED false positives
R7Z-QA: confirmed duplicate numeric false-positive risk is reduced and readiness gates remain closed
```

Current checker semantics:

```text
No explicit/page provenance -> MISSING
Explicit/page provenance without source_text -> UNVERIFIED
No row numeric values -> UNVERIFIED
No source numeric tokens -> UNVERIFIED
Every row numeric value occurrence has a matching source numeric occurrence -> VERIFIED
No row numeric values match source numeric tokens -> DISAGREED
Some but not all row numeric values match -> UNVERIFIED
```

Important current limitation:

```text
row-level matching is still not period-aware or coordinate-aware
```

R7AA must design how source_text is provided to this checker without accidentally overclaiming verification.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If the worktree is not clean after pull, stop and report.

---

## Required Read Order

Read these files:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
docs/codex_tasks/348N_R7Z_QA_agreement_checker_edge_case_review.md
docs/codex_tasks/348N_R7Z_agreement_checker_edge_case_fixture_coverage.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

Inspect current code read-only:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/review/clean_candidate_policy.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Search, read-only, for existing source/evidence/page text carriers:

```text
source_text
source_page
page_text
evidence_text
explicit_evidence_ref
locator
evidence_index
source_id
page_number
agreement_status
```

---

## Design Questions To Answer

The report must answer:

1. Where can real source_text safely come from in the current project?
2. Does current Excel intake already carry any trustworthy source text or only page/provenance references?
3. Should source_text be attached to `EvidenceRef`, `AuditRowResult`, an evidence index sidecar, or passed only at checker-call time?
4. What is the safest minimal data contract for source_text?
5. Should source_text include whole page text, table-cell text, row-local text, or snippet text?
6. What provenance fields must accompany source_text?
7. How should page_number, source_id, locator, and source_text be tied together?
8. How should the pipeline behave when source_text is missing?
9. How should it behave when source_text is present but page provenance is missing?
10. How should it behave when source_text exists but is not tied to the same source_id/page_number?
11. How should evidence_index.json represent source_text availability without bloating output or leaking large text?
12. Should review_queue.csv include agreement_status or source_text availability? If yes, what minimal fields?
13. What should remain explicitly out of scope for the first implementation slice?
14. What tests should the next implementation task require?
15. What is the recommended next task after this design?

---

## Required Design Position

The design must stay conservative:

```text
source_text missing -> keep UNVERIFIED
source_text untrusted -> keep UNVERIFIED
source_text not tied to same source/page -> keep UNVERIFIED
page_number alone -> not VERIFIED
source_text alone without provenance -> not VERIFIED
VERIFIED does not imply STRONG_EVIDENCE by default
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
```

Prefer a minimal integration slice that passes source_text into the checker only when it is already available in a deterministic, provenance-tied way.

Do not design a broad OCR/PDF extraction pipeline in this task.

Do not design LLM/VLM verification.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
```

No other file may be created or modified.

---

## Forbidden Actions

Do not modify code.

Do not modify tests.

Do not modify output.

Do not modify input.

Do not modify previous reports.

Do not modify:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/
temp/
data/
legacy datefac/
dependencies
config files
```

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not wire source_text into the real pipeline.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change output_schema_guardrails.

Do not change readiness gates.

Do not stage or commit output files.

Do not use broad Git staging.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Report Content

The report must include:

```text
Task ID
Recommended reasoning level used
Preflight
Files reviewed
Current source_text availability review
Current evidence index review
Proposed source_text contract
Proposed integration slice
Evidence index / review_queue output design
Out-of-scope list
Risk review
Validation outputs
Decision
Recommended next task
Data Result / 数据结果
```

Data Result must include:

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
source_text_availability_result（source_text可用性结果）=
integration_design_result（接入设计结果）=
evidence_index_design_result（证据索引设计结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. exactly one design report was created under `docs/agent/`,
2. no code/tests/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AA source text integration design"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Post-push validation:

```text
git status -sb
git log --oneline -10
```

Stop after push. Do not start the next task.
