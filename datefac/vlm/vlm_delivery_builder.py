from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "vlm_table_inventory",
    "vlm_rows_normalized",
    "metric_candidates_all",
    "trusted_preview",
    "review_required_preview",
    "rejected_preview",
    "per_table_summary",
    "per_report_summary",
    "metric_coverage",
    "unit_year_context_summary",
    "risk_tag_counts",
    "provenance_coverage",
    "qa_checks",
    "vlm_vs_ppstructure_summary",
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
            dataframe = sheets.get(name, pd.DataFrame())
            dataframe.to_excel(writer, sheet_name=safe_sheet_name(name, used), index=False)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for _, row in dataframe.iterrows():
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")


def write_markdown_report(path: Path, summary: Dict[str, Any], qa_df: pd.DataFrame, comparison_df: pd.DataFrame, risk_df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    top_risk_tags = []
    if not risk_df.empty and "risk_tag" in risk_df.columns:
        for _, row in risk_df.head(10).iterrows():
            top_risk_tags.append(f"{_norm(row.get('risk_tag'))}:{row.get('count')}")

    qa_lines: List[str] = []
    if not qa_df.empty:
        for _, row in qa_df.iterrows():
            qa_lines.append(
                f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}"
            )

    comparison_lines: List[str] = []
    if not comparison_df.empty:
        for _, row in comparison_df.iterrows():
            comparison_lines.append(
                f"- {row.get('metric_name', '')}: VLM={row.get('vlm_value', '')}, PPStructure={row.get('ppstructure_value', '')}, winner={row.get('winner', '')}, notes={row.get('notes', '')}"
            )

    lines = [
        "# 321B VLM Mapping Benchmark",
        "",
        "## Summary",
        f"- output_dir: `{summary.get('output_dir', '')}`",
        f"- vlm_folder_count: {summary.get('vlm_folder_count', 0)}",
        f"- parsed_json_count: {summary.get('parsed_json_count', 0)}",
        f"- table_ready_count: {summary.get('table_ready_count', 0)}",
        f"- mapped_table_count: {summary.get('mapped_table_count', 0)}",
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
        f"- vlm_benchmark_decision: {summary.get('vlm_benchmark_decision', '')}",
        "",
        "## QA Checks",
    ]
    if qa_lines:
        lines.extend(qa_lines)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## PPStructure Comparison",
        ]
    )
    if comparison_lines:
        lines.extend(comparison_lines)
    else:
        lines.append("- comparison unavailable")

    lines.extend(
        [
            "",
            "## Top Risk Tags",
            f"- {' | '.join(top_risk_tags) if top_risk_tags else 'none'}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_summary_dataframe(summary: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for key, value in summary.items():
        rows.append(
            {
                "metric": key,
                "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value,
            }
        )
    return pd.DataFrame(rows)


def top_risk_tags_from_df(risk_tag_counts_df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
    if risk_tag_counts_df.empty or "risk_tag" not in risk_tag_counts_df.columns:
        return []
    rows: List[Dict[str, Any]] = []
    for _, row in risk_tag_counts_df.head(limit).iterrows():
        rows.append({"risk_tag": _norm(row.get("risk_tag")), "count": int(row.get("count", 0))})
    return rows
