# 348N-R3 Remaining Non-Normalized Unknown-Family Refinement

## Goal

Refine the remaining non-normalized unknown-row families in the Linyang Energy testset workbook after 348N-R2.

This is a targeted implementation task.

Do not modify normalized_testset behavior unless a regression test needs to protect it.

Do not widen clean_data acceptance broadly.

---

## Current validated chain

```text
348N_R1_CONFIRMED_LINYANG_UNKNOWN_ROW_FAMILIES_DIAGNOSED
348N_R2_CONFIRMED_NORMALIZED_TESTSET_SCHEMA_SUPPORT_VALID
348N_R2_QA_CONFIRMED_NORMALIZED_TESTSET_SCHEMA_SUPPORT_VALID
```

R2-QA confirmed:

```text
NORMALIZED_TESTSET_RECORD_ROW is schema-specific / review-only
NORMALIZED_TESTSET_RECORD_ROW is excluded from clean_data
clean_data_row_count stayed 37
review_queue was not artificially shrunk
runner changes were reporting-only
pytest: 42 passed
```

R2 metrics:

```text
unknown_row_count: 367 -> 48
normalized_testset_record_row_count: 0 -> 320
clean_data_row_count: 37 -> 37
review_queue_row_count: 446 -> 447
evidence_issue_count: 397 -> 78
strong_evidence_count: 86 -> 406
weak_evidence_count: 397 -> 78
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
docs/agent/项目进程.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/348N_R2_QA_NORMALIZED_TESTSET_SCHEMA_SUPPORT_REVIEW.md
docs/agent/348N_R2_NORMALIZED_TESTSET_INTAKE_SCHEMA_SUPPORT_RESULT.md
docs/agent/348N_R1_LINYANG_UNKNOWN_ROW_SHAPE_DIAGNOSIS.md
```

---

## Preflight

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

Stop if the worktree is not clean.

---

## Input/output for replay

Input pair:

```text
PDF:   D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf
Excel: D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx
```

Baseline R2 output:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348n_r2_linyang_normalized_testset_schema
```

New output directory:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families
```

Do not commit output files.

---

## Target families

Handle only the remaining non-normalized unknown families, expected to include:

```text
README
data_dictionary
doc_metadata
figure_index
related_research
validation_checks
market_base_data
```

Do not change the `normalized_testset` main long-record routing except for regression protection.

---

## Desired behavior

### Review-only / out-of-scope families

These should not enter clean_data:

```text
README bookkeeping/narrative rows
data_dictionary field-definition rows
figure_index chart-index / handling-strategy rows
doc_metadata metadata rows
related_research reference/narrative rows
validation_checks testset validation/bookkeeping rows
```

Acceptable options:

```text
route to NARRATIVE_ASSERTION if semantically narrative/metadata
or route to a schema-specific bookkeeping/out-of-scope row type if the model already supports it or can safely add it
```

They must remain review-only or excluded from clean_data.

### Market reference family

`market_base_data` may be considered for `MARKET_REFERENCE_ROW` only if all of these hold:

```text
has structured metric/value/unit/source-page lineage
does not broaden generic market-reference routing beyond this sheet/header family
does not create unintended clean_data promotion for unrelated rows
is covered by targeted tests
```

If uncertain, leave `market_base_data` review-only and document why.

---

## Required implementation constraints

Do not create a generic rule that turns all metadata-like sheets into clean data.

Do not make `UNKNOWN_ROW` disappear by hiding rows.

Do not loosen unit, period, valuation, evidence, or clean-candidate policy globally.

Do not change readiness gates.

Do not modify legacy `datefac/`.

---

## Allowed changes

Allowed source/test/docs changes:

```text
datefac_agent/schemas/audit_models.py
datefac_agent/intake/excel_intake.py
datefac_agent/review/clean_candidate_policy.py
tools/run_agent_excel_intake_audit_348a.py  # only if new row counters are needed
tests/agent/test_agent_excel_intake_audit_348a.py
tests/agent/fixtures/  # compact fixture only if useful
docs/agent/348N_R3_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_RESULT.md
```

Do not modify input files.

Do not commit output files.

---

## Required tests

Add targeted tests for:

```text
README / metadata family does not enter clean_data
data_dictionary rows do not enter clean_data
figure_index rows do not enter clean_data
validation_checks rows do not enter clean_data if present
market_base_data routing is either explicitly MARKET_REFERENCE_ROW or explicitly review-only, with tests
normalized_testset behavior from R2 remains unchanged
normal wide workbook classification remains protected
```

Existing agent tests must still pass.

---

## Required validation

Run:

```powershell
python -m py_compile datefac_agent\schemas\audit_models.py datefac_agent\intake\excel_intake.py datefac_agent\review\clean_candidate_policy.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_excel_intake_audit_348a.py
python -m pytest tests\agent -q
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\6862e6f3995d3dbfbed310b51601fb0a.pdf --excel-path "D:\_datefac_agent\input\linyang_energy_pdf_extracted_testset (1).xlsx" --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348n_r3_linyang_remaining_unknown_families
```

If additional Python files are modified, include them in py_compile.

---

## Expected report

Create:

```text
docs/agent/348N_R3_REMAINING_NON_NORMALIZED_UNKNOWN_FAMILY_REFINEMENT_RESULT.md
```

Include:

```text
Task ID
Files modified
Target family behavior
Before/after metrics
Unknown-row QA
Clean-data boundary QA
Review-queue QA
Market-base-data decision
Regression test summary
Validation commands and results
Boundary discipline
Decision
Recommended next task
```

Decision values:

```text
348N_R3_CONFIRMED_REMAINING_UNKNOWN_FAMILY_REFINEMENT_VALID
348N_R3_CONFIRMED_PARTIAL_REFINEMENT_STILL_NEEDS_FAMILY_SPLIT
348N_R3_BLOCKED_BY_SCHEMA_CONTRACT_LIMITATION
348N_R3_BLOCKED_BY_RUNNER_FAILURE
```

---

## Completion report

Report:

1. Files modified.
2. Current branch.
3. Whether worktree was clean before editing.
4. Target family behavior.
5. Before/after metrics.
6. Whether remaining non-normalized unknown rows dropped.
7. Whether normalized_testset behavior stayed unchanged.
8. Whether clean_data stayed conservative.
9. Whether review_queue stayed explainable.
10. Market-base-data decision.
11. pytest result.
12. Runner result and output directory.
13. Whether legacy datefac/ was untouched.
14. Whether output files were not committed.
15. Whether LLM/MinerU/OCR calls were zero.
16. git status -sb.
17. Recommended next task.
