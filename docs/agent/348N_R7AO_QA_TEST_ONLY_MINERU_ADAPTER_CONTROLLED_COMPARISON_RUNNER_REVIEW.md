# 348N-R7AO-QA test-only MinerU adapter controlled comparison runner review

## Task ID

```text
348N-R7AO-QA test-only MinerU adapter controlled comparison runner review
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = QA-review-only
reason = R7AO completed a local no-commit controlled comparison runner. R7AO-QA reviews local outputs, count sanity, probe coverage, boundary safety, and tracked-file cleanliness before recommending the next R7AP slice.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating ab8175f..07ecb4c
  Fast-forward
  created docs/codex_tasks/348N_R7AO_QA_test_only_mineru_adapter_controlled_comparison_runner_review.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git branch --show-current:
  pivot/348-agent-foundation

git log --oneline -12:
  07ecb4c docs: update handoff after R7AO
  ccc30bd docs: refresh plain-language progress after R7AO
  c1065f5 docs: sync progress after R7AO
  78ddbd6 docs: add R7AO QA review task
  ab8175f docs: update handoff after R7AN
  7ac4823 docs: refresh plain-language progress after R7AN
  d00a921 docs: sync progress after R7AN
  505097d docs: add R7AO controlled comparison runner task
  f29cc07 docs: add R7AN controlled comparison design
  6fe7573 docs: update handoff after R7AM QA
  ac57cb9 docs: refresh plain-language progress after R7AM QA
  311a820 docs: sync progress after R7AM QA
```

Tracked worktree was clean after pull and before creating this QA report.

## Files reviewed

Required context read:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AO_QA_test_only_mineru_adapter_controlled_comparison_runner_review.md`
- `docs/codex_tasks/348N_R7AO_test_only_mineru_adapter_controlled_comparison_runner.md`
- `docs/agent/348N_R7AN_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_DRY_RUN_DESIGN.md`
- `docs/agent/348N_R7AM_QA_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AM_TEST_ONLY_MINERU_ARTIFACT_ADAPTER_PROTOTYPE_REPORT.md`

R7AM adapter context reviewed read-only:

- `tests/agent/mineru_artifact_adapter_348n.py`
- `tests/agent/test_mineru_artifact_adapter_348n.py`

No production code or tests were modified.

## Local outputs reviewed

Reviewed output directory:

```text
D:\_datefac_agent\output\comparison\anjing_foods_mineru_adapter_r7ao\
```

Expected local outputs all existed:

| File | Status | Size bytes |
| --- | --- | ---: |
| `run_r7ao_mineru_adapter_comparison.py` | PASS | 39668 |
| `r7ao_mineru_adapter_comparison_report.xlsx` | PASS | 129829 |
| `r7ao_mineru_adapter_comparison_summary.md` | PASS | 8620 |
| `r7ao_mineru_adapter_run_metadata.json` | PASS | 3209 |
| `r7ao_mineru_adapter_evidence_rows.csv` | PASS | 2616 |
| `r7ao_mineru_adapter_unmatched_rows.csv` | PASS | 22455 |

CSV output review:

```text
r7ao_mineru_adapter_evidence_rows.csv rows = 9
r7ao_mineru_adapter_unmatched_rows.csv rows = 49
```

No WARN for missing CSV files was needed.

## Runner review

Runner reviewed:

```text
output/comparison/anjing_foods_mineru_adapter_r7ao/run_r7ao_mineru_adapter_comparison.py
```

QA result:

```text
PASS: runner is local-only under the approved output directory.
PASS: runner imports and reuses tests.agent.mineru_artifact_adapter_348n.
PASS: runner does not import datefac_agent production pipeline modules.
PASS: runner does not add CLI, runner, or production hook wiring.
PASS: runner uses subprocess only for read-only git branch/head metadata.
PASS: runner does not run MinerU, OCR, LLM, VLM, or real PDF extraction.
PASS: runner does not contain git add, git commit, or git push operations.
```

Import review:

```text
imports = __future__, collections, dataclasses, datetime, decimal, pathlib, hashlib, json, math, re, subprocess, sys, typing, pandas, tests.agent
datefac_agent import = absent
adapter import = from tests.agent import mineru_artifact_adapter_348n
```

The strings `ocr` and `vlm` appear only in zero-count boundary flags and boundary statement text, not as calls.

## Input resolution review

Required DateFac Excel:

```text
D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx
```

Resolved MinerU `content_list_v2`:

```text
E:\mineru331\smoke_output\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json
```

QA result:

```text
PASS: DateFac Excel was resolved exactly.
PASS: one content_list_v2 was selected from the user-specified exact auto root.
PASS: other search-root candidates were recorded as non-selected candidates in metadata.
PASS: source_document_id remained H3_AP202606081823352906_1.pdf.
```

Resolution note:

```text
metadata.mineru_resolution_strategy =
  resolved_unique_match_in_user_specified_exact_auto_root; other search-root candidates recorded as non-selected
```

This is acceptable because the task explicitly listed the exact `auto` root first and required no guessing when multiple candidates were ambiguous. The runner selected the unique candidate inside that exact root and preserved the other broader-root matches for traceability.

## Metadata review

Reviewed:

```text
output/comparison/anjing_foods_mineru_adapter_r7ao/r7ao_mineru_adapter_run_metadata.json
```

Metadata contains:

```text
task_id = 348N-R7AO test-only MinerU adapter controlled comparison runner
branch = pivot/348-agent-foundation
commit_head = ab8175f879315f35b5625a895bf38be4903df287
input_paths = DateFac Excel + MinerU search roots
resolved_mineru_content_list_v2_path = exact auto-root v2 JSON
adapter_module = tests.agent.mineru_artifact_adapter_348n
candidate_sheet = Balance_Sheet
row_count = 451
block_count = 89
status_counts = VERIFIED 402 / UNVERIFIED 15 / DISAGREED 5 / AMBIGUOUS 10 / MISSING_EVIDENCE 1 / PARSE_SKIPPED 18
probe_examples_result = VERIFIED:11
readiness_gates = CLOSED
boundary_flags = all production/external-call/promotion flags false or zero
```

QA result:

```text
PASS: metadata records required input paths, branch/head, row counts, block counts, status counts, readiness gates, and boundary flags.
PASS: metadata includes selected path plus all discovered content_list_v2 candidates.
PASS: metadata records output paths for xlsx, markdown summary, evidence CSV, unmatched CSV, and metadata JSON.
```

## Report/output review

Excel report reviewed:

```text
output/comparison/anjing_foods_mineru_adapter_r7ao/r7ao_mineru_adapter_comparison_report.xlsx
```

Required sheets present:

```text
input_summary
sheet_detection
candidate_rows_normalized
mineru_adapter_blocks_index
comparison_results
source_text_evidence_draft
unmatched_or_review_required
probe_examples
run_metadata
```

Markdown summary reviewed:

```text
output/comparison/anjing_foods_mineru_adapter_r7ao/r7ao_mineru_adapter_comparison_summary.md
```

QA result:

```text
PASS: xlsx/md/json outputs are complete.
PASS: summary includes input paths, adapter import result, sheet detection, block count, row count, status counts, probe results, examples, R7AL difference note, boundary statement, recommended next task, and Data Result.
PASS: evidence CSV is metadata-only: source_text_id, source_document_id, page_number, locator, text_kind, source_text_sha256, char_count, trusted_source, extraction_method, serialization_policy, used_by_comparison_rows.
PASS: comparison output carries compact source_text status/id/hash/page/locator fields, not full matched source_text.
PASS: block index includes only a bounded `text_preview_160`, not uncontrolled full source_text dumping.
WARN: the R7AO/R7AL difference explanation is high-level rather than a row-level delta analysis; this is acceptable for R7AO-QA but should drive the next discrepancy workflow design.
```

Full source_text serialization check:

```text
source_text_evidence_draft text column = absent
evidence CSV text column = absent
comparison_results full matched text column = absent
mineru_adapter_blocks_index text_preview_160 = bounded preview only
```

## Status count sanity check

Required counts:

```text
total_rows = 451
verified_count = 402
review_required_count = 49
disagreed_count = 5
ambiguous_count = 10
missing_evidence_count = 1
parse_skipped_count = 18
probe_examples_result = VERIFIED:11
```

Observed from metadata and xlsx:

```text
row_count = 451
block_count = 89
VERIFIED = 402
UNVERIFIED = 15
DISAGREED = 5
AMBIGUOUS = 10
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 18
probe_examples_result = VERIFIED:11
```

Internal consistency:

```text
status_count_sum = 402 + 15 + 5 + 10 + 1 + 18 = 451
review_required_count = total_rows - verified_count = 451 - 402 = 49
non_verified_sum = UNVERIFIED 15 + DISAGREED 5 + AMBIGUOUS 10 + MISSING_EVIDENCE 1 + PARSE_SKIPPED 18 = 49
unmatched_or_review_required sheet rows = 49
```

QA result:

```text
PASS: status counts are internally consistent.
PASS: review_required_count is an aggregate of all non-VERIFIED statuses.
PASS: DISAGREED / AMBIGUOUS / MISSING_EVIDENCE / PARSE_SKIPPED are represented explicitly.
```

## Probe examples review

Required 11 probes:

```text
2026Q1 营业收入 = 47.10 亿元
2026Q1 归母净利润 = 5.63 亿元
2026Q1 扣非归母净利润 = 5.25 亿元
2026Q1 毛利率 = 24.99%
2026Q1 净利率 = 12.05%
2026E EPS = 5.37 元
2026E PE = 18.3 倍
2026E 营业收入 = 18,379 百万元
2026E 净利润 = 1,791 百万元
2026E ROE = 10.3%
2026E P/B = 1.9 倍
```

Observed:

```text
probe_examples rows = 11
probe_status counts = VERIFIED:11
```

QA result:

```text
PASS: all 11 required probe examples are reported.
PASS: all 11 required probe examples are VERIFIED.
PASS: no probe was injected as a synthetic candidate row; probes were matched against normalized DateFac rows.
```

## R7AO vs R7AL review

Known R7AL baseline:

```text
DateFac rows = 451
MinerU blocks = 173
VERIFIED = 395
review_required = 56
DISAGREED = 10
AMBIGUOUS = 10
MISSING_EVIDENCE = 2
required probes = VERIFIED:11
```

R7AO observed:

```text
DateFac rows = 451
MinerU adapter blocks = 89
VERIFIED = 402
review_required = 49
DISAGREED = 5
AMBIGUOUS = 10
MISSING_EVIDENCE = 1
PARSE_SKIPPED = 18
required probes = VERIFIED:11
```

QA interpretation:

```text
PASS with limitation: R7AO count changes are plausible because R7AO uses the QA-reviewed R7AM adapter shape and primary content_list_v2 block indexing, while R7AL was a one-off local comparison with broader block handling. R7AO summary records this high-level difference.
LIMITATION: R7AO-QA did not perform row-level reconciliation between the R7AL and R7AO result sets.
NEXT-SLICE DRIVER: the safest R7AP path is a discrepancy review workflow design before production-boundary integration.
```

## Boundary review

QA result:

```text
PASS: tracked files were clean before this QA report.
PASS: local outputs stayed under output/comparison/anjing_foods_mineru_adapter_r7ao/.
PASS: local outputs were not staged, committed, or pushed.
PASS: no datefac_agent/ production files were modified.
PASS: no tests/ files were modified.
PASS: no docs/ files were modified except this QA report.
PASS: no dependency/config files were modified.
PASS: no DateFac Excel was committed.
PASS: no MinerU artifact was committed.
PASS: no local runner/report was committed in R7AO.
PASS: no MinerU rerun.
PASS: no OCR / LLM / VLM calls.
PASS: no real PDF extraction.
PASS: no production pipeline hook.
PASS: VERIFIED remains local comparison status only.
PASS: no STRONG_EVIDENCE promotion.
PASS: no clean_data admission change.
PASS: readiness_gates remain CLOSED.
```

Readiness gates:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
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
  201 passed in 0.87s

python output/comparison/anjing_foods_mineru_adapter_r7ao/run_r7ao_mineru_adapter_comparison.py
  PASS
  Decision = PASS，348N_R7AO_LOCAL_CONTROLLED_COMPARISON_COMPLETED
  datefac_rows_count = 451
  mineru_adapter_blocks_count = 89
  verified_count = 402
  review_required_count = 49
  disagreed_count = 5
  ambiguous_count = 10
  missing_evidence_count = 1
  parse_skipped_count = 18
  probe_examples_result = VERIFIED:11

git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git diff --stat
  no output before QA report creation

git diff --name-only
  no output before QA report creation

git diff --check
  PASS
```

