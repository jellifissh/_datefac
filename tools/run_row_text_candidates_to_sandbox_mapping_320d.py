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


def _build_blocked_output(input_dir: Path, output_dir: Path, blocked_code: str, blocked_message: str) -> Dict[str, Any]:
    summary = {
        "source_candidate_count": 0,
        "normalized_candidate_count": 0,
        "trusted_preview_count": 0,
        "review_required_preview_count": 0,
        "rejected_preview_count": 0,
        "duplicate_same_value_count": 0,
        "conflict_count": 0,
        "unknown_metric_code_count": 0,
        "invalid_year_count": 0,
        "value_missing_count": 0,
        "unit_unknown_count": 0,
        "risk_tag_counts": {},
        "sandbox_mapping_decision": blocked_code,
        "blocked_message": blocked_message,
        "input_dir": str(input_dir),
    }
    summary_df = pd.DataFrame([{"metric": k, "value": v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False)} for k, v in summary.items()])
    empty_norm = pd.DataFrame()
    excel_path = output_dir / "row_text_mapping_320d.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "normalized_candidates": empty_norm,
            "trusted_preview": empty_norm,
            "review_required_preview": empty_norm,
            "rejected_preview": empty_norm,
            "duplicates": empty_norm,
            "conflicts": empty_norm,
            "risk_tag_counts": pd.DataFrame(columns=["risk_tag", "count"]),
            "metric_counts": pd.DataFrame(columns=["metric_code", "count"]),
            "source_candidate_rows": empty_norm,
            "mapping_audit": empty_norm,
        },
    )
    _json_dump(output_dir / "row_text_mapping_320d_summary.json", summary)
    report = output_dir / "row_text_mapping_320d_report.md"
    report.write_text(
        "\n".join(
            [
                "# 320D Row-Text Candidates to Sandbox Mapping",
                "",
                f"- input_dir: `{input_dir}`",
                f"- sandbox_mapping_decision: `{blocked_code}`",
                f"- blocked_message: {blocked_message}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {"summary": summary, "excel_path": str(excel_path), "report_md_path": str(report)}


def run_320d_mapping(input_dir: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    src = load_320c4_sources(input_dir)
    if src["blocked"]:
        return _build_blocked_output(
            input_dir=input_dir,
            output_dir=output_dir,
            blocked_code=src["blocked_code"],
            blocked_message=src["blocked_message"],
        )

    source_df = src["source_candidate_rows_df"]
    smoke_ids = src["smoke_passed_candidate_ids"]
    mapped, mapping_audit_rows = map_row_text_candidates(source_df)
    dedup = resolve_duplicates_and_conflicts(mapped)
    canonical = dedup["canonical_candidates"]
    split = split_candidates_for_sandbox_preview(
        candidates=canonical,
        smoke_passed_candidate_source_ids=smoke_ids,
    )

    normalized_df = candidates_to_dataframe(canonical)
    trusted_df = candidates_to_dataframe(split["trusted_preview"])
    review_df = candidates_to_dataframe(split["review_required_preview"])
    rejected_df = candidates_to_dataframe(split["rejected_preview"])
    duplicates_df = pd.DataFrame(dedup["duplicates_rows"])
    conflicts_df = pd.DataFrame(dedup["conflicts_rows"])
    mapping_audit_df = pd.DataFrame(mapping_audit_rows)

    if duplicates_df.empty:
        duplicates_df = pd.DataFrame(columns=["group_key", "kept_candidate_id", "dropped_candidate_id", "metric_code", "year", "normalized_value", "drop_reason"])
    if conflicts_df.empty:
        conflicts_df = pd.DataFrame(columns=["group_key", "candidate_id", "metric_code", "year", "normalized_value", "confidence", "risk_tags"])

    risk_counts_df = _risk_tag_counts(normalized_df)
    metric_counts_df = _metric_counts(normalized_df)
    risk_tag_counts = {}
    if not risk_counts_df.empty:
        risk_tag_counts = {str(r["risk_tag"]): int(r["count"]) for _, r in risk_counts_df.iterrows()}

    def _count_risk(tag: str) -> int:
        if normalized_df.empty:
            return 0
        return int(normalized_df["risk_tags"].astype(str).str.contains(rf"(?:^|\|){tag}(?:$|\|)", regex=True).sum())

    source_candidate_count = int(len(source_df))
    normalized_candidate_count = int(len(normalized_df))
    trusted_preview_count = int(len(trusted_df))
    review_required_preview_count = int(len(review_df))
    rejected_preview_count = int(len(rejected_df))
    duplicate_same_value_count = int(dedup["duplicate_same_value_count"])
    conflict_count = int(dedup["conflict_count"])
    unknown_metric_code_count = _count_risk("UNKNOWN_METRIC_CODE")
    invalid_year_count = _count_risk("INVALID_YEAR") + _count_risk("YEAR_MISSING")
    value_missing_count = _count_risk("VALUE_MISSING")
    unit_unknown_count = _count_risk("UNIT_UNKNOWN")
    noise_leak_count = _count_risk("NOISE_LEAK_BBOX_HTML")

    if noise_leak_count > 0:
        decision = "MAPPING_FAILED_NOISE_LEAK"
    elif conflict_count > 0:
        decision = "MAPPING_READY_WITH_REVIEW_REQUIRED_CONFLICTS"
    elif normalized_candidate_count >= 50 and trusted_preview_count >= 30 and rejected_preview_count == 0:
        decision = "ROW_TEXT_MAPPING_READY_FOR_320E_SANDBOX_INTEGRATION"
    elif normalized_candidate_count >= 20 and review_required_preview_count > 0:
        decision = "ROW_TEXT_MAPPING_USABLE_NEEDS_REVIEW_GATE"
    else:
        decision = "ROW_TEXT_MAPPING_NOT_READY"

    summary_payload = {
        "source_candidate_count": source_candidate_count,
        "normalized_candidate_count": normalized_candidate_count,
        "trusted_preview_count": trusted_preview_count,
        "review_required_preview_count": review_required_preview_count,
        "rejected_preview_count": rejected_preview_count,
        "duplicate_same_value_count": duplicate_same_value_count,
        "conflict_count": conflict_count,
        "unknown_metric_code_count": unknown_metric_code_count,
        "invalid_year_count": invalid_year_count,
        "value_missing_count": value_missing_count,
        "unit_unknown_count": unit_unknown_count,
        "risk_tag_counts": risk_tag_counts,
        "sandbox_mapping_decision": decision,
    }
    summary_df = pd.DataFrame(
        [{"metric": k, "value": v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False)} for k, v in summary_payload.items()]
    )

    excel_path = output_dir / "row_text_mapping_320d.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "normalized_candidates": normalized_df,
            "trusted_preview": trusted_df,
            "review_required_preview": review_df,
            "rejected_preview": rejected_df,
            "duplicates": duplicates_df,
            "conflicts": conflicts_df,
            "risk_tag_counts": risk_counts_df,
            "metric_counts": metric_counts_df,
            "source_candidate_rows": source_df,
            "mapping_audit": mapping_audit_df,
        },
    )

    summary_json = output_dir / "row_text_mapping_320d_summary.json"
    _json_dump(summary_json, summary_payload)

    report_path = output_dir / "row_text_mapping_320d_report.md"
    report_lines = [
        "# 320D Row-Text Candidates to Sandbox Mapping",
        "",
        f"- input_dir: `{input_dir}`",
        f"- source_candidate_count: {source_candidate_count}",
        f"- normalized_candidate_count: {normalized_candidate_count}",
        f"- trusted_preview_count: {trusted_preview_count}",
        f"- review_required_preview_count: {review_required_preview_count}",
        f"- rejected_preview_count: {rejected_preview_count}",
        f"- duplicate_same_value_count: {duplicate_same_value_count}",
        f"- conflict_count: {conflict_count}",
        f"- unknown_metric_code_count: {unknown_metric_code_count}",
        f"- unit_unknown_count: {unit_unknown_count}",
        f"- sandbox_mapping_decision: {decision}",
        "",
        "## Output",
        f"- excel: `{excel_path}`",
        f"- summary_json: `{summary_json}`",
        f"- report_md: `{report_path}`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    for name, df in [
        ("normalized_candidates.jsonl", normalized_df),
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
    parser = argparse.ArgumentParser(description="Map 320C4 row-text candidates into sandbox metric mapping (320D).")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_320d_mapping(Path(args.input_dir), Path(args.output_dir))
    s = result["summary"]
    print(f"row_text_mapping_excel: {result['excel_path']}")
    print(f"row_text_mapping_summary_json: {result.get('summary_json_path', '')}")
    print(f"row_text_mapping_report_md: {result['report_md_path']}")
    print(f"source_candidate_count: {s.get('source_candidate_count', 0)}")
    print(f"normalized_candidate_count: {s.get('normalized_candidate_count', 0)}")
    print(f"trusted_preview_count: {s.get('trusted_preview_count', 0)}")
    print(f"review_required_preview_count: {s.get('review_required_preview_count', 0)}")
    print(f"rejected_preview_count: {s.get('rejected_preview_count', 0)}")
    print(f"duplicate_same_value_count: {s.get('duplicate_same_value_count', 0)}")
    print(f"conflict_count: {s.get('conflict_count', 0)}")
    print(f"unknown_metric_code_count: {s.get('unknown_metric_code_count', 0)}")
    print(f"unit_unknown_count: {s.get('unit_unknown_count', 0)}")
    print(f"sandbox_mapping_decision: {s.get('sandbox_mapping_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
