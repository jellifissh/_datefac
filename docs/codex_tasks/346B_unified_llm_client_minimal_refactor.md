# 346B Unified LLM Client Minimal Refactor

## Task Goal

Introduce a minimal shared LLM client layer for DateFac so repeated chat-model call plumbing is unified without changing prompts, schema expectations, deterministic guards, recommendation logic, or numbered-task business behavior.

This task only standardizes how the model API is called.
It does not standardize what the model should decide.

## Modification Scope

Allowed new shared modules:

- `datefac/llm/__init__.py`
- `datefac/llm/client.py`
- `datefac/llm/config.py`
- `datefac/llm/json_utils.py`
- `datefac/llm/README.md`

Allowed migration targets:

- `datefac/trust/deepseek_text_adjudicator_338a.py`
- `datefac/trust/ai_review_model_ab_338b.py`
- `datefac/trust/grounded_ai_review_338c.py`

Allowed tests/docs:

- `tests/trust/test_unified_llm_client_346b.py`
- `docs/codex_tasks/346B_unified_llm_client_minimal_refactor.md`

## Forbidden

- changing prompt meaning
- changing validator behavior
- changing deterministic guards
- changing recommendation logic
- changing cache key or cache file behavior
- refactoring 342K / 342L / 342M / 342N mainline business logic
- rerunning MinerU
- making real LLM API calls
- touching `input/`, `output/`, or `temp/` artifacts
- modifying protected dirty files
- `git add .`
- `git add -A`
- `git reset --hard`
- `git checkout --`

## New Shared Module Responsibilities

### `datefac/llm/config.py`

- define a small generic chat-model runtime config dataclass
- resolve `AI_REVIEW_*` first for AI-review paths
- fall back to `DEEPSEEK_*` where already supported
- preserve DeepSeek-only environment semantics for 338A

### `datefac/llm/client.py`

- issue OpenAI-compatible `/chat/completions` HTTP requests using `requests.post`
- extract `choices[0].message.content`
- keep the return shape compatible with current trust modules

### `datefac/llm/json_utils.py`

- parse raw JSON responses
- repair fenced JSON blocks
- repair `{...}` bracket slices from noisy text output
- report parse method labels compatible with current task modules

## Migration Strategy

1. Keep public class/function names in 338A/338B/338C available.
2. Move only generic runtime/client/JSON parsing logic to `datefac.llm`.
3. Keep prompts, validators, evidence checks, deterministic guards, and recommendation builders inside the original trust modules.
4. Preserve existing builder call patterns so numbered task runners and tests remain stable.

## Test Plan

Add targeted tests for:

- raw JSON parse
- fenced JSON parse
- bracket repair
- content extraction from OpenAI-compatible responses
- AI-review env preference
- DeepSeek fallback
- DeepSeek-only env resolution
- import compatibility of 338A / 338B / 338C entry points

## Validation Commands

```powershell
python -m compileall datefac tools
python -m pytest tests/trust/test_unified_llm_client_346b.py -q
git status --short
```

## Rollback Boundary

If this task must be reverted later, revert only the new `datefac/llm/` shared layer and the small compatibility changes in 338A/338B/338C.
Do not mix rollback with benchmark/output artifacts or unrelated parser/pipeline work.

## Next-Phase Suggestions

Suggestions only, not implementation:

- abstract a shared prompt builder layer
- abstract shared response validators after behavior is fully snapshotted
- gradually move stable logic from numbered benchmark/trust files into long-lived business modules
- add more schema-level tests for LLM response ingestion and backward compatibility
