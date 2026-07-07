# 348N-R7AM-QA test-only MinerU artifact adapter prototype review

## Task ID

```text
348N-R7AM-QA test-only MinerU artifact adapter prototype review
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = Review the R7AM test-only MinerU artifact adapter prototype for boundary safety, fixture scope, conservative matching, production isolation, and readiness/clean/evidence non-promotion.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 0de3a4a..c940c47
  Fast-forward
  created docs/codex_tasks/348N_R7AM_QA_test_only_mineru_artifact_adapter_prototype_review.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  c940c47 docs: update handoff after R7AM
  6eebce2 docs: refresh plain-language progress after R7AM
  ab965f8 docs: sync progress after R7AM
  ef99a69 docs: add R7AM QA review task
  0de3a4a test: add MinerU artifact adapter prototype
  df5b39d docs: update handoff after R7AL comparison
  699b63c docs: refresh plain-language progress after R7AL comparison
  571c234 docs: sync progress after R7AL comparison
  ea31066 docs: add R7AM MinerU adapter prototype task
  08819e6 docs: refresh plain-language progress for R7AK
  3cb64db docs: sync progress for R7AK
  6c4f566 docs: update handoff for R7AK
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
- `docs/codex_tasks/348N_R7AM_QA_test_only_mineru_artifact_adapter_prototype_review.md`
- `docs/codex_tasks/348N_R7AM_test_only_mineru_artifact_adapter_prototype.md`
- `docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md`

R7AM files reviewed:

- `tests/agent/mineru_artifact_adapter_348n.py`
- `tests/agent/test_mineru_artifact_adapter_348n.py`
- `tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json`

Related boundary files inspected read-only:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `tests/agent/lightweight_pdf_evidence_bridge_348n.py`
- `tests/agent/source_text_sidecar_loader_348n.py`

## R7AM commit scope review

R7AM implementation commit reviewed:

```text
0de3a4a test: add MinerU artifact adapter prototype
```

Files in that commit:

```text
docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
```

QA result:

```text
PASS: R7AM modified only the four allowed files.
PASS: No datefac_agent/ production files were modified.
PASS: No dependency/config files were modified.
PASS: No output/comparison files were committed.
PASS: No DateFac Excel output was committed.
```

Additional git checks:

```text
git ls-files output/comparison
  no tracked files

git ls-files output/datefac_raw_material_anjing_foods.xlsx
  no tracked file
```

## Adapter placement review

Adapter file:

```text
tests/agent/mineru_artifact_adapter_348n.py
```

QA result:

```text
PASS: adapter is under tests/agent/.
PASS: adapter is not imported by datefac_agent/, runner, CLI, or production pipeline.
PASS: adapter imports only standard library plus existing datefac_agent.schemas.audit_models.SourceTextEvidence for shape compatibility.
PASS: no PyMuPDF / pdfplumber / pypdf / pdfminer / MinerU / OCR / LLM / VLM imports.
```

The adapter remains a test-only prototype, not production integration.

## Fixture review

Fixture file:

```text
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
```

Fixture facts:

```text
fixture_size_bytes = 2599
page_count = 3
block_count_payload = 7
block_count_adapter = 7
pages = [1, 2, 3]
```

Fixture includes:

- Page 1 paragraph for 2026Q1 revenue, attributable net profit, deducted attributable net profit, gross margin, and net margin.
- Page 1 value-only negative block.
- Page 1 metric/period-only incomplete negative block.
- Page 2 financial data / valuation table HTML with EPS, P/E, revenue, profit, ROE, and P/B.
- Page 3 duplicate revenue blocks for ambiguity.
- Page 3 conflicting gross-margin block for DISAGREED.

QA result:

```text
PASS: fixture is small and curated.
PASS: fixture is not a full MinerU output dump.
PASS: fixture contains the required positive and negative coverage seeds.
```

## content_list_v2 structure review

R7AM adapter supports the expected page-grouped shape:

```text
[
  [page_1_blocks],
  [page_2_blocks],
  ...
]
```

QA result:

```text
PASS: outer list index becomes page_idx.
PASS: page_number is generated as page_idx + 1.
PASS: block_index is generated from each page's inner block order.
PASS: paragraph/title/page_header/page_footer/page_number/table block types are supported.
PASS: table block uses content.html.
```

## Evidence block metadata review

Generated block fields include:

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
source_text_id
```

QA result:

```text
PASS: locator includes page/block/bbox.
PASS: text_sha256 is deterministic sha256(text UTF-8).
PASS: char_count equals len(text).
PASS: source_text_id is deterministic.
PASS: text paragraph evidence is extracted.
PASS: table HTML evidence is extracted with caption/footnote previews.
```

Observed locator examples:

```text
mineru:v2:page:1:block:0:bbox:356,205,947,266
mineru:v2:page:1:block:1:bbox:100,300,420,330
mineru:v2:page:1:block:2:bbox:100,340,520,370
```

## Matching helper review

Helper reviewed:

```text
find_mineru_evidence_for_candidate(row, blocks)
```

Supported statuses:

```text
VERIFIED
UNVERIFIED
DISAGREED
AMBIGUOUS
MISSING_EVIDENCE
```

QA probe results:

```text
q1_revenue     -> VERIFIED
q1_net_profit  -> VERIFIED
q1_gross_margin -> VERIFIED
eps            -> VERIFIED
pe             -> VERIFIED
revenue_e      -> VERIFIED
value_only     -> UNVERIFIED
metric_conflict -> DISAGREED
ambiguous      -> AMBIGUOUS
missing        -> MISSING_EVIDENCE
```

QA result:

```text
PASS: VERIFIED requires value + metric + period in one block, or table row/period/value structure.
PASS: table positives are verified through metric row + period column + value cell for the financial table fixture.
PASS: value-only does not become VERIFIED.
PASS: metric/period without expected value can become DISAGREED when conflicting numeric candidates exist.
PASS: duplicate plausible evidence becomes AMBIGUOUS.
PASS: missing page/block/evidence becomes MISSING_EVIDENCE.
```

Conservative note:

```text
The helper remains test-only. Its table matching includes a same-block fallback after structured table matching returns no table result. This is acceptable for this prototype and covered by tests, but future production integration should keep the stricter table-cell cross-check as the default policy.
```

## Boundary policy review

QA result:

```text
PASS: No production pipeline hook.
PASS: No datefac_agent/ modification.
PASS: No tests outside allowed R7AM test file were modified.
PASS: No dependency/config changes.
PASS: No full MinerU output committed.
PASS: No DateFac output committed.
PASS: No comparison xlsx/csv/md output committed.
PASS: No MinerU rerun.
PASS: No OCR / LLM / VLM calls.
PASS: No real PDF parser dependency.
```

## Evidence / clean / readiness review

R7AM tests explicitly verify:

```text
VERIFIED stays agreement_status only.
evidence_level remains WEAK_EVIDENCE.
clean_candidate_type remains REVIEW_REQUIRED for MARKET_REFERENCE_ROW fixture.
client_ready = false.
production_ready = false.
formal_client_export_allowed = false.
demo_export_only = true.
```

Related production delivery/review code remains metadata-only for source_text serialization:

```text
evidence_index writes source_text_id/source/page/locator/kind/sha256/char_count/status metadata, not full text.
review_queue writes compact source_text status/page/locator fields, not full text.
```

QA result:

```text
PASS: VERIFIED did not promote to STRONG_EVIDENCE.
PASS: VERIFIED did not change clean_data admission.
PASS: readiness gates remain CLOSED.
```

## Test review

R7AM test file covers 21 cases:

- fixture load and smallness
- page number from outer page index
- deterministic locator/hash/count/source_text_id
- paragraph evidence extraction
- table HTML evidence extraction
- existing SourceTextEvidence shape conversion
- 2026Q1 营业收入 = 47.10
- 2026Q1 归母净利润 = 5.63
- 2026Q1 毛利率 = 24.99
- 2026E EPS = 5.37
- 2026E PE = 18.3
- 2026E 营业收入 = 18379 / 18,379
- 2026E 净利润 = 1,791
- 2026E ROE = 10.3
- 2026E P/B = 1.9
- value-only negative
- metric/period conflict
- ambiguous duplicate evidence
- missing evidence
- non-promotional VERIFIED boundary
- no heavy parser / external-call imports

QA result:

```text
PASS: coverage matches task requirements.
```

## Validation outputs

Required commands run:

```text
python -m py_compile tests/agent/mineru_artifact_adapter_348n.py tests/agent/test_mineru_artifact_adapter_348n.py
  PASS

python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

pytest tests/agent/test_mineru_artifact_adapter_348n.py -q
  21 passed in 0.15s

pytest tests/agent -q
  201 passed in 1.82s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git diff --stat
  no output before report creation

git diff --name-only
  no output before report creation

git diff --check
  PASS
```

## Decision

```text
Decision = 348N_R7AM_QA_CONFIRMED_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_VALID
```

R7AM is confirmed valid for a test-only MinerU `content_list_v2` artifact adapter prototype. It stays within test scope, uses a small curated fixture, preserves conservative matching behavior, does not commit real outputs, does not modify production code, and keeps evidence/clean/readiness boundaries closed.

## Recommended next task

```text
348N-R7AN test-only MinerU adapter controlled comparison dry-run design
```

Rationale:

```text
After QA confirms the adapter prototype, the next safe slice should design how to reuse this test-only adapter against a controlled comparison path without production wiring or readiness changes.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AM_QA_CONFIRMED_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_VALID
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent/test_mineru_artifact_adapter_348n.py -q => 21 passed; pytest tests/agent -q => 201 passed
files_modified（修改文件数）= 1，only docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md
error_count（错误数）= 0
fixture_review_result（fixture审查结果）= PASS，小型 curated fixture，2599 bytes，7 blocks，not full MinerU dump
adapter_review_result（adapter审查结果）= PASS，adapter only under tests/agent/; no production hook; deterministic metadata
matching_helper_review_result（匹配助手审查结果）= PASS，positive/negative/ambiguous/disagreed/missing evidence behavior conservative
boundary_check（边界检查）= PASS，no datefac_agent changes; no dependencies; no output commits; no MinerU/OCR/LLM/VLM; VERIFIED non-promotional
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AN test-only MinerU adapter controlled comparison dry-run design
```
