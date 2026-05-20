import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
STAGE3A_DIR = BASE_DIR / "output" / "stage3a_backlog_review"
STAGE3B_DIR = BASE_DIR / "output" / "stage3b_override_draft_review"

P85 = STAGE3A_DIR / "85_stage3a_backlog_review.xlsx"
P86 = STAGE3A_DIR / "86_stage3a_backlog_review_summary.json"
P75 = DELIVERY_DIR / "75_stage1b_backlog_inventory.xlsx"
P02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

ACTION_MANUAL = "READY_FOR_MANUAL_EVIDENCE_REVIEW"
ACTION_OVERRIDE = "READY_FOR_OVERRIDE_DRAFT"

DEC_APPROVED = "APPROVED_FOR_OVERRIDE_DRAFT"
DEC_NEED_MANUAL = "NEED_MANUAL_CONFIRMATION"
DEC_REJECT = "REJECT_AFTER_REVIEW"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _key(asset: Any, metric: Any, year: Any) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _parse_number(text: str):
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


def _value_equal(v1: Any, v2: Any) -> bool:
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
    return {"01": _sha256(p01), "02": _sha256(p02), "02A": _sha256(p02a), "06": _sha256(p06)}


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


def _load_inputs():
    if not P85.exists():
        raise FileNotFoundError(f"Missing input: {P85}")
    if not P86.exists():
        raise FileNotFoundError(f"Missing input: {P86}")
    if not P75.exists():
        raise FileNotFoundError(f"Missing input: {P75}")
    if not P02B.exists():
        raise FileNotFoundError(f"Missing input: {P02B}")

    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    stage3a = pd.read_excel(P85, sheet_name="stage3a_review").fillna("")
    summary86 = json.loads(P86.read_text(encoding="utf-8"))
    backlog75 = pd.read_excel(P75, sheet_name="backlog_inventory").fillna("")
    df06 = pd.read_excel(p06).fillna("")
    df02b = pd.read_excel(P02B, sheet_name="ai_repair_override").fillna("")
    return stage3a, summary86, backlog75, df06, df02b


def _build_maps(df06: pd.DataFrame, df02b: pd.DataFrame, backlog75: pd.DataFrame):
    d06 = df06.copy()
    d06["_key"] = d06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    map06 = {}
    for _, r in d06.iterrows():
        map06[_norm(r["_key"])] = {
            "value": _norm(r.get("final_value")),
            "unit": _norm(r.get("final_unit")),
            "source": _norm(r.get("final_value_source")),
        }

    d2b = df02b.copy()
    d2b["_key"] = d2b.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    map2b = {}
    for _, r in d2b.iterrows():
        map2b[_norm(r["_key"])] = {
            "value": _norm(r.get("final_value")),
            "unit": _norm(r.get("final_unit")),
            "candidate_id": _norm(r.get("candidate_id")),
        }

    map75 = {}
    for _, r in backlog75.iterrows():
        map75[_norm(r.get("candidate_id"))] = {
            "evidence": _norm(r.get("evidence / source_reference")),
            "raw_proposed_value": _norm(r.get("extracted_value / proposed_value")),
        }
    return map06, map2b, map75


