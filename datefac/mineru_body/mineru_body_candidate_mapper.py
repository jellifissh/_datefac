from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.domain.metric_candidate import MetricCandidate
from datefac.mineru_body.mineru_table_normalizer import UnifiedTable
from datefac.vlm.vlm_candidate_mapper import (
    KNOWN_METRICS,
    PER_SHARE_METRICS,
    SAFE_RATIO_METRICS,
    UNKNOWN_METRIC_CODE,
    _as_float,
    _build_candidate_id,
    _canonical_metric_name,
    _contains_corruption,
    _infer_currency,
    _infer_unit,
    _map_metric_code,
    _metric_code_is_known,
    _metric_family,
    _period_from_year,
    candidates_to_dataframe,
)


SOURCE_STAGE = "mineru_table_body_321d"
RECOGNITION_SOURCE = "MINERU_TABLE_BODY_STRUCTURING"


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def map_unified_tables_to_candidates(unified_tables: Sequence[UnifiedTable]) -> Dict[str, Any]:
    candidates: List[MetricCandidate] = []
    mapping_rows: List[Dict[str, Any]] = []
    per_table_rows: List[Dict[str, Any]] = []

    for table in unified_tables:
        previous_metric_code: Optional[str] = None
        previous_metric_label = ""
        table_candidate_start = len(candidates)

        for row in table.rows:
            raw_metric_name = _norm(row.metric_name_cn or row.metric_name_raw)
            metric_code = _map_metric_code(raw_metric_name, previous_metric_code, previous_metric_label)
            if raw_metric_name:
                previous_metric_label = raw_metric_name
                if metric_code != UNKNOWN_METRIC_CODE:
                    previous_metric_code = metric_code

            for value_cell in row.values:
                if not _norm(value_cell.raw_value) and value_cell.normalized_value is None:
                    continue
                year_norm, period_type, year_tags = _period_from_year(value_cell.column)
                parsed_value = value_cell.normalized_value
                if parsed_value is None and _norm(value_cell.raw_value):
                    parsed_value = _as_float(value_cell.raw_value)
                unit, unit_source, unit_tags = _infer_unit(
                    metric_code=metric_code,
                    raw_metric_name=raw_metric_name,
                    table_title=table.table_title,
                    table_unit=table.unit,
                    raw_value=value_cell.raw_value,
                )
                currency = _infer_currency(
                    explicit_currency=table.currency,
                    text_parts=[table.table_title, raw_metric_name, table.unit],
                    unit=unit,
                )

                risk_tags: List[str] = []
                risk_tags.extend(year_tags)
                risk_tags.extend(unit_tags)
                if metric_code == UNKNOWN_METRIC_CODE:
                    risk_tags.append("UNKNOWN_METRIC_CODE")
                if _contains_corruption(raw_metric_name):
                    risk_tags.append("CHINESE_LABEL_CORRUPTED")
                if parsed_value is None:
                    risk_tags.append("VALUE_PARSE_FAILED" if _norm(value_cell.raw_value) else "VALUE_MISSING")
                if row.warnings:
                    risk_tags.extend([warning for warning in row.warnings if _norm(warning)])
                if table.warnings:
                    risk_tags.extend([warning for warning in table.warnings if _norm(warning)])

                candidate = MetricCandidate(
                    candidate_id=_build_candidate_id(
                        source_stage=SOURCE_STAGE,
                        source_file=table.provenance.get("content_source_file", ""),
                        source_table_id=table.table_asset_id,
                        source_row_index=row.row_index,
                        metric_code=metric_code,
                        year=year_norm,
                        raw_value=value_cell.raw_value,
                    ),
                    source_stage=SOURCE_STAGE,
                    source_file=_norm(table.provenance.get("content_source_file")),
                    source_doc_name=table.source_report_name,
                    source_table_id=table.table_asset_id,
                    source_row_index=row.row_index,
                    source_row_text=row.source_row_text,
                    metric_code=metric_code,
                    canonical_metric_name=_canonical_metric_name(metric_code, raw_metric_name),
                    raw_metric_name=raw_metric_name,
                    year=year_norm,
                    period_type=period_type,
                    raw_value=_norm(value_cell.raw_value),
                    normalized_value=parsed_value,
                    unit=unit,
                    unit_source=unit_source,
                    currency=currency,
                    confidence=0.95,
                    year_source="TABLE_HEADER" if not year_tags else "INVALID",
                    smoke_check_status="NOT_APPLICABLE",
                    smoke_check_source="",
                    table_title=table.table_title,
                    table_unit=table.unit,
                    risk_tags=sorted(set(tag for tag in risk_tags if _norm(tag))),
                    split_decision="review_required_preview",
                    split_reason="PENDING_MINERU_BODY_TRUST_SPLIT",
                    provenance_json={
                        "recognition_source": RECOGNITION_SOURCE,
                        "source_stage": SOURCE_STAGE,
                        "table_asset_id": table.table_asset_id,
                        "source_report_name": table.source_report_name,
                        "table_title": table.table_title,
                        "table_unit": table.unit,
                        "content_source_file": _norm(table.provenance.get("content_source_file")),
                        "content_item_index": table.provenance.get("content_item_index"),
                        "matched_by": _norm(table.provenance.get("matched_by")),
                        "effective_role_category": _norm(table.provenance.get("effective_role_category")),
                        "source_image_path": _norm(table.provenance.get("image_path")),
                        "year_source": "TABLE_HEADER" if not year_tags else "INVALID",
                        "unit_source": unit_source,
                    },
                )
                candidates.append(candidate)
                mapping_rows.append(
                    {
                        "table_id": table.table_id,
                        "row_index": row.row_index,
                        "raw_metric_name": raw_metric_name,
                        "metric_code": metric_code,
                        "metric_family": _metric_family(metric_code),
                        "year": year_norm,
                        "raw_value": _norm(value_cell.raw_value),
                        "normalized_value": parsed_value,
                        "unit": unit or "",
                        "split_decision": candidate.split_decision,
                        "risk_tags": "|".join(candidate.risk_tags),
                        "reason": "initial_mapping",
                    }
                )

        table_candidates = candidates[table_candidate_start:]
        per_table_rows.append(
            {
                "table_id": table.table_id,
                "source_report_name": table.source_report_name,
                "table_asset_id": table.table_asset_id,
                "table_title": table.table_title,
                "candidate_count": len(table_candidates),
                "trusted_count": 0,
                "review_required_count": 0,
                "rejected_count": 0,
                "table_decision": "TABLE_NO_CANDIDATES" if not table_candidates else "TABLE_HAS_CANDIDATES",
            }
        )

    return {
        "candidates": candidates,
        "metric_candidates_df": candidates_to_dataframe(candidates),
        "mapping_diagnostics_df": pd.DataFrame(mapping_rows),
        "per_table_summary_df": pd.DataFrame(per_table_rows),
    }


def split_mineru_body_candidates(candidates: Iterable[MetricCandidate], selected_table_ids: Sequence[str], selected_core_roles: Dict[str, str]) -> Dict[str, Any]:
    trusted: List[MetricCandidate] = []
    review_required: List[MetricCandidate] = []
    rejected: List[MetricCandidate] = []

    selected_id_set = set(selected_table_ids)
    core_roles = {"FINANCIAL_FORECAST_VALUATION", "BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT", "CORE_METRIC_TABLE"}

    for candidate in candidates:
        tags = set(candidate.risk_tags)
        table_id = _norm(candidate.source_table_id)
        role = _norm(selected_core_roles.get(table_id))

        def finalize(decision: str, reason: str, bucket: List[MetricCandidate]) -> None:
            candidate.split_decision = decision
            candidate.split_reason = reason
            bucket.append(candidate)

        if table_id not in selected_id_set:
            finalize("rejected_preview", "TABLE_NOT_IN_SELECTED_WORKLIST", rejected)
            continue
        if role and role not in core_roles:
            finalize("review_required_preview", "NON_CORE_ROLE_REVIEW", review_required)
            continue
        if any(tag in tags for tag in {"CHINESE_LABEL_CORRUPTED", "NO_YEAR_COLUMNS", "TABLE_NOT_PARSEABLE"}):
            finalize("rejected_preview", "STRICT_REJECT_TAG", rejected)
            continue
        if any(tag in tags for tag in {"UNKNOWN_METRIC_CODE", "VALUE_PARSE_FAILED", "INVALID_YEAR", "YEAR_MISSING", "ROW_LABEL_MISSING"}):
            finalize("review_required_preview", "HAS_MAPPING_REVIEW_TAG", review_required)
            continue
        if candidate.metric_code == UNKNOWN_METRIC_CODE:
            finalize("review_required_preview", "UNKNOWN_METRIC_CODE", review_required)
            continue
        if candidate.normalized_value is None:
            finalize("review_required_preview", "VALUE_MISSING_OR_INVALID", review_required)
            continue
        if candidate.year_source != "TABLE_HEADER":
            finalize("review_required_preview", "INVALID_OR_NON_HEADER_YEAR", review_required)
            continue
        if not candidate.unit and candidate.metric_code not in SAFE_RATIO_METRICS and candidate.metric_code not in PER_SHARE_METRICS:
            finalize("review_required_preview", "UNIT_UNKNOWN", review_required)
            continue
        finalize("trusted_preview", "PASS_MINERU_BODY_TRUST_GATE", trusted)

    return {
        "trusted_preview": trusted,
        "review_required_preview": review_required,
        "rejected_preview": rejected,
        "trusted_df": candidates_to_dataframe(trusted),
        "review_required_df": candidates_to_dataframe(review_required),
        "rejected_df": candidates_to_dataframe(rejected),
    }
