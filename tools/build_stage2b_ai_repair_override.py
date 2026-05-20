import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OVERRIDE_DIR = BASE_DIR / "data" / "overrides"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _key(asset: Any, metric: Any, year: Any) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str, prefer_no_copy: bool = True) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file pattern: {pattern}")
    if prefer_no_copy:
        filtered = [p for p in files if "_copy_" not in p.name]
        if filtered:
            return filtered[0]
    return files[0]


def _snapshot_prod_files() -> Dict[str, str]:
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
    p = subprocess.run(
        [sys.executable, str(script), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN"}


def _read_inputs() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any], pd.DataFrame, Dict[str, Path]]:
    p68 = DELIVERY_DIR / "68_ai_extract_real_apply_approval_review.xlsx"
    p70 = DELIVERY_DIR / "70_ai_extract_real_apply_log.xlsx"
    p71 = DELIVERY_DIR / "71_ai_extract_real_apply_diff.xlsx"
    p72 = DELIVERY_DIR / "72_ai_extract_real_apply_summary.json"
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")

    if not p68.exists() or not p70.exists() or not p71.exists() or not p72.exists():
        raise FileNotFoundError("Required Stage 1 artifacts missing (68/70/71/72).")

    df68 = pd.read_excel(p68, sheet_name="approval_review")
    df70 = pd.read_excel(p70, sheet_name="apply_log")
    df71 = pd.read_excel(p71, sheet_name="real_apply_diff")
    s72 = json.loads(p72.read_text(encoding="utf-8"))
    df06 = pd.read_excel(p06)

    paths = {"68": p68, "70": p70, "71": p71, "72": p72, "06": p06}
    return df68, df70, df71, s72, df06, paths


def _build_override(df68: pd.DataFrame, df70: pd.DataFrame, df71: pd.DataFrame, df06: pd.DataFrame, paths: Dict[str, Path]) -> pd.DataFrame:
    approved = df68[df68["review_decision"].astype(str).str.strip().str.lower().isin({"auto_approve", "approved"})].copy()
    if len(approved) != 13:
        raise RuntimeError(f"Expected 13 approved records in 68, got {len(approved)}")

    merged = approved.merge(df70, on="candidate_id", how="left", suffixes=("_68", "_70"))
    merged = merged.merge(df71, on="candidate_id", how="left", suffixes=("", "_71"))

    ai06 = df06[df06["final_value_source"].astype(str).str.strip() == "ai_extract_real_apply"].copy()
    ai06["metric_key"] = ai06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    ai06_map = {k: v for k, v in zip(ai06["metric_key"], ai06.to_dict(orient="records"))}

    rows: List[Dict[str, Any]] = []
    for _, r in merged.iterrows():
        asset = _norm(r.get("target_asset_package"))
        metric = _norm(r.get("metric"))
        year = _norm(r.get("year"))
        metric_key = _key(asset, metric, year)
        from06 = ai06_map.get(metric_key, {})

        candidate_id = _norm(r.get("candidate_id"))
        source_reference = _norm(r.get("source_reference_70")) or _norm(r.get("source_reference_68")) or _norm(r.get("source_reference"))
        evidence = _norm(r.get("review_reason"))
        proposed = _norm(r.get("new_value_68")) or _norm(r.get("new_value_70")) or _norm(r.get("new_value"))
        final_value = _norm(from06.get("final_value")) or proposed
        final_unit = _norm(from06.get("final_unit")) or _norm(r.get("new_unit"))
        final_value_source = _norm(from06.get("final_value_source")) or "ai_extract_real_apply"
        final_review_status = _norm(from06.get("final_review_status")) or "approved_auto_applied"

        rows.append(
            {
                "repair_id": f"STAGE2B_{candidate_id}",
                "candidate_id": candidate_id,
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "final_value": final_value,
                "final_unit": final_unit,
                "final_value_source": final_value_source,
                "final_review_status": final_review_status,
                "evidence": evidence,
                "source_reference": source_reference,
                "approval_review_file": str(paths["68"]),
                "real_apply_log_file": str(paths["70"]),
                "real_apply_diff_file": str(paths["71"]),
                "stage_name": "stage1_extract_positive",
                "apply_batch_id": "stage1_real_apply_20260520",
                "created_from_commit": "f518a10",
                "provenance_status": "REBUILDABLE_INPUT_READY",
            }
        )

    out = pd.DataFrame(rows)
    return out


def _validate(override_df: pd.DataFrame, df68: pd.DataFrame, df06: pd.DataFrame) -> Dict[str, Any]:
    required = [
        "repair_id",
        "candidate_id",
        "asset_package",
        "standard_metric",
        "year",
        "final_value",
        "final_unit",
        "final_value_source",
        "final_review_status",
        "evidence",
        "source_reference",
        "approval_review_file",
        "real_apply_log_file",
        "real_apply_diff_file",
        "stage_name",
        "apply_batch_id",
        "created_from_commit",
        "provenance_status",
    ]
    for c in required:
        if c not in override_df.columns:
            raise RuntimeError(f"Missing required column in override: {c}")

    approved = df68[df68["review_decision"].astype(str).str.strip().str.lower().isin({"auto_approve", "approved"})].copy()
    keys68 = sorted([_key(r.get("target_asset_package"), r.get("metric"), r.get("year")) for _, r in approved.iterrows()])

    ai06 = df06[df06["final_value_source"].astype(str).str.strip() == "ai_extract_real_apply"].copy()
    keys06 = sorted([_key(r.get("asset_package"), r.get("standard_metric"), r.get("year")) for _, r in ai06.iterrows()])

    keys_override = sorted([_key(r.get("asset_package"), r.get("standard_metric"), r.get("year")) for _, r in override_df.iterrows()])

    dup_count = int(pd.Series(keys_override).duplicated().sum())

    missing_required = 0
    for _, r in override_df.iterrows():
        if any(_norm(r.get(c)) == "" for c in ["asset_package", "standard_metric", "year", "final_value"]):
            missing_required += 1
        if _norm(r.get("provenance_status")) != "REBUILDABLE_INPUT_READY":
            missing_required += 1

    return {
        "override_record_count": len(override_df),
        "expected_stage1_record_count": 13,
        "key_match_with_06": keys_override == keys06,
        "key_match_with_approval_review": keys_override == keys68,
        "duplicate_key_count": dup_count,
        "missing_required_field_count": missing_required,
        "keys_only_in_override_not_06": sorted(set(keys_override) - set(keys06)),
        "keys_only_in_06_not_override": sorted(set(keys06) - set(keys_override)),
        "keys_only_in_override_not_68": sorted(set(keys_override) - set(keys68)),
        "keys_only_in_68_not_override": sorted(set(keys68) - set(keys_override)),
    }


