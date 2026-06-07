from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.source_attribution_unit_signal_fix_330i import (
    _listify_tokens,
    _normalize_unit_text,
    _read_json,
    _read_jsonl_rows,
)
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_330J_DECISION = "DELIVERY_REPORT_REFRESH_330J_READY_FOR_330K_UNIT_SIGNAL_OR_REVIEW_SAMPLE"
READY_FOR_330J2_DECISION = "UNIT_SIGNAL_REVIEW_330K_READY_FOR_330J2_DELIVERY_REFRESH"
READY_FOR_REVIEW_DECISION = "UNIT_SIGNAL_REVIEW_330K_READY_FOR_HUMAN_UNIT_REVIEW"
NOT_READY_DECISION = "UNIT_SIGNAL_REVIEW_330K_NOT_READY"

DEFAULT_DELIVERY_REPORT_REFRESH_DIR = Path(r"D:\_datefac\output\delivery_report_refresh_330j")
DEFAULT_SOURCE_ATTRIBUTION_UNIT_FIX_DIR = Path(
    r"D:\_datefac\output\source_attribution_unit_signal_fix_330i"
)
DEFAULT_FIXED_PREPARED_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split_330i")
DEFAULT_OPTIONAL_FIXED_PREPARED_OUTPUT_DIR = Path(
    r"D:\_datefac\output\unfamiliar_trust_split_330k"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\unit_signal_review_330k")

STATUS_FIELDS_330K = [
    "unit_status_330k",
    "unit_missing_category_330k",
    "unit_fix_330k_method",
    "unit_fix_330k_source_text",
    "unit_fix_330k_confidence",
    "unit_fix_330k_notes",
]
OUTPUT_FIELDS_330K = [
    "candidate_id",
    "metric_label_raw",
    "normalized_metric",
    "value",
    "unit",
    "year",
    "parser_sources",
    "evidence_refs",
    "risk_flags",
    "existing_status",
    "source_pdf",
    "source_artifact",
    "source_page",
    "row_text",
    "table_id",
    "unit_fix_method",
    "unit_fix_source_text",
    "unit_fix_confidence",
    "unit_fix_notes",
    *STATUS_FIELDS_330K,
]


def validate_330j_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
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
        "readiness::330j_decision",
        _norm_text(summary.get("decision")) == READY_330J_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330j_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330j_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 117,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "records::330j_strict_deduped_candidate_count",
        _safe_int(summary.get("strict_deduped_candidate_count"), -1) == 117,
        str(summary.get("strict_deduped_candidate_count", "")),
    )
    add(
        "quality::330j_unit_missing_count",
        _safe_int(summary.get("unit_missing_count"), -1) == 54,
        str(summary.get("unit_missing_count", "")),
    )
    add(
        "quality::330j_unit_unknown_risk_count",
        _safe_int(summary.get("unit_unknown_risk_count"), -1) == 54,
        str(summary.get("unit_unknown_risk_count", "")),
    )
    add(
        "quality::330j_unit_conflict_risk_count",
        _safe_int(summary.get("unit_conflict_risk_count"), -1) == 12,
        str(summary.get("unit_conflict_risk_count", "")),
    )
    add(
        "quality::330j_source_page_missing_count",
        _safe_int(summary.get("source_page_missing_count"), -1) == 0,
        str(summary.get("source_page_missing_count", "")),
    )
    add(
        "quality::330j_delivery_readiness_judgment",
        _norm_text(summary.get("delivery_readiness_judgment"))
        == "DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS",
        _norm_text(summary.get("delivery_readiness_judgment")),
    )
    add(
        "safety::330j_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330j")) is True,
        str(summary.get("no_official_asset_modification_during_330j", "")),
    )
    return checks


