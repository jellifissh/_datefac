from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.vlm.vlm_candidate_mapper import (
    candidates_to_dataframe,
    map_vlm_outputs_to_candidates,
    resolve_vlm_duplicates_and_conflicts,
    split_vlm_candidates_for_sandbox_preview,
)
from datefac.vlm.vlm_delivery_builder import (
    build_summary_dataframe,
    top_risk_tags_from_df,
    write_excel,
    write_json,
    write_jsonl,
    write_markdown_report,
)
from datefac.vlm.vlm_output_reader import scan_vlm_output_root


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _empty_df(columns: Sequence[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_sheet_safe(path: Path, sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def _load_quality_inputs(quality_dir: Path) -> Dict[str, Any]:
    summary_json = quality_dir / "vlm_output_quality_321a_summary.json"
    workbook = quality_dir / "vlm_output_quality_321a.xlsx"
    summary = _read_json(summary_json)
    inventory_df = _read_sheet_safe(workbook, "table_inventory")
    schema_errors_df = _read_sheet_safe(workbook, "schema_errors")
    row_quality_df = _read_sheet_safe(workbook, "row_quality")
    return {
        "summary": summary,
        "inventory_df": inventory_df,
        "schema_errors_df": schema_errors_df,
        "row_quality_df": row_quality_df,
    }


def _table_inventory_from_records(folder_records: Sequence[Any], quality_inventory_df: pd.DataFrame) -> pd.DataFrame:
    lookup: Dict[str, Dict[str, Any]] = {}
    if not quality_inventory_df.empty:
        for _, row in quality_inventory_df.iterrows():
            row_dict = row.to_dict()
            folder_name = _norm(row_dict.get("table_folder"))
            if folder_name:
                lookup[folder_name] = row_dict

    rows: List[Dict[str, Any]] = []
    for record in folder_records:
        row = dict(lookup.get(record.folder_name, {}))
        row.setdefault("table_folder", record.folder_name)
        row.setdefault("folder_path", record.folder_path)
        row.setdefault("source_json_path", record.source_json_path or "")
        row.setdefault("parse_success", record.parse_success)
        row.setdefault("table_title", _norm(record.table.table_title) if record.table else "")
        row.setdefault("unit", _norm(record.table.unit) if record.table else "")
        row.setdefault("current_decision", "VLM_PARSE_FAILED" if not record.parse_success else "")
        row.setdefault("main_issue", record.parse_error if not record.parse_success else "")
        row.setdefault("schema_shape", _norm(record.table.schema_shape) if record.table else "")
        row.setdefault("table_warnings", "|".join(record.table.table_warnings) if record.table else "")
        row.setdefault("currency", _norm(record.table.currency) if record.table else "")
        rows.append(row)
    return pd.DataFrame(rows)


def _per_table_summary(
    candidates_df: pd.DataFrame,
    trusted_df: pd.DataFrame,
    review_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    table_inventory_df: pd.DataFrame,
) -> pd.DataFrame:
    inventory_lookup: Dict[str, Dict[str, Any]] = {}
    if not table_inventory_df.empty:
        for _, row in table_inventory_df.iterrows():
            inventory_lookup[_norm(row.get("table_folder"))] = row.to_dict()

    counts_by_folder: Dict[str, Dict[str, int]] = {}
    for split_name, dataframe in [
        ("candidate_count", candidates_df),
        ("trusted_count", trusted_df),
        ("review_required_count", review_df),
        ("rejected_count", rejected_df),
    ]:
        if dataframe.empty:
            continue
        grouped = dataframe.groupby("source_table_id", dropna=False).size()
        for folder_name, count in grouped.items():
            folder_key = _norm(folder_name)
            counts_by_folder.setdefault(folder_key, {})
            counts_by_folder[folder_key][split_name] = int(count)

    rows: List[Dict[str, Any]] = []
    for folder_name, inventory in inventory_lookup.items():
        candidate_count = counts_by_folder.get(folder_name, {}).get("candidate_count", 0)
        trusted_count = counts_by_folder.get(folder_name, {}).get("trusted_count", 0)
        review_count = counts_by_folder.get(folder_name, {}).get("review_required_count", 0)
        rejected_count = counts_by_folder.get(folder_name, {}).get("rejected_count", 0)
        table_decision = "TABLE_NO_CANDIDATES"
        if trusted_count > 0:
            table_decision = "TABLE_HAS_TRUSTED_OUTPUT"
        elif review_count > 0:
            table_decision = "TABLE_USABLE_NEEDS_REVIEW"
        elif rejected_count > 0:
            table_decision = "TABLE_REJECTED_ONLY"
        rows.append(
            {
                "table_folder": folder_name,
                "report_name": _norm(inventory.get("report_name")) or _norm(inventory.get("image_filename")),
                "table_title": _norm(inventory.get("table_title")),
                "quality_decision": _norm(inventory.get("current_decision")),
                "quality_main_issue": _norm(inventory.get("main_issue")),
                "candidate_count": candidate_count,
                "trusted_count": trusted_count,
                "review_required_count": review_count,
                "rejected_count": rejected_count,
                "unique_metric_count": 0,
                "unique_year_count": 0,
                "qa_status": "PASS" if trusted_count > 0 or candidate_count > 0 else "WARN",
                "table_decision": table_decision,
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(
            columns=[
                "table_folder",
                "report_name",
                "table_title",
                "quality_decision",
                "quality_main_issue",
                "candidate_count",
                "trusted_count",
                "review_required_count",
                "rejected_count",
                "unique_metric_count",
                "unique_year_count",
                "qa_status",
                "table_decision",
            ]
        )

    if not candidates_df.empty:
        metric_counts = (
            candidates_df.groupby("source_table_id", dropna=False)
            .agg(
                unique_metric_count=("metric_code", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
                unique_year_count=("year", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
            )
            .reset_index()
            .rename(columns={"source_table_id": "table_folder"})
        )
        result = result.drop(columns=["unique_metric_count", "unique_year_count"], errors="ignore").merge(
            metric_counts, on="table_folder", how="left"
        )
        result["unique_metric_count"] = result["unique_metric_count"].fillna(0).astype(int)
        result["unique_year_count"] = result["unique_year_count"].fillna(0).astype(int)

    return result.sort_values(["table_folder"]).reset_index(drop=True)


def _per_report_summary(candidates_df: pd.DataFrame, trusted_df: pd.DataFrame, review_df: pd.DataFrame, rejected_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return pd.DataFrame(
            columns=[
                "report_name",
                "table_count",
                "candidate_count",
                "trusted_count",
                "review_required_count",
                "rejected_count",
                "unique_metric_count",
                "unique_year_count",
            ]
        )

    all_reports = candidates_df.copy()
    all_reports["trusted_count_row"] = 0
    all_reports["review_required_count_row"] = 0
    all_reports["rejected_count_row"] = 0

    if not trusted_df.empty:
        trusted_ids = set(trusted_df["candidate_id"].astype(str).tolist())
        all_reports.loc[all_reports["candidate_id"].astype(str).isin(trusted_ids), "trusted_count_row"] = 1
    if not review_df.empty:
        review_ids = set(review_df["candidate_id"].astype(str).tolist())
        all_reports.loc[all_reports["candidate_id"].astype(str).isin(review_ids), "review_required_count_row"] = 1
    if not rejected_df.empty:
        rejected_ids = set(rejected_df["candidate_id"].astype(str).tolist())
        all_reports.loc[all_reports["candidate_id"].astype(str).isin(rejected_ids), "rejected_count_row"] = 1

    result = (
        all_reports.groupby("source_doc_name", dropna=False)
        .agg(
            table_count=("source_table_id", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
            candidate_count=("candidate_id", "count"),
            trusted_count=("trusted_count_row", "sum"),
            review_required_count=("review_required_count_row", "sum"),
            rejected_count=("rejected_count_row", "sum"),
            unique_metric_count=("metric_code", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
            unique_year_count=("year", lambda s: int(pd.Series(s).replace("", pd.NA).dropna().nunique())),
        )
        .reset_index()
        .rename(columns={"source_doc_name": "report_name"})
        .sort_values(["report_name"])
        .reset_index(drop=True)
    )
    return result


def _metric_coverage(candidates_df: pd.DataFrame, trusted_df: pd.DataFrame, review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "metric_family",
        "metric_code",
        "candidate_count",
        "trusted_count",
        "review_required_count",
        "unique_report_count",
        "unique_table_count",
        "years_covered",
    ]
    if candidates_df.empty:
        return pd.DataFrame(columns=columns)

    trusted_ids = set(trusted_df["candidate_id"].astype(str).tolist()) if not trusted_df.empty else set()
    review_ids = set(review_df["candidate_id"].astype(str).tolist()) if not review_df.empty else set()
    temp = candidates_df.copy()
    temp["trusted_count_row"] = temp["candidate_id"].astype(str).isin(trusted_ids).astype(int)
    temp["review_required_count_row"] = temp["candidate_id"].astype(str).isin(review_ids).astype(int)
    grouped = (
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
    return grouped[columns]


def _risk_tag_counts(candidates_df: pd.DataFrame) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    if not candidates_df.empty:
        for tags in candidates_df["risk_tags"].astype(str).tolist():
            for tag in [item.strip() for item in tags.split("|") if item.strip()]:
                counter[tag] += 1
    rows = [{"risk_tag": tag, "count": count} for tag, count in counter.most_common()]
    return pd.DataFrame(rows)


def _unit_year_context_summary(candidates_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return pd.DataFrame(
            [
                {
                    "unit_unknown_count": 0,
                    "year_inferred_count": 0,
                    "table_header_year_count": 0,
                    "invalid_year_count": 0,
                    "unit_context_sources": "",
                    "year_context_sources": "",
                }
            ]
        )
    unit_unknown_count = int(candidates_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum())
    year_inferred_count = int((candidates_df["year_source"].astype(str) == "INFERRED_SEQUENCE").sum())
    table_header_year_count = int((candidates_df["year_source"].astype(str) == "TABLE_HEADER").sum())
    invalid_year_count = int(candidates_df["risk_tags"].astype(str).str.contains(r"(?:^|\|)INVALID_YEAR(?:$|\|)", regex=True).sum())
    return pd.DataFrame(
        [
            {
                "unit_unknown_count": unit_unknown_count,
                "year_inferred_count": year_inferred_count,
                "table_header_year_count": table_header_year_count,
                "invalid_year_count": invalid_year_count,
                "unit_context_sources": "|".join(sorted(set([_norm(v) for v in candidates_df["unit_source"].tolist() if _norm(v)]))),
                "year_context_sources": "|".join(sorted(set([_norm(v) for v in candidates_df["year_source"].tolist() if _norm(v)]))),
            }
        ]
    )


def _provenance_coverage(candidates_df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    if candidates_df.empty:
        return (
            pd.DataFrame(
                columns=[
                    "candidate_id",
                    "table_folder",
                    "report_name",
                    "metric_code",
                    "year",
                    "has_source_file",
                    "has_source_row_text",
                    "has_source_table_id",
                    "has_source_stage",
                    "has_year_source",
                    "has_unit_source",
                    "provenance_complete",
                    "missing_fields",
                ]
            ),
            0.0,
        )

    rows: List[Dict[str, Any]] = []
    for _, row in candidates_df.iterrows():
        missing: List[str] = []
        has_source_file = bool(_norm(row.get("source_file")))
        has_source_row_text = bool(_norm(row.get("source_row_text")))
        has_source_table_id = bool(_norm(row.get("source_table_id")))
        has_source_stage = bool(_norm(row.get("source_stage")))
        has_year_source = bool(_norm(row.get("year_source")))
        has_unit_source = bool(_norm(row.get("unit_source")))
        if not has_source_file:
            missing.append("source_file")
        if not has_source_row_text:
            missing.append("source_row_text")
        if not has_source_table_id:
            missing.append("source_table_id")
        if not has_source_stage:
            missing.append("source_stage")
        if not has_year_source:
            missing.append("year_source")
        if not has_unit_source:
            missing.append("unit_source")
        rows.append(
            {
                "candidate_id": _norm(row.get("candidate_id")),
                "table_folder": _norm(row.get("source_table_id")),
                "report_name": _norm(row.get("source_doc_name")),
                "metric_code": _norm(row.get("metric_code")),
                "year": _norm(row.get("year")),
                "has_source_file": has_source_file,
                "has_source_row_text": has_source_row_text,
                "has_source_table_id": has_source_table_id,
                "has_source_stage": has_source_stage,
                "has_year_source": has_year_source,
                "has_unit_source": has_unit_source,
                "provenance_complete": len(missing) == 0,
                "missing_fields": "|".join(missing),
            }
        )
    dataframe = pd.DataFrame(rows)
    return dataframe, float(dataframe["provenance_complete"].mean()) if not dataframe.empty else 0.0


def _qa_checks(
    trusted_df: pd.DataFrame,
    candidates_df: pd.DataFrame,
    table_inventory_df: pd.DataFrame,
    quality_summary: Dict[str, Any],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def _status(pass_condition: bool, warn_condition: bool = False) -> str:
        if pass_condition:
            return "PASS"
        if warn_condition:
            return "WARN"
        return "FAIL"

    trusted_tags = trusted_df["risk_tags"].astype(str) if not trusted_df.empty and "risk_tags" in trusted_df.columns else pd.Series(dtype=str)
    corrupted_label_count = int(trusted_df["source_row_text"].astype(str).str.contains(r"[?？�]").sum()) if not trusted_df.empty else 0
    invalid_year_count = int((~trusted_df["year"].astype(str).str.match(r"^20\d{2}(?:[AE])?$", na=False)).sum()) if not trusted_df.empty else 0
    unknown_metric_count = int((trusted_df["metric_code"].astype(str) == "unknown_metric").sum()) if not trusted_df.empty else 0
    missing_value_count = int(trusted_df["normalized_value"].isna().sum()) if not trusted_df.empty else 0
    trusted_conflict_count = int(trusted_tags.str.contains(r"(?:^|\|)VALUE_CONFLICT(?:$|\|)", regex=True).sum()) if not trusted_df.empty else 0
    schema_invalid_trusted_count = int(trusted_tags.str.contains(r"(?:^|\|)SCHEMA_REVIEW_REQUIRED(?:$|\|)", regex=True).sum()) if not trusted_df.empty else 0
    chinese_replacement_count = int(candidates_df["source_row_text"].astype(str).str.contains(r"[?？�]").sum()) if not candidates_df.empty else 0

    rows.append({"check_name": "no_corrupted_labels_in_trusted_output", "status": _status(corrupted_label_count == 0), "detail": f"corrupted_label_count={corrupted_label_count}"})
    rows.append({"check_name": "no_invalid_year_in_trusted_output", "status": _status(invalid_year_count == 0), "detail": f"invalid_year_count={invalid_year_count}"})
    rows.append({"check_name": "no_unknown_metric_code_in_trusted_output", "status": _status(unknown_metric_count == 0), "detail": f"unknown_metric_code_count={unknown_metric_count}"})
    rows.append({"check_name": "no_missing_normalized_value_in_trusted_output", "status": _status(missing_value_count == 0), "detail": f"missing_normalized_value_count={missing_value_count}"})
    rows.append({"check_name": "no_conflict_in_trusted_output", "status": _status(trusted_conflict_count == 0), "detail": f"trusted_conflict_count={trusted_conflict_count}"})
    rows.append({"check_name": "schema_invalid_tables_not_silently_trusted", "status": _status(schema_invalid_trusted_count == 0), "detail": f"schema_invalid_trusted_count={schema_invalid_trusted_count}"})

    quality_table_ready = int(quality_summary.get("table_ready_count", 0))
    inventory_table_ready = int((table_inventory_df["current_decision"].astype(str) == "VLM_TABLE_READY_FOR_MAPPING").sum()) if not table_inventory_df.empty else 0
    rows.append(
        {
            "check_name": "table_ready_count_matches_321a",
            "status": _status(quality_table_ready == inventory_table_ready),
            "detail": f"quality_table_ready={quality_table_ready}, inventory_table_ready={inventory_table_ready}",
        }
    )

    rows.append(
        {
            "check_name": "chinese_text_preserved",
            "status": _status(chinese_replacement_count == 0),
            "detail": f"replacement_char_or_question_mark_count={chinese_replacement_count}",
        }
    )
    return pd.DataFrame(rows)


def _comparison_rows(summary: Dict[str, Any], ppstructure_summary: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    metrics = [
        ("parsed_table_count", "higher_better"),
        ("table_with_candidates_count", "higher_better"),
        ("table_with_trusted_count", "higher_better"),
        ("trusted_total_count", "higher_better"),
        ("review_required_total_count", "lower_better"),
        ("trusted_rate", "higher_better"),
        ("unit_unknown_count", "lower_better"),
        ("year_inferred_count", "lower_better"),
        ("conflict_count", "lower_better"),
        ("provenance_complete_rate", "higher_better"),
    ]
    for metric_name, direction in metrics:
        vlm_value = summary.get(metric_name)
        pp_value = ppstructure_summary.get(metric_name)
        winner = "tie"
        notes = direction
        if vlm_value is None or pp_value is None:
            winner = "unavailable"
            notes = "missing baseline or vlm value"
        else:
            if direction == "higher_better":
                if float(vlm_value) > float(pp_value):
                    winner = "vlm"
                elif float(vlm_value) < float(pp_value):
                    winner = "ppstructure"
            else:
                if float(vlm_value) < float(pp_value):
                    winner = "vlm"
                elif float(vlm_value) > float(pp_value):
                    winner = "ppstructure"
        rows.append(
            {
                "metric_name": metric_name,
                "vlm_value": vlm_value,
                "ppstructure_value": pp_value,
                "winner": winner,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


def _known_limitations_df(ppstructure_available: bool) -> pd.DataFrame:
    rows = [
        {
            "limitation": "sandbox_only",
            "detail": "321B is a sandbox benchmark only and must not be treated as production apply readiness.",
        },
        {
            "limitation": "manual_vlm_input_generation",
            "detail": "VLM inputs were manually rerun into strict JSON and are not part of the production recognizer path.",
        },
        {
            "limitation": "hierarchical_segment_tables",
            "detail": "Schema-invalid hierarchical or segment tables are explicitly kept out of trusted output in this stage.",
        },
    ]
    if ppstructure_available:
        rows.append(
            {
                "limitation": "comparison_not_apples_to_apples",
                "detail": "PPStructure benchmark is based on local OCR row-text outputs while VLM outputs are manually generated strict JSON samples.",
            }
        )
    return pd.DataFrame(rows)


def _decision(summary: Dict[str, Any]) -> str:
    if int(summary.get("qa_fail_count", 0)) > 0:
        return "VLM_MAPPING_BLOCKED_BY_QA_FAILURE"
    if int(summary.get("corrupted_label_candidate_count", 0)) > 0:
        return "VLM_MAPPING_BLOCKED_BY_LABEL_CORRUPTION"
    if (
        int(summary.get("mapped_table_count", 0)) >= 9
        and int(summary.get("table_with_trusted_count", 0)) >= 7
        and float(summary.get("trusted_rate", 0.0)) >= 0.60
        and float(summary.get("provenance_complete_rate", 0.0)) >= 0.95
        and int(summary.get("qa_fail_count", 0)) == 0
    ):
        return "VLM_MAPPING_READY_FOR_321C_RECOGNIZER_ROUTER_PLAN"
    if (
        int(summary.get("mapped_table_count", 0)) >= 7
        and int(summary.get("table_with_candidates_count", 0)) >= 7
        and int(summary.get("qa_fail_count", 0)) == 0
    ):
        return "VLM_MAPPING_PARTIAL_NEEDS_ALIAS_OR_SCHEMA_CALIBRATION"
    return "VLM_MAPPING_NOT_READY"


def _blocked_result(vlm_output_root: Path, quality_dir: Path, output_dir: Path, blocked_code: str, blocked_message: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "321B",
        "blocked": True,
        "blocked_code": blocked_code,
        "blocked_message": blocked_message,
        "vlm_output_root": str(vlm_output_root),
        "quality_dir": str(quality_dir),
        "output_dir": str(output_dir),
        "vlm_folder_count": 0,
        "parsed_json_count": 0,
        "table_ready_count": 0,
        "mapped_table_count": 0,
        "table_with_candidates_count": 0,
        "table_with_trusted_count": 0,
        "total_candidate_count": 0,
        "trusted_total_count": 0,
        "review_required_total_count": 0,
        "rejected_total_count": 0,
        "trusted_rate": 0.0,
        "unique_metric_count": 0,
        "unique_year_count": 0,
        "unique_report_count": 0,
        "unit_unknown_count": 0,
        "year_inferred_count": 0,
        "conflict_count": 0,
        "corrupted_label_candidate_count": 0,
        "provenance_complete_rate": 0.0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "ppstructure_comparison_available": False,
        "vlm_benchmark_decision": blocked_code,
        "top_risk_tags": [],
    }
    sheets = {
        "summary": build_summary_dataframe(summary),
        "vlm_table_inventory": pd.DataFrame(),
        "vlm_rows_normalized": pd.DataFrame(),
        "metric_candidates_all": pd.DataFrame(),
        "trusted_preview": pd.DataFrame(),
        "review_required_preview": pd.DataFrame(),
        "rejected_preview": pd.DataFrame(),
        "per_table_summary": pd.DataFrame(),
        "per_report_summary": pd.DataFrame(),
        "metric_coverage": pd.DataFrame(),
        "unit_year_context_summary": pd.DataFrame(),
        "risk_tag_counts": pd.DataFrame(),
        "provenance_coverage": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": blocked_code, "status": "FAIL", "detail": blocked_message}]),
        "vlm_vs_ppstructure_summary": pd.DataFrame(),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": blocked_message}]),
    }
    excel_path = output_dir / "vlm_mapping_benchmark_321b.xlsx"
    summary_json_path = output_dir / "vlm_mapping_benchmark_321b_summary.json"
    report_md_path = output_dir / "vlm_mapping_benchmark_321b_report.md"
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_markdown_report(report_md_path, summary, sheets["qa_checks"], sheets["vlm_vs_ppstructure_summary"], sheets["risk_tag_counts"])
    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }


def run_vlm_mapping_benchmark(
    vlm_output_root: Path,
    quality_dir: Path,
    output_dir: Path,
    ppstructure_benchmark_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    if not vlm_output_root.exists() or not vlm_output_root.is_dir():
        return _blocked_result(
            vlm_output_root=vlm_output_root,
            quality_dir=quality_dir,
            output_dir=output_dir,
            blocked_code="BLOCKED_MISSING_VLM_OUTPUT_ROOT",
            blocked_message=f"missing vlm output root: {vlm_output_root}",
        )
    if not quality_dir.exists() or not quality_dir.is_dir():
        return _blocked_result(
            vlm_output_root=vlm_output_root,
            quality_dir=quality_dir,
            output_dir=output_dir,
            blocked_code="BLOCKED_MISSING_QUALITY_DIR",
            blocked_message=f"missing quality dir: {quality_dir}",
        )

    quality_inputs = _load_quality_inputs(quality_dir)
    quality_summary = quality_inputs["summary"]
    quality_inventory_df = quality_inputs["inventory_df"]
    folder_records = scan_vlm_output_root(vlm_output_root)
    table_inventory_df = _table_inventory_from_records(folder_records, quality_inventory_df)

    mapping_result = map_vlm_outputs_to_candidates(folder_records, quality_inventory_df)
    dedupe_result = resolve_vlm_duplicates_and_conflicts(mapping_result["candidates"])
    split_result = split_vlm_candidates_for_sandbox_preview(dedupe_result["canonical_candidates"])

    normalized_rows_df = pd.DataFrame(mapping_result["normalized_rows"])
    candidates_df = candidates_to_dataframe(dedupe_result["canonical_candidates"])
    trusted_df = candidates_to_dataframe(split_result["trusted_preview"])
    review_df = candidates_to_dataframe(split_result["review_required_preview"])
    rejected_df = candidates_to_dataframe(split_result["rejected_preview"])
    per_table_df = _per_table_summary(candidates_df, trusted_df, review_df, rejected_df, table_inventory_df)
    per_report_df = _per_report_summary(candidates_df, trusted_df, review_df, rejected_df)
    metric_coverage_df = _metric_coverage(candidates_df, trusted_df, review_df)
    unit_year_df = _unit_year_context_summary(candidates_df)
    risk_tag_counts_df = _risk_tag_counts(candidates_df)
    provenance_df, provenance_complete_rate = _provenance_coverage(candidates_df)
    qa_df = _qa_checks(trusted_df, candidates_df, table_inventory_df, quality_summary)
    known_limitations_df = _known_limitations_df(bool(ppstructure_benchmark_dir and ppstructure_benchmark_dir.exists()))

    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    ppstructure_available = bool(ppstructure_benchmark_dir and ppstructure_benchmark_dir.exists())
    ppstructure_summary = _read_json(ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json") if ppstructure_available else {}
    comparison_df = _comparison_rows(
        {
            "parsed_table_count": int(quality_summary.get("parsed_json_count", 0)),
            "table_with_candidates_count": int((per_table_df["candidate_count"] > 0).sum()) if not per_table_df.empty else 0,
            "table_with_trusted_count": int((per_table_df["trusted_count"] > 0).sum()) if not per_table_df.empty else 0,
            "trusted_total_count": int(len(trusted_df)),
            "review_required_total_count": int(len(review_df)),
            "trusted_rate": float(len(trusted_df) / len(candidates_df)) if len(candidates_df) else 0.0,
            "unit_unknown_count": int(unit_year_df["unit_unknown_count"].iloc[0]) if not unit_year_df.empty else 0,
            "year_inferred_count": int(unit_year_df["year_inferred_count"].iloc[0]) if not unit_year_df.empty else 0,
            "conflict_count": int(dedupe_result["conflict_group_count"]),
            "provenance_complete_rate": provenance_complete_rate,
        },
        ppstructure_summary,
    ) if ppstructure_available else pd.DataFrame(
        columns=["metric_name", "vlm_value", "ppstructure_value", "winner", "notes"]
    )

    summary = {
        "stage": "321B",
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "vlm_output_root": str(vlm_output_root),
        "quality_dir": str(quality_dir),
        "output_dir": str(output_dir),
        "vlm_folder_count": int(quality_summary.get("vlm_folder_count", len(folder_records))),
        "parsed_json_count": int(quality_summary.get("parsed_json_count", 0)),
        "table_ready_count": int(quality_summary.get("table_ready_count", 0)),
        "mapped_table_count": int((per_table_df["candidate_count"] > 0).sum()) if not per_table_df.empty else 0,
        "table_with_candidates_count": int((per_table_df["candidate_count"] > 0).sum()) if not per_table_df.empty else 0,
        "table_with_trusted_count": int((per_table_df["trusted_count"] > 0).sum()) if not per_table_df.empty else 0,
        "total_candidate_count": int(len(candidates_df)),
        "trusted_total_count": int(len(trusted_df)),
        "review_required_total_count": int(len(review_df)),
        "rejected_total_count": int(len(rejected_df)),
        "trusted_rate": float(len(trusted_df) / len(candidates_df)) if len(candidates_df) else 0.0,
        "unique_metric_count": int(candidates_df["metric_code"].replace("", pd.NA).dropna().nunique()) if not candidates_df.empty else 0,
        "unique_year_count": int(candidates_df["year"].replace("", pd.NA).dropna().nunique()) if not candidates_df.empty else 0,
        "unique_report_count": int(candidates_df["source_doc_name"].replace("", pd.NA).dropna().nunique()) if not candidates_df.empty else 0,
        "unit_unknown_count": int(unit_year_df["unit_unknown_count"].iloc[0]) if not unit_year_df.empty else 0,
        "year_inferred_count": int(unit_year_df["year_inferred_count"].iloc[0]) if not unit_year_df.empty else 0,
        "conflict_count": int(dedupe_result["conflict_group_count"]),
        "corrupted_label_candidate_count": int(candidates_df["source_row_text"].astype(str).str.contains(r"[?？�]").sum()) if not candidates_df.empty else 0,
        "provenance_complete_rate": provenance_complete_rate,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "ppstructure_comparison_available": ppstructure_available,
        "top_risk_tags": top_risk_tags_from_df(risk_tag_counts_df),
    }
    summary["vlm_benchmark_decision"] = _decision(summary)

    summary_df = build_summary_dataframe(summary)
    sheets = {
        "summary": summary_df,
        "vlm_table_inventory": table_inventory_df,
        "vlm_rows_normalized": normalized_rows_df,
        "metric_candidates_all": candidates_df,
        "trusted_preview": trusted_df,
        "review_required_preview": review_df,
        "rejected_preview": rejected_df,
        "per_table_summary": per_table_df,
        "per_report_summary": per_report_df,
        "metric_coverage": metric_coverage_df,
        "unit_year_context_summary": unit_year_df,
        "risk_tag_counts": risk_tag_counts_df,
        "provenance_coverage": provenance_df,
        "qa_checks": qa_df,
        "vlm_vs_ppstructure_summary": comparison_df,
        "known_limitations": known_limitations_df,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    excel_path = output_dir / "vlm_mapping_benchmark_321b.xlsx"
    summary_json_path = output_dir / "vlm_mapping_benchmark_321b_summary.json"
    report_md_path = output_dir / "vlm_mapping_benchmark_321b_report.md"
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    write_markdown_report(report_md_path, summary, qa_df, comparison_df, risk_tag_counts_df)

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
