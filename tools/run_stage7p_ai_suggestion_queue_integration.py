import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")

IN_STAGE7O_SUMMARY = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_five_case_summary.json"
IN_STAGE7O_SELECTED = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_selected_requests.jsonl"
IN_STAGE7O_AUDIT = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_validation_audit.xlsx"
IN_STAGE7O_VALIDATED = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_validated_suggestions.xlsx"
IN_STAGE7O_REJECTED = BASE_DIR / "output" / "stage7o_five_case_new_model_batch_test" / "200_stage7o_rejected_suggestions.xlsx"

IN_STAGE7O2_SUMMARY = BASE_DIR / "output" / "stage7o2_failed_case_retry" / "202_stage7o2_failed_case_retry_summary.json"
IN_STAGE7O2_SELECTED = BASE_DIR / "output" / "stage7o2_failed_case_retry" / "202_stage7o2_retry_selected_requests.jsonl"
IN_STAGE7O2_AUDIT = BASE_DIR / "output" / "stage7o2_failed_case_retry" / "202_stage7o2_validation_audit.xlsx"
IN_STAGE7O2_VALIDATED = BASE_DIR / "output" / "stage7o2_failed_case_retry" / "202_stage7o2_validated_suggestions.xlsx"
IN_STAGE7O2_REJECTED = BASE_DIR / "output" / "stage7o2_failed_case_retry" / "202_stage7o2_rejected_suggestions.xlsx"

IN_STAGE7G_MANUAL = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_remaining_manual_review.xlsx"
IN_SCHEMA = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_review_response_schema.json"
IN_RULES = BASE_DIR / "output" / "stage7h_ai_assisted_review_design" / "187_stage7h_ai_validation_rules.json"

OUT_DIR = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration"
OUT_SUMMARY = OUT_DIR / "203_stage7p_ai_suggestion_queue_summary.json"
OUT_REPORT = OUT_DIR / "203_stage7p_ai_suggestion_queue_report.md"
OUT_QUEUE = OUT_DIR / "203_stage7p_ai_suggestion_queue.xlsx"
OUT_TEMPLATE = OUT_DIR / "203_stage7p_human_approval_template.xlsx"
OUT_SUPERSEDED = OUT_DIR / "203_stage7p_superseded_rejected_suggestions.xlsx"
OUT_AUDIT = OUT_DIR / "203_stage7p_integration_audit.xlsx"

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


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


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


def _read_excel_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_excel(path)


def _build_source_request_map(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {_norm(r.get("review_id")): r for r in rows}


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_STAGE7O_SUMMARY,
        IN_STAGE7O_SELECTED,
        IN_STAGE7O_AUDIT,
        IN_STAGE7O_VALIDATED,
        IN_STAGE7O_REJECTED,
        IN_STAGE7O2_SUMMARY,
        IN_STAGE7O2_SELECTED,
        IN_STAGE7O2_AUDIT,
        IN_STAGE7O2_VALIDATED,
        IN_STAGE7O2_REJECTED,
        IN_STAGE7G_MANUAL,
        IN_SCHEMA,
        IN_RULES,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7p_ai_suggestion_queue_integration",
                "mode": "integration_only_no_api_call_no_apply",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        return 0

    before = _snapshot_hashes()

    stage7o_summary = _load_json(IN_STAGE7O_SUMMARY)
    stage7o2_summary = _load_json(IN_STAGE7O2_SUMMARY)
    stage7o_selected = _load_jsonl(IN_STAGE7O_SELECTED)
    stage7o2_selected = _load_jsonl(IN_STAGE7O2_SELECTED)
    stage7o_validated = _read_excel_safe(IN_STAGE7O_VALIDATED)
    stage7o2_validated = _read_excel_safe(IN_STAGE7O2_VALIDATED)
    stage7o_rejected = _read_excel_safe(IN_STAGE7O_REJECTED)
    stage7o2_rejected = _read_excel_safe(IN_STAGE7O2_REJECTED)
    stage7o_audit = _read_excel_safe(IN_STAGE7O_AUDIT)
    stage7o2_audit = _read_excel_safe(IN_STAGE7O2_AUDIT)

    # Read for scope completeness; no mutation or apply in this stage.
    _ = _read_excel_safe(IN_STAGE7G_MANUAL)
    _ = _load_json(IN_SCHEMA)
    _ = _load_json(IN_RULES)

    source_req_map = _build_source_request_map(stage7o_selected + stage7o2_selected)
    stage7o_model = _norm(stage7o_summary.get("model"))
    stage7o2_model = _norm(stage7o2_summary.get("model"))
    stage7o_commit = "c540c4c11081f66cdedd355ce578781a711c009a"
    stage7o2_commit = "cf748443dc8b42246f6b8bbdd331d6561c749976"

    stage7o_valid_map: Dict[str, Dict[str, Any]] = {}
    for _, rec in stage7o_validated.iterrows():
        rid = _norm(rec.get("review_id"))
        if rid:
            stage7o_valid_map[rid] = rec.to_dict()

    stage7o2_valid_map: Dict[str, Dict[str, Any]] = {}
    for _, rec in stage7o2_validated.iterrows():
        rid = _norm(rec.get("review_id"))
        if rid:
            stage7o2_valid_map[rid] = rec.to_dict()

    stage7o_rej_map: Dict[str, Dict[str, Any]] = {}
    if "review_id" in stage7o_rejected.columns:
        for _, rec in stage7o_rejected.iterrows():
            rid = _norm(rec.get("review_id"))
            if rid:
                stage7o_rej_map[rid] = rec.to_dict()

    overlap_rej_valid = sorted(set(stage7o_rej_map.keys()) & set(stage7o2_valid_map.keys()))
    superseded_rows: List[Dict[str, Any]] = []
    for rid in overlap_rej_valid:
        row = dict(stage7o_rej_map[rid])
        row["superseded_by_stage"] = "stage7o2_failed_case_retry"
        row["superseded_by_commit"] = stage7o2_commit
        row["superseded_reason"] = "stage7o_rejected_but_stage7o2_validated"
        superseded_rows.append(row)

    # Merge validated suggestions: keep stage7o validated, override with stage7o2 validated for same review_id.
    merged: Dict[str, Dict[str, Any]] = {}
    for rid, rec in stage7o_valid_map.items():
        merged[rid] = {
            "source_stage": "stage7o_five_case_new_model_batch_test",
            "source_commit": stage7o_commit,
            "model": stage7o_model,
            "record": rec,
        }
    for rid, rec in stage7o2_valid_map.items():
        merged[rid] = {
            "source_stage": "stage7o2_failed_case_retry",
            "source_commit": stage7o2_commit,
            "model": stage7o2_model,
            "record": rec,
        }

    # duplicate_review_id_count reflects duplicates in final queue (should be 0 after merge).
    duplicate_review_id_count = 0

    # Build audit counters from source audits for integrated review_ids.
    audit_rows = pd.concat([stage7o_audit, stage7o2_audit], ignore_index=True, sort=False) if not stage7o2_audit.empty else stage7o_audit
    review_to_last_audit: Dict[str, Dict[str, Any]] = {}
    if "review_id" in audit_rows.columns:
        for _, rec in audit_rows.iterrows():
            rid = _norm(rec.get("review_id"))
            if rid:
                review_to_last_audit[rid] = rec.to_dict()

    queue_rows: List[Dict[str, Any]] = []
    integration_audit_rows: List[Dict[str, Any]] = []
    for idx, rid in enumerate(sorted(merged.keys()), start=1):
        info = merged[rid]
        rec = info["record"]
        req_meta = source_req_map.get(rid, {})
        audit_meta = review_to_last_audit.get(rid, {})
        suggested_row_ids = _norm(rec.get("suggested_row_ids"))
        risk_flags = _norm(rec.get("risk_flags"))
        requires_human = True  # force true by policy

        q = {
            "queue_id": f"stage7p_queue_{idx:03d}",
            "review_id": rid,
            "source_stage": info["source_stage"],
            "source_commit": info["source_commit"],
            "original_request_id": _norm(req_meta.get("conflict_group_id")) or rid,
            "model": _norm(info["model"]),
            "suggested_action": _norm(rec.get("suggested_action")),
            "suggested_row_ids": suggested_row_ids,
            "suggested_metric_name": _norm(rec.get("suggested_metric_name")),
            "suggested_year": _norm(rec.get("suggested_year")),
            "suggested_value": _norm(rec.get("suggested_value")),
            "suggested_unit": _norm(rec.get("suggested_unit")),
            "confidence": rec.get("confidence", ""),
            "reasoning_summary": _norm(rec.get("reasoning_summary")),
            "risk_flags": risk_flags,
            "requires_human_approval": requires_human,
            "validation_status": "validated",
            "hallucinated_value": int(audit_meta.get("hallucinated_value_count", 0) or 0),
            "invalid_source_row_reference": int(audit_meta.get("invalid_source_row_reference_count", 0) or 0),
            "bad_eps_ratio": int(audit_meta.get("bad_eps_ratio_count", 0) or 0),
            "approval_status": "pending_human_review",
            "human_decision": "",
            "human_comment": "",
            "approved_by": "",
            "approved_at": "",
            "apply_allowed": False,
            "apply_target": "none",
            "audit_note": "stage7p_integrated_queue;manual_review_required",
        }
        queue_rows.append(q)

        integration_audit_rows.append(
            {
                "review_id": rid,
                "source_stage": info["source_stage"],
                "source_commit": info["source_commit"],
                "validation_status": q["validation_status"],
                "requires_human_approval": q["requires_human_approval"],
                "approval_status": q["approval_status"],
                "apply_allowed": q["apply_allowed"],
                "hallucinated_value": q["hallucinated_value"],
                "invalid_source_row_reference": q["invalid_source_row_reference"],
                "bad_eps_ratio": q["bad_eps_ratio"],
                "is_superseded_rejected_case": rid in overlap_rej_valid,
            }
        )

    queue_df = pd.DataFrame(queue_rows)
    template_cols = [
        "queue_id",
        "review_id",
        "source_stage",
        "model",
        "suggested_action",
        "suggested_row_ids",
        "suggested_metric_name",
        "suggested_year",
        "suggested_value",
        "suggested_unit",
        "confidence",
        "reasoning_summary",
        "risk_flags",
        "requires_human_approval",
        "approval_status",
        "human_decision",
        "human_comment",
        "approved_by",
        "approved_at",
        "apply_allowed",
        "apply_target",
    ]
    template_df = queue_df[template_cols].copy()
    template_df["approval_status"] = "pending_human_review"
    template_df["approval_status_allowed_values"] = "approve|reject|needs_more_info"

    superseded_df = pd.DataFrame(superseded_rows)
    integration_audit_df = pd.DataFrame(integration_audit_rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    queue_df.to_excel(OUT_QUEUE, sheet_name="ai_suggestion_queue", index=False, engine="openpyxl")
    template_df.to_excel(OUT_TEMPLATE, sheet_name="human_approval_template", index=False, engine="openpyxl")
    superseded_df.to_excel(OUT_SUPERSEDED, sheet_name="superseded_rejected", index=False, engine="openpyxl")
    integration_audit_df.to_excel(OUT_AUDIT, sheet_name="integration_audit", index=False, engine="openpyxl")

    integrated_count = len(queue_rows)
    pending_human_review_count = int(sum(1 for r in queue_rows if _norm(r.get("approval_status")) == "pending_human_review"))
    requires_human_approval_count = int(sum(1 for r in queue_rows if _as_bool(r.get("requires_human_approval"))))
    apply_allowed_count = int(sum(1 for r in queue_rows if _as_bool(r.get("apply_allowed"))))
    hallucinated_value_count = int(sum(int(r.get("hallucinated_value", 0) or 0) for r in queue_rows))
    invalid_source_row_reference_count = int(sum(int(r.get("invalid_source_row_reference", 0) or 0) for r in queue_rows))
    bad_eps_ratio_count = int(sum(int(r.get("bad_eps_ratio", 0) or 0) for r in queue_rows))

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    ready_for_stage7q = bool(
        integrated_count == 5
        and requires_human_approval_count == integrated_count
        and apply_allowed_count == 0
        and hallucinated_value_count == 0
        and invalid_source_row_reference_count == 0
        and bad_eps_ratio_count == 0
        and check_status == "PASS"
    )

    summary = {
        "stage": "stage7p_ai_suggestion_queue_integration",
        "mode": "integration_only_no_api_call_no_apply",
        "based_on_stage7o2_commit": "cf748443dc8b42246f6b8bbdd331d6561c749976",
        "external_api_called": False,
        "stage7o_validated_suggestion_count": int(stage7o_summary.get("validated_suggestion_count", 0)),
        "stage7o2_validated_suggestion_count": int(stage7o2_summary.get("validated_suggestion_count", 0)),
        "integrated_ai_suggestion_count": integrated_count,
        "duplicate_review_id_count": duplicate_review_id_count,
        "superseded_rejected_count": len(superseded_rows),
        "pending_human_review_count": pending_human_review_count,
        "requires_human_approval_count": requires_human_approval_count,
        "apply_allowed_count": apply_allowed_count,
        "hallucinated_value_count": hallucinated_value_count,
        "invalid_source_row_reference_count": invalid_source_row_reference_count,
        "bad_eps_ratio_count": bad_eps_ratio_count,
        "human_approval_template_generated": True,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7q_human_approval_flow_design": ready_for_stage7q,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7P AI Suggestion Queue Integration",
        "",
        "## Scope",
        "- integration_only_no_api_call_no_apply",
        "- source: stage7o validated + stage7o2 validated",
        "- no production write-back; approval queue only",
        "",
        "## Counts",
        f"- stage7o_validated_suggestion_count: {summary['stage7o_validated_suggestion_count']}",
        f"- stage7o2_validated_suggestion_count: {summary['stage7o2_validated_suggestion_count']}",
        f"- integrated_ai_suggestion_count: {summary['integrated_ai_suggestion_count']}",
        f"- duplicate_review_id_count: {summary['duplicate_review_id_count']}",
        f"- superseded_rejected_count: {summary['superseded_rejected_count']}",
        f"- pending_human_review_count: {summary['pending_human_review_count']}",
        "",
        "## Safety Guards",
        f"- requires_human_approval_count: {summary['requires_human_approval_count']}",
        f"- apply_allowed_count: {summary['apply_allowed_count']}",
        f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
        f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        f"- human_approval_template_generated: {summary['human_approval_template_generated']}",
        "",
        "## Change Boundary",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Decision",
        f"- ready_for_stage7q_human_approval_flow_design: {summary['ready_for_stage7q_human_approval_flow_design']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
