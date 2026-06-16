# 348P2 Agent Foundation Cleanup

## 1. Goal

Implement the first safe cleanup step for the DateFac Agent pivot.

This task must create a clean agent-oriented foundation without deleting, rewriting, or relocating the legacy DateFac project.

The goal is:

```text
Build a clean new DateFac Agent foundation beside the legacy codebase.
```

The goal is not:

```text
Delete old code or migrate the whole legacy project.
```

---

## 2. Required context

Read these files first:

```text
datefac_agent/README.md
datefac_agent/PROJECT_BACKGROUND.md
datefac_agent/CODE_MIGRATION_PLAN.md
datefac_agent/FOUNDATION_TASK.md
docs/project_strategy/348_agent_pivot_brief.md
```

They define the pivot, the migration rules, and the safety boundary.

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

Do not work from the dirty legacy workspace:

```text
D:\_datefac
```

---

## 4. Non-negotiable safety rules

Do not delete or rewrite legacy source code.

Do not move the old `datefac/` package.

Do not remove old scripts under `tools/`.

Do not delete `input/`, `output/`, `temp/`, `data/`, or old benchmark folders.

Do not modify 345D / 346B / 346B4 / 346B5 / 346B5Q outputs.

Do not modify protected dirty files from the old main workspace.

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

This is a foundation cleanup task. It should create clear structure and documents, plus a minimal importable package skeleton.

### 5.1 Create package skeleton

Create the following files:

```text
datefac_agent/__init__.py

datefac_agent/intake/__init__.py
datefac_agent/audit/__init__.py
datefac_agent/review/__init__.py
datefac_agent/delivery/__init__.py
datefac_agent/orchestrator/__init__.py
datefac_agent/schemas/__init__.py
datefac_agent/llm/__init__.py
```

Do not implement heavy logic yet.

Each `__init__.py` can contain only a short docstring.

### 5.2 Create basic schema placeholder

Create:

```text
datefac_agent/schemas/audit_models.py
```

It should define minimal dataclass or Pydantic-compatible models, but keep them simple.

Minimum models:

```text
EvidenceRef
ExtractedMetric
AuditIssue
AuditResult
ReviewDecision
```

If Pydantic is already available in the project dependencies, use Pydantic. If not, use standard `dataclasses` to avoid adding dependencies during this task.

### 5.3 Create minimal smoke test

Create:

```text
tests/agent/test_agent_foundation_imports.py
```

The test should verify that the new package and schema module can be imported.

Example expectations:

```text
import datefac_agent
from datefac_agent.schemas.audit_models import AuditResult
```

No external files should be required.

### 5.4 Create agent docs index

Create:

```text
docs/agent/AGENT_ARCHITECTURE.md
docs/agent/348A_EXCEL_INTAKE_AUDIT_PLAN.md
```

These docs should stay high level.

Do not promise advanced future actions such as automatic trading, market monitoring, or external automation yet.

Focus only on:

```text
intake -> audit -> review -> delivery
```

### 5.5 Create legacy asset map

Create:

```text
docs/legacy/LEGACY_ASSET_MAP.md
```

It should classify old assets into:

```text
KEEP_AS_LEGACY_REFERENCE
MIGRATE_CAPABILITY_LATER
FREEZE_AS_HISTORICAL_EXPERIMENT
DO_NOT_TOUCH
```

Mention that 346B series is valuable as audit-rule and test-fixture material, but should not be continued as the immediate mainline.

### 5.6 Optional README touch

Do not rewrite the root `README.md` in this task unless it is clearly safe.

If editing root `README.md`, only add a short top-level notice pointing to:

```text
datefac_agent/README.md
```

Prefer not to edit root README in this first cleanup if it risks conflicts.

---

## 6. What not to do

Do not implement 348A yet.

Do not parse Excel yet.

Do not call LLM APIs.

Do not run MinerU.

Do not build a generic chatbot agent.

Do not wire old DateFac pipelines into the new package.

Do not move old benchmark scripts.

Do not perform output cleanup.

Do not delete files.

---

## 7. Validation commands

Run:

```powershell
cd D:\_datefac_agent

python -m py_compile datefac_agent\__init__.py datefac_agent\schemas\audit_models.py tests\agent\test_agent_foundation_imports.py

python -m pytest tests\agent\test_agent_foundation_imports.py -q
```

If pytest is not available, report that clearly and still run py_compile.

---

## 8. Expected changed files

Expected new files:

```text
datefac_agent/__init__.py

datefac_agent/intake/__init__.py
datefac_agent/audit/__init__.py
datefac_agent/review/__init__.py
datefac_agent/delivery/__init__.py
datefac_agent/orchestrator/__init__.py
datefac_agent/schemas/__init__.py
datefac_agent/llm/__init__.py

datefac_agent/schemas/audit_models.py

tests/agent/test_agent_foundation_imports.py

docs/agent/AGENT_ARCHITECTURE.md
docs/agent/348A_EXCEL_INTAKE_AUDIT_PLAN.md

docs/legacy/LEGACY_ASSET_MAP.md
```

No old code should be deleted.

---

## 9. Completion report

After finishing, report:

1. Files created or modified.
2. Whether branch is `pivot/348-agent-foundation`.
3. Whether legacy `datefac/` was untouched.
4. Whether `input/`, `output/`, `temp/`, `data/` were untouched.
5. Whether root README was modified.
6. `py_compile` result.
7. `pytest` result.
8. `git status -sb`.
9. Recommended next step.

---

## 10. Next step after this task

If this foundation cleanup passes, the next task should be:

```text
348A AI-Extracted Excel Intake Audit Pilot
```

348A should audit an already extracted Excel file against a PDF. It should not re-extract the PDF from scratch.
