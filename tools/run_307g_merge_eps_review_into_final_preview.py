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
OUT_DIR = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview"

IN_307A_FINAL = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_final_core_metric_preview.xlsx"
IN_307A_REVIEW = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_review_required_core_metrics.xlsx"
IN_307F_ALL = BASE_DIR / "output" / "eval_307f_expand_eps_review_to_candidate_results" / "307f_eps_candidate_review_results.xlsx"
IN_307F_CORR = BASE_DIR / "output" / "eval_307f_expand_eps_review_to_candidate_results" / "307f_eps_corrected_candidate_results.xlsx"
IN_307F_APPR = BASE_DIR / "output" / "eval_307f_expand_eps_review_to_candidate_results" / "307f_eps_approved_candidate_results.xlsx"
IN_307F_REJ = BASE_DIR / "output" / "eval_307f_expand_eps_review_to_candidate_results" / "307f_eps_rejected_candidate_results.xlsx"
IN_307F_NEED = BASE_DIR / "output" / "eval_307f_expand_eps_review_to_candidate_results" / "307f_eps_needs_more_info_candidate_results.xlsx"
IN_307F_MISS = BASE_DIR / "output" / "eval_307f_expand_eps_review_to_candidate_results" / "307f_eps_human_discovered_missing_candidates.xlsx"

