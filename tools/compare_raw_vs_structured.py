import argparse
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = r"D:\_datefac\output"
DEFAULT_REPORT_PATH = r"D:\_datefac\output\11_raw_vs_structured_report.xlsx"


def _safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", str(name or "").strip()) or "Sheet"
    cleaned = cleaned[:31]
    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def _save_excel_robustly(sheet_map: Dict[str, pd.DataFrame], report_path: str) -> str:
    out_path = Path(report_path)
    final_path = out_path
    if out_path.exists():
        try:
            with open(out_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = out_path.with_name(f"{out_path.stem}_副本_{ts}{out_path.suffix}")

    used = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            safe = _safe_sheet_name(sheet, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return str(final_path)


def _find_asset_packages(output_dir: str) -> List[Path]:
    root = Path(output_dir)
    if not root.exists():
        return []
    pkgs = []
    for child in root.iterdir():
        if child.is_dir() and child.name.endswith("_资产包"):
            pkgs.append(child)
    return sorted(pkgs)


def _select_latest_matching_file(asset_pkg: Path, pattern_fn) -> Optional[Path]:
    candidates = []
    for p in asset_pkg.iterdir():
        if p.is_file() and pattern_fn(p.name):
            candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]


def _find_artifact_files(asset_pkg: Path) -> Tuple[Optional[Path], Optional[Path]]:
    file_02a = _select_latest_matching_file(
        asset_pkg,
        lambda n: n.lower().endswith(".xlsx") and n.startswith("02A_"),
    )
    file_02 = _select_latest_matching_file(
        asset_pkg,
        lambda n: n.lower().endswith(".xlsx") and n.startswith("02_"),
    )
    return file_02a, file_02


def _find_raw_index_sheet_name(xls: pd.ExcelFile) -> Optional[str]:
    sheets = list(xls.sheet_names)
    if "00_表格索引" in sheets:
        return "00_表格索引"
    for s in sheets:
        ns = re.sub(r"\s+", "", s)
        if ns.startswith("00_") and ("索引" in ns or "index" in ns.lower()):
            return s
    return None


def _safe_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_len: int = 300) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join(str(x).strip() for x in row.tolist()))
    text = " || ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _compute_empty_cell_ratio(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return 1.0
    norm = df.fillna("").astype(str)
    rows, cols = norm.shape
    total = rows * cols
    if total <= 0:
        return 1.0
    stripped = norm.replace(r"^\s*$", "", regex=True)
    non_empty = int((stripped != "").sum().sum())
    ratio = 1 - (non_empty / total)
    return float(round(max(0.0, min(1.0, ratio)), 4))


def _diagnose(row: Dict[str, object]) -> str:
    has_02a = bool(row.get("has_02A", False))
    has_02 = bool(row.get("has_02", False))
    raw_index_count = int(row.get("raw_index_count", 0) or 0)
    raw_bad_count = int(row.get("raw_bad_count", 0) or 0)
    structured_sheet_count = int(row.get("structured_sheet_count", 0) or 0)

    if not has_02a:
        return "raw_asset_missing"
    if not has_02:
        return "structured_asset_missing"
    if raw_index_count == 0:
        return "extractor_no_raw_tables"
    if raw_bad_count == raw_index_count and raw_index_count > 0:
        return "extractor_quality_bad"
    if raw_index_count > 0 and structured_sheet_count == 0:
        return "postprocess_lost_all_tables"
    if raw_index_count > 0 and structured_sheet_count < raw_index_count * 0.5:
        return "possible_postprocess_over_filtering"
    return "ok_or_need_manual_review"


def build_report(output_dir: str, report_path: str) -> Tuple[str, pd.DataFrame, pd.DataFrame]:
    summary_rows: List[Dict[str, object]] = []
    raw_detail_rows: List[Dict[str, object]] = []
    structured_detail_rows: List[Dict[str, object]] = []

    for pkg in _find_asset_packages(output_dir):
        asset_name = pkg.name
        file_02a, file_02 = _find_artifact_files(pkg)

        row: Dict[str, object] = {
            "asset_package": asset_name,
            "has_02A": bool(file_02a),
            "has_02": bool(file_02),
            "raw_index_count": 0,
            "raw_sheet_count": 0,
            "structured_sheet_count": 0,
            "raw_good_count": 0,
            "raw_ok_count": 0,
            "raw_bad_count": 0,
            "raw_backend_distribution": "",
            "raw_to_structured_sheet_ratio": 0.0,
            "diagnosis": "",
            "error_message": "",
        }
        errors: List[str] = []

        if file_02a:
            try:
                xls_02a = pd.ExcelFile(file_02a, engine="openpyxl")
                sheet_names_02a = list(xls_02a.sheet_names)
                index_sheet = _find_raw_index_sheet_name(xls_02a)
                if index_sheet:
                    idx_df = pd.read_excel(file_02a, sheet_name=index_sheet, engine="openpyxl")
                    row["raw_index_count"] = int(len(idx_df))
                    row["raw_sheet_count"] = max(0, len(sheet_names_02a) - 1)

                    if not idx_df.empty:
                        detail_df = idx_df.copy()
                        detail_df.insert(0, "asset_package", asset_name)
                        raw_detail_rows.extend(detail_df.to_dict("records"))

                        if "quality_level" in idx_df.columns:
                            qv = idx_df["quality_level"].fillna("").astype(str)
                            row["raw_good_count"] = int((qv == "GOOD").sum())
                            row["raw_ok_count"] = int((qv == "OK").sum())
                            row["raw_bad_count"] = int((qv == "BAD").sum())
                        if "backend" in idx_df.columns:
                            backend_dist = idx_df["backend"].fillna("NA").astype(str).value_counts().to_dict()
                            row["raw_backend_distribution"] = str(backend_dist)
                else:
                    errors.append("missing_raw_index_sheet")
                    row["raw_sheet_count"] = len(sheet_names_02a)
            except Exception as exc:
                errors.append(f"read_02A_error:{exc}")

        if file_02:
            try:
                xls_02 = pd.ExcelFile(file_02, engine="openpyxl")
                sheet_names_02 = list(xls_02.sheet_names)
                row["structured_sheet_count"] = int(len(sheet_names_02))
                for sheet in sheet_names_02:
                    try:
                        df = pd.read_excel(file_02, sheet_name=sheet, engine="openpyxl")
                        structured_detail_rows.append(
                            {
                                "asset_package": asset_name,
                                "sheet_name": sheet,
                                "row_count": int(df.shape[0]),
                                "col_count": int(df.shape[1]),
                                "empty_cell_ratio": _compute_empty_cell_ratio(df),
                                "preview": _safe_preview(df),
                            }
                        )
                    except Exception as exc:
                        structured_detail_rows.append(
                            {
                                "asset_package": asset_name,
                                "sheet_name": sheet,
                                "row_count": "",
                                "col_count": "",
                                "empty_cell_ratio": "",
                                "preview": f"read_sheet_error:{exc}",
                            }
                        )
            except Exception as exc:
                errors.append(f"read_02_error:{exc}")

        raw_index_count = int(row["raw_index_count"] or 0)
        structured_sheet_count = int(row["structured_sheet_count"] or 0)
        row["raw_to_structured_sheet_ratio"] = float(
            round((raw_index_count / structured_sheet_count), 4) if structured_sheet_count > 0 else 0.0
        )
        row["diagnosis"] = _diagnose(row)
        row["error_message"] = " | ".join(errors)
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    raw_detail_df = pd.DataFrame(raw_detail_rows)
    structured_detail_df = pd.DataFrame(
        structured_detail_rows,
        columns=["asset_package", "sheet_name", "row_count", "col_count", "empty_cell_ratio", "preview"],
    )

    backend_summary_df = pd.DataFrame(
        columns=["backend", "table_count", "good_count", "ok_count", "bad_count", "avg_quality_score"]
    )
    if not raw_detail_df.empty:
        df = raw_detail_df.copy()
        if "backend" in df.columns:
            df["backend"] = df["backend"].fillna("NA").astype(str)
            if "quality_level" not in df.columns:
                df["quality_level"] = ""
            if "quality_score" not in df.columns:
                df["quality_score"] = 0.0
            df["quality_score"] = pd.to_numeric(df["quality_score"], errors="coerce").fillna(0.0)

            rows = []
            for backend, g in df.groupby("backend"):
                q = g["quality_level"].fillna("").astype(str)
                rows.append(
                    {
                        "backend": backend,
                        "table_count": int(len(g)),
                        "good_count": int((q == "GOOD").sum()),
                        "ok_count": int((q == "OK").sum()),
                        "bad_count": int((q == "BAD").sum()),
                        "avg_quality_score": float(round(g["quality_score"].mean(), 4)),
                    }
                )
            backend_summary_df = pd.DataFrame(rows)

    final_path = _save_excel_robustly(
        {
            "summary": summary_df,
            "raw_table_details": raw_detail_df,
            "structured_table_details": structured_detail_df,
            "backend_summary": backend_summary_df,
        },
        report_path,
    )
    return final_path, summary_df, backend_summary_df


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare 02A raw table asset layer and 02 structured layer.")
    ap.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory containing *_资产包.")
    ap.add_argument("--report-path", default=DEFAULT_REPORT_PATH, help="Output report path.")
    args = ap.parse_args()

    final_path, summary_df, backend_summary_df = build_report(args.output_dir, args.report_path)
    print(f"report_path={final_path}")
    print(f"summary_rows={len(summary_df)}")
    if not summary_df.empty:
        for _, row in summary_df.iterrows():
            print(f"{row.get('asset_package','')}: {row.get('diagnosis','')}")
    print("backend_summary:")
    if backend_summary_df.empty:
        print("(empty)")
    else:
        print(backend_summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
