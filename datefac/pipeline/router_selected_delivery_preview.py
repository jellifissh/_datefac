from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


MINERU_322A_SOURCE = "ROUTER_DRIVEN_MINERU_BODY_322A"


@dataclass
class SelectedOutputBundle:
    selected_preview_df: pd.DataFrame
    metric_candidates_df: pd.DataFrame
    trusted_df: pd.DataFrame
    review_required_df: pd.DataFrame
    rejected_df: pd.DataFrame
    semantic_worklist_df: pd.DataFrame
    manual_review_df: pd.DataFrame
    delivery_preview_rows: List[Dict[str, Any]]
    selected_output_sources: Dict[str, str]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value).lower() in {"1", "true", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0
        return int(float(value))
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _ensure_columns(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return out


def _parse_provenance_json(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _sample_labels(df: pd.DataFrame, limit: int = 5) -> str:
    if df.empty or "raw_metric_name" not in df.columns:
        return ""
    values = []
    for value in df["raw_metric_name"].astype(str).tolist():
        text = _norm(value)
        if text and text not in values:
            values.append(text)
        if len(values) >= limit:
            break
    return "|".join(values)


def _build_selected_preview_row(table_asset_id: str, recognizer: str, table_df: pd.DataFrame, notes: str, risk_tags: str = "") -> Dict[str, Any]:
    candidate_count = len(table_df)
    trusted_count = int((table_df["split_decision"].astype(str) == "trusted_preview").sum()) if candidate_count else 0
    review_required_count = int((table_df["split_decision"].astype(str) == "review_required_preview").sum()) if candidate_count else 0
    rejected_count = int((table_df["split_decision"].astype(str) == "rejected_preview").sum()) if candidate_count else 0
    trusted_rate = round(trusted_count / candidate_count, 6) if candidate_count else 0.0
    provenance_complete = bool(candidate_count) and all(table_df["provenance_json"].astype(str).map(lambda v: bool(_parse_provenance_json(v))))
    if not risk_tags and candidate_count:
        risk_values: List[str] = []
        for tags in table_df["risk_tags"].astype(str).tolist():
            for tag in [item.strip() for item in tags.split("|") if item.strip()]:
                if tag not in risk_values:
                    risk_values.append(tag)
        risk_tags = "|".join(risk_values)
    return {
        "table_asset_id": table_asset_id,
        "selected_output_source": recognizer,
        "output_origin": "322A_NEW_MINERU" if recognizer == MINERU_322A_SOURCE else "EXISTING_SANDBOX_OUTPUT",
        "candidate_count": candidate_count,
        "trusted_count": trusted_count,
        "review_required_count": review_required_count,
        "rejected_count": rejected_count,
        "core_candidate_trusted_rate": trusted_rate,
        "all_candidate_trusted_rate": trusted_rate,
        "risk_tags": risk_tags,
        "provenance_status": "COMPLETE" if provenance_complete else "PARTIAL_OR_MISSING",
        "notes": notes,
    }


def _split_from_candidates(candidates_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if candidates_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    trusted_df = candidates_df[candidates_df["split_decision"].astype(str) == "trusted_preview"].copy()
    review_df = candidates_df[candidates_df["split_decision"].astype(str) == "review_required_preview"].copy()
    rejected_df = candidates_df[candidates_df["split_decision"].astype(str) == "rejected_preview"].copy()
    return trusted_df, review_df, rejected_df


def build_router_selected_delivery_preview(
    route_inventory_df: pd.DataFrame,
    action_plan_rows: Sequence[Dict[str, Any]],
    base_selected_preview_df: pd.DataFrame,
    existing_candidates_by_table: Dict[str, pd.DataFrame],
    new_322a_candidates_df: pd.DataFrame,
    existing_selected_output_sources: Dict[str, str],
) -> SelectedOutputBundle:
    route_inventory_df = _ensure_columns(
        route_inventory_df,
        [
            "table_asset_id",
            "source_report_name",
            "table_title",
            "effective_category",
            "recommended_recognizer",
            "fallback_recognizer",
            "semantic_adjudicator_required",
            "manual_review_required",
            "router_risk_tags",
            "router_reason",
        ],
    ).fillna("")
    base_selected_preview_df = _ensure_columns(
        base_selected_preview_df,
        [
            "table_asset_id",
            "selected_output_source",
            "candidate_count",
            "trusted_count",
            "review_required_count",
            "rejected_count",
            "core_candidate_trusted_rate",
            "all_candidate_trusted_rate",
            "risk_tags",
            "provenance_status",
            "notes",
        ],
    ).fillna("")
    new_322a_candidates_df = _ensure_columns(
        new_322a_candidates_df,
        [
            "candidate_id",
            "source_stage",
            "source_file",
            "source_doc_name",
            "source_table_id",
            "source_row_index",
            "source_row_text",
            "metric_code",
            "canonical_metric_name",
            "raw_metric_name",
            "year",
            "period_type",
            "raw_value",
            "normalized_value",
            "unit",
            "unit_source",
            "currency",
            "confidence",
            "year_source",
            "smoke_check_status",
            "smoke_check_source",
            "table_title",
            "table_unit",
            "risk_tags",
            "split_decision",
            "split_reason",
            "provenance_json",
            "metric_family",
        ],
    ).fillna("")
    base_preview_map = {
        _norm(row.get("table_asset_id")): row.to_dict()
        for _, row in base_selected_preview_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    route_map = {
        _norm(row.get("table_asset_id")): row.to_dict()
        for _, row in route_inventory_df.iterrows()
        if _norm(row.get("table_asset_id"))
    }
    action_map = {
        _norm(row.get("table_asset_id")): dict(row)
        for row in action_plan_rows
        if _norm(row.get("table_asset_id"))
    }
    new_grouped = {
        table_id: df.copy()
        for table_id, df in new_322a_candidates_df.groupby(new_322a_candidates_df["source_table_id"].astype(str))
    } if not new_322a_candidates_df.empty else {}

    preview_rows: List[Dict[str, Any]] = []
    delivery_preview_rows: List[Dict[str, Any]] = []
    selected_output_sources: Dict[str, str] = {}
    candidate_frames: List[pd.DataFrame] = []
    semantic_rows: List[Dict[str, Any]] = []
    manual_rows: List[Dict[str, Any]] = []

    seen_table_ids: set[str] = set()
    all_table_ids = list(dict.fromkeys(list(route_map.keys()) + list(base_preview_map.keys()) + list(existing_candidates_by_table.keys()) + list(new_grouped.keys())))
    for table_asset_id in all_table_ids:
        if not table_asset_id or table_asset_id in seen_table_ids:
            continue
        seen_table_ids.add(table_asset_id)
        route_row = route_map.get(table_asset_id, {})
        action_row = action_map.get(table_asset_id, {})
        selected_output_source = ""
        selected_table_df = pd.DataFrame()
        notes = ""
        risk_tags = _norm(route_row.get("router_risk_tags"))

        if table_asset_id in new_grouped and not new_grouped[table_asset_id].empty:
            selected_output_source = MINERU_322A_SOURCE
            selected_table_df = new_grouped[table_asset_id].copy()
            notes = "newly generated 322A MinerU-body output"
        elif table_asset_id in existing_candidates_by_table and not existing_candidates_by_table[table_asset_id].empty:
            selected_output_source = _norm(existing_selected_output_sources.get(table_asset_id))
            selected_table_df = existing_candidates_by_table[table_asset_id].copy()
            notes = _norm(base_preview_map.get(table_asset_id, {}).get("notes")) or "existing sandbox selected output"
        elif table_asset_id in base_preview_map:
            preview_row = dict(base_preview_map[table_asset_id])
            preview_row.setdefault("output_origin", "EXISTING_SANDBOX_OUTPUT")
            preview_rows.append(preview_row)
            delivery_preview_rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "selected_output_source": _norm(preview_row.get("selected_output_source")),
                    "output_origin": _norm(preview_row.get("output_origin")) or "EXISTING_SANDBOX_OUTPUT",
                    "candidate_count": _to_int(preview_row.get("candidate_count")),
                    "trusted_count": _to_int(preview_row.get("trusted_count")),
                    "review_required_count": _to_int(preview_row.get("review_required_count")),
                    "rejected_count": _to_int(preview_row.get("rejected_count")),
                    "notes": _norm(preview_row.get("notes")),
                }
            )
            selected_output_sources[table_asset_id] = _norm(preview_row.get("selected_output_source"))
            continue
        else:
            continue

        if not selected_output_source or selected_table_df.empty:
            continue

        selected_output_sources[table_asset_id] = selected_output_source
        preview_row = _build_selected_preview_row(
            table_asset_id=table_asset_id,
            recognizer=selected_output_source,
            table_df=selected_table_df,
            notes=notes,
            risk_tags=risk_tags,
        )
        preview_rows.append(preview_row)
        delivery_preview_rows.append(dict(preview_row))
        candidate_frames.append(selected_table_df)

        semantic_required = _to_bool(route_row.get("semantic_adjudicator_required")) or _to_bool(action_row.get("semantic_adjudicator_required"))
        manual_required = _to_bool(route_row.get("manual_review_required")) or _to_bool(action_row.get("manual_review_required"))
        table_title = _norm(route_row.get("table_title"))
        source_report_name = _norm(route_row.get("source_report_name"))
        if semantic_required:
            semantic_rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "source_report_name": source_report_name,
                    "table_title": table_title,
                    "selected_output_source": selected_output_source,
                    "adjudication_reason": "UNKNOWN_METRIC_CODE_CORE_CONTEXT" if "UNKNOWN_METRIC" in risk_tags else "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION",
                    "risk_tags": risk_tags,
                    "candidate_count_affected": int((selected_table_df["split_decision"].astype(str) == "review_required_preview").sum()),
                    "sample_labels": _sample_labels(selected_table_df),
                    "priority": "HIGH" if _norm(route_row.get("effective_category")) in {"BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT", "FINANCIAL_FORECAST_VALUATION", "CORE_METRIC_TABLE"} else "MEDIUM",
                }
            )
        if manual_required:
            manual_rows.append(
                {
                    "table_asset_id": table_asset_id,
                    "source_report_name": source_report_name,
                    "table_title": table_title,
                    "manual_review_reason": _norm(action_row.get("reason")) or _norm(route_row.get("router_reason")),
                    "selected_output_source": selected_output_source,
                    "priority": "HIGH" if _norm(route_row.get("effective_category")) in {"BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT", "FINANCIAL_FORECAST_VALUATION", "CORE_METRIC_TABLE"} else "MEDIUM",
                    "notes": _norm(route_row.get("router_reason")),
                }
            )

    metric_candidates_df = pd.concat(candidate_frames, ignore_index=True) if candidate_frames else pd.DataFrame()
    trusted_df, review_required_df, rejected_df = _split_from_candidates(metric_candidates_df)
    return SelectedOutputBundle(
        selected_preview_df=pd.DataFrame(preview_rows).drop_duplicates(subset=["table_asset_id"], keep="first") if preview_rows else pd.DataFrame(),
        metric_candidates_df=metric_candidates_df,
        trusted_df=trusted_df,
        review_required_df=review_required_df,
        rejected_df=rejected_df,
        semantic_worklist_df=pd.DataFrame(semantic_rows),
        manual_review_df=pd.DataFrame(manual_rows),
        delivery_preview_rows=delivery_preview_rows,
        selected_output_sources=selected_output_sources,
    )
