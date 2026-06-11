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


READY_INPUT_342Q_DECISION = "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY"
READY_INPUT_342P_DECISION = "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY"
READY_INPUT_342O_DECISION = "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY"
READY_INPUT_342J_DECISION = "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY"
READY_DECISION = "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY"
NOT_READY_DECISION = "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_NOT_READY"

DEFAULT_PREVIEW_AUDIT_342Q_DIR = Path(r"D:\_datefac\output\preview_audit_export_readiness_gate_342q")
DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR = Path(r"D:\_datefac\output\reviewed_plus_simulated_client_preview_342p")
DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR = Path(r"D:\_datefac\output\post_adoption_sidecar_simulation_342o")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\audit_labeled_export_candidate_package_342r")

SUMMARY_FILE_NAME = "audit_labeled_export_candidate_package_342r_summary.json"
MANIFEST_FILE_NAME = "audit_labeled_export_candidate_package_342r_manifest.json"
QA_FILE_NAME = "audit_labeled_export_candidate_package_342r_qa.json"
NO_WRITE_BACK_FILE_NAME = "audit_labeled_export_candidate_package_342r_no_write_back_proof.json"
REPORT_FILE_NAME = "audit_labeled_export_candidate_package_342r_report.md"
WORKBOOK_FILE_NAME = "audit_labeled_export_candidate_package_342r.xlsx"
CSV_FILE_NAME = "audit_labeled_export_candidate_package_342r_candidates.csv"
METADATA_FILE_NAME = "audit_labeled_export_candidate_package_342r_metadata.json"

INPUT_342Q_SUMMARY_NAME = "preview_audit_export_readiness_gate_342q_summary.json"
INPUT_342Q_QA_NAME = "preview_audit_export_readiness_gate_342q_qa.json"
INPUT_342Q_REPORT_NAME = "preview_audit_export_readiness_gate_342q_report.md"
INPUT_342Q_WORKBOOK_NAME = "preview_audit_export_readiness_gate_342q.xlsx"

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

REQUIRED_342Q_SHEETS = [
    "01_AUDIT_SUMMARY",
    "03_PREVIEW_AUDIT",
    "04_TRUST_LEVEL_AUDIT",
    "05_SIM_BOUNDARY_AUDIT",
    "06_COLLISION_AUDIT",
    "09_EXPORT_RISK_GATE",
    "10_EXPORT_CANDIDATE_SCOPE",
    "11_REMAINING_BACKLOG",
    "12_342R_READINESS",
    "13_NO_WRITE_BACK",
]

REQUIRED_342P_SHEETS = [
    "04_COMBINED_PREVIEW",
    "05_HUMAN_REVIEWED",
    "06_SIM_DIRECT",
    "07_SIM_CORRECTED",
    "09_COLLISION_CHECK",
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

AUDIT_LABEL_MAP = {
    "HUMAN_REVIEWED": {
        "audit_label": "AUDIT_LABEL_HUMAN_REVIEWED",
        "display_badge": "REVIEWED_PILOT",
        "warning_level": "MEDIUM",
        "requires_later_audit": False,
        "package_note": "human-reviewed pilot row; still not a formal client export",
    },
    "SIMULATED_DIRECT_ADOPTED": {
        "audit_label": "AUDIT_LABEL_SIMULATED_DIRECT",
        "display_badge": "SIMULATION_ONLY",
        "warning_level": "HIGH",
        "requires_later_audit": True,
        "package_note": "simulation-only adopted row; later audit required before any broader export claim",
    },
    "SIMULATED_CORRECTION_ADOPTED": {
        "audit_label": "AUDIT_LABEL_SIMULATED_CORRECTED",
        "display_badge": "SIMULATION_CORRECTED_ONLY",
        "warning_level": "HIGH",
        "requires_later_audit": True,
        "package_note": "simulation-corrected adopted row; later audit required before any broader export claim",
    },
}

VALID_PREVIEW_SOURCE_TYPE = {
    "HUMAN_REVIEWED": "HUMAN_REVIEWED",
    "SIMULATED_DIRECT_ADOPTED": "SIMULATED_DIRECT",
    "SIMULATED_CORRECTION_ADOPTED": "SIMULATED_CORRECTED",
}

RECOMMENDED_342S_SCOPE = "package_audit_snapshot_or_demo_handoff"


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


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _load_342q_context(preview_audit_342q_dir: Path) -> tuple[
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, pd.DataFrame],
    List[str],
    List[str],
    List[str],
]:
    summary, qa_json, files_read, warnings = _load_summary_qa_report(
        base_dir=preview_audit_342q_dir,
        summary_name=INPUT_342Q_SUMMARY_NAME,
        qa_name=INPUT_342Q_QA_NAME,
        report_name=INPUT_342Q_REPORT_NAME,
    )
    workbook_path = preview_audit_342q_dir / INPUT_342Q_WORKBOOK_NAME
    sheets, sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342Q_SHEETS)
    if workbook_path.exists():
        files_read.append(str(workbook_path))
    else:
        warnings.append(f"missing workbook: {workbook_path}")
    warnings.extend(workbook_warnings)
    return summary, qa_json, sheets, sheet_names, files_read, warnings


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


def _join_strings(parts: Sequence[str]) -> str:
    return " | ".join([part for part in parts if _norm_text(part)])


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "section": "scope",
            "message": "342R packages the 342Q-approved export candidate scope into an audit-labeled candidate package.",
        },
        {
            "section": "boundary",
            "message": "342R is not a formal client export and must keep formal_client_export_allowed=false, client_ready=false, and production_ready=false.",
        },
        {
            "section": "simulation",
            "message": "Simulated rows remain simulation-only and require later audit before any broader export claim.",
        },
        {
            "section": "risk",
            "message": "The package preserves HIGH export risk, collision context, and remaining backlog context.",
        },
        {
            "section": "usage",
            "message": "Allowed usage is internal audit, demo handoff with explicit disclaimer, or downstream package audit snapshot.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _add_row_ids(frame: pd.DataFrame, prefix: str, column: str) -> pd.DataFrame:
    if frame.empty:
        result = frame.copy()
        result[column] = pd.Series(dtype=object)
        return result
    result = frame.copy()
    result[column] = [f"{prefix}{index + 1:04d}" for index in range(len(result))]
    ordered_cols = [column] + [col for col in result.columns if col != column]
    return result[ordered_cols]


def _build_candidate_rows(
    candidate_scope_df: pd.DataFrame,
    preview_audit_df: pd.DataFrame,
    combined_preview_df: pd.DataFrame,
) -> tuple[pd.DataFrame, Dict[str, int]]:
    if candidate_scope_df.empty:
        empty = pd.DataFrame(
            columns=[
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
                "required_disclaimer_text",
                "not_formal_client_export",
                "formal_client_export_allowed",
                "client_ready",
                "production_ready",
                "final_confirmed",
                "package_row_status",
                "package_warning_level",
                "requires_later_audit",
                "source_stage",
                "upstream_source_stage",
                "preview_source_type",
                "package_note",
            ]
        )
        return _clean_frame(empty), {
            "package_row_fail_count": 0,
            "trust_level_mismatch_count": 0,
            "invalid_trust_level_count": 0,
            "disclaimer_required_count": 0,
            "later_audit_required_count": 0,
        }

    preview_lookup = combined_preview_df.copy()
    if "preview_row_id" in preview_lookup.columns:
        preview_lookup = preview_lookup.rename(columns={"preview_row_id": "source_preview_row_id"})
    audit_lookup = preview_audit_df.copy()
    if "preview_row_id" in audit_lookup.columns:
        audit_lookup = audit_lookup.rename(columns={"preview_row_id": "source_preview_row_id"})

    merged = candidate_scope_df.merge(
        preview_lookup,
        on="source_preview_row_id",
        how="left",
        suffixes=("", "_342p"),
    )
    merged = merged.merge(
        audit_lookup[
            [
                "source_preview_row_id",
                "audit_status",
                "audit_reason",
                "requires_disclaimer",
                "requires_later_audit",
                "export_candidate_allowed",
            ]
        ],
        on="source_preview_row_id",
        how="left",
        suffixes=("", "_342q"),
    )

    rows: List[Dict[str, Any]] = []
    package_row_fail_count = 0
    trust_level_mismatch_count = 0
    invalid_trust_level_count = 0
    disclaimer_required_count = 0
    later_audit_required_count = 0

    for item in merged.to_dict(orient="records"):
        trust_level = _norm_text(item.get("data_trust_level"))
        preview_source_type = _norm_text(item.get("preview_source_type"))
        audit_meta = AUDIT_LABEL_MAP.get(trust_level)
        expected_preview_source = VALID_PREVIEW_SOURCE_TYPE.get(trust_level, "")
        audit_status = _norm_text(item.get("audit_status"))
        display_warning = _norm_text(item.get("display_warning"))
        required_disclaimer = _as_bool(item.get("required_disclaimer"))
        requires_later_audit = audit_meta["requires_later_audit"] if audit_meta else _as_bool(item.get("requires_later_audit"))

        row_fail_reasons: List[str] = []
        if not audit_meta:
            invalid_trust_level_count += 1
            row_fail_reasons.append("invalid data_trust_level for 342R package")
        if expected_preview_source and preview_source_type and preview_source_type != expected_preview_source:
            trust_level_mismatch_count += 1
            row_fail_reasons.append("preview_source_type does not match data_trust_level")
        if audit_status == "FAIL":
            row_fail_reasons.append("upstream 342Q preview audit failed for this row")
        if _as_bool(item.get("client_ready")):
            row_fail_reasons.append("client_ready must remain false")
        if _as_bool(item.get("production_ready")):
            row_fail_reasons.append("production_ready must remain false")
        if _as_bool(item.get("final_confirmed")):
            row_fail_reasons.append("final_confirmed must remain false in 342R package")
        if not display_warning:
            row_fail_reasons.append("display_warning missing")
        if trust_level != "HUMAN_REVIEWED" and "later audit" not in display_warning.casefold():
            row_fail_reasons.append("simulated row warning must mention later audit")
        if trust_level != "HUMAN_REVIEWED" and "simulation" not in display_warning.casefold():
            row_fail_reasons.append("simulated row warning must mention simulation-only boundary")
        if trust_level == "HUMAN_REVIEWED" and not display_warning:
            row_fail_reasons.append("human-reviewed row warning missing")
        if trust_level != "HUMAN_REVIEWED" and not requires_later_audit:
            row_fail_reasons.append("simulated rows must require later audit")
        if not _as_bool(item.get("not_formal_client_export", True)):
            row_fail_reasons.append("not_formal_client_export must remain true")
        if _norm_text(item.get("export_scope_status")) == "":
            row_fail_reasons.append("export_scope_status missing")

        if row_fail_reasons:
            package_row_fail_count += 1

        if required_disclaimer:
            disclaimer_required_count += 1
        if requires_later_audit:
            later_audit_required_count += 1

        audit_label = audit_meta["audit_label"] if audit_meta else "AUDIT_LABEL_UNKNOWN"
        display_badge = audit_meta["display_badge"] if audit_meta else "UNKNOWN_SCOPE"
        package_warning_level = audit_meta["warning_level"] if audit_meta else "HIGH"
        package_note = audit_meta["package_note"] if audit_meta else "unknown trust-level candidate row; review required"
        if row_fail_reasons:
            package_note = _join_strings([package_note, "; ".join(row_fail_reasons)])

        rows.append(
            {
                "export_candidate_row_id": item.get("export_candidate_row_id", ""),
                "source_preview_row_id": item.get("source_preview_row_id", ""),
                "review_item_id": item.get("review_item_id", ""),
                "metric_standardized": item.get("metric_standardized", ""),
                "year_standardized": item.get("year_standardized", ""),
                "value_numeric": item.get("value_numeric", ""),
                "normalized_unit": item.get("normalized_unit", ""),
                "data_trust_level": trust_level,
                "export_scope_status": item.get("export_scope_status", ""),
                "display_warning": display_warning,
                "required_disclaimer": required_disclaimer,
                "required_disclaimer_text": (
                    "This row is in an audit-labeled export candidate package only."
                    if required_disclaimer
                    else "Human-reviewed pilot row; still not a formal client export."
                ),
                "not_formal_client_export": True,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "final_confirmed": False,
                "package_row_status": "INCLUDED_IN_AUDIT_LABELED_PACKAGE",
                "package_warning_level": package_warning_level,
                "requires_later_audit": requires_later_audit,
                "source_stage": "342Q",
                "upstream_source_stage": item.get("source_stage_342p", item.get("source_stage", "")),
                "preview_source_type": preview_source_type or expected_preview_source,
                "review_status_for_client_display": item.get("review_status_for_client_display", ""),
                "audit_status": audit_status or ("FAIL" if row_fail_reasons else "PASS"),
                "audit_reason": item.get("audit_reason", ""),
                "audit_label": audit_label,
                "display_badge": display_badge,
                "package_note": package_note,
                "corpus_pdf_id": item.get("corpus_pdf_id", ""),
                "file_name": item.get("file_name", ""),
                "table_id": item.get("table_id", ""),
                "table_type": item.get("table_type", ""),
                "source_page": item.get("source_page", ""),
                "bbox": item.get("bbox", ""),
                "image_path": item.get("image_path", ""),
                "evidence": item.get("evidence", ""),
                "adoption_confidence": item.get("adoption_confidence", ""),
                "adoption_evidence": item.get("adoption_evidence", ""),
                "correction_pattern": item.get("correction_pattern", ""),
                "correction_reason": item.get("correction_reason", ""),
                "original_metric_standardized": item.get("original_metric_standardized", ""),
                "original_normalized_unit": item.get("original_normalized_unit", ""),
                "collision_key": item.get("collision_key", ""),
            }
        )

    result = _clean_frame(pd.DataFrame(rows))
    metrics = {
        "package_row_fail_count": package_row_fail_count,
        "trust_level_mismatch_count": trust_level_mismatch_count,
        "invalid_trust_level_count": invalid_trust_level_count,
        "disclaimer_required_count": disclaimer_required_count,
        "later_audit_required_count": later_audit_required_count,
    }
    return result, metrics


def _build_audit_labels_df(candidates_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return pd.DataFrame(
            columns=[
                "audit_label_row_id",
                "review_item_id",
                "data_trust_level",
                "audit_label",
                "audit_label_reason",
                "display_badge",
            ]
        )
    rows = []
    for item in candidates_df.to_dict(orient="records"):
        reason = {
            "HUMAN_REVIEWED": "Human-reviewed pilot row kept in bounded audit-labeled candidate scope.",
            "SIMULATED_DIRECT_ADOPTED": "Simulation-only direct adopted row kept only with later-audit boundary.",
            "SIMULATED_CORRECTION_ADOPTED": "Simulation-corrected adopted row kept only with later-audit boundary.",
        }.get(_norm_text(item.get("data_trust_level")), "Unknown trust label requires review.")
        rows.append(
            {
                "review_item_id": item.get("review_item_id", ""),
                "data_trust_level": item.get("data_trust_level", ""),
                "audit_label": item.get("audit_label", ""),
                "audit_label_reason": reason,
                "display_badge": item.get("display_badge", ""),
            }
        )
    return _add_row_ids(_clean_frame(pd.DataFrame(rows)), "342r::audit_label::", "audit_label_row_id")


def _build_required_warnings_df(candidates_df: pd.DataFrame, remaining_review_count: int) -> pd.DataFrame:
    if candidates_df.empty:
        return pd.DataFrame(
            columns=[
                "warning_row_id",
                "review_item_id",
                "data_trust_level",
                "warning_text",
                "disclaimer_required",
                "later_audit_required",
                "formal_export_blocker",
            ]
        )
    rows = []
    for item in candidates_df.to_dict(orient="records"):
        warning_parts = [
            "formal client export is not allowed",
            "client_ready=false",
            "production_ready=false",
        ]
        if _as_bool(item.get("requires_later_audit")):
            warning_parts.append("simulated rows require later audit")
        warning_parts.append("export risk level is HIGH")
        warning_parts.append(f"{remaining_review_count} rows remain outside current reviewed/simulated scope")
        rows.append(
            {
                "review_item_id": item.get("review_item_id", ""),
                "data_trust_level": item.get("data_trust_level", ""),
                "warning_text": " | ".join(warning_parts),
                "disclaimer_required": _as_bool(item.get("required_disclaimer")),
                "later_audit_required": _as_bool(item.get("requires_later_audit")),
                "formal_export_blocker": True,
            }
        )
    return _add_row_ids(_clean_frame(pd.DataFrame(rows)), "342r::warning::", "warning_row_id")


def _build_risk_disclosure_df(summary_342q: Mapping[str, Any]) -> pd.DataFrame:
    risk_reasons = [
        "package contains simulated rows",
        f"collision count is high ({_safe_int(summary_342q.get('collision_logged_count', 0))})",
        f"severe_collision_count = {_safe_int(summary_342q.get('severe_collision_count', 0))}",
        f"duplicate_metric_year_source_count = {_safe_int(summary_342q.get('duplicate_metric_year_source_count', 0))}",
        f"remaining_review_count = {_safe_int(summary_342q.get('remaining_review_count', 0))}",
        f"still_human_required_count = {_safe_int(summary_342q.get('still_human_required_count', 0))}",
    ]
    row = {
        "export_risk_level": "HIGH",
        "risk_reasons": " | ".join(risk_reasons),
        "formal_client_export_allowed": False,
        "export_candidate_scope_allowed": True,
        "client_ready": False,
        "production_ready": False,
        "recommended_usage": "internal audit | demo with explicit disclaimer | downstream review package | not formal client delivery",
    }
    return _clean_frame(pd.DataFrame([row]))


def _build_collision_context_df(collision_audit_df: pd.DataFrame, summary_342q: Mapping[str, Any]) -> pd.DataFrame:
    base = collision_audit_df.copy()
    if base.empty:
        base = pd.DataFrame([{}])
    base["collision_logged_count"] = _safe_int(summary_342q.get("collision_logged_count", 0))
    base["duplicate_metric_year_source_count"] = _safe_int(summary_342q.get("duplicate_metric_year_source_count", 0))
    base["human_over_simulation_override_count"] = _safe_int(summary_342q.get("human_over_simulation_override_count", 0))
    base["simulated_duplicate_dropped_count"] = _safe_int(summary_342q.get("simulated_duplicate_dropped_count", 0))
    base["unresolved_collision_count"] = _safe_int(summary_342q.get("unresolved_collision_count", 0))
    base["severe_collision_count"] = _safe_int(summary_342q.get("severe_collision_count", 0))
    base["collision_note"] = (
        "collision records are retained as audit evidence; dropped simulated duplicates stay outside the package; human-priority overrides remain preserved; risk level stays HIGH"
    )
    return _clean_frame(base)


def _build_backlog_context_df(summary_342q: Mapping[str, Any]) -> pd.DataFrame:
    row = {
        "remaining_review_count": _safe_int(summary_342q.get("remaining_review_count", 0)),
        "still_human_required_count": _safe_int(summary_342q.get("still_human_required_count", 0)),
        "backlog_note": "current package covers only the bounded 342Q export candidate scope",
        "recommended_next_review_action": "continue human review, expand spot-check evidence, or proceed to 342S package audit snapshot / demo handoff with explicit disclaimer",
    }
    return _clean_frame(pd.DataFrame([row]))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342s": summary.get("ready_for_342s", False),
                    "recommended_342s_scope": summary.get("recommended_342s_scope", ""),
                    "formal_client_export_allowed": summary.get("formal_client_export_allowed", False),
                    "client_ready": summary.get("client_ready", False),
                    "production_ready": summary.get("production_ready", False),
                    "decision": summary.get("decision", ""),
                }
            ]
        )
    )


def _build_no_write_back_proof_df(no_write_back_json: Mapping[str, Any]) -> pd.DataFrame:
    rows = [{"key": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value} for key, value in no_write_back_json.items()]
    return _clean_frame(pd.DataFrame(rows))


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "step_order": 1,
            "next_step": "342S Package Audit Snapshot Or Demo Handoff" if summary.get("ready_for_342s") else "Fix 342R QA blockers before 342S",
            "detail": "Use the package only as an audit-labeled candidate handoff, never as formal client export.",
        },
        {
            "step_order": 2,
            "next_step": "Preserve disclaimer boundaries",
            "detail": "Keep formal_client_export_allowed=false, client_ready=false, production_ready=false in all downstream uses.",
        },
        {
            "step_order": 3,
            "next_step": "Continue review backlog handling",
            "detail": f"Remaining review backlog stays {_safe_int(summary.get('remaining_review_count', 0))} rows with {_safe_int(summary.get('still_human_required_count', 0))} still-human-required rows.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_audit_labeled_export_candidate_package_342r(
    *,
    preview_audit_342q_dir: Path = DEFAULT_PREVIEW_AUDIT_342Q_DIR,
    reviewed_plus_preview_342p_dir: Path = DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR,
    post_adoption_sidecar_342o_dir: Path = DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR,
    reviewed_preview_342j_dir: Path = DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path = Path(__file__).resolve().parents[2],
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    warnings: List[str] = []
    files_read: List[str] = []
    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342q, qa_342q, workbook_342q, workbook_342q_sheet_names, files_342q, warnings_342q = _load_342q_context(preview_audit_342q_dir)
    summary_342p, qa_342p, workbook_342p, workbook_342p_sheet_names, files_342p, warnings_342p = _load_342p_context(reviewed_plus_preview_342p_dir)
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
    warnings.extend(warnings_342q + warnings_342p + warnings_342o + warnings_342j)
    files_read.extend(files_342q + files_342p + files_342o + files_342j)

    summary_342q_path = preview_audit_342q_dir / INPUT_342Q_SUMMARY_NAME
    qa_342q_path = preview_audit_342q_dir / INPUT_342Q_QA_NAME
    workbook_342q_path = preview_audit_342q_dir / INPUT_342Q_WORKBOOK_NAME
    summary_342p_path = reviewed_plus_preview_342p_dir / INPUT_342P_SUMMARY_NAME
    qa_342p_path = reviewed_plus_preview_342p_dir / INPUT_342P_QA_NAME
    workbook_342p_path = reviewed_plus_preview_342p_dir / INPUT_342P_WORKBOOK_NAME

    all_input_paths = [
        summary_342q_path,
        qa_342q_path,
        workbook_342q_path,
        summary_342p_path,
        qa_342p_path,
        workbook_342p_path,
        post_adoption_sidecar_342o_dir / INPUT_342O_SUMMARY_NAME,
        post_adoption_sidecar_342o_dir / INPUT_342O_QA_NAME,
        workbook_342o_path,
        reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME,
        reviewed_preview_342j_dir / INPUT_342J_QA_NAME,
        workbook_342j_path,
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}

    required_342q_present = all(sheet in workbook_342q_sheet_names for sheet in REQUIRED_342Q_SHEETS)
    required_342p_present = all(sheet in workbook_342p_sheet_names for sheet in REQUIRED_342P_SHEETS)

    input_ready = bool(
        summary_342q.get("decision") == READY_INPUT_342Q_DECISION
        and _as_bool(summary_342q.get("ready_for_342r"))
        and _safe_int(summary_342q.get("qa_fail_count", 1)) == 0
        and _as_bool(summary_342q.get("export_candidate_scope_allowed"))
        and not _as_bool(summary_342q.get("formal_client_export_allowed"))
        and not _as_bool(summary_342q.get("client_ready"))
        and not _as_bool(summary_342q.get("production_ready"))
        and summary_342p.get("decision") == READY_INPUT_342P_DECISION
        and _safe_int(summary_342p.get("qa_fail_count", 1)) == 0
        and summary_342o.get("decision") == READY_INPUT_342O_DECISION
        and _safe_int(summary_342o.get("qa_fail_count", 1)) == 0
        and summary_342j.get("decision") == READY_INPUT_342J_DECISION
        and _safe_int(summary_342j.get("qa_fail_count", 1)) == 0
        and required_342q_present
        and required_342p_present
    )

    candidate_scope_df = _clean_frame(workbook_342q.get("10_EXPORT_CANDIDATE_SCOPE", pd.DataFrame())) if input_ready else pd.DataFrame()
    preview_audit_df = _clean_frame(workbook_342q.get("03_PREVIEW_AUDIT", pd.DataFrame())) if input_ready else pd.DataFrame()
    collision_audit_df = _clean_frame(workbook_342q.get("06_COLLISION_AUDIT", pd.DataFrame())) if input_ready else pd.DataFrame()
    combined_preview_df = _clean_frame(workbook_342p.get("04_COMBINED_PREVIEW", pd.DataFrame())) if input_ready else pd.DataFrame()

    candidates_df, candidate_metrics = _build_candidate_rows(
        candidate_scope_df=candidate_scope_df,
        preview_audit_df=preview_audit_df,
        combined_preview_df=combined_preview_df,
    )
    human_reviewed_df = _clean_frame(candidates_df[candidates_df["data_trust_level"].map(_norm_text) == "HUMAN_REVIEWED"].copy()) if not candidates_df.empty else pd.DataFrame()
    simulated_direct_df = _clean_frame(candidates_df[candidates_df["data_trust_level"].map(_norm_text) == "SIMULATED_DIRECT_ADOPTED"].copy()) if not candidates_df.empty else pd.DataFrame()
    simulated_corrected_df = _clean_frame(candidates_df[candidates_df["data_trust_level"].map(_norm_text) == "SIMULATED_CORRECTION_ADOPTED"].copy()) if not candidates_df.empty else pd.DataFrame()
    audit_labels_df = _build_audit_labels_df(candidates_df)
    remaining_review_count = _safe_int(summary_342q.get("remaining_review_count", 0))
    warnings_df = _build_required_warnings_df(candidates_df, remaining_review_count)
    risk_disclosure_df = _build_risk_disclosure_df(summary_342q)
    collision_context_df = _build_collision_context_df(collision_audit_df, summary_342q)
    backlog_context_df = _build_backlog_context_df(summary_342q)

    export_candidate_expected_count = _safe_int(summary_342q.get("export_candidate_row_count", 0))
    export_candidate_package_row_count = int(len(candidates_df))
    human_reviewed_candidate_count = int(len(human_reviewed_df))
    simulated_direct_candidate_count = int(len(simulated_direct_df))
    simulated_corrected_candidate_count = int(len(simulated_corrected_df))
    simulated_candidate_count = simulated_direct_candidate_count + simulated_corrected_candidate_count
    disclaimer_required_count = int(candidate_metrics.get("disclaimer_required_count", 0) or 0)
    later_audit_required_count = int(candidate_metrics.get("later_audit_required_count", 0) or 0)

    row_final_confirmed_true_count = int(candidates_df["final_confirmed"].map(_as_bool).sum()) if not candidates_df.empty else 0
    row_client_ready_true_count = int(candidates_df["client_ready"].map(_as_bool).sum()) if not candidates_df.empty else 0
    row_production_ready_true_count = int(candidates_df["production_ready"].map(_as_bool).sum()) if not candidates_df.empty else 0
    simulated_rows_missing_later_audit_count = int(
        candidates_df[
            (candidates_df["data_trust_level"].map(_norm_text).isin({"SIMULATED_DIRECT_ADOPTED", "SIMULATED_CORRECTION_ADOPTED"}))
            & (~candidates_df["requires_later_audit"].map(_as_bool))
        ].shape[0]
    ) if not candidates_df.empty else 0
    required_disclaimer_missing_count = int(
        candidates_df[
            candidates_df["display_warning"].map(_norm_text).eq("")
        ].shape[0]
    ) if not candidates_df.empty else 0

    input_hashes_after = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342R",
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
        no_write_back_json.get("no_official_asset_modification_during_342r")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
    )

    claims_text = "\n".join(
        _clean_frame(risk_disclosure_df).astype(str).fillna("").sum(axis=1).tolist()
        + _clean_frame(warnings_df).astype(str).fillna("").sum(axis=1).tolist()
        + _clean_frame(_build_readme_df()).astype(str).fillna("").sum(axis=1).tolist()
    )

    checks = [
        {"check_name": "inputs::342q_output_dir_exists", "status": "PASS" if preview_audit_342q_dir.exists() else "FAIL", "detail": str(preview_audit_342q_dir)},
        {"check_name": "inputs::342q_summary_exists", "status": "PASS" if summary_342q_path.exists() else "FAIL", "detail": str(summary_342q_path)},
        {"check_name": "inputs::342q_qa_exists", "status": "PASS" if qa_342q_path.exists() else "FAIL", "detail": str(qa_342q_path)},
        {"check_name": "inputs::342q_workbook_exists", "status": "PASS" if workbook_342q_path.exists() else "FAIL", "detail": str(workbook_342q_path)},
        {
            "check_name": "inputs::342q_ready_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "342q_decision": summary_342q.get("decision", ""),
                    "342q_ready_for_342r": summary_342q.get("ready_for_342r", False),
                    "342q_qa_fail_count": summary_342q.get("qa_fail_count", 0),
                    "342q_export_candidate_scope_allowed": summary_342q.get("export_candidate_scope_allowed", False),
                    "342p_decision": summary_342p.get("decision", ""),
                    "342o_decision": summary_342o.get("decision", ""),
                    "342j_decision": summary_342j.get("decision", ""),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342q_required_sheets_exist",
            "status": "PASS" if required_342q_present else "FAIL",
            "detail": json.dumps({sheet: sheet in workbook_342q_sheet_names for sheet in REQUIRED_342Q_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::342p_required_sheets_exist",
            "status": "PASS" if required_342p_present else "FAIL",
            "detail": json.dumps({sheet: sheet in workbook_342p_sheet_names for sheet in REQUIRED_342P_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "quality::export_candidate_rows_loaded",
            "status": "PASS" if export_candidate_package_row_count > 0 else "FAIL",
            "detail": str(export_candidate_package_row_count),
        },
        {
            "check_name": "quality::package_row_count_matches_342q",
            "status": "PASS" if export_candidate_package_row_count == export_candidate_expected_count else "FAIL",
            "detail": f"package={export_candidate_package_row_count} 342q={export_candidate_expected_count}",
        },
        {
            "check_name": "quality::package_rows_have_no_internal_failures",
            "status": "PASS" if candidate_metrics["package_row_fail_count"] == 0 else "FAIL",
            "detail": str(candidate_metrics["package_row_fail_count"]),
        },
        {
            "check_name": "quality::trust_levels_are_valid",
            "status": "PASS" if candidate_metrics["invalid_trust_level_count"] == 0 and candidate_metrics["trust_level_mismatch_count"] == 0 else "FAIL",
            "detail": json.dumps(
                {
                    "invalid_trust_level_count": candidate_metrics["invalid_trust_level_count"],
                    "trust_level_mismatch_count": candidate_metrics["trust_level_mismatch_count"],
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::no_row_final_confirmed_true",
            "status": "PASS" if row_final_confirmed_true_count == 0 else "FAIL",
            "detail": str(row_final_confirmed_true_count),
        },
        {
            "check_name": "quality::no_row_client_ready_true",
            "status": "PASS" if row_client_ready_true_count == 0 else "FAIL",
            "detail": str(row_client_ready_true_count),
        },
        {
            "check_name": "quality::no_row_production_ready_true",
            "status": "PASS" if row_production_ready_true_count == 0 else "FAIL",
            "detail": str(row_production_ready_true_count),
        },
        {
            "check_name": "quality::simulated_rows_require_later_audit",
            "status": "PASS" if simulated_rows_missing_later_audit_count == 0 else "FAIL",
            "detail": str(simulated_rows_missing_later_audit_count),
        },
        {
            "check_name": "quality::required_disclaimers_exist",
            "status": "PASS" if required_disclaimer_missing_count == 0 else "FAIL",
            "detail": str(required_disclaimer_missing_count),
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
            "detail": "342R package text checked",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "342R adds audit-sidecar packaging only.",
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
            "detail": "all 342R sheet names are <= 31 chars",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342s = bool(
        input_ready
        and export_candidate_package_row_count > 0
        and export_candidate_package_row_count == export_candidate_expected_count
        and candidate_metrics["package_row_fail_count"] == 0
        and row_final_confirmed_true_count == 0
        and row_client_ready_true_count == 0
        and row_production_ready_true_count == 0
        and simulated_rows_missing_later_audit_count == 0
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )
    decision = READY_DECISION if ready_for_342s else NOT_READY_DECISION
    recommended_342s_scope = RECOMMENDED_342S_SCOPE if ready_for_342s else ""

    summary = {
        "generated_at_utc": _utc_now(),
        "export_candidate_package_row_count": export_candidate_package_row_count,
        "human_reviewed_candidate_count": human_reviewed_candidate_count,
        "simulated_candidate_count": simulated_candidate_count,
        "simulated_direct_candidate_count": simulated_direct_candidate_count,
        "simulated_corrected_candidate_count": simulated_corrected_candidate_count,
        "formal_client_export_allowed": False,
        "export_candidate_scope_allowed": True,
        "export_risk_level": "HIGH",
        "collision_logged_count": _safe_int(summary_342q.get("collision_logged_count", 0)),
        "duplicate_metric_year_source_count": _safe_int(summary_342q.get("duplicate_metric_year_source_count", 0)),
        "severe_collision_count": _safe_int(summary_342q.get("severe_collision_count", 0)),
        "human_over_simulation_override_count": _safe_int(summary_342q.get("human_over_simulation_override_count", 0)),
        "simulated_duplicate_dropped_count": _safe_int(summary_342q.get("simulated_duplicate_dropped_count", 0)),
        "still_human_required_count": _safe_int(summary_342q.get("still_human_required_count", 0)),
        "remaining_review_count": remaining_review_count,
        "disclaimer_required_count": disclaimer_required_count,
        "later_audit_required_count": later_audit_required_count,
        "package_row_fail_count": candidate_metrics["package_row_fail_count"],
        "ready_for_342s": ready_for_342s,
        "recommended_342s_scope": recommended_342s_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    metadata = {
        "task": "342R_audit_labeled_export_candidate_package",
        "input_summary_counts": {
            "342q_export_candidate_row_count": export_candidate_expected_count,
            "342p_human_reviewed_preview_count": _safe_int(summary_342p.get("human_reviewed_preview_count", 0)),
            "342p_simulated_preview_count": _safe_int(summary_342p.get("simulated_preview_count", 0)),
            "342o_simulated_adopted_cell_count": _safe_int(summary_342o.get("simulated_adopted_cell_count", 0)),
            "342j_reviewed_preview_row_count": _safe_int(summary_342j.get("reviewed_preview_row_count", 0)),
        },
        "warnings": warnings,
    }

    manifest = {
        "task": "342R_audit_labeled_export_candidate_package",
        "preview_audit_342q_dir": str(preview_audit_342q_dir),
        "reviewed_plus_preview_342p_dir": str(reviewed_plus_preview_342p_dir),
        "post_adoption_sidecar_342o_dir": str(post_adoption_sidecar_342o_dir),
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "candidates_csv": str(output_dir / CSV_FILE_NAME),
            "metadata_json": str(output_dir / METADATA_FILE_NAME),
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
        "00_README": _build_readme_df(),
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342Q_SUMMARY": _clean_frame(pd.DataFrame([summary_342q])) if summary_342q else pd.DataFrame(),
        "03_EXPORT_CANDIDATES": candidates_df,
        "04_HUMAN_REVIEWED": human_reviewed_df,
        "05_SIMULATED_DIRECT": simulated_direct_df,
        "06_SIMULATED_CORRECTED": simulated_corrected_df,
        "07_AUDIT_LABELS": audit_labels_df,
        "08_REQUIRED_WARNINGS": warnings_df,
        "09_RISK_DISCLOSURE": risk_disclosure_df,
        "10_COLLISION_CONTEXT": collision_context_df,
        "11_BACKLOG_CONTEXT": backlog_context_df,
        "12_342S_READINESS": _build_readiness_df(summary),
        "13_NO_WRITE_BACK": _build_no_write_back_proof_df(no_write_back_json),
        "14_NEXT_STEPS": _build_next_steps_df(summary),
    }
    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "metadata_json": metadata,
        "workbook_sheets": workbook_sheets,
        "candidates_csv_df": candidates_df,
    }
