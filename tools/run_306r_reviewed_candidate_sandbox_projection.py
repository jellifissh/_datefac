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
OUT_DIR = BASE_DIR / "output" / "eval_306r_reviewed_candidate_sandbox_projection"

IN_306Q_SUMMARY = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_summary.json"
IN_POOL = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_reviewed_candidate_pool.xlsx"
IN_CORR_AUDIT = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_corrected_value_audit.xlsx"
IN_MISS_AUDIT = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_missing_candidate_intake_audit.xlsx"
IN_EXCL_AUDIT = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_excluded_rejected_needs_more_info_audit.xlsx"
IN_306M_G2C = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_to_candidate_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "306r_summary.json"
OUT_REPORT = OUT_DIR / "306r_report.md"
OUT_PROJ = OUT_DIR / "306r_reviewed_candidate_projection.xlsx"
OUT_VALUE_AUDIT = OUT_DIR / "306r_effective_value_audit.xlsx"
OUT_UNIT_AUDIT = OUT_DIR / "306r_unit_sanity_audit.xlsx"
OUT_MISSING_PROJ = OUT_DIR / "306r_missing_candidate_projection_preview.xlsx"
OUT_EXCLUDED_AUDIT = OUT_DIR / "306r_excluded_candidate_audit.xlsx"
OUT_DUP = OUT_DIR / "306r_projection_duplicate_key_audit.xlsx"
OUT_CONFLICT = OUT_DIR / "306r_projection_value_conflict_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "306r_no_apply_proof.json"

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


def _drop_note_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "note" in df.columns:
        return df[~df["note"].map(_norm).str.startswith("no_")].copy()
    return df.copy()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306Q_SUMMARY, IN_POOL, IN_CORR_AUDIT, IN_MISS_AUDIT, IN_EXCL_AUDIT, IN_306M_G2C]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306R",
                "mode": "reviewed_candidate_sandbox_projection",
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

    s_306q = json.loads(IN_306Q_SUMMARY.read_text(encoding="utf-8"))
    reviewed_pool = _drop_note_rows(_load_first_sheet(IN_POOL, "reviewed_candidate_pool"))
    corrected_audit = _drop_note_rows(_load_first_sheet(IN_CORR_AUDIT, "corrected_candidates"))
    missing_intake = _drop_note_rows(_load_first_sheet(IN_MISS_AUDIT, "missing_candidate_intake"))
    excluded_needs = _drop_note_rows(_load_first_sheet(IN_EXCL_AUDIT, "excluded_needs_more_info"))
    excluded_rej = _drop_note_rows(_load_first_sheet(IN_EXCL_AUDIT, "excluded_rejected"))
    g2c = pd.read_excel(IN_306M_G2C).fillna("")

    # Build sandbox reviewed projection rows.
    proj = reviewed_pool.copy()
    proj["candidate_id"] = proj.get("candidate_id", "").map(_norm) if "candidate_id" in proj.columns else ""
    proj["decision_candidate"] = proj.get("decision_candidate", "").map(_norm) if "decision_candidate" in proj.columns else ""

    # original value fields normalization
    if "original_value" not in proj.columns:
        proj["original_value"] = proj.get("原数值", "")
    proj["original_value"] = proj["original_value"].map(_norm)
    proj["corrected_value"] = proj.get("corrected_value", "").map(_norm)
    proj["corrected_unit"] = proj.get("corrected_unit", "").map(_norm)
    proj["original_unit"] = proj.get("单位", "").map(_norm) if "单位" in proj.columns else ""

    # Effective projection rules
    proj["effective_value"] = proj["original_value"]
    proj.loc[proj["decision_candidate"].eq("correct_value"), "effective_value"] = proj.loc[
        proj["decision_candidate"].eq("correct_value"), "corrected_value"
    ]
    proj["effective_unit"] = proj["original_unit"]
    corr_mask = proj["decision_candidate"].eq("correct_value")
    proj.loc[corr_mask & proj["corrected_unit"].ne(""), "effective_unit"] = proj.loc[corr_mask & proj["corrected_unit"].ne(""), "corrected_unit"]

    # Projection only includes approve + correct_value
    proj = proj[proj["decision_candidate"].isin(["approve", "correct_value"])].copy()

    # Missing candidate projection preview (separate pool, no fake candidate id)
    missing_preview = missing_intake.copy()
    if "candidate_id" not in missing_preview.columns:
        missing_preview["candidate_id"] = ""
    missing_preview["candidate_id"] = missing_preview["candidate_id"].map(_norm)
    missing_preview["effective_value"] = missing_preview.get("corrected_value", "").map(_norm)
    missing_preview["effective_unit"] = missing_preview.get("corrected_unit", "").map(_norm)
    missing_preview["projection_bucket"] = "missing_candidate_projection_preview"

    # Excluded candidate audit snapshot
    excluded_df = pd.DataFrame(
        [
            {"bucket": "rejected", "count": int(len(excluded_rej)), "in_projection_count": int(0)},
            {"bucket": "needs_more_info", "count": int(len(excluded_needs)), "in_projection_count": int(0)},
        ]
    )

    # Fake candidate id checks
    manifest_ids = set(g2c["candidate_id"].map(_norm).tolist())
    fake_candidate_id_generated_count = int(
        sum(1 for cid in proj["candidate_id"].map(_norm).tolist() if cid != "" and cid not in manifest_ids)
    )
    missing_fake_candidate_id_count = int(
        sum(1 for cid in missing_preview["candidate_id"].map(_norm).tolist() if cid != "" and cid not in manifest_ids)
    )

    # Duplicate key and value conflict checks on projection.
    key_cols = ["PDF文件名", "标准指标", "年份"]
    if all(c in proj.columns for c in key_cols) and not proj.empty:
        key_df = proj.copy()
        key_df["key_pdf"] = key_df["PDF文件名"].map(_norm)
        key_df["key_metric"] = key_df["标准指标"].map(_norm)
        key_df["key_year"] = key_df["年份"].map(_to_int)
        key_df["key"] = key_df["key_pdf"] + "|" + key_df["key_metric"] + "|" + key_df["key_year"].astype(str)

        dup_keys = key_df.groupby("key", dropna=False).size().reset_index(name="count")
        dup_keys = dup_keys[dup_keys["count"] > 1].copy()
        dup_detail = key_df[key_df["key"].isin(set(dup_keys["key"]))].copy() if not dup_keys.empty else pd.DataFrame()

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
                        "distinct_effective_values": " | ".join(vals),
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

    # Forbidden fields
    all_cols = set(proj.columns).union(set(missing_preview.columns))
    forbidden_fields_generated = sorted([c for c in all_cols if c in FORBIDDEN_FIELDS])

    # Assertion counts
    reviewed_candidate_pool_count = int(s_306q.get("reviewed_candidate_pool_count", 0))
    projection_count = int(len(proj))
    rejected_needs_in_projection_count = int((proj["decision_candidate"].isin(["reject", "needs_more_info"])).sum()) if "decision_candidate" in proj.columns else 0
    missing_only_separate = bool(
        ("candidate_id" in missing_preview.columns) and (missing_preview["candidate_id"].map(_norm).eq("").all())
    )

    # Output tables
    _write_excel(
        OUT_PROJ,
        {
            "reviewed_candidate_projection": proj if not proj.empty else pd.DataFrame([{"note": "no_projection_rows"}]),
            "projection_distribution": (
                proj.groupby("decision_candidate", dropna=False).size().reset_index(name="row_count")
                if not proj.empty and "decision_candidate" in proj.columns
                else pd.DataFrame([{"decision_candidate": "N/A", "row_count": 0}])
            ),
        },
    )
    _write_excel(
        OUT_VALUE_AUDIT,
        {
            "effective_value_audit": proj[
                [
                    c
                    for c in [
                        "candidate_id",
                        "PDF文件名",
                        "标准指标",
                        "年份",
                        "decision_candidate",
                        "original_value",
                        "corrected_value",
                        "effective_value",
                        "reviewer_id",
                        "reviewed_at",
                        "review_comment",
                    ]
                    if c in proj.columns
                ]
            ]
            if not proj.empty
            else pd.DataFrame([{"note": "no_effective_value_rows"}]),
        },
    )
    _write_excel(
        OUT_UNIT_AUDIT,
        {
            "unit_sanity_audit": proj[
                [
                    c
                    for c in [
                        "candidate_id",
                        "PDF文件名",
                        "标准指标",
                        "年份",
                        "decision_candidate",
                        "original_unit",
                        "corrected_unit",
                        "effective_unit",
                    ]
                    if c in proj.columns
                ]
            ]
            if not proj.empty
            else pd.DataFrame([{"note": "no_unit_rows"}]),
        },
    )
    _write_excel(
        OUT_MISSING_PROJ,
        {
            "missing_candidate_projection_preview": missing_preview if not missing_preview.empty else pd.DataFrame([{"note": "no_missing_projection_rows"}]),
        },
    )
    _write_excel(OUT_EXCLUDED_AUDIT, {"excluded_candidate_audit": excluded_df})
    _write_excel(
        OUT_DUP,
        {
            "duplicate_key_summary": dup_keys if not dup_keys.empty else pd.DataFrame([{"note": "duplicate_key_count_0"}]),
            "duplicate_key_detail": dup_detail if not dup_detail.empty else pd.DataFrame([{"note": "no_duplicate_key_rows"}]),
        },
    )
    _write_excel(
        OUT_CONFLICT,
        {"projection_value_conflict_audit": conflict_df if not conflict_df.empty else pd.DataFrame([{"note": "value_conflict_count_0"}])},
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
        "stage": "EVAL-306R",
        "mode": "reviewed_candidate_sandbox_projection",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "reviewed_candidate_pool_count_from_306q": reviewed_candidate_pool_count,
        "reviewed_candidate_projection_count": projection_count,
        "reviewed_candidate_projection_count_match_306q": bool(projection_count == reviewed_candidate_pool_count),
        "rejected_and_needs_more_info_count_in_projection": rejected_needs_in_projection_count,
        "missing_candidate_projection_preview_count": int(len(missing_preview)),
        "missing_candidates_only_in_missing_projection_preview": bool(missing_only_separate),
        "fake_candidate_id_generated_count": int(fake_candidate_id_generated_count + missing_fake_candidate_id_count),
        "duplicate_key_count": duplicate_key_count,
        "value_conflict_count": value_conflict_count,
        "forbidden_fields_generated": forbidden_fields_generated,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "source_306q_stage": _norm(s_306q.get("stage", "")),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306R Reviewed Candidate Sandbox Projection",
        "",
        "## Scope",
        "- Projected 306Q reviewed candidate pool to sandbox effective preview rows only.",
        "- Rejected / needs_more_info excluded from projection.",
        "- Missing candidate intake projected separately without candidate_id fabrication.",
        "",
        "## Counts",
        f"- reviewed_candidate_pool_count_from_306q: {summary['reviewed_candidate_pool_count_from_306q']}",
        f"- reviewed_candidate_projection_count: {summary['reviewed_candidate_projection_count']}",
        f"- missing_candidate_projection_preview_count: {summary['missing_candidate_projection_preview_count']}",
        "",
        "## Assertions",
        f"- reviewed_candidate_projection_count_match_306q: {summary['reviewed_candidate_projection_count_match_306q']}",
        f"- rejected_and_needs_more_info_count_in_projection: {summary['rejected_and_needs_more_info_count_in_projection']}",
        f"- missing_candidates_only_in_missing_projection_preview: {summary['missing_candidates_only_in_missing_projection_preview']}",
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

    print(f"eval_306r_summary_json: {OUT_SUMMARY}")
    print(f"eval_306r_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

