import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_CONFLICT_REVIEW_XLSX = OUTPUT_DIR / "stage5u_06_conflict_review" / "166_stage5u_06_conflict_review.xlsx"
INPUT_STAGE5U_SUMMARY_JSON = OUTPUT_DIR / "stage5u_06_conflict_review" / "167_stage5u_06_conflict_review_summary.json"
INPUT_STAGE5V2_SUMMARY_JSON = OUTPUT_DIR / "stage5v2_update_06_safe_rows_excluding_eps" / "171_stage5v2_update_06_summary.json"
INPUT_PROD_05_XLSX = OUTPUT_DIR / "H3_AP202605121822223662_1_资产包" / "05_核心财务指标标准化.xlsx"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5w_eps_unit_conflict_review"
OUT_REVIEW_XLSX = OUT_DIR / "172_stage5w_eps_conflict_review.xlsx"
OUT_REPORT_MD = OUT_DIR / "172_stage5w_eps_unit_decision_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "173_stage5w_eps_unit_conflict_summary.json"


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


def _find_prod_06() -> Path:
    candidates = sorted(DELIVERY_DIR.glob("06_*.xlsx"))
    if not candidates:
        raise FileNotFoundError("No production 06 workbook found in output/delivery_package.")
    non_copy = [p for p in candidates if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else candidates[0]


def main() -> int:
    required = [
        INPUT_CONFLICT_REVIEW_XLSX,
        INPUT_STAGE5U_SUMMARY_JSON,
        INPUT_STAGE5V2_SUMMARY_JSON,
        INPUT_PROD_05_XLSX,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_STANDARDIZER_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    prod06_file = _find_prod_06()
    hash_06_before = _sha256(prod06_file)
    rules_before = {
        "scope": _sha256(FORMAL_SCOPE_RULES_JSON),
        "std": _sha256(FORMAL_STANDARDIZER_FILE),
    }

    s5u = json.loads(INPUT_STAGE5U_SUMMARY_JSON.read_text(encoding="utf-8"))
    s5v2 = json.loads(INPUT_STAGE5V2_SUMMARY_JSON.read_text(encoding="utf-8"))
    if int(s5u.get("conflict_key_count", -1)) != 5:
        raise RuntimeError("Precondition failed: Stage5U conflict_key_count is not 5.")
    if int(s5v2.get("eps_conflict_excluded_count", -1)) != 5:
        raise RuntimeError("Precondition failed: Stage5V2 eps_conflict_excluded_count is not 5.")

    conflict_review = pd.read_excel(INPUT_CONFLICT_REVIEW_XLSX, sheet_name="conflict_review").fillna("")
    conflict_candidates = pd.read_excel(INPUT_CONFLICT_REVIEW_XLSX, sheet_name="conflict_candidate_rows").fillna("")
    current_06 = pd.read_excel(prod06_file).fillna("")
    prod05_detail = pd.read_excel(INPUT_PROD_05_XLSX, sheet_name="抽取明细").fillna("")

    conflict_review["standard_metric"] = conflict_review.get("standard_metric", "").map(_norm)
    conflict_review["year"] = conflict_review.get("year", "").map(_norm)
    conflict_review["key"] = conflict_review.get("key", "").map(_norm)

    eps_conflicts = conflict_review[conflict_review["standard_metric"] == "每股收益"].copy()
    eps_conflicts = eps_conflicts.sort_values("year")

    # Build lookup maps
    current_06["asset_package"] = current_06.get("asset_package", "").map(_norm)
    current_06["source_pdf"] = current_06.get("source_pdf", "").map(_norm)
    current_06["standard_metric"] = current_06.get("standard_metric", "").map(_norm)
    current_06["year"] = current_06.get("year", "").map(_norm)
    current_06["final_value"] = current_06.get("final_value", "").map(_norm)
    current_06["final_unit"] = current_06.get("final_unit", "").map(_norm)
    current_06["final_value_source"] = current_06.get("final_value_source", "").map(_norm)
    current_06["key"] = (
        current_06["asset_package"]
        + "||"
        + current_06["source_pdf"]
        + "||"
        + current_06["standard_metric"]
        + "||"
        + current_06["year"]
    )

    conflict_candidates["key"] = conflict_candidates.get("key", "").map(_norm)
    conflict_candidates["value"] = conflict_candidates.get("value", "").map(_norm)
    conflict_candidates["unit"] = conflict_candidates.get("unit", "").map(_norm)
    conflict_candidates["source_reference"] = conflict_candidates.get("source_reference", "").map(_norm)

    rows: List[Dict[str, Any]] = []
    recommended_keep_existing_count = 0
    recommended_replace_with_candidate_count = 0
    recommended_unit_normalization_rule_count = 0

    for _, row in eps_conflicts.iterrows():
        key = _norm(row.get("key", ""))
        year = _norm(row.get("year", ""))
        cand_grp = conflict_candidates[conflict_candidates["key"] == key].copy()
        ex_grp = current_06[current_06["key"] == key].copy()

        existing_06_value = _norm(ex_grp["final_value"].iloc[0]) if not ex_grp.empty else ""
        existing_06_unit = _norm(ex_grp["final_unit"].iloc[0]) if not ex_grp.empty else ""
        existing_06_source = _norm(ex_grp["final_value_source"].iloc[0]) if not ex_grp.empty else ""

        cand_values = sorted({v for v in cand_grp["value"].tolist() if v != ""})
        cand_units = sorted({u for u in cand_grp["unit"].tolist() if u != ""})
        cand_sources = sorted({s for s in cand_grp["source_reference"].tolist() if s != ""})

        candidate_value = cand_values[0] if len(cand_values) == 1 else " | ".join(cand_values)
        candidate_unit = " | ".join(cand_units)

        candidate_values_consistent = len(cand_values) <= 1
        value_same = bool(candidate_values_consistent and (existing_06_value in ("", candidate_value)))

        if "ratio" in cand_units and ("元" in cand_units or "元/股" in cand_units):
            unit_conflict_type = "RATIO_VS_CURRENCY_UNIT"
        elif len(cand_units) > 1:
            unit_conflict_type = "MULTI_CANDIDATE_UNIT_CONFLICT"
        elif existing_06_unit and cand_units and existing_06_unit not in cand_units:
            unit_conflict_type = "EXISTING_VS_CANDIDATE_UNIT_MISMATCH"
        else:
            unit_conflict_type = "NO_UNIT_CONFLICT"

        if existing_06_value != "":
            if value_same and unit_conflict_type == "NO_UNIT_CONFLICT":
                recommended_action = "KEEP_EXISTING_06"
                recommended_keep_existing_count += 1
            else:
                recommended_action = "NEED_MANUAL_UNIT_ADJUDICATION"
        else:
            # No existing 06 row: candidate value is internally consistent, unit needs canonicalization
            if candidate_values_consistent and unit_conflict_type != "NO_UNIT_CONFLICT":
                recommended_action = "ADD_WITH_UNIT_NORMALIZATION_TO_元/股"
                recommended_replace_with_candidate_count += 1
                recommended_unit_normalization_rule_count = 1
            elif candidate_values_consistent:
                recommended_action = "ADD_CANDIDATE_AS_IS"
                recommended_replace_with_candidate_count += 1
            else:
                recommended_action = "BLOCKED_VALUE_INCONSISTENT"

        evidence = (
            f"candidate_units={candidate_unit}; candidate_sources={' | '.join(cand_sources)}; "
            f"existing_source={existing_06_source}; prod05_detail_rows={len(prod05_detail)}"
        )

        rows.append(
            {
                "key": key,
                "year": year,
                "existing_06_value": existing_06_value,
                "existing_06_unit": existing_06_unit,
                "candidate_value": candidate_value,
                "candidate_unit": candidate_unit,
                "value_same": value_same,
                "unit_conflict_type": unit_conflict_type,
                "recommended_action": recommended_action,
                "evidence": evidence,
            }
        )

    review_df = pd.DataFrame(rows)
    review_df = review_df.sort_values("year")

    eps_conflict_count = int(len(review_df))
    eps_value_same_count = int(review_df["value_same"].sum()) if not review_df.empty else 0
    eps_value_mismatch_count = int(eps_conflict_count - eps_value_same_count)
    eps_unit_conflict_count = int(
        review_df["unit_conflict_type"].map(_norm).ne("NO_UNIT_CONFLICT").sum()
    ) if not review_df.empty else 0

    # Recommended standard unit decision
    recommended_standard_eps_unit = "元/股"

    ready_for_stage5x_eps_apply = bool(
        eps_conflict_count == 5
        and eps_value_mismatch_count == 0
        and eps_unit_conflict_count == 5
        and recommended_replace_with_candidate_count == 5
    )

    _write_excel(
        OUT_REVIEW_XLSX,
        {
            "eps_conflict_review": review_df,
            "source_conflict_review": conflict_review,
            "source_conflict_candidates": conflict_candidates,
        },
    )

    rules_after = {
        "scope": _sha256(FORMAL_SCOPE_RULES_JSON),
        "std": _sha256(FORMAL_STANDARDIZER_FILE),
    }
    production_06_unchanged = bool(hash_06_before == _sha256(prod06_file))
    formal_rules_unchanged = bool(rules_before == rules_after)

    summary = {
        "eps_conflict_count": eps_conflict_count,
        "eps_value_same_count": eps_value_same_count,
        "eps_value_mismatch_count": eps_value_mismatch_count,
        "eps_unit_conflict_count": eps_unit_conflict_count,
        "recommended_keep_existing_count": int(recommended_keep_existing_count),
        "recommended_replace_with_candidate_count": int(recommended_replace_with_candidate_count),
        "recommended_unit_normalization_rule_count": int(recommended_unit_normalization_rule_count),
        "recommended_standard_eps_unit": recommended_standard_eps_unit,
        "ready_for_stage5x_eps_apply": ready_for_stage5x_eps_apply,
        "production_06_unchanged": production_06_unchanged,
        "formal_rules_unchanged": formal_rules_unchanged,
        "stage5w_eps_conflict_review_pass": False,
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
    }

    summary["stage5w_eps_conflict_review_pass"] = bool(
        summary["eps_conflict_count"] == 5
        and summary["eps_unit_conflict_count"] == 5
        and summary["production_06_unchanged"]
        and summary["formal_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Stage5W EPS Unit Conflict Review",
        "",
        "## Decision",
        f"- recommended_standard_eps_unit: {recommended_standard_eps_unit}",
        f"- ready_for_stage5x_eps_apply: {summary['ready_for_stage5x_eps_apply']}",
        "",
        "## Counts",
        f"- eps_conflict_count: {summary['eps_conflict_count']}",
        f"- eps_value_same_count: {summary['eps_value_same_count']}",
        f"- eps_value_mismatch_count: {summary['eps_value_mismatch_count']}",
        f"- eps_unit_conflict_count: {summary['eps_unit_conflict_count']}",
        f"- recommended_keep_existing_count: {summary['recommended_keep_existing_count']}",
        f"- recommended_replace_with_candidate_count: {summary['recommended_replace_with_candidate_count']}",
        f"- recommended_unit_normalization_rule_count: {summary['recommended_unit_normalization_rule_count']}",
        "",
        "## Guard",
        f"- production_06_unchanged: {summary['production_06_unchanged']}",
        f"- formal_rules_unchanged: {summary['formal_rules_unchanged']}",
        f"- stage5w_eps_conflict_review_pass: {summary['stage5w_eps_conflict_review_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"eps_conflict_review_xlsx: {OUT_REVIEW_XLSX}")
    print(f"eps_unit_decision_report_md: {OUT_REPORT_MD}")
    print(f"eps_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5w_eps_conflict_review_pass: {summary['stage5w_eps_conflict_review_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
