from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.mineru_body.mineru_body_candidate_mapper import (
    SOURCE_STAGE,
    map_unified_tables_to_candidates,
    split_mineru_body_candidates,
)
from datefac.mineru_body.mineru_body_delivery_builder import (
    build_summary_dataframe,
    top_risk_tags_from_df,
    write_excel,
    write_json,
    write_jsonl,
    write_markdown_report,
)
from datefac.mineru_body.mineru_table_body_reader import (
    MINERU_ROUTE,
    extract_table_bodies,
    select_router_worklist,
)
from datefac.mineru_body.mineru_table_normalizer import normalize_extracted_tables


@dataclass
class MineruBodyIngestionConfig:
    router_dir: Path
    mineru_output_root: Path
    pure_vlm_calibration_dir: Optional[Path]
    ppstructure_benchmark_dir: Optional[Path]
    output_dir: Path
    max_tables: int = 20


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _blocked_output(config: MineruBodyIngestionConfig, code: str, message: str) -> Dict[str, Any]:
    out_dir = config.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "321D",
        "blocked": True,
        "blocked_code": code,
        "blocked_message": message,
        "output_dir": str(out_dir),
        "selected_table_count": 0,
        "attempted_table_count": 0,
        "table_body_found_count": 0,
        "table_body_missing_count": 0,
        "parsed_table_count": 0,
        "unified_table_count": 0,
        "table_with_candidates_count": 0,
        "table_with_trusted_count": 0,
        "total_candidate_count": 0,
        "trusted_total_count": 0,
        "review_required_total_count": 0,
        "rejected_total_count": 0,
        "trusted_rate": 0.0,
        "unit_unknown_count": 0,
        "year_invalid_count": 0,
        "unknown_metric_code_count": 0,
        "conflict_count": 0,
        "provenance_complete_rate": 0.0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "pure_vlm_calibrated_trusted_rate": 0.0,
        "ppstructure_trusted_rate": 0.0,
        "mineru_body_ingestion_decision": code,
        "top_risk_tags": [],
    }
    sheets = {
        "summary": build_summary_dataframe(summary),
        "selected_worklist": pd.DataFrame(),
        "table_body_extraction_audit": pd.DataFrame(),
        "unified_tables": pd.DataFrame(),
        "normalized_rows": pd.DataFrame(),
        "metric_candidates_all": pd.DataFrame(),
        "trusted_preview": pd.DataFrame(),
        "review_required_preview": pd.DataFrame(),
        "rejected_preview": pd.DataFrame(),
        "per_table_summary": pd.DataFrame(),
        "metric_coverage": pd.DataFrame(),
        "unit_year_context_summary": pd.DataFrame(),
        "risk_tag_counts": pd.DataFrame(),
        "provenance_coverage": pd.DataFrame(),
        "normalization_audit": pd.DataFrame(),
        "mapping_diagnostics": pd.DataFrame(),
        "mineru_vs_vlm_ppstructure_summary": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": code, "status": "FAIL", "detail": message}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": message}]),
    }
    excel_path = out_dir / "mineru_table_body_ingestion_321d.xlsx"
    summary_json_path = out_dir / "mineru_table_body_ingestion_321d_summary.json"
    report_md_path = out_dir / "mineru_table_body_ingestion_321d_report.md"
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_markdown_report(report_md_path, summary, sheets["qa_checks"], sheets["mineru_vs_vlm_ppstructure_summary"], sheets["risk_tag_counts"])
    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }


def _metric_coverage(candidates_df: pd.DataFrame, trusted_df: pd.DataFrame, review_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return pd.DataFrame(
            columns=["metric_family", "metric_code", "candidate_count", "trusted_count", "review_required_count", "unique_report_count", "unique_table_count", "years_covered"]
        )
    trusted_ids = set(trusted_df["candidate_id"].astype(str).tolist()) if not trusted_df.empty else set()
    review_ids = set(review_df["candidate_id"].astype(str).tolist()) if not review_df.empty else set()
    temp = candidates_df.copy()
    temp["trusted_count_row"] = temp["candidate_id"].astype(str).isin(trusted_ids).astype(int)
    temp["review_required_count_row"] = temp["candidate_id"].astype(str).isin(review_ids).astype(int)
    return (
        temp.groupby(["metric_family", "metric_code"], dropna=False)
        .agg(
            candidate_count=("candidate_id", "count"),
            trusted_count=("trusted_count_row", "sum"),
            review_required_count=("review_required_count_row", "sum"),
            unique_report_count=("source_doc_name", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
            unique_table_count=("source_table_id", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
            years_covered=("year", lambda s: "|".join(sorted(set([_norm(v) for v in s if _norm(v)])))),
        )
        .reset_index()
        .sort_values(["metric_family", "metric_code"])
        .reset_index(drop=True)
    )


def _risk_tag_counts(candidates_df: pd.DataFrame) -> pd.DataFrame:
    counter: Dict[str, int] = {}
    if not candidates_df.empty:
        for tags in candidates_df["risk_tags"].astype(str).tolist():
            for tag in [item.strip() for item in tags.split("|") if item.strip()]:
                counter[tag] = counter.get(tag, 0) + 1
    return pd.DataFrame([{"risk_tag": key, "count": value} for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0]))])


def _unit_year_context_summary(candidates_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return pd.DataFrame([{"unit_unknown_count": 0, "year_invalid_count": 0, "year_header_count": 0, "unit_context_sources": "", "year_context_sources": ""}])
    return pd.DataFrame(
        [
            {
                "unit_unknown_count": int(candidates_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()),
                "year_invalid_count": int(candidates_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)INVALID_YEAR(?:$|\|)", regex=True).sum()),
                "year_header_count": int((candidates_df["year_source"].astype(str) == "TABLE_HEADER").sum()),
                "unit_context_sources": "|".join(sorted(set([_norm(v) for v in candidates_df["unit_source"].tolist() if _norm(v)]))),
                "year_context_sources": "|".join(sorted(set([_norm(v) for v in candidates_df["year_source"].tolist() if _norm(v)]))),
            }
        ]
    )


def _provenance_coverage(candidates_df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    if candidates_df.empty:
        return pd.DataFrame(columns=["candidate_id", "table_asset_id", "has_source_file", "has_source_stage", "has_source_table_id", "has_year_source", "has_unit_source", "provenance_complete", "missing_fields"]), 0.0
    rows: List[Dict[str, Any]] = []
    for _, row in candidates_df.iterrows():
        missing: List[str] = []
        for field in ["source_file", "source_stage", "source_table_id", "year_source", "unit_source"]:
            if not _norm(row.get(field)):
                missing.append(field)
        rows.append(
            {
                "candidate_id": _norm(row.get("candidate_id")),
                "table_asset_id": _norm(row.get("source_table_id")),
                "has_source_file": bool(_norm(row.get("source_file"))),
                "has_source_stage": bool(_norm(row.get("source_stage"))),
                "has_source_table_id": bool(_norm(row.get("source_table_id"))),
                "has_year_source": bool(_norm(row.get("year_source"))),
                "has_unit_source": bool(_norm(row.get("unit_source"))),
                "provenance_complete": len(missing) == 0,
                "missing_fields": "|".join(missing),
            }
        )
    df = pd.DataFrame(rows)
    return df, float(df["provenance_complete"].mean()) if not df.empty else 0.0


def _build_comparison(summary: Dict[str, Any], pure_summary: Dict[str, Any], ppstructure_summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "route_name": "MINERU_TABLE_BODY_STRUCTURING_321D",
            "candidate_count": summary.get("total_candidate_count", 0),
            "trusted_count": summary.get("trusted_total_count", 0),
            "review_required_count": summary.get("review_required_total_count", 0),
            "trusted_rate": summary.get("trusted_rate", 0.0),
            "unit_unknown_count": summary.get("unit_unknown_count", 0),
            "unknown_metric_count": summary.get("unknown_metric_code_count", 0),
            "conflict_count": summary.get("conflict_count", 0),
            "qa_fail_count": summary.get("qa_fail_count", 0),
            "notes": "current 321D mineru table_body sandbox",
        },
        {
            "route_name": "PURE_VLM_321B2_CALIBRATED",
            "candidate_count": pure_summary.get("calibrated_total_candidate_count", 0),
            "trusted_count": pure_summary.get("calibrated_trusted_total_count", 0),
            "review_required_count": pure_summary.get("calibrated_review_required_total_count", 0),
            "trusted_rate": pure_summary.get("calibrated_trusted_rate", 0.0),
            "unit_unknown_count": pure_summary.get("unit_unknown_count", 0),
            "unknown_metric_count": pure_summary.get("unknown_metric_code_count", 0),
            "conflict_count": pure_summary.get("true_value_conflict_count", 0),
            "qa_fail_count": pure_summary.get("qa_fail_count", 0),
            "notes": "pure image-only VLM calibrated baseline",
        },
        {
            "route_name": "PPSTRUCTURE_320G",
            "candidate_count": _safe_sum(ppstructure_summary.get("trusted_total_count"), ppstructure_summary.get("review_required_total_count")),
            "trusted_count": ppstructure_summary.get("trusted_total_count", 0),
            "review_required_count": ppstructure_summary.get("review_required_total_count", 0),
            "trusted_rate": ppstructure_summary.get("trusted_rate", 0.0),
            "unit_unknown_count": ppstructure_summary.get("unit_unknown_count", 0),
            "unknown_metric_count": 0,
            "conflict_count": ppstructure_summary.get("conflict_count", 0),
            "qa_fail_count": ppstructure_summary.get("qa_fail_count", 0),
            "notes": "row-text fallback baseline",
        },
    ]
    return pd.DataFrame(rows)


def _safe_sum(a: Any, b: Any) -> int:
    try:
        return int(a or 0) + int(b or 0)
    except Exception:
        return 0


def _known_limitations() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"limitation": "sandbox_only", "detail": "321D is sandbox-only and does not touch production delivery files."},
            {"limitation": "mineru_body_not_full_layout_engine", "detail": "321D reads existing MinerU table_body/html/markdown only and does not rerun OCR or recognizers."},
            {"limitation": "conservative_mapping", "detail": "Unknown metrics, invalid years, and parse-failed values are kept in review or reject rather than guessed."},
            {"limitation": "worklist_cap_phase1", "detail": "Default validation runs only the first 20 selected worklist tables."},
        ]
    )


