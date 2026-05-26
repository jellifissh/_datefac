import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
MARKER1_DIR = BASE_DIR / "output" / "eval_marker1_no_llm_parser_benchmark"
OUT_DIR = BASE_DIR / "output" / "eval_marker1a_json_to_markdown_readable_export"
OUT_MD_DIR = OUT_DIR / "readable_markdown"

IN_SUMMARY = MARKER1_DIR / "304_eval_marker1_no_llm_benchmark_summary.json"
IN_PER_PDF = MARKER1_DIR / "304_eval_marker1_per_pdf_benchmark.xlsx"
IN_TABLE_INV = MARKER1_DIR / "304_eval_marker1_marker_table_inventory.xlsx"
IN_MARKER_OUTPUTS = MARKER1_DIR / "marker_outputs"

OUT_SUMMARY = OUT_DIR / "305_eval_marker1a_summary.json"
OUT_REPORT = OUT_DIR / "305_eval_marker1a_report.md"
OUT_STATUS = OUT_DIR / "305_eval_marker1a_per_pdf_export_status.xlsx"
OUT_TABLE_INDEX = OUT_DIR / "305_eval_marker1a_table_index.xlsx"
OUT_NO_APPLY = OUT_DIR / "305_eval_marker1a_no_apply_proof.json"

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
    used = set()
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


