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

from datefac.extraction.row_text_cleaner import clean_row_texts
from datefac.extraction.row_text_metric_extractor import extract_metric_candidates_from_repaired_rows
from datefac.extraction.row_text_repair import repair_row_fragments
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


def _build_raw_rows_from_extracted(extracted_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for t in extracted_tables:
        row_texts = t.get("row_texts", [])
        if not isinstance(row_texts, list) or len(row_texts) == 0:
            row_texts = [x.get("text", "") for x in t.get("cells", []) if int(x.get("col", 0)) == 0]
            row_texts = [x for x in row_texts if _norm(x)]
        if not row_texts and _norm(t.get("raw_text")):
            row_texts = [x.strip() for x in _norm(t.get("raw_text")).splitlines() if x.strip()]

        for i, rt in enumerate(row_texts):
            rows.append(
                {
                    "source_file": _norm(t.get("source_doc_name")),
                    "extracted_table_id": _norm(t.get("extracted_table_id")),
                    "row_index": i,
                    "row_text": _norm(rt),
                    "recognition_status": _norm(t.get("recognition_status")),
                }
            )
    return rows


def _expected_smoke_check(metric_df: pd.DataFrame) -> Dict[str, Any]:
    # soft smoke set for known sample; no hardcoding of output rows, only check presence patterns
    expected = [
        ("net_profit", "2024", "1974"),
        ("net_profit", "2028E", "4526"),
        ("depreciation_amortization", "2024", "1083"),
        ("operating_cash_flow", "2024", "3537"),
        ("investing_cash_flow", "2025", "-2705"),
        ("financing_cash_flow", "2024", "-967"),
        ("net_cash_change", "2024", "2828"),
        ("free_cash_flow_firm", "2027E", "4312"),
    ]
    passed = 0
    details: List[Dict[str, Any]] = []
    if metric_df.empty:
        for e in expected:
            details.append({"metric_code": e[0], "year": e[1], "expected_value": e[2], "passed": False})
        return {
            "smoke_check_expected_row_count": len(expected),
            "smoke_check_passed_row_count": 0,
            "smoke_check_failed_row_count": len(expected),
            "details": details,
        }

    for metric_code, year, exp_value in expected:
        cond = (
            (metric_df["metric_code"].astype(str) == metric_code)
            & (metric_df["year"].astype(str) == year)
            & (metric_df["normalized_value"].astype(str).str.replace(",", "", regex=False) == exp_value)
        )
        ok = bool(cond.any())
        if ok:
            passed += 1
        details.append({"metric_code": metric_code, "year": year, "expected_value": exp_value, "passed": ok})
    return {
        "smoke_check_expected_row_count": len(expected),
        "smoke_check_passed_row_count": passed,
        "smoke_check_failed_row_count": len(expected) - passed,
        "details": details,
    }


def run_calibration(ppstructure_result_dir: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rr = read_legacy_ppstructure_results(ppstructure_result_dir)

    extracted_tables = [x.to_dict() for x in rr.extracted_tables]
    raw_rows = _build_raw_rows_from_extracted(extracted_tables)
    raw_row_text_count = len(raw_rows)

    cleaned = clean_row_texts(raw_rows)
    cleaned_rows = cleaned["cleaned_rows"]
    rejected_rows = cleaned["rejected_rows"]
    cleaner_warnings = cleaned["warnings"]

    repaired = repair_row_fragments(cleaned_rows, expected_year_count=5)
    repaired_rows = repaired["repaired_rows"]
    repair_warnings = repaired["warnings"]

    extracted = extract_metric_candidates_from_repaired_rows(repaired_rows, expected_year_count=5)
    metric_candidates = extracted["metric_candidate_preview"]
    parse_warnings = extracted["parse_warnings"]
    unmatched_rows = extracted["unmatched_rows"]
    numeric_split = extracted["numeric_tokenizer_split_1974_detected"]

    # merge warnings
    warnings_all = []
    warnings_all.extend(rr.warnings)
    warnings_all.extend(cleaner_warnings)
    warnings_all.extend(repair_warnings)
    warnings_all.extend(parse_warnings)

    metric_df = pd.DataFrame(metric_candidates)
    if metric_df.empty:
        metric_df = pd.DataFrame(
            columns=[
                "source_file",
                "extracted_table_id",
                "row_index",
                "row_text",
                "metric_code",
                "raw_metric_name",
                "year",
                "raw_value",
                "normalized_value",
                "raw_unit",
                "alignment_status",
                "risk_tags",
                "confidence",
            ]
        )

    smoke = _expected_smoke_check(metric_df)
    bbox_or_html_leak = False
    if not metric_df.empty:
        for rt in metric_df["row_text"].astype(str).tolist():
            low = rt.lower()
            if "cell_bbox" in low or low.strip().startswith("{") or "<table" in low or "<td" in low:
                bbox_or_html_leak = True
                break

    cleaned_human_row_text_count = len(cleaned_rows)
    repaired_row_count = len([r for r in repaired_rows if _norm(r.get("repair_tags")) != ""])
    high_conf = int((metric_df["confidence"] == "high").sum()) if not metric_df.empty else 0
    med_conf = int((metric_df["confidence"] == "medium").sum()) if not metric_df.empty else 0
    low_conf = int((metric_df["confidence"] == "low").sum()) if not metric_df.empty else 0
    numeric_count_mismatch_count = int(extracted["numeric_count_mismatch_count"])

    if bbox_or_html_leak:
        decision = "ROW_TEXT_CALIBRATION_FAILED_NOISE_LEAK"
    elif numeric_split:
        decision = "ROW_TEXT_CALIBRATION_FAILED_NUMERIC_TOKENIZER"
    elif smoke["smoke_check_passed_row_count"] >= 8 and numeric_count_mismatch_count <= 3:
        decision = "ROW_TEXT_CALIBRATION_READY_FOR_320D"
    elif repaired_row_count > 0 and smoke["smoke_check_passed_row_count"] < 8:
        decision = "ROW_TEXT_REPAIR_NEEDS_MORE_CALIBRATION"
    else:
        decision = "ROW_TEXT_CALIBRATION_NOT_READY"

    summary_payload = {
        "source_result_file_count": len(rr.source_files),
        "raw_row_text_count": raw_row_text_count,
        "cleaned_human_row_text_count": cleaned_human_row_text_count,
        "skipped_raw_bbox_count": int(cleaned["skipped_raw_bbox_count"]),
        "skipped_raw_html_count": int(cleaned["skipped_raw_html_count"]),
        "repaired_row_count": repaired_row_count,
        "metric_candidate_count": int(len(metric_df)),
        "high_confidence_candidate_count": high_conf,
        "medium_confidence_candidate_count": med_conf,
        "low_confidence_candidate_count": low_conf,
        "numeric_count_mismatch_count": numeric_count_mismatch_count,
        "smoke_check_expected_row_count": int(smoke["smoke_check_expected_row_count"]),
        "smoke_check_passed_row_count": int(smoke["smoke_check_passed_row_count"]),
        "smoke_check_failed_row_count": int(smoke["smoke_check_failed_row_count"]),
        "row_text_calibration_decision": decision,
    }

    cleaned_df = pd.DataFrame(cleaned_rows)
    repaired_df = pd.DataFrame(repaired_rows)
    warning_df = pd.DataFrame(warnings_all)
    rejected_df = pd.DataFrame(rejected_rows)
    unmatched_df = pd.DataFrame(unmatched_rows)
    source_files_df = pd.DataFrame(rr.source_files)
    smoke_df = pd.DataFrame(smoke["details"])
    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary_payload.items()])

    if cleaned_df.empty:
        cleaned_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text_raw", "row_text_category", "row_text_cleaned"])
    if repaired_df.empty:
        repaired_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text_repaired", "repaired_label", "repaired_values", "repair_tags"])
    if warning_df.empty:
        warning_df = pd.DataFrame(columns=["source_file", "warning_code", "warning_message"])
    if rejected_df.empty:
        rejected_df = pd.DataFrame(columns=["source_file", "row_text_raw", "row_text_category"])
    if unmatched_df.empty:
        unmatched_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text"])
    if source_files_df.empty:
        source_files_df = pd.DataFrame(columns=["source_file", "source_kind"])

    out_excel = output_dir / "legacy_ppstructure_row_text_320c3.xlsx"
    _write_excel(
        out_excel,
        {
            "summary": summary_df,
            "cleaned_row_texts": cleaned_df,
            "repaired_rows": repaired_df,
            "metric_candidate_preview": metric_df,
            "expected_value_smoke_check": smoke_df,
            "parse_warnings": warning_df,
            "rejected_noise_rows": rejected_df,
            "unmatched_rows": unmatched_df,
            "source_files": source_files_df,
        },
    )

    out_summary = output_dir / "legacy_ppstructure_row_text_320c3_summary.json"
    _json_dump(out_summary, summary_payload)

    out_report = output_dir / "legacy_ppstructure_row_text_320c3_report.md"
    report_lines = [
        "# 320C3 Row-Text Candidate Calibration",
        "",
        f"- source_result_file_count: {summary_payload['source_result_file_count']}",
        f"- raw_row_text_count: {summary_payload['raw_row_text_count']}",
        f"- cleaned_human_row_text_count: {summary_payload['cleaned_human_row_text_count']}",
        f"- skipped_raw_bbox_count: {summary_payload['skipped_raw_bbox_count']}",
        f"- skipped_raw_html_count: {summary_payload['skipped_raw_html_count']}",
        f"- repaired_row_count: {summary_payload['repaired_row_count']}",
        f"- metric_candidate_count: {summary_payload['metric_candidate_count']}",
        f"- numeric_count_mismatch_count: {summary_payload['numeric_count_mismatch_count']}",
        f"- smoke_check_passed_row_count: {summary_payload['smoke_check_passed_row_count']}",
        f"- row_text_calibration_decision: {summary_payload['row_text_calibration_decision']}",
        "",
        "## Output",
        f"- excel: `{out_excel}`",
        f"- summary_json: `{out_summary}`",
        f"- report_md: `{out_report}`",
    ]
    out_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    with (output_dir / "cleaned_row_texts.jsonl").open("w", encoding="utf-8") as f:
        for _, r in cleaned_df.iterrows():
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    with (output_dir / "repaired_rows.jsonl").open("w", encoding="utf-8") as f:
        for _, r in repaired_df.iterrows():
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    with (output_dir / "metric_candidate_preview.jsonl").open("w", encoding="utf-8") as f:
        for _, r in metric_df.iterrows():
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    return {
        "excel_path": str(out_excel),
        "summary_json_path": str(out_summary),
        "report_md_path": str(out_report),
        "summary": summary_payload,
        "warning_df": warning_df,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 320C3 row text candidate calibration.")
    parser.add_argument("--ppstructure-result-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_calibration(
        ppstructure_result_dir=Path(args.ppstructure_result_dir),
        output_dir=Path(args.output_dir),
    )
    s = result["summary"]
    print(f"legacy_row_text_calibration_excel: {result['excel_path']}")
    print(f"legacy_row_text_calibration_summary_json: {result['summary_json_path']}")
    print(f"legacy_row_text_calibration_report_md: {result['report_md_path']}")
    print(f"cleaned_human_row_text_count: {s.get('cleaned_human_row_text_count', 0)}")
    print(f"skipped_raw_bbox_count: {s.get('skipped_raw_bbox_count', 0)}")
    print(f"skipped_raw_html_count: {s.get('skipped_raw_html_count', 0)}")
    print(f"repaired_row_count: {s.get('repaired_row_count', 0)}")
    print(f"metric_candidate_count: {s.get('metric_candidate_count', 0)}")
    print(f"numeric_count_mismatch_count: {s.get('numeric_count_mismatch_count', 0)}")
    print(f"smoke_check_passed_row_count: {s.get('smoke_check_passed_row_count', 0)}")
    print(f"row_text_calibration_decision: {s.get('row_text_calibration_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

