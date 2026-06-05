from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd

from datefac.semantic.human_confirmed_patch_preview import (
    _candidate_passes_trust_gate,
    _normalize_label,
    apply_human_confirmed_patches,
    build_remaining_review_burden,
    read_jsonl,
)


EXPECTED_325H_DECISION = "ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_READY_FOR_325I_SANDBOX_REPLAY"
EXPECTED_325G_DECISION = "ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_READY_FOR_HUMAN_CONFIRMATION"
READY_DECISION = "ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_READY_FOR_325J_OFFICIAL_RULE_CANDIDATES"
READY_WARN_DECISION = "ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_READY_WITH_WARNINGS"
NOT_READY_DECISION = "ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_NOT_READY"

DEFAULT_REVIEWED_CONFIRMATION_DIR = Path(r"D:\_datefac\output\alias_human_confirmation_325h_reviewed")
DEFAULT_SCHEMA_VALIDATION_DIR = Path(r"D:\_datefac\output\alias_response_schema_validation_325g")
DEFAULT_REQUEST_DIR = Path(r"D:\_datefac\output\alias_safe_adjudicator_request_325e")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_POST_PATCH_REGRESSION_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_324m")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

TARGET_MAP = {
    "EBIT": {
        "metric_code": "EBIT",
        "metric_family": "profitability",
        "canonical_metric_name": "EBIT",
    },
    "attributable_net_margin": {
        "metric_code": "attributable_net_margin",
        "metric_family": "profitability",
        "canonical_metric_name": "Attributable Net Margin",
    },
    "ROE": {
        "metric_code": "ROE",
        "metric_family": "profitability",
        "canonical_metric_name": "ROE",
    },
    "diluted_EPS": {
        "metric_code": "diluted_EPS",
        "metric_family": "per_share",
        "canonical_metric_name": "Diluted EPS",
    },
    "adjusted_EPS": {
        "metric_code": "adjusted_EPS",
        "metric_family": "per_share",
        "canonical_metric_name": "Adjusted EPS",
    },
    "adjusted_attributable_net_profit": {
        "metric_code": "adjusted_attributable_net_profit",
        "metric_family": "profitability",
        "canonical_metric_name": "Adjusted Attributable Net Profit",
    },
}


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


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _official_hashes() -> Dict[str, str]:
    return {
        "formal_scope_rules": _sha256_file(FORMAL_SCOPE_RULES_PATH),
        "semantic_alias_candidates": _sha256_file(OFFICIAL_ALIAS_OVERRIDE_PATH),
    }


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
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


def _split_flags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [part.strip() for part in text.replace(",", "|").split("|") if part.strip()]


