# DateFac Project Overview 333A/339A Synced

## 1. What Problem The Project Is Solving

DateFac is no longer best described as “a PDF table extractor.” The more accurate framing is:

> once parser output already exists, how does the system decide what can be trusted, what must stay under review, what should be rejected, and how should that state be explained without overstating maturity?

That is why the current repository focus includes:

- MinerU-first real PDF intake
- candidate precision calibration
- financial-table context repair
- reviewed strictness and year-alignment QA
- AI text adjudication dry-runs
- grounded review
- adoption simulation

## 2. Current Engineering Position

The current path should be described as:

- local
- sidecar
- demo
- preview
- no-write-back

Those are not decorative terms. They are boundary terms.

The documentation must continue to acknowledge:

- `client_ready = false`
- `production_ready = false`
- AI conclusions do not write back into official assets

## 3. Functional View Of The Current Pipeline

Ignore stage numbers first and think in functions:

1. MinerU parses real PDFs into usable layout, table, and candidate artifacts
2. rule calibration suppresses obvious noise and low-quality candidates
3. context repair restores table role and unit clues
4. strict reviewed QA tightens the reviewed set
5. AI performs text-only dry-run adjudication
6. grounded review and adoption simulation constrain that model output further
7. final preview and docs remain conservative

## 4. What 337A-338D Added

- 336A: PDF-folder smoke runner
- 336B: per-PDF debug package
- 337A: MinerU-first real PDF intake
- 337B: candidate precision calibration
- 337C: core financial context repair
- 337D: reviewed strictness, year-alignment, suspicious-row QA
- 338A: DeepSeek flash text-adjudication baseline
- 338B: `AI_REVIEW_MODEL` versus DeepSeek flash
- 338C: grounded schema tightening
- 338D: adoption simulation

The most important boundary across 338A-338D is:

> these stages evaluate whether model recommendations are usable, not whether production adoption is complete.

## 5. Current Metrics

### Real PDF intake

- 337A parsed `3` real PDFs successfully
- per-PDF metric candidates:
  - `H3_AP202606081823352620_1.pdf = 134`
  - `H3_AP202606081823352906_1.pdf = 111`
  - `H3_AP202606081823356439_1.pdf = 102`
- 337A totals:
  - `reviewed = 303`
  - `needs_review = 42`
  - `rejected_or_excluded = 2`

### Rule calibration and repair

- 337B reduced reviewed rows from `303` to `98`
- 337C raised reviewed rows to `148`
- 337C `table_role_repair_count = 35`
- 337C `unit_filled_count = 119`
- 337D tightened reviewed rows down to `112`
- 337D `year_alignment_repaired_count = 33`
- 337D `reviewed_duplicate_removed_count = 27`

### AI dry-run

- 338A DeepSeek flash baseline:
  - `low_confidence = 34 / 50`
  - `NEEDS_MORE_CONTEXT = 33 / 50`
- 338B `gpt-5.5` A/B:
  - `low_confidence = 0 / 50`
  - `NEEDS_MORE_CONTEXT = 3 / 50`
  - `invalid_response = 3`
- 338C grounded review:
  - `invalid_response = 1`
  - `grounding_source BOTH = 49`
- 338D adoption simulation:
  - `ACCEPT_MODEL_CONFIRM = 39`
  - `ACCEPT_MODEL_REJECT = 3`
  - `HOLD_FOR_HUMAN_REVIEW = 3`
  - `REJECT_BY_DETERMINISTIC_RULE = 4`
  - `INVALID_MODEL_RESPONSE = 1`
  - `deterministic_rule_override_count = 0`

## 6. Model Role Split

- MinerU: current primary parser
- deterministic rules: current highest-priority safety layer
- `AI_REVIEW_MODEL`: current main candidate text adjudicator
- DeepSeek flash: baseline / fallback
- vision model: future tool for screenshot, layout, or image-table uncertainty
- human review: final safety layer

One key detail matters:

> 338D does not recommend immediately setting `AI_REVIEW_MODEL` as the default formal adjudicator because `suggest_set_ai_review_model_default = false`.

## 7. Why This State Is Valuable

Its value is not that it already supports direct client delivery.

Its value is that:

- real PDF intake now runs on actual documents
- the rule layer can materially reduce false reviewed rows
- the AI layer is constrained by deterministic guards, grounding requirements, and adoption policy
- the documentation explicitly preserves maturity boundaries

That is more credible than a polished spreadsheet with weak explanation.

## 8. Safe Claims And Unsafe Claims

### Safe claims

- MinerU-first intake preview for real research PDFs exists
- rule-based candidate precision repair exists
- financial-context repair and stricter reviewed QA exist
- AI text-adjudication dry-run, A/B evaluation, grounded review, and adoption simulation exist
- the path remains no-write-back and preview-oriented

### Unsafe claims

- client-ready
- production-ready
- AI replaces humans
- 100% accurate
- fully automatic commercial SaaS
- direct investment-decision suitability

## 9. Current Limitations

Current limitations include:

- the path remains sidecar, demo, and preview-oriented
- AI decisions remain dry-run only
- human review remains necessary
- broader benchmarking is still needed
- deployment, security, permissions, and data isolation remain unfinished

## 10. Final Positioning

The strongest honest description of DateFac today is:

> it is a coherent engineering chain that combines real-PDF parsing, rule-based constraint layers, AI adjudication experiments, human-review boundaries, and claim-safe documentation, without pretending that production adoption is already complete.
