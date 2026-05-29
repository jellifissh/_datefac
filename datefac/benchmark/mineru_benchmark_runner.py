from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

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


def _deterministic_role_classify(caption: str, footnote: str, nearby_text: str, raw_guess: str, raw_block_type: str) -> str:
    text = f"{caption} {footnote} {nearby_text}".lower()
    rg = _norm(raw_guess).lower()
    bt = _norm(raw_block_type).lower()

    if "disclaimer" in text or "免责声明" in text or "重要声明" in text or "分析师声明" in text:
        return "DISCLAIMER_OR_LEGAL"
    if "评级标准" in text or "优于大市" in text or "弱于大市" in text or "rating" in text:
        return "RATING_STANDARD"
    if "基础数据" in text or "收盘价" in text or "总市值" in text or "basic data" in text:
        return "BASIC_DATA"
    if "主营业务假设" in text or "业务假设" in text or "毛利率" in text and "假设" in text:
        return "BUSINESS_ASSUMPTION"
    if "现金流量表" in text or "经营活动现金流" in text or "投资活动现金流" in text or "融资活动现金流" in text:
        return "CASH_FLOW_STATEMENT"
    if "利润表" in text or "营业收入" in text or "营业成本" in text or "归属于母公司净利润" in text:
        return "INCOME_STATEMENT"
    if "资产负债表" in text or "资产总计" in text or "负债合计" in text or "股东权益" in text:
        return "BALANCE_SHEET"
    if (
        "财务预测与估值" in text
        or "关键财务与估值指标" in text
        or "估值" in text
        or "ev/ebitda" in text
        or "p/e" in text
        or "p/b" in text
        or rg in {"valuation_table", "forecast_table"}
    ):
        return "FINANCIAL_FORECAST_VALUATION"
    if (
        "盈利预测和财务指标" in text
        or "每股收益" in text
        or "roe" in text
        or "eps" in text
        or "营业收入" in text
        or "归母净利润" in text
        or rg == "core_metric_table"
    ):
        return "CORE_METRIC_TABLE"
    if "chart" in bt or "plot" in bt or "trend" in text or "走势图" in text:
        return "CHART_OR_MARKET_TREND"
    return "UNKNOWN_TABLE"


def _role_counter() -> Dict[str, int]:
    return {k: 0 for k in ROLE_KEYS}


def _compute_report_status(row: Dict[str, Any], unknown_rate: float) -> str:
    if _norm(row.get("benchmark_status")) == "FAILED_OR_INCOMPLETE":
        return "FAILED_OR_INCOMPLETE"
    if unknown_rate > 0.60:
        return "WARN_HIGH_UNKNOWN_TABLE_RATE"
    if int(row.get("core_metric_table_count", 0)) == 0:
        return "WARN_LOW_CORE_TABLE_DETECTION"
    return "PASS"


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


def _to_asset_row(report_name: str, asset: Dict[str, Any], role_category: str, image_exists: bool, bbox_missing: bool) -> Dict[str, Any]:
    out = dict(asset)
    out["report_name"] = report_name
    out["role_category"] = role_category
    out["image_exists"] = image_exists
    out["bbox_missing"] = bbox_missing
    return out


def _warning_row(report_name: str, warning: TableAssetWarning) -> Dict[str, Any]:
    d = warning.to_dict()
    d["report_name"] = report_name
    return d


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
                    "image_missing_count": 0,
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

        source_files_rows = [s.to_dict() for s in res.source_files]
        content_list_found = _has_kind(source_files_rows, "content_list") or _has_kind(source_files_rows, "generic_json")
        content_list_v2_found = _has_kind(source_files_rows, "content_list_v2")
        markdown_found = _has_kind(source_files_rows, "markdown")

        role_counts = _role_counter()
        image_missing_count = 0
        bbox_missing_count = 0
        for a in res.table_assets:
            ad = a.to_dict()
            image_path = _norm(ad.get("image_path"))
            image_exists = bool(image_path and Path(image_path).exists())
            bbox_missing = ad.get("bbox") is None
            role_category = _deterministic_role_classify(
                caption=_norm(ad.get("caption")),
                footnote=_norm(ad.get("footnote")),
                nearby_text=_norm(ad.get("nearby_text")),
                raw_guess=_norm(ad.get("table_role_guess")),
                raw_block_type=_norm(ad.get("raw_block_type")),
            )
            role_counts[role_category] = role_counts.get(role_category, 0) + 1
            if not image_exists:
                image_missing_count += 1
            if bbox_missing:
                bbox_missing_count += 1
            table_assets_all_rows.append(_to_asset_row(report_name, ad, role_category, image_exists, bbox_missing))

        for w in res.warnings:
            warnings_all_rows.append(_warning_row(report_name, w))

        table_asset_count = len(res.table_assets)
        warning_count = len(res.warnings)
        unknown_count = role_counts["UNKNOWN_TABLE"]
        unknown_rate = float(unknown_count / table_asset_count) if table_asset_count > 0 else 1.0
        status_counts = {"READY_FOR_REVIEW": max(table_asset_count - image_missing_count - bbox_missing_count, 0), "IMAGE_MISSING": image_missing_count, "BBOX_MISSING": bbox_missing_count}

        initial_status = "PASS"
        if not content_list_found:
            initial_status = "FAILED_OR_INCOMPLETE"
            warnings_all_rows.append(
                {
                    "report_name": report_name,
                    "source_file": str(report_dir),
                    "warning_code": "missing_content_list",
                    "warning_message": "该报告目录缺少 *_content_list.json 或 generic json。",
                    "block_index": None,
                    "block_id": "",
                }
            )
            warning_count += 1
        if table_asset_count == 0:
            initial_status = "FAILED_OR_INCOMPLETE"

        report_row: Dict[str, Any] = {
            "report_name": report_name,
            "mineru_output_dir": str(report_dir),
            "benchmark_status": initial_status,
            "content_list_found": content_list_found,
            "content_list_v2_found": content_list_v2_found,
            "markdown_found": markdown_found,
            "source_file_count": len(source_files_rows),
            "table_asset_count": table_asset_count,
            "image_missing_count": image_missing_count,
            "bbox_missing_count": bbox_missing_count,
            "warning_count": warning_count,
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
        }
        report_row["benchmark_status"] = _compute_report_status(report_row, unknown_rate)
        if initial_status == "FAILED_OR_INCOMPLETE":
            report_row["benchmark_status"] = "FAILED_OR_INCOMPLETE"
        per_report_rows.append(report_row)

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
                "image_missing_count",
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
            ]
        )

    table_assets_df = pd.DataFrame(table_assets_all_rows)
    if table_assets_df.empty:
        table_assets_df = pd.DataFrame(columns=["report_name", "source_file", "page_idx", "bbox", "image_path", "image_exists", "bbox_missing", "caption", "footnote", "nearby_text", "table_role_guess", "role_category"])

    warnings_df = pd.DataFrame(warnings_all_rows)
    if warnings_df.empty:
        warnings_df = pd.DataFrame(columns=["report_name", "source_file", "warning_code", "warning_message", "block_index", "block_id"])

    parsed_report_count = int((per_report_df["benchmark_status"] != "FAILED_OR_INCOMPLETE").sum()) if not per_report_df.empty else 0
    failed_report_count = int((per_report_df["benchmark_status"] == "FAILED_OR_INCOMPLETE").sum()) if not per_report_df.empty else 0
    report_count = int(len(per_report_df))
    total_table_asset_count = int(per_report_df["table_asset_count"].sum()) if not per_report_df.empty else 0
    total_warning_count = int(per_report_df["warning_count"].sum()) if not per_report_df.empty else int(len(warnings_df))

    image_exists_count = int(table_assets_df["image_exists"].sum()) if "image_exists" in table_assets_df.columns and len(table_assets_df) else 0
    bbox_present_count = int((~table_assets_df["bbox_missing"]).sum()) if "bbox_missing" in table_assets_df.columns and len(table_assets_df) else 0
    image_path_coverage_rate = float(image_exists_count / total_table_asset_count) if total_table_asset_count > 0 else 0.0
    bbox_coverage_rate = float(bbox_present_count / total_table_asset_count) if total_table_asset_count > 0 else 0.0
    unknown_total = int((table_assets_df["role_category"] == "UNKNOWN_TABLE").sum()) if "role_category" in table_assets_df.columns else 0
    unknown_table_rate = float(unknown_total / total_table_asset_count) if total_table_asset_count > 0 else 1.0

    core_detected_report_count = int((per_report_df["core_metric_table_count"] > 0).sum()) if not per_report_df.empty else 0
    core_table_detected_rate = float(core_detected_report_count / parsed_report_count) if parsed_report_count > 0 else 0.0

    fin_stmt_detected_report_count = 0
    business_assumption_detected_report_count = 0
    if not per_report_df.empty:
        fin_stmt_detected_report_count = int(
            (
                (per_report_df["balance_sheet_count"] > 0)
                | (per_report_df["income_statement_count"] > 0)
                | (per_report_df["cash_flow_statement_count"] > 0)
            ).sum()
        )
        business_assumption_detected_report_count = int((per_report_df["business_assumption_count"] > 0).sum())

    avg_table_asset_per_report = float(total_table_asset_count / parsed_report_count) if parsed_report_count > 0 else 0.0

    parser_decision = "NEED_MORE_BENCHMARK_OR_FALLBACK"
    if (
        parsed_report_count >= 5
        and image_path_coverage_rate >= 0.95
        and bbox_coverage_rate >= 0.90
        and core_table_detected_rate >= 0.80
    ):
        parser_decision = "MINERU_CANDIDATE_PRIMARY_PARSER"

    benchmark_status = "PASS"
    if parsed_report_count < config.min_report_count:
        benchmark_status = "WARN_INSUFFICIENT_REPORT_COUNT"
    elif unknown_table_rate > 0.60:
        benchmark_status = "WARN_HIGH_UNKNOWN_TABLE_RATE"
    elif core_table_detected_rate < 0.80:
        benchmark_status = "WARN_LOW_CORE_TABLE_DETECTION"

    summary_payload = {
        "source_dir": str(root),
        "report_count": report_count,
        "parsed_report_count": parsed_report_count,
        "failed_report_count": failed_report_count,
        "total_table_asset_count": total_table_asset_count,
        "avg_table_asset_per_report": round(avg_table_asset_per_report, 6),
        "image_path_coverage_rate": round(image_path_coverage_rate, 6),
        "bbox_coverage_rate": round(bbox_coverage_rate, 6),
        "unknown_table_rate": round(unknown_table_rate, 6),
        "core_table_detected_report_count": core_detected_report_count,
        "core_table_detected_rate": round(core_table_detected_rate, 6),
        "financial_statement_detected_report_count": fin_stmt_detected_report_count,
        "business_assumption_detected_report_count": business_assumption_detected_report_count,
        "total_warning_count": total_warning_count,
        "parser_decision": parser_decision,
        "benchmark_status": benchmark_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    role_counts_global = pd.DataFrame(
        [{"role_category": k, "count": int((table_assets_df["role_category"] == k).sum()) if "role_category" in table_assets_df.columns else 0} for k in ROLE_KEYS]
    )
    warning_summary_df = (
        warnings_df.groupby(["warning_code"], dropna=False).size().reset_index(name="count").sort_values("count", ascending=False)
        if not warnings_df.empty
        else pd.DataFrame(columns=["warning_code", "count"])
    )
    missing_image_df = table_assets_df[table_assets_df["image_exists"] == False].copy() if "image_exists" in table_assets_df.columns else pd.DataFrame(columns=table_assets_df.columns)
    missing_bbox_df = table_assets_df[table_assets_df["bbox_missing"] == True].copy() if "bbox_missing" in table_assets_df.columns else pd.DataFrame(columns=table_assets_df.columns)
    failed_reports_df = per_report_df[per_report_df["benchmark_status"] == "FAILED_OR_INCOMPLETE"].copy() if not per_report_df.empty else pd.DataFrame(columns=per_report_df.columns)

    decision_df = pd.DataFrame(
        [
            {"metric": "benchmark_status", "value": benchmark_status},
            {"metric": "parser_decision", "value": parser_decision},
            {"metric": "threshold_parsed_report_count", "value": ">=5"},
            {"metric": "threshold_image_path_coverage_rate", "value": ">=0.95"},
            {"metric": "threshold_bbox_coverage_rate", "value": ">=0.90"},
            {"metric": "threshold_core_table_detected_rate", "value": ">=0.80"},
            {"metric": "actual_parsed_report_count", "value": parsed_report_count},
            {"metric": "actual_image_path_coverage_rate", "value": round(image_path_coverage_rate, 6)},
            {"metric": "actual_bbox_coverage_rate", "value": round(bbox_coverage_rate, 6)},
            {"metric": "actual_core_table_detected_rate", "value": round(core_table_detected_rate, 6)},
        ]
    )
    source_dirs_df = pd.DataFrame(source_rows)

    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary_payload.items()])
    excel_path = out_dir / "mineru_benchmark_320b.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "per_report": per_report_df,
            "table_assets_all": table_assets_df,
            "role_counts": role_counts_global,
            "warning_summary": warning_summary_df,
            "missing_image_cases": missing_image_df,
            "missing_bbox_cases": missing_bbox_df,
            "failed_reports": failed_reports_df,
            "candidate_primary_parser_decision": decision_df,
            "source_dirs": source_dirs_df,
        },
    )

    summary_json_path = out_dir / "mineru_benchmark_320b_summary.json"
    _json_dump(summary_json_path, summary_payload)

    report_md_path = out_dir / "mineru_benchmark_320b_report.md"
    recommendation = (
        "可进入下一阶段（320C）做更大样本 benchmark 或并行对照现有 parser。"
        if parser_decision == "MINERU_CANDIDATE_PRIMARY_PARSER"
        else "建议继续扩展样本并强化 role 规则/字段覆盖，再评估 primary parser 切换。"
    )
    report_lines = [
        "# MinerU Benchmark 320B Report",
        "",
        "## Input",
        f"- benchmark_root: `{root}`",
        "",
        "## Snapshot",
        f"- report_count: {report_count}",
        f"- parsed_report_count: {parsed_report_count}",
        f"- failed_report_count: {failed_report_count}",
        f"- total_table_asset_count: {total_table_asset_count}",
        f"- image_path_coverage_rate: {summary_payload['image_path_coverage_rate']}",
        f"- bbox_coverage_rate: {summary_payload['bbox_coverage_rate']}",
        f"- core_table_detected_rate: {summary_payload['core_table_detected_rate']}",
        f"- unknown_table_rate: {summary_payload['unknown_table_rate']}",
        f"- parser_decision: {parser_decision}",
        f"- benchmark_status: {benchmark_status}",
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

