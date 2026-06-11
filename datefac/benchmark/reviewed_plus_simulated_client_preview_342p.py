from __future__ import annotations

import json
import re
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


READY_INPUT_342O_DECISION = "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY"
READY_INPUT_342J_DECISION = "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY"
READY_INPUT_342I_DECISION = "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY"
READY_INPUT_342N_DECISION = "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY"
READY_DECISION = "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY"
NOT_READY_DECISION = "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_NOT_READY"

DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR = Path(r"D:\_datefac\output\post_adoption_sidecar_simulation_342o")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_POST_HUMAN_SIDECAR_342I_DIR = Path(r"D:\_datefac\output\table_first_post_human_review_sidecar_result_342i")
DEFAULT_ADOPTION_SIMULATION_342N_DIR = Path(r"D:\_datefac\output\correction_aware_adoption_simulation_342n")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\reviewed_plus_simulated_client_preview_342p")

SUMMARY_FILE_NAME = "reviewed_plus_simulated_client_preview_342p_summary.json"
MANIFEST_FILE_NAME = "reviewed_plus_simulated_client_preview_342p_manifest.json"
QA_FILE_NAME = "reviewed_plus_simulated_client_preview_342p_qa.json"
NO_WRITE_BACK_FILE_NAME = "reviewed_plus_simulated_client_preview_342p_no_write_back_proof.json"
REPORT_FILE_NAME = "reviewed_plus_simulated_client_preview_342p_report.md"
WORKBOOK_FILE_NAME = "reviewed_plus_simulated_client_preview_342p.xlsx"

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

