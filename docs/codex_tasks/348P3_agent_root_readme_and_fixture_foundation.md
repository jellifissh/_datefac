# 348P3 Agent Root README and Fixture Foundation

## 1. Goal

Implement the second foundation cleanup step for the DateFac Agent pivot.

This task should improve the project-level entry point and prepare the future fixture/test strategy for 348A.

The goal is:

```text
Make the repository explain the Agent pivot clearly and prepare test-fixture foundations.
```

The goal is not:

```text
Implement 348A, parse Excel, call LLMs, run MinerU, or migrate legacy runners.
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
docs/agent/348A_EXCEL_INTAKE_AUDIT_PLAN.md
docs/legacy/LEGACY_ASSET_MAP.md
docs/project_strategy/348_agent_pivot_brief.md
```

They define the new Agent direction, the legacy asset boundary, and the migration rules.

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
git status -sb
git branch --show-current
```

The worktree must be clean before starting. If there are uncommitted changes, stop and report.

---

## 4. Non-negotiable safety rules

Do not delete legacy source code.

Do not move the old `datefac/` package.

Do not rewrite old runners under `tools/`.

Do not touch `input/`, `output/`, `temp/`, or `data/`.

Do not modify old 345D / 346B / 346B4 / 346B5 / 346B5Q outputs.

Do not implement Excel intake logic yet.

Do not call LLM APIs.

Do not run MinerU.

Do not continue 346B6.

Do not use:

```text
git add .
git add -A
git reset --hard
git checkout --
```

Only add explicitly named files.

---

## 5. What to do in this task

### 5.1 Add a root README pivot notice

Modify the root `README.md` lightly.

At the top, add a short notice explaining that the current mainline is pivoting toward DateFac Agent.

The notice should point to:

```text
datefac_agent/README.md
docs/agent/AGENT_ARCHITECTURE.md
docs/legacy/LEGACY_ASSET_MAP.md
```

Keep the old README content below the notice unless there is a clear reason to remove it.

Do not rewrite the whole README during this task.

### 5.2 Add fixture directory documentation

Create:

```text
tests/agent/fixtures/README.md
```

Explain that future fixtures should preserve known bad cases from legacy 346B and related audits.

Mention fixture categories:

```text
unit_mismatch
period_shift
valuation_metric_confusion
per_share_vs_total_amount
weak_evidence
false_positive_recovery
semantic_class_unknown
```

Do not copy large real outputs into fixtures during this task.

### 5.3 Add fixture strategy document

Create:

```text
docs/agent/FIXTURE_STRATEGY.md
```

It should explain:

- why fixtures matter after the Agent pivot;
- how 346B/346B2/346B3/346B4/346B5/346B5Q become test material;
- naming conventions;
- privacy/safety boundaries;
- what not to put into fixtures;
- how future tests should use them.

### 5.4 Add 348A input/output contract draft

Create:

```text
docs/agent/348A_INPUT_OUTPUT_CONTRACT.md
```

This should be a draft contract for the next milestone only.

It should define:

- expected inputs;
- expected outputs;
- non-goals;
- audit categories;
- review queue expectations;
- evidence index expectations;
- no-production/no-client gate status.

Do not implement code.

---

## 6. Expected changed files

Expected new or modified files:

```text
README.md
tests/agent/fixtures/README.md
docs/agent/FIXTURE_STRATEGY.md
docs/agent/348A_INPUT_OUTPUT_CONTRACT.md
```

Do not modify other files unless absolutely necessary. If extra files are touched, explain why.

---

## 7. Validation

Run the existing foundation smoke test:

```powershell
cd D:\_datefac_agent
python -m pytest tests\agent\test_agent_foundation_imports.py -q
```

No MinerU, LLM, OCR, Excel parsing, or legacy pipeline should be run in this task.

---

## 8. Completion report

After finishing, report:

1. Files created or modified.
2. Whether branch is `pivot/348-agent-foundation`.
3. Whether the worktree was clean before editing.
4. Whether root `README.md` was modified and how.
5. Whether legacy `datefac/` was untouched.
6. Whether `input/`, `output/`, `temp/`, and `data/` were untouched.
7. Whether any old runner was touched.
8. Pytest result.
9. `git status -sb`.
10. Recommended next step.

---

## 9. Next step after this task

If 348P3 passes, the next candidate is:

```text
348A AI-Extracted Excel Intake Audit Pilot
```

348A should begin implementation of the first audit-first workflow over an already extracted Excel file and its corresponding PDF evidence.
