import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
DRAFT_PATH = BASE_DIR / "data" / "overrides" / "drafts" / "03_stage3_ai_repair_override_draft.xlsx"
APPROVAL_XLSX = BASE_DIR / "output" / "stage3f_draft_promotion_approval" / "95_stage3f_draft_promotion_approval.xlsx"
APPROVAL_JSON = BASE_DIR / "output" / "stage3f_draft_promotion_approval" / "96_stage3f_draft_promotion_summary.json"
OUT_DIR = BASE_DIR / "output" / "stage3g_promote_override"
BACKUP_PATH = OUT_DIR / "backup" / "02B_ai_repair_override.before_stage3g.xlsx"


APPROVED_DECISION = "APPROVED_FOR_02B_PROMOTION"


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


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name]
    return non_copy[0] if non_copy else files[0]


def _snapshot_production_hashes() -> Dict[str, str]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p05 = _find_delivery_file("05_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    return {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "05": _sha256(p05),
        "06": _sha256(p06),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
        return {"overall_status": "UNKNOWN"}


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _load_inputs() -> Dict[str, Any]:
    for p in [OFFICIAL_02B_PATH, DRAFT_PATH, APPROVAL_XLSX, APPROVAL_JSON]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    official = pd.read_excel(OFFICIAL_02B_PATH, sheet_name="ai_repair_override").fillna("")
    draft = pd.read_excel(DRAFT_PATH).fillna("")
    approval = pd.read_excel(APPROVAL_XLSX, sheet_name="approval_review").fillna("")
    summary = json.loads(APPROVAL_JSON.read_text(encoding="utf-8"))
    return {
        "official": official,
        "draft": draft,
        "approval": approval,
        "summary": summary,
    }


def _validate_stage3f_gate(summary: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not bool(summary.get("stage3f_approval_ready")):
        errors.append("stage3f_approval_ready must be true")
    if int(summary.get("approved_for_02b_promotion_count", -1)) != 4:
        errors.append("approved_for_02b_promotion_count must be 4")
    if int(summary.get("need_manual_approval_count", -1)) != 0:
        errors.append("need_manual_approval_count must be 0")
    if int(summary.get("reject_promotion_count", -1)) != 0:
        errors.append("reject_promotion_count must be 0")
    if int(summary.get("duplicate_key_count", -1)) != 0:
        errors.append("duplicate_key_count must be 0")
    if int(summary.get("conflict_count", -1)) != 0:
        errors.append("conflict_count must be 0")
    if int(summary.get("hard_blocker_count", -1)) != 0:
        errors.append("hard_blocker_count must be 0")
    return errors


def _build_promoted_rows(
    official_df: pd.DataFrame,
    draft_df: pd.DataFrame,
    approval_df: pd.DataFrame,
    now_ts: str,
) -> Dict[str, Any]:
    approved = approval_df[approval_df["approval_decision"].map(_norm) == APPROVED_DECISION].copy()
    approved["_key"] = approved.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    draft = draft_df.copy()
    draft["_key"] = draft.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)

    official_keys = set(
        official_df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist()
    )
    official_value_unit = {
        _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")): (
            _norm(r.get("final_value")),
            _norm(r.get("final_unit")),
        )
        for _, r in official_df.iterrows()
    }

    rows: List[Dict[str, Any]] = []
    log_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    skipped_rows: List[Dict[str, Any]] = []
    missing_required_field_count = 0

    for _, a in approved.iterrows():
        k = _norm(a.get("_key"))
        d = draft[draft["_key"] == k]
        if d.empty:
            conflict_rows.append(
                {
                    "key": k,
                    "reason": "approved record not found in draft workbook",
                    "approval_decision": _norm(a.get("approval_decision")),
                }
            )
            continue

        dr = d.iloc[0]
        asset = _norm(dr.get("asset_package"))
        metric = _norm(dr.get("standard_metric"))
        year = _norm(dr.get("year"))
        value = _norm(dr.get("final_value"))
        unit = _norm(dr.get("final_unit"))
        evidence = _norm(dr.get("evidence"))
        source_reference = _norm(dr.get("source_reference"))
        candidate_id = _norm(dr.get("candidate_id"))
        draft_repair_id = _norm(dr.get("draft_repair_id"))

        required_missing = [x for x in [asset, metric, year, value, unit] if x == ""]
        if required_missing:
            missing_required_field_count += 1
            conflict_rows.append(
                {
                    "key": k,
                    "reason": "missing required fields in draft record",
                    "candidate_id": candidate_id,
                    "draft_repair_id": draft_repair_id,
                }
            )
            continue

        if k in official_keys:
            old_val, old_unit = official_value_unit[k]
            if old_val == value and old_unit == unit:
                skipped_rows.append(
                    {
                        "key": k,
                        "candidate_id": candidate_id,
                        "status": "ALREADY_COVERED",
                        "reason": "official 02B already has same key/value/unit",
                    }
                )
                continue
            conflict_rows.append(
                {
                    "key": k,
                    "candidate_id": candidate_id,
                    "status": "CONFLICT",
                    "official_value": old_val,
                    "official_unit": old_unit,
                    "draft_value": value,
                    "draft_unit": unit,
                    "reason": "official 02B already has same key with different value/unit",
                }
            )
            continue

        repair_id = f"STAGE3G_PROMOTED_{candidate_id or draft_repair_id}"
        row = {
            "repair_id": repair_id,
            "candidate_id": candidate_id or draft_repair_id,
            "asset_package": asset,
            "standard_metric": metric,
            "year": year,
            "final_value": value,
            "final_unit": unit,
            "final_value_source": "stage3_ai_repair_override",
            "final_review_status": "approved_promoted",
            "evidence": evidence,
            "source_reference": source_reference,
            "approval_review_file": str(APPROVAL_XLSX),
            "real_apply_log_file": "",
            "real_apply_diff_file": "",
            "stage_name": "stage3_draft_override_promotion",
            "apply_batch_id": f"stage3g_promote_{now_ts}",
            "created_from_commit": "",
            "provenance_status": "PROMOTED_TO_OFFICIAL_02B",
        }
        rows.append(row)
        log_rows.append(
            {
                "key": k,
                "repair_id": repair_id,
                "candidate_id": candidate_id,
                "status": "PROMOTED",
                "reason": "approved in stage3f and inserted into official 02B",
            }
        )

    return {
        "promoted_rows": rows,
        "promotion_log": log_rows,
        "conflicts": conflict_rows,
        "skipped": skipped_rows,
        "missing_required_field_count": missing_required_field_count,
    }


