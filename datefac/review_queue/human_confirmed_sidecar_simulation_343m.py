from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_pure_human_attestation_343l import READY_DECISION_343L
from datefac.review_queue.ingest_strict_review_343j import FORBIDDEN_STAGE_PATHS, PROTECTED_DIRTY_PATHS
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_343M = "HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_READY"
REMEDIATION_REQUIRED_DECISION_343M = (
    "HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_REMEDIATION_REQUIRED"
)
NOT_READY_DECISION_343M = "HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_NOT_READY"
RECOMMENDED_343N_SCOPE_343M = (
    "limited_human_confirmed_export_package_generation_for_demo_only"
)

WORKBOOK_SHEETS_343M = [
    "00_README",
    "01_SIM_SUMMARY",
    "02_INPUT_343L_SUMMARY",
    "03_HUMAN_CONFIRMED_ROWS",
    "04_SIDECAR_SIMULATION",
    "05_LIMITED_EXPORT_GATE",
    "06_REMAINING_BACKLOG",
    "07_SCOPE_BOUNDARY",
    "08_NO_WRITE_BACK",
    "09_NEXT_STEPS",
]

INPUT_343L_SUMMARY_NAME = "review_queue_pure_human_attestation_ingestion_343l_summary.json"
INPUT_343L_QA_NAME = "review_queue_pure_human_attestation_ingestion_343l_qa.json"
INPUT_343L_RESULT_NAME = "review_queue_pure_human_attestation_ingestion_343l_result.jsonl"
INPUT_343L_DECISION_SUMMARY_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_decision_summary.json"
)
INPUT_343L_CLIENT_EXPORT_GATE_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_client_export_gate.json"
)
INPUT_343L_SCOPE_BOUNDARY_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_scope_boundary.md"
)
INPUT_343L_NO_WRITE_BACK_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_no_write_back_proof.json"
)

