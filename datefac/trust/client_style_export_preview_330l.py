from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.delivery_report_refresh_330j import _read_json
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.source_attribution_unit_signal_fix_330i import _read_jsonl_rows
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_330J2_DECISION = (
    "DELIVERY_REPORT_REFRESH_330J2_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_330L_EXPORT_PREVIEW"
)
READY_DECISION = (
    "CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING"
)
NOT_READY_DECISION = "CLIENT_STYLE_EXPORT_PREVIEW_330L_NOT_READY"

DEFAULT_DELIVERY_REPORT_REFRESH_DIR = Path(
    r"D:\_datefac\output\delivery_report_refresh_after_330k_330j2"
)
DEFAULT_FIXED_PREPARED_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split_330k")
DEFAULT_UNIT_SIGNAL_REVIEW_DIR = Path(r"D:\_datefac\output\unit_signal_review_330k")
DEFAULT_OPTIONAL_RERUN_330F_DIR = Path(
    r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j2"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\client_style_export_preview_330l")

REQUIRED_SHEETS = [
    "00_README",
    "01_EXEC_SUMMARY",
    "02_TRUSTED_SUGGESTIONS",
    "03_REVIEW_REQUIRED",
    "04_UNIT_REVIEW_SAMPLE",
    "05_SOURCE_PROVENANCE",
    "06_QA_CAVEATS",
]


def validate_330j2_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append(
            {
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    add(
        "readiness::330j2_decision",
        _norm_text(summary.get("decision")) == READY_330J2_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330j2_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330j2_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 117,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "records::330j2_strict_deduped_candidate_count",
        _safe_int(summary.get("strict_deduped_candidate_count"), -1) == 117,
        str(summary.get("strict_deduped_candidate_count", "")),
    )
    add(
        "quality::330j2_source_page_missing_count",
        _safe_int(summary.get("source_page_missing_count"), -1) == 0,
        str(summary.get("source_page_missing_count", "")),
    )
    add(
        "quality::330j2_unit_missing_count",
        _safe_int(summary.get("unit_missing_count"), -1) == 18,
        str(summary.get("unit_missing_count", "")),
    )
    add(
        "quality::330j2_unit_unknown_risk_count",
        _safe_int(summary.get("unit_unknown_risk_count"), -1) == 18,
        str(summary.get("unit_unknown_risk_count", "")),
    )
    add(
        "quality::330j2_unit_conflict_risk_count",
        _safe_int(summary.get("unit_conflict_risk_count"), -1) == 12,
        str(summary.get("unit_conflict_risk_count", "")),
    )
    add(
        "quality::330j2_sidecar_trusted_suggestion_count",
        _safe_int(summary.get("sidecar_trusted_suggestion_count"), -1) == 192,
        str(summary.get("sidecar_trusted_suggestion_count", "")),
    )
    add(
        "quality::330j2_sidecar_review_required_suggestion_count",
        _safe_int(summary.get("sidecar_review_required_suggestion_count"), -1) == 42,
        str(summary.get("sidecar_review_required_suggestion_count", "")),
    )
    add(
        "quality::330j2_delivery_readiness_judgment",
        _norm_text(summary.get("delivery_readiness_judgment"))
        == "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
        _norm_text(summary.get("delivery_readiness_judgment")),
    )
    add(
        "safety::330j2_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330j2")) is True,
        str(summary.get("no_official_asset_modification_during_330j2", "")),
    )
    return checks


def _dedupe_scored_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for row in rows:
        candidate_id = _norm_text(row.get("candidate_id"))
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        deduped.append(dict(row))
    return deduped


def _merge_prepared_with_scored(
    fixed_rows: Sequence[Mapping[str, Any]],
    scored_rows: Sequence[Mapping[str, Any]],
) -> pd.DataFrame:
    scored_by_candidate = {
        _norm_text(row.get("candidate_id")): dict(row)
        for row in scored_rows
        if _norm_text(row.get("candidate_id"))
    }
    merged_rows: List[Dict[str, Any]] = []
    for row in fixed_rows:
        merged = dict(row)
        scored = scored_by_candidate.get(_norm_text(row.get("candidate_id")), {})
        for key in [
            "confidence_score",
            "confidence_level",
            "routing_decision",
            "risk_flags",
            "evidence_refs",
            "source_pdf_name",
            "warning_risks",
            "blocking_risks",
        ]:
            if key in scored:
                merged[key] = scored.get(key)
        merged_rows.append(merged)
    return _frame_for_output(pd.DataFrame(merged_rows))


