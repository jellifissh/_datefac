import argparse
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extractor_quality import score_table_block
from financial_standardizer import standardize_core_financials
from table_block import dataframe_to_table_block


DEFAULT_ASSET_PACKAGE = Path(r"D:\_datefac\output\H3_AP202605121822223662_1_资产包")
DEFAULT_REPORT_NAME = "18_glued_table_split_probe.xlsx"

CORE_METRICS = [
    "营业收入",
    "归属母公司净利润",
    "毛利率",
    "ROE",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
]

FINANCIAL_KEYWORDS = [
    "财务报表",
    "财务预测",
    "主要财务指标",
    "利润表",
    "资产负债表",
    "现金流量表",
    "财务比率",
    "估值指标",
    "盈利预测",
]

METRIC_KEYWORDS = [
    "营业收入",
    "归母净利润",
    "归属母公司",
    "毛利率",
    "ROE",
    "EPS",
    "每股收益",
    "PE",
    "P/E",
    "PB",
    "P/B",
    "EV/EBITDA",
]

ANCHOR_KEYWORDS = ["资产负债表", "利润表", "现金流量表", "财务比率", "主要财务指标"]
YEAR_PATTERN = re.compile(r"(20\d{2}\s*[AE]?|20\d{2}\s*年)", flags=re.IGNORECASE)


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", _normalize_text(name) or "sheet")
    cleaned = cleaned[:31]
    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def _save_excel_robustly(sheet_df_map: Dict[str, pd.DataFrame], target_path: Path) -> Path:
    final_path = target_path
    if target_path.exists():
        try:
            with open(target_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = target_path.with_name(f"{target_path.stem}_copy_{ts}{target_path.suffix}")

    used_names = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for raw_name, df in sheet_df_map.items():
            safe = _safe_sheet_name(raw_name, used_names)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, index=False, sheet_name=safe)
    return final_path


def _find_file(asset_pkg: Path, prefix: str) -> Optional[Path]:
    files = sorted(asset_pkg.glob(f"{prefix}_*.xlsx"))
    return files[0] if files else None


def _collect_cells(df: pd.DataFrame) -> List[str]:
    if df is None or df.empty:
        return []
    values = df.fillna("").astype(str).values.flatten().tolist()
    return [v.strip() for v in values if str(v).strip()]


def _count_keyword_hits(text: str, keywords: List[str]) -> Tuple[int, List[str]]:
    hit_list = []
    total = 0
    for kw in keywords:
        cnt = text.count(kw)
        if cnt > 0:
            hit_list.append(kw)
            total += cnt
    return total, hit_list


def _build_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 6, max_len: int = 320) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join([_normalize_text(v) for v in row.tolist()]))
    text = " || ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df.copy()
    normalized = df.fillna("").astype(str)
    normalized = normalized.apply(lambda col: col.map(lambda v: re.sub(r"\s+", " ", v).strip()))
    normalized = normalized.loc[(normalized != "").any(axis=1), (normalized != "").any(axis=0)]
    if normalized.empty:
        return pd.DataFrame()
    return normalized.reset_index(drop=True)


def _candidate_record(
    source_sheet: str,
    profile: str,
    split_index: int,
    row_start: int,
    row_end: int,
    col_start: int,
    col_end: int,
    df: pd.DataFrame,
) -> Dict[str, object]:
    cleaned = _normalize_df(df)
    block = dataframe_to_table_block(
        df=cleaned,
        backend="pdfplumber_split_probe",
        page="",
        table_index=split_index,
        source_meta={"split_profile": profile, "source_sheet": source_sheet},
    )
    score = score_table_block(block)

    cells = _collect_cells(cleaned)
    all_text = " ".join(cells)
    financial_keyword_count, financial_keywords = _count_keyword_hits(all_text, FINANCIAL_KEYWORDS)
    metric_keyword_count, metric_keywords = _count_keyword_hits(all_text, METRIC_KEYWORDS)
    year_token_count = len(YEAR_PATTERN.findall(all_text))

    return {
        "split_profile": profile,
        "split_index": split_index,
        "source_sheet": source_sheet,
        "row_start": row_start,
        "row_end": row_end,
        "col_start": col_start,
        "col_end": col_end,
        "row_count": int(cleaned.shape[0]),
        "col_count": int(cleaned.shape[1]),
        "non_empty_cell_count": int(block.non_empty_cell_count or 0),
        "financial_keyword_count": int(financial_keyword_count),
        "financial_keywords": "|".join(financial_keywords),
        "metric_keyword_count": int(metric_keyword_count),
        "metric_keywords": "|".join(metric_keywords),
        "year_token_count": int(year_token_count),
        "quality_score": float(score.get("quality_score", 0.0)),
        "quality_level": score.get("quality_level", ""),
        "quality_flags": score.get("quality_flags", ""),
        "preview": _build_preview(cleaned),
        "_df": cleaned,
    }


def _valid_candidate(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False
    r, c = df.shape
    return r >= 5 and c >= 3


def _column_gap_split(df: pd.DataFrame, source_sheet: str) -> List[Dict[str, object]]:
    if df is None or df.empty:
        return []
    n_rows, n_cols = df.shape
    if n_cols < 4:
        return []

    non_empty_ratios = []
    for col_idx in range(n_cols):
        col = df.iloc[:, col_idx].fillna("").astype(str).str.strip()
        ratio = float((col != "").sum()) / float(max(1, n_rows))
        non_empty_ratios.append(ratio)

    separator_cols = [i for i, ratio in enumerate(non_empty_ratios) if ratio <= 0.10]
    if not separator_cols:
        return []

    segments = []
    prev = 0
    for sep in separator_cols:
        if sep - prev >= 3:
            segments.append((prev, sep - 1))
        prev = sep + 1
    if n_cols - prev >= 3:
        segments.append((prev, n_cols - 1))

    results = []
    split_index = 1
    for c0, c1 in segments:
        sub = df.iloc[:, c0 : c1 + 1]
        if not _valid_candidate(_normalize_df(sub)):
            continue
        rec = _candidate_record(
            source_sheet=source_sheet,
            profile="column_gap_split",
            split_index=split_index,
            row_start=1,
            row_end=n_rows,
            col_start=c0 + 1,
            col_end=c1 + 1,
            df=sub,
        )
        split_index += 1
        results.append(rec)
    return results


def _cluster_positions(values: List[int], max_gap: int = 2) -> List[List[int]]:
    if not values:
        return []
    values = sorted(set(values))
    clusters = [[values[0]]]
    for v in values[1:]:
        if v - clusters[-1][-1] <= max_gap:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return clusters


def _keyword_anchor_split(df: pd.DataFrame, source_sheet: str) -> List[Dict[str, object]]:
    if df is None or df.empty:
        return []
    n_rows, n_cols = df.shape
    anchor_cols = []
    for r in range(min(n_rows, 12)):
        for c in range(n_cols):
            text = _normalize_text(df.iat[r, c])
            if not text:
                continue
            for kw in ANCHOR_KEYWORDS:
                if kw in text:
                    anchor_cols.append(c)
                    break

    if not anchor_cols:
        return []

    clusters = _cluster_positions(anchor_cols, max_gap=2)
    cluster_centers = [int(round(sum(cluster) / len(cluster))) for cluster in clusters]
    cluster_centers = sorted(set(cluster_centers))
    if not cluster_centers:
        return []

    bounds: List[Tuple[int, int]] = []
    for i, center in enumerate(cluster_centers):
        left = 0 if i == 0 else int((cluster_centers[i - 1] + center) / 2) + 1
        right = n_cols - 1 if i == len(cluster_centers) - 1 else int((center + cluster_centers[i + 1]) / 2)
        left = max(0, min(left, n_cols - 1))
        right = max(left, min(right, n_cols - 1))
        if right - left + 1 >= 3:
            bounds.append((left, right))

    results = []
    split_index = 1
    for c0, c1 in bounds:
        sub = df.iloc[:, c0 : c1 + 1]
        if not _valid_candidate(_normalize_df(sub)):
            continue
        rec = _candidate_record(
            source_sheet=source_sheet,
            profile="keyword_anchor_split",
            split_index=split_index,
            row_start=1,
            row_end=n_rows,
            col_start=c0 + 1,
            col_end=c1 + 1,
            df=sub,
        )
        split_index += 1
        results.append(rec)
    return results


def _fixed_window_split(df: pd.DataFrame, source_sheet: str) -> List[Dict[str, object]]:
    if df is None or df.empty:
        return []
    n_rows, n_cols = df.shape
    if n_cols < 3:
        return []

    windows = [4, 5, 6]
    step_overlap = 1
    results = []
    split_index = 1

    for win in windows:
        if n_cols < win:
            continue
        step = max(1, win - step_overlap)
        for start in range(0, n_cols - win + 1, step):
            end = start + win - 1
            sub = df.iloc[:, start : end + 1]
            if not _valid_candidate(_normalize_df(sub)):
                continue
            rec = _candidate_record(
                source_sheet=source_sheet,
                profile="fixed_window_split",
                split_index=split_index,
                row_start=1,
                row_end=n_rows,
                col_start=start + 1,
                col_end=end + 1,
                df=sub,
            )
            split_index += 1
            results.append(rec)
    return results


def _dedup_candidates(candidates: List[Dict[str, object]]) -> List[Dict[str, object]]:
    seen = set()
    kept = []
    for rec in candidates:
        key = (
            rec.get("split_profile"),
            rec.get("source_sheet"),
            rec.get("row_start"),
            rec.get("row_end"),
            rec.get("col_start"),
            rec.get("col_end"),
        )
        if key in seen:
            continue
        seen.add(key)
        kept.append(rec)
    return kept


def _resolve_glued_target_sheet(asset_pkg: Path, file_02a: Path) -> Tuple[str, pd.DataFrame]:
    report17 = asset_pkg.parent / "17_raw_table_business_relevance_report.xlsx"
    candidate_sheet_names: List[str] = []
    if report17.exists():
        try:
            details = pd.read_excel(report17, sheet_name="table_relevance_details")
            sub = details[
                (details["asset_package"].astype(str) == asset_pkg.name)
                & (details["business_table_type"].astype(str) == "glued_financial_table")
            ]
            candidate_sheet_names.extend(sub["sheet_name"].astype(str).tolist())
        except Exception:
            pass

    candidate_sheet_names.extend(["raw_pdfplumber_p3_t1", "p3_t1"])
    x02a = pd.ExcelFile(file_02a, engine="openpyxl")

    for s in candidate_sheet_names:
        if s in x02a.sheet_names:
            df = pd.read_excel(file_02a, sheet_name=s, engine="openpyxl")
            return s, df

    for s in x02a.sheet_names:
        if s.lower().startswith("raw_") and "p3_t1" in s:
            df = pd.read_excel(file_02a, sheet_name=s, engine="openpyxl")
            return s, df

    for s in x02a.sheet_names[1:]:
        df = pd.read_excel(file_02a, sheet_name=s, engine="openpyxl")
        if df.shape[1] >= 8:
            return s, df
    return x02a.sheet_names[1], pd.read_excel(file_02a, sheet_name=x02a.sheet_names[1], engine="openpyxl")


def _run_financial_probe(candidate_df: pd.DataFrame) -> Dict[str, object]:
    try:
        result = standardize_core_financials([candidate_df], classification_results=None, logger=None, config=None)
        detail_df = result.get("detail_df", pd.DataFrame())
        if detail_df is None:
            detail_df = pd.DataFrame()
        hit_metrics: List[str] = []
        if not detail_df.empty and "标准指标" in detail_df.columns:
            hit_metrics = [
                str(v).strip()
                for v in detail_df["标准指标"].dropna().astype(str).tolist()
                if str(v).strip()
            ]
            hit_metrics = list(dict.fromkeys(hit_metrics))
        hit_count = len(hit_metrics)
        missing = [m for m in CORE_METRICS if m not in hit_metrics]
        return {
            "financial_detail_count": int(len(detail_df)),
            "financial_metric_hit_count": int(hit_count),
            "financial_hit_metrics": "|".join(hit_metrics),
            "financial_missing_metrics": "|".join(missing),
            "_probe_error": "",
        }
    except Exception as exc:
        return {
            "financial_detail_count": 0,
            "financial_metric_hit_count": 0,
            "financial_hit_metrics": "",
            "financial_missing_metrics": "|".join(CORE_METRICS),
            "_probe_error": str(exc),
        }


def run_probe(asset_package: Path) -> Tuple[Path, pd.DataFrame, pd.DataFrame]:
    asset_pkg = Path(asset_package)
    file_02a = _find_file(asset_pkg, "02A")
    file_02 = _find_file(asset_pkg, "02")
    if file_02a is None or file_02 is None:
        raise FileNotFoundError("Missing 02A or 02 in asset package.")

    source_sheet, glued_df = _resolve_glued_target_sheet(asset_pkg, file_02a)
    glued_df = _normalize_df(glued_df)
    if glued_df.empty:
        raise ValueError("Resolved glued table is empty.")

    candidates: List[Dict[str, object]] = []
    candidates.extend(_column_gap_split(glued_df, source_sheet=source_sheet))
    candidates.extend(_keyword_anchor_split(glued_df, source_sheet=source_sheet))
    candidates.extend(_fixed_window_split(glued_df, source_sheet=source_sheet))
    candidates = _dedup_candidates(candidates)

    split_summary_rows = []
    financial_probe_rows = []
    raw_candidate_sheets: Dict[str, pd.DataFrame] = {}

    profile_counters = defaultdict(int)
    for rec in candidates:
        profile = str(rec.get("split_profile", "unknown"))
        profile_counters[profile] += 1
        probe = _run_financial_probe(rec["_df"])
        rec["financial_detail_count"] = probe["financial_detail_count"]
        rec["financial_metric_hit_count"] = probe["financial_metric_hit_count"]
        rec["financial_hit_metrics"] = probe["financial_hit_metrics"]
        rec["financial_missing_metrics"] = probe["financial_missing_metrics"]
        rec["probe_error"] = probe["_probe_error"]

        split_summary_rows.append(
            {k: v for k, v in rec.items() if k != "_df"}
        )
        financial_probe_rows.append(
            {
                "split_profile": rec["split_profile"],
                "split_index": rec["split_index"],
                "source_sheet": rec["source_sheet"],
                "financial_detail_count": rec["financial_detail_count"],
                "financial_metric_hit_count": rec["financial_metric_hit_count"],
                "financial_hit_metrics": rec["financial_hit_metrics"],
                "financial_missing_metrics": rec["financial_missing_metrics"],
                "probe_error": rec["probe_error"],
            }
        )
        raw_candidate_sheets[f"split_{profile}_{int(rec['split_index'])}"] = rec["_df"]

    split_summary_df = pd.DataFrame(split_summary_rows)
    probe_summary_df = pd.DataFrame(financial_probe_rows)

    workbook = {
        "split_summary": split_summary_df,
        "financial_probe_summary": probe_summary_df,
        "original_glued_table": glued_df,
    }
    workbook.update(raw_candidate_sheets)

    report_path = asset_pkg / DEFAULT_REPORT_NAME
    final_path = _save_excel_robustly(workbook, report_path)
    return final_path, split_summary_df, probe_summary_df


def _print_summary(report_path: Path, split_summary_df: pd.DataFrame, probe_summary_df: pd.DataFrame) -> None:
    print(f"report_path={report_path}")
    total = len(split_summary_df)
    print(f"total_candidates={total}")

    if split_summary_df.empty:
        print("profile_counts=none")
        print("best_candidate=none")
        return

    profile_counts = (
        split_summary_df.groupby("split_profile")
        .size()
        .reset_index(name="candidate_count")
    )
    for _, row in profile_counts.iterrows():
        print(f"profile={row['split_profile']} candidate_count={int(row['candidate_count'])}")

    for _, row in probe_summary_df.iterrows():
        print(
            "candidate split_profile={0} split_index={1} financial_metric_hit_count={2} financial_hit_metrics={3}".format(
                row.get("split_profile", ""),
                row.get("split_index", ""),
                row.get("financial_metric_hit_count", 0),
                row.get("financial_hit_metrics", ""),
            )
        )

    best = split_summary_df.sort_values(
        by=["financial_metric_hit_count", "financial_detail_count", "quality_score"],
        ascending=[False, False, False],
    ).head(1)
    if not best.empty:
        b = best.iloc[0]
        print(
            "best_candidate split_profile={0} split_index={1} financial_metric_hit_count={2} financial_hit_metrics={3} preview={4}".format(
                b.get("split_profile", ""),
                b.get("split_index", ""),
                b.get("financial_metric_hit_count", 0),
                b.get("financial_hit_metrics", ""),
                b.get("preview", ""),
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe split strategies for glued financial tables.")
    parser.add_argument("--asset-package", default=str(DEFAULT_ASSET_PACKAGE), help="Target asset package path.")
    args = parser.parse_args()

    final_path, split_summary_df, probe_summary_df = run_probe(Path(args.asset_package))
    _print_summary(final_path, split_summary_df, probe_summary_df)


if __name__ == "__main__":
    main()
