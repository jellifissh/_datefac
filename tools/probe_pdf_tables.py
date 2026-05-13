import argparse
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = r"D:\_datefac\output\_probe_tables"
GENERATE_BACKEND_EXCEL = True


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def fallback_path_if_locked(path: Path) -> Path:
    if not path.exists():
        return path
    try:
        with open(path, "a", encoding="utf-8"):
            pass
        return path
    except PermissionError:
        stem = path.stem
        return path.with_name(f"{stem}_{now_stamp()}{path.suffix}")


def safe_sheet_name(raw_name: str, used: Optional[set] = None) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", raw_name).strip() or "sheet"
    cleaned = cleaned[:31]
    if used is None:
        return cleaned

    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def normalize_dataframe(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    if df is None:
        return None
    normalized = df.fillna("").astype(str)
    normalized = normalized.apply(lambda col: col.map(lambda v: re.sub(r"\s+", " ", v).strip()))
    normalized = normalized.loc[(normalized != "").any(axis=1), (normalized != "").any(axis=0)]
    if normalized.empty or normalized.shape[1] == 0:
        return None
    return normalized.reset_index(drop=True)


def build_preview(df: Optional[pd.DataFrame], max_rows: int = 2, max_cols: int = 4, max_len: int = 220) -> str:
    if df is None or df.empty:
        return ""
    snippet = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    text_rows = []
    for _, row in snippet.iterrows():
        text_rows.append(" | ".join(cell.strip() for cell in row.tolist()))
    preview = " || ".join(text_rows)
    preview = re.sub(r"\s+", " ", preview).strip()
    return preview[:max_len] + ("..." if len(preview) > max_len else "")


def parse_pages_arg(raw: str, total_pages: Optional[int] = None) -> List[int]:
    pages_raw = (raw or "all").strip().lower()
    if pages_raw == "all":
        if total_pages is None:
            return []
        return list(range(1, total_pages + 1))

    pages = set()
    for part in pages_raw.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_s, end_s = token.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start > end:
                start, end = end, start
            pages.update(range(start, end + 1))
        else:
            pages.add(int(token))

    parsed = sorted(p for p in pages if p >= 1)
    if total_pages is not None:
        parsed = [p for p in parsed if p <= total_pages]
    return parsed


def pages_to_camelot_expr(pages: Sequence[int], original: str) -> str:
    if (original or "").strip().lower() == "all":
        return "all"
    if not pages:
        return "1"
    return ",".join(str(p) for p in pages)


def unique_columns(columns: Iterable[str]) -> List[str]:
    seen: Dict[str, int] = {}
    result: List[str] = []
    for col in columns:
        raw = str(col).strip() or "unnamed_col"
        if raw not in seen:
            seen[raw] = 0
            result.append(raw)
        else:
            seen[raw] += 1
            result.append(f"{raw}.{seen[raw]}")
    return result


def extract_markdown_table_blocks(markdown_text: str) -> List[str]:
    lines = markdown_text.splitlines()
    blocks: List[str] = []
    current: List[str] = []
    non_table_gap = 0

    for line in lines:
        stripped = line.strip()
        if stripped.count("|") >= 2:
            current.append(stripped)
            non_table_gap = 0
            continue

        if current:
            non_table_gap += 1
            if non_table_gap >= 2:
                blocks.append("\n".join(current))
                current = []
                non_table_gap = 0

    if current:
        blocks.append("\n".join(current))
    return blocks


def parse_markdown_table_to_df(table_block: str) -> Optional[pd.DataFrame]:
    lines = [line for line in table_block.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    filtered = [line for line in lines if not re.match(r"^\s*\|?[\s:\-]+\|[\s\|\-:]*\|?\s*$", line)]
    if len(filtered) < 2:
        return None

    rows: List[List[str]] = []
    for line in filtered:
        segment = line.strip()
        if segment.startswith("|"):
            segment = segment[1:]
        if segment.endswith("|"):
            segment = segment[:-1]
        rows.append([cell.strip() for cell in segment.split("|")])

    width = max((len(r) for r in rows), default=0)
    if width == 0:
        return None

    rows = [r + [""] * (width - len(r)) for r in rows]
    header = unique_columns(rows[0])
    body = rows[1:]
    if not body:
        return None

    df = pd.DataFrame(body, columns=header)
    return normalize_dataframe(df)


@dataclass
class ProbeContext:
    pdf_path: Path
    output_dir: Path
    pages_arg: str
    marker_cache_path: Optional[Path]
    log_lines: List[str]


def append_log(log_lines: List[str], message: str) -> None:
    log_lines.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def report_row(
    backend: str,
    status: str,
    page: object = "",
    table_index: object = "",
    rows: object = "",
    cols: object = "",
    preview: str = "",
    output_file: str = "",
    error: str = "",
) -> Dict[str, object]:
    return {
        "backend": backend,
        "status": status,
        "page": page,
        "table_index": table_index,
        "rows": rows,
        "cols": cols,
        "preview": preview,
        "output_file": output_file,
        "error": error,
    }


def write_excel_sheets(output_path: Path, sheets: List[Tuple[str, pd.DataFrame]]) -> Optional[Path]:
    if not sheets:
        return None
    target = fallback_path_if_locked(output_path)
    used = set()
    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        for raw_name, df in sheets:
            sheet_name = safe_sheet_name(raw_name, used)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return target


def probe_marker_cache(
    ctx: ProbeContext,
) -> Tuple[List[Dict[str, object]], Optional[Path], int, List[Tuple[str, pd.DataFrame]]]:
    backend = "marker_cache"
    rows: List[Dict[str, object]] = []
    sheets: List[Tuple[str, pd.DataFrame]] = []
    table_count = 0

    if not ctx.marker_cache_path or not ctx.marker_cache_path.exists():
        rows.append(report_row(backend, "dependency_missing", error="marker_cache_missing"))
        append_log(ctx.log_lines, f"{backend}: marker cache missing, skipped")
        return rows, None, table_count, []

    try:
        markdown_text = ctx.marker_cache_path.read_text(encoding="utf-8", errors="ignore")
        blocks = extract_markdown_table_blocks(markdown_text)
        append_log(ctx.log_lines, f"{backend}: markdown table blocks={len(blocks)}")

        for idx, block in enumerate(blocks, start=1):
            df = parse_markdown_table_to_df(block)
            if df is None:
                continue
            table_count += 1
            sheets.append((f"pNA_t{idx}", df))
            rows.append(
                report_row(
                    backend=backend,
                    status="ok",
                    page="",
                    table_index=idx,
                    rows=int(df.shape[0]),
                    cols=int(df.shape[1]),
                    preview=build_preview(df),
                )
            )

        output_file = write_excel_sheets(ctx.output_dir / "marker_cache_tables.xlsx", sheets) if GENERATE_BACKEND_EXCEL else None
        output_str = str(output_file) if output_file else ""
        for row in rows:
            row["output_file"] = output_str

        if table_count == 0:
            rows.append(report_row(backend, "ok_no_tables", rows=0, cols=0, output_file=output_str))
        unified_sheets: List[Tuple[str, pd.DataFrame]] = []
        for row, (_, df) in zip([r for r in rows if r.get("status") == "ok"], sheets):
            page = row.get("page") or "NA"
            table_index = row.get("table_index") or "NA"
            unified_sheets.append((f"marker_p{page}_t{table_index}", df))
        return rows, output_file, table_count, unified_sheets
    except Exception as exc:
        rows.append(report_row(backend, "error", error=str(exc)))
        append_log(ctx.log_lines, f"{backend}: failed: {exc}")
        return rows, None, table_count, []


def probe_pdfplumber(
    ctx: ProbeContext,
) -> Tuple[List[Dict[str, object]], Optional[Path], int, List[Tuple[str, pd.DataFrame]]]:
    backend = "pdfplumber"
    rows: List[Dict[str, object]] = []
    sheets: List[Tuple[str, pd.DataFrame]] = []
    table_count = 0

    try:
        import pdfplumber  # type: ignore
    except ImportError:
        rows.append(report_row(backend, "dependency_missing", error="pdfplumber_not_installed"))
        append_log(ctx.log_lines, f"{backend}: dependency missing")
        return rows, None, table_count, []

    try:
        with pdfplumber.open(str(ctx.pdf_path)) as pdf:
            pages = parse_pages_arg(ctx.pages_arg, total_pages=len(pdf.pages))
            if not pages:
                pages = list(range(1, len(pdf.pages) + 1))

            for page_num in pages:
                try:
                    page = pdf.pages[page_num - 1]
                    tables = page.extract_tables() or []
                    for table_idx, table in enumerate(tables, start=1):
                        if not table:
                            continue
                        raw_df = pd.DataFrame(table)
                        df = normalize_dataframe(raw_df)
                        if df is None:
                            continue
                        table_count += 1
                        sheets.append((f"p{page_num}_t{table_idx}", df))
                        rows.append(
                            report_row(
                                backend=backend,
                                status="ok",
                                page=page_num,
                                table_index=table_idx,
                                rows=int(df.shape[0]),
                                cols=int(df.shape[1]),
                                preview=build_preview(df),
                            )
                        )
                except Exception as page_exc:
                    rows.append(report_row(backend, "page_error", page=page_num, error=str(page_exc)))

        output_file = write_excel_sheets(ctx.output_dir / "pdfplumber_tables.xlsx", sheets) if GENERATE_BACKEND_EXCEL else None
        output_str = str(output_file) if output_file else ""
        for row in rows:
            if row["status"] == "ok":
                row["output_file"] = output_str
        if table_count == 0:
            rows.append(report_row(backend, "ok_no_tables", rows=0, cols=0, output_file=output_str))
        unified_sheets: List[Tuple[str, pd.DataFrame]] = []
        for row, (_, df) in zip([r for r in rows if r.get("status") == "ok"], sheets):
            page = row.get("page") or "NA"
            table_index = row.get("table_index") or "NA"
            unified_sheets.append((f"plumber_p{page}_t{table_index}", df))
        return rows, output_file, table_count, unified_sheets
    except Exception as exc:
        rows.append(report_row(backend, "error", error=str(exc)))
        append_log(ctx.log_lines, f"{backend}: failed: {exc}")
        return rows, None, table_count, []


def probe_camelot(
    ctx: ProbeContext,
    flavor: str,
) -> Tuple[List[Dict[str, object]], Optional[Path], int, List[Tuple[str, pd.DataFrame]]]:
    backend = f"camelot_{flavor}"
    rows: List[Dict[str, object]] = []
    sheets: List[Tuple[str, pd.DataFrame]] = []
    table_count = 0

    try:
        import camelot  # type: ignore
    except ImportError:
        rows.append(report_row(backend, "dependency_missing", error="camelot_not_installed"))
        append_log(ctx.log_lines, f"{backend}: dependency missing")
        return rows, None, table_count, []

    try:
        pages = parse_pages_arg(ctx.pages_arg)
        pages_expr = pages_to_camelot_expr(pages, ctx.pages_arg)
        tables = camelot.read_pdf(str(ctx.pdf_path), pages=pages_expr, flavor=flavor)
        for table_idx, table in enumerate(tables, start=1):
            try:
                df = normalize_dataframe(getattr(table, "df", None))
                if df is None:
                    continue
                page_text = str(getattr(table, "page", "")).strip()
                page_value = page_text.split(",")[0] if page_text else ""
                page_num = int(page_value) if page_value.isdigit() else ""
                table_count += 1
                sheets.append((f"p{page_num or 'NA'}_t{table_idx}", df))
                rows.append(
                    report_row(
                        backend=backend,
                        status="ok",
                        page=page_num,
                        table_index=table_idx,
                        rows=int(df.shape[0]),
                        cols=int(df.shape[1]),
                        preview=build_preview(df),
                    )
                )
            except Exception as table_exc:
                rows.append(report_row(backend, "table_error", table_index=table_idx, error=str(table_exc)))

        output_file = write_excel_sheets(ctx.output_dir / f"{backend}_tables.xlsx", sheets) if GENERATE_BACKEND_EXCEL else None
        output_str = str(output_file) if output_file else ""
        for row in rows:
            if row["status"] == "ok":
                row["output_file"] = output_str
        if table_count == 0:
            rows.append(report_row(backend, "ok_no_tables", rows=0, cols=0, output_file=output_str))
        unified_sheets: List[Tuple[str, pd.DataFrame]] = []
        prefix = "camS" if flavor == "stream" else "camL"
        for row, (_, df) in zip([r for r in rows if r.get("status") == "ok"], sheets):
            page = row.get("page") or "NA"
            table_index = row.get("table_index") or "NA"
            unified_sheets.append((f"{prefix}_p{page}_t{table_index}", df))
        return rows, output_file, table_count, unified_sheets
    except Exception as exc:
        # lattice on windows may fail due to ghostscript/cv dependencies; keep non-fatal
        rows.append(report_row(backend, "error", error=str(exc)))
        append_log(ctx.log_lines, f"{backend}: failed: {exc}")
        return rows, None, table_count, []


def probe_pymupdf(
    ctx: ProbeContext,
) -> Tuple[List[Dict[str, object]], Optional[Path], int, List[Tuple[str, pd.DataFrame]]]:
    backend = "pymupdf_probe"
    rows: List[Dict[str, object]] = []
    sheets: List[Tuple[str, pd.DataFrame]] = []
    page_count = 0

    try:
        import fitz  # type: ignore
    except ImportError:
        rows.append(report_row(backend, "dependency_missing", error="pymupdf_not_installed"))
        append_log(ctx.log_lines, f"{backend}: dependency missing")
        return rows, None, page_count, []

    try:
        doc = fitz.open(str(ctx.pdf_path))
        pages = parse_pages_arg(ctx.pages_arg, total_pages=doc.page_count)
        if not pages:
            pages = list(range(1, doc.page_count + 1))

        for page_num in pages:
            try:
                page = doc.load_page(page_num - 1)
                blocks = page.get_text("blocks") or []
                page_count += 1
                block_rows = []
                for idx, block in enumerate(blocks[:300], start=1):
                    text = str(block[4]).strip() if len(block) > 4 else ""
                    text = re.sub(r"\s+", " ", text)
                    block_rows.append(
                        {
                            "page": page_num,
                            "block_index": idx,
                            "x0": block[0],
                            "y0": block[1],
                            "x1": block[2],
                            "y1": block[3],
                            "text_preview": text[:300],
                        }
                    )
                df = pd.DataFrame(block_rows)
                if df.empty:
                    df = pd.DataFrame(
                        [{"page": page_num, "block_index": "", "x0": "", "y0": "", "x1": "", "y1": "", "text_preview": ""}]
                    )
                sheets.append((f"p{page_num}_blocks", df))
                rows.append(
                    report_row(
                        backend=backend,
                        status="ok",
                        page=page_num,
                        table_index="",
                        rows=int(len(block_rows)),
                        cols=int(df.shape[1]),
                        preview=build_preview(df, max_rows=2, max_cols=2),
                    )
                )
            except Exception as page_exc:
                rows.append(report_row(backend, "page_error", page=page_num, error=str(page_exc)))

        doc.close()
        output_file = write_excel_sheets(ctx.output_dir / "pymupdf_page_blocks.xlsx", sheets) if GENERATE_BACKEND_EXCEL else None
        output_str = str(output_file) if output_file else ""
        for row in rows:
            if row["status"] == "ok":
                row["output_file"] = output_str
        combined_blocks = pd.concat([df for _, df in sheets], ignore_index=True) if sheets else pd.DataFrame()
        unified_sheets = [("fitz_blocks", combined_blocks)] if not combined_blocks.empty else []
        return rows, output_file, page_count, unified_sheets
    except Exception as exc:
        rows.append(report_row(backend, "error", error=str(exc)))
        append_log(ctx.log_lines, f"{backend}: failed: {exc}")
        return rows, None, page_count, []


def write_report(output_dir: Path, rows: List[Dict[str, object]]) -> Path:
    report_df = pd.DataFrame(
        rows,
        columns=["backend", "status", "page", "table_index", "rows", "cols", "preview", "output_file", "error"],
    )
    report_path = fallback_path_if_locked(output_dir / "table_probe_report.xlsx")
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        report_df.to_excel(writer, sheet_name="table_probe_report", index=False)
    return report_path


def write_all_tables_workbook(output_dir: Path, report_rows: List[Dict[str, object]], sheets: List[Tuple[str, pd.DataFrame]]) -> Path:
    output_path = fallback_path_if_locked(output_dir / "table_probe_all_tables.xlsx")
    report_df = pd.DataFrame(
        report_rows,
        columns=["backend", "status", "page", "table_index", "rows", "cols", "preview", "output_file", "error"],
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        report_df.to_excel(writer, sheet_name="00_report", index=False)
        used = {"00_report"}
        for raw_name, df in sheets:
            safe_name = safe_sheet_name(raw_name, used)
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return output_path


def write_log(output_dir: Path, lines: List[str]) -> Path:
    log_path = fallback_path_if_locked(output_dir / "probe_log.txt")
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path


def summarize_backend(rows: List[Dict[str, object]]) -> List[str]:
    result: List[str] = []
    by_backend: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        by_backend.setdefault(str(row["backend"]), []).append(row)
    for backend in sorted(by_backend):
        group = by_backend[backend]
        statuses = sorted({str(r["status"]) for r in group})
        ok_tables = sum(1 for r in group if r["status"] == "ok")
        result.append(f"{backend}: ok={ok_tables}, statuses={','.join(statuses)}")
    return result


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="POC: probe multiple PDF table extraction backends and compare output.")
    ap.add_argument("--pdf", required=True, help="Target PDF path")
    ap.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help=f"Output directory, default: {DEFAULT_OUTPUT_DIR}")
    ap.add_argument("--marker-cache", default="", help="Optional existing marker markdown cache file (.txt/.md)")
    ap.add_argument("--pages", default="all", help='Page selector: all | 1 | 1-3 | 2,3,5 (default: all)')
    return ap


def main() -> int:
    args = parser().parse_args()
    pdf_path = Path(args.pdf).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    marker_cache_path = Path(args.marker_cache).expanduser().resolve() if args.marker_cache else None
    ensure_dir(output_dir)

    log_lines: List[str] = []
    append_log(log_lines, f"PDF path: {pdf_path}")
    append_log(log_lines, f"Output dir: {output_dir}")
    append_log(log_lines, f"Pages arg: {args.pages}")
    append_log(log_lines, f"Marker cache: {marker_cache_path if marker_cache_path else '(not provided)'}")

    if not pdf_path.exists():
        append_log(log_lines, "fatal: pdf not found")
        log_file = write_log(output_dir, log_lines)
        print(f"[probe] pdf not found: {pdf_path}")
        print(f"[probe] log: {log_file}")
        return 1

    ctx = ProbeContext(
        pdf_path=pdf_path,
        output_dir=output_dir,
        pages_arg=args.pages,
        marker_cache_path=marker_cache_path,
        log_lines=log_lines,
    )

    runners = [
        ("marker_cache", lambda: probe_marker_cache(ctx)),
        ("pdfplumber", lambda: probe_pdfplumber(ctx)),
        ("camelot_stream", lambda: probe_camelot(ctx, flavor="stream")),
        ("camelot_lattice", lambda: probe_camelot(ctx, flavor="lattice")),
        ("pymupdf_probe", lambda: probe_pymupdf(ctx)),
    ]

    all_rows: List[Dict[str, object]] = []
    all_table_sheets: List[Tuple[str, pd.DataFrame]] = []
    backend_counts: Dict[str, int] = {}
    backend_status: Dict[str, str] = {}

    for name, runner in runners:
        try:
            rows, _output_file, count, unified_sheets = runner()
            all_rows.extend(rows)
            all_table_sheets.extend(unified_sheets)
            backend_counts[name] = count
            statuses = sorted({str(r["status"]) for r in rows}) if rows else ["ok_no_rows"]
            backend_status[name] = ",".join(statuses)
            append_log(log_lines, f"{name}: tables/pages captured={count}, statuses={backend_status[name]}")
        except Exception as exc:
            all_rows.append(report_row(name, "error", error=str(exc)))
            backend_counts[name] = 0
            backend_status[name] = "error"
            append_log(log_lines, f"{name}: unexpected error: {exc}")

    report_path = write_report(output_dir, all_rows)
    all_tables_path = write_all_tables_workbook(output_dir, all_rows, all_table_sheets)
    append_log(log_lines, f"Report file: {report_path}")
    append_log(log_lines, f"All tables workbook: {all_tables_path}")
    append_log(log_lines, "Backend availability and counts:")
    for name in ["marker_cache", "pdfplumber", "camelot_stream", "camelot_lattice", "pymupdf_probe"]:
        append_log(log_lines, f"  - {name}: {backend_status.get(name, 'unknown')} | count={backend_counts.get(name, 0)}")

    failure_rows = [r for r in all_rows if str(r.get("status", "")).endswith("error") or r.get("status") == "dependency_missing"]
    append_log(log_lines, f"Failure summary rows: {len(failure_rows)}")
    for row in failure_rows[:20]:
        append_log(log_lines, f"  * {row['backend']} | {row['status']} | page={row.get('page', '')} | err={row.get('error', '')}")

    log_path = write_log(output_dir, log_lines)
    print(f"[probe] report: {report_path}")
    print(f"[probe] all_tables: {all_tables_path}")
    print(f"[probe] log: {log_path}")
    for line in summarize_backend(all_rows):
        print(f"[probe] {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
