# 344F Strict Human Review Package

## 1. Task Goal

Implement `344F Strict Human Review Package` for the DateFac project.

Current project state:

- 343O has closed the 10-row demo trusted arc.
- 344A-344D have resolved the 19-row source-check backlog.
- 344E has generated the 29-row expanded demo audit snapshot.
- 344E validation has passed:
  - `decision = EXPANDED_TRUSTED_DEMO_AUDIT_SNAPSHOT_344E_READY`
  - `review_queue_schema_version = 343A.review_queue.v1`
  - `qa_fail_count = 0`
  - `no_write_back_proof_passed = true`
  - `upstream_workbooks_unchanged = true`
  - `input_expanded_export_row_count / audit_label_row_count = 29 / 29`
  - `prior_demo_trusted_row_count / source_check_trusted_row_count = 10 / 19`
  - `source_check_confirmed_row_count / corrected_row_count = 10 / 9`
  - `expanded_demo_arc_closed = true`
  - `expanded_review_demo_package_generated = true`
  - `expanded_demo_handoff_ready = true`
  - `expanded_demo_audit_snapshot_generated = true`
  - `final_handoff_summary_generated = true`
  - `expanded_export_row_count = 29`
  - `audit_label_row_count = 29`
  - `expanded_export_scope = 343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED`
  - `export_usage = REVIEW_DEMO_ONLY`
  - `formal_client_export_allowed = false`
  - `client_ready = false`
  - `production_ready = false`
  - `global_strict_human_review_completed = false`

344F must generate a strict human review package based on the 344E output. The package will be used by a human reviewer to review all 29 expanded trusted demo rows line by line.

344F must not turn on formal client export. It prepares human review only. Apparently we still need humans to bless numbers before sending them to clients, which is annoying but financially sensible.

---

## 2. Scope

### 2.1 Input

The runner must accept:

```bash
--expanded-demo-audit-snapshot-344e-dir D:\_datefac\output\review_queue_expanded_demo_audit_snapshot_344e
--output-dir D:\_datefac\output\review_queue_strict_human_review_package_344f
```

344F should primarily read from the 344E output directory.

Important 344E input artifacts:

```text
review_queue_expanded_demo_audit_snapshot_344e_final_export_gate_snapshot.json
review_queue_expanded_demo_audit_snapshot_344e_artifact_index.md
review_queue_expanded_demo_audit_snapshot_344e_trust_chain_report.md
review_queue_expanded_demo_audit_snapshot_344e_executive_summary.md
review_queue_expanded_demo_audit_snapshot_344e_final_handoff_summary.md
```

If 344F needs the 29-row detail artifact, locate it from the 344E artifact index or from clearly named 344E outputs inside the provided 344E directory. Do not scan the whole repository.

If any required input file is missing, fail with a clear error that includes the missing path.

---

### 2.2 Output Directory

The default real output directory is:

```text
D:\_datefac\output\review_queue_strict_human_review_package_344f
```

Generate at least these files:

```text
review_queue_strict_human_review_package_344f_manifest.json
review_queue_strict_human_review_package_344f_review_rows.csv
review_queue_strict_human_review_package_344f_review_rows.json
review_queue_strict_human_review_package_344f_reviewer_checklist.md
review_queue_strict_human_review_package_344f_executive_summary.md
review_queue_strict_human_review_package_344f_artifact_index.md
review_queue_strict_human_review_package_344f_final_gate_snapshot.json
```

Only write new files under the 344F output directory. Do not write back into the 344E input directory.

---

## 3. Review Rows Requirements

Generate exactly 29 strict review rows in both:

```text
review_queue_strict_human_review_package_344f_review_rows.csv
review_queue_strict_human_review_package_344f_review_rows.json
```

Each row must include at least these fields:

```text
review_row_id
source_scope
source_stage
source_row_id
metric_name
normalized_metric_name
reported_value
normalized_value
unit
period
source_document
source_page
source_evidence_ref
audit_label
trust_status
source_check_status
correction_status
needs_strict_human_review
strict_human_review_decision
strict_human_reviewer
strict_human_reviewed_at
strict_human_review_notes
client_export_allowed
```

Field rules:

- `needs_strict_human_review` must be `true` for every row.
- `strict_human_review_decision` must initially be an empty string.
- `strict_human_reviewer` must initially be an empty string.
- `strict_human_reviewed_at` must initially be an empty string.
- `strict_human_review_notes` must initially be an empty string.
- `client_export_allowed` must be `false` for every row.
- Do not infer a strict human review result just because 344E is ready.
- If 344E uses different field names, implement a compatibility mapping and record the mapping in the 344F manifest.

---

## 4. Manifest Requirements

Generate:

```text
review_queue_strict_human_review_package_344f_manifest.json
```

It must include at least:

```json
{
  "decision": "STRICT_HUMAN_REVIEW_PACKAGE_344F_READY",
  "review_queue_schema_version": "343A.review_queue.v1",
  "input_stage": "344E",
  "input_expanded_export_row_count": 29,
  "strict_review_row_count": 29,
  "prior_demo_trusted_row_count": 10,
  "source_check_trusted_row_count": 19,
  "source_check_confirmed_row_count": 10,
  "corrected_row_count": 9,
  "qa_fail_count": 0,
  "no_write_back_proof_passed": true,
  "upstream_workbooks_unchanged": true,
  "strict_human_review_package_generated": true,
  "global_strict_human_review_completed": false,
  "formal_client_export_allowed": false,
  "client_ready": false,
  "production_ready": false,
  "export_usage": "STRICT_HUMAN_REVIEW_ONLY"
}
```

Additional fields are allowed, but the core fields above must not be removed or weakened.

---

## 5. Final Gate Snapshot Requirements

Generate:

```text
review_queue_strict_human_review_package_344f_final_gate_snapshot.json
```

It must include at least:

```json
{
  "strict_human_review_package_generated": true,
  "global_strict_human_review_completed": false,
  "formal_client_export_allowed": false,
  "client_ready": false,
  "production_ready": false,
  "expanded_review_demo_package_generated": true,
  "expanded_demo_handoff_ready": true,
  "expanded_demo_audit_snapshot_generated": true,
  "strict_review_row_count": 29,
  "client_export_allowed_row_count": 0,
  "export_usage": "STRICT_HUMAN_REVIEW_ONLY"
}
```

The following fields must remain `false`:

```text
formal_client_export_allowed
client_ready
production_ready
global_strict_human_review_completed
```

Do not create formal client export artifacts in 344F.

---

## 6. Reviewer Checklist Requirements

Generate:

```text
review_queue_strict_human_review_package_344f_reviewer_checklist.md
```

It must state:

1. This package is for strict human review only.
2. The 29 rows come from:
   - 10 rows from the 343O prior demo trusted arc.
   - 19 rows from the 344A-344D source-check resolved backlog.
3. 344F does not mean the package is ready for formal client delivery.
4. The reviewer must check each row for:
   - metric name correctness
   - value correctness
   - unit correctness
   - period correctness
   - source evidence support
   - correction reasonableness
   - whether the row should be allowed into a later formal export candidate
5. The reviewer should only fill or edit:
   - `strict_human_review_decision`
   - `strict_human_reviewer`
   - `strict_human_reviewed_at`
   - `strict_human_review_notes`
6. The reviewer must not edit original evidence fields, metric fields, or source fields.
7. 344G will ingest the completed human review result later.

---

## 7. Executive Summary Requirements

Generate:

```text
review_queue_strict_human_review_package_344f_executive_summary.md
```

It must include:

- 344F decision.
- Input 344E directory.
- Output directory.
- Strict review row count: 29.
- Source split: 10 prior demo trusted rows and 19 source-check trusted rows.
- Source-check result split: 10 confirmed rows and 9 corrected rows.
- Gate status:
  - `formal_client_export_allowed = false`
  - `client_ready = false`
  - `production_ready = false`
  - `global_strict_human_review_completed = false`
- Recommended next steps:
  - 344G ingest strict human review result.
  - 344H strict reviewed final gate snapshot.

