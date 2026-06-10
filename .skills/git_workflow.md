# Skill: Git Workflow

## Start Every Task With
1. `git status -sb`
2. Read the task boundary carefully
3. Confirm which files are allowed to change

## Hard Staging Rules
- never git add -A
- never git add .
- use precise `git add <path>` only
- stage only files from the current task

## Never Stage
- `output/`
- `temp/`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- large benchmark or demo output artifacts
- unrelated dirty files

## Protected Dirty Files
Keep these unstaged unless the user explicitly asks:
- `datefac/benchmark/batch_row_text_delivery_benchmark.py`
- `datefac/extraction/row_text_metric_extractor.py`
- `datefac/pipeline/batch_ppstructure_row_text_pipeline.py`
- `tools/run_batch_ppstructure_outputs_320g.py`
- `input/semantic_adjudicator_responses_322d/`
- `input/semantic_adjudicator_responses_322f/`
- `temp/`

## Before Commit
1. `git status -sb`
2. `git diff --stat`
3. verify only intended files are staged
4. verify protected dirty files remain unstaged
5. verify output artifacts are not staged

## Output Boundaries
- output artifacts are evidence, not normal commit payloads
- benchmark sidecar outputs are not source-of-truth production assets
- human review / preview / audit outputs should not be committed unless the user explicitly asks

## Risk Rules
- do not use `git reset --hard`
- do not use `git checkout --`
- do not revert unrelated user changes
- if rebase is explicitly required, protect dirty files first and recheck status after rebase