def _decide_row(r: pd.Series, map06: Dict[str, Dict[str, str]], map2b: Dict[str, Dict[str, str]], map75: Dict[str, Dict[str, str]]):
    candidate_id = _norm(r.get("candidate_id"))
    asset = _norm(r.get("asset_package"))
    metric = _norm(r.get("standard_metric"))
    year = _norm(r.get("year"))
    proposed_value = _norm(r.get("proposed_value"))
    proposed_unit = _norm(r.get("proposed_unit"))
    stage3a_action = _norm(r.get("recommended_stage3_action"))
    source_evidence = _norm(r.get("source_reference / evidence"))
    if not source_evidence and candidate_id in map75:
        source_evidence = _norm(map75[candidate_id].get("evidence"))

    k = _key(asset, metric, year)
    r06 = map06.get(k, {})
    r2b = map2b.get(k, {})
    current_06_exists = bool(r06)
    current_02b_exists = bool(r2b)
    current_06_value = _norm(r06.get("value"))
    current_06_unit = _norm(r06.get("unit"))

    decision = DEC_APPROVED
    reason = "complete_fields_and_evidence_ready_for_override_draft"

    if not source_evidence:
        decision = DEC_NEED_MANUAL
        reason = "missing_source_reference_or_evidence"
    elif not proposed_value:
        decision = DEC_REJECT
        reason = "proposed_value_empty_after_review"
    elif current_06_exists and current_06_unit and proposed_unit and _norm(current_06_unit) != _norm(proposed_unit):
        decision = DEC_NEED_MANUAL
        reason = "unit_differs_from_current_06_needs_manual_confirmation"
    elif current_06_exists and _value_equal(current_06_value, proposed_value) and _norm(current_06_unit) == _norm(proposed_unit):
        decision = DEC_REJECT
        reason = "already_covered_same_key_same_value_same_unit_in_06"
    elif current_02b_exists and _value_equal(_norm(r2b.get("value")), proposed_value) and _norm(_norm(r2b.get("unit"))) == _norm(proposed_unit):
        decision = DEC_REJECT
        reason = "already_covered_same_key_same_value_same_unit_in_02b"
    elif stage3a_action == ACTION_MANUAL:
        decision = DEC_NEED_MANUAL
        reason = "stage3a_requires_manual_evidence_confirmation_before_override_draft"
    elif stage3a_action == ACTION_OVERRIDE:
        decision = DEC_APPROVED
        reason = "stage3a_ready_for_override_draft_and_no_blocking_rule_hit"

    return {
        "candidate_id": candidate_id,
        "asset_package": asset,
        "standard_metric": metric,
        "year": year,
        "proposed_value": proposed_value,
        "proposed_unit": proposed_unit,
        "source_reference": source_evidence,
        "evidence": source_evidence,
        "current_06_key_exists": current_06_exists,
        "current_06_value": current_06_value,
        "current_02B_key_exists": current_02b_exists,
        "stage3a_action": stage3a_action,
        "stage3b_decision": decision,
        "stage3b_reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3B review for override draft candidates (exclude hard conflicts).")
    parser.parse_args()

    snap_before = _snapshot_prod()
    stage3a, summary86, backlog75, df06, df02b = _load_inputs()
    map06, map2b, map75 = _build_maps(df06, df02b, backlog75)

    process_mask = stage3a["recommended_stage3_action"].isin([ACTION_MANUAL, ACTION_OVERRIDE])
    process_df = stage3a[process_mask].copy().reset_index(drop=True)

    review_rows = [_decide_row(r, map06, map2b, map75) for _, r in process_df.iterrows()]
    review_df = pd.DataFrame(review_rows)
    review_df = review_df.sort_values(by=["stage3b_decision", "asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)

    input_candidate_count = len(review_df)
    approved_for_override_draft_count = int((review_df["stage3b_decision"] == DEC_APPROVED).sum())
    need_manual_confirmation_count = int((review_df["stage3b_decision"] == DEC_NEED_MANUAL).sum())
    reject_after_review_count = int((review_df["stage3b_decision"] == DEC_REJECT).sum())
    excluded_conflict_candidate_count = int(summary86.get("need_conflict_resolution_count", 0))

    snap_after = _snapshot_prod()
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before["06"] == snap_after["06"]
    delivery_status = _run_delivery_check()
    stage3b_review_pass = bool(
        input_candidate_count == 8
        and excluded_conflict_candidate_count == 4
        and production_files_unchanged
        and output_06_unchanged
        and delivery_status.get("overall_status") == "PASS"
    )

    summary = {
        "input_candidate_count": input_candidate_count,
        "approved_for_override_draft_count": approved_for_override_draft_count,
        "need_manual_confirmation_count": need_manual_confirmation_count,
        "reject_after_review_count": reject_after_review_count,
        "excluded_conflict_candidate_count": excluded_conflict_candidate_count,
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage3b_review_pass": bool(stage3b_review_pass),
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
    }

    out_xlsx = STAGE3B_DIR / "87_stage3b_override_draft_review.xlsx"
    out_md = STAGE3B_DIR / "87_stage3b_override_draft_review.md"
    out_json = STAGE3B_DIR / "88_stage3b_override_draft_review_summary.json"

    decision_dist = (
        review_df.groupby("stage3b_decision", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(by=["count", "stage3b_decision"], ascending=[False, True], kind="mergesort")
    )

    _safe_write_excel_multi(
        {
            "stage3b_review": review_df,
            "summary": pd.DataFrame([summary]),
            "decision_distribution": decision_dist,
        },
        out_xlsx,
    )

    md = [
        "# Stage3B Override Draft Review",
        "",
        "## Summary",
        f"- input_candidate_count: {summary['input_candidate_count']}",
        f"- approved_for_override_draft_count: {summary['approved_for_override_draft_count']}",
        f"- need_manual_confirmation_count: {summary['need_manual_confirmation_count']}",
        f"- reject_after_review_count: {summary['reject_after_review_count']}",
        f"- excluded_conflict_candidate_count: {summary['excluded_conflict_candidate_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage3b_review_pass: {summary['stage3b_review_pass']}",
    ]
    _safe_write_text("\n".join(md), out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3b_review_xlsx: {out_xlsx}")
    print(f"stage3b_review_md: {out_md}")
    print(f"stage3b_summary_json: {out_json}")
    for k in [
        "input_candidate_count",
        "approved_for_override_draft_count",
        "need_manual_confirmation_count",
        "reject_after_review_count",
        "excluded_conflict_candidate_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "stage3b_review_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
