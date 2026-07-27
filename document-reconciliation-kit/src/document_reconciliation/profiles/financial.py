"""Optional financial metric aliases; the generic core does not depend on this module."""

from __future__ import annotations

from typing import Any

from ..normalization import normalize_metric_key


FINANCIAL_METRIC_ALIASES = {
    "营业收入": "revenue",
    "营收": "revenue",
    "revenue": "revenue",
    "收入": "revenue",
    "归母净利润": "parent_net_profit",
    "归属于母公司股东的净利润": "parent_net_profit",
    "净利润": "net_profit",
    "每股收益": "eps",
    "eps": "eps",
    "净资产收益率": "roe",
    "roe": "roe",
    "市盈率": "pe",
    "pe": "pe",
    "市净率": "pb",
    "p/b": "pb",
    "pb": "pb",
}


def normalize_financial_metric(value: Any) -> str:
    raw = "" if value is None else str(value).strip()
    return FINANCIAL_METRIC_ALIASES.get(raw, normalize_metric_key(raw))
