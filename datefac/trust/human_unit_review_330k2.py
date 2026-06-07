from __future__ import annotations

import hashlib
import json
import subprocess
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


READY_330L_DECISION = (
    "CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING"
)
READY_331A_DECISION = "DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW"
READY_DECISION = "HUMAN_UNIT_REVIEW_330K2_READY_FOR_MANUAL_REVIEW"
NOT_READY_DECISION = "HUMAN_UNIT_REVIEW_330K2_NOT_READY"

DEFAULT_DEMO_PACKAGING_DIR = Path(r"D:\_datefac\output\demo_packaging_331a")
DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR = Path(r"D:\_datefac\output\client_style_export_preview_330l")
DEFAULT_UNIT_SIGNAL_REVIEW_DIR = Path(r"D:\_datefac\output\unit_signal_review_330k")
DEFAULT_DELIVERY_REPORT_REFRESH_DIR = Path(
    r"D:\_datefac\output\delivery_report_refresh_after_330k_330j2"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\human_unit_review_330k2")

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
REVIEWER_DECISIONS = [
    "CONFIRM_UNIT",
    "REJECT_UNIT",
    "KEEP_UNIT_UNKNOWN",
    "NEEDS_MORE_CONTEXT",
]


def validate_330l_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::330l_decision",
        _norm_text(summary.get("decision")) == READY_330L_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330l_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330l_preview_workbook_generated",
        bool(summary.get("preview_workbook_generated")) is True,
        str(summary.get("preview_workbook_generated", "")),
    )
    add(
        "records::330l_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 117,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "records::330l_strict_deduped_candidate_count",
        _safe_int(summary.get("strict_deduped_candidate_count"), -1) == 117,
        str(summary.get("strict_deduped_candidate_count", "")),
    )
    add(
        "quality::330l_unit_missing_count",
        _safe_int(summary.get("unit_missing_count"), -1) == 18,
        str(summary.get("unit_missing_count", "")),
    )
    add(
        "quality::330l_unit_conflict_risk_count",
        _safe_int(summary.get("unit_conflict_risk_count"), -1) == 12,
        str(summary.get("unit_conflict_risk_count", "")),
    )
    add(
        "quality::330l_delivery_readiness_judgment",
        _norm_text(summary.get("delivery_readiness_judgment")) == "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
        _norm_text(summary.get("delivery_readiness_judgment")),
    )
    add(
        "safety::330l_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330l")) is True,
        str(summary.get("no_official_asset_modification_during_330l", "")),
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


def _read_workbook_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _frame_for_output(pd.read_excel(path, sheet_name=sheet_name))


def _load_optional_prepared_rows(unit_signal_review_summary: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    optional_dir = _norm_text(unit_signal_review_summary.get("optional_fixed_prepared_output_dir"))
    if not optional_dir:
        return {}
    rows_path = Path(optional_dir) / "unfamiliar_candidate_rows.jsonl"
    if not rows_path.exists():
        return {}
    rows = _read_jsonl_rows(rows_path)
    return {
        _norm_text(row.get("candidate_id")): dict(row)
        for row in rows
        if _norm_text(row.get("candidate_id"))
    }


def _build_review_queue(
    review_sample_df: pd.DataFrame,
    review_required_df: pd.DataFrame,
    prepared_rows_by_candidate: Mapping[str, Mapping[str, Any]],
) -> pd.DataFrame:
    if review_sample_df.empty:
        return pd.DataFrame()
    review_required_by_candidate = {
        _norm_text(row.get("candidate_id")): row
        for row in review_required_df.to_dict(orient="records")
        if _norm_text(row.get("candidate_id"))
    }
    rows: List[Dict[str, Any]] = []
    for row in review_sample_df.to_dict(orient="records"):
        candidate_id = _norm_text(row.get("candidate_id"))
        review_required_row = review_required_by_candidate.get(candidate_id, {})
        prepared_row = dict(prepared_rows_by_candidate.get(candidate_id, {}))
        current_unit = _normalize_text(row.get("unit") or prepared_row.get("unit"))
        risk_flags_text = _normalize_text(row.get("risk_flags") or review_required_row.get("risk_flags") or prepared_row.get("risk_flags"))
        evidence_refs = _normalize_text(review_required_row.get("evidence_refs") or prepared_row.get("evidence_refs"))
        parser_sources = prepared_row.get("parser_sources", [])
        if isinstance(parser_sources, list):
            parser_sources_text = " | ".join(_normalize_text(item) for item in parser_sources if _normalize_text(item))
        else:
            parser_sources_text = _normalize_text(parser_sources)
        provenance_summary = " | ".join(
            [
                token
                for token in [
                    _normalize_text(prepared_row.get("source_artifact")),
                    _normalize_text(prepared_row.get("table_id")),
                    _normalize_text(prepared_row.get("unit_fix_method")),
                    _normalize_text(prepared_row.get("unit_fix_source_text")),
                ]
                if token
            ]
        )
        rows.append(
            {
                "candidate_id": candidate_id,
                "pdf_document_id": _normalize_text(row.get("source_pdf")),
                "metric_label_raw": _normalize_text(row.get("metric_label_raw")),
                "normalized_metric": _normalize_text(row.get("normalized_metric")),
                "year": _normalize_text(prepared_row.get("year") or review_required_row.get("year")),
                "value": _normalize_text(prepared_row.get("value") or review_required_row.get("value")),
                "current_unit": current_unit,
                "unit_missing_flag": current_unit == "",
                "unit_conflict_risk_flag": "UNIT_CONFLICT" in risk_flags_text,
                "source_page": _normalize_text(row.get("source_page")),
                "source_evidence_text": _normalize_text(row.get("row_text") or review_required_row.get("row_text") or prepared_row.get("row_text")),
                "source_evidence_refs": evidence_refs,
                "parser_sources": parser_sources_text,
                "provenance_summary": provenance_summary,
                "recommended_reviewer_action": _normalize_text(row.get("recommended_human_decision")),
                "reviewer_unit": "",
                "reviewer_decision": "",
                "reviewer_notes": "",
            }
        )
    return _frame_for_output(pd.DataFrame(rows))


def _build_readme_df(summary_330l: Mapping[str, Any], summary_331a: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"section": "title", "content": "DateFac 330K2 human unit review package"},
        {"section": "project_status", "content": _norm_text(summary_331a.get("project_status")) or "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS"},
        {"section": "scope", "content": "This workbook packages exactly the 21 manual unit-review rows from the 330L / 331A demo state."},
        {"section": "claim_boundary", "content": "This is a manual-review package only. It is not production-ready and not client-ready."},
        {"section": "reviewer_decisions", "content": "Allowed reviewer_decision values: CONFIRM_UNIT | REJECT_UNIT | KEEP_UNIT_UNKNOWN | NEEDS_MORE_CONTEXT"},
        {"section": "writeback_policy", "content": "330K2 does not apply changes, does not write back to production, and does not modify official assets."},
        {"section": "upstream_counts", "content": f"Upstream unit_missing_count={_safe_int(summary_330l.get('unit_missing_count'), 0)}, unit_conflict_risk_count={_safe_int(summary_330l.get('unit_conflict_risk_count'), 0)}"},
    ]
    return _frame_for_output(pd.DataFrame(rows))


def _build_context_df(summary_330l: Mapping[str, Any], summary_330j2: Mapping[str, Any], summary_331a: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"metric": "project_status", "value": _norm_text(summary_331a.get("project_status"))},
        {"metric": "prepared_candidate_row_count", "value": _safe_int(summary_330l.get("prepared_candidate_row_count"), 0)},
        {"metric": "trusted_sheet_row_count", "value": _safe_int(summary_330l.get("trusted_sheet_row_count"), 0)},
        {"metric": "review_required_sheet_row_count", "value": _safe_int(summary_330l.get("review_required_sheet_row_count"), 0)},
        {"metric": "unit_review_sheet_row_count", "value": _safe_int(summary_330l.get("unit_review_sheet_row_count"), 0)},
        {"metric": "source_page_missing_count", "value": _safe_int(summary_330j2.get("source_page_missing_count"), 0)},
        {"metric": "unit_missing_count", "value": _safe_int(summary_330j2.get("unit_missing_count"), 0)},
        {"metric": "unit_conflict_risk_count", "value": _safe_int(summary_330j2.get("unit_conflict_risk_count"), 0)},
        {"metric": "delivery_readiness_judgment", "value": _norm_text(summary_330l.get("delivery_readiness_judgment"))},
    ]
    return _frame_for_output(pd.DataFrame(rows))


def build_human_unit_review_330k2(
    *,
    demo_packaging_dir: Path,
    client_style_export_preview_dir: Path,
    unit_signal_review_dir: Path,
    delivery_report_refresh_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330l_path = client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"
    workbook_330l_path = client_style_export_preview_dir / "client_style_export_preview_330l_preview.xlsx"
    summary_331a_path = demo_packaging_dir / "demo_packaging_331a_summary.json"
    summary_330k_path = unit_signal_review_dir / "unit_signal_review_330k_summary.json"
    summary_330j2_path = delivery_report_refresh_dir / "delivery_report_refresh_after_330k_330j2_summary.json"

    summary_330l = _read_json(summary_330l_path)
    summary_331a = _read_json(summary_331a_path)
    summary_330k = _read_json(summary_330k_path)
    summary_330j2 = _read_json(summary_330j2_path)

    review_required_df = _read_workbook_sheet(workbook_330l_path, "03_REVIEW_REQUIRED")
    review_sample_df = _read_workbook_sheet(workbook_330l_path, "04_UNIT_REVIEW_SAMPLE")
    prepared_rows_by_candidate = _load_optional_prepared_rows(summary_330k)

    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    qa_rows = validate_330l_summary(summary_330l)

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
        "readiness::331a_qa_fail_count",
        _safe_int(summary_331a.get("qa_fail_count"), 1) == 0,
        str(summary_331a.get("qa_fail_count", "")),
    )
    add_qa("inputs::330l_workbook_exists", workbook_330l_path.exists(), str(workbook_330l_path))
    add_qa("records::review_sample_row_count", len(review_sample_df) == 21, str(len(review_sample_df)))
    add_qa("records::review_required_row_count", len(review_required_df) >= 21, str(len(review_required_df)))

    review_queue_df = _build_review_queue(
        review_sample_df=review_sample_df,
        review_required_df=review_required_df,
        prepared_rows_by_candidate=prepared_rows_by_candidate,
    )
    packaged_unit_review_row_count = int(len(review_queue_df))
    source_page_missing_count = int((review_queue_df["source_page"].map(_normalize_text) == "").sum()) if not review_queue_df.empty else 0
    unit_missing_count = int(review_queue_df["unit_missing_flag"].sum()) if not review_queue_df.empty else 0
    unit_conflict_risk_count = int(review_queue_df["unit_conflict_risk_flag"].sum()) if not review_queue_df.empty else 0

    readme_df = _build_readme_df(summary_330l, summary_331a)
    context_df = _build_context_df(summary_330l, summary_330j2, summary_331a)

    review_template_path = output_dir / "human_unit_review_330k2_review_template.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(review_template_path, engine="openpyxl") as writer:
        readme_df.to_excel(writer, sheet_name="00_README", index=False)
        review_queue_df.to_excel(writer, sheet_name="01_UNIT_REVIEW_QUEUE", index=False)
        context_df.to_excel(writer, sheet_name="02_UPSTREAM_QA_CONTEXT", index=False)

    production_forbidden = ["production-ready", "production ready", "ready for production", "already deployed to production"]
    client_forbidden = ["client-ready", "client ready", "paid-client ready"]
    workbook_readme_text = "\n".join(readme_df["content"].astype(str).tolist()) if not readme_df.empty else ""

    add_qa("quality::packaged_unit_review_row_count", packaged_unit_review_row_count == 21, str(packaged_unit_review_row_count))
    add_qa("quality::source_page_missing_count", source_page_missing_count == 0, str(source_page_missing_count))
    add_qa(
        "quality::unit_missing_count",
        unit_missing_count == _safe_int(summary_330j2.get("unit_missing_count"), 18),
        str(unit_missing_count),
    )
    add_qa(
        "quality::unit_conflict_risk_count",
        unit_conflict_risk_count == _safe_int(summary_330j2.get("unit_conflict_risk_count"), 12),
        str(unit_conflict_risk_count),
    )
    add_qa(
        "claims::no_production_ready_claims",
        not _contains_forbidden_claim(workbook_readme_text, production_forbidden),
        "readme text checked for production-ready claims",
    )
    add_qa(
        "claims::no_client_ready_claims",
        not _contains_forbidden_claim(workbook_readme_text, client_forbidden),
        "readme text checked for client-ready claims",
    )
    add_qa(
        "safety::no_apply_or_writeback_behavior",
        True,
        "330K2 packages reviewer rows only and performs no apply/write-back behavior.",
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330k2 = official_assets_before == official_assets_after
    add_qa(
        "safety::official_assets_unchanged",
        no_official_asset_modification_during_330k2,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_staged_names = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    add_qa(
        "safety::protected_dirty_files_state_unchanged",
        protected_before == protected_after,
        json.dumps({"before": protected_before, "after": protected_after}, ensure_ascii=False),
    )
    add_qa(
        "safety::protected_dirty_files_not_staged",
        len(protected_staged_names) == 0,
        json.dumps(protected_staged_names, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "330K2",
        "output_dir": str(output_dir),
        "validated_330l_export_preview": all(row.get("status") == "PASS" for row in validate_330l_summary(summary_330l)),
        "validated_331a_demo_packaging": _norm_text(summary_331a.get("decision")) == READY_331A_DECISION and _safe_int(summary_331a.get("qa_fail_count"), 1) == 0,
        "project_status": _norm_text(summary_331a.get("project_status")) or "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
        "packaged_unit_review_row_count": packaged_unit_review_row_count,
        "review_template_workbook_generated": review_template_path.exists(),
        "review_template_workbook_path": str(review_template_path),
        "source_page_missing_count": source_page_missing_count,
        "unit_missing_count": unit_missing_count,
        "unit_conflict_risk_count": unit_conflict_risk_count,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330k2": no_official_asset_modification_during_330k2,
        "protected_dirty_files_status_before": protected_before,
        "protected_dirty_files_status_after": protected_after,
        "protected_dirty_files_staged": protected_staged_names,
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    manifest = {
        "stage": "330K2",
        "input_dirs": [
            str(demo_packaging_dir),
            str(client_style_export_preview_dir),
            str(unit_signal_review_dir),
            str(delivery_report_refresh_dir),
        ],
        "output_dir": str(output_dir),
        "review_template_workbook_path": str(review_template_path),
        "packaged_unit_review_row_count": packaged_unit_review_row_count,
        "allowed_reviewer_decisions": list(REVIEWER_DECISIONS),
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="330K2",
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
        "qa_summary_df": _frame_for_output(pd.DataFrame([{"qa_pass_count": qa_pass_count, "qa_fail_count": qa_fail_count, "decision": summary["decision"]}])),
        "qa_checks_df": qa_df,
        "readme_df": readme_df,
        "review_queue_df": review_queue_df,
        "context_df": context_df,
    }
