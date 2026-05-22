import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_PATH = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_NORMALIZATION_RULES_PATH = BASE_DIR / "financial_standardizer.py"

STAGE4A_SUMMARY = OUTPUT_DIR / "stage4a_structured_inventory" / "106_stage4a_structured_layer_inventory_summary.json"
STAGE4B_SUMMARY = OUTPUT_DIR / "stage4b_mapping_gap_classification" / "108_stage4b_mapping_gap_classification_summary.json"
STAGE4C_SUMMARY = OUTPUT_DIR / "stage4c_mapping_rule_draft" / "110_stage4c_mapping_rule_draft_summary.json"
STAGE4D_SUMMARY = OUTPUT_DIR / "stage4d_mapping_rule_validation" / "112_stage4d_mapping_rule_validation_summary.json"
STAGE4E_SUMMARY = OUTPUT_DIR / "stage4e_normalization_scope_fix_draft" / "114_stage4e_normalization_scope_fix_summary.json"
STAGE4F_SUMMARY = OUTPUT_DIR / "stage4f_dry_run_validate_fixes" / "116_stage4f_dry_run_validate_fixes_summary.json"
STAGE4G_SUMMARY = OUTPUT_DIR / "stage4g_scope_promotion_approval" / "118_stage4g_scope_promotion_summary.json"
STAGE4H_SUMMARY = OUTPUT_DIR / "stage4h_promote_scope_fixes" / "120_stage4h_scope_promotion_summary.json"
STAGE4I_SUMMARY = OUTPUT_DIR / "stage4i_validate_formal_scope_rules" / "122_stage4i_validate_formal_scope_rules_summary.json"
STAGE4J_SUMMARY = OUTPUT_DIR / "stage4j_downstream_impact_dry_run" / "124_stage4j_downstream_impact_summary.json"

OUT_DIR = OUTPUT_DIR / "stage4k_closure"
OUT_JSON = OUT_DIR / "125_stage4k_closure_summary.json"
OUT_MD = OUT_DIR / "125_stage4k_closure.md"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str, prefer_no_copy: bool = True, prefer_no_backup: bool = True) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing required file pattern: {pattern}")
    picked = files
    if prefer_no_copy:
        p2 = [p for p in picked if "_copy_" not in p.name.lower()]
        if p2:
            picked = p2
    if prefer_no_backup:
        p3 = [p for p in picked if "backup" not in p.name.lower()]
        if p3:
            picked = p3
    return picked[0]


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def _snapshot_hashes() -> Dict[str, str]:
    p01 = _find_delivery_file("01_*.xlsx")
    p02 = _find_delivery_file("02_*.xlsx")
    p02a = _find_delivery_file("02A_*.xlsx")
    p05 = _find_delivery_file("05_*.xlsx")
    p06 = _find_delivery_file("06_*.xlsx")
    return {
        "01": _sha256(p01),
        "02": _sha256(p02),
        "02A": _sha256(p02a),
        "05": _sha256(p05),
        "06": _sha256(p06),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_PATH),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULES_PATH),
    }


def _safe_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4K closure verification for structured-layer scope rule repair.")
    parser.parse_args()

    required_paths = [
        OFFICIAL_02B_PATH,
        FORMAL_SCOPE_RULES_PATH,
        FORMAL_NORMALIZATION_RULES_PATH,
        STAGE4A_SUMMARY,
        STAGE4B_SUMMARY,
        STAGE4C_SUMMARY,
        STAGE4D_SUMMARY,
        STAGE4E_SUMMARY,
        STAGE4F_SUMMARY,
        STAGE4G_SUMMARY,
        STAGE4H_SUMMARY,
        STAGE4I_SUMMARY,
        STAGE4J_SUMMARY,
    ]
    for p in required_paths:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    snapshot_before = _snapshot_hashes()

    s4a = _load_json(STAGE4A_SUMMARY)
    s4b = _load_json(STAGE4B_SUMMARY)
    s4c = _load_json(STAGE4C_SUMMARY)
    s4d = _load_json(STAGE4D_SUMMARY)
    s4e = _load_json(STAGE4E_SUMMARY)
    s4f = _load_json(STAGE4F_SUMMARY)
    s4g = _load_json(STAGE4G_SUMMARY)
    s4h = _load_json(STAGE4H_SUMMARY)
    s4i = _load_json(STAGE4I_SUMMARY)
    s4j = _load_json(STAGE4J_SUMMARY)

    # Read-only touch of delivery layers to enforce boundary check coverage.
    _ = pd.read_excel(_find_delivery_file("01_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02A_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")
    _ = pd.read_excel(OFFICIAL_02B_PATH).fillna("")

    snapshot_after = _snapshot_hashes()
    production_01_unchanged = snapshot_before["01"] == snapshot_after["01"]
    production_02_unchanged = snapshot_before["02"] == snapshot_after["02"]
    production_02A_unchanged = snapshot_before["02A"] == snapshot_after["02A"]
    production_05_unchanged = snapshot_before["05"] == snapshot_after["05"]
    production_06_unchanged = snapshot_before["06"] == snapshot_after["06"]
    official_02B_unchanged = snapshot_before["02B"] == snapshot_after["02B"]

    delivery_status_after = _run_delivery_check().get("overall_status", "UNKNOWN")

    promoted_scope_fix_count = int(s4j.get("promoted_scope_fix_count", 0))
    matched_formal_scope_rule_count = int(s4j.get("matched_formal_scope_rule_count", 0))
    conflict_with_05_count = int(s4j.get("conflict_with_05_count", 0))
    conflict_with_01_count = int(s4j.get("conflict_with_01_count", 0))
    conflict_with_06_count = int(s4j.get("conflict_with_06_count", 0))
    conflict_with_02B_count = int(s4j.get("conflict_with_02B_count", 0))
    duplicate_after_dry_run_count = int(s4j.get("duplicate_after_dry_run_count", 0))

    formal_scope_rules_changed_in_stage4h = _to_bool(s4h.get("formal_mapping_rules_changed", False))
    formal_scope_rules_validated_in_stage4i = _to_bool(s4i.get("stage4i_formal_scope_validation_pass", False))
    downstream_impact_pass_in_stage4j = _to_bool(s4j.get("stage4j_downstream_impact_pass", False))

    stage4_closed = bool(
        _to_bool(s4a.get("stage4a_inventory_pass", False))
        and _to_bool(s4b.get("stage4b_classification_pass", False))
        and _to_bool(s4c.get("stage4c_mapping_rule_draft_ready", False))
        and _to_bool(s4d.get("stage4d_validation_pass", False))
        and _to_bool(s4e.get("stage4e_fix_draft_ready", False))
        and _to_bool(s4f.get("stage4f_dry_run_validation_pass", False))
        and _to_bool(s4g.get("stage4g_scope_promotion_approval_ready", False))
        and _to_bool(s4h.get("stage4h_scope_promotion_pass", False))
        and formal_scope_rules_changed_in_stage4h
        and formal_scope_rules_validated_in_stage4i
        and downstream_impact_pass_in_stage4j
        and promoted_scope_fix_count == 15
        and matched_formal_scope_rule_count == 15
        and conflict_with_05_count == 0
        and conflict_with_01_count == 0
        and conflict_with_06_count == 0
        and conflict_with_02B_count == 0
        and duplicate_after_dry_run_count == 0
        and production_01_unchanged
        and production_02_unchanged
        and production_02A_unchanged
        and production_05_unchanged
        and production_06_unchanged
        and official_02B_unchanged
        and delivery_status_after == "PASS"
    )

    summary = {
        "stage4_closed": bool(stage4_closed),
        "promoted_scope_fix_count": promoted_scope_fix_count,
        "matched_formal_scope_rule_count": matched_formal_scope_rule_count,
        "conflict_with_05_count": conflict_with_05_count,
        "conflict_with_01_count": conflict_with_01_count,
        "conflict_with_06_count": conflict_with_06_count,
        "conflict_with_02B_count": conflict_with_02B_count,
        "duplicate_after_dry_run_count": duplicate_after_dry_run_count,
        "production_01_unchanged": bool(production_01_unchanged),
        "production_02_unchanged": bool(production_02_unchanged),
        "production_02A_unchanged": bool(production_02A_unchanged),
        "production_05_unchanged": bool(production_05_unchanged),
        "production_06_unchanged": bool(production_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_changed_in_stage4h": bool(formal_scope_rules_changed_in_stage4h),
        "formal_scope_rules_validated_in_stage4i": bool(formal_scope_rules_validated_in_stage4i),
        "downstream_impact_pass_in_stage4j": bool(downstream_impact_pass_in_stage4j),
        "delivery_status_after": delivery_status_after,
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
    }

    md_lines: List[str] = [
        "# Stage 4K Scope Rule Repair Closure Summary",
        "",
        f"- stage4_closed: {summary['stage4_closed']}",
        f"- promoted_scope_fix_count: {summary['promoted_scope_fix_count']}",
        f"- matched_formal_scope_rule_count: {summary['matched_formal_scope_rule_count']}",
        f"- conflict_with_05_count: {summary['conflict_with_05_count']}",
        f"- conflict_with_01_count: {summary['conflict_with_01_count']}",
        f"- conflict_with_06_count: {summary['conflict_with_06_count']}",
        f"- conflict_with_02B_count: {summary['conflict_with_02B_count']}",
        f"- duplicate_after_dry_run_count: {summary['duplicate_after_dry_run_count']}",
        f"- production_01_unchanged: {summary['production_01_unchanged']}",
        f"- production_02_unchanged: {summary['production_02_unchanged']}",
        f"- production_02A_unchanged: {summary['production_02A_unchanged']}",
        f"- production_05_unchanged: {summary['production_05_unchanged']}",
        f"- production_06_unchanged: {summary['production_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_changed_in_stage4h: {summary['formal_scope_rules_changed_in_stage4h']}",
        f"- formal_scope_rules_validated_in_stage4i: {summary['formal_scope_rules_validated_in_stage4i']}",
        f"- downstream_impact_pass_in_stage4j: {summary['downstream_impact_pass_in_stage4j']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
    ]

    _safe_write_text(json.dumps(summary, ensure_ascii=False, indent=2), OUT_JSON)
    _safe_write_text("\n".join(md_lines), OUT_MD)

    print(f"stage4k_summary_json: {OUT_JSON}")
    print(f"stage4k_summary_md: {OUT_MD}")
    for k in [
        "stage4_closed",
        "promoted_scope_fix_count",
        "matched_formal_scope_rule_count",
        "conflict_with_05_count",
        "conflict_with_01_count",
        "conflict_with_06_count",
        "conflict_with_02B_count",
        "duplicate_after_dry_run_count",
        "production_01_unchanged",
        "production_02_unchanged",
        "production_02A_unchanged",
        "production_05_unchanged",
        "production_06_unchanged",
        "official_02B_unchanged",
        "formal_scope_rules_changed_in_stage4h",
        "formal_scope_rules_validated_in_stage4i",
        "downstream_impact_pass_in_stage4j",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
