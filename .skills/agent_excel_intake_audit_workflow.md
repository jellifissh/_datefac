# Skill: Agent Excel Intake Audit Workflow

## Purpose

This skill defines the 348A-style workflow for auditing already extracted Excel workbooks.

It exists to prevent the Agent workflow from drifting back into raw PDF extraction, MinerU reruns, OCR, or LLM calls when the task only asks for Excel intake audit.

## Workflow Scope

The expected flow is:

```text
already extracted workbook + source PDF reference
-> Excel intake
-> audit checkers
-> review queue
-> audit report / evidence index / clean output
```

This workflow starts from extracted spreadsheet artifacts.

It does not re-extract PDFs.

## Default Inputs

A 348A-style task may use:

- one source financial PDF path;
- one already extracted Excel workbook path;
- optional evidence notes or page references;
- optional compact fixtures under `tests/agent/fixtures/`.

The source PDF can be used as identity/evidence context, but this workflow does not parse or OCR the PDF unless a future task explicitly expands the boundary.

## Default Outputs

Expected pilot outputs may include:

```text
agent_excel_intake_audit_348a_manifest.json
agent_excel_intake_audit_348a_run_summary.json
audit_report.md
evidence_index.json
review_queue.csv
clean_data.csv
```

Outputs must be written to a task-specific output directory under the current clean worktree, for example:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a
```

Do not write into old legacy output directories.

## Required Audit Categories

A minimal Excel intake audit should prefer conservative checks:

- unit semantic checking;
- period / year alignment;
- valuation metric classification;
- per-share vs total amount distinction;
- evidence presence and lineage completeness;
- duplicate or suspicious core metric detection when available.

## Evidence Policy

Do not silently pass rows without evidence.

Recommended evidence levels:

```text
STRONG_EVIDENCE
WEAK_EVIDENCE
MISSING_EVIDENCE
NOT_APPLICABLE
```

For early pilots, a workbook row with sheet name and row index but no page number should generally be treated as weak evidence or review-worthy, not as a clean pass.

## Review Policy

The default decision should be conservative.

Use:

```text
PASS
REVIEW
FAIL
```

Rows with uncertain unit semantics, missing periods, suspicious valuation metrics, weak evidence, or ambiguous meaning should go to `REVIEW`.

A first pilot producing many review rows is acceptable if the issues are explicit and explainable.

## Forbidden By Default

Do not do the following unless the task explicitly expands scope:

- do not run MinerU;
- do not call LLM/VLM APIs;
- do not run OCR;
- do not re-extract the PDF;
- do not continue 346B6;
- do not migrate old runners;
- do not mutate legacy outputs;
- do not generate formal client or production delivery artifacts.

## Validation Expectations

For code tasks in this workflow, run at least:

```powershell
python -m py_compile <changed python files>
python -m pytest tests\agent -q
```

If a real runner is available and inputs exist, run it and report manifest decision and key metrics.

If inputs are missing, do not fake results. Report missing inputs clearly.

## Manifest Discipline

Runner manifests should include at least:

```text
decision
input_stage
source_pdf_path
source_excel_path
output_dir
sheet_count
row_count_total
row_count_audited
pass_count
review_count
fail_count
issue_count_total
clean_data_row_count
review_queue_row_count
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
legacy_datefac_touched = false
legacy_outputs_touched = false
client_ready = false
production_ready = false
recommended_next_step
```

If the output is conservative and mostly review, that is not automatically failure. The manifest should explain why.

## Next-Step Pattern

After a first real pilot, prefer:

```text
result review / QA
then focused refinement
then fixture harvest
then capability migration
```

Do not jump directly from one pilot into a full production agent.
