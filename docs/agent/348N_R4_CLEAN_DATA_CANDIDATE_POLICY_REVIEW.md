## Task ID

`348N-R4 Clean Data Candidate Policy Review`

## Reviewed files and output artifacts

Reviewed source (read-only, not modified):

- `datefac_agent/intake/excel_intake.py` (header detection + evidence extraction + special-schema routing)
- `datefac_agent/review/clean_candidate_policy.py` (clean candidate classification)
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/schemas/audit_models.py`
- `tools/run_agent_excel_intake_audit_348a.py`

Reviewed output artifacts (read-only, not modified or committed):

- R3 (current): `output/agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families/`
  - `clean_data.csv`, `evidence_index.json`, `agent_excel_intake_audit_348a_manifest.json`, `agent_excel_intake_audit_348a_run_summary.json`, `audit_report.md`
- R2 baseline (linyang): `output/agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema/`
- Prior workbooks for evidence-strength comparison:
  - first workbook (anyi food): `output/agent_excel_intake_audit_348a_r4/clean_data.csv`
  - second workbook (H3): `output/agent_excel_intake_audit_348s_r2_h3_ap202605231822706325_1/clean_data.csv`
  - third workbook (taihao): `output/agent_excel_intake_audit_348s_r3c_third_taihao_keji_doubaoai/clean_data.csv`
- Source workbook (read-only): `input/linyang_energy_pdf_extracted_testset (1).xlsx`, sheet `qualitative_facts`

Reviewed context docs: `AGENTS.md`, `.skills/*`, `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`, `项目进展大白话说明.md`, `docs/agent/348N_R3_QA_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_REVIEW.md`, `docs/agent/348N_R3_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_RESULT.md`.

## Clean-data composition

R3 `clean_data.csv` has exactly 33 rows. All 33 are:

```text
sheet_name            = qualitative_facts
row_type              = STRICT_FINANCIAL_TABLE_ROW
clean_candidate_type  = INTERNAL_CLEAN_CANDIDATE
evidence_level        = WEAK_EVIDENCE
decision              = REVIEW
explicit_evidence_ref = (none, 0/33)
```

No other sheet appears in `clean_data.csv`. The manifest confirms `clean_data_row_count = 33 = internal_clean_candidate_count(33) + internal_reference_candidate_count(0)`.

## Qualitative-facts row analysis

The 33 rows are `F002` through `F034` (row indices 3-35) of the `qualitative_facts` sheet. By business meaning they are a mix:

```text
performance facts (numeric, value+unit+period)   ~25 rows  (F003-F011, F013-F018, F022-F031)
   revenue / net profit / gross margin / expense / cash flow / capacity utilization, with 亿元 / % / GW / MW/MWh / GWh
segment / project facts (qualitative-ish)        ~3 rows   (F002 business layout, F012 project revenue timing, F019-F021 order/产能 scale)
earnings forecast (expectation values)           ~2 rows   (F032-F033 2026-2028 归母净利润预期)
risk disclaimer (pure narrative text)            ~1 row    (F034 风险提示)
```

So most rows (~30) are real financial/operating facts with a value, unit, and period embedded in the cell text. They are not testset labels or field-dictionary entries. By raw content they are broadly comparable to the strict financial rows of prior workbooks.

However, their structure inside the audit pipeline is broken (see next section).

## Evidence and structure assessment

### Structural break: header mis-detection

The source `qualitative_facts` sheet has a legitimate Chinese header on row 1:

```text
['事实ID', '页码', '类别', '主体', '指标/事件', '数值', '单位', '期间', '摘录/说明', '置信度']
```

`_is_header_candidate` (in `excel_intake.py`) did NOT recognize this header:
- `事实ID` is not in `HEADER_LABEL_HINTS` (which targets 财务宽表 words like 项目/指标/会计年度).
- The header has no period-style cells, so `period_hits = 0`, failing both the `>=2` and the `>=1 with >=3 non-empty` thresholds.
- Result: the true header was skipped.

The function then accepted row 2 (`F001`) as the header, because `F001`'s cells contain `1995` and `公司成立于1995年…`, both of which match `PERIOD_LABEL_RE` (`\d{2}` inside `1995`), giving `period_hits = 2 >= 2`.

This is verifiable: testing `_is_header_candidate` directly returns `False` for the true header row and `True` for the F001 data row.

### Consequences of the header break

1. **Column names are shifted.** Every data row's `raw_values` keys are the F001 cell values (`F001`, `1`, `业务概况`, `林洋能源`, `成立时间`, `1995`, `年`, `column_8`, `公司成立于1995年…`, `高`), not the real schema (`事实ID`, `页码`, …). The real schema is lost.
2. **Page evidence is lost.** The real `页码` column (value = 1 for F002-F034) cannot be matched by `_extract_explicit_evidence_ref`, because `EVIDENCE_HEADER_HINTS` (`页`/`page`/`evidence`/…) is matched against `header_names`, and `页码` is no longer a header name. So `explicit_evidence_ref = None` for all 33 rows.
3. **Evidence downgrades to WEAK.** Without an explicit evidence ref, `audit_evidence_presence` returns `WEAK_EVIDENCE` (a workbook row with sheet+index but no page number).
4. **Period labels are corrupted.** `period_labels` becomes `1995;公司成立于1995年…` for every row, because `1995` (a data value in the mis-named column) matches `PERIOD_LABEL_RE`. The real `期间` column (e.g. `2025`, `2022-2024`, `2026Q1`) is buried under a wrong key and not harvested.
5. **STRICT_FINANCIAL_TABLE_ROW still fires** via other heuristics, and with no unit/period/valuation issue raised (the checkers run on the shifted structure), the clean-candidate policy reaches the `STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + no unit/period/valuation issue` branch and returns `INTERNAL_CLEAN_CANDIDATE`.

So the 33 rows entered `clean_data` not because their evidence or structure justified it, but because a header-detection bug silently destroyed both their column schema and their page evidence, and the resulting `WEAK_EVIDENCE` happened to be exactly the policy gate that admits strict rows into clean data.

### Cross-sheet comparison within the same linyang workbook

This is the strongest single piece of evidence. In the same R3 run, the five real financial sheets were parsed correctly and behave oppositely:

```text
sheet              row_type              evidence        explicit_ref   clean_candidate
income_statement   STRICT_FINANCIAL      STRONG (26/26)  26/26          REVIEW_REQUIRED
balance_sheet      STRICT_FINANCIAL      STRONG (30/30)  30/30          REVIEW_REQUIRED
cash_flow          STRICT_FINANCIAL      STRONG (7/7)    7/7            REVIEW_REQUIRED
valuation_metrics  STRICT_FINANCIAL      STRONG (7/7)    7/7            REVIEW_REQUIRED
earnings_forecast  STRICT_FINANCIAL      STRONG (6/6)    6/6            REVIEW_REQUIRED
qualitative_facts  STRICT_FINANCIAL      WEAK (33/33)    0/33           INTERNAL_CLEAN_CANDIDATE  <-- only outlier
```

The other five sheets have correct headers (`科目层级/项目/单位/2025A/…/来源页`), retain their `来源页` evidence, and are `STRONG_EVIDENCE`. Because they are `STRONG` (not `WEAK`), the policy returns `REVIEW_REQUIRED` at `clean_candidate_policy.py:34` and they stay out of clean data.

`qualitative_facts` is the only sheet that is `WEAK_EVIDENCE` with zero explicit refs, and it is the only sheet in clean data. This is an inverted boundary: the cleanest-evidenced rows are excluded, and the most structurally damaged rows are admitted.

### Comparison with prior workbooks

All three prior workbooks' clean_data rows are also `WEAK_EVIDENCE`:

```text
first  (anyi)   75 rows, all WEAK_EVIDENCE, sheets = 资产负债表/利润表/现金流量表/财务估值/市场与基础数据
second (H3)     94 rows, all WEAK_EVIDENCE, sheets = 利润表/资产负债表/现金流量表/盈利预测与估值/...
third  (taihao) 94 rows, all WEAK_EVIDENCE, sheets = 三大财务报表与核心指标/行业赛道数据/...
```

So `WEAK_EVIDENCE -> INTERNAL_CLEAN_CANDIDATE` for strict rows is the project's long-standing design, not a linyang-specific loosening. The policy itself is consistent. The difference is that prior workbooks' clean rows had correctly-detected headers and real period structures (e.g. taihao shows `2024A;2025A;2026E;2027E;2028E`), whereas linyang `qualitative_facts` has corrupted headers and fake period labels (`1995;公司成立于1995年…`).

Conclusion: this is not a policy-classification problem. It is an intake-layer header-detection defect that, as a side effect, both (a) destroyed the evidence/structure of 33 rows and (b) routed exactly those damaged rows into clean_data via the WEAK_EVIDENCE gate.

## Business risk assessment

Keeping these 33 rows in `clean_data` creates real risk:

1. **Inverted trust signal.** `clean_data` is meant to be the conservative, higher-trust subset. Here it contains the only sheet in the workbook with zero page evidence and broken columns, while every fully-evidenced financial sheet sits in `review_queue`. A downstream consumer would trust the least-traceable rows most.
2. **Corrupted fields shipped as clean.** `period_labels` and `period_values_json` in `clean_data.csv` for all 33 rows are the fake `1995;公司成立于1995年…` value. Any downstream use of period alignment would ingest garbage.
3. **Lost page lineage.** The real `页码 = 1` evidence exists in the source but is not carried through; clean_data promises traceability it cannot deliver for these rows.
4. **Mixed content.** Even if the header were fixed, `F034` (risk disclaimer) and arguably `F002`/`F012` are narrative/qualitative, not financial facts; admitting the whole sheet wholesale blurs the clean-data boundary.
5. **No regression protection yet.** There is no test asserting that a facts-schema sheet with a non-宽表 Chinese header is detected as a header, so this can silently recur on the next testset-style workbook.

Mitigating observation: gates are closed (`client_ready=false`, etc.) and `demo_export_only=true`, so no external delivery is exposed. The risk is contained to internal pilot artifacts for now, but it should be fixed before any clean-data consumer is wired up.

## Policy recommendation

Recommendation: **the 33 `qualitative_facts` rows should NOT remain in `clean_data` in their current state**, and the fix is an intake-layer change, not a clean-candidate-policy loosening/tightening.

Specifically:

1. **Primary fix (intake):** make `_find_header_row` / `_is_header_candidate` recognize the `qualitative_facts` facts-schema header. Either add a named-header path for `qualitative_facts` (like the existing `_find_special_header_row` for `data_dictionary`/`doc_metadata`/`figure_index`/`related_research`/`market_base_data`) keyed on its real header set `{事实ID, 页码, 类别, 主体, 指标/事件, 数值, 单位, 期间, 摘录/说明, 置信度}`, or broaden `_is_header_candidate` to accept a row whose first cell is an ID-like header (`事实ID`) plus several known semantic headers (`页码`/`单位`/`期间`/`置信度`).
2. **Expected effect of the fix:** the `页码` column is restored as a header, `_extract_explicit_evidence_ref` matches `页码`, the 33 rows gain `explicit_evidence_ref = 1`, evidence becomes `STRONG_EVIDENCE`, and the policy returns `REVIEW_REQUIRED` (same as the other five financial sheets). They leave `clean_data` and join `review_queue`. `clean_data_row_count` would drop from 33 to 0 for this workbook, which is the correct conservative outcome until a deliberate clean-admission policy for facts sheets is designed.
3. **Secondary policy question (separate task, not now):** whether any `qualitative_facts` rows should ever be clean candidates. Given ~30 are real financial facts, a future task could design a narrow facts-sheet clean-admission rule (e.g. require `页码` + numeric `数值` + `单位` + `期间`), but that must be a deliberate implementation task with tests, not a side effect of a bug.
4. **Do not** simply tighten `clean_candidate_policy` to exclude `qualitative_facts` by sheet name. That would mask the intake bug and leave the corrupted headers/evidence in place for every other consumer of `evidence_index.json`.

## Whether implementation is needed

Yes. This review recommends a follow-up **implementation** task (not done here, this is diagnosis-only):

```text
348N-R5 qualitative_facts facts-schema header detection fix
```

Scope of that future task: add `qualitative_facts` named-header detection in `excel_intake.py`, add regression tests asserting (a) the real header is detected, (b) `页码` evidence is extracted, (c) evidence becomes STRONG, (d) rows leave clean_data, (e) the five other linyang financial sheets and prior workbooks do not regress. That task must re-run the pilot and confirm `clean_data_row_count` drops appropriately and `review_queue_row_count` grows correspondingly.

This R4 task itself makes no code/test/output changes.

## Validation result

- `git pull --ff-only origin pivot/348-agent-foundation` -> `Already up to date` (fast-forwarded `08dd985..4627759` first, bringing in the R4 task doc and handoff update).
- `git status -sb` before editing -> clean (`## pivot/348-agent-foundation...origin/pivot/348-agent-foundation`).
- `git diff --check` -> no output (no whitespace errors, no conflict markers).
- No pytest required (no code/tests changed); no code or tests were touched.
- All diagnosis used read-only inspection of output artifacts and the source workbook; no output files were modified or committed.

## Decision

`348N_R4_RECOMMENDS_QUALITATIVE_FACTS_REVIEW_ONLY_IMPLEMENTATION`

Rationale: the 33 rows should move to review-only, but the correct mechanism is an intake header-detection fix (restoring `页码` evidence so they become STRONG_EVIDENCE and naturally fall out of clean_data via the existing policy), not a clean-candidate-policy edit. A pure policy change would hide the underlying intake defect.

## Recommended next task

```text
348N-R5 qualitative_facts facts-schema header detection fix
```

An implementation task: detect the `qualitative_facts` header explicitly, restore `页码` evidence extraction, add regression tests, re-run the linyang pilot, and confirm the 33 rows leave `clean_data` (expected `clean_data_row_count: 33 -> 0` for this workbook) while the five other financial sheets and prior workbooks do not regress.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R4_RECOMMENDS_QUALITATIVE_FACTS_REVIEW_ONLY_IMPLEMENTATION
clean_data_row_count（清洗数据行数）= 33 (all qualitative_facts, all WEAK_EVIDENCE, 0/33 with page evidence)
qualitative_facts_row_count（定性事实行数）= 33
qualitative_facts_evidence_level（定性事实证据级别）= WEAK_EVIDENCE (root cause: header mis-detection lost 页码 column)
qualitative_facts_explicit_ref（定性事实显式证据引用）= 0 / 33
other_financial_sheets_evidence（其他财务表证据级别）= STRONG_EVIDENCE (income_statement/balance_sheet/cash_flow/valuation_metrics/earnings_forecast, 76/76 with page evidence)
prior_workbooks_clean_evidence（历史 workbook 清洗行证据）= all WEAK_EVIDENCE (policy design, not a defect)
header_detection_root_cause（表头检测根因）= _is_header_candidate skipped the real 事实ID/页码/... header and accepted the F001 data row (1995 matched PERIOD_LABEL_RE)
implementation_needed（是否需要实现修复）= yes, follow-up 348N-R5 intake header fix
pytest_result（测试结果）= not run (diagnosis-only, no code/tests changed)
LLM / MinerU / OCR calls（外部调用次数）= 0
clean_data_boundary（清洗数据边界）= inverted for qualitative_facts — weakest-evidenced sheet admitted while strongest-evidenced sheets excluded; fix via intake, not policy
```
