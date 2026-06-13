from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def parse_model_json(text: str) -> Tuple[Dict[str, Any] | None, str]:
    cleaned = _normalize_text(text)
    if not cleaned:
        return None, "empty_response"
    try:
        return json.loads(cleaned), "raw_json"
    except Exception:
        pass
    if "```" in cleaned:
        for block in cleaned.split("```"):
            candidate = block.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                try:
                    return json.loads(candidate), "fence_repair"
                except Exception:
                    continue
    left = cleaned.find("{")
    right = cleaned.rfind("}")
    if left >= 0 and right > left:
        candidate = cleaned[left : right + 1]
        try:
            return json.loads(candidate), "bracket_repair"
        except Exception:
            return None, "json_parse_failed"
    return None, "json_parse_failed"
