import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_ROOT = Path(r"D:\_datefac\output")
DEFAULT_DELIVERY_DIR = Path(r"D:\_datefac\output\delivery_package")
DEFAULT_TRIAL_ROOT = Path(r"D:\_datefac\output\_stage1_safe_runner_trial")
DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_SANDBOX_DELIVERY_DIR = DEFAULT_TRIAL_ROOT / "delivery_package"
DEFAULT_STAGE1_MANIFEST = DEFAULT_DELIVERY_DIR / "27_stage1_pdfplumber_selected_samples_manifest.json"
BASELINE_GUARD_PDF = "H3_AP202605091822098939_1.pdf"
PRODUCTION_PREFIX_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]

YEAR_RE = re.compile(r"\b(20\d{2}(?:[AE])?)\b", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
METRIC_KEYWORDS = [
    "营业收入",
    "收入",
    "归属母公司净利润",
    "归母净利润",
    "净利润",
    "每股收益",
    "EPS",
    "P/E",
    "PE",
    "P/B",
    "PB",
    "EV/EBITDA",
    "ROE",
    "EBITDA",
    "毛利率",
    "净利率",
]
RATING_DISCLAIMER_HINTS = ["评级", "免责声明", "法律声明", "风险提示", "投资建议"]

STANDARD_METRIC_MAP = {
    "营业收入": ["营业收入", "收入"],
    "归属母公司净利润": ["归属母公司净利润", "归母净利润", "净利润"],
    "每股收益": ["每股收益", "EPS"],
    "P/E": ["P/E", "PE"],
    "P/B": ["P/B", "PB"],
    "EV/EBITDA": ["EV/EBITDA"],
    "ROE": ["ROE"],
    "EBITDA": ["EBITDA"],
    "毛利率": ["毛利率"],
    "净利率": ["净利率"],
}
STANDARD_METRIC_PRIORITY = [
    "营业收入",
    "归属母公司净利润",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "ROE",
    "EBITDA",
    "毛利率",
    "净利率",
]

SAFE_ENTRYPOINT_CANDIDATES = [
    r"D:\_datefac\tools\probe_pdf_tables.py",
    r"D:\_datefac\tools\probe_pdfplumber_profiles.py",
    r"D:\_datefac\tools\probe_extractors.py",
    r"D:\_datefac\tools\check_delivery_state.py",
]
UNSAFE_ENTRYPOINTS = [
    ("D:\\_datefac\\factory_core.py", "forbidden: factory_core entrypoint"),
    ("D:\\_datefac\\tools\\probe_visual_table_regions.py", "forbidden: vision-related probe"),
    ("D:\\_datefac\\tools\\check_vision_dependencies.py", "forbidden: vision dependency chain"),
    ("D:\\_datefac\\tools\\prewarm_marker_models.py", "forbidden: may trigger model downloads"),
]


@dataclass
class SampleItem:
    pdf_path: Path
    sample_id: str
    company: str
    approved_pages: List[int]
    ignored_pages: List[int]
    source: str = ""


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _safe_sheet_name(name: str, used: set) -> str:
    safe = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = safe
    i = 1
    while safe in used:
        suffix = f"_{i}"
        safe = f"{base[:31-len(suffix)]}{suffix}"
        i += 1
    used.add(safe)
    return safe


def _safe_write_text(path: Path, text: str) -> Path:
    final = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_text(text, encoding="utf-8")
    return final


def _safe_write_excel(sheets: Dict[str, pd.DataFrame], path: Path) -> Path:
    final = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(final, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)
    return final


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _collect_production_guard_files(delivery_dir: Path) -> List[Path]:
    out = []
    for pattern in PRODUCTION_PREFIX_PATTERNS:
        matched = sorted(delivery_dir.glob(pattern))
        if matched:
            out.append(matched[0])
    return out


def _snapshot_files(files: List[Path]) -> Dict[str, Dict[str, str]]:
    snap = {}
    for file in files:
        if not file.exists():
            snap[str(file)] = {"exists": "0", "size": "0", "sha256": ""}
        else:
            snap[str(file)] = {"exists": "1", "size": str(file.stat().st_size), "sha256": _sha256(file)}
    return snap


def _compare_snapshot(before: Dict[str, Dict[str, str]], after: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    keys = sorted(set(before.keys()) | set(after.keys()))
    for key in keys:
        b = before.get(key, {"exists": "0", "size": "0", "sha256": ""})
        a = after.get(key, {"exists": "0", "size": "0", "sha256": ""})
        rows.append(
            {
                "file": key,
                "before_exists": b["exists"],
                "after_exists": a["exists"],
                "before_size": b["size"],
                "after_size": a["size"],
                "before_sha256": b["sha256"],
                "after_sha256": a["sha256"],
                "changed": "1" if b != a else "0",
            }
        )
    return rows


def _parse_int_list(v) -> List[int]:
    if v is None:
        return []
    if isinstance(v, list):
        out = []
        for x in v:
            try:
                out.append(int(x))
            except Exception:
                pass
        return out
    text = _norm(v)
    if not text:
        return []
    out = []
    for p in re.split(r"[,\s]+", text):
        if not p:
            continue
        try:
            out.append(int(p))
        except Exception:
            pass
    return out


def _load_manifest(path: Path) -> Tuple[List[SampleItem], List[Dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    items = payload.get("samples", payload if isinstance(payload, list) else [])
    samples = []
    source_rows = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        pdf_path = Path(_norm(item.get("pdf_path") or item.get("pdf")))
        sample_id = _norm(item.get("sample_id")) or f"S{i+1}"
        company = _norm(item.get("company"))
        approved = _parse_int_list(item.get("approved_pages"))
        ignored = _parse_int_list(item.get("ignored_pages"))
        samples.append(
            SampleItem(
                pdf_path=pdf_path,
                sample_id=sample_id,
                company=company,
                approved_pages=approved,
                ignored_pages=ignored,
                source="manifest",
            )
        )
        source_rows.append(
            {
                "sample_id": sample_id,
                "pdf_path": str(pdf_path),
                "company": company,
                "approved_pages": ",".join(str(x) for x in approved),
                "ignored_pages": ",".join(str(x) for x in ignored),
            }
        )
    return samples, source_rows


def _build_default_stage1_manifest(path: Path) -> Path:
    payload = {
        "samples": [
            {
                "sample_id": "S1",
                "pdf_path": r"D:\_datefac\input\H3_AP202605141822317484_1.pdf",
                "company": "三鑫医疗",
                "approved_pages": [1, 4, 5],
                "ignored_pages": [],
            },
            {
                "sample_id": "S2",
                "pdf_path": r"D:\_datefac\input\H3_AP202605121822223662_1.pdf",
                "company": "冠豪高新",
                "approved_pages": [2, 3],
                "ignored_pages": [],
            },
            {
                "sample_id": "S3",
                "pdf_path": r"D:\_datefac\input\H3_AP202605141822318060_1.pdf",
                "company": "科锐国际",
                "approved_pages": [5],
                "ignored_pages": [6],
            },
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_samples(manifest: Optional[Path], pdf_args: List[str]) -> Tuple[List[SampleItem], List[Dict[str, str]], Path]:
    if manifest and pdf_args:
        raise ValueError("Use either --manifest or --pdf, not both.")
    if not manifest and not pdf_args:
        manifest = _build_default_stage1_manifest(DEFAULT_STAGE1_MANIFEST)
        return _load_manifest(manifest)[0], _load_manifest(manifest)[1], manifest
    if manifest:
        samples, rows = _load_manifest(manifest)
        return samples, rows, manifest

    samples = []
    rows = []
    for i, pdf in enumerate(pdf_args):
        sample_id = f"CLI{i+1}"
        p = Path(pdf)
        samples.append(SampleItem(pdf_path=p, sample_id=sample_id, company="", approved_pages=[], ignored_pages=[], source="cli"))
        rows.append({"sample_id": sample_id, "pdf_path": str(p), "company": "", "approved_pages": "", "ignored_pages": ""})
    return samples, rows, Path("")


def _discover_safe_entrypoints() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    safe = []
    for path in SAFE_ENTRYPOINT_CANDIDATES:
        p = Path(path)
        safe.append({"entrypoint": path, "exists": "1" if p.exists() else "0", "notes": "safe non-vision candidate"})
    unsafe = []
    for path, reason in UNSAFE_ENTRYPOINTS:
        unsafe.append({"entrypoint": path, "exists": "1" if Path(path).exists() else "0", "blocked_reason": reason})
    return safe, unsafe


def _validate_samples(samples: List[SampleItem], strict_scope: bool, allow_baseline: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[SampleItem]]:
    rows = []
    errors = []
    resolved = []
    seen = set()
    for item in samples:
        abs_path = item.pdf_path if item.pdf_path.is_absolute() else DEFAULT_INPUT_DIR / item.pdf_path
        key = str(abs_path).lower()
        duplicate = key in seen
        seen.add(key)
        exists = abs_path.exists()
        is_pdf = abs_path.suffix.lower() == ".pdf"
        baseline_hit = abs_path.name == BASELINE_GUARD_PDF
        in_scope = str(abs_path).lower().startswith(str(DEFAULT_INPUT_DIR).lower())
        approved = item.approved_pages
        rows.append(
            {
                "sample_id": item.sample_id,
                "company": item.company,
                "pdf_path": str(abs_path),
                "exists": "1" if exists else "0",
                "is_pdf": "1" if is_pdf else "0",
                "duplicate": "1" if duplicate else "0",
                "strict_scope_pass": "1" if (not strict_scope or in_scope) else "0",
                "baseline_guard_hit": "1" if baseline_hit else "0",
                "approved_pages": ",".join(str(x) for x in approved),
                "ignored_pages": ",".join(str(x) for x in item.ignored_pages),
            }
        )
        if not exists:
            errors.append({"sample_id": item.sample_id, "error_code": "MISSING_PDF", "detail": str(abs_path)})
        if not is_pdf:
            errors.append({"sample_id": item.sample_id, "error_code": "NOT_PDF", "detail": str(abs_path)})
        if duplicate:
            errors.append({"sample_id": item.sample_id, "error_code": "DUPLICATE_PDF", "detail": str(abs_path)})
        if strict_scope and not in_scope:
            errors.append({"sample_id": item.sample_id, "error_code": "STRICT_SCOPE_VIOLATION", "detail": str(abs_path)})
        if baseline_hit and not allow_baseline:
            errors.append({"sample_id": item.sample_id, "error_code": "BASELINE_NOT_ALLOWED", "detail": str(abs_path)})
        if not approved:
            errors.append({"sample_id": item.sample_id, "error_code": "MISSING_APPROVED_PAGES", "detail": str(abs_path)})

        resolved.append(
            SampleItem(
                pdf_path=abs_path,
                sample_id=item.sample_id,
                company=item.company,
                approved_pages=approved,
                ignored_pages=item.ignored_pages,
                source=item.source,
            )
        )
    return rows, errors, resolved


def _run_delivery_check_json(delivery_dir: Path, no_write: bool = True) -> Dict[str, str]:
    script = Path(r"D:\_datefac\tools\check_delivery_state.py")
    if not script.exists():
        return {"overall_status": "UNKNOWN", "pass_count": "0", "warn_count": "0", "fail_count": "0"}
    cmd = [sys.executable, str(script), "--delivery-dir", str(delivery_dir), "--json"]
    if no_write:
        cmd.append("--no-write-report")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        data = json.loads(p.stdout) if p.stdout.strip() else {}
        return {
            "overall_status": _norm(data.get("overall_status")),
            "pass_count": _norm(data.get("pass_count")),
            "warn_count": _norm(data.get("warn_count")),
            "fail_count": _norm(data.get("fail_count")),
            "check_count": _norm(data.get("check_count")),
        }
    except Exception:
        return {"overall_status": "UNKNOWN", "pass_count": "0", "warn_count": "0", "fail_count": "0", "check_count": "0"}


def _ensure_under(parent: Path, child: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _row_text(row_values: List[str]) -> str:
    return " | ".join([_norm(v) for v in row_values if _norm(v)])


def _metric_hits(text: str) -> List[str]:
    upper = text.upper()
    hits = []
    for kw in METRIC_KEYWORDS:
        if kw.upper() in upper:
            hits.append(kw)
    return sorted(set(hits))


def _year_hits(text: str) -> List[str]:
    return sorted(set(m.group(1).upper() for m in YEAR_RE.finditer(text)))


def _table_confidence(year_count: int, metric_hit_count: int, text: str) -> Tuple[str, str]:
    if any(h in text for h in RATING_DISCLAIMER_HINTS):
        return "ignore", "ignore"
    if year_count == 0:
        return "ignore", "ignore"
    if metric_hit_count >= 3:
        return "high", "likely_core_metric"
    if metric_hit_count >= 1:
        return "medium", "manual_review_candidate"
    return "low", "ignore"


def _extract_with_pdfplumber(sample: SampleItem, asset_dir: Path) -> Dict[str, object]:
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:
        return {
            "sample_status": "FAIL",
            "error": f"pdfplumber_unavailable:{type(exc).__name__}:{exc}",
            "raw_tables_index": [],
            "raw_table_cells": [],
            "diag_rows": [],
            "candidate_rows": [],
            "tables_index_02": [],
            "table_dataframes": {},
        }

    raw_tables_index = []
    raw_table_cells = []
    diag_rows = []
    candidate_rows = []
    tables_index_02 = []
    table_dataframes = {}

    asset_package = asset_dir.name
    pdf_file = sample.pdf_path.name
    overall_errors = 0
    total_tables = 0
    pages_processed = 0
    candidate_tables = 0

    try:
        with pdfplumber.open(str(sample.pdf_path)) as pdf:
            pdf_pages = len(pdf.pages)
            for page in sample.approved_pages:
                if page < 1 or page > pdf_pages:
                    overall_errors += 1
                    diag_rows.append(
                        {
                            "asset_package": asset_package,
                            "pdf_file": pdf_file,
                            "page": page,
                            "diagnostic_type": "page_out_of_range",
                            "detail": f"page={page}, pdf_pages={pdf_pages}",
                            "status": "error",
                        }
                    )
                    continue
                pages_processed += 1
                try:
                    tables = pdf.pages[page - 1].extract_tables() or []
                except Exception as page_exc:
                    overall_errors += 1
                    diag_rows.append(
                        {
                            "asset_package": asset_package,
                            "pdf_file": pdf_file,
                            "page": page,
                            "diagnostic_type": "extract_failed",
                            "detail": f"{type(page_exc).__name__}: {page_exc}",
                            "status": "error",
                        }
                    )
                    continue

                if not tables:
                    diag_rows.append(
                        {
                            "asset_package": asset_package,
                            "pdf_file": pdf_file,
                            "page": page,
                            "diagnostic_type": "no_tables",
                            "detail": "pdfplumber extracted zero tables on approved page",
                            "status": "warn",
                        }
                    )
                    continue

                for t_idx, table in enumerate(tables, start=1):
                    total_tables += 1
                    df = pd.DataFrame(table).fillna("").astype(str)
                    row_count, col_count = df.shape
                    if row_count == 0 or col_count == 0:
                        diag_rows.append(
                            {
                                "asset_package": asset_package,
                                "pdf_file": pdf_file,
                                "page": page,
                                "diagnostic_type": "empty_table",
                                "detail": f"table_index={t_idx}",
                                "status": "warn",
                            }
                        )
                        continue
                    table_text = " ".join(df.astype(str).values.flatten().tolist())
                    year_cells = _year_hits(table_text)
                    m_hits = _metric_hits(table_text)
                    conf, ctype = _table_confidence(len(year_cells), len(m_hits), table_text)
                    extraction_status = "ok" if ctype != "ignore" or year_cells else "weak"
                    if ctype != "ignore":
                        candidate_tables += 1
                    raw_tables_index.append(
                        {
                            "asset_package": asset_package,
                            "pdf_file": pdf_file,
                            "company": sample.company,
                            "page": page,
                            "table_index": t_idx,
                            "backend": "pdfplumber",
                            "row_count": row_count,
                            "column_count": col_count,
                            "detected_year_cells": "|".join(year_cells),
                            "metric_keyword_hits": "|".join(m_hits),
                            "candidate_type": ctype,
                            "confidence": conf,
                            "extraction_status": extraction_status,
                            "source_note": "approved_pages_only_pdfplumber",
                        }
                    )
                    tables_index_02.append(
                        {
                            "asset_package": asset_package,
                            "pdf_file": pdf_file,
                            "company": sample.company,
                            "page": page,
                            "table_index": t_idx,
                            "row_count": row_count,
                            "column_count": col_count,
                            "detected_year_cells": "|".join(year_cells),
                            "metric_keyword_hits": "|".join(m_hits),
                        }
                    )

                    sheet_name = f"p{page:03d}_t{t_idx:03d}"
                    table_dataframes[sheet_name] = df.copy()

                    for r in range(row_count):
                        row_values = []
                        for c in range(col_count):
                            cell = _norm(df.iat[r, c])
                            row_values.append(cell)
                            raw_table_cells.append(
                                {
                                    "asset_package": asset_package,
                                    "pdf_file": pdf_file,
                                    "page": page,
                                    "table_index": t_idx,
                                    "row_index": r + 1,
                                    "col_index": c + 1,
                                    "cell_value": cell,
                                }
                            )
                        row_txt = _row_text(row_values)
                        row_hits = _metric_hits(row_txt)
                        if row_hits:
                            year_evidence = "|".join(_year_hits(row_txt) or year_cells)
                            route = "likely_core_metric" if conf == "high" else "manual_review_candidate"
                            candidate_rows.append(
                                {
                                    "asset_package": asset_package,
                                    "company": sample.company,
                                    "page": page,
                                    "table_index": t_idx,
                                    "metric_keyword": "|".join(row_hits),
                                    "matched_row_index": r + 1,
                                    "year_cells_in_table": year_evidence,
                                    "row_preview": row_txt[:300],
                                    "candidate_confidence": conf,
                                    "recommended_route": route,
                                }
                            )
    except Exception as exc:
        return {
            "sample_status": "FAIL",
            "error": f"pdf_read_failed:{type(exc).__name__}:{exc}",
            "raw_tables_index": raw_tables_index,
            "raw_table_cells": raw_table_cells,
            "diag_rows": diag_rows,
            "candidate_rows": candidate_rows,
            "tables_index_02": tables_index_02,
            "table_dataframes": table_dataframes,
        }

    if overall_errors > 0 and total_tables == 0:
        sample_status = "FAIL"
    elif total_tables == 0:
        sample_status = "WARN"
    else:
        sample_status = "PASS" if overall_errors == 0 else "PARTIAL"
    return {
        "sample_status": sample_status,
        "error": "",
        "raw_tables_index": raw_tables_index,
        "raw_table_cells": raw_table_cells,
        "diag_rows": diag_rows,
        "candidate_rows": candidate_rows,
        "tables_index_02": tables_index_02,
        "table_dataframes": table_dataframes,
        "pages_processed": pages_processed,
        "tables_extracted": total_tables,
        "candidate_tables": candidate_tables,
        "metric_candidate_rows": len(candidate_rows),
        "extraction_errors": overall_errors,
    }


def _write_sample_assets(sample: SampleItem, trial_assets_root: Path, result: Dict[str, object]) -> Dict[str, str]:
    sample_dir = trial_assets_root / f"{sample.pdf_path.stem}_资产包"
    sample_dir.mkdir(parents=True, exist_ok=True)

    raw_tables_index_df = pd.DataFrame(result.get("raw_tables_index", []))
    raw_cells_df = pd.DataFrame(result.get("raw_table_cells", []))
    diag_df = pd.DataFrame(result.get("diag_rows", []))
    candidates_df = pd.DataFrame(result.get("candidate_rows", []))
    tables_index_df = pd.DataFrame(result.get("tables_index_02", []))

    p02a = _safe_write_excel(
        {
            "raw_tables_index": raw_tables_index_df,
            "raw_table_cells": raw_cells_df,
            "extraction_diagnostics": diag_df,
        },
        sample_dir / "02A_研报原始表格资产.xlsx",
    )

    sheets_02 = {"tables_index": tables_index_df}
    table_sheets = result.get("table_dataframes", {})
    if isinstance(table_sheets, dict):
        for k, v in table_sheets.items():
            if isinstance(v, pd.DataFrame):
                sheets_02[k] = v
    p02 = _safe_write_excel(sheets_02, sample_dir / "02_研报全量结构化数据.xlsx")
    p05 = _safe_write_excel({"metric_candidates": candidates_df}, sample_dir / "05_stage1_core_metric_candidates.xlsx")
    summary_df = pd.DataFrame(
        [
            {
                "asset_package": sample_dir.name,
                "pdf_file": sample.pdf_path.name,
                "company": sample.company,
                "pages_processed": result.get("pages_processed", 0),
                "tables_extracted": result.get("tables_extracted", 0),
                "candidate_tables": result.get("candidate_tables", 0),
                "metric_candidate_rows": result.get("metric_candidate_rows", 0),
                "extraction_errors": result.get("extraction_errors", 0),
                "overall_sample_status": result.get("sample_status", "FAIL"),
            }
        ]
    )
    psummary = _safe_write_excel({"summary": summary_df}, sample_dir / "stage1_sandbox_asset_summary.xlsx")
    return {
        "asset_dir": str(sample_dir),
        "file_02A": str(p02a),
        "file_02": str(p02),
        "file_05": str(p05),
        "file_summary": str(psummary),
    }


def _write_trial_inventory(
    trial_run_dir: Path,
    per_sample_status_rows: List[Dict[str, object]],
    generated_file_rows: List[Dict[str, object]],
) -> Tuple[Path, Path]:
    inv_xlsx = _safe_write_excel(
        {
            "per_sample_status": pd.DataFrame(per_sample_status_rows),
            "generated_files": pd.DataFrame(generated_file_rows),
        },
        trial_run_dir / "stage1_trial_asset_inventory.xlsx",
    )
    lines = ["# Stage1 Trial Asset Inventory", ""]
    for row in per_sample_status_rows:
        lines.append(
            f"- {row.get('sample_id')} | status={row.get('sample_status')} | tables={row.get('tables_extracted')} | metric_rows={row.get('metric_candidate_rows')}"
        )
    inv_md = _safe_write_text(trial_run_dir / "stage1_trial_asset_inventory.md", "\n".join(lines))
    return inv_md, inv_xlsx


def _write_27_28_reports(
    delivery_dir: Path,
    task_title: str,
    runner_path: Path,
    started_at: str,
    finished_at: str,
    command_run: str,
    manifest_path: Path,
    trial_run_root: Path,
    per_sample_status_rows: List[Dict[str, object]],
    tables_extracted_rows: List[Dict[str, object]],
    metric_candidates_rows: List[Dict[str, object]],
    generated_file_rows: List[Dict[str, object]],
    production_guard_rows: List[Dict[str, str]],
    safety_checks_rows: List[Dict[str, str]],
    production_status_after: Dict[str, str],
) -> Tuple[Path, Path, Path, Path, str]:
    changed_count = sum(1 for r in production_guard_rows if r.get("changed") == "1")
    sample_statuses = [str(r.get("sample_status", "FAIL")) for r in per_sample_status_rows]
    pass_count = sum(1 for s in sample_statuses if s == "PASS")
    fail_count = sum(1 for s in sample_statuses if s == "FAIL")
    partial_count = sum(1 for s in sample_statuses if s == "PARTIAL")
    warn_count = sum(1 for s in sample_statuses if s == "WARN")

    if changed_count > 0 or fail_count == len(sample_statuses):
        build_status = "FAIL"
    elif fail_count > 0 or partial_count > 0:
        build_status = "PARTIAL"
    elif warn_count > 0:
        build_status = "WARN"
    else:
        build_status = "PASS"

    report27_md = _safe_write_text(
        delivery_dir / "27_stage1_pdfplumber_sandbox_asset_build_log.md",
        "\n".join(
            [
                "# Stage1 pdfplumber Sandbox Asset Build Log",
                "",
                f"- task_title: {task_title}",
                f"- runner_path: {runner_path}",
                f"- started_at: {started_at}",
                f"- finished_at: {finished_at}",
                f"- command_run: {command_run}",
                f"- manifest_path: {manifest_path}",
                f"- trial_run_root: {trial_run_root}",
                f"- sandbox_asset_build_status: {build_status}",
                f"- production_guard_changed_count: {changed_count}",
            ]
        ),
    )
    report27_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": task_title},
                    {"field": "runner_path", "value": str(runner_path)},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": finished_at},
                    {"field": "command_run", "value": command_run},
                    {"field": "manifest_path", "value": str(manifest_path)},
                    {"field": "trial_run_root", "value": str(trial_run_root)},
                    {"field": "sandbox_asset_build_status", "value": build_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "per_sample_pages_processed": pd.DataFrame(per_sample_status_rows),
            "per_sample_tables_extracted": pd.DataFrame(tables_extracted_rows),
            "files_generated_by_sample": pd.DataFrame(generated_file_rows),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks_rows),
        },
        delivery_dir / "27_stage1_pdfplumber_sandbox_asset_build_log.xlsx",
    )

    hmli = {"high": 0, "medium": 0, "low": 0, "ignore": 0}
    for row in metric_candidates_rows:
        c = _norm(row.get("candidate_confidence")).lower()
        if c in hmli:
            hmli[c] += 1
    ready_samples = [r.get("sample_id") for r in per_sample_status_rows if r.get("sample_status") == "PASS"]
    review_samples = [r.get("sample_id") for r in per_sample_status_rows if r.get("sample_status") != "PASS"]
    blockers = []
    if changed_count > 0:
        blockers.append("production_guard_changed")
    if not ready_samples:
        blockers.append("no_ready_samples")
    report28_md = _safe_write_text(
        delivery_dir / "28_stage1_pdfplumber_sandbox_asset_evaluation.md",
        "\n".join(
            [
                "# Stage1 pdfplumber Sandbox Asset Evaluation",
                "",
                f"- sandbox_asset_build_status: {build_status}",
                f"- production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}",
                f"- high_medium_low_candidate_counts: {json.dumps(hmli, ensure_ascii=False)}",
                f"- samples_ready_for_standardizer_trial: {','.join(str(x) for x in ready_samples)}",
                f"- samples_needing_manual_review: {','.join(str(x) for x in review_samples)}",
                f"- blockers: {'|'.join(blockers) if blockers else 'none'}",
            ]
        ),
    )
    report28_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "sandbox_asset_build_status", "value": build_status},
                    {"field": "production_delivery_status_after", "value": json.dumps(production_status_after, ensure_ascii=False)},
                    {"field": "selected_samples", "value": len(per_sample_status_rows)},
                    {"field": "samples_ready_for_standardizer_trial", "value": "|".join(str(x) for x in ready_samples)},
                    {"field": "samples_needing_manual_review", "value": "|".join(str(x) for x in review_samples)},
                    {"field": "blockers", "value": "|".join(blockers)},
                ]
            ),
            "per_sample_status": pd.DataFrame(per_sample_status_rows),
            "tables_extracted": pd.DataFrame(tables_extracted_rows),
            "metric_candidates": pd.DataFrame(metric_candidates_rows),
            "generated_files": pd.DataFrame(generated_file_rows),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks_rows),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Run standardizer trial on sandbox 02 outputs only for samples in PASS/PARTIAL.",
                    }
                ]
            ),
        },
        delivery_dir / "28_stage1_pdfplumber_sandbox_asset_evaluation.xlsx",
    )
    return report27_md, report27_xlsx, report28_md, report28_xlsx, build_status


def _write_23_24_reports(
    delivery_dir: Path,
    runner_path: Path,
    source_rows: List[Dict[str, str]],
    sample_rows: List[Dict[str, str]],
    safe_rows: List[Dict[str, str]],
    unsafe_rows: List[Dict[str, str]],
    errors: List[Dict[str, str]],
    status: str,
) -> Tuple[Path, Path, Path, Path]:
    report23_md = _safe_write_text(
        delivery_dir / "23_stage1_safe_runner_dry_run.md",
        "\n".join(
            [
                "# Stage1 Safe Runner Dry Run",
                "",
                f"- runner_path: {runner_path}",
                f"- dry_run_status: {status}",
                f"- sample_count: {len(sample_rows)}",
            ]
        ),
    )
    report23_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame([{"runner_path": str(runner_path), "dry_run_status": status, "sample_count": len(sample_rows)}]),
            "inputs": pd.DataFrame(source_rows),
            "sample_validation": pd.DataFrame(sample_rows),
            "safe_entrypoints": pd.DataFrame(safe_rows),
            "unsafe_entrypoints": pd.DataFrame(unsafe_rows),
            "errors": pd.DataFrame(errors),
        },
        delivery_dir / "23_stage1_safe_runner_dry_run.xlsx",
    )
    report24_md = _safe_write_text(
        delivery_dir / "24_stage1_safe_runner_implementation_report.md",
        "\n".join(
            [
                "# Stage1 Safe Runner Implementation Report",
                "",
                f"- implemented_runner_path: {runner_path}",
                f"- dry_run_status: {status}",
                "- why execute was not run: dry-run mode requested",
            ]
        ),
    )
    report24_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame([{"implemented_runner_path": str(runner_path), "dry_run_status": status}]),
            "runner_interface": pd.DataFrame(
                [
                    {"arg": "--manifest", "note": "sample list input"},
                    {"arg": "--execute --execute-sandbox", "note": "sandbox asset extraction"},
                    {"arg": "--pdfplumber-only", "note": "required in this task"},
                ]
            ),
            "safe_entrypoints": pd.DataFrame(safe_rows),
            "unsafe_entrypoints": pd.DataFrame(unsafe_rows),
            "dry_run_plan": pd.DataFrame(sample_rows),
            "dry_run_results": pd.DataFrame([{"dry_run_status": status}]),
            "delivery_status": pd.DataFrame(),
            "next_steps": pd.DataFrame([{"next_step": "run execute-sandbox mode"}]),
        },
        delivery_dir / "24_stage1_safe_runner_implementation_report.xlsx",
    )
    return report23_md, report23_xlsx, report24_md, report24_xlsx


