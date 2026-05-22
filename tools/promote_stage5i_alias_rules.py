import argparse
import hashlib
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE5H_DIR = OUTPUT_DIR / "stage5h_alias_draft_validation"
STAGE5F_DIR = OUTPUT_DIR / "stage5f_raw_metric_extraction_fix"

INPUT_DRAFT_XLSX = STAGE5H_DIR / "140_stage5h_alias_draft.xlsx"
INPUT_DRYRUN_XLSX = STAGE5H_DIR / "140_stage5h_alias_dry_run_result.xlsx"
INPUT_REPORT_XLSX = STAGE5H_DIR / "140_stage5h_alias_draft_validation_report.xlsx"
INPUT_SUMMARY_JSON = STAGE5H_DIR / "141_stage5h_alias_draft_validation_summary.json"
INPUT_IMPROVED_02_XLSX = STAGE5F_DIR / "136_stage5f_improved_structured_02.xlsx"
INPUT_IMPROVED_PREVIEW_XLSX = STAGE5F_DIR / "136_stage5f_improved_standardization_preview.xlsx"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_RULE_SOURCE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_NORMALIZATION_RULE_FILE = FORMAL_RULE_SOURCE_FILE
FORMAL_ALIAS_RULE_FILE = FORMAL_RULE_SOURCE_FILE
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5i_alias_promotion"
OUT_LOG_XLSX = OUT_DIR / "142_stage5i_alias_promotion_log.xlsx"
OUT_VERIFY_XLSX = OUT_DIR / "142_stage5i_alias_promotion_verification.xlsx"
OUT_REPORT_MD = OUT_DIR / "142_stage5i_alias_promotion_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "143_stage5i_alias_promotion_summary.json"

PROMOTED = "PROMOTED_TO_FORMAL_ALIAS"
SKIPPED_EXISTS = "SKIPPED_ALREADY_EXISTS"
BLOCKED_DUP = "BLOCKED_DUPLICATE_ALIAS_KEY"
BLOCKED_CONFLICT = "BLOCKED_CONFLICT_WITH_EXISTING_ALIAS"
BLOCKED_PRECHECK = "BLOCKED_PRECHECK_FAILED"

ISSUE_NONE = "NONE"
ISSUE_DUP = "DUPLICATE_ALIAS_KEY"
ISSUE_CONFLICT = "CONFLICT_WITH_EXISTING_ALIAS"
ISSUE_UNKNOWN_PRECHECK = "UNKNOWN_COUNT_PRECHECK_FAILED"
ISSUE_SCHEMA = "SCHEMA_MISMATCH"
ISSUE_UNKNOWN = "UNKNOWN"

CHG_FORMAL_OK = "FORMAL_ALIAS_MATCHED_STANDARDIZED_OK"
CHG_UNCHANGED_OK = "UNCHANGED_ALREADY_STANDARDIZED"
CHG_UNCHANGED_DERIVED = "UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED"
CHG_UNCHANGED_NON_CORE = "UNCHANGED_NON_CORE_METRIC"
CHG_UNCHANGED_MISS = "UNCHANGED_MAPPING_MISS"
CHG_UNCHANGED_OTHER = "UNCHANGED_OTHER"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    t = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    return re.sub(r"\s+", "", t).upper()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else files[0]


def _find_assignment_dict_block(text: str, var_name: str) -> Tuple[int, int]:
    m = re.search(rf"^\s*{re.escape(var_name)}(?:\s*:[^=]+)?\s*=\s*{{", text, re.M)
    if not m:
        raise RuntimeError(f"Cannot find dict block assignment: {var_name}")
    start = m.end() - 1
    depth = 0
    in_str = False
    quote = ""
    i = start
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                in_str = False
            i += 1
            continue
        if ch in ("'", '"'):
            in_str = True
            quote = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return (m.start(), i + 1)
        i += 1
    raise RuntimeError(f"Cannot close dict block for: {var_name}")


def _extract_alias_block_text(file_path: Path) -> str:
    text = file_path.read_text(encoding="utf-8")
    s, e = _find_assignment_dict_block(text, "STANDARD_METRIC_ALIASES")
    return text[s:e]


def _extract_normalization_surrogate_text(file_path: Path) -> str:
    # Surrogate for normalization rules: remove alias dictionary block from source.
    # This keeps all normalization logic but excludes alias-only promotions.
    text = file_path.read_text(encoding="utf-8")
    s, e = _find_assignment_dict_block(text, "STANDARD_METRIC_ALIASES")
    return text[:s] + "STANDARD_METRIC_ALIASES = <OMITTED_ALIAS_BLOCK>" + text[e:]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "formal_mapping_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
        "formal_normalization_rules": _sha256_text(_extract_normalization_surrogate_text(FORMAL_NORMALIZATION_RULE_FILE)),
        "formal_alias_rules": _sha256_text(_extract_alias_block_text(FORMAL_ALIAS_RULE_FILE)),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _load_df_first_sheet(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    return pd.read_excel(path, sheet_name=xl.sheet_names[0]).fillna("")


def _build_alias_index() -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    by_alias: Dict[str, str] = {}
    by_metric: Dict[str, Set[str]] = {}
    for std, aliases in fs.STANDARD_METRIC_ALIASES.items():
        metric = _norm(std)
        by_metric.setdefault(metric, set())
        for a in aliases:
            ak = _compact(a)
            if ak:
                by_alias[ak] = metric
                by_metric[metric].add(_norm(a))
    return by_alias, by_metric


def _append_alias_to_file(file_path: Path, standard_metric: str, alias_text: str) -> bool:
    text = file_path.read_text(encoding="utf-8")
    if _compact(alias_text) in {_compact(x) for x in fs.STANDARD_METRIC_ALIASES.get(standard_metric, [])}:
        return False

    block_re = re.compile(rf'("{re.escape(standard_metric)}"\s*:\s*\[)(.*?)(\n\s*\],)', re.S)
    m = block_re.search(text)
    if not m:
        raise RuntimeError(f"Cannot find alias list block for standard metric: {standard_metric}")

    prefix, body, suffix = m.group(1), m.group(2), m.group(3)
    indent = " " * 8
    add_line = f'\n{indent}"{alias_text}",'

    if f'"{alias_text}"' in body:
        return False

    new_body = body + add_line
    new_block = prefix + new_body + suffix
    new_text = text[: m.start()] + new_block + text[m.end() :]
    file_path.write_text(new_text, encoding="utf-8")
    return True


def _is_valid_year(y: str) -> bool:
    return bool(re.fullmatch(r"20\d{2}(?:[AE])?", _norm(y).upper()))


def _is_valid_value(v: str) -> bool:
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", _norm(v).replace(",", "")))


def _is_valid_unit(u: str) -> bool:
    return _norm(u) != ""


def _classify_mapping_miss(raw: str) -> str:
    t = _norm(raw)
    if any(x in t for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return CHG_UNCHANGED_DERIVED
    if any(x in t for x in ["营业利润", "净利润", "EBITDA"]):
        return CHG_UNCHANGED_NON_CORE
    return CHG_UNCHANGED_MISS


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5I promote validated alias rules.")
    parser.parse_args()

    required = [
        INPUT_DRAFT_XLSX,
        INPUT_DRYRUN_XLSX,
        INPUT_REPORT_XLSX,
        INPUT_SUMMARY_JSON,
        INPUT_IMPROVED_02_XLSX,
        INPUT_IMPROVED_PREVIEW_XLSX,
        FORMAL_SCOPE_RULES_JSON,
        OFFICIAL_02B_PATH,
        FORMAL_ALIAS_RULE_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    draft_df = _load_df_first_sheet(INPUT_DRAFT_XLSX)
    dryrun_df = _load_df_first_sheet(INPUT_DRYRUN_XLSX)
    preview_df = _load_df_first_sheet(INPUT_IMPROVED_PREVIEW_XLSX)
    s5h = json.loads(INPUT_SUMMARY_JSON.read_text(encoding="utf-8"))

    ready_df = draft_df[draft_df["draft_status"].map(_norm) == "DRAFT_ALIAS_READY"].copy()
    input_draft_alias_rule_count = int(len(draft_df))
    input_draft_alias_ready_count = int(len(ready_df))

    unknown_rows = dryrun_df[dryrun_df["change_type"].map(_norm) == CHG_UNCHANGED_OTHER].copy()
    unknown_count_precheck_pass = True
    unknown_count_precheck_reason = "unknown rows are duplicate-candidate residuals already standardized"
    if len(unknown_rows) != int(s5h.get("remaining_unknown_count", 0)):
        unknown_count_precheck_pass = False
        unknown_count_precheck_reason = "unknown count mismatch with stage5h summary"
    else:
        for _, r in unknown_rows.iterrows():
            if _norm(r.get("standardization_status_before")) != "DUPLICATE_CANDIDATE":
                unknown_count_precheck_pass = False
                unknown_count_precheck_reason = "unknown rows include non-duplicate-candidate records"
                break

    by_alias, _ = _build_alias_index()
    duplicate_key_in_draft = False
    draft_key_seen: Dict[str, str] = {}
    for _, r in ready_df.iterrows():
        key = _compact(_norm(r.get("raw_metric_name_cleaned")) or _norm(r.get("raw_metric_name")))
        target = _norm(r.get("target_standard_metric"))
        if not key or not target:
            continue
        prev_target = draft_key_seen.get(key)
        if prev_target and prev_target != target:
            duplicate_key_in_draft = True
            break
        draft_key_seen[key] = target

    precheck_pass = bool(
        int(s5h.get("draft_alias_ready_count", 0)) == 5
        and int(s5h.get("ready_for_stage5i_alias_promotion_count", 0)) == 5
        and input_draft_alias_ready_count == 5
        and unknown_count_precheck_pass
        and (not duplicate_key_in_draft)
    )

    promotion_rows: List[Dict[str, Any]] = []
    promoted_alias_rule_count = 0
    skipped_existing_alias_count = 0
    blocked_duplicate_alias_key_count = 0
    blocked_conflict_alias_count = 0

    promoted_keys_this_run: Set[Tuple[str, str]] = set()

    if precheck_pass:
        for _, r in ready_df.iterrows():
            alias_rule_id = _norm(r.get("alias_rule_id"))
            raw_metric_name = _norm(r.get("raw_metric_name"))
            raw_metric_name_cleaned = _norm(r.get("raw_metric_name_cleaned"))
            target_standard_metric = _norm(r.get("target_standard_metric"))
            alias_candidate = raw_metric_name_cleaned or raw_metric_name
            alias_key = _compact(alias_candidate)

            status = PROMOTED
            issue = ISSUE_NONE
            evidence = _norm(r.get("evidence"))

            if not alias_key or not target_standard_metric:
                status = BLOCKED_PRECHECK
                issue = ISSUE_SCHEMA
            else:
                existing_metric = by_alias.get(alias_key, "")
                if existing_metric and existing_metric != target_standard_metric:
                    status = BLOCKED_CONFLICT
                    issue = ISSUE_CONFLICT
                    blocked_conflict_alias_count += 1
                elif (alias_key, target_standard_metric) in promoted_keys_this_run:
                    status = SKIPPED_EXISTS
                    issue = ISSUE_NONE
                    skipped_existing_alias_count += 1
                elif existing_metric == target_standard_metric:
                    status = SKIPPED_EXISTS
                    issue = ISSUE_NONE
                    skipped_existing_alias_count += 1
                else:
                    changed = _append_alias_to_file(FORMAL_ALIAS_RULE_FILE, target_standard_metric, alias_candidate)
                    importlib.reload(fs)
                    by_alias, _ = _build_alias_index()
                    if changed:
                        status = PROMOTED
                        issue = ISSUE_NONE
                        promoted_alias_rule_count += 1
                        promoted_keys_this_run.add((alias_key, target_standard_metric))
                    else:
                        status = SKIPPED_EXISTS
                        issue = ISSUE_NONE
                        skipped_existing_alias_count += 1

            promotion_rows.append(
                {
                    "alias_rule_id": alias_rule_id,
                    "raw_metric_name": raw_metric_name,
                    "raw_metric_name_cleaned": raw_metric_name_cleaned,
                    "target_standard_metric": target_standard_metric,
                    "target_existing_mapping_rule_id": _norm(r.get("target_existing_mapping_rule_id")),
                    "statement_type": _norm(r.get("statement_type")),
                    "asset_package": _norm(r.get("asset_package")),
                    "unit": _norm(r.get("unit")),
                    "source_pdf": _norm(r.get("source_pdf")),
                    "source_page": _norm(r.get("source_page")),
                    "source_table_id": _norm(r.get("source_table_id")),
                    "row_trace_id": _norm(r.get("row_trace_id")),
                    "promotion_status": status,
                    "promotion_issue_type": issue,
                    "evidence": evidence,
                }
            )
    else:
        for _, r in ready_df.iterrows():
            promotion_rows.append(
                {
                    "alias_rule_id": _norm(r.get("alias_rule_id")),
                    "raw_metric_name": _norm(r.get("raw_metric_name")),
                    "raw_metric_name_cleaned": _norm(r.get("raw_metric_name_cleaned")),
                    "target_standard_metric": _norm(r.get("target_standard_metric")),
                    "target_existing_mapping_rule_id": _norm(r.get("target_existing_mapping_rule_id")),
                    "statement_type": _norm(r.get("statement_type")),
                    "asset_package": _norm(r.get("asset_package")),
                    "unit": _norm(r.get("unit")),
                    "source_pdf": _norm(r.get("source_pdf")),
                    "source_page": _norm(r.get("source_page")),
                    "source_table_id": _norm(r.get("source_table_id")),
                    "row_trace_id": _norm(r.get("row_trace_id")),
                    "promotion_status": BLOCKED_PRECHECK,
                    "promotion_issue_type": ISSUE_UNKNOWN_PRECHECK if not unknown_count_precheck_pass else ISSUE_DUP,
                    "evidence": "precheck failed",
                }
            )
        blocked_duplicate_alias_key_count = 1 if duplicate_key_in_draft else 0

    verify_rows: List[Dict[str, Any]] = []
    promoted_alias_map: Dict[str, str] = {}
    for pr in promotion_rows:
        if _norm(pr.get("promotion_status")) == PROMOTED:
            key = _compact(_norm(pr.get("raw_metric_name_cleaned")) or _norm(pr.get("raw_metric_name")))
            promoted_alias_map[key] = _norm(pr.get("alias_rule_id"))

    for _, r in preview_df.iterrows():
        row_trace_id = _norm(r.get("row_trace_id"))
        raw_metric_name = _norm(r.get("raw_metric_name"))
        source_reference = _norm(r.get("source_reference"))
        status_before = _norm(r.get("standardization_status"))
        raw_clean = fs._clean_metric_label_noise(raw_metric_name)
        k = _compact(raw_clean or raw_metric_name)

        m = fs._match_standard_metric(raw_metric_name)
        standard_metric_after = _norm(m.get("standard_metric")) if m else ""
        if status_before == "STANDARDIZED_OK":
            status_after = "STANDARDIZED_OK"
            change_type = CHG_UNCHANGED_OK
            issue_type_after = "NONE"
            matched_formal_alias_rule_id = ""
        elif status_before == "DUPLICATE_CANDIDATE":
            status_after = "DUPLICATE_CANDIDATE"
            change_type = CHG_UNCHANGED_OTHER
            issue_type_after = "DUPLICATE_KEY"
            matched_formal_alias_rule_id = ""
        elif status_before == "MAPPING_MISS":
            if m and _is_valid_year(_norm(r.get("year"))) and _is_valid_value(_norm(r.get("value"))) and _is_valid_unit(_norm(r.get("unit"))):
                status_after = "STANDARDIZED_OK"
                change_type = CHG_FORMAL_OK
                issue_type_after = "NONE"
                matched_formal_alias_rule_id = promoted_alias_map.get(k, "")
            else:
                status_after = "MAPPING_MISS"
                change_type = _classify_mapping_miss(raw_metric_name)
                issue_type_after = "METRIC_MAPPING_ISSUE"
                matched_formal_alias_rule_id = ""
        else:
            status_after = status_before
            change_type = CHG_UNCHANGED_OTHER
            issue_type_after = _norm(r.get("standardization_issue_type")) or ISSUE_UNKNOWN
            matched_formal_alias_rule_id = ""

        verify_rows.append(
            {
                "row_trace_id": row_trace_id,
                "raw_metric_name": raw_metric_name,
                "standard_metric_after_formal_alias": standard_metric_after,
                "standardization_status_after_formal_alias": status_after,
                "matched_formal_alias_rule_id": matched_formal_alias_rule_id,
                "change_type": change_type,
                "issue_type_after": issue_type_after,
                "source_reference": source_reference,
            }
        )

    promo_df = pd.DataFrame(promotion_rows)
    verify_df = pd.DataFrame(verify_rows)

    formal_alias_standardized_ok_count = int((verify_df["standardization_status_after_formal_alias"].map(_norm) == "STANDARDIZED_OK").sum()) if not verify_df.empty else 0
    formal_alias_mapping_miss_count = int((verify_df["standardization_status_after_formal_alias"].map(_norm) == "MAPPING_MISS").sum()) if not verify_df.empty else 0

    previous_stage5h_after_alias_standardized_ok_count = int(s5h.get("after_alias_standardized_ok_count", 0))
    previous_stage5h_after_alias_mapping_miss_count = int(s5h.get("after_alias_mapping_miss_count", 0))

    standardized_ok_matches_stage5h = bool(formal_alias_standardized_ok_count == previous_stage5h_after_alias_standardized_ok_count)
    mapping_miss_matches_stage5h = bool(formal_alias_mapping_miss_count == previous_stage5h_after_alias_mapping_miss_count)

    remaining_derived_metric_not_supported_count = int((verify_df["change_type"].map(_norm) == CHG_UNCHANGED_DERIVED).sum()) if not verify_df.empty else 0
    remaining_non_core_metric_count = int((verify_df["change_type"].map(_norm) == CHG_UNCHANGED_NON_CORE).sum()) if not verify_df.empty else 0
    remaining_unknown_count_after_precheck = int((verify_df["change_type"].map(_norm) == CHG_UNCHANGED_OTHER).sum()) if not verify_df.empty else 0
    remaining_true_mapping_gap_count = int(
        (
            (verify_df["standardization_status_after_formal_alias"].map(_norm) == "MAPPING_MISS")
            & (~verify_df["change_type"].map(_norm).isin([CHG_UNCHANGED_DERIVED, CHG_UNCHANGED_NON_CORE]))
        ).sum()
    ) if not verify_df.empty else 0

    after = _snapshot_hashes()
    production_files_unchanged = bool(
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02B_unchanged = bool(before["02B"] == after["02B"])
    formal_scope_rules_unchanged = bool(before["formal_scope_rules"] == after["formal_scope_rules"])
    formal_mapping_rules_unchanged = bool(before["formal_mapping_rules"] == after["formal_mapping_rules"])
    formal_normalization_rules_unchanged = bool(before["formal_normalization_rules"] == after["formal_normalization_rules"])
    formal_alias_rules_changed = bool(before["formal_alias_rules"] != after["formal_alias_rules"])

    summary = {
        "input_draft_alias_rule_count": int(input_draft_alias_rule_count),
        "input_draft_alias_ready_count": int(input_draft_alias_ready_count),
        "precheck_pass": bool(precheck_pass),
        "unknown_count_precheck_pass": bool(unknown_count_precheck_pass),
        "unknown_count_precheck_reason": _norm(unknown_count_precheck_reason),
        "promoted_alias_rule_count": int(promoted_alias_rule_count),
        "skipped_existing_alias_count": int(skipped_existing_alias_count),
        "blocked_duplicate_alias_key_count": int(blocked_duplicate_alias_key_count),
        "blocked_conflict_alias_count": int(blocked_conflict_alias_count),
        "formal_alias_rules_changed": bool(formal_alias_rules_changed),
        "previous_stage5h_after_alias_standardized_ok_count": int(previous_stage5h_after_alias_standardized_ok_count),
        "formal_alias_standardized_ok_count": int(formal_alias_standardized_ok_count),
        "standardized_ok_matches_stage5h": bool(standardized_ok_matches_stage5h),
        "previous_stage5h_after_alias_mapping_miss_count": int(previous_stage5h_after_alias_mapping_miss_count),
        "formal_alias_mapping_miss_count": int(formal_alias_mapping_miss_count),
        "mapping_miss_matches_stage5h": bool(mapping_miss_matches_stage5h),
        "remaining_derived_metric_not_supported_count": int(remaining_derived_metric_not_supported_count),
        "remaining_non_core_metric_count": int(remaining_non_core_metric_count),
        "remaining_true_mapping_gap_count": int(remaining_true_mapping_gap_count),
        "remaining_unknown_count_after_precheck": int(remaining_unknown_count_after_precheck),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5i_alias_promotion_pass": False,
    }

    promoted_or_skipped_ok = (
        summary["promoted_alias_rule_count"] == 5
        or summary["promoted_alias_rule_count"] + summary["skipped_existing_alias_count"] == 5
    )
    alias_changed_or_all_skipped = summary["formal_alias_rules_changed"] or (
        summary["promoted_alias_rule_count"] == 0 and summary["skipped_existing_alias_count"] == 5
    )

    summary["stage5i_alias_promotion_pass"] = bool(
        summary["input_draft_alias_ready_count"] == 5
        and summary["precheck_pass"]
        and summary["unknown_count_precheck_pass"]
        and promoted_or_skipped_ok
        and alias_changed_or_all_skipped
        and summary["formal_alias_standardized_ok_count"] >= 45
        and summary["formal_alias_mapping_miss_count"] <= 80
        and summary["remaining_true_mapping_gap_count"] == 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["formal_mapping_rules_unchanged"]
        and summary["formal_normalization_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    promo_status_df = (
        promo_df.groupby(["promotion_status", "promotion_issue_type"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "promotion_status"], ascending=[False, True], kind="mergesort")
        if not promo_df.empty else pd.DataFrame(columns=["promotion_status", "promotion_issue_type", "count"])
    )
    verify_status_df = (
        verify_df.groupby(["change_type", "standardization_status_after_formal_alias"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "change_type"], ascending=[False, True], kind="mergesort")
        if not verify_df.empty else pd.DataFrame(columns=["change_type", "standardization_status_after_formal_alias", "count"])
    )

    _write_excel(OUT_LOG_XLSX, {"alias_promotion_log": promo_df, "promotion_distribution": promo_status_df, "summary": pd.DataFrame([summary])})
    _write_excel(OUT_VERIFY_XLSX, {"alias_promotion_verification": verify_df, "verification_distribution": verify_status_df})

    md_lines = [
        "# Stage5I Alias Promotion Report",
        "",
        f"- input_draft_alias_rule_count: {summary['input_draft_alias_rule_count']}",
        f"- input_draft_alias_ready_count: {summary['input_draft_alias_ready_count']}",
        f"- precheck_pass: {summary['precheck_pass']}",
        f"- unknown_count_precheck_pass: {summary['unknown_count_precheck_pass']}",
        f"- unknown_count_precheck_reason: {summary['unknown_count_precheck_reason']}",
        f"- promoted_alias_rule_count: {summary['promoted_alias_rule_count']}",
        f"- skipped_existing_alias_count: {summary['skipped_existing_alias_count']}",
        f"- blocked_duplicate_alias_key_count: {summary['blocked_duplicate_alias_key_count']}",
        f"- blocked_conflict_alias_count: {summary['blocked_conflict_alias_count']}",
        f"- formal_alias_rules_changed: {summary['formal_alias_rules_changed']}",
        f"- previous_stage5h_after_alias_standardized_ok_count: {summary['previous_stage5h_after_alias_standardized_ok_count']}",
        f"- formal_alias_standardized_ok_count: {summary['formal_alias_standardized_ok_count']}",
        f"- standardized_ok_matches_stage5h: {summary['standardized_ok_matches_stage5h']}",
        f"- previous_stage5h_after_alias_mapping_miss_count: {summary['previous_stage5h_after_alias_mapping_miss_count']}",
        f"- formal_alias_mapping_miss_count: {summary['formal_alias_mapping_miss_count']}",
        f"- mapping_miss_matches_stage5h: {summary['mapping_miss_matches_stage5h']}",
        f"- remaining_derived_metric_not_supported_count: {summary['remaining_derived_metric_not_supported_count']}",
        f"- remaining_non_core_metric_count: {summary['remaining_non_core_metric_count']}",
        f"- remaining_true_mapping_gap_count: {summary['remaining_true_mapping_gap_count']}",
        f"- remaining_unknown_count_after_precheck: {summary['remaining_unknown_count_after_precheck']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- stage5i_alias_promotion_pass: {summary['stage5i_alias_promotion_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5i_promotion_log_xlsx: {OUT_LOG_XLSX}")
    print(f"stage5i_verification_xlsx: {OUT_VERIFY_XLSX}")
    print(f"stage5i_report_md: {OUT_REPORT_MD}")
    print(f"stage5i_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5i_alias_promotion_pass: {summary['stage5i_alias_promotion_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
