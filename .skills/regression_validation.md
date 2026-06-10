# Skill: Regression Validation

## General Validation
- compile modified Python files with `python -m py_compile ...`
- run focused tests first
- use broader regression only when the task actually touches production code

## Documentation / Skills Refresh Tasks
- prefer consistency checks over heavy runtime execution
- confirm required files exist
- confirm required markers are present
- confirm no accidental `client_ready = true`
- confirm no accidental `production_ready = true`

## Benchmark Validation Boundary
- do not run large benchmark jobs unless the task explicitly requires them
- do not hit HuggingFace or MinerU runtime during documentation-only tasks
- benchmark outputs are evidence, not commit payloads

## Trusted Current Milestones
- human-reviewed client preview chain is the current demo-safe path
- MinerU benchmark chain is still benchmark evidence only
- `342C2` current state is `3/5` success and `ready_for_342d = conditional`

## Reporting Template
- change scope
- what was not changed
- commands executed
- verification result
- remaining risk