def _parse_page_table_from_sheet(sheet_name: str) -> Tuple[int, int]:
    m = re.match(r"p(\d+)_t(\d+)", _norm(sheet_name).lower())
    if not m:
        return 0, 0
    return int(m.group(1)), int(m.group(2))


def _match_standard_metric(text: str) -> str:
    t = _norm(text).upper()
    for std in STANDARD_METRIC_PRIORITY:
        for kw in STANDARD_METRIC_MAP.get(std, []):
            if _norm(kw).upper() in t:
                return std
    return ""


def _detect_year_columns(df: pd.DataFrame) -> Dict[int, Tuple[str, List[str]]]:
    year_cols: Dict[int, Tuple[str, List[str]]] = {}
    if df is None or df.empty:
        return year_cols
    max_scan_rows = min(5, len(df))
    for cidx, col in enumerate(df.columns):
        flags: List[str] = []
        candidates: List[str] = []
        head_text = _norm(col)
        cells = [head_text]
        for ridx in range(max_scan_rows):
            cells.append(_norm(df.iat[ridx, cidx]))
        for cell in cells:
            for m in YEAR_RE.finditer(cell):
                token = m.group(1).upper()
                candidates.append(token)
        if not candidates:
            continue
        year = candidates[0]
        if re.fullmatch(r"20\d{2}", year):
            flags.append("year_suffix_missing")
        year_cols[cidx] = (year, flags)
    return year_cols


