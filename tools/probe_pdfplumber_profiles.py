import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import pdfplumber

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extractor_quality import score_table_block
from table_block import dataframe_to_table_block


DEFAULT_TARGETS: List[Tuple[str, int]] = [
    (r"D:\_datefac\input\H3_AP202605091822098939_1.pdf", 2),
    (r"D:\_datefac\input\H3_AP202605121822218343_1.pdf", 10),
    (r"D:\_datefac\input\H3_AP202605121822223662_1.pdf", 3),
]

PROFILE_SETTINGS: Dict[str, Dict[str, Any]] = {
    "default": {},
    "text_text": {
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "min_words_vertical": 1,
        "min_words_horizontal": 1,
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "intersection_tolerance": 5,
        "text_tolerance": 3,
    },
    "text_lines": {
        "vertical_strategy": "text",
        "horizontal_strategy": "lines",
        "min_words_vertical": 1,
    },
    "lines_text": {
        "vertical_strategy": "lines",
        "horizontal_strategy": "text",
        "min_words_horizontal": 1,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe multiple pdfplumber extraction profiles on key pages.")
    parser.add_argument("--pdf", action="append", help="PDF path (can pass multiple times)")
    parser.add_argument("--pages", help="Page numbers, e.g. 2 or 2,3,10")
    return parser.parse_args()


def parse_pages_arg(pages_arg: str) -> List[int]:
    if not pages_arg:
        return []
    pages: List[int] = []
    for part in pages_arg.split(","):
        text = part.strip()
        if not text:
            continue
        pages.append(int(text))
    return pages


def resolve_targets(args: argparse.Namespace) -> List[Tuple[Path, int]]:
    if not args.pdf:
        return [(Path(pdf).resolve(), page) for pdf, page in DEFAULT_TARGETS]

    pdfs = [Path(p).expanduser().resolve() for p in args.pdf]
    pages = parse_pages_arg(args.pages or "")

    if len(pdfs) == 1:
        if not pages:
            pages = [1]
        return [(pdfs[0], p) for p in pages]

    if pages:
        return [(pdf, p) for pdf in pdfs for p in pages]

    return [(pdf, 1) for pdf in pdfs]


def fallback_path_if_locked(path: Path) -> Path:
    if not path.exists():
        return path
    try:
        with open(path, "a", encoding="utf-8"):
            pass
        return path
    except PermissionError:
        return path.with_name(f"{path.stem}_copy{path.suffix}")


def safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", str(name or "").strip()) or "sheet"
    cleaned = cleaned[:31]
    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def build_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 6, max_len: int = 320) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    rows: List[str] = []
    for _, row in sample.iterrows():
        rows.append(" | ".join(v.strip() for v in row.tolist()))
    text = " || ".join(rows)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def table_to_df(table: Any) -> pd.DataFrame:
    if not table or not isinstance(table, list):
        return pd.DataFrame()

    max_cols = 0
    for row in table:
        if isinstance(row, list):
            max_cols = max(max_cols, len(row))
    if max_cols == 0:
        return pd.DataFrame()

    rows: List[List[Any]] = []
    for row in table:
        if not isinstance(row, list):
            row = []
        normalized = list(row[:max_cols])
        if len(normalized) < max_cols:
            normalized.extend([""] * (max_cols - len(normalized)))
        rows.append(normalized)
    return pd.DataFrame(rows)


def extract_tables_with_profile(page: pdfplumber.page.Page, profile_name: str) -> List[Any]:
    if profile_name == "default":
        return page.extract_tables() or []
    return page.extract_tables(table_settings=PROFILE_SETTINGS[profile_name]) or []


def build_group_recommendations(group_rows: List[Dict[str, Any]]) -> Dict[str, str]:
    per_profile = {row["profile_name"]: row for row in group_rows}
    default_row = per_profile.get("default")
    text_text_row = per_profile.get("text_text")

    for row in group_rows:
        row["good_ok_count"] = int(row["good_count"] + row["ok_count"])

    all_tables = sum(int(r["table_count"]) for r in group_rows)
    all_bad_or_empty = all(int(r["good_ok_count"]) == 0 for r in group_rows)
    if all_tables == 0 or all_bad_or_empty:
        return {row["profile_name"]: "needs_new_backend_or_manual_review" for row in group_rows}

    if default_row and text_text_row:
        if int(default_row["table_count"]) == 0 and int(text_text_row["good_ok_count"]) > 0:
            recs = {}
            for row in group_rows:
                recs[row["profile_name"]] = "text_text_fallback_candidate" if row["profile_name"] == "text_text" else ""
            return recs

    max_good_ok = max(int(r["good_ok_count"]) for r in group_rows)
    winners = [
        r for r in group_rows
        if int(r["good_ok_count"]) == max_good_ok and max_good_ok > 0
    ]
    if len(winners) > 1:
        best_avg = max(float(r["avg_quality_score"]) for r in winners)
        winners = [r for r in winners if float(r["avg_quality_score"]) == best_avg]

    winner_profiles = {w["profile_name"] for w in winners}
    recs = {}
    for row in group_rows:
        recs[row["profile_name"]] = "candidate" if row["profile_name"] in winner_profiles else ""
    return recs


def main() -> int:
    args = parse_args()
    targets = resolve_targets(args)
    report_path = Path(r"D:\_datefac\output\16_pdfplumber_profile_probe.xlsx")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path = fallback_path_if_locked(report_path)

    summary_rows: List[Dict[str, Any]] = []
    detail_rows: List[Dict[str, Any]] = []
    raw_sheet_payloads: List[Tuple[str, pd.DataFrame]] = []

    for pdf_path, page_number in targets:
        source_pdf = str(pdf_path)
        if not pdf_path.exists():
            for profile_name in PROFILE_SETTINGS.keys():
                summary_rows.append(
                    {
                        "source_pdf": source_pdf,
                        "page_number": page_number,
                        "profile_name": profile_name,
                        "table_count": 0,
                        "total_rows": 0,
                        "total_cols_max": 0,
                        "total_non_empty_cells": 0,
                        "avg_quality_score": 0.0,
                        "good_count": 0,
                        "ok_count": 0,
                        "bad_count": 0,
                        "recommendation": "pdf_not_found",
                    }
                )
            continue

        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    for profile_name in PROFILE_SETTINGS.keys():
                        summary_rows.append(
                            {
                                "source_pdf": source_pdf,
                                "page_number": page_number,
                                "profile_name": profile_name,
                                "table_count": 0,
                                "total_rows": 0,
                                "total_cols_max": 0,
                                "total_non_empty_cells": 0,
                                "avg_quality_score": 0.0,
                                "good_count": 0,
                                "ok_count": 0,
                                "bad_count": 0,
                                "recommendation": "invalid_page_number",
                            }
                        )
                    continue

                page = pdf.pages[page_number - 1]
                group_rows: List[Dict[str, Any]] = []
                for profile_name in PROFILE_SETTINGS.keys():
                    tables = extract_tables_with_profile(page, profile_name)
                    profile_scores: List[float] = []
                    good_count = 0
                    ok_count = 0
                    bad_count = 0
                    total_rows = 0
                    total_non_empty_cells = 0
                    total_cols_max = 0

                    for table_index, table in enumerate(tables):
                        df = table_to_df(table)
                        block = dataframe_to_table_block(
                            df=df,
                            backend=f"pdfplumber_{profile_name}",
                            page=page_number,
                            table_index=table_index,
                            source_meta={
                                "source_pdf": source_pdf,
                                "profile_name": profile_name,
                            },
                        )
                        score = score_table_block(block)

                        profile_scores.append(float(score["quality_score"]))
                        total_rows += int(block.row_count or 0)
                        total_non_empty_cells += int(block.non_empty_cell_count or 0)
                        total_cols_max = max(total_cols_max, int(block.col_count or 0))

                        if score["quality_level"] == "GOOD":
                            good_count += 1
                        elif score["quality_level"] == "OK":
                            ok_count += 1
                        else:
                            bad_count += 1

                        detail_rows.append(
                            {
                                "source_pdf": source_pdf,
                                "page_number": page_number,
                                "profile_name": profile_name,
                                "table_index": table_index,
                                "row_count": int(block.row_count or 0),
                                "col_count": int(block.col_count or 0),
                                "non_empty_cell_count": int(block.non_empty_cell_count or 0),
                                "empty_cell_ratio": float(block.empty_cell_ratio or 0.0),
                                "quality_score": float(score["quality_score"]),
                                "quality_level": score["quality_level"],
                                "quality_flags": score["quality_flags"],
                                "preview": build_preview(df),
                            }
                        )

                        raw_sheet_payloads.append(
                            (
                                f"raw_{pdf_path.stem}_p{page_number}_{profile_name}_t{table_index}",
                                df,
                            )
                        )

                    avg_quality = round(sum(profile_scores) / len(profile_scores), 4) if profile_scores else 0.0
                    group_rows.append(
                        {
                            "source_pdf": source_pdf,
                            "page_number": page_number,
                            "profile_name": profile_name,
                            "table_count": int(len(tables)),
                            "total_rows": int(total_rows),
                            "total_cols_max": int(total_cols_max),
                            "total_non_empty_cells": int(total_non_empty_cells),
                            "avg_quality_score": avg_quality,
                            "good_count": int(good_count),
                            "ok_count": int(ok_count),
                            "bad_count": int(bad_count),
                            "recommendation": "",
                        }
                    )

                recs = build_group_recommendations(group_rows)
                for row in group_rows:
                    row["recommendation"] = recs.get(row["profile_name"], "")
                    summary_rows.append(row)

        except Exception as exc:
            msg = f"page_probe_failed: {exc}"
            for profile_name in PROFILE_SETTINGS.keys():
                summary_rows.append(
                    {
                        "source_pdf": source_pdf,
                        "page_number": page_number,
                        "profile_name": profile_name,
                        "table_count": 0,
                        "total_rows": 0,
                        "total_cols_max": 0,
                        "total_non_empty_cells": 0,
                        "avg_quality_score": 0.0,
                        "good_count": 0,
                        "ok_count": 0,
                        "bad_count": 0,
                        "recommendation": msg,
                    }
                )

    summary_df = pd.DataFrame(summary_rows)
    details_df = pd.DataFrame(detail_rows)

    used_sheet_names: set = set()
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name=safe_sheet_name("summary", used_sheet_names))
        details_df.to_excel(writer, index=False, sheet_name=safe_sheet_name("table_details", used_sheet_names))
        if raw_sheet_payloads:
            for raw_sheet_name, raw_df in raw_sheet_payloads:
                raw_df.to_excel(
                    writer,
                    index=False,
                    header=False,
                    sheet_name=safe_sheet_name(raw_sheet_name, used_sheet_names),
                )
        else:
            pd.DataFrame([{"info": "no tables extracted"}]).to_excel(
                writer, index=False, sheet_name=safe_sheet_name("raw_tables", used_sheet_names)
            )

    print(f"report_path={report_path}")
    if not summary_df.empty:
        print("summary_rows=" + str(len(summary_df)))
        print(summary_df.to_string(index=False))
    else:
        print("summary_rows=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
