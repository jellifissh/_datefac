# 342B Real PDF Corpus Intake And Metadata Audit

## Goal

Create a real-PDF corpus intake and metadata audit package for the current benchmark corpus.

This task is intake, manifest, hashing, dedup, tier assignment, split planning, and readiness audit only.
It must not run MinerU.
It must not deeply parse PDF table content.
It must not modify production pipeline, parser, extraction, or delivery behavior.
It must not generate client export artifacts.

## Current Upstream State

- `342A decision = LARGER_REAL_PDF_BENCHMARK_PLAN_342A_READY`
- `current_pdf_count = 31`
- `benchmark_status = READY_FOR_SMALL_SCALE_BENCHMARK`
- `target_pdf_count_min / recommended / stretch = 10 / 30 / 50`
- `341A decision = HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY`
- `340G decision = CLIENT_PREVIEW_EXPORT_AUDIT_340G_READY`
- `340F client_preview_core_metric_count = 34`
- `qa_fail_count = 0`

## Inputs

- `D:/_datefac/input`
- `D:/_datefac/output/larger_real_pdf_benchmark_plan_342a`

## Optional Nested Input

- `D:/_datefac/input/real_pdf_benchmark_342a`

## Output Dir

- `D:/_datefac/output/real_pdf_corpus_intake_342b`

## Output Files

- `real_pdf_corpus_intake_342b.xlsx`
- `real_pdf_corpus_intake_342b_summary.json`
- `real_pdf_corpus_intake_342b_manifest.json`
- `real_pdf_corpus_intake_342b_qa.json`
- `real_pdf_corpus_intake_342b_no_write_back_proof.json`
- `real_pdf_corpus_intake_342b_report.md`

## Workbook Sheets

1. `00_README`
2. `01_CORPUS_SUMMARY`
3. `02_PDF_CORPUS`
4. `03_DEDUP_AUDIT`
5. `04_TIER_ASSIGNMENT`
6. `05_SPLIT_PLAN`
7. `06_METADATA_AUDIT`
8. `07_RUN_READINESS`
9. `08_RISK_FLAGS`
10. `09_NO_WRITE_BACK_PROOF`
11. `10_NEXT_STEPS`

All sheet names must be `<= 31` characters.

## Required PDF Corpus Fields

- `corpus_pdf_id`
- `file_name`
- `file_path`
- `file_size_mb`
- `sha256`
- `modified_time`
- `source_bucket`
- `document_hint`
- `page_count`
- `intake_status`

## Required Dedup Audit Fields

- `duplicate_group_id`
- `duplicate_count`
- `canonical_pdf_id`
- `duplicate_pdf_ids`
- `dedup_action`

Use:

- `dedup_action = KEEP_CANONICAL_REVIEW_DUPLICATES`

Do not delete files.
Do not move files.

## Required Tier Assignment Fields

Allowed tiers:

- `Tier A`
- `Tier B`
- `Tier C`
- `Tier D`
- `Tier E`
- `Tier F`
- `UNKNOWN`

Each row must include:

- `corpus_pdf_id`
- `assigned_tier`
- `tier_confidence`
- `tier_reason`
- `expected_parser_risk`
- `expected_review_burden`

Tier assignment must stay lightweight and transparent.
If confidence is low, prefer `UNKNOWN` rather than aggressive guessing.

## Required Split Plan

Create split labels:

- `pilot_set`
- `benchmark_set`
- `holdout_set`

Recommended rule when `current_pdf_count >= 30`:

- `pilot_set = 5`
- `benchmark_set = 20`
- `holdout_set = remaining`

Requirements:

- preserve tier diversity if practical
- do not place duplicates into different splits

Each row must include:

- `corpus_pdf_id`
- `split`
- `split_reason`

## Required Metadata Audit Counts

- `missing_sha256_count`
- `duplicate_pdf_count`
- `unreadable_pdf_count`
- `missing_page_count_count`
- `unknown_tier_count`
- `oversized_pdf_count`
- `zero_byte_file_count`

## Required Run Readiness

Audit readiness for `342C MinerU Batch Parse Benchmark`.

Rules:

- `current_pdf_count >= 10`
- `unique_pdf_count >= 10`
- `zero_byte_file_count = 0`
- duplicates do not block readiness but must be recorded
- unreadable PDFs may exist but must be surfaced as risk

Output fields:

- `ready_for_342c`
- `recommended_342c_scope`
- `recommended_first_run_pdf_count`
- `reason`

With current actual inventory near `31` PDFs and no blocking file-integrity issue, the likely recommendation is:

- `ready_for_342c = true`
- `recommended_342c_scope = pilot_set`
- `recommended_first_run_pdf_count = 5`

## Required Summary Fields

- `current_pdf_count`
- `unique_pdf_count`
- `duplicate_pdf_count`
- `assigned_tier_count`
- `unknown_tier_count`
- `pilot_set_count`
- `benchmark_set_count`
- `holdout_set_count`
- `ready_for_342c`
- `recommended_first_run_pdf_count`
- `qa_fail_count = 0`
- `client_ready = false`
- `production_ready = false`
- `decision = REAL_PDF_CORPUS_INTAKE_342B_READY`

## No-Write-Back Proof

The proof must show:

- no upstream benchmark plan summary changed
- no scanned input PDFs changed
- no PDF deleted or moved
- no official assets changed
- no client export generated
- no production pipeline / parser / extraction / delivery paths were modified by this task

## QA Requirements

- input directories checked
- 342A summary detected
- PDF corpus generated
- sha256 generated for each file
- duplicate audit generated
- tier assignment generated
- split plan generated
- metadata audit generated
- run readiness generated
- no PDF deleted or moved
- no parser/extraction/delivery modified
- no `client_ready = true`
- no `production_ready = true`
- no investment advice claim
- no sheet name exceeds 31 chars
- `qa_fail_count = 0`

## Files

- `docs/codex_tasks/342B_real_pdf_corpus_intake_metadata_audit.md`
- `datefac/benchmark/real_pdf_corpus_intake_342b.py`
- `datefac/benchmark/real_pdf_corpus_intake_342b_report.py`
- `tools/run_real_pdf_corpus_intake_342b.py`
- `tests/benchmark/test_real_pdf_corpus_intake_342b.py`

## Run

```powershell
python -m py_compile datefac\benchmark\real_pdf_corpus_intake_342b.py datefac\benchmark\real_pdf_corpus_intake_342b_report.py tools\run_real_pdf_corpus_intake_342b.py tests\benchmark\test_real_pdf_corpus_intake_342b.py

python -m pytest tests\benchmark\test_real_pdf_corpus_intake_342b.py -q

python tools\run_real_pdf_corpus_intake_342b.py --input-dir D:\_datefac\input --benchmark-plan-342a-dir D:\_datefac\output\larger_real_pdf_benchmark_plan_342a --output-dir D:\_datefac\output\real_pdf_corpus_intake_342b
```
