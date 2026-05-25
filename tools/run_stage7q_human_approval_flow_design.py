import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")

IN_STAGE7P_SUMMARY = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_ai_suggestion_queue_summary.json"
IN_STAGE7P_QUEUE = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_ai_suggestion_queue.xlsx"
IN_STAGE7P_TEMPLATE = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_human_approval_template.xlsx"
IN_STAGE7P_AUDIT = BASE_DIR / "output" / "stage7p_ai_suggestion_queue_integration" / "203_stage7p_integration_audit.xlsx"
IN_STAGE7G_REMAINING = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_remaining_manual_review.xlsx"
IN_STAGE7G_PREVIEW = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox" / "186_stage7g_reduced_clean_06_preview.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7q_human_approval_flow_design"
OUT_SUMMARY = OUT_DIR / "204_stage7q_human_approval_flow_summary.json"
OUT_REPORT = OUT_DIR / "204_stage7q_human_approval_flow_report.md"
OUT_STATE_MACHINE = OUT_DIR / "204_stage7q_approval_state_machine.md"
OUT_SCHEMA = OUT_DIR / "204_stage7q_approval_result_schema.json"
OUT_MOCK = OUT_DIR / "204_stage7q_mock_human_approval_result.xlsx"
OUT_APPROVED = OUT_DIR / "204_stage7q_approved_suggestions.xlsx"
OUT_REJECTED = OUT_DIR / "204_stage7q_rejected_by_human.xlsx"
OUT_NEEDS_INFO = OUT_DIR / "204_stage7q_needs_more_info_queue.xlsx"
OUT_APPLY_PREVIEW = OUT_DIR / "204_stage7q_apply_preview_sandbox.xlsx"
OUT_VALIDATION_AUDIT = OUT_DIR / "204_stage7q_approval_validation_audit.xlsx"

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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_STAGE7P_SUMMARY,
        IN_STAGE7P_QUEUE,
        IN_STAGE7P_TEMPLATE,
        IN_STAGE7P_AUDIT,
        IN_STAGE7G_REMAINING,
        IN_STAGE7G_PREVIEW,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "stage7q_human_approval_flow_design",
                "mode": "approval_flow_design_no_api_call_no_apply",
                "external_api_called": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        return 0

    before = _snapshot_hashes()

    stage7p_summary = _load_json(IN_STAGE7P_SUMMARY)
    queue_df = pd.read_excel(IN_STAGE7P_QUEUE)
    _ = pd.read_excel(IN_STAGE7P_TEMPLATE)
    _ = pd.read_excel(IN_STAGE7P_AUDIT)
    _ = pd.read_excel(IN_STAGE7G_REMAINING)
    _ = pd.read_excel(IN_STAGE7G_PREVIEW)

    queue_df = queue_df.sort_values("queue_id").reset_index(drop=True)
    input_ai_suggestion_count = len(queue_df)

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Required mock distribution: 2 approve / 2 reject / 1 needs_more_info
    mock_statuses = ["approve", "approve", "reject", "reject", "needs_more_info"]
    if input_ai_suggestion_count != 5:
        # Keep robust fallback while preserving legality.
        base = ["approve", "approve", "reject", "reject", "needs_more_info"]
        mock_statuses = (base + ["needs_more_info"] * input_ai_suggestion_count)[:input_ai_suggestion_count]

    mock_rows: List[Dict[str, Any]] = []
    for idx, (_, row) in enumerate(queue_df.iterrows()):
        status = mock_statuses[idx] if idx < len(mock_statuses) else "needs_more_info"
        mock_rows.append(
            {
                "queue_id": _norm(row.get("queue_id")),
                "review_id": _norm(row.get("review_id")),
                "approval_status": status,
                "human_decision": f"mock_{status}",
                "human_comment": "mock approval only, no real apply",
                "approved_by": "mock_reviewer",
                "approved_at": now_iso,
            }
        )
    mock_df = pd.DataFrame(mock_rows)
    mock_df.to_excel(OUT_MOCK, sheet_name="mock_human_approval", index=False, engine="openpyxl")

    allowed_status = {"approve", "reject", "needs_more_info"}
    validation_rows: List[Dict[str, Any]] = []
    merged = queue_df.merge(mock_df, on=["queue_id", "review_id"], how="left", suffixes=("", "_human"))
    approval_validation_pass = True

    approved_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    needs_info_rows: List[Dict[str, Any]] = []
    pending_rows: List[Dict[str, Any]] = []
    apply_preview_rows: List[Dict[str, Any]] = []

    for _, row in merged.iterrows():
        status_raw = _norm(row.get("approval_status_human"))
        status = status_raw if status_raw in allowed_status else "pending_human_review"
        invalid_status = status_raw != "" and status_raw not in allowed_status

        base = row.to_dict()
        base["approval_status"] = status
        base["human_decision"] = _norm(row.get("human_decision"))
        base["human_comment"] = _norm(row.get("human_comment"))
        base["approved_by"] = _norm(row.get("approved_by"))
        base["approved_at"] = _norm(row.get("approved_at"))
        base["requires_human_approval"] = True

        # apply_allowed is system-generated, never directly from mock template
        apply_allowed = status == "approve"
        base["apply_allowed"] = apply_allowed
        base["apply_target"] = "sandbox_apply_preview_only" if apply_allowed else "none"
        base["real_apply_executed"] = False
        base["audit_note"] = _norm(base.get("audit_note")) + ";stage7q_mock_approval_only"

        hallu = int(base.get("hallucinated_value", 0) or 0)
        bad_ref = int(base.get("invalid_source_row_reference", 0) or 0)
        bad_eps = int(base.get("bad_eps_ratio", 0) or 0)
        if hallu > 0 or bad_ref > 0 or bad_eps > 0:
            approval_validation_pass = False

        if invalid_status:
            approval_validation_pass = False

        if status == "approve":
            approved_rows.append(base)
            apply_preview_rows.append(
                {
                    "queue_id": _norm(base.get("queue_id")),
                    "review_id": _norm(base.get("review_id")),
                    "source_stage": _norm(base.get("source_stage")),
                    "model": _norm(base.get("model")),
                    "suggested_action": _norm(base.get("suggested_action")),
                    "suggested_row_ids": _norm(base.get("suggested_row_ids")),
                    "suggested_metric_name": _norm(base.get("suggested_metric_name")),
                    "suggested_year": _norm(base.get("suggested_year")),
                    "suggested_value": _norm(base.get("suggested_value")),
                    "suggested_unit": _norm(base.get("suggested_unit")),
                    "confidence": base.get("confidence", ""),
                    "human_decision": _norm(base.get("human_decision")),
                    "human_comment": _norm(base.get("human_comment")),
                    "approved_by": _norm(base.get("approved_by")),
                    "approved_at": _norm(base.get("approved_at")),
                    "apply_allowed": True,
                    "apply_target": "sandbox_apply_preview_only",
                    "real_apply_executed": False,
                    "apply_note": "approved_for_preview_only_no_production_write",
                }
            )
        elif status == "reject":
            rejected_rows.append(base)
        elif status == "needs_more_info":
            needs_info_rows.append(base)
        else:
            pending_rows.append(base)

        validation_rows.append(
            {
                "queue_id": _norm(base.get("queue_id")),
                "review_id": _norm(base.get("review_id")),
                "approval_status_input": status_raw,
                "approval_status_final": status,
                "invalid_status": invalid_status,
                "requires_human_approval": True,
                "apply_allowed": apply_allowed,
                "real_apply_executed": False,
                "hallucinated_value": hallu,
                "invalid_source_row_reference": bad_ref,
                "bad_eps_ratio": bad_eps,
                "row_validation_pass": (not invalid_status and hallu == 0 and bad_ref == 0 and bad_eps == 0),
            }
        )

    approved_df = pd.DataFrame(approved_rows)
    rejected_df = pd.DataFrame(rejected_rows)
    needs_info_df = pd.DataFrame(needs_info_rows)
    apply_preview_df = pd.DataFrame(apply_preview_rows)
    validation_df = pd.DataFrame(validation_rows)

    approved_cols = [
        "queue_id",
        "review_id",
        "human_decision",
        "human_comment",
        "approved_by",
        "approved_at",
        "source_stage",
        "model",
        "validation_status",
        "audit_note",
        "apply_allowed",
        "apply_target",
        "real_apply_executed",
    ]
    for col in approved_cols:
        if col not in approved_df.columns:
            approved_df[col] = ""
    approved_df = approved_df[approved_cols]

    approved_df.to_excel(OUT_APPROVED, sheet_name="approved_suggestions", index=False, engine="openpyxl")
    rejected_df.to_excel(OUT_REJECTED, sheet_name="rejected_by_human", index=False, engine="openpyxl")
    needs_info_df.to_excel(OUT_NEEDS_INFO, sheet_name="needs_more_info_queue", index=False, engine="openpyxl")
    apply_preview_df.to_excel(OUT_APPLY_PREVIEW, sheet_name="apply_preview_sandbox", index=False, engine="openpyxl")
    validation_df.to_excel(OUT_VALIDATION_AUDIT, sheet_name="approval_validation", index=False, engine="openpyxl")

    state_machine_md = """# Stage7Q Approval State Machine

## States
- `pending_human_review`
- `approve`
- `reject`
- `needs_more_info`

## Allowed Transition
- queue initialization -> `pending_human_review`
- `pending_human_review` -> `approve` / `reject` / `needs_more_info`
- invalid or empty human input -> remain `pending_human_review`

## Enforcement Rules
1. Only `approve` can enter sandbox apply preview.
2. `reject` goes to rejected_by_human queue.
3. `needs_more_info` goes to needs_more_info queue.
4. `apply_allowed` is system-generated from final status; human template cannot force it.
5. Even when `approve`, this stage cannot write production 06.
6. `real_apply_executed` must remain `false` in Stage7Q.
"""
    OUT_STATE_MACHINE.write_text(state_machine_md, encoding="utf-8")

    result_schema = {
        "schema_name": "stage7q_human_approval_result",
        "type": "object",
        "required": ["queue_id", "review_id", "approval_status", "human_decision", "human_comment", "approved_by", "approved_at"],
        "properties": {
            "queue_id": {"type": "string"},
            "review_id": {"type": "string"},
            "approval_status": {"type": "string", "enum": ["approve", "reject", "needs_more_info"]},
            "human_decision": {"type": "string"},
            "human_comment": {"type": "string"},
            "approved_by": {"type": "string"},
            "approved_at": {"type": "string", "description": "ISO-like datetime string"},
        },
        "forbidden_values": ["auto_apply", "real_apply", "write_production"],
        "empty_status_behavior": "pending_human_review",
    }
    _write_json(OUT_SCHEMA, result_schema)

    approved_count = len(approved_df)
    rejected_count = len(rejected_df)
    needs_info_count = len(needs_info_df)
    pending_count = len(pending_rows)
    apply_preview_row_count = len(apply_preview_df)
    hallucinated_total = int(queue_df["hallucinated_value"].fillna(0).sum()) if "hallucinated_value" in queue_df.columns else 0
    invalid_ref_total = int(queue_df["invalid_source_row_reference"].fillna(0).sum()) if "invalid_source_row_reference" in queue_df.columns else 0
    bad_eps_total = int(queue_df["bad_eps_ratio"].fillna(0).sum()) if "bad_eps_ratio" in queue_df.columns else 0

    # Must satisfy required mock split exactly for 5 rows.
    if input_ai_suggestion_count == 5:
        approval_validation_pass = approval_validation_pass and approved_count == 2 and rejected_count == 2 and needs_info_count == 1 and pending_count == 0

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    check_status = _norm(delivery.get("overall_status"))

    ready_for_stage7r = bool(
        input_ai_suggestion_count == 5
        and approval_validation_pass
        and approved_count == 2
        and rejected_count == 2
        and needs_info_count == 1
        and apply_preview_row_count == 2
        and check_status == "PASS"
    )

    summary = {
        "stage": "stage7q_human_approval_flow_design",
        "mode": "approval_flow_design_no_api_call_no_apply",
        "based_on_stage7p_commit": "0cdff5999f635541d7ac19c63154f08cd7b701fa",
        "external_api_called": False,
        "input_ai_suggestion_count": input_ai_suggestion_count,
        "mock_approval_result_generated": True,
        "approval_state_machine_generated": True,
        "approval_result_schema_generated": True,
        "approval_validation_pass": bool(approval_validation_pass),
        "approved_count": approved_count,
        "rejected_by_human_count": rejected_count,
        "needs_more_info_count": needs_info_count,
        "pending_human_review_count": pending_count,
        "apply_preview_row_count": apply_preview_row_count,
        "real_apply_executed": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": check_status,
        "ready_for_stage7r_human_approval_sandbox_apply_preview": ready_for_stage7r,
        "source_stage7p_integrated_count": int(stage7p_summary.get("integrated_ai_suggestion_count", 0)),
        "hallucinated_value_count": hallucinated_total,
        "invalid_source_row_reference_count": invalid_ref_total,
        "bad_eps_ratio_count": bad_eps_total,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage7Q Human Approval Flow Design and Validation",
        "",
        "mock approval only, no real apply.",
        "",
        "## Input",
        f"- input_ai_suggestion_count: {summary['input_ai_suggestion_count']}",
        f"- source_stage7p_integrated_count: {summary['source_stage7p_integrated_count']}",
        "",
        "## Mock Approval Result",
        f"- approved_count: {summary['approved_count']}",
        f"- rejected_by_human_count: {summary['rejected_by_human_count']}",
        f"- needs_more_info_count: {summary['needs_more_info_count']}",
        f"- pending_human_review_count: {summary['pending_human_review_count']}",
        "",
        "## Apply Preview",
        f"- apply_preview_row_count: {summary['apply_preview_row_count']}",
        f"- real_apply_executed: {summary['real_apply_executed']}",
        "",
        "## Validation",
        f"- approval_validation_pass: {summary['approval_validation_pass']}",
        f"- hallucinated_value_count: {summary['hallucinated_value_count']}",
        f"- invalid_source_row_reference_count: {summary['invalid_source_row_reference_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        "",
        "## Boundaries",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Decision",
        f"- ready_for_stage7r_human_approval_sandbox_apply_preview: {summary['ready_for_stage7r_human_approval_sandbox_apply_preview']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
