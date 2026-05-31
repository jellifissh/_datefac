# 321B VLM Mapping Benchmark

## task_title
Map strict VLM table JSON outputs into DateFac sandbox MetricCandidates and compare against PPStructure row-text route

## project
D:\_datefac

## current_context
321A VLM quality gate was implemented and run twice.

Initial VLM output quality result:
- input: `E:\mineru_lab\vlm_table_outputs_321a`
- vlm_folder_count: 11
- parsed_json_count: 11
- table_ready_count: 0
- values_ok_labels_corrupted_count: 9
- corrupted_label_rate: 0.9356
- numeric_parse_success_rate: 1.0000
- global_vlm_quality_decision: VLM_OUTPUT_NOT_READY_LABEL_CORRUPTION

The user then reran the same 11 images with a stricter JSON prompt into:

```powershell
E:\mineru_lab\vlm_table_outputs_321a_rerun_strict
```

321A rerun quality result:
- output quality dir: `D:\_datefac\output\vlm_output_quality_321a_rerun_strict`
- vlm_folder_count: 11
- parsed_json_count: 11
- table_output_count: 11
- table_ready_count: 9
- values_ok_labels_corrupted_count: 0
- corrupted_label_rate: 0.0
- numeric_parse_success_rate: 1.0
- global_vlm_quality_decision: VLM_OUTPUT_READY_FOR_321B_MAPPING_BENCHMARK

Remaining two invalid tables:
- Their issue is not Chinese corruption.
- They are hierarchical/segment tables with natural missing columns / group header rows.
- Current 321A marks them as `ROW_MISSING_VALUES_FOR_COLUMNS`.
- Do not block 321B on these two tables. Treat them as schema_review_required or unsupported_for_now.

Engineering interpretation:
- VLM strict prompt solved the Chinese label corruption problem.
- VLM outputs are now ready for sandbox mapping benchmark.
- Do not return to deep PPStructure row-text repair unless VLM mapping quality fails.
- This stage must still be sandbox-only.

## goal
Implement 321B:

Strict VLM JSON outputs
-> normalized VLM table records
-> DateFac MetricCandidate records
-> metric/unit/year/value validation
-> trusted/review/rejected split
-> VLM sandbox delivery bundle
-> comparison against PPStructure row-text benchmark outputs

The output should answer:
- How many VLM tables can be mapped into useful candidates?
- How many trusted/review/rejected candidates are produced?
- Which metric families work best?
- How does VLM compare to the PPStructure row-text route from 320G?
- Is VLM ready to become the main recognizer for complex/core financial tables, or only a fallback?

## non_goals
Do not do these in 321B:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call AI/VLM/cloud/network APIs.
- Do not modify production Excel files.
- Do not apply data into `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.
- Do not claim production readiness.

## expected_new_or_modified_files
Suggested new files:
- `docs/codex_tasks/321b_vlm_mapping_benchmark.md`
- `datefac/vlm/vlm_candidate_mapper.py`
- `datefac/vlm/vlm_mapping_benchmark.py`
- `datefac/vlm/vlm_delivery_builder.py`
- `tools/run_vlm_mapping_benchmark_321b.py`

Potentially modify only if needed:
- `datefac/vlm/vlm_output_reader.py`
- `datefac/vlm/vlm_quality_gate.py`
- `datefac/domain/metric_candidate.py`
- `datefac/governance/risk_splitter.py`

Keep VLM logic separate from PPStructure row-text pipeline.

## input_contract
Primary VLM input:

```powershell
E:\mineru_lab\vlm_table_outputs_321a_rerun_strict
```

Primary quality gate input:

```powershell
D:\_datefac\output\vlm_output_quality_321a_rerun_strict
```

Optional comparison input:

```powershell
D:\_datefac\output\batch_row_text_delivery_320g
```

CLI:

```powershell
python tools/run_vlm_mapping_benchmark_321b.py ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321a_rerun_strict ^
  --quality-dir D:\_datefac\output\vlm_output_quality_321a_rerun_strict ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\vlm_mapping_benchmark_321b
```

If optional PPStructure benchmark dir is missing, continue and mark comparison as unavailable.
If VLM input dir is missing, produce blocked report:
- `BLOCKED_MISSING_VLM_OUTPUT_ROOT`

Do not crash.

## supported_vlm_schema
Support both schema variants from 321A:

- `row_name`
- `metric_name`
- `metric_name_raw`
- `metric_name_cn`

Value items may use:
- `column`
- `year`

Normalize these into common fields:
- table_id
- table_folder
- source_image_path
- table_title
- unit
- currency
- columns
- row_index
- raw_metric_name
- metric_name_cn
- year
- raw_value
- normalized_value
- confidence
- uncertain
- warnings

## mapping_requirements
Map VLM rows into DateFac metric candidates.

### Metric families to support
At minimum:
- cash_flow
- income_statement
- balance_sheet
- valuation
- profitability
- growth
- margin
- other

### Important metric aliases
Support Chinese aliases from current financial report tables, including but not limited to:

Cash flow:
- 经营活动现金流
- 净利润
- 折旧摊销
- 财务费用
- 营运资金变动 / 营运资本变动
- 投资活动现金流
- 资本支出 / 资本开支
- 长期投资
- 其他投资现金流 / 其它投资现金流
- 筹资活动现金流 / 融资活动现金流
- 短期借款
- 长期借款
- 普通股增加
- 资本公积增加
- 其他筹资现金流 / 其它融资现金流
- 现金净增加额 / 现金净变动
- 企业自由现金流
- 权益自由现金流

Income statement:
- 营业收入
- 营业成本
- 毛利润
- 毛利率
- 销售费用
- 管理费用
- 研发费用
- 财务费用
- 营业利润
- 利润总额
- 所得税费用
- 归属于母公司净利润 / 归母净利润
- 净利润

Balance sheet:
- 货币资金
- 应收账款
- 存货
- 流动资产合计
- 固定资产
- 无形资产
- 资产总计 / 资产总额
- 短期借款
- 应付账款
- 流动负债合计
- 长期借款
- 负债合计
- 股东权益
- 少数股东权益
- 负债和股东权益合计

Valuation / key metrics:
- 每股收益 / EPS
- 每股红利 / DPS
- 每股净资产 / BVPS
- ROE / 净资产收益率
- ROIC
- 毛利率
- EBIT Margin
- EBITDA Margin
- 收入增长
- 净利润增长率
- 资产负债率
- P/E / 市盈率
- P/B / 市净率
- EV/EBITDA

Unknown labels should not be discarded. Keep them as review-required with `UNKNOWN_METRIC_CODE`.

## unit_and_year_rules
Use VLM JSON context first:
- table-level `unit`
- row-level metric labels like `营业收入（百万元）`
- raw value percent signs
- table title such as `现金流量表（百万元）`

Rules:
- monetary statement tables with table unit `百万元` should propagate unit to monetary rows.
- valuation tables are mixed-unit; row-level unit or metric implication has priority.
- percentage metrics should use `%` when value or metric implies percentage.
- PE/PB/EV_EBITDA are ratio/unitless unless the row says otherwise.
- EPS/DPS/BVPS usually use `元` if stated or metric implies per-share CNY; if not stated, mark `UNIT_INFERRED_PER_SHARE` not fatal.

Years:
- preserve suffixes: `2024A`, `2025A`, `2026E`, `2027E`, `2028E`.
- also support `2024`, `2025` etc.
- invalid year -> review_required.

## trust_split_rules
This is sandbox preview.

Trusted allowed if:
- source VLM table passed 321A quality gate;
- known metric code;
- valid year;
- normalized value exists;
- label is not corrupted;
- no conflict within same table/metric/year;
- unit is known or safely inferred for ratio/per-share metrics;
- row confidence >= 0.80 if available;
- no `uncertain = true` on the row/value.

Review required if:
- unknown metric code;
- schema invalid table but values are still parseable;
- row confidence low or uncertain;
- mixed-unit valuation row with unclear unit;
- missing value;
- duplicate/conflict inside same table;
- hierarchical/segment table with missing columns.

Rejected if:
- non-table output;
- corrupted labels;
- invalid JSON/table schema severe enough to prevent candidate creation;
- meaningless value.

## comparison_against_ppstructure
If `D:\_datefac\output\batch_row_text_delivery_320g` exists, compare high-level metrics:
- parsed_table_count
- table_with_candidates_count
- table_with_trusted_count
- trusted_total_count
- review_required_total_count
- trusted_rate
- unit_unknown_count
- year_inferred_count
- conflict_count
- provenance_complete_rate

Create sheet:
- `vlm_vs_ppstructure_summary`

Columns:
- metric_name
- vlm_value
- ppstructure_value
- winner
- notes

Expected comparison logic:
- higher parsed table count is better;
- higher table_with_candidates_count is better;
- higher trusted_total_count/trusted_rate is better only if QA passes;
- lower unit_unknown/year_inferred/conflict is better;
- provenance completeness should remain high.

Do not pretend this is a perfect apples-to-apples benchmark. VLM samples were manually generated, PPStructure outputs were local OCR outputs. Note this limitation.

## output_contract
Write to:

```powershell
D:\_datefac\output\vlm_mapping_benchmark_321b
```

Required files:

1. `vlm_mapping_benchmark_321b.xlsx`

Sheets:
- `summary`
- `vlm_table_inventory`
- `vlm_rows_normalized`
- `metric_candidates_all`
- `trusted_preview`
- `review_required_preview`
- `rejected_preview`
- `per_table_summary`
- `per_report_summary`
- `metric_coverage`
- `unit_year_context_summary`
- `risk_tag_counts`
- `provenance_coverage`
- `qa_checks`
- `vlm_vs_ppstructure_summary`
- `known_limitations`

2. `vlm_mapping_benchmark_321b_summary.json`

3. `vlm_mapping_benchmark_321b_report.md`

Optional:
- `metric_candidates_all.jsonl`
- `trusted_preview.jsonl`
- `review_required_preview.jsonl`

## qa_checks
Required QA checks:
- no corrupted labels in trusted output;
- no invalid year in trusted output;
- no unknown metric code in trusted output;
- no missing normalized value in trusted output;
- no conflict in trusted output;
- provenance complete for trusted output;
- table_ready_count from 321A matches or is explained;
- schema-invalid segment tables are not silently trusted;
- Chinese text preserved.

## summary_metrics
Include:
- vlm_folder_count
- parsed_json_count
- table_ready_count
- mapped_table_count
- table_with_candidates_count
- table_with_trusted_count
- total_candidate_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- unique_metric_count
- unique_year_count
- unique_report_count
- unit_unknown_count
- year_inferred_count
- conflict_count
- corrupted_label_candidate_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- ppstructure_comparison_available
- vlm_benchmark_decision

Decision rule:
- If qa_fail_count > 0:
  `VLM_MAPPING_BLOCKED_BY_QA_FAILURE`
- If corrupted_label_candidate_count > 0:
  `VLM_MAPPING_BLOCKED_BY_LABEL_CORRUPTION`
- If mapped_table_count >= 9, table_with_trusted_count >= 7, trusted_rate >= 0.60, provenance_complete_rate >= 0.95, and qa_fail_count == 0:
  `VLM_MAPPING_READY_FOR_321C_RECOGNIZER_ROUTER_PLAN`
- If mapped_table_count >= 7 and table_with_candidates_count >= 7 and qa_fail_count == 0:
  `VLM_MAPPING_PARTIAL_NEEDS_ALIAS_OR_SCHEMA_CALIBRATION`
- Otherwise:
  `VLM_MAPPING_NOT_READY`

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call AI/VLM/cloud/network APIs.
4. Do not modify production delivery files:
   - `01_自动可信核心指标.xlsx`
   - `02_人工复核指标队列.xlsx`
   - `02A_人工年份修正覆盖表.xlsx`
   - `05_核心财务指标标准化.xlsx`
   - `06_最终核心财务指标.xlsx`
5. Do not modify:
   - `data/overrides/02B_ai_repair_override.xlsx`
   - `data/mapping/formal_scope_rules.json`
6. Do not run `factory_core.py`.
7. Do not rewrite old Stage7 pipeline.
8. Do not commit `output/` artifacts.
9. Do not commit anything under `E:\mineru_lab`.
10. Preserve Chinese text as UTF-8. No `????` in generated data except in explicit corruption detection tests/docs.

## validation
Run:

```powershell
python -m py_compile datefac/vlm/vlm_candidate_mapper.py
python -m py_compile datefac/vlm/vlm_mapping_benchmark.py
python -m py_compile datefac/vlm/vlm_delivery_builder.py
python -m py_compile tools/run_vlm_mapping_benchmark_321b.py
```

Then run:

```powershell
python tools/run_vlm_mapping_benchmark_321b.py ^
  --vlm-output-root E:\mineru_lab\vlm_table_outputs_321a_rerun_strict ^
  --quality-dir D:\_datefac\output\vlm_output_quality_321a_rerun_strict ^
  --ppstructure-benchmark-dir D:\_datefac\output\batch_row_text_delivery_320g ^
  --output-dir D:\_datefac\output\vlm_mapping_benchmark_321b
```

If optional comparison input is missing, continue and report comparison unavailable.

## commit_requirements
After implementation:
1. `git status`
2. only add 321B code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
   - uncommitted 320G2 experimental files unless they are explicitly required for 321B, which they should not be.
6. commit message:
   `Benchmark VLM table mapping`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- vlm_folder_count
- parsed_json_count
- table_ready_count
- mapped_table_count
- table_with_candidates_count
- table_with_trusted_count
- total_candidate_count
- trusted_total_count
- review_required_total_count
- rejected_total_count
- trusted_rate
- unit_unknown_count
- year_inferred_count
- conflict_count
- provenance_complete_rate
- qa_pass_count
- qa_warn_count
- qa_fail_count
- ppstructure_comparison_available
- vlm_benchmark_decision
- top risk tags
- skipped/untracked files
