import argparse
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = r"D:\_datefac\output"
DEFAULT_REPORT_PATH = r"D:\_datefac\output\08_批量回归报告.xlsx"
DEFAULT_VALUE_REPORT_PATH = r"D:\_datefac\output\19_financial_value_validation_report.xlsx"
DEFAULT_REPORT_TYPE_PATH = r"D:\_datefac\output\24_report_type_diagnostics.xlsx"

ASSET_SUFFIX = "_资产包"
CORE_METRICS = [
    "\u8425\u4e1a\u6536\u5165",
    "\u5f52\u5c5e\u6bcd\u516c\u53f8\u51c0\u5229\u6da6",
    "\u6bdb\u5229\u7387",
    "ROE",
    "\u6bcf\u80a1\u6536\u76ca",
    "P/E",
    "P/B",
    "EV/EBITDA",
]
TIER_ORDER = ["A_usable", "B_partial_review", "C_label_only_untrusted", "D_insufficient", "E_hard_sample"]

EVAL_SCOPE_IN = "in_scope_8_metric_eval"
EVAL_SCOPE_OUT = "out_of_scope_non_target"
EVAL_SCOPE_UNKNOWN = "unknown_scope"


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _to_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _safe_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_chars: int = 300) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        vals = [str(x).strip() for x in row.tolist()]
        vals = [v for v in vals if v]
        if vals:
            lines.append(" | ".join(vals))
    text = " || ".join(lines)
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


