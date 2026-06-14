from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345C4 = "ALIAS_SUGGESTION_HUMAN_REVIEW_PACKAGE_345C4_READY"
READY_DECISION_345C5 = "REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY"
INPUT_STAGE_345C5 = "POST_345C4_REVIEWED_ALIAS_DECISION_INGESTION"

DEFAULT_345C4_DIR = Path(r"D:\_datefac\output\alias_suggestion_human_review_package_345c4")
DEFAULT_REVIEWED_WORKBOOK = DEFAULT_345C4_DIR / "alias_suggestion_human_review_package_345c4_reviewed.xlsx"
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\reviewed_alias_decision_ingestion_345c5")

MANIFEST_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_manifest.json"
REVIEWED_DECISIONS_JSON_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_reviewed_decisions.json"
REVIEWED_DECISIONS_CSV_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_reviewed_decisions.csv"
VALIDATED_APPROVED_JSON_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json"
VALIDATED_APPROVED_CSV_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.csv"
REJECTED_OR_DEFERRED_JSON_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json"
REJECTED_OR_DEFERRED_CSV_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.csv"
VALIDATION_ISSUES_JSON_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_validation_issues.json"
DECISION_SUMMARY_JSON_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_decision_summary.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "reviewed_alias_decision_ingestion_345c5_next_plan.md"

INPUT_MANIFEST_NAME = "alias_suggestion_human_review_package_345c4_manifest.json"
INPUT_REVIEW_ROWS_JSON_NAME = "alias_suggestion_human_review_package_345c4_review_rows.json"
INPUT_WORKBOOK_NAME = "alias_suggestion_human_review_package_345c4.xlsx"

REVIEWED_SHEET_NAME = "02_REVIEW_ROWS"

ALLOWED_DECISIONS = {
    "APPROVE_EXISTING_MAPPING",
    "APPROVE_NEW_STANDARD",
    "REJECT_ALIAS",
    "NEEDS_MORE_CONTEXT",
    "DEFER",
}

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

