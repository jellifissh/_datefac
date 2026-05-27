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
OUT_DIR = BASE_DIR / "output" / "eval_307f_expand_eps_review_to_candidate_results"

IN_VALID = BASE_DIR / "output" / "eval_307e_eps_focused_review_input_validation" / "307e_valid_eps_review_results.xlsx"
IN_MAP = BASE_DIR / "output" / "eval_307d_eps_focused_human_review_package" / "307d_eps_group_to_candidate_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "307f_summary.json"
OUT_REPORT = OUT_DIR / "307f_report.md"
OUT_ALL = OUT_DIR / "307f_eps_candidate_review_results.xlsx"
OUT_CORR = OUT_DIR / "307f_eps_corrected_candidate_results.xlsx"
OUT_APPR = OUT_DIR / "307f_eps_approved_candidate_results.xlsx"
OUT_REJ = OUT_DIR / "307f_eps_rejected_candidate_results.xlsx"
OUT_NEED = OUT_DIR / "307f_eps_needs_more_info_candidate_results.xlsx"
OUT_MISS = OUT_DIR / "307f_eps_human_discovered_missing_candidates.xlsx"
OUT_AUDIT = OUT_DIR / "307f_eps_review_expansion_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "307f_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
YEAR_COLS = [str(y) for y in range(2020, 2031)]
CORR_COLS = [f"corrected_{y}" for y in YEAR_COLS]


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

    required = [IN_VALID, IN_MAP]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307F",
                "mode": "expand_eps_review_to_candidate_results",
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

    valid = _load_first_sheet(IN_VALID, "valid_eps_review_results").fillna("")
    manifest = _load_first_sheet(IN_MAP, "eps_group_to_candidate_manifest").fillna("")

    valid["group_id"] = valid["group_id"].map(_norm)
    manifest["group_id"] = manifest["group_id"].map(_norm)
    manifest["candidate_id"] = manifest["candidate_id"].map(_norm)
    manifest["年份"] = manifest["年份"].map(_to_int)
    manifest["数值"] = manifest["数值"].map(_norm)

    expanded_rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []

    manifest_candidate_ids = set(manifest["candidate_id"].tolist())

    for _, r in valid.iterrows():
        gid = _norm(r.get("group_id", ""))
        decision = _norm(r.get("decision", ""))
        reviewer_id = _norm(r.get("reviewer_id", ""))
        reviewed_at = _norm(r.get("reviewed_at", ""))
        review_comment = _norm(r.get("review_comment", ""))
        corrected_unit = _norm(r.get("corrected_unit", ""))
        extra_info_request = _norm(r.get("extra_info_request", ""))

        gm = manifest[manifest["group_id"] == gid].copy()
        gm["year_str"] = gm["年份"].astype(str)
        mapped_years = set(gm["年份"].tolist())

        corrected_map: Dict[int, str] = {}
        for y in YEAR_COLS:
            cv = _norm(r.get(f"corrected_{y}", ""))
            if cv != "":
                corrected_map[int(y)] = cv

        if decision == "approve_eps_series":
            for _, mr in gm.iterrows():
                expanded_rows.append(
                    {
                        "group_id": gid,
                        "candidate_id": _norm(mr["candidate_id"]),
                        "PDF文件名": _norm(mr["PDF文件名"]),
                        "标准指标": _norm(mr["标准指标"]),
                        "年份": _to_int(mr["年份"]),
                        "original_value": _norm(mr["数值"]),
                        "decision_group": decision,
                        "decision_candidate": "approve_eps",
                        "reviewer_id": reviewer_id,
                        "reviewed_at": reviewed_at,
                        "review_comment": review_comment,
                        "extra_info_request": extra_info_request,
                        "corrected_value": "",
                        "corrected_unit": "",
                    }
                )
        elif decision == "reject_eps_series":
            for _, mr in gm.iterrows():
                expanded_rows.append(
                    {
                        "group_id": gid,
                        "candidate_id": _norm(mr["candidate_id"]),
                        "PDF文件名": _norm(mr["PDF文件名"]),
                        "标准指标": _norm(mr["标准指标"]),
                        "年份": _to_int(mr["年份"]),
                        "original_value": _norm(mr["数值"]),
                        "decision_group": decision,
                        "decision_candidate": "reject_eps",
                        "reviewer_id": reviewer_id,
                        "reviewed_at": reviewed_at,
                        "review_comment": review_comment,
                        "extra_info_request": extra_info_request,
                        "corrected_value": "",
                        "corrected_unit": "",
                    }
                )
        elif decision == "needs_more_info":
            for _, mr in gm.iterrows():
                expanded_rows.append(
                    {
                        "group_id": gid,
                        "candidate_id": _norm(mr["candidate_id"]),
                        "PDF文件名": _norm(mr["PDF文件名"]),
                        "标准指标": _norm(mr["标准指标"]),
                        "年份": _to_int(mr["年份"]),
                        "original_value": _norm(mr["数值"]),
                        "decision_group": decision,
                        "decision_candidate": "needs_more_info",
                        "reviewer_id": reviewer_id,
                        "reviewed_at": reviewed_at,
                        "review_comment": review_comment,
                        "extra_info_request": extra_info_request,
                        "corrected_value": "",
                        "corrected_unit": "",
                    }
                )
        elif decision == "correct_eps_series":
            # existing mapped candidates
            for _, mr in gm.iterrows():
                y = _to_int(mr["年份"])
                has_correct = y in corrected_map
                expanded_rows.append(
                    {
                        "group_id": gid,
                        "candidate_id": _norm(mr["candidate_id"]),
                        "PDF文件名": _norm(mr["PDF文件名"]),
                        "标准指标": _norm(mr["标准指标"]),
                        "年份": y,
                        "original_value": _norm(mr["数值"]),
                        "decision_group": decision,
                        "decision_candidate": "correct_value" if has_correct else "approve_eps",
                        "reviewer_id": reviewer_id,
                        "reviewed_at": reviewed_at,
                        "review_comment": review_comment,
                        "extra_info_request": extra_info_request,
                        "corrected_value": corrected_map.get(y, ""),
                        "corrected_unit": corrected_unit if has_correct else "",
                    }
                )

            # corrected years not in mapped set => missing candidate intake
            for y, cv in corrected_map.items():
                if y not in mapped_years:
                    missing_rows.append(
                        {
                            "group_id": gid,
                            "candidate_id": "",
                            "missing_candidate_marker": "eps_human_discovered_missing_candidate",
                            "PDF文件名": _norm(r.get("PDF文件名", "")),
                            "标准指标": "eps",
                            "年份": y,
                            "original_value": "",
                            "decision_group": decision,
                            "decision_candidate": "eps_human_discovered_missing_candidate",
                            "reviewer_id": reviewer_id,
                            "reviewed_at": reviewed_at,
                            "review_comment": review_comment,
                            "extra_info_request": extra_info_request,
                            "corrected_value": cv,
                            "corrected_unit": corrected_unit,
                        }
                    )

        audit_rows.append(
            {
                "group_id": gid,
                "decision_group": decision,
                "mapped_candidate_count": int(len(gm)),
                "corrected_year_count": int(len(corrected_map)),
                "corrected_year_missing_candidate_count": int(sum(1 for y in corrected_map if y not in mapped_years)),
            }
        )

    expanded_df = pd.DataFrame(expanded_rows)
    missing_df = pd.DataFrame(missing_rows)
    audit_df = pd.DataFrame(audit_rows)

    # split buckets
    corrected_df = expanded_df[expanded_df["decision_candidate"] == "correct_value"].copy() if not expanded_df.empty else pd.DataFrame()
    approved_df = expanded_df[expanded_df["decision_candidate"] == "approve_eps"].copy() if not expanded_df.empty else pd.DataFrame()
    rejected_df = expanded_df[expanded_df["decision_candidate"] == "reject_eps"].copy() if not expanded_df.empty else pd.DataFrame()
    needs_df = expanded_df[expanded_df["decision_candidate"] == "needs_more_info"].copy() if not expanded_df.empty else pd.DataFrame()

    fake_candidate_id_generated_count = int(
        expanded_df["candidate_id"].map(_norm).map(lambda x: x.startswith("FAKE_") or x.startswith("fake_")).sum()
    ) if not expanded_df.empty else 0

    existing_expanded_candidate_ids = set(expanded_df["candidate_id"].map(_norm).tolist()) if not expanded_df.empty else set()
    existing_expanded_candidate_ids = {x for x in existing_expanded_candidate_ids if x != ""}
    every_existing_candidate_in_manifest = existing_expanded_candidate_ids.issubset(manifest_candidate_ids)

    corrected_missing_only_in_missing_table = True
    if not expanded_df.empty:
        # corrected rows in expanded should all have candidate_id
        corrected_without_candidate = corrected_df[corrected_df["candidate_id"].map(_norm) == ""]
        corrected_missing_only_in_missing_table = corrected_without_candidate.empty

    _write_excel(OUT_ALL, {"eps_candidate_review_results": expanded_df if not expanded_df.empty else pd.DataFrame([{"note": "no_expanded_rows"}])})
    _write_excel(OUT_CORR, {"eps_corrected_candidate_results": corrected_df if not corrected_df.empty else pd.DataFrame([{"note": "no_corrected_rows"}])})
    _write_excel(OUT_APPR, {"eps_approved_candidate_results": approved_df if not approved_df.empty else pd.DataFrame([{"note": "no_approved_rows"}])})
    _write_excel(OUT_REJ, {"eps_rejected_candidate_results": rejected_df if not rejected_df.empty else pd.DataFrame([{"note": "no_rejected_rows"}])})
    _write_excel(OUT_NEED, {"eps_needs_more_info_candidate_results": needs_df if not needs_df.empty else pd.DataFrame([{"note": "no_needs_more_info_rows"}])})
    _write_excel(OUT_MISS, {"eps_human_discovered_missing_candidates": missing_df if not missing_df.empty else pd.DataFrame([{"note": "no_missing_candidates"}])})
    _write_excel(OUT_AUDIT, {"eps_review_expansion_audit": audit_df if not audit_df.empty else pd.DataFrame([{"note": "no_audit_rows"}])})

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

    forbidden_fields_generated = sorted([c for c in set(expanded_df.columns).union(set(missing_df.columns)) if c in FORBIDDEN_FIELDS])

    expanded_group_count = int(valid["group_id"].map(_norm).nunique())
    expanded_existing_candidate_review_count = int(len(expanded_df))
    approved_corrected_rejected_needs_count_sum = int(len(approved_df) + len(corrected_df) + len(rejected_df) + len(needs_df))

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307F",
        "mode": "expand_eps_review_to_candidate_results",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "expanded_eps_review_group_count": expanded_group_count,
        "expanded_existing_candidate_review_count": expanded_existing_candidate_review_count,
        "approved_eps_count": int(len(approved_df)),
        "corrected_eps_count": int(len(corrected_df)),
        "rejected_eps_count": int(len(rejected_df)),
        "needs_more_info_count": int(len(needs_df)),
        "eps_human_discovered_missing_candidate_count": int(len(missing_df)),
        "approved_corrected_rejected_needs_count_sum": approved_corrected_rejected_needs_count_sum,
        "every_existing_expanded_candidate_id_exists_in_manifest": bool(every_existing_candidate_in_manifest),
        "fake_candidate_id_generated_count": int(fake_candidate_id_generated_count),
        "corrected_missing_years_only_in_missing_candidates_table": bool(corrected_missing_only_in_missing_table),
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
        "# 307F Expand EPS Review To Candidate Results",
        "",
        "## Expansion Overview",
        f"- expanded_eps_review_group_count: {summary['expanded_eps_review_group_count']}",
        f"- expanded_existing_candidate_review_count: {summary['expanded_existing_candidate_review_count']}",
        f"- approved_eps_count: {summary['approved_eps_count']}",
        f"- corrected_eps_count: {summary['corrected_eps_count']}",
        f"- rejected_eps_count: {summary['rejected_eps_count']}",
        f"- needs_more_info_count: {summary['needs_more_info_count']}",
        f"- eps_human_discovered_missing_candidate_count: {summary['eps_human_discovered_missing_candidate_count']}",
        "",
        "## Assertions",
        f"- every_existing_expanded_candidate_id_exists_in_manifest: {summary['every_existing_expanded_candidate_id_exists_in_manifest']}",
        f"- fake_candidate_id_generated_count: {summary['fake_candidate_id_generated_count']}",
        f"- corrected_missing_years_only_in_missing_candidates_table: {summary['corrected_missing_years_only_in_missing_candidates_table']}",
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

    print(f"eval_307f_summary_json: {OUT_SUMMARY}")
    print(f"eval_307f_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
