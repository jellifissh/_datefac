from __future__ import annotations

import hashlib
import json
import subprocess
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


READY_330K2_DECISION = "HUMAN_UNIT_REVIEW_330K2_READY_FOR_MANUAL_REVIEW"
READY_331A_DECISION = "DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW"
READY_330L_DECISION = (
    "CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING"
)
READY_DECISION = (
    "HUMAN_UNIT_REVIEW_APPLY_SIMULATION_330K3_READY_FOR_REVIEW_SUMMARY_AND_NEXT_STEP_DECISION"
)
NOT_READY_DECISION = "HUMAN_UNIT_REVIEW_APPLY_SIMULATION_330K3_NOT_READY"

DEFAULT_FILLED_REVIEW_WORKBOOK = Path(
    r"D:\_datefac\output\human_unit_review_330k2\human_unit_review_330k2_review_filled.xlsx"
)
DEFAULT_HUMAN_UNIT_REVIEW_DIR = Path(r"D:\_datefac\output\human_unit_review_330k2")
DEFAULT_DEMO_PACKAGING_DIR = Path(r"D:\_datefac\output\demo_packaging_331a")
DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR = Path(r"D:\_datefac\output\client_style_export_preview_330l")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\human_unit_review_apply_simulation_330k3")

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
ALLOWED_DECISIONS = [
    "CONFIRM_UNIT",
    "REJECT_UNIT",
    "KEEP_UNIT_UNKNOWN",
    "NEEDS_MORE_CONTEXT",
]
EXPECTED_DECISION_COUNTS = {
    "CONFIRM_UNIT": 2,
    "REJECT_UNIT": 18,
    "KEEP_UNIT_UNKNOWN": 0,
    "NEEDS_MORE_CONTEXT": 1,
}
ACTION_BY_DECISION = {
    "CONFIRM_UNIT": "WOULD_CONFIRM_OR_SET_UNIT",
    "REJECT_UNIT": "WOULD_REJECT_FROM_TRUSTED_EXPORT",
    "KEEP_UNIT_UNKNOWN": "WOULD_KEEP_UNIT_UNKNOWN_REVIEW_REQUIRED",
    "NEEDS_MORE_CONTEXT": "WOULD_KEEP_REVIEW_REQUIRED_FOR_SOURCE_CHECK",
}


def validate_330k2_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::330k2_decision",
        _norm_text(summary.get("decision")) == READY_330K2_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330k2_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330k2_packaged_unit_review_row_count",
        _safe_int(summary.get("packaged_unit_review_row_count"), -1) == 21,
        str(summary.get("packaged_unit_review_row_count", "")),
    )
    add(
        "quality::330k2_source_page_missing_count",
        _safe_int(summary.get("source_page_missing_count"), -1) == 0,
        str(summary.get("source_page_missing_count", "")),
    )
    add(
        "quality::330k2_unit_missing_count",
        _safe_int(summary.get("unit_missing_count"), -1) == 18,
        str(summary.get("unit_missing_count", "")),
    )
    add(
        "quality::330k2_unit_conflict_risk_count",
        _safe_int(summary.get("unit_conflict_risk_count"), -1) == 12,
        str(summary.get("unit_conflict_risk_count", "")),
    )
    add(
        "safety::330k2_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330k2")) is True,
        str(summary.get("no_official_asset_modification_during_330k2", "")),
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


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _frame_for_output(pd.read_excel(path, sheet_name=sheet_name))


def _decision_counts(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty or "reviewer_decision" not in df.columns:
        return {key: 0 for key in ALLOWED_DECISIONS}
    counts = {_norm_text(key): int(value) for key, value in df["reviewer_decision"].fillna("").value_counts().to_dict().items()}
    return {key: counts.get(key, 0) for key in ALLOWED_DECISIONS}


def _build_apply_plan(reviewed_df: pd.DataFrame) -> pd.DataFrame:
    if reviewed_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for row in reviewed_df.to_dict(orient="records"):
        reviewer_decision = _normalize_text(row.get("reviewer_decision"))
        rows.append(
            {
                "candidate_id": _normalize_text(row.get("candidate_id")),
                "pdf_document_id": _normalize_text(row.get("pdf_document_id")),
                "normalized_metric": _normalize_text(row.get("normalized_metric")),
                "year": _normalize_text(row.get("year")),
                "value": _normalize_text(row.get("value")),
                "current_unit": _normalize_text(row.get("current_unit")),
                "reviewer_unit": _normalize_text(row.get("reviewer_unit")),
                "reviewer_decision": reviewer_decision,
                "reviewer_notes": _normalize_text(row.get("reviewer_notes")),
                "dry_run_action": ACTION_BY_DECISION.get(reviewer_decision, ""),
                "would_write_back": False,
                "would_refresh_export": False,
                "would_modify_official_assets": False,
            }
        )
    return _frame_for_output(pd.DataFrame(rows))


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {"section": "title", "content": "DateFac 330K3 human unit review apply simulation"},
        {"section": "mode", "content": "This stage is a dry-run apply simulation only."},
        {"section": "writeback_policy", "content": "330K3 does not write back to the 330L workbook and does not refresh the client-style export."},
        {"section": "claim_boundary", "content": "This artifact set is not production-ready and not client-ready."},
        {"section": "allowed_decisions", "content": "Allowed reviewer_decision values: CONFIRM_UNIT | REJECT_UNIT | KEEP_UNIT_UNKNOWN | NEEDS_MORE_CONTEXT"},
    ]
    return _frame_for_output(pd.DataFrame(rows))


def build_human_unit_review_apply_simulation_330k3(
    *,
    filled_review_workbook: Path,
    human_unit_review_dir: Path,
    demo_packaging_dir: Path,
    client_style_export_preview_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330k2_path = human_unit_review_dir / "human_unit_review_330k2_summary.json"
    summary_331a_path = demo_packaging_dir / "demo_packaging_331a_summary.json"
    summary_330l_path = client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"

    summary_330k2 = _read_json(summary_330k2_path)
    summary_331a = _read_json(summary_331a_path)
    summary_330l = _read_json(summary_330l_path)

    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    qa_rows = validate_330k2_summary(summary_330k2)

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    add_qa(
        "readiness::331a_decision",
        _norm_text(summary_331a.get("decision")) == READY_331A_DECISION,
        _norm_text(summary_331a.get("decision")),
    )
    add_qa(
        "readiness::330l_decision",
        _norm_text(summary_330l.get("decision")) == READY_330L_DECISION,
        _norm_text(summary_330l.get("decision")),
    )
    add_qa("inputs::filled_review_workbook_exists", filled_review_workbook.exists(), str(filled_review_workbook))

    reviewed_df = _read_sheet(filled_review_workbook, "01_UNIT_REVIEW_QUEUE")
    reviewed_row_count = int(len(reviewed_df))
    blank_reviewer_decision_count = int((reviewed_df["reviewer_decision"].map(_normalize_text) == "").sum()) if not reviewed_df.empty else 0
    decision_counts = _decision_counts(reviewed_df)
    invalid_decisions = sorted(
        {
            _normalize_text(value)
            for value in reviewed_df.get("reviewer_decision", pd.Series(dtype=object)).tolist()
            if _normalize_text(value) and _normalize_text(value) not in ALLOWED_DECISIONS
        }
    )

    apply_plan_df = _build_apply_plan(reviewed_df)
    apply_plan_row_count = int(len(apply_plan_df))

    output_dir.mkdir(parents=True, exist_ok=True)
    apply_plan_json_path = output_dir / "human_unit_review_apply_simulation_330k3_apply_plan.json"
    apply_plan_xlsx_path = output_dir / "human_unit_review_apply_simulation_330k3_apply_plan.xlsx"
    readme_df = _build_readme_df()

    apply_plan_json_path.write_text(
        json.dumps(apply_plan_df.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pd.ExcelWriter(apply_plan_xlsx_path, engine="openpyxl") as writer:
        readme_df.to_excel(writer, sheet_name="00_README", index=False)
        apply_plan_df.to_excel(writer, sheet_name="01_APPLY_PLAN", index=False)
        _frame_for_output(
            pd.DataFrame([{"reviewer_decision": key, "count": value} for key, value in decision_counts.items()])
        ).to_excel(writer, sheet_name="02_DECISION_COUNTS", index=False)

    production_forbidden = ["production-ready", "production ready", "ready for production", "already deployed to production"]
    client_forbidden = ["client-ready", "client ready", "paid-client ready"]
    readme_text = "\n".join(readme_df["content"].astype(str).tolist()) if not readme_df.empty else ""

    add_qa("quality::reviewed_row_count", reviewed_row_count == 21, str(reviewed_row_count))
    add_qa("quality::no_blank_reviewer_decision", blank_reviewer_decision_count == 0, str(blank_reviewer_decision_count))
    add_qa("quality::allowed_reviewer_decision_values", len(invalid_decisions) == 0, json.dumps(invalid_decisions, ensure_ascii=False))
    for decision, expected in EXPECTED_DECISION_COUNTS.items():
        add_qa(f"quality::decision_count::{decision}", decision_counts.get(decision, 0) == expected, str(decision_counts.get(decision, 0)))
    add_qa("quality::apply_plan_row_count", apply_plan_row_count == 21, str(apply_plan_row_count))
    add_qa(
        "safety::no_write_back_behavior",
        bool(apply_plan_df["would_write_back"].eq(False).all()) if not apply_plan_df.empty else True,
        "dry-run actions only; no write-back behavior exists.",
    )
    add_qa(
        "safety::no_refresh_export_behavior",
        bool(apply_plan_df["would_refresh_export"].eq(False).all()) if not apply_plan_df.empty else True,
        "330K3 does not refresh the client-style export.",
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

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330k3 = official_assets_before == official_assets_after
    add_qa(
        "safety::official_assets_unchanged",
        no_official_asset_modification_during_330k3,
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
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "330K3",
        "output_dir": str(output_dir),
        "validated_330k2_review_package": all(row.get("status") == "PASS" for row in validate_330k2_summary(summary_330k2)),
        "reviewed_row_count": reviewed_row_count,
        "confirm_unit_count": decision_counts.get("CONFIRM_UNIT", 0),
        "reject_unit_count": decision_counts.get("REJECT_UNIT", 0),
        "needs_more_context_count": decision_counts.get("NEEDS_MORE_CONTEXT", 0),
        "keep_unit_unknown_count": decision_counts.get("KEEP_UNIT_UNKNOWN", 0),
        "apply_plan_row_count": apply_plan_row_count,
        "source_page_missing_count": _safe_int(summary_330k2.get("source_page_missing_count"), 0),
        "unit_missing_count": _safe_int(summary_330k2.get("unit_missing_count"), 0),
        "unit_conflict_risk_count": _safe_int(summary_330k2.get("unit_conflict_risk_count"), 0),
        "no_official_asset_modification_during_330k3": no_official_asset_modification_during_330k3,
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    manifest = {
        "stage": "330K3",
        "filled_review_workbook": str(filled_review_workbook),
        "human_unit_review_dir": str(human_unit_review_dir),
        "demo_packaging_dir": str(demo_packaging_dir),
        "client_style_export_preview_dir": str(client_style_export_preview_dir),
        "output_dir": str(output_dir),
        "allowed_reviewer_decisions": list(ALLOWED_DECISIONS),
        "dry_run_action_mapping": dict(ACTION_BY_DECISION),
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="330K3",
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
        "apply_plan_json": apply_plan_df.to_dict(orient="records"),
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(pd.DataFrame([{"qa_pass_count": qa_pass_count, "qa_fail_count": qa_fail_count, "decision": summary["decision"]}])),
        "qa_checks_df": qa_df,
        "readme_df": readme_df,
        "apply_plan_df": apply_plan_df,
    }
