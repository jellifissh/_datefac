# 348A AI-Extracted Excel Intake Audit Pilot

## 1. Goal

Implement the first minimal DateFac Agent functional pilot.

348A starts from an already extracted Excel workbook and a corresponding PDF. It should audit the extracted spreadsheet using conservative, pure-function style checks and produce review-oriented outputs.

The goal is:

```text
Audit already extracted financial spreadsheet data against a source PDF/evidence context.
```

The goal is not:

```text
Re-extract the PDF, call LLMs, run MinerU, or build a full generic Agent.
```

---

## 2. Required context

Read these files first:

```text
datefac_agent/README.md
datefac_agent/PROJECT_BACKGROUND.md
datefac_agent/CODE_MIGRATION_PLAN.md
datefac_agent/FOUNDATION_TASK.md
docs/agent/AGENT_ARCHITECTURE.md
docs/agent/FIXTURE_STRATEGY.md
docs/agent/348A_EXCEL_INTAKE_AUDIT_PLAN.md
docs/agent/348A_INPUT_OUTPUT_CONTRACT.md
docs/legacy/LEGACY_ASSET_MAP.md
docs/project_strategy/348_agent_pivot_brief.md
```

They define the pivot, the first agent architecture boundary, fixture strategy, and 348A contract.

---

## 3. Working directory

Use the clean worktree:

```text
D:\_datefac_agent
```

Expected branch:

```text
pivot/348-agent-foundation
```

Before editing, run:

```powershell
cd D:\_datefac_agent
git pull --ff-only origin pivot/348-agent-foundation
git status -sb
git branch --show-current
```

The worktree must be clean before starting. If there are uncommitted changes, stop and report.

---

## 4. Input files for the pilot

Use the local user-provided files:

```text
D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf
D:\_datefac_agent\input\安井食品研报数据汇总.xlsx
```

If these files are not already present under `D:\_datefac_agent\input\`, do not invent paths. Ask the user to copy them there or support explicit CLI args pointing to their actual locations.

Do not modify the source PDF or source Excel.

---

## 5. Output directory

Write only under:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a
```

Do not write into old legacy output directories such as:

```text
D:\_datefac\output\345D*
D:\_datefac\output\346B*
D:\_datefac\output\346B4*
D:\_datefac\output\346B5*
D:\_datefac\output\larger_expansion_qa_audit_346b5q
```

---

## 6. Non-negotiable safety rules

Do not delete legacy source code.

Do not move the old `datefac/` package.

Do not rewrite old runners under `tools/`.

Do not touch old `D:\_datefac` protected dirty files.

Do not mutate old `input/`, `output/`, `temp/`, or `data/` directories.

Do not modify old 345D / 346B / 346B4 / 346B5 / 346B5Q outputs.

Do not run MinerU.

Do not call LLM/VLM APIs.

Do not continue 346B6.

Do not create client or production delivery artifacts.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

Only add explicitly named files.

---

## 7. Implementation scope

This is a minimal pilot. Implement only enough to read spreadsheet-like extracted data, normalize it into internal records, run conservative audits, and generate review-oriented outputs.

### 7.1 Intake

Create or update:

```text
datefac_agent/intake/excel_intake.py
```

Responsibilities:

- read an `.xlsx` workbook;
- enumerate sheets;
- extract rows into lightweight records;
- preserve sheet name, row index, column names, raw values;
- do not perform heavy business logic inside intake;
- return structured records for audit.

If `openpyxl` is available, use it. If not available, stop and report dependency issue clearly. Do not use LibreOffice or PDF tooling for the spreadsheet.

### 7.2 Schemas

Update:

```text
datefac_agent/schemas/audit_models.py
```

Keep existing foundation models but extend minimally if needed.

Suggested additions:

```text
SpreadsheetRow
WorkbookIntakeResult
AuditDecision
AuditSummary
```

Keep models simple. Use dataclasses unless Pydantic is already an established dependency in this branch.

### 7.3 Audit checkers

Create minimal pure-function style modules:

```text
datefac_agent/audit/unit_semantic_checker.py
datefac_agent/audit/period_alignment_checker.py
datefac_agent/audit/valuation_metric_checker.py
datefac_agent/audit/evidence_checker.py
```

First-pass checker behavior should be conservative and explainable.

#### Unit checker

Should flag likely mismatches or missing unit context, especially:

- percentages / margins;
- valuation multiples such as P/E, P/B, EV/EBITDA;
- per-share metrics such as EPS, 每股收益, 每股净资产, 每股经营现金流;
- monetary amounts such as revenue, net profit, assets, liabilities.

#### Period checker

Should identify common year/period labels such as:

```text
2024A
2025A
2026E
2027E
2028E
2026Q1
```

It should flag rows or sheets with suspicious missing period information when period columns are expected.

#### Valuation checker

Should flag valuation metrics that appear to be misclassified or have suspicious units:

```text
P/E
P/B
EV/EBITDA
PE
PB
```

#### Evidence checker

For 348A, evidence can be minimal.

It should not perform OCR or PDF parsing.

It should record source PDF path, sheet name, row index, and whether explicit page/evidence reference exists if present in the workbook.

If evidence is not available, make that visible as `weak_evidence` or `missing_evidence`, not a silent pass.

### 7.4 Review queue

Create:

```text
datefac_agent/review/review_queue_builder.py
```

Responsibilities:

- combine audit issues per row;
- assign decision: `PASS`, `REVIEW`, or `FAIL`;
- keep the default conservative;
- output structured review rows for delivery.

