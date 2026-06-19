## Task ID

`348N-R5-QA Qualitative Facts Header Fix Review`

## Reviewed files and artifacts

Reviewed source (read-only; not modified by this QA):

- `datefac_agent/intake/excel_intake.py` (the R5 fix site)
- `datefac_agent/review/clean_candidate_policy.py` (confirmed NOT touched by R5)
- `datefac_agent/audit/evidence_checker.py` (evidence-level logic, context only)
- `datefac_agent/audit/row_type_classifier.py` (classifier, context only)
- `tests/agent/test_agent_excel_intake_audit_348a.py` (R5 new tests)
- `tools/run_agent_excel_intake_audit_348a.py` (runner, context only)

Reviewed git history:

- R5 commit `3c0e7ce` "fix: detect qualitative facts header in agent intake" — full diff inspected
- `clean_candidate_policy.py` last touched at `708148f` (R3), NOT in R5

Reviewed output artifacts (read-only, not committed):

- R5 pilot: `output/agent_excel_intake_audit_348n_r5_linyang_qualitative_facts_header_fix/` (`manifest`, `run_summary`, `clean_data.csv`, `evidence_index.json`, `review_queue.csv`)
- R3 baseline: `output/agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families/` (manifest, for delta)
- Source workbook (read-only): `input/linyang_energy_pdf_extracted_testset (1).xlsx`, sheet `qualitative_facts` raw rows
- Prior workbooks re-read via `read_excel_workbook` (read-only): anyi / H3 / taihao `input/*.xlsx`

Reviewed context docs: `AGENTS.md`, `.skills/*`, `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`, `docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md`, `docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md`, `docs/codex_tasks/348N_R5_qualitative_facts_header_detection_fix.md`.

## Implementation boundary QA

Conclusion: VALID.

- `git show --stat 3c0e7ce` shows exactly 3 files changed: `datefac_agent/intake/excel_intake.py` (+5), `tests/agent/test_agent_excel_intake_audit_348a.py` (+162), `docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md` (new). These are precisely the task's "Allowed changes".
- `clean_candidate_policy.py` is NOT in the commit. Independently confirmed: `git log -1 -- clean_candidate_policy.py` returns `708148f` (R3), and `findstr qualitative clean_candidate_policy.py` returns no match — there is no sheet-name special-casing of `qualitative_facts` anywhere in the policy.
- No `input/`, `output/`, `tools/`, legacy `datefac/`, or historical report files were touched.
- The R5 pilot output directory was generated but is NOT tracked/committed.

## Correct-layer QA

Conclusion: VALID (fix is at intake/header detection, not clean-candidate policy).

The R5 diff adds four things, all in `excel_intake.py`:

1. `QUALITATIVE_FACTS_HEADERS` constant (the real facts-schema header set).
2. `"qualitative_facts"` entry in `_find_special_header_row`'s `header_lookup` — so the real header is matched by `_matches_named_header` (subset match), before the generic `_is_header_candidate` can misfire.
3. `"qualitative_facts"` in `TESTSET_SUPPORTING_SHEETS` — routes to `TESTSET_SUPPORTING_ROW`.
4. A `qualitative_facts` branch in `_extract_special_metric_name` preferring `指标/事件`.

This is header-family detection, not a filename ban. It does not loosen `_is_header_candidate` for ordinary data rows — the named-header path only fires when the specific header set is present. Rows leave `clean_data` through the existing policy (`TESTSET_SUPPORTING_ROW -> REVIEW_REQUIRED`), exactly as R4 recommended. No policy masking.

## Header detection QA

Conclusion: VALID.

Independently verified against the REAL source workbook (not R5 fixtures):