def _html_to_preview(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", _norm(html))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:400]


def _extract_shape(html: str) -> Tuple[int, int]:
    h = _norm(html)
    if not h:
        return 0, 0
    row_count = len(re.findall(r"<tr\b", h, flags=re.IGNORECASE))
    max_cols = 0
    for row_html in re.findall(r"<tr\b.*?</tr>", h, flags=re.IGNORECASE | re.DOTALL):
        c = len(re.findall(r"<t[dh]\b", row_html, flags=re.IGNORECASE))
        max_cols = max(max_cols, c)
    return row_count, max_cols


def _extract_page_num(node_id: str, fallback_page: Optional[int]) -> int:
    m = PAGE_ID_RE.search(node_id)
    if m:
        return int(m.group(1)) + 1
    return int(fallback_page or 0)


def _walk_for_tables(node: Dict[str, Any], page_ctx: Optional[int], out_rows: List[Dict[str, Any]], base64_counter: Dict[str, int]) -> None:
    node_id = _norm(node.get("id"))
    page_num = _extract_page_num(node_id, page_ctx)
    block_type = _norm(node.get("block_type"))

    if block_type in {"Table", "TableGroup"}:
        raw_html = _norm(node.get("html"))
        html, had_b64 = _strip_base64(raw_html)
        if had_b64:
            base64_counter["count"] += 1
        preview = _html_to_preview(html)
        row_count, col_count = _extract_shape(html)
        bbox = node.get("bbox")
        has_bbox = isinstance(bbox, list) and len(bbox) == 4
        bbox_txt = ",".join(str(x) for x in bbox) if has_bbox else ""

        out_rows.append(
            {
                "page_number": page_num,
                "marker_table_id": node_id,
                "block_type": block_type,
                "row_count_est": int(row_count),
                "col_count_est": int(col_count),
                "has_bbox": has_bbox,
                "bbox": bbox_txt,
                "table_text_preview": preview,
                "html_table": html,
            }
        )

    for ch in node.get("children", []) or []:
        if isinstance(ch, dict):
            _walk_for_tables(ch, page_num, out_rows, base64_counter)


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


def _render_markdown(
    pdf_name: str,
    table_rows: List[Dict[str, Any]],
    page_stats: List[Dict[str, Any]],
    toc_titles: List[str],
) -> str:
    lines: List[str] = []
    lines.append(f"# Marker Readable Export: {pdf_name}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- table_like_block_count: {len(table_rows)}")
    lines.append(f"- page_stats_count: {len(page_stats)}")
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

    lines.append("## Table-Like Blocks")
    if not table_rows:
        lines.append("_No table-like blocks found._")
        lines.append("")
        return "\n".join(lines)

    table_rows_sorted = sorted(table_rows, key=lambda r: (int(r.get("page_number", 0)), _norm(r.get("marker_table_id"))))
    for i, r in enumerate(table_rows_sorted, start=1):
        lines.append(f"### {i}. {_norm(r.get('marker_table_id'))}")
        lines.append(f"- page_number: {int(r.get('page_number', 0))}")
        lines.append(f"- block_type: {_norm(r.get('block_type'))}")
        lines.append(f"- row_count_est: {int(r.get('row_count_est', 0))}")
        lines.append(f"- col_count_est: {int(r.get('col_count_est', 0))}")
        lines.append(f"- has_bbox: {bool(r.get('has_bbox', False))}")
        lines.append(f"- bbox: {_norm(r.get('bbox'))}")
        lines.append("")
        lines.append("Preview:")
        lines.append(f"> {_norm(r.get('table_text_preview'))}")
        lines.append("")
        html_block = _norm(r.get("html_table"))
        if html_block:
            # Keep readable; avoid gigantic sections.
            trimmed = html_block[:6000]
            if len(html_block) > len(trimmed):
                trimmed += "\n<!-- trimmed_for_readability -->"
            lines.append("```html")
            lines.append(trimmed)
            lines.append("```")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_SUMMARY, IN_PER_PDF, IN_TABLE_INV, IN_MARKER_OUTPUTS]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-MARKER-1A",
                "mode": "marker_json_to_markdown_readable_export",
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

    status_rows: List[Dict[str, Any]] = []
    table_index_rows: List[Dict[str, Any]] = []
    generated_md_files: List[str] = []
    base64_excluded_any = False
    readable_markdown_generated_count = 0

    for pdf_name in pdf_list:
        stem = Path(pdf_name).stem
        json_path = _find_json(stem)
        meta_path = _find_meta(stem)
        out_md = OUT_MD_DIR / f"{stem}_readable.md"

        page_stats: List[Dict[str, Any]] = []
        toc_titles: List[str] = []
        table_rows: List[Dict[str, Any]] = []
        err = ""
        base64_counter = {"count": 0}

        try:
            if not json_path or not json_path.exists():
                raise FileNotFoundError(f"missing_marker_json_for_{pdf_name}")
            doc = json.loads(json_path.read_text(encoding="utf-8"))
            _walk_for_tables(doc, None, table_rows, base64_counter)

            if meta_path and meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                page_stats = meta.get("page_stats", []) or []
                toc_titles = [str(x.get("title", "")) for x in (meta.get("table_of_contents", []) or [])]

            md_text = _render_markdown(pdf_name, table_rows, page_stats, toc_titles)
            out_md.write_text(md_text, encoding="utf-8")
            generated_md_files.append(str(out_md))
            readable_markdown_generated_count += 1
            if base64_counter["count"] > 0:
                base64_excluded_any = True

            for r in table_rows:
                table_index_rows.append(
                    {
                        "pdf_file_name": pdf_name,
                        "page_number": int(r.get("page_number", 0)),
                        "marker_table_id": _norm(r.get("marker_table_id")),
                        "block_type": _norm(r.get("block_type")),
                        "row_count_est": int(r.get("row_count_est", 0)),
                        "col_count_est": int(r.get("col_count_est", 0)),
                        "has_bbox": bool(r.get("has_bbox", False)),
                        "table_text_preview": _norm(r.get("table_text_preview")),
                        "md_path": str(out_md),
                    }
                )

            status_rows.append(
                {
                    "pdf_file_name": pdf_name,
                    "json_path": str(json_path),
                    "meta_path": str(meta_path) if meta_path else "",
                    "md_path": str(out_md),
                    "export_status": "SUCCESS",
                    "table_like_block_count": len(table_rows),
                    "base64_excluded_count": int(base64_counter["count"]),
                    "error_message": "",
                }
            )
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            status_rows.append(
                {
                    "pdf_file_name": pdf_name,
                    "json_path": str(json_path) if json_path else "",
                    "meta_path": str(meta_path) if meta_path else "",
                    "md_path": str(out_md),
                    "export_status": "FAILED",
                    "table_like_block_count": 0,
                    "base64_excluded_count": 0,
                    "error_message": err,
                }
            )

    status_df = pd.DataFrame(status_rows).fillna("")
    table_index_df = pd.DataFrame(table_index_rows).fillna("")
    _write_excel(OUT_STATUS, {"per_pdf_export_status": status_df})
    _write_excel(OUT_TABLE_INDEX, {"table_index": table_index_df})
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

    total_base64_excluded = int(status_df["base64_excluded_count"].sum()) if not status_df.empty else 0

    summary = {
        "stage": "EVAL-MARKER-1A",
        "mode": "marker_json_to_markdown_readable_export",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_marker1_summary_loaded": bool(_norm(marker1_summary.get("stage")) == "EVAL-MARKER-1"),
        "input_pdf_count": len(pdf_list),
        "readable_markdown_generated_count": readable_markdown_generated_count,
        "table_index_generated": True,
        "base64_images_excluded": bool(base64_excluded_any or total_base64_excluded > 0),
        "base64_excluded_total_count": total_base64_excluded,
        "generated_md_files": generated_md_files,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "sample_pdf_md_path": str(OUT_MD_DIR / f"{Path('0b4b955b8219ffd0bc5a277fab5b8b6c').stem}_readable.md"),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# EVAL-MARKER-1A JSON to Markdown Readable Export",
        "",
        f"- input_pdf_count: {len(pdf_list)}",
        f"- readable_markdown_generated_count: {readable_markdown_generated_count}",
        f"- base64_images_excluded: {summary['base64_images_excluded']}",
        f"- check_delivery_state_overall_status: {delivery_status}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"eval_marker1a_summary_json: {OUT_SUMMARY}")
    print(f"eval_marker1a_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
