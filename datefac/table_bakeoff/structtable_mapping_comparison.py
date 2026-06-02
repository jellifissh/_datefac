from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_row(
    route_name: str,
    sample_count: Any,
    candidate_count: Any,
    trusted_count: Any,
    review_required_count: Any,
    rejected_count: Any,
    trusted_rate: Any,
    unit_unknown_count: Any,
    unknown_metric_count: Any,
    invalid_year_count: Any,
    value_parse_failed_count: Any,
    possible_missing_value_count: Any,
    label_issue_count: Any,
    qa_fail_count: Any,
    notes: str,
) -> Dict[str, Any]:
    return {
        "route_name": route_name,
        "sample_count": sample_count,
        "candidate_count": candidate_count,
        "trusted_count": trusted_count,
        "review_required_count": review_required_count,
        "rejected_count": rejected_count,
        "trusted_rate": trusted_rate,
        "unit_unknown_count": unit_unknown_count,
        "unknown_metric_count": unknown_metric_count,
        "invalid_year_count": invalid_year_count,
        "value_parse_failed_count": value_parse_failed_count,
        "possible_missing_value_count": possible_missing_value_count,
        "label_issue_count": label_issue_count,
        "qa_fail_count": qa_fail_count,
        "notes": notes,
    }


def build_structtable_comparison_rows(
    structtable_summary: Dict[str, Any],
    docling_mapping_dir: Path | None,
    docling_audit_dir: Path | None,
    mineru_body_dir: Path | None,
    pure_vlm_calibration_dir: Path | None,
    ppstructure_benchmark_dir: Path | None,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = [
        _safe_row(
            route_name="STRUCTTABLE_INTERVL2_321E4",
            sample_count=structtable_summary.get("input_image_count"),
            candidate_count=structtable_summary.get("total_candidate_count"),
            trusted_count=structtable_summary.get("trusted_total_count"),
            review_required_count=structtable_summary.get("review_required_total_count"),
            rejected_count=structtable_summary.get("rejected_total_count"),
            trusted_rate=structtable_summary.get("trusted_rate"),
            unit_unknown_count=structtable_summary.get("unit_unknown_count"),
            unknown_metric_count=structtable_summary.get("unknown_metric_code_count"),
            invalid_year_count=structtable_summary.get("invalid_year_count"),
            value_parse_failed_count=structtable_summary.get("value_parse_failed_count"),
            possible_missing_value_count=structtable_summary.get("possible_missing_value_count"),
            label_issue_count=structtable_summary.get("label_issue_candidate_count"),
            qa_fail_count=structtable_summary.get("qa_fail_count"),
            notes="321E4 sandbox-only StructEqTable unified mapping probe",
        )
    ]

    if docling_mapping_dir and docling_mapping_dir.exists():
        summary = _read_json(docling_mapping_dir / "docling_unified_mapping_321e2_summary.json")
        rows.append(
            _safe_row(
                route_name="DOCLING_TABLE_GRID_321E2",
                sample_count=summary.get("input_image_count"),
                candidate_count=summary.get("total_candidate_count"),
                trusted_count=summary.get("trusted_total_count"),
                review_required_count=summary.get("review_required_total_count"),
                rejected_count=summary.get("rejected_total_count"),
                trusted_rate=summary.get("trusted_rate"),
                unit_unknown_count=summary.get("unit_unknown_count"),
                unknown_metric_count=summary.get("unknown_metric_code_count"),
                invalid_year_count=summary.get("invalid_year_count"),
                value_parse_failed_count=summary.get("value_parse_failed_count"),
                possible_missing_value_count=summary.get("possible_missing_value_count"),
                label_issue_count=None,
                qa_fail_count=summary.get("qa_fail_count"),
                notes="Docling 321E2 mapping baseline",
            )
        )
    else:
        rows.append(_safe_row("DOCLING_TABLE_GRID_321E2", None, None, None, None, None, None, None, None, None, None, None, None, None, "missing optional comparison dir"))

    if docling_audit_dir and docling_audit_dir.exists():
        summary = _read_json(docling_audit_dir / "docling_output_audit_321e1_summary.json")
        rows.append(
            _safe_row(
                route_name="DOCLING_AUDIT_321E1",
                sample_count=summary.get("input_image_count"),
                candidate_count=None,
                trusted_count=None,
                review_required_count=None,
                rejected_count=None,
                trusted_rate=None,
                unit_unknown_count=None,
                unknown_metric_count=None,
                invalid_year_count=summary.get("invalid_year_header_count"),
                value_parse_failed_count=None,
                possible_missing_value_count=summary.get("possible_missing_value_count"),
                label_issue_count=None,
                qa_fail_count=summary.get("qa_fail_count"),
                notes="extraction-level Docling audit reference",
            )
        )
    else:
        rows.append(_safe_row("DOCLING_AUDIT_321E1", None, None, None, None, None, None, None, None, None, None, None, None, None, "missing optional comparison dir"))

    if mineru_body_dir and mineru_body_dir.exists():
        summary = _read_json(mineru_body_dir / "mineru_table_body_ingestion_321d_summary.json")
        rows.append(
            _safe_row(
                route_name="MINERU_TABLE_BODY_321D",
                sample_count=summary.get("selected_table_count"),
                candidate_count=summary.get("total_candidate_count"),
                trusted_count=summary.get("trusted_total_count"),
                review_required_count=summary.get("review_required_total_count"),
                rejected_count=summary.get("rejected_total_count"),
                trusted_rate=summary.get("trusted_rate"),
                unit_unknown_count=summary.get("unit_unknown_count"),
                unknown_metric_count=summary.get("unknown_metric_code_count"),
                invalid_year_count=summary.get("year_invalid_count"),
                value_parse_failed_count=None,
                possible_missing_value_count=None,
                label_issue_count=None,
                qa_fail_count=summary.get("qa_fail_count"),
                notes="current MinerU body sandbox baseline",
            )
        )
    else:
        rows.append(_safe_row("MINERU_TABLE_BODY_321D", None, None, None, None, None, None, None, None, None, None, None, None, None, "missing optional comparison dir"))

    if pure_vlm_calibration_dir and pure_vlm_calibration_dir.exists():
        summary = _read_json(pure_vlm_calibration_dir / "vlm_mapping_calibration_321b2_summary.json")
        rows.append(
            _safe_row(
                route_name="PURE_VLM_321B2_CALIBRATED",
                sample_count=summary.get("vlm_folder_count"),
                candidate_count=summary.get("calibrated_total_candidate_count"),
                trusted_count=summary.get("calibrated_trusted_total_count"),
                review_required_count=summary.get("calibrated_review_required_total_count"),
                rejected_count=summary.get("rejected_total_count"),
                trusted_rate=summary.get("calibrated_trusted_rate"),
                unit_unknown_count=summary.get("unit_unknown_count"),
                unknown_metric_count=summary.get("unknown_metric_code_count"),
                invalid_year_count=summary.get("invalid_year_count"),
                value_parse_failed_count=None,
                possible_missing_value_count=None,
                label_issue_count=summary.get("corrupted_label_candidate_count"),
                qa_fail_count=summary.get("qa_fail_count"),
                notes="pure image-only VLM calibrated baseline",
            )
        )
    else:
        rows.append(_safe_row("PURE_VLM_321B2_CALIBRATED", None, None, None, None, None, None, None, None, None, None, None, None, None, "missing optional comparison dir"))

    if ppstructure_benchmark_dir and ppstructure_benchmark_dir.exists():
        summary = _read_json(ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json")
        rows.append(
            _safe_row(
                route_name="PPSTRUCTURE_320G",
                sample_count=summary.get("batch_table_count"),
                candidate_count=(summary.get("trusted_total_count", 0) or 0) + (summary.get("review_required_total_count", 0) or 0) + (summary.get("rejected_total_count", 0) or 0),
                trusted_count=summary.get("trusted_total_count"),
                review_required_count=summary.get("review_required_total_count"),
                rejected_count=summary.get("rejected_total_count"),
                trusted_rate=summary.get("trusted_rate"),
                unit_unknown_count=summary.get("unit_unknown_count"),
                unknown_metric_count=None,
                invalid_year_count=summary.get("year_inferred_count"),
                value_parse_failed_count=None,
                possible_missing_value_count=None,
                label_issue_count=None,
                qa_fail_count=summary.get("qa_fail_count"),
                notes="row-text fallback baseline",
            )
        )
    else:
        rows.append(_safe_row("PPSTRUCTURE_320G", None, None, None, None, None, None, None, None, None, None, None, None, None, "missing optional comparison dir"))

    return pd.DataFrame(rows)
