# DateFac Newbie Operator Guide 333A/339A Synced

## 1. What The Project Is Right Now

DateFac is not a client-delivery system and not a production write-back system.

Right now it is a local, sidecar, provenance-aware preview-governance pipeline for financial research PDFs. Its current value is:

- MinerU-first intake for real PDFs
- conservative candidate cleanup and repair
- explicit reviewed / needs-review / rejected separation
- AI adjudication as dry-run evaluation only
- explainable preview artifacts and audited documentation

The short version is:

> DateFac is currently stronger at managing uncertainty after extraction than at claiming fully automated final delivery.

## 2. What Was Added Beyond The Earlier 330L-335A Story

The documentation now needs to reflect these newer stages:

- 336A: raw PDF folder smoke runner
- 336B: per-PDF debug package
- 337A: MinerU-first real PDF intake
- 337B: candidate precision calibration
- 337C: core financial context repair
- 337D: reviewed strictness, year alignment, suspicious-row QA
- 338A: DeepSeek text adjudication dry-run baseline
- 338B: `AI_REVIEW_MODEL` A/B evaluation against DeepSeek flash
- 338C: grounded AI review schema tightening
- 338D: AI review adoption simulation

All of them remain sidecar, demo, preview, and no-write-back work.

## 3. The Simplest Mental Model Of The Current Real-PDF Flow

Do not start from stage numbers. Start from functions:

1. Put real research PDFs in `D:\_datefac\input\real_test`
2. Let MinerU parse layout and tables
3. Let DateFac reduce candidate noise and repair context
4. Keep only safer rows in reviewed preview
5. Use AI only as dry-run adjudication and adoption simulation

You can think of the current flow as:

```text
real PDFs
-> MinerU parsing
-> candidate calibration
-> context repair
-> strict reviewed QA
-> AI dry-run adjudication
-> adoption simulation
-> explainable preview
```

## 4. Facts That Must Stay Consistent

The current documentation must stay aligned with these values:

- 337A parsed `3` real PDFs successfully
- 337A metric candidates:
  - `352620_1 = 134`
  - `352906_1 = 111`
  - `356439_1 = 102`
- 337A `reviewed / needs_review / rejected = 303 / 42 / 2`
- 337B reduced reviewed rows from `303` to `98`
- 337C raised reviewed rows to `148`
- 337C `unit_filled_count = 119`
- 337D reduced reviewed rows to `112`
- 338A DeepSeek baseline:
  - `low_confidence = 34 / 50`
  - `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B `gpt-5.5` comparison:
  - `low_confidence = 0 / 50`
  - `NEEDS_MORE_CONTEXT = 3 / 50`
  - `invalid_response = 3`
- 338C:
  - `invalid_response = 1`
  - `grounding_source BOTH = 49`
- 338D:
  - `ACCEPT_MODEL_CONFIRM = 39`
  - `ACCEPT_MODEL_REJECT = 3`
  - `HOLD_FOR_HUMAN_REVIEW = 3`
  - `INVALID_MODEL_RESPONSE = 1`

## 5. What Each Model Or Rule Layer Does

- MinerU: primary parser for real PDF layout and tables
- deterministic rules: highest-priority safety layer for units, duplicates, obvious noise, and percentage-as-amount errors
- `AI_REVIEW_MODEL`: main text-adjudication candidate
- DeepSeek flash: conservative baseline / fallback
- vision models: future tools for screenshot, layout, or image-table uncertainty
- human review: final safety layer

The key sentence:

> AI is currently not the final decider. It is a dry-run adjudication layer.

## 6. What To Run First

The current minimum real-PDF sequence is:

```powershell
python tools\run_mineru_real_pdf_intake_337a.py --input-pdf-dir D:\_datefac\input\real_test --output-dir D:\_datefac\output\mineru_real_test_337a

python tools\run_mineru_candidate_precision_337b.py --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\mineru_candidate_precision_337b

python tools\run_core_financial_context_repair_337c.py --precision-337b-dir D:\_datefac\output\mineru_candidate_precision_337b --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\core_financial_context_repair_337c

python tools\run_reviewed_strictness_year_alignment_337d.py --context-repair-337c-dir D:\_datefac\output\core_financial_context_repair_337c --mineru-real-test-dir D:\_datefac\output\mineru_real_test_337a --output-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d
```

If you want the AI dry-run continuation:

```powershell
python tools\run_deepseek_text_adjudicator_338a.py --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\deepseek_text_adjudicator_338a --limit 50

python tools\run_ai_review_model_ab_338b.py --baseline-338a-dir D:\_datefac\output\deepseek_text_adjudicator_338a --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_model_ab_338b --limit 50

python tools\run_grounded_ai_review_338c.py --ab-338b-dir D:\_datefac\output\ai_review_model_ab_338b --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\grounded_ai_review_338c --limit 50

python tools\run_ai_review_adoption_simulation_338d.py --grounded-ai-review-338c-dir D:\_datefac\output\grounded_ai_review_338c --reviewed-strictness-337d-dir D:\_datefac\output\reviewed_strictness_year_alignment_337d --output-dir D:\_datefac\output\ai_review_adoption_simulation_338d
```

## 7. Which Files To Open First

Start with:

- `README.md`
- `docs/demo/（英文项目总览）datefac_project_overview_333a_en.md`
- `docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md`
- `docs/demo/datefac_ai_review_architecture_339a_en.md`

Then inspect:

- `D:\_datefac\output\mineru_real_test_337a\00_batch_summary.json`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\reviewed_strictness_year_alignment_337d_summary.json`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_summary.json`

If you want the workbooks:

- `D:\_datefac\output\mineru_real_test_337a\real_test_mineru_client_export_337a.xlsx`
- `D:\_datefac\output\reviewed_strictness_year_alignment_337d\real_test_mineru_client_export_337d.xlsx`
- `D:\_datefac\output\ai_review_adoption_simulation_338d\ai_review_adoption_simulation_338d_plan.xlsx`

## 8. What You Must Not Misread This As

Do not interpret the current state as:

- client-ready
- production-ready
- AI-replaces-human
- final model write-back
- 100% accurate

The correct statements are:

- not client-ready
- not production-ready
- AI decisions are dry-run only
- human review remains necessary

## 9. If You Remember Only One Sentence

> DateFac is currently a “real PDF -> MinerU -> rule repair -> strict QA -> AI dry-run -> adoption simulation -> explainable preview” pipeline, not a production write-back system.
