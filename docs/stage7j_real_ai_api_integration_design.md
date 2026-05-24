# Stage7J Real AI API Integration Design

## Purpose
Design real API integration architecture for AI-assisted manual review, without executing real requests.

## Provider abstraction
- disabled provider
- local mock provider
- openai-compatible provider
- deepseek-compatible provider
- qwen-compatible provider

## Core modules
1. config loader + env resolver
2. provider adapter interface
3. request builder (Stage7H schema)
4. response validator (Stage7H/7I rules)
5. suggestion routing (queue vs rejected)
6. human approval gate
7. audit logger

## Security requirements
- No API key in code/repo.
- Use env var indirection only (`api_key_env`).
- external_api_enabled defaults to false.
- explicit runtime flag required for future real-call stage.

## Runtime controls
- timeout, retry, rate cap, token cap, cost cap.
- JSON schema response enforcement.
- fallback to keep_manual_review on any failure.

## Human approval protocol
- all suggestions require_human_approval=true
- no direct write to formal 06
- approval decision logged per review_id