def _stringify_tokens(value: Any) -> str:
    if isinstance(value, list):
        return " | ".join(str(item) for item in value if _norm_text(item))
    return _norm_text(value)


def _sheet_subset(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=list(columns))
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    out = out.loc[:, list(columns)].copy()
    for column in out.columns:
        out[column] = out[column].map(_stringify_tokens)
    return _frame_for_output(out)


def _build_readme_df(summary_330j2: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"section": "title", "content": "DateFac client-style export preview"},
        {
            "section": "demo_readiness",
            "content": f"Demo readiness: {_norm_text(summary_330j2.get('delivery_readiness_judgment'))}",
        },
        {"section": "scope", "content": "Scope: 13 unfamiliar PDFs, 7 with candidates"},
        {
            "section": "candidate_rows",
            "content": f"Candidate rows: {_safe_int(summary_330j2.get('prepared_candidate_row_count'), 0)}",
        },
        {
            "section": "sidecar_only",
            "content": "This is sidecar trust scoring, not production routing",
        },
        {
            "section": "not_client_ready",
            "content": "Not client-ready; manual unit review caveats remain",
        },
    ]
    return _frame_for_output(pd.DataFrame(rows))


def _build_exec_summary_df(summary_330j2: Mapping[str, Any]) -> pd.DataFrame:
    return _frame_for_output(
        pd.DataFrame(
            [
                {
                    "metric": key,
                    "value": summary_330j2.get(key, ""),
                }
                for key in [
                    "source_pdf_unique_count",
                    "prepared_candidate_row_count",
                    "strict_deduped_candidate_count",
                    "sidecar_trusted_suggestion_count",
                    "sidecar_review_required_suggestion_count",
                    "unit_missing_count",
                    "unit_unknown_risk_count",
                    "unit_conflict_risk_count",
                    "source_page_missing_count",
                    "delivery_readiness_judgment",
                    "recommended_next_step",
                ]
            ]
        )
    )


def _build_unit_review_sample_df(workbook_path: Path) -> pd.DataFrame:
    if not workbook_path.exists():
        return pd.DataFrame(
            columns=[
                "candidate_id",
                "source_pdf",
                "source_page",
                "normalized_metric",
                "metric_label_raw",
                "row_text",
                "unit",
                "unit_status_330k",
                "unit_missing_category_330k",
                "risk_flags",
                "recommended_human_decision",
                "human_unit_decision",
                "human_unit_value",
                "human_notes",
            ]
        )
    review_df = pd.read_excel(workbook_path, sheet_name="review_candidates")
    for column in ["human_unit_decision", "human_unit_value", "human_notes"]:
        if column not in review_df.columns:
            review_df[column] = ""
    return _frame_for_output(review_df)


def _build_source_provenance_df(merged_df: pd.DataFrame) -> pd.DataFrame:
    if merged_df.empty:
        return pd.DataFrame(
            columns=[
                "source_pdf",
                "source_page",
                "candidate_count",
                "trusted_suggestion_count",
                "review_required_count",
                "unit_risk_count",
            ]
        )
    working = merged_df.copy()
    working["source_pdf"] = working["source_pdf"].map(_norm_text)
    working["source_page"] = working["source_page"].map(_norm_text)
    working["routing_decision"] = working["routing_decision"].map(_norm_text)
    working["risk_flags_str"] = working["risk_flags"].map(_stringify_tokens)
    rows: List[Dict[str, Any]] = []
    for (source_pdf, source_page), group in working.groupby(["source_pdf", "source_page"], dropna=False):
        rows.append(
            {
                "source_pdf": source_pdf,
                "source_page": source_page,
                "candidate_count": int(len(group)),
                "trusted_suggestion_count": int((group["routing_decision"] == "TRUSTED").sum()),
                "review_required_count": int((group["routing_decision"] == "REVIEW_REQUIRED").sum()),
                "unit_risk_count": int(
                    group["risk_flags_str"].str.contains("UNIT_UNKNOWN|UNIT_CONFLICT", na=False).sum()
                ),
            }
        )
    return _frame_for_output(pd.DataFrame(rows))


