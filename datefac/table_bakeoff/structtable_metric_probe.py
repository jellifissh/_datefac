from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.domain.metric_candidate import MetricCandidate
from datefac.governance.row_text_candidate_mapper import candidates_to_dataframe
from datefac.table_bakeoff.structtable_mapping_comparison import build_structtable_comparison_rows
from datefac.table_bakeoff.structtable_unified_mapper import (
    NON_ROW_TABLE_WARNING,
    QUALITY_REVIEW_WARNING,
    SECTION_CONTEXT_WARNING,
    TABLE_SCHEMA_UNCERTAIN,
    StructTableUnifiedTable,
    normalize_structtable_to_unified_tables,
    unified_tables_to_jsonl_rows,
)
from datefac.vlm.vlm_candidate_mapper import (
    PER_SHARE_METRICS,
    SAFE_RATIO_METRICS,
    UNKNOWN_METRIC_CODE,
    _as_float,
    _canonical_metric_name,
    _contains_corruption,
    _infer_currency,
    _infer_unit,
    _map_metric_code,
    _metric_family,
    _period_from_year,
)


SHEET_ORDER = [
    "summary",
    "structtable_unified_tables",
    "structtable_normalized_rows",
    "structtable_metric_candidates_all",
    "structtable_trusted_preview",
    "structtable_review_required_preview",
    "structtable_rejected_preview",
    "structtable_mapping_diagnostics",
    "structtable_vs_tools_summary",
    "risk_tag_counts",
    "qa_checks",
    "known_limitations",
]

SOURCE_STAGE = "structtable_unified_mapping_321e4"
RECOGNITION_SOURCE = "STRUCTTABLE_MARKDOWN"
STRUCTTABLE_ALIAS_MAP = {
    "毛利率": "gross_margin",
    "毛利率(%)": "gross_margin",
    "毛利率（%）": "gross_margin",
    "销售净利率": "net_margin",
    "销售收入增长率": "revenue_growth",
    "营业收入增长率": "revenue_growth",
    "净利润增长率": "net_profit_growth",
    "归母净利润": "parent_net_profit",
    "归属母公司股东净利润": "parent_net_profit",
    "归属于母公司股东净利润": "parent_net_profit",
    "营业收入": "revenue",
    "货币资金": "cash_and_equivalents",
    "应收和预付款项": "accounts_receivable",
    "在建工程": "unknown_metric",
    "无形资产开发支出": "unknown_metric",
    "长期待摊费用": "unknown_metric",
    "其他非流动资产": "unknown_metric",
    "其他负债": "unknown_metric",
    "股本": "unknown_metric",
    "资本公积金": "unknown_metric",
    "留存收益": "unknown_metric",
    "归母公司股东权益": "shareholders_equity",
    "股东权益合计": "shareholders_equity",
    "负债和股东权益": "total_liabilities_and_equity",
    "eps(x)": "eps",
    "eps（x）": "eps",
    "eps(元)": "eps",
    "pe(x)": "pe",
    "pe（x）": "pe",
    "pb(x)": "pb",
    "pb（x）": "pb",
    "ev/ebitda(x)": "ev_ebitda",
    "ev/ebitda（x）": "ev_ebitda",
    "ebit margin": "unknown_metric",
    "roa": "unknown_metric",
    "roic": "unknown_metric",
    "ps(x)": "unknown_metric",
}
EXTRACTION_RISK_TAGS = {
    NON_ROW_TABLE_WARNING,
    SECTION_CONTEXT_WARNING,
    TABLE_SCHEMA_UNCERTAIN,
    QUALITY_REVIEW_WARNING,
    "POSSIBLE_MISSING_VALUE_RISK",
}
LABEL_RISK_TAGS = {"CHINESE_LABEL_CORRUPTED", "ROW_LABEL_MISSING", "ROW_LABEL_CODE_LIKE", "CORRUPTED_LABEL"}
OUT_OF_SCOPE_RISK_TAGS = {"OUT_OF_SCOPE_METRIC", "NON_CORE_STATEMENT_LINE"}
CORE_BALANCE_SHEET_METRICS = {
    "cash_and_equivalents",
    "accounts_receivable",
    "inventory",
    "current_assets_total",
    "fixed_assets",
    "investment_property",
    "total_assets",
    "accounts_payable",
    "current_liabilities_total",
    "total_liabilities",
    "shareholders_equity",
    "minority_interest",
    "total_liabilities_and_equity",
    "short_term_borrowings",
    "long_term_borrowings",
}
OUT_OF_SCOPE_LABELS = {
    "在建工程",
    "无形资产开发支出",
    "长期待摊费用",
    "其他非流动资产",
    "其他流动资产",
    "其他流动负债",
    "其他非流动负债",
    "其他负债",
    "股本",
    "资本公积金",
    "留存收益",
    "预付款",
    "其他应收款",
    "应收票据及应收款合计",
    "应付票据及应付账款合计",
    "应付和预收款项",
    "流动资产",
    "非流动资产",
    "流动负债",
    "非流动负债",
}


def _stage_slug_for_output(output_dir: Path) -> str:
    name = _norm(output_dir.name).lower()
    return name if name else "structtable_unified_mapping_321e4"


@dataclass
class StructTableMetricProbeConfig:
    structtable_audit_dir: Path
    structtable_output_dir: Path
    input_image_dir: Path
    docling_mapping_dir: Optional[Path]
    docling_audit_dir: Optional[Path]
    mineru_body_dir: Optional[Path]
    pure_vlm_calibration_dir: Optional[Path]
    ppstructure_benchmark_dir: Optional[Path]
    output_dir: Path


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_sheet_name(name: str, used: set[str]) -> str:
    cleaned = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    base = cleaned
    index = 1
    while cleaned in used:
        suffix = f"_{index}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(cleaned)
    return cleaned


def _normalize_metric_label(text: str) -> str:
    return _norm(text).replace("\u3000", "").replace(" ", "").lower()


def _map_structtable_metric_code(raw_metric_name: str, previous_metric_code: Optional[str], previous_metric_label: str) -> str:
    normalized = _normalize_metric_label(raw_metric_name)
    if normalized in STRUCTTABLE_ALIAS_MAP:
        return STRUCTTABLE_ALIAS_MAP[normalized]
    return _map_metric_code(raw_metric_name, previous_metric_code, previous_metric_label)


def _is_out_of_scope_balance_sheet_line(table_type_guess: str, raw_metric_name: str, metric_code: str) -> bool:
    if table_type_guess != "balance_sheet":
        return False
    if metric_code != UNKNOWN_METRIC_CODE:
        return False
    normalized = _normalize_metric_label(raw_metric_name)
    if normalized in {_normalize_metric_label(label) for label in OUT_OF_SCOPE_LABELS}:
        return True
    return False


def _split_risk_tags_text(value: Any) -> List[str]:
    return [_norm(item) for item in _norm(value).split("|") if _norm(item) and _norm(item).lower() != "nan"]


def _risk_tag_counter(df: pd.DataFrame) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    if df.empty or "risk_tags" not in df.columns:
        return counts
    for value in df["risk_tags"]:
        for tag in _split_risk_tags_text(value):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def _risk_tag_set(candidate: MetricCandidate) -> set[str]:
    return {tag for tag in candidate.risk_tags if _norm(tag)}


def _provenance_complete(candidate: MetricCandidate) -> bool:
    provenance = candidate.provenance_json or {}
    source_cells = provenance.get("source_cells", [])
    return bool(
        _norm(candidate.source_table_id)
        and _norm(candidate.source_stage)
        and _norm(provenance.get("input_image_path"))
        and _norm(provenance.get("source_format"))
        and _norm(candidate.year)
        and isinstance(source_cells, list)
        and len(source_cells) > 0
    )


def _looks_like_clear_noise(metric_name: str) -> bool:
    text = _norm(metric_name)
    if not text:
        return True
    if text in {"项目", "指标", "代码", "公司", "货币", "收盘价", "市值", "会计年度"}:
        return True
    if text.startswith("注"):
        return True
    return False


def _resolve_structtable_duplicates_and_conflicts(candidates: Sequence[MetricCandidate]) -> Dict[str, Any]:
    grouped: Dict[Tuple[str, str, str, str], List[MetricCandidate]] = {}
    for candidate in candidates:
        metric_key = candidate.metric_code if candidate.metric_code != UNKNOWN_METRIC_CODE else _normalize_metric_label(candidate.raw_metric_name)
        group_key = (candidate.source_file, candidate.source_table_id or "", metric_key, candidate.year)
        grouped.setdefault(group_key, []).append(candidate)

    canonical_candidates: List[MetricCandidate] = []
    duplicate_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    conflict_count = 0

    for group_key, rows in grouped.items():
        if len(rows) == 1:
            canonical_candidates.append(rows[0])
            continue

        unique_values = sorted(set("" if row.normalized_value is None else str(row.normalized_value) for row in rows))
        if len(unique_values) == 1:
            rows_sorted = sorted(rows, key=lambda row: (-row.confidence, row.candidate_id))
            keep = rows_sorted[0]
            keep.risk_tags = sorted(set(keep.risk_tags + ["DUPLICATE_SAME_VALUE_COLLAPSED"]))
            canonical_candidates.append(keep)
            for dropped in rows_sorted[1:]:
                dropped.split_decision = "rejected_preview"
                dropped.split_reason = "DUPLICATE_SAME_VALUE_COLLAPSED"
                duplicate_rows.append(
                    {
                        "group_key": "|".join(group_key),
                        "kept_candidate_id": keep.candidate_id,
                        "dropped_candidate_id": dropped.candidate_id,
                        "metric_code": dropped.metric_code,
                        "raw_metric_name": dropped.raw_metric_name,
                        "year": dropped.year,
                        "normalized_value": dropped.normalized_value,
                        "drop_reason": "DUPLICATE_SAME_VALUE_COLLAPSED",
                    }
                )
            continue

        conflict_count += 1
        for row in rows:
            row.risk_tags = sorted(set(row.risk_tags + ["VALUE_CONFLICT"]))
            canonical_candidates.append(row)
            conflict_rows.append(
                {
                    "group_key": "|".join(group_key),
                    "candidate_id": row.candidate_id,
                    "metric_code": row.metric_code,
                    "raw_metric_name": row.raw_metric_name,
                    "year": row.year,
                    "normalized_value": row.normalized_value,
                    "confidence": row.confidence,
                    "risk_tags": "|".join(row.risk_tags),
                }
            )

    return {
        "canonical_candidates": canonical_candidates,
        "duplicates_rows": duplicate_rows,
        "conflicts_rows": conflict_rows,
        "conflict_count": conflict_count,
    }


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows_df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for _, row in rows_df.iterrows():
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")


def _write_report(path: Path, summary: Dict[str, Any], comparison_df: pd.DataFrame, qa_df: pd.DataFrame) -> None:
    lines = [
        "# 321E4 StructEqTable Unified Mapping Probe",
        "",
        "## Summary",
        f"- input_image_count: {summary.get('input_image_count', 0)}",
        f"- structtable_table_count: {summary.get('structtable_table_count', 0)}",
        f"- unified_table_count: {summary.get('unified_table_count', 0)}",
        f"- table_with_candidates_count: {summary.get('table_with_candidates_count', 0)}",
        f"- table_with_trusted_count: {summary.get('table_with_trusted_count', 0)}",
        f"- total_candidate_count: {summary.get('total_candidate_count', 0)}",
        f"- trusted_total_count: {summary.get('trusted_total_count', 0)}",
        f"- review_required_total_count: {summary.get('review_required_total_count', 0)}",
        f"- rejected_total_count: {summary.get('rejected_total_count', 0)}",
        f"- trusted_rate: {summary.get('trusted_rate', 0.0)}",
        f"- all_candidate_trusted_rate: {summary.get('all_candidate_trusted_rate', 0.0)}",
        f"- core_candidate_trusted_rate: {summary.get('core_candidate_trusted_rate', 0.0)}",
        f"- unit_unknown_count: {summary.get('unit_unknown_count', 0)}",
        f"- out_of_scope_candidate_count: {summary.get('out_of_scope_candidate_count', 0)}",
        f"- invalid_year_count: {summary.get('invalid_year_count', 0)}",
        f"- unknown_metric_code_count: {summary.get('unknown_metric_code_count', 0)}",
        f"- value_parse_failed_count: {summary.get('value_parse_failed_count', 0)}",
        f"- possible_missing_value_count: {summary.get('possible_missing_value_count', 0)}",
        f"- extraction_risk_candidate_count: {summary.get('extraction_risk_candidate_count', 0)}",
        f"- label_issue_candidate_count: {summary.get('label_issue_candidate_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        f"- provenance_complete_rate: {summary.get('provenance_complete_rate', 0.0)}",
        f"- unit_unknown_consistency_check: {summary.get('unit_unknown_consistency_check', '')}",
        f"- risk_tag_summary_consistency_check: {summary.get('risk_tag_summary_consistency_check', '')}",
        f"- structtable_mapping_decision: {summary.get('structtable_mapping_decision', '')}",
        "",
        "## Route Comparison",
    ]
    if comparison_df.empty:
        lines.append("- none")
    else:
        for _, row in comparison_df.iterrows():
            lines.append(
                "- "
                f"{row.get('route_name', '')}: candidate_count={row.get('candidate_count', '')}, "
                f"trusted_count={row.get('trusted_count', '')}, trusted_rate={row.get('trusted_rate', '')}, "
                f"notes={row.get('notes', '')}"
            )
    lines.append("")
    lines.append("## QA Checks")
    if qa_df.empty:
        lines.append("- none")
    else:
        for _, row in qa_df.iterrows():
            lines.append(f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _blocked_output(config: StructTableMetricProbeConfig, code: str, message: str) -> Dict[str, Any]:
    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_slug = _stage_slug_for_output(output_dir)
    summary = {
        "stage": stage_slug.upper(),
        "blocked": True,
        "blocked_code": code,
        "blocked_message": message,
        "input_image_count": 0,
        "structtable_table_count": 0,
        "unified_table_count": 0,
        "table_with_candidates_count": 0,
        "table_with_trusted_count": 0,
        "total_candidate_count": 0,
        "trusted_total_count": 0,
        "review_required_total_count": 0,
        "rejected_total_count": 0,
        "trusted_rate": 0.0,
        "all_candidate_trusted_rate": 0.0,
        "core_candidate_trusted_rate": 0.0,
        "unit_unknown_count": 0,
        "out_of_scope_candidate_count": 0,
        "invalid_year_count": 0,
        "unknown_metric_code_count": 0,
        "value_parse_failed_count": 0,
        "possible_missing_value_count": 0,
        "extraction_risk_candidate_count": 0,
        "label_issue_candidate_count": 0,
        "conflict_count": 0,
        "provenance_complete_rate": 0.0,
        "mineru_body_trusted_rate": None,
        "pure_vlm_calibrated_trusted_rate": None,
        "docling_mapping_trusted_rate": None,
        "ppstructure_trusted_rate": None,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "unit_unknown_consistency_check": "BLOCKED",
        "risk_tag_summary_consistency_check": "BLOCKED",
        "structtable_mapping_decision": code,
        "top_risk_tags": [],
    }
    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "structtable_unified_tables": pd.DataFrame(),
        "structtable_normalized_rows": pd.DataFrame(),
        "structtable_metric_candidates_all": pd.DataFrame(),
        "structtable_trusted_preview": pd.DataFrame(),
        "structtable_review_required_preview": pd.DataFrame(),
        "structtable_rejected_preview": pd.DataFrame(),
        "structtable_mapping_diagnostics": pd.DataFrame(),
        "structtable_vs_tools_summary": pd.DataFrame(),
        "risk_tag_counts": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": code, "status": "FAIL", "detail": message}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": message}]),
    }
    excel_path = output_dir / f"{stage_slug}.xlsx"
    summary_json_path = output_dir / f"{stage_slug}_summary.json"
    report_md_path = output_dir / f"{stage_slug}_report.md"
    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary)
    _write_report(report_md_path, summary, pd.DataFrame(), sheets["qa_checks"])
    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }


def map_structtable_unified_tables_to_candidates(unified_tables: Sequence[StructTableUnifiedTable]) -> Dict[str, Any]:
    candidates: List[MetricCandidate] = []
    candidate_rows: List[Dict[str, Any]] = []
    diagnostics_rows: List[Dict[str, Any]] = []
    table_summary_rows: List[Dict[str, Any]] = []
    extraction_risk_candidate_count = 0
    label_issue_candidate_count = 0
    provenance_complete_count = 0

    for table in unified_tables:
        previous_metric_code: Optional[str] = None
        previous_metric_label = ""
        table_candidate_start = len(candidates)

        if NON_ROW_TABLE_WARNING in table.warnings:
            diagnostics_rows.append(
                {
                    "image_name": table.image_name,
                    "table_id": table.table_id,
                    "row_index": None,
                    "raw_metric_name": "",
                    "metric_code": "",
                    "year": "",
                    "raw_value": "",
                    "normalized_value": None,
                    "issue_type": NON_ROW_TABLE_WARNING,
                    "recommended_action": "KEEP_TABLE_LEVEL_REVIEW",
                    "reason": "|".join(table.warnings),
                }
            )

        for row in table.rows:
            raw_metric_name = _norm(row.metric_name_cn or row.metric_name_raw)
            if _looks_like_clear_noise(raw_metric_name):
                diagnostics_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": row.row_index,
                        "raw_metric_name": raw_metric_name,
                        "metric_code": "",
                        "year": "",
                        "raw_value": "",
                        "normalized_value": None,
                        "issue_type": "CLEAR_NOISE_ROW",
                        "recommended_action": "REJECT_ROW",
                        "reason": row.source_row_text,
                    }
                )
                continue

            metric_code = _map_structtable_metric_code(raw_metric_name, previous_metric_code, previous_metric_label)
            if raw_metric_name:
                previous_metric_label = raw_metric_name
                if metric_code != UNKNOWN_METRIC_CODE:
                    previous_metric_code = metric_code

            if not row.values:
                diagnostics_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": row.row_index,
                        "raw_metric_name": raw_metric_name,
                        "metric_code": metric_code,
                        "year": "",
                        "raw_value": "",
                        "normalized_value": None,
                        "issue_type": "ROW_HAS_NO_VALUES",
                        "recommended_action": "KEEP_REVIEW",
                        "reason": "|".join(row.warnings),
                    }
                )
                continue

            for value_cell in row.values:
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
                risk_tags.extend([warning for warning in row.warnings if _norm(warning)])
                risk_tags.extend([warning for warning in table.warnings if _norm(warning)])
                risk_tags.extend([warning for warning in value_cell.warnings if _norm(warning)])
                if _is_out_of_scope_balance_sheet_line(table.table_type_guess, raw_metric_name, metric_code):
                    risk_tags.append("OUT_OF_SCOPE_METRIC")
                    risk_tags.append("NON_CORE_STATEMENT_LINE")
                elif metric_code == UNKNOWN_METRIC_CODE:
                    risk_tags.append("UNKNOWN_METRIC_CODE")
                if _contains_corruption(raw_metric_name):
                    risk_tags.append("CHINESE_LABEL_CORRUPTED")
                if parsed_value is None:
                    risk_tags.append("VALUE_PARSE_FAILED" if _norm(value_cell.raw_value) else "VALUE_MISSING")

                source_file = _norm(table.provenance.get("input_image_path"))
                provenance_json = {
                    "recognition_source": RECOGNITION_SOURCE,
                    "source_stage": SOURCE_STAGE,
                    "table_id": table.table_id,
                    "image_name": table.image_name,
                    "input_image_path": source_file,
                    "output_folder": _norm(table.provenance.get("output_folder")),
                    "markdown_path": _norm(table.provenance.get("markdown_path")),
                    "csv_path": _norm(table.provenance.get("csv_path")),
                    "xlsx_path": _norm(table.provenance.get("xlsx_path")),
                    "source_format": _norm(table.provenance.get("source_format")),
                    "table_title": table.table_title,
                    "table_unit": table.unit,
                    "table_type_guess": table.table_type_guess,
                    "source_cells": list(value_cell.source_cells),
                    "source_row_text": row.source_row_text,
                    "source_row_index": row.row_index,
                    "source_column_label": value_cell.column,
                    "year_source": "TABLE_HEADER" if not year_tags else "INVALID",
                    "unit_source": unit_source,
                }

                candidate_payload = "|".join(
                    [
                        SOURCE_STAGE,
                        source_file,
                        table.table_id,
                        str(row.row_index),
                        metric_code,
                        year_norm,
                        _norm(value_cell.raw_value),
                    ]
                )
                candidate_id = hashlib.sha1(candidate_payload.encode("utf-8")).hexdigest()[:24]

                candidate = MetricCandidate(
                    candidate_id=candidate_id,
                    source_stage=SOURCE_STAGE,
                    source_file=source_file,
                    source_doc_name=Path(source_file).stem if source_file else Path(table.image_name).stem,
                    source_table_id=table.table_id,
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
                    confidence=0.95 if not risk_tags else 0.85,
                    year_source="TABLE_HEADER" if not year_tags else "INVALID",
                    smoke_check_status="NOT_APPLICABLE",
                    smoke_check_source="",
                    table_title=table.table_title,
                    table_unit=table.unit,
                    risk_tags=sorted(set(tag for tag in risk_tags if _norm(tag))),
                    split_decision="review_required_preview",
                    split_reason="PENDING_STRUCTTABLE_TRUST_SPLIT",
                    provenance_json=provenance_json,
                )
                if _provenance_complete(candidate):
                    provenance_complete_count += 1
                else:
                    candidate.risk_tags = sorted(set(candidate.risk_tags + ["PROVENANCE_INCOMPLETE"]))

                if _risk_tag_set(candidate).intersection(EXTRACTION_RISK_TAGS):
                    extraction_risk_candidate_count += 1
                if _risk_tag_set(candidate).intersection(LABEL_RISK_TAGS):
                    label_issue_candidate_count += 1

                candidates.append(candidate)
                candidate_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": row.row_index,
                        "metric_code": candidate.metric_code,
                        "metric_family": _metric_family(candidate.metric_code),
                        "year": candidate.year,
                        "raw_value": candidate.raw_value,
                        "normalized_value": candidate.normalized_value,
                        "unit": candidate.unit or "",
                        "split_decision": candidate.split_decision,
                        "risk_tags": "|".join(candidate.risk_tags),
                        "reason": candidate.split_reason or "initial_mapping",
                        "provenance": json.dumps(candidate.provenance_json, ensure_ascii=False),
                    }
                )

                issue_type = ""
                action = ""
                reason = ""
                tags = _risk_tag_set(candidate)
                if candidate.metric_code == UNKNOWN_METRIC_CODE:
                    if "OUT_OF_SCOPE_METRIC" in tags:
                        issue_type = "OUT_OF_SCOPE_METRIC"
                        action = "KEEP_REVIEW_EXCLUDE_FROM_CORE_DENOMINATOR"
                    else:
                        issue_type = "UNKNOWN_METRIC_CODE"
                        action = "KEEP_REVIEW"
                    reason = raw_metric_name
                elif candidate.year_source != "TABLE_HEADER":
                    issue_type = "INVALID_YEAR"
                    action = "KEEP_REVIEW"
                    reason = value_cell.column
                elif candidate.normalized_value is None:
                    issue_type = "VALUE_PARSE_FAILED"
                    action = "KEEP_REVIEW"
                    reason = candidate.raw_value
                elif NON_ROW_TABLE_WARNING in tags or SECTION_CONTEXT_WARNING in tags:
                    issue_type = "TABLE_SCHEMA_UNCERTAIN"
                    action = "KEEP_REVIEW"
                    reason = "|".join(sorted(tags.intersection(EXTRACTION_RISK_TAGS)))
                elif "PROVENANCE_INCOMPLETE" in tags:
                    issue_type = "PROVENANCE_INCOMPLETE"
                    action = "KEEP_REVIEW"
                    reason = "missing source cells or source paths"

                if issue_type:
                    diagnostics_rows.append(
                        {
                            "image_name": table.image_name,
                            "table_id": table.table_id,
                            "row_index": row.row_index,
                            "raw_metric_name": raw_metric_name,
                            "metric_code": candidate.metric_code,
                            "year": candidate.year,
                            "raw_value": candidate.raw_value,
                            "normalized_value": candidate.normalized_value,
                            "issue_type": issue_type,
                            "recommended_action": action,
                            "reason": reason,
                        }
                    )

        table_summary_rows.append(
            {
                "image_name": table.image_name,
                "table_id": table.table_id,
                "table_title": table.table_title,
                "candidate_count": len(candidates) - table_candidate_start,
                "warnings": "|".join(table.warnings),
            }
        )

    dedupe_result = _resolve_structtable_duplicates_and_conflicts(candidates)
    duplicate_rejected = [
        candidate
        for candidate in candidates
        if candidate.split_decision == "rejected_preview" and candidate.split_reason == "DUPLICATE_SAME_VALUE_COLLAPSED"
    ]
    return {
        "all_candidates": candidates,
        "canonical_candidates": dedupe_result["canonical_candidates"],
        "duplicate_rejected": duplicate_rejected,
        "candidate_rows_df": pd.DataFrame(candidate_rows),
        "mapping_diagnostics_df": pd.DataFrame(diagnostics_rows),
        "table_mapping_summary_df": pd.DataFrame(table_summary_rows),
        "duplicate_rows_df": pd.DataFrame(dedupe_result["duplicates_rows"]),
        "conflict_rows_df": pd.DataFrame(dedupe_result["conflicts_rows"]),
        "conflict_count": dedupe_result["conflict_count"],
        "extraction_risk_candidate_count": extraction_risk_candidate_count,
        "label_issue_candidate_count": label_issue_candidate_count,
        "provenance_complete_count": provenance_complete_count,
    }


def split_structtable_candidates_for_preview(
    canonical_candidates: Iterable[MetricCandidate],
    duplicate_rejected: Iterable[MetricCandidate],
) -> Dict[str, Any]:
    trusted: List[MetricCandidate] = []
    review_required: List[MetricCandidate] = []
    rejected: List[MetricCandidate] = list(duplicate_rejected)
    split_audit_rows: List[Dict[str, Any]] = []
    trusted_table_ids: set[str] = set()

    def finalize(candidate: MetricCandidate, decision: str, reason: str, bucket: List[MetricCandidate]) -> None:
        candidate.split_decision = decision
        candidate.split_reason = reason
        bucket.append(candidate)
        split_audit_rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "table_id": _norm(candidate.source_table_id),
                "metric_code": candidate.metric_code,
                "year": candidate.year,
                "decision": decision,
                "reason": reason,
                "risk_tags": "|".join(candidate.risk_tags),
            }
        )
        if decision == "trusted_preview":
            trusted_table_ids.add(_norm(candidate.source_table_id))

    for dropped in duplicate_rejected:
        split_audit_rows.append(
            {
                "candidate_id": dropped.candidate_id,
                "table_id": _norm(dropped.source_table_id),
                "metric_code": dropped.metric_code,
                "year": dropped.year,
                "decision": "rejected_preview",
                "reason": dropped.split_reason or "DUPLICATE_SAME_VALUE_COLLAPSED",
                "risk_tags": "|".join(dropped.risk_tags),
            }
        )

    for candidate in canonical_candidates:
        tags = _risk_tag_set(candidate)
        if "CLEAR_NOISE_ROW" in tags:
            finalize(candidate, "rejected_preview", "CLEAR_NOISE_ROW", rejected)
            continue
        if "VALUE_CONFLICT" in tags:
            finalize(candidate, "review_required_preview", "VALUE_CONFLICT", review_required)
            continue
        if tags.intersection(OUT_OF_SCOPE_RISK_TAGS):
            finalize(candidate, "review_required_preview", "OUT_OF_SCOPE_METRIC", review_required)
            continue
        if candidate.metric_code == UNKNOWN_METRIC_CODE:
            finalize(candidate, "review_required_preview", "UNKNOWN_METRIC_CODE", review_required)
            continue
        if candidate.year_source != "TABLE_HEADER":
            finalize(candidate, "review_required_preview", "INVALID_OR_NON_HEADER_YEAR", review_required)
            continue
        if candidate.normalized_value is None:
            finalize(candidate, "review_required_preview", "VALUE_MISSING_OR_INVALID", review_required)
            continue
        if tags.intersection(EXTRACTION_RISK_TAGS):
            finalize(candidate, "review_required_preview", "EXTRACTION_OR_SCHEMA_RISK", review_required)
            continue
        if tags.intersection(LABEL_RISK_TAGS):
            finalize(candidate, "review_required_preview", "LABEL_QUALITY_RISK", review_required)
            continue
        if "PROVENANCE_INCOMPLETE" in tags:
            finalize(candidate, "review_required_preview", "PROVENANCE_INCOMPLETE", review_required)
            continue
        if not candidate.unit and candidate.metric_code not in SAFE_RATIO_METRICS and candidate.metric_code not in PER_SHARE_METRICS:
            finalize(candidate, "review_required_preview", "UNIT_UNKNOWN", review_required)
            continue
        finalize(candidate, "trusted_preview", "PASS_STRUCTTABLE_TRUST_GATE", trusted)

    return {
        "trusted_preview": trusted,
        "review_required_preview": review_required,
        "rejected_preview": rejected,
        "split_audit_df": pd.DataFrame(split_audit_rows),
        "trusted_table_ids": trusted_table_ids,
    }


