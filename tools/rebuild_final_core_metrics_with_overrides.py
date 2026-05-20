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
OVERRIDE_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
STAGE2D_OUT = BASE_DIR / "output" / "stage2d_official_rebuild_dry_run"

TRUE_VALUES = {"true", "1", "yes", "y", "是", "对", "使用", "采用", "√"}
ACCEPTED_REVIEW_STATUS = {"corrected", "accepted", "修正", "已修正", "已确认", "确认"}
MANUAL_SOURCES = {"manual_corrected", "manual_year_override", "manual_added"}
OVERRIDE_SOURCES = {"ai_extract_real_apply", "ai_repair_override"}


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


def _safe_write_excel(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False, engine="openpyxl")


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _load_inputs() -> Dict[str, Any]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")
    if not OVERRIDE_PATH.exists():
        raise FileNotFoundError(f"Missing override table: {OVERRIDE_PATH}")

    df01 = pd.read_excel(p01).fillna("")
    df02 = pd.read_excel(p02).fillna("")
    df02a = pd.read_excel(p02a).fillna("")
    df02b = pd.read_excel(OVERRIDE_PATH, sheet_name="ai_repair_override").fillna("")
    df06 = pd.read_excel(p06).fillna("")
    return {
        "p01": p01,
        "p02": p02,
        "p02a": p02a,
        "p06": p06,
        "df01": df01,
        "df02": df02,
        "df02a": df02a,
        "df02b": df02b,
        "df06": df06,
    }


def _build_base_from_01(df01: pd.DataFrame) -> pd.DataFrame:
    base = df01.copy()
    defaults = {
        "source_pdf": "",
        "report_type": "",
        "data_usability_tier": "",
        "unit": "",
        "value_validation_status": "",
        "value_repair_applied": "",
        "source_row_label": "",
        "source_table_index": "",
        "source_row_index": "",
        "source_column": "",
        "evidence_crop_path": "",
        "trace_note": "",
    }
    for c, d in defaults.items():
        if c not in base.columns:
            base[c] = d
    for c in ["asset_package", "standard_metric", "year", "value"]:
        if c not in base.columns:
            raise RuntimeError(f"01 missing required column: {c}")

    base["final_value_source"] = "auto_trusted"
    base["final_review_status"] = "auto"
    base["final_value"] = base["value"].map(_norm)
    base["final_unit"] = base["unit"].map(_norm)
    base["original_auto_value"] = base["value"].map(_norm)
    base["original_auto_unit"] = base["unit"].map(_norm)
    base["corrected_value"] = ""
    base["corrected_unit"] = ""
    base["reviewer"] = ""
    base["reviewed_at"] = ""
    base["reviewer_note"] = ""
    base["_key"] = base.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    return base


def _manual_candidates(df02: pd.DataFrame, df02a: pd.DataFrame) -> List[Dict[str, Any]]:
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
        return [], pd.DataFrame(
            columns=[
                "key",
                "duplicate_type",
                "winner_source",
                "loser_source",
                "winner_value",
                "loser_value",
                "reason",
            ]
        )
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for c in candidates:
        grouped.setdefault(_key(c["asset_package"], c["standard_metric"], c["year"]), []).append(c)

    winners: List[Dict[str, Any]] = []
    warning_rows: List[Dict[str, Any]] = []
    for k, arr in grouped.items():
        arr_sorted = sorted(
            arr,
            key=lambda x: (
                1 if _norm(x["_source_code"]) == "02A_manual_year_override" else 0,
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
            actions.append(
                {
                    "key": key,
                    "action": "manual_override_existing_auto",
                    "source_code": _norm(m.get("_source_code")),
                    "final_value_source": _norm(out.at[i, "final_value_source"]),
                }
            )
        else:
            final_source = "manual_year_override" if is_02a else "manual_added"
            trace_note = "manual year override from 02A" if is_02a else "manual addition from review queue"
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
                "trace_note": trace_note,
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
            }
            out = pd.concat([out, pd.DataFrame([new_row])], ignore_index=True)
            out.at[len(out) - 1, "_key"] = key
            idx_map[key] = len(out) - 1
            actions.append(
                {
                    "key": key,
                    "action": "manual_add_new",
                    "source_code": _norm(m.get("_source_code")),
                    "final_value_source": final_source,
                }
            )
    return out, pd.DataFrame(actions)


def _build_override_rows(df02b: pd.DataFrame) -> pd.DataFrame:
    required = [
        "candidate_id",
        "asset_package",
        "standard_metric",
        "year",
        "final_value",
        "final_unit",
        "final_value_source",
        "final_review_status",
        "source_reference",
    ]
    for c in required:
        if c not in df02b.columns:
            raise RuntimeError(f"02B missing required column: {c}")
    out = df02b.copy()
    for c in out.columns:
        out[c] = out[c].map(_norm)
    out["_key"] = out.apply(lambda r: _key(r["asset_package"], r["standard_metric"], r["year"]), axis=1)
    return out


def _apply_overrides(
    manual_applied_df: pd.DataFrame,
    override_df: pd.DataFrame,
    manual_actions_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out = manual_applied_df.copy()
    idx_map = {k: i for i, k in enumerate(out["_key"].tolist())}
    manual_action_map = dict(zip(manual_actions_df["key"].tolist(), manual_actions_df["final_value_source"].tolist()))

    metadata_warnings: List[Dict[str, Any]] = []
    true_conflicts: List[Dict[str, Any]] = []
    override_actions: List[Dict[str, Any]] = []

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
                            "conflict_type": "true_conflict_duplicate",
                            "manual_value": current_value,
                            "manual_unit": current_unit,
                            "manual_source": current_source,
                            "override_value": ov["final_value"],
                            "override_unit": ov["final_unit"],
                            "override_source": ov["final_value_source"],
                            "reason": "manual priority key value/unit differs from override",
                        }
                    )
                    override_actions.append(
                        {
                            "key": key,
                            "action": "override_blocked_conflict_keep_manual",
                            "candidate_id": ov["candidate_id"],
                        }
                    )
                    continue
                if current_source != ov["final_value_source"]:
                    metadata_warnings.append(
                        {
                            "key": key,
                            "warning_type": "SOURCE_ONLY_MISMATCH",
                            "current_source": current_source,
                            "override_source": ov["final_value_source"],
                            "reason": "manual and override value/unit equal but source label differs",
                        }
                    )
                override_actions.append(
                    {
                        "key": key,
                        "action": "override_skipped_keep_manual_priority",
                        "candidate_id": ov["candidate_id"],
                    }
                )
                continue

            # baseline or existing override can be replaced by override
            out.at[i, "final_value"] = ov["final_value"]
            out.at[i, "final_unit"] = ov["final_unit"]
            out.at[i, "final_value_source"] = ov["final_value_source"]
            out.at[i, "final_review_status"] = ov["final_review_status"]
            out.at[i, "corrected_value"] = ov["final_value"]
            out.at[i, "corrected_unit"] = ov["final_unit"]
            out.at[i, "source_row_label"] = ov["standard_metric"]
            out.at[i, "source_table_index"] = ""
            out.at[i, "source_row_index"] = ""
            out.at[i, "trace_note"] = f"official_rebuild_from_{ov['candidate_id']}"
            out.at[i, "reviewer"] = "codex_rebuild"
            out.at[i, "reviewed_at"] = ""
            out.at[i, "reviewer_note"] = f"override source={ov['source_reference']}"
            override_actions.append(
                {
                    "key": key,
                    "action": "override_applied_existing_non_manual",
                    "candidate_id": ov["candidate_id"],
                }
            )
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
                "reviewer_note": f"override source={ov['source_reference']}",
                "_key": key,
            }
            out = pd.concat([out, pd.DataFrame([new_row])], ignore_index=True)
            idx_map[key] = len(out) - 1
            override_actions.append(
                {
                    "key": key,
                    "action": "override_add_new",
                    "candidate_id": ov["candidate_id"],
                }
            )

    # Metadata warning from historical manual_added/manual_corrected semantic split.
    for key, src in manual_action_map.items():
        if src == "manual_added":
            idx = idx_map.get(key)
            if idx is not None:
                cur_src = _norm(out.at[idx, "final_value_source"])
                if cur_src == "manual_added":
                    metadata_warnings.append(
                        {
                            "key": key,
                            "warning_type": "SOURCE_ONLY_MISMATCH",
                            "current_source": "manual_added",
                            "override_source": "manual_corrected",
                            "reason": "manual queue key absent in baseline kept as manual_added semantics",
                        }
                    )

    return (
        out,
        pd.DataFrame(override_actions),
        pd.DataFrame(metadata_warnings),
        pd.DataFrame(true_conflicts),
    )


def _finalize_rebuilt_df(rebuilt: pd.DataFrame, current06: pd.DataFrame) -> pd.DataFrame:
    cols = list(current06.columns)
    out = rebuilt.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = ""
    out = out[cols].copy()
    out = out.sort_values(by=["asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)
    return out


def _classify_equivalence(
    rebuilt06: pd.DataFrame,
    current06: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, int], List[str]]:
    rb = rebuilt06.copy()
    cu = current06.copy()
    rb["_key"] = rb.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    cu["_key"] = cu.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    rb_map = {r["_key"]: r for _, r in rb.iterrows()}
    cu_map = {r["_key"]: r for _, r in cu.iterrows()}
    all_keys = sorted(set(rb_map.keys()) | set(cu_map.keys()))

    rows: List[Dict[str, Any]] = []
    for k in all_keys:
        rb_row = rb_map.get(k)
        cu_row = cu_map.get(k)
        if rb_row is None:
            rows.append(
                {
                    "key": k,
                    "classification": "MISSING_IN_REBUILT",
                    "rebuilt_value": "",
                    "current_value": _norm(cu_row.get("final_value")),
                    "rebuilt_unit": "",
                    "current_unit": _norm(cu_row.get("final_unit")),
                    "rebuilt_source": "",
                    "current_source": _norm(cu_row.get("final_value_source")),
                    "rebuilt_review_status": "",
                    "current_review_status": _norm(cu_row.get("final_review_status")),
                }
            )
            continue
        if cu_row is None:
            rows.append(
                {
                    "key": k,
                    "classification": "EXTRA_IN_REBUILT",
                    "rebuilt_value": _norm(rb_row.get("final_value")),
                    "current_value": "",
                    "rebuilt_unit": _norm(rb_row.get("final_unit")),
                    "current_unit": "",
                    "rebuilt_source": _norm(rb_row.get("final_value_source")),
                    "current_source": "",
                    "rebuilt_review_status": _norm(rb_row.get("final_review_status")),
                    "current_review_status": "",
                }
            )
            continue

        rv = _norm(rb_row.get("final_value"))
        cv = _norm(cu_row.get("final_value"))
        ru = _norm(rb_row.get("final_unit"))
        cuu = _norm(cu_row.get("final_unit"))
        rs = _norm(rb_row.get("final_value_source"))
        cs = _norm(cu_row.get("final_value_source"))
        rr = _norm(rb_row.get("final_review_status"))
        cr = _norm(cu_row.get("final_review_status"))

        if rv == cv and ru == cuu and rs == cs and rr == cr:
            classification = "EXACT_MATCH"
        elif rv != cv:
            classification = "VALUE_MISMATCH"
        elif ru != cuu:
            classification = "UNIT_MISMATCH"
        elif rs != cs and rr == cr:
            classification = "SOURCE_ONLY_MISMATCH"
        elif rr != cr and rs == cs:
            classification = "REVIEW_STATUS_ONLY_MISMATCH"
        else:
            classification = "SOURCE_ONLY_MISMATCH"

        rows.append(
            {
                "key": k,
                "classification": classification,
                "rebuilt_value": rv,
                "current_value": cv,
                "rebuilt_unit": ru,
                "current_unit": cuu,
                "rebuilt_source": rs,
                "current_source": cs,
                "rebuilt_review_status": rr,
                "current_review_status": cr,
            }
        )

    cls_df = pd.DataFrame(rows)
    counts = {
        "exact_match_count": int((cls_df["classification"] == "EXACT_MATCH").sum()),
        "value_mismatch_count": int((cls_df["classification"] == "VALUE_MISMATCH").sum()),
        "unit_mismatch_count": int((cls_df["classification"] == "UNIT_MISMATCH").sum()),
        "source_only_mismatch_count": int((cls_df["classification"] == "SOURCE_ONLY_MISMATCH").sum()),
        "review_status_only_mismatch_count": int((cls_df["classification"] == "REVIEW_STATUS_ONLY_MISMATCH").sum()),
        "missing_in_rebuilt_count": int((cls_df["classification"] == "MISSING_IN_REBUILT").sum()),
        "extra_in_rebuilt_count": int((cls_df["classification"] == "EXTRA_IN_REBUILT").sum()),
    }
    source_or_review_keys = cls_df[
        cls_df["classification"].isin(["SOURCE_ONLY_MISMATCH", "REVIEW_STATUS_ONLY_MISMATCH"])
    ]["key"].tolist()
    return cls_df, counts, source_or_review_keys


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage2D official rebuild dry-run with 02B overrides.")
    parser.parse_args()

    snap_before = _snapshot_prod()
    data = _load_inputs()

    base = _build_base_from_01(data["df01"])
    manual_raw = _manual_candidates(data["df02"], data["df02a"])
    manual_winners, manual_dup_df = _dedupe_manual_candidates(manual_raw)
    manual_applied, manual_actions = _apply_manual_to_base(base, manual_winners)
    override_rows = _build_override_rows(data["df02b"])

    rebuilt_pre_final, override_actions, metadata_warning_df, true_conflict_df = _apply_overrides(
        manual_applied_df=manual_applied,
        override_df=override_rows,
        manual_actions_df=manual_actions,
    )
    rebuilt06 = _finalize_rebuilt_df(rebuilt_pre_final, data["df06"])

    # Input duplicate warning includes both manual dedupe duplicates and multi-layer overlaps.
    pre_resolve_keys = pd.concat(
        [
            base[["_key"]].assign(layer="baseline"),
            pd.DataFrame({"_key": [c["_key"] for c in [{"_key": _key(x["asset_package"], x["standard_metric"], x["year"])} for x in manual_winners]], "layer": "manual"}),
            override_rows[["_key"]].assign(layer="override"),
        ],
        ignore_index=True,
    )
    layered_dup = (
        pre_resolve_keys.groupby("_key", dropna=False)
        .agg(layer_count=("layer", "size"), layers=("layer", lambda s: ",".join(sorted(set(s.tolist())))))
        .reset_index()
    )
    layered_dup_warn = layered_dup[layered_dup["layer_count"] > 1].copy()
    if not layered_dup_warn.empty:
        layered_dup_warn["duplicate_type"] = "input_duplicate_before_priority_resolution"
        layered_dup_warn["reason"] = "same key appears in multiple input layers before priority resolution"
    input_duplicate_df = pd.concat(
        [manual_dup_df, layered_dup_warn.rename(columns={"_key": "key"})],
        ignore_index=True,
        sort=False,
    ).fillna("")
    input_duplicate_warning_count = int(input_duplicate_df["key"].nunique()) if not input_duplicate_df.empty else 0

    rebuilt06["_key"] = rebuilt06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    resolved_output_duplicate_count = int(rebuilt06.groupby("_key", dropna=False).size().gt(1).sum())
    rebuilt06 = rebuilt06.drop(columns=["_key"]).copy()

    eq_df, eq_counts, source_or_review_keys = _classify_equivalence(rebuilt06, data["df06"])
    metadata_warning_keys = set(source_or_review_keys)
    if not metadata_warning_df.empty:
        metadata_warning_keys.update(metadata_warning_df["key"].tolist())
    metadata_warning_count = len(metadata_warning_keys)

    override_keys = set(override_rows["_key"].tolist())
    rebuilt_keys = set(
        rebuilt06.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist()
    )
    override_records_present_in_rebuilt_06 = override_keys.issubset(rebuilt_keys)
    true_conflict_duplicate_count = int(true_conflict_df["key"].nunique()) if not true_conflict_df.empty else 0

    rebuilt_row_count = len(rebuilt06)
    current_06_row_count = len(data["df06"])
    row_count_match = rebuilt_row_count == current_06_row_count
    current_keys = set(
        data["df06"].apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist()
    )
    key_set_match = rebuilt_keys == current_keys

    business_value_equivalence_pass = bool(
        eq_counts["value_mismatch_count"] == 0
        and eq_counts["unit_mismatch_count"] == 0
        and eq_counts["missing_in_rebuilt_count"] == 0
        and eq_counts["extra_in_rebuilt_count"] == 0
        and resolved_output_duplicate_count == 0
        and true_conflict_duplicate_count == 0
        and override_records_present_in_rebuilt_06
    )
    hard_blocker_count = int(
        eq_counts["value_mismatch_count"]
        + eq_counts["unit_mismatch_count"]
        + eq_counts["missing_in_rebuilt_count"]
        + eq_counts["extra_in_rebuilt_count"]
        + resolved_output_duplicate_count
        + true_conflict_duplicate_count
    )

    rebuilt_path = STAGE2D_OUT / "06_最终核心财务指标.official_rebuilt_with_02B.xlsx"
    diff_xlsx = STAGE2D_OUT / "83_stage2d_official_rebuild_diff.xlsx"
    diff_md = STAGE2D_OUT / "83_stage2d_official_rebuild_diff.md"
    summary_json = STAGE2D_OUT / "84_stage2d_official_rebuild_summary.json"

    _safe_write_excel(rebuilt06, rebuilt_path)
    _safe_write_excel_multi(
        {
            "equivalence_classification": eq_df,
            "input_duplicate_warnings": input_duplicate_df if not input_duplicate_df.empty else pd.DataFrame(columns=["key"]),
            "metadata_warnings": metadata_warning_df if not metadata_warning_df.empty else pd.DataFrame(columns=["key"]),
            "true_conflicts": true_conflict_df if not true_conflict_df.empty else pd.DataFrame(columns=["key"]),
            "override_actions": override_actions if not override_actions.empty else pd.DataFrame(columns=["key"]),
            "summary": pd.DataFrame(
                [
                    {
                        "rebuilt_row_count": rebuilt_row_count,
                        "current_06_row_count": current_06_row_count,
                        "row_count_match": row_count_match,
                        "key_set_match": key_set_match,
                        "business_value_equivalence_pass": business_value_equivalence_pass,
                        "metadata_warning_count": metadata_warning_count,
                        "input_duplicate_warning_count": input_duplicate_warning_count,
                        "hard_blocker_count": hard_blocker_count,
                        "override_records_present_in_rebuilt_06": override_records_present_in_rebuilt_06,
                        "resolved_output_duplicate_count": resolved_output_duplicate_count,
                        "true_conflict_duplicate_count": true_conflict_duplicate_count,
                    }
                ]
            ),
        },
        diff_xlsx,
    )

    snap_after = _snapshot_prod()
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before["06"] == snap_after["06"]
    delivery_status = _run_delivery_check()
    stage2d_official_rebuild_dry_run_pass = bool(
        business_value_equivalence_pass
        and production_files_unchanged
        and output_06_unchanged
        and delivery_status.get("overall_status") == "PASS"
    )

    summary = {
        "rebuilt_row_count": rebuilt_row_count,
        "current_06_row_count": current_06_row_count,
        "row_count_match": bool(row_count_match),
        "key_set_match": bool(key_set_match),
        "business_value_equivalence_pass": bool(business_value_equivalence_pass),
        "metadata_warning_count": int(metadata_warning_count),
        "input_duplicate_warning_count": int(input_duplicate_warning_count),
        "hard_blocker_count": int(hard_blocker_count),
        "override_records_present_in_rebuilt_06": bool(override_records_present_in_rebuilt_06),
        "resolved_output_duplicate_count": int(resolved_output_duplicate_count),
        "true_conflict_duplicate_count": int(true_conflict_duplicate_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage2d_official_rebuild_dry_run_pass": bool(stage2d_official_rebuild_dry_run_pass),
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
        "value_mismatch_count": int(eq_counts["value_mismatch_count"]),
        "unit_mismatch_count": int(eq_counts["unit_mismatch_count"]),
        "missing_in_rebuilt_count": int(eq_counts["missing_in_rebuilt_count"]),
        "extra_in_rebuilt_count": int(eq_counts["extra_in_rebuilt_count"]),
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    diff_md.write_text(
        "\n".join(
            [
                "# Stage2D Official Rebuild Dry-Run",
                "",
                f"- rebuilt_row_count: {summary['rebuilt_row_count']}",
                f"- current_06_row_count: {summary['current_06_row_count']}",
                f"- row_count_match: {summary['row_count_match']}",
                f"- key_set_match: {summary['key_set_match']}",
                f"- business_value_equivalence_pass: {summary['business_value_equivalence_pass']}",
                f"- metadata_warning_count: {summary['metadata_warning_count']}",
                f"- input_duplicate_warning_count: {summary['input_duplicate_warning_count']}",
                f"- hard_blocker_count: {summary['hard_blocker_count']}",
                f"- override_records_present_in_rebuilt_06: {summary['override_records_present_in_rebuilt_06']}",
                f"- resolved_output_duplicate_count: {summary['resolved_output_duplicate_count']}",
                f"- true_conflict_duplicate_count: {summary['true_conflict_duplicate_count']}",
                f"- production_files_unchanged: {summary['production_files_unchanged']}",
                f"- output_06_unchanged: {summary['output_06_unchanged']}",
                f"- delivery_status_after: {summary['delivery_status_after']}",
                f"- stage2d_official_rebuild_dry_run_pass: {summary['stage2d_official_rebuild_dry_run_pass']}",
            ]
        ),
        encoding="utf-8",
    )

    print(f"rebuilt_path: {rebuilt_path}")
    print(f"diff_xlsx: {diff_xlsx}")
    print(f"diff_md: {diff_md}")
    print(f"summary_json: {summary_json}")
    for k in [
        "rebuilt_row_count",
        "current_06_row_count",
        "row_count_match",
        "key_set_match",
        "business_value_equivalence_pass",
        "metadata_warning_count",
        "input_duplicate_warning_count",
        "hard_blocker_count",
        "override_records_present_in_rebuilt_06",
        "resolved_output_duplicate_count",
        "true_conflict_duplicate_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "stage2d_official_rebuild_dry_run_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