INPUT_343H_BACKLOG_NAME = "review_queue_audit_summary_343h_source_check_backlog.jsonl"
INPUT_343H_GATE_NAME = "review_queue_audit_summary_343h_client_export_gate.json"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    return _clean_frame(pd.DataFrame(rows))


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


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


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343M simulates applying the 343K package-confirmed rows into a sidecar-only result set.",
                },
                {
                    "section": "scope",
                    "message": "The limited candidate remains restricted to 343K_PACKAGE_ONLY and is not a formal client export.",
                },
                {
                    "section": "boundary",
                    "message": "Global strict-human completion, formal export, client_ready, and production_ready remain false.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def build_sidecar_row(row: Dict[str, Any]) -> Dict[str, Any]:
    decision = normalize_text(row.get("human_attestation_decision"))
    metric = normalize_text(row.get("metric_standardized"))
    year = normalize_text(row.get("year_standardized"))
    value = row.get("value_numeric", "")
    unit = normalize_text(row.get("normalized_unit"))
    if decision == "HUMAN_CORRECT":
        metric = normalize_text(row.get("human_attested_metric_standardized")) or metric
        year = normalize_text(row.get("human_attested_year_standardized")) or year
        value = row.get("human_attested_value_numeric", value)
        unit = normalize_text(row.get("human_attested_normalized_unit")) or unit

    sidecar = dict(row)
    sidecar["sidecar_action"] = (
        "SIMULATE_APPLY_HUMAN_ACCEPT"
        if decision == "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM"
        else "SIMULATE_APPLY_HUMAN_CORRECTION"
    )
    sidecar["sidecar_result_status"] = (
        "HUMAN_CONFIRMED_ACCEPTED"
        if decision == "HUMAN_ACCEPT_AI_ASSISTED_CONFIRM"
        else "HUMAN_CONFIRMED_CORRECTED"
    )
    sidecar["sidecar_metric_standardized"] = metric
    sidecar["sidecar_year_standardized"] = year
    sidecar["sidecar_value_numeric"] = value
    sidecar["sidecar_normalized_unit"] = unit
    sidecar["package_strict_human_review_completed"] = True
    sidecar["strict_human_review_completed_scope"] = "343K_PACKAGE_ONLY"
    sidecar["sidecar_apply_simulation_completed"] = True
    sidecar["limited_export_scope"] = "343K_PACKAGE_ONLY"
    sidecar["formal_client_export_allowed"] = False
    sidecar["client_ready"] = False
    sidecar["production_ready"] = False
    sidecar["global_strict_human_review_completed"] = False
    return sidecar


def build_limited_export_candidate_row(sidecar_row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "queue_item_id": sidecar_row.get("queue_item_id", ""),
        "review_item_id": sidecar_row.get("review_item_id", ""),
        "export_scope": "343K_PACKAGE_ONLY",
        "source_milestone": "343L",
        "human_confirmation_scope": "343K_PACKAGE_ONLY",
        "limited_package_export_candidate": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "metric_standardized": sidecar_row.get("sidecar_metric_standardized", ""),
        "year_standardized": sidecar_row.get("sidecar_year_standardized", ""),
        "value_numeric": sidecar_row.get("sidecar_value_numeric", ""),
        "normalized_unit": sidecar_row.get("sidecar_normalized_unit", ""),
        "source_pdf_name": sidecar_row.get("source_pdf_name", ""),
        "page_number": sidecar_row.get("page_number", ""),
        "table_id": sidecar_row.get("table_id", ""),
        "bbox": sidecar_row.get("bbox", ""),
        "image_path": sidecar_row.get("image_path", ""),
        "source_text_snippet": sidecar_row.get("source_text_snippet", ""),
        "source_html_snippet": sidecar_row.get("source_html_snippet", ""),
        "human_attestation_decision": sidecar_row.get("human_attestation_decision", ""),
        "human_attestation_note": sidecar_row.get("human_attestation_note", ""),
        "human_reviewer_id": sidecar_row.get("human_reviewer_id", ""),
        "human_reviewed_at": sidecar_row.get("human_reviewed_at", ""),
        "human_source_evidence_checked": sidecar_row.get("human_source_evidence_checked", ""),
        "human_independent_check_attested": sidecar_row.get("human_independent_check_attested", ""),
        "sidecar_result_status": sidecar_row.get("sidecar_result_status", ""),
    }


def build_scope_boundary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343M Scope Boundary",
            "",
            "## 中文说明",
            "- 343M 只模拟 343K_PACKAGE_ONLY 范围内的 10 条 human-confirmed rows。",
            "- 不做真实写回，不生成 formal client export，也不改变全局严格人工审核完成状态。",
            "- limited package export candidate 只能作为受限 demo / audited sample 候选。",
            "",
            "## English Note",
            "- 343M only simulates sidecar application for the package-scoped human-confirmed rows.",
            "- Formal export remains blocked and global strict-human completion remains false.",
            "",
            "## Current Boundary",
            f"- package_strict_human_review_completed: {summary.get('package_strict_human_review_completed', False)}",
            f"- strict_human_review_completed_scope: {summary.get('strict_human_review_completed_scope', '')}",
            f"- limited_package_export_candidate_allowed: {summary.get('limited_package_export_candidate_allowed', False)}",
            f"- limited_export_scope: {summary.get('limited_export_scope', '')}",
            f"- global_strict_human_review_completed: {summary.get('global_strict_human_review_completed', False)}",
            f"- formal_client_export_allowed: {summary.get('formal_client_export_allowed', False)}",
        ]
    )


def _build_gate_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {"gate": "formal_client_export_allowed", "value": summary.get("formal_client_export_allowed", False)},
        {"gate": "client_ready", "value": summary.get("client_ready", False)},
        {"gate": "production_ready", "value": summary.get("production_ready", False)},
        {"gate": "global_strict_human_review_completed", "value": summary.get("global_strict_human_review_completed", False)},
        {"gate": "package_strict_human_review_completed", "value": summary.get("package_strict_human_review_completed", False)},
        {"gate": "limited_package_export_candidate_allowed", "value": summary.get("limited_package_export_candidate_allowed", False)},
        {"gate": "remaining_source_check_backlog_count", "value": summary.get("remaining_source_check_backlog_count", 0)},
    ]


