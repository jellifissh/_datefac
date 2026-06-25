## Task ID

`348N-R7S-QA strict_table scaffolding clean-boundary review`

## Task Type

QA / review task. Not an implementation task. Not a Taihao output rerun task. No code or tests were modified in this task. One QA report was created.

---

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 0e09901..b623c58
  Fast-forward
   ...348N_R7S_QA_strict_table_scaffolding_clean_boundary_review.md | 252 +++++
   1 file changed, 252 insertions(+)
   create mode 100644 ...review.md

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  (clean)

git log --oneline -8:
  b623c58 docs: add R7S QA task
  0e09901 fix: narrow strict table clean admission
  96fb1aa docs: add R7S implementation task
  fd2325b docs: add R7R clean-boundary design
  12c451d docs: sync R7Q pilot review progress
  c7df270 docs: add R7Q workbook family pilot review
  84783a9 docs: update handoff for R7Q pilot review
  1124183 docs: add R7Q workbook family pilot review task
```

Worktree was clean after pull. The R7S implementation is already committed at `0e09901 fix: narrow strict table clean admission`. This QA task reviews that committed implementation.

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
- `docs/codex_tasks/348N_R7S_strict_table_pseudo_header_comparison_row_clean_boundary_implementation.md`
- `docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md`
- `docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md`
- `datefac_agent/review/clean_candidate_policy.py` (implementation under review)
- `tests/agent/test_agent_excel_intake_audit_348a.py` (tests under review)
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/agent_excel_intake_audit_348a_manifest.json` (read-only grounding)
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/clean_data.csv` (read-only grounding)
- `output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/review_queue.csv` (read-only grounding)

No output file was modified.

---

## Implementation review

Reviewed `datefac_agent/review/clean_candidate_policy.py` at commit `0e09901`.

The R7S implementation adds a deterministic scaffolding guard inside `classify_clean_candidate(...)`, placed in the `STRICT_FINANCIAL_TABLE_ROW` branch after the unit / period / valuation issue checks and before returning `INTERNAL_CLEAN_CANDIDATE`.

New helpers:

- `STRICT_TABLE_SCAFFOLDING_METRIC_LABELS`: a frozenset of generic scaffolding labels (`市场数据 / 厂商 / 对比维度 / 订单日期 / 项目 / 指标`), used only as a secondary reinforcing signal.
- `_is_numeric_value(value)`: returns True for int/float and numeric strings (`"4356"`, `"-991.03"`); explicitly rejects `bool` (an int subclass but not a financial fact), and rejects `None` / `""` / non-numeric strings.
- `_period_values_carry_no_numeric_fact(result)`: True when `period_values` is empty or no value is numeric.
- `_period_values_echo_period_labels(result)`: True when every value equals its own period label (e.g. `{"2025A":"2025A","2026E":"2026E"}`).
- `_looks_like_strict_table_scaffolding(result)`: combines the signals — all-non-numeric period_values, or echoed period labels, or a scaffolding label with all-non-numeric period_values.

When matched, the policy returns `REVIEW_REQUIRED`; otherwise the existing `INTERNAL_CLEAN_CANDIDATE` path is preserved.

The guard is placed correctly: it sits after the `evidence_level != "WEAK_EVIDENCE" -> REVIEW_REQUIRED` early return, so it only applies to weak-evidence strict rows; and it sits after the unit/period/valuation issue checks, so rows already flagged for those issues are not affected by the guard.

---

## Test review

Reviewed `tests/agent/test_agent_excel_intake_audit_348a.py` at commit `0e09901`.

10 R7S tests were added, grouped under a clear section comment, sharing a `_make_strict_scaffolding_row(...)` helper:

1. `test_r7s_market_data_pseudo_header_row_does_not_enter_clean_data` — 市场数据 + non-numeric period_values -> REVIEW_REQUIRED
2. `test_r7s_vendor_comparison_dimension_row_does_not_enter_clean_data` — 厂商 + non-numeric period_values -> REVIEW_REQUIRED
3. `test_r7s_comparison_axis_row_does_not_enter_clean_data` — 对比维度 + non-numeric period_values -> REVIEW_REQUIRED
4. `test_r7s_echoed_period_label_header_row_does_not_enter_clean_data` — 项目 + echoed period labels -> REVIEW_REQUIRED
5. `test_r7s_indicator_echoed_label_header_row_does_not_enter_clean_data` — 指标 + echoed period labels -> REVIEW_REQUIRED
6. `test_r7s_normal_numeric_fact_row_preserves_clean_admission` — 营业总收入 + numeric values -> INTERNAL_CLEAN_CANDIDATE
7. `test_r7s_numeric_string_fact_row_preserves_clean_admission` — 归母净利润 + numeric strings -> INTERNAL_CLEAN_CANDIDATE
8. `test_r7s_mixed_numeric_and_dash_fact_row_preserves_clean_admission` — PUE系数 + dash/numeric mix -> INTERNAL_CLEAN_CANDIDATE
9. `test_r7s_scaffolding_guard_does_not_apply_when_strong_evidence` — STRONG_EVIDENCE path unchanged
10. `test_r7s_scaffolding_label_with_numeric_values_stays_clean` — 指标 label + numeric values -> INTERNAL_CLEAN_CANDIDATE (label-alone never blocks)

Existing tests preserved: `test_strict_financial_weak_evidence_row_becomes_internal_clean_candidate`, `test_market_reference_weak_evidence_row_now_stays_review_required`, `test_market_reference_weak_evidence_row_with_unit_issue_stays_review_required`, the `test_qualitative_facts_*` family, and the guardrail tests are all unchanged and pass.

The tests are specific and not over-broad: each test isolates one signal (non-numeric period_values, echoed labels, numeric preservation, mixed dash/numeric, strong-evidence scoping, label-alone non-blocking). They directly map to the 7 required scenarios in the R7S task doc.

---

## Validation outputs

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
  -> COMPILE_OK
```

