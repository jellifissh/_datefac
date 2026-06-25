# 348N-R7X evidence provenance parsing: page_number population + agreement_status field

## Task Goal

Implement the first small evidence-strengthening slice recommended by R7W.

Task ID:

```text
348N-R7X evidence provenance parsing: page_number population + agreement_status field
```

This is an implementation + tests task.

Goal:

1. Parse page information from `explicit_evidence_ref` into a structured `page_number` field when the page reference is deterministic.
2. Add an auditable evidence agreement status field with conservative defaults.
3. Prevent unverified explicit/page provenance from being treated as fully strong evidence.
4. Keep readiness gates closed.

This task does not verify PDF text values yet.

This task does not promote rows to production readiness.

This task must not run workbook reruns, MinerU, OCR, LLM, or VLM.

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
docs/agent/348N_R7W_EVIDENCE_STRENGTHENING_DESIGN_WEAK_TO_STRONG_PATH.md
docs/agent/348N_R7V_CROSS_FAMILY_CLEAN_BOUNDARY_SUMMARY_AND_READINESS_REVIEW.md
docs/agent/348N_R7U_LINYANG_ANJING_WORKBOOK_FAMILY_REGRESSION_CHECK.md
docs/agent/348N_R7T_TAIHAO_STRICT_TABLE_SCAFFOLDING_CLEAN_BOUNDARY_PILOT_RERUN.md
```

Inspect current evidence/provenance implementation read-only before editing:

```text
datefac_agent/**/evidence*.py
datefac_agent/**/audit*.py
datefac_agent/**/models*.py
datefac_agent/**/review*.py
tests/agent/test_agent_excel_intake_audit_348a.py
```

Use existing names and style from the repository. Do not invent parallel structures if a suitable model/helper already exists.

---

## Current Design Constraints From R7W

R7W defined:

```text
Strong evidence must mean traceable and auditable, not merely plausible.
```

R7W also found that current `STRONG_EVIDENCE` can be reached too cheaply if explicit evidence text or page fields exist without verification.

R7X must therefore be conservative:

```text
parsed page_number + unverified agreement is better provenance, but not verified strong evidence.
```

Unless the repository already has a verified agreement mechanism, R7X should not create rows that claim verified strong evidence merely because a page number was parsed.

Separate these concepts clearly:

```text
evidence provenance present
evidence agreement verified
evidence strength
clean admission
readiness/export status
```

---

## Allowed Scope

Expected allowed implementation files include only the minimum required evidence/model files, likely one or more of:

```text
datefac_agent/audit/evidence_checker.py
datefac_agent/audit/audit_models.py
```

If the actual model/helper file names differ, use the existing repository layout and explain the exact files changed.

Allowed test scope:

```text
tests/agent/
```

Only modify tests directly related to R7X evidence provenance parsing and agreement status behavior.

Do not modify clean-boundary policy unless strictly necessary. R7X should not change the R7S strict-table scaffolding guard.

---

## Forbidden Actions

Do not modify:

```text
AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/codex_tasks/
input/
output/
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

Do not change output_schema_guardrails unless you stop first and explain why R7X cannot proceed without doing so.

Do not change readiness gates.

Do not claim:

```text
client_ready = true
production_ready = true
formal_client_export_allowed = true
```

Do not use broad Git staging or destructive cleanup commands.

---

## Implementation Requirements

### 1. Page reference parser

Implement a deterministic local parser for page references in `explicit_evidence_ref` or the current equivalent evidence text field.

It should parse common page references such as:

```text
第12页
12页
页码：12
page 12
Page 12
p.12
P12
pp. 12-13
第12-13页
```

Expected conservative behavior:

```text
If one deterministic page number is present, populate page_number with an int.
If a range is present and the current model supports only one page_number, use the first page as page_number and preserve the full raw locator string.
If the reference is unparseable, page_number remains None and the raw locator remains preserved.
If there is no explicit evidence ref, do not invent a page number.
```

Do not OCR the PDF.

Do not inspect PDF text.

Do not call LLM/VLM.

### 2. Evidence agreement status

