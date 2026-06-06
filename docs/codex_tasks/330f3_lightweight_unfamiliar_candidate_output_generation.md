# DateFac 330F3 Task
## Lightweight Unfamiliar Candidate Output Generation

## Context

330F2 unfamiliar output preparation is complete and pushed.

330F2 result:

```text
D:\_datefac\input\unfamiliar exists
unfamiliar input PDF count = 13
D:\_datefac\output\unfamiliar_trust_split does not exist before run
D:\_datefac\output\delivery_benchmark_unfamiliar does not exist
matched_cached_output_count = 0
prepared_candidate_row_count = 0
can_rerun_330f = false
unfamiliar_output_preparation_status = WAITING_FOR_PARSER_OUTPUTS
qa_fail_count = 0
decision = UNFAMILIAR_OUTPUT_PREPARATION_330F2_WAITING
```

330F framework is implemented but waiting:

```text
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
unfamiliar_source_status = missing_or_empty
scored_unfamiliar_record_count = 0
decision = TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_WAITING_FOR_UNFAMILIAR_OUTPUTS
```

The project now needs lightweight candidate rows for the 13 unfamiliar PDFs before 330F can run a real unfamiliar Trust Engine benchmark.

## Goal

Implement 330F3: generate lightweight candidate outputs for the 13 unfamiliar PDFs in:

```text
D:\_datefac\input\unfamiliar
```

The output must be consumable by 330F and 330F2, preferably:

```text
D:\_datefac\output\unfamiliar_trust_split
```

330F3 is an output-generation bridge between existing local parser/extraction capabilities and the Trust Engine sidecar benchmark. It must remain sidecar-oriented and must not modify production routing or official assets.

## Important positioning

330F3 is allowed to run an existing local lightweight extraction/export path if one already exists in the repository.

330F3 should not create a new parser system. It should inspect and reuse existing tools/pipelines where possible, especially any current MinerU / row text / trust split / delivery benchmark scripts already present in the project.

If no safe runnable path exists, produce a clear not-ready report instead of inventing fake candidate rows.

## Recommended Codex reasoning level

```text
High
```

Use `High` because this task touches the boundary between local parser outputs and Trust Engine sidecar benchmark. It must inspect existing scripts and avoid contaminating production code or known dirty files.

Use `Ultra/Very High` only if the local environment forces debugging parser/runtime failures across multiple existing scripts.

## Hard constraints

- Do not modify production pipeline behavior.
- Do not modify existing parser/extraction/delivery behavior unless only adding a new sidecar wrapper/export utility.
- Do not modify official mapping / override assets.
- Do not apply semantic rules to production data.
- Do not mark anything trusted in production.
- Do not call LLM or semantic adjudicator.
- Do not start a new alias/scope/unit rule mining cycle.
- Do not commit output, temp, input PDFs, input/semantic_adjudicator_responses_*, E:\mineru_lab, or existing dirty files.
- Do not use `git add -A` or `git add .`.
- Only precisely add 330F3 source/report/runner/test files.

Parser/runtime constraints:

- Prefer existing cached or already generated local parser outputs if discovered.
- If running parser/extraction is necessary, use the existing lightest local path that can produce candidate-like rows.
- Do not install new heavy dependencies.
- Do not download new models.
- Do not run LLM/VLM adjudication.
- Do not run remote services.
- If MinerU must be used, use the already installed local setup and keep outputs under `D:\_datefac\output\unfamiliar_*`; do not write into E:\mineru_lab or commit parser outputs.
- If existing pipeline scripts are dirty in the working tree, inspect but do not modify them.

Existing dirty files to leave untouched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
input/semantic_adjudicator_responses_322d/
input/semantic_adjudicator_responses_322f/
temp/
```

## Suggested files

New files:

```text
datefac/trust/unfamiliar_candidate_output_generation_330f3.py
datefac/trust/unfamiliar_candidate_output_generation_330f3_report.py
tools/run_unfamiliar_candidate_output_generation_330f3.py
tests/trust/test_unfamiliar_candidate_output_generation_330f3.py
```

Possible precise updates only if needed:

```text
datefac/trust/__init__.py
```

Do not edit production pipeline modules.

## Inputs

Primary unfamiliar PDF input directory:

```text
D:\_datefac\input\unfamiliar
```

Previous readiness/report inputs:

```text
D:\_datefac\output\unfamiliar_output_preparation_330f2
D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
D:\_datefac\output\deduped_candidate_trust_benchmark_330e
D:\_datefac\output\trust_engine_scoring_330b
```

Existing local output roots to inspect for reusable parser outputs:

```text
D:\_datefac\output
D:\_datefac\output\mineru_outputs
D:\_datefac\output\batch_outputs
D:\_datefac\output\delivery
D:\_datefac\output\router_mineru_trust_split_322b2
```

Official assets may be read only for no-apply proof:

```text
D:\_datefac\data\overrides\semantic_alias_candidates.json
D:\_datefac\data\mapping\formal_scope_rules.json
```

## Required behavior

1. Validate that 330F2 is waiting for parser outputs:

```text
decision = UNFAMILIAR_OUTPUT_PREPARATION_330F2_WAITING
unfamiliar_output_preparation_status = WAITING_FOR_PARSER_OUTPUTS
discovered_unfamiliar_input_pdf_count = 13
matched_cached_output_count = 0
prepared_candidate_row_count = 0
qa_fail_count = 0
```

2. Discover the 13 unfamiliar PDFs under `D:\_datefac\input\unfamiliar`.
3. Inspect existing repository tools and output directories for the safest already available path to generate candidate-like rows.
4. Prefer one of these approaches, in this order:

### Approach A: Reuse existing cached parser outputs for those exact PDFs

If matching parser outputs already exist after deeper search, normalize them into `unfamiliar_trust_split`.

### Approach B: Run an existing lightweight local candidate export path

Use an existing project script if available to process the 13 PDFs and emit candidate-like rows. Keep this sidecar-oriented.

### Approach C: Generate a not-ready report

If no safe path exists, do not fabricate data. Produce a not-ready result with commands the user should run to generate parser outputs.

5. Normalized output rows must be written to:

```text
D:\_datefac\output\unfamiliar_trust_split\unfamiliar_candidate_rows.jsonl
D:\_datefac\output\unfamiliar_trust_split\unfamiliar_candidate_rows.xlsx
```

6. Required columns/fields:

```text
candidate_id
metric_label_raw
normalized_metric
value
unit
year
parser_sources
evidence_refs
risk_flags
existing_status
source_pdf
source_artifact
source_page
row_text
table_id
```

7. Candidate IDs must be stable and deterministic, e.g. hash of:

```text
source_pdf + source_page + table_id + row_text + metric_label_raw + normalized_metric + value + unit + year
```

8. If only partial fields are available, still write compatible rows but record missing-field counts.
9. Produce summary metrics:

```text
unfamiliar_pdf_count
processed_pdf_count
failed_pdf_count
prepared_candidate_row_count
prepared_candidate_file_count
source_output_reuse_count
newly_generated_output_count
missing_required_field_count_by_field
can_rerun_330f
```

10. Confirm official assets are not modified.
11. Generate QA, no-apply proof, output manifest, and report.

## Output directories

Runner/report output:

```text
D:\_datefac\output\unfamiliar_candidate_output_generation_330f3
```

Prepared source for 330F rerun:

```text
D:\_datefac\output\unfamiliar_trust_split
```

Suggested outputs:

```text
unfamiliar_candidate_output_generation_330f3_summary.json
unfamiliar_candidate_output_generation_330f3_qa.json
unfamiliar_candidate_output_generation_330f3_manifest.json
unfamiliar_candidate_output_generation_330f3_no_apply_proof.json
unfamiliar_candidate_output_generation_330f3_report.md
```

Prepared outputs:

```text
D:\_datefac\output\unfamiliar_trust_split\unfamiliar_candidate_rows.jsonl
D:\_datefac\output\unfamiliar_trust_split\unfamiliar_candidate_rows.xlsx
D:\_datefac\output\unfamiliar_trust_split\unfamiliar_candidate_manifest.json
```

## Expected successful result

If candidate outputs are generated or normalized successfully:

```text
validated_330f2_waiting_for_parser_outputs = true
unfamiliar_pdf_count = 13
processed_pdf_count > 0
prepared_candidate_row_count > 0
can_rerun_330f = true
output_dir_for_330f = D:\_datefac\output\unfamiliar_trust_split
no_official_asset_modification_during_330f3 = true
qa_fail_count = 0
decision = UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_READY_FOR_330F_RERUN
```

If no safe candidate generation path exists:

```text
validated_330f2_waiting_for_parser_outputs = true
unfamiliar_pdf_count = 13
prepared_candidate_row_count = 0
can_rerun_330f = false
qa_fail_count = 0
decision = UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_WAITING_FOR_SAFE_EXPORT_PATH
```

If blocking QA fails:

```text
UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_NOT_READY
```

## Suggested command

```bash
python tools/run_unfamiliar_candidate_output_generation_330f3.py \
  --unfamiliar-input-dir D:\_datefac\input\unfamiliar \
  --previous-preparation-dir D:\_datefac\output\unfamiliar_output_preparation_330f2 \
  --prepared-output-dir D:\_datefac\output\unfamiliar_trust_split \
  --output-dir D:\_datefac\output\unfamiliar_candidate_output_generation_330f3
```

## Compile checks

```bash
python -m py_compile datefac\trust\unfamiliar_candidate_output_generation_330f3.py datefac\trust\unfamiliar_candidate_output_generation_330f3_report.py tools\run_unfamiliar_candidate_output_generation_330f3.py tests\trust\test_unfamiliar_candidate_output_generation_330f3.py
```

Run only the new lightweight trust tests if tests are added.

## After successful 330F3

If 330F3 generates rows, rerun 330F with:

```bash
python tools\run_unfamiliar_pdf_trust_benchmark_330f.py \
  --deduped-candidate-benchmark-dir D:\_datefac\output\deduped_candidate_trust_benchmark_330e \
  --trust-scoring-dir D:\_datefac\output\trust_engine_scoring_330b \
  --unfamiliar-source-dir D:\_datefac\output\unfamiliar_trust_split \
  --output-dir D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f
```

## Git workflow

Use precise adds only:

```bash
git add datefac/trust/unfamiliar_candidate_output_generation_330f3.py
git add datefac/trust/unfamiliar_candidate_output_generation_330f3_report.py
git add tools/run_unfamiliar_candidate_output_generation_330f3.py
git add tests/trust/test_unfamiliar_candidate_output_generation_330f3.py
```

If existing trust files are deliberately updated:

```bash
git add datefac/trust/__init__.py
```

Commit:

```text
Add 330F3 unfamiliar candidate output generation
```

## Final report expected from Codex

Report:

1. Modified files.
2. Commands run.
3. Unfamiliar PDF count and file list summary.
4. Existing output discovery result.
5. Generation/export approach used: A/B/C.
6. Prepared output dir.
7. Prepared candidate row count.
8. Missing-field counts.
9. Whether 330F can be rerun.
10. Recommended rerun command for 330F.
11. Official asset modification confirmation.
12. QA fail count.
13. Decision.
14. Git status result.
15. Commit hash.
16. Push result.
17. Residual risks.
