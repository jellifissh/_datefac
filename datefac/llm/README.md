# `datefac.llm`

This package contains the minimal shared LLM API call layer introduced by task `346B`.

Scope is intentionally narrow:

- runtime config resolution for chat-model calls
- OpenAI-compatible `/chat/completions` HTTP client
- common JSON response parsing helpers

This package does not own:

- prompts
- schema/business validators
- deterministic guards
- review recommendations
- cache policy

Those behaviors remain in the numbered trust-task modules so the 338A/338B/338C and 342K/342M mainline semantics stay unchanged.
