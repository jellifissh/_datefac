# 348N-R7Y deterministic source-value agreement checker

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = This task touches the meaning of VERIFIED / DISAGREED evidence agreement. It affects future evidence_strength and readiness interpretation, so it must be conservative, deterministic, and tightly scoped.
```

## Task Goal

Implement the next evidence-strengthening slice after R7X and R7X-QA.

Task ID:

```text
348N-R7Y deterministic source-value agreement checker / evidence agreement verification slice
```

Goal:

1. Add a deterministic source-value agreement checker for rows with parsed page provenance.
2. Populate `agreement_status = VERIFIED` only when structured numeric values are deterministically found in trusted source evidence text.
3. Populate `agreement_status = DISAGREED` only when deterministic comparison proves disagreement.
4. Preserve conservative defaults: unavailable or insufficient source text remains `UNVERIFIED`.
5. Keep evidence level, clean admission, and readiness gates separate.

This task is implementation + tests.

This task must not run MinerU, OCR, LLM, or VLM.

This task must not declare production readiness.

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
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
docs/codex_tasks/348N_R7X_QA_evidence_provenance_parsing_review.md
docs/codex_tasks/348N_R7X_evidence_provenance_parsing_page_number_agreement_status.md
```

Inspect current evidence/provenance implementation before editing:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Search for existing source/evidence text fields, evidence_index fields, PDF text extraction artifacts, and manifest fields before adding anything new.

---

## Key Semantics

R7X-QA confirmed:

```text
page_number parsed = provenance anchor exists
agreement_status = UNVERIFIED = source-value agreement not checked yet
UNVERIFIED provenance remains WEAK_EVIDENCE
parsed page_number does not automatically become VERIFIED or STRONG_EVIDENCE
```

R7Y may introduce `VERIFIED` / `DISAGREED`, but only with deterministic source-value agreement logic.

Do not turn `VERIFIED` into production readiness.

Do not turn `VERIFIED` into automatic clean admission.

Separate these concepts:

```text
evidence_strength
agreement_status
clean_admission
review_required
export_readiness
production_readiness
```

---

## Allowed Scope

Expected allowed implementation files include only the minimum required files, likely:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
```

Allowed test scope:

```text
tests/agent/
```

If another existing implementation file is clearly the right home for agreement checking, use it only if necessary and explain why.

Do not modify docs except this task report is not required in this implementation task.

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

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change R7S strict-table scaffolding guard.

Do not change output_schema_guardrails unless you stop and explain why R7Y cannot proceed without doing so.

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

## Implementation Requirements

### 1. Agreement checker API

Add or reuse a deterministic helper with semantics like:

```text
classify_agreement_status(row, evidence_refs, source_text=None) -> EvidenceAgreementStatus
```

The exact signature may follow existing project style.

Required behavior:

```text
No explicit/page provenance -> MISSING
Explicit/page provenance but no source text available -> UNVERIFIED
Explicit/page provenance + source text contains all required normalized numeric values -> VERIFIED
Explicit/page provenance + source text exists but deterministic numeric comparison proves mismatch -> DISAGREED
Ambiguous / partial / non-numeric-only / unsupported text -> UNVERIFIED
```

R7Y should be row-level first. Do not implement broad PDF/OCR extraction.

### 2. Numeric normalization

Implement deterministic numeric token normalization sufficient for common financial values:

```text
1,234
1234
1,234.56
1234.56
-123
(123)
12.3%
12.30%
```

Do not over-normalize text-valued facts.

Do not treat approximate textual statements as verified.

If value comparison is ambiguous, return `UNVERIFIED`, not `VERIFIED`.

### 3. Source text input

Use existing evidence/source text fields if present.

If the current pipeline does not yet carry source PDF page text, implement the checker so tests can call it directly with `source_text`, while production row-building remains `UNVERIFIED` until real source text is supplied.

Do not run OCR/PDF extraction to get source text in this task.

### 4. Evidence level behavior

Do not automatically change evidence level to `STRONG_EVIDENCE` just because `agreement_status = VERIFIED`, unless current project design already supports that safely.

Preferred conservative behavior for R7Y:

```text
agreement_status can become VERIFIED / DISAGREED in the model
EvidenceLevel remains governed by existing conservative classification unless explicitly designed otherwise
clean admission remains separate
readiness gates remain closed
```

If you decide to map `VERIFIED` to `STRONG_EVIDENCE`, stop and justify with tests and docs-level reasoning before doing it. Default is: do not do it.

### 5. Serialization

Ensure `agreement_status` continues to serialize in evidence_index outputs.

No existing output artifacts should be modified or committed.

---

## Test Requirements

Add compact tests covering:

1. No explicit evidence -> `MISSING`.
2. Explicit page ref but no source text -> `UNVERIFIED`.
3. Source text contains exact numeric value -> `VERIFIED`.
4. Source text contains comma-formatted equivalent value -> `VERIFIED`.
5. Source text contains percentage equivalent -> `VERIFIED`.
6. Source text contains negative value equivalent, including parentheses if supported -> `VERIFIED`.
7. Source text has numeric mismatch -> `DISAGREED`.
8. Source text has partial coverage for multi-period row -> `UNVERIFIED` or conservative non-verified result.
9. Text-valued / non-numeric facts remain `UNVERIFIED`, not `VERIFIED`.
10. `VERIFIED` does not automatically open readiness gates.
11. `VERIFIED` does not change MARKET_REFERENCE_ROW policy.
12. R7X parser tests still pass.
13. R7S clean-boundary tests still pass.

Prefer extending existing `tests/agent/test_agent_excel_intake_audit_348a.py` only if it remains manageable. If a small dedicated evidence test file is cleaner under `tests/agent/`, create one there.

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

If `pytest tests/agent -q` fails, report the full failure and whether it is caused by R7Y.

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Output

Final execution report must include:

```text
Recommended reasoning level used
Preflight
Files modified
Agreement checker implementation summary
Numeric normalization summary
Evidence level behavior before/after
Tests added/modified
Validation outputs
Whether VERIFIED/DISAGREED were introduced safely
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
agreement_checker_result（一致性检查器结果）=
verified_status_result（VERIFIED状态结果）=
disagreed_status_result（DISAGREED状态结果）=
strong_evidence_claim_result（强证据声明结果）=
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

then stage only exact modified files with explicit `git add <path>` commands.

Do not use broad staging commands.

Suggested commit message:

```text
feat: add deterministic evidence agreement checker
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
