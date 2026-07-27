"""Source-neutral normalization helpers."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any


PREVIEW_LIMIT = 240
_PERIOD_PATTERN = re.compile(r"(?P<year>(?:19|20)\d{2})\s*(?:年|/|-)?\s*(?P<suffix>Q[1-4]|H[12]|[AEF])?", re.IGNORECASE)
_NUMERIC_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def compact_text(value: Any) -> str:
    return " ".join("" if value is None else str(value).split())


def normalize_metric_key(value: Any) -> str:
    text = compact_text(value).casefold()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text)
    return text.strip("_")


def normalize_period(value: Any) -> str | None:
    text = compact_text(value).upper().replace("FY", "")
    if not text:
        return None
    match = _PERIOD_PATTERN.search(text)
    if not match:
        return None
    year = match.group("year")
    suffix = (match.group("suffix") or "").upper()
    return f"{year}{suffix}"


def normalize_numeric(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, (int, float)):
        decimal_value = Decimal(str(value))
    else:
        text = compact_text(value).replace(",", "").replace("，", "")
        if not text or text in {"-", "--", "—", "N/A", "NA", "NULL"}:
            return None
        text = text.replace("％", "%")
        if text.startswith("(") and text.endswith(")"):
            text = "-" + text[1:-1].strip()
        text = text.rstrip("%")
        if not _NUMERIC_PATTERN.fullmatch(text):
            return None
        try:
            decimal_value = Decimal(text)
        except InvalidOperation:
            return None
    if not decimal_value.is_finite():
        return None
    normalized = decimal_value.normalize()
    rendered = format(normalized, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return "0" if rendered in {"", "-0"} else rendered


def normalize_unit(value: Any) -> str | None:
    raw_text = compact_text(value).casefold()
    text = raw_text.replace(" ", "")
    if not raw_text:
        return None
    aliases = {
        "%": "percent",
        "％": "percent",
        "percent": "percent",
        "百分点": "percent",
        "倍": "times",
        "x": "times",
        "times": "times",
        "元": "yuan",
        "人民币元": "yuan",
        "万元": "ten_thousand_yuan",
        "千元": "thousand_yuan",
        "百万元": "million_yuan",
        "百万": "million_yuan",
        "亿元": "hundred_million_yuan",
        "亿": "hundred_million_yuan",
        "million": "million",
    }
    return aliases.get(text, normalize_metric_key(raw_text) or None)


def bounded_preview(value: Any, *, limit: int = PREVIEW_LIMIT) -> str:
    text = compact_text(value)
    if limit < 1:
        return ""
    return text if len(text) <= limit else text[: max(limit - 1, 0)] + "…"


def stable_hash(value: Any, *, length: int = 24) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]
