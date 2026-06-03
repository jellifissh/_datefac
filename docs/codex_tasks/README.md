# Codex Task Handoff Convention

This directory stores full Codex task prompts for DateFac.

## Rule

When preparing a new Codex task:

1. Put the complete Codex prompt in `docs/codex_tasks/` as a dedicated markdown file.
2. In ChatGPT conversation, only provide:
   - the short Codex prompt;
   - the purpose of each step;
   - key guardrails or risks if needed.
3. Do not paste the full long-form Codex prompt directly into chat unless explicitly requested.

## Suggested filename format

```text
<stage>_<short_task_name>.md
```

Example:

```text
322k_controlled_official_patch_proposal.md
```

## Why

Full prompts belong in version-controlled docs so Codex can consume them directly, while the chat stays readable and focused on task intent. Humanity has produced enough scroll-walls already.
