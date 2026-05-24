# Stage 7H AI-Assisted Manual Review Design

## Background
- Stage7G remaining_manual_review_rows: 57
- Current goal: design-only, no real API call, no production update.

## Design Scope
1. AI review request schema
2. AI review response schema
3. Prompt template
4. Validation rules
5. Runtime integration plan
6. Mock request/response set (5 cases)

## Input Snapshot
- reduced_clean_06_preview_rows: 62
- manual_review_reason_distribution: {"year_semantics_uncertain": 57}

## Mock Case Validation
- validation_pass_count: 5
- validation_fail_count: 0

## Safety Rules
- AI cannot write production 06.
- AI cannot modify formal rules.
- EPS/每股收益 cannot use ratio/% unit.
- If evidence is insufficient, keep_manual_review.
- All suggestions require human approval.

## Verification
- check_delivery_state_overall_status: PASS
- production_files_modified: False
- official_02b_modified: False
- formal_rules_modified: False
- standardizer_modified: False
- release_package_modified: False

## Decision
- ready_for_stage7i_ai_runtime_dry_run: True