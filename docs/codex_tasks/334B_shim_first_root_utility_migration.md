# 334B Shim-First Root Utility Migration

## Goal
Perform a small, safe, shim-first migration for only the low-risk root utility modules identified by `334A`:
- `artifact_names.py`
- `logger_utils.py`
- `run_state.py`

This task should reduce root clutter while preserving backward compatibility. It must not change business behavior.

## Read First
- `docs/architecture/repository_layout_audit_334a.md`
- `docs/architecture/root_python_migration_plan_334a.md`
- `docs/architecture/repository_layout_audit_334a.json`
- `artifact_names.py`
- `logger_utils.py`
- `run_state.py`
- `factory_core.py`
- `raw_table_exporter.py`
- relevant tests and tools that import these modules

## Scope
Only migrate these three root modules:
1. `artifact_names.py`
2. `logger_utils.py`
3. `run_state.py`

## Target Package Paths
- `datefac/utils/artifact_names.py`
- `datefac/utils/logger_utils.py`
- `datefac/utils/run_state.py`

Also ensure:
- `datefac/utils/__init__.py` exists

## Shim Strategy
- Keep root-level files in place as compatibility shims.
- Each root shim re-exports from the new package location.
- Preserve compatibility for:
  - `import artifact_names`
  - `from artifact_names import ...`
  - `import logger_utils`
  - `from logger_utils import ...`
  - `import run_state`
  - `from run_state import ...`

Example style:
```python
from datefac.utils.artifact_names import *
```

## Boundaries
- Do not delete the root files.
- Do not mass-rewrite imports across the repository.
- Do not touch `factory_core.py` unless absolutely necessary.
- Do not touch parser/extraction/delivery production behavior.
- Do not migrate:
  - `config_manager.py`
  - `extractor_adapter.py`
  - `factory_core.py`
  - `financial_standardizer.py`
  - `pdfplumber_*`
  - `table_*`
  - `vision_runtime.py`
- Do not modify official assets.
- Do not modify output artifacts.
- Do not use `git add -A`.
- Do not use `git add .`
- Do not commit unless explicitly asked.

## Expected Files
- `docs/codex_tasks/334B_shim_first_root_utility_migration.md`
- `datefac/utils/__init__.py`
- `datefac/utils/artifact_names.py`
- `datefac/utils/logger_utils.py`
- `datefac/utils/run_state.py`
- `artifact_names.py` as shim
- `logger_utils.py` as shim
- `run_state.py` as shim
- `tests/trust/test_root_utility_shims_334b.py`

## Validation Requirements
- Root imports still work.
- Package imports work.
- Public symbols are preserved.
- Existing direct import compatibility is preserved.
- No production pipeline behavior changes.
- No parser/extraction/delivery logic changes.
- No official assets changed.
- Protected dirty files remain unstaged.
- Output artifacts are not staged.

## Suggested Tests
Create a lightweight test that verifies:
- `import artifact_names` works
- `import logger_utils` works
- `import run_state` works
- `import datefac.utils.artifact_names` works
- `import datefac.utils.logger_utils` works
- `import datefac.utils.run_state` works
- selected known symbols/classes/functions from each old module are available from both old and new import paths
- old and new imports point to equivalent objects where practical

## Commands
```powershell
python -m py_compile artifact_names.py logger_utils.py run_state.py datefac\utils\artifact_names.py datefac\utils\logger_utils.py datefac\utils\run_state.py
python -m pytest tests\trust\test_root_utility_shims_334b.py -q
python -c "import artifact_names, logger_utils, run_state; import datefac.utils.artifact_names, datefac.utils.logger_utils, datefac.utils.run_state; print('334B import smoke ok')"
```

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Reporting Requirements
After completion, report:
- files changed
- migration summary
- tests run
- py_compile result
- import smoke result
- `git status -sb`
- confirm protected dirty files remain unstaged