---

## 8. Artifact Index Requirements

Generate:

```text
review_queue_strict_human_review_package_344f_artifact_index.md
```

It must list all 344F output files and explain what each file is used for.

---

## 9. Allowed File Changes

Only add or modify these files:

```text
docs/codex_tasks/344F_strict_human_review_package.md
datefac/review_queue/strict_human_review_package_344f.py
datefac/benchmark/review_queue_strict_human_review_package_344f.py
datefac/benchmark/review_queue_strict_human_review_package_344f_report.py
tools/run_review_queue_strict_human_review_package_344f.py
tests/benchmark/test_review_queue_strict_human_review_package_344f.py
docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md
```

If another file truly must be changed, stop and explain why before changing it.

---

## 10. Forbidden Changes

Do not:

- scan the whole repository
- perform broad refactors
- modify unrelated files
- auto commit
- auto push
- auto merge
- delete important code
- change the tech stack
- add dependencies
- modify production pipeline
- modify parser logic
- modify extraction logic
- modify delivery logic
- modify formal client export logic
- modify reviewed workbook files
- modify LLM response directories
- modify existing `input/`, `temp/`, or `output/` content
- write back into the 344E input directory

Protected dirty files must not be touched:

```text
datefac/benchmark/batch_row_text_delivery_benchmark.py
datefac/extraction/row_text_metric_extractor.py
datefac/pipeline/batch_ppstructure_row_text_pipeline.py
tools/run_batch_ppstructure_outputs_320g.py
```

344F may only create new output files under the new 344F output directory.

---

## 11. Validation Commands

Run py_compile:

```bash
python -m py_compile datefac\review_queue\strict_human_review_package_344f.py datefac\benchmark\review_queue_strict_human_review_package_344f.py datefac\benchmark\review_queue_strict_human_review_package_344f_report.py tools\run_review_queue_strict_human_review_package_344f.py tests\benchmark\test_review_queue_strict_human_review_package_344f.py
```

Run pytest:

```bash
python -m pytest tests\benchmark\test_review_queue_strict_human_review_package_344f.py -q
```

Run the real runner:

```bash
python tools\run_review_queue_strict_human_review_package_344f.py --expanded-demo-audit-snapshot-344e-dir D:\_datefac\output\review_queue_expanded_demo_audit_snapshot_344e --output-dir D:\_datefac\output\review_queue_strict_human_review_package_344f
```

Tests must cover at least:

1. 344F package can be generated.
2. Review rows count is 29.
3. Manifest contains:
   - `decision = STRICT_HUMAN_REVIEW_PACKAGE_344F_READY`
   - `strict_review_row_count = 29`
   - `qa_fail_count = 0`
   - `no_write_back_proof_passed = true`
   - `upstream_workbooks_unchanged = true`
4. Final gate contains:
   - `formal_client_export_allowed = false`
   - `client_ready = false`
   - `production_ready = false`
   - `global_strict_human_review_completed = false`
5. Review rows contain:
   - every row has `needs_strict_human_review = true`
   - every row has `client_export_allowed = false`
   - every row has empty strict human review fields initially
6. Artifact index exists.
7. Reviewer checklist exists.
8. Executive summary exists.
9. 344E input directory is not written back.
10. Upstream workbook is not modified.
11. Protected dirty files are not modified.

---

## 12. Completion Report Required From Codex

After implementation, report:

1. Files changed.
2. Whether py_compile passed.
3. Whether pytest passed.
4. Whether the real runner passed.
5. Output directory.
6. Decision / QA metrics.
7. Strict review row count.
8. Prior demo trusted row count / source-check trusted row count.
9. Source-check confirmed row count / corrected row count.
10. Final gate status:
    - `strict_human_review_package_generated`
    - `global_strict_human_review_completed`
    - `formal_client_export_allowed`
    - `client_ready`
    - `production_ready`
    - `export_usage`
11. The first file the user should open.
12. `git status -sb`.
13. Whether `output/`, `temp/`, `input/`, reviewed workbook, LLM response, and protected dirty files were not modified.
