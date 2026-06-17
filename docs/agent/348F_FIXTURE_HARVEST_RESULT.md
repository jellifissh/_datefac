# 348F Fixture Harvest Result

## Task ID

`348F Fixture Harvest from 346B`

## Fixture Sources Used

Primary source documents:

- `docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md`
- `docs/agent/348S_R2_QA_UNIT_PERIOD_RESIDUAL_REFINEMENT_REVIEW.md`
- `docs/agent/FIXTURE_STRATEGY.md`

Narrow legacy lesson source used only for semantic traceability:

- `docs/codex_tasks/346B2_recovery_candidate_qa_audit.md`

Harvest strategy:

- use 348A-R4 and 348S-R2-QA as the current verified behavior source
- use 346B2 only as a compact statement of historical unit-risk classes:
  - ratio/multiple
  - percentage/margin
  - per-share
  - monetary amount

## Fixture Files Created

Created fixture files:

- `tests/agent/fixtures/unit_semantics__346b_lessons_and_348s_r2__v1.json`
- `tests/agent/fixtures/period_detection__embedded_headers_and_missing_period__v1.json`
- `tests/agent/fixtures/routing_policy__narrative_market_strict_and_missing_evidence__v1.json`

## Test Changes

Modified:

- `tests/agent/test_agent_excel_intake_audit_348a.py`

Added fixture-backed tests for:

- unit semantic fixture cases
- period detection fixture cases
- clean/review routing fixture cases

The existing inline tests were preserved. The new fixture tests supplement them rather than replacing them.

## Validation Results

- `python -m py_compile tests\agent\test_agent_excel_intake_audit_348a.py` -> passed
- `python -m pytest tests\agent -q` -> passed

## What Behavior Is Now Protected

Fixture-backed protection now covers:

- `资产负债率(%)` stays a rate metric and does not trigger `monetary_unit_mismatch`
- `资产负债率(%,LF)` stays a rate metric and does not trigger `monetary_unit_mismatch`
- `资产总计(%)` still triggers `monetary_unit_mismatch`
- `负债合计(%)` still triggers `monetary_unit_mismatch`
- ROE-style percentage metrics stay protected from the old false-positive pattern
- embedded period labels such as `2025A收入(亿元)` and `2026E毛利率(%)` stay detectable
- truly periodless strict financial rows still trigger `period_context_missing`
- narrative rows stay out of `clean_data`
- market reference rows with weak evidence can become `INTERNAL_REFERENCE_CANDIDATE`
- strict financial rows with weak evidence and no blocking issues can become `INTERNAL_CLEAN_CANDIDATE`
- strict financial rows with period issues stay `REVIEW_REQUIRED`
- missing-evidence rows stay excluded from clean data

## What Was Intentionally Not Harvested

Not harvested:

- full 346B output folders
- real PDF content
- large CSV output snapshots
- legacy runners
- legacy `datefac/` code
- broad replay fixtures that depend on `input/` or `output/`

This task kept fixtures compact and semantic.

## Remaining Risks

- The fixtures are intentionally narrow and do not yet cover full workbook-shape variation.
- `346B` lessons were harvested as semantics, not as exact historical row payloads.
- Future fixture work may still need valuation-metric confusion and per-share-vs-total-amount cases beyond the minimal current set.

## Decision

Primary decision:

`348F_CONFIRMED_FIXTURE_HARVEST_COMPLETE`

## Recommended Next Task

`348F-QA Fixture Harvest Review`

Alternative next task if broader real-world validation is preferred:

`348S Third Workbook Pilot`
