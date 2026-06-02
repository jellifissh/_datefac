from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


STRUCTTABLE_ROUTE = "STRUCTTABLE_INTERVL2_321E4B"
DOCLING_ROUTE = "DOCLING_TABLE_GRID_321E2"
MINERU_ROUTE = "MINERU_TABLE_BODY_321D"
PURE_VLM_ROUTE = "PURE_VLM_321B2_CALIBRATED"
PPSTRUCTURE_ROUTE = "PPSTRUCTURE_320G"

OUT_OF_SCOPE_RISK_TAGS = {"OUT_OF_SCOPE_METRIC", "NON_CORE_STATEMENT_LINE"}
ANALYSIS_OUT_OF_SCOPE_LABELS = {
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
SHEET_ORDER = [
    "summary",
    "route_scorecard",
    "route_rankings",
    "router_plan",
    "qa_checks",
    "known_limitations",
]


@dataclass
class FullBakeoffConfig:
    structtable_mapping_dir: Path
    structtable_audit_dir: Path
    docling_mapping_dir: Path
    docling_audit_dir: Path
    mineru_body_dir: Path
    pure_vlm_calibration_dir: Path
    ppstructure_benchmark_dir: Path
    output_dir: Path


@dataclass
class RouteArtifacts:
    route_name: str
    route_family: str
    mapping_summary_path: Path
    mapping_jsonl_paths: List[Path]
    audit_summary_path: Optional[Path] = None
    prefer_summary_unknown_metric_count: bool = True


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


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


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


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


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_jsonl(paths: Sequence[Path]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    return rows


def _split_risk_tags(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    return [_norm(item) for item in _norm(value).split("|") if _norm(item) and _norm(item).lower() != "nan"]


def _normalize_metric_label(text: Any) -> str:
    return _norm(text).replace("\u3000", "").replace(" ", "").lower()


def _candidate_table_id(row: Dict[str, Any]) -> str:
    for key in ("source_table_id", "table_id", "extracted_table_id", "table_asset_id"):
        value = _norm(row.get(key))
        if value:
            return value
    return ""


def _candidate_split_decision(row: Dict[str, Any]) -> str:
    decision = _norm(row.get("split_decision"))
    if decision:
        return decision
    if _norm(row.get("split_reason")):
        return "review_required_preview"
    return ""


def _analysis_out_of_scope(row: Dict[str, Any], risk_tags: Sequence[str]) -> bool:
    if any(tag in OUT_OF_SCOPE_RISK_TAGS for tag in risk_tags):
        return True
    if _norm(row.get("metric_code")) != "unknown_metric":
        return False
    return _normalize_metric_label(row.get("raw_metric_name")) in {
        _normalize_metric_label(label) for label in ANALYSIS_OUT_OF_SCOPE_LABELS
    }


def _weighted_score(components: Sequence[Tuple[str, float, float]]) -> float:
    numerator = 0.0
    denominator = 0.0
    for _, value, weight in components:
        numerator += _clamp_score(value) * weight
        denominator += weight
    if denominator <= 0:
        return 0.0
    return 100.0 * numerator / denominator


def _sample_count(route_name: str, summary: Dict[str, Any]) -> int:
    if route_name == STRUCTTABLE_ROUTE:
        return _to_int(summary.get("input_image_count"))
    if route_name == DOCLING_ROUTE:
        return _to_int(summary.get("input_image_count"))
    if route_name == MINERU_ROUTE:
        return _to_int(summary.get("selected_table_count") or summary.get("unified_table_count"))
    if route_name == PURE_VLM_ROUTE:
        return _to_int(summary.get("vlm_folder_count"))
    if route_name == PPSTRUCTURE_ROUTE:
        return _to_int(summary.get("batch_table_count"))
    return 0


def _extract_conflict_count(summary: Dict[str, Any], candidates: List[Dict[str, Any]]) -> int:
    summary_count = _to_int(summary.get("conflict_count") or summary.get("true_value_conflict_count"))
    tag_count = sum(1 for row in candidates if "VALUE_CONFLICT" in _split_risk_tags(row.get("risk_tags")))
    return max(summary_count, tag_count)


def _build_route_scorecard_row(artifacts: RouteArtifacts) -> Dict[str, Any]:
    summary = _read_json(artifacts.mapping_summary_path)
    audit_summary = _read_json(artifacts.audit_summary_path) if artifacts.audit_summary_path else {}
    candidates = _read_jsonl(artifacts.mapping_jsonl_paths)

    trusted_count = 0
    review_count = 0
    rejected_count = 0
    out_of_scope_count = 0
    trusted_core_count = 0
    review_required_core_count = 0
    value_conflict_count = 0
    unit_unknown_count = 0
    unknown_metric_code_count = 0
    core_unit_unknown_count = 0
    core_unknown_metric_code_count = 0
    core_value_conflict_count = 0
    core_review_table_ids: set[str] = set()
    table_ids: set[str] = set()

    for row in candidates:
        risk_tags = _split_risk_tags(row.get("risk_tags"))
        table_id = _candidate_table_id(row)
        if table_id:
            table_ids.add(table_id)
        split_decision = _candidate_split_decision(row)
        is_out_of_scope = _analysis_out_of_scope(row, risk_tags)
        if is_out_of_scope:
            out_of_scope_count += 1
        if "VALUE_CONFLICT" in risk_tags:
            value_conflict_count += 1
        if "UNIT_UNKNOWN" in risk_tags:
            unit_unknown_count += 1
        if _norm(row.get("metric_code")) == "unknown_metric" or "UNKNOWN_METRIC_CODE" in risk_tags:
            unknown_metric_code_count += 1
        if not is_out_of_scope:
            if "VALUE_CONFLICT" in risk_tags:
                core_value_conflict_count += 1
            if "UNIT_UNKNOWN" in risk_tags:
                core_unit_unknown_count += 1
            if _norm(row.get("metric_code")) == "unknown_metric" or "UNKNOWN_METRIC_CODE" in risk_tags:
                core_unknown_metric_code_count += 1
        if split_decision == "trusted_preview":
            trusted_count += 1
            if not is_out_of_scope:
                trusted_core_count += 1
        elif split_decision == "review_required_preview":
            review_count += 1
            if not is_out_of_scope:
                review_required_core_count += 1
                if table_id:
                    core_review_table_ids.add(table_id)
        elif split_decision == "rejected_preview":
            rejected_count += 1

    total_candidate_count = len(candidates) or _to_int(
        summary.get("total_candidate_count")
        or summary.get("calibrated_total_candidate_count")
        or (_to_int(summary.get("trusted_total_count")) + _to_int(summary.get("review_required_total_count")) + _to_int(summary.get("rejected_total_count")))
    )
    if trusted_count == 0 and review_count == 0 and rejected_count == 0:
        trusted_count = _to_int(summary.get("trusted_total_count") or summary.get("calibrated_trusted_total_count"))
        review_count = _to_int(summary.get("review_required_total_count") or summary.get("calibrated_review_required_total_count"))
        rejected_count = _to_int(summary.get("rejected_total_count"))
    if artifacts.prefer_summary_unknown_metric_count:
        summary_unknown_metric_count = _to_int(summary.get("unknown_metric_code_count"))
        if summary_unknown_metric_count > 0:
            unknown_metric_code_count = summary_unknown_metric_count
    core_candidate_count = max(total_candidate_count - out_of_scope_count, 0)
    all_candidate_trusted_rate = (trusted_count / total_candidate_count) if total_candidate_count else 0.0
    core_candidate_trusted_rate = (trusted_core_count / core_candidate_count) if core_candidate_count else 0.0
    provenance_complete_rate = _to_float(summary.get("provenance_complete_rate"))
    sample_count = _sample_count(artifacts.route_name, summary)
    table_with_candidates_count = len(table_ids) or _to_int(summary.get("table_with_candidates_count"))
    review_required_core_table_count = len(core_review_table_ids)
    conflict_count = _extract_conflict_count(summary, candidates)
    value_parse_failed_count = sum(1 for row in candidates if "VALUE_PARSE_FAILED" in _split_risk_tags(row.get("risk_tags")))
    if value_parse_failed_count == 0:
        value_parse_failed_count = _to_int(summary.get("value_parse_failed_count"))

    extraction_components: List[Tuple[str, float, float]] = []
    coverage_score: Optional[float] = None
    schema_score: Optional[float] = None
    numeric_score: Optional[float] = None
    label_score: Optional[float] = None
    completeness_score: Optional[float] = None

    if artifacts.route_name == STRUCTTABLE_ROUTE:
        coverage_score = _to_int(audit_summary.get("image_with_real_table_grid_count")) / max(_to_int(audit_summary.get("input_image_count")), 1)
        schema_score = 1.0 - (_to_int(audit_summary.get("invalid_year_header_count")) / max(_to_int(audit_summary.get("total_year_header_count")), 1))
        numeric_score = _to_float(audit_summary.get("numeric_parse_success_rate"))
        label_score = 1.0 - (_to_int(audit_summary.get("label_corruption_count")) / max(_to_int(audit_summary.get("chinese_label_row_count")), 1))
        completeness_score = 1.0 - (_to_int(audit_summary.get("possible_missing_value_count")) / max(_to_int(audit_summary.get("total_row_count")), 1))
    elif artifacts.route_name == DOCLING_ROUTE:
        coverage_score = _to_int(audit_summary.get("image_with_real_cell_grid_count")) / max(_to_int(audit_summary.get("input_image_count")), 1)
        schema_score = 1.0 - (_to_int(audit_summary.get("invalid_year_header_count")) / max(_to_int(audit_summary.get("total_year_header_count")), 1))
        numeric_score = _to_float(audit_summary.get("numeric_parse_success_rate"))
        completeness_score = 1.0 - (_to_int(audit_summary.get("possible_missing_value_count")) / max(_to_int(audit_summary.get("total_cell_count")), 1))
    elif artifacts.route_name == MINERU_ROUTE:
        coverage_score = _to_int(summary.get("parsed_table_count")) / max(_to_int(summary.get("selected_table_count")), 1)
        schema_score = 1.0 - (_to_int(summary.get("year_invalid_count")) / max(total_candidate_count, 1))
        numeric_score = 1.0 - (value_parse_failed_count / max(total_candidate_count, 1))
    elif artifacts.route_name == PURE_VLM_ROUTE:
        coverage_score = _to_int(summary.get("table_ready_count")) / max(_to_int(summary.get("vlm_folder_count")), 1)
        schema_score = 1.0 - (_to_int(summary.get("invalid_year_count")) / max(total_candidate_count, 1))
        numeric_score = 1.0 - (value_parse_failed_count / max(total_candidate_count, 1))
        label_score = 1.0 - (_to_int(summary.get("corrupted_label_candidate_count")) / max(total_candidate_count, 1))
    elif artifacts.route_name == PPSTRUCTURE_ROUTE:
        coverage_score = _to_int(summary.get("table_with_row_text_count")) / max(_to_int(summary.get("batch_table_count")), 1)
        schema_score = 1.0 - (_to_int(summary.get("year_inferred_count")) / max(total_candidate_count, 1))
        numeric_score = 1.0 - (value_parse_failed_count / max(total_candidate_count, 1))

    if coverage_score is not None:
        extraction_components.append(("coverage", coverage_score, 0.30))
    if schema_score is not None:
        extraction_components.append(("schema", schema_score, 0.25))
    if numeric_score is not None:
        extraction_components.append(("numeric", numeric_score, 0.20))
    if label_score is not None:
        extraction_components.append(("label", label_score, 0.10))
    if completeness_score is not None:
        extraction_components.append(("completeness", completeness_score, 0.05))
    extraction_components.append(("qa", 1.0 if _to_int(summary.get("qa_fail_count")) == 0 else 0.0, 0.10))
    extraction_score = _weighted_score(extraction_components)

    all_mapping_score = _weighted_score(
        [
            ("trusted_rate", all_candidate_trusted_rate, 0.50),
            ("provenance", provenance_complete_rate, 0.15),
            ("unit", 1.0 - (unit_unknown_count / max(total_candidate_count, 1)), 0.10),
            ("unknown_metric", 1.0 - (unknown_metric_code_count / max(total_candidate_count, 1)), 0.15),
            ("conflict", 1.0 - (conflict_count / max(total_candidate_count, 1)), 0.10),
        ]
    )
    core_mapping_score = _weighted_score(
        [
            ("core_trusted_rate", core_candidate_trusted_rate, 0.55),
            ("provenance", provenance_complete_rate, 0.15),
            ("core_unit", 1.0 - (core_unit_unknown_count / max(core_candidate_count, 1)), 0.10),
            ("core_unknown_metric", 1.0 - (core_unknown_metric_code_count / max(core_candidate_count, 1)), 0.10),
            ("core_conflict", 1.0 - (core_value_conflict_count / max(core_candidate_count, 1)), 0.10),
        ]
    )
    review_burden_score = _weighted_score(
        [
            ("core_review_rate", 1.0 - (review_required_core_count / max(core_candidate_count, 1)), 0.55),
            ("table_review_rate", 1.0 - (review_required_core_table_count / max(sample_count, 1 if sample_count == 0 else sample_count)), 0.25),
            ("core_conflict", 1.0 - (core_value_conflict_count / max(core_candidate_count, 1)), 0.20),
        ]
    )
    overall_bakeoff_score = _weighted_score(
        [
            ("extraction", extraction_score / 100.0, 0.25),
            ("all_mapping", all_mapping_score / 100.0, 0.25),
            ("core_mapping", core_mapping_score / 100.0, 0.35),
            ("review_burden", review_burden_score / 100.0, 0.15),
        ]
    )

    return {
        "route_name": artifacts.route_name,
        "route_family": artifacts.route_family,
        "sample_count": sample_count,
        "table_with_candidates_count": table_with_candidates_count,
        "total_candidate_count": total_candidate_count,
        "trusted_total_count": trusted_count,
        "review_required_total_count": review_count,
        "rejected_total_count": rejected_count,
        "all_candidate_trusted_rate": all_candidate_trusted_rate,
        "core_candidate_trusted_rate": core_candidate_trusted_rate,
        "out_of_scope_candidate_count": out_of_scope_count,
        "review_required_core_count": review_required_core_count,
        "review_required_core_table_count": review_required_core_table_count,
        "unit_unknown_count": unit_unknown_count,
        "unknown_metric_code_count": unknown_metric_code_count,
        "value_conflict_count": conflict_count,
        "provenance_complete_rate": provenance_complete_rate,
        "core_candidate_count": core_candidate_count,
        "core_trusted_count": trusted_core_count,
        "core_unit_unknown_count": core_unit_unknown_count,
        "core_unknown_metric_code_count": core_unknown_metric_code_count,
        "core_value_conflict_count": core_value_conflict_count,
        "value_parse_failed_count": value_parse_failed_count,
        "possible_missing_value_count": _to_int(summary.get("possible_missing_value_count")),
        "qa_fail_count": _to_int(summary.get("qa_fail_count")),
        "mapping_decision": _norm(
            summary.get("structtable_mapping_decision")
            or summary.get("docling_mapping_decision")
            or summary.get("mineru_body_ingestion_decision")
            or summary.get("calibration_decision")
            or summary.get("batch_delivery_decision")
        ),
        "extraction_score": extraction_score,
        "all_candidate_mapping_score": all_mapping_score,
        "core_candidate_mapping_score": core_mapping_score,
        "review_burden_score": review_burden_score,
        "overall_bakeoff_score": overall_bakeoff_score,
    }


def _router_plan_rows(scorecard_df: pd.DataFrame) -> List[Dict[str, Any]]:
    pdf_rows = scorecard_df[scorecard_df["route_family"] == "pdf_table_body"].sort_values(
        ["core_candidate_mapping_score", "overall_bakeoff_score"],
        ascending=[False, False],
    )
    image_rows = scorecard_df[scorecard_df["route_family"] == "image_table"].sort_values(
        ["core_candidate_mapping_score", "extraction_score", "overall_bakeoff_score"],
        ascending=[False, False, False],
    )
    pdf_best = pdf_rows.iloc[0] if not pdf_rows.empty else None
    image_best = image_rows.iloc[0] if not image_rows.empty else None

    rows = [
        {
            "plan_type": "PDF_TABLE_BODY_DEFAULT_ROUTE",
            "recommended_route": _norm(pdf_best["route_name"]) if pdf_best is not None else "",
            "reason": (
                f"best pdf-body core_mapping={_to_float(pdf_best['core_candidate_mapping_score']):.2f}, "
                f"all_mapping={_to_float(pdf_best['all_candidate_mapping_score']):.2f}, "
                f"provenance={_to_float(pdf_best['provenance_complete_rate']):.2f}"
            ) if pdf_best is not None else "no pdf-table-body route available",
        },
        {
            "plan_type": "IMAGE_TABLE_DEFAULT_ROUTE",
            "recommended_route": _norm(image_best["route_name"]) if image_best is not None else "",
            "reason": (
                f"best image-table core_mapping={_to_float(image_best['core_candidate_mapping_score']):.2f}, "
                f"extraction={_to_float(image_best['extraction_score']):.2f}, "
                f"review_burden={_to_float(image_best['review_burden_score']):.2f}"
            ) if image_best is not None else "no image-table route available",
        },
        {
            "plan_type": "SEMANTIC_ADJUDICATOR_USE_CASE",
            "recommended_route": "VALUE_CONFLICT_OR_CONTEXT_DISPUTE",
            "reason": "use semantic adjudicator on duplicated labels, repeated section metrics, or value conflicts where extraction looks otherwise strong",
        },
        {
            "plan_type": "SEMANTIC_ADJUDICATOR_USE_CASE",
            "recommended_route": "UNKNOWN_METRIC_BUT_CORE_CONTEXT",
            "reason": "use semantic adjudicator when row text is readable and year/value are stable but metric code stays unknown on core statements",
        },
        {
            "plan_type": "MANUAL_REVIEW_USE_CASE",
            "recommended_route": "SCHEMA_OR_YEAR_FAILURE",
            "reason": "keep manual review for unsupported layouts, invalid/non-header year paths, or table-level review-only routes",
        },
        {
            "plan_type": "MANUAL_REVIEW_USE_CASE",
            "recommended_route": "PERSISTENT_UNIT_OR_PROVENANCE_RISK",
            "reason": "keep manual review for unresolved core UNIT_UNKNOWN, missing provenance, or routes with weak extraction evidence",
        },
    ]
    return rows


def _known_limitations_rows() -> List[Dict[str, Any]]:
    return [
        {
            "limitation": "analysis_only",
            "detail": "321E5 is a read-only bakeoff over existing outputs and does not rerun recognizers or production pipeline stages.",
        },
        {
            "limitation": "analysis_scope_gate",
            "detail": "out-of-scope counts for non-321E4B routes use a conservative analysis-only label gate for fairer core-rate comparison.",
        },
        {
            "limitation": "score_formula",
            "detail": "bakeoff scores are weighted proxies for comparison and should not be mistaken for production SLAs.",
        },
    ]


def _build_report(path: Path, summary: Dict[str, Any], rankings_df: pd.DataFrame, router_plan_df: pd.DataFrame, qa_df: pd.DataFrame) -> None:
    lines = [
        "# 321E5 Full Table Extraction Bakeoff",
        "",
        "## Summary",
        f"- pdf_table_body_default_route: {summary.get('pdf_table_body_default_route', '')}",
        f"- image_table_default_route: {summary.get('image_table_default_route', '')}",
        f"- top_overall_route: {summary.get('top_overall_route', '')}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Rankings",
    ]
    if rankings_df.empty:
        lines.append("- none")
    else:
        for _, row in rankings_df.iterrows():
            lines.append(
                "- "
                f"{row.get('route_name', '')}: overall={row.get('overall_bakeoff_score', 0):.2f}, "
                f"extraction={row.get('extraction_score', 0):.2f}, "
                f"all_mapping={row.get('all_candidate_mapping_score', 0):.2f}, "
                f"core_mapping={row.get('core_candidate_mapping_score', 0):.2f}, "
                f"review_burden={row.get('review_burden_score', 0):.2f}"
            )
    lines.extend(["", "## Router Plan"])
    if router_plan_df.empty:
        lines.append("- none")
    else:
        for _, row in router_plan_df.iterrows():
            lines.append(f"- {row.get('plan_type', '')}: {row.get('recommended_route', '')} | {row.get('reason', '')}")
    lines.extend(["", "## QA Checks"])
    if qa_df.empty:
        lines.append("- none")
    else:
        for _, row in qa_df.iterrows():
            lines.append(f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_qa_checks(config: FullBakeoffConfig, scorecard_df: pd.DataFrame, router_plan_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    required_dirs = [
        config.structtable_mapping_dir,
        config.structtable_audit_dir,
        config.docling_mapping_dir,
        config.docling_audit_dir,
        config.mineru_body_dir,
        config.pure_vlm_calibration_dir,
        config.ppstructure_benchmark_dir,
    ]
    add("all_required_input_dirs_exist", all(path.exists() for path in required_dirs), "; ".join(str(path) for path in required_dirs))
    add("only_existing_outputs_consumed", True, "321E5 reads summary/jsonl/xlsx outputs only")
    add("no_recognizer_execution_required", True, "StructEqTable/Docling/MinerU/PPStructure/VLM were not rerun")
    add("five_routes_scored", len(scorecard_df) == 5, f"route_count={len(scorecard_df)}")
    add(
        "all_route_counts_reconcile",
        bool(
            scorecard_df.empty
            or (
                scorecard_df["trusted_total_count"] + scorecard_df["review_required_total_count"] + scorecard_df["rejected_total_count"]
            ).eq(scorecard_df["total_candidate_count"]).all()
        ),
        "trusted + review + rejected must equal total candidates",
    )
    add(
        "router_defaults_present",
        bool(
            not router_plan_df.empty
            and (router_plan_df["plan_type"] == "PDF_TABLE_BODY_DEFAULT_ROUTE").any()
            and (router_plan_df["plan_type"] == "IMAGE_TABLE_DEFAULT_ROUTE").any()
        ),
        "pdf/image default route rows must exist",
    )
    return pd.DataFrame(rows)


def _route_artifacts(config: FullBakeoffConfig) -> List[RouteArtifacts]:
    return [
        RouteArtifacts(
            route_name=STRUCTTABLE_ROUTE,
            route_family="image_table",
            mapping_summary_path=config.structtable_mapping_dir / "structtable_unified_mapping_321e4b_summary.json",
            mapping_jsonl_paths=[config.structtable_mapping_dir / "structtable_metric_candidates_all.jsonl"],
            audit_summary_path=config.structtable_audit_dir / "structtable_output_audit_321e3_summary.json",
            prefer_summary_unknown_metric_count=True,
        ),
        RouteArtifacts(
            route_name=DOCLING_ROUTE,
            route_family="image_table",
            mapping_summary_path=config.docling_mapping_dir / "docling_unified_mapping_321e2_summary.json",
            mapping_jsonl_paths=[config.docling_mapping_dir / "docling_metric_candidates_all.jsonl"],
            audit_summary_path=config.docling_audit_dir / "docling_output_audit_321e1_summary.json",
            prefer_summary_unknown_metric_count=True,
        ),
        RouteArtifacts(
            route_name=MINERU_ROUTE,
            route_family="pdf_table_body",
            mapping_summary_path=config.mineru_body_dir / "mineru_table_body_ingestion_321d_summary.json",
            mapping_jsonl_paths=[
                config.mineru_body_dir / "trusted_preview.jsonl",
                config.mineru_body_dir / "review_required_preview.jsonl",
                config.mineru_body_dir / "rejected_preview.jsonl",
            ],
            prefer_summary_unknown_metric_count=True,
        ),
        RouteArtifacts(
            route_name=PURE_VLM_ROUTE,
            route_family="image_table",
            mapping_summary_path=config.pure_vlm_calibration_dir / "vlm_mapping_calibration_321b2_summary.json",
            mapping_jsonl_paths=[
                config.pure_vlm_calibration_dir / "trusted_preview.jsonl",
                config.pure_vlm_calibration_dir / "review_required_preview.jsonl",
            ],
            prefer_summary_unknown_metric_count=True,
        ),
        RouteArtifacts(
            route_name=PPSTRUCTURE_ROUTE,
            route_family="row_text_fallback",
            mapping_summary_path=config.ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json",
            mapping_jsonl_paths=[config.ppstructure_benchmark_dir / "normalized_candidates_all.jsonl"],
            prefer_summary_unknown_metric_count=False,
        ),
    ]


def run_full_table_extraction_bakeoff(config: FullBakeoffConfig) -> Dict[str, Any]:
    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    scorecard_rows = [_build_route_scorecard_row(artifacts) for artifacts in _route_artifacts(config)]
    scorecard_df = pd.DataFrame(scorecard_rows)
    rankings_df = scorecard_df.sort_values(
        ["overall_bakeoff_score", "core_candidate_mapping_score", "extraction_score"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    rankings_df["rank"] = rankings_df.index + 1
    rankings_df = rankings_df[
        [
            "rank",
            "route_name",
            "route_family",
            "overall_bakeoff_score",
            "extraction_score",
            "all_candidate_mapping_score",
            "core_candidate_mapping_score",
            "review_burden_score",
            "all_candidate_trusted_rate",
            "core_candidate_trusted_rate",
            "out_of_scope_candidate_count",
            "review_required_core_count",
            "unit_unknown_count",
            "unknown_metric_code_count",
            "value_conflict_count",
            "provenance_complete_rate",
        ]
    ]

    router_plan_df = pd.DataFrame(_router_plan_rows(scorecard_df))
    qa_df = _build_qa_checks(config, scorecard_df, router_plan_df)
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0

    pdf_default_route = _norm(
        router_plan_df.loc[router_plan_df["plan_type"] == "PDF_TABLE_BODY_DEFAULT_ROUTE", "recommended_route"].iloc[0]
    ) if not router_plan_df.empty and (router_plan_df["plan_type"] == "PDF_TABLE_BODY_DEFAULT_ROUTE").any() else ""
    image_default_route = _norm(
        router_plan_df.loc[router_plan_df["plan_type"] == "IMAGE_TABLE_DEFAULT_ROUTE", "recommended_route"].iloc[0]
    ) if not router_plan_df.empty and (router_plan_df["plan_type"] == "IMAGE_TABLE_DEFAULT_ROUTE").any() else ""
    top_route = _norm(rankings_df.iloc[0]["route_name"]) if not rankings_df.empty else ""

    summary = {
        "stage": "321E5",
        "output_dir": str(output_dir),
        "route_count": int(len(scorecard_df)),
        "top_overall_route": top_route,
        "pdf_table_body_default_route": pdf_default_route,
        "image_table_default_route": image_default_route,
        "semantic_adjudicator_scenarios": [
            "VALUE_CONFLICT or duplicated-section metrics with otherwise strong extraction evidence",
            "UNKNOWN_METRIC on core statements when row text, year, and value parse are stable",
        ],
        "manual_review_scenarios": [
            "unsupported layouts or table-level review-only outputs",
            "persistent core UNIT_UNKNOWN / provenance gaps / invalid year paths",
        ],
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    excel_path = output_dir / "table_extraction_full_bakeoff_321e5.xlsx"
    summary_json_path = output_dir / "table_extraction_full_bakeoff_321e5_summary.json"
    report_md_path = output_dir / "table_extraction_full_bakeoff_321e5_report.md"
    router_json_path = output_dir / "table_extraction_router_plan_321e5.json"

    _write_excel(
        excel_path,
        {
            "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
            "route_scorecard": scorecard_df,
            "route_rankings": rankings_df,
            "router_plan": router_plan_df,
            "qa_checks": qa_df,
            "known_limitations": pd.DataFrame(_known_limitations_rows()),
        },
    )
    _write_json(summary_json_path, summary)
    _write_json(
        router_json_path,
        {
            "stage": "321E5",
            "pdf_table_body_default_route": pdf_default_route,
            "image_table_default_route": image_default_route,
            "semantic_adjudicator_scenarios": summary["semantic_adjudicator_scenarios"],
            "manual_review_scenarios": summary["manual_review_scenarios"],
        },
    )
    _build_report(report_md_path, summary, rankings_df, router_plan_df, qa_df)

    return {
        "summary": summary,
        "scorecard_df": scorecard_df,
        "rankings_df": rankings_df,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
        "router_json_path": str(router_json_path),
    }
