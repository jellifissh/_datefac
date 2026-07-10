"""R7CC MinerU/original reconciliation vertical slice.

This module compares a tiny MinerU-style artifact with an existing extraction
artifact. It is deterministic, pure Python, and intentionally does not write
clean_data, delivery/export output, databases, or readiness gates.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MATCH = "MATCH"
CONFLICT = "CONFLICT"
MINERU_ONLY = "MINERU_ONLY"
ORIGINAL_ONLY = "ORIGINAL_ONLY"
UNPARSEABLE = "UNPARSEABLE"
REVIEW_REQUIRED_STATUSES = frozenset({CONFLICT, MINERU_ONLY, ORIGINAL_ONLY, UNPARSEABLE})
EVIDENCE_PREVIEW_LIMIT = 160
RECONCILIATION_VERSION = "r7cc_mineru_original_reconciliation_vertical_slice_v1"

READINESS_GATES_CLOSED: dict[str, bool] = {
    "client_ready": False,
    "production_ready": False,
    "formal_client_export_allowed": False,
    "demo_export_only": True,
}

METRIC_ALIASES: dict[str, str] = {
    "revenue": "revenue",
    "operating revenue": "revenue",
    "营业收入": "revenue",
    "收入": "revenue",
    "net profit": "net_profit",
    "net income": "net_profit",
    "归母净利润": "net_profit",
    "净利润": "net_profit",
    "eps": "eps",
    "earnings per share": "eps",
    "每股收益": "eps",
    "roe": "roe",
    "return on equity": "roe",
    "净资产收益率": "roe",
}

METRIC_DISPLAY_NAMES: dict[str, str] = {
    "revenue": "Revenue",
    "net_profit": "Net Profit",
    "eps": "EPS",
    "roe": "ROE",
}

METRIC_SORT_ORDER: dict[str, int] = {
    "revenue": 10,
    "net_profit": 20,
    "eps": 30,
    "roe": 40,
}


def load_json_artifact(path: str | Path) -> Any:
    """Load a JSON artifact from a caller-supplied path."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_metric_name(metric_name: Any) -> str | None:
    """Normalize a metric alias to a canonical metric key."""

    if metric_name is None:
        return None
    text = str(metric_name).strip()
    if not text:
        return None
    compact = re.sub(r"[\s_\-/（）()]+", " ", text).strip().lower()
    if compact in METRIC_ALIASES:
        return METRIC_ALIASES[compact]
    no_space = compact.replace(" ", "")
    return METRIC_ALIASES.get(no_space)


def metric_display_name(metric_key: str | None, fallback: Any = "") -> str:
    """Return a stable display name for a normalized metric key."""

    if metric_key in METRIC_DISPLAY_NAMES:
        return METRIC_DISPLAY_NAMES[metric_key]
    return str(fallback or "UNPARSEABLE_METRIC")


def normalize_period(period: Any) -> str | None:
    """Normalize common annual period strings to a year."""

    if period is None:
        return None
    text = str(period).strip()
    if not text:
        return None
    match = re.search(r"(20\d{2}|19\d{2})", text)
    if match:
        return match.group(1)
    return text


def normalize_numeric_value(value: Any) -> str | None:
    """Normalize a numeric value to a deterministic decimal string."""

    if value is None:
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "").replace("，", "")
    text = text.replace("％", "%")
    text = re.sub(r"\s+", "", text)
    is_parenthesized_negative = text.startswith("(") and text.endswith(")")
    if is_parenthesized_negative:
        text = "-" + text[1:-1]
    text = text.rstrip("%")
    text = re.sub(r"(元|亿元|万元|百万元|倍|CNYm|cnym|RMB|rmb)$", "", text)
    try:
        decimal = Decimal(text)
    except InvalidOperation:
        return None
    if decimal == 0:
        return "0"
    normalized = decimal.normalize()
    return format(normalized, "f")


def extract_mineru_records(mineru_artifact: Any) -> list[dict[str, Any]]:
    """Extract normalized rows from a tiny MinerU content_list_v2-style artifact."""

    artifact = deepcopy(mineru_artifact)
    pages = _extract_mineru_pages(artifact)
    records: list[dict[str, Any]] = []
    for page_idx, page_blocks in enumerate(pages):
        page_number = page_idx + 1
        if not isinstance(page_blocks, list):
            continue
        for block_index, block in enumerate(page_blocks):
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type", "unknown"))
            bbox = block.get("bbox")
            rows = _extract_rows_from_mineru_block(block)
            for row_index, row in enumerate(rows):
                record = _record_from_row(
                    source="mineru",
                    row=row,
                    row_index=row_index,
                    source_trace={
                        "source": "mineru",
                        "page_number": page_number,
                        "page_idx": page_idx,
                        "block_index": block_index,
                        "block_type": block_type,
                        "bbox": bbox,
                    },
                )
                records.append(record)
    return records


