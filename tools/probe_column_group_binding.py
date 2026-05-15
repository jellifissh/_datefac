import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from financial_standardizer import standardize_core_financials


DEFAULT_ASSET_STEM = "H3_AP202605141822317484_1"
DEFAULT_OUTPUT_BASE = Path(r"D:\_datefac\output")

YEAR_TOKEN_RE = re.compile(r"20\d{2}(?:[AE])?|20\d{2}年", re.IGNORECASE)
METRIC_KEYWORDS = [
    "营业收入",
    "归属母公司",
    "归母净利润",
    "毛利率",
    "ROE",
    "每股收益",
    "EPS",
    "P/E",
    "PE",
    "P/B",
    "PB",
    "EV/EBITDA",
]
STATEMENT_KEYWORDS = [
    "利润表",
    "现金流量表",
    "资产负债表",
    "财务分析指标",
    "每股指标",
    "估值指标",
]
CORE_METRICS = ["营业收入", "归属母公司净利润", "毛利率", "ROE", "每股收益", "P/E", "P/B", "EV/EBITDA"]


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _safe_excel_path(path: Path) -> Path:
    if not path.exists():
        return path
    try:
        with open(path, "a", encoding="utf-8"):
            pass
        return path
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name))[:31] or "Sheet"
    base = s
    idx = 1
    while s in used:
        suffix = f"_{idx}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        idx += 1
    used.add(s)
    return s


def _find_asset_pkg(output_base: Path, asset_stem: str) -> Path:
    matches = [p for p in output_base.iterdir() if p.is_dir() and p.name.startswith(asset_stem)]
    if not matches:
        raise FileNotFoundError(f"Asset package not found for stem={asset_stem}")
    return sorted(matches, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _find_latest_file(pkg: Path, prefix: str) -> Optional[Path]:
    files = [p for p in pkg.iterdir() if p.is_file() and p.suffix.lower() == ".xlsx" and p.name.startswith(prefix)]
    if not files:
        return None
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _detect_target_table_index(file_05: Path) -> int:
    detail = pd.read_excel(file_05, sheet_name=1, engine="openpyxl").fillna("")
    if "source_table_index" not in detail.columns or detail.empty:
        return 1
    ctr = Counter([int(x) for x in detail["source_table_index"].tolist() if _norm(x) != ""])
    if not ctr:
        return 1
    return ctr.most_common(1)[0][0]


def _map_table_index_to_sheet(file_02: Path, table_index: int) -> str:
    xls = pd.ExcelFile(file_02, engine="openpyxl")
    if len(xls.sheet_names) <= 1:
        return xls.sheet_names[-1]
    idx_sheet = pd.read_excel(file_02, sheet_name=0, engine="openpyxl").fillna("")
    cols = [str(c) for c in idx_sheet.columns]
    if "table_index" in cols and "sheet_name" in cols:
        for _, row in idx_sheet.iterrows():
            try:
                if int(row["table_index"]) == int(table_index):
                    sn = _norm(row["sheet_name"])
                    if sn and sn in xls.sheet_names:
                        return sn
            except Exception:
                continue
    # fallback: main data sheet often at index 2
    if len(xls.sheet_names) > 2:
        return xls.sheet_names[2]
    return xls.sheet_names[-1]


def _column_non_empty_ratio(df: pd.DataFrame) -> Dict[str, float]:
    ratios = {}
    n = max(len(df), 1)
    for c in df.columns:
        ser = df[c].astype(str)
        non_empty = (ser != "").sum()
        ratios[str(c)] = float(non_empty) / n
    return ratios


def _continuous_groups(indices: List[int]) -> List[Tuple[int, int]]:
    if not indices:
        return []
    out = []
    start = indices[0]
    prev = indices[0]
    for i in indices[1:]:
        if i == prev + 1:
            prev = i
            continue
        out.append((start, prev))
        start = i
        prev = i
    out.append((start, prev))
    return out


def _profile_low_empty_gap_groups(df: pd.DataFrame) -> List[Tuple[int, int]]:
    ratios = _column_non_empty_ratio(df)
    gap_cols = []
    cols = list(df.columns)
    for i, c in enumerate(cols):
        r = ratios[str(c)]
        if r <= 0.35:
            gap_cols.append(i)
    if not gap_cols:
        return [(0, len(cols)-1)]
    groups = []
    start = 0
    for g in gap_cols:
        if g - 1 >= start:
            groups.append((start, g-1))
        start = g + 1
    if start <= len(cols)-1:
        groups.append((start, len(cols)-1))
    return [g for g in groups if g[1]-g[0]+1 >= 3]


def _profile_keyword_anchor_groups(df: pd.DataFrame) -> List[Tuple[int, int]]:
    cols = list(df.columns)
    anchors = []
    for i, c in enumerate(cols):
        col_text = " ".join([_norm(v) for v in df[c].tolist()[:40]])
        if any(k in col_text for k in STATEMENT_KEYWORDS):
            anchors.append(i)
    anchors = sorted(set(anchors))
    if not anchors:
        return []
    groups = []
    for idx, a in enumerate(anchors):
        left = max(0, a-1)
        right = (anchors[idx+1]-1) if idx+1 < len(anchors) else len(cols)-1
        if right - left + 1 >= 3:
            groups.append((left, right))
    return groups


def _profile_year_header_groups(df: pd.DataFrame) -> List[Tuple[int, int]]:
    cols = list(df.columns)
    year_cols = []
    for i, c in enumerate(cols):
        col_values = [_norm(v) for v in df[c].tolist()[:15]]
        hits = sum(1 for v in col_values if YEAR_TOKEN_RE.search(v))
        if hits >= 1:
            year_cols.append(i)
    year_groups = _continuous_groups(year_cols)
    groups = []
    for s, e in year_groups:
        left = max(0, s-2)
        right = min(len(cols)-1, e+1)
        if right >= left and right - left + 1 >= 3:
            groups.append((left, right))
    return groups


def _profile_sliding_window_groups(df: pd.DataFrame) -> List[Tuple[int, int]]:
    cols = list(df.columns)
    n = len(cols)
    groups = []
    for w in (4, 5, 6):
        step = 2
        i = 0
        while i + w - 1 < n:
            left = i
            right = i + w - 1
            if right >= left:
                groups.append((left, right))
            i += step
    return groups


def _extract_sub_df(df: pd.DataFrame, cstart: int, cend: int) -> pd.DataFrame:
    cols = list(df.columns)[cstart:cend+1]
    sub = df.loc[:, cols].copy().fillna("")
    return sub


def _count_tokens_in_df(df: pd.DataFrame) -> Tuple[int, int, int]:
    year_cnt = 0
    metric_cnt = 0
    statement_cnt = 0
    for v in df.astype(str).values.flatten().tolist():
        t = _norm(v)
        if not t:
            continue
        if YEAR_TOKEN_RE.search(t):
            year_cnt += 1
        for k in METRIC_KEYWORDS:
            if k.lower() in t.lower():
                metric_cnt += 1
        for k in STATEMENT_KEYWORDS:
            if k in t:
                statement_cnt += 1
    return year_cnt, metric_cnt, statement_cnt


def _preview_df(df: pd.DataFrame, rows: int = 3) -> str:
    lines = []
    for i in range(min(rows, len(df))):
        row = [_norm(x) for x in df.iloc[i].tolist() if _norm(x)]
        lines.append(" | ".join(row[:8]))
    return " || ".join(lines)


def _probe_group(sub_df: pd.DataFrame) -> Dict[str, object]:
    try:
        result = standardize_core_financials([sub_df], classification_results=None, logger=None, config=None)
        wide = result.get("wide_df", pd.DataFrame()).fillna("")
        detail = result.get("detail_df", pd.DataFrame()).fillna("")
    except Exception as e:
        return {
            "label_hit_metric_count": 0,
            "value_valid_metric_count": 0,
            "wide_non_empty_metric_count": 0,
            "hit_metrics": "",
            "valid_metrics": "",
            "invalid_metrics": "",
            "suspicious_metrics": "",
            "missing_metrics": "|".join(CORE_METRICS),
            "example_source_rows": f"probe_error:{e}",
            "invalid_metric_count": len(CORE_METRICS),
        }

    label_hit = 0
    hit_metrics = []
    valid_metrics = []
    invalid_metrics = []
    suspicious_metrics = []
    missing_metrics = []
    wide_non_empty = 0

    year_cols = [c for c in wide.columns if YEAR_TOKEN_RE.search(_norm(c))]
    for metric in CORE_METRICS:
        row = wide[wide["指标"] == metric] if "指标" in wide.columns else pd.DataFrame()
        if row.empty:
            missing_metrics.append(metric)
            continue
        r = row.iloc[0]
        source = _norm(r.get("来源表", ""))
        if source != "":
            label_hit += 1
            hit_metrics.append(metric)
        has_value = any(_norm(r.get(c, "")) != "" for c in year_cols)
        if has_value:
            wide_non_empty += 1
        status = _norm(r.get("value_validation_status", ""))
        if status == "valid":
            valid_metrics.append(metric)
        elif status == "invalid":
            invalid_metrics.append(metric)
        elif status == "suspicious":
            suspicious_metrics.append(metric)
        else:
            if source != "":
                suspicious_metrics.append(metric)
            else:
                missing_metrics.append(metric)

    value_valid_metric_count = len(valid_metrics)
    invalid_metric_count = len(invalid_metrics)
    ex_rows = []
    if not detail.empty:
        for _, r in detail.head(5).iterrows():
            ex_rows.append(f"{_norm(r.get('标准指标',''))}:{_norm(r.get('source_row_label',''))}")

    return {
        "label_hit_metric_count": int(label_hit),
        "value_valid_metric_count": int(value_valid_metric_count),
        "wide_non_empty_metric_count": int(wide_non_empty),
        "hit_metrics": "|".join(hit_metrics),
        "valid_metrics": "|".join(valid_metrics),
        "invalid_metrics": "|".join(invalid_metrics),
        "suspicious_metrics": "|".join(suspicious_metrics),
        "missing_metrics": "|".join(missing_metrics),
        "example_source_rows": " || ".join(ex_rows),
        "invalid_metric_count": int(invalid_metric_count),
    }


def run_probe(asset_pkg: Path) -> Tuple[Path, pd.DataFrame]:
    file_02 = _find_latest_file(asset_pkg, "02_")
    file_05 = _find_latest_file(asset_pkg, "05_")
    if not file_02 or not file_05:
        raise FileNotFoundError("Missing 02 or 05 file.")

    target_table_index = _detect_target_table_index(file_05)
    target_sheet = _map_table_index_to_sheet(file_02, target_table_index)
    df = pd.read_excel(file_02, sheet_name=target_sheet, engine="openpyxl").fillna("")
    df.columns = [str(c) for c in df.columns]

    profiles = {
        "low_empty_gap_groups": _profile_low_empty_gap_groups(df),
        "keyword_anchor_groups": _profile_keyword_anchor_groups(df),
        "year_header_groups": _profile_year_header_groups(df),
        "sliding_window_groups": _profile_sliding_window_groups(df),
    }

    groups: List[Dict[str, object]] = []
    seen = set()
    profile_count = {}
    for profile_name, ranges in profiles.items():
        profile_count[profile_name] = len(ranges)
        gidx = 0
        for cstart, cend in ranges:
            if cstart < 0 or cend < 0:
                continue
            if cend < cstart:
                continue
            key = (cstart, cend)
            # keep duplicates across profiles (for comparison), but avoid exact same profile dup
            if (profile_name, key) in seen:
                continue
            seen.add((profile_name, key))
            sub = _extract_sub_df(df, cstart, cend)
            if sub.shape[0] < 3 or sub.shape[1] < 3:
                continue
            non_empty_cnt = int((sub.astype(str) != "").sum().sum())
            year_cnt, metric_cnt, stmt_cnt = _count_tokens_in_df(sub)
            probe = _probe_group(sub)
            groups.append(
                {
                    "group_profile": profile_name,
                    "group_index": gidx,
                    "source_sheet": target_sheet,
                    "source_table_index": target_table_index,
                    "col_start": int(cstart),
                    "col_end": int(cend),
                    "row_count": int(sub.shape[0]),
                    "col_count": int(sub.shape[1]),
                    "non_empty_cell_count": int(non_empty_cnt),
                    "year_token_count": int(year_cnt),
                    "metric_keyword_count": int(metric_cnt),
                    "statement_keyword_count": int(stmt_cnt),
                    "preview": _preview_df(sub),
                    **probe,
                }
            )
            gidx += 1

    summary_df = pd.DataFrame(groups)
    if summary_df.empty:
        raise RuntimeError("No valid column groups generated.")

    summary_df["sort_key_valid"] = -pd.to_numeric(summary_df["value_valid_metric_count"], errors="coerce").fillna(0)
    summary_df["sort_key_non_empty"] = -pd.to_numeric(summary_df["wide_non_empty_metric_count"], errors="coerce").fillna(0)
    summary_df["sort_key_invalid"] = pd.to_numeric(summary_df["invalid_metric_count"], errors="coerce").fillna(999)
    summary_df["sort_key_col_span"] = (pd.to_numeric(summary_df["col_end"], errors="coerce").fillna(0) - pd.to_numeric(summary_df["col_start"], errors="coerce").fillna(0)).abs()
    summary_df = summary_df.sort_values(
        ["sort_key_valid", "sort_key_non_empty", "sort_key_invalid", "sort_key_col_span"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)

    best = summary_df.iloc[0]
    best_sub = _extract_sub_df(df, int(best["col_start"]), int(best["col_end"]))

    report_path = _safe_excel_path(asset_pkg / "21_column_group_binding_probe.xlsx")
    used = set()
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        summary_df.drop(
            columns=["sort_key_valid", "sort_key_non_empty", "sort_key_invalid", "sort_key_col_span"], errors="ignore"
        ).to_excel(writer, sheet_name=_safe_sheet_name("group_summary", used), index=False)
        summary_df[
            [
                "group_profile",
                "group_index",
                "source_sheet",
                "col_start",
                "col_end",
                "label_hit_metric_count",
                "value_valid_metric_count",
                "wide_non_empty_metric_count",
                "hit_metrics",
                "valid_metrics",
                "invalid_metrics",
                "suspicious_metrics",
                "missing_metrics",
                "example_source_rows",
                "preview",
            ]
        ].to_excel(writer, sheet_name=_safe_sheet_name("financial_probe_details", used), index=False)
        best_sub.to_excel(writer, sheet_name=_safe_sheet_name("best_group_preview", used), index=False)
        df.to_excel(writer, sheet_name=_safe_sheet_name("original_table", used), index=False)

    print(f"asset_package={asset_pkg.name}")
    print(f"source_sheet={target_sheet}")
    print(f"total_groups={len(summary_df)}")
    for name, cnt in profile_count.items():
        print(f"profile={name} group_count={cnt}")
    print(f"best_group_profile={best['group_profile']}")
    print(f"best_group_index={int(best['group_index'])}")
    print(f"best_value_valid_metric_count={int(best['value_valid_metric_count'])}")
    print(f"best_valid_metrics={best['valid_metrics']}")
    print(f"best_preview={best['preview']}")
    print(f"report_path={report_path}")
    return report_path, summary_df


def main():
    parser = argparse.ArgumentParser(description="Probe column group binding for structured table misalignment.")
    parser.add_argument("--asset-stem", default=DEFAULT_ASSET_STEM, help="Asset package stem, e.g. H3_AP..._1")
    parser.add_argument("--asset-path", default="", help="Explicit asset package path")
    parser.add_argument("--output-base", default=str(DEFAULT_OUTPUT_BASE), help="Output base directory")
    args = parser.parse_args()

    output_base = Path(args.output_base)
    if args.asset_path:
        asset_pkg = Path(args.asset_path)
    else:
        asset_pkg = _find_asset_pkg(output_base, args.asset_stem)

    run_probe(asset_pkg)


if __name__ == "__main__":
    main()