def _ensure_no_duplicate_key(df: pd.DataFrame) -> int:
    keys = df.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    return int(keys.duplicated().sum())


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3G promote approved draft overrides into official 02B.")
    parser.parse_args()

    now_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    production_before = _snapshot_production_hashes()
    official_02b_before_hash = _sha256(OFFICIAL_02B_PATH)
    data = _load_inputs()

    gate_errors = _validate_stage3f_gate(data["summary"])
    if gate_errors:
        raise RuntimeError("Stage3F gate check failed: " + "; ".join(gate_errors))

    official_before = data["official"].copy()
    official_02b_record_count_before = len(official_before)
    if official_02b_record_count_before != 13:
        raise RuntimeError(f"official_02b_record_count_before expected 13, got {official_02b_record_count_before}")

    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OFFICIAL_02B_PATH, BACKUP_PATH)
    backup_hash = _sha256(BACKUP_PATH)

    build = _build_promoted_rows(
        official_df=official_before,
        draft_df=data["draft"],
        approval_df=data["approval"],
        now_ts=now_ts,
    )
    promoted_rows = build["promoted_rows"]
    conflict_rows = build["conflicts"]
    skipped_rows = build["skipped"]
    promotion_log = build["promotion_log"]
    missing_required_field_count = int(build["missing_required_field_count"])

    promoted_record_count = len(promoted_rows)
    conflict_count = len(conflict_rows)
    if promoted_record_count != 4:
        raise RuntimeError(f"promoted_record_count expected 4, got {promoted_record_count}")
    if conflict_count != 0:
        raise RuntimeError(f"conflict_count expected 0, got {conflict_count}")
    if missing_required_field_count != 0:
        raise RuntimeError(f"missing_required_field_count expected 0, got {missing_required_field_count}")

    combined = pd.concat([official_before, pd.DataFrame(promoted_rows)], ignore_index=True)
    duplicate_key_count = _ensure_no_duplicate_key(combined)
    if duplicate_key_count != 0:
        raise RuntimeError(f"duplicate_key_count expected 0, got {duplicate_key_count}")

    promoted_df = pd.DataFrame(promoted_rows)
    required_cols = ["asset_package", "standard_metric", "year", "final_value", "final_unit"]
    null_required = 0
    for col in required_cols:
        null_required += int(promoted_df[col].map(_norm).eq("").sum())
    if null_required != 0:
        raise RuntimeError(f"promoted required fields empty count expected 0, got {null_required}")

    official_after = combined.copy()
    official_02b_record_count_after = len(official_after)
    if official_02b_record_count_after != 17:
        raise RuntimeError(f"official_02b_record_count_after expected 17, got {official_02b_record_count_after}")

    with pd.ExcelWriter(OFFICIAL_02B_PATH, engine="openpyxl") as writer:
        official_after.to_excel(writer, sheet_name="ai_repair_override", index=False)

    official_02b_after_hash = _sha256(OFFICIAL_02B_PATH)
    official_02B_changed = official_02b_before_hash != official_02b_after_hash
    if not official_02B_changed:
        raise RuntimeError("official 02B hash unchanged after promotion write")

    production_after = _snapshot_production_hashes()
    production_01_unchanged = production_before["01"] == production_after["01"]
    production_02_unchanged = production_before["02"] == production_after["02"]
    production_02A_unchanged = production_before["02A"] == production_after["02A"]
    production_05_unchanged = production_before["05"] == production_after["05"]
    production_06_unchanged = production_before["06"] == production_after["06"]
    output_06_unchanged = production_06_unchanged

    delivery_status = _run_delivery_check().get("overall_status", "UNKNOWN")

    stage3g_promotion_pass = bool(
        official_02b_record_count_before == 13
        and promoted_record_count == 4
        and official_02b_record_count_after == 17
        and duplicate_key_count == 0
        and conflict_count == 0
        and missing_required_field_count == 0
        and official_02B_changed
        and production_01_unchanged
        and production_02_unchanged
        and production_02A_unchanged
        and production_05_unchanged
        and production_06_unchanged
        and output_06_unchanged
        and delivery_status == "PASS"
    )

    summary = {
        "official_02b_record_count_before": int(official_02b_record_count_before),
        "promoted_record_count": int(promoted_record_count),
        "official_02b_record_count_after": int(official_02b_record_count_after),
        "duplicate_key_count": int(duplicate_key_count),
        "conflict_count": int(conflict_count),
        "missing_required_field_count": int(missing_required_field_count),
        "official_02B_changed": bool(official_02B_changed),
        "production_01_unchanged": bool(production_01_unchanged),
        "production_02_unchanged": bool(production_02_unchanged),
        "production_02A_unchanged": bool(production_02A_unchanged),
        "production_05_unchanged": bool(production_05_unchanged),
        "production_06_unchanged": bool(production_06_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage3g_promotion_pass": bool(stage3g_promotion_pass),
        "delivery_status_after": delivery_status,
        "official_02b_hash_before": official_02b_before_hash,
        "official_02b_hash_after": official_02b_after_hash,
        "official_02b_backup_hash": backup_hash,
        "backup_file": str(BACKUP_PATH),
    }

    out_xlsx = OUT_DIR / "97_stage3g_02b_promotion_log.xlsx"
    out_md = OUT_DIR / "97_stage3g_02b_promotion_log.md"
    out_json = OUT_DIR / "98_stage3g_02b_promotion_summary.json"

    _safe_write_excel_multi(
        {
            "promotion_log": pd.DataFrame(promotion_log),
            "promoted_rows": pd.DataFrame(promoted_rows),
            "conflicts": pd.DataFrame(conflict_rows),
            "skipped": pd.DataFrame(skipped_rows),
            "summary": pd.DataFrame([summary]),
        },
        out_xlsx,
    )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(
        "\n".join(
            [
                "# Stage3G 02B Promotion Log",
                "",
                f"- official_02b_record_count_before: {summary['official_02b_record_count_before']}",
                f"- promoted_record_count: {summary['promoted_record_count']}",
                f"- official_02b_record_count_after: {summary['official_02b_record_count_after']}",
                f"- duplicate_key_count: {summary['duplicate_key_count']}",
                f"- conflict_count: {summary['conflict_count']}",
                f"- missing_required_field_count: {summary['missing_required_field_count']}",
                f"- official_02B_changed: {summary['official_02B_changed']}",
                f"- production_01_unchanged: {summary['production_01_unchanged']}",
                f"- production_02_unchanged: {summary['production_02_unchanged']}",
                f"- production_02A_unchanged: {summary['production_02A_unchanged']}",
                f"- production_05_unchanged: {summary['production_05_unchanged']}",
                f"- production_06_unchanged: {summary['production_06_unchanged']}",
                f"- output_06_unchanged: {summary['output_06_unchanged']}",
                f"- stage3g_promotion_pass: {summary['stage3g_promotion_pass']}",
                f"- delivery_status_after: {summary['delivery_status_after']}",
                f"- backup_file: {summary['backup_file']}",
            ]
        ),
        encoding="utf-8",
    )
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3g_log_xlsx: {out_xlsx}")
    print(f"stage3g_log_md: {out_md}")
    print(f"stage3g_summary_json: {out_json}")
    for k in [
        "official_02b_record_count_before",
        "promoted_record_count",
        "official_02b_record_count_after",
        "duplicate_key_count",
        "conflict_count",
        "missing_required_field_count",
        "official_02B_changed",
        "production_01_unchanged",
        "production_02_unchanged",
        "production_02A_unchanged",
        "production_05_unchanged",
        "production_06_unchanged",
        "output_06_unchanged",
        "stage3g_promotion_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
