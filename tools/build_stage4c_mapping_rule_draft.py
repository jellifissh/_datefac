import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"
STAGE4B_XLSX = OUTPUT_DIR / "stage4b_mapping_gap_classification" / "107_stage4b_mapping_gap_classification.xlsx"
STAGE4B_SUMMARY = OUTPUT_DIR / "stage4b_mapping_gap_classification" / "108_stage4b_mapping_gap_classification_summary.json"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
DRAFT_DIR = BASE_DIR / "data" / "mapping" / "drafts"
DRAFT_XLSX = DRAFT_DIR / "stage4c_mapping_rule_draft.xlsx"
REPORT_DIR = OUTPUT_DIR / "stage4c_mapping_rule_draft"
FORMAL_MAPPING_RULE_FILE = BASE_DIR / "financial_standardizer.py"


READY_ACTION = "READY_FOR_MAPPING_RULE_DRAFT"
STATUS_DRAFT_READY = "DRAFT_READY"

CONF_HIGH = "HIGH"
CONF_MEDIUM = "MEDIUM"
ALLOWED_CONFIDENCE = {CONF_HIGH, CONF_MEDIUM}

SCOPE_GLOBAL = "GLOBAL"
SCOPE_PACKAGE = "PACKAGE_SPECIFIC_CANDIDATE"
ALLOWED_SCOPE = {SCOPE_GLOBAL, SCOPE_PACKAGE}


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


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_mapping_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
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
                return {"overall_status": "UNKNOWN"}
    return {"overall_status": "UNKNOWN"}


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def _safe_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _compact_text(value: Any) -> str:
    text = _norm(value)
    text = text.replace("（", "(").replace("）", ")").replace("％", "%")
    text = re.sub(r"\s+", "", text)
    return text.upper()


def _clean_metric_label_noise(label: str) -> str:
    text = _norm(label)
    if not text:
        return ""
    text = text.replace("（", "(").replace("）", ")").replace("／", "/")
    text = re.sub(r"\s+", " ", text).strip()

    compact = _compact_text(text)
    has_metric_token = any(
        token in compact
        for token in (
            "EV/EBITDA",
            "EVEBITDA",
            "EPS",
            "ROE",
            "P/E",
            "P/B",
            "营业收入",
            "归属母公司",
            "归母净利润",
            "毛利率",
            "每股收益",
        )
    )
    if not has_metric_token:
        return text

    text = re.sub(
        r"([\s\|,:：;；]+[-+]?\d*\.?\d+(?:[%％])?)+\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    return text


def _load_existing_alias_map() -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    mod = __import__("financial_standardizer")
    aliases: Dict[str, List[str]] = getattr(mod, "STANDARD_METRIC_ALIASES", {})  # type: ignore
    exact_to_standard: Dict[str, str] = {}
    compact_to_standards: Dict[str, Set[str]] = {}
    for standard, raw_list in aliases.items():
        for raw in raw_list:
            r = _norm(raw)
            if not r:
                continue
            exact_to_standard[r] = _norm(standard)
            c = _compact_text(r)
            compact_to_standards.setdefault(c, set()).add(_norm(standard))
    return exact_to_standard, compact_to_standards


def _year_cols(columns: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for c in columns:
        cc = _norm(c)
        if re.fullmatch(r"20\d{2}(?:[AE])?", cc, flags=re.IGNORECASE):
            out.append(cc)
    return out


def _first_existing_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _find_asset_dirs() -> List[Path]:
    out = []
    for p in OUTPUT_DIR.iterdir():
        if not p.is_dir():
            continue
        n = p.name
        if ("资产包" in n) and (n.endswith("_资产包") or n.endswith("资产包")):
            out.append(p)
    return sorted(out)


def _pick_latest_asset_file(asset_dir: Path, prefix: str, include_keywords: Optional[List[str]] = None) -> Optional[Path]:
    files = []
    for p in asset_dir.glob(f"{prefix}*.xlsx"):
        low = p.name.lower()
        if "backup" in low or "copy" in low or "副本" in p.name:
            continue
        if include_keywords and not all(k in p.name for k in include_keywords):
            continue
        files.append(p)
    if not files:
        return None
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]


def _build_05_statement_type_map() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for asset_dir in _find_asset_dirs():
        f05 = _pick_latest_asset_file(asset_dir, "05_", include_keywords=["核心财务指标"])
        if not f05:
            f05 = _pick_latest_asset_file(asset_dir, "05_")
        if not f05:
            continue
        try:
            xls = pd.ExcelFile(f05)
        except Exception:
            continue
        if "抽取明细" not in xls.sheet_names:
            continue
        try:
            df = pd.read_excel(f05, sheet_name="抽取明细").fillna("")
        except Exception:
            continue
        if df.empty:
            continue
        col_metric = _first_existing_column(df, ["标准指标", "standard_metric", "指标"])
        col_stmt = _first_existing_column(df, ["source_table_type", "statement_type"])
        yc = _year_cols(df.columns)
        if not col_metric or not yc:
            continue
        for _, r in df.iterrows():
            metric = _norm(r.get(col_metric))
            if not metric:
                continue
            stmt = _norm(r.get(col_stmt)) if col_stmt else ""
            for y in yc:
                value = _norm(r.get(y))
                if not value:
                    continue
                key = "|".join([asset_dir.name, metric, y])
                if key not in out:
                    out[key] = stmt
    return out


def _confidence_from_priority(priority: str) -> str:
    p = _norm(priority).upper()
    if p == "HIGH":
        return CONF_HIGH
    return CONF_MEDIUM


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage4C build draft mapping rules from Stage4B READY gaps.")
    parser.parse_args()

    for p in [STAGE4B_XLSX, STAGE4B_SUMMARY, OFFICIAL_02B_PATH, FORMAL_MAPPING_RULE_FILE]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    snapshot_before = _snapshot_hashes()

    # Read required layer files for boundary check / read-only compliance.
    _ = pd.read_excel(_find_delivery_file("01_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("02_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    _ = pd.read_excel(_find_delivery_file("06_*.xlsx")).fillna("")

    stage4b_summary = json.loads(STAGE4B_SUMMARY.read_text(encoding="utf-8"))
    if not bool(stage4b_summary.get("stage4b_classification_pass", False)):
        raise RuntimeError("Stage4B summary indicates pass=false, aborting Stage4C draft.")

    df = pd.read_excel(STAGE4B_XLSX, sheet_name="stage4b_classification").fillna("")
    ready_df = df[df["recommended_stage4b_action"].map(_norm) == READY_ACTION].copy()
    input_ready_mapping_gap_count = len(ready_df)

    exact_alias_map, compact_alias_map = _load_existing_alias_map()
    statement_type_map = _build_05_statement_type_map()

    # For scope decision: raw -> number of distinct assets.
    raw_asset_count = (
        ready_df[["raw_metric_name", "asset_package"]]
        .assign(raw_metric_name=ready_df["raw_metric_name"].map(_norm))
        .drop_duplicates()
        .groupby("raw_metric_name")
        .size()
        .to_dict()
    )

    # Build report rows at record level (28 inputs).
    rec_rows: List[Dict[str, Any]] = []
    possible_overlap_rows: List[Dict[str, Any]] = []
    already_existing_rule_count = 0
    conflict_rule_count = 0
    possible_overlap_count = 0
    missing_required_field_count = 0

    for _, r in ready_df.iterrows():
        issue_id = _norm(r.get("issue_id"))
        asset = _norm(r.get("asset_package"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        standard_metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        source_layer = _norm(r.get("source_layer"))
        target_layer = _norm(r.get("target_layer"))
        current_value = _norm(r.get("current_value"))
        current_unit = _norm(r.get("current_unit"))
        mapping_gap_category = _norm(r.get("mapping_gap_category"))
        priority = _norm(r.get("priority")).upper() or "MEDIUM"
        stage4b_action_reason = _norm(r.get("action_reason"))

        normalized_raw = _clean_metric_label_noise(raw_metric_name)
        if not normalized_raw:
            normalized_raw = raw_metric_name

        rule_scope = SCOPE_GLOBAL if int(raw_asset_count.get(raw_metric_name, 0)) >= 2 else SCOPE_PACKAGE
        confidence_level = _confidence_from_priority(priority)
        if confidence_level not in ALLOWED_CONFIDENCE:
            confidence_level = CONF_MEDIUM
        if rule_scope not in ALLOWED_SCOPE:
            rule_scope = SCOPE_PACKAGE
        if priority not in {"HIGH", "MEDIUM", "LOW"}:
            priority = "MEDIUM"

        stmt_key = "|".join([asset, standard_metric, year])
        statement_type = _norm(statement_type_map.get(stmt_key))
        evidence_source = f"stage4b:{issue_id};source={source_layer};target={target_layer};value={current_value}"

        missing_required = (not raw_metric_name) or (not standard_metric)
        if missing_required:
            missing_required_field_count += 1

        already_existing = False
        conflict = False
        possible_overlap = False

        exact_existing_std = exact_alias_map.get(raw_metric_name)
        if exact_existing_std:
            if exact_existing_std == standard_metric:
                already_existing = True
            else:
                conflict = True

        compact_raw = _compact_text(raw_metric_name)
        compact_norm = _compact_text(normalized_raw)
        compact_candidates = [c for c in [compact_raw, compact_norm] if c]
        if not already_existing and not conflict:
            for c in compact_candidates:
                matched_standards = compact_alias_map.get(c, set())
                if not matched_standards:
                    continue
                if standard_metric in matched_standards:
                    possible_overlap = True
                elif len(matched_standards) > 0:
                    conflict = True
                if possible_overlap or conflict:
                    break

        if already_existing:
            already_existing_rule_count += 1
        if conflict:
            conflict_rule_count += 1
        if possible_overlap:
            possible_overlap_count += 1
            possible_overlap_rows.append(
                {
                    "issue_id": issue_id,
                    "asset_package": asset,
                    "raw_metric_name": raw_metric_name,
                    "normalized_raw_metric_name": normalized_raw,
                    "proposed_standard_metric": standard_metric,
                    "overlap_reason": "normalized form overlaps with existing alias rule",
                }
            )

        rec_rows.append(
            {
                "issue_id": issue_id,
                "asset_package": asset,
                "raw_metric_name": raw_metric_name,
                "normalized_raw_metric_name": normalized_raw,
                "proposed_standard_metric": standard_metric,
                "statement_type": statement_type,
                "year": year,
                "source_layer": source_layer,
                "target_layer": target_layer,
                "current_value": current_value,
                "current_unit": current_unit,
                "mapping_gap_category": mapping_gap_category,
                "priority": priority,
                "rule_scope": rule_scope,
                "confidence_level": confidence_level,
                "evidence_source": evidence_source,
                "stage4b_action_reason": stage4b_action_reason,
                "draft_status": STATUS_DRAFT_READY,
                "already_existing": bool(already_existing),
                "conflict": bool(conflict),
                "possible_overlap": bool(possible_overlap),
                "missing_required_field": bool(missing_required),
            }
        )

    rec_df = pd.DataFrame(rec_rows)

    # Build draft rows: exclude already_existing/conflict/missing_required.
    draft_candidates = rec_df[
        (~rec_df["already_existing"]) & (~rec_df["conflict"]) & (~rec_df["missing_required_field"])
    ].copy()

    # Enforce dedupe: raw_metric_name + proposed_standard_metric + rule_scope.
    dedupe_key_cols = ["raw_metric_name", "proposed_standard_metric", "rule_scope"]
    draft_candidates["__rank"] = (
        draft_candidates["priority"].map({"HIGH": 0, "MEDIUM": 1, "LOW": 2}).fillna(3).astype(int)
    )
    draft_candidates = draft_candidates.sort_values(
        by=["__rank", "issue_id"], kind="mergesort"
    ).reset_index(drop=True)

    duplicate_draft_rule_count = int(
        draft_candidates.duplicated(subset=dedupe_key_cols, keep=False).sum()
    )
    draft_unique = draft_candidates.drop_duplicates(subset=dedupe_key_cols, keep="first").copy()

    # Assign draft rule id after dedupe.
    draft_unique = draft_unique.reset_index(drop=True)
    draft_unique["draft_rule_id"] = [
        f"S4C-RULE-{i:04d}" for i in range(1, len(draft_unique) + 1)
    ]

    draft_cols = [
        "draft_rule_id",
        "issue_id",
        "asset_package",
        "raw_metric_name",
        "normalized_raw_metric_name",
        "proposed_standard_metric",
        "statement_type",
        "year",
        "source_layer",
        "target_layer",
        "current_value",
        "current_unit",
        "mapping_gap_category",
        "priority",
        "rule_scope",
        "confidence_level",
        "evidence_source",
        "stage4b_action_reason",
        "draft_status",
    ]
    draft_df = draft_unique[draft_cols].copy()

    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(DRAFT_XLSX, engine="openpyxl") as writer:
        draft_df.to_excel(writer, sheet_name="stage4c_mapping_rule_draft", index=False)

    high_confidence_rule_count = int((draft_df["confidence_level"] == CONF_HIGH).sum()) if not draft_df.empty else 0
    medium_confidence_rule_count = int((draft_df["confidence_level"] == CONF_MEDIUM).sum()) if not draft_df.empty else 0

    snapshot_after = _snapshot_hashes()
    production_files_unchanged = (
        snapshot_before["01"] == snapshot_after["01"]
        and snapshot_before["02"] == snapshot_after["02"]
        and snapshot_before["02A"] == snapshot_after["02A"]
        and snapshot_before["05"] == snapshot_after["05"]
        and snapshot_before["06"] == snapshot_after["06"]
    )
    output_06_unchanged = snapshot_before["06"] == snapshot_after["06"]
    official_02B_unchanged = snapshot_before["02B"] == snapshot_after["02B"]
    formal_mapping_rules_unchanged = snapshot_before["formal_mapping_rules"] == snapshot_after["formal_mapping_rules"]
    delivery_status_after = _run_delivery_check().get("overall_status", "UNKNOWN")

    summary = {
        "input_ready_mapping_gap_count": int(input_ready_mapping_gap_count),
        "draft_mapping_rule_count": int(len(draft_df)),
        "already_existing_rule_count": int(already_existing_rule_count),
        "conflict_rule_count": int(conflict_rule_count),
        "possible_overlap_count": int(possible_overlap_count),
        "duplicate_draft_rule_count": int(duplicate_draft_rule_count),
        "missing_required_field_count": int(missing_required_field_count),
        "high_confidence_rule_count": int(high_confidence_rule_count),
        "medium_confidence_rule_count": int(medium_confidence_rule_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "output_06_unchanged": bool(output_06_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage4c_mapping_rule_draft_ready": bool(
            input_ready_mapping_gap_count == 28
            and production_files_unchanged
            and output_06_unchanged
            and official_02B_unchanged
            and formal_mapping_rules_unchanged
            and delivery_status_after == "PASS"
            and missing_required_field_count == 0
        ),
        "delivery_status_after": delivery_status_after,
    }

    out_xlsx = REPORT_DIR / "109_stage4c_mapping_rule_draft_report.xlsx"
    out_md = REPORT_DIR / "109_stage4c_mapping_rule_draft_report.md"
    out_json = REPORT_DIR / "110_stage4c_mapping_rule_draft_summary.json"

    rec_export_cols = [
        "issue_id",
        "asset_package",
        "raw_metric_name",
        "normalized_raw_metric_name",
        "proposed_standard_metric",
        "statement_type",
        "year",
        "source_layer",
        "target_layer",
        "current_value",
        "current_unit",
        "mapping_gap_category",
        "priority",
        "rule_scope",
        "confidence_level",
        "evidence_source",
        "stage4b_action_reason",
        "draft_status",
        "already_existing",
        "conflict",
        "possible_overlap",
        "missing_required_field",
    ]
    rec_export_df = rec_df[rec_export_cols].copy().sort_values(
        by=["already_existing", "conflict", "possible_overlap", "asset_package", "raw_metric_name", "year"],
        ascending=[False, False, False, True, True, True],
        kind="mergesort",
    )

    _safe_write_excel_multi(
        {
            "stage4c_input_ready_records": rec_export_df,
            "stage4c_draft_rules": draft_df,
            "possible_overlap": pd.DataFrame(possible_overlap_rows),
            "summary": pd.DataFrame([summary]),
        },
        out_xlsx,
    )

    md_lines = [
        "# Stage4C Mapping Rule Draft Report",
        "",
        "## Summary",
        f"- input_ready_mapping_gap_count: {summary['input_ready_mapping_gap_count']}",
        f"- draft_mapping_rule_count: {summary['draft_mapping_rule_count']}",
        f"- already_existing_rule_count: {summary['already_existing_rule_count']}",
        f"- conflict_rule_count: {summary['conflict_rule_count']}",
        f"- possible_overlap_count: {summary['possible_overlap_count']}",
        f"- duplicate_draft_rule_count: {summary['duplicate_draft_rule_count']}",
        f"- missing_required_field_count: {summary['missing_required_field_count']}",
        f"- high_confidence_rule_count: {summary['high_confidence_rule_count']}",
        f"- medium_confidence_rule_count: {summary['medium_confidence_rule_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- output_06_unchanged: {summary['output_06_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- delivery_status_after: {summary['delivery_status_after']}",
        f"- stage4c_mapping_rule_draft_ready: {summary['stage4c_mapping_rule_draft_ready']}",
    ]
    _safe_write_text("\n".join(md_lines), out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage4c_draft_xlsx: {DRAFT_XLSX}")
    print(f"stage4c_report_xlsx: {out_xlsx}")
    print(f"stage4c_report_md: {out_md}")
    print(f"stage4c_summary_json: {out_json}")
    for k in [
        "input_ready_mapping_gap_count",
        "draft_mapping_rule_count",
        "already_existing_rule_count",
        "conflict_rule_count",
        "possible_overlap_count",
        "duplicate_draft_rule_count",
        "missing_required_field_count",
        "high_confidence_rule_count",
        "medium_confidence_rule_count",
        "production_files_unchanged",
        "output_06_unchanged",
        "official_02B_unchanged",
        "formal_mapping_rules_unchanged",
        "stage4c_mapping_rule_draft_ready",
    ]:
        print(f"{k}: {summary[k]}")
    print(f"delivery_status_after: {summary['delivery_status_after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

