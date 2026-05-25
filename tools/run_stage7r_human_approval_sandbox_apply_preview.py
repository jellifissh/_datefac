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

IN_STAGE7Q_SUMMARY = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_human_approval_flow_summary.json"
IN_APPROVED = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_approved_suggestions.xlsx"
IN_REJECTED = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_rejected_by_human.xlsx"
IN_NEEDS_INFO = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_needs_more_info_queue.xlsx"
IN_STAGE7Q_PREVIEW = BASE_DIR / "output" / "stage7q_human_approval_flow_design" / "204_stage7q_apply_preview_sandbox.xlsx"
IN_STAGE7P_QUEUE = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_ai_suggestion_queue.xlsx"
IN_STAGE7G_PREVIEW = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_reduced_clean_06_preview.xlsx"
IN_STAGE7G_REMAINING = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_remaining_manual_review.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7r_human_approval_sandbox_apply_preview"
OUT_SUMMARY = OUT_DIR / "205_stage7r_sandbox_apply_preview_summary.json"
OUT_REPORT = OUT_DIR / "205_stage7r_sandbox_apply_preview_report.md"
OUT_APPROVED_INPUT = OUT_DIR / "205_stage7r_approved_input_suggestions.xlsx"
OUT_SANDBOX_PREVIEW = OUT_DIR / "205_stage7r_sandbox_apply_preview.xlsx"
OUT_BLOCKED = OUT_DIR / "205_stage7r_blocked_apply_preview.xlsx"
OUT_AUDIT = OUT_DIR / "205_stage7r_apply_validation_audit.xlsx"
OUT_CONFLICT = OUT_DIR / "205_stage7r_conflict_check.json"

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


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


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


def _is_eps(metric_name: str) -> bool:
    t = metric_name.lower()
    return "eps" in t or "每股收益" in metric_name


def _build_key(asset_package: str, metric: str, year: str) -> str:
    return f"{asset_package}||{metric}||{year}"


def _suggested_value_empty_allowed(action: str) -> bool:
    return action in {"keep_manual_review"}


def _is_illegal_unit(unit: str) -> bool:
    return _norm(unit).lower() in {"", "nan", "none", "null", "非法单位"}


def _extract_asset_from_key(original_request_id: str) -> Tuple[str, str, str]:
    parts = original_request_id.split("||")
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    return "", "", ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_STAGE7Q_SUMMARY,
        IN_APPROVED,
        IN_REJECTED,
        IN_NEEDS_INFO,
        IN_STAGE7Q_PREVIEW,
        IN_STAGE7P_QUEUE,
        IN_STAGE7G_PREVIEW,
        IN_STAGE7G_REMAINING,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7r_human_approval_sandbox_apply_preview",
                "mode": "sandbox_apply_preview_no_api_call_no_real_apply",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        return 0

    before = _snapshot_hashes()

    stage7q_summary = _load_json(IN_STAGE7Q_SUMMARY)
    approved_df = pd.read_excel(IN_APPROVED)
    rejected_df = pd.read_excel(IN_REJECTED)
    needs_info_df = pd.read_excel(IN_NEEDS_INFO)
    stage7q_preview_df = pd.read_excel(IN_STAGE7Q_PREVIEW)
    queue_df = pd.read_excel(IN_STAGE7P_QUEUE)
    clean_preview_df = pd.read_excel(IN_STAGE7G_PREVIEW)
    _ = pd.read_excel(IN_STAGE7G_REMAINING)

    queue_map = {(_norm(r["queue_id"]), _norm(r["review_id"])): r for _, r in queue_df.iterrows()}
    stage7q_preview_map = {(_norm(r["queue_id"]), _norm(r["review_id"])): r for _, r in stage7q_preview_df.iterrows()}

    approved_rows_full: List[Dict[str, Any]] = []
    for _, a in approved_df.iterrows():
        key = (_norm(a.get("queue_id")), _norm(a.get("review_id")))
        q = queue_map.get(key)
        if q is None:
            continue
        p = stage7q_preview_map.get(key)
        item = q.to_dict()
        item["approval_status"] = "approve"
        item["apply_allowed"] = True
        item["apply_target"] = "sandbox_apply_preview_only"
        item["real_apply_executed"] = False
        if p is not None:
            item["human_decision"] = _norm(p.get("human_decision"))
            item["human_comment"] = _norm(p.get("human_comment"))
            item["approved_by"] = _norm(p.get("approved_by"))
            item["approved_at"] = _norm(p.get("approved_at"))
        approved_rows_full.append(item)

    approved_input_df = pd.DataFrame(approved_rows_full)
    approved_input_df.to_excel(OUT_APPROVED_INPUT, sheet_name="approved_input", index=False, engine="openpyxl")

    sandbox_before = len(clean_preview_df)
    sandbox_preview = clean_preview_df.copy()

    validation_rows: List[Dict[str, Any]] = []
    blocked_rows: List[Dict[str, Any]] = []
    apply_rows: List[Dict[str, Any]] = []

    duplicate_key_count = 0
    value_mismatch_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0
    bad_eps_ratio_count = 0

    for rec in approved_rows_full:
        queue_id = _norm(rec.get("queue_id"))
        review_id = _norm(rec.get("review_id"))
        approval_status = "approve"
        requires_human_approval = _as_bool(rec.get("requires_human_approval"))
        suggested_action = _norm(rec.get("suggested_action"))
        suggested_row_ids = _norm(rec.get("suggested_row_ids"))
        suggested_metric_name = _norm(rec.get("suggested_metric_name"))
        suggested_year = _norm(rec.get("suggested_year"))
        suggested_value = _norm(rec.get("suggested_value"))
        suggested_unit = _norm(rec.get("suggested_unit"))
        original_request_id = _norm(rec.get("original_request_id"))
        asset_package, metric_from_key, year_from_key = _extract_asset_from_key(original_request_id)
        metric = suggested_metric_name or metric_from_key
        year = suggested_year or year_from_key
        analysis_key = _build_key(asset_package, metric, year) if asset_package and metric and year else ""

        errors: List[str] = []
        if approval_status != "approve":
            errors.append("approval_status_not_approve")
        if not requires_human_approval:
            errors.append("requires_human_approval_false")
        if not suggested_row_ids and suggested_action not in {"keep_manual_review", "split_metric", "exclude"}:
            errors.append("suggested_row_ids_empty_not_allowed")
        if not suggested_value and not _suggested_value_empty_allowed(suggested_action):
            errors.append("suggested_value_empty_not_allowed")
        if _is_illegal_unit(suggested_unit) and suggested_action != "keep_manual_review":
            errors.append("illegal_unit")

        if _is_eps(metric) and ("ratio" in suggested_unit.lower() or "%" in suggested_unit):
            bad_eps_ratio_count += 1
            errors.append("eps_ratio_error")

        target_rows = pd.DataFrame()
        if analysis_key:
            target_rows = sandbox_preview[sandbox_preview.apply(lambda r: _build_key(_norm(r.get("asset_package")), _norm(r.get("standard_metric")), _norm(r.get("year"))) == analysis_key, axis=1)]
        if len(target_rows) > 1:
            duplicate_key_count += 1
            errors.append("duplicate_key_in_sandbox_preview")
        if len(target_rows) == 1:
            tr = target_rows.iloc[0]
            final_value = _norm(tr.get("final_value"))
            final_unit = _norm(tr.get("final_unit"))
            if _norm(year) and _norm(year) != _norm(tr.get("year")):
                year_conflict_count += 1
                errors.append("year_conflict")
            # Compare numeric value if both numeric
            sv = _to_float(suggested_value)
            fv = _to_float(final_value)
            if not pd.isna(sv) and not pd.isna(fv):
                if abs(sv - fv) > 1e-9:
                    value_mismatch_count += 1
                    errors.append("value_mismatch")
            elif suggested_value and final_value and suggested_value != final_value:
                value_mismatch_count += 1
                errors.append("value_mismatch")
            if suggested_unit and final_unit and suggested_unit != final_unit:
                unit_conflict_count += 1
                errors.append("unit_conflict")

        blocked = len(errors) > 0
        apply_allowed = (not blocked) and approval_status == "approve" and requires_human_approval

        row_out = {
            "queue_id": queue_id,
            "review_id": review_id,
            "analysis_key": analysis_key,
            "source_stage": _norm(rec.get("source_stage")),
            "model": _norm(rec.get("model")),
            "suggested_action": suggested_action,
            "suggested_row_ids": suggested_row_ids,
            "suggested_metric_name": metric,
            "suggested_year": year,
            "suggested_value": suggested_value,
            "suggested_unit": suggested_unit,
            "approval_status": approval_status,
            "requires_human_approval": requires_human_approval,
            "apply_allowed_system": apply_allowed,
            "blocked": blocked,
            "block_reasons": "|".join(errors),
            "real_apply_executed": False,
            "apply_target": "sandbox_apply_preview_only" if apply_allowed else "none",
            "audit_note": _norm(rec.get("audit_note")) + ";stage7r_sandbox_preview_only",
        }
        validation_rows.append(row_out)

        if blocked:
            blocked_rows.append(row_out)
        else:
            apply_rows.append(row_out)

    # Build output sandbox apply preview by appending approved-apply rows as AI preview proposals.
    if apply_rows:
        add_rows = []
        for r in apply_rows:
            add_rows.append(
                {
                    "source_pdf": "",
                    "asset_package": _extract_asset_from_key(_norm(next((x.get("original_request_id") for x in approved_rows_full if _norm(x.get("queue_id")) == r["queue_id"] and _norm(x.get("review_id")) == r["review_id"]), "")))[0],
                    "standard_metric": _norm(r.get("suggested_metric_name")),
                    "year": _norm(r.get("suggested_year")),
                    "final_value": _norm(r.get("suggested_value")),
                    "final_unit": _norm(r.get("suggested_unit")),
                    "statement_type": "",
                    "source_pdf_name": "",
                    "page_number": "",
                    "raw_metric_name": "",
                    "source_text_excerpt": "",
                    "policy_score": "",
                    "policy_action": "STAGE7R_HUMAN_APPROVED_SANDBOX_PREVIEW",
                    "conflict_category": "human_approved_sandbox_preview",
                    "stage7r_queue_id": _norm(r.get("queue_id")),
                    "stage7r_review_id": _norm(r.get("review_id")),
                    "stage7r_apply_allowed": True,
                    "stage7r_real_apply_executed": False,
                    "stage7r_note": "sandbox only no production write",
                }
            )
        sandbox_preview = pd.concat([sandbox_preview, pd.DataFrame(add_rows)], ignore_index=True, sort=False)

    sandbox_after = len(sandbox_preview)

    sandbox_preview.to_excel(OUT_SANDBOX_PREVIEW, sheet_name="sandbox_apply_preview", index=False, engine="openpyxl")
    pd.DataFrame(blocked_rows).to_excel(OUT_BLOCKED, sheet_name="blocked_apply_preview", index=False, engine="openpyxl")
    pd.DataFrame(validation_rows).to_excel(OUT_AUDIT, sheet_name="apply_validation_audit", index=False, engine="openpyxl")

    conflict_json = {
        "duplicate_key_count": duplicate_key_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "blocked_review_ids": [r["review_id"] for r in blocked_rows],
        "blocked_queue_ids": [r["queue_id"] for r in blocked_rows],
    }
    _write_json(OUT_CONFLICT, conflict_json)

    approved_input_suggestion_count = len(approved_rows_full)
    sandbox_apply_attempt_count = approved_input_suggestion_count
    sandbox_apply_success_count = len(apply_rows)
    blocked_apply_count = len(blocked_rows)

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    ready_for_stage7s = bool(
        approved_input_suggestion_count == 2
        and sandbox_apply_attempt_count == 2
        and bad_eps_ratio_count == 0
        and check_status == "PASS"
    )

    summary = {
        "stage": "stage7r_human_approval_sandbox_apply_preview",
        "mode": "sandbox_apply_preview_no_api_call_no_real_apply",
        "based_on_stage7q_commit": "f4faaab49f0f45d0cfc54c267891e43534d5fb04",
        "external_api_called": False,
        "approved_input_suggestion_count": approved_input_suggestion_count,
        "sandbox_apply_attempt_count": sandbox_apply_attempt_count,
        "sandbox_apply_success_count": sandbox_apply_success_count,
        "blocked_apply_count": blocked_apply_count,
        "sandbox_preview_row_count_before": sandbox_before,
        "sandbox_preview_row_count_after": sandbox_after,
        "duplicate_key_count": duplicate_key_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "real_apply_executed": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7s_real_human_approval_input_design": ready_for_stage7s,
        "rejected_input_count": len(rejected_df),
        "needs_more_info_input_count": len(needs_info_df),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7R Human-approved AI Suggestion Sandbox Apply Preview",
        "",
        "- No external API call.",
        "- Sandbox preview only. No production 06 write.",
        "- No real apply executed.",
        "",
        "## Input",
        f"- approved_input_suggestion_count: {summary['approved_input_suggestion_count']}",
        f"- rejected_input_count: {summary['rejected_input_count']}",
        f"- needs_more_info_input_count: {summary['needs_more_info_input_count']}",
        "",
        "## Apply Result",
        f"- sandbox_apply_attempt_count: {summary['sandbox_apply_attempt_count']}",
        f"- sandbox_apply_success_count: {summary['sandbox_apply_success_count']}",
        f"- blocked_apply_count: {summary['blocked_apply_count']}",
        f"- sandbox_preview_row_count_before/after: {summary['sandbox_preview_row_count_before']}/{summary['sandbox_preview_row_count_after']}",
        "",
        "## Conflict Check",
        f"- duplicate_key_count: {summary['duplicate_key_count']}",
        f"- value_mismatch_count: {summary['value_mismatch_count']}",
        f"- unit_conflict_count: {summary['unit_conflict_count']}",
        f"- year_conflict_count: {summary['year_conflict_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
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
        f"- ready_for_stage7s_real_human_approval_input_design: {summary['ready_for_stage7s_real_human_approval_input_design']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