def _write_reports(override_df: pd.DataFrame, summary: Dict[str, Any], delivery_status: Dict[str, Any]) -> None:
    report_md = DELIVERY_DIR / "77_stage2b_ai_repair_override_build_report.md"
    report_xlsx = DELIVERY_DIR / "77_stage2b_ai_repair_override_build_report.xlsx"
    report_json = DELIVERY_DIR / "78_stage2b_ai_repair_override_summary.json"

    with pd.ExcelWriter(report_xlsx, engine="openpyxl") as writer:
        override_df.to_excel(writer, sheet_name="override_records", index=False)
        pd.DataFrame([{"field": k, "value": v} for k, v in summary.items()]).to_excel(writer, sheet_name="summary", index=False)
        pd.DataFrame([delivery_status]).to_excel(writer, sheet_name="delivery_check", index=False)

    report_md.write_text(
        "\n".join(
            [
                "# Stage2B AI Repair Override Build Report",
                "",
                f"- override_record_count: {summary['override_record_count']}",
                f"- expected_stage1_record_count: {summary['expected_stage1_record_count']}",
                f"- key_match_with_06: {summary['key_match_with_06']}",
                f"- key_match_with_approval_review: {summary['key_match_with_approval_review']}",
                f"- duplicate_key_count: {summary['duplicate_key_count']}",
                f"- missing_required_field_count: {summary['missing_required_field_count']}",
                f"- production_files_unchanged: {summary['production_files_unchanged']}",
                f"- output_06_unchanged: {summary['output_06_unchanged']}",
                f"- delivery_status_after: {delivery_status.get('overall_status', 'UNKNOWN')}",
            ]
        ),
        encoding="utf-8",
    )

    report_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage2B AI repair override table from Stage1 real-applied records.")
    parser.parse_args()

    snap_before = _snapshot_prod_files()
    df68, df70, df71, _s72, df06, paths = _read_inputs()
    override_df = _build_override(df68, df70, df71, df06, paths)

    OVERRIDE_DIR.mkdir(parents=True, exist_ok=True)
    override_path = OVERRIDE_DIR / "02B_ai_repair_override.xlsx"
    with pd.ExcelWriter(override_path, engine="openpyxl") as writer:
        override_df.to_excel(writer, sheet_name="ai_repair_override", index=False)

    validate = _validate(override_df, df68, df06)

    snap_after = _snapshot_prod_files()
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before["06"] == snap_after["06"]

    delivery_status = _run_delivery_check()

    summary = {
        "override_record_count": validate["override_record_count"],
        "expected_stage1_record_count": validate["expected_stage1_record_count"],
        "key_match_with_06": bool(validate["key_match_with_06"]),
        "key_match_with_approval_review": bool(validate["key_match_with_approval_review"]),
        "duplicate_key_count": int(validate["duplicate_key_count"]),
        "missing_required_field_count": int(validate["missing_required_field_count"]),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage2b_override_ready": bool(
            validate["override_record_count"] == 13
            and validate["key_match_with_06"]
            and validate["key_match_with_approval_review"]
            and validate["duplicate_key_count"] == 0
            and validate["missing_required_field_count"] == 0
            and production_files_unchanged
            and output_06_unchanged
            and delivery_status.get("overall_status") == "PASS"
        ),
    }
    summary["keys_only_in_override_not_06"] = validate["keys_only_in_override_not_06"]
    summary["keys_only_in_06_not_override"] = validate["keys_only_in_06_not_override"]
    summary["keys_only_in_override_not_68"] = validate["keys_only_in_override_not_68"]
    summary["keys_only_in_68_not_override"] = validate["keys_only_in_68_not_override"]
    summary["delivery_status_after"] = delivery_status.get("overall_status", "UNKNOWN")

    _write_reports(override_df, summary, delivery_status)

    print(f"override_path: {override_path}")
    print(f"override_record_count: {summary['override_record_count']}")
    print(f"expected_stage1_record_count: {summary['expected_stage1_record_count']}")
    print(f"key_match_with_06: {summary['key_match_with_06']}")
    print(f"key_match_with_approval_review: {summary['key_match_with_approval_review']}")
    print(f"duplicate_key_count: {summary['duplicate_key_count']}")
    print(f"missing_required_field_count: {summary['missing_required_field_count']}")
    print(f"production_files_unchanged: {summary['production_files_unchanged']}")
    print(f"output_06_unchanged: {summary['output_06_unchanged']}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    print(f"stage2b_override_ready: {summary['stage2b_override_ready']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
