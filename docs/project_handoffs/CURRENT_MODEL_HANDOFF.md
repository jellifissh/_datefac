# Current Handoff

## Workspace

```text
D:\_datefac_agent
pivot/348-agent-foundation
```

## Operating model

After each meaningful completed task, the workflow is:

```text
review execution report -> decide result -> write next task doc -> give short local-agent prompt -> sync progress docs
```

Progress sync targets:

```text
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
```

Before writing the local-agent prompt, always include a reasoning-level recommendation:

```text
recommended_reasoning_level = high / very high / max
reason = why this task needs that level
```

Default rule:

```text
high = ordinary docs sync / simple QA / small bounded changes
very high = implementation + tests, QA touching evidence / clean_data / guardrails
max = architecture, readiness, cross-family regression, evidence-strength semantics, production-boundary decisions
```

Full task specs live in `docs/codex_tasks/`. Chat output should normally include only the decision, next task document path, reasoning-level recommendation, and short local-agent prompt.

## Current task

```text
348N-R7Y-QA deterministic source-value agreement checker review
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7Y-QA reviews VERIFIED / DISAGREED evidence-agreement semantics. A false pass can pollute future evidence_strength and readiness interpretation.
```

Task document:

```text
docs/codex_tasks/348N_R7Y_QA_deterministic_source_value_agreement_checker_review.md
```

Expected report:

```text
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
```

Task type:

```text
QA / review task
```

R7Y-QA focus:

```text
VERIFIED only when all row numeric period_values match source_text deterministically
DISAGREED only when source text has numeric tokens and no row numeric values match
partial coverage remains UNVERIFIED
text-only facts remain UNVERIFIED
VERIFIED does not become STRONG_EVIDENCE automatically
VERIFIED does not become clean admission automatically
VERIFIED does not open readiness gates
MARKET_REFERENCE_ROW policy unchanged
qualitative_facts admission unchanged
R7S strict-table clean-boundary unchanged
```

## Minimum read order

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
项目进展大白话说明.md
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/codex_tasks/348N_R7Y_QA_deterministic_source_value_agreement_checker_review.md
docs/codex_tasks/348N_R7Y_deterministic_source_value_agreement_checker.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
```

## Latest completed result

### R7Y deterministic source-value agreement checker

```text
commit = 973ff68 feat: add deterministic evidence agreement checker
Decision = PASS，R7Y deterministic source-value agreement checker 已完成并推送
build_result = PASS，py_compile 全部通过
test_result = PASS，pytest tests/agent -q => 106 passed in 0.77s
files_modified = 2
agreement_checker_result = PASS
verified_status_result = PASS
disagreed_status_result = PASS
strong_evidence_claim_result = PASS
readiness_gates = CLOSED
```

R7Y implemented:

```text
classify_agreement_status(row, evidence_refs, source_text=None)
numeric normalization using Decimal
VERIFIED for deterministic full numeric coverage in source_text
DISAGREED for deterministic numeric mismatch when source has numbers and no values match
UNVERIFIED for no source_text / partial coverage / text-valued facts / ambiguity
```

Important boundary:

```text
VERIFIED != STRONG_EVIDENCE
VERIFIED != clean admission
VERIFIED != production readiness
```

### R7X-QA evidence provenance parsing review

```text
commit = 6fb00ec docs: add R7X QA review
Decision = 348N_R7X_QA_CONFIRMED_EVIDENCE_PROVENANCE_PARSING_VALID
test_result = tests/agent 95 passed
qa_result = VALID
readiness_gates = closed
```

R7X-QA confirmed:

```text
page_number parsed = provenance anchor exists
agreement_status = UNVERIFIED = source-value agreement not checked yet
UNVERIFIED provenance remains WEAK_EVIDENCE
parsed page_number does not automatically become VERIFIED or STRONG_EVIDENCE
```

## Clean-boundary summary

```text
R7P-FIX2 fixed MARKET_REFERENCE_ROW clean_data leak.
R7S narrowed STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE clean admission for scaffolding / pseudo-header / comparison rows.
R7T confirmed Taihao: clean_data 92 -> 72, review_queue 66 -> 86, 20 risky rows moved to review_queue.
R7U confirmed no R7S regression on Linyang and Anjing.
R7V confirmed cross-family clean-boundary valid, readiness gates remain closed.
```

Readiness gates:

```text
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

## Next-step guidance

Current next step is R7Y-QA.

If R7Y-QA passes, recommended next step is not production readiness. Prefer either:

```text
R7Z source_text integration design / evidence index wiring
```

or:

```text
R7Z targeted fixture coverage for deterministic agreement checker edge cases
```

Decision should depend on QA findings.

## Boundaries

```text
legacy datefac/ stays reference-only by default
input/output/temp/data source files stay untouched unless a task explicitly allows generated output
output files are not committed
MinerU / OCR / LLM / VLM remain unused unless a task explicitly allows them
readiness gates stay closed
qualitative_facts admission remains closed
MARKET_REFERENCE_ROW policy stays conservative
page_number parsing is not source-value verification
VERIFIED is not automatic clean admission
VERIFIED is not production readiness
agent tasks should stage only explicit allowed paths
```
