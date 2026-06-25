# 348N-R7W evidence strengthening design: WEAK_EVIDENCE -> STRONG_EVIDENCE path

## Task Goal

Design the next evidence-strengthening step after R7V.

Task ID:

```text
348N-R7W evidence strengthening design: WEAK_EVIDENCE -> STRONG_EVIDENCE path
```

This is a documentation-only design task.

Do not modify code.

Do not modify tests.

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not create or modify output artifacts.

The goal is to design how the DateFac Agent Excel intake/audit pipeline can promote selected rows from `WEAK_EVIDENCE` to stronger evidence status using deterministic, auditable provenance signals.

The design must explain what evidence is required before any future task can claim better readiness.

Do not claim production readiness.

Do not claim formal client export is allowed.

---

## Background

R7P-R7V validated the clean-boundary policy across Taihao, Linyang, and Anjing.

R7V confirmed:

```text
Taihao: clean_data 92 -> 72; review_queue 66 -> 86; 20 scaffolding rows moved to review
Linyang: clean_data 0; review_queue 489; no R7S regression
Anjing: clean_data 65; review_queue 17; R7S removed 0 normal fact rows
MARKET_REFERENCE_ROW boundary remains stable
normal numeric financial facts preserved
readiness gates remain closed
```

However, R7V also confirmed remaining risks:

```text
Taihao rows remain WEAK_EVIDENCE
No evidence/page-number strengthening has been done
The project is still demo-only
client_ready = false
production_ready = false
formal_client_export_allowed = false
```

Therefore the next valuable step is to design a deterministic evidence-strengthening path, not to declare readiness.

---

## Required Preflight

Run and report:

```text
git status -sb
git pull origin pivot/348-agent-foundation
git status -sb
git log --oneline -12
```

If the worktree is not clean after pull, stop and report.

---

## Required Read Order

Read these files:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/agent/348N_R7V_CROSS_FAMILY_CLEAN_BOUNDARY_SUMMARY_AND_READINESS_REVIEW.md
docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md
docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md
docs/agent/348N_R7S_QA_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_REVIEW.md
docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
```

Review implementation and model definitions read-only as needed:

```text
datefac_agent/review/clean_candidate_policy.py
datefac_agent/**/audit*.py
datefac_agent/**/evidence*.py
datefac_agent/**/review*.py
datefac_agent/**/models*.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Use search/read-only inspection to identify current evidence fields, provenance fields, page/cell references, manifest fields, and review/export readiness checks.

No output directory needs to be modified.

---

## Design Questions

Answer all of these in the report:

1. What does `WEAK_EVIDENCE` currently mean in the pipeline?
2. What does `STRONG_EVIDENCE` currently mean, if it already exists?
3. Which fields currently carry evidence/provenance information?
4. What information is missing before rows can be promoted safely?
5. Should evidence strengthening be row-level, cell-level, metric-level, sheet-level, or artifact-level?
6. What deterministic criteria should be required before a row can be promoted from `WEAK_EVIDENCE`?
7. Should page number, PDF source span, Excel cell address, sheet name, row index, metric name, period, unit, and value all be required?
8. How should numeric value agreement be checked between source evidence and structured row?
9. How should confidence be represented separately from clean-admission status?
10. How should evidence strengthening interact with `clean_data`, `review_queue`, and readiness gates?
11. Should `STRONG_EVIDENCE` automatically imply clean admission? If not, explain why.
12. How should the system avoid LLM/VLM-dependent evidence promotion?
13. What tests are needed for the next implementation task?
14. What small implementation slice should R7X do first?

---

## Required Design Constraints

The design must be conservative:

```text
Strong evidence must mean traceable and auditable, not merely plausible.
```

Do not propose using LLM confidence alone as strong evidence.

Do not propose broadening qualitative_facts clean admission.

Do not propose weakening MARKET_REFERENCE_ROW boundaries.

Do not propose making `client_ready`, `production_ready`, or `formal_client_export_allowed` true.

Do not treat `STRONG_EVIDENCE` as automatically production-ready.

Separate these concepts clearly:

```text
evidence_strength
clean_admission
review_required
export_readiness
production_readiness
```

---

## Expected Design Topics

Cover at least these topics:

```text
Current evidence model
Current provenance fields
Gap analysis
Proposed evidence schema additions or reuse
Promotion criteria from WEAK_EVIDENCE to STRONG_EVIDENCE
Negative criteria that must keep rows weak/review-only
Interaction with strict-table scaffolding guard
Interaction with MARKET_REFERENCE_ROW
Interaction with normal numeric financial facts
Test plan
Migration/compatibility plan
Recommended R7X implementation slice
Readiness gates
```

---

## Allowed Scope

Allowed to create exactly one result report:

```text
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
```

No other file may be created or modified.

---

## Forbidden Actions

Do not modify code.

Do not modify tests.

Do not modify output.

Do not modify input.

Do not modify previous reports.

Do not modify:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/
temp/
data/
legacy datefac/
dependencies
config files
```

Do not run workbook reruns.

Do not run MinerU, OCR, LLM, or VLM.

Do not change MARKET_REFERENCE_ROW policy.

Do not broaden qualitative_facts admission.

Do not change output_schema_guardrails.

Do not change readiness gates.

Do not stage or commit output files.

Do not use broad Git staging or destructive cleanup commands.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

Do not run full `pytest tests -q` unless you choose to confirm historical failures. `pytest tests/agent -q` is sufficient for this docs-only evidence-design review.

---

## Expected Report Content

The report must include:

```text
Task ID
Preflight
Files reviewed
Current evidence model
Current provenance model
Gap analysis
WEAK_EVIDENCE meaning
STRONG_EVIDENCE requirements
Promotion criteria
Negative criteria
Interaction with clean-boundary policy
Interaction with market-reference policy
Interaction with readiness gates
Test plan
Recommended R7X implementation slice
Remaining risks
Decision
Data Result / 数据结果
```

Data Result must include:

```text
Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
design_result（设计结果）=
strong_evidence_definition（强证据定义）=
promotion_required_fields（提升所需字段）=
readiness_gates（就绪门）=
production_ready（是否生产就绪）=
formal_client_export_allowed（是否允许正式客户导出）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. exactly one report was created under `docs/agent/`,
2. no code/tests/output/input/previous docs other than the allowed report were modified,
3. validation commands were run and reported,
4. `git diff --name-only` contains only the allowed report,
5. `git diff --check` is clean,

then stage exactly the report file:

```text
git add docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
```

Do not use `git add .`.

Do not use `git add -A`.

Commit:

```text
git commit -m "docs: add R7W evidence strengthening design"
```

Push:

```text
git push origin pivot/348-agent-foundation
```

Post-push validation:

```text
git status -sb
git log --oneline -10
```

Stop after push. Do not start the next task.
