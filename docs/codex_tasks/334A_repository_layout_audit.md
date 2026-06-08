# 334A Repository Layout Audit

## Goal
Audit the current repository layout and produce a safe migration plan for root-level Python files.

This task is audit-only. It must not move, rename, delete, or modify Python source files. It must not change production pipeline behavior, parser behavior, extraction behavior, delivery behavior, official assets, output artifacts, or protected dirty files.

## Current Context
- `333A` bilingual README and operator guides are complete and pushed.
- The repository root still contains multiple Python modules that may represent active core code, parser adapters, utilities, legacy modules, or historical entry points.
- The current task is to classify those files and prepare a migration plan without changing runtime behavior.

## Scope
- Create:
  - `docs/codex_tasks/334A_repository_layout_audit.md`
  - `docs/architecture/repository_layout_audit_334a.md`
  - `docs/architecture/root_python_migration_plan_334a.md`
  - `docs/architecture/repository_layout_audit_334a.json`
- Inspect:
  - root-level `*.py` files
  - `datefac/**/*.py`
  - `tools/**/*.py`
  - `tests/**/*.py`
  - `docs/**/*.md`
  - imports referencing root-level modules
  - runner scripts
  - current `README.md`
  - current `333A` docs

## Root-Level Python Files To Audit
Including but not limited to:
- `ai_summary_service.py`
- `artifact_names.py`
- `config_manager.py`
- `extractor_adapter.py`
- `extractor_quality.py`
- `factory_core.py`
- `financial_standardizer.py`
- `glued_table_splitter.py`
- `logger_utils.py`
- `pdfplumber_profile_extractor.py`
- `pdfplumber_table_extractor.py`
- `pdfplumber_table_postprocessor.py`
- `raw_table_exporter.py`

Also currently present:
- `run_state.py`
- `segment_validator.py`
- `table_block.py`
- `table_classifier.py`
- `table_cleaner.py`
- `table_segmenter.py`
- `vision_runtime.py`

## Required Classification
For every root-level Python file, classify it as one of:
1. `active_core_module`
2. `active_tool_or_runner_dependency`
3. `parser_or_extraction_module`
4. `standardization_or_mapping_module`
5. `utility_module`
6. `historical_legacy_module`
7. `safe_to_archive_candidate`
8. `unsafe_to_move_without_import_shim`

## Required Per-File Reporting
For every root-level Python file, report:
- current path
- likely purpose
- whether it is imported by other files
- files that import it
- whether tests or tools depend on it
- suggested target location
- migration risk: `low` / `medium` / `high`
- whether an import compatibility shim is needed
- recommended action

## Suggested Target Locations
- `datefac/extraction/`
- `datefac/parsers/`
- `datefac/standardization/`
- `datefac/utils/`
- `datefac/legacy/`
- `tools/`
- `keep_in_root`

## Validation Rules
- Do not modify any Python source file.
- Do not move files.
- Do not rename files.
- Do not delete files.
- Do not modify official assets.
- Do not modify output artifacts.
- Do not stage protected dirty files.
- Do not use `git add -A`.
- Do not use `git add .`.
- Use read-only inspection commands only.

## Protected Dirty Files
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Required Output Focus
The audit must answer:
- Which root modules are still active.
- Which ones are runtime-critical.
- Which ones are mostly tool-facing or test-facing.
- Which ones can move only behind import shims.
- Which ones are reasonable `334B` pilot migration targets.

## Expected Deliverables
- A human-readable architecture audit.
- A migration plan with phased scope.
- A machine-readable JSON summary.
- Final report including:
  - files created
  - number of root-level Python files audited
  - high-risk migration files
  - low-risk migration files
  - recommended `334B` migration scope
  - `git status -sb`