def _build_qa_caveats_df(summary_330j2: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "caveat_code": "sidecar_only_not_production_routing",
            "detail": "This preview reflects sidecar trust scoring only and does not represent production routing.",
        },
        {
            "caveat_code": "not_client_ready",
            "detail": "Conservative wording applies: this package is demo-ready only and not client-ready.",
        },
        {
            "caveat_code": "unit_review_remaining",
            "detail": f"{_safe_int(summary_330j2.get('unit_missing_count'), 0)} rows still lack a unit after 330K.",
        },
        {
            "caveat_code": "unit_conflict_remaining",
            "detail": f"{_safe_int(summary_330j2.get('unit_conflict_risk_count'), 0)} rows still carry UNIT_CONFLICT risk.",
        },
        {
            "caveat_code": "artifact_row_vs_candidate_row_difference",
            "detail": f"Artifact rows {_safe_int(summary_330j2.get('artifact_row_count'), 0)} differ from candidate rows {_safe_int(summary_330j2.get('prepared_candidate_row_count'), 0)} because rerun scoring reads compatibility artifacts.",
        },
        {
            "caveat_code": "only_7_of_13_pdfs_produced_candidates",
            "detail": "Only 7 of 13 unfamiliar PDFs produced candidate rows in the current cached sidecar inputs.",
        },
        {
            "caveat_code": "no_official_assets_modified",
            "detail": "No official alias or scope assets were modified during 330L.",
        },
    ]
    return _frame_for_output(pd.DataFrame(rows))


def build_client_style_export_preview_330l(
    *,
    delivery_report_refresh_dir: Path,
    fixed_prepared_dir: Path,
    unit_signal_review_dir: Path,
    optional_rerun_330f_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330j2_path = (
        delivery_report_refresh_dir / "delivery_report_refresh_after_330k_330j2_summary.json"
    )
    fixed_rows_path = fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"
    review_summary_path = unit_signal_review_dir / "unit_signal_review_330k_summary.json"
    review_workbook_path = unit_signal_review_dir / "unit_signal_review_330k_workbook.xlsx"
    scored_records_path = (
        optional_rerun_330f_dir / "unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl"
    )

    summary_330j2 = _read_json(summary_330j2_path)
    review_summary = _read_json(review_summary_path)
    fixed_rows = _read_jsonl_rows(fixed_rows_path)
    scored_rows = _read_jsonl_rows(scored_records_path) if scored_records_path.exists() else []

    qa_rows = validate_330j2_summary(summary_330j2)

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append(
            {
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }

    add_qa("inputs::fixed_rows_exists", fixed_rows_path.exists(), str(fixed_rows_path))
    add_qa("records::fixed_rows_count", len(fixed_rows) == 117, str(len(fixed_rows)))
    add_qa(
        "inputs::unit_review_workbook_exists",
        review_workbook_path.exists(),
        str(review_workbook_path),
    )
    deduped_scored_rows = _dedupe_scored_rows(scored_rows)
    merged_df = _merge_prepared_with_scored(fixed_rows, deduped_scored_rows)
    add_qa(
        "records::merged_candidate_row_count",
        len(merged_df) == 117,
        str(len(merged_df)),
    )

    trusted_sheet_df = _sheet_subset(
        merged_df.loc[merged_df["routing_decision"].map(_norm_text) == "TRUSTED"].copy(),
        [
            "candidate_id",
            "source_pdf",
            "source_page",
            "metric_label_raw",
            "normalized_metric",
            "value",
            "unit",
            "year",
            "confidence_score",
            "confidence_level",
            "routing_decision",
            "risk_flags",
            "evidence_refs",
            "row_text",
        ],
    )
    review_required_df = _sheet_subset(
        merged_df.loc[
            (merged_df["routing_decision"].map(_norm_text) == "REVIEW_REQUIRED")
            | (merged_df["risk_flags"].map(_stringify_tokens).str.contains("UNIT_UNKNOWN|UNIT_CONFLICT", na=False))
        ].copy(),
        [
            "candidate_id",
            "source_pdf",
            "source_page",
            "metric_label_raw",
            "normalized_metric",
            "value",
            "unit",
            "year",
            "confidence_score",
            "confidence_level",
            "routing_decision",
            "risk_flags",
            "evidence_refs",
            "row_text",
        ],
    )
    unit_review_sample_df = _build_unit_review_sample_df(review_workbook_path)
    source_provenance_df = _build_source_provenance_df(merged_df)
    qa_caveats_df = _build_qa_caveats_df(summary_330j2)
    readme_df = _build_readme_df(summary_330j2)
    exec_summary_df = _build_exec_summary_df(summary_330j2)

    preview_workbook_path = output_dir / "client_style_export_preview_330l_preview.xlsx"
    preview_workbook_generated = False

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }
    no_official_asset_modification_during_330l = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330l",
        no_official_asset_modification_during_330l,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    add_qa(
        "quality::unit_review_sheet_row_count",
        len(unit_review_sample_df) >= 21,
        str(len(unit_review_sample_df)),
    )
    add_qa(
        "quality::source_pdf_unique_count",
        _safe_int(summary_330j2.get("source_pdf_unique_count"), -1) == 7,
        str(summary_330j2.get("source_pdf_unique_count", "")),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    export_metrics = {
        "preview_workbook_generated": preview_workbook_generated,
        "trusted_sheet_row_count": int(len(trusted_sheet_df)),
        "review_required_sheet_row_count": int(len(review_required_df)),
        "unit_review_sheet_row_count": int(len(unit_review_sample_df)),
        "source_provenance_sheet_row_count": int(len(source_provenance_df)),
        "qa_caveat_count": int(len(qa_caveats_df)),
    }

    summary = {
        "stage": "330L",
        "output_dir": str(output_dir),
        "validated_330j2_delivery_refresh": all(
            row.get("status") == "PASS" for row in validate_330j2_summary(summary_330j2)
        ),
        "preview_workbook_path": str(preview_workbook_path),
        "sheet_names": REQUIRED_SHEETS,
        "source_pdf_unique_count": _safe_int(summary_330j2.get("source_pdf_unique_count"), 0),
        "prepared_candidate_row_count": _safe_int(summary_330j2.get("prepared_candidate_row_count"), 0),
        "strict_deduped_candidate_count": _safe_int(summary_330j2.get("strict_deduped_candidate_count"), 0),
        "unit_missing_count": _safe_int(summary_330j2.get("unit_missing_count"), 0),
        "unit_conflict_risk_count": _safe_int(summary_330j2.get("unit_conflict_risk_count"), 0),
        "delivery_readiness_judgment": _norm_text(summary_330j2.get("delivery_readiness_judgment")),
        "recommended_next_step": _norm_text(summary_330j2.get("recommended_next_step")),
        **export_metrics,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330l": no_official_asset_modification_during_330l,
        "files_written_to_official_assets": [],
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    workbook_sheets = {
        "00_README": readme_df,
        "01_EXEC_SUMMARY": exec_summary_df,
        "02_TRUSTED_SUGGESTIONS": trusted_sheet_df,
        "03_REVIEW_REQUIRED": review_required_df,
        "04_UNIT_REVIEW_SAMPLE": unit_review_sample_df,
        "05_SOURCE_PROVENANCE": source_provenance_df,
        "06_QA_CAVEATS": qa_caveats_df,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(preview_workbook_path, engine="openpyxl") as writer:
        for sheet_name in REQUIRED_SHEETS:
            workbook_sheets[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
    summary["preview_workbook_generated"] = preview_workbook_path.exists()

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="330L",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_330l": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(
            pd.DataFrame(
                [
                    {
                        "qa_pass_count": qa_pass_count,
                        "qa_fail_count": qa_fail_count,
                        "decision": summary["decision"],
                    }
                ]
            )
        ),
        "qa_checks_df": qa_df,
        "readme_df": readme_df,
        "exec_summary_df": exec_summary_df,
        "trusted_sheet_df": trusted_sheet_df,
        "review_required_df": review_required_df,
        "unit_review_sample_df": unit_review_sample_df,
        "source_provenance_df": source_provenance_df,
        "qa_caveats_df": qa_caveats_df,
        "official_asset_proof_df": official_asset_proof_df,
    }
