from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.full_human_review_apply_plan_340d import READY_DECISION as READY_340D_DECISION
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "POST_HUMAN_REVIEW_SIDECAR_RESULT_340E_READY"
NOT_READY_DECISION = "POST_HUMAN_REVIEW_SIDECAR_RESULT_340E_NOT_READY"

DEFAULT_FULL_HUMAN_REVIEW_APPLY_340D_DIR = Path(r"D:\_datefac\output\full_human_review_apply_plan_340d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\post_human_review_sidecar_result_340e")

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
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


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "340E converts the final 340D dry-run plan into a post-human-review sidecar result package.",
        },
        {
            "topic": "Write-back boundary",
            "message": "No upstream workbook or official asset is modified. This stage does not write back to 337D, 338D, 340B, 340C, or 340D.",
        },
        {
            "topic": "Scope",
            "message": "340E creates a sidecar result only. It does not create a client export and it does not change production behavior.",
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


def build_post_human_review_sidecar_result_340e(
    *,
    full_human_review_apply_340d_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    workbook_340d = full_human_review_apply_340d_dir / "full_human_review_apply_plan_340d.xlsx"
    summary_340d_path = full_human_review_apply_340d_dir / "full_human_review_apply_plan_340d_summary.json"

    files_read = [str(summary_340d_path), str(workbook_340d)]
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    input_hashes_before = {str(path): sha256_file(path) for path in [workbook_340d]}

    summary_340d = _read_json(summary_340d_path) if summary_340d_path.exists() else {}
    final_plan_df = _read_excel(workbook_340d, "02_FINAL_APPLY_PLAN")
    risk_audit_df = _read_excel(workbook_340d, "07_DUPLICATE_AND_UNIT_RISK_AUDIT")

    reviewed_df = _clean_frame(
        final_plan_df[final_plan_df["final_dry_run_action"] == "FINAL_WOULD_CONFIRM_REVIEWED"].copy()
    )
    corrected_df = _clean_frame(
        final_plan_df[final_plan_df["final_dry_run_action"] == "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM"].copy()
    )
    needs_review_df = _clean_frame(
        final_plan_df[final_plan_df["final_dry_run_action"] == "FINAL_WOULD_KEEP_NEEDS_REVIEW"].copy()
    )
    rejected_df = _clean_frame(
        final_plan_df[final_plan_df["final_dry_run_action"] == "FINAL_WOULD_REJECT"].copy()
    )

    corrected_output_df = corrected_df.copy()
    for source_col, corrected_col in [
        ("metric_before", "corrected_metric"),
        ("year_before", "corrected_year"),
        ("value_before", "corrected_value"),
        ("unit_before", "corrected_unit"),
    ]:
        corrected_output_df[f"final_{source_col.replace('_before', '')}"] = corrected_output_df[corrected_col]

    reviewed_output_df = reviewed_df.copy()
    for source_col in ["metric_before", "year_before", "value_before", "unit_before"]:
        reviewed_output_df[f"final_{source_col.replace('_before', '')}"] = reviewed_output_df[source_col]

    correction_log_df = _clean_frame(
        corrected_df[
            [
                "final_apply_id",
                "review_id",
                "document",
                "metric_before",
                "year_before",
                "value_before",
                "unit_before",
                "corrected_metric",
                "corrected_year",
                "corrected_value",
                "corrected_unit",
                "reviewer_notes",
                "risk_flags",
            ]
        ].copy()
    )

    source_trace_df = _clean_frame(
        final_plan_df[
            [
                "final_apply_id",
                "review_id",
                "document",
                "source_sheet",
                "source_row_no",
                "source_page",
                "evidence",
                "metric_before",
                "year_before",
                "value_before",
                "unit_before",
                "final_dry_run_action",
                "final_route_after_apply",
            ]
        ].copy()
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    input_hashes_after = {str(path): sha256_file(path) for path in [workbook_340d]}
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_apply_proof_json = build_no_apply_proof(
        stage="340E",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof_json["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof_json["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_apply_proof_json["no_write_back"] = True

    no_write_back_proof_passed = (
        bool(no_apply_proof_json.get("no_official_asset_modification_during_340e"))
        and upstream_unchanged
    )

    total_input_rows = int(len(final_plan_df))
    reviewed_after_human_count = int(len(reviewed_df))
    reviewed_after_human_corrected_count = int(len(corrected_df))
    reviewed_after_human_total_count = reviewed_after_human_count + reviewed_after_human_corrected_count
    rejected_after_human_count = int(len(rejected_df))
    needs_review_after_human_count = int(len(needs_review_df))

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    checks = [
        {"check_name": "inputs::340d_workbook_exists", "status": "PASS" if workbook_340d.exists() else "FAIL", "detail": str(workbook_340d)},
        {
            "check_name": "readiness::340d_ready",
            "status": "PASS" if summary_340d.get("decision") == READY_340D_DECISION and summary_340d.get("qa_fail_count") == 0 else "FAIL",
            "detail": json.dumps(summary_340d, ensure_ascii=False),
        },
        {"check_name": "quality::all_input_rows_represented", "status": "PASS" if total_input_rows == 77 else "FAIL", "detail": str(total_input_rows)},
        {"check_name": "quality::reviewed_after_human_count", "status": "PASS" if reviewed_after_human_count == 22 else "FAIL", "detail": str(reviewed_after_human_count)},
        {"check_name": "quality::reviewed_after_human_corrected_count", "status": "PASS" if reviewed_after_human_corrected_count == 12 else "FAIL", "detail": str(reviewed_after_human_corrected_count)},
        {"check_name": "quality::reviewed_after_human_total_count", "status": "PASS" if reviewed_after_human_total_count == 34 else "FAIL", "detail": str(reviewed_after_human_total_count)},
        {"check_name": "quality::rejected_after_human_count", "status": "PASS" if rejected_after_human_count == 31 else "FAIL", "detail": str(rejected_after_human_count)},
        {"check_name": "quality::needs_review_after_human_count", "status": "PASS" if needs_review_after_human_count == 12 else "FAIL", "detail": str(needs_review_after_human_count)},
        {
            "check_name": "quality::category_counts_sum_total",
            "status": "PASS" if reviewed_after_human_total_count + rejected_after_human_count + needs_review_after_human_count == total_input_rows else "FAIL",
            "detail": str(reviewed_after_human_total_count + rejected_after_human_count + needs_review_after_human_count),
        },
        {"check_name": "safety::upstream_workbook_unchanged", "status": "PASS" if upstream_unchanged else "FAIL", "detail": json.dumps(input_hashes_after, ensure_ascii=False)},
        {"check_name": "safety::official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "safety::no_write_back_proof_passed", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"upstream_unchanged": upstream_unchanged, "official_assets_unchanged": bool(no_apply_proof_json.get("no_official_asset_modification_during_340e"))}, ensure_ascii=False)},
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
        "total_input_rows": total_input_rows,
        "reviewed_after_human_count": reviewed_after_human_count,
        "reviewed_after_human_corrected_count": reviewed_after_human_corrected_count,
        "reviewed_after_human_total_count": reviewed_after_human_total_count,
        "rejected_after_human_count": rejected_after_human_count,
        "needs_review_after_human_count": needs_review_after_human_count,
        "no_write_back": True,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "output_workbook_path": str(output_dir / "post_human_review_sidecar_result_340e.xlsx"),
    }

    manifest = {
        "task": "340E_post_human_review_sidecar_result",
        "full_human_review_apply_340d_dir": str(full_human_review_apply_340d_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "post_human_review_sidecar_result_340e_summary.json"),
            "manifest_json": str(output_dir / "post_human_review_sidecar_result_340e_manifest.json"),
            "qa_json": str(output_dir / "post_human_review_sidecar_result_340e_qa.json"),
            "no_write_back_proof_json": str(output_dir / "post_human_review_sidecar_result_340e_no_write_back_proof.json"),
            "report_md": str(output_dir / "post_human_review_sidecar_result_340e_report.md"),
            "workbook_xlsx": str(output_dir / "post_human_review_sidecar_result_340e.xlsx"),
        },
        "files_read": files_read,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "checks": checks,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    next_step_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "next_step": "WAIT_FOR_EXPLICIT_EXPORT_OR_APPLY_STAGE",
                    "recommendation": "340E is ready as a sidecar post-human-review result. Wait for an explicit next task before any export refresh or write-back stage.",
                }
            ]
        )
    )

    workbook_sheets = {
        "00_README": _build_readme_df(),
        "01_REVIEWED_AFTER_HUMAN": reviewed_output_df,
        "02_REVIEWED_HUMAN_CORRECTED": corrected_output_df,
        "03_NEEDS_REVIEW_AFTER_HUMAN": needs_review_df,
        "04_REJECTED_AFTER_HUMAN": rejected_df,
        "05_CORRECTION_LOG": correction_log_df,
        "06_SOURCE_TRACE": source_trace_df,
        "07_RISK_AUDIT": risk_audit_df,
        "08_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "09_NO_WRITE_BACK_PROOF": _build_no_apply_proof_df(no_apply_proof_json),
        "10_NEXT_STEP_RECOMMENDATION": next_step_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }
