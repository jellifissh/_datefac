from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
)


READY_DECISION = "REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_READY"
PARTIAL_DECISION = "REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_PARTIAL"
BLOCKED_DECISION = "REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_BLOCKED"

DEFAULT_CONTEXT_REPAIR_337C_DIR = Path(r"D:\_datefac\output\core_financial_context_repair_337c")
DEFAULT_MINERU_REAL_TEST_DIR = Path(r"D:\_datefac\output\mineru_real_test_337a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

CUSTOMER_WORKBOOK_SHEETS = {
    "readme": "00_README",
    "reviewed": "01_REVIEWED_CORE_METRICS",
    "needs_review": "02_NEEDS_REVIEW",
    "rejected": "03_REJECTED_OR_EXCLUDED",
    "trace": "04_SOURCE_TRACE",
    "document_summary": "05_DOCUMENT_SUMMARY",
    "table_summary": "06_TABLE_CLASSIFICATION_SUMMARY",
    "context_summary": "07_CONTEXT_REPAIR_SUMMARY",
    "suspicious": "08_SUSPICIOUS_REVIEWED_AUDIT",
    "route_change": "09_ROUTE_CHANGE_TRACE",
}

DISPLAY_BY_METRIC = {
    "revenue": "营业收入",
    "net_profit": "归母净利润",
    "EPS": "每股收益",
    "PE": "PE",
    "PB": "PB",
    "ROE": "ROE",
    "gross_margin": "毛利率",
    "net_margin": "净利率",
    "revenue_yoy": "营业收入同比",
    "net_profit_yoy": "归母净利润同比",
}

PERCENT_METRICS = {"ROE", "gross_margin", "net_margin", "revenue_yoy", "net_profit_yoy"}
MULTIPLE_METRICS = {"PE", "PB"}
YUAN_METRICS = {"EPS"}
AMOUNT_METRICS = {"revenue", "net_profit"}
MONEY_UNIT_KEYWORDS = ("百万元", "亿元", "万元", "千元", "元")
GROWTH_KEYWORDS = ("同比", "增长", "增长率", "yoy", "YoY", "成长能力")
SUSPICIOUS_356439_KEYWORDS = ("行业", "产品", "渠道", "历史", "公司简介", "品牌", "市场", "竞争格局", "品类")
TABLE_ROLE_PRIORITY = {
    "CORE_FINANCIAL_SUMMARY": 0,
    "PROFIT_FORECAST_VALUATION": 1,
    "FINANCIAL_STATEMENT_DETAIL": 2,
}
HIGH_REVIEWED_PDF = "H3_AP202606081823356439_1.pdf"
YEAR_RE = re.compile(r"(?:19|20)\d{2}[AE]?")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return re.sub(r"\s+", " ", str(value).strip())


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _git_status_porcelain_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_cached_names_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _contains_any(text: str, patterns: Iterable[str]) -> bool:
    normalized = _norm_text(text).casefold()
    return any(pattern.casefold() in normalized for pattern in patterns)


def _extract_year_headers(table_preview: str) -> List[str]:
    lines = [line for line in _norm_text(table_preview).splitlines() if line.strip()]
    candidates = lines[:1] or lines
    years: List[str] = []
    seen = set()
    for text in candidates + lines:
        for match in YEAR_RE.findall(text):
            if match not in seen:
                seen.add(match)
                years.append(match)
    return years


def _extract_evidence_values(evidence: str) -> List[str]:
    cells = [_norm_text(cell) for cell in _norm_text(evidence).split("|")]
    if len(cells) <= 1:
        return []
    return [cell for cell in cells[1:] if cell]


def _normalize_value_for_key(value: Any) -> str:
    text = _norm_text(value).replace(",", "")
    return text.casefold()


def _normalize_unit_for_key(unit: Any) -> str:
    text = _norm_text(unit)
    if text.lower() == "x":
        return "倍"
    return text


def _extract_unit_from_text(text: str) -> str:
    normalized = _norm_text(text)
    if "百万元" in normalized:
        return "百万元"
    if "亿元" in normalized:
        return "亿元"
    if "万元" in normalized:
        return "万元"
    if "千元" in normalized:
        return "千元"
    if "元" in normalized:
        return "元"
    if "%" in normalized:
        return "%"
    if "倍" in normalized or normalized.lower() == "x":
        return "倍"
    return ""


def _metric_display(metric: str, fallback: str) -> str:
    return DISPLAY_BY_METRIC.get(metric, _norm_text(fallback))


def _append_reason(row: MutableMapping[str, Any], reason: str) -> None:
    if not reason:
        return
    reasons = row.setdefault("_suspicious_reasons", [])
    if reason not in reasons:
        reasons.append(reason)


def _append_action(row: MutableMapping[str, Any], action: str) -> None:
    if not action:
        return
    actions = row.setdefault("_actions_337d", [])
    if action not in actions:
        actions.append(action)


def _set_status(row: MutableMapping[str, Any], status: str, reason: str, action: str) -> None:
    row["status_after_337d"] = status
    row["route_reason_after_337d"] = reason
    _append_action(row, action)


def _is_reviewed(row: Mapping[str, Any]) -> bool:
    return _norm_text(row.get("status_after_337d")) == "reviewed_preview"


def _is_money_unit(unit: str) -> bool:
    normalized = _norm_text(unit)
    return any(keyword in normalized for keyword in MONEY_UNIT_KEYWORDS)


def _customer_readme_df() -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {"topic": "Workbook purpose", "message": "This workbook is a stricter 337D local preview derived from 337C context-repair output."},
                {"topic": "Strictness", "message": "337D repairs confident year alignment, blocks percentage-as-amount mistakes, enforces unit strictness, and removes duplicate reviewed rows."},
                {"topic": "Boundaries", "message": "This remains local-only, preview-only, not client-ready, not production-ready, and does not write back to any upstream output."},
            ]
        )
    )


def _prepare_rows(route_df: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for raw in route_df.to_dict(orient="records"):
        row = dict(raw)
        metric = _norm_text(raw.get("metric_after"))
        row["metric_after_337d"] = metric
        row["metric_display_zh_after_337d"] = _metric_display(metric, _norm_text(raw.get("metric_display_zh_after")))
        row["year_after_337d"] = _norm_text(raw.get("year"))
        row["unit_after_337d"] = _normalize_unit_for_key(raw.get("unit_after_337c") or raw.get("unit"))
        row["status_after_337d"] = _norm_text(raw.get("status_after_337c"))
        row["route_reason_after_337d"] = _norm_text(raw.get("route_reason_after_337c"))
        row["duplicate_of"] = ""
        row["year_alignment_changed"] = False
        row["_suspicious_reasons"] = []
        row["_actions_337d"] = []
        rows.append(row)
    return rows


def _apply_year_alignment(rows: List[Dict[str, Any]]) -> Tuple[int, int, pd.DataFrame]:
    repaired_count = 0
    downgraded_count = 0
    audit_rows: List[Dict[str, Any]] = []
    grouped: Dict[Tuple[str, int, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not _is_reviewed(row):
            continue
        key = (
            _norm_text(row.get("document")),
            _safe_int(row.get("table_index"), -1),
            _norm_text(row.get("metric_after_337d")),
            _norm_text(row.get("source_evidence_excerpt")),
        )
        grouped[key].append(row)

    for group_rows in grouped.values():
        if len(group_rows) <= 1:
            continue
        evidence_values = _extract_evidence_values(_norm_text(group_rows[0].get("source_evidence_excerpt")))
        expected_years = _extract_year_headers(_norm_text(group_rows[0].get("table_preview")))
        unique_years = {_norm_text(row.get("year_after_337d")) for row in group_rows if _norm_text(row.get("year_after_337d"))}
        if len(evidence_values) != len(group_rows) or len(expected_years) < len(evidence_values):
            if len(unique_years) < len(group_rows):
                for row in group_rows:
                    _append_reason(row, "same_year_multiple_values_from_same_evidence")
                    _set_status(row, "needs_review", "year_alignment_not_confident", "DOWNGRADE_YEAR_ALIGNMENT")
                    downgraded_count += 1
                    audit_rows.append(
                        {
                            "candidate_id": _norm_text(row.get("candidate_id")),
                            "document": _norm_text(row.get("document")),
                            "metric_after_337d": _norm_text(row.get("metric_after_337d")),
                            "old_year": _norm_text(row.get("year")),
                            "new_year": _norm_text(row.get("year_after_337d")),
                            "value": _norm_text(row.get("value")),
                            "action": "DOWNGRADE_YEAR_ALIGNMENT",
                            "detail": "could_not_confidently_map_values_to_year_headers",
                        }
                    )
            continue

        positions_by_value: Dict[str, List[int]] = defaultdict(list)
        for idx, value in enumerate(evidence_values):
            positions_by_value[_normalize_value_for_key(value)].append(idx)

        value_counts = Counter(_normalize_value_for_key(row.get("value")) for row in group_rows)
        confident = True
        for value_key, count in value_counts.items():
            if len(positions_by_value.get(value_key, [])) != count:
                confident = False
                break
        if not confident:
            if len(unique_years) < len(group_rows):
                for row in group_rows:
                    _append_reason(row, "same_year_multiple_values_from_same_evidence")
                    _set_status(row, "needs_review", "year_alignment_not_confident", "DOWNGRADE_YEAR_ALIGNMENT")
                    downgraded_count += 1
                    audit_rows.append(
                        {
                            "candidate_id": _norm_text(row.get("candidate_id")),
                            "document": _norm_text(row.get("document")),
                            "metric_after_337d": _norm_text(row.get("metric_after_337d")),
                            "old_year": _norm_text(row.get("year")),
                            "new_year": _norm_text(row.get("year_after_337d")),
                            "value": _norm_text(row.get("value")),
                            "action": "DOWNGRADE_YEAR_ALIGNMENT",
                            "detail": "duplicate_or_ambiguous_value_positions",
                        }
                    )
            continue

        row_occurrence_counter: Counter[str] = Counter()
        for row in sorted(group_rows, key=lambda item: (_normalize_value_for_key(item.get("value")), _norm_text(item.get("candidate_id")))):
            value_key = _normalize_value_for_key(row.get("value"))
            occurrence_index = row_occurrence_counter[value_key]
            row_occurrence_counter[value_key] += 1
            expected_position = positions_by_value[value_key][occurrence_index]
            expected_year = expected_years[expected_position]
            current_year = _norm_text(row.get("year_after_337d"))
            if current_year != expected_year:
                row["year_after_337d"] = expected_year
                row["year_alignment_changed"] = True
                _append_reason(row, "same_year_multiple_values_from_same_evidence")
                _append_action(row, "REPAIR_YEAR_ALIGNMENT")
                repaired_count += 1
                audit_rows.append(
                    {
                        "candidate_id": _norm_text(row.get("candidate_id")),
                        "document": _norm_text(row.get("document")),
                        "metric_after_337d": _norm_text(row.get("metric_after_337d")),
                        "old_year": current_year,
                        "new_year": expected_year,
                        "value": _norm_text(row.get("value")),
                        "action": "REPAIR_YEAR_ALIGNMENT",
                        "detail": "mapped_value_position_to_header_year",
                    }
                )
    return repaired_count, downgraded_count, _clean_frame(pd.DataFrame(audit_rows))


def _apply_percent_amount_guard(rows: List[Dict[str, Any]]) -> Tuple[int, int, pd.DataFrame]:
    downgraded_count = 0
    remapped_count = 0
    audit_rows: List[Dict[str, Any]] = []
    for row in rows:
        if not _is_reviewed(row):
            continue
        metric = _norm_text(row.get("metric_after_337d"))
        if metric not in AMOUNT_METRICS:
            continue
        value = _norm_text(row.get("value"))
        unit = _normalize_unit_for_key(row.get("unit_after_337d"))
        evidence = _norm_text(row.get("source_evidence_excerpt"))
        if "%" not in value and unit != "%":
            continue
        _append_reason(row, "percent_value_for_amount_metric")
        if "%" in evidence or _contains_any(evidence, GROWTH_KEYWORDS):
            new_metric = "revenue_yoy" if metric == "revenue" else "net_profit_yoy"
            row["metric_after_337d"] = new_metric
            row["metric_display_zh_after_337d"] = _metric_display(new_metric, row.get("metric_display_zh_after_337d"))
            row["unit_after_337d"] = "%"
            row["route_reason_after_337d"] = "percent_amount_guard_remapped"
            _append_action(row, "REMAP_TO_YOY")
            remapped_count += 1
            audit_rows.append(
                {
                    "candidate_id": _norm_text(row.get("candidate_id")),
                    "document": _norm_text(row.get("document")),
                    "old_metric": metric,
                    "new_metric": new_metric,
                    "value": value,
                    "unit": unit,
                    "action": "REMAP_TO_YOY",
                    "detail": "percent_value_or_percent_unit_for_amount_metric",
                }
            )
        else:
            _set_status(row, "needs_review", "percent_amount_guard_downgraded", "DOWNGRADE_PERCENT_AS_AMOUNT")
            downgraded_count += 1
            audit_rows.append(
                {
                    "candidate_id": _norm_text(row.get("candidate_id")),
                    "document": _norm_text(row.get("document")),
                    "old_metric": metric,
                    "new_metric": metric,
                    "value": value,
                    "unit": unit,
                    "action": "DOWNGRADE_PERCENT_AS_AMOUNT",
                    "detail": "percent_unit_without_growth_evidence",
                }
            )
    return downgraded_count, remapped_count, _clean_frame(pd.DataFrame(audit_rows))


def _apply_unit_strictness(rows: List[Dict[str, Any]]) -> Tuple[int, int, pd.DataFrame]:
    downgraded_count = 0
    filled_count = 0
    audit_rows: List[Dict[str, Any]] = []
    for row in rows:
        if not _is_reviewed(row):
            continue
        metric = _norm_text(row.get("metric_after_337d"))
        unit = _normalize_unit_for_key(row.get("unit_after_337d"))
        evidence = _norm_text(row.get("source_evidence_excerpt"))
        preview = _norm_text(row.get("table_preview"))
        inferred_unit = unit or _extract_unit_from_text(evidence) or _extract_unit_from_text(preview)
        desired_unit = inferred_unit
        if metric in MULTIPLE_METRICS and not desired_unit:
            desired_unit = "倍"
        elif metric in YUAN_METRICS and not desired_unit:
            desired_unit = "元"
        elif metric in PERCENT_METRICS and not desired_unit:
            desired_unit = "%"

        if metric in MULTIPLE_METRICS and desired_unit.lower() == "x":
            desired_unit = "倍"

        if metric in AMOUNT_METRICS:
            if not _is_money_unit(desired_unit):
                _append_reason(row, "missing_unit_for_amount_metric")
                _set_status(row, "needs_review", "unit_strictness_missing_money_unit", "DOWNGRADE_MISSING_UNIT")
                downgraded_count += 1
                audit_rows.append(
                    {
                        "candidate_id": _norm_text(row.get("candidate_id")),
                        "document": _norm_text(row.get("document")),
                        "metric": metric,
                        "value": _norm_text(row.get("value")),
                        "unit_before": unit,
                        "unit_after": desired_unit,
                        "action": "DOWNGRADE_MISSING_UNIT",
                        "detail": "reviewed_amount_metric_requires_money_unit",
                    }
                )
                continue
        else:
            if not desired_unit:
                _append_reason(row, "missing_unit_for_amount_metric")
                _set_status(row, "needs_review", "unit_strictness_missing_unit", "DOWNGRADE_MISSING_UNIT")
                downgraded_count += 1
                audit_rows.append(
                    {
                        "candidate_id": _norm_text(row.get("candidate_id")),
                        "document": _norm_text(row.get("document")),
                        "metric": metric,
                        "value": _norm_text(row.get("value")),
                        "unit_before": unit,
                        "unit_after": desired_unit,
                        "action": "DOWNGRADE_MISSING_UNIT",
                        "detail": "reviewed_metric_requires_unit",
                    }
                )
                continue

        if unit != desired_unit:
            row["unit_after_337d"] = desired_unit
            filled_count += 1
            _append_action(row, "FILL_OR_NORMALIZE_UNIT")
            audit_rows.append(
                {
                    "candidate_id": _norm_text(row.get("candidate_id")),
                    "document": _norm_text(row.get("document")),
                    "metric": metric,
                    "value": _norm_text(row.get("value")),
                    "unit_before": unit,
                    "unit_after": desired_unit,
                    "action": "FILL_OR_NORMALIZE_UNIT",
                    "detail": "filled_or_normalized_reviewed_unit",
                }
            )
    return downgraded_count, filled_count, _clean_frame(pd.DataFrame(audit_rows))


def _apply_356439_targeted_audit(rows: List[Dict[str, Any]]) -> int:
    downgraded_count = 0
    for row in rows:
        if not _is_reviewed(row):
            continue
        if _norm_text(row.get("document")) != HIGH_REVIEWED_PDF:
            continue
        combined = " ".join(
            [
                _norm_text(row.get("table_preview")),
                _norm_text(row.get("source_evidence_excerpt")),
            ]
        )
        if _contains_any(combined, SUSPICIOUS_356439_KEYWORDS):
            _append_reason(row, "suspicious_356439_source")
            _set_status(row, "needs_review", "356439_targeted_audit_downgrade", "DOWNGRADE_356439_SUSPICIOUS_SOURCE")
            downgraded_count += 1
    return downgraded_count


def _apply_reviewed_dedup(rows: List[Dict[str, Any]]) -> Tuple[int, pd.DataFrame]:
    removed_count = 0
    audit_rows: List[Dict[str, Any]] = []
    grouped: Dict[Tuple[str, str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not _is_reviewed(row):
            continue
        key = (
            _norm_text(row.get("document")),
            _norm_text(row.get("metric_after_337d")),
            _norm_text(row.get("year_after_337d")),
            _normalize_value_for_key(row.get("value")),
            _normalize_unit_for_key(row.get("unit_after_337d")),
        )
        grouped[key].append(row)

    for group_rows in grouped.values():
        if len(group_rows) <= 1:
            continue
        sorted_rows = sorted(
            group_rows,
            key=lambda item: (
                TABLE_ROLE_PRIORITY.get(_norm_text(item.get("table_role_337c")), 99),
                _safe_int(item.get("source_page"), 9999),
                _norm_text(item.get("candidate_id")),
            ),
        )
        kept = sorted_rows[0]
        kept_id = _norm_text(kept.get("candidate_id"))
        for row in sorted_rows[1:]:
            row["duplicate_of"] = kept_id
            _append_reason(row, "duplicate_reviewed_row")
            _set_status(row, "rejected_or_excluded", "duplicate_reviewed_row", "REMOVE_DUPLICATE_REVIEWED")
            removed_count += 1
            audit_rows.append(
                {
                    "candidate_id": _norm_text(row.get("candidate_id")),
                    "document": _norm_text(row.get("document")),
                    "metric": _norm_text(row.get("metric_after_337d")),
                    "year": _norm_text(row.get("year_after_337d")),
                    "value": _norm_text(row.get("value")),
                    "unit": _norm_text(row.get("unit_after_337d")),
                    "duplicate_of": kept_id,
                    "action": "REMOVE_DUPLICATE_REVIEWED",
                    "detail": f"kept_source_role={_norm_text(kept.get('table_role_337c'))}",
                }
            )
    return removed_count, _clean_frame(pd.DataFrame(audit_rows))


def _build_customer_frames(rows: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = _clean_frame(pd.DataFrame(rows))

    def _sheet(status: str) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(columns=["row_no", "document", "metric", "metric_display_zh", "year", "value", "unit", "source_page", "status", "source_evidence_excerpt", "notes"])
        selected = frame[frame["status_after_337d"] == status].copy()
        if selected.empty:
            return pd.DataFrame(columns=["row_no", "document", "metric", "metric_display_zh", "year", "value", "unit", "source_page", "status", "source_evidence_excerpt", "notes"])
        out = _clean_frame(
            selected[
                [
                    "document",
                    "metric_after_337d",
                    "metric_display_zh_after_337d",
                    "year_after_337d",
                    "value",
                    "unit_after_337d",
                    "source_page",
                    "status_after_337d",
                    "source_evidence_excerpt",
                    "route_reason_after_337d",
                ]
            ].rename(
                columns={
                    "metric_after_337d": "metric",
                    "metric_display_zh_after_337d": "metric_display_zh",
                    "year_after_337d": "year",
                    "unit_after_337d": "unit",
                    "status_after_337d": "status",
                    "route_reason_after_337d": "notes",
                }
            )
        )
        out.insert(0, "row_no", range(1, len(out) + 1))
        return out

    return _sheet("reviewed_preview"), _sheet("needs_review"), _sheet("rejected_or_excluded")


def _build_suspicious_audit_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    suspicious_rows = []
    for row in rows:
        if _norm_text(row.get("status_after_337c")) != "reviewed_preview":
            continue
        reasons = row.get("_suspicious_reasons", [])
        actions = row.get("_actions_337d", [])
        if not reasons and not actions and _norm_text(row.get("status_after_337d")) == "reviewed_preview":
            continue
        suspicious_rows.append(
            {
                "candidate_id": _norm_text(row.get("candidate_id")),
                "document": _norm_text(row.get("document")),
                "metric": _norm_text(row.get("metric_after_337d")),
                "year": _norm_text(row.get("year_after_337d")),
                "value": _norm_text(row.get("value")),
                "unit": _norm_text(row.get("unit_after_337d")),
                "source_page": row.get("source_page", ""),
                "evidence": _norm_text(row.get("source_evidence_excerpt")),
                "suspicious_reason": "|".join(reasons),
                "337d_action": "|".join(actions) or _norm_text(row.get("route_reason_after_337d")),
            }
        )
    return _clean_frame(pd.DataFrame(suspicious_rows))


def _build_route_change_trace_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    changed_rows = []
    for row in rows:
        changed = any(
            [
                _norm_text(row.get("metric_after")) != _norm_text(row.get("metric_after_337d")),
                _norm_text(row.get("year")) != _norm_text(row.get("year_after_337d")),
                _normalize_unit_for_key(row.get("unit_after_337c")) != _normalize_unit_for_key(row.get("unit_after_337d")),
                _norm_text(row.get("status_after_337c")) != _norm_text(row.get("status_after_337d")),
                _norm_text(row.get("duplicate_of")) != "",
            ]
        )
        if not changed:
            continue
        changed_rows.append(
            {
                "candidate_id": _norm_text(row.get("candidate_id")),
                "document": _norm_text(row.get("document")),
                "metric_before_337d": _norm_text(row.get("metric_after")),
                "metric_after_337d": _norm_text(row.get("metric_after_337d")),
                "year_before_337d": _norm_text(row.get("year")),
                "year_after_337d": _norm_text(row.get("year_after_337d")),
                "unit_before_337d": _normalize_unit_for_key(row.get("unit_after_337c")),
                "unit_after_337d": _normalize_unit_for_key(row.get("unit_after_337d")),
                "status_before_337d": _norm_text(row.get("status_after_337c")),
                "status_after_337d": _norm_text(row.get("status_after_337d")),
                "route_reason_before_337d": _norm_text(row.get("route_reason_after_337c")),
                "route_reason_after_337d": _norm_text(row.get("route_reason_after_337d")),
                "duplicate_of": _norm_text(row.get("duplicate_of")),
                "337d_action": "|".join(row.get("_actions_337d", [])),
                "suspicious_reason": "|".join(row.get("_suspicious_reasons", [])),
                "source_evidence_excerpt": _norm_text(row.get("source_evidence_excerpt")),
            }
        )
    return _clean_frame(pd.DataFrame(changed_rows))


def _build_document_summary_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    frame = _clean_frame(pd.DataFrame(rows))
    if frame.empty:
        return pd.DataFrame()
    grouped = frame.groupby("document", dropna=False)
    result_rows = []
    for document, group in grouped:
        result_rows.append(
            {
                "document": document,
                "reviewed_after_337d_count": int((group["status_after_337d"] == "reviewed_preview").sum()),
                "needs_review_after_337d_count": int((group["status_after_337d"] == "needs_review").sum()),
                "rejected_after_337d_count": int((group["status_after_337d"] == "rejected_or_excluded").sum()),
            }
        )
    return _clean_frame(pd.DataFrame(result_rows))


def _build_table_summary_df(table_df: pd.DataFrame, rows: List[Dict[str, Any]]) -> pd.DataFrame:
    table_work = _clean_frame(table_df.copy())
    if table_work.empty:
        return pd.DataFrame()
    counts = defaultdict(int)
    for row in rows:
        if _is_reviewed(row):
            counts[(_norm_text(row.get("document")), _safe_int(row.get("table_index"), -1))] += 1
    table_work["reviewed_after_337d_count"] = table_work.apply(
        lambda item: counts.get((_norm_text(item.get("document")), _safe_int(item.get("table_index"), -1)), 0),
        axis=1,
    )
    return table_work


def build_reviewed_strictness_year_alignment_337d(
    *,
    context_repair_337c_dir: Path,
    mineru_real_test_dir: Path,
    output_dir: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)

    summary_337c_path = context_repair_337c_dir / "core_financial_context_repair_337c_summary.json"
    workbook_337c_path = context_repair_337c_dir / "real_test_mineru_client_export_337c.xlsx"
    summary_337a_path = mineru_real_test_dir / "00_batch_summary.json"

    blocked_reasons: List[str] = []
    for path in [summary_337c_path, workbook_337c_path, summary_337a_path]:
        if not path.exists():
            blocked_reasons.append(f"Missing required input: {path}")

    if blocked_reasons:
        summary = {
            "generated_at_utc": _utc_now(),
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": len(blocked_reasons),
            "decision": BLOCKED_DECISION,
        }
        return {
            "summary": summary,
            "manifest": {},
            "qa_json": {"decision": BLOCKED_DECISION, "qa_fail_count": len(blocked_reasons), "checks": [], "blocked_reasons": blocked_reasons},
            "no_apply_proof": {},
            "before_after_sheets": {},
            "customer_workbook_sheets": {},
        }

    summary_337c = json.loads(summary_337c_path.read_text(encoding="utf-8"))
    summary_337a = json.loads(summary_337a_path.read_text(encoding="utf-8"))
    route_df = _read_excel(workbook_337c_path, "04_SOURCE_TRACE")
    table_df = _read_excel(workbook_337c_path, "06_TABLE_CLASSIFICATION_SUMMARY")

    rows = _prepare_rows(route_df)
    year_alignment_repaired_count, year_alignment_downgraded_count, year_alignment_df = _apply_year_alignment(rows)
    percent_amount_guard_downgraded_count, percent_amount_guard_remapped_count, percent_guard_df = _apply_percent_amount_guard(rows)
    unit_strictness_downgraded_count, unit_strictness_filled_count, unit_strictness_df = _apply_unit_strictness(rows)
    reviewed_356439_targeted_downgrade_count = _apply_356439_targeted_audit(rows)
    reviewed_duplicate_removed_count, reviewed_dedup_df = _apply_reviewed_dedup(rows)

    reviewed_customer_df, needs_review_customer_df, rejected_customer_df = _build_customer_frames(rows)
    suspicious_audit_df = _build_suspicious_audit_df(rows)
    route_change_trace_df = _build_route_change_trace_df(rows)
    document_summary_df = _build_document_summary_df(rows)
    table_summary_df = _build_table_summary_df(table_df, rows)

    reviewed_356439_before_count = _safe_int(summary_337c.get("reviewed_356439_after_count", 0))
    reviewed_356439_after_count = 0
    if not document_summary_df.empty:
        reviewed_356439_after_count = int(
            document_summary_df.loc[
                document_summary_df["document"] == HIGH_REVIEWED_PDF,
                "reviewed_after_337d_count",
            ].sum()
        )
    reviewed_356439_downgraded_count = reviewed_356439_before_count - reviewed_356439_after_count

    context_summary_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "reviewed_before_count": _safe_int(summary_337c.get("reviewed_after_count", 0)),
                    "reviewed_after_count": len(reviewed_customer_df),
                    "needs_review_after_count": len(needs_review_customer_df),
                    "rejected_after_count": len(rejected_customer_df),
                    "year_alignment_repaired_count": year_alignment_repaired_count,
                    "year_alignment_downgraded_count": year_alignment_downgraded_count,
                    "percent_amount_guard_remapped_count": percent_amount_guard_remapped_count,
                    "percent_amount_guard_downgraded_count": percent_amount_guard_downgraded_count,
                    "unit_strictness_filled_count": unit_strictness_filled_count,
                    "unit_strictness_downgraded_count": unit_strictness_downgraded_count,
                    "reviewed_duplicate_removed_count": reviewed_duplicate_removed_count,
                    "reviewed_356439_before_count": reviewed_356439_before_count,
                    "reviewed_356439_after_count": reviewed_356439_after_count,
                    "reviewed_356439_downgraded_count": reviewed_356439_downgraded_count,
                }
            ]
        )
    )

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)

    reviewed_frame = _clean_frame(pd.DataFrame(rows))
    if not reviewed_frame.empty:
        reviewed_frame = reviewed_frame[reviewed_frame["status_after_337d"] == "reviewed_preview"].copy()

    reviewed_amount_mask = reviewed_frame["metric_after_337d"].isin(sorted(AMOUNT_METRICS)) if not reviewed_frame.empty else pd.Series(dtype=bool)
    reviewed_amounts = reviewed_frame[reviewed_amount_mask].copy() if not reviewed_frame.empty else pd.DataFrame()
    duplicate_check_ok = True
    if not reviewed_amounts.empty or not reviewed_frame.empty:
        dedup_key = reviewed_frame.apply(
            lambda row: (
                _norm_text(row.get("document")),
                _norm_text(row.get("metric_after_337d")),
                _norm_text(row.get("year_after_337d")),
                _normalize_value_for_key(row.get("value")),
                _normalize_unit_for_key(row.get("unit_after_337d")),
            ),
            axis=1,
        )
        duplicate_check_ok = not dedup_key.duplicated().any()

    qa_checks = [
        {"check_name": "input_337c_workbook_exists", "status": "PASS" if workbook_337c_path.exists() else "FAIL", "detail": str(workbook_337c_path)},
        {"check_name": "three_pdfs_represented", "status": "PASS" if len(document_summary_df) == 3 else "FAIL", "detail": str(len(document_summary_df))},
        {
            "check_name": "reviewed_after_not_higher_than_337c",
            "status": "PASS" if len(reviewed_customer_df) <= _safe_int(summary_337c.get("reviewed_after_count", 0)) else "FAIL",
            "detail": f"{len(reviewed_customer_df)} <= {_safe_int(summary_337c.get('reviewed_after_count', 0))}",
        },
        {
            "check_name": "no_reviewed_revenue_net_profit_percent_unit",
            "status": "PASS" if reviewed_amounts.empty or not reviewed_amounts["unit_after_337d"].astype(str).str.contains("%", na=False).any() else "FAIL",
            "detail": str(0 if reviewed_amounts.empty else int(reviewed_amounts["unit_after_337d"].astype(str).str.contains('%', na=False).sum())),
        },
        {
            "check_name": "no_reviewed_revenue_net_profit_percent_value",
            "status": "PASS" if reviewed_amounts.empty or not reviewed_amounts["value"].astype(str).str.contains("%", na=False).any() else "FAIL",
            "detail": str(0 if reviewed_amounts.empty else int(reviewed_amounts["value"].astype(str).str.contains('%', na=False).sum())),
        },
        {
            "check_name": "no_reviewed_revenue_net_profit_empty_unit",
            "status": "PASS" if reviewed_amounts.empty or not reviewed_amounts["unit_after_337d"].astype(str).str.strip().eq("").any() else "FAIL",
            "detail": str(0 if reviewed_amounts.empty else int(reviewed_amounts["unit_after_337d"].astype(str).str.strip().eq("").sum())),
        },
        {"check_name": "no_duplicate_reviewed_rows", "status": "PASS" if duplicate_check_ok else "FAIL", "detail": str(duplicate_check_ok)},
        {
            "check_name": "356439_reviewed_not_higher_than_337c",
            "status": "PASS" if reviewed_356439_after_count <= reviewed_356439_before_count else "FAIL",
            "detail": f"{reviewed_356439_after_count} <= {reviewed_356439_before_count}",
        },
        {
            "check_name": "downgraded_rows_in_route_change_trace",
            "status": "PASS" if not route_change_trace_df.empty else "FAIL",
            "detail": str(len(route_change_trace_df)),
        },
        {"check_name": "client_ready_false", "status": "PASS", "detail": "False"},
        {"check_name": "production_ready_false", "status": "PASS", "detail": "False"},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "client_ready": False,
        "production_ready": False,
        "context_repair_337c_dir": str(context_repair_337c_dir),
        "mineru_real_test_dir": str(mineru_real_test_dir),
        "output_dir": str(output_dir),
        "reviewed_before_count": _safe_int(summary_337c.get("reviewed_after_count", 0)),
        "reviewed_after_count": len(reviewed_customer_df),
        "needs_review_after_count": len(needs_review_customer_df),
        "rejected_after_count": len(rejected_customer_df),
        "year_alignment_repaired_count": year_alignment_repaired_count,
        "year_alignment_downgraded_count": year_alignment_downgraded_count,
        "percent_amount_guard_downgraded_count": percent_amount_guard_downgraded_count,
        "percent_amount_guard_remapped_count": percent_amount_guard_remapped_count,
        "unit_strictness_downgraded_count": unit_strictness_downgraded_count,
        "unit_strictness_filled_count": unit_strictness_filled_count,
        "reviewed_duplicate_removed_count": reviewed_duplicate_removed_count,
        "reviewed_356439_before_count": reviewed_356439_before_count,
        "reviewed_356439_after_count": reviewed_356439_after_count,
        "reviewed_356439_downgraded_count": reviewed_356439_downgraded_count,
        "no_official_asset_modification_during_337d": official_assets_before == official_assets_after,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "document_status_counts": document_summary_df.to_dict(orient="records"),
        "reviewed_before_337a_count": _safe_int(summary_337a.get("reviewed_count", 0)),
    }

    no_apply_proof = build_no_apply_proof(
        stage="337d",
        files_read=[str(summary_337c_path), str(workbook_337c_path), str(summary_337a_path)],
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    manifest = {
        "task": "337D_reviewed_strictness_year_alignment_qa",
        "context_repair_337c_dir": str(context_repair_337c_dir),
        "mineru_real_test_dir": str(mineru_real_test_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "reviewed_strictness_year_alignment_337d_summary.json"),
            "manifest_json": str(output_dir / "reviewed_strictness_year_alignment_337d_manifest.json"),
            "qa_json": str(output_dir / "reviewed_strictness_year_alignment_337d_qa.json"),
            "no_apply_proof_json": str(output_dir / "reviewed_strictness_year_alignment_337d_no_apply_proof.json"),
            "report_md": str(output_dir / "reviewed_strictness_year_alignment_337d_report.md"),
            "before_after_xlsx": str(output_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx"),
            "customer_workbook_xlsx": str(output_dir / "real_test_mineru_client_export_337d.xlsx"),
        },
    }

    qa_json = {
        "decision": decision,
        "qa_fail_count": qa_fail_count,
        "checks": qa_checks,
        "blocked_reasons": blocked_reasons,
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
    }

    before_after_sheets = {
        "00_SUMMARY": context_summary_df,
        "01_337C_COUNTS": _clean_frame(pd.DataFrame([summary_337c])),
        "02_337D_COUNTS": _clean_frame(pd.DataFrame([summary])),
        "03_YEAR_ALIGNMENT_ACTIONS": year_alignment_df,
        "04_PERCENT_AMOUNT_GUARD": percent_guard_df,
        "05_UNIT_STRICTNESS": unit_strictness_df,
        "06_REVIEWED_DEDUP": reviewed_dedup_df,
        "07_REVIEWED_AFTER_337D": reviewed_customer_df,
        "08_NEEDS_REVIEW_AFTER_337D": needs_review_customer_df,
        "09_REJECTED_AFTER_337D": rejected_customer_df,
        "10_SUSPICIOUS_REVIEWED_AUDIT": suspicious_audit_df,
        "11_ROUTE_CHANGE_TRACE": route_change_trace_df,
    }

    customer_workbook_sheets = {
        CUSTOMER_WORKBOOK_SHEETS["readme"]: _customer_readme_df(),
        CUSTOMER_WORKBOOK_SHEETS["reviewed"]: reviewed_customer_df,
        CUSTOMER_WORKBOOK_SHEETS["needs_review"]: needs_review_customer_df,
        CUSTOMER_WORKBOOK_SHEETS["rejected"]: rejected_customer_df,
        CUSTOMER_WORKBOOK_SHEETS["trace"]: _clean_frame(pd.DataFrame(rows)),
        CUSTOMER_WORKBOOK_SHEETS["document_summary"]: document_summary_df,
        CUSTOMER_WORKBOOK_SHEETS["table_summary"]: table_summary_df,
        CUSTOMER_WORKBOOK_SHEETS["context_summary"]: context_summary_df,
        CUSTOMER_WORKBOOK_SHEETS["suspicious"]: suspicious_audit_df,
        CUSTOMER_WORKBOOK_SHEETS["route_change"]: route_change_trace_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_apply_proof": no_apply_proof,
        "before_after_sheets": before_after_sheets,
        "customer_workbook_sheets": customer_workbook_sheets,
    }
