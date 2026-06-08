# Repository Layout Audit 334A

## Scope And Boundaries
- Scope: audit the current repository layout with emphasis on root-level Python modules.
- Out of scope: moving, renaming, deleting, or editing Python source files.
- Explicitly not changed: production pipeline, parser chain, extraction chain, delivery chain, official assets, output artifacts, and protected dirty files.

## Inspection Method
- Read-only inventory from `git ls-files "*.py"`.
- Read-only import mapping from a generated summary derived from repository source scans.
- Spot checks of root-level modules, representative tests, current `README.md`, and `333A` documentation.
- No runtime behavior changes and no source relocation.

## Executive Summary
The repository currently has `20` root-level Python modules. Most are still active and several are on the legacy execution spine centered on [`factory_core.py`](/D:/_datefac/factory_core.py). The root is therefore not just historical clutter; it still contains active parser, extraction, standardization, and utility dependencies consumed by tools, tests, and trust-side runners.

The main architectural issue is not file count by itself. The issue is that root-level modules are coupled through absolute root imports, with `factory_core.py` acting as a high-fan-out legacy hub. Because of that, a safe migration cannot begin with direct moves. It must begin with a shim-first strategy and a narrow pilot scope on low-fan-out modules.

## Repository-Level Findings
- `factory_core.py` is the highest-coupling root entry point and directly imports many other root modules.
- Parser and extraction helpers such as `pdfplumber_table_extractor.py`, `pdfplumber_profile_extractor.py`, `extractor_adapter.py`, `table_block.py`, and `table_segmenter.py` remain active.
- `financial_standardizer.py` is heavily reused by tooling and tests, so it is not a legacy orphan.
- Several smaller modules are active but have narrower fan-out and are better 334B migration candidates.
- No root-level Python file is currently a zero-risk direct move candidate without some compatibility handling.

## Classification Summary

| File | Classification | Suggested Target | Risk | Shim Needed | Recommended Action |
|---|---|---|---|---|---|
| `ai_summary_service.py` | `unsafe_to_move_without_import_shim` | `datefac/legacy/` | medium | yes | keep in root for now; only archive behind shim after `factory_core` decoupling |
| `artifact_names.py` | `utility_module` | `datefac/utils/` | low | yes | good early shim-first pilot candidate |
| `config_manager.py` | `active_tool_or_runner_dependency` | `datefac/utils/` | high | yes | postpone until tool import path migration plan is ready |
| `extractor_adapter.py` | `parser_or_extraction_module` | `datefac/extraction/` | high | yes | postpone; active in trust runners and extraction tools |
| `extractor_quality.py` | `utility_module` | `datefac/extraction/` | medium | yes | possible second-wave migration after `table_block` path is stabilized |
| `factory_core.py` | `active_core_module` | `keep_in_root` | high | no | keep in root during 334B; treat as blocker to larger moves |
| `financial_standardizer.py` | `standardization_or_mapping_module` | `datefac/standardization/` | high | yes | postpone; migrate only with test-backed shim plan |
| `glued_table_splitter.py` | `parser_or_extraction_module` | `datefac/extraction/` | medium | yes | defer until standardizer and extractor paths are stabilized |
| `logger_utils.py` | `utility_module` | `datefac/utils/` | low | yes | good early shim-first pilot candidate |
| `pdfplumber_profile_extractor.py` | `parser_or_extraction_module` | `datefac/parsers/` | high | yes | postpone; tool-facing parser dependency |
| `pdfplumber_table_extractor.py` | `parser_or_extraction_module` | `datefac/parsers/` | high | yes | postpone; shared by parser modules and tests |
| `pdfplumber_table_postprocessor.py` | `parser_or_extraction_module` | `datefac/extraction/` | high | yes | postpone; coupled to parser test coverage and `factory_core` |
| `raw_table_exporter.py` | `parser_or_extraction_module` | `datefac/extraction/` | medium | yes | possible later migration after `artifact_names` and `table_block` |
| `run_state.py` | `utility_module` | `datefac/utils/` | low | yes | good early shim-first pilot candidate |
| `segment_validator.py` | `parser_or_extraction_module` | `datefac/extraction/` | medium | yes | later pilot candidate after root import policy is defined |
| `table_block.py` | `unsafe_to_move_without_import_shim` | `datefac/extraction/` | high | yes | postpone; shared data model across many tools |
| `table_classifier.py` | `parser_or_extraction_module` | `datefac/extraction/` | high | yes | postpone; runtime and tests depend on current import path |
| `table_cleaner.py` | `parser_or_extraction_module` | `datefac/extraction/` | high | yes | postpone; runtime and tests depend on current import path |
| `table_segmenter.py` | `parser_or_extraction_module` | `datefac/extraction/` | high | yes | postpone; protected by explicit repo guidance |
| `vision_runtime.py` | `active_tool_or_runner_dependency` | `datefac/utils/` | high | yes | postpone; tied to environment and dependency-prewarm tooling |

