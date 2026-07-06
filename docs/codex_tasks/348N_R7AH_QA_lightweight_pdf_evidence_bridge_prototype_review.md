# 348N-R7AH-QA lightweight PDF evidence bridge prototype review

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AH added the first test-only lightweight PDF evidence bridge prototype. QA must verify it proves the low-cost anchor route while staying test-only, synthetic-only, no-heavy-parser, metadata-only, and boundary-safe.
```

## Task Goal

Review and validate the R7AH lightweight PDF evidence bridge test-only prototype.

Task ID:

```text
348N-R7AH-QA lightweight PDF evidence bridge prototype review
```

This is a QA / review task.

Do not modify implementation code.

Do not modify tests.

Do not modify fixtures.

Do not run real PDFs.

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
docs/codex_tasks/348N_R7AH_lightweight_pdf_evidence_bridge_test_only_prototype.md
docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md
```

Review R7AH implementation files:

```text
tests/agent/lightweight_pdf_evidence_bridge_348n.py
tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
```

Also inspect, read-only, if useful:

```text
tests/agent/source_text_sidecar_loader_348n.py
tests/agent/test_source_text_sidecar_loader_348n.py
tests/agent/test_agent_excel_intake_audit_348a.py
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/review/clean_candidate_policy.py
```

---

## QA Questions

Answer all questions in the report:

1. Was R7AH limited to allowed test helper/test files?
2. Does the lightweight bridge live only under `tests/agent/`?
3. Is there no code under `datefac_agent/`?
4. Is there no runner, CLI, `run_pilot(...)`, production hook, or real PDF path?
5. Does the prototype avoid PyMuPDF/pdfplumber/pypdf imports?
6. Does the prototype avoid new dependencies?
7. Does the prototype avoid MinerU/OCR/LLM/VLM calls?
8. Does it use only synthetic page-text provider / fixtures?
9. Does page-number row matching use only the target page?
10. Does no-page-number matching use capped candidate search?
11. Does accepted matching require value + metric + period proximity?
12. Does value-only match fail conservatively without trusted SourceTextEvidence?
13. Does metric + period without value fail conservatively?
14. Does wrong-page value fail conservatively?
15. Does duplicate/ambiguous value fail conservatively or surface ambiguity?
16. Does missing page text fail conservatively?
17. Does scanned/image-only marker require fallback and avoid trusted evidence?
18. Are bridge statuses deterministic and explainable?
19. Does accepted match map into SourceTextEvidence correctly?
20. Is `source_text_id` deterministic/stable?
21. Is locator lightweight and deterministic, e.g. `page:<n>:text_anchor:<start>-<end>`?
22. Are `text_sha256` and `char_count` computed from snippet text?
23. Is `trusted_source=true` used only for accepted synthetic provider matches?
24. Is `extraction_method` test-fixture specific?
25. Can accepted evidence drive existing agreement checker to `VERIFIED`?
26. Does evidence_index remain metadata/hash/count/status only and exclude full snippet text?
27. Does review_queue remain compact-only and exclude full snippet text?
28. Does `VERIFIED` remain non-promotional: no STRONG_EVIDENCE, no clean admission, no readiness change?
29. Do existing R7AF sidecar tests still pass?
30. What are the main compatibility risks before moving to a real PDF text-layer provider?
31. What is the recommended next task?

---

## Expected QA Position

Be strict:

```text
lightweight bridge prototype must be test-only
synthetic page text is not production PDF extraction
no real PDF parser must be introduced
no heavy parser / MinerU / OCR path must be introduced
accepted snippets can support agreement only within test scope
full source_text must not be serialized by default
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean admission
VERIFIED does not imply production readiness
```

If any of these are violated, mark QA as failed or needs fix.

If all are preserved, mark QA as valid.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md
```

No other file may be created or modified.

---

## Forbidden Actions

Do not modify code.

Do not modify tests.

Do not modify fixtures.

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
datefac_agent/
temp/
data/
legacy datefac/
dependencies
config files
```

Do not run real PDFs.

Do not run workbook reruns.

Do not run `run_pilot(...)` or real workbook-family reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not add a PDF extraction pipeline.

Do not add dependencies.

Do not change sidecar loader behavior.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change clean_candidate_policy.

Do not change evidence_level promotion.

Do not change readiness gates.

Do not stage or commit output files.

Do not use broad Git staging.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
python -m py_compile tests/agent/source_text_sidecar_loader_348n.py tests/agent/test_source_text_sidecar_loader_348n.py tests/agent/test_agent_excel_intake_audit_348a.py
python -m py_compile tests/agent/lightweight_pdf_evidence_bridge_348n.py tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
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
Task size / reasoning level used
Preflight
Files reviewed
Prototype placement review
Synthetic provider review
Anchor matching review
Conservative failure review
SourceTextEvidence mapping review
No-heavy-parser review
Evidence index serialization review
Review queue serialization review
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
lightweight_bridge_prototype_result（轻量桥原型结果）=
anchor_matching_result（锚点匹配结果）=
source_text_mapping_result（source_text映射结果）=
no_heavy_parser_result（无重型解析器结果）=
evidence_index_validation_result（证据索引验证结果）=
review_queue_validation_result（复核队列验证结果）=
qa_result（QA结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AI real PDF text-layer provider design
```

But if QA finds issues, recommend a narrow R7AH-FIX task instead.

---

## Commit / Push Rule

If and only if:

1. exactly one QA report was created under `docs/agent/`,
2. no code/tests/fixtures/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AH QA review"
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
