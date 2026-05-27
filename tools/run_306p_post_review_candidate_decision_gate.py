from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate"

IN_306O_SUMMARY = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_summary.json"
IN_306O_CANDIDATE = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_candidate_review_results.xlsx"
IN_306O_CORRECTED = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_corrected_candidate_results.xlsx"
IN_306O_REJECTED = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_rejected_candidate_results.xlsx"
IN_306O_NEEDS = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_needs_more_info_candidate_results.xlsx"
IN_306O_MISSING = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_human_discovered_missing_candidates.xlsx"
IN_306M_G2C = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_to_candidate_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "306p_summary.json"
OUT_REPORT = OUT_DIR / "306p_report.md"
OUT_APPROVED = OUT_DIR / "306p_approved_reviewed_candidates.xlsx"
OUT_CORRECTED = OUT_DIR / "306p_corrected_reviewed_candidates.xlsx"
OUT_REJECTED = OUT_DIR / "306p_rejected_candidates.xlsx"
OUT_NEEDS = OUT_DIR / "306p_needs_more_info_candidates.xlsx"
OUT_MISSING = OUT_DIR / "306p_missing_candidate_intake.xlsx"
OUT_AUDIT = OUT_DIR / "306p_post_review_decision_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "306p_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    s = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _run_delivery_check() -> Dict[str, Any]:
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
        IN_306O_SUMMARY,
        IN_306O_CANDIDATE,
        IN_306O_CORRECTED,
        IN_306O_REJECTED,
        IN_306O_NEEDS,
        IN_306O_MISSING,
        IN_306M_G2C,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306P",
                "mode": "post_review_candidate_decision_gate",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
            },
        )
        return 0

    before = _snapshot_guard()

    s_306o = json.loads(IN_306O_SUMMARY.read_text(encoding="utf-8"))
    cand = pd.read_excel(IN_306O_CANDIDATE).fillna("")
    corr_src = pd.read_excel(IN_306O_CORRECTED).fillna("")
    rej_src = pd.read_excel(IN_306O_REJECTED).fillna("")
    needs_src = pd.read_excel(IN_306O_NEEDS).fillna("")
    missing_src = pd.read_excel(IN_306O_MISSING).fillna("")
    g2c = pd.read_excel(IN_306M_G2C).fillna("")

    # Filter placeholder notes if any.
    if "candidate_id" in cand.columns:
        cand = cand[cand["candidate_id"].map(_norm) != ""].copy()
    if "decision_candidate" in cand.columns:
        cand["decision_candidate"] = cand["decision_candidate"].map(_norm)
    if "candidate_id" in missing_src.columns:
        missing_src["candidate_id"] = missing_src["candidate_id"].map(_norm)

    # Decision gating pools.
    approved = cand[cand["decision_candidate"].eq("approve")].copy()
    corrected = cand[cand["decision_candidate"].eq("correct_value")].copy()
    rejected = cand[cand["decision_candidate"].eq("reject")].copy()
    needs_more = cand[cand["decision_candidate"].eq("needs_more_info")].copy()
    missing_intake = missing_src.copy()

    # Ensure corrected pool preserves required fields.
    corrected = corrected.rename(columns={"原数值": "original_value"})
    for c in ["corrected_value", "corrected_unit", "reviewer_id", "reviewed_at", "review_comment", "original_value"]:
        if c not in corrected.columns:
            corrected[c] = ""

    # Required assertions.
    manifest_cid_set = set(g2c["candidate_id"].map(_norm).tolist())
    fake_candidate_id_generated_count = int(
        sum(
            1
            for x in cand["candidate_id"].map(_norm).tolist()
            if x != "" and x not in manifest_cid_set
        )
    )

    forbidden_field_generated = any(
        f in set(approved.columns).union(set(corrected.columns)).union(set(rejected.columns)).union(set(needs_more.columns)).union(set(missing_intake.columns))
        for f in FORBIDDEN_FIELDS
    )

    missing_candidates_only_in_missing_intake = bool(
        ("candidate_id" in missing_intake.columns)
        and missing_intake["candidate_id"].map(_norm).eq("").all()
    )
    missing_candidate_in_existing_pool_count = int(
        sum(df["candidate_id"].map(_norm).eq("").sum() for df in [approved, corrected, rejected, needs_more] if "candidate_id" in df.columns)
    )

    existing_expanded_count = int(len(cand))
    gated_existing_count = int(len(approved) + len(corrected) + len(rejected) + len(needs_more))
    gate_count_match = gated_existing_count == existing_expanded_count

    # Write outputs.
    _write_excel(OUT_APPROVED, {"approved_reviewed_candidates": approved if not approved.empty else pd.DataFrame([{"note": "no_approved_rows"}])})
    _write_excel(OUT_CORRECTED, {"corrected_reviewed_candidates": corrected if not corrected.empty else pd.DataFrame([{"note": "no_corrected_rows"}])})
    _write_excel(OUT_REJECTED, {"rejected_candidates": rejected if not rejected.empty else pd.DataFrame([{"note": "no_rejected_rows"}])})
    _write_excel(OUT_NEEDS, {"needs_more_info_candidates": needs_more if not needs_more.empty else pd.DataFrame([{"note": "no_needs_more_info_rows"}])})
    _write_excel(
        OUT_MISSING,
        {"missing_candidate_intake": missing_intake if not missing_intake.empty else pd.DataFrame([{"note": "no_missing_candidate_intake_rows"}])},
    )
    _write_excel(
        OUT_AUDIT,
        {
            "decision_distribution": pd.DataFrame(
                [
                    {"pool": "approved_reviewed_candidates", "row_count": int(len(approved))},
                    {"pool": "corrected_reviewed_candidates", "row_count": int(len(corrected))},
                    {"pool": "rejected_candidates", "row_count": int(len(rejected))},
                    {"pool": "needs_more_info_candidates", "row_count": int(len(needs_more))},
                    {"pool": "missing_candidate_intake", "row_count": int(len(missing_intake) if "note" not in missing_intake.columns else 0)},
                ]
            ),
            "gate_assertions": pd.DataFrame(
                [
                    {"assertion": "fake_candidate_id_generated_count", "value": fake_candidate_id_generated_count},
                    {"assertion": "forbidden_field_generated", "value": forbidden_field_generated},
                    {"assertion": "missing_candidates_only_in_missing_intake", "value": missing_candidates_only_in_missing_intake},
                    {"assertion": "missing_candidate_in_existing_pool_count", "value": missing_candidate_in_existing_pool_count},
                    {"assertion": "existing_expanded_count", "value": existing_expanded_count},
                    {"assertion": "gated_existing_count", "value": gated_existing_count},
                    {"assertion": "gate_count_match", "value": gate_count_match},
                ]
            ),
            "source_pool_cross_check": pd.DataFrame(
                [
                    {"source_file": "306o_corrected_candidate_results.xlsx", "row_count": int(len(corr_src) if "note" not in corr_src.columns else 0)},
                    {"source_file": "306o_rejected_candidate_results.xlsx", "row_count": int(len(rej_src) if "note" not in rej_src.columns else 0)},
                    {"source_file": "306o_needs_more_info_candidate_results.xlsx", "row_count": int(len(needs_src) if "note" not in needs_src.columns else 0)},
                    {"source_file": "306o_human_discovered_missing_candidates.xlsx", "row_count": int(len(missing_src) if "note" not in missing_src.columns else 0)},
                ]
            ),
        },
    )
    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
            "pdfplumber_rerun_executed": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-306P",
        "mode": "post_review_candidate_decision_gate",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "expanded_existing_candidate_review_count": existing_expanded_count,
        "approved_reviewed_candidate_count": int(len(approved)),
        "corrected_reviewed_candidate_count": int(len(corrected)),
        "rejected_candidate_count": int(len(rejected)),
        "needs_more_info_candidate_count": int(len(needs_more)),
        "missing_candidate_intake_count": int(len(missing_intake) if "note" not in missing_intake.columns else 0),
        "approved_corrected_rejected_needs_count_sum": gated_existing_count,
        "approved_corrected_rejected_needs_count_match_expanded_existing": gate_count_match,
        "fake_candidate_id_generated_count": fake_candidate_id_generated_count,
        "missing_candidates_only_in_missing_candidate_intake": missing_candidates_only_in_missing_intake,
        "missing_candidate_in_existing_pool_count": missing_candidate_in_existing_pool_count,
        "forbidden_field_generated": forbidden_field_generated,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": (not forbidden_field_generated),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "source_306o_stage": _norm(s_306o.get("stage")),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306P Post-Review Candidate Decision Gate",
        "",
        "## Scope",
        "- Gated 306O candidate-level reviewed rows into post-review pools only.",
        "- No apply fields generated; no production apply.",
        "- No Marker/pdfplumber rerun; no API/LLM/OCR.",
        "",
        "## Pool Counts",
        f"- expanded_existing_candidate_review_count: {summary['expanded_existing_candidate_review_count']}",
        f"- approved_reviewed_candidate_count: {summary['approved_reviewed_candidate_count']}",
        f"- corrected_reviewed_candidate_count: {summary['corrected_reviewed_candidate_count']}",
        f"- rejected_candidate_count: {summary['rejected_candidate_count']}",
        f"- needs_more_info_candidate_count: {summary['needs_more_info_candidate_count']}",
        f"- missing_candidate_intake_count: {summary['missing_candidate_intake_count']}",
        "",
        "## Assertions",
        f"- fake_candidate_id_generated_count: {summary['fake_candidate_id_generated_count']}",
        f"- missing_candidates_only_in_missing_candidate_intake: {summary['missing_candidates_only_in_missing_candidate_intake']}",
        f"- approved_corrected_rejected_needs_count_match_expanded_existing: {summary['approved_corrected_rejected_needs_count_match_expanded_existing']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        "",
        "## Delivery Guard",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306p_summary_json: {OUT_SUMMARY}")
    print(f"eval_306p_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