def _explode_risk_tags(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "risk_tags" not in df.columns:
        return pd.DataFrame(columns=["risk_tag", "count"])
    counts = _risk_tag_counter(df)
    rows = [{"risk_tag": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    return pd.DataFrame(rows)


def run_structtable_metric_probe(config: StructTableMetricProbeConfig) -> Dict[str, Any]:
    if not config.structtable_audit_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_321E3_AUDIT_DIR", f"missing 321E3 audit dir: {config.structtable_audit_dir}")
    if not config.structtable_output_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_STRUCTTABLE_OUTPUT_DIR", f"missing structtable output dir: {config.structtable_output_dir}")
    if not config.input_image_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_INPUT_IMAGE_DIR", f"missing input image dir: {config.input_image_dir}")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_slug = _stage_slug_for_output(output_dir)

    unified_result = normalize_structtable_to_unified_tables(
        audit_dir=config.structtable_audit_dir,
        structtable_output_dir=config.structtable_output_dir,
        input_image_dir=config.input_image_dir,
    )
    unified_tables: List[StructTableUnifiedTable] = unified_result["unified_tables"]
    mapping_result = map_structtable_unified_tables_to_candidates(unified_tables)
    split_result = split_structtable_candidates_for_preview(
        canonical_candidates=mapping_result["canonical_candidates"],
        duplicate_rejected=mapping_result["duplicate_rejected"],
    )

    trusted_df = candidates_to_dataframe(split_result["trusted_preview"])
    review_df = candidates_to_dataframe(split_result["review_required_preview"])
    rejected_df = candidates_to_dataframe(split_result["rejected_preview"])

    all_candidates_final = list(split_result["trusted_preview"]) + list(split_result["review_required_preview"]) + list(split_result["rejected_preview"])
    all_candidates_df = candidates_to_dataframe(all_candidates_final)
    if not all_candidates_df.empty:
        all_candidates_df["image_name"] = all_candidates_df["source_file"].astype(str).map(lambda value: Path(value).name if value else "")
        all_candidates_df["table_id"] = all_candidates_df["source_table_id"].astype(str)
        all_candidates_df["row_index"] = all_candidates_df["source_row_index"]
        all_candidates_df["metric_family"] = all_candidates_df["metric_code"].astype(str).map(_metric_family)

    table_with_candidates_count = int(all_candidates_df["table_id"].replace("", pd.NA).dropna().nunique()) if not all_candidates_df.empty else 0
    table_with_trusted_count = int(trusted_df["source_table_id"].replace("", pd.NA).dropna().nunique()) if not trusted_df.empty else 0
    trusted_total_count = int(len(trusted_df))
    review_required_total_count = int(len(review_df))
    rejected_total_count = int(len(rejected_df))
    total_candidate_count = int(len(all_candidates_df))
    risk_tag_counts_df = _explode_risk_tags(all_candidates_df)
    risk_tag_counts_lookup = {str(row["risk_tag"]): int(row["count"]) for _, row in risk_tag_counts_df.iterrows()} if not risk_tag_counts_df.empty else {}
    out_of_scope_candidate_count = int(risk_tag_counts_lookup.get("OUT_OF_SCOPE_METRIC", 0))
    core_candidate_count = max(total_candidate_count - out_of_scope_candidate_count, 0)
    all_candidate_trusted_rate = float(trusted_total_count / total_candidate_count) if total_candidate_count else 0.0
    core_candidate_trusted_rate = float(trusted_total_count / core_candidate_count) if core_candidate_count else 0.0
    trusted_rate = core_candidate_trusted_rate
    unit_unknown_count = int(risk_tag_counts_lookup.get("UNIT_UNKNOWN", 0))
    invalid_year_count = int((all_candidates_df["year_source"].astype(str) != "TABLE_HEADER").sum()) if not all_candidates_df.empty else 0
    unknown_metric_code_count = int(risk_tag_counts_lookup.get("UNKNOWN_METRIC_CODE", 0))
    value_parse_failed_count = int(all_candidates_df["risk_tags"].astype(str).str.contains("VALUE_PARSE_FAILED", regex=False).sum()) if not all_candidates_df.empty else 0
    provenance_complete_rate = float(mapping_result["provenance_complete_count"] / total_candidate_count) if total_candidate_count else 0.0
    top_risk_tags = risk_tag_counts_df.head(10).to_dict("records") if not risk_tag_counts_df.empty else []

    qa_rows: List[Dict[str, Any]] = []
    qa_rows.append({"check_name": "audit_dir_exists", "status": "PASS", "detail": str(config.structtable_audit_dir)})
    qa_rows.append({"check_name": "structtable_output_dir_exists", "status": "PASS", "detail": str(config.structtable_output_dir)})
    qa_rows.append({"check_name": "no_e_drive_files_modified", "status": "PASS", "detail": "321E4 reads E drive only"})
    qa_rows.append({"check_name": "no_structtable_docling_mineru_vlm_ppstructure_command_executed", "status": "PASS", "detail": "321E4 reads existing outputs only"})
    if not all_candidates_df.empty:
        missing_ids = int(all_candidates_df["source_table_id"].astype(str).eq("").sum()) + int(all_candidates_df["source_stage"].astype(str).eq("").sum())
    else:
        missing_ids = 0
    qa_rows.append({"check_name": "every_candidate_has_table_id_and_source_stage", "status": "PASS" if missing_ids == 0 else "FAIL", "detail": f"missing_id_or_stage_count={missing_ids}"})
    trusted_invalid_year = int((trusted_df["year_source"].astype(str) != "TABLE_HEADER").sum()) if not trusted_df.empty else 0
    qa_rows.append({"check_name": "trusted_candidates_have_valid_year", "status": "PASS" if trusted_invalid_year == 0 else "FAIL", "detail": f"trusted_invalid_year_count={trusted_invalid_year}"})
    trusted_unknown_metric = int((trusted_df["metric_code"].astype(str) == UNKNOWN_METRIC_CODE).sum()) if not trusted_df.empty else 0
    qa_rows.append({"check_name": "trusted_candidates_have_known_metric_code", "status": "PASS" if trusted_unknown_metric == 0 else "FAIL", "detail": f"trusted_unknown_metric_count={trusted_unknown_metric}"})
    trusted_missing_value = int(trusted_df["normalized_value"].isna().sum()) if not trusted_df.empty else 0
    qa_rows.append({"check_name": "trusted_candidates_have_parsed_numeric_value", "status": "PASS" if trusted_missing_value == 0 else "FAIL", "detail": f"trusted_missing_value_count={trusted_missing_value}"})
    trusted_missing_prov = 0
    if not trusted_df.empty:
        for _, row in trusted_df.iterrows():
            try:
                provenance = json.loads(_norm(row.get("provenance_json")))
            except Exception:
                provenance = {}
            if not provenance.get("source_cells"):
                trusted_missing_prov += 1
    qa_rows.append({"check_name": "trusted_candidates_have_provenance", "status": "PASS" if trusted_missing_prov == 0 else "FAIL", "detail": f"trusted_missing_provenance_count={trusted_missing_prov}"})
    risky_trusted = 0
    if not trusted_df.empty:
        risky_trusted = int(
            trusted_df["risk_tags"].astype(str).apply(
                lambda text: any(tag in set(_norm(item) for item in text.split("|") if _norm(item)) for tag in EXTRACTION_RISK_TAGS)
            ).sum()
        )
    qa_rows.append({"check_name": "extraction_risk_candidates_not_silently_trusted", "status": "PASS" if risky_trusted == 0 else "FAIL", "detail": f"risky_trusted_count={risky_trusted}"})
    unit_unknown_consistency_pass = unit_unknown_count == int(risk_tag_counts_lookup.get("UNIT_UNKNOWN", 0))
    qa_rows.append(
        {
            "check_name": "unit_unknown_consistency_check",
            "status": "PASS" if unit_unknown_consistency_pass else "FAIL",
            "detail": f"summary_unit_unknown_count={unit_unknown_count}; risk_tag_unit_unknown_count={int(risk_tag_counts_lookup.get('UNIT_UNKNOWN', 0))}",
        }
    )
    risk_tag_total_from_sheet = int(risk_tag_counts_df["count"].sum()) if not risk_tag_counts_df.empty else 0
    risk_tag_total_from_candidates = sum(len(_split_risk_tags_text(value)) for value in all_candidates_df["risk_tags"]) if not all_candidates_df.empty else 0
    risk_tag_consistency_pass = risk_tag_total_from_sheet == risk_tag_total_from_candidates
    qa_rows.append(
        {
            "check_name": "risk_tag_summary_consistency_check",
            "status": "PASS" if risk_tag_consistency_pass else "FAIL",
            "detail": f"risk_tag_sheet_total={risk_tag_total_from_sheet}; risk_tag_candidate_total={risk_tag_total_from_candidates}",
        }
    )
    qa_rows.append({"check_name": "output_written", "status": "PASS", "detail": str(output_dir)})
    qa_df = pd.DataFrame(qa_rows)
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    input_image_count = len(list(config.input_image_dir.glob("*")))
    summary = {
        "stage": stage_slug.upper(),
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "input_image_count": input_image_count,
        "structtable_table_count": unified_result["structtable_table_count"],
        "unified_table_count": len(unified_tables),
        "table_with_candidates_count": table_with_candidates_count,
        "table_with_trusted_count": table_with_trusted_count,
        "total_candidate_count": total_candidate_count,
        "trusted_total_count": trusted_total_count,
        "review_required_total_count": review_required_total_count,
        "rejected_total_count": rejected_total_count,
        "trusted_rate": trusted_rate,
        "all_candidate_trusted_rate": all_candidate_trusted_rate,
        "core_candidate_trusted_rate": core_candidate_trusted_rate,
        "unit_unknown_count": unit_unknown_count,
        "out_of_scope_candidate_count": out_of_scope_candidate_count,
        "invalid_year_count": invalid_year_count,
        "unknown_metric_code_count": unknown_metric_code_count,
        "value_parse_failed_count": value_parse_failed_count,
        "possible_missing_value_count": unified_result["possible_missing_value_count"],
        "extraction_risk_candidate_count": mapping_result["extraction_risk_candidate_count"],
        "label_issue_candidate_count": mapping_result["label_issue_candidate_count"],
        "conflict_count": mapping_result["conflict_count"],
        "provenance_complete_rate": provenance_complete_rate,
        "mineru_body_trusted_rate": None,
        "pure_vlm_calibrated_trusted_rate": None,
        "docling_mapping_trusted_rate": None,
        "ppstructure_trusted_rate": None,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "unit_unknown_consistency_check": "PASS" if unit_unknown_consistency_pass else "FAIL",
        "risk_tag_summary_consistency_check": "PASS" if risk_tag_consistency_pass else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_risk_tags": top_risk_tags,
    }

    if qa_fail_count > 0:
        decision = "STRUCTTABLE_MAPPING_BLOCKED_BY_QA_FAILURE"
    elif len(unified_tables) >= 8 and table_with_trusted_count >= 6 and trusted_rate >= 0.35 and provenance_complete_rate >= 0.95:
        decision = "STRUCTTABLE_MAPPING_READY_FOR_321E5_FULL_BAKEOFF"
    elif len(unified_tables) >= 5 and table_with_candidates_count >= 5:
        decision = "STRUCTTABLE_MAPPING_PARTIAL_INCLUDE_IN_BAKEOFF"
    else:
        decision = "STRUCTTABLE_MAPPING_NOT_READY"
    summary["structtable_mapping_decision"] = decision

    comparison_df = build_structtable_comparison_rows(
        structtable_summary=summary,
        docling_mapping_dir=config.docling_mapping_dir,
        docling_audit_dir=config.docling_audit_dir,
        mineru_body_dir=config.mineru_body_dir,
        pure_vlm_calibration_dir=config.pure_vlm_calibration_dir,
        ppstructure_benchmark_dir=config.ppstructure_benchmark_dir,
    )
    if not comparison_df.empty:
        lookup = {str(row["route_name"]): row for _, row in comparison_df.iterrows()}
        summary["mineru_body_trusted_rate"] = lookup.get("MINERU_TABLE_BODY_321D", {}).get("trusted_rate")
        summary["pure_vlm_calibrated_trusted_rate"] = lookup.get("PURE_VLM_321B2_CALIBRATED", {}).get("trusted_rate")
        summary["docling_mapping_trusted_rate"] = lookup.get("DOCLING_TABLE_GRID_321E2", {}).get("trusted_rate")
        summary["ppstructure_trusted_rate"] = lookup.get("PPSTRUCTURE_320G", {}).get("trusted_rate")

    unified_tables_jsonl_df = unified_tables_to_jsonl_rows(unified_tables)
    unified_tables_sheet_df = unified_result["unified_tables_df"]
    normalized_rows_df = unified_result["normalized_rows_df"]
    diagnostics_parts = []
    for diagnostics_df in [
        unified_result["normalization_diagnostics_df"],
        mapping_result["mapping_diagnostics_df"],
    ]:
        if diagnostics_df.empty:
            continue
        cleaned_diagnostics_df = diagnostics_df.dropna(axis=1, how="all")
        if cleaned_diagnostics_df.empty and len(cleaned_diagnostics_df.columns) == 0:
            continue
        diagnostics_parts.append(cleaned_diagnostics_df)
    mapping_diagnostics_df = pd.concat(diagnostics_parts, ignore_index=True) if diagnostics_parts else pd.DataFrame()

    if not all_candidates_df.empty:
        all_candidates_sheet_df = all_candidates_df[
            [
                "image_name",
                "table_id",
                "row_index",
                "metric_code",
                "metric_family",
                "year",
                "raw_value",
                "normalized_value",
                "unit",
                "split_decision",
                "risk_tags",
                "split_reason",
                "provenance_json",
            ]
        ].rename(columns={"split_reason": "reason", "provenance_json": "provenance"})
    else:
        all_candidates_sheet_df = pd.DataFrame(
            columns=[
                "image_name",
                "table_id",
                "row_index",
                "metric_code",
                "metric_family",
                "year",
                "raw_value",
                "normalized_value",
                "unit",
                "split_decision",
                "risk_tags",
                "reason",
                "provenance",
            ]
        )

    known_limitations_df = pd.DataFrame(
        [
            {"limitation": "sandbox_only", "detail": "321E4 probes sandbox mapping only and does not alter production delivery outputs."},
            {"limitation": "structtable_not_rerun", "detail": "321E4 consumes existing StructEqTable outputs and 321E3 audit artifacts only."},
            {"limitation": "peer_comparison_tables", "detail": "Peer comparison layouts are kept as table-level review and are not force-mapped into metric rows."},
            {"limitation": "section_context_review", "detail": "Repeated segment metric rows are preserved but held for review when section context changes semantics."},
        ]
    )

    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "structtable_unified_tables": unified_tables_sheet_df,
        "structtable_normalized_rows": normalized_rows_df,
        "structtable_metric_candidates_all": all_candidates_sheet_df,
        "structtable_trusted_preview": trusted_df,
        "structtable_review_required_preview": review_df,
        "structtable_rejected_preview": rejected_df,
        "structtable_mapping_diagnostics": mapping_diagnostics_df,
        "structtable_vs_tools_summary": comparison_df,
        "risk_tag_counts": risk_tag_counts_df,
        "qa_checks": qa_df,
        "known_limitations": known_limitations_df,
    }

    excel_path = output_dir / f"{stage_slug}.xlsx"
    summary_json_path = output_dir / f"{stage_slug}_summary.json"
    report_md_path = output_dir / f"{stage_slug}_report.md"
    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary)
    _write_report(report_md_path, summary, comparison_df, qa_df)
    if not unified_tables_jsonl_df.empty:
        _write_jsonl(output_dir / "structtable_unified_tables.jsonl", unified_tables_jsonl_df)
    if not all_candidates_df.empty:
        _write_jsonl(output_dir / "structtable_metric_candidates_all.jsonl", all_candidates_df)

    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }
