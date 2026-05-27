from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_307e_eps_focused_review_input_validation"

IN_TEMPLATE = BASE_DIR / "output" / "eval_307d_eps_focused_human_review_package" / "307d_eps_grouped_review_template.xlsx"
IN_MANIFEST = BASE_DIR / "output" / "eval_307d_eps_focused_human_review_package" / "307d_eps_group_to_candidate_manifest.xlsx"
IN_REAL = BASE_DIR / "input" / "human_review" / "307e_eps_focused_review_input.xlsx"

OUT_SUMMARY = OUT_DIR / "307e_summary.json"
OUT_REPORT = OUT_DIR / "307e_report.md"
OUT_VALID = OUT_DIR / "307e_valid_eps_review_results.xlsx"
OUT_INVALID = OUT_DIR / "307e_invalid_eps_review_results.xlsx"
OUT_AUDIT = OUT_DIR / "307e_eps_review_validation_audit.xlsx"
OUT_NEG = OUT_DIR / "307e_negative_validation_tests.json"
OUT_NO_APPLY = OUT_DIR / "307e_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
DECISIONS = {"approve_eps_series", "reject_eps_series", "correct_eps_series", "needs_more_info"}
IMMUTABLE_FIELDS = [
    "PDF文件名",
    "group_id",
    "source_page",
    "source_parser",
    "blocker_reasons",
    "suspicious_value_flags",
    "suspicious_priority_score",
    "is_suspicious_group",
    "current_row_count",
    "2020",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
    "2026",
    "2027",
    "2028",
    "2029",
    "2030",
    "source_panel_id",
]
CORR_YEAR_COLS = [f"corrected_{y}" for y in range(2020, 2031)]


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


def _parse_dt(s: str) -> bool:
    t = _norm(s)
    if t == "":
        return False
    try:
        datetime.fromisoformat(t.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


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


def _load_first_sheet(path: Path, preferred: str | None = None) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    if preferred and preferred in xls.sheet_names:
        return pd.read_excel(path, sheet_name=preferred).fillna("")
    return pd.read_excel(path, sheet_name=xls.sheet_names[0]).fillna("")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_TEMPLATE, IN_MANIFEST]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307E",
                "mode": "eps_focused_review_input_validation",
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

    template = _load_first_sheet(IN_TEMPLATE, "eps_grouped_review_template").fillna("")
    manifest = _load_first_sheet(IN_MANIFEST, "eps_group_to_candidate_manifest").fillna("")
    real_input_present = IN_REAL.exists()

    input_df = _load_first_sheet(IN_REAL) if real_input_present else template.copy()
    input_df = input_df.fillna("")
    input_df["group_id"] = input_df["group_id"].map(_norm)
    template["group_id"] = template["group_id"].map(_norm)
    manifest["group_id"] = manifest["group_id"].map(_norm)

    manifest_groups = set(manifest["group_id"].map(_norm).tolist())
    template_by_group = { _norm(r["group_id"]): r for _, r in template.iterrows() if _norm(r["group_id"]) != "" }

    # forbidden fields
    forbidden_fields_generated = sorted([c for c in input_df.columns if c in FORBIDDEN_FIELDS])

    # duplicate group_id
    non_empty_gid = input_df[input_df["group_id"].map(_norm) != ""].copy()
    dup_gid_df = non_empty_gid.groupby("group_id", dropna=False).size().reset_index(name="count")
    dup_gids = set(dup_gid_df[dup_gid_df["count"] > 1]["group_id"].tolist())

    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []

    unknown_group_detected = False
    immutable_tamper_detected = False
    invalid_decision_detected = False
    missing_reviewer_detected = False
    missing_reviewed_at_detected = False
    correct_missing_correction_detected = False
    needs_more_info_missing_request_detected = False
    reject_missing_comment_detected = False

    for _, r in input_df.iterrows():
        rec = r.to_dict()
        gid = _norm(r.get("group_id", ""))
        decision = _norm(r.get("decision", ""))
        errs: List[str] = []
        warns: List[str] = []

        if gid == "" or gid not in manifest_groups:
            errs.append("group_id_unknown")
            unknown_group_detected = True
        if gid in dup_gids:
            errs.append("group_id_duplicated")

        # immutable checks against template
        if gid in template_by_group:
            tr = template_by_group[gid]
            for f in IMMUTABLE_FIELDS:
                if f in rec:
                    if _norm(rec.get(f, "")) != _norm(tr.get(f, "")):
                        errs.append(f"immutable_field_tamper:{f}")
                        immutable_tamper_detected = True
                        break

        if decision != "":
            if decision not in DECISIONS:
                errs.append("invalid_decision")
                invalid_decision_detected = True
            reviewer_id = _norm(r.get("reviewer_id", ""))
            reviewed_at = _norm(r.get("reviewed_at", ""))
            if reviewer_id == "":
                errs.append("missing_reviewer_id")
                missing_reviewer_detected = True
            if reviewed_at == "" or not _parse_dt(reviewed_at):
                errs.append("missing_or_unparseable_reviewed_at")
                missing_reviewed_at_detected = True

            if decision == "correct_eps_series":
                has_corr_year = any(_norm(r.get(c, "")) != "" for c in CORR_YEAR_COLS)
                has_corr_unit = _norm(r.get("corrected_unit", "")) != ""
                if not (has_corr_year or has_corr_unit):
                    errs.append("correct_eps_series_missing_correction")
                    correct_missing_correction_detected = True

            if decision == "needs_more_info":
                if _norm(r.get("extra_info_request", "")) == "":
                    errs.append("needs_more_info_missing_request")
                    needs_more_info_missing_request_detected = True

            if decision == "reject_eps_series":
                if _norm(r.get("review_comment", "")) == "":
                    warns.append("reject_eps_series_missing_review_comment")
                    reject_missing_comment_detected = True

        out = dict(rec)
        out["validation_errors"] = "|".join(errs)
        out["validation_warnings"] = "|".join(warns)
        out["validation_status"] = "VALID" if len(errs) == 0 else "INVALID"
        if len(errs) == 0:
            valid_rows.append(out)
        else:
            invalid_rows.append(out)

    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)

    # candidate mapping preserved
    input_groups = set(input_df["group_id"].map(_norm).tolist()) - {""}
    mapped_groups = set(manifest["group_id"].map(_norm).tolist())
    candidate_mapping_preserved = input_groups.issubset(mapped_groups)
    candidate_mapping_count = int(manifest["candidate_id"].map(_norm).nunique()) if "candidate_id" in manifest.columns else 0

    audit_rows.append({"check": "real_input_present", "result": real_input_present})
    audit_rows.append({"check": "group_id_unknown_detected", "result": unknown_group_detected})
    audit_rows.append({"check": "duplicate_group_id_detected", "result": len(dup_gids) > 0})
    audit_rows.append({"check": "immutable_group_field_tamper_detected", "result": immutable_tamper_detected})
    audit_rows.append({"check": "invalid_decision_detected", "result": invalid_decision_detected})
    audit_rows.append({"check": "missing_reviewer_id_detected", "result": missing_reviewer_detected})
    audit_rows.append({"check": "missing_reviewed_at_detected", "result": missing_reviewed_at_detected})
    audit_rows.append({"check": "correct_eps_series_missing_correction_detected", "result": correct_missing_correction_detected})
    audit_rows.append({"check": "needs_more_info_missing_request_detected", "result": needs_more_info_missing_request_detected})
    audit_rows.append({"check": "reject_eps_series_missing_comment_detected", "result": reject_missing_comment_detected})
    audit_rows.append({"check": "forbidden_field_detected", "result": len(forbidden_fields_generated) > 0})
    audit_rows.append({"check": "candidate_mapping_preserved", "result": candidate_mapping_preserved})
    audit_rows.append({"check": "candidate_mapping_count", "result": candidate_mapping_count})
    audit_df = pd.DataFrame(audit_rows)

    negative_tests = {
        "decision_enum": sorted(list(DECISIONS)),
        "correct_eps_series_rule": "requires at least one corrected_2020..2030 or corrected_unit",
        "needs_more_info_rule": "requires extra_info_request",
        "reject_eps_series_warning": "review_comment should be present",
        "forbidden_fields": sorted(list(FORBIDDEN_FIELDS)),
        "immutable_fields_checked": IMMUTABLE_FIELDS,
    }

    _write_excel(OUT_VALID, {"valid_eps_review_results": valid_df if not valid_df.empty else pd.DataFrame([{"note": "no_valid_rows"}])})
    _write_excel(OUT_INVALID, {"invalid_eps_review_results": invalid_df if not invalid_df.empty else pd.DataFrame([{"note": "no_invalid_rows"}])})
    _write_excel(OUT_AUDIT, {"eps_review_validation_audit": audit_df})
    _write_json(OUT_NEG, negative_tests)
    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
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
        "stage": "EVAL-307E",
        "mode": "eps_focused_review_input_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "real_input_present": bool(real_input_present),
        "input_row_count": int(len(input_df)),
        "valid_row_count": int(len(valid_df)),
        "invalid_row_count": int(len(invalid_df)),
        "group_id_unknown_detected": bool(unknown_group_detected),
        "duplicate_group_id_detected": bool(len(dup_gids) > 0),
        "immutable_group_field_tamper_detected": bool(immutable_tamper_detected),
        "invalid_decision_detected": bool(invalid_decision_detected),
        "missing_reviewer_id_detected": bool(missing_reviewer_detected),
        "missing_reviewed_at_detected": bool(missing_reviewed_at_detected),
        "correct_eps_series_missing_correction_detected": bool(correct_missing_correction_detected),
        "needs_more_info_missing_request_detected": bool(needs_more_info_missing_request_detected),
        "forbidden_field_detected": bool(len(forbidden_fields_generated) > 0),
        "candidate_mapping_preserved": bool(candidate_mapping_preserved),
        "candidate_mapping_count": int(candidate_mapping_count),
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "forbidden_fields_generated": forbidden_fields_generated,
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 307E EPS Focused Review Input Validation",
        "",
        "## Input Status",
        f"- real_input_present: {summary['real_input_present']}",
        f"- input_row_count: {summary['input_row_count']}",
        f"- valid_row_count: {summary['valid_row_count']}",
        f"- invalid_row_count: {summary['invalid_row_count']}",
        "",
        "## Validation Flags",
        f"- group_id_unknown_detected: {summary['group_id_unknown_detected']}",
        f"- duplicate_group_id_detected: {summary['duplicate_group_id_detected']}",
        f"- immutable_group_field_tamper_detected: {summary['immutable_group_field_tamper_detected']}",
        f"- invalid_decision_detected: {summary['invalid_decision_detected']}",
        f"- missing_reviewer_id_detected: {summary['missing_reviewer_id_detected']}",
        f"- missing_reviewed_at_detected: {summary['missing_reviewed_at_detected']}",
        f"- correct_eps_series_missing_correction_detected: {summary['correct_eps_series_missing_correction_detected']}",
        f"- needs_more_info_missing_request_detected: {summary['needs_more_info_missing_request_detected']}",
        "",
        "## Guard",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- candidate_mapping_preserved: {summary['candidate_mapping_preserved']}",
        f"- candidate_mapping_count: {summary['candidate_mapping_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_307e_summary_json: {OUT_SUMMARY}")
    print(f"eval_307e_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
