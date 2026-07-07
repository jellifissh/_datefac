# 348N-R7AM-QA test-only MinerU artifact adapter prototype review

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AM added a test-only MinerU artifact adapter prototype with fixture and tests. QA must verify it stayed test-only, did not commit full MinerU/DateFac outputs, did not alter production code, and preserved conservative evidence semantics.
```

## Task Goal

Review the R7AM implementation for correctness, boundaries, and evidence safety.

Task ID:

```text
348N-R7AM-QA test-only MinerU artifact adapter prototype review
```

This is a QA review task only.

Do not modify production code.
Do not modify adapter code unless a blocking defect requires a tiny QA fix and you explicitly report it.
Do not add dependencies.
Do not run MinerU, OCR, LLM, or VLM.
Do not run real PDFs.
Do not commit output files.

---

## Background

R7AM completed:

```text
Commit = 0de3a4a test: add MinerU artifact adapter prototype
pytest tests/agent/test_mineru_artifact_adapter_348n.py -q => 21 passed
pytest tests/agent -q => 201 passed
fixture_result = PASS, small curated fixture, no full MinerU output
adapter_result = PASS, test-only content_list_v2 adapter
matching_helper_result = PASS, VERIFIED / UNVERIFIED / DISAGREED / AMBIGUOUS / MISSING_EVIDENCE covered
boundary_check = PASS
readiness_gates = CLOSED
```

R7AL before it proved the real local comparison shape:

```text
451 DateFac rows compared
173 MinerU blocks indexed
395 VERIFIED
56 review-required
10 DISAGREED
10 AMBIGUOUS
2 MISSING_EVIDENCE
11 required probe examples all VERIFIED
primary input = content_list_v2
```

R7AM converted that shape into a small test-only prototype, not production integration.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If worktree is not clean after pull, stop and report.

---

## Required Read Order

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/codex_tasks/348N_R7AM_test_only_mineru_artifact_adapter_prototype.md
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

Review these exact R7AM files:

```text
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
```

Inspect related boundaries read-only:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tests/agent/lightweight_pdf_evidence_bridge_348n.py
tests/agent/source_text_sidecar_loader_348n.py
```

---

## QA Questions

Answer all:

1. Did R7AM modify only allowed files?
2. Is the adapter truly test-only under `tests/agent/`?
3. Is the fixture small and curated, not a full MinerU output dump?
4. Does the fixture include the required Anjing paragraph/table examples?
5. Does the adapter support `content_list_v2` page-grouped structure?
6. Does it extract page number from outer page index correctly?
7. Does it create deterministic locators with page/block/bbox?
8. Does it calculate deterministic `text_sha256` and `char_count`?
9. Does it extract text block evidence correctly?
10. Does it extract table HTML evidence correctly?
11. Does matching require value + metric + period for VERIFIED?
12. Does table matching require row metric + column period + value, or an equivalent conservative rule?
13. Are value-only and metric-only matches rejected?
14. Are duplicate/ambiguous numeric matches conservative?
15. Are DISAGREED and MISSING_EVIDENCE represented distinctly?
16. Does the prototype avoid full source_text serialization into production outputs?
17. Does it avoid STRONG_EVIDENCE promotion?
18. Does it avoid clean_data admission changes?
19. Does it avoid readiness gate changes?
20. Does it avoid MinerU/OCR/LLM/VLM/PDF parser dependencies?
21. Are tests sufficient for the current slice?
22. What limitations should be carried into the next task?

---

## Boundary Checks

Must confirm:

```text
no datefac_agent/ changes
no dependency changes
no output/comparison files committed
no full MinerU artifact committed
no DateFac Excel committed
no production pipeline hook
no MinerU run
no OCR / LLM / VLM use
VERIFIED remains non-promotional
readiness_gates remain CLOSED
```

---

## Validation Commands

Run and report:

```text
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent/test_mineru_artifact_adapter_348n.py -q
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Do not run full unrelated test suites unless needed to investigate a failure.

---

## Allowed Scope

Allowed to create exactly one QA report:

```text
docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md
```

No other file may be changed unless a blocking defect requires a tiny QA fix. If a fix is needed, stop first and report the proposed fix instead of silently broadening scope.

---

## Expected Report Content

The report must include:

```text
Task ID
Task size / reasoning level used
Preflight
Files reviewed
Implementation review
Fixture review
Adapter behavior review
Matching helper review
Test coverage review
Boundary review
Validation outputs
Limitations
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
fixture_review_result（fixture审查结果）=
adapter_review_result（adapter审查结果）=
matching_helper_review_result（匹配助手审查结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be one of:

```text
348N-R7AN controlled adapter integration design
348N-R7AN test-only MinerU adapter comparison dry-run
348N-R7AN source_text sidecar bridge integration design
```

Choose based on QA findings.

---

## Commit / Push Rule

If QA passes and only the QA report is created, stage exactly:

```text
git add docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AM QA review"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
