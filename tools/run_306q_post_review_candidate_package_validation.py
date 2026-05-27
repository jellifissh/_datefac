from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation"

IN_306P_SUMMARY = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_summary.json"
IN_APPROVED = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_approved_reviewed_candidates.xlsx"
IN_CORRECTED = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_corrected_reviewed_candidates.xlsx"
IN_REJECTED = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_rejected_candidates.xlsx"
IN_NEEDS = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_needs_more_info_candidates.xlsx"
IN_MISSING = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_missing_candidate_intake.xlsx"
IN_AUDIT = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_post_review_decision_audit.xlsx"
IN_306M_G2C = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_to_candidate_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "306q_summary.json"
OUT_REPORT = OUT_DIR / "306q_report.md"
OUT_POOL = OUT_DIR / "306q_reviewed_candidate_pool.xlsx"
OUT_CORRECTED_AUDIT = OUT_DIR / "306q_corrected_value_audit.xlsx"
OUT_EXCLUDED_AUDIT = OUT_DIR / "306q_excluded_rejected_needs_more_info_audit.xlsx"
OUT_MISSING_AUDIT = OUT_DIR / "306q_missing_candidate_intake_audit.xlsx"
OUT_DUP = OUT_DIR / "306q_duplicate_key_audit.xlsx"
OUT_CONFLICT = OUT_DIR / "306q_value_conflict_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "306q_no_apply_proof.json"

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


def _to_int(v: Any) -> int:
    s = _norm(v)
    if s == "":
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


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


def _drop_note_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "note" in df.columns:
        return df[~df["note"].map(_norm).str.startswith("no_")].copy()
    return df.copy()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_306P_SUMMARY,
        IN_APPROVED,
        IN_CORRECTED,
        IN_REJECTED,
        IN_NEEDS,
        IN_MISSING,
        IN_AUDIT,
        IN_306M_G2C,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306Q",
                "mode": "post_review_candidate_package_validation",
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

    s_306p = json.loads(IN_306P_SUMMARY.read_text(encoding="utf-8"))
    approved = _drop_note_rows(pd.read_excel(IN_APPROVED).fillna(""))
    corrected = _drop_note_rows(pd.read_excel(IN_CORRECTED).fillna(""))
    rejected = _drop_note_rows(pd.read_excel(IN_REJECTED).fillna(""))
    needs_more = _drop_note_rows(pd.read_excel(IN_NEEDS).fillna(""))
    missing_intake = _drop_note_rows(pd.read_excel(IN_MISSING).fillna(""))
    audit_306p = pd.read_excel(IN_AUDIT, sheet_name=None)
    g2c = pd.read_excel(IN_306M_G2C).fillna("")

    reviewed_pool = pd.concat([approved, corrected], ignore_index=True).fillna("")

    # Core counts
    approved_count = int(len(approved))
    corrected_count = int(len(corrected))
    rejected_count = int(len(rejected))
    needs_more_count = int(len(needs_more))
    missing_count = int(len(missing_intake))
    reviewed_pool_count = int(len(reviewed_pool))

    # Candidate id presence checks (existing pools)
    def _missing_cid_count(df: pd.DataFrame) -> int:
        if "candidate_id" not in df.columns:
            return int(len(df))
        return int(df["candidate_id"].map(_norm).eq("").sum())

    missing_cid_approved = _missing_cid_count(approved)
    missing_cid_corrected = _missing_cid_count(corrected)
    missing_cid_rejected = _missing_cid_count(rejected)
    missing_cid_needs = _missing_cid_count(needs_more)

    # Missing intake fake candidate ids.
    manifest_ids = set(g2c["candidate_id"].map(_norm).tolist())
    fake_candidate_id_generated_count = 0
    if "candidate_id" in missing_intake.columns:
        fake_candidate_id_generated_count = int(
            sum(
                1
                for cid in missing_intake["candidate_id"].map(_norm).tolist()
                if cid != "" and cid not in manifest_ids
            )
        )

    # Corrected field preservation
    required_corrected_fields = [
        "original_value",
        "corrected_value",
        "corrected_unit",
        "reviewer_id",
        "reviewed_at",
        "review_comment",
    ]
    corrected_missing_required_fields = [c for c in required_corrected_fields if c not in corrected.columns]
    corrected_required_field_empty_count = 0
    if not corrected.empty:
        for c in required_corrected_fields:
            if c in corrected.columns:
                corrected_required_field_empty_count += int(corrected[c].map(_norm).eq("").sum())

    # Reviewed pool duplicate key and conflict check.
    key_cols = ["PDF文件名", "标准指标", "年份"]
    reviewed_pool_key_ready = all(c in reviewed_pool.columns for c in key_cols)
    if reviewed_pool_key_ready and not reviewed_pool.empty:
        key_df = reviewed_pool.copy()
        key_df["key_pdf"] = key_df["PDF文件名"].map(_norm)
        key_df["key_metric"] = key_df["标准指标"].map(_norm)
        key_df["key_year"] = key_df["年份"].map(_to_int)
        key_df["key"] = key_df["key_pdf"] + "|" + key_df["key_metric"] + "|" + key_df["key_year"].astype(str)

        dup_keys = key_df.groupby("key", dropna=False).size().reset_index(name="count")
        dup_keys = dup_keys[dup_keys["count"] > 1].copy()

        dup_detail = key_df[key_df["key"].isin(set(dup_keys["key"]))].copy() if not dup_keys.empty else pd.DataFrame()

        # conflict check on corrected/effective value
        if "corrected_value" in key_df.columns and "original_value" in key_df.columns:
            key_df["effective_value"] = key_df["corrected_value"].map(_norm)
            key_df.loc[key_df["effective_value"].eq(""), "effective_value"] = key_df["original_value"].map(_norm)
        elif "corrected_value" in key_df.columns:
            key_df["effective_value"] = key_df["corrected_value"].map(_norm)
        elif "原数值" in key_df.columns:
            key_df["effective_value"] = key_df["原数值"].map(_norm)
        else:
            key_df["effective_value"] = ""

        conflict_rows: List[Dict[str, Any]] = []
        for k, g in key_df.groupby("key", dropna=False):
            vals = sorted({v for v in g["effective_value"].map(_norm).tolist() if v != ""})
            if len(vals) > 1:
                one = g.iloc[0]
                conflict_rows.append(
                    {
                        "key": k,
                        "PDF文件名": _norm(one.get("PDF文件名", "")),
                        "标准指标": _norm(one.get("标准指标", "")),
                        "年份": _to_int(one.get("年份", 0)),
                        "distinct_values": " | ".join(vals),
                        "row_count": int(len(g)),
                    }
                )
        conflict_df = pd.DataFrame(conflict_rows)
    else:
        dup_keys = pd.DataFrame()
        dup_detail = pd.DataFrame()
        conflict_df = pd.DataFrame()

    duplicate_key_count = int(len(dup_keys))
    value_conflict_count = int(len(conflict_df))

    # Exclusion rules
    reviewed_ids = set(reviewed_pool["candidate_id"].map(_norm).tolist()) if "candidate_id" in reviewed_pool.columns else set()
    rejected_ids = set(rejected["candidate_id"].map(_norm).tolist()) if "candidate_id" in rejected.columns else set()
    needs_ids = set(needs_more["candidate_id"].map(_norm).tolist()) if "candidate_id" in needs_more.columns else set()
    rejected_in_reviewed = sorted([x for x in rejected_ids if x != "" and x in reviewed_ids])
    needs_in_reviewed = sorted([x for x in needs_ids if x != "" and x in reviewed_ids])

    # Missing intake must remain separate and not in reviewed existing pool.
    missing_ids = set(missing_intake["candidate_id"].map(_norm).tolist()) if "candidate_id" in missing_intake.columns else set()
    missing_ids_nonempty = {x for x in missing_ids if x != ""}
    missing_in_reviewed = sorted([x for x in missing_ids_nonempty if x in reviewed_ids])

    # Forbidden fields
    all_cols = set(reviewed_pool.columns).union(set(rejected.columns)).union(set(needs_more.columns)).union(set(missing_intake.columns))
    forbidden_fields_generated = sorted([c for c in all_cols if c in FORBIDDEN_FIELDS])

    # Save outputs
    _write_excel(
        OUT_POOL,
        {
            "reviewed_candidate_pool": reviewed_pool if not reviewed_pool.empty else pd.DataFrame([{"note": "no_reviewed_pool_rows"}]),
            "pool_distribution": pd.DataFrame(
                [
                    {"pool": "approved", "count": approved_count},
                    {"pool": "corrected", "count": corrected_count},
                    {"pool": "reviewed_pool", "count": reviewed_pool_count},
                ]
            ),
        },
    )
    _write_excel(
        OUT_CORRECTED_AUDIT,
        {
            "corrected_candidates": corrected if not corrected.empty else pd.DataFrame([{"note": "no_corrected_candidates"}]),
            "corrected_field_check": pd.DataFrame(
                [
                    {
                        "required_field": c,
                        "exists": c in corrected.columns,
                        "empty_value_count": int(corrected[c].map(_norm).eq("").sum()) if c in corrected.columns and not corrected.empty else 0,
                    }
                    for c in required_corrected_fields
                ]
            ),
        },
    )
    _write_excel(
        OUT_EXCLUDED_AUDIT,
        {
            "excluded_rejected": rejected if not rejected.empty else pd.DataFrame([{"note": "no_rejected_candidates"}]),
            "excluded_needs_more_info": needs_more if not needs_more.empty else pd.DataFrame([{"note": "no_needs_more_info_candidates"}]),
            "excluded_overlap_check": pd.DataFrame(
                [
                    {"check": "rejected_in_reviewed_count", "count": int(len(rejected_in_reviewed))},
                    {"check": "needs_more_info_in_reviewed_count", "count": int(len(needs_in_reviewed))},
                ]
            ),
        },
    )
    _write_excel(
        OUT_MISSING_AUDIT,
        {
            "missing_candidate_intake": missing_intake if not missing_intake.empty else pd.DataFrame([{"note": "no_missing_candidate_intake"}]),
            "missing_intake_checks": pd.DataFrame(
                [
                    {"check": "missing_candidate_intake_count", "value": missing_count},
                    {"check": "fake_candidate_id_generated_count", "value": fake_candidate_id_generated_count},
                    {"check": "missing_candidate_id_in_reviewed_count", "value": int(len(missing_in_reviewed))},
                ]
            ),
        },
    )
    _write_excel(
        OUT_DUP,
        {
            "duplicate_key_summary": dup_keys if not dup_keys.empty else pd.DataFrame([{"note": "duplicate_key_count_0"}]),
            "duplicate_key_detail": dup_detail if not dup_detail.empty else pd.DataFrame([{"note": "no_duplicate_key_rows"}]),
        },
    )
    _write_excel(
        OUT_CONFLICT,
        {"value_conflict_audit": conflict_df if not conflict_df.empty else pd.DataFrame([{"note": "value_conflict_count_0"}])},
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

    reviewed_pool_expected = approved_count + corrected_count
    rejected_needs_excluded = (len(rejected_in_reviewed) == 0 and len(needs_in_reviewed) == 0)
    no_forbidden_fields = len(forbidden_fields_generated) == 0

    summary = {
        "stage": "EVAL-306Q",
        "mode": "post_review_candidate_package_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "approved_count": approved_count,
        "corrected_count": corrected_count,
        "rejected_count": rejected_count,
        "needs_more_info_count": needs_more_count,
        "missing_candidate_intake_count": missing_count,
        "reviewed_candidate_pool_count": reviewed_pool_count,
        "reviewed_candidate_pool_count_expected": reviewed_pool_expected,
        "reviewed_candidate_pool_count_match": bool(reviewed_pool_count == reviewed_pool_expected),
        "rejected_needs_more_info_excluded_from_reviewed_pool": bool(rejected_needs_excluded),
        "missing_candidate_intake_is_separate": bool(len(missing_in_reviewed) == 0),
        "missing_candidate_id_required_fail_count_approved": missing_cid_approved,
        "missing_candidate_id_required_fail_count_corrected": missing_cid_corrected,
        "missing_candidate_id_required_fail_count_rejected": missing_cid_rejected,
        "missing_candidate_id_required_fail_count_needs_more_info": missing_cid_needs,
        "corrected_missing_required_fields_count": int(len(corrected_missing_required_fields)),
        "corrected_required_field_empty_count": int(corrected_required_field_empty_count),
        "duplicate_key_count": duplicate_key_count,
        "value_conflict_count": value_conflict_count,
        "fake_candidate_id_generated_count": int(fake_candidate_id_generated_count),
        "forbidden_fields_generated": forbidden_fields_generated,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(no_forbidden_fields),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "source_306p_stage": _norm(s_306p.get("stage")),
        "source_306p_audit_sheets": sorted(audit_306p.keys()),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306Q Post-Review Candidate Package Validation",
        "",
        "## Scope",
        "- Validated 306P post-review pools before any projection/apply stage.",
        "- Built reviewed candidate pool from approved + corrected only.",
        "- Excluded rejected / needs_more_info / missing intake from reviewed pool.",
        "",
        "## Counts",
        f"- approved_count: {approved_count}",
        f"- corrected_count: {corrected_count}",
        f"- reviewed_candidate_pool_count: {reviewed_pool_count}",
        f"- rejected_count: {rejected_count}",
        f"- needs_more_info_count: {needs_more_count}",
        f"- missing_candidate_intake_count: {missing_count}",
        "",
        "## Assertions",
        f"- reviewed_candidate_pool_count_match: {summary['reviewed_candidate_pool_count_match']}",
        f"- rejected_needs_more_info_excluded_from_reviewed_pool: {summary['rejected_needs_more_info_excluded_from_reviewed_pool']}",
        f"- missing_candidate_intake_is_separate: {summary['missing_candidate_intake_is_separate']}",
        f"- duplicate_key_count: {summary['duplicate_key_count']}",
        f"- value_conflict_count: {summary['value_conflict_count']}",
        f"- fake_candidate_id_generated_count: {summary['fake_candidate_id_generated_count']}",
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

    print(f"eval_306q_summary_json: {OUT_SUMMARY}")
    print(f"eval_306q_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

