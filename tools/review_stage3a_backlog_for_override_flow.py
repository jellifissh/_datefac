import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OVERRIDE_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
STAGE3A_OUT = BASE_DIR / "output" / "stage3a_backlog_review"


ACTION_READY_MANUAL = "READY_FOR_MANUAL_EVIDENCE_REVIEW"
ACTION_READY_OVERRIDE = "READY_FOR_OVERRIDE_DRAFT"
ACTION_NEED_CONFLICT = "NEED_CONFLICT_RESOLUTION"
ACTION_NEED_EVIDENCE = "NEED_SOURCE_EVIDENCE"
ACTION_REJECT = "REJECT_CANDIDATE"
ACTION_COVERED = "ALREADY_COVERED_BY_02B_OR_06"

ALLOWED_ACTIONS = {
    ACTION_READY_MANUAL,
    ACTION_READY_OVERRIDE,
    ACTION_NEED_CONFLICT,
    ACTION_NEED_EVIDENCE,
    ACTION_REJECT,
    ACTION_COVERED,
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _key(asset: str, metric: str, year: str) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _parse_number(text: str) -> Optional[float]:
    s = _norm(text).replace(",", "")
    if not s:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    try:
        v = float(s)
        return -v if neg else v
    except Exception:
        return None


def _value_equal(v1: str, v2: str) -> bool:
    n1 = _parse_number(v1)
    n2 = _parse_number(v2)
    if n1 is not None and n2 is not None:
        return abs(n1 - n2) <= 1e-9
    return _norm(v1) == _norm(v2)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str, prefer_no_copy: bool = True) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    if prefer_no_copy:
        filtered = [p for p in files if "_copy_" not in p.name]
        if filtered:
            return filtered[0]
    return files[0]


