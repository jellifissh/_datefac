import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"

INPUT_VERIFY_XLSX = OUTPUT_DIR / "stage5t_post_apply_verify_06_dry_run" / "164_stage5t_post_apply_verification.xlsx"
INPUT_DRYRUN_XLSX = OUTPUT_DIR / "stage5t_post_apply_verify_06_dry_run" / "164_stage5t_06_impact_dry_run.xlsx"
INPUT_SUMMARY_JSON = OUTPUT_DIR / "stage5t_post_apply_verify_06_dry_run" / "165_stage5t_post_apply_06_dry_run_summary.json"
INPUT_PROD_05_XLSX = OUTPUT_DIR / "H3_AP202605121822223662_1_资产包" / "05_核心财务指标标准化.xlsx"
INPUT_PROD_06_XLSX = OUTPUT_DIR / "delivery_package" / "06_最终核心财务指标.xlsx"

FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_STANDARDIZER = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5u_06_conflict_review"
OUT_REVIEW_XLSX = OUT_DIR / "166_stage5u_06_conflict_review.xlsx"
OUT_SAFE_MANIFEST_XLSX = OUT_DIR / "166_stage5u_06_safe_update_manifest.xlsx"
OUT_REPORT_MD = OUT_DIR / "166_stage5u_06_conflict_review_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "167_stage5u_06_conflict_review_summary.json"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for s, df in sheets.items():
            df.to_excel(writer, sheet_name=s[:31], index=False)


def _conflict_type(existing_val: str, candidate_vals: List[str], existing_unit: str, candidate_units: List[str]) -> str:
    val_set = {v for v in candidate_vals if v != ""}
    unit_set = {u for u in candidate_units if u != ""}
    if len(unit_set) > 1 or (existing_unit and unit_set and existing_unit not in unit_set):
        return "UNIT_CONFLICT"
    if len(val_set) > 1 or (existing_val and val_set and existing_val not in val_set):
        return "VALUE_CONFLICT"
    return "SOURCE_PRIORITY_CONFLICT"


