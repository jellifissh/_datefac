# 348N-R7AJ dependency audit for real PDF text-layer provider

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = dependency-audit-only
reason = R7AJ decides whether the real PDF text-layer provider can proceed with current project dependencies, or whether dependency addition must be split into a separate task. It must not implement parsing, add dependencies, run real PDFs, or open any production path.
```

## Task Goal

Audit the current dependency/config state and recommend the safest next slice for a real PDF text-layer provider.

Task ID:

```text
348N-R7AJ dependency audit for real PDF text-layer provider
```

This is a dependency audit / design review task.

Create one audit report only.

Do not implement code.

Do not change tests.

Do not add dependencies.

Do not run real PDFs.

Do not run MinerU, OCR, LLM, or VLM.

---

## Background

R7AI completed with:

```text
Decision = PASS，348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN_VALID
dependency_strategy_result = PASS，next step is R7AJ dependency audit
cost_control_result = PASS
cache_design_result = PASS
fallback_policy_result = PASS
readiness_gates = CLOSED
```

R7AI kept the provider lightweight-first: MinerU/OCR are fallback only, full source_text is not serialized, and VERIFIED is non-promotional.

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

Read first:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md
docs/codex_tasks/348N_R7AI_real_pdf_text_layer_provider_design.md
docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md
docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
```

Inspect read-only:

```text
tests/agent/lightweight_pdf_evidence_bridge_348n.py
tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
```

Inspect dependency/config files read-only if present:

```text
pyproject.toml
requirements.txt
requirements-dev.txt
setup.cfg
setup.py
Pipfile
poetry.lock
uv.lock
```

If a file is absent, report `NOT_PRESENT`.

---

## Core Audit Problem

Answer:

```text
Can the next real PDF text-layer provider implementation proceed safely with existing dependencies, or must dependency addition be split into a separate task?
```

Do not choose a library casually. Weigh current availability, optional-import feasibility, Windows risk, text extraction ability, page selection, scanned-PDF behavior, performance, and whether the choice could make heavy parsing the default.

---

## Audit Questions

### Existing dependency inventory

1. Which dependency/config files exist?
2. Is any PDF text extraction library already declared?
3. Is PyMuPDF / fitz declared?
4. Is pdfplumber declared?
5. Is pypdf / PyPDF2 declared?
6. Is pdfminer.six declared?
7. Are lock files present?
8. What dependency workflow does the project appear to use?

### Candidate comparison

Compare:

```text
pypdf
PyMuPDF / fitz
pdfplumber
pdfminer.six
no new dependency yet / adapter boundary only
```

For each, summarize page text extraction fit, page-selection fit, Windows/install risk, scanned-PDF behavior, performance expectation, and fit for lightweight-first provider.

Use local repository evidence. Do not browse the internet unless you explicitly report why local evidence is insufficient.

### Implementation readiness

9. If a suitable dependency is already present, which provider should the next task implement first?
10. If no suitable dependency is present, should the next task be adapter-boundary-only or a separate optional dependency design?
11. Should optional imports be used?
12. How should missing dependency be represented in provider status?
13. Should the first implementation be test-only, demo-only, or production-code reachable?
14. Should generated in-test PDF be used, or should real PDF files remain deferred?
15. Should cache manifest implementation be included or deferred?
16. What is the smallest safe next scope?

### Risk and boundary check

17. Could adding a dependency pull the project toward batch PDF production too early?
18. Could any candidate behave like OCR/heavy parsing by default?
19. How should scanned/image-only PDFs be handled?
20. How should encrypted/unreadable PDFs be handled?
21. How should page-count and max-page controls be enforced?
22. What must stay metadata-only and review_queue-first?
23. What remains out of scope?

---

## Required Audit Position

The audit must be conservative:

```text
Do not add dependencies in R7AJ.
Do not implement PDF parsing in R7AJ.
Do not run real PDFs in R7AJ.
If no suitable dependency is already present, recommend a separate optional-dependency task or adapter-boundary-only task.
If a suitable dependency is already present, still recommend a narrow test-only or demo-only provider slice first.
MinerU remains fallback, not default.
OCR remains fallback, not default.
Scanned PDFs must return fallback-required status and must not silently pass.
Full source_text must not be serialized to evidence_index/review_queue.
VERIFIED does not imply STRONG_EVIDENCE, clean_data admission, or production readiness.
```

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md
```

No other file may be created or modified.

---

## Forbidden Actions

Do not modify code, tests, fixtures, dependency/config files, input/output/temp/data, previous reports, or production package files.

Do not run real PDFs, workbook reruns, run_pilot, MinerU, OCR, LLM, or VLM.

Do not add PDF extraction code.

Do not add dependencies or run dependency installation commands.

Do not change sidecar loader, lightweight bridge prototype, MARKET_REFERENCE_ROW policy, qualitative_facts admission, clean_candidate_policy, evidence_level promotion, or readiness gates.

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
Dependency/config inventory
Existing PDF library findings
Candidate comparison
Recommended dependency strategy
Optional import strategy
Missing dependency status design
Implementation readiness decision
Recommended next slice
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
dependency_inventory_result（依赖盘点结果）=
pdf_library_available_result（PDF库可用性结果）=
dependency_strategy_result（依赖策略结果）=
implementation_readiness_result（实现准备度结果）=
risk_control_result（风险控制结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should be one of:

```text
348N-R7AK real PDF text-layer provider test-only implementation
348N-R7AK optional PDF dependency addition design
348N-R7AK adapter-boundary-only provider skeleton
```

Choose based on audit evidence.

---

## Commit / Push Rule

If exactly one audit report was created, validation passed, and `git diff --name-only` contains only the allowed report, stage exactly:

```text
git add docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AJ dependency audit"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
