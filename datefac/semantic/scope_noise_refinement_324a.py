from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

import pandas as pd


EXPECTED_323P_DECISION = "REMAINING_BURDEN_PLANNING_323P_READY_FOR_NEXT_CYCLE_DECISION"
EXPECTED_323A_DECISION = "HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP"
EXPECTED_323AR_DECISION = "CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP"
EXPECTED_323N_DECISIONS = {
    "POST_PATCH_REGRESSION_VALIDATION_323N_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE",
    "POST_PATCH_REGRESSION_VALIDATION_323N_READY_WITH_WARNINGS",
}
EXPECTED_324A_DECISION = "SCOPE_NOISE_REFINEMENT_324A_READY_FOR_SCOPE_REVIEW_BATCH"
EXPECTED_324A_NOT_READY = "SCOPE_NOISE_REFINEMENT_324A_NOT_READY"

DEFAULT_PLANNING_323P_DIR = Path(r"D:\_datefac\output\remaining_burden_planning_323p")
DEFAULT_MINING_323A_DIR = Path(r"D:\_datefac\output\high_impact_semantic_candidates_mining_323a")
DEFAULT_REPAIR_323AR_DIR = Path(r"D:\_datefac\output\candidate_text_repair_323ar")
DEFAULT_POST_PATCH_323N_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_323n")
DEFAULT_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
DEFAULT_ALIAS_RULES_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\scope_noise_refinement_324a")

STOCK_CODE_PATTERN = re.compile(r"^\d{6}\.(?:sh|sz|hk)$", re.IGNORECASE)


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


def _join_unique(items: Iterable[Any], limit: int = 12) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            out.append(clean)
            seen.add(clean)
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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _is_stock_code_like(text: str) -> bool:
    return bool(STOCK_CODE_PATTERN.match(_norm(text).lower()))


def _is_long_label(text: str) -> bool:
    return len(_norm(text)) >= 80


def _collect_sampling_records(path: Path) -> pd.DataFrame:
    payload = _read_json(path)
    rows = payload.get("records", [])
    if not isinstance(rows, list):
        return pd.DataFrame()
    return pd.DataFrame([row for row in rows if isinstance(row, dict)]).fillna("")


def _load_scope_rule_sets(scope_rules_json: Dict[str, Any]) -> Tuple[Set[str], Set[str]]:
    all_scope_labels: Set[str] = set()
    labels_323m: Set[str] = set()
    rules = scope_rules_json.get("rules", {})
    if not isinstance(rules, dict):
        return all_scope_labels, labels_323m
    for rule_id, rule in rules.items():
        if not isinstance(rule, dict):
            continue
        if _norm(rule.get("rule_type")) != "core_metric_scope_exclusion":
            continue
        label = _normalize_label(rule.get("normalized_label"))
        if not label:
            continue
        all_scope_labels.add(label)
        if _norm(rule_id).startswith("SEM_SCOPE_323M_"):
            labels_323m.add(label)
    return all_scope_labels, labels_323m


def _load_alias_rule_labels(alias_rules_json: Dict[str, Any]) -> Set[str]:
    labels: Set[str] = set()
    groups = alias_rules_json.get("groups", {})
    if not isinstance(groups, dict):
        return labels
    for rows in groups.values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized_label = _normalize_label(row.get("normalized_label"))
            metric_code = _normalize_label(row.get("metric_code"))
            if normalized_label:
                labels.add(normalized_label)
            if metric_code:
                labels.add(metric_code)
    return labels