## Limitations

- R7AO remains a local no-commit dry-run, not production integration.
- The local runner lives under `output/comparison/` and is intentionally not committed.
- The R7AM adapter still lives under `tests/agent/`; this is acceptable only for controlled comparison and not a production hook.
- R7AO reviewed one document pair only: Anjing DateFac Excel + Anjing MinerU content_list_v2.
- R7AO/R7AL differences are explained at workflow level but not row-by-row.
- `text_preview_160` is bounded and acceptable for QA, but production evidence indexes/review queues should continue metadata-only serialization.
- `VERIFIED` remains non-promotional and must not be interpreted as `STRONG_EVIDENCE`, clean admission, client readiness, or production readiness.

## Decision

```text
Decision = 348N_R7AO_QA_CONFIRMED_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_VALID
```

R7AO-QA confirms the local controlled comparison runner and outputs are credible for the test-only dry-run boundary. Counts are internally consistent, all 11 required probes are VERIFIED, local outputs are complete and kept outside tracked source, and readiness/evidence/clean boundaries remain closed.

## Recommended next task

```text
348N-R7AP DateFac-MinerU discrepancy review workflow design
```

Rationale:

```text
R7AO passed, but R7AO differs from R7AL in verified/review-required counts and block indexing. Before production-boundary integration, the safest next slice is to design a discrepancy review workflow for non-VERIFIED rows and R7AL/R7AO deltas.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AO_QA_CONFIRMED_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_VALID
build_result（构建结果）= PASS，py_compile validation passed and local runner regenerated reports
test_result（测试结果）= PASS，pytest tests/agent/test_mineru_artifact_adapter_348n.py -q => 21 passed; pytest tests/agent -q => 201 passed
files_modified（修改文件数）= 1，only docs/agent/348N_R7AO_QA_TEST_ONLY_MINERU_ADAPTER_CONTROLLED_COMPARISON_RUNNER_REVIEW.md
error_count（错误数）= 0
runner_review_result（runner审查结果）= PASS，runner is local-only, reuses tests.agent.mineru_artifact_adapter_348n, no production hook or external calls
metadata_review_result（metadata审查结果）= PASS，metadata records inputs, branch/head, row/block/status counts, probes, readiness gates, and boundary flags
comparison_output_review_result（对比输出审查结果）= PASS，xlsx/md/json/csv outputs complete; evidence CSV metadata-only; no uncontrolled full source_text dump
count_sanity_result（计数一致性结果）= PASS，451 total = 402 VERIFIED + 49 non-VERIFIED; non-VERIFIED = 15 UNVERIFIED + 5 DISAGREED + 10 AMBIGUOUS + 1 MISSING_EVIDENCE + 18 PARSE_SKIPPED
probe_examples_review_result（探针样例审查结果）= PASS，11/11 probes reported and VERIFIED
boundary_check（边界检查）= PASS，no datefac_agent/tests/dependency changes; output files not staged/committed; no MinerU/OCR/LLM/VLM; VERIFIED non-promotional
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AP DateFac-MinerU discrepancy review workflow design
```
