import argparse
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pdfplumber


DEFAULT_INPUT_DIR = r"D:\_datefac\input"
DEFAULT_OUTPUT_DIR = r"D:\_datefac\output"
DEFAULT_REPORT_PATH = r"D:\_datefac\output\15_extraction_coverage_report.xlsx"

FINANCIAL_KEYWORDS = [
    "财务报表",
    "主要财务指标",
    "利润表",
    "资产负债表",
    "现金流量表",
    "现金流量",
    "财务比率",
    "营业收入",
    "归母净利润",
    "归属母公司",
    "每股收益",
    "ROE",
    "PE",
    "PB",
    "EBITDA",
]


def _safe_report_path(report_path: str) -> str:
    final = report_path
    if os.path.exists(report_path):
        try:
            with open(report_path, "a"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%H%M%S")
            final = report_path.replace(".xlsx", f"_副本_{ts}.xlsx")
    return final


def _safe_preview(df: pd.DataFrame, max_rows: int = 2, max_cols: int = 5, max_chars: int = 240) -> str:
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


def _to_int_page(value) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    m = re.search(r"\d+", s)
    if not m:
        return None
    return int(m.group(0))


def _latest_file(pkg: Path, prefix: str) -> Optional[Path]:
    cands = [x for x in pkg.iterdir() if x.is_file() and x.name.startswith(prefix) and x.suffix.lower() == ".xlsx"]
    if not cands:
        return None
    return sorted(cands, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def _find_asset_package(output_dir: Path, pdf_stem: str) -> Optional[Path]:
    for n in os.listdir(output_dir):
        if n.startswith(pdf_stem + "_") and n.endswith("_资产包"):
            p = output_dir / n
            if p.is_dir():
                return p
    return None


def _load_02a_index(file_02a: Optional[Path]) -> pd.DataFrame:
    if file_02a is None or not file_02a.exists():
        return pd.DataFrame()
    try:
        xls = pd.ExcelFile(str(file_02a))
        sheet = "00_表格索引" if "00_表格索引" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(str(file_02a), sheet_name=sheet)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _load_probe_summary(asset_pkg: Path, source_pdf: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    if asset_pkg is None or not asset_pkg.exists():
        return rows
    files = [x for x in asset_pkg.iterdir() if x.is_file() and x.name.startswith("10_extractor_compare_report") and x.suffix.lower() == ".xlsx"]
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return rows
    for f in files:
        try:
            xls = pd.ExcelFile(str(f))
            if "summary" not in xls.sheet_names:
                continue
            df = pd.read_excel(str(f), sheet_name="summary")
            for _, r in df.iterrows():
                rows.append(
                    {
                        "source_pdf": source_pdf,
                        "backend": r.get("backend", ""),
                        "backend_status": r.get("backend_status", ""),
                        "table_count": r.get("table_count", ""),
                        "avg_quality_score": r.get("avg_quality_score", ""),
                        "good_table_count": r.get("good_table_count", ""),
                        "warning_count": r.get("warning_count", ""),
                        "error_message": r.get("error_message", ""),
                    }
                )
            break
        except Exception:
            continue
    return rows


def _keywords_in_text(text: str) -> Tuple[int, str]:
    if not text:
        return 0, ""
    t = text.upper()
    hits = []
    for kw in FINANCIAL_KEYWORDS:
        if kw.upper() in t:
            hits.append(kw)
    return len(hits), "|".join(hits)


def build_report(input_dir: str, output_dir: str, report_path: str) -> Tuple[str, Dict[str, object]]:
    input_p = Path(input_dir)
    output_p = Path(output_dir)
    pdf_files = sorted([x for x in input_p.iterdir() if x.is_file() and x.suffix.lower() == ".pdf"], key=lambda p: p.name)

    page_rows: List[Dict[str, object]] = []
    summary_rows: List[Dict[str, object]] = []
    raw_table_rows: List[Dict[str, object]] = []
    probe_rows: List[Dict[str, object]] = []

    for pdf in pdf_files:
        source_pdf = str(pdf)
        pdf_stem = pdf.stem
        asset_pkg = _find_asset_package(output_p, pdf_stem)
        file_02a = _latest_file(asset_pkg, "02A_") if asset_pkg else None
        idx_df = _load_02a_index(file_02a)

        # raw table by page map
        page_map: Dict[int, Dict[str, int]] = {}
        total_raw = 0
        total_good = 0
        total_ok = 0
        total_bad = 0
        if not idx_df.empty:
            for _, r in idx_df.iterrows():
                page = _to_int_page(r.get("page", None))
                if page is None:
                    continue
                q = str(r.get("quality_level", "")).strip().upper()
                info = page_map.setdefault(page, {"raw": 0, "good": 0, "ok": 0, "bad": 0})
                info["raw"] += 1
                total_raw += 1
                if q == "GOOD":
                    info["good"] += 1
                    total_good += 1
                elif q == "OK":
                    info["ok"] += 1
                    total_ok += 1
                elif q == "BAD":
                    info["bad"] += 1
                    total_bad += 1

                raw_table_rows.append(
                    {
                        "source_pdf": source_pdf,
                        "asset_package": asset_pkg.name if asset_pkg else "",
                        "backend": r.get("backend", ""),
                        "page": r.get("page", ""),
                        "table_index": r.get("table_index", ""),
                        "row_count": r.get("row_count", ""),
                        "col_count": r.get("col_count", ""),
                        "quality_score": r.get("quality_score", ""),
                        "quality_level": r.get("quality_level", ""),
                        "quality_flags": r.get("quality_flags", ""),
                        "preview": r.get("preview", ""),
                    }
                )

        # probe reference
        if asset_pkg:
            probe_rows.extend(_load_probe_summary(asset_pkg, source_pdf))

        page_count = 0
        keyword_pages = 0
        suspected_pages = 0
        pdf_error = ""
        try:
            with pdfplumber.open(str(pdf)) as doc:
                page_count = len(doc.pages)
                for i, page in enumerate(doc.pages, start=1):
                    try:
                        txt = page.extract_text() or ""
                    except Exception:
                        txt = ""
                    txt_len = len(txt)
                    hit_count, hit_keys = _keywords_in_text(txt)
                    if hit_count >= 1:
                        keyword_pages += 1
                    pstats = page_map.get(i, {"raw": 0, "good": 0, "ok": 0, "bad": 0})
                    raw_cnt = pstats["raw"]
                    good_cnt = pstats["good"]
                    ok_cnt = pstats["ok"]
                    bad_cnt = pstats["bad"]

                    missed = False
                    reason = ""
                    if hit_count >= 2 and raw_cnt == 0:
                        missed = True
                        reason = "keyword_hits>=2_but_no_raw_table"
                    elif hit_count >= 3 and raw_cnt > 0 and bad_cnt == raw_cnt:
                        missed = True
                        reason = "keyword_hits>=3_and_all_raw_tables_bad"
                    if missed:
                        suspected_pages += 1

                    page_rows.append(
                        {
                            "source_pdf": source_pdf,
                            "pdf_stem": pdf_stem,
                            "page_number": i,
                            "page_text_length": txt_len,
                            "financial_keyword_hits": hit_count,
                            "financial_keywords": hit_keys,
                            "raw_table_count_on_page": raw_cnt,
                            "raw_good_count_on_page": good_cnt,
                            "raw_ok_count_on_page": ok_cnt,
                            "raw_bad_count_on_page": bad_cnt,
                            "suspected_missed_financial_table": bool(missed),
                            "suspected_reason": reason,
                        }
                    )
        except Exception as exc:
            pdf_error = f"read_pdf_error: {exc}"

        # summary status
        if suspected_pages > 0:
            status = "partial_or_bad"
        elif total_raw < 3:
            status = "partial"
        elif total_raw > 0 and total_bad == total_raw:
            status = "bad"
        else:
            status = "ok"

        if suspected_pages > 0:
            recommendation = "建议检查 pdfplumber 漏表，尝试 marker 缓存或其他后端。"
        elif total_raw > 0 and total_bad == total_raw:
            recommendation = "建议优先改抽取后端/后端仲裁。"
        elif total_raw < 3:
            recommendation = "建议检查抽取覆盖率，不要优先修 05。"
        else:
            recommendation = "当前抽取覆盖基本可接受。"

        summary_rows.append(
            {
                "source_pdf": source_pdf,
                "asset_package": asset_pkg.name if asset_pkg else "",
                "page_count": page_count,
                "total_financial_keyword_pages": keyword_pages,
                "raw_table_count": total_raw,
                "raw_good_count": total_good,
                "raw_ok_count": total_ok,
                "raw_bad_count": total_bad,
                "suspected_missed_page_count": suspected_pages,
                "extraction_coverage_status": status,
                "recommendation": recommendation,
                "error": pdf_error,
            }
        )

    page_df = pd.DataFrame(page_rows)
    summary_df = pd.DataFrame(summary_rows)
    raw_table_df = pd.DataFrame(raw_table_rows)
    probe_df = pd.DataFrame(probe_rows)

    final_path = _safe_report_path(report_path)
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        page_df.to_excel(writer, sheet_name="pdf_page_coverage", index=False)
        summary_df.to_excel(writer, sheet_name="asset_summary", index=False)
        raw_table_df.to_excel(writer, sheet_name="raw_table_by_page", index=False)
        probe_df.to_excel(writer, sheet_name="backend_probe_reference", index=False)

    return final_path, {"summary_rows": len(summary_df), "page_rows": len(page_df)}


def main():
    parser = argparse.ArgumentParser(description="Diagnose extraction coverage from PDF pages and existing assets.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR, help="PDF input directory.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory containing asset packages.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH, help="Output report path.")
    args = parser.parse_args()

    final_path, counters = build_report(args.input_dir, args.output_dir, args.report_path)
    print(f"report_path={final_path}")
    print(f"summary_rows={counters['summary_rows']}")
    print(f"page_rows={counters['page_rows']}")


if __name__ == "__main__":
    main()
