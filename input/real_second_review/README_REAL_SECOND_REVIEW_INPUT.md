# Real Second Review Input (Stage 8A)

This folder is for **real** second-review human input only.

## Steps
1. Copy the Stage 7W template:
   - `D:\_datefac\output\stage7w_second_review_needs_more_info_package\210_stage7w_second_review_input_template.xlsx`
2. Fill with real second reviewer information.
3. Save as: `D:\_datefac\input\real_second_review\stage8a_real_second_review_input.xlsx`

## Mandatory Rules
- Do not edit immutable queue fields.
- Do not add `safe_to_apply`.
- Do not use `APPROVE_FOR_REAL_APPLY`.
- `APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE` only creates a future sandbox preview candidate; it is not production apply.

## Rerun Sequence After Real Input
1. `python tools/run_stage7x_second_review_input_validation.py`
2. `python tools/run_stage7y_sandbox_preview_candidate_preflight.py`
3. `python tools/run_stage7z_controlled_sample_exclusion_readiness_gate.py`
4. `python tools/run_stage8b_real_second_review_validation.py` (future stage)