- Raw row 1 = `['事实ID','页码','类别','主体','指标/事件','数值','单位','期间','摘录/说明','置信度']` (the real header).
- `_find_special_header_row("qualitative_facts", sheet_rows)` returns `(1, [...real header...])` — row 1 is detected as the header.
- `_is_header_candidate(row 1)` returns `False` (the real header has no period cells and `事实ID` is not in `HEADER_LABEL_HINTS`), confirming the generic path cannot recognize it.
- `_is_header_candidate(row 2 / F001)` returns `True` (because `1995` and `公司成立于1995年…` match `PERIOD_LABEL_RE`) — this reproduces the pre-R5 bug.
- Generic `_find_header_row(sheet_rows)` returns row 2 (F001) — confirming the old path WOULD still misfire, so the R5 special-header path is genuinely necessary.
- Post-R5, F001 is parsed as a data row (now counted in row_count_total), not as a header.
- All 10 real headers (`事实ID/页码/类别/主体/指标/事件/数值/单位/期间/摘录/说明/置信度`) are preserved as `column_names` for all 34 qualitative_facts rows.

## Evidence recovery QA

Conclusion: VALID.

- `页码` is preserved as a real column in all 34 rows (`all('页码' in r.column_names)` = True).
- `_extract_explicit_evidence_ref` on a real data row (页码 column value = 1) returns `'1'`.
- In the R5 `evidence_index.json`: `explicit_evidence_ref` is non-empty for 34/34 qualitative_facts rows (was 0/33 pre-R5).
- `evidence_level` for all 34 qualitative_facts rows = `STRONG_EVIDENCE` (was `WEAK_EVIDENCE`). The `classify_evidence_level` `has_explicit` branch fires because `explicit_evidence_ref` is now populated from `页码`.

## Clean-data boundary QA

Conclusion: VALID (boundary inversion corrected).

- `clean_data.csv` in the R5 pilot: 0 data rows (header only). `clean_data_row_count: 33 -> 0`.
- `review_queue_row_count: 455 -> 489` (+34), accounting for the 34 qualitative_facts rows moving into the review queue.
- All 34 qualitative_facts rows: `clean_candidate_type = REVIEW_REQUIRED` (via `TESTSET_SUPPORTING_ROW -> REVIEW_REQUIRED` in the unchanged policy).
- No qualitative_facts row appears in `clean_data.csv`.
- R4's boundary inversion is corrected: the previously-leaking weakest-evidenced sheet now joins the strongest-evidenced financial sheets in `review_queue`, and `clean_data` is empty for this workbook.
- Expected side effect (not a regression): `pass_count 419 -> 443` (+24) and `review_count 69 -> 46` (-23) because the 34 rows upgraded from WEAK (carrying a `weak_evidence` warning -> REVIEW) to STRONG (no evidence issue); 24 became PASS, 10 remain REVIEW for other reasons. `fail_count` stays 0.

## Regression QA

Conclusion: VALID (no regression).

Linyang workbook (R5 vs R3):

```text
unknown_row_count: 0 -> 0 (unchanged)
normalized_testset_record_row_count: 320 -> 320 (unchanged)
market_reference_row_count: 10 -> 10 (unchanged)
```

The five Linyang financial sheets retain correct behavior:

```text
income_statement    26 STRICT_FINANCIAL_TABLE_ROW, 26 STRONG_EVIDENCE, REVIEW_REQUIRED
balance_sheet       30 STRICT_FINANCIAL_TABLE_ROW, 30 STRONG_EVIDENCE, REVIEW_REQUIRED
cash_flow            7 STRICT_FINANCIAL_TABLE_ROW,  7 STRONG_EVIDENCE, REVIEW_REQUIRED
valuation_metrics    7 STRICT_FINANCIAL_TABLE_ROW,  7 STRONG_EVIDENCE, REVIEW_REQUIRED
earnings_forecast    6 STRICT_FINANCIAL_TABLE_ROW,  6 STRONG_EVIDENCE, REVIEW_REQUIRED
```

All retain page evidence (STRONG) and stay out of clean_data — unchanged from R3.

Other Linyang supporting sheets unchanged: README / data_dictionary / doc_metadata / figure_index / related_research / validation_checks all remain `TESTSET_SUPPORTING_ROW`.

Prior workbooks re-read via `read_excel_workbook` (none contain a `qualitative_facts` sheet, so the R5 named-header path cannot affect them):

```text
FIRST  (anyi):   82 rows, 0 UNKNOWN, row_type dist matches R4 baseline
SECOND (H3):    112 rows, 0 UNKNOWN, row_type dist matches R4 baseline
THIRD  (taihao): 158 rows, 0 UNKNOWN, row_type dist matches R4 baseline
```

