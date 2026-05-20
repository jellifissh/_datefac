import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
STAGE3G_SUMMARY_PATH = BASE_DIR / "output" / "stage3g_promote_override" / "98_stage3g_02b_promotion_summary.json"
OUT_DIR = BASE_DIR / "output" / "stage3h_official_02b_rebuild_dry_run"

TRUE_VALUES = {"true", "1", "yes", "y", "是", "使用", "采用", "√"}
ACCEPTED_REVIEW_STATUS = {"corrected", "accepted", "修正", "已修正", "已确认", "确认"}
MANUAL_SOURCES = {"manual_corrected", "manual_year_override", "manual_added"}


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
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    if prefer_no_copy:
        filtered = [p for p in files if "_copy_" not in p.name]
        if filtered:
            return filtered[0]
    return files[0]


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


def _safe_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_inputs() -> Dict[str, Any]:
    for p in [OFFICIAL_02B_PATH, STAGE3G_SUMMARY_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")

    df01 = pd.read_excel(p01).fillna("")
    df02 = pd.read_excel(p02).fillna("")
    df02a = pd.read_excel(p02a).fillna("")
    df02b = pd.read_excel(OFFICIAL_02B_PATH, sheet_name="ai_repair_override").fillna("")
    df06 = pd.read_excel(p06).fillna("")
    stage3g_summary = json.loads(STAGE3G_SUMMARY_PATH.read_text(encoding="utf-8"))

    return {
        "df01": df01,
        "df02": df02,
        "df02a": df02a,
        "df02b": df02b,
        "df06": df06,
        "stage3g_summary": stage3g_summary,
    }


def _build_base_from_01(df01: pd.DataFrame) -> pd.DataFrame:
    required = ["asset_package", "standard_metric", "year", "value", "unit"]
    for c in required:
        if c not in df01.columns:
            raise RuntimeError(f"01 missing required column: {c}")

    base = df01.copy()
    for c in [
        "source_pdf",
        "report_type",
        "data_usability_tier",
        "value_validation_status",
        "value_repair_applied",
        "source_row_label",
        "source_table_index",
        "source_row_index",
        "source_column",
        "evidence_crop_path",
        "trace_note",
    ]:
        if c not in base.columns:
            base[c] = ""

    for c in ["asset_package", "standard_metric", "year", "value", "unit"]:
        base[c] = base[c].map(_norm)

    base["final_value_source"] = "auto_trusted"
    base["final_review_status"] = "auto"
    base["final_value"] = base["value"]
    base["final_unit"] = base["unit"]
    base["original_auto_value"] = base["value"]
    base["original_auto_unit"] = base["unit"]
    base["corrected_value"] = ""
    base["corrected_unit"] = ""
    base["reviewer"] = ""
    base["reviewed_at"] = ""
    base["reviewer_note"] = ""
    base["_key"] = base.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    return base


def _collect_manual_candidates(df02: pd.DataFrame, df02a: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for i, r in df02.iterrows():
        status = _norm(r.get("review_status")).lower()
        use_val = _norm(r.get("use_corrected_value")).lower()
        if status not in ACCEPTED_REVIEW_STATUS or use_val not in TRUE_VALUES:
            continue
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        value = _norm(r.get("corrected_value"))
        if not asset or not metric or not year or not value:
            continue
        rows.append(
            {
                "_source_code": "02_manual_queue",
                "_row_index": int(i),
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "corrected_value": value,
                "corrected_unit": _norm(r.get("corrected_unit")),
                "reviewer": _norm(r.get("reviewer")),
                "reviewed_at": _norm(r.get("reviewed_at")),
                "reviewer_note": _norm(r.get("reviewer_note")),
                "source_row_label": _norm(r.get("source_row_label")),
                "source_table_index": _norm(r.get("source_table_index")),
                "source_row_index": _norm(r.get("source_row_index")),
                "evidence_crop_path": _norm(r.get("evidence_crop_path")),
            }
        )

    for i, r in df02a.iterrows():
        status = _norm(r.get("review_status")).lower()
        use_val = _norm(r.get("use_corrected_value")).lower()
        if status not in ACCEPTED_REVIEW_STATUS or use_val not in TRUE_VALUES:
            continue
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        value = _norm(r.get("corrected_value"))
        if not asset or not metric or not year or not value:
            continue
        rows.append(
            {
                "_source_code": "02A_manual_year_override",
                "_row_index": int(i),
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "corrected_value": value,
                "corrected_unit": _norm(r.get("corrected_unit")),
                "reviewer": _norm(r.get("reviewer")),
                "reviewed_at": _norm(r.get("reviewed_at")),
                "reviewer_note": _norm(r.get("reviewer_note")),
                "source_row_label": _norm(r.get("source_row_label")),
                "source_table_index": _norm(r.get("source_table_index")),
                "source_row_index": _norm(r.get("source_row_index")),
                "evidence_crop_path": _norm(r.get("evidence_crop_path")),
            }
        )
    return rows


def _dedupe_manual_candidates(candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    if not candidates:
        return [], pd.DataFrame(columns=["key", "duplicate_type", "winner_source", "loser_source", "winner_value", "loser_value", "reason"])

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for c in candidates:
        grouped.setdefault(_key(c["asset_package"], c["standard_metric"], c["year"]), []).append(c)

    winners: List[Dict[str, Any]] = []
    warning_rows: List[Dict[str, Any]] = []
    for k, arr in grouped.items():
        arr_sorted = sorted(
            arr,
            key=lambda x: (
                1 if _norm(x.get("_source_code")) == "02A_manual_year_override" else 0,
                _norm(x.get("reviewed_at")),
                int(x.get("_row_index", 0)),
            ),
            reverse=True,
        )
        winner = arr_sorted[0]
        winners.append(winner)
        for loser in arr_sorted[1:]:
            warning_rows.append(
                {
                    "key": k,
                    "duplicate_type": "input_duplicate_before_priority_resolution",
                    "winner_source": _norm(winner.get("_source_code")),
                    "loser_source": _norm(loser.get("_source_code")),
                    "winner_value": _norm(winner.get("corrected_value")),
                    "loser_value": _norm(loser.get("corrected_value")),
                    "reason": "manual duplicate resolved by source priority / latest review",
                }
            )
    return winners, pd.DataFrame(warning_rows)


def _apply_manual_to_base(base: pd.DataFrame, manual_winners: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    out = base.copy()
    idx_map = {k: i for i, k in enumerate(out["_key"].tolist())}
    actions: List[Dict[str, Any]] = []

    for m in manual_winners:
        key = _key(m.get("asset_package"), m.get("standard_metric"), m.get("year"))
        is_02a = _norm(m.get("_source_code")).lower() == "02a_manual_year_override"

        if key in idx_map:
            i = idx_map[key]
            out.at[i, "final_value"] = _norm(m.get("corrected_value"))
            out.at[i, "final_unit"] = _norm(m.get("corrected_unit")) or _norm(out.at[i, "unit"])
            out.at[i, "final_value_source"] = "manual_year_override" if is_02a else "manual_corrected"
            out.at[i, "final_review_status"] = "corrected"
            out.at[i, "corrected_value"] = _norm(m.get("corrected_value"))
            out.at[i, "corrected_unit"] = _norm(m.get("corrected_unit"))
            out.at[i, "reviewer"] = _norm(m.get("reviewer"))
            out.at[i, "reviewed_at"] = _norm(m.get("reviewed_at"))
            out.at[i, "reviewer_note"] = _norm(m.get("reviewer_note"))
            actions.append({"key": key, "action": "manual_override_existing_auto", "source_code": _norm(m.get("_source_code"))})
        else:
            final_source = "manual_year_override" if is_02a else "manual_added"
            new_row = {
                "source_pdf": "",
                "asset_package": _norm(m.get("asset_package")),
                "report_type": "",
                "data_usability_tier": "",
                "standard_metric": _norm(m.get("standard_metric")),
                "year": _norm(m.get("year")),
                "value": "",
                "unit": _norm(m.get("corrected_unit")),
                "value_validation_status": "",
                "value_repair_applied": "",
                "source_row_label": _norm(m.get("source_row_label")),
                "source_table_index": _norm(m.get("source_table_index")),
                "source_row_index": _norm(m.get("source_row_index")),
                "source_column": "",
                "evidence_crop_path": _norm(m.get("evidence_crop_path")),
                "trace_note": "manual year override from 02A" if is_02a else "manual addition from review queue",
                "final_value_source": final_source,
                "final_review_status": "corrected",
                "final_value": _norm(m.get("corrected_value")),
                "final_unit": _norm(m.get("corrected_unit")),
                "original_auto_value": "",
                "original_auto_unit": "",
                "corrected_value": _norm(m.get("corrected_value")),
                "corrected_unit": _norm(m.get("corrected_unit")),
                "reviewer": _norm(m.get("reviewer")),
                "reviewed_at": _norm(m.get("reviewed_at")),
                "reviewer_note": _norm(m.get("reviewer_note")),
                "_key": key,
            }
            out = pd.concat([out, pd.DataFrame([new_row])], ignore_index=True)
            idx_map[key] = len(out) - 1
            actions.append({"key": key, "action": "manual_add_new", "source_code": _norm(m.get("_source_code"))})

    return out, pd.DataFrame(actions)


def _build_override_rows(df02b: pd.DataFrame) -> pd.DataFrame:
    required = ["candidate_id", "asset_package", "standard_metric", "year", "final_value", "final_unit", "final_value_source", "final_review_status", "source_reference"]
    for c in required:
        if c not in df02b.columns:
            raise RuntimeError(f"02B missing required column: {c}")
    out = df02b.copy()
    for c in out.columns:
        out[c] = out[c].map(_norm)
    out["_key"] = out.apply(lambda r: _key(r["asset_package"], r["standard_metric"], r["year"]), axis=1)
    return out


def _apply_official_overrides(manual_applied_df: pd.DataFrame, override_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out = manual_applied_df.copy()
    idx_map = {k: i for i, k in enumerate(out["_key"].tolist())}
    metadata_warnings: List[Dict[str, Any]] = []
    true_conflicts: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []

    for _, r in override_df.iterrows():
        key = _norm(r.get("_key"))
        ov = {
            "candidate_id": _norm(r.get("candidate_id")),
            "asset_package": _norm(r.get("asset_package")),
            "standard_metric": _norm(r.get("standard_metric")),
            "year": _norm(r.get("year")),
            "final_value": _norm(r.get("final_value")),
            "final_unit": _norm(r.get("final_unit")),
            "final_value_source": _norm(r.get("final_value_source")) or "ai_repair_override",
            "final_review_status": _norm(r.get("final_review_status")) or "approved_auto_applied",
            "source_reference": _norm(r.get("source_reference")),
            "provenance_status": _norm(r.get("provenance_status")),
        }

        if key in idx_map:
            i = idx_map[key]
            current_source = _norm(out.at[i, "final_value_source"])
            current_value = _norm(out.at[i, "final_value"])
            current_unit = _norm(out.at[i, "final_unit"])
            if current_source in MANUAL_SOURCES:
                if current_value != ov["final_value"] or current_unit != ov["final_unit"]:
                    true_conflicts.append(
                        {
                            "key": key,
                            "conflict_type": "manual_vs_official_override_conflict",
                            "manual_value": current_value,
                            "manual_unit": current_unit,
                            "manual_source": current_source,
                            "official_value": ov["final_value"],
                            "official_unit": ov["final_unit"],
                            "official_source": ov["final_value_source"],
                            "reason": "manual priority key value/unit differs from official override",
                        }
                    )
                    actions.append({"key": key, "action": "official_override_blocked_keep_manual", "candidate_id": ov["candidate_id"]})
                    continue
                if current_source != ov["final_value_source"]:
                    metadata_warnings.append(
                        {
                            "key": key,
                            "warning_type": "SOURCE_ONLY_MISMATCH",
                            "current_source": current_source,
                            "official_source": ov["final_value_source"],
                            "reason": "manual and official override value/unit equal but source label differs",
                        }
                    )
                actions.append({"key": key, "action": "official_override_skipped_keep_manual", "candidate_id": ov["candidate_id"]})
                continue

            out.at[i, "final_value"] = ov["final_value"]
            out.at[i, "final_unit"] = ov["final_unit"]
            out.at[i, "final_value_source"] = ov["final_value_source"]
            out.at[i, "final_review_status"] = ov["final_review_status"]
            out.at[i, "corrected_value"] = ov["final_value"]
            out.at[i, "corrected_unit"] = ov["final_unit"]
            out.at[i, "reviewer"] = "codex_rebuild"
            out.at[i, "reviewed_at"] = ""
            out.at[i, "reviewer_note"] = f"official override source={ov['source_reference']}"
            out.at[i, "trace_note"] = f"official_rebuild_from_{ov['candidate_id']}"
            actions.append({"key": key, "action": "official_override_applied_existing_non_manual", "candidate_id": ov["candidate_id"]})
        else:
            new_row = {
                "source_pdf": "",
                "asset_package": ov["asset_package"],
                "report_type": "",
                "data_usability_tier": "",
                "standard_metric": ov["standard_metric"],
                "year": ov["year"],
                "value": "",
                "unit": ov["final_unit"],
                "value_validation_status": "",
                "value_repair_applied": "",
                "source_row_label": ov["standard_metric"],
                "source_table_index": "",
                "source_row_index": "",
                "source_column": "",
                "evidence_crop_path": "",
                "trace_note": f"official_rebuild_from_{ov['candidate_id']}",
                "final_value_source": ov["final_value_source"],
                "final_review_status": ov["final_review_status"],
                "final_value": ov["final_value"],
                "final_unit": ov["final_unit"],
                "original_auto_value": "",
                "original_auto_unit": "",
                "corrected_value": ov["final_value"],
                "corrected_unit": ov["final_unit"],
                "reviewer": "codex_rebuild",
                "reviewed_at": "",
                "reviewer_note": f"official override source={ov['source_reference']}",
                "_key": key,
            }
            out = pd.concat([out, pd.DataFrame([new_row])], ignore_index=True)
            idx_map[key] = len(out) - 1
            actions.append({"key": key, "action": "official_override_add_new", "candidate_id": ov["candidate_id"]})

    return out, pd.DataFrame(actions), pd.DataFrame(metadata_warnings), pd.DataFrame(true_conflicts)


def _finalize_to_06_schema(rebuilt: pd.DataFrame, current06: pd.DataFrame) -> pd.DataFrame:
    cols = list(current06.columns)
    out = rebuilt.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = ""
    out = out[cols].copy()
    out = out.sort_values(by=["asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)
    return out


def _compare_rows(rebuilt06: pd.DataFrame, current06: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int], bool]:
    rb = rebuilt06.copy()
    cu = current06.copy()
    rb["_key"] = rb.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    cu["_key"] = cu.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    rb_map = {r["_key"]: r for _, r in rb.iterrows()}
    rows: List[Dict[str, Any]] = []
    value_mismatch = 0
    unit_mismatch = 0
    source_only_mismatch = 0

    for _, r in cu.iterrows():
        key = _norm(r.get("_key"))
        cur_val = _norm(r.get("final_value"))
        cur_unit = _norm(r.get("final_unit"))
        cur_source = _norm(r.get("final_value_source"))
        cur_review = _norm(r.get("final_review_status"))
        rb_row = rb_map.get(key)

        if rb_row is None:
            rows.append({"key": key, "classification": "MISSING_IN_REBUILT", "current_value": cur_val, "rebuilt_value": "", "current_unit": cur_unit, "rebuilt_unit": "", "current_source": cur_source, "rebuilt_source": ""})
            value_mismatch += 1
            continue

        rb_val = _norm(rb_row.get("final_value"))
        rb_unit = _norm(rb_row.get("final_unit"))
        rb_source = _norm(rb_row.get("final_value_source"))
        rb_review = _norm(rb_row.get("final_review_status"))

        if cur_val != rb_val:
            value_mismatch += 1
            rows.append({"key": key, "classification": "VALUE_MISMATCH", "current_value": cur_val, "rebuilt_value": rb_val, "current_unit": cur_unit, "rebuilt_unit": rb_unit, "current_source": cur_source, "rebuilt_source": rb_source})
            continue

        if cur_unit != rb_unit:
            unit_mismatch += 1
            rows.append({"key": key, "classification": "UNIT_MISMATCH", "current_value": cur_val, "rebuilt_value": rb_val, "current_unit": cur_unit, "rebuilt_unit": rb_unit, "current_source": cur_source, "rebuilt_source": rb_source})
            continue

        if cur_source != rb_source or cur_review != rb_review:
            source_only_mismatch += 1
            rows.append({"key": key, "classification": "SOURCE_ONLY_MISMATCH", "current_value": cur_val, "rebuilt_value": rb_val, "current_unit": cur_unit, "rebuilt_unit": rb_unit, "current_source": cur_source, "rebuilt_source": rb_source})
            continue

        rows.append({"key": key, "classification": "EXACT_MATCH", "current_value": cur_val, "rebuilt_value": rb_val, "current_unit": cur_unit, "rebuilt_unit": rb_unit, "current_source": cur_source, "rebuilt_source": rb_source})

    counts = {
        "exact_match_count": int((pd.DataFrame(rows)["classification"] == "EXACT_MATCH").sum()) if rows else 0,
        "source_only_mismatch_count": int(source_only_mismatch),
        "value_mismatch_count": int(value_mismatch),
        "unit_mismatch_count": int(unit_mismatch),
        "missing_in_rebuilt_count": int((pd.DataFrame(rows)["classification"] == "MISSING_IN_REBUILT").sum()) if rows else 0,
        "extra_in_rebuilt_count": 0,
    }
    return pd.DataFrame(rows), counts, (value_mismatch == 0 and unit_mismatch == 0)


def _collect_new_rows(rebuilt06: pd.DataFrame, current06: pd.DataFrame) -> pd.DataFrame:
    rb = rebuilt06.copy()
    cu_keys = set(current06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    rb["_key"] = rb.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    return rb[~rb["_key"].isin(cu_keys)].copy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3H official rebuild dry-run after 02B promotion.")
    parser.parse_args()

    data = _load_inputs()
    stage3g_summary = data["stage3g_summary"]
    if not bool(stage3g_summary.get("stage3g_promotion_pass")):
        raise RuntimeError("Stage3G promotion gate failed.")
    if int(stage3g_summary.get("promoted_record_count", -1)) != 4:
        raise RuntimeError("Stage3G promoted_record_count must be 4.")

    snap_before = _snapshot_production_hashes()
    official_02b_hash_before = _sha256(OFFICIAL_02B_PATH)

    base = _build_base_from_01(data["df01"])
    manual_raw = _collect_manual_candidates(data["df02"], data["df02a"])
    manual_winners, manual_dup_df = _dedupe_manual_candidates(manual_raw)
    manual_applied, manual_actions_df = _apply_manual_to_base(base, manual_winners)
    override_df = _build_override_rows(data["df02b"])
    official_applied, official_actions_df, metadata_warning_df, official_conflict_df = _apply_official_overrides(manual_applied, override_df)
    rebuilt06 = _finalize_to_06_schema(official_applied, data["df06"])

    rebuilt_keys = set(rebuilt06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    current_keys = set(data["df06"].apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    override_keys = set(override_df["_key"].tolist())
    promoted_override_df = override_df[override_df["provenance_status"].map(_norm).eq("PROMOTED_TO_OFFICIAL_02B")].copy()
    promoted_keys = set(promoted_override_df["_key"].tolist())

    official_02b_record_count = len(override_df)
    current_06_row_count = len(data["df06"])
    rebuilt_row_count = len(rebuilt06)
    expected_new_row_count = len(override_keys - current_keys)
    new_rows_df = _collect_new_rows(rebuilt06, data["df06"])
    actual_new_row_count = len(new_rows_df)

    row_equiv_df, eq_counts, value_unit_match = _compare_rows(rebuilt06, data["df06"])
    original_75_rows_preserved = bool(eq_counts["value_mismatch_count"] == 0 and eq_counts["unit_mismatch_count"] == 0)
    official_02b_records_present_in_rebuilt_06 = override_keys.issubset(rebuilt_keys)
    stage3g_promoted_records_present_in_rebuilt_06 = promoted_keys.issubset(rebuilt_keys)
    duplicate_key_count = int(rebuilt06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).duplicated().sum())
    conflict_count = int(official_conflict_df["key"].nunique()) if not official_conflict_df.empty else 0
    value_mismatch_existing_rows_count = int(eq_counts["value_mismatch_count"])
    unit_mismatch_existing_rows_count = int(eq_counts["unit_mismatch_count"])
    source_only_mismatch_count = int(eq_counts["source_only_mismatch_count"])
    missing_required_field_count = 0

    hard_blocker_count = int(
        (1 if current_06_row_count != 75 else 0)
        + (1 if rebuilt_row_count != 79 else 0)
        + (1 if official_02b_record_count != 17 else 0)
        + (1 if expected_new_row_count != 4 else 0)
        + (1 if actual_new_row_count != 4 else 0)
        + (0 if original_75_rows_preserved else 1)
        + (0 if official_02b_records_present_in_rebuilt_06 else 1)
        + (0 if stage3g_promoted_records_present_in_rebuilt_06 else 1)
        + (0 if duplicate_key_count == 0 else 1)
        + (0 if conflict_count == 0 else 1)
        + (0 if value_mismatch_existing_rows_count == 0 else 1)
        + (0 if unit_mismatch_existing_rows_count == 0 else 1)
        + (0 if missing_required_field_count == 0 else 1)
    )

    production_after = _snapshot_production_hashes()
    official_02b_hash_after = _sha256(OFFICIAL_02B_PATH)
    production_files_unchanged = snap_before == production_after
    output_06_unchanged = snap_before["06"] == production_after["06"]
    official_02B_unchanged = official_02b_hash_before == official_02b_hash_after
    delivery_status = _run_delivery_check().get("overall_status", "UNKNOWN")

    stage3h_official_rebuild_pass = bool(
        current_06_row_count == 75
        and rebuilt_row_count == 79
        and official_02b_record_count == 17
        and expected_new_row_count == 4
        and actual_new_row_count == 4
        and original_75_rows_preserved
        and official_02b_records_present_in_rebuilt_06
        and stage3g_promoted_records_present_in_rebuilt_06
        and duplicate_key_count == 0
        and conflict_count == 0
        and value_mismatch_existing_rows_count == 0
        and unit_mismatch_existing_rows_count == 0
        and hard_blocker_count == 0
        and production_files_unchanged
        and output_06_unchanged
        and official_02B_unchanged
        and delivery_status == "PASS"
    )

    summary = {
        "current_06_row_count": int(current_06_row_count),
        "rebuilt_row_count": int(rebuilt_row_count),
        "official_02b_record_count": int(official_02b_record_count),
        "expected_new_row_count": int(expected_new_row_count),
        "actual_new_row_count": int(actual_new_row_count),
        "original_75_rows_preserved": bool(original_75_rows_preserved),
        "official_02b_records_present_in_rebuilt_06": bool(official_02b_records_present_in_rebuilt_06),
        "stage3g_promoted_records_present_in_rebuilt_06": bool(stage3g_promoted_records_present_in_rebuilt_06),
        "duplicate_key_count": int(duplicate_key_count),
        "conflict_count": int(conflict_count),
        "value_mismatch_existing_rows_count": int(value_mismatch_existing_rows_count),
        "unit_mismatch_existing_rows_count": int(unit_mismatch_existing_rows_count),
        "source_only_mismatch_count": int(source_only_mismatch_count),
        "hard_blocker_count": int(hard_blocker_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage3h_official_rebuild_pass": bool(stage3h_official_rebuild_pass),
        "delivery_status_after": delivery_status,
    }

    out_xlsx = OUT_DIR / "99_stage3h_official_02b_rebuild_diff.xlsx"
    out_md = OUT_DIR / "99_stage3h_official_02b_rebuild_diff.md"
    out_json = OUT_DIR / "100_stage3h_official_02b_rebuild_summary.json"

    _safe_write_excel_multi(
        {
            "row_equivalence": row_equiv_df,
            "new_rows": new_rows_df.drop(columns=["_key"], errors="ignore") if not new_rows_df.empty else pd.DataFrame(),
            "official_02b_present": pd.DataFrame([{"official_02b_records_present_in_rebuilt_06": official_02b_records_present_in_rebuilt_06}]),
            "stage3g_promoted_present": pd.DataFrame([{"stage3g_promoted_records_present_in_rebuilt_06": stage3g_promoted_records_present_in_rebuilt_06}]),
            "manual_input_duplicates": manual_dup_df if not manual_dup_df.empty else pd.DataFrame(),
            "metadata_warnings": metadata_warning_df if not metadata_warning_df.empty else pd.DataFrame(),
            "official_conflicts": official_conflict_df if not official_conflict_df.empty else pd.DataFrame(),
            "official_override_actions": official_actions_df if not official_actions_df.empty else pd.DataFrame(),
            "manual_override_actions": manual_actions_df if not manual_actions_df.empty else pd.DataFrame(),
            "summary": pd.DataFrame([summary]),
        },
        out_xlsx,
    )

    _safe_write_text(
        "\n".join(
            [
                "# Stage3H Official 02B Rebuild Dry-Run",
                "",
                f"- current_06_row_count: {summary['current_06_row_count']}",
                f"- rebuilt_row_count: {summary['rebuilt_row_count']}",
                f"- official_02b_record_count: {summary['official_02b_record_count']}",
                f"- expected_new_row_count: {summary['expected_new_row_count']}",
                f"- actual_new_row_count: {summary['actual_new_row_count']}",
                f"- original_75_rows_preserved: {summary['original_75_rows_preserved']}",
                f"- official_02b_records_present_in_rebuilt_06: {summary['official_02b_records_present_in_rebuilt_06']}",
                f"- stage3g_promoted_records_present_in_rebuilt_06: {summary['stage3g_promoted_records_present_in_rebuilt_06']}",
                f"- duplicate_key_count: {summary['duplicate_key_count']}",
                f"- conflict_count: {summary['conflict_count']}",
                f"- value_mismatch_existing_rows_count: {summary['value_mismatch_existing_rows_count']}",
                f"- unit_mismatch_existing_rows_count: {summary['unit_mismatch_existing_rows_count']}",
                f"- source_only_mismatch_count: {summary['source_only_mismatch_count']}",
                f"- hard_blocker_count: {summary['hard_blocker_count']}",
                f"- production_files_unchanged: {summary['production_files_unchanged']}",
                f"- output_06_unchanged: {summary['output_06_unchanged']}",
                f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
                f"- delivery_status_after: {summary['delivery_status_after']}",
                f"- stage3h_official_rebuild_pass: {summary['stage3h_official_rebuild_pass']}",
            ]
        ),
        out_md,
    )
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3h_diff_xlsx: {out_xlsx}")
    print(f"stage3h_diff_md: {out_md}")
    print(f"stage3h_summary_json: {out_json}")
    for k in [
        "current_06_row_count",
        "rebuilt_row_count",
        "official_02b_record_count",
        "expected_new_row_count",
        "actual_new_row_count",
        "original_75_rows_preserved",
        "official_02b_records_present_in_rebuilt_06",
        "stage3g_promoted_records_present_in_rebuilt_06",
        "duplicate_key_count",
        "conflict_count",
        "value_mismatch_existing_rows_count",
        "unit_mismatch_existing_rows_count",
        "hard_blocker_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "stage3h_official_rebuild_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
