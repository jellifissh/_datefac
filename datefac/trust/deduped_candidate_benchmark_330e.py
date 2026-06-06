from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import build_no_apply_proof


READY_330D_DECISION = "TRUST_ENGINE_ROUTING_POLICY_CALIBRATION_330D_READY_WITH_WARNINGS"
READY_330D_FULL_DECISION = "TRUST_ENGINE_ROUTING_POLICY_CALIBRATION_330D_READY_FOR_330E_UNFAMILIAR_PDF_BENCHMARK_OR_DEDUPED_SCORING"
READY_DECISION = "TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_FOR_330F_UNFAMILIAR_PDF_TRUST_BENCHMARK"
READY_WITH_WARNINGS_DECISION = "TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_WITH_WARNINGS"
NOT_READY_DECISION = "TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_NOT_READY"

DEFAULT_CACHED_CANDIDATE_BENCHMARK_DIR = Path(r"D:\_datefac\output\cached_candidate_trust_scoring_330c")
DEFAULT_ROUTING_POLICY_CALIBRATION_DIR = Path(r"D:\_datefac\output\routing_policy_calibration_330d")
DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\deduped_candidate_trust_benchmark_330e")

PRIMARY_SCORED_RECORDS_JSONL = "cached_candidate_trust_scoring_330c_scored_records.jsonl"
FALLBACK_SCORED_RECORDS_JSONL = "cached_candidate_trust_scoring_330c_benchmark_records.jsonl"


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


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


def _frame_for_output(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


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


def _sha1_json(payload: Mapping[str, Any]) -> str:
    return hashlib.sha1(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _upstream_provenance(row: Mapping[str, Any]) -> Dict[str, Any]:
    provenance = row.get("provenance")
    if not isinstance(provenance, dict):
        return {}
    upstream = provenance.get("upstream_provenance")
    return upstream if isinstance(upstream, dict) else {}


def strict_candidate_key(row: Mapping[str, Any]) -> str:
    candidate_id = _norm_text(row.get("candidate_id"))
    if candidate_id:
        return f"candidate_id::{candidate_id}"

    source_candidate_id = _norm_text(row.get("source_candidate_id"))
    if source_candidate_id:
        return f"source_candidate_id::{source_candidate_id}"

    upstream = _upstream_provenance(row)
    upstream_source_candidate_id = _norm_text(upstream.get("source_candidate_id"))
    if upstream_source_candidate_id:
        return f"upstream_source_candidate_id::{upstream_source_candidate_id}"

    provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
    return "artifact_row::" + _sha1_json(
        {
            "source_artifact": _norm_text(row.get("source_artifact")),
            "source_sheet": _norm_text(row.get("source_sheet")),
            "source_row": _norm_text(row.get("source_row")),
            "source_row_index": _norm_text(provenance.get("source_row_index")),
            "source_table": _norm_text(row.get("source_table")),
        }
    )


def content_fingerprint_key(row: Mapping[str, Any]) -> str:
    return _sha1_json(
        {
            "metric_label_raw": _norm_text(row.get("metric_label_raw")),
            "normalized_metric": _norm_text(row.get("normalized_metric")),
            "value": _norm_text(row.get("value")),
            "unit": _norm_text(row.get("unit")),
            "year": _norm_text(row.get("year")),
            "parser_sources": sorted(_listify_tokens(row.get("parser_sources"))),
            "evidence_refs": sorted(_listify_tokens(row.get("evidence_refs"))),
            "existing_status": _norm_text(row.get("existing_status")),
        }
    )


def cross_artifact_fingerprint_key(row: Mapping[str, Any]) -> str:
    upstream = _upstream_provenance(row)
    source_artifact = _norm_text(row.get("source_artifact"))
    source_sheet = _norm_text(row.get("source_sheet"))
    filtered_refs = [
        token
        for token in _listify_tokens(row.get("evidence_refs"))
        if token not in {source_artifact, source_sheet}
    ]
    return _sha1_json(
        {
            "metric_label_raw": _norm_text(row.get("metric_label_raw")),
            "normalized_metric": _norm_text(row.get("normalized_metric")),
            "value": _norm_text(row.get("value")),
            "unit": _norm_text(row.get("unit")),
            "year": _norm_text(row.get("year")),
            "parser_sources": sorted(_listify_tokens(row.get("parser_sources"))),
            "evidence_refs": sorted(filtered_refs),
            "existing_status": _norm_text(row.get("existing_status")),
            "source_table": _norm_text(row.get("source_table") or upstream.get("table_asset_id")),
            "source_row": _norm_text(row.get("source_row")),
            "source_report_name": _norm_text(upstream.get("source_report_name")),
        }
    )


def _enrich_with_keys(scored_records_df: pd.DataFrame) -> pd.DataFrame:
    working_df = scored_records_df.copy()
    if working_df.empty:
        return working_df
    for column in [
        "candidate_id",
        "source_candidate_id",
        "source_artifact",
        "source_sheet",
        "source_row",
        "source_table",
        "existing_status",
        "routing_decision",
        "confidence_level",
        "score_bucket",
        "risk_flags",
        "warning_risks",
        "parser_sources",
        "evidence_refs",
    ]:
        if column not in working_df.columns:
            working_df[column] = ""
    working_df["strict_candidate_key"] = working_df.apply(lambda row: strict_candidate_key(row.to_dict()), axis=1)
    working_df["content_fingerprint_key"] = working_df.apply(lambda row: content_fingerprint_key(row.to_dict()), axis=1)
    working_df["cross_artifact_fingerprint_key"] = working_df.apply(lambda row: cross_artifact_fingerprint_key(row.to_dict()), axis=1)
    return working_df


def _coverage_from_mask(mask: pd.Series, total_count: int) -> tuple[int, float]:
    count = int(mask.sum())
    rate = round((count / total_count), 6) if total_count > 0 else 0.0
    return count, rate


def _view_metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    if frame.empty:
        return {
            "record_count": 0,
            "confidence_level_distribution": {},
            "routing_decision_distribution": {},
            "risk_flag_distribution": {},
            "score_bucket_distribution": {},
            "source_artifact_distribution": {},
            "potential_false_trusted_count": 0,
            "trusted_with_warning_risk_count": 0,
            "trusted_with_low_evidence_count": 0,
            "missing_evidence_count": 0,
            "target_metric_ambiguous_count": 0,
        }

    potential_false_trusted_mask = (
        (frame["routing_decision"].fillna("").astype(str) == "TRUSTED")
        & (frame["existing_status"].fillna("").astype(str).str.strip() != "")
        & (frame["existing_status"].fillna("").astype(str) != "TRUSTED")
    )
    trusted_with_warning_mask = (
        (frame["routing_decision"].fillna("").astype(str) == "TRUSTED")
        & frame["warning_risks"].apply(lambda value: len(_listify_tokens(value)) > 0)
    )
    trusted_with_low_evidence_mask = (
        (frame["routing_decision"].fillna("").astype(str) == "TRUSTED")
        & (
            (pd.to_numeric(frame["evidence_score"], errors="coerce").fillna(0) < 20)
            | frame["risk_flags"].apply(lambda value: "LOW_EVIDENCE_STRENGTH" in _listify_tokens(value))
        )
    )
    missing_evidence_mask = (
        (pd.to_numeric(frame["evidence_score"], errors="coerce").fillna(0) == 0)
        | frame["evidence_refs"].apply(lambda value: len(_listify_tokens(value)) == 0)
    )
    target_metric_ambiguous_mask = frame["risk_flags"].apply(
        lambda value: "TARGET_METRIC_AMBIGUOUS" in _listify_tokens(value)
    )

    return {
        "record_count": int(len(frame)),
        "confidence_level_distribution": _distribution_from_series(frame["confidence_level"]),
        "routing_decision_distribution": _distribution_from_series(frame["routing_decision"]),
        "risk_flag_distribution": _distribution_from_token_lists(frame["risk_flags"].tolist()),
        "score_bucket_distribution": _distribution_from_series(frame["score_bucket"]),
        "source_artifact_distribution": _distribution_from_series(frame["source_artifact"]),
        "potential_false_trusted_count": int(potential_false_trusted_mask.sum()),
        "trusted_with_warning_risk_count": int(trusted_with_warning_mask.sum()),
        "trusted_with_low_evidence_count": int(trusted_with_low_evidence_mask.sum()),
        "missing_evidence_count": int(missing_evidence_mask.sum()),
        "target_metric_ambiguous_count": int(target_metric_ambiguous_mask.sum()),
    }


def _delta_against_artifact_row(artifact_metrics: Dict[str, Any], other_metrics: Dict[str, Any]) -> Dict[str, int]:
    return {
        "potential_false_trusted_delta": int(other_metrics["potential_false_trusted_count"]) - int(artifact_metrics["potential_false_trusted_count"]),
        "trusted_count_delta": int(other_metrics["routing_decision_distribution"].get("TRUSTED", 0)) - int(artifact_metrics["routing_decision_distribution"].get("TRUSTED", 0)),
        "review_required_count_delta": int(other_metrics["routing_decision_distribution"].get("REVIEW_REQUIRED", 0)) - int(artifact_metrics["routing_decision_distribution"].get("REVIEW_REQUIRED", 0)),
        "target_metric_ambiguous_delta": int(other_metrics["target_metric_ambiguous_count"]) - int(artifact_metrics["target_metric_ambiguous_count"]),
    }


def dedup_reliability_level(*, source_candidate_id_coverage_rate: float, candidate_id_coverage_rate: float, strict_duplicate_rate: float, cross_artifact_duplicate_rate: float) -> str:
    if source_candidate_id_coverage_rate >= 0.5 and candidate_id_coverage_rate >= 0.9:
        return "HIGH"
    if candidate_id_coverage_rate >= 0.9 and strict_duplicate_rate <= 0.02 and cross_artifact_duplicate_rate <= 0.15:
        return "MEDIUM"
    return "LOW"


def recommended_next_step(*, reliability_level: str, policy_calibration_safe_to_continue: bool) -> str:
    if policy_calibration_safe_to_continue and reliability_level in {"HIGH", "MEDIUM"}:
        return "330F_UNFAMILIAR_PDF_TRUST_BENCHMARK"
    return "330D2_STRONGER_CANDIDATE_ID_EXTRACTION"


def build_deduped_candidate_benchmark_330e(
    *,
    cached_candidate_summary: Dict[str, Any],
    cached_candidate_qa: Dict[str, Any],
    routing_policy_summary: Dict[str, Any],
    routing_policy_qa: Dict[str, Any],
    trust_scoring_summary: Dict[str, Any],
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
        "readiness::330d_decision",
        _norm_text(routing_policy_summary.get("decision")) in {READY_330D_DECISION, READY_330D_FULL_DECISION},
        _norm_text(routing_policy_summary.get("decision")),
    )
    add_qa(
        "readiness::330d_qa_fail_count_summary",
        _safe_int(routing_policy_summary.get("qa_fail_count"), 1) == 0,
        str(routing_policy_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330d_qa_fail_count_qa_json",
        _safe_int(routing_policy_qa.get("qa_fail_count"), 1) == 0,
        str(routing_policy_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330d_scored_record_count",
        _safe_int(routing_policy_summary.get("scored_record_count")) == len(scored_records_df) and len(scored_records_df) > 0,
        f"summary={routing_policy_summary.get('scored_record_count', '')}; actual={len(scored_records_df)}",
    )
    add_qa(
        "readiness::330d_artifact_row_benchmark",
        bool(routing_policy_summary.get("artifact_row_benchmark")) is True,
        str(routing_policy_summary.get("artifact_row_benchmark", "")),
    )
    add_qa(
        "readiness::330d_deduped_candidate_benchmark_false",
        bool(routing_policy_summary.get("deduped_candidate_benchmark")) is False,
        str(routing_policy_summary.get("deduped_candidate_benchmark", "")),
    )
    add_qa(
        "safety::330d_production_routing_modified_false",
        bool(routing_policy_summary.get("production_routing_modified")) is False,
        str(routing_policy_summary.get("production_routing_modified", "")),
    )
    add_qa(
        "safety::330d_official_assets_modified_false",
        bool(routing_policy_summary.get("official_assets_modified")) is False,
        str(routing_policy_summary.get("official_assets_modified", "")),
    )
    add_qa(
        "readiness::330c_qa_fail_count",
        _safe_int(cached_candidate_qa.get("qa_fail_count"), 1) == 0,
        str(cached_candidate_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330b_qa_fail_count",
        _safe_int(trust_scoring_summary.get("qa_fail_count"), 1) == 0,
        str(trust_scoring_summary.get("qa_fail_count", "")),
    )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    enriched_df = _enrich_with_keys(scored_records_df)
    artifact_row_view_df = enriched_df.copy()
    strict_deduped_view_df = enriched_df.drop_duplicates("strict_candidate_key", keep="first").copy()
    cross_artifact_deduped_view_df = enriched_df.drop_duplicates("cross_artifact_fingerprint_key", keep="first").copy()

    artifact_metrics = _view_metrics(artifact_row_view_df)
    strict_metrics = _view_metrics(strict_deduped_view_df)
    cross_metrics = _view_metrics(cross_artifact_deduped_view_df)

    artifact_row_count = int(len(artifact_row_view_df))
    strict_deduped_candidate_count = int(len(strict_deduped_view_df))
    cross_artifact_deduped_candidate_count = int(len(cross_artifact_deduped_view_df))
    strict_duplicate_count = artifact_row_count - strict_deduped_candidate_count
    cross_artifact_duplicate_count = artifact_row_count - cross_artifact_deduped_candidate_count

    candidate_id_coverage_count, candidate_id_coverage_rate = _coverage_from_mask(
        enriched_df["candidate_id"].fillna("").astype(str).str.strip().ne(""),
        artifact_row_count,
    )

    source_candidate_id_mask = pd.Series(False, index=enriched_df.index)
    if "source_candidate_id" in enriched_df.columns:
        source_candidate_id_mask = source_candidate_id_mask | enriched_df["source_candidate_id"].fillna("").astype(str).str.strip().ne("")
    source_candidate_id_mask = source_candidate_id_mask | enriched_df["provenance"].apply(
        lambda raw: _norm_text(_upstream_provenance({"provenance": raw}).get("source_candidate_id")) != ""
    )
    source_candidate_id_coverage_count, source_candidate_id_coverage_rate = _coverage_from_mask(
        source_candidate_id_mask,
        artifact_row_count,
    )

    content_fingerprint_coverage_rate = 1.0 if artifact_row_count > 0 else 0.0
    strict_duplicate_rate = round((strict_duplicate_count / artifact_row_count), 6) if artifact_row_count > 0 else 0.0
    cross_artifact_duplicate_rate = round((cross_artifact_duplicate_count / artifact_row_count), 6) if artifact_row_count > 0 else 0.0
    reliability_level = dedup_reliability_level(
        source_candidate_id_coverage_rate=source_candidate_id_coverage_rate,
        candidate_id_coverage_rate=candidate_id_coverage_rate,
        strict_duplicate_rate=strict_duplicate_rate,
        cross_artifact_duplicate_rate=cross_artifact_duplicate_rate,
    )
    policy_calibration_safe_to_continue = reliability_level in {"HIGH", "MEDIUM"}
    next_step = recommended_next_step(
        reliability_level=reliability_level,
        policy_calibration_safe_to_continue=policy_calibration_safe_to_continue,
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330e = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330e",
        no_official_asset_modification_during_330e,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    validated_330d_calibration = qa_fail_count == 0 and _norm_text(routing_policy_summary.get("decision")) == READY_330D_DECISION
    decision = READY_DECISION if policy_calibration_safe_to_continue else READY_WITH_WARNINGS_DECISION
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION

    strict_deltas = _delta_against_artifact_row(artifact_metrics, strict_metrics)
    cross_deltas = _delta_against_artifact_row(artifact_metrics, cross_metrics)

    summary = {
        "stage": "330E",
        "output_dir": str(output_dir),
        "validated_330d_calibration": validated_330d_calibration,
        "artifact_row_benchmark_retained": True,
        "strict_deduped_benchmark_generated": True,
        "cross_artifact_deduped_benchmark_generated": True,
        "artifact_row_count": artifact_row_count,
        "strict_deduped_candidate_count": strict_deduped_candidate_count,
        "cross_artifact_deduped_candidate_count": cross_artifact_deduped_candidate_count,
        "strict_duplicate_count": strict_duplicate_count,
        "cross_artifact_duplicate_count": cross_artifact_duplicate_count,
        "source_candidate_id_coverage_count": source_candidate_id_coverage_count,
        "source_candidate_id_coverage_rate": source_candidate_id_coverage_rate,
        "candidate_id_coverage_count": candidate_id_coverage_count,
        "candidate_id_coverage_rate": candidate_id_coverage_rate,
        "content_fingerprint_coverage_rate": content_fingerprint_coverage_rate,
        "dedup_reliability_level": reliability_level,
        "artifact_row_metrics": artifact_metrics,
        "strict_deduped_metrics": strict_metrics,
        "cross_artifact_deduped_metrics": cross_metrics,
        "strict_deltas_vs_artifact_row": strict_deltas,
        "cross_artifact_deltas_vs_artifact_row": cross_deltas,
        "policy_calibration_safe_to_continue": policy_calibration_safe_to_continue,
        "recommended_next_step": next_step,
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330e": no_official_asset_modification_during_330e,
        "files_written_to_official_assets": [],
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
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
        stage="330E",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    summary_df = _frame_for_output(pd.DataFrame([summary]))
    qa_summary_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "qa_pass_count": qa_pass_count,
                    "qa_fail_count": qa_fail_count,
                    "blocking_reasons": " | ".join(blocking_reasons),
                    "decision": decision,
                }
            ]
        )
    )
    comparison_rows = [
        {
            "benchmark_view": "artifact_row",
            "record_count": artifact_metrics["record_count"],
            "potential_false_trusted_count": artifact_metrics["potential_false_trusted_count"],
            "trusted_with_warning_risk_count": artifact_metrics["trusted_with_warning_risk_count"],
            "trusted_with_low_evidence_count": artifact_metrics["trusted_with_low_evidence_count"],
            "missing_evidence_count": artifact_metrics["missing_evidence_count"],
            "target_metric_ambiguous_count": artifact_metrics["target_metric_ambiguous_count"],
            "trusted_count": artifact_metrics["routing_decision_distribution"].get("TRUSTED", 0),
            "review_required_count": artifact_metrics["routing_decision_distribution"].get("REVIEW_REQUIRED", 0),
        },
        {
            "benchmark_view": "strict_deduped",
            "record_count": strict_metrics["record_count"],
            "potential_false_trusted_count": strict_metrics["potential_false_trusted_count"],
            "trusted_with_warning_risk_count": strict_metrics["trusted_with_warning_risk_count"],
            "trusted_with_low_evidence_count": strict_metrics["trusted_with_low_evidence_count"],
            "missing_evidence_count": strict_metrics["missing_evidence_count"],
            "target_metric_ambiguous_count": strict_metrics["target_metric_ambiguous_count"],
            "trusted_count": strict_metrics["routing_decision_distribution"].get("TRUSTED", 0),
            "review_required_count": strict_metrics["routing_decision_distribution"].get("REVIEW_REQUIRED", 0),
            **strict_deltas,
        },
        {
            "benchmark_view": "cross_artifact_deduped",
            "record_count": cross_metrics["record_count"],
            "potential_false_trusted_count": cross_metrics["potential_false_trusted_count"],
            "trusted_with_warning_risk_count": cross_metrics["trusted_with_warning_risk_count"],
            "trusted_with_low_evidence_count": cross_metrics["trusted_with_low_evidence_count"],
            "missing_evidence_count": cross_metrics["missing_evidence_count"],
            "target_metric_ambiguous_count": cross_metrics["target_metric_ambiguous_count"],
            "trusted_count": cross_metrics["routing_decision_distribution"].get("TRUSTED", 0),
            "review_required_count": cross_metrics["routing_decision_distribution"].get("REVIEW_REQUIRED", 0),
            **cross_deltas,
        },
    ]
    coverage_df = _frame_for_output(
        pd.DataFrame(
            [
                {"metric": "source_candidate_id_coverage_count", "value": source_candidate_id_coverage_count},
                {"metric": "source_candidate_id_coverage_rate", "value": source_candidate_id_coverage_rate},
                {"metric": "candidate_id_coverage_count", "value": candidate_id_coverage_count},
                {"metric": "candidate_id_coverage_rate", "value": candidate_id_coverage_rate},
                {"metric": "content_fingerprint_coverage_rate", "value": content_fingerprint_coverage_rate},
                {"metric": "strict_duplicate_rate", "value": strict_duplicate_rate},
                {"metric": "cross_artifact_duplicate_rate", "value": cross_artifact_duplicate_rate},
                {"metric": "dedup_reliability_level", "value": reliability_level},
            ]
        )
    )
    comparison_df = _frame_for_output(pd.DataFrame(comparison_rows))
    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_330e": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    known_limitations_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "limitation": "no_source_candidate_id_coverage",
                    "detail": "Source candidate id coverage is zero in current cached artifacts, so cross-artifact dedupe still relies on fingerprints.",
                },
                {
                    "limitation": "sidecar_only",
                    "detail": "330E remains a sidecar-only benchmark and does not modify production routing.",
                },
                {
                    "limitation": "fingerprint_collision_risk",
                    "detail": "Fingerprint-based cross-artifact dedupe is stronger than 330D but still heuristic and may over-collapse semantically similar rows.",
                },
            ]
        )
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "summary_df": summary_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "coverage_df": coverage_df,
        "comparison_df": comparison_df,
        "official_asset_proof_df": official_asset_proof_df,
        "known_limitations_df": known_limitations_df,
        "artifact_row_view_df": _frame_for_output(artifact_row_view_df),
        "strict_deduped_view_df": _frame_for_output(strict_deduped_view_df),
        "cross_artifact_deduped_view_df": _frame_for_output(cross_artifact_deduped_view_df),
        "strict_duplicate_rows_df": _frame_for_output(enriched_df.loc[enriched_df.duplicated("strict_candidate_key", keep=False)].copy()),
        "cross_artifact_duplicate_rows_df": _frame_for_output(enriched_df.loc[enriched_df.duplicated("cross_artifact_fingerprint_key", keep=False)].copy()),
    }
