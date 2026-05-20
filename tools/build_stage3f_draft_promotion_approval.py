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
DRAFT_PATH = BASE_DIR / "data" / "overrides" / "drafts" / "03_stage3_ai_repair_override_draft.xlsx"
STAGE3D_XLSX = BASE_DIR / "output" / "stage3d_structured_mapping" / "91_stage3d_structured_mapping.xlsx"
STAGE3D_JSON = BASE_DIR / "output" / "stage3d_structured_mapping" / "92_stage3d_structured_mapping_summary.json"
STAGE3E_XLSX = BASE_DIR / "output" / "stage3e_draft_rebuild_dry_run" / "93_stage3e_draft_rebuild_diff.xlsx"
STAGE3E_JSON = BASE_DIR / "output" / "stage3e_draft_rebuild_dry_run" / "94_stage3e_draft_rebuild_summary.json"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
OUT_DIR = BASE_DIR / "output" / "stage3f_draft_promotion_approval"

TARGET_FINAL_ONLY = "FINAL_METRIC_OVERRIDE_ONLY"
APPROVED = "APPROVED_FOR_02B_PROMOTION"
NEED_MANUAL = "NEED_MANUAL_APPROVAL"
REJECT = "REJECT_PROMOTION"


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
        return {"overall_status": "UNKNOWN"}


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _load_inputs() -> Dict[str, Any]:
    if not DRAFT_PATH.exists():
        raise FileNotFoundError(f"Missing draft file: {DRAFT_PATH}")
    if not STAGE3D_XLSX.exists():
        raise FileNotFoundError(f"Missing stage3d workbook: {STAGE3D_XLSX}")
    if not STAGE3D_JSON.exists():
        raise FileNotFoundError(f"Missing stage3d summary: {STAGE3D_JSON}")
    if not STAGE3E_XLSX.exists():
        raise FileNotFoundError(f"Missing stage3e workbook: {STAGE3E_XLSX}")
    if not STAGE3E_JSON.exists():
        raise FileNotFoundError(f"Missing stage3e summary: {STAGE3E_JSON}")
    if not OFFICIAL_02B_PATH.exists():
        raise FileNotFoundError(f"Missing official 02B override: {OFFICIAL_02B_PATH}")

    draft_df = pd.read_excel(DRAFT_PATH).fillna("")
    stage3d_df = pd.read_excel(STAGE3D_XLSX, sheet_name="stage3d_mapping").fillna("")
    stage3e_summary = json.loads(STAGE3E_JSON.read_text(encoding="utf-8"))
    stage3d_summary = json.loads(STAGE3D_JSON.read_text(encoding="utf-8"))
    current_06 = pd.read_excel(_find_delivery_file("06_*核心财务指标.xlsx")).fillna("")
    official_02b = pd.read_excel(OFFICIAL_02B_PATH, sheet_name="ai_repair_override").fillna("")

    return {
        "draft_df": draft_df,
        "stage3d_df": stage3d_df,
        "stage3d_summary": stage3d_summary,
        "stage3e_summary": stage3e_summary,
        "current_06": current_06,
        "official_02b": official_02b,
    }


def _build_stage3d_map(stage3d_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    m: Dict[str, Dict[str, Any]] = {}
    for _, r in stage3d_df.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        m[k] = {
            "target": _norm(r.get("recommended_structured_target")),
            "evidence": _norm(r.get("evidence")),
            "source_reference": _norm(r.get("source_reference")),
            "final_value": _norm(r.get("final_value")),
            "final_unit": _norm(r.get("final_unit")),
        }
    return m


def _build_current06_map(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    m: Dict[str, Dict[str, str]] = {}
    for _, r in df.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        m[k] = {
            "final_value": _norm(r.get("final_value")),
            "final_unit": _norm(r.get("final_unit")),
            "final_value_source": _norm(r.get("final_value_source")),
        }
    return m


def _build_02b_map(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    m: Dict[str, Dict[str, str]] = {}
    for _, r in df.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        m[k] = {
            "final_value": _norm(r.get("final_value")),
            "final_unit": _norm(r.get("final_unit")),
            "final_value_source": _norm(r.get("final_value_source")),
        }
    return m


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage3F draft promotion approval package builder.")
    parser.parse_args()

    snap_before = _snapshot_production_hashes()
    official_02b_hash_before = _sha256(OFFICIAL_02B_PATH)
    data = _load_inputs()

    stage3d_map = _build_stage3d_map(data["stage3d_df"])
    current06_map = _build_current06_map(data["current_06"])
    official02b_map = _build_02b_map(data["official_02b"])
    stage3e_summary = data["stage3e_summary"]
    stage3d_summary = data["stage3d_summary"]

    rows: List[Dict[str, Any]] = []
    for _, r in data["draft_df"].iterrows():
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        key = _key(asset, metric, year)
        stage3d_info = stage3d_map.get(key, {})
        current06_info = current06_map.get(key, {})
        official02b_info = official02b_map.get(key, {})
        stage3d_target = _norm(stage3d_info.get("target"))
        evidence = _norm(r.get("evidence"))
        source_reference = _norm(r.get("source_reference"))
        stage3e_status = "PASS" if bool(stage3e_summary.get("stage3e_draft_rebuild_pass")) else "FAIL"

        conditions_ok = [
            stage3d_target == TARGET_FINAL_ONLY,
            bool(stage3e_summary.get("stage3e_draft_rebuild_pass")),
            bool(stage3e_summary.get("original_75_rows_preserved")),
            int(stage3e_summary.get("actual_new_row_count", 0)) == 4,
            int(stage3e_summary.get("duplicate_key_count", 0)) == 0,
            int(stage3e_summary.get("conflict_count", 0)) == 0,
            int(stage3e_summary.get("hard_blocker_count", 0)) == 0,
            _norm(evidence) != "",
            _norm(source_reference) != "",
        ]

        if all(conditions_ok):
            decision = APPROVED
            reason = "Stage 3D final-only target and Stage 3E dry-run passed with no blockers."
        elif not _norm(evidence) or not _norm(source_reference):
            decision = NEED_MANUAL
            reason = "Evidence or source reference missing."
        else:
            decision = REJECT
            reason = "Target or dry-run readiness failed."

        rows.append(
            {
                "draft_repair_id": _norm(r.get("draft_repair_id")),
                "candidate_id": _norm(r.get("candidate_id")),
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "final_value": _norm(r.get("final_value")),
                "final_unit": _norm(r.get("final_unit")),
                "final_value_source": _norm(r.get("final_value_source")),
                "evidence": evidence,
                "source_reference": source_reference,
                "stage3d_target": stage3d_target,
                "stage3e_rebuild_status": stage3e_status,
                "approval_decision": decision,
                "approval_reason": reason,
            }
        )

    approval_df = pd.DataFrame(rows)
    input_draft_record_count = len(approval_df)
    approved_for_02b_promotion_count = int((approval_df["approval_decision"] == APPROVED).sum())
    need_manual_approval_count = int((approval_df["approval_decision"] == NEED_MANUAL).sum())
    reject_promotion_count = int((approval_df["approval_decision"] == REJECT).sum())

    production_files_unchanged = snap_before == _snapshot_production_hashes()
    official_02B_unchanged = official_02b_hash_before == _sha256(OFFICIAL_02B_PATH)
    output_06_unchanged = snap_before["06"] == _snapshot_production_hashes()["06"]

    stage3f_approval_ready = bool(
        input_draft_record_count == 4
        and approved_for_02b_promotion_count == 4
        and need_manual_approval_count == 0
        and reject_promotion_count == 0
        and bool(stage3e_summary.get("stage3e_draft_rebuild_pass"))
        and bool(stage3d_summary.get("stage3d_mapping_pass"))
        and production_files_unchanged
        and official_02B_unchanged
        and output_06_unchanged
    )

    summary = {
        "input_draft_record_count": int(input_draft_record_count),
        "approved_for_02b_promotion_count": int(approved_for_02b_promotion_count),
        "need_manual_approval_count": int(need_manual_approval_count),
        "reject_promotion_count": int(reject_promotion_count),
        "stage3e_draft_rebuild_pass": bool(stage3e_summary.get("stage3e_draft_rebuild_pass")),
        "original_75_rows_preserved": bool(stage3e_summary.get("original_75_rows_preserved")),
        "actual_new_row_count": int(stage3e_summary.get("actual_new_row_count", 0)),
        "duplicate_key_count": int(stage3e_summary.get("duplicate_key_count", 0)),
        "conflict_count": int(stage3e_summary.get("conflict_count", 0)),
        "hard_blocker_count": int(stage3e_summary.get("hard_blocker_count", 0)),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage3f_approval_ready": bool(stage3f_approval_ready),
        "delivery_status_after": _run_delivery_check().get("overall_status", "UNKNOWN"),
        "stage3d_mapping_pass": bool(stage3d_summary.get("stage3d_mapping_pass")),
    }

    out_xlsx = OUT_DIR / "95_stage3f_draft_promotion_approval.xlsx"
    out_md = OUT_DIR / "95_stage3f_draft_promotion_approval.md"
    out_json = OUT_DIR / "96_stage3f_draft_promotion_summary.json"

    _safe_write_excel_multi(
        {
            "approval_review": approval_df,
            "summary": pd.DataFrame([summary]),
        },
        out_xlsx,
    )

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(
        "\n".join(
            [
                "# Stage3F Draft Promotion Approval",
                "",
                f"- input_draft_record_count: {summary['input_draft_record_count']}",
                f"- approved_for_02b_promotion_count: {summary['approved_for_02b_promotion_count']}",
                f"- need_manual_approval_count: {summary['need_manual_approval_count']}",
                f"- reject_promotion_count: {summary['reject_promotion_count']}",
                f"- stage3e_draft_rebuild_pass: {summary['stage3e_draft_rebuild_pass']}",
                f"- original_75_rows_preserved: {summary['original_75_rows_preserved']}",
                f"- actual_new_row_count: {summary['actual_new_row_count']}",
                f"- duplicate_key_count: {summary['duplicate_key_count']}",
                f"- conflict_count: {summary['conflict_count']}",
                f"- hard_blocker_count: {summary['hard_blocker_count']}",
                f"- production_files_unchanged: {summary['production_files_unchanged']}",
                f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
                f"- output_06_unchanged: {summary['output_06_unchanged']}",
                f"- stage3f_approval_ready: {summary['stage3f_approval_ready']}",
                f"- delivery_status_after: {summary['delivery_status_after']}",
            ]
        ),
        encoding="utf-8",
    )
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage3f_approval_xlsx: {out_xlsx}")
    print(f"stage3f_approval_md: {out_md}")
    print(f"stage3f_approval_summary_json: {out_json}")
    for k in [
        "input_draft_record_count",
        "approved_for_02b_promotion_count",
        "need_manual_approval_count",
        "reject_promotion_count",
        "stage3e_draft_rebuild_pass",
        "original_75_rows_preserved",
        "actual_new_row_count",
        "duplicate_key_count",
        "conflict_count",
        "hard_blocker_count",
        "production_files_unchanged",
        "official_02B_unchanged",
        "output_06_unchanged",
        "stage3f_approval_ready",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
