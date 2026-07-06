# 348N-R7AI real PDF text-layer provider design

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AI designs the first path from synthetic page text toward real PDF text-layer extraction. It must preserve the lightweight-first cost-control route while preventing accidental production parser integration, dependency creep, heavy-parser fallback by default, or readiness boundary leaks.
```

## Task Goal

Design a real PDF text-layer provider for the lightweight evidence bridge.

Task ID:

```text
348N-R7AI real PDF text-layer provider design
```

This is a design / review task.

Do not implement code.

Do not modify tests.

Do not add dependencies.

Do not run real PDFs.

Do not run MinerU, OCR, LLM, or VLM.

Create one design report only.

---

## Background

R7AH-QA confirmed:

```text
R7AH lightweight bridge prototype is valid
prototype is test-only under tests/agent/
synthetic page-text provider only
no real PDF IO
no PyMuPDF/pdfplumber/pypdf imports
no new dependencies
no MinerU/OCR/LLM/VLM
no production hook
accepted match requires value + metric + period proximity
conservative failures remain conservative
evidence_index metadata-only
review_queue compact-only
full snippet text is not serialized
VERIFIED does not affect STRONG_EVIDENCE, clean admission, or readiness
pytest tests/agent -q = 180 passed
readiness_gates = CLOSED
```

R7AI is the next design step: move from synthetic provider design toward a real PDF text-layer provider, but still without implementation or real runs.

The goal is not batch PDF production.

The goal is a narrow design for one lightweight provider layer that can later be implemented safely.

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
docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md
docs/codex_tasks/348N_R7AH_QA_lightweight_pdf_evidence_bridge_prototype_review.md
docs/codex_tasks/348N_R7AH_lightweight_pdf_evidence_bridge_test_only_prototype.md
docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md
```

Inspect implementation read-only:

```text
tests/agent/lightweight_pdf_evidence_bridge_348n.py
tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
tests/agent/source_text_sidecar_loader_348n.py
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/review/clean_candidate_policy.py
```

Inspect project dependency/config files read-only, only to determine whether any PDF text dependency already exists:

```text
pyproject.toml
requirements.txt
setup.cfg
setup.py
```

If some files do not exist, report that.

---

## Core Design Problem

The design must answer:

```text
How should DateFac move from synthetic page-text provider to a real PDF text-layer provider without turning real PDF parsing into an uncontrolled production path?
```

The answer must keep:

```text
lightweight-first
single-PDF/single-provider first
no MinerU-first
no OCR default
cache-aware
review_queue-first
readiness gates closed
```

---

## Design Questions To Answer

### A. Provider boundary

1. What interface should a real PDF text-layer provider expose?
2. Should it mirror the synthetic provider API from R7AH?
3. What methods are needed: `get_page_text`, `search_pages`, `page_count`, `has_text_layer`, `provider_metadata`?
4. What input identity should be used: file path, source_document_id, source_file_sha256, or all three?
5. What should be returned for missing pages, invalid page numbers, encrypted PDFs, unreadable PDFs, and empty text pages?
6. How should provider errors be represented without crashing the audit pipeline?

### B. Dependency strategy

7. Should the first real provider use an optional dependency boundary?
8. Should the design prefer PyMuPDF, pdfplumber, pypdf, or no specific library yet?
9. Should R7AJ implementation be dependency-free if no suitable library is already present?
10. If a dependency is needed, should it be isolated behind an adapter module and optional import?
11. How should missing dependency be handled?
12. Should adding any dependency require a separate task and QA?

### C. Text-layer detection

13. How should the provider detect text-layer availability?
14. How should it distinguish text-layer PDF from scanned/image-only PDF?
15. What threshold should mark a page/document as text-empty?
16. What status should be returned for scanned/image-only documents?
17. Should scanned PDFs trigger MinerU/OCR automatically or only return fallback-required?

### D. Page selection and cost control

18. How should the provider extract only requested pages when page_number exists?
19. How should capped candidate search work when page_number is missing?
20. What max-pages or max-candidates controls should exist?
21. How should extraction avoid reading every page for dozens of PDFs by default?
22. What should happen when page_count exceeds a configured limit?
23. How should repeated runs reuse cached page text?

### E. Caching and manifest design

24. What cache key should be used: source_file_sha256 + provider_name + provider_version + extraction_config_hash?
25. What should be cached: page_text, page_hash, page_char_count, text_layer_status, extraction errors, provider metadata?
26. Where should cache live for demo/test runs?
27. Should cache files be committed? Default answer should be no.
28. What should a cache manifest look like?
29. When should cache be invalidated?
30. How should the design prevent stale PDF/source mismatch?

### F. Bridge integration

31. How should real provider output flow into the existing lightweight bridge anchor matcher?
32. Should R7AJ implementation reuse R7AH test-only matcher or introduce a production candidate under `datefac_agent/`?
33. If production code is introduced later, what minimal module boundary should be used?
34. How should SourceTextEvidence be created from real PDF page text snippets?
35. What `extraction_method` should be used?
36. What `text_kind` should be used?
37. How should `trusted_source` be interpreted for real text-layer extraction?

### G. Agreement and confidence boundary

38. Should real PDF text-layer snippets be allowed to drive `VERIFIED`?
39. What additional conditions are required beyond value + metric + period proximity?
40. Should `VERIFIED` from lightweight provider remain `WEAK_EVIDENCE`?
41. Should any real provider result ever promote to `STRONG_EVIDENCE` in this phase?
42. What cases must remain `UNVERIFIED` or review-required?
43. How should ambiguity be represented?

### H. Fallback policy

44. When should MinerU be recommended?
45. When should OCR be recommended?
46. When should manual review be recommended?
47. Should fallback be automatic or explicit/manual at this stage?
48. How should fallback-needed statuses enter review_queue?

### I. Test and implementation slicing

49. What should R7AJ implement first?
50. Should R7AJ be test-only, demo-only, or production-code reachable?
51. Should R7AJ use a tiny local fake PDF file, a generated in-test PDF, or still avoid real PDF files?
52. What tests should be required?
53. What must remain out of scope?

---

## Required Design Position

The report must take a conservative position:

```text
real PDF text-layer provider is still lightweight evidence, not production readiness
MinerU remains fallback, not default
OCR remains fallback, not default
scanned/image-only PDF must not silently pass
raw Excel/JSON excerpts remain hints, not trusted evidence
cache outputs are generated artifacts and should not be committed by default
full source_text must not be serialized to evidence_index or review_queue
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean_data admission
VERIFIED does not imply production readiness
```

If the design proposes production-code implementation later, it must keep the first slice narrow and QA-gated.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md
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
tests/
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

Do not change lightweight bridge prototype behavior.

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
Problem statement
Provider boundary design
Dependency strategy
Text-layer detection policy
Page selection / cost-control policy
Cache and manifest design
Bridge integration design
SourceTextEvidence mapping
Agreement and confidence boundary
Fallback policy
Implementation slice recommendation
Test plan for R7AJ
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
provider_design_result（provider设计结果）=
dependency_strategy_result（依赖策略结果）=
cost_control_result（成本控制结果）=
cache_design_result（缓存设计结果）=
fallback_policy_result（fallback策略结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be one of:

```text
348N-R7AJ real PDF text-layer provider test-only implementation
348N-R7AJ dependency audit for real PDF text-layer provider
```

Choose based on whether an acceptable PDF text dependency already exists.

---

## Commit / Push Rule

If and only if:

1. exactly one design report was created under `docs/agent/`,
2. no code/tests/fixtures/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AI real PDF text layer provider design"
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
