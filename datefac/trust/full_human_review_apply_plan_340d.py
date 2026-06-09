from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.human_review_apply_simulation_340c import READY_FULL_DECISION as READY_340C_FULL_DECISION
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "FULL_HUMAN_REVIEW_APPLY_PLAN_340D_READY"
NOT_READY_DECISION = "FULL_HUMAN_REVIEW_APPLY_PLAN_340D_NOT_READY"

DEFAULT_HUMAN_REVIEW_340B_DIR = Path(r"D:\_datefac\output\human_review_after_ai_adoption_340b")
DEFAULT_HUMAN_REVIEW_APPLY_340C_DIR = Path(r"D:\_datefac\output\human_review_apply_simulation_340c")
DEFAULT_REVIEWED_STRICTNESS_337D_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
DEFAULT_AI_ADOPTION_338D_DIR = Path(r"D:\_datefac\output\ai_review_adoption_simulation_338d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\full_human_review_apply_plan_340d")

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

FINAL_ACTION_BY_DECISION = {
    "CONFIRM_AS_REVIEWED": "FINAL_WOULD_CONFIRM_REVIEWED",
    "CORRECT_AND_CONFIRM": "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM",
    "KEEP_NEEDS_REVIEW": "FINAL_WOULD_KEEP_NEEDS_REVIEW",
    "REJECT": "FINAL_WOULD_REJECT",
    "NEEDS_MORE_CONTEXT": "FINAL_WOULD_KEEP_NEEDS_MORE_CONTEXT",
}

FINAL_ROUTE_BY_ACTION = {
    "FINAL_WOULD_CONFIRM_REVIEWED": "reviewed_after_human",
    "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM": "reviewed_after_human_corrected",
    "FINAL_WOULD_REJECT": "rejected_after_human",
    "FINAL_WOULD_KEEP_NEEDS_REVIEW": "needs_review_after_human",
    "FINAL_WOULD_KEEP_NEEDS_MORE_CONTEXT": "needs_more_context_after_human",
}

FINAL_PLAN_COLUMNS = [
    "final_apply_id",
    "review_id",
    "document",
    "source_sheet",
    "source_row_no",
    "metric_before",
    "year_before",
    "value_before",
    "unit_before",
    "reviewer_decision",
    "corrected_metric",
    "corrected_year",
    "corrected_value",
    "corrected_unit",
    "final_dry_run_action",
    "final_route_after_apply",
    "source_page",
    "evidence",
    "reviewer_notes",
    "risk_flags",
    "adoption_action_338d",
    "dry_run_action_340c",
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


def _requires_amount_unit(metric_name: str) -> bool:
    lowered = metric_name.casefold()
    return "revenue" in lowered or "net_profit" in lowered


def _effective_metric(row: Mapping[str, Any]) -> str:
    return _norm_text(row.get("reviewer_corrected_metric")) or _norm_text(row.get("metric_before"))


def _merge_row(
    review_row: Mapping[str, Any],
    apply_row: Mapping[str, Any],
) -> Dict[str, Any]:
    reviewer_decision = _norm_text(review_row.get("reviewer_decision"))
    final_action = FINAL_ACTION_BY_DECISION.get(reviewer_decision, "")
    return {
        "review_id": _norm_text(review_row.get("review_id")),
        "document": _norm_text(review_row.get("document")),
        "source_sheet": _norm_text(review_row.get("source_sheet")),
        "source_row_no": _norm_text(review_row.get("source_row_no")),
        "metric_before": _norm_text(review_row.get("metric_before")),
        "year_before": _norm_text(review_row.get("year_before")),
        "value_before": _norm_text(review_row.get("value_before")),
        "unit_before": _norm_text(review_row.get("unit_before")),
        "reviewer_decision": reviewer_decision,
        "corrected_metric": _norm_text(review_row.get("reviewer_corrected_metric")),
        "corrected_year": _norm_text(review_row.get("reviewer_corrected_year")),
        "corrected_value": _norm_text(review_row.get("reviewer_corrected_value")),
        "corrected_unit": _norm_text(review_row.get("reviewer_corrected_unit")),
        "final_dry_run_action": final_action,
        "final_route_after_apply": FINAL_ROUTE_BY_ACTION.get(final_action, ""),
        "source_page": _norm_text(review_row.get("source_page")),
        "evidence": _norm_text(review_row.get("evidence")),
        "reviewer_notes": _norm_text(review_row.get("reviewer_notes")),
        "risk_flags": _norm_text(review_row.get("risk_flags")),
        "adoption_action_338d": _norm_text(review_row.get("adoption_action")),
        "dry_run_action_340c": _norm_text(apply_row.get("dry_run_action")),
    }


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "340D creates a final sidecar full human review dry-run apply plan from the fully validated 340C stage.",
        },
        {
            "topic": "Write-back boundary",
            "message": "No upstream workbook or official asset is modified. This stage does not write back to 337D, 338D, 340B, or 340C.",
        },
        {
            "topic": "Scope",
            "message": "340D is a final dry-run planning artifact only. It does not create a client export and it does not change production behavior.",
        },
        {
            "topic": "Decision basis",
            "message": "340D requires 340C full-validation ready status before generating the final dry-run plan.",
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


def build_full_human_review_apply_plan_340d(
    *,
    human_review_340b_dir: Path,
    human_review_apply_340c_dir: Path,
    reviewed_strictness_337d_dir: Path,
    ai_adoption_338d_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    workbook_340b = human_review_340b_dir / "human_review_after_ai_adoption_340b_review_template.xlsx"
    summary_340b_path = human_review_340b_dir / "human_review_after_ai_adoption_340b_summary.json"
    workbook_340c = human_review_apply_340c_dir / "human_review_apply_simulation_340c_apply_plan.xlsx"
    summary_340c_path = human_review_apply_340c_dir / "human_review_apply_simulation_340c_summary.json"
    workbook_337d = reviewed_strictness_337d_dir / "real_test_mineru_client_export_337d.xlsx"
    workbook_338d = ai_adoption_338d_dir / "ai_review_adoption_simulation_338d_plan.xlsx"

    files_read = [
        str(summary_340b_path),
        str(summary_340c_path),
        str(workbook_340b),
        str(workbook_340c),
        str(workbook_337d),
        str(workbook_338d),
    ]

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    upstream_hashes_before = {
        str(path): sha256_file(path)
        for path in [workbook_340b, workbook_340c, workbook_337d, workbook_338d]
    }

    summary_340b = _read_json(summary_340b_path) if summary_340b_path.exists() else {}
    summary_340c = _read_json(summary_340c_path) if summary_340c_path.exists() else {}

    review_queue_df = _read_excel(workbook_340b, "01_REVIEW_QUEUE")
    apply_plan_340c_df = _read_excel(workbook_340c, "01_APPLY_PLAN")
    adoption_plan_338d_df = _read_excel(workbook_338d, "02_ADOPTION_PLAN")

    apply_lookup = {
        _norm_text(row.get("review_id")): row
        for row in apply_plan_340c_df.to_dict(orient="records")
    }

    final_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    for row in review_queue_df.to_dict(orient="records"):
        review_id = _norm_text(row.get("review_id"))
        apply_row = apply_lookup.get(review_id, {})
        final_row = _merge_row(row, apply_row)
        final_rows.append(final_row)

        reviewer_decision = _norm_text(row.get("reviewer_decision"))
        corrected_unit = _norm_text(row.get("reviewer_corrected_unit"))
        corrected_metric = _effective_metric(row)
        corrected_value = _norm_text(row.get("reviewer_corrected_value"))
        corrected_year = _norm_text(row.get("reviewer_corrected_year"))
        corrected_metric_value = _norm_text(row.get("reviewer_corrected_metric"))
        risk_flags = _norm_text(row.get("risk_flags"))
        risk_tokens = risk_flags.casefold()
        audit_rows.append(
            {
                "review_id": review_id,
                "document": _norm_text(row.get("document")),
                "metric_before": _norm_text(row.get("metric_before")),
                "reviewer_decision": reviewer_decision,
                "corrected_metric": corrected_metric_value,
                "corrected_unit": corrected_unit,
                "risk_flags": risk_flags,
                "duplicate_risk_flag": "duplicate" in risk_tokens,
                "missing_unit_risk_flag": "missing_unit" in risk_tokens or "missing unit" in risk_tokens,
                "percent_value_risk_flag": "percent_value" in risk_tokens or "percent value" in risk_tokens,
            }
        )
        if reviewer_decision == "CORRECT_AND_CONFIRM":
            if not corrected_metric_value:
                warnings.append({"review_id": review_id, "warning_code": "MISSING_CORRECTED_METRIC", "detail": "Corrected metric is required."})
            if not corrected_year:
                warnings.append({"review_id": review_id, "warning_code": "MISSING_CORRECTED_YEAR", "detail": "Corrected year is required."})
            if not corrected_value:
                warnings.append({"review_id": review_id, "warning_code": "MISSING_CORRECTED_VALUE", "detail": "Corrected value is required."})
            if _requires_amount_unit(corrected_metric) and not corrected_unit:
                warnings.append({"review_id": review_id, "warning_code": "MISSING_CORRECTED_UNIT", "detail": "Money metric correction requires corrected unit."})
            if corrected_metric.casefold() == "eps" and not corrected_unit:
                warnings.append({"review_id": review_id, "warning_code": "EPS_UNIT_REQUIRED", "detail": "EPS correction requires non-empty corrected unit."})

    final_plan_df = _clean_frame(pd.DataFrame(final_rows))
    final_plan_df.insert(0, "final_apply_id", [f"340d::{index:03d}" for index in range(1, len(final_plan_df) + 1)])
    final_plan_df = _clean_frame(final_plan_df[FINAL_PLAN_COLUMNS])
    audit_df = _clean_frame(pd.DataFrame(audit_rows))
    warnings_df = _clean_frame(pd.DataFrame(warnings))

    final_confirm_count = int((final_plan_df["reviewer_decision"] == "CONFIRM_AS_REVIEWED").sum()) if not final_plan_df.empty else 0
    final_correct_and_confirm_count = int((final_plan_df["reviewer_decision"] == "CORRECT_AND_CONFIRM").sum()) if not final_plan_df.empty else 0
    final_reject_count = int((final_plan_df["reviewer_decision"] == "REJECT").sum()) if not final_plan_df.empty else 0
    final_keep_needs_review_count = int((final_plan_df["reviewer_decision"] == "KEEP_NEEDS_REVIEW").sum()) if not final_plan_df.empty else 0
    final_needs_more_context_count = int((final_plan_df["reviewer_decision"] == "NEEDS_MORE_CONTEXT").sum()) if not final_plan_df.empty else 0
    total_review_queue_count = int(len(final_plan_df))
    final_reviewed_after_human_candidate_count = final_confirm_count + final_correct_and_confirm_count
    final_non_reviewed_after_human_count = total_review_queue_count - final_reviewed_after_human_candidate_count

    output_dir.mkdir(parents=True, exist_ok=True)

    upstream_hashes_after = {
        str(path): sha256_file(path)
        for path in [workbook_340b, workbook_340c, workbook_337d, workbook_338d]
    }
    upstream_workbooks_unchanged = upstream_hashes_before == upstream_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_apply_proof_json = build_no_apply_proof(
        stage="340D",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof_json["upstream_input_hashes_before"] = upstream_hashes_before
    no_apply_proof_json["upstream_input_hashes_after"] = upstream_hashes_after
    no_apply_proof_json["upstream_workbooks_unchanged"] = upstream_workbooks_unchanged
    no_apply_proof_json["no_write_back"] = True

    no_apply_proof_passed = (
        bool(no_apply_proof_json.get("no_official_asset_modification_during_340d"))
        and upstream_workbooks_unchanged
    )

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    checks = [
        {"check_name": "inputs::340b_review_workbook_exists", "status": "PASS" if workbook_340b.exists() else "FAIL", "detail": str(workbook_340b)},
        {"check_name": "inputs::340c_apply_plan_exists", "status": "PASS" if workbook_340c.exists() else "FAIL", "detail": str(workbook_340c)},
        {"check_name": "inputs::337d_workbook_exists", "status": "PASS" if workbook_337d.exists() else "FAIL", "detail": str(workbook_337d)},
        {"check_name": "inputs::338d_workbook_exists", "status": "PASS" if workbook_338d.exists() else "FAIL", "detail": str(workbook_338d)},
        {
            "check_name": "readiness::340c_full_validation_ready",
            "status": "PASS"
            if (
                summary_340c.get("filled_review_row_count") == summary_340c.get("total_review_queue_count")
                and summary_340c.get("pending_review_row_count") == 0
                and summary_340c.get("validation_warning_count") == 0
                and summary_340c.get("qa_fail_count") == 0
                and summary_340c.get("decision") == READY_340C_FULL_DECISION
            )
            else "FAIL",
            "detail": json.dumps(summary_340c, ensure_ascii=False),
        },
        {"check_name": "quality::all_review_rows_represented", "status": "PASS" if total_review_queue_count == 77 else "FAIL", "detail": str(total_review_queue_count)},
        {"check_name": "quality::no_pending_review_rows", "status": "PASS" if int(summary_340c.get("pending_review_row_count", -1)) == 0 else "FAIL", "detail": str(summary_340c.get("pending_review_row_count", ""))},
        {
            "check_name": "quality::decision_counts_total_77",
            "status": "PASS"
            if final_confirm_count + final_correct_and_confirm_count + final_reject_count + final_keep_needs_review_count + final_needs_more_context_count == 77
            else "FAIL",
            "detail": str(final_confirm_count + final_correct_and_confirm_count + final_reject_count + final_keep_needs_review_count + final_needs_more_context_count),
        },
        {"check_name": "quality::validation_warning_count_zero", "status": "PASS" if len(warnings_df) == 0 else "FAIL", "detail": str(len(warnings_df))},
        {"check_name": "quality::final_reviewed_after_human_candidate_count", "status": "PASS" if final_reviewed_after_human_candidate_count == 34 else "FAIL", "detail": str(final_reviewed_after_human_candidate_count)},
        {"check_name": "quality::final_non_reviewed_after_human_count", "status": "PASS" if final_non_reviewed_after_human_count == 43 else "FAIL", "detail": str(final_non_reviewed_after_human_count)},
        {"check_name": "quality::340c_plan_row_count", "status": "PASS" if len(apply_plan_340c_df) == 77 else "FAIL", "detail": str(len(apply_plan_340c_df))},
        {"check_name": "safety::upstream_workbooks_unchanged", "status": "PASS" if upstream_workbooks_unchanged else "FAIL", "detail": json.dumps(upstream_hashes_after, ensure_ascii=False)},
        {"check_name": "safety::official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "safety::no_apply_proof_passed", "status": "PASS" if no_apply_proof_passed else "FAIL", "detail": json.dumps({"upstream_workbooks_unchanged": upstream_workbooks_unchanged, "official_assets_unchanged": bool(no_apply_proof_json.get("no_official_asset_modification_during_340d"))}, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::no_client_ready_claims", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["client-ready", "client ready"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "claims::no_production_ready_claims", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["production-ready", "production ready"]) else "FAIL", "detail": "README text checked"},
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "total_review_queue_count": total_review_queue_count,
        "final_confirm_count": final_confirm_count,
        "final_correct_and_confirm_count": final_correct_and_confirm_count,
        "final_reject_count": final_reject_count,
        "final_keep_needs_review_count": final_keep_needs_review_count,
        "final_needs_more_context_count": final_needs_more_context_count,
        "final_reviewed_after_human_candidate_count": final_reviewed_after_human_candidate_count,
        "final_non_reviewed_after_human_count": final_non_reviewed_after_human_count,
        "upstream_workbooks_unchanged": upstream_workbooks_unchanged,
        "no_apply_proof_passed": no_apply_proof_passed,
        "no_write_back": True,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "final_apply_plan_workbook_path": str(output_dir / "full_human_review_apply_plan_340d.xlsx"),
    }

    manifest = {
        "task": "340D_full_human_review_apply_plan",
        "human_review_340b_dir": str(human_review_340b_dir),
        "human_review_apply_340c_dir": str(human_review_apply_340c_dir),
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "ai_adoption_338d_dir": str(ai_adoption_338d_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "full_human_review_apply_plan_340d_summary.json"),
            "manifest_json": str(output_dir / "full_human_review_apply_plan_340d_manifest.json"),
            "qa_json": str(output_dir / "full_human_review_apply_plan_340d_qa.json"),
            "no_apply_proof_json": str(output_dir / "full_human_review_apply_plan_340d_no_apply_proof.json"),
            "report_md": str(output_dir / "full_human_review_apply_plan_340d_report.md"),
            "workbook_xlsx": str(output_dir / "full_human_review_apply_plan_340d.xlsx"),
        },
        "final_action_mapping": dict(FINAL_ACTION_BY_DECISION),
        "final_route_mapping": dict(FINAL_ROUTE_BY_ACTION),
        "files_read": files_read,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "checks": checks,
        "validation_warnings": warnings_df.to_dict(orient="records"),
        "upstream_input_hashes_before": upstream_hashes_before,
        "upstream_input_hashes_after": upstream_hashes_after,
    }

    next_step_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "next_step": "WAIT_FOR_EXPLICIT_APPLY_STAGE",
                    "recommendation": "340D is ready as a final dry-run plan. Wait for an explicit next task before any write-back or client export refresh.",
                }
            ]
        )
    )

    workbook_sheets = {
        "00_README": _build_readme_df(),
        "01_FINAL_APPLY_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_FINAL_APPLY_PLAN": final_plan_df,
        "03_WOULD_CONFIRM_REVIEWED": _clean_frame(final_plan_df[final_plan_df["final_dry_run_action"] == "FINAL_WOULD_CONFIRM_REVIEWED"]),
        "04_WOULD_CORRECT_AND_CONFIRM": _clean_frame(final_plan_df[final_plan_df["final_dry_run_action"] == "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM"]),
        "05_WOULD_REJECT": _clean_frame(final_plan_df[final_plan_df["final_dry_run_action"] == "FINAL_WOULD_REJECT"]),
        "06_WOULD_KEEP_NEEDS_REVIEW": _clean_frame(
            final_plan_df[
                final_plan_df["final_dry_run_action"].isin(
                    ["FINAL_WOULD_KEEP_NEEDS_REVIEW", "FINAL_WOULD_KEEP_NEEDS_MORE_CONTEXT"]
                )
            ]
        ),
        "07_DUPLICATE_AND_UNIT_RISK_AUDIT": audit_df,
        "08_NO_APPLY_PROOF": _build_no_apply_proof_df(no_apply_proof_json),
        "09_NEXT_STEP_RECOMMENDATION": next_step_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }
