## Task ID

`348N-R7V cross-family clean-boundary summary and readiness review`

## Task Type

documentation-only readiness review. No code, tests, output, input, or config was modified. No workbook reruns, MinerU, OCR, LLM, or VLM calls were made. One result report was created.

---

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating b4a0ee9..3206d7d
  Fast-forward
   ...348N_R7V_cross_family_clean_boundary_summary_and_readiness_review.md | 304 +++++
   1 file changed, 304 insertions(+)

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation (clean)

git log --oneline -12:
  3206d7d docs: add R7V readiness review task
  b4a0ee9 docs: add R7U workbook regression review
  bb4ae21 docs: add R7U workbook regression task
  7a8f35a docs: add R7T Taihao rerun review
  0e9344c docs: add R7T Taihao rerun task
  8d1c063 docs: add R7S QA review
  b623c58 docs: add R7S QA task
  0e09901 fix: narrow strict table clean admission
  96fb1aa docs: add R7S implementation task
  fd2325b docs: add R7R clean-boundary design
  12c451d docs: sync R7Q pilot review progress
  c7df270 docs: add R7Q workbook family pilot review
```

Worktree was clean after pull.

---

## Files reviewed

Read-only review (all previously read during R7R-R7U; no output was modified):

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/项目进程.md`
- `项目进展大白话说明.md`
- `docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md`
- `docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md`
- `docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md`
- `docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md`
- `docs/agent/348N_R7P_FIX2_QA_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_REVIEW.md`
- `docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md`
- `docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md`
- `datefac_agent/review/clean_candidate_policy.py` (read-only)
- `tests/agent/test_agent_excel_intake_audit_348a.py` (read-only)

---

## R7P-R7U chain summary

The R7P-R7U chain is a single coherent clean-boundary hardening arc across three workbook families. Each round solved one clearly-scoped problem without broadening admission.

```text
R7P  another workbook family guardrails pilot (Taihao)
     -> exposed a clean_data boundary violation: MARKET_REFERENCE_ROW (收盘价) entered clean_data

R7P-FIX  market reference clean_data boundary leak investigation
     -> root cause: clean_candidate_policy still mapped MARKET_REFERENCE_ROW + WEAK_EVIDENCE -> INTERNAL_REFERENCE_CANDIDATE
     -> diagnosis only, no code change

R7P-FIX2  market reference clean_data admission policy alignment
     -> fix: MARKET_REFERENCE_ROW -> REVIEW_REQUIRED (local policy change)
     -> tests updated, Taihao guardrail failure gone

R7P-FIX2-QA  market reference policy review
     -> confirmed MARKET_REFERENCE_ROW no longer enters clean_data
     -> Taihao rerun clean, no new guardrail failure

R7Q  another workbook family pilot review (Taihao post-FIX2)
     -> confirmed market-reference leak fixed
     -> revealed a new, narrower risk: STRICT_FINANCIAL_TABLE_ROW over-admits pseudo-header / comparison-dimension rows
     -> decision: 348N_R7Q_RECOMMENDS_FOCUSED_POLICY_DESIGN

R7R  strict_table pseudo-header / comparison-row clean-boundary design
     -> design: narrower clean_candidate_policy (Option B), not a new row_type
     -> primary signal: period_values all-non-numeric OR echo period labels
     -> design only, no code change

R7S  strict_table scaffolding clean-boundary implementation
     -> implemented the R7R design in clean_candidate_policy.py
     -> added deterministic helpers + scaffolding guard
     -> 10 new tests; 86 passed (tests/agent)

R7S-QA  strict_table scaffolding clean-boundary review
     -> confirmed guard valid, scoped to WEAK_EVIDENCE strict rows
     -> confirmed MARKET_REFERENCE_ROW / qualitative_facts / numeric fact rows preserved
     -> no row_type_classifier or output_schema_guardrails change

R7T  Taihao strict_table scaffolding clean-boundary pilot rerun
     -> clean_data 92 -> 72; review_queue 66 -> 86
     -> 20 scaffolding rows moved to review; all 6 risky labels gone from clean_data
     -> no guardrail failure; readiness gates closed

R7U  Linyang / Anjing workbook family regression check
     -> Linyang: clean_data 0 (unchanged), review_queue 489 (unchanged), no regression
     -> Anjing: clean_data 65, internal_clean_candidate_count 65 (unchanged), R7S removed 0 rows
        (-10 vs R4 baseline is entirely R7P-FIX2 MARKET_REFERENCE_ROW, not R7S)
     -> no guardrail failure; readiness gates closed
```

Chain outcome: the clean-boundary policy is now validated across all three workbook families. The guard narrows admission (never broadens), removes zero legitimate numeric fact rows, and keeps all readiness gates closed.

---

## Cross-family evidence table

```text
family    clean_data   review_queue  unknown  market_ref  guardrail  R7S effect        readiness
---------- ------------ ------------- -------- ----------- ---------- ----------------- ----------
Taihao    92 -> 72     66 -> 86      0 -> 0   2 (stable)  none       -20 scaffolding   closed
Linyang   0 (stable)   489 (stable)  0        10          none       0 (no change)     closed
Anjing    75 -> 65 *   7 -> 17 *     0        10          none       0 (R7S removed 0) closed
```

