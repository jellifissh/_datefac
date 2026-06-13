# 345C2 LLM-Assisted Metric Alias Adjudication Sidecar

## Goal

Implement `345C2 LLM-Assisted Metric Alias Adjudication Sidecar`.

Current context:

- 345A completed full structured-data inventory.
- 345B completed full extraction quality audit.
- 345C completed metric candidate normalization coverage.
- 346B introduced the shared `datefac.llm` client layer.

345C key metrics:

- `metric_candidate_row_count = 14788`
- `normalized_metric_row_count = 6691`
- `unnormalized_metric_row_count = 8097`
- `normalization_coverage_ratio = 0.452461`
- `unique_raw_metric_name_count = 207`
- `unique_normalized_metric_name_count = 18`
- `unique_unnormalized_raw_metric_name_count = 134`
- `alias_candidate_count = 134`
- `high_priority_alias_candidate_count = 26`

345C2 must use the shared `datefac.llm` package to adjudicate metric alias candidates from 345C. It should generate sidecar suggestions only. It must not modify normalization rules, official assets, upstream extraction results, reviewed workbooks, or formal export gates.

345C2 answers:

> For each high-value unnormalized raw metric name, what standard metric does it likely map to, should it become a new standard metric, should it be excluded, or does it need human review?

This task finally lets the LLM do semantic work instead of sitting in the codebase like a decorative toaster.

---

## Required LLM boundary

345C2 must call LLMs only through `datefac.llm`.

Use:

- `datefac.llm.config.resolve_ai_review_runtime_config`
- `datefac.llm.client.ChatCompletionsClient`
- `datefac.llm.json_utils` helpers when parsing JSON responses

Do not create new scattered `/chat/completions` request logic.

The existing `datefac.llm` package is intentionally narrow: it owns runtime config, OpenAI-compatible chat calls, and JSON parsing helpers; prompts, validators, guards, and review recommendations remain inside numbered task modules.

---

## Preflight

Read if present:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/project_milestone_ledger.md`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md`
- `docs/codex_tasks/345C2_llm_assisted_metric_alias_adjudication.md`
- `datefac/llm/README.md`
- `datefac/llm/client.py`
- `datefac/llm/config.py`
- `datefac/llm/json_utils.py`

Inspect only runner input dirs. Do not scan the whole repo.

---

## Runner inputs

Support:

```powershell
--metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c
--output-dir D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2
```

Also support:

```powershell
--max-alias-candidates 26
--include-medium-priority false
--llm-mode auto
--timeout-seconds 60
```

`--llm-mode` values:

- `auto`: use live LLM if runtime config exists; otherwise generate a request package and mark live suggestions as not generated.
- `live`: require runtime config and call the LLM. If config is missing, fail clearly.
- `request_only`: do not call the LLM; generate deterministic prompt/request package for later live execution.
- `fixture`: use deterministic local fixture responses for tests only.

Runtime config must be resolved through `resolve_ai_review_runtime_config`. Prefer `AI_REVIEW_API_KEY` / `AI_REVIEW_BASE_URL` / `AI_MODEL`, then fallback to DeepSeek env variables if implemented by the shared config.

If required 345C manifest or alias candidate queue files are missing, fail clearly.

---

## Inputs to read from 345C

Primarily read:

- `metric_candidate_normalization_coverage_345c_manifest.json`
- `metric_candidate_normalization_coverage_345c_alias_candidate_queue.json` or `.csv`
- `metric_candidate_normalization_coverage_345c_raw_metric_summary.json` or `.csv`
- `metric_candidate_normalization_coverage_345c_metric_rows.json` or `.csv` only when needed for sample evidence

Prioritize:

1. `HIGH` alias candidates
2. high-frequency `MEDIUM` candidates only if `--include-medium-priority true`
3. never silently process all 134 candidates when `--max-alias-candidates` is set

---

## Outputs

Write only under:

```text
D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2
```

Generate:

