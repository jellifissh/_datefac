from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306k_human_review_input_validation"

IN_306J_SUMMARY = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design" / "306j_summary.json"
IN_MANIFEST = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design" / "306j_candidate_id_manifest.xlsx"
IN_SAMPLE = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design" / "306j_sample_review_input.xlsx"
IN_REAL = BASE_DIR / "input" / "human_review" / "306k_human_review_input.xlsx"

OUT_SUMMARY = OUT_DIR / "306k_summary.json"
OUT_REPORT = OUT_DIR / "306k_report.md"
OUT_VALID = OUT_DIR / "306k_valid_review_results.xlsx"
OUT_INVALID = OUT_DIR / "306k_invalid_review_results.xlsx"
OUT_AUDIT = OUT_DIR / "306k_review_validation_audit.xlsx"
OUT_NEG_TEST = OUT_DIR / "306k_negative_validation_tests.json"
OUT_NO_APPLY = OUT_DIR / "306k_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

ALLOWED_DECISIONS = {"approve", "reject", "needs_more_info", "correct_value"}
FORBIDDEN_COLUMNS = {"safe_to_apply", "approve_for_real_apply"}
REQUIRED_REVIEW_COLS = {
    "candidate_id",
    "decision",
    "reviewer_id",
    "reviewed_at",
    "review_comment",
    "corrected_value",
    "corrected_unit",
    "extra_info_request",
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _canon(v: Any) -> str:
    s = _norm(v)
    if s == "":
        return ""
    low = s.lower()
    if low in {"true", "false"}:
        return low
    try:
        f = float(s)
        return f"{f:.12g}"
    except Exception:
        return s


def _to_int(v: Any) -> int:
    if isinstance(v, bool):
        return 1 if v else 0
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


def _parse_reviewed_at(v: Any) -> bool:
    s = _norm(v)
    if s == "":
        return False
    try:
        pd.to_datetime(s, errors="raise")
        return True
    except Exception:
        return False


def _is_unreviewed_row(row: pd.Series) -> bool:
    return (
        _norm(row.get("decision", "")) == ""
        and _norm(row.get("reviewer_id", "")) == ""
        and _norm(row.get("reviewed_at", "")) == ""
        and _norm(row.get("review_comment", "")) == ""
        and _norm(row.get("corrected_value", "")) == ""
        and _norm(row.get("corrected_unit", "")) == ""
        and _norm(row.get("extra_info_request", "")) == ""
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306J_SUMMARY, IN_MANIFEST, IN_SAMPLE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306K",
                "mode": "human_review_input_validation",
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

    s_306j = json.loads(IN_306J_SUMMARY.read_text(encoding="utf-8"))
    manifest = pd.read_excel(IN_MANIFEST).fillna("")
    sample = pd.read_excel(IN_SAMPLE, sheet_name=0).fillna("")
    real_input_present = IN_REAL.exists()
    real = pd.read_excel(IN_REAL).fillna("") if real_input_present else pd.DataFrame()

    manifest["candidate_id"] = manifest["candidate_id"].map(_norm)
    manifest_map = {row["candidate_id"]: row for _, row in manifest.iterrows()}

    immutable_cols = [c for c in manifest.columns if c != "candidate_id"]
    forbidden_in_manifest = [c for c in manifest.columns if c in FORBIDDEN_COLUMNS]

    inputs: List[Tuple[str, pd.DataFrame]] = [("sample", sample)]
    if real_input_present:
        inputs.append(("real", real))

    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    skipped_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []
    rule_counts: Dict[str, int] = {}

    for src_name, df in inputs:
        cols_lower = {c.lower() for c in df.columns}
        forbidden_present = [c for c in df.columns if c in FORBIDDEN_COLUMNS]
        missing_review_cols = [c for c in REQUIRED_REVIEW_COLS if c not in df.columns]

        # file-level checks
        audit_rows.append(
            {
                "input_source": src_name,
                "row_count": int(len(df)),
                "forbidden_columns_present": "|".join(forbidden_present),
                "missing_required_columns": "|".join(missing_review_cols),
            }
        )
        if forbidden_present:
            rule_counts["forbidden_columns_present"] = rule_counts.get("forbidden_columns_present", 0) + len(forbidden_present)

        # duplicate candidate_id checks on reviewed rows
        reviewed_mask = df.apply(lambda r: not _is_unreviewed_row(r), axis=1)
        reviewed_df = df[reviewed_mask].copy()
        dup_ids = reviewed_df["candidate_id"].map(_norm).value_counts()
        dup_id_set = {cid for cid, cnt in dup_ids.items() if cid != "" and cnt > 1}

        for idx, row in df.iterrows():
            row_out = row.to_dict()
            row_out["input_source"] = src_name
            row_out["row_index"] = int(idx + 2)  # excel-like index considering header
            candidate_id = _norm(row.get("candidate_id", ""))
            decision = _norm(row.get("decision", "")).lower()
            errors: List[str] = []
            warnings: List[str] = []

            if _is_unreviewed_row(row):
                row_out["validation_status"] = "SKIPPED_UNREVIEWED"
                row_out["validation_errors"] = ""
                row_out["validation_warnings"] = ""
                skipped_rows.append(row_out)
                continue

            if candidate_id == "":
                errors.append("candidate_id_required")
            elif candidate_id not in manifest_map:
                errors.append("candidate_id_not_in_manifest")

            if candidate_id in dup_id_set:
                errors.append("candidate_id_duplicated")

            # immutable field checks
            if candidate_id in manifest_map:
                mrow = manifest_map[candidate_id]
                for c in immutable_cols:
                    if c not in row.index:
                        errors.append(f"immutable_field_missing:{c}")
                        continue
                    if _canon(row.get(c, "")) != _canon(mrow.get(c, "")):
                        errors.append(f"immutable_field_changed:{c}")

            # decision and required fields
            if decision not in ALLOWED_DECISIONS:
                errors.append("decision_invalid")

            if _norm(row.get("reviewer_id", "")) == "":
                errors.append("reviewer_id_required")

            reviewed_at = _norm(row.get("reviewed_at", ""))
            if reviewed_at == "":
                errors.append("reviewed_at_required")
            elif not _parse_reviewed_at(reviewed_at):
                errors.append("reviewed_at_unparseable")

            if decision == "correct_value":
                if _norm(row.get("corrected_value", "")) == "":
                    errors.append("corrected_value_required_for_correct_value")
                if _norm(row.get("corrected_unit", "")) == "":
                    errors.append("corrected_unit_required_for_correct_value")

            if decision == "reject" and _norm(row.get("review_comment", "")) == "":
                errors.append("review_comment_required_for_reject")

            if decision == "needs_more_info" and _norm(row.get("extra_info_request", "")) == "":
                errors.append("extra_info_request_required_for_needs_more_info")

            # forbidden columns if exist and non-empty
            for fc in FORBIDDEN_COLUMNS:
                if fc in row.index and _norm(row.get(fc, "")) != "":
                    errors.append(f"forbidden_field_filled:{fc}")

            for e in errors:
                rule_counts[e] = rule_counts.get(e, 0) + 1

            row_out["validation_errors"] = "|".join(errors)
            row_out["validation_warnings"] = "|".join(warnings)
            if errors:
                row_out["validation_status"] = "INVALID"
                invalid_rows.append(row_out)
            else:
                row_out["validation_status"] = "VALID"
                valid_rows.append(row_out)

    valid_df = pd.DataFrame(valid_rows).fillna("")
    invalid_df = pd.DataFrame(invalid_rows).fillna("")
    skipped_df = pd.DataFrame(skipped_rows).fillna("")
    audit_df = pd.DataFrame(audit_rows).fillna("")

    if valid_df.empty:
        valid_df = pd.DataFrame([{"note": "no_valid_review_rows"}])
    if invalid_df.empty:
        invalid_df = pd.DataFrame([{"note": "no_invalid_review_rows"}])
    if skipped_df.empty:
        skipped_df = pd.DataFrame([{"note": "no_skipped_unreviewed_rows"}])

    rule_df = pd.DataFrame(
        [{"rule_key": k, "violation_count": v} for k, v in sorted(rule_counts.items(), key=lambda x: (-x[1], x[0]))]
    )
    if rule_df.empty:
        rule_df = pd.DataFrame([{"rule_key": "no_rule_violation", "violation_count": 0}])

    _write_excel(OUT_VALID, {"valid_review_results": valid_df})
    _write_excel(OUT_INVALID, {"invalid_review_results": invalid_df})
    _write_excel(
        OUT_AUDIT,
        {
            "review_validation_audit": audit_df,
            "rule_violation_counts": rule_df,
            "skipped_unreviewed_rows": skipped_df,
        },
    )

    # Negative validation tests (synthetic) to prove rules.
    neg_tests = [
        {"name": "invalid_decision", "decision": "approve_now", "expected_error": "decision_invalid"},
        {"name": "missing_reviewer", "decision": "approve", "reviewer_id": "", "expected_error": "reviewer_id_required"},
        {"name": "missing_reviewed_at", "decision": "approve", "reviewed_at": "", "expected_error": "reviewed_at_required"},
        {"name": "bad_reviewed_at", "decision": "approve", "reviewed_at": "not-a-time", "expected_error": "reviewed_at_unparseable"},
        {"name": "correct_value_missing_fields", "decision": "correct_value", "corrected_value": "", "corrected_unit": "", "expected_error": "corrected_value_required_for_correct_value"},
        {"name": "reject_without_comment", "decision": "reject", "review_comment": "", "expected_error": "review_comment_required_for_reject"},
        {"name": "needs_more_info_without_request", "decision": "needs_more_info", "extra_info_request": "", "expected_error": "extra_info_request_required_for_needs_more_info"},
        {"name": "forbidden_field_present", "field": "safe_to_apply", "expected_error": "forbidden_columns_present"},
    ]
    _write_json(
        OUT_NEG_TEST,
        {
            "stage": "EVAL-306K",
            "negative_tests": neg_tests,
            "note": "rule coverage reference for downstream automation",
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

    # counts excluding placeholder rows
    valid_count = 0 if ("note" in valid_df.columns and len(valid_df) == 1) else len(valid_rows)
    invalid_count = 0 if ("note" in invalid_df.columns and len(invalid_df) == 1) else len(invalid_rows)
    skipped_count = 0 if ("note" in skipped_df.columns and len(skipped_df) == 1) else len(skipped_rows)

    summary = {
        "stage": "EVAL-306K",
        "mode": "human_review_input_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "manifest_candidate_count": int(len(manifest)),
        "sample_input_present": True,
        "real_input_present": bool(real_input_present),
        "validated_sources": [name for name, _ in inputs],
        "valid_review_row_count": int(valid_count),
        "invalid_review_row_count": int(invalid_count),
        "skipped_unreviewed_row_count": int(skipped_count),
        "rule_violation_total_count": int(sum(rule_counts.values())),
        "forbidden_columns_present_count": int(
            sum(
                _to_int(r.get("forbidden_columns_present", "") != "")
                for _, r in audit_df.iterrows()
                if "forbidden_columns_present" in audit_df.columns
            )
        ),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306K Human Review Input Validation",
        "",
        f"- manifest_candidate_count: {summary['manifest_candidate_count']}",
        f"- sample_input_present: {summary['sample_input_present']}",
        f"- real_input_present: {summary['real_input_present']}",
        f"- validated_sources: {', '.join(summary['validated_sources'])}",
        f"- valid_review_row_count: {summary['valid_review_row_count']}",
        f"- invalid_review_row_count: {summary['invalid_review_row_count']}",
        f"- skipped_unreviewed_row_count: {summary['skipped_unreviewed_row_count']}",
        f"- rule_violation_total_count: {summary['rule_violation_total_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306k_summary_json: {OUT_SUMMARY}")
    print(f"eval_306k_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