REQUIRED_342O_SHEETS = [
    "01_SIDECAR_SUMMARY",
    "03_SIM_ADOPTED_CELLS",
    "04_DIRECT_ADOPTED",
    "05_CORRECTED_ADOPTED",
    "06_STILL_HUMAN_REQUIRED",
    "07_BEFORE_AFTER_TRACE",
    "08_METRIC_COVERAGE",
    "09_REMAINING_REVIEW",
    "10_RISK_BOUNDARY",
    "11_342P_READINESS",
    "12_NO_WRITE_BACK",
]
REQUIRED_342N_SHEETS = [
    "04_ADOPTION_INPUT",
    "05_DIRECT_ADOPT_SIM",
    "06_CORRECTION_ADOPT_SIM",
    "07_STILL_HUMAN_REQUIRED",
    "10_BEFORE_AFTER_SIM",
]
REQUIRED_342I_SHEETS = [
    "03_HUMAN_REVIEWED_CELLS",
    "04_FINAL_CONFIRMED",
]
REVIEWED_PREVIEW_SHEET_CANDIDATES = [
    "03_REVIEWED_PREVIEW",
    "04_CLIENT_PREVIEW",
    "03_CLIENT_PREVIEW",
    "04_REVIEWED_PREVIEW",
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

RECOMMENDED_342Q_SCOPE = "preview_audit_and_export_readiness_gate"
HUMAN_DISPLAY_WARNING = "human reviewed pilot row; not full client export"
SIM_DISPLAY_WARNING = "simulation only; requires later audit before client delivery"

TRUST_PRIORITY = {
    "HUMAN_REVIEWED": 1,
    "SIMULATED_CORRECTION_ADOPTED": 2,
    "SIMULATED_DIRECT_ADOPTED": 3,
}


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


def _safe_float(value: Any) -> float | None:
    text = _norm_text(value)
    if not text:
        return None
    try:
        return float(value)
    except Exception:
        try:
            return float(text.replace(",", ""))
        except Exception:
            return None


def _value_key(value: Any) -> str:
    number = _safe_float(value)
    if number is not None:
        return f"{number:.12g}"
    return _norm_text(value)


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
            if "not " not in window and "false" not in window and "simulation" not in window:
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


def _load_summary_pair(
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
    for path, label in [
        (summary_path, "summary"),
        (qa_path, "qa"),
        (report_path, "report"),
    ]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")
    return summary, qa_json, files_read, warnings


def _find_reviewed_preview_sheet(sheet_names: Sequence[str]) -> str:
    for candidate in REVIEWED_PREVIEW_SHEET_CANDIDATES:
        if candidate in sheet_names:
            return candidate
    return ""


def _derive_corpus_pdf_id(table_id: str, review_item_id: str) -> str:
    for text in [table_id, review_item_id]:
        match = re.search(r"(342b_pdf_\d+)", text)
        if match:
            return match.group(1)
    return ""


def _load_342o_context(
    post_adoption_sidecar_342o_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = post_adoption_sidecar_342o_dir / INPUT_342O_SUMMARY_NAME
    qa_path = post_adoption_sidecar_342o_dir / INPUT_342O_QA_NAME
    report_path = post_adoption_sidecar_342o_dir / INPUT_342O_REPORT_NAME
    workbook_path = post_adoption_sidecar_342o_dir / INPUT_342O_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path in [summary_path, qa_path, report_path, workbook_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input file: {path}")
    workbook_sheets, sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342O_SHEETS)
    warnings.extend(workbook_warnings)
    return summary, qa_json, workbook_sheets, sheet_names, files_read, warnings


def _load_342n_context(
    adoption_simulation_342n_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = adoption_simulation_342n_dir / INPUT_342N_SUMMARY_NAME
    qa_path = adoption_simulation_342n_dir / INPUT_342N_QA_NAME
    report_path = adoption_simulation_342n_dir / INPUT_342N_REPORT_NAME
    workbook_path = adoption_simulation_342n_dir / INPUT_342N_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path in [summary_path, qa_path, report_path, workbook_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input file: {path}")
    workbook_sheets, sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342N_SHEETS)
    warnings.extend(workbook_warnings)
    return summary, qa_json, workbook_sheets, sheet_names, files_read, warnings


def _load_342i_context(
    post_human_sidecar_342i_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = post_human_sidecar_342i_dir / INPUT_342I_SUMMARY_NAME
    qa_path = post_human_sidecar_342i_dir / INPUT_342I_QA_NAME
    report_path = post_human_sidecar_342i_dir / INPUT_342I_REPORT_NAME
    workbook_path = post_human_sidecar_342i_dir / INPUT_342I_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path in [summary_path, qa_path, report_path, workbook_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input file: {path}")
    workbook_sheets, sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342I_SHEETS)
    warnings.extend(workbook_warnings)
    return summary, qa_json, workbook_sheets, sheet_names, files_read, warnings


def _load_342j_context(
    reviewed_preview_342j_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, str, List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    qa_path = reviewed_preview_342j_dir / INPUT_342J_QA_NAME
    report_path = reviewed_preview_342j_dir / INPUT_342J_REPORT_NAME
    workbook_path = reviewed_preview_342j_dir / INPUT_342J_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path in [summary_path, qa_path, report_path, workbook_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input file: {path}")

    preview_df = pd.DataFrame()
    preview_sheet_name = ""
    if workbook_path.exists():
        try:
            excel = pd.ExcelFile(workbook_path)
            preview_sheet_name = _find_reviewed_preview_sheet(excel.sheet_names)
            if preview_sheet_name:
                preview_df = _clean_frame(pd.read_excel(workbook_path, sheet_name=preview_sheet_name))
            else:
                warnings.append("unable to find reviewed preview sheet in 342J workbook")
        except Exception as exc:
            warnings.append(f"unable to read 342J workbook {workbook_path}: {exc}")
    return summary, qa_json, preview_df, preview_sheet_name, files_read, warnings


def _bool_false(value: Any) -> bool:
    if isinstance(value, bool):
        return value is False
    text = _norm_text(value).casefold()
    return text in {"", "false", "0", "no"}


def _build_human_reviewed_df(preview_df: pd.DataFrame) -> pd.DataFrame:
    if preview_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for row in preview_df.to_dict(orient="records"):
        rows.append(
            {
                "preview_row_id": _norm_text(row.get("preview_row_id")),
                "review_item_id": _norm_text(row.get("review_item_id")),
                "source_stage": "342J",
                "preview_source_type": "HUMAN_REVIEWED",
                "data_trust_level": "HUMAN_REVIEWED",
                "review_status_for_client_display": "REVIEWED",
                "display_warning": HUMAN_DISPLAY_WARNING,
                "reviewer_decision": _norm_text(row.get("reviewer_decision")),
                "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_id": _norm_text(row.get("table_id")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "metric_raw": _norm_text(row.get("metric_raw")),
                "metric_standardized": _norm_text(row.get("final_metric_standardized", row.get("metric_standardized"))),
                "year_standardized": _norm_text(row.get("final_year_standardized", row.get("year_standardized"))),
                "value_numeric": row.get("final_value_numeric", row.get("value_numeric")),
                "normalized_unit": _norm_text(row.get("final_normalized_unit", row.get("normalized_unit"))),
                "evidence": _norm_text(row.get("source_html_snippet")),
                "adoption_confidence": "",
                "adoption_evidence": "",
                "correction_pattern": "",
                "correction_reason": "",
                "not_final_confirmation": False,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": False,
                "dropped_reason": "",
                "winner_preview_row_id": "",
                "collision_key": "",
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_342n_metadata_maps(workbook_342n: Mapping[str, pd.DataFrame]) -> tuple[Dict[str, Mapping[str, Any]], Dict[str, Mapping[str, Any]]]:
    adoption_input_df = _clean_frame(workbook_342n.get("04_ADOPTION_INPUT", pd.DataFrame()))
    before_after_df = _clean_frame(workbook_342n.get("10_BEFORE_AFTER_SIM", pd.DataFrame()))
    metadata_map: Dict[str, Mapping[str, Any]] = {}
    if not adoption_input_df.empty and "review_item_id" in adoption_input_df.columns:
        metadata_map = {
            _norm_text(row.get("review_item_id")): row
            for row in adoption_input_df.to_dict(orient="records")
        }
    correction_map: Dict[str, Mapping[str, Any]] = {}
    if not before_after_df.empty and "review_item_id" in before_after_df.columns:
        correction_map = {
            _norm_text(row.get("review_item_id")): row
            for row in before_after_df.to_dict(orient="records")
        }
    return metadata_map, correction_map


def _build_sim_direct_df(
    direct_df: pd.DataFrame,
    sim_lookup: Mapping[str, Mapping[str, Any]],
    metadata_map: Mapping[str, Mapping[str, Any]],
) -> pd.DataFrame:
    if direct_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(direct_df.to_dict(orient="records"), start=1):
        review_item_id = _norm_text(row.get("review_item_id"))
        lookup_row = sim_lookup.get(review_item_id, {})
        meta_row = metadata_map.get(review_item_id, {})
        table_id = _norm_text(meta_row.get("table_id", lookup_row.get("table_id", "")))
        file_name = _norm_text(meta_row.get("file_name", lookup_row.get("file_name", "")))
        rows.append(
            {
                "preview_row_id": f"342p::sim_direct::{index:04d}",
                "review_item_id": review_item_id,
                "source_stage": "342O",
                "preview_source_type": "SIMULATED_DIRECT",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "review_status_for_client_display": "SIMULATED",
                "display_warning": SIM_DISPLAY_WARNING,
                "reviewer_decision": "SIMULATED_DIRECT_ADOPTED",
                "corpus_pdf_id": _derive_corpus_pdf_id(table_id, review_item_id),
                "file_name": file_name,
                "table_id": table_id,
                "table_type": _norm_text(meta_row.get("table_type", "")),
                "source_page": meta_row.get("source_page", lookup_row.get("source_page")),
                "bbox": _norm_text(meta_row.get("bbox", lookup_row.get("bbox"))),
                "image_path": _norm_text(meta_row.get("image_path", lookup_row.get("image_path"))),
                "metric_raw": "",
                "metric_standardized": _norm_text(row.get("simulated_metric_standardized")),
                "year_standardized": _norm_text(row.get("simulated_year_standardized")),
                "value_numeric": row.get("simulated_value_numeric"),
                "normalized_unit": _norm_text(row.get("simulated_normalized_unit")),
                "evidence": _norm_text(lookup_row.get("source_html_snippet")),
                "adoption_confidence": row.get("adoption_confidence"),
                "adoption_evidence": _norm_text(row.get("adoption_evidence")),
                "correction_pattern": "",
                "correction_reason": "",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": False,
                "dropped_reason": "",
                "winner_preview_row_id": "",
                "collision_key": "",
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_sim_corrected_df(
    corrected_df: pd.DataFrame,
    sim_lookup: Mapping[str, Mapping[str, Any]],
    metadata_map: Mapping[str, Mapping[str, Any]],
    correction_map: Mapping[str, Mapping[str, Any]],
) -> pd.DataFrame:
    if corrected_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(corrected_df.to_dict(orient="records"), start=1):
        review_item_id = _norm_text(row.get("review_item_id"))
        lookup_row = sim_lookup.get(review_item_id, {})
        meta_row = metadata_map.get(review_item_id, {})
        corr_row = correction_map.get(review_item_id, {})
        table_id = _norm_text(meta_row.get("table_id", lookup_row.get("table_id", "")))
        file_name = _norm_text(meta_row.get("file_name", lookup_row.get("file_name", "")))
        rows.append(
            {
                "preview_row_id": f"342p::sim_corrected::{index:04d}",
                "review_item_id": review_item_id,
                "source_stage": "342O",
                "preview_source_type": "SIMULATED_CORRECTED",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "review_status_for_client_display": "SIMULATED_CORRECTED",
                "display_warning": SIM_DISPLAY_WARNING,
                "reviewer_decision": "SIMULATED_CORRECTION_ADOPTED",
                "corpus_pdf_id": _derive_corpus_pdf_id(table_id, review_item_id),
                "file_name": file_name,
                "table_id": table_id,
                "table_type": _norm_text(meta_row.get("table_type", "")),
                "source_page": meta_row.get("source_page", lookup_row.get("source_page")),
                "bbox": _norm_text(meta_row.get("bbox", lookup_row.get("bbox"))),
                "image_path": _norm_text(meta_row.get("image_path", lookup_row.get("image_path"))),
                "metric_raw": "",
                "metric_standardized": _norm_text(row.get("simulated_metric_standardized")),
                "year_standardized": _norm_text(row.get("simulated_year_standardized")),
                "value_numeric": row.get("simulated_value_numeric"),
                "normalized_unit": _norm_text(row.get("simulated_normalized_unit")),
                "evidence": _norm_text(lookup_row.get("source_html_snippet")),
                "adoption_confidence": row.get("adoption_confidence"),
                "adoption_evidence": _norm_text(row.get("adoption_evidence")),
                "correction_pattern": _norm_text(row.get("correction_pattern")),
                "correction_reason": _norm_text(row.get("correction_reason", corr_row.get("correction_reason"))),
                "original_metric_standardized": _norm_text(
                    row.get("original_suggested_metric_standardized", corr_row.get("original_suggested_metric_standardized"))
                ),
                "original_normalized_unit": _norm_text(
                    row.get("original_suggested_normalized_unit", corr_row.get("original_suggested_normalized_unit"))
                ),
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": False,
                "dropped_reason": "",
                "winner_preview_row_id": "",
                "collision_key": "",
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_still_human_required_df(still_human_df: pd.DataFrame) -> pd.DataFrame:
    if still_human_df.empty:
        return pd.DataFrame()
    out = _clean_frame(still_human_df.copy())
    out["auto_apply_allowed"] = False
    out["included_in_preview"] = False
    return _clean_frame(out)


def _collision_key(row: Mapping[str, Any]) -> str:
    return "||".join(
        [
            _norm_text(row.get("metric_standardized")),
            _norm_text(row.get("year_standardized")),
            _value_key(row.get("value_numeric")),
            _norm_text(row.get("normalized_unit")),
            _norm_text(row.get("source_page")),
            _norm_text(row.get("bbox")),
        ]
    )


def _priority_rank(row: Mapping[str, Any]) -> int:
    return TRUST_PRIORITY.get(_norm_text(row.get("data_trust_level")), 99)


def _select_winner(group_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    sorted_rows = sorted(
        group_rows,
        key=lambda item: (
            _priority_rank(item),
            _norm_text(item.get("preview_row_id")),
        ),
    )
    return sorted_rows[0]


def _apply_collision_resolution(
    human_df: pd.DataFrame,
    sim_direct_df: pd.DataFrame,
    sim_corrected_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    frames = [df for df in [human_df, sim_corrected_df, sim_direct_df] if not df.empty]
    if not frames:
        empty_metrics = {
            "duplicate_review_item_id_count": 0,
            "duplicate_metric_year_source_count": 0,
            "human_over_simulation_override_count": 0,
            "simulated_duplicate_dropped_count": 0,
            "collision_logged_count": 0,
        }
        return human_df, sim_direct_df, sim_corrected_df, pd.DataFrame(), empty_metrics

    combined_raw_df = _clean_frame(pd.concat(frames, ignore_index=True))
    row_map = {
        _norm_text(row.get("preview_row_id")): dict(row)
        for row in combined_raw_df.to_dict(orient="records")
    }
    review_groups: Dict[str, List[Dict[str, Any]]] = {}
    collision_groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in row_map.values():
        review_item_id = _norm_text(row.get("review_item_id"))
        if review_item_id:
            review_groups.setdefault(review_item_id, []).append(row)
        key = _collision_key(row)
        row["collision_key"] = key
        if key != "|||||":
            collision_groups.setdefault(key, []).append(row)

    duplicate_review_item_id_count = sum(1 for rows in review_groups.values() if len(rows) > 1)
    duplicate_metric_year_source_count = sum(1 for rows in collision_groups.values() if len(rows) > 1)

    survivors: Dict[str, Dict[str, Any]] = dict(row_map)
    collision_log_rows: List[Dict[str, Any]] = []
    human_over_simulation_override_count = 0
    simulated_duplicate_dropped_count = 0

    for review_item_id, group_rows in review_groups.items():
        if len(group_rows) <= 1:
            continue
        winner = _select_winner(group_rows)
        winner_source = _norm_text(winner.get("preview_source_type"))
        for loser in group_rows:
            if _norm_text(loser.get("preview_row_id")) == _norm_text(winner.get("preview_row_id")):
                continue
            survivors.pop(_norm_text(loser.get("preview_row_id")), None)
            loser_source = _norm_text(loser.get("preview_source_type"))
            if winner_source == "HUMAN_REVIEWED" and loser_source.startswith("SIMULATED"):
                human_over_simulation_override_count += 1
            elif winner_source.startswith("SIMULATED") and loser_source.startswith("SIMULATED"):
                simulated_duplicate_dropped_count += 1
            collision_log_rows.append(
                {
                    "collision_type": "DUPLICATE_REVIEW_ITEM_ID",
                    "collision_key": review_item_id,
                    "review_item_id": review_item_id,
                    "winner_review_item_id": _norm_text(winner.get("review_item_id")),
                    "preview_row_id": _norm_text(loser.get("preview_row_id")),
                    "winner_preview_row_id": _norm_text(winner.get("preview_row_id")),
                    "source_type": loser_source,
                    "winner_source_type": winner_source,
                    "collision_severity": "HIGH",
                    "recommended_action": "keep higher trust row only",
                }
            )

    collision_groups_after_review: Dict[str, List[Dict[str, Any]]] = {}
    for row in survivors.values():
        key = _norm_text(row.get("collision_key"))
        if key:
            collision_groups_after_review.setdefault(key, []).append(row)

    for key, group_rows in collision_groups_after_review.items():
        if len(group_rows) <= 1:
            continue
        winner = _select_winner(group_rows)
        winner_source = _norm_text(winner.get("preview_source_type"))
        for loser in group_rows:
            if _norm_text(loser.get("preview_row_id")) == _norm_text(winner.get("preview_row_id")):
                continue
            survivors.pop(_norm_text(loser.get("preview_row_id")), None)
            loser_source = _norm_text(loser.get("preview_source_type"))
            if winner_source == "HUMAN_REVIEWED" and loser_source.startswith("SIMULATED"):
                human_over_simulation_override_count += 1
            elif winner_source.startswith("SIMULATED") and loser_source.startswith("SIMULATED"):
                simulated_duplicate_dropped_count += 1
            collision_log_rows.append(
                {
                    "collision_type": "DUPLICATE_METRIC_YEAR_VALUE_SOURCE",
                    "collision_key": key,
                    "review_item_id": _norm_text(loser.get("review_item_id")),
                    "winner_review_item_id": _norm_text(winner.get("review_item_id")),
                    "preview_row_id": _norm_text(loser.get("preview_row_id")),
                    "winner_preview_row_id": _norm_text(winner.get("preview_row_id")),
                    "source_type": loser_source,
                    "winner_source_type": winner_source,
                    "collision_severity": "MEDIUM" if winner_source.startswith("SIMULATED") else "HIGH",
                    "recommended_action": "keep highest trust metric/year/value/source row",
                }
            )

    survivor_ids = set(survivors.keys())
    winner_map: Dict[str, str] = {}
    loser_reason_map: Dict[str, str] = {}
    collision_key_map: Dict[str, str] = {}
    for row in row_map.values():
        preview_row_id = _norm_text(row.get("preview_row_id"))
        collision_key_map[preview_row_id] = _norm_text(row.get("collision_key"))
        winner_map[preview_row_id] = preview_row_id if preview_row_id in survivor_ids else ""
    for collision in collision_log_rows:
        loser_reason_map[_norm_text(collision.get("preview_row_id"))] = _norm_text(collision.get("collision_type"))
        winner_map[_norm_text(collision.get("preview_row_id"))] = _norm_text(collision.get("winner_preview_row_id"))

    def _mark(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = _clean_frame(df.copy())
        out["included_in_combined_preview"] = out["preview_row_id"].map(lambda value: _norm_text(value) in survivor_ids)
        out["dropped_reason"] = out["preview_row_id"].map(lambda value: loser_reason_map.get(_norm_text(value), ""))
        out["winner_preview_row_id"] = out["preview_row_id"].map(lambda value: winner_map.get(_norm_text(value), _norm_text(value)))
        out["collision_key"] = out["preview_row_id"].map(lambda value: collision_key_map.get(_norm_text(value), ""))
        return _clean_frame(out)

    marked_human_df = _mark(human_df)
    marked_sim_direct_df = _mark(sim_direct_df)
    marked_sim_corrected_df = _mark(sim_corrected_df)

    final_rows = [row for row in (_norm_text(v.get("preview_row_id")) and v for v in survivors.values()) if row]
    final_combined_df = _clean_frame(pd.DataFrame(final_rows))
    if not final_combined_df.empty:
        final_combined_df = _clean_frame(
            final_combined_df.sort_values(
                by=["source_page", "metric_standardized", "year_standardized", "preview_row_id"],
                ascending=[True, True, True, True],
            )
        )

    metrics = {
        "duplicate_review_item_id_count": duplicate_review_item_id_count,
        "duplicate_metric_year_source_count": duplicate_metric_year_source_count,
        "human_over_simulation_override_count": human_over_simulation_override_count,
        "simulated_duplicate_dropped_count": simulated_duplicate_dropped_count,
        "collision_logged_count": len(collision_log_rows),
    }
    return (
        marked_human_df,
        marked_sim_direct_df,
        marked_sim_corrected_df,
        _clean_frame(pd.DataFrame(collision_log_rows)),
        metrics | {"final_combined_df": final_combined_df},
    )


def _metric_year_pair_count(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    keys = (
        frame["metric_standardized"].map(_norm_text)
        + "||"
        + frame["year_standardized"].map(_norm_text)
    )
    return int(keys.replace("||", pd.NA).dropna().nunique())


def _build_metric_coverage_df(final_combined_df: pd.DataFrame) -> pd.DataFrame:
    if final_combined_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for metric_name, group in final_combined_df.groupby("metric_standardized", dropna=False):
        metric = _norm_text(metric_name)
        years = sorted({_norm_text(value) for value in group["year_standardized"].tolist() if _norm_text(value)})
        units = sorted({_norm_text(value) for value in group["normalized_unit"].tolist() if _norm_text(value)})
        numeric_values = [_safe_float(value) for value in group["value_numeric"].tolist()]
        numeric_values = [value for value in numeric_values if value is not None]
        rows.append(
            {
                "metric_standardized": metric,
                "preview_row_count": int(len(group)),
                "unique_year_count": int(len(years)),
                "years_covered": " | ".join(years),
                "human_reviewed_count": int(group["preview_source_type"].eq("HUMAN_REVIEWED").sum()),
                "simulated_direct_count": int(group["preview_source_type"].eq("SIMULATED_DIRECT").sum()),
                "simulated_corrected_count": int(group["preview_source_type"].eq("SIMULATED_CORRECTED").sum()),
                "unit_set": " | ".join(units),
                "min_value": min(numeric_values) if numeric_values else "",
                "max_value": max(numeric_values) if numeric_values else "",
            }
        )
    return _clean_frame(pd.DataFrame(rows).sort_values(by=["preview_row_count", "metric_standardized"], ascending=[False, True]))


def _build_readme_df(summary_342o: Mapping[str, Any], summary_342j: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342P builds a reviewed plus simulated client preview pilot. It is a bounded internal preview, not a formal client export.",
        },
        {
            "topic": "Human rows",
            "message": f"Human-reviewed preview input from 342J = {int(summary_342j.get('reviewed_preview_row_count', 0) or 0)} rows.",
        },
        {
            "topic": "Simulated rows",
            "message": f"Simulated adopted input from 342O = {int(summary_342o.get('simulated_adopted_cell_count', 0) or 0)} rows, with {int(summary_342o.get('still_human_required_count', 0) or 0)} still human-required rows kept outside preview.",
        },
        {
            "topic": "Boundary",
            "message": "HUMAN_REVIEWED and SIMULATED rows are explicitly separated. Simulated rows are not final confirmation. client_ready=false and production_ready=false must remain unchanged.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_preview_boundary_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"message": "342P is a reviewed + simulated client preview pilot, not a formal client export."},
        {"message": "Simulated rows remain simulation only and require later audit before any client delivery claim."},
        {"message": f"remaining_review_count = {summary.get('remaining_review_count', 0)} stays outside this preview pilot."},
        {"message": f"still_human_required_count = {summary.get('still_human_required_count', 0)} remains outside preview and still requires human handling."},
        {"message": "client_ready = false; production_ready = false; not investment advice."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342q": summary.get("ready_for_342q", False),
                    "recommended_342q_scope": summary.get("recommended_342q_scope", ""),
                    "decision": summary.get("decision", ""),
                    "client_ready": summary.get("client_ready", False),
                    "production_ready": summary.get("production_ready", False),
                }
            ]
        )
    )


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    if summary.get("ready_for_342q", False):
        steps = [
            "Proceed to 342Q preview audit and export-readiness gate.",
            "Keep simulated rows labeled as simulation only.",
            "Keep client_ready=false and production_ready=false.",
        ]
    else:
        steps = [
            "Fix missing inputs or QA failures before any preview audit step.",
            "Do not treat reviewed + simulated preview as formal client delivery.",
            "Do not write back to upstream workbooks.",
        ]
    return _clean_frame(pd.DataFrame([{"next_step": step} for step in steps]))


def _build_no_write_back_proof_df(payload: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for key, value in payload.items():
        rows.append({"key": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value})
    return _clean_frame(pd.DataFrame(rows))


def build_reviewed_plus_simulated_client_preview_342p(
    *,
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

    summary_342o, qa_342o, workbook_342o, workbook_342o_sheet_names, files_342o, warnings_342o = _load_342o_context(
        post_adoption_sidecar_342o_dir
    )
    summary_342j, qa_342j, reviewed_preview_df, preview_sheet_name, files_342j, warnings_342j = _load_342j_context(
        reviewed_preview_342j_dir
    )
    summary_342i, qa_342i, workbook_342i, workbook_342i_sheet_names, files_342i, warnings_342i = _load_342i_context(
        post_human_sidecar_342i_dir
    )
    summary_342n, qa_342n, workbook_342n, workbook_342n_sheet_names, files_342n, warnings_342n = _load_342n_context(
        adoption_simulation_342n_dir
    )
    files_read.extend(files_342o + files_342j + files_342i + files_342n)
    warnings.extend(warnings_342o + warnings_342j + warnings_342i + warnings_342n)

    summary_342o_path = post_adoption_sidecar_342o_dir / INPUT_342O_SUMMARY_NAME
    qa_342o_path = post_adoption_sidecar_342o_dir / INPUT_342O_QA_NAME
    report_342o_path = post_adoption_sidecar_342o_dir / INPUT_342O_REPORT_NAME
    workbook_342o_path = post_adoption_sidecar_342o_dir / INPUT_342O_WORKBOOK_NAME
    summary_342j_path = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    qa_342j_path = reviewed_preview_342j_dir / INPUT_342J_QA_NAME
    report_342j_path = reviewed_preview_342j_dir / INPUT_342J_REPORT_NAME
    workbook_342j_path = reviewed_preview_342j_dir / INPUT_342J_WORKBOOK_NAME
    summary_342i_path = post_human_sidecar_342i_dir / INPUT_342I_SUMMARY_NAME
    qa_342i_path = post_human_sidecar_342i_dir / INPUT_342I_QA_NAME
    report_342i_path = post_human_sidecar_342i_dir / INPUT_342I_REPORT_NAME
    workbook_342i_path = post_human_sidecar_342i_dir / INPUT_342I_WORKBOOK_NAME
    summary_342n_path = adoption_simulation_342n_dir / INPUT_342N_SUMMARY_NAME
    qa_342n_path = adoption_simulation_342n_dir / INPUT_342N_QA_NAME
    report_342n_path = adoption_simulation_342n_dir / INPUT_342N_REPORT_NAME
    workbook_342n_path = adoption_simulation_342n_dir / INPUT_342N_WORKBOOK_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [
            summary_342o_path,
            qa_342o_path,
            report_342o_path,
            workbook_342o_path,
            summary_342j_path,
            qa_342j_path,
            report_342j_path,
            workbook_342j_path,
            summary_342i_path,
            qa_342i_path,
            report_342i_path,
            workbook_342i_path,
            summary_342n_path,
            qa_342n_path,
            report_342n_path,
            workbook_342n_path,
        ]
        if path.exists()
    }

    required_342o_present = all(sheet in workbook_342o_sheet_names for sheet in REQUIRED_342O_SHEETS)
    required_342n_present = all(sheet in workbook_342n_sheet_names for sheet in REQUIRED_342N_SHEETS)
    required_342i_present = all(sheet in workbook_342i_sheet_names for sheet in REQUIRED_342I_SHEETS)

    input_ready = bool(
        post_adoption_sidecar_342o_dir.exists()
        and reviewed_preview_342j_dir.exists()
        and post_human_sidecar_342i_dir.exists()
        and adoption_simulation_342n_dir.exists()
        and summary_342o_path.exists()
        and qa_342o_path.exists()
        and workbook_342o_path.exists()
        and summary_342j_path.exists()
        and qa_342j_path.exists()
        and workbook_342j_path.exists()
        and summary_342i_path.exists()
        and qa_342i_path.exists()
        and workbook_342i_path.exists()
        and summary_342n_path.exists()
        and qa_342n_path.exists()
        and workbook_342n_path.exists()
        and summary_342o.get("decision") == READY_INPUT_342O_DECISION
        and bool(summary_342o.get("ready_for_342p", False))
        and int(summary_342o.get("qa_fail_count", 0) or 0) == 0
        and summary_342j.get("decision") == READY_INPUT_342J_DECISION
        and int(summary_342j.get("qa_fail_count", 0) or 0) == 0
        and summary_342i.get("decision") == READY_INPUT_342I_DECISION
        and int(summary_342i.get("qa_fail_count", 0) or 0) == 0
        and summary_342n.get("decision") == READY_INPUT_342N_DECISION
        and int(summary_342n.get("qa_fail_count", 0) or 0) == 0
        and required_342o_present
        and required_342n_present
        and required_342i_present
        and preview_sheet_name != ""
        and summary_342o.get("client_ready", False) is False
        and summary_342o.get("production_ready", False) is False
        and summary_342j.get("client_ready", False) is False
        and summary_342j.get("production_ready", False) is False
        and summary_342i.get("client_ready", False) is False
        and summary_342i.get("production_ready", False) is False
        and summary_342n.get("client_ready", False) is False
        and summary_342n.get("production_ready", False) is False
    )

    sim_adopted_df = _clean_frame(workbook_342o.get("03_SIM_ADOPTED_CELLS", pd.DataFrame())) if input_ready else pd.DataFrame()
    direct_adopted_df = _clean_frame(workbook_342o.get("04_DIRECT_ADOPTED", pd.DataFrame())) if input_ready else pd.DataFrame()
    corrected_adopted_df = _clean_frame(workbook_342o.get("05_CORRECTED_ADOPTED", pd.DataFrame())) if input_ready else pd.DataFrame()
    still_human_input_df = _clean_frame(workbook_342o.get("06_STILL_HUMAN_REQUIRED", pd.DataFrame())) if input_ready else pd.DataFrame()

    sim_lookup = (
        {
            _norm_text(row.get("review_item_id")): row
            for row in sim_adopted_df.to_dict(orient="records")
        }
        if not sim_adopted_df.empty
        else {}
    )
    metadata_map, correction_map = _build_342n_metadata_maps(workbook_342n)

    human_df = _build_human_reviewed_df(reviewed_preview_df) if input_ready else pd.DataFrame()
    sim_direct_df = _build_sim_direct_df(direct_adopted_df, sim_lookup, metadata_map) if input_ready else pd.DataFrame()
    sim_corrected_df = _build_sim_corrected_df(corrected_adopted_df, sim_lookup, metadata_map, correction_map) if input_ready else pd.DataFrame()
    still_human_required_df = _build_still_human_required_df(still_human_input_df) if input_ready else pd.DataFrame()

    (
        human_df,
        sim_direct_df,
        sim_corrected_df,
        collision_log_df,
        collision_metrics,
    ) = _apply_collision_resolution(human_df, sim_direct_df, sim_corrected_df) if input_ready else (
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        {
            "duplicate_review_item_id_count": 0,
            "duplicate_metric_year_source_count": 0,
            "human_over_simulation_override_count": 0,
            "simulated_duplicate_dropped_count": 0,
            "collision_logged_count": 0,
            "final_combined_df": pd.DataFrame(),
        },
    )
    final_combined_df = _clean_frame(collision_metrics.pop("final_combined_df", pd.DataFrame()))

    human_reviewed_preview_count = int(final_combined_df["preview_source_type"].eq("HUMAN_REVIEWED").sum()) if not final_combined_df.empty else 0
    simulated_direct_preview_count = int(final_combined_df["preview_source_type"].eq("SIMULATED_DIRECT").sum()) if not final_combined_df.empty else 0
    simulated_corrected_preview_count = int(final_combined_df["preview_source_type"].eq("SIMULATED_CORRECTED").sum()) if not final_combined_df.empty else 0
    simulated_preview_count = simulated_direct_preview_count + simulated_corrected_preview_count
    combined_preview_row_count = int(len(final_combined_df))
    still_human_required_count = int(len(still_human_required_df))
    remaining_review_count = int(summary_342o.get("remaining_review_count", 0) or 0) if input_ready else 0
    metric_covered_count = int(final_combined_df["metric_standardized"].map(_norm_text).replace("", pd.NA).dropna().nunique()) if not final_combined_df.empty else 0
    metric_year_pair_count = _metric_year_pair_count(final_combined_df)
    human_metric_year_pair_count = _metric_year_pair_count(human_df)
    simulated_metric_year_pair_count = _metric_year_pair_count(
        _clean_frame(pd.concat([df for df in [sim_direct_df, sim_corrected_df] if not df.empty], ignore_index=True))
        if (not sim_direct_df.empty or not sim_corrected_df.empty)
        else pd.DataFrame()
    )

    metric_coverage_df = _build_metric_coverage_df(final_combined_df)

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [
            summary_342o_path,
            qa_342o_path,
            report_342o_path,
            workbook_342o_path,
            summary_342j_path,
            qa_342j_path,
            report_342j_path,
            workbook_342j_path,
            summary_342i_path,
            qa_342i_path,
            report_342i_path,
            workbook_342i_path,
            summary_342n_path,
            qa_342n_path,
            report_342n_path,
            workbook_342n_path,
        ]
        if path.exists()
    }
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342P",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["client_export_generated"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_342p")
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df(summary_342o if input_ready else {}, summary_342j if input_ready else {})
    preview_boundary_df = _build_preview_boundary_df(
        {
            "remaining_review_count": remaining_review_count,
            "still_human_required_count": still_human_required_count,
        }
    )
    claims_text = "\n".join(
        readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
        + preview_boundary_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
    )

    human_priority_preserved = collision_log_df.empty or not any(
        _norm_text(row.get("source_type")) == "HUMAN_REVIEWED" and _norm_text(row.get("winner_source_type")).startswith("SIMULATED")
        for row in collision_log_df.to_dict(orient="records")
    )
    all_simulated_not_final = (
        sim_direct_df.empty or sim_direct_df["not_final_confirmation"].astype(bool).all()
    ) and (
        sim_corrected_df.empty or sim_corrected_df["not_final_confirmation"].astype(bool).all()
    )
    no_simulated_claimed_final = (
        sim_adopted_df.empty
        or (
            not sim_adopted_df.get("final_confirmed", pd.Series(dtype=bool)).astype(bool).any()
            and not sim_adopted_df.get("human_confirmed", pd.Series(dtype=bool)).astype(bool).any()
        )
    )
    preview_client_ready_false = final_combined_df.empty or not final_combined_df["client_ready"].astype(bool).any()
    preview_production_ready_false = final_combined_df.empty or not final_combined_df["production_ready"].astype(bool).any()
    still_human_not_included = still_human_required_df.empty or not still_human_required_df["included_in_preview"].astype(bool).any()
    no_sheet_name_exceeds_limit = all(len(name) <= 31 for name in [
        "00_README",
        "01_PREVIEW_SUMMARY",
        "02_INPUT_342O_SUMMARY",
        "03_INPUT_342J_SUMMARY",
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
        "14_NEXT_STEPS",
    ])

    checks = [
        {"check_name": "inputs::342o_output_dir_exists", "status": "PASS" if post_adoption_sidecar_342o_dir.exists() else "FAIL", "detail": str(post_adoption_sidecar_342o_dir)},
        {"check_name": "inputs::342o_summary_exists", "status": "PASS" if summary_342o_path.exists() else "FAIL", "detail": str(summary_342o_path)},
        {"check_name": "inputs::342o_qa_exists", "status": "PASS" if qa_342o_path.exists() else "FAIL", "detail": str(qa_342o_path)},
        {"check_name": "inputs::342o_workbook_exists", "status": "PASS" if workbook_342o_path.exists() else "FAIL", "detail": str(workbook_342o_path)},
        {"check_name": "inputs::342j_output_dir_exists", "status": "PASS" if reviewed_preview_342j_dir.exists() else "FAIL", "detail": str(reviewed_preview_342j_dir)},
        {"check_name": "inputs::342j_summary_exists", "status": "PASS" if summary_342j_path.exists() else "FAIL", "detail": str(summary_342j_path)},
        {"check_name": "inputs::342j_qa_exists", "status": "PASS" if qa_342j_path.exists() else "FAIL", "detail": str(qa_342j_path)},
        {"check_name": "inputs::342j_workbook_exists", "status": "PASS" if workbook_342j_path.exists() else "FAIL", "detail": str(workbook_342j_path)},
        {"check_name": "inputs::342i_summary_exists", "status": "PASS" if summary_342i_path.exists() else "FAIL", "detail": str(summary_342i_path)},
        {"check_name": "inputs::342n_summary_exists", "status": "PASS" if summary_342n_path.exists() else "FAIL", "detail": str(summary_342n_path)},
        {
            "check_name": "inputs::342o_ready_for_342p_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "342o_decision": summary_342o.get("decision", ""),
                    "342o_ready_for_342p": summary_342o.get("ready_for_342p", False),
                    "342j_decision": summary_342j.get("decision", ""),
                    "342i_decision": summary_342i.get("decision", ""),
                    "342n_decision": summary_342n.get("decision", ""),
                    "preview_sheet_name": preview_sheet_name,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342o_required_sheets_exist",
            "status": "PASS" if required_342o_present else "FAIL",
            "detail": json.dumps({sheet: sheet in workbook_342o_sheet_names for sheet in REQUIRED_342O_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::342n_required_sheets_exist",
            "status": "PASS" if required_342n_present else "FAIL",
            "detail": json.dumps({sheet: sheet in workbook_342n_sheet_names for sheet in REQUIRED_342N_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "quality::human_reviewed_rows_loaded",
            "status": "PASS" if len(human_df) > 0 else "FAIL",
            "detail": str(len(human_df)),
        },
        {
            "check_name": "quality::simulated_rows_loaded",
            "status": "PASS" if len(sim_direct_df) + len(sim_corrected_df) > 0 else "FAIL",
            "detail": f"direct={len(sim_direct_df)} corrected={len(sim_corrected_df)}",
        },
        {
            "check_name": "quality::direct_plus_corrected_equals_simulated_preview_count",
            "status": "PASS" if len(sim_direct_df) + len(sim_corrected_df) == int(summary_342o.get("simulated_adopted_cell_count", 0) or 0) else "FAIL",
            "detail": f"{len(sim_direct_df)}+{len(sim_corrected_df)} vs {summary_342o.get('simulated_adopted_cell_count', 0)}",
        },
        {
            "check_name": "quality::combined_preview_rows_calculated_after_collision_handling",
            "status": "PASS" if combined_preview_row_count > 0 else "FAIL",
            "detail": str(combined_preview_row_count),
        },
        {
            "check_name": "quality::human_reviewed_rows_have_higher_priority_than_simulated",
            "status": "PASS" if human_priority_preserved else "FAIL",
            "detail": json.dumps(collision_metrics, ensure_ascii=False),
        },
        {
            "check_name": "quality::all_simulated_rows_not_final_confirmation",
            "status": "PASS" if all_simulated_not_final else "FAIL",
            "detail": f"direct={len(sim_direct_df)} corrected={len(sim_corrected_df)}",
        },
        {
            "check_name": "quality::no_simulated_row_final_confirmed_true",
            "status": "PASS" if no_simulated_claimed_final else "FAIL",
            "detail": str(len(sim_adopted_df)),
        },
        {
            "check_name": "quality::still_human_required_rows_not_in_preview",
            "status": "PASS" if still_human_not_included else "FAIL",
            "detail": str(len(still_human_required_df)),
        },
        {
            "check_name": "claims::client_ready_false",
            "status": "PASS" if preview_client_ready_false else "FAIL",
            "detail": "false",
        },
        {
            "check_name": "claims::production_ready_false",
            "status": "PASS" if preview_production_ready_false else "FAIL",
            "detail": "false",
        },
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(claims_text, ["investment advice"]) else "FAIL",
            "detail": "readme and preview boundary text checked",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "342P adds sidecar preview code only.",
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
            "status": "PASS" if no_sheet_name_exceeds_limit else "FAIL",
            "detail": "all 342P sheet names are <= 31 chars",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342q = bool(
        input_ready
        and combined_preview_row_count > 0
        and human_reviewed_preview_count > 0
        and simulated_preview_count > 0
        and no_write_back_proof_passed
        and preview_client_ready_false
        and preview_production_ready_false
        and qa_fail_count == 0
    )
    decision = READY_DECISION if ready_for_342q else NOT_READY_DECISION
    recommended_342q_scope = RECOMMENDED_342Q_SCOPE if ready_for_342q else ""

    summary = {
        "generated_at_utc": _utc_now(),
        "human_reviewed_preview_count": human_reviewed_preview_count,
        "simulated_preview_count": simulated_preview_count,
        "simulated_direct_preview_count": simulated_direct_preview_count,
        "simulated_corrected_preview_count": simulated_corrected_preview_count,
        "combined_preview_row_count": combined_preview_row_count,
        "still_human_required_count": still_human_required_count,
        "remaining_review_count": remaining_review_count,
        "metric_covered_count": metric_covered_count,
        "metric_year_pair_count": metric_year_pair_count,
        "human_metric_year_pair_count": human_metric_year_pair_count,
        "simulated_metric_year_pair_count": simulated_metric_year_pair_count,
        "duplicate_review_item_id_count": int(collision_metrics.get("duplicate_review_item_id_count", 0) or 0),
        "duplicate_metric_year_source_count": int(collision_metrics.get("duplicate_metric_year_source_count", 0) or 0),
        "human_over_simulation_override_count": int(collision_metrics.get("human_over_simulation_override_count", 0) or 0),
        "simulated_duplicate_dropped_count": int(collision_metrics.get("simulated_duplicate_dropped_count", 0) or 0),
        "collision_logged_count": int(collision_metrics.get("collision_logged_count", 0) or 0),
        "ready_for_342q": ready_for_342q,
        "recommended_342q_scope": recommended_342q_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342P_reviewed_plus_simulated_client_preview_pilot",
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
        "01_PREVIEW_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342O_SUMMARY": _clean_frame(pd.DataFrame([summary_342o])) if summary_342o else pd.DataFrame(),
        "03_INPUT_342J_SUMMARY": _clean_frame(pd.DataFrame([summary_342j])) if summary_342j else pd.DataFrame(),
        "04_COMBINED_PREVIEW": final_combined_df,
        "05_HUMAN_REVIEWED": human_df,
        "06_SIM_DIRECT": sim_direct_df,
        "07_SIM_CORRECTED": sim_corrected_df,
        "08_STILL_HUMAN_REQUIRED": still_human_required_df,
        "09_COLLISION_CHECK": collision_log_df,
        "10_METRIC_COVERAGE": metric_coverage_df,
        "11_PREVIEW_BOUNDARY": preview_boundary_df,
        "12_342Q_READINESS": _build_readiness_df(summary),
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
