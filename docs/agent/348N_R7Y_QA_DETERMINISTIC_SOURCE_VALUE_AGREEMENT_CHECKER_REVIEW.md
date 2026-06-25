# 348N-R7Y-QA deterministic source-value agreement checker review

## Task ID

```text
348N-R7Y-QA deterministic source-value agreement checker review
```

## Recommended reasoning level used

```text
recommended_reasoning_level = max
reason = R7Y-QA reviews VERIFIED / DISAGREED evidence-agreement semantics. A false pass can pollute future evidence_strength and readiness interpretation.
```

## Preflight

```text
git status -sb (before pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating 973ff68..ee59b90
  Fast-forward
   docs/agent/项目进程.md                                      | 131 +++------
   docs/codex_tasks/348N_R7Y_QA_deterministic_source_value_agreement_checker_review.md | 287 +++++++++++++++++++
   docs/project_handoffs/CURRENT_MODEL_HANDOFF.md               | 128 +++++----
   项目进展大白话说明.md                                        | 317 +++++++--------------
   4 files changed, 499 insertions(+), 364 deletions(-)
   create mode 100644 docs/codex_tasks/348N_R7Y_QA_deterministic_source_value_agreement_checker_review.md

git status -sb (after pull):
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  ee59b90 docs: update handoff after R7Y
  c83677c docs: refresh plain-language progress after R7Y
  a854b93 docs: sync progress after R7Y
  b427de5 docs: add R7Y QA task
  973ff68 feat: add deterministic evidence agreement checker
  ce879c8 docs: update handoff after R7X QA
  724aae2 docs: refresh plain-language progress after R7X QA
  744a106 docs: sync progress after R7X QA
  bee81f9 docs: add R7Y source-value agreement task
  6fb00ec docs: add R7X QA review
  d7737f2 docs: update handoff after R7X
  6069553 docs: refresh plain-language progress after R7X
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
- `docs/codex_tasks/348N_R7Y_QA_deterministic_source_value_agreement_checker_review.md`
- `docs/codex_tasks/348N_R7Y_deterministic_source_value_agreement_checker.md`
- `docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md`
- `docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md`

R7Y implementation and tests reviewed, read-only:

- `datefac_agent/audit/evidence_checker.py`
- `tests/agent/test_agent_excel_intake_audit_348a.py`

Boundary interaction files reviewed, read-only:

- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`
- `datefac_agent/review/clean_candidate_policy.py`

## Agreement checker review

R7Y implementation under review:

```text
commit = 973ff68 feat: add deterministic evidence agreement checker
```

Core API reviewed:

```python
classify_agreement_status(
    row: SpreadsheetRow,
    evidence_refs: list[EvidenceRef],
    source_text: str | None = None,
) -> EvidenceAgreementStatus
```

QA answers:

1. **No provenance remains `MISSING`: VALID.** The checker first computes explicit/page provenance using `ref.is_explicit`, `ref.page_number`, or `row.explicit_evidence_ref`. If absent, it returns `MISSING` before looking at `source_text`.
2. **Explicit/page provenance without source text remains `UNVERIFIED`: VALID.** If provenance exists and `source_text` is missing/empty, the checker returns `UNVERIFIED`.
3. **Exact numeric source-text match becomes `VERIFIED`: VALID.** Tests cover `1234` in row values matching `1234` in source text.
4. **Comma-formatted numeric equivalence becomes `VERIFIED`: VALID.** Tests cover row `1234` matching source `1,234`.
5. **Percentage equivalence is display-value based: VALID.** Tests cover row `12.30%` matching source `12.3%`. The implementation strips `%` and compares `Decimal("12.30") == Decimal("12.3")`; it does not convert to `0.123`.
6. **Parenthesized negative equivalence becomes `VERIFIED`: VALID.** Tests cover row `-123` matching source `(123)`.
7. **Numeric mismatch becomes `DISAGREED` only when deterministic mismatch is proven: VALID.** The checker returns `DISAGREED` only after provenance exists, source text exists, row numeric values exist, source numeric tokens exist, and `matched_count == 0`.
8. **Partial multi-period coverage remains conservative: VALID.** If some but not all row numeric values match, `matched_count` is neither full nor zero, so the checker returns `UNVERIFIED`. Tests cover row `[100, 200]` with source containing only `100`.
9. **Text-only / non-numeric facts remain `UNVERIFIED`: VALID.** If no numeric period values are found, the checker returns `UNVERIFIED`. Tests cover text values `基础数据` / `数值`.
10. **Production pipeline remains `UNVERIFIED` unless source text is supplied: VALID.** `build_row_audit_result(...)` calls `classify_agreement_status(row, list(evidence_refs))` without `source_text`, so explicit/page provenance remains `UNVERIFIED` in normal row-building.

QA result: **VALID**. R7Y introduces `VERIFIED` / `DISAGREED` only through deterministic numeric source-text comparison and keeps source-text absence conservative.

## Numeric normalization review

Reviewed helpers:

```python
_normalize_numeric_value(value: object) -> Decimal | None
_extract_numeric_tokens(text: str) -> set[Decimal]
_numeric_period_values(row: SpreadsheetRow) -> list[Decimal]
```

Supported forms confirmed:

```text
1234
1,234
1234.56
1,234.56
-123
(123)
12.3%
12.30%
```

Conservative behavior confirmed:

- `None`, bool, empty text, dash-like placeholders, and non-numeric text normalize to `None`.
- Text-valued facts do not become `VERIFIED`.
- Percent values are compared as displayed numeric values, not converted into ratios.
- Parenthesized numeric tokens are normalized as negative values.
- `Decimal` equality avoids trailing-zero mismatch such as `12.30` vs `12.3`.

Unsafe false-positive risk review:

- **Known limitation / future risk:** row-level token-set matching does not bind values to individual period labels or source table coordinates. If source text includes all row numbers but in an unrelated nearby context, R7Y can return `VERIFIED`. This is acceptable for R7Y because the task is explicitly row-level first, but future R7Z should consider period-aware or value-level provenance before using agreement for stronger evidence semantics.
- **Known limitation / future risk:** duplicate repeated numeric values are counted independently against a set of source tokens. For exact duplicate row values, one source token can satisfy repeated values. This is conservative enough for current unit tests but should be revisited if value-level coverage becomes required.
- **No current boundary violation found:** these risks do not cause partial coverage, text-only facts, or missing source text to become `VERIFIED` under current implementation.

QA result: **VALID with noted future precision risks**.

## Evidence level behavior review

Reviewed `classify_evidence_level(...)` in `datefac_agent/audit/evidence_checker.py`.

Findings:

- R7Y did not change evidence level promotion logic.
- Explicit/page provenance with complete lineage still returns `WEAK_EVIDENCE`.
- `VERIFIED` agreement status is not mapped to `STRONG_EVIDENCE`.
- R7Y tests explicitly check that a row can produce `VERIFIED` from `classify_agreement_status(...)` while `evidence_level` remains `WEAK_EVIDENCE`.

QA result: **VALID**.

## Boundary policy review

### MARKET_REFERENCE_ROW

Reviewed `datefac_agent/review/clean_candidate_policy.py`:

```python
if result.row_type == "MARKET_REFERENCE_ROW":
    return "REVIEW_REQUIRED"
```

R7Y did not modify this policy. R7Y tests confirm a market reference row remains `REVIEW_REQUIRED` even when direct checker invocation returns `VERIFIED` for supplied source text.

Result: **unchanged / valid**.

### qualitative_facts admission

Reviewed tests and row-type policy coverage. `qualitative_facts` rows remain `TESTSET_SUPPORTING_ROW` / `REVIEW_REQUIRED` in existing tests, with explicit page references parsed but agreement status staying `UNVERIFIED` in production row-building because no source text is supplied.

R7Y did not broaden qualitative_facts admission.

Result: **unchanged / valid**.

### R7S strict-table scaffolding guard

Reviewed `clean_candidate_policy.py` and R7S tests. R7S guard remains based on strict-table row type plus period value shape and scaffolding checks. R7Y did not change this policy.

Existing tests still cover:

- pseudo-header rows such as `市场数据`, `项目`, `指标` do not enter clean_data when period values are non-numeric or echo labels;
- numeric fact rows preserve clean admission;
- explicit page provenance does not bypass the scaffolding guard.

Result: **unchanged / valid**.

### clean admission separation

`classify_clean_candidate(...)` does not reference `agreement_status`. Therefore `VERIFIED` cannot automatically enter clean_data through current clean admission policy.

Result: **valid**.

## Readiness gates review

Reviewed readiness behavior in `tools/run_agent_excel_intake_audit_348a.py` through tests and manifest construction. Gates remain closed:

```text
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
```

R7Y tests include `test_r7y_manifest_readiness_gates_remain_closed`, confirming no readiness gate opened.

Result: **valid / closed**.

## Test review

R7Y test coverage added in `tests/agent/test_agent_excel_intake_audit_348a.py` covers:

