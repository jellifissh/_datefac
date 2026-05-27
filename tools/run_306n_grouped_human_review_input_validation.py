from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306n_grouped_human_review_input_validation"

IN_306M_SUMMARY = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_summary.json"
IN_GROUP_MANIFEST = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_id_manifest.xlsx"
IN_GROUP_TO_CAND = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_to_candidate_manifest.xlsx"
IN_SAMPLE = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_sample_grouped_review_input.xlsx"
IN_REAL = BASE_DIR / "input" / "human_review" / "306n_grouped_human_review_input.xlsx"

OUT_SUMMARY = OUT_DIR / "306n_summary.json"
OUT_REPORT = OUT_DIR / "306n_report.md"
OUT_VALID = OUT_DIR / "306n_valid_group_review_results.xlsx"
OUT_INVALID = OUT_DIR / "306n_invalid_group_review_results.xlsx"
OUT_AUDIT = OUT_DIR / "306n_group_review_validation_audit.xlsx"
OUT_NEG_TEST = OUT_DIR / "306n_negative_validation_tests.json"
OUT_NO_APPLY = OUT_DIR / "306n_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

ALLOWED_DECISIONS = {"approve_series", "reject_series", "needs_more_info", "correct_series"}
FORBIDDEN_COLUMNS = {"safe_to_apply", "approve_for_real_apply"}
CORRECTED_YEAR_COLS = [f"corrected_{y}" for y in range(2020, 2031)]
REQUIRED_REVIEW_COLS = {
    "group_id",
    "decision",
    "reviewer_id",
    "reviewed_at",
    "review_comment",
    "extra_info_request",
    "corrected_unit",
    *CORRECTED_YEAR_COLS,
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
        and _norm(row.get("extra_info_request", "")) == ""
        and _norm(row.get("corrected_unit", "")) == ""
        and all(_norm(row.get(c, "")) == "" for c in CORRECTED_YEAR_COLS)
    )


def _has_any_series_correction(row: pd.Series) -> bool:
    if _norm(row.get("corrected_unit", "")) != "":
        return True
    for c in CORRECTED_YEAR_COLS:
        if _norm(row.get(c, "")) != "":
            return True
    return False


