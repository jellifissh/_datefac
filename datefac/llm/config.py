from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Dict, Mapping, Sequence, Tuple


DEFAULT_TIMEOUT_SECONDS = 60


@dataclass
class ChatModelRuntimeConfig:
    api_key: str
    base_url: str
    model: str
    env_source: str
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


def _normalize_env_value(value: str | None) -> str:
    return str(value or "").strip()


def _status_map(source_env: Mapping[str, str], keys: Sequence[str]) -> Dict[str, str]:
    return {
        key: "SET" if _normalize_env_value(source_env.get(key)) else "MISSING"
        for key in keys
    }


def _resolve_triplet(
    source_env: Mapping[str, str],
    *,
    api_key_name: str,
    base_url_name: str,
    model_name: str,
) -> Tuple[str, str, str]:
    return (
        _normalize_env_value(source_env.get(api_key_name)),
        _normalize_env_value(source_env.get(base_url_name)),
        _normalize_env_value(source_env.get(model_name)),
    )


def resolve_ai_review_runtime_config(
    env: Mapping[str, str] | None = None,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Tuple[ChatModelRuntimeConfig | None, Dict[str, str]]:
    source_env = dict(os.environ if env is None else env)
    keys = (
        "AI_REVIEW_API_KEY",
        "AI_REVIEW_BASE_URL",
        "AI_MODEL",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_MODEL",
    )
    statuses = _status_map(source_env, keys)
    preferred = _resolve_triplet(
        source_env,
        api_key_name="AI_REVIEW_API_KEY",
        base_url_name="AI_REVIEW_BASE_URL",
        model_name="AI_MODEL",
    )
    if all(preferred):
        return (
            ChatModelRuntimeConfig(
                api_key=preferred[0],
                base_url=preferred[1],
                model=preferred[2],
                env_source="AI_REVIEW",
                timeout_seconds=timeout_seconds,
            ),
            statuses,
        )

    fallback = _resolve_triplet(
        source_env,
        api_key_name="DEEPSEEK_API_KEY",
        base_url_name="DEEPSEEK_BASE_URL",
        model_name="DEEPSEEK_MODEL",
    )
    if all(fallback):
        return (
            ChatModelRuntimeConfig(
                api_key=fallback[0],
                base_url=fallback[1],
                model=fallback[2],
                env_source="DEEPSEEK_FALLBACK",
                timeout_seconds=timeout_seconds,
            ),
            statuses,
        )
    return None, statuses


def resolve_deepseek_runtime_config(
    env: Mapping[str, str] | None = None,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Tuple[ChatModelRuntimeConfig | None, Dict[str, str]]:
    source_env = dict(os.environ if env is None else env)
    keys = ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL")
    statuses = _status_map(source_env, keys)
    values = _resolve_triplet(
        source_env,
        api_key_name="DEEPSEEK_API_KEY",
        base_url_name="DEEPSEEK_BASE_URL",
        model_name="DEEPSEEK_MODEL",
    )
    if not all(values):
        return None, statuses
    return (
        ChatModelRuntimeConfig(
            api_key=values[0],
            base_url=values[1],
            model=values[2],
            env_source="DEEPSEEK",
            timeout_seconds=timeout_seconds,
        ),
        statuses,
    )
