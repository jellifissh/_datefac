# 348N-R7CC mainline MinerU/original reconciliation vertical slice demo

## Task ID

```text
348N-R7CC mainline MinerU/original reconciliation vertical slice demo
```

Task type: mainline reconciliation vertical slice.

## Preflight

```text
git status -sb
PASS: clean before pull.

git pull origin pivot/348-agent-foundation
PASS: already up to date.

git status -sb
PASS: clean after pull.
```

## Reason for pivot back to mainline

R7CB proved a minimum local test DB prototype, but R7CC intentionally pauses the DB/adapter/repository chain. The mainline need is to show a small deterministic reconciliation path from MinerU-style extracted data and an existing extraction artifact into comparison rows and review_queue-style candidates.

## Mainline vertical slice scope

Implemented a tiny pure-Python slice:

```text
MinerU-style artifact + existing extraction artifact
-> normalize metric / period / value
-> compare values
-> produce reconciliation rows
-> produce review_queue-style candidates
```

This slice does not run MinerU, OCR, LLM, VLM, PDF extraction, DB persistence, delivery/export, clean_data writes, or readiness changes.

## Files changed

Created the allowed R7CC files:

- `datefac_agent/reconciliation/__init__.py`
- `datefac_agent/reconciliation/mineru_original_reconciliation_348n.py`
- `tests/agent/test_mineru_original_reconciliation_348n.py`
- `tests/agent/fixtures/mineru_original_reconciliation/mineru_content_list_sample.json`
- `tests/agent/fixtures/mineru_original_reconciliation/original_extraction_sample.json`
- `docs/agent/348N_R7CC_MAINLINE_MINERU_ORIGINAL_RECONCILIATION_VERTICAL_SLICE_DEMO_REPORT.md`

## Fixture design

The fixtures are tiny and curated:

- MinerU sample is a content_list_v2-style page-grouped table block.
- Original sample is a small existing-extraction JSON with three rows.

They prove the required demo cases:

- `Revenue 2023 = MATCH`
- `Net Profit 2023 = CONFLICT`
- `EPS 2023 = MINERU_ONLY`
- `ROE 2023 = ORIGINAL_ONLY`

## Loading behavior

`load_json_artifact(...)` loads JSON fixtures. `load_and_reconcile(...)` loads both inputs and delegates to the pure reconciliation path. The module does not write outputs.

## Normalization behavior

Implemented deterministic normalization:

- metric aliases: English and Chinese aliases normalize to canonical metric keys;
- period strings normalize common annual strings like `FY2023` and `2023年度` to `2023`;
- numeric strings normalize commas, percent signs, and parenthesized negatives to stable decimal strings.

## Comparison behavior

`reconcile_mineru_original(...)` returns comparison rows with:

- `metric`
- `period`
- `mineru_value`
- `original_value`
- `status`
- `reason`
- `review_required`
- `blocked_delivery_reason`
- `evidence_preview`
- `source_trace`

Only `CONFLICT`, `MINERU_ONLY`, `ORIGINAL_ONLY`, and `UNPARSEABLE` require review by default.

## Review_queue candidate behavior

`build_review_queue_candidates(...)` emits compact metadata-first review_queue-style candidates only for review-required rows. Candidates include deterministic `review_item_id`, status, reason, bounded evidence preview, source trace, `review_status = PENDING_REVIEW`, `clean_data_eligible = false`, and closed readiness gates.

## Boundary review

R7CC does not continue DB work. It adds no schema, migration, DB adapter, repository implementation, delivery/export integration, clean_data write, or readiness change. Static tests confirm no DB/network/LLM/OCR/MinerU runtime imports.

Readiness remains:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Validation outputs

```text
python -m py_compile datefac_agent/reconciliation/mineru_original_reconciliation_348n.py
PASS

python -m py_compile tests/agent/test_mineru_original_reconciliation_348n.py
PASS

python -m pytest tests/agent/test_mineru_original_reconciliation_348n.py -q
PASS: 11 passed in 0.10s

python -m pytest tests/agent/test_review_queue_writer_contract_348n.py -q
PASS: 24 passed in 0.14s

python -m pytest tests/agent/test_review_queue_writer_schema_alignment_contract_348n.py -q
PASS: 29 passed in 0.20s

python -m pytest tests/agent -q
PASS: 803 passed in 3.30s

git status -sb
PASS before staging: only allowed R7CC files are untracked.

git diff --stat
PASS before staging: no tracked diff outside untracked allowed R7CC files.

git diff --name-only
PASS before staging: no tracked diff outside untracked allowed R7CC files.

git diff --check
PASS: no whitespace errors.
```

## Limitations

- This is a tiny demo fixture, not a full reconciliation engine.
- It does not parse full MinerU output or real PDFs.
- It does not solve duplicate metric ambiguity, cross-table hierarchy, unit conversion, or production review UI.
- It does not write clean_data, delivery/export files, DB rows, or readiness state.

## Decision

PASS. R7CC implements a small deterministic mainline reconciliation vertical slice with tiny fixtures, comparison rows, and review_queue-style candidates while preserving safety boundaries.

## Recommended next task

```text
348N-R7CC-QA mainline MinerU/original reconciliation vertical slice review
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS; R7CC mainline reconciliation vertical slice completed.
build_result（构建结果）= PASS; required py_compile commands passed.
test_result（测试结果）= PASS; R7CC tests 11 passed, writer contract 24 passed, schema alignment 29 passed, full tests/agent 803 passed.
files_modified（修改文件数）= 6.
error_count（错误数）= 0.
mainline_vertical_slice_result（主线纵切结果）= PASS; MinerU/original reconciliation demo implemented.
normalization_result（标准化结果）= PASS; metric, period, and numeric normalization covered.
comparison_result（对比结果）= PASS; MATCH, CONFLICT, MINERU_ONLY, and ORIGINAL_ONLY covered.
review_queue_candidate_result（review_queue候选结果）= PASS; review-required rows become compact candidates.
boundary_check（边界检查）= PASS; no DB, schema, migration, clean_data, delivery/export, MinerU/OCR/LLM/VLM, or readiness changes.
readiness_gates（就绪门）= CLOSED; client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true.
recommended_next_task（推荐下一任务）= 348N-R7CC-QA mainline MinerU/original reconciliation vertical slice review.
```
