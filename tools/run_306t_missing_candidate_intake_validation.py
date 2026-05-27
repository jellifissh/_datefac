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
OUT_DIR = BASE_DIR / "output" / "eval_306t_missing_candidate_intake_validation"

IN_306S_SUMMARY = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate" / "306s_summary.json"
IN_PROJ = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate" / "306s_unit_normalized_projection.xlsx"
IN_MISSING = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate" / "306s_missing_candidate_unit_preview.xlsx"
IN_306M_G2C = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_to_candidate_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "306t_summary.json"
OUT_REPORT = OUT_DIR / "306t_report.md"
OUT_VALID = OUT_DIR / "306t_valid_missing_candidate_intake.xlsx"
OUT_INVALID = OUT_DIR / "306t_invalid_missing_candidate_intake.xlsx"
OUT_CONFLICT = OUT_DIR / "306t_missing_candidate_conflict_audit.xlsx"
OUT_DUP = OUT_DIR / "306t_missing_candidate_duplicate_audit.xlsx"
OUT_COMBINED = OUT_DIR / "306t_combined_reviewed_plus_missing_preview.xlsx"
OUT_NO_APPLY = OUT_DIR / "306t_no_apply_proof.json"

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


def _load_first_sheet(path: Path, preferred: str | None = None) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    if preferred and preferred in xls.sheet_names:
        return pd.read_excel(path, sheet_name=preferred).fillna("")
    return pd.read_excel(path, sheet_name=xls.sheet_names[0]).fillna("")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306S_SUMMARY, IN_PROJ, IN_MISSING, IN_306M_G2C]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306T",
                "mode": "missing_candidate_intake_validation",
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

    s_306s = json.loads(IN_306S_SUMMARY.read_text(encoding="utf-8"))
    reviewed = _load_first_sheet(IN_PROJ, "unit_normalized_projection")
    missing_df = _load_first_sheet(IN_MISSING, "missing_candidate_unit_preview")
    g2c = pd.read_excel(IN_306M_G2C).fillna("")

    # Key prep for reviewed projection
    reviewed = reviewed.fillna("")
    reviewed["key_pdf"] = reviewed.get("PDF文件名", "").map(_norm)
    reviewed["key_metric"] = reviewed.get("标准指标", "").map(_norm)
    reviewed["key_year"] = reviewed.get("年份", 0).map(_to_int)
    reviewed["key"] = reviewed["key_pdf"] + "|" + reviewed["key_metric"] + "|" + reviewed["key_year"].astype(str)
    reviewed["effective_value_norm"] = reviewed.get("effective_value", "").map(_norm)
    reviewed_key_to_values = {
        k: sorted({v for v in g["effective_value_norm"].tolist() if v != ""})
        for k, g in reviewed.groupby("key", dropna=False)
    }

    # Validate missing intake rows
    missing_df = missing_df.fillna("")
    errors_rows: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    dup_rows: List[Dict[str, Any]] = []

    # duplicate detection inside missing intake
    md = missing_df.copy()
    md["key_pdf"] = md.get("PDF文件名", "").map(_norm)
    md["key_metric"] = md.get("标准指标", "").map(_norm)
    md["key_year"] = md.get("年份", 0).map(_to_int)
    md["key"] = md["key_pdf"] + "|" + md["key_metric"] + "|" + md["key_year"].astype(str)
    dup_in_missing = md.groupby("key", dropna=False).size().reset_index(name="count")
    dup_in_missing = dup_in_missing[dup_in_missing["count"] > 1].copy()
    if not dup_in_missing.empty:
        dup_rows.extend(dup_in_missing.to_dict("records"))

    # fake candidate id check set
    manifest_ids = set(g2c["candidate_id"].map(_norm).tolist())

    for _, r in md.iterrows():
        rec = r.to_dict()
        errs: List[str] = []

        cid = _norm(r.get("candidate_id", ""))
        pdf = _norm(r.get("PDF文件名", ""))
        metric = _norm(r.get("标准指标", ""))
        year = _to_int(r.get("年份", 0))
        value = _norm(r.get("effective_value", ""))
        unit = _norm(r.get("normalized_unit", ""))
        warn = _norm(r.get("unit_warning", ""))
        key = _norm(r.get("key", ""))

        # no fake candidate_id
        if cid != "" and cid not in manifest_ids:
            errs.append("fake_candidate_id")

        # required fields
        if pdf == "":
            errs.append("missing_pdf")
        if metric == "":
            errs.append("missing_metric")
        if year == 0:
            errs.append("missing_year")
        if value == "":
            errs.append("missing_value")
        if unit == "" and warn == "":
            errs.append("missing_unit_and_warning")

        # year range
        if year < 2020 or year > 2032:
            errs.append("year_out_of_range")

        # no duplicate key against reviewed projection
        if key in set(reviewed["key"].tolist()):
            errs.append("duplicate_key_against_reviewed_projection")
            dup_rows.append(
                {
                    "key": key,
                    "source": "missing_vs_reviewed",
                    "missing_value": value,
                    "reviewed_values": " | ".join(reviewed_key_to_values.get(key, [])),
                }
            )

        # no value conflict against reviewed projection
        rv = reviewed_key_to_values.get(key, [])
        if key in reviewed_key_to_values and value != "" and len(rv) > 0 and value not in rv:
            errs.append("value_conflict_against_reviewed_projection")
            conflict_rows.append(
                {
                    "key": key,
                    "PDF文件名": pdf,
                    "标准指标": metric,
                    "年份": year,
                    "missing_effective_value": value,
                    "reviewed_effective_values": " | ".join(rv),
                }
            )

        # forbidden fields absent (column-level checked separately, row-level marker only)
        rec["validation_errors"] = ";".join(errs)
        rec["validation_status"] = "VALID" if len(errs) == 0 else "INVALID"
        if len(errs) == 0:
            valid_rows.append(rec)
        else:
            errors_rows.append(rec)

    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(errors_rows)
    conflict_df = pd.DataFrame(conflict_rows)
    dup_df = pd.DataFrame(dup_rows)

    if valid_df.empty:
        valid_df = pd.DataFrame([{"note": "no_valid_missing_rows"}])
    if invalid_df.empty:
        invalid_df = pd.DataFrame([{"note": "no_invalid_missing_rows"}])
    if conflict_df.empty:
        conflict_df = pd.DataFrame([{"note": "no_missing_conflict_rows"}])
    if dup_df.empty:
        dup_df = pd.DataFrame([{"note": "no_missing_duplicate_rows"}])

    # combined preview (keep separate buckets)
    rp = reviewed.copy()
    rp["preview_bucket"] = "reviewed_projection"
    mp = md.copy()
    mp["preview_bucket"] = "missing_candidate_intake_preview"
    combined = pd.concat([rp, mp], ignore_index=True, sort=False).fillna("")

    # assertions
    forbidden_fields_generated = [c for c in combined.columns if c in FORBIDDEN_FIELDS]
    fake_candidate_id_generated_count = int(
        sum(
            1
            for cid in md.get("candidate_id", pd.Series(dtype=str)).map(_norm).tolist()
            if cid != "" and cid not in manifest_ids
        )
    )
    duplicate_key_count = int(0 if "note" in dup_df.columns else len(dup_df))
    value_conflict_count = int(0 if "note" in conflict_df.columns else len(conflict_df))
    valid_count = int(0 if "note" in valid_df.columns else len(valid_df))
    invalid_count = int(0 if "note" in invalid_df.columns else len(invalid_df))

    _write_excel(OUT_VALID, {"valid_missing_candidate_intake": valid_df})
    _write_excel(OUT_INVALID, {"invalid_missing_candidate_intake": invalid_df})
    _write_excel(OUT_CONFLICT, {"missing_candidate_conflict_audit": conflict_df})
    _write_excel(OUT_DUP, {"missing_candidate_duplicate_audit": dup_df})
    _write_excel(
        OUT_COMBINED,
        {
            "combined_reviewed_plus_missing_preview": combined,
            "bucket_distribution": combined.groupby("preview_bucket", dropna=False).size().reset_index(name="row_count"),
        },
    )
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
        "stage": "EVAL-306T",
        "mode": "missing_candidate_intake_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "reviewed_projection_count": int(len(reviewed)),
        "missing_candidate_input_count": int(len(md)),
        "valid_missing_candidate_count": valid_count,
        "invalid_missing_candidate_count": invalid_count,
        "fake_candidate_id_generated_count": fake_candidate_id_generated_count,
        "duplicate_key_count": duplicate_key_count,
        "value_conflict_count": value_conflict_count,
        "forbidden_fields_generated": forbidden_fields_generated,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "source_306s_stage": _norm(s_306s.get("stage", "")),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306T Missing Candidate Intake Validation",
        "",
        "## Scope",
        "- Validated missing candidate intake from 306S before any sandbox export preview.",
        "- Kept reviewed projection and missing preview in separate buckets.",
        "- No apply operations and no production changes.",
        "",
        "## Counts",
        f"- reviewed_projection_count: {summary['reviewed_projection_count']}",
        f"- missing_candidate_input_count: {summary['missing_candidate_input_count']}",
        f"- valid_missing_candidate_count: {summary['valid_missing_candidate_count']}",
        f"- invalid_missing_candidate_count: {summary['invalid_missing_candidate_count']}",
        "",
        "## Assertions",
        f"- fake_candidate_id_generated_count: {summary['fake_candidate_id_generated_count']}",
        f"- duplicate_key_count: {summary['duplicate_key_count']}",
        f"- value_conflict_count: {summary['value_conflict_count']}",
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

    print(f"eval_306t_summary_json: {OUT_SUMMARY}")
    print(f"eval_306t_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

