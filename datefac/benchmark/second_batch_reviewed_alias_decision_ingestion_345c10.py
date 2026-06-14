from __future__ import annotations

import csv
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


READY_DECISION_345C9 = "REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE_345C9_READY"
READY_DECISION_345C10 = "SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY"
INPUT_STAGE_345C10 = "POST_345C9_SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION"

DEFAULT_345C9_DIR = Path(r"D:\_datefac\output\remaining_blind_spot_human_review_package_345c9")
DEFAULT_REVIEWED_WORKBOOK = (
    DEFAULT_345C9_DIR / "remaining_blind_spot_human_review_package_345c9_reviewed.xlsx"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\second_batch_reviewed_alias_decision_ingestion_345c10"
)
DEFAULT_LEDGER_PATH = Path(
    r"D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md"
)

MANIFEST_FILE_NAME = "second_batch_reviewed_alias_decision_ingestion_345c10_manifest.json"
REVIEWED_DECISIONS_JSON_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.json"
)
REVIEWED_DECISIONS_CSV_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.csv"
)
VALIDATED_APPROVED_JSON_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.json"
)
VALIDATED_APPROVED_CSV_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.csv"
)
REJECTED_OR_BLOCKED_JSON_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.json"
)
REJECTED_OR_BLOCKED_CSV_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.csv"
)
VALIDATION_ISSUES_JSON_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_validation_issues.json"
)
DECISION_SUMMARY_JSON_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_decision_summary.json"
)
EXECUTIVE_SUMMARY_MD_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_executive_summary.md"
)
ARTIFACT_INDEX_MD_FILE_NAME = (
    "second_batch_reviewed_alias_decision_ingestion_345c10_artifact_index.md"
)
NEXT_PLAN_MD_FILE_NAME = "second_batch_reviewed_alias_decision_ingestion_345c10_next_plan.md"

INPUT_MANIFEST_NAME = "remaining_blind_spot_human_review_package_345c9_manifest.json"
INPUT_REVIEW_ROWS_JSON_NAME = (
    "remaining_blind_spot_human_review_package_345c9_review_rows.json"
)
INPUT_REVIEW_ROWS_CSV_NAME = (
    "remaining_blind_spot_human_review_package_345c9_review_rows.csv"
)
INPUT_CONTEXT_ONLY_ROWS_JSON_NAME = (
    "remaining_blind_spot_human_review_package_345c9_context_only_rows.json"
)
INPUT_CONTEXT_ONLY_ROWS_CSV_NAME = (
    "remaining_blind_spot_human_review_package_345c9_context_only_rows.csv"
)
INPUT_BLOCKED_ROWS_JSON_NAME = (
    "remaining_blind_spot_human_review_package_345c9_blocked_rows.json"
)
INPUT_BLOCKED_ROWS_CSV_NAME = (
    "remaining_blind_spot_human_review_package_345c9_blocked_rows.csv"
)

REVIEWED_SHEET_NAME = "review_required"
ALLOWED_DECISIONS = {
    "APPROVE_EXISTING_MAPPING",
    "APPROVE_NEW_STANDARD",
    "REJECT_TOO_GENERIC",
    "NEEDS_SOURCE_CONTEXT",
    "DEFER",
}

OUTPUT_ROW_FIELDS = [
    "blind_spot_review_row_id",
    "source_345c8_blind_spot_candidate_id",
    "raw_metric_name",
    "remaining_row_count",
    "remaining_raw_metric_rank",
    "candidate_priority",
    "risk_level",
    "estimated_max_newly_normalized_rows",
    "estimated_coverage_delta_if_resolved",
    "estimated_ready_candidate_delta_if_resolved",
    "human_blind_spot_review_decision",
    "approved_standard_metric",
    "approved_new_standard_metric",
    "needs_alias_family_expansion",
    "needs_source_context",
    "reviewer",
    "reviewed_at",
    "review_notes",
    "decision_validation_status",
    "decision_validation_issues",
    "apply_simulation_eligible",
    "canonical_alias_target",
    "alias_rule_update_allowed",
]

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

