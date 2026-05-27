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
OUT_DIR = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results"

IN_306N_SUMMARY = BASE_DIR / "output" / "eval_306n_grouped_human_review_input_validation" / "306n_summary.json"
IN_306N_VALID = BASE_DIR / "output" / "eval_306n_grouped_human_review_input_validation" / "306n_valid_group_review_results.xlsx"
IN_306M_G2C = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_to_candidate_manifest.xlsx"
IN_306M_GMAN = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design" / "306m_group_id_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "306o_summary.json"
OUT_REPORT = OUT_DIR / "306o_report.md"
OUT_CANDIDATE = OUT_DIR / "306o_candidate_review_results.xlsx"
OUT_CORRECTED = OUT_DIR / "306o_corrected_candidate_results.xlsx"
OUT_REJECTED = OUT_DIR / "306o_rejected_candidate_results.xlsx"
OUT_NEEDS_INFO = OUT_DIR / "306o_needs_more_info_candidate_results.xlsx"
OUT_MISSING = OUT_DIR / "306o_human_discovered_missing_candidates.xlsx"
OUT_AUDIT = OUT_DIR / "306o_group_review_expansion_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "306o_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

YEAR_COLS = [str(y) for y in range(2020, 2031)]
CORRECTED_YEAR_COLS = [f"corrected_{y}" for y in range(2020, 2031)]
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


def _to_bool(v: Any) -> bool:
    s = _norm(v).lower()
    return s in {"true", "1", "yes"}


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


def _corrected_year_values(group_row: pd.Series) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for yc in CORRECTED_YEAR_COLS:
        val = _norm(group_row.get(yc, ""))
        if val != "":
            year = _to_int(yc.replace("corrected_", ""))
            out[year] = val
    return out


def _build_candidate_row(
    group_row: pd.Series,
    map_row: pd.Series,
    decision_expanded: str,
    corrected_value: str = "",
    corrected_unit: str = "",
) -> Dict[str, Any]:
    return {
        "group_id": _norm(group_row.get("group_id", "")),
        "candidate_id": _norm(map_row.get("candidate_id", "")),
        "row_uid": _norm(map_row.get("row_uid", "")),
        "PDF文件名": _norm(map_row.get("PDF文件名", group_row.get("PDF文件名", ""))),
        "标准指标": _norm(map_row.get("标准指标", group_row.get("标准指标", ""))),
        "年份": _to_int(map_row.get("年份", 0)),
        "原数值": _norm(map_row.get("数值", "")),
        "decision_group": _norm(group_row.get("decision", "")).lower(),
        "decision_candidate": decision_expanded,
        "reviewer_id": _norm(group_row.get("reviewer_id", "")),
        "reviewed_at": _norm(group_row.get("reviewed_at", "")),
        "review_comment": _norm(group_row.get("review_comment", "")),
        "extra_info_request": _norm(group_row.get("extra_info_request", "")),
        "corrected_value": corrected_value,
        "corrected_unit": corrected_unit,
        "source_panel_id": _norm(group_row.get("source_panel_id", "")),
        "来源解析器": _norm(group_row.get("来源解析器", "")),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306N_SUMMARY, IN_306N_VALID, IN_306M_G2C, IN_306M_GMAN]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306O",
                "mode": "expand_grouped_review_to_candidate_results",
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

    s_306n = json.loads(IN_306N_SUMMARY.read_text(encoding="utf-8"))
    valid_all = pd.read_excel(IN_306N_VALID).fillna("")
    g2c = pd.read_excel(IN_306M_G2C).fillna("")
    gman = pd.read_excel(IN_306M_GMAN).fillna("")

    # Keep only validated real review rows.
    valid = valid_all.copy()
    if "validation_status" in valid.columns:
        valid = valid[valid["validation_status"].map(_norm).str.upper().eq("VALID")].copy()
    if "input_source" in valid.columns:
        valid = valid[valid["input_source"].map(_norm).str.lower().eq("real")].copy()

    valid["group_id"] = valid["group_id"].map(_norm)
    g2c["group_id"] = g2c["group_id"].map(_norm)
    g2c["candidate_id"] = g2c["candidate_id"].map(_norm)
    g2c["年份_int"] = g2c["年份"].map(_to_int)
    gman["group_id"] = gman["group_id"].map(_norm)

    # For assertion reporting.
    expanded_group_count = int(valid["group_id"].nunique())
    valid_group_count_all = int(valid_all["group_id"].map(_norm).nunique()) if "group_id" in valid_all.columns else 0

    candidate_rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []

    for _, gr in valid.iterrows():
        gid = _norm(gr.get("group_id", ""))
        decision = _norm(gr.get("decision", "")).lower()
        corrected_unit = _norm(gr.get("corrected_unit", ""))
        corrected_map = _corrected_year_values(gr)

        mapped = g2c[g2c["group_id"] == gid].copy()
        mapped_years = set(mapped["年份_int"].tolist())
        missing_corrected_years = sorted([y for y in corrected_map.keys() if y not in mapped_years])

        created = 0
        created_correct = 0
        created_missing = 0

        if decision in {"approve_series", "reject_series", "needs_more_info"}:
            dmap = {
                "approve_series": "approve",
                "reject_series": "reject",
                "needs_more_info": "needs_more_info",
            }
            c_decision = dmap[decision]
            for _, mr in mapped.iterrows():
                candidate_rows.append(_build_candidate_row(gr, mr, c_decision))
                created += 1

        elif decision == "correct_series":
            for _, mr in mapped.iterrows():
                y = _to_int(mr.get("年份_int", 0))
                if y in corrected_map:
                    candidate_rows.append(
                        _build_candidate_row(
                            gr,
                            mr,
                            "correct_value",
                            corrected_value=corrected_map[y],
                            corrected_unit=corrected_unit,
                        )
                    )
                    created += 1
                    created_correct += 1
                else:
                    candidate_rows.append(_build_candidate_row(gr, mr, "approve"))
                    created += 1

            for y in missing_corrected_years:
                missing_rows.append(
                    {
                        "group_id": gid,
                        "candidate_id": "",
                        "missing_candidate_marker": "human_discovered_missing_candidate",
                        "PDF文件名": _norm(gr.get("PDF文件名", "")),
                        "标准指标": _norm(gr.get("标准指标", "")),
                        "年份": y,
                        "decision_group": decision,
                        "decision_candidate": "human_discovered_missing_candidate",
                        "reviewer_id": _norm(gr.get("reviewer_id", "")),
                        "reviewed_at": _norm(gr.get("reviewed_at", "")),
                        "review_comment": _norm(gr.get("review_comment", "")),
                        "extra_info_request": _norm(gr.get("extra_info_request", "")),
                        "corrected_value": corrected_map[y],
                        "corrected_unit": corrected_unit,
                        "source_panel_id": _norm(gr.get("source_panel_id", "")),
                        "来源解析器": _norm(gr.get("来源解析器", "")),
                    }
                )
                created_missing += 1
        else:
            # Unexpected decision should not happen for validated rows; keep audit only.
            pass

        audit_rows.append(
            {
                "group_id": gid,
                "decision_group": decision,
                "mapped_candidate_count": int(len(mapped)),
                "corrected_year_count": int(len(corrected_map)),
                "missing_corrected_year_count": int(len(missing_corrected_years)),
                "expanded_candidate_row_count": int(created),
                "expanded_correct_value_row_count": int(created_correct),
                "expanded_missing_candidate_row_count": int(created_missing),
            }
        )

    cand_df = pd.DataFrame(candidate_rows).fillna("")
    missing_df = pd.DataFrame(missing_rows).fillna("")
    audit_df = pd.DataFrame(audit_rows).fillna("")

    if cand_df.empty:
        cand_df = pd.DataFrame([{"note": "no_expanded_candidate_rows"}])
    if missing_df.empty:
        missing_df = pd.DataFrame([{"note": "no_human_discovered_missing_candidates"}])
    if audit_df.empty:
        audit_df = pd.DataFrame([{"note": "no_expansion_audit_rows"}])

    corrected_df = cand_df[cand_df["decision_candidate"].map(_norm).eq("correct_value")].copy() if "decision_candidate" in cand_df.columns else pd.DataFrame()
    rejected_df = cand_df[cand_df["decision_candidate"].map(_norm).eq("reject")].copy() if "decision_candidate" in cand_df.columns else pd.DataFrame()
    needs_df = cand_df[cand_df["decision_candidate"].map(_norm).eq("needs_more_info")].copy() if "decision_candidate" in cand_df.columns else pd.DataFrame()

    if corrected_df.empty:
        corrected_df = pd.DataFrame([{"note": "no_corrected_candidate_rows"}])
    if rejected_df.empty:
        rejected_df = pd.DataFrame([{"note": "no_rejected_candidate_rows"}])
    if needs_df.empty:
        needs_df = pd.DataFrame([{"note": "no_needs_more_info_candidate_rows"}])

    _write_excel(
        OUT_CANDIDATE,
        {
            "candidate_review_results": cand_df,
            "decision_distribution": (
                cand_df.groupby("decision_candidate", dropna=False).size().reset_index(name="row_count")
                if "decision_candidate" in cand_df.columns
                else pd.DataFrame([{"decision_candidate": "N/A", "row_count": 0}])
            ),
        },
    )
    _write_excel(OUT_CORRECTED, {"corrected_candidate_results": corrected_df})
    _write_excel(OUT_REJECTED, {"rejected_candidate_results": rejected_df})
    _write_excel(OUT_NEEDS_INFO, {"needs_more_info_candidate_results": needs_df})
    _write_excel(OUT_MISSING, {"human_discovered_missing_candidates": missing_df})
    _write_excel(
        OUT_AUDIT,
        {
            "group_expansion_audit": audit_df,
            "expanded_group_source_audit": pd.DataFrame(
                [
                    {
                        "valid_group_count_all_sources": valid_group_count_all,
                        "expanded_group_count_real_only": expanded_group_count,
                        "source_filter_note": "expanded_real_only_from_306n_valid",
                    }
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

    # Assertions
    cand_id_manifest_set = set(g2c["candidate_id"].map(_norm).tolist())
    expanded_existing_cids = set(cand_df["candidate_id"].map(_norm).tolist()) if "candidate_id" in cand_df.columns else set()
    expanded_existing_cids.discard("")

    existing_candidate_id_all_in_manifest = expanded_existing_cids.issubset(cand_id_manifest_set)
    fake_candidate_id_generated = any(
        (_norm(x) != "") and (_norm(x) not in cand_id_manifest_set)
        for x in (cand_df["candidate_id"].tolist() if "candidate_id" in cand_df.columns else [])
    )
    missing_rows_have_empty_candidate_id = bool(
        ("candidate_id" in missing_df.columns)
        and (missing_df["candidate_id"].map(_norm).eq("").all())
    )
    forbidden_field_generated = any(
        f in set(cand_df.columns).union(set(missing_df.columns)).union(set(audit_df.columns)) for f in FORBIDDEN_FIELDS
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
        "stage": "EVAL-306O",
        "mode": "expand_grouped_review_to_candidate_results",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "valid_group_count_all_sources": valid_group_count_all,
        "expanded_reviewed_group_count_real_only": expanded_group_count,
        "expanded_reviewed_group_count_equals_19": bool(expanded_group_count == 19),
        "expanded_candidate_row_count": int(len(candidate_rows)),
        "corrected_candidate_row_count": int((cand_df["decision_candidate"].map(_norm).eq("correct_value").sum()) if "decision_candidate" in cand_df.columns else 0),
        "rejected_candidate_row_count": int((cand_df["decision_candidate"].map(_norm).eq("reject").sum()) if "decision_candidate" in cand_df.columns else 0),
        "needs_more_info_candidate_row_count": int((cand_df["decision_candidate"].map(_norm).eq("needs_more_info").sum()) if "decision_candidate" in cand_df.columns else 0),
        "human_discovered_missing_candidate_row_count": int(len(missing_rows)),
        "existing_candidate_id_all_in_manifest": bool(existing_candidate_id_all_in_manifest),
        "fake_candidate_id_generated": bool(fake_candidate_id_generated),
        "missing_corrected_years_only_in_missing_sheet": bool(missing_rows_have_empty_candidate_id),
        "forbidden_field_generated": bool(forbidden_field_generated),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306O Expand Grouped Review To Candidate Results",
        "",
        "## Scope",
        "- Expanded only VALID + real grouped review rows from 306N.",
        "- Preserved candidate_id mapping from 306M group_to_candidate_manifest.",
        "- No Marker/pdfplumber rerun. No API/LLM/OCR. No apply.",
        "",
        "## Expansion Counts",
        f"- valid_group_count_all_sources: {summary['valid_group_count_all_sources']}",
        f"- expanded_reviewed_group_count_real_only: {summary['expanded_reviewed_group_count_real_only']}",
        f"- expanded_candidate_row_count: {summary['expanded_candidate_row_count']}",
        f"- corrected_candidate_row_count: {summary['corrected_candidate_row_count']}",
        f"- rejected_candidate_row_count: {summary['rejected_candidate_row_count']}",
        f"- needs_more_info_candidate_row_count: {summary['needs_more_info_candidate_row_count']}",
        f"- human_discovered_missing_candidate_row_count: {summary['human_discovered_missing_candidate_row_count']}",
        "",
        "## Assertions",
        f"- expanded_reviewed_group_count_equals_19: {summary['expanded_reviewed_group_count_equals_19']}",
        f"- existing_candidate_id_all_in_manifest: {summary['existing_candidate_id_all_in_manifest']}",
        f"- fake_candidate_id_generated: {summary['fake_candidate_id_generated']}",
        f"- missing_corrected_years_only_in_missing_sheet: {summary['missing_corrected_years_only_in_missing_sheet']}",
        f"- forbidden_field_generated: {summary['forbidden_field_generated']}",
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

    print(f"eval_306o_summary_json: {OUT_SUMMARY}")
    print(f"eval_306o_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

