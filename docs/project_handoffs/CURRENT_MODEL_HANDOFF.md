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

Full task specs live in `docs/codex_tasks/`.

## Current task

```text
348N-R7Z-QA agreement checker edge-case review
```

Recommended reasoning level:

```text
recommended_reasoning_level = max
reason = R7Z-QA verifies that multiplicity-aware matching reduces VERIFIED false positives without making DISAGREED too aggressive or changing clean/readiness boundaries.
```

Task document:

```text
docs/codex_tasks/348N_R7Z_QA_agreement_checker_edge_case_review.md
```

Expected report:

```text
docs/agent/348N_R7Z_QA_AGREEMENT_CHECKER_EDGE_CASE_REVIEW.md
```

Task type:

```text
QA / review task
```

R7Z-QA focus:

```text
duplicate row numeric values require duplicate source occurrences
one source occurrence for two identical row values stays UNVERIFIED
enough duplicate source occurrences can verify
partial coverage remains UNVERIFIED
source text with no numeric tokens remains UNVERIFIED
text-only facts remain UNVERIFIED
full mismatch remains DISAGREED only when no row values match
VERIFIED does not become STRONG_EVIDENCE
VERIFIED does not become clean admission
VERIFIED does not open readiness gates
source_text is still not wired into the real pipeline
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
docs/codex_tasks/348N_R7Z_QA_agreement_checker_edge_case_review.md
docs/agent/348N_R7Y_QA_DETERMINISTIC_SOURCE_VALUE_AGREEMENT_CHECKER_REVIEW.md
docs/agent/348N_R7X_QA_EVIDENCE_PROVENANCE_PARSING_REVIEW.md
```

## Latest completed result

### R7Z agreement checker edge-case fixture coverage

```text
commit = 004e307 fix: make agreement checker multiplicity conservative
Decision = PASS，R7Z agreement checker edge-case coverage and conservative multiplicity fix completed
build_result = PASS，py_compile 全部通过
test_result = PASS，pytest tests/agent -q => 111 passed in 0.84s
files_modified = 2
edge_case_coverage_result = PASS
verified_false_positive_result = REDUCED
disagreed_status_result = PASS
source_text_integration_result = NOT_CHANGED
readiness_gates = CLOSED
```

R7Z fixed:

```text
before: source numeric tokens were stored as a set
problem: row values [100, 100] could be satisfied by one source token 100 -> unsafe VERIFIED
after: source numeric tokens are counted with Counter[Decimal]
result: duplicate row values require duplicate source occurrences
```

Concrete example:

```text
row period_values = {2024A: 100, 2025A: 100}
source_text = one occurrence of 100
before R7Z -> VERIFIED
after R7Z -> UNVERIFIED
```

Still not solved intentionally:

```text
row-level matching is still not period-aware or coordinate-aware
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

Current next step is R7Z-QA.

If R7Z-QA passes, recommended next step is not production readiness. Prefer:

```text
R7AA source_text integration design / evidence index wiring design
```

or a more limited targeted design task depending on QA findings.

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
