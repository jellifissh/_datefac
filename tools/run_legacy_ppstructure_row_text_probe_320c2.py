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

from datefac.extraction.row_text_metric_extractor import extract_metric_candidates_from_row_text
from datefac.parser.mineru_output_reader import read_mineru_output
from datefac.recognition.legacy_ppstructure_result_reader import read_legacy_ppstructure_results


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


def _selection_only_from_mineru(mineru_output_root: Path) -> Dict[str, Any]:
    roles = {
        "CORE_METRIC_TABLE",
        "FINANCIAL_FORECAST_VALUATION",
        "BALANCE_SHEET",
        "INCOME_STATEMENT",
        "CASH_FLOW_STATEMENT",
        "BUSINESS_ASSUMPTION",
    }
    selected_rows: List[Dict[str, Any]] = []
    parse_warnings: List[Dict[str, Any]] = []
    for rd in sorted([p for p in mineru_output_root.iterdir() if p.is_dir()]):
        res = read_mineru_output(rd)
        for w in res.warnings:
            parse_warnings.append(
                {
                    "source_file": _norm(w.source_file),
                    "warning_code": _norm(w.warning_code),
                    "warning_message": _norm(w.warning_message),
                }
            )
        for a in res.table_assets:
            ad = a.to_dict()
            extra = ad.get("extra", {}) if isinstance(ad.get("extra"), dict) else {}
            role = _norm(extra.get("role_category") or ad.get("table_role_guess"))
            if role in roles:
                selected_rows.append(
                    {
                        "source_file": _norm(ad.get("source_file")),
                        "table_asset_id": f"{rd.name}__{_norm(ad.get('source_doc_id'))}__{ad.get('block_index')}",
                        "source_doc_name": _norm(ad.get("source_doc_id")) or rd.name,
                        "table_role_guess": role,
                        "row_text": "",
                        "recognition_status": "SKIPPED_SELECTION_ONLY",
                    }
                )
    return {"selected_rows": selected_rows, "parse_warnings": parse_warnings}


def run_probe(
    output_dir: Path,
    ppstructure_result_dir: Path | None = None,
    mineru_output_root: Path | None = None,
    selection_only: bool = False,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_tables_rows: List[Dict[str, Any]] = []
    row_text_rows: List[Dict[str, Any]] = []
    source_files_rows: List[Dict[str, Any]] = []
    parse_warnings_rows: List[Dict[str, Any]] = []

    if selection_only and mineru_output_root is not None:
        probe = _selection_only_from_mineru(mineru_output_root)
        selected_rows = probe["selected_rows"]
        parse_warnings_rows.extend(probe["parse_warnings"])

        metric_candidate_preview_rows: List[Dict[str, Any]] = []
        unmatched_rows: List[Dict[str, Any]] = selected_rows
        summary_payload = {
            "source_result_file_count": 0,
            "extracted_table_count": 0,
            "recognized_row_text_count": 0,
            "recognized_grid_count": 0,
            "total_row_text_count": 0,
            "metric_candidate_count": 0,
            "matched_metric_row_count": 0,
            "unmatched_row_count": len(unmatched_rows),
            "year_inferred_count": 0,
            "numeric_count_mismatch_count": 0,
            "row_text_probe_decision": "NEED_MORE_ROW_TEXT_SAMPLES",
        }
    else:
        if ppstructure_result_dir is None:
            raise ValueError("ppstructure_result_dir is required unless selection_only mode is enabled.")

        rr = read_legacy_ppstructure_results(ppstructure_result_dir)
        source_files_rows.extend(rr.source_files)
        for w in rr.warnings:
            parse_warnings_rows.append(
                {
                    "source_file": _norm(w.get("source_file")),
                    "warning_code": _norm(w.get("warning_code")),
                    "warning_message": _norm(w.get("warning_message")),
                }
            )

        for et in rr.extracted_tables:
            ed = et.to_dict()
            extracted_tables_rows.append(
                {
                    "extracted_table_id": ed["extracted_table_id"],
                    "table_asset_id": ed["table_asset_id"],
                    "source_doc_name": ed["source_doc_name"],
                    "source_file": ed["source_doc_name"],
                    "recognizer_name": ed["recognizer_name"],
                    "recognizer_version": ed["recognizer_version"],
                    "recognition_status": ed["recognition_status"],
                    "row_count": ed["row_count"],
                    "col_count": ed["col_count"],
                    "cell_count": ed["cell_count"],
                    "non_empty_cell_count": ed["non_empty_cell_count"],
                    "raw_text": ed["raw_text"][:8000],
                    "warnings": "|".join(ed.get("warnings", [])),
                }
            )
            row_texts = ed.get("row_texts", None)
            if not isinstance(row_texts, list) or len(row_texts) == 0:
                row_texts = [x.get("text", "") for x in ed.get("cells", []) if int(x.get("col", 0)) == 0]
                row_texts = [x for x in row_texts if _norm(x)]
            for i, rt in enumerate(row_texts):
                row_text_rows.append(
                    {
                        "source_file": ed["source_doc_name"],
                        "extracted_table_id": ed["extracted_table_id"],
                        "row_index": i,
                        "row_text": _norm(rt),
                    }
                )

        extractor_out = extract_metric_candidates_from_row_text(rr.extracted_tables)
        metric_candidate_preview_rows = extractor_out["metric_candidate_preview"]
        unmatched_rows = extractor_out["unmatched_rows"]
        parse_warnings_rows.extend(extractor_out["parse_warnings"])

        source_result_file_count = len(source_files_rows)
        extracted_table_count = len(rr.extracted_tables)
        recognized_row_text_count = sum(1 for x in rr.extracted_tables if x.recognition_status == "RECOGNIZED_ROW_TEXT")
        recognized_grid_count = sum(1 for x in rr.extracted_tables if x.recognition_status in {"RECOGNIZED_GRID", "RECOGNIZED_GRID_WEAK"})
        total_row_text_count = extractor_out["total_row_text_count"]
        metric_candidate_count = len(metric_candidate_preview_rows)
        matched_metric_row_count = extractor_out["matched_metric_row_count"]
        unmatched_row_count = len(unmatched_rows)
        year_inferred_count = extractor_out["year_inferred_count"]
        numeric_count_mismatch_count = extractor_out["numeric_count_mismatch_count"]

        mismatch_ratio = float(numeric_count_mismatch_count / max(metric_candidate_count, 1))
        if metric_candidate_count >= 20 and mismatch_ratio <= 0.30:
            decision = "ROW_TEXT_RECOGNITION_READY_FOR_320D_CANDIDATE_MAPPING"
        elif recognized_row_text_count > 0 and metric_candidate_count < 20:
            decision = "ROW_TEXT_AVAILABLE_NEEDS_RULE_CALIBRATION"
        elif total_row_text_count == 0:
            decision = "LEGACY_PPSTRUCTURE_RESULT_PARSE_FAILED"
        else:
            decision = "NEED_MORE_ROW_TEXT_SAMPLES"

        if any(_norm(x.get("warning_code")) == "BLOCKED_MISSING_PPSTRUCTURE_RESULT_DIR" for x in parse_warnings_rows):
            decision = "BLOCKED_MISSING_PPSTRUCTURE_RESULT_DIR"

        summary_payload = {
            "source_result_file_count": source_result_file_count,
            "extracted_table_count": extracted_table_count,
            "recognized_row_text_count": recognized_row_text_count,
            "recognized_grid_count": recognized_grid_count,
            "total_row_text_count": total_row_text_count,
            "metric_candidate_count": metric_candidate_count,
            "matched_metric_row_count": matched_metric_row_count,
            "unmatched_row_count": unmatched_row_count,
            "year_inferred_count": year_inferred_count,
            "numeric_count_mismatch_count": numeric_count_mismatch_count,
            "row_text_probe_decision": decision,
        }

    # export
    extracted_df = pd.DataFrame(extracted_tables_rows)
    row_text_df = pd.DataFrame(row_text_rows)
    metric_df = pd.DataFrame(metric_candidate_preview_rows)
    parse_warnings_df = pd.DataFrame(parse_warnings_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)
    source_files_df = pd.DataFrame(source_files_rows)

    if extracted_df.empty:
        extracted_df = pd.DataFrame(columns=["extracted_table_id", "table_asset_id", "source_doc_name", "recognition_status", "row_count", "col_count", "cell_count", "non_empty_cell_count", "raw_text", "warnings"])
    if row_text_df.empty:
        row_text_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text"])
    if metric_df.empty:
        metric_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text", "metric_code", "raw_metric_name", "year", "raw_value", "normalized_value", "raw_unit", "alignment_status", "risk_tags", "confidence"])
    if parse_warnings_df.empty:
        parse_warnings_df = pd.DataFrame(columns=["source_file", "warning_code", "warning_message"])
    if unmatched_df.empty:
        unmatched_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text"])
    if source_files_df.empty:
        source_files_df = pd.DataFrame(columns=["source_file", "source_kind"])

    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary_payload.items()])

    out_excel = output_dir / "legacy_ppstructure_row_text_320c2.xlsx"
    _write_excel(
        out_excel,
        {
            "summary": summary_df,
            "extracted_tables": extracted_df,
            "row_texts": row_text_df,
            "metric_candidate_preview": metric_df,
            "parse_warnings": parse_warnings_df,
            "unmatched_rows": unmatched_df,
            "source_files": source_files_df,
        },
    )

    out_summary = output_dir / "legacy_ppstructure_row_text_320c2_summary.json"
    _json_dump(out_summary, summary_payload)

    out_report = output_dir / "legacy_ppstructure_row_text_320c2_report.md"
    report_lines = [
        "# 320C2 Legacy PPStructure Row-Text Probe",
        "",
        f"- source_result_file_count: {summary_payload.get('source_result_file_count', 0)}",
        f"- extracted_table_count: {summary_payload.get('extracted_table_count', 0)}",
        f"- recognized_row_text_count: {summary_payload.get('recognized_row_text_count', 0)}",
        f"- recognized_grid_count: {summary_payload.get('recognized_grid_count', 0)}",
        f"- metric_candidate_count: {summary_payload.get('metric_candidate_count', 0)}",
        f"- numeric_count_mismatch_count: {summary_payload.get('numeric_count_mismatch_count', 0)}",
        f"- row_text_probe_decision: {summary_payload.get('row_text_probe_decision', '')}",
        "",
        "## Output",
        f"- excel: `{out_excel}`",
        f"- summary_json: `{out_summary}`",
        f"- report_md: `{out_report}`",
    ]
    out_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    with (output_dir / "extracted_tables.jsonl").open("w", encoding="utf-8") as f:
        for _, r in extracted_df.iterrows():
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    with (output_dir / "metric_candidate_preview.jsonl").open("w", encoding="utf-8") as f:
        for _, r in metric_df.iterrows():
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    return {
        "excel_path": str(out_excel),
        "summary_json_path": str(out_summary),
        "report_md_path": str(out_report),
        "summary": summary_payload,
        "warning_summary_df": parse_warnings_df,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run legacy PPStructure row-text probe 320C2.")
    parser.add_argument("--ppstructure-result-dir", default="")
    parser.add_argument("--mineru-output-root", default="")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--selection-only", action="store_true")
    args = parser.parse_args()

    pp_dir = Path(args.ppstructure_result_dir) if _norm(args.ppstructure_result_dir) else None
    mineru_root = Path(args.mineru_output_root) if _norm(args.mineru_output_root) else None

    result = run_probe(
        output_dir=Path(args.output_dir),
        ppstructure_result_dir=pp_dir,
        mineru_output_root=mineru_root,
        selection_only=bool(args.selection_only),
    )
    s = result["summary"]
    print(f"legacy_row_text_probe_excel: {result['excel_path']}")
    print(f"legacy_row_text_probe_summary_json: {result['summary_json_path']}")
    print(f"legacy_row_text_probe_report_md: {result['report_md_path']}")
    print(f"source_result_file_count: {s.get('source_result_file_count', 0)}")
    print(f"extracted_table_count: {s.get('extracted_table_count', 0)}")
    print(f"recognized_row_text_count: {s.get('recognized_row_text_count', 0)}")
    print(f"metric_candidate_count: {s.get('metric_candidate_count', 0)}")
    print(f"numeric_count_mismatch_count: {s.get('numeric_count_mismatch_count', 0)}")
    print(f"row_text_probe_decision: {s.get('row_text_probe_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

