import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from financial_standardizer import (
    _extract_year_columns,
    _find_row_label,
    _match_standard_metric,
    _normalize_text,
    _compact_text,
)


DEFAULT_ASSET_PACKAGE = r"D:\_datefac\output\H3_AP202605121822218343_1_资产包"
DEFAULT_OUTPUT_NAME = "13_financial_standardizer_diagnostics.xlsx"

YEAR_TOKEN_RE = re.compile(r"(20\d{2}(?:[AE])?)", re.IGNORECASE)


def _save_excel_robustly(sheet_map: Dict[str, pd.DataFrame], output_path: Path) -> str:
    final_path = output_path
    if output_path.exists():
        try:
            with open(output_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = output_path.with_name(f"{output_path.stem}_副本_{ts}{output_path.suffix}")

    used = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for raw_name, df in sheet_map.items():
            sheet_name = re.sub(r"[\\/*?:\[\]]", "_", str(raw_name or "Sheet"))[:31] or "Sheet"
            base = sheet_name
            idx = 1
            while sheet_name in used:
                suffix = f"_{idx}"
                sheet_name = f"{base[:31 - len(suffix)]}{suffix}"
                idx += 1
            used.add(sheet_name)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=sheet_name, index=False)
    return str(final_path)


def _find_latest_file(asset_pkg: Path, prefix: str) -> Optional[Path]:
    files = [p for p in asset_pkg.iterdir() if p.is_file() and p.name.lower().endswith(".xlsx") and p.name.startswith(prefix)]
    if not files:
        return None
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]


def _detect_year_tokens(text: str) -> List[str]:
    if not text:
        return []
    return sorted({m.group(1).upper() for m in YEAR_TOKEN_RE.finditer(text)})


def _serialize_year_values(row: pd.Series, year_columns: List[str]) -> str:
    values = []
    for col in year_columns:
        v = _normalize_text(row.get(col, ""))
        if v:
            values.append(f"{col}={v}")
    return "; ".join(values)


def _preview_row(row: pd.Series, max_cols: int = 6, max_len: int = 240) -> str:
    vals = []
    for col in row.index.tolist()[:max_cols]:
        vals.append(f"{col}:{_normalize_text(row.get(col,''))}")
    text = " | ".join(vals)
    return (text[:max_len] + "...") if len(text) > max_len else text


def _possible_metric_label_columns(df: pd.DataFrame, detected_year_cols: List[str]) -> List[str]:
    candidates = []
    for col in df.columns.tolist()[:5]:
        col_name = str(col)
        if col_name in detected_year_cols:
            continue
        series = df[col].fillna("").astype(str).head(30)
        text_like = 0
        non_empty = 0
        for v in series.tolist():
            s = _normalize_text(v)
            if not s:
                continue
            non_empty += 1
            compact = _compact_text(s).replace("%", "").replace(",", "")
            if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", compact):
                text_like += 1
        if non_empty > 0 and text_like / non_empty >= 0.4:
            candidates.append(col_name)
    return candidates