### 7.5 Delivery

Create:

```text
datefac_agent/delivery/audit_report_writer.py
datefac_agent/delivery/evidence_index_writer.py
```

Responsibilities:

- write `audit_report.md`;
- write `evidence_index.json`;
- optionally write `review_queue.csv`;
- optionally write `clean_data.csv`.

Do not require `.xlsx` output in the first pilot if CSV is simpler and safer. The contract allows equivalent review-oriented outputs.

### 7.6 Runner

Create:

```text
tools/run_agent_excel_intake_audit_348a.py
```

CLI args:

```text
--pdf-path
--excel-path
--output-dir
```

Example:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348a
```

Runner should produce a manifest and summary.

---

## 8. Required outputs

Under output dir:

```text
D:\_datefac_agent\output\agent_excel_intake_audit_348a
```

Generate:

```text
agent_excel_intake_audit_348a_manifest.json
agent_excel_intake_audit_348a_run_summary.json
audit_report.md
evidence_index.json
review_queue.csv
clean_data.csv
```

If any output cannot be generated, record the reason in manifest and run summary.

---

## 9. Manifest metrics

Manifest should include:

```text
decision
input_stage = AI_EXTRACTED_EXCEL_INTAKE_AUDIT_PILOT_348A
qa_fail_count
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
unit_issue_count
period_issue_count
valuation_issue_count
evidence_issue_count
clean_data_row_count
review_queue_row_count
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
legacy_datefac_touched = false
legacy_outputs_touched = false
official_rules_modified = false
official_alias_assets_modified = false
formal_export_generated = false
demo_export_only = true
formal_client_export_allowed = false
client_ready = false
production_ready = false
recommended_next_step
```

Possible `decision` values:

```text
AI_EXCEL_INTAKE_AUDIT_348A_READY
AI_EXCEL_INTAKE_AUDIT_348A_INPUT_MISSING
AI_EXCEL_INTAKE_AUDIT_348A_DEPENDENCY_MISSING
AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
```

---

## 10. Tests

Create:

```text
tests/agent/test_agent_excel_intake_audit_348a.py
```

Minimum tests:

- package imports still work;
- schema models can be constructed;
- unit checker flags obvious unit mismatch;
- period checker detects expected period labels;
- valuation checker treats PE/PB/EV/EBITDA as multiple-like metrics;
- review queue builder returns REVIEW when issues exist;
- runner helper functions can write minimal outputs to a temporary directory if feasible.

Do not require the real PDF/Excel in unit tests. Use compact in-memory fixtures.

---

## 11. Validation commands

Run:

```powershell
cd D:\_datefac_agent

python -m py_compile datefac_agent\schemas\audit_models.py datefac_agent\intake\excel_intake.py datefac_agent\audit\unit_semantic_checker.py datefac_agent\audit\period_alignment_checker.py datefac_agent\audit\valuation_metric_checker.py datefac_agent\audit\evidence_checker.py datefac_agent\review\review_queue_builder.py datefac_agent\delivery\audit_report_writer.py datefac_agent\delivery\evidence_index_writer.py tools\run_agent_excel_intake_audit_348a.py tests\agent\test_agent_foundation_imports.py tests\agent\test_agent_excel_intake_audit_348a.py

python -m pytest tests\agent\test_agent_foundation_imports.py tests\agent\test_agent_excel_intake_audit_348a.py -q
```

Then run the real pilot if input files exist:

```powershell
python tools\run_agent_excel_intake_audit_348a.py --pdf-path D:\_datefac_agent\input\H3_AP202606081823352906_1_331fresh_20260615_21591.pdf --excel-path D:\_datefac_agent\input\安井食品研报数据汇总.xlsx --output-dir D:\_datefac_agent\output\agent_excel_intake_audit_348a
```

If real input files do not exist locally, do not fake the result. Report missing inputs and keep tests passing.

---

## 12. Expected changed files

Expected source/test files:

```text
datefac_agent/intake/excel_intake.py
datefac_agent/audit/unit_semantic_checker.py
datefac_agent/audit/period_alignment_checker.py
datefac_agent/audit/valuation_metric_checker.py
datefac_agent/audit/evidence_checker.py
datefac_agent/review/review_queue_builder.py
datefac_agent/delivery/audit_report_writer.py
datefac_agent/delivery/evidence_index_writer.py
datefac_agent/schemas/audit_models.py
tools/run_agent_excel_intake_audit_348a.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Optional docs update:

```text
docs/agent/348A_EXCEL_INTAKE_AUDIT_PLAN.md
docs/project_milestones/PROJECT_MILESTONE_LEDGER_项目进程.md
```

Do not modify unrelated legacy code.

---

## 13. Completion report

Report:

1. Files created or modified.
2. Whether branch is `pivot/348-agent-foundation`.
3. Whether worktree was clean before editing.
4. Whether input files existed locally.
5. py_compile result.
6. pytest result.
7. Real runner result, or clear explanation if skipped due to missing input.
8. Output directory.
9. Manifest decision and key metrics.
10. Whether legacy `datefac/` was untouched.
11. Whether old `input/output/temp/data` and historical outputs were untouched.
12. Whether LLM/MinerU/OCR calls were zero.
13. `git status -sb`.
14. Recommended next step.

---

## 14. Next step after 348A

If 348A passes, the next likely step is:

```text
348A-QA Excel Intake Audit Result Review
```

or a small refinement task if the first pilot exposes schema/checker issues.
