from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.extraction.row_text_cleaner import clean_row_texts
from datefac.extraction.row_text_metric_extractor import extract_metric_candidates_from_repaired_rows
from datefac.extraction.row_text_repair import repair_row_fragments
from datefac.recognition.legacy_ppstructure_result_reader import read_legacy_ppstructure_results


EXPECTED_YEARS = ["2024", "2025", "2026E", "2027E", "2028E"]
CRITICAL_METRICS = [
    "net_profit",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "net_cash_change",
    "free_cash_flow_firm",
    "free_cash_flow_equity",
]
EXPECTED_SMOKE_ROWS: List[Dict[str, Any]] = [
    {
        "expected_metric_code": "net_profit",
        "expected_metric_name": "净利润",
        "values": {"2024": "1974", "2025": "2371", "2026E": "3307", "2027E": "3885", "2028E": "4526"},
    },
    {
        "expected_metric_code": "asset_impairment_provision",
        "expected_metric_name": "资产减值准备",
        "values": {"2024": "0", "2025": "0", "2026E": "0", "2027E": "0", "2028E": "0"},
    },
    {
        "expected_metric_code": "depreciation_amortization",
        "expected_metric_name": "折旧摊销",
        "values": {"2024": "1083", "2025": "1299", "2026E": "1204", "2027E": "1238", "2028E": "1282"},
    },
    {
        "expected_metric_code": "fair_value_change_loss",
        "expected_metric_name": "公允价值变动损失",
        "values": {"2024": "-45", "2025": "-135", "2026E": "0", "2027E": "0", "2028E": "0"},
    },
    {
        "expected_metric_code": "finance_expense",
        "expected_metric_name": "财务费用",
        "values": {"2024": "36", "2025": "172", "2026E": "-10", "2027E": "-57", "2028E": "-140"},
    },
    {
        "expected_metric_code": "working_capital_change",
        "expected_metric_name": "营运资本变动",
        "values": {"2024": "511", "2025": "528", "2026E": "361", "2027E": "353", "2028E": "327"},
    },
    {
        "expected_metric_code": "other_operating_cf",
        "expected_metric_name": "其它",
        "values": {"2024": "14", "2025": "38", "2026E": "53", "2027E": "62", "2028E": "72"},
    },
    {
        "expected_metric_code": "operating_cash_flow",
        "expected_metric_name": "经营活动现金流",
        "values": {"2024": "3537", "2025": "4102", "2026E": "4924", "2027E": "5537", "2028E": "6207"},
    },
    {
        "expected_metric_code": "capex",
        "expected_metric_name": "资本开支",
        "values": {"2024": "0", "2025": "-869", "2026E": "-1100", "2027E": "-1100", "2028E": "-1100"},
    },
    {
        "expected_metric_code": "other_investing_cash_flow",
        "expected_metric_name": "其它投资现金流",
        "values": {"2024": "1073", "2025": "-2449", "2026E": "0", "2027E": "-1123", "2028E": "-647"},
    },
    {
        "expected_metric_code": "investing_cash_flow",
        "expected_metric_name": "投资活动现金流",
        "values": {"2024": "258", "2025": "-2705", "2026E": "-1300", "2027E": "-2423", "2028E": "-1947"},
    },
    {
        "expected_metric_code": "equity_financing",
        "expected_metric_name": "权益性融资",
        "values": {"2024": "0", "2025": "0", "2026E": "0", "2027E": "0", "2028E": "0"},
    },
    {
        "expected_metric_code": "debt_net_change",
        "expected_metric_name": "负债净变化",
        "values": {"2024": "2784", "2025": "-1966", "2026E": "50", "2027E": "50", "2028E": "50"},
    },
    {
        "expected_metric_code": "dividend_interest_paid",
        "expected_metric_name": "支付股利、利息",
        "values": {"2024": "0", "2025": "0", "2026E": "0", "2027E": "0", "2028E": "0"},
    },
    {
        "expected_metric_code": "other_financing_cash_flow",
        "expected_metric_name": "其它融资现金流",
        "values": {"2024": "-6534", "2025": "1022", "2026E": "466", "2027E": "-1138", "2028E": "0"},
    },
    {
        "expected_metric_code": "financing_cash_flow",
        "expected_metric_name": "融资活动现金流",
        "values": {"2024": "-967", "2025": "-2910", "2026E": "516", "2027E": "-1088", "2028E": "50"},
    },
    {
        "expected_metric_code": "net_cash_change",
        "expected_metric_name": "现金净变动",
        "values": {"2024": "2828", "2025": "-1514", "2026E": "4141", "2027E": "2026", "2028E": "4309"},
    },
    {
        "expected_metric_code": "cash_beginning_balance",
        "expected_metric_name": "货币资金的期初余额",
        "values": {"2024": "5192", "2025": "8020", "2026E": "6506", "2027E": "10647", "2028E": "12673"},
    },
    {
        "expected_metric_code": "cash_ending_balance",
        "expected_metric_name": "货币资金的期末余额",
        "values": {"2024": "8020", "2025": "6506", "2026E": "10647", "2027E": "12673", "2028E": "16982"},
    },
    {
        "expected_metric_code": "free_cash_flow_firm",
        "expected_metric_name": "企业自由现金流",
        "values": {"2024": "0", "2025": "3568", "2026E": "3737", "2027E": "4312", "2028E": "4915"},
    },
    {
        "expected_metric_code": "free_cash_flow_equity",
        "expected_metric_name": "权益自由现金流",
        "values": {"2024": "0", "2025": "2486", "2026E": "4261", "2027E": "3269", "2028E": "5077"},
    },
]


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


