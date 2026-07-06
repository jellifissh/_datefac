# 348N-R7Z-QA agreement checker edge-case review

## Task ID

```text
348N-R7Z-QA agreement checker edge-case review
```

## Recommended reasoning level used

```text
recommended_reasoning_level = max
reason = R7Z changed the verified-agreement checker from set membership to multiplicity-aware matching. QA must verify the fix really reduces VERIFIED false positives without making DISAGREED too aggressive or changing clean/readiness boundaries.
```

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 004e307..5890cf8
  Fast-forward
   docs/agent/项目进程.md                                      |  47 ++--
   docs/codex_tasks/348N_R7Z_QA_agreement_checker_edge_case_review.md | 289 +++++++++++++++++++++
   docs/project_handoffs/CURRENT_MODEL_HANDOFF.md               | 100 +++----
   项目进展大白话说明.md                                        | 153 ++++++-----
   4 files changed, 446 insertions(+), 143 deletions(-)
   create mode 100644 docs/codex_tasks/348N_R7Z_QA_agreement_checker_edge_case_review.md

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  5890cf8 docs: update handoff after R7Z
  7814358 docs: refresh plain-language progress after R7Z
  6663f39 docs: sync progress after R7Z
  f8fbf6d docs: add R7Z QA task
  004e307 fix: make agreement checker multiplicity conservative
  eb2e355 docs: update handoff after R7Y QA
  39fd02e docs: refresh plain-language progress after R7Y QA
  c4dcaaf docs: sync progress after R7Y QA
  b201e92 docs: add R7Z agreement checker edge-case task
  4e71f28 docs: add R7Y QA review
  ee59b90 docs: update handoff after R7Y
  c83677c docs: refresh plain-language progress after R7Y
```

Worktree was clean after pull.

## Files reviewed

Required context, read-only:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7Z_QA_agreement_checker_edge_case_review.md`
- `docs/codex_tasks/348N_R7Z_agreement_checker_edge_case_fixture_coverage.md`
- `docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md`
- `docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md`

R7Z implementation and tests reviewed, read-only:

- `datefac_agent/audit/evidence_checker.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

Boundary interaction files reviewed, read-only:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/review/clean_candidate_policy.py`

## Multiplicity fix review

R7Z implementation commit under review:

```text
004e307 fix: make agreement checker multiplicity conservative
```

R7Z changed source numeric token storage from set membership to multiplicity-aware counts:

```python
from collections import Counter

def _extract_numeric_tokens(text: str) -> Counter[Decimal]:
    tokens: Counter[Decimal] = Counter()
    ...
    tokens[number] += 1
```

`classify_agreement_status(...)` now copies and consumes source-token counts while iterating each row numeric value:

```python
matched_count = 0
remaining_source_numbers = source_numbers.copy()
for value in row_numbers:
    if remaining_source_numbers[value] > 0:
        matched_count += 1
        remaining_source_numbers[value] -= 1
```

QA findings:

1. **R7Z reproduced the duplicate-value false positive before the fix: VALID.** The R7Z execution report recorded focused test-first failure: row values `[100, 100]` with only one source `100` returned `VERIFIED` before the fix.
2. **Duplicate row numeric values now require duplicate source occurrences: VALID.** The checker consumes one source occurrence per row value occurrence.
3. **One source occurrence for two identical row values stays `UNVERIFIED`: VALID.** Covered by `test_r7z_duplicate_row_values_need_duplicate_source_occurrences`.
4. **Enough duplicate source occurrences allow `VERIFIED`: VALID.** Covered by `test_r7z_duplicate_row_values_with_enough_source_occurrences_can_verify`.
5. **No broadening of `VERIFIED`: VALID.** The change tightens matching only; it does not add new ways to verify.

QA result: **VALID**.

## Edge-case coverage review

R7Z added compact tests in `tests/agent/test_agent_excel_intake_audit_348a.py` for:

```text
- duplicate row values with one source occurrence -> UNVERIFIED
- duplicate row values with enough source occurrences -> VERIFIED
- incomplete coverage with many unrelated standalone numeric tokens -> UNVERIFIED
- full mismatch with unrelated standalone numeric tokens -> DISAGREED
- source text with no numeric tokens -> UNVERIFIED
```

Existing R7Y tests still cover:

```text
- exact numeric match -> VERIFIED
- comma-formatted equivalent -> VERIFIED
- percentage equivalent -> VERIFIED
- parenthesized negative equivalent -> VERIFIED
- numeric mismatch -> DISAGREED
- partial multi-period coverage -> UNVERIFIED
- text-valued / non-numeric facts -> UNVERIFIED
- VERIFIED does not change evidence_level or MARKET_REFERENCE_ROW policy
- readiness gates remain closed
```

Existing R7X/R7S tests still cover:

```text
- page-number parser behavior
- UNVERIFIED page provenance does not claim STRONG_EVIDENCE
- strict-table scaffolding rows remain out of clean_data
```

QA result: **VALID**.

## Agreement checker behavior review

The current agreement checker preserves the R7Y/R7Z semantics:

```text
No explicit/page provenance -> MISSING
Explicit/page provenance without source_text -> UNVERIFIED
No row numeric values -> UNVERIFIED
No source numeric tokens -> UNVERIFIED
Every row numeric value occurrence has a matching source numeric occurrence -> VERIFIED
No row numeric values match source numeric tokens -> DISAGREED
Some but not all row numeric values match -> UNVERIFIED
```

QA question answers:

