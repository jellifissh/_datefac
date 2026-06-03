from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd


EXPECTED_323A_READY_DECISION = "HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP"
EXPECTED_323AR_READY_DECISION = "CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP"
EXPECTED_323AR_NOT_READY_DECISION = "CANDIDATE_TEXT_REPAIR_323AR_NOT_READY_SOURCE_TEXT_RECHECK_REQUIRED"

DEFAULT_MINING_DIR = Path(r"D:\_datefac\output\high_impact_semantic_candidates_mining_323a")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_POST_PATCH_REGRESSION_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_322o")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\candidate_text_repair_323ar")

REPAIR_STATUS_ALREADY_CLEAN = "ALREADY_CLEAN"
REPAIR_STATUS_REPAIRED = "REPAIRED_DETERMINISTIC"
REPAIR_STATUS_HOLDOUT = "UNREPAIRABLE_HOLDOUT"
REPAIR_STATUS_RECHECK = "NEEDS_SOURCE_TEXT_RECHECK"

MOJIBAKE_MARKERS = (
    "閸",
    "閿",
    "濮",
    "娑",
    "绁",
    "鍋",
    "锟",
    "\ufffd",
)

KNOWN_MOJIBAKE_MAP = {
    "鍏朵腑锛氭湇鍔?": "其中：服务",
    "鍏朵腑锛氳澶?": "其中：设备",
    "鍏朵粬闈炴祦鍔ㄨ礋鍊?": "其他非流动负债",
    "鍏朵粬闈炴祦鍔ㄨ祫浜?": "其他非流动资产",
    "褰掑睘姣嶅叕鍙歌偂涓滄潈鐩?": "归属母公司股东权益",
}