def _build_candidate_matrix(metric_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if metric_df.empty:
        cols = ["metric_code"] + EXPECTED_YEARS
        return pd.DataFrame(columns=cols), pd.DataFrame(columns=["metric_code", "year", "candidate_count"])

    g = (
        metric_df.groupby(["metric_code", "year"], dropna=False)
        .agg(
            values=("normalized_value", lambda s: " | ".join(sorted({str(x) for x in s.tolist()}))),
            source_rows=("row_text", lambda s: " || ".join(sorted({str(x) for x in s.tolist()}))),
            candidate_row_ids=("candidate_row_id", lambda s: " | ".join(sorted({str(x) for x in s.tolist()}))),
            candidate_count=("normalized_value", "count"),
        )
        .reset_index()
    )
    pivot = g.pivot_table(index="metric_code", columns="year", values="values", aggfunc="first").reset_index()
    for y in EXPECTED_YEARS:
        if y not in pivot.columns:
            pivot[y] = ""
    pivot = pivot[["metric_code"] + EXPECTED_YEARS]
    dup = g[g["candidate_count"] > 1][["metric_code", "year", "candidate_count", "values", "source_rows", "candidate_row_ids"]].copy()
    return pivot, dup


def _expected_vs_actual(metric_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    rows: List[Dict[str, Any]] = []
    passed = 0
    critical_passed = 0

    for exp in EXPECTED_SMOKE_ROWS:
        code = exp["expected_metric_code"]
        mdf = metric_df[metric_df["metric_code"] == code] if not metric_df.empty else pd.DataFrame()
        actual_by_year: Dict[str, List[str]] = {y: [] for y in EXPECTED_YEARS}
        matched_ids: List[str] = []
        matched_texts: List[str] = []
        if not mdf.empty:
            for _, r in mdf.iterrows():
                y = str(r.get("year", ""))
                if y in actual_by_year:
                    actual_by_year[y].append(str(r.get("normalized_value", "")))
                matched_ids.append(str(r.get("candidate_row_id", "")))
                matched_texts.append(str(r.get("row_text", "")))

        has_duplicate = any(len(v) > 1 for v in actual_by_year.values())
        all_years_present = all(len(actual_by_year[y]) >= 1 for y in EXPECTED_YEARS)
        value_match = all(
            (exp["values"][y] in actual_by_year[y]) if actual_by_year[y] else False
            for y in EXPECTED_YEARS
        )
        year_shifted = False
        if not value_match and not mdf.empty:
            actual_flat = [x for y in EXPECTED_YEARS for x in actual_by_year[y]]
            expected_flat = [exp["values"][y] for y in EXPECTED_YEARS]
            if len(actual_flat) >= 5 and sorted(actual_flat[:5]) == sorted(expected_flat):
                year_shifted = True

        if mdf.empty:
            pf = "FAIL"
            reason = "MISSING_METRIC_ROW"
        elif has_duplicate:
            pf = "FAIL"
            reason = "DUPLICATE_CANDIDATES"
        elif year_shifted:
            pf = "FAIL"
            reason = "YEAR_SHIFTED"
        elif all_years_present and value_match:
            pf = "PASS"
            reason = ""
            passed += 1
            if code in CRITICAL_METRICS:
                critical_passed += 1
        elif not all_years_present:
            pf = "FAIL"
            reason = "ROW_REPAIR_FAILED"
        else:
            pf = "FAIL"
            reason = "VALUE_MISMATCH"

        row = {
            "expected_metric_code": code,
            "expected_metric_name": exp["expected_metric_name"],
            "expected_values_2024": exp["values"]["2024"],
            "expected_values_2025": exp["values"]["2025"],
            "expected_values_2026E": exp["values"]["2026E"],
            "expected_values_2027E": exp["values"]["2027E"],
            "expected_values_2028E": exp["values"]["2028E"],
            "actual_values_2024": " | ".join(actual_by_year["2024"]),
            "actual_values_2025": " | ".join(actual_by_year["2025"]),
            "actual_values_2026E": " | ".join(actual_by_year["2026E"]),
            "actual_values_2027E": " | ".join(actual_by_year["2027E"]),
            "actual_values_2028E": " | ".join(actual_by_year["2028E"]),
            "matched_candidate_row_ids": " | ".join(sorted(set(matched_ids))),
            "matched_source_row_texts": " || ".join(sorted(set(matched_texts))),
            "pass_fail": pf,
            "failure_reason": reason,
        }
        rows.append(row)

    return pd.DataFrame(rows), passed, critical_passed


def run_calibration(ppstructure_result_dir: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rr = read_legacy_ppstructure_results(ppstructure_result_dir)

    extracted_tables = [x.to_dict() for x in rr.extracted_tables]
    raw_rows = _build_raw_rows_from_extracted(extracted_tables)

    cleaned = clean_row_texts(raw_rows)
    repaired = repair_row_fragments(cleaned["cleaned_rows"], expected_year_count=5)
    extracted = extract_metric_candidates_from_repaired_rows(repaired["repaired_rows"], expected_year_count=5)

    warnings_all = []
    warnings_all.extend(rr.warnings)
    warnings_all.extend(cleaned["warnings"])
    warnings_all.extend(repaired["warnings"])
    warnings_all.extend(extracted["parse_warnings"])

    metric_df = pd.DataFrame(extracted["metric_candidate_preview"])
    if metric_df.empty:
        metric_df = pd.DataFrame(
            columns=[
                "candidate_row_id",
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

    candidate_matrix_df, dup_df = _build_candidate_matrix(metric_df)
    evs_df, smoke_pass, critical_passed = _expected_vs_actual(metric_df)
    smoke_expected_count = len(EXPECTED_SMOKE_ROWS)

    bbox_or_html_leak = False
    if not metric_df.empty:
        for rt in metric_df["row_text"].astype(str).tolist():
            low = rt.lower()
            if "cell_bbox" in low or low.strip().startswith("{") or "<table" in low or "<td" in low:
                bbox_or_html_leak = True
                break

    numeric_split = bool(extracted["numeric_tokenizer_split_1974_detected"])
    duplicate_metric_year_count = int(len(dup_df))
    critical_dup = 0
    if not dup_df.empty:
        critical_dup = int(dup_df[dup_df["metric_code"].isin(CRITICAL_METRICS)].shape[0])

    if bbox_or_html_leak:
        decision = "ROW_TEXT_SMOKE_FIX_FAILED_NOISE_LEAK"
    elif numeric_split:
        decision = "ROW_TEXT_SMOKE_FIX_FAILED_NUMERIC_TOKENIZER"
    elif critical_dup > 0:
        decision = "ROW_TEXT_SMOKE_FIX_FAILED_DUPLICATES"
    elif smoke_pass >= 14 and critical_passed == len(CRITICAL_METRICS):
        decision = "ROW_TEXT_READY_FOR_320D_SANDBOX_MAPPING"
    elif smoke_pass > 4:
        decision = "ROW_TEXT_REPAIR_IMPROVED_BUT_NEEDS_MORE_CALIBRATION"
    else:
        decision = "ROW_TEXT_SMOKE_FIX_NOT_READY"

    summary_payload = {
        "source_result_file_count": len(rr.source_files),
        "raw_row_text_count": len(raw_rows),
        "cleaned_human_row_text_count": len(cleaned["cleaned_rows"]),
        "skipped_raw_bbox_count": int(cleaned["skipped_raw_bbox_count"]),
        "skipped_raw_html_count": int(cleaned["skipped_raw_html_count"]),
        "repaired_row_count": int(repaired["repaired_row_count"]),
        "metric_candidate_count": int(len(metric_df)),
        "duplicate_metric_year_count": duplicate_metric_year_count,
        "numeric_count_mismatch_count": int(extracted["numeric_count_mismatch_count"]),
        "smoke_check_expected_row_count": smoke_expected_count,
        "smoke_check_passed_row_count": int(smoke_pass),
        "smoke_check_failed_row_count": int(smoke_expected_count - smoke_pass),
        "critical_smoke_rows_passed_count": int(critical_passed),
        "row_text_smoke_fix_decision": decision,
    }

    cleaned_df = pd.DataFrame(cleaned["cleaned_rows"])
    repaired_df = pd.DataFrame(repaired["repaired_rows"])
    repair_trace_df = pd.DataFrame(repaired.get("row_repair_trace", []))
    warning_df = pd.DataFrame(warnings_all)
    rejected_df = pd.DataFrame(cleaned["rejected_rows"])
    unmatched_df = pd.DataFrame(extracted["unmatched_rows"])
    source_files_df = pd.DataFrame(rr.source_files)
    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary_payload.items()])

    if cleaned_df.empty:
        cleaned_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text_raw", "row_text_category", "row_text_cleaned"])
    if repaired_df.empty:
        repaired_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text_repaired", "repaired_label", "repaired_values", "repair_tags"])
    if repair_trace_df.empty:
        repair_trace_df = pd.DataFrame(columns=["trace_step", "action", "source_row_index", "reason", "pending_label", "pending_nums", "result_row_text_repaired", "repair_tags"])
    if warning_df.empty:
        warning_df = pd.DataFrame(columns=["source_file", "warning_code", "warning_message"])
    if rejected_df.empty:
        rejected_df = pd.DataFrame(columns=["source_file", "row_text_raw", "row_text_category"])
    if unmatched_df.empty:
        unmatched_df = pd.DataFrame(columns=["source_file", "extracted_table_id", "row_index", "row_text"])
    if source_files_df.empty:
        source_files_df = pd.DataFrame(columns=["source_file", "source_kind"])
    if dup_df.empty:
        dup_df = pd.DataFrame(columns=["metric_code", "year", "candidate_count", "values", "source_rows", "candidate_row_ids"])

    out_excel = output_dir / "legacy_ppstructure_row_text_320c4.xlsx"
    _write_excel(
        out_excel,
        {
            "summary": summary_df,
            "cleaned_row_texts": cleaned_df,
            "repaired_rows": repaired_df,
            "row_repair_trace": repair_trace_df,
            "metric_candidate_preview": metric_df,
            "candidate_matrix": candidate_matrix_df,
            "expected_vs_actual_matrix": evs_df,
            "duplicate_candidates": dup_df,
            "parse_warnings": warning_df,
            "rejected_noise_rows": rejected_df,
            "unmatched_rows": unmatched_df,
            "source_files": source_files_df,
        },
    )

    out_summary = output_dir / "legacy_ppstructure_row_text_320c4_summary.json"
    _json_dump(out_summary, summary_payload)

    out_report = output_dir / "legacy_ppstructure_row_text_320c4_report.md"
    report_lines = [
        "# 320C4 Cashflow Row-Text Smoke Fix",
        "",
        f"- cleaned_human_row_text_count: {summary_payload['cleaned_human_row_text_count']}",
        f"- repaired_row_count: {summary_payload['repaired_row_count']}",
        f"- metric_candidate_count: {summary_payload['metric_candidate_count']}",
        f"- duplicate_metric_year_count: {summary_payload['duplicate_metric_year_count']}",
        f"- numeric_count_mismatch_count: {summary_payload['numeric_count_mismatch_count']}",
        f"- smoke_check_passed_row_count: {summary_payload['smoke_check_passed_row_count']}",
        f"- critical_smoke_rows_passed_count: {summary_payload['critical_smoke_rows_passed_count']}",
        f"- row_text_smoke_fix_decision: {summary_payload['row_text_smoke_fix_decision']}",
        "",
        "## Output",
        f"- excel: `{out_excel}`",
        f"- summary_json: `{out_summary}`",
        f"- report_md: `{out_report}`",
    ]
    out_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "excel_path": str(out_excel),
        "summary_json_path": str(out_summary),
        "report_md_path": str(out_report),
        "summary": summary_payload,
        "warning_df": warning_df,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 320C4 row text smoke fix calibration.")
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
    print(f"repaired_row_count: {s.get('repaired_row_count', 0)}")
    print(f"metric_candidate_count: {s.get('metric_candidate_count', 0)}")
    print(f"duplicate_metric_year_count: {s.get('duplicate_metric_year_count', 0)}")
    print(f"numeric_count_mismatch_count: {s.get('numeric_count_mismatch_count', 0)}")
    print(f"smoke_check_passed_row_count: {s.get('smoke_check_passed_row_count', 0)}")
    print(f"critical_smoke_rows_passed_count: {s.get('critical_smoke_rows_passed_count', 0)}")
    print(f"row_text_smoke_fix_decision: {s.get('row_text_smoke_fix_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
