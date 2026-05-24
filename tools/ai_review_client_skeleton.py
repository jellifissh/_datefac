from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


class ExternalAPIDisabledError(RuntimeError):
    pass


@dataclass
class AIReviewRuntimeConfig:
    provider: str = "disabled"
    base_url: str = ""
    api_key_env: str = "AI_REVIEW_API_KEY"
    model: str = ""
    timeout_seconds: int = 30
    max_retries: int = 2
    max_requests_per_run: int = 5
    max_tokens_per_request: int = 2000
    temperature: float = 0.0
    response_format: str = "json_schema"
    external_api_enabled: bool = False
    require_human_approval: bool = True
    allow_real_apply: bool = False


class AIReviewClientSkeleton:
    """Stage7J skeleton only.

    This class intentionally does NOT perform any real external API call.
    Real calls must be explicitly enabled in future stage by passing
    enable_external_api=True and using reviewed implementation.
    """

    def __init__(self, config: AIReviewRuntimeConfig, enable_external_api: bool = False) -> None:
        self.config = config
        self.enable_external_api = bool(enable_external_api)

    def ensure_runtime_guard(self) -> None:
        if not self.enable_external_api:
            raise ExternalAPIDisabledError(
                "External API call blocked: --enable-external-api not provided."
            )
        if not self.config.external_api_enabled:
            raise ExternalAPIDisabledError(
                "External API call blocked: config.external_api_enabled=false."
            )
        raise ExternalAPIDisabledError(
            "Stage7J skeleton forbids real API call by design."
        )

    def review_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dry-run placeholder returning keep_manual_review for each request."""
        responses: List[Dict[str, Any]] = []
        for req in requests:
            responses.append(
                {
                    "review_id": str(req.get("review_id", "")),
                    "suggested_action": "keep_manual_review",
                    "suggested_row_ids": [],
                    "suggested_metric_name": "",
                    "suggested_year": "",
                    "suggested_value": "",
                    "suggested_unit": "",
                    "confidence": 0.0,
                    "reasoning_summary": "Stage7J skeleton mock response.",
                    "risk_flags": ["skeleton_mode"],
                    "requires_human_approval": True,
                }
            )
        return responses


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows
