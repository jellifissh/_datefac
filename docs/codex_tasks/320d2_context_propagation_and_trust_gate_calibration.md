# 320D2 Context Propagation and Trust Gate Calibration

## task_title
Propagate table context into row-text metric candidates and calibrate sandbox trusted/review split

## project
D:\_datefac

## current_context
320D mapped calibrated row-text candidates into a sandbox MetricCandidate schema and produced a risk split preview.

Latest 320D result:
- pushed branch: main
- commit hash: ef839e1
- source_candidate_count: 100
- normalized_candidate_count: 100
- trusted_preview_count: 0
- review_required_preview_count: 100
- rejected_preview_count: 0
- duplicate_same_value_count: 0
- conflict_count: 0
- unknown_metric_code_count: 0
- unit_unknown_count: 95
- sandbox_mapping_decision: ROW_TEXT_MAPPING_USABLE_NEEDS_REVIEW_GATE

Top risk tags:
- ROW_TEXT_ONLY: 100
- YEAR_INFERRED: 100
- UNIT_UNKNOWN: 95
- NEGATIVE_PARENTHESES: 23
- ROW_REPAIRED_VALUES_BEFORE_LABEL: 20
- ROW_REPAIRED_CONTINUATION: 10

Engineering interpretation:
320D did not fail. It proved candidates can be normalized without duplicates, conflicts, unknown metrics, or rejects. However, the trust gate is currently too conservative because context is not being propagated:
1. `YEAR_INFERRED` is attached to all candidates even though the known table header explicitly contains 2024, 2025, 2026E, 2027E, 2028E.
2. `UNIT_UNKNOWN` is attached to 95 candidates even though the table title is `现金流量表（百万元）`.
3. `ROW_TEXT_ONLY` blocks all candidates even when rows were smoke-verified in 320C4.
4. Repaired rows are all treated as risky even if the 320C4 expected-vs-actual smoke check passed.

Do not proceed to production integration. First calibrate sandbox context propagation and trust split.

## goal
Implement 320D2:

320D normalized candidates
+ 320C4 context/smoke-check artifacts
-> context-enriched MetricCandidates
-> calibrated trusted_preview/review_required_preview/rejected_preview
-> audit sheets explaining why each candidate is trusted or still review-required.

The goal is not to blindly trust everything. The goal is to correctly move smoke-verified, conflict-free, context-complete candidates into `trusted_preview`, while keeping genuinely ambiguous rows in `review_required_preview`.

Still sandbox-only.

## non_goals
Do not do these in 320D2:
- Do not run MinerU.
- Do not run PaddleOCR/PPStructure.
- Do not call LLM/VLM/cloud API/network.
- Do not modify production Excel files.
- Do not apply data to `06_最终核心财务指标.xlsx`.
- Do not alter official override/mapping files.
- Do not rewrite old Stage7 pipeline.

## expected_new_or_modified_files
Likely modified:
- `datefac/governance/row_text_candidate_mapper.py`
- `datefac/governance/risk_splitter.py`
- `tools/run_row_text_candidates_to_sandbox_mapping_320d.py`

Suggested new files if cleaner:
- `datefac/governance/context_propagation.py`
- `datefac/governance/smoke_verification_loader.py`
- `datefac/governance/trust_gate_audit.py`
- `docs/codex_tasks/320d2_context_propagation_and_trust_gate_calibration.md`

Do not create a giant unmaintainable script. Keep mapping, context propagation, and split logic modular.

## input_contract
Primary input directories:

```powershell
D:\_datefac\output\legacy_ppstructure_row_text_320c4
D:\_datefac\output\row_text_mapping_320d
```

The CLI should support:

```powershell
python tools/run_row_text_candidates_to_sandbox_mapping_320d.py ^
  --input-dir D:\_datefac\output\legacy_ppstructure_row_text_320c4 ^
  --previous-mapping-dir D:\_datefac\output\row_text_mapping_320d ^
  --output-dir D:\_datefac\output\row_text_mapping_320d2
```

If `--previous-mapping-dir` is not implemented, rerun from 320C4 input but still produce 320D2 outputs. Keep backward compatibility with existing 320D usage if practical.

If input is missing, generate a clear blocked report:
- `BLOCKED_MISSING_320C4_INPUT`
- or `BLOCKED_MISSING_320D_INPUT`

