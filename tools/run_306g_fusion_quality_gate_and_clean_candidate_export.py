from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306g_fusion_quality_gate_and_clean_candidate_export"

IN_306E_SUMMARY = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_summary.json"
IN_306E_FUSION = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_structured_table.xlsx"
IN_306E_CORE = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_core_metric_candidates.xlsx"
IN_306E_CONFLICT = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_conflict_audit.xlsx"

IN_306F_SUMMARY = BASE_DIR / "output" / "eval_306f_fusion_result_quality_validation" / "306f_summary.json"
IN_306F_CORE_AUDIT = BASE_DIR / "output" / "eval_306f_fusion_result_quality_validation" / "306f_core_candidate_quality_audit.xlsx"
IN_306F_SUSPICIOUS = BASE_DIR / "output" / "eval_306f_fusion_result_quality_validation" / "306f_suspicious_fusion_rows.xlsx"

OUT_SUMMARY = OUT_DIR / "306g_summary.json"
OUT_REPORT = OUT_DIR / "306g_report.md"
OUT_CLEAN_CORE = OUT_DIR / "306g_clean_core_candidates.xlsx"
OUT_CLEAN_STRUCTURED = OUT_DIR / "306g_clean_structured_rows.xlsx"
OUT_SUSPICIOUS = OUT_DIR / "306g_suspicious_structured_rows.xlsx"
OUT_BLOCKED = OUT_DIR / "306g_blocked_structured_rows.xlsx"
OUT_RULES = OUT_DIR / "306g_quality_gate_rules.json"
OUT_MANUAL = OUT_DIR / "306g_manual_review_samples.xlsx"
OUT_NO_APPLY = OUT_DIR / "306g_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

CORE_METRICS = {
    "revenue",
    "net_profit",
    "attributable_net_profit",
    "total_assets",
    "total_liabilities",
    "operating_cash_flow",
    "eps",
    "roe",
    "gross_margin",
    "pe",
    "pb",
    "ev_ebitda",
}

BLOCK_METRIC_KEYWORDS = [
    "评级",
    "基准",
    "指数",
    "风险",
    "免责声明",
    "报告",
    "联系人",
    "分析师",
    "大市",
    "ixic",
    "沪深",
    "msci",
]

BLOCK_VALUE_KEYWORDS = [
    "同比",
    "环比",
    "观点",
    "风险提示",
    "评级",
    "证券",
    "研究所",
    "报告",
    "免责声明",
]


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


def _to_float(v: Any) -> Optional[float]:
    s = _norm(v)
    if s == "":
        return None
    s = s.replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


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


def _row_uid(row: pd.Series) -> str:
    return "|".join(
        [
            _norm(row.get("source_pdf_name", "")),
            str(_to_int(row.get("page_number", 0))),
            _norm(row.get("normalized_metric_name", "")),
            str(_to_int(row.get("year", 0))),
            _norm(row.get("source_panel_id", "")),
            _norm(row.get("value_raw", "")),
        ]
    )


def _is_sentence_like_metric(metric: str) -> bool:
    s = _norm(metric).lower()
    if s == "":
        return True
    if len(s) >= 24:
        return True
    if any(ch in s for ch in ["。", "，", ",", "；", ";", "：", ":", " "]) and len(s) >= 12:
        return True
    return False


def _metric_has_block_keyword(metric: str) -> bool:
    s = _norm(metric).lower()
    return any(k.lower() in s for k in BLOCK_METRIC_KEYWORDS)


def _value_is_prose(value_raw: str) -> bool:
    s = _norm(value_raw)
    if s == "":
        return True
    if len(s) >= 40:
        return True
    if any(k in s for k in BLOCK_VALUE_KEYWORDS):
        return True
    return False


def _value_has_multi_numbers(value_raw: str) -> bool:
    s = _norm(value_raw)
    if s == "":
        return False
    nums = re.findall(r"-?\d+(?:\.\d+)?", s)
    if len(nums) <= 1:
        return False
    if any(sep in s for sep in [" ", "，", ",", "、", "/", "|"]):
        return True
    return len(nums) >= 3


