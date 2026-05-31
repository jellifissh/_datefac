from __future__ import annotations

import re
from html import unescape
from typing import Any, Dict, List


FLOAT_SEQ_RULE = re.compile(r"(?:-?\d+\.\d+\s*,?\s*){4,}")
HTML_TAG_RULE = re.compile(r"<[^>]+>")
CELL_BBOX_RULE = re.compile(r"cell_bbox", re.IGNORECASE)
HTML_START_RULE = re.compile(r"^\s*<(html|table|tbody|tr|td|div|span)\b", re.IGNORECASE)


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _clean_html_to_text(s: str) -> str:
    t = _norm(s)
    if not t:
        return ""
    t = HTML_TAG_RULE.sub(" ", t)
    t = unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def classify_and_clean_row_text(row_text: str) -> Dict[str, str]:
    raw = _norm(row_text)
    if not raw:
        return {"category": "EMPTY_OR_NOISE", "cleaned_text": "", "warning_code": "SKIPPED_NOISE_ROW"}

    low = raw.lower()
    if raw.startswith("{") and CELL_BBOX_RULE.search(low):
        return {"category": "RAW_BBOX_METADATA", "cleaned_text": "", "warning_code": "SKIPPED_RAW_BBOX_METADATA"}
    if FLOAT_SEQ_RULE.search(raw):
        return {"category": "RAW_BBOX_METADATA", "cleaned_text": "", "warning_code": "SKIPPED_RAW_BBOX_METADATA"}

    if HTML_START_RULE.search(raw) or ("<td" in low and "</td>" in low):
        cleaned = _clean_html_to_text(raw)
        if cleaned and len(cleaned) >= 2:
            return {"category": "RAW_HTML", "cleaned_text": cleaned, "warning_code": "HTML_CLEANED_TO_TEXT"}
        return {"category": "RAW_HTML", "cleaned_text": "", "warning_code": "SKIPPED_RAW_HTML"}

    if len(raw) <= 1:
        return {"category": "EMPTY_OR_NOISE", "cleaned_text": "", "warning_code": "SKIPPED_NOISE_ROW"}

    return {"category": "HUMAN_ROW_TEXT", "cleaned_text": raw, "warning_code": ""}


def clean_row_texts(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    cleaned_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    skipped_raw_bbox_count = 0
    skipped_raw_html_count = 0

    for r in rows:
        row_text = _norm(r.get("row_text"))
        result = classify_and_clean_row_text(row_text)
        category = result["category"]
        cleaned = result["cleaned_text"]
        warning_code = result["warning_code"]

        base = dict(r)
        base["row_text_raw"] = row_text
        base["row_text_category"] = category
        base["row_text_cleaned"] = cleaned

        if category == "HUMAN_ROW_TEXT":
            cleaned_rows.append(base)
            continue

        if warning_code == "HTML_CLEANED_TO_TEXT" and cleaned:
            cleaned_rows.append(base)
            warnings.append(
                {
                    "source_file": _norm(r.get("source_file")),
                    "extracted_table_id": _norm(r.get("extracted_table_id")),
                    "row_index": r.get("row_index"),
                    "warning_code": warning_code,
                    "warning_message": "HTML row cleaned to text.",
                }
            )
            continue

        rejected_rows.append(base)
        if warning_code:
            warnings.append(
                {
                    "source_file": _norm(r.get("source_file")),
                    "extracted_table_id": _norm(r.get("extracted_table_id")),
                    "row_index": r.get("row_index"),
                    "warning_code": warning_code,
                    "warning_message": "row skipped by cleaner.",
                }
            )
        if warning_code == "SKIPPED_RAW_BBOX_METADATA":
            skipped_raw_bbox_count += 1
        if warning_code in {"SKIPPED_RAW_HTML"}:
            skipped_raw_html_count += 1

    return {
        "cleaned_rows": cleaned_rows,
        "rejected_rows": rejected_rows,
        "warnings": warnings,
        "skipped_raw_bbox_count": skipped_raw_bbox_count,
        "skipped_raw_html_count": skipped_raw_html_count,
    }

