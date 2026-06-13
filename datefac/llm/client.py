from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Mapping

import requests

from .config import ChatModelRuntimeConfig


def extract_message_content(response_data: Mapping[str, Any] | None) -> str:
    if not isinstance(response_data, Mapping):
        return ""
    choices = response_data.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""
    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        return ""
    message = first_choice.get("message", {})
    if not isinstance(message, Mapping):
        return ""
    content = message.get("content")
    if content is None:
        return ""
    return re.sub(r"\s+", " ", str(content).strip())


@dataclass
class ChatCompletionsClient:
    config: ChatModelRuntimeConfig
    system_prompt: str
    temperature: float = 0
    response_format: Mapping[str, Any] | None = None

    def adjudicate(self, prompt: str) -> Dict[str, Any]:
        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        if self.response_format is not None:
            payload["response_format"] = dict(self.response_format)
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "raw_response": data,
            "content": extract_message_content(data),
        }
