## Task ID

`348N-R7 Qualitative Facts Narrow Clean-Admission Policy Design`

## Reviewed files

Read-only review:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/agent/348N_R6D_QA_GUARDRAILS_CONTRACT_DOCUMENTATION_REVIEW.md`
- `docs/agent/348N_R6D_GUARDRAILS_CONTRACT_DOCUMENTATION_UPDATE.md`
- `docs/agent/348N_R6C_OUTPUT_GUARDRAILS_ADOPTION_REVIEW.md`
- `docs/agent/348N_R5_QA_QUALITATIVE_FACTS_HEADER_FIX_REVIEW.md`
- `docs/agent/348N_R5_QUALITATIVE_FACTS_HEADER_DETECTION_FIX_RESULT.md`
- `docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md`

## Current qualitative_facts state

After R5 / R5-QA, `qualitative_facts` is no longer a malformed weak-evidence leak. Its current state is:

```text
row_type = TESTSET_SUPPORTING_ROW
evidence_level = STRONG_EVIDENCE
explicit_evidence_ref = 34 / 34
clean_candidate_type = REVIEW_REQUIRED
clean_data_row_count = 0
```

Key facts confirmed by R5/R5-QA and stabilized by R6B guardrails:

- The real Chinese header is now recognized.
- `页码` is preserved and every `qualitative_facts` row now has explicit page evidence.
- The sheet no longer enters `clean_data`; it routes to `TESTSET_SUPPORTING_ROW` and stays review-only.
- `qualitative_facts` rows include a mixed population:
  - numeric financial/operating facts (revenue, net profit, gross margin,费用,现金流,规模等)
  - earnings forecasts
  - business facts / company events
  - pure narrative/risk rows
- So the current conservative state is **well-evidenced but still review-only**.

## Clean-data policy question

The actual R7 question is not "can qualitative_facts be parsed?" — that is already solved.

The real question is:

```text
Should a subset of STRONG-evidenced qualitative_facts be allowed into clean_data,
or should clean_data remain restricted to structured financial-table style outputs only?
```

This is a policy-definition question, not a parser question.

Two competing interpretations of `clean_data` are possible:

1. **Narrow interpretation**
   - `clean_data` exists only for structured financial metrics that fit a stable metric/value/unit/period/entity shape.
   - Under this interpretation, all `qualitative_facts` should remain review-only, even when strongly evidenced.

2. **Broader interpretation**
   - `clean_data` may include some non-table facts if they are strongly evidenced and structurally complete enough to behave like safe structured metrics.
   - Under this interpretation, only a very narrow subset of `qualitative_facts` could be admitted.

Because the current project principle is "宁可进入 review_queue，也不要把不确定数据错放进 clean_data", any broadening must be extremely narrow, explicit, and fully auditable.

## Candidate admission criteria

If future policy ever allows `qualitative_facts` into `clean_data`, the admissible subset should be much narrower than "all rows in the sheet".

Recommended candidate segmentation:

### A. Potentially admissible: structured numeric financial/operating facts

Examples:

```text
营业收入 / 归母净利润 / 毛利率 / 期间费用 / 现金流
同比增速 / 费用率 / 产能利用率
明确规模值（如 GW / GWh / MW/MWh）
```

These rows may be eligible **only if all of the following are present**:

```text
source sheet = qualitative_facts (explicitly recognized facts schema)
row_type = TESTSET_SUPPORTING_ROW OR future dedicated QUALITATIVE_FACT_ROW type
explicit_evidence_ref present
source page present / explicit_ref present
entity present (主体)
metric present (指标/事件)
value present (数值)
unit present when the metric is unit-bearing
period present when the metric is period-bearing
row is semantically numeric / structured, not pure free-text narrative
```

### B. Keep review-only: pure text / narrative business facts

Examples:

```text
三大业务布局
业务概况
纯描述性业务事实
```

Reason: even if page-evidenced, they are not stable metric-table style data and are likely to contaminate downstream structured consumers.

### C. Keep review-only: company events / timing statements

Examples:

```text
项目并网时间
预计收入确认
签约/投产事件
```

Reason: they are factual but event-like and often depend on nuance, timing, and narrative wording rather than stable metric-table semantics.

### D. Keep review-only: pure risk / disclaimer rows

Examples:

```text
风险提示
政策/地缘政治/竞争风险说明
```

Reason: these are not clean-data facts under the current product shape.

### E. Keep review-only (for now): earnings forecasts embedded in qualitative_facts

Examples:

```text
2026-2028 归母净利润预期
```

Reason: forecasts may be structured, but they already overlap conceptually with `earnings_forecast` / structured forecast sheets. Admitting them from `qualitative_facts` before reconciliation rules exist risks double-entry or conflicting-source ambiguity.

## Recommended policy

Recommendation:

`348N_R7_RECOMMENDS_PILOT_ANOTHER_WORKBOOK_BEFORE_POLICY_CHANGE`

Detailed recommendation:

1. **Do not allow `qualitative_facts` into `clean_data` now.**
2. Keep the current R5+ behavior:

```text
qualitative_facts -> TESTSET_SUPPORTING_ROW -> REVIEW_REQUIRED
```

3. If the project later wants a narrow admission policy, design it **only after** another workbook family under the stabilized guardrails has been piloted.

Why not allow it now:

- Current evidence is only from one workbook family (`linyang_energy_pdf_extracted_testset`).
- `qualitative_facts` still mixes multiple semantic categories in one sheet (numeric facts, business descriptions, events, forecasts, risk text).
- There is no dedicated row type separating "structured fact candidate" from "supporting narrative fact" yet.
- There is no deduplication / overlap policy between `qualitative_facts` facts and existing financial/forecast sheets.
- Output guardrails are now stable, so the safest next move is to test another workbook family under those guardrails before broadening clean admission semantics.

So the best current policy is:

```text
Keep qualitative_facts review-only now.
Use another guarded pilot to see whether a second workbook family produces the same kind of strongly-evidenced, structurally-complete facts.
Only then decide whether a future R7B implementation is justified.
```

## Required guardrails if implemented

If a future implementation ever allows a narrow subset of `qualitative_facts` into `clean_data`, these guardrails would be mandatory:

### Row typing guardrails

- Prefer introducing a new explicit row type (for example a future `QUALITATIVE_FACT_CANDIDATE_ROW`) rather than reusing generic `TESTSET_SUPPORTING_ROW`.
- Do **not** allow all `TESTSET_SUPPORTING_ROW` into `clean_data`.

### Evidence guardrails

- `evidence_level == STRONG_EVIDENCE`
- `explicit_evidence_ref` required
- source page / explicit page reference required

### Completeness guardrails

- `metric` required
- `value` required
- `entity` required
- `unit` required when applicable
- `period` required when applicable
- missing any required element -> fallback to `REVIEW_REQUIRED`

### Semantic class guardrails

Only structured numeric facts may be admitted. Explicitly exclude:

```text
risk rows
pure narrative description rows
project/event timing rows
free-text only rows
```

### Sheet restriction guardrails

- admission, if ever allowed, must be restricted to the recognized `qualitative_facts` facts schema
- must not generalize to arbitrary supporting sheets

### Confidence guardrails

- if confidence is later used operationally, only a narrow threshold should be accepted
- but confidence alone must never substitute for evidence or completeness

### Duplicate / overlap guardrails

- if a fact overlaps with `income_statement` / `balance_sheet` / `cash_flow` / `earnings_forecast`, define precedence rules first
- no duplicate metric should enter `clean_data` from two semantically different sheets without explicit policy

### Output guardrail updates

If future admission is implemented, `output_schema_guardrails` must be updated to encode the new allowed row type / candidate semantics explicitly.

Example implications:

- today: `clean_data` forbids `TESTSET_SUPPORTING_ROW`
- future: if a dedicated `QUALITATIVE_FACT_CANDIDATE_ROW` is introduced, guardrails must still forbid all other supporting rows

### Review fallback

Whenever any of the above conditions is not met:

```text
fallback = REVIEW_REQUIRED
```

No partial-confidence auto-clean path.

## Non-goals

This R7 task does **not** recommend:

- broadening `clean_data` to all `qualitative_facts`
- changing `clean_candidate_policy` now
- changing `output_schema_guardrails` now
- changing row types now
- introducing new dependencies
- changing readiness gates or export behavior

## Risks

Risks if qualitative_facts is admitted too early:

1. **Semantic contamination** — clean_data stops meaning "structured financial-safe rows" and becomes a mix of metrics, narratives, events, and risk text.
2. **Cross-sheet duplication** — the same business fact may appear in both financial sheets and facts sheets.
3. **Workbook-family overfitting** — a rule tuned to Linyang may not hold on the next facts-style workbook.
4. **Downstream confusion** — consumers may assume clean_data fields are homogeneous when they are not.
5. **Guardrail complexity** — once facts-schema admission exists, output guardrails become more complex and must be updated carefully.

Risks if kept review-only too long:

- some strongly-evidenced numeric facts remain unavailable to downstream consumers;
- clean_data stays narrower than it might eventually need to be.

At the current stage, the first risk set is much more dangerous than the second.

## Validation result

```text
git pull --ff-only origin pivot/348-agent-foundation
  -> Already up to date

git status -sb before editing
  -> clean

git branch --show-current
  -> pivot/348-agent-foundation

git diff --check
  -> clean
```

No pytest required because this is a policy/design task and no code/tests were modified.

## Decision

`348N_R7_RECOMMENDS_PILOT_ANOTHER_WORKBOOK_BEFORE_POLICY_CHANGE`

Rationale: `qualitative_facts` is now correctly parsed and strongly evidenced, but it still mixes numeric facts, events, forecasts, business descriptions, and risk text in one schema. The project should not broaden clean_data semantics from a single workbook family. First validate another workbook family under the current guardrails; only if the same structured-fact pattern repeats should a narrow clean-admission implementation be designed.

## Recommended next task

`348N-R7 pilot another workbook family under guardrails`

Recommended sequence:

```text
1. Run another workbook family under the stabilized output guardrails
2. Compare whether a similar strongly-evidenced facts schema appears
3. If repeated, open R7B narrow qualitative_facts clean-admission implementation/design
4. Then QA that implementation before any delivery/export work
```

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7_RECOMMENDS_PILOT_ANOTHER_WORKBOOK_BEFORE_POLICY_CHANGE
current_qualitative_facts_policy（当前 qualitative_facts 策略）= TESTSET_SUPPORTING_ROW + STRONG_EVIDENCE + REVIEW_REQUIRED, review-only
recommended_policy（推荐策略）= keep qualitative_facts review-only for now; do not broaden clean_data yet
clean_admission_allowed_now（现在是否允许进入 clean_data）= no
required_guardrails_if_allowed（如允许所需护栏）= dedicated row_type or equivalent narrow row-class; STRONG_EVIDENCE; explicit_evidence_ref; entity/metric/value/unit/period completeness; semantic numeric-fact restriction; duplicate/overlap policy; output_schema_guardrails update; REVIEW_REQUIRED fallback
code_changes_made（是否改代码）= no
pytest_result（测试结果）= not run / not required
LLM / MinerU / OCR / VLM calls（外部调用次数）= 0
readiness_gates（就绪门）= unchanged / closed
recommended_next_task（推荐下一任务）= 348N-R7 pilot another workbook family under guardrails
```
