from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.delivery_report_refresh_330j import _read_json, _write_rerun_330f
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.source_attribution_unit_signal_fix_330i import (
    _listify_tokens,
    _read_jsonl_rows,
)
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_330K_DECISION = "UNIT_SIGNAL_REVIEW_330K_READY_FOR_330J2_DELIVERY_REFRESH"
READY_330F_DECISION = (
    "TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT"
)
READY_DECISION = (
    "DELIVERY_REPORT_REFRESH_330J2_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_330L_EXPORT_PREVIEW"
)
NOT_READY_DECISION = "DELIVERY_REPORT_REFRESH_330J2_NOT_READY"

DEFAULT_UNIT_SIGNAL_REVIEW_DIR = Path(r"D:\_datefac\output\unit_signal_review_330k")
DEFAULT_FIXED_PREPARED_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split_330k")
DEFAULT_PREVIOUS_DELIVERY_REPORT_DIR = Path(r"D:\_datefac\output\delivery_report_refresh_330j")
DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR = Path(
    r"D:\_datefac\output\deduped_candidate_trust_benchmark_330e"
)
DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")
DEFAULT_RERUN_330F_OUTPUT_DIR = Path(
    r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j2"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\delivery_report_refresh_after_330k_330j2")

REQUIRED_FIXED_PREPARED_FILES = [
    "unfamiliar_candidate_rows.jsonl",
    "unfamiliar_candidate_rows.xlsx",
    "unfamiliar_candidate_manifest.json",
]

BASELINE_330J = {
    "unit_missing_count": 54,
    "unit_unknown_risk_count": 54,
    "unit_conflict_risk_count": 12,
    "sidecar_trusted_suggestion_count": 120,
    "sidecar_review_required_suggestion_count": 114,
    "confidence_level_distribution": {"HIGH": 120, "MEDIUM": 96, "LOW": 18},
    "routing_decision_distribution": {"TRUSTED": 120, "REVIEW_REQUIRED": 114},
    "risk_flag_distribution": {
        "UNIT_UNKNOWN": 108,
        "UNIT_CONFLICT": 24,
        "LABEL_AMBIGUOUS": 16,
    },
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _distribution_from_series(values: Iterable[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for raw in values:
        token = _norm_text(raw)
        if not token:
            continue
        counts[token] = counts.get(token, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _delta_distribution(
    current: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> Dict[str, int]:
    keys = sorted(set(current) | set(baseline))
    return {
        key: _safe_int(current.get(key), 0) - _safe_int(baseline.get(key), 0)
        for key in keys
    }


def validate_330k_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append(
            {
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    add(
        "readiness::330k_decision",
        _norm_text(summary.get("decision")) == READY_330K_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330k_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330k_input_candidate_row_count",
        _safe_int(summary.get("input_candidate_row_count"), -1) == 117,
        str(summary.get("input_candidate_row_count", "")),
    )
    add(
        "quality::330k_unit_missing_count_input",
        _safe_int(summary.get("unit_missing_count_input"), -1) == 54,
        str(summary.get("unit_missing_count_input", "")),
    )
    add(
        "quality::330k_additional_safe_unit_fix_count",
        _safe_int(summary.get("additional_safe_unit_fix_count"), -1) == 36,
        str(summary.get("additional_safe_unit_fix_count", "")),
    )
    add(
        "quality::330k_unit_missing_count_after_330k",
        _safe_int(summary.get("unit_missing_count_after_330k"), -1) == 18,
        str(summary.get("unit_missing_count_after_330k", "")),
    )
    add(
        "review::330k_review_sample_row_count",
        _safe_int(summary.get("review_sample_row_count"), -1) == 21,
        str(summary.get("review_sample_row_count", "")),
    )
    add(
        "review::330k_human_review_workbook_generated",
        bool(summary.get("human_review_workbook_generated")) is True,
        str(summary.get("human_review_workbook_generated", "")),
    )
    add(
        "safety::330k_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330k")) is True,
        str(summary.get("no_official_asset_modification_during_330k", "")),
    )
    return checks


def _build_refreshed_metrics(
    *,
    fixed_rows: Sequence[Mapping[str, Any]],
    rerun_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    prepared_candidate_row_count = len(fixed_rows)
    source_pdf_unique_count = len(
        {
            _norm_text(row.get("source_pdf"))
            for row in fixed_rows
            if _norm_text(row.get("source_pdf"))
        }
    )
    artifact_row_count = _safe_int(
        rerun_summary.get("unfamiliar_candidate_artifact_row_count"),
        prepared_candidate_row_count,
    )
    strict_deduped_candidate_count = _safe_int(
        rerun_summary.get("unfamiliar_strict_deduped_candidate_count"),
        prepared_candidate_row_count,
    )
    unit_missing_count = sum(1 for row in fixed_rows if not _norm_text(row.get("unit")))
    source_page_missing_count = sum(1 for row in fixed_rows if not _norm_text(row.get("source_page")))
    unit_unknown_risk_count = sum(
        1 for row in fixed_rows if "UNIT_UNKNOWN" in _listify_tokens(row.get("risk_flags"))
    )
    unit_conflict_risk_count = sum(
        1 for row in fixed_rows if "UNIT_CONFLICT" in _listify_tokens(row.get("risk_flags"))
    )
    sidecar_trusted_suggestion_count = _safe_int(
        rerun_summary.get("sidecar_trusted_suggestion_count")
    )
    sidecar_review_required_suggestion_count = _safe_int(
        rerun_summary.get("sidecar_review_required_suggestion_count")
    )
    confidence_level_distribution = dict(rerun_summary.get("confidence_level_distribution", {}))
    routing_decision_distribution = dict(rerun_summary.get("routing_decision_distribution", {}))
    risk_flag_distribution = dict(rerun_summary.get("risk_flag_distribution", {}))
    return {
        "prepared_candidate_row_count": prepared_candidate_row_count,
        "artifact_row_count": artifact_row_count,
        "strict_deduped_candidate_count": strict_deduped_candidate_count,
        "source_pdf_unique_count": source_pdf_unique_count,
        "source_page_missing_count": source_page_missing_count,
        "unit_missing_count": unit_missing_count,
        "unit_unknown_risk_count": unit_unknown_risk_count,
        "unit_conflict_risk_count": unit_conflict_risk_count,
        "sidecar_trusted_suggestion_count": sidecar_trusted_suggestion_count,
        "sidecar_review_required_suggestion_count": sidecar_review_required_suggestion_count,
        "sidecar_auto_trusted_ratio_artifact_row": round(
            sidecar_trusted_suggestion_count / artifact_row_count, 6
        )
        if artifact_row_count
        else 0.0,
        "confidence_level_distribution": confidence_level_distribution,
        "routing_decision_distribution": routing_decision_distribution,
        "risk_flag_distribution": risk_flag_distribution,
        "actual_source_pdf_distribution": _distribution_from_series(
            row.get("source_pdf") for row in fixed_rows
        ),
    }


def _build_comparison_vs_330j(refreshed_metrics: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "unit_missing_delta_vs_330j": _safe_int(refreshed_metrics.get("unit_missing_count"), 0)
        - BASELINE_330J["unit_missing_count"],
        "unit_unknown_risk_delta_vs_330j": _safe_int(
            refreshed_metrics.get("unit_unknown_risk_count"), 0
        )
        - BASELINE_330J["unit_unknown_risk_count"],
        "unit_conflict_risk_delta_vs_330j": _safe_int(
            refreshed_metrics.get("unit_conflict_risk_count"), 0
        )
        - BASELINE_330J["unit_conflict_risk_count"],
        "trusted_suggestion_delta_vs_330j": _safe_int(
            refreshed_metrics.get("sidecar_trusted_suggestion_count"), 0
        )
        - BASELINE_330J["sidecar_trusted_suggestion_count"],
        "review_required_delta_vs_330j": _safe_int(
            refreshed_metrics.get("sidecar_review_required_suggestion_count"), 0
        )
        - BASELINE_330J["sidecar_review_required_suggestion_count"],
        "confidence_level_delta_vs_330j": _delta_distribution(
            dict(refreshed_metrics.get("confidence_level_distribution", {})),
            BASELINE_330J["confidence_level_distribution"],
        ),
        "routing_decision_delta_vs_330j": _delta_distribution(
            dict(refreshed_metrics.get("routing_decision_distribution", {})),
            BASELINE_330J["routing_decision_distribution"],
        ),
        "risk_flag_delta_vs_330j": _delta_distribution(
            dict(refreshed_metrics.get("risk_flag_distribution", {})),
            BASELINE_330J["risk_flag_distribution"],
        ),
    }


def _build_comparison_vs_330k(summary_330k: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "unit_missing_count_after_330k": _safe_int(summary_330k.get("unit_missing_count_after_330k"), 0),
        "unit_review_required_count": _safe_int(summary_330k.get("unit_review_required_count"), 0),
        "unit_conflict_review_count": _safe_int(summary_330k.get("unit_conflict_review_count"), 0),
        "unit_unknown_review_count": _safe_int(summary_330k.get("unit_unknown_review_count"), 0),
        "review_sample_row_count": _safe_int(summary_330k.get("review_sample_row_count"), 0),
    }


def _delivery_readiness_judgment(
    *,
    rerun_success: bool,
    refreshed_metrics: Mapping[str, Any],
) -> str:
    if (
        rerun_success
        and _safe_int(refreshed_metrics.get("source_page_missing_count"), -1) == 0
        and _safe_int(refreshed_metrics.get("unit_missing_count"), 999999) <= 18
    ):
        return "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS"
    return "DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS"


def build_delivery_report_refresh_after_330k_330j2(
    *,
    unit_signal_review_dir: Path,
    fixed_prepared_dir: Path,
    previous_delivery_report_dir: Path,
    deduped_candidate_benchmark_dir: Path,
    trust_scoring_dir: Path,
    rerun_330f: bool,
    output_dir: Path,
    rerun_330f_output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330k_path = unit_signal_review_dir / "unit_signal_review_330k_summary.json"
    summary_330j_path = previous_delivery_report_dir / "delivery_report_refresh_330j_summary.json"
    fixed_manifest_path = fixed_prepared_dir / "unfamiliar_candidate_manifest.json"
    fixed_rows_path = fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"

    summary_330k = _read_json(summary_330k_path)
    summary_330j = _read_json(summary_330j_path)
    fixed_manifest = _read_json(fixed_manifest_path)
    fixed_rows = _read_jsonl_rows(fixed_rows_path)

    qa_rows = validate_330k_summary(summary_330k)

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append(
            {
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }

    for filename in REQUIRED_FIXED_PREPARED_FILES:
        path = fixed_prepared_dir / filename
        add_qa(f"inputs::fixed_prepared::{filename}", path.exists(), str(path))
    add_qa("records::fixed_candidate_row_count", len(fixed_rows) == 117, str(len(fixed_rows)))
    add_qa(
        "records::fixed_manifest_output_candidate_row_count",
        _safe_int(fixed_manifest.get("output_candidate_row_count"), -1) == 117,
        str(fixed_manifest.get("output_candidate_row_count", "")),
    )

    rerun_summary: Dict[str, Any]
    if rerun_330f:
        rerun_summary = _write_rerun_330f(
            fixed_prepared_dir=fixed_prepared_dir,
            rerun_330f_output_dir=rerun_330f_output_dir,
            deduped_candidate_benchmark_dir=deduped_candidate_benchmark_dir,
            trust_scoring_dir=trust_scoring_dir,
        )["summary"]
    else:
        rerun_summary = _read_json(
            rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.json"
        )

    rerun_success = (
        _norm_text(rerun_summary.get("decision")) == READY_330F_DECISION
        and _norm_text(rerun_summary.get("unfamiliar_source_status")) == "loaded"
        and _safe_int(rerun_summary.get("qa_fail_count"), 1) == 0
    )
    add_qa(
        "rerun::330f_decision",
        _norm_text(rerun_summary.get("decision")) == READY_330F_DECISION,
        _norm_text(rerun_summary.get("decision")),
    )
    add_qa(
        "rerun::330f_unfamiliar_source_status",
        _norm_text(rerun_summary.get("unfamiliar_source_status")) == "loaded",
        _norm_text(rerun_summary.get("unfamiliar_source_status")),
    )

    refreshed_metrics = _build_refreshed_metrics(
        fixed_rows=fixed_rows,
        rerun_summary=rerun_summary,
    )
    comparison_vs_330j = _build_comparison_vs_330j(refreshed_metrics)
    comparison_vs_330k = _build_comparison_vs_330k(summary_330k)
    delivery_readiness_judgment = _delivery_readiness_judgment(
        rerun_success=rerun_success,
        refreshed_metrics=refreshed_metrics,
    )

    add_qa(
        "quality::prepared_candidate_row_count",
        _safe_int(refreshed_metrics.get("prepared_candidate_row_count"), -1) == 117,
        str(refreshed_metrics.get("prepared_candidate_row_count", "")),
    )
    add_qa(
        "quality::source_page_missing_count",
        _safe_int(refreshed_metrics.get("source_page_missing_count"), -1) == 0,
        str(refreshed_metrics.get("source_page_missing_count", "")),
    )
    add_qa(
        "quality::unit_missing_count",
        _safe_int(refreshed_metrics.get("unit_missing_count"), 999999) <= 18,
        str(refreshed_metrics.get("unit_missing_count", "")),
    )
    add_qa(
        "quality::unit_missing_delta_vs_330j",
        _safe_int(comparison_vs_330j.get("unit_missing_delta_vs_330j"), 999999) <= -36,
        str(comparison_vs_330j.get("unit_missing_delta_vs_330j", "")),
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }
    no_official_asset_modification_during_330j2 = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330j2",
        no_official_asset_modification_during_330j2,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    decision = READY_DECISION if qa_fail_count == 0 and rerun_success else NOT_READY_DECISION
    comparison_json = {
        "comparison_vs_330j": comparison_vs_330j,
        "comparison_vs_330k": comparison_vs_330k,
    }

    summary = {
        "stage": "330J2",
        "output_dir": str(output_dir),
        "validated_330k_unit_review": all(
            row.get("status") == "PASS" for row in validate_330k_summary(summary_330k)
        ),
        "reran_330f": bool(rerun_330f),
        "330f_rerun_output_dir": str(rerun_330f_output_dir),
        "330f_unfamiliar_source_status": _norm_text(rerun_summary.get("unfamiliar_source_status")),
        "330f_scored_unfamiliar_record_count": _safe_int(
            rerun_summary.get("scored_unfamiliar_record_count"), 0
        ),
        "330f_decision": _norm_text(rerun_summary.get("decision")),
        **refreshed_metrics,
        **comparison_vs_330j,
        **comparison_vs_330k,
        "delivery_readiness_judgment": delivery_readiness_judgment,
        "delivery_readiness_rationale": [
            "330J2 reruns 330F against the 330K fixed prepared rows in sidecar mode only.",
            "The refreshed report verifies source-page completeness and quantifies the residual unit-review burden.",
            "The result is demo-ready with unit-review caveats and does not claim client-ready production routing.",
        ],
        "recommended_next_step": "330K2_HUMAN_UNIT_REVIEW_OR_330L_CLIENT_STYLE_EXPORT_PREVIEW",
        "secondary_next_step": "330L_CLIENT_STYLE_EXPORT_PREVIEW",
        "official_assets_modified": False,
        "no_official_asset_modification_during_330j2": no_official_asset_modification_during_330j2,
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
        stage="330J2",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    refreshed_metrics_df = _frame_for_output(
        pd.DataFrame(
            [
                {"metric": key, "value": value}
                for key, value in refreshed_metrics.items()
                if not isinstance(value, dict)
            ]
        )
    )
    comparison_df = _frame_for_output(
        pd.DataFrame(
            [
                {"metric": key, "value": value}
                for key, value in comparison_vs_330j.items()
                if not isinstance(value, dict)
            ]
            + [{"metric": key, "value": value} for key, value in comparison_vs_330k.items()]
        )
    )
    delta_distribution_rows: List[Dict[str, Any]] = []
    for distribution_name, payload in [
        ("confidence_level_delta_vs_330j", comparison_vs_330j["confidence_level_delta_vs_330j"]),
        ("routing_decision_delta_vs_330j", comparison_vs_330j["routing_decision_delta_vs_330j"]),
        ("risk_flag_delta_vs_330j", comparison_vs_330j["risk_flag_delta_vs_330j"]),
    ]:
        for bucket, count in payload.items():
            delta_distribution_rows.append(
                {"distribution_name": distribution_name, "bucket": bucket, "delta_count": count}
            )
    comparison_delta_df = _frame_for_output(pd.DataFrame(delta_distribution_rows))
    distribution_rows: List[Dict[str, Any]] = []
    for distribution_name in [
        "confidence_level_distribution",
        "routing_decision_distribution",
        "risk_flag_distribution",
        "actual_source_pdf_distribution",
    ]:
        for bucket, count in refreshed_metrics.get(distribution_name, {}).items():
            distribution_rows.append(
                {"distribution_name": distribution_name, "bucket": bucket, "count": count}
            )
    distribution_df = _frame_for_output(pd.DataFrame(distribution_rows))
    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_330j2": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    rerun_summary_df = _frame_for_output(pd.DataFrame([rerun_summary])) if rerun_summary else pd.DataFrame()
    known_limitations_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "limitation": "sidecar_only",
                    "detail": "330J2 refreshes delivery reporting only and does not change production routing or rule assets.",
                },
                {
                    "limitation": "residual_unit_review",
                    "detail": f"{_safe_int(refreshed_metrics.get('unit_missing_count'), 0)} rows still require manual unit review after 330K.",
                },
                {
                    "limitation": "cached_inputs_only",
                    "detail": "330J2 uses cached 330K/330J/330E/330B artifacts and does not reopen PDFs or run extraction engines.",
                },
            ]
        )
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "comparison_json": comparison_json,
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(
            pd.DataFrame(
                [
                    {
                        "qa_pass_count": qa_pass_count,
                        "qa_fail_count": qa_fail_count,
                        "decision": decision,
                    }
                ]
            )
        ),
        "qa_checks_df": qa_df,
        "refreshed_metrics_df": refreshed_metrics_df,
        "comparison_df": comparison_df,
        "comparison_delta_df": comparison_delta_df,
        "distribution_df": distribution_df,
        "rerun_330f_summary_df": rerun_summary_df,
        "fixed_manifest_df": _frame_for_output(pd.DataFrame([fixed_manifest]))
        if fixed_manifest
        else pd.DataFrame(),
        "fixed_candidate_rows_df": _frame_for_output(pd.DataFrame(fixed_rows)),
        "official_asset_proof_df": official_asset_proof_df,
        "known_limitations_df": known_limitations_df,
        "previous_delivery_report_df": _frame_for_output(pd.DataFrame([summary_330j]))
        if summary_330j
        else pd.DataFrame(),
        "unit_signal_review_df": _frame_for_output(pd.DataFrame([summary_330k]))
        if summary_330k
        else pd.DataFrame(),
    }