def _metric_key(value: Any) -> str:
    return _norm(value).lower().replace(" ", "").replace("_", "").replace("-", "")


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _flatten_official_aliases(payload: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return pd.DataFrame()
    for group_name, items in groups.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row["target_group"] = _norm(group_name)
            row["normalized_label_key"] = _normalize_label(row.get("normalized_label"))
            rows.append(row)
    return pd.DataFrame(rows).fillna("")


def _flatten_official_scope_rules(payload: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        return pd.DataFrame()
    for rule_id, item in rules.items():
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("rule_id", _norm(rule_id))
        row["normalized_label_key"] = _normalize_label(row.get("normalized_label"))
        rows.append(row)
    return pd.DataFrame(rows).fillna("")


def load_alias_human_confirmed_sandbox_replay_325i_inputs(
    reviewed_confirmation_dir: Path,
    schema_validation_dir: Path,
    request_dir: Path,
    trust_split_dir: Path,
    post_patch_regression_dir: Path,
) -> Dict[str, Any]:
    request_package = _read_json(request_dir / "alias_safe_adjudicator_request_325e_request_package.json")
    return {
        "reviewed_summary": _read_json(
            reviewed_confirmation_dir / "alias_human_confirmation_325h_reviewed_summary.json"
        ),
        "reviewed_qa": _read_json(
            reviewed_confirmation_dir / "alias_human_confirmation_325h_reviewed_qa.json"
        ),
        "reviewed_plan": _read_json(
            reviewed_confirmation_dir / "alias_human_confirmation_325h_human_confirmed_plan.json"
        ),
        "schema_summary": _read_json(
            schema_validation_dir / "alias_response_schema_validation_325g_summary.json"
        ),
        "schema_qa": _read_json(
            schema_validation_dir / "alias_response_schema_validation_325g_qa.json"
        ),
        "validated_suggestions": _read_json(
            schema_validation_dir / "alias_response_schema_validation_325g_validated_suggestions.json"
        ),
        "request_package": request_package,
        "request_items": request_package.get("request_items", [])
        if isinstance(request_package.get("request_items"), list)
        else [],
        "trust_summary": _read_json(
            trust_split_dir / "router_mineru_trust_split_322b2_summary.json"
        ),
        "selected_candidates_df": read_jsonl(
            trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"
        ),
        "post_patch_summary": _read_json(
            post_patch_regression_dir / "post_patch_regression_validation_324m_summary.json"
        ),
        "official_alias_df": _flatten_official_aliases(_read_json(OFFICIAL_ALIAS_OVERRIDE_PATH)),
        "official_scope_df": _flatten_official_scope_rules(_read_json(FORMAL_SCOPE_RULES_PATH)),
        "official_hashes_before": _official_hashes(),
    }


def _confirmed_records(reviewed_plan: Dict[str, Any]) -> pd.DataFrame:
    rows = reviewed_plan.get("confirmed_records", [])
    if not isinstance(rows, list):
        return pd.DataFrame()
    return pd.DataFrame([row for row in rows if isinstance(row, dict)]).fillna("")


def _request_lookup(request_items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in request_items:
        if not isinstance(item, dict):
            continue
        request_id = _norm(item.get("request_id"))
        if request_id:
            out[request_id] = item
    return out


def _build_rule_inventory(confirmed_df: pd.DataFrame, request_items: List[Dict[str, Any]]) -> pd.DataFrame:
    request_map = _request_lookup(request_items)
    rows: List[Dict[str, Any]] = []
    if confirmed_df.empty:
        return pd.DataFrame()
    for index, (_, row) in enumerate(confirmed_df.iterrows(), start=1):
        request_id = _norm(row.get("request_id"))
        request_item = request_map.get(request_id, {})
        target_metric = _norm(row.get("target_metric"))
        target_payload = TARGET_MAP.get(target_metric, {})
        alias_label = _norm(row.get("alias_label"))
        normalized_alias_label = _norm(row.get("normalized_alias_label"))
        rows.append(
            {
                "source_rule_id": f"325i::sandbox_alias_rule::{index:03d}",
                "confirmation_id": _norm(row.get("confirmation_id")),
                "request_id": request_id,
                "source_candidate_id": _norm(row.get("source_candidate_id"))
                or _norm(request_item.get("source_candidate_id")),
                "proposal_type": "alias",
                "alias_label": alias_label,
                "normalized_alias_label": normalized_alias_label,
                "normalized_label": alias_label,
                "normalized_label_key": _normalize_label(alias_label),
                "target_metric": target_metric,
                "proposed_metric_code": _norm(target_payload.get("metric_code")),
                "proposed_metric_family": _norm(target_payload.get("metric_family")),
                "canonical_metric_name": _norm(target_payload.get("canonical_metric_name")),
                "confidence": _norm(row.get("confidence")),
                "rationale": _norm(row.get("rationale")),
                "deterministic_gate_result": _norm(row.get("deterministic_gate_result")),
                "risk_flags": _norm(row.get("risk_flags")),
                "evidence": _norm(row.get("evidence")),
                "provenance": _norm(row.get("provenance")),
                "reviewer_note": _norm(row.get("reviewer_note")),
                "reviewer_name": _norm(row.get("reviewer_name")),
                "review_timestamp": _norm(row.get("review_timestamp")),
                "request_reference": json.dumps(request_item, ensure_ascii=False),
                "target_resolved": bool(target_payload),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_apply_dataframe(rule_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if rule_df.empty:
        return pd.DataFrame()
    for _, row in rule_df.iterrows():
        rows.append(
            {
                "proposal_id": _norm(row.get("source_rule_id")),
                "proposal_type": "alias",
                "source_case_id": _norm(row.get("confirmation_id")),
                "normalized_label": _norm(row.get("normalized_label")),
                "sample_table_titles": "",
                "sample_row_labels": _norm(row.get("alias_label")),
                "sample_values": "",
                "risk_flags": _norm(row.get("risk_flags")),
                "affected_candidate_count": 0,
                "review_reduction": 0,
                "reviewer_decision": "CONFIRM",
                "reviewer_comment": _join_unique(
                    [
                        _norm(row.get("reviewer_note")),
                        _norm(row.get("rationale")),
                    ],
                    limit=4,
                ),
                "proposed_metric_code": _norm(row.get("proposed_metric_code")),
                "proposed_metric_family": _norm(row.get("proposed_metric_family")),
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_duplicate_conflict_df(
    rule_df: pd.DataFrame,
    official_alias_df: pd.DataFrame,
    official_scope_df: pd.DataFrame,
) -> pd.DataFrame:
    if rule_df.empty:
        return pd.DataFrame()
    official_alias_keys = set(official_alias_df.get("normalized_label_key", pd.Series(dtype=str)).astype(str))
    official_scope_keys = set(official_scope_df.get("normalized_label_key", pd.Series(dtype=str)).astype(str))
    rows: List[Dict[str, Any]] = []
    for (label_key,), group in rule_df.groupby(["normalized_label_key"], dropna=False):
        targets = sorted({_norm(value) for value in group["proposed_metric_code"].tolist() if _norm(value)})
        rows.append(
            {
                "normalized_label": _norm(group.iloc[0].get("normalized_label")),
                "normalized_label_key": _norm(label_key),
                "source_rule_count": int(len(group)),
                "duplicate_rule": int(len(group)) > 1,
                "proposed_metric_codes": " | ".join(targets),
                "target_conflict": len(targets) > 1,
                "official_alias_overlap": _norm(label_key) in official_alias_keys,
                "official_scope_overlap": _norm(label_key) in official_scope_keys,
                "source_rule_ids": _join_unique(group["source_rule_id"].tolist(), limit=12),
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(["normalized_label_key"]).reset_index(drop=True)


def _special_check_rows(rule_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, row in rule_df.iterrows():
        alias_text = f"{_norm(row.get('alias_label'))} {_norm(row.get('normalized_alias_label'))}"
        alias_key = _metric_key(alias_text)
        target_key = _metric_key(row.get("target_metric"))
        failures: List[str] = []
        adjusted_mismatch = False
        diluted_mismatch = False

        if _metric_key(row.get("alias_label")) == "ebit" and target_key != "ebit":
            failures.append("EBIT_MUST_MAP_ONLY_TO_EBIT")
        if "roe" in alias_key and target_key != "roe":
            failures.append("ROE_MUST_MAP_ONLY_TO_ROE")
        if any(term in alias_key for term in ["diluted", "摊薄", "latestdiluted", "最新摊薄"]):
            if target_key in {"eps", "basiceps", "每股收益"} or target_key != "dilutedeps":
                diluted_mismatch = True
                failures.append("DILUTED_EPS_ALIAS_MUST_NOT_MAP_TO_BASIC_EPS")
        if "经调整" in alias_text and "eps" in alias_key:
            if target_key != "adjustedeps":
                adjusted_mismatch = True
                failures.append("ADJUSTED_EPS_MUST_NOT_MAP_TO_ORDINARY_EPS")
        if "经调整" in alias_text and ("归母净利润" in alias_text or "attributable" in alias_key):
            if target_key != "adjustedattributablenetprofit":
                adjusted_mismatch = True
                failures.append("ADJUSTED_ATTRIBUTABLE_NET_PROFIT_MUST_NOT_MAP_TO_ORDINARY_ATTRIBUTABLE_NET_PROFIT")
        if "netmargin" in target_key or "净利率" in alias_text:
            if target_key in {"netprofit", "attributablenetprofit", "归母净利润", "归属母公司净利润"}:
                failures.append("ATTRIBUTABLE_NET_MARGIN_MUST_NOT_MAP_TO_NET_PROFIT")

        rows.append(
            {
                "source_rule_id": _norm(row.get("source_rule_id")),
                "alias_label": _norm(row.get("alias_label")),
                "target_metric": _norm(row.get("target_metric")),
                "special_check_pass": len(failures) == 0,
                "failure_reasons": " | ".join(failures),
                "adjusted_metric_mismatch": adjusted_mismatch,
                "diluted_eps_mismatch": diluted_mismatch,
            }
        )
    return pd.DataFrame(rows).fillna("")


def _core_false_mapping_df(diff_df: pd.DataFrame, rule_df: pd.DataFrame) -> pd.DataFrame:
    if diff_df.empty or rule_df.empty:
        return pd.DataFrame()
    expected_by_rule = {
        _norm(row.get("source_rule_id")): _norm(row.get("proposed_metric_code"))
        for _, row in rule_df.iterrows()
    }
    rows: List[Dict[str, Any]] = []
    for _, row in diff_df.iterrows():
        proposal_id = _norm(row.get("proposal_id"))
        expected = expected_by_rule.get(proposal_id, "")
        actual = _norm(row.get("metric_code_after"))
        if expected and actual and actual != expected:
            item = row.to_dict()
            item["expected_metric_code"] = expected
            item["false_mapping_reason"] = "metric_code_after_does_not_match_sandbox_rule_target"
            rows.append(item)
    return pd.DataFrame(rows).fillna("")


def _sandbox_rules_json(rule_df: pd.DataFrame, duplicate_conflict_df: pd.DataFrame) -> Dict[str, Any]:
    rules: List[Dict[str, Any]] = []
    for _, row in rule_df.iterrows():
        rules.append(
            {
                "source_rule_id": _norm(row.get("source_rule_id")),
                "confirmation_id": _norm(row.get("confirmation_id")),
                "request_id": _norm(row.get("request_id")),
                "source_candidate_id": _norm(row.get("source_candidate_id")),
                "operation": "SANDBOX_ALIAS_MAPPING_ONLY",
                "alias_label": _norm(row.get("alias_label")),
                "normalized_alias_label": _norm(row.get("normalized_alias_label")),
                "match_label": _norm(row.get("normalized_label")),
                "target_metric": _norm(row.get("target_metric")),
                "proposed_metric_code": _norm(row.get("proposed_metric_code")),
                "proposed_metric_family": _norm(row.get("proposed_metric_family")),
                "canonical_metric_name": _norm(row.get("canonical_metric_name")),
                "confidence": _norm(row.get("confidence")),
                "deterministic_gate_result": _norm(row.get("deterministic_gate_result")),
                "risk_flags": _split_flags(row.get("risk_flags")),
                "provenance": _norm(row.get("provenance")),
            }
        )
    return {
        "stage": "325I",
        "mode": "sandbox_replay_only",
        "official_assets_written": [],
        "confirmed_alias_count": int(len(rule_df)),
        "sandbox_alias_rule_count": int(len(rule_df)),
        "sandbox_scope_rule_count": 0,
        "duplicate_conflict_summary": duplicate_conflict_df.to_dict(orient="records"),
        "alias_rules": rules,
    }


def build_alias_human_confirmed_sandbox_replay_325i(inputs: Dict[str, Any]) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    reviewed_summary = inputs["reviewed_summary"]
    reviewed_qa = inputs["reviewed_qa"]
    schema_summary = inputs["schema_summary"]
    schema_qa = inputs["schema_qa"]
    trust_summary = inputs["trust_summary"]
    post_patch_summary = inputs["post_patch_summary"]
    selected_candidates_df = inputs["selected_candidates_df"]
    confirmed_df = _confirmed_records(inputs["reviewed_plan"])
    rule_df = _build_rule_inventory(confirmed_df, inputs["request_items"])
    duplicate_conflict_df = _build_duplicate_conflict_df(
        rule_df,
        inputs["official_alias_df"],
        inputs["official_scope_df"],
    )
    special_checks_df = _special_check_rows(rule_df)

    readiness_expected = {
        "decision": EXPECTED_325H_DECISION,
        "qa_fail_count": 0,
        "confirmation_record_count": 6,
        "confirmed_count": 6,
        "pending_count": 0,
        "invalid_decision_count": 0,
    }
    for key, expected in readiness_expected.items():
        actual = reviewed_summary.get(key)
        ok = _safe_int(actual) == expected if isinstance(expected, int) else _norm(actual) == expected
        add_qa(f"readiness::325h_{key}", "PASS" if ok else "FAIL", f"expected={expected}; actual={actual}")
    add_qa(
        "readiness::325h_reviewed_qa_json_fail_count",
        "PASS" if _safe_int(reviewed_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(reviewed_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325g_decision",
        "PASS" if _norm(schema_summary.get("decision")) == EXPECTED_325G_DECISION else "FAIL",
        _norm(schema_summary.get("decision")),
    )
    add_qa(
        "readiness::325g_qa_fail_count",
        "PASS" if _safe_int(schema_summary.get("qa_fail_count")) == 0 and _safe_int(schema_qa.get("qa_fail_count")) == 0 else "FAIL",
        f"summary={schema_summary.get('qa_fail_count', '')}; qa={schema_qa.get('qa_fail_count', '')}",
    )
    add_qa(
        "confirmed_aliases::exactly_six_loaded",
        "PASS" if len(confirmed_df) == 6 and len(rule_df) == 6 else "FAIL",
        f"confirmed={len(confirmed_df)} rules={len(rule_df)}",
    )
    add_qa(
        "confirmed_aliases::all_decisions_confirm",
        "PASS" if not confirmed_df.empty and confirmed_df["human_confirmation_decision"].astype(str).eq("CONFIRM").all() else "FAIL",
        "only CONFIRM rows may enter 325I",
    )
    unresolved_target_count = int(rule_df["target_resolved"].astype(bool).eq(False).sum()) if not rule_df.empty else 0
    add_qa(
        "sandbox_rules::all_targets_resolved",
        "PASS" if unresolved_target_count == 0 else "FAIL",
        f"unresolved_target_count={unresolved_target_count}",
    )

    duplicate_count = int(duplicate_conflict_df["duplicate_rule"].astype(bool).sum()) if not duplicate_conflict_df.empty else 0
    target_conflict_count = int(duplicate_conflict_df["target_conflict"].astype(bool).sum()) if not duplicate_conflict_df.empty else 0
    official_overlap_count = int(duplicate_conflict_df["official_alias_overlap"].astype(bool).sum()) if not duplicate_conflict_df.empty else 0
    scope_overlap_count = int(duplicate_conflict_df["official_scope_overlap"].astype(bool).sum()) if not duplicate_conflict_df.empty else 0
    conflict_count = target_conflict_count + official_overlap_count + scope_overlap_count
    adjusted_metric_mismatch_count = int(special_checks_df["adjusted_metric_mismatch"].astype(bool).sum()) if not special_checks_df.empty else 0
    diluted_eps_mismatch_count = int(special_checks_df["diluted_eps_mismatch"].astype(bool).sum()) if not special_checks_df.empty else 0
    special_failure_count = int(special_checks_df["special_check_pass"].astype(bool).eq(False).sum()) if not special_checks_df.empty else 0

    add_qa("sandbox_rules::duplicate_count_zero", "PASS" if duplicate_count == 0 else "FAIL", f"duplicate_count={duplicate_count}")
    add_qa("sandbox_rules::target_conflict_count_zero", "PASS" if target_conflict_count == 0 else "FAIL", f"target_conflict_count={target_conflict_count}")
    add_qa("sandbox_rules::official_alias_overlap_zero", "PASS" if official_overlap_count == 0 else "FAIL", f"official_overlap_count={official_overlap_count}")
    add_qa("sandbox_rules::official_scope_overlap_zero", "PASS" if scope_overlap_count == 0 else "FAIL", f"official_scope_overlap_count={scope_overlap_count}")
    add_qa("sandbox_rules::special_mapping_checks_pass", "PASS" if special_failure_count == 0 else "FAIL", f"special_failure_count={special_failure_count}")
    add_qa("sandbox_rules::adjusted_metric_mismatch_zero", "PASS" if adjusted_metric_mismatch_count == 0 else "FAIL", f"adjusted_metric_mismatch_count={adjusted_metric_mismatch_count}")
    add_qa("sandbox_rules::diluted_eps_mismatch_zero", "PASS" if diluted_eps_mismatch_count == 0 else "FAIL", f"diluted_eps_mismatch_count={diluted_eps_mismatch_count}")
    add_qa("sandbox_replay::selected_candidate_pool_loaded", "PASS" if not selected_candidates_df.empty else "FAIL", f"candidate_count={len(selected_candidates_df)}")

    if not selected_candidates_df.empty and "risk_tags_after" not in selected_candidates_df.columns:
        selected_candidates_df["risk_tags_after"] = selected_candidates_df.get("risk_tags", "")
    if not selected_candidates_df.empty and "decision_after" not in selected_candidates_df.columns:
        selected_candidates_df["decision_after"] = selected_candidates_df.get("split_decision", "")

    applied = apply_human_confirmed_patches(
        accepted_proposals_df=_build_apply_dataframe(rule_df),
        selected_candidates_df=selected_candidates_df.copy(),
    )
    trusted_before_df = applied["trusted_before_df"]
    review_before_df = applied["review_before_df"]
    rejected_before_df = applied["rejected_before_df"]
    trusted_after_df = applied["trusted_after_df"]
    review_after_df = applied["review_after_df"]
    rejected_after_df = applied["rejected_after_df"]
    diff_df = applied["candidate_before_after_diff_df"].copy()
    impact_df = applied["patch_impact_by_proposal_df"].copy()
    remaining_review_burden_df = build_remaining_review_burden(review_after_df)
    core_false_mapping_df = _core_false_mapping_df(diff_df, rule_df)
    core_false_mapping_count = int(len(core_false_mapping_df))

    affected_candidate_count = int(len(diff_df))
    trusted_gain_325i = int(len(trusted_after_df) - len(trusted_before_df))
    review_reduction_325i = int(len(review_before_df) - len(review_after_df))
    out_of_scope_or_rejected_gain_325i = int(len(rejected_after_df) - len(rejected_before_df))
    add_qa(
        "sandbox_replay::candidate_counts_reconcile",
        "PASS" if len(selected_candidates_df) == len(trusted_after_df) + len(review_after_df) + len(rejected_after_df) else "FAIL",
        f"input={len(selected_candidates_df)} after_total={len(trusted_after_df) + len(review_after_df) + len(rejected_after_df)}",
    )
    add_qa(
        "sandbox_replay::trusted_gain_matches_impact",
        "PASS" if trusted_gain_325i == _safe_numeric_sum(impact_df, "trusted_gain") else "FAIL",
        f"summary={trusted_gain_325i}; impact={_safe_numeric_sum(impact_df, 'trusted_gain')}",
    )
    add_qa(
        "sandbox_replay::review_reduction_matches_impact",
        "PASS" if review_reduction_325i == _safe_numeric_sum(impact_df, "review_reduction") else "FAIL",
        f"summary={review_reduction_325i}; impact={_safe_numeric_sum(impact_df, 'review_reduction')}",
    )
    add_qa(
        "sandbox_replay::affected_count_matches_impact",
        "PASS" if affected_candidate_count == _safe_numeric_sum(impact_df, "affected_candidate_count") else "FAIL",
        f"summary={affected_candidate_count}; impact={_safe_numeric_sum(impact_df, 'affected_candidate_count')}",
    )
    trusted_gate_ok = trusted_after_df.apply(_candidate_passes_trust_gate, axis=1).all() if not trusted_after_df.empty else True
    add_qa(
        "sandbox_replay::trusted_after_candidates_pass_gate",
        "PASS" if trusted_gate_ok else "FAIL",
        f"trusted_after_count={len(trusted_after_df)}",
    )
    add_qa(
        "sandbox_replay::core_false_mapping_count_zero",
        "PASS" if core_false_mapping_count == 0 else "FAIL",
        f"core_false_mapping_count={core_false_mapping_count}",
    )
    add_qa(
        "reference::324m_ready_or_warning",
        "PASS" if _norm(post_patch_summary.get("decision")).startswith("POST_PATCH_REGRESSION_VALIDATION_324M_READY") else "WARN",
        _norm(post_patch_summary.get("decision")),
    )
    add_qa("safety::no_llm_or_adjudicator_called", "PASS", "325I uses cached 325H/325G/325E/322B2/324M outputs only.")
    add_qa("safety::no_parser_or_vlm_run", "PASS", "325I does not run MinerU/StructEqTable/Docling/PPStructure/VLM.")
    add_qa("safety::no_official_rule_candidates_created", "PASS", "325I produces sandbox replay artifacts only.")
    add_qa("safety::no_controlled_proposals_created", "PASS", "325I produces no controlled proposal artifacts.")
    add_qa("safety::no_official_patch_applied", "PASS", "325I does not apply patches.")

    official_after = _official_hashes()
    official_assets_modified = inputs["official_hashes_before"] != official_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if not official_assets_modified else "FAIL",
        json.dumps({"before": inputs["official_hashes_before"], "after": official_after}, ensure_ascii=False),
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    decision = NOT_READY_DECISION if qa_fail_count else (READY_WARN_DECISION if qa_warn_count else READY_DECISION)

    before_after_overview_df = pd.DataFrame(
        [
            {"metric": "trusted_total", "before": len(trusted_before_df), "after": len(trusted_after_df), "delta": trusted_gain_325i},
            {"metric": "review_required_total", "before": len(review_before_df), "after": len(review_after_df), "delta": -review_reduction_325i},
            {"metric": "rejected_total", "before": len(rejected_before_df), "after": len(rejected_after_df), "delta": out_of_scope_or_rejected_gain_325i},
            {"metric": "affected_candidate_count", "before": 0, "after": affected_candidate_count, "delta": affected_candidate_count},
        ]
    )

    summary = {
        "stage": "325I",
        "output_dir": "",
        "confirmed_alias_count": int(len(confirmed_df)),
        "sandbox_alias_rule_count": int(len(rule_df)),
        "sandbox_scope_rule_count": 0,
        "affected_candidate_count": affected_candidate_count,
        "trusted_gain_325i": trusted_gain_325i,
        "review_reduction_325i": review_reduction_325i,
        "out_of_scope_or_rejected_gain_325i": out_of_scope_or_rejected_gain_325i,
        "duplicate_count": duplicate_count,
        "conflict_count": conflict_count,
        "target_conflict_count": target_conflict_count,
        "official_overlap_count": official_overlap_count,
        "official_scope_overlap_count": scope_overlap_count,
        "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
        "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
        "core_false_mapping_count": core_false_mapping_count,
        "trusted_total_before_325i": int(len(trusted_before_df)),
        "trusted_total_after_325i": int(len(trusted_after_df)),
        "review_required_total_before_325i": int(len(review_before_df)),
        "review_required_total_after_325i": int(len(review_after_df)),
        "rejected_total_before_325i": int(len(rejected_before_df)),
        "rejected_total_after_325i": int(len(rejected_after_df)),
        "baseline_selected_core_trusted_rate_after_322b2": trust_summary.get("selected_core_trusted_rate_after_322b2", ""),
        "reference_324m_decision": _norm(post_patch_summary.get("decision")),
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "official_asset_hashes_before": inputs["official_hashes_before"],
        "official_asset_hashes_after": official_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_officially_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_proposals_created": False,
        "official_patches_applied": False,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }
    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "sandbox_rules_json": _sandbox_rules_json(rule_df, duplicate_conflict_df),
        "no_apply_proof": {
            "stage": "325I",
            "decision": decision,
            "official_assets_written": [],
            "official_assets_modified": official_assets_modified,
            "llm_or_adjudicator_called": False,
            "semantic_rules_officially_applied": False,
            "trusted_marked_in_production": False,
            "official_rule_candidates_created": False,
            "controlled_proposals_created": False,
            "official_patches_applied": False,
        },
        "confirmed_aliases_df": confirmed_df,
        "sandbox_alias_rules_df": rule_df,
        "duplicate_conflict_df": duplicate_conflict_df,
        "special_checks_df": special_checks_df,
        "before_after_overview_df": before_after_overview_df,
        "affected_candidates_df": diff_df,
        "patch_impact_by_rule_df": impact_df,
        "trusted_after_df": trusted_after_df,
        "review_after_df": review_after_df,
        "rejected_after_df": rejected_after_df,
        "remaining_review_burden_df": remaining_review_burden_df,
        "core_false_mapping_df": core_false_mapping_df,
        "qa_checks_df": qa_df,
    }