- `llm_assisted_metric_alias_adjudication_345c2_manifest.json`
- `llm_assisted_metric_alias_adjudication_345c2_alias_request_package.json`
- `llm_assisted_metric_alias_adjudication_345c2_alias_request_package.csv`
- `llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.json`
- `llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.csv`
- `llm_assisted_metric_alias_adjudication_345c2_review_required.json`
- `llm_assisted_metric_alias_adjudication_345c2_review_required.csv`
- `llm_assisted_metric_alias_adjudication_345c2_response_audit.json`
- `llm_assisted_metric_alias_adjudication_345c2_prompt_audit.md`
- `llm_assisted_metric_alias_adjudication_345c2_executive_summary.md`
- `llm_assisted_metric_alias_adjudication_345c2_artifact_index.md`
- `llm_assisted_metric_alias_adjudication_345c2_next_plan.md`

Do not write back into 345C, 345B, 345A, official rules, alias assets, input dirs, or upstream outputs.

---

## Prompt requirements

The prompt must be deterministic and bounded.

Each alias adjudication prompt should include:

- raw metric name
- frequency
- source stages
- PDFs/source artifacts
- sample row ids
- sample neighboring/evidence text when available
- current quality severity distribution
- existing known standard metrics list
- instruction that the model must not invent financial values
- instruction that the output must be JSON only

The model should choose one suggested action:

- `MAP_TO_EXISTING_STANDARD_METRIC`
- `PROPOSE_NEW_STANDARD_METRIC`
- `EXCLUDE_NON_CORE_METRIC`
- `NEEDS_HUMAN_REVIEW`
- `INSUFFICIENT_EVIDENCE`

Suggested existing standard metrics should be constrained to the existing standard metric universe when `MAP_TO_EXISTING_STANDARD_METRIC` is chosen.

Known standard metric universe should include at least the standards already seen in 342F/345C, such as:

- `revenue`
- `net_profit`
- `EPS`
- `PE`
- `PB`
- `ROE`
- `gross_margin`
- `net_margin`
- `revenue_yoy`
- `net_profit_yoy`
- `operating_cash_flow`
- `investing_cash_flow`
- `financing_cash_flow`
- `cash_net_change`
- `total_assets`
- `total_liabilities`
- `shareholder_equity`
- `total_liabilities_and_equity`

Do not automatically add new standards to official rules.

---

## Suggestion schema

Each suggestion row must include:

- `alias_adjudication_id`
- `raw_metric_name`
- `frequency`
- `alias_candidate_priority`
- `source_stages`
- `pdf_names`
- `sample_row_ids`
- `suggested_action`
- `suggested_standard_metric`
- `suggested_new_standard_metric`
- `confidence`
- `reason`
- `evidence_excerpt`
- `risk_flags`
- `needs_human_review`
- `response_parse_status`
- `response_validation_status`
- `llm_mode`
- `llm_provider_env_source`
- `llm_model`
- `prompt_version`
- `prompt_hash`
- `raw_response_hash`

`confidence` must be one of:

- `HIGH`
- `MEDIUM`
- `LOW`
- `UNKNOWN`

`needs_human_review` must be true when confidence is not `HIGH`, action is `PROPOSE_NEW_STANDARD_METRIC`, action is `INSUFFICIENT_EVIDENCE`, output parsing fails, or validation fails.

---

## Validation rules

Validate every parsed LLM response.

A valid response must:

- be JSON object
- include `suggested_action`
- include `confidence`
- include `reason`
- use allowed enum values
- not include numeric financial facts invented by the model
- not claim client/export readiness
- not mutate input data

If parsing or validation fails, record a review-required row. Do not drop the candidate.

---

## Manifest metrics

Manifest must include:

- `decision`
- `input_stage = POST_345C_LLM_ALIAS_ADJUDICATION`
- `qa_fail_count = 0`
- `no_write_back_proof_passed = true`
- `formal_client_export_allowed = false`
- `client_ready = false`
- `production_ready = false`
- `global_strict_human_review_completed = false`
- `llm_mode`
- `live_llm_suggestions_generated`
- `runtime_config_available`
- `input_alias_candidate_count`
- `selected_alias_candidate_count`
- `suggestion_row_count`
- `map_to_existing_count`
- `propose_new_standard_count`
- `exclude_non_core_count`
- `needs_human_review_count`
- `insufficient_evidence_count`
- `high_confidence_suggestion_count`
- `medium_confidence_suggestion_count`
- `low_confidence_suggestion_count`
- `parse_failed_count`
- `validation_failed_count`
- `request_package_generated`
- `alias_apply_simulation_ready`

Decision values:

- live mode with successful suggestions: `LLM_ASSISTED_METRIC_ALIAS_ADJUDICATION_345C2_READY`
- request-only/no-config mode: `LLM_ALIAS_ADJUDICATION_REQUEST_PACKAGE_345C2_READY`
- fixture test mode: `LLM_ALIAS_ADJUDICATION_FIXTURE_345C2_READY`

All formal/client/production gates must remain false in every mode.

---

## Reports

Executive summary must explain:

- input 345C context
- how many alias candidates were selected
- LLM mode used
- whether live LLM was called
- suggestion distribution
- high-confidence mappings
- proposed new standards
- review-required / insufficient-evidence cases
- why no rules were changed
- why all formal/client/production gates remain false
- what 345C3 should do next

Next plan must recommend:

- `345C3 Alias Apply Simulation`
- `345C4 Human Review Package For Alias Suggestions` if many suggestions need review
- `345D Full Structured Demo Export Package` only after alias impact is measured

It must also state that 344G still waits for a genuinely human-filled 344F workbook.

---

## Allowed files

Only add/modify:

- `docs/codex_tasks/345C2_llm_assisted_metric_alias_adjudication.md`
- `datefac/benchmark/llm_assisted_metric_alias_adjudication_345c2.py`
- `datefac/benchmark/llm_assisted_metric_alias_adjudication_345c2_report.py`
- `tools/run_llm_assisted_metric_alias_adjudication_345c2.py`
- `tests/benchmark/test_llm_assisted_metric_alias_adjudication_345c2.py`
- `docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md` only if clean or explicitly requested as ledger-only

Do not modify `datefac/llm/` unless there is a tiny compatibility bug that blocks use of the existing shared client. If a change to `datefac/llm/` is necessary, explain it clearly and keep it minimal.

If the ledger is dirty, do not modify it during 345C2.

---

## Forbidden

Do not:

- modify normalization rules
- modify official alias assets
- apply alias suggestions to upstream data
- rerun MinerU
- call VLM
- scan the repo
- add dependencies
- modify production pipeline/parser/extraction/delivery/formal export logic
- modify reviewed workbooks
- modify LLM response dirs from previous tasks
- modify `input/`, `temp/`, or existing `output/` content
- auto commit/push/merge
- use `git add -A`, `git add .`, `git reset --hard`, or `git checkout --`

Do not touch protected dirty files:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

---

## Validation

Run:

```powershell
python -m py_compile datefac\benchmark\llm_assisted_metric_alias_adjudication_345c2.py datefac\benchmark\llm_assisted_metric_alias_adjudication_345c2_report.py tools\run_llm_assisted_metric_alias_adjudication_345c2.py tests\benchmark\test_llm_assisted_metric_alias_adjudication_345c2.py
python -m pytest tests\benchmark\test_llm_assisted_metric_alias_adjudication_345c2.py -q
python tools\run_llm_assisted_metric_alias_adjudication_345c2.py --metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c --output-dir D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2 --llm-mode request_only --max-alias-candidates 26
```

If runtime config is available and the user explicitly wants live LLM execution, also run:

```powershell
python tools\run_llm_assisted_metric_alias_adjudication_345c2.py --metric-candidate-normalization-coverage-345c-dir D:\_datefac\output\metric_candidate_normalization_coverage_345c --output-dir D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2_live --llm-mode live --max-alias-candidates 26
```

Tests must verify:

- outputs exist
- request-only mode works without API keys
- fixture mode produces deterministic suggestions
- live mode fails clearly when config is missing
- decision matches mode
- QA is zero
- all client/export/production gates remain false
- selected candidate count respects max limit
- response parsing and validation errors become review-required rows
- no input write-back occurs
- missing/invalid required 345C inputs fail clearly

---

## Completion report

Report:

1. Files changed.
2. Whether `datefac/llm/` was reused without scattered API calls.
3. py_compile result.
4. pytest result.
5. request-only real runner result.
6. live runner result if executed, or why not executed.
7. output dir.
8. decision and QA metrics.
9. llm_mode and runtime_config_available.
10. selected alias candidate count.
11. suggestion row count.
12. map/propose/exclude/review/insufficient-evidence counts.
13. high-confidence suggestion count.
14. needs-human-review count.
15. final gate status.
16. first file to open.
17. `git status -sb`.
18. no-touch confirmation for existing output/temp/input/reviewed workbook/old LLM response/protected dirty files.
