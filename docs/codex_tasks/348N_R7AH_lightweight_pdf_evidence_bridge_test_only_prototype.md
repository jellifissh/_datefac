# 348N-R7AH lightweight PDF evidence bridge test-only prototype

## Execution sizing

```text
task_size = large
recommended_reasoning_level = max
execution_mode = phased-hard-stop + implementation-with-self-QA
reason = R7AH implements a bounded test-only prototype for the lightweight PDF evidence bridge. It should prove the low-cost evidence anchor route without adding production PDF parsing, new dependencies, MinerU, OCR, LLM, VLM, or real PDF runs.
```

## Task Goal

Implement a test-only lightweight PDF evidence bridge prototype using synthetic page-text fixtures.

Task ID:

```text
348N-R7AH lightweight PDF evidence bridge test-only prototype
```

This is implementation + tests + self-QA, but test-only.

Do not add production PDF parser code.

Do not add dependencies.

Do not run real PDFs.

Do not run MinerU, OCR, LLM, or VLM.

Do not connect this prototype to runner / CLI / run_pilot.

---

## Background

R7AG design concluded:

```text
MinerU-first is not acceptable as default
lightweight PDF evidence bridge should be the default cost-control layer
existing extraction products provide hints: page_number / metric_name / period / value
PDF text-layer/page-text provider supplies lower-cost source_text snippets
page-number rows should extract only target pages
no-page rows should use capped candidate search
trusted snippets require value + metric + period proximity
Excel/JSON raw excerpts are hints, not trusted evidence by default
MinerU/OCR/manual review are fallback paths, not default
VERIFIED remains non-promotional for STRONG_EVIDENCE, clean_data, and readiness
```

R7AF-QA confirmed:

```text
file-backed sidecar loader is valid and test-only
full source_text is not serialized
evidence_index metadata-only
review_queue compact-only
bad sidecars fail closed
pytest tests/agent -q = 162 passed
readiness_gates = CLOSED
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
docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md
docs/codex_tasks/348N_R7AG_lightweight_pdf_evidence_bridge_design.md
docs/agent/348N_R7AF_QA_SOURCE_TEXT_FILE_BACKED_SIDECAR_LOADER_REVIEW.md
docs/codex_tasks/348N_R7AF_test_only_source_text_file_backed_sidecar_loader_implementation.md
```

Inspect implementation read-only before editing:

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

## Phase Rules

This is a larger task, but it must remain test-only and stop at checkpoints.

### Phase 1: Plan

Write a short internal implementation plan before editing.

The plan must answer:

```text
Where will the test-only bridge helper live?
What synthetic extraction-row objects/fixtures will be used?
What synthetic page-text provider will be used?
How will value / metric / period anchors be matched?
How will SourceTextEvidence records be produced?
What tests prove no MinerU/default-heavy path was introduced?
```

If any required boundary cannot be preserved, stop and report.

### Phase 2: Implement test-only bridge helper

Preferred placement:

```text
tests/agent/lightweight_pdf_evidence_bridge_348n.py
```

Allowed alternative if cleaner:

```text
tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
```

Do not put implementation under `datefac_agent/` in this task.

The prototype should use synthetic page text fixtures, not real PDFs.

### Phase 3: Tests

Add tests for positive anchor matching, conservative failures, SourceTextEvidence mapping, and output serialization boundaries.

### Phase 4: Validation and self-QA

Run all validation commands and include self-QA in the final report.

Stop after push. Do not begin R7AI.

---

## Required Prototype Behavior

The prototype should model this cheap path:

```text
existing row hints
+ synthetic PDF page text provider
+ anchor matching
-> SourceTextEvidence sidecar-like records
-> existing agreement checker / evidence_index / review_queue tests
```

It must not parse PDFs directly.

It must not import PyMuPDF/pdfplumber/pypdf.

It must not add dependencies.

It must not call MinerU/OCR/LLM/VLM.

---

## Suggested Test-Only Objects

Use lightweight dataclasses or simple dictionaries under tests only.

A synthetic row hint should include:

```text
source_document_id
source_file_sha256 or synthetic equivalent
page_number optional
metric_name
period
value
unit optional
row_id optional
```

A synthetic page text provider should expose a simple call like:

```text
get_page_text(source_document_id, page_number) -> str | None
search_pages(source_document_id, max_pages=None) -> iterable[(page_number, text)]
```

Keep this provider in tests only.

---

## Required Matching Rules

Implement conservative anchor logic in tests only:

```text
value + metric + period proximity -> can produce SourceTextEvidence
value only -> no trusted SourceTextEvidence; return conservative no-match status
metric + period but no value -> no trusted SourceTextEvidence
value found on wrong page -> no trusted SourceTextEvidence for page-number row
no page_number -> capped candidate page search can match only if value + metric + period proximity exists
multiple occurrences of same numeric value -> require deterministic snippet selection and record ambiguity when not unique
```

Use existing numeric normalization behavior where practical, or implement a narrow test-only normalizer that covers:

```text
commas
decimals
negative sign
parentheses negative
percent
Chinese units 万 / 亿 as text-nearby hints, not automatic unit conversion unless explicitly designed in R7AG
```

Do not overbuild a production normalizer.

---

## SourceTextEvidence Mapping Requirements

When a match is accepted, create `SourceTextEvidence` with:

```text
source_text_id deterministic from row/page/match position or synthetic stable id
source_document_id from row/provider
page_number matched page
locator lightweight format, e.g. page:<n>:text_anchor:<start>-<end>
text_kind = lightweight_page_text_snippet
text = snippet around match
text_sha256 = sha256 UTF-8 of snippet
char_count = len(snippet)
trusted_source = true only for synthetic PDF text provider positive match
extraction_method = lightweight_pdf_text_bridge_test_fixture
```

Do not serialize full text into evidence_index or review_queue.

---

## Required Test Coverage

### Positive cases

1. Page-number row with value + metric + period on that page produces `SourceTextEvidence`.
2. No-page-number row can find a capped candidate page only when value + metric + period proximity exists.
3. Produced evidence can drive existing agreement checker to `VERIFIED`.
4. Evidence index output remains metadata-only and excludes snippet text.
5. Review queue output remains compact-only and excludes snippet text.

### Conservative negative cases

6. Value-only match does not create trusted SourceTextEvidence.
7. Metric + period but missing value does not create trusted SourceTextEvidence.
8. Page-number row with value on a different page does not match.
9. Ambiguous duplicate value without strong proximity does not create trusted SourceTextEvidence.
10. Missing PDF text layer / provider returns no text -> no trusted SourceTextEvidence, row remains `UNVERIFIED` or review-required.
11. Synthetic scanned-PDF marker / empty extracted text -> fallback-needed status, no trusted SourceTextEvidence.

### Boundary cases

12. No MinerU/OCR/LLM/VLM imports or calls.
13. No production path hook.
14. `VERIFIED` does not become `STRONG_EVIDENCE`.
15. `VERIFIED` does not clean-admit rows.
16. readiness gates remain closed.
17. Existing R7AF sidecar tests still pass.

---

## Suggested Status Values

For test-only bridge return objects, use explicit statuses such as:

```text
MATCHED_SNIPPET
NO_VALUE_MATCH
NO_KEYWORD_PROXIMITY
NO_PERIOD_PROXIMITY
PAGE_TEXT_MISSING
PAGE_MISMATCH
AMBIGUOUS_DUPLICATE_VALUE
SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED
```

Do not add production schema fields unless you stop and justify why tests cannot proceed without it.

---

## Allowed Scope

Allowed files:

```text
tests/agent/lightweight_pdf_evidence_bridge_348n.py
tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
```

Allowed to update if needed:

```text
tests/agent/test_source_text_sidecar_loader_348n.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Do not modify production code.

Do not modify docs in this task.

Do not create input/output/temp/data artifacts.

---

## Forbidden Actions

Do not modify:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/
datefac_agent/
input/
output/
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

Do not import PyMuPDF/pdfplumber/pypdf.

Do not add dependencies.

Do not add production PDF parser code.

Do not change sidecar loader behavior unless the task cannot proceed and you stop to report.

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

If a py_compile target does not exist because you chose a different allowed placement, explain and compile the actual created files.

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Final Report

The execution report must include:

```text
Task ID
Task size / reasoning level used
Execution mode used
Preflight
Files modified
Prototype placement
Synthetic provider design
Anchor matching behavior
SourceTextEvidence mapping
Positive cases covered
Conservative negative cases covered
Boundary checks
No-heavy-parser verification
Evidence index serialization check
Review queue serialization check
Validation outputs
Commit hash
Push result
Final git status
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
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AH-QA lightweight PDF evidence bridge prototype review
```

---

## Commit / Push Rule

If and only if:

1. only allowed test helper/test files were modified,
2. validation commands were run and reported,
3. `git diff --name-only` contains only allowed test files,
4. `git diff --check` is clean,
5. no production/docs/output/input/temp/data/config/dependency files were modified,

then stage only exact modified files with explicit path staging.

Do not use broad staging commands.

Suggested commit message:

```text
test: add lightweight PDF evidence bridge prototype
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