```text
No explicit evidence -> MISSING
Explicit page ref without source text -> UNVERIFIED
Exact numeric value -> VERIFIED
Comma-formatted equivalent -> VERIFIED
Percentage equivalent -> VERIFIED
Parenthesized negative equivalent -> VERIFIED
Numeric mismatch -> DISAGREED
Partial multi-period coverage -> UNVERIFIED
Text-valued facts -> UNVERIFIED
VERIFIED does not change evidence_level or MARKET_REFERENCE_ROW policy
Readiness gates remain closed
```

R7X parser behavior remains covered by existing tests for Chinese/English page refs, page ranges, unparseable refs, missing explicit refs, evidence index serialization, and `UNVERIFIED` not becoming `STRONG_EVIDENCE`.

R7S clean-boundary behavior remains covered by existing strict-table scaffolding guard tests.

Validation result:

```text
pytest tests/agent -q
106 passed in 0.58s
```

QA result: **VALID**.

## Compatibility risk review

Compatibility findings:

- `EvidenceAgreementStatus` already included `VERIFIED` and `DISAGREED`, so R7Y did not require schema expansion.
- `AuditRowResult.agreement_status` has a default of `MISSING`.
- Evidence index serialization already includes `agreement_status` and remains compatible.
- `build_row_audit_result(...)` still calls the checker without `source_text`, preserving current production behavior as `UNVERIFIED` for explicit provenance.
- Review queue rows do not currently serialize `agreement_status`; this is not a regression from R7Y but may be a future delivery UX improvement if reviewers need to see VERIFIED/DISAGREED in queue CSV.
- Main compatibility risk is semantic, not technical: downstream code must not interpret `VERIFIED` as `STRONG_EVIDENCE`, clean admission, or readiness. Current code does not do so.

QA result: **VALID with future delivery-display consideration**.

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
  ........................................................................ [ 67%]
  ..................................                                       [100%]
  106 passed in 0.58s
```

```text
git status -sb
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation
  ?? docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
```

```text
git diff --stat
  no tracked diff output; only the new untracked QA report is present
```

```text
git diff --name-only
  no tracked diff output; only the new untracked QA report is present
```

```text
git diff --check
  passed, no output
```

## Decision

```text
Decision = 348N_R7Y_QA_CONFIRMED_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_VALID
```

R7Y passes QA. `VERIFIED` and `DISAGREED` are introduced safely within the task scope:

```text
VERIFIED = deterministic full numeric source-value coverage
DISAGREED = deterministic numeric mismatch with zero matching row values
partial coverage = UNVERIFIED
text-only facts = UNVERIFIED
no source_text = UNVERIFIED
VERIFIED != STRONG_EVIDENCE
VERIFIED != clean admission
VERIFIED != production readiness
```

## Recommended next task

Recommended next task should remain non-production. Prefer one of:

```text
348N-R7Z source_text integration design / evidence index wiring
```

or, if the project wants more conservative hardening first:

```text
348N-R7Z targeted fixture coverage for deterministic agreement checker edge cases
```

Suggested focus for R7Z: decide whether to add period-aware/value-level source-text matching before any future evidence-level promotion uses `VERIFIED`.

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，R7Y deterministic source-value agreement checker QA valid
build_result（构建结果）= PASS，py_compile 全部通过
test_result（测试结果）= PASS，pytest tests/agent -q => 106 passed in 0.58s
files_modified（修改文件数）= 1，only this QA report
error_count（错误数）= 0
boundary_check（边界检查）= PASS，未修改代码/测试/output/input/temp/data/legacy/config/dependencies；仅创建允许的 R7Y-QA report
agreement_checker_result（一致性检查器结果）= PASS，MISSING/UNVERIFIED/VERIFIED/DISAGREED 语义保守且确定性
verified_status_result（VERIFIED状态结果）= PASS，仅 full numeric coverage 产生 VERIFIED；partial/text-only/no source_text 不会 VERIFIED
disagreed_status_result（DISAGREED状态结果）= PASS，仅 source text 有 numeric tokens 且 row numeric values 完全无匹配时产生 DISAGREED
strong_evidence_claim_result（强证据声明结果）= PASS，VERIFIED 未自动变成 STRONG_EVIDENCE
readiness_gates（就绪门）= CLOSED，demo_export_only=true，formal_client_export_allowed=false，client_ready=false，production_ready=false
qa_result（QA结果）= VALID
recommended_next_task（推荐下一任务）= R7Z source_text integration design / evidence index wiring, or targeted fixture coverage for agreement checker edge cases
```
