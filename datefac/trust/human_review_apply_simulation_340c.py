from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pandas as pd

from datefac.trust.human_review_after_ai_adoption_340b import READY_DECISION as READY_340B_DECISION
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INCREMENTAL_DECISION = "HUMAN_REVIEW_APPLY_SIMULATION_340C_READY_FOR_INCREMENTAL_REVIEW_VALIDATION"
READY_FULL_DECISION = "HUMAN_REVIEW_APPLY_SIMULATION_340C_READY_FOR_FULL_REVIEW_VALIDATION"
NOT_READY_DECISION = "HUMAN_REVIEW_APPLY_SIMULATION_340C_NOT_READY"

DEFAULT_HUMAN_REVIEW_340B_DIR = Path(r"D:\_datefac\output\human_review_after_ai_adoption_340b")
DEFAULT_REVIEWED_STRICTNESS_337D_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
DEFAULT_AI_ADOPTION_338D_DIR = Path(r"D:\_datefac\output\ai_review_adoption_simulation_338d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\human_review_apply_simulation_340c")

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
    "CONFIRM_AS_REVIEWED",
    "CORRECT_AND_CONFIRM",
    "KEEP_NEEDS_REVIEW",
    "REJECT",
    "NEEDS_MORE_CONTEXT",
]

ACTION_BY_DECISION = {
    "CONFIRM_AS_REVIEWED": "WOULD_CONFIRM_REVIEWED",
    "CORRECT_AND_CONFIRM": "WOULD_APPLY_CORRECTION_AND_CONFIRM",
    "KEEP_NEEDS_REVIEW": "WOULD_KEEP_NEEDS_REVIEW",
    "REJECT": "WOULD_REJECT",
    "NEEDS_MORE_CONTEXT": "WOULD_KEEP_NEEDS_MORE_CONTEXT",
}

REVIEW_QUEUE_COLUMNS = [
    "review_id",
    "priority",
    "document",
    "source_sheet",
    "source_row_no",
    "metric_before",
    "year_before",
    "value_before",
    "unit_before",
    "source_page",
    "evidence",
    "model_decision",
    "model_confidence",
    "adoption_action",
    "adoption_reason",
    "deterministic_guard_result",
    "risk_flags",
    "recommended_reviewer_action",
    "reviewer_decision",
    "reviewer_corrected_metric",
    "reviewer_corrected_year",
    "reviewer_corrected_value",
    "reviewer_corrected_unit",
    "reviewer_notes",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    staged: List[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        start = 0
        while True:
            idx = lowered.find(token, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 40) : idx]
            if "not " not in window and "dry-run" not in window and "false" not in window:
                return True
            start = idx + len(token)
    return False


def _metric_requires_amount_unit(metric_name: str) -> bool:
    lowered = metric_name.casefold()
    return "revenue" in lowered or "net_profit" in lowered


def _validation_status_for_row(row_warnings: Sequence[Dict[str, Any]]) -> str:
    severities = {warning["severity"] for warning in row_warnings}
    if "FAIL" in severities:
        return "FAIL"
    if "WARN" in severities:
        return "WARN"
    return "PASS"


def _build_warning(
    *,
    review_id: str,
    source_row_reference: str,
    severity: str,
    warning_code: str,
    detail: str,
) -> Dict[str, Any]:
    return {
        "review_id": review_id,
        "source_row_reference": source_row_reference,
        "severity": severity,
        "warning_code": warning_code,
        "detail": detail,
    }


def _validate_filled_rows(
    review_queue_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[Dict[str, Any]], Dict[str, int]]:
    queue_df = _clean_frame(review_queue_df.copy())
    queue_df["_sheet_row_number"] = [index + 2 for index in range(len(queue_df))]
    queue_df["_source_row_reference"] = queue_df["_sheet_row_number"].map(lambda value: f"01_REVIEW_QUEUE::row_{value}")
    queue_df["_reviewer_decision_norm"] = queue_df["reviewer_decision"].map(_norm_text)

    filled_mask = queue_df["_reviewer_decision_norm"] != ""
    filled_df = queue_df.loc[filled_mask].copy()
    pending_df = queue_df.loc[~filled_mask].copy()

    warnings: List[Dict[str, Any]] = []
    decision_counts = {decision: 0 for decision in ALLOWED_DECISIONS}
    validation_statuses: List[str] = []

    for row in filled_df.to_dict(orient="records"):
        review_id = _norm_text(row.get("review_id"))
        metric_before = _norm_text(row.get("metric_before"))
        decision = _norm_text(row.get("_reviewer_decision_norm"))
        source_row_reference = _norm_text(row.get("_source_row_reference"))
        corrected_metric = _norm_text(row.get("reviewer_corrected_metric"))
        corrected_year = _norm_text(row.get("reviewer_corrected_year"))
        corrected_value = _norm_text(row.get("reviewer_corrected_value"))
        corrected_unit = _norm_text(row.get("reviewer_corrected_unit"))
        reviewer_notes = _norm_text(row.get("reviewer_notes"))
        effective_metric = corrected_metric or metric_before

        row_warnings: List[Dict[str, Any]] = []
        if decision not in ALLOWED_DECISIONS:
            row_warnings.append(
                _build_warning(
                    review_id=review_id,
                    source_row_reference=source_row_reference,
                    severity="FAIL",
                    warning_code="INVALID_DECISION",
                    detail=f"Unsupported reviewer_decision: {decision}",
                )
            )
        else:
            decision_counts[decision] += 1

        if decision == "CORRECT_AND_CONFIRM":
            if not corrected_metric:
                row_warnings.append(
                    _build_warning(
                        review_id=review_id,
                        source_row_reference=source_row_reference,
                        severity="FAIL",
                        warning_code="MISSING_CORRECTED_METRIC",
                        detail="CORRECT_AND_CONFIRM requires reviewer_corrected_metric.",
                    )
                )
            if not corrected_year:
                row_warnings.append(
                    _build_warning(
                        review_id=review_id,
                        source_row_reference=source_row_reference,
                        severity="FAIL",
                        warning_code="MISSING_CORRECTED_YEAR",
                        detail="CORRECT_AND_CONFIRM requires reviewer_corrected_year.",
                    )
                )
            if not corrected_value:
                row_warnings.append(
                    _build_warning(
                        review_id=review_id,
                        source_row_reference=source_row_reference,
                        severity="FAIL",
                        warning_code="MISSING_CORRECTED_VALUE",
                        detail="CORRECT_AND_CONFIRM requires reviewer_corrected_value.",
                    )
                )
            if _metric_requires_amount_unit(effective_metric) and not corrected_unit:
                row_warnings.append(
                    _build_warning(
                        review_id=review_id,
                        source_row_reference=source_row_reference,
                        severity="FAIL",
                        warning_code="MISSING_CORRECTED_UNIT",
                        detail="Amount metric correction requires reviewer_corrected_unit.",
                    )
                )
        elif decision == "REJECT" and not reviewer_notes:
            row_warnings.append(
                _build_warning(
                    review_id=review_id,
                    source_row_reference=source_row_reference,
                    severity="WARN",
                    warning_code="MISSING_REJECT_NOTES",
                    detail="REJECT should usually include reviewer_notes.",
                )
            )
        elif decision == "NEEDS_MORE_CONTEXT" and not reviewer_notes:
            row_warnings.append(
                _build_warning(
                    review_id=review_id,
                    source_row_reference=source_row_reference,
                    severity="WARN",
                    warning_code="MISSING_CONTEXT_NOTES",
                    detail="NEEDS_MORE_CONTEXT should explain missing context when possible.",
                )
            )

        warnings.extend(row_warnings)
        validation_statuses.append(_validation_status_for_row(row_warnings))

    if not filled_df.empty:
        filled_df["validation_status"] = validation_statuses
        filled_df["dry_run_action"] = filled_df["_reviewer_decision_norm"].map(lambda value: ACTION_BY_DECISION.get(value, ""))
        filled_df["action_status"] = "NOT_EXECUTED_DRY_RUN_ONLY"
    else:
        filled_df["validation_status"] = []
        filled_df["dry_run_action"] = []
        filled_df["action_status"] = []

    warnings_df = _clean_frame(pd.DataFrame(warnings))
    pending_df["validation_status"] = "PENDING"
    pending_df["dry_run_action"] = ""
    pending_df["action_status"] = "PENDING_HUMAN_REVIEW"
    return filled_df, pending_df, warnings_df, warnings, decision_counts


def _build_apply_plan_df(filled_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(filled_df.to_dict(orient="records"), start=1):
        rows.append(
            {
                "apply_plan_id": f"340c::{index:03d}",
                "review_id": _norm_text(row.get("review_id")),
                "document": _norm_text(row.get("document")),
                "metric_before": _norm_text(row.get("metric_before")),
                "year_before": _norm_text(row.get("year_before")),
                "value_before": _norm_text(row.get("value_before")),
                "unit_before": _norm_text(row.get("unit_before")),
                "reviewer_decision": _norm_text(row.get("_reviewer_decision_norm")),
                "corrected_metric": _norm_text(row.get("reviewer_corrected_metric")),
                "corrected_year": _norm_text(row.get("reviewer_corrected_year")),
                "corrected_value": _norm_text(row.get("reviewer_corrected_value")),
                "corrected_unit": _norm_text(row.get("reviewer_corrected_unit")),
                "dry_run_action": _norm_text(row.get("dry_run_action")),
                "action_status": _norm_text(row.get("action_status")),
                "validation_status": _norm_text(row.get("validation_status")),
                "reviewer_notes": _norm_text(row.get("reviewer_notes")),
                "source_row_reference": _norm_text(row.get("_source_row_reference")),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "340C validates the currently filled 340B review rows and builds a dry-run apply plan only.",
        },
        {
            "topic": "Write-back boundary",
            "message": "No upstream workbook is modified. This stage does not write back to 337D, 338D, 340B, or any client export.",
        },
        {
            "topic": "Incremental review support",
            "message": "340C supports incremental manual review validation and can be rerun after each batch of filled rows.",
        },
        {
            "topic": "Allowed reviewer_decision",
            "message": "CONFIRM_AS_REVIEWED | CORRECT_AND_CONFIRM | KEEP_NEEDS_REVIEW | REJECT | NEEDS_MORE_CONTEXT",
        },
        {
            "topic": "Action mapping",
            "message": "CONFIRM_AS_REVIEWED -> WOULD_CONFIRM_REVIEWED; CORRECT_AND_CONFIRM -> WOULD_APPLY_CORRECTION_AND_CONFIRM; KEEP_NEEDS_REVIEW -> WOULD_KEEP_NEEDS_REVIEW; REJECT -> WOULD_REJECT; NEEDS_MORE_CONTEXT -> WOULD_KEEP_NEEDS_MORE_CONTEXT",
        },
        {
            "topic": "Legacy smoke note",
            "message": "The original first-5-row expectation was only an initial smoke expectation and is no longer hard-coded in QA.",
        },
        {
            "topic": "Status boundary",
            "message": "This output is not client-ready and not production-ready.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_no_apply_proof_df(no_apply_proof_json: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for path, before_hash in no_apply_proof_json.get("upstream_input_hashes_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_apply_proof_json.get("upstream_input_hashes_after", {}).get(path, ""),
                "unchanged": before_hash == no_apply_proof_json.get("upstream_input_hashes_after", {}).get(path, ""),
            }
        )
    for path, before_hash in no_apply_proof_json.get("official_assets_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_apply_proof_json.get("official_assets_after", {}).get(path, ""),
                "unchanged": before_hash == no_apply_proof_json.get("official_assets_after", {}).get(path, ""),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _decide_stage_status(
    *,
    qa_fail_count: int,
    filled_review_row_count: int,
    pending_review_row_count: int,
    validation_warning_count: int,
) -> str:
    if qa_fail_count != 0 or validation_warning_count != 0:
        return NOT_READY_DECISION
    if filled_review_row_count <= 0:
        return NOT_READY_DECISION
    if pending_review_row_count == 0:
        return READY_FULL_DECISION
    return READY_INCREMENTAL_DECISION


def build_human_review_apply_simulation_340c(
    *,
    human_review_340b_dir: Path,
    reviewed_strictness_337d_dir: Path,
    ai_adoption_338d_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    review_workbook = human_review_340b_dir / "human_review_after_ai_adoption_340b_review_template.xlsx"
    summary_340b_path = human_review_340b_dir / "human_review_after_ai_adoption_340b_summary.json"
    workbook_337d = reviewed_strictness_337d_dir / "real_test_mineru_client_export_337d.xlsx"
    workbook_338d = ai_adoption_338d_dir / "ai_review_adoption_simulation_338d_plan.xlsx"

    files_read = [
        str(summary_340b_path),
        str(review_workbook),
        str(workbook_337d),
        str(workbook_338d),
    ]

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    upstream_hashes_before = {
        str(path): sha256_file(path)
        for path in [review_workbook, workbook_337d, workbook_338d]
    }

    summary_340b = _read_json(summary_340b_path) if summary_340b_path.exists() else {}
    review_queue_df = _read_excel(review_workbook, "01_REVIEW_QUEUE")
    review_queue_df = _clean_frame(review_queue_df)

    filled_df, pending_df, warnings_df, warning_rows, decision_counts = _validate_filled_rows(review_queue_df)
    apply_plan_df = _build_apply_plan_df(filled_df)

    output_dir.mkdir(parents=True, exist_ok=True)

    upstream_hashes_after = {
        str(path): sha256_file(path)
        for path in [review_workbook, workbook_337d, workbook_338d]
    }
    review_workbook_unchanged = upstream_hashes_before.get(str(review_workbook)) == upstream_hashes_after.get(str(review_workbook))
    upstream_workbooks_unchanged = upstream_hashes_before == upstream_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    total_review_queue_count = int(len(review_queue_df))
    filled_review_row_count = int(len(filled_df))
    pending_review_row_count = int(len(pending_df))
    confirm_as_reviewed_count = int(decision_counts.get("CONFIRM_AS_REVIEWED", 0))
    correct_and_confirm_count = int(decision_counts.get("CORRECT_AND_CONFIRM", 0))
    keep_needs_review_count = int(decision_counts.get("KEEP_NEEDS_REVIEW", 0))
    reject_count = int(decision_counts.get("REJECT", 0))
    needs_more_context_count = int(decision_counts.get("NEEDS_MORE_CONTEXT", 0))
    validation_warning_count = int(len(warnings_df))
    validation_fail_count = int(sum(1 for warning in warning_rows if warning["severity"] == "FAIL"))
    decision_count_total = int(sum(decision_counts.values()))

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    no_apply_proof_json = build_no_apply_proof(
        stage="340C",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof_json["upstream_input_hashes_before"] = upstream_hashes_before
    no_apply_proof_json["upstream_input_hashes_after"] = upstream_hashes_after
    no_apply_proof_json["review_workbook_unchanged"] = review_workbook_unchanged
    no_apply_proof_json["upstream_workbooks_unchanged"] = upstream_workbooks_unchanged
    no_apply_proof_json["no_write_back"] = True

    no_apply_proof_passed = (
        bool(no_apply_proof_json.get("no_official_asset_modification_during_340c"))
        and review_workbook_unchanged
        and upstream_workbooks_unchanged
    )

    checks = [
        {"check_name": "inputs::340b_review_workbook_exists", "status": "PASS" if review_workbook.exists() else "FAIL", "detail": str(review_workbook)},
        {"check_name": "inputs::340b_summary_exists", "status": "PASS" if summary_340b_path.exists() else "FAIL", "detail": str(summary_340b_path)},
        {"check_name": "inputs::337d_workbook_exists", "status": "PASS" if workbook_337d.exists() else "FAIL", "detail": str(workbook_337d)},
        {"check_name": "inputs::338d_workbook_exists", "status": "PASS" if workbook_338d.exists() else "FAIL", "detail": str(workbook_338d)},
        {"check_name": "inputs::01_review_queue_sheet_loaded", "status": "PASS" if set(REVIEW_QUEUE_COLUMNS).issubset(set(review_queue_df.columns)) else "FAIL", "detail": json.dumps(list(review_queue_df.columns), ensure_ascii=False)},
        {"check_name": "readiness::340b_decision", "status": "PASS" if _norm_text(summary_340b.get("decision")) == READY_340B_DECISION else "FAIL", "detail": _norm_text(summary_340b.get("decision"))},
        {"check_name": "quality::total_review_queue_count_positive", "status": "PASS" if total_review_queue_count > 0 else "FAIL", "detail": str(total_review_queue_count)},
        {"check_name": "quality::filled_rows_detected", "status": "PASS" if filled_review_row_count > 0 else "FAIL", "detail": str(filled_review_row_count)},
        {"check_name": "quality::filled_row_count_within_total", "status": "PASS" if 0 < filled_review_row_count <= total_review_queue_count else "FAIL", "detail": f"filled={filled_review_row_count} total={total_review_queue_count}"},
        {"check_name": "quality::pending_rows_allowed", "status": "PASS", "detail": f"pending={pending_review_row_count}"},
        {"check_name": "quality::pending_row_count_consistent", "status": "PASS" if pending_review_row_count == total_review_queue_count - filled_review_row_count else "FAIL", "detail": f"pending={pending_review_row_count} expected={total_review_queue_count - filled_review_row_count}"},
        {"check_name": "quality::decision_count_total_consistent", "status": "PASS" if decision_count_total == filled_review_row_count else "FAIL", "detail": f"decision_total={decision_count_total} filled={filled_review_row_count}"},
        {"check_name": "quality::apply_plan_generated", "status": "PASS" if len(apply_plan_df) == filled_review_row_count else "FAIL", "detail": f"apply_plan={len(apply_plan_df)} filled={filled_review_row_count}"},
        {"check_name": "quality::validation_warning_count_zero", "status": "PASS" if validation_warning_count == 0 else "FAIL", "detail": str(validation_warning_count)},
        {"check_name": "quality::validation_fail_count_zero", "status": "PASS" if validation_fail_count == 0 else "FAIL", "detail": str(validation_fail_count)},
        {"check_name": "safety::review_workbook_unchanged", "status": "PASS" if review_workbook_unchanged else "FAIL", "detail": json.dumps({"before": upstream_hashes_before.get(str(review_workbook), ""), "after": upstream_hashes_after.get(str(review_workbook), "")}, ensure_ascii=False)},
        {"check_name": "safety::upstream_workbooks_unchanged", "status": "PASS" if upstream_workbooks_unchanged else "FAIL", "detail": json.dumps(upstream_hashes_after, ensure_ascii=False)},
        {"check_name": "safety::official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "safety::no_apply_proof_passed", "status": "PASS" if no_apply_proof_passed else "FAIL", "detail": json.dumps({"review_workbook_unchanged": review_workbook_unchanged, "upstream_workbooks_unchanged": upstream_workbooks_unchanged, "official_assets_unchanged": bool(no_apply_proof_json.get("no_official_asset_modification_during_340c"))}, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "safety::no_write_back_behavior", "status": "PASS", "detail": "Dry-run only. No write-back path exists in 340C."},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::no_client_ready_claims", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["client-ready", "client ready"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "claims::no_production_ready_claims", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["production-ready", "production ready"]) else "FAIL", "detail": "README text checked"},
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    decision = _decide_stage_status(
        qa_fail_count=qa_fail_count,
        filled_review_row_count=filled_review_row_count,
        pending_review_row_count=pending_review_row_count,
        validation_warning_count=validation_warning_count,
    )

    apply_plan_workbook_path = output_dir / "human_review_apply_simulation_340c_apply_plan.xlsx"
    summary = {
        "generated_at_utc": _utc_now(),
        "input_review_workbook_path": str(review_workbook),
        "apply_plan_workbook_path": str(apply_plan_workbook_path),
        "total_review_queue_count": total_review_queue_count,
        "filled_review_row_count": filled_review_row_count,
        "pending_review_row_count": pending_review_row_count,
        "confirm_as_reviewed_count": confirm_as_reviewed_count,
        "correct_and_confirm_count": correct_and_confirm_count,
        "keep_needs_review_count": keep_needs_review_count,
        "reject_count": reject_count,
        "needs_more_context_count": needs_more_context_count,
        "validation_warning_count": validation_warning_count,
        "validation_fail_count": validation_fail_count,
        "incremental_review_supported": True,
        "review_workbook_unchanged": review_workbook_unchanged,
        "upstream_workbooks_unchanged": upstream_workbooks_unchanged,
        "no_apply_proof_passed": no_apply_proof_passed,
        "no_write_back": True,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "340C_human_review_apply_simulation_after_ai_adoption",
        "human_review_340b_dir": str(human_review_340b_dir),
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "ai_adoption_338d_dir": str(ai_adoption_338d_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "human_review_apply_simulation_340c_summary.json"),
            "manifest_json": str(output_dir / "human_review_apply_simulation_340c_manifest.json"),
            "qa_json": str(output_dir / "human_review_apply_simulation_340c_qa.json"),
            "no_apply_proof_json": str(output_dir / "human_review_apply_simulation_340c_no_apply_proof.json"),
            "apply_plan_xlsx": str(apply_plan_workbook_path),
            "report_md": str(output_dir / "human_review_apply_simulation_340c_report.md"),
        },
        "allowed_reviewer_decisions": list(ALLOWED_DECISIONS),
        "dry_run_action_mapping": dict(ACTION_BY_DECISION),
        "supports_incremental_manual_review_validation": True,
        "files_read": files_read,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "validation_warning_count": validation_warning_count,
        "checks": checks,
        "validation_warnings": warning_rows,
        "upstream_input_hashes_before": upstream_hashes_before,
        "upstream_input_hashes_after": upstream_hashes_after,
    }

    workbook_sheets = {
        "00_README": readme_df,
        "01_APPLY_PLAN": apply_plan_df,
        "02_FILLED_REVIEW_ROWS": _clean_frame(
            filled_df[
                REVIEW_QUEUE_COLUMNS + ["_source_row_reference", "validation_status", "dry_run_action", "action_status"]
            ].rename(columns={"_source_row_reference": "source_row_reference"})
        ),
        "03_PENDING_REVIEW_ROWS": _clean_frame(
            pending_df[
                REVIEW_QUEUE_COLUMNS + ["_source_row_reference", "validation_status", "action_status"]
            ].rename(columns={"_source_row_reference": "source_row_reference"})
        ),
        "04_VALIDATION_WARNINGS": warnings_df,
        "05_NO_APPLY_PROOF": _build_no_apply_proof_df(no_apply_proof_json),
        "06_SUMMARY": _clean_frame(pd.DataFrame([summary])),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }
