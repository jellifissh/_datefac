# 348N-R7AN test-only MinerU adapter controlled comparison dry-run design

## Task ID

```text
348N-R7AN test-only MinerU adapter controlled comparison dry-run design
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = design-review-only
reason = R7AM-QA confirmed the test-only MinerU artifact adapter prototype is valid. R7AN designs the next controlled comparison dry-run without implementing a runner, changing tests, touching production code, committing local outputs, or opening readiness gates.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 4daa3bf..6fe7573
  Fast-forward
  created docs/codex_tasks/348N_R7AN_test_only_mineru_adapter_controlled_comparison_dry_run_design.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  6fe7573 docs: update handoff after R7AM QA
  ac57cb9 docs: refresh plain-language progress after R7AM QA
  311a820 docs: sync progress after R7AM QA
  62130bb docs: add R7AN controlled comparison design task
  4daa3bf docs: add R7AM QA review
  c940c47 docs: update handoff after R7AM
  6eebce2 docs: refresh plain-language progress after R7AM
  ab965f8 docs: sync progress after R7AM
  ef99a69 docs: add R7AM QA review task
  0de3a4a test: add MinerU artifact adapter prototype
  df5b39d docs: update handoff after R7AL comparison
  699b63c docs: refresh plain-language progress after R7AL comparison
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
- `docs/codex_tasks/348N_R7AN_test_only_mineru_adapter_controlled_comparison_dry_run_design.md`
- `docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md`

Implementation context reviewed read-only:

- `tests/agent/mineru_artifact_adapter_348n.py`
- `tests/agent/test_mineru_artifact_adapter_348n.py`

No production files were modified.

## R7AL/R7AM/R7AM-QA evidence recap

R7AL local dry-run proved the real Anjing comparison shape:

```text
DateFac candidate rows normalized = 451
MinerU blocks indexed = 173
VERIFIED = 395
review_required_total = 56
DISAGREED = 10
AMBIGUOUS = 10
MISSING_EVIDENCE = 2
required 11 probe examples = all found and VERIFIED against MinerU v2 blocks
primary input = content_list_v2
content_list = fallback / cross-check
readiness_gates = CLOSED
commit = none
```

R7AM converted the useful shape into a test-only adapter:

```text
tests/agent/mineru_artifact_adapter_348n.py
tests/agent/test_mineru_artifact_adapter_348n.py
tests/agent/fixtures/mineru_artifacts/anjing_minimal_content_list_v2__r7am.json
```

R7AM-QA confirmed:

```text
fixture = small curated, 2599 bytes / 7 blocks
adapter = tests/agent/ only, no production hook
matching helper = conservative VERIFIED / UNVERIFIED / DISAGREED / AMBIGUOUS / MISSING_EVIDENCE
no datefac_agent/ changes
no output commits
no dependencies
no MinerU/OCR/LLM/VLM
readiness_gates = CLOSED
```

## Design decision matrix

| Decision | R7AN design choice | Rationale |
| --- | --- | --- |
| `input_scope` | Full Anjing DateFac Excel + full local MinerU `auto/` output for the next dry-run; optional small row limit for smoke mode. | R7AL already ran the full pair once; R7AO should make it repeatable while retaining an emergency small-scope mode. |
| `local_output_policy` | Write outputs only under `output/comparison/anjing_foods_mineru_adapter_r7ao/`; do not commit outputs. | Comparison artifacts are evidence/debug outputs, not source files. |
| `committed_fixture_policy` | No new fixture in R7AN/R7AO unless a later fixture-harvest task is explicitly created. | R7AM fixture already covers adapter behavior; full MinerU/DateFac outputs must remain local. |
| `runner_location` | `output/comparison/anjing_foods_mineru_adapter_r7ao/run_r7ao_mineru_adapter_comparison.py` for the next dry-run script. | Keeps one-off controlled runner outside production and outside tests, while allowing reproducible local execution. |
| `whether to reuse R7AM adapter directly` | Yes, reuse `tests.agent.mineru_artifact_adapter_348n` directly for block indexing and matching semantics in R7AO. | Avoids duplicating evidence-block parsing logic and preserves QA-reviewed behavior. |
| `candidate_row_normalization_strategy` | Reuse R7AL normalization concepts, but keep them local to R7AO runner; no production schema changes. | DateFac Excel schema is workbook-specific and not ready for production intake changes. |
| `evidence_block_indexing_strategy` | Primary `content_list_v2`, page-grouped; optional `content_list` fallback only as review metadata, not as trusted primary match. | R7AL/R7AM showed v2 has the better page/block/table shape. |
| `matching_status_semantics` | Preserve R7AM statuses plus R7AL reporting columns. | Keeps conservative semantics and audit explainability. |
| `report_sheet_design` | XLSX + Markdown + CSV local reports, not committed. | Matches R7AL operator expectations while avoiding repo pollution. |
| `validation_commands` | Run adapter py_compile, production boundary py_compile, adapter test, full `tests/agent`. | Confirms R7AO did not regress adapter or current agent tests. |
| `pass_fail_blocked_criteria` | PASS/BLOCKED/FAIL defined below. | Prevents over-claiming if inputs are missing or evidence quality drops. |
| `next_task_name` | `348N-R7AO test-only MinerU adapter controlled comparison runner`. | Next safe slice is implementation of the local dry-run runner. |

## Input scope

Recommended next dry-run input scope:

```text
required DateFac Excel:
  D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx

required MinerU v2 JSON:
  E:\mineru331\smoke_output\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json

required source_document_id:
  H3_AP202606081823352906_1.pdf
```

Optional inputs:

```text
MinerU content_list JSON:
  E:\mineru331\smoke_output\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list.json

MinerU Markdown preview:
  E:\mineru331\smoke_output\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1.md
```

Forbidden inputs:

```text
raw PDF parsing input
new MinerU run output generated during the task
OCR output generated during the task
LLM/VLM generated evidence
production clean_data as an input authority
```

Row scope decision:

```text
Default = compare all normalized DateFac candidate rows, expected around 451 rows for Anjing.
Optional smoke mode = limit to the 11 R7AL required probe examples plus a small review sample.
R7AO should run full mode by default if all required inputs exist.
```

## Runner scope

R7AN does not implement the runner.

Recommended R7AO runner placement:

```text
output/comparison/anjing_foods_mineru_adapter_r7ao/run_r7ao_mineru_adapter_comparison.py
```

Why not `datefac_agent/`:

```text
This is not production integration.
DateFac workbook normalization and full local MinerU artifact handling are still controlled dry-run logic.
```

Why not `tests/agent/`:

```text
The runner will read full local output paths and produce xlsx/csv/md comparison reports.
That is operator dry-run behavior, not unit-test behavior.
```

Why not docs-only procedure for R7AO:

```text
R7AN is the docs-only procedure design.
The next useful slice is a local script that can reproduce R7AL with R7AM adapter semantics.
```

## Candidate row normalization design

R7AO should normalize DateFac Excel rows into a local dry-run row model:

```text
row_id
row_kind
sheet_name
excel_row_number
metric_name
period
value
value_numeric_normalized
numeric_token_count
unit
source_page
page_number
raw_text_preview
source_document_id
normalization_notes
```

Required candidate fields for a match attempt:

```text
metric_name
period
value
source_document_id
```

Strongly preferred:

```text
page_number / source_page
unit
raw_text_preview
sheet_name + row index
```

Rows missing required fields:

```text
missing metric_name -> PARSE_SKIPPED / UNSUPPORTED_ROW
missing period -> MISSING_EVIDENCE / normalization_required
missing value or compound unsupported value -> PARSE_SKIPPED
missing source_document_id -> BLOCKED row-level risk, no trusted source_text
```

Rows missing page number:

```text
Run capped all-page candidate search.
Mark match_reason = no_page_candidate_search.
Allow VERIFIED only when a unique block satisfies value + metric + period.
If multiple blocks match, AMBIGUOUS.
If cap is exceeded, MISSING_EVIDENCE / REVIEW_REQUIRED.
```

Candidate normalization should remain in the local R7AO script, not in `datefac_agent/`, until QA confirms multiple workbook shapes.

## MinerU adapter usage design

R7AO should directly reuse:

```text
tests.agent.mineru_artifact_adapter_348n.extract_mineru_evidence_blocks(...)
tests.agent.mineru_artifact_adapter_348n.find_mineru_evidence_for_candidate(...)
```

Required adapter behavior:

```text
content_list_v2 page-grouped JSON -> MinerUEvidenceBlock list
page_number = page_idx + 1
locator = mineru:v2:page:{page_number}:block:{block_index}:bbox:{x1},{y1},{x2},{y2}
text_sha256 = sha256(text UTF-8)
char_count = len(text)
paragraph/title/table evidence supported
table uses content.html
```

R7AO should not copy/paste the adapter into the runner. The runner should import the test-only adapter with an explicit banner:

```text
TEST_ONLY_R7AO_RUNNER = true
production_ready = false
formal_client_export_allowed = false
```

If importing from `tests.agent` is considered too awkward in R7AO, the task should stop and recommend a design for a non-production helper module. It should not silently move code into `datefac_agent/`.

## Evidence matching design

Primary evidence ranking:

```text
1. content_list_v2 table HTML block on explicit page
2. content_list_v2 paragraph/title block on explicit page
3. content_list_v2 table HTML block from capped no-page search
4. content_list_v2 paragraph/title block from capped no-page search
5. content_list/content_list.md preview only as fallback metadata, not trusted primary evidence
```

Matching semantics:

```text
VERIFIED:
  value + metric + period in one evidence block, or table metric row + period column + value cell match.

UNVERIFIED:
  only partial anchor match exists, such as value-only, metric-only, period-only, or value + one missing anchor.

DISAGREED:
  metric + period are present but expected value is absent and conflicting numeric candidates exist.

AMBIGUOUS:
  multiple plausible evidence blocks satisfy value + metric + period and page/source context cannot disambiguate.

MISSING_EVIDENCE:
  no usable page/block/evidence text exists or required provenance is missing.

PARSE_SKIPPED:
  row cannot be normalized into a single metric/period/value candidate.
```

`VERIFIED` remains non-promotional:

```text
agreement_status = VERIFIED only
evidence_level remains unchanged / no STRONG_EVIDENCE promotion
no clean_data admission change
no readiness gate change
```

## Output report design

Local output directory:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\
```

Recommended output files:

```text
anjing_mineru_adapter_comparison_report.xlsx
anjing_mineru_adapter_comparison_summary.md
anjing_mineru_adapter_evidence_rows.csv
anjing_mineru_adapter_review_required_rows.csv
anjing_mineru_adapter_run_manifest.json
```

Commit policy:

```text
Do not commit any output files.
Do not commit DateFac Excel.
Do not commit full MinerU JSON/Markdown/images.
Do not commit comparison reports.
```

Recommended XLSX sheets:

```text
input_summary
datefac_sheets_summary
datefac_rows_normalized
mineru_evidence_blocks_index
comparison_results
source_text_evidence_draft
review_required_rows
manual_probe_examples
run_manifest
```

Required summary metrics:

```text
total_candidate_rows
normalized_candidate_rows
mineru_blocks_count
verified_count
unverified_count
disagreed_count
ambiguous_count
missing_evidence_count
parse_skipped_count
review_required_count
required_probe_found_count
required_probe_verified_count
external_call_counts = 0
readiness_gates = CLOSED
```

SourceTextEvidence draft output should include only bounded preview and metadata:

```text
source_text_id
source_document_id
page_number
locator
text_kind
text_sha256
char_count
trusted_source_candidate
extraction_method
text_snippet_preview
```

The full repeated source text should not be serialized into review_queue-like summaries.

## Difference from R7AL one-off script

R7AL was a local exploratory dry-run:

```text
read full DateFac Excel
read full local MinerU output
implemented ad hoc block indexing + matching
generated local xlsx/csv/md outputs
committed nothing
```

R7AO should differ by:

```text
reusing R7AM adapter for evidence block parsing and matching semantics
making input checks explicit and fail-closed
emitting a run manifest with gates and external-call counts
separating required inputs, optional fallbacks, and forbidden inputs
preserving clear PASS/BLOCKED/FAIL criteria
keeping all outputs local and ignored/uncommitted
```

R7AO should not become production integration.

## Pass / fail / blocked criteria

PASS when all are true:

