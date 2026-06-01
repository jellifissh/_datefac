from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def _count_risk_tags_from_jsonl(path: Path, risk_tag: str) -> Optional[int]:
    if not path.exists():
        return None
    count = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                tags = payload.get("risk_tags", "")
                if isinstance(tags, list):
                    tag_list = [_norm(item) for item in tags]
                else:
                    tag_list = [_norm(item) for item in _norm(tags).split("|") if _norm(item)]
                if risk_tag in tag_list:
                    count += 1
    except Exception:
        return None
    return count


def _safe_summary_row(
    route_name: str,
    sample_count: Optional[int],
    candidate_count: Optional[int],
    trusted_count: Optional[int],
    review_required_count: Optional[int],
    rejected_count: Optional[int],
    trusted_rate: Optional[float],
    unit_unknown_count: Optional[int],
    unknown_metric_count: Optional[int],
    invalid_year_count: Optional[int],
    value_parse_failed_count: Optional[int],
    possible_missing_value_count: Optional[int],
    qa_fail_count: Optional[int],
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
        "qa_fail_count": qa_fail_count,
        "notes": notes,
    }


def build_tool_comparison_rows(
    docling_summary: Dict[str, Any],
    mineru_body_dir: Optional[Path],
    pure_vlm_calibration_dir: Optional[Path],
    ppstructure_benchmark_dir: Optional[Path],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    rows.append(
        _safe_summary_row(
            route_name="DOCLING_TABLE_GRID_321E2",
            sample_count=docling_summary.get("input_image_count"),
            candidate_count=docling_summary.get("total_candidate_count"),
            trusted_count=docling_summary.get("trusted_total_count"),
            review_required_count=docling_summary.get("review_required_total_count"),
            rejected_count=docling_summary.get("rejected_total_count"),
            trusted_rate=docling_summary.get("trusted_rate"),
            unit_unknown_count=docling_summary.get("unit_unknown_count"),
            unknown_metric_count=docling_summary.get("unknown_metric_code_count"),
            invalid_year_count=docling_summary.get("invalid_year_count"),
            value_parse_failed_count=docling_summary.get("value_parse_failed_count"),
            possible_missing_value_count=docling_summary.get("possible_missing_value_count"),
            qa_fail_count=docling_summary.get("qa_fail_count"),
            notes="321E2 sandbox-only Docling unified mapping probe",
        )
    )

    if mineru_body_dir and mineru_body_dir.exists():
        summary = _read_json(mineru_body_dir / "mineru_table_body_ingestion_321d_summary.json")
        value_parse_failed = _count_risk_tags_from_jsonl(mineru_body_dir / "metric_candidates_all.jsonl", "VALUE_PARSE_FAILED")
        rows.append(
            _safe_summary_row(
                route_name="MINERU_TABLE_BODY_321D",
                sample_count=summary.get("selected_table_count", summary.get("unified_table_count")),
                candidate_count=summary.get("total_candidate_count"),
                trusted_count=summary.get("trusted_total_count"),
                review_required_count=summary.get("review_required_total_count"),
                rejected_count=summary.get("rejected_total_count"),
                trusted_rate=summary.get("trusted_rate"),
                unit_unknown_count=summary.get("unit_unknown_count"),
                unknown_metric_count=summary.get("unknown_metric_code_count"),
                invalid_year_count=summary.get("year_invalid_count"),
                value_parse_failed_count=value_parse_failed,
                possible_missing_value_count=None,
                qa_fail_count=summary.get("qa_fail_count"),
                notes="current 321D mineru table_body sandbox",
            )
        )
    else:
        rows.append(
            _safe_summary_row(
                route_name="MINERU_TABLE_BODY_321D",
                sample_count=None,
                candidate_count=None,
                trusted_count=None,
                review_required_count=None,
                rejected_count=None,
                trusted_rate=None,
                unit_unknown_count=None,
                unknown_metric_count=None,
                invalid_year_count=None,
                value_parse_failed_count=None,
                possible_missing_value_count=None,
                qa_fail_count=None,
                notes="missing optional comparison dir",
            )
        )

    if pure_vlm_calibration_dir and pure_vlm_calibration_dir.exists():
        summary = _read_json(pure_vlm_calibration_dir / "vlm_mapping_calibration_321b2_summary.json")
        value_parse_failed = _count_risk_tags_from_jsonl(pure_vlm_calibration_dir / "review_required_preview.jsonl", "VALUE_PARSE_FAILED")
        rows.append(
            _safe_summary_row(
                route_name="PURE_VLM_321B2_CALIBRATED",
                sample_count=summary.get("mapped_table_count", summary.get("vlm_folder_count")),
                candidate_count=summary.get("calibrated_total_candidate_count"),
                trusted_count=summary.get("calibrated_trusted_total_count"),
                review_required_count=summary.get("calibrated_review_required_total_count"),
                rejected_count=summary.get("rejected_total_count"),
                trusted_rate=summary.get("calibrated_trusted_rate"),
                unit_unknown_count=summary.get("unit_unknown_count"),
                unknown_metric_count=summary.get("unknown_metric_code_count"),
                invalid_year_count=summary.get("invalid_year_count"),
                value_parse_failed_count=value_parse_failed,
                possible_missing_value_count=None,
                qa_fail_count=summary.get("qa_fail_count"),
                notes="pure image-only VLM calibrated baseline",
            )
        )
    else:
        rows.append(
            _safe_summary_row(
                route_name="PURE_VLM_321B2_CALIBRATED",
                sample_count=None,
                candidate_count=None,
                trusted_count=None,
                review_required_count=None,
                rejected_count=None,
                trusted_rate=None,
                unit_unknown_count=None,
                unknown_metric_count=None,
                invalid_year_count=None,
                value_parse_failed_count=None,
                possible_missing_value_count=None,
                qa_fail_count=None,
                notes="missing optional comparison dir",
            )
        )

    if ppstructure_benchmark_dir and ppstructure_benchmark_dir.exists():
        summary = _read_json(ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json")
        value_parse_failed = _count_risk_tags_from_jsonl(ppstructure_benchmark_dir / "metric_candidates_all.jsonl", "VALUE_PARSE_FAILED")
        rows.append(
            _safe_summary_row(
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
                value_parse_failed_count=value_parse_failed,
                possible_missing_value_count=None,
                qa_fail_count=summary.get("qa_fail_count"),
                notes="row-text fallback baseline",
            )
        )
    else:
        rows.append(
            _safe_summary_row(
                route_name="PPSTRUCTURE_320G",
                sample_count=None,
                candidate_count=None,
                trusted_count=None,
                review_required_count=None,
                rejected_count=None,
                trusted_rate=None,
                unit_unknown_count=None,
                unknown_metric_count=None,
                invalid_year_count=None,
                value_parse_failed_count=None,
                possible_missing_value_count=None,
                qa_fail_count=None,
                notes="missing optional comparison dir",
            )
        )

    return pd.DataFrame(rows)
