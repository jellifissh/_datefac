from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


CORE_ROLE_SET = {
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "CORE_METRIC_TABLE",
    "FINANCIAL_FORECAST_VALUATION",
}
SAFE_UNITLESS_METRICS = {
    "roe",
    "gross_margin",
    "revenue_growth",
    "net_profit_growth",
    "debt_ratio",
    "pe",
    "pb",
    "ev_ebitda",
}
PER_SHARE_METRICS = {"eps", "bps"}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _split_risk_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _normalize_label(text: Any) -> str:
    return _norm(text).replace("\u3000", "").replace(" ", "").lower()


def build_review_burden_by_reason_322b2(review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "review_reason",
        "candidate_count",
        "unique_table_count",
        "unique_label_count",
        "sample_labels",
        "recommended_next_action",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    rows: List[Dict[str, Any]] = []
    for review_reason, group in review_df.groupby(review_df["split_reason"].astype(str)):
        labels: List[str] = []
        for value in group["raw_metric_name"].astype(str).tolist():
            text = _norm(value)
            if text and text not in labels:
                labels.append(text)
            if len(labels) >= 8:
                break
        next_action = "manual_review_required"
        if review_reason == "UNKNOWN_METRIC_CODE":
            next_action = "alias_candidate_review"
        elif review_reason == "SECTION_CONTEXT_REQUIRED":
            next_action = "semantic_adjudicator_candidate"
        elif review_reason == "UNIT_UNKNOWN":
            next_action = "manual_review_required"
        elif review_reason in {"INVALID_OR_MISSING_YEAR", "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN", "HAS_MAPPING_REVIEW_TAG"}:
            next_action = "manual_review_required"
        rows.append(
            {
                "review_reason": review_reason,
                "candidate_count": int(len(group)),
                "unique_table_count": int(group["source_table_id"].astype(str).nunique()) if "source_table_id" in group.columns else 0,
                "unique_label_count": int(group["raw_metric_name"].astype(str).nunique()) if "raw_metric_name" in group.columns else 0,
                "sample_labels": "|".join(labels),
                "recommended_next_action": next_action,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["candidate_count", "unique_table_count", "review_reason"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_unknown_metric_label_frequency_322b2(review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "normalized_label",
        "raw_label_examples",
        "candidate_count",
        "unique_table_count",
        "table_title_examples",
        "suggested_action",
        "priority",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    filtered = review_df[review_df["metric_code"].astype(str) == "unknown_metric"].copy()
    if filtered.empty:
        return pd.DataFrame(columns=columns)
    rows: List[Dict[str, Any]] = []
    for normalized_label, group in filtered.groupby(filtered["raw_metric_name"].map(_normalize_label)):
        raw_examples = []
        titles = []
        for value in group["raw_metric_name"].astype(str).tolist():
            text = _norm(value)
            if text and text not in raw_examples:
                raw_examples.append(text)
            if len(raw_examples) >= 5:
                break
        for value in group["table_title"].astype(str).tolist():
            text = _norm(value)
            if text and text not in titles:
                titles.append(text)
            if len(titles) >= 3:
                break
        candidate_count = int(len(group))
        suggested_action = "alias_candidate_review"
        priority = "MEDIUM"
        if any("图" in item or "估值" in item for item in titles):
            suggested_action = "semantic_adjudicator_candidate"
        if candidate_count >= 20:
            priority = "HIGH"
        rows.append(
            {
                "normalized_label": normalized_label,
                "raw_label_examples": "|".join(raw_examples),
                "candidate_count": candidate_count,
                "unique_table_count": int(group["source_table_id"].astype(str).nunique()) if "source_table_id" in group.columns else 0,
                "table_title_examples": "|".join(titles),
                "suggested_action": suggested_action,
                "priority": priority,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["candidate_count", "unique_table_count", "normalized_label"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_unit_unknown_diagnostics_322b2(review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "table_asset_id",
        "table_title",
        "metric_label",
        "metric_code",
        "raw_value",
        "unit_context_source",
        "reason",
        "recommended_action",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    mask = review_df["split_reason"].astype(str).eq("UNIT_UNKNOWN") | review_df["risk_tags"].astype(str).str.contains(
        r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)",
        regex=True,
    )
    filtered = review_df.loc[mask].copy()
    if filtered.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for _, row in filtered.iterrows():
        risk_tags = _split_risk_tags(row.get("risk_tags"))
        rows.append(
            {
                "table_asset_id": _norm(row.get("source_table_id")),
                "table_title": _norm(row.get("table_title")),
                "metric_label": _norm(row.get("raw_metric_name")),
                "metric_code": _norm(row.get("metric_code")),
                "raw_value": _norm(row.get("raw_value")),
                "unit_context_source": _norm(row.get("unit_source")) or _norm(row.get("table_unit")),
                "reason": "UNIT_UNKNOWN" if "UNIT_UNKNOWN" in risk_tags else (_norm(row.get("split_reason")) or "UNIT_UNKNOWN"),
                "recommended_action": "manual_review_required",
            }
        )
    return pd.DataFrame(rows, columns=columns)


def build_section_context_required_diagnostics_322b2(review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "table_asset_id",
        "table_title",
        "duplicated_label",
        "section_context_hint",
        "affected_candidate_count",
        "recommended_action",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    mask = review_df["split_reason"].astype(str).eq("SECTION_CONTEXT_REQUIRED") | review_df["risk_tags"].astype(str).str.contains(
        r"(?:^|\|)(?:SECTION_CONTEXT_REQUIRED|VALUE_CONFLICT)(?:$|\|)",
        regex=True,
    )
    filtered = review_df.loc[mask].copy()
    if filtered.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for (table_asset_id, table_title, raw_metric_name), group in filtered.groupby(
        [
            filtered["source_table_id"].astype(str),
            filtered["table_title"].astype(str),
            filtered["raw_metric_name"].astype(str),
        ]
    ):
        section_hints: List[str] = []
        for risk_text in group["risk_tags"].astype(str).tolist():
            for tag in _split_risk_tags(risk_text):
                if tag not in section_hints and tag in {"SECTION_CONTEXT_REQUIRED", "VALUE_CONFLICT"}:
                    section_hints.append(tag)
        rows.append(
            {
                "table_asset_id": table_asset_id,
                "table_title": table_title,
                "duplicated_label": raw_metric_name,
                "section_context_hint": "|".join(section_hints),
                "affected_candidate_count": int(len(group)),
                "recommended_action": "semantic_adjudicator_candidate",
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["affected_candidate_count", "table_asset_id", "duplicated_label"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def build_alias_candidate_worklist_322b2(
    unknown_metric_label_frequency_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "normalized_label",
        "raw_label_examples",
        "suggested_metric_code",
        "suggested_metric_family",
        "evidence_table_titles",
        "candidate_count",
        "priority",
        "safety_level",
        "requires_human_confirmation",
    ]
    if unknown_metric_label_frequency_df.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for _, row in unknown_metric_label_frequency_df.iterrows():
        if int(row.get("candidate_count", 0)) < 3:
            continue
        rows.append(
            {
                "normalized_label": _norm(row.get("normalized_label")),
                "raw_label_examples": _norm(row.get("raw_label_examples")),
                "suggested_metric_code": "",
                "suggested_metric_family": "",
                "evidence_table_titles": _norm(row.get("table_title_examples")),
                "candidate_count": int(row.get("candidate_count", 0)),
                "priority": _norm(row.get("priority")) or "MEDIUM",
                "safety_level": "LOW",
                "requires_human_confirmation": True,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["candidate_count", "normalized_label"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_semantic_adjudicator_worklist_322b2(review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "table_asset_id",
        "source_report_name",
        "table_title",
        "adjudication_reason",
        "affected_candidate_count",
        "sample_labels",
        "sample_values",
        "priority",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for table_asset_id, group in review_df.groupby(review_df["source_table_id"].astype(str)):
        reasons = set(group["split_reason"].astype(str).tolist())
        if not reasons.intersection({"UNKNOWN_METRIC_CODE", "SECTION_CONTEXT_REQUIRED"}):
            continue
        labels = []
        values = []
        for label in group["raw_metric_name"].astype(str).tolist():
            text = _norm(label)
            if text and text not in labels:
                labels.append(text)
            if len(labels) >= 6:
                break
        for value in group["raw_value"].astype(str).tolist():
            text = _norm(value)
            if text and text not in values:
                values.append(text)
            if len(values) >= 6:
                break
        adjudication_reason = "UNKNOWN_METRIC_CODE_CORE_CONTEXT"
        if "SECTION_CONTEXT_REQUIRED" in reasons:
            adjudication_reason = "VALUE_CONFLICT_SECTION_CONTEXT"
        rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(group["source_doc_name"].iloc[0]) if not group.empty else "",
                "table_title": _norm(group["table_title"].iloc[0]) if not group.empty else "",
                "adjudication_reason": adjudication_reason,
                "affected_candidate_count": int(len(group)),
                "sample_labels": "|".join(labels),
                "sample_values": "|".join(values),
                "priority": "HIGH",
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["affected_candidate_count", "table_asset_id"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_manual_review_worklist_322b2(review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "table_asset_id",
        "source_report_name",
        "table_title",
        "manual_review_reason",
        "selected_output_source",
        "priority",
        "notes",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for table_asset_id, group in review_df.groupby(review_df["source_table_id"].astype(str)):
        reason_counts = group["split_reason"].astype(str).value_counts()
        dominant_reason = str(reason_counts.index[0]) if not reason_counts.empty else "REVIEW_REQUIRED"
        review_count = int(len(group))
        if review_count < 20 and dominant_reason not in {"INVALID_OR_MISSING_YEAR", "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN"}:
            continue
        rows.append(
            {
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(group["source_doc_name"].iloc[0]) if not group.empty else "",
                "table_title": _norm(group["table_title"].iloc[0]) if not group.empty else "",
                "manual_review_reason": dominant_reason,
                "selected_output_source": _norm(group["selected_output_source"].iloc[0]) if "selected_output_source" in group.columns and not group.empty else "",
                "priority": "HIGH" if review_count >= 50 else "MEDIUM",
                "notes": f"review_candidate_count={review_count}",
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["priority", "table_asset_id"],
        ascending=[True, True],
    ).reset_index(drop=True)


def known_limitations_df_322b2() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322B2 recalibrates router-driven MinerU trust split in sandbox only and does not modify production delivery files.",
            },
            {
                "limitation": "deterministic_only",
                "detail": "322B2 only applies deterministic trust/review/reject gates before any semantic adjudication design.",
            },
            {
                "limitation": "no_alias_expansion",
                "detail": "322B2 surfaces alias candidates as review worklists only and does not alter mapping rules.",
            },
        ]
    )
