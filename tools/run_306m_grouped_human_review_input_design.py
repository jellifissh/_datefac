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
OUT_DIR = BASE_DIR / "output" / "eval_306m_grouped_human_review_input_design"

IN_306L_FIX_SUMMARY = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_summary.json"
IN_306L_FIX_GROUPED = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_306L_FIX_MAP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_group_to_candidate_manifest.xlsx"
IN_306J_CAND_MANIFEST = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design" / "306j_candidate_id_manifest.xlsx"

OUT_SUMMARY = OUT_DIR / "306m_summary.json"
OUT_REPORT = OUT_DIR / "306m_report.md"
OUT_TEMPLATE = OUT_DIR / "306m_grouped_review_input_template.xlsx"
OUT_README = OUT_DIR / "306m_grouped_review_readme.md"
OUT_POLICY = OUT_DIR / "306m_grouped_review_validation_policy.json"
OUT_SAMPLE = OUT_DIR / "306m_sample_grouped_review_input.xlsx"
OUT_GROUP_MANIFEST = OUT_DIR / "306m_group_id_manifest.xlsx"
OUT_GROUP_TO_CAND = OUT_DIR / "306m_group_to_candidate_manifest.xlsx"
OUT_NO_APPLY = OUT_DIR / "306m_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

YEAR_COLS = [str(y) for y in range(2020, 2031)]
DECISIONS = ["approve_series", "reject_series", "needs_more_info", "correct_series"]
FORBIDDEN_COLUMNS = {"safe_to_apply", "approve_for_real_apply"}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306L_FIX_SUMMARY, IN_306L_FIX_GROUPED, IN_306L_FIX_MAP, IN_306J_CAND_MANIFEST]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306M",
                "mode": "grouped_human_review_input_design",
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

    s_306l_fix = json.loads(IN_306L_FIX_SUMMARY.read_text(encoding="utf-8"))
    grouped = pd.read_excel(IN_306L_FIX_GROUPED).fillna("")
    g2c = pd.read_excel(IN_306L_FIX_MAP).fillna("")
    cand_manifest = pd.read_excel(IN_306J_CAND_MANIFEST).fillna("")

    # Prepare grouped template.
    grouped = grouped.copy()
    grouped["group_id"] = grouped["group_id"].map(_norm)
    grouped = grouped.sort_values(["review_priority", "PDF文件名", "标准指标", "指标名", "source_panel_id"]).reset_index(drop=True)

    template_df = grouped.copy()
    template_df["decision"] = ""
    template_df["reviewer_id"] = ""
    template_df["reviewed_at"] = ""
    template_df["review_comment"] = ""
    template_df["extra_info_request"] = ""
    for yc in YEAR_COLS:
        template_df[f"corrected_{yc}"] = ""
    template_df["corrected_unit"] = ""

    # Do not include forbidden columns.
    for f in FORBIDDEN_COLUMNS:
        if f in template_df.columns:
            template_df = template_df.drop(columns=[f])

    # Build sample grouped input with all 4 decision types.
    sample_df = template_df.head(4).copy()
    if len(sample_df) >= 1:
        sample_df.loc[sample_df.index[0], "decision"] = "approve_series"
        sample_df.loc[sample_df.index[0], "reviewer_id"] = "reviewer_demo_01"
        sample_df.loc[sample_df.index[0], "reviewed_at"] = "2026-05-27T10:00:00+08:00"
        sample_df.loc[sample_df.index[0], "review_comment"] = "series value set reviewed and approved"
    if len(sample_df) >= 2:
        sample_df.loc[sample_df.index[1], "decision"] = "reject_series"
        sample_df.loc[sample_df.index[1], "reviewer_id"] = "reviewer_demo_02"
        sample_df.loc[sample_df.index[1], "reviewed_at"] = "2026-05-27T10:10:00+08:00"
        sample_df.loc[sample_df.index[1], "review_comment"] = "series appears mismatched with context"
    if len(sample_df) >= 3:
        sample_df.loc[sample_df.index[2], "decision"] = "needs_more_info"
        sample_df.loc[sample_df.index[2], "reviewer_id"] = "reviewer_demo_03"
        sample_df.loc[sample_df.index[2], "reviewed_at"] = "2026-05-27T10:20:00+08:00"
        sample_df.loc[sample_df.index[2], "extra_info_request"] = "need page snippet and unit evidence"
        sample_df.loc[sample_df.index[2], "review_comment"] = "insufficient supporting context"
    if len(sample_df) >= 4:
        sample_df.loc[sample_df.index[3], "decision"] = "correct_series"
        sample_df.loc[sample_df.index[3], "reviewer_id"] = "reviewer_demo_04"
        sample_df.loc[sample_df.index[3], "reviewed_at"] = "2026-05-27T10:30:00+08:00"
        sample_df.loc[sample_df.index[3], "corrected_2024"] = sample_df.loc[sample_df.index[3], "2024"]
        sample_df.loc[sample_df.index[3], "corrected_2025"] = sample_df.loc[sample_df.index[3], "2025"]
        sample_df.loc[sample_df.index[3], "corrected_unit"] = _norm(sample_df.loc[sample_df.index[3], "单位"]) or "unknown"
        sample_df.loc[sample_df.index[3], "review_comment"] = "corrected series values and/or unit"

    # Group manifest.
    group_manifest_cols = [
        "group_id",
        "PDF文件名",
        "标准指标",
        "指标名",
        "单位",
        "来源解析器",
        "source_panel_id",
        "years_present",
        "year_count",
        "candidate_count",
        "review_priority",
        "risk_reasons",
        "blocked_auto_accept",
    ]
    group_manifest = grouped[[c for c in group_manifest_cols if c in grouped.columns]].copy()

    # Keep mapping from 306L-fix as-is, with a light integrity check.
    g2c["group_id"] = g2c["group_id"].map(_norm)
    g2c["candidate_id"] = g2c["candidate_id"].map(_norm)
    cand_manifest["candidate_id"] = cand_manifest["candidate_id"].map(_norm)
    cand_id_set = set(cand_manifest["candidate_id"].tolist())
    map_id_set = set(g2c["candidate_id"].tolist())

    # Write Excel outputs.
    _write_excel(
        OUT_TEMPLATE,
        {
            "grouped_review_input_template": template_df,
            "decision_enum": pd.DataFrame({"decision": DECISIONS}),
        },
    )
    _write_excel(OUT_SAMPLE, {"sample_grouped_review_input": sample_df})
    _write_excel(OUT_GROUP_MANIFEST, {"group_id_manifest": group_manifest})
    _write_excel(OUT_GROUP_TO_CAND, {"group_to_candidate_manifest": g2c})

    # Validation policy/readme.
    policy = {
        "stage": "EVAL-306M",
        "decision_allowed_values": DECISIONS,
        "required_for_all_decisions": ["reviewer_id", "reviewed_at"],
        "rule_needs_more_info": {"decision": "needs_more_info", "required_fields": ["extra_info_request"]},
        "rule_correct_series": {
            "decision": "correct_series",
            "requires_any_of": [f"corrected_{y}" for y in YEAR_COLS] + ["corrected_unit"],
        },
        "forbidden_fields": sorted(FORBIDDEN_COLUMNS),
        "notes": [
            "Template is grouped series-level review input only.",
            "No safe_to_apply or approve_for_real_apply field is included.",
            "Group-to-candidate mapping is preserved for downstream expansion.",
        ],
    }
    _write_json(OUT_POLICY, policy)

    readme_lines = [
        "# 306M Grouped Human Review Input Template",
        "",
        "## Purpose",
        "- Review one metric series (group) at a time instead of one metric-year row.",
        "",
        "## Allowed decisions",
        "- approve_series",
        "- reject_series",
        "- needs_more_info",
        "- correct_series",
        "",
        "## Required fields",
        "- All decisions: reviewer_id, reviewed_at",
        "- needs_more_info: extra_info_request",
        "- correct_series: at least one corrected_YYYY or corrected_unit",
        "",
        "## Forbidden fields",
        "- safe_to_apply",
        "- approve_for_real_apply",
        "",
        "## Files",
        f"- template: {OUT_TEMPLATE}",
        f"- sample: {OUT_SAMPLE}",
        f"- group manifest: {OUT_GROUP_MANIFEST}",
        f"- group to candidate mapping: {OUT_GROUP_TO_CAND}",
        "",
        "## Notes",
        "- Keep group_id unchanged to preserve downstream mapping.",
        "- group_to_candidate_manifest expands grouped decision back to candidate rows.",
    ]
    OUT_README.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

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

    forbidden_in_template = [c for c in template_df.columns if c in FORBIDDEN_COLUMNS]
    required_review_fields = ["decision", "reviewer_id", "reviewed_at", "review_comment", "extra_info_request", "corrected_unit"] + [
        f"corrected_{y}" for y in YEAR_COLS
    ]
    missing_required_review_fields = [c for c in required_review_fields if c not in template_df.columns]

    summary = {
        "stage": "EVAL-306M",
        "mode": "grouped_human_review_input_design",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "source_grouped_row_count_from_306l_fix": int(len(grouped)),
        "grouped_template_row_count": int(len(template_df)),
        "group_manifest_row_count": int(len(group_manifest)),
        "group_to_candidate_mapping_row_count": int(len(g2c)),
        "group_to_candidate_unique_candidate_count": int(g2c["candidate_id"].nunique()),
        "group_to_candidate_unique_group_count": int(g2c["group_id"].nunique()),
        "candidate_id_overlap_with_306j_manifest_all_true": bool(map_id_set.issubset(cand_id_set)),
        "mapping_preserved_from_306l_fix": bool(len(g2c) == int(s_306l_fix.get("group_to_candidate_mapping_row_count", len(g2c)))),
        "forbidden_fields_present_count": int(len(forbidden_in_template)),
        "missing_required_review_fields_count": int(len(missing_required_review_fields)),
        "sample_contains_all_4_decisions": bool(set(sample_df["decision"].map(_norm)) == set(DECISIONS) if len(sample_df) >= 4 else False),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306M Grouped Human Review Input Design",
        "",
        "## Scope",
        "- Built grouped human review template from 306L-Fix grouped outputs.",
        "- Preserved group-to-candidate mapping for downstream expansion.",
        "- No Marker/pdfplumber rerun. No API/LLM/OCR calls.",
        "",
        "## Output Counts",
        f"- source_grouped_row_count_from_306l_fix: {summary['source_grouped_row_count_from_306l_fix']}",
        f"- grouped_template_row_count: {summary['grouped_template_row_count']}",
        f"- group_manifest_row_count: {summary['group_manifest_row_count']}",
        f"- group_to_candidate_mapping_row_count: {summary['group_to_candidate_mapping_row_count']}",
        "",
        "## Validation Design",
        f"- allowed decisions: {', '.join(DECISIONS)}",
        "- all decisions require reviewer_id + reviewed_at",
        "- needs_more_info requires extra_info_request",
        "- correct_series requires at least one corrected year value or corrected_unit",
        "",
        "## Guards",
        f"- forbidden_fields_present_count: {summary['forbidden_fields_present_count']}",
        f"- missing_required_review_fields_count: {summary['missing_required_review_fields_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306m_summary_json: {OUT_SUMMARY}")
    print(f"eval_306m_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

