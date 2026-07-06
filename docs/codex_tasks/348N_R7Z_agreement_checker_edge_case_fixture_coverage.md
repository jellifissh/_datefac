# 348N-R7Z agreement checker edge-case fixture coverage

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = This task hardens deterministic agreement semantics after R7Y-QA. Unsafe false positives in VERIFIED / DISAGREED would pollute future evidence_strength and readiness interpretation before source_text is wired into the real pipeline.
```

## Task Goal

Implement targeted fixture coverage and, only if required by failing tests, a minimal conservative fix for deterministic source-value agreement edge cases.

Task ID:

```text
348N-R7Z agreement checker edge-case fixture coverage
```

This is an implementation + tests task, but the preferred change is test-first and minimal.

Goal:

1. Add targeted tests for edge cases called out by R7Y-QA.
2. Ensure row-level numeric token matching does not overclaim `VERIFIED` in unsafe ambiguity cases.
3. Preserve the R7Y conservative agreement semantics.
4. Do not wire source_text into the real pipeline yet.
5. Do not run workbook reruns, MinerU, OCR, LLM, or VLM.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If the worktree is not clean after pull, stop and report.

---

## Required Read Order

Read these files first:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/codex_tasks/348N_R7Y_QA_deterministic_source_value_agreement_checker_review.md
docs/codex_tasks/348N_R7Y_deterministic_source_value_agreement_checker.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
```

Inspect current implementation before editing:

```text
datefac_agent/audit/evidence_checker.py
tests/agent/test_agent_excel_intake_audit_348a.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/review/clean_candidate_policy.py
```

---

## Background

R7Y-QA validated the deterministic agreement checker, but noted future precision risks:

```text
row-level token matching is not yet period-aware or coordinate-aware
duplicate numeric values are matched against a source token set
```

These were not R7Y boundary failures, but they must be hardened before wiring source_text into the real pipeline.

R7Z therefore focuses on edge-case fixtures and conservative behavior, not production integration.

---

## Allowed Scope

Allowed implementation files, only if needed:

```text
datefac_agent/audit/evidence_checker.py
```

Allowed test files:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

If adding a small dedicated tests/agent evidence test file is cleaner, it is allowed, but explain why.

Do not modify docs in this task.

Do not modify schemas unless a test proves schema change is strictly required. It should not be required.

---

## Forbidden Actions

Do not modify:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/
input/
output/
temp/
data/
legacy datefac/
dependencies
config files
```

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not wire source_text into the real intake/audit pipeline.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change R7S strict-table scaffolding guard.

Do not change output_schema_guardrails.

Do not change readiness gates.

Do not claim:

```text
client_ready = true
production_ready = true
formal_client_export_allowed = true
```

Do not stage or commit output files.

Do not use broad Git staging.

---

## Test Requirements

Add compact tests for the following edge cases.

### 1. Duplicate source token should not satisfy duplicate row values unsafely

If a row has two numeric period values that are the same value, and source_text has only one matching numeric occurrence, the safest result should be conservative unless the checker explicitly tracks multiplicity.

Preferred result:

```text
UNVERIFIED
```

### 2. Multi-period partial coverage remains UNVERIFIED

If source_text matches one period value but not another, result must remain:

```text
UNVERIFIED
```

### 3. Source text with many unrelated numbers must not produce false VERIFIED

If source_text contains many numeric tokens and only accidentally includes one row value while missing other row values, result must remain:

```text
UNVERIFIED
```

### 4. Full mismatch remains DISAGREED only when source text has numeric tokens and none match

If source_text has numeric tokens and no row numeric period value matches, result may be:

```text
DISAGREED
```

### 5. No source numeric tokens remains UNVERIFIED

If source_text exists but contains no numeric tokens, result should be:

```text
UNVERIFIED
```

### 6. Text-only facts remain UNVERIFIED

Text-valued / non-numeric facts must not become VERIFIED.

### 7. Existing R7Y tests still pass

Existing verified, disagreed, partial, percent, comma, and negative tests must still pass.

### 8. Existing R7X and R7S behavior still passes

Page parser behavior and strict-table clean-boundary behavior must remain unchanged.

---

## Conservative Fix Guidance

If tests show the current implementation overclaims `VERIFIED`, make the smallest conservative fix.

Acceptable minimal approaches include:

```text
track numeric token multiplicity rather than set membership
require every row numeric value occurrence to have a corresponding source numeric token occurrence
keep partial / ambiguous cases UNVERIFIED
```

Do not implement period-aware or coordinate-aware matching in R7Z unless it can be done extremely narrowly and safely. Prefer documenting that as a future design task.

Do not broaden `VERIFIED` behavior.

Do not map `VERIFIED` to `STRONG_EVIDENCE`.

Do not map `VERIFIED` to clean admission.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

If `pytest tests/agent -q` fails, report the full failure and whether it is caused by R7Z.

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Output

Final execution report must include:

```text
Recommended reasoning level used
Preflight
Files modified
Edge-case tests added
Agreement checker behavior before/after
Conservative fixes applied, if any
Validation outputs
Whether VERIFIED false-positive risk was reduced
Whether DISAGREED remains conservative
Whether MARKET_REFERENCE_ROW policy changed
Whether qualitative_facts admission changed
Whether readiness gates remain closed
Commit hash
Push result
Final git status
Data Result / 数据结果
```

Data Result must include:

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
edge_case_coverage_result（边界用例覆盖结果）=
verified_false_positive_result（VERIFIED误判风险结果）=
disagreed_status_result（DISAGREED状态结果）=
source_text_integration_result（source_text接入结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. only allowed implementation/test files were modified,
2. validation commands were run and reported,
3. `git diff --name-only` contains only allowed implementation/test files,
4. `git diff --check` is clean,
5. no output/input/temp/data/legacy/config/docs files were modified,

then stage only exact modified files with explicit path staging.

Do not use broad staging commands.

Suggested commit message:

```text
test: add agreement checker edge-case coverage
```

If implementation is changed as well:

```text
fix: make agreement checker multiplicity conservative
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Post-push validation:

```text
git status -sb
git log --oneline -10
```

Stop after push. Do not start the next task.
