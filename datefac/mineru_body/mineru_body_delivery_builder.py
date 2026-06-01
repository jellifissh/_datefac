from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "selected_worklist",
    "table_body_extraction_audit",
    "unified_tables",
    "normalized_rows",
    "metric_candidates_all",
    "trusted_preview",
    "review_required_preview",
    "rejected_preview",
    "per_table_summary",
    "metric_coverage",
    "unit_year_context_summary",
    "risk_tag_counts",
    "provenance_coverage",
    "normalization_audit",
    "mapping_diagnostics",
    "mineru_vs_vlm_ppstructure_summary",
    "qa_checks",
    "known_limitations",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def safe_sheet_name(name: str, used: Set[str]) -> str:
    cleaned = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    base = cleaned
    index = 1
    while cleaned in used:
        suffix = f"_{index}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(cleaned)
    return cleaned


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(writer, sheet_name=safe_sheet_name(name, used), index=False)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for _, row in dataframe.iterrows():
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")


def build_summary_dataframe(summary: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "metric": key,
                "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value,
            }
            for key, value in summary.items()
        ]
    )


def top_risk_tags_from_df(risk_tag_counts_df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
    if risk_tag_counts_df.empty or "risk_tag" not in risk_tag_counts_df.columns:
        return []
    rows: List[Dict[str, Any]] = []
    for _, row in risk_tag_counts_df.head(limit).iterrows():
        rows.append({"risk_tag": _norm(row.get("risk_tag")), "count": int(row.get("count", 0))})
    return rows


def write_markdown_report(path: Path, summary: Dict[str, Any], qa_df: pd.DataFrame, comparison_df: pd.DataFrame, risk_df: pd.DataFrame) -> None:
    qa_lines = [
        f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}"
        for _, row in qa_df.iterrows()
    ] if not qa_df.empty else ["- none"]
    comparison_lines = [
        f"- {row.get('route_name', '')}: candidate_count={row.get('candidate_count', '')}, trusted_count={row.get('trusted_count', '')}, trusted_rate={row.get('trusted_rate', '')}, notes={row.get('notes', '')}"
        for _, row in comparison_df.iterrows()
    ] if not comparison_df.empty else ["- comparison unavailable"]
    top_risk_tags = [f"{_norm(row.get('risk_tag'))}:{row.get('count')}" for _, row in risk_df.head(10).iterrows()] if not risk_df.empty else []
    lines = [
        "# 321D MinerU Table Body Ingestion",
        "",
        "## Summary",
        f"- output_dir: `{summary.get('output_dir', '')}`",
        f"- selected_table_count: {summary.get('selected_table_count', 0)}",
        f"- attempted_table_count: {summary.get('attempted_table_count', 0)}",
        f"- table_body_found_count: {summary.get('table_body_found_count', 0)}",
        f"- parsed_table_count: {summary.get('parsed_table_count', 0)}",
        f"- table_with_candidates_count: {summary.get('table_with_candidates_count', 0)}",
        f"- table_with_trusted_count: {summary.get('table_with_trusted_count', 0)}",
        f"- total_candidate_count: {summary.get('total_candidate_count', 0)}",
        f"- trusted_total_count: {summary.get('trusted_total_count', 0)}",
        f"- review_required_total_count: {summary.get('review_required_total_count', 0)}",
        f"- rejected_total_count: {summary.get('rejected_total_count', 0)}",
        f"- trusted_rate: {summary.get('trusted_rate', 0.0)}",
        f"- provenance_complete_rate: {summary.get('provenance_complete_rate', 0.0)}",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        f"- mineru_body_ingestion_decision: {summary.get('mineru_body_ingestion_decision', '')}",
        "",
        "## QA Checks",
    ]
    lines.extend(qa_lines)
    lines.extend(["", "## Route Comparison"])
    lines.extend(comparison_lines)
    lines.extend(["", "## Top Risk Tags", f"- {' | '.join(top_risk_tags) if top_risk_tags else 'none'}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
