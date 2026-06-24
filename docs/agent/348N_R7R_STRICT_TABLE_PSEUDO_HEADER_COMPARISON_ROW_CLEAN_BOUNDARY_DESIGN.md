## Task ID

`348N-R7R strict_table pseudo-header / comparison-row clean-boundary design`

## Task Type

review / diagnosis / policy design only

This is a design task, not an implementation task. No code, tests, output, config, or pipeline was modified. No MinerU / OCR / LLM / VLM calls were made.

---

## Input context

```text
workspace = D:\_datefac_agent
branch    = pivot/348-agent-foundation
pipeline  = intake -> audit -> review -> delivery
active package = datefac_agent/
stage     = strict audit / review / clean-boundary design (not production delivery)
```

Readiness gates preserved unchanged:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

R7Q reviewed workbook family:

```text
input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx
pilot output = output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/
```

R7Q confirmed the prior MARKET_REFERENCE_ROW clean_data leak is fixed. R7Q narrowed the remaining risk to:

```text
STRICT_FINANCIAL_TABLE_ROW may still over-admit pseudo-header / comparison-dimension rows into clean_data
```

Typical risky rows observed in R7Q:

```text
市场数据
厂商
对比维度
```

---

## Files reviewed

Read-only review:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/项目进程.md`
- `项目进展大白话说明.md`
- `docs/codex_tasks/348N_R7R_strict_table_pseudo_header_comparison_row_clean_boundary_design.md`
- `docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md`
- `docs/agent/348N_R7P_FIX2_QA_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_REVIEW.md`
- `docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md`
- `docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md`
- `datefac_agent/review/clean_candidate_policy.py` (read-only grounding)
- `datefac_agent/audit/row_type_classifier.py` (read-only grounding)
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json` (read-only)
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv` (read-only)
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/review_queue.csv` (read-only)
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/evidence_index.json` (read-only)

No file in `output/` was modified. Source code files (`clean_candidate_policy.py`, `row_type_classifier.py`) were only read to ground the design; they were not modified because this is a design-only task.

---

## R7Q recap

Post-FIX2 Taihao pilot manifest:

```text
decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
market_reference_row_count = 2
normalized_testset_record_row_count = 0
testset_supporting_row_count = 0
strict_financial_table_row_count = 104
internal_clean_candidate_count = 92
internal_reference_candidate_count = 0
weak_evidence_count = 158
strong_evidence_count = 0
forbidden_clean_row_type_found = no
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

R7Q confirmed:

- no logical / physical count confusion (`clean_data_row_count == clean_data_csv_row_count == 92`, `review_queue_row_count == review_queue_csv_row_count == 66`)
- `clean_data` has no forbidden `row_type` (no `MARKET_REFERENCE_ROW` / `TESTSET_SUPPORTING_ROW` / `NORMALIZED_TESTSET_RECORD_ROW` / `UNKNOWN_ROW`)
- 收盘价 / 总市值 `MARKET_REFERENCE_ROW` correctly remain in `review_queue`
- no second `qualitative_facts`-like facts schema found in the Taihao workbook family
- the new remaining risk is narrower: `STRICT_FINANCIAL_TABLE_ROW` may over-admit pseudo-header / comparison-dimension rows into `clean_data`

R7Q decision: `348N_R7Q_RECOMMENDS_FOCUSED_POLICY_DESIGN`

---

## Problem statement

After R7P-FIX2, the market-reference clean_data leak is closed. The output guardrail contract no longer fires on this workbook family. However, R7Q read-only inspection of `clean_data.csv` shows that all 92 clean rows are typed as `STRICT_FINANCIAL_TABLE_ROW` + `INTERNAL_CLEAN_CANDIDATE` + `WEAK_EVIDENCE`, and a subset of those rows do not look like stable financial facts. They look like table scaffolding:

- pseudo-header rows (a cell whose value is a column header for a sub-table block, e.g. `市场数据`, `项目`, `指标`)
- comparison-dimension rows (a row whose metric cell names a comparison axis rather than a metric, e.g. `厂商`, `对比维度`, `订单日期`)

These rows currently pass `classify_clean_candidate(...)` because the policy only checks `STRICT_FINANCIAL_TABLE_ROW` + `WEAK_EVIDENCE` + absence of unit/period/valuation issues, and then returns `INTERNAL_CLEAN_CANDIDATE`. The policy has no signal for "this strict row is actually a header / dimension row, not a financial fact".

The project principle is:

```text
宁可进 review，不轻易进 clean。
```

So the design question is: should these scaffolding rows continue to enter `clean_data`, and if not, what is the smallest safe policy change?

---

## Observed risky rows

Inspection of `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv` (read-only). The rows below are currently admitted as `INTERNAL_CLEAN_CANDIDATE` but do not look like direct financial facts.

### Pseudo-header rows (metric cell is a block / column header)

```text
核心盈利预测与估值,11,市场数据      period_values = "数值","基础数据","数值"
行业赛道数据,13,厂商                period_values = "型号","最大功率","排量","缸型"
行业赛道数据,19,对比维度            period_values = "中速燃气内燃机","重型/航改型燃气轮机"
行业赛道数据,29,订单日期            period_values = "季度","项目地点","容量","发动机型号","数量","用途"
行业赛道数据,34,厂商                period_values = "2025-2026年现有产能","2030年规划产能"
三大财务报表与核心指标,17,项目      period_values = "2025A","2026E","2027E","2028E"   (echoes period labels)
三大财务报表与核心指标,28,项目      period_values = "2025A","2026E","2027E","2028E"   (echoes period labels)
三大财务报表与核心指标,35,指标      period_values = "2025A","2026E","2027E","2028E"   (echoes period labels)
```

### Comparison-dimension rows (metric cell names a comparison axis / category)

The same `行业赛道数据` sheet also contains rows whose `metric_name` is a category label and whose `period_values` are descriptive strings rather than numeric facts, for example:

```text
行业赛道数据,20,热效率              period_values = "单循环48-49%，无联合循环","单循环38-42%，联合循环60-65%"
行业赛道数据,21,单机功率            period_values = "18-19MW/台","联合循环400+MW/台"
行业赛道数据,22,交付+部署周期       period_values = "12-18个月","3-5年"
行业赛道数据,23,单位建设成本        period_values = "1200-1500美元/kW","1800-2500美元/kW"
行业赛道数据,24,大修间隔            period_values = "24000小时","16000-20000小时"
行业赛道数据,25,燃料灵活性          period_values = "适配多气源，支持20%混氢","高纯度天然气，混氢能力弱"
行业赛道数据,26,氮氧化物排放        period_values = "500-800ppm，需SCR脱硝","100-200ppm，DLN技术即可达标"
```

These are technically "structured" rows (they sit in a sheet with period headers), but their values are descriptive comparison strings, not stable numeric financial facts. Under a strict clean-admission reading they are comparison-dimension content, not clean exportable facts.

### Common structural signal

All the risky rows share a deterministic, auditable signal:

```text
period_values are entirely non-numeric strings (or echo the period labels themselves)
```

By contrast, the true financial fact rows in the same `clean_data.csv` have `period_values` that are predominantly numeric (e.g. 营业总收入, 归母净利润, EPS, P/E, 营业成本, 资产总计). The numeric-vs-non-numeric split of `period_values` is the cleanest deterministic discriminator available without an LLM.

---

## Policy options

### Option A — new row_type

Introduce one or more new `row_type` values, e.g.:

```text
STRICT_TABLE_PSEUDO_HEADER_ROW
STRICT_TABLE_COMPARISON_DIMENSION_ROW
STRUCTURED_TABLE_SCAFFOLDING_ROW
```

and route them to `REVIEW_REQUIRED`.

- Pros: makes the scaffolding nature explicit in the manifest / evidence index; reusable across workbook families.
- Cons: touches `row_type_classifier.py` (typing layer), not just policy; larger blast radius; requires new typing tests; risks regressing existing workbook families if the new typing is too eager.

### Option B — narrower clean_candidate_policy

Keep `row_type = STRICT_FINANCIAL_TABLE_ROW`, but add a deterministic admission guard inside `classify_clean_candidate(...)`:

```text
STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + (all period_values are non-numeric / period_values echo period labels) -> REVIEW_REQUIRED
```

- Pros: smallest safe change; local to `clean_candidate_policy.py`; no row typing change; no output guardrail contract change; directly aligns with the project principle.
- Cons: the signal "all period_values non-numeric" must be available to the policy layer; today `AuditRowResult` carries `period_values_json`, so the signal is already present or trivially derivable; does not make the scaffolding nature visible in `row_type` for downstream readers.

### Option C — additional review-required rule for STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + pseudo-header-like metric text

Add a review rule keyed on metric-text shape, e.g. metric in `{市场数据, 厂商, 对比维度, 项目, 指标, 订单日期, ...}`.

- Pros: very targeted.
- Cons: metric-text allowlist / denylist is fragile and overfits to one workbook; high maintenance; will miss new scaffolding labels in future workbook families.

### Comparison

```text
Option A: typing change, larger blast radius, most explicit
Option B: policy-only change, smallest safe change, general, deterministic
Option C: metric-text denylist, fragile, overfit, not recommended
```

---

## Recommended option

**Option B — narrower `clean_candidate_policy` with a deterministic non-numeric `period_values` admission guard**, as the primary recommendation.

Concretely, the design direction (to be implemented in a later task, not here) is:

```text
Inside classify_clean_candidate(...), for STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE with no unit/period/valuation issue,
add a final guard before returning INTERNAL_CLEAN_CANDIDATE:

  if all period_values are non-numeric (or period_values echo the period labels themselves):
      return REVIEW_REQUIRED

otherwise:
      return INTERNAL_CLEAN_CANDIDATE
```

This keeps the row typed as `STRICT_FINANCIAL_TABLE_ROW` (no typing change), keeps the output guardrail contract unchanged, and only narrows clean admission for rows whose `period_values` carry no numeric fact content.

Option A (new `row_type`) is **not recommended now**. The scaffolding rows are a clean-admission problem, not a row-typing problem. Adding a new `row_type` now would widen blast radius and risk regressing the already-stable Linyang and Anjing workbook families before the policy signal is validated. A new `row_type` can be reconsidered later if downstream consumers need the scaffolding nature to be visible in `row_type`.

Option C (metric-text denylist) is **not recommended**. It is fragile and overfits to the Taihao workbook family.

---

## Rationale

1. **Project principle alignment.** "宁可进 review，不轻易进 clean" means a row that carries no numeric financial fact should not be admitted to `clean_data` merely because it sits in a structured sheet. Pseudo-header and comparison-dimension rows carry no stable numeric fact, so they should go to `REVIEW_REQUIRED`.

2. **Deterministic and auditable.** The signal "all `period_values` are non-numeric (or echo the period labels)" is fully deterministic, requires no LLM, and is auditable from `period_values_json` already present in `AuditRowResult`. It is testable with compact fixtures.

3. **Smallest safe change.** Option B is local to `clean_candidate_policy.py`. It does not touch `row_type_classifier.py`, `output_schema_guardrails.py`, clean row assembly, readiness gates, or export behavior. This matches the precedent set by R7P-FIX2, which was also a local policy alignment.

4. **General, not Taihao-specific.** The non-numeric-`period_values` signal is structural, not workbook-specific. A pseudo-header row in any workbook family will have non-numeric `period_values`. So the policy is general by construction, not overfit to Taihao.

5. **Does not weaken the guardrail contract.** The output guardrail contract already forbids `MARKET_REFERENCE_ROW` / `TESTSET_SUPPORTING_ROW` / `NORMALIZED_TESTSET_RECORD_ROW` / `UNKNOWN_ROW` in `clean_data`. Option B only narrows which `STRICT_FINANCIAL_TABLE_ROW` rows become `INTERNAL_CLEAN_CANDIDATE`; it does not add a new forbidden `row_type` and therefore does not risk blocking legitimate data through a hard guardrail.

6. **Conservative on evidence.** All Taihao rows are still `WEAK_EVIDENCE`. Narrowing admission under `WEAK_EVIDENCE` is consistent with the evidence policy: a weak-evidence row with no numeric fact content should not be exported as clean.

---

## Required Analysis Questions (answers)

### 1. Classification Question

Should rows like `市场数据 / 厂商 / 对比维度` remain classified as `STRICT_FINANCIAL_TABLE_ROW`?

**Answer: yes, for now.** They should remain `STRICT_FINANCIAL_TABLE_ROW` at the typing layer. The problem is not that they were mis-typed as strict-table rows (they do sit inside structured sheets with period headers), but that the clean-admission policy over-admits them. Introducing a new `row_type` now (e.g. `STRICT_TABLE_PSEUDO_HEADER_ROW`) is premature: it widens blast radius and risks regressing stable workbook families before the policy signal is validated. A new `row_type` can be reconsidered later only if downstream consumers need the scaffolding nature visible in `row_type`.

### 2. Clean Admission Question

Should these rows remain in `clean_data`?

**Answer: no.** Pseudo-header and comparison-dimension rows should not remain in `clean_data`. They carry no stable numeric financial fact. Under the project principle, they should become `REVIEW_REQUIRED`.

### 3. Policy Question

Is the better fix a new `row_type`, a narrower `clean_candidate_policy`, or a review-required rule?

**Answer: narrower `clean_candidate_policy` (Option B).** Add a deterministic admission guard for `STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE` rows whose `period_values` are entirely non-numeric (or echo the period labels). This is the smallest safe policy change. A new `row_type` is not needed now. A metric-text denylist is fragile and not recommended.

### 4. Evidence Question

What signals distinguish a true clean financial fact row from a pseudo-header / comparison-dimension row?

**Primary deterministic signal:**

```text
period_values content shape
  - true financial fact row: period_values are predominantly numeric (e.g. 4356, -991.03, 33.98)
  - pseudo-header / dimension row: period_values are entirely non-numeric strings
    (e.g. "数值","基础数据","数值" / "型号","最大功率","排量","缸型")
    or period_values echo the period labels themselves (e.g. "2025A","2026E","2027E","2028E")
```

**Supporting deterministic signals (available, not LLM-dependent):**

```text
- metric_name shape: pure generic label like 项目 / 指标 / 市场数据 / 厂商 / 对比维度 / 订单日期
- unit_hint empty AND period_values all non-numeric (reinforces non-fact)
- value density: no numeric token anywhere across period_values
- row position / neighbor rows: a scaffolding row is often followed by numeric fact rows
    (but row position is a weaker signal and should NOT be the primary discriminator)
```

**Signals explicitly rejected as primary discriminator:**

```text
- LLM judgment (forbidden)
- metric-text denylist (fragile, overfit)
- row position alone (too weak, context-dependent)
```

The recommended primary signal — "all `period_values` non-numeric OR echo period labels" — is deterministic, auditable, and testable. It does not rely on LLM judgment.

### 5. Scope Question

Should the policy be general across workbook families, or limited to Taihao?

**Answer: general.** The non-numeric-`period_values` signal is structural, not workbook-specific. A pseudo-header or comparison-dimension row in any workbook family will exhibit non-numeric `period_values`. Limiting the policy to Taihao would be overfitting and would not protect future workbook families. The default from the task doc applies: general if evidence is structural, narrow if evidence is workbook-specific — here the evidence is structural.

### 6. Guardrail Question

Should this become a hard output guardrail?

**Answer: not yet.** This should first be a `clean_candidate_policy` refinement validated through tests. The output guardrail contract (`output_schema_guardrails.py`) currently forbids specific `row_type` values in `clean_data`. Adding a "no non-numeric-`period_values` row in `clean_data`" hard guardrail now is risky: it could block legitimate rows whose values are legitimately textual in a future workbook family, and a hard guardrail failure stops the run loudly. The safer path is:

```text
1. narrow clean_candidate_policy first (policy layer)
2. validate with tests across Linyang / Anjing / Taihao fixtures
3. only after the policy is stable, consider promoting to a hard guardrail
```

A hard guardrail should only enforce stable rules unlikely to block legitimate data. The non-numeric-`period_values` signal is promising but not yet validated across families, so it should not be a hard guardrail in the first implementation.

### 7. Implementation Readiness Question

Should R7R recommend an implementation task?

**Answer: yes.** Recommend a separate implementation task:

```text
348N-R7S strict_table pseudo-header / comparison-row clean-boundary implementation
```

Scope for R7S (to be defined in its own task doc):

```text
- add a deterministic non-numeric period_values admission guard in clean_candidate_policy.py
  for STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE rows
- keep row_type = STRICT_FINANCIAL_TABLE_ROW (no typing change)
- keep output_schema_guardrails.py unchanged
- add compact fixtures under tests/agent/fixtures/ covering pseudo-header, comparison-dimension,
  and true numeric-fact rows
- rerun the Taihao pilot to confirm scaffolding rows move to review_queue without breaking
  the Linyang / Anjing workbook families
- keep all readiness gates closed
```

The implementation task must be separate from this design task, per the task boundary.

### 8. Tests Question

Are tests required in a later implementation task?

**Answer: yes.** R7S should add tests that prove:

```text
1. STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + all-non-numeric period_values -> REVIEW_REQUIRED
2. STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + period_values echoing period labels -> REVIEW_REQUIRED
3. STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE + numeric period_values -> INTERNAL_CLEAN_CANDIDATE (unchanged)
4. existing MARKET_REFERENCE_ROW / NORMALIZED_TESTSET_RECORD_ROW / TESTSET_SUPPORTING_ROW behavior unchanged
5. the full agent suite remains green
6. the Taihao pilot rerun moves scaffolding rows to review_queue without a new guardrail failure
```

Tests are required because this changes clean-admission behavior and must not silently regress the Linyang or Anjing workbook families.

### 9. Rerun Question

Is an output rerun required in a later task?

**Answer: yes, but only in the implementation task (R7S), not here.** After the policy change, R7S should rerun the Taihao pilot to confirm:

```text
- scaffolding rows (市场数据 / 厂商 / 对比维度 / 项目 / 指标 / 订单日期) move to review_queue
- clean_data_row_count drops from 92 by the number of scaffolding rows
- no new output guardrail failure
- Linyang and Anjing workbook families do not regress
```

No rerun is performed in this R7R design task. This task is docs-only.

---

## Whether new row_type is needed

```text
new_row_type_needed = no (not now)
```

A new `row_type` (e.g. `STRICT_TABLE_PSEUDO_HEADER_ROW`) is not needed at this stage. The problem is a clean-admission policy gap, not a row-typing error. Adding a new `row_type` now would widen blast radius and risk regressing stable workbook families. A new `row_type` can be reconsidered later if downstream consumers need the scaffolding nature visible in `row_type`.

---

## Whether clean_candidate_policy should change

```text
clean_candidate_policy_should_change = yes (in a later implementation task, not here)
```

`clean_candidate_policy.py` should add a deterministic admission guard for `STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE` rows whose `period_values` are entirely non-numeric or echo the period labels. The change should be local to `classify_clean_candidate(...)`, should not touch `row_type_classifier.py` or `output_schema_guardrails.py`, and should be validated by tests and a Taihao rerun in R7S.

---

## Whether output guardrails should change

```text
output_guardrails_should_change = no (not now)
```

`output_schema_guardrails.py` should remain unchanged. The non-numeric-`period_values` signal should first be a policy-layer refinement validated through tests. Promoting it to a hard guardrail is premature and could block legitimate textual-value rows in future workbook families. A hard guardrail should only enforce stable rules unlikely to block legitimate data.

---

## Whether tests are required in a later implementation task

```text
tests_required_later = yes
```

R7S must add tests proving the non-numeric-`period_values` admission guard routes scaffolding rows to `REVIEW_REQUIRED` while leaving true numeric-fact rows as `INTERNAL_CLEAN_CANDIDATE`, and must keep the full agent suite green.

---

## Whether rerun is required in a later task

```text
output_rerun_required_later = yes (in R7S, not here)
```

R7S should rerun the Taihao pilot after the policy change to confirm scaffolding rows move to `review_queue` without a new guardrail failure and without regressing other workbook families.

---

## Readiness gates

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Unchanged. This design task does not promote any readiness gate.

---

## Forbidden actions respected

```text
code_modified = no
tests_modified = no
output_modified = no
config_modified = no
dependencies_modified = no
input_modified = no
temp_modified = no
data_modified = no
legacy_datefac_modified = no
AGENTS_md_modified = no
skills_modified = no
handoff_modified = no
项目进程_modified = no
项目进展大白话说明_modified = no
codex_tasks_modified = no
MARKET_REFERENCE_ROW_policy_changed = no
qualitative_facts_admission_broadened = no
output_guardrails_changed = no
MinerU_run = no
OCR_run = no
LLM_run = no
VLM_run = no
new_workbook_pilot_run = no
git_add_dot = no
git_add_A = no
git_reset_hard = no
git_commit = no
git_push = no
```

---

## Boundary check

```text
only_allowed_result_report_created = yes
  -> docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md
files_modified_outside_allowed_scope = no
code_changes_made = no
test_changes_made = no
output_files_modified = no
config_files_modified = no
readiness_gates_changed = no
export_behavior_changed = no
external_calls_made = 0
```

This task created exactly one file under the allowed `docs/agent/` scope. No code, test, output, config, input, temp, data, legacy, or protected doc file was modified.

---

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7R_RECOMMENDS_NARROWER_CLEAN_CANDIDATE_POLICY_NOT_NEW_ROW_TYPE
design_result（设计结果）= Option B: add deterministic non-numeric period_values admission guard in clean_candidate_policy.py for STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE; route scaffolding rows to REVIEW_REQUIRED; keep row_type and output guardrails unchanged
implementation_required（是否需要实现）= yes (in a separate later task, R7S)
test_required_later（后续是否需要测试）= yes
output_rerun_required_later（后续是否需要重跑 output）= yes (in R7S, Taihao pilot rerun)
readiness_gates（就绪门）= unchanged / closed (client_ready=false, production_ready=false, formal_client_export_allowed=false, demo_export_only=true)
code_changes_made（是否改代码）= no
test_changes_made（是否改测试）= no
output_files_modified（是否修改 output）= no
recommended_next_task（推荐下一任务）= 348N-R7S strict_table pseudo-header / comparison-row clean-boundary implementation
```

---

## Recommended next task

```text
348N-R7S strict_table pseudo-header / comparison-row clean-boundary implementation
```

Suggested scope (to be confirmed in its own task doc):

```text
- add a deterministic non-numeric period_values admission guard in clean_candidate_policy.py
  for STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE rows (all period_values non-numeric OR echo period labels -> REVIEW_REQUIRED)
- keep row_type = STRICT_FINANCIAL_TABLE_ROW (no typing change)
- keep output_schema_guardrails.py unchanged
- add compact fixtures under tests/agent/fixtures/ for pseudo-header, comparison-dimension, and true numeric-fact rows
- rerun the Taihao pilot to confirm scaffolding rows move to review_queue
- verify Linyang and Anjing workbook families do not regress
- keep all readiness gates closed
- do not broaden qualitative_facts admission
- do not change MARKET_REFERENCE_ROW policy
- do not change output guardrails
```

The implementation task must be separate from this design task.

---

## Whether the result is ready for human review

```text
ready_for_human_review = yes
```

This is a docs-only design report. It makes no code, test, or output change. It recommends a conservative, deterministic, auditable policy direction. It should be reviewed by a human before any implementation task (R7S) is opened.

---

## Whether a follow-up implementation task is recommended

```text
follow_up_implementation_task_recommended = yes
  -> 348N-R7S strict_table pseudo-header / comparison-row clean-boundary implementation
```

---

Stop after this task.

Do not git add.

Do not commit.

Do not push.
