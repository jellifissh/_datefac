# 333A Bilingual README Refresh And Operator Guides

## Goal
Fully rewrite the root `README.md` based on the current whole-project state, and create bilingual Chinese / English documentation for project presentation, operation, and beginner usage.

This is a documentation-only task.

## Prerequisite
- The latest completed stage must be `332A Demo Release Audit`.
- If `332A` is not committed and pushed, stop and report:
  - `332A should be committed and pushed before starting 333A.`

## Scope
- Rewrite the root `README.md`
- Create bilingual operator guides
- Create bilingual runbooks
- Create bilingual project overviews
- Create the 333A task document

## Files To Modify Or Create
1. `README.md`
2. `docs/demo/（中文新手指南）datefac_newbie_operator_guide_333a_zh.md`
3. `docs/demo/（英文新手指南）datefac_newbie_operator_guide_333a_en.md`
4. `docs/demo/（中文运行手册）datefac_current_runbook_333a_zh.md`
5. `docs/demo/（英文运行手册）datefac_current_runbook_333a_en.md`
6. `docs/demo/（中文项目总览）datefac_project_overview_333a_zh.md`
7. `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`
8. `docs/codex_tasks/333A_bilingual_readme_refresh_and_operator_guides.md`

## Source Material To Inspect Before Writing
- `README.md`
- `docs/demo/*.md`
- `docs/codex_tasks/*.md`
- `tools/run_*.py`
- `tests/trust/*.py`
- `datefac/trust/*.py`
- recent commits if useful
- runner defaults and output paths
- 331B and 332A demo docs
- current summaries referenced by the runners

## Current Required Status
- `project_status = DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- `client_ready = false`
- `production_ready = false`

## Required Current Metrics
- `13 unfamiliar PDFs`
- `7 PDFs produced candidates`
- `prepared_candidate_row_count = 117`
- `original_trusted_sheet_row_count = 96`
- `reviewed_unit_confirmed_count = 2`
- `reviewed_trusted_preview_row_count = 98`
- `human_rejected_row_count = 18`
- `remaining_review_required_after_unit_review_count = 1`
- `apply_plan_row_count = 21`
- `overclaim_risk_count = 0`
- `qa_fail_count = 0`

## README Requirements
- Chinese first, then English
- Suitable for GitHub visitors, interviewers, and reviewers
- Explain what DateFac does, why it exists, and what its current limits are
- Include:
  - project title
  - Chinese summary
  - English summary
  - problem statement
  - current status
  - current metrics
  - core capabilities
  - architecture overview
  - stage history through `332A`
  - current demo pipeline commands
  - safe showcase files
  - safety boundaries
  - known limitations
  - next milestones

## Bilingual Content Rules
- Chinese and English sections must be technically consistent
- Numbers and stage names must match exactly
- Chinese must not be a rough summary of English
- English must not read like broken translation
- Avoid random language mixing except for technical terms

## Length Targets
- `README.md`: roughly `4,000-7,000` Chinese-character-equivalent, bilingual
- `datefac_newbie_operator_guide_333a_zh.md`: `7,000-10,000` Chinese characters
- `datefac_newbie_operator_guide_333a_en.md`: `4,000-7,000` English words
- `datefac_current_runbook_333a_zh.md`: `3,000-5,000` Chinese characters
- `datefac_current_runbook_333a_en.md`: `2,000-4,000` English words
- `datefac_project_overview_333a_zh.md`: `3,000-5,000` Chinese characters
- `datefac_project_overview_333a_en.md`: `2,000-4,000` English words

## Minimum Totals
- Total Chinese generated documentation: at least `10,000` Chinese characters
- Total English generated documentation: at least `6,000` English words
- No filler-only padding

## Safety Rules
- Do not modify production pipeline
- Do not modify parser / extraction / delivery behavior
- Do not modify official assets
- Do not modify previous output artifacts
- Do not modify protected dirty files
- Do not use `git add -A`
- Do not use `git add .`
- Do not commit unless explicitly asked later

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Validation
- Verify README includes:
  - `330L`
  - `331A`
  - `330K2`
  - `330K3`
  - `330K4`
  - `331B`
  - `332A`
  - `DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
  - `client_ready = false`
  - `production_ready = false`
  - `reviewed_trusted_preview_row_count = 98`
  - `human_rejected_row_count = 18`
  - `remaining_review_required_after_unit_review_count = 1`
  - `qa_fail_count = 0`
- Verify docs mention:
  - `sidecar`
  - `demo`
  - `preview`
  - `no write-back`
  - `human review`
  - `current limitations`
- Verify forbidden positive claims are absent:
  - `client-ready`
  - `production-ready`
  - `ready for production`
  - `production deployment`
  - `fully automatic commercial system`
  - `guaranteed accuracy`
  - `100% accurate`
  - `direct investment decision`
  - `no human review needed`
  - `customer-ready SaaS`
- Negative forms are allowed:
  - `not client-ready`
  - `not production-ready`
  - `not ready for production`
  - `not a fully automatic commercial system`
  - `does not guarantee 100% accuracy`

## Reporting Requirements
After editing, report:
1. files changed
2. summary of README rewrite
3. summary of Chinese docs
4. summary of English docs
5. unsafe claim check result
6. approximate length counts
7. `git status -sb`
