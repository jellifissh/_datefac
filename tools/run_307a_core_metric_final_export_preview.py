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
OUT_DIR = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview"

IN_Z_AUTO = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_auto_accept_candidate_preview_v2.xlsx"
IN_Z_REVIEW = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_review_required_v2.xlsx"
IN_S_PROJ = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate" / "306s_unit_normalized_projection.xlsx"
IN_T_VALID = BASE_DIR / "output" / "eval_306t_missing_candidate_intake_validation" / "306t_valid_missing_candidate_intake.xlsx"
IN_Q_POOL = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_reviewed_candidate_pool.xlsx"
IN_L_MAP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_group_to_candidate_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "307a_summary.json"
OUT_REPORT = OUT_DIR / "307a_report.md"
OUT_FINAL = OUT_DIR / "307a_final_core_metric_preview.xlsx"
OUT_AUTO = OUT_DIR / "307a_auto_accept_core_metrics.xlsx"
OUT_MANUAL = OUT_DIR / "307a_manual_reviewed_core_metrics.xlsx"
OUT_MISSING = OUT_DIR / "307a_missing_intake_core_metrics.xlsx"
OUT_REVIEW_REQ = OUT_DIR / "307a_review_required_core_metrics.xlsx"
OUT_CONFLICT = OUT_DIR / "307a_conflict_audit.xlsx"
OUT_COVERAGE = OUT_DIR / "307a_coverage_by_pdf_metric.xlsx"
OUT_QUALITY = OUT_DIR / "307a_export_quality_summary.xlsx"
OUT_NO_APPLY = OUT_DIR / "307a_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
FINAL_COLS = [
    "PDF文件名",
    "group_id",
    "candidate_id",
    "标准指标",
    "指标名",
    "年份",
    "value",
    "unit",
    "normalized_unit",
    "source_bucket",
    "review_status",
    "risk_level",
    "source_parser",
    "source_page",
    "evidence_note",
]
BUCKET_PRIORITY = {"manual_reviewed": 3, "human_missing_intake": 2, "auto_accept_v2": 1}


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


def _extract_page_from_row_uid(row_uid: str) -> str:
    s = _norm(row_uid)
    if s == "":
        return ""
    parts = s.split("|")
    if len(parts) >= 2 and parts[1].isdigit():
        return parts[1]
    return ""


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in FINAL_COLS:
        if c not in out.columns:
            out[c] = ""
    out["年份"] = out["年份"].map(_to_int)
    out["candidate_id"] = out["candidate_id"].map(_norm)
    out["group_id"] = out["group_id"].map(_norm)
    out["PDF文件名"] = out["PDF文件名"].map(_norm)
    out["标准指标"] = out["标准指标"].map(_norm)
    out["指标名"] = out["指标名"].map(_norm)
    out["source_bucket"] = out["source_bucket"].map(_norm)
    out["source_key"] = out["PDF文件名"] + "|" + out["标准指标"] + "|" + out["年份"].astype(str)
    out["source_key_bucket"] = out["source_key"] + "|" + out["source_bucket"]
    return out[FINAL_COLS + ["source_key", "source_key_bucket"]]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_Z_AUTO, IN_Z_REVIEW, IN_S_PROJ, IN_T_VALID, IN_Q_POOL, IN_L_MAP]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307A",
                "mode": "core_metric_final_export_preview",
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

    z_auto = _drop_note_rows(_load_first_sheet(IN_Z_AUTO, "auto_accept_candidate_preview_v2"))
    z_review = _drop_note_rows(_load_first_sheet(IN_Z_REVIEW, "review_required_v2"))
    s_proj = _drop_note_rows(_load_first_sheet(IN_S_PROJ, "unit_normalized_projection"))
    t_valid = _drop_note_rows(_load_first_sheet(IN_T_VALID, "valid_missing_candidate_intake"))
    q_pool = _drop_note_rows(_load_first_sheet(IN_Q_POOL, "reviewed_candidate_pool"))
    l_map = _drop_note_rows(_load_first_sheet(IN_L_MAP, "group_to_candidate_manifest"))

    # map candidate -> row_uid for page traceability
    l_map["candidate_id"] = l_map["candidate_id"].map(_norm)
    cand_page = (
        l_map.assign(source_page=l_map["row_uid"].map(_extract_page_from_row_uid))
        .groupby("candidate_id", dropna=False)["source_page"]
        .apply(lambda s: "|".join(sorted({_norm(v) for v in s.tolist() if _norm(v) != ""})))
        .to_dict()
    )

    # auto_accept_v2 bucket
    auto_rows = pd.DataFrame()
    if not z_auto.empty:
        auto_rows = pd.DataFrame(
            {
                "PDF文件名": z_auto["PDF文件名"].map(_norm),
                "group_id": z_auto.get("group_id", "").map(_norm),
                "candidate_id": z_auto.get("candidate_id", "").map(_norm),
                "标准指标": z_auto["标准指标"].map(_norm),
                "指标名": z_auto["标准指标"].map(_norm),
                "年份": z_auto["年份"].map(_to_int),
                "value": z_auto.get("value_raw", "").map(_norm),
                "unit": "",
                "normalized_unit": "",
                "source_bucket": "auto_accept_v2",
                "review_status": "auto_accepted_v2",
                "risk_level": "LOW",
                "source_parser": "",
                "source_page": z_auto.get("candidate_id", "").map(lambda x: cand_page.get(_norm(x), "")),
                "evidence_note": "from 306z auto_accept_candidate_preview_v2",
            }
        )

    # manual reviewed normalized projection bucket
    manual_rows = pd.DataFrame()
    if not s_proj.empty:
        manual_rows = pd.DataFrame(
            {
                "PDF文件名": s_proj["PDF文件名"].map(_norm),
                "group_id": s_proj.get("group_id", "").map(_norm),
                "candidate_id": s_proj.get("candidate_id", "").map(_norm),
                "标准指标": s_proj["标准指标"].map(_norm),
                "指标名": s_proj["标准指标"].map(_norm),
                "年份": s_proj["年份"].map(_to_int),
                "value": s_proj.get("effective_value", "").map(_norm),
                "unit": s_proj.get("effective_unit", "").map(_norm),
                "normalized_unit": s_proj.get("normalized_unit", "").map(_norm),
                "source_bucket": "manual_reviewed",
                "review_status": s_proj.get("decision_candidate", "").map(_norm),
                "risk_level": s_proj.get("unit_warning", "").map(lambda x: "MEDIUM" if _norm(x) != "" else "LOW"),
                "source_parser": s_proj.get("来源解析器", "").map(_norm),
                "source_page": s_proj.get("candidate_id", "").map(lambda x: cand_page.get(_norm(x), "")),
                "evidence_note": "from 306s unit_normalized_projection",
            }
        )

    # valid missing intake bucket (no fake candidate_id)
    missing_rows = pd.DataFrame()
    fake_candidate_id_generated_count = 0
    if not t_valid.empty:
        missing_rows = pd.DataFrame(
            {
                "PDF文件名": t_valid["PDF文件名"].map(_norm),
                "group_id": t_valid.get("group_id", "").map(_norm),
                "candidate_id": t_valid.get("candidate_id", "").map(_norm),
                "标准指标": t_valid["标准指标"].map(_norm),
                "指标名": t_valid["标准指标"].map(_norm),
                "年份": t_valid["年份"].map(_to_int),
                "value": t_valid.get("effective_value", "").map(_norm),
                "unit": t_valid.get("effective_unit", "").map(_norm),
                "normalized_unit": t_valid.get("normalized_unit", "").map(_norm),
                "source_bucket": "human_missing_intake",
                "review_status": t_valid.get("validation_status", "").map(_norm),
                "risk_level": t_valid.get("unit_warning", "").map(lambda x: "MEDIUM" if _norm(x) != "" else "LOW"),
                "source_parser": t_valid.get("来源解析器", "").map(_norm),
                "source_page": "",
                "evidence_note": "from 306t valid_missing_candidate_intake",
            }
        )
        # guard: missing intake should not have fake candidate id; allow empty candidate_id.
        # if candidate_id starts with a fabricated marker (not observed), count as fake.
        fake_candidate_id_generated_count = int(
            missing_rows["candidate_id"].map(_norm).map(lambda x: x.startswith("FAKE_") or x.startswith("fake_")).sum()
        )

    # review required separate
    review_required_rows = pd.DataFrame()
    if not z_review.empty:
        review_required_rows = pd.DataFrame(
            {
                "PDF文件名": z_review["PDF文件名"].map(_norm),
                "group_id": z_review.get("group_id", "").map(_norm),
                "candidate_id": z_review.get("candidate_id", "").map(_norm),
                "标准指标": z_review["标准指标"].map(_norm),
                "指标名": z_review["标准指标"].map(_norm),
                "年份": z_review["年份"].map(_to_int),
                "value": z_review.get("value_raw", "").map(_norm),
                "unit": "",
                "normalized_unit": "",
                "source_bucket": "review_required",
                "review_status": "review_required_v2",
                "risk_level": "HIGH",
                "source_parser": "",
                "source_page": z_review.get("candidate_id", "").map(lambda x: cand_page.get(_norm(x), "")),
                "evidence_note": "from 306z review_required_v2",
            }
        )

    auto_rows = _normalize_frame(auto_rows) if not auto_rows.empty else pd.DataFrame(columns=FINAL_COLS + ["source_key", "source_key_bucket"])
    manual_rows = _normalize_frame(manual_rows) if not manual_rows.empty else pd.DataFrame(columns=FINAL_COLS + ["source_key", "source_key_bucket"])
    missing_rows = _normalize_frame(missing_rows) if not missing_rows.empty else pd.DataFrame(columns=FINAL_COLS + ["source_key", "source_key_bucket"])
    review_required_rows = _normalize_frame(review_required_rows) if not review_required_rows.empty else pd.DataFrame(columns=FINAL_COLS + ["source_key", "source_key_bucket"])

    trusted_all = pd.concat([auto_rows, manual_rows, missing_rows], ignore_index=True)

    # dedupe inside each source bucket first by PDF+metric+year+source_bucket
    trusted_all = trusted_all.sort_values(["PDF文件名", "标准指标", "年份", "source_bucket"]).drop_duplicates(
        subset=["source_key_bucket"], keep="first"
    )

    # conflicts across trusted buckets for same key (value/unit/normalized_unit differences)
    conflict_rows: List[Dict[str, Any]] = []
    final_rows: List[pd.Series] = []
    for key, g in trusted_all.groupby("source_key", dropna=False):
        g2 = g.copy()
        g2["bucket_priority"] = g2["source_bucket"].map(lambda x: BUCKET_PRIORITY.get(_norm(x), 0))
        values = sorted({_norm(v) for v in g2["value"].tolist() if _norm(v) != ""})
        units = sorted({_norm(v) for v in g2["normalized_unit"].tolist() if _norm(v) != ""})
        # if conflicting values for same key across buckets, keep highest priority and log conflict
        if len(values) > 1:
            top = g2.sort_values("bucket_priority", ascending=False).iloc[0]
            for _, r in g2.iterrows():
                conflict_rows.append(
                    {
                        "source_key": key,
                        "PDF文件名": _norm(r["PDF文件名"]),
                        "标准指标": _norm(r["标准指标"]),
                        "年份": _to_int(r["年份"]),
                        "source_bucket": _norm(r["source_bucket"]),
                        "value": _norm(r["value"]),
                        "unit": _norm(r["unit"]),
                        "normalized_unit": _norm(r["normalized_unit"]),
                        "conflict_type": "value_conflict_across_trusted_buckets",
                        "selected_for_final": bool(r["source_bucket"] == top["source_bucket"]),
                    }
                )
            final_rows.append(top)
        else:
            top = g2.sort_values("bucket_priority", ascending=False).iloc[0]
            if len(units) > 1:
                for _, r in g2.iterrows():
                    conflict_rows.append(
                        {
                            "source_key": key,
                            "PDF文件名": _norm(r["PDF文件名"]),
                            "标准指标": _norm(r["标准指标"]),
                            "年份": _to_int(r["年份"]),
                            "source_bucket": _norm(r["source_bucket"]),
                            "value": _norm(r["value"]),
                            "unit": _norm(r["unit"]),
                            "normalized_unit": _norm(r["normalized_unit"]),
                            "conflict_type": "unit_conflict_across_trusted_buckets",
                            "selected_for_final": bool(r["source_bucket"] == top["source_bucket"]),
                        }
                    )
            final_rows.append(top)

    final_df = pd.DataFrame(final_rows).drop(columns=["bucket_priority"], errors="ignore")
    conflict_df = pd.DataFrame(conflict_rows)

    # final dedupe safety
    dup_final = (
        final_df.groupby("source_key", dropna=False).size().reset_index(name="count")
        if not final_df.empty
        else pd.DataFrame(columns=["source_key", "count"])
    )
    dup_final = dup_final[dup_final["count"] > 1].copy()
    duplicate_trusted_key_count_after_priority_resolution = int(len(dup_final))
    unresolved_conflict_count_for_final_preview = int(duplicate_trusted_key_count_after_priority_resolution)

    # coverage
    coverage_df = (
        final_df.groupby(["PDF文件名", "标准指标"], dropna=False)
        .agg(year_count=("年份", "nunique"), row_count=("source_key", "count"), source_buckets=("source_bucket", lambda x: "|".join(sorted(set(x)))))
        .reset_index()
        if not final_df.empty
        else pd.DataFrame(columns=["PDF文件名", "标准指标", "year_count", "row_count", "source_buckets"])
    )

    quality_summary_df = pd.DataFrame(
        [
            {"metric": "auto_accept_core_rows", "value": int(len(auto_rows))},
            {"metric": "manual_reviewed_core_rows", "value": int(len(manual_rows))},
            {"metric": "missing_intake_core_rows", "value": int(len(missing_rows))},
            {"metric": "trusted_combined_rows_before_priority", "value": int(len(trusted_all))},
            {"metric": "final_core_preview_rows", "value": int(len(final_df))},
            {"metric": "review_required_rows_separate", "value": int(len(review_required_rows))},
            {"metric": "conflict_audit_row_count", "value": int(len(conflict_df))},
            {"metric": "duplicate_trusted_key_count_after_priority_resolution", "value": duplicate_trusted_key_count_after_priority_resolution},
            {"metric": "unresolved_conflict_count_for_final_preview", "value": unresolved_conflict_count_for_final_preview},
        ]
    )

    # output excel files
    _write_excel(OUT_FINAL, {"final_core_metric_preview": final_df[FINAL_COLS] if not final_df.empty else pd.DataFrame(columns=FINAL_COLS)})
    _write_excel(OUT_AUTO, {"auto_accept_core_metrics": auto_rows[FINAL_COLS] if not auto_rows.empty else pd.DataFrame(columns=FINAL_COLS)})
    _write_excel(OUT_MANUAL, {"manual_reviewed_core_metrics": manual_rows[FINAL_COLS] if not manual_rows.empty else pd.DataFrame(columns=FINAL_COLS)})
    _write_excel(OUT_MISSING, {"missing_intake_core_metrics": missing_rows[FINAL_COLS] if not missing_rows.empty else pd.DataFrame(columns=FINAL_COLS)})
    _write_excel(OUT_REVIEW_REQ, {"review_required_core_metrics": review_required_rows[FINAL_COLS] if not review_required_rows.empty else pd.DataFrame(columns=FINAL_COLS)})
    _write_excel(
        OUT_CONFLICT,
        {
            "conflict_audit": conflict_df if not conflict_df.empty else pd.DataFrame([{"note": "no_conflict_rows"}]),
            "duplicate_after_priority": dup_final if not dup_final.empty else pd.DataFrame([{"note": "duplicate_trusted_key_count_0"}]),
        },
    )
    _write_excel(OUT_COVERAGE, {"coverage_by_pdf_metric": coverage_df})
    _write_excel(OUT_QUALITY, {"export_quality_summary": quality_summary_df})

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

    forbidden_fields_generated = sorted([c for c in set(final_df.columns).union(set(review_required_rows.columns)) if c in FORBIDDEN_FIELDS])

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307A",
        "mode": "core_metric_final_export_preview",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "auto_accept_core_rows": int(len(auto_rows)),
        "manual_reviewed_core_rows": int(len(manual_rows)),
        "missing_intake_core_rows": int(len(missing_rows)),
        "final_core_preview_rows": int(len(final_df)),
        "review_required_rows_separate": int(len(review_required_rows)),
        "fake_candidate_id_generated_count": int(fake_candidate_id_generated_count),
        "duplicate_trusted_key_count_after_priority_resolution": int(duplicate_trusted_key_count_after_priority_resolution),
        "unresolved_conflict_count_for_final_preview": int(unresolved_conflict_count_for_final_preview),
        "review_required_rows_remain_separate": True,
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
        "# 307A Core Metric Final Export Preview",
        "",
        "## Trusted Buckets",
        f"- auto_accept_core_rows: {summary['auto_accept_core_rows']}",
        f"- manual_reviewed_core_rows: {summary['manual_reviewed_core_rows']}",
        f"- missing_intake_core_rows: {summary['missing_intake_core_rows']}",
        f"- final_core_preview_rows: {summary['final_core_preview_rows']}",
        "",
        "## Quality Assertions",
        f"- fake_candidate_id_generated_count: {summary['fake_candidate_id_generated_count']}",
        f"- duplicate_trusted_key_count_after_priority_resolution: {summary['duplicate_trusted_key_count_after_priority_resolution']}",
        f"- unresolved_conflict_count_for_final_preview: {summary['unresolved_conflict_count_for_final_preview']}",
        f"- review_required_rows_remain_separate: {summary['review_required_rows_remain_separate']}",
        "",
        "## Guard",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_307a_summary_json: {OUT_SUMMARY}")
    print(f"eval_307a_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
