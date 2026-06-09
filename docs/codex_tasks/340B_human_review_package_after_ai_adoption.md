# 340B Human Review Package After AI Adoption

## Goal

Create a sidecar human review package after 338D AI adoption simulation.
This task organizes remaining risky or uncertain rows into a reviewer-friendly workbook.
It must not apply decisions, write back, or modify upstream workbooks.

## Inputs

- `D:/_datefac/output/reviewed_strictness_year_alignment_337d`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx`
- `D:/_datefac/output/reviewed_strictness_year_alignment_337d/reviewed_strictness_year_alignment_337d_before_after.xlsx`
- `D:/_datefac/output/ai_review_adoption_simulation_338d`
- `D:/_datefac/output/ai_review_adoption_simulation_338d/ai_review_adoption_simulation_338d_plan.xlsx`
- `D:/_datefac/output/milestone_acceptance_audit_340a`
- `D:/_datefac/output/milestone_acceptance_audit_340a/milestone_acceptance_audit_340a.xlsx`

## Outputs

- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_summary.json`
- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_manifest.json`
- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_qa.json`
- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_no_apply_proof.json`
- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_report.md`
- `D:/_datefac/output/human_review_after_ai_adoption_340b/human_review_after_ai_adoption_340b_review_template.xlsx`

## Scope

- Sidecar review packaging only.
- No write-back.
- No refreshed client export.
- No production pipeline changes.
- No parser, extraction, or delivery changes.
- No official asset changes.

## Workbook Sheets

1. `00_README`
2. `01_REVIEW_QUEUE`
3. `02_HOLD_FOR_HUMAN_REVIEW`
4. `03_INVALID_MODEL_RESPONSES`
5. `04_REJECTED_BY_RULE_FOR_CHECK`
6. `05_ACCEPTED_CONFIRM_SPOT_CHECK`
7. `06_ACCEPTED_REJECT_SPOT_CHECK`
8. `07_SOURCE_TRACE_CONTEXT`
9. `08_REVIEW_GUIDE`
10. `09_SUMMARY`

## Review Queue Rules

The main queue must include:

- all `HOLD_FOR_HUMAN_REVIEW` rows from 338D
- all `INVALID_MODEL_RESPONSE` rows from 338D
- all `REJECT_BY_DETERMINISTIC_RULE` rows from 338D where human checking is useful
- optional 337D `02_NEEDS_REVIEW` rows not already represented
- optional 337D `08_SUSPICIOUS_REVIEWED_AUDIT` rows not already represented
- accepted-confirm spot-check rows
- accepted-reject spot-check rows

Allowed `reviewer_decision` values:

- `CONFIRM_AS_REVIEWED`
- `CORRECT_AND_CONFIRM`
- `KEEP_NEEDS_REVIEW`
- `REJECT`
- `NEEDS_MORE_CONTEXT`

Priority rules:

- `P0`: invalid model response or hard-rule conflict-like row
- `P1`: hold for human review
- `P2`: deterministic rule reject or unresolved 337D needs-review backlog
- `P3`: accepted-confirm spot-check or suspicious reviewed backlog
- `P4`: accepted-reject spot-check

## QA Requirements

- 337D workbook exists.
- 338D workbook exists.
- 340A workbook exists.
- review workbook is generated.
- review queue includes all 338D hold rows.
- review queue includes all 338D invalid rows.
- reviewer fields exist.
- upstream workbooks remain unchanged.
- no-apply proof is generated.
- output artifacts are not staged.
- `client_ready = false`
- `production_ready = false`
- `qa_fail_count = 0`

## Run

```powershell
python -m py_compile datefac\trust\human_review_after_ai_adoption_340b.py datefac\trust\human_review_after_ai_adoption_340b_report.py tools\run_human_review_after_ai_adoption_340b.py tests\trust\test_human_review_after_ai_adoption_340b.py

python -m pytest tests\trust\test_human_review_after_ai_adoption_340b.py -q

python tools\run_human_review_after_ai_adoption_340b.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --ai-adoption-338d-dir D:\_datefac\output\ai_review_adoption_simulation_338d --milestone-audit-340a-dir D:\_datefac\output\milestone_acceptance_audit_340a --output-dir D:\_datefac\output\human_review_after_ai_adoption_340b
```
