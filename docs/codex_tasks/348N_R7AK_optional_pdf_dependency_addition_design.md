# 348N-R7AK optional PDF dependency addition design

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AJ confirmed there is no declared project PDF text-layer dependency. R7AK must choose a safe optional dependency strategy before any implementation or install occurs.
```

## Task Goal

Design the optional PDF text-layer dependency addition plan for the future real PDF text-layer provider.

Task ID:

```text
348N-R7AK optional PDF dependency addition design
```

This is a design task only.

Do not add dependencies.
Do not run install commands.
Do not implement PDF parsing.
Do not run real PDFs.
Do not run MinerU, OCR, LLM, or VLM.
Create one design report only.

---

## Background

R7AJ dependency audit concluded:

```text
Decision = PASS，348N_R7AJ_DEPENDENCY_AUDIT_CONFIRMED_NO_DECLARED_PDF_TEXT_LAYER_DEPENDENCY
pdf_library_available_result = NO_DECLARED_PROJECT_PDF_TEXT_LAYER_LIBRARY
implementation_readiness_result = NOT_READY
recommended_next_task = 348N-R7AK optional PDF dependency addition design
```

Current project dependency state:

```text
only minimal requirements.txt exists
no declared PyMuPDF / fitz
no declared pdfplumber
no declared pypdf / PyPDF2
no declared pdfminer.six
no declared reportlab
local environment packages do not count as project dependencies
```

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
docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md
docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md
docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md
```

Inspect dependency/config files read-only:

```text
requirements.txt
pyproject.toml
requirements-dev.txt
setup.cfg
setup.py
Pipfile
poetry.lock
uv.lock
```

If absent, report `NOT_PRESENT`.

---

## Design Questions

Answer all:

1. Which candidate should be the first optional PDF text-layer dependency: pypdf, PyMuPDF, pdfplumber, or pdfminer.six?
2. Why is it the best fit for lightweight text-layer extraction rather than heavy parsing?
3. What are the Windows install risks?
4. What are native/binary dependency risks?
5. What are page-level extraction capabilities?
6. What are scanned/image-only PDF limitations?
7. What should happen for encrypted/unreadable PDFs?
8. Should the dependency be required or optional?
9. How should optional import be structured?
10. What provider status should be returned when dependency is missing?
11. Which file should be changed in the future dependency-add task?
12. Should dependency addition be separated from provider implementation?
13. Should the first provider implementation be test-only, demo-only, or production-reachable?
14. Should generated in-test PDFs be used later, or still avoid real PDF files at first?
15. What QA gates are required before adding the dependency?
16. What QA gates are required after adding the dependency?
17. How should the design avoid MinerU-first and OCR-first behavior?
18. How should scanned PDFs return fallback-required instead of silently passing?
19. What remains metadata-only?
20. What remains out of scope?

---

## Required Position

Be conservative:

```text
No dependency is added in R7AK.
No PDF parser is implemented in R7AK.
No real PDF is run in R7AK.
Dependency addition and provider implementation should be separate unless the report gives a strong reason otherwise.
MinerU remains fallback, not default.
OCR remains fallback, not default.
Full source_text is not serialized to evidence_index or review_queue.
VERIFIED does not imply STRONG_EVIDENCE, clean_data admission, or production readiness.
```

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AK_OPTIONAL_PDF_DEPENDENCY_ADDITION_DESIGN.md
```

No other file may be changed.

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

Do not run install commands.

---

## Expected Report Content

Include:

```text
Task ID
Task size / reasoning level used
Preflight
Files reviewed
Candidate comparison
Recommended dependency
Optional import design
Missing dependency status design
Dependency addition plan
Provider implementation separation decision
QA gates
Risk review
Boundary review
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
candidate_selection_result（候选库选择结果）=
optional_dependency_design_result（可选依赖设计结果）=
dependency_addition_plan_result（依赖添加计划结果）=
provider_implementation_split_result（provider实现拆分结果）=
risk_control_result（风险控制结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be one of:

```text
348N-R7AL optional PDF dependency addition implementation
348N-R7AL adapter-boundary-only provider skeleton
```

---

## Commit / Push Rule

If exactly one report was created and validation passed, stage exactly:

```text
git add docs/agent/348N_R7AK_OPTIONAL_PDF_DEPENDENCY_ADDITION_DESIGN.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AK optional PDF dependency design"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