```text
pytest tests/agent -q
  -> 86 passed in 0.56s
```

```text
pytest tests -q
  -> 33 failed, 445 passed in 60.71s
```

Full-suite failure breakdown (all pre-existing, unrelated to R7S):

1. failure count = 33
2. failing areas:
   - `tests/benchmark/` — 29 failures across legacy 343j / 343k / 343l / 343m / 343n / 343o / 344a / 344a2 / 344b / 344c / 344d / 344e / 345c8 / 345c9 / 345c11 chains
   - `tests/test_pdfplumber_table_extractor.py` — 1 failure (legacy PDF extraction)
   - `tests/test_table_segmenter.py` — 2 failures (legacy table segmentation)
   - `tests/trust/test_deepseek_text_adjudicator_338a.py` — 1 failure (DeepSeek mock)
3. why unrelated to R7S:
   - None of these modules import `clean_candidate_policy` (verified by content search: `clean_candidate_policy` / `classify_clean_candidate` is referenced only in `tests/agent/test_agent_excel_intake_audit_348a.py`).
   - The failures are in legacy extraction / benchmark / trust modules that are explicitly marked as legacy reference in `AGENTS.md` §4 and are out of the current modification boundary.
   - These same 33 failures were verified as pre-existing during R7S implementation via `git stash` (they persisted with R7S changes stashed).
4. `pytest tests/agent -q` passed: yes — 86 passed.

No R7S-related test was modified or added in this QA task, and the agent suite remains green.

```text
git status -sb
  -> ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
     (clean before QA report creation)

git diff --stat
  -> (no output; clean)

git diff --name-only
  -> (no output; clean)

git diff --check
  -> (no output; clean)
```

---

## Policy boundary review

```text
row_type_classifier_modified = no
output_schema_guardrails_modified = no
MARKET_REFERENCE_ROW_policy_changed = no
qualitative_facts_admission_broadened = no
new_row_type_introduced = no
readiness_gates_changed = no
export_behavior_changed = no
```

