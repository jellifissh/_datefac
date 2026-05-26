from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
IN_DIR = BASE_DIR / "output" / "eval_306g_fusion_quality_gate_and_clean_candidate_export"
OUT_DIR = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate"

IN_SUMMARY = IN_DIR / "306g_summary.json"
IN_CLEAN_CORE = IN_DIR / "306g_clean_core_candidates.xlsx"
IN_CLEAN_STRUCTURED = IN_DIR / "306g_clean_structured_rows.xlsx"
IN_SUSPICIOUS = IN_DIR / "306g_suspicious_structured_rows.xlsx"

OUT_SUMMARY = OUT_DIR / "306g_fix_summary.json"
OUT_REPORT = OUT_DIR / "306g_fix_report.md"
OUT_CLEAN_CORE = OUT_DIR / "306g_fix_clean_core_candidates.xlsx"
OUT_REMOVED = OUT_DIR / "306g_fix_removed_core_false_positives.xlsx"
OUT_CLEAN_STRUCTURED = OUT_DIR / "306g_fix_clean_structured_rows.xlsx"
OUT_SUSPICIOUS = OUT_DIR / "306g_fix_suspicious_structured_rows.xlsx"
OUT_RULES = OUT_DIR / "306g_fix_quality_gate_rules.json"
OUT_NO_APPLY = OUT_DIR / "306g_fix_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