The wide-workbook classification regression test (`test_normalized_testset_support_does_not_change_wide_workbook_classification`) still passes.

## Test adequacy QA

Conclusion: VALID (all 7 required boundaries covered).

Seven new deterministic unit tests (no external services, consistent with the existing `SpreadsheetRow`-based idiom):

| Required boundary | Test |
|---|---|
| real header detection | `test_qualitative_facts_real_chinese_header_is_detected_as_header` |
| F001 data row not selected as header | `test_qualitative_facts_f001_data_row_is_not_selected_as_header` |
| page column preservation | `test_qualitative_facts_page_column_is_preserved_in_parsed_row` |
| explicit evidence extraction | `test_qualitative_facts_explicit_evidence_ref_extracted_from_page_column` |
| metric extraction from 指标/事件 | `test_qualitative_facts_metric_name_prefers_indicator_over_fact_id` |
| STRONG + TESTSET_SUPPORTING + not clean | `test_qualitative_facts_rows_become_testset_supporting_and_stay_out_of_clean_data` |
| WEAK facts-schema rows do not enter clean | `test_qualitative_facts_weak_evidence_row_still_does_not_enter_clean_data` |

Coverage is complete against the task §7 checklist. The WEAK-row test is a good defensive case: it proves the routing keeps facts-schema rows out of clean_data even if page evidence is somehow absent (so the boundary does not depend solely on evidence strength).

## Validation result

```text
python -m py_compile datefac_agent\intake\excel_intake.py tests\agent\test_agent_excel_intake_audit_348a.py
  -> OK (compiled)

python -m pytest tests\agent -q
  -> 55 passed in 0.54s

git diff --check
  -> clean (no whitespace/conflict errors; QA task made no source changes)
```

The R5 pilot output directory already existed (generated by R5), so it was inspected read-only; no pilot rerun was needed and no new output was committed.

## External call QA

Conclusion: VALID (zero).

From R5 manifest:

```text
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
```

No VLM call paths exist. R5 diff added no external-service invocation.

## Readiness gate QA

Conclusion: VALID (closed).

From R5 manifest:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

No gate field was modified by R5.

## Decision

`348N_R5_QA_CONFIRMED_QUALITATIVE_FACTS_HEADER_FIX_VALID`

R5 is independently confirmed valid: the fix is at the intake/header-detection layer (not a clean-candidate-policy special-case), the real facts-schema header is recognized, F001 no longer masquerades as the header, `页码` evidence is recovered (0/33 -> 34/34), evidence upgrades WEAK -> STRONG, the 33 leaking rows leave `clean_data` (33 -> 0) via the existing policy, and no regression is observed (unknown=0, normalized=320, market=10, five financial sheets intact, prior workbooks intact, wide-workbook classification intact, 55 tests pass, gates closed, external calls zero).

## Recommended next task

- The deferred policy question from R4: whether any `qualitative_facts` rows should ever be clean candidates. Now that rows are correctly parsed as STRONG-evidenced facts (not a corrupted-WEAK artifact), a future task can design a narrow facts-sheet clean-admission rule (e.g. require `页码` + numeric `数值` + `单位` + `期间`) if the project wants any facts in clean_data. Until then the current conservative `REVIEW_REQUIRED` outcome is correct.
- No code action is needed before that policy decision.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R5_QA_CONFIRMED_QUALITATIVE_FACTS_HEADER_FIX_VALID
clean_data_row_count_before（修复前清洗数据行数）= 33
clean_data_row_count_after（修复后清洗数据行数）= 0
qualitative_facts_row_count（定性事实行数）= 34
qualitative_facts_explicit_ref_after（修复后显式证据引用）= 34 / 34
qualitative_facts_evidence_level_after（修复后证据级别）= STRONG_EVIDENCE
unknown_row_count（未知行数）= 0
normalized_testset_record_row_count（标准化测试集记录行数）= 320
market_reference_row_count（市场参考行数）= 10
pytest_result（测试结果）= 55 passed
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= closed
clean_data_boundary（清洗数据边界）= corrected — qualitative_facts now STRONG_EVIDENCE + TESTSET_SUPPORTING_ROW + REVIEW_REQUIRED; clean_data_row_count 33 -> 0; no regression
```
