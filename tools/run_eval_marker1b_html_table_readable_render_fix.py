from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None


BASE_DIR = Path(r"D:\_datefac")
MARKER1_DIR = BASE_DIR / "output" / "eval_marker1_no_llm_parser_benchmark"
OUT_DIR = BASE_DIR / "output" / "eval_marker1b_html_table_readable_render_fix"
OUT_MD_DIR = OUT_DIR / "readable_markdown_v2"
OUT_XLSX_DIR = OUT_DIR / "readable_excel"

IN_SUMMARY = MARKER1_DIR / "304_eval_marker1_no_llm_benchmark_summary.json"
IN_PER_PDF = MARKER1_DIR / "304_eval_marker1_per_pdf_benchmark.xlsx"
IN_TABLE_INV = MARKER1_DIR / "304_eval_marker1_marker_table_inventory.xlsx"
IN_MARKER_OUTPUTS = MARKER1_DIR / "marker_outputs"

OUT_SUMMARY = OUT_DIR / "305b_summary.json"
OUT_REPORT = OUT_DIR / "305b_report.md"
OUT_TABLE_INDEX = OUT_DIR / "305b_table_render_index.xlsx"
OUT_NO_APPLY = OUT_DIR / "305b_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

BASE64_RE = re.compile(r"data:image/[^;]+;base64,[A-Za-z0-9+/=\n\r]+", flags=re.IGNORECASE)
PAGE_ID_RE = re.compile(r"/page/(\d+)/")


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
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
    used: set = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _strip_base64(s: str) -> Tuple[str, bool]:
    txt = _norm(s)
    hit = bool(BASE64_RE.search(txt))
    if hit:
        txt = BASE64_RE.sub("[[base64_image_excluded]]", txt)
    return txt, hit


def _extract_page_num(node_id: str, fallback_page: Optional[int]) -> int:
    m = PAGE_ID_RE.search(node_id)
    if m:
        return int(m.group(1)) + 1
    return int(fallback_page or 0)


def _find_json(stem: str) -> Optional[Path]:
    p = IN_MARKER_OUTPUTS / stem / f"{stem}.json"
    if p.exists():
        return p
    cands = [x for x in (IN_MARKER_OUTPUTS / stem).glob("*.json") if not x.name.endswith("_meta.json")] if (IN_MARKER_OUTPUTS / stem).exists() else []
    return sorted(cands)[0] if cands else None


def _find_meta(stem: str) -> Optional[Path]:
    p = IN_MARKER_OUTPUTS / stem / f"{stem}_meta.json"
    if p.exists():
        return p
    cands = list((IN_MARKER_OUTPUTS / stem).glob("*_meta.json")) if (IN_MARKER_OUTPUTS / stem).exists() else []
    return sorted(cands)[0] if cands else None