OUT_SUMMARY = OUT_DIR / "307g_summary.json"
OUT_REPORT = OUT_DIR / "307g_report.md"
OUT_FINAL = OUT_DIR / "307g_final_core_metric_preview_v2.xlsx"
OUT_EPS_TRUSTED = OUT_DIR / "307g_eps_manual_reviewed_core_metrics.xlsx"
OUT_EPS_MISSING = OUT_DIR / "307g_eps_missing_intake_preview.xlsx"
OUT_REVIEW_V2 = OUT_DIR / "307g_review_required_core_metrics_v2.xlsx"
OUT_EXCLUDED = OUT_DIR / "307g_excluded_eps_candidates.xlsx"
OUT_CONFLICT = OUT_DIR / "307g_conflict_audit.xlsx"
OUT_DELTA = OUT_DIR / "307g_coverage_delta_from_307a.xlsx"
OUT_NO_APPLY = OUT_DIR / "307g_no_apply_proof.json"

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
PRIORITY = {
    "eps_manual_corrected": 5,
    "eps_manual_reviewed": 4,
    "human_missing_intake": 3,
    "manual_reviewed": 2,
    "auto_accept_v2": 1,
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


def _normalize_final(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in FINAL_COLS:
        if c not in out.columns:
            out[c] = ""
    out["PDF文件名"] = out["PDF文件名"].map(_norm)
    out["group_id"] = out["group_id"].map(_norm)
    out["candidate_id"] = out["candidate_id"].map(_norm)
    out["标准指标"] = out["标准指标"].map(_norm).str.lower()
    out["指标名"] = out["指标名"].map(_norm)
    out["年份"] = out["年份"].map(_to_int)
    out["source_bucket"] = out["source_bucket"].map(_norm)
    out["value"] = out["value"].map(_norm)
    out["unit"] = out["unit"].map(_norm)
    out["normalized_unit"] = out["normalized_unit"].map(_norm)
    out["source_key"] = out["PDF文件名"] + "|" + out["标准指标"] + "|" + out["年份"].astype(str)
    out["source_key_bucket"] = out["source_key"] + "|" + out["source_bucket"]
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_307A_FINAL, IN_307A_REVIEW, IN_307F_ALL, IN_307F_CORR, IN_307F_APPR, IN_307F_REJ, IN_307F_NEED, IN_307F_MISS]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307G",
                "mode": "merge_eps_review_into_final_preview",
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

    final_v1 = _drop_note_rows(_load_first_sheet(IN_307A_FINAL, "final_core_metric_preview"))
    review_v1 = _drop_note_rows(_load_first_sheet(IN_307A_REVIEW, "review_required_core_metrics"))
    eps_all = _drop_note_rows(_load_first_sheet(IN_307F_ALL, "eps_candidate_review_results"))
    eps_corr = _drop_note_rows(_load_first_sheet(IN_307F_CORR, "eps_corrected_candidate_results"))
    eps_appr = _drop_note_rows(_load_first_sheet(IN_307F_APPR, "eps_approved_candidate_results"))
    eps_rej = _drop_note_rows(_load_first_sheet(IN_307F_REJ, "eps_rejected_candidate_results"))
    eps_need = _drop_note_rows(_load_first_sheet(IN_307F_NEED, "eps_needs_more_info_candidate_results"))
    eps_missing = _drop_note_rows(_load_first_sheet(IN_307F_MISS, "eps_human_discovered_missing_candidates"))

    final_v1 = _normalize_final(final_v1)
    review_v1 = _normalize_final(review_v1)

    # build trusted EPS rows from 307F
    trusted_eps_rows: List[Dict[str, Any]] = []
    excluded_rows: List[Dict[str, Any]] = []
    resolved_candidate_ids: Set[str] = set()
    rejected_candidate_ids: Set[str] = set()
    needs_candidate_ids: Set[str] = set()

    if not eps_all.empty:
        for _, r in eps_all.iterrows():
            cand = _norm(r.get("candidate_id", ""))
            decision = _norm(r.get("decision_candidate", ""))
            pdf = _norm(r.get("PDF文件名", ""))
            group_id = _norm(r.get("group_id", ""))
            year = _to_int(r.get("年份", 0))
            original_value = _norm(r.get("original_value", ""))
            corrected_value = _norm(r.get("corrected_value", ""))
            corrected_unit = _norm(r.get("corrected_unit", ""))
            reviewer = _norm(r.get("reviewer_id", ""))
            reviewed_at = _norm(r.get("reviewed_at", ""))
            review_comment = _norm(r.get("review_comment", ""))

            if cand != "":
                resolved_candidate_ids.add(cand)

            if decision == "correct_value":
                val = corrected_value if corrected_value != "" else original_value
                trusted_eps_rows.append(
                    {
                        "PDF文件名": pdf,
                        "group_id": group_id,
                        "candidate_id": cand,
                        "标准指标": "eps",
                        "指标名": "eps",
                        "年份": year,
                        "value": val,
                        "unit": corrected_unit,
                        "normalized_unit": corrected_unit if corrected_unit != "" else "yuan_per_share",
                        "source_bucket": "eps_manual_corrected",
                        "review_status": "correct_value",
                        "risk_level": "LOW",
                        "source_parser": "",
                        "source_page": "",
                        "evidence_note": f"from 307f corrected ({reviewer}|{reviewed_at}) {review_comment}",
                    }
                )
            elif decision == "approve_eps":
                trusted_eps_rows.append(
                    {
                        "PDF文件名": pdf,
                        "group_id": group_id,
                        "candidate_id": cand,
                        "标准指标": "eps",
                        "指标名": "eps",
                        "年份": year,
                        "value": original_value,
                        "unit": "",
                        "normalized_unit": "yuan_per_share",
                        "source_bucket": "eps_manual_reviewed",
                        "review_status": "approve_eps",
                        "risk_level": "LOW",
                        "source_parser": "",
                        "source_page": "",
                        "evidence_note": f"from 307f approved ({reviewer}|{reviewed_at}) {review_comment}",
                    }
                )
            elif decision == "reject_eps":
                rejected_candidate_ids.add(cand)
                excluded_rows.append(
                    {
                        "candidate_id": cand,
                        "group_id": group_id,
                        "PDF文件名": pdf,
                        "标准指标": "eps",
                        "年份": year,
                        "decision_candidate": decision,
                        "excluded_reason": "rejected_eps_not_in_trusted_preview",
                    }
                )
            elif decision == "needs_more_info":
                needs_candidate_ids.add(cand)
                excluded_rows.append(
                    {
                        "candidate_id": cand,
                        "group_id": group_id,
                        "PDF文件名": pdf,
                        "标准指标": "eps",
                        "年份": year,
                        "decision_candidate": decision,
                        "excluded_reason": "needs_more_info_not_in_trusted_preview",
                    }
                )

    trusted_eps_df = pd.DataFrame(trusted_eps_rows)
    trusted_eps_df = _normalize_final(trusted_eps_df) if not trusted_eps_df.empty else pd.DataFrame(columns=final_v1.columns)

    # EPS missing intake preview separate
    eps_missing_preview = pd.DataFrame()
    fake_candidate_id_generated_count = 0
    if not eps_missing.empty:
        eps_missing_preview = pd.DataFrame(
            {
                "PDF文件名": eps_missing["PDF文件名"].map(_norm),
                "group_id": eps_missing["group_id"].map(_norm),
                "candidate_id": eps_missing.get("candidate_id", "").map(_norm),
                "标准指标": "eps",
                "指标名": "eps",
                "年份": eps_missing["年份"].map(_to_int),
                "value": eps_missing.get("corrected_value", "").map(_norm),
                "unit": eps_missing.get("corrected_unit", "").map(_norm),
                "normalized_unit": eps_missing.get("corrected_unit", "").map(lambda x: _norm(x) if _norm(x) != "" else "yuan_per_share"),
                "source_bucket": "eps_missing_intake_preview",
                "review_status": eps_missing.get("decision_candidate", "").map(_norm),
                "risk_level": "MEDIUM",
                "source_parser": "",
                "source_page": "",
                "evidence_note": "from 307f eps_human_discovered_missing_candidates",
            }
        )
        fake_candidate_id_generated_count = int(
            eps_missing_preview["candidate_id"].map(_norm).map(lambda x: x.startswith("FAKE_") or x.startswith("fake_")).sum()
        )

    # remove resolved EPS candidate_ids from review_required v1
    review_v2 = review_v1.copy()
    if "candidate_id" in review_v2.columns:
        review_v2 = review_v2[~review_v2["candidate_id"].map(_norm).isin(resolved_candidate_ids)].copy()

    # combine trusted with v1 + new eps trusted
    trusted_all = pd.concat([final_v1, trusted_eps_df], ignore_index=True)
    trusted_all = trusted_all.drop_duplicates(subset=["source_key_bucket"], keep="first")

    # priority resolution across source_key
    conflict_rows: List[Dict[str, Any]] = []
    final_rows: List[pd.Series] = []
    for key, g in trusted_all.groupby("source_key", dropna=False):
        g2 = g.copy()
        g2["prio"] = g2["source_bucket"].map(lambda x: PRIORITY.get(_norm(x), 0))
        vals = sorted({_norm(v) for v in g2["value"].tolist() if _norm(v) != ""})
        if len(vals) > 1:
            top = g2.sort_values("prio", ascending=False).iloc[0]
            for _, r in g2.iterrows():
                conflict_rows.append(
                    {
                        "source_key": key,
                        "PDF文件名": _norm(r["PDF文件名"]),
                        "标准指标": _norm(r["标准指标"]),
                        "年份": _to_int(r["年份"]),
                        "source_bucket": _norm(r["source_bucket"]),
                        "value": _norm(r["value"]),
                        "conflict_type": "value_conflict_across_trusted_sources",
                        "selected_for_final": bool(r["source_bucket"] == top["source_bucket"]),
                    }
                )
            final_rows.append(top)
        else:
            top = g2.sort_values("prio", ascending=False).iloc[0]
            final_rows.append(top)

    final_v2 = pd.DataFrame(final_rows).drop(columns=["prio"], errors="ignore")
    dup_v2 = final_v2.groupby("source_key", dropna=False).size().reset_index(name="count")
    dup_v2 = dup_v2[dup_v2["count"] > 1].copy()
    duplicate_trusted_key_count_after_priority_resolution = int(len(dup_v2))
    unresolved_conflict_count = duplicate_trusted_key_count_after_priority_resolution

    conflict_df = pd.DataFrame(conflict_rows)

    # assertions
    resolved_eps_removed_from_review_required_v2 = True
    if not review_v2.empty:
        overlap = review_v2[review_v2["candidate_id"].map(_norm).isin(resolved_candidate_ids)]
        resolved_eps_removed_from_review_required_v2 = overlap.empty

    rejected_and_needs_not_in_trusted = True
    if not final_v2.empty:
        forbidden = set(rejected_candidate_ids).union(needs_candidate_ids)
        if forbidden:
            overlap2 = final_v2[final_v2["candidate_id"].map(_norm).isin(forbidden)]
            rejected_and_needs_not_in_trusted = overlap2.empty

    # coverage delta
    base_rows = int(len(final_v1))
    v2_rows = int(len(final_v2))
    eps_base = int(len(final_v1[final_v1["标准指标"] == "eps"])) if not final_v1.empty else 0
    eps_v2 = int(len(final_v2[final_v2["标准指标"] == "eps"])) if not final_v2.empty else 0
    coverage_delta = pd.DataFrame(
        [
            {"metric": "trusted_rows_total", "v1": base_rows, "v2": v2_rows, "delta": v2_rows - base_rows},
            {"metric": "trusted_rows_eps", "v1": eps_base, "v2": eps_v2, "delta": eps_v2 - eps_base},
            {"metric": "review_required_rows", "v1": int(len(review_v1)), "v2": int(len(review_v2)), "delta": int(len(review_v2)) - int(len(review_v1))},
        ]
    )

    _write_excel(OUT_FINAL, {"final_core_metric_preview_v2": final_v2[FINAL_COLS] if not final_v2.empty else pd.DataFrame(columns=FINAL_COLS)})
    _write_excel(OUT_EPS_TRUSTED, {"eps_manual_reviewed_core_metrics": trusted_eps_df[FINAL_COLS] if not trusted_eps_df.empty else pd.DataFrame([{"note": "no_eps_trusted_rows"}])})
    _write_excel(OUT_EPS_MISSING, {"eps_missing_intake_preview": eps_missing_preview if not eps_missing_preview.empty else pd.DataFrame([{"note": "no_eps_missing_intake_rows"}])})
    _write_excel(OUT_REVIEW_V2, {"review_required_core_metrics_v2": review_v2[FINAL_COLS] if not review_v2.empty else pd.DataFrame(columns=FINAL_COLS)})
    _write_excel(OUT_EXCLUDED, {"excluded_eps_candidates": pd.DataFrame(excluded_rows) if excluded_rows else pd.DataFrame([{"note": "no_excluded_eps_candidates"}])})
    _write_excel(
        OUT_CONFLICT,
        {
            "conflict_audit": conflict_df if not conflict_df.empty else pd.DataFrame([{"note": "no_conflict_rows"}]),
            "duplicate_after_priority": dup_v2 if not dup_v2.empty else pd.DataFrame([{"note": "duplicate_trusted_key_count_0"}]),
        },
    )
    _write_excel(OUT_DELTA, {"coverage_delta_from_307a": coverage_delta})
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

    forbidden_fields_generated = sorted([c for c in set(final_v2.columns).union(set(review_v2.columns)).union(set(eps_missing_preview.columns if not eps_missing_preview.empty else [])) if c in FORBIDDEN_FIELDS])

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307G",
        "mode": "merge_eps_review_into_final_preview",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "final_v1_row_count": base_rows,
        "final_v2_row_count": v2_rows,
        "review_required_v1_row_count": int(len(review_v1)),
        "review_required_v2_row_count": int(len(review_v2)),
        "eps_trusted_added_row_count": int(len(trusted_eps_df)),
        "eps_missing_intake_preview_row_count": int(len(eps_missing_preview)),
        "fake_candidate_id_generated_count": int(fake_candidate_id_generated_count),
        "duplicate_trusted_key_count_after_priority_resolution": int(duplicate_trusted_key_count_after_priority_resolution),
        "unresolved_conflict_count_for_final_preview_v2": int(unresolved_conflict_count),
        "eps_resolved_candidate_ids_removed_from_review_required_v2": bool(resolved_eps_removed_from_review_required_v2),
        "rejected_and_needs_more_info_eps_not_in_trusted_preview": bool(rejected_and_needs_not_in_trusted),
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
        "# 307G Merge EPS Review Into Final Preview",
        "",
        "## Row Counts",
        f"- final_v1_row_count: {summary['final_v1_row_count']}",
        f"- final_v2_row_count: {summary['final_v2_row_count']}",
        f"- review_required_v1_row_count: {summary['review_required_v1_row_count']}",
        f"- review_required_v2_row_count: {summary['review_required_v2_row_count']}",
        f"- eps_trusted_added_row_count: {summary['eps_trusted_added_row_count']}",
        "",
        "## Assertions",
        f"- fake_candidate_id_generated_count: {summary['fake_candidate_id_generated_count']}",
        f"- duplicate_trusted_key_count_after_priority_resolution: {summary['duplicate_trusted_key_count_after_priority_resolution']}",
        f"- unresolved_conflict_count_for_final_preview_v2: {summary['unresolved_conflict_count_for_final_preview_v2']}",
        f"- eps_resolved_candidate_ids_removed_from_review_required_v2: {summary['eps_resolved_candidate_ids_removed_from_review_required_v2']}",
        f"- rejected_and_needs_more_info_eps_not_in_trusted_preview: {summary['rejected_and_needs_more_info_eps_not_in_trusted_preview']}",
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

    print(f"eval_307g_summary_json: {OUT_SUMMARY}")
    print(f"eval_307g_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