## Detailed Per-File Audit

### `ai_summary_service.py`
- Current path: `D:\_datefac\ai_summary_service.py`
- Likely purpose: AI-assisted JSON summary generation helper used by legacy orchestration.
- Imported by other files: yes
- Importers: `factory_core.py`
- Tool or test dependency: no direct tool/test references found
- Suggested target location: `datefac/legacy/`
- Migration risk: medium
- Import compatibility shim needed: yes
- Recommended action: treat as legacy but do not move before `factory_core.py` is decoupled

### `artifact_names.py`
- Current path: `D:\_datefac\artifact_names.py`
- Likely purpose: constant definitions for output asset names
- Imported by other files: yes
- Importers: `factory_core.py`, `raw_table_exporter.py`
- Tool or test dependency: no direct tool/test references found
- Suggested target location: `datefac/utils/`
- Migration risk: low
- Import compatibility shim needed: yes
- Recommended action: first-wave shim-first migration candidate

### `config_manager.py`
- Current path: `D:\_datefac\config_manager.py`
- Likely purpose: config loading and deep-merge support for runtime tools
- Imported by other files: yes
- Importers: `factory_core.py`, `tools/check_vision_dependencies.py`, `tools/extract_stage5b_pdf_raw_tables.py`, `tools/prewarm_marker_models.py`, `tools/probe_extractors.py`, `tools/rebuild_stage5k_full_sandbox_02_05_from_pdf.py`, `tools/run_eval1_10pdf_sandbox_extraction_evaluation.py`, `tools/run_eval1b_profile_selection_fix_regression.py`, `tools/run_stage7d_sandbox_pipeline.py`
- Tool or test dependency: strong tool dependency, no direct test dependency found
- Suggested target location: `datefac/utils/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone until tool import migration is explicitly scripted and validated

### `extractor_adapter.py`
- Current path: `D:\_datefac\extractor_adapter.py`
- Likely purpose: adapter layer that normalizes extractor outputs into common table-block structures
- Imported by other files: yes
- Importers: `datefac/trust/full_unfamiliar_export_benchmark_330h.py`, `datefac/trust/unfamiliar_candidate_export_smoke_330f4.py`, `factory_core.py`, `tools/extract_stage5b_pdf_raw_tables.py`, `tools/probe_extractors.py`, `tools/rebuild_stage5k_full_sandbox_02_05_from_pdf.py`, `tools/run_eval1_10pdf_sandbox_extraction_evaluation.py`, `tools/run_eval1b_profile_selection_fix_regression.py`, `tools/run_stage7d_sandbox_pipeline.py`
- Tool or test dependency: strong tool dependency and trust-runner dependency
- Suggested target location: `datefac/extraction/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: defer to a later parser/extraction migration phase

### `extractor_quality.py`
- Current path: `D:\_datefac\extractor_quality.py`
- Likely purpose: scoring helper for table-block quality and keyword/year density
- Imported by other files: yes
- Importers: `pdfplumber_profile_extractor.py`, `raw_table_exporter.py`, `tools/probe_extractors.py`, `tools/probe_glued_table_split.py`, `tools/probe_pdfplumber_profiles.py`
- Tool or test dependency: tool dependency present, no direct tests
- Suggested target location: `datefac/extraction/`
- Migration risk: medium
- Import compatibility shim needed: yes
- Recommended action: consider after `table_block.py` and parser helper paths are stabilized

### `factory_core.py`
- Current path: `D:\_datefac\factory_core.py`
- Likely purpose: legacy orchestration hub and high-fan-out runtime core
- Imported by other files: no direct importers found, but it imports many root modules
- Importers: none found
- Tool or test dependency: implicit runtime dependency via legacy orchestration
- Suggested target location: `keep_in_root`
- Migration risk: high
- Import compatibility shim needed: no for 334A recommendation, because the file should stay put in 334B
- Recommended action: keep in root and treat as the main decoupling blocker

