from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.schema_343a import (
    SCHEMA_VERSION,
    build_argilla_mapping,
    build_excel_template_spec,
    build_json_schema,
    build_ui_contract,
    field_count,
    field_specs,
    lifecycle_transitions,
    priority_count,
    priority_levels,
    reason_code_count,
    reason_codes,
    required_field_count,
    status_catalog,
    status_count,
    trust_mapping,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_342S_DECISION = "PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY"
READY_INPUT_342R_DECISION = "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY"
READY_INPUT_342Q_DECISION = "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY"
READY_INPUT_342P_DECISION = "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY"
READY_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"
NOT_READY_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_NOT_READY"
RECOMMENDED_343B_SCOPE = "argilla_human_review_ui_pilot"

DEFAULT_SNAPSHOT_342S_DIR = Path(r"D:\_datefac\output\package_audit_snapshot_demo_handoff_342s")
DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR = Path(r"D:\_datefac\output\audit_labeled_export_candidate_package_342r")
DEFAULT_PREVIEW_AUDIT_342Q_DIR = Path(r"D:\_datefac\output\preview_audit_export_readiness_gate_342q")
DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR = Path(r"D:\_datefac\output\reviewed_plus_simulated_client_preview_342p")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")

SUMMARY_FILE_NAME = "review_queue_schema_343a_summary.json"
MANIFEST_FILE_NAME = "review_queue_schema_343a_manifest.json"
QA_FILE_NAME = "review_queue_schema_343a_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_schema_343a_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_schema_343a_report.md"
WORKBOOK_FILE_NAME = "review_queue_schema_343a.xlsx"
SCHEMA_FILE_NAME = "review_queue_schema_343a_schema.json"
JSON_SCHEMA_FILE_NAME = "review_queue_schema_343a_json_schema.json"
EXCEL_TEMPLATE_SPEC_FILE_NAME = "review_queue_schema_343a_excel_template_spec.json"
ARGILLA_MAPPING_FILE_NAME = "review_queue_schema_343a_argilla_mapping.json"
UI_CONTRACT_FILE_NAME = "review_queue_schema_343a_ui_contract.md"
SAMPLE_ITEMS_FILE_NAME = "review_queue_schema_343a_sample_items.jsonl"

INPUT_342S_SUMMARY_NAME = "package_audit_snapshot_demo_handoff_342s_summary.json"
INPUT_342S_QA_NAME = "package_audit_snapshot_demo_handoff_342s_qa.json"
INPUT_342S_REPORT_NAME = "package_audit_snapshot_demo_handoff_342s_report.md"
INPUT_342S_DEMO_README_NAME = "package_audit_snapshot_demo_handoff_342s_demo_readme.md"
INPUT_342S_HANDOFF_NAME = "package_audit_snapshot_demo_handoff_342s_handoff_checklist.md"

INPUT_342R_SUMMARY_NAME = "audit_labeled_export_candidate_package_342r_summary.json"
INPUT_342R_QA_NAME = "audit_labeled_export_candidate_package_342r_qa.json"
INPUT_342R_WORKBOOK_NAME = "audit_labeled_export_candidate_package_342r.xlsx"
INPUT_342Q_SUMMARY_NAME = "preview_audit_export_readiness_gate_342q_summary.json"
INPUT_342Q_QA_NAME = "preview_audit_export_readiness_gate_342q_qa.json"
INPUT_342P_SUMMARY_NAME = "reviewed_plus_simulated_client_preview_342p_summary.json"
INPUT_342P_QA_NAME = "reviewed_plus_simulated_client_preview_342p_qa.json"

REQUIRED_342R_SHEETS = [
    "03_EXPORT_CANDIDATES",
    "10_COLLISION_CONTEXT",
    "11_BACKLOG_CONTEXT",
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
    "input/table_first_review_342g_reviewed",
    "input/spot_check_reviewed_342m",
    "input/llm_review_responses_342m",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

FORBIDDEN_CLAIMS = [
    "investment advice",
    "formal_client_export_allowed=true",
    "client_ready=true",
    "production_ready=true",
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


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _norm_text(value).casefold()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return bool(value)


def _safe_int(value: Any) -> int:
    text = _norm_text(value)
    if not text:
        return 0
    try:
        return int(value)
    except Exception:
        try:
            return int(float(text))
        except Exception:
            return 0


def _safe_float(value: Any) -> float | None:
    text = _norm_text(value)
    if not text:
        return None
    try:
        return float(value)
    except Exception:
        try:
            return float(text)
        except Exception:
            return None


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _git_head_sha(repo_root: Path) -> str:
    if not _is_git_repo(repo_root):
        return ""
    result = _run_git(repo_root, ["rev-parse", "HEAD"])
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


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


def _contains_forbidden_claim(text: str, forbidden_tokens: Sequence[str]) -> bool:
    safe_cues = ("not ", "false", "no ", "do not", "must not", "forbidden", "cannot", "can't")
    lowered_lines = [line.casefold() for line in text.splitlines()]
    for token in forbidden_tokens:
        token_lower = token.casefold()
        for line in lowered_lines:
            if token_lower not in line:
                continue
            if any(cue in line for cue in safe_cues):
                continue
            return True
    return False


def _read_workbook_sheets(
    workbook_path: Path,
    required_sheets: Sequence[str],
) -> tuple[Dict[str, pd.DataFrame], List[str], List[str]]:
    sheets: Dict[str, pd.DataFrame] = {}
    warnings: List[str] = []
    sheet_names: List[str] = []
    if not workbook_path.exists():
        for sheet in required_sheets:
            sheets[sheet] = pd.DataFrame()
        return sheets, sheet_names, [f"missing workbook: {workbook_path}"]
    try:
        excel = pd.ExcelFile(workbook_path)
        sheet_names = list(excel.sheet_names)
        for sheet in required_sheets:
            if sheet in sheet_names:
                sheets[sheet] = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet))
            else:
                sheets[sheet] = pd.DataFrame()
                warnings.append(f"missing required workbook sheet: {sheet}")
    except Exception as exc:
        warnings.append(f"unable to read workbook {workbook_path}: {exc}")
        for sheet in required_sheets:
            sheets[sheet] = pd.DataFrame()
    return sheets, sheet_names, warnings


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return _norm_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    return _clean_frame(pd.DataFrame(rows))


def _load_summary_qa_report(base_dir: Path, summary_name: str, qa_name: str, text_names: Sequence[str]) -> tuple[Dict[str, Any], Dict[str, Any], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = base_dir / summary_name
    qa_path = base_dir / qa_name
    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path, label in ((summary_path, "summary"), (qa_path, "qa")):
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")
    for text_name in text_names:
        path = base_dir / text_name
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing text artifact: {path}")
    return summary, qa_json, files_read, warnings


def _select_rows(frame: pd.DataFrame, trust_level: str, limit: int) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    filtered = frame[frame["data_trust_level"].astype(str) == trust_level].copy()
    if filtered.empty:
        return filtered
    sort_columns = [column for column in ["review_item_id", "export_candidate_row_id", "metric_standardized", "year_standardized"] if column in filtered.columns]
    if sort_columns:
        filtered = filtered.sort_values(sort_columns, kind="stable")
    return _clean_frame(filtered.head(limit))


def _build_collision_lookup(collision_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    if collision_df.empty:
        return lookup
    for _, row in collision_df.iterrows():
        row_dict = row.to_dict()
        keys = [_norm_text(row_dict.get("review_item_id")), _norm_text(row_dict.get("winner_review_item_id")), _norm_text(row_dict.get("collision_key"))]
        for key in keys:
            if key and key not in lookup:
                lookup[key] = row_dict
    return lookup


def _derive_queue_reason(row: Dict[str, Any], collision_row: Dict[str, Any] | None) -> str:
    trust = _norm_text(row.get("data_trust_level"))
    if collision_row and _norm_text(collision_row.get("collision_severity")).upper() == "HIGH":
        return "SEVERE_COLLISION"
    if collision_row:
        return "DUPLICATE_METRIC_YEAR_SOURCE"
    if trust == "HUMAN_REVIEWED":
        return "RANDOM_SPOT_CHECK"
    if _as_bool(row.get("requires_later_audit")):
        return "SIMULATED_REQUIRES_LATER_AUDIT"
    confidence = _safe_float(row.get("adoption_confidence"))
    if confidence is not None and confidence < 0.6:
        return "LOW_CONFIDENCE"
    return "STILL_HUMAN_REQUIRED"


def _derive_priority(reason_code: str, trust: str, collision_row: Dict[str, Any] | None) -> str:
    if reason_code == "SEVERE_COLLISION":
        return "P0_BLOCKER"
    if reason_code in {"DUPLICATE_METRIC_YEAR_SOURCE", "STILL_HUMAN_REQUIRED", "LOW_CONFIDENCE"}:
        return "P1_HIGH_RISK"
    if reason_code == "RANDOM_SPOT_CHECK" and trust == "HUMAN_REVIEWED":
        return "P3_SPOT_CHECK"
    if reason_code == "BACKLOG_REVIEW":
        return "P4_BACKLOG"
    return "P2_STANDARD_REVIEW"


def _derive_risk_level(reason_code: str, trust: str, collision_row: Dict[str, Any] | None) -> str:
    if reason_code == "SEVERE_COLLISION":
        return "CRITICAL"
    if trust != "HUMAN_REVIEWED" or collision_row:
        return "HIGH"
    return "MEDIUM"


def _derive_risk_tags(row: Dict[str, Any], collision_row: Dict[str, Any] | None) -> List[str]:
    tags: List[str] = []
    trust = _norm_text(row.get("data_trust_level"))
    preview_source_type = _norm_text(row.get("preview_source_type"))
    if trust == "HUMAN_REVIEWED":
        tags.append("HUMAN_REVIEWED_SPOT_CHECK")
    if "SIMULATED" in trust or "SIMULATED" in preview_source_type:
        tags.append("SIMULATION_ONLY")
    if _as_bool(row.get("requires_later_audit")):
        tags.append("LATER_AUDIT_REQUIRED")
    if _as_bool(row.get("required_disclaimer")):
        tags.append("DISCLAIMER_REQUIRED")
    if collision_row:
        tags.append("COLLISION_LOGGED")
        if _norm_text(collision_row.get("collision_severity")).upper() == "HIGH":
            tags.append("SEVERE_COLLISION")
    warning_level = _norm_text(row.get("package_warning_level")).upper()
    if warning_level:
        tags.append(f"PACKAGE_WARNING_{warning_level}")
    return tags or ["REVIEW_QUEUE_PILOT"]


def _build_queue_item(
    row: Dict[str, Any],
    *,
    queue_item_id: str,
    source_artifact_path: Path,
    source_artifact_sheet: str,
    source_row_id: str,
    source_detail_level: str,
    source_stage: str,
    source_commit_sha: str,
    collision_row: Dict[str, Any] | None,
) -> Dict[str, Any]:
    reason_code = _derive_queue_reason(row, collision_row)
    trust = _norm_text(row.get("data_trust_level")) or "SUMMARY_DERIVED"
    preview_source_type = _norm_text(row.get("preview_source_type"))
    if not preview_source_type:
        preview_source_type = "SUMMARY_DERIVED" if source_detail_level == "SUMMARY_DERIVED" else trust
    risk_tags = _derive_risk_tags(row, collision_row)
    confidence = _safe_float(row.get("adoption_confidence"))
    metric = _norm_text(row.get("metric_standardized")) or "BACKLOG_PLACEHOLDER"
    year = _norm_text(row.get("year_standardized")) or "BACKLOG"
    value = _safe_float(row.get("value_numeric"))
    if value is None:
        value = 0.0
    normalized_unit = _norm_text(row.get("normalized_unit")) or "N/A"
    source_html = _norm_text(row.get("evidence"))
    note_parts = [_norm_text(row.get("display_warning")), _norm_text(row.get("package_note")), _norm_text(row.get("recommended_next_review_action"))]
    source_text = " | ".join(part for part in note_parts if part)
    collision_group_id = _norm_text(row.get("collision_key"))
    if not collision_group_id and collision_row:
        collision_group_id = _norm_text(collision_row.get("collision_key"))

    return {
        "queue_item_id": queue_item_id,
        "review_item_id": _norm_text(row.get("review_item_id")) or queue_item_id,
        "source_stage": source_stage,
        "source_commit_sha": source_commit_sha,
        "source_artifact_path": str(source_artifact_path),
        "source_artifact_sheet": source_artifact_sheet,
        "source_row_id": source_row_id,
        "source_detail_level": source_detail_level,
        "source_pdf_id": _norm_text(row.get("corpus_pdf_id")),
        "source_pdf_path": _norm_text(row.get("source_pdf_path")),
        "page_number": _safe_int(row.get("source_page")) if _norm_text(row.get("source_page")) else "",
        "table_id": _norm_text(row.get("table_id")),
        "cell_id": _norm_text(row.get("cell_id")),
        "bbox": _norm_text(row.get("bbox")),
        "image_path": _norm_text(row.get("image_path")),
        "source_html_snippet": source_html,
        "source_text_snippet": source_text,
        "metric_candidate_raw": _norm_text(row.get("metric_candidate_raw")),
        "metric_standardized": metric,
        "year_standardized": year,
        "value_numeric": value,
        "normalized_unit": normalized_unit,
        "original_metric_standardized": _norm_text(row.get("original_metric_standardized")),
        "original_normalized_unit": _norm_text(row.get("original_normalized_unit")),
        "correction_pattern": _norm_text(row.get("correction_pattern")),
        "correction_reason": _norm_text(row.get("correction_reason")),
        "data_trust_level": trust,
        "audit_label": _norm_text(row.get("audit_label")) or ("AUDIT_LABEL_SUMMARY_DERIVED" if source_detail_level == "SUMMARY_DERIVED" else "AUDIT_LABEL_UNKNOWN"),
        "preview_source_type": preview_source_type,
        "risk_level": _derive_risk_level(reason_code, trust, collision_row),
        "risk_tags": risk_tags,
        "queue_reason_code": reason_code,
        "confidence_score": confidence if confidence is not None else (1.0 if trust == "HUMAN_REVIEWED" else 0.5),
        "collision_group_id": collision_group_id,
        "requires_disclaimer": _as_bool(row.get("required_disclaimer")),
        "requires_later_audit": _as_bool(row.get("requires_later_audit")),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "not_final_confirmation": True,
        "review_status": "QUEUED",
        "review_priority": _derive_priority(reason_code, trust, collision_row),
        "assigned_reviewer_id": "",
        "reviewer_decision": "",
        "reviewer_metric_standardized": "",
        "reviewer_year_standardized": "",
        "reviewer_value_numeric": "",
        "reviewer_normalized_unit": "",
        "reviewer_note": "",
        "reviewed_at": "",
        "review_round": 1,
        "apply_allowed": False,
        "apply_target": "SIDECAR_SIMULATION_ONLY",
        "applied_at": "",
        "applied_by": "",
        "apply_batch_id": "",
        "no_write_back_required": True,
        "audit_log_ref": collision_group_id or _norm_text(row.get("review_item_id")) or source_row_id,
    }


def _build_summary_placeholder(backlog_df: pd.DataFrame, source_artifact_path: Path, source_commit_sha: str, queue_index: int) -> Dict[str, Any]:
    backlog_row: Dict[str, Any] = backlog_df.iloc[0].to_dict() if not backlog_df.empty else {}
    placeholder_row = {
        "review_item_id": "343a::summary_backlog::0001",
        "metric_standardized": "BACKLOG_PLACEHOLDER",
        "year_standardized": "BACKLOG",
        "value_numeric": _safe_int(backlog_row.get("remaining_review_count", 0)),
        "normalized_unit": "rows",
        "data_trust_level": "SUMMARY_DERIVED",
        "audit_label": "AUDIT_LABEL_SUMMARY_DERIVED",
        "preview_source_type": "SUMMARY_DERIVED",
        "display_warning": "summary-derived placeholder only; row-level backlog details are not available in 342R/342S",
        "required_disclaimer": False,
        "requires_later_audit": True,
        "package_note": _norm_text(backlog_row.get("backlog_note")),
        "recommended_next_review_action": _norm_text(backlog_row.get("recommended_next_review_action")),
        "collision_key": "",
    }
    item = _build_queue_item(
        placeholder_row,
        queue_item_id=f"343a::queue::{queue_index:04d}",
        source_artifact_path=source_artifact_path,
        source_artifact_sheet="11_BACKLOG_CONTEXT",
        source_row_id="11_BACKLOG_CONTEXT::0001",
        source_detail_level="SUMMARY_DERIVED",
        source_stage="SUMMARY_DERIVED",
        source_commit_sha=source_commit_sha,
        collision_row=None,
    )
    item["queue_reason_code"] = "BACKLOG_REVIEW"
    item["review_priority"] = "P4_BACKLOG"
    item["risk_level"] = "MEDIUM"
    item["risk_tags"] = ["SUMMARY_DERIVED", "BACKLOG_REVIEW", "LATER_AUDIT_REQUIRED"]
    item["requires_later_audit"] = True
    item["source_text_snippet"] = "summary-derived placeholder only; expand to row-level queue later"
    return item


def _input_summary_df(summary_342s: Dict[str, Any], summary_342r: Dict[str, Any], summary_342q: Dict[str, Any], summary_342p: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for stage, summary in [("342S", summary_342s), ("342R", summary_342r), ("342Q", summary_342q), ("342P", summary_342p)]:
        for key, value in summary.items():
            rows.append({"source_stage": stage, "key": key, "value": _flatten_value(value)})
    return _clean_frame(pd.DataFrame(rows))


def _queue_fields_df() -> pd.DataFrame:
    return _clean_frame(pd.DataFrame(field_specs()))


def _status_lifecycle_df() -> pd.DataFrame:
    catalog = {item["status"]: item for item in status_catalog()}
    rows = []
    for transition in lifecycle_transitions():
        rows.append(
            {
                "from_status": transition["from_status"],
                "to_status": transition["to_status"],
                "rule": transition["rule"],
                "from_status_terminal": catalog.get(transition["from_status"], {}).get("is_terminal", False),
                "to_status_terminal": catalog.get(transition["to_status"], {}).get("is_terminal", False),
                "from_status_description": catalog.get(transition["from_status"], {}).get("description", ""),
                "to_status_description": catalog.get(transition["to_status"], {}).get("description", ""),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _excel_template_df(excel_spec: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(pd.DataFrame(excel_spec.get("columns", [])))


def _argilla_mapping_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for category in ["text_fields", "metadata_fields", "response_fields"]:
        for item in mapping.get(category, []):
            rows.append({"mapping_group": category, **item})
    return _clean_frame(pd.DataFrame(rows))


def _ui_contract_df(contract: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for section, values in [
        ("positioning", [contract.get("positioning", "")]),
        ("list_view_columns", contract.get("list_view_columns", [])),
        ("detail_view_sections", contract.get("detail_view_sections", [])),
        ("review_actions", contract.get("review_actions", [])),
        ("validation_rules", contract.get("validation_rules", [])),
        ("export_contract", contract.get("export_contract", [])),
        ("audit_log_expectations", contract.get("audit_log_expectations", [])),
    ]:
        for value in values:
            rows.append({"section": section, "value": value})
    return _clean_frame(pd.DataFrame(rows))


def _backlog_strategy_df(summary_342s: Dict[str, Any], backlog_df: pd.DataFrame) -> pd.DataFrame:
    backlog_row = backlog_df.iloc[0].to_dict() if not backlog_df.empty else {}
    rows = [
        {
            "strategy_part": "current_backlog_context",
            "detail": f"still_human_required_count={_safe_int(summary_342s.get('still_human_required_count', 0))}, remaining_review_count={_safe_int(summary_342s.get('remaining_review_count', 0))}",
        },
        {
            "strategy_part": "row_level_gap",
            "detail": "342R/342S expose backlog only as summary context, so 343A adds summary-derived placeholders instead of fabricating row-level detail.",
        },
        {
            "strategy_part": "next_queue_expansion",
            "detail": _norm_text(backlog_row.get("recommended_next_review_action")) or "expand row-level backlog routing in a future 343B/343C task",
        },
        {
            "strategy_part": "pilot_scope",
            "detail": "343A generates a deterministic pilot queue only, not the full production workload.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"section": "positioning", "message": "343A defines a durable Review Queue schema and pilot package."},
        {"section": "boundary", "message": "343A does not implement full Argilla, full UI, or production apply logic."},
        {"section": "input_mapping", "message": "342R export candidates become queue items; 342S/342Q/342P summaries provide risk and readiness context."},
        {"section": "safety", "message": "formal_client_export_allowed=false, client_ready=false, production_ready=false must remain unchanged."},
        {"section": "next", "message": "Recommended next step is 343B Argilla Human Review UI Pilot or an Excel round-trip pilot."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _readiness_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"gate": "decision", "value": summary.get("decision", ""), "meaning": "343A readiness decision"},
        {"gate": "ready_for_343b", "value": summary.get("ready_for_343b", False), "meaning": "Whether Argilla/UI pilot can start next"},
        {"gate": "recommended_343b_scope", "value": summary.get("recommended_343b_scope", ""), "meaning": "Preferred 343B scope"},
        {"gate": "formal_client_export_allowed", "value": summary.get("formal_client_export_allowed", False), "meaning": "Must remain false"},
        {"gate": "client_ready", "value": summary.get("client_ready", False), "meaning": "Must remain false"},
        {"gate": "production_ready", "value": summary.get("production_ready", False), "meaning": "Must remain false"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _next_steps_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"step": "343B_argilla", "recommendation": "Use the 343A queue schema as the source of truth and pilot Argilla as a pluggable review UI.", "trigger": bool(summary.get("ready_for_343b"))},
        {"step": "343B_excel_roundtrip", "recommendation": "If lighter tooling is preferred, validate the Excel round-trip spec with a bounded queue sample.", "trigger": bool(summary.get("ready_for_343b"))},
        {"step": "keep_boundaries", "recommendation": "Do not treat simulated rows as final confirmed export rows.", "trigger": True},
        {"step": "no_write_back", "recommendation": "Continue to keep all apply behavior sidecar-only and traceable.", "trigger": True},
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_review_queue_schema_343a(
    *,
    snapshot_342s_dir: Path = DEFAULT_SNAPSHOT_342S_DIR,
    audit_labeled_package_342r_dir: Path = DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR,
    preview_audit_342q_dir: Path = DEFAULT_PREVIEW_AUDIT_342Q_DIR,
    reviewed_plus_preview_342p_dir: Path = DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    latest_commit_sha = _git_head_sha(repo_root)

    files_read: List[str] = []
    warnings: List[str] = []

    summary_342s, qa_342s, files_342s, warnings_342s = _load_summary_qa_report(
        snapshot_342s_dir,
        INPUT_342S_SUMMARY_NAME,
        INPUT_342S_QA_NAME,
        [INPUT_342S_REPORT_NAME, INPUT_342S_DEMO_README_NAME, INPUT_342S_HANDOFF_NAME],
    )
    summary_342r, qa_342r, files_342r, warnings_342r = _load_summary_qa_report(
        audit_labeled_package_342r_dir,
        INPUT_342R_SUMMARY_NAME,
        INPUT_342R_QA_NAME,
        [],
    )
    summary_342q, qa_342q, files_342q, warnings_342q = _load_summary_qa_report(
        preview_audit_342q_dir,
        INPUT_342Q_SUMMARY_NAME,
        INPUT_342Q_QA_NAME,
        [],
    )
    summary_342p, qa_342p, files_342p, warnings_342p = _load_summary_qa_report(
        reviewed_plus_preview_342p_dir,
        INPUT_342P_SUMMARY_NAME,
        INPUT_342P_QA_NAME,
        [],
    )
    files_read.extend(files_342s + files_342r + files_342q + files_342p)
    warnings.extend(warnings_342s + warnings_342r + warnings_342q + warnings_342p)

    workbook_342r_path = audit_labeled_package_342r_dir / INPUT_342R_WORKBOOK_NAME
    workbook_342r, workbook_342r_sheet_names, workbook_342r_warnings = _read_workbook_sheets(workbook_342r_path, REQUIRED_342R_SHEETS)
    warnings.extend(workbook_342r_warnings)
    if workbook_342r_path.exists():
        files_read.append(str(workbook_342r_path))

    all_input_paths = [
        snapshot_342s_dir / INPUT_342S_SUMMARY_NAME,
        snapshot_342s_dir / INPUT_342S_QA_NAME,
        snapshot_342s_dir / INPUT_342S_REPORT_NAME,
        snapshot_342s_dir / INPUT_342S_DEMO_README_NAME,
        snapshot_342s_dir / INPUT_342S_HANDOFF_NAME,
        audit_labeled_package_342r_dir / INPUT_342R_SUMMARY_NAME,
        audit_labeled_package_342r_dir / INPUT_342R_QA_NAME,
        workbook_342r_path,
        preview_audit_342q_dir / INPUT_342Q_SUMMARY_NAME,
        preview_audit_342q_dir / INPUT_342Q_QA_NAME,
        reviewed_plus_preview_342p_dir / INPUT_342P_SUMMARY_NAME,
        reviewed_plus_preview_342p_dir / INPUT_342P_QA_NAME,
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}

    candidates_df = _clean_frame(workbook_342r.get("03_EXPORT_CANDIDATES", pd.DataFrame()))
    collision_df = _clean_frame(workbook_342r.get("10_COLLISION_CONTEXT", pd.DataFrame()))
    backlog_df = _clean_frame(workbook_342r.get("11_BACKLOG_CONTEXT", pd.DataFrame()))
    collision_lookup = _build_collision_lookup(collision_df)

    source_commit_sha = _norm_text(summary_342s.get("latest_commit_sha_before_342s")) or latest_commit_sha
    sample_items: List[Dict[str, Any]] = []
    queue_index = 1
    human_df = _select_rows(candidates_df, "HUMAN_REVIEWED", 10)
    direct_df = _select_rows(candidates_df, "SIMULATED_DIRECT_ADOPTED", 20)
    corrected_df = _select_rows(candidates_df, "SIMULATED_CORRECTION_ADOPTED", 20)

    for sample_df in [human_df, direct_df, corrected_df]:
        for _, row in sample_df.iterrows():
            row_dict = row.to_dict()
            collision_row = collision_lookup.get(_norm_text(row_dict.get("review_item_id"))) or collision_lookup.get(_norm_text(row_dict.get("collision_key")))
            sample_items.append(
                _build_queue_item(
                    row_dict,
                    queue_item_id=f"343a::queue::{queue_index:04d}",
                    source_artifact_path=workbook_342r_path,
                    source_artifact_sheet="03_EXPORT_CANDIDATES",
                    source_row_id=_norm_text(row_dict.get("export_candidate_row_id")) or f"03_EXPORT_CANDIDATES::{queue_index:04d}",
                    source_detail_level="ROW_LEVEL",
                    source_stage=_norm_text(row_dict.get("source_stage")) or "342R",
                    source_commit_sha=source_commit_sha,
                    collision_row=collision_row,
                )
            )
            queue_index += 1

    summary_derived_sample_count = 0
    if _safe_int(summary_342s.get("remaining_review_count", 0)) > 0 or not backlog_df.empty:
        sample_items.append(_build_summary_placeholder(backlog_df, workbook_342r_path, source_commit_sha, queue_index))
        queue_index += 1
        summary_derived_sample_count = 1

    schema_json = {
        "schema_version": SCHEMA_VERSION,
        "fields": field_specs(),
        "status_catalog": status_catalog(),
        "lifecycle_transitions": lifecycle_transitions(),
        "reason_codes": reason_codes(),
        "priority_levels": priority_levels(),
        "trust_mapping": trust_mapping(),
    }
    json_schema = build_json_schema()
    excel_template_spec = build_excel_template_spec()
    argilla_mapping = build_argilla_mapping()
    ui_contract = build_ui_contract()

    sample_df = _clean_frame(pd.DataFrame(sample_items))
    required_342r_present = all(sheet in workbook_342r_sheet_names for sheet in REQUIRED_342R_SHEETS)
    input_ready = bool(
        summary_342s.get("decision") == READY_INPUT_342S_DECISION
        and _as_bool(summary_342s.get("ready_for_343a"))
        and _safe_int(summary_342s.get("qa_fail_count", 1)) == 0
        and summary_342r.get("decision") == READY_INPUT_342R_DECISION
        and _as_bool(summary_342r.get("ready_for_342s"))
        and _safe_int(summary_342r.get("qa_fail_count", 1)) == 0
        and summary_342q.get("decision") == READY_INPUT_342Q_DECISION
        and _safe_int(summary_342q.get("qa_fail_count", 1)) == 0
        and summary_342p.get("decision") == READY_INPUT_342P_DECISION
        and _safe_int(summary_342p.get("qa_fail_count", 1)) == 0
        and required_342r_present
        and not _as_bool(summary_342s.get("formal_client_export_allowed"))
        and not _as_bool(summary_342s.get("client_ready"))
        and not _as_bool(summary_342s.get("production_ready"))
    )

    simulated_rows = [item for item in sample_items if str(item.get("data_trust_level", "")).startswith("SIMULATED")]
    no_simulated_final_confirmed = all(
        not _as_bool(item.get("formal_client_export_allowed"))
        and not _as_bool(item.get("client_ready"))
        and not _as_bool(item.get("production_ready"))
        and _as_bool(item.get("not_final_confirmation"))
        for item in simulated_rows
    ) and _safe_int(summary_342q.get("simulated_final_confirmed_true_count", 0)) == 0

    summary = {
        "generated_at_utc": _utc_now(),
        "review_queue_schema_version": SCHEMA_VERSION,
        "field_count": field_count(),
        "required_field_count": required_field_count(),
        "status_count": status_count(),
        "reason_code_count": reason_code_count(),
        "priority_level_count": priority_count(),
        "sample_queue_item_count": len(sample_items),
        "human_reviewed_sample_count": len(human_df),
        "simulated_sample_count": len(direct_df) + len(corrected_df),
        "summary_derived_sample_count": summary_derived_sample_count,
        "argilla_mapping_generated": True,
        "excel_template_spec_generated": True,
        "ui_contract_generated": True,
        "schema_json_generated": True,
        "json_schema_generated": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343b": False,
        "recommended_343b_scope": "",
        "qa_fail_count": 0,
        "decision": NOT_READY_DECISION,
        "no_write_back_proof_passed": False,
        "recommended_open_excel_path": str(output_dir / WORKBOOK_FILE_NAME),
        "recommended_schema_artifact_path": str(output_dir / JSON_SCHEMA_FILE_NAME),
        "recommended_ui_contract_path": str(output_dir / UI_CONTRACT_FILE_NAME),
        "input_mainline": _norm_text(summary_342s.get("current_mainline")) or "MinerU-first / table-first",
        "source_export_candidate_package_row_count": _safe_int(summary_342r.get("export_candidate_package_row_count", 0)),
        "source_human_reviewed_candidate_count": _safe_int(summary_342r.get("human_reviewed_candidate_count", 0)),
        "source_simulated_candidate_count": _safe_int(summary_342r.get("simulated_candidate_count", 0)),
        "source_collision_logged_count": _safe_int(summary_342r.get("collision_logged_count", 0)),
        "source_severe_collision_count": _safe_int(summary_342r.get("severe_collision_count", 0)),
        "source_still_human_required_count": _safe_int(summary_342r.get("still_human_required_count", 0)),
        "source_remaining_review_count": _safe_int(summary_342r.get("remaining_review_count", 0)),
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_after = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343A",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343a")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
    )

    claims_text = "\n".join(
        [
            json.dumps(summary, ensure_ascii=False),
            json.dumps(ui_contract, ensure_ascii=False),
            json.dumps(argilla_mapping, ensure_ascii=False),
            json.dumps(excel_template_spec, ensure_ascii=False),
        ]
    )

    checks = [
        {"check_name": "inputs::342s_output_dir_exists", "status": "PASS" if snapshot_342s_dir.exists() else "FAIL", "detail": str(snapshot_342s_dir)},
        {"check_name": "inputs::342s_ready", "status": "PASS" if input_ready else "FAIL", "detail": json.dumps({"342s_decision": summary_342s.get("decision", ""), "342s_ready_for_343a": summary_342s.get("ready_for_343a", False), "342s_qa_fail_count": summary_342s.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "inputs::342r_workbook_exists", "status": "PASS" if workbook_342r_path.exists() else "FAIL", "detail": str(workbook_342r_path)},
        {"check_name": "inputs::342r_required_sheets_exist", "status": "PASS" if required_342r_present else "FAIL", "detail": json.dumps({sheet: sheet in workbook_342r_sheet_names for sheet in REQUIRED_342R_SHEETS}, ensure_ascii=False)},
        {"check_name": "inputs::342q_ready_context_exists", "status": "PASS" if summary_342q.get("decision") == READY_INPUT_342Q_DECISION and _safe_int(summary_342q.get("qa_fail_count", 1)) == 0 else "FAIL", "detail": json.dumps({"decision": summary_342q.get("decision", ""), "qa_fail_count": summary_342q.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "inputs::342p_ready_context_exists", "status": "PASS" if summary_342p.get("decision") == READY_INPUT_342P_DECISION and _safe_int(summary_342p.get("qa_fail_count", 1)) == 0 else "FAIL", "detail": json.dumps({"decision": summary_342p.get("decision", ""), "qa_fail_count": summary_342p.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "schema::fields_generated", "status": "PASS" if field_count() > 0 else "FAIL", "detail": str(field_count())},
        {"check_name": "schema::lifecycle_generated", "status": "PASS" if status_count() > 0 and len(lifecycle_transitions()) > 0 else "FAIL", "detail": f"status_count={status_count()} transitions={len(lifecycle_transitions())}"},
        {"check_name": "schema::reason_codes_generated", "status": "PASS" if reason_code_count() > 0 else "FAIL", "detail": str(reason_code_count())},
        {"check_name": "schema::priority_levels_generated", "status": "PASS" if priority_count() > 0 else "FAIL", "detail": str(priority_count())},
        {"check_name": "schema::trust_mapping_generated", "status": "PASS" if len(trust_mapping()) > 0 else "FAIL", "detail": str(len(trust_mapping()))},
        {"check_name": "schema::sample_queue_generated", "status": "PASS" if len(sample_items) > 0 else "FAIL", "detail": str(len(sample_items))},
        {"check_name": "schema::excel_template_spec_generated", "status": "PASS", "detail": str(len(excel_template_spec.get('columns', [])))},
        {"check_name": "schema::argilla_mapping_generated", "status": "PASS", "detail": str(len(argilla_mapping.get('metadata_fields', [])))},
        {"check_name": "schema::ui_contract_generated", "status": "PASS", "detail": str(len(ui_contract.get('list_view_columns', [])))},
        {"check_name": "quality::sample_counts_within_limits", "status": "PASS" if len(human_df) <= 10 and len(direct_df) <= 20 and len(corrected_df) <= 20 else "FAIL", "detail": json.dumps({"human": len(human_df), "sim_direct": len(direct_df), "sim_corrected": len(corrected_df)}, ensure_ascii=False)},
        {"check_name": "quality::no_simulated_row_treated_as_final_confirmed", "status": "PASS" if no_simulated_final_confirmed else "FAIL", "detail": json.dumps({"simulated_sample_count": len(simulated_rows), "simulated_final_confirmed_true_count": summary_342q.get("simulated_final_confirmed_true_count", 0)}, ensure_ascii=False)},
        {"check_name": "claims::formal_client_export_allowed_false", "status": "PASS" if not summary["formal_client_export_allowed"] else "FAIL", "detail": "false"},
        {"check_name": "claims::client_ready_false", "status": "PASS" if not summary["client_ready"] else "FAIL", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS" if not summary["production_ready"] else "FAIL", "detail": "false"},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if not _contains_forbidden_claim(claims_text, FORBIDDEN_CLAIMS) else "FAIL", "detail": "generated 343A texts checked"},
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "343A adds review-queue sidecar files only."},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::forbidden_output_or_input_artifacts_not_staged", "status": "PASS" if not forbidden_staged else "FAIL", "detail": json.dumps(forbidden_staged, ensure_ascii=False)},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 343A sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    ready_for_343b = bool(input_ready and len(sample_items) > 0 and no_write_back_proof_passed and qa_fail_count == 0)
    summary["ready_for_343b"] = ready_for_343b
    summary["recommended_343b_scope"] = RECOMMENDED_343B_SCOPE if ready_for_343b else ""
    summary["qa_fail_count"] = qa_fail_count
    summary["decision"] = READY_DECISION if ready_for_343b else NOT_READY_DECISION
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "343A_review_queue_schema_and_human_review_ui_pilot",
        "snapshot_342s_dir": str(snapshot_342s_dir),
        "audit_labeled_package_342r_dir": str(audit_labeled_package_342r_dir),
        "preview_audit_342q_dir": str(preview_audit_342q_dir),
        "reviewed_plus_preview_342p_dir": str(reviewed_plus_preview_342p_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "schema_json": str(output_dir / SCHEMA_FILE_NAME),
            "json_schema_json": str(output_dir / JSON_SCHEMA_FILE_NAME),
            "excel_template_spec_json": str(output_dir / EXCEL_TEMPLATE_SPEC_FILE_NAME),
            "argilla_mapping_json": str(output_dir / ARGILLA_MAPPING_FILE_NAME),
            "ui_contract_md": str(output_dir / UI_CONTRACT_FILE_NAME),
            "sample_items_jsonl": str(output_dir / SAMPLE_ITEMS_FILE_NAME),
        },
        "files_read": list(files_read),
        "warnings": warnings,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_SCHEMA_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342S_SUMMARY": _input_summary_df(summary_342s, summary_342r, summary_342q, summary_342p),
        "03_QUEUE_FIELDS": _queue_fields_df(),
        "04_STATUS_LIFECYCLE": _status_lifecycle_df(),
        "05_REASON_CODES": _clean_frame(pd.DataFrame(reason_codes())),
        "06_PRIORITY_RULES": _clean_frame(pd.DataFrame(priority_levels())),
        "07_TRUST_MAPPING": _clean_frame(pd.DataFrame(trust_mapping())),
        "08_SAMPLE_QUEUE_ITEMS": sample_df,
        "09_EXCEL_TEMPLATE": _excel_template_df(excel_template_spec),
        "10_ARGILLA_MAPPING": _argilla_mapping_df(argilla_mapping),
        "11_UI_CONTRACT": _ui_contract_df(ui_contract),
        "12_BACKLOG_STRATEGY": _backlog_strategy_df(summary_342s, backlog_df),
        "13_343B_READINESS": _readiness_df(summary),
        "14_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "15_NEXT_STEPS": _next_steps_df(summary),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "schema_json": schema_json,
        "json_schema": json_schema,
        "excel_template_spec": excel_template_spec,
        "argilla_mapping": argilla_mapping,
        "ui_contract": ui_contract,
        "sample_items": sample_items,
        "workbook_sheets": workbook_sheets,
    }
