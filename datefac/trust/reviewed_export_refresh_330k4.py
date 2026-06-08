from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.delivery_report_refresh_330j import _read_json
from datefac.trust.human_unit_review_330k2 import validate_330l_summary
from datefac.trust.human_unit_review_apply_simulation_330k3 import validate_330k2_summary
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_330L_DECISION = (
    "CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING"
)
READY_330K2_DECISION = "HUMAN_UNIT_REVIEW_330K2_READY_FOR_MANUAL_REVIEW"
READY_330K3_DECISION = (
    "HUMAN_UNIT_REVIEW_APPLY_SIMULATION_330K3_READY_FOR_REVIEW_SUMMARY_AND_NEXT_STEP_DECISION"
)
READY_DECISION = "REVIEWED_EXPORT_REFRESH_330K4_READY_FOR_PREVIEW_REVIEW"
NOT_READY_DECISION = "REVIEWED_EXPORT_REFRESH_330K4_NOT_READY"

DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR = Path(
    r"D:\_datefac\output\client_style_export_preview_330l"
)
DEFAULT_HUMAN_UNIT_REVIEW_DIR = Path(r"D:\_datefac\output\human_unit_review_330k2")
DEFAULT_APPLY_SIMULATION_DIR = Path(
    r"D:\_datefac\output\human_unit_review_apply_simulation_330k3"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\reviewed_export_refresh_330k4")

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
EXPECTED_DECISION_COUNTS = {
    "CONFIRM_UNIT": 2,
    "REJECT_UNIT": 18,
    "NEEDS_MORE_CONTEXT": 1,
    "KEEP_UNIT_UNKNOWN": 0,
}
PREVIEW_COLUMNS = [
    "candidate_id",
    "pdf_document_id",
    "source_page",
    "metric_label_raw",
    "normalized_metric",
    "year",
    "value",
    "final_unit_preview",
    "current_unit",
    "reviewer_unit",
    "confidence_level",
    "confidence_score",
    "upstream_routing_decision",
    "preview_routing_bucket",
    "risk_flags",
    "source_evidence_refs",
    "source_evidence_text",
    "reviewer_decision",
    "reviewer_notes",
    "dry_run_action",
    "preview_row_origin",
]
TRACE_COLUMNS = [
    "candidate_id",
    "pdf_document_id",
    "metric_label_raw",
    "normalized_metric",
    "year",
    "value",
    "current_unit",
    "reviewer_unit",
    "final_unit_preview",
    "source_page",
    "source_evidence_refs",
    "source_evidence_text",
    "parser_sources",
    "provenance_summary",
    "confidence_level",
    "confidence_score",
    "upstream_routing_decision",
    "risk_flags",
    "reviewer_decision",
    "reviewer_notes",
    "dry_run_action",
    "preview_routing_bucket",
    "preview_row_origin",
]
SHEET_README = "00_README"
SHEET_REVIEWED_TRUSTED_PREVIEW = "01_REVIEWED_TRUSTED_PREVIEW"
SHEET_REMAINING_REVIEW_REQUIRED = "02_REMAINING_REVIEW_REQUIRED"
SHEET_HUMAN_REJECTED = "03_HUMAN_REJECTED_BY_UNIT_REV"
SHEET_APPLY_PLAN_TRACE = "04_APPLY_PLAN_TRACE"
SHEET_QA_CONTEXT = "05_QA_CONTEXT"


def validate_330k3_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append(
            {"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail}
        )

    add(
        "readiness::330k3_decision",
        _norm_text(summary.get("decision")) == READY_330K3_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330k3_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330k3_apply_plan_row_count",
        _safe_int(summary.get("apply_plan_row_count"), -1) == 21,
        str(summary.get("apply_plan_row_count", "")),
    )
    add(
        "quality::330k3_confirm_unit_count",
        _safe_int(summary.get("confirm_unit_count"), -1) == 2,
        str(summary.get("confirm_unit_count", "")),
    )
    add(
        "quality::330k3_reject_unit_count",
        _safe_int(summary.get("reject_unit_count"), -1) == 18,
        str(summary.get("reject_unit_count", "")),
    )
    add(
        "quality::330k3_needs_more_context_count",
        _safe_int(summary.get("needs_more_context_count"), -1) == 1,
        str(summary.get("needs_more_context_count", "")),
    )
    add(
        "quality::330k3_keep_unit_unknown_count",
        _safe_int(summary.get("keep_unit_unknown_count"), -1) == 0,
        str(summary.get("keep_unit_unknown_count", "")),
    )
    add(
        "safety::330k3_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330k3")) is True,
        str(summary.get("no_official_asset_modification_during_330k3", "")),
    )
    return checks


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
        start = 0
        while True:
            idx = lowered.find(token, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 40) : idx]
            if "not " not in window and "not yet " not in window:
                return True
            start = idx + len(token)
    return False


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _frame_for_output(pd.read_excel(path, sheet_name=sheet_name))


def _read_apply_plan_json(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.get("apply_plan", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []
    return _frame_for_output(pd.DataFrame(rows))


def _decision_counts(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty or "reviewer_decision" not in df.columns:
        return {key: 0 for key in EXPECTED_DECISION_COUNTS}
    counts = {
        _norm_text(key): int(value)
        for key, value in df["reviewer_decision"].fillna("").value_counts().to_dict().items()
    }
    return {key: counts.get(key, 0) for key in EXPECTED_DECISION_COUNTS}


def _ensure_columns(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return out.loc[:, list(columns)].copy()


def _build_trace_df(
    apply_plan_df: pd.DataFrame,
    reviewed_df: pd.DataFrame,
    review_required_df: pd.DataFrame,
) -> pd.DataFrame:
    reviewed_by_candidate = {
        _normalize_text(row.get("candidate_id")): dict(row)
        for row in reviewed_df.to_dict(orient="records")
        if _normalize_text(row.get("candidate_id"))
    }
    review_required_by_candidate = {
        _normalize_text(row.get("candidate_id")): dict(row)
        for row in review_required_df.to_dict(orient="records")
        if _normalize_text(row.get("candidate_id"))
    }
    rows: List[Dict[str, Any]] = []
    for row in apply_plan_df.to_dict(orient="records"):
        candidate_id = _normalize_text(row.get("candidate_id"))
        reviewed_row = reviewed_by_candidate.get(candidate_id, {})
        review_required_row = review_required_by_candidate.get(candidate_id, {})
        reviewer_decision = _normalize_text(row.get("reviewer_decision"))
        final_unit_preview = _normalize_text(row.get("reviewer_unit")) or _normalize_text(
            row.get("current_unit")
        )
        if reviewer_decision == "CONFIRM_UNIT":
            preview_bucket = "REVIEWED_UNIT_CONFIRMED"
            preview_origin = "330K3_CONFIRMED_FROM_UNIT_REVIEW"
        elif reviewer_decision == "REJECT_UNIT":
            preview_bucket = "HUMAN_REJECTED_BY_UNIT_REVIEW"
            preview_origin = "330K3_REJECTED_FROM_UNIT_REVIEW"
        else:
            preview_bucket = "REMAINING_REVIEW_REQUIRED"
            preview_origin = "330K3_STILL_REVIEW_REQUIRED"
        rows.append(
            {
                "candidate_id": candidate_id,
                "pdf_document_id": _normalize_text(
                    row.get("pdf_document_id") or reviewed_row.get("pdf_document_id")
                ),
                "metric_label_raw": _normalize_text(reviewed_row.get("metric_label_raw")),
                "normalized_metric": _normalize_text(
                    row.get("normalized_metric") or reviewed_row.get("normalized_metric")
                ),
                "year": _normalize_text(row.get("year") or reviewed_row.get("year")),
                "value": _normalize_text(row.get("value") or reviewed_row.get("value")),
                "current_unit": _normalize_text(
                    row.get("current_unit") or reviewed_row.get("current_unit")
                ),
                "reviewer_unit": _normalize_text(
                    row.get("reviewer_unit") or reviewed_row.get("reviewer_unit")
                ),
                "final_unit_preview": final_unit_preview,
                "source_page": _normalize_text(reviewed_row.get("source_page")),
                "source_evidence_refs": _normalize_text(
                    reviewed_row.get("source_evidence_refs")
                    or review_required_row.get("evidence_refs")
                ),
                "source_evidence_text": _normalize_text(
                    reviewed_row.get("source_evidence_text") or review_required_row.get("row_text")
                ),
                "parser_sources": _normalize_text(reviewed_row.get("parser_sources")),
                "provenance_summary": _normalize_text(reviewed_row.get("provenance_summary")),
                "confidence_level": _normalize_text(review_required_row.get("confidence_level")),
                "confidence_score": _normalize_text(review_required_row.get("confidence_score")),
                "upstream_routing_decision": _normalize_text(
                    review_required_row.get("routing_decision")
                ),
                "risk_flags": _normalize_text(review_required_row.get("risk_flags")),
                "reviewer_decision": reviewer_decision,
                "reviewer_notes": _normalize_text(
                    row.get("reviewer_notes") or reviewed_row.get("reviewer_notes")
                ),
                "dry_run_action": _normalize_text(row.get("dry_run_action")),
                "preview_routing_bucket": preview_bucket,
                "preview_row_origin": preview_origin,
            }
        )
    return _frame_for_output(_ensure_columns(pd.DataFrame(rows), TRACE_COLUMNS))


def _build_baseline_trusted_df(trusted_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for row in trusted_df.to_dict(orient="records"):
        rows.append(
            {
                "candidate_id": _normalize_text(row.get("candidate_id")),
                "pdf_document_id": _normalize_text(row.get("source_pdf")),
                "source_page": _normalize_text(row.get("source_page")),
                "metric_label_raw": _normalize_text(row.get("metric_label_raw")),
                "normalized_metric": _normalize_text(row.get("normalized_metric")),
                "year": _normalize_text(row.get("year")),
                "value": _normalize_text(row.get("value")),
                "final_unit_preview": _normalize_text(row.get("unit")),
                "current_unit": _normalize_text(row.get("unit")),
                "reviewer_unit": "",
                "confidence_level": _normalize_text(row.get("confidence_level")),
                "confidence_score": _normalize_text(row.get("confidence_score")),
                "upstream_routing_decision": _normalize_text(row.get("routing_decision")),
                "preview_routing_bucket": "TRUSTED_PREVIEW",
                "risk_flags": _normalize_text(row.get("risk_flags")),
                "source_evidence_refs": _normalize_text(row.get("evidence_refs")),
                "source_evidence_text": _normalize_text(row.get("row_text")),
                "reviewer_decision": "",
                "reviewer_notes": "",
                "dry_run_action": "",
                "preview_row_origin": "330L_TRUSTED_BASELINE",
            }
        )
    return _frame_for_output(_ensure_columns(pd.DataFrame(rows), PREVIEW_COLUMNS))


def _build_preview_subset(trace_df: pd.DataFrame, decisions: Sequence[str]) -> pd.DataFrame:
    subset = trace_df.loc[trace_df["reviewer_decision"].isin(list(decisions))].copy()
    return _frame_for_output(_ensure_columns(subset, PREVIEW_COLUMNS))


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "section": "title",
            "content": "DateFac 330K4 reviewed export refresh",
        },
        {
            "section": "mode",
            "content": "This stage refreshes a reviewed export preview only.",
        },
        {
            "section": "writeback_policy",
            "content": "330K4 does not write back to the original 330L workbook and does not refresh production outputs.",
        },
        {
            "section": "claim_boundary",
            "content": "This workbook is not production-ready and not client-ready.",
        },
        {
            "section": "routing",
            "content": "CONFIRM_UNIT rows can surface in reviewed trusted preview; REJECT_UNIT rows remain excluded; NEEDS_MORE_CONTEXT and KEEP_UNIT_UNKNOWN remain review-required.",
        },
    ]
    return _frame_for_output(pd.DataFrame(rows))


def _build_qa_context_df(
    *,
    summary_330l: Mapping[str, Any],
    summary_330k2: Mapping[str, Any],
    summary_330k3: Mapping[str, Any],
    original_trusted_sheet_row_count: int,
    reviewed_trusted_preview_row_count: int,
    reviewed_unit_confirmed_count: int,
    human_rejected_row_count: int,
    remaining_review_required_count: int,
    duplicate_confirmed_overlap_count: int,
) -> pd.DataFrame:
    rows = [
        {"metric": "330l_trusted_sheet_row_count", "value": _safe_int(summary_330l.get("trusted_sheet_row_count"), 0)},
        {"metric": "330l_review_required_sheet_row_count", "value": _safe_int(summary_330l.get("review_required_sheet_row_count"), 0)},
        {"metric": "330k2_packaged_unit_review_row_count", "value": _safe_int(summary_330k2.get("packaged_unit_review_row_count"), 0)},
        {"metric": "330k3_apply_plan_row_count", "value": _safe_int(summary_330k3.get("apply_plan_row_count"), 0)},
        {"metric": "reviewed_trusted_preview_row_count", "value": reviewed_trusted_preview_row_count},
        {"metric": "original_trusted_sheet_row_count", "value": original_trusted_sheet_row_count},
        {"metric": "reviewed_unit_confirmed_count", "value": reviewed_unit_confirmed_count},
        {"metric": "human_rejected_row_count", "value": human_rejected_row_count},
        {"metric": "remaining_review_required_after_unit_review_count", "value": remaining_review_required_count},
        {"metric": "duplicate_confirmed_candidate_overlap_count", "value": duplicate_confirmed_overlap_count},
    ]
    return _frame_for_output(pd.DataFrame(rows))


def build_reviewed_export_refresh_330k4(
    *,
    client_style_export_preview_dir: Path,
    human_unit_review_dir: Path,
    apply_simulation_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330l_path = client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"
    preview_330l_path = (
        client_style_export_preview_dir / "client_style_export_preview_330l_preview.xlsx"
    )
    summary_330k2_path = human_unit_review_dir / "human_unit_review_330k2_summary.json"
    filled_review_path = human_unit_review_dir / "human_unit_review_330k2_review_filled.xlsx"
    summary_330k3_path = (
        apply_simulation_dir / "human_unit_review_apply_simulation_330k3_summary.json"
    )
    apply_plan_json_path = (
        apply_simulation_dir / "human_unit_review_apply_simulation_330k3_apply_plan.json"
    )

    summary_330l = _read_json(summary_330l_path)
    summary_330k2 = _read_json(summary_330k2_path)
    summary_330k3 = _read_json(summary_330k3_path)

    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    qa_rows = validate_330l_summary(summary_330l)
    qa_rows.extend(validate_330k2_summary(summary_330k2))
    qa_rows.extend(validate_330k3_summary(summary_330k3))

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append(
            {"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail}
        )

    official_assets_before = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    input_hashes_before = {
        str(preview_330l_path): _file_sha256(preview_330l_path),
        str(filled_review_path): _file_sha256(filled_review_path),
        str(apply_plan_json_path): _file_sha256(apply_plan_json_path),
    }

    add_qa("inputs::330l_preview_workbook_exists", preview_330l_path.exists(), str(preview_330l_path))
    add_qa("inputs::330k2_filled_review_workbook_exists", filled_review_path.exists(), str(filled_review_path))
    add_qa("inputs::330k3_apply_plan_json_exists", apply_plan_json_path.exists(), str(apply_plan_json_path))

    trusted_df = _read_sheet(preview_330l_path, "02_TRUSTED_SUGGESTIONS")
    review_required_df = _read_sheet(preview_330l_path, "03_REVIEW_REQUIRED")
    reviewed_df = _read_sheet(filled_review_path, "01_UNIT_REVIEW_QUEUE")
    apply_plan_df = _read_apply_plan_json(apply_plan_json_path)

    original_trusted_sheet_row_count = int(len(trusted_df))
    apply_plan_row_count = int(len(apply_plan_df))
    decision_counts = _decision_counts(apply_plan_df)
    baseline_trusted_preview_df = _build_baseline_trusted_df(trusted_df)
    trace_df = _build_trace_df(apply_plan_df, reviewed_df, review_required_df)

    confirmed_df = _build_preview_subset(trace_df, ["CONFIRM_UNIT"])
    rejected_df = _build_preview_subset(trace_df, ["REJECT_UNIT"])
    remaining_df = _build_preview_subset(trace_df, ["NEEDS_MORE_CONTEXT", "KEEP_UNIT_UNKNOWN"])

    trusted_candidate_ids = set(
        baseline_trusted_preview_df["candidate_id"].map(_normalize_text).tolist()
    )
    confirmed_candidate_ids = set(confirmed_df["candidate_id"].map(_normalize_text).tolist())
    rejected_candidate_ids = set(rejected_df["candidate_id"].map(_normalize_text).tolist())
    remaining_candidate_ids = set(remaining_df["candidate_id"].map(_normalize_text).tolist())

    confirmed_overlap_with_trusted = sorted(
        candidate_id
        for candidate_id in confirmed_candidate_ids
        if candidate_id and candidate_id in trusted_candidate_ids
    )
    confirmed_to_append_df = confirmed_df.loc[
        ~confirmed_df["candidate_id"].map(_normalize_text).isin(confirmed_overlap_with_trusted)
    ].copy()

    reviewed_trusted_preview_df = _frame_for_output(
        pd.concat([baseline_trusted_preview_df, confirmed_to_append_df], ignore_index=True)
    )
    reviewed_trusted_preview_row_count = int(len(reviewed_trusted_preview_df))
    reviewed_unit_confirmed_count = int(len(confirmed_df))
    human_rejected_row_count = int(len(rejected_df))
    remaining_review_required_count = int(len(remaining_df))

    readme_df = _build_readme_df()
    qa_context_df = _build_qa_context_df(
        summary_330l=summary_330l,
        summary_330k2=summary_330k2,
        summary_330k3=summary_330k3,
        original_trusted_sheet_row_count=original_trusted_sheet_row_count,
        reviewed_trusted_preview_row_count=reviewed_trusted_preview_row_count,
        reviewed_unit_confirmed_count=reviewed_unit_confirmed_count,
        human_rejected_row_count=human_rejected_row_count,
        remaining_review_required_count=remaining_review_required_count,
        duplicate_confirmed_overlap_count=len(confirmed_overlap_with_trusted),
    )

    production_forbidden = [
        "production-ready",
        "production ready",
        "ready for production",
        "already deployed to production",
    ]
    client_forbidden = ["client-ready", "client ready", "paid-client ready"]
    readme_text = "\n".join(readme_df["content"].astype(str).tolist()) if not readme_df.empty else ""

    add_qa(
        "quality::original_trusted_sheet_row_count",
        original_trusted_sheet_row_count == 96,
        str(original_trusted_sheet_row_count),
    )
    add_qa(
        "quality::apply_plan_row_count",
        apply_plan_row_count == 21,
        str(apply_plan_row_count),
    )
    add_qa(
        "quality::reviewed_row_count_alignment",
        len(reviewed_df) == 21,
        str(len(reviewed_df)),
    )
    for decision, expected in EXPECTED_DECISION_COUNTS.items():
        add_qa(
            f"quality::decision_count::{decision}",
            decision_counts.get(decision, 0) == expected,
            str(decision_counts.get(decision, 0)),
        )
    add_qa(
        "quality::confirmed_candidate_overlap_with_trusted_baseline",
        len(confirmed_overlap_with_trusted) == 0,
        json.dumps(confirmed_overlap_with_trusted, ensure_ascii=False),
    )
    add_qa(
        "quality::reviewed_trusted_preview_row_count",
        reviewed_trusted_preview_row_count == 98,
        str(reviewed_trusted_preview_row_count),
    )
    add_qa(
        "quality::human_rejected_row_count",
        human_rejected_row_count == 18,
        str(human_rejected_row_count),
    )
    add_qa(
        "quality::remaining_review_required_after_unit_review_count",
        remaining_review_required_count == 1,
        str(remaining_review_required_count),
    )
    add_qa(
        "routing::reject_unit_not_in_reviewed_trusted_preview",
        len(
            rejected_candidate_ids
            & set(reviewed_trusted_preview_df["candidate_id"].map(_normalize_text).tolist())
        )
        == 0,
        json.dumps(
            sorted(
                rejected_candidate_ids
                & set(reviewed_trusted_preview_df["candidate_id"].map(_normalize_text).tolist())
            ),
            ensure_ascii=False,
        ),
    )
    add_qa(
        "routing::needs_more_context_remains_review_required",
        remaining_candidate_ids
        == set(
            trace_df.loc[
                trace_df["reviewer_decision"].isin(["NEEDS_MORE_CONTEXT", "KEEP_UNIT_UNKNOWN"]),
                "candidate_id",
            ].map(_normalize_text)
        ),
        json.dumps(sorted(remaining_candidate_ids), ensure_ascii=False),
    )
    add_qa(
        "safety::no_write_back_behavior",
        bool(apply_plan_df["would_write_back"].eq(False).all()) if not apply_plan_df.empty else True,
        "330K4 reads the dry-run apply plan and writes only sidecar preview artifacts.",
    )
    add_qa(
        "safety::no_refresh_export_behavior",
        bool(apply_plan_df["would_refresh_export"].eq(False).all()) if not apply_plan_df.empty else True,
        "330K4 does not refresh the original 330L export in place.",
    )
    add_qa(
        "claims::no_production_ready_claims",
        not _contains_forbidden_claim(readme_text, production_forbidden),
        "readme text checked for production-ready claims",
    )
    add_qa(
        "claims::no_client_ready_claims",
        not _contains_forbidden_claim(readme_text, client_forbidden),
        "readme text checked for client-ready claims",
    )

    input_hashes_after = {
        str(preview_330l_path): _file_sha256(preview_330l_path),
        str(filled_review_path): _file_sha256(filled_review_path),
        str(apply_plan_json_path): _file_sha256(apply_plan_json_path),
    }
    add_qa(
        "safety::input_artifacts_unchanged",
        input_hashes_before == input_hashes_after,
        json.dumps({"before": input_hashes_before, "after": input_hashes_after}, ensure_ascii=False),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    preview_output_path = output_dir / "reviewed_export_refresh_330k4_preview.xlsx"

    with pd.ExcelWriter(preview_output_path, engine="openpyxl") as writer:
        readme_df.to_excel(writer, sheet_name=SHEET_README, index=False)
        reviewed_trusted_preview_df.to_excel(
            writer, sheet_name=SHEET_REVIEWED_TRUSTED_PREVIEW, index=False
        )
        remaining_df.to_excel(writer, sheet_name=SHEET_REMAINING_REVIEW_REQUIRED, index=False)
        rejected_df.to_excel(writer, sheet_name=SHEET_HUMAN_REJECTED, index=False)
        trace_df.to_excel(writer, sheet_name=SHEET_APPLY_PLAN_TRACE, index=False)
        qa_context_df.to_excel(writer, sheet_name=SHEET_QA_CONTEXT, index=False)

    add_qa(
        "outputs::reviewed_preview_workbook_generated",
        preview_output_path.exists(),
        str(preview_output_path),
    )

    official_assets_after = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    no_official_asset_modification_during_330k4 = official_assets_before == official_assets_after
    add_qa(
        "safety::official_assets_unchanged",
        no_official_asset_modification_during_330k4,
        json.dumps(
            {"before": official_assets_before, "after": official_assets_after},
            ensure_ascii=False,
        ),
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

    summary = {
        "stage": "330K4",
        "output_dir": str(output_dir),
        "validated_330l_preview": all(
            row.get("status") == "PASS" for row in validate_330l_summary(summary_330l)
        ),
        "validated_330k2_review_package": all(
            row.get("status") == "PASS" for row in validate_330k2_summary(summary_330k2)
        ),
        "validated_330k3_apply_simulation": all(
            row.get("status") == "PASS" for row in validate_330k3_summary(summary_330k3)
        ),
        "preview_workbook_path": str(preview_output_path),
        "preview_workbook_generated": preview_output_path.exists(),
        "original_trusted_sheet_row_count": original_trusted_sheet_row_count,
        "reviewed_unit_confirmed_count": reviewed_unit_confirmed_count,
        "human_rejected_row_count": human_rejected_row_count,
        "remaining_review_required_after_unit_review_count": remaining_review_required_count,
        "reviewed_trusted_preview_row_count": reviewed_trusted_preview_row_count,
        "duplicate_confirmed_candidate_overlap_count": len(confirmed_overlap_with_trusted),
        "apply_plan_row_count": apply_plan_row_count,
        "confirm_unit_count": decision_counts.get("CONFIRM_UNIT", 0),
        "reject_unit_count": decision_counts.get("REJECT_UNIT", 0),
        "needs_more_context_count": decision_counts.get("NEEDS_MORE_CONTEXT", 0),
        "keep_unit_unknown_count": decision_counts.get("KEEP_UNIT_UNKNOWN", 0),
        "no_official_asset_modification_during_330k4": no_official_asset_modification_during_330k4,
        "official_assets_modified": False,
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    manifest = {
        "stage": "330K4",
        "input_dirs": [
            str(client_style_export_preview_dir),
            str(human_unit_review_dir),
            str(apply_simulation_dir),
        ],
        "input_files": [
            str(preview_330l_path),
            str(filled_review_path),
            str(apply_plan_json_path),
        ],
        "output_dir": str(output_dir),
        "preview_workbook_path": str(preview_output_path),
        "sheet_names": [
            SHEET_README,
            SHEET_REVIEWED_TRUSTED_PREVIEW,
            SHEET_REMAINING_REVIEW_REQUIRED,
            SHEET_HUMAN_REJECTED,
            SHEET_APPLY_PLAN_TRACE,
            SHEET_QA_CONTEXT,
        ],
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="330K4",
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
        "readme_df": readme_df,
        "reviewed_trusted_preview_df": reviewed_trusted_preview_df,
        "remaining_review_required_df": remaining_df,
        "human_rejected_df": rejected_df,
        "apply_plan_trace_df": trace_df,
        "qa_context_df": qa_context_df,
    }