`*` Anjing delta (-10 clean / +10 review) is entirely from R7P-FIX2 (MARKET_REFERENCE_ROW), not from R7S. Anjing `internal_clean_candidate_count` stayed 65 (65 -> 65), proving R7S removed zero numeric fact rows.

Cross-family invariants confirmed:

```text
forbidden_clean_row_type_found = no (all three families)
market_reference_boundary_ok = yes (all three families)
normal_fact_preservation_ok = yes (Taihao + Anjing; Linyang N/A — clean_data is 0 by design)
logical == physical csv counts = yes (all three families)
unknown_row_count = 0 (all three families)
external calls (LLM/MinerU/OCR/VLM) = 0 (all three families)
```

---

## Taihao result summary

```text
input:  input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
R7Q baseline (pre-R7S): clean_data=92, review_queue=66
R7T rerun (post-R7S):   clean_data=72, review_queue=86
delta: clean_data -20, review_queue +20
unknown_row_count_after = 0
market_reference_row_count_after = 2
risky_rows_in_clean_after = no (市场数据/厂商/对比维度/订单日期/项目/指标 all moved to review_queue)
20 moved rows = 8 pseudo-header + 7 comparison-dimension + 5 comparison-table data rows
all moved rows share the signal: period_values entirely non-numeric
clean_data row_type set = {STRICT_FINANCIAL_TABLE_ROW} (no forbidden row_type)
normal numeric fact rows preserved (营业总收入/归母净利润/EPS/P/E/ROE/P/B/PUE系数)
guardrail failure = none
output_committed = no
```

---

## Linyang result summary

```text
input:  input/linyang_energy_pdf_extracted_testset (1).xlsx
baseline (R6B-FIX): clean_data=0, review_queue=489, review_queue_csv=46
R7U rerun (post-R7S): clean_data=0, review_queue=489, review_queue_csv=46
delta: 0 (no change)
unknown_row_count = 0
market_reference_row_count = 10 (stable)
clean_data row_type set = EMPTY (0 data rows; no forbidden row_type)
R7S effect = 0 (Linyang clean_data is 0 by design since R5; Linyang strict rows are STRONG_EVIDENCE so the WEAK_EVIDENCE-only R7S guard does not apply)
guardrail failure = none
R7S regression = no
```

---

## Anjing result summary

```text
input:  input/安井食品研报数据汇总.xlsx
baseline (R4): clean_data=75 (65 INTERNAL_CLEAN + 10 INTERNAL_REFERENCE/MARKET_REFERENCE), review_queue=7
R7U rerun (post-R7S): clean_data=65, review_queue=17
delta: clean_data -10, review_queue +10
cause of delta: R7P-FIX2 (MARKET_REFERENCE_ROW no longer enters clean_data; internal_reference_candidate_count 10 -> 0)
R7S effect = 0 (internal_clean_candidate_count 65 -> 65, R7S removed 0 rows)
unknown_row_count = 0
market_reference_row_count = 10 (stable; all 10 in review_queue, none in clean_data)
clean_data row_type set = {STRICT_FINANCIAL_TABLE_ROW} (no forbidden row_type)
normal financial fact preservation = yes (营业收入/YoY/净利润/毛利率 etc. all preserved)
guardrail failure = none
R7S regression = no
```

---

## Clean-boundary policy conclusion

The strict-table scaffolding clean-boundary policy is validated across all three workbook families.

```text
policy = R7S scaffolding guard in clean_candidate_policy.py
  -> STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + (all-non-numeric period_values OR echoed period labels) -> REVIEW_REQUIRED
  -> scoped to WEAK_EVIDENCE strict rows only
  -> primary discriminator = period_values numeric shape (deterministic, auditable, no LLM)
  -> metric label set is secondary, never blocks a row with numeric period_values
  -> no new row_type introduced
  -> row_type_classifier unchanged
  -> output_schema_guardrails unchanged
  -> MARKET_REFERENCE_ROW policy unchanged (R7P-FIX2)
  -> qualitative_facts admission unchanged

cross-family outcome:
  Taihao: 20 scaffolding rows correctly removed from clean_data
  Linyang: 0 rows affected (clean_data already 0; no regression)
  Anjing: 0 rows affected by R7S (numeric fact rows preserved; -10 is R7P-FIX2)
```

The guard behaves exactly as designed in R7R and implemented in R7S. It narrows admission conservatively ("宁可进 review，不轻易进 clean"), removes zero legitimate numeric fact rows, and produces no guardrail failure.

---

## Readiness gates review

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

These gates remained closed across R7T and R7U. No readiness gate was changed, weakened, or bypassed during the R7P-R7U chain.

`AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX` decisions on all three families reflect review pressure under weak evidence, not a guardrail failure, unknown-row collapse, or production readiness. The project remains in strict audit / review / clean-boundary design stage, not production delivery.

---

## Remaining risks

1. **All Taihao rows remain WEAK_EVIDENCE.** The Taihao workbook has 0 STRONG_EVIDENCE rows; clean_data trust still depends on conservative policy plus later human/QA interpretation. R7S narrows which weak-evidence rows enter clean_data but does not upgrade evidence strength.

2. **No evidence/page-number strengthening.** The R7P-R7U chain did not add page-number evidence extraction or strengthen WEAK_EVIDENCE to STRONG_EVIDENCE. Until evidence strengthening is addressed, clean_data remains weak-evidence-only.

3. **Scaffolding label set is open.** The current `STRICT_TABLE_SCAFFOLDING_METRIC_LABELS` covers 市场数据/厂商/对比维度/订单日期/项目/指标, but the primary discriminator is period_values shape, so future workbook families with new scaffolding labels are still protected by the numeric-shape check. However, a future workbook with legitimately all-text-valued financial facts (e.g. credit ratings) would route to REVIEW_REQUIRED — conservative but potentially over-cautious for such rows.

4. **Three families do not prove universality.** Taihao, Linyang, and Anjing cover diverse structures (豆包AI deep-report, normalized testset, traditional wide table), but they do not exhaust real-world workbook diversity. A fourth workbook family pilot may expose new boundary questions.

5. **qualitative_facts clean admission remains closed.** R7Q found no second qualitative_facts-like schema, so clean admission for facts-like sheets was not broadened. This is intentional, but it means strongly-evidenced facts schemas (like Linyang qualitative_facts) still route to review-only.

6. **Output guardrails not extended.** The R7S guard is a policy-layer refinement, not a hard output guardrail. If a future regression re-admits scaffolding rows, the guardrail contract would not catch it (it only forbids specific row_types, not non-numeric period_values). Promoting to a hard guardrail was deliberately deferred to avoid blocking legitimate text-valued rows.

---

## Decision

`348N_R7V_CONFIRMED_CROSS_FAMILY_CLEAN_BOUNDARY_VALID_READINESS_GATES_REMAIN_CLOSED`

The strict-table scaffolding clean-boundary policy is validated across Taihao, Linyang, and Anjing:

- R7T proved the guard removes 20 scaffolding rows from Taihao clean_data with zero guardrail failure.
- R7U proved the guard regresses zero rows in Linyang (0 change) and Anjing (R7S removed 0 rows; the -10 delta is R7P-FIX2).
- Normal numeric financial fact rows are preserved in all families.
- Market reference rows remain out of clean_data in all families.
- No forbidden row_type enters clean_data in any family.
- All readiness gates remain closed.

However, the project is NOT production-ready and formal client export is NOT allowed. The readiness gates remain closed by design. The clean-boundary hardening is complete for the current three-family scope, but evidence strengthening, a potential fourth family pilot, and qualitative_facts admission remain open questions for future tasks.

---

## Recommended next task

```text
348N-R7W evidence strengthening design (WEAK_EVIDENCE -> STRONG_EVIDENCE path)
```

Purpose:

- the R7P-R7U chain narrowed clean admission but did not strengthen evidence;
- all Taihao rows remain WEAK_EVIDENCE, so clean_data trust is still limited;
- design a deterministic, auditable path to elevate page-number-evidenced rows from WEAK_EVIDENCE to STRONG_EVIDENCE;
- keep all readiness gates closed;
- do not broaden admission; focus on evidence quality, not clean_data count.

Alternative if evidence strengthening is deferred:

```text
348N-R7W fourth workbook family pilot
```

- run a fourth real workbook family to test cross-family universality of the R7S guard;
- keep readiness gates closed.

This R7V task does not start either next task. The choice between evidence strengthening and a fourth family pilot is a project-direction decision for the human reviewer.

---

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7V_CONFIRMED_CROSS_FAMILY_CLEAN_BOUNDARY_VALID_READINESS_GATES_REMAIN_CLOSED
build_result（构建结果）= COMPILE_OK
test_result（测试结果）= tests/agent 86 passed
cross_family_result（跨family结果）= valid (Taihao + Linyang + Anjing all pass; no R7S regression; no guardrail failure)
taihao_result（泰豪结果）= clean_data 92->72, review_queue 66->86, 20 scaffolding rows removed, no guardrail failure
linyang_result（林洋结果）= clean_data 0 (unchanged), review_queue 489 (unchanged), no R7S regression
anjing_result（安井结果）= clean_data 65, review_queue 17, R7S removed 0 rows (-10 vs R4 is R7P-FIX2), normal facts preserved
readiness_gates（就绪门）= closed (client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true)
production_ready（是否生产就绪）= no
formal_client_export_allowed（是否允许正式客户导出）= no
files_modified（修改文件数）= 1 (R7V report only; no code/test/output/input/config changes)
error_count（错误数）= 0
boundary_check（边界检查）= passed (only the allowed R7V report created; no code/test/output/input/previous-doc/temp/data/legacy/config/guardrails/row_type_classifier/qualitative_facts/MARKET_REFERENCE_ROW/readiness-gate changes; no workbook reruns; no external calls)
recommended_next_task（推荐下一任务）= 348N-R7W evidence strengthening design (WEAK_EVIDENCE -> STRONG_EVIDENCE path) OR 348N-R7W fourth workbook family pilot (project-direction decision for human reviewer)
```
