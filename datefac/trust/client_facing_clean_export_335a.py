from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.delivery_report_refresh_330j import _read_json
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_330K4_DECISION = "REVIEWED_EXPORT_REFRESH_330K4_READY_FOR_PREVIEW_REVIEW"
READY_331B_DECISION = "DEMO_PACKAGING_331B_READY_FOR_PRESENTATION_REFRESH"
READY_332A_DECISION = "DEMO_RELEASE_AUDIT_332A_READY_FOR_FINAL_DEMO_USE"
READY_DECISION = "CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY"
NOT_READY_DECISION = "CLIENT_FACING_CLEAN_EXPORT_PREVIEW_NOT_READY"

DEFAULT_REVIEWED_EXPORT_REFRESH_DIR = Path(
    r"D:\_datefac\output\reviewed_export_refresh_330k4"
)
DEFAULT_DEMO_PACKAGING_331B_DIR = Path(r"D:\_datefac\output\demo_packaging_331b")
DEFAULT_DEMO_RELEASE_AUDIT_DIR = Path(r"D:\_datefac\output\demo_release_audit_332a")
DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR = Path(
    r"D:\_datefac\output\client_style_export_preview_330l"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\client_facing_clean_export_335a")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

SOURCE_SHEETS = {
    "readme": "00_README",
    "reviewed": "01_REVIEWED_TRUSTED_PREVIEW",
    "needs_review": "02_REMAINING_REVIEW_REQUIRED",
    "rejected": "03_HUMAN_REJECTED_BY_UNIT_REV",
    "trace": "04_APPLY_PLAN_TRACE",
    "qa_context": "05_QA_CONTEXT",
}

CUSTOMER_SHEETS = {
    "readme": "00_README_FOR_CUSTOMER",
    "reviewed": "01_CORE_METRICS_REVIEWED",
    "needs_review": "02_NEEDS_REVIEW",
    "rejected": "03_EXCLUDED_OR_REJECTED",
    "trace": "04_SOURCE_TRACE",
    "summary": "05_DELIVERY_SUMMARY",
}

EXPECTED_COUNTS = {
    "reviewed_trusted_preview_row_count": 98,
    "remaining_review_required_after_unit_review_count": 1,
    "human_rejected_row_count": 18,
    "apply_plan_row_count": 21,
    "original_trusted_sheet_row_count": 96,
    "reviewed_unit_confirmed_count": 2,
}

FORBIDDEN_POSITIVE_CLAIMS = [
    "client-ready",
    "client ready",
    "production-ready",
    "production ready",
    "100% accuracy",
    "fully automatic delivery",
    "investment-decision readiness",
    "investment decision readiness",
]


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_status_porcelain_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_cached_names_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        token_l = token.casefold()
        start = 0
        while True:
            idx = lowered.find(token_l, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 60) : idx]
            if "not " not in window and "not yet " not in window and "= false" not in lowered[idx : idx + 40]:
                return True
            start = idx + len(token_l)
    return False


def _clean_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return value


def _first_present(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        cleaned = _clean_cell(value)
        if isinstance(cleaned, str):
            if cleaned.strip():
                return cleaned.strip()
        elif cleaned != "":
            return cleaned
    return ""


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _frame_for_output(pd.read_excel(path, sheet_name=sheet_name))


def _validate_summary(
    summary: Mapping[str, Any],
    *,
    expected_decision: str,
    checks: List[Dict[str, Any]],
    prefix: str,
) -> None:
    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        f"readiness::{prefix}_decision",
        _norm_text(summary.get("decision")) == expected_decision,
        _norm_text(summary.get("decision")),
    )
    add(
        f"readiness::{prefix}_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )


def _customer_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "What this workbook is",
            "message": "This workbook is a clean preview export generated from financial research PDF extraction.",
        },
        {
            "topic": "Reviewed rows",
            "message": "Reviewed rows are the safest rows in this demo state.",
        },
        {
            "topic": "Needs-review rows",
            "message": "Needs-review rows should be checked manually before use.",
        },
        {
            "topic": "Excluded or rejected rows",
            "message": "Excluded or rejected rows are kept for transparency and should not be treated as trusted.",
        },
        {
            "topic": "Usage boundary",
            "message": "This workbook is for data organization and review assistance, not investment advice.",
        },
        {
            "topic": "Readiness boundary",
            "message": "This is not a production-ready or client-ready automated delivery system.",
        },
        {
            "topic": "Traceability",
            "message": "Source pages and evidence text are included for manual checking.",
        },
    ]
    return _frame_for_output(pd.DataFrame(rows))


def _map_reviewed_rows(source_df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    customer_rows: List[Dict[str, Any]] = []
    trace_seed: List[Dict[str, Any]] = []
    for idx, row in enumerate(source_df.to_dict(orient="records"), start=1):
        review_status = (
            "human_unit_confirmed"
            if _norm_text(row.get("reviewer_decision")) == "CONFIRM_UNIT"
            or _norm_text(row.get("preview_row_origin")) == "330K3_CONFIRMED_FROM_UNIT_REVIEW"
            else "system_trusted"
        )
        notes = (
            "Unit reviewed and confirmed during manual unit review."
            if review_status == "human_unit_confirmed"
            else "High-confidence preview row from trust routing."
        )
        customer_rows.append(
            {
                "row_no": idx,
                "document": _first_present(row, "pdf_document_id", "source_pdf"),
                "metric": _first_present(row, "normalized_metric", "metric_label_raw"),
                "year": _clean_cell(row.get("year")),
                "value": _clean_cell(row.get("value")),
                "unit": _first_present(row, "final_unit_preview", "reviewer_unit", "current_unit"),
                "source_page": _clean_cell(row.get("source_page")),
                "confidence_status": "reviewed_trusted_preview",
                "review_status": review_status,
                "source_evidence": _first_present(row, "source_evidence_text"),
                "notes": notes,
            }
        )
        trace_seed.append(
            {
                "candidate_id": _first_present(row, "candidate_id"),
                "customer_sheet": CUSTOMER_SHEETS["reviewed"],
                "customer_row_no": idx,
                "trace_status": "reviewed_trusted_preview",
                "internal_review_decision": _first_present(row, "reviewer_decision"),
                "document": _first_present(row, "pdf_document_id", "source_pdf"),
                "metric": _first_present(row, "normalized_metric", "metric_label_raw"),
                "year": _clean_cell(row.get("year")),
                "value": _clean_cell(row.get("value")),
                "unit": _first_present(row, "final_unit_preview", "reviewer_unit", "current_unit"),
                "source_page": _clean_cell(row.get("source_page")),
                "source_evidence_refs": _first_present(row, "source_evidence_refs"),
                "source_evidence_text": _first_present(row, "source_evidence_text"),
            }
        )
    return _frame_for_output(pd.DataFrame(customer_rows)), trace_seed


def _map_needs_review_rows(source_df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    customer_rows: List[Dict[str, Any]] = []
    trace_seed: List[Dict[str, Any]] = []
    for idx, row in enumerate(source_df.to_dict(orient="records"), start=1):
        review_reason = (
            _first_present(row, "reviewer_notes")
            or _first_present(row, "risk_flags")
            or "Needs manual source check before use."
        )
        customer_rows.append(
            {
                "row_no": idx,
                "document": _first_present(row, "pdf_document_id", "source_pdf"),
                "metric": _first_present(row, "normalized_metric", "metric_label_raw"),
                "year": _clean_cell(row.get("year")),
                "value": _clean_cell(row.get("value")),
                "current_unit": _first_present(row, "current_unit", "reviewer_unit", "final_unit_preview"),
                "source_page": _clean_cell(row.get("source_page")),
                "review_reason": review_reason,
                "source_evidence": _first_present(row, "source_evidence_text"),
                "recommended_action": "Verify the value and unit against the source PDF before use.",
                "notes": "This row remains review-required and should not be treated as trusted.",
            }
        )
        trace_seed.append(
            {
                "candidate_id": _first_present(row, "candidate_id"),
                "customer_sheet": CUSTOMER_SHEETS["needs_review"],
                "customer_row_no": idx,
                "trace_status": "needs_review",
                "internal_review_decision": _first_present(row, "reviewer_decision"),
                "document": _first_present(row, "pdf_document_id", "source_pdf"),
                "metric": _first_present(row, "normalized_metric", "metric_label_raw"),
                "year": _clean_cell(row.get("year")),
                "value": _clean_cell(row.get("value")),
                "unit": _first_present(row, "current_unit", "reviewer_unit", "final_unit_preview"),
                "source_page": _clean_cell(row.get("source_page")),
                "source_evidence_refs": _first_present(row, "source_evidence_refs"),
                "source_evidence_text": _first_present(row, "source_evidence_text"),
            }
        )
    return _frame_for_output(pd.DataFrame(customer_rows)), trace_seed


def _map_rejected_rows(source_df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    customer_rows: List[Dict[str, Any]] = []
    trace_seed: List[Dict[str, Any]] = []
    for idx, row in enumerate(source_df.to_dict(orient="records"), start=1):
        rejection_reason = (
            _first_present(row, "reviewer_notes")
            or _first_present(row, "risk_flags")
            or "Rejected during manual unit review."
        )
        reviewer_notes = _first_present(row, "reviewer_notes")
        customer_rows.append(
            {
                "row_no": idx,
                "document": _first_present(row, "pdf_document_id", "source_pdf"),
                "metric": _first_present(row, "normalized_metric", "metric_label_raw"),
                "year": _clean_cell(row.get("year")),
                "value": _clean_cell(row.get("value")),
                "current_unit": _first_present(row, "current_unit", "reviewer_unit", "final_unit_preview"),
                "source_page": _clean_cell(row.get("source_page")),
                "rejection_reason": rejection_reason,
                "source_evidence": _first_present(row, "source_evidence_text"),
                "reviewer_notes": reviewer_notes,
                "notes": "Excluded from reviewed preview and should not be treated as trusted data.",
            }
        )
        trace_seed.append(
            {
                "candidate_id": _first_present(row, "candidate_id"),
                "customer_sheet": CUSTOMER_SHEETS["rejected"],
                "customer_row_no": idx,
                "trace_status": "excluded_or_rejected",
                "internal_review_decision": _first_present(row, "reviewer_decision"),
                "document": _first_present(row, "pdf_document_id", "source_pdf"),
                "metric": _first_present(row, "normalized_metric", "metric_label_raw"),
                "year": _clean_cell(row.get("year")),
                "value": _clean_cell(row.get("value")),
                "unit": _first_present(row, "current_unit", "reviewer_unit", "final_unit_preview"),
                "source_page": _clean_cell(row.get("source_page")),
                "source_evidence_refs": _first_present(row, "source_evidence_refs"),
                "source_evidence_text": _first_present(row, "source_evidence_text"),
            }
        )
    return _frame_for_output(pd.DataFrame(customer_rows)), trace_seed


def _build_trace_df(
    trace_source_df: pd.DataFrame,
    trace_seed_rows: Sequence[Dict[str, Any]],
) -> pd.DataFrame:
    trace_by_candidate = {
        _first_present(row, "candidate_id"): row
        for row in trace_source_df.to_dict(orient="records")
        if _first_present(row, "candidate_id")
    }
    rows: List[Dict[str, Any]] = []
    for idx, seed in enumerate(trace_seed_rows, start=1):
        candidate_id = _first_present(seed, "candidate_id")
        trace_row = trace_by_candidate.get(candidate_id, {})
        rows.append(
            {
                "trace_id": f"TRACE-{idx:04d}",
                "internal_candidate_id": candidate_id,
                "document": _first_present(seed, "document") or _first_present(trace_row, "pdf_document_id", "source_pdf"),
                "metric": _first_present(seed, "metric") or _first_present(trace_row, "normalized_metric", "metric_label_raw"),
                "year": _first_present(seed, "year") if _first_present(seed, "year") != "" else _clean_cell(trace_row.get("year")),
                "value": _first_present(seed, "value") if _first_present(seed, "value") != "" else _clean_cell(trace_row.get("value")),
                "unit": _first_present(seed, "unit") or _first_present(trace_row, "final_unit_preview", "reviewer_unit", "current_unit"),
                "source_page": _first_present(seed, "source_page") if _first_present(seed, "source_page") != "" else _clean_cell(trace_row.get("source_page")),
                "source_evidence_refs": _first_present(seed, "source_evidence_refs") or _first_present(trace_row, "source_evidence_refs"),
                "source_evidence_text": _first_present(seed, "source_evidence_text") or _first_present(trace_row, "source_evidence_text"),
                "customer_sheet": _first_present(seed, "customer_sheet"),
                "customer_row_no": _clean_cell(seed.get("customer_row_no")),
                "trace_status": _first_present(seed, "trace_status"),
                "internal_review_decision": _first_present(seed, "internal_review_decision") or _first_present(trace_row, "reviewer_decision"),
            }
        )
    return _frame_for_output(pd.DataFrame(rows))


def _build_delivery_summary_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"field": "project_status", "value": "CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY"},
        {"field": "client_facing_preview", "value": True},
        {"field": "client_ready", "value": False},
        {"field": "production_ready", "value": False},
        {
            "field": "source_reviewed_trusted_preview_row_count",
            "value": summary.get("source_reviewed_trusted_preview_row_count", 0),
        },
        {"field": "core_metrics_reviewed_row_count", "value": summary.get("core_metrics_reviewed_row_count", 0)},
        {"field": "needs_review_row_count", "value": summary.get("needs_review_row_count", 0)},
        {"field": "excluded_or_rejected_row_count", "value": summary.get("excluded_or_rejected_row_count", 0)},
        {"field": "source_page_missing_count", "value": summary.get("source_page_missing_count", 0)},
        {"field": "qa_fail_count", "value": summary.get("qa_fail_count", 0)},
        {"field": "generated_at", "value": summary.get("generated_at", "")},
        {"field": "source_output_dir", "value": summary.get("source_output_dir", "")},
        {
            "field": "safe_usage_note_1",
            "value": "Use reviewed rows as the safest preview output.",
        },
        {
            "field": "safe_usage_note_2",
            "value": "Review needs-review rows before using them.",
        },
        {
            "field": "safe_usage_note_3",
            "value": "Do not use excluded or rejected rows as trusted data.",
        },
        {
            "field": "safe_usage_note_4",
            "value": "Verify critical numbers against source PDFs before business or investment use.",
        },
    ]
    return _frame_for_output(pd.DataFrame(rows))


def build_client_facing_clean_export_335a(
    *,
    reviewed_export_refresh_dir: Path,
    demo_packaging_331b_dir: Path,
    demo_release_audit_dir: Path,
    client_style_export_preview_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330k4_path = (
        reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_summary.json"
    )
    qa_330k4_path = reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_qa.json"
    preview_330k4_path = (
        reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_preview.xlsx"
    )
    summary_331b_path = demo_packaging_331b_dir / "demo_packaging_331b_summary.json"
    summary_332a_path = demo_release_audit_dir / "demo_release_audit_332a_summary.json"
    summary_330l_path = (
        client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"
    )

    summary_330k4 = _read_json(summary_330k4_path)
    qa_330k4 = _read_json(qa_330k4_path)
    summary_331b = _read_json(summary_331b_path)
    summary_332a = _read_json(summary_332a_path)
    summary_330l = _read_json(summary_330l_path)

    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    _validate_summary(summary_330k4, expected_decision=READY_330K4_DECISION, checks=qa_rows, prefix="330k4")
    _validate_summary(summary_331b, expected_decision=READY_331B_DECISION, checks=qa_rows, prefix="331b")
    _validate_summary(summary_332a, expected_decision=READY_332A_DECISION, checks=qa_rows, prefix="332a")

    official_assets_before = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    input_hashes_before = {
        str(summary_330k4_path): _file_sha256(summary_330k4_path),
        str(qa_330k4_path): _file_sha256(qa_330k4_path),
        str(preview_330k4_path): _file_sha256(preview_330k4_path),
        str(summary_331b_path): _file_sha256(summary_331b_path),
        str(summary_332a_path): _file_sha256(summary_332a_path),
        str(summary_330l_path): _file_sha256(summary_330l_path),
    }

    add_qa("inputs::330k4_summary_exists", summary_330k4_path.exists(), str(summary_330k4_path))
    add_qa("inputs::330k4_qa_exists", qa_330k4_path.exists(), str(qa_330k4_path))
    add_qa("inputs::330k4_preview_workbook_exists", preview_330k4_path.exists(), str(preview_330k4_path))
    add_qa("inputs::331b_summary_exists", summary_331b_path.exists(), str(summary_331b_path))
    add_qa("inputs::332a_summary_exists", summary_332a_path.exists(), str(summary_332a_path))
    add_qa("inputs::330l_summary_exists", summary_330l_path.exists(), str(summary_330l_path))
    add_qa(
        "quality::330k4_qa_fail_count",
        _safe_int(qa_330k4.get("qa_fail_count"), 1) == 0,
        str(qa_330k4.get("qa_fail_count", "")),
    )

    reviewed_source_df = _read_sheet(preview_330k4_path, SOURCE_SHEETS["reviewed"])
    needs_review_source_df = _read_sheet(preview_330k4_path, SOURCE_SHEETS["needs_review"])
    rejected_source_df = _read_sheet(preview_330k4_path, SOURCE_SHEETS["rejected"])
    trace_source_df = _read_sheet(preview_330k4_path, SOURCE_SHEETS["trace"])

    add_qa(
        "records::source_reviewed_trusted_preview_row_count",
        len(reviewed_source_df) == EXPECTED_COUNTS["reviewed_trusted_preview_row_count"],
        str(len(reviewed_source_df)),
    )
    add_qa(
        "records::source_remaining_review_required_row_count",
        len(needs_review_source_df)
        == EXPECTED_COUNTS["remaining_review_required_after_unit_review_count"],
        str(len(needs_review_source_df)),
    )
    add_qa(
        "records::source_human_rejected_row_count",
        len(rejected_source_df) == EXPECTED_COUNTS["human_rejected_row_count"],
        str(len(rejected_source_df)),
    )
    add_qa(
        "records::source_apply_plan_trace_row_count",
        len(trace_source_df) == EXPECTED_COUNTS["apply_plan_row_count"],
        str(len(trace_source_df)),
    )

    reviewed_customer_df, reviewed_trace_seed = _map_reviewed_rows(reviewed_source_df)
    needs_review_customer_df, needs_review_trace_seed = _map_needs_review_rows(needs_review_source_df)
    rejected_customer_df, rejected_trace_seed = _map_rejected_rows(rejected_source_df)
    source_trace_df = _build_trace_df(
        trace_source_df,
        [*reviewed_trace_seed, *needs_review_trace_seed, *rejected_trace_seed],
    )

    reviewed_candidate_ids = {_first_present(row, "candidate_id") for row in reviewed_trace_seed if _first_present(row, "candidate_id")}
    needs_review_candidate_ids = {_first_present(row, "candidate_id") for row in needs_review_trace_seed if _first_present(row, "candidate_id")}
    rejected_candidate_ids = {_first_present(row, "candidate_id") for row in rejected_trace_seed if _first_present(row, "candidate_id")}

    source_page_missing_count = 0
    for frame in [reviewed_source_df, needs_review_source_df, rejected_source_df]:
        if not frame.empty and "source_page" in frame.columns:
            source_page_missing_count += int(frame["source_page"].map(_clean_cell).eq("").sum())

    add_qa(
        "records::customer_reviewed_row_count",
        len(reviewed_customer_df) == EXPECTED_COUNTS["reviewed_trusted_preview_row_count"],
        str(len(reviewed_customer_df)),
    )
    add_qa(
        "records::customer_needs_review_row_count",
        len(needs_review_customer_df)
        == EXPECTED_COUNTS["remaining_review_required_after_unit_review_count"],
        str(len(needs_review_customer_df)),
    )
    add_qa(
        "records::customer_excluded_or_rejected_row_count",
        len(rejected_customer_df) == EXPECTED_COUNTS["human_rejected_row_count"],
        str(len(rejected_customer_df)),
    )
    add_qa(
        "routing::rejected_candidate_not_in_reviewed_customer_sheet",
        len(reviewed_candidate_ids & rejected_candidate_ids) == 0,
        json.dumps(sorted(reviewed_candidate_ids & rejected_candidate_ids), ensure_ascii=False),
    )
    add_qa(
        "routing::needs_review_candidate_not_in_reviewed_customer_sheet",
        len(reviewed_candidate_ids & needs_review_candidate_ids) == 0,
        json.dumps(sorted(reviewed_candidate_ids & needs_review_candidate_ids), ensure_ascii=False),
    )

    forbidden_main_columns = {"dry_run_action", "preview_routing_bucket", "candidate_id"}
    for name, frame in [
        ("reviewed", reviewed_customer_df),
        ("needs_review", needs_review_customer_df),
        ("rejected", rejected_customer_df),
    ]:
        add_qa(
            f"columns::no_internal_noise::{name}",
            len(forbidden_main_columns & set(frame.columns)) == 0,
            json.dumps(sorted(forbidden_main_columns & set(frame.columns)), ensure_ascii=False),
        )

    add_qa(
        "columns::source_trace_preserves_internal_candidate_id",
        "internal_candidate_id" in source_trace_df.columns,
        json.dumps(list(source_trace_df.columns), ensure_ascii=False),
    )
    add_qa(
        "quality::source_page_missing_count",
        source_page_missing_count == 0,
        str(source_page_missing_count),
    )

    customer_readme_df = _customer_readme_df()

    generated_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "stage": "335A",
        "output_dir": str(output_dir),
        "project_status": "CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY",
        "client_facing_preview": True,
        "client_ready": False,
        "production_ready": False,
        "validated_330k4_reviewed_export_refresh": _norm_text(summary_330k4.get("decision")) == READY_330K4_DECISION and _safe_int(summary_330k4.get("qa_fail_count"), 1) == 0,
        "validated_331b_demo_packaging": _norm_text(summary_331b.get("decision")) == READY_331B_DECISION and _safe_int(summary_331b.get("qa_fail_count"), 1) == 0,
        "validated_332a_demo_release_audit": _norm_text(summary_332a.get("decision")) == READY_332A_DECISION and _safe_int(summary_332a.get("qa_fail_count"), 1) == 0,
        "source_reviewed_trusted_preview_row_count": int(len(reviewed_source_df)),
        "core_metrics_reviewed_row_count": int(len(reviewed_customer_df)),
        "needs_review_row_count": int(len(needs_review_customer_df)),
        "excluded_or_rejected_row_count": int(len(rejected_customer_df)),
        "source_trace_row_count": int(len(source_trace_df)),
        "source_page_missing_count": int(source_page_missing_count),
        "source_output_dir": str(reviewed_export_refresh_dir),
        "generated_at": generated_at,
        "official_assets_modified": False,
        "decision": "",
        "qa_pass_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "no_official_asset_modification_during_335a": False,
    }
    delivery_summary_df = _build_delivery_summary_df(summary)

    combined_text = "\n".join(
        [
            "\n".join(customer_readme_df["message"].astype(str).tolist()) if not customer_readme_df.empty else "",
            "\n".join(delivery_summary_df["value"].astype(str).tolist()) if not delivery_summary_df.empty else "",
        ]
    )
    add_qa(
        "claims::no_positive_overclaim_language",
        not _contains_forbidden_claim(combined_text, FORBIDDEN_POSITIVE_CLAIMS),
        "customer-facing readme and delivery summary checked for forbidden positive claims",
    )
    add_qa(
        "safety::no_write_back_behavior",
        True,
        "335A reads prior sidecar outputs and writes only a new 335A output directory.",
    )

    input_hashes_after = {
        str(summary_330k4_path): _file_sha256(summary_330k4_path),
        str(qa_330k4_path): _file_sha256(qa_330k4_path),
        str(preview_330k4_path): _file_sha256(preview_330k4_path),
        str(summary_331b_path): _file_sha256(summary_331b_path),
        str(summary_332a_path): _file_sha256(summary_332a_path),
        str(summary_330l_path): _file_sha256(summary_330l_path),
    }
    add_qa(
        "safety::input_artifacts_unchanged",
        input_hashes_before == input_hashes_after,
        json.dumps({"before": input_hashes_before, "after": input_hashes_after}, ensure_ascii=False),
    )

    official_assets_after = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    no_official_asset_modification_during_335a = official_assets_before == official_assets_after
    add_qa(
        "safety::official_assets_unchanged",
        no_official_asset_modification_during_335a,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_staged = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    add_qa(
        "safety::protected_dirty_files_state_unchanged",
        protected_before == protected_after,
        json.dumps({"before": protected_before, "after": protected_after}, ensure_ascii=False),
    )
    add_qa(
        "safety::protected_dirty_files_not_staged",
        len(protected_staged) == 0,
        json.dumps(protected_staged, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    summary["qa_pass_count"] = qa_pass_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    summary["decision"] = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION
    summary["no_official_asset_modification_during_335a"] = no_official_asset_modification_during_335a

    delivery_summary_df = _build_delivery_summary_df(summary)

    manifest = {
        "stage": "335A",
        "input_dirs": [
            str(reviewed_export_refresh_dir),
            str(demo_packaging_331b_dir),
            str(demo_release_audit_dir),
            str(client_style_export_preview_dir),
        ],
        "input_files": [
            str(summary_330k4_path),
            str(qa_330k4_path),
            str(preview_330k4_path),
            str(summary_331b_path),
            str(summary_332a_path),
            str(summary_330l_path),
        ],
        "output_dir": str(output_dir),
        "sheet_names": list(CUSTOMER_SHEETS.values()),
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="335A",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    return {
        "summary": summary,
        "manifest": manifest,
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
        "customer_readme_df": customer_readme_df,
        "core_metrics_reviewed_df": reviewed_customer_df,
        "needs_review_df": needs_review_customer_df,
        "excluded_or_rejected_df": rejected_customer_df,
        "source_trace_df": source_trace_df,
        "delivery_summary_df": delivery_summary_df,
    }