Do not crash.

## context_propagation_requirements
Implement a context propagation layer.

### Table title and unit
Extract table title/header context from 320C4 artifacts if available:
- `cleaned_row_texts`
- `repaired_rows`
- `expected_vs_actual_matrix`
- `source_files`
- candidate source row text fields

For the known cash-flow table:
- Title: `现金流量表（百万元）`
- Unit: `百万元`
- Apply `unit = 百万元` to cash-flow monetary metrics unless row-specific unit overrides exist.
- `unit_source = TABLE_TITLE`

If unit is inferred only from table title, this is acceptable for sandbox trusted preview, but preserve provenance.

Do not assign `百万元` to percentage metrics such as ROE, gross margin, debt ratio. For percentage rows, use `%` if raw value includes `%` or metric code implies percent and source value is percent-like.

### Years
If the source table/header or 320C4 smoke check explicitly identifies years:
- 2024
- 2025
- 2026E
- 2027E
- 2028E

then remove or downgrade `YEAR_INFERRED` for candidates aligned to this header.

Add:
- `year_source = TABLE_HEADER` when years came from actual row/table context.
- `year_source = SMOKE_CHECK_CONTEXT` only if table header is not directly available but 320C4 smoke check validates the row.
- `year_source = INFERRED_SEQUENCE` only when no source/header evidence exists.

Candidates with `year_source = TABLE_HEADER` or `SMOKE_CHECK_CONTEXT` should not carry `YEAR_INFERRED` as a blocking risk tag.

### Smoke verification
Load 320C4 `expected_vs_actual_matrix` if present.

A metric_code is smoke-verified if:
- pass_fail is pass/true, or equivalent;
- actual values match expected values for all available years.

Add candidate-level tag:
- `SMOKE_VERIFIED_ROW`

For each candidate in a smoke-verified metric row:
- attach `smoke_check_status = PASSED`
- attach `smoke_check_source = 320C4_EXPECTED_VS_ACTUAL`

If a metric row failed smoke check:
- attach `SMOKE_CHECK_FAILED` and keep review_required_preview.

## risk_split_calibration
Revise risk split logic.

### trusted_preview allowed if all conditions hold
A candidate may enter `trusted_preview` if:
- metric_code is known;
- year is valid;
- normalized_value is not None;
- conflict_count for candidate key is zero;
- duplicate disagreement is zero;
- no bbox/html/noise risk tag;
- unit is known OR metric is unitless/ratio/percentage;
- year_source is TABLE_HEADER or SMOKE_CHECK_CONTEXT;
- smoke_check_status is PASSED for repaired row candidates;
- confidence >= 0.80 if confidence exists.

`ROW_TEXT_ONLY` alone must not block trusted_preview if the candidate is smoke-verified and context-complete. Row-text is the recognizer mode, not automatically a fatal risk.

`ROW_REPAIRED_CONTINUATION` and `ROW_REPAIRED_VALUES_BEFORE_LABEL` should not block trusted_preview if smoke_check_status is PASSED and there are no mismatches/conflicts.

### review_required_preview if any condition holds
- generic `其它` metrics unless smoke-verified and disambiguated by cash-flow section;
- unit unknown for monetary metrics;
- year still inferred from sequence only;
- medium/low confidence;
- repaired row without smoke verification;
- negative value in a metric where negative is unusual and not expected from source context;
- any ambiguous repair tag not resolved by smoke verification.

### rejected_preview if any condition holds
- noise-derived candidate leaked from bbox/html/raw metadata;
- invalid year not repairable;
- missing/None value with meaningless raw value;
- unknown metric code with no safe fallback.

## expected_improvements
Given 320D had:
- trusted_preview_count = 0
- review_required_preview_count = 100
- unit_unknown_count = 95
- YEAR_INFERRED = 100

320D2 should aim for:
- unit_unknown_count substantially reduced for cash-flow rows;
- YEAR_INFERRED substantially reduced or replaced by TABLE_HEADER/SMOKE_CHECK_CONTEXT;
- trusted_preview_count > 0;
- no increase in conflicts or rejects;
- known smoke-verified critical rows should mostly move to trusted_preview.

Do not force all 100 candidates into trusted. That would be dumb, and software already has enough ways to be dumb without our help.

## output_contract
Write to:

```powershell
D:\_datefac\output\row_text_mapping_320d2
```

Required files:

1. `row_text_mapping_320d2.xlsx`
   Sheets:
   - `summary`
   - `context_enriched_candidates`
   - `trusted_preview`
   - `review_required_preview`
   - `rejected_preview`
   - `context_propagation_audit`
   - `trust_gate_audit`
   - `smoke_verified_candidates`
   - `duplicates`
   - `conflicts`
   - `risk_tag_counts`
   - `metric_counts`
   - `source_candidate_rows`
   - `mapping_audit`

2. `row_text_mapping_320d2_summary.json`

3. `row_text_mapping_320d2_report.md`

Optional:
- `context_enriched_candidates.jsonl`
- `trusted_preview.jsonl`
- `review_required_preview.jsonl`

## summary_metrics
Include:
- source_candidate_count
- context_enriched_candidate_count
- trusted_preview_count
- review_required_preview_count
- rejected_preview_count
- duplicate_same_value_count
- conflict_count
- unknown_metric_code_count
- invalid_year_count
- value_missing_count
- unit_unknown_count
- year_inferred_count
- table_header_year_count
- smoke_context_year_count
- smoke_verified_candidate_count
- row_text_only_trusted_count
- repaired_trusted_count
- sandbox_mapping_decision

Decision rule:
- If any bbox/html/noise candidate reaches context_enriched candidates:
  `MAPPING_FAILED_NOISE_LEAK`
- If conflict_count > 0:
  `MAPPING_READY_WITH_REVIEW_REQUIRED_CONFLICTS`
- If context_enriched_candidate_count >= 50, trusted_preview_count >= 50, rejected_preview_count == 0, and conflict_count == 0:
  `ROW_TEXT_MAPPING_READY_FOR_320E_SANDBOX_INTEGRATION`
- If trusted_preview_count > 0 and review_required_preview_count > 0:
  `ROW_TEXT_MAPPING_TRUST_GATE_CALIBRATED_NEEDS_REVIEW_QUEUE`
- Otherwise:
  `ROW_TEXT_MAPPING_CONTEXT_PROPAGATION_NOT_READY`

## validation
Run:

```powershell
python -m py_compile datefac/governance/row_text_candidate_mapper.py
python -m py_compile datefac/governance/risk_splitter.py
```

If new files are added:

```powershell
python -m py_compile datefac/governance/context_propagation.py
python -m py_compile datefac/governance/smoke_verification_loader.py
python -m py_compile datefac/governance/trust_gate_audit.py
```

Then run:

```powershell
python tools/run_row_text_candidates_to_sandbox_mapping_320d.py ^
  --input-dir D:\_datefac\output\legacy_ppstructure_row_text_320c4 ^
  --previous-mapping-dir D:\_datefac\output\row_text_mapping_320d ^
  --output-dir D:\_datefac\output\row_text_mapping_320d2
```

If `--previous-mapping-dir` is not supported, run an equivalent command and document it in the final response.

## safety_constraints
Absolute constraints:
1. Do not run MinerU.
2. Do not run PaddleOCR/PPStructure.
3. Do not call cloud APIs, LLMs, VLMs, or network endpoints.
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
10. Preserve Chinese text as UTF-8. No `????` or replacement characters.

## commit_requirements
After implementation:
1. `git status`
2. only add 320D2 code and this task document;
3. do not add `output/`;
4. do not add `E:\mineru_lab`;
5. do not add unrelated untracked files such as:
   - `fix_307e_reviewed_at.py`
   - `tools/run_stage7a_5pdf_regression_sandbox.py`
   - `tools/update_stage5v_production_06_safe_rows.py`
6. commit message:
   `Calibrate row text mapping trust gate`
7. push to remote `main`.

## final_response_requirements
After push, report:
- pushed branch
- commit hash
- changed files
- output report path
- source_candidate_count
- context_enriched_candidate_count
- trusted_preview_count
- review_required_preview_count
- rejected_preview_count
- unit_unknown_count
- year_inferred_count
- smoke_verified_candidate_count
- row_text_only_trusted_count
- repaired_trusted_count
- sandbox_mapping_decision
- top risk tags
- skipped/untracked files