def _html_to_text_preview(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", _norm(html))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:400]


def _extract_tables_from_html(html: str) -> Tuple[List[pd.DataFrame], str]:
    html = _norm(html)
    if not html:
        return [], "empty_html"

    # Preferred parser path: pandas.read_html
    try:
        tables = pd.read_html(StringIO(html))
        out = []
        for t in tables:
            t2 = t.fillna("")
            t2.columns = [f"col_{i}" if _norm(c) == "" else _norm(c) for i, c in enumerate(t2.columns)]
            out.append(t2)
        if out:
            return out, "pandas_read_html"
    except Exception:
        pass

    # Fallback path: BeautifulSoup (if available), manual row/cell extraction.
    if BeautifulSoup is not None:
        try:
            soup = BeautifulSoup(html, "html.parser")
            out_tables: List[pd.DataFrame] = []
            for table in soup.find_all("table"):
                rows: List[List[str]] = []
                for tr in table.find_all("tr"):
                    row = []
                    for cell in tr.find_all(["td", "th"]):
                        row.append(_norm(cell.get_text(" ", strip=True)))
                    if row:
                        rows.append(row)
                if rows:
                    max_cols = max(len(r) for r in rows)
                    padded = [r + [""] * (max_cols - len(r)) for r in rows]
                    headers = [f"col_{i}" for i in range(max_cols)]
                    out_tables.append(pd.DataFrame(padded, columns=headers).fillna(""))
            if out_tables:
                return out_tables, "beautifulsoup_fallback"
        except Exception:
            pass

    return [], "parse_failed"


def _walk_for_tables(
    node: Dict[str, Any],
    page_ctx: Optional[int],
    out_rows: List[Dict[str, Any]],
    base64_counter: Dict[str, int],
) -> None:
    node_id = _norm(node.get("id"))
    page_num = _extract_page_num(node_id, page_ctx)
    block_type = _norm(node.get("block_type"))

    if block_type in {"Table", "TableGroup"}:
        raw_html = _norm(node.get("html"))
        html, had_b64 = _strip_base64(raw_html)
        if had_b64:
            base64_counter["count"] += 1

        bbox = node.get("bbox")
        has_bbox = isinstance(bbox, list) and len(bbox) == 4
        bbox_txt = ",".join(str(x) for x in bbox) if has_bbox else ""
        preview = _html_to_text_preview(html)

        out_rows.append(
            {
                "page_number": int(page_num),
                "marker_table_id": node_id,
                "block_type": block_type,
                "has_bbox": has_bbox,
                "bbox": bbox_txt,
                "table_text_preview": preview,
                "html_table": html,
            }
        )

    for ch in node.get("children", []) or []:
        if isinstance(ch, dict):
            _walk_for_tables(ch, page_num, out_rows, base64_counter)


def _render_markdown(pdf_name: str, table_render_rows: List[Dict[str, Any]], toc_titles: List[str], page_stats: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append(f"# Marker HTML Table Render (V2): {pdf_name}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- table_block_count: {len(table_render_rows)}")
    lines.append("")

    if toc_titles:
        lines.append("## TOC / Section Titles")
        for t in toc_titles[:30]:
            if _norm(t):
                lines.append(f"- {_norm(t)}")
        lines.append("")

    if page_stats:
        lines.append("## Page Stats")
        for ps in page_stats:
            p = int(ps.get("page_id", -1)) + 1
            bcs = ps.get("block_counts", []) or []
            bc_txt = ", ".join(f"{x[0]}={x[1]}" for x in bcs[:10] if isinstance(x, list) and len(x) >= 2)
            lines.append(f"- page {p}: {bc_txt}")
        lines.append("")

    lines.append("## Rendered Tables")
    if not table_render_rows:
        lines.append("_No table blocks found._")
        lines.append("")
        return "\n".join(lines)

    for i, r in enumerate(table_render_rows, start=1):
        lines.append(f"### {i}. {_norm(r.get('marker_table_id'))}")
        lines.append(f"- page_number: {int(r.get('page_number', 0))}")
        lines.append(f"- block_type: {_norm(r.get('block_type'))}")
        lines.append(f"- render_status: {_norm(r.get('render_status'))}")
        lines.append(f"- parser_used: {_norm(r.get('parser_used'))}")
        lines.append(f"- has_bbox: {bool(r.get('has_bbox', False))}")
        lines.append(f"- bbox: {_norm(r.get('bbox'))}")
        lines.append(f"- parsed_table_count: {int(r.get('parsed_table_count', 0))}")
        lines.append("")
        lines.append("Preview:")
        lines.append(f"> {_norm(r.get('table_text_preview'))}")
        lines.append("")

        markdown_tables: List[str] = r.get("markdown_tables", []) or []
        if markdown_tables:
            for j, md_tbl in enumerate(markdown_tables, start=1):
                lines.append(f"Table {j}:")
                lines.append("")
                lines.append(md_tbl)
                lines.append("")
        else:
            lines.append("_No readable table parsed from HTML for this block._")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD_DIR.mkdir(parents=True, exist_ok=True)
    OUT_XLSX_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_SUMMARY, IN_PER_PDF, IN_TABLE_INV, IN_MARKER_OUTPUTS]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-MARKER-1B",
                "mode": "html_table_readable_render_fix",
                "blocked": True,
                "blocked_reason": "missing_marker1_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
                "marker_rerun_executed": False,
            },
        )
        return 0

    marker1_summary = json.loads(IN_SUMMARY.read_text(encoding="utf-8"))
    per_pdf_df = pd.read_excel(IN_PER_PDF).fillna("")
    _ = pd.read_excel(IN_TABLE_INV).fillna("")

    pdf_list = marker1_summary.get("source_of_truth_pdf_list_used") or per_pdf_df.get("pdf_file_name", pd.Series([], dtype=str)).tolist()
    pdf_list = [_norm(x) for x in pdf_list if _norm(x)]

    before = _snapshot_guard()

    render_index_rows: List[Dict[str, Any]] = []
    generated_md_files: List[str] = []
    generated_excel_files: List[str] = []
    base64_excluded_total_count = 0
    parsed_markdown_table_total_count = 0
    failed_table_render_count = 0

    for pdf_name in pdf_list:
        stem = Path(pdf_name).stem
        json_path = _find_json(stem)
        meta_path = _find_meta(stem)
        out_md = OUT_MD_DIR / f"{stem}_readable_v2.md"
        out_xlsx = OUT_XLSX_DIR / f"{stem}_tables_v2.xlsx"

        page_stats: List[Dict[str, Any]] = []
        toc_titles: List[str] = []
        table_rows: List[Dict[str, Any]] = []
        base64_counter = {"count": 0}

        try:
            if not json_path or not json_path.exists():
                raise FileNotFoundError(f"missing_marker_json_for_{pdf_name}")

            doc = json.loads(json_path.read_text(encoding="utf-8"))
            _walk_for_tables(doc, None, table_rows, base64_counter)
            base64_excluded_total_count += int(base64_counter["count"])

            if meta_path and meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                page_stats = meta.get("page_stats", []) or []
                toc_titles = [str(x.get("title", "")) for x in (meta.get("table_of_contents", []) or [])]

            sheets: Dict[str, pd.DataFrame] = {}
            table_render_rows: List[Dict[str, Any]] = []

            for t_idx, tr in enumerate(table_rows, start=1):
                html = _norm(tr.get("html_table"))
                parsed_tables, parser_used = _extract_tables_from_html(html)
                parsed_markdown_tables: List[str] = []

                if parsed_tables:
                    for parsed_idx, df in enumerate(parsed_tables, start=1):
                        if df.empty:
                            continue
                        md = df.to_markdown(index=False)
                        parsed_markdown_tables.append(md)
                        sheet_name = f"t{t_idx}_p{int(tr.get('page_number', 0))}_{parsed_idx}"
                        sheets[sheet_name] = df
                    parsed_markdown_table_total_count += len(parsed_markdown_tables)
                    render_status = "SUCCESS"
                else:
                    render_status = "FAILED_PARSE"
                    failed_table_render_count += 1

                row = {
                    **tr,
                    "render_status": render_status,
                    "parser_used": parser_used,
                    "parsed_table_count": len(parsed_markdown_tables),
                    "markdown_tables": parsed_markdown_tables,
                }
                table_render_rows.append(row)

                render_index_rows.append(
                    {
                        "pdf_file_name": pdf_name,
                        "page_number": int(tr.get("page_number", 0)),
                        "marker_table_id": _norm(tr.get("marker_table_id")),
                        "block_type": _norm(tr.get("block_type")),
                        "render_status": render_status,
                        "parser_used": parser_used,
                        "parsed_table_count": len(parsed_markdown_tables),
                        "has_bbox": bool(tr.get("has_bbox", False)),
                        "table_text_preview": _norm(tr.get("table_text_preview")),
                        "md_path": str(out_md),
                        "xlsx_path": str(out_xlsx),
                    }
                )

            if not sheets:
                sheets["meta"] = pd.DataFrame(
                    [{"pdf_file_name": pdf_name, "note": "No parseable HTML tables found"}]
                )
            _write_excel(out_xlsx, sheets)
            generated_excel_files.append(str(out_xlsx))

            md_text = _render_markdown(pdf_name, table_render_rows, toc_titles, page_stats)
            out_md.write_text(md_text, encoding="utf-8")
            generated_md_files.append(str(out_md))

        except Exception as exc:
            render_index_rows.append(
                {
                    "pdf_file_name": pdf_name,
                    "page_number": 0,
                    "marker_table_id": "",
                    "block_type": "",
                    "render_status": "FAILED_PDF",
                    "parser_used": "",
                    "parsed_table_count": 0,
                    "has_bbox": False,
                    "table_text_preview": "",
                    "md_path": str(out_md),
                    "xlsx_path": str(out_xlsx),
                    "error_message": f"{type(exc).__name__}: {exc}",
                }
            )

    render_index_df = pd.DataFrame(render_index_rows).fillna("")
    _write_excel(OUT_TABLE_INDEX, {"table_render_index": render_index_df})

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-MARKER-1B",
        "mode": "html_table_readable_render_fix",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_marker1_summary_loaded": bool(_norm(marker1_summary.get("stage")) == "EVAL-MARKER-1"),
        "input_pdf_count": len(pdf_list),
        "readable_markdown_generated_count": len(generated_md_files),
        "readable_excel_generated_count": len(generated_excel_files),
        "table_render_index_generated": True,
        "base64_images_excluded": bool(base64_excluded_total_count > 0),
        "base64_excluded_total_count": int(base64_excluded_total_count),
        "parsed_markdown_table_total_count": int(parsed_markdown_table_total_count),
        "failed_table_render_count": int(failed_table_render_count),
        "generated_md_files": generated_md_files,
        "generated_excel_files": generated_excel_files,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 305B Marker HTML Table Readable Render Fix",
        "",
        f"- input_pdf_count: {len(pdf_list)}",
        f"- readable_markdown_generated_count: {len(generated_md_files)}",
        f"- readable_excel_generated_count: {len(generated_excel_files)}",
        f"- parsed_markdown_table_total_count: {parsed_markdown_table_total_count}",
        f"- failed_table_render_count: {failed_table_render_count}",
        f"- base64_images_excluded: {summary['base64_images_excluded']}",
        f"- check_delivery_state_overall_status: {delivery_status}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_marker1b_summary_json: {OUT_SUMMARY}")
    print(f"eval_marker1b_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
