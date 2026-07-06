# 348N-R7AB source_text availability / evidence index wiring implementation

## Recommended reasoning level

```text
recommended_reasoning_level = max
reason = This task introduces the first implementation slice for source_text availability metadata and checker-call-time injection. It must preserve conservative UNVERIFIED defaults and must not turn source_text presence into readiness, clean admission, or STRONG_EVIDENCE.
```

## Task Goal

Implement the first narrow source_text availability and evidence-index wiring slice designed by R7AA.

Task ID:

```text
348N-R7AB source_text availability / evidence index wiring implementation
```

This is an implementation + tests task.

This task must not run workbook reruns.

This task must not run MinerU, OCR, LLM, or VLM.

This task must not wire a broad PDF extraction pipeline.

This task must not open readiness gates.

---

## Background

R7AA concluded:

```text
Current active pipeline has no trusted production source_text carrier.
Existing Excel fields are provenance hints / workbook-side extracted fields, not trusted source evidence text.
A trusted source_text sidecar/index should be separate, provenance-tied, and optional.
Missing / untrusted / mismatched source_text must keep agreement_status UNVERIFIED.
```

R7AA recommended a minimal implementation slice:

```text
add a small source_text sidecar/index model
add deterministic source_text selection by source_id/page_number/locator
pass selected trusted source_text into classify_agreement_status
serialize source_text availability metadata in evidence_index
add compact agreement/source_text fields to review_queue
keep source_text optional and default behavior unchanged
```

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
docs/agent/348N_R7AA_SOURCE_TEXT_INTEGRATION_DESIGN_EVIDENCE_INDEX_WIRING.md
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

Inspect current implementation before editing:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/intake/excel_intake.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/audit/output_schema_guardrails.py
datefac_agent/review/clean_candidate_policy.py
tests/agent/test_agent_excel_intake_audit_348a.py
tools/run_agent_excel_intake_audit_348a.py
```

---

## Required Implementation Semantics

### 1. Add a source_text sidecar/index contract

Add a minimal internal model or dataclass for trusted source text records. Use the project style and simplest stable location.

Conceptual fields:

```text
source_text_id
source_document_id
page_number
locator
text_kind
text
text_sha256
char_count
trusted_source
extraction_method
```

A narrower field set is acceptable if tests prove it covers the contract.

Required rule:

```text
Do not store full source_text in evidence_index or review_queue by default.
```

### 2. Add deterministic source_text selection

Implement a helper that selects source_text only when binding is safe:

```text
row/evidence_refs contain explicit page provenance
parsed page_number is not None
source_text.source_document_id matches EvidenceRef.source_id
source_text.page_number matches EvidenceRef.page_number
source_text.trusted_source is true
source_text.text is non-empty
locator is compatible when locator is available
```

If any condition fails, no source_text is selected.

### 3. Inject source_text into agreement checker only when selected

When trusted source_text is selected, pass it into:

```text
classify_agreement_status(row, evidence_refs, source_text=...)
```

When not selected, preserve existing behavior:

```text
classify_agreement_status(row, evidence_refs)
```

This means default production behavior must remain UNVERIFIED unless a trusted source_text sidecar is explicitly provided.

### 4. Evidence index metadata

Add source_text availability metadata to evidence_index rows.

Recommended fields:

```text
source_text_status
source_text_id
source_text_source_id
source_text_page_number
source_text_locator
source_text_kind
source_text_sha256
source_text_char_count
source_text_used_for_agreement
source_text_unavailable_reason
```

Do not serialize full source_text.

### 5. Review queue compact fields

If review_queue builder has a stable schema path, add compact fields such as:

```text
agreement_status
source_text_status
source_text_page_number
source_text_locator
source_text_unavailable_reason
```

If adding review_queue fields would destabilize existing tests or output contract, implement evidence_index metadata first and document review_queue additions as deferred. Prefer safety over broad CSV churn.

### 6. No readiness or clean admission changes

Do not change:

```text
evidence_level promotion
clean_candidate_policy
MARKET_REFERENCE_ROW policy
qualitative_facts admission
readiness gates
```

`VERIFIED` must remain separate from `STRONG_EVIDENCE`, clean admission, and production readiness.

---

## Test Requirements

Add compact tests covering:

1. No sidecar source_text provided -> existing UNVERIFIED behavior preserved.
2. Trusted sidecar source_text with matching source_id/page_number -> checker receives source_text and can produce VERIFIED.
3. Trusted sidecar source_text with matching source_id/page_number but numeric mismatch -> can produce DISAGREED.
4. Source_text source_id mismatch -> UNVERIFIED and source_text not used.
5. Source_text page_number mismatch -> UNVERIFIED and source_text not used.
6. Untrusted source_text -> UNVERIFIED and source_text not used.
7. Empty source_text -> UNVERIFIED and source_text not used.
8. Evidence_index metadata serializes source_text_status and hash/metadata, not full text.
9. Source_text missing/unavailable reason is explicit and deterministic.
10. VERIFIED still does not become STRONG_EVIDENCE.
11. VERIFIED still does not change MARKET_REFERENCE_ROW policy.
12. Readiness gates remain closed.
13. Existing R7X/R7Y/R7Z tests still pass.

---

## Allowed Scope

Allowed implementation files may include only the minimum necessary subset of:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/schemas/audit_models.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/evidence_index_writer.py
tools/run_agent_excel_intake_audit_348a.py
```

Allowed tests:

```text
tests/agent/
```

Do not modify docs in this task.

Do not modify input/output/temp/data/legacy/config/dependencies.

---

## Forbidden Actions

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not add a PDF extraction pipeline.

Do not treat Excel raw fields such as `value_text_original`, `source_page`, `来源页`, `页码`, or `摘录/说明` as trusted source_text.

Do not serialize full source_text into evidence_index or review_queue by default.

Do not change clean admission.

Do not change evidence_level promotion.

Do not change readiness gates.

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

Do not use broad Git staging.

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

If `pytest tests/agent -q` fails, report the full failure and whether it is caused by R7AB.

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Output

Final execution report must include:

```text
Recommended reasoning level used
Preflight
Files modified
Source text model/contract summary
Source text selection behavior
Agreement checker injection behavior
Evidence index metadata changes
Review queue changes, or explicit deferral reason
Tests added/modified
Validation outputs
Whether default behavior remains UNVERIFIED without trusted source_text
Whether full source_text is excluded from serialized outputs
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
source_text_contract_result（source_text契约结果）=
source_text_selection_result（source_text选择结果）=
agreement_injection_result（一致性检查注入结果）=
evidence_index_wiring_result（证据索引接线结果）=
review_queue_wiring_result（复核队列接线结果）=
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
feat: wire trusted source text metadata
```

If the task becomes mostly tests:

```text
test: add source text wiring coverage
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
