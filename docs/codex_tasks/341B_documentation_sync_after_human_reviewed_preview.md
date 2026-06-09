# 341B Documentation Sync And Demo Runbook After Human-Reviewed Client Preview Milestone

## Goal

Synchronize repository documentation to the validated 341A milestone state after the human-reviewed client preview chain.

This task is documentation-only.
It must not modify production pipeline, parser, extraction, or delivery behavior.
It must not modify output artifacts.
It must not modify official assets.

## Current Upstream State

- `341A decision = HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY`
- `demo_ready = true`
- `client_preview_ready = true`
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Required Chain To Document

`Real PDFs -> MinerU-first extraction -> AI dry-run review -> Human review -> 340C full validation -> 340D apply plan -> 340E post-human sidecar -> 340F client preview -> 340G audit -> 341A milestone package`

## New Docs

- `docs/codex_tasks/341B_documentation_sync_after_human_reviewed_preview.md`
- `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_zh.md`
- `docs/demo/datefac_human_reviewed_client_preview_runbook_341b_en.md`
- `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_zh.md`
- `docs/demo/datefac_human_reviewed_client_preview_architecture_341b_en.md`

## Docs To Update

- `README.md`
- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md`
- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md`
- `docs/demo/datefac_ai_review_architecture_339a_zh.md`
- `docs/demo/datefac_ai_review_architecture_339a_en.md`
- `docs/demo/datefac_demo_release_checklist_332a.md`
- `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
- `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`
- `docs/demo/（中文运行手册）datefac_current_runbook_333a_zh.md`
- `docs/demo/（英文运行手册）datefac_current_runbook_333a_en.md`

## Required Statements

All synced docs must clearly preserve:

- current phase is `demo_ready / client_preview_ready`
- `client_ready = false`
- `production_ready = false`
- not investment advice
- AI decisions are dry-run only
- human review was used before client preview
- `340F` is a human-reviewed client preview, not official delivery
- `340G` audit passed
- current benchmark is a limited real PDF sample set
- next bottlenecks are larger benchmark, parser robustness, metadata extraction, UI review workflow, and batch reliability

## Required Metrics

- `340B review queue = 77`
- `340C filled = 77 / pending = 0`
- `340D reviewed_after_human_candidate_count = 34`
- `340E reviewed_after_human_total_count = 34`
- `340F client_preview_core_metric_count = 34`
- `340G audited_core_metric_count = 34`
- `duplicate_issue_count = 0`
- `unit_issue_count = 0`
- `missing_source_trace_count = 0`
- `unsafe_claim_count = 0`
- `qa_fail_count = 0`

## Required Sections Across The New Docs

1. one-line positioning
2. what the current demo can show
3. what the current demo must not promise
4. real workflow diagram
5. main Excel artifact list
6. human-review loop explanation
7. AI review role explanation
8. risk-control explanation
9. demo operation steps
10. next-stage roadmap

## Validation

- run text checks only
- confirm there is no accidental `client_ready = true`
- confirm there is no accidental `production_ready = true`
- confirm not investment advice wording remains explicit
- confirm 341A milestone status appears in the synced docs
- confirm output artifacts are not modified or staged

## Boundaries

- do not modify Python source unless explicitly needed
- do not modify output directories
- do not modify official assets
- do not commit output artifacts
- do not use `git add -A`
- do not use `git add .`