The R7S change is local to `clean_candidate_policy.py`. It does not touch typing, guardrails, market-reference policy, qualitative_facts routing, readiness gates, or export behavior. The guard only narrows which `STRICT_FINANCIAL_TABLE_ROW` + `WEAK_EVIDENCE` rows become `INTERNAL_CLEAN_CANDIDATE`; it never broadens admission and never introduces a new `row_type`.

---

## Risk review

1. **False-positive risk for text-valued financial facts.** A strict-table row whose period_values are legitimately all-text (e.g. a rating like "AAA"/"AA+") would be routed to REVIEW_REQUIRED. This is acceptable under the project principle "宁可进 review，不轻易进 clean": such a row is better reviewed than silently admitted, and the Taihao clean_data.csv inspection showed the all-text rows are scaffolding (市场数据/厂商/对比维度/项目/指标), not facts. No numeric fact row is blocked because the guard keys on numeric presence.

2. **Empty period_values strict rows.** `_period_values_carry_no_numeric_fact` returns True for an empty dict, so a weak-evidence strict row with no period values routes to REVIEW_REQUIRED. This is conservative and consistent with the existing `test_period_issue_strict_row_does_not_enter_clean_data` behavior (period-missing rows already go to REVIEW_REQUIRED via the period issue path).

3. **Mixed dash/numeric rows.** Preserved correctly — `test_r7s_mixed_numeric_and_dash_fact_row_preserves_clean_admission` proves a row like PUE系数 (`-` + 1.49 + ...) stays INTERNAL_CLEAN_CANDIDATE because at least one value is numeric.

4. **Label-alone blocking.** Eliminated by design — `test_r7s_scaffolding_label_with_numeric_values_stays_clean` proves a scaffolding label (指标) with numeric values still stays clean. The period_values shape is the primary discriminator; the label set is secondary and only triggers when period_values are also non-numeric.

5. **STRONG_EVIDENCE scoping.** The guard is unreachable for STRONG_EVIDENCE rows because the `evidence_level != "WEAK_EVIDENCE" -> REVIEW_REQUIRED` early return precedes the strict-table branch. `test_r7s_scaffolding_guard_does_not_apply_when_strong_evidence` confirms this.

6. **No Taihao rerun yet.** The guard's effect on the actual Taihao pilot (scaffolding rows moving to review_queue, clean_data dropping from 92) has not been verified by a rerun in this task. This is the recommended next task.

---

## QA Questions (answers)

1. **Does R7S implement the R7R recommendation as a narrower clean-candidate policy, not a new row type?** Yes. The change is local to `clean_candidate_policy.py`; no new `row_type` was introduced and `row_type_classifier.py` was not modified.

2. **Does the guard apply only to weak-evidence strict-table rows that would otherwise enter clean_data?** Yes. It sits after the `evidence_level != "WEAK_EVIDENCE" -> REVIEW_REQUIRED` return and after the unit/period/valuation issue checks, so it only affects weak-evidence strict rows with no blocking issues that would otherwise become `INTERNAL_CLEAN_CANDIDATE`.

3. **Does the guard route scaffolding / pseudo-header / comparison-dimension rows to `REVIEW_REQUIRED`?** Yes. Tests 1–5 prove 市场数据 / 厂商 / 对比维度 / 项目 / 指标 with non-numeric or echoed period_values route to REVIEW_REQUIRED.

4. **Does it preserve normal numeric financial fact rows as clean candidates under the existing policy?** Yes. Tests 6 and 7 prove numeric (int/float and numeric-string) fact rows stay INTERNAL_CLEAN_CANDIDATE.

5. **Does it preserve mixed numeric rows such as rows with dash plus numeric values?** Yes. Test 8 proves a PUE系数 row with `-` plus numeric values stays INTERNAL_CLEAN_CANDIDATE.