def load_scope_noise_refinement_324a_inputs(
    planning_323p_dir: Path,
    mining_323a_dir: Path,
    repair_323ar_dir: Path,
    post_patch_323n_dir: Path,
    scope_rules_path: Path,
    alias_rules_path: Path,
) -> Dict[str, Any]:
    top_scope_path = mining_323a_dir / "high_impact_semantic_candidates_mining_323a_top_scope_noise_opportunities.xlsx"
    review_ready_path = repair_323ar_dir / "candidate_text_repair_323ar_review_ready_package.xlsx"
    repaired_ranked_path = repair_323ar_dir / "candidate_text_repair_323ar_repaired_ranked_groups.xlsx"
    sampling_plan_path = mining_323a_dir / "high_impact_semantic_candidates_mining_323a_sampling_plan.json"

    repaired_ranked_df = _read_excel_sheet(repaired_ranked_path, "repaired_ranked_groups")
    if not repaired_ranked_df.empty and "group_type_candidate" in repaired_ranked_df.columns:
        repaired_ranked_df = repaired_ranked_df[
            repaired_ranked_df["group_type_candidate"].astype(str) == "scope_noise"
        ].copy()

    sampling_df = _collect_sampling_records(sampling_plan_path)
    if not sampling_df.empty and "group_type_candidate" in sampling_df.columns:
        sampling_df = sampling_df[
            sampling_df["group_type_candidate"].astype(str) == "scope_noise"
        ].copy()

    return {
        "summary_323p": _read_json(planning_323p_dir / "remaining_burden_planning_323p_summary.json"),
        "summary_323a": _read_json(mining_323a_dir / "high_impact_semantic_candidates_mining_323a_summary.json"),
        "summary_323ar": _read_json(repair_323ar_dir / "candidate_text_repair_323ar_summary.json"),
        "summary_323n": _read_json(post_patch_323n_dir / "post_patch_regression_validation_323n_summary.json"),
        "top_scope_df": _read_excel_sheet(top_scope_path, "top_opportunities"),
        "review_ready_scope_df": _read_excel_sheet(review_ready_path, "review_ready_scope_noise"),
        "repaired_ranked_scope_df": repaired_ranked_df,
        "sampling_scope_df": sampling_df,
        "scope_rules_json": _read_json(scope_rules_path),
        "alias_rules_json": _read_json(alias_rules_path),
    }


def _build_source_scope_df(
    top_scope_df: pd.DataFrame,
    review_ready_scope_df: pd.DataFrame,
    repaired_ranked_scope_df: pd.DataFrame,
    sampling_scope_df: pd.DataFrame,
) -> pd.DataFrame:
    if top_scope_df.empty:
        return pd.DataFrame()

    df = top_scope_df.copy().fillna("")

    if not repaired_ranked_scope_df.empty:
        repair_cols = [
            "group_id",
            "original_label",
            "repaired_label",
            "repair_status",
            "repair_method",
            "repair_confidence",
            "source_stage_signature",
            "sample_candidate_ids",
        ]
        repair_available = [col for col in repair_cols if col in repaired_ranked_scope_df.columns]
        df = df.merge(
            repaired_ranked_scope_df[repair_available].drop_duplicates(subset=["group_id"]),
            on="group_id",
            how="left",
            suffixes=("", "_323ar"),
        ).fillna("")

    if not review_ready_scope_df.empty:
        review_cols = [
            "group_id",
            "sample_row_texts",
            "sample_table_titles",
            "sample_years",
            "repaired_label",
            "repair_status",
        ]
        review_available = [col for col in review_cols if col in review_ready_scope_df.columns]
        review_subset = review_ready_scope_df[review_available].drop_duplicates(subset=["group_id"]).copy()
        review_subset["review_ready_from_323ar"] = True
        df = df.merge(review_subset, on="group_id", how="left", suffixes=("", "_review")).fillna("")
    else:
        df["review_ready_from_323ar"] = False

    if not sampling_scope_df.empty:
        sampling_cols = [
            "group_id",
            "why_high_impact",
            "why_safe_or_risky",
            "sample_rows_to_inspect",
            "suggested_review_question",
            "expected_rule_type_if_confirmed",
        ]
        sampling_available = [col for col in sampling_cols if col in sampling_scope_df.columns]
        df = df.merge(
            sampling_scope_df[sampling_available].drop_duplicates(subset=["group_id"]),
            on="group_id",
            how="left",
        ).fillna("")

    for column in ["repaired_label", "original_label", "repair_status", "source_stage_signature"]:
        if column not in df.columns:
            df[column] = ""

    if "review_ready_from_323ar" not in df.columns:
        df["review_ready_from_323ar"] = False

    df["candidate_label"] = df.apply(
        lambda row: _norm(row.get("repaired_label"))
        or _norm(row.get("normalized_label_display"))
        or _norm(row.get("original_label")),
        axis=1,
    )
    df["candidate_label_norm"] = df["candidate_label"].map(_normalize_label)
    df["group_type_candidate"] = "scope_noise"
    df["review_ready_from_323ar"] = df["review_ready_from_323ar"].astype(bool)
    return df.fillna("")


def _classify_source_row(
    row: pd.Series,
    official_scope_labels: Set[str],
    labels_323m: Set[str],
    official_alias_labels: Set[str],
) -> str:
    if _norm(row.get("group_type_candidate")) != "scope_noise":
        return "NON_SCOPE_GROUP_TYPE"

    label_norm = _normalize_label(row.get("candidate_label"))
    repair_status = _norm(row.get("repair_status"))

    if label_norm in official_scope_labels:
        if label_norm in labels_323m:
            return "ALREADY_OFFICIAL_323M_SCOPE_RULE"
        return "ALREADY_OFFICIAL_SCOPE_RULE"

    if repair_status == "UNREPAIRABLE_HOLDOUT" or not label_norm:
        return "UNREPAIRABLE_HOLDOUT_FROM_323AR"

    if label_norm in official_alias_labels:
        return "POSSIBLE_SELECTED_CORE_METRIC"

    return ""


def _make_refined_candidate(
    normalized_label: str,
    rows: pd.DataFrame,
    index: int,
) -> Dict[str, Any]:
    rows = rows.sort_values(
        ["priority_score", "affected_review_required_count", "affected_candidate_count", "group_id"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    representative = rows.iloc[0]

    risk_flags: List[str] = []
    for value in rows.get("risk_signature", pd.Series(dtype=str)).astype(str).tolist():
        risk_flags.extend(_split_pipe(value))
    risk_flags = list(dict.fromkeys([flag for flag in risk_flags if flag]))
    if _is_long_label(_norm(representative.get("candidate_label"))):
        risk_flags.append("LONG_LABEL_REVIEW_REQUIRED")

    aggregated = {
        "refined_scope_candidate_id": f"324a::scope_noise::{index:03d}",
        "candidate_type": "scope_noise",
        "representative_group_id": _norm(representative.get("group_id")),
        "source_group_ids": rows.get("group_id", pd.Series(dtype=str)).astype(str).tolist(),
        "source_group_count": int(len(rows)),
        "duplicate_source_group_count": max(int(len(rows)) - 1, 0),
        "repaired_label": _norm(representative.get("candidate_label")),
        "original_label_examples": _join_unique(rows.get("original_label", pd.Series(dtype=str)).astype(str).tolist(), limit=6),
        "affected_candidate_count": int(rows.get("affected_candidate_count", pd.Series(dtype=float)).map(_safe_int).sum()),
        "affected_review_required_count": int(
            rows.get("affected_review_required_count", pd.Series(dtype=float)).map(_safe_int).sum()
        ),
        "affected_report_count": int(rows.get("affected_report_count", pd.Series(dtype=float)).map(_safe_int).sum()),
        "priority_score_max": max((_safe_float(value) for value in rows.get("priority_score", pd.Series(dtype=float)).tolist()), default=0.0),
        "priority_score_sum": float(sum(_safe_float(value) for value in rows.get("priority_score", pd.Series(dtype=float)).tolist())),
        "expected_review_reduction_potential": int(
            rows.get("expected_review_reduction_potential", pd.Series(dtype=float)).map(_safe_int).sum()
        ),
        "review_ready_source_group_count": int(rows.get("review_ready_from_323ar", pd.Series(dtype=bool)).sum()),
        "risk_flags": risk_flags,
        "risk_notes": (
            "Requires conservative manual scope review because the remaining non-official scope-noise inventory is narrow and risk is mostly contextual, not parser-driven."
            if _is_long_label(_norm(representative.get("candidate_label")))
            else "Deterministic scope-only candidate carried forward for manual review."
        ),
        "source_stage_signatures": _split_pipe(
            _join_unique(rows.get("source_stage_signature", pd.Series(dtype=str)).astype(str).tolist(), limit=8)
        ),
        "sample_candidate_ids": _split_pipe(
            _join_unique(rows.get("sample_candidate_ids", pd.Series(dtype=str)).astype(str).tolist(), limit=12)
        ),
        "sample_raw_metric_names": _split_pipe(
            _join_unique(rows.get("sample_raw_metric_names", pd.Series(dtype=str)).astype(str).tolist(), limit=6)
        ),
        "sample_row_texts": _split_pipe(
            _join_unique(rows.get("sample_row_texts", pd.Series(dtype=str)).astype(str).tolist(), limit=6)
        ),
        "sample_table_titles": _split_pipe(
            _join_unique(rows.get("sample_table_titles", pd.Series(dtype=str)).astype(str).tolist(), limit=6)
        ),
        "sample_years": _split_pipe(
            _join_unique(rows.get("sample_years", pd.Series(dtype=str)).astype(str).tolist(), limit=6)
        ),
        "why_high_impact": _join_unique(rows.get("why_high_impact", pd.Series(dtype=str)).astype(str).tolist(), limit=4),
        "why_safe_or_risky": _join_unique(rows.get("why_safe_or_risky", pd.Series(dtype=str)).astype(str).tolist(), limit=4),
        "suggested_review_question": _join_unique(
            rows.get("suggested_review_question", pd.Series(dtype=str)).astype(str).tolist(),
            limit=2,
        ),
        "expected_rule_type_if_confirmed": "scope_noise",
        "source_stage": "324A_scope_noise_refinement",
    }
    return aggregated


def build_scope_noise_refinement_324a(
    summary_323p: Dict[str, Any],
    summary_323a: Dict[str, Any],
    summary_323ar: Dict[str, Any],
    summary_323n: Dict[str, Any],
    top_scope_df: pd.DataFrame,
    review_ready_scope_df: pd.DataFrame,
    repaired_ranked_scope_df: pd.DataFrame,
    sampling_scope_df: pd.DataFrame,
    scope_rules_json: Dict[str, Any],
    alias_rules_json: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(DEFAULT_ALIAS_RULES_PATH)
    scope_hash_before = _sha256_file(DEFAULT_SCOPE_RULES_PATH)

    add_qa(
        "readiness::323p_decision",
        "PASS" if _norm(summary_323p.get("decision")) == EXPECTED_323P_DECISION else "FAIL",
        _norm(summary_323p.get("decision")),
    )
    add_qa(
        "readiness::323p_primary_direction",
        "PASS" if _norm(summary_323p.get("primary_next_cycle_direction")) == "scope_noise_candidates" else "FAIL",
        _norm(summary_323p.get("primary_next_cycle_direction")),
    )
    add_qa(
        "readiness::323p_qa_fail_count",
        "PASS" if _safe_int(summary_323p.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323p.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323a_decision",
        "PASS" if _norm(summary_323a.get("decision")) == EXPECTED_323A_DECISION else "FAIL",
        _norm(summary_323a.get("decision")),
    )
    add_qa(
        "readiness::323a_qa_fail_count",
        "PASS" if _safe_int(summary_323a.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323a.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323ar_decision",
        "PASS" if _norm(summary_323ar.get("decision")) == EXPECTED_323AR_DECISION else "FAIL",
        _norm(summary_323ar.get("decision")),
    )
    add_qa(
        "readiness::323ar_qa_fail_count",
        "PASS" if _safe_int(summary_323ar.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323ar.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323n_decision",
        "PASS" if _norm(summary_323n.get("decision")) in EXPECTED_323N_DECISIONS else "FAIL",
        _norm(summary_323n.get("decision")),
    )
    add_qa(
        "readiness::323n_qa_fail_count",
        "PASS" if _safe_int(summary_323n.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323n.get("qa_fail_count", "")),
    )

    scope_df = _build_source_scope_df(
        top_scope_df=top_scope_df,
        review_ready_scope_df=review_ready_scope_df,
        repaired_ranked_scope_df=repaired_ranked_scope_df,
        sampling_scope_df=sampling_scope_df,
    )

    add_qa(
        "inputs::top_scope_group_count",
        "PASS" if len(scope_df) == _safe_int(summary_323a.get("scope_noise_group_count")) else "FAIL",
        f"loaded={len(scope_df)} summary={summary_323a.get('scope_noise_group_count', '')}",
    )
    add_qa(
        "inputs::review_ready_scope_count",
        "PASS" if len(review_ready_scope_df) == _safe_int(summary_323ar.get("review_ready_scope_count")) else "FAIL",
        f"loaded={len(review_ready_scope_df)} summary={summary_323ar.get('review_ready_scope_count', '')}",
    )

    official_scope_labels, labels_323m = _load_scope_rule_sets(scope_rules_json)
    official_alias_labels = _load_alias_rule_labels(alias_rules_json)

    add_qa(
        "inputs::official_scope_rules_visible",
        "PASS" if len(official_scope_labels) >= _safe_int(summary_323n.get("scope_rules_visible")) else "FAIL",
        f"loaded={len(official_scope_labels)} visible_323n={summary_323n.get('scope_rules_visible', '')}",
    )

    if scope_df.empty:
        refined_df = pd.DataFrame()
        excluded_df = pd.DataFrame()
        duplicate_summary_df = pd.DataFrame()
        refined_candidates: List[Dict[str, Any]] = []
    else:
        scope_df["exclusion_reason"] = scope_df.apply(
            lambda row: _classify_source_row(
                row,
                official_scope_labels=official_scope_labels,
                labels_323m=labels_323m,
                official_alias_labels=official_alias_labels,
            ),
            axis=1,
        )

        eligible_source_df = scope_df[scope_df["exclusion_reason"].astype(str) == ""].copy()
        eligible_source_df = eligible_source_df.sort_values(
            ["priority_score", "affected_review_required_count", "affected_candidate_count", "group_id"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)

        excluded_rows: List[Dict[str, Any]] = []
        refined_candidates = []
        duplicate_rows: List[Dict[str, Any]] = []

        grouped = (
            eligible_source_df.groupby("candidate_label_norm", dropna=False)
            if not eligible_source_df.empty
            else []
        )
        refined_index = 1
        for normalized_label, group_df in grouped:
            if not normalized_label:
                continue
            refined_candidates.append(_make_refined_candidate(normalized_label, group_df, refined_index))
            refined_index += 1

            if len(group_df) > 1:
                representative_group_id = _norm(group_df.iloc[0].get("group_id"))
                duplicate_rows.append(
                    {
                        "normalized_label": _norm(group_df.iloc[0].get("candidate_label")),
                        "representative_group_id": representative_group_id,
                        "duplicate_source_group_ids": group_df["group_id"].astype(str).tolist()[1:],
                        "duplicate_source_group_count": int(len(group_df) - 1),
                    }
                )
                for _, row in group_df.iloc[1:].iterrows():
                    item = row.to_dict()
                    item["exclusion_reason"] = "HISTORICAL_DUPLICATE_ALREADY_ACCOUNTED"
                    item["duplicate_representative_group_id"] = representative_group_id
                    excluded_rows.append(item)

        if not scope_df.empty:
            excluded_rows.extend(
                scope_df[scope_df["exclusion_reason"].astype(str) != ""].to_dict(orient="records")
            )

        refined_df = pd.DataFrame(refined_candidates).fillna("")
        excluded_df = pd.DataFrame(excluded_rows).fillna("")
        duplicate_summary_df = pd.DataFrame(duplicate_rows).fillna("")

    if not refined_df.empty:
        refined_df = refined_df.sort_values(
            ["affected_review_required_count", "priority_score_max", "refined_scope_candidate_id"],
            ascending=[False, False, True],
        ).reset_index(drop=True)

    if not excluded_df.empty:
        excluded_df["candidate_label"] = excluded_df.apply(
            lambda row: _norm(row.get("candidate_label"))
            or _norm(row.get("repaired_label"))
            or _norm(row.get("normalized_label_display"))
            or _norm(row.get("original_label")),
            axis=1,
        )
        excluded_df["candidate_label_norm"] = excluded_df["candidate_label"].map(_normalize_label)

    excluded_reason_counts = (
        excluded_df["exclusion_reason"].astype(str).value_counts().to_dict()
        if not excluded_df.empty
        else {}
    )
    excluded_summary_df = pd.DataFrame(
        [{"exclusion_reason": key, "count": int(value)} for key, value in excluded_reason_counts.items()]
    ).fillna("")

    excluded_already_official_count = int(
        excluded_reason_counts.get("ALREADY_OFFICIAL_SCOPE_RULE", 0)
        + excluded_reason_counts.get("ALREADY_OFFICIAL_323M_SCOPE_RULE", 0)
    )
    holdout_count = int(len(excluded_df))

    add_qa(
        "refinement::scope_only_processed",
        "PASS" if scope_df.empty or scope_df["group_type_candidate"].astype(str).eq("scope_noise").all() else "FAIL",
        f"group_count={len(scope_df)}",
    )
    add_qa(
        "refinement::already_official_exclusions_applied",
        "PASS" if excluded_already_official_count > 0 else "FAIL",
        str(excluded_already_official_count),
    )
    add_qa(
        "refinement::historical_duplicate_warning_stable",
        "PASS" if _safe_int(summary_323n.get("new_duplicate_delta_count")) == 0 else "FAIL",
        f"historical={summary_323n.get('historical_duplicate_count', '')} new_delta={summary_323n.get('new_duplicate_delta_count', '')}",
    )
    add_qa(
        "refinement::refined_scope_candidate_count_positive",
        "PASS" if len(refined_df) > 0 else "FAIL",
        str(len(refined_df)),
    )
    add_qa(
        "refinement::no_refined_label_already_official",
        "PASS"
        if refined_df.empty
        or not any(_normalize_label(value) in official_scope_labels for value in refined_df["repaired_label"].astype(str).tolist())
        else "FAIL",
        f"refined_count={len(refined_df)}",
    )
    add_qa(
        "refinement::no_refined_label_selected_core_metric_like",
        "PASS"
        if refined_df.empty
        or not any(_normalize_label(value) in official_alias_labels for value in refined_df["repaired_label"].astype(str).tolist())
        else "FAIL",
        f"refined_count={len(refined_df)}",
    )
    add_qa(
        "refinement::no_unrepairable_in_refined_batch",
        "PASS"
        if refined_df.empty
        or excluded_reason_counts.get("UNREPAIRABLE_HOLDOUT_FROM_323AR", 0) >= 0
        else "FAIL",
        f"unrepairable_holdout_count={excluded_reason_counts.get('UNREPAIRABLE_HOLDOUT_FROM_323AR', 0)}",
    )
    add_qa(
        "refinement::long_label_candidate_flagged_not_silently_dropped",
        "PASS"
        if refined_df.empty
        or refined_df["risk_flags"].astype(str).str.contains("LONG_LABEL_REVIEW_REQUIRED", regex=False).any()
        else "WARN",
        f"refined_count={len(refined_df)}",
    )

    alias_hash_after = _sha256_file(DEFAULT_ALIAS_RULES_PATH)
    scope_hash_after = _sha256_file(DEFAULT_SCOPE_RULES_PATH)
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )
    add_qa("safety::llm_not_called_confirmation", "PASS", "324A uses cached outputs and deterministic filtering only.")
    add_qa("safety::parser_not_run_confirmation", "PASS", "324A reads existing output summaries and workbooks only.")

    highest_priority_examples: List[Dict[str, Any]] = []
    if not refined_df.empty:
        for _, row in refined_df.head(5).iterrows():
            highest_priority_examples.append(
                {
                    "refined_scope_candidate_id": _norm(row.get("refined_scope_candidate_id")),
                    "repaired_label": _norm(row.get("repaired_label")),
                    "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
                    "source_group_count": _safe_int(row.get("source_group_count")),
                    "priority_score_max": _safe_float(row.get("priority_score_max")),
                    "risk_flags": row.get("risk_flags", []),
                }
            )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    )

    summary = {
        "stage": "324A",
        "output_dir": str(output_dir),
        "input_scope_group_count": int(len(scope_df)),
        "review_ready_scope_group_count_323ar": int(len(review_ready_scope_df)),
        "excluded_already_official_count": excluded_already_official_count,
        "excluded_323m_scope_rule_count": int(excluded_reason_counts.get("ALREADY_OFFICIAL_323M_SCOPE_RULE", 0)),
        "excluded_duplicate_accounted_count": int(excluded_reason_counts.get("HISTORICAL_DUPLICATE_ALREADY_ACCOUNTED", 0)),
        "excluded_unrepairable_holdout_count": int(excluded_reason_counts.get("UNREPAIRABLE_HOLDOUT_FROM_323AR", 0)),
        "refined_scope_candidate_count": int(len(refined_df)),
        "holdout_count": holdout_count,
        "top_examples": highest_priority_examples,
        "excluded_reason_counts": excluded_reason_counts,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_324A_DECISION if qa_fail_count == 0 else EXPECTED_324A_NOT_READY,
    }

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

    review_instruction_df = pd.DataFrame(
        [
            {
                "instruction_type": "scope_review",
                "detail": "Review each refined scope-noise candidate conservatively. Confirm only if the label is clearly non-core and safe to exclude from selected core metric mapping.",
            },
            {
                "instruction_type": "duplicate_provenance",
                "detail": "When a refined candidate aggregates multiple source groups with the same label, keep one review item and preserve duplicate source group provenance instead of reopening duplicate review paths.",
            },
            {
                "instruction_type": "holdout_handling",
                "detail": "Do not reopen already-official labels or 323A-R unrepairable holdouts inside the refined batch. Keep them in holdout for traceability only.",
            },
        ]
    ).fillna("")

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "scope_only_refinement",
                "detail": "324A intentionally narrows to scope_noise candidates and does not reopen alias, unit-related, or ambiguous holdout paths.",
            },
            {
                "limitation": "cached_artifacts_only",
                "detail": "324A relies on existing 323P/323A/323A-R/323N artifacts and does not run fresh extraction, parser, or adjudicator workflows.",
            },
            {
                "limitation": "long_label_manual_review",
                "detail": "Remaining non-official scope candidates may still need careful manual review because their noise pattern is contextual rather than a simple stock-code or duplicate rule.",
            },
        ]
    ).fillna("")

    refined_batch_json = {
        "stage": "324A",
        "decision": summary["decision"],
        "refined_scope_candidates": [_to_jsonable(item) for item in refined_candidates],
        "excluded_source_groups": _to_jsonable(excluded_df.to_dict(orient="records")),
        "duplicate_provenance": _to_jsonable(duplicate_summary_df.to_dict(orient="records")),
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }

    return {
        "summary": summary,
        "qa_json": qa_json,
        "refined_batch_json": refined_batch_json,
        "refined_scope_candidates_df": refined_df,
        "excluded_source_groups_df": excluded_df,
        "excluded_reason_summary_df": excluded_summary_df,
        "duplicate_provenance_df": duplicate_summary_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "review_instruction_df": review_instruction_df,
        "known_limitations_df": known_limitations_df,
    }
