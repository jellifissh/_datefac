# 348N-R7AB-QA source_text availability / evidence index wiring review

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = R7AB added the first trusted source_text metadata and checker injection implementation. QA must verify that trusted source_text is only used when provenance binding is safe, that serialized outputs exclude full text, and that clean/readiness boundaries did not change.
```

## Task Goal

Review and validate the R7AB implementation.

Task ID:

```text
348N-R7AB-QA source_text availability / evidence index wiring review
```

This is a QA / review task.

Do not modify implementation code.

Do not modify tests.

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Create one QA report only.

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
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

Review R7AB implementation files:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/conftest.py
```

Also inspect, read-only, if useful:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/output_schema_guardrails.py
datefac_agent/review/clean_candidate_policy.py
```

---

## QA Questions

Answer all questions in the report:

1. Does R7AB define a minimal `SourceTextEvidence` contract with document id, page, locator, text, trust, hash, and char count metadata?
2. Does `SourceTextSelection` clearly represent selected/not selected state and deterministic unavailable reasons?
3. Is source_text selected only when explicit/page provenance exists?
4. Is source_text selected only when source_id matches the evidence ref source_id?
5. Is source_text selected only when page_number matches the evidence ref page_number?
6. Is untrusted source_text rejected and kept `UNVERIFIED`?
7. Is empty source_text rejected and kept `UNVERIFIED`?
8. Is locator compatibility enforced or conservatively handled?
9. Without a source_text index, does default behavior remain `UNVERIFIED` for page provenance rows?
10. With trusted matching source_text, can the checker produce `VERIFIED`?
11. With trusted matching source_text and numeric mismatch, can the checker produce `DISAGREED`?
12. Does R7AB avoid using Excel raw fields such as `value_text_original`, `source_page`, `来源页`, `页码`, or `摘录/说明` as trusted source_text?
13. Does evidence_index serialize metadata/status/hash/char_count but not full source_text?
14. Are review_queue compact fields added safely, and do they avoid full source_text?
15. Did `tests/agent/conftest.py` only solve direct pytest import path behavior without changing production code?
16. Did R7AB avoid changing evidence_level promotion?
17. Did R7AB avoid changing clean_candidate_policy / MARKET_REFERENCE_ROW / qualitative_facts admission?
18. Did R7AB avoid changing readiness gates?
19. Do all R7X/R7Y/R7Z/R7AB tests pass together?
20. What is the recommended next task?

---

## Expected QA Position

Be strict about these boundaries:

```text
source_text missing -> UNVERIFIED
source_text untrusted -> UNVERIFIED
source_id mismatch -> UNVERIFIED
page_number mismatch -> UNVERIFIED
empty source_text -> UNVERIFIED
Excel workbook raw fields are not trusted source_text
full source_text is not serialized by default
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
```

If R7AB violates any boundary, mark QA as failed or needs fix.

If R7AB preserves these boundaries, mark QA as valid.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
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

Do not add a PDF extraction pipeline.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change output_schema_guardrails unless reporting a read-only finding.

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
Source text contract review
Source text selection review
Agreement checker injection review
Evidence index metadata review
Review queue compact fields review
Boundary policy review
Readiness gates review
Test review
Compatibility risk review
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
source_text_contract_result（source_text契约结果）=
source_text_selection_result（source_text选择结果）=
agreement_injection_result（一致性检查注入结果）=
evidence_index_wiring_result（证据索引接线结果）=
review_queue_wiring_result（复核队列接线结果）=
full_text_serialization_result（全文序列化结果）=
readiness_gates（就绪门）=
qa_result（QA结果）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. exactly one QA report was created under `docs/agent/`,
2. no code/tests/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AB QA review"
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