def _build_negative_tests(sample_df: pd.DataFrame, immutable_cols: List[str]) -> List[Dict[str, Any]]:
    tests: List[Dict[str, Any]] = []
    if sample_df.empty:
        return tests

    base = sample_df.iloc[0].to_dict()

    def run_case(name: str, mutate: Dict[str, Any], expected_error_contains: str) -> None:
        row = dict(base)
        row.update(mutate)
        errs: List[str] = []

        decision = _norm(row.get("decision", "")).lower()
        if decision not in ALLOWED_DECISIONS:
            errs.append("decision_invalid")
        if _norm(row.get("reviewer_id", "")) == "":
            errs.append("reviewer_id_required")
        if not _parse_reviewed_at(row.get("reviewed_at", "")):
            errs.append("reviewed_at_required_or_unparseable")
        if decision == "correct_series" and not _has_any_series_correction(pd.Series(row)):
            errs.append("correct_series_missing_correction")
        if decision == "needs_more_info" and _norm(row.get("extra_info_request", "")) == "":
            errs.append("needs_more_info_missing_extra_info_request")
        if decision == "reject_series" and _norm(row.get("review_comment", "")) == "":
            errs.append("reject_series_missing_review_comment")

        tests.append(
            {
                "test_case": name,
                "mutations": mutate,
                "expected_error_contains": expected_error_contains,
                "actual_errors": errs,
                "detected": any(expected_error_contains in e for e in errs),
            }
        )

    run_case(
        "invalid_decision",
        {"decision": "approve_for_real_apply"},
        "decision_invalid",
    )
    run_case(
        "missing_reviewer_id",
        {"decision": "approve_series", "reviewer_id": ""},
        "reviewer_id_required",
    )
    run_case(
        "bad_reviewed_at",
        {"decision": "approve_series", "reviewed_at": "not-a-date"},
        "reviewed_at_required_or_unparseable",
    )
    run_case(
        "correct_series_missing_all_corrections",
        {
            "decision": "correct_series",
            "corrected_unit": "",
            **{k: "" for k in CORRECTED_YEAR_COLS},
        },
        "correct_series_missing_correction",
    )
    run_case(
        "needs_more_info_missing_extra_info_request",
        {"decision": "needs_more_info", "extra_info_request": ""},
        "needs_more_info_missing_extra_info_request",
    )
    run_case(
        "reject_series_missing_review_comment",
        {"decision": "reject_series", "review_comment": ""},
        "reject_series_missing_review_comment",
    )

    return tests


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306M_SUMMARY, IN_GROUP_MANIFEST, IN_GROUP_TO_CAND, IN_SAMPLE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306N",
                "mode": "grouped_human_review_input_validation",
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

    s_306m = json.loads(IN_306M_SUMMARY.read_text(encoding="utf-8"))
    manifest = pd.read_excel(IN_GROUP_MANIFEST).fillna("")
    g2c = pd.read_excel(IN_GROUP_TO_CAND).fillna("")
    sample = pd.read_excel(IN_SAMPLE, sheet_name=0).fillna("")
    real_input_present = IN_REAL.exists()
    real = pd.read_excel(IN_REAL).fillna("") if real_input_present else pd.DataFrame()

    manifest["group_id"] = manifest["group_id"].map(_norm)
    manifest_map = {row["group_id"]: row for _, row in manifest.iterrows()}
    immutable_cols = [c for c in manifest.columns if c != "group_id"]

    g2c["candidate_id"] = g2c["candidate_id"].map(_norm)
    mapping_row_count = int(len(g2c))
    mapping_unique_candidate_count = int(g2c["candidate_id"].nunique())
    mapping_count_ok = mapping_row_count == 372 and mapping_unique_candidate_count == 372

    inputs: List[Tuple[str, pd.DataFrame]] = [("sample", sample)]
    if real_input_present:
        inputs.append(("real", real))

    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    skipped_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []
    rule_counts: Dict[str, int] = {}

    for src_name, df in inputs:
        forbidden_present = [c for c in df.columns if c in FORBIDDEN_COLUMNS]
        missing_review_cols = [c for c in REQUIRED_REVIEW_COLS if c not in df.columns]
        missing_immutable_cols = [c for c in immutable_cols if c not in df.columns]

        audit_rows.append(
            {
                "input_source": src_name,
                "row_count": int(len(df)),
                "forbidden_columns_present": "|".join(forbidden_present),
                "missing_required_review_columns": "|".join(missing_review_cols),
                "missing_immutable_columns": "|".join(missing_immutable_cols),
            }
        )
        if forbidden_present:
            rule_counts["forbidden_columns_present"] = rule_counts.get("forbidden_columns_present", 0) + len(forbidden_present)

        reviewed_mask = df.apply(lambda r: not _is_unreviewed_row(r), axis=1)
        reviewed_df = df[reviewed_mask].copy()
        dup_ids = reviewed_df["group_id"].map(_norm).value_counts() if "group_id" in reviewed_df.columns else pd.Series(dtype=int)
        dup_id_set = {gid for gid, cnt in dup_ids.items() if gid != "" and cnt > 1}

        for idx, row in df.iterrows():
            row_out = row.to_dict()
            row_out["input_source"] = src_name
            row_out["row_index"] = int(idx + 2)
            errors: List[str] = []
            warnings: List[str] = []

            if _is_unreviewed_row(row):
                row_out["validation_status"] = "SKIPPED_UNREVIEWED"
                row_out["validation_errors"] = ""
                row_out["validation_warnings"] = ""
                skipped_rows.append(row_out)
                continue

            if forbidden_present:
                errors.append("forbidden_columns_present")

            gid = _norm(row.get("group_id", ""))
            decision = _norm(row.get("decision", "")).lower()

            if gid == "":
                errors.append("group_id_required")
            elif gid not in manifest_map:
                errors.append("group_id_not_in_manifest")

            if gid in dup_id_set:
                errors.append("group_id_duplicated")

            if gid in manifest_map:
                mrow = manifest_map[gid]
                for c in immutable_cols:
                    if c not in row.index:
                        errors.append(f"immutable_field_missing:{c}")
                        continue
                    if _canon(row.get(c, "")) != _canon(mrow.get(c, "")):
                        errors.append(f"immutable_field_changed:{c}")

            if decision not in ALLOWED_DECISIONS:
                errors.append("decision_invalid")

            if _norm(row.get("reviewer_id", "")) == "":
                errors.append("reviewer_id_required")

            if not _parse_reviewed_at(row.get("reviewed_at", "")):
                errors.append("reviewed_at_required_or_unparseable")

            if decision == "correct_series" and not _has_any_series_correction(row):
                errors.append("correct_series_missing_correction")

            if decision == "needs_more_info" and _norm(row.get("extra_info_request", "")) == "":
                errors.append("needs_more_info_missing_extra_info_request")

            if decision == "reject_series" and _norm(row.get("review_comment", "")) == "":
                errors.append("reject_series_missing_review_comment")

            for e in errors:
                rule_counts[e] = rule_counts.get(e, 0) + 1

            row_out["validation_errors"] = ";".join(errors)
            row_out["validation_warnings"] = ";".join(warnings)
            row_out["validation_status"] = "INVALID" if errors else "VALID"

            if errors:
                invalid_rows.append(row_out)
            else:
                valid_rows.append(row_out)

    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)
    skipped_df = pd.DataFrame(skipped_rows)
    audit_df = pd.DataFrame(audit_rows)
    rule_df = pd.DataFrame(
        [{"rule": k, "count": v} for k, v in sorted(rule_counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    )
    neg_tests = _build_negative_tests(sample, immutable_cols)
    neg_pass_count = sum(1 for x in neg_tests if x.get("detected"))

    if valid_df.empty:
        valid_df = pd.DataFrame([{"note": "no_valid_review_rows"}])
    if invalid_df.empty:
        invalid_df = pd.DataFrame([{"note": "no_invalid_review_rows"}])
    if skipped_df.empty:
        skipped_df = pd.DataFrame([{"note": "no_skipped_unreviewed_rows"}])
    if audit_df.empty:
        audit_df = pd.DataFrame([{"note": "no_audit_rows"}])
    if rule_df.empty:
        rule_df = pd.DataFrame([{"rule": "no_rule_violations", "count": 0}])

    _write_excel(OUT_VALID, {"valid_group_review_results": valid_df})
    _write_excel(OUT_INVALID, {"invalid_group_review_results": invalid_df})
    _write_excel(
        OUT_AUDIT,
        {
            "file_level_audit": audit_df,
            "rule_violation_counts": rule_df,
            "skipped_unreviewed_rows": skipped_df,
            "mapping_integrity": pd.DataFrame(
                [
                    {
                        "mapping_row_count": mapping_row_count,
                        "mapping_unique_candidate_count": mapping_unique_candidate_count,
                        "mapping_count_ok_372": mapping_count_ok,
                    }
                ]
            ),
        },
    )
    _write_json(
        OUT_NEG_TEST,
        {
            "stage": "EVAL-306N",
            "negative_test_total_count": len(neg_tests),
            "negative_test_detected_count": int(neg_pass_count),
            "negative_tests": neg_tests,
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
        "stage": "EVAL-306N",
        "mode": "grouped_human_review_input_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "real_input_present": bool(real_input_present),
        "validated_input_sources": [k for k, _ in inputs],
        "sample_row_count": int(len(sample)),
        "real_row_count": int(len(real) if real_input_present else 0),
        "manifest_group_row_count": int(len(manifest)),
        "mapping_row_count": mapping_row_count,
        "mapping_unique_candidate_count": mapping_unique_candidate_count,
        "mapping_count_ok_372": bool(mapping_count_ok),
        "valid_review_row_count": int(len(valid_rows)),
        "invalid_review_row_count": int(len(invalid_rows)),
        "skipped_unreviewed_row_count": int(len(skipped_rows)),
        "rule_violation_type_count": int(len(rule_counts)),
        "negative_test_total_count": len(neg_tests),
        "negative_test_detected_count": int(neg_pass_count),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306N Grouped Human Review Input Validation",
        "",
        "## Scope",
        "- Validated grouped human review input from 306M.",
        "- Sample input validated first; real input path validated only if present.",
        "- No Marker/pdfplumber rerun. No API/LLM/OCR.",
        "",
        "## Input Status",
        f"- real_input_present: {summary['real_input_present']}",
        f"- sample_row_count: {summary['sample_row_count']}",
        f"- real_row_count: {summary['real_row_count']}",
        "",
        "## Validation Result",
        f"- valid_review_row_count: {summary['valid_review_row_count']}",
        f"- invalid_review_row_count: {summary['invalid_review_row_count']}",
        f"- skipped_unreviewed_row_count: {summary['skipped_unreviewed_row_count']}",
        f"- mapping_count_ok_372: {summary['mapping_count_ok_372']}",
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

    print(f"eval_306n_summary_json: {OUT_SUMMARY}")
    print(f"eval_306n_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

