# 348N-R7AM test-only MinerU artifact adapter prototype

## Execution sizing

```text
task_size = medium
recommended_reasoning_level = max
execution_mode = implementation-with-self-QA
reason = R7AL completed a real controlled DateFac-vs-MinerU dry-run with strong results. R7AM should convert the proven local comparison shape into a small test-only MinerU artifact adapter prototype without touching production code, committing full MinerU outputs, or opening readiness gates.
```

## Task Goal

Implement a **test-only** MinerU artifact adapter prototype that can read a tiny MinerU-like fixture and emit SourceTextEvidence-like evidence blocks suitable for future DateFac comparison.

Task ID:

```text
348N-R7AM test-only MinerU artifact adapter prototype
```

This is not production integration.

Do not modify `datefac_agent/` production code.
Do not commit full MinerU output.
Do not run MinerU.
Do not run OCR, LLM, or VLM.
Do not run real PDF extraction.
Do not add dependencies.
Do not open readiness gates.

---

## Background

R7AL controlled comparison dry-run completed locally with:

```text
DateFac candidate rows normalized = 451
MinerU blocks indexed = 173
VERIFIED = 395
review_required_total = 56
DISAGREED = 10
AMBIGUOUS = 10
MISSING_EVIDENCE = 2
required 11 probe examples = all found and VERIFIED against MinerU v2 blocks
primary input recommendation = content_list_v2
fallback/cross-check = content_list
readiness_gates = CLOSED
```

R7AL outputs stayed local under:

```text
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\
```

Do not commit those output files.

R7AM should take the useful shape from R7AL and make a small, test-only, repeatable prototype under `tests/agent/`.

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
docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md
docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md
docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md
```

Read local R7AL outputs if present, but do not commit them:

```text
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\anjing_datefac_vs_mineru_comparison_summary.md
D:\_datefac_agent\output\comparison\anjing_foods_datefac_vs_mineru\run_anjing_comparison.py
```

If these local files are absent, continue using the R7AL execution report summary above.

Inspect implementation read-only:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/audit/evidence_checker.py
tests/agent/lightweight_pdf_evidence_bridge_348n.py
tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
tests/agent/source_text_sidecar_loader_348n.py
```

---

## Allowed Files

Allowed to create or modify only:

```text
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

Do not modify any other files.

The fixture must be small and manually curated. It must not be a full MinerU output dump.

---

## Prototype Requirements

Implement a test-only adapter module under:

```text
tests/agent/mineru_artifact_adapter_348n.py
```

It should support MinerU `content_list_v2`-style input shaped like:

```text
[
  [page_1_blocks],
  [page_2_blocks],
  ...
]
```

The adapter should extract evidence blocks from:

```text
paragraph / title / page_header / page_footer / page_number
table blocks with content.html
```

Each extracted block should include:

```text
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
```

Use metadata-only practices:

```text
source_text_id should be deterministic
locator should include page/block/bbox
test report may include short preview only
full source_text must not be serialized into evidence_index/review_queue outputs
```

The prototype may use a lightweight local dataclass or dict. It may also instantiate existing SourceTextEvidence model if doing so does not require production changes. Do not change production schemas.

---

## Matching Helper Requirements

Implement a small deterministic helper for tests only:

```text
find_mineru_evidence_for_candidate(row, blocks)
```

It should be conservative:

```text
VERIFIED only if value + metric + period are found in the same text/table block, or table structure clearly supports row metric + column period + value.
UNVERIFIED if only partial match exists.
AMBIGUOUS if multiple plausible blocks match and cannot be disambiguated.
MISSING_EVIDENCE if no usable block exists.
DISAGREED if metric + period are present but the expected value is absent and conflicting numeric candidates are present.
```

Keep this helper test-only. Do not wire it into production.

---

## Fixture Requirements

Create a tiny fixture:

```text
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
```

It must include only a minimal subset sufficient to test:

1. A text paragraph from Anjing page 1:

```text
2026Q1 实现营业收入 47.10 亿元，同比+30.84%；归母净利润 5.63 亿元，同比+42.74%，扣非归母净利润 5.25 亿元，同比+53.04%。毛利率达到 24.99%（同比+1.67pct），净利率达到 12.05%（同比+1.12pct）。
```

2. A table block from the financial data / valuation table with enough rows/columns to test:

```text
EPS(摊薄/元), 2026E = 5.37
P/E(倍), 2026E = 18.3
营业收入(百万元), 2026E = 18,379
净利润(百万元), 2026E = 1,791
ROE(%), 2026E = 10.3
P/B(倍), 2026E = 1.9
```

3. A negative/ambiguous block if needed to test conservative behavior.

Do not include the whole original MinerU artifact.

---

## Required Tests

Create tests under:

```text
tests/agent/test_mineru_artifact_adapter_348n.py
```

Cover at least:

1. Loads minimal `content_list_v2` fixture.
2. Extracts page_number from outer page index.
3. Emits deterministic locator with page/block/bbox.
4. Emits deterministic `text_sha256` and `char_count`.
5. Extracts text paragraph evidence.
6. Extracts table HTML evidence.
7. Verifies 2026Q1 营业收入 = 47.10 亿元.
8. Verifies 2026Q1 归母净利润 = 5.63 亿元.
9. Verifies 2026Q1 毛利率 = 24.99%.
10. Verifies 2026E EPS = 5.37.
11. Verifies 2026E PE = 18.3.
12. Verifies 2026E 营业收入 = 18379 / 18,379.
13. Does not verify value-only match.
14. Does not verify metric-only match.
15. Marks ambiguous duplicate numeric evidence conservatively.
16. Does not treat VERIFIED as STRONG_EVIDENCE or clean admission.
17. Does not require MinerU, OCR, LLM, VLM, or PDF parser dependency.

---

## Boundary Rules

Forbidden:

```text
modify datefac_agent/
modify production pipeline
modify existing tests unrelated to this task
commit full MinerU output
commit DateFac output
commit comparison xlsx/csv/md outputs
run MinerU
run OCR / LLM / VLM
add dependencies
run pip install / uv add / poetry add
open readiness gates
promote VERIFIED to STRONG_EVIDENCE
promote VERIFIED to clean_data admission
```

Allowed:

```text
small curated test fixture under tests/agent/fixtures/mineru_artifacts/
test-only adapter helper under tests/agent/
test-only report under docs/agent/
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

---

## Expected Report Content

Create:

```text
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

Include:

```text
Task ID
Task size / reasoning level used
Preflight
Files reviewed
Files created/modified
Fixture scope
Adapter behavior
Matching helper behavior
Test coverage
Validation outputs
Boundary review
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
fixture_result（fixture结果）=
adapter_result（adapter结果）=
matching_helper_result（匹配助手结果）=
boundary_check（边界检查）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

Recommended next task should normally be:

```text
348N-R7AM-QA test-only MinerU artifact adapter prototype review
```

---

## Commit / Push Rule

If and only if validation passes and `git diff --name-only` contains only the allowed files, stage exactly:

```text
git add tests/agent/mineru_artifact_adapter_348n.py
git add tests/agent/test_mineru_artifact_adapter_348n.py
git add tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
git add docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
```

Do not use broad staging.

Commit:

```text
git commit -m "test: add MinerU artifact adapter prototype"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Stop after push. Do not start the next task.
