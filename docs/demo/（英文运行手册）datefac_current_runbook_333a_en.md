# DateFac Current Runbook 333A/339A Synced

## 1. Scope

This runbook covers the current real-PDF preview chain:

- 337A MinerU-first intake
- 337B precision calibration
- 337C core financial context repair
- 337D reviewed strictness / year-alignment QA
- 338A DeepSeek baseline dry-run
- 338B `AI_REVIEW_MODEL` A/B evaluation
- 338C grounded AI review
- 338D adoption simulation

This is not a production operations manual.

It does not authorize:

- production pipeline changes
- parser / extraction / delivery changes
- official asset modification
- committing generated output artifacts

## 2. Assumptions

Expected environment:

- Windows
- repository root at `D:\_datefac`
- PowerShell
- local Python available
- 337A-338D code already present

All synced docs must continue to acknowledge:

- `client_ready = false`
- `production_ready = false`
- AI decisions are dry-run only
- no-write-back is still active

## 3. Key Paths

Input directory:

- `D:\_datefac\input\real_test`

Main output directories:

- `D:\_datefac\output\mineru_real_test_337a`
- `D:\_datefac\output\mineru_candidate_precision_337b`
- `D:\_datefac\output\core_financial_context_repair_337c`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d`
- `D:\_datefac\output\deepseek_text_adjudicator_338a`
- `D:\_datefac\output\ai_review_model_ab_338b`
- `D:\_datefac\output\grounded_ai_review_338c`
- `D:\_datefac\output\ai_review_adoption_simulation_338d`

## 4. Recommended Run Order

### 4.1 Real PDF intake

```powershell
python tools\run_mineru_real_pdf_intake_337a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\mineru_real_test_337a
```

### 4.2 Candidate precision calibration

```powershell
python tools\run_mineru_candidate_precision_337b.py --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\mineru_candidate_precision_337b
```

### 4.3 Core financial context repair

```powershell
python tools\run_core_financial_context_repair_337c.py --precision-337b-dir D:\_datefac\output\mineru_candidate_precision_337b --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\core_financial_context_repair_337c
```

### 4.4 Reviewed strictness / year alignment

```powershell
python tools\run_reviewed_strictness_year_alignment_337d.py --context-repair-337c-dir D:\_datefac\output\core_financial_context_repair_337c --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d
```

### 4.5 AI baseline dry-run

```powershell
python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50
```

### 4.6 A/B evaluation

```powershell
python tools\run_ai_review_model_ab_338b.py --baseline-338a-dir D:\_datefac\output\deepseek_text_adjudicator_338a --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_model_ab_338b --limit 50
```

### 4.7 Grounded review

```powershell
python tools\run_grounded_ai_review_338c.py --ab-338b-dir D:\_datefac\output\ai_review_model_ab_338b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\grounded_ai_review_338c --limit 50
```

### 4.8 Adoption simulation

```powershell
python tools\run_ai_review_adoption_simulation_338d.py --grounded-ai-review-338c-dir D:\_datefac\output\grounded_ai_review_338c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_adoption_simulation_338d
```

## 5. What To Inspect After Each Stage

### 337A

Inspect:

- `00_batch_summary.json`
- `real_test_mineru_client_export_337a.xlsx`
- each per-PDF `document_summary.json`

Expected:

- `pdf_found_count = 3`
- `mineru_success_count = 3`
- `reviewed_count = 303`
- `needs_review_count = 42`
- `rejected_or_excluded_count = 2`

### 337B

Inspect:

- `mineru_candidate_precision_337b_summary.json`

Expected:

- `reviewed_before_count = 303`
- `reviewed_after_count = 98`

### 337C

Inspect:

- `core_financial_context_repair_337c_summary.json`

Expected:

- `reviewed_after_count = 148`
- `table_role_repair_count = 35`
- `unit_filled_count = 119`

### 337D

Inspect:

- `reviewed_strictness_year_alignment_337d_summary.json`
- `real_test_mineru_client_export_337d.xlsx`

Expected:

- `reviewed_after_count = 112`
- `year_alignment_repaired_count = 33`
- `reviewed_duplicate_removed_count = 27`
- `qa_fail_count = 0`

### 338A

Inspect:

- `deepseek_text_adjudicator_338a_summary.json`

Expected:

- `model_name = deepseek-v4-flash`
- `low_confidence_count = 34`
- `needs_more_context_count = 33`

### 338B

Inspect:

- `ai_review_model_ab_338b_summary.json`

Expected:

- `new_model_name = gpt-5.5`
- `low_confidence_count_new = 0`
- `needs_more_context_count_new = 3`
- `invalid_response_count_new = 3`

### 338C

Inspect:

- `grounded_ai_review_338c_summary.json`

Expected:

- `invalid_response_count_338c = 1`
- `grounding_source_counts.BOTH = 49`

### 338D

Inspect:

- `ai_review_adoption_simulation_338d_summary.json`
- `ai_review_adoption_simulation_338d_plan.xlsx`

Expected:

- `accept_model_confirm_count = 39`
- `accept_model_reject_count = 3`
- `hold_for_human_review_count = 3`
- `invalid_model_response_count = 1`
- `deterministic_rule_override_count = 0`

## 6. Boundaries That Must Stay Visible

Do not lose these:

- this is sidecar preview work, not production
- AI conclusions are dry-run only, not formal write-back
- deterministic rules outrank model outputs
- human review is still necessary
- `AI_REVIEW_MODEL` is still only a candidate default adjudicator

## 7. Common Misreads

### Misread 1

“337A parsed 3 PDFs successfully, so the system is ready for delivery.”

False. 337A proves real-PDF intake can run. It does not prove delivery readiness.

### Misread 2

“338B/338C show `gpt-5.5` is stronger, so it should immediately replace the baseline by default.”

False. 338D explicitly says:

- `suggest_set_ai_review_model_default = false`

### Misread 3

“AI adoption simulation means AI is now officially adopted.”

False. It is still only a simulation layer.

## 8. Git Discipline

For this documentation sync task:

- do not use `git add -A`
- do not use `git add .`
- do not stage `output/*`
- do not stage protected dirty files

Protected dirty files still include:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## 9. Minimum Re-Entry Order

When you return to the repo, use this order:

1. `git status -sb`
2. read `README.md`
3. read this runbook
4. read `datefac_ai_review_architecture_339a_en.md`
5. inspect the 337A, 337D, and 338D summaries
6. only then open workbooks

## 10. Final Sentence

> The point of the current runbook is not to make the project sound stronger. It is to help you run it correctly, read it correctly, and describe it correctly within its real boundary.
