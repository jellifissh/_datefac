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
OFFICIAL_OVERRIDE_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
DRAFT_OVERRIDE_PATH = BASE_DIR / "data" / "overrides" / "drafts" / "03_stage3_ai_repair_override_draft.xlsx"
STAGE3D_SUMMARY_PATH = BASE_DIR / "output" / "stage3d_structured_mapping" / "92_stage3d_structured_mapping_summary.json"
OUT_DIR = BASE_DIR / "output" / "stage3e_draft_rebuild_dry_run"


TRUE_VALUES = {
    "true",
    "1",
    "yes",
    "y",
    "是",
    "使用",
    "采用",
    "√",
}
ACCEPTED_REVIEW_STATUS = {
    "corrected",
    "accepted",
    "修正",
    "已修正",
    "已确认",
    "确认",
}
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
    p06 = _find_delivery_file("06_*核心财务指标.xlsx")

    p05_candidates = sorted(DELIVERY_DIR.glob("05_*.xlsx"))
    snapshot = {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "06": _sha256(p06),
    }
    if p05_candidates:
        snapshot["05"] = _sha256(p05_candidates[0])
    return snapshot


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

    if not OFFICIAL_OVERRIDE_PATH.exists():
        raise FileNotFoundError(f"Missing official override table: {OFFICIAL_OVERRIDE_PATH}")
    if not DRAFT_OVERRIDE_PATH.exists():
        raise FileNotFoundError(f"Missing stage3 draft override table: {DRAFT_OVERRIDE_PATH}")

    df01 = pd.read_excel(p01).fillna("")
    df02 = pd.read_excel(p02).fillna("")
    df02a = pd.read_excel(p02a).fillna("")
    df02b = pd.read_excel(OFFICIAL_OVERRIDE_PATH, sheet_name="ai_repair_override").fillna("")
    df03 = pd.read_excel(DRAFT_OVERRIDE_PATH).fillna("")
    df06 = pd.read_excel(p06).fillna("")

    stage3d_summary = {}
    if STAGE3D_SUMMARY_PATH.exists():
        try:
            stage3d_summary = json.loads(STAGE3D_SUMMARY_PATH.read_text(encoding="utf-8"))
        except Exception:
            stage3d_summary = {}

    return {
        "df01": df01,
        "df02": df02,
        "df02a": df02a,
        "df02b": df02b,
        "df03": df03,
        "df06": df06,
        "stage3d_summary": stage3d_summary,
    }


def _build_base_from_01(df01: pd.DataFrame) -> pd.DataFrame:
    required = ["asset_package", "standard_metric", "year", "value", "unit"]
    for col in required:
        if col not in df01.columns:
            raise RuntimeError(f"01 missing required column: {col}")

    base = df01.copy()
    defaults = {
        "source_pdf": "",
        "report_type": "",
        "data_usability_tier": "",
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

    base["asset_package"] = base["asset_package"].map(_norm)
    base["standard_metric"] = base["standard_metric"].map(_norm)
    base["year"] = base["year"].map(_norm)
    base["unit"] = base["unit"].map(_norm)
    base["value"] = base["value"].map(_norm)

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


def _build_official_override_rows(df02b: pd.DataFrame) -> pd.DataFrame:
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


def _build_draft_override_rows(df03: pd.DataFrame) -> pd.DataFrame:
    required = [
        "draft_repair_id",
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
        if c not in df03.columns:
            raise RuntimeError(f"stage3 draft missing required column: {c}")

    out = df03.copy()
    for c in out.columns:
        out[c] = out[c].map(_norm)
    out["_key"] = out.apply(lambda r: _key(r["asset_package"], r["standard_metric"], r["year"]), axis=1)

    if out["_key"].duplicated().any():
        dup = out[out["_key"].duplicated(keep=False)].copy()
        keys = ", ".join(sorted(dup["_key"].unique().tolist()))
        raise RuntimeError(f"stage3 draft contains duplicate key(s): {keys}")

    return out


def _apply_official_overrides(
    manual_applied_df: pd.DataFrame,
    override_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
            out.at[i, "source_row_label"] = ov["standard_metric"]
            out.at[i, "trace_note"] = f"official_rebuild_from_{ov['candidate_id']}"
            out.at[i, "reviewer"] = "codex_rebuild"
            out.at[i, "reviewed_at"] = ""
            out.at[i, "reviewer_note"] = f"official override source={ov['source_reference']}"
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


def _apply_stage3_draft_overrides(
    official_applied_df: pd.DataFrame,
    draft_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out = official_applied_df.copy()
    idx_map = {k: i for i, k in enumerate(out["_key"].tolist())}

    actions: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []

    for _, r in draft_df.iterrows():
        key = _norm(r.get("_key"))
        draft_repair_id = _norm(r.get("draft_repair_id"))
        candidate_id = _norm(r.get("candidate_id"))
        final_value = _norm(r.get("final_value"))
        final_unit = _norm(r.get("final_unit"))
        final_value_source = _norm(r.get("final_value_source")) or "stage3_override_draft"
        final_review_status = _norm(r.get("final_review_status")) or "draft_approved"
        source_reference = _norm(r.get("source_reference"))
        asset_package = _norm(r.get("asset_package"))
        standard_metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))

        if not asset_package or not standard_metric or not year or not final_value:
            conflicts.append(
                {
                    "key": key,
                    "draft_repair_id": draft_repair_id,
                    "candidate_id": candidate_id,
                    "conflict_type": "draft_missing_required_field",
                    "reason": "asset_package/standard_metric/year/final_value missing",
                }
            )
            actions.append({"key": key, "action": "draft_blocked_missing_required", "candidate_id": candidate_id})
            continue

        if key in idx_map:
            i = idx_map[key]
            current_value = _norm(out.at[i, "final_value"])
            current_unit = _norm(out.at[i, "final_unit"])
            current_source = _norm(out.at[i, "final_value_source"])

            conflict_type = "draft_key_exists_conflict"
            reason = "stage3 draft override is not allowed to overwrite any existing key"
            if current_value == final_value and current_unit == final_unit:
                conflict_type = "draft_key_already_covered"
                reason = "existing key has same value/unit; draft treated as already covered"

            conflicts.append(
                {
                    "key": key,
                    "draft_repair_id": draft_repair_id,
                    "candidate_id": candidate_id,
                    "conflict_type": conflict_type,
                    "existing_value": current_value,
                    "existing_unit": current_unit,
                    "existing_source": current_source,
                    "draft_value": final_value,
                    "draft_unit": final_unit,
                    "reason": reason,
                }
            )
            actions.append({"key": key, "action": "draft_blocked_existing_key", "candidate_id": candidate_id})
            continue

        new_row = {
            "source_pdf": "",
            "asset_package": asset_package,
            "report_type": "",
            "data_usability_tier": "",
            "standard_metric": standard_metric,
            "year": year,
            "value": "",
            "unit": final_unit,
            "value_validation_status": "",
            "value_repair_applied": "",
            "source_row_label": standard_metric,
            "source_table_index": "",
            "source_row_index": "",
            "source_column": "",
            "evidence_crop_path": "",
            "trace_note": f"stage3_draft_rebuild_from_{candidate_id}",
            "final_value_source": final_value_source,
            "final_review_status": final_review_status,
            "final_value": final_value,
            "final_unit": final_unit,
            "original_auto_value": "",
            "original_auto_unit": "",
            "corrected_value": final_value,
            "corrected_unit": final_unit,
            "reviewer": "codex_stage3e_dry_run",
            "reviewed_at": "",
            "reviewer_note": f"stage3 draft source={source_reference}; draft_repair_id={draft_repair_id}",
            "_key": key,
        }
        out = pd.concat([out, pd.DataFrame([new_row])], ignore_index=True)
        idx_map[key] = len(out) - 1
        actions.append({"key": key, "action": "draft_added_new", "candidate_id": candidate_id})

    return out, pd.DataFrame(actions), pd.DataFrame(conflicts)


def _finalize_to_06_schema(rebuilt: pd.DataFrame, current06: pd.DataFrame) -> pd.DataFrame:
    cols = list(current06.columns)
    out = rebuilt.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = ""
    out = out[cols].copy()
    out = out.sort_values(by=["asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)
    return out


def _existing_row_equivalence(
    rebuilt06: pd.DataFrame,
    current06: pd.DataFrame,
) -> Tuple[pd.DataFrame, int, int, bool]:
    rb = rebuilt06.copy()
    cu = current06.copy()

    rb["_key"] = rb.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    cu["_key"] = cu.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)

    rb_map = {r["_key"]: r for _, r in rb.iterrows()}
    value_mismatch = 0
    unit_mismatch = 0
    rows: List[Dict[str, Any]] = []

    for _, r in cu.iterrows():
        key = _norm(r.get("_key"))
        cur_val = _norm(r.get("final_value"))
        cur_unit = _norm(r.get("final_unit"))
        rb_row = rb_map.get(key)

        if rb_row is None:
            rows.append(
                {
                    "key": key,
                    "classification": "MISSING_EXISTING_ROW_IN_REBUILT",
                    "current_value": cur_val,
                    "rebuilt_value": "",
                    "current_unit": cur_unit,
                    "rebuilt_unit": "",
                }
            )
            value_mismatch += 1
            continue

        rb_val = _norm(rb_row.get("final_value"))
        rb_unit = _norm(rb_row.get("final_unit"))

        if cur_val != rb_val:
            value_mismatch += 1
            rows.append(
                {
                    "key": key,
                    "classification": "VALUE_MISMATCH_EXISTING_ROW",
                    "current_value": cur_val,
                    "rebuilt_value": rb_val,
                    "current_unit": cur_unit,
                    "rebuilt_unit": rb_unit,
                }
            )
            continue

        if cur_unit != rb_unit:
            unit_mismatch += 1
            rows.append(
                {
                    "key": key,
                    "classification": "UNIT_MISMATCH_EXISTING_ROW",
                    "current_value": cur_val,
                    "rebuilt_value": rb_val,
                    "current_unit": cur_unit,
                    "rebuilt_unit": rb_unit,
                }
            )
            continue

        rows.append(
            {
                "key": key,
                "classification": "EXISTING_ROW_PRESERVED",
                "current_value": cur_val,
                "rebuilt_value": rb_val,
                "current_unit": cur_unit,
                "rebuilt_unit": rb_unit,
            }
        )

    original_75_rows_preserved = value_mismatch == 0 and unit_mismatch == 0
    return pd.DataFrame(rows), value_mismatch, unit_mismatch, original_75_rows_preserved


def _collect_new_rows(rebuilt06: pd.DataFrame, current06: pd.DataFrame) -> pd.DataFrame:
    rb = rebuilt06.copy()
    cu = current06.copy()
    rb["_key"] = rb.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    cu_keys = set(cu.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1).tolist())
    new_rows = rb[~rb["_key"].isin(cu_keys)].copy()
    return new_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3E dry-run official rebuild with stage3 draft override.")
    parser.parse_args()

    snap_before = _snapshot_production_hashes()
    official_02b_hash_before = _sha256(OFFICIAL_OVERRIDE_PATH)
    data = _load_inputs()

    base = _build_base_from_01(data["df01"])
    manual_raw = _collect_manual_candidates(data["df02"], data["df02a"])
    manual_winners, manual_dup_df = _dedupe_manual_candidates(manual_raw)
    manual_applied, manual_actions_df = _apply_manual_to_base(base, manual_winners)

    official_override_df = _build_official_override_rows(data["df02b"])
    draft_override_df = _build_draft_override_rows(data["df03"])

    official_applied, official_actions_df, metadata_warning_df, official_conflict_df = _apply_official_overrides(
        manual_applied_df=manual_applied,
        override_df=official_override_df,
    )

    draft_applied, draft_actions_df, draft_conflict_df = _apply_stage3_draft_overrides(
        official_applied_df=official_applied,
        draft_df=draft_override_df,
    )

    rebuilt06 = _finalize_to_06_schema(draft_applied, data["df06"])

    rebuilt_with_key = rebuilt06.copy()
    rebuilt_with_key["_key"] = rebuilt_with_key.apply(lambda r: _key(r.get("asset_package"), r.get("standard_metric"), r.get("year")), axis=1)
    duplicate_key_count = int(rebuilt_with_key["_key"].duplicated().sum())

    current_06_row_count = len(data["df06"])
    rebuilt_row_count = len(rebuilt06)

    existing_eq_df, value_mismatch_existing_rows_count, unit_mismatch_existing_rows_count, original_75_rows_preserved = _existing_row_equivalence(
        rebuilt06=rebuilt06,
        current06=data["df06"],
    )

    new_rows_df = _collect_new_rows(rebuilt06=rebuilt06, current06=data["df06"])
    actual_new_row_count = len(new_rows_df)

    draft_keys = set(draft_override_df["_key"].tolist())
    rebuilt_keys = set(rebuilt_with_key["_key"].tolist())
    stage3_draft_records_present_in_rebuilt_06 = draft_keys.issubset(rebuilt_keys)

    new_row_keys = set(new_rows_df["_key"].tolist()) if not new_rows_df.empty else set()
    draft_new_rows_df = draft_override_df[draft_override_df["_key"].isin(new_row_keys)].copy()

    expected_new_draft_row_count = len(draft_override_df)

    conflict_count = 0
    if not official_conflict_df.empty:
        conflict_count += int(official_conflict_df["key"].nunique())
    if not draft_conflict_df.empty:
        conflict_count += int(draft_conflict_df["key"].nunique())

    row_count_expected = current_06_row_count + expected_new_draft_row_count

    hard_blocker_count = int(
        (1 if expected_new_draft_row_count != 4 else 0)
        + (1 if actual_new_row_count != expected_new_draft_row_count else 0)
        + (0 if original_75_rows_preserved else 1)
        + (0 if stage3_draft_records_present_in_rebuilt_06 else 1)
        + (0 if duplicate_key_count == 0 else 1)
        + (0 if conflict_count == 0 else 1)
        + (0 if value_mismatch_existing_rows_count == 0 else 1)
        + (0 if unit_mismatch_existing_rows_count == 0 else 1)
        + (0 if rebuilt_row_count == row_count_expected else 1)
    )

    rebuilt_path = OUT_DIR / "06_最终核心财务指标.rebuilt_with_stage3_draft.xlsx"
    diff_xlsx = OUT_DIR / "93_stage3e_draft_rebuild_diff.xlsx"
    diff_md = OUT_DIR / "93_stage3e_draft_rebuild_diff.md"
    summary_json = OUT_DIR / "94_stage3e_draft_rebuild_summary.json"

    _safe_write_excel(rebuilt06, rebuilt_path)
    _safe_write_excel_multi(
        {
            "existing_row_equivalence": existing_eq_df,
            "new_rows": new_rows_df.drop(columns=["_key"], errors="ignore") if not new_rows_df.empty else pd.DataFrame(),
            "draft_new_rows_match": draft_new_rows_df.drop(columns=["_key"], errors="ignore") if not draft_new_rows_df.empty else pd.DataFrame(),
            "official_override_actions": official_actions_df if not official_actions_df.empty else pd.DataFrame(),
            "draft_override_actions": draft_actions_df if not draft_actions_df.empty else pd.DataFrame(),
            "manual_input_duplicates": manual_dup_df if not manual_dup_df.empty else pd.DataFrame(),
            "metadata_warnings": metadata_warning_df if not metadata_warning_df.empty else pd.DataFrame(),
            "official_conflicts": official_conflict_df if not official_conflict_df.empty else pd.DataFrame(),
            "draft_conflicts": draft_conflict_df if not draft_conflict_df.empty else pd.DataFrame(),
            "summary": pd.DataFrame(
                [
                    {
                        "current_06_row_count": current_06_row_count,
                        "rebuilt_row_count": rebuilt_row_count,
                        "expected_new_draft_row_count": expected_new_draft_row_count,
                        "actual_new_row_count": actual_new_row_count,
                        "row_count_expected": row_count_expected,
                        "row_count_match_expected": rebuilt_row_count == row_count_expected,
                        "original_75_rows_preserved": original_75_rows_preserved,
                        "stage3_draft_records_present_in_rebuilt_06": stage3_draft_records_present_in_rebuilt_06,
                        "duplicate_key_count": duplicate_key_count,
                        "conflict_count": conflict_count,
                        "value_mismatch_existing_rows_count": value_mismatch_existing_rows_count,
                        "unit_mismatch_existing_rows_count": unit_mismatch_existing_rows_count,
                        "hard_blocker_count": hard_blocker_count,
                    }
                ]
            ),
        },
        diff_xlsx,
    )

    snap_after = _snapshot_production_hashes()
    official_02b_hash_after = _sha256(OFFICIAL_OVERRIDE_PATH)
    production_files_unchanged = snap_before == snap_after
    output_06_unchanged = snap_before.get("06") == snap_after.get("06")
    official_02B_unchanged = official_02b_hash_before == official_02b_hash_after

    delivery_status = _run_delivery_check()

    stage3e_draft_rebuild_pass = bool(
        expected_new_draft_row_count == 4
        and actual_new_row_count == 4
        and original_75_rows_preserved
        and stage3_draft_records_present_in_rebuilt_06
        and duplicate_key_count == 0
        and conflict_count == 0
        and value_mismatch_existing_rows_count == 0
        and unit_mismatch_existing_rows_count == 0
        and hard_blocker_count == 0
        and production_files_unchanged
        and output_06_unchanged
        and official_02B_unchanged
        and delivery_status.get("overall_status") == "PASS"
    )

    stage3d_pass = bool(data.get("stage3d_summary", {}).get("stage3d_mapping_pass", True))

    summary = {
        "current_06_row_count": int(current_06_row_count),
        "rebuilt_row_count": int(rebuilt_row_count),
        "expected_new_draft_row_count": int(expected_new_draft_row_count),
        "actual_new_row_count": int(actual_new_row_count),
        "original_75_rows_preserved": bool(original_75_rows_preserved),
        "stage3_draft_records_present_in_rebuilt_06": bool(stage3_draft_records_present_in_rebuilt_06),
        "duplicate_key_count": int(duplicate_key_count),
        "conflict_count": int(conflict_count),
        "value_mismatch_existing_rows_count": int(value_mismatch_existing_rows_count),
        "unit_mismatch_existing_rows_count": int(unit_mismatch_existing_rows_count),
        "hard_blocker_count": int(hard_blocker_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage3e_draft_rebuild_pass": bool(stage3e_draft_rebuild_pass),
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
        "stage3d_mapping_pass": stage3d_pass,
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    diff_md.write_text(
        "\n".join(
            [
                "# Stage3E Draft Override Rebuild Dry-Run",
                "",
                f"- current_06_row_count: {summary['current_06_row_count']}",
                f"- rebuilt_row_count: {summary['rebuilt_row_count']}",
                f"- expected_new_draft_row_count: {summary['expected_new_draft_row_count']}",
                f"- actual_new_row_count: {summary['actual_new_row_count']}",
                f"- original_75_rows_preserved: {summary['original_75_rows_preserved']}",
                f"- stage3_draft_records_present_in_rebuilt_06: {summary['stage3_draft_records_present_in_rebuilt_06']}",
                f"- duplicate_key_count: {summary['duplicate_key_count']}",
                f"- conflict_count: {summary['conflict_count']}",
                f"- value_mismatch_existing_rows_count: {summary['value_mismatch_existing_rows_count']}",
                f"- unit_mismatch_existing_rows_count: {summary['unit_mismatch_existing_rows_count']}",
                f"- hard_blocker_count: {summary['hard_blocker_count']}",
                f"- production_files_unchanged: {summary['production_files_unchanged']}",
                f"- output_06_unchanged: {summary['output_06_unchanged']}",
                f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
                f"- delivery_status_after: {summary['delivery_status_after']}",
                f"- stage3e_draft_rebuild_pass: {summary['stage3e_draft_rebuild_pass']}",
            ]
        ),
        encoding="utf-8",
    )

    print(f"rebuilt_path: {rebuilt_path}")
    print(f"diff_xlsx: {diff_xlsx}")
    print(f"diff_md: {diff_md}")
    print(f"summary_json: {summary_json}")
    for k in [
        "current_06_row_count",
        "rebuilt_row_count",
        "expected_new_draft_row_count",
        "actual_new_row_count",
        "original_75_rows_preserved",
        "stage3_draft_records_present_in_rebuilt_06",
        "duplicate_key_count",
        "conflict_count",
        "value_mismatch_existing_rows_count",
        "unit_mismatch_existing_rows_count",
        "hard_blocker_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "stage3e_draft_rebuild_pass",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
