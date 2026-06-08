# Root Python Migration Plan 334A

## Objective
Provide a safe migration plan for root-level Python modules without changing runtime behavior during the planning stage.

## Constraints
- No source moves in 334A.
- No Python source edits in 334A.
- No changes to production pipeline, parser chain, extraction chain, delivery chain, official assets, or output artifacts.
- Protected dirty files remain untouched and unstaged.

## Planning Principle
The correct migration unit is not “one file at a time with direct moves.” The correct unit is “one dependency cluster at a time with backward-compatible import shims.” Current root imports are too broad for a direct relocation campaign.

## Proposed Phases

### Phase 0: Freeze And Inventory
- Preserve current root file locations.
- Record import graph and risk levels.
- Define allowed target packages.

Exit criteria:
- Per-file audit approved.
- 334B pilot scope explicitly chosen.

### Phase 1: Utility Pilot With Import Shims
Candidate files:
- `artifact_names.py`
- `logger_utils.py`
- `run_state.py`

Proposed target packages:
- `datefac/utils/artifact_names.py`
- `datefac/utils/logger_utils.py`
- `datefac/utils/run_state.py`

Required migration pattern:
1. copy implementation to target package
2. leave root-level compatibility shim importing from package path
3. update a very small number of internal imports only if necessary
4. run focused regression checks

Why this phase is safe:
- low fan-out
- no direct protected pipeline edits required
- limited tool and test exposure

### Phase 2: Low-To-Medium Fan-Out Extraction Helpers
Candidate files:
- `segment_validator.py`
- `extractor_quality.py`
- `raw_table_exporter.py`
- `glued_table_splitter.py`

Conditions before starting:
- Phase 1 must complete cleanly.
- A standard root-shim template must exist.
- Import policy for `datefac/extraction/` must be agreed.

Risks:
- shared helper coupling
- possible hidden CLI consumers
- interaction with `table_block.py`

### Phase 3: Shared Model And Parser Dependencies
Candidate files:
- `table_block.py`
- `pdfplumber_table_extractor.py`
- `pdfplumber_profile_extractor.py`
- `pdfplumber_table_postprocessor.py`
- `extractor_adapter.py`
- `table_classifier.py`
- `table_cleaner.py`

Conditions before starting:
- parser and extraction package boundaries must be explicit
- shim pattern must be proven in earlier phases
- tests for parser and postprocessor modules must pass after staged path migration

Risks:
- direct test breakage
- wide tool breakage
- hidden import path assumptions

### Phase 4: High-Coupling Orchestration And Configuration
Candidate files:
- `config_manager.py`
- `vision_runtime.py`
- `financial_standardizer.py`
- `factory_core.py`

Conditions before starting:
- dependency fan-out reduced from earlier phases
- runtime entry points explicitly documented
- regression plan covers tools and legacy orchestration paths

Risks:
- broad tool breakage
- environment bootstrapping breakage
- regression ambiguity across parser, post-processing, and standardization layers

### Phase 5: Legacy Isolation Or Archival
Candidate files:
- `ai_summary_service.py`

Conditions before starting:
- `factory_core.py` no longer depends directly on root-level legacy service paths

Likely end state:
- move to `datefac/legacy/`
- retain root compatibility shim for one transition cycle

## Recommended 334B Scope
Only do a shim-first pilot for:
- `artifact_names.py`
- `logger_utils.py`
- `run_state.py`

Do not include:
- `factory_core.py`
- `table_segmenter.py`
- `financial_standardizer.py`
- `config_manager.py`
- `vision_runtime.py`
- `table_block.py`
- any `pdfplumber_*` parser modules

## Validation Strategy For Later Migration Tasks
- Verify root shim imports preserve current CLI and test behavior.
- Verify no protected dirty files are staged.
- Verify parser, extraction, and delivery behavior remain unchanged.
- Separate findings by:
  - extraction layer
  - post-processing layer
  - standardization layer
- Prefer focused regression probes over speculative refactors.

## Success Criteria
A future migration stage should only be considered successful if:
- imports continue to resolve from old root paths
- new package paths are canonical
- tests and tool runners using migrated modules still execute
- no production outputs or official assets are changed
- git status remains clean apart from known protected dirty files