def _parse_numeric(cell: str) -> Tuple[Optional[float], List[str]]:
    text = _norm(cell)
    flags: List[str] = []
    if not text:
        return None, flags
    compact = text.replace(",", "").replace(" ", "").replace("％", "%")
    is_percent = compact.endswith("%")
    if is_percent:
        compact = compact[:-1]
        flags.append("percent_value")
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", compact):
        val = float(compact)
        if val < 0:
            flags.append("negative_value_present")
        return val, flags
    nums = NUM_RE.findall(compact)
    if len(nums) == 1:
        val = float(nums[0])
        flags.append("parsed_from_mixed_text")
        if val < 0:
            flags.append("negative_value_present")
        return val, flags
    if len(nums) > 1:
        flags.append("ambiguous_multi_numeric_cell")
    return None, flags


def _standardize_table_sheet(
    sample_id: str,
    asset_package: str,
    company: str,
    sheet_name: str,
    df: pd.DataFrame,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    standardized_rows: List[Dict[str, object]] = []
    manual_rows: List[Dict[str, object]] = []
    diag_rows: List[Dict[str, object]] = []
    page, table_index = _parse_page_table_from_sheet(sheet_name)
    year_cols = _detect_year_columns(df)
    if not year_cols:
        diag_rows.append(
            {
                "sample_id": sample_id,
                "sheet_name": sheet_name,
                "diagnostic_type": "no_year_columns",
                "detail": "no year-like evidence detected",
            }
        )
        return standardized_rows, manual_rows, diag_rows

    risky_flags = {
        "multi_metric_row_ambiguous",
        "ambiguous_year_value_alignment",
        "ambiguous_multi_numeric_cell",
        "no_year_columns",
        "standardizer_no_metric_candidates",
    }

    for ridx in range(len(df)):
        row_values = [_norm(x) for x in df.iloc[ridx].tolist()]
        row_text = _row_text(row_values)
        metric_positions: List[Tuple[int, str]] = []
        row_upper = row_text.upper()
        for std in STANDARD_METRIC_PRIORITY:
            best_pos = -1
            for kw in STANDARD_METRIC_MAP.get(std, []):
                pos = row_upper.find(_norm(kw).upper())
                if pos >= 0 and (best_pos < 0 or pos < best_pos):
                    best_pos = pos
            if best_pos >= 0:
                metric_positions.append((best_pos, std))
        metric_positions = sorted(metric_positions, key=lambda x: x[0])
        if not metric_positions:
            continue
        if len(metric_positions) > 1:
            manual_rows.append(
                {
                    "sample_id": sample_id,
                    "asset_package": asset_package,
                    "company": company,
                    "standard_metric": metric_positions[0][1],
                    "metric_keyword": metric_positions[0][1],
                    "year": "",
                    "value": "",
                    "unit_guess": "",
                    "source_page": page,
                    "source_table_index": table_index,
                    "source_row_index": ridx + 1,
                    "row_preview": row_text[:300],
                    "confidence": "low",
                    "route_recommendation": "manual_review_candidate",
                    "flags": "multi_metric_row_ambiguous",
                }
            )
            continue
        std_metric = metric_positions[0][1]

        extracted_any = False
        ambiguous_count = 0
        extracted_values = 0
        for cidx, (year, year_flags) in year_cols.items():
            if cidx >= len(row_values):
                continue
            raw_cell = row_values[cidx]
            val, flags = _parse_numeric(raw_cell)
            if val is None:
                if _norm(raw_cell):
                    ambiguous_count += 1
                continue
            extracted_any = True
            extracted_values += 1
            route = "likely_core_metric_trial"
            confidence = "high" if len(year_cols) >= 3 else "medium"
            row_flags = year_flags + flags
            if any(f in risky_flags for f in row_flags):
                route = "manual_review_candidate"
                confidence = "low"
            standardized_rows.append(
                {
                    "sample_id": sample_id,
                    "asset_package": asset_package,
                    "company": company,
                    "standard_metric": std_metric,
                    "metric_keyword": std_metric,
                    "year": year,
                    "value": val,
                    "unit_guess": "",
                    "source_page": page,
                    "source_table_index": table_index,
                    "source_row_index": ridx + 1,
                    "row_preview": row_text[:300],
                    "confidence": confidence,
                    "route_recommendation": route,
                    "flags": "|".join(sorted(set(row_flags))),
                }
            )
        if not extracted_any:
            flags = ["ambiguous_year_value_alignment"]
            if ambiguous_count > 0:
                flags.append("non_numeric_or_mixed_cells")
            manual_rows.append(
                {
                    "sample_id": sample_id,
                    "asset_package": asset_package,
                    "company": company,
                    "standard_metric": std_metric,
                    "metric_keyword": std_metric,
                    "year": "",
                    "value": "",
                    "unit_guess": "",
                    "source_page": page,
                    "source_table_index": table_index,
                    "source_row_index": ridx + 1,
                    "row_preview": row_text[:300],
                    "confidence": "low",
                    "route_recommendation": "manual_review_candidate",
                    "flags": "|".join(flags),
                }
            )
        else:
            if extracted_values != len(year_cols):
                manual_rows.append(
                    {
                        "sample_id": sample_id,
                        "asset_package": asset_package,
                        "company": company,
                        "standard_metric": std_metric,
                        "metric_keyword": std_metric,
                        "year": "",
                        "value": "",
                        "unit_guess": "",
                        "source_page": page,
                        "source_table_index": table_index,
                        "source_row_index": ridx + 1,
                        "row_preview": row_text[:300],
                        "confidence": "low",
                        "route_recommendation": "manual_review_candidate",
                        "flags": "ambiguous_year_value_alignment",
                    }
                )
    return standardized_rows, manual_rows, diag_rows


def _extract_pdf_stem_from_asset_package(asset_package: str) -> str:
    name = _norm(asset_package)
    if name.endswith("_资产包"):
        return name[: -len("_资产包")]
    return name


def _load_stage1_manifest_identity(delivery_dir: Path) -> Dict[str, Dict[str, str]]:
    path = delivery_dir / "27_stage1_pdfplumber_selected_samples_manifest.json"
    mapping: Dict[str, Dict[str, str]] = {}
    if not path.exists():
        return mapping
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        items = payload.get("samples", payload if isinstance(payload, list) else [])
        for item in items:
            if not isinstance(item, dict):
                continue
            pdf_path = Path(_norm(item.get("pdf_path") or item.get("pdf")))
            stem = pdf_path.stem
            if not stem:
                continue
            mapping[stem] = {
                "sample_id": _norm(item.get("sample_id")),
                "company": _norm(item.get("company")),
                "pdf_path": str(pdf_path),
            }
    except Exception:
        return {}
    return mapping


def _resolve_sample_identity(asset_dir: Path, manifest_mapping: Dict[str, Dict[str, str]], default_sample_id: str) -> Dict[str, str]:
    asset_package = asset_dir.name
    pdf_stem = _extract_pdf_stem_from_asset_package(asset_package)
    company = ""
    source_method = "folder_name_fallback"
    warning = ""

    summary_files = sorted(asset_dir.glob("stage1_sandbox_asset_summary.xlsx"))
    if summary_files:
        try:
            sdf = pd.read_excel(summary_files[0], engine="openpyxl").fillna("")
            if not sdf.empty:
                pdf_file = _norm(sdf.iloc[0].get("pdf_file"))
                if pdf_file:
                    pdf_stem = Path(pdf_file).stem
                company = _norm(sdf.iloc[0].get("company"))
                source_method = "summary_xlsx"
        except Exception:
            pass

    if source_method == "folder_name_fallback":
        files_02a = sorted(asset_dir.glob("02A_*.xlsx"))
        if files_02a:
            try:
                rdf = pd.read_excel(files_02a[0], sheet_name="raw_tables_index", engine="openpyxl").fillna("")
                if not rdf.empty:
                    pdf_file = _norm(rdf.iloc[0].get("pdf_file"))
                    if pdf_file:
                        pdf_stem = Path(pdf_file).stem
                    company = _norm(rdf.iloc[0].get("company"))
                    source_method = "raw_tables_index"
            except Exception:
                pass

    expected = manifest_mapping.get(pdf_stem, {})
    sample_id = _norm(expected.get("sample_id")) or default_sample_id
    expected_company = _norm(expected.get("company"))
    if expected_company and company and expected_company != company:
        warning = f"company_mismatch:{company}!={expected_company}"
    if not expected:
        warning = (warning + "|manifest_identity_missing").strip("|")

    return {
        "sample_id": sample_id,
        "pdf_stem": pdf_stem,
        "asset_package": asset_package,
        "company": company,
        "expected_company": expected_company,
        "source_identity_method": source_method,
        "identity_warning": warning,
    }


def _run_standardizer_for_sample(asset_dir: Path, default_sample_id: str, manifest_mapping: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    identity = _resolve_sample_identity(asset_dir, manifest_mapping, default_sample_id)
    sample_id = identity["sample_id"]
    result: Dict[str, object] = {
        "sample_id": sample_id,
        "pdf_stem": identity["pdf_stem"],
        "asset_package": identity["asset_package"],
        "company": identity["company"],
        "expected_company": identity["expected_company"],
        "source_identity_method": identity["source_identity_method"],
        "identity_warning": identity["identity_warning"],
        "sample_status": "FAIL",
        "metric_rows": 0,
        "manual_rows": 0,
        "ignored_rows": 0,
        "error": "",
        "standardized_rows": [],
        "manual_review_rows": [],
        "diag_rows": [],
        "generated_files": [],
    }
    files_02a = sorted(asset_dir.glob("02A_*.xlsx"))
    files_02 = [p for p in sorted(asset_dir.glob("02_*.xlsx")) if not p.name.startswith("02A_")]
    files_05 = sorted(asset_dir.glob("05_stage1_core_metric_candidates.xlsx"))
    files_summary = sorted(asset_dir.glob("stage1_sandbox_asset_summary.xlsx"))
    if not files_02a or not files_02 or not files_05 or not files_summary:
        result["sample_status"] = "FAIL"
        result["error"] = "missing_required_trial_assets"
        return result

    try:
        xls = pd.ExcelFile(files_02[0], engine="openpyxl")
    except Exception as exc:
        result["sample_status"] = "FAIL"
        result["error"] = f"read_02_failed:{type(exc).__name__}:{exc}"
        return result

    standardized_rows: List[Dict[str, object]] = []
    manual_rows: List[Dict[str, object]] = []
    diag_rows: List[Dict[str, object]] = []
    sheet_names = [s for s in xls.sheet_names if _norm(s).lower() != "tables_index"]
    for sheet in sheet_names:
        try:
            df = pd.read_excel(files_02[0], sheet_name=sheet, engine="openpyxl").fillna("").astype(str)
        except Exception as exc:
            diag_rows.append(
                {
                    "sample_id": sample_id,
                    "sheet_name": sheet,
                    "diagnostic_type": "sheet_read_failed",
                    "detail": f"{type(exc).__name__}:{exc}",
                }
            )
            continue
        s_rows, m_rows, d_rows = _standardize_table_sheet(
            sample_id=sample_id,
            asset_package=asset_dir.name,
            company=result["company"],
            sheet_name=sheet,
            df=df,
        )
        standardized_rows.extend(s_rows)
        manual_rows.extend(m_rows)
        diag_rows.extend(d_rows)

    result["standardized_rows"] = standardized_rows
    result["manual_review_rows"] = manual_rows
    result["diag_rows"] = diag_rows
    result["metric_rows"] = len(standardized_rows)
    result["manual_rows"] = len(manual_rows)
    result["ignored_rows"] = 0
    risky_count = 0
    risky_tokens = {
        "multi_metric_row_ambiguous",
        "ambiguous_year_value_alignment",
        "ambiguous_multi_numeric_cell",
        "no_year_columns",
        "standardizer_no_metric_candidates",
    }
    for row in manual_rows + standardized_rows:
        f = {x.strip() for x in _norm(row.get("flags")).split("|") if x.strip()}
        if f & risky_tokens:
            risky_count += 1
    result["risky_alignment_rows_count"] = risky_count

    coverage_metrics = { _norm(r.get("standard_metric")) for r in standardized_rows if _norm(r.get("standard_metric")) }
    target_count = len(coverage_metrics)
    if len(standardized_rows) == 0 and len(manual_rows) == 0:
        result["sample_status"] = "WARN_NO_METRICS"
        result["error"] = "STANDARDIZER_NO_METRIC_CANDIDATES"
    elif len(standardized_rows) == 0 and len(manual_rows) > 0:
        result["sample_status"] = "WARN_RISKY_ALIGNMENT"
    elif risky_count >= max(5, len(standardized_rows) // 2):
        result["sample_status"] = "WARN_RISKY_ALIGNMENT"
    elif target_count < 3:
        result["sample_status"] = "PARTIAL"
    else:
        result["sample_status"] = "PASS_SAFE_TRIAL"
    result["target_metric_coverage_count"] = target_count
    return result


def _write_sample_standardizer_outputs(
    trial_std_root: Path,
    sample_result: Dict[str, object],
) -> List[Dict[str, str]]:
    sample_id = _norm(sample_result.get("sample_id")) or "UNKNOWN"
    sample_dir = trial_std_root / sample_id
    sample_dir.mkdir(parents=True, exist_ok=True)
    std_df = pd.DataFrame(sample_result.get("standardized_rows", []))
    manual_df = pd.DataFrame(sample_result.get("manual_review_rows", []))
    diag_df = pd.DataFrame(sample_result.get("diag_rows", []))
    summary_df = pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "asset_package": sample_result.get("asset_package", ""),
                "company": sample_result.get("company", ""),
                "sample_status": sample_result.get("sample_status", ""),
                "metric_rows": sample_result.get("metric_rows", 0),
                "manual_rows": sample_result.get("manual_rows", 0),
                "ignored_rows": sample_result.get("ignored_rows", 0),
                "error": sample_result.get("error", ""),
            }
        ]
    )
    p1 = _safe_write_excel({"standardized_trial_rows": std_df}, sample_dir / "05_stage1_standardized_core_metric_trial.xlsx")
    p2 = _safe_write_excel(
        {"diagnostics": diag_df, "manual_review_candidates": manual_df},
        sample_dir / "05_stage1_standardizer_diagnostics.xlsx",
    )
    p3 = _safe_write_excel({"summary": summary_df}, sample_dir / "stage1_standardizer_trial_summary.xlsx")
    return [
        {"sample_id": sample_id, "file_type": "standardized_trial", "path": str(p1)},
        {"sample_id": sample_id, "file_type": "diagnostics", "path": str(p2)},
        {"sample_id": sample_id, "file_type": "trial_summary", "path": str(p3)},
    ]


def _write_29_30_reports(
    delivery_dir: Path,
    trial_run_root: Path,
    runner_path: Path,
    started_at: str,
    finished_at: str,
    command_run: str,
    files_read: List[str],
    generated_files: List[Dict[str, str]],
    sample_identity_rows: List[Dict[str, object]],
    per_sample_status: List[Dict[str, object]],
    standardized_rows: List[Dict[str, object]],
    manual_rows: List[Dict[str, object]],
    risky_rows: List[Dict[str, object]],
    duplicate_summary: List[Dict[str, object]],
    promoted_likely_rows: List[Dict[str, object]],
    routed_manual_rows: List[Dict[str, object]],
    production_guard_rows: List[Dict[str, str]],
    safety_checks: List[Dict[str, str]],
    production_status_after: Dict[str, str],
) -> Tuple[Path, Path, Path, Path, str]:
    changed_count = sum(1 for r in production_guard_rows if r.get("changed") == "1")
    has_fail = any(_norm(r.get("sample_status")) == "FAIL" for r in per_sample_status)
    has_partial = any(_norm(r.get("sample_status")) == "PARTIAL" for r in per_sample_status)
    has_warn = any(_norm(r.get("sample_status")) == "WARN" for r in per_sample_status)
    if changed_count > 0:
        status = "FAIL"
    elif has_fail and len(per_sample_status) == sum(1 for r in per_sample_status if _norm(r.get("sample_status")) == "FAIL"):
        status = "FAIL"
    elif has_fail or has_partial:
        status = "PARTIAL"
    elif has_warn:
        status = "WARN"
    else:
        status = "PASS"

    per_sample_metric_rows = []
    for r in per_sample_status:
        per_sample_metric_rows.append(
            {
                "sample_id": r.get("sample_id", ""),
                "sample_status": r.get("sample_status", ""),
                "metric_rows": r.get("metric_rows", 0),
                "manual_review_candidate_rows": r.get("manual_rows", 0),
                "ignored_rows": r.get("ignored_rows", 0),
                "error": r.get("error", ""),
            }
        )

    flags_counter: Dict[str, int] = {}
    for row in standardized_rows + manual_rows:
        for f in [x.strip() for x in _norm(row.get("flags")).split("|") if x.strip()]:
            flags_counter[f] = flags_counter.get(f, 0) + 1
    flags_summary = [{"flag": k, "count": v} for k, v in sorted(flags_counter.items(), key=lambda x: (-x[1], x[0]))]

    coverage: Dict[str, Dict[str, int]] = {}
    for row in standardized_rows:
        metric = _norm(row.get("standard_metric"))
        sid = _norm(row.get("sample_id"))
        if not metric:
            continue
        if metric not in coverage:
            coverage[metric] = {"row_count": 0, "sample_count": 0}
        coverage[metric]["row_count"] += 1
        coverage[metric].setdefault(f"sample::{sid}", 1)
    coverage_rows = []
    for metric, payload in coverage.items():
        sample_count = len([k for k in payload.keys() if k.startswith("sample::")])
        coverage_rows.append({"standard_metric": metric, "row_count": payload["row_count"], "sample_count": sample_count})

    blockers = []
    if changed_count > 0:
        blockers.append("production_guard_changed")
    if not standardized_rows:
        blockers.append("no_standardized_rows")
    ready_samples = [r["sample_id"] for r in per_sample_metric_rows if int(r.get("metric_rows", 0) or 0) > 0]

    report29_md = _safe_write_text(
        delivery_dir / "31_stage1_standardizer_alignment_fix_log.md",
        "\n".join(
            [
                "# Stage1 Standardizer Alignment Fix Log",
                "",
                "- task_title: Harden Stage 1 sandbox standardizer alignment",
                f"- runner_path: {runner_path}",
                f"- started_at: {started_at}",
                f"- finished_at: {finished_at}",
                f"- trial_run_root: {trial_run_root}",
                f"- command_run: {command_run}",
                f"- production_guard_changed_count: {changed_count}",
                f"- sandbox_standardizer_status: {status}",
            ]
        ),
    )
    report29_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Harden Stage 1 sandbox standardizer alignment"},
                    {"field": "runner_path", "value": str(runner_path)},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": finished_at},
                    {"field": "trial_run_root", "value": str(trial_run_root)},
                    {"field": "command_run", "value": command_run},
                    {"field": "sandbox_standardizer_status", "value": status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "files_read": pd.DataFrame([{"path": p} for p in files_read]),
            "files_generated": pd.DataFrame(generated_files),
            "sample_identity_mapping": pd.DataFrame(sample_identity_rows),
            "per_sample_trial_standardizer_status": pd.DataFrame(per_sample_status),
            "alignment_fix_summary": pd.DataFrame(
                [
                    {
                        "risky_alignment_rows_count": len(risky_rows),
                        "duplicate_metric_year_groups": len(duplicate_summary),
                        "rows_promoted_to_likely_core_metric_trial": len(promoted_likely_rows),
                        "rows_routed_to_manual_review_candidate": len(routed_manual_rows),
                    }
                ]
            ),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
        },
        delivery_dir / "31_stage1_standardizer_alignment_fix_log.xlsx",
    )

    report30_md = _safe_write_text(
        delivery_dir / "32_stage1_standardizer_alignment_fix_evaluation.md",
        "\n".join(
            [
                "# Stage1 Standardizer Alignment Fix Evaluation",
                "",
                f"- sandbox_standardizer_status: {status}",
                f"- production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}",
                f"- sample_identity_mapping: {json.dumps(sample_identity_rows, ensure_ascii=False)}",
                f"- risky_alignment_rows_count: {len(risky_rows)}",
                f"- duplicate_metric_year_summary_count: {len(duplicate_summary)}",
                f"- samples_ready_for_sandbox_delivery_trial: {','.join(ready_samples)}",
                f"- blockers: {'|'.join(blockers) if blockers else 'none'}",
            ]
        ),
    )
    report30_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "sandbox_standardizer_status", "value": status},
                    {"field": "production_delivery_status_after", "value": json.dumps(production_status_after, ensure_ascii=False)},
                    {"field": "risky_alignment_rows_count", "value": len(risky_rows)},
                    {"field": "duplicate_metric_year_groups", "value": len(duplicate_summary)},
                    {"field": "rows_promoted_to_likely_core_metric_trial", "value": len(promoted_likely_rows)},
                    {"field": "rows_routed_to_manual_review_candidate", "value": len(routed_manual_rows)},
                    {"field": "samples_ready_for_sandbox_delivery_trial", "value": "|".join(ready_samples)},
                    {"field": "blockers", "value": "|".join(blockers)},
                ]
            ),
            "sample_identity_mapping": pd.DataFrame(sample_identity_rows),
            "per_sample_status": pd.DataFrame(per_sample_metric_rows),
            "standardized_trial_rows": pd.DataFrame(standardized_rows),
            "manual_review_candidates": pd.DataFrame(manual_rows),
            "risky_alignment_rows": pd.DataFrame(risky_rows),
            "duplicate_metric_year_summary": pd.DataFrame(duplicate_summary),
            "flags_summary": pd.DataFrame(flags_summary),
            "target_metric_coverage": pd.DataFrame(coverage_rows),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Review risky/manual rows first; only then proceed to sandbox delivery trial for ready samples.",
                    }
                ]
            ),
        },
        delivery_dir / "32_stage1_standardizer_alignment_fix_evaluation.xlsx",
    )
    return report29_md, report29_xlsx, report30_md, report30_xlsx, status