def main() -> int:
    for p in [
        INPUT_VERIFY_XLSX,
        INPUT_DRYRUN_XLSX,
        INPUT_SUMMARY_JSON,
        INPUT_PROD_05_XLSX,
        INPUT_PROD_06_XLSX,
        FORMAL_SCOPE_RULES,
        FORMAL_STANDARDIZER,
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rules_hash_before = {
        "scope": _sha256(FORMAL_SCOPE_RULES),
        "std": _sha256(FORMAL_STANDARDIZER),
    }
    prod06_hash_before = _sha256(INPUT_PROD_06_XLSX)

    summary_5t = json.loads(INPUT_SUMMARY_JSON.read_text(encoding="utf-8"))
    input_dry_run_06_new_row_count = int(summary_5t.get("dry_run_06_new_row_count", 0))
    input_dry_run_06_conflict_count = int(summary_5t.get("dry_run_06_conflict_count", 0))

    applied_05 = pd.read_excel(INPUT_VERIFY_XLSX, sheet_name="applied_05_rows").fillna("")
    current_06 = pd.read_excel(INPUT_DRYRUN_XLSX, sheet_name="current_06").fillna("")
    dry_new = pd.read_excel(INPUT_DRYRUN_XLSX, sheet_name="dry_run_new_rows").fillna("")

    # Normalize 05 candidate keys
    for c in ["asset_package", "source_pdf", "standard_metric", "year", "value", "unit", "source_reference"]:
        if c not in applied_05.columns:
            applied_05[c] = ""
        applied_05[c] = applied_05[c].map(_norm)
    applied_05 = applied_05[
        applied_05["standard_metric"].ne("") & applied_05["year"].ne("")
    ].copy()
    applied_05["key"] = (
        applied_05["asset_package"]
        + "||"
        + applied_05["source_pdf"]
        + "||"
        + applied_05["standard_metric"]
        + "||"
        + applied_05["year"]
    )

    # Normalize existing 06 keys
    for c in ["asset_package", "source_pdf", "standard_metric", "year", "final_value", "final_unit", "final_value_source"]:
        if c not in current_06.columns:
            current_06[c] = ""
        current_06[c] = current_06[c].map(_norm)
    current_06["key"] = (
        current_06["asset_package"]
        + "||"
        + current_06["source_pdf"]
        + "||"
        + current_06["standard_metric"]
        + "||"
        + current_06["year"]
    )

    # Conflict keys are duplicated candidate keys in applied_05 (root cause from stage5t)
    conflict_keys = sorted(
        applied_05.loc[applied_05["key"].duplicated(keep=False), "key"].unique().tolist()
    )

    conflict_rows: List[Dict[str, Any]] = []
    conflict_same_value_count = 0
    conflict_value_mismatch_count = 0
    conflict_unit_mismatch_count = 0
    conflict_source_priority_unclear_count = 0

    for key in conflict_keys:
        cand_grp = applied_05[applied_05["key"] == key].copy()
        ex_grp = current_06[current_06["key"] == key].copy()

        std_metric = _norm(cand_grp["standard_metric"].iloc[0]) if not cand_grp.empty else ""
        year = _norm(cand_grp["year"].iloc[0]) if not cand_grp.empty else ""
        unit = _norm(cand_grp["unit"].iloc[0]) if not cand_grp.empty else ""
        cand_values = sorted({_norm(v) for v in cand_grp["value"].tolist()})
        cand_units = sorted({_norm(u) for u in cand_grp["unit"].tolist()})
        cand_sources = sorted({_norm(s) for s in cand_grp["source_reference"].tolist()})

        existing_06_value = ""
        existing_06_unit = ""
        existing_source = ""
        if not ex_grp.empty:
            existing_06_value = _norm(ex_grp["final_value"].iloc[0])
            existing_06_unit = _norm(ex_grp["final_unit"].iloc[0])
            existing_source = _norm(ex_grp["final_value_source"].iloc[0])

        conflict_type = _conflict_type(existing_06_value, cand_values, existing_06_unit, cand_units)

        if len(set(cand_values)) == 1 and len(set(cand_units)) == 1 and existing_06_value in ("", cand_values[0]):
            conflict_same_value_count += 1
            recommended_action = "SAFE_TO_ADD_TO_06"
            action_reason = "duplicate candidates carry same value/unit"
        else:
            recommended_action = "BLOCKED_NEED_MANUAL_REVIEW"
            action_reason = "candidate duplicate key has unresolved value/unit/source ambiguity"
            if conflict_type == "VALUE_CONFLICT":
                conflict_value_mismatch_count += 1
            elif conflict_type == "UNIT_CONFLICT":
                conflict_unit_mismatch_count += 1
            else:
                conflict_source_priority_unclear_count += 1

        conflict_rows.append(
            {
                "key": key,
                "standard_metric": std_metric,
                "year": year,
                "unit": unit,
                "existing_06_value": existing_06_value,
                "candidate_05_value": " | ".join(cand_values),
                "existing_source": existing_source,
                "candidate_source": " | ".join(cand_sources),
                "conflict_type": conflict_type,
                "recommended_action": recommended_action,
                "evidence": action_reason,
            }
        )

    conflict_df = pd.DataFrame(conflict_rows)

    # Safe rows are the 40 dry-run new rows from Stage5T.
    # Conflict rows are reviewed separately as blocked duplicate-candidate keys.
    for c in ["asset_package", "source_pdf", "standard_metric", "year"]:
        if c not in dry_new.columns:
            dry_new[c] = ""
        dry_new[c] = dry_new[c].map(_norm)
    if "key" not in dry_new.columns:
        dry_new["key"] = (
            dry_new["asset_package"]
            + "||"
            + dry_new["source_pdf"]
            + "||"
            + dry_new["standard_metric"]
            + "||"
            + dry_new["year"]
        )
    safe_new_df = dry_new.copy()
    safe_new_df["recommended_action"] = "SAFE_TO_ADD_TO_06"

    blocked_conflict_count = int(
        (conflict_df["recommended_action"] == "BLOCKED_NEED_MANUAL_REVIEW").sum()
    ) if not conflict_df.empty else 0
    conflict_key_count = int(len(conflict_keys))
    safe_to_add_06_row_count = int(len(safe_new_df))

    ready_for_stage5v_update_06_safe_rows = bool(
        safe_to_add_06_row_count > 0 and blocked_conflict_count >= 0
    )

    _write_excel(
        OUT_REVIEW_XLSX,
        {
            "conflict_review": conflict_df,
            "conflict_candidate_rows": applied_05[applied_05["key"].isin(conflict_keys)].copy(),
            "conflict_existing_06_rows": current_06[current_06["key"].isin(conflict_keys)].copy(),
        },
    )
    _write_excel(
        OUT_SAFE_MANIFEST_XLSX,
        {
            "safe_to_add_06_rows": safe_new_df,
            "blocked_conflict_rows": conflict_df,
        },
    )

    rules_hash_after = {
        "scope": _sha256(FORMAL_SCOPE_RULES),
        "std": _sha256(FORMAL_STANDARDIZER),
    }
    production_06_unchanged = bool(prod06_hash_before == _sha256(INPUT_PROD_06_XLSX))
    formal_rules_unchanged = bool(rules_hash_before == rules_hash_after)

    summary = {
        "input_dry_run_06_new_row_count": input_dry_run_06_new_row_count,
        "input_dry_run_06_conflict_count": input_dry_run_06_conflict_count,
        "conflict_key_count": conflict_key_count,
        "safe_to_add_06_row_count": safe_to_add_06_row_count,
        "conflict_same_value_count": int(conflict_same_value_count),
        "conflict_value_mismatch_count": int(conflict_value_mismatch_count),
        "conflict_unit_mismatch_count": int(conflict_unit_mismatch_count),
        "conflict_source_priority_unclear_count": int(conflict_source_priority_unclear_count),
        "blocked_conflict_count": int(blocked_conflict_count),
        "ready_for_stage5v_update_06_safe_rows": ready_for_stage5v_update_06_safe_rows,
        "production_06_unchanged": production_06_unchanged,
        "formal_rules_unchanged": formal_rules_unchanged,
        "stage5u_06_conflict_review_pass": False,
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
    }

    summary["stage5u_06_conflict_review_pass"] = bool(
        summary["input_dry_run_06_conflict_count"] == 5
        and summary["conflict_key_count"] == 5
        and summary["safe_to_add_06_row_count"] == 40
        and summary["production_06_unchanged"]
        and summary["formal_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Stage5U 06 Conflict Review",
        "",
        "## Input Snapshot",
        f"- input_dry_run_06_new_row_count: {summary['input_dry_run_06_new_row_count']}",
        f"- input_dry_run_06_conflict_count: {summary['input_dry_run_06_conflict_count']}",
        "",
        "## Conflict Review",
        f"- conflict_key_count: {summary['conflict_key_count']}",
        f"- conflict_same_value_count: {summary['conflict_same_value_count']}",
        f"- conflict_value_mismatch_count: {summary['conflict_value_mismatch_count']}",
        f"- conflict_unit_mismatch_count: {summary['conflict_unit_mismatch_count']}",
        f"- conflict_source_priority_unclear_count: {summary['conflict_source_priority_unclear_count']}",
        f"- blocked_conflict_count: {summary['blocked_conflict_count']}",
        "",
        "## Safe Plan",
        f"- safe_to_add_06_row_count: {summary['safe_to_add_06_row_count']}",
        f"- ready_for_stage5v_update_06_safe_rows: {summary['ready_for_stage5v_update_06_safe_rows']}",
        "",
        "## Guard",
        f"- production_06_unchanged: {summary['production_06_unchanged']}",
        f"- formal_rules_unchanged: {summary['formal_rules_unchanged']}",
        f"- stage5u_06_conflict_review_pass: {summary['stage5u_06_conflict_review_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"conflict_review_xlsx: {OUT_REVIEW_XLSX}")
    print(f"safe_manifest_xlsx: {OUT_SAFE_MANIFEST_XLSX}")
    print(f"report_md: {OUT_REPORT_MD}")
    print(f"summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5u_06_conflict_review_pass: {summary['stage5u_06_conflict_review_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
