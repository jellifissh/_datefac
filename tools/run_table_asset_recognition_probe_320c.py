from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.parser.mineru_output_reader import read_mineru_output
from datefac.recognition.table_image_recognizer import build_recognizer


ROLE_PRIORITY = {
    "CORE_METRIC_TABLE": 1,
    "FINANCIAL_FORECAST_VALUATION": 2,
    "BALANCE_SHEET": 3,
    "INCOME_STATEMENT": 4,
    "CASH_FLOW_STATEMENT": 5,
    "BUSINESS_ASSUMPTION": 6,
}
DEFAULT_ROLES = list(ROLE_PRIORITY.keys())


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    s = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
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
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _json_dump(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _json_safe_value(v: Any) -> Any:
    if isinstance(v, (list, dict, bool, int, float, str)) or v is None:
        return v
    try:
        if pd.isna(v):  # type: ignore[arg-type]
            return None
    except Exception:
        pass
    return _norm(v)


def _load_assets(mineru_output_root: Path, max_reports: int) -> List[Dict[str, Any]]:
    report_dirs = sorted([p for p in mineru_output_root.iterdir() if p.is_dir()])[:max_reports]
    rows: List[Dict[str, Any]] = []
    for rd in report_dirs:
        res = read_mineru_output(rd)
        warning_count = len(res.warnings)
        for a in res.table_assets:
            ad = a.to_dict()
            extra = ad.get("extra", {}) if isinstance(ad.get("extra"), dict) else {}
            rows.append(
                {
                    "report_name": rd.name,
                    "mineru_output_dir": str(rd),
                    "table_asset_id": f"{rd.name}__{_norm(ad.get('source_doc_id'))}__{ad.get('block_index')}",
                    "source_doc_name": _norm(ad.get("source_doc_id")) or rd.name,
                    "table_role_guess": _norm(extra.get("role_category") or ad.get("table_role_guess")),
                    "table_role_reason": _norm(ad.get("table_role_reason")),
                    "image_path": _norm(extra.get("image_path_resolved") or ad.get("image_path")),
                    "image_exists": bool(extra.get("image_exists", False)),
                    "image_path_raw": _norm(extra.get("image_path_raw")),
                    "warning_count_report": warning_count,
                    "source_file": _norm(ad.get("source_file")),
                    "page_idx": ad.get("page_idx"),
                    "bbox": ad.get("bbox"),
                    "caption": _norm(ad.get("caption")),
                    "nearby_text": _norm(ad.get("nearby_text")),
                }
            )
    return rows


def _select_assets(rows: List[Dict[str, Any]], allowed_roles: List[str], max_tables: int) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
    selected_candidates: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    allowed_set = set(allowed_roles)

    for r in rows:
        role = _norm(r.get("table_role_guess"))
        if role not in allowed_set:
            x = dict(r)
            x["skip_reason"] = "SKIPPED_BY_ROLE"
            skipped.append(x)
            continue
        selected_candidates.append(r)

    selected_candidates.sort(
        key=lambda x: (
            ROLE_PRIORITY.get(_norm(x.get("table_role_guess")), 999),
            0 if bool(x.get("image_exists", False)) else 1,
            int(x.get("warning_count_report", 0)),
        )
    )

    selected: List[Dict[str, Any]] = []
    for i, r in enumerate(selected_candidates):
        if i >= max_tables:
            x = dict(r)
            x["skip_reason"] = "SKIPPED_BY_LIMIT"
            skipped.append(x)
            continue
        selected.append(r)

    return selected, skipped


def run_probe(
    mineru_output_root: Path,
    output_dir: Path,
    max_reports: int,
    max_tables: int,
    roles: List[str],
    recognizer_mode: str,
    dry_run_selection_only: bool,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    all_assets = _load_assets(mineru_output_root, max_reports=max_reports)
    selected, skipped = _select_assets(all_assets, allowed_roles=roles, max_tables=max_tables)

    recognizer = build_recognizer(recognizer_mode)
    recognizer_available = recognizer.is_available()

    extracted_rows: List[Dict[str, Any]] = []
    extracted_cells_rows: List[Dict[str, Any]] = []
    raw_text_preview_rows: List[Dict[str, Any]] = []
    warnings_rows: List[Dict[str, Any]] = []

    for row in selected:
        if not row.get("image_exists", False):
            extracted_rows.append(
                {
                    "extracted_table_id": f"{row['table_asset_id']}__missing",
                    "table_asset_id": row["table_asset_id"],
                    "source_doc_name": row["source_doc_name"],
                    "table_role_guess": row["table_role_guess"],
                    "image_path": row["image_path"],
                    "recognizer_name": recognizer.name,
                    "recognizer_version": recognizer.version,
                    "recognition_status": "IMAGE_MISSING",
                    "row_count": 0,
                    "col_count": 0,
                    "cell_count": 0,
                    "non_empty_cell_count": 0,
                    "raw_text": "",
                    "warnings": "image missing",
                }
            )
            warnings_rows.append(
                {
                    "table_asset_id": row["table_asset_id"],
                    "warning_code": "IMAGE_MISSING",
                    "warning_message": "selected asset image missing",
                }
            )
            continue

        if dry_run_selection_only:
            status = "SKIPPED_BY_LIMIT" if False else "RECOGNIZER_UNAVAILABLE"
            extracted_rows.append(
                {
                    "extracted_table_id": f"{row['table_asset_id']}__dryrun",
                    "table_asset_id": row["table_asset_id"],
                    "source_doc_name": row["source_doc_name"],
                    "table_role_guess": row["table_role_guess"],
                    "image_path": row["image_path"],
                    "recognizer_name": recognizer.name,
                    "recognizer_version": recognizer.version,
                    "recognition_status": status,
                    "row_count": 0,
                    "col_count": 0,
                    "cell_count": 0,
                    "non_empty_cell_count": 0,
                    "raw_text": "",
                    "warnings": "dry run selection only",
                }
            )
            continue

        et = recognizer.recognize(
            image_path=row["image_path"],
            table_asset_id=row["table_asset_id"],
            source_doc_name=row["source_doc_name"],
            table_role_guess=row["table_role_guess"],
        )
        ed = et.to_dict()
        extracted_rows.append(
            {
                "extracted_table_id": ed["extracted_table_id"],
                "table_asset_id": ed["table_asset_id"],
                "source_doc_name": ed["source_doc_name"],
                "table_role_guess": ed["table_role_guess"],
                "image_path": ed["image_path"],
                "recognizer_name": ed["recognizer_name"],
                "recognizer_version": ed["recognizer_version"],
                "recognition_status": ed["recognition_status"],
                "row_count": ed["row_count"],
                "col_count": ed["col_count"],
                "cell_count": ed["cell_count"],
                "non_empty_cell_count": ed["non_empty_cell_count"],
                "raw_text": ed["raw_text"],
                "warnings": "|".join(ed.get("warnings", [])),
            }
        )
        raw_text_preview_rows.append(
            {
                "table_asset_id": ed["table_asset_id"],
                "recognition_status": ed["recognition_status"],
                "raw_text_preview": _norm(ed["raw_text"])[:800],
            }
        )
        for c in ed.get("cells", []):
            extracted_cells_rows.append(
                {
                    "table_asset_id": ed["table_asset_id"],
                    "extracted_table_id": ed["extracted_table_id"],
                    "row": c.get("row"),
                    "col": c.get("col"),
                    "text": _norm(c.get("text")),
                }
            )
        for w in ed.get("warnings", []):
            warnings_rows.append(
                {
                    "table_asset_id": ed["table_asset_id"],
                    "warning_code": "RECOGNIZER_WARNING",
                    "warning_message": _norm(w),
                }
            )

    selected_df = pd.DataFrame(selected)
    skipped_df = pd.DataFrame(skipped)
    extracted_df = pd.DataFrame(extracted_rows)
    cells_df = pd.DataFrame(extracted_cells_rows)
    text_df = pd.DataFrame(raw_text_preview_rows)
    warnings_df = pd.DataFrame(warnings_rows)

    if selected_df.empty:
        selected_df = pd.DataFrame(columns=["report_name", "table_asset_id", "table_role_guess", "image_path", "image_exists", "caption", "nearby_text"])
    if skipped_df.empty:
        skipped_df = pd.DataFrame(columns=["table_asset_id", "skip_reason", "table_role_guess"])
    if extracted_df.empty:
        extracted_df = pd.DataFrame(columns=["extracted_table_id", "table_asset_id", "recognition_status", "row_count", "col_count", "cell_count", "non_empty_cell_count", "raw_text"])
    if cells_df.empty:
        cells_df = pd.DataFrame(columns=["table_asset_id", "extracted_table_id", "row", "col", "text"])
    if text_df.empty:
        text_df = pd.DataFrame(columns=["table_asset_id", "recognition_status", "raw_text_preview"])
    if warnings_df.empty:
        warnings_df = pd.DataFrame(columns=["table_asset_id", "warning_code", "warning_message"])

    status_counts = (
        extracted_df.groupby("recognition_status", dropna=False).size().reset_index(name="count").sort_values("count", ascending=False)
        if not extracted_df.empty
        else pd.DataFrame(columns=["recognition_status", "count"])
    )

    recognized_grid_count = int((extracted_df["recognition_status"] == "RECOGNIZED_GRID").sum()) if not extracted_df.empty else 0
    recognized_text_only_count = int((extracted_df["recognition_status"] == "RECOGNIZED_TEXT_ONLY").sum()) if not extracted_df.empty else 0
    recognizer_unavailable_count = int((extracted_df["recognition_status"] == "RECOGNIZER_UNAVAILABLE").sum()) if not extracted_df.empty else 0
    image_missing_count = int((extracted_df["recognition_status"] == "IMAGE_MISSING").sum()) if not extracted_df.empty else 0
    failed_count = int((extracted_df["recognition_status"] == "FAILED").sum()) if not extracted_df.empty else 0
    avg_non_empty = float(extracted_df["non_empty_cell_count"].mean()) if not extracted_df.empty else 0.0

    if len(selected_df) > 0 and recognized_grid_count >= 3:
        decision = "TABLE_RECOGNITION_PROBE_READY_FOR_320D_METRIC_CANDIDATE_MAPPING"
    elif not recognizer_available:
        decision = "BLOCKED_RECOGNIZER_UNAVAILABLE_CHOOSE_LOCAL_OCR_OR_VLM_NEXT"
    elif recognized_text_only_count > 0 and recognized_grid_count == 0:
        decision = "TEXT_ONLY_RECOGNITION_NEEDS_TABLE_STRUCTURE_ENGINE"
    else:
        decision = "NEED_RECOGNIZER_CALIBRATION"

    summary_payload = {
        "report_count_scanned": int(len(set(selected_df["report_name"].tolist() + skipped_df.get("report_name", pd.Series([], dtype=object)).tolist()))) if (not selected_df.empty or not skipped_df.empty) else 0,
        "table_asset_count_scanned": int(len(all_assets)),
        "selected_table_asset_count": int(len(selected_df)),
        "recognizer_name": recognizer.name,
        "recognizer_available": bool(recognizer_available),
        "recognized_grid_count": recognized_grid_count,
        "recognized_text_only_count": recognized_text_only_count,
        "recognizer_unavailable_count": recognizer_unavailable_count,
        "image_missing_count": image_missing_count,
        "failed_count": failed_count,
        "avg_non_empty_cell_count": round(avg_non_empty, 6),
        "recognition_probe_decision": decision,
    }

    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary_payload.items()])

    out_excel = output_dir / "table_asset_recognition_320c.xlsx"
    _write_excel(
        out_excel,
        {
            "summary": summary_df,
            "selected_table_assets": selected_df,
            "extracted_tables": extracted_df,
            "extracted_cells": cells_df,
            "raw_text_preview": text_df,
            "warnings": warnings_df,
            "recognizer_status_counts": status_counts,
            "skipped_assets": skipped_df,
        },
    )

    out_summary = output_dir / "table_asset_recognition_320c_summary.json"
    _json_dump(out_summary, summary_payload)

    out_report = output_dir / "table_asset_recognition_320c_report.md"
    report_lines = [
        "# 320C TableAsset Recognition Probe",
        "",
        f"- mineru_output_root: `{mineru_output_root}`",
        f"- selected_table_asset_count: {summary_payload['selected_table_asset_count']}",
        f"- recognizer_name: {summary_payload['recognizer_name']}",
        f"- recognizer_available: {summary_payload['recognizer_available']}",
        f"- recognized_grid_count: {summary_payload['recognized_grid_count']}",
        f"- recognized_text_only_count: {summary_payload['recognized_text_only_count']}",
        f"- recognizer_unavailable_count: {summary_payload['recognizer_unavailable_count']}",
        f"- recognition_probe_decision: {summary_payload['recognition_probe_decision']}",
        "",
        "## Output",
        f"- excel: `{out_excel}`",
        f"- summary_json: `{out_summary}`",
        f"- report_md: `{out_report}`",
    ]
    out_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    # optional jsonl
    with (output_dir / "selected_table_assets.jsonl").open("w", encoding="utf-8") as f:
        for _, r in selected_df.iterrows():
            f.write(json.dumps({k: _json_safe_value(v) for k, v in r.to_dict().items()}, ensure_ascii=False) + "\n")
    with (output_dir / "extracted_tables.jsonl").open("w", encoding="utf-8") as f:
        for _, r in extracted_df.iterrows():
            f.write(json.dumps({k: _json_safe_value(v) for k, v in r.to_dict().items()}, ensure_ascii=False) + "\n")

    return {
        "excel_path": str(out_excel),
        "summary_json_path": str(out_summary),
        "report_md_path": str(out_report),
        "summary": summary_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 320C table asset recognition probe.")
    parser.add_argument("--mineru-output-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-reports", type=int, default=3)
    parser.add_argument("--max-tables", type=int, default=20)
    parser.add_argument("--roles", default=",".join(DEFAULT_ROLES))
    parser.add_argument("--recognizer", default="auto", choices=["auto", "paddleocr", "ocr_text_only", "none"])
    parser.add_argument("--dry-run-selection-only", action="store_true")
    args = parser.parse_args()

    roles = [x.strip() for x in args.roles.split(",") if x.strip()]
    result = run_probe(
        mineru_output_root=Path(args.mineru_output_root),
        output_dir=Path(args.output_dir),
        max_reports=int(args.max_reports),
        max_tables=int(args.max_tables),
        roles=roles,
        recognizer_mode=args.recognizer,
        dry_run_selection_only=bool(args.dry_run_selection_only),
    )
    summary = result["summary"]
    print(f"table_asset_recognition_probe_excel: {result['excel_path']}")
    print(f"table_asset_recognition_probe_summary_json: {result['summary_json_path']}")
    print(f"table_asset_recognition_probe_report_md: {result['report_md_path']}")
    print(f"selected_table_asset_count: {summary.get('selected_table_asset_count', 0)}")
    print(f"recognizer_name: {summary.get('recognizer_name', '')}")
    print(f"recognizer_available: {summary.get('recognizer_available', False)}")
    print(f"recognized_grid_count: {summary.get('recognized_grid_count', 0)}")
    print(f"recognized_text_only_count: {summary.get('recognized_text_only_count', 0)}")
    print(f"recognition_probe_decision: {summary.get('recognition_probe_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