- Partial multi-period coverage remains `UNVERIFIED`: **VALID**.
- Source text with many unrelated numeric tokens avoids false `VERIFIED` when coverage is incomplete: **VALID**.
- Full mismatch with unrelated standalone numeric tokens remains `DISAGREED` only when no row values match: **VALID**.
- Source text with no numeric tokens remains `UNVERIFIED`: **VALID**.
- Text-only / non-numeric facts remain `UNVERIFIED`: **VALID**.
- R7Z avoided period-aware or coordinate-aware matching changes: **VALID**. This remains future work.
- R7Z avoided source_text integration into the real pipeline: **VALID**. `build_row_audit_result(...)` still calls `classify_agreement_status(row, list(evidence_refs))` without source text.

QA result: **VALID**.

## Boundary policy review

### Evidence level

Reviewed `classify_evidence_level(...)`. R7Z did not change evidence-level classification. Explicit/page provenance remains `WEAK_EVIDENCE`, not `STRONG_EVIDENCE`, unless a future designed promotion path changes it.

Result: **VALID**.

### Clean admission

Reviewed `classify_clean_candidate(...)`. Clean admission still does not reference `agreement_status`. `VERIFIED` cannot automatically enter clean_data through current policy.

Result: **VALID**.

### MARKET_REFERENCE_ROW

Reviewed `clean_candidate_policy.py`:

```python
if result.row_type == "MARKET_REFERENCE_ROW":
    return "REVIEW_REQUIRED"
```

R7Z did not change this policy. Existing tests still assert market reference rows remain `REVIEW_REQUIRED`.

Result: **VALID / unchanged**.

### qualitative_facts admission

R7Z did not touch qualitative_facts classification or admission. Existing tests still keep qualitative_facts rows as `TESTSET_SUPPORTING_ROW` / `REVIEW_REQUIRED`.

Result: **VALID / unchanged**.

### R7S strict-table scaffolding guard

R7Z did not modify strict-table scaffolding logic. Existing R7S tests still pass under the full `tests/agent` run.

Result: **VALID / unchanged**.

## Readiness gates review

R7Z did not modify manifest/readiness logic. Tests still cover closed gates, and output guardrail tests still reject open gates.

Current required defaults remain:

```text
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
```

QA result: **VALID / CLOSED**.

## Test review

Validation confirms all R7X / R7Y / R7Z tests pass together:

```text
pytest tests/agent -q
111 passed in 0.68s
```

This includes the new R7Z edge-case tests, existing R7Y agreement-status tests, R7X page parsing tests, R7S clean-boundary tests, qualitative_facts tests, and output guardrail tests.

QA result: **VALID**.

## Compatibility risk review

`Counter[Decimal]` compatibility review:

- Uses only Python standard library `collections.Counter`.
- Keeps Decimal normalization semantics from R7Y.
- Does not change public schema types.
- Does not change `EvidenceAgreementStatus` values.
- Does not change evidence index serialization shape.
- Does not require source_text to be present in production row-building.
- Tightens matching by requiring one source occurrence per row numeric occurrence.

Residual risk:

```text
row-level matching is still not period-aware or coordinate-aware
```

That limitation is explicit, unchanged, and should be handled before future source-text pipeline wiring or evidence-level promotion depends on `VERIFIED`.

QA result: **VALID with known future design limitation**.

## Validation outputs

```text
D:\anaconda\python.exe -m py_compile datefac_agent/review/clean_candidate_policy.py
  passed, no output
```

```text
D:\anaconda\python.exe -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  passed, no output
```

```text
D:\anaconda\python.exe -m pytest tests/agent -q
  ........................................................................ [ 64%]
  .......................................                                  [100%]
  111 passed in 0.68s
```

```text
git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
```

```text
git diff --stat
  no output
```

```text
git diff --name-only
  no output
```

```text
git diff --check
  passed, no output
```

## Decision

```text
Decision = 348N_R7Z_QA_CONFIRMED_MULTIPLICITY_AWARE_AGREEMENT_CHECKER_VALID
```

R7Z passes QA. The multiplicity-aware fix reduces the specific duplicate numeric value `VERIFIED` false-positive risk without making `DISAGREED` too aggressive and without changing source-text wiring, evidence level, clean admission, MARKET_REFERENCE_ROW policy, qualitative_facts admission, R7S guardrails, output guardrails, or readiness gates.

## Recommended next task

Recommended next task remains non-production. Prefer:

```text
348N-R7AA source_text integration design / evidence index wiring design
```

The design should decide how source text is represented, how it is trusted, and whether period-aware/value-level provenance is required before any future evidence-level promotion uses `VERIFIED`.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7Z-QA confirms multiplicity-aware agreement checker is valid
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 111 passed in 0.68s
files_modified（修改文件数）= 1，only this QA report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7Z-QA report
edge_case_coverage_result（边界用例覆盖结果）= PASS，duplicate values / unrelated numeric tokens / no numeric tokens / text-only / partial coverage 均有覆盖
verified_false_positive_result（VERIFIED误判风险结果）= REDUCED，duplicate row values now require duplicate source occurrences
disagreed_status_result（DISAGREED状态结果）= PASS，DISAGREED 仍只在有 source numeric tokens 且 no row numeric values match 时产生；partial coverage 仍为 UNVERIFIED
source_text_integration_result（source_text接入结果）= NOT_CHANGED，未接入真实 pipeline
qa_result（QA结果）= VALID
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
recommended_next_task（推荐下一任务）= R7AA source_text integration design / evidence index wiring design
```
