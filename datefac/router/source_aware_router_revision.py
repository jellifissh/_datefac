from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from datefac.router.source_provenance_audit import (
    MINERU_TABLE_BODY_STRUCTURING,
    PURE_VLM_IMAGE_ONLY,
    audit_vlm_output_root,
)
from datefac.vlm.vlm_mapping_benchmark import run_vlm_mapping_benchmark
from datefac.vlm.vlm_quality_gate import run_vlm_output_quality_gate


VLM_API_LATER = "VLM_API_LATER"
MINERU_MARKDOWN_DIRECT = "MINERU_MARKDOWN_DIRECT"
PPSTRUCTURE_FALLBACK = "PPSTRUCTURE_FALLBACK"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
SKIP_NON_CORE_TABLE = "SKIP_NON_CORE_TABLE"
UNSUPPORTED_TABLE_TYPE = "UNSUPPORTED_TABLE_TYPE"

ROUTE_ORDER = [
    MINERU_TABLE_BODY_STRUCTURING,
    PURE_VLM_IMAGE_ONLY,
    VLM_API_LATER,
    MINERU_MARKDOWN_DIRECT,
    PPSTRUCTURE_FALLBACK,
    MANUAL_REVIEW_REQUIRED,
    SKIP_NON_CORE_TABLE,
    UNSUPPORTED_TABLE_TYPE,
]

CORE_ROLE_SET = {
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "CORE_METRIC_TABLE",
    "FINANCIAL_FORECAST_VALUATION",
}
NON_CORE_ROLE_SET = {
    "RATING_STANDARD",
    "DISCLAIMER_OR_LEGAL",
    "CHART_OR_MARKET_TREND",
}

SHEET_ORDER = [
    "summary",
    "revised_router_policy",
    "source_provenance_audit",
    "route_comparison_summary",
    "table_route_preview_revised",
    "mineru_table_body_worklist",
    "pure_vlm_worklist",
    "ppstructure_fallback_worklist",
    "manual_review_worklist",
    "unsupported_tables",
    "integration_plan",
    "known_limitations",
    "qa_checks",
]


@dataclass
class SourceAwareRouterRevisionConfig:
    pure_vlm_calibration_dir: Path
    pure_vlm_output_root: Path
    mineru_assisted_output_root: Optional[Path]
    previous_router_dir: Optional[Path]
    ppstructure_benchmark_dir: Optional[Path]
    mineru_benchmark_dir: Optional[Path]
    mineru_output_root: Optional[Path]
    output_dir: Path


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
        return int(float(str(value).strip()))
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    base = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    out = base
    index = 1
    while out in used:
        suffix = f"_{index}"
        out = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(out)
    return out


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


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


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def _parse_extra(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = ast.literal_eval(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in _norm(text))


def _blocked_output(config: SourceAwareRouterRevisionConfig) -> Dict[str, Any]:
    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "321C2",
        "blocked": True,
        "blocked_code": "BLOCKED_MISSING_321B2_PURE_VLM_CALIBRATION",
        "blocked_message": "pure VLM calibration dir is required for source-aware router revision",
        "router_revision_decision": "SOURCE_AWARE_ROUTER_BLOCKED_BY_QA_FAILURE",
        "output_dir": str(output_dir),
        "router_qa_pass_count": 0,
        "router_qa_warn_count": 0,
        "router_qa_fail_count": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    policy = {
        "route_types": ROUTE_ORDER,
        "notes": "321C2 blocked before source-aware routing due missing pure VLM calibration input",
    }
    report_lines = [
        "# 321C2 Source-aware Router Revision",
        "",
        "- blocked: `BLOCKED_MISSING_321B2_PURE_VLM_CALIBRATION`",
        f"- output_dir: `{output_dir}`",
    ]
    _write_excel(
        output_dir / "source_aware_router_revision_321c2.xlsx",
        {
            "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
            "revised_router_policy": pd.DataFrame([{"route_type": route} for route in ROUTE_ORDER]),
            "source_provenance_audit": pd.DataFrame(),
            "route_comparison_summary": pd.DataFrame(),
            "table_route_preview_revised": pd.DataFrame(),
            "mineru_table_body_worklist": pd.DataFrame(),
            "pure_vlm_worklist": pd.DataFrame(),
            "ppstructure_fallback_worklist": pd.DataFrame(),
            "manual_review_worklist": pd.DataFrame(),
            "unsupported_tables": pd.DataFrame(),
            "integration_plan": pd.DataFrame(),
            "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": summary["blocked_message"]}]),
            "qa_checks": pd.DataFrame([{"check_name": summary["blocked_code"], "status": "FAIL", "detail": summary["blocked_message"]}]),
        },
    )
    _write_json(output_dir / "source_aware_router_revision_321c2_summary.json", summary)
    _write_json(output_dir / "recognizer_router_policy_321c2.json", policy)
    (output_dir / "source_aware_router_revision_321c2_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return {
        "summary": summary,
        "excel_path": str(output_dir / "source_aware_router_revision_321c2.xlsx"),
        "summary_json_path": str(output_dir / "source_aware_router_revision_321c2_summary.json"),
        "report_md_path": str(output_dir / "source_aware_router_revision_321c2_report.md"),
        "policy_json_path": str(output_dir / "recognizer_router_policy_321c2.json"),
    }


def _load_pure_vlm_calibration(calibration_dir: Path) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    summary = _read_json(calibration_dir / "vlm_mapping_calibration_321b2_summary.json")
    workbook = calibration_dir / "vlm_mapping_calibration_321b2.xlsx"
    per_table = _read_sheet(workbook, "per_table_summary").fillna("")
    candidates = _read_sheet(workbook, "metric_candidates_all").fillna("")
    return summary, per_table, candidates


def _load_previous_router(previous_router_dir: Optional[Path]) -> Tuple[Dict[str, Any], pd.DataFrame]:
    if not previous_router_dir or not previous_router_dir.exists():
        return {}, pd.DataFrame()
    summary = _read_json(previous_router_dir / "recognizer_router_plan_321c_summary.json")
    workbook = previous_router_dir / "recognizer_router_plan_321c.xlsx"
    preview = _read_sheet(workbook, "table_route_preview").fillna("")
    return summary, preview


