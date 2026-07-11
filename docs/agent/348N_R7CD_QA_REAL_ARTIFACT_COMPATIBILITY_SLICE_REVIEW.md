# 348N-R7CD-QA real artifact compatibility slice review

## Task ID

```text
348N-R7CD-QA real artifact compatibility slice review
```

Task type: QA-only.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: fast-forward 7973df3..d5e5466; R7CD-QA task doc added.

git status -sb
PASS: clean after pull.

git log --oneline -145
PASS: latest history includes d5e5466 R7CD-QA task and 7973df3 R7CD implementation.
```

## Files reviewed

Reviewed task and reports:

- `docs/codex_tasks/348N_R7CD_QA_real_artifact_compatibility_slice_review.md`
- `docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md`
- `docs/agent/348N_R7CC_QA_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_REVIEW.md`
- `docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md`

Reviewed implementation, CLI, tests, and fixture:

- `datefac_agent/reconciliation/real_artifact_compatibility_348n.py`
- `tools/run_real_artifact_reconciliation_348n.py`
- `tests/agent/test_real_artifact_compatibility_348n.py`
- `tests/agent/fixtures/mineru_original_reconciliation/real_content_list_v2_table_sample.json`

Reviewed supporting context:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`

## R7CD recap

R7CD added a demo-only compatibility slice that reads real-style MinerU `content_list_v2` table blocks and the existing Anjing Foods DateFac workbook into a shared reconciliation record model. It compares rows on `statement_context + metric_key + period`, preserves `A/E/F` period suffixes, normalizes unit metadata, and emits compact review_queue-style candidates for review-required rows only.

## Allowed file boundary review

PASS. R7CD changed exactly the five allowed files:

- `datefac_agent/reconciliation/real_artifact_compatibility_348n.py`
- `tools/run_real_artifact_reconciliation_348n.py`
- `tests/agent/test_real_artifact_compatibility_348n.py`
- `tests/agent/fixtures/mineru_original_reconciliation/real_content_list_v2_table_sample.json`
- `docs/agent/348N_R7CD_REAL_MINERU_ARTIFACT_COMPATIBILITY_SLICE_DEMO_ONLY_REPORT.md`

No complete real MinerU JSON, PDF, Markdown, Excel workbook, or local output artifact was committed. The committed fixture is a curated 1,954-byte table sample, not the full real artifact.

## Real MinerU parsing review

PASS. The parser accepts page-grouped lists, filters table blocks, reads `content.html`, carries `table_caption`, `table_footnote`, `bbox`, `page_number`, `page_idx`, and `block_index`, and emits deterministic source locators such as `page:3:block:3:row:15:col:3`.

The real smoke parsed `415` MinerU records from `H3_AP202606081823352906_1_content_list_v2.json`.

## Real workbook parsing review

PASS. Workbook loading uses `openpyxl.load_workbook(..., read_only=True, data_only=True)` and closes the workbook in `finally`. The implementation reads only the five approved sheets:

- `Financial_Data_Valuation`
- `Balance_Sheet`
- `Income_Statement`
- `Cash_Flow`
- `Ratios_Per_Share`

`Key_Info`, `Q1_Event_and_Text`, and `Source_Notes` are not included in this slice. The real smoke parsed `415` workbook records from `datefac_raw_material_anjing_foods.xlsx`.

## HTML table expansion review

PASS. HTML table expansion uses the standard-library `html.parser`, supports `td`/`th`, `tr`, `br`, and simple `colspan`, and preserves normal rows. Tests cover matrix expansion, page-grouped table shape, caption/bbox/page source trace, and deterministic output.

## Period/context/unit review

PASS. Periods preserve suffixes such as `2024A`, `2025A`, and `2026E` instead of collapsing to bare years. Statement context is derived from table captions or Excel sheet identity and participates in comparison identity. Metric labels strip embedded unit suffixes while preserving normalized unit metadata.

PASS with conservative caveat. Unit-incompatible comparisons route to `UNIT_REVIEW`, and `UNIT_REVIEW` is review-required. The implementation does not silently treat incompatible units as matches.

## Comparison identity and status review

PASS. Comparison identity is `statement_context + metric_key + period`, which prevents duplicate labels such as `营业收入` from colliding across financial data, income statement, cash flow, and ratios contexts.

Statuses are deterministic and include:

- `MATCH`
- `CONFLICT`
- `MINERU_ONLY`
- `ORIGINAL_ONLY`
- `UNPARSEABLE`
- `UNIT_REVIEW`

The real smoke count is internally consistent:

```text
416 comparison rows = 414 MATCH + 1 ORIGINAL_ONLY + 1 UNPARSEABLE
```

## Review candidate safety review

PASS. Review candidates are generated only for review-required rows and contain bounded evidence previews, source trace, deterministic IDs, `clean_data_eligible = false`, and closed readiness gates.

PASS. Review candidates do not include full raw MinerU artifacts, full workbook contents, full source_text, clean_data payloads, delivery/export payloads, or DB persistence payloads.

## CLI smoke behavior review

PASS. The CLI requires explicit `--mineru-json` and `--original-xlsx` input paths, calls the compatibility slice, prints compact summary counts only, and does not create output files.

The real smoke was reproduced against:

- `H3_AP202606081823352906_1_content_list_v2.json`
- `datefac_raw_material_anjing_foods.xlsx`

## Real smoke count reconciliation

PASS. Reproduced count output:

```text
mineru_record_count=415
original_record_count=415
comparison_row_count=416
match_count=414
conflict_count=0
mineru_only_count=0
original_only_count=1
unparseable_count=1
unit_review_count=0
review_required_count=2
```

The `416` comparison rows are explainable despite `415` MinerU records and `415` workbook records because one logical discrepancy appears as one unparseable MinerU-side record plus one workbook-only corrected record.

## 总资产周转率 discrepancy cluster review

PASS. The two review-required rows both belong to the same `ratios_per_share / total_asset_turnover / 2026E` cluster:

- `ORIGINAL_ONLY`: workbook row `Ratios_Per_Share` row 14, col 4 preserves corrected value `0.8` with note `次；P3原文“0.08.8”按表格语境修正为0.8`.
- `UNPARSEABLE`: MinerU row points to page 3, block 3, row 15, col 3 with locator `page:3:block:3:row:15:col:3`, but the extracted cell cannot be normalized as a trusted numeric value.

PASS. This is not two unrelated hidden failures; it is a single discrepancy cluster that stays review-required. The corrected workbook-side value is preserved in trace/evidence preview only and is not written to clean_data.

## Compatibility review

PASS. R7CC tests remain green, and the full agent test baseline is `813 passed`. R7CD did not regress the earlier hand-written fixture vertical slice.

## Boundary review

PASS. R7CD did not add DB/repository/schema/migration/storage code, production hooks, clean_data writes, delivery/export integration, output files, dependency changes, MinerU execution, OCR, LLM, or VLM calls.

Readiness remains:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Validation outputs

```text
python -m py_compile datefac_agent/reconciliation/real_artifact_compatibility_348n.py
PASS

python -m py_compile tools/run_real_artifact_reconciliation_348n.py
PASS

python -m py_compile tests/agent/test_real_artifact_compatibility_348n.py
PASS

python -m pytest tests/agent/test_real_artifact_compatibility_348n.py -q
PASS: 10 passed in 0.57s

python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
PASS: 11 passed in 0.09s

python -m pytest tests/agent -q
PASS: 813 passed in 2.63s

python tools/run_real_artifact_reconciliation_348n.py --mineru-json E:\\mineru_lab\\output_new\\H3_AP202606081823352906_1\\auto\\H3_AP202606081823352906_1_content_list_v2.json --original-xlsx D:\\_datefac_agent\\output\\datefac_raw_material_anjing_foods.xlsx
PASS: compact count output reproduced

git status -sb
PASS before report creation: clean

git diff --stat
PASS before report creation: no tracked diff

git diff --name-only
PASS before report creation: no tracked diff

git diff --check
PASS: no whitespace errors
```

## Limitations

- This is still demo-only compatibility, not production reconciliation.
- It does not write discrepancy reports, review outputs, clean_data, delivery files, DB rows, or manifests.
- It does not solve human review UI or production workflow admission.
- The `总资产周转率` discrepancy remains review-required and should be diagnosed in the next slice rather than silently repaired.

## Decision

PASS. R7CD is a valid real-artifact compatibility slice: it reads the real MinerU JSON and DateFac workbook, preserves period/context/unit identity, produces reproducible counts, keeps the two review-required rows explainable, and stays inside demo-only boundaries.

## Recommended next task

```text
348N-R7CE real discrepancy diagnosis and review report demo-only
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS
build_result（构建结果）= PASS
test_result（测试结果）= PASS; R7CD targeted tests 10 passed, R7CC tests 11 passed, full tests/agent 813 passed
files_modified（修改文件数）= 1
error_count（错误数）= 0
real_mineru_compatibility_review_result（真实MinerU兼容审查结果）= PASS; real page-grouped content_list_v2 tables parsed with page/block/bbox trace
real_xlsx_compatibility_review_result（真实xlsx兼容审查结果）= PASS; five approved workbook sheets parsed read-only/data-only and closed reliably
html_table_expansion_review_result（HTML表格展开审查结果）= PASS; deterministic stdlib table expansion covered by tests
period_context_unit_review_result（期间上下文单位审查结果）= PASS; A/E/F periods preserved, statement context participates in identity, unit mismatches route to UNIT_REVIEW
comparison_identity_review_result（对比身份审查结果）= PASS; real smoke count reconciles as 416 = 414 MATCH + 1 ORIGINAL_ONLY + 1 UNPARSEABLE
review_candidate_safety_review_result（复核候选安全审查结果）= PASS; bounded evidence/source trace only, no full raw artifact/source_text, no clean_data
real_smoke_reproducibility_result（真实smoke复现结果）= PASS; real local smoke reproduced counts only
discrepancy_cluster_review_result（差异簇审查结果）= PASS; both review-required rows belong to 总资产周转率 2026E cluster
boundary_check（边界检查）= PASS; QA report only, no production hook, no DB, no output commit, no MinerU/OCR/LLM/VLM run
readiness_gates（就绪门）= CLOSED
recommended_next_task（推荐下一任务）= 348N-R7CE real discrepancy diagnosis and review report demo-only
```