ABSOLUTE_CORE_METRICS = {"revenue", "net_profit", "attributable_net_profit"}
ALL_CORE_METRICS = {
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
GROWTH_KEYWORDS = ["增长率", "增长", "同比", "yoy", "YoY", "YOY"]
PROSE_HINTS = [
    "报告",
    "观点",
    "评级",
    "证券",
    "风险",
    "联系人",
    "研究所",
    "指数",
    "大市",
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


def _metric_sentence_like(text: str) -> bool:
    s = _norm(text)
    if s == "":
        return True
    if len(s) >= 20:
        return True
    if any(ch in s for ch in ["。", "，", ",", ";", "；", ":", "：", " "]):
        return True
    return False


def _contains_growth_hint(text: str) -> bool:
    s = _norm(text).lower()
    return any(k.lower() in s for k in GROWTH_KEYWORDS)


def _value_looks_code_or_prose(value_raw: str) -> bool:
    s = _norm(value_raw)
    if s == "":
        return True
    if any(k in s for k in PROSE_HINTS):
        return True
    # stock-like code or ID-like token
    if re.search(r"[A-Za-z]{2,}\d{2,}", s) or re.search(r"\d{6}\.[A-Za-z]{2,4}", s):
        return True
    if len(s) >= 35:
        return True
    # must contain numeric signal for core rows
    has_num = re.search(r"-?\d+(?:\.\d+)?", s) is not None
    if not has_num:
        return True
    # too many numbers in a core value cell indicates merged prose/list
    nums = re.findall(r"-?\d+(?:\.\d+)?", s)
    if len(nums) >= 3 and any(sep in s for sep in [" ", "，", ",", "、", "/", "|"]):
        return True
    return False


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_SUMMARY, IN_CLEAN_CORE, IN_CLEAN_STRUCTURED, IN_SUSPICIOUS]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306G-FIX",
                "mode": "core_semantic_quality_gate_fix",
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

    summary_306g = json.loads(IN_SUMMARY.read_text(encoding="utf-8"))
    clean_core = pd.read_excel(IN_CLEAN_CORE).fillna("")
    clean_structured = pd.read_excel(IN_CLEAN_STRUCTURED).fillna("")
    suspicious_structured = pd.read_excel(IN_SUSPICIOUS).fillna("")

    removed_rows: List[Dict[str, Any]] = []
    keep_rows: List[Dict[str, Any]] = []

    for _, r in clean_core.iterrows():
        metric = _norm(r.get("normalized_metric_name", ""))
        raw_metric = _norm(r.get("raw_metric_name", ""))
        year = _to_int(r.get("year", 0))
        value_raw = _norm(r.get("value_raw", ""))
        reasons: List[str] = []

        if metric in ABSOLUTE_CORE_METRICS and _contains_growth_hint(raw_metric):
            reasons.append("growth_row_mapped_to_absolute_core_metric")
        if _metric_sentence_like(raw_metric):
            reasons.append("sentence_like_raw_metric_name")
        if year < 2020 or year > 2032:
            reasons.append("unreasonable_year_out_of_range")
        if _value_looks_code_or_prose(value_raw):
            reasons.append("value_raw_code_or_prose_like")
        if metric not in ALL_CORE_METRICS:
            reasons.append("non_core_metric_in_clean_core")

        rec = r.to_dict()
        rec["removed_reasons"] = "|".join(sorted(set(reasons)))
        # optional semantic remap hint for growth rows
        if "growth_row_mapped_to_absolute_core_metric" in reasons:
            rec["suggested_metric_remap"] = f"{metric}_growth_rate"
        else:
            rec["suggested_metric_remap"] = ""

        if reasons:
            removed_rows.append(rec)
        else:
            keep_rows.append(r.to_dict())

    fixed_clean_core = pd.DataFrame(keep_rows).fillna("")
    removed_df = pd.DataFrame(removed_rows).fillna("")

    removed_uid_set = set(removed_df["row_uid"].map(_norm).tolist()) if not removed_df.empty else set()

    # propagate removed core rows from clean structured into suspicious structured.
    moved_df = clean_structured[clean_structured["row_uid"].map(_norm).isin(removed_uid_set)].copy()
    if not moved_df.empty:
        if "suspicious_reasons" not in moved_df.columns:
            moved_df["suspicious_reasons"] = ""
        moved_df["suspicious_reasons"] = moved_df["suspicious_reasons"].map(
            lambda x: (f"{_norm(x)}|core_semantic_false_positive").strip("|")
        )

    fixed_clean_structured = clean_structured[~clean_structured["row_uid"].map(_norm).isin(removed_uid_set)].copy()
    fixed_suspicious = pd.concat([suspicious_structured, moved_df], ignore_index=True).fillna("")
    if "row_uid" in fixed_suspicious.columns:
        fixed_suspicious = fixed_suspicious.drop_duplicates(subset=["row_uid"], keep="first")

    _write_excel(OUT_CLEAN_CORE, {"clean_core_candidates": fixed_clean_core if not fixed_clean_core.empty else pd.DataFrame([{"note": "no_clean_core_candidates"}])})
    _write_excel(OUT_REMOVED, {"removed_core_false_positives": removed_df if not removed_df.empty else pd.DataFrame([{"note": "no_removed_false_positives"}])})
    _write_excel(OUT_CLEAN_STRUCTURED, {"clean_structured_rows": fixed_clean_structured if not fixed_clean_structured.empty else pd.DataFrame([{"note": "no_clean_structured_rows"}])})
    _write_excel(OUT_SUSPICIOUS, {"suspicious_structured_rows": fixed_suspicious if not fixed_suspicious.empty else pd.DataFrame([{"note": "no_suspicious_structured_rows"}])})

    rules = {
        "stage": "EVAL-306G-FIX",
        "mode": "core_semantic_quality_gate_fix",
        "absolute_core_metrics_guarded": sorted(list(ABSOLUTE_CORE_METRICS)),
        "growth_keywords": GROWTH_KEYWORDS,
        "year_min": 2020,
        "year_max": 2032,
        "value_code_or_prose_hints": PROSE_HINTS,
        "actions": {
            "growth_absolute_core": "quarantine_removed_core_false_positives",
            "sentence_like_metric": "quarantine_removed_core_false_positives",
            "out_of_range_year": "quarantine_removed_core_false_positives",
            "code_or_prose_value": "quarantine_removed_core_false_positives",
        },
    }
    _write_json(OUT_RULES, rules)

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

    removed_reason_counts = {}
    if not removed_df.empty and "removed_reasons" in removed_df.columns:
        for rr in removed_df["removed_reasons"].tolist():
            for token in [x for x in _norm(rr).split("|") if x]:
                removed_reason_counts[token] = removed_reason_counts.get(token, 0) + 1

    summary = {
        "stage": "EVAL-306G-FIX",
        "mode": "core_semantic_quality_gate_fix",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_306g_summary_loaded": True,
        "source_clean_core_row_count": int(len(clean_core)),
        "fixed_clean_core_row_count": int(len(fixed_clean_core)),
        "removed_core_false_positive_count": int(len(removed_df)),
        "growth_semantic_removed_count": int(removed_reason_counts.get("growth_row_mapped_to_absolute_core_metric", 0)),
        "sentence_metric_removed_count": int(removed_reason_counts.get("sentence_like_raw_metric_name", 0)),
        "year_out_of_range_removed_count": int(removed_reason_counts.get("unreasonable_year_out_of_range", 0)),
        "value_semantic_removed_count": int(removed_reason_counts.get("value_raw_code_or_prose_like", 0)),
        "moved_clean_to_suspicious_count": int(len(moved_df)),
        "source_clean_structured_row_count": int(len(clean_structured)),
        "fixed_clean_structured_row_count": int(len(fixed_clean_structured)),
        "source_suspicious_structured_row_count": int(len(suspicious_structured)),
        "fixed_suspicious_structured_row_count": int(len(fixed_suspicious)),
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
            and len(fixed_clean_core) > 0
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306G-Fix Core Semantic Quality Gate",
        "",
        f"- source_clean_core_row_count: {summary['source_clean_core_row_count']}",
        f"- fixed_clean_core_row_count: {summary['fixed_clean_core_row_count']}",
        f"- removed_core_false_positive_count: {summary['removed_core_false_positive_count']}",
        f"- growth_semantic_removed_count: {summary['growth_semantic_removed_count']}",
        f"- sentence_metric_removed_count: {summary['sentence_metric_removed_count']}",
        f"- year_out_of_range_removed_count: {summary['year_out_of_range_removed_count']}",
        f"- value_semantic_removed_count: {summary['value_semantic_removed_count']}",
        f"- moved_clean_to_suspicious_count: {summary['moved_clean_to_suspicious_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- ready_for_next_candidate_stage: {summary['ready_for_next_candidate_stage']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306g_fix_summary_json: {OUT_SUMMARY}")
    print(f"eval_306g_fix_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
