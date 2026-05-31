from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd

from datefac.pipeline.batch_ppstructure_row_text_pipeline import run_batch_ppstructure_row_text_pipeline


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


def _write_jsonl(path: Path, df: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")


def run_batch_row_text_delivery_benchmark(ppstructure_batch_dir: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pipeline = run_batch_ppstructure_row_text_pipeline(ppstructure_batch_dir=ppstructure_batch_dir)

    if pipeline.get("blocked"):
        summary_payload = {
            "batch_table_count": 0,
            "batch_ok_count": 0,
            "parsed_table_count": 0,
            "table_with_row_text_count": 0,
            "table_with_candidates_count": 0,
            "table_with_trusted_count": 0,
            "report_count": 0,
            "trusted_total_count": 0,
            "review_required_total_count": 0,
            "rejected_total_count": 0,
            "trusted_rate": 0.0,
            "review_required_rate": 0.0,
            "rejected_rate": 0.0,
            "unique_metric_count": 0,
            "unique_year_count": 0,
            "unique_report_count": 0,
            "unit_unknown_count": 0,
            "year_inferred_count": 0,
            "conflict_count": 0,
            "provenance_complete_rate": 0.0,
            "qa_pass_count": 0,
            "qa_warn_count": 0,
            "qa_fail_count": 1,
            "batch_delivery_decision": pipeline.get("blocked_code", "BATCH_ROW_TEXT_DELIVERY_NOT_READY"),
            "blocked_message": pipeline.get("blocked_message", ""),
            "top_risk_tags": [],
        }
        summary_df = pd.DataFrame([{"metric": k, "value": v if not isinstance(v, list) else json.dumps(v, ensure_ascii=False)} for k, v in summary_payload.items()])
        excel_path = output_dir / "batch_row_text_delivery_320g.xlsx"
        _write_excel(
            excel_path,
            {
                "summary": summary_df,
                "table_run_inventory": pd.DataFrame(),
                "extracted_row_texts_all": pd.DataFrame(),
                "metric_candidates_all": pd.DataFrame(),
                "normalized_candidates_all": pd.DataFrame(),
                "trusted_preview_all": pd.DataFrame(),
                "review_required_preview_all": pd.DataFrame(),
                "rejected_preview_all": pd.DataFrame(),
                "per_table_summary": pd.DataFrame(),
                "per_report_summary": pd.DataFrame(),
                "metric_coverage": pd.DataFrame(),
                "table_type_performance": pd.DataFrame(),
                "risk_tag_counts": pd.DataFrame(),
                "provenance_coverage": pd.DataFrame(),
                "qa_checks": pd.DataFrame(),
                "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": summary_payload["blocked_message"]}]),
            },
        )
        summary_json_path = output_dir / "batch_row_text_delivery_320g_summary.json"
        _json_dump(summary_json_path, summary_payload)
        report_md_path = output_dir / "batch_row_text_delivery_320g_report.md"
        report_md_path.write_text(
            "\n".join(
                [
                    "# 320G Batch PPStructure Outputs to Multi-Report Delivery",
                    "",
                    f"- ppstructure_batch_dir: `{ppstructure_batch_dir}`",
                    f"- batch_delivery_decision: {summary_payload['batch_delivery_decision']}",
                    f"- blocked_message: {summary_payload['blocked_message']}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "summary": summary_payload,
            "excel_path": str(excel_path),
            "summary_json_path": str(summary_json_path),
            "report_md_path": str(report_md_path),
        }

    summary_payload = dict(pipeline["summary"])
    dfs = pipeline["dataframes"]

    summary_df = pd.DataFrame(
        [
            {
                "metric": k,
                "value": (
                    json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                ),
            }
            for k, v in summary_payload.items()
        ]
    )

    excel_path = output_dir / "batch_row_text_delivery_320g.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "table_run_inventory": dfs["table_run_inventory"],
            "extracted_row_texts_all": dfs["extracted_row_texts_all"],
            "metric_candidates_all": dfs["metric_candidates_all"],
            "normalized_candidates_all": dfs["normalized_candidates_all"],
            "trusted_preview_all": dfs["trusted_preview_all"],
            "review_required_preview_all": dfs["review_required_preview_all"],
            "rejected_preview_all": dfs["rejected_preview_all"],
            "per_table_summary": dfs["per_table_summary"],
            "per_report_summary": dfs["per_report_summary"],
            "metric_coverage": dfs["metric_coverage"],
            "table_type_performance": dfs["table_type_performance"],
            "risk_tag_counts": dfs["risk_tag_counts"],
            "provenance_coverage": dfs["provenance_coverage"],
            "qa_checks": dfs["qa_checks"],
            "known_limitations": dfs["known_limitations"],
        },
    )

    summary_json_path = output_dir / "batch_row_text_delivery_320g_summary.json"
    _json_dump(summary_json_path, summary_payload)

    report_md_path = output_dir / "batch_row_text_delivery_320g_report.md"
    report_lines = [
        "# 320G Batch PPStructure Outputs to Multi-Report Delivery",
        "",
        f"- ppstructure_batch_dir: `{ppstructure_batch_dir}`",
        f"- batch_table_count: {summary_payload.get('batch_table_count', 0)}",
        f"- batch_ok_count: {summary_payload.get('batch_ok_count', 0)}",
        f"- parsed_table_count: {summary_payload.get('parsed_table_count', 0)}",
        f"- table_with_row_text_count: {summary_payload.get('table_with_row_text_count', 0)}",
        f"- table_with_candidates_count: {summary_payload.get('table_with_candidates_count', 0)}",
        f"- table_with_trusted_count: {summary_payload.get('table_with_trusted_count', 0)}",
        f"- report_count: {summary_payload.get('report_count', 0)}",
        f"- trusted_total_count: {summary_payload.get('trusted_total_count', 0)}",
        f"- review_required_total_count: {summary_payload.get('review_required_total_count', 0)}",
        f"- rejected_total_count: {summary_payload.get('rejected_total_count', 0)}",
        f"- trusted_rate: {summary_payload.get('trusted_rate', 0.0)}",
        f"- provenance_complete_rate: {summary_payload.get('provenance_complete_rate', 0.0)}",
        f"- qa_pass_count: {summary_payload.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary_payload.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary_payload.get('qa_fail_count', 0)}",
        f"- batch_delivery_decision: {summary_payload.get('batch_delivery_decision', '')}",
        "",
        "## Output",
        f"- excel: `{excel_path}`",
        f"- summary_json: `{summary_json_path}`",
        f"- report_md: `{report_md_path}`",
    ]
    report_md_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    optional = {
        "metric_candidates_all.jsonl": dfs["metric_candidates_all"],
        "normalized_candidates_all.jsonl": dfs["normalized_candidates_all"],
        "trusted_preview_all.jsonl": dfs["trusted_preview_all"],
        "review_required_preview_all.jsonl": dfs["review_required_preview_all"],
        "table_run_inventory.jsonl": dfs["table_run_inventory"],
    }
    for name, df in optional.items():
        if not df.empty:
            _write_jsonl(output_dir / name, df)

    return {
        "summary": summary_payload,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }
