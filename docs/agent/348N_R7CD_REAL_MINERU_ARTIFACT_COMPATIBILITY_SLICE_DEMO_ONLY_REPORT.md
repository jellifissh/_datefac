# 348N-R7CD real MinerU artifact compatibility slice demo-only

## Task ID

```text
348N-R7CD real MinerU artifact compatibility slice demo-only
```

## Preflight

```text
git status -sb
PASS: clean before task work.

git pull origin pivot/348-agent-foundation
PASS: already up to date.

git status -sb
PASS: clean after pull.

python -c "import openpyxl; print(openpyxl.__version__)"
PASS: 3.1.5 available.
```

## Files reviewed

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7CD_real_mineru_artifact_compatibility_slice_demo_only.md`
- `docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md`
- `docs/agent/348N_R7CC_QA_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_REVIEW.md`
- `datefac_agent/reconciliation/mineru_original_reconciliation_348n.py`
- `tests/agent/test_mineru_original_reconciliation_348n.py`
- real local inputs:
  - `E:\mineru_lab\output_new\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json`
  - `D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx`

## Goal recap

Move the reconciliation slice from hand-written fixtures to the real Anjing Foods artifacts already used in the project, while staying demo-only and not touching clean_data, DB persistence, delivery/export, or readiness gates.

## Implementation summary

- Added a pure-Python real-artifact compatibility slice for page-grouped MinerU `content_list_v2` tables and read-only Excel sheets.
- Expanded real HTML tables with stdlib `html.parser`.
- Preserved annual periods such as `2024A`, `2025A`, `2026E`.
- Kept statement context separate so same metric/period pairs from different sheets do not collide.
- Normalized metric labels, units, numeric values, and bounded evidence previews.
- Produced `MATCH`, `CONFLICT`, `MINERU_ONLY`, `ORIGINAL_ONLY`, `UNPARSEABLE`, and `UNIT_REVIEW` rows.
- Added a compact CLI smoke script that prints counts only.

## Boundary review

PASS. This slice stays demo-only:

- no clean_data writes;
- no DB/repository/migration/storage code;
- no MinerU/OCR/LLM/VLM execution;
- no delivery/export output;
- no readiness gate changes;
- no broad staging.

Readiness remains:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Real local smoke

Real inputs used:

- `H3_AP202606081823352906_1_content_list_v2.json`
- `datefac_raw_material_anjing_foods.xlsx`

Smoke summary:

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

The only non-match cluster is the `总资产周转率` row, where the real artifact still leaves one side structurally unparseable and the workbook side preserves the corrected review value `0.8`.

## Validation outputs

```text
python -m py_compile datefac_agent/reconciliation/real_artifact_compatibility_348n.py
PASS

python -m py_compile tools/run_real_artifact_reconciliation_348n.py
PASS

python -m py_compile tests/agent/test_real_artifact_compatibility_348n.py
PASS

python -m pytest tests/agent/test_real_artifact_compatibility_348n.py -q
PASS: 10 passed

python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
PASS: 11 passed

python -m pytest tests/agent -q
PASS: 813 passed

python tools/run_real_artifact_reconciliation_348n.py --mineru-json E:\\mineru_lab\\output_new\\H3_AP202606081823352906_1\\auto\\H3_AP202606081823352906_1_content_list_v2.json --original-xlsx D:\\_datefac_agent\\output\\datefac_raw_material_anjing_foods.xlsx
PASS: compact counts printed only

git status -sb
PASS: only allowed new R7CD files are untracked before staging.

git diff --stat
PASS: no tracked diff outside the allowed new files.

git diff --name-only
PASS: no tracked diff outside the allowed new files.

git diff --check
PASS: no whitespace issues.
```

## Decision

PASS. The real-artifact compatibility slice is implemented and validated with the real local MinerU JSON and DateFac workbook, while preserving demo-only boundaries and bounded review output.

## Data Result / 数据结果

```text
Decision=PASS
build_result=PASS
test_result=PASS
files_modified=5
error_count=0
real_mineru_compatibility_result=PASS; parsed real page-grouped MinerU tables into 415 records
real_xlsx_compatibility_result=PASS; parsed the five target workbook sheets into 415 records
html_table_expansion_result=PASS; real HTML table blocks expanded deterministically with caption/bbox trace
period_context_result=PASS; annual periods preserved and statement contexts kept separate
unit_handling_result=PASS; unit metadata normalized and unit-incompatible rows route to UNIT_REVIEW
real_local_smoke_result=PASS; local smoke completed with compact counts only
comparison_summary=mineru_record_count=415; original_record_count=415; comparison_row_count=416; match_count=414; conflict_count=0; mineru_only_count=0; original_only_count=1; unparseable_count=1; unit_review_count=0; review_required_count=2
boundary_check=PASS; demo-only, no clean_data, no DB, no production hook, no MinerU/OCR/LLM/VLM
readiness_gates=CLOSED
recommended_next_task=348N-R7CD-QA real artifact compatibility slice review
```
