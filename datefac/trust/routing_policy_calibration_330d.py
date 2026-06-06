from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.risk_registry import RISK_REGISTRY, get_risk_definition


READY_330C_DECISION = "TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_READY_FOR_330D_ROUTING_POLICY_CALIBRATION"
READY_WITH_WARNINGS_330C_DECISION = "TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_READY_WITH_WARNINGS"
READY_DECISION = "TRUST_ENGINE_ROUTING_POLICY_CALIBRATION_330D_READY_FOR_330E_UNFAMILIAR_PDF_BENCHMARK_OR_DEDUPED_SCORING"
READY_WITH_WARNINGS_DECISION = "TRUST_ENGINE_ROUTING_POLICY_CALIBRATION_330D_READY_WITH_WARNINGS"
NOT_READY_DECISION = "TRUST_ENGINE_ROUTING_POLICY_CALIBRATION_330D_NOT_READY"

DEFAULT_CACHED_CANDIDATE_BENCHMARK_DIR = Path(r"D:\_datefac\output\cached_candidate_trust_scoring_330c")
DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")
DEFAULT_TRUST_FOUNDATION_DIR = Path(r"D:\_datefac\output\trust_engine_foundation_330a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\routing_policy_calibration_330d")

BENCHMARK_RECORDS_JSONL = "cached_candidate_trust_scoring_330c_benchmark_records.jsonl"

BLOCKING_REVIEW_RISKS = [
    "TARGET_METRIC_AMBIGUOUS",
    "UNIT_CONFLICT",
    "YEAR_MISMATCH",
    "PARSER_CONFLICT",
]
BLOCKING_REJECT_OR_MORE_INFO_RISKS = [
    "VALUE_PARSE_FAILED",
    "OFFICIAL_RULE_CONFLICT",
]
WARNING_REVIEW_RISKS = [
    "UNIT_UNKNOWN",
    "LABEL_AMBIGUOUS",
    "LOW_EVIDENCE_STRENGTH",
    "ALIAS_MAPPING_RISK",
    "ADJUSTED_METRIC_RISK",
    "DILUTED_EPS_RISK",
    "SCOPE_NOISE_RISK",
    "TABLE_STRUCTURE_UNSTABLE",
    "YEAR_MISSING",
]


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_json_loads(value: Any) -> Dict[str, Any]:
    text = _norm_text(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _listify_tokens(value: Any) -> List[str]:
    if value in ("", None):
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    else:
        text = _norm_text(value)
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                items = parsed
            else:
                items = [text]
        else:
            items = [token for token in text.replace("|", ",").replace(";", ",").split(",")]
    ordered: List[str] = []
    seen = set()
    for item in items:
        token = _norm_text(item)
        if token and token not in seen:
            ordered.append(token)
            seen.add(token)
    return ordered


def _distribution_from_series(series: pd.Series) -> Dict[str, int]:
    if series.empty:
        return {}
    counts = series.fillna("").astype(str).value_counts()
    return {str(index): int(value) for index, value in counts.items() if str(index).strip()}


def _distribution_from_token_lists(values: Iterable[Any]) -> Dict[str, int]:
    counter: Dict[str, int] = {}
    for raw in values:
        for token in _listify_tokens(raw):
            counter[token] = counter.get(token, 0) + 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _frame_for_output(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _sha1_json(payload: Mapping[str, Any]) -> str:
    return hashlib.sha1(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _candidate_identity_key(row: Mapping[str, Any]) -> str:
    candidate_id = _norm_text(row.get("candidate_id"))
    if candidate_id:
        return f"candidate_id::{candidate_id}"

    source_candidate_id = _norm_text(row.get("source_candidate_id"))
    if source_candidate_id:
        return f"source_candidate_id::{source_candidate_id}"

    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        upstream = provenance.get("upstream_provenance")
        if isinstance(upstream, dict):
            upstream_source_candidate_id = _norm_text(upstream.get("source_candidate_id"))
            if upstream_source_candidate_id:
                return f"upstream_source_candidate_id::{upstream_source_candidate_id}"

    return "fingerprint::" + _sha1_json(
        {
            "metric_label_raw": _norm_text(row.get("metric_label_raw")),
            "normalized_metric": _norm_text(row.get("normalized_metric")),
            "value": _norm_text(row.get("value")),
            "unit": _norm_text(row.get("unit")),
            "year": _norm_text(row.get("year")),
            "source_table": _norm_text(row.get("source_table")),
            "source_row": _norm_text(row.get("source_row")),
            "source_page": _norm_text(row.get("source_page")),
            "source_dir_name": _norm_text(row.get("source_dir_name")),
        }
    )


def _cross_artifact_row_fingerprint(row: Mapping[str, Any]) -> str:
    provenance = row.get("provenance")
    source_report_name = ""
    if isinstance(provenance, dict):
        upstream = provenance.get("upstream_provenance")
        if isinstance(upstream, dict):
            source_report_name = _norm_text(upstream.get("source_report_name"))
    return _sha1_json(
        {
            "metric_label_raw": _norm_text(row.get("metric_label_raw")),
            "normalized_metric": _norm_text(row.get("normalized_metric")),
            "value": _norm_text(row.get("value")),
            "unit": _norm_text(row.get("unit")),
            "year": _norm_text(row.get("year")),
            "source_table": _norm_text(row.get("source_table")),
            "source_row": _norm_text(row.get("source_row")),
            "source_page": _norm_text(row.get("source_page")),
            "source_report_name": source_report_name,
        }
    )


def build_best_effort_dedupe_view(scored_records_df: pd.DataFrame) -> Dict[str, Any]:
    if scored_records_df.empty:
        empty = pd.DataFrame()
        return {
            "candidate_identity_deduped_df": empty,
            "candidate_identity_duplicates_df": empty,
            "row_fingerprint_duplicates_df": empty,
            "dedupe_summary": {
                "artifact_row_count": 0,
                "deduped_candidate_count": 0,
                "duplicate_artifact_row_count": 0,
                "candidate_id_based_deduped_candidate_count": 0,
                "candidate_id_duplicate_artifact_row_count": 0,
                "cross_artifact_row_fingerprint_unique_count": 0,
                "cross_artifact_row_fingerprint_duplicate_artifact_row_count": 0,
                "deduped_candidate_benchmark": False,
                "best_effort_dedupe_available": False,
                "source_candidate_id_available_count": 0,
                "dedupe_method": "candidate_id_or_source_candidate_id_or_row_fingerprint",
                "dedupe_warning": "No scored records available.",
            },
        }

    working_df = scored_records_df.copy()
    working_df["candidate_identity_key"] = working_df.apply(
        lambda row: _candidate_identity_key(row.to_dict()),
        axis=1,
    )
    working_df["cross_artifact_row_fingerprint"] = working_df.apply(
        lambda row: _cross_artifact_row_fingerprint(row.to_dict()),
        axis=1,
    )

    artifact_row_count = len(working_df)
    candidate_identity_duplicates_mask = working_df.duplicated("candidate_identity_key", keep=False)
    candidate_identity_deduped_df = working_df.drop_duplicates("candidate_identity_key", keep="first").copy()
    candidate_identity_duplicates_df = working_df.loc[candidate_identity_duplicates_mask].copy()

    candidate_id_present_mask = working_df["candidate_id"].fillna("").astype(str).str.strip() != ""
    candidate_id_based_deduped_candidate_count = int(working_df.loc[candidate_id_present_mask, "candidate_id"].nunique())
    candidate_id_duplicate_artifact_row_count = int(candidate_id_present_mask.sum()) - candidate_id_based_deduped_candidate_count

    row_fingerprint_duplicates_mask = working_df.duplicated("cross_artifact_row_fingerprint", keep=False)
    row_fingerprint_duplicates_df = working_df.loc[row_fingerprint_duplicates_mask].copy()
    cross_artifact_row_fingerprint_unique_count = int(working_df["cross_artifact_row_fingerprint"].nunique())
    cross_artifact_row_fingerprint_duplicate_artifact_row_count = artifact_row_count - cross_artifact_row_fingerprint_unique_count

    source_candidate_id_available_count = 0
    if "source_candidate_id" in working_df.columns:
        source_candidate_id_available_count += int(
            working_df["source_candidate_id"].fillna("").astype(str).str.strip().ne("").sum()
        )
    for raw in working_df.get("provenance", pd.Series(dtype=object)):
        if isinstance(raw, dict):
            upstream = raw.get("upstream_provenance")
            if isinstance(upstream, dict) and _norm_text(upstream.get("source_candidate_id")):
                source_candidate_id_available_count += 1

    deduped_candidate_count = len(candidate_identity_deduped_df)
    duplicate_artifact_row_count = artifact_row_count - deduped_candidate_count

    return {
        "candidate_identity_deduped_df": candidate_identity_deduped_df,
        "candidate_identity_duplicates_df": candidate_identity_duplicates_df,
        "row_fingerprint_duplicates_df": row_fingerprint_duplicates_df,
        "dedupe_summary": {
            "artifact_row_count": artifact_row_count,
            "deduped_candidate_count": deduped_candidate_count,
            "duplicate_artifact_row_count": duplicate_artifact_row_count,
            "candidate_id_based_deduped_candidate_count": candidate_id_based_deduped_candidate_count,
            "candidate_id_duplicate_artifact_row_count": candidate_id_duplicate_artifact_row_count,
            "cross_artifact_row_fingerprint_unique_count": cross_artifact_row_fingerprint_unique_count,
            "cross_artifact_row_fingerprint_duplicate_artifact_row_count": cross_artifact_row_fingerprint_duplicate_artifact_row_count,
            "deduped_candidate_benchmark": False,
            "best_effort_dedupe_available": True,
            "source_candidate_id_available_count": source_candidate_id_available_count,
            "dedupe_method": "candidate_id_or_source_candidate_id_or_row_fingerprint",
            "dedupe_warning": (
                "Best-effort dedupe counts are available, but a validated deduped benchmark is not established "
                "because source_candidate_id coverage is sparse and cross-artifact duplicates may still remain."
            ),
        },
    }


def _top_risk_distribution(frame: pd.DataFrame) -> Dict[str, int]:
    if frame.empty or "risk_flags" not in frame.columns:
        return {}
    return _distribution_from_token_lists(frame["risk_flags"].tolist())


def analyze_potential_false_trusted(scored_records_df: pd.DataFrame) -> Dict[str, Any]:
    if scored_records_df.empty:
        empty = pd.DataFrame()
        return {
            "potential_false_trusted_df": empty,
            "summary": {
                "potential_false_trusted_count": 0,
                "existing_status_distribution": {},
                "source_artifact_distribution": {},
                "score_bucket_distribution": {},
                "confidence_level_distribution": {},
                "top_risk_flags": {},
            },
        }

    subset = scored_records_df.loc[
        (scored_records_df["routing_decision"].fillna("").astype(str) == "TRUSTED")
        & (scored_records_df["existing_status"].fillna("").astype(str).str.strip() != "")
        & (scored_records_df["existing_status"].fillna("").astype(str) != "TRUSTED")
    ].copy()

    return {
        "potential_false_trusted_df": subset,
        "summary": {
            "potential_false_trusted_count": int(len(subset)),
            "existing_status_distribution": _distribution_from_series(subset["existing_status"]) if "existing_status" in subset.columns else {},
            "source_artifact_distribution": _distribution_from_series(subset["source_artifact"]) if "source_artifact" in subset.columns else {},
            "score_bucket_distribution": _distribution_from_series(subset["score_bucket"]) if "score_bucket" in subset.columns else {},
            "confidence_level_distribution": _distribution_from_series(subset["confidence_level"]) if "confidence_level" in subset.columns else {},
            "top_risk_flags": _top_risk_distribution(subset),
        },
    }


def analyze_target_metric_ambiguous(scored_records_df: pd.DataFrame) -> Dict[str, Any]:
    if scored_records_df.empty:
        empty = pd.DataFrame()
        return {
            "target_metric_ambiguous_df": empty,
            "summary": {
                "target_metric_ambiguous_count": 0,
                "target_metric_ambiguous_routing_distribution": {},
                "target_metric_ambiguous_score_distribution": {},
                "target_metric_ambiguous_confidence_distribution": {},
                "target_metric_ambiguous_source_artifact_distribution": {},
            },
        }

    subset = scored_records_df.loc[
        scored_records_df["risk_flags"].apply(lambda value: "TARGET_METRIC_AMBIGUOUS" in _listify_tokens(value))
    ].copy()

    return {
        "target_metric_ambiguous_df": subset,
        "summary": {
            "target_metric_ambiguous_count": int(len(subset)),
            "target_metric_ambiguous_routing_distribution": _distribution_from_series(subset["routing_decision"]) if "routing_decision" in subset.columns else {},
            "target_metric_ambiguous_score_distribution": _distribution_from_series(subset["score_bucket"]) if "score_bucket" in subset.columns else {},
            "target_metric_ambiguous_confidence_distribution": _distribution_from_series(subset["confidence_level"]) if "confidence_level" in subset.columns else {},
            "target_metric_ambiguous_source_artifact_distribution": _distribution_from_series(subset["source_artifact"]) if "source_artifact" in subset.columns else {},
        },
    }


def build_policy_proposal(*, scored_record_count: int, potential_false_trusted_count: int, target_metric_ambiguous_count: int) -> Dict[str, Any]:
    return {
        "policy_stage": "330D",
        "policy_proposal_version": "330D_preview_v1",
        "policy_proposal_generated": True,
        "production_apply_allowed": False,
        "recommended_trusted_min_score": 85,
        "recommended_review_min_score": 60,
        "trusted_requirements": {
            "confidence_score_gte": 85,
            "blocking_risk_count_eq": 0,
            "disallowed_risks": [
                "TARGET_METRIC_AMBIGUOUS",
                "VALUE_PARSE_FAILED",
                "OFFICIAL_RULE_CONFLICT",
            ],
            "minimum_evidence_score": 20,
            "minimum_semantic_score": 25,
        },
        "blocking_risk_policy": {
            "default_action": "REVIEW_REQUIRED",
            "review_first_risks": BLOCKING_REVIEW_RISKS,
            "reject_or_needs_more_info_risks": BLOCKING_REJECT_OR_MORE_INFO_RISKS,
        },
        "warning_risk_policy": {
            "default_action": "REVIEW_REQUIRED",
            "warning_risks": WARNING_REVIEW_RISKS,
        },
        "target_metric_ambiguous_policy": {
            "action": "REVIEW_REQUIRED",
            "trusted_allowed": False,
            "reason": "Target metric ambiguity was the dominant blocking risk in 330C benchmark output.",
        },
        "value_parse_failed_policy": {
            "action": "REJECTED_OR_NEEDS_MORE_INFO",
            "trusted_allowed": False,
            "reason": "Value parsing failures invalidate numeric trust and should not auto-route to trusted.",
        },
        "unit_unknown_policy": {
            "action": "REVIEW_REQUIRED",
            "trusted_allowed": False,
            "reason": "Unit ambiguity is warning-level but unsafe for direct trust promotion.",
        },
        "calibration_observations": {
            "scored_record_count": int(scored_record_count),
            "potential_false_trusted_count": int(potential_false_trusted_count),
            "target_metric_ambiguous_count": int(target_metric_ambiguous_count),
        },
        "notes": [
            "This is a sidecar proposal only and must not override production routing in 330D.",
            "330E should benchmark unfamiliar PDFs or validate a stronger deduped candidate identity model before policy promotion.",
        ],
    }


def build_routing_policy_calibration_330d(
    *,
    cached_candidate_summary: Dict[str, Any],
    cached_candidate_qa: Dict[str, Any],
    cached_candidate_no_apply: Dict[str, Any],
    trust_scoring_summary: Dict[str, Any],
    trust_foundation_summary: Dict[str, Any],
    scored_records_df: pd.DataFrame,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(check_name: str, passed: bool, detail: str) -> None:
        qa_rows.append(
            {
                "check_name": check_name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    add_qa(
        "readiness::330c_decision",
        _norm_text(cached_candidate_summary.get("decision")) in {READY_330C_DECISION, READY_WITH_WARNINGS_330C_DECISION},
        _norm_text(cached_candidate_summary.get("decision")),
    )
    add_qa(
        "readiness::330c_qa_fail_count_summary",
        _safe_int(cached_candidate_summary.get("qa_fail_count"), 1) == 0,
        str(cached_candidate_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330c_qa_fail_count_qa_json",
        _safe_int(cached_candidate_qa.get("qa_fail_count"), 1) == 0,
        str(cached_candidate_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330c_fallback_fixture_count",
        _safe_int(cached_candidate_summary.get("fallback_fixture_count"), 1) == 0,
        str(cached_candidate_summary.get("fallback_fixture_count", "")),
    )
    add_qa(
        "readiness::330c_candidate_source_status",
        _norm_text(cached_candidate_summary.get("candidate_source_status")) == "cached_candidates_loaded",
        _norm_text(cached_candidate_summary.get("candidate_source_status")),
    )
    add_qa(
        "readiness::330c_scored_record_count",
        _safe_int(cached_candidate_summary.get("scored_record_count")) > 0 and len(scored_records_df) > 0,
        f"summary={cached_candidate_summary.get('scored_record_count', '')}; actual={len(scored_records_df)}",
    )
    add_qa(
        "readiness::330b_summary_ready",
        bool(trust_scoring_summary) and _safe_int(trust_scoring_summary.get("qa_fail_count"), 1) == 0,
        _norm_text(trust_scoring_summary.get("decision")),
    )
    add_qa(
        "readiness::330a_summary_ready",
        bool(trust_foundation_summary) and _safe_int(trust_foundation_summary.get("qa_fail_count"), 1) == 0,
        _norm_text(trust_foundation_summary.get("decision")),
    )
    add_qa(
        "safety::330c_no_apply_proof",
        bool(cached_candidate_no_apply.get("no_official_asset_modification_during_330c")),
        str(cached_candidate_no_apply.get("no_official_asset_modification_during_330c", "")),
    )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    working_df = scored_records_df.copy()
    if not working_df.empty:
        for column in [
            "candidate_id",
            "existing_status",
            "routing_decision",
            "source_artifact",
            "confidence_level",
            "score_bucket",
        ]:
            if column not in working_df.columns:
                working_df[column] = ""

    dedupe = build_best_effort_dedupe_view(working_df)
    potential_false_trusted = analyze_potential_false_trusted(working_df)
    target_metric_ambiguous = analyze_target_metric_ambiguous(working_df)
    policy_proposal = build_policy_proposal(
        scored_record_count=len(working_df),
        potential_false_trusted_count=potential_false_trusted["summary"]["potential_false_trusted_count"],
        target_metric_ambiguous_count=target_metric_ambiguous["summary"]["target_metric_ambiguous_count"],
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330d = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330d",
        no_official_asset_modification_during_330d,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    validated_330c_benchmark = qa_fail_count == 0 and _norm_text(cached_candidate_summary.get("decision")) == READY_330C_DECISION
    decision = READY_DECISION
    decision_warning = ""
    if not dedupe["dedupe_summary"]["deduped_candidate_benchmark"]:
        decision = READY_WITH_WARNINGS_DECISION
        decision_warning = dedupe["dedupe_summary"]["dedupe_warning"]
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION

    potential_false_trusted_summary = potential_false_trusted["summary"]
    target_metric_ambiguous_summary = target_metric_ambiguous["summary"]
    dedupe_summary = dedupe["dedupe_summary"]

    summary = {
        "stage": "330D",
        "output_dir": str(output_dir),
        "validated_330c_benchmark": validated_330c_benchmark,
        "artifact_row_benchmark": True,
        "deduped_candidate_benchmark": bool(dedupe_summary["deduped_candidate_benchmark"]),
        "scored_record_count": len(working_df),
        "artifact_row_count": dedupe_summary["artifact_row_count"],
        "deduped_candidate_count": dedupe_summary["deduped_candidate_count"],
        "duplicate_artifact_row_count": dedupe_summary["duplicate_artifact_row_count"],
        "candidate_id_based_deduped_candidate_count": dedupe_summary["candidate_id_based_deduped_candidate_count"],
        "candidate_id_duplicate_artifact_row_count": dedupe_summary["candidate_id_duplicate_artifact_row_count"],
        "cross_artifact_row_fingerprint_unique_count": dedupe_summary["cross_artifact_row_fingerprint_unique_count"],
        "cross_artifact_row_fingerprint_duplicate_artifact_row_count": dedupe_summary["cross_artifact_row_fingerprint_duplicate_artifact_row_count"],
        "best_effort_dedupe_available": dedupe_summary["best_effort_dedupe_available"],
        "source_candidate_id_available_count": dedupe_summary["source_candidate_id_available_count"],
        "dedupe_method": dedupe_summary["dedupe_method"],
        "dedupe_warning": dedupe_summary["dedupe_warning"],
        "potential_false_trusted_count": potential_false_trusted_summary["potential_false_trusted_count"],
        "potential_false_trusted_top_risk_flags": potential_false_trusted_summary["top_risk_flags"],
        "potential_false_trusted_source_artifact_distribution": potential_false_trusted_summary["source_artifact_distribution"],
        "potential_false_trusted_score_distribution": potential_false_trusted_summary["score_bucket_distribution"],
        "target_metric_ambiguous_count": target_metric_ambiguous_summary["target_metric_ambiguous_count"],
        "target_metric_ambiguous_routing_distribution": target_metric_ambiguous_summary["target_metric_ambiguous_routing_distribution"],
        "target_metric_ambiguous_score_distribution": target_metric_ambiguous_summary["target_metric_ambiguous_score_distribution"],
        "policy_proposal_generated": True,
        "recommended_trusted_min_score": policy_proposal["recommended_trusted_min_score"],
        "recommended_review_min_score": policy_proposal["recommended_review_min_score"],
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330d": no_official_asset_modification_during_330d,
        "files_written_to_official_assets": [],
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision_warning": decision_warning,
        "decision": decision,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="330D",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    policy_rows = []
    for key, value in policy_proposal.items():
        policy_rows.append(
            {
                "policy_field": key,
                "policy_value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value,
            }
        )

    risk_registry_rows = []
    for risk_code, definition in RISK_REGISTRY.items():
        risk_registry_rows.append(
            {
                "risk_code": risk_code,
                "severity": definition.severity,
                "blocking": definition.blocking,
                "description": definition.description,
                "recommended_action": definition.recommended_action,
            }
        )

    dedupe_summary_df = _frame_for_output(pd.DataFrame(
        [{"metric": key, "value": value} for key, value in dedupe_summary.items()]
    ))
    potential_false_trusted_distribution_df = _frame_for_output(pd.DataFrame(
        [{"metric": key, "count": value} for key, value in potential_false_trusted_summary["top_risk_flags"].items()]
    ))
    target_metric_ambiguous_distribution_df = _frame_for_output(pd.DataFrame(
        [
            {"distribution_kind": "routing_decision", "bucket": key, "count": value}
            for key, value in target_metric_ambiguous_summary["target_metric_ambiguous_routing_distribution"].items()
        ]
        + [
            {"distribution_kind": "score_bucket", "bucket": key, "count": value}
            for key, value in target_metric_ambiguous_summary["target_metric_ambiguous_score_distribution"].items()
        ]
        + [
            {"distribution_kind": "confidence_level", "bucket": key, "count": value}
            for key, value in target_metric_ambiguous_summary["target_metric_ambiguous_confidence_distribution"].items()
        ]
    ))
    official_asset_proof_df = _frame_for_output(pd.DataFrame(
        [
            {
                "asset_path": asset_path,
                "hash_before": before_hash,
                "hash_after": official_assets_after.get(asset_path, ""),
                "modified_during_330d": before_hash != official_assets_after.get(asset_path, ""),
            }
            for asset_path, before_hash in official_assets_before.items()
        ]
    ))

    summary_df = _frame_for_output(pd.DataFrame([summary]))
    qa_summary_df = _frame_for_output(pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": decision,
            }
        ]
    ))
    known_limitations_df = _frame_for_output(pd.DataFrame(
        [
            {
                "limitation": "artifact_row_benchmark_only",
                "detail": "330D calibrates against 330C artifact rows and does not validate a canonical deduped candidate benchmark.",
            },
            {
                "limitation": "best_effort_dedupe",
                "detail": dedupe_summary["dedupe_warning"],
            },
            {
                "limitation": "no_production_apply",
                "detail": "330D produces a sidecar policy proposal only and does not modify production routing.",
            },
        ]
    ))

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "policy_proposal_json": policy_proposal,
        "summary_df": summary_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "policy_preview_df": _frame_for_output(pd.DataFrame(policy_rows)),
        "official_asset_proof_df": official_asset_proof_df,
        "dedupe_summary_df": dedupe_summary_df,
        "potential_false_trusted_df": _frame_for_output(potential_false_trusted["potential_false_trusted_df"]),
        "potential_false_trusted_distribution_df": potential_false_trusted_distribution_df,
        "target_metric_ambiguous_df": _frame_for_output(target_metric_ambiguous["target_metric_ambiguous_df"]),
        "target_metric_ambiguous_distribution_df": target_metric_ambiguous_distribution_df,
        "candidate_identity_duplicates_df": _frame_for_output(dedupe["candidate_identity_duplicates_df"]),
        "row_fingerprint_duplicates_df": _frame_for_output(dedupe["row_fingerprint_duplicates_df"]),
        "risk_registry_df": _frame_for_output(pd.DataFrame(risk_registry_rows)),
        "known_limitations_df": known_limitations_df,
    }
