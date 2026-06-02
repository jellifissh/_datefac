from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd

from datefac.semantic.adjudicator_schema import ALLOWED_ACTIONS, build_allowed_metric_codes_rows


PRIORITY_REASON_ORDER = {
    "UNKNOWN_METRIC_CODE": 1,
    "HAS_MAPPING_REVIEW_TAG": 2,
    "UNIT_UNKNOWN": 3,
    "INVALID_OR_MISSING_YEAR": 4,
    "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN": 5,
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(text: Any) -> str:
    return _norm(text).replace("\u3000", "").replace(" ", "").lower()


def _split_risk_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _parse_provenance_json(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _candidate_category(row: pd.Series) -> str:
    reason = _norm(row.get("split_reason"))
    risk_tags = set(_split_risk_tags(row.get("risk_tags_after") or row.get("risk_tags")))
    if reason == "UNKNOWN_METRIC_CODE":
        table_title = _norm(row.get("table_title"))
        if any(keyword in table_title for keyword in ["估值", "可比公司", "图", "基础数据"]):
            return "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION"
        return "UNKNOWN_METRIC_ALIAS_CANDIDATE"
    if "UNIT_UNKNOWN" in risk_tags or reason == "UNIT_UNKNOWN":
        return "UNIT_CONTEXT_INFERENCE"
    if reason == "HAS_MAPPING_REVIEW_TAG":
        return "MAPPING_REVIEW_TAG_EXPLANATION"
    if reason == "INVALID_OR_MISSING_YEAR":
        return "INVALID_YEAR_OR_SCHEMA_REVIEW"
    return "VALUE_PARSE_OR_SCHEMA_UNCERTAIN"


def _priority_label(reason: str) -> str:
    order = PRIORITY_REASON_ORDER.get(reason, 99)
    if order <= 2:
        return "HIGH"
    if order <= 4:
        return "MEDIUM"
    return "LOW"


def build_semantic_case_inventory(review_df: pd.DataFrame, max_case_pack: int) -> pd.DataFrame:
    columns = [
        "case_id",
        "category",
        "table_asset_id",
        "source_report_name",
        "table_title",
        "row_label",
        "current_review_reason",
        "risk_tags",
        "priority",
        "recommended_adjudication_type",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    rows: List[Dict[str, Any]] = []
    sorted_df = review_df.copy()
    sorted_df["__priority_num"] = sorted_df["split_reason"].astype(str).map(lambda x: PRIORITY_REASON_ORDER.get(x, 99))
    sorted_df = sorted_df.sort_values(
        ["__priority_num", "source_table_id", "raw_metric_name", "year"],
        ascending=[True, True, True, True],
    ).head(max_case_pack)
    for _, row in sorted_df.iterrows():
        reason = _norm(row.get("split_reason"))
        category = _candidate_category(row)
        table_asset_id = _norm(row.get("source_table_id"))
        row_label = _norm(row.get("raw_metric_name"))
        year = _norm(row.get("year"))
        case_id = f"case::{table_asset_id}::{_normalize_label(row_label)}::{year or 'na'}"
        recommended_adjudication_type = "candidate_level"
        if category in {"UNKNOWN_METRIC_ALIAS_CANDIDATE", "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION"}:
            recommended_adjudication_type = "label_level"
        rows.append(
            {
                "case_id": case_id,
                "category": category,
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(row.get("source_report_name") or row.get("source_doc_name")),
                "table_title": _norm(row.get("table_title")),
                "row_label": row_label,
                "current_review_reason": reason,
                "risk_tags": _norm(row.get("risk_tags_after") or row.get("risk_tags")),
                "priority": _priority_label(reason),
                "recommended_adjudication_type": recommended_adjudication_type,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def build_label_level_pack(review_df: pd.DataFrame, max_label_pack: int) -> pd.DataFrame:
    columns = [
        "label_case_id",
        "normalized_label",
        "raw_label_examples",
        "candidate_count",
        "unique_table_count",
        "table_title_examples",
        "source_report_examples",
        "value_examples",
        "year_examples",
        "unit_context_examples",
        "current_risk_tags",
        "candidate_category",
        "allowed_metric_codes_sample",
        "allowed_actions",
        "priority",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    filtered = review_df[review_df["split_reason"].astype(str).isin(["UNKNOWN_METRIC_CODE", "HAS_MAPPING_REVIEW_TAG"])].copy()
    if filtered.empty:
        return pd.DataFrame(columns=columns)
    rows: List[Dict[str, Any]] = []
    allowed_metric_codes = build_allowed_metric_codes_rows()
    allowed_metric_code_sample = "|".join(row["metric_code"] for row in allowed_metric_codes[:12])
    for normalized_label, group in filtered.groupby(filtered["raw_metric_name"].map(_normalize_label)):
        raw_examples = []
        titles = []
        reports = []
        values = []
        years = []
        units = []
        risk_tags = []
        for _, row in group.iterrows():
            for target, text in [
                (raw_examples, _norm(row.get("raw_metric_name"))),
                (titles, _norm(row.get("table_title"))),
                (reports, _norm(row.get("source_report_name") or row.get("source_doc_name"))),
                (values, _norm(row.get("raw_value"))),
                (years, _norm(row.get("year"))),
                (units, _norm(row.get("unit")) or _norm(row.get("table_unit"))),
                (risk_tags, _norm(row.get("risk_tags_after") or row.get("risk_tags"))),
            ]:
                if text and text not in target:
                    target.append(text)
        reason = _norm(group["split_reason"].iloc[0]) if not group.empty else ""
        candidate_category = _candidate_category(group.iloc[0])
        label_case_id = f"label::{normalized_label}"
        rows.append(
            {
                "label_case_id": label_case_id,
                "normalized_label": normalized_label,
                "raw_label_examples": "|".join(raw_examples[:5]),
                "candidate_count": int(len(group)),
                "unique_table_count": int(group["source_table_id"].astype(str).nunique()),
                "table_title_examples": "|".join(titles[:3]),
                "source_report_examples": "|".join(reports[:3]),
                "value_examples": "|".join(values[:5]),
                "year_examples": "|".join(years[:5]),
                "unit_context_examples": "|".join(units[:5]),
                "current_risk_tags": "|".join(risk_tags[:5]),
                "candidate_category": candidate_category,
                "allowed_metric_codes_sample": allowed_metric_code_sample,
                "allowed_actions": "|".join(ALLOWED_ACTIONS),
                "priority": _priority_label(reason),
            }
        )
    out = pd.DataFrame(rows, columns=columns).sort_values(
        ["candidate_count", "unique_table_count", "normalized_label"],
        ascending=[False, False, True],
    ).head(max_label_pack)
    return out.reset_index(drop=True)


def build_candidate_level_pack(review_df: pd.DataFrame, semantic_case_inventory_df: pd.DataFrame, max_case_pack: int) -> pd.DataFrame:
    columns = [
        "case_id",
        "table_asset_id",
        "source_report_name",
        "table_title",
        "table_context",
        "row_label",
        "row_values",
        "year_columns",
        "unit_context",
        "current_metric_code",
        "current_risk_tags",
        "current_review_reason",
        "available_provenance",
        "allowed_actions",
        "priority",
    ]
    if review_df.empty or semantic_case_inventory_df.empty:
        return pd.DataFrame(columns=columns)
    candidate_case_ids = set(
        semantic_case_inventory_df[
            semantic_case_inventory_df["recommended_adjudication_type"].astype(str) == "candidate_level"
        ]["case_id"].astype(str).tolist()
    )
    rows: List[Dict[str, Any]] = []
    for _, row in review_df.iterrows():
        table_asset_id = _norm(row.get("source_table_id"))
        row_label = _norm(row.get("raw_metric_name"))
        year = _norm(row.get("year"))
        case_id = f"case::{table_asset_id}::{_normalize_label(row_label)}::{year or 'na'}"
        if case_id not in candidate_case_ids:
            continue
        provenance = _parse_provenance_json(row.get("provenance_json"))
        rows.append(
            {
                "case_id": case_id,
                "table_asset_id": table_asset_id,
                "source_report_name": _norm(row.get("source_report_name") or row.get("source_doc_name")),
                "table_title": _norm(row.get("table_title")),
                "table_context": _norm(provenance.get("matched_by")) or _norm(provenance.get("effective_role_category")),
                "row_label": row_label,
                "row_values": _norm(row.get("raw_value")),
                "year_columns": year,
                "unit_context": _norm(row.get("unit")) or _norm(row.get("table_unit")) or _norm(provenance.get("unit_source")),
                "current_metric_code": _norm(row.get("metric_code")),
                "current_risk_tags": _norm(row.get("risk_tags_after") or row.get("risk_tags")),
                "current_review_reason": _norm(row.get("split_reason")),
                "available_provenance": "yes" if provenance else "provenance_warning",
                "allowed_actions": "|".join(ALLOWED_ACTIONS),
                "priority": _priority_label(_norm(row.get("split_reason"))),
            }
        )
    out = pd.DataFrame(rows, columns=columns).drop_duplicates(subset=["case_id"]).head(max_case_pack)
    return out.reset_index(drop=True)


def build_estimated_review_impact(
    review_df: pd.DataFrame,
    label_level_pack_df: pd.DataFrame,
    candidate_level_pack_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "category",
        "candidate_count",
        "unique_label_count",
        "estimated_llm_resolvable_count",
        "estimated_manual_remaining_count",
        "reason",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)
    rows: List[Dict[str, Any]] = []
    category_groups: Dict[str, pd.DataFrame] = {}
    for category in [
        "UNKNOWN_METRIC_ALIAS_CANDIDATE",
        "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION",
        "UNIT_CONTEXT_INFERENCE",
        "MAPPING_REVIEW_TAG_EXPLANATION",
        "INVALID_YEAR_OR_SCHEMA_REVIEW",
        "VALUE_PARSE_OR_SCHEMA_UNCERTAIN",
    ]:
        category_groups[category] = review_df[review_df.apply(_candidate_category, axis=1) == category].copy()
    for category, group in category_groups.items():
        candidate_count = int(len(group))
        unique_label_count = int(group["raw_metric_name"].astype(str).nunique()) if not group.empty else 0
        if category in {"UNKNOWN_METRIC_ALIAS_CANDIDATE", "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION"}:
            estimated_llm_resolvable_count = int(candidate_count * 0.45)
            reason = "label-level semantic disambiguation should reduce high-frequency unknown labels"
        elif category == "UNIT_CONTEXT_INFERENCE":
            estimated_llm_resolvable_count = int(candidate_count * 0.35)
            reason = "explicit table-title or header unit evidence can be packaged for semantic confirmation"
        elif category == "MAPPING_REVIEW_TAG_EXPLANATION":
            estimated_llm_resolvable_count = int(candidate_count * 0.20)
            reason = "some mapping review tags may be explainable, but many remain manual"
        else:
            estimated_llm_resolvable_count = 0
            reason = "deterministic or manual issue; keep outside initial LLM scope"
        rows.append(
            {
                "category": category,
                "candidate_count": candidate_count,
                "unique_label_count": unique_label_count,
                "estimated_llm_resolvable_count": estimated_llm_resolvable_count,
                "estimated_manual_remaining_count": max(candidate_count - estimated_llm_resolvable_count, 0),
                "reason": reason,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def build_batch_plan(
    label_level_pack_df: pd.DataFrame,
    candidate_level_pack_df: pd.DataFrame,
    output_dir: Path,
) -> pd.DataFrame:
    rows = []
    if not label_level_pack_df.empty:
        rows.append(
            {
                "batch_id": "322C_LABEL_PACK_001",
                "batch_type": "label_level",
                "case_count": int(len(label_level_pack_df)),
                "priority": "HIGH",
                "input_file": str(output_dir / "llm_label_pack_322c.jsonl"),
                "expected_output_file": str(output_dir / "llm_label_pack_322c_output.jsonl"),
            }
        )
    if not candidate_level_pack_df.empty:
        rows.append(
            {
                "batch_id": "322C_CASE_PACK_001",
                "batch_type": "candidate_level",
                "case_count": int(len(candidate_level_pack_df)),
                "priority": "HIGH",
                "input_file": str(output_dir / "llm_candidate_pack_322c.jsonl"),
                "expected_output_file": str(output_dir / "llm_candidate_pack_322c_output.jsonl"),
            }
        )
    return pd.DataFrame(rows)