### `financial_standardizer.py`
- Current path: `D:\_datefac\financial_standardizer.py`
- Likely purpose: financial metric normalization and standardization logic
- Imported by other files: yes
- Importers: `factory_core.py`, `glued_table_splitter.py`, `tests/test_financial_standardizer.py`, and multiple standardization/reporting tools
- Tool or test dependency: very strong on both tools and tests
- Suggested target location: `datefac/standardization/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone until a dedicated standardization package move is planned with regression coverage

### `glued_table_splitter.py`
- Current path: `D:\_datefac\glued_table_splitter.py`
- Likely purpose: split heuristics for glued multi-table captures
- Imported by other files: yes
- Importers: `factory_core.py`
- Tool or test dependency: no direct tool/test import found, but functionally coupled to extractor stack
- Suggested target location: `datefac/extraction/`
- Migration risk: medium
- Import compatibility shim needed: yes
- Recommended action: later extraction migration candidate, not first-wave

### `logger_utils.py`
- Current path: `D:\_datefac\logger_utils.py`
- Likely purpose: central logging setup helper
- Imported by other files: yes
- Importers: `factory_core.py`
- Tool or test dependency: no direct tool/test references found
- Suggested target location: `datefac/utils/`
- Migration risk: low
- Import compatibility shim needed: yes
- Recommended action: first-wave shim-first migration candidate

### `pdfplumber_profile_extractor.py`
- Current path: `D:\_datefac\pdfplumber_profile_extractor.py`
- Likely purpose: profile-driven PDFPlumber extraction orchestration
- Imported by other files: yes
- Importers: `factory_core.py`, `tools/extract_stage5b_pdf_raw_tables.py`, `tools/rebuild_stage5k_full_sandbox_02_05_from_pdf.py`, `tools/run_eval1_10pdf_sandbox_extraction_evaluation.py`, `tools/run_eval1b_profile_selection_fix_regression.py`, `tools/run_stage7d_sandbox_pipeline.py`
- Tool or test dependency: strong tool dependency
- Suggested target location: `datefac/parsers/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone; migrate only with parser import shims

### `pdfplumber_table_extractor.py`
- Current path: `D:\_datefac\pdfplumber_table_extractor.py`
- Likely purpose: low-level PDFPlumber table extraction and block-to-DataFrame conversion
- Imported by other files: yes
- Importers: `extractor_adapter.py`, `factory_core.py`, `pdfplumber_profile_extractor.py`, `tests/test_pdfplumber_table_extractor.py`, `tests/test_pdfplumber_table_postprocessor.py`
- Tool or test dependency: direct test dependency and parser-stack dependency
- Suggested target location: `datefac/parsers/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone; direct move would break both runtime imports and tests

### `pdfplumber_table_postprocessor.py`
- Current path: `D:\_datefac\pdfplumber_table_postprocessor.py`
- Likely purpose: post-processing and merge heuristics for extracted PDFPlumber blocks
- Imported by other files: yes
- Importers: `factory_core.py`, `tests/test_pdfplumber_table_postprocessor.py`
- Tool or test dependency: direct test dependency
- Suggested target location: `datefac/extraction/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone; treat as a test-backed migration item

### `raw_table_exporter.py`
- Current path: `D:\_datefac\raw_table_exporter.py`
- Likely purpose: export extracted table blocks into reviewable raw assets
- Imported by other files: yes
- Importers: `factory_core.py`
- Tool or test dependency: no direct tool/test import found
- Suggested target location: `datefac/extraction/`
- Migration risk: medium
- Import compatibility shim needed: yes
- Recommended action: consider after `artifact_names.py` and `table_block.py` path policy is set

### `run_state.py`
- Current path: `D:\_datefac\run_state.py`
- Likely purpose: document-level run state dataclass
- Imported by other files: yes
- Importers: `factory_core.py`
- Tool or test dependency: no direct tool/test references found
- Suggested target location: `datefac/utils/`
- Migration risk: low
- Import compatibility shim needed: yes
- Recommended action: first-wave shim-first migration candidate

### `segment_validator.py`
- Current path: `D:\_datefac\segment_validator.py`
- Likely purpose: segment validation helper for classification/type consistency checks
- Imported by other files: yes
- Importers: `factory_core.py`
- Tool or test dependency: no direct tool/test references found
- Suggested target location: `datefac/extraction/`
- Migration risk: medium
- Import compatibility shim needed: yes
- Recommended action: later-wave candidate after utility pilot succeeds