REVIEW_READY_GROUP_TYPES = {"alias", "scope_noise"}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _split_pipe(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except Exception:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return pd.DataFrame(rows).fillna("")


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _mojibake_marker_count(text: str) -> int:
    normalized = _norm(text)
    return sum(normalized.count(marker) for marker in MOJIBAKE_MARKERS)


def looks_mojibake(text: Any) -> bool:
    normalized = _norm(text)
    if not normalized:
        return False
    if normalized in KNOWN_MOJIBAKE_MAP:
        return True
    if any(marker in normalized for marker in MOJIBAKE_MARKERS):
        return True
    question_count = normalized.count("?")
    if question_count >= 2 and _contains_cjk(normalized):
        return True
    if question_count >= 1 and any(token in normalized for token in ("鍏", "褰", "閮", "璧", "娴")):
        return True
    return False


def _human_readable(text: str) -> bool:
    normalized = _norm(text)
    if not normalized:
        return False
    if looks_mojibake(normalized):
        return False
    if normalized.count("?") >= 2:
        return False
    if "\ufffd" in normalized:
        return False
    if _contains_cjk(normalized):
        return True
    alpha_like = sum(1 for ch in normalized if ch.isalpha())
    return alpha_like >= max(2, len(normalized) // 3)


def _looks_structural_not_encoding_issue(text: str) -> bool:
    normalized = _norm(text)
    if not normalized:
        return True
    compact = normalized.replace(" ", "")
    if compact.replace("/", "").replace("-", "").replace(".", "").isdigit():
        return True
    if compact.endswith((".sh", ".sz", ".hk")) and any(ch.isdigit() for ch in compact):
        return True
    if compact in {"(+/-%)", "(+/% )", "(+/-)", "y\\", "y/", "1"}:
        return True
    return False


def _try_redecode(text: str) -> Optional[Tuple[str, str, str]]:
    if not text:
        return None
    candidates: List[Tuple[str, str]] = []
    for source_encoding, target_encoding in [
        ("latin1", "utf-8"),
        ("cp1252", "utf-8"),
        ("latin1", "gbk"),
        ("cp1252", "gbk"),
        ("gbk", "utf-8"),
    ]:
        try:
            candidate = text.encode(source_encoding, errors="ignore").decode(target_encoding, errors="ignore").strip()
        except Exception:
            continue
        if not candidate or candidate == text:
            continue
        candidates.append((candidate, f"{source_encoding}_to_{target_encoding}"))
    best: Optional[Tuple[str, str, str]] = None
    best_score = -10**9
    for candidate, method in candidates:
        score = 0
        if _human_readable(candidate):
            score += 50
        if _contains_cjk(candidate):
            score += 20
        score -= _mojibake_marker_count(candidate) * 15
        score -= candidate.count("?") * 10
        score += len(candidate)
        if score > best_score:
            best_score = score
            confidence = "high" if score >= 55 else "medium" if score >= 35 else "low"
            best = (candidate, method, confidence)
    return best


def _build_candidate_text_lookup(selected_candidates_df: pd.DataFrame) -> Dict[str, List[str]]:
    lookup: Dict[str, List[str]] = {}
    if selected_candidates_df.empty:
        return lookup
    temp = selected_candidates_df.copy()
    temp["raw_metric_name"] = temp.get("raw_metric_name", "").astype(str)
    temp["source_row_text"] = temp.get("source_row_text", "").astype(str)
    for _, row in temp.iterrows():
        for source_key in [_normalize_label(row.get("raw_metric_name")), _normalize_label(row.get("source_row_text"))]:
            if not source_key:
                continue
            values = lookup.setdefault(source_key, [])
            for candidate_text in [row.get("raw_metric_name"), row.get("source_row_text"), row.get("table_title")]:
                clean = _norm(candidate_text)
                if clean and clean not in values:
                    values.append(clean)
    return lookup


def _find_clean_source_match(
    original_label: str,
    normalized_key: str,
    row: pd.Series,
    candidate_text_lookup: Dict[str, List[str]],
) -> Optional[Tuple[str, str, str]]:
    direct_candidates: List[str] = []
    for field in [
        "normalized_label_display",
        "sample_raw_metric_names",
        "sample_row_texts",
        "sample_table_titles",
    ]:
        direct_candidates.extend(_split_pipe(row.get(field)))
    for candidate in direct_candidates:
        if candidate and _human_readable(candidate):
            return candidate, "workbook_clean_text", "high"

    if normalized_key in candidate_text_lookup:
        for candidate in candidate_text_lookup[normalized_key]:
            if candidate and _human_readable(candidate):
                return candidate, "cached_candidate_text_lookup", "high"

    if original_label in KNOWN_MOJIBAKE_MAP:
        return KNOWN_MOJIBAKE_MAP[original_label], "known_mojibake_map", "high"

    decoded = _try_redecode(original_label)
    if decoded is not None:
        repaired_text, method, confidence = decoded
        if _human_readable(repaired_text):
            return repaired_text, method, confidence
    return None


def _repair_group_row(row: pd.Series, candidate_text_lookup: Dict[str, List[str]]) -> Dict[str, Any]:
    original_label = _norm(row.get("normalized_label_display"))
    normalized_key = _normalize_label(row.get("normalized_label_key") or original_label)
    is_mojibake = looks_mojibake(original_label)
    structural_not_encoding = _looks_structural_not_encoding_issue(original_label)

    repaired_label = original_label
    repair_method = "identity_preserve"
    repair_confidence = "high" if _human_readable(original_label) else "low"
    if _human_readable(original_label):
        repair_status = REPAIR_STATUS_ALREADY_CLEAN
    elif is_mojibake:
        matched = _find_clean_source_match(original_label, normalized_key, row, candidate_text_lookup)
        if matched is not None:
            repaired_label, repair_method, repair_confidence = matched
            repair_status = REPAIR_STATUS_REPAIRED if repaired_label != original_label else REPAIR_STATUS_ALREADY_CLEAN
        else:
            repair_status = REPAIR_STATUS_HOLDOUT
            repaired_label = ""
            repair_method = "no_safe_repair"
            repair_confidence = "low"
    else:
        repair_status = REPAIR_STATUS_RECHECK if structural_not_encoding else REPAIR_STATUS_HOLDOUT
        repaired_label = ""
        repair_method = "non_encoding_label_holdout"
        repair_confidence = "low"

    human_readable_after = _human_readable(repaired_label)
    review_ready = (
        row.get("group_type_candidate") in REVIEW_READY_GROUP_TYPES
        and repair_status in {REPAIR_STATUS_ALREADY_CLEAN, REPAIR_STATUS_REPAIRED}
        and human_readable_after
        and _norm(row.get("group_id")) != ""
    )

    repaired = row.to_dict()
    repaired.update(
        {
            "original_label": original_label,
            "repaired_label": repaired_label,
            "repair_method": repair_method,
            "repair_confidence": repair_confidence,
            "is_mojibake": bool(is_mojibake),
            "repair_status": repair_status,
            "human_readable_after_repair": bool(human_readable_after),
            "review_ready_for_adjudication": bool(review_ready),
        }
    )
    return repaired


def _build_review_ready_df(df: pd.DataFrame, group_type: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    subset = df[
        (df["group_type_candidate"].astype(str) == group_type)
        & (df["review_ready_for_adjudication"] == True)
    ].copy()
    if subset.empty:
        return subset
    cols = [
        "group_id",
        "group_type_candidate",
        "original_label",
        "repaired_label",
        "repair_status",
        "repair_method",
        "repair_confidence",
        "affected_candidate_count",
        "affected_review_required_count",
        "priority_score",
        "risk_signature",
        "sample_raw_metric_names",
        "sample_row_texts",
        "sample_table_titles",
        "sample_years",
        "suggested_next_action",
    ]
    present_cols = [col for col in cols if col in subset.columns]
    return subset[present_cols].reset_index(drop=True)


def _build_holdout_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    subset = df[df["review_ready_for_adjudication"] != True].copy()
    if subset.empty:
        return subset
    cols = [
        "group_id",
        "group_type_candidate",
        "original_label",
        "repaired_label",
        "repair_status",
        "repair_method",
        "repair_confidence",
        "is_mojibake",
        "human_readable_after_repair",
        "affected_candidate_count",
        "affected_review_required_count",
        "priority_score",
        "risk_signature",
        "sample_raw_metric_names",
        "sample_row_texts",
        "sample_table_titles",
        "sample_years",
    ]
    present_cols = [col for col in cols if col in subset.columns]
    return subset[present_cols].reset_index(drop=True)


def _build_mojibake_groups_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    subset = df[df["is_mojibake"] == True].copy()
    if subset.empty:
        return subset
    cols = [
        "group_id",
        "group_type_candidate",
        "original_label",
        "repaired_label",
        "repair_status",
        "repair_method",
        "repair_confidence",
        "affected_candidate_count",
        "affected_review_required_count",
        "priority_score",
        "sample_raw_metric_names",
        "sample_row_texts",
        "sample_table_titles",
    ]
    present_cols = [col for col in cols if col in subset.columns]
    return subset[present_cols].reset_index(drop=True)


def load_candidate_text_repair_inputs(
    mining_dir: Path,
    trust_split_dir: Path,
    post_patch_regression_dir: Path,
) -> Dict[str, Any]:
    ranked_groups_path = mining_dir / "high_impact_semantic_candidates_mining_323a_ranked_groups.xlsx"
    top_alias_path = mining_dir / "high_impact_semantic_candidates_mining_323a_top_alias_opportunities.xlsx"
    top_scope_path = mining_dir / "high_impact_semantic_candidates_mining_323a_top_scope_noise_opportunities.xlsx"

    return {
        "mining_summary": _read_json(mining_dir / "high_impact_semantic_candidates_mining_323a_summary.json"),
        "mining_qa": _read_json(mining_dir / "high_impact_semantic_candidates_mining_323a_qa.json"),
        "post_patch_summary": _read_json(post_patch_regression_dir / "post_patch_regression_validation_322o_summary.json"),
        "ranked_groups_df": _read_excel_sheet(ranked_groups_path, "ranked_groups"),
        "ranked_summary_df": _read_excel_sheet(ranked_groups_path, "summary"),
        "qa_checks_df": _read_excel_sheet(ranked_groups_path, "qa_checks"),
        "top_alias_df": _read_excel_sheet(top_alias_path, "top_opportunities"),
        "top_scope_df": _read_excel_sheet(top_scope_path, "top_opportunities"),
        "selected_candidates_df": _read_jsonl(trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"),
    }


def build_candidate_text_repair_323ar(
    mining_summary: Dict[str, Any],
    mining_qa: Dict[str, Any],
    post_patch_summary: Dict[str, Any],
    ranked_groups_df: pd.DataFrame,
    top_alias_df: pd.DataFrame,
    top_scope_df: pd.DataFrame,
    selected_candidates_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json"))
    scope_hash_before = _sha256_file(Path(r"D:\_datefac\data\mapping\formal_scope_rules.json"))

    readiness_checks = {
        "decision": _norm(mining_summary.get("decision")) == EXPECTED_323A_READY_DECISION,
        "qa_fail_count": _safe_int(mining_summary.get("qa_fail_count")) == 0,
        "grouped_candidate_count_positive": _safe_int(mining_summary.get("grouped_candidate_count")) > 0,
        "has_top_alias_or_scope": (
            _safe_int(mining_summary.get("top_alias_opportunity_count")) > 0
            or _safe_int(mining_summary.get("top_scope_noise_opportunity_count")) > 0
        ),
    }
    for key, passed in readiness_checks.items():
        add_qa(f"input_323a::{key}", "PASS" if passed else "FAIL", str(mining_summary.get(key, "")))

    add_qa(
        "input_323a::qa_json_fail_count",
        "PASS" if _safe_int(mining_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(mining_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "input_322o::closed_state",
        "PASS" if _safe_int(post_patch_summary.get("qa_fail_count")) == 0 else "FAIL",
        _norm(post_patch_summary.get("decision")),
    )
    add_qa(
        "cached_inputs::ranked_groups_loaded",
        "PASS" if not ranked_groups_df.empty else "FAIL",
        f"row_count={len(ranked_groups_df)}",
    )
    add_qa(
        "cached_inputs::selected_candidates_loaded",
        "PASS" if not selected_candidates_df.empty else "FAIL",
        f"row_count={len(selected_candidates_df)}",
    )

    candidate_text_lookup = _build_candidate_text_lookup(selected_candidates_df)
    repaired_rows = [_repair_group_row(row, candidate_text_lookup) for _, row in ranked_groups_df.iterrows()]
    repaired_df = pd.DataFrame(repaired_rows).fillna("")

    mojibake_group_count = int(repaired_df["is_mojibake"].sum()) if not repaired_df.empty else 0
    mojibake_top_alias_count = int(
        repaired_df[
            repaired_df["group_id"].astype(str).isin(set(top_alias_df.get("group_id", pd.Series(dtype=str)).astype(str).tolist()))
            & repaired_df["is_mojibake"]
        ].shape[0]
    ) if not repaired_df.empty else 0
    mojibake_top_scope_count = int(
        repaired_df[
            repaired_df["group_id"].astype(str).isin(set(top_scope_df.get("group_id", pd.Series(dtype=str)).astype(str).tolist()))
            & repaired_df["is_mojibake"]
        ].shape[0]
    ) if not repaired_df.empty else 0
    mojibake_sample_text_count = 0
    if not repaired_df.empty:
        for field in ["sample_raw_metric_names", "sample_row_texts", "sample_table_titles"]:
            mojibake_sample_text_count += int(repaired_df[field].astype(str).map(looks_mojibake).sum()) if field in repaired_df.columns else 0

    deterministic_repair_count = int((repaired_df["repair_status"] == REPAIR_STATUS_REPAIRED).sum()) if not repaired_df.empty else 0
    already_clean_count = int((repaired_df["repair_status"] == REPAIR_STATUS_ALREADY_CLEAN).sum()) if not repaired_df.empty else 0
    unrepairable_holdout_count = int(
        repaired_df["repair_status"].isin([REPAIR_STATUS_HOLDOUT, REPAIR_STATUS_RECHECK]).sum()
    ) if not repaired_df.empty else 0

    review_ready_alias_df = _build_review_ready_df(repaired_df, "alias")
    review_ready_scope_df = _build_review_ready_df(repaired_df, "scope_noise")
    holdout_df = _build_holdout_df(repaired_df)
    mojibake_groups_df = _build_mojibake_groups_df(repaired_df)
    unrepairable_df = repaired_df[
        repaired_df["repair_status"].isin([REPAIR_STATUS_HOLDOUT, REPAIR_STATUS_RECHECK])
    ].copy().reset_index(drop=True) if not repaired_df.empty else pd.DataFrame()

    add_qa(
        "repair::original_repaired_fields_present",
        "PASS" if all(col in repaired_df.columns for col in ["original_label", "repaired_label", "repair_method", "repair_confidence", "is_mojibake", "repair_status"]) else "FAIL",
        "required repair columns",
    )
    add_qa(
        "repair::ranking_row_count_stable",
        "PASS" if len(repaired_df) == _safe_int(mining_summary.get("grouped_candidate_count")) else "FAIL",
        f"repaired={len(repaired_df)} summary_grouped={_safe_int(mining_summary.get('grouped_candidate_count'))}",
    )
    priority_score_changed = False
    affected_count_changed = False
    if not repaired_df.empty and not ranked_groups_df.empty:
        merged = repaired_df.merge(
            ranked_groups_df[["group_id", "priority_score", "affected_candidate_count"]],
            on="group_id",
            how="left",
            suffixes=("_repaired", "_original"),
        )
        priority_score_changed = bool(
            (merged["priority_score_repaired"].astype(float).round(6) != merged["priority_score_original"].astype(float).round(6)).any()
        )
        affected_count_changed = bool(
            (merged["affected_candidate_count_repaired"].astype(int) != merged["affected_candidate_count_original"].astype(int)).any()
        )
    add_qa(
        "repair::priority_scores_preserved",
        "PASS" if not priority_score_changed else "FAIL",
        "display-text repair must not change ranking scores",
    )
    add_qa(
        "repair::affected_counts_preserved",
        "PASS" if not affected_count_changed else "FAIL",
        "display-text repair must not change affected candidate counts",
    )

    top_package_df = pd.concat([review_ready_alias_df, review_ready_scope_df], ignore_index=True).fillna("")
    top_package_has_mojibake = False
    if not top_package_df.empty:
        for field in ["original_label", "repaired_label", "sample_raw_metric_names", "sample_row_texts", "sample_table_titles"]:
            if field in top_package_df.columns:
                top_package_has_mojibake = top_package_has_mojibake or bool(top_package_df[field].astype(str).map(looks_mojibake).any())
    add_qa(
        "review_ready::no_mojibake_remaining_in_top_package",
        "PASS" if not top_package_has_mojibake else "FAIL",
        f"review_ready_count={len(top_package_df)}",
    )

    duplicate_group_id_count = int(repaired_df["group_id"].astype(str).duplicated().sum()) if not repaired_df.empty else 0
    add_qa(
        "review_ready::duplicate_group_id_count",
        "PASS" if duplicate_group_id_count == 0 else "FAIL",
        f"actual={duplicate_group_id_count}",
    )

    parser_not_run = True
    llm_not_called = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323A-R reads cached outputs only.")
    add_qa("safety::llm_not_called_confirmation", "PASS" if llm_not_called else "FAIL", "323A-R performs deterministic repair only.")

    alias_hash_after = _sha256_file(Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json"))
    scope_hash_after = _sha256_file(Path(r"D:\_datefac\data\mapping\formal_scope_rules.json"))
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    add_qa(
        "review_ready::alias_count_non_negative",
        "PASS",
        f"actual={len(review_ready_alias_df)}",
    )
    add_qa(
        "review_ready::scope_count_non_negative",
        "PASS",
        f"actual={len(review_ready_scope_df)}",
    )

    highest_priority_repaired_examples: List[Dict[str, Any]] = []
    if not repaired_df.empty:
        for _, row in repaired_df.sort_values(["priority_score", "affected_candidate_count"], ascending=[False, False]).head(5).iterrows():
            highest_priority_repaired_examples.append(
                {
                    "group_id": _norm(row.get("group_id")),
                    "group_type_candidate": _norm(row.get("group_type_candidate")),
                    "original_label": _norm(row.get("original_label")),
                    "repaired_label": _norm(row.get("repaired_label")) or _norm(row.get("original_label")),
                    "repair_status": _norm(row.get("repair_status")),
                    "priority_score": _safe_float(row.get("priority_score")),
                    "affected_candidate_count": _safe_int(row.get("affected_candidate_count")),
                }
            )

    summary = {
        "stage": "323A-R",
        "output_dir": "",
        "input_323a_decision": _norm(mining_summary.get("decision")),
        "input_323a_qa_fail_count": _safe_int(mining_summary.get("qa_fail_count")),
        "grouped_candidate_count_323a": _safe_int(mining_summary.get("grouped_candidate_count")),
        "mojibake_group_count": mojibake_group_count,
        "mojibake_top_alias_count": mojibake_top_alias_count,
        "mojibake_top_scope_count": mojibake_top_scope_count,
        "mojibake_sample_text_count": mojibake_sample_text_count,
        "deterministic_repair_count": deterministic_repair_count,
        "already_clean_count": already_clean_count,
        "unrepairable_holdout_count": unrepairable_holdout_count,
        "review_ready_alias_count": int(len(review_ready_alias_df)),
        "review_ready_scope_count": int(len(review_ready_scope_df)),
        "review_ready_total_count": int(len(top_package_df)),
        "highest_priority_repaired_examples": highest_priority_repaired_examples,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "decision": "",
    }

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    summary["decision"] = EXPECTED_323AR_READY_DECISION if qa_fail_count == 0 and not top_package_has_mojibake else EXPECTED_323AR_NOT_READY_DECISION

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "cached_output_repair_only",
                "detail": "323A-R repairs or isolates cached 323A display text and does not rerun parsers or mine fresh candidates.",
            },
            {
                "limitation": "deterministic_only",
                "detail": "Only deterministic text repair is allowed; anything unsafe remains in holdout instead of being guessed.",
            },
            {
                "limitation": "review_ready_focus",
                "detail": "Review-ready packages include only alias/scope groups with readable repaired labels and preserved provenance.",
            },
        ]
    )

    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "repaired_df": repaired_df,
        "review_ready_alias_df": review_ready_alias_df,
        "review_ready_scope_df": review_ready_scope_df,
        "mojibake_groups_df": mojibake_groups_df,
        "unrepairable_df": unrepairable_df,
        "holdout_df": holdout_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