def _distribution_from_series(values: Iterable[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for raw in values:
        token = _norm_text(raw)
        if not token:
            continue
        counts[token] = counts.get(token, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _candidate_status(row: Mapping[str, Any]) -> str:
    unit = _norm_text(row.get("unit"))
    risk_flags = set(_listify_tokens(row.get("risk_flags")))
    confidence = _norm_text(row.get("unit_fix_confidence"))
    method = _norm_text(row.get("unit_fix_method"))
    if "UNIT_CONFLICT" in risk_flags:
        return "unit_conflict"
    if unit:
        if method.startswith("INFERRED_"):
            if confidence == "HIGH":
                return "unit_inferred_high_confidence"
            if confidence == "MEDIUM":
                return "unit_inferred_medium_confidence"
            if confidence == "LOW":
                return "unit_inferred_low_confidence"
        return "unit_present"
    if "UNIT_UNKNOWN" in risk_flags:
        return "unit_missing_with_unit_unknown"
    return "unit_missing_without_unit_unknown"


def _has_text_token(text: str, tokens: Sequence[str]) -> bool:
    normalized = _norm_text(text).casefold()
    return any(token.casefold() in normalized for token in tokens if token)


def _categorize_missing_row(row: Mapping[str, Any]) -> str:
    metric = _norm_text(row.get("normalized_metric")).casefold()
    label = _norm_text(row.get("metric_label_raw"))
    row_text = _norm_text(row.get("row_text"))
    joined = f"{label} {row_text}".casefold()

    if metric in {"pe", "pb", "ev_ebitda"}:
        return "COUNT_OR_VOLUME_LIKE_METRIC"
    if metric == "eps" or _has_text_token(joined, ["eps", "每股收益", "每股"]):
        return "PER_SHARE_LIKE_METRIC_WITH_NO_UNIT_MARKER"
    if metric in {"gross_margin", "margin", "roe"} or _has_text_token(
        joined, ["margin", "率", "比率"]
    ):
        return "PERCENT_LIKE_METRIC_WITH_NO_PERCENT_MARKER"
    if metric in {"revenue", "net_profit"} or _has_text_token(
        joined, ["营业收入", "净利润", "收入", "利润"]
    ):
        return "MONEY_LIKE_METRIC_WITH_NO_TABLE_UNIT_CONTEXT"
    if "ambiguous" in joined or "?" in joined:
        return "AMBIGUOUS_LABEL_OR_TARGET"
    if not row_text and not label:
        return "NO_SAFE_UNIT_CONTEXT"
    return "OTHER"


def _additional_safe_fix(row: Mapping[str, Any]) -> Dict[str, Any] | None:
    unit = _norm_text(row.get("unit"))
    if unit:
        return None
    risk_flags = set(_listify_tokens(row.get("risk_flags")))
    if "UNIT_CONFLICT" in risk_flags:
        return None

    metric = _norm_text(row.get("normalized_metric")).casefold()
    label = _norm_text(row.get("metric_label_raw"))
    row_text = _norm_text(row.get("row_text"))
    joined = f"{label} {row_text}"

    if metric == "pe" and _has_text_token(joined, ["p/e", "市盈率"]):
        return {
            "unit": "x",
            "method": "INFERRED_RATIO_MULTIPLE_TOKEN_330K",
            "source_text": "P/E",
            "confidence": "HIGH",
            "notes": "explicit P/E multiple token in existing row text",
        }
    if metric == "pb" and _has_text_token(joined, ["p/b", "市净率"]):
        return {
            "unit": "x",
            "method": "INFERRED_RATIO_MULTIPLE_TOKEN_330K",
            "source_text": "P/B",
            "confidence": "HIGH",
            "notes": "explicit P/B multiple token in existing row text",
        }
    if metric == "ev_ebitda" and _has_text_token(joined, ["ev/ebitda"]):
        return {
            "unit": "x",
            "method": "INFERRED_RATIO_MULTIPLE_TOKEN_330K",
            "source_text": "EV/EBITDA",
            "confidence": "HIGH",
            "notes": "explicit EV/EBITDA multiple token in existing row text",
        }
    if (
        metric == "eps"
        and _has_text_token(joined, ["eps", "每股收益"])
        and _has_text_token(joined, ["元/股", "rmb/share"])
    ):
        return {
            "unit": "RMB_per_share",
            "method": "INFERRED_PER_SHARE_TOKEN_330K",
            "source_text": "元/股",
            "confidence": "HIGH",
            "notes": "explicit per-share token in existing row text",
        }
    if (
        metric in {"gross_margin", "roe"}
        and _has_text_token(joined, ["%", "pct", "percentage"])
    ):
        return {
            "unit": "percent",
            "method": "INFERRED_PERCENT_TOKEN_330K",
            "source_text": "%" if "%" in joined else "pct",
            "confidence": "HIGH",
            "notes": "explicit percent token in existing row text",
        }
    if (
        metric in {"revenue", "net_profit"}
        and _has_text_token(joined, ["百万元", "rmb mn", "rmb million"])
    ):
        return {
            "unit": "RMB_mn",
            "method": "INFERRED_MONEY_TOKEN_330K",
            "source_text": "百万元",
            "confidence": "HIGH",
            "notes": "explicit monetary unit token in existing row text",
        }
    return None


def _apply_330k_review(
    *,
    rows_330i: Sequence[Mapping[str, Any]],
    scored_rows_330j: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    score_by_candidate: Dict[str, Mapping[str, Any]] = {}
    for scored_row in scored_rows_330j:
        candidate_id = _norm_text(scored_row.get("candidate_id"))
        if candidate_id and candidate_id not in score_by_candidate:
            score_by_candidate[candidate_id] = scored_row

    reviewed_rows: List[Dict[str, Any]] = []
    fixes_applied = 0
    review_rows: List[Dict[str, Any]] = []

    for row in rows_330i:
        out = dict(row)
        status = _candidate_status(out)
        missing_category = (
            _categorize_missing_row(out)
            if status in {"unit_missing_with_unit_unknown", "unit_missing_without_unit_unknown", "unit_conflict"}
            else ""
        )
        fix = _additional_safe_fix(out)
        if fix:
            fixes_applied += 1
            out["unit"] = fix["unit"]
            out["unit_fix_330k_method"] = fix["method"]
            out["unit_fix_330k_source_text"] = fix["source_text"]
            out["unit_fix_330k_confidence"] = fix["confidence"]
            out["unit_fix_330k_notes"] = fix["notes"]
            risk_flags = [token for token in _listify_tokens(out.get("risk_flags")) if token != "UNIT_UNKNOWN"]
            out["risk_flags"] = risk_flags
            status = "unit_inferred_high_confidence"
            missing_category = ""
        else:
            out["unit_fix_330k_method"] = ""
            out["unit_fix_330k_source_text"] = ""
            out["unit_fix_330k_confidence"] = ""
            out["unit_fix_330k_notes"] = ""
        out["unit_status_330k"] = status
        out["unit_missing_category_330k"] = missing_category

        reviewed_rows.append(out)

        scored = score_by_candidate.get(_norm_text(out.get("candidate_id")), {})
        needs_review = status in {
            "unit_missing_with_unit_unknown",
            "unit_missing_without_unit_unknown",
            "unit_conflict",
        }
        high_impact_with_unit_risk = (
            _norm_text(scored.get("confidence_level")) == "HIGH"
            or _norm_text(scored.get("routing_decision")) == "TRUSTED"
        ) and (
            "UNIT_UNKNOWN" in _listify_tokens(out.get("risk_flags"))
            or "UNIT_CONFLICT" in _listify_tokens(out.get("risk_flags"))
        )
        if needs_review or high_impact_with_unit_risk:
            review_rows.append(
                {
                    "candidate_id": _norm_text(out.get("candidate_id")),
                    "source_pdf": _norm_text(out.get("source_pdf")),
                    "source_page": _norm_text(out.get("source_page")),
                    "normalized_metric": _norm_text(out.get("normalized_metric")),
                    "metric_label_raw": _norm_text(out.get("metric_label_raw")),
                    "row_text": _norm_text(out.get("row_text")),
                    "unit": _norm_text(out.get("unit")),
                    "unit_status_330k": status,
                    "unit_missing_category_330k": missing_category,
                    "risk_flags": " | ".join(_listify_tokens(out.get("risk_flags"))),
                    "unit_fix_method": _norm_text(out.get("unit_fix_method")),
                    "unit_fix_source_text": _norm_text(out.get("unit_fix_source_text")),
                    "unit_fix_330k_method": _norm_text(out.get("unit_fix_330k_method")),
                    "unit_fix_330k_source_text": _norm_text(out.get("unit_fix_330k_source_text")),
                    "confidence_level_330j": _norm_text(scored.get("confidence_level")),
                    "routing_decision_330j": _norm_text(scored.get("routing_decision")),
                    "recommended_human_decision": (
                        "KEEP_UNIT_UNKNOWN"
                        if status == "unit_missing_with_unit_unknown"
                        else "REJECT_UNIT"
                        if status == "unit_conflict"
                        else "NEEDS_MORE_CONTEXT"
                    ),
                    "notes": "",
                }
            )

    reviewed_df = _frame_for_output(pd.DataFrame(reviewed_rows, columns=OUTPUT_FIELDS_330K))
    review_df = _frame_for_output(pd.DataFrame(review_rows))
    return {
        "reviewed_rows_df": reviewed_df,
        "review_df": review_df,
        "additional_safe_unit_fix_count": fixes_applied,
    }


def _write_optional_fixed_outputs(
    optional_fixed_prepared_output_dir: Path,
    reviewed_df: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> Dict[str, str]:
    optional_fixed_prepared_output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = optional_fixed_prepared_output_dir / "unfamiliar_candidate_rows.jsonl"
    xlsx_path = optional_fixed_prepared_output_dir / "unfamiliar_candidate_rows.xlsx"
    manifest_path = optional_fixed_prepared_output_dir / "unfamiliar_candidate_manifest.json"

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in reviewed_df.to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        reviewed_df.to_excel(writer, sheet_name="unfamiliar_candidate_rows", index=False)

    manifest_path.write_text(json.dumps(dict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "jsonl_path": str(jsonl_path),
        "xlsx_path": str(xlsx_path),
        "manifest_path": str(manifest_path),
    }


def _write_review_workbook(output_dir: Path, review_df: pd.DataFrame) -> str:
    workbook_path = output_dir / "unit_signal_review_330k_workbook.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)
    by_pdf_df = (
        _frame_for_output(
            review_df.groupby("source_pdf", dropna=False).size().reset_index(name="count")
        )
        if not review_df.empty
        else pd.DataFrame()
    )
    by_metric_df = (
        _frame_for_output(
            review_df.groupby("normalized_metric", dropna=False).size().reset_index(name="count")
        )
        if not review_df.empty
        else pd.DataFrame()
    )
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        review_df.to_excel(writer, sheet_name="review_candidates", index=False)
        by_pdf_df.to_excel(writer, sheet_name="examples_by_source_pdf", index=False)
        by_metric_df.to_excel(writer, sheet_name="examples_by_metric", index=False)
    return str(workbook_path)


def build_unit_signal_review_330k(
    *,
    delivery_report_refresh_dir: Path,
    source_attribution_unit_fix_dir: Path,
    fixed_prepared_dir: Path,
    output_dir: Path,
    optional_fixed_prepared_output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330j_path = delivery_report_refresh_dir / "delivery_report_refresh_330j_summary.json"
    summary_330i_path = (
        source_attribution_unit_fix_dir / "source_attribution_unit_signal_fix_330i_summary.json"
    )
    fixed_rows_path = fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"
    fixed_manifest_path = fixed_prepared_dir / "unfamiliar_candidate_manifest.json"
    scored_rows_path = (
        Path(r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j")
        / "unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl"
    )

    summary_330j = _read_json(summary_330j_path)
    summary_330i = _read_json(summary_330i_path)
    rows_330i = _read_jsonl_rows(fixed_rows_path)
    fixed_manifest = _read_json(fixed_manifest_path)
    scored_rows_330j = _read_jsonl_rows(scored_rows_path)

    qa_rows = validate_330j_summary(summary_330j)

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

    add_qa("inputs::fixed_candidate_rows_exists", fixed_rows_path.exists(), str(fixed_rows_path))
    add_qa("inputs::scored_rows_330j_exists", scored_rows_path.exists(), str(scored_rows_path))
    add_qa("records::input_candidate_row_count", len(rows_330i) == 117, str(len(rows_330i)))

    review_artifacts = _apply_330k_review(rows_330i=rows_330i, scored_rows_330j=scored_rows_330j)
    reviewed_df = review_artifacts["reviewed_rows_df"]
    review_df = review_artifacts["review_df"]
    additional_safe_unit_fix_count = int(review_artifacts["additional_safe_unit_fix_count"])

    unit_status_distribution = _distribution_from_series(reviewed_df["unit_status_330k"].tolist())
    unit_missing_category_distribution = _distribution_from_series(
        reviewed_df["unit_missing_category_330k"].tolist()
    )
    unit_missing_count_after_330k = int(
        sum(1 for row in reviewed_df.to_dict(orient="records") if not _norm_text(row.get("unit")))
    )
    unit_conflict_count_input = int(
        sum(
            1
            for row in rows_330i
            if "UNIT_CONFLICT" in _listify_tokens(row.get("risk_flags"))
        )
    )
    unit_missing_count_input = int(
        sum(1 for row in rows_330i if not _norm_text(row.get("unit")))
    )
    unit_review_required_count = int(len(review_df))
    unit_conflict_review_count = int(
        sum(1 for row in review_df.to_dict(orient="records") if row.get("unit_status_330k") == "unit_conflict")
    )
    unit_unknown_review_count = int(
        sum(
            1
            for row in review_df.to_dict(orient="records")
            if row.get("unit_status_330k") == "unit_missing_with_unit_unknown"
        )
    )
    high_confidence_with_unit_risk_count = int(
        sum(
            1
            for row in review_df.to_dict(orient="records")
            if _norm_text(row.get("confidence_level_330j")) == "HIGH"
        )
    )
    pdfs_affected_by_unit_risk_count = int(
        len(
            {
                _norm_text(row.get("source_pdf"))
                for row in review_df.to_dict(orient="records")
                if _norm_text(row.get("source_pdf"))
            }
        )
    )

    review_workbook_path = _write_review_workbook(output_dir=output_dir, review_df=review_df)
    human_review_workbook_generated = Path(review_workbook_path).exists()
    add_qa(
        "review::human_review_workbook_generated",
        human_review_workbook_generated,
        review_workbook_path,
    )
    add_qa(
        "quality::unit_missing_count_after_330k",
        unit_missing_count_after_330k <= 54,
        str(unit_missing_count_after_330k),
    )
    add_qa(
        "review::review_sample_row_count",
        len(review_df) > 0,
        str(len(review_df)),
    )

    optional_fixed_output_manifest: Dict[str, Any] = {}
    optional_fixed_output_paths: Dict[str, str] = {}
    if additional_safe_unit_fix_count > 0:
        optional_fixed_output_manifest = {
            "stage": "330K",
            "input_candidate_row_count": int(len(rows_330i)),
            "output_candidate_row_count": int(len(reviewed_df)),
            "additional_safe_unit_fix_count": additional_safe_unit_fix_count,
            "unit_missing_count_after_330k": unit_missing_count_after_330k,
            "source_pdf_unique_count": _safe_int(summary_330i.get("source_pdf_unique_count"), 0),
            "canonical_candidate_source_file": "unfamiliar_candidate_rows.jsonl",
            "inspection_mirror_file": "unfamiliar_candidate_rows.xlsx",
        }
        optional_fixed_output_paths = _write_optional_fixed_outputs(
            optional_fixed_prepared_output_dir=optional_fixed_prepared_output_dir,
            reviewed_df=reviewed_df,
            manifest=optional_fixed_output_manifest,
        )
        optional_fixed_output_manifest.update(optional_fixed_output_paths)

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }
    no_official_asset_modification_during_330k = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330k",
        no_official_asset_modification_during_330k,
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

    if qa_fail_count > 0:
        decision = NOT_READY_DECISION
    elif additional_safe_unit_fix_count > 0:
        decision = READY_FOR_330J2_DECISION
    else:
        decision = READY_FOR_REVIEW_DECISION

    recommended_next_step = (
        "330J2_DELIVERY_REPORT_REFRESH_AFTER_330K"
        if additional_safe_unit_fix_count > 0
        else "330K2_HUMAN_UNIT_REVIEW"
    )
    secondary_next_step = "330L_CLIENT_STYLE_EXPORT_PREVIEW"

    summary = {
        "stage": "330K",
        "output_dir": str(output_dir),
        "validated_330j_delivery_refresh": all(
            row.get("status") == "PASS" for row in validate_330j_summary(summary_330j)
        ),
        "input_candidate_row_count": int(len(rows_330i)),
        "unit_missing_count_input": unit_missing_count_input,
        "unit_conflict_count_input": unit_conflict_count_input,
        "unit_status_distribution": unit_status_distribution,
        "unit_missing_category_distribution": unit_missing_category_distribution,
        "additional_safe_unit_fix_count": additional_safe_unit_fix_count,
        "unit_missing_count_after_330k": unit_missing_count_after_330k,
        "review_sample_row_count": int(len(review_df)),
        "human_review_workbook_generated": human_review_workbook_generated,
        "human_review_workbook_path": review_workbook_path,
        "unit_review_required_count": unit_review_required_count,
        "unit_conflict_review_count": unit_conflict_review_count,
        "unit_unknown_review_count": unit_unknown_review_count,
        "high_confidence_with_unit_risk_count": high_confidence_with_unit_risk_count,
        "pdfs_affected_by_unit_risk_count": pdfs_affected_by_unit_risk_count,
        "recommended_next_step": recommended_next_step,
        "secondary_next_step": secondary_next_step,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330k": no_official_asset_modification_during_330k,
        "files_written_to_official_assets": [],
        "optional_fixed_prepared_output_dir": str(optional_fixed_prepared_output_dir)
        if additional_safe_unit_fix_count > 0
        else "",
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
        stage="330K",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    status_distribution_df = _frame_for_output(
        pd.DataFrame(
            [{"unit_status_330k": key, "count": value} for key, value in unit_status_distribution.items()]
        )
    )
    category_distribution_df = _frame_for_output(
        pd.DataFrame(
            [
                {"unit_missing_category_330k": key, "count": value}
                for key, value in unit_missing_category_distribution.items()
                if _norm_text(key)
            ]
        )
    )
    review_burden_df = _frame_for_output(
        pd.DataFrame(
            [
                {"metric": "unit_review_required_count", "value": unit_review_required_count},
                {"metric": "unit_conflict_review_count", "value": unit_conflict_review_count},
                {"metric": "unit_unknown_review_count", "value": unit_unknown_review_count},
                {"metric": "high_confidence_with_unit_risk_count", "value": high_confidence_with_unit_risk_count},
                {"metric": "pdfs_affected_by_unit_risk_count", "value": pdfs_affected_by_unit_risk_count},
                {"metric": "additional_safe_unit_fix_count", "value": additional_safe_unit_fix_count},
                {"metric": "unit_missing_count_after_330k", "value": unit_missing_count_after_330k},
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
                    "modified_during_330k": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    optional_fixed_manifest_df = (
        _frame_for_output(pd.DataFrame([optional_fixed_output_manifest]))
        if optional_fixed_output_manifest
        else pd.DataFrame()
    )
    known_limitations_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "limitation": "no_pdf_reopen",
                    "detail": "330K only uses existing 330I/330J row context and does not reopen PDFs.",
                },
                {
                    "limitation": "conflict_rows_not_auto_fixed",
                    "detail": "Rows with conflicting unit evidence remain review-required by design.",
                },
                {
                    "limitation": "review_package_required",
                    "detail": "Remaining unit-risk rows still require human review before any further delivery refresh.",
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
        "status_distribution_df": status_distribution_df,
        "category_distribution_df": category_distribution_df,
        "review_burden_df": review_burden_df,
        "review_df": review_df,
        "reviewed_rows_df": reviewed_df,
        "fixed_manifest_df": _frame_for_output(pd.DataFrame([fixed_manifest])) if fixed_manifest else pd.DataFrame(),
        "optional_fixed_manifest_df": optional_fixed_manifest_df,
        "official_asset_proof_df": official_asset_proof_df,
        "known_limitations_df": known_limitations_df,
    }
