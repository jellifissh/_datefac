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
OUT_DIR = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design"

IN_306I_SUMMARY = BASE_DIR / "output" / "eval_306i_clean_candidate_review_package" / "306i_summary.json"
IN_306I_REVIEW = BASE_DIR / "output" / "eval_306i_clean_candidate_review_package" / "306i_clean_core_candidates_review.xlsx"
IN_306I_MISSING = BASE_DIR / "output" / "eval_306i_clean_candidate_review_package" / "306i_missing_metric_review.xlsx"
IN_306I_RESCUED = BASE_DIR / "output" / "eval_306i_clean_candidate_review_package" / "306i_rescued_zero_candidate_review.xlsx"

OUT_SUMMARY = OUT_DIR / "306j_summary.json"
OUT_REPORT = OUT_DIR / "306j_report.md"
OUT_PER_PDF = OUT_DIR / "306j_per_pdf_candidate_summary.xlsx"
OUT_TEMPLATE = OUT_DIR / "306j_human_review_input_template.xlsx"
OUT_README = OUT_DIR / "306j_human_review_readme.md"
OUT_POLICY = OUT_DIR / "306j_review_validation_policy.json"
OUT_SAMPLE = OUT_DIR / "306j_sample_review_input.xlsx"
OUT_MANIFEST = OUT_DIR / "306j_candidate_id_manifest.xlsx"
OUT_NO_APPLY = OUT_DIR / "306j_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

ALLOWED_DECISIONS = ["approve", "reject", "needs_more_info", "correct_value"]


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