```text
required DateFac Excel exists
required MinerU content_list_v2 exists
R7AM adapter imports and validates
candidate normalization completes
MinerU blocks index successfully
all 11 required probe examples are found in DateFac rows
all 11 required probe examples are VERIFIED or explicitly explained if missing from source input
output reports are written locally
external_call_counts = 0
readiness_gates = CLOSED
no production files modified
no output files committed
```

BLOCKED when any are true:

```text
required DateFac Excel missing
required MinerU content_list_v2 missing
adapter import fails
input JSON invalid or not page-grouped
DateFac candidate rows cannot be normalized enough to identify metric/period/value
source_document_id cannot be bound
worktree not clean before the run
```

FAIL / regression risk when any are true:

```text
runner touches datefac_agent/
runner modifies tests/ without explicit implementation task permission
runner commits output artifacts
runner runs MinerU/OCR/LLM/VLM/real PDF extraction
VERIFIED is promoted to STRONG_EVIDENCE
VERIFIED changes clean_data admission
readiness gates are opened
value-only matches are VERIFIED
ambiguous duplicate evidence is not marked AMBIGUOUS
DISAGREED is collapsed into UNVERIFIED without explanation
```

## Boundary review

R7AN stayed docs-only:

```text
datefac_agent/ modified = no
tests/ modified = no
runner implementation created = no
new fixture created = no
full MinerU output committed = no
DateFac Excel committed = no
comparison xlsx/csv/md output committed = no
MinerU run = no
OCR / LLM / VLM run = no
real PDF extraction = no
dependencies added = no
VERIFIED -> STRONG_EVIDENCE promotion = no
VERIFIED -> clean_data admission = no
readiness gates opened = no
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
  21 passed in 0.13s

pytest tests/agent -q
  201 passed in 0.89s

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git diff --stat
  no output before report creation

git diff --name-only
  no output before report creation

git diff --check
  PASS
```

## Limitations

- This report does not implement R7AO.
- This report does not validate current availability of the full Anjing local input files.
- This report does not create any new fixture or runner.
- R7AM adapter is still under `tests/agent/`; importing it from a local dry-run script is acceptable only for controlled test-only comparison.
- DateFac candidate normalization remains workbook-specific until more real workbooks are tested.
- `VERIFIED` remains a comparison agreement status, not `STRONG_EVIDENCE`, clean admission, client readiness, or production readiness.

## Decision

```text
Decision = 348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN_VALID
```

R7AN confirms the next safe step is a local, test-only controlled comparison runner that reuses the R7AM adapter, reads the full Anjing DateFac Excel plus full local MinerU `content_list_v2`, writes local-only reports, and keeps production/evidence/readiness boundaries closed.

## Recommended next task

```text
348N-R7AO test-only MinerU adapter controlled comparison runner
```

Recommended R7AO scope:

```text
implement local dry-run script under output/comparison/anjing_foods_mineru_adapter_r7ao/
reuse tests.agent.mineru_artifact_adapter_348n
read full Anjing DateFac Excel and full local MinerU content_list_v2
write local xlsx/csv/md/json reports
run validation and git status checks
do not commit output artifacts
do not modify datefac_agent/
do not open readiness gates
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN_VALID
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent/test_mineru_artifact_adapter_348n.py -q => 21 passed; pytest tests/agent -q => 201 passed
files_modified（修改文件数）= 1，only docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md
error_count（错误数）= 0
input_scope_decision（输入范围决策）= Full Anjing DateFac Excel + full local MinerU content_list_v2 for R7AO, optional small smoke mode only as fallback
runner_scope_decision（runner范围决策）= local test-only runner under output/comparison/anjing_foods_mineru_adapter_r7ao/, not datefac_agent/ and not tests/
adapter_usage_decision（adapter使用决策）= reuse R7AM tests.agent.mineru_artifact_adapter_348n directly for evidence block indexing and matching semantics
output_policy_decision（输出策略决策）= write xlsx/csv/md/json reports locally under output/comparison; do not commit outputs
boundary_check（边界检查）= PASS，docs-only; no production/tests/fixtures/output/dependency changes; no MinerU/OCR/LLM/VLM; VERIFIED non-promotional
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AO test-only MinerU adapter controlled comparison runner
```
