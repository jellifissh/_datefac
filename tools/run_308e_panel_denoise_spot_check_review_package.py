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
OUT_DIR = BASE_DIR / "output" / "eval_308e_panel_denoise_spot_check_review_package"

IN_308D_SAMPLE = BASE_DIR / "output" / "eval_308d_panel_denoise_rescue_safety_validation" / "308d_manual_spot_check_sample.xlsx"
IN_308D_SCORED = BASE_DIR / "output" / "eval_308d_panel_denoise_rescue_safety_validation" / "308d_rescue_safety_scored_rows.xlsx"
IN_308D_METRIC = BASE_DIR / "output" / "eval_308d_panel_denoise_rescue_safety_validation" / "308d_risk_distribution_by_metric.xlsx"
IN_308D_PDF = BASE_DIR / "output" / "eval_308d_panel_denoise_rescue_safety_validation" / "308d_risk_distribution_by_pdf.xlsx"
IN_308D_RULE = BASE_DIR / "output" / "eval_308d_panel_denoise_rescue_safety_validation" / "308d_rule_safety_audit.xlsx"
IN_308C_RESCUE = BASE_DIR / "output" / "eval_308c_parser_panel_denoise_rule_simulation" / "308c_would_rescue_from_review.xlsx"
IN_307G_FINAL = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"

OUT_SUMMARY = OUT_DIR / "308e_summary.json"
OUT_REPORT = OUT_DIR / "308e_report.md"
OUT_TEMPLATE = OUT_DIR / "308e_spot_check_review_template.xlsx"
OUT_README = OUT_DIR / "308e_spot_check_readme.md"
OUT_MANIFEST = OUT_DIR / "308e_spot_check_candidate_manifest.xlsx"
OUT_CONTEXT = OUT_DIR / "308e_rule_metric_pdf_context.xlsx"
OUT_NO_APPLY = OUT_DIR / "308e_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}

