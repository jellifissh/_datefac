# 342A Larger Real-PDF Benchmark Plan

## Goal

Create a larger real-PDF benchmark planning package that expands the current limited real-PDF sample set into a repeatable benchmark plan.

This task is planning, inventory, manifest, and runbook only.
It must not run large-scale parsing.
It must not modify production pipeline, parser, extraction, or delivery behavior.
It must not generate client export artifacts.

## Current Upstream State

- `341A decision = HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY`
- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Inputs

- `D:/_datefac/input`
- `D:/_datefac/output/human_reviewed_client_preview_milestone_341a`
- `D:/_datefac/output/client_preview_export_audit_340g`
- `D:/_datefac/output/client_preview_after_human_review_340f`

## Future User-Addable Input Dir

- `D:/_datefac/input/real_pdf_benchmark_342a`

## Output Dir

- `D:/_datefac/output/larger_real_pdf_benchmark_plan_342a`

## Output Files

- `larger_real_pdf_benchmark_plan_342a.xlsx`
- `larger_real_pdf_benchmark_plan_342a_summary.json`
- `larger_real_pdf_benchmark_plan_342a_manifest.json`
- `larger_real_pdf_benchmark_plan_342a_qa.json`
- `larger_real_pdf_benchmark_plan_342a_report.md`

## Workbook Sheets

1. `00_README`
2. `01_BENCHMARK_SUMMARY`
3. `02_PDF_INVENTORY`
4. `03_SAMPLE_TIERS`
5. `04_TARGET_METRICS`
6. `05_RUN_PLAN`
7. `06_REVIEW_BUDGET`
8. `07_SUCCESS_CRITERIA`
9. `08_RISK_REGISTER`
10. `09_NEXT_STEPS`
11. `10_NO_WRITE_BACK_PROOF`

All sheet names must be `<= 31` characters.

## Required PDF Inventory Fields

- `pdf_id`
- `file_name`
- `file_path`
- `file_size_mb`
- `modified_time`
- `document_hint`
- `source_bucket`
- `detected_in_current_sample`
- `planned_benchmark_status`

## Required Summary Fields

- `current_pdf_count`
- `target_pdf_count_min = 10`
- `target_pdf_count_recommended = 30`
- `target_pdf_count_stretch = 50`
- `benchmark_status = NEEDS_MORE_PDFS` or `READY_FOR_SMALL_SCALE_BENCHMARK`
- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`
- `decision = LARGER_REAL_PDF_BENCHMARK_PLAN_342A_READY`

## Required 341A / 340G / 340F Detection

Prefer reading:

- `summary.json`
- or `report.md` only as a fallback

Capture if available:

- `341A decision`
- `340G audit passed`
- `340F client_preview_core_metric_count = 34`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`

If a summary is missing, record a warning and do not invent values.

## Required Sample Tiers

- `Tier A: clean financial forecast table`
- `Tier B: multi-panel financial statements`
- `Tier C: multi-page tables / cross-page tables`
- `Tier D: scanned or OCR-heavy PDF`
- `Tier E: mixed industry/comparable-company tables`
- `Tier F: severe layout / table-header confusion`

Each tier must include:

- `tier_name`
- `description`
- `expected_parser_risk`
- `expected_review_burden`
- `recommended_pdf_count`
- `main_failure_modes`

## Required Target Metrics

- `revenue`
- `net_profit`
- `EPS`
- `PE`
- `PB`
- `ROE`
- `revenue_yoy`
- `net_profit_yoy`
- `gross_margin`
- `net_margin`

Each metric must include:

- `metric`
- `display_name_zh`
- `expected_unit`
- `high_risk_unit_confusion`
- `benchmark_priority`
- `validation_notes`

## Required Run Plan

- `342B: Real PDF Corpus Intake And Metadata Audit`
- `342C: MinerU Batch Parse Benchmark`
- `342D: Parser Ensemble Compare Benchmark`
- `342E: Core Metric Candidate Quality Audit`
- `342F: AI Review Scaling Simulation`
- `342G: Human Review Burden Estimate`
- `342H: Client Preview Benchmark Rollup`

Each row must include:

- `stage_id`
- `stage_name`
- `goal`
- `input`
- `output`
- `success_criteria`
- `should_modify_pipeline = false`

## Required Review Budget Estimates

Estimate scenarios for:

- `10 PDFs`
- `30 PDFs`
- `50 PDFs`

Include:

- `expected_candidate_rows`
- `expected_review_required_rows`
- `expected_human_minutes_low`
- `expected_human_minutes_high`
- `main_cost_driver`

These are estimates only and must not pretend to be exact.

## Required Success Criteria

At minimum include:

- `parser_success_rate`
- `core_metric_candidate_count`
- `trusted_or_confirmed_ratio`
- `review_required_ratio`
- `unit_issue_rate`
- `duplicate_issue_rate`
- `source_trace_coverage`
- `client_preview_audit_pass_rate`

Also state clearly that `341A` is still a small-sample milestone and not evidence of production stability.

## Required Risk Register

Include at minimum:

- `parser robustness`
- `OCR-heavy PDFs`
- `unit ambiguity`
- `year alignment`
- `duplicate rows`
- `non-core industry tables`
- `metadata confusion`
- `review burden explosion`
- `client overclaim risk`

## No-Write-Back Proof

The proof must show:

- no upstream workbooks changed
- no official assets changed
- no client export generated
- no production pipeline / parser / extraction / delivery paths were modified by this task

## QA Requirements

- input directories checked
- PDF inventory generated
- 341A / 340G / 340F summary detected if available
- sample tiers generated
- target metrics generated
- run plan generated
- review budget generated
- success criteria generated
- risk register generated
- no write-back proof generated
- no sheet name exceeds 31 chars
- no `client_ready = true`
- no `production_ready = true`
- no investment advice claim
- `qa_fail_count = 0`

## Files

- `docs/codex_tasks/342A_larger_real_pdf_benchmark_plan.md`
- `datefac/benchmark/larger_real_pdf_benchmark_plan_342a.py`
- `datefac/benchmark/larger_real_pdf_benchmark_plan_342a_report.py`
- `tools/run_larger_real_pdf_benchmark_plan_342a.py`
- `tests/benchmark/test_larger_real_pdf_benchmark_plan_342a.py`

## Run

```powershell
python -m py_compile datefac\benchmark\larger_real_pdf_benchmark_plan_342a.py datefac\benchmark\larger_real_pdf_benchmark_plan_342a_report.py tools\run_larger_real_pdf_benchmark_plan_342a.py tests\benchmark\test_larger_real_pdf_benchmark_plan_342a.py

python -m pytest tests\benchmark\test_larger_real_pdf_benchmark_plan_342a.py -q

python tools\run_larger_real_pdf_benchmark_plan_342a.py --input-dir D:\_datefac\input --milestone-341a-dir D:\_datefac\output\human_reviewed_client_preview_milestone_341a --client-preview-audit-340g-dir D:\_datefac\output\client_preview_export_audit_340g --client-preview-340f-dir D:\_datefac\output\client_preview_after_human_review_340f --output-dir D:\_datefac\output\larger_real_pdf_benchmark_plan_342a
```
