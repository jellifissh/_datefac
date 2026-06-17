# 348F-QA Fixture Harvest Review

## Task ID

`348F-QA Fixture Harvest Review`

## Files Reviewed

Reviewed fixture files:

- `tests/agent/fixtures/unit_semantics__346b_lessons_and_348s_r2__v1.json`
- `tests/agent/fixtures/period_detection__embedded_headers_and_missing_period__v1.json`
- `tests/agent/fixtures/routing_policy__narrative_market_strict_and_missing_evidence__v1.json`

Reviewed test file:

- `tests/agent/test_agent_excel_intake_audit_348a.py`

Reviewed result/context docs:

- `docs/agent/348F_FIXTURE_HARVEST_RESULT.md`
- `docs/agent/FIXTURE_STRATEGY.md`
- `docs/agent/348S_R2_QA_UNIT_PERIOD_RESIDUAL_REFINEMENT_REVIEW.md`
- `docs/agent/348A_R4_QA_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md`

## Fixture Structure QA

Findings:

- all three fixtures are compact JSON files rather than copied output snapshots
- file sizes remain small and local-test friendly:
  - unit fixture: about `2.9 KB`
  - period fixture: about `1.7 KB`
  - routing fixture: about `4.3 KB`
- no fixture depends on `input/`, `output/`, `temp/`, or `data/`
- each fixture includes traceability fields such as:
  - `source_task`
  - `issue_type`
  - `why_it_matters`
  - per-case `case_id`
- fixture payloads are semantic reductions, not raw historical dumps

Conclusion:

Fixture structure is appropriately narrow and consistent with `FIXTURE_STRATEGY.md`.

## Unit Fixture QA

Verified coverage:

- `资产负债率(%)` -> no `monetary_unit_mismatch`
- `资产负债率(%,LF)` -> no `monetary_unit_mismatch`
- `资产总计(%)` -> `monetary_unit_mismatch`
- `负债合计(%)` -> `monetary_unit_mismatch`
- `净资产收益率(%)` -> preserved rate-metric behavior
- `EPS(百万元)` -> `per_share_unit_mismatch`

Test quality:

- tests load fixture rows and convert them into real `SpreadsheetRow` objects
- tests call the real `audit_unit_semantics()` checker
- tests compare actual returned issue codes rather than fixture constants alone

Conclusion:

The unit fixture set is valid and does exercise real checker behavior.

## Period Fixture QA

Verified coverage:

- `2025A收入(亿元)` -> `2025A`
- `2026E收入(亿元)` -> `2026E`
- `2027E收入(亿元)` -> `2027E`
- `2028E收入(亿元)` -> `2028E`
- `2026E毛利率(%)` -> `2026E`
- generalized label mix `FY2026` / `2027FY` / `2028 Q1`
- truly periodless strict financial row -> `period_context_missing`

Test quality:

- tests call the real `detect_period_labels()` logic
- period-row fixtures also call the real `audit_period_alignment()` checker
- expected period detection and expected issue codes are asserted separately

Conclusion:

The period fixture set is valid and meaningfully protects the 348S-R2 embedded-header repair.

## Routing Policy Fixture QA

Verified coverage:

- narrative rows stay `NARRATIVE_REVIEW`
- market reference weak-evidence rows become `INTERNAL_REFERENCE_CANDIDATE`
- strict financial weak-evidence clean rows become `INTERNAL_CLEAN_CANDIDATE`
- strict financial rows with period issue stay `REVIEW_REQUIRED`
- missing-evidence rows stay `EXCLUDED_FROM_CLEAN_DATA`

Test quality:

- routing tests call real logic through:
  - `audit_unit_semantics()` when applicable
  - `audit_period_alignment()` when applicable
  - `audit_evidence_presence()` when applicable
  - `build_row_audit_result()`
  - `build_review_queue_rows()`
- this confirms the tests exercise actual policy routing, not static fixture metadata replay

Conclusion:

The routing fixture set is valid and protects the current internal clean/review policy boundaries.

## Test Implementation Quality

Positive findings:

- fixture-backed tests supplement rather than replace existing inline tests
- fixtures are used as structured inputs, not as precomputed golden decisions only
- the new tests target pure functions and policy helpers directly
- no dependency on large local directories or external runtime state was introduced

Residual limitation:

- the tests still assert expected outputs encoded in fixture JSON, so fixture mistakes could still encode a wrong expectation if not caught by QA
- however, this is mitigated because the fixtures are small, readable, and routed through real checker logic

## Validation Results

- `python -m py_compile tests\agent\test_agent_excel_intake_audit_348a.py` -> passed
- `python -m pytest tests\agent -q` -> passed
- current result: `29 passed`

## Boundary Discipline

Confirmed:

- no source-code modules under `datefac_agent/` were modified in this QA task
- no new fixture categories were added
- no output files were committed or touched
- legacy `datefac/` remained untouched
- old runners remained untouched
- MinerU / LLM / OCR were not called
- no PDF re-extraction was performed

## Remaining Risks

- fixture scope remains intentionally narrow and does not yet cover valuation-metric confusion cases
- per-share coverage currently has one guardrail case, but broader per-share families may still need follow-up fixtures
- workbook-shape generalization is still better validated by future real-workbook pilots than by fixtures alone

## Decision

Primary decision:

`348F_QA_CONFIRMED_FIXTURE_HARVEST_VALID`

## Recommended Next Task

`348S Third Workbook Pilot`

Alternative next task if test hardening should continue before more real-workbook expansion:

`348F-R1 Add Valuation/Per-Share Fixtures`
