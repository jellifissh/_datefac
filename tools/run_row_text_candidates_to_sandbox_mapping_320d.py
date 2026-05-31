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

from datefac.governance.risk_splitter import split_candidates_for_sandbox_preview
from datefac.governance.row_text_candidate_mapper import (
    candidates_to_dataframe,
    load_320c4_sources,
    map_row_text_candidates,
    resolve_duplicates_and_conflicts,
)


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


def _risk_tag_counts(df: pd.DataFrame) -> pd.DataFrame:
    counts: Dict[str, int] = {}
    if df.empty:
        return pd.DataFrame(columns=["risk_tag", "count"])
    for tags in df["risk_tags"].astype(str).tolist():
        for t in [x.strip() for x in tags.split("|") if x.strip()]:
            counts[t] = counts.get(t, 0) + 1
    rows = [{"risk_tag": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
    return pd.DataFrame(rows)


def _metric_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["metric_code", "count"])
    out = df["metric_code"].astype(str).value_counts().reset_index()
    out.columns = ["metric_code", "count"]
    return out


def _count_risk(df: pd.DataFrame, tag: str) -> int:
    if df.empty:
        return 0
    return int(df["risk_tags"].astype(str).str.contains(rf"(?:^|\|){tag}(?:$|\|)", regex=True).sum())


def _build_blocked_output(input_dir: Path, previous_mapping_dir: Path | None, output_dir: Path, blocked_code: str, blocked_message: str) -> Dict[str, Any]:
    summary = {
        "source_candidate_count": 0,
        "context_enriched_candidate_count": 0,
        "trusted_preview_count": 0,
        "review_required_preview_count": 0,
        "rejected_preview_count": 0,
        "duplicate_same_value_count": 0,
        "conflict_count": 0,
        "unknown_metric_code_count": 0,
        "invalid_year_count": 0,
        "value_missing_count": 0,
        "unit_unknown_count": 0,
        "year_inferred_count": 0,
        "table_header_year_count": 0,
        "smoke_context_year_count": 0,
        "smoke_verified_candidate_count": 0,
        "row_text_only_trusted_count": 0,
        "repaired_trusted_count": 0,
        "risk_tag_counts": {},
        "sandbox_mapping_decision": blocked_code,
        "blocked_message": blocked_message,
        "input_dir": str(input_dir),
        "previous_mapping_dir": str(previous_mapping_dir) if previous_mapping_dir else "",
    }
    summary_df = pd.DataFrame([{"metric": k, "value": v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False)} for k, v in summary.items()])
    empty_df = pd.DataFrame()
    excel_path = output_dir / "row_text_mapping_320d2.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "context_enriched_candidates": empty_df,
            "trusted_preview": empty_df,
            "review_required_preview": empty_df,
            "rejected_preview": empty_df,
            "context_propagation_audit": empty_df,
            "trust_gate_audit": empty_df,
            "smoke_verified_candidates": empty_df,
            "duplicates": empty_df,
            "conflicts": empty_df,
            "risk_tag_counts": pd.DataFrame(columns=["risk_tag", "count"]),
            "metric_counts": pd.DataFrame(columns=["metric_code", "count"]),
            "source_candidate_rows": empty_df,
            "mapping_audit": empty_df,
        },
    )
    _json_dump(output_dir / "row_text_mapping_320d2_summary.json", summary)
    report = output_dir / "row_text_mapping_320d2_report.md"
    report.write_text(
        "\n".join(
            [
                "# 320D2 Context Propagation and Trust Gate Calibration",
                "",
                f"- input_dir: `{input_dir}`",
                f"- previous_mapping_dir: `{previous_mapping_dir}`" if previous_mapping_dir else "- previous_mapping_dir: ``",
                f"- sandbox_mapping_decision: `{blocked_code}`",
                f"- blocked_message: {blocked_message}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {"summary": summary, "excel_path": str(excel_path), "report_md_path": str(report)}


def run_320d2_mapping(input_dir: Path, output_dir: Path, previous_mapping_dir: Path | None = None) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if previous_mapping_dir is not None:
        prev_summary = previous_mapping_dir / "row_text_mapping_320d_summary.json"
        if not prev_summary.exists():
            return _build_blocked_output(
                input_dir=input_dir,
                previous_mapping_dir=previous_mapping_dir,
                output_dir=output_dir,
                blocked_code="BLOCKED_MISSING_320D_INPUT",
                blocked_message=f"missing previous mapping summary: {prev_summary}",
            )

    src = load_320c4_sources(input_dir)
    if src["blocked"]:
        return _build_blocked_output(
            input_dir=input_dir,
            previous_mapping_dir=previous_mapping_dir,
            output_dir=output_dir,
            blocked_code=src["blocked_code"],
            blocked_message=src["blocked_message"],
        )

    source_df = src["source_candidate_rows_df"]
    smoke_ids = src["smoke_passed_candidate_ids"]
    smoke_metric_codes = src["smoke_passed_metric_codes"]
    table_title = src["table_title"]
    table_unit = src["table_unit"]
    table_header_years = set(src["table_header_years"])

    mapped, mapping_audit_rows, context_audit_rows = map_row_text_candidates(
        source_candidate_rows_df=source_df,
        table_title=table_title,
        table_unit=table_unit,
        table_header_years=table_header_years,
        smoke_passed_candidate_ids=smoke_ids,
        smoke_passed_metric_codes=smoke_metric_codes,
    )
    dedup = resolve_duplicates_and_conflicts(mapped)
    canonical = dedup["canonical_candidates"]
    split = split_candidates_for_sandbox_preview(
        candidates=canonical,
        smoke_passed_candidate_source_ids=smoke_ids,
    )

    context_enriched_df = candidates_to_dataframe(canonical)
    trusted_df = candidates_to_dataframe(split["trusted_preview"])
    review_df = candidates_to_dataframe(split["review_required_preview"])
    rejected_df = candidates_to_dataframe(split["rejected_preview"])
    smoke_verified_df = context_enriched_df[context_enriched_df["smoke_check_status"].astype(str) == "PASSED"].copy() if not context_enriched_df.empty else pd.DataFrame()
    context_audit_df = pd.DataFrame(context_audit_rows)
    trust_gate_audit_df = pd.DataFrame(split.get("trust_gate_audit_rows", []))
    duplicates_df = pd.DataFrame(dedup["duplicates_rows"])
    conflicts_df = pd.DataFrame(dedup["conflicts_rows"])
    mapping_audit_df = pd.DataFrame(mapping_audit_rows)

    if duplicates_df.empty:
        duplicates_df = pd.DataFrame(columns=["group_key", "kept_candidate_id", "dropped_candidate_id", "metric_code", "year", "normalized_value", "drop_reason"])
    if conflicts_df.empty:
        conflicts_df = pd.DataFrame(columns=["group_key", "candidate_id", "metric_code", "year", "normalized_value", "confidence", "risk_tags"])
    if context_audit_df.empty:
        context_audit_df = pd.DataFrame(columns=["candidate_id", "metric_code", "year", "year_source", "unit", "unit_source", "table_title", "table_unit", "smoke_check_status", "smoke_check_source", "risk_tags"])
    if trust_gate_audit_df.empty:
        trust_gate_audit_df = pd.DataFrame(columns=["candidate_id", "metric_code", "year", "confidence", "year_source", "unit_source", "smoke_check_status", "decision", "reason", "risk_tags"])
    if smoke_verified_df.empty:
        smoke_verified_df = pd.DataFrame(columns=context_enriched_df.columns.tolist() if not context_enriched_df.empty else [])

    risk_counts_df = _risk_tag_counts(context_enriched_df)
    metric_counts_df = _metric_counts(context_enriched_df)
    risk_tag_counts = {str(r["risk_tag"]): int(r["count"]) for _, r in risk_counts_df.iterrows()} if not risk_counts_df.empty else {}

    source_candidate_count = int(len(source_df))
    context_enriched_candidate_count = int(len(context_enriched_df))
    trusted_preview_count = int(len(trusted_df))
    review_required_preview_count = int(len(review_df))
    rejected_preview_count = int(len(rejected_df))
    duplicate_same_value_count = int(dedup["duplicate_same_value_count"])
    conflict_count = int(dedup["conflict_count"])
    unknown_metric_code_count = _count_risk(context_enriched_df, "UNKNOWN_METRIC_CODE")
    invalid_year_count = _count_risk(context_enriched_df, "INVALID_YEAR") + _count_risk(context_enriched_df, "YEAR_MISSING")
    value_missing_count = _count_risk(context_enriched_df, "VALUE_MISSING")
    unit_unknown_count = _count_risk(context_enriched_df, "UNIT_UNKNOWN")
    year_inferred_count = int((context_enriched_df["year_source"].astype(str) == "INFERRED_SEQUENCE").sum()) if not context_enriched_df.empty else 0
    table_header_year_count = int((context_enriched_df["year_source"].astype(str) == "TABLE_HEADER").sum()) if not context_enriched_df.empty else 0
    smoke_context_year_count = int((context_enriched_df["year_source"].astype(str) == "SMOKE_CHECK_CONTEXT").sum()) if not context_enriched_df.empty else 0
    smoke_verified_candidate_count = int(len(smoke_verified_df))
    row_text_only_trusted_count = _count_risk(trusted_df, "ROW_TEXT_ONLY")
    repaired_trusted_count = _count_risk(trusted_df, "ROW_REPAIRED_CONTINUATION") + _count_risk(trusted_df, "ROW_REPAIRED_VALUES_BEFORE_LABEL")
    noise_leak_count = _count_risk(context_enriched_df, "NOISE_LEAK_BBOX_HTML")

    if noise_leak_count > 0:
        decision = "MAPPING_FAILED_NOISE_LEAK"
    elif conflict_count > 0:
        decision = "MAPPING_READY_WITH_REVIEW_REQUIRED_CONFLICTS"
    elif context_enriched_candidate_count >= 50 and trusted_preview_count >= 50 and rejected_preview_count == 0 and conflict_count == 0:
        decision = "ROW_TEXT_MAPPING_READY_FOR_320E_SANDBOX_INTEGRATION"
    elif trusted_preview_count > 0 and review_required_preview_count > 0:
        decision = "ROW_TEXT_MAPPING_TRUST_GATE_CALIBRATED_NEEDS_REVIEW_QUEUE"
    else:
        decision = "ROW_TEXT_MAPPING_CONTEXT_PROPAGATION_NOT_READY"

    summary_payload = {
        "source_candidate_count": source_candidate_count,
        "context_enriched_candidate_count": context_enriched_candidate_count,
        "trusted_preview_count": trusted_preview_count,
        "review_required_preview_count": review_required_preview_count,
        "rejected_preview_count": rejected_preview_count,
        "duplicate_same_value_count": duplicate_same_value_count,
        "conflict_count": conflict_count,
        "unknown_metric_code_count": unknown_metric_code_count,
        "invalid_year_count": invalid_year_count,
        "value_missing_count": value_missing_count,
        "unit_unknown_count": unit_unknown_count,
        "year_inferred_count": year_inferred_count,
        "table_header_year_count": table_header_year_count,
        "smoke_context_year_count": smoke_context_year_count,
        "smoke_verified_candidate_count": smoke_verified_candidate_count,
        "row_text_only_trusted_count": row_text_only_trusted_count,
        "repaired_trusted_count": repaired_trusted_count,
        "risk_tag_counts": risk_tag_counts,
        "sandbox_mapping_decision": decision,
    }
    summary_df = pd.DataFrame(
        [{"metric": k, "value": v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False)} for k, v in summary_payload.items()]
    )

    excel_path = output_dir / "row_text_mapping_320d2.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "context_enriched_candidates": context_enriched_df,
            "trusted_preview": trusted_df,
            "review_required_preview": review_df,
            "rejected_preview": rejected_df,
            "context_propagation_audit": context_audit_df,
            "trust_gate_audit": trust_gate_audit_df,
            "smoke_verified_candidates": smoke_verified_df,
            "duplicates": duplicates_df,
            "conflicts": conflicts_df,
            "risk_tag_counts": risk_counts_df,
            "metric_counts": metric_counts_df,
            "source_candidate_rows": source_df,
            "mapping_audit": mapping_audit_df,
        },
    )

    summary_json = output_dir / "row_text_mapping_320d2_summary.json"
    _json_dump(summary_json, summary_payload)

    report_path = output_dir / "row_text_mapping_320d2_report.md"
    report_lines = [
        "# 320D2 Context Propagation and Trust Gate Calibration",
        "",
        f"- input_dir: `{input_dir}`",
        f"- previous_mapping_dir: `{previous_mapping_dir}`" if previous_mapping_dir else "- previous_mapping_dir: ``",
        f"- source_candidate_count: {source_candidate_count}",
        f"- context_enriched_candidate_count: {context_enriched_candidate_count}",
        f"- trusted_preview_count: {trusted_preview_count}",
        f"- review_required_preview_count: {review_required_preview_count}",
        f"- rejected_preview_count: {rejected_preview_count}",
        f"- unit_unknown_count: {unit_unknown_count}",
        f"- year_inferred_count: {year_inferred_count}",
        f"- smoke_verified_candidate_count: {smoke_verified_candidate_count}",
        f"- row_text_only_trusted_count: {row_text_only_trusted_count}",
        f"- repaired_trusted_count: {repaired_trusted_count}",
        f"- sandbox_mapping_decision: {decision}",
        "",
        "## Output",
        f"- excel: `{excel_path}`",
        f"- summary_json: `{summary_json}`",
        f"- report_md: `{report_path}`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    for name, df in [
        ("context_enriched_candidates.jsonl", context_enriched_df),
        ("trusted_preview.jsonl", trusted_df),
        ("review_required_preview.jsonl", review_df),
    ]:
        p = output_dir / name
        with p.open("w", encoding="utf-8") as f:
            for _, r in df.iterrows():
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    return {
        "summary": summary_payload,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json),
        "report_md_path": str(report_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 320D2 context propagation and trust gate calibration.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--previous-mapping-dir", required=False, default="")
    args = parser.parse_args()

    prev = Path(args.previous_mapping_dir) if _norm(args.previous_mapping_dir) else None
    result = run_320d2_mapping(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        previous_mapping_dir=prev,
    )
    s = result["summary"]
    print(f"row_text_mapping_excel: {result['excel_path']}")
    print(f"row_text_mapping_summary_json: {result.get('summary_json_path', '')}")
    print(f"row_text_mapping_report_md: {result['report_md_path']}")
    print(f"source_candidate_count: {s.get('source_candidate_count', 0)}")
    print(f"context_enriched_candidate_count: {s.get('context_enriched_candidate_count', 0)}")
    print(f"trusted_preview_count: {s.get('trusted_preview_count', 0)}")
    print(f"review_required_preview_count: {s.get('review_required_preview_count', 0)}")
    print(f"rejected_preview_count: {s.get('rejected_preview_count', 0)}")
    print(f"unit_unknown_count: {s.get('unit_unknown_count', 0)}")
    print(f"year_inferred_count: {s.get('year_inferred_count', 0)}")
    print(f"smoke_verified_candidate_count: {s.get('smoke_verified_candidate_count', 0)}")
    print(f"row_text_only_trusted_count: {s.get('row_text_only_trusted_count', 0)}")
    print(f"repaired_trusted_count: {s.get('repaired_trusted_count', 0)}")
    print(f"sandbox_mapping_decision: {s.get('sandbox_mapping_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