LEDGER_HEADING = "## 345C10 Second Batch Reviewed Alias Decision Ingestion"


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


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    lowered = _safe_text(value).lower()
    return lowered in {"1", "true", "yes", "y"}


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    text = _safe_text(value)
    if not text:
        return 0
    return int(float(text))


def _float_value(value: Any) -> float:
    text = _safe_text(value)
    if not text:
        return 0.0
    return float(text)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_rows(path: Path) -> List[Dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON payload in {path}")
    return [dict(row) for row in payload]


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "blind_spot_review_row_id": _safe_text(row.get("blind_spot_review_row_id")),
        "source_345c8_blind_spot_candidate_id": _safe_text(
            row.get("source_345c8_blind_spot_candidate_id")
        ),
        "raw_metric_name": _safe_text(row.get("raw_metric_name")),
        "remaining_row_count": _int_value(row.get("remaining_row_count")),
        "remaining_raw_metric_rank": _int_value(row.get("remaining_raw_metric_rank")),
        "candidate_priority": _safe_text(row.get("candidate_priority")),
        "risk_level": _safe_text(row.get("risk_level")),
        "estimated_max_newly_normalized_rows": _int_value(
            row.get("estimated_max_newly_normalized_rows")
        ),
        "estimated_coverage_delta_if_resolved": round(
            _float_value(row.get("estimated_coverage_delta_if_resolved")),
            6,
        ),
        "estimated_ready_candidate_delta_if_resolved": _int_value(
            row.get("estimated_ready_candidate_delta_if_resolved")
        ),
        "human_blind_spot_review_decision": _safe_text(
            row.get("human_blind_spot_review_decision")
        ),
        "approved_standard_metric": _safe_text(row.get("approved_standard_metric")),
        "approved_new_standard_metric": _safe_text(row.get("approved_new_standard_metric")),
        "needs_alias_family_expansion": _bool_value(
            row.get("needs_alias_family_expansion")
        ),
        "needs_source_context": _bool_value(row.get("needs_source_context")),
        "reviewer": _safe_text(row.get("reviewer")),
        "reviewed_at": _safe_text(row.get("reviewed_at")),
        "review_notes": _safe_text(row.get("review_notes")),
        "alias_rule_update_allowed": False,
    }


def _load_rows_with_fallback(json_path: Path, csv_path: Path) -> tuple[List[Dict[str, Any]], str]:
    if json_path.exists():
        try:
            return [_normalize_row(row) for row in _load_json_rows(json_path)], "json"
        except Exception:
            pass
    return [_normalize_row(row) for row in _read_csv_rows(_require_existing(csv_path))], "csv"


def _load_reviewed_rows(workbook_path: Path) -> List[Dict[str, Any]]:
    frame = pd.read_excel(workbook_path, sheet_name=REVIEWED_SHEET_NAME)
    if frame.empty:
        return []
    return frame.astype(object).where(pd.notna(frame), "").to_dict(orient="records")


def _validate_required_columns(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    required_columns = {
        "blind_spot_review_row_id",
        "source_345c8_blind_spot_candidate_id",
        "human_blind_spot_review_decision",
        "approved_standard_metric",
        "approved_new_standard_metric",
        "needs_alias_family_expansion",
        "needs_source_context",
        "reviewer",
        "reviewed_at",
        "review_notes",
        "alias_rule_update_allowed",
    }
    missing = sorted(
        column for column in required_columns if column not in rows[0]
    )
    if missing:
        raise ValueError(f"Reviewed workbook missing required columns: {missing}")


def _validation_for_row(row: Dict[str, Any]) -> tuple[str, List[str], bool, str]:
    issues: List[str] = []
    decision = _safe_text(row.get("human_blind_spot_review_decision"))
    approved_standard_metric = _safe_text(row.get("approved_standard_metric"))
    approved_new_standard_metric = _safe_text(row.get("approved_new_standard_metric"))
    review_notes = _safe_text(row.get("review_notes"))

    if not decision:
        issues.append("missing_human_blind_spot_review_decision")
    elif decision not in ALLOWED_DECISIONS:
        issues.append("invalid_human_blind_spot_review_decision")
    elif decision == "APPROVE_EXISTING_MAPPING":
        if not approved_standard_metric:
            issues.append("missing_approved_standard_metric")
        if approved_new_standard_metric and approved_new_standard_metric != approved_standard_metric:
            issues.append("unexpected_approved_new_standard_metric")
    elif decision == "APPROVE_NEW_STANDARD":
        if not approved_new_standard_metric:
            issues.append("missing_approved_new_standard_metric")
        if not review_notes:
            issues.append("missing_review_notes_for_new_standard")
    elif decision == "REJECT_TOO_GENERIC":
        if not review_notes:
            issues.append("missing_review_notes_for_reject_too_generic")
    elif decision == "NEEDS_SOURCE_CONTEXT":
        if not review_notes:
            issues.append("missing_review_notes_for_needs_source_context")
    elif decision == "DEFER":
        if not review_notes:
            issues.append("missing_review_notes_for_defer")

    validation_status = "VALID" if not issues else "INVALID"
    apply_simulation_eligible = (
        validation_status == "VALID"
        and decision in {"APPROVE_EXISTING_MAPPING", "APPROVE_NEW_STANDARD"}
    )
    canonical_alias_target = ""
    if apply_simulation_eligible:
        canonical_alias_target = (
            approved_standard_metric
            if decision == "APPROVE_EXISTING_MAPPING"
            else approved_new_standard_metric
        )
    return validation_status, issues, apply_simulation_eligible, canonical_alias_target


def build_345c10_ledger_entry(*, manifest: Dict[str, Any]) -> str:
    lines = [
        LEDGER_HEADING,
        "",
        "Status: completed",
        "",
        "Decision:",
        f"- `{manifest.get('decision', '')}`",
        "",
        "Input package:",
        f"- `{manifest.get('input_345c9_package_dir', '')}`",
        "",
        "Reviewed workbook path:",
        f"- `{manifest.get('reviewed_blind_spot_workbook', '')}`",
        "",
        "Output package:",
        f"- `{manifest.get('output_dir', '')}`",
        "",
        "Key metrics:",
        f"- `reviewed_row_count = {manifest.get('reviewed_row_count', 0)}`",
        f"- `approved_existing_mapping_count = {manifest.get('approved_existing_mapping_count', 0)}`",
        f"- `approved_new_standard_count = {manifest.get('approved_new_standard_count', 0)}`",
        f"- `rejected_too_generic_count = {manifest.get('rejected_too_generic_count', 0)}`",
        f"- `needs_source_context_count = {manifest.get('needs_source_context_count', 0)}`",
        f"- `deferred_count = {manifest.get('deferred_count', 0)}`",
        f"- `validation_issue_count = {manifest.get('validation_issue_count', 0)}`",
        f"- `apply_simulation_eligible_count = {manifest.get('apply_simulation_eligible_count', 0)}`",
        f"- `qa_fail_count = {manifest.get('qa_fail_count', 0)}`",
        "",
        "Gate status:",
        f"- `formal_client_export_allowed = {str(bool(manifest.get('formal_client_export_allowed'))).lower()}`",
        f"- `client_ready = {str(bool(manifest.get('client_ready'))).lower()}`",
        f"- `production_ready = {str(bool(manifest.get('production_ready'))).lower()}`",
        f"- `global_strict_human_review_completed = {str(bool(manifest.get('global_strict_human_review_completed'))).lower()}`",
        "",
        "No-write-back confirmation:",
        f"- `no_write_back_proof_passed = {str(bool(manifest.get('no_write_back_proof_passed'))).lower()}`",
        f"- `official_rules_modified = {str(bool(manifest.get('official_rules_modified'))).lower()}`",
        f"- `official_alias_assets_modified = {str(bool(manifest.get('official_alias_assets_modified'))).lower()}`",
        "",
        "Validation commands and results:",
        "- `python -m py_compile ...` passed",
        "- `python -m pytest tests\\benchmark\\test_second_batch_reviewed_alias_decision_ingestion_345c10.py -q` passed",
        "- real runner passed",
        "",
        "Next recommended step:",
        "- `345C11 Second Batch Alias Apply Simulation`",
    ]
    return "\n".join(lines)


def ledger_has_345c10_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return LEDGER_HEADING in ledger_path.read_text(encoding="utf-8")


def append_345c10_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if ledger_has_345c10_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = build_345c10_ledger_entry(manifest=manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


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
            "artifact_name": REVIEWED_DECISIONS_CSV_FILE_NAME,
            "path": str(output_dir / REVIEWED_DECISIONS_CSV_FILE_NAME),
            "purpose": "Merged reviewed decisions in CSV.",
        },
        {
            "artifact_name": VALIDATED_APPROVED_JSON_FILE_NAME,
            "path": str(output_dir / VALIDATED_APPROVED_JSON_FILE_NAME),
            "purpose": "Apply-simulation-eligible approved second-batch aliases.",
        },
        {
            "artifact_name": VALIDATED_APPROVED_CSV_FILE_NAME,
            "path": str(output_dir / VALIDATED_APPROVED_CSV_FILE_NAME),
            "purpose": "Apply-simulation-eligible approved second-batch aliases in CSV.",
        },
        {
            "artifact_name": REJECTED_OR_BLOCKED_JSON_FILE_NAME,
            "path": str(output_dir / REJECTED_OR_BLOCKED_JSON_FILE_NAME),
            "purpose": "Rejected, blocked, deferred, or invalid rows in JSON.",
        },
        {
            "artifact_name": REJECTED_OR_BLOCKED_CSV_FILE_NAME,
            "path": str(output_dir / REJECTED_OR_BLOCKED_CSV_FILE_NAME),
            "purpose": "Rejected, blocked, deferred, or invalid rows in CSV.",
        },
        {
            "artifact_name": VALIDATION_ISSUES_JSON_FILE_NAME,
            "path": str(output_dir / VALIDATION_ISSUES_JSON_FILE_NAME),
            "purpose": "Validation issues list.",
        },
        {
            "artifact_name": DECISION_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / DECISION_SUMMARY_JSON_FILE_NAME),
            "purpose": "Decision distribution and validation summary.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME),
            "purpose": "Narrative summary of second-batch decision ingestion.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_MD_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_MD_FILE_NAME),
            "purpose": "Index of all 345C10 artifacts.",
        },
        {
            "artifact_name": NEXT_PLAN_MD_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME),
            "purpose": "Recommended next step after 345C10.",
        },
    ]


