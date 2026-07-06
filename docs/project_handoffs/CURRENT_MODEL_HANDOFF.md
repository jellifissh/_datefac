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

Before writing the local-agent prompt, always include:

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

Full task specs live in `docs/codex_tasks/`.

## Current task

```text
348N-R7Z agreement checker edge-case fixture coverage
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7Z hardens VERIFIED / DISAGREED boundary cases before any source-text wiring. False positives would pollute future evidence_strength and readiness interpretation.
```

Task document:

```text
docs/codex_tasks/348N_R7Z_agreement_checker_edge_case_fixture_coverage.md
```

Task type:

```text
implementation + tests, test-first preferred
```

R7Z focus:

```text
duplicate numeric values
partial multi-period coverage
source text with unrelated numeric tokens
source text with no numeric tokens
text-only facts
reduce VERIFIED false-positive risk
preserve conservative DISAGREED behavior
no source-text wiring into real pipeline yet
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
docs/codex_tasks/348N_R7Z_agreement_checker_edge_case_fixture_coverage.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/codex_tasks/348N_R7Y_QA_deterministic_source_value_agreement_checker_review.md
docs/codex_tasks/348N_R7Y_deterministic_source_value_agreement_checker.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
```

## Latest completed result

### R7Y-QA deterministic source-value agreement checker review

```text
commit = 4e71f28 docs: add R7Y QA review
Decision = PASS，R7Y deterministic source-value agreement checker QA valid
build_result = PASS，py_compile 全部通过
test_result = PASS，pytest tests/agent -q => 106 passed in 0.58s
qa_result = VALID
agreement_checker_result = PASS
verified_status_result = PASS
disagreed_status_result = PASS
strong_evidence_claim_result = PASS
readiness_gates = CLOSED
```

R7Y-QA confirmed:

```text
VERIFIED only comes from full deterministic numeric coverage
partial / text-only / no source text remains UNVERIFIED
DISAGREED only comes from deterministic numeric mismatch
VERIFIED does not become STRONG_EVIDENCE
VERIFIED does not become clean admission
VERIFIED does not open readiness gates
```

R7Y-QA noted future precision risks:

```text
row-level token matching is not yet period-aware or coordinate-aware
duplicate numeric values are matched against a source token set
```

## Clean-boundary summary

```text
R7P-FIX2 fixed MARKET_REFERENCE_ROW clean_data leak.
R7S narrowed STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE clean admission for scaffolding / pseudo-header / comparison rows.
R7T confirmed Taihao: clean_data 92 -> 72, review_queue 66 -> 86.
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

Current next step is R7Z.

After R7Z, expected next task is R7Z-QA before any source-text wiring or workbook-family rerun.

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
