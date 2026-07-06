# 348N-R7AG lightweight PDF evidence bridge design

## Execution sizing

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AG changes the next integration direction from MinerU-first to lightweight PDF evidence bridging. The design must reduce default workload/cost while preserving evidence safety, source_text metadata boundaries, and review_queue-first behavior.
```

## Task Goal

Design a lightweight PDF evidence bridge that can connect existing extraction products to the original PDF without making MinerU the default path.

Task ID:

```text
348N-R7AG lightweight PDF evidence bridge design
```

This is a design / review task.

Do not implement code.

Do not modify tests.

Do not run real PDFs.

Do not run MinerU, OCR, LLM, or VLM.

Create one design report only.

---

## Background

R7AF-QA confirmed:

```text
R7AF file-backed source_text sidecar loader is valid
loader remains test-only under tests/agent/
JSON object v1 strict schema
invalid sidecars fail closed with no partial records
evidence_index remains metadata-only
review_queue remains compact-only
full source_text is not serialized
VERIFIED does not promote to STRONG_EVIDENCE
VERIFIED does not enter clean_data
readiness gates remain CLOSED
pytest tests/agent -q = 162 passed
```

The previous suggested next task was a single-real-MinerU-artifact adapter design. But the project direction is adjusted because MinerU-first may cause unacceptable time, compute, and labor cost when users provide many PDFs.

R7AG should design a cheaper default bridge:

```text
existing extraction product
+ original PDF text layer / page text / numeric anchors / keyword anchors
-> SourceTextEvidence sidecar
-> DateFac agreement / review_queue
```

MinerU should become a fallback path, not the default first path.

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
docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md
docs/codex_tasks/348N_R7AF_QA_source_text_file_backed_sidecar_loader_review.md
docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md
docs/agent/348N_R7AE_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_DESIGN.md
```

Inspect implementation read-only:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tests/agent/source_text_sidecar_loader_348n.py
tests/agent/test_source_text_sidecar_loader_348n.py
tests/agent/fixtures/source_text_sidecars/r7af_source_text_sidecar__basic_positive_negative__v1.json
```

---

## Core Design Problem

The design must answer:

```text
How can DateFac cheaply connect existing extraction products to the original PDF without requiring MinerU for most runs?
```

The answer should center on a lightweight evidence bridge, not a MinerU adapter.

---

## Design Questions To Answer

The report must answer all questions below.

### A. Input assumptions

1. What minimum fields can an existing extraction product provide?
2. What happens if it has page_number?
3. What happens if it has no page_number?
4. What happens if it has metric_name, period, and values but no source_text?
5. What happens if it has raw excerpt fields from Excel/JSON?
6. Which fields are treated only as hints, not trusted evidence?

### B. Lightweight PDF text extraction path

7. Should the first bridge use PyMuPDF, pdfplumber, pypdf, or an abstract provider interface?
8. Should R7AG recommend adding a new dependency immediately, or designing behind a provider boundary first?
9. How should the system extract only needed pages instead of the full PDF when page_number exists?
10. How should it detect whether the PDF has a text layer?
11. What should happen for scanned/image-only PDFs?
12. How should extraction errors be represented?

### C. Evidence anchor strategy

13. How should the bridge match row values against page text?
14. How should it normalize numeric formats, commas, decimals, negatives, percentages, Chinese units, 万/亿, and parentheses negatives?
15. How should it use metric_name keywords and period anchors near numeric values?
16. How should it handle duplicate numbers on the same page?
17. How should it handle value found on page but keyword not nearby?
18. How should it handle keyword found but value not found?
19. How should it produce snippets around matched text?
20. How should it assign locator values for lightweight matches?

### D. SourceTextEvidence mapping

21. How should lightweight bridge output map into SourceTextEvidence?
22. What should `trusted_source` mean for lightweight PDF text extraction?
23. What should `extraction_method` values be?
24. What should `text_kind` values be?
25. How should text_sha256 and char_count be calculated?
26. How should source_document_id be tied to the original PDF hash/path?

### E. Confidence / status boundary

27. Should lightweight matches produce VERIFIED directly, or a weaker status?
28. Should a value-only match without keyword proximity remain UNVERIFIED or become VERIFIED?
29. Should keyword + value + period proximity be allowed to produce VERIFIED?
30. Should repeated numeric values require multiplicity-aware matching?
31. What cases should be REVIEW_REQUIRED regardless of match?
32. How should `source_text_provider` and `source_text_quality` be represented without breaking existing schemas?

### F. MinerU fallback policy

33. When should MinerU be recommended?
34. When should MinerU be forbidden as default?
35. What should trigger fallback to MinerU or OCR?
36. How should this be exposed as a cost-control policy?
37. How should cached MinerU outputs be reused when available?

### G. Caching and cost control

38. How should `source_file_sha256` control reuse?
39. What cache manifest should be designed?
40. What should be cached: page_text, snippets, sidecar, extraction method, parser version?
41. When should cache be invalidated?
42. How should the design support dozens of PDFs without running heavy parsing by default?

### H. Next implementation slice

43. What should R7AH implement first: provider abstraction, test fixtures, or a tiny PyMuPDF/pypdf prototype?
44. Should R7AH be test-only, demo-only, or production-code reachable?
45. What tests should R7AH require?
46. What remains out of scope?

---

## Required Design Position

The design must be conservative:

```text
MinerU is not the default path
lightweight bridge is a cost-control layer
Excel/JSON raw excerpts are hints, not trusted source_text by default
PDF text-layer extraction is stronger than Excel raw hints but weaker than human review
scanned PDFs require OCR/MinerU/manual review and must not silently pass
value-only matches are risky and should not automatically clean-admit rows
keyword + value + period proximity can support agreement, but not production readiness
full source_text must not be serialized to evidence_index or review_queue
VERIFIED does not imply STRONG_EVIDENCE
VERIFIED does not imply clean_data admission
VERIFIED does not imply production readiness
```

If the design proposes any promotion beyond current boundaries, mark it as future-only and require separate QA.

---

## Allowed Scope

Allowed to create exactly one report:

```text
docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
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

Do not add PDF extraction code.

Do not add dependencies.

Do not add a production PDF parser.

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
Why MinerU-first is not acceptable as default
Input assumptions
Lightweight provider options
Recommended provider boundary
Page text extraction strategy
No-page-number fallback strategy
Evidence anchor matching strategy
Numeric normalization strategy
Keyword / period proximity strategy
Duplicate-number handling
SourceTextEvidence mapping
Provider / quality metadata design
Confidence and boundary policy
Scanned PDF policy
MinerU fallback policy
Caching / manifest design
Cost-control workflow
Risks and failure modes
R7AH implementation recommendation
Out-of-scope list
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
mineru_default_policy（MinerU默认策略）=
lightweight_bridge_design_result（轻量桥设计结果）=
evidence_anchor_design_result（证据锚点设计结果）=
cost_control_result（成本控制结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AH lightweight PDF evidence bridge test-only prototype
```

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
git add docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
```

Do not use broad staging commands.

Commit:

```text
git commit -m "docs: add R7AG lightweight evidence bridge design"
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