Add a conservative evidence agreement status field using existing model style.

Preferred semantic values:

```text
MISSING       = no explicit evidence / no provenance anchor
UNVERIFIED    = provenance text/page exists but source-value agreement has not been checked
VERIFIED      = deterministic source-value agreement confirmed by a future checker
DISAGREED     = deterministic source-value disagreement found by a future checker
```

R7X should normally populate only:

```text
MISSING
UNVERIFIED
```

because R7X does not implement PDF value verification.

Do not set `VERIFIED` in this task unless a verified mechanism already exists and is proven by tests.

### 3. Evidence level semantics

Update or guard evidence classification so that unverified explicit/page provenance does not become verified strong evidence merely by existing.

Acceptable conservative result for R7X:

```text
explicit page parsed + agreement_status = UNVERIFIED -> evidence remains WEAK_EVIDENCE, unless existing verified agreement logic says otherwise
no page/no explicit ref but workbook lineage exists -> WEAK_EVIDENCE
missing lineage -> MISSING_EVIDENCE
```

If the project already has no distinct `STRONG_EVIDENCE_UNVERIFIED` enum, do not add one unless it is clearly the least invasive option. Prefer preserving existing public evidence levels and using `agreement_status` to prevent overclaiming.

### 4. Compatibility

The change must be backward-compatible with existing manifests and tests where possible.

Adding a default field is acceptable if existing serialization remains stable.

No old output artifact should need to be modified.

No output artifact should be committed.

---

## Test Requirements

Add compact tests covering:

1. `explicit_evidence_ref = 第12页` populates `page_number = 12` and `agreement_status = UNVERIFIED`.
2. `explicit_evidence_ref = page 12` or `p.12` populates `page_number = 12`.
3. A page range such as `第12-13页` or `pp. 12-13` populates first page `12` and preserves raw locator.
4. Unparseable explicit ref such as `附录A` preserves raw locator but does not populate `page_number`.
5. Missing explicit ref yields `agreement_status = MISSING` or the repository-equivalent default.
6. Parsed page with `UNVERIFIED` does not automatically claim verified strong evidence.
7. Existing workbook-row based weak evidence behavior still works.
8. R7S clean-boundary tests still pass.
9. MARKET_REFERENCE_ROW and qualitative_facts behavior remain unchanged through existing tests.

Prefer extending existing agent evidence/audit tests. If no specific evidence test file exists, add tests in the closest existing `tests/agent` file consistent with current project style.

---

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
python -m py_compile <modified implementation files>
pytest tests/agent -q
git status -sb
git diff --stat
git diff --name-only
git diff --check
```

If `pytest tests/agent -q` fails, report the full failure and whether it is caused by R7X.

Do not run full `pytest tests -q` unless you choose to confirm historical failures.

---

## Expected Output

Report:

1. Preflight result.
2. Files modified.
3. Page parser implementation summary.
4. Evidence agreement status implementation summary.
5. Evidence level behavior before/after.
6. Tests added or modified.
7. Validation outputs.
8. Whether any rows now falsely claim verified strong evidence.
9. Whether MARKET_REFERENCE_ROW policy changed.
10. Whether qualitative_facts admission changed.
11. Whether output/input/temp/data/legacy were modified.
12. Whether readiness gates remain closed.
13. Whether commit/push was performed.
14. Recommended next task.

Final summary must include:

```text
Data Result / 数据结果

Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
page_number_parsing_result（页码解析结果）=
agreement_status_result（一致性状态结果）=
strong_evidence_claim_result（强证据声明结果）=
readiness_gates（就绪门）=
recommended_next_task（推荐下一任务）=
```

---

## Commit / Push Rule

If and only if:

1. only allowed implementation/test files were modified,
2. validation commands were run and reported,
3. `git diff --name-only` contains only allowed implementation/test files,
4. `git diff --check` is clean,
5. no output/input/temp/data/legacy/config/docs files were modified,

then stage only the exact modified files with explicit `git add <path>` commands.

Do not use:

```text
git add .
git add -A
```

Suggested commit message:

```text
feat: add evidence provenance parsing
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