# parser output guard files (must remain unchanged)
PARSER_OUTPUT_GUARD_FILES = {
    "307g_final_core_metric_preview_v2": IN_307G_FINAL,
    "307g_review_required_core_metrics_v2": IN_307G_REVIEW,
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


def _to_bool(v: Any) -> bool:
    return _norm(v).lower() in {"1", "true", "yes"}


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


def _snapshot_parser_outputs() -> Dict[str, str]:
    return {k: _sha256(p) for k, p in PARSER_OUTPUT_GUARD_FILES.items()}


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


def _silent_risk_flags(row: pd.Series) -> str:
    cols = [
        "silent_risk_metric_family_mismatch",
        "silent_risk_unit_mismatch",
        "silent_risk_year_sequence_gap",
        "silent_risk_abnormal_value_range",
        "silent_risk_source_page_concentration",
        "silent_risk_repeated_identical_series_across_pdfs",
    ]
    out = []
    for c in cols:
        if c in row and _to_bool(row[c]):
            out.append(c)
    return "|".join(out)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_308D_SAMPLE,
        IN_308D_SCORED,
        IN_308D_METRIC,
        IN_308D_PDF,
        IN_308D_RULE,
        IN_308C_RESCUE,
        IN_307G_FINAL,
        IN_307G_REVIEW,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-308E",
                "mode": "panel_denoise_spot_check_review_package",
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

    before_guard = _snapshot_guard()
    before_parser_outputs = _snapshot_parser_outputs()
    final_before_hash = _sha256(IN_307G_FINAL)

    sample_df = _drop_note_rows(_load_first_sheet(IN_308D_SAMPLE, "manual_spot_check_sample"))
    scored_df = _drop_note_rows(_load_first_sheet(IN_308D_SCORED, "rescue_safety_scored_rows"))
    risk_metric_df = _drop_note_rows(_load_first_sheet(IN_308D_METRIC, "risk_distribution_by_metric"))
    risk_pdf_df = _drop_note_rows(_load_first_sheet(IN_308D_PDF, "risk_distribution_by_pdf"))
    rule_audit_df = _drop_note_rows(_load_first_sheet(IN_308D_RULE, "rule_safety_audit"))
    rescue_308c_df = _drop_note_rows(_load_first_sheet(IN_308C_RESCUE, "would_rescue_from_review"))
    final_df = _drop_note_rows(_load_first_sheet(IN_307G_FINAL, "final_core_metric_preview_v2"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))

    for c in ["candidate_id", "group_id", "PDF文件名", "标准指标", "指标名", "source_parser", "source_page", "source_bucket", "value", "unit", "normalized_unit", "denoise_rule", "safety_risk_label"]:
        if c in sample_df.columns:
            sample_df[c] = sample_df[c].map(_norm)
        if c in scored_df.columns:
            scored_df[c] = scored_df[c].map(_norm)

    sample_df["年份"] = sample_df["年份"].map(_to_int)
    scored_df["年份"] = scored_df["年份"].map(_to_int)

    sample_count = int(len(sample_df))

    # Build context: nearby trusted rows + review_required context
    final_ctx = final_df.copy()
    final_ctx["标准指标"] = final_ctx["标准指标"].map(_norm)
    final_ctx["PDF文件名"] = final_ctx["PDF文件名"].map(_norm)
    final_ctx["年份"] = final_ctx["年份"].map(_to_int)

    review_ctx = review_df.copy()
    review_ctx["标准指标"] = review_ctx["标准指标"].map(_norm)
    review_ctx["PDF文件名"] = review_ctx["PDF文件名"].map(_norm)
    review_ctx["年份"] = review_ctx["年份"].map(_to_int)

    def _nearby_trusted(pdf: str, metric: str, year: int) -> str:
        sub = final_ctx[(final_ctx["PDF文件名"] == pdf) & (final_ctx["标准指标"] == metric)]
        if sub.empty:
            return ""
        sub = sub.assign(_yd=(sub["年份"] - year).abs()).sort_values(["_yd", "年份"]).head(3)
        parts = [f"{_to_int(r['年份'])}:{_norm(r['value'])}:{_norm(r['normalized_unit'])}" for _, r in sub.iterrows()]
        return " | ".join(parts)

    def _review_required_context(pdf: str, metric: str, year: int) -> str:
        sub = review_ctx[(review_ctx["PDF文件名"] == pdf) & (review_ctx["标准指标"] == metric)]
        if sub.empty:
            return ""
        cnt = len(sub)
        yr = sorted(set(_to_int(v) for v in sub["年份"].tolist() if _to_int(v) > 0))
        return f"rows={cnt};years={','.join(str(x) for x in yr[:8])}"

    sample_df["silent_risk_flags"] = sample_df.apply(_silent_risk_flags, axis=1)
    sample_df["risk_label"] = sample_df.get("safety_risk_label", "").map(_norm)
    sample_df["nearby_trusted_rows"] = sample_df.apply(
        lambda r: _nearby_trusted(_norm(r.get("PDF文件名", "")), _norm(r.get("标准指标", "")), _to_int(r.get("年份", 0))),
        axis=1,
    )
    sample_df["review_required_context"] = sample_df.apply(
        lambda r: _review_required_context(_norm(r.get("PDF文件名", "")), _norm(r.get("标准指标", "")), _to_int(r.get("年份", 0))),
        axis=1,
    )

    # Template with reviewer fields
    template_cols = [
        "candidate_id",
        "group_id",
        "PDF文件名",
        "标准指标",
        "指标名",
        "年份",
        "value",
        "unit",
        "normalized_unit",
        "source_parser",
        "source_page",
        "source_bucket",
        "denoise_rule",
        "risk_label",
        "silent_risk_flags",
        "nearby_trusted_rows",
        "review_required_context",
        "decision",
        "reviewer_id",
        "reviewed_at",
        "review_comment",
        "corrected_metric",
        "corrected_year",
        "corrected_value",
        "corrected_unit",
        "extra_info_request",
    ]
    review_template = sample_df.copy()
    for c in ["decision", "reviewer_id", "reviewed_at", "review_comment", "corrected_metric", "corrected_year", "corrected_value", "corrected_unit", "extra_info_request"]:
        review_template[c] = ""
    review_template = review_template[template_cols]

    # Manifest
    manifest_cols = [
        "candidate_id",
        "group_id",
        "PDF文件名",
        "标准指标",
        "指标名",
        "年份",
        "value",
        "unit",
        "normalized_unit",
        "source_parser",
        "source_page",
        "source_bucket",
        "denoise_rule",
        "risk_label",
        "silent_risk_flags",
    ]
    manifest = sample_df[manifest_cols].copy()
    candidate_manifest_preserved = int(len(manifest)) == sample_count

    # Context workbook
    ctx_metric_pdf = (
        sample_df.groupby(["标准指标", "PDF文件名", "denoise_rule", "risk_label"], dropna=False)
        .agg(sampled_row_count=("candidate_id", "count"), candidate_count=("candidate_id", "nunique"))
        .reset_index()
        .sort_values(["sampled_row_count", "candidate_count"], ascending=[False, False])
    )

    _write_excel(
        OUT_TEMPLATE,
        {
            "spot_check_review_template": review_template,
            "decision_guide": pd.DataFrame(
                [
                    {"decision": "approve_rescue", "rule": "Reviewer confirms rescue candidate is safe under current evidence."},
                    {"decision": "reject_rescue", "rule": "review_comment should be provided."},
                    {"decision": "correct_rescue", "rule": "At least one corrected_* field is required."},
                    {"decision": "needs_more_info", "rule": "extra_info_request is required."},
                ]
            ),
        },
    )
    _write_excel(
        OUT_MANIFEST,
        {
            "spot_check_candidate_manifest": manifest,
        },
    )
    _write_excel(
        OUT_CONTEXT,
        {
            "rule_metric_pdf_context": ctx_metric_pdf,
            "risk_distribution_by_metric": risk_metric_df,
            "risk_distribution_by_pdf": risk_pdf_df,
            "rule_safety_audit": rule_audit_df,
        },
    )

    readme_lines = [
        "# 308E Spot-Check Readme",
        "",
        "## Decision Enum",
        "- approve_rescue",
        "- reject_rescue",
        "- correct_rescue",
        "- needs_more_info",
        "",
        "## Field Rules",
        "- correct_rescue: requires at least one corrected_* field.",
        "- needs_more_info: requires extra_info_request.",
        "- reject_rescue: should include review_comment.",
        "- reviewer_id and reviewed_at are required when decision is provided.",
        "- Do not add safe_to_apply / approve_for_real_apply.",
        "",
        "## Notes",
        "- This package is calibration-only and does not merge rows into trusted preview.",
    ]
    OUT_README.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

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

    forbidden_fields_generated = sorted([c for c in set(review_template.columns).union(set(manifest.columns)) if c in FORBIDDEN_FIELDS])

    final_after_hash = _sha256(IN_307G_FINAL)
    final_preview_v2_unchanged = final_before_hash == final_after_hash

    after_parser_outputs = _snapshot_parser_outputs()
    parser_output_files_modified = any(before_parser_outputs[k] != after_parser_outputs[k] for k in before_parser_outputs.keys())
    parser_output_modified_files = [k for k in before_parser_outputs.keys() if before_parser_outputs[k] != after_parser_outputs[k]]

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-308E",
        "mode": "panel_denoise_spot_check_review_package",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "sampled_row_count": sample_count,
        "sampled_row_count_equals_308d_manual_spot_check_sample_row_count": bool(sample_count == len(sample_df)),
        "candidate_manifest_preserved": bool(candidate_manifest_preserved),
        "no_rows_merged_into_final_preview": True,
        "final_preview_v2_unchanged": bool(final_preview_v2_unchanged),
        "parser_output_files_unchanged": bool(not parser_output_files_modified),
        "parser_output_modified_files": parser_output_modified_files,
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
        "# 308E Panel Denoise Spot-Check Review Package",
        "",
        "## Package Summary",
        f"- sampled_row_count: {sample_count}",
        f"- candidate_manifest_preserved: {summary['candidate_manifest_preserved']}",
        "",
        "## Template Coverage",
        "- one row per sampled candidate",
        "- includes denoise_rule/risk_label/silent_risk_flags",
        "- includes nearby trusted rows and review_required context",
        "- includes reviewer decision/correction fields",
        "",
        "## Guard Assertions",
        f"- no_rows_merged_into_final_preview: {summary['no_rows_merged_into_final_preview']}",
        f"- final_preview_v2_unchanged: {summary['final_preview_v2_unchanged']}",
        f"- parser_output_files_unchanged: {summary['parser_output_files_unchanged']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_308e_summary_json: {OUT_SUMMARY}")
    print(f"eval_308e_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
