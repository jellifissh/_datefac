## Task ID

`348N-R3-QA Remaining Non-Normalized Unknown-Family Refinement Review`

## Reviewed Files

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/intake/excel_intake.py`
- `datefac_agent/review/clean_candidate_policy.py`
- `datefac_agent/review/review_queue_builder.py`
- `tools/run_agent_excel_intake_audit_348a.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`
- `docs/agent/348N_R3_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_RESULT.md`
- `docs/agent/348N_R2_QA_NORMALIZED_TESTSET_SCHEMA_SUPPORT_REVIEW.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R3_QA_remaining_non_normalized_unknown_family_refinement_review.md`

## Reviewed Output Directories

- R3 output: `D:\_datefac_agent\output\agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families`
  - `agent_excel_intake_audit_348a_manifest.json`
  - `agent_excel_intake_audit_348a_run_summary.json`
  - `audit_report.md`
  - `clean_data.csv`
  - `review_queue.csv`
  - `evidence_index.json`
- R2 baseline output: `D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema`
  - same artifact set, used for delta verification

## Implementation Boundary QA

Conclusion: VALID.

- R3 commit `708148f` touched only the allowed-scope files:
  - `datefac_agent/intake/excel_intake.py`
  - `datefac_agent/review/clean_candidate_policy.py`
  - `datefac_agent/schemas/audit_models.py`
  - `tools/run_agent_excel_intake_audit_348a.py`
  - `tests/agent/test_agent_excel_intake_audit_348a.py`
  - `docs/agent/348N_R3_..._RESULT.md`
- No legacy `datefac/` package touch.
- No `input/` mutation, no `output/` commit (`git ls-files output` shows no tracked R3 artifacts).
- No readiness-gate field was changed; the three gates stayed `false` and `demo_export_only` stayed `true`.
- No global loosening of unit / period / valuation / evidence / clean-candidate policy; the only policy additions are explicit schema-family branches.

## Target-Family Routing QA

Conclusion: VALID.

Routing in source confirmed against the documented R3 decision:

- `README` -> `TESTSET_SUPPORTING_ROW` (via `TESTSET_SUPPORTING_SHEETS` membership in `excel_intake.py`)
- `data_dictionary` -> `TESTSET_SUPPORTING_ROW`
- `doc_metadata` -> `TESTSET_SUPPORTING_ROW`
- `figure_index` -> `TESTSET_SUPPORTING_ROW`
- `related_research` -> `TESTSET_SUPPORTING_ROW`
- `validation_checks` -> `TESTSET_SUPPORTING_ROW` (detected via `_is_validation_checks_header`, then routed in `_refine_special_schema_row_type`)
- `market_base_data` -> `MARKET_REFERENCE_ROW` only when metric / value / unit / source-page lineage are all present; otherwise fallback `TESTSET_SUPPORTING_ROW` (`excel_intake.py:307-314`)
- `normalized_testset` -> unchanged `NORMALIZED_TESTSET_RECORD_ROW`

Routing is header-family based, not filename-only. `market_base_data` routing is explicitly gated on four lineage fields, so partial rows cannot sneak into `MARKET_REFERENCE_ROW`.

## Unknown-Row QA

Conclusion: VALID.

- `unknown_row_count: 48 -> 0`.
- R2 baseline `evidence_index` had `UNKNOWN_ROW` rows in README / data_dictionary / doc_metadata / figure_index / related_research / validation_checks sheets.
- R3 `evidence_index.json` (488 rows) contains zero `UNKNOWN_ROW` rows; every row resolves to one of:
  - `NORMALIZED_TESTSET_RECORD_ROW: 320`
  - `STRICT_FINANCIAL_TABLE_ROW: 109`
  - `TESTSET_SUPPORTING_ROW: 49`
  - `MARKET_REFERENCE_ROW: 10`
  - total 488, matching `row_count_total: 488`.
- The reduction came from explicit schema-family routing, not row hiding: `row_count_total` increased `484 -> 488` (better header-family recognition exposes previously malformed pseudo-header rows as real data rows), and the full 488-row population is still audited (`row_count_audited: 488`).

## Clean-Data Boundary QA

Conclusion: VALID (correctly tightened).

- `clean_data_row_count: 37 -> 33`.
- R2 `clean_data.csv` (37 rows) wrongly contained:
  - `README`: 2 rows (`MARKET_REFERENCE_ROW` / `INTERNAL_REFERENCE_CANDIDATE`)
  - `validation_checks`: 2 rows (`STRICT_FINANCIAL_TABLE_ROW` / `INTERNAL_CLEAN_CANDIDATE`)
  - `qualitative_facts`: 33 rows (legitimate)
- R3 `clean_data.csv` (33 rows) contains only `qualitative_facts` rows, all `INTERNAL_CLEAN_CANDIDATE` + `STRICT_FINANCIAL_TABLE_ROW` + `WEAK_EVIDENCE`.
- The 4 previously-leaked rows (README x2, validation_checks x2) are now `TESTSET_SUPPORTING_ROW` / `REVIEW_REQUIRED` and excluded from clean data.
- `internal_reference_candidate_count: 2 -> 0` (README leak removed); `internal_clean_candidate_count: 35 -> 33` (validation_checks leak removed).
- `validation_checks` removal from clean data is justified: it is a validation/cross-check sheet, not a financial fact source.
- No `TESTSET_SUPPORTING_ROW`, `NORMALIZED_TESTSET_RECORD_ROW`, or `MARKET_REFERENCE_ROW` appears in `clean_data.csv`.

## Review-Queue Explainability QA

Conclusion: VALID (explainable growth).

- `review_queue_row_count: 447 -> 455` (delta `+8`).
- Manifest formula: `narrative_review_count + review_required_count + excluded_from_clean_data_count`.
  - R2: `2 + 445 + 0 = 447`
  - R3: `0 + 455 + 0 = 455`
- Delta decomposition:
  - `narrative_review_count: 2 -> 0`: R2 README rows that were `NARRATIVE_REVIEW` are now `TESTSET_SUPPORTING_ROW` / `REVIEW_REQUIRED` (same queue, different bucket; net queue impact 0).
  - `review_required_count: 445 -> 455` (+10): +4 from the 4 rows removed out of clean data (README x2, validation_checks x2), +8 from the new `market_base_data` `MARKET_REFERENCE_ROW` rows that are `STRONG_EVIDENCE` (not `WEAK_EVIDENCE`, so policy returns `REVIEW_REQUIRED`), -2 from README rows reclassified out of the old `MARKET_REFERENCE_ROW`/`INTERNAL_REFERENCE_CANDIDATE` clean path (these 2 had been in clean data, now in queue). Net +10 within review_required, combined with narrative_review -2 gives +8 total.
- Note on the two queue counters: the manifest `review_queue_row_count` (455) counts all non-clean-candidate rows, while `review_queue.csv` (36 rows) only ships REVIEW/FAIL-decision rows. This is the pre-existing R2 design and R3 did not change the counter semantics.
- Queue growth is policy-conservative, not a forced shrink or a forced nicer number.

## Market-Base-Data QA

Conclusion: VALID (narrow and non-expanding).

- `market_reference_row_count: 2 -> 10`.
- R2 value of 2 came from README rows misrouted as `MARKET_REFERENCE_ROW`; R3 removes that misrouting and the 10 now come entirely from `market_base_data`.
- All 10 `market_base_data` rows in R3 `evidence_index.json`:
  - `row_type: MARKET_REFERENCE_ROW` (10/10)
  - `evidence_level: STRONG_EVIDENCE` (10/10)
  - `clean_candidate_type: REVIEW_REQUIRED` (10/10)
  - `decision: PASS` (10/10)
- Because they are `STRONG_EVIDENCE` (not `WEAK_EVIDENCE`), the clean-candidate policy returns `REVIEW_REQUIRED` at `clean_candidate_policy.py:34` before reaching the `MARKET_REFERENCE_ROW` branch, so none enter `INTERNAL_REFERENCE_CANDIDATE` or clean data.
- Routing is narrow: gated on metric + value + unit + source-page all being present (`excel_intake.py:307-314`); partial rows fall back to `TESTSET_SUPPORTING_ROW`.
- Clean-data acceptance did not widen: `internal_reference_candidate_count: 2 -> 0`.

## Normalized-Testset Regression QA

Conclusion: VALID (unchanged).

- `normalized_testset_record_row_count: 320 -> 320`.
- All 320 `normalized_testset` rows in R3 `evidence_index.json`:
  - `row_type: NORMALIZED_TESTSET_RECORD_ROW` (320/320)
  - `clean_candidate_type: REVIEW_REQUIRED` (320/320)
  - `decision: PASS` (320/320)
  - `evidence_level: STRONG_EVIDENCE` (320/320)
- `normalized_testset` detection stayed header-family based (`_is_normalized_testset_header`, >=8 of the 12 canonical headers), and the `NORMALIZED_TESTSET_RECORD_ROW` branch in `_refine_special_schema_row_type` is unchanged from R2.
- No normalized-testset row entered clean data.

## Runner Reporting QA

Conclusion: VALID.

- `run_agent_excel_intake_audit_348a.py` writes both `agent_excel_intake_audit_348a_manifest.json` and `agent_excel_intake_audit_348a_run_summary.json`, plus `audit_report.md`, `evidence_index.json`, `review_queue.csv`, `clean_data.csv`.
- New manifest counters `testset_supporting_row_count` are tracked in `_summarize_issues` and emitted in both manifest and run_summary.
- `clean_data_row_count` is computed as `internal_clean_candidate_count + internal_reference_candidate_count`.
- `review_queue_row_count` is computed as `narrative_review_count + review_required_count + excluded_from_clean_data_count`.
- Readiness flags and external-call counters are emitted in the manifest.

## Regression Test QA

Conclusion: VALID.

- `python -m pytest tests\agent -q` -> `48 passed`.
- New R3 tests assert the exact routing and clean-data exclusion:
  - `test_readme_rows_become_testset_supporting_rows_and_stay_out_of_clean_data`
  - `test_data_dictionary_rows_become_testset_supporting_rows_and_stay_out_of_clean_data`
  - `test_figure_index_rows_become_testset_supporting_rows_and_stay_out_of_clean_data`
  - `test_figure_index_metric_name_prefers_chart_id_over_title`
  - `test_validation_checks_rows_become_testset_supporting_rows_and_do_not_enter_clean_data` (inputs `STRICT_FINANCIAL_TABLE_ROW` to prove it is overridden)
  - `test_market_base_data_rows_become_market_reference_rows_but_do_not_expand_clean_data` (asserts `MARKET_REFERENCE_ROW` + `STRONG_EVIDENCE` + `REVIEW_REQUIRED`)
- Preserved R2 behavior:
  - `test_normalized_testset_header_detection_is_explicit`
  - `test_normalized_testset_rows_receive_explicit_schema_row_type`
  - `test_normalized_testset_rows_stay_out_of_clean_data`
- Wide-workbook classification regression still protected:
  - `test_normalized_testset_support_does_not_change_wide_workbook_classification` asserts a wide financial sheet still classifies as `STRICT_FINANCIAL_TABLE_ROW`.
- `test_runner_helper_manifest_contains_zero_external_calls` asserts `llm_api_call_count == 0`, `mineru_run_count == 0`, `ocr_run_count == 0`, and all three gates `False`.
- `test_clean_candidate_routing_fixture_cases` exercises the policy via fixture cases.

## Readiness Gate QA

Conclusion: VALID (gates closed).

From R3 manifest:
- `client_ready = false`
- `production_ready = false`
- `formal_client_export_allowed = false`
- `demo_export_only = true`

No gate field was modified by R3 source changes.

## External Call QA

Conclusion: VALID (zero external calls).

From R3 manifest:
- `llm_api_call_count = 0`
- `mineru_run_count = 0`
- `ocr_run_count = 0`

No MinerU / OCR / LLM / VLM invocation paths exist in the R3 diff. The runner hardcodes these counters to 0 in `build_manifest`.

## Baseline Validation

- `python -m pytest tests\agent -q`
- result: `48 passed` (with `D:\anaconda\python.exe`)
- note: `git pull --ff-only origin pivot/348-agent-foundation` failed due to network reset; local branch was already at `origin/pivot/348-agent-foundation` with a clean worktree (`## pivot/348-agent-foundation...origin/pivot/348-agent-foundation`), so the QA proceeded on the local copy. No remote-only commits were missed.

## Decision

`348N_R3_QA_CONFIRMED_REMAINING_UNKNOWN_FAMILY_REFINEMENT_VALID`

## Recommended Next Task

- `348N-R4 clean data candidate policy review` (the manifest's `recommended_next_step` already points to `348A-R4-QA Clean Data Candidate Policy Review`).
- Optionally, a separate task for the still-strict but likely testset-specific `qualitative_facts` family if future sample coverage shows its 33 `WEAK_EVIDENCE` rows should not all remain in clean data.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R3_QA_CONFIRMED_REMAINING_UNKNOWN_FAMILY_REFINEMENT_VALID
unknown_row_count（未知行数）= 0
clean_data_row_count（清洗数据行数）= 33
review_queue_row_count（审核队列行数）= 455
testset_supporting_row_count（测试集辅助行数）= 49
market_reference_row_count（市场参考行数）= 10
normalized_testset_record_row_count（标准化测试集记录行数）= 320
pytest_result（测试结果）= 48 passed
LLM / MinerU / OCR calls（外部调用次数）= 0
clean_data_boundary（清洗数据边界）= conservative / tightened from 37 to 33 (README + validation_checks leaks removed; only qualitative_facts INTERNAL_CLEAN_CANDIDATE rows remain)
```
