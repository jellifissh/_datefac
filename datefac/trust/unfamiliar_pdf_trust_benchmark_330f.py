from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.cached_candidate_benchmark_330c import load_cached_candidate_like_rows, score_bucket_label
from datefac.trust.confidence_scoring import score_trust_record
from datefac.trust.deduped_candidate_benchmark_330e import (
    cross_artifact_fingerprint_key,
    strict_candidate_key,
)
from datefac.trust.no_apply_proof import build_no_apply_proof


READY_330E_DECISION = "TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_FOR_330F_UNFAMILIAR_PDF_TRUST_BENCHMARK"
READY_WITH_WARNINGS_330E_DECISION = "TRUST_ENGINE_DEDUPED_CANDIDATE_BENCHMARK_330E_READY_WITH_WARNINGS"
READY_DECISION = "TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT"
WAITING_DECISION = "TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_WAITING_FOR_UNFAMILIAR_OUTPUTS"
READY_WITH_WARNINGS_DECISION = "TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_WITH_WARNINGS"
NOT_READY_DECISION = "TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_NOT_READY"

DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR = Path(r"D:\_datefac\output\deduped_candidate_trust_benchmark_330e")
DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f")
DEFAULT_UNFAMILIAR_SOURCE_DIRS = [
    Path(r"D:\_datefac\output\unfamiliar_pdf_outputs"),
    Path(r"D:\_datefac\output\unfamiliar_trust_split"),
    Path(r"D:\_datefac\output\mineru_unfamiliar_benchmark"),
    Path(r"D:\_datefac\output\delivery_benchmark_unfamiliar"),
]


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


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


def _upstream_provenance(row: Mapping[str, Any]) -> Dict[str, Any]:
    provenance = row.get("provenance")
    if not isinstance(provenance, dict):
        return {}
    upstream = provenance.get("upstream_provenance")
    return upstream if isinstance(upstream, dict) else {}


def _source_pdf_name(row: Mapping[str, Any]) -> str:
    upstream = _upstream_provenance(row)
    for key in ["source_report_name", "source_doc_name", "content_source_file"]:
        value = _norm_text(upstream.get(key))
        if value:
            return value
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        value = _norm_text(provenance.get("source_artifact_path"))
        if value:
            return Path(value).stem
    return ""


def _existing_status_distribution(frame: pd.DataFrame) -> Dict[str, int]:
    if frame.empty or "existing_status" not in frame.columns:
        return {}
    values = frame["existing_status"].fillna("").astype(str)
    non_empty = values[values.str.strip() != ""]
    return _distribution_from_series(non_empty)


def _sidecar_vs_existing(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    if frame.empty or "existing_status" not in frame.columns or "routing_decision" not in frame.columns:
        return []
    working = frame.copy()
    working["existing_status"] = working["existing_status"].fillna("").astype(str)
    working = working.loc[working["existing_status"].str.strip() != ""]
    if working.empty:
        return []
    pair_counts = working.groupby(["existing_status", "routing_decision"]).size().reset_index(name="count")
    return pair_counts.to_dict(orient="records")


def _view_metrics(frame: pd.DataFrame) -> Dict[str, Any]:
    if frame.empty:
        return {
            "record_count": 0,
            "confidence_level_distribution": {},
            "routing_decision_distribution": {},
            "risk_flag_distribution": {},
            "score_bucket_distribution": {},
            "source_artifact_distribution": {},
            "source_pdf_distribution": {},
            "existing_status_distribution": {},
            "sidecar_vs_existing_status_comparison": [],
            "potential_false_trusted_count": 0,
            "trusted_with_warning_risk_count": 0,
            "trusted_with_low_evidence_count": 0,
            "missing_evidence_count": 0,
            "target_metric_ambiguous_count": 0,
            "value_parse_failed_count": 0,
            "unit_unknown_count": 0,
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
    value_parse_failed_mask = frame["risk_flags"].apply(
        lambda value: "VALUE_PARSE_FAILED" in _listify_tokens(value)
    )
    unit_unknown_mask = frame["risk_flags"].apply(
        lambda value: "UNIT_UNKNOWN" in _listify_tokens(value)
    )

    source_pdf_series = frame.apply(lambda row: _source_pdf_name(row.to_dict()), axis=1)
    source_pdf_distribution = _distribution_from_series(source_pdf_series) if not source_pdf_series.empty else {}

    return {
        "record_count": int(len(frame)),
        "confidence_level_distribution": _distribution_from_series(frame["confidence_level"]),
        "routing_decision_distribution": _distribution_from_series(frame["routing_decision"]),
        "risk_flag_distribution": _distribution_from_token_lists(frame["risk_flags"].tolist()),
        "score_bucket_distribution": _distribution_from_series(frame["score_bucket"]),
        "source_artifact_distribution": _distribution_from_series(frame["source_artifact"]),
        "source_pdf_distribution": source_pdf_distribution,
        "existing_status_distribution": _existing_status_distribution(frame),
        "sidecar_vs_existing_status_comparison": _sidecar_vs_existing(frame),
        "potential_false_trusted_count": int(potential_false_trusted_mask.sum()),
        "trusted_with_warning_risk_count": int(trusted_with_warning_mask.sum()),
        "trusted_with_low_evidence_count": int(trusted_with_low_evidence_mask.sum()),
        "missing_evidence_count": int(missing_evidence_mask.sum()),
        "target_metric_ambiguous_count": int(target_metric_ambiguous_mask.sum()),
        "value_parse_failed_count": int(value_parse_failed_mask.sum()),
        "unit_unknown_count": int(unit_unknown_mask.sum()),
    }


def _delivery_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    trusted = int(metrics["routing_decision_distribution"].get("TRUSTED", 0))
    review_required = int(metrics["routing_decision_distribution"].get("REVIEW_REQUIRED", 0))
    rejected = int(metrics["routing_decision_distribution"].get("REJECTED", 0))
    needs_more_info = int(metrics["routing_decision_distribution"].get("NEEDS_MORE_INFO", 0))
    total = int(metrics["record_count"])
    return {
        "sidecar_trusted_suggestion_count": trusted,
        "sidecar_review_required_suggestion_count": review_required,
        "sidecar_needs_more_info_or_rejected_count": rejected + needs_more_info,
        "estimated_human_review_burden_count": review_required + rejected + needs_more_info,
        "estimated_auto_trusted_ratio": round((trusted / total), 6) if total > 0 else 0.0,
    }


def _enrich_unfamiliar_scored_records(scored_df: pd.DataFrame) -> pd.DataFrame:
    working_df = scored_df.copy()
    if working_df.empty:
        return working_df
    if "score_bucket" not in working_df.columns:
        working_df["score_bucket"] = working_df["confidence_score"].apply(score_bucket_label)
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
        "risk_flags",
        "warning_risks",
        "evidence_refs",
    ]:
        if column not in working_df.columns:
            working_df[column] = ""
    working_df["strict_candidate_key"] = working_df.apply(lambda row: strict_candidate_key(row.to_dict()), axis=1)
    working_df["cross_artifact_fingerprint_key"] = working_df.apply(
        lambda row: cross_artifact_fingerprint_key(row.to_dict()),
        axis=1,
    )
    working_df["source_pdf_name"] = working_df.apply(lambda row: _source_pdf_name(row.to_dict()), axis=1)
    return working_df


def _waiting_summary(
    *,
    output_dir: Path,
    unfamiliar_source_dirs: Sequence[Path],
    no_official_asset_modification_during_330f: bool,
    decision: str = WAITING_DECISION,
) -> Dict[str, Any]:
    return {
        "stage": "330F",
        "output_dir": str(output_dir),
        "validated_330e_benchmark": True,
        "unfamiliar_source_status": "missing_or_empty",
        "unfamiliar_source_dir_count": len(unfamiliar_source_dirs),
        "unfamiliar_source_dirs_checked": [str(path) for path in unfamiliar_source_dirs],
        "unfamiliar_candidate_artifact_row_count": 0,
        "unfamiliar_strict_deduped_candidate_count": 0,
        "unfamiliar_cross_artifact_deduped_candidate_count": 0,
        "scored_unfamiliar_record_count": 0,
        "confidence_level_distribution": {},
        "routing_decision_distribution": {},
        "risk_flag_distribution": {},
        "score_bucket_distribution": {},
        "source_artifact_distribution": {},
        "source_pdf_distribution": {},
        "existing_status_distribution": {},
        "sidecar_vs_existing_status_comparison": [],
        "potential_false_trusted_count": 0,
        "trusted_with_warning_risk_count": 0,
        "trusted_with_low_evidence_count": 0,
        "missing_evidence_count": 0,
        "target_metric_ambiguous_count": 0,
        "value_parse_failed_count": 0,
        "unit_unknown_count": 0,
        "sidecar_trusted_suggestion_count": 0,
        "sidecar_review_required_suggestion_count": 0,
        "sidecar_needs_more_info_or_rejected_count": 0,
        "estimated_human_review_burden_count": 0,
        "estimated_auto_trusted_ratio": 0.0,
        "recommended_next_step": "330F2_UNFAMILIAR_OUTPUT_PREPARATION",
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330f": no_official_asset_modification_during_330f,
        "files_written_to_official_assets": [],
        "qa_pass_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "decision": decision,
    }


def build_unfamiliar_pdf_trust_benchmark_330f(
    *,
    deduped_candidate_summary: Dict[str, Any],
    deduped_candidate_qa: Dict[str, Any],
    trust_scoring_summary: Dict[str, Any],
    unfamiliar_source_dirs: Sequence[Path],
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
        "readiness::330e_decision",
        _norm_text(deduped_candidate_summary.get("decision")) == READY_330E_DECISION,
        _norm_text(deduped_candidate_summary.get("decision")),
    )
    add_qa(
        "readiness::330e_qa_fail_count_summary",
        _safe_int(deduped_candidate_summary.get("qa_fail_count"), 1) == 0,
        str(deduped_candidate_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330e_qa_fail_count_qa_json",
        _safe_int(deduped_candidate_qa.get("qa_fail_count"), 1) == 0,
        str(deduped_candidate_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330e_policy_calibration_safe_to_continue",
        bool(deduped_candidate_summary.get("policy_calibration_safe_to_continue")) is True,
        str(deduped_candidate_summary.get("policy_calibration_safe_to_continue", "")),
    )
    add_qa(
        "readiness::330e_dedup_reliability_level",
        _norm_text(deduped_candidate_summary.get("dedup_reliability_level")) in {"MEDIUM", "HIGH"},
        _norm_text(deduped_candidate_summary.get("dedup_reliability_level")),
    )
    add_qa(
        "safety::330e_no_official_asset_modification",
        bool(deduped_candidate_summary.get("no_official_asset_modification_during_330e")) is True,
        str(deduped_candidate_summary.get("no_official_asset_modification_during_330e", "")),
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

    existing_source_dirs = [path for path in unfamiliar_source_dirs if path.exists() and path.is_dir()]
    unfamiliar_rows: List[Dict[str, Any]] = []
    source_inventory_df = pd.DataFrame()
    unfamiliar_source_status = "missing_or_empty"
    if existing_source_dirs:
        unfamiliar_rows, source_inventory_df = load_cached_candidate_like_rows(existing_source_dirs)
        if unfamiliar_rows:
            unfamiliar_source_status = "loaded"

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330f = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330f",
        no_official_asset_modification_during_330f,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    if unfamiliar_source_status != "loaded":
        summary = _waiting_summary(
            output_dir=output_dir,
            unfamiliar_source_dirs=unfamiliar_source_dirs,
            no_official_asset_modification_during_330f=no_official_asset_modification_during_330f,
        )
        summary["qa_pass_count"] = qa_pass_count
        summary["qa_fail_count"] = qa_fail_count
        summary["blocking_reasons"] = blocking_reasons
        summary["validated_330e_benchmark"] = qa_fail_count == 0 and _norm_text(deduped_candidate_summary.get("decision")) == READY_330E_DECISION
        summary_df = _frame_for_output(pd.DataFrame([summary]))
        qa_summary_df = _frame_for_output(
            pd.DataFrame(
                [
                    {
                        "qa_pass_count": qa_pass_count,
                        "qa_fail_count": qa_fail_count,
                        "blocking_reasons": " | ".join(blocking_reasons),
                        "decision": summary["decision"],
                    }
                ]
            )
        )
        no_apply_proof_json = build_no_apply_proof(
            stage="330F",
            files_read=list(files_read),
            official_assets_before=official_assets_before,
            official_assets_after=official_assets_after,
            official_assets_written=[],
        )
        return {
            "summary": summary,
            "qa_json": {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": 0,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": blocking_reasons,
                "checks": qa_df.to_dict(orient="records"),
            },
            "no_apply_proof_json": no_apply_proof_json,
            "summary_df": summary_df,
            "qa_summary_df": qa_summary_df,
            "qa_checks_df": qa_df,
            "source_inventory_df": _frame_for_output(source_inventory_df),
            "coverage_df": pd.DataFrame(),
            "distribution_df": pd.DataFrame(),
            "delivery_summary_df": pd.DataFrame(),
            "official_asset_proof_df": _frame_for_output(
                pd.DataFrame(
                    [
                        {
                            "asset_path": asset_path,
                            "hash_before": before_hash,
                            "hash_after": official_assets_after.get(asset_path, ""),
                            "modified_during_330f": before_hash != official_assets_after.get(asset_path, ""),
                        }
                        for asset_path, before_hash in official_assets_before.items()
                    ]
                )
            ),
            "known_limitations_df": _frame_for_output(
                pd.DataFrame(
                    [
                        {
                            "limitation": "missing_or_empty_unfamiliar_sources",
                            "detail": "No unfamiliar source directories were present with compatible candidate rows.",
                        }
                    ]
                )
            ),
            "artifact_row_view_df": pd.DataFrame(),
            "strict_deduped_view_df": pd.DataFrame(),
            "cross_artifact_deduped_view_df": pd.DataFrame(),
            "strict_duplicate_rows_df": pd.DataFrame(),
            "cross_artifact_duplicate_rows_df": pd.DataFrame(),
        }

    scored_records = [score_trust_record(row) for row in unfamiliar_rows]
    scored_df = _frame_for_output(pd.DataFrame(scored_records))
    if not scored_df.empty:
        scored_df["score_bucket"] = scored_df["confidence_score"].apply(score_bucket_label)
    enriched_df = _enrich_unfamiliar_scored_records(scored_df)
    artifact_row_view_df = enriched_df.copy()
    strict_deduped_view_df = enriched_df.drop_duplicates("strict_candidate_key", keep="first").copy()
    cross_artifact_deduped_view_df = enriched_df.drop_duplicates("cross_artifact_fingerprint_key", keep="first").copy()

    artifact_metrics = _view_metrics(artifact_row_view_df)
    delivery_summary = _delivery_summary(artifact_metrics)

    summary = {
        "stage": "330F",
        "output_dir": str(output_dir),
        "validated_330e_benchmark": qa_fail_count == 0 and _norm_text(deduped_candidate_summary.get("decision")) == READY_330E_DECISION,
        "unfamiliar_source_status": unfamiliar_source_status,
        "unfamiliar_source_dir_count": len(existing_source_dirs),
        "unfamiliar_source_dirs_checked": [str(path) for path in unfamiliar_source_dirs],
        "unfamiliar_source_dirs_loaded": [str(path) for path in existing_source_dirs],
        "unfamiliar_candidate_artifact_row_count": int(len(artifact_row_view_df)),
        "unfamiliar_strict_deduped_candidate_count": int(len(strict_deduped_view_df)),
        "unfamiliar_cross_artifact_deduped_candidate_count": int(len(cross_artifact_deduped_view_df)),
        "scored_unfamiliar_record_count": int(len(scored_records)),
        "confidence_level_distribution": artifact_metrics["confidence_level_distribution"],
        "routing_decision_distribution": artifact_metrics["routing_decision_distribution"],
        "risk_flag_distribution": artifact_metrics["risk_flag_distribution"],
        "score_bucket_distribution": artifact_metrics["score_bucket_distribution"],
        "source_artifact_distribution": artifact_metrics["source_artifact_distribution"],
        "source_pdf_distribution": artifact_metrics["source_pdf_distribution"],
        "existing_status_distribution": artifact_metrics["existing_status_distribution"],
        "sidecar_vs_existing_status_comparison": artifact_metrics["sidecar_vs_existing_status_comparison"],
        "potential_false_trusted_count": artifact_metrics["potential_false_trusted_count"],
        "trusted_with_warning_risk_count": artifact_metrics["trusted_with_warning_risk_count"],
        "trusted_with_low_evidence_count": artifact_metrics["trusted_with_low_evidence_count"],
        "missing_evidence_count": artifact_metrics["missing_evidence_count"],
        "target_metric_ambiguous_count": artifact_metrics["target_metric_ambiguous_count"],
        "value_parse_failed_count": artifact_metrics["value_parse_failed_count"],
        "unit_unknown_count": artifact_metrics["unit_unknown_count"],
        **delivery_summary,
        "recommended_next_step": "330G_END_TO_END_DELIVERY_QUALITY_REPORT",
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330f": no_official_asset_modification_during_330f,
        "files_written_to_official_assets": [],
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    no_apply_proof_json = build_no_apply_proof(
        stage="330F",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }

    summary_df = _frame_for_output(pd.DataFrame([summary]))
    qa_summary_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "qa_pass_count": qa_pass_count,
                    "qa_fail_count": qa_fail_count,
                    "blocking_reasons": " | ".join(blocking_reasons),
                    "decision": summary["decision"],
                }
            ]
        )
    )
    distribution_rows = []
    for distribution_name in [
        "confidence_level_distribution",
        "routing_decision_distribution",
        "risk_flag_distribution",
        "score_bucket_distribution",
        "source_artifact_distribution",
        "source_pdf_distribution",
        "existing_status_distribution",
    ]:
        for bucket, count in artifact_metrics.get(distribution_name, {}).items():
            distribution_rows.append(
                {
                    "distribution_name": distribution_name,
                    "bucket": bucket,
                    "count": count,
                }
            )
    distribution_df = _frame_for_output(pd.DataFrame(distribution_rows))
    delivery_summary_df = _frame_for_output(pd.DataFrame([delivery_summary]))
    coverage_df = _frame_for_output(
        pd.DataFrame(
            [
                {"metric": "unfamiliar_source_dir_count", "value": len(existing_source_dirs)},
                {"metric": "unfamiliar_candidate_artifact_row_count", "value": len(artifact_row_view_df)},
                {"metric": "unfamiliar_strict_deduped_candidate_count", "value": len(strict_deduped_view_df)},
                {"metric": "unfamiliar_cross_artifact_deduped_candidate_count", "value": len(cross_artifact_deduped_view_df)},
                {"metric": "scored_unfamiliar_record_count", "value": len(scored_records)},
            ]
        )
    )
    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_330f": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    known_limitations_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "limitation": "sidecar_only",
                    "detail": "330F scores unfamiliar candidate-like outputs in sidecar mode only and does not modify production routing.",
                },
                {
                    "limitation": "cached_output_preference",
                    "detail": "330F only uses cached unfamiliar outputs and does not run MinerU or other extraction engines.",
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
        "source_inventory_df": _frame_for_output(source_inventory_df),
        "coverage_df": coverage_df,
        "distribution_df": distribution_df,
        "delivery_summary_df": delivery_summary_df,
        "official_asset_proof_df": official_asset_proof_df,
        "known_limitations_df": known_limitations_df,
        "artifact_row_view_df": _frame_for_output(artifact_row_view_df),
        "strict_deduped_view_df": _frame_for_output(strict_deduped_view_df),
        "cross_artifact_deduped_view_df": _frame_for_output(cross_artifact_deduped_view_df),
        "strict_duplicate_rows_df": _frame_for_output(enriched_df.loc[enriched_df.duplicated("strict_candidate_key", keep=False)].copy()),
        "cross_artifact_duplicate_rows_df": _frame_for_output(enriched_df.loc[enriched_df.duplicated("cross_artifact_fingerprint_key", keep=False)].copy()),
    }
