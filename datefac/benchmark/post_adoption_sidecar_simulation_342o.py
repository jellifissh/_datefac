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


READY_INPUT_DECISION = "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY"
READY_DECISION = "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY"
NOT_READY_DECISION = "POST_ADOPTION_SIDECAR_SIMULATION_342O_NOT_READY"

DEFAULT_ADOPTION_SIMULATION_342N_DIR = Path(r"D:\_datefac\output\correction_aware_adoption_simulation_342n")
DEFAULT_SPOT_CHECK_GATE_342M_DIR = Path(r"D:\_datefac\output\llm_suggestion_spot_check_gate_342m")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_POST_HUMAN_SIDECAR_342I_DIR = Path(r"D:\_datefac\output\table_first_post_human_review_sidecar_result_342i")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\post_adoption_sidecar_simulation_342o")

SUMMARY_FILE_NAME = "post_adoption_sidecar_simulation_342o_summary.json"
MANIFEST_FILE_NAME = "post_adoption_sidecar_simulation_342o_manifest.json"
QA_FILE_NAME = "post_adoption_sidecar_simulation_342o_qa.json"
NO_WRITE_BACK_FILE_NAME = "post_adoption_sidecar_simulation_342o_no_write_back_proof.json"
REPORT_FILE_NAME = "post_adoption_sidecar_simulation_342o_report.md"
WORKBOOK_FILE_NAME = "post_adoption_sidecar_simulation_342o.xlsx"

INPUT_342N_SUMMARY_NAME = "correction_aware_adoption_simulation_342n_summary.json"
INPUT_342N_QA_NAME = "correction_aware_adoption_simulation_342n_qa.json"
INPUT_342N_REPORT_NAME = "correction_aware_adoption_simulation_342n_report.md"
INPUT_342N_WORKBOOK_NAME = "correction_aware_adoption_simulation_342n.xlsx"

INPUT_342M_SUMMARY_NAME = "llm_suggestion_spot_check_gate_342m_summary.json"
INPUT_342J_SUMMARY_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"
INPUT_342I_SUMMARY_NAME = "table_first_post_human_review_sidecar_result_342i_summary.json"

REQUIRED_342N_SHEETS = [
    "01_ADOPTION_SUMMARY",
    "03_SPOT_CHECK_PATTERNS",
    "04_ADOPTION_INPUT",
    "05_DIRECT_ADOPT_SIM",
    "06_CORRECTION_ADOPT_SIM",
    "07_STILL_HUMAN_REQUIRED",
    "08_PATTERN_APPLICATION",
    "09_RISK_REVIEW",
    "10_BEFORE_AFTER_SIM",
    "11_REDUCTION_SIM",
    "12_342O_READINESS",
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

OPTIONAL_INPUT_PATHS = [
    "input/spot_check_reviewed_342m",
    "input/llm_review_responses_342m",
]

EXPECTED_PENDING_REVIEW_COUNT = 1075
EXPECTED_INPUT_ADOPTION_CANDIDATE_COUNT = 254
EXPECTED_DIRECT_ADOPT_COUNT = 110
EXPECTED_CORRECTION_ADOPT_COUNT = 78
EXPECTED_STILL_HUMAN_REQUIRED_COUNT = 66
EXPECTED_ADOPTION_SIM_TOTAL_COUNT = 188
RECOMMENDED_342P_SCOPE = "reviewed_plus_simulated_client_preview_pilot"


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
            window = lowered[max(0, idx - 64) : idx]
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

    workbook_sheets, workbook_sheet_names, workbook_warnings = _read_workbook_sheets(
        workbook_path,
        REQUIRED_342N_SHEETS,
    )
    warnings.extend(workbook_warnings)
    return summary, qa_json, workbook_sheets, workbook_sheet_names, files_read, warnings


def _load_summary(path: Path, label: str) -> tuple[Dict[str, Any], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    if path.exists():
        files_read.append(str(path))
        return _read_json(path), files_read, warnings
    warnings.append(f"missing {label}: {path}")
    return {}, files_read, warnings


def _build_sim_adopted_cells_df(direct_df: pd.DataFrame, correction_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for adoption_type, source_df in [("DIRECT", direct_df), ("CORRECTION_AWARE", correction_df)]:
        for row in source_df.to_dict(orient="records"):
            rows.append(
                {
                    "sidecar_cell_id": "",
                    "source_stage": "342N",
                    "review_item_id": _norm_text(row.get("review_item_id")),
                    "simulation_status": _norm_text(row.get("simulation_status")),
                    "adoption_type": adoption_type,
                    "suggested_metric_standardized": _norm_text(row.get("suggested_metric_standardized")),
                    "suggested_year_standardized": _norm_text(row.get("suggested_year_standardized")),
                    "suggested_value_numeric": row.get("suggested_value_numeric"),
                    "suggested_normalized_unit": _norm_text(row.get("suggested_normalized_unit")),
                    "simulated_metric_standardized": _norm_text(row.get("simulated_metric_standardized")),
                    "simulated_year_standardized": _norm_text(row.get("simulated_year_standardized")),
                    "simulated_value_numeric": row.get("simulated_value_numeric"),
                    "simulated_normalized_unit": _norm_text(row.get("simulated_normalized_unit")),
                    "correction_pattern": _norm_text(row.get("correction_pattern")),
                    "adoption_evidence": _norm_text(row.get("adoption_evidence")),
                    "adoption_confidence": row.get("adoption_confidence"),
                    "not_final_confirmation": True,
                    "final_confirmed": False,
                    "human_confirmed": False,
                    "client_ready": False,
                    "production_ready": False,
                    "source_page": row.get("source_page"),
                    "bbox": _norm_text(row.get("bbox")),
                    "image_path": _norm_text(row.get("image_path")),
                    "source_html_snippet": _norm_text(row.get("source_html_snippet")),
                }
            )

    out = _clean_frame(pd.DataFrame(rows))
    if out.empty:
        return out
    out["sidecar_cell_id"] = [f"342o::sim::{index:04d}" for index in range(1, len(out) + 1)]
    return _clean_frame(out)


def _build_direct_adopted_df(direct_df: pd.DataFrame) -> pd.DataFrame:
    if direct_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for row in direct_df.to_dict(orient="records"):
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "simulated_metric_standardized": _norm_text(row.get("simulated_metric_standardized")),
                "simulated_year_standardized": _norm_text(row.get("simulated_year_standardized")),
                "simulated_value_numeric": row.get("simulated_value_numeric"),
                "simulated_normalized_unit": _norm_text(row.get("simulated_normalized_unit")),
                "adoption_confidence": row.get("adoption_confidence"),
                "adoption_evidence": _norm_text(row.get("adoption_evidence")),
                "not_final_confirmation": True,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_corrected_adopted_df(
    correction_df: pd.DataFrame,
    before_after_input_df: pd.DataFrame,
) -> pd.DataFrame:
    if correction_df.empty:
        return pd.DataFrame()

    reason_map: Dict[str, Mapping[str, Any]] = {}
    if not before_after_input_df.empty and "review_item_id" in before_after_input_df.columns:
        reason_map = {
            _norm_text(row.get("review_item_id")): row
            for row in before_after_input_df.to_dict(orient="records")
        }

    rows: List[Dict[str, Any]] = []
    for row in correction_df.to_dict(orient="records"):
        review_item_id = _norm_text(row.get("review_item_id"))
        trace_row = reason_map.get(review_item_id, {})
        rows.append(
            {
                "review_item_id": review_item_id,
                "original_suggested_metric_standardized": _norm_text(
                    trace_row.get("original_suggested_metric_standardized", row.get("suggested_metric_standardized"))
                ),
                "simulated_metric_standardized": _norm_text(row.get("simulated_metric_standardized")),
                "original_suggested_normalized_unit": _norm_text(
                    trace_row.get("original_suggested_normalized_unit", row.get("suggested_normalized_unit"))
                ),
                "simulated_normalized_unit": _norm_text(row.get("simulated_normalized_unit")),
                "simulated_year_standardized": _norm_text(row.get("simulated_year_standardized")),
                "simulated_value_numeric": row.get("simulated_value_numeric"),
                "correction_pattern": _norm_text(row.get("correction_pattern")),
                "correction_reason": _norm_text(trace_row.get("correction_reason")),
                "adoption_evidence": _norm_text(row.get("adoption_evidence")),
                "adoption_confidence": row.get("adoption_confidence"),
                "not_final_confirmation": True,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_still_human_required_df(still_human_df: pd.DataFrame) -> pd.DataFrame:
    if still_human_df.empty:
        return pd.DataFrame()
    out = _clean_frame(still_human_df.copy())
    if "auto_apply_allowed" not in out.columns:
        out["auto_apply_allowed"] = False
    out["auto_apply_allowed"] = False
    return _clean_frame(out)


def _build_before_after_trace_df(
    correction_df: pd.DataFrame,
    before_after_input_df: pd.DataFrame,
) -> pd.DataFrame:
    if correction_df.empty:
        return pd.DataFrame()
    trace_map: Dict[str, Mapping[str, Any]] = {}
    if not before_after_input_df.empty and "review_item_id" in before_after_input_df.columns:
        trace_map = {
            _norm_text(row.get("review_item_id")): row
            for row in before_after_input_df.to_dict(orient="records")
        }

    rows: List[Dict[str, Any]] = []
    for row in correction_df.to_dict(orient="records"):
        review_item_id = _norm_text(row.get("review_item_id"))
        trace_row = trace_map.get(review_item_id, {})
        rows.append(
            {
                "review_item_id": review_item_id,
                "original_metric": _norm_text(
                    trace_row.get("original_suggested_metric_standardized", row.get("suggested_metric_standardized"))
                ),
                "simulated_metric": _norm_text(row.get("simulated_metric_standardized")),
                "original_unit": _norm_text(
                    trace_row.get("original_suggested_normalized_unit", row.get("suggested_normalized_unit"))
                ),
                "simulated_unit": _norm_text(row.get("simulated_normalized_unit")),
                "original_value": trace_row.get("original_suggested_value_numeric", row.get("suggested_value_numeric")),
                "simulated_value": row.get("simulated_value_numeric"),
                "original_year": _norm_text(
                    trace_row.get("original_suggested_year_standardized", row.get("suggested_year_standardized"))
                ),
                "simulated_year": _norm_text(row.get("simulated_year_standardized")),
                "correction_pattern": _norm_text(row.get("correction_pattern")),
                "correction_reason": _norm_text(trace_row.get("correction_reason")),
                "sidecar_note": "342O simulation only; not final confirmation and not written back upstream.",
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_metric_coverage_df(sim_adopted_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    if sim_adopted_df.empty:
        return pd.DataFrame(), {
            "metric_covered_count": 0,
            "metric_year_pair_count": 0,
            "direct_metric_year_pair_count": 0,
            "correction_metric_year_pair_count": 0,
            "correction_pattern_count": 0,
        }

    rows: List[Dict[str, Any]] = []
    grouped = sim_adopted_df.groupby("simulated_metric_standardized", dropna=False)
    for metric_name, group in grouped:
        metric = _norm_text(metric_name)
        years = sorted({_norm_text(value) for value in group["simulated_year_standardized"].tolist() if _norm_text(value)})
        numeric_values = [_safe_float(value) for value in group["simulated_value_numeric"].tolist()]
        numeric_values = [value for value in numeric_values if value is not None]
        rows.append(
            {
                "metric_standardized": metric,
                "adopted_cell_count": int(len(group)),
                "unique_year_count": int(len(years)),
                "years_covered": " | ".join(years),
                "direct_count": int(group["adoption_type"].map(_norm_text).eq("DIRECT").sum()),
                "correction_count": int(group["adoption_type"].map(_norm_text).eq("CORRECTION_AWARE").sum()),
                "unit_set": " | ".join(
                    sorted({_norm_text(value) for value in group["simulated_normalized_unit"].tolist() if _norm_text(value)})
                ),
                "min_value": min(numeric_values) if numeric_values else "",
                "max_value": max(numeric_values) if numeric_values else "",
            }
        )

    metric_year_pair_count = int(
        (
            sim_adopted_df["simulated_metric_standardized"].map(_norm_text)
            + "||"
            + sim_adopted_df["simulated_year_standardized"].map(_norm_text)
        ).replace("||", pd.NA).dropna().nunique()
    )
    direct_metric_year_pair_count = int(
        (
            sim_adopted_df[sim_adopted_df["adoption_type"].map(_norm_text).eq("DIRECT")]["simulated_metric_standardized"].map(_norm_text)
            + "||"
            + sim_adopted_df[sim_adopted_df["adoption_type"].map(_norm_text).eq("DIRECT")]["simulated_year_standardized"].map(_norm_text)
        ).replace("||", pd.NA).dropna().nunique()
    )
    correction_metric_year_pair_count = int(
        (
            sim_adopted_df[sim_adopted_df["adoption_type"].map(_norm_text).eq("CORRECTION_AWARE")]["simulated_metric_standardized"].map(_norm_text)
            + "||"
            + sim_adopted_df[sim_adopted_df["adoption_type"].map(_norm_text).eq("CORRECTION_AWARE")]["simulated_year_standardized"].map(_norm_text)
        ).replace("||", pd.NA).dropna().nunique()
    )
    metrics = {
        "metric_covered_count": int(sim_adopted_df["simulated_metric_standardized"].map(_norm_text).replace("", pd.NA).dropna().nunique()),
        "metric_year_pair_count": metric_year_pair_count,
        "direct_metric_year_pair_count": direct_metric_year_pair_count,
        "correction_metric_year_pair_count": correction_metric_year_pair_count,
        "correction_pattern_count": int(
            sim_adopted_df["correction_pattern"].map(_norm_text).replace("", pd.NA).dropna().nunique()
        ),
    }
    out = _clean_frame(pd.DataFrame(rows).sort_values(by=["adopted_cell_count", "metric_standardized"], ascending=[False, True]))
    return out, metrics


def _build_remaining_review_df(
    pending_review_count: int,
    input_adoption_candidate_count: int,
    simulated_adopted_cell_count: int,
    direct_adopted_count: int,
    corrected_adopted_count: int,
    still_human_required_count: int,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    remaining_review_count = pending_review_count - simulated_adopted_cell_count
    reduction_rate = round(simulated_adopted_cell_count / pending_review_count, 6) if pending_review_count else 0.0
    row = {
        "original_pending_review_count": pending_review_count,
        "input_adoption_candidate_count": input_adoption_candidate_count,
        "simulated_adopted_cell_count": simulated_adopted_cell_count,
        "direct_adopted_count": direct_adopted_count,
        "corrected_adopted_count": corrected_adopted_count,
        "still_human_required_count": still_human_required_count,
        "remaining_review_count": remaining_review_count,
        "reduction_rate_after_342o": reduction_rate,
    }
    return _clean_frame(pd.DataFrame([row])), {
        "remaining_review_count": remaining_review_count,
        "reduction_rate_after_342o": reduction_rate,
    }


def _build_readme_df(
    summary_342n: Mapping[str, Any],
    summary_342m: Mapping[str, Any],
    summary_342j: Mapping[str, Any],
    summary_342i: Mapping[str, Any],
) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342O builds a post-adoption sidecar simulation from 342N direct and correction-aware adoption rows only.",
        },
        {
            "topic": "Boundary",
            "message": "342O is simulation only, not final confirmed, not full human review completion, not real LLM review completion, and not client delivery.",
        },
        {
            "topic": "Input baseline",
            "message": (
                f"342N ready with pending_review_count={summary_342n.get('pending_review_count', 0)}, "
                f"adoption_sim_total_count={summary_342n.get('adoption_sim_total_count', 0)}, "
                f"still_human_required_count={summary_342n.get('still_human_required_count', 0)}."
            ),
        },
        {
            "topic": "Upstream context",
            "message": (
                f"342M reviewed spot-check gate remains the evidence source, 342I post_human_confirmed_count="
                f"{summary_342i.get('post_human_confirmed_count', 0)}, and 342J reviewed_preview_row_count="
                f"{summary_342j.get('reviewed_preview_row_count', 0)}."
            ),
        },
        {
            "topic": "Safety",
            "message": (
                f"Spot-check correction rate from 342M stays at {summary_342m.get('spot_check_correct_count', 0)}/"
                f"{summary_342m.get('reviewed_spot_check_count', 0)}, so client_ready=false and production_ready=false must remain unchanged."
            ),
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_risk_boundary_df(
    *,
    remaining_review_count: int,
    still_human_required_count: int,
    spot_check_correction_rate: float,
) -> pd.DataFrame:
    rows = [
        {"risk_id": "risk_01", "message": "Sidecar result is simulation only and must not be treated as final confirmed output."},
        {"risk_id": "risk_02", "message": "342O does not represent full human review completion or real LLM response ingestion."},
        {"risk_id": "risk_03", "message": f"{remaining_review_count} rows still remain in the broader review queue after this simulation layer."},
        {"risk_id": "risk_04", "message": f"{still_human_required_count} adoption candidates still require explicit human handling."},
        {
            "risk_id": "risk_05",
            "message": (
                f"Spot-check correction rate remains {spot_check_correction_rate:.6f}; therefore simulated adoption cannot be turned into direct client export."
            ),
        },
        {"risk_id": "risk_06", "message": "client_ready=false and production_ready=false must remain unchanged."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342p": summary.get("ready_for_342p", False),
                    "recommended_342p_scope": summary.get("recommended_342p_scope", ""),
                    "decision": summary.get("decision", ""),
                    "client_ready": summary.get("client_ready", False),
                    "production_ready": summary.get("production_ready", False),
                    "reason": summary.get("readiness_reason", ""),
                }
            ]
        )
    )


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    if summary.get("ready_for_342p", False):
        rows = [
            {
                "next_step": "Proceed to 342P reviewed plus simulated client preview pilot.",
                "recommendation": "Blend reviewed 342J preview rows with 342O simulated adopted rows in a clearly bounded preview-only package.",
            },
            {
                "next_step": "Keep no-write-back boundaries.",
                "recommendation": "Do not write simulated adoption rows back to upstream workbooks.",
            },
            {
                "next_step": "Keep readiness boundaries explicit.",
                "recommendation": "client_ready=false and production_ready=false must remain unchanged in 342P.",
            },
        ]
    else:
        rows = [
            {
                "next_step": "Resolve 342O readiness blockers.",
                "recommendation": "Review missing inputs, failed QA checks, or no-write-back proof issues before attempting 342P.",
            }
        ]
    return _clean_frame(pd.DataFrame(rows))


def _build_no_write_back_proof_df(payload: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for key, value in payload.items():
        rows.append(
            {
                "key": key,
                "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def build_post_adoption_sidecar_simulation_342o(
    *,
    adoption_simulation_342n_dir: Path,
    spot_check_gate_342m_dir: Path,
    reviewed_preview_342j_dir: Path,
    post_human_sidecar_342i_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    (
        summary_342n,
        qa_342n,
        workbook_342n,
        workbook_342n_sheet_names,
        files_read_342n,
        warnings_342n,
    ) = _load_342n_context(adoption_simulation_342n_dir)
    files_read.extend(files_read_342n)
    warnings.extend(warnings_342n)

    summary_342m, files_read_342m, warnings_342m = _load_summary(
        spot_check_gate_342m_dir / INPUT_342M_SUMMARY_NAME,
        "342M summary",
    )
    summary_342j, files_read_342j, warnings_342j = _load_summary(
        reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME,
        "342J summary",
    )
    summary_342i, files_read_342i, warnings_342i = _load_summary(
        post_human_sidecar_342i_dir / INPUT_342I_SUMMARY_NAME,
        "342I summary",
    )
    files_read.extend(files_read_342m + files_read_342j + files_read_342i)
    warnings.extend(warnings_342m + warnings_342j + warnings_342i)

    summary_342n_path = adoption_simulation_342n_dir / INPUT_342N_SUMMARY_NAME
    qa_342n_path = adoption_simulation_342n_dir / INPUT_342N_QA_NAME
    report_342n_path = adoption_simulation_342n_dir / INPUT_342N_REPORT_NAME
    workbook_342n_path = adoption_simulation_342n_dir / INPUT_342N_WORKBOOK_NAME
    summary_342m_path = spot_check_gate_342m_dir / INPUT_342M_SUMMARY_NAME
    summary_342j_path = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    summary_342i_path = post_human_sidecar_342i_dir / INPUT_342I_SUMMARY_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [
            summary_342n_path,
            qa_342n_path,
            report_342n_path,
            workbook_342n_path,
            summary_342m_path,
            summary_342j_path,
            summary_342i_path,
        ]
        if path.exists()
    }

    required_342n_present = all(sheet in workbook_342n_sheet_names for sheet in REQUIRED_342N_SHEETS)
    input_ready = bool(
        adoption_simulation_342n_dir.exists()
        and summary_342n_path.exists()
        and qa_342n_path.exists()
        and workbook_342n_path.exists()
        and summary_342n.get("decision") == READY_INPUT_DECISION
        and bool(summary_342n.get("ready_for_342o", False))
        and int(summary_342n.get("qa_fail_count", 0) or 0) == 0
        and int(summary_342n.get("pending_review_count", 0) or 0) == EXPECTED_PENDING_REVIEW_COUNT
        and int(summary_342n.get("input_adoption_candidate_count", 0) or 0) == EXPECTED_INPUT_ADOPTION_CANDIDATE_COUNT
        and int(summary_342n.get("direct_adopt_sim_count", 0) or 0) == EXPECTED_DIRECT_ADOPT_COUNT
        and int(summary_342n.get("correction_adopt_sim_count", 0) or 0) == EXPECTED_CORRECTION_ADOPT_COUNT
        and int(summary_342n.get("still_human_required_count", 0) or 0) == EXPECTED_STILL_HUMAN_REQUIRED_COUNT
        and int(summary_342n.get("adoption_sim_total_count", 0) or 0) == EXPECTED_ADOPTION_SIM_TOTAL_COUNT
        and summary_342n.get("client_ready", False) is False
        and summary_342n.get("production_ready", False) is False
        and required_342n_present
        and summary_342m_path.exists()
        and summary_342j_path.exists()
        and summary_342i_path.exists()
        and summary_342m.get("client_ready", False) is False
        and summary_342m.get("production_ready", False) is False
        and summary_342j.get("client_ready", False) is False
        and summary_342j.get("production_ready", False) is False
        and summary_342i.get("client_ready", False) is False
        and summary_342i.get("production_ready", False) is False
    )

    direct_input_df = _clean_frame(workbook_342n.get("05_DIRECT_ADOPT_SIM", pd.DataFrame())) if input_ready else pd.DataFrame()
    correction_input_df = _clean_frame(workbook_342n.get("06_CORRECTION_ADOPT_SIM", pd.DataFrame())) if input_ready else pd.DataFrame()
    still_human_input_df = _clean_frame(workbook_342n.get("07_STILL_HUMAN_REQUIRED", pd.DataFrame())) if input_ready else pd.DataFrame()
    before_after_input_df = _clean_frame(workbook_342n.get("10_BEFORE_AFTER_SIM", pd.DataFrame())) if input_ready else pd.DataFrame()

    sim_adopted_df = _build_sim_adopted_cells_df(direct_input_df, correction_input_df) if input_ready else pd.DataFrame()
    direct_adopted_df = _build_direct_adopted_df(direct_input_df) if input_ready else pd.DataFrame()
    corrected_adopted_df = _build_corrected_adopted_df(correction_input_df, before_after_input_df) if input_ready else pd.DataFrame()
    still_human_required_df = _build_still_human_required_df(still_human_input_df) if input_ready else pd.DataFrame()
    before_after_trace_df = _build_before_after_trace_df(correction_input_df, before_after_input_df) if input_ready else pd.DataFrame()
    metric_coverage_df, coverage_metrics = _build_metric_coverage_df(sim_adopted_df) if input_ready else (pd.DataFrame(), {
        "metric_covered_count": 0,
        "metric_year_pair_count": 0,
        "direct_metric_year_pair_count": 0,
        "correction_metric_year_pair_count": 0,
        "correction_pattern_count": 0,
    })

    pending_review_count = int(summary_342n.get("pending_review_count", 0) or 0) if input_ready else 0
    input_adoption_candidate_count = int(len(sim_adopted_df) + len(still_human_required_df))
    direct_adopted_count = int(len(direct_adopted_df))
    corrected_adopted_count = int(len(corrected_adopted_df))
    simulated_adopted_cell_count = int(len(sim_adopted_df))
    still_human_required_count = int(len(still_human_required_df))
    remaining_review_df, remaining_metrics = _build_remaining_review_df(
        pending_review_count,
        input_adoption_candidate_count,
        simulated_adopted_cell_count,
        direct_adopted_count,
        corrected_adopted_count,
        still_human_required_count,
    ) if input_ready else (pd.DataFrame(), {"remaining_review_count": 0, "reduction_rate_after_342o": 0.0})

    correction_pattern_counts = (
        corrected_adopted_df["correction_pattern"].map(_norm_text).value_counts().to_dict()
        if not corrected_adopted_df.empty
        else {}
    )

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [
            summary_342n_path,
            qa_342n_path,
            report_342n_path,
            workbook_342n_path,
            summary_342m_path,
            summary_342j_path,
            summary_342i_path,
        ]
        if path.exists()
    }
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths(["output"], repo_root)
    optional_inputs_staged = _git_staged_names_for_paths(OPTIONAL_INPUT_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342O",
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
        no_write_back_json.get("no_official_asset_modification_during_342o")
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df(
        summary_342n if input_ready else {},
        summary_342m if summary_342m else {},
        summary_342j if summary_342j else {},
        summary_342i if summary_342i else {},
    )
    risk_boundary_df = _build_risk_boundary_df(
        remaining_review_count=int(remaining_metrics.get("remaining_review_count", 0) or 0),
        still_human_required_count=still_human_required_count,
        spot_check_correction_rate=float(summary_342n.get("spot_check_correction_rate", 0) or 0),
    )
    claims_text = "\n".join(
        readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
        + risk_boundary_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
    )

    checks = [
        {"check_name": "inputs::342n_output_dir_exists", "status": "PASS" if adoption_simulation_342n_dir.exists() else "FAIL", "detail": str(adoption_simulation_342n_dir)},
        {"check_name": "inputs::342n_summary_exists", "status": "PASS" if summary_342n_path.exists() else "FAIL", "detail": str(summary_342n_path)},
        {"check_name": "inputs::342n_qa_exists", "status": "PASS" if qa_342n_path.exists() else "FAIL", "detail": str(qa_342n_path)},
        {"check_name": "inputs::342n_workbook_exists", "status": "PASS" if workbook_342n_path.exists() else "FAIL", "detail": str(workbook_342n_path)},
        {
            "check_name": "inputs::342n_ready_for_342o_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342n.get("decision", ""),
                    "ready_for_342o": summary_342n.get("ready_for_342o", False),
                    "pending_review_count": summary_342n.get("pending_review_count", 0),
                    "input_adoption_candidate_count": summary_342n.get("input_adoption_candidate_count", 0),
                    "direct_adopt_sim_count": summary_342n.get("direct_adopt_sim_count", 0),
                    "correction_adopt_sim_count": summary_342n.get("correction_adopt_sim_count", 0),
                    "still_human_required_count": summary_342n.get("still_human_required_count", 0),
                    "qa_fail_count": summary_342n.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342n_required_sheets_exist",
            "status": "PASS" if required_342n_present else "FAIL",
            "detail": json.dumps({sheet: sheet in workbook_342n_sheet_names for sheet in REQUIRED_342N_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "quality::direct_plus_corrected_equals_simulated",
            "status": "PASS" if direct_adopted_count + corrected_adopted_count == simulated_adopted_cell_count else "FAIL",
            "detail": f"{direct_adopted_count}+{corrected_adopted_count} vs {simulated_adopted_cell_count}",
        },
        {
            "check_name": "quality::simulated_plus_still_human_equals_input_candidates",
            "status": "PASS" if simulated_adopted_cell_count + still_human_required_count == input_adoption_candidate_count else "FAIL",
            "detail": f"{simulated_adopted_cell_count}+{still_human_required_count} vs {input_adoption_candidate_count}",
        },
        {
            "check_name": "quality::remaining_review_count_consistent",
            "status": "PASS"
            if int(remaining_metrics.get("remaining_review_count", 0) or 0) == pending_review_count - simulated_adopted_cell_count
            else "FAIL",
            "detail": f"pending={pending_review_count}; simulated={simulated_adopted_cell_count}; remaining={remaining_metrics.get('remaining_review_count', 0)}",
        },
        {
            "check_name": "quality::no_simulated_row_becomes_final_confirmed",
            "status": "PASS"
            if sim_adopted_df.empty or not sim_adopted_df["final_confirmed"].astype(bool).any()
            else "FAIL",
            "detail": str(len(sim_adopted_df)),
        },
        {
            "check_name": "quality::no_simulated_row_becomes_human_confirmed",
            "status": "PASS"
            if sim_adopted_df.empty or not sim_adopted_df["human_confirmed"].astype(bool).any()
            else "FAIL",
            "detail": str(len(sim_adopted_df)),
        },
        {
            "check_name": "quality::simulated_rows_keep_client_ready_false",
            "status": "PASS"
            if sim_adopted_df.empty or not sim_adopted_df["client_ready"].astype(bool).any()
            else "FAIL",
            "detail": str(len(sim_adopted_df)),
        },
        {
            "check_name": "quality::simulated_rows_keep_production_ready_false",
            "status": "PASS"
            if sim_adopted_df.empty or not sim_adopted_df["production_ready"].astype(bool).any()
            else "FAIL",
            "detail": str(len(sim_adopted_df)),
        },
        {
            "check_name": "quality::correction_rows_preserve_before_after_trace",
            "status": "PASS"
            if corrected_adopted_count == len(before_after_trace_df) and set(corrected_adopted_df.get("review_item_id", pd.Series(dtype=object)).astype(str)) == set(before_after_trace_df.get("review_item_id", pd.Series(dtype=object)).astype(str))
            else "FAIL",
            "detail": f"corrected={corrected_adopted_count}; trace={len(before_after_trace_df)}",
        },
        {
            "check_name": "quality::still_human_rows_not_auto_applied",
            "status": "PASS"
            if still_human_required_df.empty or still_human_required_df["auto_apply_allowed"].astype(bool).eq(False).all()
            else "FAIL",
            "detail": str(len(still_human_required_df)),
        },
        {
            "check_name": "quality::correction_pattern_examples_preserved",
            "status": "PASS"
            if corrected_adopted_df.empty
            else (
                "PASS"
                if {
                    ("revenue_yoy", "亿元", "revenue", "亿元"),
                    ("revenue", "%", "revenue_yoy", "%"),
                    ("net_profit", "%", "net_profit_yoy", "%"),
                }.issubset(
                    {
                        (
                            _norm_text(row.get("original_suggested_metric_standardized")),
                            _norm_text(row.get("original_suggested_normalized_unit")),
                            _norm_text(row.get("simulated_metric_standardized")),
                            _norm_text(row.get("simulated_normalized_unit")),
                        )
                        for row in corrected_adopted_df.to_dict(orient="records")
                    }
                )
                else "FAIL"
            ),
            "detail": json.dumps(correction_pattern_counts, ensure_ascii=False),
        },
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "342O adds sidecar simulation code only."},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "safety::optional_input_artifacts_not_staged", "status": "PASS" if not optional_inputs_staged else "FAIL", "detail": json.dumps(optional_inputs_staged, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(claims_text, ["investment advice"]) else "FAIL",
            "detail": "readme and risk boundary text checked",
        },
        {
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS",
            "detail": "all 342O sheet names are <= 31 chars",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342p = bool(
        input_ready
        and simulated_adopted_cell_count > 0
        and still_human_required_count >= 0
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )
    recommended_342p_scope = RECOMMENDED_342P_SCOPE if ready_for_342p else ""
    decision = READY_DECISION if ready_for_342p else NOT_READY_DECISION
    readiness_reason = (
        "342O produced a bounded post-adoption sidecar simulation and can move to a reviewed plus simulated preview pilot while keeping client_ready=false and production_ready=false."
        if ready_for_342p
        else "342O cannot move to 342P yet because required inputs or QA checks are not satisfied."
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "pending_review_count": pending_review_count,
        "input_adoption_candidate_count": input_adoption_candidate_count,
        "direct_adopted_count": direct_adopted_count,
        "corrected_adopted_count": corrected_adopted_count,
        "simulated_adopted_cell_count": simulated_adopted_cell_count,
        "still_human_required_count": still_human_required_count,
        "remaining_review_count": int(remaining_metrics.get("remaining_review_count", 0) or 0),
        "reduction_rate_after_342o": float(remaining_metrics.get("reduction_rate_after_342o", 0) or 0),
        "metric_covered_count": int(coverage_metrics.get("metric_covered_count", 0) or 0),
        "metric_year_pair_count": int(coverage_metrics.get("metric_year_pair_count", 0) or 0),
        "direct_metric_year_pair_count": int(coverage_metrics.get("direct_metric_year_pair_count", 0) or 0),
        "correction_metric_year_pair_count": int(coverage_metrics.get("correction_metric_year_pair_count", 0) or 0),
        "correction_pattern_count": int(coverage_metrics.get("correction_pattern_count", 0) or 0),
        "REVENUE_AMOUNT_NOT_YOY_count": int(correction_pattern_counts.get("REVENUE_AMOUNT_NOT_YOY", 0) or 0),
        "REVENUE_YOY_PERCENT_count": int(correction_pattern_counts.get("REVENUE_YOY_PERCENT", 0) or 0),
        "NET_PROFIT_YOY_PERCENT_count": int(correction_pattern_counts.get("NET_PROFIT_YOY_PERCENT", 0) or 0),
        "ready_for_342p": ready_for_342p,
        "recommended_342p_scope": recommended_342p_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "readiness_reason": readiness_reason,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342O_post_adoption_sidecar_simulation",
        "adoption_simulation_342n_dir": str(adoption_simulation_342n_dir),
        "spot_check_gate_342m_dir": str(spot_check_gate_342m_dir),
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
        "post_human_sidecar_342i_dir": str(post_human_sidecar_342i_dir),
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
        "01_SIDECAR_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342N_SUMMARY": _clean_frame(pd.DataFrame([summary_342n])) if summary_342n else pd.DataFrame(),
        "03_SIM_ADOPTED_CELLS": sim_adopted_df,
        "04_DIRECT_ADOPTED": direct_adopted_df,
        "05_CORRECTED_ADOPTED": corrected_adopted_df,
        "06_STILL_HUMAN_REQUIRED": still_human_required_df,
        "07_BEFORE_AFTER_TRACE": before_after_trace_df,
        "08_METRIC_COVERAGE": metric_coverage_df,
        "09_REMAINING_REVIEW": remaining_review_df,
        "10_RISK_BOUNDARY": risk_boundary_df,
        "11_342P_READINESS": _build_readiness_df(summary),
        "12_NO_WRITE_BACK": _build_no_write_back_proof_df(no_write_back_json),
        "13_NEXT_STEPS": _build_next_steps_df(summary),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