def _candidate_id(row_uid: str, idx: int) -> str:
    digest = hashlib.sha1(row_uid.encode("utf-8")).hexdigest()[:8].upper()
    return f"C306J-{idx:05d}-{digest}"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306I_SUMMARY, IN_306I_REVIEW, IN_306I_MISSING, IN_306I_RESCUED]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306J",
                "mode": "clean_candidate_human_review_input_design",
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

    s_306i = json.loads(IN_306I_SUMMARY.read_text(encoding="utf-8"))
    review = pd.read_excel(IN_306I_REVIEW).fillna("")
    missing_review = pd.read_excel(IN_306I_MISSING).fillna("")
    rescued_review = pd.read_excel(IN_306I_RESCUED).fillna("")

    review = review.sort_values(["PDF文件名", "标准指标", "年份", "页码", "row_uid"]).reset_index(drop=True)
    review["candidate_id"] = [
        _candidate_id(_norm(rid), i + 1) for i, rid in enumerate(review["row_uid"].map(_norm).tolist())
    ]
    review["candidate_set_version"] = "306h_fix2_clean_core_candidates_v3"

    # Candidate manifest (no human decision fields).
    manifest_cols = [
        "candidate_id",
        "candidate_set_version",
        "PDF文件名",
        "页码",
        "指标名",
        "标准指标",
        "标准指标中文",
        "年份",
        "数值",
        "单位",
        "来源解析器",
        "来源原因",
        "是否别名恢复",
        "是否zero-candidate救回",
        "source_bucket",
        "source_panel_id",
        "row_uid",
    ]
    manifest_df = review[manifest_cols].copy()

    # Human review template with required decision fields.
    template_df = manifest_df.copy()
    template_df["decision"] = ""
    template_df["reviewer_id"] = ""
    template_df["reviewed_at"] = ""
    template_df["review_comment"] = ""
    template_df["corrected_value"] = ""
    template_df["corrected_unit"] = ""
    template_df["evidence_note"] = ""
    template_df["extra_info_request"] = ""
    # explicitly avoid forbidden fields by not creating them.

    # Sample review input (first 4 rows, one per decision type).
    sample_df = template_df.head(4).copy()
    if len(sample_df) >= 1:
        sample_df.loc[sample_df.index[0], "decision"] = "approve"
        sample_df.loc[sample_df.index[0], "reviewer_id"] = "reviewer_demo_01"
        sample_df.loc[sample_df.index[0], "reviewed_at"] = "2026-05-27T10:00:00+08:00"
        sample_df.loc[sample_df.index[0], "review_comment"] = "数值与原表一致。"
    if len(sample_df) >= 2:
        sample_df.loc[sample_df.index[1], "decision"] = "reject"
        sample_df.loc[sample_df.index[1], "reviewer_id"] = "reviewer_demo_02"
        sample_df.loc[sample_df.index[1], "reviewed_at"] = "2026-05-27T10:05:00+08:00"
        sample_df.loc[sample_df.index[1], "review_comment"] = "疑似指标错配，建议剔除。"
    if len(sample_df) >= 3:
        sample_df.loc[sample_df.index[2], "decision"] = "needs_more_info"
        sample_df.loc[sample_df.index[2], "reviewer_id"] = "reviewer_demo_03"
        sample_df.loc[sample_df.index[2], "reviewed_at"] = "2026-05-27T10:10:00+08:00"
        sample_df.loc[sample_df.index[2], "extra_info_request"] = "请补充原页截图与单位来源。"
    if len(sample_df) >= 4:
        sample_df.loc[sample_df.index[3], "decision"] = "correct_value"
        sample_df.loc[sample_df.index[3], "reviewer_id"] = "reviewer_demo_04"
        sample_df.loc[sample_df.index[3], "reviewed_at"] = "2026-05-27T10:15:00+08:00"
        sample_df.loc[sample_df.index[3], "corrected_value"] = "123.45"
        sample_df.loc[sample_df.index[3], "corrected_unit"] = "million_cny"
        sample_df.loc[sample_df.index[3], "review_comment"] = "原值小数点疑似错位，已人工更正。"

    # Validation policy JSON
    policy = {
        "stage": "EVAL-306J",
        "mode": "clean_candidate_human_review_input_design",
        "candidate_source": "output/eval_306i_clean_candidate_review_package/306i_clean_core_candidates_review.xlsx",
        "candidate_set_version": "306h_fix2_clean_core_candidates_v3",
        "allowed_decisions": ALLOWED_DECISIONS,
        "required_fields_all_decisions": ["candidate_id", "decision", "reviewer_id", "reviewed_at"],
        "conditional_required_fields": {
            "correct_value": ["corrected_value", "corrected_unit"],
        },
        "forbidden_fields": ["safe_to_apply", "approve_for_real_apply"],
        "timestamp_format_recommendation": "ISO-8601 with timezone, e.g. 2026-05-27T10:15:00+08:00",
        "review_workflow_notes": [
            "approve/reject/needs_more_info/correct_value only",
            "correct_value must provide both corrected_value and corrected_unit",
            "reviewer_id and reviewed_at required for every reviewed row",
            "human review file must not add safe_to_apply or approve_for_real_apply columns",
        ],
    }
    _write_json(OUT_POLICY, policy)

    # Readme for reviewers
    readme_lines = [
        "# 306J Human Review Input Readme",
        "",
        "## 1. 输入文件",
        "- 使用 `306j_human_review_input_template.xlsx` 填写人工审核结果。",
        "- `candidate_id` 为唯一键，不可修改。",
        "",
        "## 2. 决策枚举",
        "- `approve`",
        "- `reject`",
        "- `needs_more_info`",
        "- `correct_value`",
        "",
        "## 3. 必填规则",
        "- 所有决策都必须填写：`reviewer_id`, `reviewed_at`。",
        "- 当 `decision=correct_value` 时，必须填写：`corrected_value`, `corrected_unit`。",
        "",
        "## 4. 禁止字段",
        "- 禁止新增或填写：`safe_to_apply`。",
        "- 禁止新增或填写：`approve_for_real_apply`。",
        "",
        "## 5. 审核建议",
        "- `reviewed_at` 建议使用 ISO-8601（含时区）。",
        "- 对 `needs_more_info` 建议填写 `extra_info_request`。",
        "- 对 `reject`/`correct_value` 建议填写 `review_comment` 和 `evidence_note`。",
    ]
    OUT_README.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    # Workbook outputs
    template_dict_df = pd.DataFrame(
        [
            {"field_name": "decision", "description": "人工决策", "required": "yes", "allowed_values": "|".join(ALLOWED_DECISIONS)},
            {"field_name": "reviewer_id", "description": "审核人ID", "required": "yes", "allowed_values": ""},
            {"field_name": "reviewed_at", "description": "审核时间(ISO-8601)", "required": "yes", "allowed_values": ""},
            {"field_name": "review_comment", "description": "审核意见", "required": "no", "allowed_values": ""},
            {"field_name": "corrected_value", "description": "更正值", "required": "if decision=correct_value", "allowed_values": ""},
            {"field_name": "corrected_unit", "description": "更正单位", "required": "if decision=correct_value", "allowed_values": ""},
            {"field_name": "evidence_note", "description": "证据说明", "required": "no", "allowed_values": ""},
            {"field_name": "extra_info_request", "description": "补充信息请求", "required": "no", "allowed_values": ""},
            {"field_name": "safe_to_apply", "description": "禁止字段", "required": "forbidden", "allowed_values": "N/A"},
            {"field_name": "approve_for_real_apply", "description": "禁止字段", "required": "forbidden", "allowed_values": "N/A"},
        ]
    )

    _write_excel(
        OUT_TEMPLATE,
        {
            "human_review_input_template": template_df,
            "field_dictionary": template_dict_df,
        },
    )
    _write_excel(
        OUT_SAMPLE,
        {
            "sample_review_input": sample_df,
            "field_dictionary": template_dict_df,
        },
    )
    _write_excel(OUT_MANIFEST, {"candidate_id_manifest": manifest_df})

    # Also provide concise summaries from 306i views.
    per_pdf_summary = (
        review.groupby("PDF文件名", dropna=False)
        .agg(
            候选行数=("candidate_id", "count"),
            别名恢复行数=("是否别名恢复", lambda x: int(pd.Series(x).astype(bool).sum())),
            zero_candidate救回行数=("是否zero-candidate救回", lambda x: int(pd.Series(x).astype(bool).sum())),
        )
        .reset_index()
    )
    # include 306i missing & rescued references
    _write_excel(
        OUT_PER_PDF,
        {
            "per_pdf_candidate_summary": per_pdf_summary,
            "source_306i_missing_metric_review": missing_review,
            "source_306i_rescued_zero_candidate_review": rescued_review,
        },
    )

    # no_apply proof
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
        "stage": "EVAL-306J",
        "mode": "clean_candidate_human_review_input_design",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "source_candidate_row_count": int(len(review)),
        "candidate_manifest_row_count": int(len(manifest_df)),
        "template_row_count": int(len(template_df)),
        "sample_row_count": int(len(sample_df)),
        "forbidden_fields_present_in_template": bool(
            ("safe_to_apply" in template_df.columns) or ("approve_for_real_apply" in template_df.columns)
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
        "# 306J Clean Candidate Human Review Input Design",
        "",
        f"- source_candidate_row_count: {summary['source_candidate_row_count']}",
        f"- candidate_manifest_row_count: {summary['candidate_manifest_row_count']}",
        f"- template_row_count: {summary['template_row_count']}",
        f"- sample_row_count: {summary['sample_row_count']}",
        f"- forbidden_fields_present_in_template: {summary['forbidden_fields_present_in_template']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306j_summary_json: {OUT_SUMMARY}")
    print(f"eval_306j_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
