import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


DEFAULT_DELIVERY_DIR = Path(r"D:\_datefac\output\delivery_package")
DEFAULT_REPORT_NAME = "07_delivery_state_check.xlsx"

EXPECTED_FILES = {
    "01_auto_trusted": "01_自动可信核心指标.xlsx",
    "01A_conflicts": "01A_自动可信核心指标冲突明细.xlsx",
    "02_manual_queue": "02_人工复核指标队列.xlsx",
    "03_excluded_failed": "03_非目标报告与失败说明.xlsx",
    "04_summary": "04_处理摘要.md",
    "05_region_index": "05_表格区域截图索引.xlsx",
    "06_final": "06_最终核心财务指标.xlsx",
    "06A_apply_detail": "06A_人工修正应用明细.xlsx",
    "06B_unresolved": "06B_未解决问题清单.xlsx",
    "06C_template": "06C_复核模板说明.md",
    "06D_diagnosis": "06D_人工复核回写诊断.xlsx",
}

HIGH_RISK_FLAGS = {
    "source_row_semantic_mismatch",
    "forbidden_account_row_as_metric_source",
    "multiple_mixed_text_source",
    "mixed_text_values",
    "likely_wrong_row",
    "non_numeric_value",
    "label_value_glued",
    "amount_has_percent",
    "invalid_ratio_too_large",
    "invalid_eps_too_large",
    "suspicious_pb_too_large",
}

TEST_TOKENS = ["TEST", "20266", "987654.321"]
KEY_COLS = ["asset_package", "standard_metric", "year"]
YEAR_TOKEN_RE = re.compile(r"(20\d{2}[AE]?)", re.IGNORECASE)
TRUE_VALUES = {"true", "1", "yes", "y", "是", "对", "使用", "采用", "√"}
STATUS_CORRECTED = {"corrected", "accepted", "修正", "已修正", "已确认", "确认", "通过", "accept", "ok"}


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _split_flags(v) -> List[str]:
    return [x.strip() for x in _norm(v).split("|") if x.strip()]


def _read_excel(path: Path) -> Tuple[pd.DataFrame, str]:
    if not path.exists():
        return pd.DataFrame(), "missing"
    try:
        return pd.read_excel(path, engine="openpyxl").fillna(""), "ok"
    except Exception as exc:
        return pd.DataFrame(), f"read_failed:{type(exc).__name__}:{exc}"


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for enc in ("utf-8", "gbk"):
        try:
            return path.read_text(encoding=enc, errors="ignore")
        except Exception:
            pass
    return ""


def _write_report(sheets: Dict[str, pd.DataFrame], path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return final_path


def _check(rows: List[Dict[str, object]], name: str, status: str, severity: str = "INFO", count: int = 0, detail: str = "", fix: str = "") -> None:
    rows.append({
        "check_name": name,
        "status": status,
        "severity": severity,
        "count": int(count or 0),
        "detail": detail,
        "how_to_fix": fix,
    })


def _check_files(delivery_dir: Path) -> Tuple[List[Dict[str, object]], Dict[str, Path]]:
    paths = {k: delivery_dir / v for k, v in EXPECTED_FILES.items()}
    rows = []
    for key, path in paths.items():
        rows.append({
            "file_key": key,
            "expected_name": path.name,
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        })
    return rows, paths


def _required_cols(df: pd.DataFrame, table: str, cols: List[str], checks: List[Dict[str, object]], details: List[Dict[str, object]]) -> None:
    missing = [c for c in cols if c not in df.columns]
    for c in cols:
        details.append({"table": table, "column": c, "exists": c in df.columns})
    _check(checks, f"{table}_required_columns", "PASS" if not missing else "FAIL", "ERROR" if missing else "INFO", len(missing), "missing=" + "|".join(missing) if missing else "", "重新生成对应文件或检查列名。" if missing else "")


def _duplicate_keys(df: pd.DataFrame, table: str, checks: List[Dict[str, object]], details: List[Dict[str, object]]) -> None:
    if df.empty:
        _check(checks, f"{table}_duplicate_keys", "SKIP", detail="empty_table")
        return
    missing = [c for c in KEY_COLS if c not in df.columns]
    if missing:
        _check(checks, f"{table}_duplicate_keys", "FAIL", "ERROR", len(missing), "missing_key_cols=" + "|".join(missing))
        return
    work = df.copy()
    for c in KEY_COLS:
        work[c] = work[c].map(_norm)
    grouped = work.groupby(KEY_COLS, dropna=False).size().reset_index(name="duplicate_count")
    grouped = grouped[grouped["duplicate_count"] > 1]
    for _, r in grouped.iterrows():
        details.append({
            "table": table,
            "asset_package": r["asset_package"],
            "standard_metric": r["standard_metric"],
            "year": r["year"],
            "duplicate_count": int(r["duplicate_count"]),
        })
    _check(checks, f"{table}_duplicate_keys", "PASS" if grouped.empty else "FAIL", "ERROR" if not grouped.empty else "INFO", len(grouped), f"duplicate_key_groups={len(grouped)}", "检查去重逻辑或人工回写冲突。" if not grouped.empty else "")


def _high_risk_flags(df: pd.DataFrame, table: str, checks: List[Dict[str, object]], details: List[Dict[str, object]]) -> None:
    if df.empty:
        _check(checks, f"{table}_high_risk_flags", "SKIP", detail="empty_table")
        return
    flag_cols = [c for c in ("value_issue_flags", "delivery_warning_flags") if c in df.columns]
    if not flag_cols:
        _check(checks, f"{table}_high_risk_flags", "SKIP", detail="no_flag_columns")
        return
    start_len = len(details)
    for i, r in df.iterrows():
        flags = set()
        for c in flag_cols:
            flags.update(_split_flags(r.get(c)))
        bad = sorted(flags & HIGH_RISK_FLAGS)
        if bad:
            details.append({
                "table": table,
                "row_index": int(i),
                "asset_package": _norm(r.get("asset_package")),
                "standard_metric": _norm(r.get("standard_metric")),
                "year": _norm(r.get("year")),
                "high_risk_flags": "|".join(bad),
                "value_issue_flags": _norm(r.get("value_issue_flags")),
                "delivery_warning_flags": _norm(r.get("delivery_warning_flags")),
            })
    count = len(details) - start_len
    _check(checks, f"{table}_high_risk_flags", "PASS" if count == 0 else "FAIL", "ERROR" if count else "INFO", count, f"rows_with_high_risk_flags={count}", "高风险 flags 不应进入 01/06。" if count else "")


def _test_tokens(frames: Dict[str, pd.DataFrame], template_text: str, checks: List[Dict[str, object]], details: List[Dict[str, object]]) -> None:
    hard_hits = 0
    for key, df in frames.items():
        if df.empty:
            continue
        as_text = df.astype(str)
        for token in TEST_TOKENS:
            mask = as_text.apply(lambda col: col.str.contains(re.escape(token), case=False, na=False))
            for row_idx, col in mask.stack()[lambda s: s].index:
                hard_hits += 1
                details.append({
                    "file_key": key,
                    "row_index": int(row_idx),
                    "column": str(col),
                    "token": token,
                    "cell_value": _norm(df.at[row_idx, col])[:300],
                    "severity": "ERROR",
                })
    template_hits = 0
    for token in TEST_TOKENS:
        if token.lower() in template_text.lower():
            template_hits += 1
            details.append({"file_key": "06C_template", "row_index": "", "column": "text", "token": token, "cell_value": "template_contains_token", "severity": "WARN"})
    status = "FAIL" if hard_hits else ("WARN" if template_hits else "PASS")
    severity = "ERROR" if hard_hits else ("WARN" if template_hits else "INFO")
    _check(checks, "test_tokens", status, severity, hard_hits, f"hard_hits={hard_hits}; template_hits={template_hits}", "清理 TEST/20266/987654.321；模板示例也建议换成正式示例。" if hard_hits or template_hits else "")


def _manual_queue(df02: pd.DataFrame, checks: List[Dict[str, object]], col_details: List[Dict[str, object]], issue_details: List[Dict[str, object]]) -> None:
    if df02.empty:
        _check(checks, "manual_queue", "SKIP", detail="empty_table")
        return
    cols = list(map(str, df02.columns))
    important = ["review_status", "use_corrected_value", "corrected_value", "year"]
    for c in important:
        col_details.append({"target_column": c, "exists_exact": c in cols})
    missing = [c for c in important if c not in cols]
    _check(checks, "manual_queue_required_review_columns", "PASS" if not missing else "WARN", "WARN" if missing else "INFO", len(missing), "missing=" + "|".join(missing) if missing else "", "确认 02 表里存在复核列。" if missing else "")

    multi_year = 0
    not_ready = 0
    for i, r in df02.iterrows():
        year = _norm(r.get("year"))
        tokens = list(dict.fromkeys([x.upper() for x in YEAR_TOKEN_RE.findall(year)]))
        if len(tokens) > 1:
            multi_year += 1
            issue_details.append({"row_index": int(i), "issue_type": "multi_year", "asset_package": _norm(r.get("asset_package")), "standard_metric": _norm(r.get("standard_metric")), "year": year, "tokens": "|".join(tokens), "how_to_fix": "year 只能填单一年份，如 2026E。"})
        status = _norm(r.get("review_status")).lower()
        use_value = _norm(r.get("use_corrected_value")).lower()
        corrected = _norm(r.get("corrected_value"))
        wants_apply = status in STATUS_CORRECTED or use_value in TRUE_VALUES
        if wants_apply and (not corrected or len(tokens) != 1):
            not_ready += 1
            issue_details.append({"row_index": int(i), "issue_type": "corrected_row_not_ready", "asset_package": _norm(r.get("asset_package")), "standard_metric": _norm(r.get("standard_metric")), "year": year, "tokens": "|".join(tokens), "how_to_fix": "填写 corrected_value，并保证 year 是单一年份。"})
    _check(checks, "manual_queue_multi_year", "PASS" if multi_year == 0 else "WARN", "WARN" if multi_year else "INFO", multi_year, f"multi_year_rows={multi_year}")
    _check(checks, "manual_queue_corrected_rows_ready", "PASS" if not_ready == 0 else "WARN", "WARN" if not_ready else "INFO", not_ready, f"not_ready_rows={not_ready}")


def check_delivery_state(delivery_dir: Path, write_report: bool = True) -> Dict[str, object]:
    file_rows, paths = _check_files(delivery_dir)
    checks: List[Dict[str, object]] = []
    missing_files = sum(1 for r in file_rows if not r["exists"])
    _check(checks, "required_delivery_files", "PASS" if missing_files == 0 else "FAIL", "ERROR" if missing_files else "INFO", missing_files, f"missing_files={missing_files}")

    df01, s01 = _read_excel(paths["01_auto_trusted"])
    df02, s02 = _read_excel(paths["02_manual_queue"])
    df06, s06 = _read_excel(paths["06_final"])
    df06a, s06a = _read_excel(paths["06A_apply_detail"])
    df06b, s06b = _read_excel(paths["06B_unresolved"])
    template_text = _read_text(paths["06C_template"])
    read_rows = [
        {"file_key": "01_auto_trusted", "read_status": s01, "rows": len(df01), "cols": len(df01.columns)},
        {"file_key": "02_manual_queue", "read_status": s02, "rows": len(df02), "cols": len(df02.columns)},
        {"file_key": "06_final", "read_status": s06, "rows": len(df06), "cols": len(df06.columns)},
        {"file_key": "06A_apply_detail", "read_status": s06a, "rows": len(df06a), "cols": len(df06a.columns)},
        {"file_key": "06B_unresolved", "read_status": s06b, "rows": len(df06b), "cols": len(df06b.columns)},
    ]
    failed_reads = [r for r in read_rows if not str(r["read_status"]).startswith(("ok", "missing"))]
    _check(checks, "read_excels", "PASS" if not failed_reads else "FAIL", "ERROR" if failed_reads else "INFO", len(failed_reads), f"failed_reads={len(failed_reads)}")

    col_details: List[Dict[str, object]] = []
    _required_cols(df01, "01_auto_trusted", ["asset_package", "standard_metric", "year", "value"], checks, col_details)
    _required_cols(df02, "02_manual_queue", ["asset_package", "standard_metric"], checks, col_details)
    _required_cols(df06, "06_final", ["asset_package", "standard_metric", "year", "final_value", "final_value_source"], checks, col_details)

    duplicate_details: List[Dict[str, object]] = []
    _duplicate_keys(df01, "01_auto_trusted", checks, duplicate_details)
    _duplicate_keys(df06, "06_final", checks, duplicate_details)

    high_risk_details: List[Dict[str, object]] = []
    _high_risk_flags(df01, "01_auto_trusted", checks, high_risk_details)
    _high_risk_flags(df06, "06_final", checks, high_risk_details)

    token_details: List[Dict[str, object]] = []
    _test_tokens({"01_auto_trusted": df01, "02_manual_queue": df02, "06_final": df06, "06A_apply_detail": df06a, "06B_unresolved": df06b}, template_text, checks, token_details)

    manual_col_details: List[Dict[str, object]] = []
    manual_issue_details: List[Dict[str, object]] = []
    _manual_queue(df02, checks, manual_col_details, manual_issue_details)

    checks_df = pd.DataFrame(checks)
    fail_count = int((checks_df["status"] == "FAIL").sum()) if not checks_df.empty else 0
    warn_count = int((checks_df["status"] == "WARN").sum()) if not checks_df.empty else 0
    pass_count = int((checks_df["status"] == "PASS").sum()) if not checks_df.empty else 0
    overall = "FAIL" if fail_count else ("WARN" if warn_count else "PASS")
    summary_df = pd.DataFrame([{
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "delivery_dir": str(delivery_dir),
        "overall_status": overall,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "check_count": len(checks_df),
        "01_rows": len(df01),
        "02_rows": len(df02),
        "06_rows": len(df06),
    }])
    report_path = ""
    if write_report:
        report_path = str(_write_report({
            "summary": summary_df,
            "checks": checks_df,
            "files": pd.DataFrame(file_rows),
            "read_status": pd.DataFrame(read_rows),
            "required_columns": pd.DataFrame(col_details),
            "duplicate_keys": pd.DataFrame(duplicate_details),
            "high_risk_flags": pd.DataFrame(high_risk_details),
            "test_token_hits": pd.DataFrame(token_details),
            "manual_review_columns": pd.DataFrame(manual_col_details),
            "manual_review_issues": pd.DataFrame(manual_issue_details),
        }, delivery_dir / DEFAULT_REPORT_NAME))
    return {"overall_status": overall, "pass_count": pass_count, "warn_count": warn_count, "fail_count": fail_count, "check_count": len(checks_df), "delivery_dir": str(delivery_dir), "report_path": report_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check delivery package state without mutating core outputs.")
    parser.add_argument("--delivery-dir", default=str(DEFAULT_DELIVERY_DIR))
    parser.add_argument("--no-write-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check_delivery_state(Path(args.delivery_dir), write_report=not args.no_write_report)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key in ["overall_status", "pass_count", "warn_count", "fail_count", "check_count", "delivery_dir", "report_path"]:
            if result.get(key) != "":
                print(f"{key}: {result[key]}")


if __name__ == "__main__":
    main()