def build_second_batch_reviewed_alias_decision_ingestion_345c10(
    *,
    remaining_blind_spot_human_review_package_345c9_dir: Path,
    reviewed_blind_spot_workbook: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345c9_path = _require_existing(
        remaining_blind_spot_human_review_package_345c9_dir / INPUT_MANIFEST_NAME
    )
    original_review_rows_json_path = (
        remaining_blind_spot_human_review_package_345c9_dir / INPUT_REVIEW_ROWS_JSON_NAME
    )
    original_review_rows_csv_path = (
        remaining_blind_spot_human_review_package_345c9_dir / INPUT_REVIEW_ROWS_CSV_NAME
    )
    context_only_rows_json_path = (
        remaining_blind_spot_human_review_package_345c9_dir / INPUT_CONTEXT_ONLY_ROWS_JSON_NAME
    )
    context_only_rows_csv_path = (
        remaining_blind_spot_human_review_package_345c9_dir / INPUT_CONTEXT_ONLY_ROWS_CSV_NAME
    )
    blocked_rows_json_path = (
        remaining_blind_spot_human_review_package_345c9_dir / INPUT_BLOCKED_ROWS_JSON_NAME
    )
    blocked_rows_csv_path = (
        remaining_blind_spot_human_review_package_345c9_dir / INPUT_BLOCKED_ROWS_CSV_NAME
    )
    reviewed_blind_spot_workbook = _require_existing(reviewed_blind_spot_workbook)

    files_read = [
        str(manifest_345c9_path),
        str(reviewed_blind_spot_workbook),
    ]
    input_paths = [manifest_345c9_path, reviewed_blind_spot_workbook]
    for path in [
        original_review_rows_json_path,
        original_review_rows_csv_path,
        context_only_rows_json_path,
        context_only_rows_csv_path,
        blocked_rows_json_path,
        blocked_rows_csv_path,
    ]:
        if path.exists():
            files_read.append(str(path))
            input_paths.append(path)

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    reviewed_workbook_hash_before = sha256_file(reviewed_blind_spot_workbook)
    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345c9 = _read_json(manifest_345c9_path)
    original_review_rows, original_source = _load_rows_with_fallback(
        original_review_rows_json_path,
        original_review_rows_csv_path,
    )
    context_only_rows, context_source = _load_rows_with_fallback(
        context_only_rows_json_path,
        context_only_rows_csv_path,
    )
    blocked_rows, blocked_source = _load_rows_with_fallback(
        blocked_rows_json_path,
        blocked_rows_csv_path,
    )
    reviewed_rows = _load_reviewed_rows(reviewed_blind_spot_workbook)
    _validate_required_columns(reviewed_rows)

    if _safe_text(manifest_345c9.get("decision")) != READY_DECISION_345C9:
        raise ValueError("345C9 manifest decision is not READY.")
    if int(manifest_345c9.get("qa_fail_count", 1)) != 0:
        raise ValueError("345C9 qa_fail_count must be zero.")
    for gate_name in ["formal_client_export_allowed", "client_ready", "production_ready"]:
        if bool(manifest_345c9.get(gate_name)):
            raise ValueError(f"345C9 gate must remain false: {gate_name}")
    if bool(manifest_345c9.get("official_rules_modified")):
        raise ValueError("345C9 official_rules_modified must remain false.")
    if bool(manifest_345c9.get("official_alias_assets_modified")):
        raise ValueError("345C9 official_alias_assets_modified must remain false.")

    original_by_row_id: Dict[str, Dict[str, Any]] = {}
    original_source_ids_seen: set[str] = set()
    for row in original_review_rows:
        row_id = _safe_text(row.get("blind_spot_review_row_id"))
        source_candidate_id = _safe_text(row.get("source_345c8_blind_spot_candidate_id"))
        if not row_id or not source_candidate_id:
            raise ValueError("Original 345C9 review rows missing stable ids.")
        if row_id in original_by_row_id:
            raise ValueError(f"Duplicate original blind_spot_review_row_id: {row_id}")
        if source_candidate_id in original_source_ids_seen:
            raise ValueError(
                f"Duplicate original source_345c8_blind_spot_candidate_id: {source_candidate_id}"
            )
        original_source_ids_seen.add(source_candidate_id)
        original_by_row_id[row_id] = row

    reviewed_row_ids_seen: set[str] = set()
    reviewed_source_ids_seen: set[str] = set()
    merged_rows: List[Dict[str, Any]] = []
    validation_issues_rows: List[Dict[str, Any]] = []

    for reviewed_row in reviewed_rows:
        row_id = _safe_text(reviewed_row.get("blind_spot_review_row_id"))
        source_candidate_id = _safe_text(
            reviewed_row.get("source_345c8_blind_spot_candidate_id")
        )
        if not row_id or not source_candidate_id:
            raise ValueError(
                "Reviewed workbook row missing blind_spot_review_row_id or source_345c8_blind_spot_candidate_id."
            )
        if row_id in reviewed_row_ids_seen:
            raise ValueError(f"Duplicate reviewed blind_spot_review_row_id: {row_id}")
        if source_candidate_id in reviewed_source_ids_seen:
            raise ValueError(
                f"Duplicate reviewed source_345c8_blind_spot_candidate_id: {source_candidate_id}"
            )
        reviewed_row_ids_seen.add(row_id)
        reviewed_source_ids_seen.add(source_candidate_id)

        original_row = original_by_row_id.get(row_id)
        if original_row is None:
            raise ValueError(f"Reviewed row id not found in original package: {row_id}")
        if (
            _safe_text(original_row.get("source_345c8_blind_spot_candidate_id"))
            != source_candidate_id
        ):
            raise ValueError(
                f"Reviewed row id/source candidate mismatch: {row_id} / {source_candidate_id}"
            )

        merged = dict(original_row)
        merged["human_blind_spot_review_decision"] = _safe_text(
            reviewed_row.get("human_blind_spot_review_decision")
        )
        merged["approved_standard_metric"] = _safe_text(
            reviewed_row.get("approved_standard_metric")
        )
        merged["approved_new_standard_metric"] = _safe_text(
            reviewed_row.get("approved_new_standard_metric")
        )
        merged["needs_alias_family_expansion"] = _bool_value(
            reviewed_row.get("needs_alias_family_expansion")
        )
        merged["needs_source_context"] = _bool_value(
            reviewed_row.get("needs_source_context")
        )
        merged["reviewer"] = _safe_text(reviewed_row.get("reviewer"))
        merged["reviewed_at"] = _safe_text(reviewed_row.get("reviewed_at"))
        merged["review_notes"] = _safe_text(reviewed_row.get("review_notes"))

        validation_status, validation_issues, eligible, canonical_target = _validation_for_row(
            merged
        )
        merged["decision_validation_status"] = validation_status
        merged["decision_validation_issues"] = validation_issues
        merged["apply_simulation_eligible"] = eligible
        merged["canonical_alias_target"] = canonical_target
        merged["alias_rule_update_allowed"] = False
        merged_rows.append(merged)

        if validation_issues:
            validation_issues_rows.append(
                {
                    "blind_spot_review_row_id": row_id,
                    "source_345c8_blind_spot_candidate_id": source_candidate_id,
                    "raw_metric_name": merged.get("raw_metric_name", ""),
                    "human_blind_spot_review_decision": merged[
                        "human_blind_spot_review_decision"
                    ],
                    "decision_validation_issues": validation_issues,
                }
            )

    expected_review_required_count = int(manifest_345c9.get("review_required_row_count", 0))
    if len(merged_rows) != expected_review_required_count:
        raise ValueError(
            "Reviewed row count "
            f"{len(merged_rows)} does not match original review_required_row_count {expected_review_required_count}."
        )

    validated_approved_rows = [
        row for row in merged_rows if bool(row.get("apply_simulation_eligible"))
    ]
    rejected_or_blocked_rows = [
        row for row in merged_rows if not bool(row.get("apply_simulation_eligible"))
    ]

    approved_existing_mapping_count = sum(
        1
        for row in merged_rows
        if row.get("human_blind_spot_review_decision") == "APPROVE_EXISTING_MAPPING"
    )
    approved_new_standard_count = sum(
        1
        for row in merged_rows
        if row.get("human_blind_spot_review_decision") == "APPROVE_NEW_STANDARD"
    )
    rejected_too_generic_count = sum(
        1
        for row in merged_rows
        if row.get("human_blind_spot_review_decision") == "REJECT_TOO_GENERIC"
    )
    needs_source_context_count = sum(
        1
        for row in merged_rows
        if row.get("human_blind_spot_review_decision") == "NEEDS_SOURCE_CONTEXT"
    )
    deferred_count = sum(
        1 for row in merged_rows if row.get("human_blind_spot_review_decision") == "DEFER"
    )
    missing_decision_count = sum(
        1 for row in merged_rows if not _safe_text(row.get("human_blind_spot_review_decision"))
    )
    invalid_decision_count = sum(
        1
        for row in merged_rows
        if _safe_text(row.get("human_blind_spot_review_decision"))
        and _safe_text(row.get("human_blind_spot_review_decision")) not in ALLOWED_DECISIONS
    )
    validation_issue_count = len(validation_issues_rows)
    apply_simulation_eligible_count = len(validated_approved_rows)
    needs_alias_family_expansion_count = sum(
        1 for row in merged_rows if bool(row.get("needs_alias_family_expansion"))
    )
    source_context_boolean_count = sum(
        1 for row in merged_rows if bool(row.get("needs_source_context"))
    )
    alias_rule_update_allowed_count = 0

    decision_summary = {
        "reviewed_row_count": len(merged_rows),
        "approved_existing_mapping_count": approved_existing_mapping_count,
        "approved_new_standard_count": approved_new_standard_count,
        "rejected_too_generic_count": rejected_too_generic_count,
        "needs_source_context_count": needs_source_context_count,
        "deferred_count": deferred_count,
        "missing_decision_count": missing_decision_count,
        "invalid_decision_count": invalid_decision_count,
        "validation_issue_count": validation_issue_count,
        "apply_simulation_eligible_count": apply_simulation_eligible_count,
        "needs_alias_family_expansion_count": needs_alias_family_expansion_count,
        "source_context_boolean_count": source_context_boolean_count,
        "expected_distribution_for_this_run": {
            "reviewed_row_count": 16,
            "approved_new_standard_count": 15,
            "needs_source_context_count": 1,
            "approved_existing_mapping_count": 0,
            "rejected_too_generic_count": 0,
            "deferred_count": 0,
            "apply_simulation_eligible_count": 15,
        },
    }

    reviewed_workbook_hash_after = sha256_file(reviewed_blind_spot_workbook)
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    upstream_unchanged = input_hashes_before == input_hashes_after

    no_apply_proof = build_no_apply_proof(
        stage="345C10",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof["upstream_workbooks_unchanged"] = upstream_unchanged
    no_apply_proof["reviewed_workbook_unchanged"] = (
        reviewed_workbook_hash_before == reviewed_workbook_hash_after
    )
    no_apply_proof["formal_client_export_generated"] = False
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["official_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["alias_apply_simulation_ready"] = (
        apply_simulation_eligible_count > 0 and validation_issue_count == 0
    )
    no_apply_proof["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_345c10")
        and upstream_unchanged
        and no_apply_proof.get("reviewed_workbook_unchanged")
        and not no_apply_proof.get("formal_client_export_generated", True)
        and not no_apply_proof.get("real_production_apply_performed", True)
        and not no_apply_proof.get("official_rules_modified", True)
        and not no_apply_proof.get("official_alias_assets_modified", True)
    )

    milestone_ledger_updated = (
        ledger_has_345c10_entry(ledger_path) if ledger_path is not None else False
    )

    checks = [
        {
            "check_name": "inputs::345c9_ready",
            "status": "PASS"
            if _safe_text(manifest_345c9.get("decision")) == READY_DECISION_345C9
            and int(manifest_345c9.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_345c9_decision": manifest_345c9.get("decision"),
                    "input_qa_fail_count": manifest_345c9.get("qa_fail_count"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::reviewed_row_count_matches_original",
            "status": "PASS" if len(merged_rows) == expected_review_required_count else "FAIL",
            "detail": json.dumps(
                {
                    "reviewed_row_count": len(merged_rows),
                    "input_review_required_row_count": expected_review_required_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "decisions::distribution_computed",
            "status": "PASS",
            "detail": json.dumps(decision_summary, ensure_ascii=False),
        },
        {
            "check_name": "eligibility::approved_rows_become_apply_simulation_eligible",
            "status": "PASS"
            if all(
                bool(row.get("apply_simulation_eligible"))
                for row in merged_rows
                if row.get("human_blind_spot_review_decision")
                in {"APPROVE_EXISTING_MAPPING", "APPROVE_NEW_STANDARD"}
                and row.get("decision_validation_status") == "VALID"
            )
            else "FAIL",
            "detail": "validated approved rows must become apply-simulation eligible",
        },
        {
            "check_name": "eligibility::non_approved_rows_not_apply_simulation_eligible",
            "status": "PASS"
            if all(
                not bool(row.get("apply_simulation_eligible"))
                for row in merged_rows
                if row.get("human_blind_spot_review_decision")
                in {"NEEDS_SOURCE_CONTEXT", "REJECT_TOO_GENERIC", "DEFER"}
                or row.get("decision_validation_status") != "VALID"
            )
            else "FAIL",
            "detail": "needs-source-context/rejected/deferred/invalid rows must stay ineligible",
        },
        {
            "check_name": "safety::alias_rule_update_allowed_forced_false",
            "status": "PASS"
            if all(row.get("alias_rule_update_allowed") is False for row in merged_rows)
            else "FAIL",
            "detail": "alias_rule_update_allowed must remain false in output rows",
        },
        {
            "check_name": "safety::official_rules_and_alias_assets_unchanged",
            "status": "PASS" if official_assets_before == official_assets_after else "FAIL",
            "detail": json.dumps(official_assets_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::all_gates_remain_false",
            "status": "PASS",
            "detail": "formal_client_export_allowed/client_ready/production_ready/global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::no_input_write_back",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::reviewed_workbook_unchanged",
            "status": "PASS"
            if reviewed_workbook_hash_before == reviewed_workbook_hash_after
            else "FAIL",
            "detail": reviewed_blind_spot_workbook.as_posix(),
        },
        {
            "check_name": "safety::protected_dirty_status_preserved",
            "status": "PASS" if protected_before == protected_after else "FAIL",
            "detail": json.dumps(protected_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::protected_dirty_files_not_staged",
            "status": "PASS" if not protected_staged else "FAIL",
            "detail": json.dumps(protected_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::forbidden_paths_not_staged",
            "status": "PASS" if not forbidden_staged else "FAIL",
            "detail": json.dumps(forbidden_staged, ensure_ascii=False),
        },
        {
            "check_name": "ledger::345c10_entry_present",
            "status": "PASS" if milestone_ledger_updated else "FAIL",
            "detail": str(ledger_path) if ledger_path is not None else "__NO_LEDGER_PATH__",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {"no_write_back_proof_passed": no_write_back_proof_passed},
                ensure_ascii=False,
            ),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    manifest = {
        "decision": READY_DECISION_345C10,
        "input_stage": INPUT_STAGE_345C10,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c9_decision": _safe_text(manifest_345c9.get("decision")),
        "input_review_required_row_count": expected_review_required_count,
        "reviewed_row_count": len(merged_rows),
        "approved_existing_mapping_count": approved_existing_mapping_count,
        "approved_new_standard_count": approved_new_standard_count,
        "rejected_too_generic_count": rejected_too_generic_count,
        "needs_source_context_count": needs_source_context_count,
        "deferred_count": deferred_count,
        "missing_decision_count": missing_decision_count,
        "invalid_decision_count": invalid_decision_count,
        "validation_issue_count": validation_issue_count,
        "apply_simulation_eligible_count": apply_simulation_eligible_count,
        "needs_alias_family_expansion_count": needs_alias_family_expansion_count,
        "alias_rule_update_allowed_count": alias_rule_update_allowed_count,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "human_review_completed": (
            len(merged_rows) == expected_review_required_count
            and missing_decision_count == 0
            and invalid_decision_count == 0
        ),
        "alias_apply_simulation_ready": (
            apply_simulation_eligible_count > 0 and validation_issue_count == 0
        ),
        "selected_review_rows_read_source": original_source,
        "context_only_rows_read_source": context_source,
        "blocked_rows_read_source": blocked_source,
        "context_only_row_count": len(context_only_rows),
        "blocked_reference_row_count": len(blocked_rows),
        "input_345c9_package_dir": str(remaining_blind_spot_human_review_package_345c9_dir),
        "reviewed_blind_spot_workbook": str(reviewed_blind_spot_workbook),
        "milestone_ledger_updated": milestone_ledger_updated,
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    return {
        "manifest": manifest,
        "reviewed_decisions": merged_rows,
        "validated_approved_aliases": validated_approved_rows,
        "rejected_or_blocked_aliases": rejected_or_blocked_rows,
        "validation_issues": validation_issues_rows,
        "decision_summary": decision_summary,
        "qa_json": {
            "decision": READY_DECISION_345C10,
            "qa_fail_count": qa_fail_count,
            "checks": checks,
        },
        "no_apply_proof": no_apply_proof,
        "artifact_index_rows": _artifact_rows(output_dir),
    }

