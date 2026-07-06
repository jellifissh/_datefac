# 348N-R7AM test-only MinerU artifact adapter prototype report

## Task ID

```text
348N-R7AM test-only MinerU artifact adapter prototype
```

## Task size / reasoning level used

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = implementation-with-self-QA
reason = Convert the R7AL Anjing DateFac-vs-MinerU controlled comparison shape into a small repeatable test-only adapter prototype under tests/agent without production wiring, full MinerU output commits, new dependencies, or readiness changes.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 6ceddc0..df5b39d
  Fast-forward
  created docs/codex_tasks/348N_R7AK_optional_pdf_dependency_addition_design.md
  created docs/codex_tasks/348N_R7AM_test_only_mineru_artifact_adapter_prototype.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  df5b39d docs: update handoff after R7AL comparison
  699b63c docs: refresh plain-language progress after R7AL comparison
  571c234 docs: sync progress after R7AL comparison
  ea31066 docs: add R7AM MinerU adapter prototype task
  08819e6 docs: refresh plain-language progress for R7AK
  3cb64db docs: sync progress for R7AK
  6c4f566 docs: update handoff for R7AK
  27e9466 docs: add R7AK optional PDF dependency design task
  6ceddc0 docs: add R7AJ dependency audit
  785de6e docs: update handoff after R7AI
  253cfcc docs: refresh plain-language progress after R7AI
  e2f21fd docs: sync progress after R7AI
```

Worktree was clean after pull.

## Files reviewed

Required context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AM_test_only_mineru_artifact_adapter_prototype.md`
- `docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md`
- `docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md`
- `docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md`

Local R7AL outputs reviewed as reference only and not staged:

- `output/comparison/anjing_foods_datefac_vs_mineru/anjing_datefac_vs_mineru_comparison_summary.md`
- `output/comparison/anjing_foods_datefac_vs_mineru/run_anjing_comparison.py`

Read-only implementation context:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `tests/agent/lightweight_pdf_evidence_bridge_348n.py`
- `tests/agent/test_lightweight_pdf_evidence_bridge_348n.py`
- `tests/agent/source_text_sidecar_loader_348n.py`

## Files created/modified

Created exactly the allowed R7AM files:

- `tests/agent/mineru_artifact_adapter_348n.py`
- `tests/agent/test_mineru_artifact_adapter_348n.py`
- `tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json`
- `docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md`

No `datefac_agent/` production files were modified.

## Fixture scope

The fixture is a small curated `content_list_v2`-style payload:

```text
[
  [page_1_blocks],
  [page_2_blocks],
  [page_3_blocks]
]
```

It contains only seven blocks:

1. Page 1 Anjing 2026Q1 paragraph with revenue, attributable net profit, deducted attributable net profit, gross margin, and net margin.
2. Page 1 value-only negative paragraph.
3. Page 1 metric-only / incomplete negative paragraph.
4. Page 2 financial data / valuation table HTML.
5. Page 3 duplicate revenue evidence A.
6. Page 3 duplicate revenue evidence B.
7. Page 3 conflicting gross-margin paragraph.

The fixture is intentionally not a full MinerU output dump and stays below 10 KB.

## Adapter behavior

Implemented test-only adapter in:

```text
tests/agent/mineru_artifact_adapter_348n.py
```

Supported input shape:

```text
list[list[dict]]
```

Supported block types:

```text
paragraph
title
page_header
page_footer
page_number
table
```

Adapter output:

```text
MinerUEvidenceBlock
  source_document_id
  page_number
  page_idx
  block_index
  type
  bbox
  locator
  text_kind
  text
  text_sha256
  char_count
  trusted_source
  extraction_method
  caption_preview
  footnote_preview
  source_text_id
```

Locator is deterministic:

```text
mineru:v2:page:{page_number}:block:{block_index}:bbox:{x1},{y1},{x2},{y2}
```

Hash and count behavior:

```text
text_sha256 = sha256(text UTF-8)
char_count = len(text)
source_text_id = deterministic r7am:<hash-prefix>
```

The helper can convert a block into existing `SourceTextEvidence` shape for tests through `to_source_text_evidence()`, without modifying production schema.

## Matching helper behavior

Implemented:

```text
find_mineru_evidence_for_candidate(row, blocks)
```

Conservative statuses:

```text
VERIFIED
UNVERIFIED
DISAGREED
AMBIGUOUS
MISSING_EVIDENCE
```

Matching rules:

- `VERIFIED` only when value + metric alias + period are present in one text/table block.
- Table `VERIFIED` uses metric row + period column + value cell cross-match when available.
- Value-only evidence returns `UNVERIFIED`.
- Metric/period with conflicting numeric value returns `DISAGREED`.
- Multiple verified-looking evidence blocks return `AMBIGUOUS`.
- Missing page/block/anchors return `MISSING_EVIDENCE` or `UNVERIFIED`.

Numeric normalization supports:

```text
18,379 -> 18379
47.10 -> 47.10
24.99% -> 24.99
+30.84% -> 30.84
```

## Test coverage

Created:

```text
tests/agent/test_mineru_artifact_adapter_348n.py
```

Coverage includes:

- Minimal `content_list_v2` fixture load.
- Page number from outer page index.
- Deterministic locator with page/block/bbox.
- Deterministic `text_sha256`, `char_count`, and `source_text_id`.
- Paragraph evidence extraction.
- Table HTML evidence extraction.
- `SourceTextEvidence` shape conversion.
- 2026Q1 营业收入 = 47.10 亿元.
- 2026Q1 归母净利润 = 5.63 亿元.
- 2026Q1 毛利率 = 24.99%.
- 2026E EPS = 5.37.
- 2026E PE = 18.3.
- 2026E 营业收入 = 18379 / 18,379.
- 2026E 净利润 = 1,791.
- 2026E ROE = 10.3.
- 2026E P/B = 1.9.
- Value-only negative path.
- Metric/period conflict path.
- Ambiguous duplicate evidence path.
- Missing evidence path.
- `VERIFIED` remains non-promotional for `STRONG_EVIDENCE`, clean admission, and readiness.
- No heavy parser / external call imports.
- Fixture is small and not a full MinerU dump.

## Validation outputs

Required validation commands run:

```text
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_mineru_artifact_adapter_348n.py -q
  21 passed in 0.13s

pytest tests/agent -q
  201 passed in 0.86s
```

Pre-stage diff validation:

```text
git status -sb
  allowed R7AM files only

git diff --stat
  allowed R7AM files only

git diff --name-only
  allowed R7AM files only

git diff --check
  PASS
```

## Boundary review

R7AM stayed within the requested boundary:

```text
datefac_agent/ modified = no
production pipeline modified = no
existing unrelated tests modified = no
full MinerU output committed = no
DateFac output committed = no
comparison xlsx/csv/md committed = no
MinerU run = no
OCR / LLM / VLM run = no
new dependency added = no
pip install / uv add / poetry add = no
readiness gates opened = no
VERIFIED -> STRONG_EVIDENCE promotion = no
VERIFIED -> clean_data admission = no
```

Self-QA:

```text
fixture_result = PASS, small curated fixture only
adapter_result = PASS, test-only content_list_v2 evidence blocks generated
matching_helper_result = PASS, conservative positive/negative/ambiguous paths covered
external_call_result = PASS, no MinerU/OCR/LLM/VLM/PDF parser dependency
readiness_gates = CLOSED
```

## Decision

```text
Decision = 348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_VALID
```

R7AM confirms the R7AL MinerU `content_list_v2` evidence shape can be reduced into a repeatable, small, test-only adapter prototype. This does not create production integration, `STRONG_EVIDENCE`, clean admission, or readiness.

## Recommended next task

```text
348N-R7AM-QA test-only MinerU artifact adapter prototype review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_VALID
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent/test_mineru_artifact_adapter_348n.py -q => 21 passed; pytest tests/agent -q => 201 passed
files_modified（修改文件数）= 4
error_count（错误数）= 0
fixture_result（fixture结果）= PASS，小型 curated content_list_v2 fixture，7 blocks，非完整 MinerU output
adapter_result（adapter结果）= PASS，test-only MinerU evidence block adapter created under tests/agent/
matching_helper_result（匹配助手结果）= PASS，VERIFIED / UNVERIFIED / DISAGREED / AMBIGUOUS / MISSING_EVIDENCE conservative paths covered
boundary_check（边界检查）= PASS，no production code/tests/deps/output commit; no MinerU/OCR/LLM/VLM; VERIFIED non-promotional
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AM-QA test-only MinerU artifact adapter prototype review
```
