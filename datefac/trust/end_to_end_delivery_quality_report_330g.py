from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import build_no_apply_proof


READY_330F4_DECISION = "UNFAMILIAR_CANDIDATE_EXPORT_SMOKE_330F4_READY_FOR_330F_RERUN"
READY_330F_DECISION = "TRUST_ENGINE_UNFAMILIAR_PDF_BENCHMARK_330F_READY_FOR_330G_END_TO_END_DELIVERY_QUALITY_REPORT"
READY_DECISION = "END_TO_END_DELIVERY_QUALITY_REPORT_330G_READY_FOR_330H_FULL_UNFAMILIAR_BENCHMARK"
NOT_READY_DECISION = "END_TO_END_DELIVERY_QUALITY_REPORT_330G_NOT_READY"

DEFAULT_UNFAMILIAR_EXPORT_SMOKE_DIR = Path(r"D:\_datefac\output\unfamiliar_candidate_export_smoke_330f4")
DEFAULT_UNFAMILIAR_TRUST_BENCHMARK_DIR = Path(r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f")
DEFAULT_PREPARED_UNFAMILIAR_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\end_to_end_delivery_quality_report_330g")


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
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
    return rows


def _frame_for_output(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _distribution_from_series(values: Iterable[str]) -> Dict[str, int]:
    counter: Dict[str, int] = {}
    for raw in values:
        token = _norm_text(raw)
        if not token:
            continue
        counter[token] = counter.get(token, 0) + 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def validate_330f4_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::330f4_decision", _norm_text(summary.get("decision")) == READY_330F4_DECISION, _norm_text(summary.get("decision")))
    add("readiness::330f4_qa_fail_count", _safe_int(summary.get("qa_fail_count"), 1) == 0, str(summary.get("qa_fail_count", "")))
    add("selection::330f4_selected_pdf_count", _safe_int(summary.get("selected_pdf_count"), -1) == 3, str(summary.get("selected_pdf_count", "")))
    add(
        "records::330f4_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 83,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add("handoff::330f4_can_rerun_330f", bool(summary.get("can_rerun_330f")) is True, str(summary.get("can_rerun_330f", "")))
    add(
        "safety::330f4_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330f4")) is True,
        str(summary.get("no_official_asset_modification_during_330f4", "")),
    )
    return checks


def validate_330f_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::330f_decision", _norm_text(summary.get("decision")) == READY_330F_DECISION, _norm_text(summary.get("decision")))
    add("readiness::330f_qa_fail_count", _safe_int(summary.get("qa_fail_count"), 1) == 0, str(summary.get("qa_fail_count", "")))
    add(
        "inputs::330f_unfamiliar_source_status",
        _norm_text(summary.get("unfamiliar_source_status")) == "loaded",
        _norm_text(summary.get("unfamiliar_source_status")),
    )
    add(
        "records::330f_unfamiliar_candidate_artifact_row_count",
        _safe_int(summary.get("unfamiliar_candidate_artifact_row_count"), -1) == 166,
        str(summary.get("unfamiliar_candidate_artifact_row_count", "")),
    )
    add(
        "records::330f_unfamiliar_strict_deduped_candidate_count",
        _safe_int(summary.get("unfamiliar_strict_deduped_candidate_count"), -1) == 83,
        str(summary.get("unfamiliar_strict_deduped_candidate_count", "")),
    )
    add(
        "records::330f_scored_unfamiliar_record_count",
        _safe_int(summary.get("scored_unfamiliar_record_count"), -1) == 166,
        str(summary.get("scored_unfamiliar_record_count", "")),
    )
    add(
        "delivery::330f_sidecar_trusted_suggestion_count",
        _safe_int(summary.get("sidecar_trusted_suggestion_count"), -1) == 153,
        str(summary.get("sidecar_trusted_suggestion_count", "")),
    )
    add(
        "delivery::330f_sidecar_review_required_suggestion_count",
        _safe_int(summary.get("sidecar_review_required_suggestion_count"), -1) == 13,
        str(summary.get("sidecar_review_required_suggestion_count", "")),
    )
    add(
        "safety::330f_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330f")) is True,
        str(summary.get("no_official_asset_modification_during_330f", "")),
    )
    return checks


def _missing_field_counts_from_rows(prepared_rows: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    counts = {"unit": 0, "source_page": 0}
    for row in prepared_rows:
        if _norm_text(row.get("unit")) == "":
            counts["unit"] += 1
        if _norm_text(row.get("source_page")) == "":
            counts["source_page"] += 1
    return counts


def _pdf_distribution_from_prepared_rows(prepared_rows: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    return _distribution_from_series(_norm_text(row.get("source_pdf")) for row in prepared_rows)


def build_delivery_metrics(
    *,
    export_summary: Mapping[str, Any],
    benchmark_summary: Mapping[str, Any],
    prepared_manifest: Mapping[str, Any],
    prepared_rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    prepared_candidate_row_count = len(prepared_rows) or _safe_int(prepared_manifest.get("prepared_candidate_row_count"))
    processed_pdf_count = len({_norm_text(row.get("source_pdf")) for row in prepared_rows if _norm_text(row.get("source_pdf"))})
    if processed_pdf_count == 0:
        processed_pdf_count = _safe_int(prepared_manifest.get("processed_pdf_count"))
    strict_deduped_candidate_count = len(
        {
            _norm_text(row.get("candidate_id"))
            for row in prepared_rows
            if _norm_text(row.get("candidate_id"))
        }
    ) or prepared_candidate_row_count
    artifact_row_count = _safe_int(benchmark_summary.get("unfamiliar_candidate_artifact_row_count"))
    sidecar_trusted_suggestion_count = _safe_int(benchmark_summary.get("sidecar_trusted_suggestion_count"))
    sidecar_review_required_suggestion_count = _safe_int(benchmark_summary.get("sidecar_review_required_suggestion_count"))
    artifact_duplication_factor = round((artifact_row_count / strict_deduped_candidate_count), 6) if strict_deduped_candidate_count else 0.0
    sidecar_auto_trusted_ratio_artifact_row = round((sidecar_trusted_suggestion_count / artifact_row_count), 6) if artifact_row_count else 0.0
    sidecar_auto_trusted_ratio_strict_deduped = None
    if artifact_row_count == strict_deduped_candidate_count and strict_deduped_candidate_count:
        sidecar_auto_trusted_ratio_strict_deduped = round((sidecar_trusted_suggestion_count / strict_deduped_candidate_count), 6)

    manifest_missing_counts = prepared_manifest.get("missing_field_counts", {})
    calculated_missing_counts = _missing_field_counts_from_rows(prepared_rows)
    unit_missing_count = _safe_int(manifest_missing_counts.get("unit"), calculated_missing_counts["unit"])
    source_page_missing_count = _safe_int(manifest_missing_counts.get("source_page"), calculated_missing_counts["source_page"])

    actual_prepared_source_pdf_distribution = _pdf_distribution_from_prepared_rows(prepared_rows)
    benchmark_source_pdf_distribution = benchmark_summary.get("source_pdf_distribution", {})
    source_pdf_distribution_fallback_issue = bool(
        actual_prepared_source_pdf_distribution
        and benchmark_source_pdf_distribution
        and set(actual_prepared_source_pdf_distribution.keys()) != set(str(key) for key in benchmark_source_pdf_distribution.keys())
    )

    return {
        "processed_pdf_count": processed_pdf_count,
        "prepared_candidate_row_count": prepared_candidate_row_count,
        "strict_deduped_candidate_count": strict_deduped_candidate_count,
        "artifact_row_count": artifact_row_count,
        "artifact_duplication_factor": artifact_duplication_factor,
        "sidecar_trusted_suggestion_count": sidecar_trusted_suggestion_count,
        "sidecar_review_required_suggestion_count": sidecar_review_required_suggestion_count,
        "sidecar_auto_trusted_ratio_artifact_row": sidecar_auto_trusted_ratio_artifact_row,
        "sidecar_auto_trusted_ratio_strict_deduped": sidecar_auto_trusted_ratio_strict_deduped,
        "sidecar_auto_trusted_ratio_strict_deduped_computable": sidecar_auto_trusted_ratio_strict_deduped is not None,
        "estimated_human_review_burden_count": _safe_int(benchmark_summary.get("estimated_human_review_burden_count"), sidecar_review_required_suggestion_count),
        "unit_missing_count": unit_missing_count,
        "source_page_missing_count": source_page_missing_count,
        "risk_flag_distribution": benchmark_summary.get("risk_flag_distribution", {}),
        "confidence_level_distribution": benchmark_summary.get("confidence_level_distribution", {}),
        "routing_decision_distribution": benchmark_summary.get("routing_decision_distribution", {}),
        "source_artifact_distribution": benchmark_summary.get("source_artifact_distribution", {}),
        "benchmark_source_pdf_distribution": benchmark_source_pdf_distribution,
        "actual_prepared_source_pdf_distribution": actual_prepared_source_pdf_distribution,
        "source_pdf_distribution_fallback_issue": source_pdf_distribution_fallback_issue,
    }


def build_smoke_limitations(metrics: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "limitation": "not_full_13_pdf_benchmark",
            "status": "PRESENT",
            "detail": "330G covers a 3 PDF smoke subset rather than the full 13 unfamiliar PDFs.",
        },
        {
            "limitation": "sidecar_only_not_production_routing",
            "status": "PRESENT",
            "detail": "Trust Engine outputs are sidecar suggestions only and were not applied to production routing.",
        },
        {
            "limitation": "missing_unit_signal",
            "status": "PRESENT" if _safe_int(metrics.get("unit_missing_count")) > 0 else "ABSENT",
            "detail": f"Prepared unfamiliar rows still miss unit for {_safe_int(metrics.get('unit_missing_count'))} records.",
        },
        {
            "limitation": "missing_source_page_signal",
            "status": "PRESENT" if _safe_int(metrics.get("source_page_missing_count")) > 0 else "ABSENT",
            "detail": f"Prepared unfamiliar rows still miss source_page for {_safe_int(metrics.get('source_page_missing_count'))} records.",
        },
        {
            "limitation": "source_pdf_distribution_fallback_issue",
            "status": "PRESENT" if bool(metrics.get("source_pdf_distribution_fallback_issue")) else "ABSENT",
            "detail": "330F source_pdf_distribution falls back to compatibility artifact stem instead of actual PDF names.",
        },
        {
            "limitation": "artifact_row_duplication_due_to_jsonl_xlsx",
            "status": "PRESENT" if _safe_float(metrics.get("artifact_duplication_factor")) > 1.0 else "ABSENT",
            "detail": "330F artifact-row counts include both JSONL and XLSX compatibility artifacts for the same prepared rows.",
        },
    ]


def build_end_to_end_delivery_quality_report_330g(
    *,
    export_summary: Mapping[str, Any],
    benchmark_summary: Mapping[str, Any],
    prepared_unfamiliar_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    qa_rows = validate_330f4_summary(export_summary) + validate_330f_summary(benchmark_summary)

    def add_qa(check_name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": check_name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    manifest_path = prepared_unfamiliar_dir / "unfamiliar_candidate_manifest.json"
    rows_path = prepared_unfamiliar_dir / "unfamiliar_candidate_rows.jsonl"
    prepared_manifest = _read_json(manifest_path)
    prepared_rows = _read_jsonl(rows_path)

    add_qa("inputs::prepared_manifest_exists", manifest_path.exists(), str(manifest_path))
    add_qa("inputs::prepared_candidate_rows_exists", rows_path.exists(), str(rows_path))

    delivery_metrics = build_delivery_metrics(
        export_summary=export_summary,
        benchmark_summary=benchmark_summary,
        prepared_manifest=prepared_manifest,
        prepared_rows=prepared_rows,
    )

    add_qa(
        "records::processed_pdf_count",
        _safe_int(delivery_metrics.get("processed_pdf_count"), -1) == 3,
        str(delivery_metrics.get("processed_pdf_count", "")),
    )
    add_qa(
        "records::prepared_candidate_row_count",
        _safe_int(delivery_metrics.get("prepared_candidate_row_count"), -1) == 83,
        str(delivery_metrics.get("prepared_candidate_row_count", "")),
    )
    add_qa(
        "records::strict_deduped_candidate_count",
        _safe_int(delivery_metrics.get("strict_deduped_candidate_count"), -1) == 83,
        str(delivery_metrics.get("strict_deduped_candidate_count", "")),
    )
    add_qa(
        "records::artifact_row_count",
        _safe_int(delivery_metrics.get("artifact_row_count"), -1) == 166,
        str(delivery_metrics.get("artifact_row_count", "")),
    )
    add_qa(
        "records::artifact_duplication_factor",
        abs(_safe_float(delivery_metrics.get("artifact_duplication_factor")) - 2.0) < 0.000001,
        str(delivery_metrics.get("artifact_duplication_factor", "")),
    )
    add_qa(
        "records::unit_missing_count",
        _safe_int(delivery_metrics.get("unit_missing_count"), -1) == 83,
        str(delivery_metrics.get("unit_missing_count", "")),
    )
    add_qa(
        "records::source_page_missing_count",
        _safe_int(delivery_metrics.get("source_page_missing_count"), -1) == 83,
        str(delivery_metrics.get("source_page_missing_count", "")),
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330g = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330g",
        no_official_asset_modification_during_330g,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    validated_330f4_smoke_export = all(row["status"] == "PASS" for row in validate_330f4_summary(export_summary))
    validated_330f_unfamiliar_benchmark = all(row["status"] == "PASS" for row in validate_330f_summary(benchmark_summary))

    limitations = build_smoke_limitations(delivery_metrics)
    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    qa_warn_count = int(sum(1 for row in limitations if row.get("status") == "PRESENT"))

    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION
    delivery_readiness_judgment = "SMOKE_DEMO_READY_INTERNAL_ONLY"

    summary = {
        "stage": "330G",
        "output_dir": str(output_dir),
        "validated_330f4_smoke_export": validated_330f4_smoke_export,
        "validated_330f_unfamiliar_benchmark": validated_330f_unfamiliar_benchmark,
        "processed_pdf_count": _safe_int(delivery_metrics.get("processed_pdf_count")),
        "prepared_candidate_row_count": _safe_int(delivery_metrics.get("prepared_candidate_row_count")),
        "artifact_row_count": _safe_int(delivery_metrics.get("artifact_row_count")),
        "strict_deduped_candidate_count": _safe_int(delivery_metrics.get("strict_deduped_candidate_count")),
        "artifact_duplication_factor": _safe_float(delivery_metrics.get("artifact_duplication_factor")),
        "sidecar_trusted_suggestion_count": _safe_int(delivery_metrics.get("sidecar_trusted_suggestion_count")),
        "sidecar_review_required_suggestion_count": _safe_int(delivery_metrics.get("sidecar_review_required_suggestion_count")),
        "sidecar_auto_trusted_ratio_artifact_row": _safe_float(delivery_metrics.get("sidecar_auto_trusted_ratio_artifact_row")),
        "sidecar_auto_trusted_ratio_strict_deduped": delivery_metrics.get("sidecar_auto_trusted_ratio_strict_deduped"),
        "sidecar_auto_trusted_ratio_strict_deduped_computable": bool(delivery_metrics.get("sidecar_auto_trusted_ratio_strict_deduped_computable")),
        "estimated_human_review_burden_count": _safe_int(delivery_metrics.get("estimated_human_review_burden_count")),
        "unit_missing_count": _safe_int(delivery_metrics.get("unit_missing_count")),
        "source_page_missing_count": _safe_int(delivery_metrics.get("source_page_missing_count")),
        "risk_flag_distribution": delivery_metrics.get("risk_flag_distribution", {}),
        "confidence_level_distribution": delivery_metrics.get("confidence_level_distribution", {}),
        "routing_decision_distribution": delivery_metrics.get("routing_decision_distribution", {}),
        "source_artifact_distribution": delivery_metrics.get("source_artifact_distribution", {}),
        "benchmark_source_pdf_distribution": delivery_metrics.get("benchmark_source_pdf_distribution", {}),
        "actual_prepared_source_pdf_distribution": delivery_metrics.get("actual_prepared_source_pdf_distribution", {}),
        "delivery_readiness_judgment": delivery_readiness_judgment,
        "delivery_readiness_rationale": [
            "Trust Engine can score unfamiliar rows end-to-end on the 3 PDF smoke subset.",
            "Missing unit and source_page signals plus the small sample prevent client-delivery claims.",
        ],
        "smoke_limitations": [row["limitation"] for row in limitations if row.get("status") == "PRESENT"],
        "recommended_next_step": "330H_FULL_13_PDF_UNFAMILIAR_EXPORT_AND_BENCHMARK",
        "recommended_next_step_secondary": "330I_SOURCE_ATTRIBUTION_AND_UNIT_SIGNAL_FIX",
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330g": no_official_asset_modification_during_330g,
        "files_written_to_official_assets": [],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="330G",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    distribution_rows: List[Dict[str, Any]] = []
    for distribution_name in [
        "risk_flag_distribution",
        "confidence_level_distribution",
        "routing_decision_distribution",
        "source_artifact_distribution",
        "benchmark_source_pdf_distribution",
        "actual_prepared_source_pdf_distribution",
    ]:
        for bucket, count in summary.get(distribution_name, {}).items():
            distribution_rows.append({"distribution_name": distribution_name, "bucket": bucket, "count": count})

    delivery_metrics_df = _frame_for_output(
        pd.DataFrame(
            [
                {"metric": "processed_pdf_count", "value": summary["processed_pdf_count"]},
                {"metric": "prepared_candidate_row_count", "value": summary["prepared_candidate_row_count"]},
                {"metric": "artifact_row_count", "value": summary["artifact_row_count"]},
                {"metric": "strict_deduped_candidate_count", "value": summary["strict_deduped_candidate_count"]},
                {"metric": "artifact_duplication_factor", "value": summary["artifact_duplication_factor"]},
                {"metric": "sidecar_trusted_suggestion_count", "value": summary["sidecar_trusted_suggestion_count"]},
                {"metric": "sidecar_review_required_suggestion_count", "value": summary["sidecar_review_required_suggestion_count"]},
                {"metric": "sidecar_auto_trusted_ratio_artifact_row", "value": summary["sidecar_auto_trusted_ratio_artifact_row"]},
                {
                    "metric": "sidecar_auto_trusted_ratio_strict_deduped",
                    "value": summary["sidecar_auto_trusted_ratio_strict_deduped"] if summary["sidecar_auto_trusted_ratio_strict_deduped"] is not None else "",
                },
                {"metric": "estimated_human_review_burden_count", "value": summary["estimated_human_review_burden_count"]},
                {"metric": "unit_missing_count", "value": summary["unit_missing_count"]},
                {"metric": "source_page_missing_count", "value": summary["source_page_missing_count"]},
                {"metric": "delivery_readiness_judgment", "value": summary["delivery_readiness_judgment"]},
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
                    "modified_during_330g": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    prepared_manifest_df = _frame_for_output(pd.DataFrame([prepared_manifest])) if prepared_manifest else pd.DataFrame()

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
                        "qa_warn_count": qa_warn_count,
                        "qa_fail_count": qa_fail_count,
                        "decision": decision,
                    }
                ]
            )
        ),
        "qa_checks_df": qa_df,
        "delivery_metrics_df": delivery_metrics_df,
        "distribution_df": _frame_for_output(pd.DataFrame(distribution_rows)),
        "limitations_df": _frame_for_output(pd.DataFrame(limitations)),
        "prepared_manifest_df": prepared_manifest_df,
        "prepared_candidate_rows_df": _frame_for_output(pd.DataFrame(prepared_rows)),
        "official_asset_proof_df": official_asset_proof_df,
    }
