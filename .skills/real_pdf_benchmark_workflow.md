# Skill: Real PDF Benchmark Workflow

## Scope
This skill covers the real PDF benchmark path from `342A` through `342C2`, plus `342C4` environment repair.

## Workflow
- `342A` larger real-PDF benchmark plan
- `342B` corpus intake / metadata audit
- `342C` MinerU pilot first failure
- `342C2` verified env retry
- `342C4` environment repair

## Current Key Results
- `342A current_pdf_count = 31`
- `benchmark_status = READY_FOR_SMALL_SCALE_BENCHMARK`
- `target_pdf_count_min/recommended/stretch = 10/30/50`
- `342B unique_pdf_count = 31`
- `duplicate_pdf_count = 0`
- `pilot/benchmark/holdout = 5/20/6`
- `ready_for_342c = true`
- `342C first run = 0/5 due to SSL/HuggingFace/env issue`
- `342C2 after env fix = 3/5 success, 2 failed/empty`
- `ready_for_342d = conditional`

## What To Do Next
- inspect failed retry rows
- if failures are environment/path/output matching related, fix runner audit
- if failures are PDF-specific, mark parser risk explicitly
- only then proceed to `342D Parser Ensemble Compare Benchmark`
- do not skip directly to full 31 PDFs

## Current Boundary
- benchmark outputs are parser evaluation evidence
- benchmark outputs are not client delivery assets
- conditional MinerU success is not a full parser endorsement

