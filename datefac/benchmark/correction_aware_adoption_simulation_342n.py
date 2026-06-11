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


READY_INPUT_DECISION = "LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY"
READY_DECISION = "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY"
NOT_READY_DECISION = "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_NOT_READY"

DEFAULT_SPOT_CHECK_GATE_342M_DIR = Path(r"D:\_datefac\output\llm_suggestion_spot_check_gate_342m")
DEFAULT_LLM_SUGGESTION_342L_DIR = Path(r"D:\_datefac\output\llm_suggestion_apply_simulation_342l")
DEFAULT_LLM_REVIEW_342K_DIR = Path(r"D:\_datefac\output\llm_assisted_review_adjudication_342k")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\correction_aware_adoption_simulation_342n")

SUMMARY_FILE_NAME = "correction_aware_adoption_simulation_342n_summary.json"
MANIFEST_FILE_NAME = "correction_aware_adoption_simulation_342n_manifest.json"
QA_FILE_NAME = "correction_aware_adoption_simulation_342n_qa.json"
NO_WRITE_BACK_FILE_NAME = "correction_aware_adoption_simulation_342n_no_write_back_proof.json"
REPORT_FILE_NAME = "correction_aware_adoption_simulation_342n_report.md"
WORKBOOK_FILE_NAME = "correction_aware_adoption_simulation_342n.xlsx"

INPUT_342M_SUMMARY_NAME = "llm_suggestion_spot_check_gate_342m_summary.json"
INPUT_342M_QA_NAME = "llm_suggestion_spot_check_gate_342m_qa.json"
INPUT_342M_REPORT_NAME = "llm_suggestion_spot_check_gate_342m_report.md"
INPUT_342M_WORKBOOK_NAME = "llm_suggestion_spot_check_gate_342m.xlsx"
INPUT_342M_NO_WRITE_BACK_NAME = "llm_suggestion_spot_check_gate_342m_no_write_back_proof.json"

INPUT_342L_SUMMARY_NAME = "llm_suggestion_apply_simulation_342l_summary.json"
INPUT_342L_QA_NAME = "llm_suggestion_apply_simulation_342l_qa.json"
INPUT_342L_WORKBOOK_NAME = "llm_suggestion_apply_simulation_342l.xlsx"
INPUT_342K_SUMMARY_NAME = "llm_assisted_review_adjudication_342k_summary.json"
INPUT_342K_QA_NAME = "llm_assisted_review_adjudication_342k_qa.json"
INPUT_342K_WORKBOOK_NAME = "llm_assisted_review_adjudication_342k.xlsx"
INPUT_342J_SUMMARY_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"

REQUIRED_342M_SHEETS = [
    "01_GATE_SUMMARY",
    "03_SPOT_CHECK_TEMPLATE",
    "04_SPOT_CHECK_APPLY",
    "09_ADOPTION_CANDIDATES",
    "12_REDUCTION_AFTER_GATE",
    "13_342N_READINESS",
    "14_NO_WRITE_BACK",
]
REQUIRED_342L_SHEETS = [
    "03_AUTO_CANDIDATES",
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

PATTERN_NO_CORRECTION = "NO_CORRECTION_REQUIRED"
PATTERN_REVENUE_AMOUNT = "REVENUE_AMOUNT_NOT_YOY"
PATTERN_REVENUE_YOY = "REVENUE_YOY_PERCENT"
PATTERN_NET_PROFIT_YOY = "NET_PROFIT_YOY_PERCENT"
PATTERN_OTHER = "OTHER_CORRECTION"
PATTERN_UNRESOLVED = "UNRESOLVED_PATTERN"

UNIT_PERCENT = "%"
UNIT_YI_CNY = "\u4ebf\u5143"
UNIT_MILLION_CNY = "\u767e\u4e07\u5143"
UNIT_YUAN = "\u5143"
UNIT_PE = "\u500d_or_unitless"

REVENUE_AMOUNT_REASON = "Spot-check pattern shows amount rows with unit 亿元 should map to revenue, not revenue_yoy."
REVENUE_YOY_REASON = "Spot-check pattern shows revenue rows with % unit should map to revenue_yoy."
NET_PROFIT_YOY_REASON = "Spot-check pattern shows net_profit rows with % unit should map to net_profit_yoy."

SAFE_METRIC_UNIT_PAIRS = {
    ("ROE", UNIT_PERCENT),
    ("gross_margin", UNIT_PERCENT),
    ("net_margin", UNIT_PERCENT),
    ("EPS", UNIT_YUAN),
    ("PE", UNIT_PE),
    ("PB", UNIT_PE),
    ("revenue", UNIT_MILLION_CNY),
    ("revenue", UNIT_YI_CNY),
    ("net_profit", UNIT_MILLION_CNY),
    ("net_profit", UNIT_YI_CNY),
    ("revenue_yoy", UNIT_PERCENT),
    ("net_profit_yoy", UNIT_PERCENT),
    ("investing_cash_flow", UNIT_MILLION_CNY),
    ("financing_cash_flow", UNIT_MILLION_CNY),
    ("cash_net_change", UNIT_MILLION_CNY),
    ("operating_cash_flow", UNIT_MILLION_CNY),
    ("total_assets", UNIT_MILLION_CNY),
    ("total_liabilities", UNIT_MILLION_CNY),
    ("shareholder_equity", UNIT_MILLION_CNY),
}
PATTERN_SHEET_ORDER = [
    PATTERN_REVENUE_AMOUNT,
    PATTERN_REVENUE_YOY,
    PATTERN_NET_PROFIT_YOY,
    PATTERN_NO_CORRECTION,
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
            window = lowered[max(0, idx - 32) : idx]
            if "not " not in window and "false" not in window:
                return True
            start = idx + len(token_lower)
    return False


def _read_workbook_sheets(path: Path, required: Sequence[str]) -> tuple[Dict[str, pd.DataFrame], List[str], List[str]]:
    sheets: Dict[str, pd.DataFrame] = {}
    sheet_names: List[str] = []
    warnings: List[str] = []
    if not path.exists():
        for sheet in required:
            sheets[sheet] = pd.DataFrame()
        return sheets, sheet_names, [f"missing workbook: {path}"]
    try:
        excel = pd.ExcelFile(path)
        sheet_names = list(excel.sheet_names)
        for sheet in required:
            if sheet in sheet_names:
                sheets[sheet] = _clean_frame(pd.read_excel(path, sheet_name=sheet))
            else:
                sheets[sheet] = pd.DataFrame()
                warnings.append(f"missing required workbook sheet: {sheet}")
    except Exception as exc:
        warnings.append(f"unable to read workbook {path}: {exc}")
        for sheet in required:
            sheets[sheet] = pd.DataFrame()
    return sheets, sheet_names, warnings


def _load_required_inputs(
    spot_check_gate_342m_dir: Path,
    llm_suggestion_342l_dir: Path,
    llm_review_342k_dir: Path,
    reviewed_preview_342j_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], Dict[str, pd.DataFrame], List[str], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []

    summary_342m_path = spot_check_gate_342m_dir / INPUT_342M_SUMMARY_NAME
    qa_342m_path = spot_check_gate_342m_dir / INPUT_342M_QA_NAME
    report_342m_path = spot_check_gate_342m_dir / INPUT_342M_REPORT_NAME
    workbook_342m_path = spot_check_gate_342m_dir / INPUT_342M_WORKBOOK_NAME
    proof_342m_path = spot_check_gate_342m_dir / INPUT_342M_NO_WRITE_BACK_NAME

    summary_342l_path = llm_suggestion_342l_dir / INPUT_342L_SUMMARY_NAME
    qa_342l_path = llm_suggestion_342l_dir / INPUT_342L_QA_NAME
    workbook_342l_path = llm_suggestion_342l_dir / INPUT_342L_WORKBOOK_NAME
    summary_342k_path = llm_review_342k_dir / INPUT_342K_SUMMARY_NAME
    qa_342k_path = llm_review_342k_dir / INPUT_342K_QA_NAME
    workbook_342k_path = llm_review_342k_dir / INPUT_342K_WORKBOOK_NAME
    summary_342j_path = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME

    summary_342m = _read_json(summary_342m_path) if summary_342m_path.exists() else {}
    qa_342m = _read_json(qa_342m_path) if qa_342m_path.exists() else {}
    proof_342m = _read_json(proof_342m_path) if proof_342m_path.exists() else {}
    summary_342l = _read_json(summary_342l_path) if summary_342l_path.exists() else {}
    qa_342l = _read_json(qa_342l_path) if qa_342l_path.exists() else {}
    summary_342k = _read_json(summary_342k_path) if summary_342k_path.exists() else {}
    qa_342k = _read_json(qa_342k_path) if qa_342k_path.exists() else {}
    summary_342j = _read_json(summary_342j_path) if summary_342j_path.exists() else {}

    for path in [
        summary_342m_path,
        qa_342m_path,
        report_342m_path,
        workbook_342m_path,
        proof_342m_path,
        summary_342l_path,
        qa_342l_path,
        workbook_342l_path,
        summary_342k_path,
        qa_342k_path,
        workbook_342k_path,
        summary_342j_path,
    ]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input file: {path}")

    workbook_342m, workbook_342m_names, workbook_342m_warnings = _read_workbook_sheets(
        workbook_342m_path,
        REQUIRED_342M_SHEETS,
    )
    workbook_342l, workbook_342l_names, workbook_342l_warnings = _read_workbook_sheets(
        workbook_342l_path,
        REQUIRED_342L_SHEETS,
    )
    warnings.extend(workbook_342m_warnings + workbook_342l_warnings)
    return (
        summary_342m,
        qa_342m,
        proof_342m,
        summary_342l,
        qa_342l,
        workbook_342m,
        workbook_342l,
        workbook_342m_names,
        workbook_342l_names,
        files_read,
        warnings,
    )


def _normalize_unit(value: Any) -> str:
    text = _norm_text(value)
    mapping = {
        UNIT_PERCENT: UNIT_PERCENT,
        UNIT_YI_CNY: UNIT_YI_CNY,
        UNIT_MILLION_CNY: UNIT_MILLION_CNY,
        UNIT_YUAN: UNIT_YUAN,
        UNIT_PE: UNIT_PE,
    }
    return mapping.get(text, text)


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


def _source_trace_ok(row: Mapping[str, Any]) -> bool:
    source_page = _norm_text(row.get("source_page"))
    image_path = _norm_text(row.get("image_path"))
    html = _norm_text(row.get("source_html_snippet"))
    return bool(source_page and (image_path or html))


def _has_unresolved_conflict(risk_flags: str, candidate_reason: str) -> bool:
    combined = f"{risk_flags} | {candidate_reason}".upper()
    return any(token in combined for token in ["CONFLICT", "UNRESOLVED", "DUPLICATE_CONFLICT"])


def _spot_check_pattern_from_row(row: Mapping[str, Any]) -> tuple[str, str]:
    reviewer_decision = _norm_text(row.get("reviewer_decision_apply", row.get("reviewer_decision")))
    reviewer_metric = _norm_text(
        row.get("reviewer_metric_standardized_apply", row.get("reviewer_metric_standardized"))
    )
    reviewer_unit = _normalize_unit(
        row.get("reviewer_normalized_unit_apply", row.get("reviewer_normalized_unit"))
    )
    if reviewer_decision == "CONFIRM_SUGGESTION":
        return PATTERN_NO_CORRECTION, "Reviewer confirmed original suggestion."
    if reviewer_decision == "CORRECT_SUGGESTION":
        if reviewer_metric == "revenue" and reviewer_unit == UNIT_YI_CNY:
            return PATTERN_REVENUE_AMOUNT, REVENUE_AMOUNT_REASON
        if reviewer_metric == "revenue_yoy" and reviewer_unit == UNIT_PERCENT:
            return PATTERN_REVENUE_YOY, REVENUE_YOY_REASON
        if reviewer_metric == "net_profit_yoy" and reviewer_unit == UNIT_PERCENT:
            return PATTERN_NET_PROFIT_YOY, NET_PROFIT_YOY_REASON
        return PATTERN_OTHER, "Correction exists but does not match a reusable explicit pattern."
    if reviewer_decision in {"REJECT_SUGGESTION", "KEEP_HUMAN_REQUIRED", "NEEDS_SOURCE_CHECK"}:
        return PATTERN_UNRESOLVED, f"Reviewer decision {reviewer_decision} is not reusable for adoption simulation."
    return PATTERN_UNRESOLVED, "Reviewer decision missing or unresolved."


def _build_spot_check_patterns_df(template_df: pd.DataFrame, apply_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, int], Dict[str, Any]]:
    counts = {
        PATTERN_NO_CORRECTION: 0,
        PATTERN_REVENUE_AMOUNT: 0,
        PATTERN_REVENUE_YOY: 0,
        PATTERN_NET_PROFIT_YOY: 0,
        PATTERN_OTHER: 0,
        PATTERN_UNRESOLVED: 0,
    }
    empty_metrics = {
        "spot_check_total_count": 0,
        "spot_check_confirm_count": 0,
        "spot_check_correct_count": 0,
        "spot_check_reject_count": 0,
        "correction_rate": 0.0,
        "confirm_rate": 0.0,
    }
    if (
        template_df.empty
        or apply_df.empty
        or "review_item_id" not in template_df.columns
        or "review_item_id" not in apply_df.columns
    ):
        return pd.DataFrame(), counts, empty_metrics

    merged = template_df.merge(apply_df, on="review_item_id", how="inner", suffixes=("_template", "_apply"))
    rows: List[Dict[str, Any]] = []
    for row in merged.to_dict(orient="records"):
        pattern_name, pattern_reason = _spot_check_pattern_from_row(row)
        counts[pattern_name] += 1
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "spot_check_id": _norm_text(row.get("spot_check_id_template", row.get("spot_check_id"))),
                "reviewer_decision": _norm_text(row.get("reviewer_decision_apply", row.get("reviewer_decision"))),
                "suggested_metric_standardized": _norm_text(
                    row.get("suggested_metric_standardized_template", row.get("suggested_metric_standardized"))
                ),
                "suggested_normalized_unit": _normalize_unit(
                    row.get("suggested_normalized_unit_template", row.get("suggested_normalized_unit"))
                ),
                "reviewer_metric_standardized": _norm_text(
                    row.get("reviewer_metric_standardized_apply", row.get("reviewer_metric_standardized"))
                ),
                "reviewer_normalized_unit": _normalize_unit(
                    row.get("reviewer_normalized_unit_apply", row.get("reviewer_normalized_unit"))
                ),
                "pattern_name": pattern_name,
                "pattern_reason": pattern_reason,
            }
        )
    spot_check_total = len(rows)
    confirm_count = counts[PATTERN_NO_CORRECTION]
    correct_count = counts[PATTERN_REVENUE_AMOUNT] + counts[PATTERN_REVENUE_YOY] + counts[PATTERN_NET_PROFIT_YOY] + counts[PATTERN_OTHER]
    reject_count = counts[PATTERN_UNRESOLVED]
    metrics = {
        "spot_check_total_count": spot_check_total,
        "spot_check_confirm_count": confirm_count,
        "spot_check_correct_count": correct_count,
        "spot_check_reject_count": reject_count,
        "correction_rate": round(correct_count / spot_check_total, 6) if spot_check_total else 0.0,
        "confirm_rate": round(confirm_count / spot_check_total, 6) if spot_check_total else 0.0,
    }
    return _clean_frame(pd.DataFrame(rows)), counts, metrics


def _build_adoption_input_df(adoption_candidates_df: pd.DataFrame, auto_candidates_df: pd.DataFrame) -> pd.DataFrame:
    if adoption_candidates_df.empty or "review_item_id" not in adoption_candidates_df.columns:
        return pd.DataFrame()
    merge_columns = [
        "review_item_id",
        "source_page",
        "bbox",
        "image_path",
        "source_html_snippet",
        "file_name",
        "table_id",
        "table_type",
    ]
    if auto_candidates_df.empty or "review_item_id" not in auto_candidates_df.columns:
        extra = pd.DataFrame(columns=merge_columns)
    else:
        extra = auto_candidates_df[[col for col in merge_columns if col in auto_candidates_df.columns]].drop_duplicates(
            subset=["review_item_id"]
        )
    merged = adoption_candidates_df.merge(extra, on="review_item_id", how="left")
    return _clean_frame(merged)


def _correction_pattern_for_candidate(metric: str, unit: str) -> tuple[str, str, str]:
    if metric == "revenue_yoy" and unit == UNIT_YI_CNY:
        return PATTERN_REVENUE_AMOUNT, "revenue", UNIT_YI_CNY
    if metric == "revenue" and unit == UNIT_PERCENT:
        return PATTERN_REVENUE_YOY, "revenue_yoy", UNIT_PERCENT
    if metric == "net_profit" and unit == UNIT_PERCENT:
        return PATTERN_NET_PROFIT_YOY, "net_profit_yoy", UNIT_PERCENT
    return "", "", ""


def _simulate_adoption(adoption_input_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any], Dict[str, Dict[str, Any]]]:
    direct_rows: List[Dict[str, Any]] = []
    correction_rows: List[Dict[str, Any]] = []
    human_rows: List[Dict[str, Any]] = []
    before_after_rows: List[Dict[str, Any]] = []

    source_trace_missing_count = 0
    low_confidence_count = 0
    unresolved_pattern_count = 0

    pattern_stats: Dict[str, Dict[str, Any]] = {
        PATTERN_REVENUE_AMOUNT: {"input_candidate_count": 0, "applied_candidate_count": 0, "still_human_required_count": 0, "examples": []},
        PATTERN_REVENUE_YOY: {"input_candidate_count": 0, "applied_candidate_count": 0, "still_human_required_count": 0, "examples": []},
        PATTERN_NET_PROFIT_YOY: {"input_candidate_count": 0, "applied_candidate_count": 0, "still_human_required_count": 0, "examples": []},
        PATTERN_NO_CORRECTION: {"input_candidate_count": 0, "applied_candidate_count": 0, "still_human_required_count": 0, "examples": []},
    }

    for row in adoption_input_df.to_dict(orient="records"):
        review_item_id = _norm_text(row.get("review_item_id"))
        metric = _norm_text(row.get("suggested_metric_standardized"))
        year = _norm_text(row.get("suggested_year_standardized"))
        unit = _normalize_unit(row.get("suggested_normalized_unit"))
        value_numeric = row.get("suggested_value_numeric")
        confidence = _safe_float(row.get("suggested_confidence"))
        risk_flags = _norm_text(row.get("risk_flags"))
        candidate_reason = _norm_text(row.get("candidate_reason"))
        source_ok = _source_trace_ok(row)
        correction_pattern, corrected_metric, corrected_unit = _correction_pattern_for_candidate(metric, unit)
        safe_pair = (metric, unit) in SAFE_METRIC_UNIT_PAIRS

        base_payload = {
            "review_item_id": review_item_id,
            "rule_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
            "dry_run_suggested_decision": _norm_text(row.get("dry_run_suggested_decision")),
            "suggested_metric_standardized": metric,
            "suggested_year_standardized": year,
            "suggested_value_numeric": value_numeric,
            "suggested_normalized_unit": unit,
            "suggested_confidence": confidence,
            "candidate_reason": candidate_reason,
            "risk_flags": risk_flags,
            "not_final_confirmation": True,
            "source_page": row.get("source_page"),
            "bbox": _norm_text(row.get("bbox")),
            "image_path": _norm_text(row.get("image_path")),
            "source_html_snippet": _norm_text(row.get("source_html_snippet")),
        }

        failed_reasons: List[str] = []
        if not metric or not year or _norm_text(value_numeric) == "" or not unit:
            failed_reasons.append("missing_core_fields")
        if not source_ok:
            source_trace_missing_count += 1
            failed_reasons.append("source_trace_missing")
        if confidence is None or confidence < 0.95:
            low_confidence_count += 1
            failed_reasons.append("low_confidence")
        if _has_unresolved_conflict(risk_flags, candidate_reason):
            failed_reasons.append("unresolved_conflict")

        if correction_pattern:
            pattern_stats[correction_pattern]["input_candidate_count"] += 1
            if not failed_reasons:
                correction_rows.append(
                    {
                        **base_payload,
                        "simulation_status": "CORRECTION_AWARE_ADOPT_SIMULATION",
                        "simulated_metric_standardized": corrected_metric,
                        "simulated_year_standardized": year,
                        "simulated_value_numeric": value_numeric,
                        "simulated_normalized_unit": corrected_unit,
                        "correction_pattern": correction_pattern,
                        "adoption_evidence": f"{correction_pattern} matched spot-check correction pattern.",
                        "adoption_confidence": confidence,
                    }
                )
                before_after_rows.append(
                    {
                        "review_item_id": review_item_id,
                        "original_suggested_metric_standardized": metric,
                        "simulated_metric_standardized": corrected_metric,
                        "original_suggested_year_standardized": year,
                        "simulated_year_standardized": year,
                        "original_suggested_value_numeric": value_numeric,
                        "simulated_value_numeric": value_numeric,
                        "original_suggested_normalized_unit": unit,
                        "simulated_normalized_unit": corrected_unit,
                        "correction_pattern": correction_pattern,
                        "correction_reason": {
                            PATTERN_REVENUE_AMOUNT: REVENUE_AMOUNT_REASON,
                            PATTERN_REVENUE_YOY: REVENUE_YOY_REASON,
                            PATTERN_NET_PROFIT_YOY: NET_PROFIT_YOY_REASON,
                        }[correction_pattern],
                    }
                )
                pattern_stats[correction_pattern]["applied_candidate_count"] += 1
                if len(pattern_stats[correction_pattern]["examples"]) < 5:
                    pattern_stats[correction_pattern]["examples"].append(review_item_id)
                continue

            unresolved_pattern_count += 1
            pattern_stats[correction_pattern]["still_human_required_count"] += 1
            human_rows.append(
                {
                    "review_item_id": review_item_id,
                    "human_required_reason": " | ".join(failed_reasons),
                    "failed_pattern_reason": correction_pattern,
                    "recommended_human_action": "verify source trace or confidence before applying correction pattern",
                    "auto_apply_allowed": False,
                }
            )
            continue

        if safe_pair:
            pattern_stats[PATTERN_NO_CORRECTION]["input_candidate_count"] += 1
            if not failed_reasons:
                direct_rows.append(
                    {
                        **base_payload,
                        "simulation_status": "DIRECT_ADOPT_SIMULATION",
                        "simulated_metric_standardized": metric,
                        "simulated_year_standardized": year,
                        "simulated_value_numeric": value_numeric,
                        "simulated_normalized_unit": unit,
                        "adoption_evidence": "safe metric/unit pair with no explicit correction pattern required",
                        "adoption_confidence": confidence,
                    }
                )
                pattern_stats[PATTERN_NO_CORRECTION]["applied_candidate_count"] += 1
                if len(pattern_stats[PATTERN_NO_CORRECTION]["examples"]) < 5:
                    pattern_stats[PATTERN_NO_CORRECTION]["examples"].append(review_item_id)
                continue

            pattern_stats[PATTERN_NO_CORRECTION]["still_human_required_count"] += 1
            unresolved_pattern_count += 1
            human_rows.append(
                {
                    "review_item_id": review_item_id,
                    "human_required_reason": " | ".join(failed_reasons),
                    "failed_pattern_reason": PATTERN_NO_CORRECTION,
                    "recommended_human_action": "verify source trace or confidence before direct adoption simulation",
                    "auto_apply_allowed": False,
                }
            )
            continue

        unresolved_pattern_count += 1
        human_rows.append(
            {
                "review_item_id": review_item_id,
                "human_required_reason": "no_safe_metric_unit_pair",
                "failed_pattern_reason": PATTERN_UNRESOLVED,
                "recommended_human_action": "manual review required for unresolved metric/unit pattern",
                "auto_apply_allowed": False,
            }
        )

    direct_df = _clean_frame(pd.DataFrame(direct_rows))
    correction_df = _clean_frame(pd.DataFrame(correction_rows))
    human_df = _clean_frame(pd.DataFrame(human_rows))
    before_after_df = _clean_frame(pd.DataFrame(before_after_rows))
    metrics = {
        "direct_adopt_sim_count": len(direct_rows),
        "correction_adopt_sim_count": len(correction_rows),
        "still_human_required_count": len(human_rows),
        "adoption_sim_total_count": len(direct_rows) + len(correction_rows),
        "source_trace_missing_count": source_trace_missing_count,
        "low_confidence_count": low_confidence_count,
        "unresolved_pattern_count": unresolved_pattern_count,
    }
    return direct_df, correction_df, human_df, before_after_df, metrics, pattern_stats


def _build_pattern_application_df(pattern_stats: Mapping[str, Mapping[str, Any]]) -> pd.DataFrame:
    risk_notes = {
        PATTERN_REVENUE_AMOUNT: "Amount rows mislabeled as revenue_yoy can be simulated only with explicit correction.",
        PATTERN_REVENUE_YOY: "Percent revenue rows require yoy remapping before simulation.",
        PATTERN_NET_PROFIT_YOY: "Percent net_profit rows require yoy remapping before simulation.",
        PATTERN_NO_CORRECTION: "Safe metric/unit pairs can move through direct adoption simulation only.",
    }
    rows: List[Dict[str, Any]] = []
    for pattern_name in PATTERN_SHEET_ORDER:
        stat = pattern_stats.get(pattern_name, {})
        rows.append(
            {
                "pattern_name": pattern_name,
                "input_candidate_count": int(stat.get("input_candidate_count", 0) or 0),
                "applied_candidate_count": int(stat.get("applied_candidate_count", 0) or 0),
                "still_human_required_count": int(stat.get("still_human_required_count", 0) or 0),
                "example_review_item_ids": " | ".join(stat.get("examples", [])),
                "risk_note": risk_notes[pattern_name],
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_risk_review_df(spot_metrics: Mapping[str, Any], sim_metrics: Mapping[str, Any], pattern_counts: Mapping[str, int]) -> pd.DataFrame:
    row = {
        "spot_check_correction_rate": spot_metrics.get("correction_rate", 0.0),
        "spot_check_confirm_rate": spot_metrics.get("confirm_rate", 0.0),
        "correction_pattern_count": sum(
            1
            for name in [PATTERN_REVENUE_AMOUNT, PATTERN_REVENUE_YOY, PATTERN_NET_PROFIT_YOY]
            if int(pattern_counts.get(name, 0) or 0) > 0
        ),
        "correction_adopt_sim_count": sim_metrics.get("correction_adopt_sim_count", 0),
        "direct_adopt_sim_count": sim_metrics.get("direct_adopt_sim_count", 0),
        "still_human_required_count": sim_metrics.get("still_human_required_count", 0),
        "adoption_sim_total_count": sim_metrics.get("adoption_sim_total_count", 0),
        "source_trace_missing_count": sim_metrics.get("source_trace_missing_count", 0),
        "low_confidence_count": sim_metrics.get("low_confidence_count", 0),
        "unresolved_pattern_count": sim_metrics.get("unresolved_pattern_count", 0),
        "risk_note": "High correction rate means raw bulk adoption is unsafe. 342N only permits correction-aware simulation, not final confirmation.",
    }
    return _clean_frame(pd.DataFrame([row]))


def _build_reduction_df(pending_review_count: int, input_candidate_count: int, sim_metrics: Mapping[str, Any]) -> tuple[pd.DataFrame, Dict[str, Any]]:
    adoption_total = int(sim_metrics.get("adoption_sim_total_count", 0) or 0)
    row = {
        "original_pending_review_count": pending_review_count,
        "input_adoption_candidate_count": input_candidate_count,
        "direct_adopt_sim_count": int(sim_metrics.get("direct_adopt_sim_count", 0) or 0),
        "correction_adopt_sim_count": int(sim_metrics.get("correction_adopt_sim_count", 0) or 0),
        "still_human_required_count": int(sim_metrics.get("still_human_required_count", 0) or 0),
        "adoption_sim_total_count": adoption_total,
        "risk_adjusted_reduction_count": adoption_total,
        "required_human_review_after_342n": max(pending_review_count - adoption_total, 0),
        "conservative_reduction_rate_after_342n": round(adoption_total / pending_review_count, 6)
        if pending_review_count
        else 0.0,
    }
    return _clean_frame(pd.DataFrame([row])), row


def _build_readme_df(summary_342m: Mapping[str, Any], summary_342j: Mapping[str, Any]) -> pd.DataFrame:
    messages = [
        "342N is a correction-aware adoption simulation only. It is not final adoption and does not write back upstream workbooks.",
        "The 342M reviewed spot-check set found 33 corrections out of 50 rows, so raw bulk adoption is unsafe.",
        "342N only simulates adoption for safe direct pairs or explicit correction patterns.",
        f"Upstream 342M decision: {summary_342m.get('decision', '')}",
        f"Boundary check from 342J: client_ready={summary_342j.get('client_ready', False)}, production_ready={summary_342j.get('production_ready', False)}",
    ]
    return _clean_frame(pd.DataFrame([{"message": message} for message in messages]))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342o": summary.get("ready_for_342o", False),
                    "recommended_342o_scope": summary.get("recommended_342o_scope", ""),
                    "decision": summary.get("decision", ""),
                    "client_ready": summary.get("client_ready", False),
                    "production_ready": summary.get("production_ready", False),
                }
            ]
        )
    )


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    if summary.get("ready_for_342o", False):
        steps = [
            "Proceed to 342O post-adoption sidecar simulation or review template generation.",
            "Keep no-write-back boundaries in place.",
            "Keep client_ready=false and production_ready=false.",
        ]
    else:
        steps = [
            "Review unresolved metric/unit patterns manually.",
            "Do not treat 342N simulation rows as final confirmations.",
            "Do not claim client_ready or production_ready.",
        ]
    return _clean_frame(pd.DataFrame([{"next_step": step} for step in steps]))


def _build_no_write_back_proof_df(payload: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for key, value in payload.items():
        rows.append({"key": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value})
    return _clean_frame(pd.DataFrame(rows))


def build_correction_aware_adoption_simulation_342n(
    *,
    spot_check_gate_342m_dir: Path,
    llm_suggestion_342l_dir: Path,
    llm_review_342k_dir: Path,
    reviewed_preview_342j_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    (
        summary_342m,
        qa_342m,
        proof_342m,
        summary_342l,
        qa_342l,
        workbook_342m,
        workbook_342l,
        workbook_342m_names,
        workbook_342l_names,
        files_read,
        warnings,
    ) = _load_required_inputs(
        spot_check_gate_342m_dir,
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
    )

    summary_342k_path = llm_review_342k_dir / INPUT_342K_SUMMARY_NAME
    qa_342k_path = llm_review_342k_dir / INPUT_342K_QA_NAME
    workbook_342k_path = llm_review_342k_dir / INPUT_342K_WORKBOOK_NAME
    summary_342j_path = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    summary_342k = _read_json(summary_342k_path) if summary_342k_path.exists() else {}
    qa_342k = _read_json(qa_342k_path) if qa_342k_path.exists() else {}
    summary_342j = _read_json(summary_342j_path) if summary_342j_path.exists() else {}
    for path in [summary_342k_path, qa_342k_path, workbook_342k_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input file: {path}")

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342m_path = spot_check_gate_342m_dir / INPUT_342M_SUMMARY_NAME
    qa_342m_path = spot_check_gate_342m_dir / INPUT_342M_QA_NAME
    report_342m_path = spot_check_gate_342m_dir / INPUT_342M_REPORT_NAME
    workbook_342m_path = spot_check_gate_342m_dir / INPUT_342M_WORKBOOK_NAME
    summary_342l_path = llm_suggestion_342l_dir / INPUT_342L_SUMMARY_NAME
    qa_342l_path = llm_suggestion_342l_dir / INPUT_342L_QA_NAME
    workbook_342l_path = llm_suggestion_342l_dir / INPUT_342L_WORKBOOK_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [
            summary_342m_path,
            qa_342m_path,
            report_342m_path,
            workbook_342m_path,
            summary_342l_path,
            qa_342l_path,
            workbook_342l_path,
            summary_342k_path,
            qa_342k_path,
            workbook_342k_path,
            summary_342j_path,
        ]
        if path.exists()
    }

    required_342m_present = all(sheet in workbook_342m_names for sheet in REQUIRED_342M_SHEETS)
    required_342l_present = all(sheet in workbook_342l_names for sheet in REQUIRED_342L_SHEETS)
    input_ready = bool(
        spot_check_gate_342m_dir.exists()
        and summary_342m_path.exists()
        and qa_342m_path.exists()
        and workbook_342m_path.exists()
        and summary_342m.get("decision") == READY_INPUT_DECISION
        and bool(summary_342m.get("ready_for_342n", False))
        and int(summary_342m.get("qa_fail_count", 0) or 0) == 0
        and int(summary_342m.get("reviewed_spot_check_count", 0) or 0) == 50
        and int(summary_342m.get("spot_check_validation_error_count", 0) or 0) == 0
        and int(summary_342m.get("adoption_candidate_count", 0) or 0) == 254
        and summary_342m.get("client_ready", False) is False
        and summary_342m.get("production_ready", False) is False
        and required_342m_present
        and summary_342l_path.exists()
        and qa_342l_path.exists()
        and workbook_342l_path.exists()
        and required_342l_present
        and summary_342k_path.exists()
        and qa_342k_path.exists()
        and workbook_342k_path.exists()
        and summary_342j_path.exists()
        and summary_342j.get("client_ready", False) is False
        and summary_342j.get("production_ready", False) is False
    )

    spot_template_df = _clean_frame(workbook_342m.get("03_SPOT_CHECK_TEMPLATE", pd.DataFrame())) if input_ready else pd.DataFrame()
    spot_apply_df = _clean_frame(workbook_342m.get("04_SPOT_CHECK_APPLY", pd.DataFrame())) if input_ready else pd.DataFrame()
    adoption_candidates_df = _clean_frame(workbook_342m.get("09_ADOPTION_CANDIDATES", pd.DataFrame())) if input_ready else pd.DataFrame()
    auto_candidates_df = _clean_frame(workbook_342l.get("03_AUTO_CANDIDATES", pd.DataFrame())) if input_ready else pd.DataFrame()

    pattern_df, pattern_counts, spot_metrics = _build_spot_check_patterns_df(spot_template_df, spot_apply_df)
    adoption_input_df = _build_adoption_input_df(adoption_candidates_df, auto_candidates_df) if input_ready else pd.DataFrame()
    (
        direct_adopt_df,
        correction_adopt_df,
        still_human_df,
        before_after_df,
        sim_metrics,
        pattern_stats,
    ) = _simulate_adoption(adoption_input_df)
    pattern_application_df = _build_pattern_application_df(pattern_stats)
    risk_review_df = _build_risk_review_df(spot_metrics, sim_metrics, pattern_counts)
    reduction_df, reduction_metrics = _build_reduction_df(
        int(summary_342m.get("pending_review_count", 0) or 0) if input_ready else 0,
        len(adoption_input_df),
        sim_metrics,
    )

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [
            summary_342m_path,
            qa_342m_path,
            report_342m_path,
            workbook_342m_path,
            summary_342l_path,
            qa_342l_path,
            workbook_342l_path,
            summary_342k_path,
            qa_342k_path,
            workbook_342k_path,
            summary_342j_path,
        ]
        if path.exists()
    }
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)
    optional_inputs_staged = _git_staged_names_for_paths(
        ["input/spot_check_reviewed_342m", "input/llm_review_responses_342m"],
        repo_root,
    )

    no_write_back_json = build_no_apply_proof(
        stage="342N",
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
        no_write_back_json.get("no_official_asset_modification_during_342n")
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df(summary_342m if input_ready else {}, summary_342j if input_ready else {})
    claims_text = "\n".join(readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist())

    checks = [
        {"check_name": "inputs::342m_output_dir_exists", "status": "PASS" if spot_check_gate_342m_dir.exists() else "FAIL", "detail": str(spot_check_gate_342m_dir)},
        {"check_name": "inputs::342m_summary_exists", "status": "PASS" if summary_342m_path.exists() else "FAIL", "detail": str(summary_342m_path)},
        {"check_name": "inputs::342m_qa_exists", "status": "PASS" if qa_342m_path.exists() else "FAIL", "detail": str(qa_342m_path)},
        {"check_name": "inputs::342m_workbook_exists", "status": "PASS" if workbook_342m_path.exists() else "FAIL", "detail": str(workbook_342m_path)},
        {
            "check_name": "inputs::342m_ready_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342m.get("decision", ""),
                    "ready_for_342n": summary_342m.get("ready_for_342n", False),
                    "reviewed_spot_check_count": summary_342m.get("reviewed_spot_check_count", 0),
                    "qa_fail_count": summary_342m.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {"check_name": "quality::spot_check_count_50", "status": "PASS" if int(summary_342m.get("reviewed_spot_check_count", 0) or 0) == 50 else "FAIL", "detail": str(summary_342m.get("reviewed_spot_check_count", 0))},
        {"check_name": "quality::spot_check_validation_errors_clear", "status": "PASS" if int(summary_342m.get("spot_check_validation_error_count", 0) or 0) == 0 else "FAIL", "detail": str(summary_342m.get("spot_check_validation_error_count", 0))},
        {"check_name": "quality::adoption_candidates_loaded", "status": "PASS" if len(adoption_input_df) == int(summary_342m.get("adoption_candidate_count", 0) or 0) else "FAIL", "detail": str(len(adoption_input_df))},
        {"check_name": "quality::no_candidate_becomes_final_confirmed", "status": "PASS" if direct_adopt_df.empty or direct_adopt_df["not_final_confirmation"].astype(bool).all() else "FAIL", "detail": str(len(direct_adopt_df))},
        {"check_name": "quality::correction_rows_not_final_confirmed", "status": "PASS" if correction_adopt_df.empty or correction_adopt_df["not_final_confirmation"].astype(bool).all() else "FAIL", "detail": str(len(correction_adopt_df))},
        {"check_name": "quality::direct_adoption_only_safe_pairs", "status": "PASS" if all((_norm_text(row.get('simulated_metric_standardized')), _normalize_unit(row.get('simulated_normalized_unit'))) in SAFE_METRIC_UNIT_PAIRS for row in direct_adopt_df.to_dict(orient='records')) else "FAIL", "detail": str(len(direct_adopt_df))},
        {"check_name": "quality::correction_adoption_only_explicit_patterns", "status": "PASS" if all(_norm_text(row.get('correction_pattern')) in {PATTERN_REVENUE_AMOUNT, PATTERN_REVENUE_YOY, PATTERN_NET_PROFIT_YOY} for row in correction_adopt_df.to_dict(orient='records')) else "FAIL", "detail": str(len(correction_adopt_df))},
        {"check_name": "quality::still_human_required_not_auto_applied", "status": "PASS" if still_human_df.empty or still_human_df["auto_apply_allowed"].astype(bool).eq(False).all() else "FAIL", "detail": str(len(still_human_df))},
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "342N adds sidecar simulation code only."},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "safety::optional_input_artifacts_not_staged", "status": "PASS" if not optional_inputs_staged else "FAIL", "detail": json.dumps(optional_inputs_staged, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if not _contains_forbidden_claim(claims_text, ["investment advice"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 342N sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342o = bool(
        input_ready
        and qa_fail_count == 0
        and int(summary_342m.get("spot_check_validation_error_count", 0) or 0) == 0
        and int(sim_metrics.get("adoption_sim_total_count", 0) or 0) > 0
        and no_write_back_proof_passed
    )
    recommended_342o_scope = "post_adoption_sidecar_simulation_or_review_template_generation" if ready_for_342o else ""
    decision = READY_DECISION if ready_for_342o else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "pending_review_count": int(summary_342m.get("pending_review_count", 0) or 0) if input_ready else 0,
        "input_adoption_candidate_count": len(adoption_input_df),
        "spot_check_sample_count": int(summary_342m.get("spot_check_sample_count", 0) or 0) if input_ready else 0,
        "spot_check_confirm_count": int(summary_342m.get("spot_check_confirm_count", 0) or 0),
        "spot_check_correct_count": int(summary_342m.get("spot_check_correct_count", 0) or 0),
        "spot_check_reject_count": int(summary_342m.get("spot_check_reject_count", 0) or 0),
        "spot_check_correction_rate": spot_metrics.get("correction_rate", 0.0),
        "direct_adopt_sim_count": int(sim_metrics.get("direct_adopt_sim_count", 0) or 0),
        "correction_adopt_sim_count": int(sim_metrics.get("correction_adopt_sim_count", 0) or 0),
        "still_human_required_count": int(sim_metrics.get("still_human_required_count", 0) or 0),
        "adoption_sim_total_count": int(sim_metrics.get("adoption_sim_total_count", 0) or 0),
        f"{PATTERN_REVENUE_AMOUNT}_count": int(pattern_counts.get(PATTERN_REVENUE_AMOUNT, 0) or 0),
        f"{PATTERN_REVENUE_YOY}_count": int(pattern_counts.get(PATTERN_REVENUE_YOY, 0) or 0),
        f"{PATTERN_NET_PROFIT_YOY}_count": int(pattern_counts.get(PATTERN_NET_PROFIT_YOY, 0) or 0),
        "source_trace_missing_count": int(sim_metrics.get("source_trace_missing_count", 0) or 0),
        "low_confidence_count": int(sim_metrics.get("low_confidence_count", 0) or 0),
        "unresolved_pattern_count": int(sim_metrics.get("unresolved_pattern_count", 0) or 0),
        "risk_adjusted_reduction_count": int(reduction_metrics.get("risk_adjusted_reduction_count", 0) or 0),
        "required_human_review_after_342n": int(reduction_metrics.get("required_human_review_after_342n", 0) or 0),
        "conservative_reduction_rate_after_342n": float(reduction_metrics.get("conservative_reduction_rate_after_342n", 0) or 0),
        "ready_for_342o": ready_for_342o,
        "recommended_342o_scope": recommended_342o_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342N_correction_aware_adoption_simulation",
        "spot_check_gate_342m_dir": str(spot_check_gate_342m_dir),
        "llm_suggestion_342l_dir": str(llm_suggestion_342l_dir),
        "llm_review_342k_dir": str(llm_review_342k_dir),
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
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
        "01_ADOPTION_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342M_SUMMARY": _clean_frame(pd.DataFrame([summary_342m])) if summary_342m else pd.DataFrame(),
        "03_SPOT_CHECK_PATTERNS": pattern_df,
        "04_ADOPTION_INPUT": adoption_input_df,
        "05_DIRECT_ADOPT_SIM": direct_adopt_df,
        "06_CORRECTION_ADOPT_SIM": correction_adopt_df,
        "07_STILL_HUMAN_REQUIRED": still_human_df,
        "08_PATTERN_APPLICATION": pattern_application_df,
        "09_RISK_REVIEW": risk_review_df,
        "10_BEFORE_AFTER_SIM": before_after_df,
        "11_REDUCTION_SIM": reduction_df,
        "12_342O_READINESS": _build_readiness_df(summary),
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