def _dirty_confidence(flag: str) -> bool:
    s = _norm(flag)
    return s not in {"", "ok", "pdfplumber_selected"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_306E_SUMMARY,
        IN_306E_FUSION,
        IN_306E_CORE,
        IN_306E_CONFLICT,
        IN_306F_SUMMARY,
        IN_306F_CORE_AUDIT,
        IN_306F_SUSPICIOUS,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306G",
                "mode": "fusion_quality_gate_and_clean_candidate_export",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
                "marker_rerun_executed": False,
                "pdfplumber_rerun_executed": False,
            },
        )
        return 0

    before = _snapshot_guard()

    fusion = pd.read_excel(IN_306E_FUSION).fillna("")
    core = pd.read_excel(IN_306E_CORE).fillna("")
    conflict = pd.read_excel(IN_306E_CONFLICT).fillna("")
    core_audit = pd.read_excel(IN_306F_CORE_AUDIT).fillna("")
    suspicious_306f = pd.read_excel(IN_306F_SUSPICIOUS).fillna("")
    sum_306e = json.loads(IN_306E_SUMMARY.read_text(encoding="utf-8"))
    sum_306f = json.loads(IN_306F_SUMMARY.read_text(encoding="utf-8"))

    fusion["row_uid"] = fusion.apply(_row_uid, axis=1)
    core["row_uid"] = core.apply(_row_uid, axis=1)
    core_audit["row_uid"] = core_audit.apply(_row_uid, axis=1)
    suspicious_306f["row_uid"] = suspicious_306f.apply(_row_uid, axis=1)

    conflict_keys: Set[Tuple[str, str, int]] = set()
    for _, r in conflict.iterrows():
        conflict_keys.add(
            (
                _norm(r.get("source_pdf_name", "")),
                _norm(r.get("metric_norm", "")),
                _to_int(r.get("year", 0)),
            )
        )

    suspicious_uid_set = set(suspicious_306f["row_uid"].map(_norm).tolist())
    pass_core_uid_set = set(
        core_audit[core_audit["quality_status"].map(_norm) == "PASS"]["row_uid"].map(_norm).tolist()
    )

    blocked_rows: List[Dict[str, Any]] = []
    suspicious_rows: List[Dict[str, Any]] = []
    clean_rows: List[Dict[str, Any]] = []

    for _, row in fusion.iterrows():
        metric = _norm(row.get("normalized_metric_name", ""))
        raw_metric = _norm(row.get("raw_metric_name", ""))
        value_raw = _norm(row.get("value_raw", ""))
        conf_flag = _norm(row.get("confidence_flags", ""))
        pdf_name = _norm(row.get("source_pdf_name", ""))
        year = _to_int(row.get("year", 0))
        uid = _norm(row.get("row_uid", ""))
        reasons_block: List[str] = []
        reasons_suspicious: List[str] = []

        if (pdf_name, metric, year) in conflict_keys:
            reasons_block.append("cross_source_conflict")
        if _dirty_confidence(conf_flag):
            reasons_block.append("dirty_confidence_flag")
        if _is_sentence_like_metric(metric) or _is_sentence_like_metric(raw_metric):
            reasons_suspicious.append("metric_sentence_like_or_too_long")
        if _metric_has_block_keyword(metric) or _metric_has_block_keyword(raw_metric):
            reasons_block.append("metric_contains_rating_index_risk_disclaimer")
        if _value_is_prose(value_raw):
            reasons_suspicious.append("value_raw_long_prose")
        if _value_has_multi_numbers(value_raw):
            reasons_suspicious.append("value_raw_multi_numbers")
        if uid in suspicious_uid_set:
            reasons_suspicious.append("flagged_by_306f_suspicious_audit")

        # promote suspicious to blocked when both metric+value indicate severe noise.
        if (
            ("metric_sentence_like_or_too_long" in reasons_suspicious and "value_raw_long_prose" in reasons_suspicious)
            or ("metric_sentence_like_or_too_long" in reasons_suspicious and "value_raw_multi_numbers" in reasons_suspicious)
        ):
            reasons_block.append("severe_metric_value_noise")

        rec = row.to_dict()
        rec["block_reasons"] = "|".join(sorted(set(reasons_block)))
        rec["suspicious_reasons"] = "|".join(sorted(set(reasons_suspicious)))

        if len(reasons_block) > 0:
            blocked_rows.append(rec)
        elif len(reasons_suspicious) > 0:
            suspicious_rows.append(rec)
        else:
            clean_rows.append(rec)

    clean_df = pd.DataFrame(clean_rows).fillna("")
    suspicious_df = pd.DataFrame(suspicious_rows).fillna("")
    blocked_df = pd.DataFrame(blocked_rows).fillna("")

    # clean core candidates: keep PASS from 306F, then remove blocked row_uids.
    blocked_uid_set = set(blocked_df["row_uid"].map(_norm).tolist()) if not blocked_df.empty else set()
    core["keep_by_306f_pass"] = core["row_uid"].map(lambda x: _norm(x) in pass_core_uid_set)
    core["blocked_by_306g"] = core["row_uid"].map(lambda x: _norm(x) in blocked_uid_set)
    clean_core = core[(core["keep_by_306f_pass"]) & (~core["blocked_by_306g"])].copy()
    clean_core = clean_core.drop(columns=["keep_by_306f_pass", "blocked_by_306g"], errors="ignore")

    # ensure clean core metric names are core set.
    clean_core = clean_core[clean_core["normalized_metric_name"].map(_norm).isin(CORE_METRICS)].copy()

    # manual review samples.
    manual_block = blocked_df.head(120).copy() if not blocked_df.empty else pd.DataFrame([{"note": "no_blocked_rows"}])
    manual_susp = suspicious_df.head(120).copy() if not suspicious_df.empty else pd.DataFrame([{"note": "no_suspicious_rows"}])
    core_warn = core_audit[core_audit["quality_status"].map(_norm) != "PASS"].head(80).copy()
    if core_warn.empty:
        core_warn = pd.DataFrame([{"note": "no_non_pass_core_rows"}])

    # write outputs.
    _write_excel(OUT_CLEAN_STRUCTURED, {"clean_structured_rows": clean_df if not clean_df.empty else pd.DataFrame([{"note": "no_clean_rows"}])})
    _write_excel(OUT_SUSPICIOUS, {"suspicious_structured_rows": suspicious_df if not suspicious_df.empty else pd.DataFrame([{"note": "no_suspicious_rows"}])})
    _write_excel(OUT_BLOCKED, {"blocked_structured_rows": blocked_df if not blocked_df.empty else pd.DataFrame([{"note": "no_blocked_rows"}])})
    _write_excel(OUT_CLEAN_CORE, {"clean_core_candidates": clean_core if not clean_core.empty else pd.DataFrame([{"note": "no_clean_core_rows"}])})
    _write_excel(
        OUT_MANUAL,
        {
            "blocked_manual_review": manual_block,
            "suspicious_manual_review": manual_susp,
            "core_warn_manual_review": core_warn,
        },
    )

    rules_payload = {
        "stage": "EVAL-306G",
        "mode": "fusion_quality_gate_and_clean_candidate_export",
        "hard_block_rules": [
            "cross_source_conflict",
            "dirty_confidence_flag",
            "metric_contains_rating_index_risk_disclaimer",
            "severe_metric_value_noise",
        ],
        "suspicious_rules": [
            "metric_sentence_like_or_too_long",
            "value_raw_long_prose",
            "value_raw_multi_numbers",
            "flagged_by_306f_suspicious_audit",
        ],
        "metric_block_keywords": BLOCK_METRIC_KEYWORDS,
        "value_block_keywords": BLOCK_VALUE_KEYWORDS,
        "core_metric_set": sorted(list(CORE_METRICS)),
    }
    _write_json(OUT_RULES, rules_payload)

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

    block_reason_stats = (
        blocked_df["block_reasons"].value_counts().reset_index(name="count").rename(columns={"index": "block_reasons"})
        if not blocked_df.empty
        else pd.DataFrame(columns=["block_reasons", "count"])
    )
    susp_reason_stats = (
        suspicious_df["suspicious_reasons"].value_counts().reset_index(name="count").rename(columns={"index": "suspicious_reasons"})
        if not suspicious_df.empty
        else pd.DataFrame(columns=["suspicious_reasons", "count"])
    )
    if not block_reason_stats.empty or not susp_reason_stats.empty:
        _write_excel(
            OUT_MANUAL,
            {
                "blocked_manual_review": manual_block,
                "suspicious_manual_review": manual_susp,
                "core_warn_manual_review": core_warn,
                "block_reason_stats": block_reason_stats if not block_reason_stats.empty else pd.DataFrame([{"note": "no_block_reason"}]),
                "suspicious_reason_stats": susp_reason_stats if not susp_reason_stats.empty else pd.DataFrame([{"note": "no_suspicious_reason"}]),
            },
        )

    summary = {
        "stage": "EVAL-306G",
        "mode": "fusion_quality_gate_and_clean_candidate_export",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_306e_summary_loaded": True,
        "eval_306f_summary_loaded": True,
        "source_fusion_row_count": int(len(fusion)),
        "source_core_candidate_row_count": int(len(core)),
        "clean_structured_row_count": int(len(clean_df)),
        "suspicious_structured_row_count": int(len(suspicious_df)),
        "blocked_structured_row_count": int(len(blocked_df)),
        "clean_core_candidate_row_count": int(len(clean_core)),
        "core_pass_row_count_from_306f": int(_to_int(sum_306f.get("core_candidate_pass_count", 0))),
        "core_warn_row_count_from_306f": int(_to_int(sum_306f.get("core_candidate_warn_count", 0))),
        "core_fail_row_count_from_306f": int(_to_int(sum_306f.get("core_candidate_fail_count", 0))),
        "conflict_row_count_from_306e": int(len(conflict)),
        "manual_review_sample_count": int(len(manual_block) + len(manual_susp) + len(core_warn)),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_next_candidate_stage": bool(
            delivery_status == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
            and len(clean_core) > 0
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306G Fusion Quality Gate And Clean Candidate Export",
        "",
        f"- source_fusion_row_count: {summary['source_fusion_row_count']}",
        f"- clean_structured_row_count: {summary['clean_structured_row_count']}",
        f"- suspicious_structured_row_count: {summary['suspicious_structured_row_count']}",
        f"- blocked_structured_row_count: {summary['blocked_structured_row_count']}",
        f"- source_core_candidate_row_count: {summary['source_core_candidate_row_count']}",
        f"- clean_core_candidate_row_count: {summary['clean_core_candidate_row_count']}",
        f"- conflict_row_count_from_306e: {summary['conflict_row_count_from_306e']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- ready_for_next_candidate_stage: {summary['ready_for_next_candidate_stage']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306g_summary_json: {OUT_SUMMARY}")
    print(f"eval_306g_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
