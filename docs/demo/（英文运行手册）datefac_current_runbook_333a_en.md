# DateFac Current Runbook 333A (English)

## 1. Scope

This runbook covers the current `330K2` through `332A` sidecar, demo, preview, and no-write-back path. It is not a production operations manual. It does not authorize changes to the production pipeline, parser, extraction logic, delivery logic, or official assets. Its purpose is narrower and more practical: help a careful operator understand the current stage sequence, verify upstream outputs, run the correct commands, inspect the right artifacts, and avoid unsafe Git or staging mistakes.

Use this runbook if you need to:

- package unit-risk rows for manual review
- read a filled review workbook and simulate the effect of manual decisions
- refresh the reviewed preview export
- refresh demo-facing documentation
- audit the final demo narrative for consistency and overclaim risk

Do not use this runbook as justification to:

- rewrite parser behavior
- rewrite extraction rules
- modify delivery outputs in the main pipeline
- edit official assets casually
- stage output artifacts

## 2. Environment Assumptions

The current instructions assume:

- Windows environment
- repository root at `D:\_datefac`
- PowerShell terminal
- Python available in the current environment
- upstream project stages already exist locally

The important completed stages behind the current reviewed preview narrative are:

- `330L` client-style export preview
- `331A` demo packaging
- `330K2` human unit review package
- `330K3` human unit review apply simulation
- `330K4` reviewed export refresh
- `331B` demo packaging refresh after human unit review
- `332A` demo release audit

The current high-level state that all documentation should respect is:

- `project_status = DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW`
- `client_ready = false`
- `production_ready = false`

## 3. Important Paths

### Repository and docs paths

| Type | Path |
|---|---|
| Repository root | `D:\_datefac` |
| Demo docs | `D:\_datefac\docs\demo` |
| Codex task docs | `D:\_datefac\docs\codex_tasks` |

### Output directories

| Stage | Path |
|---|---|
| 330L | `D:\_datefac\output\client_style_export_preview_330l` |
| 331A | `D:\_datefac\output\demo_packaging_331a` |
| 330K2 | `D:\_datefac\output\human_unit_review_330k2` |
| 330K3 | `D:\_datefac\output\human_unit_review_apply_simulation_330k3` |
| 330K4 | `D:\_datefac\output\reviewed_export_refresh_330k4` |
| 331B | `D:\_datefac\output\demo_packaging_331b` |
| 332A | `D:\_datefac\output\demo_release_audit_332a` |

### Frequently inspected files

- `D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_preview.xlsx`
- `D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_summary.json`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_template.xlsx`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx`
- `D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_summary.json`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3\human_unit_review_apply_simulation_330k3_apply_plan.xlsx`
- `D:\_datefac\output\human_unit_review_apply_simulation_330k3\human_unit_review_apply_simulation_330k3_summary.json`
- `D:\_datefac\output\reviewed_export_refresh_330k4\reviewed_export_refresh_330k4_preview.xlsx`
- `D:\_datefac\output\reviewed_export_refresh_330k4\reviewed_export_refresh_330k4_summary.json`
- `D:\_datefac\output\demo_packaging_331b\demo_packaging_331b_summary.json`
- `D:\_datefac\output\demo_release_audit_332a\demo_release_audit_332a_summary.json`

## 4. Required Upstream Outputs

### 330K2 requirements

The 330K2 stage packages the review queue. It expects:

- `demo_packaging_331a`
- `client_style_export_preview_330l`
- `unit_signal_review_330k`
- `delivery_report_refresh_after_330k_330j2`

Before running it, check that the 330L preview workbook and 330L summary both exist. Also check that the 331A summary exists.

### 330K3 requirements

The 330K3 stage simulates the effect of manual review decisions. It expects:

- the 330K2 output directory
- a filled review workbook
- the 331A summary context
- the 330L preview context

If the review workbook is not actually filled, the stage may still run into validation issues or produce unusable results.

### 330K4 requirements

The 330K4 stage refreshes the reviewed preview. It expects:

- the 330L baseline preview
- the 330K2 review package
- the 330K3 apply simulation

This stage should never be interpreted as a write-back step. It produces a refreshed preview workbook, not a production replacement.

### 331B requirements

The 331B stage refreshes public-facing demo materials. It expects:

- the 331A demo packaging baseline
- the 330K4 reviewed export refresh
- the 330K3 apply simulation
- the 330K2 review package
- the 330L preview baseline

The purpose is to align the story with the reviewed preview state.

### 332A requirements

The 332A stage audits the final demo narrative. It expects:

- the 331B demo packaging
- the 330K4 reviewed export refresh
- the 331A demo packaging
- the relevant demo docs under `docs\demo`

This stage checks wording and consistency. It does not produce new parser outputs.

## 5. Exact Commands

Keep Windows paths, stage names, and runner names exactly as they are.

### 330K2

```powershell
python tools\run_human_unit_review_330k2.py --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --unit-signal-review-dir D:\_datefac\output\unit_signal_review_330k --delivery-report-refresh-dir D:\_datefac\output\delivery_report_refresh_after_330k_330j2 --output-dir D:\_datefac\output\human_unit_review_330k2
```

### 330K3

```powershell
python tools\run_human_unit_review_apply_simulation_330k3.py --filled-review-workbook D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --demo-packaging-dir D:\_datefac\output\demo_packaging_331a --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3
```

### 330K4

```powershell
python tools\run_reviewed_export_refresh_330k4.py --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --output-dir D:\_datefac\output\reviewed_export_refresh_330k4
```

### 331B

```powershell
python tools\run_demo_packaging_331b.py --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --apply-simulation-dir D:\_datefac\output\human_unit_review_apply_simulation_330k3 --human-unit-review-dir D:\_datefac\output\human_unit_review_330k2 --client-style-export-preview-dir D:\_datefac\output\client_style_export_preview_330l --output-dir D:\_datefac\output\demo_packaging_331b
```

### 332A

```powershell
python tools\run_demo_release_audit_332a.py --demo-packaging-331b-dir D:\_datefac\output\demo_packaging_331b --reviewed-export-refresh-dir D:\_datefac\output\reviewed_export_refresh_330k4 --demo-packaging-331a-dir D:\_datefac\output\demo_packaging_331a --docs-demo-dir D:\_datefac\docs\demo --output-dir D:\_datefac\output\demo_release_audit_332a
```

## 6. Expected Output Directories And Main Artifacts

| Stage | Output Directory | First File To Inspect |
|---|---|---|
| 330K2 | `D:\_datefac\output\human_unit_review_330k2` | `human_unit_review_330k2_review_template.xlsx` |
| 330K3 | `D:\_datefac\output\human_unit_review_apply_simulation_330k3` | `human_unit_review_apply_simulation_330k3_apply_plan.xlsx` |
| 330K4 | `D:\_datefac\output\reviewed_export_refresh_330k4` | `reviewed_export_refresh_330k4_preview.xlsx` |
| 331B | `D:\_datefac\output\demo_packaging_331b` | `demo_packaging_331b_summary.json` |
| 332A | `D:\_datefac\output\demo_release_audit_332a` | `demo_release_audit_332a_summary.json` |

If you want to understand “what changed” at each stage, the summary JSON is usually the fastest starting point, and the workbook is usually the best contextual follow-up.

## 7. Expected Summary Metrics

The current reviewed-preview chain should align with these values:

| Stage | Metric | Expected Value |
|---|---|---:|
| 330L | `prepared_candidate_row_count` | 117 |
| 330L | `trusted_sheet_row_count` | 96 |
| 330L | `review_required_sheet_row_count` | 21 |
| 330K2 | `packaged_unit_review_row_count` | 21 |
| 330K2 | `unit_missing_count` | 18 |
| 330K2 | `unit_conflict_risk_count` | 12 |
| 330K3 | `apply_plan_row_count` | 21 |
| 330K3 | `confirm_unit_count` | 2 |
| 330K3 | `reject_unit_count` | 18 |
| 330K3 | `needs_more_context_count` | 1 |
| 330K4 | `reviewed_trusted_preview_row_count` | 98 |
| 330K4 | `human_rejected_row_count` | 18 |
| 330K4 | `remaining_review_required_after_unit_review_count` | 1 |
| 331B | `project_status` | `DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW` |
| 332A | `overclaim_risk_count` | 0 |
| 332A | `qa_fail_count` | 0 |

These numbers are not decoration. They are the current public story of the demo state. If documentation says something else, the documentation is wrong.

## 8. Validation Commands

For most task types, start with:

```powershell
git status -sb
python -m py_compile <changed_python_files>
python -m pytest <relevant_test_file> -q
```

For this current demo path, also inspect the key summaries directly:

```powershell
Get-Content D:\_datefac\output\client_style_export_preview_330l\client_style_export_preview_330l_summary.json
Get-Content D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_summary.json
Get-Content D:\_datefac\output\human_unit_review_apply_simulation_330k3\human_unit_review_apply_simulation_330k3_summary.json
Get-Content D:\_datefac\output\reviewed_export_refresh_330k4\reviewed_export_refresh_330k4_summary.json
Get-Content D:\_datefac\output\demo_packaging_331b\demo_packaging_331b_summary.json
Get-Content D:\_datefac\output\demo_release_audit_332a\demo_release_audit_332a_summary.json
```

Check:

- `decision`
- `qa_fail_count`
- `blocking_reasons`
- no official-asset modification proof fields

## 9. Git Safety Rules

These rules are strict because the project often operates in a workspace with existing dirty files and large output artifacts.

Never do the following:

- `git add -A`
- `git add .`
- stage `output/*`
- stage protected dirty files
- stage manual response or temporary directories casually

Always prefer precise staging:

- `git add path\to\one_file`
- verify `git status -sb`
- only then commit

If a rebase or pull is blocked by protected dirty files, stash only the protected paths you were explicitly told to protect. Do not stash the entire repository unless there is an explicit reason.

## 10. Protected Dirty Files

The current protected dirty paths are:

- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

Treat these as out of scope for the current documentation and sidecar tasks unless a separate task explicitly tells you otherwise.

## 11. What To Do Before Committing

Before any commit related to this demo path:

1. run `git status -sb`
2. confirm only task-relevant files were modified
3. rerun the minimum necessary validation
4. check that metrics and stage names are still consistent
5. confirm that `output/*` is not staged
6. confirm that protected dirty files are not staged
7. stage files one by one with precise `git add`

The most common avoidable mistake is to prepare a clean sidecar or docs commit and accidentally include unrelated dirty files or output artifacts.

## 12. What Must Never Be Staged

At minimum, do not stage:

- `output/*`
- `temp/*`
- `input/semantic_adjudicator_responses_*`
- unrelated production code
- official assets
- protected dirty files

If you are unsure whether a file is generated output or source material, stop and inspect it before staging.

## 13. Troubleshooting Checklist

If a command fails, work through these checks in order:

1. Does the required upstream output directory exist?
2. Does the expected summary JSON exist?
3. Does the prior summary show a ready decision?
4. Is the workbook path correct?
5. Was the workbook actually filled?
6. Are you confusing the 330L baseline preview with the 330K4 reviewed preview?
7. Are you reading 331A docs when you mean 331B docs?
8. Did a local unstaged change shift the workspace state?
9. Is there a `.git/index.lock` or permission issue?

This order matters because many failures are not code logic bugs. They are context, version, or path mismatches.

## 14. Current Boundaries

The current runbook is built around the following boundary terms, and every operator should keep them visible:

- sidecar
- demo
- preview
- no write-back
- human review
- current limitations

If you remove these boundary terms from your explanation, the project starts sounding much more mature than it actually is. That is exactly what the release audit tries to prevent.
