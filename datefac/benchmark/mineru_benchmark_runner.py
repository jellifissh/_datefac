from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from datefac.domain.table_asset import TableAssetWarning
from datefac.parser.mineru_output_reader import MineruReadResult, read_mineru_output


ROLE_KEYS = [
    "CORE_METRIC_TABLE",
    "FINANCIAL_FORECAST_VALUATION",
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "BUSINESS_ASSUMPTION",
    "BASIC_DATA",
    "RATING_STANDARD",
    "DISCLAIMER_OR_LEGAL",
    "CHART_OR_MARKET_TREND",
    "UNKNOWN_TABLE",
]


@dataclass
class RunnerConfig:
    mineru_output_root: Path
    output_dir: Path
    min_report_count: int = 5
    exclude_names: Optional[Set[str]] = None
    include_name_regex: Optional[str] = None


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    s = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _json_dump(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _has_kind(source_files: List[Dict[str, Any]], kind: str) -> bool:
    for row in source_files:
        if _norm(row.get("source_kind")) == kind and _to_bool(row.get("file_exists", True)):
            return True
    return False


def _scan_report_dirs(root: Path, exclude_names: Set[str], include_regex: Optional[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    regex = re.compile(include_regex) if include_regex else None
    for p in sorted([x for x in root.iterdir() if x.is_dir()]):
        name = p.name
        include = True
        reason = "selected"
        if name in exclude_names:
            include = False
            reason = "excluded_by_name"
        if include and regex is not None and not regex.search(name):
            include = False
            reason = "excluded_by_include_regex"
        rows.append(
            {
                "report_name": name,
                "mineru_output_dir": str(p),
                "is_selected": include,
                "selection_reason": reason,
            }
        )
    return rows


def _to_asset_row(report_name: str, asset: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(asset)
    out["report_name"] = report_name
    out["role_category"] = _norm(asset.get("extra", {}).get("role_category") if isinstance(asset.get("extra"), dict) else "")
    out["role_confidence"] = _norm(asset.get("extra", {}).get("role_confidence") if isinstance(asset.get("extra"), dict) else "")
    out["core_signal_hit"] = bool(asset.get("extra", {}).get("core_signal_hit", False)) if isinstance(asset.get("extra"), dict) else False
    out["image_path_raw"] = _norm(asset.get("extra", {}).get("image_path_raw") if isinstance(asset.get("extra"), dict) else "")
    out["image_path_resolved"] = _norm(asset.get("extra", {}).get("image_path_resolved") if isinstance(asset.get("extra"), dict) else _norm(asset.get("image_path")))
    out["image_exists"] = bool(asset.get("extra", {}).get("image_exists", False)) if isinstance(asset.get("extra"), dict) else False
    out["bbox_missing"] = asset.get("bbox") is None
    return out


def _warning_row(report_name: str, warning: TableAssetWarning) -> Dict[str, Any]:
    d = warning.to_dict()
    d["report_name"] = report_name
    return d


def _role_counter() -> Dict[str, int]:
    return {k: 0 for k in ROLE_KEYS}


def _compute_report_status(
    missing_content_list: bool,
    table_asset_count: int,
    unknown_rate: float,
    core_metric_count: int,
) -> str:
    if missing_content_list or table_asset_count == 0:
        return "FAILED_OR_INCOMPLETE"
    if unknown_rate > 0.60:
        return "WARN_HIGH_UNKNOWN_TABLE_RATE"
    if core_metric_count == 0:
        return "WARN_LOW_CORE_TABLE_DETECTION"
    return "PASS"


def run_mineru_benchmark(config: RunnerConfig) -> Dict[str, Any]:
    root = config.mineru_output_root.resolve()
    out_dir = config.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    excludes = set(config.exclude_names or set())

    source_rows = _scan_report_dirs(root, excludes, config.include_name_regex)
    selected = [x for x in source_rows if x["is_selected"]]

    per_report_rows: List[Dict[str, Any]] = []
    table_assets_all_rows: List[Dict[str, Any]] = []
    warnings_all_rows: List[Dict[str, Any]] = []

    for row in selected:
        report_name = _norm(row["report_name"])
        report_dir = Path(row["mineru_output_dir"])
        try:
            res: MineruReadResult = read_mineru_output(report_dir)
        except Exception as exc:
            per_report_rows.append(
                {
                    "report_name": report_name,
                    "mineru_output_dir": str(report_dir),
                    "benchmark_status": "FAILED_OR_INCOMPLETE",
                    "content_list_found": False,
                    "content_list_v2_found": False,
                    "markdown_found": False,
                    "source_file_count": 0,
                    "table_asset_count": 0,
                    "image_path_raw_count": 0,
                    "image_resolved_exists_count": 0,
                    "image_path_missing_count": 0,
                    "image_path_resolve_failed_count": 0,
                    "bbox_missing_count": 0,
                    "warning_count": 1,
                    "role_counts": "{}",
                    "status_counts": json.dumps({"FAILED_OR_INCOMPLETE": 1}, ensure_ascii=False),
                    "core_metric_table_count": 0,
                    "financial_forecast_table_count": 0,
                    "balance_sheet_count": 0,
                    "income_statement_count": 0,
                    "cash_flow_statement_count": 0,
                    "business_assumption_count": 0,
                    "basic_data_count": 0,
                    "rating_standard_count": 0,
                    "disclaimer_or_legal_count": 0,
                    "unknown_table_count": 0,
                    "core_signal_hit_count": 0,
                    "role_guess_confidence_distribution": "{}",
                }
            )
            warnings_all_rows.append(
                {
                    "report_name": report_name,
                    "source_file": str(report_dir),
                    "warning_code": "reader_exception",
                    "warning_message": f"{exc}",
                    "block_index": None,
                    "block_id": "",
                }
            )
            continue

        summary = res.summary()
        source_files_rows = [s.to_dict() for s in res.source_files]
        content_list_found = _has_kind(source_files_rows, "content_list") or _has_kind(source_files_rows, "generic_json")
        content_list_v2_found = _has_kind(source_files_rows, "content_list_v2")
        markdown_found = _has_kind(source_files_rows, "markdown")

        role_counts = _role_counter()
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        core_signal_hit_count = 0

        for a in res.table_assets:
            ad = a.to_dict()
            asset_row = _to_asset_row(report_name, ad)
            rc = _norm(asset_row.get("role_category"))
            if rc in role_counts:
                role_counts[rc] += 1
            else:
                role_counts["UNKNOWN_TABLE"] += 1
            conf = _norm(asset_row.get("role_confidence")).lower() or "low"
            if conf not in confidence_counts:
                conf = "low"
            confidence_counts[conf] += 1
            if bool(asset_row.get("core_signal_hit", False)):
                core_signal_hit_count += 1
            table_assets_all_rows.append(asset_row)

        for w in res.warnings:
            warnings_all_rows.append(_warning_row(report_name, w))

        table_asset_count = len(res.table_assets)
        unknown_count = role_counts["UNKNOWN_TABLE"]
        unknown_rate = float(unknown_count / table_asset_count) if table_asset_count > 0 else 1.0

        benchmark_status = _compute_report_status(
            missing_content_list=not content_list_found,
            table_asset_count=table_asset_count,
            unknown_rate=unknown_rate,
            core_metric_count=role_counts["CORE_METRIC_TABLE"],
        )

        status_counts = {
            "READY_FOR_REVIEW": max(table_asset_count - int(summary.get("table_image_missing_count", 0)) - int(summary.get("image_path_resolve_failed_count", 0)), 0),
            "IMAGE_PATH_MISSING": int(summary.get("table_image_missing_count", 0)),
            "IMAGE_PATH_RESOLVE_FAILED": int(summary.get("image_path_resolve_failed_count", 0)),
        }

        per_report_rows.append(
            {
                "report_name": report_name,
                "mineru_output_dir": str(report_dir),
                "benchmark_status": benchmark_status,
                "content_list_found": content_list_found,
                "content_list_v2_found": content_list_v2_found,
                "markdown_found": markdown_found,
                "source_file_count": len(source_files_rows),
                "table_asset_count": table_asset_count,
                "image_path_raw_count": int(round(summary.get("image_path_raw_coverage_rate", 0.0) * table_asset_count)),
                "image_resolved_exists_count": int(round(summary.get("image_path_resolved_exists_rate", 0.0) * table_asset_count)),
                "image_path_missing_count": int(summary.get("table_image_missing_count", 0)),
                "image_path_resolve_failed_count": int(summary.get("image_path_resolve_failed_count", 0)),
                "bbox_missing_count": int(sum(1 for x in res.table_assets if x.bbox is None)),
                "warning_count": len(res.warnings),
                "role_counts": json.dumps(role_counts, ensure_ascii=False),
                "status_counts": json.dumps(status_counts, ensure_ascii=False),
                "core_metric_table_count": role_counts["CORE_METRIC_TABLE"],
                "financial_forecast_table_count": role_counts["FINANCIAL_FORECAST_VALUATION"],
                "balance_sheet_count": role_counts["BALANCE_SHEET"],
                "income_statement_count": role_counts["INCOME_STATEMENT"],
                "cash_flow_statement_count": role_counts["CASH_FLOW_STATEMENT"],
                "business_assumption_count": role_counts["BUSINESS_ASSUMPTION"],
                "basic_data_count": role_counts["BASIC_DATA"],
                "rating_standard_count": role_counts["RATING_STANDARD"],
                "disclaimer_or_legal_count": role_counts["DISCLAIMER_OR_LEGAL"],
                "unknown_table_count": role_counts["UNKNOWN_TABLE"],
                "core_signal_hit_count": core_signal_hit_count,
                "role_guess_confidence_distribution": json.dumps(confidence_counts, ensure_ascii=False),
            }
        )

    per_report_df = pd.DataFrame(per_report_rows)
    if per_report_df.empty:
        per_report_df = pd.DataFrame(
            columns=[
                "report_name",
                "mineru_output_dir",
                "benchmark_status",
                "content_list_found",
                "content_list_v2_found",
                "markdown_found",
                "source_file_count",
                "table_asset_count",
                "image_path_raw_count",
                "image_resolved_exists_count",
                "image_path_missing_count",
                "image_path_resolve_failed_count",
                "bbox_missing_count",
                "warning_count",
                "role_counts",
                "status_counts",
                "core_metric_table_count",
                "financial_forecast_table_count",
                "balance_sheet_count",
                "income_statement_count",
                "cash_flow_statement_count",
                "business_assumption_count",
                "basic_data_count",
                "rating_standard_count",
                "disclaimer_or_legal_count",
                "unknown_table_count",
                "core_signal_hit_count",
                "role_guess_confidence_distribution",
            ]
        )

    table_assets_df = pd.DataFrame(table_assets_all_rows)
    if table_assets_df.empty:
        table_assets_df = pd.DataFrame(
            columns=[
                "report_name",
                "source_file",
                "page_idx",
                "bbox",
                "image_path",
                "image_path_raw",
                "image_path_resolved",
                "image_exists",
                "bbox_missing",
                "caption",
                "footnote",
                "nearby_text",
                "table_role_guess",
                "role_category",
                "role_confidence",
                "core_signal_hit",
            ]
        )

    warnings_df = pd.DataFrame(warnings_all_rows)
    if warnings_df.empty:
        warnings_df = pd.DataFrame(columns=["report_name", "source_file", "warning_code", "warning_message", "block_index", "block_id"])

    report_count = int(len(per_report_df))
    parsed_report_count = int((per_report_df["benchmark_status"] != "FAILED_OR_INCOMPLETE").sum()) if report_count else 0
    failed_report_count = int((per_report_df["benchmark_status"] == "FAILED_OR_INCOMPLETE").sum()) if report_count else 0
    total_table_asset_count = int(per_report_df["table_asset_count"].sum()) if report_count else 0
    total_warning_count = int(per_report_df["warning_count"].sum()) if report_count else int(len(warnings_df))

    image_path_raw_count = int(per_report_df["image_path_raw_count"].sum()) if report_count else 0
    image_resolved_exists_count = int(per_report_df["image_resolved_exists_count"].sum()) if report_count else 0
    table_image_missing_count = int(per_report_df["image_path_missing_count"].sum()) if report_count else 0
    image_path_resolve_failed_count = int(per_report_df["image_path_resolve_failed_count"].sum()) if report_count else 0
    bbox_missing_count_total = int(per_report_df["bbox_missing_count"].sum()) if report_count else 0
    bbox_present_count = max(total_table_asset_count - bbox_missing_count_total, 0)

    image_path_raw_coverage_rate = float(image_path_raw_count / total_table_asset_count) if total_table_asset_count > 0 else 0.0
    image_path_resolved_exists_rate = float(image_resolved_exists_count / total_table_asset_count) if total_table_asset_count > 0 else 0.0
    bbox_coverage_rate = float(bbox_present_count / total_table_asset_count) if total_table_asset_count > 0 else 0.0

    unknown_total = int(per_report_df["unknown_table_count"].sum()) if report_count else 0
    unknown_table_rate = float(unknown_total / total_table_asset_count) if total_table_asset_count > 0 else 1.0
    unknown_table_sample_count = min(20, unknown_total)

    core_detected_report_count = int((per_report_df["core_metric_table_count"] > 0).sum()) if report_count else 0
    core_table_detected_rate = float(core_detected_report_count / parsed_report_count) if parsed_report_count > 0 else 0.0
    core_signal_hit_count = int(per_report_df["core_signal_hit_count"].sum()) if report_count else 0
    core_signal_hit_rate = float(core_signal_hit_count / total_table_asset_count) if total_table_asset_count > 0 else 0.0

    fin_stmt_detected_report_count = 0
    business_assumption_detected_report_count = 0
    if report_count:
        fin_stmt_detected_report_count = int(
            (
                (per_report_df["balance_sheet_count"] > 0)
                | (per_report_df["income_statement_count"] > 0)
                | (per_report_df["cash_flow_statement_count"] > 0)
            ).sum()
        )
        business_assumption_detected_report_count = int((per_report_df["business_assumption_count"] > 0).sum())

    avg_table_asset_per_report = float(total_table_asset_count / parsed_report_count) if parsed_report_count > 0 else 0.0

    # updated 320B2 parser decision rules
    if (
        parsed_report_count >= 5
        and image_path_raw_coverage_rate >= 0.90
        and image_path_resolved_exists_rate >= 0.80
        and bbox_coverage_rate >= 0.90
        and core_table_detected_rate >= 0.60
    ):
        parser_decision = "MINERU_ASSET_LAYER_NEEDS_TABLE_RECOGNITION_NEXT"
    elif image_path_raw_coverage_rate < 0.70 and bbox_coverage_rate >= 0.90:
        parser_decision = "MINERU_LAYOUT_OK_IMAGE_PATH_READER_NEEDS_FIX"
    elif core_table_detected_rate < 0.40:
        parser_decision = "ROLE_CLASSIFIER_NEEDS_CALIBRATION"
    else:
        parser_decision = "NEED_MORE_BENCHMARK_OR_FALLBACK"

    benchmark_status = "PASS"
    if parsed_report_count < config.min_report_count:
        benchmark_status = "WARN_INSUFFICIENT_REPORT_COUNT"
    elif unknown_table_rate > 0.60:
        benchmark_status = "WARN_HIGH_UNKNOWN_TABLE_RATE"
    elif core_table_detected_rate < 0.40:
        benchmark_status = "WARN_LOW_CORE_TABLE_DETECTION"

    # confidence distribution
    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    if "role_confidence" in table_assets_df.columns and len(table_assets_df):
        for k in confidence_dist.keys():
            confidence_dist[k] = int((table_assets_df["role_confidence"].str.lower() == k).sum())

    summary_payload = {
        "source_dir": str(root),
        "report_count": report_count,
        "parsed_report_count": parsed_report_count,
        "failed_report_count": failed_report_count,
        "total_table_asset_count": total_table_asset_count,
        "avg_table_asset_per_report": round(avg_table_asset_per_report, 6),
        "image_path_raw_coverage_rate": round(image_path_raw_coverage_rate, 6),
        "image_path_resolved_exists_rate": round(image_path_resolved_exists_rate, 6),
        "bbox_coverage_rate": round(bbox_coverage_rate, 6),
        "table_image_missing_count": table_image_missing_count,
        "image_path_resolve_failed_count": image_path_resolve_failed_count,
        "unknown_table_rate_before_or_current": round(unknown_table_rate, 6),
        "unknown_table_sample_count": unknown_table_sample_count,
        "core_table_detected_report_count": core_detected_report_count,
        "core_table_detected_rate": round(core_table_detected_rate, 6),
        "core_signal_hit_count": core_signal_hit_count,
        "core_signal_hit_rate": round(core_signal_hit_rate, 6),
        "financial_statement_detected_report_count": fin_stmt_detected_report_count,
        "business_assumption_detected_report_count": business_assumption_detected_report_count,
        "role_guess_confidence_distribution": confidence_dist,
        "total_warning_count": total_warning_count,
        "parser_decision": parser_decision,
        "benchmark_status": benchmark_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    role_counts_global = pd.DataFrame(
        [{"role_category": k, "count": int(per_report_df[f"{k.lower()}_count"].sum()) if False else int((table_assets_df["role_category"] == k).sum()) if "role_category" in table_assets_df.columns else 0} for k in ROLE_KEYS]
    )
    warning_summary_df = (
        warnings_df.groupby(["warning_code"], dropna=False).size().reset_index(name="count").sort_values("count", ascending=False)
        if not warnings_df.empty
        else pd.DataFrame(columns=["warning_code", "count"])
    )

    image_path_diagnostics_df = pd.DataFrame(
        [
            {"metric": "image_path_raw_count", "value": image_path_raw_count},
            {"metric": "image_resolved_exists_count", "value": image_resolved_exists_count},
            {"metric": "table_image_missing_count", "value": table_image_missing_count},
            {"metric": "image_path_resolve_failed_count", "value": image_path_resolve_failed_count},
            {"metric": "image_path_raw_coverage_rate", "value": round(image_path_raw_coverage_rate, 6)},
            {"metric": "image_path_resolved_exists_rate", "value": round(image_path_resolved_exists_rate, 6)},
        ]
    )
    core_table_diag_df = pd.DataFrame(
        [
            {"metric": "core_table_detected_report_count", "value": core_detected_report_count},
            {"metric": "core_table_detected_rate", "value": round(core_table_detected_rate, 6)},
            {"metric": "core_signal_hit_count", "value": core_signal_hit_count},
            {"metric": "core_signal_hit_rate", "value": round(core_signal_hit_rate, 6)},
            {"metric": "unknown_table_rate_before_or_current", "value": round(unknown_table_rate, 6)},
            {"metric": "role_guess_confidence_distribution", "value": json.dumps(confidence_dist, ensure_ascii=False)},
        ]
    )
    unknown_samples_df = (
        table_assets_df[table_assets_df["role_category"] == "UNKNOWN_TABLE"].head(unknown_table_sample_count).copy()
        if "role_category" in table_assets_df.columns and len(table_assets_df)
        else pd.DataFrame(columns=table_assets_df.columns)
    )
    missing_image_df = table_assets_df[table_assets_df["image_exists"] == False].copy() if "image_exists" in table_assets_df.columns else pd.DataFrame(columns=table_assets_df.columns)
    failed_reports_df = per_report_df[per_report_df["benchmark_status"] == "FAILED_OR_INCOMPLETE"].copy() if report_count else pd.DataFrame(columns=per_report_df.columns)

    parser_decision_df = pd.DataFrame(
        [
            {"metric": "benchmark_status", "value": benchmark_status},
            {"metric": "parser_decision", "value": parser_decision},
            {"metric": "threshold_parsed_report_count", "value": ">=5"},
            {"metric": "threshold_image_path_raw_coverage_rate", "value": ">=0.90"},
            {"metric": "threshold_image_path_resolved_exists_rate", "value": ">=0.80"},
            {"metric": "threshold_bbox_coverage_rate", "value": ">=0.90"},
            {"metric": "threshold_core_table_detected_rate", "value": ">=0.60"},
            {"metric": "actual_parsed_report_count", "value": parsed_report_count},
            {"metric": "actual_image_path_raw_coverage_rate", "value": round(image_path_raw_coverage_rate, 6)},
            {"metric": "actual_image_path_resolved_exists_rate", "value": round(image_path_resolved_exists_rate, 6)},
            {"metric": "actual_bbox_coverage_rate", "value": round(bbox_coverage_rate, 6)},
            {"metric": "actual_core_table_detected_rate", "value": round(core_table_detected_rate, 6)},
        ]
    )

    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary_payload.items()])

    excel_path = out_dir / "mineru_benchmark_320b2.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "per_report": per_report_df,
            "table_assets_all": table_assets_df,
            "role_counts": role_counts_global,
            "warning_summary": warning_summary_df,
            "image_path_diagnostics": image_path_diagnostics_df,
            "core_table_detection_diagnostics": core_table_diag_df,
            "unknown_table_samples": unknown_samples_df,
            "missing_image_cases": missing_image_df,
            "failed_reports": failed_reports_df,
            "parser_decision": parser_decision_df,
        },
    )

    summary_json_path = out_dir / "mineru_benchmark_320b2_summary.json"
    _json_dump(summary_json_path, summary_payload)

    report_md_path = out_dir / "mineru_benchmark_320b2_report.md"
    recommendation = (
        "MinerU 资产层可进入下一阶段表格识别评估（仍建议保持 sandbox 门控）。"
        if parser_decision == "MINERU_ASSET_LAYER_NEEDS_TABLE_RECOGNITION_NEXT"
        else "建议继续校准 image path resolver 与 role 规则，再评估是否进入 320C。"
    )
    report_lines = [
        "# MinerU Benchmark 320B2 Report",
        "",
        "## Input",
        f"- benchmark_root: `{root}`",
        "",
        "## Snapshot",
        f"- report_count: {report_count}",
        f"- parsed_report_count: {parsed_report_count}",
        f"- failed_report_count: {failed_report_count}",
        f"- total_table_asset_count: {total_table_asset_count}",
        f"- image_path_raw_coverage_rate: {summary_payload['image_path_raw_coverage_rate']}",
        f"- image_path_resolved_exists_rate: {summary_payload['image_path_resolved_exists_rate']}",
        f"- bbox_coverage_rate: {summary_payload['bbox_coverage_rate']}",
        f"- core_table_detected_rate: {summary_payload['core_table_detected_rate']}",
        f"- unknown_table_rate_before_or_current: {summary_payload['unknown_table_rate_before_or_current']}",
        f"- parser_decision: {parser_decision}",
        "",
        "## Next Recommendation",
        f"- {recommendation}",
        "",
        "## Output",
        f"- excel: `{excel_path}`",
        f"- summary_json: `{summary_json_path}`",
        f"- report_md: `{report_md_path}`",
    ]
    report_md_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
        "summary": summary_payload,
    }

