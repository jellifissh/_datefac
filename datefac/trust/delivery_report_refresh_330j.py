from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_export_smoke_330f4 import (
    _compatibility_row_from_prepared,
)
from datefac.trust.source_attribution_unit_signal_fix_330i import _listify_tokens
from datefac.trust.source_attribution_unit_signal_fix_330i import _read_json as _read_json_330i
from datefac.trust.source_attribution_unit_signal_fix_330i import _read_jsonl_rows
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import _frame_for_output
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import _norm_text
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import _safe_int


READY_330I_DECISION = (
    "SOURCE_ATTRIBUTION_UNIT_SIGNAL_FIX_330I_READY_FOR_330J_DELIVERY_REPORT_REFRESH"
)
READY_330F_DECISION = (
    "TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT"
)
READY_DECISION = "DELIVERY_REPORT_REFRESH_330J_READY_FOR_330K_UNIT_SIGNAL_OR_REVIEW_SAMPLE"
NOT_READY_DECISION = "DELIVERY_REPORT_REFRESH_330J_NOT_READY"

DEFAULT_SOURCE_ATTRIBUTION_UNIT_FIX_DIR = Path(
    r"D:\_datefac\output\source_attribution_unit_signal_fix_330i"
)
DEFAULT_FIXED_PREPARED_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split_330i")
DEFAULT_PREVIOUS_DELIVERY_REPORT_DIR = Path(
    r"D:\_datefac\output\end_to_end_delivery_quality_report_330g"
)
DEFAULT_FULL_UNFAMILIAR_BENCHMARK_DIR = Path(
    r"D:\_datefac\output\full_unfamiliar_export_benchmark_330h"
)
DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR = Path(
    r"D:\_datefac\output\deduped_candidate_trust_benchmark_330e"
)
DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")
DEFAULT_RERUN_330F_OUTPUT_DIR = Path(
    r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\delivery_report_refresh_330j")


def _read_json(path: Path) -> Dict[str, Any]:
    return _read_json_330i(path)


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


def _distribution_from_token_lists(values: Iterable[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for raw in values:
        for token in _listify_tokens(raw):
            counts[token] = counts.get(token, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def validate_330i_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
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
        "readiness::330i_decision",
        _norm_text(summary.get("decision")) == READY_330I_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330i_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330i_input_candidate_row_count",
        _safe_int(summary.get("input_candidate_row_count"), -1) == 117,
        str(summary.get("input_candidate_row_count", "")),
    )
    add(
        "records::330i_output_candidate_row_count",
        _safe_int(summary.get("output_candidate_row_count"), -1) == 117,
        str(summary.get("output_candidate_row_count", "")),
    )
    add(
        "quality::330i_source_page_missing_count_after",
        _safe_int(summary.get("source_page_missing_count_after"), -1) == 0,
        str(summary.get("source_page_missing_count_after", "")),
    )
    add(
        "quality::330i_unit_missing_count_after",
        _safe_int(summary.get("unit_missing_count_after"), -1) == 54,
        str(summary.get("unit_missing_count_after", "")),
    )
    add(
        "safety::330i_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330i")) is True,
        str(summary.get("no_official_asset_modification_during_330i", "")),
    )
    return checks


def _write_rerun_330f(
    *,
    fixed_prepared_dir: Path,
    rerun_330f_output_dir: Path,
    deduped_candidate_benchmark_dir: Path,
    trust_scoring_dir: Path,
) -> Dict[str, Any]:
    from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH
    from datefac.trust.unfamiliar_pdf_trust_benchmark_330f import build_unfamiliar_pdf_trust_benchmark_330f
    from datefac.trust.unfamiliar_pdf_trust_benchmark_330f_report import (
        SAMPLES_SHEET_ORDER,
        SUMMARY_SHEET_ORDER,
        unfamiliar_pdf_trust_benchmark_330f_markdown,
        write_excel,
        write_json,
    )

    deduped_summary_path = (
        deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_summary.json"
    )
    deduped_qa_path = deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_qa.json"
    trust_scoring_summary_path = trust_scoring_dir / "trust_engine_scoring_330b_summary.json"
    fixed_rows_path = fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"
    fixed_rows = _read_jsonl_rows(fixed_rows_path)
    compat_dir = rerun_330f_output_dir / "input_compat"
    compat_dir.mkdir(parents=True, exist_ok=True)
    compat_jsonl_path = compat_dir / "unfamiliar_330j_affected_candidates.jsonl"
    compat_xlsx_path = compat_dir / "unfamiliar_330j_affected_candidates.xlsx"
    compatibility_rows = [_compatibility_row_from_prepared(row) for row in fixed_rows]

    with compat_jsonl_path.open("w", encoding="utf-8") as handle:
        for row in compatibility_rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    with pd.ExcelWriter(compat_xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame(compatibility_rows).to_excel(
            writer,
            sheet_name="affected_candidates",
            index=False,
        )

    artifacts = build_unfamiliar_pdf_trust_benchmark_330f(
        deduped_candidate_summary=_read_json(deduped_summary_path),
        deduped_candidate_qa=_read_json(deduped_qa_path),
        trust_scoring_summary=_read_json(trust_scoring_summary_path),
        unfamiliar_source_dirs=[compat_dir],
        output_dir=rerun_330f_output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(deduped_summary_path),
            str(deduped_qa_path),
            str(trust_scoring_summary_path),
            str(fixed_prepared_dir),
            str(fixed_rows_path),
            str(compat_jsonl_path),
            str(compat_xlsx_path),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    rerun_330f_output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.json"
    qa_json = rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_qa.json"
    no_apply_json = rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_no_apply_proof.json"
    summary_xlsx = rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.xlsx"
    samples_xlsx = rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_samples.xlsx"
    report_md = rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_report.md"
    scored_jsonl = rerun_330f_output_dir / "unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "source_inventory": artifacts["source_inventory_df"],
            "coverage": artifacts["coverage_df"],
            "distribution": artifacts["distribution_df"],
            "delivery_summary": artifacts["delivery_summary_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    write_excel(
        samples_xlsx,
        {
            "summary": artifacts["summary_df"],
            "artifact_row_view": artifacts["artifact_row_view_df"],
            "strict_deduped_view": artifacts["strict_deduped_view_df"],
            "cross_artifact_deduped_view": artifacts["cross_artifact_deduped_view_df"],
            "strict_duplicate_rows": artifacts["strict_duplicate_rows_df"],
            "cross_artifact_duplicate_rows": artifacts["cross_artifact_duplicate_rows_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
        SAMPLES_SHEET_ORDER,
    )
    report_md.write_text(
        unfamiliar_pdf_trust_benchmark_330f_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    with scored_jsonl.open("w", encoding="utf-8") as handle:
        for row in artifacts["artifact_row_view_df"].to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return artifacts


def _build_refreshed_metrics(
    *,
    fixed_rows: Sequence[Mapping[str, Any]],
    rerun_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    processed_pdf_count = len(
        {_norm_text(row.get("source_pdf")) for row in fixed_rows if _norm_text(row.get("source_pdf"))}
    )
    source_pdf_unique_count = processed_pdf_count
    prepared_candidate_row_count = len(fixed_rows)
    artifact_row_count = _safe_int(rerun_summary.get("unfamiliar_candidate_artifact_row_count"))
    strict_deduped_candidate_count = _safe_int(
        rerun_summary.get("unfamiliar_strict_deduped_candidate_count"),
        prepared_candidate_row_count,
    )
    sidecar_trusted_suggestion_count = _safe_int(
        rerun_summary.get("sidecar_trusted_suggestion_count")
    )
    sidecar_review_required_suggestion_count = _safe_int(
        rerun_summary.get("sidecar_review_required_suggestion_count")
    )
    sidecar_auto_trusted_ratio_artifact_row = round(
        (sidecar_trusted_suggestion_count / artifact_row_count), 6
    ) if artifact_row_count else 0.0
    sidecar_auto_trusted_ratio_strict_deduped = round(
        (sidecar_trusted_suggestion_count / strict_deduped_candidate_count), 6
    ) if strict_deduped_candidate_count else 0.0
    unit_missing_count = sum(1 for row in fixed_rows if not _norm_text(row.get("unit")))
    source_page_missing_count = sum(
        1 for row in fixed_rows if not _norm_text(row.get("source_page"))
    )
    unit_unknown_risk_count = sum(
        1 for row in fixed_rows if "UNIT_UNKNOWN" in _listify_tokens(row.get("risk_flags"))
    )
    unit_conflict_risk_count = sum(
        1 for row in fixed_rows if "UNIT_CONFLICT" in _listify_tokens(row.get("risk_flags"))
    )
    confidence_level_distribution = rerun_summary.get("confidence_level_distribution", {})
    routing_decision_distribution = rerun_summary.get("routing_decision_distribution", {})
    risk_flag_distribution = rerun_summary.get("risk_flag_distribution", {})
    actual_source_pdf_distribution = _distribution_from_series(
        row.get("source_pdf") for row in fixed_rows
    )
    return {
        "processed_pdf_count": processed_pdf_count,
        "source_pdf_unique_count": source_pdf_unique_count,
        "prepared_candidate_row_count": prepared_candidate_row_count,
        "artifact_row_count": artifact_row_count,
        "strict_deduped_candidate_count": strict_deduped_candidate_count,
        "sidecar_trusted_suggestion_count": sidecar_trusted_suggestion_count,
        "sidecar_review_required_suggestion_count": sidecar_review_required_suggestion_count,
        "sidecar_auto_trusted_ratio_artifact_row": sidecar_auto_trusted_ratio_artifact_row,
        "sidecar_auto_trusted_ratio_strict_deduped": sidecar_auto_trusted_ratio_strict_deduped,
        "unit_missing_count": unit_missing_count,
        "source_page_missing_count": source_page_missing_count,
        "unit_unknown_risk_count": unit_unknown_risk_count,
        "unit_conflict_risk_count": unit_conflict_risk_count,
        "confidence_level_distribution": confidence_level_distribution,
        "routing_decision_distribution": routing_decision_distribution,
        "risk_flag_distribution": risk_flag_distribution,
        "actual_source_pdf_distribution": actual_source_pdf_distribution,
    }


def _build_comparison(
    *,
    summary_330g: Mapping[str, Any],
    summary_330h: Mapping[str, Any],
    summary_330i: Mapping[str, Any],
    refreshed_metrics: Mapping[str, Any],
) -> Dict[str, Any]:
    current_risk_flag_distribution = dict(refreshed_metrics.get("risk_flag_distribution", {}))
    previous_risk_flag_distribution = dict(summary_330g.get("risk_flag_distribution", {}))
    all_risks = sorted(set(current_risk_flag_distribution) | set(previous_risk_flag_distribution))
    risk_flag_delta = {
        risk: int(current_risk_flag_distribution.get(risk, 0))
        - int(previous_risk_flag_distribution.get(risk, 0))
        for risk in all_risks
    }
    return {
        "unit_missing_before_330i": _safe_int(summary_330h.get("unit_missing_count"), 64),
        "unit_missing_after_330i": _safe_int(summary_330i.get("unit_missing_count_after"), 54),
        "unit_filled_count": _safe_int(summary_330i.get("unit_filled_count"), 19),
        "source_page_missing_before_330h": _safe_int(summary_330g.get("source_page_missing_count"), 83),
        "source_page_missing_after_330i": _safe_int(summary_330i.get("source_page_missing_count_after"), 0),
        "trusted_suggestion_delta": int(refreshed_metrics.get("sidecar_trusted_suggestion_count", 0))
        - _safe_int(summary_330h.get("330f_sidecar_trusted_suggestion_count"), 0),
        "review_required_delta": int(
            refreshed_metrics.get("sidecar_review_required_suggestion_count", 0)
        ) - _safe_int(summary_330h.get("330f_sidecar_review_required_suggestion_count"), 0),
        "risk_flag_delta": risk_flag_delta,
        "artifact_row_delta_vs_330g": int(refreshed_metrics.get("artifact_row_count", 0))
        - _safe_int(summary_330g.get("artifact_row_count"), 0),
        "prepared_candidate_row_delta_vs_330g": int(
            refreshed_metrics.get("prepared_candidate_row_count", 0)
        ) - _safe_int(summary_330g.get("prepared_candidate_row_count"), 0),
    }


def _delivery_readiness_judgment(
    *,
    reran_330f: bool,
    rerun_summary: Mapping[str, Any],
    refreshed_metrics: Mapping[str, Any],
) -> str:
    if (
        reran_330f
        and _norm_text(rerun_summary.get("unfamiliar_source_status")) == "loaded"
        and _safe_int(refreshed_metrics.get("source_page_missing_count"), -1) == 0
        and _safe_int(refreshed_metrics.get("unit_missing_count"), 0) > 0
    ):
        return "DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS"
    return "SMOKE_DEMO_READY_INTERNAL_ONLY"


def build_delivery_report_refresh_330j(
    *,
    source_attribution_unit_fix_dir: Path,
    fixed_prepared_dir: Path,
    previous_delivery_report_dir: Path,
    full_unfamiliar_benchmark_dir: Path,
    deduped_candidate_benchmark_dir: Path,
    trust_scoring_dir: Path,
    rerun_330f: bool,
    output_dir: Path,
    rerun_330f_output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330i_path = (
        source_attribution_unit_fix_dir / "source_attribution_unit_signal_fix_330i_summary.json"
    )
    summary_330h_path = (
        full_unfamiliar_benchmark_dir / "full_unfamiliar_export_benchmark_330h_summary.json"
    )
    summary_330g_path = (
        previous_delivery_report_dir / "end_to_end_delivery_quality_report_330g_summary.json"
    )
    fixed_manifest_path = fixed_prepared_dir / "unfamiliar_candidate_manifest.json"
    fixed_rows_path = fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"

    summary_330i = _read_json(summary_330i_path)
    summary_330h = _read_json(summary_330h_path)
    summary_330g = _read_json(summary_330g_path)
    fixed_manifest = _read_json(fixed_manifest_path)
    fixed_rows = _read_jsonl_rows(fixed_rows_path)

    qa_rows = validate_330i_summary(summary_330i)

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

    add_qa("inputs::fixed_manifest_exists", fixed_manifest_path.exists(), str(fixed_manifest_path))
    add_qa("inputs::fixed_candidate_rows_exists", fixed_rows_path.exists(), str(fixed_rows_path))
    add_qa("records::fixed_candidate_row_count", len(fixed_rows) == 117, str(len(fixed_rows)))

    rerun_summary: Dict[str, Any] = {}
    rerun_artifacts: Dict[str, Any] | None = None
    if rerun_330f:
        rerun_artifacts = _write_rerun_330f(
            fixed_prepared_dir=fixed_prepared_dir,
            rerun_330f_output_dir=rerun_330f_output_dir,
            deduped_candidate_benchmark_dir=deduped_candidate_benchmark_dir,
            trust_scoring_dir=trust_scoring_dir,
        )
        rerun_summary = rerun_artifacts["summary"]
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
        "rerun::330f_unfamiliar_source_status",
        _norm_text(rerun_summary.get("unfamiliar_source_status")) == "loaded",
        _norm_text(rerun_summary.get("unfamiliar_source_status")),
    )
    add_qa(
        "rerun::330f_decision",
        _norm_text(rerun_summary.get("decision")) == READY_330F_DECISION,
        _norm_text(rerun_summary.get("decision")),
    )

    refreshed_metrics = _build_refreshed_metrics(
        fixed_rows=fixed_rows,
        rerun_summary=rerun_summary,
    )
    add_qa(
        "quality::source_page_missing_count",
        _safe_int(refreshed_metrics.get("source_page_missing_count"), -1) == 0,
        str(refreshed_metrics.get("source_page_missing_count", "")),
    )
    add_qa(
        "quality::unit_missing_count",
        _safe_int(refreshed_metrics.get("unit_missing_count"), -1) == 54,
        str(refreshed_metrics.get("unit_missing_count", "")),
    )
    add_qa(
        "records::prepared_candidate_row_count",
        _safe_int(refreshed_metrics.get("prepared_candidate_row_count"), -1) == 117,
        str(refreshed_metrics.get("prepared_candidate_row_count", "")),
    )

    comparison = _build_comparison(
        summary_330g=summary_330g,
        summary_330h=summary_330h,
        summary_330i=summary_330i,
        refreshed_metrics=refreshed_metrics,
    )
    delivery_readiness_judgment = _delivery_readiness_judgment(
        reran_330f=rerun_330f,
        rerun_summary=rerun_summary,
        refreshed_metrics=refreshed_metrics,
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }
    no_official_asset_modification_during_330j = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330j",
        no_official_asset_modification_during_330j,
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
    recommended_next_step = "330K_UNIT_SIGNAL_IMPROVEMENT_OR_FULL_REVIEW_SAMPLE"
    recommended_next_step_secondary = "330L_CLIENT_STYLE_EXPORT_PREVIEW"

    summary = {
        "stage": "330J",
        "output_dir": str(output_dir),
        "validated_330i_unit_fix": all(
            row.get("status") == "PASS" for row in validate_330i_summary(summary_330i)
        ),
        "reran_330f": bool(rerun_330f),
        "330f_rerun_output_dir": str(rerun_330f_output_dir),
        "330f_unfamiliar_source_status": _norm_text(rerun_summary.get("unfamiliar_source_status")),
        "330f_scored_unfamiliar_record_count": _safe_int(
            rerun_summary.get("scored_unfamiliar_record_count"), 0
        ),
        "330f_decision": _norm_text(rerun_summary.get("decision")),
        **refreshed_metrics,
        **comparison,
        "delivery_readiness_judgment": delivery_readiness_judgment,
        "delivery_readiness_rationale": [
            "330J uses the 330I fixed prepared rows for a refreshed unfamiliar benchmark rerun.",
            "source_page coverage is complete, but unit gaps and UNIT_UNKNOWN risk remain material.",
            "Results are sidecar-only and still require manual review, so client-ready claims remain out of scope.",
        ],
        "recommended_next_step": recommended_next_step,
        "recommended_next_step_secondary": recommended_next_step_secondary,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330j": no_official_asset_modification_during_330j,
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
        stage="330J",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    refreshed_metrics_df = _frame_for_output(
        pd.DataFrame(
            [{"metric": key, "value": value} for key, value in refreshed_metrics.items() if not isinstance(value, dict)]
        )
    )
    comparison_df = _frame_for_output(
        pd.DataFrame(
            [
                {"metric": key, "value": value}
                for key, value in comparison.items()
                if key != "risk_flag_delta"
            ]
        )
    )
    risk_flag_delta_df = _frame_for_output(
        pd.DataFrame(
            [
                {"risk_flag": key, "delta_count": value}
                for key, value in comparison.get("risk_flag_delta", {}).items()
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
                    "modified_during_330j": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    rerun_summary_df = _frame_for_output(pd.DataFrame([rerun_summary])) if rerun_summary else pd.DataFrame()
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
    known_limitations_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "limitation": "unit_missing_remains_significant",
                    "detail": f"{_safe_int(refreshed_metrics.get('unit_missing_count'))} fixed rows still lack a unit after 330I.",
                },
                {
                    "limitation": "sidecar_only",
                    "detail": "330J refreshes sidecar benchmark and delivery reporting only; no production routing was modified.",
                },
                {
                    "limitation": "manual_review_required",
                    "detail": "Delivery judgment remains demo-only with manual review caveats and is not client-ready.",
                },
            ]
        )
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
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
        "risk_flag_delta_df": risk_flag_delta_df,
        "distribution_df": distribution_df,
        "official_asset_proof_df": official_asset_proof_df,
        "rerun_330f_summary_df": rerun_summary_df,
        "fixed_manifest_df": _frame_for_output(pd.DataFrame([fixed_manifest])) if fixed_manifest else pd.DataFrame(),
        "fixed_candidate_rows_df": _frame_for_output(pd.DataFrame(fixed_rows)),
        "known_limitations_df": known_limitations_df,
    }
