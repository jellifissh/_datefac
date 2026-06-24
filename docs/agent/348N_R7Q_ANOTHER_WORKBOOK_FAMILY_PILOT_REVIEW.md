## Task ID

`348N-R7Q Another Workbook Family Pilot Review`

## Input workbook

```text
input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
```

Source PDF:

```text
input/H3_AP202605231822706325_1.pdf
```

## Reviewed artifacts

Read-only review:

- `docs/agent/348N_R7P_FIX2_QA_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_REVIEW.md`
- `docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md`
- `docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md`
- `docs/agent/348N_R7P_ANOTHER_WORKBOOK_GUARDRAILS_PILOT_RESULT.md`
- `docs/agent/348N_R7_QUALITATIVE_FACTS_NARROW_CLEAN_ADMISSION_POLICY_DESIGN.md`
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json`
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv`
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/review_queue.csv`
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/evidence_index.json`

## Manifest summary

Post-FIX2 Taihao pilot manifest values:

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
market_reference_row_count = 2
normalized_testset_record_row_count = 0
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

The prior blocked guardrail failure (`MARKET_REFERENCE_ROW entered clean_data`) is gone.

## Clean/review split

```text
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
```

Interpretation:

- logical and physical counts now align one-to-one for both clean and review outputs on this workbook family;
- there is no hidden logical-vs-physical mismatch in this post-FIX2 pilot;
- the runner still returns `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX`, which in this case reflects explicit review pressure, not a guardrail failure or unknown-row collapse.

## Clean data boundary assessment

Conclusion: mixed / partly safe.

Positive findings:

- `clean_data.csv` contains **no forbidden row types**.
- Distribution is:

```text
row_type: STRICT_FINANCIAL_TABLE_ROW = 92
clean_candidate_type: INTERNAL_CLEAN_CANDIDATE = 92
evidence_level: WEAK_EVIDENCE = 92
forbidden_clean_row_type_found = no
```

So the immediate R7P guardrail failure is fixed.

However, the clean set is still not obviously "only clean financial metrics". Read-only inspection shows several rows inside `clean_data.csv` that look more like table section headers / comparison labels / mixed-support rows than stable metric facts, for example:

```text
核心盈利预测与估值,11,市场数据,...
行业赛道数据,13,厂商,...
行业赛道数据,19,对比维度,...
```

These are all typed as `STRICT_FINANCIAL_TABLE_ROW` and admitted as `INTERNAL_CLEAN_CANDIDATE` under the current weak-evidence strict-row policy. That means the market-reference leak is gone, but a different clean-data boundary question remains: **some pseudo-header / comparison-dimension rows in otherwise structured sheets may still be entering clean_data.**

## Review queue assessment

Review queue distribution from `review_queue.csv`:

```text
row_type:
- NARRATIVE_ASSERTION = 52
- MARKET_REFERENCE_ROW = 2
- STRICT_FINANCIAL_TABLE_ROW = 12

clean_candidate_type:
- NARRATIVE_REVIEW = 51
- REVIEW_REQUIRED = 14
- EXCLUDED_FROM_CLEAN_DATA = 1

evidence_level:
- WEAK_EVIDENCE = 66
```

Interpretation:

- Most review pressure is narrative and expected.
- The 2 `MARKET_REFERENCE_ROW` rows (`收盘价`, `总市值`) now correctly remain in review instead of leaking to clean.
- There are still 12 strict rows in review, which suggests some remaining unit/period/valuation/evidence ambiguity in structured sheets.
- There are **no high-confidence (`STRONG_EVIDENCE`) rows stuck in review_queue** in this workbook family; all rows in `evidence_index.json` are `WEAK_EVIDENCE`.

So `AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX` here means **expected review pressure under weak evidence**, not a new runner failure.

## Facts-like / qualitative-like observation

```text
facts_like_schema_found = no
qualitative_facts_like_rows = no dedicated qualitative_facts-like sheet observed
```

Detailed observation:

- This Taihao workbook does **not** expose a `qualitative_facts`-style facts schema like Linyang.
- There are no strongly-evidenced supporting rows (`TESTSET_SUPPORTING_ROW` + `STRONG_EVIDENCE`) and no separate facts-schema family comparable to Linyang's `qualitative_facts`.
- The workbook's supporting/narrative complexity instead appears through:
  - `报告核心信息与投资要点` narrative rows
  - `公司业务与产品矩阵`
  - `北美AIDC电力供需与技术路径`
- The new possible boundary issue is different from `qualitative_facts`: it is **strict-table over-admission of pseudo-header / dimension rows** inside structured sheets.

So this pilot does not strengthen the case for a `qualitative_facts` clean-admission policy change. Instead, it shifts attention toward stricter differentiation within `STRICT_FINANCIAL_TABLE_ROW` populations.

## Remaining risks

1. **Strict-table over-admission risk**
   - Some rows admitted to clean_data appear to be section labels, category rows, or table scaffolding rather than direct metric facts.
   - This is not a guardrail violation, but it may still be a semantic quality issue.

2. **All rows are still WEAK_EVIDENCE**
   - Even with the market-reference fix, the Taihao workbook remains entirely WEAK_EVIDENCE.
   - This is not a bug by itself, but it means clean-data trust still depends on conservative policy plus later human/QA interpretation.

3. **No second facts-like schema found**
   - This pilot does not provide evidence that `qualitative_facts`-style strongly-evidenced facts schemas recur across workbook families.
   - Therefore it does not justify broadening clean admission for facts-like sheets.

## Decision

`348N_R7Q_RECOMMENDS_FOCUSED_POLICY_DESIGN`

Rationale:

- The Taihao pilot is valid and the previous market-reference leak is fixed.
- But the workbook now reveals a different, narrower policy question: some rows currently admitted as `STRICT_FINANCIAL_TABLE_ROW` clean candidates look more like pseudo-headers / table-dimension rows than final clean facts.
- This is a more immediate and better-evidenced design question than opening another workbook-family pilot right away.
- The pilot does **not** reveal a second `qualitative_facts`-like schema, so it weakens the case for broadening facts-like clean admission now.

## Recommended next task

`348N-R7R strict_table pseudo-header / comparison-row clean-boundary design`

Suggested scope:

- review whether rows like `市场数据`, `厂商`, `对比维度` should remain `STRICT_FINANCIAL_TABLE_ROW` clean candidates;
- decide whether a narrower policy or structural row split is needed inside strict-table sheets;
- keep current output guardrails unchanged;
- do not broaden qualitative_facts admission until this simpler boundary question is settled.

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7Q_RECOMMENDS_FOCUSED_POLICY_DESIGN
input_workbook（输入 workbook）= input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
post_fix2_pilot_decision（FIX2 后 pilot decision）= AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count（逻辑 clean 行数）= 92
clean_data_csv_row_count（clean CSV 物理行数）= 92
review_queue_row_count（逻辑 review/non-clean 池行数）= 66
review_queue_csv_row_count（review_queue CSV 物理行数）= 66
unknown_row_count（UNKNOWN_ROW 逻辑计数）= 0
market_reference_row_count（market reference 行数）= 2
forbidden_clean_row_type_found（clean_data 是否仍有 forbidden row_type）= no
facts_like_schema_found（是否发现 facts-like schema）= no
qualitative_facts_like_rows（类似 qualitative_facts 行）= no dedicated qualitative_facts-like sheet observed
readiness_gates（就绪门）= unchanged / closed
code_changes_made（是否改代码）= no
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
recommended_next_task（推荐下一任务）= 348N-R7R strict_table pseudo-header / comparison-row clean-boundary design
```