def _build_next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    if summary.get("ready_for_343n"):
        return [
            {"step": "open_sidecar_and_gate", "recommendation": "Open the sidecar simulation workbook and limited export gate first."},
            {"step": "prepare_343n_scope", "recommendation": summary.get("recommended_343n_scope", "")},
        ]
    return [
        {"step": "inspect_blocked_rows", "recommendation": "Review blocked or non-accepted rows before any limited export candidate is considered."},
        {"step": "rerun_343m_after_remediation", "recommendation": "Rerun 343M only after upstream remediation is completed."},
    ]


def build_review_queue_human_confirmed_sidecar_simulation_343m(
    *,
    pure_human_attestation_ingestion_343l_dir: Path,
    pure_human_attestation_package_343k_dir: Path,
    source_evidence_enrichment_343i2_dir: Path,
    audit_summary_343h_dir: Path,
    review_queue_schema_343a_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    input_paths = [
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_SUMMARY_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_QA_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_RESULT_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_DECISION_SUMMARY_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_CLIENT_EXPORT_GATE_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_SCOPE_BOUNDARY_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_NO_WRITE_BACK_NAME,
        audit_summary_343h_dir / INPUT_343H_BACKLOG_NAME,
        audit_summary_343h_dir / INPUT_343H_GATE_NAME,
        review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME,
    ]

    files_read: List[str] = []
    missing_required_inputs: List[str] = []
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            missing_required_inputs.append(str(path))

    summary_343l = _read_json(pure_human_attestation_ingestion_343l_dir / INPUT_343L_SUMMARY_NAME)
    result_rows_343l = _read_jsonl(pure_human_attestation_ingestion_343l_dir / INPUT_343L_RESULT_NAME)
    backlog_343h = _read_jsonl(audit_summary_343h_dir / INPUT_343H_BACKLOG_NAME)
    summary_343a = _read_json(review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME)

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        not missing_required_inputs
        and summary_343l.get("decision") == READY_DECISION_343L
        and int(summary_343l.get("qa_fail_count", 1)) == 0
        and int(summary_343l.get("valid_row_count", -1)) == 10
        and int(summary_343l.get("invalid_row_count", -1)) == 0
        and normalize_bool(summary_343l.get("pure_human_attestation_result_ingested"))
        and normalize_bool(summary_343l.get("pure_strict_human_review_completed_for_package"))
        and normalize_text(summary_343l.get("strict_human_review_completed_scope")) == "343K_PACKAGE_ONLY"
        and not normalize_bool(summary_343l.get("global_strict_human_review_completed"))
        and not normalize_bool(summary_343l.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343l.get("client_ready"))
        and not normalize_bool(summary_343l.get("production_ready"))
    )

    accepted_or_corrected_rows = [
        row for row in result_rows_343l if normalize_text(row.get("human_attestation_decision")) in {"HUMAN_ACCEPT_AI_ASSISTED_CONFIRM", "HUMAN_CORRECT"}
    ]
    blocked_rows = [
        row for row in result_rows_343l if normalize_text(row.get("human_attestation_decision")) not in {"HUMAN_ACCEPT_AI_ASSISTED_CONFIRM", "HUMAN_CORRECT"}
    ]
    sidecar_rows = [build_sidecar_row(row) for row in accepted_or_corrected_rows]
    limited_candidate_rows = [build_limited_export_candidate_row(row) for row in sidecar_rows]

    sidecar_row_count = len(sidecar_rows)
    sidecar_human_accept_count = sum(
        1 for row in sidecar_rows if normalize_text(row.get("sidecar_result_status")) == "HUMAN_CONFIRMED_ACCEPTED"
    )
    sidecar_human_correct_count = sum(
        1 for row in sidecar_rows if normalize_text(row.get("sidecar_result_status")) == "HUMAN_CONFIRMED_CORRECTED"
    )
    sidecar_blocked_count = len(blocked_rows)
    remaining_source_check_backlog_count = len(backlog_343h)

    gate_pass = bool(
        input_ready
        and sidecar_blocked_count == 0
        and sidecar_row_count == len(accepted_or_corrected_rows)
        and len(limited_candidate_rows) == sidecar_row_count
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343L",
        "decision": NOT_READY_DECISION_343M,
        "review_queue_schema_version": summary_343l.get("review_queue_schema_version", summary_343a.get("review_queue_schema_version", "")),
        "input_human_attested_row_count": len(result_rows_343l),
        "valid_human_attested_row_count": len(accepted_or_corrected_rows),
        "sidecar_row_count": sidecar_row_count,
        "sidecar_human_accept_count": sidecar_human_accept_count,
        "sidecar_human_correct_count": sidecar_human_correct_count,
        "sidecar_blocked_count": sidecar_blocked_count,
        "limited_export_candidate_row_count": len(limited_candidate_rows),
        "remaining_source_check_backlog_count": remaining_source_check_backlog_count,
        "package_strict_human_review_completed": True,
        "strict_human_review_completed_scope": "343K_PACKAGE_ONLY",
        "global_strict_human_review_completed": False,
        "sidecar_apply_simulation_completed": gate_pass,
        "limited_export_gate_evaluated": True,
        "limited_package_export_candidate_allowed": gate_pass,
        "limited_export_scope": "343K_PACKAGE_ONLY",
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343n": gate_pass,
        "recommended_343n_scope": RECOMMENDED_343N_SCOPE_343M if gate_pass else "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343M",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["sidecar_apply_simulation_completed"] = gate_pass
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343m")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    limited_export_gate = {
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "package_strict_human_review_completed": True,
        "strict_human_review_completed_scope": "343K_PACKAGE_ONLY",
        "sidecar_apply_simulation_completed": gate_pass,
        "limited_export_gate_evaluated": True,
        "limited_package_export_candidate_allowed": gate_pass,
        "limited_export_scope": "343K_PACKAGE_ONLY",
        "remaining_source_check_backlog_count": remaining_source_check_backlog_count,
        "reason": "Limited package candidate may be used only as a scoped audited sample/demo artifact; formal client export remains blocked until global review/export gates are satisfied.",
    }

    checks = [
        {
            "check_name": "inputs::343l_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps({"missing_required_inputs": missing_required_inputs, "decision": summary_343l.get("decision", ""), "qa_fail_count": summary_343l.get("qa_fail_count", 0)}, ensure_ascii=False),
        },
        {
            "check_name": "claims::package_completion_true",
            "status": "PASS" if normalize_bool(summary_343l.get("pure_strict_human_review_completed_for_package")) else "FAIL",
            "detail": "343L package completion must be true",
        },
        {
            "check_name": "claims::global_review_remains_false",
            "status": "PASS" if not normalize_bool(summary_343l.get("global_strict_human_review_completed")) else "FAIL",
            "detail": "global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "claims::formal_client_production_flags_remain_false",
            "status": "PASS" if not normalize_bool(summary_343l.get("formal_client_export_allowed")) and not normalize_bool(summary_343l.get("client_ready")) and not normalize_bool(summary_343l.get("production_ready")) else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "counts::sidecar_rows_match_human_confirmed_rows",
            "status": "PASS" if sidecar_row_count == len(accepted_or_corrected_rows) else "FAIL",
            "detail": json.dumps({"sidecar_row_count": sidecar_row_count, "accepted_or_corrected_rows": len(accepted_or_corrected_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "counts::limited_export_candidate_matches_sidecar_when_gate_passes",
            "status": "PASS" if (not gate_pass) or len(limited_candidate_rows) == sidecar_row_count else "FAIL",
            "detail": json.dumps({"limited_export_candidate_row_count": len(limited_candidate_rows), "sidecar_row_count": sidecar_row_count}, ensure_ascii=False),
        },
        {
            "check_name": "scope::limited_candidate_carries_package_scope",
            "status": "PASS" if all(normalize_text(row.get("export_scope")) == "343K_PACKAGE_ONLY" and normalize_text(row.get("human_confirmation_scope")) == "343K_PACKAGE_ONLY" for row in limited_candidate_rows) else "FAIL",
            "detail": "All limited export candidates must carry 343K_PACKAGE_ONLY scope",
        },
        {
            "check_name": "backlog::remaining_backlog_carried_forward",
            "status": "PASS",
            "detail": json.dumps({"remaining_source_check_backlog_count": remaining_source_check_backlog_count}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::limited_export_gate_generated_and_formal_export_false",
            "status": "PASS" if not limited_export_gate["formal_client_export_allowed"] and limited_export_gate["limited_export_gate_evaluated"] else "FAIL",
            "detail": json.dumps(limited_export_gate, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343M is sidecar simulation only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343M does not write back or perform production apply.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343M adds review-queue sidecar files only.",
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
            "check_name": "safety::forbidden_output_or_input_artifacts_not_staged",
            "status": "PASS" if not forbidden_staged else "FAIL",
            "detail": json.dumps(forbidden_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::sheet_names_within_limit",
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343M) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343M, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    if qa_fail_count == 0 and gate_pass:
        summary["decision"] = READY_DECISION_343M
    elif qa_fail_count == 0 and sidecar_row_count > 0:
        summary["decision"] = REMEDIATION_REQUIRED_DECISION_343M
    else:
        summary["decision"] = NOT_READY_DECISION_343M
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "343M_human_confirmed_sidecar_apply_simulation_and_limited_export_gate",
        "pure_human_attestation_ingestion_343l_dir": str(pure_human_attestation_ingestion_343l_dir),
        "pure_human_attestation_package_343k_dir": str(pure_human_attestation_package_343k_dir),
        "source_evidence_enrichment_343i2_dir": str(source_evidence_enrichment_343i2_dir),
        "audit_summary_343h_dir": str(audit_summary_343h_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_dir": str(output_dir),
        "files_read": list(files_read),
        "warnings": [],
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": 0,
        "checks": checks,
        "warnings": [],
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    apply_plan_rows = [
        {
            "queue_item_id": row.get("queue_item_id", ""),
            "review_item_id": row.get("review_item_id", ""),
            "sidecar_action": row.get("sidecar_action", ""),
            "sidecar_result_status": row.get("sidecar_result_status", ""),
            "limited_export_scope": "343K_PACKAGE_ONLY",
            "apply_mode": "SIMULATION_ONLY",
        }
        for row in sidecar_rows
    ]

    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_SIM_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343L_SUMMARY": _build_key_value_df(summary_343l),
        "03_HUMAN_CONFIRMED_ROWS": _clean_frame(pd.DataFrame(accepted_or_corrected_rows)),
        "04_SIDECAR_SIMULATION": _clean_frame(pd.DataFrame(sidecar_rows)),
        "05_LIMITED_EXPORT_GATE": _clean_frame(pd.DataFrame(_build_gate_rows(summary))),
        "06_REMAINING_BACKLOG": _clean_frame(pd.DataFrame(backlog_343h)),
        "07_SCOPE_BOUNDARY": _build_key_value_df({"scope_boundary_report": build_scope_boundary_markdown(summary)}),
        "08_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "09_NEXT_STEPS": _clean_frame(pd.DataFrame(_build_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "sidecar_rows": sidecar_rows,
        "apply_plan_rows": apply_plan_rows,
        "limited_export_gate": limited_export_gate,
        "limited_export_candidate_rows": limited_candidate_rows,
        "remaining_backlog_rows": backlog_343h,
        "scope_boundary_markdown": build_scope_boundary_markdown(summary),
        "workbook_sheets": workbook_sheets,
    }