OUTPUT_ROW_FIELDS = [
    "alias_review_row_id",
    "alias_adjudication_id",
    "raw_metric_name",
    "frequency",
    "alias_candidate_priority",
    "llm_suggested_action",
    "llm_suggested_standard_metric",
    "llm_suggested_new_standard_metric",
    "llm_confidence",
    "human_alias_review_decision",
    "approved_standard_metric",
    "approved_new_standard_metric",
    "alias_reviewer",
    "alias_reviewed_at",
    "alias_review_notes",
    "decision_validation_status",
    "decision_validation_issues",
    "apply_simulation_eligible",
    "canonical_alias_target",
    "alias_rule_update_allowed",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return " ".join(str(value).strip().split())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_rows(path: Path) -> List[Dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON payload in {path}")
    return [dict(row) for row in payload]


def _require_existing(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = _run_git(repo_root, ["status", "--porcelain", "--", *paths])
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _load_reviewed_rows(workbook_path: Path) -> List[Dict[str, Any]]:
    frame = pd.read_excel(workbook_path, sheet_name=REVIEWED_SHEET_NAME)
    if frame.empty:
        return []
    return frame.astype(object).where(pd.notna(frame), "").to_dict(orient="records")


def _validation_for_row(row: Dict[str, Any]) -> tuple[str, List[str], bool, str]:
    issues: List[str] = []
    decision = _safe_text(row.get("human_alias_review_decision"))
    approved_standard_metric = _safe_text(row.get("approved_standard_metric"))
    approved_new_standard_metric = _safe_text(row.get("approved_new_standard_metric"))
    review_notes = _safe_text(row.get("alias_review_notes"))

    if not decision:
        issues.append("missing_human_alias_review_decision")
    elif decision not in ALLOWED_DECISIONS:
        issues.append("invalid_human_alias_review_decision")
    elif decision == "APPROVE_EXISTING_MAPPING":
        if not approved_standard_metric:
            issues.append("missing_approved_standard_metric")
        if approved_new_standard_metric:
            issues.append("unexpected_approved_new_standard_metric")
    elif decision == "APPROVE_NEW_STANDARD":
        if not approved_new_standard_metric:
            issues.append("missing_approved_new_standard_metric")
        if not review_notes:
            issues.append("missing_review_notes_for_new_standard")
        if approved_standard_metric:
            issues.append("unexpected_approved_standard_metric")
    elif decision == "REJECT_ALIAS":
        if not review_notes:
            issues.append("missing_review_notes_for_reject")
    elif decision == "NEEDS_MORE_CONTEXT":
        if not review_notes:
            issues.append("missing_review_notes_for_needs_more_context")

    validation_status = "VALID" if not issues else "INVALID"
    apply_simulation_eligible = (
        validation_status == "VALID"
        and decision in {"APPROVE_EXISTING_MAPPING", "APPROVE_NEW_STANDARD"}
    )
    canonical_alias_target = ""
    if apply_simulation_eligible:
        if decision == "APPROVE_EXISTING_MAPPING":
            canonical_alias_target = approved_standard_metric
        elif decision == "APPROVE_NEW_STANDARD":
            canonical_alias_target = approved_new_standard_metric
    return validation_status, issues, apply_simulation_eligible, canonical_alias_target


def _artifact_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "Manifest and gate summary.",
        },
        {
            "artifact_name": REVIEWED_DECISIONS_JSON_FILE_NAME,
            "path": str(output_dir / REVIEWED_DECISIONS_JSON_FILE_NAME),
            "purpose": "Merged reviewed decisions with validation status.",
        },
        {
            "artifact_name": VALIDATED_APPROVED_JSON_FILE_NAME,
            "path": str(output_dir / VALIDATED_APPROVED_JSON_FILE_NAME),
            "purpose": "Apply-simulation-eligible approved alias decisions.",
        },
        {
            "artifact_name": REJECTED_OR_DEFERRED_JSON_FILE_NAME,
            "path": str(output_dir / REJECTED_OR_DEFERRED_JSON_FILE_NAME),
            "purpose": "Rejected, needs-context, deferred, or invalid rows.",
        },
        {
            "artifact_name": VALIDATION_ISSUES_JSON_FILE_NAME,
            "path": str(output_dir / VALIDATION_ISSUES_JSON_FILE_NAME),
            "purpose": "Validation issues summary.",
        },
    ]


def build_reviewed_alias_decision_ingestion_345c5(
    *,
    alias_suggestion_human_review_package_345c4_dir: Path,
    reviewed_alias_workbook: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    manifest_345c4_path = _require_existing(
        alias_suggestion_human_review_package_345c4_dir / INPUT_MANIFEST_NAME
    )
    original_review_rows_path = _require_existing(
        alias_suggestion_human_review_package_345c4_dir / INPUT_REVIEW_ROWS_JSON_NAME
    )
    _ = _require_existing(alias_suggestion_human_review_package_345c4_dir / INPUT_WORKBOOK_NAME)
    reviewed_alias_workbook = _require_existing(reviewed_alias_workbook)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged_before = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    reviewed_workbook_hash_before = sha256_file(reviewed_alias_workbook)
    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [manifest_345c4_path, original_review_rows_path, reviewed_alias_workbook]
    }

    manifest_345c4 = _read_json(manifest_345c4_path)
    if _safe_text(manifest_345c4.get("decision")) != READY_DECISION_345C4:
        raise ValueError("345C4 manifest decision is not READY.")

    original_review_rows = _load_json_rows(original_review_rows_path)
    reviewed_rows = _load_reviewed_rows(reviewed_alias_workbook)

    original_by_id: Dict[str, Dict[str, Any]] = {}
    for row in original_review_rows:
        row_id = _safe_text(row.get("alias_review_row_id"))
        adjudication_id = _safe_text(row.get("alias_adjudication_id"))
        if not row_id or not adjudication_id:
            raise ValueError("Original 345C4 review rows missing stable ids.")
        if row_id in original_by_id:
            raise ValueError(f"Duplicate original alias_review_row_id: {row_id}")
        original_by_id[row_id] = row

    reviewed_seen: set[str] = set()
    merged_rows: List[Dict[str, Any]] = []
    validation_issues_rows: List[Dict[str, Any]] = []

    for reviewed_row in reviewed_rows:
        row_id = _safe_text(reviewed_row.get("alias_review_row_id"))
        adjudication_id = _safe_text(reviewed_row.get("alias_adjudication_id"))
        if not row_id or not adjudication_id:
            raise ValueError("Reviewed workbook row missing alias_review_row_id or alias_adjudication_id.")
        if row_id in reviewed_seen:
            raise ValueError(f"Duplicate reviewed alias_review_row_id: {row_id}")
        reviewed_seen.add(row_id)
        original_row = original_by_id.get(row_id)
        if original_row is None:
            raise ValueError(f"Reviewed row id not found in original package: {row_id}")
        if _safe_text(original_row.get("alias_adjudication_id")) != adjudication_id:
            raise ValueError(f"Reviewed row id/adjudication mismatch: {row_id}")

        merged = dict(original_row)
        merged["human_alias_review_decision"] = _safe_text(reviewed_row.get("human_alias_review_decision"))
        merged["approved_standard_metric"] = _safe_text(reviewed_row.get("approved_standard_metric"))
        merged["approved_new_standard_metric"] = _safe_text(reviewed_row.get("approved_new_standard_metric"))
        merged["alias_reviewer"] = _safe_text(reviewed_row.get("alias_reviewer"))
        merged["alias_reviewed_at"] = _safe_text(reviewed_row.get("alias_reviewed_at"))
        merged["alias_review_notes"] = _safe_text(reviewed_row.get("alias_review_notes"))
        validation_status, validation_issues, eligible, canonical_target = _validation_for_row(merged)
        merged["decision_validation_status"] = validation_status
        merged["decision_validation_issues"] = validation_issues
        merged["apply_simulation_eligible"] = eligible
        merged["canonical_alias_target"] = canonical_target
        merged["alias_rule_update_allowed"] = False
        merged_rows.append(merged)
        if validation_issues:
            validation_issues_rows.append(
                {
                    "alias_review_row_id": row_id,
                    "alias_adjudication_id": adjudication_id,
                    "human_alias_review_decision": merged["human_alias_review_decision"],
                    "decision_validation_issues": validation_issues,
                }
            )

    if len(merged_rows) != len(original_review_rows):
        raise ValueError(
            f"Reviewed row count {len(merged_rows)} does not match original review row count {len(original_review_rows)}."
        )

    validated_approved_rows = [
        row for row in merged_rows if bool(row.get("apply_simulation_eligible"))
    ]
    rejected_or_deferred_rows = [
        row
        for row in merged_rows
        if not bool(row.get("apply_simulation_eligible"))
    ]

    approved_existing_mapping_count = sum(
        1 for row in merged_rows if row.get("human_alias_review_decision") == "APPROVE_EXISTING_MAPPING"
    )
    approved_new_standard_count = sum(
        1 for row in merged_rows if row.get("human_alias_review_decision") == "APPROVE_NEW_STANDARD"
    )
    rejected_alias_count = sum(
        1 for row in merged_rows if row.get("human_alias_review_decision") == "REJECT_ALIAS"
    )
    needs_more_context_count = sum(
        1 for row in merged_rows if row.get("human_alias_review_decision") == "NEEDS_MORE_CONTEXT"
    )
    deferred_count = sum(
        1 for row in merged_rows if row.get("human_alias_review_decision") == "DEFER"
    )
    missing_decision_count = sum(
        1 for row in merged_rows if not _safe_text(row.get("human_alias_review_decision"))
    )
    invalid_decision_count = sum(
        1
        for row in merged_rows
        if _safe_text(row.get("human_alias_review_decision"))
        and _safe_text(row.get("human_alias_review_decision")) not in ALLOWED_DECISIONS
    )
    validation_issue_count = len(validation_issues_rows)
    apply_simulation_eligible_count = len(validated_approved_rows)
    alias_rule_update_allowed_count = 0

    decision_summary = {
        "reviewed_row_count": len(merged_rows),
        "approved_existing_mapping_count": approved_existing_mapping_count,
        "approved_new_standard_count": approved_new_standard_count,
        "rejected_alias_count": rejected_alias_count,
        "needs_more_context_count": needs_more_context_count,
        "deferred_count": deferred_count,
        "missing_decision_count": missing_decision_count,
        "invalid_decision_count": invalid_decision_count,
        "validation_issue_count": validation_issue_count,
        "apply_simulation_eligible_count": apply_simulation_eligible_count,
    }

    reviewed_workbook_hash_after = sha256_file(reviewed_alias_workbook)
    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [manifest_345c4_path, original_review_rows_path, reviewed_alias_workbook]
    }
    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged_after = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    qa_checks = [
        {"check": "input_manifest_exists", "passed": manifest_345c4_path.exists()},
        {"check": "input_review_rows_exist", "passed": original_review_rows_path.exists()},
        {"check": "reviewed_workbook_exists", "passed": reviewed_alias_workbook.exists()},
        {"check": "input_345c4_decision_ready", "passed": _safe_text(manifest_345c4.get("decision")) == READY_DECISION_345C4},
        {"check": "reviewed_row_count_matches_original", "passed": len(merged_rows) == len(original_review_rows)},
        {"check": "reviewed_workbook_unchanged", "passed": reviewed_workbook_hash_before == reviewed_workbook_hash_after},
        {"check": "no_write_back_to_inputs", "passed": input_hashes_before == input_hashes_after},
        {"check": "official_assets_unchanged", "passed": official_assets_before == official_assets_after},
        {"check": "protected_dirty_status_unchanged", "passed": protected_before == protected_after},
        {"check": "forbidden_paths_not_staged", "passed": forbidden_staged_before == forbidden_staged_after},
        {"check": "alias_rule_update_allowed_forced_false", "passed": all(row.get("alias_rule_update_allowed") is False for row in merged_rows)},
        {"check": "formal_client_export_allowed_false", "passed": True},
        {"check": "client_ready_false", "passed": True},
        {"check": "production_ready_false", "passed": True},
    ]
    qa_fail_count = sum(1 for row in qa_checks if not row["passed"])

    no_apply_proof = build_no_apply_proof(
        stage="345C5",
        files_read=[
            str(manifest_345c4_path),
            str(original_review_rows_path),
            str(reviewed_alias_workbook),
        ],
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    manifest = {
        "decision": READY_DECISION_345C5,
        "input_stage": INPUT_STAGE_345C5,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": (
            input_hashes_before == input_hashes_after
            and official_assets_before == official_assets_after
            and protected_before == protected_after
            and reviewed_workbook_hash_before == reviewed_workbook_hash_after
        ),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c4_decision": _safe_text(manifest_345c4.get("decision")),
        "input_review_row_count": len(original_review_rows),
        "reviewed_row_count": len(merged_rows),
        "approved_existing_mapping_count": approved_existing_mapping_count,
        "approved_new_standard_count": approved_new_standard_count,
        "rejected_alias_count": rejected_alias_count,
        "needs_more_context_count": needs_more_context_count,
        "deferred_count": deferred_count,
        "missing_decision_count": missing_decision_count,
        "invalid_decision_count": invalid_decision_count,
        "validation_issue_count": validation_issue_count,
        "apply_simulation_eligible_count": apply_simulation_eligible_count,
        "alias_rule_update_allowed_count": alias_rule_update_allowed_count,
        "alias_apply_simulation_ready": apply_simulation_eligible_count > 0 and validation_issue_count == 0,
        "input_345c4_package_dir": str(alias_suggestion_human_review_package_345c4_dir),
        "reviewed_alias_workbook": str(reviewed_alias_workbook),
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    return {
        "manifest": manifest,
        "reviewed_decisions": merged_rows,
        "validated_approved_aliases": validated_approved_rows,
        "rejected_or_deferred_aliases": rejected_or_deferred_rows,
        "validation_issues": validation_issues_rows,
        "decision_summary": decision_summary,
        "qa_json": {
            "decision": manifest["decision"],
            "qa_fail_count": qa_fail_count,
            "checks": qa_checks,
        },
        "no_apply_proof": no_apply_proof,
        "artifact_index_rows": _artifact_rows(output_dir),
    }