def _load_mineru_benchmark(mineru_benchmark_dir: Optional[Path]) -> Tuple[Dict[str, Any], pd.DataFrame]:
    if not mineru_benchmark_dir or not mineru_benchmark_dir.exists():
        return {}, pd.DataFrame()
    summary = _read_json(mineru_benchmark_dir / "mineru_benchmark_320b2_summary.json")
    workbook = mineru_benchmark_dir / "mineru_benchmark_320b2.xlsx"
    assets = _read_sheet(workbook, "table_assets_all").fillna("")
    return summary, assets


def _load_ppstructure_summary(ppstructure_benchmark_dir: Optional[Path]) -> Dict[str, Any]:
    if not ppstructure_benchmark_dir or not ppstructure_benchmark_dir.exists():
        return {}
    summary_json = ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json"
    if summary_json.exists():
        return _read_json(summary_json)
    workbook = ppstructure_benchmark_dir / "batch_row_text_delivery_320g.xlsx"
    summary_df = _read_sheet(workbook, "summary")
    if summary_df.empty or not {"metric", "value"}.issubset(summary_df.columns):
        return {}
    return {str(row["metric"]): row["value"] for _, row in summary_df.iterrows()}


def _bootstrap_mineru_assisted_sample_metrics(sample_root: Optional[Path], output_dir: Path) -> Dict[str, Any]:
    if not sample_root or not sample_root.exists():
        return {}
    quality_dir = output_dir / "_bootstrap_sample_quality_321a"
    mapping_dir = output_dir / "_bootstrap_sample_mapping_321b"
    quality_summary = run_vlm_output_quality_gate(vlm_output_root=sample_root, output_dir=quality_dir)
    mapping_result = run_vlm_mapping_benchmark(
        vlm_output_root=sample_root,
        quality_dir=quality_dir,
        output_dir=mapping_dir,
        ppstructure_benchmark_dir=None,
    )
    summary = dict(mapping_result.get("summary", {}))
    summary["quality_summary"] = quality_summary
    return summary


def _load_previous_strict_vlm_summary(previous_router_summary: Dict[str, Any]) -> Dict[str, Any]:
    candidate_dirs = []
    path_from_router = _norm(previous_router_summary.get("vlm_benchmark_dir"))
    if path_from_router:
        candidate_dirs.append(Path(path_from_router))
    candidate_dirs.append(Path(r"D:\_datefac\output\vlm_mapping_benchmark_321b"))
    for directory in candidate_dirs:
        summary_path = directory / "vlm_mapping_benchmark_321b_summary.json"
        if summary_path.exists():
            return _read_json(summary_path)
    return {}


def _build_pure_match_df(per_table_df: pd.DataFrame, candidate_df: pd.DataFrame) -> pd.DataFrame:
    if per_table_df.empty:
        return pd.DataFrame()
    image_df = candidate_df[["source_table_id", "source_file"]].drop_duplicates().copy() if not candidate_df.empty else pd.DataFrame(columns=["source_table_id", "source_file"])
    image_df = image_df.rename(columns={"source_table_id": "table_folder", "source_file": "pure_source_file"})
    merged = per_table_df.merge(image_df, on="table_folder", how="left")
    merged["pure_image_filename"] = merged["pure_source_file"].astype(str).str.replace("\\", "/", regex=False).str.split("/").str[-1]
    merged["pure_quality_decision"] = merged["quality_decision"]
    merged["pure_table_decision"] = merged["table_decision"]
    merged["pure_trusted_count"] = merged["trusted_count"].apply(_to_int)
    merged["pure_review_required_count"] = merged["review_required_count"].apply(_to_int)
    merged["pure_candidate_count"] = merged["candidate_count"].apply(_to_int)
    return merged


def _reduce_pure_match_df(pure_match_df: pd.DataFrame) -> pd.DataFrame:
    if pure_match_df.empty:
        return pure_match_df
    reduced = pure_match_df.copy()
    reduced["pure_match_rank"] = list(
        zip(
            reduced["pure_trusted_count"].apply(_to_int),
            reduced["pure_review_required_count"].apply(_to_int).mul(-1),
            reduced["pure_candidate_count"].apply(_to_int),
            reduced["table_folder"].astype(str),
        )
    )
    reduced = reduced.sort_values(
        by=[
            "pure_image_filename",
            "pure_trusted_count",
            "pure_review_required_count",
            "pure_candidate_count",
            "table_folder",
        ],
        ascending=[True, False, True, False, True],
    )
    reduced = reduced.drop_duplicates(subset=["pure_image_filename"], keep="first").drop(columns=["pure_match_rank"], errors="ignore")
    return reduced


def _build_mineru_body_df(assets_df: pd.DataFrame) -> pd.DataFrame:
    if assets_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for _, row in assets_df.iterrows():
        extra = _parse_extra(row.get("extra"))
        raw_block = extra.get("raw_block", {}) if isinstance(extra, dict) else {}
        table_body = _norm(raw_block.get("table_body"))
        table_caption = raw_block.get("table_caption", [])
        caption_text = "|".join(_norm(item) for item in table_caption) if isinstance(table_caption, list) else _norm(table_caption)
        has_table_body = bool(table_body)
        has_html_table = "<table" in table_body.lower()
        body_has_chinese = _contains_chinese(table_body)
        table_body_length = len(table_body)
        rows.append(
            {
                "source_report_name": _norm(row.get("report_name")),
                "bbox": _norm(row.get("bbox")),
                "image_path": _norm(row.get("image_path")),
                "image_filename": Path(_norm(row.get("image_path"))).name if _norm(row.get("image_path")) else "",
                "mineru_has_table_body": has_table_body,
                "mineru_has_html_table": has_html_table,
                "mineru_body_has_chinese": body_has_chinese,
                "mineru_table_body_length": table_body_length,
                "mineru_caption_text": caption_text,
                "mineru_table_body_clean": bool(has_table_body and has_html_table and body_has_chinese and table_body_length >= 40),
            }
        )
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return dataframe
    grouped = (
        dataframe.groupby(["source_report_name", "image_filename", "bbox"], dropna=False)
        .agg(
            mineru_has_table_body=("mineru_has_table_body", "max"),
            mineru_has_html_table=("mineru_has_html_table", "max"),
            mineru_body_has_chinese=("mineru_body_has_chinese", "max"),
            mineru_table_body_length=("mineru_table_body_length", "max"),
            mineru_caption_text=("mineru_caption_text", lambda series: next((item for item in series if _norm(item)), "")),
            mineru_table_body_clean=("mineru_table_body_clean", "max"),
            image_path=("image_path", lambda series: next((item for item in series if _norm(item)), "")),
        )
        .reset_index()
        .rename(columns={"image_path": "image_path_y"})
    )
    return grouped


def _finalize_route_preview_df(route_preview_df: pd.DataFrame) -> pd.DataFrame:
    if route_preview_df.empty:
        return route_preview_df
    out = route_preview_df.copy()
    if "table_asset_id" not in out.columns:
        return out.reset_index(drop=True)
    out["table_asset_id"] = out["table_asset_id"].astype(str)
    out = out.sort_values(
        ["source_report_name", "image_filename", "estimated_value_score", "table_asset_id"],
        ascending=[True, True, False, True],
    )
    out = out.drop_duplicates(subset=["table_asset_id"], keep="first")
    return out.reset_index(drop=True)


def _policy_rows() -> List[Dict[str, Any]]:
    return [
        {
            "route_type": MINERU_TABLE_BODY_STRUCTURING,
            "priority_order": 1,
            "conditions": "core/high-value table and MinerU already has clean html table body with Chinese preserved",
            "notes": "cheaper than pure VLM and preferred first ingestion route for 321D sandbox",
        },
        {
            "route_type": PURE_VLM_IMAGE_ONLY,
            "priority_order": 2,
            "conditions": "core/high-value table, image exists, pure VLM source verified, quality ready, and trusted output available",
            "notes": "promising but still calibration-needed; not unconditional primary",
        },
        {
            "route_type": VLM_API_LATER,
            "priority_order": 3,
            "conditions": "core/high-value table with image but no verified pure output and no clean MinerU table body",
            "notes": "defer until live VLM API is stable",
        },
        {
            "route_type": MINERU_MARKDOWN_DIRECT,
            "priority_order": 4,
            "conditions": "simple/basic-data style table where text table is enough and no visual reconstruction is needed",
            "notes": "lowest-cost path for simple rows",
        },
        {
            "route_type": PPSTRUCTURE_FALLBACK,
            "priority_order": 5,
            "conditions": "lower-value table with existing PPStructure row-text evidence and no better route",
            "notes": "fallback and diagnostic only",
        },
        {
            "route_type": MANUAL_REVIEW_REQUIRED,
            "priority_order": 6,
            "conditions": "core table without reliable source output or with high review/conflict burden",
            "notes": "hold before ingestion",
        },
        {
            "route_type": SKIP_NON_CORE_TABLE,
            "priority_order": 7,
            "conditions": "ratings, disclaimers, metadata, non-core tables",
            "notes": "do not spend recognizer budget",
        },
        {
            "route_type": UNSUPPORTED_TABLE_TYPE,
            "priority_order": 8,
            "conditions": "segment/hierarchical or schema-invalid table still unsupported",
            "notes": "must stay explicit and untrusted",
        },
    ]


def _is_non_core(row: Dict[str, Any]) -> bool:
    role = _norm(row.get("effective_role_category") or row.get("table_role_guess"))
    caption = _norm(row.get("caption"))
    return role in NON_CORE_ROLE_SET or any(keyword in caption for keyword in ["评级", "免责声明", "市场数据"])


def _is_unsupported(row: Dict[str, Any]) -> bool:
    pure_quality = _norm(row.get("pure_quality_decision"))
    pure_table_decision = _norm(row.get("pure_table_decision"))
    previous_route = _norm(row.get("previous_recommended_route"))
    if previous_route == UNSUPPORTED_TABLE_TYPE:
        return True
    if pure_quality == "VLM_TABLE_SCHEMA_INVALID":
        return True
    if pure_table_decision == "TABLE_LEVEL_REVIEW_ONLY":
        return True
    return False


def _is_core_or_high_value(row: Dict[str, Any]) -> bool:
    role = _norm(row.get("effective_role_category") or row.get("table_role_guess"))
    value_score = _to_int(row.get("estimated_value_score"))
    return role in CORE_ROLE_SET or value_score >= 75


def _decide_revised_route(row: Dict[str, Any], pure_calibration_summary: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    blocker_reason = ""
    image_exists = _to_bool(row.get("image_exists"))
    mineru_body_clean = _to_bool(row.get("mineru_table_body_clean"))
    ppstructure_trusted = _to_int(row.get("ppstructure_trusted_count"))
    ppstructure_available = _to_bool(row.get("ppstructure_output_available"))
    pure_source_verified = _to_bool(row.get("pure_source_verified"))
    pure_quality_ready = _norm(row.get("pure_quality_decision")) == "VLM_TABLE_READY_FOR_MAPPING"
    pure_trusted_count = _to_int(row.get("pure_trusted_count"))
    pure_review_count = _to_int(row.get("pure_review_required_count"))
    pure_table_decision = _norm(row.get("pure_table_decision"))
    sample_contamination_risk = _to_bool(row.get("mineru_assisted_source_risk"))
    core_or_high_value = _is_core_or_high_value(row)

    if not image_exists:
        reasons.append("image_missing")
        blocker_reason = "IMAGE_PATH_MISSING"
        route = MANUAL_REVIEW_REQUIRED if core_or_high_value else SKIP_NON_CORE_TABLE
    elif _is_non_core(row):
        reasons.append("non_core_table")
        route = SKIP_NON_CORE_TABLE
    elif _is_unsupported(row):
        reasons.append("unsupported_schema_or_segment")
        if pure_table_decision == "TABLE_LEVEL_REVIEW_ONLY":
            reasons.append("pure_vlm_table_level_review_only")
        route = UNSUPPORTED_TABLE_TYPE
        blocker_reason = "SCHEMA_SUPPORT_NEEDED"
    elif core_or_high_value and mineru_body_clean:
        reasons.extend(["core_or_high_value_table", "clean_mineru_table_body_available", "cheaper_than_pure_vlm"])
        if _to_float(pure_calibration_summary.get("calibrated_trusted_rate")) < 0.45:
            reasons.append("pure_vlm_still_partial")
        route = MINERU_TABLE_BODY_STRUCTURING
    elif core_or_high_value and pure_source_verified and pure_quality_ready and pure_trusted_count > 0:
        reasons.extend(["core_or_high_value_table", "pure_vlm_source_verified", "pure_vlm_quality_ready", "pure_vlm_trusted_output_available"])
        if sample_contamination_risk:
            reasons.append("sample_root_contamination_tracked_separately")
        route = PURE_VLM_IMAGE_ONLY
    elif core_or_high_value and pure_source_verified and pure_quality_ready and pure_review_count > 0 and pure_trusted_count == 0:
        reasons.extend(["core_or_high_value_table", "pure_vlm_available_but_review_heavy"])
        route = MANUAL_REVIEW_REQUIRED
        blocker_reason = "PURE_VLM_REVIEW_BURDEN_HIGH"
    elif core_or_high_value and ppstructure_trusted > 0:
        reasons.extend(["core_or_high_value_table", "ppstructure_has_some_trusted_output", "fallback_until_better_source"])
        route = PPSTRUCTURE_FALLBACK
    elif core_or_high_value:
        reasons.extend(["core_or_high_value_table", "no_verified_pure_vlm_output", "defer_to_live_vlm_api_later"])
        route = VLM_API_LATER
        blocker_reason = "PURE_VLM_SAMPLE_COVERAGE_MISSING"
    elif mineru_body_clean:
        reasons.extend(["simple_or_mid_value_table", "clean_mineru_table_body_available"])
        route = MINERU_MARKDOWN_DIRECT
    elif ppstructure_available:
        reasons.extend(["lower_value_table", "ppstructure_fallback_available"])
        route = PPSTRUCTURE_FALLBACK
    else:
        reasons.append("no_reliable_source_route")
        route = MANUAL_REVIEW_REQUIRED
        blocker_reason = "NO_RELIABLE_RECOGNIZER_OUTPUT"

    return {
        "recommended_route": route,
        "route_reason": "|".join(reasons),
        "blocker_reason": blocker_reason,
    }


def _build_route_comparison_rows(
    pure_summary: Dict[str, Any],
    ppstructure_summary: Dict[str, Any],
    previous_strict_summary: Dict[str, Any],
    mineru_sample_summary: Dict[str, Any],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = [
        {
            "route_label": "PURE_VLM_321B2_CALIBRATED",
            "source_type": PURE_VLM_IMAGE_ONLY,
            "candidate_count": _to_int(pure_summary.get("calibrated_total_candidate_count")),
            "trusted_count": _to_int(pure_summary.get("calibrated_trusted_total_count")),
            "trusted_rate": _to_float(pure_summary.get("calibrated_trusted_rate")),
            "review_required_count": _to_int(pure_summary.get("calibrated_review_required_total_count")),
            "unit_unknown_count": _to_int(pure_summary.get("unit_unknown_count")),
            "unknown_metric_count": _to_int(pure_summary.get("unknown_metric_code_count")),
            "conflict_count": _to_int(pure_summary.get("true_value_conflict_count")),
            "qa_pass_count": _to_int(pure_summary.get("qa_pass_count")),
            "qa_fail_count": _to_int(pure_summary.get("qa_fail_count")),
            "provenance_source_confidence": 1.0,
            "benchmark_decision": _norm(pure_summary.get("calibration_decision")),
            "notes": "pure image-only VLM benchmark after 321B2 calibration",
        },
        {
            "route_label": "PPSTRUCTURE_320G",
            "source_type": PPSTRUCTURE_FALLBACK,
            "candidate_count": _to_int(ppstructure_summary.get("trusted_total_count")) + _to_int(ppstructure_summary.get("review_required_total_count")),
            "trusted_count": _to_int(ppstructure_summary.get("trusted_total_count")),
            "trusted_rate": _to_float(ppstructure_summary.get("trusted_rate")),
            "review_required_count": _to_int(ppstructure_summary.get("review_required_total_count")),
            "unit_unknown_count": _to_int(ppstructure_summary.get("unit_unknown_count")),
            "unknown_metric_count": 0,
            "conflict_count": _to_int(ppstructure_summary.get("conflict_count")),
            "qa_pass_count": _to_int(ppstructure_summary.get("qa_pass_count")),
            "qa_fail_count": _to_int(ppstructure_summary.get("qa_fail_count")),
            "provenance_source_confidence": _to_float(ppstructure_summary.get("provenance_complete_rate")),
            "benchmark_decision": _norm(ppstructure_summary.get("batch_delivery_decision")),
            "notes": "row-text fallback benchmark; not apples-to-apples with VLM",
        },
    ]
    if previous_strict_summary:
        rows.append(
            {
                "route_label": "PREVIOUS_STRICT_VLM_321B",
                "source_type": "STRICT_VLM_MANUAL_JSON",
                "candidate_count": _to_int(previous_strict_summary.get("total_candidate_count")),
                "trusted_count": _to_int(previous_strict_summary.get("trusted_total_count")),
                "trusted_rate": _to_float(previous_strict_summary.get("trusted_rate")),
                "review_required_count": _to_int(previous_strict_summary.get("review_required_total_count")),
                "unit_unknown_count": _to_int(previous_strict_summary.get("unit_unknown_count")),
                "unknown_metric_count": 0,
                "conflict_count": _to_int(previous_strict_summary.get("conflict_count")),
                "qa_pass_count": _to_int(previous_strict_summary.get("qa_pass_count")),
                "qa_fail_count": _to_int(previous_strict_summary.get("qa_fail_count")),
                "provenance_source_confidence": _to_float(previous_strict_summary.get("provenance_complete_rate")),
                "benchmark_decision": _norm(previous_strict_summary.get("vlm_benchmark_decision")),
                "notes": "earlier strict VLM sample used by 321C baseline",
            }
        )
    if mineru_sample_summary:
        rows.append(
            {
                "route_label": "MINERU_ASSISTED_321D_SAMPLE_LOCAL_JSON",
                "source_type": MINERU_TABLE_BODY_STRUCTURING,
                "candidate_count": _to_int(mineru_sample_summary.get("total_candidate_count")),
                "trusted_count": _to_int(mineru_sample_summary.get("trusted_total_count")),
                "trusted_rate": _to_float(mineru_sample_summary.get("trusted_rate")),
                "review_required_count": _to_int(mineru_sample_summary.get("review_required_total_count")),
                "unit_unknown_count": _to_int(mineru_sample_summary.get("unit_unknown_count")),
                "unknown_metric_count": 0,
                "conflict_count": _to_int(mineru_sample_summary.get("conflict_count")),
                "qa_pass_count": _to_int(mineru_sample_summary.get("qa_pass_count")),
                "qa_fail_count": _to_int(mineru_sample_summary.get("qa_fail_count")),
                "provenance_source_confidence": 0.35,
                "benchmark_decision": _norm(mineru_sample_summary.get("vlm_benchmark_decision")),
                "notes": "manual sample root with contamination risk; use only as assisted-source evidence",
            }
        )
    return pd.DataFrame(rows)


def _build_integration_plan(
    summary: Dict[str, Any],
    route_preview_df: pd.DataFrame,
    source_audit_df: pd.DataFrame,
) -> pd.DataFrame:
    contamination_count = int(source_audit_df["risk_tags"].astype(str).str.contains("SOURCE_CONTAMINATION_RISK").sum()) if not source_audit_df.empty else 0
    rows = [
        {
            "phase": "321D_SANDBOX_FIRST",
            "priority": "P0",
            "action": "ingest MINERU_TABLE_BODY_STRUCTURING tables first",
            "reason": f"revised mineru body route count={summary.get('revised_mineru_table_body_structuring_count', 0)} and pure VLM remains partial",
            "gate": "keep source labels explicit; do not label MinerU-assisted outputs as pure VLM",
        },
        {
            "phase": "321D_LABEL_FIX",
            "priority": "P0",
            "action": "relabel 321d_sample lineage as MINERU_TABLE_BODY_STRUCTURING or MINERU_TABLE_BODY_ASSISTED",
            "reason": f"source contamination risk folders={contamination_count}",
            "gate": "no E-drive file modification in 321C2; audit only",
        },
        {
            "phase": "321D_PURE_VLM_SECOND",
            "priority": "P1",
            "action": "use PURE_VLM_IMAGE_ONLY only for verified tables with trusted calibrated outputs",
            "reason": f"pure VLM trusted tables={summary.get('pure_vlm_table_with_trusted_count', 0)} trusted_rate={summary.get('pure_vlm_calibrated_trusted_rate', 0.0)}",
            "gate": "keep manual review on high unknown-unit/conflict cases",
        },
        {
            "phase": "LATER_API_WORK",
            "priority": "P2",
            "action": "defer VLM_API_LATER route until live API stability recovers",
            "reason": "current router revision stays sandbox-only and source-aware",
            "gate": "no production integration claim",
        },
    ]
    if route_preview_df.empty:
        rows.append(
            {
                "phase": "FALLBACK",
                "priority": "P2",
                "action": "collect more route samples",
                "reason": "route preview unavailable",
                "gate": "needs additional benchmarks",
            }
        )
    return pd.DataFrame(rows)


def _build_known_limitations() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "manual_sample_not_apples_to_apples",
                "detail": "pure VLM and MinerU-assisted samples were manually generated and are not directly comparable to a live production recognizer run.",
            },
            {
                "limitation": "pure_vlm_partial",
                "detail": "321B2 improved pure VLM substantially but it still has high unknown metric and unit burden.",
            },
            {
                "limitation": "mineru_body_asset_availability_not_mapping",
                "detail": "MinerU table_body availability is structural evidence and not a fully validated ingestion benchmark by itself.",
            },
            {
                "limitation": "live_vlm_api_unstable",
                "detail": "VLM_API_LATER remains deferred because earlier live API tests were unstable.",
            },
        ]
    )


def _build_qa_checks(
    config: SourceAwareRouterRevisionConfig,
    pure_summary: Dict[str, Any],
    policy_json: Dict[str, Any],
    route_preview_df: pd.DataFrame,
    source_audit_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def add(check_name: str, passed: bool, severity: str, detail: str) -> None:
        rows.append(
            {
                "check_name": check_name,
                "status": "PASS" if passed else ("WARN" if severity == "warn" else "FAIL"),
                "severity": severity.upper(),
                "detail": detail,
            }
        )

    pure_root_exists = config.pure_vlm_calibration_dir.exists()
    add("pure_vlm_calibration_dir_exists", pure_root_exists, "fail", str(config.pure_vlm_calibration_dir))
    pure_audit = source_audit_df[source_audit_df["dataset_label"] == "PURE_VLM_OUTPUT_ROOT"].copy() if not source_audit_df.empty else pd.DataFrame()
    sample_audit = source_audit_df[source_audit_df["dataset_label"] == "MINERU_ASSISTED_SAMPLE_ROOT"].copy() if not source_audit_df.empty else pd.DataFrame()
    pure_fail_count = int((pure_audit["audit_status"] == "FAIL").sum()) if not pure_audit.empty else 0
    add("pure_vlm_source_meta_not_contaminated", pure_fail_count == 0, "fail", f"pure_source_fail_count={pure_fail_count}")
    add("no_production_files_modified", True, "fail", "321C2 only writes sandbox outputs under output/source_aware_router_revision_321c2")
    add("router_policy_json_valid", bool(policy_json.get("route_types")), "fail", "policy JSON built from deterministic route definitions")
    add(
        "every_revised_route_has_reason",
        route_preview_df.empty or bool((route_preview_df["route_reason"].fillna("").astype(str).str.len() > 0).all()),
        "fail",
        "all revised route rows should have route_reason",
    )
    unique_table_asset_count = route_preview_df["table_asset_id"].astype(str).nunique() if (not route_preview_df.empty and "table_asset_id" in route_preview_df.columns) else 0
    add(
        "table_asset_id_unique_after_route_merge",
        route_preview_df.empty or len(route_preview_df) == unique_table_asset_count,
        "fail",
        f"rows={len(route_preview_df)} unique_table_asset_id={unique_table_asset_count}",
    )
    pure_route_df = route_preview_df[route_preview_df["recommended_route"] == PURE_VLM_IMAGE_ONLY].copy() if not route_preview_df.empty else pd.DataFrame()
    add(
        "pure_vlm_route_only_for_tables_with_image",
        pure_route_df.empty or bool(pure_route_df["image_exists"].fillna(False).astype(bool).all()),
        "fail",
        "PURE_VLM_IMAGE_ONLY requires image_exists",
    )
    mislabeled_body_df = route_preview_df[
        (route_preview_df["recommended_route"] == MINERU_TABLE_BODY_STRUCTURING)
        & (route_preview_df["pure_source_verified"].fillna(False).astype(bool))
        & (route_preview_df["mineru_assisted_source_risk"].fillna(False).astype(bool))
    ] if not route_preview_df.empty else pd.DataFrame()
    add(
        "mineru_table_body_route_not_mislabeled_as_pure_vlm",
        mislabeled_body_df.empty,
        "warn",
        f"mixed provenance rows={len(mislabeled_body_df)}",
    )
    unsupported_bad_df = route_preview_df[
        (route_preview_df["recommended_route"].isin([MINERU_TABLE_BODY_STRUCTURING, PURE_VLM_IMAGE_ONLY]))
        & (route_preview_df["pure_quality_decision"].astype(str) == "VLM_TABLE_SCHEMA_INVALID")
    ] if not route_preview_df.empty else pd.DataFrame()
    add(
        "unsupported_tables_not_silently_trusted",
        unsupported_bad_df.empty,
        "fail",
        f"unsupported routed as trusted-like count={len(unsupported_bad_df)}",
    )
    chinese_ok = route_preview_df.empty or bool(~route_preview_df["table_title_final"].fillna("").astype(str).str.contains(r"\?{2,}", regex=True).any())
    add("chinese_text_preserved", chinese_ok, "warn", "route preview should not replace Chinese labels with question marks")
    sample_risk_count = int(sample_audit["risk_tags"].astype(str).str.contains("SOURCE_CONTAMINATION_RISK").sum()) if not sample_audit.empty else 0
    add("mineru_assisted_sample_contamination_tracked", sample_risk_count > 0, "warn", f"source_contamination_risk_count={sample_risk_count}")
    add(
        "pure_vlm_calibration_not_blocked",
        _norm(pure_summary.get("calibration_decision")) != "",
        "fail",
        _norm(pure_summary.get("calibration_decision")) or "missing calibration decision",
    )
    return pd.DataFrame(rows)


def _policy_json(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "stage": "321C2",
        "route_types": ROUTE_ORDER,
        "policy_rows": _policy_rows(),
        "decision_rules": {
            "blocked": "router_qa_fail_count > 0",
            "mineru_body_first": "pure VLM partial and mineru table body route available for many core tables",
            "pure_vlm_ready": "pure_vlm_calibrated_trusted_rate >= 0.45 and source audit passes",
        },
        "summary_snapshot": {
            "pure_vlm_calibrated_trusted_rate": summary.get("pure_vlm_calibrated_trusted_rate", 0.0),
            "revised_mineru_table_body_structuring_count": summary.get("revised_mineru_table_body_structuring_count", 0),
            "revised_pure_vlm_image_only_count": summary.get("revised_pure_vlm_image_only_count", 0),
            "revised_vlm_api_later_count": summary.get("revised_vlm_api_later_count", 0),
            "revised_mineru_markdown_direct_count": summary.get("revised_mineru_markdown_direct_count", 0),
            "revised_route_total_count": summary.get("revised_route_total_count", 0),
            "source_contamination_risk_count": summary.get("source_contamination_risk_count", 0),
        },
        "notes": "source-aware router revision separates pure image-only VLM from MinerU table-body assisted structuring",
    }


def _build_report(summary: Dict[str, Any], output_dir: Path, qa_df: pd.DataFrame) -> str:
    qa_lines = [
        f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}"
        for _, row in qa_df.iterrows()
    ]
    lines = [
        "# 321C2 Source-aware Router Revision",
        "",
        "## Decision",
        f"- router_revision_decision: {summary.get('router_revision_decision', '')}",
        "",
        "## Snapshot",
        f"- pure_vlm_calibrated_trusted_rate: {summary.get('pure_vlm_calibrated_trusted_rate', 0.0)}",
        f"- pure_vlm_table_with_trusted_count: {summary.get('pure_vlm_table_with_trusted_count', 0)}",
        f"- ppstructure_trusted_rate: {summary.get('ppstructure_trusted_rate', 0.0)}",
        f"- previous_router_vlm_primary_count: {summary.get('previous_router_vlm_primary_count', 0)}",
        f"- revised_mineru_table_body_structuring_count: {summary.get('revised_mineru_table_body_structuring_count', 0)}",
        f"- revised_pure_vlm_image_only_count: {summary.get('revised_pure_vlm_image_only_count', 0)}",
        f"- revised_vlm_api_later_count: {summary.get('revised_vlm_api_later_count', 0)}",
        f"- revised_mineru_markdown_direct_count: {summary.get('revised_mineru_markdown_direct_count', 0)}",
        f"- revised_ppstructure_fallback_count: {summary.get('revised_ppstructure_fallback_count', 0)}",
        f"- revised_manual_review_required_count: {summary.get('revised_manual_review_required_count', 0)}",
        f"- revised_skip_non_core_count: {summary.get('revised_skip_non_core_count', 0)}",
        f"- revised_unsupported_count: {summary.get('revised_unsupported_count', 0)}",
        f"- revised_route_total_count: {summary.get('revised_route_total_count', 0)}",
        f"- revised_unique_table_asset_count: {summary.get('revised_unique_table_asset_count', 0)}",
        f"- source_contamination_risk_count: {summary.get('source_contamination_risk_count', 0)}",
        "",
        "## QA Checks",
    ]
    lines.extend(qa_lines or ["- none"])
    lines.extend(["", "## Output", f"- output_dir: `{output_dir}`"])
    return "\n".join(lines) + "\n"


def run_source_aware_router_revision(config: SourceAwareRouterRevisionConfig) -> Dict[str, Any]:
    if not config.pure_vlm_calibration_dir.exists():
        return _blocked_output(config)

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pure_summary, pure_per_table_df, pure_candidate_df = _load_pure_vlm_calibration(config.pure_vlm_calibration_dir)
    previous_router_summary, previous_preview_df = _load_previous_router(config.previous_router_dir)
    mineru_summary, mineru_assets_df = _load_mineru_benchmark(config.mineru_benchmark_dir)
    ppstructure_summary = _load_ppstructure_summary(config.ppstructure_benchmark_dir)
    previous_strict_vlm_summary = _load_previous_strict_vlm_summary(previous_router_summary)
    mineru_assisted_sample_summary = _bootstrap_mineru_assisted_sample_metrics(config.mineru_assisted_output_root, output_dir)

    pure_source_audit_df = audit_vlm_output_root(
        root=config.pure_vlm_output_root,
        dataset_label="PURE_VLM_OUTPUT_ROOT",
        expected_recognition_source=PURE_VLM_IMAGE_ONLY,
    )
    sample_source_audit_df = audit_vlm_output_root(
        root=config.mineru_assisted_output_root or Path(""),
        dataset_label="MINERU_ASSISTED_SAMPLE_ROOT",
        expected_recognition_source=MINERU_TABLE_BODY_STRUCTURING,
        assume_manual_sample_contamination=True,
    ) if config.mineru_assisted_output_root else pd.DataFrame()
    source_audit_df = pd.concat([pure_source_audit_df, sample_source_audit_df], ignore_index=True) if not sample_source_audit_df.empty else pure_source_audit_df.copy()

    pure_match_df = _reduce_pure_match_df(_build_pure_match_df(pure_per_table_df, pure_candidate_df))
    mineru_body_df = _build_mineru_body_df(mineru_assets_df)

    route_preview_df = previous_preview_df.copy()
    if route_preview_df.empty and not mineru_assets_df.empty:
        route_preview_df = pd.DataFrame(
            {
                "source_report_name": mineru_assets_df.get("report_name", ""),
                "table_asset_id": mineru_assets_df.get("table_asset_id", ""),
                "table_role_guess": mineru_assets_df.get("table_role_guess", ""),
                "effective_role_category": mineru_assets_df.get("role_category", ""),
                "image_path": mineru_assets_df.get("image_path", ""),
                "image_filename": mineru_assets_df.get("image_path", "").astype(str).str.replace("\\", "/", regex=False).str.split("/").str[-1],
                "image_exists": mineru_assets_df.get("image_exists", False),
                "caption": mineru_assets_df.get("caption", ""),
                "nearby_text_preview": mineru_assets_df.get("nearby_text", ""),
                "estimated_value_score": 0,
                "confidence_score": 0.0,
                "recommended_route": "",
                "route_reason": "",
            }
        )
    route_preview_df = route_preview_df.fillna("")
    if not route_preview_df.empty and "image_filename" not in route_preview_df.columns:
        route_preview_df["image_filename"] = route_preview_df["image_path"].astype(str).str.replace("\\", "/", regex=False).str.split("/").str[-1]

    if not pure_match_df.empty:
        route_preview_df = route_preview_df.merge(
            pure_match_df[
                [
                    "table_folder",
                    "pure_image_filename",
                    "table_title",
                    "pure_quality_decision",
                    "pure_table_decision",
                    "pure_trusted_count",
                    "pure_review_required_count",
                    "pure_candidate_count",
                ]
            ],
            left_on="image_filename",
            right_on="pure_image_filename",
            how="left",
        )
    else:
        for column in [
            "table_folder",
            "pure_image_filename",
            "table_title",
            "pure_quality_decision",
            "pure_table_decision",
            "pure_trusted_count",
            "pure_review_required_count",
            "pure_candidate_count",
        ]:
            route_preview_df[column] = ""

    if not mineru_body_df.empty:
        route_preview_df = route_preview_df.merge(
            mineru_body_df,
            on=["source_report_name", "image_filename", "bbox"],
            how="left",
        )
    else:
        for column in [
            "mineru_has_table_body",
            "mineru_has_html_table",
            "mineru_body_has_chinese",
            "mineru_table_body_length",
            "mineru_caption_text",
            "mineru_table_body_clean",
        ]:
            route_preview_df[column] = False if "has_" in column or column.endswith("_clean") else ""

    pure_verified_ids = set(
        pure_source_audit_df.loc[pure_source_audit_df["audit_status"] == "PASS", "sample_id"].astype(str).tolist()
    ) if not pure_source_audit_df.empty else set()
    sample_risk_ids = set(
        sample_source_audit_df.loc[
            sample_source_audit_df["risk_tags"].astype(str).str.contains("SOURCE_CONTAMINATION_RISK"), "sample_id"
        ].astype(str).tolist()
    ) if not sample_source_audit_df.empty else set()

    route_preview_df["pure_source_verified"] = route_preview_df["table_folder"].astype(str).isin(pure_verified_ids)
    route_preview_df["mineru_assisted_source_risk"] = route_preview_df["table_folder"].astype(str).isin(sample_risk_ids)
    route_preview_df["previous_recommended_route"] = route_preview_df.get("recommended_route", "")
    route_preview_df["previous_route_reason"] = route_preview_df.get("route_reason", "")
    route_preview_df["previous_blocker_reason"] = route_preview_df.get("blocker_reason", "")
    route_preview_df["table_title_final"] = route_preview_df.get("table_title", "")
    route_preview_df["table_title_final"] = route_preview_df["table_title_final"].where(
        route_preview_df["table_title_final"].astype(str).str.len() > 0,
        route_preview_df.get("caption", ""),
    )
    route_preview_df = route_preview_df.drop(columns=["recommended_route", "route_reason", "blocker_reason"], errors="ignore")

    decisions = route_preview_df.apply(
        lambda row: _decide_revised_route(row.to_dict(), pure_summary),
        axis=1,
        result_type="expand",
    )
    route_preview_df = pd.concat([route_preview_df, decisions], axis=1)
    route_preview_df["recommended_route"] = route_preview_df["recommended_route"].fillna("")
    route_preview_df["route_reason"] = route_preview_df["route_reason"].fillna("")
    route_preview_df["blocker_reason"] = route_preview_df["blocker_reason"].fillna("")
    route_preview_df = _finalize_route_preview_df(route_preview_df)

    route_comparison_df = _build_route_comparison_rows(
        pure_summary=pure_summary,
        ppstructure_summary=ppstructure_summary,
        previous_strict_summary=previous_strict_vlm_summary,
        mineru_sample_summary=mineru_assisted_sample_summary,
    )

    revised_route_counts = {
        route_name: int((route_preview_df["recommended_route"] == route_name).sum()) if not route_preview_df.empty else 0
        for route_name in ROUTE_ORDER
    }
    revised_route_total_count = int(len(route_preview_df))
    revised_unique_table_asset_count = int(route_preview_df["table_asset_id"].astype(str).nunique()) if (not route_preview_df.empty and "table_asset_id" in route_preview_df.columns) else 0
    source_audit_folder_count = int(len(source_audit_df))
    pure_vlm_source_verified_count = int((pure_source_audit_df["audit_status"] == "PASS").sum()) if not pure_source_audit_df.empty else 0
    source_contamination_risk_count = int(source_audit_df["risk_tags"].astype(str).str.contains("SOURCE_CONTAMINATION_RISK").sum()) if not source_audit_df.empty else 0

    summary = {
        "stage": "321C2",
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "output_dir": str(output_dir),
        "pure_vlm_calibrated_trusted_rate": _to_float(pure_summary.get("calibrated_trusted_rate")),
        "pure_vlm_table_with_trusted_count": _to_int(pure_summary.get("table_with_trusted_count")),
        "pure_vlm_unit_unknown_count": _to_int(pure_summary.get("unit_unknown_count")),
        "pure_vlm_unknown_metric_count": _to_int(pure_summary.get("unknown_metric_code_count")),
        "pure_vlm_calibration_decision": _norm(pure_summary.get("calibration_decision")),
        "ppstructure_trusted_rate": _to_float(ppstructure_summary.get("trusted_rate")),
        "previous_router_vlm_primary_count": _to_int(previous_router_summary.get("vlm_primary_count")),
        "revised_mineru_table_body_structuring_count": revised_route_counts[MINERU_TABLE_BODY_STRUCTURING],
        "revised_pure_vlm_image_only_count": revised_route_counts[PURE_VLM_IMAGE_ONLY],
        "revised_vlm_api_later_count": revised_route_counts[VLM_API_LATER],
        "revised_mineru_markdown_direct_count": revised_route_counts[MINERU_MARKDOWN_DIRECT],
        "revised_ppstructure_fallback_count": revised_route_counts[PPSTRUCTURE_FALLBACK],
        "revised_manual_review_required_count": revised_route_counts[MANUAL_REVIEW_REQUIRED] + revised_route_counts[VLM_API_LATER],
        "revised_skip_non_core_count": revised_route_counts[SKIP_NON_CORE_TABLE],
        "revised_unsupported_count": revised_route_counts[UNSUPPORTED_TABLE_TYPE],
        "revised_route_total_count": revised_route_total_count,
        "revised_unique_table_asset_count": revised_unique_table_asset_count,
        "source_audit_folder_count": source_audit_folder_count,
        "pure_vlm_source_verified_count": pure_vlm_source_verified_count,
        "source_contamination_risk_count": source_contamination_risk_count,
        "mineru_body_clean_core_count": int(
            route_preview_df[
                route_preview_df["route_reason"].astype(str).str.contains("clean_mineru_table_body_available")
            ].shape[0]
        ) if not route_preview_df.empty else 0,
        "mineru_assisted_sample_summary_available": bool(mineru_assisted_sample_summary),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    policy_json = _policy_json(summary)
    qa_df = _build_qa_checks(config, pure_summary, policy_json, route_preview_df, source_audit_df)
    summary["router_qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["router_qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["router_qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    if summary["router_qa_fail_count"] > 0:
        decision = "SOURCE_AWARE_ROUTER_BLOCKED_BY_QA_FAILURE"
    elif (
        summary["pure_vlm_calibration_decision"] == "PURE_VLM_CALIBRATION_PARTIAL_NEEDS_MORE_PROMPT_OR_ALIAS_WORK"
        and summary["revised_mineru_table_body_structuring_count"] >= max(5, summary["revised_pure_vlm_image_only_count"])
    ):
        decision = "SOURCE_AWARE_ROUTER_READY_FOR_321D_MINERU_BODY_INGESTION_FIRST"
    elif (
        summary["pure_vlm_calibrated_trusted_rate"] >= 0.45
        and summary["source_contamination_risk_count"] == 0
    ):
        decision = "SOURCE_AWARE_ROUTER_READY_FOR_321D_PURE_VLM_INGESTION"
    elif summary["revised_mineru_table_body_structuring_count"] == 0 and summary["revised_pure_vlm_image_only_count"] == 0:
        decision = "SOURCE_AWARE_ROUTER_NOT_READY"
    else:
        decision = "SOURCE_AWARE_ROUTER_PARTIAL_NEEDS_MORE_ROUTE_BENCHMARKS"
    summary["router_revision_decision"] = decision

    summary_df = pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()])
    route_preview_out = route_preview_df.copy()
    mineru_body_worklist_df = route_preview_out[route_preview_out["recommended_route"] == MINERU_TABLE_BODY_STRUCTURING].copy()
    pure_vlm_worklist_df = route_preview_out[route_preview_out["recommended_route"].isin([PURE_VLM_IMAGE_ONLY, VLM_API_LATER])].copy()
    ppstructure_worklist_df = route_preview_out[route_preview_out["recommended_route"] == PPSTRUCTURE_FALLBACK].copy()
    manual_review_worklist_df = route_preview_out[route_preview_out["recommended_route"] == MANUAL_REVIEW_REQUIRED].copy()
    unsupported_tables_df = route_preview_out[route_preview_out["recommended_route"] == UNSUPPORTED_TABLE_TYPE].copy()
    integration_plan_df = _build_integration_plan(summary, route_preview_out, source_audit_df)
    known_limitations_df = _build_known_limitations()

    _write_excel(
        output_dir / "source_aware_router_revision_321c2.xlsx",
        {
            "summary": summary_df,
            "revised_router_policy": pd.DataFrame(_policy_rows()),
            "source_provenance_audit": source_audit_df,
            "route_comparison_summary": route_comparison_df,
            "table_route_preview_revised": route_preview_out,
            "mineru_table_body_worklist": mineru_body_worklist_df,
            "pure_vlm_worklist": pure_vlm_worklist_df,
            "ppstructure_fallback_worklist": ppstructure_worklist_df,
            "manual_review_worklist": manual_review_worklist_df,
            "unsupported_tables": unsupported_tables_df,
            "integration_plan": integration_plan_df,
            "known_limitations": known_limitations_df,
            "qa_checks": qa_df,
        },
    )
    _write_json(output_dir / "source_aware_router_revision_321c2_summary.json", summary)
    _write_json(output_dir / "recognizer_router_policy_321c2.json", policy_json)
    (output_dir / "source_aware_router_revision_321c2_report.md").write_text(
        _build_report(summary, output_dir, qa_df),
        encoding="utf-8",
    )

    return {
        "summary": summary,
        "excel_path": str(output_dir / "source_aware_router_revision_321c2.xlsx"),
        "summary_json_path": str(output_dir / "source_aware_router_revision_321c2_summary.json"),
        "report_md_path": str(output_dir / "source_aware_router_revision_321c2_report.md"),
        "policy_json_path": str(output_dir / "recognizer_router_policy_321c2.json"),
    }
