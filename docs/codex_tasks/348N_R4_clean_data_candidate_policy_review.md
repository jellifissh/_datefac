# 348N-R4 Clean Data Candidate Policy Review

## Goal

Review whether the remaining `clean_data` rows in the Linyang Energy R3 output should really stay in `clean_data`.

This is a diagnosis/review task, not an implementation task.

Do not modify source code, tests, input files, output files, or historical reports.

---

## Current context

R3-QA is valid:

```text
348N_R3_QA_CONFIRMED_REMAINING_UNKNOWN_FAMILY_REFINEMENT_VALID
```

Current R3 metrics:

```text
unknown_row_count = 0
clean_data_row_count = 33
review_queue_row_count = 455
testset_supporting_row_count = 49
market_reference_row_count = 10
normalized_testset_record_row_count = 320
pytest_result = 48 passed
LLM / MinerU / OCR calls = 0
```

The remaining `clean_data` rows are currently described as:

```text
qualitative_facts: 33 rows
STRICT_FINANCIAL_TABLE_ROW
INTERNAL_CLEAN_CANDIDATE
WEAK_EVIDENCE
```

The key question:

```text
Should these qualitative_facts rows stay in clean_data, or should they become review-only / testset-specific rows?
```

---

## Required context

Read:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
项目进展大白话说明.md
docs/agent/348N_R3_QA_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_REVIEW.md
docs/agent/348N_R3_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_RESULT.md
```

---

## Input/output to inspect read-only

Inspect R3 output read-only:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families
```

Focus on:

```text
clean_data.csv
evidence_index.json
agent_excel_intake_audit_348a_manifest.json
agent_excel_intake_audit_348a_run_summary.json
audit_report.md
```

Do not modify or commit output files.

---

## Review focus

Answer these questions:

```text
What exactly are the 33 qualitative_facts clean_data rows?
Are they financial facts, narrative facts, qualitative claims, testset labels, or something else?
Do they have enough metric/value/unit/period/source-page structure to justify clean_data?
Are they comparable to strict financial table rows from prior workbooks?
Are they only WEAK_EVIDENCE because evidence is genuinely weak, or because the sheet is testset-specific?
Would keeping them in clean_data create business risk?
Would moving them to review-only reduce useful clean_data too much?
Should R4 recommend no code change, or a follow-up implementation task to reroute qualitative_facts?
```

---

## Allowed output

Create only:

```text
docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

---

## Forbidden actions

Do not modify:

```text
datefac_agent/
tests/
tools/
legacy datefac/
input/
output/
temp/
old docs/agent result or QA reports
```

Do not run MinerU, OCR, LLM, or VLM.

Do not re-extract PDFs.

Do not open readiness gates.

Do not use `git add .` or `git add -A`.

---

## Validation

Run:

```powershell
git diff --check
```

No pytest is required unless code/tests are accidentally modified. If code/tests are modified, stop and report a boundary violation.

---

## Expected report

Create:

```text
docs/agent/348N_R4_CLEAN_DATA_CANDIDATE_POLICY_REVIEW.md
```

Include:

```text
Task ID
Reviewed files and output artifacts
Clean-data composition
Qualitative-facts row analysis
Evidence and structure assessment
Business risk assessment
Policy recommendation
Whether implementation is needed
Validation result
Decision
Recommended next task
Data Result / 数据结果
```

Decision values:

```text
348N_R4_CONFIRMED_QUALITATIVE_FACTS_CAN_REMAIN_CLEAN
348N_R4_RECOMMENDS_QUALITATIVE_FACTS_REVIEW_ONLY_IMPLEMENTATION
348N_R4_RECOMMENDS_MORE_SAMPLE_EVIDENCE_BEFORE_POLICY_CHANGE
348N_R4_BLOCKED_BY_MISSING_OUTPUT
```

---

## Completion report

Report:

1. Files created or modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Reviewed output artifacts.
5. Clean-data composition.
6. Qualitative-facts row analysis.
7. Evidence and structure assessment.
8. Business risk assessment.
9. Policy recommendation.
10. Whether implementation is needed.
11. Validation result.
12. Whether code/tests/input/output were untouched.
13. git status -sb.
14. Recommended next task.
15. Data Result / 数据结果.