def extract_original_records(original_artifact: Any) -> list[dict[str, Any]]:
    """Extract normalized rows from an existing extraction artifact."""

    artifact = deepcopy(original_artifact)
    rows = artifact.get("rows", artifact) if isinstance(artifact, dict) else artifact
    records: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return records
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        source_trace = {
            "source": "original",
            "source_row_id": row.get("row_id", f"original:{row_index}"),
            "row_index": row_index,
            "sheet": row.get("sheet"),
        }
        records.append(_record_from_row(source="original", row=row, row_index=row_index, source_trace=source_trace))
    return records


def compare_records(
    mineru_records: list[dict[str, Any]],
    original_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare normalized MinerU and original records."""

    mineru_by_key, mineru_unparseable = _index_records(mineru_records)
    original_by_key, original_unparseable = _index_records(original_records)
    comparison_rows: list[dict[str, Any]] = []

    for key in sorted(set(mineru_by_key) | set(original_by_key), key=_sort_key):
        mineru_record = mineru_by_key.get(key)
        original_record = original_by_key.get(key)
        if mineru_record and original_record:
            if mineru_record["normalized_value"] == original_record["normalized_value"]:
                status = MATCH
                reason = "values match after metric, period, and numeric normalization"
            else:
                status = CONFLICT
                reason = "normalized values differ for the same metric and period"
            comparison_rows.append(_comparison_row(status, reason, mineru_record, original_record))
        elif mineru_record:
            comparison_rows.append(
                _comparison_row(MINERU_ONLY, "metric-period exists only in MinerU artifact", mineru_record, None)
            )
        elif original_record:
            comparison_rows.append(
                _comparison_row(ORIGINAL_ONLY, "metric-period exists only in original extraction", None, original_record)
            )

    for record in mineru_unparseable:
        comparison_rows.append(_comparison_row(UNPARSEABLE, "MinerU row could not be normalized", record, None))
    for record in original_unparseable:
        comparison_rows.append(_comparison_row(UNPARSEABLE, "Original row could not be normalized", None, record))

    return comparison_rows


def reconcile_mineru_original(mineru_artifact: Any, original_artifact: Any) -> dict[str, Any]:
    """Build comparison rows and review_queue-style candidates."""

    mineru_records = extract_mineru_records(mineru_artifact)
    original_records = extract_original_records(original_artifact)
    comparison_rows = compare_records(mineru_records, original_records)
    review_candidates = build_review_queue_candidates(comparison_rows)
    return {
        "reconciliation_version": RECONCILIATION_VERSION,
        "comparison_rows": comparison_rows,
        "review_queue_candidates": review_candidates,
        "summary": {
            "comparison_row_count": len(comparison_rows),
            "review_required_count": len(review_candidates),
            "match_count": sum(1 for row in comparison_rows if row["status"] == MATCH),
            "conflict_count": sum(1 for row in comparison_rows if row["status"] == CONFLICT),
            "mineru_only_count": sum(1 for row in comparison_rows if row["status"] == MINERU_ONLY),
            "original_only_count": sum(1 for row in comparison_rows if row["status"] == ORIGINAL_ONLY),
            "unparseable_count": sum(1 for row in comparison_rows if row["status"] == UNPARSEABLE),
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        },
    }


def load_and_reconcile(mineru_path: str | Path, original_path: str | Path) -> dict[str, Any]:
    """Load two JSON artifacts and reconcile them."""

    return reconcile_mineru_original(load_json_artifact(mineru_path), load_json_artifact(original_path))


def build_review_queue_candidates(comparison_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build compact review_queue-style candidates from review-required rows."""

    candidates: list[dict[str, Any]] = []
    for row in comparison_rows:
        if not row["review_required"]:
            continue
        identity = f"{row['metric']}|{row['period']}|{row['status']}"
        review_item_id = "r7cc:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        candidates.append(
            {
                "review_item_id": review_item_id,
                "candidate_metric_name": row["metric"],
                "candidate_period": row["period"],
                "agreement_status": row["status"],
                "reason": row["reason"],
                "blocked_delivery_reason": row["blocked_delivery_reason"],
                "evidence_preview": row["evidence_preview"],
                "source_trace": deepcopy(row["source_trace"]),
                "review_status": "PENDING_REVIEW",
                "clean_data_eligible": False,
                "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
            }
        )
    return candidates


def _extract_mineru_pages(artifact: Any) -> list[Any]:
    if isinstance(artifact, list):
        return artifact
    if isinstance(artifact, dict):
        pages = artifact.get("content_list_v2", artifact.get("pages"))
        if isinstance(pages, list):
            return pages
    return []