def _snapshot_prod() -> Dict[str, str]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02_candidates = sorted(DELIVERY_DIR.glob("02_*.xlsx"))
    p02 = next((p for p in p02_candidates if "backup" not in p.name.lower()), p02_candidates[0])
    p02a = _find_delivery_file("02A_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    return {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "06": _sha256(p06),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    try:
        return json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN"}


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _safe_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_inputs() -> Dict[str, Any]:
    p75 = DELIVERY_DIR / "75_stage1b_backlog_inventory.xlsx"
    p76 = DELIVERY_DIR / "76_stage1b_backlog_summary.json"
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    if not p75.exists():
        raise FileNotFoundError(f"Missing backlog inventory: {p75}")
    if not p76.exists():
        raise FileNotFoundError(f"Missing backlog summary: {p76}")
    if not OVERRIDE_PATH.exists():
        raise FileNotFoundError(f"Missing override table: {OVERRIDE_PATH}")

    backlog = pd.read_excel(p75, sheet_name="backlog_inventory").fillna("")
    summary76 = json.loads(p76.read_text(encoding="utf-8"))
    df06 = pd.read_excel(p06).fillna("")
    df02b = pd.read_excel(OVERRIDE_PATH, sheet_name="ai_repair_override").fillna("")
    return {"p75": p75, "p76": p76, "p06": p06, "backlog": backlog, "summary76": summary76, "df06": df06, "df02b": df02b}


def _metric_alias(metric: str) -> str:
    m = _norm(metric)
    aliases = {
        "净利润": "归属母公司净利润",
        "EPS": "每股收益",
    }
    return aliases.get(m, m)


def _parse_metric_key(metric_key: str) -> Tuple[str, str, str]:
    parts = _norm(metric_key).split("|")
    if len(parts) >= 3:
        return _norm(parts[0]), _norm(parts[1]), _norm(parts[2])
    return "", "", ""


def _build_reference_maps(df06: pd.DataFrame, df02b: pd.DataFrame) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    d06 = df06.copy()
    d06["_key"] = d06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    m06: Dict[str, Dict[str, Any]] = {}
    for _, r in d06.iterrows():
        m06[_norm(r["_key"])] = {
            "final_value": _norm(r.get("final_value")),
            "final_unit": _norm(r.get("final_unit")),
            "final_value_source": _norm(r.get("final_value_source")),
        }

    d2b = df02b.copy()
    d2b["_key"] = d2b.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    m2b: Dict[str, Dict[str, Any]] = {}
    for _, r in d2b.iterrows():
        m2b[_norm(r["_key"])] = {
            "final_value": _norm(r.get("final_value")),
            "final_unit": _norm(r.get("final_unit")),
            "candidate_id": _norm(r.get("candidate_id")),
            "source_reference": _norm(r.get("source_reference")),
        }
    return m06, m2b


def _infer_asset_package(row: pd.Series) -> str:
    mk = _norm(row.get("metric_key"))
    if mk.startswith("H3_") and "|资产包|" in mk:
        return mk.split("|")[0]
    company = _norm(row.get("company"))
    mapping = {
        "三鑫医疗": "H3_AP202605141822317484_1_资产包",
        "科锐国际": "H3_AP202605141822318060_1_资产包",
        "冠豪高新": "H3_AP202605121822223662_1_资产包",
    }
    return mapping.get(company, "")


def _infer_standard_metric(row: pd.Series) -> str:
    mk = _norm(row.get("metric_key"))
    _, metric, _ = _parse_metric_key(mk)
    if metric:
        return _metric_alias(metric)
    reason = _norm(row.get("block_or_review_reason"))
    if "missing_eps_unit" in reason:
        return "每股收益"
    return ""


def _infer_year(row: pd.Series) -> str:
    mk = _norm(row.get("metric_key"))
    _, _, y = _parse_metric_key(mk)
    if y:
        return y
    return _norm(row.get("year"))


def _infer_proposed_unit(metric: str, raw_reason: str) -> str:
    m = _norm(metric)
    if m in {"每股收益"}:
        return "元/股"
    if m in {"P/E", "P/B", "EV/EBITDA"}:
        return ""
    if m in {"营业收入", "归属母公司净利润"}:
        return "百万元"
    if "missing_eps_unit" in _norm(raw_reason):
        return "元/股"
    return ""


def _classify_one(
    row: pd.Series,
    map06: Dict[str, Dict[str, Any]],
    map2b: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    candidate_id = _norm(row.get("candidate_id"))
    original_reason = _norm(row.get("block_or_review_reason"))
    source_stage = _norm(row.get("source_stage"))
    evidence = _norm(row.get("evidence / source_reference"))
    proposed_value = _norm(row.get("extracted_value / proposed_value"))
    asset = _infer_asset_package(row)
    metric = _infer_standard_metric(row)
    year = _infer_year(row)
    proposed_unit = _infer_proposed_unit(metric, original_reason)

    k = _key(asset, metric, year) if asset and metric and year else ""
    row06 = map06.get(k, {})
    row2b = map2b.get(k, {})
    current_06_key_exists = bool(row06)
    current_02b_key_exists = bool(row2b)

    current_06_value = _norm(row06.get("final_value"))
    current_06_unit = _norm(row06.get("final_unit"))
    current_06_source = _norm(row06.get("final_value_source"))

    conflict_with_existing_override = False
    hard_conflict = False
    metadata_only = False

    if current_02b_key_exists:
        v2b = _norm(row2b.get("final_value"))
        u2b = _norm(row2b.get("final_unit"))
        if not _value_equal(v2b, proposed_value) or _norm(u2b) != _norm(proposed_unit):
            conflict_with_existing_override = True
            hard_conflict = True

    if current_06_key_exists:
        if _value_equal(current_06_value, proposed_value) and _norm(current_06_unit) == _norm(proposed_unit):
            if current_06_source in {"manual_added", "manual_corrected"}:
                metadata_only = True
        else:
            hard_conflict = True

    action = ACTION_NEED_EVIDENCE
    action_reason = "insufficient_key_mapping_or_source_evidence"

    if not evidence:
        action = ACTION_NEED_EVIDENCE
        action_reason = "missing_source_reference_or_evidence"
    elif original_reason == "free_cash_flow_requires_manual_review":
        action = ACTION_REJECT
        action_reason = "non_target_metric_for_stage3_override_first_flow"
    elif not asset or not metric or not year:
        action = ACTION_NEED_EVIDENCE
        action_reason = "cannot_build_asset_metric_year_key"
    elif hard_conflict:
        action = ACTION_NEED_CONFLICT
        action_reason = "proposed_value_or_unit_conflicts_with_existing_02b_or_06"
    elif current_02b_key_exists:
        action = ACTION_COVERED
        action_reason = "key_already_covered_by_02b_override"
    elif current_06_key_exists and metadata_only:
        action = ACTION_COVERED
        action_reason = "metadata_warning_only_same_value_unit_already_in_06"
    elif current_06_key_exists:
        action = ACTION_COVERED
        action_reason = "key_already_covered_in_06_no_business_gap"
    elif original_reason in {"missing_eps_unit", "same_metric_year_already_exists_in_06"}:
        action = ACTION_READY_OVERRIDE
        action_reason = "has_structured_key_and_evidence_ready_for_override_draft"
    elif original_reason == "net_profit_not_auto_mapped_to_parent_net_profit":
        action = ACTION_READY_MANUAL
        action_reason = "requires_manual_alias_confirmation_before_override_draft"
    elif source_stage == "review_before_apply":
        action = ACTION_READY_OVERRIDE
        action_reason = "review_before_apply_candidate_ready_for_override_first_draft"
    elif source_stage in {"merge_conflict", "merge_blocked"}:
        action = ACTION_NEED_CONFLICT
        action_reason = "historical_merge_conflict_needs_override_first_conflict_resolution"

    if action not in ALLOWED_ACTIONS:
        action = ACTION_NEED_EVIDENCE
        action_reason = "fallback_to_allowed_action_set"

    return {
        "candidate_id": candidate_id,
        "asset_package": asset,
        "standard_metric": metric,
        "year": year,
        "proposed_value": proposed_value,
        "proposed_unit": proposed_unit,
        "source_reference / evidence": evidence,
        "original_backlog_reason": original_reason,
        "current_06_key_exists": current_06_key_exists,
        "current_06_value": current_06_value,
        "current_06_unit": current_06_unit,
        "current_06_value_source": current_06_source,
        "current_02B_key_exists": current_02b_key_exists,
        "conflict_with_existing_override": conflict_with_existing_override,
        "metadata_warning_only": metadata_only,
        "hard_conflict": hard_conflict,
        "recommended_stage3_action": action,
        "action_reason": action_reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3A backlog review for override-first repair flow.")
    parser.parse_args()

    snap_before = _snapshot_prod()
    data = _load_inputs()
    backlog = data["backlog"].copy()
    map06, map2b = _build_reference_maps(data["df06"], data["df02b"])

    review_rows = [_classify_one(r, map06, map2b) for _, r in backlog.iterrows()]
    review_df = pd.DataFrame(review_rows)
    review_df = review_df.sort_values(by=["recommended_stage3_action", "asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)

    backlog_candidate_count = len(review_df)
    ready_for_manual_evidence_review_count = int((review_df["recommended_stage3_action"] == ACTION_READY_MANUAL).sum())
    ready_for_override_draft_count = int((review_df["recommended_stage3_action"] == ACTION_READY_OVERRIDE).sum())
    need_conflict_resolution_count = int((review_df["recommended_stage3_action"] == ACTION_NEED_CONFLICT).sum())
    need_source_evidence_count = int((review_df["recommended_stage3_action"] == ACTION_NEED_EVIDENCE).sum())
    reject_candidate_count = int((review_df["recommended_stage3_action"] == ACTION_REJECT).sum())
    already_covered_count = int((review_df["recommended_stage3_action"] == ACTION_COVERED).sum())
    hard_conflict_count = int(review_df["hard_conflict"].sum())

    snap_after = _snapshot_prod()
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before["06"] == snap_after["06"]
    delivery_status = _run_delivery_check()
    stage3a_backlog_review_pass = bool(
        backlog_candidate_count == 17
        and production_files_unchanged
        and output_06_unchanged
        and delivery_status.get("overall_status") == "PASS"
    )

    summary = {
        "backlog_candidate_count": backlog_candidate_count,
        "ready_for_manual_evidence_review_count": ready_for_manual_evidence_review_count,
        "ready_for_override_draft_count": ready_for_override_draft_count,
        "need_conflict_resolution_count": need_conflict_resolution_count,
        "need_source_evidence_count": need_source_evidence_count,
        "reject_candidate_count": reject_candidate_count,
        "already_covered_count": already_covered_count,
        "hard_conflict_count": hard_conflict_count,
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage3a_backlog_review_pass": bool(stage3a_backlog_review_pass),
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
    }

    out_xlsx = STAGE3A_OUT / "85_stage3a_backlog_review.xlsx"
    out_md = STAGE3A_OUT / "85_stage3a_backlog_review.md"
    out_json = STAGE3A_OUT / "86_stage3a_backlog_review_summary.json"

    action_dist = (
        review_df.groupby("recommended_stage3_action", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "recommended_stage3_action"], ascending=[False, True], kind="mergesort")
    )
    conflict_rows = review_df[review_df["hard_conflict"]].copy()
    covered_rows = review_df[review_df["recommended_stage3_action"] == ACTION_COVERED].copy()

    _safe_write_excel_multi(
        {
            "stage3a_review": review_df,
            "summary": pd.DataFrame([summary]),
            "action_distribution": action_dist,
            "hard_conflicts": conflict_rows if not conflict_rows.empty else pd.DataFrame(columns=["candidate_id"]),
            "already_covered": covered_rows if not covered_rows.empty else pd.DataFrame(columns=["candidate_id"]),
        },
        out_xlsx,
    )

    md_lines = [
        "# Stage3A Backlog Review for Override-First Flow",
        "",
        "## Summary",
        f"- backlog_candidate_count: {summary['backlog_candidate_count']}",
        f"- ready_for_manual_evidence_review_count: {summary['ready_for_manual_evidence_review_count']}",
        f"- ready_for_override_draft_count: {summary['ready_for_override_draft_count']}",
        f"- need_conflict_resolution_count: {summary['need_conflict_resolution_count']}",
        f"- need_source_evidence_count: {summary['need_source_evidence_count']}",
        f"- reject_candidate_count: {summary['reject_candidate_count']}",
        f"- already_covered_count: {summary['already_covered_count']}",
        f"- hard_conflict_count: {summary['hard_conflict_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage3a_backlog_review_pass: {summary['stage3a_backlog_review_pass']}",
        "",
        "## Policy Notes",
        "- No candidate is sent to direct 06 real apply in Stage3A.",
        "- `ALREADY_COVERED_BY_02B_OR_06` includes metadata-only warning cases with same value/unit.",
        "- `NEED_CONFLICT_RESOLUTION` is only for value/unit hard conflicts against existing 02B/06 state.",
    ]
    _safe_write_text("\n".join(md_lines), out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3a_review_xlsx: {out_xlsx}")
    print(f"stage3a_review_md: {out_md}")
    print(f"stage3a_summary_json: {out_json}")
    for k in [
        "backlog_candidate_count",
        "ready_for_manual_evidence_review_count",
        "ready_for_override_draft_count",
        "need_conflict_resolution_count",
        "need_source_evidence_count",
        "reject_candidate_count",
        "already_covered_count",
        "hard_conflict_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "stage3a_backlog_review_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
