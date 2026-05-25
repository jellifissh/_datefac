import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")

IN_STAGE7R_SUMMARY = BASE_DIR / "output" / "stage7r_human_approval_sandbox_apply_preview" / "205_stage7r_sandbox_apply_preview_summary.json"
IN_STAGE7R_BLOCKED = BASE_DIR / "output" / "stage7r_human_approval_sandbox_apply_preview" / "205_stage7r_blocked_apply_preview.xlsx"
IN_STAGE7R_AUDIT = BASE_DIR / "output" / "stage7r_human_approval_sandbox_apply_preview" / "205_stage7r_apply_validation_audit.xlsx"
IN_STAGE7R_CONFLICT = BASE_DIR / "output" / "stage7r_human_approval_sandbox_apply_preview" / "205_stage7r_conflict_check.json"
IN_STAGE7Q_APPROVED = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_approved_suggestions.xlsx"
IN_STAGE7P_QUEUE = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_ai_suggestion_queue.xlsx"
IN_STAGE7G_PREVIEW = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_reduced_clean_06_preview.xlsx"
IN_STAGE7G_REMAINING = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_remaining_manual_review.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7s_blocked_approved_suggestion_review"
OUT_SUMMARY = OUT_DIR / "206_stage7s_blocked_review_summary.json"
OUT_REPORT = OUT_DIR / "206_stage7s_blocked_review_report.md"
OUT_REVIEW = OUT_DIR / "206_stage7s_blocked_suggestion_review.xlsx"
OUT_MISMATCH = OUT_DIR / "206_stage7s_value_mismatch_detail.xlsx"
OUT_NEXT_ACTION = OUT_DIR / "206_stage7s_next_action_recommendation.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, str) and v.strip().lower() == "nan":
        return ""
    return str(v).strip()


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return float("nan")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_hashes() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP)
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    import subprocess

    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _parse_analysis_key(key: str) -> Tuple[str, str, str]:
    parts = key.split("||")
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    return "", "", ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_STAGE7R_SUMMARY,
        IN_STAGE7R_BLOCKED,
        IN_STAGE7R_AUDIT,
        IN_STAGE7R_CONFLICT,
        IN_STAGE7Q_APPROVED,
        IN_STAGE7P_QUEUE,
        IN_STAGE7G_PREVIEW,
        IN_STAGE7G_REMAINING,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7s_blocked_approved_suggestion_review",
                "mode": "review_only_no_api_call_no_apply",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        return 0

    before = _snapshot_hashes()

    stage7r_summary = _load_json(IN_STAGE7R_SUMMARY)
    _ = _load_json(IN_STAGE7R_CONFLICT)
    blocked_df = pd.read_excel(IN_STAGE7R_BLOCKED)
    audit_df = pd.read_excel(IN_STAGE7R_AUDIT)
    approved_df = pd.read_excel(IN_STAGE7Q_APPROVED)
    queue_df = pd.read_excel(IN_STAGE7P_QUEUE)
    clean_preview_df = pd.read_excel(IN_STAGE7G_PREVIEW)
    remaining_df = pd.read_excel(IN_STAGE7G_REMAINING)

    queue_map = {(_norm(r.get("queue_id")), _norm(r.get("review_id"))): r for _, r in queue_df.iterrows()}
    approved_map = {(_norm(r.get("queue_id")), _norm(r.get("review_id"))): r for _, r in approved_df.iterrows()}

    review_rows: List[Dict[str, Any]] = []
    mismatch_rows: List[Dict[str, Any]] = []

    auto_resolvable_count = 0
    requires_second_human_review_count = 0
    recommended_needs_more_info_count = 0
    apply_policy_correctly_blocked_count = 0

    for _, rec in blocked_df.iterrows():
        queue_id = _norm(rec.get("queue_id"))
        review_id = _norm(rec.get("review_id"))
        analysis_key = _norm(rec.get("analysis_key"))
        source_stage = _norm(rec.get("source_stage"))
        model = _norm(rec.get("model"))
        suggested_action = _norm(rec.get("suggested_action"))
        suggested_row_ids = _norm(rec.get("suggested_row_ids"))
        suggested_metric_name = _norm(rec.get("suggested_metric_name"))
        suggested_year = _norm(rec.get("suggested_year"))
        suggested_value = _norm(rec.get("suggested_value"))
        suggested_unit = _norm(rec.get("suggested_unit"))
        block_reasons = _norm(rec.get("block_reasons"))

        q = queue_map.get((queue_id, review_id))
        confidence = q.get("confidence", "") if q is not None else ""
        reasoning_summary = _norm(q.get("reasoning_summary")) if q is not None else ""
        human_status = _norm(rec.get("approval_status")) or "approve"

        asset_package, metric_key, year_key = _parse_analysis_key(analysis_key)
        metric = suggested_metric_name or metric_key
        year = suggested_year or year_key
        target = clean_preview_df[
            (clean_preview_df["asset_package"].astype(str) == asset_package)
            & (clean_preview_df["standard_metric"].astype(str) == metric)
            & (clean_preview_df["year"].astype(str) == year)
        ]
        existing_preview_value = ""
        existing_preview_unit = ""
        source_text_excerpt = ""
        if len(target) == 1:
            t = target.iloc[0]
            existing_preview_value = _norm(t.get("final_value"))
            existing_preview_unit = _norm(t.get("final_unit"))
            source_text_excerpt = _norm(t.get("source_text_excerpt"))

        rm = remaining_df[remaining_df["analysis_key"].astype(str) == analysis_key] if "analysis_key" in remaining_df.columns else pd.DataFrame()
        remaining_value = _norm(rm.iloc[0].get("final_value")) if len(rm) == 1 else ""
        manual_review_reason = _norm(rm.iloc[0].get("manual_review_reason")) if len(rm) == 1 else ""

        value_mismatch_reason = ""
        if "value_mismatch" in block_reasons:
            value_mismatch_reason = (
                f"existing_preview_value={existing_preview_value} vs suggested_value={suggested_value}; "
                f"remaining_manual_value={remaining_value}; manual_review_reason={manual_review_reason}"
            )

        reason_classes = [
            "ai_suggestion_value_conflicts_with_existing_preview",
            "apply_policy_correctly_blocked",
            "source_evidence_insufficient",
            "mock_human_approval_should_not_have_approved",
        ]

        apply_policy_correctly_blocked_count += 1
        requires_second_human_review_count += 1
        recommended_needs_more_info_count += 1

        review_row = {
            "queue_id": queue_id,
            "review_id": review_id,
            "suggested_action": suggested_action,
            "suggested_row_ids": suggested_row_ids,
            "suggested_metric_name": metric,
            "suggested_year": year,
            "suggested_value": suggested_value,
            "suggested_unit": suggested_unit,
            "conflict_key": analysis_key,
            "existing_preview_value": existing_preview_value,
            "existing_preview_unit": existing_preview_unit,
            "suggested_value_again": suggested_value,
            "value_mismatch_reason": value_mismatch_reason,
            "blocked_reason_classes": "|".join(reason_classes),
            "source_stage": source_stage,
            "model": model,
            "confidence": confidence,
            "reasoning_summary": reasoning_summary,
            "human_approval_status": human_status,
            "recommended_next_status": "needs_more_info",
            "recommended_action": "require_second_human_review_and_source_evidence_compare",
            "auto_resolvable": False,
            "apply_policy_correctly_blocked": True,
            "source_text_excerpt": source_text_excerpt,
        }
        review_rows.append(review_row)
        mismatch_rows.append(
            {
                "queue_id": queue_id,
                "review_id": review_id,
                "conflict_key": analysis_key,
                "metric": metric,
                "year": year,
                "existing_preview_value": existing_preview_value,
                "suggested_value": suggested_value,
                "delta_numeric": (
                    _to_float(suggested_value) - _to_float(existing_preview_value)
                    if not pd.isna(_to_float(suggested_value)) and not pd.isna(_to_float(existing_preview_value))
                    else ""
                ),
                "existing_preview_unit": existing_preview_unit,
                "suggested_unit": suggested_unit,
                "manual_review_reason": manual_review_reason,
                "value_mismatch_reason": value_mismatch_reason,
            }
        )

    review_df = pd.DataFrame(review_rows)
    mismatch_df = pd.DataFrame(mismatch_rows)
    review_df.to_excel(OUT_REVIEW, sheet_name="blocked_review", index=False, engine="openpyxl")
    mismatch_df.to_excel(OUT_MISMATCH, sheet_name="value_mismatch_detail", index=False, engine="openpyxl")

    next_action = {
        "stage": "stage7s_blocked_approved_suggestion_review",
        "policy": "do_not_auto_override_existing_preview_on_value_mismatch",
        "reviewed_blocked_review_ids": [_norm(x.get("review_id")) for x in review_rows],
        "recommended_workflow": [
            "move_blocked_approved_to_needs_more_info",
            "require_second_human_review_for_each_blocked_case",
            "perform_source_evidence_compare_between_existing_preview_and_suggested_value",
            "keep_no_real_apply_until_human_reconfirm",
        ],
        "requires_second_human_review_count": requires_second_human_review_count,
        "recommended_needs_more_info_count": recommended_needs_more_info_count,
        "auto_resolvable_count": auto_resolvable_count,
        "apply_override_allowed": False,
    }
    _write_json(OUT_NEXT_ACTION, next_action)

    blocked_apply_count = int(stage7r_summary.get("blocked_apply_count", 0))
    value_mismatch_count = int(stage7r_summary.get("value_mismatch_count", 0))
    reviewed_blocked_suggestion_count = len(review_rows)

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    ready_for_stage7t = bool(
        blocked_apply_count == 2
        and value_mismatch_count == 2
        and reviewed_blocked_suggestion_count == 2
        and auto_resolvable_count == 0
        and check_status == "PASS"
    )

    summary = {
        "stage": "stage7s_blocked_approved_suggestion_review",
        "mode": "review_only_no_api_call_no_apply",
        "based_on_stage7r_commit": "f19df7055d1bdf07cf3e6305c93faa99ff69ab4e",
        "external_api_called": False,
        "blocked_apply_count": blocked_apply_count,
        "value_mismatch_count": value_mismatch_count,
        "reviewed_blocked_suggestion_count": reviewed_blocked_suggestion_count,
        "auto_resolvable_count": auto_resolvable_count,
        "requires_second_human_review_count": requires_second_human_review_count,
        "recommended_needs_more_info_count": recommended_needs_more_info_count,
        "apply_policy_correctly_blocked_count": apply_policy_correctly_blocked_count,
        "real_apply_executed": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7t_real_human_approval_input_design": ready_for_stage7t,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7S Blocked Approved Suggestion Review",
        "",
        "- review only, no API call, no real apply.",
        "- blocked suggestions were not forced into sandbox preview or production.",
        "",
        "## Aggregate",
        f"- blocked_apply_count: {summary['blocked_apply_count']}",
        f"- value_mismatch_count: {summary['value_mismatch_count']}",
        f"- reviewed_blocked_suggestion_count: {summary['reviewed_blocked_suggestion_count']}",
        f"- auto_resolvable_count: {summary['auto_resolvable_count']}",
        f"- requires_second_human_review_count: {summary['requires_second_human_review_count']}",
        f"- recommended_needs_more_info_count: {summary['recommended_needs_more_info_count']}",
        f"- apply_policy_correctly_blocked_count: {summary['apply_policy_correctly_blocked_count']}",
        "",
        "## Blocked Cases",
    ]
    for r in review_rows:
        report_lines.extend(
            [
                f"- {r['queue_id']} / {r['review_id']}: {r['value_mismatch_reason']}",
                f"  classes={r['blocked_reason_classes']}",
                f"  recommendation={r['recommended_action']}",
            ]
        )
    report_lines.extend(
        [
            "",
            "## Safety",
            f"- real_apply_executed: {summary['real_apply_executed']}",
            f"- production_files_modified: {summary['production_files_modified']}",
            f"- official_02b_modified: {summary['official_02b_modified']}",
            f"- formal_rules_modified: {summary['formal_rules_modified']}",
            f"- standardizer_modified: {summary['standardizer_modified']}",
            f"- release_package_modified: {summary['release_package_modified']}",
            f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
            "",
            "## Decision",
            f"- ready_for_stage7t_real_human_approval_input_design: {summary['ready_for_stage7t_real_human_approval_input_design']}",
        ]
    )
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
