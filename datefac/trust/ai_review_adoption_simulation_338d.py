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
    capture_official_asset_hashes,
)


READY_DECISION = "AI_REVIEW_ADOPTION_SIMULATION_338D_READY"
PARTIAL_DECISION = "AI_REVIEW_ADOPTION_SIMULATION_338D_PARTIAL"
BLOCKED_DECISION = "AI_REVIEW_ADOPTION_SIMULATION_338D_BLOCKED"

DEFAULT_GROUNDED_AI_REVIEW_338C_DIR = Path(r"D:\_datefac\output\grounded_ai_review_338c")
DEFAULT_REVIEWED_STRICTNESS_337D_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\ai_review_adoption_simulation_338d")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

ADOPTION_ACCEPT_CONFIRM = "ACCEPT_MODEL_CONFIRM"
ADOPTION_ACCEPT_DOWNGRADE = "ACCEPT_MODEL_DOWNGRADE"
ADOPTION_ACCEPT_REJECT = "ACCEPT_MODEL_REJECT"
ADOPTION_HOLD = "HOLD_FOR_HUMAN_REVIEW"
ADOPTION_REJECT_BY_RULE = "REJECT_BY_DETERMINISTIC_RULE"
ADOPTION_INVALID = "INVALID_MODEL_RESPONSE"

LEGAL_LIKE_ROLES = {"LEGAL_DISCLOSURE_TABLE", "RATING_STANDARD_TABLE"}


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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _git_status_porcelain_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_cached_names_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _decision_counts(frame: pd.DataFrame, column: str) -> Dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    counts: Dict[str, int] = {}
    for value in frame[column].tolist():
        key = _norm_text(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _is_complete(row: Mapping[str, Any]) -> bool:
    return all(
        _norm_text(row.get(field))
        for field in ["metric_before", "year_before", "value_before", "unit_before"]
    )


def _has_table_context(row: Mapping[str, Any]) -> bool:
    return any(
        _norm_text(row.get(field))
        for field in ["table_year_headers", "matched_table_line", "nearby_previous_row", "nearby_next_row"]
    )


def _is_legal_like(row: Mapping[str, Any]) -> bool:
    role_guess = _norm_text(row.get("table_role_guess"))
    role_337d = _norm_text(row.get("table_role_337d"))
    return role_guess in LEGAL_LIKE_ROLES or role_337d in LEGAL_LIKE_ROLES


def _allow_reject(reason: str, risk_flags: str, suspicious_reason: str, notes: str, guard_result: str, table_role_guess: str) -> bool:
    haystack = " | ".join([reason, risk_flags, suspicious_reason, notes, table_role_guess, guard_result]).lower()
    keywords = [
        "legal",
        "rating",
        "disclosure",
        "duplicate",
        "noise",
        "non-financial",
        "remove_duplicate_reviewed",
        "hard_reject",
    ]
    return any(keyword in haystack for keyword in keywords)


def decide_adoption(row: Mapping[str, Any]) -> Dict[str, Any]:
    model_decision_status = _norm_text(row.get("model_decision_status"))
    model_decision = _norm_text(row.get("model_decision"))
    confidence = _safe_float(row.get("confidence"))
    grounding_source = _norm_text(row.get("grounding_source"))
    raw_quote_valid = bool(row.get("raw_quote_valid"))
    context_quote_valid = bool(row.get("context_quote_valid"))
    guard_result = _norm_text(row.get("deterministic_guard_result"))
    table_role_guess = _norm_text(row.get("table_role_guess"))
    suspicious_reason = _norm_text(row.get("suspicious_reason"))
    risk_flags = _norm_text(row.get("risk_flags"))
    reason = _norm_text(row.get("reason"))
    notes = _norm_text(row.get("notes"))

    adoption_action = ADOPTION_HOLD
    adoption_reason = ""
    recommended_route_after_adoption = "needs_review"
    human_review_required = True

    if model_decision_status == "INVALID_RESPONSE":
        return {
            "adoption_action": ADOPTION_INVALID,
            "adoption_reason": "invalid_model_response",
            "recommended_route_after_adoption": "needs_review",
            "human_review_required": True,
        }

    if guard_result != "PASS":
        return {
            "adoption_action": ADOPTION_REJECT_BY_RULE,
            "adoption_reason": f"deterministic_guard:{guard_result}",
            "recommended_route_after_adoption": "needs_review",
            "human_review_required": True,
        }

    if model_decision == "CONFIRM_REVIEWED":
        if confidence < 0.80:
            adoption_reason = "low_confidence_confirm"
        elif grounding_source not in {"RAW_EVIDENCE", "BOTH"}:
            adoption_reason = "confirm_without_required_grounding"
        elif not raw_quote_valid:
            adoption_reason = "invalid_raw_quote"
        elif grounding_source == "BOTH" and not context_quote_valid:
            adoption_reason = "invalid_context_quote"
        elif _is_legal_like(row):
            adoption_reason = "legal_or_rating_role_not_allowed"
        elif not _is_complete(row):
            adoption_reason = "incomplete_metric_fields"
        elif grounding_source == "BOTH" and not _has_table_context(row):
            adoption_reason = "missing_required_table_context"
        else:
            adoption_action = ADOPTION_ACCEPT_CONFIRM
            adoption_reason = "confirm_passed_adoption_policy"
            recommended_route_after_adoption = "reviewed_preview"
            human_review_required = False
            return {
                "adoption_action": adoption_action,
                "adoption_reason": adoption_reason,
                "recommended_route_after_adoption": recommended_route_after_adoption,
                "human_review_required": human_review_required,
            }
        return {
            "adoption_action": ADOPTION_HOLD,
            "adoption_reason": adoption_reason,
            "recommended_route_after_adoption": "needs_review",
            "human_review_required": True,
        }

    if model_decision == "DOWNGRADE_TO_NEEDS_REVIEW":
        if confidence >= 0.70 and _norm_text(reason) and (_norm_text(risk_flags) or _norm_text(suspicious_reason) or _norm_text(notes)):
            return {
                "adoption_action": ADOPTION_ACCEPT_DOWNGRADE,
                "adoption_reason": "downgrade_passed_adoption_policy",
                "recommended_route_after_adoption": "needs_review",
                "human_review_required": False,
            }
        return {
            "adoption_action": ADOPTION_HOLD,
            "adoption_reason": "downgrade_not_grounded_enough",
            "recommended_route_after_adoption": "needs_review",
            "human_review_required": True,
        }

    if model_decision == "REJECT":
        if confidence >= 0.80 and _allow_reject(reason, risk_flags, suspicious_reason, notes, guard_result, table_role_guess):
            return {
                "adoption_action": ADOPTION_ACCEPT_REJECT,
                "adoption_reason": "reject_passed_adoption_policy",
                "recommended_route_after_adoption": "rejected_or_excluded",
                "human_review_required": False,
            }
        return {
            "adoption_action": ADOPTION_HOLD,
            "adoption_reason": "reject_not_grounded_enough",
            "recommended_route_after_adoption": "needs_review",
            "human_review_required": True,
        }

    if model_decision == "NEEDS_MORE_CONTEXT":
        return {
            "adoption_action": ADOPTION_HOLD,
            "adoption_reason": "needs_more_context_requires_human_review",
            "recommended_route_after_adoption": "needs_review",
            "human_review_required": True,
        }

    return {
        "adoption_action": ADOPTION_INVALID,
        "adoption_reason": "unsupported_model_decision",
        "recommended_route_after_adoption": "needs_review",
        "human_review_required": True,
    }


def _customer_readme_df() -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "topic": "Workbook purpose",
                    "message": "This workbook simulates whether grounded AI review outputs are safe to adopt into dry-run route changes.",
                },
                {
                    "topic": "Boundary",
                    "message": "338D is adoption simulation only. It does not write back to 337D or any upstream workbook.",
                },
                {
                    "topic": "Policy",
                    "message": "Acceptance is stricter than model output. Many rows can still be held for human review even if the model is confident.",
                },
            ]
        )
    )


def build_ai_review_adoption_simulation_338d(
    *,
    grounded_ai_review_338c_dir: Path,
    reviewed_strictness_337d_dir: Path,
    output_dir: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)

    summary_338c_path = grounded_ai_review_338c_dir / "grounded_ai_review_338c_summary.json"
    plan_338c_path = grounded_ai_review_338c_dir / "grounded_ai_review_338c_plan.xlsx"
    reviewed_workbook_path = reviewed_strictness_337d_dir / "real_test_mineru_client_export_337d.xlsx"

    blocked_reasons: List[str] = []
    for path in [summary_338c_path, plan_338c_path, reviewed_workbook_path]:
        if not path.exists():
            blocked_reasons.append(f"Missing required input: {path}")

    if blocked_reasons:
        summary = {
            "generated_at_utc": _utc_now(),
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": len(blocked_reasons),
            "decision": BLOCKED_DECISION,
        }
        return {
            "summary": summary,
            "manifest": {},
            "qa_json": {
                "decision": BLOCKED_DECISION,
                "qa_fail_count": len(blocked_reasons),
                "checks": [],
                "blocked_reasons": blocked_reasons,
            },
            "workbook_sheets": {},
        }

    summary_338c = json.loads(summary_338c_path.read_text(encoding="utf-8"))
    grounded_df = _read_excel(plan_338c_path, "02_GROUNDED_ADJUDICATION_PLAN")
    policy_notes_df = _read_excel(plan_338c_path, "09_PROMPT_AND_SCHEMA_NOTES")

    adoption_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(grounded_df.to_dict(orient="records"), start=1):
        decision = decide_adoption(row)
        adoption_rows.append(
            {
                "adoption_id": f"338d::{index:03d}",
                "adjudication_id": _norm_text(row.get("adjudication_id")),
                "document": _norm_text(row.get("document")),
                "source_sheet": _norm_text(row.get("source_sheet")),
                "source_row_no": _norm_text(row.get("source_row_no")),
                "metric_before": _norm_text(row.get("metric_before")),
                "year_before": _norm_text(row.get("year_before")),
                "value_before": _norm_text(row.get("value_before")),
                "unit_before": _norm_text(row.get("unit_before")),
                "model_decision": _norm_text(row.get("model_decision")),
                "confidence": _safe_float(row.get("confidence")),
                "grounding_source": _norm_text(row.get("grounding_source")),
                "raw_quote_valid": bool(row.get("raw_quote_valid")),
                "context_quote_valid": bool(row.get("context_quote_valid")),
                "deterministic_guard_result": _norm_text(row.get("deterministic_guard_result")),
                "adoption_action": decision["adoption_action"],
                "adoption_reason": decision["adoption_reason"],
                "recommended_route_after_adoption": decision["recommended_route_after_adoption"],
                "human_review_required": decision["human_review_required"],
                "model_name": _norm_text(row.get("model_name")),
                "table_role_guess": _norm_text(row.get("table_role_guess")),
                "model_decision_status": _norm_text(row.get("model_decision_status")),
            }
        )

    adoption_df = _clean_frame(pd.DataFrame(adoption_rows))
    accepted_confirms_df = adoption_df[adoption_df["adoption_action"] == ADOPTION_ACCEPT_CONFIRM].copy()
    accepted_downgrades_df = adoption_df[adoption_df["adoption_action"] == ADOPTION_ACCEPT_DOWNGRADE].copy()
    accepted_rejects_df = adoption_df[adoption_df["adoption_action"] == ADOPTION_ACCEPT_REJECT].copy()
    hold_df = adoption_df[adoption_df["adoption_action"] == ADOPTION_HOLD].copy()
    rejected_by_rule_df = adoption_df[adoption_df["adoption_action"] == ADOPTION_REJECT_BY_RULE].copy()
    invalid_df = adoption_df[adoption_df["adoption_action"] == ADOPTION_INVALID].copy()

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)

    counts = _decision_counts(adoption_df, "adoption_action")
    grounded_confirm_count = _decision_counts(grounded_df, "recommended_final_action").get("CONFIRM_REVIEWED", 0)

    legal_like_accept_count = 0
    if not accepted_confirms_df.empty:
        legal_like_accept_count = int(
            accepted_confirms_df["table_role_guess"].astype(str).isin(sorted(LEGAL_LIKE_ROLES)).sum()
        )
    low_confidence_confirm_accept_count = 0
    if not accepted_confirms_df.empty:
        low_confidence_confirm_accept_count = int((accepted_confirms_df["confidence"].astype(float) < 0.80).sum())
    invalid_accepted_count = int(
        adoption_df[
            (adoption_df["model_decision_status"] == "INVALID_RESPONSE")
            & (adoption_df["adoption_action"].isin([ADOPTION_ACCEPT_CONFIRM, ADOPTION_ACCEPT_DOWNGRADE, ADOPTION_ACCEPT_REJECT]))
        ].shape[0]
    )
    hard_reject_overridden_count = int(
        adoption_df[
            (adoption_df["deterministic_guard_result"] != "PASS")
            & (adoption_df["adoption_action"] == ADOPTION_ACCEPT_CONFIRM)
        ].shape[0]
    )

    qa_checks = [
        {"check_name": "input_338c_workbook_exists", "status": "PASS" if plan_338c_path.exists() else "FAIL", "detail": str(plan_338c_path)},
        {"check_name": "row_count_is_50", "status": "PASS" if len(adoption_df) == 50 else "FAIL", "detail": str(len(adoption_df))},
        {"check_name": "no_invalid_model_response_accepted", "status": "PASS" if invalid_accepted_count == 0 else "FAIL", "detail": str(invalid_accepted_count)},
        {"check_name": "no_low_confidence_confirm_accepted", "status": "PASS" if low_confidence_confirm_accept_count == 0 else "FAIL", "detail": str(low_confidence_confirm_accept_count)},
        {"check_name": "no_legal_or_rating_row_accepted_as_reviewed", "status": "PASS" if legal_like_accept_count == 0 else "FAIL", "detail": str(legal_like_accept_count)},
        {"check_name": "no_deterministic_hard_reject_overridden", "status": "PASS" if hard_reject_overridden_count == 0 else "FAIL", "detail": str(hard_reject_overridden_count)},
        {"check_name": "accepted_confirm_count_not_above_338c", "status": "PASS" if len(accepted_confirms_df) <= grounded_confirm_count else "FAIL", "detail": f"{len(accepted_confirms_df)} <= {grounded_confirm_count}"},
        {"check_name": "hold_for_human_review_present", "status": "PASS" if len(hold_df) > 0 else "FAIL", "detail": str(len(hold_df))},
        {"check_name": "client_ready_false", "status": "PASS", "detail": "False"},
        {"check_name": "production_ready_false", "status": "PASS", "detail": "False"},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "client_ready": False,
        "production_ready": False,
        "grounded_ai_review_338c_dir": str(grounded_ai_review_338c_dir),
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "output_dir": str(output_dir),
        "input_338c_row_count": len(adoption_df),
        "accept_model_confirm_count": len(accepted_confirms_df),
        "accept_model_downgrade_count": len(accepted_downgrades_df),
        "accept_model_reject_count": len(accepted_rejects_df),
        "hold_for_human_review_count": len(hold_df),
        "reject_by_deterministic_rule_count": len(rejected_by_rule_df),
        "invalid_model_response_count": len(invalid_df),
        "deterministic_rule_override_count": hard_reject_overridden_count,
        "suggest_set_ai_review_model_default": len(accepted_confirms_df) > 0 and hard_reject_overridden_count == 0 and len(invalid_df) == 0,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "338D_ai_review_adoption_simulation",
        "grounded_ai_review_338c_dir": str(grounded_ai_review_338c_dir),
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "ai_review_adoption_simulation_338d_summary.json"),
            "manifest_json": str(output_dir / "ai_review_adoption_simulation_338d_manifest.json"),
            "qa_json": str(output_dir / "ai_review_adoption_simulation_338d_qa.json"),
            "report_md": str(output_dir / "ai_review_adoption_simulation_338d_report.md"),
            "plan_xlsx": str(output_dir / "ai_review_adoption_simulation_338d_plan.xlsx"),
        },
    }

    qa_json = {
        "decision": decision,
        "qa_fail_count": qa_fail_count,
        "checks": qa_checks,
        "blocked_reasons": blocked_reasons,
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
    }

    workbook_sheets = {
        "00_README": _customer_readme_df(),
        "01_ADOPTION_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_ADOPTION_PLAN": adoption_df,
        "03_ACCEPTED_CONFIRMS": _clean_frame(accepted_confirms_df),
        "04_ACCEPTED_DOWNGRADES": _clean_frame(accepted_downgrades_df),
        "05_ACCEPTED_REJECTS": _clean_frame(accepted_rejects_df),
        "06_HOLD_FOR_HUMAN_REVIEW": _clean_frame(hold_df),
        "07_REJECTED_BY_RULE": _clean_frame(rejected_by_rule_df),
        "08_INVALID_MODEL_RESPONSES": _clean_frame(invalid_df),
        "09_ADOPTION_POLICY_NOTES": _clean_frame(policy_notes_df),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "workbook_sheets": workbook_sheets,
    }