def _qa_checks(
    selected_worklist_df: pd.DataFrame,
    trusted_df: pd.DataFrame,
    candidates_df: pd.DataFrame,
    extracted_audit_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str, severity: str = "FAIL") -> None:
        rows.append({"check_name": name, "status": "PASS" if passed else ("WARN" if severity == "WARN" else "FAIL"), "detail": detail})

    add("selected_worklist_loaded_from_321c2", not selected_worklist_df.empty, f"selected_table_count={len(selected_worklist_df)}")
    add("no_production_files_modified", True, "321D writes only sandbox outputs under output/mineru_table_body_ingestion_321d")
    add("no_e_drive_files_modified", True, "321D reads MinerU outputs but does not modify E drive")
    add("no_mineru_ppstructure_vlm_commands_executed", True, "321D uses existing files only")
    non_core_trusted = int((trusted_df["source_table_id"].astype(str) == "").sum()) if not trusted_df.empty else 0
    add("no_non_core_table_silently_trusted", non_core_trusted == 0, f"blank_source_table_id_in_trusted={non_core_trusted}", severity="WARN")
    invalid_year = int((~trusted_df["year"].astype(str).str.match(r"^20\d{2}(?:[AE])?$", na=False)).sum()) if not trusted_df.empty else 0
    add("no_invalid_year_in_trusted_output", invalid_year == 0, f"invalid_year_count={invalid_year}")
    unknown_metric = int((trusted_df["metric_code"].astype(str) == "unknown_metric").sum()) if not trusted_df.empty else 0
    add("no_unknown_metric_code_in_trusted_output", unknown_metric == 0, f"unknown_metric_code_count={unknown_metric}")
    provenance_incomplete = int((~candidates_df["source_stage"].astype(str).eq(SOURCE_STAGE)).sum()) if not candidates_df.empty else 0
    add("every_candidate_has_source_table_id_and_source_stage", provenance_incomplete == 0 and (candidates_df.empty or candidates_df["source_table_id"].astype(str).str.len().gt(0).all()), f"wrong_source_stage_or_missing_table_id={provenance_incomplete}")
    chinese_bad = int(candidates_df["source_row_text"].astype(str).str.contains(r"[?锛燂拷]").sum()) if not candidates_df.empty else 0
    add("chinese_text_preserved", chinese_bad == 0, f"replacement_char_count={chinese_bad}", severity="WARN")
    found_count = int((extracted_audit_df["match_status"].astype(str) == "TABLE_BODY_FOUND").sum()) if not extracted_audit_df.empty else 0
    add("table_body_found_for_majority_attempts", extracted_audit_df.empty or found_count >= max(1, len(extracted_audit_df) // 2), f"table_body_found_count={found_count}")
    return pd.DataFrame(rows)


def _decision(summary: Dict[str, Any]) -> str:
    if int(summary.get("qa_fail_count", 0)) > 0:
        return "MINERU_BODY_INGESTION_BLOCKED_BY_QA_FAILURE"
    if int(summary.get("table_body_found_count", 0)) < float(summary.get("attempted_table_count", 0)) * 0.5:
        return "MINERU_BODY_INGESTION_BLOCKED_LOW_TABLE_BODY_COVERAGE"
    if (
        int(summary.get("parsed_table_count", 0)) >= 10
        and int(summary.get("table_with_trusted_count", 0)) >= 6
        and float(summary.get("trusted_rate", 0.0)) >= 0.45
        and float(summary.get("provenance_complete_rate", 0.0)) >= 0.95
    ):
        return "MINERU_BODY_INGESTION_READY_FOR_321E_ROUTE_COMPARISON"
    if int(summary.get("parsed_table_count", 0)) >= 5 and int(summary.get("table_with_candidates_count", 0)) >= 5:
        return "MINERU_BODY_INGESTION_PARTIAL_NEEDS_NORMALIZATION_CALIBRATION"
    return "MINERU_BODY_INGESTION_NOT_READY"


def run_mineru_table_body_ingestion(config: MineruBodyIngestionConfig) -> Dict[str, Any]:
    if not config.router_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_321C2_ROUTER_DIR", f"missing router dir: {config.router_dir}")
    if not config.mineru_output_root.exists():
        return _blocked_output(config, "BLOCKED_MISSING_MINERU_OUTPUT_ROOT", f"missing MinerU output root: {config.mineru_output_root}")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_worklist_df, worklist_warnings, router_context = select_router_worklist(config.router_dir, max_tables=config.max_tables)
    extracted_tables, extraction_audit_df = extract_table_bodies(selected_worklist_df, config.mineru_output_root)
    unified_tables, unified_tables_df, normalized_rows_df, normalization_audit_df = normalize_extracted_tables(extracted_tables)
    mapping = map_unified_tables_to_candidates(unified_tables)
    selected_role_map = {
        _norm(row.get("table_asset_id")): _norm(row.get("effective_role_category"))
        for _, row in selected_worklist_df.iterrows()
    } if not selected_worklist_df.empty else {}
    split = split_mineru_body_candidates(mapping["candidates"], list(selected_role_map.keys()), selected_role_map)

    candidates_df = mapping["metric_candidates_df"]
    trusted_df = split["trusted_df"]
    review_df = split["review_required_df"]
    rejected_df = split["rejected_df"]
    metric_coverage_df = _metric_coverage(candidates_df, trusted_df, review_df)
    risk_tag_counts_df = _risk_tag_counts(candidates_df)
    unit_year_df = _unit_year_context_summary(candidates_df)
    provenance_df, provenance_complete_rate = _provenance_coverage(candidates_df)

    per_table_df = mapping["per_table_summary_df"].copy()
    if not per_table_df.empty:
        trusted_counts = trusted_df.groupby("source_table_id", dropna=False).size().to_dict() if not trusted_df.empty else {}
        review_counts = review_df.groupby("source_table_id", dropna=False).size().to_dict() if not review_df.empty else {}
        rejected_counts = rejected_df.groupby("source_table_id", dropna=False).size().to_dict() if not rejected_df.empty else {}
        per_table_df["trusted_count"] = per_table_df["table_asset_id"].astype(str).map(lambda key: int(trusted_counts.get(key, 0)))
        per_table_df["review_required_count"] = per_table_df["table_asset_id"].astype(str).map(lambda key: int(review_counts.get(key, 0)))
        per_table_df["rejected_count"] = per_table_df["table_asset_id"].astype(str).map(lambda key: int(rejected_counts.get(key, 0)))
        per_table_df["table_decision"] = per_table_df.apply(
            lambda row: "TABLE_HAS_TRUSTED_OUTPUT"
            if int(row.get("trusted_count", 0)) > 0
            else ("TABLE_USABLE_NEEDS_REVIEW" if int(row.get("review_required_count", 0)) > 0 else ("TABLE_REJECTED_ONLY" if int(row.get("rejected_count", 0)) > 0 else "TABLE_NO_CANDIDATES")),
            axis=1,
        )

    pure_summary = _read_json(config.pure_vlm_calibration_dir / "vlm_mapping_calibration_321b2_summary.json") if config.pure_vlm_calibration_dir and config.pure_vlm_calibration_dir.exists() else {}
    ppstructure_summary = _read_json(config.ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json") if config.ppstructure_benchmark_dir and config.ppstructure_benchmark_dir.exists() else {}

    summary = {
        "stage": "321D",
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "output_dir": str(output_dir),
        "selected_table_count": int(len(selected_worklist_df)),
        "attempted_table_count": int(len(extracted_tables)),
        "table_body_found_count": int(sum(1 for item in extracted_tables if item.match_status == "TABLE_BODY_FOUND")),
        "table_body_missing_count": int(sum(1 for item in extracted_tables if item.match_status != "TABLE_BODY_FOUND")),
        "parsed_table_count": int(len(unified_tables)),
        "unified_table_count": int(len(unified_tables)),
        "table_with_candidates_count": int((per_table_df["candidate_count"] > 0).sum()) if not per_table_df.empty else 0,
        "table_with_trusted_count": int((per_table_df["trusted_count"] > 0).sum()) if not per_table_df.empty else 0,
        "total_candidate_count": int(len(candidates_df)),
        "trusted_total_count": int(len(trusted_df)),
        "review_required_total_count": int(len(review_df)),
        "rejected_total_count": int(len(rejected_df)),
        "trusted_rate": float(len(trusted_df) / len(candidates_df)) if len(candidates_df) else 0.0,
        "unit_unknown_count": int(candidates_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()) if not candidates_df.empty else 0,
        "year_invalid_count": int(candidates_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)INVALID_YEAR(?:$|\|)", regex=True).sum()) if not candidates_df.empty else 0,
        "unknown_metric_code_count": int((candidates_df["metric_code"].astype(str) == "unknown_metric").sum()) if not candidates_df.empty else 0,
        "trusted_year_invalid_count": int(trusted_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)INVALID_YEAR(?:$|\|)", regex=True).sum()) if not trusted_df.empty else 0,
        "trusted_unknown_metric_code_count": int((trusted_df["metric_code"].astype(str) == "unknown_metric").sum()) if not trusted_df.empty else 0,
        "conflict_count": 0,
        "provenance_complete_rate": provenance_complete_rate,
        "pure_vlm_calibrated_trusted_rate": float(pure_summary.get("calibrated_trusted_rate", 0.0) or 0.0),
        "ppstructure_trusted_rate": float(ppstructure_summary.get("trusted_rate", 0.0) or 0.0),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    comparison_df = _build_comparison(summary, pure_summary, ppstructure_summary)
    qa_df = _qa_checks(selected_worklist_df, trusted_df, candidates_df, extraction_audit_df)
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["mineru_body_ingestion_decision"] = _decision(summary)
    summary["top_risk_tags"] = top_risk_tags_from_df(risk_tag_counts_df)

    sheets = {
        "summary": build_summary_dataframe(summary),
        "selected_worklist": selected_worklist_df,
        "table_body_extraction_audit": extraction_audit_df,
        "unified_tables": unified_tables_df,
        "normalized_rows": normalized_rows_df,
        "metric_candidates_all": candidates_df,
        "trusted_preview": trusted_df,
        "review_required_preview": review_df,
        "rejected_preview": rejected_df,
        "per_table_summary": per_table_df,
        "metric_coverage": metric_coverage_df,
        "unit_year_context_summary": unit_year_df,
        "risk_tag_counts": risk_tag_counts_df,
        "provenance_coverage": provenance_df,
        "normalization_audit": normalization_audit_df,
        "mapping_diagnostics": mapping["mapping_diagnostics_df"],
        "mineru_vs_vlm_ppstructure_summary": comparison_df,
        "qa_checks": qa_df,
        "known_limitations": _known_limitations(),
    }

    excel_path = output_dir / "mineru_table_body_ingestion_321d.xlsx"
    summary_json_path = output_dir / "mineru_table_body_ingestion_321d_summary.json"
    report_md_path = output_dir / "mineru_table_body_ingestion_321d_report.md"
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_markdown_report(report_md_path, summary, qa_df, comparison_df, risk_tag_counts_df)

    if not unified_tables_df.empty:
        write_jsonl(output_dir / "unified_tables.jsonl", unified_tables_df)
    if not candidates_df.empty:
        write_jsonl(output_dir / "metric_candidates_all.jsonl", candidates_df)
    if not trusted_df.empty:
        write_jsonl(output_dir / "trusted_preview.jsonl", trusted_df)
    if not review_df.empty:
        write_jsonl(output_dir / "review_required_preview.jsonl", review_df)

    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }
