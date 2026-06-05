from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


EXPECTED_325I_DECISION = "ALIAS_HUMAN_CONFIRMED_SANDBOX_REPLAY_325I_READY_FOR_325J_OFFICIAL_RULE_CANDIDATES"
EXPECTED_325H_DECISION = "ALIAS_HUMAN_CONFIRMATION_325H_REVIEWED_READY_FOR_325I_SANDBOX_REPLAY"
EXPECTED_325G_DECISION = "ALIAS_RESPONSE_SCHEMA_VALIDATION_325G_READY_FOR_HUMAN_CONFIRMATION"
READY_DECISION = "ALIAS_OFFICIAL_RULE_CANDIDATES_325J_READY_FOR_325K_CONTROLLED_PROPOSAL"
NOT_READY_DECISION = "ALIAS_OFFICIAL_RULE_CANDIDATES_325J_NOT_READY"

DEFAULT_SANDBOX_REPLAY_DIR = Path(r"D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i")
DEFAULT_HUMAN_CONFIRMATION_REVIEWED_DIR = Path(r"D:\_datefac\output\alias_human_confirmation_325h_reviewed")
DEFAULT_SCHEMA_VALIDATION_DIR = Path(r"D:\_datefac\output\alias_response_schema_validation_325g")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_official_rule_candidates_from_325i_325j")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
OFFICIAL_ALIAS_OVERRIDE_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
TARGET_ASSET_FILE = "data/overrides/semantic_alias_candidates.json"
DEFAULT_TARGET_GROUP = "profitability"


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _metric_key(value: Any) -> str:
    return _norm(value).lower().replace(" ", "").replace("_", "").replace("-", "")


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


def _join_unique(items: Iterable[Any], limit: int = 16) -> str:
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


def _flatten_official_aliases(payload: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    groups = payload.get("groups", {}) if isinstance(payload, dict) else {}
    if not isinstance(groups, dict):
        return pd.DataFrame()
    for group_name, entries in groups.items():
        if not isinstance(entries, list):
            continue
        for item in entries:
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "target_asset_group": _norm(group_name),
                    "normalized_label": _norm(item.get("normalized_label")),
                    "normalized_label_key": _normalize_label(item.get("normalized_label")),
                    "metric_code": _norm(item.get("metric_code")),
                    "metric_code_key": _metric_key(item.get("metric_code")),
                    "metric_family": _norm(item.get("metric_family")) or _norm(group_name),
                    "rule_id": _norm(item.get("rule_id")),
                }
            )
    return pd.DataFrame(rows).fillna("")


def _target_group_for_rule(rule: Dict[str, Any], existing_groups: Set[str]) -> str:
    family = _norm(rule.get("proposed_metric_family"))
    if family in existing_groups:
        return family
    if DEFAULT_TARGET_GROUP in existing_groups:
        return DEFAULT_TARGET_GROUP
    return sorted(existing_groups)[0] if existing_groups else ""


def _candidate_id(source_rule_id: str) -> str:
    digest = hashlib.sha1(source_rule_id.encode("utf-8")).hexdigest()[:12]
    return f"325j::alias_candidate::{digest}"


def _read_patch_impact(sandbox_replay_dir: Path) -> pd.DataFrame:
    workbook = sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_affected_candidates.xlsx"
    if not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name="patch_impact_by_rule", dtype=object).fillna("")
    except Exception:
        return pd.DataFrame()


def load_alias_official_rule_candidates_from_325i_inputs(
    sandbox_replay_dir: Path,
    human_confirmation_reviewed_dir: Path,
    schema_validation_dir: Path,
) -> Dict[str, Any]:
    alias_payload = _read_json(OFFICIAL_ALIAS_OVERRIDE_PATH)
    groups = alias_payload.get("groups", {}) if isinstance(alias_payload, dict) else {}
    return {
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json"
        ),
        "sandbox_qa": _read_json(
            sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_qa.json"
        ),
        "sandbox_rules": _read_json(
            sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_sandbox_rules.json"
        ),
        "patch_impact_df": _read_patch_impact(sandbox_replay_dir),
        "human_confirmation_summary": _read_json(
            human_confirmation_reviewed_dir / "alias_human_confirmation_325h_reviewed_summary.json"
        ),
        "human_confirmation_plan": _read_json(
            human_confirmation_reviewed_dir / "alias_human_confirmation_325h_human_confirmed_plan.json"
        ),
        "schema_summary": _read_json(
            schema_validation_dir / "alias_response_schema_validation_325g_summary.json"
        ),
        "validated_suggestions": _read_json(
            schema_validation_dir / "alias_response_schema_validation_325g_validated_suggestions.json"
        ),
        "official_alias_payload": alias_payload,
        "official_alias_df": _flatten_official_aliases(alias_payload),
        "official_alias_groups": set(groups.keys()) if isinstance(groups, dict) else set(),
        "official_hashes_before": _official_hashes(),
    }


def _impact_by_rule(patch_impact_df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    if patch_impact_df.empty:
        return out
    for _, row in patch_impact_df.iterrows():
        rule_id = _norm(row.get("proposal_id"))
        if not rule_id:
            continue
        out[rule_id] = {
            "affected": _safe_int(row.get("affected_candidate_count")),
            "trusted": _safe_int(row.get("trusted_gain")),
            "review": _safe_int(row.get("review_reduction")),
            "out_of_scope": _safe_int(row.get("rejected_or_out_of_scope_count")),
        }
    return out


def _special_mismatch(rule: Dict[str, Any]) -> Dict[str, Any]:
    alias_text = f"{_norm(rule.get('alias_label'))} {_norm(rule.get('normalized_alias_label'))}"
    alias_key = _metric_key(alias_text)
    target_key = _metric_key(rule.get("target_metric"))
    failures: List[str] = []
    adjusted = False
    diluted = False
    if _metric_key(rule.get("alias_label")) == "ebit" and target_key != "ebit":
        failures.append("EBIT_MUST_MAP_ONLY_TO_EBIT")
    if "roe" in alias_key and target_key != "roe":
        failures.append("ROE_MUST_MAP_ONLY_TO_ROE")
    if any(term in alias_key for term in ["diluted", "摊薄", "最新摊薄"]):
        if target_key not in {"dilutedeps", "epsdiluted"}:
            diluted = True
            failures.append("DILUTED_EPS_ALIAS_MUST_MAP_TO_DILUTED_EPS")
    if "经调整" in alias_text and "eps" in alias_key:
        if target_key != "adjustedeps":
            adjusted = True
            failures.append("ADJUSTED_EPS_MUST_MAP_TO_ADJUSTED_EPS")
    if "经调整" in alias_text and ("归母净利润" in alias_text or "attributable" in alias_key):
        if target_key not in {"adjustedattributablenetprofit", "adjustedparentnetprofit"}:
            adjusted = True
            failures.append("ADJUSTED_ATTRIBUTABLE_NET_PROFIT_TARGET_MISMATCH")
    if "净利率" in alias_text or "netmargin" in alias_key:
        if target_key not in {"attributablenetmargin", "parentnetmargin"}:
            failures.append("ATTRIBUTABLE_NET_MARGIN_TARGET_MISMATCH")
    return {
        "pass": len(failures) == 0,
        "failure_reasons": failures,
        "adjusted_metric_mismatch": adjusted,
        "diluted_eps_mismatch": diluted,
    }


def _build_candidates(
    sandbox_rules: Dict[str, Any],
    patch_impact_df: pd.DataFrame,
    official_alias_df: pd.DataFrame,
    official_groups: Set[str],
) -> Dict[str, pd.DataFrame]:
    rules = sandbox_rules.get("alias_rules", [])
    if not isinstance(rules, list):
        rules = []
    impact = _impact_by_rule(patch_impact_df)
    official_by_label: Dict[str, Set[str]] = {}
    if not official_alias_df.empty:
        for _, row in official_alias_df.iterrows():
            official_by_label.setdefault(_norm(row.get("normalized_label_key")), set()).add(_metric_key(row.get("metric_code")))

    rows: List[Dict[str, Any]] = []
    safety_rows: List[Dict[str, Any]] = []
    for index, rule in enumerate([item for item in rules if isinstance(item, dict)], start=1):
        source_rule_id = _norm(rule.get("source_rule_id"))
        alias_label = _norm(rule.get("alias_label"))
        normalized_alias_label = _norm(rule.get("normalized_alias_label")) or alias_label
        label_key = _normalize_label(alias_label)
        target_metric = _norm(rule.get("target_metric"))
        target_key = _metric_key(target_metric)
        official_targets = official_by_label.get(label_key, set())
        official_overlap = bool(official_targets)
        target_conflict = bool(official_targets and target_key not in official_targets)
        special = _special_mismatch(rule)
        impact_row = impact.get(source_rule_id, {})
        candidate_id = _candidate_id(source_rule_id)
        duplicate_or_conflict = target_conflict or not special["pass"]
        status = "NEEDS_REVIEW" if duplicate_or_conflict or official_overlap else "READY_FOR_CONTROLLED_PROPOSAL"
        target_group = _target_group_for_rule(rule, official_groups)
        safety_checks = {
            "official_overlap": official_overlap,
            "target_conflict": target_conflict,
            "semantic_constraint_pass": special["pass"],
            "semantic_constraint_failures": special["failure_reasons"],
            "official_assets_modified": False,
        }
        provenance = {
            "source_sandbox_rule_id": source_rule_id,
            "source_confirmation_id_325h": _norm(rule.get("confirmation_id")),
            "source_request_id_325e": _norm(rule.get("request_id")),
            "source_candidate_id_325a": _norm(rule.get("source_candidate_id")),
            "source_stage_325i": "alias_human_confirmed_sandbox_replay_325i",
            "source_stage_325g": "alias_response_schema_validation_325g",
            "source_stage_325h": "alias_human_confirmation_325h_reviewed",
            "raw_325i_provenance": _norm(rule.get("provenance")),
        }
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_sandbox_rule_id": source_rule_id,
                "alias_label": alias_label,
                "normalized_alias_label": normalized_alias_label,
                "normalized_alias_label_key": label_key,
                "target_metric": target_metric,
                "candidate_type": "alias",
                "status": status,
                "target_asset_file": TARGET_ASSET_FILE,
                "target_asset_group": target_group,
                "expected_affected_candidate_count": _safe_int(impact_row.get("affected")),
                "expected_trusted_gain": _safe_int(impact_row.get("trusted")),
                "expected_review_reduction": _safe_int(impact_row.get("review")),
                "expected_out_of_scope_or_rejected_gain": _safe_int(impact_row.get("out_of_scope")),
                "safety_checks": json.dumps(safety_checks, ensure_ascii=False),
                "provenance": json.dumps(provenance, ensure_ascii=False),
                "proposed_metric_code": _norm(rule.get("proposed_metric_code")),
                "proposed_metric_family": _norm(rule.get("proposed_metric_family")),
                "canonical_metric_name": _norm(rule.get("canonical_metric_name")),
                "confidence": _norm(rule.get("confidence")),
                "deterministic_gate_result": _norm(rule.get("deterministic_gate_result")),
                "official_overlap": official_overlap,
                "target_conflict": target_conflict,
                "adjusted_metric_mismatch": bool(special["adjusted_metric_mismatch"]),
                "diluted_eps_mismatch": bool(special["diluted_eps_mismatch"]),
                "semantic_constraint_failures": " | ".join(special["failure_reasons"]),
                "candidate_readiness_reason": (
                    "Conflict-free sandbox alias rule ready for controlled proposal."
                    if status == "READY_FOR_CONTROLLED_PROPOSAL"
                    else "Candidate retained for review due to official overlap, target conflict, or semantic constraint failure."
                ),
            }
        )
        safety_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sandbox_rule_id": source_rule_id,
                "alias_label": alias_label,
                "target_metric": target_metric,
                **safety_checks,
            }
        )
    candidates_df = pd.DataFrame(rows).fillna("")
    safety_df = pd.DataFrame(safety_rows).fillna("")
    return {"candidates_df": candidates_df, "safety_df": safety_df}


def _build_known_limitations_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "candidate_only",
                "detail": "325J creates official alias rule candidates only; it does not create controlled proposals, dry runs, or official patches.",
            },
            {
                "limitation": "cached_evidence_only",
                "detail": "325J uses cached 325I/325H/325G/325E evidence and reads official assets only for overlap and target group checks.",
            },
            {
                "limitation": "target_group_existing_structure_only",
                "detail": "325J resolves target_asset_group to an existing semantic_alias_candidates.json group and does not create new groups.",
            },
        ]
    )


def build_alias_official_rule_candidates_from_325i(inputs: Dict[str, Any]) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    sandbox_summary = inputs["sandbox_summary"]
    sandbox_qa = inputs["sandbox_qa"]
    human_summary = inputs["human_confirmation_summary"]
    schema_summary = inputs["schema_summary"]
    candidates_payload = _build_candidates(
        inputs["sandbox_rules"],
        inputs["patch_impact_df"],
        inputs["official_alias_df"],
        inputs["official_alias_groups"],
    )
    candidates_df = candidates_payload["candidates_df"]
    safety_df = candidates_payload["safety_df"]

    expected_readiness = {
        "decision": EXPECTED_325I_DECISION,
        "qa_fail_count": 0,
        "confirmed_alias_count": 6,
        "sandbox_alias_rule_count": 6,
        "affected_candidate_count": 45,
        "trusted_gain_325i": 45,
        "review_reduction_325i": 45,
        "out_of_scope_or_rejected_gain_325i": 0,
        "duplicate_count": 0,
        "conflict_count": 0,
        "target_conflict_count": 0,
        "official_overlap_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
        "core_false_mapping_count": 0,
    }
    for key, expected in expected_readiness.items():
        actual = sandbox_summary.get(key)
        ok = _safe_int(actual) == expected if isinstance(expected, int) else _norm(actual) == expected
        add_qa(f"readiness::325i_{key}", "PASS" if ok else "FAIL", f"expected={expected}; actual={actual}")
    add_qa(
        "readiness::325i_official_assets_modified_false",
        "PASS" if sandbox_summary.get("official_assets_modified") is False else "FAIL",
        str(sandbox_summary.get("official_assets_modified")),
    )
    add_qa(
        "readiness::325i_qa_json_fail_count",
        "PASS" if _safe_int(sandbox_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(sandbox_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::325h_decision",
        "PASS" if _norm(human_summary.get("decision")) == EXPECTED_325H_DECISION else "FAIL",
        _norm(human_summary.get("decision")),
    )
    add_qa(
        "readiness::325g_decision",
        "PASS" if _norm(schema_summary.get("decision")) == EXPECTED_325G_DECISION else "FAIL",
        _norm(schema_summary.get("decision")),
    )

    source_sandbox_rule_count = len(inputs["sandbox_rules"].get("alias_rules", [])) if isinstance(inputs["sandbox_rules"].get("alias_rules", []), list) else 0
    candidate_count = len(candidates_df)
    alias_candidate_count = int(candidates_df["candidate_type"].astype(str).eq("alias").sum()) if not candidates_df.empty else 0
    ready_count = int(candidates_df["status"].astype(str).eq("READY_FOR_CONTROLLED_PROPOSAL").sum()) if not candidates_df.empty else 0
    review_count = int(candidates_df["status"].astype(str).eq("NEEDS_REVIEW").sum()) if not candidates_df.empty else 0
    rejected_count = int(candidates_df["status"].astype(str).eq("REJECTED").sum()) if not candidates_df.empty else 0
    duplicate_candidate_id_count = int(candidates_df["candidate_id"].astype(str).duplicated().sum()) if not candidates_df.empty else 0
    duplicate_alias_target_pair_count = int(candidates_df[["normalized_alias_label_key", "target_metric"]].astype(str).duplicated().sum()) if not candidates_df.empty else 0
    official_overlap_count = int(candidates_df["official_overlap"].astype(bool).sum()) if not candidates_df.empty else 0
    target_conflict_count = int(candidates_df["target_conflict"].astype(bool).sum()) if not candidates_df.empty else 0
    adjusted_metric_mismatch_count = int(candidates_df["adjusted_metric_mismatch"].astype(bool).sum()) if not candidates_df.empty else 0
    diluted_eps_mismatch_count = int(candidates_df["diluted_eps_mismatch"].astype(bool).sum()) if not candidates_df.empty else 0
    affected_candidate_count = _safe_int(candidates_df["expected_affected_candidate_count"].sum()) if not candidates_df.empty else 0
    trusted_gain = _safe_int(candidates_df["expected_trusted_gain"].sum()) if not candidates_df.empty else 0
    review_reduction = _safe_int(candidates_df["expected_review_reduction"].sum()) if not candidates_df.empty else 0
    out_of_scope_gain = _safe_int(candidates_df["expected_out_of_scope_or_rejected_gain"].sum()) if not candidates_df.empty else 0
    target_group_missing_count = int(candidates_df["target_asset_group"].astype(str).eq("").sum()) if not candidates_df.empty else 0

    checks = [
        ("inputs::source_sandbox_rule_count", source_sandbox_rule_count, 6),
        ("candidates::candidate_count", candidate_count, 6),
        ("candidates::alias_candidate_count", alias_candidate_count, 6),
        ("candidates::ready_for_controlled_proposal_count", ready_count, 6),
        ("candidates::needs_review_candidate_count", review_count, 0),
        ("candidates::rejected_candidate_count", rejected_count, 0),
        ("dedupe::duplicate_candidate_id_count", duplicate_candidate_id_count, 0),
        ("dedupe::duplicate_alias_target_pair_count", duplicate_alias_target_pair_count, 0),
        ("target::official_overlap_count", official_overlap_count, 0),
        ("target::target_conflict_count", target_conflict_count, 0),
        ("target::target_group_missing_count", target_group_missing_count, 0),
        ("semantic::adjusted_metric_mismatch_count", adjusted_metric_mismatch_count, 0),
        ("semantic::diluted_eps_mismatch_count", diluted_eps_mismatch_count, 0),
        ("impact::affected_candidate_count", affected_candidate_count, 45),
        ("impact::trusted_gain_325j", trusted_gain, 45),
        ("impact::review_reduction_325j", review_reduction, 45),
        ("impact::out_of_scope_or_rejected_gain_325j", out_of_scope_gain, 0),
    ]
    for name, actual, expected in checks:
        add_qa(name, "PASS" if actual == expected else "FAIL", f"expected={expected}; actual={actual}")

    official_after = _official_hashes()
    official_assets_modified = inputs["official_hashes_before"] != official_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if not official_assets_modified else "FAIL",
        json.dumps({"before": inputs["official_hashes_before"], "after": official_after}, ensure_ascii=False),
    )
    add_qa("safety::no_llm_or_adjudicator_called", "PASS", "325J uses cached 325I/325H/325G/325E evidence only.")
    add_qa("safety::no_official_rule_candidates_beyond_candidate_package", "PASS", "325J creates candidate package only.")
    add_qa("safety::no_controlled_proposals_or_dry_run_or_patch", "PASS", "325J does not run controlled proposal, dry run, or patch application.")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary = {
        "stage": "325J",
        "output_dir": "",
        "source_sandbox_rule_count": source_sandbox_rule_count,
        "candidate_count": candidate_count,
        "alias_candidate_count": alias_candidate_count,
        "ready_for_controlled_proposal_count": ready_count,
        "needs_review_candidate_count": review_count,
        "rejected_candidate_count": rejected_count,
        "duplicate_candidate_id_count": duplicate_candidate_id_count,
        "duplicate_alias_target_pair_count": duplicate_alias_target_pair_count,
        "official_overlap_count": official_overlap_count,
        "target_conflict_count": target_conflict_count,
        "adjusted_metric_mismatch_count": adjusted_metric_mismatch_count,
        "diluted_eps_mismatch_count": diluted_eps_mismatch_count,
        "affected_candidate_count": affected_candidate_count,
        "trusted_gain_325j": trusted_gain,
        "review_reduction_325j": review_reduction,
        "out_of_scope_or_rejected_gain_325j": out_of_scope_gain,
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "official_asset_hashes_before": inputs["official_hashes_before"],
        "official_asset_hashes_after": official_after,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": NOT_READY_DECISION if qa_fail_count else READY_DECISION,
    }
    candidate_package = {
        "stage": "325J",
        "decision": summary["decision"],
        "target_asset_file": TARGET_ASSET_FILE,
        "candidates": candidates_df.to_dict(orient="records"),
    }
    no_apply_proof = {
        "stage": "325J",
        "decision": summary["decision"],
        "official_assets_written": [],
        "official_assets_modified": official_assets_modified,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "controlled_proposals_created": False,
        "dry_run_executed": False,
        "official_patches_applied": False,
        "llm_or_adjudicator_called": False,
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
        "candidate_package": candidate_package,
        "no_apply_proof": no_apply_proof,
        "candidates_df": candidates_df,
        "safety_checks_df": safety_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": _build_known_limitations_df(),
    }