def _pick_col(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    for c in df.columns:
        cc = _normalize_text(c).lower()
        if any(k in cc for k in keywords):
            return c
    return None


def _load_classification_context(file_04: Optional[Path]) -> pd.DataFrame:
    if not file_04 or not file_04.exists():
        return pd.DataFrame(columns=["table_index", "table_type", "confidence", "reason", "matched_keywords"])
    try:
        xls = pd.ExcelFile(file_04, engine="openpyxl")
        sheet = xls.sheet_names[0]
        df = pd.read_excel(file_04, sheet_name=sheet, engine="openpyxl")
        if df.empty:
            return pd.DataFrame(columns=["table_index", "table_type", "confidence", "reason", "matched_keywords"])

        c_idx = _pick_col(df, ["table_index", "索引"])
        c_type = _pick_col(df, ["table_type", "类型"])
        c_conf = _pick_col(df, ["confidence", "置信"])
        c_reason = _pick_col(df, ["reason", "原因"])
        c_kw = _pick_col(df, ["matched_keywords", "关键词"])

        out = pd.DataFrame(
            {
                "table_index": df[c_idx] if c_idx else "",
                "table_type": df[c_type] if c_type else "",
                "confidence": df[c_conf] if c_conf else "",
                "reason": df[c_reason] if c_reason else "",
                "matched_keywords": df[c_kw] if c_kw else "",
            }
        )
        return out
    except Exception:
        return pd.DataFrame(columns=["table_index", "table_type", "confidence", "reason", "matched_keywords"])


def diagnose(asset_package: Path) -> str:
    file_02 = _find_latest_file(asset_package, "02_")
    file_04 = _find_latest_file(asset_package, "04_")
    if not file_02:
        raise FileNotFoundError(f"02 file not found in {asset_package}")

    xls_02 = pd.ExcelFile(file_02, engine="openpyxl")
    sheet_overview_rows = []
    row_scan_rows = []
    header_scan_rows = []

    for sheet_name in xls_02.sheet_names:
        try:
            df = pd.read_excel(file_02, sheet_name=sheet_name, engine="openpyxl")
        except Exception as exc:
            sheet_overview_rows.append(
                {
                    "sheet_name": sheet_name,
                    "row_count": "",
                    "col_count": "",
                    "columns_raw": "",
                    "detected_year_columns": "",
                    "detected_year_count": 0,
                    "possible_header_year_tokens": "",
                    "possible_metric_label_columns": "",
                    "matched_metric_row_count": 0,
                    "skip_reason": f"read_sheet_error:{exc}",
                }
            )
            continue

        row_count, col_count = df.shape
        columns_raw = "|".join([str(c) for c in df.columns.tolist()])
        year_pairs = _extract_year_columns(df) if not df.empty else []
        year_cols_raw = [raw for raw, _ in year_pairs]
        detected_year_count = len(year_cols_raw)

        header_tokens = set()
        for c in df.columns.tolist():
            for token in _detect_year_tokens(_normalize_text(c)):
                header_tokens.add(token)
                header_scan_rows.append(
                    {
                        "sheet_name": sheet_name,
                        "location_type": "column_name",
                        "row_index": "",
                        "column_name": str(c),
                        "cell_value": str(c),
                        "detected_year_token": token,
                    }
                )
        for ridx in range(min(5, row_count)):
            row = df.iloc[ridx]
            for col in df.columns.tolist():
                val = _normalize_text(row.get(col, ""))
                if not val:
                    continue
                tokens = _detect_year_tokens(val)
                if not tokens:
                    continue
                for token in tokens:
                    header_tokens.add(token)
                    header_scan_rows.append(
                        {
                            "sheet_name": sheet_name,
                            "location_type": "row_cell",
                            "row_index": ridx,
                            "column_name": str(col),
                            "cell_value": val,
                            "detected_year_token": token,
                        }
                    )

        label_candidates = _possible_metric_label_columns(df, year_cols_raw)
        matched_metric_row_count = 0

        if not df.empty:
            for ridx, row in df.iterrows():
                candidate_label, label_col = _find_row_label(row)
                match = _match_standard_metric(candidate_label)
                detected_values = _serialize_year_values(row, year_cols_raw)
                if match and detected_values:
                    matched_metric_row_count += 1
                row_scan_rows.append(
                    {
                        "sheet_name": sheet_name,
                        "row_index": int(ridx),
                        "candidate_label": candidate_label,
                        "label_column": label_col,
                        "matched_standard_metric": match.get("standard_metric", "") if match else "",
                        "matched_alias": match.get("matched_alias", "") if match else "",
                        "match_method": match.get("match_method", "") if match else "",
                        "confidence": match.get("confidence", "") if match else "",
                        "detected_values_by_year": detected_values,
                        "row_preview": _preview_row(row),
                    }
                )

        if detected_year_count == 0:
            skip_reason = "no_year_columns_detected"
        elif len(label_candidates) == 0:
            skip_reason = "no_metric_label_candidates"
        elif matched_metric_row_count == 0:
            skip_reason = "no_metric_rows_matched"
        else:
            skip_reason = "ok_has_candidates"

        sheet_overview_rows.append(
            {
                "sheet_name": sheet_name,
                "row_count": row_count,
                "col_count": col_count,
                "columns_raw": columns_raw,
                "detected_year_columns": "|".join(year_cols_raw),
                "detected_year_count": detected_year_count,
                "possible_header_year_tokens": "|".join(sorted(header_tokens)),
                "possible_metric_label_columns": "|".join(label_candidates),
                "matched_metric_row_count": matched_metric_row_count,
                "skip_reason": skip_reason,
            }
        )

    sheet_overview_df = pd.DataFrame(sheet_overview_rows)
    row_scan_df = pd.DataFrame(row_scan_rows)
    header_scan_df = pd.DataFrame(header_scan_rows)
    classification_df = _load_classification_context(file_04)

    out_path = asset_package / DEFAULT_OUTPUT_NAME
    report_path = _save_excel_robustly(
        {
            "sheet_overview": sheet_overview_df,
            "row_scan_details": row_scan_df,
            "header_scan_details": header_scan_df,
            "classification_context": classification_df,
        },
        out_path,
    )

    print(f"report_path={report_path}")
    for _, r in sheet_overview_df.iterrows():
        print(
            f"{r['sheet_name']} | skip_reason={r['skip_reason']} | "
            f"detected_year_columns={r['detected_year_columns']} | "
            f"matched_metric_row_count={r['matched_metric_row_count']}"
        )
    return report_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Diagnose why financial standardizer has zero detail rows.")
    ap.add_argument("--asset-package", default=DEFAULT_ASSET_PACKAGE, help="Asset package path.")
    args = ap.parse_args()

    diagnose(Path(args.asset_package))


if __name__ == "__main__":
    main()
