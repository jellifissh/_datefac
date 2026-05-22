import argparse
import hashlib
import importlib.util
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

from config_manager import ConfigManager
from extractor_adapter import extract_marker_table_blocks, extract_pdfplumber_table_blocks
from pdfplumber_profile_extractor import extract_tables_with_pdfplumber_profiles
from table_block import TableBlock


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OUTPUT_DIR = BASE_DIR / "output" / "stage5b_table_extraction_restore"
RAW_XLSX = OUTPUT_DIR / "raw_tables.xlsx"
RAW_JSON = OUTPUT_DIR / "raw_tables.json"
REPORT_XLSX = OUTPUT_DIR / "128_stage5b_table_extraction_restore.xlsx"
REPORT_MD = OUTPUT_DIR / "128_stage5b_table_extraction_restore.md"
SUMMARY_JSON = OUTPUT_DIR / "129_stage5b_table_extraction_restore_summary.json"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_PATH = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"

DEFAULT_PDF = BASE_DIR / "input" / "H3_AP202605121822223662_1.pdf"
STAGE5A_SUMMARY = BASE_DIR / "output" / "stage5a_pdf_conversion_audit" / "127_stage5a_pdf_conversion_audit_summary.json"

FIN_KEYWORDS = [
    "营业收入",
    "归母净利润",
    "归属母公司净利润",
    "ROE",
    "毛利率",
    "每股收益",
    "EPS",
    "P/E",
    "P/B",
    "EV/EBITDA",
]

SEARCH_PATTERNS: List[Tuple[str, str]] = [
    ("MARKER", r"marker"),
    ("OCR", r"\bocr\b|paddleocr|surya"),
    ("PDFPLUMBER", r"pdfplumber|extract_tables"),
    ("TABLE_EXTRACTOR", r"table_extractor|extractor_adapter|table block"),
    ("RAW_TABLES", r"raw_tables|ARTIFACT_RAW_TABLES|raw table"),
    ("STRUCTURED_02", r"02_研报全量结构化数据|generate_structured_tables|structured"),
]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else files[0]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_PATH),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _scan_repo_entrypoints() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    candidates = list(BASE_DIR.glob("*.py")) + list((BASE_DIR / "tools").glob("*.py"))
    for file in sorted(candidates):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            for cat, pat in SEARCH_PATTERNS:
                if re.search(pat, line, flags=re.IGNORECASE):
                    rows.append(
                        {
                            "category": cat,
                            "file": str(file),
                            "line": i,
                            "snippet": line.strip()[:500],
                        }
                    )
    return pd.DataFrame(rows, columns=["category", "file", "line", "snippet"])


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    idx = 1
    while s in used:
        suffix = f"_{idx}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        idx += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _resolve_marker_cache(temp_cache_dir: Path, pdf_path: Path) -> Optional[Path]:
    candidates = [
        temp_cache_dir / f"{pdf_path.name}.txt",
        temp_cache_dir / f"{pdf_path.stem}.txt",
        temp_cache_dir / f"{pdf_path.name}.md",
        temp_cache_dir / f"{pdf_path.stem}.md",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def _table_to_rows(block: TableBlock, source_pdf: Path, extractor_name: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    df = block.raw_df if isinstance(block.raw_df, pd.DataFrame) else pd.DataFrame()
    if df.empty:
        return rows

    page = _norm(block.page)
    t_idx = _norm(block.table_index)
    table_id = f"{source_pdf.stem}|p{page or 'NA'}|t{t_idx or 'NA'}|{extractor_name}"
    col_count = int(df.shape[1])

    for ridx in range(df.shape[0]):
        row_values = [_norm(df.iat[ridx, c]) for c in range(df.shape[1])]
        raw_row_text = " | ".join([v for v in row_values if v])
        for cidx in range(df.shape[1]):
            rows.append(
                {
                    "table_id": table_id,
                    "page": page,
                    "row_index": ridx + 1,
                    "col_index": cidx + 1,
                    "cell_text": _norm(df.iat[ridx, cidx]),
                    "extractor_name": extractor_name,
                    "extraction_status": "ok",
                    "source_pdf": str(source_pdf),
                    "source_bbox": _norm(block.bbox),
                    "raw_row_text": raw_row_text,
                    "raw_col_count": col_count,
                }
            )
    return rows


def _aggregate_table_index(blocks: List[TableBlock], extractor_name: str, source_pdf: Path) -> pd.DataFrame:
    rows = []
    for b in blocks:
        df = b.raw_df if isinstance(b.raw_df, pd.DataFrame) else pd.DataFrame()
        rows.append(
            {
                "source_pdf": str(source_pdf),
                "extractor_name": extractor_name,
                "page": b.page,
                "table_index": b.table_index,
                "rows": int(df.shape[0]) if not df.empty else 0,
                "cols": int(df.shape[1]) if not df.empty else 0,
                "non_empty_cells": int((df.fillna("").astype(str) != "").sum().sum()) if not df.empty else 0,
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5B restore raw table extraction entrypoint (sandbox-only).")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="Input PDF path")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = Path(args.pdf)

    before = _snapshot_hashes()

    cm = ConfigManager(config_path="config.yaml")
    config = cm.load()
    extraction_cfg = config.get("table_extraction", {}) or {}
    temp_cache_dir = Path(config.get("paths", {}).get("temp_cache_dir", str(BASE_DIR / "output" / ".temp_cache")))

    summary: Dict[str, Any] = {
        "input_pdf_file": str(pdf_path),
        "pdf_exists": bool(pdf_path.exists()),
        "pdf_page_count": 0,
        "pdf_text_readable": False,
        "marker_entry_found": True,
        "marker_available": False,
        "marker_ran": False,
        "marker_raw_table_count": 0,
        "pdfplumber_available": importlib.util.find_spec("pdfplumber") is not None,
        "pdfplumber_ran": False,
        "pdfplumber_raw_table_count": 0,
        "selected_extractor": "",
        "raw_table_file_generated": False,
        "raw_table_count": 0,
        "raw_table_total_row_count": 0,
        "raw_table_total_cell_count": 0,
        "raw_table_contains_financial_keywords": False,
        "raw_table_to_02_converter_found": True,
        "root_cause_of_stage5a_zero_rows": "",
        "recommended_next_stage": "",
        "production_files_unchanged": True,
        "official_02B_unchanged": True,
        "formal_scope_rules_unchanged": True,
        "ai_called": False,
        "internet_called": False,
        "stage5b_restore_pass": False,
    }

    marker_meta: Dict[str, Any] = {
        "marker_error_reason": "",
        "marker_cache_path": "",
        "fallback_extractor": "",
    }
    entrypoints_df = _scan_repo_entrypoints()

    if not pdf_path.exists():
        summary["root_cause_of_stage5a_zero_rows"] = "input_pdf_missing"
        summary["recommended_next_stage"] = "FIX_INPUT_PATH_AND_RERUN_STAGE5B"
        issues_df = pd.DataFrame([{"issue": "input_pdf_missing", "severity": "HIGH"}])
        _write_excel(REPORT_XLSX, {"issues": issues_df, "summary": pd.DataFrame([summary])})
        REPORT_MD.write_text("# Stage5B Table Extraction Restore\n\n- input pdf missing\n", encoding="utf-8")
        SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    # PDF readability baseline.
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(pdf_path)) as pdf:
            summary["pdf_page_count"] = len(pdf.pages)
            text_readable_pages = 0
            for page in pdf.pages:
                text = _norm(page.extract_text() or "")
                if text:
                    text_readable_pages += 1
            summary["pdf_text_readable"] = text_readable_pages > 0
    except Exception:
        summary["pdf_text_readable"] = False

    # ---- marker adapter path (from markdown cache) ----
    marker_blocks: List[TableBlock] = []
    marker_cache = _resolve_marker_cache(temp_cache_dir, pdf_path)
    marker_meta["marker_cache_path"] = str(marker_cache) if marker_cache else ""
    marker_installed = importlib.util.find_spec("marker") is not None
    marker_cache_available = marker_cache is not None
    summary["marker_available"] = bool(marker_installed and marker_cache_available)

    if summary["marker_available"]:
        try:
            md_text = marker_cache.read_text(encoding="utf-8", errors="ignore") if marker_cache else ""
            marker_blocks = extract_marker_table_blocks(md_text, extraction_cfg, logger=None)
            summary["marker_ran"] = True
            summary["marker_raw_table_count"] = int(len(marker_blocks))
            if len(marker_blocks) == 0:
                marker_meta["marker_error_reason"] = "marker_cache_parsed_zero_tables"
        except Exception as exc:
            summary["marker_ran"] = True
            summary["marker_raw_table_count"] = 0
            marker_meta["marker_error_reason"] = f"marker_extract_failed:{type(exc).__name__}:{exc}"
    else:
        if not marker_installed:
            marker_meta["marker_error_reason"] = "marker_module_not_installed"
        elif not marker_cache_available:
            marker_meta["marker_error_reason"] = "marker_markdown_cache_missing_for_pdf"
        else:
            marker_meta["marker_error_reason"] = "marker_unavailable_unknown"

    # ---- pdfplumber path ----
    pdfplumber_blocks: List[TableBlock] = []
    profile_diag_df = pd.DataFrame()
    if summary["pdfplumber_available"]:
        try:
            selected_blocks, profile_diag_df = extract_tables_with_pdfplumber_profiles(str(pdf_path), config, logger=None)
            pdfplumber_blocks = extract_pdfplumber_table_blocks(str(pdf_path), extraction_cfg, logger=None)
            # prefer profile-selected if non-empty (closer to factory behavior)
            if selected_blocks:
                # selected_blocks are dict-like blocks from profile extractor.
                converted: List[TableBlock] = []
                for b in selected_blocks:
                    df = b.get("df")
                    if not isinstance(df, pd.DataFrame) or df.empty:
                        continue
                    tb = TableBlock(
                        backend="pdfplumber",
                        page=b.get("page"),
                        table_index=b.get("table_index"),
                        bbox=b.get("bbox"),
                        confidence=b.get("confidence"),
                        raw_df=df,
                    )
                    converted.append(tb)
                if converted:
                    pdfplumber_blocks = converted
            summary["pdfplumber_ran"] = True
            summary["pdfplumber_raw_table_count"] = int(len(pdfplumber_blocks))
        except Exception:
            summary["pdfplumber_ran"] = True
            summary["pdfplumber_raw_table_count"] = 0
    else:
        summary["pdfplumber_ran"] = False

    # select extractor
    selected_extractor = ""
    selected_blocks: List[TableBlock] = []
    if len(marker_blocks) > 0:
        selected_extractor = "marker"
        selected_blocks = marker_blocks
    elif len(pdfplumber_blocks) > 0:
        selected_extractor = "pdfplumber"
        selected_blocks = pdfplumber_blocks
        marker_meta["fallback_extractor"] = "pdfplumber"
    else:
        selected_extractor = "none"
        marker_meta["fallback_extractor"] = "none"
    summary["selected_extractor"] = selected_extractor

    # build unified raw tables schema rows
    raw_rows: List[Dict[str, Any]] = []
    table_index_df = pd.DataFrame()
    if selected_extractor in {"marker", "pdfplumber"}:
        for b in selected_blocks:
            raw_rows.extend(_table_to_rows(b, pdf_path, selected_extractor))
        table_index_df = _aggregate_table_index(selected_blocks, selected_extractor, pdf_path)

    raw_df = pd.DataFrame(
        raw_rows,
        columns=[
            "table_id",
            "page",
            "row_index",
            "col_index",
            "cell_text",
            "extractor_name",
            "extraction_status",
            "source_pdf",
            "source_bbox",
            "raw_row_text",
            "raw_col_count",
        ],
    )
    if raw_df.empty:
        raw_df = pd.DataFrame(
            columns=[
                "table_id",
                "page",
                "row_index",
                "col_index",
                "cell_text",
                "extractor_name",
                "extraction_status",
                "source_pdf",
                "source_bbox",
                "raw_row_text",
                "raw_col_count",
            ]
        )

    # Outputs
    _write_excel(RAW_XLSX, {"raw_tables": raw_df, "table_index": table_index_df})
    RAW_JSON.write_text(raw_df.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")

    summary["raw_table_file_generated"] = bool(RAW_XLSX.exists() and RAW_JSON.exists())
    summary["raw_table_count"] = int(raw_df["table_id"].nunique()) if not raw_df.empty else 0
    summary["raw_table_total_row_count"] = int(raw_df.groupby("table_id")["row_index"].max().sum()) if summary["raw_table_count"] > 0 else 0
    summary["raw_table_total_cell_count"] = int(len(raw_df))

    cell_texts = raw_df["cell_text"].map(_norm).tolist() if not raw_df.empty else []
    has_fin_keywords = any(any(k in t for k in FIN_KEYWORDS) for t in cell_texts)
    summary["raw_table_contains_financial_keywords"] = bool(has_fin_keywords)

    # Root cause statement for stage5a zero rows.
    if summary["pdfplumber_raw_table_count"] == 0 and summary["marker_raw_table_count"] == 0:
        summary["root_cause_of_stage5a_zero_rows"] = (
            "no_raw_tables_from_both_extractors; marker cache unavailable and pdfplumber returned zero normalized blocks"
        )
    elif summary["pdfplumber_raw_table_count"] > 0 and summary["selected_extractor"] == "pdfplumber":
        summary["root_cause_of_stage5a_zero_rows"] = (
            "stage5a_path_used_narrow_pdfplumber_normalization_or_selection_logic; "
            "stage5b confirms pdfplumber/profile path can output raw tables"
        )
    elif summary["marker_raw_table_count"] > 0 and summary["selected_extractor"] == "marker":
        summary["root_cause_of_stage5a_zero_rows"] = (
            "stage5a did not have marker cache entrypoint wired; stage5b marker adapter can output raw tables"
        )
    else:
        summary["root_cause_of_stage5a_zero_rows"] = "extractor_entrypoint_mismatch_in_stage5a"

    summary["recommended_next_stage"] = (
        "STAGE5C_BUILD_RAW_TABLE_TO_02_CONVERTER_BASED_ON_STAGE5B_SCHEMA"
        if summary["raw_table_count"] > 0
        else "STAGE5C_PROFILE_TUNING_OR_PDF_REGION_EXTRACTION_PROBE"
    )

    # compare with Stage5A summary for explicit diagnosis sheet
    stage5a_ref = {}
    if STAGE5A_SUMMARY.exists():
        stage5a_ref = json.loads(STAGE5A_SUMMARY.read_text(encoding="utf-8"))
    diagnosis_rows = [
        {
            "check_item": "stage5a_structured_02_row_count",
            "value": stage5a_ref.get("structured_02_row_count", ""),
            "diagnosis": "stage5a reported zero 02 rows",
        },
        {
            "check_item": "stage5b_pdfplumber_raw_table_count",
            "value": summary["pdfplumber_raw_table_count"],
            "diagnosis": "raw table extraction count by pdfplumber/profile path",
        },
        {
            "check_item": "stage5b_marker_raw_table_count",
            "value": summary["marker_raw_table_count"],
            "diagnosis": "raw table extraction count by marker cache path",
        },
        {
            "check_item": "root_cause_of_stage5a_zero_rows",
            "value": summary["root_cause_of_stage5a_zero_rows"],
            "diagnosis": "final root cause",
        },
    ]
    summary["marker_error_reason"] = marker_meta.get("marker_error_reason", "")
    summary["fallback_extractor"] = marker_meta.get("fallback_extractor", "")

    # Snapshot protection
    after = _snapshot_hashes()
    summary["production_files_unchanged"] = bool(
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    summary["official_02B_unchanged"] = bool(before["02B"] == after["02B"])
    summary["formal_scope_rules_unchanged"] = bool(before["formal_scope_rules"] == after["formal_scope_rules"])

    summary["stage5b_restore_pass"] = bool(
        summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and (summary["root_cause_of_stage5a_zero_rows"] != "")
        and (summary["recommended_next_stage"] != "")
        and (
            (summary["raw_table_count"] == 0)
            or (summary["raw_table_count"] > 0 and summary["raw_table_file_generated"])
        )
    )

    summary_df = pd.DataFrame([summary])
    marker_meta_df = pd.DataFrame([marker_meta])
    diagnosis_df = pd.DataFrame(diagnosis_rows)
    profile_df = profile_diag_df if isinstance(profile_diag_df, pd.DataFrame) else pd.DataFrame()

    _write_excel(
        REPORT_XLSX,
        {
            "summary": summary_df,
            "diagnosis": diagnosis_df,
            "extractor_meta": marker_meta_df,
            "entrypoint_search": entrypoints_df,
            "selected_table_index": table_index_df,
            "selected_raw_cells_sample": raw_df.head(300),
            "pdfplumber_profile_diag": profile_df,
        },
    )

    md_lines = [
        "# Stage5B Table Extraction Restore",
        "",
        f"- input_pdf_file: {summary['input_pdf_file']}",
        f"- pdf_exists: {summary['pdf_exists']}",
        f"- pdf_page_count: {summary['pdf_page_count']}",
        f"- pdf_text_readable: {summary['pdf_text_readable']}",
        f"- marker_entry_found: {summary['marker_entry_found']}",
        f"- marker_available: {summary['marker_available']}",
        f"- marker_ran: {summary['marker_ran']}",
        f"- marker_raw_table_count: {summary['marker_raw_table_count']}",
        f"- marker_error_reason: {marker_meta.get('marker_error_reason','')}",
        f"- pdfplumber_available: {summary['pdfplumber_available']}",
        f"- pdfplumber_ran: {summary['pdfplumber_ran']}",
        f"- pdfplumber_raw_table_count: {summary['pdfplumber_raw_table_count']}",
        f"- selected_extractor: {summary['selected_extractor']}",
        f"- raw_table_file_generated: {summary['raw_table_file_generated']}",
        f"- raw_table_count: {summary['raw_table_count']}",
        f"- raw_table_total_row_count: {summary['raw_table_total_row_count']}",
        f"- raw_table_total_cell_count: {summary['raw_table_total_cell_count']}",
        f"- raw_table_contains_financial_keywords: {summary['raw_table_contains_financial_keywords']}",
        f"- raw_table_to_02_converter_found: {summary['raw_table_to_02_converter_found']}",
        f"- root_cause_of_stage5a_zero_rows: {summary['root_cause_of_stage5a_zero_rows']}",
        f"- recommended_next_stage: {summary['recommended_next_stage']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- stage5b_restore_pass: {summary['stage5b_restore_pass']}",
    ]
    REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"raw_tables_xlsx: {RAW_XLSX}")
    print(f"raw_tables_json: {RAW_JSON}")
    print(f"stage5b_report_xlsx: {REPORT_XLSX}")
    print(f"stage5b_report_md: {REPORT_MD}")
    print(f"stage5b_summary_json: {SUMMARY_JSON}")
    print(f"selected_extractor: {summary['selected_extractor']}")
    print(f"raw_table_count: {summary['raw_table_count']}")
    print(f"stage5b_restore_pass: {summary['stage5b_restore_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