def _safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", _norm(name or "Sheet"))[:31] or "Sheet"
    base = cleaned
    i = 1
    while cleaned in used:
        suffix = f"_{i}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(cleaned)
    return cleaned


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], report_path: str) -> str:
    final_path = report_path
    if os.path.exists(report_path):
        try:
            with open(report_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%H%M%S")
            final_path = report_path.replace(".xlsx", f"_copy_{ts}.xlsx")

    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        used = set()
        for sheet_name, df in sheet_map.items():
            safe = _safe_sheet_name(sheet_name, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return final_path


def _find_asset_packages(output_dir: str) -> List[Path]:
    root = Path(output_dir)
    if not root.is_dir():
        return []
    return sorted([x for x in root.iterdir() if x.is_dir() and x.name.endswith(ASSET_SUFFIX)], key=lambda x: x.name)


def _latest_file(pkg: Path, prefix: str) -> Optional[Path]:
    cands = [x for x in pkg.iterdir() if x.is_file() and x.name.startswith(prefix) and x.suffix.lower() == ".xlsx"]
    if not cands:
        return None
    return sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _latest_02(pkg: Path) -> Optional[Path]:
    cands = [
        x
        for x in pkg.iterdir()
        if x.is_file() and x.suffix.lower() == ".xlsx" and x.name.startswith("02_") and not x.name.startswith("02A_")
    ]
    if not cands:
        return None
    return sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _load_consistency_map(output_dir: str) -> Dict[str, Dict[str, object]]:
    report_path = Path(output_dir) / "12_asset_consistency_report.xlsx"
    if not report_path.exists():
        return {}
    try:
        df = pd.read_excel(str(report_path), sheet_name="summary")
    except Exception:
        return {}

    mapping: Dict[str, Dict[str, object]] = {}
    for _, row in df.iterrows():
        name = _norm(row.get("asset_package", ""))
        if not name:
            continue
        mapping[name] = {
            "consistency_status": _norm(row.get("consistency_status", "")),
            "issue_flags": _norm(row.get("issue_flags", "")),
            "recommendation": _norm(row.get("recommendation", "")),
            "can_join_financial_regression": _to_bool(row.get("can_join_financial_regression", False)),
            "missing_core_artifacts": _norm(row.get("missing_core_artifacts", "")),
            "missing_optional_artifacts": _norm(row.get("missing_optional_artifacts", "")),
        }
    return mapping


def _load_raw_vs_structured_map(output_dir: str) -> Dict[str, Dict[str, object]]:
    report_path = Path(output_dir) / "11_raw_vs_structured_report.xlsx"
    if not report_path.exists():
        return {}
    try:
        df = pd.read_excel(str(report_path), sheet_name="summary")
    except Exception:
        return {}
    mapping: Dict[str, Dict[str, object]] = {}
    for _, row in df.iterrows():
        name = _norm(row.get("asset_package", ""))
        if not name:
            continue
        mapping[name] = row.to_dict()
    return mapping


def _load_value_validation_maps() -> Tuple[bool, Dict[str, Dict[str, object]], Dict[Tuple[str, str, str], Dict[str, object]]]:
    report_path = Path(DEFAULT_VALUE_REPORT_PATH)
    if not report_path.exists():
        return False, {}, {}

    try:
        asset_df = pd.read_excel(str(report_path), sheet_name="asset_value_summary")
        detail_df = pd.read_excel(str(report_path), sheet_name="metric_value_details")
    except Exception:
        return False, {}, {}

    asset_map: Dict[str, Dict[str, object]] = {}
    for _, row in asset_df.iterrows():
        asset = _norm(row.get("asset_package", ""))
        if not asset:
            continue
        asset_map[asset] = {
            "label_hit_metric_count": row.get("label_hit_metric_count", ""),
            "value_valid_metric_count": row.get("value_valid_metric_count", ""),
            "value_suspicious_metric_count": row.get("value_suspicious_metric_count", ""),
            "value_invalid_metric_count": row.get("value_invalid_metric_count", ""),
            "value_missing_metric_count": row.get("missing_metric_count", ""),
            "value_valid_ratio": row.get("value_valid_ratio", ""),
            "primary_value_issue": _norm(row.get("primary_value_issue", "")),
        }

    detail_map: Dict[Tuple[str, str, str], Dict[str, object]] = {}
    grouped = defaultdict(list)
    for _, row in detail_df.fillna("").iterrows():
        asset = _norm(row.get("asset_package", ""))
        metric = _norm(row.get("standard_metric", ""))
        label = _norm(row.get("source_row_label", ""))
        if not asset or not metric:
            continue
        grouped[(asset, metric, label)].append(row.to_dict())

    for key, rows in grouped.items():
        valid_cnt = sum(1 for r in rows if _norm(r.get("validation_status", "")) == "valid")
        invalid_cnt = sum(1 for r in rows if _norm(r.get("validation_status", "")) == "invalid")
        suspicious_cnt = sum(1 for r in rows if _norm(r.get("validation_status", "")) == "suspicious")

        flags = []
        for r in rows:
            flags.extend([x.strip() for x in _norm(r.get("issue_flags", "")).split("|") if x.strip()])

        uniq_flags = []
        seen = set()
        for f in flags:
            if f not in seen:
                seen.add(f)
                uniq_flags.append(f)

        if invalid_cnt > 0:
            status = "invalid"
        elif valid_cnt > 0 and suspicious_cnt == 0:
            status = "valid"
        elif valid_cnt > 0 or suspicious_cnt > 0:
            status = "suspicious"
        else:
            status = "missing"

        detail_map[key] = {
            "value_validation_status": status,
            "value_issue_flags": "|".join(uniq_flags),
            "valid_year_count": int(valid_cnt),
            "invalid_year_count": int(invalid_cnt),
        }
    return True, asset_map, detail_map


def _load_hard_probe_map(output_dir: str) -> Dict[str, Dict[str, object]]:
    mapping: Dict[str, Dict[str, object]] = {}
    for pkg in _find_asset_packages(output_dir):
        file_21 = _latest_file(pkg, "21_")
        if not file_21:
            continue
        try:
            df = pd.read_excel(str(file_21), sheet_name="group_summary")
            if df.empty or "value_valid_metric_count" not in df.columns:
                continue
            best = int(pd.to_numeric(df["value_valid_metric_count"], errors="coerce").fillna(0).max())
            mapping[pkg.name] = {"probe_file": str(file_21), "best_value_valid_metric_count": best}
        except Exception:
            continue
    return mapping


def _load_report_type_map() -> Tuple[bool, Dict[str, Dict[str, object]]]:
    path = Path(DEFAULT_REPORT_TYPE_PATH)
    if not path.exists():
        return False, {}
    try:
        df = pd.read_excel(path, sheet_name="report_type_summary", engine="openpyxl").fillna("")
    except Exception:
        return False, {}

    mapping: Dict[str, Dict[str, object]] = {}
    for _, row in df.iterrows():
        asset = _norm(row.get("asset_package"))
        if not asset:
            continue
        mapping[asset] = {
            "report_type": _norm(row.get("report_type")),
            "target_applicability": _norm(row.get("target_applicability")),
            "should_include_in_8_metric_eval": _to_bool(row.get("should_include_in_8_metric_eval")),
        }
    return True, mapping


def _eval_scope(report_type: str, target_applicability: str, include_in_eval: Optional[bool]) -> str:
    if include_in_eval is True:
        return EVAL_SCOPE_IN
    if include_in_eval is False:
        if _norm(target_applicability) or _norm(report_type):
            return EVAL_SCOPE_OUT
        return EVAL_SCOPE_UNKNOWN
    return EVAL_SCOPE_UNKNOWN


def _raw_quality(file_02a: Optional[Path]) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    summary = {
        "has_02A": bool(file_02a and file_02a.exists()),
        "raw_table_count": 0,
        "raw_good_count": 0,
        "raw_ok_count": 0,
        "raw_bad_count": 0,
        "raw_good_ok_ratio": 0.0,
        "raw_backend_distribution": "",
    }
    rows: List[Dict[str, object]] = []
    if not summary["has_02A"]:
        return summary, rows
    try:
        xls = pd.ExcelFile(str(file_02a))
        idx_sheet = next((s for s in xls.sheet_names if s.startswith("00_")), xls.sheet_names[0])
        idx_df = pd.read_excel(str(file_02a), sheet_name=idx_sheet)
        if idx_df.empty:
            return summary, rows

        summary["raw_table_count"] = int(len(idx_df))
        qcol = "quality_level" if "quality_level" in idx_df.columns else None
        bcol = "backend" if "backend" in idx_df.columns else None
        if qcol:
            qvc = idx_df[qcol].fillna("NA").astype(str).value_counts()
            summary["raw_good_count"] = int(qvc.get("GOOD", 0))
            summary["raw_ok_count"] = int(qvc.get("OK", 0))
            summary["raw_bad_count"] = int(qvc.get("BAD", 0))
        if bcol:
            bvc = idx_df[bcol].fillna("NA").astype(str).value_counts()
            summary["raw_backend_distribution"] = "|".join([f"{k}:{int(v)}" for k, v in bvc.items()])

        table_cnt = int(summary["raw_table_count"])
        good_ok = int(summary["raw_good_count"]) + int(summary["raw_ok_count"])
        summary["raw_good_ok_ratio"] = round((good_ok / table_cnt), 4) if table_cnt > 0 else 0.0
        rows = idx_df.to_dict(orient="records")
    except Exception:
        pass
    return summary, rows


def _structured_quality(file_02: Optional[Path]) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    summary = {"has_02": bool(file_02 and file_02.exists()), "structured_sheet_count": 0}
    rows: List[Dict[str, object]] = []
    if not summary["has_02"]:
        return summary, rows
    try:
        xls = pd.ExcelFile(str(file_02))
        data_sheets = [s for s in xls.sheet_names if not s.startswith("00_")]
        summary["structured_sheet_count"] = len(data_sheets)
        for s in data_sheets:
            try:
                df = pd.read_excel(str(file_02), sheet_name=s)
                total = int(df.shape[0] * df.shape[1]) if not df.empty else 0
                non_empty = int(df.fillna("").astype(str).replace(r"^\s*$", "", regex=True).ne("").sum().sum()) if total else 0
                empty_ratio = round((total - non_empty) / total, 4) if total else 0.0
                rows.append(
                    {
                        "sheet_name": s,
                        "row_count": int(df.shape[0]),
                        "col_count": int(df.shape[1]),
                        "empty_cell_ratio": empty_ratio,
                        "preview": _safe_preview(df),
                    }
                )
            except Exception as exc:
                rows.append({"sheet_name": s, "row_count": "", "col_count": "", "empty_cell_ratio": "", "preview": f"read_error: {exc}"})
    except Exception:
        pass
    return summary, rows


def _financial_quality(file_05: Optional[Path]) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    summary = {
        "has_05": bool(file_05 and file_05.exists()),
        "financial_detail_count": 0,
        "financial_metric_hit_count": 0,
        "financial_metric_hit_ratio": 0.0,
        "financial_hit_metrics": "",
        "financial_missing_metrics": "|".join(CORE_METRICS),
        "header_repaired_count": 0,
        "suspicious_misextract_count": 0,
        "invalid_blocked_count": 0,
    }
    rows: List[Dict[str, object]] = []
    if not summary["has_05"]:
        return summary, rows
    try:
        xls = pd.ExcelFile(str(file_05))
        detail_df = None
        metric_col = None
        for sn in xls.sheet_names:
            df = pd.read_excel(str(file_05), sheet_name=sn)
            if "source_row_label" in df.columns:
                detail_df = df
                metric_col = "标准指标" if "标准指标" in df.columns else ("standard_metric" if "standard_metric" in df.columns else df.columns[0])
                break
        if detail_df is None or detail_df.empty:
            return summary, rows

        detail_df = detail_df.fillna("")
        hits = sorted(set(detail_df[metric_col].astype(str).str.strip().tolist()))
        hits = [h for h in hits if h]
        missing = [m for m in CORE_METRICS if m not in hits]
        summary["financial_detail_count"] = int(len(detail_df))
        summary["financial_metric_hit_count"] = int(len(hits))
        summary["financial_metric_hit_ratio"] = round(len(hits) / len(CORE_METRICS), 4)
        summary["financial_hit_metrics"] = "|".join(hits)
        summary["financial_missing_metrics"] = "|".join(missing)

        if "header_repaired" in detail_df.columns:
            summary["header_repaired_count"] = int(detail_df["header_repaired"].astype(str).str.lower().isin(["true", "1"]).sum())

        if "source_row_label" in detail_df.columns:
            labels = detail_df["source_row_label"].fillna("").astype(str)
            suspicious = int(labels.str.contains("同比|增速|增长率|扣非|少数股东损益", regex=True, na=False).sum())
            summary["suspicious_misextract_count"] = suspicious

        wide_df = pd.read_excel(str(file_05), sheet_name=0).fillna("")
        year_cols = [c for c in wide_df.columns if re.fullmatch(r"20\d{2}[AE]?", _norm(c))]
        blocked = 0
        if "value_validation_status" in wide_df.columns and year_cols:
            for _, row in wide_df.iterrows():
                if _norm(row.get("value_validation_status", "")) != "invalid":
                    continue
                has_year_value = any(_norm(row.get(c, "")) != "" for c in year_cols)
                if not has_year_value:
                    blocked += 1
        summary["invalid_blocked_count"] = int(blocked)
        rows = detail_df.to_dict(orient="records")
    except Exception:
        pass
    return summary, rows


def _diagnose(summary: Dict[str, object]) -> Dict[str, str]:
    extraction_status = "partial"
    postprocess_status = "partial"
    financial_status = "partial"
    bottleneck = "unknown"
    recommendation = "建议人工复核"

    raw_table_count = int(summary.get("raw_table_count", 0) or 0)
    raw_good_ok_ratio = float(summary.get("raw_good_ok_ratio", 0.0) or 0.0)
    raw_bad = int(summary.get("raw_bad_count", 0) or 0)
    structured_sheet_count = int(summary.get("structured_sheet_count", 0) or 0)
    hit_count = int(summary.get("financial_metric_hit_count", 0) or 0)

    if raw_table_count == 0:
        extraction_status = "bad"
    elif raw_bad == raw_table_count and raw_table_count > 0:
        extraction_status = "bad"
    elif raw_good_ok_ratio >= 0.6:
        extraction_status = "good"
    elif raw_good_ok_ratio >= 0.3:
        extraction_status = "partial"
    else:
        extraction_status = "bad"

    if raw_table_count > 0 and structured_sheet_count < raw_table_count * 0.5:
        postprocess_status = "partial"
    elif structured_sheet_count > 0:
        postprocess_status = "good"
    else:
        postprocess_status = "bad"

    if hit_count >= 6:
        financial_status = "good"
    elif 3 <= hit_count <= 5:
        financial_status = "partial"
    else:
        financial_status = "bad"

    if extraction_status == "bad" and financial_status in ("bad", "partial"):
        bottleneck = "extraction_layer"
        recommendation = "优先改抽取后端/后端仲裁，不要继续修05"
    elif raw_table_count < 3 and hit_count < 3:
        bottleneck = "extraction_coverage"
        recommendation = "原始表覆盖不足，优先检查抽取链路"
    elif extraction_status == "good" and financial_status == "bad":
        bottleneck = "financial_standardizer"
        recommendation = "优先修05规则"
    elif financial_status == "good":
        bottleneck = "none_or_minor"
        recommendation = "保持当前策略，优先扩样本验证"
    elif postprocess_status == "partial":
        bottleneck = "postprocess_layer"
        recommendation = "复核02相对02A的丢表与过滤"
    else:
        bottleneck = "financial_standardizer"
        recommendation = "定向审计05未命中指标"

    return {
        "extraction_layer_status": extraction_status,
        "postprocess_layer_status": postprocess_status,
        "financial_standardization_status": financial_status,
        "primary_bottleneck": bottleneck,
        "recommendation": recommendation,
    }


def _top_issue_flags_from_detail_rows(rows: List[Dict[str, object]], topn: int = 3) -> str:
    flags = []
    for r in rows:
        text = _norm(r.get("issue_flags", ""))
        if not text:
            continue
        flags.extend([x.strip() for x in text.split("|") if x.strip()])
    if not flags:
        return ""
    c = Counter(flags)
    return "|".join([f"{k}:{int(v)}" for k, v in c.most_common(topn)])


def _compute_data_tier(
    label_hit_metric_count: int,
    value_valid_metric_count: int,
    value_invalid_metric_count: int,
    hard_probe_best_valid: Optional[int],
) -> str:
    if (value_valid_metric_count == 0 and label_hit_metric_count >= 6) or (
        hard_probe_best_valid is not None and hard_probe_best_valid == 0
    ):
        return "E_hard_sample"
    if value_valid_metric_count >= 6 and value_invalid_metric_count == 0:
        return "A_usable"
    if 3 <= value_valid_metric_count < 6:
        return "B_partial_review"
    if label_hit_metric_count >= 6 and value_valid_metric_count < 3:
        return "C_label_only_untrusted"
    if label_hit_metric_count < 3:
        return "D_insufficient"
    return "B_partial_review"


def _tier_recommendation(tier: str) -> str:
    mapping = {
        "A_usable": "可进入下游AI分析，但仍保留来源追溯",
        "B_partial_review": "可部分进入报告，缺失/可疑指标需要人工复核",
        "C_label_only_untrusted": "标签命中但值不可信，优先修列对齐和值绑定",
        "D_insufficient": "抽取或结构化覆盖不足，优先检查02A/02",
        "E_hard_sample": "当前规则不适合自动处理，建议更强后端或人工复核",
    }
    return mapping.get(tier, "建议人工复核")


def build_regression_report(output_dir: str, report_path: str) -> Tuple[str, Dict[str, float]]:
    packages = _find_asset_packages(output_dir)
    consistency_map = _load_consistency_map(output_dir)
    raw_vs_map = _load_raw_vs_structured_map(output_dir)
    has_value_report, value_asset_map, value_detail_map = _load_value_validation_maps()
    hard_probe_map = _load_hard_probe_map(output_dir)
    has_report_type, report_type_map = _load_report_type_map()

    summary_rows: List[Dict[str, object]] = []
    asset_details_rows: List[Dict[str, object]] = []
    financial_metric_rows: List[Dict[str, object]] = []
    raw_table_quality_rows: List[Dict[str, object]] = []
    rec_rows: List[Dict[str, object]] = []

    consistency_ok_count = 0
    warning_but_eligible_count = 0
    core_missing_count = 0
    eligible_count = 0

    for pkg in packages:
        asset = pkg.name
        cinfo = consistency_map.get(asset, {})
        consistency_status = _norm(cinfo.get("consistency_status", ""))
        issue_flags = _norm(cinfo.get("issue_flags", ""))
        missing_core = _norm(cinfo.get("missing_core_artifacts", ""))
        missing_optional = _norm(cinfo.get("missing_optional_artifacts", ""))

        file_02a = _latest_file(pkg, "02A_")
        file_02 = _latest_02(pkg)
        file_05 = _latest_file(pkg, "05_")

        can_join = _to_bool(cinfo.get("can_join_financial_regression", False))
        if "can_join_financial_regression" not in cinfo:
            can_join = bool(file_02a and file_02 and file_05)
        is_eligible = bool(consistency_status == "OK" or can_join)

        if consistency_status == "OK":
            consistency_ok_count += 1
        if consistency_status == "WARNING" and can_join:
            warning_but_eligible_count += 1
        if not can_join:
            core_missing_count += 1
        if is_eligible:
            eligible_count += 1

        raw_summary, raw_rows = _raw_quality(file_02a)
        structured_summary, structured_rows = _structured_quality(file_02)
        financial_summary, financial_rows = _financial_quality(file_05) if is_eligible else (
            {
                "has_05": bool(file_05 and file_05.exists()),
                "financial_detail_count": 0,
                "financial_metric_hit_count": 0,
                "financial_metric_hit_ratio": 0.0,
                "financial_hit_metrics": "",
                "financial_missing_metrics": "|".join(CORE_METRICS),
                "header_repaired_count": 0,
                "suspicious_misextract_count": 0,
                "invalid_blocked_count": 0,
            },
            [],
        )

        rt = report_type_map.get(asset, {}) if has_report_type else {}
        report_type = _norm(rt.get("report_type", ""))
        target_applicability = _norm(rt.get("target_applicability", ""))
        include_8_metric = rt.get("should_include_in_8_metric_eval", None)
        if include_8_metric is not None:
            include_8_metric = bool(include_8_metric)
        eval_scope = _eval_scope(report_type, target_applicability, include_8_metric)

        summary_row: Dict[str, object] = {
            "asset_package": asset,
            "consistency_status": consistency_status,
            "issue_flags": issue_flags,
            "can_join_financial_regression": can_join,
            "regression_eligible": is_eligible,
            "missing_core_artifacts": missing_core,
            "missing_optional_artifacts": missing_optional,
            **raw_summary,
            **structured_summary,
            **financial_summary,
            "report_type": report_type,
            "target_applicability": target_applicability,
            "should_include_in_8_metric_eval": include_8_metric if include_8_metric is not None else "",
            "eval_scope": eval_scope,
        }

        if asset in raw_vs_map:
            summary_row["raw_vs_structured_diagnosis"] = _norm(raw_vs_map[asset].get("diagnosis", ""))
            summary_row["raw_vs_structured_error"] = _norm(raw_vs_map[asset].get("error_message", ""))
        else:
            summary_row["raw_vs_structured_diagnosis"] = ""
            summary_row["raw_vs_structured_error"] = ""

        summary_row.update(_diagnose(summary_row))

        if not is_eligible:
            summary_row["primary_bottleneck"] = "core_artifacts_missing"
            summary_row["recommendation"] = "缺少02A/02/05，先补核心产物后再纳入05回归"
            summary_row["financial_standardization_status"] = "bad"

        if has_value_report and asset in value_asset_map:
            v = value_asset_map[asset]
            summary_row["label_hit_metric_count"] = v.get("label_hit_metric_count", "")
            summary_row["value_valid_metric_count"] = v.get("value_valid_metric_count", "")
            summary_row["value_suspicious_metric_count"] = v.get("value_suspicious_metric_count", "")
            summary_row["value_invalid_metric_count"] = v.get("value_invalid_metric_count", "")
            summary_row["value_missing_metric_count"] = v.get("value_missing_metric_count", "")
            summary_row["value_valid_ratio"] = v.get("value_valid_ratio", "")

            detail_rows_for_asset = []
            for (a, _, _), vv in value_detail_map.items():
                if a == asset:
                    detail_rows_for_asset.append({"issue_flags": vv.get("value_issue_flags", "")})
            summary_row["value_top_issue_flags"] = _top_issue_flags_from_detail_rows(detail_rows_for_asset)
            summary_row["invalid_blocked_count"] = summary_row.get("invalid_blocked_count", 0)

            hard_best = None
            if asset in hard_probe_map:
                hard_best = hard_probe_map[asset].get("best_value_valid_metric_count")
            tier = _compute_data_tier(
                _to_int(summary_row.get("label_hit_metric_count", 0), 0),
                _to_int(summary_row.get("value_valid_metric_count", 0), 0),
                _to_int(summary_row.get("value_invalid_metric_count", 0), 0),
                _to_int(hard_best, 0) if hard_best is not None else None,
            )
            summary_row["data_usability_tier"] = tier
            summary_row["value_quality_recommendation"] = _tier_recommendation(tier)
        else:
            summary_row["label_hit_metric_count"] = ""
            summary_row["value_valid_metric_count"] = ""
            summary_row["value_suspicious_metric_count"] = ""
            summary_row["value_invalid_metric_count"] = ""
            summary_row["value_missing_metric_count"] = ""
            summary_row["value_valid_ratio"] = ""
            summary_row["invalid_blocked_count"] = ""
            summary_row["value_top_issue_flags"] = ""
            summary_row["data_usability_tier"] = ""
            summary_row["value_quality_recommendation"] = ""

        if eval_scope == EVAL_SCOPE_OUT:
            summary_row["recommendation"] = "不纳入8项核心财务指标质量统计；建议进入报告类型专用流程或跳过。"

        summary_rows.append(summary_row)

        for r in structured_rows:
            rec = {"asset_package": asset}
            rec.update(r)
            if not is_eligible:
                rec["note"] = "not_eligible_for_financial_regression"
            asset_details_rows.append(rec)

        if is_eligible:
            for r in financial_rows:
                rec = {"asset_package": asset}
                rec.update(r)
                metric = _norm(rec.get("标准指标", rec.get("standard_metric", rec.get("指标", ""))))
                label = _norm(rec.get("source_row_label", ""))
                dkey = (asset, metric, label)
                if dkey in value_detail_map:
                    vv = value_detail_map[dkey]
                    rec.setdefault("value_validation_status", vv.get("value_validation_status", ""))
                    rec.setdefault("value_issue_flags", vv.get("value_issue_flags", ""))
                    rec.setdefault("valid_year_count", vv.get("valid_year_count", ""))
                    rec.setdefault("invalid_year_count", vv.get("invalid_year_count", ""))
                rec.setdefault("value_validation_status", _norm(rec.get("value_validation_status", "")))
                rec.setdefault("value_issue_flags", _norm(rec.get("value_issue_flags", "")))
                rec.setdefault("valid_year_count", rec.get("valid_year_count", ""))
                rec.setdefault("invalid_year_count", rec.get("invalid_year_count", ""))
                rec.setdefault("value_repair_applied", rec.get("value_repair_applied", ""))
                rec.setdefault("value_repair_strategy", rec.get("value_repair_strategy", ""))
                financial_metric_rows.append(rec)

        for r in raw_rows:
            rec = {"asset_package": asset}
            rec.update(r)
            raw_table_quality_rows.append(rec)

        rec_rows.append(
            {
                "asset_package": asset,
                "regression_eligible": is_eligible,
                "can_join_financial_regression": can_join,
                "consistency_status": consistency_status,
                "primary_bottleneck": summary_row["primary_bottleneck"],
                "recommendation": summary_row["recommendation"],
                "extraction_layer_status": summary_row["extraction_layer_status"],
                "postprocess_layer_status": summary_row["postprocess_layer_status"],
                "financial_standardization_status": summary_row["financial_standardization_status"],
                "data_usability_tier": _norm(summary_row.get("data_usability_tier", "")),
                "value_quality_recommendation": _norm(summary_row.get("value_quality_recommendation", "")),
                "report_type": report_type,
                "target_applicability": target_applicability,
                "should_include_in_8_metric_eval": include_8_metric if include_8_metric is not None else "",
                "eval_scope": eval_scope,
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    asset_details_df = pd.DataFrame(asset_details_rows)
    financial_metrics_df = pd.DataFrame(financial_metric_rows)
    raw_table_quality_df = pd.DataFrame(raw_table_quality_rows)
    recommendations_df = pd.DataFrame(rec_rows)

    final = _save_excel_robust(
        {
            "summary": summary_df,
            "asset_details": asset_details_df,
            "financial_metrics": financial_metrics_df,
            "raw_table_quality": raw_table_quality_df,
            "recommendations": recommendations_df,
        },
        report_path,
    )

    # full-scope stats (existing semantics).
    eligible_df = summary_df[summary_df.get("regression_eligible", False) == True] if not summary_df.empty else pd.DataFrame()
    tier_counts = {tier: 0 for tier in TIER_ORDER}
    if not eligible_df.empty and "data_usability_tier" in eligible_df.columns:
        vc = eligible_df["data_usability_tier"].fillna("").astype(str).value_counts()
        for t in TIER_ORDER:
            tier_counts[t] = int(vc.get(t, 0))

    total_label_hit_metrics = 0
    total_value_valid_metrics = 0
    overall_value_valid_ratio = 0.0
    if not eligible_df.empty and "label_hit_metric_count" in eligible_df.columns:
        total_label_hit_metrics = int(pd.to_numeric(eligible_df["label_hit_metric_count"], errors="coerce").fillna(0).sum())
    if not eligible_df.empty and "value_valid_metric_count" in eligible_df.columns:
        total_value_valid_metrics = int(pd.to_numeric(eligible_df["value_valid_metric_count"], errors="coerce").fillna(0).sum())
    denom = int(len(eligible_df) * len(CORE_METRICS)) if len(eligible_df) > 0 else 0
    if denom > 0:
        overall_value_valid_ratio = round(total_value_valid_metrics / denom, 4)

    # new report-type scope stats.
    total_assets_all = len(summary_df)
    total_assets_in_scope = int((summary_df.get("eval_scope", "") == EVAL_SCOPE_IN).sum()) if not summary_df.empty else 0
    total_assets_out_of_scope = int((summary_df.get("eval_scope", "") == EVAL_SCOPE_OUT).sum()) if not summary_df.empty else 0
    total_assets_unknown_scope = int((summary_df.get("eval_scope", "") == EVAL_SCOPE_UNKNOWN).sum()) if not summary_df.empty else 0

    in_scope_eligible_df = summary_df[
        (summary_df.get("regression_eligible", False) == True)
        & (summary_df.get("eval_scope", "") == EVAL_SCOPE_IN)
    ] if not summary_df.empty else pd.DataFrame()

    in_scope_tier_counts = {tier: 0 for tier in TIER_ORDER}
    if not in_scope_eligible_df.empty and "data_usability_tier" in in_scope_eligible_df.columns:
        vc = in_scope_eligible_df["data_usability_tier"].fillna("").astype(str).value_counts()
        for t in TIER_ORDER:
            in_scope_tier_counts[t] = int(vc.get(t, 0))

    in_scope_total_label_hit_metrics = 0
    in_scope_total_value_valid_metrics = 0
    in_scope_overall_value_valid_ratio = 0.0
    if not in_scope_eligible_df.empty and "label_hit_metric_count" in in_scope_eligible_df.columns:
        in_scope_total_label_hit_metrics = int(pd.to_numeric(in_scope_eligible_df["label_hit_metric_count"], errors="coerce").fillna(0).sum())
    if not in_scope_eligible_df.empty and "value_valid_metric_count" in in_scope_eligible_df.columns:
        in_scope_total_value_valid_metrics = int(pd.to_numeric(in_scope_eligible_df["value_valid_metric_count"], errors="coerce").fillna(0).sum())
    in_scope_denom = int(len(in_scope_eligible_df) * len(CORE_METRICS)) if len(in_scope_eligible_df) > 0 else 0
    if in_scope_denom > 0:
        in_scope_overall_value_valid_ratio = round(in_scope_total_value_valid_metrics / in_scope_denom, 4)

    counters: Dict[str, float] = {
        # existing counters
        "total_asset_packages": len(packages),
        "summary_rows": len(summary_df),
        "asset_details_rows": len(asset_details_df),
        "financial_metrics_rows": len(financial_metrics_df),
        "raw_table_quality_rows": len(raw_table_quality_df),
        "recommendations_rows": len(recommendations_df),
        "regression_eligible_asset_count": eligible_count,
        "consistency_ok_count": consistency_ok_count,
        "consistency_warning_but_eligible_count": warning_but_eligible_count,
        "core_artifacts_missing_count": core_missing_count,
        "total_regression_eligible_assets": eligible_count,
        "A_usable_count": tier_counts["A_usable"],
        "B_partial_review_count": tier_counts["B_partial_review"],
        "C_label_only_untrusted_count": tier_counts["C_label_only_untrusted"],
        "D_insufficient_count": tier_counts["D_insufficient"],
        "E_hard_sample_count": tier_counts["E_hard_sample"],
        "total_label_hit_metrics": total_label_hit_metrics,
        "total_value_valid_metrics": total_value_valid_metrics,
        "overall_value_valid_ratio": overall_value_valid_ratio,
        "has_value_report": int(has_value_report),
        # new scope counters
        "total_assets_all": total_assets_all,
        "total_assets_in_scope": total_assets_in_scope,
        "total_assets_out_of_scope": total_assets_out_of_scope,
        "total_assets_unknown_scope": total_assets_unknown_scope,
        "in_scope_A_usable_count": in_scope_tier_counts["A_usable"],
        "in_scope_B_partial_review_count": in_scope_tier_counts["B_partial_review"],
        "in_scope_C_label_only_untrusted_count": in_scope_tier_counts["C_label_only_untrusted"],
        "in_scope_D_insufficient_count": in_scope_tier_counts["D_insufficient"],
        "in_scope_E_hard_sample_count": in_scope_tier_counts["E_hard_sample"],
        "in_scope_total_label_hit_metrics": in_scope_total_label_hit_metrics,
        "in_scope_total_value_valid_metrics": in_scope_total_value_valid_metrics,
        "in_scope_overall_value_valid_ratio": in_scope_overall_value_valid_ratio,
        "has_report_type_report": int(has_report_type),
    }
    return final, counters


def main() -> None:
    parser = argparse.ArgumentParser(description="Build batch regression report with value tiers and report-type scope.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output root containing *_资产包 directories.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH, help="Target report xlsx path.")
    args = parser.parse_args()

    final, counters = build_regression_report(args.output_dir, args.report_path)
    print(f"报告路径: {final}")
    print(f"summary行数: {counters['summary_rows']}")
    print(
        "行数统计: asset_details={asset_details_rows}, financial_metrics={financial_metrics_rows}, "
        "raw_table_quality={raw_table_quality_rows}, recommendations={recommendations_rows}".format(**counters)
    )
    print(
        "全量口径: total_asset_packages={total_asset_packages}, regression_eligible_asset_count={regression_eligible_asset_count}, "
        "consistency_ok_count={consistency_ok_count}, consistency_warning_but_eligible_count={consistency_warning_but_eligible_count}, "
        "core_artifacts_missing_count={core_artifacts_missing_count}".format(**counters)
    )
    print(
        "tier统计(全量 eligible): A={A_usable_count}, B={B_partial_review_count}, C={C_label_only_untrusted_count}, "
        "D={D_insufficient_count}, E={E_hard_sample_count}".format(**counters)
    )
    print(
        "value统计(全量 eligible): total_label_hit_metrics={total_label_hit_metrics}, total_value_valid_metrics={total_value_valid_metrics}, "
        "overall_value_valid_ratio={overall_value_valid_ratio}".format(**counters)
    )
    print(
        "scope统计: total_assets_all={total_assets_all}, total_assets_in_scope={total_assets_in_scope}, "
        "total_assets_out_of_scope={total_assets_out_of_scope}, total_assets_unknown_scope={total_assets_unknown_scope}".format(**counters)
    )
    print(
        "in_scope tier: A={in_scope_A_usable_count}, B={in_scope_B_partial_review_count}, C={in_scope_C_label_only_untrusted_count}, "
        "D={in_scope_D_insufficient_count}, E={in_scope_E_hard_sample_count}".format(**counters)
    )
    print(
        "in_scope value: in_scope_total_label_hit_metrics={in_scope_total_label_hit_metrics}, "
        "in_scope_total_value_valid_metrics={in_scope_total_value_valid_metrics}, "
        "in_scope_overall_value_valid_ratio={in_scope_overall_value_valid_ratio}".format(**counters)
    )


if __name__ == "__main__":
    main()

