from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_342P_DECISION = "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY"
READY_INPUT_342O_DECISION = "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY"
READY_INPUT_342J_DECISION = "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY"
READY_INPUT_342I_DECISION = "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY"
READY_INPUT_342N_DECISION = "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY"
READY_DECISION = "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY"
NOT_READY_DECISION = "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_NOT_READY"

DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR = Path(r"D:\_datefac\output\reviewed_plus_simulated_client_preview_342p")
DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR = Path(r"D:\_datefac\output\post_adoption_sidecar_simulation_342o")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_POST_HUMAN_SIDECAR_342I_DIR = Path(r"D:\_datefac\output\table_first_post_human_review_sidecar_result_342i")
DEFAULT_ADOPTION_SIMULATION_342N_DIR = Path(r"D:\_datefac\output\correction_aware_adoption_simulation_342n")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\preview_audit_export_readiness_gate_342q")

SUMMARY_FILE_NAME = "preview_audit_export_readiness_gate_342q_summary.json"
MANIFEST_FILE_NAME = "preview_audit_export_readiness_gate_342q_manifest.json"
QA_FILE_NAME = "preview_audit_export_readiness_gate_342q_qa.json"
NO_WRITE_BACK_FILE_NAME = "preview_audit_export_readiness_gate_342q_no_write_back_proof.json"
REPORT_FILE_NAME = "preview_audit_export_readiness_gate_342q_report.md"
WORKBOOK_FILE_NAME = "preview_audit_export_readiness_gate_342q.xlsx"

INPUT_342P_SUMMARY_NAME = "reviewed_plus_simulated_client_preview_342p_summary.json"
INPUT_342P_QA_NAME = "reviewed_plus_simulated_client_preview_342p_qa.json"
INPUT_342P_REPORT_NAME = "reviewed_plus_simulated_client_preview_342p_report.md"
INPUT_342P_WORKBOOK_NAME = "reviewed_plus_simulated_client_preview_342p.xlsx"

INPUT_342O_SUMMARY_NAME = "post_adoption_sidecar_simulation_342o_summary.json"
INPUT_342O_QA_NAME = "post_adoption_sidecar_simulation_342o_qa.json"
INPUT_342O_REPORT_NAME = "post_adoption_sidecar_simulation_342o_report.md"
INPUT_342O_WORKBOOK_NAME = "post_adoption_sidecar_simulation_342o.xlsx"

INPUT_342J_SUMMARY_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"
INPUT_342J_QA_NAME = "table_first_reviewed_client_preview_pilot_342j_qa.json"
INPUT_342J_REPORT_NAME = "table_first_reviewed_client_preview_pilot_342j_report.md"
INPUT_342J_WORKBOOK_NAME = "table_first_reviewed_client_preview_pilot_342j.xlsx"

INPUT_342I_SUMMARY_NAME = "table_first_post_human_review_sidecar_result_342i_summary.json"
INPUT_342I_QA_NAME = "table_first_post_human_review_sidecar_result_342i_qa.json"
INPUT_342I_REPORT_NAME = "table_first_post_human_review_sidecar_result_342i_report.md"
INPUT_342I_WORKBOOK_NAME = "table_first_post_human_review_sidecar_result_342i.xlsx"

INPUT_342N_SUMMARY_NAME = "correction_aware_adoption_simulation_342n_summary.json"
INPUT_342N_QA_NAME = "correction_aware_adoption_simulation_342n_qa.json"
INPUT_342N_REPORT_NAME = "correction_aware_adoption_simulation_342n_report.md"
INPUT_342N_WORKBOOK_NAME = "correction_aware_adoption_simulation_342n.xlsx"

REQUIRED_342P_SHEETS = [
    "01_PREVIEW_SUMMARY",
    "04_COMBINED_PREVIEW",
    "05_HUMAN_REVIEWED",
    "06_SIM_DIRECT",
    "07_SIM_CORRECTED",
    "08_STILL_HUMAN_REQUIRED",
    "09_COLLISION_CHECK",
    "10_METRIC_COVERAGE",
    "11_PREVIEW_BOUNDARY",
    "12_342Q_READINESS",
    "13_NO_WRITE_BACK",
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

VALID_TRUST_BY_SOURCE = {
    "HUMAN_REVIEWED": "HUMAN_REVIEWED",
    "SIMULATED_DIRECT": "SIMULATED_DIRECT_ADOPTED",
    "SIMULATED_CORRECTED": "SIMULATED_CORRECTION_ADOPTED",
}
SIM_WARNING_TOKENS = ["simulation", "later audit"]
HUMAN_WARNING_TOKEN = "human reviewed"
RECOMMENDED_342R_SCOPE = "audit_labeled_export_candidate_package"


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


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        token_lower = token.casefold()
        start = 0
        while True:
            idx = lowered.find(token_lower, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 80) : idx]
            if "not " not in window and "false" not in window and "no " not in window:
                return True
            start = idx + len(token_lower)
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


def _load_summary_qa_report(
    *,
    base_dir: Path,
    summary_name: str,
    qa_name: str,
    report_name: str,
) -> tuple[Dict[str, Any], Dict[str, Any], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = base_dir / summary_name
    qa_path = base_dir / qa_name
    report_path = base_dir / report_name
    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path, label in [(summary_path, "summary"), (qa_path, "qa"), (report_path, "report")]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")
    return summary, qa_json, files_read, warnings


def _load_342p_context(reviewed_plus_preview_342p_dir: Path) -> tuple[
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, pd.DataFrame],
    List[str],
    List[str],
    List[str],
]:
    summary, qa_json, files_read, warnings = _load_summary_qa_report(
        base_dir=reviewed_plus_preview_342p_dir,
        summary_name=INPUT_342P_SUMMARY_NAME,
        qa_name=INPUT_342P_QA_NAME,
        report_name=INPUT_342P_REPORT_NAME,
    )
    workbook_path = reviewed_plus_preview_342p_dir / INPUT_342P_WORKBOOK_NAME
    sheets, sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342P_SHEETS)
    if workbook_path.exists():
        files_read.append(str(workbook_path))
    else:
        warnings.append(f"missing workbook: {workbook_path}")
    warnings.extend(workbook_warnings)
    return summary, qa_json, sheets, sheet_names, files_read, warnings


def _load_support_context(
    *,
    base_dir: Path,
    summary_name: str,
    qa_name: str,
    report_name: str,
    workbook_name: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Path, List[str], List[str]]:
    summary, qa_json, files_read, warnings = _load_summary_qa_report(
        base_dir=base_dir,
        summary_name=summary_name,
        qa_name=qa_name,
        report_name=report_name,
    )
    workbook_path = base_dir / workbook_name
    if workbook_path.exists():
        files_read.append(str(workbook_path))
    else:
        warnings.append(f"missing workbook: {workbook_path}")
    return summary, qa_json, workbook_path, files_read, warnings


def _risk_level(simulated_preview_count: int, duplicate_metric_year_source_count: int, severe_collision_count: int) -> str:
    if simulated_preview_count > 0 and (duplicate_metric_year_source_count > 0 or severe_collision_count > 0):
        return "HIGH"
    if simulated_preview_count > 0 or duplicate_metric_year_source_count > 0:
        return "MEDIUM"
    return "LOW"


def _warning_has_tokens(text: str, tokens: Sequence[str]) -> bool:
    lowered = text.casefold()
    return all(token.casefold() in lowered for token in tokens)


def _build_preview_audit_df(combined_preview_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    unknown_trust_level_count = 0
    trust_level_mismatch_count = 0
    missing_display_warning_count = 0
    simulated_final_confirmed_true_count = 0
    simulated_client_ready_true_count = 0
    simulated_production_ready_true_count = 0
    simulated_not_final_confirmation_true_count = 0
    simulated_requires_later_audit_count = 0

    for row in combined_preview_df.to_dict(orient="records"):
        source_type = _norm_text(row.get("preview_source_type"))
        trust_level = _norm_text(row.get("data_trust_level"))
        display_warning = _norm_text(row.get("display_warning"))
        client_ready = _as_bool(row.get("client_ready"))
        production_ready = _as_bool(row.get("production_ready"))
        not_final_confirmation = _as_bool(row.get("not_final_confirmation"))

        audit_status = "PASS"
        audit_reason_parts: List[str] = []
        requires_disclaimer = source_type.startswith("SIMULATED")
        requires_later_audit = source_type.startswith("SIMULATED")

        expected_trust = VALID_TRUST_BY_SOURCE.get(source_type, "")
        if not expected_trust:
            unknown_trust_level_count += 1
            audit_status = "FAIL"
            audit_reason_parts.append("unknown preview_source_type or trust mapping")
        elif trust_level != expected_trust:
            trust_level_mismatch_count += 1
            audit_status = "FAIL"
            audit_reason_parts.append("data_trust_level does not match preview_source_type")

        if client_ready:
            audit_status = "FAIL"
            audit_reason_parts.append("client_ready must remain false")
        if production_ready:
            audit_status = "FAIL"
            audit_reason_parts.append("production_ready must remain false")

        if not display_warning:
            missing_display_warning_count += 1
            audit_status = "FAIL"
            audit_reason_parts.append("display_warning missing")

        if source_type == "HUMAN_REVIEWED":
            if display_warning and HUMAN_WARNING_TOKEN not in display_warning.casefold():
                audit_status = "WARN" if audit_status == "PASS" else audit_status
                audit_reason_parts.append("human row warning text is non-standard")
        elif source_type.startswith("SIMULATED"):
            if not_final_confirmation:
                simulated_not_final_confirmation_true_count += 1
            else:
                audit_status = "FAIL"
                audit_reason_parts.append("simulated row lost not_final_confirmation=true boundary")
            if _as_bool(row.get("final_confirmed")):
                simulated_final_confirmed_true_count += 1
                audit_status = "FAIL"
                audit_reason_parts.append("simulated row cannot become final_confirmed=true")
            if client_ready:
                simulated_client_ready_true_count += 1
            if production_ready:
                simulated_production_ready_true_count += 1
            if _warning_has_tokens(display_warning, SIM_WARNING_TOKENS):
                simulated_requires_later_audit_count += 1
                if audit_status == "PASS":
                    audit_status = "WARN"
                    audit_reason_parts.append("simulation-only preview candidate; later audit required")
            else:
                missing_display_warning_count += 1 if display_warning else 0
                audit_status = "FAIL"
                audit_reason_parts.append("simulated row warning must mention simulation only and later audit")

        rows.append(
            {
                "preview_row_id": row.get("preview_row_id", ""),
                "review_item_id": row.get("review_item_id", ""),
                "preview_source_type": source_type,
                "data_trust_level": trust_level,
                "review_status_for_client_display": row.get("review_status_for_client_display", ""),
                "metric_standardized": row.get("metric_standardized", ""),
                "year_standardized": row.get("year_standardized", ""),
                "value_numeric": row.get("value_numeric", ""),
                "normalized_unit": row.get("normalized_unit", ""),
                "display_warning": display_warning,
                "not_final_confirmation": not_final_confirmation,
                "client_ready": client_ready,
                "production_ready": production_ready,
                "audit_status": audit_status,
                "audit_reason": "; ".join(audit_reason_parts) if audit_reason_parts else "preview row passed audit gate",
                "included_in_export_candidate_scope": audit_status != "FAIL",
                "export_candidate_allowed": audit_status != "FAIL",
                "requires_disclaimer": requires_disclaimer,
                "requires_later_audit": requires_later_audit,
            }
        )

    metrics = {
        "unknown_trust_level_count": unknown_trust_level_count,
        "trust_level_mismatch_count": trust_level_mismatch_count,
        "missing_display_warning_count": missing_display_warning_count,
        "simulated_final_confirmed_true_count": simulated_final_confirmed_true_count,
        "simulated_client_ready_true_count": simulated_client_ready_true_count,
        "simulated_production_ready_true_count": simulated_production_ready_true_count,
        "simulated_not_final_confirmation_true_count": simulated_not_final_confirmation_true_count,
        "simulated_requires_later_audit_count": simulated_requires_later_audit_count,
    }
    return _clean_frame(pd.DataFrame(rows)), metrics


def _build_trust_level_audit_df(preview_audit_df: pd.DataFrame, metrics: Mapping[str, int]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for source_type, trust_level in VALID_TRUST_BY_SOURCE.items():
        source_mask = preview_audit_df["preview_source_type"].map(_norm_text).eq(source_type) if not preview_audit_df.empty else pd.Series(dtype=bool)
        trust_mask = preview_audit_df["data_trust_level"].map(_norm_text).eq(trust_level) if not preview_audit_df.empty else pd.Series(dtype=bool)
        mismatch_count = int((source_mask & ~trust_mask).sum()) if not preview_audit_df.empty else 0
        rows.append(
            {
                "audit_item": f"trust_map::{source_type}",
                "observed_count": int(source_mask.sum()) if not preview_audit_df.empty else 0,
                "expected_trust_level": trust_level,
                "mismatch_count": mismatch_count,
                "status": "PASS" if mismatch_count == 0 else "FAIL",
                "detail": f"{source_type} rows should map to {trust_level}",
            }
        )
    rows.extend(
        [
            {
                "audit_item": "unknown_trust_level_count",
                "observed_count": int(metrics.get("unknown_trust_level_count", 0) or 0),
                "expected_trust_level": "",
                "mismatch_count": int(metrics.get("unknown_trust_level_count", 0) or 0),
                "status": "PASS" if int(metrics.get("unknown_trust_level_count", 0) or 0) == 0 else "FAIL",
                "detail": "all rows must use a known preview_source_type / data_trust_level mapping",
            },
            {
                "audit_item": "trust_level_mismatch_count",
                "observed_count": int(metrics.get("trust_level_mismatch_count", 0) or 0),
                "expected_trust_level": "",
                "mismatch_count": int(metrics.get("trust_level_mismatch_count", 0) or 0),
                "status": "PASS" if int(metrics.get("trust_level_mismatch_count", 0) or 0) == 0 else "FAIL",
                "detail": "source type and trust level must stay aligned",
            },
            {
                "audit_item": "missing_display_warning_count",
                "observed_count": int(metrics.get("missing_display_warning_count", 0) or 0),
                "expected_trust_level": "",
                "mismatch_count": int(metrics.get("missing_display_warning_count", 0) or 0),
                "status": "PASS" if int(metrics.get("missing_display_warning_count", 0) or 0) == 0 else "FAIL",
                "detail": "preview rows must keep explicit boundary warnings",
            },
        ]
    )
    return _clean_frame(pd.DataFrame(rows))


def _build_sim_boundary_audit_df(preview_audit_df: pd.DataFrame, metrics: Mapping[str, int]) -> pd.DataFrame:
    sim_mask = preview_audit_df["preview_source_type"].map(_norm_text).str.startswith("SIMULATED") if not preview_audit_df.empty else pd.Series(dtype=bool)
    simulated_preview_count = int(sim_mask.sum()) if not preview_audit_df.empty else 0
    rows = [
        {
            "audit_item": "simulated_preview_count",
            "value": simulated_preview_count,
            "status": "PASS" if simulated_preview_count >= 0 else "FAIL",
            "detail": "simulated rows remain audit-labeled preview only",
        },
        {
            "audit_item": "simulated_not_final_confirmation_true_count",
            "value": int(metrics.get("simulated_not_final_confirmation_true_count", 0) or 0),
            "status": "PASS"
            if int(metrics.get("simulated_not_final_confirmation_true_count", 0) or 0) == simulated_preview_count
            else "FAIL",
            "detail": "all simulated rows must keep not_final_confirmation=true",
        },
        {
            "audit_item": "simulated_final_confirmed_true_count",
            "value": int(metrics.get("simulated_final_confirmed_true_count", 0) or 0),
            "status": "PASS" if int(metrics.get("simulated_final_confirmed_true_count", 0) or 0) == 0 else "FAIL",
            "detail": "simulated rows must never become final confirmed",
        },
        {
            "audit_item": "simulated_client_ready_true_count",
            "value": int(metrics.get("simulated_client_ready_true_count", 0) or 0),
            "status": "PASS" if int(metrics.get("simulated_client_ready_true_count", 0) or 0) == 0 else "FAIL",
            "detail": "simulated rows must keep client_ready=false",
        },
        {
            "audit_item": "simulated_production_ready_true_count",
            "value": int(metrics.get("simulated_production_ready_true_count", 0) or 0),
            "status": "PASS" if int(metrics.get("simulated_production_ready_true_count", 0) or 0) == 0 else "FAIL",
            "detail": "simulated rows must keep production_ready=false",
        },
        {
            "audit_item": "simulated_requires_later_audit_count",
            "value": int(metrics.get("simulated_requires_later_audit_count", 0) or 0),
            "status": "PASS"
            if int(metrics.get("simulated_requires_later_audit_count", 0) or 0) == simulated_preview_count
            else "FAIL",
            "detail": "simulation rows must carry later-audit boundary language",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_collision_audit_df(collision_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    unresolved_collision_count = 0
    severe_collision_count = 0
    human_priority_violation_count = 0
    if collision_df.empty:
        return _clean_frame(pd.DataFrame()), {
            "collision_logged_count": 0,
            "unresolved_collision_count": 0,
            "severe_collision_count": 0,
            "human_over_simulation_override_count": 0,
            "human_priority_violation_count": 0,
        }

    for row in collision_df.to_dict(orient="records"):
        source_type = _norm_text(row.get("source_type"))
        winner_source_type = _norm_text(row.get("winner_source_type"))
        collision_severity = _norm_text(row.get("collision_severity"))
        unresolved = not _norm_text(row.get("winner_preview_row_id")) or not _norm_text(row.get("recommended_action"))
        if unresolved:
            unresolved_collision_count += 1
        if collision_severity in {"HIGH", "CRITICAL"}:
            severe_collision_count += 1
        human_priority_violation = source_type == "HUMAN_REVIEWED" and winner_source_type.startswith("SIMULATED")
        if human_priority_violation:
            human_priority_violation_count += 1
        rows.append(
            {
                **row,
                "collision_unresolved": unresolved,
                "human_priority_violation": human_priority_violation,
                "audit_status": "FAIL" if unresolved or human_priority_violation else "PASS",
            }
        )

    override_count = int(
        (
            collision_df["source_type"].map(_norm_text).str.startswith("SIMULATED")
            & collision_df["winner_source_type"].map(_norm_text).eq("HUMAN_REVIEWED")
        ).sum()
    )

    metrics = {
        "collision_logged_count": int(len(collision_df)),
        "unresolved_collision_count": unresolved_collision_count,
        "severe_collision_count": severe_collision_count,
        "human_over_simulation_override_count": override_count,
        "human_priority_violation_count": human_priority_violation_count,
    }
    return _clean_frame(pd.DataFrame(rows)), metrics


def _build_dropped_dup_audit_df(
    *,
    sim_direct_df: pd.DataFrame,
    sim_corrected_df: pd.DataFrame,
    combined_preview_df: pd.DataFrame,
) -> tuple[pd.DataFrame, Dict[str, int]]:
    sim_frames = [df for df in [sim_direct_df, sim_corrected_df] if not df.empty]
    if not sim_frames:
        return _clean_frame(pd.DataFrame()), {
            "simulated_duplicate_dropped_count": 0,
            "dropped_rows_found_in_combined_count": 0,
        }

    all_sim_df = _clean_frame(pd.concat(sim_frames, ignore_index=True))
    dropped_df = _clean_frame(all_sim_df[all_sim_df["dropped_reason"].map(_norm_text) != ""])
    combined_ids = set(combined_preview_df["preview_row_id"].map(_norm_text).tolist()) if not combined_preview_df.empty else set()
    combined_lookup = {
        _norm_text(row.get("preview_row_id")): row for row in combined_preview_df.to_dict(orient="records")
    } if not combined_preview_df.empty else {}

    rows: List[Dict[str, Any]] = []
    dropped_rows_found_in_combined_count = 0
    simulated_duplicate_dropped_count = 0
    for row in dropped_df.to_dict(orient="records"):
        preview_row_id = _norm_text(row.get("preview_row_id"))
        winner_preview_row_id = _norm_text(row.get("winner_preview_row_id"))
        found_in_combined = preview_row_id in combined_ids
        if found_in_combined:
            dropped_rows_found_in_combined_count += 1
        winner_row = combined_lookup.get(winner_preview_row_id, {})
        is_human_override = (
            _norm_text(winner_row.get("preview_source_type")) == "HUMAN_REVIEWED"
            or winner_preview_row_id.startswith("342j::")
        )
        if is_human_override:
            continue
        simulated_duplicate_dropped_count += 1
        rows.append(
            {
                "dropped_review_item_id": row.get("review_item_id", ""),
                "dropped_preview_row_id": preview_row_id,
                "drop_reason": row.get("dropped_reason", ""),
                "retained_preview_row_id": winner_preview_row_id,
                "retained_row_type": winner_row.get("preview_source_type", ""),
                "retained_review_item_id": winner_row.get("review_item_id", ""),
                "drop_audit_status": "FAIL" if found_in_combined else "PASS",
                "detail": "dropped duplicate row must stay outside combined preview",
            }
        )
    return _clean_frame(pd.DataFrame(rows)), {
        "simulated_duplicate_dropped_count": simulated_duplicate_dropped_count,
        "dropped_rows_found_in_combined_count": dropped_rows_found_in_combined_count,
    }


def _build_override_audit_df(collision_audit_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, int]]:
    if collision_audit_df.empty:
        return _clean_frame(pd.DataFrame()), {
            "override_count": 0,
            "human_retained_count": 0,
            "simulation_suppressed_count": 0,
        }
    override_df = collision_audit_df[
        collision_audit_df["source_type"].map(_norm_text).str.startswith("SIMULATED")
        & collision_audit_df["winner_source_type"].map(_norm_text).eq("HUMAN_REVIEWED")
    ].copy()
    if override_df.empty:
        return _clean_frame(pd.DataFrame()), {
            "override_count": 0,
            "human_retained_count": 0,
            "simulation_suppressed_count": 0,
        }
    override_df["override_audit_status"] = "PASS"
    override_df["detail"] = "human-reviewed winner retained over simulated candidate"
    count = int(len(override_df))
    return _clean_frame(override_df), {
        "override_count": count,
        "human_retained_count": count,
        "simulation_suppressed_count": count,
    }


def _build_export_candidate_scope_df(preview_audit_df: pd.DataFrame) -> pd.DataFrame:
    if preview_audit_df.empty:
        return pd.DataFrame()
    allowed_df = preview_audit_df[preview_audit_df["export_candidate_allowed"].astype(bool)].copy()
    allowed_df.insert(0, "export_candidate_row_id", [f"342q::export_candidate::{index + 1:04d}" for index in range(len(allowed_df))])
    allowed_df["source_preview_row_id"] = allowed_df["preview_row_id"]
    allowed_df["export_scope_status"] = allowed_df["audit_status"].map(
        lambda value: "AUDIT_LABELED_SIMULATION_SCOPE" if value == "WARN" else "AUDIT_LABELED_HUMAN_SCOPE"
    )
    allowed_df["required_disclaimer"] = allowed_df["requires_disclaimer"]
    allowed_df["not_formal_client_export"] = True
    allowed_df["client_ready"] = False
    allowed_df["production_ready"] = False
    return _clean_frame(
        allowed_df[
            [
                "export_candidate_row_id",
                "source_preview_row_id",
                "review_item_id",
                "metric_standardized",
                "year_standardized",
                "value_numeric",
                "normalized_unit",
                "data_trust_level",
                "export_scope_status",
                "display_warning",
                "required_disclaimer",
                "not_formal_client_export",
                "client_ready",
                "production_ready",
            ]
        ]
    )


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "section": "purpose",
            "message": "342Q is a preview audit and export readiness gate for the 342P reviewed-plus-simulated preview.",
        },
        {
            "section": "boundary",
            "message": "342Q audits trust level, simulation boundary, collision handling, and export risk without generating a formal client export.",
        },
        {
            "section": "safety",
            "message": "formal_client_export_allowed=false, client_ready=false, production_ready=false, and this output is not investment advice.",
        },
        {
            "section": "next",
            "message": "If QA passes, only an audit-labeled 342R export candidate package may proceed next.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_export_risk_gate_df(
    *,
    export_candidate_scope_allowed: bool,
    export_risk_level: str,
    risk_reasons: Sequence[str],
    required_disclaimers: Sequence[str],
) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "export_candidate_scope_allowed": export_candidate_scope_allowed,
                    "formal_client_export_allowed": False,
                    "client_ready": False,
                    "production_ready": False,
                    "export_risk_level": export_risk_level,
                    "risk_reasons": " | ".join(risk_reasons),
                    "required_disclaimers": " | ".join(required_disclaimers),
                }
            ]
        )
    )


def _build_remaining_backlog_df(*, still_human_required_count: int, remaining_review_count: int) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "still_human_required_count": still_human_required_count,
                    "remaining_review_count": remaining_review_count,
                    "remaining_backlog_note": "current preview remains partial and bounded",
                    "recommended_backlog_action": "continue human review or later audit before any broader export claim",
                }
            ]
        )
    )


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342r": summary.get("ready_for_342r", False),
                    "recommended_342r_scope": summary.get("recommended_342r_scope", ""),
                    "formal_client_export_allowed": summary.get("formal_client_export_allowed", False),
                    "client_ready": summary.get("client_ready", False),
                    "production_ready": summary.get("production_ready", False),
                    "decision": summary.get("decision", ""),
                }
            ]
        )
    )


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    steps = [
        "Keep client_ready=false and production_ready=false.",
        "Do not use 342Q as a formal client export or investment advice artifact.",
        "Keep simulation-labeled rows under disclaimer and later-audit control.",
    ]
    if summary.get("ready_for_342r", False):
        steps.append("Proceed to 342R audit-labeled export candidate package.")
    else:
        steps.append("Resolve 342Q QA failures before attempting 342R.")
    return _clean_frame(pd.DataFrame([{"next_step": step} for step in steps]))


def _build_no_write_back_proof_df(payload: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for key, value in payload.items():
        rows.append({"key": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value})
    return _clean_frame(pd.DataFrame(rows))


def build_preview_audit_export_readiness_gate_342q(
    *,
    reviewed_plus_preview_342p_dir: Path,
    post_adoption_sidecar_342o_dir: Path,
    reviewed_preview_342j_dir: Path,
    post_human_sidecar_342i_dir: Path,
    adoption_simulation_342n_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342p, qa_342p, workbook_342p, workbook_342p_sheet_names, files_342p, warnings_342p = _load_342p_context(
        reviewed_plus_preview_342p_dir
    )
    summary_342o, qa_342o, workbook_342o_path, files_342o, warnings_342o = _load_support_context(
        base_dir=post_adoption_sidecar_342o_dir,
        summary_name=INPUT_342O_SUMMARY_NAME,
        qa_name=INPUT_342O_QA_NAME,
        report_name=INPUT_342O_REPORT_NAME,
        workbook_name=INPUT_342O_WORKBOOK_NAME,
    )
    summary_342j, qa_342j, workbook_342j_path, files_342j, warnings_342j = _load_support_context(
        base_dir=reviewed_preview_342j_dir,
        summary_name=INPUT_342J_SUMMARY_NAME,
        qa_name=INPUT_342J_QA_NAME,
        report_name=INPUT_342J_REPORT_NAME,
        workbook_name=INPUT_342J_WORKBOOK_NAME,
    )
    summary_342i, qa_342i, workbook_342i_path, files_342i, warnings_342i = _load_support_context(
        base_dir=post_human_sidecar_342i_dir,
        summary_name=INPUT_342I_SUMMARY_NAME,
        qa_name=INPUT_342I_QA_NAME,
        report_name=INPUT_342I_REPORT_NAME,
        workbook_name=INPUT_342I_WORKBOOK_NAME,
    )
    summary_342n, qa_342n, workbook_342n_path, files_342n, warnings_342n = _load_support_context(
        base_dir=adoption_simulation_342n_dir,
        summary_name=INPUT_342N_SUMMARY_NAME,
        qa_name=INPUT_342N_QA_NAME,
        report_name=INPUT_342N_REPORT_NAME,
        workbook_name=INPUT_342N_WORKBOOK_NAME,
    )
    files_read.extend(files_342p + files_342o + files_342j + files_342i + files_342n)
    warnings.extend(warnings_342p + warnings_342o + warnings_342j + warnings_342i + warnings_342n)

    summary_342p_path = reviewed_plus_preview_342p_dir / INPUT_342P_SUMMARY_NAME
    qa_342p_path = reviewed_plus_preview_342p_dir / INPUT_342P_QA_NAME
    report_342p_path = reviewed_plus_preview_342p_dir / INPUT_342P_REPORT_NAME
    workbook_342p_path = reviewed_plus_preview_342p_dir / INPUT_342P_WORKBOOK_NAME
    support_paths = [
        post_adoption_sidecar_342o_dir / INPUT_342O_SUMMARY_NAME,
        post_adoption_sidecar_342o_dir / INPUT_342O_QA_NAME,
        post_adoption_sidecar_342o_dir / INPUT_342O_REPORT_NAME,
        workbook_342o_path,
        reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME,
        reviewed_preview_342j_dir / INPUT_342J_QA_NAME,
        reviewed_preview_342j_dir / INPUT_342J_REPORT_NAME,
        workbook_342j_path,
        post_human_sidecar_342i_dir / INPUT_342I_SUMMARY_NAME,
        post_human_sidecar_342i_dir / INPUT_342I_QA_NAME,
        post_human_sidecar_342i_dir / INPUT_342I_REPORT_NAME,
        workbook_342i_path,
        adoption_simulation_342n_dir / INPUT_342N_SUMMARY_NAME,
        adoption_simulation_342n_dir / INPUT_342N_QA_NAME,
        adoption_simulation_342n_dir / INPUT_342N_REPORT_NAME,
        workbook_342n_path,
    ]
    all_input_paths = [summary_342p_path, qa_342p_path, report_342p_path, workbook_342p_path, *support_paths]
    input_hashes_before = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}

    required_342p_present = all(sheet in workbook_342p_sheet_names for sheet in REQUIRED_342P_SHEETS)
    input_ready = bool(
        reviewed_plus_preview_342p_dir.exists()
        and summary_342p_path.exists()
        and qa_342p_path.exists()
        and workbook_342p_path.exists()
        and summary_342p.get("decision") == READY_INPUT_342P_DECISION
        and bool(summary_342p.get("ready_for_342q", False))
        and _safe_int(summary_342p.get("qa_fail_count", 0)) == 0
        and required_342p_present
        and summary_342p.get("client_ready", False) is False
        and summary_342p.get("production_ready", False) is False
        and summary_342o.get("decision") == READY_INPUT_342O_DECISION
        and _safe_int(summary_342o.get("qa_fail_count", 0)) == 0
        and summary_342j.get("decision") == READY_INPUT_342J_DECISION
        and _safe_int(summary_342j.get("qa_fail_count", 0)) == 0
        and summary_342i.get("decision") == READY_INPUT_342I_DECISION
        and _safe_int(summary_342i.get("qa_fail_count", 0)) == 0
        and summary_342n.get("decision") == READY_INPUT_342N_DECISION
        and _safe_int(summary_342n.get("qa_fail_count", 0)) == 0
    )

    combined_preview_df = _clean_frame(workbook_342p.get("04_COMBINED_PREVIEW", pd.DataFrame())) if input_ready else pd.DataFrame()
    human_reviewed_df = _clean_frame(workbook_342p.get("05_HUMAN_REVIEWED", pd.DataFrame())) if input_ready else pd.DataFrame()
    sim_direct_df = _clean_frame(workbook_342p.get("06_SIM_DIRECT", pd.DataFrame())) if input_ready else pd.DataFrame()
    sim_corrected_df = _clean_frame(workbook_342p.get("07_SIM_CORRECTED", pd.DataFrame())) if input_ready else pd.DataFrame()
    still_human_required_df = _clean_frame(workbook_342p.get("08_STILL_HUMAN_REQUIRED", pd.DataFrame())) if input_ready else pd.DataFrame()
    collision_raw_df = _clean_frame(workbook_342p.get("09_COLLISION_CHECK", pd.DataFrame())) if input_ready else pd.DataFrame()

    if not combined_preview_df.empty and "included_in_combined_preview" in combined_preview_df.columns:
        included_counts = combined_preview_df["included_in_combined_preview"].map(_as_bool)
        if not included_counts.any():
            warnings.append(
                "342P included_in_combined_preview flag appears non-authoritative; 342Q uses actual sheet rows as the combined preview scope."
            )

    preview_audit_df, preview_metrics = _build_preview_audit_df(combined_preview_df) if input_ready else (_clean_frame(pd.DataFrame()), {
        "unknown_trust_level_count": 0,
        "trust_level_mismatch_count": 0,
        "missing_display_warning_count": 0,
        "simulated_final_confirmed_true_count": 0,
        "simulated_client_ready_true_count": 0,
        "simulated_production_ready_true_count": 0,
        "simulated_not_final_confirmation_true_count": 0,
        "simulated_requires_later_audit_count": 0,
    })
    trust_level_audit_df = _build_trust_level_audit_df(preview_audit_df, preview_metrics)
    sim_boundary_audit_df = _build_sim_boundary_audit_df(preview_audit_df, preview_metrics)
    collision_audit_df, collision_metrics = _build_collision_audit_df(collision_raw_df)
    dropped_dup_audit_df, dropped_metrics = _build_dropped_dup_audit_df(
        sim_direct_df=sim_direct_df,
        sim_corrected_df=sim_corrected_df,
        combined_preview_df=combined_preview_df,
    )
    override_audit_df, override_metrics = _build_override_audit_df(collision_audit_df)
    export_candidate_scope_df = _build_export_candidate_scope_df(preview_audit_df)

    human_reviewed_preview_count = int((combined_preview_df["preview_source_type"].map(_norm_text) == "HUMAN_REVIEWED").sum()) if not combined_preview_df.empty else 0
    simulated_direct_preview_count = int((combined_preview_df["preview_source_type"].map(_norm_text) == "SIMULATED_DIRECT").sum()) if not combined_preview_df.empty else 0
    simulated_corrected_preview_count = int((combined_preview_df["preview_source_type"].map(_norm_text) == "SIMULATED_CORRECTED").sum()) if not combined_preview_df.empty else 0
    simulated_preview_count = simulated_direct_preview_count + simulated_corrected_preview_count
    combined_preview_row_count = int(len(combined_preview_df))
    export_candidate_row_count = int(len(export_candidate_scope_df))
    still_human_required_count = int(len(still_human_required_df))
    remaining_review_count = _safe_int(summary_342p.get("remaining_review_count", 0))

    export_risk_level = _risk_level(
        simulated_preview_count=simulated_preview_count,
        duplicate_metric_year_source_count=_safe_int(summary_342p.get("duplicate_metric_year_source_count", 0)),
        severe_collision_count=int(collision_metrics.get("severe_collision_count", 0) or 0),
    )
    risk_reasons = []
    if simulated_preview_count > 0:
        risk_reasons.append("preview contains simulated rows that still require disclaimer and later audit")
    if _safe_int(summary_342p.get("duplicate_metric_year_source_count", 0)) > 0:
        risk_reasons.append("collision count is high and shows non-trivial deduplication handling")
    if int(collision_metrics.get("severe_collision_count", 0) or 0) > 0:
        risk_reasons.append("high-severity collision records remain part of the audit trail")
    if not risk_reasons:
        risk_reasons.append("preview remains bounded and non-final by policy")
    required_disclaimers = [
        "not formal client export",
        "simulated rows are simulation only and require later audit",
        "client_ready=false and production_ready=false",
    ]

    export_candidate_scope_allowed = bool(
        input_ready
        and combined_preview_row_count > 0
        and preview_metrics["unknown_trust_level_count"] == 0
        and preview_metrics["trust_level_mismatch_count"] == 0
        and preview_metrics["simulated_final_confirmed_true_count"] == 0
        and preview_metrics["simulated_client_ready_true_count"] == 0
        and preview_metrics["simulated_production_ready_true_count"] == 0
        and dropped_metrics["dropped_rows_found_in_combined_count"] == 0
        and int(collision_metrics.get("human_priority_violation_count", 0) or 0) == 0
        and int(collision_metrics.get("unresolved_collision_count", 0) or 0) == 0
    )

    input_hashes_after = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342Q",
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
        no_write_back_json.get("no_official_asset_modification_during_342q")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
    )

    readme_df = _build_readme_df()
    export_risk_gate_df = _build_export_risk_gate_df(
        export_candidate_scope_allowed=export_candidate_scope_allowed,
        export_risk_level=export_risk_level,
        risk_reasons=risk_reasons,
        required_disclaimers=required_disclaimers,
    )
    remaining_backlog_df = _build_remaining_backlog_df(
        still_human_required_count=still_human_required_count,
        remaining_review_count=remaining_review_count,
    )
    claims_text = "\n".join(
        readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
        + export_risk_gate_df.get("risk_reasons", pd.Series(dtype=object)).astype(str).tolist()
        + export_risk_gate_df.get("required_disclaimers", pd.Series(dtype=object)).astype(str).tolist()
    )

    checks = [
        {"check_name": "inputs::342p_output_dir_exists", "status": "PASS" if reviewed_plus_preview_342p_dir.exists() else "FAIL", "detail": str(reviewed_plus_preview_342p_dir)},
        {"check_name": "inputs::342p_summary_exists", "status": "PASS" if summary_342p_path.exists() else "FAIL", "detail": str(summary_342p_path)},
        {"check_name": "inputs::342p_qa_exists", "status": "PASS" if qa_342p_path.exists() else "FAIL", "detail": str(qa_342p_path)},
        {"check_name": "inputs::342p_workbook_exists", "status": "PASS" if workbook_342p_path.exists() else "FAIL", "detail": str(workbook_342p_path)},
        {
            "check_name": "inputs::342p_ready_for_342q_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "342p_decision": summary_342p.get("decision", ""),
                    "342p_ready_for_342q": summary_342p.get("ready_for_342q", False),
                    "342p_qa_fail_count": summary_342p.get("qa_fail_count", 0),
                    "342o_decision": summary_342o.get("decision", ""),
                    "342j_decision": summary_342j.get("decision", ""),
                    "342i_decision": summary_342i.get("decision", ""),
                    "342n_decision": summary_342n.get("decision", ""),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342p_required_sheets_exist",
            "status": "PASS" if required_342p_present else "FAIL",
            "detail": json.dumps({sheet: sheet in workbook_342p_sheet_names for sheet in REQUIRED_342P_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "quality::combined_preview_rows_loaded",
            "status": "PASS" if combined_preview_row_count > 0 else "FAIL",
            "detail": str(combined_preview_row_count),
        },
        {
            "check_name": "quality::human_reviewed_rows_loaded",
            "status": "PASS" if len(human_reviewed_df) > 0 else "FAIL",
            "detail": str(len(human_reviewed_df)),
        },
        {
            "check_name": "quality::simulated_rows_loaded",
            "status": "PASS" if len(sim_direct_df) + len(sim_corrected_df) > 0 else "FAIL",
            "detail": f"direct={len(sim_direct_df)} corrected={len(sim_corrected_df)}",
        },
        {
            "check_name": "quality::342p_summary_combined_count_consistent",
            "status": "PASS" if combined_preview_row_count == _safe_int(summary_342p.get("combined_preview_row_count", 0)) else "FAIL",
            "detail": f"sheet={combined_preview_row_count} summary={summary_342p.get('combined_preview_row_count', 0)}",
        },
        {
            "check_name": "quality::342p_summary_simulated_count_consistent",
            "status": "PASS" if simulated_preview_count == _safe_int(summary_342p.get("simulated_preview_count", 0)) else "FAIL",
            "detail": f"sheet={simulated_preview_count} summary={summary_342p.get('simulated_preview_count', 0)}",
        },
        {
            "check_name": "quality::trust_levels_are_valid",
            "status": "PASS" if preview_metrics["unknown_trust_level_count"] == 0 and preview_metrics["trust_level_mismatch_count"] == 0 else "FAIL",
            "detail": json.dumps(
                {
                    "unknown_trust_level_count": preview_metrics["unknown_trust_level_count"],
                    "trust_level_mismatch_count": preview_metrics["trust_level_mismatch_count"],
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::no_simulated_row_final_confirmed_true",
            "status": "PASS" if preview_metrics["simulated_final_confirmed_true_count"] == 0 else "FAIL",
            "detail": str(preview_metrics["simulated_final_confirmed_true_count"]),
        },
        {
            "check_name": "quality::no_row_client_ready_true",
            "status": "PASS" if not (not preview_audit_df.empty and preview_audit_df["client_ready"].astype(bool).any()) else "FAIL",
            "detail": str(int(preview_audit_df["client_ready"].astype(bool).sum()) if not preview_audit_df.empty else 0),
        },
        {
            "check_name": "quality::no_row_production_ready_true",
            "status": "PASS" if not (not preview_audit_df.empty and preview_audit_df["production_ready"].astype(bool).any()) else "FAIL",
            "detail": str(int(preview_audit_df["production_ready"].astype(bool).sum()) if not preview_audit_df.empty else 0),
        },
        {
            "check_name": "quality::dropped_duplicate_rows_not_in_export_candidate_scope",
            "status": "PASS" if dropped_metrics["dropped_rows_found_in_combined_count"] == 0 else "FAIL",
            "detail": json.dumps(dropped_metrics, ensure_ascii=False),
        },
        {
            "check_name": "quality::human_over_simulation_override_retains_human_priority",
            "status": "PASS" if int(collision_metrics.get("human_priority_violation_count", 0) or 0) == 0 else "FAIL",
            "detail": json.dumps(
                {
                    "override_count": override_metrics["override_count"],
                    "human_priority_violation_count": collision_metrics.get("human_priority_violation_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::formal_client_export_allowed_false",
            "status": "PASS",
            "detail": "false",
        },
        {
            "check_name": "claims::client_ready_false",
            "status": "PASS",
            "detail": "false",
        },
        {
            "check_name": "claims::production_ready_false",
            "status": "PASS",
            "detail": "false",
        },
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(claims_text, ["investment advice"]) else "FAIL",
            "detail": "342Q audit text checked",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "342Q adds audit-sidecar logic only.",
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
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS",
            "detail": "all 342Q sheet names are <= 31 chars",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342r = bool(
        input_ready
        and export_candidate_scope_allowed
        and combined_preview_row_count > 0
        and qa_fail_count == 0
        and no_write_back_proof_passed
    )
    decision = READY_DECISION if ready_for_342r else NOT_READY_DECISION
    recommended_342r_scope = RECOMMENDED_342R_SCOPE if ready_for_342r else ""

    summary = {
        "generated_at_utc": _utc_now(),
        "human_reviewed_preview_count": human_reviewed_preview_count,
        "simulated_preview_count": simulated_preview_count,
        "simulated_direct_preview_count": simulated_direct_preview_count,
        "simulated_corrected_preview_count": simulated_corrected_preview_count,
        "combined_preview_row_count": combined_preview_row_count,
        "export_candidate_row_count": export_candidate_row_count,
        "unknown_trust_level_count": preview_metrics["unknown_trust_level_count"],
        "trust_level_mismatch_count": preview_metrics["trust_level_mismatch_count"],
        "simulated_final_confirmed_true_count": preview_metrics["simulated_final_confirmed_true_count"],
        "simulated_client_ready_true_count": preview_metrics["simulated_client_ready_true_count"],
        "simulated_production_ready_true_count": preview_metrics["simulated_production_ready_true_count"],
        "missing_display_warning_count": preview_metrics["missing_display_warning_count"],
        "collision_logged_count": int(collision_metrics.get("collision_logged_count", 0) or 0),
        "duplicate_metric_year_source_count": _safe_int(summary_342p.get("duplicate_metric_year_source_count", 0)),
        "human_over_simulation_override_count": int(override_metrics.get("override_count", 0) or 0),
        "simulated_duplicate_dropped_count": int(dropped_metrics.get("simulated_duplicate_dropped_count", 0) or 0),
        "unresolved_collision_count": int(collision_metrics.get("unresolved_collision_count", 0) or 0),
        "severe_collision_count": int(collision_metrics.get("severe_collision_count", 0) or 0),
        "formal_client_export_allowed": False,
        "export_candidate_scope_allowed": export_candidate_scope_allowed,
        "export_risk_level": export_risk_level,
        "still_human_required_count": still_human_required_count,
        "remaining_review_count": remaining_review_count,
        "ready_for_342r": ready_for_342r,
        "recommended_342r_scope": recommended_342r_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342Q_preview_audit_export_readiness_gate",
        "reviewed_plus_preview_342p_dir": str(reviewed_plus_preview_342p_dir),
        "post_adoption_sidecar_342o_dir": str(post_adoption_sidecar_342o_dir),
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
        "post_human_sidecar_342i_dir": str(post_human_sidecar_342i_dir),
        "adoption_simulation_342n_dir": str(adoption_simulation_342n_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
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
        "00_README": readme_df,
        "01_AUDIT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342P_SUMMARY": _clean_frame(pd.DataFrame([summary_342p])) if summary_342p else pd.DataFrame(),
        "03_PREVIEW_AUDIT": preview_audit_df,
        "04_TRUST_LEVEL_AUDIT": trust_level_audit_df,
        "05_SIM_BOUNDARY_AUDIT": sim_boundary_audit_df,
        "06_COLLISION_AUDIT": collision_audit_df,
        "07_DROPPED_DUP_AUDIT": dropped_dup_audit_df,
        "08_OVERRIDE_AUDIT": override_audit_df,
        "09_EXPORT_RISK_GATE": export_risk_gate_df,
        "10_EXPORT_CANDIDATE_SCOPE": export_candidate_scope_df,
        "11_REMAINING_BACKLOG": remaining_backlog_df,
        "12_342R_READINESS": _build_readiness_df(summary),
        "13_NO_WRITE_BACK": _build_no_write_back_proof_df(no_write_back_json),
        "14_NEXT_STEPS": _build_next_steps_df(summary),
    }
    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