6. **Does it preserve `MARKET_REFERENCE_ROW` behavior?** Yes. The `MARKET_REFERENCE_ROW -> REVIEW_REQUIRED` path is unchanged; existing market-reference tests pass.

7. **Does it preserve qualitative_facts behavior?** Yes. qualitative_facts rows route through `TESTSET_SUPPORTING_ROW -> REVIEW_REQUIRED`, which is unchanged; existing `test_qualitative_facts_*` tests pass.

8. **Does it avoid changes to row_type_classifier and output_schema_guardrails?** Yes. Neither file was modified. The guardrail contract is unchanged (no new forbidden row_type).

9. **Are tests specific enough and not over-broad?** Yes. Each test isolates one signal; they cover all 7 R7S-required scenarios plus 3 boundary protections (strong-evidence scoping, label-alone non-blocking, mixed dash/numeric). They do not over-mock or assert unrelated behavior.

10. **Are there any false-positive risks, especially for text-valued financial facts?** Low and acceptable. An all-text-valued strict row would route to REVIEW_REQUIRED, which is the conservative correct behavior under "宁可进 review，不轻易进 clean". No numeric fact row is blocked. The observed Taihao all-text rows are scaffolding, not facts.

11. **Is a Taihao pilot rerun recommended as a later separate task?** Yes. The rerun should confirm scaffolding rows (市场数据/厂商/对比维度/项目/指标/订单日期) move to review_queue, clean_data_row_count drops from 92, no new guardrail failure, and no regression in Linyang/Anjing families.

---

## Decision

`348N_R7S_QA_CONFIRMED_STRICT_TABLE_SCAFFOLDING_GUARD_VALID`

The R7S implementation is independently confirmed valid:
- it implements the R7R recommendation as a narrower clean-candidate policy, not a new row type;
- the guard is correctly scoped to weak-evidence strict-table rows that would otherwise enter clean_data;
- scaffolding / pseudo-header / comparison-dimension rows route to REVIEW_REQUIRED;
- normal numeric fact rows, mixed dash/numeric rows, MARKET_REFERENCE_ROW, and qualitative_facts behavior are all preserved;
- row_type_classifier and output_schema_guardrails were not modified;
- tests are specific and pass (86 passed in tests/agent);
- the full-suite failures (33) are all pre-existing legacy failures unrelated to R7S;
- no readiness gate, export behavior, or guardrail contract was weakened.

---

## Recommended next task

```text
348N-R7T Taihao strict_table scaffolding clean-boundary pilot rerun
```

Purpose:

- rerun the Taihao pilot under the committed R7S policy;
- confirm scaffolding rows (市场数据 / 厂商 / 对比维度 / 项目 / 指标 / 订单日期) move to review_queue;
- confirm clean_data_row_count drops from 92 by the number of scaffolding rows;
- confirm no new output guardrail failure;
- confirm Linyang and Anjing workbook families do not regress;
- keep all readiness gates closed.

This is a separate task. This QA task does not start the rerun.

---

## Data Result / 数据结果

```text
Decision（任务结论）= 348N_R7S_QA_CONFIRMED_STRICT_TABLE_SCAFFOLDING_GUARD_VALID
build_result（构建结果）= COMPILE_OK
test_result（测试结果）= tests/agent 86 passed; tests (full) 33 failed / 445 passed (33 failures all pre-existing legacy, unrelated to R7S)
files_modified（修改文件数）= 0 (QA task; 1 QA report created, no code/test changes)
error_count（错误数）= 0 (no new failures introduced by R7S)
boundary_check（边界检查）= passed (only the allowed QA report created; no code/test/output/input/temp/data/legacy/config/guardrails/row_type_classifier/qualitative_facts/MARKET_REFERENCE_ROW/readiness-gate changes)
qa_result（QA结果）= VALID
recommended_next_task（推荐下一任务）= 348N-R7T Taihao strict_table scaffolding clean-boundary pilot rerun
```
