from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.expanded_demo_audit_snapshot_344e import (
    ARTIFACT_INDEX_JSON_FILE_NAME as INPUT_344E_ARTIFACT_INDEX_JSON_NAME,
    DEFAULT_OUTPUT_DIR as DEFAULT_EXPANDED_DEMO_AUDIT_SNAPSHOT_344E_DIR,
    FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME as INPUT_344E_FINAL_GATE_NAME,
    READY_DECISION_344E,
    SUMMARY_FILE_NAME as INPUT_344E_SUMMARY_NAME,
)
from datefac.review_queue.ingest_strict_review_343j import (
    FORBIDDEN_STAGE_PATHS,
    PROTECTED_DIRTY_PATHS,
)
from datefac.review_queue.strict_human_review_package_344f import (
    ARTIFACT_INDEX_FILE_NAME,
    DEFAULT_OUTPUT_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    EXPORT_USAGE_344F,
    FINAL_GATE_SNAPSHOT_FILE_NAME,
    INPUT_STAGE_344F,
    MANIFEST_FILE_NAME,
    NOT_READY_DECISION_344F,
    READY_DECISION_344F,
    REVIEW_ROW_FIELDS_344F,
    REVIEW_ROWS_CSV_FILE_NAME,
    REVIEW_ROWS_JSON_FILE_NAME,
    REVIEWER_CHECKLIST_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344F,
    build_checklist_rules,
    build_evidence_context_rows,
    build_field_mapping,
    build_output_artifact_rows,
    build_review_rows,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


INPUT_344D_EXPORT_ROWS_JSONL_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
        )
    )


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


def _require_existing(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


def _artifact_index_row_map(rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        name = normalize_text(row.get("artifact_name"))
        if name:
            mapped[name] = row
    return mapped


def _locate_export_rows_path(
    expanded_demo_audit_snapshot_344e_dir: Path,
    artifact_index_rows: List[Dict[str, Any]],
) -> Path:
    artifact_map = _artifact_index_row_map(artifact_index_rows)
    export_row_entry = artifact_map.get("344D export rows")
    if export_row_entry:
        return _require_existing(Path(normalize_text(export_row_entry.get("path"))))
    fallback = (
        expanded_demo_audit_snapshot_344e_dir.parent
        / "review_queue_expanded_trusted_demo_export_package_344d"
        / INPUT_344D_EXPORT_ROWS_JSONL_NAME
    )
    return _require_existing(fallback)


def _build_readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "344F builds a strict human review package for all 29 expanded trusted demo rows.",
                },
                {
                    "section": "input_stage",
                    "message": summary.get("input_stage", ""),
                },
                {
                    "section": "boundary",
                    "message": "344F prepares human review only and does not enable formal client export.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _build_summary_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {"key": "decision", "value": summary.get("decision", "")},
        {"key": "input_stage", "value": summary.get("input_stage", "")},
        {
            "key": "input_expanded_export_row_count",
            "value": summary.get("input_expanded_export_row_count", 0),
        },
        {"key": "strict_review_row_count", "value": summary.get("strict_review_row_count", 0)},
        {
            "key": "prior_demo_trusted_row_count",
            "value": summary.get("prior_demo_trusted_row_count", 0),
        },
        {
            "key": "source_check_trusted_row_count",
            "value": summary.get("source_check_trusted_row_count", 0),
        },
        {
            "key": "source_check_confirmed_row_count",
            "value": summary.get("source_check_confirmed_row_count", 0),
        },
        {"key": "corrected_row_count", "value": summary.get("corrected_row_count", 0)},
        {"key": "export_usage", "value": summary.get("export_usage", "")},
        {
            "key": "strict_human_review_package_generated",
            "value": summary.get("strict_human_review_package_generated", False),
        },
    ]


def _build_next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "step": "Human reviewer fills strict review decision columns only.",
            "detail": "Do not edit metric, source, or evidence locator fields.",
        },
        {
            "step": "Run 344G strict human review ingestion later.",
            "detail": "344F itself does not ingest any completed review workbook.",
        },
        {
            "step": "Run 344H strict reviewed final gate snapshot later.",
            "detail": "Formal client export must remain blocked until later gate evaluation.",
        },
        {
            "step": "Keep current boundary flags false.",
            "detail": f"formal_client_export_allowed={summary.get('formal_client_export_allowed', False)}, client_ready={summary.get('client_ready', False)}, production_ready={summary.get('production_ready', False)}",
        },
    ]


def _build_final_gate_snapshot(summary: Dict[str, Any]) -> Dict[str, Any]:
    strict_review_row_count = int(summary.get("strict_review_row_count", 0))
    return {
        "strict_human_review_package_generated": bool(
            summary.get("strict_human_review_package_generated", False)
        ),
        "global_strict_human_review_completed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "expanded_review_demo_package_generated": bool(
            summary.get("expanded_review_demo_package_generated", False)
        ),
        "expanded_demo_handoff_ready": bool(summary.get("expanded_demo_handoff_ready", False)),
        "expanded_demo_audit_snapshot_generated": bool(
            summary.get("expanded_demo_audit_snapshot_generated", False)
        ),
        "strict_review_row_count": strict_review_row_count,
        "client_export_allowed_row_count": 0,
        "export_usage": EXPORT_USAGE_344F,
    }


def build_review_queue_strict_human_review_package_344f(
    *,
    expanded_demo_audit_snapshot_344e_dir: Path = DEFAULT_EXPANDED_DEMO_AUDIT_SNAPSHOT_344E_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_344e_path = _require_existing(
        expanded_demo_audit_snapshot_344e_dir / INPUT_344E_SUMMARY_NAME
    )
    artifact_index_344e_path = _require_existing(
        expanded_demo_audit_snapshot_344e_dir / INPUT_344E_ARTIFACT_INDEX_JSON_NAME
    )
    final_gate_344e_path = _require_existing(
        expanded_demo_audit_snapshot_344e_dir / INPUT_344E_FINAL_GATE_NAME
    )

    files_read: List[str] = [
        str(summary_344e_path),
        str(artifact_index_344e_path),
        str(final_gate_344e_path),
    ]

    summary_344e = _read_json(summary_344e_path)
    artifact_index_rows_344e = _read_json(artifact_index_344e_path)
    final_gate_344e = _read_json(final_gate_344e_path)
    export_rows_path = _locate_export_rows_path(
        expanded_demo_audit_snapshot_344e_dir,
        artifact_index_rows_344e,
    )
    export_rows_344d = _read_jsonl(export_rows_path)
    files_read.append(str(export_rows_path))

    input_paths = [summary_344e_path, artifact_index_344e_path, final_gate_344e_path, export_rows_path]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}

    review_rows = build_review_rows(export_rows_344d)
    evidence_context_rows = build_evidence_context_rows(export_rows_344d)
    field_mapping_rows = build_field_mapping()
    checklist_rule_rows = build_checklist_rules()

    prior_demo_trusted_row_count = sum(
        1 for row in export_rows_344d if normalize_text(row.get("source_lineage_stage")) == "343N_DEMO"
    )
    source_check_trusted_row_count = sum(
        1
        for row in export_rows_344d
        if normalize_text(row.get("source_lineage_stage")) == "344B_SOURCE_CHECK"
    )
    source_check_confirmed_row_count = sum(
        1 for row in export_rows_344d if normalize_text(row.get("source_check_status")) == "CONFIRMED"
    )
    corrected_row_count = sum(
        1 for row in export_rows_344d if normalize_text(row.get("source_check_status")) == "CORRECTED"
    )

    input_ready = bool(
        summary_344e.get("decision") == READY_DECISION_344E
        and int(summary_344e.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_344e.get("no_write_back_proof_passed"))
        and normalize_bool(summary_344e.get("expanded_demo_arc_closed"))
        and int(summary_344e.get("input_expanded_export_row_count", -1)) == len(export_rows_344d)
        and int(summary_344e.get("audit_label_row_count", -1)) == len(export_rows_344d)
        and not normalize_bool(final_gate_344e.get("formal_client_export_allowed"))
        and not normalize_bool(final_gate_344e.get("client_ready"))
        and not normalize_bool(final_gate_344e.get("production_ready"))
        and not normalize_bool(final_gate_344e.get("global_strict_human_review_completed"))
    )

    review_rows_shape_ok = len(review_rows) == 29 and all(
        sorted(row.keys()) == sorted(REVIEW_ROW_FIELDS_344F) for row in review_rows
    )
    review_rows_blank_ok = all(
        row["needs_strict_human_review"] is True
        and row["client_export_allowed"] is False
        and row["strict_human_review_decision"] == ""
        and row["strict_human_reviewer"] == ""
        and row["strict_human_reviewed_at"] == ""
        and row["strict_human_review_notes"] == ""
        for row in review_rows
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "decision": NOT_READY_DECISION_344F,
        "review_queue_schema_version": summary_344e.get("review_queue_schema_version", ""),
        "input_stage": INPUT_STAGE_344F,
        "input_344e_dir": str(expanded_demo_audit_snapshot_344e_dir),
        "input_expanded_export_row_count": len(export_rows_344d),
        "strict_review_row_count": len(review_rows),
        "prior_demo_trusted_row_count": prior_demo_trusted_row_count,
        "source_check_trusted_row_count": source_check_trusted_row_count,
        "source_check_confirmed_row_count": source_check_confirmed_row_count,
        "corrected_row_count": corrected_row_count,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "upstream_workbooks_unchanged": True,
        "strict_human_review_package_generated": False,
        "global_strict_human_review_completed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "export_usage": EXPORT_USAGE_344F,
        "expanded_review_demo_package_generated": bool(
            summary_344e.get("expanded_review_demo_package_generated", False)
        ),
        "expanded_demo_handoff_ready": bool(summary_344e.get("expanded_demo_handoff_ready", False)),
        "expanded_demo_audit_snapshot_generated": bool(
            summary_344e.get("expanded_demo_audit_snapshot_generated", False)
        ),
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="344F",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["strict_human_review_result_ingested"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_344f")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("strict_human_review_result_ingested", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::344e_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_344e.get("decision", ""),
                    "qa_fail_count": summary_344e.get("qa_fail_count", None),
                    "expanded_demo_arc_closed": summary_344e.get("expanded_demo_arc_closed", None),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::strict_review_row_count_is_29",
            "status": "PASS" if len(review_rows) == 29 else "FAIL",
            "detail": json.dumps({"strict_review_row_count": len(review_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "counts::source_split_is_10_plus_19",
            "status": "PASS"
            if prior_demo_trusted_row_count == 10 and source_check_trusted_row_count == 19
            else "FAIL",
            "detail": json.dumps(
                {
                    "prior_demo_trusted_row_count": prior_demo_trusted_row_count,
                    "source_check_trusted_row_count": source_check_trusted_row_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::source_check_result_split_is_10_plus_9",
            "status": "PASS"
            if source_check_confirmed_row_count == 10 and corrected_row_count == 9
            else "FAIL",
            "detail": json.dumps(
                {
                    "source_check_confirmed_row_count": source_check_confirmed_row_count,
                    "corrected_row_count": corrected_row_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "rows::review_rows_have_required_schema",
            "status": "PASS" if review_rows_shape_ok else "FAIL",
            "detail": json.dumps(REVIEW_ROW_FIELDS_344F, ensure_ascii=False),
        },
        {
            "check_name": "rows::review_rows_keep_blank_review_fields",
            "status": "PASS" if review_rows_blank_ok else "FAIL",
            "detail": "All rows must keep blank strict human review fields and client_export_allowed=false.",
        },
        {
            "check_name": "outputs::field_mapping_generated",
            "status": "PASS" if len(field_mapping_rows) >= 9 else "FAIL",
            "detail": json.dumps({"field_mapping_count": len(field_mapping_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::reviewer_checklist_contract_ready",
            "status": "PASS" if len(checklist_rule_rows) >= 7 else "FAIL",
            "detail": json.dumps({"checklist_rule_count": len(checklist_rule_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "claims::final_gate_flags_remain_false",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            and not summary["global_strict_human_review_completed"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready/global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_344F) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_344F, ensure_ascii=False),
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
    ready_state = bool(
        input_ready
        and review_rows_shape_ok
        and review_rows_blank_ok
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )

    summary["decision"] = READY_DECISION_344F if ready_state else NOT_READY_DECISION_344F
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed
    summary["upstream_workbooks_unchanged"] = upstream_unchanged
    summary["strict_human_review_package_generated"] = ready_state

    final_gate_snapshot = _build_final_gate_snapshot(summary)
    artifact_index_rows = build_output_artifact_rows(output_dir)

    manifest = {
        "decision": summary["decision"],
        "review_queue_schema_version": summary["review_queue_schema_version"],
        "input_stage": INPUT_STAGE_344F,
        "input_expanded_export_row_count": summary["input_expanded_export_row_count"],
        "strict_review_row_count": summary["strict_review_row_count"],
        "prior_demo_trusted_row_count": summary["prior_demo_trusted_row_count"],
        "source_check_trusted_row_count": summary["source_check_trusted_row_count"],
        "source_check_confirmed_row_count": summary["source_check_confirmed_row_count"],
        "corrected_row_count": summary["corrected_row_count"],
        "qa_fail_count": summary["qa_fail_count"],
        "no_write_back_proof_passed": summary["no_write_back_proof_passed"],
        "upstream_workbooks_unchanged": summary["upstream_workbooks_unchanged"],
        "strict_human_review_package_generated": summary["strict_human_review_package_generated"],
        "global_strict_human_review_completed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "export_usage": EXPORT_USAGE_344F,
        "input_344e_dir": str(expanded_demo_audit_snapshot_344e_dir),
        "output_dir": str(output_dir),
        "files_read": files_read,
        "compatibility_mapping": field_mapping_rows,
        "artifacts": {row["artifact_name"]: row["path"] for row in artifact_index_rows},
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": 0,
        "checks": checks,
        "warnings": [],
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame(_build_summary_rows(summary))),
        "02_INPUT_344E_SUMMARY": _build_key_value_df(summary_344e),
        "03_REVIEW_ROWS": _clean_frame(pd.DataFrame(review_rows)),
        "04_REVIEW_TEMPLATE": _clean_frame(pd.DataFrame(review_rows)),
        "05_EVIDENCE_CONTEXT": _clean_frame(pd.DataFrame(evidence_context_rows)),
        "06_CHECKLIST_RULES": _clean_frame(pd.DataFrame(checklist_rule_rows)),
        "07_FIELD_MAPPING": _clean_frame(pd.DataFrame(field_mapping_rows)),
        "08_FINAL_GATE": _build_key_value_df(final_gate_snapshot),
        "09_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "10_NEXT_STEPS": _clean_frame(pd.DataFrame(_build_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "review_rows": review_rows,
        "review_rows_csv_fields": REVIEW_ROW_FIELDS_344F,
        "reviewer_checklist_rules": checklist_rule_rows,
        "executive_summary": summary,
        "artifact_index_rows": artifact_index_rows,
        "final_gate_snapshot": final_gate_snapshot,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }


__all__ = [
    "ARTIFACT_INDEX_FILE_NAME",
    "DEFAULT_EXPANDED_DEMO_AUDIT_SNAPSHOT_344E_DIR",
    "DEFAULT_OUTPUT_DIR",
    "EXECUTIVE_SUMMARY_FILE_NAME",
    "FINAL_GATE_SNAPSHOT_FILE_NAME",
    "MANIFEST_FILE_NAME",
    "REVIEW_ROWS_CSV_FILE_NAME",
    "REVIEW_ROWS_JSON_FILE_NAME",
    "REVIEWER_CHECKLIST_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "build_review_queue_strict_human_review_package_344f",
]
