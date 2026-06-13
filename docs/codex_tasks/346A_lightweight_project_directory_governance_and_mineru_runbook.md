# 346A Lightweight Project Directory Governance And MinerU Runbook

## Goal

Add lightweight directory-governance documentation, README coverage, `.gitignore` hygiene, and a MinerU runbook for the current DateFac repo.

This task is documentation and repository-governance only.
It does not refactor business logic.
It does not move core source files.

## Modification Scope

Allowed:

- lightweight docs
- lightweight directory READMEs
- `.gitignore` minimal supplementation
- MinerU runbook documentation
- this task document
- optional small README link updates

## Forbidden

- moving core Python source files
- renaming `datefac/` core package directories
- large import rewrites
- business logic changes
- deleting existing `input/`, `output/`, or `temp/` contents
- rerunning MinerU
- calling VLM / LLM for benchmark execution
- generating large new benchmark or demo outputs
- `git add -A`
- `git add .`
- `git reset --hard`
- `git checkout --`

## New Or Updated Files

- `docs/architecture/project_directory_governance.md`
- `docs/demo/mineru_runbook.md`
- `docs/codex_tasks/346A_lightweight_project_directory_governance_and_mineru_runbook.md`
- `docs/README.md`
- `tools/README.md`
- `tests/README.md`
- `datefac/README.md`
- `datefac/benchmark/README.md`
- `datefac/extraction/README.md`
- `datefac/pipeline/README.md`
- `datefac/review_queue/README.md`
- `datefac/trust/README.md`
- `datefac/mineru_body/README.md`
- `datefac/parser/README.md`
- `datefac/recognition/README.md`
- `datefac/classification/README.md`
- `datefac/semantic/README.md`
- `datefac/router/README.md`
- `datefac/utils/README.md`
- `.gitignore`
- optional root `README.md` pointer update

## MinerU Runbook Information Sources

The MinerU runbook should be derived from repo-visible evidence such as:

- `tools/*mineru*`
- `datefac/mineru_body/`
- `datefac/pipeline/*mineru*`
- `datefac/benchmark/*mineru*`
- `.skills/mineru_local_benchmark_workflow.md`
- `docs/codex_tasks/320*.md`
- `docs/codex_tasks/337*.md`
- `docs/codex_tasks/342*.md`
- existing MinerU-related `output/*summary.json`, `*qa.json`, and `*report.md` file names

If a command cannot be fully confirmed, mark it clearly as:

`TODO: verify command before running`

## Validation Commands

```powershell
python -m compileall datefac tools
git status --short
```

If `compileall` fails because of a pre-existing unrelated code issue, record the exact failure and do not repair unrelated business logic just to make this task pass.

## Change Summary Template

Use the final report to summarize:

1. changed files
2. newly added READMEs
3. directory-governance doc path
4. MinerU runbook path
5. MinerU runbook information sources
6. whether `.gitignore` changed
7. whether core source files were moved
8. whether business logic changed
9. whether MinerU was rerun
10. validation results
11. `git status --short` summary

## Next-Phase Suggestions

Suggestions only, not implementation:

- abstract a unified LLM client
- abstract a prompt builder
- abstract a response validator
- gradually thin `datefac/benchmark/` so numbered tasks stay organized while shared logic moves to stable packages
- if MinerU command coverage still has `TODO` markers, run a dedicated command-verification task later