def _run_standardize_sandbox_mode(args: argparse.Namespace, runner_path: Path) -> int:
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    if args.strict_scope and not _ensure_under(DEFAULT_TRIAL_ROOT, trial_run_root):
        print("BLOCKED_STRICT_SCOPE: trial-run-root must be under output/_stage1_safe_runner_trial")
        return 3
    assets_root = trial_run_root / "assets"
    if not assets_root.exists():
        print(f"BLOCKED_TRIAL_ASSETS_MISSING: {assets_root}")
        return 3

    before = _snapshot_files(_collect_production_guard_files(DEFAULT_DELIVERY_DIR))
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files_read: List[str] = []
    generated_files: List[Dict[str, str]] = []
    per_sample_status: List[Dict[str, object]] = []
    sample_identity_rows: List[Dict[str, object]] = []
    standardized_all: List[Dict[str, object]] = []
    manual_all: List[Dict[str, object]] = []

    trial_std_root = trial_run_root / "standardizer_trial"
    trial_std_root.mkdir(parents=True, exist_ok=True)

    manifest_mapping = _load_stage1_manifest_identity(delivery_dir)
    sample_dirs = sorted([p for p in assets_root.iterdir() if p.is_dir()])
    for idx, sample_dir in enumerate(sample_dirs, start=1):
        sample_id = f"S{idx}"
        files_read.extend([str(x) for x in sample_dir.glob("*.xlsx")])
        res = _run_standardizer_for_sample(sample_dir, default_sample_id=sample_id, manifest_mapping=manifest_mapping)
        sample_identity_rows.append(
            {
                "sample_id": res.get("sample_id", ""),
                "pdf_stem": res.get("pdf_stem", ""),
                "asset_package": res.get("asset_package", ""),
                "company": res.get("company", ""),
                "expected_company": res.get("expected_company", ""),
                "source_identity_method": res.get("source_identity_method", ""),
                "identity_warning": res.get("identity_warning", ""),
            }
        )
        per_sample_status.append(
            {
                "sample_id": res.get("sample_id", sample_id),
                "asset_package": res.get("asset_package", ""),
                "company": res.get("company", ""),
                "pdf_stem": res.get("pdf_stem", ""),
                "sample_status": res.get("sample_status", ""),
                "metric_rows": res.get("metric_rows", 0),
                "manual_rows": res.get("manual_rows", 0),
                "ignored_rows": res.get("ignored_rows", 0),
                "risky_alignment_rows_count": res.get("risky_alignment_rows_count", 0),
                "target_metric_coverage_count": res.get("target_metric_coverage_count", 0),
                "error": res.get("error", ""),
            }
        )
        standardized_rows = res.get("standardized_rows", [])
        manual_rows = res.get("manual_review_rows", [])
        if isinstance(standardized_rows, list):
            standardized_all.extend(standardized_rows)
        if isinstance(manual_rows, list):
            manual_all.extend(manual_rows)
        generated_files.extend(_write_sample_standardizer_outputs(trial_std_root, res))

    dup_map: Dict[Tuple[str, str, str], Dict[str, object]] = {}
    for row in standardized_all:
        key = (_norm(row.get("sample_id")), _norm(row.get("standard_metric")), _norm(row.get("year")))
        if not key[0] or not key[1] or not key[2]:
            continue
        if key not in dup_map:
            dup_map[key] = {"count": 0, "tables": set()}
        dup_map[key]["count"] += 1
        dup_map[key]["tables"].add(f"{_norm(row.get('source_page'))}:{_norm(row.get('source_table_index'))}")
    duplicate_summary = []
    duplicate_keys = {k for k, v in dup_map.items() if int(v["count"]) > 1}
    for key, payload in dup_map.items():
        if key not in duplicate_keys:
            continue
        sample_id, metric, year = key
        duplicate_summary.append(
            {
                "sample_id": sample_id,
                "standard_metric": metric,
                "year": year,
                "duplicate_count": int(payload["count"]),
                "source_table_count": len(payload["tables"]),
                "source_tables": "|".join(sorted(payload["tables"])),
            }
        )
    for row in standardized_all:
        key = (_norm(row.get("sample_id")), _norm(row.get("standard_metric")), _norm(row.get("year")))
        if key in duplicate_keys:
            existing_flags = [x for x in _norm(row.get("flags")).split("|") if x]
            if "duplicate_metric_year_in_sample" not in existing_flags:
                existing_flags.append("duplicate_metric_year_in_sample")
            if len(dup_map[key]["tables"]) > 1 and "multiple_source_tables_for_metric_year" not in existing_flags:
                existing_flags.append("multiple_source_tables_for_metric_year")
            row["flags"] = "|".join(existing_flags)

    risky_tokens = {
        "multi_metric_row_ambiguous",
        "ambiguous_year_value_alignment",
        "ambiguous_multi_numeric_cell",
        "no_year_columns",
        "standardizer_no_metric_candidates",
    }
    risky_rows = []
    promoted_likely_rows = []
    routed_manual_rows = []
    for row in standardized_all + manual_all:
        flags = {x.strip() for x in _norm(row.get("flags")).split("|") if x.strip()}
        if flags & risky_tokens:
            risky_rows.append(row)
        route = _norm(row.get("route_recommendation"))
        if route == "likely_core_metric_trial":
            promoted_likely_rows.append(row)
        if route == "manual_review_candidate":
            routed_manual_rows.append(row)

    after = _snapshot_files(_collect_production_guard_files(DEFAULT_DELIVERY_DIR))
    production_guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in production_guard_rows if r.get("changed") == "1")
    production_status_after = _run_delivery_check_json(DEFAULT_DELIVERY_DIR, no_write=False)
    finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safety_checks = [
        {"check_name": "factory_core_not_run", "status": "PASS", "detail": "standardizer mode reads trial xlsx only"},
        {"check_name": "vision_backends_not_triggered", "status": "PASS", "detail": "no vision/OCR code paths"},
        {"check_name": "model_download_not_triggered", "status": "PASS", "detail": "no model backend imports"},
        {"check_name": "production_files_unchanged", "status": "PASS" if changed_count == 0 else "FAIL", "detail": f"changed={changed_count}"},
    ]

    command_run = " ".join([sys.executable, str(runner_path)] + sys.argv[1:])
    r29m, r29x, r30m, r30x, status = _write_29_30_reports(
        delivery_dir=delivery_dir,
        trial_run_root=trial_run_root,
        runner_path=runner_path,
        started_at=started_at,
        finished_at=finished_at,
        command_run=command_run,
        files_read=files_read,
        generated_files=generated_files,
        sample_identity_rows=sample_identity_rows,
        per_sample_status=per_sample_status,
        standardized_rows=standardized_all,
        manual_rows=manual_all,
        risky_rows=risky_rows,
        duplicate_summary=duplicate_summary,
        promoted_likely_rows=promoted_likely_rows,
        routed_manual_rows=routed_manual_rows,
        production_guard_rows=production_guard_rows,
        safety_checks=safety_checks,
        production_status_after=production_status_after,
    )
    print(f"runner_path: {runner_path}")
    print(f"sandbox_standardizer_status: {status}")
    print(f"trial_run_root: {trial_run_root}")
    print(f"report_31_md: {r29m}")
    print(f"report_31_xlsx: {r29x}")
    print(f"report_32_md: {r30m}")
    print(f"report_32_xlsx: {r30x}")
    print(f"production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}")
    print(f"production_guard_changed_count: {changed_count}")
    print(f"sample_identity_mapping: {json.dumps(sample_identity_rows, ensure_ascii=False)}")
    print(f"per_sample_metric_rows: {json.dumps([{ 'sample_id': r.get('sample_id'), 'metric_rows': r.get('metric_rows', 0)} for r in per_sample_status], ensure_ascii=False)}")
    print(f"risky_alignment_rows_count: {len(risky_rows)}")
    print(f"duplicate_metric_year_summary: {json.dumps(duplicate_summary, ensure_ascii=False)}")
    if changed_count > 0:
        return 5
    return 0 if status in {"PASS", "WARN", "PARTIAL"} else 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scoped safe non-vision Stage 1 runner.")
    parser.add_argument("--manifest", type=str, default="")
    parser.add_argument("--pdf", action="append", default=[])
    parser.add_argument("--output-root", type=str, default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--delivery-dir", type=str, default=str(DEFAULT_DELIVERY_DIR))
    parser.add_argument("--trial-root", type=str, default=str(DEFAULT_TRIAL_ROOT))
    parser.add_argument("--sandbox-delivery-dir", type=str, default=str(DEFAULT_SANDBOX_DELIVERY_DIR))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--execute-sandbox", action="store_true")
    parser.add_argument("--strict-scope", action="store_true")
    parser.add_argument("--no-vision", action="store_true", default=True)
    parser.add_argument("--pdfplumber-only", action="store_true", default=True)
    parser.add_argument("--allow-production-write", action="store_true")
    parser.add_argument("--allow-baseline", action="store_true")
    parser.add_argument("--standardize-sandbox", action="store_true")
    parser.add_argument("--trial-run-root", type=str, default="")
    return parser


def _run_dry_mode(
    args: argparse.Namespace,
    runner_path: Path,
    source_rows: List[Dict[str, str]],
    sample_rows: List[Dict[str, str]],
    sample_errors: List[Dict[str, str]],
    safe_rows: List[Dict[str, str]],
    unsafe_rows: List[Dict[str, str]],
) -> int:
    status = "DRY_RUN_READY"
    if sample_errors:
        status = "DRY_RUN_BLOCKED_INPUT_VALIDATION_FAILED"
    else:
        status = "DRY_RUN_BLOCKED_NO_SAFE_FULL_PIPELINE"
        sample_errors = [{"sample_id": "", "error_code": "BLOCKED_NO_SAFE_FULL_PIPELINE", "detail": "execute sandbox required"}]
    r23m, r23x, r24m, r24x = _write_23_24_reports(
        delivery_dir=Path(args.delivery_dir),
        runner_path=runner_path,
        source_rows=source_rows,
        sample_rows=sample_rows,
        safe_rows=safe_rows,
        unsafe_rows=unsafe_rows,
        errors=sample_errors,
        status=status,
    )
    print(f"runner_path: {runner_path}")
    print(f"dry_run_status: {status}")
    print(f"report_23_md: {r23m}")
    print(f"report_23_xlsx: {r23x}")
    print(f"report_24_md: {r24m}")
    print(f"report_24_xlsx: {r24x}")
    return 0 if status == "DRY_RUN_READY" else 2


def _run_execute_sandbox_mode(
    args: argparse.Namespace,
    runner_path: Path,
    manifest_path: Path,
    resolved_samples: List[SampleItem],
    sample_rows: List[Dict[str, str]],
    sample_errors: List[Dict[str, str]],
) -> int:
    if not args.execute_sandbox and not args.allow_production_write:
        print("BLOCKED_EXECUTE_REQUIRES_SANDBOX: use --execute-sandbox for this task.")
        return 3
    if args.allow_production_write:
        print("BLOCKED_PRODUCTION_WRITE_NOT_ALLOWED: --allow-production-write is forbidden in this task.")
        return 3
    if not args.pdfplumber_only:
        print("BLOCKED_UNSAFE_ARGS: pdfplumber-only mode must stay enabled.")
        return 3

    trial_root = Path(args.trial_root)
    sandbox_delivery_dir = Path(args.sandbox_delivery_dir)
    output_root = Path(args.output_root)
    delivery_dir = Path(args.delivery_dir)
    if not _ensure_under(DEFAULT_TRIAL_ROOT, trial_root):
        print("BLOCKED_TRIAL_ROOT_SCOPE: trial-root must remain under output/_stage1_safe_runner_trial")
        return 3

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    trial_run_dir = trial_root / f"run_{ts}"
    trial_assets_root = trial_run_dir / "assets"
    trial_assets_root.mkdir(parents=True, exist_ok=True)
    sandbox_delivery_dir.mkdir(parents=True, exist_ok=True)

    guard_files = _collect_production_guard_files(DEFAULT_DELIVERY_DIR)
    before = _snapshot_files(guard_files)

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    per_sample_status_rows = []
    tables_extracted_rows = []
    metric_candidates_rows: List[Dict[str, object]] = []
    generated_file_rows: List[Dict[str, object]] = []
    safety_checks_rows = [
        {"check_name": "factory_core_not_run", "status": "PASS", "detail": "runner does not invoke factory_core.py"},
        {"check_name": "vision_backends_not_triggered", "status": "PASS", "detail": "--no-vision + pdfplumber-only guard"},
        {"check_name": "model_download_not_triggered", "status": "PASS", "detail": "no model backend imports"},
        {"check_name": "strict_scope", "status": "PASS" if args.strict_scope else "WARN", "detail": f"strict_scope={args.strict_scope}"},
        {"check_name": "trial_root", "status": "PASS", "detail": str(trial_root)},
    ]

    if sample_errors:
        for e in sample_errors:
            per_sample_status_rows.append(
                {
                    "sample_id": e.get("sample_id", ""),
                    "company": "",
                    "pdf_file": "",
                    "approved_pages": "",
                    "pages_processed": 0,
                    "tables_extracted": 0,
                    "candidate_tables": 0,
                    "metric_candidate_rows": 0,
                    "extraction_errors": 1,
                    "sample_status": "FAIL",
                    "error_detail": f"{e.get('error_code')}: {e.get('detail')}",
                }
            )
    else:
        for sample in resolved_samples:
            result = _extract_with_pdfplumber(sample, trial_assets_root / f"{sample.pdf_path.stem}_资产包")
            files = _write_sample_assets(sample, trial_assets_root, result)
            for k, v in files.items():
                generated_file_rows.append({"sample_id": sample.sample_id, "file_type": k, "path": v})
            metric_candidates_rows.extend(result.get("candidate_rows", []))
            tables_extracted_rows.extend(result.get("raw_tables_index", []))
            per_sample_status_rows.append(
                {
                    "sample_id": sample.sample_id,
                    "company": sample.company,
                    "pdf_file": sample.pdf_path.name,
                    "approved_pages": ",".join(str(x) for x in sample.approved_pages),
                    "pages_processed": result.get("pages_processed", 0),
                    "tables_extracted": result.get("tables_extracted", 0),
                    "candidate_tables": result.get("candidate_tables", 0),
                    "metric_candidate_rows": result.get("metric_candidate_rows", 0),
                    "extraction_errors": result.get("extraction_errors", 0),
                    "sample_status": result.get("sample_status", "FAIL"),
                    "error_detail": result.get("error", ""),
                }
            )

    inv_md, inv_xlsx = _write_trial_inventory(trial_run_dir, per_sample_status_rows, generated_file_rows)
    generated_file_rows.append({"sample_id": "ALL", "file_type": "trial_inventory_md", "path": str(inv_md)})
    generated_file_rows.append({"sample_id": "ALL", "file_type": "trial_inventory_xlsx", "path": str(inv_xlsx)})

    after = _snapshot_files(guard_files)
    guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in guard_rows if r["changed"] == "1")
    production_status_after = _run_delivery_check_json(DEFAULT_DELIVERY_DIR, no_write=False)
    finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    command_run = " ".join([sys.executable, str(runner_path)] + sys.argv[1:])
    report27_md, report27_xlsx, report28_md, report28_xlsx, build_status = _write_27_28_reports(
        delivery_dir=delivery_dir,
        task_title="Implement pdfplumber-only sandbox asset builder for Stage 1",
        runner_path=runner_path,
        started_at=started_at,
        finished_at=finished_at,
        command_run=command_run,
        manifest_path=manifest_path,
        trial_run_root=trial_run_dir,
        per_sample_status_rows=per_sample_status_rows,
        tables_extracted_rows=tables_extracted_rows,
        metric_candidates_rows=metric_candidates_rows,
        generated_file_rows=generated_file_rows,
        production_guard_rows=guard_rows,
        safety_checks_rows=safety_checks_rows,
        production_status_after=production_status_after,
    )

    print(f"runner_path: {runner_path}")
    print(f"sandbox_asset_build_status: {build_status}")
    print(f"trial_run_root: {trial_run_dir}")
    print(f"report_27_md: {report27_md}")
    print(f"report_27_xlsx: {report27_xlsx}")
    print(f"report_28_md: {report28_md}")
    print(f"report_28_xlsx: {report28_xlsx}")
    print(f"production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}")
    print(f"production_guard_changed_count: {changed_count}")
    print(f"samples_processed: {len(per_sample_status_rows)}")

    if changed_count > 0:
        return 5
    return 0 if build_status in {"PASS", "WARN", "PARTIAL"} else 4


def main() -> int:
    args = build_parser().parse_args()
    runner_path = Path(__file__).resolve()
    if args.standardize_sandbox:
        if args.dry_run or args.execute:
            print("BLOCKED_INVALID_ARGS: --standardize-sandbox cannot be combined with --dry-run/--execute.")
            return 2
        if not args.no_vision:
            print("BLOCKED_UNSAFE_ARGS: --no-vision must stay enabled.")
            return 2
        if not _norm(args.trial_run_root):
            print("BLOCKED_INVALID_ARGS: --trial-run-root is required for --standardize-sandbox.")
            return 2
        return _run_standardize_sandbox_mode(args, runner_path)

    if args.dry_run and args.execute:
        print("BLOCKED_INVALID_ARGS: --dry-run and --execute cannot both be set.")
        return 2
    if not args.dry_run and not args.execute:
        print("BLOCKED_INVALID_ARGS: one of --dry-run or --execute is required.")
        return 2
    if not args.no_vision:
        print("BLOCKED_UNSAFE_ARGS: --no-vision must stay enabled.")
        return 2

    manifest = Path(args.manifest) if _norm(args.manifest) else None
    try:
        samples, source_rows, manifest_path = _load_samples(manifest, args.pdf)
    except Exception as exc:
        print(f"BLOCKED_INVALID_INPUT: {exc}")
        return 2

    sample_rows, sample_errors, resolved_samples = _validate_samples(samples, args.strict_scope, args.allow_baseline)
    safe_rows, unsafe_rows = _discover_safe_entrypoints()

    if args.dry_run:
        return _run_dry_mode(args, runner_path, source_rows, sample_rows, sample_errors, safe_rows, unsafe_rows)
    return _run_execute_sandbox_mode(args, runner_path, manifest_path, resolved_samples, sample_rows, sample_errors)


if __name__ == "__main__":
    raise SystemExit(main())
