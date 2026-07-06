# 348N-R7AD-QA source_text fixture dry-run review

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = R7AD added controlled fixture dry-run coverage for source_text wiring. QA must verify the tests truly exercise trusted source_text selection, evidence_index metadata, review_queue compact fields, full-text exclusion, and closed clean/readiness boundaries.
```

## Task Goal

Review and validate the R7AD fixture dry-run implementation.

Task ID:

```text
348N-R7AD-QA source_text fixture dry-run review
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

Read these files first:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/codex_tasks/348N_R7AD_source_text_sidecar_fixture_dry_run_implementation.md
docs/agent/348N_R7AC_SOURCE_TEXT_SIDECAR_FIXTURE_INTEGRATION_DRY_RUN_DESIGN.md
docs/agent/348N_R7AB_QA_SOURCE_TEXT_AVAILABILITY_EVIDENCE_INDEX_WIRING_REVIEW.md
docs/codex_tasks/348N_R7AB_source_text_availability_evidence_index_wiring_implementation.md
```

Review R7AD implementation files:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

Also inspect, read-only, if useful:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/conftest.py
datefac_agent/audit/output_schema_guardrails.py
datefac_agent/review/clean_candidate_policy.py
```

---

## QA Questions

Answer all questions in the report:

1. Was R7AD tests-only, or were helper changes added? If helper changes were added, were they allowed and minimal?
2. Does R7AD use in-test `SourceTextEvidence` objects rather than file-backed fixtures or loaders?
3. Did R7AD avoid workbook reruns and avoid `run_pilot(...)` / real family reruns?
4. Did R7AD avoid MinerU, OCR, LLM, VLM, and PDF extraction?
5. Does a trusted matching fixture source_text produce `VERIFIED`?
6. Does trusted numeric mismatch produce `DISAGREED` without changing clean/readiness boundaries?
7. Does missing source_text remain `UNVERIFIED`?
8. Does source_id mismatch remain `UNVERIFIED` and source_text not used?
9. Does page_number mismatch remain `UNVERIFIED` and source_text not used?
10. Does locator mismatch remain `UNVERIFIED` or otherwise follow the conservative mismatch behavior?
11. Does untrusted source_text remain `UNVERIFIED`?
12. Does empty source_text remain `UNVERIFIED`?
13. Does evidence_index validation use tempfile or other safe temporary paths without committing output artifacts?
14. Does evidence_index include source_text metadata/status/hash/char_count/used flag?
15. Does evidence_index exclude full source_text?
16. Does review_queue validation use in-memory rows/builders and avoid output churn?
17. Does review_queue include compact fields and exclude full source_text?
18. Does R7AD prove `VERIFIED` does not become `STRONG_EVIDENCE`?
19. Does R7AD prove `VERIFIED` does not change MARKET_REFERENCE_ROW policy or clean admission?
20. Do readiness gates remain closed?
21. Do all R7X/R7Y/R7Z/R7AB/R7AD tests pass together?
22. What is the recommended next task?

---

## Expected QA Position

Be strict about these boundaries:

```text
fixture source_text is not production source_text
fixture source_text must be provenance-tied
missing / mismatch / untrusted / empty source_text remains UNVERIFIED
trusted numeric mismatch may be DISAGREED but must not alter clean/readiness gates
full source_text must not be serialized by default
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
```

If R7AD violates any boundary, mark QA as failed or needs fix.

If R7AD preserves these boundaries, mark QA as valid.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
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
Fixture dry-run coverage review
Positive case review
Negative case review
Evidence index validation review
Review queue validation review
Full source_text serialization review
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
fixture_dry_run_result（fixture dry-run结果）=
evidence_index_validation_result（证据索引验证结果）=
review_queue_validation_result（复核队列验证结果）=
full_text_serialization_result（全文序列化结果）=
qa_result（QA结果）=
readiness_gates（就绪门）=
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
git add docs/agent/348N_R7AD_QA_SOURCE_TEXT_FIXTURE_DRY_RUN_REVIEW.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AD QA review"
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