### `table_block.py`
- Current path: `D:\_datefac\table_block.py`
- Likely purpose: shared table-block datamodel plus feature helpers
- Imported by other files: yes
- Importers: `extractor_adapter.py`, `extractor_quality.py`, `pdfplumber_profile_extractor.py`, `raw_table_exporter.py`, and multiple tools
- Tool or test dependency: strong tool dependency
- Suggested target location: `datefac/extraction/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone; this is a shared model dependency and a path-change multiplier

### `table_classifier.py`
- Current path: `D:\_datefac\table_classifier.py`
- Likely purpose: classify tables by statement/type using keyword heuristics
- Imported by other files: yes
- Importers: `factory_core.py`, `tests/test_table_classifier.py`
- Tool or test dependency: direct test dependency
- Suggested target location: `datefac/extraction/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone; migrate only with retained backward import path

### `table_cleaner.py`
- Current path: `D:\_datefac\table_cleaner.py`
- Likely purpose: table cleanup, row filtering, and deduplication
- Imported by other files: yes
- Importers: `factory_core.py`, `tests/test_table_cleaner.py`
- Tool or test dependency: direct test dependency
- Suggested target location: `datefac/extraction/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone; runtime-sensitive and test-sensitive

### `table_segmenter.py`
- Current path: `D:\_datefac\table_segmenter.py`
- Likely purpose: row-segmentation and merge logic for complex tables
- Imported by other files: yes
- Importers: `factory_core.py`, `tests/test_table_segmenter.py`
- Tool or test dependency: direct test dependency
- Suggested target location: `datefac/extraction/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: do not include in 334B pilot; explicit repo guidance already says not to modify it casually

### `vision_runtime.py`
- Current path: `D:\_datefac\vision_runtime.py`
- Likely purpose: vision environment construction and diagnostics for model-backed extraction tooling
- Imported by other files: yes
- Importers: `factory_core.py`, `tools/check_vision_dependencies.py`, `tools/prewarm_marker_models.py`
- Tool or test dependency: direct tool dependency
- Suggested target location: `datefac/utils/`
- Migration risk: high
- Import compatibility shim needed: yes
- Recommended action: postpone; environment tooling makes this sensitive

## Risk Buckets

### High-Risk Migration Files
- `config_manager.py`
- `extractor_adapter.py`
- `factory_core.py`
- `financial_standardizer.py`
- `pdfplumber_profile_extractor.py`
- `pdfplumber_table_extractor.py`
- `pdfplumber_table_postprocessor.py`
- `table_block.py`
- `table_classifier.py`
- `table_cleaner.py`
- `table_segmenter.py`
- `vision_runtime.py`

### Medium-Risk Migration Files
- `ai_summary_service.py`
- `extractor_quality.py`
- `glued_table_splitter.py`
- `raw_table_exporter.py`
- `segment_validator.py`

### Low-Risk Migration Files
- `artifact_names.py`
- `logger_utils.py`
- `run_state.py`

## Recommended 334B Migration Scope
`334B` should be a shim-first migration pilot limited to low-fan-out utility modules:
- `artifact_names.py`
- `logger_utils.py`
- `run_state.py`

Optional second-wave candidates if the pilot is clean:
- `segment_validator.py`
- `extractor_quality.py`
- `raw_table_exporter.py`

Explicitly out of 334B scope:
- `factory_core.py`
- `table_segmenter.py`
- parser-facing `pdfplumber_*` modules
- `financial_standardizer.py`
- `config_manager.py`
- `vision_runtime.py`
- `table_block.py`

## Layered Diagnosis
- Extraction layer: root still contains active parser and extraction modules, so repository flattening is not cosmetic; it affects runtime coupling.
- Post-processing layer: block models, cleaners, classifiers, and post-processors are tightly referenced and should not move without shims.
- Standardization layer: `financial_standardizer.py` is heavily reused by tools and tests and should be migrated only as a dedicated package move.

## Residual Risk
This audit is based on repository import references and spot inspection, not on a behavioral migration rehearsal. Dynamic imports, CLI-only invocation paths, or undocumented local scripts could add hidden coupling. That is exactly why the recommended next step is a narrow shim-first pilot rather than a broad relocation.