def _extract_rows_from_mineru_block(block: dict[str, Any]) -> list[dict[str, Any]]:
    content = block.get("content", {})
    if isinstance(content, dict) and isinstance(content.get("rows"), list):
        return [row for row in content["rows"] if isinstance(row, dict)]
    if all(key in block for key in ("metric", "period", "value")):
        return [block]
    return []


def _record_from_row(
    *,
    source: str,
    row: dict[str, Any],
    row_index: int,
    source_trace: dict[str, Any],
) -> dict[str, Any]:
    raw_metric = row.get("metric", row.get("metric_name"))
    raw_period = row.get("period")
    raw_value = row.get("value")
    metric_key = normalize_metric_name(raw_metric)
    normalized_period = normalize_period(raw_period)
    normalized_value = normalize_numeric_value(raw_value)
    evidence_preview = _bounded_preview(
        row.get("evidence_preview")
        or row.get("raw_text")
        or f"{raw_metric or ''} {raw_period or ''} {raw_value or ''}".strip()
    )
    return {
        "source": source,
        "metric_key": metric_key,
        "metric": metric_display_name(metric_key, raw_metric),
        "period": normalized_period,
        "normalized_value": normalized_value,
        "raw_metric": raw_metric,
        "raw_period": raw_period,
        "raw_value": raw_value,
        "unit": row.get("unit"),
        "evidence_preview": evidence_preview,
        "source_trace": {
            **{key: value for key, value in source_trace.items() if value is not None},
            "row_index": row_index,
        },
    }


def _index_records(records: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    unparseable: list[dict[str, Any]] = []
    for record in records:
        if not record["metric_key"] or not record["period"] or record["normalized_value"] is None:
            unparseable.append(record)
            continue
        key = (record["metric_key"], record["period"])
        if key not in indexed:
            indexed[key] = record
        else:
            duplicate = deepcopy(record)
            duplicate["metric"] = metric_display_name(record["metric_key"], record["raw_metric"])
            unparseable.append(duplicate)
    return indexed, unparseable


def _comparison_row(
    status: str,
    reason: str,
    mineru_record: dict[str, Any] | None,
    original_record: dict[str, Any] | None,
) -> dict[str, Any]:
    primary = mineru_record or original_record or {}
    metric = primary.get("metric", "UNPARSEABLE_METRIC")
    period = primary.get("period") or "UNPARSEABLE_PERIOD"
    review_required = status in REVIEW_REQUIRED_STATUSES
    return {
        "metric": metric,
        "period": period,
        "mineru_value": None if mineru_record is None else mineru_record["normalized_value"],
        "original_value": None if original_record is None else original_record["normalized_value"],
        "status": status,
        "reason": reason,
        "review_required": review_required,
        "blocked_delivery_reason": "" if not review_required else _blocked_delivery_reason(status),
        "evidence_preview": _comparison_preview(mineru_record, original_record),
        "source_trace": {
            "mineru": None if mineru_record is None else deepcopy(mineru_record["source_trace"]),
            "original": None if original_record is None else deepcopy(original_record["source_trace"]),
        },
    }


def _comparison_preview(
    mineru_record: dict[str, Any] | None,
    original_record: dict[str, Any] | None,
) -> str:
    previews: list[str] = []
    if mineru_record is not None:
        previews.append(f"MinerU: {mineru_record['evidence_preview']}")
    if original_record is not None:
        previews.append(f"Original: {original_record['evidence_preview']}")
    return _bounded_preview(" | ".join(previews))


def _bounded_preview(value: Any, *, limit: int = EVIDENCE_PREVIEW_LIMIT) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _blocked_delivery_reason(status: str) -> str:
    return {
        CONFLICT: "value_conflict_requires_review",
        MINERU_ONLY: "mineru_only_requires_review",
        ORIGINAL_ONLY: "original_only_requires_review",
        UNPARSEABLE: "unparseable_row_requires_review",
    }.get(status, "")


def _sort_key(key: tuple[str, str]) -> tuple[int, str, str]:
    metric_key, period = key
    return (METRIC_SORT_ORDER.get(metric_key, 999), metric_key, period)


__all__ = [
    "CONFLICT",
    "EVIDENCE_PREVIEW_LIMIT",
    "MATCH",
    "MINERU_ONLY",
    "ORIGINAL_ONLY",
    "READINESS_GATES_CLOSED",
    "RECONCILIATION_VERSION",
    "REVIEW_REQUIRED_STATUSES",
    "UNPARSEABLE",
    "build_review_queue_candidates",
    "compare_records",
    "extract_mineru_records",
    "extract_original_records",
    "load_and_reconcile",
    "load_json_artifact",
    "metric_display_name",
    "normalize_metric_name",
    "normalize_numeric_value",
    "normalize_period",
    "reconcile_mineru_original",
]
